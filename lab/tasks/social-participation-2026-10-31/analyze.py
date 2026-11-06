"""Fixed joint-observation comparison and one-dimensional revelation witness.

No old analysis outputs are imported; immutable permitted originals only.
"""
import os
for _key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
             'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'
import collections
import csv
import hashlib
import json
import math
import platform
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.special import expit

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
STAGES = ('A', 'F', 'D', 'B', 'Y')
MODELS = ('marginal', 'expression', 'primacy', 'cancellation')
Q_NAMES = ('none_recorded', 'one_green', 'one_pink',
           'both_green_first', 'both_pink_first')
M_NAMES = ('no_mating', 'green', 'pink')
READS = []
FITS = []
SEED = 20261031

def read(path):
    path = Path(path)
    assert path.stat().st_size < 2_000_000
    b = path.read_bytes()
    READS.append({'path': str(path.relative_to(ROOT)), 'bytes': len(b),
                  'sha256': hashlib.sha256(b).hexdigest()})
    return b

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def dump_csv(name, rows):
    if not rows:
        return
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def reconstruct(raw):
    result = []
    for i, row in enumerate(csv.DictReader(raw.decode().splitlines())):
        a = row['color_court_1'] in ('g', 'p')
        d = row['color_court_2'] in ('g', 'p')
        assert not d or a
        assert not d or row['color_court_1'] != row['color_court_2']
        ref = row['demo_color_2'] if row['treatment'] == 'C2' else row['demo_color_1']
        assert ref in ('g', 'p')
        if row['treatment'] == 'T':
            assert row['demo_color_2'] in ('g', 'p') and ref != row['demo_color_2']
        else:
            assert row['demo_color_2' if row['treatment'] == 'C1' else 'demo_color_1'] == 'NA'
        f = (1 if row['color_court_1'] == 'g' else -1) if a else 0
        q = 0 if not a else (3 if f == 1 else 4) if d else (1 if f == 1 else 2)
        m = 1 if row['test_color'] == 'g' else 2 if row['test_color'] == 'p' else 0
        result.append({'row': i + 2, 'date': row['date'], 'device': row['device'],
                       't': row['treatment'], 'z': 1 if ref == 'g' else -1,
                       'A': int(a), 'F': int(f == 1), 'f': f, 'D': int(d),
                       'Q': q, 'B': int(m != 0), 'Y': int(m == 1), 'M': m,
                       'eligible': int(d and m != 0),
                       'copy': int((m == 1) == (ref == 'g')) if m else None,
                       'first_match': int(f == (1 if ref == 'g' else -1)) if a else None})
    return result

def features(rows, stage, model, eligible_only=False):
    result = []
    for r in rows:
        x = [1.0, float(r['t'] == 'T'), float(r['t'] == 'C2')]
        if model != 'marginal' and not eligible_only:
            if stage == 'F':
                x += [float(r['z'])]
            elif stage == 'D':
                x += [float(r['f']), float(r['z'] * r['f'])]
            elif stage == 'B':
                x += [float(r['Q'] == k) for k in range(1, 5)]
                x += [float(r['z'] * r['f'])]
            elif stage == 'Y':
                x += [float(r['Q'] == k) for k in range(1, 5)]
        if stage == 'Y' and model in ('primacy', 'cancellation'):
            x += [float(r['z'] * (model == 'primacy' or r['t'] != 'T'))]
        result.append(x)
    return np.asarray(result)

def names(stage, model, eligible_only=False):
    n = ['intercept', 'T', 'C2']
    if model != 'marginal' and not eligible_only:
        if stage == 'F': n += ['reference_green_sign']
        elif stage == 'D': n += ['first_green_sign', 'first_matches_reference_sign']
        elif stage == 'B': n += list(Q_NAMES[1:]) + ['first_matches_reference_sign']
        elif stage == 'Y': n += list(Q_NAMES[1:])
    if stage == 'Y' and model in ('primacy', 'cancellation'):
        n += ['shared_nonnegative_copy_gain']
    return n

def keep(r, stage):
    return bool(r['A']) if stage in ('F', 'D') else bool(r['B']) if stage == 'Y' else True

