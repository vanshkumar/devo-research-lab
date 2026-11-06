"""One capped original-source acquisition and first record reconstruction; stdlib only."""
import csv
import datetime as dt
import difflib
import hashlib
import io
import json
import pathlib
import resource
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
URL = 'https://raw.githubusercontent.com/petal-cs-pitt/petal-cs-pitt.github.io/master/Data/annotated_revision_improvements.csv.zip'
EXPECTED_BLOB = '00581db66ef19161a18a5eaf1fb92495a11bc527'
CAP = 250_000

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def main():
    target = ROOT / 'revision_improvements.csv.zip'
    acquisition = {'url': URL, 'expected_git_blob': EXPECTED_BLOB, 'started_at': now(), 'cap': CAP}
    if target.exists():
        payload = target.read_bytes()
        acquisition['network'] = 'cached; no request'
    else:
        request = urllib.request.Request(URL, headers={'User-Agent': 'bounded-public-research/1.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            acquisition.update(status=response.status, final_url=response.url, headers=dict(response.headers.items()))
            payload = response.read(CAP + 1)
        acquisition['received_bytes'] = len(payload)
        acquisition['finished_at'] = now()
        (ROOT / 'ACQUISITION.json').write_text(json.dumps(acquisition, indent=2) + '\n')
        if len(payload) > CAP:
            raise RuntimeError('Acquisition cap exceeded; preserve charged bytes and stop')
        target.write_bytes(payload)
    blob = hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()
    assert blob == EXPECTED_BLOB, (blob, EXPECTED_BLOB)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        directory = [{'path': x.filename, 'compressed': x.compress_size, 'uncompressed': x.file_size, 'crc32': format(x.CRC, '08x')} for x in archive.infolist()]
        candidates = [x for x in archive.infolist() if x.filename.lower().endswith('.csv') and not x.filename.startswith('__MACOSX/')]
        assert len(candidates) == 1, directory
        member = candidates[0]
        assert member.file_size < 3_000_000
        raw = archive.read(member)
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    row = next(reader)
    result = {
        'calculated_at': now(), 'source_bytes': len(payload), 'source_sha256': hashlib.sha256(payload).hexdigest(),
        'source_git_blob': blob, 'directory': directory, 'member_sha256': hashlib.sha256(raw).hexdigest(),
        'member_bytes': len(raw), 'fields': reader.fieldnames, 'first_original_row': row,
        'exposure': 'Whole compressed archive acquired and hashed; complete CSV inflated/UTF8 decoded; header and first record tokenized/interpreted only. No untouched-unacquired claim for any row.',
        'rss_bytes_macos': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'status': 'Original row decoded; inspect fields and reconstruct edit/evaluation before treating as required milestone.'
    }
    (ROOT / 'FIRST_SOURCE_ROW.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
