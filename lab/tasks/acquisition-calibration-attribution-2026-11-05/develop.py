"""Old-64 calibration development. There is deliberately no 192 input path."""

import hashlib
import io
import json
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import scipy

from assess import (PairedEvaluation, family_critical, feature_bank, fit_source,
                    fixed_profiles, plan, summarize, training_terms)
from calibrate import EndpointFeatures, IDENTITY, MISSING, RankLaw, missing_distance


HERE = Path(__file__).resolve().parent
BANK = HERE.parent / 'calibration-frontier-main-2026-11-05'
INPUTS = {
    'MAIN_COUNTS.npz': (21056169, '72817c074f99ac41de4c84856798983c50d308e25550934d4c4e4e7f3061723d'),
    'REFINED_ADDITIONAL_COUNTS.npz': (6200905, 'c4c7ef8ef21d03e7107fb1b3031a624f5fa0af79d120b2ba58f01c5ecb942c1a'),
    'MAIN_OBSERVED.npz': (3677, '5096297f60968bd6ac7cdaf6760aab2f43705f42024f986e38d0b86db9580d16'),
}
CPU = time.process_time()
WALL = time.monotonic()
EXPOSURE = {}


def utc():
    return datetime.now(timezone.utc).isoformat()


def json_default(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    raise TypeError(type(x).__name__)


def save(name, value):
    destination = HERE / name
    temporary = destination.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False, default=json_default) + '\n')
    temporary.replace(destination)


def load_members(name, keys):
    size, pin = INPUTS[name]
    path = BANK / name
    if path.stat().st_size != size:
        raise ValueError(f'{name}: unexpected size')
    body = path.read_bytes()
    actual = hashlib.sha256(body).hexdigest()
    record = {'body_bytes': len(body), 'sha256': actual, 'members': {}}
    EXPOSURE[name] = record
    if actual != pin:
        raise ValueError(f'{name}: body pin mismatch')
    result = {}
    with ZipFile(io.BytesIO(body)) as archive:
        for key in keys:
            member = archive.getinfo(key + '.npy')
            record['members'][key] = {'booked_uncompressed_bytes': member.file_size}
            with archive.open(member) as stream:
                result[key] = np.lib.format.read_array(stream, allow_pickle=False)
            record['members'][key]['decoded_array_bytes'] = result[key].nbytes
    return result


def load_old64():
    axes = ('subjects', 'names', 'cutoffs', 'windows', 'stream_offsets')
    base = load_members('MAIN_COUNTS.npz', ('samples', 'conditions', *axes))
    extra = load_members('REFINED_ADDITIONAL_COUNTS.npz', ('samples', *axes))
    obs = load_members('MAIN_OBSERVED.npz', ('subjects', 'labs', 'cohort', 'observed', 'windows', 'columns'))
    assert base['samples'].shape == (64, 3, 2, 4, 2, 256, 2, 7)
    assert extra['samples'].shape == (64, 2, 4, 2, 256, 2, 7)
    assert obs['observed'].shape == (64, 2, 7)
    assert base['conditions'].tolist() == ['primary', 'source_context_input', 'source_calibrated_engagement']
    for obj in (base, extra):
        assert obj['samples'].dtype == np.dtype('int32')
        assert obj['names'].tolist() == ['growth', 'recent100', 'recent250', 'gru']
        assert obj['cutoffs'].tolist() == [200, 1000]
        assert obj['windows'].tolist() == [500, 2000]
        assert np.array_equal(obj['subjects'], obs['subjects'])
    assert base['stream_offsets'].tolist() == [0, 10000019]
    assert extra['stream_offsets'].tolist() == [20000038, 30000057]
    assert obs['windows'].tolist() == [500, 2000]
    assert obs['columns'][:4].tolist() == ['N_left', 'K_left', 'N_right', 'K_right']
    assert len(np.unique(obs['subjects'])) == 64
    assert obs['cohort'].tolist() == ['old40'] * 40 + ['later24'] * 24

    first = base['samples'][:, 0, 0, :, :, :, 1, :4]
    later = extra['samples'][:, 0, :, :, :, 1, :4]
    counts = np.concatenate((first[:, [1, 3]], later[:, [1, 3]]), axis=2)
    counts = counts.transpose(1, 0, 2, 3, 4).reshape(2, 64, 4, 256, 2, 2)
    outcome = ratios(obs['observed'][:, 1, :4].reshape(64, 2, 2))
    return counts, outcome, obs['subjects'], obs['labs'], obs['cohort']


