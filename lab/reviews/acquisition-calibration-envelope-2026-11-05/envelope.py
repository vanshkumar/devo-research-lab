"""Single-pass old-64 envelopes. No later case-level input path."""

import json
import os
from pathlib import Path
import resource
import sys
import time
from datetime import datetime, timezone

CPU, WALL = time.process_time(), time.monotonic()
HERE = Path(__file__).resolve().parent
DEADLINE = 1793924852  # 23:32:32 UTC + 55 minutes
ROUND_PAD = 2e-10

import numpy as np
from scipy.optimize import isotonic_regression

# Reuse the exact released member and chronology checks. No fitting code is called.
sys.path.insert(0, str(HERE.parent.parent / 'tasks' / 'acquisition-calibration-attribution-2026-11-05'))
from develop import EXPOSURE, load_old64, owner_names, ratios


def save(name, value):
    dst = HERE / name
    tmp = dst.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(dst)


def half_pair_distance(q):
    n = q.shape[-1]
    return np.sum(q * (2 * np.arange(n) + 1 - n), axis=-1) / n**2


def losses(q, y):
    return np.mean(np.abs(q - y[:, None]), axis=-1) - half_pair_distance(q)


def distance(x, y):
    g = np.sqrt(np.maximum(x, y)**2 - np.maximum(x, y) + 1)
    return np.where((x < 0) & (y < 0), 0,
                    np.where((x < 0) | (y < 0), g, np.abs(x - y)))


def rank_oracle(q, y, missing=None, identity=None):
    """Columns are common conditional rank intervals, including ties."""
    n, ranks = q.shape
    missing = np.zeros(n) if missing is None else np.asarray(missing)
    identity = np.full(ranks, 1 / ranks) if identity is None else identity
    p = 1 - missing
    constant = np.mean(missing * distance(-1., y))
    a = np.mean(p[:, None] * (distance(q, y[:, None]) -
                              missing[:, None] * distance(q, -1.)), axis=0)
    dx = np.diff(np.mean(p[:, None]**2 * q, axis=0))
    assert np.all(dx >= 0)
    use = dx > 0
    cdf = np.zeros(ranks - 1)
    if np.any(use):
        centers = .5 + np.diff(a)[use] / (2 * dx[use])
        fit = isotonic_regression(centers, weights=dx[use]).x
        cdf[use] = np.clip(fit, 0, 1)
        cdf = np.maximum.accumulate(cdf)
    w = np.diff(np.r_[0., cdf, 1.])
    assert np.min(w) >= 0 and abs(w.sum() - 1) < 1e-12

    def score(masses):
        cumulative = np.cumsum(masses)[:-1]
        return float(constant + np.sum(a * masses) -
                     np.sum(dx * cumulative * (1 - cumulative)))

    gradient = a + np.r_[np.cumsum((dx * (2 * cdf - 1))[::-1])[::-1], 0.]
    gap = float(max(0., np.sum(gradient * w) - gradient.min()))
    assert gap < 1e-9
    raw, fit_risk = score(identity), score(w)
    assert raw + ROUND_PAD >= fit_risk
    return {'raw_risk': raw, 'witness_risk': fit_risk,
            'gain_witness': raw - fit_risk,
            'gain_upper': raw - fit_risk + gap + ROUND_PAD,
            'gain_strict_support_witness': raw - score((1 - 1e-6) * w + 1e-6 * identity),
            'fw_gap': gap, 'nonzero_mass_intervals': int(np.count_nonzero(w)),
            'conditional_mass_mean_rank': float(w @ (np.cumsum(identity) - .5 * identity))}, w


