"""Decision screen for one complete categorical path per randomized learner."""
from itertools import combinations, product
import resource
import time

import numpy as np
from scipy.optimize import brentq
from scipy.special import expit, ndtr, ndtri, xlogy

from source import BYTES, HERE, blob, check, get, save, utc

ALPHA = .05
REPS = 12000
SIZES = (64,240)
MODS = ('first','reactive','ordinary','composition_matched')


def solve(weights, logodds, target):
    check(0<target<1,'Degenerate assignment margin')
    offset = brentq(lambda s: weights@expit(logodds+s)-target, -120.,120.,xtol=1e-13)
    return expit(logodds+offset)


def center(p,q):
    # p,q are 2 arm distributions over 3^6 paths. Index blocks encode first choice.
    prior_first = [z.reshape(2,3,-1).sum(-1) for z in (p,q)]
    shared = (p+q).mean(0)/2
    shared_first = shared.reshape(3,-1).sum(-1)
    out = []
    for z,marginal in zip((p,q),prior_first):
        arm1_first = solve(shared_first,np.log(marginal[1]/marginal[0]),.5)
        full = z.reshape(2,3,-1)
        w = shared.reshape(3,-1)
        pr = np.stack([solve(mass/mass.sum(),np.log(s[1]/s[0]),a)
                       for s,mass,a in zip(full.transpose(1,0,2),w,arm1_first)])
        new = 2*np.stack([w*(1-pr),w*pr]).reshape(z.shape)
        check(np.max(np.abs(new.sum(1)-1))<2e-12,'Centered arm normalization')
        check(np.max(np.abs(new.mean(0)-shared))<2e-12,'Shared baseline check')
        out.append(new)
    return out


def collapse(z):
    return z.reshape(z.shape[:-1]+(3,-1)).sum(-1)


def kld(p,q):
    return float(np.mean(np.sum(xlogy(p,p)-xlogy(p,q),axis=-1)))


def bkl(p,q):
    return float(xlogy(p,p/q)+xlogy(1-p,(1-p)/(1-q)))


def bounds(forward,reverse):
    def get(a,b):
        near1 = 1-1e-12
        first = 1. if a>=bkl(near1,ALPHA) else brentq(lambda x:bkl(x,ALPHA)-max(0,a),ALPHA,near1)
        second = 1. if b>=bkl(ALPHA,near1) else brentq(lambda x:bkl(ALPHA,x)-max(0,b),ALPHA,near1)
        return min(first,second)
    return [get(forward,reverse),get(reverse,forward)]