def ratios(counts):
    n, k = counts[..., 0], counts[..., 1]
    if np.any((n < 0) | (n > 2000) | (k < 0) | (k > n)) or np.any(n.sum(axis=-1) > 2000):
        raise ValueError('Count endpoints violate the signed 2,000-opportunity support')
    return np.divide(k, n, out=np.full(n.shape, MISSING), where=n > 0)


def laws_from_counts(counts):
    values = ratios(counts.reshape(2, 64, -1, 2, 2)).transpose(0, 1, 3, 2)
    laws = np.empty(values.shape[:3], dtype=object)
    masses = np.full(values.shape[-1], 1 / values.shape[-1])
    for index in np.ndindex(laws.shape):
        laws[index] = RankLaw(values[index], masses)
    return laws


def owner_names(labs):
    return np.array(['churchland_common_owner' if lab in ('churchlandlab', 'churchlandlab_ucla') else lab
                     for lab in labs])


def source_and_held(laws, feature, outcomes, owners, blocks):
    terms = training_terms(laws, outcomes)
    full_weights = fit_source(terms, np.arange(len(outcomes)))
    held = np.empty((2, len(outcomes), 3))
    deleted = {}
    for owner in np.unique(owners):
        held_here = owners == owner
        weights = fit_source(terms, np.flatnonzero(~held_here))
        deleted[str(owner)] = weights
        held[:, held_here] = weights[:, None, :]
    tiers = feature_bank(laws, feature)
    return full_weights, held, deleted, tiers, PairedEvaluation(laws, feature, tiers, held, blocks)


def alignment_summary(laws, profiles, outcomes):
    diagnostics = []
    for actor in range(2):
        means = np.full((2, laws.shape[1], 2), np.nan)
        rows = []
        for i, sign in np.ndindex(laws.shape[1:]):
            law = laws[actor, i, sign]
            y = outcomes[i, sign]
            for calibrated, w in enumerate((IDENTITY, profiles[actor, i])):
                positive = w @ law.tiers
                if law.positive:
                    p = positive / law.positive
                    means[calibrated, i, sign] = p @ law.ratios
                if y == MISSING or not law.positive:
                    continue
                cdf = np.cumsum(p)
                lo, hi = law.ratios[np.searchsorted(cdf, [.1, .9])]
                rows.append([calibrated, sign, means[calibrated, i, sign] - y,
                             float(lo <= y <= hi), p[law.ratios < y].sum() + .5 * p[law.ratios == y].sum()])
        rows = np.asarray(rows)
        summary = {}
        for j, label in enumerate(('raw', 'calibrated')):
            selected = rows[rows[:, 0] == j, 2:]
            summary[label] = {'positive_pairs': len(selected), 'bias': selected[:, 0].mean(),
                              'coverage80': selected[:, 1].mean(), 'mid_PIT': selected[:, 2].mean()}
        flips = []
        for sign in range(2):
            raw, calibrated = means[:, :, sign]
            flip = ((raw[:, None] - raw) * (calibrated[:, None] - calibrated)) < 0
            flips.append(int(np.triu(flip, 1).sum()))
        summary['strict_mean_rank_reversals_left_right'] = flips
        summary['mean_missing_mass'] = float(np.mean([law.missing for law in laws[actor].flat]))
        summary['number_laws_with_missing_mass'] = sum(law.missing > 0 for law in laws[actor].flat)
        diagnostics.append(summary)
    return diagnostics


def direct_loss(values, masses, target):
    def distance(x, y):
        both_missing = (x == MISSING) & (y == MISSING)
        either = (x == MISSING) | (y == MISSING)
        return np.where(both_missing, 0, np.where(either, missing_distance(np.maximum(x, y)), np.abs(x - y)))

    return masses @ distance(values, target) - .5 * masses @ distance(values[:, None], values) @ masses


