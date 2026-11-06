"""Paired early/late forecasts of identical future observations; development only."""
import time
import resource
import hashlib
import numpy as np
from scipy.special import expit,logit
from scipy.optimize import minimize
from scipy.spatial.distance import cdist
from pilot import (HERE,PREV,OLD,IO,PINS,read,get,save,arrays,utc,cal,track,subject,VectorTrainer)
from baselines import fit_competence,draw_initial,competence_at,omission_at
from rnn_learning import load_rnn
from rnn_rollout import calibration_particles
from retained_growth import original_seed
from generate import gru_particles,crps

CUTOFFS=(200,1000)
WINDOWS=(500,2000)
HALVES=(100.,250.,500.,np.inf)
N=256
SOURCE_N=128
FUTURE={}
FIT_CACHE={}

def estimate(a,cutoff,half=None):
    p=a[:cutoff]
    if half is None:return fit_competence(subject(p[-500:]))
    x=track.psych(np.nan_to_num(p[:,1])-np.nan_to_num(p[:,0]));c=p[:,2];ok=c!=0;y=(c[ok]<0).astype(float)
    weights=np.ones(cutoff) if np.isinf(half) else np.exp2(-(cutoff-1-np.arange(cutoff))/half)
    X=x[ok];v=weights[ok]
    def obj(w):
        z=X@w;pr=expit(z)
        return np.sum(v*(np.logaddexp(0,z)-y*z))+.5*np.sum(w*w),X.T@(v*(pr-y))+w
    opt=minimize(obj,np.zeros(3),jac=True,method='L-BFGS-B',bounds=[(-8,12),(-8,12),(-6,6)])
    assert opt.success and np.isfinite(opt.x).all()
    pr=expit(X@opt.x);cov=np.linalg.inv(np.einsum('ni,n,nj->ij',X,v*pr*(1-pr),X)+np.eye(3))
    o=(np.sum(p[-500:,2]==0)+.5)/(len(p[-500:])+1)
    return opt.x,cov,o

def bank_at(raw,ids,cutoff,half=None):
    pref=[];delta=[];omit=[];valid=[]
    for s in ids:
        a=raw[s];key=(s,cutoff,half)
        if key not in FIT_CACHE:FIT_CACHE[key]=estimate(a,cutoff,half)
        w,_,o=FIT_CACHE[key];ww=[];oo=[];vv=[]
        for b in range(10):
            lo=cutoff+b*500;hi=lo+500;yes=hi<=len(a)
            if yes:
                k=(s,lo,hi)
                if k not in FUTURE:FUTURE[k]=fit_competence(subject(a[lo:hi]))
                wb,_,ob=FUTURE[k]
            else:wb=w;ob=o
            ww.append(wb-w);oo.append(logit(ob)-logit(o));vv.append(yes)
        pref.append(np.r_[w,logit(o)]);delta.append(ww);omit.append(oo);valid.append(vv)
    return dict(subjects=np.array(ids),prefix=np.array(pref),delta_w=np.array(delta),
                delta_omit=np.array(omit),valid=np.array(valid),prefix_n=np.array(cutoff),bin_size=np.array(500),horizon=np.array(5000))

def choice_draw(s,a,cutoff,half,bank,n,stream):
    w,cov,o=estimate(a,cutoff,half);rng=np.random.default_rng(stream+611)
    dist=np.sum(((bank['prefix']-np.r_[w,logit(o)])/[1.5,1.5,1.5,2.])**2,axis=1)
    dist[bank['subjects']==s]=np.inf;order=np.argsort(dist);order=order[np.isfinite(dist[order])]
    chosen=rng.choice(order[:15],n);wb=rng.multivariate_normal(w,cov,n);dw=[]
    for b in range(10):
        pool=order[bank['valid'][order,b]][:15];assert len(pool)
        selected=chosen.copy();missing=~bank['valid'][selected,b]
        selected[missing]=rng.choice(pool,int(missing.sum()));dw.append(bank['delta_w'][selected,b])
    return dict(anchor=wb,delta_w=np.stack(dw,axis=1),bin_size=500)

