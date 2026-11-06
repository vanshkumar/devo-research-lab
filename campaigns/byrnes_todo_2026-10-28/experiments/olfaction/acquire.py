"""Bounded public Allen API acquisition, no SDK or 3D volumes needed."""
import pathlib,urllib.request,urllib.parse,json,hashlib,argparse
H=pathlib.Path(__file__).parent;C=H.parents[1];D=C/'data/olfaction';D.mkdir(parents=True,exist_ok=True)
def get(name,url):
 p=D/name
 logpath=D/'manifest.json';log=json.loads(logpath.read_text()) if logpath.exists() else []
 old=next((x for x in log if x['file']==name),None)
 if not p.exists():
  with urllib.request.urlopen(url,timeout=60) as r:b=r.read(10_000_001)
  assert len(b)<=10_000_000;p.write_bytes(b)
 b=p.read_bytes();j=json.loads(b);assert j.get('success') is True,(name,j)
 if old:assert hashlib.sha256(b).hexdigest()==old['sha256'],'Pinned source changed; retain original and review a new version separately.'
 log=[x for x in log if x['file']!=name]+[dict(file=name,url=url,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())];logpath.write_text(json.dumps(log,indent=2)+'\n')
 return j['msg']
def query(model,criteria='',include=''):
 args={'num_rows':'all'}
 if criteria:args['criteria']=criteria
 if include:args['include']=include
 return 'https://api.brain-map.org/api/v2/data/'+model+'/query.json?'+urllib.parse.urlencode(args)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['metadata','unionizes'],default='metadata');a=ap.parse_args()
 get('structures.json',query('Structure','[graph_id$eq1]'))
 m=get('experiments.json',query('ApiConnectivity'))
 print('total',len(m),'keys',list(m[0]),flush=True)
 # Selection is based on primary source injection, never on outcomes.
 chosen=[x for x in m if x.get('structure_id')==507 or x.get('primary_injection_structure_id')==507]
 (H/'selected.json').write_text(json.dumps(chosen,indent=2)+'\n');print('MOB primary candidates',len(chosen));print(json.dumps(chosen[:2],indent=2))
 if a.stage=='metadata':return
 ids=','.join(str(x['data_set_id']) for x in chosen);assert ids
 structures=[507,151,1097,961,38,390,223,512,997]
 filt='[section_data_set_id$in'+ids+'][structure_id$in'+','.join(map(str,structures))+'][hemisphere_id$eq3]'
 rows=get('unionizes.json',query('ProjectionStructureUnionize',filt));print('unionizes',len(rows))
if __name__=='__main__':main()
