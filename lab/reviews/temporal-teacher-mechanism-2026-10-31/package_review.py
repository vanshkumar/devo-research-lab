"""Package and validate saved review evidence; no source payload or new responses."""
from pathlib import Path
import datetime, hashlib, json, platform, sys
from importlib.metadata import version

P = Path(__file__).resolve().parent

def read(name):
    return json.loads((P / name).read_text())

def write(name, value):
    (P / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def main():
    logs = read('LOG_AUDIT.json')
    crossed = read('CROSSED_DIAGNOSTIC.json')
    ledger = read('READS.json')
    freeze = read('DIAGNOSTIC_FREEZE.json')
    geometry = read('DERIVED_SUMMARY.json')
    pair = read('PAIR_CHECK.json')
    precision = read('PRECISION_CHECK.json')
    report_words = len((P / 'PI_REPORT.txt').read_text().split())
    result_words = len((P / 'RESULT.md').read_text().split())
    assert report_words <= 400 and result_words <= 400
    assert logs['all_pass'] and len(logs['checks']) == 260
    assert logs['total_queries'] == 238208 and len(logs['rows']) == 64
    assert len(crossed['rows']) == 189 and len(crossed['source_checks']) == 6
    assert ledger['additional_charged_bytes'] <= 180000000
    assert ledger['inherited_actual_bytes'] + ledger['additional_charged_bytes'] < 1000000000
    for name, digest in freeze['sha256'].items():
        assert hashlib.sha256((P / name).read_bytes()).hexdigest() == digest
    assert geometry['all_wrong_pairs_have_distinct_noncollinear_content_timing_contrasts']
    source_hashes = {}
    for entry in ledger['reads']:
        if 'sha256' in entry:
            old = source_hashes.setdefault(entry['path'], entry['sha256'])
            assert old == entry['sha256'], ('input changed across reads', entry['path'])
    write('INPUT_HASHES.json', source_hashes)
    population = [x for x in logs['rows'] if x['mode'] == 'population']
    summary = {
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'checks_passed': len(logs['checks']),
        'logged_scalar_queries_replayed': logs['total_queries'],
        'neural_feedback_recomputed_for_all_logs': False,
        'independent_gold_max_error': logs['independent_gold_max_error'],
        'samplewise_gold_max_error': logs['samplewise_gold_max_error'],
        'crossed_response_count': len(crossed['rows']),
        'source_crossed_checks': len(crossed['source_checks']),
        'population_cases': [{k: x[k] for k in ('case', 'final_gold', 'success', 'correct_observable_order', 'stretch_error', 'best_gold', 'best_gold_query_index', 'regret', 'best_gold_feedback_minus_selected')} for x in population],
        'runtime_seconds': {name: doc.get('runtime_seconds') for name, doc in [('pair', pair), ('crossed', crossed), ('log_audit', logs), ('precision', precision)]},
        'peak_rss_bytes_macos': {name: doc.get('peak_rss_bytes_macos') for name, doc in [('pair', pair), ('crossed', crossed), ('log_audit', logs), ('precision', precision)]},
        'inherited_actual_bytes': ledger['inherited_actual_bytes'],
        'review_additional_charged_upper_bytes': ledger['additional_charged_bytes'],
        'lineage_charged_upper_bytes': ledger['inherited_actual_bytes'] + ledger['additional_charged_bytes'],
        'remaining_review_cap_bytes': 180000000 - ledger['additional_charged_bytes'],
        'primary_requests': ledger['primary_requests'],
        'network_bytes': ledger['network_bytes'],
        'input_hash_count': len(source_hashes),
        'freeze_matches': True,
        'pi_report_words': report_words,
        'result_words': result_words,
    }
    write('CHECKPOINT_SUMMARY.json', summary)
    exposure = {
        'utc': summary['utc'],
        'review_id': P.name,
        'inherited_actual_bytes': ledger['inherited_actual_bytes'],
        'additional_cap_bytes': 180000000,
        'review_additional_charged_upper_bytes': ledger['additional_charged_bytes'],
        'lineage_charged_upper_bytes': summary['lineage_charged_upper_bytes'],
        'accounting': 'Encoded file bytes plus declared uncompressed NPY member lengths (including headers), charged once per process/cache key; 2,000,000-byte conservative allowance covers ordinary repeated context/source text and metadata reads. This is a conservative charged bound, not a claim of exact operating-system IO. Review-generated files are derived outputs, not new scientific source exposure.',
        'read_ledger': 'READS.json',
        'input_hashes': 'INPUT_HASHES.json',
        'network_requests': 0,
        'network_bytes': 0,
        'consumed_cases': list(range(400, 408)),
        'case_status': 'Previously consumed synthetic whole tuples; all review grids and precision checks are postvalidation diagnostics, with no restored holdout.',
        'raw_exposure': 'Stored synthetic model/environment/truth arrays and full scalar proposal/gold query logs for cases400-407; selected source-equation response trajectories. No new biological raw records.',
        'ordinary_context': 'LEARNINGS, LAB_WORKFLOW, sprint mission, current brief, main study protocols/reports/source and cached primary article.',
        'protected_data_opened': [],
        'explicitly_unopened': ['Pan20 sealed target', 'Flesch81 protected observations', 'later HABITS waves', 'reserved worm/memory observations'],
        'original_sources_modified': False,
        'old_ledgers_modified': False,
        'new_plants': 0,
        'teacher_or_readout_fits': 0,
        'actor_campaign_reruns': 0,
        'scientific_process_concurrency': 1,
        'thread_limits': 'OPENBLAS/OMP/MKL/VECLIB=2 in review_core before NumPy import for response and log scripts.',
        'active_jobs': 0,
        'sharing': 'Local review artifacts and one human-authorized internal completion report to canonical PI only.',
        'manual_final_usage_checkpoint': {'utc_date': '2026-10-31', 'used_percent': 43, 'remaining_percent': 57, 'ordinary_usage_allowed': True, 'credits_or_reset_used': False},
    }
    write('EXPOSURE.json', exposure)
    write('RUNTIME.json', {
        'utc': summary['utc'],
        'python_executable': sys.executable,
        'python_version': sys.version,
        'platform': platform.platform(),
        'numpy_distribution_version': version('numpy'),
        'scipy_distribution_version': version('scipy'),
        'scope': 'Existing model environment used for this review; package metadata only, no install or new source response.',
    })
    excluded = {'MANIFEST.json', '__pycache__'}
    manifest = {}
    for path in sorted(P.iterdir()):
        if path.is_file() and path.name not in excluded:
            data = path.read_bytes()
            manifest[path.name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    write('MANIFEST.json', {'utc': summary['utc'], 'scope': 'Review-directory files only; self and Python cache excluded. Original input hashes are in INPUT_HASHES.json without rereading their payloads.', 'files': manifest})
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
