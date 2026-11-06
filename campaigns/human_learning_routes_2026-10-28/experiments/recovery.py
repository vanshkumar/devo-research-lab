"""Scientific recovery on the actual input-only schedules and locked split.

Never opens real choice/feedback data. The simulator creates all outcomes.
The scenarios were specified before protected validation responses were opened.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import expit

from model import (ModelConfig, FeatureData, prepare_features, fit_model,
                   predict_model, log_score, CALIBRATION_NAMES)
from analysis import windows, standardized_effect

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {
    'nuisance_null': dict(target=0., shape=[0., 0., 1.], shared_law=False),
    'carryover_null': dict(target=0., shape=[0., 0., 1.], shared_law=True),
    'slow_05': dict(target=.05, shape=[0., 0., 1.], shared_law=True),
    'slow_10': dict(target=.10, shape=[0., 0., 1.], shared_law=True),
    'shape_05': dict(target=.05, shape=[-1., 0., 1.], shared_law=True),
    'slow_minus05': dict(target=-.05, shape=[0., 0., -1.], shared_law=True),
}


def load_inputs():
    source = ROOT / 'outputs/input_only/trial_inputs.csv'
    inputs = pd.read_csv(source, dtype={'subject': str, 'session': str})
    assert not {'choice', 'feedbackType', 'response_times_from_stim'} & set(inputs.columns)
    split = pd.read_csv(ROOT / 'protocol/split_manifest.csv', dtype={'subject': str})
    inputs = inputs.merge(split[['subject', 'partition']], on='subject', validate='many_to_one')
    return inputs.sort_values(['subject', 'trial']).reset_index(drop=True), split


def windows_arrays(inputs):
    w = windows(inputs)
    n = w.subject.nunique()
    return (w.old_majority.to_numpy().reshape(n, 600),
            ((w.switch_offset < 20) & (w.trial >= 200)).to_numpy().reshape(n, 600),
            w.primary.to_numpy().reshape(n, 600))


def expected_history(side):
    n = len(side)
    out = np.zeros((n, 600, 3))
    decay = np.exp(-1. / np.asarray([2., 8., 32.]))
    h = np.zeros((n, 3))
    for t in range(600):
        out[:, t] = h
        h = decay * h + (1. - decay) * side[:, t, None]
    return out


def calibrate_shift(inputs, scenario):
    spec = SCENARIOS[scenario]
    if spec['target'] == 0:
        return 0., 0.
    n = inputs.subject.nunique()
    hist = expected_history(inputs.stimSide.to_numpy(float).reshape(n, 600))
    old, mask, _ = windows_arrays(inputs)
    ids = inputs[['subject', 'partition', 'instructions']].drop_duplicates()
    valid = ids.partition.str.startswith('validation').to_numpy()
    group = ids.instructions.to_numpy(float) - .5
    # Fixed population mean, no random draw or actual response. All nonhistory
    # terms remain held fixed across the group-history counterfactual.
    base = np.einsum('itk,k->it', hist, np.asarray([0., .35, .9])) + .2 * group[:, None]
    lapse = .07 - .04 * group[:, None]
    hshape = np.einsum('itk,k->it', hist, np.asarray(spec['shape']))
    def effect(scale):
        shift = (1. - lapse) * (expit(base + .5 * scale * hshape) - expit(base - .5 * scale * hshape))
        return float(np.mean([np.mean((old[i] * shift[i])[mask[i]]) for i in np.where(valid)[0]]))
    scale = brentq(lambda a: effect(a) - spec['target'], .001, 30.)
    return float(scale), effect(scale)


def simulate(inputs, scenario, seed, shift_scale):
    """Subject and schedule random effects, nonstationarity and omissions.

    True feedback is determined by scheduled target and simulated response.
    No-response trials deliver no feedback. A lapse mixture is generated even
    though the fitted psychometric flexibility is phenomenological.
    """
    rng = np.random.default_rng(seed)
    spec = SCENARIOS[scenario]
    subjects = inputs[['subject', 'schedule', 'instructions', 'partition']].drop_duplicates()
    n = len(subjects)
    side = inputs.stimSide.to_numpy(float).reshape(n, 600)
    contrast = inputs.sideContrast.to_numpy(float).reshape(n, 600)
    group0 = subjects.instructions.to_numpy(float)
    group = group0 - .5
    u = rng.normal(0., .55, n)
    bias = .2 * group + rng.normal(0., .35, n)
    motor = .25 + .25 * group + rng.normal(0., .12, n)
    shared_kernel = np.tile(np.array([0., .35, .9]), (n, 1)) + rng.normal(0., .45, (n, 3))
    schedules = sorted(subjects.schedule.unique())
    schedule_effect = {s: rng.normal(0., .16, 3) for s in schedules}
    shared_kernel += np.stack([schedule_effect[s] for s in subjects.schedule])
    if spec['shared_law']:
        # Same law of latent sensory skill in both groups. Because the sensory
        # distributions differ, the marginal history distributions can differ
        # even with no direct condition-history coefficient. Noisy first200
        # calibration must account for this as well as it can.
        shared_skill = u + (.23 / .22) * group
        shared_kernel += shared_skill[:, None] * np.asarray([.12, .25, .65])
    # Sensory skill and latent adaptation can share a common person-dependent
    # relationship without a direct condition coefficient in the null.
    h = np.zeros((n, 3))
    previous = np.zeros(n)
    choices = np.zeros((n, 600))
    feedback = np.full((n, 600), np.nan)
    truth_shift = np.zeros((n, 600))
    true_p = np.zeros((n, 600))
    decay = np.exp(-1. / np.asarray([2., 8., 32.]))
    delta = shift_scale * np.asarray(spec['shape'])
    for t in range(600):
        acquisition = 1. - (.12 + .78 * (1. - group0)) * np.exp(-t / (35. + 80. * (1. - group0)))
        skill = np.clip(1. + .23 * group + .22 * u, .3, 1.8) * acquisition
        c = contrast[:, t]
        sensory = np.zeros(n)
        for level, coefficient in [(0.1, .4), (.25, .8), (.5, 1.6), (1., 2.7)]:
            sensory += np.sign(c) * np.isclose(np.abs(c), level) * coefficient * skill
        dynamic = np.zeros((n, 3))
        drift = np.zeros(n)
        if spec['shared_law']:
            dynamic = np.tile(np.asarray([.05, .18, -.20]) * ((t - 399.5) / 200.), (n, 1))
            drift = .18 * np.sin(t / 95.) + .12 * u * (t - 300.) / 300.
        baseline = bias + motor * previous + drift + np.einsum('ij,ij->i', h, shared_kernel + dynamic)
        lapse = np.clip(.07 - .04 * group + .13 * (1. - group0) * np.exp(-t / 70.), .01, .3)
        # The persistent manipulation begins in the later target interval, so
        # calibration accuracy cannot become a surrogate manipulation label.
        delta_t = delta if t >= 200 else np.zeros(3)
        shift = np.einsum('ij,j->i', h, delta_t)
        p = .5 * lapse + (1. - lapse) * expit(sensory + baseline + group * shift)
        true_p[:, t] = p
        truth_shift[:, t] = (1. - lapse) * (expit(baseline + .5 * shift) - expit(baseline - .5 * shift))
        ch = np.where(rng.random(n) < p, 1., -1.)
        omit_prob = .008 + .007 * (1. - group0) + .04 * (1. - group0) * np.exp(-t / 45.)
        omit = rng.random(n) < omit_prob
        ch[omit] = 0.
        fb = ch * side[:, t]
        fb[omit] = np.nan
        choices[:, t], feedback[:, t] = ch, fb
        evidence = np.where(omit, 0., side[:, t])
        h = decay * h + (1. - decay) * evidence[:, None]
        previous = ch
    out = inputs.copy()
    out['choice'] = choices.ravel()
    out['feedbackType'] = feedback.ravel()
    old, mask, _ = windows_arrays(inputs)
    valid = subjects.partition.str.startswith('validation').to_numpy()
    truth_person = np.array([np.mean((old[i] * truth_shift[i])[mask[i]]) for i in range(n)])
    truth = dict(mean=float(truth_person[valid].mean()),
                 rms=float(np.sqrt(np.mean([np.mean(truth_shift[i][mask[i]] ** 2) for i in np.where(valid)[0]]))),
                 per_subject={str(s): float(v) for s, v in zip(subjects.subject, truth_person)},
                 shift_scale=shift_scale, generator_seed=int(seed),
                 mean_later_accuracy=float(np.mean((choices[:, 200:] == side[:, 200:])[choices[:, 200:] != 0])),
                 omission_rate=float(np.mean(choices == 0.)))
    return out, truth


def refine_shift(inputs, scenario, scale):
    """Calibrate the population mean under heterogeneity, without fitting.

    Ten fixed prior-predictive draws, separate from recovery seeds, correct the
    attenuation from random coefficients, actual omissions and lapse mixture.
    This adjusts the synthetic injection, never the scientific .05 boundary.
    """
    target = SCENARIOS[scenario]['target']
    if target == 0:
        return 0., 0., []
    index = list(SCENARIOS).index(scenario)
    history = []
    for step in range(3):
        effects = [simulate(inputs, scenario, 77100000 + 10000 * index + k, scale)[1]['mean'] for k in range(10)]
        observed = float(np.mean(effects))
        history.append(dict(step=step, scale=scale, mean_effect=observed))
        if abs(observed - target) < .0001:
            break
        if step < 2:
            scale *= target / observed
    return float(scale), float(observed), history


def retransform(features, transform):
    old_center = np.asarray(features.calibration_transform['center'])
    new_center = np.asarray(transform['center'])
    # Scale is fixed to1 in the frozen engine.
    return replace(features, calibration=features.calibration + old_center - new_center,
                   calibration_transform=transform)


def bootstrap_features(features, rng):
    info = features.rows[['subject', 'schedule', 'instructions']].drop_duplicates()
    indices = {s: np.flatnonzero(features.rows.subject.to_numpy() == s) for s in features.subjects}
    pieces, rows, raws, codes, names = [], [], [], [], []
    raw = features.calibration_raw.set_index('subject')
    # Condition-only participant resampling avoids freezing sparse or singleton
    # schedule×condition cells and understating population sampling variation.
    for _, block in info.groupby(['instructions'], sort=True):
        for subject in rng.choice(block.subject.to_numpy(), len(block), replace=True):
            k = len(names)
            name = f'boot{k:03d}'
            ii = indices[subject]
            pieces.append(ii)
            row = features.rows.iloc[ii].copy()
            row['subject'] = name
            rows.append(row)
            raws.append([name] + raw.loc[subject, list(CALIBRATION_NAMES)].tolist())
            codes.extend([k] * len(ii))
            names.append(name)
    idx = np.concatenate(pieces)
    raw = pd.DataFrame(raws, columns=['subject'] + list(CALIBRATION_NAMES))
    center = raw[list(CALIBRATION_NAMES)].mean().to_numpy()
    transform = dict(features.calibration_transform)
    transform['source_subjects'] = names
    transform['center'] = center.tolist()
    cal = features.calibration[idx] + np.asarray(features.calibration_transform['center']) - center
    return replace(features, rows=pd.concat(rows, ignore_index=True),
                   nuisance=features.nuisance[idx], history=features.history[idx], calibration=cal,
                   calibration_raw=raw, calibration_transform=transform,
                   group=features.group[idx], y=features.y[idx], responded=features.responded[idx],
                   subject_codes=np.asarray(codes), subjects=names)


def score_ci(table, rng, reps=2000):
    groups = [b.delta_log.to_numpy() for _, b in table.groupby(['partition', 'condition'])]
    draws = np.zeros(reps)
    for a in groups:
        draws += rng.choice(a, (reps, len(a)), replace=True).sum(axis=1) / len(table)
    return float(np.quantile(draws, .025)), float(np.quantile(draws, .975))


def analyze_simulated(frame, truth, seed, effect_bootstraps=0, random_sd=.7):
    dev = frame[frame.partition.eq('development')]
    val = frame[~frame.partition.eq('development')]
    cfg = ModelConfig(random_sd=random_sd)
    df = prepare_features(dev, config=cfg)
    vf = prepare_features(val, df.calibration_transform, cfg)
    fits = {v: fit_model(df, v, cfg) for v in ['shared', 'condition']}
    w = windows(vf.rows)
    delta = log_score(predict_model(fits['condition'], vf), vf.y) - log_score(predict_model(fits['shared'], vf), vf.y)
    score = w[['subject', 'instructions', 'partition', 'schedule']].copy()
    score['delta_log'] = delta
    score = score.loc[w.primary_responded].groupby(['subject', 'instructions', 'partition', 'schedule']).delta_log.mean().reset_index().rename(columns={'instructions': 'condition'})
    rng = np.random.default_rng(seed + 930000)
    lo, hi = score_ci(score, rng)
    effect, _ = standardized_effect(fits['condition'], vf)
    summary = dict(delta_log=float(score.delta_log.mean()), score_low=lo, score_high=hi,
                   effect=float(effect['mean']), effect_rms=float(effect['rms']),
                   truth_effect=truth['mean'], truth_rms=truth['rms'],
                   effect_bias=float(effect['mean'] - truth['mean']),
                   convergence=all(x.diagnostics['success'] for x in fits.values()),
                   max_gradient=max(x.diagnostics['max_abs_gradient'] for x in fits.values()),
                   score_detect=bool(lo > 0.), shift_scale=truth['shift_scale'])
    for partition, b in score.groupby('partition'):
        summary[partition + '_delta_log'] = float(b.delta_log.mean())
    bootstrap = []
    for b in range(effect_bootstraps):
        bf = bootstrap_features(df, rng)
        fit = fit_model(bf, 'condition', cfg)
        rf = retransform(vf, bf.calibration_transform)
        eff, _ = standardized_effect(fit, rf)
        bootstrap.append(eff['mean'])
        summary['convergence'] = summary['convergence'] and fit.diagnostics['success']
        summary['max_gradient'] = max(summary['max_gradient'], fit.diagnostics['max_abs_gradient'])
    if bootstrap:
        low, high = np.quantile(bootstrap, [.025, .975])
        summary.update(effect_low=float(low), effect_high=float(high),
                       effect_detect=bool(low > 0. or high < 0.),
                       effect_covers_truth=bool(low <= truth['mean'] <= high),
                       boundary_interval_inside_margin=bool(low > -.05 and high < .05 and abs(truth['mean']) >= .045),
                       false_equivalence=bool(low > -.05 and high < .05 and abs(truth['mean']) >= .05),
                       bootstrap_reps=effect_bootstraps)
    return summary, score, bootstrap


def normalize_reporting(table):
    """Separate nominal boundary injections from strictly outside-margin truth."""
    table = table.copy()
    if 'effect_low' in table:
        has_interval = table.effect_low.notna()
        inside = (table.effect_low > -.05) & (table.effect_high < .05)
        table['boundary_interval_inside_margin'] = np.where(has_interval, inside & (table.truth_effect.abs() >= .045), np.nan)
        table['false_equivalence'] = np.where(has_interval, inside & (table.truth_effect.abs() >= .05), np.nan)
    return table


def summarize(table):
    table = normalize_reporting(table)
    summaries = []
    for scenario, d in table.groupby('scenario', sort=False):
        row = dict(scenario=scenario, reps=len(d), mean_truth=float(d.truth_effect.mean()),
                   mean_estimate=float(d.effect.mean()), mean_bias=float(d.effect_bias.mean()),
                   effect_sd=float(d.effect.std()), rmse=float(np.sqrt(np.mean(d.effect_bias ** 2))),
                   score_mean=float(d.delta_log.mean()), score_sd=float(d.delta_log.std()),
                   score_positive_fraction=float(np.mean(d.delta_log > 0)), score_detection_fraction=float(d.score_detect.mean()),
                   effect_estimate_025=float(d.effect.quantile(.025)), effect_estimate_975=float(d.effect.quantile(.975)),
                   max_gradient=float(d.max_gradient.max()), all_converged=bool(d.convergence.all()))
        if 'bootstrap_reps' in d:
            b = d.dropna(subset=['bootstrap_reps'])
            if len(b):
                row.update(bootstrap_outer_reps=len(b), bootstrap_inner_reps=int(b.bootstrap_reps.iloc[0]),
                           effect_detection_fraction=float(b.effect_detect.mean()),
                           interval_coverage=float(b.effect_covers_truth.mean()),
                           interval_width_mean=float(np.mean(b.effect_high - b.effect_low)),
                           boundary_interval_inside_margin_fraction=float(b.boundary_interval_inside_margin.mean()),
                           false_equivalence_fraction=float(b.false_equivalence.mean()))
        summaries.append(row)
    return summaries


def plot_results(path):
    """Standalone scientific figure; only saved simulated result tables used."""
    path = Path(path)
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'outputs/recovery/mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    table = pd.read_csv(path / 'replicates.csv')
    names = [s for s in SCENARIOS if s in table.scenario.unique()]
    labels = dict(nuisance_null='Shared: nuisance differences', carryover_null='Shared: sensory–history law',
                  slow_05='Slow-history +5 pp', slow_10='Slow-history +10 pp',
                  shape_05='Kernel redistribution +5 pp', slow_minus05='Slow-history −5 pp')
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), gridspec_kw={'width_ratios': [1.35, 1.]})
    ax = axes[0]
    for j, name in enumerate(names):
        d = table[table.scenario.eq(name)]
        mean = d.effect.mean() * 100
        lo, hi = d.effect.quantile([.025, .975]).to_numpy() * 100
        ax.plot([lo, hi], [j, j], color='#2a6a8a', lw=3, alpha=.7)
        ax.scatter(mean, j, s=48, color='#2a6a8a', zorder=3,
                   label='Estimate mean and 95% simulation range' if j == 0 else None)
        ax.scatter(d.truth_effect.mean() * 100, j, s=48, color='#a04b35', marker='D', zorder=4,
                   label='True mean standardized difference' if j == 0 else None)
    ax.axvline(0, color='#777777', lw=1)
    for v in [-5, 5]:
        ax.axvline(v, color='#aaaaaa', ls='--', lw=.8)
    ax.set_yticks(range(len(names)), [labels[x] for x in names])
    ax.invert_yaxis()
    ax.set_xlabel('Old-context choice difference (percentage points)')
    ax.set_title('Observable-effect recovery')
    ax.legend(fontsize=8, loc='lower right')
    ax = axes[1]
    for j, name in enumerate(names):
        d = table[table.scenario.eq(name)]
        n, k = len(d), int(d.score_detect.sum())
        p, z = k / n, 1.96
        center = (p + z*z/(2*n))/(1+z*z/n)
        radius = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
        ax.plot([(center-radius)*100,(center+radius)*100],[j,j],color='#2a6a8a',lw=2)
        ax.scatter(p*100,j,color='#2a6a8a',s=48)
        ax.text(min(p*100+5,102),j,f'{k}/{n}',va='center',fontsize=8)
    ax.set_xlim(-3,112)
    ax.set_yticks(range(len(names)), ['']*len(names))
    ax.invert_yaxis()
    ax.set_xlabel('Positive held-out score interval (%)')
    ax.set_title('Predictive discrimination, with 95% Wilson intervals')
    for a in axes:
        a.spines[['top','right']].set_visible(False)
        a.grid(axis='x',alpha=.18)
    fig.suptitle('Actual schedules and split; all responses simulated',fontsize=13)
    fig.tight_layout()
    fig.savefig(path / 'recovery.png',dpi=180)
    fig.savefig(path / 'recovery.pdf')
    plt.close(fig)


def one_job(inputs, scenario, rep, scale, effect_bootstraps, random_sd):
    scen_no = list(SCENARIOS).index(scenario)
    seed = 202610280 + 10000 * scen_no + rep
    start = time.monotonic()
    frame, truth = simulate(inputs, scenario, seed, scale)
    stats, scores, bootstrap = analyze_simulated(frame, truth, seed, effect_bootstraps, random_sd)
    row = dict(scenario=scenario, replicate=rep, seed=seed, seconds=time.monotonic() - start, **stats)
    return row, scores, bootstrap, truth


def run(args):
    out = ROOT / 'outputs/recovery' / args.label
    out.mkdir(parents=True, exist_ok=True)
    inputs, split = load_inputs()
    all_rows = []
    definitions = {}
    begin = time.monotonic()
    jobs = []
    for scen_no, scenario in enumerate(SCENARIOS):
        if args.scenarios and scenario not in args.scenarios:
            continue
        scale, expected = calibrate_shift(inputs, scenario)
        nominal_scale = scale
        refinement = []
        if args.refine_injection:
            scale, expected, refinement = refine_shift(inputs, scenario, scale)
        definitions[scenario] = dict(**SCENARIOS[scenario], scale=scale, expected_effect=expected,
                                    nominal_scale=nominal_scale, heterogeneity_refinement=refinement)
        for rep in range(args.reps):
            outer = min(args.bootstrap_outer, 10) if scenario == 'slow_minus05' else args.bootstrap_outer
            bs = args.effect_bootstraps if rep < outer else 0
            jobs.append((inputs, scenario, rep, scale, bs, args.random_sd))
    # Run short nonbootstrap replications first, making provisional precision
    # and score-recovery summaries available while nested intervals complete.
    jobs.sort(key=lambda job: (job[4] > 0, job[2], job[1]))
    (out / 'scenario_definitions.json').write_text(json.dumps(definitions, indent=2) + '\n')
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(one_job, *job) for job in jobs]
        for future in as_completed(futures):
            row, scores, bootstrap, truth = future.result()
            scenario, rep = row['scenario'], row['replicate']
            all_rows.append(row)
            normalize_reporting(pd.DataFrame(all_rows)).sort_values(['scenario','replicate']).to_csv(out / 'replicates.csv', index=False)
            scores.assign(scenario=scenario, replicate=rep).to_csv(out / f'scores_{scenario}_{rep:03d}.csv', index=False)
            if bootstrap:
                pd.DataFrame({'effect': bootstrap}).to_csv(out / f'bootstrap_{scenario}_{rep:03d}.csv', index=False)
            (out / f'truth_{scenario}_{rep:03d}.json').write_text(json.dumps(truth, indent=2) + '\n')
            print(json.dumps(dict(scenario=scenario, replicate=rep, delta_log=row['delta_log'],
                                  effect=row['effect'], truth=row['truth_effect'],
                                  seconds=round(row['seconds'], 2))), flush=True)
            (out / 'summary.json').write_text(json.dumps(summarize(pd.DataFrame(all_rows)), indent=2) + '\n')
    manifest = dict(scenarios=definitions, args=vars(args), config=vars(ModelConfig(random_sd=args.random_sd)),
                    elapsed_seconds=time.monotonic() - begin,
                    source='input-only trial_inputs.csv; all response and feedback values simulated',
                    input_sha256=hashlib.sha256((ROOT / 'outputs/input_only/trial_inputs.csv').read_bytes()).hexdigest(),
                    split_sha256=hashlib.sha256((ROOT / 'protocol/split_manifest.csv').read_bytes()).hexdigest(),
                    interpretation='Detection rates use participant bootstrap conditional on fitted population. Effect intervals refit stratified development participant bootstrap; finite outer repetitions limit rate precision.')
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    plot_results(out)
    print(json.dumps(summarize(pd.DataFrame(all_rows)), indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reps', type=int, default=100)
    parser.add_argument('--bootstrap-outer', type=int, default=20)
    parser.add_argument('--effect-bootstraps', type=int, default=100)
    parser.add_argument('--label', default='primary')
    parser.add_argument('--scenarios', nargs='+', default=[])
    parser.add_argument('--random-sd', type=float, default=.7)
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--refine-injection', action='store_true')
    run(parser.parse_args())
