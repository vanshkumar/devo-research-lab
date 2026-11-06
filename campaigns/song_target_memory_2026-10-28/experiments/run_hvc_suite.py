from pathlib import Path
import concurrent.futures,json,subprocess,sys,time
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'outputs'/'hvc';LOG=BASE/'logs'/'hvc_suite';LOG.mkdir(exist_ok=True)
jobs=[]
for seed in range(1,7):
 for period in [0,10]:jobs.append(dict(seed=seed,period=period,mode='source'))
for seed in range(1,7):
 for period in [10,20,40]:jobs.append(dict(seed=seed,period=period,mode='matched'))
for param,scales in [('eta-scale',[0.,.5,2.]),('tau-scale',[.75,1.25])]:
 for scale in scales:
  for period in [0,10]:jobs.append(dict(seed=1,period=period,mode='source',**{param:scale}))

def task(j):
    tag='_'.join(f'{k}{v}' for k,v in j.items())
    cmd=[sys.executable,str(BASE/'experiments'/'hvc_model.py')]
    for k,v in j.items():cmd += ['--'+k,str(v)]
    started=time.monotonic()
    with (LOG/(tag+'.stdout')).open('w') as out,(LOG/(tag+'.stderr')).open('w') as err:
        p=subprocess.run(cmd,stdout=out,stderr=err)
    z={'job':j,'returncode':p.returncode,'elapsed_seconds':time.monotonic()-started,'command':cmd}
    print(json.dumps(z),flush=True);return z

if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
    results=list(ex.map(task,jobs))
 (OUT/'suite_execution.json').write_text(json.dumps(results,indent=2)+'\n')
 if any(r['returncode'] for r in results):sys.exit(1)
