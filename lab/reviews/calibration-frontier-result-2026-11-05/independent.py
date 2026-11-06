"""Independent count-score and frozen-band reconstruction. No author imports."""
from __future__ import annotations
import hashlib
import io
import json
import resource
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import t

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MAIN = ROOT / 'lab/tasks/calibration-frontier-main-2026-11-05'
METRICS = ['mae', 'mixed', 'joint_NK', 'count', 'omission', 'literal_success', 'median_mae', 'mixed_U']


class Accounting:
    def __init__(self, stage):
        self.stage = stage
        self.cpu = time.process_time()
        self.wall = time.monotonic()
        self.reads = []

    def read(self, path):
        path = Path(path).resolve()
        raw = path.read_bytes()
        self.reads.append(dict(path=str(path.relative_to(ROOT)), bytes=len(raw),
                               decoded_array_bytes=0, sha256=hashlib.sha256(raw).hexdigest()))
        return raw

    def arrays(self, path, keys=None):
        raw = self.read(path)
        with np.load(io.BytesIO(raw), allow_pickle=False) as z:
            out = {k: z[k] for k in (keys if keys is not None else z.files)}
        self.reads[-1]['decoded_array_bytes'] = sum(v.nbytes for v in out.values())
        return out

    def json(self, path):
        return json.loads(self.read(path))

    def receipt(self):
        return dict(stage=self.stage, utc=datetime.now(timezone.utc).isoformat(),
                    scientific_cpu_seconds=time.process_time()-self.cpu,
                    scientific_process_wall_seconds=time.monotonic()-self.wall,
                    explicit_file_bytes=sum(r['bytes'] for r in self.reads),
                    decoded_array_bytes=sum(r['decoded_array_bytes'] for r in self.reads),
                    explicit_read_decode_bytes=sum(r['bytes']+r['decoded_array_bytes'] for r in self.reads),
                    reads=self.reads, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    imports_physical_io_provider_runtime='unknown; not inferred from successful outputs',
                    new_archive_ingress_bytes=0)


def save(name, value):
    def default(x):
        if isinstance(x, np.ndarray): return x.tolist()
        if isinstance(x, np.generic): return x.item()
        raise TypeError(type(x).__name__)
    (HERE/name).write_text(json.dumps(value, indent=2, default=default, allow_nan=False)+'\n')


def one_dimensional_energy(values, truth):
    x = np.sort(np.asarray(values, dtype=float))
    n = x.size
    # Sum of distances over unordered pairs; no diagonal contributes.
    pair_sum = np.dot(2*np.arange(n)-n+1, x)
    return float(np.abs(x-truth).mean()-pair_sum/(n*n))


def mixed_energy(n, k, observed_n, observed_k):
    """Euclidean energy of missing/ratio embedding divided by sqrt(2)."""
    n, k = np.asarray(n), np.asarray(k)
    total = len(n)
    positive = n > 0
    ratios = np.sort(k[positive]/n[positive])
    missing = total-len(ratios)
    missing_positive = np.sqrt(1-ratios+ratios**2)
    unordered = float(np.dot(2*np.arange(len(ratios))-len(ratios)+1, ratios)
                      + missing*missing_positive.sum())
    if observed_n > 0:
        y = observed_k/observed_n
        fit = (np.abs(ratios-y).sum()+missing*np.sqrt(1-y+y*y))/total
    else:
        fit = missing_positive.sum()/total
    return float(fit-unordered/(total*total)), float(fit-unordered/(total*(total-1)))


def embedding(n, k):
    n, k = np.asarray(n), np.asarray(k)
    z = np.zeros((len(n),3))
    pos = n > 0
    z[~pos,0] = 1
    z[pos,1] = k[pos]/n[pos]
    z[pos,2] = 1-z[pos,1]
    return z


def direct_energy(points, truth):
    x = np.asarray(points, float)
    return float(np.linalg.norm(x-truth,axis=1).mean()-pdist(x).sum()/len(x)**2)


