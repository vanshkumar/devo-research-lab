"""Price the qualified cohort and a focused proper-score primary family."""
from datetime import datetime,timezone
from collections import Counter
import hashlib,io,json,resource,time
from pathlib import Path
import numpy as np
from scipy.stats import beta,t,norm

HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'calibration-frontier-main-2026-11-05'
cpu,wall=time.process_time(),time.monotonic();IO=Counter();PINS={}


def read(p):
    b=p.read_bytes();IO['explicit_reads']+=len(b);PINS[p.name]=hashlib.sha256(b).hexdigest();return b


def get(p):return json.loads(read(p))
def serial(x):return x.tolist() if isinstance(x,np.ndarray) else x.item()
def rate(e):
    k=int(e.sum());n=len(e)
    return dict(rate=k/n,n=n,k=k,binomial95=[0. if k==0 else float(beta.ppf(.025,k,n-k+1)),1. if k==n else float(beta.ppf(.975,k+1,n-k))])


cohort=get(HERE/'QUALIFIED_COHORT.json');assert cohort['candidate_primary_evaluation']==192
with np.load(io.BytesIO(read(OLD/'REFINED_CONTRASTS.npz')),allow_pickle=False) as z:a={k:z[k] for k in z.files}
IO['decoded_array_bytes']+=sum(x.nbytes for x in a.values())
cols=get(OLD/'MAIN_FAMILY_REFINED.json')['columns'];analysis=get(OLD/'MAIN_ANALYSIS.json')
refs=['recent_selected','original'];ind=[next(i for i,r in enumerate(cols) if r['kind']=='fixed_refined' and r['reference']==ref and r['cutoff']==200 and r['metric']=='D') for ref in refs]
X=a['contributions'][:,ind];mu=X.mean(0);sd=X.std(0,ddof=1);res=X-mu
risks=np.array([next(r['equal_animal']['mixed'] for r in analysis['absolute_risks'] if r['condition']=='primary' and r['cutoff']==200 and r['model']==m) for m in ['recent100','growth']])
rng=np.random.default_rng(20261105151);R=20000;out=[]
for n in [76,107,116,192,203,229,565,806,1024]:
    counts=rng.multinomial(n,np.repeat(1/64,64),size=R)
    err=np.einsum('bi,ij->bj',counts,res,optimize=False)/n
    v=np.einsum('bi,ij->bj',counts,res**2,optimize=False)/n-err**2
    q=float(t.ppf(1-.05/4,n-1));se=np.sqrt(np.maximum(v,0)/(n-1));hw=q*se
    cases=[]
    for rel in [0.,.05,.15,.20]:
        # One common GRU risk must be used for both serious references.
        neural_risk=(1-rel)*risks[0]
        truth=.9*risks-neural_risk
        y=err+truth
        cases.append(dict(true_relative_benefit_vs_selected_recent=rel,
              implied_relative_benefit_each_reference=1-neural_risk/risks,
              establish_at_least10percent_over_BOTH=rate(np.all(y-hw>0,axis=1)),
              exclude10percent_against_recent=rate(y[:,0]+hw[:,0]<0),
              exclude10percent_against_BOTH=rate(np.all(y+hw<0,axis=1))))
    one=[]
    for j in range(2):
        truth=-5*sd;truth[j]=0
        one.append(rate(np.all(err+truth+hw<0,axis=1)))
    out.append(dict(n=n,critical=q,halfwidth=q*sd/np.sqrt(n),
           cases=cases,absence_if_saved_means_repeat=rate(np.all(err+mu+hw<0,axis=1)),
           exclude_recent_if_saved_means_repeat=rate(err[:,0]+mu[0]+hw[:,0]<0),
           all_boundary_any_false_positive=rate(np.any(err-hw>0,axis=1)),
           any_band_noncoverage=rate(np.any(np.abs(err)>hw,axis=1)),
           one_active_boundary_false_absence=one,
           larger_variance_stress='Normal approximation only:1.5x SD primary recent positive20% chance='+str(float(norm.cdf(.1*risks[0]*np.sqrt(n)/(1.5*sd[0])-q)))))
execution=get(OLD/'MAIN_EXECUTION.json');n=192
fixed=execution['timings']['fixed_three_conditions_two_streams_plus_exact']['cpu_seconds']*(2/3)*(n/64)/60
sources=execution['timings']['source32_reselection_and_dependent_forecasts']['cpu_seconds']*2*(n/64)/60
price=dict(n=n,primary_two_cutoffs1024_conservative_measured_scaling_cpu_minutes=fixed,
       all32_dependent_source_draws512_cpu_minutes=sources,
       author_with_controls_and25to75percent_overhead_cpu_minutes=[1.25*(fixed+sources)+10,1.75*(fixed+sources)+25],
       independent_result_challenge_cpu_minutes=[30,90],useful_revision_cpu_minutes=[60,120],
       independent_design_challenge_cpu_minutes=[10,20],source_payload_preflight_cpu_minutes=[10,20],closeout_cpu_minutes=[5,10],
       scientist_elapsed_hours=dict(payoff_design_review=[1.5,2.5],author_data_freeze_and_main=[6,10],result_challenge=[2,4],useful_revision=[1,3],closeout=[.5,1]),
       public_ingress_upper_bytes=cohort['hypothetical_main_source_ingress_upper_bytes'],
       raw_six_field_float64_decode_upper_bytes=cohort['hypothetical_main_six_field_float64_decode_upper_bytes'],
       proposed_whole_read_decode_gb=[5,10],proposed_peak_rss_gb=[1,3],proposed_local_storage_gb=[2,4],
       scope='Future price only, NOT allocated. Includes dependent ordinary forecasts for actual donor draws, not fake extra neural optimizations. Repeated neural-training-family cost/valid source-tail law remains unpriced and unearned.',
       precision='1024 primary particles are integration, not animals. Check split-stream error against scientific headroom before any numerical refinement; source512 may still be insufficient near a zeroD boundary.')
result=dict(utc=datetime.now(timezone.utc).isoformat(),primary_proposal='ONE proper-score family at200: two comparisons against frozen selected recent growth and retained original growth. D=.9R(reference)-R(GRU). Joint95%two-sided Bonferroni Student bands. Positive material claim requires BOTH lower bounds>0; a selected-reference upper<0 excludes10%value against that fixed available alternative. The old four2pp/10%family remains predeclared secondary robustness and cannot rescue the primary.',
       why='Early proper-score value is the unresolved serious question in the completed study; this pre-evaluation design focus is prospective for new animals, not retroactive repair of an old failed gate.',
       references=refs,source64_mean=mu,source64_sd=sd,source64_risks=risks,
       planning_scope='Borrowed consumed64 residual-shift law; no biological/source-tail guarantee. New genotype/protocol/site mixture and within-site dependence may change variance. Animal, site and donor uncertainty remain distinct.',
       power_rows=out,price=price,io=dict(IO),pins=PINS,cpu_seconds=time.process_time()-cpu,
       process_wall_seconds=time.monotonic()-wall,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(HERE/'FOCUSED_DESIGN.json').write_text(json.dumps(result,indent=2,default=serial)+'\n')
print(json.dumps(dict(primary=result['primary_proposal'],power_n192=next(r for r in out if r['n']==192),price=price,
         cpu_seconds=result['cpu_seconds'],io=dict(IO)),indent=2,default=serial))
