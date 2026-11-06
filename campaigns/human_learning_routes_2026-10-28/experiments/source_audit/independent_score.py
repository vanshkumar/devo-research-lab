#!/usr/bin/env python3
"""Independent raw-byte extraction and scalar scoring audit after validation opens.

Uses only Python's standard library. It does not import campaign analysis/model
code, reconstruct latent models, refit, or select windows. Outputs one JSON file.
Guard checks occur before any raw data or prediction file is opened.
"""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import json
import math
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RAW = ROOT / 'inputs/processed_data_2026.csv'
PRED = ROOT / 'outputs/primary/trial_predictions.csv'
TOL = 2e-12


def read_csv(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle))


def finite(value):
    if value is None or value.strip() in ('', 'nan', 'NaN', 'NA'):
        return None
    result = float(value)
    assert math.isfinite(result), ('nonfinite', value)
    return result


def flag(value):
    assert value in ('True', 'False'), ('unexpected boolean', value)
    return value == 'True'


def average(values):
    values = list(values)
    assert values
    return math.fsum(values) / len(values)


def close(a, b, location, errors):
    if a is None or b is None:
        assert a is b, ('missingness mismatch', location, a, b)
        return
    error = abs(a - b)
    errors[location.split(':')[0]] = max(errors[location.split(':')[0]], error)
    assert error <= TOL, (location, a, b, error)


def summarize(subjects, records):
    return {metric: average(records[s][metric] for s in subjects)
            for metric in ('delta_log', 'delta_brier', 'history_gain')}


