"""Independent projection, chronological joins, measurement and input-boundary checks."""
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
from itertools import accumulate
import json
import re
import struct
import sys

from records import (AUTHOR, CHARGES, HERE, PINS, ROOT, SOURCE, arrays, check_budget, np,
                     read, read_json, read_jsonl, run, save)

sys.path.insert(0, str(ROOT / 'sources/longitudinal_learning_feasibility_2026-10-28/tools'))
import duckdb

FIELDS = ['contrastLeft', 'contrastRight', 'choice', 'feedbackType',
          'rewardVolume', 'probabilityLeft', 'intervals_0', 'intervals_1']
AFFECTED = 'CSHL_002'
AFFECTED_EID = 'f8254e94-1f73-48b1-953e-50b52271f9d9'
COUNT_FIELDS = ['N_left', 'K_left', 'N_right', 'K_right', 'omissions',
                'choice_negative', 'literal_feedback_success']


def verify_seals(requests):
    original_path = AUTHOR / 'PRE_OUTCOME_SEAL.json'
    amended_path = AUTHOR / 'MEASUREMENT_PRE_FORECAST_SEAL.json'
    original = read_json(original_path)
    amendment = read_json(amended_path)
    launch = read_json(AUTHOR / 'MAIN_LAUNCH.json')
    completion = read_json(AUTHOR / 'FORECAST_COMPLETION.json')
    for seal in (original, amendment):
        assert seal['write_once']
        for relative, digest in seal['pins'].items():
            actual = PINS.get(relative)
            if actual is None:
                read(ROOT / relative, digest)
            else:
                assert actual == digest, relative
    controls = read_json(AUTHOR / 'PREFLIGHT_CONTROLS.json', original['actual_passed_control_sha256'])
    assert controls['all_passed'] and controls['naive_file_head_fails']
    assert controls['no_evaluation_payload_access'] and controls['checkpoint_epoch'] == 975
    assert len(controls['poison_controls']) == 8
    assert all(c['counts_identical'] and c['all_six_future_fields_poisoned'] for c in controls['poison_controls'])
    assert original['no_evaluation_response_bodies_acquired']
    assert amendment['first_main_forecast_pending'] and amendment['unchanged_actor_seeds_origins_weights_thresholds']
    assert launch['pre_forecast_seal'] == PINS[str(amended_path.relative_to(ROOT))]
    assert completion['all_forecast_jobs_terminal']
    assert (completion['main_animals'], completion['source_animal_draws']) == (192, 384)
    assert (original['primary_particles'], original['source_particles']) == (1024, 512)
    assert amendment['particle_counts'] == {'primary': 1024, 'source': 512}
    assert amendment['source_draws'] == [0, 14]
    first_attempt = min(req['utc'] for req in requests)
    first_body = min(req['utc'] for req in requests if req['success'])
    last_body = max(req['utc'] for req in requests if req['success'])
    assert original['utc'] < first_attempt <= first_body <= last_body < amendment['utc'] < launch['utc'] < completion['utc']

    official = read_json(AUTHOR / 'OFFICIAL_SOURCE_PINS.json')
    for req in official['all_requests']:
        assert req['success'] and req['public_anonymous']
        assert len(read(AUTHOR / req['local'], req['sha256'])) == req['received_bytes']
    assert sum(req['received_bytes'] for req in official['all_requests']) == 155262
    return dict(original=original['utc'], first_attempt=first_attempt, first_body=first_body, last_body=last_body,
                amended=amendment['utc'], launch=launch['utc'], completion=completion['utc'],
                original_pins=len(original['pins']), amended_pins=len(amendment['pins']),
                official_pinned_texts=len(official['all_requests']), preflight_full_simulator_poison_controls=8)


