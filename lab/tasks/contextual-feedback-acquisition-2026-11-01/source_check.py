"""Inspect only declared source metadata, with explicit original-data modes added as needed."""
import json
import hashlib
import html
import re
import datetime
import pathlib
import resource
import sys
import zipfile

root = pathlib.Path(__file__).resolve().parent
if sys.argv[1] == 'metadata':
    obj = json.loads((root / 'sources/figshare_4265408v1_net.payload').read_bytes())
    print(json.dumps({k: obj.get(k) for k in
                      ['id', 'title', 'version', 'doi', 'description', 'license', 'files']}, indent=2))
elif sys.argv[1] == 'archive_metadata':
    path = root / 'sources/cited_BehavioralData.payload'
    digest = hashlib.md5(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as z:
        members = [{'name': m.filename, 'bytes': m.file_size,
                    'compressed_bytes': m.compress_size, 'crc': m.CRC}
                   for m in z.infolist()]
    result = {'md5': digest, 'matches_publisher': digest == '95ec5996736d59fa02fd80a781a74710',
              'members': members, 'all_trial_payloads': 'compressed acquisition/hash only, no member decoding in this mode'}
    (root / 'ARCHIVE_METADATA.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'md5': digest, 'matches_publisher': result['matches_publisher'],
                      'member_count': len(members),
                      'person_members': {folder: [m['name'] for m in members
                                         if m['name'].startswith(folder + '/') and m['name'].endswith('.mat')]
                                         for folder in ['data_exp1', 'data_exp2']}}, indent=2))
elif sys.argv[1] == 'archive_code':
    with zipfile.ZipFile(root / 'sources/cited_BehavioralData.payload') as z:
        name = 'Behavioral_Variables.m'
        b = z.read(name)
        (root / 'sources/Behavioral_Variables.m').write_bytes(b)
        print('Extraction code only:', name, 'sha256', hashlib.sha256(b).hexdigest())
        print(b.decode('utf-8'))
elif sys.argv[1] == 'final_source_audit':
    meta = json.loads((root / 'sources/figshare_4265408v1_net.payload').read_bytes())
    archive_path = root / 'sources/cited_BehavioralData.payload'
    with zipfile.ZipFile(archive_path) as z:
        code_bytes = z.read('Behavioral_Variables.m')
        code = code_bytes.decode('utf-8')
        names = z.namelist()
        people = {folder: sorted(n for n in names if n.startswith(folder + '/') and n.endswith('.mat'))
                  for folder in ['data_exp1', 'data_exp2']}
    assert [len(people[k]) for k in ['data_exp1', 'data_exp2']] == [50, 35]
    assert 'subjects=1:50' in code and 'subjects=1:35' in code
    assert 'reward and reward omission' in code and 'reward and punishment' in code
    archive_bytes = archive_path.read_bytes()
    assert hashlib.md5(archive_bytes).hexdigest() == meta['files'][0]['computed_md5']
    evidence = {}
    for year, needles in {
        '2015': ['available upon request', 'post-learning test', 'We tested 28 subjects'],
        '2017': ['Each experiment involved', '192 trials', 'outcome probabilities', '4265408.v1']
    }.items():
        p = root / ('sources/paper' + year + '.payload')
        b = p.read_bytes()
        t = b.decode('utf-8')
        t = re.sub(r'<(script|style)\b.*?</\1>', ' ', t, flags=re.I | re.S)
        t = html.unescape(re.sub(r'<[^>]*>', ' ', t))
        t = re.sub(r'\s+', ' ', t)
        evidence[year] = {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b), 'contexts': {}}
        for needle in needles:
            pos = t.lower().find(needle.lower())
            evidence[year]['contexts'][needle] = (None if pos < 0 else t[max(0, pos - 100):pos + 450])
        if year == '2017':
            assert '192 trials' in t and '4265408.v1' in t
            assert 'Each experiment involved N = 20' in t
        if year == '2015':
            assert 'available upon request' in t and 'We tested 28 subjects' in t
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = {'completed_utc': now, 'status': 'CLOSE_SOURCE_DESIGN_GATE',
              'scientific_milestone_passed': False,
              'original_person_training_feedback_first_transfer_calculation': 'UNRUN: no certified defining original record',
              'person_payloads_decoded': 0, 'person_response_values_interpreted': 0,
              'archive_md5': hashlib.md5(archive_bytes).hexdigest(),
              'archive_sha256': hashlib.sha256(archive_bytes).hexdigest(),
              'archive_bytes': len(archive_bytes),
              'archive_metadata_people_counts': {k: len(v) for k, v in people.items()},
              'archive_code_sha256': hashlib.sha256(code_bytes).hexdigest(),
              'archive_code_bytes': len(code_bytes),
              'archive_code_defines': 'Experiment1 reward/reward-omission N50; Experiment2 reward/punishment N35; four fixed probability-pair plots',
              'paper2017_defines': 'N20/N20; partial/complete feedback; four contexts, 24 exposures per context, two sessions, 192 training trials; no terminal common transfer test described',
              'linkage_verdict': 'Cited object does not certify the paper2017 original trial population/design; actual attribution unresolved, not a corruption or invalid-paper finding',
              'paper2015_original_record': 'Not located in bounded exact-family search; not proven unavailable',
              'main_fit_forecasts_controls_target_scoring': 'UNRUN',
              'evidence': evidence,
              'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'scope': 'Source provenance/design audit only; no empirical learning-law conclusion'}
    (root / 'SOURCE_AUDIT.json').write_text(json.dumps(result, indent=2) + '\n')
    first = {k: result[k] for k in ['completed_utc', 'status', 'scientific_milestone_passed',
             'original_person_training_feedback_first_transfer_calculation', 'person_payloads_decoded',
             'person_response_values_interpreted', 'archive_metadata_people_counts', 'scope']}
    (root / 'FIRST_DATA_CHECK.json').write_text(json.dumps(first, indent=2) + '\n')
    print(json.dumps(result, indent=2))
print('peak_rss', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
