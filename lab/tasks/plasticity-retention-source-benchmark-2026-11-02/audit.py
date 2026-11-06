"""Inspect saved outputs and account resources; never rerun learning."""
import datetime
import hashlib
import json
from pathlib import Path
import resource

root = Path(__file__).resolve().parent
read_bytes = 0


def read_json(name):
    global read_bytes
    b = (root / name).read_bytes()
    read_bytes += len(b)
    return json.loads(b)


inv = read_json('INVENTORY.json')
short = read_json('FEASIBILITY.json')
full = read_json('FULL_FEASIBILITY.json')
rs = read_json('REALIZATION.json')
rf = read_json('FULL_REALIZATION.json')
manifest = read_json('SOURCE_MANIFEST.json')
ops = read_json('PUBLIC_OPERATIONS.json')
assert ops['charged_operations'] == len(ops['operations']) == 30
assert short['config']['updates'] == 30000 and full['config']['updates'] == 1000000
assert short['reference']['finite_difference_passes'] == 7
assert full['reference']['finite_difference_passes'] == 8
assert full['reference']['teacher_exact_integer_checks'] == 3232
assert len(full['boundary_diagnostics']) == 100
assert all(r['scalar_update_max_abs_error'] < 1e-11
           for result in (short, full) for r in result['reference']['sgd_scalar_reference'])
assert (rs['teacher_weights'], rs['teacher_bias'], rs['teacher_out_weights'], rs['teacher_out_bias']) == (
    rf['teacher_weights'], rf['teacher_bias'], rf['teacher_out_weights'], rf['teacher_out_bias'])
for name, expected in [('REALIZATION.json', short), ('FULL_REALIZATION.json', full)]:
    b = (root / name).read_bytes()
    read_bytes += len(b)
    assert hashlib.sha256(b).hexdigest() == expected['realization_sha256']
source_bytes = 0
for row in manifest['files']:
    b = (root / 'vendor' / row['path']).read_bytes()
    read_bytes += len(b)
    source_bytes += len(b)
    assert len(b) == row['bytes']
    assert hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest() == row['blob_sha1']
