"""Consumed-data conditional model and deployed-input-law development."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import numpy as np
from scipy.special import expit, ndtr

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PREV=HERE.parent/'acquisition-reactive-sequence-2026-11-04'
OLD=ROOT/'campaigns/learning_rule_transport_2026-10-28'
REV=ROOT/'campaigns/learning_transport_revised_2026-10-29'
sys.path[:0]=[str(PREV),str(OLD/'code')]
import calibrate as cal
import tracker as track
from rnn_learning import load_rnn
from trainer import VectorTrainer, FULL_CONTRASTS
from numba import njit

IO=Counter()
PINS={}
def utc():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
def read(p,pin=None):
    b=p.read_bytes(); IO['explicit_file_read_bytes']+=len(b)
    h=hashlib.sha256(b).hexdigest(); PINS[str(p.relative_to(ROOT))]=h
    if pin: assert h==pin,str(p)
    return b
def get(p,pin=None): return json.loads(read(p,pin))
def save(name,x): (HERE/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def arrays(p):
    read(p)
    with np.load(p,allow_pickle=False) as z: out={s:z[s] for s in z.files}
    IO['decoded_array_bytes']+=sum(a.nbytes for a in out.values())
    return out
def seed(s): return int.from_bytes(hashlib.sha256(s.encode()).digest()[:4],'little')
def subject(a):
    return dict(contrastLeft=a[:,0],contrastRight=a[:,1],choice=a[:,2],
                feedbackType=a[:,3],rewardVolume=a[:,4],session_start=a[:,6].astype(bool),
                session=np.cumsum(a[:,6]).astype(int))

@njit(cache=True)
def scan(x,c,day,base,eta):
    out=np.empty(len(c)); states=np.empty((len(c),3)); state=np.zeros(3)
    for i in range(len(c)):
        if day[i]: state*=.85
        states[i]=state
        p=1/(1+np.exp(-max(-40.,min(40.,base[i]+np.sum(state*x[i])))))
        out[i]=p; state*=.996
        if c[i]!=0: state+=eta*((c[i]<0)-p)*x[i]
    return out,states,state

def fit_shared(ids,ds,d):
    coeff=[]
    for k in (0,1,2):
        pair=[]
        for j in (0,1):
            xx=[];yy=[];oo=[]
            for s in ids:
                c=d[s]['c'][1000:]; mask=c!=0 if j==0 else np.ones(len(c),bool)
                xx.append(ds[s]['matrices'][k][j][1000:][mask])
                yy.append((c[mask]<0 if j==0 else c[mask]==0).astype(float))
                oo.append(ds[s]['offsets'][j][1000:][mask])
            pair.append(cal.fit(np.concatenate(xx),np.concatenate(yy),np.concatenate(oo),12.))
        coeff.append(pair)
    return coeff

def teacher_audit(raw,ids):
    result={}
    for s in ids:
        a=raw[s]; pre=subject(a[:1000]); tr=VectorTrainer.from_prefix(pre,1,seed(s),'standard')
        totals=Counter(); example=[]; sumbins=np.zeros((10,3))
        for t in range(1000,len(a)):
            if a[t,6]: tr.new_session()
            left,right,c,r,vol,pl,_=a[t]
            contrast=max(0 if np.isnan(left) else left,0 if np.isnan(right) else right)
            side=-1 if np.isfinite(left) and (not np.isfinite(right) or left>=right) else 1
            repeat=bool(tr.pending_repeat[0]); rate=tr.response_sum_right[0]/10
            param=1-rate if repeat else .5
            sideprob=ndtr((.5-rate)/.5) if repeat else tr.prob_left[0]
            k=int(np.abs(FULL_CONTRASTS-contrast).argmin())
            unsupported=(abs(contrast-tr.repeat_contrast[0])>1e-8) if repeat else not tr.pool[0,k]
            mismatch=not np.isclose(pl,param,atol=1e-7)
            totals['n']+=1; totals['repeat']+=repeat; totals['contrast_support_failures']+=unsupported
            totals['probabilityLeft_mismatches']+=mismatch
            totals['nonzero_feedback_disagreements']+=bool(contrast>0 and ((r>0)!=(c==-side)))
            totals['omission_positive_feedback']+=bool(c==0 and r>0)
            if len(example)<5 and (unsupported or mismatch):
                example.append(dict(opportunity=t+1,contrast=float(contrast),repeat=repeat,
                    pool=tr.pool[0].tolist(),recorded_probabilityLeft=float(pl),predicted_parameter=float(param)))
            bi=min(9,int(sideprob*10)); sumbins[bi]+=[1,side<0,sideprob]
            # Assimilate this actual input/outcome only AFTER its predictive audit.
            # No widening by newly observed post-prefix contrasts.
            tr._record(np.array([contrast]),np.array([side]),np.array([int(c)]),np.array([r>0]),
                       np.array([repeat]),np.array([0. if not np.isfinite(vol) else max(0.,vol)]))
            tr.prob_left[:]=param
        result[s]=dict(**totals,examples=example,side_calibration=sumbins.tolist())
    total={k:int(sum(r[k] for r in result.values())) for k in next(iter(result.values())) if k not in ('examples','side_calibration')}
    return dict(per_animal=result,total=total,scope='actual-history pretrial input-law check; initialized only from first 1000; no future contrast augmentation')

def stats(d,p,q,start=1000):
    c=d['c'][start:]; x=d['x'][start:]; tern=cal.ternary(p,q)
    y=(1-c).astype(int)
    nll=-np.log(np.clip(tern[np.arange(len(c)),y],1e-12,1))
    ok=c!=0
    binary=-np.log(np.clip(np.where(c[ok]<0,p[ok],1-p[ok]),1e-12,1))
    correct=(x!=0)&(c==-np.sign(x))
    pc=np.where(x>0,tern[:,2],np.where(x<0,tern[:,0],0.))
    pred=np.column_stack([pc,q,tern[:,2]])
    res=np.column_stack([correct,c==0,c<0])-pred
    vv=pred*(1-pred)
    blocks={}
    for size in (6,50,200):
        z=np.zeros((3,2)); bounds=np.r_[0,np.flatnonzero(d['day'][start+1:])+1,len(c)]
        for a,b in zip(bounds[:-1],bounds[1:]):
            stop=a+(b-a)//size*size
            z[:,0]+=(res[a:stop].reshape(-1,size,3).sum(1)**2).sum(0)
            z[:,1]+=vv[a:stop].sum(0)
        blocks[str(size)]=z.tolist()
    calibration=[]
    for a in np.linspace(0,1,11)[:-1]:
        use=(pc>=a)&(pc<a+.1+1e-14)
        calibration.append([int(use.sum()),float(pc[use].sum()),int(correct[use].sum())])
    return dict(n=len(c),ternary_loss=float(nll.mean()),binary_loss=float(binary.mean()),
                brier=float(np.sum((tern-np.eye(3)[y])**2,axis=1).mean()),
                bias=res.mean(0).tolist(),blocks=blocks,calibration=calibration)

def load_data():
    prep=get(HERE/'PREPARATION.json'); manifest=prep['eval_source_manifest']
    raw=arrays(HERE/'TRAIN_ROWS.npz'); ev=arrays(PREV/'CAPPED_ROWS.npz')
    assert list(ev)==manifest['subjects']
    assert {s:len(v) for s,v in ev.items()}=={s:sum(z['stop']-z['start'] for z in manifest['sessions'] if z['subject']==s) for s in ev}
    return prep,raw,ev

def main():
    start=time.monotonic(); prep,raw,ev=load_data(); split=get(OLD/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json')
    fitids=[s for s in split['train'] if len(raw[s])>1000]
    selids=[s for s in split['validation'] if len(raw[s])>1000]
    allraw={**raw,**ev}; eligible=fitids+selids+list(ev)
    d={s:cal.prepare(allraw[s]) for s in eligible}; ds={s:cal.design(d[s]) for s in eligible}
    coeff=fit_shared(fitids,ds,d)
    grid=(0.,.04,.12,.24); losses=[]
    for s in selids:
        b=ds[s]['offsets'][0][1000:]+ds[s]['matrices'][2][0][1000:]@coeff[2][0]
        x=track.psych(d[s]['x'][1000:]); c=d[s]['c'][1000:]; day=d[s]['day'][1000:]
        ps=np.array([scan(x,c,day,b,e)[0] for e in grid]); ok=c!=0
        losses.append(-np.log(np.clip(np.where(c[None,ok]<0,ps[:,ok],1-ps[:,ok]),1e-12,1)).mean(1))
    means=np.mean(losses,axis=0); eta=grid[int(np.argmin(means))]
    path=OLD/'artifacts/rnn/rnnglm32_nested_best.npz'
    read(path,'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940'); model=load_rnn(path)
    source_ref=get(REV/'artifacts/source_comparison/RESULT.json','cc8b1aedffb9c495d20b059f9c779a8f8762e7abc7500adb40838fb9bb7dab91')
    score={}; states={}; preds={}
    for i,s in enumerate(ev):
        b=ds[s]; row=d[s]; params=get(REV/'artifacts/source_comparison'/s/'existing.json')
        cr=params['calibration']; initial=dict(w=np.array(cr['endpoint']),h=np.array(cr['hidden_endpoint']))
        ps,ws,end=model.sequence(subject(ev[s][1000:]),initial)
        q=expit(b['offsets'][1][1000:]+b['matrices'][2][1][1000:]@coeff[2][1])
        pp={}
        for k,name in enumerate(('static','drift','history')):
            pp[name]=expit(b['offsets'][0][1000:]+b['matrices'][k][0][1000:]@coeff[k][0])
        base=b['offsets'][0][1000:]+b['matrices'][2][0][1000:]@coeff[2][0]
        pp['track'],wtrack,wlast=scan(track.psych(row['x'][1000:]),row['c'][1000:],row['day'][1000:],base,eta)
        pp['gru']=ps
        score[s]={name:stats(row,p,q) for name,p in pp.items()}
        preds[s]=np.column_stack([q]+[pp[n] for n in ('static','drift','history','track','gru')])
        states[s]=dict(prefix_base=[z.tolist() for z in b['base']],gru=cr,
                       track_final=wlast.tolist(),track_pretrial=wtrack.tolist(),gru_pretrial=ws.tolist())
        if (i+1)%16==0: print('Conditional',i+1,'elapsed',round(time.monotonic()-start,2),flush=True)
    labs=dict(zip(prep['eval_source_manifest']['subjects'],prep['eval_source_manifest']['labs']))
    summary={}
    for name in ('static','drift','history','track','gru'):
        sites={l:float(np.mean([score[s][name]['ternary_loss'] for s in ev if labs[s]==l])) for l in sorted(set(labs.values()))}
        blocks={}
        for size in ('6','50','200'):
            z=np.sum([score[s][name]['blocks'][size] for s in ev],axis=0)
            blocks[size]=(z[:,0]/z[:,1]).tolist()
        summary[name]=dict(equal_site_ternary=float(np.mean(list(sites.values()))),site=sites,
                           equal_animal_ternary=float(np.mean([score[s][name]['ternary_loss'] for s in ev])),
                           correct_omit_right_block_variance_ratios=blocks)
    save('FIT.json',dict(utc=utc(),fitids=fitids,selectionids=selids,eta=eta,grid=grid,
          selection_grid_loss=means.tolist(),coeff=[[v.tolist() for v in pair] for pair in coeff],
          fit_rows=sum(len(raw[s])-1000 for s in fitids),
          observation='all models use same source-fitted history-responsive omission rule; no frozen neural modification',
          training_asymmetry='58 of 62 fitting animals provide complete-session post-1000 rows before 4000; frozen GRU historically used up to 6000 and four shorter animals',
          state=states,pins=PINS))
    save('CONDITIONAL.json',dict(utc=utc(),summary=summary,per_animal=score,labs=labs,seconds=time.monotonic()-start,
          io=dict(IO),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    np.savez_compressed(HERE/'CONDITIONAL_PROBS.npz',**preds)
    ta=teacher_audit(allraw,eligible)
    save('TEACHER_AUDIT.json',dict(utc=utc(),**ta,seconds=time.monotonic()-start,io=dict(IO)))
    print(json.dumps(dict(eta=eta,summary=summary,teacher_total=ta['total'],seconds=time.monotonic()-start)),flush=True)

if __name__=='__main__': main()