def score_distributions(p,q,n,rng):
    lpq = np.log(p/q)
    out = []
    for z in (p,q):
        sums = np.zeros(2*REPS)
        for a in range(2):
            cdf = np.cumsum(z[a])
            cdf[-1] = 1.
            draws = rng.random((2*REPS,n//2))
            sums += lpq[a][np.searchsorted(cdf,draws)].sum(1)
        sums += 1e-10*rng.random(len(sums))
        out.append(sums)
    return out


def decisions(p,q,n,seed):
    xs,ys = score_distributions(p,q,n,np.random.default_rng(seed))
    hi = np.quantile(ys[:REPS],1-ALPHA)
    lo = np.quantile(xs[:REPS],ALPHA)
    size = [float((ys[REPS:]>hi).mean()),float((xs[REPS:]<lo).mean())]
    power = [float((xs[REPS:]>hi).mean()),float((ys[REPS:]<lo).mean())]
    return dict(size=size,power=power,mcse_conditional=[float(np.sqrt(p*(1-p)/REPS)) for p in power])


def compare(p_site,q_site,seed):
    p,q = p_site.mean(0),q_site.mean(0)
    known = np.array([[kld(x,y),kld(y,x)] for x,y in zip(p_site,q_site)])
    kl = [kld(p,q),kld(q,p)]
    mix = {str(n):dict(kl=np.array(kl)*n, bound=bounds(*(n*np.array(kl))),
                       **decisions(p,q,n,seed+n)) for n in SIZES}
    # Balanced fixed site and arm, generous known-site and known-point forecasts.
    # Site pairs kept together. All four distinct-site panels provide sensitivity.
    panels = np.array([bounds(*(known[list(panel)].mean(0)*240))
                       for panel in combinations(range(len(known)),4)])
    return dict(mixture=mix,site_kl_per_learner=known,
                equal_site_oracle_240=bounds(*(known.mean(0)*240)),
                four_site_oracle_240=np.quantile(panels,[0,.5,1],axis=0))


def measurement(mass,score):
    # mass has site, arm, full path. Fixed equal sites, balanced arms,
    # independent learners. Within-path variation comes from the entire law.
    mu = mass@score
    variance = mass@(score**2)-mu**2
    sigma = np.sqrt(2*variance.mean(0).sum())
    sig240 = sigma/np.sqrt(240)
    z = ndtri(.975)
    threshold = .10/sig240-z
    return dict(effect=float((mu[:,1]-mu[:,0]).mean()),site_effect=(mu[:,1]-mu[:,0]),
                typical_95_halfwidth_240=z*sig240,
                null_equiv_prob_10pp_margin=max(0.,float(2*ndtr(threshold)-1)),
                n80_detect_10pp_one_sided=int(np.ceil((sigma*(ndtri(.95)+ndtri(.80))/.10)**2)),
                n80_equiv_10pp_at_null=int(np.ceil((sigma*(z+ndtri(.90))/.10)**2)))


def serialize(x):
    if isinstance(x,np.ndarray):
        return x.tolist()
    if isinstance(x,dict):
        return {k:serialize(v) for k,v in x.items()}
    if isinstance(x,list):
        return [serialize(v) for v in x]
    return x


def main():
    t = time.monotonic()
    with np.load(HERE/'SEQUENCE_MASSES.npz',allow_pickle=False) as z:
        mats = z['joint']
        training = z['training']
        labs,ids,assays,actor,stress = [z[k] for k in ('labs','subjects','assays','actors','stresses')]
    BYTES['sequence_file'] += (HERE/'SEQUENCE_MASSES.npz').stat().st_size
    BYTES['sequence_decoded'] += mats.nbytes+training.nbytes
    sites = np.unique(labs)
    site_mat = np.array([mats[labs==s].mean(0) for s in sites])
    arm_mass = site_mat.mean(-2)
    paths = np.asarray(list(product([1,0,-1],repeat=6)))
    measures = {}
    model_pairs = [(i,j) for i in (0,1) for j in (3,2,4)]
    for h,scenario in enumerate(stress):
        for i,name in enumerate(actor):
            for k,protocol in enumerate(MODS[1:]):
                mass = arm_mass[:,h,i,k]
                correct = paths==-np.sign(assays[k])
                key = f'{scenario}:{name}:{protocol}'
                measures[key] = dict(first=measurement(mass,correct[:,0].astype(float)),
                                     mean_correct=measurement(mass,correct.mean(1)),
                                     mean_correct_trial_independent_counterfactual_sd=float(np.sqrt(
                                         np.mean((mass@correct.astype(float))*(1-mass@correct.astype(float)))/6)))
    scores = {}
    for h,scenario in enumerate(stress):
        for i,j in model_pairs:
            key = f'{scenario}:{actor[i]}:{actor[j]}'
            rows = {}
            for k,protocol in enumerate(MODS[1:]):
                p,q = arm_mass[:,h,i,k],arm_mass[:,h,j,k]
                pairs = [center(a,b) for a,b in zip(p,q)]
                pc,qc = np.asarray(pairs).transpose(1,0,2,3)
                seed = 183647+h*1813+i*503+j*59+k*7
                raw = compare(p,q,seed+4002)
                calibrated = compare(pc,qc,seed)
                halves = []
                for s in range(2):
                    u,v = np.asarray([center(a,b) for a,b in zip(site_mat[:,h,i,k,:,s],site_mat[:,h,j,k,:,s])]).transpose(1,0,2,3)
                    halves.append([kld(u.mean(0),v.mean(0))*240,kld(v.mean(0),u.mean(0))*240])
                rows[protocol] = dict(raw=raw,centered=calibrated,centered_half_kl_240=halves)
                if k==0:
                    rows['first'] = dict(raw=compare(collapse(p),collapse(q),seed+6534),
                                         centered=compare(collapse(pc),collapse(qc),seed+1189))
                else:
                    pc0,qc0 = np.asarray([center(a,b) for a,b in zip(arm_mass[:,h,i,0],arm_mass[:,h,j,0])]).transpose(1,0,2,3)
                    check(np.max(np.abs(collapse(pc)-collapse(pc0)))<3e-12 and
                          np.max(np.abs(collapse(qc)-collapse(qc0)))<3e-12,'Centered first response invariant')
            scores[key] = rows
            print('Scored',key,flush=True)
    null = np.array([[.4995,.001,.4995],[.4995,.001,.4995]])
    known = np.array([[.5994,.001,.3996],[.3996,.001,.5994]])
    controls = {str(n):dict(same_law=decisions(null,null,n,415493+n),
                           planted_20pp=decisions(known,null,n,420354+n)) for n in SIZES}
    save('SCREEN.json',serialize(dict(utc=utc(),reps_per_calibration_and_test=REPS,
         subjects=ids.tolist(), sites=sites.tolist(), assays=assays.tolist(), training_equal_site=np.array(
             [training[labs==s].mean(0) for s in sites]).mean(0),
         actors=actor.tolist(),stresses=stress.tolist(), scores=scores, measures=measures, controls=controls,
         seconds=time.monotonic()-t, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,io=dict(BYTES))))
    print('Saved screen',utc(),flush=True)


if __name__=='__main__':
    main()
