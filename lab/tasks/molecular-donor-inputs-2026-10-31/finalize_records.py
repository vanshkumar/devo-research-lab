"""Build the finite audit's source/exposure/resource records offline."""
import datetime
import hashlib
import json
from pathlib import Path
import sys

import h5py
import numpy as np

root = Path(__file__).resolve().parent
requests = json.loads((root / 'REQUESTS.json').read_text())
audit = json.loads((root / 'INPUT_AUDIT.json').read_text())
mouse_sample = json.loads((root / 'MOUSE_SAMPLE_CHECK.json').read_text())
mouse_units = json.loads((root / 'MOUSE_UNITS_CHECK.json').read_text())
mouse_focused = json.loads((root / 'MOUSE_FOCUSED_UNITS_CHECK.json').read_text())
human_files = json.loads((root / 'sources/human_files.bin').read_text())['_embedded']['bitstreams']
mouse_files = json.loads((root / 'sources/mouse_files.bin').read_text())['_embedded']['bitstreams']
mouse_collection = json.loads((root / 'sources/mouse_collection.bin').read_text())
human = audit['human_reused_small_sample']
n_non_target = sum(x['non_target_stored_entries'] for x in human['cells'])
assert n_non_target == 29962
assert len(requests) == len(audit['all_source_response_integrity']) == 31
assert all(x['size_and_sha256_pass'] for x in audit['all_source_response_integrity'])


def save(name, value):
    (root / name).write_text(json.dumps(value, indent=2) + '\n')


def listing(values):
    return [{'name': x['name'], 'uuid': x['uuid'], 'declared_size_bytes': x['sizeBytes'],
             'publisher_declared_whole_file_checksum': x['checkSum'],
             'content_url': x['_links']['content']['href'],
             'whole_payload_downloaded_or_checksum_verified': False} for x in values]


manifest = {
    'human_deposit': {'doi': '10.17863/CAM.111988', 'handle': '1810/373636',
        'item_uuid': 'cad1c61a-e4e5-4443-ad11-92e4f48b3861', 'license': 'CC BY 4.0',
        'complete_original_bundle_listing': listing(human_files)},
    'mouse_deposit': {'doi': '10.17863/CAM.87955', 'handle': '1810/340518',
        'item_uuid': '8f9c3683-29fd-44f3-aad5-7acf5e963a75', 'license': 'CC BY 4.0',
        'complete_original_bundle_listing': listing(mouse_files)},
    'institutional_source_chain': {'url': 'https://www.mrl.ims.cam.ac.uk/our-research/data-sharing-hypomap',
        'exact_human_dataset_id': 'a2c833f7-b7f1-4f4d-ad31-cae478b601b7',
        'exact_mouse_dataset_id': 'dbb4e1ed-d820-4e83-981f-88ef7eb55a35',
        'collection_index_response': 'sources/cellxgene_collections.bin',
        'selected_collections': 'METADATA_cellxgene_collections.json'},
    'mouse_mirror': {k: mouse_collection[k] for k in ('collection_id', 'collection_version_id', 'collection_url', 'doi', 'revised_at')},
    'mouse_asset': mouse_collection['datasets'][0]['assets'][0],
    'mouse_dataset_version_id': mouse_collection['datasets'][0]['dataset_version_id'],
    'mouse_observed_etag': mouse_focused['etag'],
    'mirror_specific_license_independently_inspected': False,
    'third_party_87b802cc_candidate_downloaded': False,
    'human_reused_small_sample': {'source_asset': human['source_asset'], 'n_cells': human['n_cells'],
        'donor_ids': human['donor_ids_in_these_six_cells'], 'non_target_stored_entries': n_non_target,
        'original_leaf_file_pins': [x for x in audit['read_file_manifest'] if x['path'].startswith('campaigns/')],
        'source_provenance': 'campaigns/hypomap_quantitative_2026-10-28/PROVENANCE.md',
        'whole_hdf5_reread_in_this_tranche': False},
    'response_and_range_pins': [{'label': x['label'], 'url': x['url'], 'status': x.get('status'),
        'error': x.get('error'), 'saved_file': x['saved_file'], 'bytes': x['bytes_received'], 'sha256': x['sha256'],
        'retrieved_utc': x['finished_utc'], 'range_request': x['request_headers'].get('Range')}
        for x in requests],
    'full_response_headers_and_failures': 'REQUESTS.json',
    'provider_receipts': ['WEB_RECEIPT.json', 'WEB_MIRROR_RECEIPT.json', 'WEB_COLLECTION_RECEIPT.json'],
    'whole_atlas_sha256_claimed': False
}
save('SOURCE_MANIFEST.json', manifest)

