"""Independent exact-rational two-order reference, before new evaluation."""
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import resource
import time

from engine import OrderLearner, prior

ROOT = Path(__file__).resolve().parent


def exact(w, u, m, a, f, rate, draw, incoming, compensate, scores=None):
    w, u, m, a = w[:], u[:], m[:], a[:]
    if not rate:
        return w,u,m,a,[Q(0)]*5,[],Q(0)
    corrected=[]
    for j in range(5):
        a[j]+=1
        m[j]=(99*m[j]+f[j])/100
        c=1-Q(99,100)**a[j]
        utility = (abs(w[105+j]) * abs(f[j]-m[j]/c) /
                   (sum(abs(v) for v in w[21*j:21*j+20])/20)
                   if scores is None else Q(0))
        u[j]=(99*u[j]+utility)/100
        corrected.append(u[j]/c)
    if scores is not None:
        corrected=scores[:]
    eligible=[j for j in range(5) if a[j]>10]
    n=rate*len(eligible)
    count=int(draw<=n) if n<1 else int(n)
    chosen=sorted(eligible,key=lambda j:(corrected[j],j))[:count]
    bias_change=sum(w[105+j]*m[j]/(1-Q(99,100)**a[j]) for j in chosen) if compensate else Q(0)
    w[110]+=bias_change
    for j in chosen:
        w[21*j:21*j+20]=incoming[j][:]
        w[21*j+20]=w[105+j]=u[j]=m[j]=Q(0)
        a[j]=0
    return w,u,m,a,corrected,chosen,n


def main():
    t=time.perf_counter()
    pinned=ROOT.parent/'plasticity-retention-source-benchmark-2026-11-02'
    manifest=json.loads((pinned/'SOURCE_MANIFEST.json').read_bytes())
    checks=[]; read_bytes=(pinned/'SOURCE_MANIFEST.json').stat().st_size
    for entry in manifest['files']:
        if entry['path'] not in ['lop/algos/gnt.py','lop/algos/cbp.py','lop/slowly_changing_regression/expr.py']:
            continue
        raw=(pinned/'vendor'/entry['path']).read_bytes(); read_bytes+=len(raw)
        blob=hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest()
        assert blob==entry['blob_sha1']
        checks.append(dict(path=entry['path'],bytes=len(raw),git_blob=blob,sha256=hashlib.sha256(raw).hexdigest()))
    w=[]
    for j in range(5):
        w.extend(Q((j+1)*(k+1)*(-1)**k,1000) for k in range(20)); w.append(Q(j-2,30))
    w.extend(Q(j-2,10) for j in range(5)); w.append(Q(2,7))
    u=[Q(j+1,17) for j in range(5)]
    m=[Q(j+1,19) for j in range(5)]
    a=[9,10,11,20,100]
    f=[Q(j+2,3) for j in range(5)]
    incoming={j:[Q((j+2)*(k+3),10000) for k in range(20)] for j in range(5)}
    cases=[]
    for method,rate,draw in [('cbp',Q(1,5),Q(1,100)),('cbp',Q(1,5),Q(99,100)),
                             ('cbp',Q(0),Q(0)),('random',Q(1,5),Q(1,100))]:
        for comp in [False,True]:
            scores=[Q(5-j,10) for j in range(5)] if method=='random' else None
            ref=exact(w,u,m,a,f,rate,draw,incoming,comp,scores)
            arm=OrderLearner([float(v) for v in w],method=method,replacement_rate=float(rate),compensate=comp)
            arm.util,arm.mean,arm.ages=[float(v) for v in u],[float(v) for v in m],a[:]
            chosen=arm.renew([float(v) for v in f],float(draw),
                             {j:[float(v) for v in row] for j,row in incoming.items()},
                             None if scores is None else [float(v) for v in scores])
            assert chosen==ref[5] and 0 not in chosen
            errors=[max(abs(float(v)-z) for v,z in zip(expected,actual)) for expected,actual in
                    zip(ref[:5],[arm.theta,arm.util,arm.mean,arm.ages,arm.butil])]
            assert max(errors)<2e-12,errors
            cases.append(dict(method=method,compensate=comp,rate=float(rate),draw=float(draw),chosen=chosen,
                              maximum_error=max(errors),bias_change=arm.theta[110]-float(w[110])))
    # Literal replacement must agree with the prior independently tested engine.
    base=prior.Learner([float(v) for v in w],method='cbp',replacement_rate=.2)
    ours=OrderLearner([float(v) for v in w],method='cbp',replacement_rate=.2)
    for arm in [base,ours]:
        arm.util,arm.mean,arm.ages=[float(v) for v in u],[float(v) for v in m],a[:]
        arm.renew([float(v) for v in f],draw=0.,new_incoming={j:[float(v) for v in row] for j,row in incoming.items()})
    assert base.theta==ours.theta and base.mean==ours.mean and base.util==ours.util
    # A mature constant removed feature: true effect is output_weight*activity.
    # This discrimination example deliberately fixes unit identity, not a new teacher.
    constant=[]
    for value in [Q(0),Q(3,2)]:
        age=[20]*5; means=[Q(0)]*5
        means[4]=value*(1-Q(99,100)**20)
        feat=[Q(0)]*4+[value]
        scores=[Q(5-j) for j in range(5)]
        for comp in [False,True]:
            ref=exact(w,u,means,age,feat,Q(1,5),Q(0),incoming,comp,scores)
            removed=w[109]*value
            delta=ref[0][110]-w[110]-removed
            assert delta==(Q(0) if comp else -removed)
            constant.append(dict(activity=float(value),compensate=comp,removed_output=float(removed),
                                 prediction_change=float(delta),squared_change=float(delta*delta)))
    result=dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                source_checks=checks,exact_two_order_cases=cases,literal_prior_exact_agreement=True,
                constant_feature_discrimination=constant,separate_explicit_read_bytes=read_bytes,
                seconds=time.perf_counter()-t,max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                exposure='constructed states only; no new teacher generated; no empirical/protected raw')
    (ROOT/'REFERENCE.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    main()