files = []
for p in sorted(root.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:
        b = p.read_bytes()
        read_bytes += len(b)
        files.append({'path': str(p.relative_to(root)), 'bytes': len(b),
                      'sha256': hashlib.sha256(b).hexdigest()})
now = datetime.datetime.now(datetime.timezone.utc)
anchor = datetime.datetime(2026, 11, 3, 1, 27, 30, tzinfo=datetime.timezone.utc)
output = {
    'task': 'plasticity-retention-source-benchmark-2026-11-02',
    'audit_utc': now.isoformat(), 'elapsed_seconds_including_orientation': (now - anchor).total_seconds(),
    'native_initial_anchor': anchor.isoformat(),
    'one_substantive_premain_revision_used': True,
    'public_operations_charged': 30, 'public_operations_delivered': 29,
    'work_families': 3,
    'new_ingress': {'cap_bytes': 200000000, 'source_code_payload_bytes_exact': source_bytes,
                    'provider_allowance_charged_bytes': 58000000,
                    'allowance_basis': '2MB for each of 29 delivered public operations, including source-file payload and failed opens; predelivery denied archive has zero delivered acquisition',
                    'actual_total_ingress': 'UNCERTIFIED: provider responses, internal redirects/subrequests and failed physical transfers unknown',
                    'dependencies_installed': 0, 'published_data_or_model_payload_acquired': 0,
                    'repository_archive_acquired': False},
    'separate_additional_read': {'cap_bytes': 1000000000, 'charged_allowance_bytes': 100000000,
                               'inventory_source_read_bytes_exact': inv['source_read_bytes'],
                               'this_audit_explicit_file_read_hash_decode_bytes': read_bytes,
                               'context': 'Full LEARNINGS once in bounded excerpts plus two excerpts reread after truncated combined output; all ordinary context/brief/tree/source reads charged',
                               'runtime_library_cache_physical_io': 'unknown; allowance is not OS I/O certification'},
    'processes': {'simultaneous_scientific_processes': 1, 'simultaneous_numerical_threads': 1,
                  'successful_inventory': {'exit_code': 0, 'peak_rss_bytes': inv['max_rss_native']},
                  'short_original_task': {'exit_code': 0, 'total_seconds': short['total_seconds'],
                                          'learning_seconds': short['learning_seconds_including_checkpoint_references'],
                                          'peak_rss_bytes': short['max_rss_bytes']},
                  'full_original_task': {'exit_code': 0, 'total_seconds': full['total_seconds'],
                                         'learning_seconds': full['learning_seconds_including_checkpoint_references'],
                                         'peak_rss_bytes': full['max_rss_bytes'],
                                         'native_session': 50923, 'native_session_exit_code': 0},
                  'audit_peak_rss_bytes_so_far': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  'rss_cap_bytes': 1000000000, 'provider_toolhost_peak_rss': 'unknown',
                  'scientific_learning_failures': 0,
                  'jobs_after_completion': 0},
    'failed_or_denied_access': [
        'Before registration: native clock denied, no task identity; no science/write executed',
        'ls .venv/bin/python* denied for unquoted shell expansion',
        'Archive curl pre-tool denied for process-control path; no archive acquired; charged operation 17',
        'Explicit .venv Python ls denied because interpreter symlink escapes repository; no dependency execution',
        'python -c inventory denied because inline code/composition blocked; subsequently saved inventory.py executed',
        'arXiv v2 404; actual abs history then certifies v1',
        'PMC continuation recaptcha and Nature IDP/500; earlier primary text/indexed primary passages retained',
        'CVPR HTML and PDF 403; exact methods unverified',
        'One combined orientation output and two oversized metadata outputs truncated; relevant memory excerpts reread and compact source pins saved',
        'apply_patch extra final newline in source-file additions trimmed only beyond declared size, then all 12 original Git blob hashes verified'
    ],
    'exposure': {'old_empirical_protected_payloads': 0, 'old_fits_rescored': 0,
                 'public_summary_and_tree': 'All returned search snippets, primary views and complete repository path/size/SHA tree exposed; no binary/tree blobs implicitly read',
                 'source_files': 12,
                 'synthetic_generated_examples_including_unused_blocks': 1050000,
                 'synthetic_learned_updates': 1030000,
                 'synthetic_teacher_instances': 'two identical teacher draws from seed1729; not independent replications',
                 'short_generated_contexts': 4, 'full_generated_contexts': 101,
                 'full_distinct_contexts': len(set(map(tuple, rf['contexts']))),
                 'label_tables_exposed': 'All 4x32 and 101x32 teacher labels, all fast indices, teacher/learner parameters and saved boundary predictions; unused final 10,000-example blocks are generated/exposed, not pristine holdouts',
                 'holdout_or_main_science': 'UNRUN; no source budget or observation status resets'},
    'remaining_unknowns': ['Original Torch/RNG/float32 numerical replay', 'CBP/control/reference execution',
                           'Replay and all-old-context scorer costs', 'Complete closest-prior residual/novelty',
                           'Main matched-retention advantage and uncertainty', 'Distinct independent adversarial review'],
    'artifact_hashes_before_terminal_records': files
}
(root / 'RESOURCES.json').write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps({'audit_utc': output['audit_utc'], 'elapsed_seconds': output['elapsed_seconds_including_orientation'],
                  'audit_explicit_read_bytes': read_bytes, 'source_bytes': source_bytes,
                  'max_scientific_rss_bytes': max(short['max_rss_bytes'], full['max_rss_bytes']),
                  'full_distinct_contexts': output['exposure']['full_distinct_contexts'],
                  'artifact_files_hashed': len(files), 'status': 'PASS_saved_artifacts_only_no_learning_rerun'}))
