"""Forward, leave-whole-site-out ternary calibration on the capped projection."""
import hashlib
import math
from pathlib import Path
import resource
import sys
import time

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logit

from source import HERE, OLD, REV, ROOT, blob, check, get, reference, save, utc, BYTES

PREFIX = 1000
STAGE = 2000
MID = .25
FALLBACK = .5
FAST = .78
SLOW = .98
ACTORS = ('static','drift','history','existing','session')


def prepare(a):
    x = np.nan_to_num(a[:,1])-np.nan_to_num(a[:,0])
    c, r, volume, prob = a[:,2:6].T
    return dict(x=x, c=c, r=r, volume=volume, prob=prob, day=a[:,6].astype(bool))


def signed_basis(x):
    # A low-contrast ramp and distinct side-specific high-contrast offsets.
    x = np.asarray(x)
    z = np.tanh(5*x)/np.tanh(5.)
    low = np.minimum(np.abs(x)/.25,1.)
    return np.stack([np.ones_like(x), np.maximum(z,0), np.minimum(z,0),
                     low*(x>0), -low*(x<0), (np.abs(x)>=.99)*np.sign(x)],axis=-1)


def omission_basis(x):
    x = np.asarray(x)
    return np.stack([np.ones_like(x), np.sign(x), 1-np.abs(x), np.abs(x)<=.125],axis=-1)


def signal(x,c,r):
    direction = -c
    return np.stack([direction*(r>0), direction*((c!=0)&(r<=0)), (c==0),
                     (r>0), 1-np.abs(x)],axis=-1).astype(float)


def summarize_history(x,c,r,day):
    traces = np.zeros((len(x),3,5))
    pos = np.zeros(len(x),int)
    state = np.zeros((3,5))
    events = signal(x,c,r)
    for t,event in enumerate(events):
        if day[t]:
            state[:2] = 0
        elif t:
            pos[t] = pos[t-1]+1
        traces[t] = state
        state[0] = event
        state[1] = FAST*state[1]+(1-FAST)*event
        state[2] = SLOW*state[2]+(1-SLOW)*event
    return traces,pos,state


def predictors(x, t, pos, trace):
    x, t, pos = np.broadcast_arrays(x,t,pos)
    one = np.ones_like(x)
    mag = np.abs(x)
    difficulty = 1-mag
    age = 1-np.exp(-np.maximum(0,t-PREFIX)/800.)
    progress = np.log1p(np.minimum(pos,800)/50.)
    first = np.exp(-pos/5.)
    drift = np.stack([age,age*np.sign(x),age*x,first,progress],axis=-1)
    xb = signed_basis(x)
    ob = omission_basis(x)
    x0 = np.column_stack((xb, one*(mag==.5), one*(mag==.25), one*(mag<=.125)))
    z0 = np.column_stack((ob, one*(mag==.5), one*(mag==.25)))
    x1 = np.column_stack((x0,drift))
    z1 = np.column_stack((z0,drift))
    traceflat = trace.reshape(len(x),-1)
    reward_choice = trace[:,0,0]
    no_reward_choice = trace[:,0,1]
    rew = trace[:,0,3]
    last_diff = trace[:,0,4]
    x2 = np.column_stack((x1,traceflat,difficulty*reward_choice,difficulty*no_reward_choice,
                          last_diff*reward_choice,last_diff*no_reward_choice,x*rew))
    z2 = np.column_stack((z1,traceflat,difficulty*trace[:,0,2],difficulty*trace[:,1,2]))
    return [(x0,z0),(x1,z1),(x2,z2)]


def fit(x,y,offset,penalty):
    x = np.ascontiguousarray(x)
    offset = np.broadcast_to(offset,y.shape)
    def f(w):
        a = x@w+offset
        loss = np.logaddexp(0,a)-y*a
        grad = x.T@(expit(a)-y)
        return float(loss.sum()+.5*np.sum(penalty*w*w)),grad+penalty*w
    res = minimize(f,np.zeros(x.shape[1]),jac=True,method='L-BFGS-B',options=dict(maxiter=250,ftol=1e-11))
    check(res.success and np.isfinite(res.x).all(), f'Logit failed {res.message}')
    return res.x


def binary_offsets(x,b):
    return signed_basis(x)@b[0],omission_basis(x)@b[1]