def qualified_sessions(footprint):
    def metadata(filename):
        path = SOURCE / filename
        return read_json(path, footprint['pins'][str(path.relative_to(ROOT))])

    eligible = metadata('QUALIFIED_COHORT.json')['subjects']
    listed = {u['subject']: u for u in eligible if u['role'] == 'candidate_primary_evaluation'}
    aggregate = {u['subject']: u for u in metadata('AGGREGATE_CHRONOLOGY.json')['subjects']
                 if u['subject'] in listed}
    individual = {u['subject']: u for u in metadata('FOOTER_QUALIFICATION.json')['subjects']
                  if u['subject'] in listed and u['status'] == 'footer_qualified_3000'}
    exclusions = metadata('ORIGINAL_EXCLUSIONS.json')
    old_names = {u['subject'] for u in exclusions['subjects']}
    def normalized(name):
        return re.sub(r'[^a-z0-9]', '', name.lower())

    excluded_keys = set(exclusions['exclusion_keys']) | {normalized(s) for s in ('NYU-28', 'NYU-42')}
    assert len(old_names) == 154 and not ({normalized(s) for s in listed} & excluded_keys)
    old_sessions = metadata('ORIGINAL_SESSION_IDS.json')['sessions']
    prohibited = {u['eid'] for u in old_sessions if u['subject'] in old_names}
    assert len(prohibited) == 6222
    units = footprint['primary_units']
    assert len(units) == len(listed) == 192 and {u['subject'] for u in units} == set(listed)

    sessions = {}
    for u in units:
        s = u['subject']
        assert u == listed[s]
        if u['cohort'] == 'public_subject_aggregate':
            info = aggregate[s]
            assert info['status'] == 'identity_qualified_3000' and info['lab'] == u['lab']
            native = info['used_sessions']
            earliest = info['first_indexed_training']['eid']
        else:
            info = individual[s]
            assert u['cohort'] == info['cohort'] == 'ASD_project' and info['lab'] == u['lab']
            native = info['probes']
            earliest = info['chronology']['stable_session_ids'][0]
        ordered = sorted(native, key=lambda z: (z['date'], int(z['number']), z['eid']))
        assert ordered[0]['eid'] == earliest and len({(z['date'], z['number']) for z in ordered}) == len(ordered)
        endpoints = list(accumulate(z['rows'] for z in ordered))
        assert endpoints[-1] >= 3000 > endpoints[-2]
        sessions[s] = []
        for z, start, stop in zip(ordered, [0] + endpoints, endpoints):
            sessions[s].append({**z, 'indexed_start': start, 'indexed_stop': stop})
        frozen = [(z['eid'], z['date'], z['number'], z['rows'], z['start'], z['stop']) for z in u['training_sessions']]
        reconstructed = [(z['eid'], z['date'], z['number'], z['rows'], z['indexed_start'], z['indexed_stop'])
                         for z in sessions[s]]
        assert reconstructed == frozen, s
    return units, sessions, aggregate, prohibited


def load_projection(con, obj, req):
    path = AUTHOR / 'bodies' / obj['local']
    assert req['local'] == 'bodies/' + obj['local'] and req['resolved_url'] == obj['url']
    assert req['success'] and req['http_status'] == 200 and req['anonymous']
    assert req['received_bytes'] == req['expected_bytes'] == obj['bytes']
    assert req['response_headers']['ETag'].strip('"') == obj['etag']
    assert req['all_acquired_fields'] == obj['all_physically_acquired_fields']
    payload = read(path, req['sha256'])
    size, magic = struct.unpack('<I4s', payload[-8:])
    assert len(payload) == obj['bytes'] and payload[:4] == magic == b'PAR1' and 0 < size < len(payload) - 12
    assert hashlib.sha256(payload[-size-8:-8]).hexdigest() == obj['footer_sha256']
    del payload
    is_aggregate = obj['kind'] == 'aggregate'
    assert obj['decode_fields'] == FIELDS + (['session'] if is_aggregate else [])
    expr = ', '.join(f'CAST("{field}" AS DOUBLE) AS "{field}"' for field in FIELDS)
    if is_aggregate:
        expr += ', session'
    CHARGES['projected_parquet_nominal_file_bytes'] += obj['bytes']
    data = con.execute(f'SELECT {expr} FROM read_parquet(?, file_row_number=true) ORDER BY file_row_number',
                       [str(path)]).fetchnumpy()
    assert all(len(col) == obj['rows'] for col in data.values())
    CHARGES['decoded_numeric_and_identity_slot_bytes'] += sum(col.nbytes for col in data.values())
    CHARGES['decoded_null_mask_bytes'] += sum(col.mask.nbytes for col in data.values() if np.ma.isMaskedArray(col))
    return data


