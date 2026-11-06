"""Independent joint-score reconstruction, uncertainty, and ONE accuracy contrary."""
import os
for _v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_v]='1'
import hashlib,io,json,math,resource,sys,time,zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import scipy
from scipy.spatial.distance import pdist,squareform
from scipy.stats import t

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
M=512
inputs=[]
def load(path,npz=False):
    path=Path(path)
    if not path.is_absolute(): path=ROOT/path
    raw=path.read_bytes()
    rec=dict(path=str(path.relative_to(ROOT)),containing_bytes=len(raw),decoded_bytes=0,sha256=hashlib.sha256(raw).hexdigest())
    if npz:
        with zipfile.ZipFile(io.BytesIO(raw)) as z: rec['decoded_bytes']=sum(x.file_size for x in z.infolist())
        with np.load(io.BytesIO(raw),allow_pickle=False) as z: data={k:z[k] for k in z.files}
    else: data=json.loads(raw)
    inputs.append(rec)
    return data,rec

freeze,_=load(OUT/'FROZEN_PLAN.json')
for name,sha in freeze['pins'].items():
    raw=(OUT/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==sha,(name,'review freeze mismatch')
    inputs.append(dict(path=str((OUT/name).relative_to(ROOT)),containing_bytes=len(raw),decoded_bytes=0,sha256=sha))
assert datetime.now(timezone.utc)<datetime.fromisoformat('2026-11-01T14:28:03+00:00')
e,_=load(OUT/'PAIRED_ENDPOINTS.npz',True)
first,_=load(OUT/'FIRST_CALCULATION.json')
N=e['N'].astype(float); K=e['K'].astype(float); on=e['observed_N'].astype(float); ok=e['observed_K'].astype(float)
A=K/N; oa=ok/on; labs=e['labs']; subjects=e['subjects']
scores=np.zeros((2,24,6,2,3,2)) # model,animal,bin,side,joint/count/ratio,V/U
terms=np.zeros((2,24,6,2,3,2)) # mean distance, unordered sum
pseudovalues=np.zeros((2,24,512,3)) # per-animal twelve-cell averages
blocks=np.zeros((2,24,8,3))
delete_checks=[]
for m in range(2):
    for i in range(24):
        for b in range(6):
            for s in range(2):
                n=N[m,i,:,b,s]; k=K[m,i,:,b,s]; a=A[m,i,:,b,s]
                dn=n-on[i,b,s]; dk=k-ok[i,b,s]
                z=np.column_stack((math.sqrt(.75)*n,k-.5*n))/500
                firstdist=[np.hypot(math.sqrt(.75)*dn,dk-.5*dn)/500,np.abs(dn)/500,np.abs(a-oa[i,b,s])]
                distances=[squareform(pdist(z)),np.abs(n[:,None]-n[None,:])/500,np.abs(a[:,None]-a[None,:])]
                for f in range(3):
                    d=distances[f]; dsum=float(np.sum(d)/2); afirst=float(np.mean(firstdist[f]))
                    v=afirst-dsum/(M*M); u=afirst-dsum/(M*(M-1))
                    scores[m,i,b,s,f]=(v,u); terms[m,i,b,s,f]=(afirst,dsum)
                    pv=firstdist[f]+dsum/((M-1)*(M-2))-d.sum(axis=1)/(M-2)
                    assert abs(pv.mean()-u)<1e-12
                    pseudovalues[m,i,:,f]+=pv/12
                    for h in range(8):
                        sl=slice(h*64,(h+1)*64)
                        blocks[m,i,h,f]+=(firstdist[f][sl].mean()-d[sl,sl].sum()/(2*64*63))/12
                    if i in (0,23) and b==0 and s==0:
                        for j in (0,17,255,511):
                            um=(firstdist[f].sum()-firstdist[f][j])/(M-1)-(dsum-d[j].sum())/((M-1)*(M-2))
                            err=abs(M*u-(M-1)*um-pv[j])
                            assert err<1e-11
                            delete_checks.append(dict(model=m,animal=i,functional=f,particle=j,error=float(err)))

idx=np.random.default_rng(2026110101).integers(0,24,size=(20000,24))
def summarize(s,pv,block):
    by_animal=s.mean(axis=(2,3))
    d=by_animal[1]-by_animal[0]
    avg=float(d.mean()); se=float(d.std(ddof=1)/math.sqrt(24))
    groups=np.unique(labs); sums=np.array([np.sum(d[labs==g]-avg) for g in groups])
    cse=float(np.sqrt(len(groups)/(len(groups)-1)*np.sum(sums*sums)/24**2))
    pvdiff=pv[1]-pv[0]
    mcse=float(np.sqrt(np.sum(np.var(pvdiff,axis=1,ddof=1)/512))/24)
    blockdiff=(block[1]-block[0]).mean(axis=0)
    return dict(rnn=float(by_animal[0].mean()),growth=float(by_animal[1].mean()),growth_minus_rnn=avg,
        relative_gain_percent=float(100*avg/by_animal[1].mean()),animal_bootstrap95=np.quantile(d[idx].mean(axis=1),[.025,.975]).tolist(),
        animal_t95=[avg-float(t.ppf(.975,23))*se,avg+float(t.ppf(.975,23))*se],
        cluster_cr1_se=cse,lab_cr1_t95=[avg-float(t.ppf(.975,4))*cse,avg+float(t.ppf(.975,4))*cse],
        improving_animals=int(np.sum(d>0)),animal_differences=d.tolist(),
        labs=[dict(lab=g,n=int(np.sum(labs==g)),contrast=float(d[labs==g].mean()),leave_out_contrast=float(d[labs!=g].mean())) for g in groups],
        paired_particle_U_jackknife_mcse=mcse,fixed_eight_block_U_contrasts=blockdiff.tolist())

summaries={}
for f,name in enumerate(('declared_joint','declared_count_reference','ONE_contrary_accuracy_ratio')):
    summary=summarize(scores[...,f,0],pseudovalues[...,f],blocks[...,f])
    ucontrast=float((scores[1,...,f,1]-scores[0,...,f,1]).mean())
    summary['U_growth_minus_rnn']=ucontrast
    summary['V_to_U_contrast_change']=ucontrast-summary['growth_minus_rnn']
    summary['approximate_mc95']=[ucontrast-1.96*summary['paired_particle_U_jackknife_mcse'],ucontrast+1.96*summary['paired_particle_U_jackknife_mcse']]
    summary['first_distance_terms']=terms[...,f,0].mean(axis=(1,2,3)).tolist()
    summary['V_spread_terms']=(terms[...,f,1]/(M*M)).mean(axis=(1,2,3)).tolist()
    summaries[name]=summary

authorbase=ROOT/'lab/tasks/learning-forecast-count-joint-audit-2026-11-01'
author_audit={}
for name in ('ENDPOINTS.npz','COMPARISON_OBJECTS.npz','SCORES.npz'):
    d,rec=load(authorbase/name,True)
    author_audit[name]=dict(input_pin=rec,schemas={k:dict(shape=list(v.shape),dtype=str(v.dtype)) for k,v in d.items()})
    # Pin check without loading/executing any author code.
    known={'ENDPOINTS.npz':'6b6d699fa2dd445ebda98f43a7921271b5e341c13ae75dac4ca6bc0d8a55aac5','COMPARISON_OBJECTS.npz':'2c7f26c9e70c4fb2c0213ece3fa5aceb266b29fcfe0960d712c523e103c1bf09','SCORES.npz':'1f7cece02eada666ea3a3f1e20bd0e804bd5c97a73577ab7b36b01ee13c68585'}
    assert rec['sha256']==known[name]
    # Deterministic labeled field audit follows in final_audit.py after schema inspection.
author_result,_=load(authorbase/'RESULT.json')
author_freeze,_=load(authorbase/'FROZEN_PLAN.json')
np.savez_compressed(OUT/'REVIEW_ARRAYS.npz',scores=scores,terms=terms,pseudovalues=pseudovalues,blocks=blocks,bootstrap_indices=idx)
result=dict(utc=datetime.now(timezone.utc).isoformat(),status='independent_reconstruction_and_single_contrary_executed',summaries=summaries,
    delete_one_checks=delete_checks,source_chronology=dict(author_freeze_utc=author_freeze['utc'],review_freeze_utc=freeze['utc'],consistent_ordering_not_independent_nonaccess_proof=True),
    inputs=inputs,resources=dict(cumulative_explicit_read_hash_decode_bytes=first['resources']['cumulative_explicit_read_hash_decode_bytes']+freeze['freeze_read_hash_bytes']+sum(r['containing_bytes']+r['decoded_bytes'] for r in inputs),
    context_runtime_failed_margin_bytes=30000000,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,scientific_processes=1,numerical_threads=1,
    public_operations=0,downloads=0,ingress_bytes=0,raw_rows_read=0,physical_io_unknown=True),environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,executable=sys.executable))
(OUT/'REVIEW_NUMBERS.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'AUTHOR_ASSET_AUDIT.json').write_text(json.dumps(author_audit,indent=2)+'\n')
contrary=dict(utc=result['utc'],status='ONE_predeclared_accuracy_marginal_energy_test',predeclared_in='DESIGN.md',review_freeze_utc=freeze['utc'],
    units='accuracy-probability CRPS; positive growth-minus-RNN favors RNN',**summaries['ONE_contrary_accuracy_ratio'],
    interpretation_limits='Changed marginal accuracy score, not a repaired gate or conditional distribution given observed counts. Cannot subtract across metrics, prove counts explain all gain or identify a biological cause.')
(OUT/'CONTRARY.json').write_text(json.dumps(contrary,indent=2)+'\n')
native=json.dumps(dict(utc=result['utc'],summaries=summaries,resources=result['resources']),indent=2)
(OUT/'REVIEW.stdout').write_text(native+'\n')
print(native)
print(json.dumps(author_audit,indent=2))
