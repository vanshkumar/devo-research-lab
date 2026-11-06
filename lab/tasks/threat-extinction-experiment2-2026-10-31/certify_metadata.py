import collections
import datetime as dt
import hashlib
import json
import pathlib
import resource
import zipfile
from first_data_check import first_sav

ROOT = pathlib.Path(__file__).resolve().parent
z = zipfile.ZipFile(ROOT / 'sources/experiment2.zip')
metadata = {}
for suffix in ['SCR data_SE_exp2.sav', 'US expectancy_SE_exp2.sav']:
    n = next(n for n in z.namelist() if n.endswith('/'+suffix))
    metadata[suffix] = first_sav(z.read(n), case_limit=60,
        selected={'PP_number', 'PPnum_2', 'File', 'Conditie', 'CS_counterbalancing'})['cases']
scr, expect = metadata.values()
scrids = [int(r['PP_number']) for r in scr]
expids = [int(r['PP_number']) for r in expect]
assert len(set(scrids)) == len(set(expids)) == 60
assert set(scrids) == set(expids)
mismatches = [{'scr': {r['PP_number']: r for r in scr}[e['PP_number']], 'expectancy': e}
              for e in expect if {r['PP_number']: r for r in scr}[e['PP_number']]['Conditie'] != e['Conditie']]
(ROOT / 'METADATA_PAIRING_CHECK.json').write_text(json.dumps({'metadata': metadata, 'condition_mismatches': mismatches}, indent=2)+'\n')
print('CONDITION_MISMATCHES', json.dumps(mismatches))
assert all(m['scr']['Conditie'] == '' for m in mismatches), 'conflicting nonblank condition'
assert all({r['PP_number']: r for r in scr}[r['PP_number']]['CS_counterbalancing'] == r['CS_counterbalancing'] for r in expect)
inputs = collections.defaultdict(list)
n = next(n for n in z.namelist() if n.endswith('/Secondary extinction exp2.dat'))
with z.open(n) as f:
    header = f.readline().decode('utf-8-sig').rstrip('\r\n').split('\t')
    for line in f:
        fields = line.rstrip(b'\r\n').split(b'\t')
        # Response and latency values of all other participants remain opaque bytes.
        row = {header[k]: fields[k].decode('utf8') for k in [2, 3, 4, 5, 6, 9]}
        inputs[int(row['subject'])].append(row)
assert set(inputs) == set(scrids)
assert all(sum(r['blocknum']=='3' and r['trialcode'].startswith('CS') for r in rows)==15 for rows in inputs.values())
assert all(sum(r['blocknum']=='4' and r['trialcode'].startswith('CS') for r in rows)==18 for rows in inputs.values())
assert all(sum(r['trialcode']=='shock' for r in rows)==3 for rows in inputs.values())
assert all(not any(r['trialcode']=='shock' for r in rows if r['blocknum']=='4') for rows in inputs.values())
forced_development = {1, 109, 110}
assert forced_development <= set(scrids)
rank = sorted(set(scrids)-forced_development, key=lambda i: hashlib.sha256(f'extinction2-20261031-{i}'.encode()).hexdigest())
evaluation = sorted(rank[:20])
development = sorted(set(scrids)-set(evaluation))
out = {'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'metadata': metadata,
       'independent_unit': 'source participant ID, 60 unique IDs in each supplied channel and log',
       'paired_id_sets_equal': True, 'condition_pairing_equal_except_blank_SCR_120': True,
       'condition_missing_not_silently_imputed': mismatches, 'inputs': dict(inputs),
       'source_schedule': 'paper: CS1/CS2 always reinforced at offset in acquisition, CSminus never; extinction unreinforced; logged three unsignalled shocks after extinction',
       'hardware_delivery_audit': 'unavailable; no acquisition US-specific field or event timestamps; source-defined schedule, not independent hardware verification',
       'scoring': 'source GSR supplied peak-minus-baseline features /1000 to microS; <=0.02 to0; full-record maximum then sqrt in published syntax; use past-prefix scaling for forecast',
       'small_sample_rating_matches': 33, 'small_sample_paired_PP_number': 1,
       'development_ids': development, 'evaluation_ids': evaluation,
       'initial_outcome_exposure_ids': [1,109,110],
       'additional_read_charge_bytes': 3000000,
       'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(ROOT / 'SOURCE_CERTIFICATION.json').write_text(json.dumps(out, indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['metadata', 'inputs']}, indent=2))