def synthetic_controls(feature):
    outcomes = np.array([MISSING, 0, .19, .25, .55, 1])
    maximum_error = 0.0
    for values, masses in [([MISSING, 0, .25, .25, 1], [.2, .1, .3, .25, .15]),
                           ([MISSING], [1.]), ([0, 1], [.8, .2])]:
        law = RankLaw(values, masses)
        for weights in (IDENTITY, np.array([.16, .64, .20])):
            atoms, p = law.outcome_law(weights)
            direct = np.array([direct_loss(atoms, p, y) for y in outcomes])
            maximum_error = max(maximum_error, float(np.max(np.abs(direct - law.scores(weights, outcomes)))))
            formula = weights @ law.linear_term(outcomes) + weights @ law.gram @ weights
            maximum_error = max(maximum_error, float(np.max(np.abs(direct - formula))))
            projected = weights @ feature.tier_means(law)
            expected = p @ feature.dot_outcomes(atoms, projected)
            maximum_error = max(maximum_error, float(abs(expected - projected @ projected)))
    assert maximum_error < 1e-12

    truth = np.array([.09, .11, .80])
    ordinary_mass = np.r_[.08, .92 * IDENTITY]
    gru_mass = np.r_[.08, .92 * truth]
    n = 64
    groups = np.repeat(np.array(['a', 'b', 'c', 'd']), 16)
    laws = np.empty((2, n, 2), dtype=object)
    for i, sign in np.ndindex((n, 2)):
        shift = (i // 16 - 1.5) * .014 + ((i % 16) // 2 - 3.5) * .008 + (sign - .5) * .03
        recipient = .055 if i % 2 else -.055
        x = np.array([.23, .40, .61]) + shift
        laws[0, i, sign] = RankLaw(np.r_[MISSING, x], ordinary_mass)
        laws[1, i, sign] = RankLaw(np.r_[MISSING, x + recipient], gru_mass)

    tiers = feature_bank(laws, feature)
    results = {'direct_distance_and_projection_max_abs_error': maximum_error}
    for name, actor, true_weights in [('calibratable_null', 0, truth), ('individual', 1, IDENTITY)]:
        fit = fit_source(training_terms(laws, truth_actor=actor, truth_weights=true_weights), np.arange(n))
        evaluated = PairedEvaluation(laws, feature, tiers, fixed_profiles(fit, n), groups)
        correct = fixed_profiles(np.stack([true_weights, true_weights]), n)
        result = plan(evaluated.opposed_moments(correct, actor))
        result['fitted_O_G_weights'] = fit
        result['witness_size'] = evaluated.size.mean()
        result['orthogonality'] = evaluated.orthogonality
        sign = -1 if actor == 0 else 1
        result['witness_expectation_error'] = abs(result['D_W_C_I'][1] - sign * evaluated.size.mean())
        if actor == 0:
            different = fixed_profiles(np.tile([.2, .3, .5], (2, 1)), n)
            alternative = evaluated.opposed_moments(different, actor)[0][:, 1].mean()
            result['different_shared_calibration_W'] = alternative
            result['passed'] = bool(result['raw_relative_GRU_gain'] > 0
                                    and np.max(np.abs(fit[0] - truth)) < .03
                                    and result['D_W_C_I'][2] > 0 and result['D_W_C_I'][3] > 0
                                    and result['D_W_C_I'][1] < 0
                                    and abs(alternative + evaluated.size.mean()) < 1e-11)
        else:
            result['passed'] = bool(result['D_W_C_I'][0] > 0 and result['D_W_C_I'][1] > 0)
        result['passed'] = result['passed'] and result['witness_expectation_error'] < 1e-11
        results[name] = result
    return results


def shared_calibration_sensitivity(laws, feature, tiers, blocks, source_full, deleted, held, main_plan):
    result = {}
    n = laws.shape[1]
    fits = [('full', source_full), *deleted.items()]
    for actor, label in enumerate(('ordinary_truth', 'gru_truth')):
        points = []
        for name, weights in fits:
            estimator = PairedEvaluation(laws, feature, tiers, fixed_profiles(weights, n), blocks)
            means = estimator.opposed_moments(held, actor)[0].mean(axis=0)
            points.append(means[:4])
        values = np.stack(points)
        leave = values[1:]
        jackknife = np.sqrt((len(leave) - 1) / len(leave) * ((leave - leave.mean(axis=0)) ** 2).sum(axis=0))
        halfwidth = family_critical(len(leave) - 1) * jackknife
        result[label] = {'source_fit_D_W_C_I': dict(zip((name for name, _ in fits), values)),
                         'max_abs_movement': np.max(np.abs(leave - values[0]), axis=0),
                         'delete_owner_jackknife_scale': jackknife,
                         'nominal_additive_shared_halfwidth': halfwidth,
                         'planning_with_extra_shared_margin': plan(main_plan[label], halfwidth)}
    return result


def main():
    started = json.loads((HERE / 'START_RECEIPT.json').read_text())
    if time.time() >= started['deadline']['unix']:
        raise RuntimeError('Original deadline reached before launch')
    resource.setrlimit(resource.RLIMIT_CPU, (85, 90))
    feature = EndpointFeatures()
    controls = synthetic_controls(feature)
    save('CONTROLS.json', controls)
    if not all(controls[key]['passed'] for key in ('calibratable_null', 'individual')):
        raise ArithmeticError('Known-law control failed before any archived endpoint decode')
    print('SYNTHETIC CONTROLS PASSED', flush=True)

    counts, outcomes, subjects, labs, roster = load_old64()
    owners = owner_names(labs)
    blocks = np.array([f'{owner}/{cohort}' for owner, cohort in zip(owners, roster)])
    laws = laws_from_counts(counts)
    full_weights, held, deleted, tiers, held_eval = source_and_held(laws, feature, outcomes, owners, blocks)
    scores = held_eval.observed(outcomes)
    archive_error = np.max(np.abs(scores[:, 4:6].mean(axis=0) - [.127641, .129108]))
    if archive_error > 1e-6:
        raise ArithmeticError(f'Inherited raw score replay failed: {archive_error}')
    fixed_eval = PairedEvaluation(laws, feature, tiers, fixed_profiles(full_weights, 64), blocks)
    result = {
        'archived_rounded_raw_reference_max_abs_difference': archive_error,
        'full_O_G_weights': full_weights,
        'delete_owner_O_G_weights': deleted,
        'source_roster_size': len(subjects),
        'witness_blocks': {str(b): int(np.sum(blocks == b)) for b in np.unique(blocks)},
        'observed_missing': int(np.sum(outcomes == MISSING)),
        'held_owner': summarize(scores, owners, roster, held_eval.size),
        'in_sample': summarize(fixed_eval.observed(outcomes), owners, roster, fixed_eval.size),
        'held_owner_orthogonality': held_eval.orthogonality,
        'calibration_diagnostics_O_G': alignment_summary(laws, held, outcomes),
        'observed_mean_positive_ratio': float(outcomes[outcomes != MISSING].mean()),
        'contribution_columns': ['D', 'W', 'C', 'I', 'raw_O', 'raw_G', 'cal_O', 'cal_G'],
        'old64_animal_contributions': [dict(subject=s, registered_lab=l, owner=o, roster=r, values=v,
                                           witness_size=w) for s, l, o, r, v, w in
                                       zip(subjects, labs, owners, roster, scores, held_eval.size.mean(axis=1))],
    }
    save('DEVELOPMENT.json', result)
    print('OLD64 OBSERVED', json.dumps(result['held_owner']['D_W_C_I'], default=json_default), flush=True)

    split = {}
    for label, stream_subset in [('initial512', slice(0, 2)), ('additional512', slice(2, 4))]:
        small = laws_from_counts(counts[:, :, stream_subset])
        weights, _, _, _, evaluation = source_and_held(small, feature, outcomes, owners, blocks)
        split[label] = {'full_O_G_weights': weights, 'held_owner_D_W_C_I': evaluation.observed(outcomes).mean(axis=0)[:4],
                        'witness_size': evaluation.size.mean()}

    main_moments, planning = {}, {}
    for actor, label in enumerate(('ordinary_truth', 'gru_truth')):
        moments = held_eval.opposed_moments(held, actor)
        main_moments[label] = moments
        planning[label] = plan(moments)
        planning[label]['common_ratio_shift_sensitivities'] = {
            str(shift): plan(held_eval.opposed_moments(held, actor, shift)) for shift in (-.04, .04)}
    shared = shared_calibration_sensitivity(laws, feature, tiers, blocks, full_weights, deleted, held, main_moments)
    save('TRANSPORT_PLANNING.json', {'scenarios': planning, 'source_owner_delete_stress': shared,
                                    'disjoint_stream_refits': split,
                                    'projected_witness_size': held_eval.size.mean()})
    print('PAIRED OPPOSITE-LAW PLANNING COMPLETE', flush=True)


if __name__ == '__main__':
    status = 'failed'
    try:
        main()
        status = 'complete'
    finally:
        body = sum(rec['body_bytes'] for rec in EXPOSURE.values())
        member = sum(row['booked_uncompressed_bytes'] for rec in EXPOSURE.values()
                     for row in rec['members'].values())
        save('RUN_ACCOUNTING.json', dict(status=status, utc=utc(), cpu_seconds_after_import=time.process_time() - CPU,
                                        process_wall_seconds_after_import=time.monotonic() - WALL,
                                        self_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                        python=sys.version, numpy=np.__version__, scipy=scipy.__version__,
                                        hashed_input_body_bytes=body, selected_member_decode_bytes_booked=member,
                                        input_body_plus_decode_bytes=body + member, inputs=EXPOSURE,
                                        http_ingress_bytes=0))
