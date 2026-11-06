"""Bounded acquisition of two fixed public metadata objects. No raw LFP."""
import datetime
import hashlib
import json
import pathlib
import resource
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
SOURCES = [
    ('hc3_metadata.zip', 'https://crcns.org/files/data/hc3/crcns-hc3-metadata-tables.zip'),
    ('dandi000044.json', 'https://api.dandiarchive.org/api/dandisets/000044/versions/draft/'),
]

def main():
    records = []
    for name, url in SOURCES:
        record = {'url': url, 'name': name,
                  'at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'bounded-source-audit/1.0'})
            with urllib.request.urlopen(req, timeout=25) as response:
                data = response.read(5_000_001)
                record.update(status=response.status, final_url=response.url,
                              headers=dict(response.headers), bytes=len(data))
            if len(data) > 5_000_000:
                record['error'] = '5 MB object cap exceeded; consumed prefix retained'
            (ROOT / name).write_bytes(data)
            record['sha256'] = hashlib.sha256(data).hexdigest()
        except Exception as error:
            record['error'] = repr(error)
            if isinstance(error, urllib.error.HTTPError):
                data = error.read(1_000_000)
                (ROOT / (name + '.error')).write_bytes(data)
                record.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        records.append(record)
        print(json.dumps(record))
    report = {'records': records, 'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (ROOT / 'ACQUISITION.json').write_text(json.dumps(report, indent=2) + '\n')

if __name__ == '__main__':
    main()