def value_oracle(q, y):
    """Exact empirical CRPS optimum for a shared monotone map, zero missing."""
    n, p = q.shape
    assert np.all((q >= 0) & (q <= 1)) and np.all((y >= 0) & (y <= 1))
    order = np.argsort(q.ravel(), kind='stable')
    values = q.ravel()[order]
    case, rank = divmod(order, p)
    # A distinct value shared by any number of particles enters as one event.
    states = np.r_[0, np.flatnonzero(np.r_[values[:-1] != values[1:], True]) + 1]
    sum_squares = np.r_[0, np.cumsum(2 * rank + 1)][states]
    edges = np.unique(np.r_[0., y, 1.])
    selected, minimum = [], []
    for t in edges[:-1]:
        hit = y <= t
        cross = np.r_[0, np.cumsum(hit[case], dtype=np.int64)][states]
        costs = sum_squares - 2 * p * cross + p**2 * np.count_nonzero(hit)
        index = int(np.argmin(costs))
        selected.append(states[index])
        minimum.append(costs[index])
    assert np.all(np.diff(selected) >= 0)
    optimum = float(np.diff(edges) @ np.asarray(minimum) / (n * p**2))
    mapped = np.empty(n * p)
    mapped[order] = edges[np.searchsorted(selected, np.arange(1, n * p + 1))]
    mapped = mapped.reshape(q.shape)
    reconstructed = float(losses(mapped, y).mean())
    raw = float(losses(q, y).mean())
    assert abs(reconstructed - optimum) < 1e-9 and raw + ROUND_PAD >= optimum
    return {'raw_risk': raw, 'witness_risk': reconstructed,
            'gain_witness': raw - reconstructed, 'gain_upper': raw - optimum + ROUND_PAD,
            'threshold_lower_risk': optimum, 'witness_error': abs(optimum - reconstructed),
            'states': int(len(states)), 'target_intervals': int(len(minimum))}


def controls():
    atoms = np.array([-1., 0., .25, 1.])
    mass = np.array([.2, .4, .2, .2])
    y = np.array([-1., 0., 0., .25, 1.])
    summary, recovered = rank_oracle(np.tile(atoms[1:], (len(y), 1)), y, np.full(len(y), .2))
    exact = np.mean(distance(atoms[None, :], y[:, None]) @ mass) - (
        .5 * mass @ distance(atoms[:, None], atoms) @ mass)
    assert np.max(np.abs(recovered - [.5, .25, .25])) < 1e-9
    assert abs(exact - summary['witness_risk']) < 1e-9
    all_missing, _ = rank_oracle(np.zeros((1, 1)), np.array([-1.]), np.ones(1))
    assert all_missing['witness_risk'] == 0
    tied_q = np.tile([0., .25, .25, 1.], (2, 1))
    tied_y = np.array([0., 1.])
    tied_rank, _ = rank_oracle(tied_q, tied_y)
    tied_value = value_oracle(tied_q, tied_y)
    assert abs(tied_rank['raw_risk'] - losses(tied_q, tied_y).mean()) < 1e-9
    q = np.array([[.1, .1], [.2, .2], [.4, .4]])
    shift_y = q[:, 0] + .2
    off_rank, _ = rank_oracle(q, shift_y)
    off_value = value_oracle(q, shift_y)
    assert abs(off_rank['gain_witness']) < 1e-9 and abs(off_value['gain_witness'] - .2) < 1e-9
    opposing = value_oracle(np.array([[.2], [.8]]), np.array([.9, .1]))
    assert abs(opposing['witness_risk'] - .4) < 1e-9
    return {'mixed_missing_recovered_weights': recovered.tolist(), 'mixed_exact_risk': float(exact),
            'mixed_witness_risk': summary['witness_risk'], 'all_missing': all_missing,
            'tied_rank': tied_rank, 'tied_value': tied_value,
            'off_support_rank': off_rank, 'off_support_value': off_value,
            'ordered_forecasts_reversed_outcomes_value': opposing}


def groups(owners, rosters):
    o = np.repeat(owners, 2)
    r = np.repeat(rosters, 2)
    s = np.tile(['L', 'R'], len(owners))
    return {'pooled': np.repeat('all', len(o)), 'sign': s,
            'roster_sign': np.char.add(np.char.add(r, '/'), s),
            'owner_roster_sign': np.array([f'{a}/{b}/{c}' for a, b, c in zip(o, r, s)])}


