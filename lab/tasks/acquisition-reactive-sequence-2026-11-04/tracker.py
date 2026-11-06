"""Add a simple observation-driven score filter, scoped to the same site folds."""
import resource
import time

import numpy as np
from numba import njit
from scipy.special import expit

from calibrate import (HERE, PREFIX, STAGE, BYTES, prepare, design, response_stats, ternary,
                       check, get, save, utc)

GRID = (0., .04, .12, .24)
DECAY = .996
RETENTION = .85


def psych(x):
    z = np.tanh(5.*x)/np.tanh(5.)
    return np.stack([np.maximum(z,0), np.minimum(z,0), np.ones_like(z)],axis=-1)


@njit(cache=True)
def scan(x,c,day,base,eta):
    p = np.empty(len(c))
    state = np.zeros(3)
    endpoint = np.zeros(3)
    for i in range(len(c)):
        if day[i]:
            state *= RETENTION
        p[i] = 1/(1+np.exp(-max(-40.,min(40.,base[i]+np.sum(state*x[i])))))
        state *= DECAY
        if c[i]!=0:
            state += eta*((c[i]<0)-p[i])*x[i]
        if i==STAGE-PREFIX-1:
            endpoint = state.copy()
    return p,endpoint


def main():
    start = time.monotonic()
    report = get(HERE/'CALIBRATION.json')
    source = get(HERE/'SOURCE_MANIFEST.json')
    ids,labs = source['subjects'],source['labs']
    payload = HERE/'CAPPED_ROWS.npz'
    BYTES['capped_projection_file'] += payload.stat().st_size
    with np.load(payload,allow_pickle=False) as z:
        d = {s:prepare(z[s]) for s in ids}
    BYTES['capped_projection_decoded'] += sum(sum(x.nbytes for x in a.values()) for a in d.values())
    b = {s:design(d[s]) for s in ids}
    scores,starts,fit_grid = {},{},{}
    for lab in sorted(set(labs)):
        coeff = [np.asarray(x) for x in report['weights'][lab][2]]
        def inputs(s,stop):
            q = slice(PREFIX,stop)
            a = d[s]
            x = psych(a['x'][q])
            co = a['c'][q]
            day = a['day'][q]
            base = b[s]['offsets'][0][q]+b[s]['matrices'][2][0][q]@coeff[0]
            return x,co,day,base
        grid = []
        for train_lab in sorted(set(labs)-{lab}):
            ll = []
            for s,l in zip(ids,labs):
                if l!=train_lab:
                    continue
                inp = inputs(s,STAGE)
                ok = inp[1]!=0
                y = inp[1][ok]<0
                p = np.array([scan(*inp,e)[0][ok] for e in GRID])
                ll.append(-np.log(np.maximum(1e-10,np.where(y,p,1-p))).mean(1))
            grid.append(np.mean(ll,axis=0))
        mean = np.mean(grid,axis=0)
        eta = GRID[int(np.argmin(mean))]
        fit_grid[lab] = dict(eta=eta,other_site_loss=mean.tolist())
        for s,l in zip(ids,labs):
            if l!=lab:
                continue
            p,end = scan(*inputs(s,None),eta)
            q = expit(b[s]['offsets'][1][STAGE:]+b[s]['matrices'][2][1][STAGE:]@coeff[1])
            scores[s] = response_stats(d[s],ternary(p[STAGE-PREFIX:],q),report['selected_medium'])
            starts[s] = end.tolist()
    by_site = {l:float(np.mean([scores[s]['log_loss'] for s,k in zip(ids,labs) if k==l])) for l in sorted(set(labs))}
    var = []
    for subset in (ids,ids[:40],ids[40:]):
        block = np.sum([scores[s]['block'] for s in subset],axis=0)
        var.append(dict(variance_ratio=(block[:,0]/block[:,1]).tolist(),resid_adjacent=(block[:,2]/block[:,3]).tolist()))
    save('TRACK_CALIBRATION.json',dict(utc=utc(), grid=GRID, fit=fit_grid, site_loss=by_site,
         site_mean=float(np.mean(list(by_site.values()))),
         animal_mean=float(np.mean([s['log_loss'] for s in scores.values()])),
         dependence=var,start=starts,score=scores,seconds=time.monotonic()-start,
         peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,io=dict(BYTES)))
    print('Tracking complete',utc(),flush=True)


if __name__=='__main__':
    main()
