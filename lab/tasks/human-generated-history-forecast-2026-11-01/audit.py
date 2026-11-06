"""Independent scalar score/mask audit and exact uncertain-omission reference."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
import sys
sys.dont_write_bytecode=True
import hashlib, io, itertools, json, math, resource, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import betaln

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
CAMP=ROOT/'campaigns/human_learning_routes_2026-10-28'
sys.path.insert(0,str(HERE)); import forward
sys.path.insert(0,str(CAMP/'experiments')); from analysis import attach_split,windows

def main():
    start=time.monotonic(); pins=[]
    def read(p):
        b=p.read_bytes(); pins.append(dict(path=str(p.relative_to(ROOT)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),charge=3*len(b))); return b
    inputs=json.loads(read(HERE/'FORECAST_INPUTS.json')); fits={v:json.loads(read(CAMP/f'outputs/primary/{v}_fit.json')) for v in ('shared','no_history')}
    scores=json.loads(read(HERE/'SCORES.json')); meta=json.loads(read(HERE/'FORECAST_META.json'))
    rawforecast=read(HERE/'FORECASTS.npz'); assert hashlib.sha256(rawforecast).hexdigest()==meta['forecasts_sha256']
    arrays=dict(np.load(io.BytesIO(rawforecast))); people=inputs['people']
    cached=pd.read_csv(io.BytesIO(read(CAMP/'inputs/validation_numeric.csv')),dtype={'subject':str,'session':str})
    # The inspected original source functions reconstruct mask from original
    # cached input labels, independently of forward.py's XLSX-based mask.
    w=windows(attach_split(cached)); splitpath=CAMP/'protocol/split_manifest.csv'
    pins.append(dict(path=str(splitpath.relative_to(ROOT)),bytes=splitpath.stat().st_size,charge=3*splitpath.stat().st_size,note='original attach_split read'))
    saved=pd.read_csv(io.BytesIO(read(HERE/'PERSON_SCORES.csv')),dtype={'subject':str})
    scalar_checks={}; masks=[]
    for person in people:
        s=w.loc[(w.subject==person['subject']) & w.trial.ge(200)].sort_values('trial')
        from_source=s.primary.to_numpy(); from_xlsx=forward.windows(person)[0]
        assert np.array_equal(from_source,from_xlsx)
        masks.append(s.primary_responded.to_numpy())
    for label,a in arrays.items():
        p=a.mean(axis=0) if a.ndim==4 else a; per=[]; person_error=[]
        for i,person in enumerate(people):
            s=w.loc[(w.subject==person['subject']) & w.trial.ge(200)].sort_values('trial')
            values=[]
            for j,row in enumerate(s.itertuples(index=False)):
                if not row.primary_responded: continue
                ps,pb=map(float,p[i,j])
                values.append(math.log(ps/pb) if row.choice==1 else math.log((1-ps)/(1-pb)))
            val=math.fsum(values)/len(values); per.append(val)
            original=float(saved.loc[(saved.subject==person['subject']) & (saved.setting==label),'gain_nat'].iloc[0])
            person_error.append(abs(original-val))
        gain=math.fsum(per)/len(per)
        error=abs(gain-scores['settings'][label]['primary']['mean'])
        assert error<1e-13 and max(person_error)<1e-13
        scalar_checks[label]=dict(equal_person_gain=gain,mean_error=error,max_person_error=max(person_error))
    # An intentionally difficult known-answer observation law tests posterior
    # response selection, not a second empirical calibration or replacement law.
    person=people[0]; states=[forward.setup(fits[v],person) for v in ('shared','no_history')]
    alpha=beta=.5; steps=4; exact=np.zeros((steps,2)); denominators=np.zeros(steps); total_mass=[]
    for v,s in enumerate(states):
        numer=np.zeros(steps); denom=np.zeros(steps); mass=0.
        for path in itertools.product((-1,0,1),repeat=steps):
            h=s['h'].copy(); previous=s['previous']; choice_likelihood=1.
            for t,choice in enumerate(path):
                pp=forward.scalar_prob(s,t,h,previous)
                if choice: choice_likelihood*=pp if choice==1 else 1-pp
                h=forward.DECAY*h+(1-forward.DECAY)*(s['side'][t] if choice else 0.)
                previous=float(choice)
            omissions=path.count(0); responses=steps-omissions
            weight=choice_likelihood*math.exp(float(betaln(alpha+omissions,beta+responses)-betaln(alpha,beta)))
            mass+=weight
            for t,choice in enumerate(path):
                numer[t]+=weight*(choice==1); denom[t]+=weight*(choice!=0)
        exact[:,v]=numer/denom; total_mass.append(mass)
        assert abs(mass-1)<1e-12 and np.max(abs(denom-.5))<1e-12
    calibration=dict(alpha=alpha,beta=beta,mean=.5)
    reps=np.array([forward.particles(states,calibration,0,100+r,0,n=131072,steps=4)[0] for r in range(8)])
    error=reps.mean(axis=0)-exact; se=reps.std(axis=0,ddof=1)/np.sqrt(8)
    assert np.all(abs(error)<6*se+1e-4)
    # A coarser no-response-conditioning average would be a different target;
    # the exact denominator above verifies current-response conditioning.
    contribution={'source_omission_law':inputs['omission_law'],'teacher_law':inputs['teacher_law'],
                  'main_minus_exact_no_omission_gain':scores['settings']['main']['primary']['mean']-scores['settings']['no_omission']['primary']['mean'],
                  'all_schedule_point_gains_positive':all(x['mean']>0 for x in scores['settings']['main']['schedules'].values()),
                  'historical_conditional_point_gain':.03396,'historical_comparison_note':'Rounded saved conditional result, different conditioning. Near-equality is descriptive, not a matched causal decomposition or new precision bound.'}
    prior_runs={}
    for stage in ('checks','freeze','forecast','score'):
        prior_runs[stage]=json.loads(read(HERE/f'RUN_{stage}.json'))
    out=dict(utc=datetime.now(timezone.utc).isoformat(),all_pass=True,original_cached_input_mask_agreement=True,primary_responding=int(np.sum(masks)),scalar_score_checks=scalar_checks,
             exact_beta_omission_reference=dict(alpha=alpha,beta=beta,paths=81,steps=4,total_path_mass=total_mass,conditional_left_probabilities=exact.tolist(),particle_mean=reps.mean(axis=0).tolist(),max_absolute_error=float(np.max(abs(error))),max_mcse=float(np.max(se)),reps=8,particles_per_rep=131072,scope='Constructed high-uncertainty law; no empirical refit or changed main forecast.'),
             contribution_limits=contribution,forecast_before_score=meta['utc']<scores['utc'],unchanged_forecast_hash=meta['forecasts_sha256'],
             pins=pins,explicit_read_hash_decode_charge=sum(x['charge'] for x in pins),
             prior_run_explicit_charge={k:x['explicit_read_hash_decode_charge'] for k,x in prior_runs.items()},
             prior_run_peak_rss={k:x['peak_rss_bytes'] for k,x in prior_runs.items()},
             wall_seconds=time.monotonic()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,physical_io='unknown',runtime_host_peak='unknown')
    (HERE/'FINAL_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('utc','all_pass','scalar_score_checks','exact_beta_omission_reference','contribution_limits','explicit_read_hash_decode_charge','prior_run_explicit_charge','prior_run_peak_rss','wall_seconds','peak_rss_bytes')},indent=2))

if __name__=='__main__': main()