mouse_ranges = [x for x in requests if x.get('status') == 206 and '2408fb24' in x['url']]
mouse_range_bytes = sum(x['bytes_received'] for x in mouse_ranges)
assert mouse_range_bytes == 9184724 and mouse_range_bytes < 10_000_000
exposure = {
    'inherited_not_reset': {'selected_receptor_rows': 70, 'distinct_selected_gene_pairs': 40,
        'selected_cluster_expression_values': 229, 'global_values': 140, 'source_ratios': 70,
        'all_previous_HYPOMAP_gene_donor_cell_summary_exposures': 'remain consumed; see prior authoritative campaign/pilot/review records'},
    'mouse_new': {'physical_range_bytes': mouse_range_bytes, 'physical_range_responses': len(mouse_ranges),
        'encoded_nonrequested_content_in_coarse_ranges': 'retained and charged; not declared pristine',
        'decoded': 'root/obs/var field names, donor category strings and donor-code array structure',
        'donor_categories': mouse_focused['units']['donor_id']['categories'],
        'donor_category_cell_counts_decoded': False, 'expression_values_interpreted': 0,
        'certified_independent_mouse_animals': 0},
    'human_reused': {'cells': [x['source_row_index'] for x in human['cells']],
        'donors': human['donor_ids_in_these_six_cells'], 'new_pristine_evaluation_cells': 0,
        'full_old_raw_index_arrays_reread': True, 'decoded_array_bytes': human['raw_indices_decoded_bytes'],
        'target_panel_size_masked_before_expression_summaries': 54,
        'old_receptor_values_may_be_present_in_decoded_arrays': 'yes; prior consumed exposure preserved, no receptor scores or new pristine status',
        'non_target_entries_summarized': n_non_target, 'whole_old_count_matrix_or_range_cache_opened': False},
    'published_clusters_and_atlas_summaries': 'remain conditioning/exposure limits',
    'primary_prediction_and_controls': 'unrun', 'one_to_one_ortholog_table_certified': False,
    'protected_or_unrelated_payloads_opened': False,
    'all_previous_failures_freezes_and_target_restrictions': 'unchanged'
}
save('EXPOSURE.json', exposure)

application = sum(x['bytes_received'] for x in requests)
provider = 10_000_000
transport_margin = 2_000_000
read_components = {'ordinary_context_source_code_and_tool_output_allowance': 50_000_000,
    'acquisition_body_copy_persistence_and_hash_pass_allowance': 60_000_000,
    'all_HDF5_failed_cached_and_logical_pass_allowance': 60_000_000,
    'JSON_CSV_NPZ_inspection_human_leaf_and_audit_pass_allowance': 50_000_000,
    'final_records_verification_manifest_and_report_allowance': 30_000_000}
charged_read = sum(read_components.values())
start = datetime.datetime.fromisoformat('2026-10-31T19:51:29.229+00:00')
now = datetime.datetime.now(datetime.timezone.utc)
assert (now - start).total_seconds() < 120 * 60
assert len(requests) + 5 < 40
assert application + provider + transport_margin < 1_000_000_000
assert charged_read < 2_000_000_000
recorded_peak = max(audit['peak_rss_bytes_macos'], mouse_sample['peak_rss_bytes_macos'],
    mouse_units['peak_rss_bytes_macos'], mouse_focused['peak_rss_bytes_macos'],
    max(x['peak_rss_bytes_macos'] for x in requests))