def objective(beta, x, y):
    eta = np.einsum('ij,j->i', x, beta)
    reg = np.ones(len(beta)); reg[0] = 0
    value = np.logaddexp(0, eta).sum() - np.einsum('i,i->', y, eta)
    value += .5 * np.einsum('i,i,i->', reg, beta, beta)
    grad = np.einsum('ij,i->j', x, expit(eta) - y) + reg * beta
    return float(value), grad

def fit_stage(rows, stage, model, eligible_only=False, start_shift=0.0, strict=False):
    chosen = [r for r in rows if keep(r, stage)]
    x = features(chosen, stage, model, eligible_only)
    y = np.array([r[stage] for r in chosen], dtype=float)
    beta = np.full(x.shape[1], start_shift)
    prop = (y.sum() + .5) / (len(y) + 1)
    beta[0] = math.log(prop / (1 - prop))
    bounds = [(None, None)] * len(beta)
    if stage == 'Y' and model in ('primacy', 'cancellation'):
        bounds[-1] = (0, None)
        beta[-1] = max(beta[-1], 0)
    opt = minimize(objective, beta, args=(x, y), jac=True, method='L-BFGS-B',
                   bounds=bounds,
                   options={'maxiter': 2000 if strict else 600,
                            'ftol': 1e-15 if strict else 2e-13,
                            'gtol': 1e-10 if strict else 1e-8,
                            'maxls': 50})
    value, grad = objective(opt.x, x, y)
    pg = grad.copy()
    if bounds[-1][0] == 0 and opt.x[-1] < 1e-9 and pg[-1] > 0:
        pg[-1] = 0
    record = {'stage': stage, 'model': model, 'n': len(y), 'success': bool(opt.success),
              'message': str(opt.message), 'iterations': int(opt.nit),
              'objective': value, 'projected_gradient_max': float(np.max(np.abs(pg))),
              'coefficient_names': names(stage, model, eligible_only),
              'coefficients': opt.x.tolist()}
    FITS.append(record)
    assert np.all(np.isfinite(opt.x)) and np.max(np.abs(pg)) < 2e-3, record
    return opt.x, record

def fit_model(rows, model, eligible_only=False, start_shift=0.0, strict=False):
    beta, records = {}, {}
    for s in ('Y',) if eligible_only else STAGES:
        beta[s], records[s] = fit_stage(rows, s, model, eligible_only, start_shift, strict)
    return beta, records

def probabilities(rows, model, beta, eligible_only=False):
    return {s: expit(np.einsum('ij,j->i', features(rows, s, model, eligible_only), b))
            for s, b in beta.items()}

def bnll(p, y):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return -(y * np.log(p) + (1 - y) * np.log1p(-p))

def joint_cells(rows, model, beta):
    result = []
    for context in rows:
        fake = []
        for q in range(5):
            a = int(q != 0); f = 1 if q in (1, 3) else -1 if q in (2, 4) else 0
            r = dict(context, Q=q, A=a, F=int(f == 1), f=f, D=int(q >= 3))
            fake.append(r)
        p = probabilities(fake, model, beta)
        qprobs = []
        for q, r in enumerate(fake):
            pq = 1 - p['A'][q] if not r['A'] else p['A'][q]
            if r['A']:
                pq *= p['F'][q] if r['F'] else 1 - p['F'][q]
                pq *= p['D'][q] if r['D'] else 1 - p['D'][q]
            qprobs += [pq * (1 - p['B'][q]),
                       pq * p['B'][q] * p['Y'][q],
                       pq * p['B'][q] * (1 - p['Y'][q])]
        result.append(qprobs)
    return np.asarray(result)

def evaluate(rows, model, beta, eligible_only=False):
    p = probabilities(rows, model, beta, eligible_only)
    comps = {}
    for s in p:
        comps[s] = bnll(p[s], np.array([r[s] for r in rows]))
        comps[s] *= np.array([keep(r, s) for r in rows])
    result = {'Y': comps['Y']}
    if not eligible_only:
        result['joint'] = sum(comps.values())
        result['courtship'] = comps['A'] + comps['F'] + comps['D']
        result['mating'] = comps['B']
        result['participation'] = result['courtship'] + comps['B']
        cells = joint_cells(rows, model, beta)
        assert np.max(np.abs(cells.sum(axis=1) - 1)) < 1e-12
        direct = -np.log(cells[np.arange(len(rows)), [3*r['Q']+r['M'] for r in rows]])
        assert np.max(np.abs(direct - result['joint'])) < 1e-10
        den = cells[:, [10, 11, 13, 14]].sum(axis=1)
        pyg = cells[:, [10, 13]].sum(axis=1) / den
        result['Y_integrated'] = bnll(pyg, np.array([r['Y'] for r in rows]))
    return result

