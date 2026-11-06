"""Released fixed main and32 finite source perturbations; no scoring-based tuning."""
import time,resource
BEGIN=time.monotonic();CPU=time.process_time()
import io,json,hashlib,sys,platform
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import numpy as np
import scipy,numba
import source_models as sm
from source_models import inherited as e
import main_simulator as ms
from rnn_learning import load_rnn
from pilot import subject

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];DEV=sm.DEVELOPMENT
OLD=ROOT/'campaigns/learning_rule_transport_2026-10-28'
IO=Counter();PINS={};TIMES={};CURRENT='initializing'
CONDITIONS=['primary','source_context_input','source_calibrated_engagement']
NAMES=['growth','recent100','recent250','gru'];CUTOFFS=[200,1000];STREAMS=[0,10000019]


def utc():return datetime.now(timezone.utc).isoformat()
def serial(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)
def save(name,x):
    path=HERE/name;temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(x,indent=2,allow_nan=False,default=serial)+'\n');temp.replace(path)
def read(path,pin=None):
    b=path.read_bytes();IO['explicit_read_bytes']+=len(b);h=hashlib.sha256(b).hexdigest()
    PINS[str(path.relative_to(ROOT))]=h
    if pin is not None:assert h==pin,str(path)
    return b
def get(path,pin=None):return json.loads(read(path,pin))
def arrays(path,pin=None):
    with np.load(io.BytesIO(read(path,pin)),allow_pickle=False) as z:out={k:z[k] for k in z.files}
    IO['decoded_array_bytes']+=sum(v.nbytes for v in out.values());return out
def stamp(name,t):TIMES[name]=dict(wall_seconds=time.monotonic()-t[0],cpu_seconds=time.process_time()-t[1])
def clock():return time.monotonic(),time.process_time()
def ledger(status):
    save('MAIN_EXECUTION.json',dict(utc=utc(),status=status,current=CURRENT,
         scientific_cpu_seconds=time.process_time()-CPU,process_wall_seconds=time.monotonic()-BEGIN,
         io=dict(IO),explicit_read_decode_bytes=sum(IO.values()),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         timings=TIMES,pins=PINS,physical_io='unknown',import_provider_runtime_reads='unknown',
         prior_stage='Stage1 CPU121.991771/read-decode25,634,256 plus separate15MB estimated context charge; all older costs remain',
         ceilings=dict(cpu_seconds=8100,read_decode_bytes=800000000,elapsed_seconds=10800)))
def budget():
    if time.process_time()-CPU>7800:raise RuntimeError('Main CPU safety stop preserving300seconds for checkpoint/reduction')
    if time.monotonic()-BEGIN>10200:raise RuntimeError('Main process wall stop preserving600seconds for closeout')
    if sum(IO.values())>700000000:raise RuntimeError('Main explicit-read stop preserving read/reduction allowance')
def atomic_npz(name,**kwargs):
    path=HERE/name;tmp=path.with_suffix('.tmp.npz');np.savez_compressed(tmp,**kwargs);tmp.replace(path)


