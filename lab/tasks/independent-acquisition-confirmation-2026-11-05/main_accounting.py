"""Reconcile completed stages against the initial author allocation."""
from common import *


def main():
    earlier = get(HERE / 'DIAGNOSIS_RESOURCE_CHECKPOINT.json')
    phases = ['MEASUREMENT_PREPARATION', 'MEASUREMENT_SEAL', 'CONFIRMATION',
              'ANALYSIS', 'LITERAL_SENSITIVITY', 'COMMON_OWNER_SENSITIVITY', 'FIGURE_FIRST_RENDER', 'FIGURE']
    resources = [get(HERE / f'{phase}_RESOURCES.json') for phase in phases]
    assert all(r['status'] == 'complete' for r in resources)
    completion = get(HERE / 'FORECAST_COMPLETION.json')
    assert completion['main_animals'] == 192 and completion['source_animal_draws'] == 384
    assert completion['main_particles'] == 1024 and completion['source_particles'] == 512
    assert len(list((HERE / 'main_chunks').glob('*.npz'))) == 192
    assert len(list((HERE / 'source_chunks').glob('*.npz'))) == 384
    assert (HERE / 'CONFIRMATION_SUMMARY.png').stat().st_size > 0
    # Account for any stopped or failed phase before certifying booked headroom.
    failures = []
    for pattern in ['MEASUREMENT_PREPARATION_FAILURE*_RESOURCES.json',
                    'MEASURED_MAIN_FAILURE_*_RESOURCES.json', 'ANALYSIS_FAILURE*_RESOURCES.json']:
        failures.extend(get(p) for p in HERE.glob(pattern))
    storage = sum(p.stat().st_size for p in HERE.rglob('*') if p.is_file())
    this_stage = receipt('MAIN_ACCOUNTING')
    receipts = resources + failures + [this_stage]
    science_cpu = sum(r['cpu_seconds'] for r in receipts)
    scientific_reads = sum(r['read_decode_bytes'] for r in receipts)
    context_cpu = 2
    context_read = 20_000_000
    cpu = earlier['cumulative_booked_initial_science_cpu_seconds'] + science_cpu + context_cpu
    read_decode = earlier['cumulative_booked_initial_read_decode_bytes'] + scientific_reads + context_read
    peak = max([earlier['measured_peak_RSS_bytes']] + [r['peak_rss_bytes'] for r in receipts])
    body = earlier['cumulative_http_body_bytes']
    deadline = datetime.fromisoformat('2026-11-06T00:27:22+00:00')
    result = dict(utc=utc(), all_author_jobs_terminal=True, phases=phases,
        preserved_post_diagnosis_failures=[r['stage'] for r in failures], main_forecasts=completion,
        preserved_terminal_log_error='Literal reduction exited1 after saving numerical output and resource receipt. Only final json.dumps log formatting failed; no numerical rerun.',
        incremental_scientific_cpu_seconds=science_cpu, incremental_explicit_nominal_decoded_bytes=scientific_reads,
        incremental_context_bookings=dict(cpu_seconds=context_cpu, read_decode_bytes=context_read),
        cumulative_initial_booked_CPU_seconds=cpu, cumulative_initial_booked_read_decode_bytes=read_decode,
        cumulative_HTTP_body_bytes=body, incremental_HTTP_body_bytes=0,
        actual_max_measured_RSS_bytes=peak, owned_storage_bytes=storage,
        earliest_dispatch_deadline_UTC=deadline.isoformat(),
        before_dispatch_deadline_at_accounting=datetime.now(timezone.utc) < deadline,
        booked_remaining_initial_CPU_seconds=11100 - cpu,
        booked_remaining_initial_read_decode_bytes=3_000_000_000 - read_decode,
        physical_provider_import_io='unknown',
        experimental_exposure='All802 whole public objects acquired, 4,943,360 unique rows decoded in eight declared numeric fields plus permitted identities/order. See original receipts and diagnostic ledger for repeats and all physically acquired fields.',
        former_stages_retained='Diagnosis and source qualification/funding review plus all prior program costs preserved. Reserved review/revision/closeout charges are separate.',
        any_known_booked_ceiling_exceeded=cpu > 11100 or read_decode > 3_000_000_000 or body > 500_000_000 or peak > 3_000_000_000 or storage > 4_000_000_000)
    save('MAIN_RESOURCE_CHECKPOINT.json', result)
    print(json.dumps(result, default=serial, indent=2), flush=True)


if __name__ == '__main__':
    main()
