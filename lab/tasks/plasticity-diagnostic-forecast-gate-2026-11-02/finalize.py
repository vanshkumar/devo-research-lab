"""Bounded saved-output/resource/pin audit; never runs learning."""
import hashlib
import json
from pathlib import Path
import re
import resource
import sys
import time

ROOT = Path(__file__).resolve().parent


def main():
    started = time.perf_counter()
    reads = 0
    records = {}
    for name in ('PREPARE_OUTPUT.json', 'BLIND_FORECASTS.json', 'DIRECT_FORECASTS.json',
                 'ACQUISITION_OUTPUT.json', 'AUDIT.json'):
        raw = (ROOT / name).read_bytes()
        reads += len(raw)
        records[name] = json.loads(raw)
    prep, blind, direct, acq, audit = (records[name] for name in records)
    refs = prep['scalar_references'] + acq['scalar_references']
    scalar_max = max(row['scalar_max_abs'] for row in refs)
    fd = [row['finite_difference_scaled_max'] for row in refs if 'finite_difference_scaled_max' in row]
    assert prep['history_updates'] == 1000000 and acq['continuing_future_updates'] == 60000
    assert len(refs) == 16 and len(fd) == 10
    assert scalar_max < 1e-10
    assert blind['saved_utc'] < direct['saved_utc'] < acq['acquisition_started_utc']
    assert audit['chronology_checks_pass'] and audit['no_new_evaluation_or_predictor_fit']
    durations = [prep['total_seconds'], direct['total_seconds'], acq['total_seconds'], audit['total_seconds']]
    explicit_reads = (prep['explicit_input_bytes_this_phase'] + direct['explicit_input_bytes_this_phase']
                      + acq['explicit_input_bytes_this_phase'] + audit['explicit_input_bytes'])
    ledger = [
        {'op': 1, 'batch': 1, 'kind': 'query', 'program': 'Lyle', 'query': 'Lyle Understanding plasticity neural networks diagnostic loss plasticity probe task predict learning'},
        {'op': 2, 'batch': 1, 'kind': 'query', 'program': 'Dohare', 'query': 'Dohare 2024 loss of plasticity dead units effective rank weight magnitude slowly changing regression'},
        {'op': 3, 'batch': 2, 'kind': 'open', 'program': 'Lyle', 'url': 'https://proceedings.mlr.press/v202/lyle23b/lyle23b.pdf'},
        {'op': 4, 'batch': 2, 'kind': 'open', 'program': 'Juliani_Ash', 'url': 'https://proceedings.neurips.cc/paper_files/paper/2024/file/ce7984e36d58659211a8dc7d5457cd6f-Paper-Conference.pdf', 'status': 'FAILED_provider_content_too_large_declared_15076523_bytes'},
        {'op': 5, 'batch': 2, 'kind': 'open', 'program': 'Dohare', 'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11338828/'},
        {'op': 6, 'batch': 3, 'kind': 'open_existing_primary', 'program': 'Lyle', 'line': 245},
        {'op': 7, 'batch': 3, 'kind': 'query', 'program': 'Juliani_Ash', 'query': '"ce7984e36d58659211a8dc7d5457cd6f" plasticity'},
        {'op': 8, 'batch': 3, 'kind': 'query', 'program': 'Juliani_Ash', 'query': '"predictive power of the dead unit count" plasticity'},
        {'op': 9, 'batch': 4, 'kind': 'open', 'program': 'Juliani_Ash', 'url': 'https://openreview.net/pdf?id=MsUf8kpKTF', 'status': 'browser_challenge_no_paper_no_bypass'},
        {'op': 10, 'batch': 4, 'kind': 'open_existing_primary', 'program': 'Lyle', 'line': 600},
        {'op': 11, 'batch': 5, 'kind': 'query', 'program': 'Juliani_Ash', 'query': '"A Study of Plasticity Loss in On-Policy Deep Reinforcement Learning" arxiv github'},
        {'op': 12, 'batch': 5, 'kind': 'query', 'program': 'Lyle', 'query': '"Understanding Plasticity in Neural Networks" github code Lyle'},
        {'op': 13, 'batch': 6, 'kind': 'open', 'program': 'Juliani_Ash', 'url': 'https://arxiv.org/html/2405.19153v2'},
        {'op': 14, 'batch': 7, 'kind': 'open_existing_primary', 'program': 'Juliani_Ash', 'line': 114},
        {'op': 15, 'batch': 7, 'kind': 'open', 'program': 'Lyle', 'url': 'https://arxiv.org/html/2402.18762v2', 'status': 'FAILED_404_no_detailed_claims_used'},
    ]
    assert len(ledger) == 15
    (ROOT / 'PUBLIC_OPERATIONS.json').write_text(json.dumps({
        'conservative_operations': 15, 'cap': 20, 'deliberately_screened_programs': 3,
        'operations': ledger, 'raw_tool_rendered_responses': 'PUBLIC_SOURCE_RESPONSES.json',
        'response_bundle_original_pdf_bytes_certified': False,
        'new_public_code_data_checkpoints_dependencies_downloaded': 0,
        'license_notes': {
            'original_Dohare_code': 'MIT; all12 exact cached original Git blobs verified',
            'Dohare_paper': 'CC BY4.0 in primary PMC text',
            'Lyle_2023_paper': 'author copyright notice; no separate code/release license certified',
            'Juliani_Ash_arxiv_v2': 'arXiv perpetual non-exclusive license in primary HTML',
            'new_external_datasets_or_dependencies': 'none'},
        'summary_exposure': 'All results in saved responses, including incidental later work, source titles and search excerpts; only three programs followed.',
    }, indent=2) + '\n')
    manifest = []
    # Hash all current task files except mutable status/report/resources and
    # this self-referential manifest. No outside path or protected file read.
    skip = {'REPRODUCTION_MANIFEST.json', 'FINAL_AUDIT.json', 'RESOURCES.json',
            'STATE.md', 'TERMINAL_REPORT.md'}
    for path in sorted(ROOT.iterdir()):
        if path.is_file() and path.name not in skip:
            raw = path.read_bytes()
            reads += len(raw)
            manifest.append({'file': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    (ROOT / 'REPRODUCTION_MANIFEST.json').write_text(json.dumps({
        'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'scope': 'saved task artifacts excluding mutable status/report/resource/self files',
        'source_pins': blind['source'], 'files': manifest,
        'dependencies': 'Python3.9.6 standard library only; no installs; interpreter/runtime source pins not complete',
    }, indent=2) + '\n')
    resources = {
        'task': 'plasticity-diagnostic-forecast-gate-2026-11-02',
        'actual_owner': '01a19fa1-e738-7ab1-938f-57e7b3ef2764', 'status': 'CLOSE_no_main',
        'initial_native_utc': '2026-11-03T04:19:10Z',
        'fixed_gates_utc': ['2026-11-03T04:39:10Z', '2026-11-03T04:54:10Z', '2026-11-03T05:04:10Z', '2026-11-03T05:29:10Z'],
        'actual_forecasts_reference_completed_utc': acq['utc'],
        'close_saved_before_first_gate': True,
        'new_public_operations': {'charged': 15, 'cap': 20, 'programs': 3, 'includes_failures': True},
        'new_ingress': {'charged_conservative_provider_allowance_bytes': 200000000, 'cap_bytes': 200000000,
                        'actual_provider_ingress_bytes': 'unknown', 'compliance': 'UNCERTIFIED',
                        'note': 'Full allowance conservatively charged; provider PDF/parser/search/redirect/failure bytes not metered. No new code/data/model/dependency payload downloaded.'},
        'additional_read_hash_decode_context': {
            'separate_charged_conservative_bytes': 100000000, 'cap_bytes': 1000000000,
            'explicit_science_data_bytes_before_final_packaging': explicit_reads,
            'explicit_packaging_input_hash_bytes': reads,
            'ordinary_context_code_import_earlier_passes': 'included in conservative allowance; not fully enumerated',
            'physical_io_bytes': 'unknown', 'complete_io_compliance_certified': False},
        'process': {'recorded_science_seconds_before_packaging': sum(durations),
                    'conservative_cumulative_seconds_booking': 60, 'cap_seconds': 900,
                    'recorded_packaging_seconds': time.perf_counter() - started,
                    'maximum_measured_scientific_rss_bytes': max(prep['max_rss_bytes'], direct['max_rss_bytes'], acq['max_rss_bytes'], audit['max_rss_bytes']),
                    'rss_cap_bytes': 1000000000,
                    'one_process_native_python_thread_at_a_time': True,
                    'wrapper_provider_host_runtime_peaks_startup_physical_io': 'unknown'},
        'revisions': {'substantive_used': 0, 'cap': 1, 'predictor_retuning_after_outcomes': 0},
        'updates': {'original_history': 1000000, 'future_continuing': 60000,
                    'random_target_copy_initial': 212000, 'random_target_copy_replay': 12000,
                    'true_target_privileged_copy': 12000, 'total_sgd_updates': 1296000},
        'exposure': {'status': 'all_development_consumed', 'new_original_teacher_learner_realizations': 1,
                     'scorer_teacher_parameters': 2201, 'slow_contexts_generated': 107,
                     'fast_indices_generated': 1070000, 'unused_final_block_indices_exposed': 10000,
                     'all_context_target_support_labels': 3424,
                     'distinct_random_probe_networks_and_32_point_label_tables': 106,
                     'replayed_probe_tables': 6, 'future_branches_sharing_one_mature_state': 6,
                     'true_copy_training_presentations': 12000, 'true_copy_support_score_presentations': 192,
                     'copy_unique_future_labels_maximum_per_branch': 32,
                     'past_all_training_observations_and_all_support_scores': 'consumed',
                     'source_and_incidental_public_summaries': 'all saved tool outputs exposed'},
        'prior_lineage_preserved': {'public_operations': 66, 'charged_ingress_bytes': 229594722,
                                    'ingress_status': 'UNCERTIFIED', 'separate_read_bytes': 2200000000,
                                    'synthetic_examples_consumed': 9130000,
                                    'MNIST': 'all70000decoded/256train64testinterpreted/auxiliaryexposed; no payload reread here',
                                    'other_limitations': 'all source-copy failures, revisions, Torch intent/storage/warnings/thread/runtime/physicalIO unknowns preserved'},
        'source_failures': ['publisher PDF provider content-too-large at declared15076523bytes', 'OpenReview browser challenge', 'Lyle2025v2HTML404'],
        'other_failure': 'pre-execution unsupported wc -lc ordinary orientation read; recovered with wc -l/numeric sed',
        'protected_old_raw_reads': 0, 'old_numerical_state_payload_reads': 0,
        'new_dependencies_installed': 0, 'paid_services_contacts_publication_new_infrastructure': 0,
        'native_science_exit_codes': [0, 0, 0, 0], 'jobs': 0,
        'terminal_report': 'pending_single_send_after_save; no_resend_on_rejection',
    }
    (ROOT / 'RESOURCES.json').write_text(json.dumps(resources, indent=2) + '\n')
    # Check local Markdown links in this owned directory after packaging.
    missing = []
    for path in ROOT.glob('*.md'):
        raw = path.read_text()
        reads += len(raw.encode())
        for link in re.findall(r'\]\(([^)]+)\)', raw):
            if not link.startswith(('http:', 'https:', '#')) and not (ROOT / link).exists():
                missing.append({'file': path.name, 'target': link})
    # TERMINAL_REPORT is written immediately after this audit; do not pretend
    # a pending planned report was already delivered.
    missing_nonpending = [r for r in missing if r['target'] != 'TERMINAL_REPORT.md']
    assert not missing_nonpending, missing_nonpending
    out = {'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'status': 'PASS',
           'scalar_update_checks': len(refs), 'scalar_update_max_abs_gap': scalar_max,
           'finite_difference_checks': len(fd), 'finite_difference_max_scaled_gap': max(fd),
           'chronology_pass': True, 'source_blobs_verified': len(blind['source']['files']),
           'files_hashed': len(manifest), 'missing_local_links': missing,
           'explicit_input_hash_and_context_bytes_this_packaging': reads,
           'total_seconds': time.perf_counter() - started,
           'max_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           'no_learning_or_new_evaluation_executed': True, 'jobs': 0}
    (ROOT / 'FINAL_AUDIT.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out))


if __name__ == '__main__':
    main()
