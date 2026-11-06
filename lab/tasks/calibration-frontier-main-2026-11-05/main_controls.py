"""Finite-law missingness, no-acquisition/null and operational-boundary controls."""
import time,resource
BEGIN=time.monotonic();CPU=time.process_time()
import json
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import binom
from main_scores import mixed_score
from main_inference import resampling_counts

HERE=Path(__file__).resolve().parent


def conditional_decisions(X,counts):
    """Same primary4 fixed-studentizer maxT, vectorized independent cohorts."""
    results=[]
    for start in range(0,len(X),16):
        xx=X[start:start+16];B=len(xx);point=xx.mean(1)
        se=np.sqrt((40/64)**2*np.var(xx[:,:40],axis=1,ddof=1)/40+
                   (24/64)**2*np.var(xx[:,40:],axis=1,ddof=1)/24)
        v=counts.astype(float)@xx.transpose(1,0,2).reshape(64,B*4)/64
        v=v.reshape(len(counts),B,4)-point[None]
        T=np.divide(v,se[None],out=np.zeros_like(v),where=se[None]>1e-14)
        critical=np.quantile(np.max(np.abs(T),axis=2),.95,axis=0)
        lo=point-critical[:,None]*se;hi=point+critical[:,None]*se
        for j in range(B):results.append((point[j],lo[j],hi[j],critical[j]))
    return results


def rate(value):
    value=np.asarray(value,float);p=float(value.mean());n=len(value)
    return dict(rate=p,monte_carlo_se=float(np.sqrt(p*(1-p)/n)),cohorts=n)


def summarize(X,truth,counts,kind,source_delta=0.):
    decisions=conditional_decisions(X,counts);lo=np.array([d[1] for d in decisions]);hi=np.array([d[2] for d in decisions])
    margin=np.array([.02,0,.02,0]);true=np.asarray(truth)
    ordinary_absent=hi<margin;ordinary_positive=lo>margin
    false_absence=ordinary_absent&(true>=margin)[None]
    false_positive=ordinary_positive&(true<=margin)[None]
    # A finite declared source envelope shifts ordinary risk only; never fake biological replicates.
    shift=np.array([source_delta,.9*source_delta,source_delta,.9*source_delta])
    envelope_absent=hi+np.abs(shift)<margin
    return dict(kind=kind,true_contrasts=true.tolist(),material_margins=margin.tolist(),
         any_false_absence=rate(false_absence.any(1)),any_false_material_positive=rate(false_positive.any(1)),
         any_band_miss=rate(((lo>true)|(hi<true)).any(1)),
         per_column_absence=[rate(ordinary_absent[:,j]) for j in range(4)],
         per_column_material_positive=[rate(ordinary_positive[:,j]) for j in range(4)],
         all4_absent=rate(ordinary_absent.all(1)),finite_source_envelope_all4_absent=rate(envelope_absent.all(1)),
         per_column_finite_source_envelope_absence=[rate(envelope_absent[:,j]) for j in range(4)],
         finite_source_shift=shift.tolist(),mean_critical=float(np.mean([d[3] for d in decisions])))


