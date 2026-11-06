"""Targeted three-reference and lean-cost sensitivity; saved derived scores only."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,io,json,time,resource
import numpy as np
from scipy.stats import t,norm
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OLD=ROOT/'lab/tasks/calibration-frontier-main-2026-11-05'
NEW=ROOT/'lab/tasks/independent-acquisition-cohort-2026-11-05'
cpu=time.process_time();wall=time.monotonic();reads=[]
def read(p):
    b=p.read_bytes();reads.append(dict(path=str(p.relative_to(ROOT)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()));return b
with np.load(io.BytesIO(read(OLD/'REFINED_SCORES.npz')),allow_pickle=False) as z:
    s=z['pooled1024']
risk=s[:,0,[1,0,2],1,1]
g=s[:,0,3,1,1]
X=.9*risk-g[:,None]
mu=X.mean(0);res=X-mu;sd=X.std(0,ddof=1);r=risk.mean(0)
R=50000;n=192;rng=np.random.default_rng(202611050520)
e=np.empty((R,3));sem=np.empty_like(e)
for start in range(0,R,1000):
    x=res[rng.integers(0,64,size=(min(1000,R-start),n))]
    e[start:start+len(x)]=x.mean(1)
    sem[start:start+len(x)]=x.std(1,ddof=1)/np.sqrt(n)
def rate(x):return dict(k=int(x.sum()),n=R,rate=float(x.mean()))
rows=[];controls=[]
for family in [2,3]:
    q=float(t.ppf(1-.05/(2*family),n-1))
    hw=sem*q
    one=[]
    for j in range(family):
        truth=np.ones(family)*5*sd[:family];truth[j]=0.
        one.append(rate(np.all(e[:,:family]+truth-hw[:,:family]>0,axis=1)))
    controls.append(dict(family=family,
        any_band_noncoverage=rate(np.any(np.abs(e[:,:family])>hw[:,:family],axis=1)),
        one_active_boundary_false_positive_for_all_material=one,
        recent_boundary_false_absence=rate(e[:,0]+hw[:,0]<0),
        scope='Finite shifted empirical residual-law checks only; not biological or universal coverage guarantees.'))
    for b in [0.,.05,.15,.2]:
        truth=.9*r-(1-b)*r[0]
        y=e+truth
        rows.append(dict(primary_references=family,relative_gain_vs_recent=b,
                    positive_primary=rate(np.all((y-hw)[:,:family]>0,axis=1)),
                    negative_recent=rate(y[:,0]+hw[:,0]<0),
                    primary_positive_but_fixed250_lower_nonpositive=rate(np.all((y-hw)[:,:2]>0,axis=1)&(y[:,2]-hw[:,2]<=0)),
                    q=q,relative_recent_expected_halfwidth=100*q*sd[0]/np.sqrt(n)/r[0]))
with np.load(io.BytesIO(read(OLD/'REFINED_CONTRASTS.npz')),allow_pickle=False) as z:
    c=z['contributions']
family=json.loads(read(OLD/'MAIN_FAMILY_REFINED.json'))['columns']
by_draw=[]
for d in range(32):
    j=next(j for j,a in enumerate(family) if a['kind']=='source' and a['reference']=='recent_selected' and a['cutoff']==200 and a['metric']=='D' and a['neural']=='linear256' and a['draw']==d)
    by_draw.append(dict(draw=d,D_mean=float(c[:,j].mean()),D_sd=float(c[:,j].std(ddof=1))))
execution=json.loads(read(OLD/'MAIN_EXECUTION.json'))
fixed=execution['timings']['fixed_three_conditions_two_streams_plus_exact']['cpu_seconds']*2/3*3/60
per_draw=execution['timings']['source32_reselection_and_dependent_forecasts']['cpu_seconds']*2*3/60/32
lean=[]
for draws in [0,1,2]:
    base=fixed+draws*per_draw
    author=[1.25*base+10,1.75*base+25]
    stages=dict(main_including_scoring_controls_overhead_cpu_minutes=author,
                data_preflight_cpu_minutes=[10,20],distinct_fresh_result_challenge_cpu_minutes=[30,60],
                one_useful_numerical_revision_cpu_minutes=[60,90],closeout_cpu_minutes=[5,10])
    total=[sum(v[j] for v in stages.values()) for j in (0,1)]
    lean.append(dict(dependent_source_draws=draws,fixed_base_cpu_minutes=fixed,
                     source_base_cpu_minutes=draws*per_draw,stages=stages,
                     additional_future_cpu_minutes=total,additional_future_scientist_elapsed_hours=[6.5,11.5],
                     existing_source_development_and_this_review="Already spent and additional, no refund",
                     basis="Measured old main fixed/dependent timings scaled conservatively to192; planning estimate, not guaranteed runtime."))
result=dict(utc=datetime.now(timezone.utc).isoformat(),status='complete',new_evaluation_payloads_read=False,
       three_reference_risks=r,three_reference_D_mean=mu,three_reference_sd=sd,rows=rows,controls=controls,
       most_neural_favorable_source_draw_early=sorted(by_draw,key=lambda x:x['D_mean'],reverse=True)[:3],
       lean_prices=lean,resource=dict(cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall,
          explicit_reads=sum(x['bytes'] for x in reads),decoded_arrays_bytes=s.nbytes+c.nbytes,
          peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,read_receipts=reads,public_ingress_bytes=0),
       interpretation="Sensitivity, not a main freeze or biological-power certification. Primary family must be fixed before new outcomes; fixed250 cannot be selected after seeing them. Source draw14 was selected solely on old consumed64 outputs as a serious contrary, not a new optimal reference.")
(HERE/'LEAN_SENSITIVITY.json').write_text(json.dumps(result,indent=2,default=lambda x:x.tolist() if hasattr(x,'tolist') else x,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='resource'},indent=2,default=lambda x:x.tolist() if hasattr(x,'tolist') else x))
