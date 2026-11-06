"""Matched information-regime audit; all output is scoped to this task."""
from pathlib import Path
import datetime as dt
import hashlib
import io
import json
import os
import resource
import socket
import sys
import time
import traceback
import warnings
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
C = ROOT/'campaigns/population_learning_transport_2026-10-28'
OLD = ROOT/'campaigns/learning_rule_transport_2026-10-28'
HISTORY = ROOT/'experiments/matched_history_diagnostic_2026-10-29'
FIXED_STOP = dt.datetime.fromisoformat('2026-11-01T13:35:57+00:00')
sys.dont_write_bytecode = True
os.environ['NUMBA_CACHE_DIR'] = str(OUT/'numba_cache')
sys.path[:0] = [str(C/'code'), str(OLD/'code')]

import numpy as np
from scipy.special import expit, logit
import mixed_reader as reader
import data_io
from rnn_learning import load_rnn
from baselines import load_bank, draw_initial, omission_at
from learning_models import subject_arrays, features
import campaign

MODEL = OLD/'artifacts/rnn/rnnglm32_nested_best.npz'
BANK = OLD/'artifacts/baselines/nested_growth_bank.npz'
FREEZE = C/'protocols/FREEZE.json'
MANIFEST = C/'protocols/SOURCE_FORECASTS.json'
FOLDER = C/'artifacts/forecasts/source'
PINS = {}
ARTIFACT_BYTES = {}


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def dump(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n')


def denied(*args, **kwargs):
    raise PermissionError('No network, unrestricted history loader, or new RNN/prefix fit in this audit')


socket.create_connection = denied
socket.socket.connect = denied
reader.urlopen = denied
reader.acquire = denied
reader.coverage = denied
data_io.load_subject = denied
data_io.prepare_subject = denied


def log(event):
    with (OUT/'EXPOSURE.jsonl').open('a') as f:
        f.write(json.dumps(dict(utc=stamp(), analysis='consumed_same24_information_audit', **event))+'\n')


reader.log = log
data_io.exposure = log


def single_thread_db():
    import duckdb
    return duckdb.connect(config={'threads': 1, 'memory_limit': '96MB',
                                  'temp_directory': str(OUT/'duckdb_tmp')})


reader.db = single_thread_db


def check_bounds():
    if dt.datetime.now(dt.timezone.utc) >= FIXED_STOP:
        raise RuntimeError('Fixed hard deadline reached')
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 800_000_000:
        raise RuntimeError('Peak process RSS cap exceeded; science stops')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_pinned_npz(path, expected=None):
    data = path.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    if expected is not None and h != expected:
        raise RuntimeError('Historical artifact changed: '+str(path))
    PINS[str(path.relative_to(ROOT))] = h
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        decoded = sum(x.file_size for x in z.infolist())
    ARTIFACT_BYTES[str(path.relative_to(ROOT))] = dict(file_bytes=len(data), decoded_bytes=decoded)
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def load_pinned_json(path, expected=None):
    data = path.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    if expected is not None and h != expected:
        raise RuntimeError('Historical JSON changed: '+str(path))
    PINS[str(path.relative_to(ROOT))] = h
    ARTIFACT_BYTES[str(path.relative_to(ROOT))] = dict(file_bytes=len(data), decoded_bytes=len(data))
    return json.loads(data)


def reconstruct_particles(model, prefix, cal, seed):
    """Original fixed uncertainty map evaluated at SAVED w0, without optimization."""
    w0 = np.asarray(cal['w0'])
    p, _, end = model.sequence(prefix, w0)
    center = {'w': np.asarray(cal['endpoint']), 'h': np.asarray(cal['hidden_endpoint'])}
    center_error = max(float(np.max(np.abs(end[k]-center[k]))) for k in center)
    assert center_error < 1e-10
    ds, jw, jh = [], [], []
    for k in range(3):
        delta = np.eye(3)[k]*1e-3
        a, _, ae = model.sequence(prefix, w0+delta)
        b, _, be = model.sequence(prefix, w0-delta)
        ds.append((logit(np.clip(a, 1e-7, 1-1e-7))-logit(np.clip(b, 1e-7, 1-1e-7)))/.002)
        jw.append((ae['w']-be['w'])/.002)
        jh.append((ae['h']-be['h'])/.002)
    Jw, Jh = np.stack(jw, axis=1), np.stack(jh, axis=1)
    D = np.stack(ds, axis=1)
    _, c, _, _ = subject_arrays(prefix)
    ok = c != 0
    fisher = np.einsum('ni,n,nj->ij', D[ok], p[ok]*(1-p[ok]), D[ok])+.5*np.eye(3)
    cov = np.linalg.inv(fisher)
    ev, U = np.linalg.eigh((cov+cov.T)/2)
    cov = np.einsum('ik,k,jk->ij', U, np.clip(ev, 1e-7, 4), U)
    cov0 = np.asarray(cal['initial_covariance'])
    covariance_error = float(np.max(np.abs(cov-cov0)))
    assert covariance_error < 1e-8
    wcov = np.einsum('ik,kl,jl->ij', Jw, cov0, Jw)
    maxev = float(np.max(np.linalg.eigvalsh((wcov+wcov.T)/2)))
    factor = min(1., np.sqrt(4./maxev)) if maxev > 0 else 1.
    assert abs(factor-cal['endpoint_sd_cap_factor']) < 1e-8
    endpoint_cov_error = float(np.max(np.abs(wcov*factor**2-np.asarray(cal['endpoint_covariance']))))
    assert endpoint_cov_error < 1e-8
    # Saved cov0 and factor preserve the original covariance and RNG recipe exactly.
    delta = np.random.default_rng(seed+313).multivariate_normal(np.zeros(3), cov0, size=512)
    delta *= cal['endpoint_sd_cap_factor']
    w = center['w']+delta@Jw.T
    rawh = center['h']+delta@Jh.T
    h = np.clip(rawh, -1, 1)
    clipped = float(np.mean(rawh != h))
    assert clipped == cal['hidden_clipped_fraction']
    return dict(w=w, h=h), dict(center_max_error=center_error,
                               initial_covariance_max_error=covariance_error,
                               endpoint_covariance_max_error=endpoint_cov_error,
                               factor=factor, hidden_clipped_fraction=clipped,
                               no_initial_state_or_optimizer_called=True)


def scalar_step(w, h, s, c, r, day, p):
    """Direct broadcast-and-sum GRU equations, independent of vector einsums."""
    z = np.tanh(5*s)/np.tanh(5.)
    x = np.array([max(z, 0), min(z, 0), 1.])
    pr = float(expit(float(np.sum(w*x))))
    if c == 0:
        return pr, w.copy(), h.copy()
    u = np.r_[w, z, 1., float(day), float(c < 0), float(r > 0), float(z > 0)]
    a = np.sum(p['Wih']*u[None, :], axis=1)+p['bih']
    b = np.sum(p['Whh']*h[None, :], axis=1)+p['bhh']
    ar, au, an = np.split(a, 3)
    br, bu, bn = np.split(b, 3)
    reset, keep = expit(ar+br), expit(au+bu)
    hn = keep*h+(1-keep)*np.tanh(an+reset*bn)
    v = np.maximum(np.sum(p['A']*hn[None, :], axis=1)+p['a'], 0)
    v = np.maximum(np.sum(p['B']*v[None, :], axis=1)+p['b'], 0)
    wn = w+p['scale']*(np.sum(p['C']*v[None, :], axis=1)+p['cc'])
    return pr, wn, hn


def conditional(model, initial, common, future, seed, central_probability, center):
    s, c, r, day = subject_arrays(future)
    state = {k: v.copy() for k, v in initial.items()}
    rng = np.random.default_rng(seed+101)
    probability = np.empty((512, 3000))
    draws = np.empty((512, 3000), np.int8)
    omission = np.stack([omission_at(common, b*500) for b in range(6)], axis=1)
    check_times = set(range(16)) | set(np.flatnonzero(day).tolist()) | {2999}
    check_times |= set(np.flatnonzero(c == 0)[:4].tolist())
    particle_ids = [0, 17, 255, 511]
    maxprob = maxstate = 0.
    checked = omission_checks = 0
    # Zero uncertainty limit: identical copies must retain the saved central path.
    identical = {k: np.broadcast_to(v, (2, len(v))).copy() for k, v in center.items()}
    zero_error = 0.
    for t in range(32):
        p = model.probs(identical, np.full(2, s[t]))
        zero_error = max(zero_error, float(np.max(np.abs(p-central_probability[t]))))
        model.update(identical, s[t], c[t], r[t], session_start=bool(day[t]))
        assert all(np.array_equal(v[0], v[1]) for v in identical.values())
    assert zero_error < 1e-10
    for t in range(3000):
        if t % 500 == 0:
            check_bounds()
        pr = model.probs(state, np.full(512, s[t]))
        probability[:, t] = pr
        choice = np.where(rng.random(512) < pr, -1, 1).astype(np.int8)
        choice[rng.random(512) < omission[:, t//500]] = 0
        draws[:, t] = choice
        before = {k: v.copy() for k, v in state.items()} if t in check_times or c[t] == 0 else None
        model.update(state, s[t], c[t], r[t], session_start=bool(day[t]))
        if c[t] == 0:
            assert all(np.array_equal(before[k], state[k]) for k in state)
            omission_checks += 1
        if t in check_times:
            for j in particle_ids:
                q, w, h = scalar_step(before['w'][j], before['h'][j], s[t], c[t], r[t], day[t], model.params)
                maxprob = max(maxprob, abs(q-pr[j]))
                maxstate = max(maxstate, float(np.max(np.abs(w-state['w'][j]))),
                               float(np.max(np.abs(h-state['h'][j]))))
                checked += 1
    assert np.isfinite(probability).all() and np.all((probability >= 0) & (probability <= 1))
    assert all(np.isfinite(v).all() for v in state.values())
    assert maxprob < 1e-10 and maxstate < 1e-10
    sampled = np.empty((512, 6, 2))
    analytic = np.empty_like(sampled)
    counts = np.empty((6, 2), int)
    for b in range(6):
        for j, side in enumerate((-1, 1)):
            take = np.flatnonzero(np.isclose(s[b*500:(b+1)*500], side, rtol=0, atol=1e-9))+b*500
            counts[b, j] = len(take)
            assert len(take) > 0
            sampled[:, b, j] = (draws[:, take] == -side).mean(1)
            pc = probability[:, take] if side == 1 else 1-probability[:, take]
            analytic[:, b, j] = ((1-omission[:, b, None])*pc).mean(1)
    # Independent scalar summation of four representative particle endpoint cells.
    summary_error = 0.
    for j in particle_ids:
        for b in (0, 5):
            for side_index, side in enumerate((-1, 1)):
                ix = [t for t in range(500*b, 500*(b+1)) if abs(s[t]-side) <= 1e-9]
                q = sum(int(draws[j, t] == -side) for t in ix)/len(ix)
                a = sum((1-omission[j, b])*(probability[j, t] if side == 1 else 1-probability[j, t]) for t in ix)/len(ix)
                summary_error = max(summary_error, abs(q-sampled[j, b, side_index]),
                                    abs(a-analytic[j, b, side_index]))
    assert summary_error < 1e-12
    return dict(prob_right=probability, scoring_choice=draws, omission_by_particle_bin=omission,
                conditional_sampled_sides=sampled, conditional_analytic_sides=analytic,
                actual_signed_contrast=s, actual_choice=c, actual_feedback_positive=r,
                actual_session_start=day, counts=counts,
                initial_w=initial['w'], initial_h=initial['h'],
                final_w=state['w'], final_h=state['h']), dict(
                    scalar_transitions=checked, max_scalar_probability_error=maxprob,
                    max_scalar_state_error=maxstate, omission_invariance_opportunities=omission_checks,
                    identical_state_zero_uncertainty_max_error=zero_error,
                    max_scalar_summary_error=summary_error)


def score(target, prediction, labs):
    residual = target.mean(2)-prediction.mean(2)
    return dict(population_curve_mae_pp=float(100*np.abs(residual.mean(0)).mean()),
                individual_curve_mae_pp=float(100*np.abs(residual).mean()),
                individual_side_curve_mae_pp=float(100*np.abs(target-prediction).mean()),
                scalar_bias_observed_minus_prediction_pp=float(100*residual.mean()),
                cohort_curve_percent=(100*prediction.mean((0, 2))).tolist(),
                cohort_signed_residual_pp=(100*residual.mean(0)).tolist(),
                individual_curve_mae_pp_by_animal=(100*np.abs(residual).mean(1)).tolist(),
                lab_curve_mae_pp={lab: float(100*np.abs(residual[labs == lab].mean(0)).mean())
                                  for lab in sorted(set(labs))})


def summarize(target, central, auto, sampled, analytic, labs):
    predictions = dict(saved_central_analytic=central, saved_autonomous_sampled=auto.mean(1),
                       conditional_mixture_sampled=sampled.mean(1),
                       conditional_mixture_analytic=analytic.mean(1))
    metrics = {k: score(target, v, labs) for k, v in predictions.items()}
    rng = np.random.default_rng(20261029)
    ix = rng.integers(0, 24, (20000, 24))
    actual = target.mean(2)
    a = predictions['saved_autonomous_sampled'].mean(2)
    comparisons = {}
    for kind in ('conditional_mixture_sampled', 'conditional_mixture_analytic', 'saved_central_analytic'):
        c = predictions[kind].mean(2)
        pop = 100*(np.abs((actual-a)[ix].mean(1)).mean(1)-np.abs((actual-c)[ix].mean(1)).mean(1))
        indiv = 100*((np.abs(actual-a).mean(1)-np.abs(actual-c).mean(1))[ix].mean(1))
        loo = {}
        for lab in sorted(set(labs)):
            use = labs != lab
            loo[lab] = float(100*(np.abs((actual-a)[use].mean(0)).mean()-np.abs((actual-c)[use].mean(0)).mean()))
        comparisons[kind] = dict(population_mae_gain_pp=float(metrics['saved_autonomous_sampled']['population_curve_mae_pp']-metrics[kind]['population_curve_mae_pp']),
                                paired_animal_percentile95_pp=np.quantile(pop, [.025, .975]).tolist(),
                                individual_mae_gain_pp=float(metrics['saved_autonomous_sampled']['individual_curve_mae_pp']-metrics[kind]['individual_curve_mae_pp']),
                                individual_paired_animal_percentile95_pp=np.quantile(indiv, [.025, .975]).tolist(),
                                leave_one_lab_out_population_gain_pp=loo)
    # Monte Carlo uncertainty of the finite 512-particle numerical mixture, conditional on fixed histories.
    # Resample whole paired particle paths within each animal; no animal resampling in this calculation.
    rng = np.random.default_rng(20261101)
    bootstrap_auto = np.zeros((2000, 6))
    bootstrap_sampled = np.zeros_like(bootstrap_auto)
    bootstrap_analytic = np.zeros_like(bootstrap_auto)
    for i in range(24):
        for lo in range(0, 2000, 100):
            idx = rng.integers(0, 512, (100, 512))
            for values, accumulated in ((auto, bootstrap_auto), (sampled, bootstrap_sampled),
                                         (analytic, bootstrap_analytic)):
                accumulated[lo:lo+100] += values[i].mean(2)[idx].mean(1)/24
    truth = actual.mean(0)
    mae_auto = 100*np.abs(bootstrap_auto-truth).mean(1)
    mae_sampled = 100*np.abs(bootstrap_sampled-truth).mean(1)
    mae_analytic = 100*np.abs(bootstrap_analytic-truth).mean(1)
    mc = dict(draws=2000, seed=20261101, conditioning='fixed actual histories and fitted recipe; whole paired particles within each animal',
              sampled_gap_percentile95_pp=np.quantile(mae_auto-mae_sampled, [.025, .975]).tolist(),
              analytic_gap_percentile95_pp=np.quantile(mae_auto-mae_analytic, [.025, .975]).tolist(),
              auto_population_curve_se_pp=(100*bootstrap_auto.std(0, ddof=1)).tolist(),
              conditional_sampled_population_curve_se_pp=(100*bootstrap_sampled.std(0, ddof=1)).tolist(),
              conditional_analytic_population_curve_se_pp=(100*bootstrap_analytic.std(0, ddof=1)).tolist(),
              scoring_noise_cohort_curve_difference_pp=(100*(sampled.mean((0, 1, 3))-analytic.mean((0, 1, 3)))).tolist(),
              state_mixture_minus_central_cohort_curve_pp=(100*(analytic.mean((0, 1, 3))-central.mean((0, 2)))).tolist(),
              finite_particle_estimate_not_biological_interval=True)
    np.savez_compressed(OUT/'UNCERTAINTY_DRAWS.npz',
                        paired_animal_population_gain_sampled=100*(
                            np.abs((actual-a)[ix].mean(1)).mean(1)-
                            np.abs((actual-predictions['conditional_mixture_sampled'].mean(2))[ix].mean(1)).mean(1)),
                        particle_bootstrap_autonomous_curve=bootstrap_auto,
                        particle_bootstrap_conditional_sampled_curve=bootstrap_sampled,
                        particle_bootstrap_conditional_analytic_curve=bootstrap_analytic)
    return dict(metrics=metrics, comparisons=comparisons, monte_carlo=mc,
                observed_cohort_curve_percent=(100*target.mean((0, 2))).tolist())


def main():
    start = time.monotonic()
    check_bounds()
    plan = json.loads((OUT/'RESOURCE_PLAN.json').read_text())
    assert plan['total_conservative_planned_charge_bytes'] < 400_000_000
    freeze_before = campaign.verify_freeze(FREEZE)
    original_pins = load_pinned_json(HISTORY/'SOURCE_PINS.json')['artifacts']
    first = load_pinned_json(OUT/'FIRST_CALCULATION.json')
    curves = load_pinned_npz(HISTORY/'CURVES.npz', first['pins'][str((HISTORY/'CURVES.npz').relative_to(ROOT))])
    subjects = curves['subjects'].tolist()
    labs = curves['labs']
    assert subjects == freeze_before['source_primary_subjects'] and len(subjects) == 24
    assert not {'NYU-21', 'SWC_007'} & set(subjects)
    original_read = reader._read
    def capped_read(subject, stop):
        if subject not in subjects or int(stop) != 4000:
            raise PermissionError('Only same24 first4000 allowed')
        return original_read(subject, 4000)
    reader._read = capped_read
    model = load_rnn(MODEL)
    model.initial_state = denied
    bank = load_bank(BANK)
    assert digest(MODEL) == 'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940'
    assert digest(BANK) == '036f3cfedd56e915b051fb29a80a2622cf5a747366ea31aa46b9249a922eea01'
    predictions = OUT/'predictions'
    predictions.mkdir(exist_ok=True)
    auto, sampled, analytic, audits, complete = [], [], [], [], []
    dump('FROZEN_DESIGN.json', dict(utc=stamp(), design_sha256=digest(OUT/'DESIGN.md'),
                                  run_code_sha256=digest(Path(__file__)),
                                  resource_plan_sha256=digest(OUT/'RESOURCE_PLAN.json'),
                                  strict_freeze_sha256=digest(FREEZE),
                                  original_model_sha256=digest(MODEL),
                                  subjects=subjects, new_scores_computed=False))
    for i, subject in enumerate(subjects):
        t0 = time.monotonic()
        check_bounds()
        seed = int(hashlib.sha256(subject.encode()).hexdigest()[:8], 16) % (2**31-1)
        def oldpin(path):
            return original_pins[str(path.relative_to(ROOT))]
        meta_path = FOLDER/(subject+'__rnn.json')
        meta = load_pinned_json(meta_path, oldpin(meta_path))
        assert meta['particles'] == 512 and meta['horizon'] == 3000
        ppath = FOLDER/(subject+'__prefix.npz')
        z = load_pinned_npz(ppath, meta['prefix_sha256'])
        starts = z.pop('future_session_start')
        prefix = z
        history_path = HISTORY/(subject+'__conditional.npz')
        historical = load_pinned_npz(history_path, first['pins'][str(history_path.relative_to(ROOT))])
        opath = FOLDER/(subject+'__observed.npz')
        observed = load_pinned_npz(opath, oldpin(opath))
        apath = FOLDER/(subject+'__rnn.npz')
        autonomous = load_pinned_npz(apath, oldpin(apath))
        full = reader.load_scored(subject, stop=4000, freeze_path=FREEZE,
                                  forecast_manifest=MANIFEST,
                                  purpose='Postvalidation same24 matched averaging; consumed first4000 only')
        assert len(full['choice']) == 4000
        for k, v in prefix.items():
            if isinstance(v, np.ndarray) and v.ndim and len(v) == 1000:
                assert np.array_equal(v, full[k][:1000], equal_nan=True), k
        future = {k: v[1000:4000] for k, v in full.items()
                  if isinstance(v, np.ndarray) and v.ndim and len(v) == 4000}
        assert np.array_equal(starts, future['session_start'])
        s, c, _, _ = subject_arrays(future)
        raw_y, raw_n = campaign.summarize(s, c)
        assert np.array_equal(raw_y[0], observed['observed'])
        assert np.array_equal(raw_n[0], observed['counts'])
        assert np.array_equal(raw_y[0, :, :2], curves['observed_sides'][i])
        state, reconstruction = reconstruct_particles(model, prefix, meta['calibration'], seed)
        common = draw_initial(prefix, bank, 512, seed+211, exclude=subject, competence='growth')
        omission = np.stack([omission_at(common, b*500) for b in range(6)], axis=1)
        omit_error = float(np.max(np.abs(omission.mean(0)-historical['p_omit'].reshape(6, 500)[:, 0])))
        assert omit_error < 1e-12
        # Exact-recipe replay links recovered initial particles to the historical autonomous forecast.
        replay = campaign.simulate(model, prefix, starts, common, state, None, 'rnn', 'standard', seed)
        assert np.array_equal(replay['samples'], autonomous['samples'])
        assert np.array_equal(replay['counts'], autonomous['counts'])
        weight_error = float(np.max(np.abs(replay['weights']-autonomous['weights'])))
        hidden_error = float(np.max(np.abs(replay['hidden_final']-autonomous['hidden_final'])))
        assert weight_error < 1e-8 and hidden_error < 1e-8
        assert np.max(np.abs(autonomous['samples'].mean(0)[:, :2]-curves['autonomous_rnn'][i])) < 1e-14
        center = dict(w=np.asarray(meta['calibration']['endpoint']), h=np.asarray(meta['calibration']['hidden_endpoint']))
        out, checks = conditional(model, state, common, future, seed, historical['prob_right'], center)
        assert np.array_equal(out['counts'], observed['counts'][:, :2])
        out['observed_sides'] = raw_y[0, :, :2]
        # Full per-trial probabilities, actual inputs and generated scoring choices precede new cohort scores.
        path = predictions/(subject+'.npz')
        np.savez_compressed(path, **out)
        complete.append(dict(subject=subject, path=str(path.relative_to(ROOT)), bytes=path.stat().st_size,
                             full_file_sha256='UNRUN: avoid rereading large generated trial arrays',
                             sampled_side_array_sha256=hashlib.sha256(out['conditional_sampled_sides'].tobytes()).hexdigest(),
                             analytic_side_array_sha256=hashlib.sha256(out['conditional_analytic_sides'].tobytes()).hexdigest()))
        auto.append(autonomous['samples'][:, :, :2])
        sampled.append(out['conditional_sampled_sides'])
        analytic.append(out['conditional_analytic_sides'])
        audit = dict(subject=subject, lab=str(labs[i]), reconstructed_joint_prefix=reconstruction,
                     exact_autonomous_samples_and_counts=True, autonomous_weight_max_error=weight_error,
                     autonomous_hidden_max_error=hidden_error, omission_mean_max_error=omit_error,
                     raw_prefix_targets_counts_session_equal=True, checks=checks,
                     seconds=time.monotonic()-t0,
                     peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        audits.append(audit)
        dump('PREDICTION_MANIFEST.json', dict(utc=stamp(), complete=complete,
                                           completed=len(complete), intended=24, new_cohort_scores_computed=False))
        dump('AUDIT.json', dict(utc=stamp(), records=audits))
        dump('STATE.json', dict(utc=stamp(), status='running', complete_animals=len(complete),
                               active_process=os.getpid(), fixed_stop=FIXED_STOP.isoformat()))
        print(json.dumps(dict(subject=subject, completed=len(complete), replay_exact=True,
                              seconds=audit['seconds'], peak_rss_bytes=audit['peak_rss_bytes'])), flush=True)
        del out, full, future, replay, autonomous, prefix, historical, observed
    auto, sampled, analytic = np.array(auto), np.array(sampled), np.array(analytic)
    # Save all endpoint predictions before any new scores.
    np.savez_compressed(OUT/'MATCHED_PREDICTIONS.npz', subjects=np.array(subjects), labs=labs,
                        observed_sides=curves['observed_sides'],
                        saved_central_analytic=curves['conditional_rnn'],
                        saved_autonomous_particles=auto,
                        conditional_sampled_particles=sampled,
                        conditional_analytic_particles=analytic)
    dump('PREDICTION_MANIFEST.json', dict(utc=stamp(), complete=complete, completed=24, intended=24,
                                       endpoint_file_sha256=digest(OUT/'MATCHED_PREDICTIONS.npz'),
                                       new_cohort_scores_computed=False))
    check_bounds()
    result = summarize(curves['observed_sides'], curves['conditional_rnn'], auto, sampled, analytic, labs)
    freeze_after = campaign.verify_freeze(FREEZE)
    assert freeze_after == freeze_before
    # All relevant input pins rechecked at endpoint, still without reopening raw data.
    for path, h in PINS.items():
        assert digest(ROOT/path) == h, path
    artifact_charge = sum(v['file_bytes']+v['decoded_bytes'] for v in ARTIFACT_BYTES.values())
    artifact_rehash = sum(v['file_bytes'] for v in ARTIFACT_BYTES.values())
    # Plan's 80MB allowance covers artifact reads/rehashes, model-bank loads and small output pins.
    assert artifact_charge+artifact_rehash < 65_000_000
    resources = dict(utc=stamp(), conservative_total_charge_bytes=plan['total_conservative_planned_charge_bytes'],
                     cap_bytes=400_000_000, peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                     peak_cap_bytes=800_000_000, one_process_one_numerical_thread=True,
                     network_operations=0, ingress_bytes=0, newly_returned_raw_rows=96000,
                     new_unique_observations=0, original_rows_per_animal=4000,
                     containing_parquet_block_or_physical_io_unknown=True,
                     strict_freeze_passes=2, strict_freeze_bytes=plan['two_strict_freeze_passes_bytes'],
                     input_artifact_read_decode_bytes=artifact_charge,
                     input_artifact_terminal_rehash_bytes=artifact_rehash,
                     input_artifact_allowance_bytes=80_000_000,
                     metadata_and_raw_plan=plan, elapsed_seconds=time.monotonic()-start,
                     final_input_pins=PINS, input_artifacts=ARTIFACT_BYTES,
                     generated_full_probability_file_hashes_unrun=True)
    assert resources['peak_process_rss_bytes'] < 800_000_000
    result.update(utc=stamp(), status='completed_postvalidation_matched_information_audit',
                  animals=24, prefix=1000, future=3000, particle_count=512,
                  endpoint='six500 bins, exact±100%, omissions failures, equal side/animal',
                  no_new_learning_or_prefix_state_fit=True,
                  original_fixed_prefix_omission_nuisance_replayed=True,
                  no_protected_or_excluded_animal_access=True,
                  strict_freeze_before_after_unchanged=True,
                  all24_autonomous_samples_counts_exact=True,
                  matched_initial_states_and_response_draw_stream=True,
                  prediction_manifest_saved_before_scores=True,
                  postvalidation=True, original_gates_unchanged=True)
    dump('RESULT.json', result)
    dump('RESOURCES.json', resources)
    dump('SOURCE_PINS.json', dict(utc=stamp(), inputs=PINS, design_sha256=digest(OUT/'DESIGN.md'),
                                  run_code_sha256=digest(Path(__file__))))
    dump('STATE.json', dict(utc=stamp(), status='completed', complete_animals=24, jobs=0,
                           elapsed_seconds=time.monotonic()-start))
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    with (OUT/'RUN_STDOUT.log').open('w', buffering=1) as stdout_log, (OUT/'RUN_STDERR.log').open('w', buffering=1) as stderr_log:
        class Tee:
            def __init__(self, terminal, log):
                self.terminal, self.log = terminal, log
            def write(self, value):
                self.terminal.write(value)
                self.log.write(value)
            def flush(self):
                self.terminal.flush()
                self.log.flush()
        sys.stdout = Tee(sys.stdout, stdout_log)
        sys.stderr = Tee(sys.stderr, stderr_log)
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                main()
                dump('WARNINGS.json', [dict(category=x.category.__name__, message=str(x.message),
                                             filename=x.filename, lineno=x.lineno) for x in caught])
        except Exception as error:
            traceback.print_exc()
            dump('STOP.json', dict(utc=stamp(), exception=repr(error), traceback=traceback.format_exc(),
                                   peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                   fixed_stop=FIXED_STOP.isoformat(), no_further_science_until_assessed=True))
            raise
