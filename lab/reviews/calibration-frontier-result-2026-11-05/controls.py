"""Independent known-law controls; neither empirical fitting nor author imports."""
import time
import numpy as np
from scipy.stats import beta, binom
from independent import (HERE, MAIN, Accounting, save, embedding, mixed_energy,
                         direct_energy, bootstrap_weights, standard_error)


def event_rate(event):
    v = np.asarray(event,bool); n=v.size; k=int(v.sum())
    return dict(events=k,cohorts=n,rate=k/n,
                clopper_pearson_95=[0. if k==0 else float(beta.ppf(.025,k,n-k+1)),
                                   1. if k==n else float(beta.ppf(.975,k+1,n-k))],
                one_sided95_upper=1. if k==n else float(beta.ppf(.95,k+1,n-k)))


def simultaneous_control_intervals(x, weights):
    """Batch the frozen centered bootstrap. Independent implementation."""
    all_lo=[];all_hi=[];all_q=[];all_bon_lo=[];all_bon_hi=[]
    from scipy.stats import t
    bon=float(t.ppf(1-.05/8,23))
    w=weights.astype(float)/64
    for start in range(0,len(x),16):
        sub=x[start:start+16]
        mu=sub.mean(axis=1)
        se=np.sqrt((40*np.var(sub[:,:40],axis=1,ddof=1)+24*np.var(sub[:,40:],axis=1,ddof=1))/64**2)
        flat=sub.transpose(1,0,2).reshape(64,-1)
        boot=np.einsum('bi,ij->bj',w,flat,optimize=True).reshape(len(w),len(sub),4)
        diff=boot-mu
        z=np.divide(diff,se,out=np.zeros_like(diff),where=se>1e-14)
        q=np.quantile(np.abs(z).max(axis=2),.95,axis=0)
        all_q.extend(q);all_lo.extend(mu-q[:,None]*se);all_hi.extend(mu+q[:,None]*se)
        all_bon_lo.extend(mu-bon*se);all_bon_hi.extend(mu+bon*se)
    return np.asarray(all_lo),np.asarray(all_hi),np.asarray(all_q),np.asarray(all_bon_lo),np.asarray(all_bon_hi)


def summary(name,x,truth,weights,source_radius=None):
    lo,hi,q,blo,bhi=simultaneous_control_intervals(x,weights)
    truth=np.asarray(truth,float)
    if truth.ndim==1: truth=np.broadcast_to(truth,(len(x),4))
    material=np.array([.02,0.,.02,0.])
    genuinely_material=truth>=material-1e-13
    immaterial_or_boundary=truth<=material+1e-13
    absent=hi<material;positive=lo>material
    out=dict(name=name,true_mean_range=[truth.min(0),truth.max(0)],sample_mean=x.mean((0,1)),
             nominal_any_band_noncoverage=event_rate(((lo>truth)|(hi<truth)).any(1)),
             any_false_endpoint_absence=event_rate((absent&genuinely_material).any(1)),
             any_false_endpoint_positive=event_rate((positive&immaterial_or_boundary).any(1)),
             all_four_absent=event_rate(absent.all(1)),
             false_all_four_absence=event_rate(absent.all(1)&genuinely_material.any(1)),
             per_column_absence=[event_rate(absent[:,j]) for j in range(4)],
             per_column_positive=[event_rate(positive[:,j]) for j in range(4)],
             bonferroni_any_noncoverage=event_rate(((blo>truth)|(bhi<truth)).any(1)),
             bonferroni_false_all_four_absence=event_rate((bhi<material).all(1)&genuinely_material.any(1)),
             mean_maxT_critical=float(q.mean()))
    if source_radius is not None:
        delta=np.asarray(source_radius)
        ea=hi+delta<material
        out['finite_source_radius']=delta
        out['envelope_false_all_four_absence']=event_rate(ea.all(1)&genuinely_material.any(1))
        out['envelope_any_false_endpoint_absence']=event_rate((ea&genuinely_material).any(1))
    return out


