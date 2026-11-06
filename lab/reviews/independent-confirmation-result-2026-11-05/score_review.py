"""Independent mixed-state scores and exact blocked reassignment on saved counts."""
from collections import defaultdict
from itertools import permutations
import hashlib

from scipy.spatial.distance import cdist
from scipy.stats import t as student

from records import AUTHOR, HERE, arrays, check_budget, np, read_json, run, save

ACTORS = ['growth', 'recent100', 'recent250', 'gru']
ORIGINS = [200, 1000]
STREAMS = [0, 10000019]
DRAWS = [0, 14]


class Marginal:
    """Forecast law for one sign, with the zero-opportunity atom separate."""

    def __init__(self, counts):
        n, k = counts.T
        positive = n > 0
        self.particles = len(n)
        self.x = np.sort(k[positive] / n[positive])
        self.prefix = np.r_[0., np.cumsum(self.x)]
        self.missing = self.particles - len(self.x)
        self.to_missing = np.sqrt(1 - self.x * (1 - self.x)).sum()
        # Each gap between sorted ratios is crossed by rank*(m-rank) unordered pairs.
        ranks = np.arange(1, len(self.x))
        self.unordered = np.sum(np.diff(self.x) * ranks * (len(self.x) - ranks)) + self.missing * self.to_missing

    def score(self, observed, unbiased=False):
        """Return energy scores for ratio observations, NaN denoting a missing atom."""
        y = np.asarray(observed, dtype=np.float64)
        present = np.isfinite(y)
        distances = np.full(y.shape, self.to_missing)
        v = y[present]
        j = np.searchsorted(self.x, v, side='left')
        below = j * v - self.prefix[j]
        above = self.prefix[-1] - self.prefix[j] - (len(self.x) - j) * v
        distances[present] = below + above + self.missing * np.sqrt(1 - v * (1 - v))
        denom = self.particles * (self.particles - int(unbiased))
        return distances / self.particles - self.unordered / denom


def ratios(counts):
    n, k = counts[..., [0, 2]], counts[..., [1, 3]]
    return np.divide(k, n, out=np.full(n.shape, np.nan), where=n > 0)


def evaluate(sample, obs, other_targets=None):
    observed = ratios(obs)
    v, u, mae, cross = [], [], [], []
    for side, cols in enumerate(([0, 1], [2, 3])):
        law = Marginal(sample[:, cols])
        y = observed[side]
        v.append(law.score(y))
        u.append(law.score(y, unbiased=True))
        mae.append(abs(law.x.mean() - y) if len(law.x) else np.nan)
        if other_targets is not None:
            cross.append(law.score(other_targets[:, side]))
    cross_mean = np.mean(cross, axis=0) if other_targets is not None else None
    return np.array([np.mean(v), np.mean(u), np.mean(mae)]), cross_mean


def proper_u(sample, obs):
    y = ratios(obs)
    return (Marginal(sample[:, :2]).score(y[0], unbiased=True)
            + Marginal(sample[:, 2:4]).score(y[1], unbiased=True)) / 2


def known_answer():
    counts = np.array([[0, 0], [4, 0], [3, 1], [2, 1], [2, 1], [5, 5], [0, 0]])
    obs = np.array([0., .33, .5, 1., np.nan])

    def embed(y):
        return [1, 0, 0] if np.isnan(y) else [0, y, 1-y]

    x = np.asarray([embed(k/n if n else np.nan) for n, k in counts])
    y = np.asarray([embed(a) for a in obs])
    first = cdist(y, x).mean(axis=1) / np.sqrt(2)
    pair = cdist(x, x) / np.sqrt(2)
    v_error = np.max(np.abs(first - .5 * pair.mean() - Marginal(counts).score(obs)))
    u_error = np.max(np.abs(first - .5 * pair[~np.eye(len(x), dtype=bool)].mean()
                            - Marginal(counts).score(obs, unbiased=True)))
    assert max(v_error, u_error) < 2e-15
    assert np.array_equal(Marginal(np.zeros((4, 2), dtype=int)).score(obs),
                          np.r_[np.sqrt(1 - obs[:-1] * (1 - obs[:-1])), 0])
    return dict(direct_embedding_V_max_error=v_error, direct_embedding_U_max_error=u_error)


