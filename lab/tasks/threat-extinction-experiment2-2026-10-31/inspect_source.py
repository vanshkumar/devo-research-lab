import datetime as dt
import importlib.util
import json
import pathlib
import resource
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
z = zipfile.ZipFile(ROOT / 'sources/experiment2.zip')
info = [{'name': i.filename, 'compressed_bytes': i.compress_size,
         'decoded_bytes': i.file_size, 'crc32': f'{i.CRC:08x}'} for i in z.infolist()]
assert sum(i['decoded_bytes'] for i in info) < 500000
print('ARCHIVE', json.dumps(info))
license_data = json.loads((ROOT / 'sources/license.json').read_text())
print('LICENSE', json.dumps(license_data['data']['attributes']))
for suffix in ['READ ME.txt', 'syntax_SCR.sps', 'Syntax_US_expectancy.sps']:
    n = next(n for n in z.namelist() if n.endswith('/' + suffix))
    text = z.read(n).decode('utf-8-sig', errors='replace')
    (ROOT / suffix.replace(' ', '_')).write_text(text)
    print('\nSOURCE_TEXT', suffix, '\n', text)
n = next(n for n in z.namelist() if n.endswith('/Secondary extinction exp2.dat'))
with z.open(n) as f:
    sample = f.read(4000)
(ROOT / 'SMALL_LOG_PREFIX.txt').write_bytes(sample)
print('ACTUAL_LOG_PREFIX', sample.decode('utf-8-sig', errors='replace'))
print('DEPENDENCIES', {m: importlib.util.find_spec(m) is not None for m in ['numpy', 'scipy', 'pandas', 'pyreadstat']})
out = {'command': 'python3 lab/tasks/threat-extinction-experiment2-2026-10-31/inspect_source.py',
       'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'archive_directory': info,
       'license_attributes': license_data['data']['attributes'],
       'actual_log_prefix_bytes': len(sample), 'participant_check_complete': False,
       'scientific_read_charge_bytes': 1000000,
       'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(ROOT / 'SOURCE_INSPECTION.json').write_text(json.dumps(out, indent=2) + '\n')
print('RESOURCE', json.dumps(out, default=str))
