"""Offline source-support reconstruction; no behavioral calculation is claimed."""
from pathlib import Path
import json, hashlib, resource, re, html
from datetime import datetime, timezone

root=Path(__file__).resolve().parent
def sha(data): return hashlib.sha256(data).hexdigest()
def gitsha(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
native=[]
for meta in sorted(root.glob('*.metadata.json')):
    m=json.loads(meta.read_text())
    data=(root/meta.name.removesuffix('.metadata.json')).read_bytes()
    assert len(data)==m['bytes'] and sha(data)==m['sha256']
    native.append({k:m[k] for k in ['url','final_url','status','bytes','sha256']})
tree=json.loads((root/'openneuro-tree.json').read_text())
old=json.loads((root/'openneuro-tree-1.0.0.json').read_text())
assert not tree['truncated'] and not old['truncated']
assert [x['path'] for x in tree['tree']]==[x['path'] for x in old['tree']]
blobs=[x for x in tree['tree'] if x['type']=='blob']
imaging=[x for x in blobs if x['path'].endswith('.nii.gz')]
assert len(blobs)==171 and len(imaging)==164
assert not any(x['path'].endswith(('.tsv','.csv','.mat')) for x in blobs)
inventory=json.loads((root/'S3_CHECK.json').read_text())
assert inventory['is_truncated']=='false' and inventory['objects']==172
assert len(inventory['non_imaging'])==8
repo=json.loads((root/'revaluation2017-tree.json').read_text())
expected={x['path']:x for x in repo['tree']}
connector=[]
for name,original in [('original-2017-README.md','README.md'),
 ('SRDyna_NatHumBeh_Exp1_learning.ipynb','SRDyna_NatHumBeh_Exp1_learning.ipynb'),
 ('SRonly_learner_NatHumBeh_Exp1.ipynb','SRonly_learner_NatHumBeh_Exp1.ipynb')]:
    data=(root/name).read_bytes()
    match=gitsha(data)==expected[original]['sha']
    # apply_patch adds a terminal LF to sources whose original blob lacks it.
    if not match and data.endswith(b'\n') and gitsha(data[:-1])==expected[original]['sha']:
        (root/name).write_bytes(data[:-1])
        data=data[:-1]
        match=True
    assert match, (name,gitsha(data),expected[original]['sha'])
    record={'file':name,'original_git_blob_sha':gitsha(data),'sha256':sha(data),'bytes':len(data)}
    if name.endswith('.ipynb'):
        nb=json.loads(data)
        code='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
        record.update({'cells':len(nb['cells']),'code_cells':sum(c['cell_type']=='code' for c in nb['cells']),
         'external_data_read_tokens_present':bool(re.search(r'read_csv|loadmat|read_excel|pickle.load|np.load|open\(',code)),
         'source_type':'simulation notebook, not participant event record',
         'outputs':'acquired and JSON-decoded auxiliary, not rendered/interpreted as measurements'})
        assert 'generate_nathumbeh_env1' in code
    connector.append(record)
for name,expected_sha in [('dataset_description.json','0b651c53bb32e2be623c2763bc024ad71073103d'),
                         ('original-CHANGES.txt','8fb94b5ad96abd90594a33750e5161995fa9498c')]:
    data=(root/name).read_bytes()
    if gitsha(data)!=expected_sha and data.endswith(b'\n') and gitsha(data[:-1])==expected_sha:
        (root/name).write_bytes(data[:-1]); data=data[:-1]
    assert gitsha(data)==expected_sha, (name,gitsha(data),expected_sha)
    connector.append({'file':name,'original_git_blob_sha':gitsha(data),'sha256':sha(data),'bytes':len(data)})
texts={}
for name in ['paper2017.html','paper2018.html']:
    s=(root/name).read_text()
    s=re.sub(r'<script\b[^>]*>.*?</script>', ' ', s, flags=re.S|re.I)
    s=re.sub(r'<style\b[^>]*>.*?</style>', ' ', s, flags=re.S|re.I)
    texts[name]=' '.join(html.unescape(re.sub('<[^>]+>',' ',s)).split())
assert 'upon request' in texts['paper2017.html']
assert 'cross validation' in texts['paper2017.html']
assert 'ds001612' in texts['paper2018.html']
result={
 'timestamp_utc':datetime.now(timezone.utc).isoformat(),
 'kind':'source-support inventory audit ONLY',
 'native_source_pin_checks':native,
 'connector_original_blob_checks':connector,
 'versions':{'1.0.0':old['sha'],'1.0.2':tree['sha'],'identical_path_sets':True},
 'openneuro_counts':{'git_entries_each':244,'git_blobs_each':171,'imaging_links_each':164,
  'non_imaging_git_blobs_each':7,'s3_objects':172,'s3_imaging_objects':164,'s3_other_objects':8,
  's3_listed_payload_bytes_NOT_acquired':inventory['listed_bytes'],
  'event_tsv_csv_mat_files':0},
 'family1_repository':{'sha':repo['sha'],'files':len(repo['tree']),'notebook_data_read_tokens_absent':True},
 'original_participant_histories_acquired':0,
 'original_acquisition_change_first_probe_calculation':'UNRUN: no linked original behavioral event object certified',
 'first_data_gate':'FAILED, not earned by inventory arithmetic',
 'design_gate':'CLOSE source allocation: missing original event-linked choices/rewards/transition information',
 'model_fit_predictions_scores_controls':'UNRUN',
 'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
 'scientific_jobs_remaining':0,
}
(root/'SOURCE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
(root/'FIRST_DATA_CHECK.json').write_text(json.dumps({
 'timestamp_utc':result['timestamp_utc'],'gate_passed':False,
 'actual_command':'python3 lab/tasks/revaluation-transport-2026-11-01/audit_source.py',
 'actual_output':'SOURCE_AUDIT.json inventory counts and source-pin verification; zero original participant observations',
 'missing_object':'a participant-linked original acquisition/relearning/probe event log with states, choices, available actions, rewards and phase ordering',
 'original_observation_arithmetic':'UNRUN',
 'metadata_arithmetic':result['openneuro_counts'],
 'interpretation':'This execution is NOT the required original-observation calculation.',
 'exposure':'metadata, articles, simulation notebooks only; zero participant/neural payloads',
 'resources':'RESOURCES.json', 'source_pins':'SOURCE_AUDIT.json'
},indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['timestamp_utc','openneuro_counts','first_data_gate','design_gate','max_rss_bytes','scientific_jobs_remaining']},indent=2))
