"""Reproduce the bounded source-screening result offline; no participant data."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'sources'
read_bytes = 0


def read_json(name):
    global read_bytes
    b = (SOURCE / name).read_bytes()
    read_bytes += len(b)
    return json.loads(b)


def main():
    global read_bytes
    versions = read_json('ehlers_versions.json')['hits']['hits']
    original = read_json('ehlers_record_public.json')
    files = read_json('mertens_files.json')
    children = read_json('mertens_children.json')
    wrapper = read_json('ehlers_tree_connector.json')
    tree = json.loads(wrapper['structuredContent']['content'])
    checks = {
        'ehlers_version_ids': [v['id'] for v in versions],
        'ehlers_access': {str(v['id']): {'access_right': v['metadata']['access_right'], 'embargo_date': v['metadata'].get('embargo_date'), 'listed_file_count': len(v['files']), 'version_index': v['metadata']['relations']['version'][0]['index'], 'is_last': v['metadata']['relations']['version'][0]['is_last']} for v in versions},
        'ehlers_declared_license': original['metadata']['license'],
        'ehlers_github_tree_sha': tree['sha'],
        'ehlers_github_tree_truncated': tree['truncated'],
        'ehlers_github_file_names': [x['path'] for x in tree['tree']],
        'ehlers_github_data_files': [x['path'] for x in tree['tree'] if x['path'].lower().endswith(('.rdata', '.rds', '.csv', '.tsv', '.sav', '.mat', '.zip'))],
        'mertens_c3dtn_files': [{'name': x['attributes']['name'], 'size': x['attributes']['size'], 'version': x['attributes']['current_version'], 'hashes': x['attributes']['extra']['hashes']} for x in files['data']],
        'mertens_c3dtn_child_count': len(children['data']),
        'mertens_c3dtn_next_page': files['links']['next'],
    }
    assert all(v['metadata']['access_right'] == 'embargoed' and len(v['files']) == 0 for v in versions)
    assert tree['truncated'] is False
    assert checks['ehlers_github_data_files'] == []
    assert len(files['data']) == 2 and children['data'] == []
    assert files['links']['next'] is None
    pins = []
    for p in sorted(SOURCE.iterdir()):
        if p.is_file():
            b = p.read_bytes()
            read_bytes += len(b)
            pins.append({'path': str(p.relative_to(ROOT)), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()})
    manifest = {
        'created_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'source_pins': pins,
        'acquired_objects_are_metadata_or_search_output_only': True,
        'participant_records_acquired_or_decoded': 0,
        'actual_participant_channel_pairing_certified': False,
        'source1': {'deposit': 'https://osf.io/c3dtn/', 'experiment': 1, 'data_payload_not_acquired': True, 'license_unverified': True, 'paper_doi': '10.1016/j.jbtep.2018.09.007'},
        'source2': {'concept_doi': '10.5281/zenodo.22098433', 'observed_versions': [v['id'] for v in versions], 'access': 'embargoed', 'license_metadata': 'cc-by-4.0', 'embargo_respected': True},
        'uninspected_lead': {'url': 'https://osf.io/dxpb3/', 'basis': 'Primary-paper indexed Experiment 2 methods state a safety CS was added.', 'deposit_metadata_or_data_not_acquired': True, 'new_allocation_required': True},
    }
    (ROOT / 'SOURCE_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    check = {
        'command': 'python3 lab/tasks/threat-extinction-expression-2026-10-31/inspect_sources.py',
        'status': 'BLOCKED_BEFORE_PARTICIPANT_DATA_CHECK',
        'scope': 'Actual executed source-metadata calculation, not an empirical data result or forecasting experiment.',
        'participant_rows_measured': 0,
        'participant_units_certified': 0,
        'paired_channels_certified': False,
        'trial_order_and_delivered_US_chronology_certified': False,
        'checks': checks,
        'scientific_read_bytes_this_command': read_bytes,
        'peak_rss_bytes_this_command': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'completed_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }
    (ROOT / 'FIRST_DATA_CHECK.json').write_text(json.dumps(check, indent=2) + '\n')
    print(json.dumps(check, indent=2))


def closeout():
    r = json.loads((ROOT / 'RESOURCES.json').read_text())
    c = json.loads((ROOT / 'FIRST_DATA_CHECK.json').read_text())
    assert len(r['public_operations']) == r['public_operations_charged'] == 11
    assert sum(x['charge_bytes'] for x in r['public_operations']) == r['ingress_charged_bytes'] == 7023489
    assert r['additional_scientific_read_charged_bytes'] < r['additional_scientific_read_limit_bytes']
    assert r['jobs_at_finish'] == 0 and c['participant_rows_measured'] == 0
    assert all((ROOT / x).is_file() for x in ('STATE.md', 'RESULT.md', 'README.md', 'SOURCE_MANIFEST.json', 'PROTOCOL_STATUS.md', 'PROPOSED_LEARNING.md'))
    result = {'closeout_files_present': True, 'operations': 11, 'ingress_charge_bytes': 7023489, 'additional_read_charge_bytes': 20000000, 'participant_rows': 0, 'jobs': 0, 'command': 'python3 lab/tasks/threat-extinction-expression-2026-10-31/inspect_sources.py --closeout', 'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, 'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    (ROOT / 'CLOSEOUT_CHECK.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    if sys.argv[1:] == ['--closeout']:
        closeout()
    else:
        assert not sys.argv[1:]
        main()