def main():
    # Never move these guards below a read of raw or saved behavioral values.
    assert (ROOT / 'protocol/VALIDATION_OPENED.json').exists(), 'Validation is still sealed'
    assert (ROOT / 'outputs/primary/summary.json').exists(), 'Primary evaluation is not complete'
    marker = json.loads((ROOT / 'protocol/VALIDATION_OPENED.json').read_text())
    parent_summary = json.loads((ROOT / 'outputs/primary/summary.json').read_text())
    lock = json.loads((ROOT / 'protocol/SPLIT_LOCK.json').read_text())
    split_path = ROOT / 'protocol/split_manifest.csv'
    assert hashlib.sha256(split_path.read_bytes()).hexdigest() == lock['split_sha256']
    split_rows = read_csv(split_path)
    split = {r['subject']: r for r in split_rows}
    assert len(split) == len(split_rows) == 80
    ids = {s for s, r in split.items() if r['partition'] != 'development'}
    assert len(ids) == 39 and '006' not in ids
    withheld_schedules = set(lock['unseen_schedules'])
    for subject, row in split.items():
        assert (row['schedule'] in withheld_schedules) == (row['partition'] == 'validation_unseen_schedule')
    hash_md5 = hashlib.md5()
    with RAW.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            hash_md5.update(chunk)
    assert hash_md5.hexdigest() == '5bc8ccf8bdca2e89fc21d20ffb7c1695'

    # Select subject before converting behavioral fields; no development outcomes
    # are needed. Cursor text is ignored and not parsed or emitted.
    raw = defaultdict(list)
    with RAW.open(newline='') as handle:
        for record in csv.DictReader(handle):
            if record['subject'] not in ids:
                continue
            row = {'subject': record['subject'], 'session': record['session']}
            for key in ('trial', 'instructions', 'stimSide', 'choice'):
                row[key] = int(float(record[key]))
            for key in ('probabilityLeft', 'contrastLeft', 'contrastRight', 'stimContrast',
                        'sideContrast', 'feedbackType', 'response_times_from_stim',
                        'firstMovement_times_from_stim', 'dot.started'):
                row[key] = finite(record[key])
            raw[row['subject']].append(row)
    assert set(raw) == ids
    errors = defaultdict(float)
    switches = {}
    for subject, rows in raw.items():
        rows.sort(key=lambda r: r['trial'])
        assert [r['trial'] for r in rows] == list(range(600))
        assert {r['session'] for r in rows} == {split[subject]['session']}
        assert {r['instructions'] for r in rows} == {int(split[subject]['condition'])}
        # Match the frozen complete input array via an independent struct encoder.
        encoded = b''.join(struct.pack('<dddd', r['probabilityLeft'], r['contrastLeft'],
                                       r['contrastRight'], r['stimSide']) for r in rows)
        assert hashlib.sha256(encoded).hexdigest() == split[subject]['schedule_sha256']
        previous_probability = None
        current_switch = None
        current_old_majority = 0
        switches[subject] = []
        for row in rows:
            t, probability = row['trial'], row['probabilityLeft']
            assert probability in (.2, .5, .8)
            assert row['stimContrast'] in (0., .1, .25, .5, 1.)
            assert row['choice'] in (-1, 0, 1)
            # A change resets the prior event; only later .2<->.8 events qualify.
            if previous_probability is not None and probability != previous_probability:
                current_switch = None
                current_old_majority = 0
                if t >= 200 and {probability, previous_probability} == {.2, .8}:
                    current_switch = t
                    current_old_majority = 1 if previous_probability == .8 else -1
                    switches[subject].append(t)
            row['switch_trial'] = -1 if current_switch is None else current_switch
            row['switch_offset'] = 999 if current_switch is None else t - current_switch
            row['old_majority'] = current_old_majority
            row['responded'] = row['choice'] != 0
            row['primary'] = (200 <= t < 600 and current_switch is not None
                              and 0 <= t-current_switch < 30 and row['stimContrast'] <= .1)
            row['primary_responded'] = row['primary'] and row['responded']
            row['schedule'] = split[subject]['schedule']
            row['partition'] = split[subject]['partition']
            if row['responded']:
                assert row['feedbackType'] in (-1, 1)
                assert row['choice'] * row['feedbackType'] == row['stimSide']
            else:
                assert row['feedbackType'] is None
            previous_probability = probability

    # Compare every reserved row, including all mask/offset values. Independently
    # score the supplied probabilities with scalar log/log1p and binary outcomes.
    predicted_rows = read_csv(PRED)
    predictions = {(r['subject'], int(r['trial'])): r for r in predicted_rows}
    assert len(predictions) == len(predicted_rows) == 39 * 600
    assert set(predictions) == {(s, t) for s in ids for t in range(600)}
    subject_scores = {}
    primary_count = omission_count = 0
    for subject, rows in sorted(raw.items()):
        included = []
        for row in rows:
            key = (subject, row['trial'])
            saved = predictions[key]
            for column in ('session', 'schedule', 'partition'):
                assert saved[column] == row[column], (key, column)
            for column in ('instructions', 'stimSide', 'choice', 'probabilityLeft', 'contrastLeft',
                           'contrastRight', 'stimContrast', 'sideContrast', 'feedbackType',
                           'response_times_from_stim', 'firstMovement_times_from_stim',
                           'dot.started', 'switch_trial', 'switch_offset', 'old_majority'):
                close(row[column], finite(saved[column]), 'row_'+column+':'+str(key), errors)
            for column in ('primary', 'responded', 'primary_responded'):
                assert flag(saved[column]) == row[column], (key, column)
            y = 1 if row['choice'] == 1 else 0
            scores = {}
            for model in ('shared', 'condition', 'no_history'):
                probability = float(saved['p_'+model])
                assert math.isfinite(probability) and 0 <= probability <= 1
                p_clipped = min(1-1e-12, max(1e-12, probability))
                logscore = math.log(p_clipped) if y else math.log1p(-p_clipped)
                brier = (probability-y)**2
                scores['log_'+model] = logscore
                scores['brier_'+model] = brier
                close(logscore, float(saved['log_'+model]), 'log_'+model+':'+str(key), errors)
                close(brier, float(saved['brier_'+model]), 'brier_'+model+':'+str(key), errors)
            row['delta_log'] = scores['log_condition'] - scores['log_shared']
            row['delta_brier'] = scores['brier_shared'] - scores['brier_condition']
            row['history_gain'] = scores['log_shared'] - scores['log_no_history']
            for metric in ('delta_log', 'delta_brier', 'history_gain'):
                close(row[metric], float(saved[metric]), metric+':'+str(key), errors)
            if row['primary_responded']:
                included.append(row)
                primary_count += 1
            if row['primary'] and not row['responded']:
                omission_count += 1
        assert included
        subject_scores[subject] = dict(subject=subject, condition=int(split[subject]['condition']),
                                       schedule=split[subject]['schedule'], partition=split[subject]['partition'],
                                       n=len(included), **{m: average(r[m] for r in included)
                                       for m in ('delta_log', 'delta_brier', 'history_gain')})
    parent_people = {r['subject']: r for r in read_csv(ROOT/'outputs/primary/participant_scores.csv')}
    assert set(parent_people) == ids
    for subject, row in subject_scores.items():
        saved = parent_people[subject]
        assert int(saved['n']) == row['n']
        for metric in ('delta_log', 'delta_brier', 'history_gain'):
            close(row[metric], float(saved[metric]), 'participant_'+metric+':'+subject, errors)
    aggregate = summarize(sorted(ids), subject_scores)
    for metric, value in aggregate.items():
        close(value, parent_summary[metric]['mean'], 'overall_'+metric, errors)
    partitions = {}
    for part in sorted({split[s]['partition'] for s in ids}):
        people = sorted(s for s in ids if split[s]['partition'] == part)
        partitions[part] = dict(n_people=len(people), **summarize(people, subject_scores))
        for metric, value in summarize(people, subject_scores).items():
            close(value, parent_summary[part][metric]['mean'], 'partition_'+metric+':'+part, errors)
    schedules = []
    parent_schedules = {r['schedule']:r for r in read_csv(ROOT/'outputs/primary/schedule_scores.csv')}
    for schedule in sorted({split[s]['schedule'] for s in ids}):
        people = sorted(s for s in ids if split[s]['schedule'] == schedule)
        result = dict(schedule=schedule, n_people=len(people), n_trials=sum(subject_scores[s]['n'] for s in people),
                      **summarize(people, subject_scores))
        saved = parent_schedules[schedule]
        assert int(saved['n_people']) == result['n_people'] and int(saved['n_trials']) == result['n_trials']
        for metric, value in summarize(people, subject_scores).items():
            close(value, float(saved[metric]), 'schedule_'+metric+':'+schedule, errors)
        schedules.append(result)

    # Direct observable curves at zero and low contrast. Within each bin, first
    # average each person's responses, then average eligible people equally.
    curve_results = []
    parent_curves = {(r['contrast'], int(r['start']), int(r['stop']), int(r['condition'])): r
                     for r in read_csv(ROOT/'outputs/primary/observable_curves.csv')}
    for contrast in ('zero', 'low'):
        for lo, hi in ((0,5), (5,10), (10,20), (20,30)):
            for condition in (0,1):
                person_values = []
                n_trials = 0
                for subject, rows in raw.items():
                    if int(split[subject]['condition']) != condition:
                        continue
                    choices = [int(r['choice'] == r['old_majority']) for r in rows
                               if lo <= r['switch_offset'] < hi and r['responded']
                               and (r['stimContrast'] == 0 if contrast == 'zero' else r['stimContrast'] <= .1)]
                    if choices:
                        person_values.append(average(choices))
                        n_trials += len(choices)
                key = (contrast, lo, hi, condition)
                result = dict(contrast=contrast, start=lo, stop=hi, condition=condition,
                              n_people=len(person_values), n_trials=n_trials, mean=average(person_values))
                saved = parent_curves[key]
                assert int(saved['n_people']) == result['n_people'] and int(saved['n_trials']) == n_trials
                close(result['mean'], float(saved['mean']), 'curve:'+str(key), errors)
                curve_results.append(result)
    result = dict(status='PASS', utc=datetime.now(timezone.utc).isoformat(),
                  validation_opened_utc=marker['utc'], raw_md5=hash_md5.hexdigest(),
                  split_sha256=lock['split_sha256'], prediction_sha256=hashlib.sha256(PRED.read_bytes()).hexdigest(),
                  implementation='Python stdlib csv.DictReader, struct schedule encoder, scalar math.log/log1p; no campaign imports',
                  scope='Independent extraction, masks, outcome coding, supplied-probability scores and observable curves; no independent model fitting or probability reconstruction',
                  rows=39*600, people=39, primary_responded_trials=primary_count, primary_omissions=omission_count,
                  overall=aggregate, partitions=partitions, participant_scores=list(subject_scores.values()),
                  schedule_scores=schedules, observable_curves=curve_results, switches_zero_based=switches,
                  max_absolute_errors=dict(errors), tolerance=TOL)
    destination = HERE/'independent_score_results.json'
    destination.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','rows','people','primary_responded_trials','primary_omissions','overall','partitions')}, indent=2))


if __name__ == '__main__':
    main()
