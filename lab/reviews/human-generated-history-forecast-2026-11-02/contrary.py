"""The single prespecified persistent-coefficient joint-extension challenge."""
import itertools
import json
import time

import numpy as np
from scipy.special import expit, ndtri
from scipy.stats import qmc
from independent import (OLD, AUTHOR, OUT, blob, obj, frame, save, utc, usage,
                         score_arrays, bootstrap_summary, no_omission_path, integrated)


def recurse_given_latent(path, latent, lag=None, steps=400):
    """Exact binary-state integration conditional on each fixed residual vector."""
    ell = path['lag'] if lag is None else lag
    n = latent.shape[0]
    eta = path['eta0'][:steps, None] + np.einsum('td,nd->tn', path['loading'][:steps], latent)
    pminus = expit(eta - ell)
    pplus = expit(eta + ell)
    mass = expit(eta[0] + ell * path['initial_previous'])
    out = np.empty((steps, n))
    out[0] = mass
    for t in range(1, steps):
        mass = mass * pplus[t] + (1-mass) * pminus[t]
        out[t] = mass
    return out


def enumerate_given_latent(path, latent, steps=4):
    result = np.zeros((steps, len(latent)))
    total = np.zeros(len(latent))
    for choices in itertools.product([-1., 1.], repeat=steps):
        weight = np.ones(len(latent))
        prev = path['initial_previous']
        for t, ch in enumerate(choices):
            eta = path['eta0'][t] + path['lag'] * prev + np.einsum('nd,d->n', latent, path['loading'][t])
            p = expit(eta)
            weight *= p if ch == 1. else 1-p
            prev = ch
        total += weight
        for t, ch in enumerate(choices):
            if ch == 1.:
                result[t] += weight
    return result, total


def enumerate_kernel(path, fit, steps=4):
    result, total = np.zeros(steps), 0.
    for choices in itertools.product([-1., 1.], repeat=steps):
        weight, prev = 1., path['initial_previous']
        for t, ch in enumerate(choices):
            p = integrated(path['eta0'][t] + path['lag']*prev, path['loading'][t], fit)
            weight *= p if ch == 1. else 1-p
            prev = ch
        total += weight
        result += weight * (np.array(choices) == 1.)
    return result, total