def observed(a):
    result=[]
    for horizon in WINDOWS:
        b=a[1000:1000+horizon];x=np.nan_to_num(b[:,1])-np.nan_to_num(b[:,0]);c=b[:,2]
        row=[]
        for sign in (-1,1):row.extend([int((x==sign).sum()),int(((x==sign)&(c==-sign)).sum())])
        row.extend([int((c==0).sum()),int((c<0).sum()),int((b[:,3]>0).sum())]);result.append(row)
    return np.array(result)

def score_window(sample,obs,horizon):
    result={};ratio=[];joint=[];count=[];mae=[];mass=[];er=[];pooled=[]
    for j in (0,2):
        n,k=sample[:,j],sample[:,j+1];on,ok=obs[j:j+2];positive=n>0
        ratios=np.divide(k,n,out=np.zeros(len(k),float),where=positive)
        v=np.column_stack([~positive,ratios,np.where(positive,1-ratios,0)]).astype(float)
        target=np.array([0,ok/on,1-ok/on]) if on else np.array([1,0,0])
        ratio.append(float((np.linalg.norm(v-target,axis=1).mean()-.5*cdist(v,v).mean())/np.sqrt(2)))
        vv=np.column_stack([k,n-k,horizon-n])/horizon;yy=np.array([ok,on-ok,horizon-on])/horizon
        joint.append(float(np.linalg.norm(vv-yy,axis=1).mean()-.5*cdist(vv,vv).mean()))
        count.append(crps(n/horizon,on/horizon));mass.append(float(positive.mean()))
        mean=float(ratios[positive].mean()) if positive.any() else .5;er.append(mean)
        pooled.append(float(k.mean()/n.mean()) if n.mean() else .5)
        mae.append(float(abs(mean-ok/on)) if on else None)
    result=dict(mixed_ratio_score=float(np.mean(ratio)),joint=float(np.mean(joint)),count=float(np.mean(count)),
                equal_side_mae=float(np.mean(mae)) if all(x is not None for x in mae) else None,
                positive_mass=mass,expected_ratio=er,count_pooled=pooled,
                omission_crps=crps(sample[:,4]/horizon,obs[4]/horizon),all_correct_crps=crps(sample[:,6]/horizon,obs[6]/horizon))
    return result

def simulate(s,a,cutoff,name,model,canonical,candidate=None,half=None,n=N,calibration=None):
    stream=original_seed(s);prefix=subject(a[:cutoff])
    shared=draw_initial(prefix,canonical,n,stream+211,exclude=s,neighbors=15,competence='growth')
    info=None
    if name=='gru':
        if cutoff==1000 and calibration is not None:
            state,_=gru_particles(model,a,calibration,np.random.default_rng(stream+313),n)
        else:state,info=calibration_particles(model,prefix,n,stream+313)
    elif name=='recent_growth':choice=choice_draw(s,a,cutoff,half,candidate,n,stream)
    if cutoff==1000:
        action=np.random.default_rng(stream+101);teacher_seed=stream+419
    else:action=np.random.default_rng(stream+900101);teacher_seed=stream+900419
    teacher=VectorTrainer.from_prefix(prefix,n,teacher_seed,'standard')
    counts=np.zeros((n,7),np.int32);saved=[]
    for absolute in range(cutoff,3000):
        t=absolute-cutoff
        if absolute==1000 and cutoff<1000:
            # Couple random innovations over the shared target, never states.
            action=np.random.default_rng(stream+101);teacher.rng=np.random.default_rng(stream+419)
        day=bool(a[absolute,6])
        if day:teacher.new_session()
        task=teacher.sample();x=task['signed_contrast'];f=track.psych(x)
        if name=='gru':p=model.probs(state,x)
        elif name=='growth':p=expit(np.sum(competence_at(shared,t)*f,axis=1))
        else:p=expit(np.sum(competence_at(choice,t)*f,axis=1))
        q=omission_at(shared,t,'growth');c=np.where(action.random(n)<p,-1,1).astype(np.int8)
        c[action.random(n)<q]=0;feedback=teacher.observe(c)
        if name=='gru':model.update(state,x,c,feedback['feedbackType'],session_start=day)
        if absolute>=1000:
            for j,sign in ((0,-1),(2,1)):
                keep=x==sign;counts[:,j]+=keep;counts[:,j+1]+=keep&(c==-sign)
            counts[:,4]+=c==0;counts[:,5]+=c<0;counts[:,6]+=feedback['correct']
        if absolute+1 in (1500,3000):saved.append(counts.copy())
    return np.stack(saved,axis=1),info

