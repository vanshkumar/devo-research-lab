"""Independent finite-history check of the declared iid-Beta observation completion."""
import json
import time
import numpy as np
from numpy.polynomial.hermite import hermgauss
from scipy.special import expit
from independent import (OLD, AUTHOR, OUT, blob, obj, frame, save, utc, usage,
    DECAY, prefix_state, calibrate, coefficients, design, integrated)


def main():
    began = time.perf_counter()
    val = frame(OLD / 'inputs/validation_numeric.csv')
    person = obj(AUTHOR / 'FORECAST_INPUTS.json')['people'][0]
    fits = [obj(OLD / ('outputs/primary/' + v + '_fit.json')) for v in ['shared', 'no_history']]
    rows = val.loc[val.subject == person['subject']].sort_values('trial').reset_index(drop=True)
    prefix = rows.iloc[:200]
    initial_h, initial_prev = prefix_state(prefix)
    target = np.array(person['teacher_side'][200:204])
    # Deliberately uncertain constructed prior exposes current-response weighting.
    alpha = beta = .5
    exact = np.empty((4, 2))
    configurations = []
    mass_checks = []
    for m, fit in enumerate(fits):
        _, cal = calibrate(prefix, fit)
        nb, hb = coefficients(fit, cal, int(person['condition']))
        configurations.append((cal, nb, hb))
        states = [(initial_h.copy(), initial_prev, 0, 0, 1.)]
        masses = []
        for t in range(4):
            numerator = denominator = 0.
            following = []
            for h, prev, omitted, responded, w in states:
                q = (alpha+omitted)/(alpha+beta+t)
                eta, z = design(float(rows.sideContrast.iloc[200+t]), 200+t, prev, h, fit, cal, int(person['condition']))
                p = integrated(eta, z, fit)
                numerator += w*(1-q)*p
                denominator += w*(1-q)
                decay_only = DECAY*h
                revealed = decay_only+(1-DECAY)*target[t]
                following.extend([(decay_only, 0., omitted+1, responded, w*q),
                                  (revealed, 1., omitted, responded+1, w*(1-q)*p),
                                  (revealed, -1., omitted, responded+1, w*(1-q)*(1-p))])
            exact[t, m] = numerator/denominator
            states = following
            masses.append(dict(states=len(states), total_mass=sum(x[-1] for x in states),
                               current_response_probability=denominator))
        mass_checks.append(masses)
    repetitions = np.empty((4, 4, 2))
    nodes, weights = hermgauss(20)
    weights = weights/np.sqrt(np.pi)
    for r in range(4):
        rng = np.random.default_rng(2026110250+r)
        n = 65536
        q = rng.beta(alpha, beta, n)
        weight = 1-q
        h = np.tile(initial_h, (n, 1))
        prev = np.full((2, n), initial_prev)
        for t in range(4):
            ch_uniform, om_uniform = rng.random(n), rng.random(n)
            omit = om_uniform < q
            contrast = float(rows.sideContrast.iloc[200+t])
            for m, fit in enumerate(fits):
                cal, nb, hb = configurations[m]
                base, _ = design(contrast, 200+t, 0., np.zeros(3), fit, cal, int(person['condition']))
                eta = base + nb[5]*prev[m] + np.sum(h*hb[None, :], axis=1)
                variance = fit['config']['random_sd']**2 * (1 + np.sign(contrast)**2 +
                    (np.sum(h*h, axis=1) if m == 0 else 0))
                prob = np.zeros(n)
                for node, w in zip(nodes, weights):
                    prob += w*expit(eta+np.sqrt(2*variance)*node)
                repetitions[r, t, m] = np.sum(weight*prob)/weight.sum()
                prev[m] = np.where(omit, 0., np.where(ch_uniform < prob, 1., -1.))
            h = DECAY[None, :]*h + (1-DECAY)[None, :]*np.where(omit, 0., target[t])[:, None]
    diff = repetitions.mean(axis=0)-exact
    se = repetitions.std(axis=0, ddof=1)/2
    result = dict(utc=utc(), person=person['subject'], steps=4, models=['shared', 'no_history'],
        scope='Constructed Beta(.5,.5) omission prior, original prefix/fit/first-four source inputs; a numerical law check, not empirical engagement validation or an additional contrary',
        exact_probabilities=exact.tolist(), repetition_probabilities=repetitions.tolist(),
        difference=diff.tolist(), standard_error=se.tolist(),
        max_abs_difference=float(np.max(np.abs(diff))),
        mass_and_response_probability_checks=mass_checks,
        within_six_simulation_standard_errors=bool(np.all(np.abs(diff) <= 6*se+1e-10)),
        exact_terminal_paths_per_model=81, repetitions=4, trajectories_per_repetition=65536,
        elapsed_seconds=time.perf_counter()-began, **usage())
    save('OMISSION_REFERENCE.json', result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['reads', 'repetition_probabilities']}, indent=2), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        save('OMISSION_REFERENCE_FAILURE.json', dict(utc=utc(), exception=repr(exc), **usage()))
        raise
