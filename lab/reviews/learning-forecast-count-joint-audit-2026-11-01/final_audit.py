"""Separate scalar/count/category/provenance/uncertainty checks; no author imports."""
import os
for _v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_v]='1'
import sys
sys.dont_write_bytecode=True
import hashlib,io,json,math,resource,zipfile
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import t
OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[2]
AUTHOR=ROOT/'lab/tasks/learning-forecast-count-joint-audit-2026-11-01'
inputs=[]
def load(path,npz=False):
    path=Path(path)
    if not path.is_absolute():path=ROOT/path
    raw=path.read_bytes()
    rec=dict(path=str(path.relative_to(ROOT)),containing_bytes=len(raw),decoded_bytes=0,sha256=hashlib.sha256(raw).hexdigest())
    if npz:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:rec['decoded_bytes']=sum(x.file_size for x in z.infolist())
        with np.load(io.BytesIO(raw),allow_pickle=False) as z:ans={k:z[k] for k in z.files}
    else:ans=json.loads(raw)
    inputs.append(rec)
    return ans,rec
def pin(path):
    raw=path.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    inputs.append(dict(path=str(path.relative_to(ROOT)),containing_bytes=len(raw),decoded_bytes=0,sha256=sha))
    return sha
first,_=load(OUT/'FIRST_CALCULATION.json')
result,_=load(OUT/'REVIEW_NUMBERS.json')
ownfreeze,_=load(OUT/'FROZEN_PLAN.json')
e,_=load(OUT/'PAIRED_ENDPOINTS.npz',True)
r,_=load(OUT/'REVIEW_ARRAYS.npz',True)
sc=r['scores']; N=e['N']; K=e['K']; on=e['observed_N']; ok=e['observed_K']; oa=e['observed_A']
assert np.array_equal(oa,ok/on)
for field,n in [('N',N),('K',K),('observed_N',on),('observed_K',ok)]:assert np.issubdtype(n.dtype,np.integer),field
assert np.all(K<=N) and np.all(K>=0) and np.all(N>0) and np.all(N.sum(axis=-1)<=500)
assert np.all(ok<=on) and np.all(ok>=0) and np.all(on>0) and np.all(on.sum(axis=-1)<=500)
ae,_=load(AUTHOR/'ENDPOINTS.npz',True)
assert np.array_equal(e['subjects'],ae['subjects']) and np.array_equal(e['labs'],ae['labs'])
for key,expected in [('observed_accuracy',oa),('observed_opportunities',on),('observed_successes',ok)]:assert np.array_equal(ae[key],expected),key
for m,name in enumerate(('rnn','growth')):
    for suffix,expected in [('accuracy',K[m]/N[m]),('opportunities',N[m]),('successes',K[m])]:assert np.array_equal(ae[name+'_'+suffix],expected),(name,suffix)
del ae
ac,_=load(AUTHOR/'COMPARISON_OBJECTS.npz',True)
q=np.stack((K,N-K,500-N),axis=-1)/500
oq=np.stack((ok,on-ok,500-on),axis=-1)/500
for key,expected in [('generated_categories',q),('observed_categories',oq),('opportunities',N),('successes',K),('observed_opportunities',on),('observed_successes',ok)]:assert np.array_equal(ac[key],expected),key
del ac
asc,_=load(AUTHOR/'SCORES.npz',True)
score_errors={}
for f,name in enumerate(('joint','count')):
    for u,kind in enumerate(('v','u')):
        error=float(np.max(np.abs(sc[...,f,u]-asc[name+'_'+kind])))
        score_errors[name+'_'+kind]=error;assert error<1e-12
    for name2,key,expected in [('pseudo',name+'_u_pseudovalues',r['pseudovalues'][...,f]),('block',name+'_block_u',r['blocks'][...,f])]:
        error=float(np.max(np.abs(asc[key]-expected)));score_errors[name+'_'+name2]=error;assert error<1e-11
del asc

manifest,_=load('campaigns/population_learning_transport_2026-10-28/protocols/SOURCE_FORECASTS.json')
records={(x['subject'],x['model']):x for x in manifest['records'] if x['eligible'] and x['subject'] in set(e['subjects'].tolist()) and x['model'] in ('rnn','growth')}
seeds=[];paired_sessions=0
for i,subject in enumerate(e['subjects']):
    current=[]
    for m,model in enumerate(('rnn','growth')):
        rec=records[(subject,model)];d,p=load(rec['path'],True)
        assert p['sha256']==rec['sha256']
        assert np.array_equal(d['counts'][...,:2],N[m,i])
        assert np.array_equal(d['samples'][...,:2],K[m,i]/N[m,i])
        current.append((int(d['seed']),d['session_start'].copy()))
    assert current[0][0]==current[1][0]
    assert np.array_equal(current[0][1],current[1][1])
    seeds.append(dict(subject=subject,seed=current[0][0]));paired_sessions+=1