def point_risk_contrasts(ordinary_error,neural_error):
    # Fixed K=600 of N=1,000 is the observed truth; point forecasts have exact integer K.
    # Primary energy for a point law is absolute ratio distance, independently enumerated.
    ordinary_error=np.asarray(ordinary_error,float);neural_error=np.asarray(neural_error,float)
    assert np.max(np.abs(1000*ordinary_error-np.round(1000*ordinary_error)))<1e-9
    assert np.max(np.abs(1000*neural_error-np.round(1000*neural_error)))<1e-9
    assert np.min(.6+ordinary_error)>=0 and np.max(.6+ordinary_error)<=1
    assert np.min(.6+neural_error)>=0 and np.max(.6+neural_error)<=1
    result=np.empty((*ordinary_error.shape[:-1],4))
    result[...,0::2]=ordinary_error-neural_error
    result[...,1::2]=.9*ordinary_error-neural_error
    return result


def main():
    meter=Accounting('early independent known-law controls')
    previous=meter.json(MAIN/'MAIN_CONTROLS.json')
    weights=bootstrap_weights()
    n=np.array([0,0,100,100,100,100,100,100,100,100])
    k=np.array([0,0,20,20,20,20,80,80,80,80])
    support=np.array([[1,0,0],[0,.2,.8],[0,.8,.2]])
    probs=np.array([.2,.4,.4])
    checks=[]
    for on,ok in [(0,0),(100,20),(100,80)]:
        target=embedding(np.array([on]),np.array([ok]))[0]
        direct=direct_energy(embedding(n,k),target)/np.sqrt(2)
        fast,u=mixed_energy(n,k,on,ok)
        assert abs(direct-fast)<1e-13
        checks.append(dict(observed=[on,ok],independent_direct=direct,independent_fast=fast,U=u))
    dist=np.linalg.norm(support[:,None]-support[None,:],axis=-1)/np.sqrt(2)
    def expected(q): return float(probs@dist@q-.5*q@dist@q)
    mixture_risks={name:expected(q) for name,q in [('truth',probs),('deleted_missing_mass',np.array([0,.5,.5])),('all_missing',np.array([1.,0,0]))]}
    assert mixture_risks['truth']<mixture_risks['deleted_missing_mass']<mixture_risks['all_missing']
    # All missing and no positive predictive support stay defined in the proper observable.
    allmissing=mixed_energy(np.zeros(8),np.zeros(8),0,0)[0]
    assert allmissing==0
    missing_to_positive=mixed_energy(np.zeros(8),np.zeros(8),100,60)[0]
    assert abs(missing_to_positive-np.sqrt(.76))<1e-13
    controls=[];R=2000
    rng=np.random.default_rng(20261105091)
    nullobs=rng.binomial(1000,.6,size=(R,64,2))/1000
    null=np.zeros((R,64,4));null[...,1::2]=-.1*np.abs(nullobs-.6)
    nullD=-.1*float(np.sum(binom.pmf(np.arange(1001),1000,.6)*np.abs(np.arange(1001)/1000-.6)))
    controls.append(summary('identical_forecasts_no_acquisition_or_state_noise',null,[0,nullD,0,nullD],weights))
    for j,m in enumerate([.015,.02,.025]):
        rng=np.random.default_rng(20261105092+j)
        error=m+rng.choice([- .01,.01],size=(R,64,2))
        x=point_risk_contrasts(error,np.zeros_like(error))
        controls.append(summary('accuracy_margin_'+str(m),x,[m,.9*m,m,.9*m],weights))
    rng=np.random.default_rng(20261105095)
    for r in [.05,.1,.15]:
        ordinary=.060+rng.choice([-.004,.004],size=(R,64,2))
        neural=.060*(1-r)+rng.choice([-.004,.004],size=(R,64,2))
        controls.append(summary('proper_score_relative_gain_'+str(r),point_risk_contrasts(ordinary,neural),
                                [.06*r,.06*(r-.1),.06*r,.06*(r-.1)],weights))
    # Reconstruct the original shared-source demonstration and its exact marginal truth.
    shared=rng.choice([-.01,.01],size=(R,1,1));eps=rng.choice([-.004,.004],size=(R,64,2))
    gain=.02+shared+eps
    x=point_risk_contrasts(gain,np.zeros_like(gain))
    original_shared=summary('original_shared_source_marginal_target',x,[.02,.018,.02,.018],weights,[.01,.009,.01,.009])
    # New consequential control: ALL FOUR quantities have boundary truth, versus the
    # original separate cases that structurally avoid an all-four false exclusion.
    extra=[]
    for j,gain in enumerate([.015,.02,.025]):
        rng=np.random.default_rng(20261105111+j)
        ordinary=.200+rng.choice([-.01,.01],size=(R,64,2))
        neural=.200-gain+rng.choice([-.01,.01],size=(R,64,2))
        x=point_risk_contrasts(ordinary,neural)
        extra.append(summary('joint_accuracy_and_score_boundary_gain_'+str(gain),x,
                             [gain,gain-.02,gain,gain-.02],weights))
    rng=np.random.default_rng(20261105114)
    shared=rng.choice([-.008,.008],size=(R,1,1))
    ordinary=.2+shared+rng.choice([-.004,.004],size=(R,64,2))
    neural=.18+rng.choice([-.004,.004],size=(R,64,2))
    x=point_risk_contrasts(ordinary,neural)
    extra.append(summary('joint_boundary_with_shared_source_against_marginal_truth',x,[.02,0,.02,0],weights,[.008,.0072,.008,.0072]))
    conditional=np.empty((R,4));conditional[:,0::2]=.02+shared[:,0];conditional[:,1::2]=.9*shared[:,0]
    extra.append(summary('same_shared_source_conditional_truth',x,conditional,weights))
    # No-acquisition latent state mixture; identical forecasts can only gain from state
    # estimation, not from a learning update. Truth remains stationary at each origin.
    state=.6+rng.choice([-.10,-.06,.06,.10],size=(R,64,2))
    naive=np.abs(state-.6)
    identical=point_risk_contrasts(naive,naive)
    extra.append(summary('stationary_latent_state_noise_identical_forecasts',identical,[0,-.008,0,-.008],weights))
    recovered=point_risk_contrasts(naive,np.full_like(naive,.02))
    extra.append(summary('stationary_state_estimator_useful_gain_no_acquisition',recovered,[.06,.052,.06,.052],weights))
    comparison=[]
    for own,author in zip(controls,previous['controls']):
        assert own['name']==author['kind']
        comparison.append(dict(name=own['name'],
            nominal_band_miss_own=own['nominal_any_band_noncoverage']['rate'],
            nominal_band_miss_author=author['any_band_miss']['rate'],
            false_absence_own=own['any_false_endpoint_absence']['rate'],
            false_absence_author=author['any_false_absence']['rate'],
            all_four_absent_own=own['all_four_absent']['rate'],
            all_four_absent_author=author['all4_absent']['rate']))
    save('INDEPENDENT_CONTROLS.json',dict(missingness_checks=checks,finite_law_expected_risks=mixture_risks,
        all_missing_score=allmissing,all_missing_forecast_positive_target_score=missing_to_positive,
        original_controls_reconstruction=controls,original_shared_source_reconstruction=original_shared,
        author_comparison=comparison,additional_controls=extra,
        correction_history='V1 preserved: constant absolute latent-state error .08 produced float-only zero-width band misses at ~1e-17. Additional state control now uses four equiprobable stationary states with absolute errors .06/.10 and nonzero sampling variation, same exact expected risk .08. No empirical inference method, original controls or material margin changed.',
        model_scope='Analysis behavior under exactly specified finite laws; no biological power, empirical failure probability or universal coverage guarantee'))
    save('CONTROL_RESOURCES.json',meter.receipt())
    print('Original controls:',[(c['name'],c['nominal_any_band_noncoverage']['rate'],c['any_false_endpoint_absence']['rate']) for c in controls])
    print('Additional:',[(c['name'],c['nominal_any_band_noncoverage']['rate'],c['false_all_four_absence']['rate']) for c in extra])
    print(meter.receipt())


if __name__=='__main__':
    begin=time.process_time()
    try: main()
    except BaseException as exc:
        save('CONTROL_FAILURE_'+str(time.time_ns())+'.json',dict(error=repr(exc),process_cpu_seconds=time.process_time()-begin))
        raise