def main():
    global CURRENT
    release=get(HERE/'STAGE2_START.json');assert release['same_goal_no_reset']
    read(HERE/'MAIN_FREEZE.md');read(HERE/'AMENDMENT_SCOPE.md');read(HERE/'BRIEF.md')
    prep=get(DEV/'PREPARATION.json');manifest=prep['eval_source_manifest']
    assert manifest['maximum_rows_per_animal']==4000 and len(manifest['subjects'])==64
    sessions=manifest['sessions']
    for s in manifest['subjects']:
        rows=sorted([z for z in sessions if z['subject']==s],key=lambda z:z['start'])
        assert rows[0]['start']==0 and all(z['stop']<=4000 and z['stop']>z['start'] for z in rows)
        assert all(a['stop']==b['start'] for a,b in zip(rows[:-1],rows[1:]))
        assert all(z.get('provenance_utc') for z in rows)
    source_manifest=get(DEV/'SOURCE_FIT6000_MANIFEST.json','33365f4725bd3f398f6f8a9e0b9de8ff85bbdd1bd192dbf1daa0ece1748cb585')
    save('MAIN_ACCESS.json',dict(utc=utc(),authority='PI Stage2 release in BRIEF and native release, same active goal',
         source_fields=manifest['fields'],evaluation_cap=4000,target_end=3000,
         evaluation_subjects=manifest['subjects'],site_ledger=dict(zip(manifest['subjects'],manifest['labs'])),
         evaluation_sessions=sessions,prior_consumed_scope=True,source_fit_cap=6000,
         forbidden='Pan/Flesch/laterHABITS/memorytargets/reservedworms/otherprotected objects unchanged',
         only_certified_cache_decode=True,pins=PINS.copy()))
    raw=arrays(DEV/'TRAIN6000_ROWS.npz','71b837ea55cd6363db65d2c4ca15b7ceec1309b5dc5d972b8b85407851592049')
    ev=arrays(HERE.parent/'acquisition-reactive-sequence-2026-11-04/CAPPED_ROWS.npz','a417bbff6c989495b1fbba77777ce09b2939794b7e4016ca63105d828ea99b80')
    ids=list(ev);labs=dict(zip(manifest['subjects'],manifest['labs']))
    assert ids==manifest['subjects']
    for s,a in ev.items():
        length=sum(z['stop']-z['start'] for z in sessions if z['subject']==s)
        assert len(a)==length and 3000<=len(a)<=4000
    split=get(OLD/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json','1ebd21840771d2b101a80ee9912615075f7a99d55520e5cfe35bc4d95fbc6d10')
    assert not set(ids)&set(split['train']+split['validation'])
    source_labs={s:source_manifest['disposition'][s]['lab'] for s in raw}
    canonical={c:arrays(HERE/f'SOURCE_CANONICAL_BANK_{c}.npz') for c in CUTOFFS}
    banks={key:{c:arrays(HERE/f'SOURCE_RECENT_BANK_{key}_{c}.npz') for c in CUTOFFS} for key in ('100','250','500','infinity')}
    input_fit=arrays(HERE/'SOURCE_INPUT_FIT.npz');input_fit['sites']=input_fit['sites'].tolist()
    engagement={int(k):v for k,v in get(HERE/'SOURCE_ENGAGEMENT_FIT.json').items()}
    selection=get(HERE/'SOURCE_SELECTION.json');assert selection['chosen']=='100'
    modelpath=OLD/'artifacts/rnn/rnnglm32_nested_best.npz'
    read(modelpath,'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940')
    IO['explicit_read_bytes']+=modelpath.stat().st_size;model=load_rnn(modelpath)
    IO['decoded_model_bytes']+=sum(v.nbytes for v in model.params.values() if isinstance(v,np.ndarray))
    observed=np.stack([e.observed(ev[s]) for s in ids])
    assert (observed[:,:,[0,2]]>0).all()
    atomic_npz('MAIN_OBSERVED.npz',observed=observed,subjects=ids,labs=[labs[s] for s in ids],
               cohort=['old40']*40+['later24']*24,windows=[500,2000],columns=['N_left','K_left','N_right','K_right','omissions','choice_negative','literal_feedback_success'])
    save('MAIN_RUN_FREEZE.json',dict(utc=utc(),pins=PINS.copy(),subjects=ids,labs=labs,
         cutoffs=CUTOFFS,windows=[500,2000],conditions=CONDITIONS,names=NAMES,stream_offsets=STREAMS,
         particles_per_stream=256,exact_prefix_particles=256,source_draws=32,source_particles=256,
         versions=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,numba=numba.__version__,platform=platform.platform()),
         data_information='each simulator receives prefix values and future session flags only, all other future fields physicallyNaN'))
    chunks=HERE/'main_chunks';chunks.mkdir(exist_ok=True)
    t=clock();reference=[];nonlinear=[]
    linear_cache={};exact_cache={}
    samples=np.empty((64,3,2,4,2,256,2,7),np.int32)
    exact_samples=np.empty((64,3,2,256,2,7),np.int32)
    omission_moments=np.empty((64,3,2,4,2,40,3),float)
    for i,s in enumerate(ids):
        CURRENT='fixed animal '+str(i+1)+'/64 '+s
        a=ev[s]
        for ci,c in enumerate(CUTOFFS):
            view=ms.causal_view(a,c)
            for streamindex,offset in enumerate(STREAMS):
                state,info=ms.initial_neural(model,view,c,256,e.original_seed(s)+offset)
                linear_cache[s,c,offset]=state
                if offset==0:
                    xt=time.process_time();exact=ms.exact_initial_neural(model,view,c,256,e.original_seed(s),info)
                    exact_cache[s,c]=exact
                    error=np.array([np.abs(model.probs(state,np.full(256,x))-model.probs(exact,np.full(256,x)))
                                    for x in (-1,-.5,-.25,-.125,-.0625,0,.0625,.125,.25,.5,1)])
                    nonlinear.append(dict(subject=s,cutoff=c,exact_cpu_seconds=time.process_time()-xt,
                         mean_probability_error=float(error.mean()),max_probability_error=float(error.max()),info=info))
                for k,condition in enumerate(CONDITIONS):
                    for ni,name in enumerate(NAMES):
                        actor='recent_growth' if name.startswith('recent') else name
                        half=float(name[6:]) if actor=='recent_growth' else None
                        bank=banks[str(int(half))][c] if half is not None else None
                        sample,block=ms.simulate(s,view,c,actor,model,canonical[c],bank,half,n=256,
                             condition=condition,input_fit=input_fit,lab=labs[s],engagement_fit=engagement,
                             stream_offset=offset,neural_state=state if actor=='gru' else None)
                        samples[i,k,ci,ni,streamindex]=sample
                        omission_moments[i,k,ci,ni,streamindex]=np.stack([block.mean(0),np.mean(block**2,axis=0),np.quantile(block,.9,axis=0)],axis=-1)
                        if i==0 and condition=='primary' and offset==0 and name in ('growth','recent100','gru'):
                            inherited,_=e.simulate(s,view,c,actor,model,canonical[c],bank,half,n=256)
                            assert np.array_equal(sample,inherited)
                            reference.append(dict(subject=s,cutoff=c,model=name,max_count_difference=0))
                    if offset==0:
                        xsample,_=ms.simulate(s,view,c,'gru',model,canonical[c],n=256,condition=condition,
                             input_fit=input_fit,lab=labs[s],engagement_fit=engagement,neural_state=exact_cache[s,c])
                        exact_samples[i,k,ci]=xsample
        atomic_npz('main_chunks/'+s+'.npz',samples=samples[i],exact_samples=exact_samples[i],omission_moments=omission_moments[i])
        if (i+1)%4==0:
            print('FIXED',i+1,'/64 CPU',round(time.process_time()-CPU,2),'wall',round(time.monotonic()-BEGIN,2),flush=True)
            ledger('running');budget()
    atomic_npz('MAIN_COUNTS.npz',samples=samples,exact_samples=exact_samples,omission_moments=omission_moments,
              subjects=ids,names=NAMES,conditions=CONDITIONS,cutoffs=CUTOFFS,windows=[500,2000],stream_offsets=STREAMS)
    stamp('fixed_three_conditions_two_streams_plus_exact',t)
    save('MAIN_INITIALIZATION.json',dict(utc=utc(),reference=reference,nonlinear=nonlinear,
         frozen_weight_and_original_fisher_uncertainty=True,exact_transport='same W0 draws, actual nonlinear observed prefix, no extra free hidden parameters'))
    ledger('fixed forecasts complete; source propagation follows')
    # New simulator future-poison/reference audit, using the hash-first evaluation animal.
    t=clock();s=sorted(ids,key=lambda x:hashlib.sha256(x.encode()).hexdigest())[0];poison=[]
    for c in CUTOFFS:
        view=ms.causal_view(ev[s],c)
        altered=ev[s].copy();altered[c:,:6]=np.nan
        assert np.array_equal(view,altered[:3000],equal_nan=True)
        for condition in CONDITIONS:
            for name in ('growth','recent_growth','gru'):
                kwargs=dict(s=s,cutoff=c,name=name,model=model,canonical=canonical[c],candidate=banks['100'][c],half=100.,n=16,
                            condition=condition,input_fit=input_fit,lab=labs[s],engagement_fit=engagement)
                expected,_,_=sm.simulate(s,ev[s],c,name,model,canonical[c],banks['100'][c],100.,n=16,
                     condition=condition,input_fit=input_fit,lab=labs[s],engagement_fit=engagement)
                actual,_=ms.simulate(a=view,**kwargs)
                assert np.array_equal(expected,actual)
                poison.append(dict(subject=s,cutoff=c,condition=condition,actor=name,identical=True))
    save('MAIN_CHRONOLOGY.json',dict(utc=utc(),poison=poison,
         invariant_by_interface='future values replaced physicallyNaN at all simulator calls; only real session flags survive',
         all64_reference_scope='first actual evaluation subject matches inherited primary counts at both cutoffs/allthreeactors'))
    stamp('main_chronology',t);budget()
    # Whole-source perturbations; unchanged neural trajectories are reused by analysis.
    donors=list(canonical[1000]['subjects']);validation=[s for s in split['validation'] if len(raw[s])>=3000]
    source_samples=np.empty((32,64,2,2,256,2,7),np.int32);source_records=[]
    (HERE/'source_chunks').mkdir(exist_ok=True)
    def site_mean(rows):
        sites=sorted({source_labs[s] for s,_ in rows})
        return float(np.mean([np.mean([v for s,v in rows if source_labs[s]==lab]) for lab in sites]))
    t=clock()
    for j in range(32):
        CURRENT='source draw '+str(j+1)+'/32';drawbegin=clock();rng=np.random.default_rng(20261105041+j)
        def resample(units):
            out=[]
            for lab in sorted({source_labs[s] for s in units}):
                group=[s for s in units if source_labs[s]==lab]
                out+=list(rng.choice(group,len(group),replace=True))
            return out
        dd=resample(donors);ds=resample(validation)
        cb={c:e.bank_at(raw,dd,c) for c in CUTOFFS}
        bb={key:{c:e.bank_at(raw,dd,c,h) for c in CUTOFFS}
            for key,h in [('100',100.),('250',250.),('500',500.),('infinity',np.inf)]}
        ranking={};cv={};selection_start=clock()
        if j==0:
            prior=get(HERE/'SOURCE_ONE_RESAMPLE.json');assert prior['donors']==dd and prior['selection']==ds
            ranking=prior['ranking'];cv=prior['cv'];chosen=prior['chosen'];selection_reused=True
        else:
            for key in ('100','250','500','infinity'):
                cv[key]={}
                h=np.inf if key=='infinity' else float(key)
                for c in CUTOFFS:
                    cache={};rows=[]
                    for s in ds:
                        if s not in cache:
                            sample,_=ms.simulate(s,ms.causal_view(raw[s],c),c,'recent_growth',None,cb[c],bb[key][c],h,n=128)
                            cache[s]=e.score_window(sample[:,1],e.observed(raw[s])[1],2000)['mixed_ratio_score']
                        rows.append((s,cache[s]))
                    cv[key][str(c)]=dict(equal_site=site_mean(rows),per_animal=[dict(subject=s,score=v,lab=source_labs[s]) for s,v in rows])
                ranking[key]=float(np.mean([cv[key][str(c)]['equal_site'] for c in CUTOFFS]))
            chosen=min(ranking,key=ranking.get);selection_reused=False
        select_cpu=time.process_time()-selection_start[1]
        h=np.inf if chosen=='infinity' else float(chosen);forecaststart=clock()
        for i,s in enumerate(ids):
            for ci,c in enumerate(CUTOFFS):
                view=ms.causal_view(ev[s],c)
                for ni,name in enumerate(('growth','recent_growth')):
                    sample,_=ms.simulate(s,view,c,name,None,cb[c],bb[chosen][c],h,n=256)
                    source_samples[j,i,ci,ni]=sample
        record=dict(draw=j,seed=20261105041+j,donors=dd,selection=ds,chosen=chosen,ranking=ranking,cv=cv,
             source_selection_reused_from_stage1=selection_reused,source_selection_cpu_seconds=select_cpu,
             dependent_forecast_cpu_seconds=time.process_time()-forecaststart[1],
             total_cpu_seconds=time.process_time()-drawbegin[1],no_neural_refit_or_reforecast=True)
        source_records.append(record)
        atomic_npz(f'source_chunks/draw_{j:02d}.npz',samples=source_samples[j],subjects=ids,
                   names=['growth','recent_growth'],cutoffs=CUTOFFS,windows=[500,2000])
        save('MAIN_SOURCE_DRAWS.json',dict(utc=utc(),draws=source_records,scope='Finite conditional source envelope, not95% source-tail CI; same original eligibility and site mixture'))
        print('SOURCE',j+1,'/32 chosen',chosen,'drawCPU',round(record['total_cpu_seconds'],2),'totalCPU',round(time.process_time()-CPU,2),flush=True)
        ledger('running');budget()
    atomic_npz('MAIN_SOURCE_COUNTS.npz',samples=source_samples,subjects=ids,names=['growth','recent_growth'],cutoffs=CUTOFFS,windows=[500,2000])
    stamp('source32_reselection_and_dependent_forecasts',t)
    CURRENT='all fixed and source forecasts completed';ledger('complete')
    print('MAIN SIMULATION COMPLETE CPU',time.process_time()-CPU,'wall',time.monotonic()-BEGIN,flush=True)


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        save('MAIN_FAILURE_'+utc().replace(':','-')+'.json',dict(utc=utc(),error=repr(exc),current=CURRENT,
             scientific_cpu_seconds=time.process_time()-CPU,process_wall_seconds=time.monotonic()-BEGIN,
             io=dict(IO),pins=PINS,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        ledger('failed; preserve completed chunks and cumulative charges')
        raise