def interval(values, family):
    assert np.isfinite(values).all()
    n = len(values)
    point = np.mean(values)
    se = np.std(values, ddof=1) / np.sqrt(n)
    crit = student.ppf(1 - .025 / family, n - 1)
    half = crit * se
    return dict(point=point, se=se, lower=point-half, upper=point+half, half_width=half,
                critical=crit, df=n-1, n=n, family=family)


def integration(batches, band):
    means = batches.mean(axis=0)
    assert means.shape == (8,)
    se = means.std(ddof=1) / np.sqrt(8)
    half = student.ppf(.995, 7) * se
    bound = max(.001, .2 * band['half_width'])
    return dict(batch_means=means, mcse=se, mc99_half_width=half, criterion=bound,
                passes=half <= bound, expanded=[band['lower']-half, band['upper']+half])


def read_count_chunk(path, subject, draw=None):
    keys = ['subject', 'cutoffs', 'names', 'streams', 'samples']
    if draw is not None:
        keys.append('draw')
    chunk = arrays(path, *keys)
    assert chunk['subject'].item() == subject and chunk['streams'].tolist() == STREAMS
    assert chunk['cutoffs'].tolist() == ORIGINS
    actor_names, per_stream = ACTORS, 512
    if draw is not None:
        assert chunk['draw'].item() == draw
        actor_names, per_stream = ACTORS[:2], 256
    assert chunk['names'].tolist() == actor_names
    a = chunk['samples']
    assert a.shape == (2, len(actor_names), 2, per_stream, 2, 7) and a.dtype.kind in 'iu'
    assert np.all(a >= 0) and np.all(a <= np.array([500, 2000]).reshape(2, 1))
    assert np.all(a[..., 1] <= a[..., 0]) and np.all(a[..., 3] <= a[..., 2])
    assert np.all(a[..., 0] + a[..., 2] <= [500, 2000])
    assert np.all(a[..., 1, :] - a[..., 0, :] >= 0)
    return a[..., 1, :]


def check_seed_records(ids):
    receipt = read_json(AUTHOR / 'SEEDS.json')
    assert receipt['primary_particles_per_stream'] == 512 and receipt['source_particles_per_stream'] == 256
    records = receipt['per_animal']
    assert [r['subject'] for r in records] == ids
    shifts = dict(prefix_fisher=313, donor=211, recent_anchor=611, early_action=900101,
                  late_action=101, early_teacher=900419, late_teacher=419)
    seeds = []
    for subject, r in zip(ids, records):
        base = int(hashlib.sha256(subject.encode()).hexdigest()[:8], 16) % (2**31-1)
        assert r['base'] == base and r['stream_offsets'] == STREAMS
        for key, shift in shifts.items():
            expected = [base + shift + offset for offset in STREAMS]
            assert r[key] == expected
            seeds.extend(expected)
    return dict(verified_animals=len(ids), distinct_named_seed_integers=len(set(seeds)), entries=len(seeds))


def calibration(sample, obs):
    result = defaultdict(list)
    for side, col in enumerate((0, 2)):
        predicted = ratios(sample)[:, side]
        actual = ratios(obs)[side]
        present = np.isfinite(predicted)
        result['missing'].append([np.mean(~present), float(np.isnan(actual))])
        readouts = [('N', sample[:, col], obs[col]), ('K', sample[:, col+1], obs[col+1]),
                    ('omissions', sample[:, 4], obs[4]), ('literal_success', sample[:, 6], obs[6])]
        if np.isfinite(actual) and np.any(present):
            readouts.append(('ratio', predicted[present], actual))
        for key, values, y in readouts:
            lo95, lo80, hi80, hi95 = np.quantile(values, [.025, .1, .9, .975])
            pit = np.mean(values < y) + .5 * np.mean(values == y)
            result[key].append([values.mean(), y, lo80 <= y <= hi80, lo95 <= y <= hi95, pit])
    return result


