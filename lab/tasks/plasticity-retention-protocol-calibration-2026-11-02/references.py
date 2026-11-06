"""Independent exact-scalar GnT, gradient, reservoir and scoring references."""
from collections import Counter, OrderedDict
from fractions import Fraction as Q
import itertools
import json
import math
from pathlib import Path
import resource
import time
import traceback

from engine import ExactCache, Learner, Reservoir, pack_input, support_risk

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / 'plasticity-retention-source-benchmark-2026-11-02'


def exact_gnt(weights, utility, activity, ages, features, rate, draw, new_weights,
              random_scores=None):
    """Separate rational, per-neuron reading of pinned GnT operations."""
    w, u, m, age = weights[:], utility[:], activity[:], ages[:]
    corrected = [Q(0)]*5
    if rate == 0:
        return dict(theta=w, util=u, mean=m, ages=age, chosen=[], butil=corrected, accumulated=Q(0))
    for n in range(5):
        age[n] += 1
        b = 1-Q(99,100)**age[n]
        m[n] = Q(99,100)*m[n] + features[n]/100
        incoming_magnitude = sum(abs(w[n*21+i]) for i in range(20))/20
        value = (abs(w[105+n]) * abs(features[n]-m[n]/b)/incoming_magnitude
                 if random_scores is None else Q(0))
        u[n] = Q(99,100)*u[n] + value/100
        corrected[n] = u[n]/b
    eligible = [n for n in range(5) if age[n] > 10]
    number = rate*len(eligible)
    accumulated = number
    if number < 1:
        count = int(draw <= number)
    else:
        count = int(number)
    scores = corrected if random_scores is None else random_scores
    chosen = sorted(eligible, key=lambda n: (scores[n],n))[:count]
    for n in chosen:
        u[n], m[n] = Q(0), Q(0)
    for n in chosen:
        w[n*21:n*21+20] = new_weights[n][:]
        w[n*21+20] = Q(0)
        w[110] += w[105+n]*m[n]/(1-Q(99,100)**age[n])
        w[105+n], age[n] = Q(0), 0
    if random_scores is not None:
        corrected = random_scores[:]
    return dict(theta=w, util=u, mean=m, ages=age, chosen=chosen,
                butil=corrected, accumulated=accumulated)


