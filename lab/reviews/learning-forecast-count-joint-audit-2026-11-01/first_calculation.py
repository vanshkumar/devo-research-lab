"""Independent reconstruction from original saved ensembles, not author code."""
import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"
import hashlib, io, json, math, resource, sys, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
start=time.monotonic()
prior=json.loads((OUT/'SCHEMA_CALCULATION.json').read_text())
inputs=[]
def load(rel, npz=False):
    raw=(ROOT/rel).read_bytes()
    rec=dict(path=rel,containing_bytes=len(raw),decoded_bytes=0,sha256=hashlib.sha256(raw).hexdigest())
    if npz:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            rec['decoded_bytes']=sum(x.file_size for x in z.infolist())
        with np.load(io.BytesIO(raw),allow_pickle=False) as z:
            ans={k:z[k] for k in z.files}
    else:
        ans=json.loads(raw)
    inputs.append(rec)
    return ans,rec

manifest,_=load('campaigns/population_learning_transport_2026-10-28/protocols/SOURCE_FORECASTS.json')
original,orec=load('campaigns/population_learning_transport_2026-10-28/artifacts/results/SOURCE_ARRAYS.npz',True)
reference,rrec=load('lab/reviews/learning-forecast-information-audit-2026-11-01/RECONSTRUCTED_ENDPOINTS.npz',True)
subjects=original['subjects']; labs=original['labs']
assert len(subjects)==24 and len(set(subjects))==24
assert subjects.tolist()==reference['subjects'].tolist() and labs.tolist()==reference['labs'].tolist()
obsA=original['observed'][...,:2]
obsN=original['counts'][...,:2]
assert np.array_equal(obsA,reference['observed']) and np.array_equal(obsN,reference['observed_counts'])
obsK=np.rint(obsA*obsN).astype(np.int16)
assert np.max(np.abs(obsA*obsN-obsK))<1e-10
assert np.all(obsN>0) and np.all(obsK<=obsN) and np.all(obsK>=0)
Ns=np.empty((2,24,512,6,2),np.int16)
Ks=np.empty_like(Ns)
models=['rnn','growth']; identities={}; exact_ref=0
records={(r['subject'],r['model']):r for r in manifest['records'] if r['eligible'] and r['model'] in models and r['subject'] in set(subjects.tolist())}
assert len(records)==48
for m,model in enumerate(models):
    resid=0.0
    for i,subject in enumerate(subjects):
        r=records[(subject,model)]
        assert r['horizon']==3000
        d,rec=load(r['path'],True)
        assert rec['sha256']==r['sha256']
        a=d['samples'][...,:2]; n=d['counts'][...,:2]
        assert a.shape==(512,6,2) and n.shape==a.shape
        k=np.rint(a*n)
        resid=max(resid,float(np.max(np.abs(k-a*n))))
        assert np.all(n>0) and np.all(n<=500) and np.all(k>=0) and np.all(k<=n)
        assert np.max(np.abs(n-np.rint(n)))==0 and resid<1e-10
        if model=='rnn':
            assert np.array_equal(a,reference['autonomous'][i])
            assert np.array_equal(n,reference['autonomous_counts'][i])
            exact_ref+=1
        expected=original[model+'_means'][i]
        assert np.max(np.abs(a.mean(axis=(0,2))-expected))<1e-12
        Ns[m,i]=n; Ks[m,i]=k
    identities[model]=dict(paired_cells=int(Ns[m].size),max_integer_residual_counts=resid,min_N=int(Ns[m].min()),max_N=int(Ns[m].max()))