def score(sample, observed, horizon):
    x, y = np.asarray(sample), np.asarray(observed)
    assert x.ndim == 2 and x.shape[1] == y.size == 7
    assert np.all(x >= 0) and np.all(x <= horizon)
    assert np.all(x[:,1] <= x[:,0]) and np.all(x[:,3] <= x[:,2])
    assert np.all(x[:,0]+x[:,2] <= horizon)
    mae, med, mixed, unbiased, joint, counts = [], [], [], [], [], []
    for a in [0,2]:
        n, k = x[:,a], x[:,a+1]
        on, ok = y[a:a+2]
        pos = n > 0
        m, u = mixed_energy(n,k,on,ok)
        mixed.append(m); unbiased.append(u)
        if on == 0 or not np.any(pos):
            mae.append(np.nan); med.append(np.nan)
        else:
            ratio = k[pos]/n[pos]
            mae.append(abs(ratio.mean()-ok/on))
            med.append(abs(np.median(ratio)-ok/on))
        points = np.stack((k,n-k,horizon-n),axis=-1)/horizon
        truth = np.array((ok,on-ok,horizon-on))/horizon
        joint.append(direct_energy(points,truth))
        counts.append(one_dimensional_energy(n/horizon,on/horizon))
    return np.array([np.mean(mae),np.mean(mixed),np.mean(joint),np.mean(counts),
                     one_dimensional_energy(x[:,4]/horizon,y[4]/horizon),
                     one_dimensional_energy(x[:,6]/horizon,y[6]/horizon),
                     np.mean(med),np.mean(unbiased)])


def bootstrap_weights(seed=20261105077, repeats=20000, stratified=True):
    generator = np.random.default_rng(seed)
    result = np.zeros((repeats,64),dtype=np.int16)
    groups = [(0,40),(40,64)] if stratified else [(0,64)]
    for a,b in groups:
        draws = generator.integers(a,b,size=(repeats,b-a))
        # Independent direct bincount construction of whole-animal multiplicities.
        for r in range(repeats): result[r] += np.bincount(draws[r], minlength=64)
    assert np.all(result.sum(axis=1) == 64)
    return result


def standard_error(x, stratified=True):
    if stratified:
        return np.sqrt((40*np.var(x[:40],axis=0,ddof=1)+24*np.var(x[40:],axis=0,ddof=1))/64**2)
    return np.std(x,axis=0,ddof=1)/8


def bands(x, weights=None, stratified=True, selected=None):
    x = np.asarray(x,float)
    assert x.shape[0] == 64 and np.isfinite(x).all()
    mu = x.mean(axis=0); se = standard_error(x,stratified)
    active = se > 1e-14
    assert np.all(np.ptp(x[:,~active],axis=0) < 1e-12)
    if weights is None: weights = bootstrap_weights(stratified=stratified)
    largest = np.empty(len(weights)); chosen = np.empty(len(weights))
    selected = np.arange(x.shape[1]) if selected is None else np.asarray(selected)
    for a in range(0,len(weights),256):
        w = weights[a:a+256].astype(float)/64
        centered = np.einsum('bi,ij->bj',w,x,optimize=False)-mu
        standardized = np.divide(centered,se,out=np.zeros_like(centered),where=active)
        largest[a:a+len(w)] = np.abs(standardized).max(axis=1)
        chosen[a:a+len(w)] = np.abs(standardized[:,selected]).max(axis=1)
    def interval(critical):
        return dict(critical=critical, lower=mu-critical*se, upper=mu+critical*se)
    return dict(point=mu,se=se,primary=interval(float(np.quantile(chosen,.95))),
                joint=interval(float(np.quantile(largest,.95))),
                bonferroni_primary=interval(float(t.ppf(1-.05/(2*len(selected)),23))),
                bonferroni_joint=interval(float(t.ppf(1-.05/(2*x.shape[1]),23))),
                zero_se=np.flatnonzero(~active))


def primary_vectors(metrics):
    # Axes of fixed: animal, condition, cutoff, actor, horizon, metric.
    return np.column_stack([v for c in range(2) for v in
                            (metrics[:,0,c,1,1,0]-metrics[:,0,c,3,1,0],
                             .9*metrics[:,0,c,1,1,1]-metrics[:,0,c,3,1,1])])


