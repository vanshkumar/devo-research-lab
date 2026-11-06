"""File the completed pilot's existing accounting and artifact hashes only."""
import paired as p

audit = p.read('AUDIT.json')
prep = p.read('PREPARE_OUTPUT.json')
blind = p.read('BLIND_FORECASTS.json')
direct = p.read('DIRECT_FORECASTS.json')
acq = p.read('ACQUISITION_OUTPUT.json')
scorer = p.read('SCORER_CONTINUATION.json')
copy_footprints = [p.core.object_bytes(s) for u in scorer['units'] for s in u['states']]
future_probe_fit_seconds = sum(v['seconds'] for r in blind['forecasts'] for reps in r['replicates'] for v in reps)
record = {
    'filed_utc': p.utc(), 'task': 'plasticity-difficulty-matched-forecast-2026-11-02',
    'status': 'CLOSED_no_main_jobs0', 'scientific_revisions': 0,
    'initial_native_utc': '2026-11-03T04:37:57Z',
    'deadlines_utc': {'prior': '2026-11-03T04:52:57Z', 'actual_reference': '2026-11-03T05:07:57Z',
                      'protocol_or_close': '2026-11-03T05:17:57Z', 'hard': '2026-11-03T05:37:57Z'},
    'evidence_times': audit['chronology'],
    'public_operations_new': 4, 'public_operations_limit': 8, 'new_followed_programs': 1,
    'new_ingress_charge_bytes': 15000000, 'new_ingress_limit_bytes': 15000000,
    'new_ingress_actual_provider_bytes': 'UNKNOWN', 'exact_ingress_compliance': 'UNCERTIFIED',
    'separate_read_import_hash_decode_context_charge_bytes': 500000000,
    'read_limit_bytes': 500000000, 'physical_read_bytes': 'UNKNOWN',
    'read_charge_qualification': 'Full bounded booking retained, not complete OS/provider/import I/O certification. Known explicit numerical reads are small; ordinary context/hook/backend overhead is not completely metered.',
    'peak_scientific_rss_bytes': max(audit['maximum_scientific_rss_bytes_so_far'], p.rss()),
    'rss_limit_bytes': 500000000,
    'script_seconds_measured': audit['measured_previous_script_seconds'] + audit['seconds'],
    'conservative_cumulative_process_charge_seconds': 120,
    'process_limit_seconds': 900,
    'runtime_qualification': 'Internal numerical timings and native command completions; startup/import/final filing overhead not independently fully metered. No failed scientific pass or hidden parallel process.',
    'processes_simultaneous': 1, 'native_python_threads': 1, 'thread_qualification': 'Standard library only; no numerical backend or worker/thread spawn.',
    'interpreter': p.sys.version, 'python_executable': p.sys.executable, 'platform': p.sys.platform,
    'new_sgd_updates': {'original_history': 8000000, 'calibration_random_probes': 1440000,
                        'calibration_labelled_copies': 1440000, 'future_random_probes': 160000,
                        'future_labelled_copies': 160000, 'future_actual_acquisition': 80000,
                        'total': 11280000},
    'additional_full_scalar_reference_updates': 80000,
    'additional_checkpoint_reference_updates_each_method': 48,
    'true_support_label_checks_integer_vs_floating': 12928,
    'random_function_copies': 800,
    'unique_future_teacher_support_labels': 128,
    'future_true_labels_target_blind': 0,
    'future_assay_per_state_steps': 20000, 'future_labelled_copy_per_state_steps': 20000,
    'future_actual_acquisition_per_state_steps': 10000,
    'future_assay_optimizer_fit_seconds_excluding_target_generation_scoring': future_probe_fit_seconds,
    'all_assay_seconds_including_calibration_generation_scoring': prep['costs']['assay_seconds'],
    'future_labelled_copy_complete_phase_seconds': direct['seconds'],
    'calibration_labelled_copy_seconds': prep['costs']['copy_seconds'],
    'parameter_payload_float64_packed_bytes_per_state': 888,
    'measured_python_list_plus_float_state_footprints_bytes': copy_footprints,
    'storage_qualification': '888 is a packed numerical payload reference; implementation uses Python lists/floats. RNG, histories, true/random labels, inputs, model fitting, serialization and interpreter are extra; process RSS and artifact sizes are separate. No storage-optimality or deployment-memory claim.',
    'raw_and_summary_exposure': {
        'independent_units': 4, 'learner_initializations': 8,
        'true_teacher_parameter_sets_generated_scorer_only': 4,
        'contexts_generated': 408, 'historical_contexts_scored': 400,
        'future_contexts_scored': 4, 'unused_extra_contexts': 4,
        'fast_input_draws_generated_including_unused_extra': 4080000,
        'unused_extra_fast_draws': 40000,
        'unused_extra_teacher_labels_generated': 0,
        'history_exact_support_labels': 12800, 'future_exact_support_labels': 128,
        'random_target_support_tables_generated_per_state_copy': 800,
        'random_target_support_values': 25600,
        'calibration_pairs': 36, 'calibration_pair_dependence': 'nine temporal pairs in each of four independent units',
        'all_new_realizations': 'DEVELOPMENT_CONSUMED_no_reuse_as_confirmation',
        'old_numerical_payload_reads': 0, 'protected_payload_reads': 0},
    'prior_charges_preserved': {'public_operations': 81, 'ingress_allowance_bytes': 429594722,
        'ingress_compliance': 'UNCERTIFIED', 'separate_reads': '2.3GB',
        'older_synthetic_observations': 'all9.13M earlier', 'preceding_diagnostic_sgd_updates': 1296000,
        'MNIST': 'full70000 decoded/256train64test and auxiliary exposure preserved; no new reads',
        'all_failures_revisions_source_Torch_storage_runtime_physicalIO_qualifications': 'PRESERVED'},
    'failures': {'scientific_process_failures': 0, 'new_public_source_failures': 0,
        'orientation_only_denials': ['pre-registration clock denied for no unique active task; no clock result',
            'wc -lc combined read option unsupported; no read result; wc -l and bounded numeric sed then succeeded'],
        'failed_native_or_public_traffic_unknowns': 'Orientation denials produced no scientific execution; provider/physical I/O still uncertified'},
    'prohibited_actions': {'paid_compute_or_credits': 0, 'contacts': 0, 'publication': 0,
                          'new_human_experiments': 0, 'installations': 0, 'new_infrastructure': 0,
                          'shared_record_writes': 0, 'native_goal_changes': 0},
    'independent_distinct_review': 'UNRUN_not_claimed', 'full_history_per_update_reference': 'UNRUN',
    'numerical_processes_completed_native_exit0': ['paired.py prepare', 'inspect_blind.py', 'paired.py direct', 'paired.py acquire', 'audit.py'],
    'jobs_remaining': 0}