def cv(rows, eligible_only=False, retain_fits=True):
    models = ('marginal', 'primacy', 'cancellation') if eligible_only else MODELS
    dates = sorted(set(r['date'] for r in rows))
    results = {m: {} for m in models}
    fold_records = []
    for date in dates:
        idx = [i for i, r in enumerate(rows) if r['date'] == date]
        train = [r for r in rows if r['date'] != date]
        test = [rows[i] for i in idx]
        for m in models:
            beta, record = fit_model(train, m, eligible_only)
            if retain_fits: fold_records.append({'held_date': date, 'model': m, 'fits': record})
            values = evaluate(test, m, beta, eligible_only)
            for key, a in values.items():
                if key not in results[m]: results[m][key] = np.zeros(len(rows))
                results[m][key][idx] = a
    return results, fold_records

def masks(rows, eligible_only=False):
    all_ = np.ones(len(rows), dtype=bool)
    e = np.array([r['eligible'] for r in rows], dtype=bool)
    main = np.array([r['t'] == 'T' for r in rows])
    if eligible_only:
        return {'eligible_choice': ('Y', all_), 'T_eligible_choice': ('Y', main)}
    return {'joint': ('joint', all_), 'courtship': ('courtship', all_),
            'mating': ('mating', all_), 'participation': ('participation', all_),
            'mating_choice': ('Y', np.array([r['B'] for r in rows], dtype=bool)),
            'eligible_choice': ('Y', e), 'T_eligible_choice': ('Y', e & main),
            'eligible_integrated_choice': ('Y_integrated', e),
            'T_eligible_integrated_choice': ('Y_integrated', e & main)}

def aggregate(rows, losses, eligible_only=False):
    result = {}
    for m in losses:
        result[m] = {}
        for name, (key, mask) in masks(rows, eligible_only).items():
            dates = sorted(set(r['date'] for i, r in enumerate(rows) if mask[i]))
            dm = [np.mean([losses[m][key][i] for i, r in enumerate(rows)
                           if mask[i] and r['date'] == d]) for d in dates]
            result[m][name] = {'n': int(mask.sum()), 'dates': len(dates),
                               'nll': float(losses[m][key][mask].mean()),
                               'equal_date_nll': float(np.mean(dm))}
    return result

def contrasts(rows, losses, eligible_only=False):
    pairs = [('marginal', 'primacy'), ('cancellation', 'primacy')] if eligible_only else [
        ('marginal', 'expression'), ('expression', 'primacy'),
        ('cancellation', 'primacy'), ('expression', 'cancellation')]
    rng = np.random.default_rng(SEED)
    dates = sorted(set(r['date'] for r in rows))
    # Same paired resamples for every model/metric; count weights preserve the estimand.
    draw = rng.integers(0, len(dates), size=(5000, len(dates)))
    result = []
    for base, model in pairs:
        for name, (key, mask) in masks(rows, eligible_only).items():
            dif = losses[base][key] - losses[model][key]
            sums = np.array([sum(dif[i] for i, r in enumerate(rows)
                                 if mask[i] and r['date'] == d) for d in dates])
            ns = np.array([sum(1 for i, r in enumerate(rows)
                              if mask[i] and r['date'] == d) for d in dates])
            denom = ns[draw].sum(axis=1)
            vals = sums[draw].sum(axis=1)[denom > 0] / denom[denom > 0]
            date_means = sums[ns > 0] / ns[ns > 0]
            result.append({'baseline': base, 'model': model, 'metric': name,
                           'gain_nat': float(dif[mask].mean()),
                           'date_bootstrap_95': np.quantile(vals, [.025, .975]).tolist(),
                           'equal_date_gain': float(date_means.mean()),
                           'n': int(mask.sum()), 'dates_with_observations': int(sum(ns > 0))})
    return result