def cohorts_and_sites(x, labs):
    lab = np.asarray(labs)
    sites = sorted(set(lab))
    means = np.stack([x[lab==s].mean(0) for s in sites])
    site_point = means.mean(0)
    # Conservative t band over the four declared quantities, equal observed sites.
    site_se = means.std(0,ddof=1)/np.sqrt(len(sites))
    crit = float(t.ppf(1-.05/(2*x.shape[1]),len(sites)-1))
    contributions = np.stack([(x[lab==s]-x.mean(0)).sum(0)/64 for s in sites])
    signs = 2*((np.arange(2**len(sites))[:,None]>>np.arange(len(sites)))&1)-1
    cluster_se = np.sqrt(len(sites)/(len(sites)-1)*np.sum(contributions**2,axis=0))
    changes = signs @ contributions * np.sqrt(len(sites)/(len(sites)-1))
    critical = float(np.quantile(np.max(np.abs(changes/cluster_se),axis=1),.95))
    return dict(old40=x[:40].mean(0),later24=x[40:].mean(0),
                sites=[dict(site=s,n=int((lab==s).sum()),mean=means[i]) for i,s in enumerate(sites)],
                equal_site_point=site_point,equal_site_bonferroni_lower=site_point-crit*site_se,
                equal_site_bonferroni_upper=site_point+crit*site_se,
                animal_weight_cluster_wild_upper=x.mean(0)+critical*cluster_se,
                animal_weight_cluster_wild_lower=x.mean(0)-critical*cluster_se,
                cluster_critical=critical,
                leave_one_site_out=[dict(omitted=s,mean=x[lab!=s].mean(0)) for s in sites])


def calibration_summary(samples, observed, horizon):
    out = []
    for side in [0,2]:
        coverage = {k:[] for k in ['ratio80','ratio95','count80','count95']}
        positive_mass=[]; mean_ratios=[];pooled=[];truths=[];pit=[]
        rng=np.random.default_rng(20261105083+side)
        for x,y in zip(samples,observed):
            n,k=x[:,side],x[:,side+1];on,ok=y[side:side+2];positive=n>0
            positive_mass.append(float(positive.mean()))
            if np.any(positive) and on>0:
                r=k[positive]/n[positive];truth=ok/on
                mean_ratios.append(r.mean());pooled.append(k.sum()/n.sum());truths.append(truth)
                pit.append(float(np.mean(r<truth)+rng.random()*np.mean(r==truth)))
                for level,q in [('80',(.1,.9)),('95',(.025,.975))]:
                    interval=np.quantile(r,q);coverage['ratio'+level].append(interval[0]<=truth<=interval[1])
            for level,q in [('80',(.1,.9)),('95',(.025,.975))]:
                interval=np.quantile(n,q);coverage['count'+level].append(interval[0]<=on<=interval[1])
        out.append(dict(sign=-1 if side==0 else 1,positive_mass_range=[min(positive_mass),max(positive_mass)],
                        coverage={k:float(np.mean(v)) for k,v in coverage.items()},
                        expected_ratio_mean=float(np.mean(mean_ratios)),count_pooled_mean=float(np.mean(pooled)),
                        observed_ratio_mean=float(np.mean(truths)),randomized_PIT_histogram=np.histogram(pit,bins=np.linspace(0,1,11))[0],
                        pit_order='separate independent diagnostic seed20261105083+side; author ordering not copied'))
    return out


