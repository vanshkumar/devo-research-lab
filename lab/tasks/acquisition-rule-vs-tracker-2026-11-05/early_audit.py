"""Early-origin hidden-future poison and nonlinear prefix-uncertainty check."""
import time
import hashlib
import numpy as np
from pilot import HERE,PREV,OLD,IO,read,get,save,arrays,utc,track,subject
from early import simulate
from retained_growth import original_seed
from rnn_learning import load_rnn

def main():
    began=time.monotonic();raw=arrays(PREV/'CAPPED_ROWS.npz')
    canonical=arrays(HERE/'EARLY_CANONICAL_BANK_200.npz');recent=arrays(HERE/'EARLY_RECENT_BANK_200.npz')
    selection=get(HERE/'EARLY_SOURCE_SELECTION.json');half=np.inf if selection['chosen_half_life']=='infinity' else float(selection['chosen_half_life'])
    path=OLD/'artifacts/rnn/rnnglm32_nested_best.npz';read(path,'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940');model=load_rnn(path)
    s=next(iter(raw));a=raw[s];poison=a.copy();rng=np.random.default_rng(111)
    poison[200:,:6]=rng.normal(100,20,poison[200:,:6].shape)
    causal={}
    for name in ('growth','recent_growth','gru'):
        x,_=simulate(s,a,200,name,model,canonical,recent,half,n=16)
        y,_=simulate(s,poison,200,name,model,canonical,recent,half,n=16)
        causal[name]=int(np.max(abs(x-y)));assert np.array_equal(x,y)
    # Compare the inherited linearized prefix distribution against exact
    # nonlinear prefix propagation on three outcome-independent hash IDs.
    report=get(HERE/'EARLY_SCORES.json');checks={}
    ids=sorted(raw,key=lambda s:hashlib.sha256(s.encode()).hexdigest())[:3]
    for s in ids:
        a=raw[s];info=report['calibrations'][s]['200'];w0=np.array(info['w0']);prefix=subject(a[:200])
        jw=[];jh=[]
        for j in range(3):
            step=np.eye(3)[j]*1e-3
            up=model.sequence(prefix,w0+step)[2];dn=model.sequence(prefix,w0-step)[2]
            jw.append((up['w']-dn['w'])/2e-3);jh.append((up['h']-dn['h'])/2e-3)
        jw=np.stack(jw,axis=1);jh=np.stack(jh,axis=1)
        delta=np.random.default_rng(original_seed(s)+313).multivariate_normal(np.zeros(3),info['initial_covariance'],32)*info['endpoint_sd_cap_factor']
        linear=np.array(info['endpoint'])+delta@jw.T
        exact=np.stack([model.sequence(prefix,w0+d)[2]['w'] for d in delta])
        p=expit(linear@track.psych(np.array([-1,-.5,.5,1])).T)
        q=expit(exact@track.psych(np.array([-1,-.5,.5,1])).T)
        error=abs(p-q)
        checks[s]=dict(n_particles=32,mean_probability_error=float(error.mean()),p95_probability_error=float(np.quantile(error,.95)),
                       max_probability_error=float(error.max()),hidden_clipped_fraction=info['hidden_clipped_fraction'])
    save('EARLY_AUDIT.json',dict(utc=utc(),future_after200_poison_max_count_difference=causal,
          nonlinear_prefix_checks=checks,seconds=time.monotonic()-began,io=dict(IO),
          note='Inherited original Fisher/linearization prescription; small checked mean errors are not full initial-state posterior validation or neural source-parameter uncertainty.'))
    print('EARLY AUDIT',causal,checks,'seconds',time.monotonic()-began,flush=True)

from scipy.special import expit
if __name__=='__main__':main()