def identity_runs(data, obj, source):
    identity = data['session']
    assert not np.ma.isMaskedArray(identity) and identity.ndim == 1
    assert all(isinstance(s, str) and len(s) == 36 for s in identity)
    CHARGES['decoded_session_UTF8_bytes'] += 36 * len(identity)
    changes = np.flatnonzero(identity[1:] != identity[:-1]) + 1
    runs = {identity[lo]: (int(lo), int(hi)) for lo, hi in zip(np.r_[0, changes], np.r_[changes, len(identity)])}
    assert len(runs) == len(changes) + 1
    pinned = {z['eid']: (z['row_start'], z['row_stop']) for z in obj['full_session_row_map']}
    source_map = {z['eid']: (z['row_start'], z['row_stop']) for z in source['all_trial_identity_counts']}
    assert runs == pinned == source_map and all(hi > lo for lo, hi in runs.values())
    return runs


def view_for_sessions(sessions, aggregates, by_eid):
    raw = np.empty((3000, 8))
    allocation = np.zeros(3000, dtype=np.float64)
    provenance = []
    for z in sessions:
        eid = z['eid']
        if aggregates is None:
            data, obj = by_eid[eid]
            assert obj['url'] == z['source_url'] and obj['footer_sha256'] == z['footer_sha256']
            assert obj['bytes'] == z['file_size'] and obj['rows'] == z['rows']
            lo, hi = 0, obj['rows']
        else:
            data, runs = aggregates
            lo, hi = runs[eid]
            assert (lo, hi) == (z['aggregate_row_start'], z['aggregate_row_stop']) and hi - lo == z['rows']
        t0, t1 = (np.ma.filled(data[k][lo:hi], np.nan) for k in FIELDS[-2:])
        assert np.isfinite(t0).all() and np.isfinite(t1).all()
        assert np.all(t1 >= t0) and np.all(t0[1:] >= t0[:-1]), eid
        start, stop = z['indexed_start'], min(z['indexed_stop'], 3000)
        physical_stop = lo + stop - start
        for i, field in enumerate(FIELDS):
            raw[start:stop, i] = np.ma.filled(data[field][lo:physical_stop], np.nan)
        allocation[start] = 1
        provenance.append(dict(eid=eid, date=z['date'], number=z['number'], protocol=z['protocol'],
                               indexed_start=start, indexed_stop=stop, full_session_rows=hi-lo,
                               physical_file_start=lo, physical_file_stop=physical_stop))
    CHARGES['assembled_main_numeric_and_flag_bytes'] += raw.nbytes + allocation.nbytes
    return raw, allocation, provenance


def stored_counts(raw, use_position):
    windows = []
    for stop in (1500, 3000):
        left, right, c, feedback = raw[1000:stop, :4].T
        if use_position:
            left_one = (np.abs(left) == 1) & (np.isnan(right) | (right == 0))
            right_one = (np.abs(right) == 1) & (np.isnan(left) | (left == 0))
        else:
            signed = np.where(np.isnan(right), 0, right) - np.where(np.isnan(left), 0, left)
            left_one, right_one = signed == -1, signed == 1
        windows.append([left_one.sum(), (left_one & (c == 1)).sum(),
                        right_one.sum(), (right_one & (c == -1)).sum(),
                        (c == 0).sum(), (c == -1).sum(), (feedback > 0).sum()])
    return np.asarray(windows, dtype=np.int64)


