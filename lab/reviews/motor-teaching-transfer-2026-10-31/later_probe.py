"""Postvalidation, predeclared h=1,2,3,5 common stationary endpoint check."""
import reconstruct as r
import hashlib
import json
import resource
import warnings
from collections import Counter
import numpy as np
from threadpoolctl import threadpool_limits

def windows(rr, tsay, h):
    result=[]
    for k in range(2,len(rr)-h):
        a=rr[k];last=rr[k+h]
        if not r.core(a,tsay) or not r.valid(a) or not r.valid(last):
            continue
        if last['j'] or last['f'] or abs(last['c'])!=4:
            continue
        if any(not r.core(v,tsay) or r.portion(v,tsay)!=r.portion(a,tsay) for v in rr[k-2:k]):
            continue
        if tsay and any(not r.core(v,True) or r.portion(v,True)!=r.portion(a,True) for v in rr[k:k+h+1]):
            continue
        if not tsay and last['t']>904:
            continue
        result.append([rr[k],rr[k+h],rr[k-1],rr[k-2],rr[k+1:k+h]])
    return result

def fit(entries, cells, tsay, h, synthetic=None):
    columns=[np.ones((len(entries),1)),r.indicators([r.cell(v[0]) for v in entries],cells),
             np.array([[v[1]['c']/4] for v in entries])]
    for i in (2,3):
        columns.append(r.indicators([r.cell(v[i]) for v in entries],cells))
    block=[r.portion(v[0],tsay) for v in entries]
    columns.append(r.indicators(block,list(range(4))))
    first,stride,den=(101,181,180) if tsay else (104,200,200)
    columns.append(np.array([[(v[0]['t']-first)%stride/den-.5] for v in entries]))
    for lag in range(h-1):
        columns.append(r.indicators([r.cell(v[4][lag]) for v in entries],cells))
    X=np.concatenate(columns,axis=1)
    y=np.array([v[1]['h'] if synthetic is None else synthetic[v[1]['t']] for v in entries])
    coef,_,rank,sv=np.linalg.lstsq(X,y,rcond=None)
    C=np.r_[coef[1:len(cells)],0.]
    residual=y-np.einsum('ni,i->n',X,coef)
    counts=Counter(r.cell(v[0]) for v in entries)
    return dict(n=len(y),rank=int(rank),columns=X.shape[1],full_rank=bool(rank==X.shape[1]),
                max_normal_residual=float(abs(np.einsum('ni,n->i',X,residual)).max()),
                condition_number=float(sv[0]/sv[-1]),effects=r.effects(C,cells),
                min_current_cell_n=min(counts.get(c,0) for c in cells))

def finite_summary(v):
    arr=np.asarray(v)
    out=r.summary(v)
    bm=arr[r.RNG.integers(len(arr),size=(6000,len(arr)))].mean(axis=1)
    out['stationary_bootstrap95']=np.quantile(bm[:,0],[.025,.975]).tolist()
    out['jump_to_bootstrap95']=np.quantile(bm[:,1],[.025,.975]).tolist()
    out['bootstrap_stationary_nonpositive_fraction']=float(np.mean(bm[:,0]<=0))
    return out