def main():
    began = time.perf_counter()
    plan_pin = __import__('hashlib').sha256(blob(OUT / 'CONTRARY_PLAN.md')).hexdigest()
    val = frame(OLD / 'inputs/validation_numeric.csv')
    split = frame(OLD / 'protocol/split_manifest.csv').set_index('subject')
    inputs = obj(AUTHOR / 'FORECAST_INPUTS.json')
    fits = [obj(OLD / ('outputs/primary/' + v + '_fit.json')) for v in ['shared', 'no_history']]
    people = [x['subject'] for x in inputs['people']]
    paths, kernel = [], np.empty((39, 400, 2))
    for i, person in enumerate(inputs['people']):
        rows = val.loc[val.subject == person['subject']].sort_values('trial').reset_index(drop=True)
        pair = []
        for m, fit in enumerate(fits):
            kernel[i, :, m], path = no_omission_path(rows, np.array(person['teacher_side']), fit)
            pair.append(path)
        paths.append(pair)
    values = np.empty((8, 39, 400, 2))
    checks = dict(kernel_enumeration=[], persistent_enumeration=[], zero_variance=[], zero_lag=[])
    no_lag_means = np.empty((8, 4, 2))
    for r in range(8):
        normals = ndtri(qmc.Sobol(d=5, scramble=True, seed=2026110201+r).random_base2(14))
        for i, pair in enumerate(paths):
            for m, path in enumerate(pair):
                dim = path['loading'].shape[1]
                latent = normals[:, :dim] * fits[m]['config']['random_sd']
                # One person/model at a time; no particle-by-time arrays retained across calls.
                marginal = recurse_given_latent(path, latent)
                values[r, i, :, m] = marginal.mean(axis=1)
                del marginal
                if i == 0:
                    no_lag_means[r, :, m] = recurse_given_latent(path, latent, lag=0., steps=4).mean(axis=1)
                    if r == 0:
                        enumerated, total = enumerate_given_latent(path, latent[:8], steps=4)
                        reference = recurse_given_latent(path, latent[:8], steps=4)
                        checks['persistent_enumeration'].append(dict(model=fits[m]['variant'],
                            max_abs_difference=float(np.max(np.abs(enumerated-reference))),
                            maximum_total_mass_error=float(np.max(np.abs(total-1)))))
                        e, total = enumerate_kernel(path, fits[m], steps=4)
                        checks['kernel_enumeration'].append(dict(model=fits[m]['variant'],
                            max_abs_difference=float(np.max(np.abs(e-kernel[0, :4, m]))),
                            total_mass_error=abs(total-1)))
                        zero = np.zeros((1, dim))
                        zrec = recurse_given_latent(path, zero, steps=4)[:, 0]
                        no_sd = dict(fits[m], config=dict(fits[m]['config'], random_sd=0.))
                        zkernel = []
                        for t in range(4):
                            if t == 0:
                                zkernel.append(integrated(path['eta0'][t] + path['lag']*path['initial_previous'], path['loading'][t], no_sd))
                            else:
                                pm = integrated(path['eta0'][t]-path['lag'], path['loading'][t], no_sd)
                                pp = integrated(path['eta0'][t]+path['lag'], path['loading'][t], no_sd)
                                zkernel.append(zkernel[-1]*pp + (1-zkernel[-1])*pm)
                        checks['zero_variance'].append(dict(model=fits[m]['variant'], max_abs_difference=float(np.max(np.abs(zrec-zkernel)))))
        print(f'Independent persistent-coefficient scramble {r+1}/8 complete', flush=True)
    for m in range(2):
        path = paths[0][m]
        exact = np.array([integrated(path['eta0'][t], path['loading'][t], fits[m]) for t in range(4)])
        difference = no_lag_means[:, :, m].mean(axis=0)-exact
        se = no_lag_means[:, :, m].std(axis=0, ddof=1)/np.sqrt(8)
        checks['zero_lag'].append(dict(model=fits[m]['variant'], difference=difference.tolist(),
            integration_se=se.tolist(), max_abs_difference=float(np.max(np.abs(difference)))))
    # Algebraically each responding action reveals the same scheduled side.
    checks['choice_feedback_target_identity'] = all(ch*(ch*side) == side for ch in [-1., 1.] for side in [-1., 1.])
    mean = values.mean(axis=0)
    per = score_arrays(mean, people, val)
    original_per = score_arrays(kernel, people, val)
    summary = bootstrap_summary(per, split)
    kernel_summary = bootstrap_summary(original_per, split)
    replicate_gain = np.array([np.mean([x['primary'] for x in score_arrays(p, people, val)]) for p in values])
    loo = np.array([np.mean([x['primary'] for x in score_arrays(np.delete(values, r, axis=0).mean(axis=0), people, val)]) for r in range(8)])
    mcse = float(np.sqrt(7/8 * np.sum((loo-loo.mean())**2)))
    shifts = mean-kernel
    difference_per = np.array([p['primary']-q['primary'] for p,q in zip(per, original_per)])
    first_se = values[:, :, 0, :].std(axis=0, ddof=1)/np.sqrt(8)
    result = dict(utc=utc(), plan_sha256=plan_pin, seeds=list(range(2026110201, 2026110209)),
        scrambles=8, points_per_scramble=2**14, postvalidation=True,
        setting='zero omissions; same frozen Gaussian variance, coefficients, calibration and exact known future schedule',
        persistent_summary=summary, reintegrated_kernel_summary=kernel_summary,
        primary_gain_change=float(difference_per.mean()), person_gain_changes=difference_per.tolist(),
        score_integration_mcse=mcse, replicate_gains=replicate_gain.tolist(),
        primary_point_and_positive_interval_criterion_retained=bool(summary['primary']['mean'] >= .01 and summary['primary']['low'] > 0 and mcse < .001),
        probability_shift_max_abs=float(np.max(np.abs(shifts))), probability_shift_mean_abs=float(np.mean(np.abs(shifts))),
        first_trial_gaussian_integration_max_abs_difference=float(np.max(np.abs(shifts[:,0]))),
        first_trial_max_integration_se=float(np.max(first_se)),
        controls=checks, elapsed_seconds=time.perf_counter()-began, **usage())
    np.savez_compressed(OUT / 'CONTRARY_FORECASTS.npz', persistent_repetitions=values, reintegrated_kernel=kernel)
    save('CONTRARY.json', result)
    save('CONTRARY_PERSON_SCORES.json', per)
    print(json.dumps({k:v for k,v in result.items() if k not in ['reads', 'persistent_summary', 'reintegrated_kernel_summary', 'person_gain_changes']}, indent=2), flush=True)
    print(json.dumps(dict(primary=summary['primary'], original_primary=kernel_summary['primary']), indent=2), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        save('CONTRARY_FAILURE.json', dict(utc=utc(), exception=repr(exc), **usage()))
        raise