def design(d):
    x,c,r,day = [d[k] for k in ('x','c','r','day')]
    pref = np.arange(PREFIX)
    responds = c[pref]!=0
    bx = fit(signed_basis(x[pref][responds]),(c[pref][responds]<0).astype(float),0,
             np.array([.5,1,1,2,2,4]))
    bz = fit(omission_basis(x[pref]),(c[pref]==0).astype(float),-4,np.array([2,4,4,4]))
    bz[0] -= 4
    tr,pos,_ = summarize_history(x,c,r,day)
    offsets = binary_offsets(x,(bx,bz))
    matrices = predictors(x,np.arange(len(x)),pos,tr)
    return dict(matrices=matrices, offsets=offsets, base=(bx,bz), traces=tr,pos=pos)


def ternary(p,q):
    return np.column_stack(((1-q)*(1-p),q,(1-q)*p))


def recurrent(rows,ids):
    # Pin this exact model/reference implementation. No actor fit.
    import importlib.util
    p = HERE.parent/'acquisition-probe-design-2026-11-04/pilot.py'
    blob(p,'febcc48d80ee5163ce58d1735e470a597382f4931e627e4664feb5cb32e94c02')
    spec = importlib.util.spec_from_file_location('archive',p)
    pilot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pilot)
    models = pilot.model_load()
    ref = get(REV/'artifacts/source_comparison/RESULT.json',
              'cc8b1aedffb9c495d20b059f9c779a8f8762e7abc7500adb40838fb9bb7dab91')
    archived = {x['path']:x for x in ref['forecast_records']}
    probs = {}
    states = {}
    for s in ids:
        d = rows[s]
        a = dict(contrastLeft=np.maximum(0,-d['x']),contrastRight=np.maximum(0,d['x']),
                 choice=d['c'],feedbackType=d['r'],session_start=d['day'])
        probs[s],states[s] = {},{}
        for name in ('existing','session'):
            path = REV/'artifacts/source_comparison'/s/(name+'.json')
            rec = get(path)
            pin = archived[str(path.with_suffix('.npz').relative_to(ROOT))]['sha256']
            check(rec['forecast_sha256']==pin and rec['freeze_sha256']==ref['comparison_freeze_sha256'],
                  'Historical state provenance')
            cal = rec['calibration']
            initial = dict(w=np.asarray(cal['endpoint']),h=np.asarray(cal['hidden_endpoint']))
            model = models[name]
            pre = {k:v[PREFIX:STAGE] for k,v in a.items()}
            test = {k:v[STAGE:] for k,v in a.items()}
            _,_,state = model.sequence(pre,initial)
            q,_,_ = model.sequence(test,state)
            probs[s][name] = q
            cov = np.asarray(cal['endpoint_covariance'])
            # This is the archived covariance at 1000. It supplies a sensitivity scale
            # at 2000 rather than a posterior over that later continuation.
            states[s][name] = dict(w=state['w'].tolist(),h=state['h'].tolist(),cov=cov.tolist())
    return probs,states,dict(pilot.D)


def fit_fold(ids, rows, ds):
    coeff = []
    for k in range(3):
        z = []
        for j in range(2):
            xx,yy,oo = [],[],[]
            for s in ids:
                choice = rows[s]['c'][PREFIX:STAGE]
                mask = choice!=0 if j==0 else np.ones(len(choice),bool)
                yy.append((choice[mask]<0 if j==0 else choice[mask]==0).astype(float))
                xx.append(ds[s]['matrices'][k][j][PREFIX:STAGE][mask])
                oo.append(ds[s]['offsets'][j][PREFIX:STAGE][mask])
            z.append(fit(np.concatenate(xx),np.concatenate(yy),np.concatenate(oo),12.))
        coeff.append(z)
    return coeff