def teacher_origin(s,a,cutoff):
    tr=VectorTrainer.from_prefix(subject(a[:cutoff]),1,original_seed(s),'standard');outside=wrong=n=0
    from trainer import FULL_CONTRASTS
    for t in range(cutoff,3000):
        if a[t,6]:tr.new_session()
        left,right,c,r,vol,pl,_=a[t]
        con=max(0 if np.isnan(left) else left,0 if np.isnan(right) else right)
        side=-1 if np.isfinite(left) and (not np.isfinite(right) or left>=right) else 1
        repeat=bool(tr.pending_repeat[0]);rate=tr.response_sum_right[0]/10
        param=1-rate if repeat else .5;k=int(np.abs(FULL_CONTRASTS-con).argmin())
        outside+=bool(abs(con-tr.repeat_contrast[0])>1e-8) if repeat else bool(not tr.pool[0,k])
        wrong+=not np.isclose(pl,param,atol=1e-7);n+=1
        tr._record(np.array([con]),np.array([side]),np.array([int(c)]),np.array([r>0]),np.array([repeat]),np.array([0. if not np.isfinite(vol) else max(0.,vol)]))
        tr.prob_left[:]=param
    return dict(n=int(n),contrast_support_failures=int(outside),parameter_failures=int(wrong))

