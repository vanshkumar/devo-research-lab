"""Offline reproduction. Does not reacquire sources or change split/freeze records."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time,os
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1]

def call(args,name):
 p=ROOT/'logs'/('reproduce_'+name+'.log')
 with p.open('w') as log:subprocess.run([sys.executable,*[str(a) for a in args]],cwd=REPO,stdout=log,stderr=subprocess.STDOUT,check=True,env=dict(os.environ,MPLCONFIGDIR='/tmp/target_event_matplotlib'))
 print(name,'OK',flush=True)

def main(full=False):
 started=time.time();assert (ROOT/'protocol/VALIDATION_RELEASE.json').exists(),'Validation has not been released'
 for item in json.loads((ROOT/'provenance/source_manifest.json').read_text()):
  p=REPO/'sources/learning_intervention_feasibility_2026-10-28'/item['local'];assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],p
 before={p.name:json.loads(p.read_text()) for p in [ROOT/'outputs/validation_Hand_raw_change_all.json',ROOT/'outputs/transfer_fig3.json'] if p.exists()}
 frozen=json.loads((ROOT/'protocol/FINAL_FREEZE.json').read_text());bad=[]
 for path,h in frozen['files_sha256'].items():
  if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=h:bad.append(path)
 if bad:raise RuntimeError('Frozen code/protocol differs: '+str(bad))
 call([ROOT/'experiments/evaluate.py','--part','development'],'development')
 call([ROOT/'experiments/evaluate.py'],'validation')
 call([ROOT/'audits/independent_extraction/reconstruct.py','--part','validation'],'independent_validation')
 if (ROOT/'protocol/TRANSFER_RELEASE.json').exists():call([ROOT/'experiments/transfer.py'],'transfer')
 call([ROOT/'experiments/state_models.py','evaluate'],'state_predictions')
 call([ROOT/'audits/state_models/gls_repair.py','evaluate'],'fgls_predictions')
 call([ROOT/'experiments/placebo.py'],'preindex_placebo')
 if full:
  call([ROOT/'experiments/recovery.py','--reps','300'],'recovery')
  call([ROOT/'experiments/recovery_slow_null.py'],'slow_null_recovery')
  call([ROOT/'audits/recovery_design/oracle.py'],'oracle')
  call([ROOT/'audits/transfer_check/recovery.py'],'transfer_recovery')
  call([ROOT/'experiments/state_models.py','stress','--reps','100','--altreps','50'],'state_stress')
  call([ROOT/'experiments/state_models.py','bootstrap','--reps','200'],'state_bootstrap')
  call([ROOT/'audits/state_models/gls_repair.py','recovery','--reps','100','--scope','core'],'fgls_recovery')
 call([ROOT/'experiments/figures_tables.py'],'figures')
 comparisons={}
 for name,b in before.items():
  a=json.loads((ROOT/'outputs'/name).read_text())
  if name.startswith('validation'):comparisons[name]=float(abs(a['pooled']['estimate']-b['pooled']['estimate']))
  else:comparisons[name]=float(max(abs(a[k]['summary']['estimate']-b[k]['summary']['estimate']) for k in ['all','stationary']))
 assert all(v<1e-10 for v in comparisons.values()),comparisons
 result={'status':'passed','offline':True,'source_hashes_verified':5,'frozen_files_verified':len(frozen['files_sha256']),'decisive_estimate_max_abs_changes':comparisons,'elapsed_seconds':time.time()-started,'full_simulations':full}
 (ROOT/'outputs/offline_reproduction_check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--full',action='store_true');main(ap.parse_args().full)