def response_stats(d, pred, m):
    a = slice(STAGE,None)
    c,x = d['c'][a],d['x'][a]
    day = d['day'][a]
    y = (1-c).astype(int)
    pp = np.clip(pred[np.arange(len(y)),y],1e-10,1)
    pc = np.where(x==0,0.,np.where(x>0,pred[:,2],pred[:,0]))
    is_correct = (c==-np.sign(x))&(x!=0)
    res = np.stack([is_correct-pc, (c==0)-pred[:,1],
                    (c<0)-pred[:,2]],axis=1)
    pr = np.stack([pc,pred[:,1],pred[:,2]],axis=1)
    vv = pr*(1-pr)
    # Exact disjoint 6-slot within-session blocks, no retrospective conditioning
    # on their subsequent stimuli when predicting individual outcomes.
    spans = np.r_[0,np.flatnonzero(day[1:])+1,len(c)]
    block_moments = np.zeros((3,4))
    for i,j in zip(spans[:-1],spans[1:]):
        t = i+(j-i)//6*6
        b = res[i:t].reshape(-1,6,3)
        block_moments[:,0] += np.sum(b.sum(axis=1)**2,axis=0)
        block_moments[:,1] += np.sum(vv[i:t],axis=0)
        block_moments[:,2] += np.sum(b[:,1:]*b[:,:-1],axis=(0,1))
        block_moments[:,3] += np.sum(np.sqrt(vv[i:t].reshape(-1,6,3)[:,1:] *
                                            vv[i:t].reshape(-1,6,3)[:,:-1]),axis=(0,1))
    cells = {}
    for signed in (-1.,-m,m,1.):
        k = x==signed
        if k.any():
            cells[str(signed)] = [int(k.sum()),float(res[k,0].sum()),float(res[k,1].sum())]
    return dict(n=len(c),log_loss=float(-np.log(pp).mean()),bias=res.mean(0).tolist(),
                block=block_moments.tolist(),cells=cells)


def support(rows,ids,labs):
    out = {}
    for m in (MID,FALLBACK):
        cell = {}
        for sign in (-1,1):
            counts, sites = [],set()
            yes,no = 0,0
            for s,lab in zip(ids,labs):
                d = rows[s]
                select = d['x'][1600:2400]==sign*m
                n = select.sum()
                counts.append(int(n))
                if n>=10:
                    sites.add(lab)
                reward = d['r'][1600:2400][select]>0
                c = d['c'][1600:2400][select]
                yes += int(reward.sum())
                no += int(((~reward)&(c!=0)).sum())
            cell[str(sign)] = dict(animals_ge10=sum(n>=10 for n in counts),sites_ge10=sorted(sites),
                                   rewards=yes,incorrect_responses=no,opportunities=sum(counts))
        out[str(m)] = cell
    choose = next((m for m in (MID,FALLBACK) if all(c['animals_ge10']>=24 and len(c['sites_ge10'])>=5
                 and min(c['rewards'],c['incorrect_responses'])>0 for c in out[str(m)].values())),None)
    return out,choose


def stage_support(rows,m):
    report = {}
    sequences = [[1,-m,-1,m,-1,1],[1,-1,1,-1,1,-1],[1,-1,1,-1,-m,m]]
    for a,b in ((1600,2000),(2000,2400),(2000,4000)):
        stats = dict(n=0,per_animal=[],feedback_disagreements=0,zero=0,volume_available=0,
                     volumes={},animals_exact=[0]*3,exact=[0]*3,prob_half=0,contrast_counts={},
                     two_medium=0,same_session_windows=0)
        for s,d in rows.items():
            x,c,r,v,prob,day = [d[k][a:b] for k in ('x','c','r','volume','prob','day')]
            stats['n'] += len(x)
            nz = x!=0
            stats['zero'] += int((~nz).sum())
            stats['feedback_disagreements'] += int(((r>0)!=(c==-np.sign(x)))[nz].sum())
            stats['prob_half'] += int((prob==.5).sum())
            stats['volume_available'] += int(np.isfinite(v).sum())
            for value,n in zip(*np.unique(v[(r>0)&np.isfinite(v)],return_counts=True)):
                k = str(round(float(value),4))
                stats['volumes'][k] = stats['volumes'].get(k,0)+int(n)
            for value,n in zip(*np.unique(x,return_counts=True)):
                k = str(round(float(value),6))
                stats['contrast_counts'][k] = stats['contrast_counts'].get(k,0)+int(n)
            stats['per_animal'].append(float(np.mean(np.abs(x)==m)))
            xwin = np.lib.stride_tricks.sliding_window_view(x,6)
            within = ~np.lib.stride_tricks.sliding_window_view(day,6)[:,1:].any(1)
            stats['same_session_windows'] += int(within.sum())
            stats['two_medium'] += int(((np.abs(xwin)==m).sum(1)>=2)[within].sum())
            for k,seq in enumerate(sequences):
                n = int(((xwin==seq).all(1)&within).sum())
                stats['exact'][k] += n
                stats['animals_exact'][k] += int(n>0)
        stats['medium_quantiles'] = np.quantile(stats.pop('per_animal'),[0,.1,.25,.5,.75,.9,1]).tolist()
        report[f'{a}:{b}'] = stats
    return report


