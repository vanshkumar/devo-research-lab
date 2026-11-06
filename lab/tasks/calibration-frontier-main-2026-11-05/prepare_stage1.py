"""Execute the released finite source-only preparation. No evaluation cache I/O."""
import time
import resource
BEGIN_WALL = time.monotonic()
BEGIN_CPU = time.process_time()
import hashlib
import io
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import numpy as np
from scipy.special import expit
import source_models as sm
from source_models import inherited as e
from rnn_learning import load_rnn
from rnn_rollout import calibration_particles
from pilot import subject

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEV = sm.DEVELOPMENT
OLD = ROOT/'campaigns/learning_rule_transport_2026-10-28'
IO = Counter()
PINS = {}
TIMINGS = {}


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(path, pin=None):
    b = path.read_bytes()
    IO['explicit_read_bytes'] += len(b)
    h = hashlib.sha256(b).hexdigest()
    PINS[str(path.relative_to(ROOT))] = h
    if pin is not None and h != pin:
        raise ValueError('Input pin changed: '+str(path))
    return b


def get(path, pin=None):
    return json.loads(read(path, pin))


def arrays(path, pin=None):
    b = read(path, pin)
    with np.load(io.BytesIO(b), allow_pickle=False) as z:
        result = {key: z[key] for key in z.files}
    IO['decoded_array_bytes'] += sum(v.nbytes for v in result.values())
    return result


