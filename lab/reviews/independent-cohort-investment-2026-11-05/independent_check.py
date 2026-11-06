"""Independent investment arithmetic on saved scores and source summaries only.

No simulator, score, inference or planning module from an author is imported.
Bootstrap draws resample explicit animal indices rather than multinomial counts.
The compatible alternatives change the SAME GRU risk against both references.
This is a planning law conditional on the consumed residual sample, not power
certification for the unopened cohort or a repeated-training procedure.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib, io, json, resource, time
from pathlib import Path
import numpy as np
from scipy.stats import norm, t, nct

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OLD=ROOT/'lab/tasks/calibration-frontier-main-2026-11-05'
NEW=ROOT/'lab/tasks/independent-acquisition-cohort-2026-11-05'
READS=[]

def read(p):
    b=p.read_bytes()
    READS.append(dict(path=str(p.relative_to(ROOT)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    return b

def load(p): return json.loads(read(p))
def default(x):
    if isinstance(x,np.ndarray): return x.tolist()
    if isinstance(x,np.generic): return x.item()
    raise TypeError(type(x).__name__)

def freq(x): return dict(k=int(x.sum()),n=int(len(x)),rate=float(x.mean()))

def n_for_power(sd,gap,family=2,power=.8):
    # Finite t critical, Gaussian planning mean; a transparent diagnostic.
    for n in range(3,1000000):
        q=t.ppf(1-.05/(2*family),n-1)
        if norm.cdf(gap*np.sqrt(n)/sd-q)>=power: return n
    return None

def simulate(X,n,rng,R=50000):
    mu=X.mean(axis=0); res=X-mu
    q=float(t.ppf(1-.05/4,n-1))
    err=np.empty((R,2)); se=np.empty_like(err)
    for start in range(0,R,1000):
        ids=rng.integers(0,len(X),size=(min(1000,R-start),n))
        v=res[ids]
        err[start:start+len(v)]=v.mean(axis=1)
        se[start:start+len(v)]=v.std(axis=1,ddof=1)/np.sqrt(n)
    return err,q*se,q

def main():
    cpu=time.process_time(); wall=time.monotonic(); decode=0
    with np.load(io.BytesIO(read(OLD/'REFINED_SCORES.npz')),allow_pickle=False) as z:
        scores=z['pooled1024']; subjects=z['subjects']; metrics=z['metrics']
    decode+=scores.nbytes+subjects.nbytes+metrics.nbytes
    assert scores.shape==(64,2,4,2,8) and list(metrics)[1]=='mixed'
    # Names/horizons confirmed in saved author analysis code, not imported.
    # score axes: animal, prefix200/1000, original/recent100/recent250/GRU,
    # horizon500/2000, metric.
    risks=scores[:,0,[1,0],1,1]
    gru=scores[:,0,3,1,1]
    X=.9*risks-gru[:,None]
    with np.load(io.BytesIO(read(OLD/'REFINED_CONTRASTS.npz')),allow_pickle=False) as z:
        contributions=z['contributions']; labs=z['labs']; ids=z['subjects']
    decode+=contributions.nbytes+labs.nbytes+ids.nbytes
    family=load(OLD/'MAIN_FAMILY_REFINED.json')['columns']
    indices=[next(i for i,c in enumerate(family) if c['kind']=='fixed_refined' and c['metric']=='D' and c['cutoff']==200 and c['reference']==r) for r in ['recent_selected','original']]
    maxerr=float(np.max(np.abs(contributions[:,indices]-X)))
    assert maxerr<1e-14 and np.array_equal(subjects,ids)
    focused=load(NEW/'FOCUSED_DESIGN.json')
    cohort=load(NEW/'QUALIFIED_COHORT.json')
    chrono=load(NEW/'AGGREGATE_CHRONOLOGY.json')
    source=load(NEW/'CRITERION_SOURCE_FIT.json')
    execution=load(OLD/'MAIN_EXECUTION.json')
    eligible=[s for s in cohort['subjects'] if s['role']=='candidate_primary_evaluation']
    animal_counts=Counter(s['lab'] for s in eligible)
    assert len(eligible)==192 and dict(sorted(animal_counts.items()))==cohort['primary_counts_by_lab']
    normalized=lambda s: ''.join(c for c in s.lower() if c.isalnum())
    exclusions=load(NEW/'ORIGINAL_EXCLUSIONS.json')
    excluded_keys=set(exclusions['exclusion_keys'])
    # Separate simple normalization check against listed source subjects.
    original_names={normalized(s['subject']) for s in exclusions['subjects']}
    name_overlap=[s['subject'] for s in eligible if normalized(s['subject']) in original_names]
    assert not name_overlap
    mu=X.mean(0); sd=X.std(0,ddof=1); risk=risks.mean(0)
    rng=np.random.default_rng(202611050519)
    err,hw,q=simulate(X,192,rng)
    rates=[]
    for benefit in [0.,.05,.1,.15,.2]:
        # Author's numerical scenario, independently resampled.
        truth_each=(benefit-.1)*risk
        # A coherent common GRU shift leaves both ordinary risk means fixed.
        gmean=(1-benefit)*risk[0]
        truth_common=.9*risk-gmean
        def decisions(truth):
            y=err+truth
            return dict(positive_both=freq(np.all(y-hw>0,axis=1)),
                        negative_recent=freq(y[:,0]+hw[:,0]<0),
                        negative_both=freq(np.all(y+hw<0,axis=1)))
        rates.append(dict(relative_GRU_gain_against_recent=benefit,
                          author_equal_relative_scenario=decisions(truth_each),
                          common_GRU_risk_scenario=dict(gru_risk=gmean,truth=truth_common,**decisions(truth_common))))
    # D_recent's one-dimensional noncentral-t power is an independent
    # parametric cross-check of the simulation, not a shared bootstrap.
    analytical=[]
    for scale in [1.,1.5]:
        for b in [0.,.05,.15,.2]:
            delta=(b-.1)*risk[0]
            nc=delta*np.sqrt(192)/(scale*sd[0])
            analytical.append(dict(sd_multiplier=scale,benefit=b,
                                   positive_recent=float(nct.sf(q,191,nc)),
                                   negative_recent=float(nct.cdf(-q,191,nc)),
                                   power_positive_both_cannot_exceed_recent=float(nct.sf(q,191,nc))))
    # Site correlation is an illustrative dependence stress, not an estimated ICC.
    square_sum=sum(n*n for n in animal_counts.values())
    rho_rows=[]
    for rho in [0.,.01,.05,.1]:
        deff=1+rho*(square_sum/192-1)
        neff=192/deff
        rho_rows.append(dict(icc=rho,design_effect=deff,effective_n=neff,
           normal_positive_recent_at20=float(norm.cdf(.1*risk[0]*np.sqrt(neff)/sd[0]-q))))
    # Source criterion selection checked by direct event counting.
    milestones=[]
    for h in [3000,4000,6000]:
        subjects0=source['subjects']
        events=[s for s in subjects0 if s['first_trained1a_end'] is not None and s['first_trained1a_end']<=h]
        complete=[s for s in subjects0 if s['selected_rows']>=h]
        retained=[s for s in events if s['selected_rows']>=h]
        event_free=[s for s in subjects0 if (s['first_trained1a_end'] is None or s['first_trained1a_end']>h) and s['selected_rows']>=h]
        censored=[s for s in subjects0 if s not in events and s['selected_rows']<h]
        recorded=next(x for x in source['summary'] if x['horizon']==h)
        assert (len(events),len(event_free),len(censored),len(complete),len(retained))==(recorded['observed_first_passages'],recorded['event_free_observation_through_h'],recorded['right_censored_before_h_without_observed_event'],recorded['complete_through_h_n'],recorded['complete_through_h_events'])
        milestones.append(dict(horizon=h,all_observed_events=len(events),
             complete_at_h=len(complete),events_in_complete=len(retained),
             observed_early_events_discarded=len(events)-len(retained),
             discarded_fraction=(len(events)-len(retained))/len(events),
             excluded_observed_event_subjects=[s['subject'] for s in events if s not in retained],
             event_free_observed_through_h=len(event_free),right_censored_without_event=len(censored),
             note="Selection illustration on old source only. Not the new cohort's event rate."))
    switches=[dict(subject=s['subject'],training_opportunities=s['verified_training_opportunities'],
              intervening_other_tasks=s['intervening_other_tasks']) for s in chrono['subjects'] if s['status']=='other_task_before3000']
    # Independently sum the complete proposed staged cost and retain historicals.
    price=focused['price']
    future_min=sum(price[k][0] for k in ['author_with_controls_and25to75percent_overhead_cpu_minutes','independent_result_challenge_cpu_minutes','useful_revision_cpu_minutes','independent_design_challenge_cpu_minutes','source_payload_preflight_cpu_minutes','closeout_cpu_minutes'])
    future_max=sum(price[k][1] for k in ['author_with_controls_and25to75percent_overhead_cpu_minutes','independent_result_challenge_cpu_minutes','useful_revision_cpu_minutes','independent_design_challenge_cpu_minutes','source_payload_preflight_cpu_minutes','closeout_cpu_minutes'])
    fixed=execution['timings']['fixed_three_conditions_two_streams_plus_exact']['cpu_seconds']*2/3*3/60
    dependent=execution['timings']['source32_reselection_and_dependent_forecasts']['cpu_seconds']*2*3/60
    # Main primary use scope cannot certify a source procedure, but its
    # proposed dependent-forecast price is preserved rather than treated as free.
    result=dict(utc=datetime.now(timezone.utc).isoformat(),status='complete',
       new_evaluation_payloads_read=False,score_reconstruction_max_abs_error=maxerr,
       reconstructed_D_mean=mu,reconstructed_D_sd=sd,reference_mean_risks=risk,
       paired_reference_correlation=np.corrcoef(X.T),
       n192_critical=q,n192_expected_score_halfwidth=q*sd/np.sqrt(192),
       n192_halfwidth_as_relative_recent_percentage=100*q*sd[0]/np.sqrt(192)/risk[0],
       independent_bootstrap_rates=rates,parametric_noncentral_t_check=analytical,
       old_means_repeat=dict(recent=freq(err[:,0]+mu[0]+hw[:,0]<0),both=freq(np.all(err+mu+hw<0,axis=1))),
       source_criterion_selection=milestones,future_switch_exclusions=switches,
       qualified_unit_counts=dict(n=len(eligible),by_lab=dict(animal_counts),cohorts=dict(Counter(s['cohort'] for s in eligible))),
       name_overlap=name_overlap,identity_note="Independent canonical-name check only; source stable-session/alias receipts still govern. No universal animal-UUID claim.",
       illustrative_same_lab_correlation=rho_rows,
       near_threshold_required_n_recent_15_or5=n_for_power(sd[0],.05*risk[0]),
       at20_required_n_recent=n_for_power(sd[0],.10*risk[0]),
       independent_price=dict(primary_cpu_minutes=fixed,dependent_cpu_minutes=dependent,
                  proposed_whole_future_cpu_minutes=[future_min,future_max],
                  proposed_whole_future_elapsed_scientist_hours=[sum(v[0] for v in price['scientist_elapsed_hours'].values()),sum(v[1] for v in price['scientist_elapsed_hours'].values())],
                  source_development_and_this_review_actuals_additional=True),
       resources=dict(scientific_cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall,
           peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           explicit_reads=sum(x['bytes'] for x in READS),decoded_saved_array_bytes=decode,read_receipts=READS,
           physical_io_and_import_cpu="unmeasured; process_time starts after imports",public_ingress_bytes=0),
       scope="Planning, derived consumed-data scores, public/source metadata and criterion summaries only; conditional trained prescription, no source-tail or arbitrary-site guarantee.")
    (HERE/'INDEPENDENT_CHECK.json').write_text(json.dumps(result,indent=2,default=default,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['resources','parametric_noncentral_t_check']},indent=2,default=default))

if __name__=='__main__':main()
