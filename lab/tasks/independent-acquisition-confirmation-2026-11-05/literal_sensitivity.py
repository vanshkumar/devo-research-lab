"""Substitute the original observed count once, using the same saved forecasts."""
from common import *
from analyze import band, mc_record, metric


def main():
    mapped = arrays(HERE / 'OBSERVED_COUNTS.npz')
    literal = arrays(HERE / 'OBSERVED_LITERAL_COUNTS.npz')
    saved = arrays(HERE / 'SCORES.npz')
    primary = get(HERE / 'ANALYSIS.json')
    ids = list(saved['subjects'])
    assert ids == list(mapped['subjects']) == list(literal['subjects'])
    affected = np.flatnonzero(np.any(mapped['observed'] != literal['observed'], axis=(1, 2)))
    assert [ids[i] for i in affected] == ['CSHL_002']
    i = int(affected[0])
    z = arrays(HERE / 'main_chunks/CSHL_002.npz')['samples']
    # Preserve every forecast and every other animal contribution.
    scores = saved['scores'][:, :, :, 1].copy()
    batch_u = saved['batch_U'].copy()
    target = literal['observed'][i, 1]
    for origin in range(2):
        for actor in range(4):
            samples = z[origin, actor, :, :, 1].reshape(1024, 7)
            scores[i, origin, actor] = metric(samples, target, 2000)
            for stream in range(2):
                for block in range(4):
                    batch = z[origin, actor, stream, block*128:(block+1)*128, 1]
                    batch_u[i, origin, actor, stream*4 + block] = metric(batch, target, 2000)[2]

    rows = []
    max_change = get(HERE / 'MAPPING_CONSEQUENCE.json')['windows']['primary1001_3000']
    for reference, saved_band in enumerate(primary['primary']):
        v = .9 * scores[:, 0, reference, 1] - scores[:, 0, 3, 1]
        b = band(v, 3)
        mc = mc_record((.9 * batch_u[:, 0, reference] - batch_u[:, 0, 3]).T, b)
        diff = {k: b[k] - saved_band['D'][k] for k in ['point', 'lower', 'upper']}
        assert abs(diff['point']) <= max_change['maximum_absolute_paired_D_mean_change'] + 1e-12
        assert max(abs(diff[k]) for k in ('lower', 'upper')) <= max_change['maximum_absolute_primary_Bonferroni_endpoint_change'] + 1e-12
        rows.append(dict(reference=saved_band['reference'], literal_D=b, mapped_D=saved_band['D'],
                         literal_minus_mapped=diff, mc=mc))

    secondary = []
    for ci, cutoff in enumerate((200, 1000)):
        for k in ('A', 'D'):
            v = (scores[:, ci, 1, 0] - scores[:, ci, 3, 0] if k == 'A' else
                 .9 * scores[:, ci, 1, 1] - scores[:, ci, 3, 1])
            secondary.append(dict(cutoff=cutoff, metric=k, literal_band=band(v, 4)))
    positive = all(row['D']['lower'] > 0 and row['mc']['lower_after_mc'] > 0
                   and row['mc']['small_against_animal_precision']
                   for row in (dict(D=r['literal_D'], mc=r['mc']) for r in rows))
    selected = rows[1]
    negative = (selected['literal_D']['upper'] < 0 and selected['mc']['upper_after_mc'] < 0
                and selected['mc']['small_against_animal_precision'])
    unchanged = (positive == primary['primary_positive'] and negative == primary['primary_selected_negative'])
    result = dict(utc=utc(), diagnostic_only=True, affected_subject='CSHL_002',
        same_realized_forecasts=True, same_pairing_weights_and_interval_method=True,
        primary=rows, secondary_selected_four=secondary,
        literal_primary_positive=positive, literal_primary_selected_negative=negative,
        scientific_threshold_decision_matches_mapped=unchanged)
    save('LITERAL_SENSITIVITY.json', result)
    receipt('LITERAL_SENSITIVITY', all_jobs_terminal=True)
    print(json.dumps(dict(decision_matches=unchanged, differences=[r['literal_minus_mapped'] for r in rows]), flush=True))


if __name__ == '__main__':
    main()
