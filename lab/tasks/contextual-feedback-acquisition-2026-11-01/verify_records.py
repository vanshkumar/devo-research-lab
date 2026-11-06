"""Record-only consistency verification after the source gate has closed."""
import datetime
import hashlib
import json
import pathlib
import platform
import resource

root = pathlib.Path(__file__).resolve().parent
pins = json.loads((root / 'SOURCE_PINS.json').read_bytes())
checks = {}
read_bytes = 0
for item in pins['sources']:
    b = (root / item['local']).read_bytes()
    read_bytes += len(b)
    assert len(b) == item['bytes']
    assert hashlib.sha256(b).hexdigest() == item['sha256']
    checks[item['local']] = True
for p in sorted(root.glob('*.json')):
    b = p.read_bytes()
    read_bytes += len(b)
    json.loads(b)
first = json.loads((root / 'FIRST_DATA_CHECK.json').read_bytes())
audit = json.loads((root / 'SOURCE_AUDIT.json').read_bytes())
res = json.loads((root / 'RESOURCES.json').read_bytes())
ops = json.loads((root / 'PUBLIC_OPERATIONS.json').read_bytes())
assert first['scientific_milestone_passed'] is False
assert first['person_payloads_decoded'] == 0
assert audit['status'] == 'CLOSE_SOURCE_DESIGN_GATE'
assert len(ops['operations']) == ops['top_level_attempts'] == res['public_top_level_attempts'] == 20
assert res['conservative_public_operation_charge'] == ops['conservative_operation_charge'] == 24
assert sum(i['bytes'] for i in pins['sources'] if 'archive_member' not in i) == res['measured_saved_application_body_bytes']
assert res['jobs'] == 0
out = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'scope': 'Record-only verification; no participant decoding or new science',
       'source_pins_match': checks, 'json_valid': True, 'milestone_honestly_unrun': True,
       'operation_and_ingress_arithmetic_match': True,
       'explicit_payload_reads_this_pass_bytes': read_bytes,
       'python_version': platform.python_version(),
       'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'physical_io_runtime_reads': 'unknown'}
(root / 'FINAL_RECORD_AUDIT.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