def envelopes(q, y, labels):
    summaries = {}
    for group in np.unique(labels):
        keep = labels == group
        rank, _ = rank_oracle(q[keep], y[keep])
        value = value_oracle(q[keep], y[keep])
        summaries[str(group)] = {'n_sign_rows': int(keep.sum()), 'rank': rank, 'value': value}
    total = {}
    for name in ('rank', 'value'):
        total[name] = {key: sum(row['n_sign_rows'] * row[name][key]
                                for row in summaries.values()) / len(y)
                       for key in ('raw_risk', 'witness_risk', 'gain_witness', 'gain_upper')}
    return {'equal_original_row_weights': total, 'cells': summaries}


OWNER_192 = {'angelakilab': 85, 'churchland_common_owner': 31, 'cortexlab': 14,
             'danlab': 6, 'hausserlab': 11, 'hoferlab': 3, 'mainenlab': 24,
             'mrsicflogellab': 7, 'steinmetzlab': 7, 'wittenlab': 4}


def owner_translation(q, y, owners, rosters):
    raw = losses(q, y)
    gains = np.zeros(len(y))
    folds = {}
    repeated = np.repeat(owners, 2)
    for owner in np.unique(owners):
        keep = repeated == owner
        shift = float(np.median(y[~keep, None] - q[~keep]))
        gains[keep] = raw[keep] - losses(np.clip(q[keep] + shift, 0, 1), y[keep])
        folds[str(owner)] = {'n_animals': int(keep.sum() // 2), 'shift': shift,
                             'gain': float(gains[keep].mean())}
    overlap = {name: n for name, n in OWNER_192.items() if name in folds}
    return {'source_all_median': float(np.median(y[:, None] - q)), 'owner_folds': folds,
            'gain': float(gains.mean()),
            'old_roster_gains': {str(r): float(gains[np.repeat(rosters == r, 2)].mean())
                                 for r in np.unique(rosters)},
            'common_owner_target_weighted_gain': sum(n * folds[k]['gain'] for k, n in overlap.items())
            / sum(overlap.values()), 'later_animals_covered_by_owner_label': sum(overlap.values()),
            'unsupported_owner_animals': 192 - sum(overlap.values())}


def score_at(q, y):
    prefix = np.r_[0., np.cumsum(q)]
    index = np.searchsorted(q, y, side='right')
    abs_sum = (2 * index - len(q)) * y + prefix[-1] - 2 * prefix[index]
    return abs_sum / len(q) - half_pair_distance(q)


def matching(q, y, labels):
    results = {}
    for label in np.unique(labels):
        keep = labels == label
        atoms = np.sort(q[keep].ravel())
        mu = float(score_at(atoms, y[keep]).mean())
        variation = float(half_pair_distance(atoms) - half_pair_distance(q[keep]).mean())
        target_var = float(half_pair_distance(np.sort(y[keep])))
        raw = float(losses(q[keep], y[keep]).mean())
        results[str(label)] = {'n': int(keep.sum()), 'raw': raw, 'mean_mismatch': mu - target_var,
                               'forecast_variation': variation, 'target_variation': target_var,
                               'reassigned': mu + variation, 'matching_gain': mu + variation - raw}
    return {key: sum(row['n'] * row[key] for row in results.values()) / len(y)
            for key in ('raw', 'mean_mismatch', 'forecast_variation', 'target_variation',
                        'reassigned', 'matching_gain')}


def shift_planning(o, g):
    shifted = np.clip(o + .04, 0, 1)
    inflation = 1 + .05 * (sum(n**2 for n in OWNER_192.values()) / 192 - 1)
    out = {}
    for name, law in [('raw_ordinary', o), ('shifted_ordinary', shifted), ('raw_gru', g)]:
        gain = np.array([score_at(a, t) - score_at(b, t) for a, b, t in zip(o, shifted, law)])
        mean = float(gain.mean())
        by_animal = gain.reshape(-1, 2, gain.shape[-1])
        variances = {'independent_signs': float(np.var(by_animal, axis=-1).sum(axis=1).mean() / 4),
                     'same_uniform_signs': float(np.var(by_animal.mean(axis=1), axis=-1).mean())}
        out[name] = {'expected_I': mean, 'variance_one_fixed_recipient': variances,
                     'SE_at_192': {key: float(np.sqrt(v / 192)) for key, v in variances.items()},
                     'SE_at_192_ICC05': {key: float(np.sqrt(v * inflation / 192))
                                          for key, v in variances.items()}}
    return out


def run():
    if time.time() >= DEADLINE:
        raise RuntimeError('Native first-turn deadline reached')
    save('CONTROLS.json', controls())
    print('Known-law and score controls passed', flush=True)
    counts, targets, _, labs, rosters = load_old64()
    owners = owner_names(labs)
    assert np.all(counts[..., 0] > 0) and np.all(targets >= 0)
    q_stream = ratios(counts).transpose(0, 1, 4, 2, 3).reshape(2, 128, 4, 256)
    q = np.sort(q_stream.reshape(2, 128, 1024), axis=-1)
    y = targets.ravel()
    risks = [float(losses(law, y).mean()) for law in q]
    assert np.max(np.abs(np.asarray(risks) - [.127641, .129108])) < 1e-6, risks
    print('Old-only selected risks', risks, flush=True)

    lo, hi = 0., .2
    for _ in range(48):
        mid = (lo + hi) / 2
        if np.clip(y + mid, 0, 1).mean() < .60251:
            lo = mid
        else:
            hi = mid
    shifted_y = np.clip(y + hi, 0, 1)
    assert abs(shifted_y.mean() - .60251) < 1e-9
    label_sets = groups(owners, rosters)
    results = {'native_observed_ratio_mean': float(y.mean()), 'stress_outcome_shift': hi,
               'stress_clipped_outcomes': int(np.count_nonzero(y + hi > 1)),
               'fixed_shift_planning': shift_planning(*q), 'actors': {}}
    for a, actor in enumerate(('recent100', 'GRU975')):
        print('Computing', actor, flush=True)
        law = q[a]
        original = {name: envelopes(law, y, labels) for name, labels in label_sets.items()}
        halves = [envelopes(np.sort(q_stream[a, :, k:k+2].reshape(128, 512), axis=1), y,
                            label_sets['pooled']) for k in (0, 2)]
        stress = {name: envelopes(law, shifted_y, label_sets[name])
                  for name in ('pooled', 'sign', 'roster_sign')}
        results['actors'][actor] = {
            'forecast_ratio_mean': float(law.mean()),
            'actual': original, 'pooled_stream_halves': halves, 'held_owner_translation':
            owner_translation(law, y, owners, rosters),
            'actual_matching': matching(law, y, label_sets['owner_roster_sign']),
            'stress': stress, 'stress_raw_risk': float(losses(law, shifted_y).mean()),
            'actual_fixed_plus04_gain': float(np.mean(losses(law, y) -
                                                     losses(np.clip(law + .04, 0, 1), y))),
            'stress_fixed_plus04_gain': float(np.mean(losses(law, shifted_y) -
                                                     losses(np.clip(law + .04, 0, 1), shifted_y))),
        }
        save('CALCULATIONS.json', results)
    assert time.time() < DEADLINE


if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_CPU, (105, 110))
    status = 'interrupted'
    try:
        run()
        status = 'complete'
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        body = sum(item['body_bytes'] for item in EXPOSURE.values())
        decoded = sum(member['booked_uncompressed_bytes'] for item in EXPOSURE.values()
                      for member in item['members'].values())
        save('EXECUTION.json', {'status': status, 'pid': os.getpid(),
                                'utc': datetime.now(timezone.utc).isoformat(),
                                'cpu_seconds_since_entry': time.process_time() - CPU,
                                'user_plus_system_cpu_seconds': usage.ru_utime + usage.ru_stime,
                                'wall_seconds_since_entry': time.monotonic() - WALL,
                                'peak_rss_bytes_mac': usage.ru_maxrss, 'platform': sys.platform,
                                'body_bytes': body, 'member_bytes': decoded,
                                'body_plus_member_bytes': body + decoded, 'inputs': EXPOSURE,
                                'http_ingress_bytes': 0})
