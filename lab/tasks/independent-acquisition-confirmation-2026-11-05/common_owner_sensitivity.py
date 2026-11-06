"""Prespecified common-owner grouping and inspection of saved contributions."""
from common import *
from analyze import band
from scipy.stats import t as student


def main():
    fit = get(HERE / 'ANALYSIS.json')
    vectors = arrays(HERE / 'PRIMARY_CONTRIBUTIONS.npz')
    units = get(HERE / 'ACCESS_FOOTPRINT.json')['primary_units']
    assert list(vectors['subjects']) == [u['subject'] for u in units]
    lab = np.array([u['lab'] for u in units])
    groups = np.where(np.isin(lab, ['churchlandlab', 'churchlandlab_ucla']), 'churchland_common_owner', lab)
    owners = sorted(set(groups))
    assert len(owners) == 10 and np.sum(groups == 'churchland_common_owner') == 31
    rows = []
    max_reduction_delta = 0.
    for reference, v, r in zip(vectors['references'], vectors['D'].T, fit['primary']):
        assert reference == r['reference']
        check = band(v, 3)
        delta = max(abs(check[k] - r['D'][k]) for k in ['point', 'se', 'lower', 'upper'])
        assert delta < 1e-14
        max_reduction_delta = max(delta, max_reduction_delta)
        group_means = [v[groups == g].mean() for g in owners]
        group_residual_sums = np.array([(v[groups == g] - v.mean()).sum() for g in owners])
        n = len(owners)
        se = np.sqrt(n/(n-1) * np.sum(group_residual_sums**2)) / len(v)
        critical = student.ppf(1-.05/(2*3), n-1)
        rows.append(dict(reference=reference, equal_group_band=band(group_means, 3),
            animal_weighted_cluster_band=dict(point=v.mean(), lower=v.mean()-critical*se,
                                              upper=v.mean()+critical*se, df=n-1)))
    score_data = arrays(HERE / 'SCORES.npz')
    stream = score_data['stream_scores']
    secondary_streams = []
    for ci, origin in enumerate([200, 1000]):
        for si in range(2):
            selected = stream[:, ci, 1, si, 1]
            neural = stream[:, ci, 3, si, 1]
            secondary_streams.append(dict(cutoff=origin, stream=si,
                accuracy=band(selected[:, 0]-neural[:, 0], 4), proper=band(.9*selected[:, 1]-neural[:, 1], 4)))
    literal = get(HERE / 'LITERAL_SENSITIVITY.json')
    assert literal['same_realized_forecasts'] and literal['same_pairing_weights_and_interval_method']
    # The frozen literal script writes and accounts for its numerical output before its log-only TypeError.
    assert get(HERE / 'LITERAL_SENSITIVITY_RESOURCES.json')['status'] == 'complete'
    save('COMMON_OWNER_SENSITIVITY.json', dict(utc=utc(), prespecified_owner_mapping=True,
        owner_groups={g: int(np.sum(groups == g)) for g in owners}, contrasts=rows,
        primary_contribution_reduction_max_delta=max_reduction_delta, secondary_independent_stream_diagnostics=secondary_streams,
        literal_diagnostic_outputs_inspected=True, literal_threshold_decision_matches=literal['scientific_threshold_decision_matches_mapped']))
    receipt('COMMON_OWNER_SENSITIVITY', all_jobs_terminal=True)
    print(json.dumps(dict(owner_sensitivity=rows, secondary_streams=secondary_streams), default=serial), flush=True)


if __name__ == '__main__':
    main()