def inspect_measurement(raw, name, prov, saved_anomalies):
    left, right, choice, feedback, reward, probability = raw[:, :6].T
    assert np.isin(choice, [-1, 0, 1]).all() and np.isin(feedback, [-1, 0, 1]).all()
    assert np.all(np.isfinite(probability) & (probability >= 0) & (probability <= 1))
    assert np.isfinite(reward).all() and np.all(reward >= 0)
    assert np.all((reward > 0) == (feedback > 0)) and not np.any((choice == 0) & (feedback > 0))
    left0 = np.where(np.isnan(left), 0, left)
    right0 = np.where(np.isnan(right), 0, right)
    levels = [0, .0625, .125, .25, .5, 1]
    assert np.isin(np.abs(left0), levels).all() and np.isin(np.abs(right0), levels).all()
    assert not np.any((left0 != 0) & (right0 != 0)) and not np.any(np.isnan(left) & np.isnan(right))
    literal = right0 - left0
    nominal = np.abs(right0) - np.abs(left0)
    assert not np.any((choice != 0) & (nominal != 0) & ((choice == -np.sign(nominal)) != (feedback > 0)))
    mismatch = (choice != 0) & (literal != 0) & ((choice == -np.sign(literal)) != (feedback > 0))
    anomalies = np.flatnonzero((left0 < 0) | (right0 < 0))
    assert np.array_equal(anomalies, np.array(sorted(saved_anomalies), dtype=int)), name
    inventory = []
    for i in anomalies:
        z = next(p for p in prov if p['indexed_start'] <= i < p['indexed_stop'])
        j = i - z['indexed_start'] + z['physical_file_start']
        expected = saved_anomalies[i]
        assert name == AFFECTED and z['eid'] == expected['eid'] == AFFECTED_EID and i >= 1000
        assert j == expected['physical_file_row'] and np.isnan(left[i]) and right[i] < 0
        fields = {field: value if np.isfinite(value) else None for field, value in zip(FIELDS, raw[i])}
        assert fields == expected['values']
        inventory.append(dict(opportunity=i+1, eid=z['eid'], physical_file_row=j,
                              literal_feedback_mismatch=mismatch[i], values=fields))
    assert mismatch.sum() == (81 if name == AFFECTED else 0)
    changed_strength_one = np.sum((np.abs(literal) == 1) & (literal != nominal))
    assert changed_strength_one == (33 if name == AFFECTED else 0)
    return inventory


