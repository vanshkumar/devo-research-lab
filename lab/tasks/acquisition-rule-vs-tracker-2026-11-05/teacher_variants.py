"""Prefix-only calibration of repeat-contrast settings, without altering old code."""
import time
import numpy as np
from pilot import (HERE,PREV,OLD,IO,get,save,arrays,subject,seed,VectorTrainer,FULL_CONTRASTS,utc)
from scipy.special import ndtr

GRID=np.array([np.inf,1.,.5,.25,.125,.0625,0.])

class PrefixTrainer(VectorTrainer):
    def __init__(self,*args,repeat_min=.5,**kwargs):
        self.repeat_min=repeat_min
        super().__init__(*args,**kwargs)
    def _record(self,contrast,side,choice,correct,repeats,reward):
        super()._record(contrast,side,choice,correct,repeats,reward)
        self.pending_repeat=(~correct)&(contrast>=self.repeat_min)&self.correction

def prefix_losses(a,stop=1000):
    # The setting controls whether preceding errors invoke RepeatContrast.
    # Current parameter is checked before assimilating the current response.
    losses=np.zeros(len(GRID));n=0; buffer=[]
    for t in range(min(stop,len(a))):
        if a[t,6]:buffer=[]
        if t and not a[t,6]:
            rate=sum(c==1 for c in buffer)/10
            prev=abs(np.nan_to_num(a[t-1,1])-np.nan_to_num(a[t-1,0]))
            repeat=(a[t-1,3]<=0)&(prev>=GRID)
            predicted=np.where(repeat,1-rate,.5)
            losses+=~np.isclose(predicted,a[t,5],atol=1e-7)
            n+=1
        buffer=(buffer+[int(a[t,2])])[-10:]
    return losses,n

def choose(a):
    losses,n=prefix_losses(a)
    best=np.flatnonzero(losses==losses.min())
    # Preserve published default in ties; otherwise nearest to .5.
    idx=2 if 2 in best else best[np.argmin(np.abs(np.log2(np.maximum(GRID[best],1e-9)) +1))]
    return float(GRID[idx]),losses,n

def audit_one(s,a,repeat_min):
    tr=PrefixTrainer.from_prefix(subject(a[:1000]),1,seed(s),'standard',repeat_min=repeat_min)
    n=outside=mismatch=0;calibration=np.zeros((10,4));examples=[]
    for t in range(1000,len(a)):
        if a[t,6]:tr.new_session()
        left,right,c,r,vol,pl,_=a[t]
        contrast=max(0 if np.isnan(left) else left,0 if np.isnan(right) else right)
        side=-1 if np.isfinite(left) and (not np.isfinite(right) or left>=right) else 1
        repeat=bool(tr.pending_repeat[0]);rate=tr.response_sum_right[0]/10
        param=1-rate if repeat else .5
        pleft=ndtr((.5-rate)/.5) if repeat else tr.prob_left[0]
        k=int(np.abs(FULL_CONTRASTS-contrast).argmin())
        bad=bool(abs(contrast-tr.repeat_contrast[0])>1e-8) if repeat else bool(not tr.pool[0,k])
        mis=not np.isclose(pl,param,atol=1e-7)
        n+=1;outside+=bad;mismatch+=mis
        calibration[min(9,int(pleft*10))]+=[1,side<0,pleft,pleft*(1-pleft)]
        if len(examples)<3 and (bad or mis):examples.append(dict(t=t+1,contrast=float(contrast),repeat=repeat,parameter=float(pl),predicted=float(param)))
        tr._record(np.array([contrast]),np.array([side]),np.array([int(c)]),np.array([r>0]),np.array([repeat]),np.array([0. if not np.isfinite(vol) else max(0.,vol)]))
        tr.prob_left[:]=param
    return dict(n=n,outside=outside,parameter_mismatch=mismatch,side_calibration=calibration.tolist(),examples=examples)

def main():
    begin=time.monotonic();raw=arrays(HERE/'TRAIN6000_ROWS.npz'); ev=arrays(PREV/'CAPPED_ROWS.npz')
    split=get(OLD/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json')
    train={}; evaluation={}
    for s,a in raw.items():
        if len(a)<=1000:continue
        cut,loss,n=choose(a)
        train[s]=dict(repeat_min=None if np.isinf(cut) else cut,prefix_mismatch=loss.tolist(),n_prefix=n,
                      **audit_one(s,a,cut),role='train' if s in split['train'] else 'selection')
    for s,a in ev.items():
        cut,loss,n=choose(a)
        evaluation[s]=dict(repeat_min=None if np.isinf(cut) else cut,prefix_mismatch=loss.tolist(),n_prefix=n,
                           **audit_one(s,a,cut))
    total={k:int(sum(v[k] for v in evaluation.values())) for k in ('n','outside','parameter_mismatch')}
    save('PREFIX_TEACHER_AUDIT.json',dict(utc=utc(),grid=[None,1,.5,.25,.125,.0625,0.],
        source=train,evaluation=evaluation,total=total,seconds=time.monotonic()-begin,io=dict(IO),
        note='Repeat setting selected only from first1000; preserved published .5 default in ties. No future input/response sets the forecast setting. This does not certify hidden settings, source pool prehistory, future changes or stochastic probability law.'))
    print(total,'seconds',time.monotonic()-begin,flush=True)

if __name__=='__main__': main()