def exact_assignment(matrix):
    """Mean and variance of a total when each column is used exactly once."""
    n = len(matrix)
    mean = matrix.sum() / n
    if n == 1:
        return mean, 0.
    centered = matrix - matrix.mean(axis=0) - matrix.mean(axis=1, keepdims=True) + matrix.mean()
    return mean, np.sum(centered**2) / (n - 1)


def reassignment(scores, cross, strata):
    control = np.array([[1., 2., 7.], [3., -2., 5.], [0., 5., 2.]])
    full = [control[np.arange(3), p].sum() for p in permutations(range(3))]
    np.testing.assert_allclose(exact_assignment(control), (np.mean(full), np.var(full)), atol=2e-14)
    n = len(cross)
    np.testing.assert_allclose(cross[np.arange(n), np.arange(n)], scores, atol=2e-14)
    matched = scores.mean(axis=0)
    shuffled = np.zeros(2)
    total_var = 0.
    rows = []
    for (lab, project), inds in sorted(strata.items()):
        block = cross[np.ix_(inds, inds)]
        assert np.isfinite(block).all()
        size = len(inds)
        common = block.mean(axis=(0, 1))
        _, variance = exact_assignment(block[:, :, 0] - block[:, :, 1])
        total_var += variance
        shuffled += size * common / n
        rows.append(dict(lab=lab, project=project, n=size, matched= scores[inds].mean(axis=0),
                         reassigned=common, matching_score_reduction=common-scores[inds].mean(axis=0)))
    matched_gap = matched[0] - matched[1]
    shuffled_gap = shuffled[0] - shuffled[1]
    matched_benefit = shuffled - matched
    assert np.isclose(matched_gap, shuffled_gap + matched_benefit[1] - matched_benefit[0])
    return dict(actors=['recent100', 'gru'], n=n, stratum_count=len(rows), singleton_count=sum(r['n'] == 1 for r in rows),
                uniform_expected_fixed_points=len(rows), matched_risk=matched, reassigned_risk=shuffled,
                matched_gap=matched_gap, common_stratum_gap=shuffled_gap,
                fraction_of_matched_gap_retained=shuffled_gap/matched_gap,
                matched_relative_reduction=matched_gap/matched[0],
                reassigned_relative_reduction=shuffled_gap/shuffled[0],
                matching_reduction_by_actor=matched_benefit,
                differential_added_by_observed_matching=matched_benefit[1]-matched_benefit[0],
                exact_paired_permutation_gap_sd=np.sqrt(total_var)/n, strata=rows,
                scope='One finite postvalidation comparison, with uniform within-block permutations including fixed points.')


def grouping_sensitivity(d, labels):
    groups = sorted(set(labels))
    group_d = [d[labels == lab] for lab in groups]
    G = len(group_d)
    eq = interval(np.array([part.mean() for part in group_d]), 3)
    sumsq = sum(np.sum(part - d.mean())**2 for part in group_d)
    cluster_se = np.sqrt(G/(G-1) * sumsq) / len(d)
    cluster_half = eq['critical'] * cluster_se
    return dict(groups=dict(zip(groups, map(len, group_d))), equal_label=eq,
                animal_weighted_cluster=[d.mean()-cluster_half, d.mean()+cluster_half],
                leave_one_out={lab: d[labels != lab].mean() for lab in groups})