def serial(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def save(name, value):
    (HERE/name).write_text(json.dumps(value, indent=2, allow_nan=False, default=serial)+'\n')


def stamp(name, start):
    TIMINGS[name] = dict(wall_seconds=time.monotonic()-start[0], cpu_seconds=time.process_time()-start[1])


def clock():
    return time.monotonic(), time.process_time()


def check_budget():
    if time.process_time()-BEGIN_CPU > 890:
        raise RuntimeError('Stage1 CPU stop before900seconds')
    if sum(IO.values()) > 225_000_000:
        raise RuntimeError('Stage1 explicit I/O stop preserving context-read reserve')


def site_mean(rows, field):
    sites = sorted({r['lab'] for r in rows})
    return float(np.mean([np.mean([r[field] for r in rows if r['lab'] == lab]) for lab in sites]))


def summarize_source(samples, obs, blocks, ids, labs, raw):
    result = {}
    conditions = ['primary', 'source_context_input', 'source_calibrated_engagement']
    names = ['growth', 'recent_growth', 'gru']
    for k, condition in enumerate(conditions):
        result[condition] = {}
        for ci, cutoff in enumerate((200, 1000)):
            result[condition][str(cutoff)] = {}
            for ni, name in enumerate(names):
                rows = []
                for i, s in enumerate(ids):
                    long = samples[i, k, ci, ni, :, 1, :]
                    target = obs[i, 1]
                    score = e.score_window(long, target, 2000)
                    item = dict(subject=s, lab=labs[s], **score)
                    count_details = []
                    for j in (0, 2, 4, 6):
                        values = long[:, j]
                        low, high = np.quantile(values, [.1, .9])
                        count_details.append(dict(column=j, observed=int(target[j]), predicted_mean=float(values.mean()),
                                                  low80=float(low), high80=float(high),
                                                  covered80=bool(low <= target[j] <= high)))
                    item['count_diagnostics'] = count_details
                    item['omission_rate'] = float(long[:, 4].mean()/2000)
                    item['observed_omission_rate'] = float(target[4]/2000)
                    ob = (raw[s][1000:3000, 2] == 0).reshape(40, 50).sum(1)
                    pred = blocks[i, k, ci, ni]
                    item['omission_block50_observed_second_moment'] = float(np.mean(ob**2))
                    item['omission_block50_predicted_second_moment'] = float(np.mean(pred**2))
                    rows.append(item)
                result[condition][str(cutoff)][name] = dict(
                    equal_site={f:site_mean(rows, f) for f in ('mixed_ratio_score', 'equal_side_mae', 'joint', 'count',
                                'omission_crps', 'omission_rate', 'observed_omission_rate',
                                'omission_block50_observed_second_moment', 'omission_block50_predicted_second_moment')},
                    equal_animal={f:float(np.mean([r[f] for r in rows])) for f in ('mixed_ratio_score', 'equal_side_mae',
                                   'omission_rate', 'observed_omission_rate')}, per_animal=rows)
    return result


def main():
    access = get(DEV/'SOURCE_FIT6000_MANIFEST.json', '33365f4725bd3f398f6f8a9e0b9de8ff85bbdd1bd192dbf1daa0ece1748cb585')
    split = get(OLD/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json', '1ebd21840771d2b101a80ee9912615075f7a99d55520e5cfe35bc4d95fbc6d10')
    roster = split['train'] + split['validation']
    assert access['subjects'] == roster and len(set(roster)) == 74
    assert access['maximum_fit_rows'] == 6000 and access['boundary_decode_separately_authorized']
    for s in roster:
        prior = access['exposure_proof'][s]['prior_original_full_read']
        assert prior['event'] == 'open_outcomes' and prior['split'] == 'dev'
        assert prior['subject'] == s and prior['scope'] == 'all indexed trials for this subject'
        assert set(access['fields']) <= set(prior['fields'])
        assert all(0 <= z['fit_selected'][0] < z['fit_selected'][1] <= 6000
                   for z in access['exposure_proof'][s]['selected_exact_sessions'])
    save('PREP_ACCESS.json', dict(utc=utc(), authority='Released Stage1 BRIEF plus exact historical original74 proof',
         manifest_sha256=PINS[str((DEV/'SOURCE_FIT6000_MANIFEST.json').relative_to(ROOT))],
         subjects=roster, fields=access['fields'], fit_cap=6000, cache_only=True,
         prior_event='open_outcomes/dev/all indexed trials for each exact subject',
         historical_selected_rows=sum(v['fit_rows'] for v in access['disposition'].values()),
         historical_decoded_rows=sum(v['decoded'] for v in access['disposition'].values()),
         evaluation_raw_opened=False, evaluation_cap_unchanged=4000, no_new_archive_ingress=True))
    raw = arrays(DEV/'TRAIN6000_ROWS.npz', '71b837ea55cd6363db65d2c4ca15b7ceec1309b5dc5d972b8b85407851592049')
    assert list(raw) == roster
    assert all(len(raw[s]) == access['disposition'][s]['fit_rows'] <= 6000 for s in raw)
    labs = {s: access['disposition'][s]['lab'] for s in raw}
    train = split['train']
    validation = [s for s in split['validation'] if len(raw[s]) >= 3000]
    assert len(train) == 62 and len(validation) == 10
    oldbank = arrays(OLD/'artifacts/baselines/nested_growth_bank.npz', '036f3cfedd56e915b051fb29a80a2622cf5a747366ea31aa46b9249a922eea01')
    donors = list(oldbank['subjects'])
    assert len(donors) == 58 and set(donors) <= set(train)
    t = clock()
    canonical = {c:e.bank_at(raw, donors, c) for c in (200, 1000)}
    reference = {k:float(np.max(np.abs(canonical[1000][k] - oldbank[k]))) for k in ('prefix', 'delta_w', 'delta_omit')}
    assert max(reference.values()) < 1e-10
    assert np.array_equal(canonical[1000]['valid'], oldbank['valid'])
    canonical[1000] = oldbank
    candidates = {key:{c:e.bank_at(raw, donors, c, half) for c in (200, 1000)}
                  for key, half in [('100', 100.), ('250', 250.), ('500', 500.), ('infinity', np.inf)]}
    for c in (200, 1000):
        np.savez_compressed(HERE/f'SOURCE_CANONICAL_BANK_{c}.npz', **canonical[c])
        for key in candidates:
            np.savez_compressed(HERE/f'SOURCE_RECENT_BANK_{key}_{c}.npz', **candidates[key][c])
    stamp('source_banks_and_exact_reference', t)
    t = clock()
    input_fit = sm.fit_input(raw, train, labs)
    engagement = {c:sm.fit_engagement(raw, train, canonical[c], c) for c in (200, 1000)}
    np.savez_compressed(HERE/'SOURCE_INPUT_FIT.npz', **{k:v for k,v in input_fit.items() if k != 'sites'}, sites=input_fit['sites'])
    save('SOURCE_ENGAGEMENT_FIT.json', engagement)
    stamp('input_and_engagement_fits', t)
    save('SOURCE_FIT_CHECKPOINT.json', dict(utc=utc(), reference=reference, timings=TIMINGS, io=dict(IO),
         train_subjects=train, donors=donors, selection_eligible=validation,
         selection_excluded={s:len(raw[s]) for s in split['validation'] if s not in validation},
         short_optimizer={s:len(raw[s]) for s in train if s not in donors}, pins=PINS))
    print('Fitted finite source models', TIMINGS, flush=True)
    check_budget()
    t = clock()
    checks = {s:{str(c):sm.pretrial_input_checks(s, raw[s], c, input_fit, labs[s]) for c in (200, 1000)} for s in validation}
    conditional_engagement = {}
    for cutoff in (200, 1000):
        rows = []
        beta = np.asarray(engagement[cutoff]['beta'])
        for s in validation:
            X = sm.engagement_design(raw[s][:3000], cutoff, canonical[cutoff], s)
            y = (raw[s][cutoff:3000, 2] == 0).astype(float)
            for name, q in [('primary_offset', expit(X[:, 1])), ('source_calibrated_engagement', expit(X@beta))]:
                rows.append(dict(subject=s, lab=labs[s], condition=name, observed_rate=float(y.mean()),
                                 predicted_rate=float(q.mean()), brier=float(np.mean((q-y)**2)),
                                 log_loss=float(-np.mean(y*np.log(q)+(1-y)*np.log1p(-q)))))
        conditional_engagement[str(cutoff)] = rows
    save('SOURCE_PRETRIAL_CHECKS.json', dict(utc=utc(), input=checks, engagement=conditional_engagement,
         interpretation='Causal actual-history predictions, source selection only; not autonomous trajectory validation'))
    stamp('selection_pretrial_checks', t)
    check_budget()
    # Original recency selection, with the declared common128particle rule.
    def select(bankset, canonical_set, selection_ids):
        cv = {}
        for key in ('100', '250', '500', 'infinity'):
            half = np.inf if key == 'infinity' else float(key)
            cv[key] = {}
            for cutoff in (200, 1000):
                rows = []
                cache = {}
                for s in selection_ids:
                    if s not in cache:
                        sample, _, _ = sm.simulate(s, raw[s], cutoff, 'recent_growth', None, canonical_set[cutoff],
                                                   bankset[key][cutoff], half, n=128)
                        cache[s] = e.score_window(sample[:, 1], e.observed(raw[s])[1], 2000)['mixed_ratio_score']
                    rows.append(dict(subject=s, lab=labs[s], score=cache[s]))
                cv[key][str(cutoff)] = dict(equal_site=site_mean(rows, 'score'), per_animal=rows)
        ranking = {k:float(np.mean([v[str(c)]['equal_site'] for c in (200, 1000)])) for k,v in cv.items()}
        return min(ranking, key=ranking.get), ranking, cv
    t = clock()
    chosen, ranking, cv = select(candidates, canonical, validation)
    stamp('original_source_recency_selection', t)
    half = np.inf if chosen == 'infinity' else float(chosen)
    save('SOURCE_SELECTION.json', dict(utc=utc(), chosen=chosen, ranking=ranking, cv=cv,
         rule='equal-site source mixed proper score, averaged equally across cutoffs; primary teacher/engagement;128particles',
         tie_order=['100','250','500','infinity']))
    modelpath = OLD/'artifacts/rnn/rnnglm32_nested_best.npz'
    read(modelpath, 'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940')
    # load_rnn performs its own compressed-file read; count that duplicate explicitly.
    IO['explicit_read_bytes'] += modelpath.stat().st_size
    model = load_rnn(modelpath)
    IO['model_decoded_array_bytes'] += sum(v.nbytes for v in model.params.values() if isinstance(v, np.ndarray))
    allsamples = []
    allblocks = []
    obs = []
    t = clock()
    law_times = Counter()
    for i, s in enumerate(validation):
        contexts = []
        contextblocks = []
        obs.append(e.observed(raw[s]))
        for condition in ('primary','source_context_input','source_calibrated_engagement'):
            cuts = []
            cutblocks = []
            for cutoff in (200, 1000):
                laws = []
                lawblocks = []
                for name in ('growth','recent_growth','gru'):
                    lt = time.process_time()
                    sample, _, block = sm.simulate(s, raw[s], cutoff, name, model, canonical[cutoff],
                            candidates[chosen][cutoff], half, n=128, condition=condition,
                            input_fit=input_fit, lab=labs[s], engagement_fit=engagement)
                    law_times[condition+'__'+name] += time.process_time()-lt
                    laws.append(sample)
                    lawblocks.append(block)
                cuts.append(np.stack(laws))
                cutblocks.append(np.stack(lawblocks))
            contexts.append(np.stack(cuts))
            contextblocks.append(np.stack(cutblocks))
        allsamples.append(np.stack(contexts))
        allblocks.append(np.stack(contextblocks))
        print('Source autonomous selection', i+1, '/10 CPU', round(time.process_time()-BEGIN_CPU, 2), flush=True)
        check_budget()
    samples = np.stack(allsamples)
    observed = np.stack(obs)
    blocks = np.stack(allblocks)
    np.savez_compressed(HERE/'SOURCE_COUNTS.npz', samples=samples, observed=observed,
                        omission_blocks50=blocks, subjects=validation, cutoffs=[200,1000], windows=[500,2000],
                        names=['growth','recent_growth','gru'],
                        conditions=['primary','source_context_input','source_calibrated_engagement'])
    stamp('three_condition_source_forecasts', t)
    t = clock()
    summary = summarize_source(samples, observed, blocks, validation, labs, raw)
    save('SOURCE_PREDICTIVE_CHECKS.json', dict(utc=utc(), summary=summary, per_law_cpu_seconds=dict(law_times),
         particles=128, source_selection=chosen, scope='Original ten selection animals only; original futures consumed; no all64 main'))
    stamp('source_reduction', t)
    # Numerical chronology: poison only SOURCE futures, all seven fields except boundaries.
    t = clock()
    s = sorted(validation, key=lambda x:hashlib.sha256(x.encode()).hexdigest())[0]
    invariance = []
    for cutoff in (200,1000):
        poisoned = raw[s].copy()
        poisoned[cutoff:, :6] = np.nan
        for condition in ('primary','source_context_input','source_calibrated_engagement'):
            for name in ('growth','recent_growth','gru'):
                args = dict(s=s, cutoff=cutoff, name=name, model=model, canonical=canonical[cutoff],
                            candidate=candidates[chosen][cutoff], half=half, n=16, condition=condition,
                            input_fit=input_fit, lab=labs[s], engagement_fit=engagement)
                original, _, _ = sm.simulate(a=raw[s], **args)
                changed, _, _ = sm.simulate(a=poisoned, **args)
                assert np.array_equal(original, changed)
                invariance.append(dict(subject=s, cutoff=cutoff, condition=condition, model=name, identical=True))
    nonlinear = []
    for s in sorted(validation, key=lambda x:hashlib.sha256(x.encode()).hexdigest())[:3]:
        for cutoff in (200,1000):
            t0 = time.process_time()
            n = 32
            seed = e.original_seed(s)+313
            linear, info = calibration_particles(model, subject(raw[s][:cutoff]), n, seed)
            rng = np.random.default_rng(seed)
            delta = rng.multivariate_normal(np.zeros(3), np.asarray(info['initial_covariance']), size=n)
            delta *= info['endpoint_sd_cap_factor']
            exact = dict(w=[],h=[])
            exactstart = time.process_time()
            for v in delta:
                _, _, end = model.sequence(subject(raw[s][:cutoff]), np.asarray(info['w0'])+v)
                exact['w'].append(end['w'])
                exact['h'].append(end['h'])
            exactcpu = time.process_time()-exactstart
            exact = {k:np.array(v) for k,v in exact.items()}
            errors = np.array([np.abs(model.probs(linear,np.full(n,x))-model.probs(exact,np.full(n,x)))
                               for x in (-1,-.5,-.25,-.125,-.0625,0,.0625,.125,.25,.5,1)])
            nonlinear.append(dict(subject=s, cutoff=cutoff, particles=n, seed=seed,
                      mean_probability_error=float(errors.mean()), max_probability_error=float(errors.max()),
                      exact_transport_cpu_seconds=exactcpu, calibration_plus_transport_cpu_seconds=time.process_time()-t0))
    save('SOURCE_NUMERICAL_CHECKS.json', dict(utc=utc(), future_poison=invariance, nonlinear=nonlinear))
    stamp('source_chronology_and_nonlinear_cost', t)
    check_budget()
    # One dependent whole-source perturbation; samples are source units, never particles.
    t = clock()
    rng = np.random.default_rng(20261105041)
    def stratified_units(ids):
        draw = []
        for lab in sorted({labs[s] for s in ids}):
            group = [s for s in ids if labs[s] == lab]
            draw += list(rng.choice(group, len(group), replace=True))
        return draw
    drawdonors = stratified_units(donors)
    drawselection = stratified_units(validation)
    outercanonical = {c:e.bank_at(raw, drawdonors, c) for c in (200,1000)}
    outercandidates = {key:{c:e.bank_at(raw, drawdonors, c, h) for c in (200,1000)}
                       for key,h in [('100',100.),('250',250.),('500',500.),('infinity',np.inf)]}
    rebuilt = clock()
    outerchosen, outerranking, outercv = select(outercandidates, outercanonical, drawselection)
    selection_seconds = time.process_time()-rebuilt[1]
    outerhalf = np.inf if outerchosen == 'infinity' else float(outerchosen)
    dependent = []
    forecaststart = clock()
    for s in validation:
        cuts = []
        for cutoff in (200,1000):
            laws = []
            for name in ('growth','recent_growth'):
                a, _, _ = sm.simulate(s, raw[s], cutoff, name, None, outercanonical[cutoff],
                                     outercandidates[outerchosen][cutoff], outerhalf, n=128)
                laws.append(a)
            cuts.append(np.stack(laws))
        dependent.append(np.stack(cuts))
    forecast_cpu = time.process_time()-forecaststart[1]
    np.savez_compressed(HERE/'SOURCE_ONE_RESAMPLE_COUNTS.npz', samples=np.stack(dependent),
                        subjects=validation, names=['growth','recent_growth'], cutoffs=[200,1000], windows=[500,2000])
    stamp('one_source_draw_with_reselection_and_dependent_forecasts', t)
    save('SOURCE_ONE_RESAMPLE.json', dict(utc=utc(), seed=20261105041, donors=drawdonors,
         selection=drawselection, chosen=outerchosen, ranking=outerranking, cv=outercv,
         source_selection_cpu_seconds=selection_seconds, dependent_forecast_cpu_seconds=forecast_cpu,
         dependent_animals=len(validation), particles=128, no_neural_refit=True,
         source_fitting='Deterministic per-animal ridge fits cached; rebuild multiplicities/anchors/increments and donor law on whole-source resample. No fake repeated optimization of unchanged individual data.',
         scope='One measured source-only price pilot, not a source95%tail or biological confidence interval'))
    check_budget()
    save('STAGE1_RESOURCES.json', dict(utc=utc(), process_wall_seconds=time.monotonic()-BEGIN_WALL,
         scientific_process_cpu_seconds=time.process_time()-BEGIN_CPU, timings=TIMINGS,
         io=dict(IO), explicit_read_decode_bytes=sum(IO.values()),
         peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         pins=PINS, no_evaluation_cache_reads=True, no_all64_main=True,
         no_archive_ingress=True, estimated_additional_context_read_charge_bytes=15_000_000,
         resource_unknowns=['Physical I/O','runtime/import/provider reads','earlier-lineage unknowns unchanged'],
         historical_accounting='acquisition-rule-vs-tracker/ACCOUNTING.json; counted-plus-conservative1,061,983,723bytes and590.689978serial science wall seconds, plus older original lineage; not refunded',
         job_disposition='All scientific operations in this process finished'))
    print('Saved Stage1 outputs; CPU', time.process_time()-BEGIN_CPU, 'wall', time.monotonic()-BEGIN_WALL,
          'explicit read/decode',sum(IO.values()), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        save('STAGE1_FAILURE_'+utc().replace(':','-')+'.json', dict(utc=utc(), error=repr(exc),
             process_wall_seconds=time.monotonic()-BEGIN_WALL, scientific_cpu_seconds=time.process_time()-BEGIN_CPU,
             io=dict(IO), pins=PINS, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        raise