def witness(p, z, ratio):
    p = np.asarray(p, float)
    selected = np.array([q >= 3 and m != 0 for q in range(5) for m in range(3)])
    refchoice = np.array([m == (1 if z == 1 else 2) for q in range(5) for m in range(3)])
    e = p[selected].sum()
    a = p[selected & refchoice].sum(); b = e - a
    q = a / e
    theta = q / (q + ratio * (1 - q))
    s = np.array([a / theta, b / (1 - theta)])
    interval = [q / (1/e - (1-q)), (1/e-q)/(1-q)]
    result = {'R': float(ratio), 'eligibility': float(e), 'observed_reference_choice': float(q),
              'latent_reference_preference': float(theta),
              'revelation_probabilities': s.tolist(), 'feasible_R_interval': interval,
              'feasible': bool(np.all(s <= 1 + 1e-12))}
    if result['feasible']:
        k = np.zeros((2, 15))
        for j in range(15):
            if selected[j]:
                w = 0 if refchoice[j] else 1
                k[w, j] = p[j] / (theta if w == 0 else 1 - theta)
            else:
                k[:, j] = (1 - s) * p[j] / (1 - e) if e < 1 else 0
        rebuilt = theta * k[0] + (1-theta) * k[1]
        result.update({'observed_15cell': p.tolist(), 'latent_emission_2x15': k.tolist(),
                       'reconstructed_15cell': rebuilt.tolist(),
                       'max_cell_error': float(np.max(np.abs(rebuilt - p))),
                       'emission_row_sums': k.sum(axis=1).tolist()})
        assert result['max_cell_error'] < 1e-12
        assert np.max(np.abs(k.sum(axis=1) - 1)) < 1e-12
        assert np.min(k) > -1e-12
    return result

def make_witnesses(rows, beta):
    main = [r for r in rows if r['t'] == 'T']
    p = np.zeros(15)
    # Encode color relative to first demonstration for this aggregate witness.
    for r in main:
        q = r['Q']
        if r['z'] == -1:
            q = {0:0, 1:2, 2:1, 3:4, 4:3}[q]
        m = 0 if not r['B'] else 1 if r['copy'] else 2
        p[3*q+m] += 1/len(main)
    empirical = [witness(p, 1, ratio) for ratio in (1, 1.25, 1.5, 5/3, 2, 2.5, 3)]
    contexts = []
    for t in ('T', 'C1', 'C2'):
        for z in (-1, 1):
            candidates = [r for r in rows if r['t'] == t and r['z'] == z]
            context = dict(candidates[0]); cells = joint_cells([context], 'primacy', beta)[0]
            contexts.append({'t': t, 'z': z, 'n': len(candidates), 'p': cells})
    def latent_T(ratio):
        selected = [c for c in contexts if c['t'] == 'T']
        return sum(c['n'] * witness(c['p'], c['z'], ratio)['latent_reference_preference']
                   for c in selected) / sum(c['n'] for c in selected)
    lo, hi = .01, 100.
    for _ in range(80):
        mid = (lo + hi)/2
        if latent_T(mid) > .5: lo = mid
        else: hi = mid
    tipping = (lo+hi)/2
    ratios = sorted(set((1., 1.25, 1.5, 5/3, 2., 2.5, 3., tipping, tipping*1.25)))
    common = []
    for ratio in ratios:
        w = [{'t': c['t'], 'z': c['z'], 'n': c['n'], **witness(c['p'], c['z'], ratio)}
             for c in contexts]
        common.append({'R': ratio, 'all_six_feasible': all(x['feasible'] for x in w),
                       'mean_T_latent_reference_preference': latent_T(ratio),
                       'contexts': w})
    toy = np.zeros(15); toy[10] = .35; toy[11] = .25; toy[13] = .25; toy[14] = .15
    return {'definition': 'W is standardized-two-courter preference, observed only under eligible consistency; noneligible emissions independent of W',
            'empirical_T': empirical, 'fitted_P_common_R': common, 'fitted_T_null_tipping_R': tipping,
            'e_one_control': {'R1': witness(toy, 1, 1), 'R2': witness(toy, 1, 2)}}

