"""Frozen fixed main and two prescribed dependent ordinary sensitivities."""
from common import *
NAMES=['growth','recent100','recent250','gru'];CUTOFFS=[200,1000];STREAMS=[0,10000019]

def main():
    seal=get(HERE/'PRE_OUTCOME_SEAL.json')
    for p,h in seal['pins'].items():read(ROOT/p,h)
    assert get(HERE/'CHRONOLOGY_CHECKS.json')['all_passed']
    ms,e,model,canonical,recent=load_prescriptions()
    data=arrays(HERE/'CHRONOLOGICAL_MAIN.npz');ids=list(data['subjects']);assert len(ids)==192
    # This process uses only prefix values/boundaries. Observed scores are separate.
    a=data['values'];assert a.shape==(192,3000,7)
    seedrecords=[]
    for s in ids:
        seedrecords.append(dict(subject=s,base=e.original_seed(s),stream_offsets=STREAMS,
            prefix_fisher=[e.original_seed(s)+x+313 for x in STREAMS],donor=[e.original_seed(s)+x+211 for x in STREAMS],
            recent_anchor=[e.original_seed(s)+x+611 for x in STREAMS],
            early_action=[e.original_seed(s)+x+900101 for x in STREAMS],late_action=[e.original_seed(s)+x+101 for x in STREAMS],
            early_teacher=[e.original_seed(s)+x+900419 for x in STREAMS],late_teacher=[e.original_seed(s)+x+419 for x in STREAMS]))
    save('SEEDS.json',dict(utc=utc(),per_animal=seedrecords,primary_particles_per_stream=512,source_particles_per_stream=256))
    (HERE/'main_chunks').mkdir(exist_ok=True);(HERE/'source_chunks').mkdir(exist_ok=True)
    sourcebanks={j:{c:dict(canonical=arrays(HERE/f'banks/source{j}_canonical_{c}.npz'),
        recent=arrays(HERE/f'banks/source{j}_recent100_{c}.npz')) for c in CUTOFFS} for j in [0,14]}
    completed=0;sourcecompleted=0
    for i,s in enumerate(ids):
        path=HERE/'main_chunks'/(s+'.npz')
        if not path.exists():
            sample=np.empty((2,4,2,512,2,7),np.int32);cal=[];blocks=np.empty((2,4,2,40,3),float)
            for ci,c in enumerate(CUTOFFS):
                view=ms.causal_view(a[i],c)
                assert np.isnan(view[c:,:6]).all()
                for si,offset in enumerate(STREAMS):
                    state,info=ms.initial_neural(model,view,c,512,e.original_seed(s)+offset)
                    cal.append(dict(cutoff=c,stream=si,info=info))
                    for ni,name in enumerate(NAMES):
                        actor='recent_growth' if name.startswith('recent') else name
                        half=int(name[6:]) if actor=='recent_growth' else None
                        bank=recent[half][c] if half else None
                        out,b=ms.simulate(s,view,c,actor,model,canonical[c],bank,half,n=512,
                            stream_offset=offset,neural_state=state if actor=='gru' else None)
                        sample[ci,ni,si]=out
                        blocks[ci,ni,si]=np.stack([b.mean(0),np.mean(b*b,axis=0),np.quantile(b,.9,axis=0)],axis=-1)
            npz('main_chunks/'+s+'.npz',samples=sample,omission_blocks=blocks,subject=s,cutoffs=CUTOFFS,names=NAMES,streams=STREAMS)
            save('main_chunks/'+s+'_calibration.json',dict(subject=s,prefix=cal))
        completed+=1
        for j in [0,14]:
            p=HERE/'source_chunks'/(str(j)+'_'+s+'.npz')
            if p.exists():sourcecompleted+=1;continue
            sample=np.empty((2,2,2,256,2,7),np.int32)
            for ci,c in enumerate(CUTOFFS):
                view=ms.causal_view(a[i],c);bank=sourcebanks[j][c]
                for si,offset in enumerate(STREAMS):
                    for ni,name in enumerate(['growth','recent_growth']):
                        out,_=ms.simulate(s,view,c,name,None,bank['canonical'],bank['recent'],100,n=256,stream_offset=offset)
                        sample[ci,ni,si]=out
            npz('source_chunks/'+str(j)+'_'+s+'.npz',samples=sample,subject=s,draw=j,names=['growth','recent100'],cutoffs=CUTOFFS,streams=STREAMS)
            sourcecompleted+=1
        if (i+1)%4==0 or i+1==192:
            print('COMPLETE',i+1,'/192 fixed plus both source draws','CPU',round(time.process_time()-START_CPU,2),
                'wall',round(time.monotonic()-START_WALL,2),flush=True)
            receipt('CONFIRMATION_LIVE','running',main_animals=completed,source_animal_draws=sourcecompleted)
        if time.process_time()-START_CPU>10000:raise RuntimeError('Initial main CPU safety stop; preserve completed chunks')
        start=get(HERE/'GOAL_START.json')['goalReadback']['goal']['createdAt']
        if time.time()-start>21000:raise RuntimeError('Initial stage elapsed safety stop; no automatic extension')
    save('FORECAST_COMPLETION.json',dict(utc=utc(),main_animals=completed,source_animal_draws=sourcecompleted,
        main_particles=1024,source_particles=512,all_forecast_jobs_terminal=True,goal_should_remain_active=True,
        future_factual_information='session allocation flags only; six future values physicallyNaN',
        source_scope='ordinary donor/anchor perturbation with literal unchanged primary GRU forecast; no neural refit'))
    receipt('CONFIRMATION','complete',main_animals=completed,source_animal_draws=sourcecompleted,all_jobs_terminal=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        n=len(list(HERE.glob('CONFIRMATION_FAILURE_*.json')))
        receipt('CONFIRMATION_FAILURE_'+str(n),'failed',error=repr(exc));raise
