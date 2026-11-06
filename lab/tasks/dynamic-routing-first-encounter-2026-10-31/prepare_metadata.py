import json,base64,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;P=R.parent/'dynamic-routing-rule-transfer-2026-10-31'
todo=[]
for x in json.loads((P/'zarr.json').read_bytes()):
    root=x['nwb_path'].replace('s3://aind-open-data/','https://aind-open-data.s3.us-west-2.amazonaws.com/');sid=root.split('/')[-1].split('_')[0]
    if sid not in ['664851','713655','759434']:continue
    todo.extend([(root+'/.zmetadata','metadata/'+sid+'.json',1000000),(root.rsplit('/',1)[0]+'/data_description.json','metadata/'+sid+'_description.json',100000),(root+'/general/subject/subject_id/0','metadata/'+sid+'_subject.bin',1000),(root+'/general/session_id/0','metadata/'+sid+'_session.bin',1000),(root+'/general/source_script/0','metadata/'+sid+'_source.bin',1000)])
(R/'unit_metadata.json').write_text(json.dumps(todo,indent=2)+'\n')
blob=json.loads((R/'source_RLmodel_blob.json').read_bytes());b=base64.b64decode(blob['content']);assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==blob['sha']
(R/'source_RLmodel.py.txt').write_bytes(b)
print('REQUESTS',len(todo))
if (R/'FIRST_DATA_CHECK.json').exists() and not (R/'FIRST_DATA_CHECK_v0.json').exists(): (R/'FIRST_DATA_CHECK_v0.json').write_bytes((R/'FIRST_DATA_CHECK.json').read_bytes())
