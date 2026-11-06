from pathlib import Path
import datetime as dt
import hashlib
from io import BytesIO
import json
import itertools
import math
import resource
import time
import numpy as np
from scipy.stats import binom, norm

C=Path(__file__).resolve().parent
SRC=C/'PILOT_ARRAYS.npz'
ALPHA=.05
SCALES=(64,240)
MODELS=('existing','session','growth','reinforce')
PAIRS=(('existing','growth'),('session','growth'),('existing','reinforce'),
       ('session','reinforce'),('existing','session'))
ENDPOINTS=([-1,1],[-.25,.25],[-.125,.125],[-.0625,.0625])
NAMES=('100','25','12.5','6.25')

def np_power(a,b,n,alpha=ALPHA):
    """Most-powerful randomized test at simple null a vs simple alternative b."""
    a=np.clip(a,1e-12,1-1e-12);b=np.clip(b,1e-12,1-1e-12)
    k=np.arange(n//2+1)
    pa=[binom.pmf(k,n//2,p) for p in a]
    pb=[binom.pmf(k,n//2,p) for p in b]
    # Order by log likelihood ratio. A common tie can be split at no power cost.
    ll=[binom.logpmf(k,n//2,q)-binom.logpmf(k,n//2,p) for p,q in zip(a,b)]
    order=np.argsort(-np.add.outer(*ll).ravel())
    u=np.multiply.outer(*pa).ravel()[order]; v=np.multiply.outer(*pb).ravel()[order]
    remaining=np.maximum(0,alpha-np.r_[0,np.cumsum(u[:-1])])
    test=np.minimum(u,remaining)
    f=np.divide(test,u,out=np.where(remaining>0,1.,0.),where=u>0)
    return dict(power=float(np.sum(f*v)),actual_size=float(test.sum()))

def midpoint(a,b,o):
    # Inputs [arm,signed_probe]; o shared between the two arms and hypotheses.
    da=a[...,0,:]-a[...,1,:]; db=b[...,0,:]-b[...,1,:]
    o=np.squeeze(o,axis=-2)
    need=np.maximum(np.abs(da),np.abs(db))/2
    m=(a.mean(-2)+b.mean(-2))/2
    n=np.clip(m,need,1-o-need)
    return (n[...,None,:]+np.stack([da,-da],axis=-2)/2,
            n[...,None,:]+np.stack([db,-db],axis=-2)/2,np.max(np.abs(n-m)))

def affinity(a,b,o):
    h=np.sqrt(a*b)+np.sqrt(np.maximum(0,1-o-a)*np.maximum(0,1-o-b))+o
    return -np.log(np.minimum(h,1))

def bound(d,n):
    return min(1.,ALPHA+math.sqrt(-math.expm1(-2*n*d)))

def min_n(d):
    return math.ceil(-math.log(1-(.8-ALPHA)**2)/(2*d)) if d>0 else None

def wts(labs):
    group, counts=np.unique(labs,return_counts=True)
    return np.array([1/(len(group)*counts[np.where(group==l)[0][0]]) for l in labs])

def avg(a,w):
    return np.einsum('i,i...->...',w,a)

def arms_idx(n):
    return slice(2*n,2*n+2)

def power_record(a,b,o):
    ac,bc,shift=midpoint(a,b,o)
    return dict(midpoint_clip=shift,exact={
        name:{str(n):{'a_null':np_power(aa,bb,n),'b_null':np_power(bb,aa,n)}
            for n in SCALES}
        for name,(aa,bb) in zip(NAMES,zip(ac.reshape(2,4,2).mean(-1).T,bc.reshape(2,4,2).mean(-1).T))})

def group_bound(a,b,o,labs,w):
    ast,bst,shift=midpoint(a,b,o)
    centered_arm=affinity(ast,bst,o)
    centered=centered_arm.mean(-2)
    iid=-np.log(avg(np.exp(-centered_arm),w)).mean(0)
    uncentered=affinity(a,b,o).mean(-2)
    common=avg(centered,w)
    un=avg(uncentered,w)
    # The best single common probe (or upper bound for any common mixture),
    # and a still more permissive design with individualized preassignment probes.
    d=float(common.max()); d_choice=float(avg(centered.max(-1),w))
    return dict(max_per_learner_d=d,oracle_per_cell_probe_d=d_choice,
                common_probe_index=int(common.argmax()),
                exact100_d=float(common[:2].mean()),
                per_signed_d=common.tolist(),
                power_bound_240=bound(d,240),oracle_per_cell_probe_bound_240=bound(d_choice,240),
                optimistic_n80_floor=min_n(d),iid_common_probe_bound_240=bound(max(0.,float(iid.max())),240),uncentered_power_bound_240=bound(float(un.max()),240),
                max_midpoint_clip=float(shift))

def pair_result(mean,omit,labs,inds,aa,bb):
    a=mean[inds,aa];b=mean[inds,bb];o=omit[inds,None,None]
    l=labs[inds];w=wts(l)
    ag,bg,og=avg(a,w),avg(b,w),avg(o,w)
    avs=ag[0]-ag[1]; bvs=bg[0]-bg[1]; gap=avs-bvs
    by=np.unique(l)
    ai=np.asarray([a[l==s].mean(0) for s in by]);bi=np.asarray([b[l==s].mean(0) for s in by])
    oi=np.asarray([o[l==s].mean(0) for s in by])
    wa=np.ones(len(by))/len(by)
    return dict(gap_signed=gap.tolist(),gap_equal_side=gap.reshape(4,2).mean(-1).tolist(),
        max_abs_gap=float(np.max(np.abs(gap))),gap_over_3pp=np.maximum(0,np.abs(gap)-.03).tolist(),
        both_forecasts_compatible_with_3pp_between_model_shift=bool(np.max(np.abs(gap))<=.03),
        pooled=group_bound(ag[None],bg[None],og[None],np.array(['pooled']),np.ones(1)),
        site=group_bound(ai,bi,oi,by,wa),
        context_oracle=group_bound(a,b,o,l,w),
        **power_record(ag,bg,og))

def model_result(part,cond,train,omit,labs,idx):
    arr=part[idx]; cf=cond[idx]; tr=train[idx]; o=omit[idx]
    ll=labs[idx];w=wts(ll)
    delta=arr[:,0]-arr[:,1]
    cdelta=cf[:,0]-cf[:,1]
    base = avg(delta.mean(1),w)
    eq = delta.reshape(len(ll),delta.shape[1],4,2).mean(-1)
    dev = np.sqrt(np.einsum('i,ij->j',w*w,eq.var(1,ddof=1)/eq.shape[1]))
    by={s:delta[ll==s].mean((0,1)).tolist() for s in sorted(set(ll))}
    loo={s:avg(delta[ll!=s].mean(1),wts(ll[ll!=s])).tolist() for s in sorted(set(ll))}
    # The floor prevents an impossible negative omission rate; positive shift
    # for an arm always causes a competence-scaled drop in correct share.
    op=np.minimum(1.,o+.015); om=np.maximum(0.,o-.015)
    low=avg((cf[:,0]*(1-op[...,None])-cf[:,1]*(1-om[...,None])).mean(1),w)
    high=avg((cf[:,0]*(1-om[...,None])-cf[:,1]*(1-op[...,None])).mean(1),w)
    return dict(n=int(idx.sum()),lab_n={s:int(np.sum(ll==s)) for s in by},terminal_accuracy=avg(arr.mean(2),w).tolist(),
        training_correct_omission_and_hard_share=avg(tr.mean(-1),w).tolist(),
        terminal_omit=float(avg(o.mean(1),w)),delta=base.tolist(),
        delta_conditional=avg(cdelta.mean(1),w).tolist(),
        delta_equal_side=base.reshape(4,2).mean(-1).tolist(),
        mcse_equal_side=dev.tolist(),half_draw_delta_equal_side=[
            avg(a.mean(1),w).tolist() for a in np.split(eq,2,axis=1)],
        animal_delta_equal_side_quantiles=np.quantile(eq.mean(1),[.1,.5,.9],axis=0).tolist(),
        by_lab=by,leave_one_lab_out=loo,terminal_omit_stress_signed=[low.tolist(),high.tolist()])

def min_effect_n(gap):
    for n in range(2,5001,2):
        # Under fixed symmetric arm probabilities, sum successes in the plus
        # arm and failures in the minus arm is binomial with common p.
        cutoff=int(binom.isf(ALPHA,n,.5))
        at=binom.sf(cutoff,n,.5)
        frac=(ALPHA-at)/binom.pmf(cutoff,n,.5)
        q=.5+gap/2
        pw=binom.sf(cutoff,n,q)+frac*binom.pmf(cutoff,n,q)
        if pw>=.8:
            return n

def main():
    tick=time.perf_counter()
    f=SRC.read_bytes()
    with np.load(BytesIO(f),allow_pickle=False) as z:
        dat={k:z[k] for k in z.files}
    correct=dat['correct'].astype(np.float64); cond=dat['conditional_correct']; tr=dat['training']; om=dat['terminal_omit']
    labs=dat['labs']; rosters={'all64':np.ones(64,dtype=bool),'historical40':np.arange(64)<40,'later24':np.arange(64)>=40}
    result={}
    for t,g,x in itertools.product(range(2),range(2),range(2)):
        key=':'.join([str(dat['starts'][t]),str(dat['engagement'][g]),('order','composition')[x]])
        arc=correct[:,t,g,:,arms_idx(x)]
        con=cond[:,t,g,:,arms_idx(x)]
        trc=tr[:,t,g,:,:,arms_idx(x)]
        obs=om[:,t,0]
        assert np.array_equal(om[:,t,0],om[:,t,1]) and np.array_equal(om[:,t,0],om[:,t,2])
        mean=arc.mean(axis=3)
        out={}
        for name,sel in rosters.items():
            block={}
            for i,k in enumerate(MODELS):
                if np.all(dat['valid'][sel,i]):
                    block[k]=model_result(arc[:,i],con[:,i],trc[:,i],obs,labs,sel)
            block['pairs']={}
            for a,b in PAIRS:
                if a in block and b in block:
                    block['pairs'][a+':'+b]=pair_result(mean,obs.mean(1),labs,sel,MODELS.index(a),MODELS.index(b))
            # Convex mixtures of exposure and history as a descriptive simpler
            # rival. A single mixing coefficient must cover all signed probes.
            if 'reinforce' in block:
                s=np.asarray(block['reinforce']['delta'])
                e=np.asarray(block['growth']['delta'])
                w=np.linspace(0,1,1001)
                block['simple_mixture_signed_distance']={}
                for k in ('existing','session'):
                    x0=np.asarray(block[k]['delta'])
                    d=np.max(np.abs(x0-(e+w[:,None]*(s-e))),axis=1)
                    block['simple_mixture_signed_distance'][k]=dict(max_abs_signed_gap=float(d.min()),reinforce_weight=float(w[d.argmin()]))
            out[name]=block
        result[key]=out
    controls={}
    for n,gap in itertools.product(SCALES,(0.,.10,.20)):
        a=np.array([.5,.5]); b=a+np.array([gap,-gap])/2
        p=np_power(a,b,n); q=np_power(b,a,n)
        assert abs(p['actual_size']-ALPHA)<1e-10 and abs(q['actual_size']-ALPHA)<1e-10
        if gap==0:assert abs(p['power']-ALPHA)<1e-10 and abs(q['power']-ALPHA)<1e-10
        controls[f'N{n}_gap{gap}']=dict(no_effect_null=p,known_effect_null=q)
    control_sizes={str(g):dict(exact_n80_vs_no_effect=min_effect_n(g),near_half_n95_halfwidth=math.ceil((norm.ppf(.975)/g)**2),
                      near_half_n80_equivalence_TOST=math.ceil(((norm.ppf(.95)+norm.ppf(.9))/g)**2))
                   for g in (.05,.10,.20)}
    # Worked equality case for affinity and monotonicity.
    a=np.array([.4,.6]);o=.1
    assert np.max(np.abs(affinity(a,a,o)))<1e-12
    assert abs(bound(0,240)-ALPHA)<1e-12 and bound(.001,240)>bound(.0001,240)
    ru=resource.getrusage(resource.RUSAGE_SELF)
    out=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),sha256=hashlib.sha256(f).hexdigest(),
             probe=dat['probe'].tolist(),controls=controls,control_sizes=control_sizes,results=result,
             resource=dict(bytes_read=len(f),decoded_bytes=sum(x.nbytes for x in dat.values()),
                peak_rss_bytes=ru.ru_maxrss,seconds=time.perf_counter()-tick))
    (C/'SCREEN.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print('Saved fixed reduction',out['utc'],out['resource'],flush=True)

if __name__=='__main__':main()