def main():
    controls = known_answer()
    previous = [read_json(HERE / f'{tag}_RESOURCE.json') for tag in ('CHRONOLOGY', 'CHRONOLOGY_VERIFIED')]
    assert previous[-1]['status'] == 'complete'
    prior_read = sum(r['explicit_nominal_decoded_read_bytes'] for r in previous)
    observed = arrays(HERE / 'RECONSTRUCTED_TARGETS.npz', 'subjects', 'mapped', 'literal', 'labs', 'cohorts', 'windows')
    subjects = observed['subjects'].tolist()
    assert len(set(subjects)) == 192 and observed['windows'].tolist() == [500, 2000]
    seeds = check_seed_records(subjects)
    obs, lit = observed['mapped'][:, 1, :], observed['literal'][:, 1, :]
    labels, projects = observed['labs'], observed['cohorts']
    observed_ratios = ratios(obs)
    strata = defaultdict(list)
    for i, key in enumerate(zip(labels, projects)):
        strata[key].append(i)
    cross = np.full((192, 192, 2), np.nan)

    pooled = np.empty((192, 2, 4, 3))
    literal = np.empty_like(pooled)
    streams = np.empty((192, 2, 4, 2, 3))
    batch_U = np.empty((192, 2, 4, 8))
    literal_U = np.empty_like(batch_U)
    sources = np.empty((192, 2, 2, 2, 3))
    source_U = np.empty((192, 2, 2, 2, 8))
    cal = defaultdict(lambda: defaultdict(list))
    for i, subject in enumerate(subjects):
        a = read_count_chunk(AUTHOR / 'main_chunks' / f'{subject}.npz', subject)
        assert np.all(a[:, :, :, :, 4] == a[:, :1, :, :, 4])  # Same omission mechanism and draws by actor.
        group = strata[(labels[i], projects[i])]
        for ci, actor_samples in enumerate(a):
            for j, actor_sample in enumerate(actor_samples):
                sample = actor_sample.reshape(1024, 7)
                other_targets = observed_ratios[group] if ci == 0 and j in (1, 3) else None
                pooled[i, ci, j], block = evaluate(sample, obs[i], other_targets)
                if block is not None:
                    cross[i, group, int(j == 3)] = block
                changed = not np.array_equal(obs[i], lit[i])
                literal[i, ci, j] = evaluate(sample, lit[i])[0] if changed else pooled[i, ci, j]
                for si, stream in enumerate(actor_sample):
                    streams[i, ci, j, si] = evaluate(stream, obs[i])[0]
                for b, batch in enumerate(sample.reshape(8, 128, 7)):
                    batch_U[i, ci, j, b] = proper_u(batch, obs[i])
                    literal_U[i, ci, j, b] = proper_u(batch, lit[i]) if changed else batch_U[i, ci, j, b]
                for name, values in calibration(sample, obs[i]).items():
                    cal[(ci, j)][name].extend(values)
        for ji, draw in enumerate(DRAWS):
            s = read_count_chunk(AUTHOR / 'source_chunks' / f'{draw}_{subject}.npz', subject, draw=draw)
            for ci, actor_samples in enumerate(s):
                for j, actor_sample in enumerate(actor_samples):
                    sample = actor_sample.reshape(512, 7)
                    sources[i, ji, ci, j] = evaluate(sample, obs[i])[0]
                    for b, batch in enumerate(sample.reshape(8, 64, 7)):
                        source_U[i, ji, ci, j, b] = proper_u(batch, obs[i])
        if (i + 1) % 32 == 0:
            print(f'Reconstructed scores for {i+1}/192 animals', flush=True)
        check_budget(prior=prior_read)

    # Define the decision from the saved forecasts and our targets before loading reported numbers.
    D = .9 * pooled[:, 0, :3, 0] - pooled[:, 0, 3:4, 0]
    literal_D = .9 * literal[:, 0, :3, 0] - literal[:, 0, 3:4, 0]
    U = .9 * pooled[:, 0, :3, 1] - pooled[:, 0, 3:4, 1]
    primary, literal_rows, scope = [], [], []
    for j, actor in enumerate(ACTORS[:3]):
        band = interval(D[:, j], 3)
        mc = integration(.9 * batch_U[:, 0, j] - batch_U[:, 0, 3], band)
        recent, neural = pooled[:, 0, [j, 3], 0].mean(axis=0)
        primary.append(dict(reference=actor, D=band, integration=mc, reference_risk=recent, neural_risk=neural,
                            relative_gain=1-neural/recent, V_minus_U=(D[:, j] - U[:, j]).mean(),
                            stream_D=(.9 * streams[:, 0, j, :, 0] - streams[:, 0, 3, :, 0]).mean(axis=0)))
        lband = interval(literal_D[:, j], 3)
        literal_rows.append(dict(reference=actor, band=lband,
                                 MC=integration(.9 * literal_U[:, 0, j] - literal_U[:, 0, 3], lband),
                                 literal_minus_mapped={k: lband[k]-band[k] for k in ('point', 'lower', 'upper')}))
        merged = np.array(['churchlandlab' if lab == 'churchlandlab_ucla' else lab for lab in labels])
        scope.append(dict(reference=actor, by_registered_lab=grouping_sensitivity(D[:, j], labels),
                          merged_churchland=grouping_sensitivity(D[:, j], merged),
                          by_project={p: interval(D[projects == p, j], 3) for p in sorted(set(projects))}))
    positive = all(r['integration']['passes'] and r['integration']['expanded'][0] > 0 for r in primary)
    negative = primary[1]['integration']['passes'] and primary[1]['integration']['expanded'][1] < 0
    secondary = []
    for ci, origin in enumerate(ORIGINS):
        acc = pooled[:, ci, 1, 2] - pooled[:, ci, 3, 2]
        pscore = .9 * pooled[:, ci, 1, 0] - pooled[:, ci, 3, 0]
        secondary.extend([dict(origin=origin, metric='A', band=interval(acc, 4),
                               stream_bands=[interval(streams[:, ci, 1, s, 2] - streams[:, ci, 3, s, 2], 4)
                                             for s in (0, 1)]),
                          dict(origin=origin, metric='D', band=interval(pscore, 4))])
    source = []
    for ji, draw in enumerate(DRAWS):
        for ci, origin in enumerate(ORIGINS):
            for j, actor in enumerate(ACTORS[:2]):
                reference, neural = sources[:, ji, ci, j, 0], pooled[:, ci, 3, 0]
                band = interval(.9 * reference - neural, 8)
                source.append(dict(draw=draw, origin=origin, reference=actor, D=band,
                                   relative_gain=1-neural.mean()/reference.mean(),
                                   integration=integration(.9 * source_U[:, ji, ci, j] - batch_U[:, ci, 3], band)))

    changed = np.flatnonzero(np.any(obs != lit, axis=1))
    assert len(changed) == 1 and subjects[changed[0]] == 'CSHL_002'
    target_distance = np.abs(ratios(obs[changed]) - ratios(lit[changed])).mean()
    max_point = 1.9 * target_distance / len(subjects)
    max_endpoint = max_point * (1 + primary[0]['D']['critical'])
    assert not any(abs(r['literal_minus_mapped']['point']) > max_point for r in literal_rows)
    assert not any(abs(r['literal_minus_mapped'][k]) > max_endpoint for r in literal_rows for k in ('lower','upper'))
    shuffled = reassignment(pooled[:, 0, [1, 3], 0], cross, strata)
    cal_summary = []
    for (ci, j), row in sorted(cal.items()):
        missing_forecast, missing_observed = np.mean(row.pop('missing'), axis=0)
        readings = {name: dict(zip(['prediction', 'observed', 'coverage80', 'coverage95', 'mean_mid_PIT'],
                                   np.mean(values, axis=0))) for name, values in row.items()}
        cal_summary.append(dict(origin=ORIGINS[ci], actor=ACTORS[j], missing_forecast=missing_forecast,
                                missing_observed=missing_observed, readings=readings))

    # All author summaries are loaded as comparators only after calculations.
    comparator = read_json(AUTHOR / 'ANALYSIS.json')
    reported_D = arrays(AUTHOR / 'PRIMARY_CONTRIBUTIONS.npz', 'D', 'subjects')
    assert reported_D['subjects'].tolist() == subjects
    d_error = np.max(np.abs(D-reported_D['D']))
    assert d_error < 5e-14
    literal_saved = read_json(AUTHOR / 'LITERAL_SENSITIVITY.json')
    common_saved = read_json(AUTHOR / 'COMMON_OWNER_SENSITIVITY.json')
    for own, old in zip(primary, comparator['primary']):
        assert own['reference'] == old['reference']
        np.testing.assert_allclose([own['reference_risk'], own['neural_risk'], own['relative_gain'], own['V_minus_U']],
                                   [old['reference_risk'], old['neural_risk'], old['relative_gain_point'], old['V_minus_U_contrast_mean']], atol=5e-14)
        np.testing.assert_allclose(own['stream_D'], old['stream_D_means'], atol=5e-14)
    for families, reference_families, key, reference_key in (
        (primary, comparator['primary'], 'D', 'D'), (secondary, comparator['secondary_selected_four'], 'band', 'band'),
        (source, comparator['source_contraries'], 'D', 'D'), (literal_rows, literal_saved['primary'], 'band', 'literal_D'),
    ):
        assert len(families) == len(reference_families)
        for own, old in zip(families, reference_families):
            if 'integration' in own:
                np.testing.assert_allclose(own['integration']['batch_means'], old['mc']['batch_means'], atol=5e-14)
                np.testing.assert_allclose(own['integration']['mc99_half_width'], old['mc']['mc99_half_width'], atol=5e-14)
            np.testing.assert_allclose([own[key][k] for k in ('point','lower','upper')],
                                       [old[reference_key][k] for k in ('point','lower','upper')], atol=5e-14)
    for own, old, common in zip(scope, comparator['sensitivities'], common_saved['contrasts']):
        np.testing.assert_allclose(own['merged_churchland']['animal_weighted_cluster'],
                                   [common['animal_weighted_cluster_band'][k] for k in ('lower', 'upper')], atol=5e-14)
        np.testing.assert_allclose(list(own['by_registered_lab']['leave_one_out'].values()),
                                   [row['D'] for row in old['leave_one_label_out']], atol=5e-14)
    for own, old in zip(cal_summary, comparator['absolute_calibration']):
        assert (own['actor'], own['origin']) == (old['actor'], old['cutoff'])
        for label, detail in own['readings'].items():
            np.testing.assert_allclose([detail[k] for k in ('prediction', 'observed', 'coverage80', 'coverage95', 'mean_mid_PIT')],
                                       [old['readouts'][label][k] for k in ('mean_prediction', 'mean_observed', 'coverage80', 'coverage95', 'mean_mid_PIT')], atol=5e-14)
    assert positive == comparator['primary_positive'] and negative == comparator['primary_selected_negative']
    check_budget(prior=prior_read)

    np.savez_compressed(HERE / 'REVIEW_REDUCTIONS.npz', subjects=subjects, actors=ACTORS, origins=ORIGINS,
                        pooled=pooled, literal=literal, primary_D=D, stream_scores=streams,
                        main_batch_U=batch_U, source_scores=sources, source_batch_U=source_U,
                        reassignment_cross_V=cross, reassignment_actors=['recent100', 'gru'], labs=labels, cohorts=projects)
    save('REVIEW_CALCULATION.json', dict(
        controls=controls, verified_seeds=seeds, primary=primary, positive=positive, negative=negative,
        secondary=secondary, source=source, scope_sensitivities=scope, calibration=cal_summary,
        literal=dict(primary=literal_rows, ratio_target_distance=target_distance,
                     analytic_point_bound=max_point, analytic_endpoint_bound=max_endpoint),
        reassignment=shuffled, author_paired_D_max_absolute_difference=d_error,
        check_summary='Primary paired vectors, bands, stream/batch, source, project/site, calibration and literal checks from saved forecasts.'))
    print(f'Maximum paired D discrepancy {d_error:.3g}; primary gates {positive=}, {negative=}', flush=True)
    print(f'Observed gap {shuffled["matched_gap"]:.9f}; reassigned {shuffled["common_stratum_gap"]:.9f}; '
          f'added by matching {shuffled["differential_added_by_observed_matching"]:.9f}', flush=True)


if __name__ == '__main__':
    run('SCORES', main)