def strata(rows):
    tables = []
    for t in ('T', 'C1', 'C2'):
        for first in (None, 0, 1):
            r = [x for x in rows if x['t'] == t and x['first_match'] == first]
            mates = [x for x in r if x['B']]
            e = [x for x in r if x['eligible']]
            one = [x for x in mates if not x['D']]
            tables.append({'t': t, 'first_courter_matches_reference': first,
                           'all_n': len(r), 'mating_n': len(mates), 'eligible_n': len(e),
                           'eligible_copy_n': sum(x['copy'] for x in e),
                           'one_or_no_courtship_mating_n': len(one),
                           'one_or_no_courtship_copy_n': sum(x['copy'] for x in one),
                           'double_given_mating': len(e)/len(mates) if mates else None,
                           'copy_given_eligible': sum(x['copy'] for x in e)/len(e) if e else None})
    main = [x for x in tables if x['t'] == 'T' and x['eligible_n']]
    return {'first_courter_table': tables,
            'T_equal_first_courter_standardized_copy': sum(x['copy_given_eligible'] for x in main)/len(main),
            'warning': 'Descriptive post-exposure strata; not a causal adjustment or a counterfactual choice observation.'}

def color_swap(rows):
    return [dict(r, z=-r['z'], f=-r['f'], F=int(r['A'] and not r['F']),
                 Q={0:0,1:2,2:1,3:4,4:3}[r['Q']],
                 M={0:0,1:2,2:1}[r['M']], Y=int(r['B'] and not r['Y'])) for r in rows]

def synthetic(g, seed, n=3000):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        t = ('T','C1','C2')[i % 3]; z = 1 if rng.random() < .5 else -1
        a = int(rng.random() < .85)
        f = (1 if rng.random() < expit(.1+.3*z) else -1) if a else 0
        d = int(a and rng.random() < expit(.2-.25*z*f))
        q = 0 if not a else (3 if f == 1 else 4) if d else (1 if f == 1 else 2)
        b = int(rng.random() < expit(.4 + .8*a + .15*z*f))
        yg = int(b and rng.random() < expit(.1 + (1.5 if not d else .5)*f + g*z))
        m = 0 if not b else 1 if yg else 2
        rows.append({'row':i, 'date':'sim%02d' % (i%15), 'device':'sim', 't':t,
                     'z':z, 'A':a, 'F':int(f==1), 'f':f, 'D':d, 'Q':q, 'B':b,
                     'Y':yg, 'M':m, 'eligible':int(d and b),
                     'copy':int((m==1)==(z==1)) if b else None,
                     'first_match':int(f==z) if a else None})
    return rows