def main():
    manifest=r.load_json(r.AUTHOR/'SOURCE_MANIFEST.json')
    expected={v['local']:v for v in manifest['reused_pinned_csvs']}
    raw=[]
    for name in (r.FILES[0],r.FILES[2]):
        by,cells,meta=r.decode(name,expected[name]);raw.append((name,by,cells,meta))
    earlier=r.load_json(r.HERE/'CONTRARY.json')
    horizons=[]
    for h in (1,2,3,5):
        groups=[]
        for si,(name,by,cells,meta) in enumerate(raw):
            tsay=si==0;people=[]
            for p,rr in sorted(by.items()):
                people.append(dict(person=p,**fit(windows(rr,tsay,h),cells,tsay,h)))
            v=[[p['effects'][c] for c in ('No Jump','Jump To')] for p in people]
            groups.append(dict(source=name,people=people,summary=finite_summary(v)))
        comparison=r.comparison(groups[0]['summary']['per_person'],groups[1]['summary']['per_person'])
        horizons.append(dict(horizon=h,groups=groups,comparison=comparison))
    h1error=max(abs(horizons[0]['comparison'][k]-earlier['stationary_next_endpoint_comparison'][k])
                for k in ('Tsay_ratio','Figure3_ratio','ratio_shift','paired_MSE_gain'))
    assert h1error<1e-12
    # Exact generator proof on actual Figure3 schedules; nuisance expression is only one lag.
    name,by,cells,meta=raw[1]
    p,rr=next(iter(sorted(by.items())))
    U={c:-np.sign(c[0])*(.8 if c[1]==c[0] else 1.) for c in cells}
    V={c:np.sign(c[0])*.5 if c[1]==c[0] else 0. for c in cells}
    # At each endpoint, the stored state includes inputs strictly before this endpoint.
    state=0.;previous=0.;synthetic={};true_state={}
    for row in rr:
        key=r.cell(row)
        if key not in U:
            U[key]=0.;V[key]=0.
        synthetic[row['t']]=state+previous
        true_state[row['t']]=state
        state+=U[key];previous=V[key]
    algebra_error=0.
    for a,b,old in zip(rr[1:-1],rr[2:],rr[:-2]):
        observed=synthetic[b['t']]-synthetic[a['t']]
        wanted=U[r.cell(a)]+V[r.cell(a)]-V[r.cell(old)]
        algebra_error=max(algebra_error,abs(observed-wanted))
    # Isolate the observation-only component: it survives first endpoint, but not later
    # endpoints once the intervening and previous cells are represented.
    expression={t:synthetic[t]-true_state[t] for t in synthetic}
    recovery=[]
    for h in (1,2,3,5):
        fitout=fit(windows(rr,False,h),cells,False,h,synthetic=expression)
        recovery.append(dict(horizon=h,**fitout))
    record=dict(created_utc=r.now(),plan_amendment_sha256=hashlib.sha256(r.read(r.HERE/'CONTRARY_AMENDMENT.md')).hexdigest(),
                horizons=horizons,h1_max_previous_error=h1error,
                transient_expression_generator=dict(source=name,person=p,
                    equation='H_t=x_t+V(input_tminus1); x_tplus1=x_t+U(input_t)',
                    true_stationary_response=1.,true_jump_to_response=.8,
                    expression_only_jump_to_response=-.5,
                    max_algebra_error=algebra_error,expression_component_recovery=recovery),
                interpretation='Later common-endpoint conditional effects; not unique storage, perception, retention or randomized causal effects.')
    r.record('LATER_PROBE.json',record)
    r.record('LATER_RUN.json',dict(finished_utc=r.now(),read_passes=r.READS,
                                 charged_bytes=sum(v['charged_bytes'] for v in r.READS),
                                 peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,jobs_running_at_exit=0))
    print(json.dumps(dict(h1error=h1error,horizons=[dict(horizon=v['horizon'],
                          qA=v['comparison']['Tsay_ratio'],qF=v['comparison']['Figure3_ratio'],
                          shift=v['comparison']['ratio_shift'],ci=v['comparison']['conditional_bootstrap_shift95'],
                          groups=[dict(stationary=g['summary']['stationary'],jump=g['summary']['jump_to'],
                                       station95=g['summary']['stationary_bootstrap95'],jump95=g['summary']['jump_to_bootstrap95'],
                                       denominator_nonpositive=g['summary']['bootstrap_stationary_nonpositive_fraction'],
                                       n=sum(p['n'] for p in g['people']),fullrank=all(p['full_rank'] for p in g['people'])) for g in v['groups']]) for v in horizons],
                          transient_generator_recovery=[dict(horizon=q['horizon'],effects=q['effects']) for q in recovery],
                          charge=sum(v['charged_bytes'] for v in r.READS),peak_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)

if __name__=='__main__':
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        with threadpool_limits(limits=1):
            main()
        r.record('LATER_WARNINGS.json',dict(warnings=[dict(message=str(w.message),file=w.filename,line=w.lineno) for w in caught]))