def main():
    begin=time.monotonic()
    save('EARLY_ACCESS.json',dict(utc=utc(),authority='BRIEF same-assignment continuation; existing SOURCE_FIT6000_MANIFEST proof and capped64 manifest',
        caches=['TRAIN6000_ROWS.npz','../acquisition-reactive-sequence-2026-11-04/CAPPED_ROWS.npz'],fit_cap=6000,evaluation_cap=4000,
        fields=['contrastLeft','contrastRight','choice','feedbackType','rewardVolume','probabilityLeft','derived session starts'],
        no_new_original_rows=True))
    raw=arrays(HERE/'TRAIN6000_ROWS.npz');ev=arrays(PREV/'CAPPED_ROWS.npz')
    oldbankpath=OLD/'artifacts/baselines/nested_growth_bank.npz';read(oldbankpath,'036f3cfedd56e915b051fb29a80a2622cf5a747366ea31aa46b9249a922eea01');oldbank=arrays(oldbankpath)
    ids=list(oldbank['subjects']);split=get(OLD/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json')
    assert set(ids)<=set(split['train'])
    assert all(s in get(HERE/'SOURCE_FIT6000_MANIFEST.json')['exposure_proof'] for s in ids)
    canonical={c:bank_at(raw,ids,c) for c in CUTOFFS}
    errors={k:float(np.max(abs(canonical[1000][k]-oldbank[k]))) for k in ('prefix','delta_w','delta_omit')}
    assert np.array_equal(canonical[1000]['valid'],oldbank['valid']) and max(errors.values())<1e-10,errors
    canonical[1000]=oldbank
    validation=[s for s in split['validation'] if len(raw[s])>=3000]
    source_labs=get(HERE/'PREPARATION6000.json')['disposition']
    candidatebanks={};cv={}
    for half in HALVES:
        key='infinity' if np.isinf(half) else str(int(half));candidatebanks[key]={};cv[key]={}
        for cutoff in CUTOFFS:
            bank=bank_at(raw,ids,cutoff,half);candidatebanks[key][cutoff]=bank;loss=[]
            for s in validation:
                sample,_=simulate(s,raw[s],cutoff,'recent_growth',None,canonical[cutoff],bank,half,SOURCE_N)
                score=score_window(sample[:,1],observed(raw[s])[1],2000)
                loss.append(dict(subject=s,lab=source_labs[s]['lab'],score=score['mixed_ratio_score']))
            bylab={l:float(np.mean([v['score'] for v in loss if v['lab']==l])) for l in sorted({v['lab'] for v in loss})}
            cv[key][str(cutoff)]=dict(per_animal=loss,equal_site=float(np.mean(list(bylab.values()))))
        print('Source recency candidate',key,'seconds',round(time.monotonic()-begin,1),flush=True)
    ranking={k:np.mean([v[str(c)]['equal_site'] for c in CUTOFFS]) for k,v in cv.items()}
    chosen=min(ranking,key=ranking.get);half=np.inf if chosen=='infinity' else float(chosen)
    for cutoff in CUTOFFS:
        np.savez_compressed(HERE/f'EARLY_CANONICAL_BANK_{cutoff}.npz',**canonical[cutoff])
        np.savez_compressed(HERE/f'EARLY_RECENT_BANK_{cutoff}.npz',**candidatebanks[chosen][cutoff])
    save('EARLY_SOURCE_SELECTION.json',dict(utc=utc(),chosen_half_life=chosen,ranking=ranking,cv=cv,
         validation_eligible=validation,validation_excluded={s:len(raw[s]) for s in split['validation'] if s not in validation},
         reference_bank_errors=errors,source_donors=ids,seconds=time.monotonic()-begin,io=dict(IO)))
    fit=get(HERE/'DEVELOPED_FIT.json');modelpath=OLD/'artifacts/rnn/rnnglm32_nested_best.npz'
    read(modelpath,'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940');model=load_rnn(modelpath)
    save('EARLY_EVALUATION_FREEZE.json',dict(utc=utc(),code_sha256=hashlib.sha256(read(HERE/'early.py')).hexdigest(),
         source_selection=chosen,source_pins=PINS.copy(),cutoffs=CUTOFFS,windows=WINDOWS,particles=N,roster=list(ev),
         models=['growth','recent_growth','gru'],shared_future=[1000,3000],
         scopes='Consumed feasibility only; no main. Early800 intervening opportunities generated, no actual future input. Same target, changing information/lead time, not pure learning-stage causality.'))
    allsamples=[];obs=[];scores={};calibrations={};teacher={}
    retained=arrays(HERE/'RETAINED_GROWTH_COUNTS.npz');names=('growth','recent_growth','gru');reference=[]
    for i,(s,a) in enumerate(ev.items()):
        target=observed(a);obs.append(target);contexts=[];scores[s]={};calibrations[s]={};teacher[s]={}
        for cutoff in CUTOFFS:
            teacher[s][str(cutoff)]=teacher_origin(s,a,cutoff)
            laws=[];scores[s][str(cutoff)]={}
            for name in names:
                if cutoff==1000 and name in ('growth','gru'):
                    k=0 if name=='growth' else 2
                    sample=retained['samples'][i,k,:,[1,3],:].transpose(1,0,2)
                    info=None
                else:
                    sample,info=simulate(s,a,cutoff,name,model,canonical[cutoff],candidatebanks[chosen][cutoff],half,N,
                                         calibration=fit['prefix'][s]['gru'] if cutoff==1000 else None)
                if i==0 and cutoff==1000 and name=='growth':
                    replay,_=simulate(s,a,cutoff,name,model,canonical[cutoff],n=N)
                    reference.append(int(np.max(abs(replay-sample))));assert np.array_equal(replay,sample)
                laws.append(sample)
                scores[s][str(cutoff)][name]={str(h):score_window(sample[:,j],target[j],h) for j,h in enumerate(WINDOWS)}
                if info is not None:calibrations[s][str(cutoff)]=info
            contexts.append(np.stack(laws))
        allsamples.append(np.stack(contexts))
        if (i+1)%8==0:print('Paired calibration feasibility',i+1,'/64 seconds',round(time.monotonic()-begin,1),flush=True)
    np.savez_compressed(HERE/'EARLY_COUNTS.npz',samples=np.stack(allsamples),observed=np.stack(obs),subjects=list(ev),
                        names=names,cutoffs=CUTOFFS,windows=WINDOWS)
    save('EARLY_SCORES.json',dict(utc=utc(),per_animal=scores,calibrations=calibrations,teacher=teacher,
          reference_replay_max_count_error=max(reference),seconds=time.monotonic()-begin,io=dict(IO),
          peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print('SAVED paired feasibility',utc(),'seconds',time.monotonic()-begin,flush=True)

if __name__=='__main__':main()
