"""Independent frozen-object reconstruction; never imports author/campaign code."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import resource
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from numpy.polynomial.hermite import hermgauss
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
OLD = ROOT / 'campaigns/human_learning_routes_2026-10-28'
AUTHOR = ROOT / 'lab/tasks/human-generated-history-forecast-2026-11-01'
READS = []
DECAY = np.exp(-1 / np.array([2., 8., 32.]))


def utc():
    return datetime.now(timezone.utc).isoformat()


def blob(path):
    path = Path(path)
    b = path.read_bytes()
    READS.append(dict(path=str(path.relative_to(ROOT)), bytes=len(b),
                      sha256=hashlib.sha256(b).hexdigest(),
                      read_hash_decode_allowance=3 * len(b)))
    return b


def obj(path):
    return json.loads(blob(path))


def frame(path):
    return pd.read_csv(io.BytesIO(blob(path)), dtype={'subject': str})


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def usage():
    return dict(reads=READS, explicit_read_hash_decode_allowance=sum(
        x['read_hash_decode_allowance'] for x in READS),
        observed_process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        measurement='Darwin ru_maxrss; runtime/import/host/physical I/O unknown')


def calibrate(prefix, fit):
    ch = prefix.choice.to_numpy(float)
    c = prefix.sideContrast.to_numpy(float)
    vals = []
    for lo, hi in [(0, 100), (100, 200)]:
        good = np.isin(ch[lo:hi], [-1., 1.]) & (c[lo:hi] != 0)
        vals.append(float(np.mean(ch[lo:hi][good] * np.sign(c[lo:hi][good]))) if good.any() else 0.)
    good = np.isin(ch, [-1., 1.])
    vals.extend([float(ch[good].mean()) if good.any() else 0., float(1 - good.mean())])
    cal = (np.array(vals) - np.array(fit['calibration_transform']['center'])) / np.array(
        fit['calibration_transform']['scale'])
    return np.array(vals), cal


def prefix_state(prefix):
    h = np.zeros(3)
    prev = 0.
    for row in prefix.itertuples():
        good = row.choice in (-1., 1.)
        reveal = row.choice * row.feedbackType if good and row.feedbackType in (-1., 1.) else 0.
        h = DECAY * h + (1 - DECAY) * reveal
        prev = float(row.choice) if good else 0.
    return h, prev


def coefficients(fit, cal, condition):
    b = np.array(fit['beta'])
    nuisance = b[:8] + (condition - .5) * b[8:16]
    for k in range(4):
        nuisance += cal[k] * b[16 + 8*k:24 + 8*k]
    history = np.zeros(3)
    if fit['variant'] != 'no_history':
        history = b[48:51].copy()
        for k in range(4):
            history += cal[k] * b[51 + 3*k:54 + 3*k]
    return nuisance, history


def design(contrast, trial, previous, history, fit, cal, condition):
    sign = np.sign(contrast)
    tm = (trial - 399.5) / 200.
    n = np.array([1.] + [float(sign * np.isclose(abs(contrast), v, rtol=0, atol=1e-8))
                         for v in [.1, .25, .5, 1.]] + [previous, tm, sign*tm])
    nb, hb = coefficients(fit, cal, condition)
    eta = float(np.sum(n * nb) + np.sum(history * hb))
    z = np.r_[1., sign, history] if fit['variant'] != 'no_history' else np.array([1., sign])
    return eta, z


def integrated(eta, z, fit):
    nodes, weights = hermgauss(fit['config']['gh_nodes'])
    shifts = np.sqrt(2) * fit['config']['random_sd'] * np.sqrt(np.sum(z*z)) * nodes
    return float(np.sum(expit(eta + shifts) * weights) / np.sqrt(np.pi))


def masks(rows):
    p = rows.probabilityLeft.to_numpy(float)
    t = rows.trial.to_numpy(int)
    off = np.full(len(rows), 999)
    for k in range(1, len(rows)):
        if t[k] < 200 or p[k] == p[k-1] or p[k] == .5 or p[k-1] == .5:
            continue
        j = k
        while j < len(rows) and p[j] == p[k]:
            off[j] = t[j] - t[k]
            j += 1
    responded = np.isin(rows.choice.to_numpy(float), [-1., 1.])
    later = (t >= 200) & (t < 600)
    return dict(primary=later & responded & (off < 30) & (rows.stimContrast.to_numpy(float) <= .1),
                primary_opportunities=later & (off < 30) & (rows.stimContrast.to_numpy(float) <= .1),
                all_later=later & responded,
                zero=later & responded & (off < 30) & (rows.stimContrast.to_numpy(float) == 0))


def score_arrays(prob, people, val):
    per = []
    for i, who in enumerate(people):
        rows = val.loc[val.subject == who].sort_values('trial')
        assert np.array_equal(rows.trial, np.arange(600))
        y = (rows.choice.to_numpy(float)[200:] == 1.).astype(float)
        p = np.clip(prob[i], 1e-12, 1 - 1e-12)
        log = np.where(y[:, None] == 1., np.log(p), np.log1p(-p))
        br = (p - y[:, None]) ** 2
        mm = masks(rows)
        record = dict(subject=who, condition=int(rows.instructions.iloc[0]),
                      n=int(mm['primary'].sum()), opportunities=int(mm['primary_opportunities'].sum()))
        for kind in ['primary', 'all_later', 'zero']:
            m = mm[kind][200:]
            record[kind] = float((log[m, 0] - log[m, 1]).mean())
            record[kind + '_brier'] = float((br[m, 1] - br[m, 0]).mean())
        per.append(record)
    return per


def bootstrap_summary(per, split, seed=20261103, reps=5000):
    """Resample people in frozen condition/partition strata; no fitted parameters."""
    rows = pd.DataFrame(per).set_index('subject')
    groups = {}
    for who in rows.index:
        key = (int(rows.loc[who, 'condition']), str(split.loc[who, 'partition']))
        groups.setdefault(key, []).append(who)
    fields = [('primary', seed), ('all_later', seed + 1), ('zero', seed + 2), ('primary_brier', seed + 3)]
    out = {}
    for field, sd in fields:
        rng = np.random.default_rng(sd)
        means = np.zeros(reps)
        for ids in groups.values():
            v = rows.loc[ids, field].to_numpy(float)
            means += rng.choice(v, (reps, len(v)), replace=True).sum(axis=1) / len(rows)
        out[field] = dict(mean=float(rows[field].mean()), low=float(np.quantile(means, .025)),
                          high=float(np.quantile(means, .975)), reps=reps)
    out['partitions'] = {}
    for part in sorted(split.loc[rows.index, 'partition'].unique()):
        ids = [who for who in rows.index if split.loc[who, 'partition'] == part]
        out['partitions'][part] = dict(n_people=len(ids), mean=float(rows.loc[ids, 'primary'].mean()))
    out['schedules'] = {}
    out['leave_one_schedule_out'] = {}
    schedule_ids = []
    for sch in sorted(split.loc[rows.index, 'schedule'].unique()):
        ids = [who for who in rows.index if split.loc[who, 'schedule'] == sch]
        schedule_ids.append(ids)
        out['schedules'][sch] = dict(n_people=len(ids), mean=float(rows.loc[ids, 'primary'].mean()))
        out['leave_one_schedule_out'][sch] = float(rows.loc[~rows.index.isin(ids), 'primary'].mean())
    rng = np.random.default_rng(20261107)
    draws = []
    for _ in range(reps):
        values = []
        for i in rng.integers(0, len(schedule_ids), len(schedule_ids)):
            v = rows.loc[schedule_ids[i], 'primary'].to_numpy(float)
            values.extend(rng.choice(v, len(v), replace=True))
        draws.append(np.mean(values))
    out['schedule_person_interval'] = dict(low=float(np.quantile(draws, .025)),
                                            high=float(np.quantile(draws, .975)), reps=reps)
    return out


def no_omission_path(rows, teacher_side, fit):
    prefix = rows.iloc[:200]
    raw, cal = calibrate(prefix, fit)
    h, prev = prefix_state(prefix)
    condition = int(rows.instructions.iloc[0])
    eta0, loading, histories = [], [], []
    for t in range(200, 600):
        e, z = design(float(rows.sideContrast.iloc[t]), t, 0., h, fit, cal, condition)
        eta0.append(e)
        loading.append(z)
        histories.append(h.copy())
        h = DECAY * h + (1 - DECAY) * teacher_side[t]
    eta0, loading = np.array(eta0), np.array(loading)
    nb, _ = coefficients(fit, cal, condition)
    nodes, weights = hermgauss(fit['config']['gh_nodes'])
    scale = np.sqrt(2) * fit['config']['random_sd'] * np.sqrt((loading * loading).sum(axis=1))
    pm = np.sum(expit(eta0[:, None] - nb[5] + scale[:, None] * nodes) * weights, axis=1) / np.sqrt(np.pi)
    pp = np.sum(expit(eta0[:, None] + nb[5] + scale[:, None] * nodes) * weights, axis=1) / np.sqrt(np.pi)
    result = np.empty(400)
    result[0] = integrated(eta0[0] + nb[5] * prev, loading[0], fit)
    for j in range(1, 400):
        result[j] = result[j-1] * pp[j] + (1 - result[j-1]) * pm[j]
    return result, dict(eta0=eta0, loading=loading, lag=float(nb[5]), initial_previous=prev,
                         history=np.array(histories), calibration_raw=raw, calibration_centered=cal)


def first():
    started = time.perf_counter()
    val = frame(OLD / 'inputs/validation_numeric.csv')
    meta = obj(AUTHOR / 'FORECAST_META.json')
    inputs = obj(AUTHOR / 'FORECAST_INPUTS.json')
    fits = [obj(OLD / ('outputs/primary/' + name + '_fit.json'))
            for name in ['shared', 'no_history']]
    with np.load(io.BytesIO(blob(AUTHOR / 'FORECASTS.npz')), allow_pickle=False) as f:
        arrays = {k: f[k] for k in f.files}
    people = meta['subjects']
    main = arrays['main'].mean(axis=0)
    scores = score_arrays(main, people, val)
    no_scores = score_arrays(arrays['no_omission'], people, val)
    p0 = val.loc[(val.subject == people[0]) & (val.trial < 200)].sort_values('trial')
    h, prev = prefix_state(p0)
    target = val.loc[(val.subject == people[0]) & (val.trial == 200)].iloc[0]
    pr = []
    for fit in fits:
        raw, cal = calibrate(p0, fit)
        eta, z = design(float(target.sideContrast), 200, prev, h, fit, cal, int(target.instructions))
        pr.append(integrated(eta, z, fit))
    answer = dict(utc=utc(), origin='independently rebuilt original calibration/design and scores; no author imports',
                  arrays={k: list(v.shape) for k, v in arrays.items()},
                  input_top_keys=list(inputs), first_person_input_keys=list(inputs['people'][0]),
                  validation_columns=list(val.columns), people=len(people),
                  primary_responding_trials=sum(x['n'] for x in scores),
                  primary_opportunities=sum(x['opportunities'] for x in scores),
                  main_equal_person_gain=float(np.mean([x['primary'] for x in scores])),
                  no_omission_equal_person_gain=float(np.mean([x['primary'] for x in no_scores])),
                  first_person=people[0], first_trial=200,
                  prefix_raw_calibration=raw.tolist(), prefix_history=h.tolist(), prefix_previous_choice=prev,
                  original_kernel_first_probability=pr,
                  saved_exact_first_probability=arrays['no_omission'][0, 0].tolist(),
                  first_probability_max_abs_difference=float(np.max(np.abs(np.array(pr) - arrays['no_omission'][0, 0]))),
                  elapsed_seconds=time.perf_counter() - started, **usage())
    save('FIRST_CALCULATION.json', answer)
    save('FIRST_PERSON_SCORES.json', scores)
    print(json.dumps({k: v for k, v in answer.items() if k not in ['reads', 'validation_columns']}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['first'])
    args = parser.parse_args()
    first()
