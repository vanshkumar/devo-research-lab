"""Package this completed offline review; no source acquisition or science rerun."""
import json, hashlib, datetime, resource
from pathlib import Path
R=Path(__file__).resolve().parent
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(name):return json.loads((R/name).read_bytes())
def write(name,x):(R/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
stages={k:load(k+'_RESOURCES.json') for k in ['FIRST','AUDIT','SUPPORT']}
tracked=sum(x['input_read_and_decoded_bytes'] for x in stages.values())
peak=max(x['peak_rss_bytes'] for x in stages.values())
assert tracked<120_000_000 and peak<500_000_000
assert all(x['public_operations']==0 and x['ingress_bytes']==0 for x in stages.values())
assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat('2026-11-01T04:25:19.634+00:00')
resources=dict(created_utc=now,status='COMPLETE_offline_independent_review_no_real_evaluation_scores',
    public_operations=0,new_ingress_bytes=0,scientific_commands_completed=3,all_scientific_commands_exit_code=0,jobs=0,
    actual_id='01a19536-325a-7410-a689-b87e130531cc',authorized_start_utc='2026-11-01T03:45:19.634Z',
    confirmed_START_delivery_utc='2026-11-01T03:47:35.479Z',absolute_deadline_utc='2026-11-01T04:25:19.634Z',
    finite_limits=dict(public_operations=0,ingress_bytes=0,additional_read_decode_hash_bytes=180_000_000,peak_rss_bytes=500_000_000,scientific_processes=1,numerical_threads=1),
    explicitly_counted_input_decode_hash_bytes=tracked,
    additional_conservative_manual_phase_charges=dict(first_raw_reconstruction_and_codec_handling=30_000_000,
       freeze_forecast_contrary_and_synthetic_arithmetic=45_000_000,
       source_units_and_generator_reconstruction=30_000_000,
       ordinary_reads_library_imports_packaging_hashes_and_terminal_docs=15_000_000),
    charged_additional_read_decode_hash_bytes=120_000_000,
    charge_method='Conservative manual phase charges INCLUDE the 25,163,572 explicitly listed bytes, variable arrays, package extraction/loading, repeated ordinary/scientific reads, interpreter/library handling, packaging and terminal hashes. They are not added a second time. Exact OS/runtime I/O is not metered; no metering service was added.',
    largest_measured_scientific_peak_rss_bytes=peak,
    measured_stage_peaks={k:v['peak_rss_bytes'] for k,v in stages.items()},
    current_review_failed_scientific_commands=0,current_review_unknown_failed_scientific_peak='NOT_APPLICABLE: no scientific command failed',
    ordinary_pre_START_hook_denials='Two read command syntaxes rejected before child execution; no science. Initial PI START send rejected before delivery for stale usage, preserved in registry.',
    prior_lineage=dict(public_operations=108,charged_ingress_bytes=13_573_172,charged_read_decode_hash_bytes=355_000_000,
        author_largest_measured_local_rss_bytes=93_536_256,failed_provider_and_failed_process_peaks='UNKNOWN_preserved'),
    additive_lineage=dict(public_operations=108,charged_ingress_bytes=13_573_172,charged_read_decode_hash_bytes=475_000_000),
    shared_environment_mutations=0,dependency_handling='Cached trusted wheel extracted only to review-local deps; existing environment unchanged',
    remaining_checks='UNRUN_CHECKS.md',heartbeat='UNCHANGED_same_active_30minute_PI_heartbeat')
assert sum(resources['additional_conservative_manual_phase_charges'].values())==resources['charged_additional_read_decode_hash_bytes']
write('RESOURCES.json',resources)
write('EXPOSURE.json',dict(created_utc=now,status='CONSUMED_not_reset_by_independent_context',
    real_sessions={'742903_2024-10-22':538,'664851_2023-11-15':534,'713655_2024-08-09':515,'759434_2025-02-04':545},
    total_real_joined_rows=2132,all_acquired_real_columns='CONSUMED; inherited development21/evaluation14 each plus two controller vectors',
    controller_vectors={'742903_development_existing_column':538,'713655_existing_full_vector':515,'759434_existing_full_vector':545},
    prior_summary_exposure=['complete original notebook JSON','consolidated schemas','all five inventory session/method/performance summaries'],
    independent_read_scope='Existing four-session compressed columns, unit scalars, acquired source/task text, pinned coefficients/probabilities and synthetic controls; no newly acquired real observations',
    hypothetical_channel_comparison='postvalidation fixed-history feature comparison only; no hypothetical probabilities/losses scored',
    real_evaluation_primary_secondary_ablation_stratum_uncertainty_losses='UNCOMPUTED',
    synthetic_rows_generated=137728,synthetic_saved_endpoint_truths_outcomes_verified=960,
    new_public_operations=0,new_ingress_bytes=0,
    forbidden_or_protected_payloads_accessed=[],
    protected_preserved=['excluded668755 trial payload','sixth session','neural/original raw sensor data','Pan20','Flesch81/B2/B20 responses','later HABITS','memory target answers','four reserved worms','Figure4/optional210 outcomes','other closed fitting/raw branches'],
    source_cause_and_hardware_ground_truth='NOT_IDENTIFIED; source-script URL is an archive assertion',
    new_context_restores_validation=False))
write('SOURCE_MANIFEST.json',dict(created_utc=now,mode='offline reuse of closed cached sources',
    upstream_response_URLs_dates_and_SHA256='PINS_AND_FREEZE.json: source_response_pins',
    source_units_licenses_descriptions_and_Git_pins='SOURCE_SUPPORT.json',
    compressed_and_decoded_source_read_pins=['FIRST_RESOURCES.json','AUDIT_RESOURCES.json','SUPPORT_RESOURCES.json'],
    ancestor_task=str(R.parents[1]/'tasks/dynamic-routing-first-encounter-2026-10-31'),
    data_license='CC-BY-4.0 verified separately for each of four assets',
    codec_license='Numcodecs MIT; cached PyPI-pinned platform wheel, SHA256 f2207871868b2464dc11c513965fd99b958a9d7cde2629be7b2dc84fdaab013b',
    source_code_license='Task source license not independently certified; inspected as evidence, never imported/executed',
    no_external_retrieval=True))
pins={}
for p in sorted(R.rglob('*')):
    if not p.is_file() or any(x in p.relative_to(R).parts for x in ['deps','__pycache__']):continue
    if p.name in ['REVIEW_PINS.json','COMMUNICATION_STATUS.json','STATE.md']:continue
    b=p.read_bytes();pins[str(p.relative_to(R))]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
write('REVIEW_PINS.json',dict(created_utc=now,excludes=['deps (trusted wheel separately pinned)','__pycache__','REVIEW_PINS.json','COMMUNICATION_STATUS.json','STATE.md (terminal delivery status)'],paths=pins))
print(json.dumps(dict(status=resources['status'],scientific_peak_rss=peak,tracked_bytes=tracked,manual_charge=120_000_000,review_artifacts_pinned=len(pins),jobs=0,completed_before_deadline=True),indent=2))