def main():
    t = time.monotonic()
    src = get(HERE/'SOURCE_MANIFEST.json')
    run = get(HERE/'SOURCE_ALL_EXECUTION.json')
    ids,labs = src['subjects'],src['labs']
    payload = HERE/'CAPPED_ROWS.npz'
    BYTES['capped_projection_file'] += payload.stat().st_size
    with np.load(payload,allow_pickle=False) as z:
        check(z.files==ids,'Projection roster')
        raw = {s:z[s] for s in ids}
    BYTES['capped_projection_decoded'] += sum(a.nbytes for a in raw.values())
    check({s:len(a) for s,a in raw.items()}==run['rows'],'Projection counts')
    rows = {s:prepare(raw[s]) for s in ids}
    support_cells,m = support(rows,ids,labs)
    audit = stage_support(rows,m or FALLBACK)
    ds = {s:design(d) for s,d in rows.items()}
    rec,starts,modelio = recurrent(rows,ids)
    score = {}
    weights = {}
    start = {}
    for site in sorted(set(labs)):
        train = [s for s,lab in zip(ids,labs) if lab!=site]
        test = [s for s,lab in zip(ids,labs) if lab==site]
        params = fit_fold(train,rows,ds)
        weights[site] = [[v.tolist() for v in z] for z in params]
        for s in test:
            d,designs = rows[s],ds[s]
            score[s] = {}
            primary_omit = None
            for k,name in enumerate(ACTORS):
                if k<3:
                    mat = designs['matrices'][k]
                    p,q = [expit(designs['offsets'][j][STAGE:]+mat[j][STAGE:]@params[k][j]) for j in range(2)]
                    if name=='history':
                        primary_omit = q
                else:
                    p,q = rec[s][name],primary_omit
                score[s][name] = response_stats(d,ternary(p,q),m or FALLBACK)
            _,_,tr = summarize_history(*(d[k][:STAGE] for k in ('x','c','r','day')))
            start[s] = dict(base=[b.tolist() for b in designs['base']], traces=tr.tolist(), recurrent=starts[s])
        print('Calibrated',site,'test animals',len(test),flush=True)
    reductions = {}
    for name in ACTORS:
        losses = np.array([score[s][name]['log_loss'] for s in ids])
        ls = {lab:float(losses[np.asarray(labs)==lab].mean()) for lab in sorted(set(labs))}
        blocks = [np.sum([score[s][name]['block'] for s in subset],axis=0) for subset in (ids,ids[:40],ids[40:])]
        dep = [dict(variance_ratio=(b[:,0]/b[:,1]).tolist(),resid_adjacent=(b[:,2]/b[:,3]).tolist()) for b in blocks]
        cells = {}
        for x in (-1.,-(m or FALLBACK),m or FALLBACK,1.):
            k = str(x)
            vals = np.array([score[s][name]['cells'][k] for s in ids if k in score[s][name]['cells']])
            cells[k] = dict(n=int(vals[:,0].sum()),opportunity_bias=(vals[:,1:].sum(0)/vals[:,0].sum()).tolist(),
                            animal_equal_bias=(vals[:,1:]/vals[:,0,None]).mean(0).tolist())
        reductions[name] = dict(animal_mean=float(losses.mean()),site_mean=float(np.mean(list(ls.values()))),
                                site_loss=ls,cells=cells,dependence=dep)
    save('CALIBRATION.json',dict(utc=utc(),fit_rows=[1000,2000],evaluation_start=2000,
                                 support=support_cells,selected_medium=m,stage_support=audit,summary=reductions,
                                 per_animal=score,weights=weights,start=start,io=dict(BYTES),model_io=modelio,
                                 seconds=time.monotonic()-t,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print('Saved calibration',utc(),flush=True)


if __name__=='__main__':
    main()