def numerical_controls(rows, full):
    x = features([r for r in rows if r['B']], 'Y', 'primacy')
    y = np.array([r['Y'] for r in rows if r['B']])
    b = np.linspace(-.25,.35,x.shape[1]); eps = 1e-5
    analytic = objective(b,x,y)[1]
    finite = np.zeros(len(b))
    for j in range(len(b)):
        dx = np.zeros(len(b)); dx[j] = eps
        finite[j] = (objective(b+dx,x,y)[0]-objective(b-dx,x,y)[0])/(2*eps)
    repeat, rec = fit_model(rows, 'primacy', start_shift=.25, strict=True)
    original_cells = joint_cells(rows[:6], 'primacy', full)
    repeat_cells = joint_cells(rows[:6], 'primacy', repeat)
    swapped, sr = fit_model(color_swap(rows), 'primacy', strict=True)
    swapped_cells = joint_cells(color_swap(rows[:6]), 'primacy', swapped)
    idx = [3*{0:0,1:2,2:1,3:4,4:3}[q]+{0:0,1:2,2:1}[m]
           for q in range(5) for m in range(3)]
    # P at exact g=0 has the E predictor and likelihood before fitting.
    e_beta, _ = fit_model(rows, 'expression')
    zero_beta = dict(e_beta); zero_beta['Y'] = np.r_[e_beta['Y'], 0.]
    zero_error = np.max(np.abs(joint_cells(rows[:6],'expression',e_beta)-
                               joint_cells(rows[:6],'primacy',zero_beta)))
    result = {'finite_difference_gradient_max_error': float(np.max(np.abs(finite-analytic))),
              'repeat_full_prediction_max_error': float(np.max(np.abs(original_cells-repeat_cells))),
              'color_relabel_prediction_max_error': float(np.max(np.abs(original_cells-swapped_cells[:,idx]))),
              'g_zero_nesting_max_error': float(zero_error), 'repeat_fit': rec, 'color_fit': sr,
              'synthetic': []}
    for g, seed in ((1.,20261032),(0.,20261033)):
        sim = synthetic(g, seed)
        cvv, _ = cv(sim, retain_fits=False)
        fit, fit_records = fit_model(sim,'primacy')
        ag = aggregate(sim,cvv)
        result['synthetic'].append({'true_g':g,'seed':seed,'n':len(sim),
                                    'fitted_g':float(fit['Y'][-1]),'fit':fit_records['Y'],
                                    'cv':ag,
                                    'primacy_gain_vs_expression_joint':ag['expression']['joint']['nll']-ag['primacy']['joint']['nll'],
                                    'primacy_gain_vs_expression_eligible':ag['expression']['eligible_choice']['nll']-ag['primacy']['eligible_choice']['nll']})
    assert result['finite_difference_gradient_max_error'] < 1e-6
    assert result['repeat_full_prediction_max_error'] < 1e-5
    assert result['color_relabel_prediction_max_error'] < 1e-5
    assert result['g_zero_nesting_max_error'] < 1e-14
    return result

