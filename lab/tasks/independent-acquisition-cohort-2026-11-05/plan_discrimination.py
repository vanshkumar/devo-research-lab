"""Independent planning from saved consumed64 contributions; no trial I/O.

Empirical residual-shift calculations price discrimination, not biological power
or a validated source-tail guarantee. No author numerical module is imported.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import resource
import time

import numpy as np
from scipy.stats import beta,norm,t

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'calibration-frontier-main-2026-11-05'
IO=Counter();PINS={}


def read(p):
    b=p.read_bytes();IO['explicit_read_bytes']+=len(b)
    PINS[p.name]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return b


def get(p):return json.loads(read(p))
def save(n,x):(HERE/n).write_text(json.dumps(x,indent=2,default=serial,allow_nan=False)+'\n')
def serial(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)


def rate(event):
    k=int(np.sum(event));n=len(event)
    return dict(events=k,replicates=n,rate=k/n,exact_binomial95=[
        0. if k==0 else float(beta.ppf(.025,k,n-k+1)),
        1. if k==n else float(beta.ppf(.975,k+1,n-k))])


def min_n(sd,gap,family=4,power=.8):
    if gap<=0:return None
    # Conservative two-sided family bands; exact-boundary80% decisions are impossible.
    z=norm.ppf(power);n=max(3,int(np.ceil((sd*(norm.ppf(1-.05/(2*family))+z)/gap)**2)))
    while n<2_000_000 and gap/(sd/np.sqrt(n))-t.ppf(1-.05/(2*family),n-1)<z:n+=1
    return n


def main():
    cpu,wall=time.process_time(),time.monotonic()
    with np.load(io.BytesIO(read(OLD/'REFINED_CONTRASTS.npz')),allow_pickle=False) as z:
        a={k:z[k] for k in z.files}
    IO['decoded_array_bytes']+=sum(v.nbytes for v in a.values())
    family=get(OLD/'MAIN_FAMILY_REFINED.json')['columns'];analysis=get(OLD/'MAIN_ANALYSIS.json')
    pi=a['primary_indices'];X=a['contributions'][:,pi];assert X.shape==(64,4)
    mu=X.mean(0);sd=X.std(0,ddof=1);res=X-mu
    risk=np.array([next(r for r in analysis['absolute_risks'] if r['condition']=='primary' and r['model']=='recent100' and r['cutoff']==c)['equal_animal']['mixed'] for c in (200,1000)])
    margins=np.array([.02,0.,.02,0.]);distance=np.array([.01,.05*risk[0],.01,.05*risk[1]])
    labels=['A200','D200','A1000','D1000']
    source=[]
    for draw in range(32):
        ind=[next(i for i,r in enumerate(family) if r['kind']=='source' and r['draw']==draw and r['reference']=='recent_selected' and r['neural']=='linear256' and r['cutoff']==c and r['metric']==m) for c,m in [(200,'A'),(200,'D'),(1000,'A'),(1000,'D')]]
        source.append(a['contributions'][:,ind])
    source=np.stack(source);source_mu=source.mean(1);source_sd=source.std(1,ddof=1)
    sites=np.array(a['labs']);per_site=np.array([X[sites==s].mean(0) for s in sorted(set(sites))])
    design= dict(primary_family=[family[i] for i in pi],margins=margins,mean=mu,sd=sd,
        unstratified_se64=sd/8,correlation=np.corrcoef(X.T),
        near_boundary_distance=distance,
        near_boundary_meaning='Accuracy1pp versus3pp at2pp boundary; proper benefit5% versus15% at10% boundary, risk anchored to saved selected growth. Not a retuned gate.',
        normal_plus_student80_n_each=[min_n(s,g) for s,g in zip(sd,distance)],
        source32_point_min=source_mu.min(0),source32_point_max=source_mu.max(0),
        source32_point_sd=source_mu.std(0,ddof=1),source32_max_animal_sd=source_sd.max(0),
        source32_max_n_to_exclude_each=[max([min_n(source_sd[j,k],margins[k]-source_mu[j,k],family=128) or 2_000_000 for j in range(32)]) for k in range(4)],
        source_interpretation='Finite coupled donor/selection perturbations conditional on unchanged neural fit. Their point SD is a diagnostic, not a95% source-tail variance. Additional evaluation animals do not create new donor subjects or repeated neural fits.',
        site_means=per_site,equal_site_sd=per_site.std(0,ddof=1),
        site_interpretation='Nine observed-site means with singleton sites and unequal animals; no arbitrary-new-site power/coverage. New animals at same sites do not create independent sites.',
        original_growth_retained=True)
    rng=np.random.default_rng(20261105118);R=20000
    grid=[14,34,64,79,82,90,93,127,160,240,320,512,768,1024,1536]
    rows=[];controls=[]
    for n in grid:
        counts=rng.multinomial(n,np.repeat(1/64,64),size=R)
        # Explicit contractions avoid the workspace's previously observed BLAS warnings.
        e=np.einsum('bi,ij->bj',counts,res,optimize=False)/n
        second=np.einsum('bi,ij->bj',counts,res**2,optimize=False)/n
        se=np.sqrt(np.maximum(second-e**2,0)/(n-1))
        q=float(t.ppf(1-.05/8,n-1));hw=q*se
        mean_at_old=e+mu
        negative=e+margins-distance
        positive=e+margins+distance
        row=dict(n=n,bonferroni_critical=q,expected_halfwidth=q*sd/np.sqrt(n),
                 positive_near_boundary_each=[rate(positive[:,j]-hw[:,j]>margins[j]) for j in range(4)],
                 absence_near_boundary_all=rate(np.all(negative+hw<margins,axis=1)),
                 absence_if_saved_means_repeat=rate(np.all(mean_at_old+hw<margins,axis=1)),
                 predictive_claim='Conditional trained-instance across independent animals only; borrowed residual law is uncertain')
        rows.append(row)
        if n in [82,127,512,1024]:
            false_positive=rate(np.any(e-hw>0,axis=1))
            noncoverage=rate(np.any(np.abs(e)>hw,axis=1))
            one=[]
            for j in range(4):
                means=margins-5*sd;means[j]=margins[j]
                one.append(rate(np.all(e+means+hw<margins,axis=1)))
            controls.append(dict(n=n,all_boundary_any_false_material_positive=false_positive,
                  all_boundary_false_absence=rate(np.all(e+hw<0,axis=1)),
                  one_active_boundary_false_absence=one,any_band_noncoverage=noncoverage,
                  interpretation='Empirical shifted contribution laws, not autonomous plants, biological power or empirical-data95% guarantee. Composite absence null uses each one-active-boundary case.'))
    # Finite-envelope planning uses all32*4 columns jointly with conservative Bonferroni.
    finite=[]
    for n in [82,93,127,320,512,1024,1536]:
        q=t.ppf(1-.05/(2*128),n-1)
        upper=source_mu+q*source_sd/np.sqrt(n)
        finite.append(dict(n=n,critical=q,max_source_upper=upper.max(0),
                    all128_nominal_upper_below_margin=bool(np.all(upper<margins)),
                    scope='Expected-width finite-envelope projection only. No joint biological power and no source-tail guarantee.'))
    # Full investigation price scales measured completed work, not particle precision alone.
    execution=get(OLD/'MAIN_EXECUTION.json');account=get(OLD/'FINAL_ACCOUNTING.json')
    fixed_cpu=execution['timings']['fixed_three_conditions_two_streams_plus_exact']['cpu_seconds']
    draw_cpu=execution['timings']['source32_reselection_and_dependent_forecasts']['cpu_seconds']
    price=[]
    for n in [93,127,512,1024]:
        # Fixed primary1condition1024 approximates2/3of3condition512+exact cost;
        # no exact-prefix expansion is needed given saved negligible effects.
        fixed=(fixed_cpu*2/3)*(n/64)/60
        # Reserve2x because future source simulations need512instead of256particles;
        # shared draw reselection cost is deliberately over-scaled conservatively.
        dependent=(draw_cpu*2)*(n/64)/60
        price.append(dict(n=n,primary1024_measured_scaling_cpu_minutes=fixed,
              dependent32_at512_conservative_cpu_minutes=dependent,
              author_main_with_controls_and25to75percent_overhead_cpu_minutes=[1.25*(fixed+dependent)+10,1.75*(fixed+dependent)+25],
              independent_result_and_useful_revision_cpu_minutes=[.5*(fixed+dependent)+30,1.0*(fixed+dependent)+90],
              neural_repeated_training_cost='Not included; unavailable measured basis. A family-level claim needs a separately priced actual neural-refit pilot and source sample; no speculative certification.'))
    result=dict(utc=datetime.now(timezone.utc).isoformat(),status='complete',
        purpose='Plan sufficient positive/negative discrimination without opening any new candidate outcomes',
        design=design,power_rows=rows,controls=controls,source_finite_envelope=finite,
        whole_investigation_scaling=price,
        historical_author_cpu_seconds=account['whole_author_recorded_scientific_cpu_seconds'],
        prior_charges='All original failures, source/decode/exposure charges and unmeasured physical/provider/import/failed-process costs retained. This is additional planning, not a refund.',
        limitations=['Residual and site laws are consumed/postvalidation and may not transfer to new genotype/protocol mixtures.',
          'At an exact material boundary80% rejection/absence is not attainable under valid5% error control.',
          'Source perturbations are dependent forecasts, not new animals. Disjoint evaluation does not identify repeated neural-training procedure.',
          'The new catalogue upper bound127 is before missing fields/chronology/horizon and source-only exclusions; it is not127 qualified evaluation units.'],
        io=dict(IO),pins=PINS,cpu_seconds=time.process_time()-cpu,
        process_wall_seconds=time.monotonic()-wall,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save('DISCRIMINATION.json',result)
    print(json.dumps(dict(design={k:design[k] for k in ['mean','sd','near_boundary_distance','normal_plus_student80_n_each','source32_point_min','source32_point_max','source32_point_sd','source32_max_n_to_exclude_each']},
          selected_rows=[r for r in rows if r['n'] in [82,93,127,512,1024]],
          source_finite_envelope=finite,price=price,cpu_seconds=result['cpu_seconds'],io=dict(IO)),indent=2,default=serial))


if __name__=='__main__':main()
