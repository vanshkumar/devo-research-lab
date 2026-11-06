"""Sequential offline reproduction of the bounded campaign. --fetch only gets public inputs."""
import argparse,hashlib,json,os,pathlib,platform,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--fetch',action='store_true');a=p.parse_args()
logdir=ROOT/'experiments/reproduction';logdir.mkdir(exist_ok=True)
env=os.environ.copy();env['MPLCONFIGDIR']=str(ROOT/'.mplconfig');env['OPENBLAS_NUM_THREADS']='1'
steps=[]
if a.fetch:steps += [('fetch_worm',['neural_dynamics/acquire.py','--part','discovery']),('fetch_fly',['social_learning/acquire.py'])]
else:
 # These calls are cache-only if data exist; explicit prechecks prevent accidental network.
 assert len(list((ROOT/'data/public').glob('*.json')))==7,'Expected six worm files plus manifest'
 assert (ROOT/'data/social_learning/data_primacy.csv').exists() and (ROOT/'data/social_learning/primacy_bias_script.Rmd').exists()
 steps += [('verify_worm',['neural_dynamics/acquire.py','--part','discovery']),('verify_fly',['social_learning/acquire.py'])]
steps += [
('neural_controls',['neural_dynamics/run.py','--part','controls']),('neural_discovery',['neural_dynamics/run.py','--part','discovery']),
('local_main',['local_learning/run_pilots.py']),('local_sensitivity',['local_learning/run_pilots.py','--followup']),('local_analytic',['local_learning/analytical_check.py']),
('development',['development/run.py']),('development_analytic',['development/audit.py']),
('causal',['causal_identification/run.py']),('neural_adversarial',['causal_identification/neural_audit_check.py']),
('social',['social_learning/run.py']),('social_independent',['social_learning/audit_reconstruct.py']),('social_followup',['social_learning/followup.py']),
('social_figure',['social_learning/plot.py']),('local_figure',['local_learning/make_figure.py']),('causal_figure',['causal_identification/plot.py'])]
records=[]
for name,args in steps:
 start=time.monotonic();cmd=[sys.executable,str(ROOT/'experiments'/args[0]),*args[1:]]
 with (logdir/(name+'.log')).open('w') as out,(logdir/(name+'.stderr')).open('w') as err:
  r=subprocess.run(cmd,cwd=ROOT,env=env,stdout=out,stderr=err)
 record=dict(step=name,command=[str(pathlib.Path(sys.executable)),str(pathlib.Path('experiments')/args[0]),*args[1:]],returncode=r.returncode,seconds=time.monotonic()-start)
 records.append(record);(logdir/'execution.json').write_text(json.dumps(dict(python=platform.python_version(),platform=platform.platform(),steps=records),indent=2)+'\n')
 print(name,'PASS' if r.returncode==0 else 'FAIL',f"{record['seconds']:.2f}s",flush=True)
 if r.returncode:raise SystemExit(r.returncode)
# Semantic checks of the central evidence, in addition to scripts' known-effect controls.
s=json.loads((ROOT/'experiments/social_learning/summary.json').read_text())
assert [(x['treatment'],x['eligible']) for x in s['counts']]==[('T',64),('C1',74),('C2',67)]
z=json.loads((ROOT/'experiments/social_learning/followup_summary.json').read_text())
assert z['regressions']['archived_script_all']['n']==452
assert z['regressions']['eligible_last_single']['n']==205
assert z['controls']['zero_sd_nll_error']<1e-10
assert all(r['quadrature_max_beta_difference']<1e-4 for r in z['regressions'].values())
for ext in ['png','svg']:assert (ROOT/f'experiments/social_learning/social_learning.{ext}').stat().st_size>1000
print('CENTRAL_EVIDENCE_CHECKS PASS',flush=True)
