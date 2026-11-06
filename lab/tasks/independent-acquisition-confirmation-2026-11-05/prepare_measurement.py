"""Released target representation adapter and actual pre-forecast controls."""
from common import *
from diagnose_compatibility import diagnostics
from main_simulator import causal_view
from source_models import inherited as early

PI_AMENDMENT = ROOT / 'lab/tasks/research-run-2026-11-05/MEASUREMENT_AMENDMENT.md'
COUNT_COLUMNS = ['N_left', 'K_left', 'N_right', 'K_right', 'omissions', 'choice_negative', 'literal_feedback_success']


def nominal_magnitude(values):
    """Keep position columns and missing fields, interpreting finite negatives as magnitudes."""
    mapped = values.copy()
    contrasts = mapped[..., :2]
    negative = np.isfinite(contrasts) & (contrasts < 0)
    np.negative(contrasts, out=contrasts, where=negative)
    return mapped


def main():
    assert not (HERE / 'MEASUREMENT_PRE_FORECAST_SEAL.json').exists()
    assert not (HERE / 'main_chunks').exists()
    read(PI_AMENDMENT)
    frozen = get(HERE / 'PRE_OUTCOME_SEAL.json')
    for path, pin in frozen['pins'].items():
        read(ROOT / path, pin)
    read(HERE / 'MEASUREMENT_CONTINUATION_NATIVE.json')

    cache_path = HERE / 'DIAGNOSTIC_LITERAL_CHRONOLOGY.npz'
    cache_receipt = get(HERE / 'MAPPING_CONSEQUENCE_RESOURCES.json')
    cache = arrays(cache_path, cache_receipt['pins'][str(cache_path.relative_to(ROOT))])
    values = cache['values']
    subjects = list(cache['subjects'])
    footprint = get(HERE / 'ACCESS_FOOTPRINT.json')
    units = footprint['primary_units']
    assert values.shape == (192, 3000, 9)
    assert subjects == [u['subject'] for u in units]
    assert list(cache['fields']) == ['contrastLeft', 'contrastRight', 'choice', 'feedbackType',
                                     'rewardVolume', 'probabilityLeft', 'intervals_0', 'intervals_1', 'session_start']

    # Compare the stored first3000 provenance against the exact pinned plan.
    session_count = 0
    for i, unit in enumerate(units):
        assert unit['training_sessions'][0]['start'] == 0
        end = 0
        starts = np.zeros(3000, dtype=bool)
        for session in unit['training_sessions']:
            start, end = session['start'], min(session['stop'], 3000)
            starts[start] = True
            assert np.all(cache['session_ids'][i, start:end] == session['eid'])
            physical_start = session.get('aggregate_row_start', 0)
            assert np.array_equal(cache['physical_file_rows'][i, start:end],
                                  np.arange(physical_start, physical_start + end - start))
            intervals = values[i, start:end, 6:8]
            assert np.isfinite(intervals).all() and np.all(intervals[:, 1] >= intervals[:, 0])
            assert np.all(np.diff(intervals[:, 0]) >= 0)
            session_count += 1
        assert end == 3000 and np.array_equal(values[i, :, 8], starts)
    assert session_count == 1537

    # Known answer for two positions and a full-contrast omission.
    synthetic = np.array([[-1., np.nan, 1.], [np.nan, -1., -1.], [np.nan, -1., 0.]])
    toy = np.zeros((3000, 7)); toy[1000:1003, :3] = nominal_magnitude(synthetic)
    assert np.array_equal(early.observed(toy)[1, :4], [1, 1, 2, 1])

    rows = [json.loads(line) for line in read(HERE / 'DIAGNOSTIC_ANOMALIES.jsonl').splitlines()]
    mapped = nominal_magnitude(values)
    changed = np.argwhere(np.isfinite(values[:, :, :2]) & (mapped[:, :, :2] != values[:, :, :2]))
    affected_i = subjects.index('CSHL_002')
    expected_eid = 'f8254e94-1f73-48b1-953e-50b52271f9d9'
    assert len(rows) == 82
    assert all(r['subject'] == 'CSHL_002' and r['eid'] == expected_eid for r in rows)
    expected = np.array([[affected_i, r['opportunity'] - 1, 1] for r in rows])
    assert np.array_equal(changed, expected)
    assert np.array_equal(mapped[:, :, 2:], values[:, :, 2:], equal_nan=True)
    assert np.array_equal(np.isnan(mapped), np.isnan(values))
    assert all(cache['session_ids'][i, j] == expected_eid for i, j, _ in changed)
    assert sum(abs(values[i, j, field]) == 1 for i, j, field in changed) == 33
    assert all(j >= 1000 for _, j, _ in changed)
    for i, animal in enumerate(mapped):
        failures = [key for key, flags in diagnostics(animal[:, :8]).items() if flags.any()]
        assert not failures, (subjects[i], failures)

    legal_cols = [0, 1, 2, 3, 4, 5, 8]
    forecast = np.full((192, 3000, 7), np.nan)
    observed = np.empty((192, 2, 7), dtype=np.int64)
    literal = np.empty_like(observed)
    checked = 0
    for i, (a, b) in enumerate(zip(values, mapped)):
        raw = a[:, legal_cols]
        amended = b[:, legal_cols]
        forecast[i] = causal_view(raw, 1000)
        for origin in (200, 1000):
            before = causal_view(raw, origin)
            poison = amended.copy()
            poison[origin:, :6] = np.arange(6) + 11
            assert before.tobytes() == causal_view(amended, origin).tobytes()
            assert before.tobytes() == causal_view(poison, origin).tobytes()
            assert before.tobytes() == causal_view(forecast[i], origin).tobytes()
            checked += 1
        observed[i] = early.observed(amended)
        literal[i] = early.observed(raw)
    assert np.array_equal(np.flatnonzero(np.any(observed != literal, axis=(1, 2))), [affected_i])
    assert np.array_equal(observed[affected_i] - literal[affected_i], [[-33,-7,33,25,0,0,0]] * 2)
    assert np.array_equal(literal[affected_i, 1, :4], [480, 296, 478, 199])
    assert np.array_equal(observed[affected_i, 1, :4], [447, 289, 511, 224])
    assert np.isnan(forecast[:, 1000:, :6]).all()

    npz('CHRONOLOGICAL_MAIN.npz', values=forecast, subjects=subjects,
        labs=[u['lab'] for u in units], cohorts=[u['cohort'] for u in units],
        purpose='Fixed factual prefixes and opportunity boundaries. No target fields.')
    for name, counts in [('OBSERVED_COUNTS.npz', observed), ('OBSERVED_LITERAL_COUNTS.npz', literal)]:
        npz(name, observed=counts, subjects=subjects, windows=[500, 2000], columns=COUNT_COLUMNS)
    report = dict(utc=utc(), all_passed=True, pre_forecast=True, cohort_size=192,
        verified_complete_session_maps=session_count, input_and_future_poison_exact_checks=checked,
        all_six_unavailable_fields_poisoned=True, both_origin_prefixes_and_allocations_exact=True,
        original_full_simulator_poison_checks_pinned=True, corrected_negative_fields=len(changed),
        affected_subject='CSHL_002', affected_session=expected_eid, changed_full_strength_side_rows=33,
        corrected_controls_no_residual_compatibility_failures=True, synthetic_negative_omission_test_passed=True,
        old_literal_target_counts=literal[affected_i], mapped_target_counts=observed[affected_i],
        observed_zero_count_signs=np.sum(observed[:, 1, [0, 2]] == 0), no_forecasts_started=True,
        observed_response_fields_separate_from_forecast_cache=True, whole_body_redownload_or_redecode=False)
    save('CHRONOLOGY_CHECKS.json', report)
    print(json.dumps(report, default=serial), flush=True)
    receipt('MEASUREMENT_PREPARATION', all_jobs_terminal=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        receipt('MEASUREMENT_PREPARATION_FAILURE', 'failed', error=repr(exc))
        raise
