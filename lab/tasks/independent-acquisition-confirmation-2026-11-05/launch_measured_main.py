"""Pin the measurement amendment and invoke the original frozen simulator."""
from common import *

AMENDMENT = ROOT / 'lab/tasks/research-run-2026-11-05/MEASUREMENT_AMENDMENT.md'
DEADLINE = datetime.fromisoformat('2026-11-06T00:27:22+00:00').timestamp()
SEAL = HERE / 'MEASUREMENT_PRE_FORECAST_SEAL.json'


def seal():
    assert not (HERE / 'main_chunks').exists()
    assert not (HERE / 'ANALYSIS.json').exists()
    checks = get(HERE / 'CHRONOLOGY_CHECKS.json')
    assert checks['all_passed'] and checks['no_forecasts_started']
    assert checks['corrected_negative_fields'] == 82 and checks['changed_full_strength_side_rows'] == 33
    files = ['PRE_OUTCOME_SEAL.json', 'PREFLIGHT_CONTROLS.json', 'MEASUREMENT_CONTINUATION_NATIVE.json',
             'prepare_measurement.py', 'MEASUREMENT_PREPARATION_RESOURCES.json', 'CHRONOLOGY_CHECKS.json',
             'CHRONOLOGICAL_MAIN.npz', 'OBSERVED_COUNTS.npz', 'OBSERVED_LITERAL_COUNTS.npz',
             'DIAGNOSTIC_ANOMALIES.jsonl', 'run_confirmation.py', 'analyze.py', 'literal_sensitivity.py',
             'launch_measured_main.py']
    for p in [HERE / f for f in files] + [AMENDMENT, PREV / 'main_scores.py']:
        read(p)
    proof = dict(utc=utc(), write_once=True, actual_controls_passed=True, first_main_forecast_pending=True,
        original_seal_preserved=True, prepared_forecast_cache_contains_only_prefixes_and_allocations=True,
        factual_targets_in_separate_file=True, adopted_measurement='absolute finite magnitude within stored side column',
        unchanged_actor_seeds_origins_weights_thresholds=True, particle_counts=dict(primary=1024, source=512),
        source_draws=[0, 14], literal_sensitivity_uses_same_counts=True, pins=PINS.copy())
    with SEAL.open('x') as f:
        json.dump(proof, f, indent=2)
        f.write('\n')
    receipt('MEASUREMENT_SEAL')
    print(proof['utc'], 'measurement pre-forecast seal written', flush=True)


def launch():
    record = get(SEAL)
    assert record['actual_controls_passed'] and record['first_main_forecast_pending']
    for path, pin in record['pins'].items():
        read(ROOT / path, pin)
    assert time.time() < DEADLINE
    save('MAIN_LAUNCH.json', dict(utc=utc(), pid=os.getpid(), pre_forecast_seal=PINS[str(SEAL.relative_to(ROOT))],
        native_goal_created_at=1793903267, deadline_UTC='2026-11-06T00:27:22Z'))
    import run_confirmation
    run_confirmation.main()


if __name__ == '__main__':
    assert sys.argv[1:] in [['--seal'], ['--run']]
    try:
        seal() if sys.argv[1] == '--seal' else launch()
    except BaseException as exc:
        n = len(list(HERE.glob('MEASURED_MAIN_FAILURE_*.json')))
        receipt('MEASURED_MAIN_FAILURE_' + str(n), 'failed', error=repr(exc))
        raise