assert recorded_peak < 2_000_000_000
accounting = {
    'start_authorized_utc': start.isoformat(), 'saved_at_utc': now.isoformat(),
    'deadline_utc': '2026-10-31T21:51:29.229Z', 'elapsed_minutes_at_save': (now - start).total_seconds() / 60,
    'scientific_status': 'completed_input_attempt_primary_unrun_acquisition_route_closed',
    'scientific_jobs': 0, 'maximum_concurrent_scientific_processes': 1, 'numerical_threads': 1,
    'usage_start_check': {'pi_checked_at_utc': '2026-10-31T19:51:29.229Z', 'remaining_percent': 54,
        'ordinary_usage_allowed': True, 'secondary_window': 'unavailable', 'credits_or_reset_used': False},
    'new_requests': {'script_attempts_including_failed_DNS': len(requests), 'provider_operations': 5,
        'provider_breakdown': {'initial_queries': 2, 'explorer_open': 1, 'targeted_query': 1, 'find': 1},
        'charged_total': len(requests) + 5, 'cap': 40, 'unused': 40 - len(requests) - 5,
        'provider_internal_backend_request_count': 'unavailable; public operations counted explicitly'},
    'new_ingress': {'measured_application_body_bytes': application, 'provider_allowance_bytes': provider,
        'transport_margin_bytes': transport_margin, 'charged_bytes': application + provider + transport_margin,
        'cap_bytes': 1_000_000_000, 'exact_transport_and_provider_bytes': 'unavailable'},
    'additional_scientific_read_decoded': {'charged_bytes': charged_read, 'cap_bytes': 2_000_000_000,
        'conservative_components': read_components,
        'exact_OS_level_total': 'not metered; all repeated/cached/failed/decoded/context/output passes covered by conservative charges',
        'known_direct_file_bytes_in_input_audit': audit['known_direct_file_bytes_read_in_this_command'],
        'decoded_human_raw_index_array_bytes': human['raw_indices_decoded_bytes'],
        'mouse_sample_logical_HDF5_bytes': mouse_sample['logical_hdf5_read_bytes'],
        'mouse_offline_unit_logical_HDF5_bytes': mouse_units['logical_hdf5_read_bytes'],
        'mouse_focused_unit_logical_HDF5_bytes': mouse_focused['logical_hdf5_read_bytes'],
        'mouse_audit_logical_HDF5_bytes': audit['mouse_offline_structure_hdf5_logical_bytes']},
    'recorded_peak_rss_bytes': recorded_peak, 'RSS_cap_bytes': 2_000_000_000,
    'whole_tranche_continuous_peak_profiling': False,
    'preserved_prior_ledgers': {'molecular_pilot_read_decoded_bytes': 191_451_239,
        'molecular_review_read_decoded_bytes': 73_081_679, 'sum_prior_molecular_reads': 264_532_918,
        'molecular_ingress_charged_bytes': 20_165_421, 'molecular_public_requests': 20,
        'historic_HYPOMAP_range_ingress_bytes_separate_ledger': 3_277_786_552,
        'historic_range_payload_reread_in_this_tranche': 0},
    'additive_molecular_totals': {'read_decoded_charged_bytes': 264_532_918 + charged_read,
        'ingress_charged_bytes': 20_165_421 + application + provider + transport_margin,
        'public_operations': 20 + len(requests) + 5},
    'versions': {'python': sys.version.split()[0], 'numpy': np.__version__, 'h5py': h5py.__version__,
                 'hdf5': h5py.version.hdf5_version},
    'seed': 'none; deterministic input audit, no fit or simulation',
    'unexecuted_local_failures_covered_by_context_allowance': ['rejected ordinary shell read expressions or binary context reads',
        'missing lab/STATE path; root STATE used instead', 'unquoted question mark in one URL caused zsh glob error before request',
        'inline resource-summary helper rejected; scoped script used instead'],
    'no_full_atlas_no_get_storage_size_no_credits_no_infrastructure': True
}
save('ACCOUNTING.json', accounting)

excluded = {'ARTIFACT_MANIFEST.json', 'STATE.md', 'BRIEF.md', 'DELIVERY_RECEIPT.json'}
artifacts = []
for path in sorted(root.rglob('*')):
    if not path.is_file() or path.name in excluded or '__pycache__' in path.parts:
        continue
    data = path.read_bytes()
    artifacts.append({'path': str(path.relative_to(root)), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
save('ARTIFACT_MANIFEST.json', {'stable_owned_artifacts': artifacts, 'excluded_mutable_or_PI_owned_files': sorted(excluded)})
print(json.dumps({'requests': accounting['new_requests'], 'ingress': accounting['new_ingress'],
    'charged_additional_read_bytes': charged_read, 'additive_molecular_totals': accounting['additive_molecular_totals'],
    'recorded_peak_rss_bytes': recorded_peak, 'elapsed_minutes_at_save': accounting['elapsed_minutes_at_save'],
    'versions': accounting['versions'], 'stable_artifacts_pinned': len(artifacts), 'jobs': 0}, indent=2))