p.save('RESOURCES.json', record)
names = ['paired.py', 'inspect_blind.py', 'audit.py', 'finalize.py', 'PILOT_PLAN.md', 'PRIOR_INFORMATION_GATE.md',
         'BLIND_FORECASTS.json', 'BLIND_NONDEGENERACY.json', 'CALIBRATION.json', 'SCORER_CONTINUATION.json',
         'PREPARE_OUTPUT.json', 'DIRECT_FORECASTS.json', 'ACQUISITION_OUTPUT.json', 'AUDIT.json',
         'RESULT.md', 'CLOSE.md', 'README.md', 'PROPOSED_LEARNING.md', 'PUBLIC_OPERATIONS.json', 'RESOURCES.json']
files = []
for name in names:
    raw = (p.ROOT / name).read_bytes()
    if name.endswith('.json'):
        p.json.loads(raw)
    files.append({'path': name, 'bytes': len(raw), 'sha256': p.hashlib.sha256(raw).hexdigest()})
p.save('REPRODUCTION_MANIFEST.json', {'utc': p.utc(), 'files': files,
       'reused_helper_path': str(p.CORE_PATH), 'reused_helper_sha256': blind['helper_code_sha256'],
       'original_source_pins': blind['source'],
       'exclude_mutable_delivery_and_state': True, 'hashes_are_not_independent_time_attestation': True})
print(p.json.dumps({'filed_utc': record['filed_utc'], 'decision': 'CLOSE', 'manifest_files': len(files),
    'artifact_bytes_manifested': sum(r['bytes'] for r in files), 'rss': record['peak_scientific_rss_bytes'],
    'measured_script_seconds': record['script_seconds_measured'], 'process_charge_seconds': 120,
    'future_assay_optimizer_fit_seconds_excluding_generation_scoring': future_probe_fit_seconds,
    'python_state_footprints': copy_footprints, 'jobs': 0}), flush=True)
