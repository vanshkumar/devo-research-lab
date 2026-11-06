"""Read-only original-XLSX/cache reconstruction and independent scalar scoring."""
import io
import json
import time
import zipfile
from itertools import islice
import xml.etree.ElementTree as ET

import numpy as np
import openpyxl
from scipy.stats import beta as beta_distribution
from independent import (ROOT, OLD, AUTHOR, OUT, READS, blob, obj, frame, save, utc,
                         usage, score_arrays, bootstrap_summary, no_omission_path)


def main():
    began = time.perf_counter()
    val = frame(OLD / 'inputs/validation_numeric.csv')
    dev = frame(OLD / 'inputs/development_numeric.csv')
    split = frame(OLD / 'protocol/split_manifest.csv').set_index('subject')
    inputs = obj(AUTHOR / 'FORECAST_INPUTS.json')
    fits = [obj(OLD / ('outputs/primary/' + x + '_fit.json')) for x in ['shared', 'no_history']]
    meta = obj(AUTHOR / 'FORECAST_META.json')
    lock = obj(AUTHOR / 'FREEZE.json')
    saved_scores = obj(AUTHOR / 'SCORES.json')
    saved_person = frame(AUTHOR / 'PERSON_SCORES.csv')
    manifest = obj(OLD / 'experiments/source_audit/sources/manifest.json')
    with np.load(io.BytesIO(blob(AUTHOR / 'FORECASTS.npz')), allow_pickle=False) as archive:
        arrays = {k: archive[k] for k in archive.files}
    expanded_allowance = sum(x.nbytes for x in arrays.values()) * 2
    sources = []
    source_records = []
    for k in range(10):
        path = OLD / f'experiments/source_audit/sources/pregen_sequence_{k}.xlsx'
        raw = blob(path)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            expanded_allowance += 2 * sum(x.file_size for x in z.infolist())
        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        it = wb.active.values
        headers = next(it)
        rows = [dict(zip(headers, x)) for x in islice(it, 600)]
        wb.close()
        side = -np.sign([r['eccentricity'] for r in rows])
        contrast = np.array([r['contrastDelta'] for r in rows]) / .2 * side
        bias = np.array([r['bias'] for r in rows])
        sources.append((contrast, side, bias))
        expected = next(x for x in manifest if x['file'] == path.name)
        source_records.append(dict(sequence=k, rows=len(rows),
                                   sha256=READS[-1]['sha256'], pin_match=READS[-1]['sha256'] == expected['sha256']))
    builder_path = ROOT / 'sources/human_learning_feasibility_2026-10-28/WIN_cursor_ibl.psyexp'
    builder = ET.fromstring(blob(builder_path))
    loops = []
    for node in builder.iter('LoopInitiator'):
        params = {p.attrib.get('name'): p.attrib.get('val') for p in node.iter('Param')}
        loops.append(dict(name=node.attrib.get('name'), params=params))
    checks = []
    people = meta['subjects']
    independently_exact = np.empty((39, 400, 2))
    paths = []
    for i, person in enumerate(inputs['people']):
        who = person['subject']
        assert who == people[i]
        rows = val.loc[val.subject == who].sort_values('trial').reset_index(drop=True)
        prefix = rows.iloc[:200]
        c = prefix.sideContrast.to_numpy(float)
        responded = prefix.choice.isin([-1, 1]).to_numpy()
        revealed = prefix.choice.to_numpy(float) * prefix.feedbackType.to_numpy(float)
        candidates = []
        for k, (cc, ss, bb) in enumerate(sources):
            if np.allclose(cc[:200], c, atol=1e-10, rtol=0) and np.array_equal(ss[:200][responded], revealed[responded]):
                candidates.append(k)
        assert len(candidates) == 1
        k = candidates[0]
        cc, ss, bb = sources[k]
        raw_fb = prefix.feedbackType.to_numpy(float)
        encoded_fb = np.where(responded & np.isin(raw_fb, [-1., 1.]), raw_fb, 0.)
        feedback_diffs = np.flatnonzero(~np.isclose(raw_fb, person['prefix_feedback'], equal_nan=True))
        feedback_coding = [dict(trial=int(j), choice=float(prefix.choice.iloc[j]),
                               raw_feedback=float(raw_fb[j]) if np.isfinite(raw_fb[j]) else None,
                               forecast_feedback=float(person['prefix_feedback'][j])) for j in feedback_diffs]
        input_checks = dict(prefix_choice=np.array_equal(prefix.choice, person['prefix_choice']),
                            prefix_feedback=np.array_equal(encoded_fb, person['prefix_feedback']),
                            prefix_behavior_only=len(person['prefix_choice']) == len(person['prefix_feedback']) == 200,
                            allowed_input_fields=set(person) == {'subject', 'condition', 'partition', 'source_sequence',
                                'prefix_choice', 'prefix_feedback', 'side_contrast', 'teacher_side', 'teacher_bias'},
                            visible_contrast=np.allclose(cc, person['side_contrast'], atol=1e-10, rtol=0),
                            teacher_side=np.array_equal(ss, person['teacher_side']),
                            teacher_bias=np.array_equal(bb, person['teacher_bias']),
                            source_identity=(k == person['source_sequence']),
                            cache_inputs=np.allclose(cc, rows.sideContrast, atol=1e-10, rtol=0),
                            cache_sides=np.array_equal(ss, rows.stimSide),
                            cache_bias=np.array_equal(bb, rows.probabilityLeft),
                            condition=int(rows.instructions.iloc[0]) == person['condition'],
                            partition=str(split.loc[who, 'partition']) == person['partition'])
        assert all(input_checks.values()), (who, input_checks)
        checks.append(dict(subject=who, prefix_candidates=candidates, checks=input_checks,
                           omitted_feedback_coding=feedback_coding))
        pair = []
        for m, fit in enumerate(fits):
            independently_exact[i, :, m], path = no_omission_path(rows, ss, fit)
            pair.append(path)
        paths.append(pair)
    omission = []
    for g in [0, 1]:
        d = dev.loc[(dev.instructions == g) & (dev.trial >= 200) & (dev.trial < 600)]
        n, omitted = len(d), int((~d.choice.isin([-1, 1])).sum())
        a, b = omitted + .5, n - omitted + .5
        actual = next(x for x in inputs['observation_calibration'] if x['condition'] == g)
        computed = dict(condition=g, source_people=int(d.subject.nunique()), n=n, omissions=omitted,
                        alpha=a, beta=b, mean=a/(a+b),
                        q025=float(beta_distribution.ppf(.025, a, b)), q975=float(beta_distribution.ppf(.975, a, b)))
        computed['max_difference'] = max(abs(computed[key] - actual[key]) for key in actual)
        omission.append(computed)
    summaries, comparisons, person_diffs = {}, {}, []
    mapping = {'primary': 'primary', 'all_later': 'all_later', 'zero': 'zero_primary', 'primary_brier': 'brier_gain'}
    for setting, arr in arrays.items():
        p = arr.mean(axis=0) if arr.ndim == 4 else arr
        per = score_arrays(p, people, val)
        summary = bootstrap_summary(per, split)
        if arr.ndim == 4:
            loo = np.array([[v['primary'] for v in score_arrays(np.delete(arr, r, axis=0).mean(axis=0), people, val)]
                            for r in range(len(arr))])
            per_se = np.sqrt((len(arr)-1)/len(arr) * ((loo-loo.mean(axis=0))**2).sum(axis=0))
            summary['score_mcse'] = float(np.sqrt((len(arr)-1)/len(arr) * ((loo.mean(axis=1)-loo.mean())**2).sum()))
        else:
            per_se = np.zeros(39)
            summary['score_mcse'] = 0.
        expected = saved_scores['settings'][setting]
        differences = {name: max(abs(summary[name][f] - expected[oldname][f]) for f in ['mean', 'low', 'high'])
                       for name, oldname in mapping.items()}
        differences['score_mcse'] = abs(summary['score_mcse'] - expected['score_mcse'])
        differences['schedule_person_interval'] = max(abs(summary['schedule_person_interval'][f] - expected['schedule_person_interval'][f]) for f in ['low', 'high'])
        differences['schedule_means'] = max(abs(summary['schedules'][s]['mean'] - expected['schedules'][s]['mean']) for s in summary['schedules'])
        differences['leave_one_schedule_out'] = max(abs(summary['leave_one_schedule_out'][s] - expected['leave_one_schedule_out'][s]) for s in summary['schedules'])
        differences['partition_means'] = max(abs(summary['partitions'][s]['mean'] - expected['partitions'][s]['mean']) for s in summary['partitions'])
        comparisons[setting] = differences
        summaries[setting] = summary
        for i, v in enumerate(per):
            saved = saved_person.loc[(saved_person.setting == setting) & (saved_person.subject == v['subject'])].iloc[0]
            person_diffs.extend([abs(v['primary']-saved.gain_nat), abs(per_se[i]-saved.mcse), abs(v['n']-saved.n_primary)])
    pins = []
    for name, expected in lock['sha256'].items():
        raw = blob(ROOT / name)
        pins.append(dict(path=name, match=READS[-1]['sha256'] == expected, actual=READS[-1]['sha256']))
    np.savez_compressed(OUT / 'INDEPENDENT_EXACT.npz', probabilities=independently_exact)
    details = dict(utc=utc(), source_pins=source_records, prefix_and_input_checks=checks,
                   builder_loops=loops, observation_calibration=omission,
                   forecast_array_sha_matches=next(x for x in READS if x['path'].endswith('/FORECASTS.npz'))['sha256'] == meta['forecasts_sha256'],
                   freeze_pin_checks=pins,
                   ordering=dict(freeze=lock['utc'], forecast=meta['utc'], score=saved_scores['utc'],
                                 ordered=lock['utc'] < meta['utc'] < saved_scores['utc'],
                                 limitation='Saved pins/times establish consistency, not independent proof of historical nonaccess'),
                   independently_reconstructed_exact_shape=list(independently_exact.shape),
                   exact_forecast_max_abs_difference=float(np.max(np.abs(independently_exact-arrays['no_omission']))),
                   all_saved_person_score_count_mcse_max_difference=float(max(person_diffs)),
                   summary_differences=comparisons, independent_summaries=summaries,
                   additional_expanded_member_array_allowance=expanded_allowance,
                   elapsed_seconds=time.perf_counter()-began, **usage())
    save('RECONSTRUCTION.json', details)
    print(json.dumps({k:v for k,v in details.items() if k not in ['reads', 'prefix_and_input_checks', 'independent_summaries', 'builder_loops']}, indent=2), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        save('RECONSTRUCTION_FAILURE_CURRENT.json', dict(utc=utc(), exception=repr(exc), **usage()))
        raise