assert int(obsN.sum())==34378
terms=np.empty((2,24,6,2,4))
scores=np.empty((2,24,6,2,2))
metrics={}
for m,model in enumerate(models):
    A=Ks[m]/Ns[m]
    mean=A.mean(axis=1); pooled=Ks[m].sum(axis=1)/Ns[m].sum(axis=1)
    summaries={}
    for name,pred in [('mean_ratios',mean),('count_pooled',pooled)]:
        summaries[name]=dict(population_mae_pp=float(np.abs(pred.mean(axis=(0,2))-obsA.mean(axis=(0,2))).mean()*100),
            individual_equal_side_mae_pp=float(np.abs(pred.mean(axis=2)-obsA.mean(axis=2)).mean()*100),
            individual_side_mae_pp=float(np.abs(pred-obsA).mean()*100),
            cohort_bin_bias_pp=((pred-obsA).mean(axis=(0,2))*100).tolist())
    cov=((Ns[m]-Ns[m].mean(axis=1,keepdims=True))*(A-A.mean(axis=1,keepdims=True))).mean(axis=1)
    summaries['negative_covariance_cells']=int((cov<0).sum())
    summaries['covariance_identity_max_error']=float(np.max(np.abs(pooled-mean-cov/Ns[m].mean(axis=1))))
    metrics[model]=summaries
    for i in range(24):
        for b in range(6):
            for s in range(2):
                n=Ns[m,i,:,b,s].astype(float); k=Ks[m,i,:,b,s].astype(float)
                dn=n-obsN[i,b,s]; dk=k-obsK[i,b,s]
                # Orthogonal rotation of three-category Euclidean / sqrt(2).
                first=np.hypot(math.sqrt(.75)*dn,dk-.5*dn).mean()/500
                z=np.column_stack((math.sqrt(.75)*n,k-.5*n))/500
                unordered=pdist(z).sum()
                joint=first-unordered/(512*512)
                cfirst=np.abs(dn).mean()/500
                order=np.sort(n)
                cunordered=float(np.dot(2*np.arange(512)-511,order))/500
                count=cfirst-cunordered/(512*512)
                terms[m,i,b,s]=(first,unordered/(512*512),cfirst,cunordered/(512*512))
                scores[m,i,b,s]=(joint,count)

np.savez_compressed(OUT/'PAIRED_ENDPOINTS.npz',subjects=subjects,labs=labs,models=np.array(models),N=Ns,K=Ks,observed_N=obsN.astype(np.int16),observed_K=obsK,observed_A=obsA)
np.savez_compressed(OUT/'RECONSTRUCTED_SCORES.npz',terms=terms,scores=scores)
means=scores.mean(axis=(1,2,3))
result=dict(utc=datetime.now(timezone.utc).isoformat(),status='independent_original_paired_endpoint_and_declared_score_reconstruction',
    owner='01a1974a-e846-7e81-a7aa-ff54457bd7eb',fixed_start_utc='2026-11-01T13:28:03Z',
    command='campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python lab/reviews/learning-forecast-count-joint-audit-2026-11-01/first_calculation.py',
    units=dict(counts='integer exact100 opportunities/successes per500opportunity bin, omissions incorrect',accuracy='percentage points',scores='normalized opportunity-proportion energy/CRPS units'),
    subjects=subjects.tolist(),labs=labs.tolist(),verified_original_ensemble_pins=48,exact_prior_rnn_matches=exact_ref,observed_opportunities=int(obsN.sum()),
    observed_successes=int(obsK.sum()),identities=identities,metrics=metrics,
    scores=dict(rnn_joint=float(means[0,0]),growth_joint=float(means[1,0]),joint_gain=float(means[1,0]-means[0,0]),joint_relative_gain_percent=float(100*(1-means[0,0]/means[1,0])),
        rnn_count=float(means[0,1]),growth_count=float(means[1,1]),count_gain=float(means[1,1]-means[0,1])),
    inputs=inputs,resources=dict(cumulative_explicit_read_hash_decode_bytes=prior['resources']['containing_plus_decoded_bytes']+sum(x['containing_bytes']+x['decoded_bytes'] for x in inputs),
        context_runtime_failed_margin_bytes=30000000,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,elapsed_seconds=time.monotonic()-start,
        scientific_processes=1,numerical_threads=1,public_operations=0,downloads=0,ingress_bytes=0,raw_rows_read=0,physical_io_unknown=True))
native=json.dumps({k:result[k] for k in ['utc','status','verified_original_ensemble_pins','exact_prior_rnn_matches','observed_opportunities','observed_successes','scores','metrics','resources']},indent=2)
result['native_stdout']=native
(OUT/'FIRST_CALCULATION.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'FIRST_CALCULATION.stdout').write_text(native+'\n')
print(native)
