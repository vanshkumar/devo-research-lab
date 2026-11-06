"""Bounded long-memory null challenge on reserved INPUT schedules only.

Keeps the frozen primary estimator/operators unchanged. No validation outcome
access and no modification of the original 3,900-replicate recovery artifacts.
"""
from pathlib import Path
import json,hashlib,time,argparse
import numpy as np
from analysis import load,ROOT,jsonable
from recovery import build_operators,estimate,summarize
from generators import generate


def run(reps=300):
    started=time.time();people=load('validation',inputs_only=True);op=build_operators(people,.03)
    reference=[]
    for p in people:
        rr=generate(p['c'],p['j'],kind='two_timescale',retentions=(.65,.995),gains=(.65,.30),noise_sd=0,drift_scale=0)
        direct=.035*p['j']-.025*p['c'];reference.append((rr['clean'],direct))
    result=dict(scope='Reserved INPUTS only; fixed original primary operators. No empirical validation outcomes read.',
                retentions=[.65,.995],gains=[.65,.30],endpoint_noise_sd=3.,
                omissions='Original fixed 3% independent mask, seed194192; full chronological updates retained.',
                heterogeneity='Gain log SD.20; noise log SD.15; same seeds for both drift scenarios.',
                process_sd=.08,replicates=reps,seed=892034,
                analysis_sha256=hashlib.sha256((ROOT/'experiments/analysis.py').read_bytes()).hexdigest(),scenarios={})
    for drift in [.6,3.]:
        rng=np.random.default_rng(892034);rows=[]
        for rep in range(reps):
            scales=np.exp(.2*rng.normal(size=20)-.5*.2**2)
            noise_scales=np.exp(.15*rng.normal(size=20)-.5*.15**2)
            ys=[];means=[]
            for i,p in enumerate(people):
                g=generate(p['c'],p['j'],seed=902034+rep*20+i,kind='two_timescale',
                           retentions=(.65,.995),gains=(.65,.30),noise_sd=3*noise_scales[i],
                           person_scale=scales[i],drift_scale=drift,process_sd=.08,
                           empirical_mask=op['masks'][p['key']])
                ys.append(g['y']);ref,direct=reference[i];means.append(scales[i]*(ref-direct)+direct)
            e=estimate(op,np.array(ys));projection=estimate(op,np.array(means))['estimate']
            rows.append(dict(rep=rep,truth=0.,noiseless_projection=projection,structural_curve=[0.]*5,**e))
        name='drift_'+str(drift)
        (ROOT/'outputs'/('recovery_slow_null_'+name+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
        result['scenarios'][name]=summarize(rows)
        print(name,json.dumps(result['scenarios'][name]),flush=True)
    result['seconds']=time.time()-started
    (ROOT/'outputs/recovery_slow_null_summary.json').write_text(json.dumps(jsonable(result),indent=2)+'\n')
    return result
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--reps',type=int,default=300);a=ap.parse_args();run(a.reps)