def main():
    started = time.time()
    protocol = read(OUT/'PROTOCOL.md')
    raw = read(ROOT/'data/social_learning/data_primacy.csv')
    assert READS[-1]['sha256'] == '0f723df5825865d214e3064c1e16f0e489211f25e45f3eb34e7dfb5c4ebf568b'
    rows = reconstruct(raw)
    for filename in ('manifest.json','dryad_metadata.json','dryad_files.json',
                     'figshare_data_metadata.json','figshare_supp_metadata.json',
                     'zenodo_metadata.json','primacy_bias_script.Rmd'):
        read(ROOT/'data/social_learning'/filename)
    count = []
    for t in ('T','C1','C2'):
        r = [x for x in rows if x['t']==t]; e = [x for x in r if x['eligible']]
        count.append({'t':t,'n':len(r),'eligible':len(e),'eligible_copy':sum(x['copy'] for x in e),
                      'mating':sum(x['B'] for x in r),'any_recorded_courtship':sum(x['A'] for x in r),
                      'double_recorded_courtship':sum(x['D'] for x in r)})
    assert [(x['eligible'],x['eligible_copy']) for x in count] == [(64,40),(74,46),(67,42)]
    assert len(rows)==462
    counts = {'n':len(rows),'counts':count,
              'joint_cells':{t:[[sum(r['t']==t and r['Q']==q and r['M']==m for r in rows)
                                  for m in range(3)] for q in range(5)] for t in ('T','C1','C2')},
              'mating_with_no_recorded_courtship':sum(r['B'] and not r['A'] for r in rows),
              'one_courter_mating_to_other_color':sum(r['B'] and r['A'] and not r['D'] and r['F']!=r['Y'] for r in rows),
              'date_counts':dict(collections.Counter(r['date'] for r in rows)),
              'trial_unit':'one-use flies per Methods; simultaneous blocks/pictures unavailable',
              'schema_has_timestamps':False}
    save('RECONSTRUCTION.json',counts)
    dump_csv('reconstructed.csv',rows)
    split = [{'held_date':d,'train_n':sum(r['date']!=d for r in rows),
              'test_n':sum(r['date']==d for r in rows)} for d in sorted(counts['date_counts'])]
    save('SPLIT.json', {'recipe':'leave one recorded date out; consumed exploratory check',
                        'protocol_sha256':hashlib.sha256(protocol).hexdigest(),'folds':split})
    print(json.dumps({'phase':'reconstruction','counts':counts['counts'],
                      'no_courtship_matings':counts['mating_with_no_recorded_courtship'],
                      'protocol_sha256':hashlib.sha256(protocol).hexdigest()}),flush=True)
    losses, folds = cv(rows)
    save('CV_FITS.json',folds)
    ag = aggregate(rows,losses); dif = contrasts(rows,losses)
    eligible = [r for r in rows if r['eligible']]
    eloss, efold = cv(eligible,eligible_only=True)
    eagg = aggregate(eligible,eloss,True); ediff = contrasts(eligible,eloss,True)
    save('ELIGIBLE_ONLY_FITS.json',efold)
    save('COMPARISON.json',{'status':'consumed-data exploratory out-of-date prediction',
                           'metric':'natural-log loss; gain=baseline loss minus candidate loss',
                           'joint_models':ag,'contrasts':dif,
                           'eligible_only_models':eagg,'eligible_only_contrasts':ediff,
                           'uncertainty':'5000 paired date-proxy resamples; not calibrated coverage or refit uncertainty',
                           'seed':SEED,'meaningful_gain_nat':.01})
    perrow = []
    for i,r in enumerate(rows):
        for m in MODELS:
            perrow.append({'row':r['row'],'held_date':r['date'],'t':r['t'],'model':m,
                           'eligible':r['eligible'],'mating':r['B'],
                           **{k:float(v[i]) for k,v in losses[m].items()}})
    dump_csv('CV_LOSSES.csv',perrow)
    dump_csv('ELIGIBLE_ONLY_LOSSES.csv',[
        {'row':r['row'],'held_date':r['date'],'t':r['t'],'model':m,'Y':float(eloss[m]['Y'][i])}
        for i,r in enumerate(eligible) for m in eloss])
    fulls = {}; records = {}
    for m in MODELS:
        fulls[m],records[m]=fit_model(rows,m)
    save('FULL_FITS.json',records)
    context_output = []
    for t in ('T','C1','C2'):
        for z in (-1,1):
            r = next(r for r in rows if r['t']==t and r['z']==z)
            context_output.append({'t':t,'reference_color':'green' if z==1 else 'pink',
                                   'models':{m:joint_cells([r],m,fulls[m])[0].tolist() for m in MODELS}})
    save('FULL_JOINT_PREDICTIONS.json',{'Q':Q_NAMES,'M':M_NAMES,'flattening':'3*Q+M','contexts':context_output})
    save('SENSITIVITY.json',make_witnesses(rows,fulls['primacy']))
    save('FIRST_COURTER.json',strata(rows))
    save('CONTROLS.json',numerical_controls(rows,fulls['primacy']))
    save('MANIFEST.json',{'immutable_input_reads':READS,
                          'source_links':[
                              'https://doi.org/10.5061/dryad.hx3ffbgnr',
                              'https://ndownloader.figshare.com/files/46746183',
                              'https://ndownloader.figshare.com/files/46746186',
                              'https://pmc.ncbi.nlm.nih.gov/articles/PMC11295924/',
                              'https://pmc.ncbi.nlm.nih.gov/articles/PMC5905535/'],
                          'preserved_lineage':'All462rows and all earlier social findings consumed; original bytes unchanged; no other scientific lineage touched.'})
    save('RUN.json',{'completed_utc':datetime.now(timezone.utc).isoformat(),
                     'elapsed_seconds':time.time()-started,'python':sys.version,
                     'platform':platform.platform(),'numpy':np.__version__,'scipy':scipy.__version__,
                     'scientific_input_read_bytes':sum(x['bytes'] for x in READS),
                     'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                     'fit_count':len(FITS),'non_success_optimizer_results':sum(not x['success'] for x in FITS),
                     'max_projected_gradient':max(x['projected_gradient_max'] for x in FITS),
                     'threads':{k:os.environ[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')},
                     'public_requests_by_this_script':0,'jobs_after_completion':0})
    print(json.dumps({'phase':'complete','joint':{m:ag[m]['joint']['nll'] for m in MODELS},
                      'eligible_choice':{m:ag[m]['eligible_choice']['nll'] for m in MODELS},
                      'main_eligible_choice':{m:ag[m]['T_eligible_choice']['nll'] for m in MODELS},
                      'elapsed_seconds':time.time()-started},indent=2),flush=True)

if __name__ == '__main__':
    main()
