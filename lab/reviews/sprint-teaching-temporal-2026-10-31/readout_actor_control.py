"""One frozen normalized-readout duration actor control, no circuit learning."""
import os,sys
sys.dont_write_bytecode=True
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[name]='2'
import datetime as dt,hashlib,io,json,time,resource
import numpy as np
from audit_common import HERE,PILOT,SNAP,CACHE,read,j,npz,save
from dynamics_audit import LocalUnpickler,features,stimulus,waveform_error,reset,integrate

def actor(callback):
    x=.8;cost=callback(x);step=.05;path=[x];values=[cost];queries=[{'duration':x,'score':cost}]
    for iteration in range(12):
        proposals=[float(np.clip(x+sign*step,.7,1.2)) for sign in (-1,1)]
        scores=[callback(v) for v in proposals]
        queries.extend({'duration':v,'score':c} for v,c in zip(proposals,scores));k=int(np.argmin(scores))
        if scores[k]<cost:x=proposals[k];cost=scores[k]
        else:step=max(.00625,step/2)
        path.append(x);values.append(cost)
    return {'durations':path,'scores':values,'queries':queries,'logical_actor_queries':len(queries)}

def main():
    assert not (HERE/'READOUT_ACTOR_RESULTS.json').exists(),'one normalized actor control'
    save('READOUT_ACTOR_FREEZE.json',{'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'code_sha256':hashlib.sha256(__import__('pathlib').Path(__file__).read_bytes()).hexdigest(),
        'amendment_sha256':hashlib.sha256((HERE/'READOUT_CONTROL_AMENDMENT.md').read_bytes()).hexdigest(),
        'actor_is_duration_only':True,'new_synaptic_learning':False,'new_plants':False,'queries_per_actor':25,'calibration_slots':1})
    t0=time.monotonic();rows=[];checks=[]
    manifest=j(PILOT/'MANIFEST.json');pins={r['path']:r for r in manifest['artifacts']}
    def load(path):
        raw=read(path,'readout_control_cached_synthetic_state')
        expected=pins[str(path.relative_to(HERE.parents[2]))]
        assert hashlib.sha256(raw).hexdigest()==expected['sha256'],'cached state changed'
        return LocalUnpickler(io.BytesIO(raw)).load()
    for plant in (100,101,102):
        state=load(SNAP/('plant_%03d/state.pkl'%plant));net=load(CACHE/('noclock_%03d.pkl'%plant))['net']
        inp=npz(SNAP/('plant_%03d/inputs.npz'%plant));source=npz(PILOT/('outputs/teaching_%03d_no_clock_per_order_20.npz'%plant))
        y=features(source['actions'][-1,:4],inp['basis'],inp['bias']);teacher=features(inp['target'],inp['basis'],inp['bias'])
        hE,hI=reset(net,state,'zero');zero=np.zeros((2000,600));rh=np.zeros((2000,15));baseline=integrate(net,hE,hI,zero,rh)[0]
        cache={};physical=1
        def evaluate(duration):
            nonlocal physical
            key=float(duration)
            if key not in cache:
                traces=[];actives=[]
                for phase in (-60,60):
                    aud=stimulus(y,inp['on'],inp['off'],phase,duration,length=2000)
                    traces.append(integrate(net,hE,hI,aud,rh)[0]);actives.append(int(np.sum(np.any(aud!=0,axis=1))));physical+=1
                raw=float(np.mean([r.mean() for r in traces]));normalized=float(np.mean([(r-baseline).sum()/n for r,n in zip(traces,actives)]))
                cache[key]={'raw':raw,'normalized':normalized,'active_ms':actives[0]}
            return cache[key]
        normalized=actor(lambda d:evaluate(d)['normalized'])
        raw_actor=actor(lambda d:evaluate(d)['raw'])
        oracle=actor(lambda d:waveform_error(y,teacher,inp['on'],inp['off'],d))
        # Evaluation follows all actor choices. No gold enters circuit callbacks.
        for result in (normalized,raw_actor):result['offline_waveform_MSE']=[waveform_error(y,teacher,inp['on'],inp['off'],d) for d in result['durations']]
        check={'plant':plant,'raw_actor_reproduces_shortening':raw_actor['durations'][-1]==.7,
               'oracle_reaches_unit_duration':abs(oracle['durations'][-1]-1)<1e-12,
               'all_actors_exact25queries':all(r['logical_actor_queries']==25 for r in (normalized,raw_actor,oracle))}
        checks.append(check)
        row={'plant':plant,'normalized_actor':normalized,'raw_actor':raw_actor,'waveform_oracle':oracle,
             'cached_duration_scores':[{'duration':d,**r} for d,r in sorted(cache.items())],
             'baseline_mean_Hz':float(baseline.mean()),'quiet_calibration_logical_slots':1,'physical_integrations_including_calibration':physical,
             'scope':'Frozen no-clock critic; learned content/correct order held fixed; scalar duration control only.'}
        rows.append(row);save('READOUT_ACTOR_PARTIAL.json',{'plants':rows,'checks':checks})
        print(json.dumps({'plant':plant,'normalized_end':normalized['durations'][-1],'raw_end':raw_actor['durations'][-1],
                         'oracle_end':oracle['durations'][-1],'normalized_final_gold':normalized['offline_waveform_MSE'][-1]}),flush=True)
    save('READOUT_ACTOR_RESULTS.json',{'plants':rows,'checks':checks,'elapsed_seconds':time.monotonic()-t0,
        'maxrss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'all_control_checks_passed':all(all(v for k,v in r.items() if k!='plant') for r in checks)})

if __name__=='__main__':main()