def pinned_input_projection():
    source = ROOT / 'lab/tasks/calibration-frontier-main-2026-11-05/main_simulator.py'
    tree = ast.parse(read(source, PINS[str(source.relative_to(ROOT))]))
    [boundary] = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'causal_view']
    # Execute just the sealed pure boundary; the driver and model are never imported.
    namespace = {'np': np}
    exec(compile(ast.Module(body=[boundary], type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['causal_view']


def check_inputs(raw, allocation, stored, causal_view):
    literal = np.column_stack((raw[:, :6], allocation))
    mapped = literal.copy()
    contrast = mapped[:, :2]
    contrast[contrast < 0] *= -1
    assert np.isnan(stored[1000:, :6]).all() and np.array_equal(stored[:, 6], allocation)
    assert np.array_equal(stored[:1000], literal[:1000], equal_nan=True)
    hashes = {}
    for origin in (200, 1000):
        # Construct the expected information set without using the pinned function.
        expected = np.full(stored.shape, np.nan)
        expected[:, 6] = allocation
        expected[:origin, :6] = raw[:origin, :6]
        poisoned = mapped.copy()
        poisoned[origin:, :6] = np.arange(origin, 3000)[:, None] * 10 + np.arange(6)[None, :] + 12345
        raw_view = causal_view(literal, origin)
        assert raw_view.tobytes() == causal_view(mapped, origin).tobytes() == causal_view(poisoned, origin).tobytes()
        assert np.array_equal(raw_view, causal_view(stored, origin), equal_nan=True)
        assert np.array_equal(raw_view, expected, equal_nan=True)
        hashes[str(origin)] = hashlib.sha256(raw_view.tobytes()).hexdigest()
    return hashes


def main():
    previous = HERE / 'CHRONOLOGY_RESOURCE.json'
    prior_reads = read_json(previous)['explicit_nominal_decoded_read_bytes'] if previous.exists() else 0
    requests = read_jsonl(AUTHOR / 'PUBLIC_REQUESTS.jsonl')
    receipts = {r['url']: r for r in requests if r['success']}
    diagnosis = read_jsonl(AUTHOR / 'DIAGNOSIS_EXPOSURE.jsonl')
    earlier_partial = read_jsonl(AUTHOR / 'EXPOSURE.jsonl')
    assert len(earlier_partial) == 11 and sum(r['decoded_rows'] for r in earlier_partial) == 435020
    timeline = verify_seals(requests)
    footprint = read_json(AUTHOR / 'ACCESS_FOOTPRINT.json')
    objects = footprint['objects']
    assert len(receipts) == len(objects) == sum(r['success'] for r in requests) == 802
    assert len({o['local'] for o in objects}) == 802
    assert sum(r['received_bytes'] for r in requests) == 458383178
    assert {r['url']: (r['rows'], r['decoded_fields']) for r in diagnosis} == {
        o['url']: (o['rows'], o['decode_fields']) for o in objects}
    units, sessions, source_agg, prohibited = qualified_sessions(footprint)
    objects_by_animal = defaultdict(list)
    for o in objects:
        objects_by_animal[o['subject']].append(o)
    ids = [u['subject'] for u in units]
    assert set(objects_by_animal) == set(ids)
    cache = arrays(AUTHOR / 'CHRONOLOGICAL_MAIN.npz', 'values', 'subjects', 'labs', 'cohorts')
    assert cache['values'].shape == (192, 3000, 7) and list(cache['subjects']) == ids
    assert list(cache['labs']) == [u['lab'] for u in units] and list(cache['cohorts']) == [u['cohort'] for u in units]
    causal_view = pinned_input_projection()
    anomaly_receipts = defaultdict(dict)
    for a in read_jsonl(AUTHOR / 'DIAGNOSTIC_ANOMALIES.jsonl'):
        anomaly_receipts[a['subject']][a['opportunity'] - 1] = a

    con = duckdb.connect(':memory:')
    con.execute('SET threads=1')
    all_sessions, primary_sessions = set(), set()
    exposure, provenance, inventory, mapped, literal = [], [], [], [], []
    # Stream per-object exposure so any partial reconstruction has its own record.
    with (HERE / 'REVIEW_DECODE.jsonl').open('x') as ledger:
        for i, unit in enumerate(units):
            s = unit['subject']
            agg, individual = None, {}
            for o in objects_by_animal[s]:
                data = load_projection(con, o, receipts[o['url']])
                if o['kind'] == 'aggregate':
                    assert len(objects_by_animal[s]) == 1
                    runs = identity_runs(data, o, source_agg[s])
                    agg = (data, runs)
                    eids = set(runs)
                else:
                    assert o['kind'] == 'session' and o['eid'] not in individual
                    individual[o['eid']] = (data, o)
                    eids = {o['eid']}
                assert not (eids & all_sessions or eids & prohibited)
                all_sessions.update(eids)
                entry = dict(subject=s, url=o['url'], kind=o['kind'], decoded_rows=o['rows'],
                             projected_fields=o['decode_fields'], physical_field_count=len(o['all_physically_acquired_fields']),
                             stable_session_count=len(eids), prior_body_SHA256_verified=True,
                             frozen_footer_SHA256_verified=True, review_ingress_bytes=0)
                exposure.append(entry)
                ledger.write(json.dumps(entry) + '\n')
            scheduled = {z['eid'] for z in sessions[s]}
            assert not scheduled & primary_sessions and scheduled <= all_sessions
            primary_sessions.update(scheduled)
            if agg is None:
                assert scheduled == set(individual)
            raw, flags, prov = view_for_sessions(sessions[s], agg, individual)
            physical = [z['physical_file_start'] for z in prov]
            out_of_order = physical != sorted(physical)
            if out_of_order:
                assert agg is not None
            inventory.extend(inspect_measurement(raw, s, prov, anomaly_receipts[s]))
            mapped.append(stored_counts(raw, True))
            literal.append(stored_counts(raw, False))
            provenance.append(dict(subject=s, lab=unit['lab'], cohort=unit['cohort'],
                                   physical_order_inversion=out_of_order, sessions=prov,
                                   masked_input_sha256=check_inputs(raw, flags, cache['values'][i], causal_view)))
            if (i + 1) % 32 == 0:
                print(f'Joined {i+1}/192 animals and {len(exposure)} objects', flush=True)
            check_budget(prior=prior_reads, limit=1_720_000_000)
    con.close()

    # Compare author counts only after the independent reconstruction.
    mapped, literal = np.stack(mapped), np.stack(literal)
    for filename, observed in [('OBSERVED_COUNTS.npz', mapped), ('OBSERVED_LITERAL_COUNTS.npz', literal)]:
        saved = arrays(AUTHOR / filename, 'observed', 'subjects', 'windows', 'columns')
        assert list(saved['subjects']) == ids and list(saved['windows']) == [500, 2000]
        assert list(saved['columns']) == COUNT_FIELDS and np.array_equal(observed, saved['observed'])
    i = ids.index(AFFECTED)
    delta = mapped - literal
    assert np.array_equal(np.flatnonzero(np.any(delta != 0, axis=(1, 2))), [i])
    assert np.array_equal(delta[i], [[-33, -7, 33, 25, 0, 0, 0]] * 2)
    assert len(primary_sessions) == 1537 and len(inventory) == 82
    assert sum(z['physical_order_inversion'] for z in provenance) == 101
    by_kind = Counter(z['kind'] for z in exposure)
    assert by_kind == {'aggregate': 116, 'session': 686}
    whole_rows = sum(z['decoded_rows'] for z in exposure)
    assert whole_rows == footprint['whole_decoded_rows'] == 4943360
    aggregate_sessions = sum(z['stable_session_count'] for z in exposure if z['kind'] == 'aggregate')
    assert aggregate_sessions == 6813 and len(all_sessions) == 6813 + 686
    np.savez_compressed(HERE / 'RECONSTRUCTED_TARGETS.npz', subjects=ids, mapped=mapped, literal=literal,
                        labs=cache['labs'], cohorts=cache['cohorts'], columns=COUNT_FIELDS, windows=[500, 2000])
    save('CHRONOLOGY_REVIEW.json', dict(
        utc=datetime.now(timezone.utc).isoformat(), timeline=timeline, units=provenance, animals=len(ids),
        footprint_objects=by_kind, whole_rows=whole_rows, main_rows=192*3000, auxiliary_rows=whole_rows-192*3000,
        aggregate_identity_rows=sum(z['decoded_rows'] for z in exposure if z['kind'] == 'aggregate'),
        distinct_full_session_ids=len(all_sessions), aggregate_session_ids=aggregate_sessions,
        distinct_main_session_ids=len(primary_sessions), original_protected_or_consumed_session_ids_checked=len(prohibited),
        object_hash_and_footer_matches=len(exposure), literal_compatibility_failure_retained=True,
        nonchronological_aggregates=101, exact_input_boundary_comparisons=384,
        targets_equal_to_author_after_independent_count=True, affected=mapped[i], affected_literal=literal[i],
        negative_inventory=inventory, new_public_ingress_bytes=0))
    print(f'Confirmed {whole_rows:,} whole projected rows, 1,537 main sessions and 384 input comparisons.', flush=True)


if __name__ == '__main__':
    run('CHRONOLOGY', main)