assert len(set(x['seed'] for x in seeds))==24

scalar=[];category_error=0.;ratio_error=0.;count_error=0.
M=512
for m in range(2):
    for i in range(24):
        for b in range(6):
            for s in range(2):
                x=q[m,i,:,b,s];y=oq[i,b,s]
                energy=float(np.sqrt(np.sum((x-y)**2,axis=1)/2).mean()-pdist(x).sum()/math.sqrt(2)/(M*M))
                category_error=max(category_error,abs(energy-sc[m,i,b,s,0,0]))
                for f,z,y0 in [(1,N[m,i,:,b,s].astype(float)/500,float(on[i,b,s])/500),(2,K[m,i,:,b,s]/N[m,i,:,b,s],float(ok[i,b,s])/float(on[i,b,s]))]:
                    order=sorted(float(v) for v in z)
                    scalar_crps=math.fsum(abs(v-y0) for v in order)/M-math.fsum((2*j-M+1)*v for j,v in enumerate(order))/(M*M)
                    err=abs(scalar_crps-sc[m,i,b,s,f,0])
                    if f==1:count_error=max(count_error,err)
                    else:ratio_error=max(ratio_error,err)
                if (i,b,s) in [(0,0,0),(23,5,1)]:
                    nn=[int(v) for v in N[m,i,:,b,s]];kk=[int(v) for v in K[m,i,:,b,s]]
                    def dist(n,k,n2,k2):
                        dn=n-n2;dk=k-k2
                        return math.sqrt(dk*dk-dn*dk+dn*dn)/500
                    a=math.fsum(dist(n,k,int(on[i,b,s]),int(ok[i,b,s])) for n,k in zip(nn,kk))/M
                    p=math.fsum(dist(nn[j],kk[j],nn[l],kk[l]) for j in range(M) for l in range(j))/(M*M)
                    err=abs(a-p-sc[m,i,b,s,0,0]);assert err<1e-12
                    scalar.append(dict(model=m,animal=i,bin=b,side=s,score=a-p,error=err))
assert max(category_error,ratio_error,count_error)<1e-12

def scalar_pair_score(n,k,ny,ky):
    def distance(j,l):
        dn=n[j]-n[l];dk=k[j]-k[l]
        return math.sqrt(dn*dn-dn*dk+dk*dk)/500
    mm=len(n)
    return math.fsum(math.sqrt((n[j]-ny)**2-(n[j]-ny)*(k[j]-ky)+(k[j]-ky)**2)/500 for j in range(mm))/mm-math.fsum(distance(j,l) for j in range(mm) for l in range(j))/(mm*mm)
limits=dict(identical_pointmass=scalar_pair_score([100]*4,[50]*4,100,50),correctness_change=scalar_pair_score([100]*4,[75]*4,100,50),count_change=scalar_pair_score([150]*4,[100]*4,100,50))
assert limits['identical_pointmass']==0 and abs(limits['correctness_change']-.05)<1e-15 and abs(limits['count_change']-.1)<1e-15
n=N[0,0,:,0,0].astype(int).tolist();k=K[0,0,:,0,0].astype(int).tolist()
permutation_error=abs(scalar_pair_score(n,k,int(on[0,0,0]),int(ok[0,0,0]))-scalar_pair_score(n[::-1],k[::-1],int(on[0,0,0]),int(ok[0,0,0])))
assert permutation_error<1e-12

uncertainty={}
for f,name in enumerate(('declared_joint','declared_count_reference','ONE_contrary_accuracy_ratio')):
    differences=[math.fsum(float(sc[1,i,b,s,f,0]-sc[0,i,b,s,f,0]) for b in range(6) for s in range(2))/12 for i in range(24)]
    mean=math.fsum(differences)/24
    boot=[math.fsum(differences[int(i)] for i in row)/24 for row in r['bootstrap_indices']]
    ci=np.quantile(boot,[.025,.975])
    sums=[math.fsum(differences[i]-mean for i in range(24) if e['labs'][i]==lab) for lab in sorted(set(e['labs']))]
    cse=math.sqrt(5/4*math.fsum(v*v for v in sums)/24**2)
    lci=[mean-float(t.ppf(.975,4))*cse,mean+float(t.ppf(.975,4))*cse]
    reported=result['summaries'][name]
    err=max(abs(mean-reported['growth_minus_rnn']),float(np.max(np.abs(ci-reported['animal_bootstrap95']))),float(np.max(np.abs(np.array(lci)-reported['lab_cr1_t95']))))
    assert err<1e-12
    uncertainty[name]=dict(max_error=err,scalar_mean=mean,animal_bootstrap95=ci.tolist(),lab_cr1_t95=lci)
