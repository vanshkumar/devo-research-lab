"""Record-only final checks/sealing of this completed review. No scientific rerun."""
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
read_allowance = 0


def read(path):
    global read_allowance
    b = path.read_bytes()
    read_allowance += 3*len(b)
    return b


def write(name, value):
    (HERE/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


pins_path = HERE/'SOURCE_PINS.json'
previous_manifest = HERE/'ARTIFACT_PINS.json'
previous_sealing_passes = json.loads(read(previous_manifest)).get('sealing_passes', 1) if previous_manifest.exists() else 0
pins = json.loads(read(pins_path))
archive_path = HERE/'RECONSTRUCTION_VERBOSE.json'
archive = read(archive_path)
archive_sha = hashlib.sha256(archive).hexdigest()
remapped = 0
for pin in pins['source_pins']:
    if pin['path'] == str((HERE/'RECONSTRUCTION.json').relative_to(ROOT)) and pin['sha256'] == archive_sha:
        pin['path'] = str(archive_path.relative_to(ROOT))
        remapped += 1
pins['record_only_manifest_note'] = 'Pins refer to actual objects read. The verbose reconstruction is pinned at its preserved archive path after record compaction; FINAL_AUDIT retains the true original time-of-read path.'
write('SOURCE_PINS.json', pins)

checked_json = []
for path in sorted(HERE.glob('*.json')):
    json.loads(read(path))
    checked_json.append(path.name)
broken_links = []
for name in ['README.md','REVIEW.md','ASSUMPTIONS_AND_EXPOSURE.md','STATE.md','PROPOSED_LEARNING.md']:
    for target in re.findall(r'\]\(([^)]+)\)', read(HERE/name).decode()):
        if '://' in target or target.startswith('#'):
            continue
        if not (HERE/target.split('#')[0]).exists():
            broken_links.append(dict(file=name, target=target))
assert not broken_links, broken_links

summary = dict(utc=datetime.now(timezone.utc).isoformat(), record_only=True,
    JSON_files_valid=checked_json, broken_report_links=broken_links,
    archived_reconstruction_manifest_paths_remapped=remapped,
    archived_reconstruction_sha256=archive_sha,
    explicit_read_hash_decode_allowance_bytes=read_allowance,
    numerical_reexecution=False, live_jobs=0,
    required_outputs_present=all((HERE/x).exists() for x in ['FIRST_CALCULATION.json','CONTRARY_PLAN.md','CONTRARY.json','REVIEW.md','README.md','STATE.md','SOURCE_PINS.json','RESOURCES.json','PROPOSED_LEARNING.md']))
write('ARTIFACT_CHECK.json', summary)
resources = json.loads(read(HERE/'RESOURCES.json'))
resources['final_record_sealing_current_explicit_allowance_so_far_bytes'] = read_allowance
resources['final_record_sealing_passes'] = previous_sealing_passes+1
resources['cumulative_record_sealing_containing_allowance_bytes'] = 20000000*(previous_sealing_passes+1)
resources['final_record_sealing_note'] = '20MBper record-sealing pass contains its JSON/link checks and output hashing, preserving earlier pass charges; included within existing290MBcontaining booking. Full actual per-pass allowance is in ARTIFACT_PINS. No scientific rerun or cap extension.'
write('RESOURCES.json', resources)

manifest = []
for path in sorted(HERE.iterdir()):
    if not path.is_file() or path.name == 'ARTIFACT_PINS.json':
        continue
    b = read(path)
    manifest.append(dict(path=path.name, bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
write('ARTIFACT_PINS.json', dict(utc=datetime.now(timezone.utc).isoformat(), files=manifest,
    explicit_record_check_and_sealing_allowance_bytes=read_allowance,
    sealing_passes=previous_sealing_passes+1,
    excluded=['ARTIFACT_PINS.json itself'], note='Per-file integrity; saved hashes do not independently prove historical nonaccess.'))
print(json.dumps(dict(valid_json_files=len(checked_json), broken_links=len(broken_links),
    remapped_archival_manifest_entries=remapped, pinned_artifacts=len(manifest),
    total_record_check_and_sealing_allowance_bytes=read_allowance, required_outputs_present=summary['required_outputs_present'], live_jobs=0), indent=2))
