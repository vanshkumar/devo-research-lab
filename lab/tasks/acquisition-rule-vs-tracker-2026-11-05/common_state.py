"""Strong simple acquisition rival given the SAME permitted neural prefix policy."""
import time
import numpy as np
from scipy.special import expit,logit
from pilot import (HERE,PREV,OLD,REV,IO,PINS,read,get,save,arrays,seed,utc,cal,track,scan,stats,subject)
from develop import fit_logit,FIT_DIAGNOSTICS,omit_scan
from baselines import fit_competence
from rnn_learning import load_rnn

def smooth_growth(delta,elapsed):
    # Bin fits summarize centered future intervals. Interpolate them from
    # exactly zero at the forecast origin; a common policy cannot jump at t=0.
    knots=np.r_[0.,250.+500.*np.arange(len(delta))]
    values=np.vstack([np.zeros(3),delta])
    return np.column_stack([np.interp(elapsed,knots,values[:,j]) for j in range(3)])

def reference_matrix(x,d):
    _,pos,trace=cal.summarize_history(*(d[k][:1000] for k in ('x','c','r','day')))
    position=pos[-1]+1
    if d['day'][1000]:trace[:2]=0;position=0
    return cal.predictors(x,1000,position,np.tile(trace,(len(x),1,1)))[2][0]

def make_bank(raw,ids,endpoints):
    rows=[];keys=[]
    for s in ids:
        if len(raw[s])<1500:continue
        w=np.array(endpoints[s]['w']);a=raw[s];o=(np.sum(a[500:1000,2]==0)+.5)/501
        changes=[];valid=[]
        for t in range(1000,6000,500):
            yes=len(a)>=t+500;valid.append(yes)
            wb=fit_competence(subject(a[t:t+500]))[0] if yes else w
            changes.append(wb-w)
        keys.append(s);rows.append((np.r_[w,logit(o)],changes,valid))
    return dict(ids=np.array(keys),prefix=np.array([r[0] for r in rows]),
                delta=np.array([r[1] for r in rows]),valid=np.array([r[2] for r in rows]))

def pool_for(s,a,endpoint,bank):
    o=(np.sum(a[500:1000,2]==0)+.5)/501;cur=np.r_[endpoint['w'],logit(o)]
    dist=np.sum(((bank['prefix']-cur)/[1.5,1.5,1.5,2.])**2,axis=1)
    dist[bank['ids']==s]=np.inf;order=np.argsort(dist);order=order[np.isfinite(dist[order])]
    return [order[bank['valid'][order,b]][:15] for b in range(10)]

def fit_hybrid(ids,d,f):
    X=[];y=[];off=[]
    for s in ids:
        c=d[s]['c'][1000:];ok=c!=0
        X.append(f[s]['diff'][1000:][ok]);y.append((c[ok]<0).astype(float));off.append(f[s]['offset'][1000:][ok])
    return fit_logit(np.concatenate(X),np.concatenate(y),np.concatenate(off))