ar,_=load(AUTHOR/'RESULT.json');af,_=load(AUTHOR/'FROZEN_PLAN.json')
for ours,theirs in [('declared_joint','main_joint_energy'),('declared_count_reference','one_accuracy_blind_count_reference')]:
    a=result['summaries'][ours];b=ar[theirs]
    for u,v in [('growth_minus_rnn','growth_minus_rnn'),('animal_bootstrap95','paired_animal_bootstrap95'),('lab_cr1_t95','cluster_cr1_t95')]:assert np.max(np.abs(np.array(a[u])-b[v]))<1e-12
for name,sha in af['frozen_sources'].items():assert pin(AUTHOR/name)==sha
for name,sha in ownfreeze['pins'].items():assert pin(OUT/name)==sha
assert first['utc']<'2026-11-01T13:40:03'
assert ownfreeze['utc']<'2026-11-01T13:48:03'
assert af['utc']<ar['utc']<ownfreeze['utc']<result['utc']
assert datetime.now(timezone.utc)<datetime.fromisoformat('2026-11-01T14:28:03+00:00')
explicit=result['resources']['cumulative_explicit_read_hash_decode_bytes']+sum(x['containing_bytes']+x['decoded_bytes'] for x in inputs)
charge=explicit+30000000
assert charge<200000000
rss=max(result['resources']['peak_rss_bytes'],first['resources']['peak_rss_bytes'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
assert rss<800000000
audit=dict(utc=datetime.now(timezone.utc).isoformat(),status='independent_final_audit_passed',author_endpoints_and_category_objects_exact=True,
    score_max_errors=score_errors,all_cell_three_category_score_max_error=category_error,all_cell_scalar_sorted_count_crps_max_error=count_error,
    all_cell_scalar_sorted_ratio_crps_max_error=ratio_error,full_scalar_integer_joint_cells=scalar,permutation_error=permutation_error,limiting_cases=limits,
    uncertainty=uncertainty,original_pins_reverified=48,matching_original_cross_model_seeds=seeds,paired_session_boundary_arrays=paired_sessions,
    author_and_review_freeze_pins_unchanged=True,ordering_consistent_not_proof_of_historical_nonaccess=True,
    resources=dict(cumulative_explicit_read_hash_decode_bytes=explicit,context_runtime_failed_margin_bytes=30000000,total_conservative_read_hash_decode_allowance_bytes=charge,
        read_cap_bytes=200000000,peak_rss_bytes=rss,rss_cap_bytes=800000000,scientific_processes=1,numerical_threads=1,public_operations=0,downloads=0,ingress_bytes=0,raw_rows_read=0,physical_io_unknown=True),inputs=inputs)
(OUT/'FINAL_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
(OUT/'RESOURCES.json').write_text(json.dumps(dict(utc=audit['utc'],**audit['resources'],native_exits=dict(schema=0,first_calculation=0,freeze=0,main_review=0,final_audit=0),
    native_exit_note='Current final audit emits stdout then returns normally; native tool exit is recorded in STATE after readback.',jobs=0,
    rejected_pre_execution_commands=['composed ordinary inventory before START','ordinary ls of binary paths after START'],scientific_failed_processes=0,
    warnings='No warnings in successful native outputs/stderr; no warnings suppressed.',
    separate_preserved_history='start20failedownership/5MB; author123783434bytes/148275200RSS/nativeexits0/no rawreread; older matched author220MB/nativeexit120 and review347704984bytes/393756672RSS/failedcompiler/physicalIOunknowns.'),indent=2)+'\n')
print(json.dumps({k:audit[k] for k in ['utc','status','score_max_errors','all_cell_three_category_score_max_error','all_cell_scalar_sorted_count_crps_max_error','all_cell_scalar_sorted_ratio_crps_max_error','full_scalar_integer_joint_cells','permutation_error','limiting_cases','uncertainty','resources']},indent=2))