def main():
    # Independent direct distance enumeration checks the changed fast scoring code.
    counts=[(0,0),(100,20),(100,80)];p=np.array([.2,.4,.4])
    sample=np.array([counts[0]]*2+[counts[1]]*4+[counts[2]]*4)
    Z=np.array([[1,0,0],[0,.2,.8],[0,.8,.2]])
    checks=[]
    for on,ok in counts:
        target=np.array([1,0,0]) if on==0 else np.array([0,ok/on,1-ok/on])
        slow=float((p@np.linalg.norm(Z-target,axis=1)-.5*np.sum(p[:,None]*p[None,:]*cdist(Z,Z)))/np.sqrt(2))
        fast,_=mixed_score(sample[:,0],sample[:,1],on,ok)
        assert abs(fast-slow)<1e-13
        checks.append(dict(observed_N=on,observed_K=ok,fast=fast,independent_direct=slow,error=abs(fast-slow)))
    def expected(q):
        distance=cdist(Z,Z)/np.sqrt(2)
        score=distance@q-.5*(q[:,None]*q[None,:]*distance).sum()
        return float(p@score)
    truth_score=expected(p);wrongmissing=expected(np.array([0,.5,.5]));allmissing=expected(np.array([1,0,0]))
    assert truth_score<wrongmissing and truth_score<allmissing
    counts_bs=resampling_counts(20261105077)
    rng=np.random.default_rng(20261105091);R=2000
    nullobs=rng.binomial(1000,.6,size=(R,64,2))/1000
    residual=np.abs(nullobs-.6)
    null=np.zeros((R,64,4));null[:,:,1]=-.1*residual[:,:,0];null[:,:,3]=-.1*residual[:,:,1]
    # Identical fixed-state predictors, binomial observation noise only: no acquisition/state noise.
    support=np.arange(1001);nullD=-.1*float(np.sum(binom.pmf(support,1000,.6)*np.abs(support/1000-.6)))
    nulltruth=np.array([0,nullD,0,nullD])
    results=[summarize(null,nulltruth,counts_bs,'identical_forecasts_no_acquisition_or_state_noise')]
    for j,m in enumerate((.015,.02,.025)):
        rng=np.random.default_rng(20261105092+j)
        # Exact1000-count point forecasts; symmetry preserves the planted expected margin.
        eps=rng.choice(np.array([-.01,.01]),size=(R,64,2))
        error=m+eps
        X=np.empty((R,64,4));X[:,:,0]=error[:,:,0];X[:,:,2]=error[:,:,1]
        X[:,:,1]=.9*error[:,:,0];X[:,:,3]=.9*error[:,:,1]
        results.append(summarize(X,[m,.9*m,m,.9*m],counts_bs,'accuracy_margin_'+str(m),source_delta=.01))
    rng=np.random.default_rng(20261105095)
    for j,r in enumerate((.05,.10,.15)):
        ordinary=.060+rng.choice(np.array([-.004,.004]),size=(R,64,2))
        neural=.060*(1-r)+rng.choice(np.array([-.004,.004]),size=(R,64,2))
        # Forecast K=660+/−4 vs657/654/651+/−4, actual K=600: exact finite point-law risks.
        assert np.allclose(ordinary*1000,np.round(ordinary*1000)) and np.allclose(neural*1000,np.round(neural*1000))
        X=np.empty((R,64,4));X[:,:,0]=ordinary[:,:,0]-neural[:,:,0];X[:,:,2]=ordinary[:,:,1]-neural[:,:,1]
        X[:,:,1]=.9*ordinary[:,:,0]-neural[:,:,0];X[:,:,3]=.9*ordinary[:,:,1]-neural[:,:,1]
        A=.060*r;D=.060*(r-.10)
        results.append(summarize(X,[A,D,A,D],counts_bs,'proper_score_relative_gain_'+str(r),source_delta=.006))
    # Show why a fixed source envelope is not replaced by independent-animal confidence.
    shared=rng.choice(np.array([-.01,.01]),size=(R,1,1));eps=rng.choice(np.array([-.004,.004]),size=(R,64,2))
    gains=.02+shared+eps
    X=np.empty((R,64,4));X[:,:,0]=gains[:,:,0];X[:,:,2]=gains[:,:,1]
    X[:,:,1]=.9*gains[:,:,0];X[:,:,3]=.9*gains[:,:,1]
    demonstration=summarize(X,[.02,.018,.02,.018],counts_bs,'unmodeled_shared_source_offset_marginal_target',source_delta=.01)
    demonstration['interpretation']='The four-animal band is conditional on fitted source; comparing it to a marginal source-average target is a deliberately misspecified use. A finite source envelope prevents treating that as source-tail certification.'
    out=dict(utc=datetime.now(timezone.utc).isoformat(),missingness_checks=checks,
         finite_law_expected_scores=dict(truth=truth_score,deleted_missing_mass=wrongmissing,all_missing=allmissing),
         controls=results,source_heterogeneity_demonstration=demonstration,
         replicated_cohorts_per_case=R,bootstrap_replicates=20000,
         null_truth_note='No-acquisition null proper risk independently enumerated under Binomial1000,.6; A is exactly0. NegativeD is safely separated from the materiality boundary.',
         scope='Finite known-law/analysis checks, not biological power or model-family validation',
         scientific_cpu_seconds=time.process_time()-CPU,process_wall_seconds=time.monotonic()-BEGIN,
         peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         explicit_read_decode_bytes=0,io_note='No empirical dataset/artifact reads; interpreter/import bytes unknown')
    (HERE/'MAIN_CONTROLS.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(cpu_seconds=out['scientific_cpu_seconds'],wall_seconds=out['process_wall_seconds'],
        truth_score=truth_score,controls=[dict(kind=x['kind'],false_absence=x['any_false_absence'],false_positive=x['any_false_material_positive']) for x in results])))


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        (HERE/('CONTROLS_FAILURE_'+str(time.time())+'.json')).write_text(json.dumps(dict(error=repr(exc),
             scientific_cpu_seconds=time.process_time()-CPU,process_wall_seconds=time.monotonic()-BEGIN))+'\n')
        raise