def scalar_prediction(theta, key):
    x = [(key//2**k)%2 for k in range(20)]
    incoming = [theta[n*21:n*21+20] for n in range(5)]
    biases = [theta[n*21+20] for n in range(5)]
    hidden = [max(0., math.fsum(a*b for a,b in zip(row,x))+bias)
              for row,bias in zip(incoming,biases)]
    return math.fsum([theta[110]]+[theta[105+n]*hidden[n] for n in range(5)]), x, hidden


def scalar_step(theta, key, target, lr=.01):
    p,x,h = scalar_prediction(theta,key)
    derivative = 2*(p-target)
    result = theta[:]
    for n in range(5):
        dz = derivative*theta[105+n] if h[n] > 0 else 0.
        for k in range(20):
            result[n*21+k] = theta[n*21+k]-lr*dz*x[k]
        result[n*21+20] = theta[n*21+20]-lr*dz
        result[105+n] = theta[105+n]-lr*derivative*h[n]
    result[110] = theta[110]-lr*derivative
    return result


def main():
    started = time.perf_counter()
    raw = (PREVIOUS/'FULL_REALIZATION.json').read_bytes()
    data = json.loads(raw)
    rational_weights = [Q((n+1)*(k+1)*((-1)**k),1000)
                        for n in range(5) for k in range(20)]
    # Add biases in their separate augmented locations.
    w=[]
    for n in range(5):
        w.extend(rational_weights[n*20:n*20+20]); w.append(Q(n-2,30))
    w.extend(Q(n-2,10) for n in range(5)); w.append(Q(2,7))
    u=[Q(n+1,17) for n in range(5)]
    m=[Q(n+1,19) for n in range(5)]
    age=[9,10,11,20,100]
    features=[Q(n+2,3) for n in range(5)]
    new_weights={n:[Q((n+2)*(k+3),10000) for k in range(20)] for n in range(5)}
    cases=[]
    for method,rate,draw in [('cbp',Q(1,5),Q(1,100)),('cbp',Q(1,5),Q(99,100)),
                             ('cbp',Q(0),Q(0)),('random',Q(1,5),Q(1,100))]:
        random_scores=[Q(5-n,10) for n in range(5)] if method=='random' else None
        reference=exact_gnt(w,u,m,age,features,rate,draw,new_weights,random_scores)
        arm=Learner([float(v) for v in w],method=method,replacement_rate=float(rate))
        arm.util,arm.mean,arm.ages=[float(v) for v in u],[float(v) for v in m],age[:]
        chosen=arm.renew([float(v) for v in features],draw=float(draw),
                         new_incoming={n:[float(v) for v in values] for n,values in new_weights.items()},
                         random_scores=None if random_scores is None else [float(v) for v in random_scores])
        assert chosen==reference['chosen'],(chosen,reference['chosen'])
        errors={}
        for name,actual in [('theta',arm.theta),('util',arm.util),('mean',arm.mean),
                            ('ages',arm.ages),('butil',arm.butil)]:
            errors[name]=max(abs(a-float(b)) for a,b in zip(actual,reference[name]))
            assert errors[name] < 2e-12,(name,errors[name])
        assert abs(arm.accumulated-float(reference['accumulated'])) < 1e-14
        assert 0 not in chosen  # age9 becomes10, still ineligible
        assert arm.theta[110] == float(w[110])  # zeroed mean => zero compensation
        cases.append(dict(method=method,rate=float(rate),draw=float(draw),chosen=chosen,errors=errors))
    theta=data['initial_learner']
    gradient_checks=[]
    scorer_checks=[]
    for t,f in [(0,0),(0,31),(1,7),(2,19)]:
        key=pack_input(data['contexts'][t],f)
        y=data['targets_by_context'][t][f]
        learner=Learner(theta)
        expected=scalar_step(theta,key,y)
        err=learner.learn(key,y)
        gap=max(abs(a-b) for a,b in zip(expected,learner.theta))
        assert gap < 1e-12,gap
        finite=[]
        eps=1e-6
        for k in range(111):
            plus,minus=theta[:],theta[:]
            plus[k]+=eps; minus[k]-=eps
            numeric=((scalar_prediction(plus,key)[0]-y)**2-(scalar_prediction(minus,key)[0]-y)**2)/(2*eps)
            analytic=(theta[k]-expected[k])/.01
            finite.append(abs(numeric-analytic)/max(1,abs(numeric),abs(analytic)))
        assert max(finite)<2e-6,max(finite)
        gradient_checks.append(dict(task=t,fast=f,scalar_gap=gap,finite_difference_scaled=max(finite),loss=err))
    for t in range(3):
        keys=[pack_input(data['contexts'][t],f) for f in range(32)]
        labels=data['targets_by_context'][t]
        observed=support_risk(theta,keys,labels)
        independent=math.fsum((scalar_prediction(theta,k)[0]-y)**2 for k,y in zip(keys,labels))/32
        constant=[0.]*111; constant[110]=3.
        hand=math.fsum((3.-y)**2 for y in labels)/32
        assert abs(observed-independent)<1e-12
        assert support_risk(constant,keys,labels)==hand
        scorer_checks.append(dict(task=t,absolute_gap=abs(observed-independent),constant_risk=hand))
    # Exhaust every AlgorithmR random index path for4observations/capacity2.
    sets=Counter()
    for draw3,draw4 in itertools.product(range(3),range(4)):
        r=Reservoir(2)
        for index,draw in enumerate([0,0,draw3,draw4]):
            r.insert((index,index),draw)
        sets[tuple(sorted(e[0] for e in r.items))]+=1
    assert len(sets)==6 and set(sets.values())=={2},sets
    cache=ExactCache(3); independent=OrderedDict(); total=0.; count=0
    cache_checks=0
    for key,target in [(1,4),(2,-3),(1,4),(3,8),(4,-1),(2,-3),(4,-1),(5,9)]:
        expected=independent.get(key,total/count if count else 0.)
        assert cache.predict(key)==expected
        if key in independent: independent.move_to_end(key)
        cache.observe(key,target)
        independent[key]=target; independent.move_to_end(key)
        if len(independent)>3: independent.popitem(last=False)
        total+=target; count+=1
        assert list(zip(cache.keys,cache.labels))==list(independent.items())
        before=(list(cache.keys),list(cache.labels),cache.hits)
        cache.predict(key,touch=False)
        assert before==(list(cache.keys),list(cache.labels),cache.hits)
        cache_checks+=1
    # Actual source-observation paths for every proposed neural family.
    controls=[]
    for method in ('sgd','cbp','random','snp'):
        arm=Learner(theta,method=method,replacement_rate=1e-4,
                    weight_decay=.01 if method=='snp' else 0.,
                    perturb=1e-4 if method=='snp' else 0.)
        for i in range(200):
            key=pack_input(data['contexts'][0],data['fast_indices'][i])
            y=data['targets_by_context'][0][data['fast_indices'][i]]
            assert math.isfinite(arm.learn(key,y))
        assert all(math.isfinite(v) for v in arm.theta)
        controls.append(dict(method=method,steps=arm.gradient_steps,replacements=arm.replacements,
                             endpoint_prediction=arm.predict(key)))
    result=dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                exact_rational_renewal_cases=cases,gradient_checks=gradient_checks,
                scorer_checks=scorer_checks,reservoir_all_six_subsets_equal_counts=True,
                cache_reference_events=cache_checks,short_source_paths=controls,
                separate_decoded_read_bytes=len(raw),
                exposure='whole consumed synthetic realization decoded; no fresh holdout; no empirical raw',
                seconds=time.perf_counter()-started,
                max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (ROOT/'REFERENCES.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    try:
        main()
    except BaseException:
        (ROOT/'REFERENCE_FAILURE.txt').write_text(traceback.format_exc())
        raise