def fixed():
    meter = Accounting('early fixed-output reconstruction')
    freeze = meter.json(MAIN/'MAIN_RUN_FREEZE.json')
    obs = meter.arrays(MAIN/'MAIN_OBSERVED.npz')
    data = meter.arrays(MAIN/'MAIN_COUNTS.npz',keys=['samples','exact_samples','subjects','names','conditions','cutoffs','windows'])
    assert data['subjects'].tolist() == obs['subjects'].tolist() == freeze['subjects']
    assert obs['cohort'].tolist() == ['old40']*40+['later24']*24
    assert obs['columns'].tolist() == ['N_left','K_left','N_right','K_right','omissions','choice_negative','literal_feedback_success']
    assert data['names'].tolist() == ['growth','recent100','recent250','gru']
    s,e,y = data['samples'],data['exact_samples'],obs['observed']
    fm=np.empty((64,3,2,4,2,8));sm=np.empty((64,3,2,4,2,2,8));em=np.empty((64,3,2,2,8))
    for i in range(64):
        for condition in range(3):
            for c in range(2):
                for actor in range(4):
                    for w,h in enumerate([500,2000]):
                        draws=s[i,condition,c,actor,:,:,w,:]
                        fm[i,condition,c,actor,w]=score(draws.reshape(-1,7),y[i,w],h)
                        for stream in range(2): sm[i,condition,c,actor,stream,w]=score(draws[stream],y[i,w],h)
                for w,h in enumerate([500,2000]): em[i,condition,c,w]=score(e[i,condition,c,:,w,:],y[i,w],h)
    assert np.isfinite(fm).all() and np.isfinite(sm).all() and np.isfinite(em).all()
    x=primary_vectors(fm);weights=bootstrap_weights();primary=bands(x,weights)
    alternate=bands(x,bootstrap_weights(20261105078,stratified=False),stratified=False)
    numerical=[]
    for condition in range(3):
        for c in range(2):
            for a in range(3):
                contrasts=[]
                for stream in range(2):
                    o=sm[:,condition,c,a,stream,1];g=sm[:,condition,c,3,stream,1]
                    contrasts.append(np.column_stack([o[:,0]-g[:,0],.9*o[:,1]-g[:,1]]).mean(0))
                d=em[:,condition,c,1]-sm[:,condition,c,3,0,1]
                numerical.append(dict(condition=freeze['conditions'][condition],cutoff=[200,1000][c],
                                      reference=data['names'][a],stream_contrasts=contrasts,
                                      stream_contrast_abs_difference=np.abs(contrasts[0]-contrasts[1]),
                                      exact_minus_linear_gru_mean_metrics=d.mean(0),
                                      exact_minus_linear_max_abs_animal_metrics=np.abs(d).max(0)))
    cal=[]
    for c in range(2):
        for a in range(4):
            particles=s[:,0,c,a,:,:,1,:].reshape(64,512,7)
            cal.append(dict(cutoff=[200,1000][c],actor=data['names'][a],
                            diagnostics=calibration_summary(particles,y[:,1],2000),
                            mean_omissions=float(particles[:,:,4].mean()),observed_omissions=float(y[:,1,4].mean()),
                            mean_literal_success=float(particles[:,:,6].mean()),observed_literal_success=float(y[:,1,6].mean())))
    source=meter.arrays(MAIN/'SOURCE_COUNTS.npz',keys=['samples','observed','subjects','names','conditions'])
    source_metrics=np.empty((10,3,2,3,2,8))
    for i in range(10):
        for k in range(3):
            for c in range(2):
                for a in range(3):
                    for w,h in enumerate([500,2000]):
                        source_metrics[i,k,c,a,w]=score(source['samples'][i,k,c,a,:,w,:],source['observed'][i,w],h)
    # Independent source-site mapping is metadata only, not a trial read.
    access=meter.json(MAIN/'PREP_ACCESS.json')
    source_manifest=meter.json(ROOT/'lab/tasks/acquisition-rule-vs-tracker-2026-11-05/SOURCE_FIT6000_MANIFEST.json')
    source_labs=[source_manifest['disposition'][s]['lab'] for s in source['subjects']]
    source_contrary=[]
    for c in range(2):
        o=source_metrics[:,0,c,1,1];g=source_metrics[:,0,c,2,1]
        z=np.column_stack([o[:,0]-g[:,0],.9*o[:,1]-g[:,1]])
        source_contrary.append(dict(cutoff=[200,1000][c],equal_animal=z.mean(0),
                                    equal_site=np.mean([z[np.array(source_labs)==lab].mean(0) for lab in sorted(set(source_labs))],axis=0),
                                    recent_risks=o.mean(0),gru_risks=g.mean(0)))
    np.savez_compressed(HERE/'FIXED_CACHE.npz',fixed=fm,streams=sm,exact_gru=em,observed=y,
                        subjects=obs['subjects'],labs=obs['labs'],cohort=obs['cohort'],metrics=METRICS,
                        source_selection_metrics=source_metrics,bootstrap_weights=weights)
    output=dict(primary_columns=['A200','D200','A1000','D1000'],primary_bands=primary,
                alternate_unstratified_bands=alternate,cohort_site=cohorts_and_sites(x,obs['labs']),
                primary_mean_risks=fm[:,0,:,:,1,:].mean(0),numerical=numerical,calibration=cal,
                source_selection_contrary=source_contrary,
                semantic_checks=dict(absolute_values_before_sign_average=True,particles_are_not_animals=True,
                                     missing_accuracy_not_zero_imputed=True,full_count_energy_has_no_sqrt2_scaling=True))
    save('FIXED_RECONSTRUCTION.json',output)
    save('FIXED_RESOURCES.json',meter.receipt())
    print(json.dumps(dict(primary_point=x.mean(0).tolist(),primary_upper=primary['primary']['upper'].tolist(),
                          bonferroni_upper=primary['bonferroni_primary']['upper'].tolist(),
                          critical=primary['primary']['critical'],resources=meter.receipt()),default=lambda z:z.tolist()))


if __name__ == '__main__':
    stage = sys.argv[1] if len(sys.argv)>1 else 'fixed'
    try:
        {'fixed':fixed}[stage]()
    except BaseException as exc:
        save('FAILURE_'+str(time.time_ns())+'.json',dict(stage=stage,error=repr(exc)))
        raise
