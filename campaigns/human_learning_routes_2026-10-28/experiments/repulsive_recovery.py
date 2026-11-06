"""Post-validation generator-adequacy audit; frozen prediction procedure reused.

This supplementary simulator is oriented by DEVELOPMENT shared-model history
and previous-choice coefficients. It does not fit, change or tune the primary
model, its windows, metrics, split or protected-data analysis. All responses
used here are newly simulated. Previous attractive-generator results remain.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.optimize import brentq

from recovery import load_inputs, windows_arrays, expected_history, analyze_simulated, summarize

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {
    'shared_commonlaw': dict(target=0., shape=[0., 0., 1.]),
    'slow_plus05': dict(target=.05, shape=[0., 0., 1.]),
    'slow_minus05': dict(target=-.05, shape=[0., 0., -1.]),
    'redistribution_plus05': dict(target=.05, shape=[-1., 0., 1.]),
}


def development_anchor():
    source = ROOT / 'outputs/development/shared_tight.json'
    obj = json.loads(source.read_text())
    coef = dict(zip(obj['feature_names'], obj['beta']))
    return dict(history=[coef[f'history_tau{k}'] for k in (2, 8, 32)],
                previous_choice=coef['previous_choice'],
                condition_previous_choice=coef['condition:previous_choice'],
                source=str(source.relative_to(ROOT)),
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                qualification='Selected development mean coefficients orient one supplementary generator; this is not a validated full generative model of the human data.')


def simulate(inputs, scenario, seed, shift_scale, anchor):
    rng = np.random.default_rng(seed)
    spec = SCENARIOS[scenario]
    people = inputs[['subject', 'schedule', 'instructions', 'partition']].drop_duplicates()
    n = len(people)
    side = inputs.stimSide.to_numpy(float).reshape(n, 600)
    contrast = inputs.sideContrast.to_numpy(float).reshape(n, 600)
    group0 = people.instructions.to_numpy(float)
    group = group0 - .5
    u = rng.normal(0., .55, n)
    bias = .2 * group + rng.normal(0., .35, n)
    motor = anchor['previous_choice'] + anchor['condition_previous_choice'] * group + rng.normal(0., .12, n)
    kernel = np.tile(np.asarray(anchor['history']), (n, 1)) + rng.normal(0., .45, (n, 3))
    schedule_effect = {s: rng.normal(0., .16, 3) for s in sorted(people.schedule.unique())}
    kernel += np.stack([schedule_effect[s] for s in people.schedule])
    shared_skill = u + (.23 / .22) * group
    kernel += shared_skill[:, None] * np.asarray([.12, .25, .65])
    h = np.zeros((n, 3))
    previous = np.zeros(n)
    choices = np.zeros((n, 600))
    feedback = np.full((n, 600), np.nan)
    truth_shift = np.zeros((n, 600))
    history_component = np.zeros((n, 600))
    true_zero_prob = np.zeros((n, 600))
    decay = np.exp(-1. / np.asarray([2., 8., 32.]))
    delta = shift_scale * np.asarray(spec['shape'])
    for t in range(600):
        acquisition = 1. - (.12 + .78 * (1. - group0)) * np.exp(-t / (35. + 80. * (1. - group0)))
        skill = np.clip(1. + .23 * group + .22 * u, .3, 1.8) * acquisition
        c = contrast[:, t]
        sensory = np.zeros(n)
        for level, coefficient in [(0.1, .4), (.25, .8), (.5, 1.6), (1., 2.7)]:
            sensory += np.sign(c) * np.isclose(np.abs(c), level) * coefficient * skill
        dynamic = np.asarray([.05, .18, -.20]) * ((t - 399.5) / 200.)
        drift = .18 * np.sin(t / 95.) + .12 * u * (t - 300.) / 300.
        nonhistory = bias + motor * previous + drift
        hist_term = np.einsum('ij,ij->i', h, kernel + dynamic)
        baseline = nonhistory + hist_term
        lapse = np.clip(.07 - .04 * group + .13 * (1. - group0) * np.exp(-t / 70.), .01, .3)
        shift = np.einsum('ij,j->i', h, delta if t >= 200 else np.zeros(3))
        p = .5 * lapse + (1. - lapse) * expit(sensory + baseline + group * shift)
        truth_shift[:, t] = (1. - lapse) * (expit(baseline + .5 * shift) - expit(baseline - .5 * shift))
        true_zero_prob[:, t] = .5 * lapse + (1. - lapse) * expit(baseline + group * shift)
        history_component[:, t] = (1. - lapse) * (expit(baseline + group * shift) - expit(nonhistory))
        ch = np.where(rng.random(n) < p, 1., -1.)
        omit_prob = .008 + .007 * (1. - group0) + .04 * (1. - group0) * np.exp(-t / 45.)
        omit = rng.random(n) < omit_prob
        ch[omit] = 0.
        fb = ch * side[:, t]
        fb[omit] = np.nan
        choices[:, t], feedback[:, t] = ch, fb
        h = decay * h + (1. - decay) * np.where(omit, 0., side[:, t])[:, None]
        previous = ch
    out = inputs.copy()
    out['choice'], out['feedbackType'] = choices.ravel(), feedback.ravel()
    old, mask, primary = windows_arrays(inputs)
    valid = people.partition.str.startswith('validation').to_numpy()
    def person_mean(a):
        return np.array([np.mean(a[i][mask[i]]) for i in range(n)])
    effect = person_mean(old * truth_shift)
    component = person_mean(old * history_component)
    oldprob = person_mean(np.where(old == 1., true_zero_prob, 1. - true_zero_prob))
    truth = dict(mean=float(effect[valid].mean()),
                 rms=float(np.sqrt(person_mean(truth_shift ** 2)[valid].mean())),
                 per_subject={str(s): float(v) for s, v in zip(people.subject, effect)},
                 shift_scale=float(shift_scale), generator_seed=int(seed),
                 zero_history_component=float(component[valid].mean()),
                 zero_old_choice_probability=float(oldprob[valid].mean()),
                 mean_later_accuracy=float(np.mean((choices[:, 200:] == side[:, 200:])[choices[:, 200:] != 0])),
                 omission_rate=float(np.mean(choices == 0.)))
    return out, truth


def calibrate(inputs, scenario, anchor):
    spec = SCENARIOS[scenario]
    if spec['target'] == 0.:
        return dict(scale=0., expected_effect=0., refinement=[])
    n = inputs.subject.nunique()
    hist = expected_history(inputs.stimSide.to_numpy(float).reshape(n, 600))
    people = inputs[['subject', 'partition', 'instructions']].drop_duplicates()
    valid = people.partition.str.startswith('validation').to_numpy()
    group = people.instructions.to_numpy(float) - .5
    old, mask, _ = windows_arrays(inputs)
    base = np.einsum('itk,k->it', hist, np.asarray(anchor['history'])) + .2 * group[:, None]
    hshape = np.einsum('itk,k->it', hist, np.asarray(spec['shape']))
    lapse = .07 - .04 * group[:, None]
    def effect(scale):
        change = (1. - lapse) * (expit(base + .5 * scale * hshape) - expit(base - .5 * scale * hshape))
        return float(np.mean([np.mean((old[i] * change[i])[mask[i]]) for i in np.where(valid)[0]]))
    scale = brentq(lambda a: effect(a) - spec['target'], .001, 30.)
    initial = float(scale)
    records = []
    index = list(SCENARIOS).index(scenario)
    for step in range(4):
        means = [simulate(inputs, scenario, 87100000 + 10000 * index + k, scale, anchor)[1]['mean'] for k in range(10)]
        current = float(np.mean(means))
        records.append(dict(step=step, scale=float(scale), mean_effect=current))
        if abs(current - spec['target']) < .0001 or step == 3:
            break
        scale *= spec['target'] / current
    return dict(scale=float(scale), initial_scale=initial, expected_effect=current, refinement=records)


def one_job(inputs, scenario, rep, scale, anchor):
    seed = 502610280 + 10000 * list(SCENARIOS).index(scenario) + rep
    begin = time.monotonic()
    frame, truth = simulate(inputs, scenario, seed, scale, anchor)
    result, scores, _ = analyze_simulated(frame, truth, seed, effect_bootstraps=0)
    row = dict(scenario=scenario, replicate=rep, seed=seed, seconds=time.monotonic() - begin,
               zero_history_component=truth['zero_history_component'],
               zero_old_choice_probability=truth['zero_old_choice_probability'],
               mean_later_accuracy=truth['mean_later_accuracy'], omission_rate=truth['omission_rate'], **result)
    return row, scores, truth


def run(args):
    start = time.monotonic()
    out = ROOT / 'outputs/repulsive_recovery' / args.label
    out.mkdir(parents=True, exist_ok=True)
    inputs, split = load_inputs()
    anchor = development_anchor()
    source_names = ['model.py', 'analysis.py', 'recovery.py']
    frozen_hashes = {f: hashlib.sha256((ROOT/'experiments'/f).read_bytes()).hexdigest() for f in source_names}
    definitions = {}
    for scenario in SCENARIOS:
        definitions[scenario] = dict(**SCENARIOS[scenario], **calibrate(inputs, scenario, anchor))
    manifest = dict(status='running', status_of_analysis='post-validation supplementary generator adequacy audit',
                    anchor=anchor, scenarios=definitions, args=vars(args), seeds='502610280+10000*scenario_index+replicate',
                    validation_outcomes_used='None; only selected DEVELOPMENT mean coefficients orient generator. All choice/feedback responses generated.',
                    changes_from_original_generator='Shared history mean and previous-choice mean/group coefficient only. Common sensory-history law, heterogeneity, schedule effects, lapse/omission and nonstationarity retained.',
                    inference_limit='Conditional recovery under one development-oriented generator, not validated empirical task power or a new protected-data analysis.',
                    frozen_imported_source_sha256=frozen_hashes,
                    input_sha256=hashlib.sha256((ROOT/'outputs/input_only/trial_inputs.csv').read_bytes()).hexdigest(),
                    split_sha256=hashlib.sha256((ROOT/'protocol/split_manifest.csv').read_bytes()).hexdigest())
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(one_job,inputs,s,rep,definitions[s]['scale'],anchor)
                   for rep in range(args.reps) for s in SCENARIOS]
        for future in as_completed(futures):
            row, scores, truth = future.result()
            rows.append(row)
            pd.DataFrame(rows).sort_values(['scenario','replicate']).to_csv(out/'replicates.csv',index=False)
            key=f"{row['scenario']}_{row['replicate']:03d}"
            scores.to_csv(out/f'scores_{key}.csv',index=False)
            (out/f'truth_{key}.json').write_text(json.dumps(truth,indent=2)+'\n')
            (out/'summary.json').write_text(json.dumps(summarize(pd.DataFrame(rows)),indent=2)+'\n')
            print(json.dumps({k:row[k] for k in ['scenario','replicate','truth_effect','effect','delta_log','score_detect','seconds']}),flush=True)
    after = {f:hashlib.sha256((ROOT/'experiments'/f).read_bytes()).hexdigest() for f in source_names}
    assert after==frozen_hashes, 'Frozen imported source changed while supplementary audit ran'
    manifest.update(status='complete',elapsed_seconds=time.monotonic()-start,all_converged=bool(pd.DataFrame(rows).convergence.all()))
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(summarize(pd.DataFrame(rows)),indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--reps',type=int,default=100)
    p.add_argument('--workers',type=int,default=2)
    p.add_argument('--label',default='supplementary')
    run(p.parse_args())