def main():
    begin=time.monotonic();raw=arrays(HERE/'TRAIN6000_ROWS.npz');ev=arrays(PREV/'CAPPED_ROWS.npz')
    fit=get(HERE/'DEVELOPED_FIT.json');split=get(OLD/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json')
    tr=fit['fitids'];val=fit['selectionids'];allraw={**raw,**ev};ids=tr+val+list(ev)
    path=OLD/'artifacts/rnn/rnnglm32_nested_best.npz';read(path,'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940');model=load_rnn(path)
    endpoint_path=HERE/'COMMON_PREFIX_SOURCE_STATES.json'
    endpoints=get(endpoint_path)['states'] if endpoint_path.exists() else {}
    for i,s in enumerate(ids):
        if s in endpoints:continue
        if s in ev:
            c=fit['prefix'][s]['gru'];endpoints[s]=dict(w=c['endpoint'],h=c['hidden_endpoint'],w0=c['w0'])
        else:
            st=model.initial_state(subject(raw[s][:1000]));endpoints[s]={k:st[k].tolist() for k in ('w','h','w0')}
        if (i+1)%32==0:print('Common prefix states',i+1,'seconds',round(time.monotonic()-begin,1),flush=True)
    save('COMMON_PREFIX_SOURCE_STATES.json',dict(utc=utc(),states=endpoints,io=dict(IO),
          note='New source-only prefix MAP calibration; frozen neural shared weights unchanged; evaluation states reused exactly.'))
    d={s:cal.prepare(allraw[s]) for s in ids};ds={s:cal.design(d[s]) for s in ids}
    bank=make_bank(raw,tr,endpoints);f={};pool={}
    for s in ids:
        a=allraw[s];pools=pool_for(s,a,endpoints[s],bank);delta=np.array([bank['delta'][p,b].mean(0) for b,p in enumerate(pools)])
        policy=track.psych(d[s]['x'])@np.array(endpoints[s]['w'])
        growth=np.sum(track.psych(d[s]['x'])*smooth_growth(delta,np.maximum(0,np.arange(len(a))-1000)),axis=1)
        diff=ds[s]['matrices'][2][0]-reference_matrix(d[s]['x'],d[s])
        f[s]=dict(offset=policy+growth,diff=diff,growth=growth,policy=policy);pool[s]=[p.tolist() for p in pools]
    beta=fit_hybrid(tr,d,f);grid=(0.,.04,.12,.24);loss=[]
    for s in val:
        a=d[s];c=a['c'][1000:];ok=c!=0
        base=f[s]['offset'][1000:]+f[s]['diff'][1000:]@beta
        p=np.array([scan(track.psych(a['x'][1000:]),c,a['day'][1000:],base,e)[0] for e in grid])
        loss.append(-np.log(np.clip(np.where(c[None,ok]<0,p[:,ok],1-p[:,ok]),1e-12,1)).mean(1))
    mean=np.mean(loss,axis=0);eta=grid[int(np.argmin(mean))]
    rng=np.random.default_rng(202611052);boots=[]
    for j in range(12):boots.append(fit_hybrid(list(rng.choice(tr,len(tr),replace=True)),d,f))
    np.savez_compressed(HERE/'COMMON_GROWTH_BANK.npz',**bank)
    np.savez_compressed(HERE/'COMMON_SOURCE_BOOTSTRAP.npz',beta=np.array(boots))
    scores={};preds={};qinit={};refs={}
    historyomit=np.array(fit['history_coeff'][1])
    for s in ev:
        a=d[s];b=ds[s];c=a['c'];day=a['day'];X=track.psych(a['x'])
        # All models share the exact same prefix-warmed omission filter.
        bq=b['offsets'][1]+b['matrices'][2][1]@historyomit
        q,end=omit_scan(c,day,bq,fit['omission_eta'])
        q1000=omit_scan(c[:1000],day[:1000],bq[:1000],fit['omission_eta'])[1]
        base=f[s]['offset'][1000:3000]+f[s]['diff'][1000:3000]@beta
        ph=scan(X[1000:3000],c[1000:3000],day[1000:3000],base,eta)[0]
        pg=expit(f[s]['offset'][1000:3000]);pr=model.sequence(subject(ev[s][1000:3000]),
             dict(w=np.array(endpoints[s]['w']),h=np.array(endpoints[s]['h'])))[0]
        truncated={k:v[:3000] for k,v in a.items()}
        scores[s]={n:stats(truncated,p,q[1000:3000]) for n,p in (('common_growth',pg),('common_hybrid',ph),('gru',pr))}
        preds[s]=np.column_stack([q[1000:3000],pg,ph,pr]);qinit[s]=float(q1000)
        # Retain cue-dependent origin matrix so first prediction exactly matches.
        refs[s]=reference_matrix(np.array([-1,-.5,-.25,-.125,-.0625,0,.0625,.125,.25,.5,1]),a).tolist()
    save('COMMON_FIT.json',dict(utc=utc(),beta=beta.tolist(),eta=eta,grid=grid,grid_loss=mean.tolist(),
          source_fitids=tr,selectionids=val,donor_pools=pool,omission_start=qinit,origin_cues=[-1,-.5,-.25,-.125,-.0625,0,.0625,.125,.25,.5,1],origin_features=refs,
          fit_diagnostics=FIT_DIAGNOSTICS,seconds=time.monotonic()-begin,io=dict(IO),
          note='Each law receives the same prefix GRU policy. Simple rival then uses donor-derived growth, centered causal history effects and score updates. This is an updater ablation with neural initialization cost, not independent cheap neural-family competition.'))
    save('COMMON_CONDITIONAL.json',dict(utc=utc(),per_animal=scores,seconds=time.monotonic()-begin,io=dict(IO)))
    np.savez_compressed(HERE/'COMMON_PROBS.npz',**preds)
    print('SAVED common-state fit','eta',eta,'seconds',time.monotonic()-begin,flush=True)

if __name__=='__main__':main()
