import collections
import csv
import datetime as dt
import io
import json
import pathlib
import resource
import zipfile
from first_data_check import first_sav

ROOT = pathlib.Path(__file__).resolve().parent
z = zipfile.ZipFile(ROOT / 'sources/experiment2.zip')
result = {'command': 'python3 lab/tasks/threat-extinction-experiment2-2026-10-31/certify_sample.py',
          'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'samples': {}}
for suffix in ['SCR data_SE_exp2.sav', 'US expectancy_SE_exp2.sav']:
    name = next(n for n in z.namelist() if n.endswith('/' + suffix))
    result['samples'][suffix] = first_sav(z.read(name))
scr = result['samples']['SCR data_SE_exp2.sav']['first_case']
expect = result['samples']['US expectancy_SE_exp2.sav']['first_case']
print('FIRST_IDENTIFIERS', {k: scr.get(k) for k in ['File', 'PPnum_2', 'PP_number', 'Conditie', 'Condition', 'CS_counterbalancing']},
      {k: expect.get(k) for k in ['Averageofresponse', 'PP_number', 'Conditie', 'CS_counterbalancing']})
name = next(n for n in z.namelist() if n.endswith('/Secondary extinction exp2.dat'))
subjects = collections.Counter()
sample = []
with z.open(name) as f:
    header = f.readline().decode('utf-8-sig').rstrip('\r\n').split('\t')
    for line in f:
        fields = line.rstrip(b'\r\n').split(b'\t')
        subject = fields[2].decode('ascii')
        subjects[subject] += 1
        if subject == str(int(expect['PP_number'])):
            sample.append(dict(zip(header, [v.decode('utf8', errors='replace') for v in fields])))
result['raw_log_header'] = header
result['raw_log_subject_counts'] = dict(subjects)
result['raw_sample_rows'] = sample
result['sav_first_case_pair_equal_PP_and_counterbalancing'] = (
    scr['PP_number'] == expect['PP_number'] and scr['CS_counterbalancing'] == expect['CS_counterbalancing'])
counts = collections.Counter((r['blocknum'], r['trialcode']) for r in sample)
rating_matches = []
occurrence = collections.Counter()
for r in sample:
    if r['trialcode'].startswith('CS'):
        phase = {'3': 'Acq', '4': 'Ext'}.get(r['blocknum'])
        cue = {'CS1': 'CSplus1', 'CS2': 'CSplus2', 'CSm': 'CSmin'}[r['trialcode'].split('_')[0]]
        occurrence[(phase, cue)] += 1
        if phase:
            key = f'{phase}_{cue}_{occurrence[(phase,cue)]}'
            rating_matches.append({'key': key, 'raw': float(r['response']), 'sav': expect.get(key),
                                   'equal': float(r['response']) == expect.get(key)})
result['raw_to_sav_rating_checks'] = rating_matches
print('RAW_SUBJECT_COUNT', len(subjects), 'FIRST_CASE_RAW_ROWS', len(sample), 'TRIALCOUNTS', list(counts.items()))
print('RATING_MATCHES', rating_matches)
print('RAW_SAMPLE_INPUTS', [{k: r[k] for k in ['subject', 'blockcode', 'blocknum', 'trialcode', 'trialnum', 'stimulus1']} for r in sample])
for suffix in ['syntax_SCR.sps', 'Syntax_US_expectancy.sps']:
    text = (ROOT / suffix).read_text()
    print('SCORING_SYNTAX', suffix, '\n', text)
result['additional_read_charge_bytes'] = 2000000
result['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
(ROOT / 'SAMPLE_CERTIFICATION.json').write_text(json.dumps(result, indent=2) + '\n')
print('RESOURCE', result['additional_read_charge_bytes'], result['peak_rss_bytes'])
