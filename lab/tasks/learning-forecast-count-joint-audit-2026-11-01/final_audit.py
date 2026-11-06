"""Independent counts -> categories -> SciPy/scalar score reconstruction."""
from pathlib import Path
import datetime as dt
import hashlib
import io
import json
import math
import resource
import time
import zipfile
import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import t as student

O=Path(__file__).resolve().parent


def main():
    tic=time.monotonic()
    previous=json.loads((O/'RESOURCES.json').read_text())
    charge=previous['cumulative_read_hash_decode_charge_bytes']
    ledger=[]
    def read(path,npz=False):
        nonlocal charge
        b=path.read_bytes()
        decoded=0
        if npz:
            with zipfile.ZipFile(io.BytesIO(b)) as z:decoded=sum(v.file_size for v in z.infolist())
        charge+=len(b)+decoded
        assert charge+10_000_000<200_000_000
        ledger.append(dict(path=path.name,containing_bytes=len(b),decoded_bytes=decoded,sha256=hashlib.sha256(b).hexdigest()))
        if npz:
            with np.load(io.BytesIO(b),allow_pickle=False) as z:return {k:z[k] for k in z.files}
        return b
    endpoints=read(O/'ENDPOINTS.npz',True)
    comp=read(O/'COMPARISON_OBJECTS.npz',True)
    scores=read(O/'SCORES.npz',True)
    result=json.loads(read(O/'RESULT.json'))
    frozen=json.loads(read(O/'FROZEN_PLAN.json'))
    first=json.loads(read(O/'FIRST_CALCULATION.json'))
    assert ledger[0]['sha256']==frozen['endpoint_input_sha256']
    assert ledger[1]['sha256']==frozen['comparison_objects_sha256']==result['comparison_objects_sha256']
    assert np.array_equal(endpoints['subjects'],comp['subjects'])
    assert np.array_equal(endpoints['subjects'],scores['subjects'])
    assert np.array_equal(endpoints['labs'],comp['labs'])
    pins={}
    for path,expected in frozen['frozen_sources'].items():
        b=read(O/path)
        pins[path]=hashlib.sha256(b).hexdigest()
        assert pins[path]==expected,path
    assert dt.datetime.fromisoformat(first['utc'])<dt.datetime(2026,11,1,13,8,15,tzinfo=dt.timezone.utc)
    assert dt.datetime.fromisoformat(frozen['utc'])<dt.datetime(2026,11,1,13,16,15,tzinfo=dt.timezone.utc)
    assert dt.datetime.fromisoformat(first['utc'])<dt.datetime.fromisoformat(frozen['utc'])<dt.datetime.fromisoformat(result['utc'])
    assert frozen['new_joint_and_growth_pooled_scores_computed'] is False
    def cats(n,k):
        return np.column_stack((k,n-k,500-n)).astype(float)/500.
    def energy(q,y):
        m=len(q)
        # pdist independently computes each unordered distance once in C.
        first=math.fsum(math.dist(row,y)/math.sqrt(2) for row in q)/m
        pairs=math.fsum(float(v)/math.sqrt(2) for v in pdist(q,metric='euclidean'))
        return first-pairs/(m*m),first-pairs/(m*(m-1))
    def count_crps(n,y):
        # Sorted closed form, independently avoiding a pair-distance matrix.
        values=sorted(int(v) for v in n);m=len(values)
        absolute=math.fsum(abs(v-int(y)) for v in values)/(500*m)
        ordered=math.fsum((2*(j+1)-m-1)*v for j,v in enumerate(values))/500
        return absolute-ordered/(m*m),absolute-ordered/(m*(m-1))
    shape=(2,24,6,2)
    rv=np.empty(shape);ru=np.empty(shape);rcv=np.empty(shape);rcu=np.empty(shape)
    scalar_checks=[];pseudo_checks=[];permutation_checks=[]
    round_error=0.;category_error=0.;original_ratio_error=0.
    on=endpoints['observed_opportunities'];ok=endpoints['observed_successes']
    assert np.array_equal(on,comp['observed_opportunities']) and np.array_equal(ok,comp['observed_successes'])
    assert np.array_equal(ok,np.rint(on*endpoints['observed_accuracy']).astype(int))
    for m,method in enumerate(('rnn','growth')):
        n=endpoints[method+'_opportunities'];k=endpoints[method+'_successes']
        assert np.array_equal(n,comp['opportunities'][m]) and np.array_equal(k,comp['successes'][m])
        assert np.all(n.sum(-1)<=500) and np.all((k>=0)&(k<=n)) and np.all(n>0)
        original_ratio_error=max(original_ratio_error,float(np.max(np.abs(k/n-endpoints[method+'_accuracy']))))
        for i in range(24):
            for b in range(6):
                for s in range(2):
                    q=cats(n[i,:,b,s],k[i,:,b,s])
                    y=cats(np.array([on[i,b,s]]),np.array([ok[i,b,s]]))[0]
                    category_error=max(category_error,float(np.max(np.abs(q-comp['generated_categories'][m,i,:,b,s]))),float(np.max(np.abs(y-comp['observed_categories'][i,b,s]))))
                    rv[m,i,b,s],ru[m,i,b,s]=energy(q,y)
                    rcv[m,i,b,s],rcu[m,i,b,s]=count_crps(n[i,:,b,s],on[i,b,s])
            if i in (0,23):
                for j in (0,127,511):
                    keep=np.arange(512)!=j
                    deleted=[]
                    for b in range(6):
                        for s in range(2):
                            qq=cats(n[i,keep,b,s],k[i,keep,b,s])
                            yy=cats(np.array([on[i,b,s]]),np.array([ok[i,b,s]]))[0]
                            deleted.append(energy(qq,yy)[1])
                    exact_pseudo=512*float(ru[m,i].mean())-511*math.fsum(deleted)/12
                    error=abs(exact_pseudo-float(scores['joint_u_pseudovalues'][m,i,j]))
                    assert error<1e-11
                    pseudo_checks.append(dict(method=method,animal=i,particle=j,error=error))
        for i,b,s in ((0,0,0),(23,5,1)):
            nn=n[i,:,b,s];kk=k[i,:,b,s]
            target=(int(ok[i,b,s]),int(on[i,b,s]-ok[i,b,s]),int(500-on[i,b,s]))
            rows=[(int(kk[j]),int(nn[j]-kk[j]),int(500-nn[j])) for j in range(512)]
            # All scalar integers/distances; no category vectors or pdist.
            at=math.fsum(math.sqrt(sum((row[t]-target[t])**2 for t in range(3)))/(500*math.sqrt(2)) for row in rows)/512
            bt=math.fsum(math.sqrt(sum((rows[j][t]-rows[l][t])**2 for t in range(3)))/(500*math.sqrt(2)) for j in range(512) for l in range(j))
            scalar=at-bt/(512*512)
            err=abs(scalar-float(scores['joint_v'][m,i,b,s]));assert err<1e-12
            scalar_checks.append(dict(method=method,animal=i,bin=b,side=s,energy=scalar,vector_error=err))
            q=cats(nn,kk);y=cats(np.array([on[i,b,s]]),np.array([ok[i,b,s]]))[0]
            rev=energy(q[::-1],y)[0]
            assert abs(rev-rv[m,i,b,s])<1e-12
            permutation_checks.append(abs(rev-rv[m,i,b,s]))
    discrepancy={name:float(np.max(np.abs(a-scores[name]))) for name,a in
        (('joint_v',rv),('joint_u',ru),('count_v',rcv),('count_u',rcu))}
    assert max(discrepancy.values())<1e-12
    # Analytic point-mass checks distinguish a correctness change from counts.
    base=cats(np.array([250]*4),np.array([125]*4))
    y=base[0]
    changed_accuracy=cats(np.array([250]*4),np.array([150]*4))
    changed_counts=cats(np.array([300]*4),np.array([125]*4))
    limits=dict(identical_point_mass=energy(base,y)[0],
        correctness_only_joint=energy(changed_accuracy,y)[0],
        correctness_only_count=count_crps([250]*4,250)[0],
        count_only_joint=energy(changed_counts,y)[0],
        count_only_reference=count_crps([300]*4,250)[0])
    assert abs(limits['identical_point_mass'])<1e-14
    assert abs(limits['correctness_only_joint']-.05)<1e-14 and limits['correctness_only_count']==0
    assert abs(limits['count_only_joint']-.1)<1e-14 and abs(limits['count_only_reference']-.1)<1e-14
    labs=comp['labs'];ix=np.random.default_rng(2026110101).integers(0,24,(20000,24))
    def percentile(values,prob):
        a=sorted(float(v) for v in values);p=(len(a)-1)*prob;j=int(math.floor(p));f=p-j
        return a[j]*(1-f)+a[min(j+1,len(a)-1)]*f
    uncertainty={}
    for key,a in (('main_joint_energy',rv),('one_accuracy_blind_count_reference',rcv)):
        loss=[[math.fsum(float(v) for v in a[m,i].flat)/12 for i in range(24)] for m in range(2)]
        delta=[loss[1][i]-loss[0][i] for i in range(24)]
        mu=math.fsum(delta)/24
        bootstrap=[math.fsum(delta[int(i)] for i in row)/24 for row in ix]
        pct=[percentile(bootstrap,.025),percentile(bootstrap,.975)]
        labels=sorted(set(labs.tolist()))
        sums=[math.fsum(delta[i]-mu for i in range(24) if labs[i]==label) for label in labels]
        cse=math.sqrt(5/4*math.fsum(v*v for v in sums))/24
        cluster=[mu-float(student.ppf(.975,4))*cse,mu+float(student.ppf(.975,4))*cse]
        expected=result[key]
        errors=[abs(mu-expected['growth_minus_rnn'])]+[abs(pct[j]-expected['paired_animal_bootstrap95'][j]) for j in range(2)]+[abs(cluster[j]-expected['cluster_cr1_t95'][j]) for j in range(2)]
        assert max(errors)<1e-12
        uncertainty[key]=dict(growth_minus_rnn=mu,paired_bootstrap95=pct,cluster_cr1_t95=cluster,max_error=max(errors))
    assert not result['warnings']
    charge+=10_000_000 # audit source/import/runtime, record reads and closeout margin
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert charge<200_000_000 and rss<800_000_000
    out=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),status='independent_endpoint_score_uncertainty_and_pin_audit_passed',
        all_576_cell_energy_and_count_scores_max_errors=discrepancy,
        category_construction_max_error=category_error,original_ratio_max_error=original_ratio_error,
        scalar_integer_count_checks=scalar_checks,exact_delete_one_checks=pseudo_checks,
        permutation_max_error=max(permutation_checks),point_mass_limits=limits,
        uncertainty_reconstruction=uncertainty,frozen_sources_unchanged=pins,
        first_numeric_and_design_deadlines_passed=True,source_ordering_consistent_not_proof_of_historical_nonaccess=True,
        input_manifest=ledger,cumulative_read_hash_decode_charge_bytes=charge,
        audit_peak_rss_bytes=rss,physical_io_unknown=True,elapsed_seconds=time.monotonic()-tic)
    (O/'FINAL_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
    previous.update(utc=out['utc'],main_before_final_audit_charge_bytes=previous['cumulative_read_hash_decode_charge_bytes'],
        cumulative_read_hash_decode_charge_bytes=charge,final_audit_peak_rss_bytes=rss,
        final_audit_read_manifest=ledger,final_audit_code_runtime_closeout_allowance_bytes=10_000_000,
        peak_rss_bytes=max(previous['peak_rss_bytes'],rss),native_main_exit=0,native_first_calculation_exit=0,
        native_freeze_exit=0,failed_scientific_passes_in_this_continuation=0,
        historical_failed_start20='Preserved; zero numeric payload, exact physical I/O and peak unknown; 5MB conservative allowance remains included')
    (O/'RESOURCES.json').write_text(json.dumps(previous,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('utc','status','all_576_cell_energy_and_count_scores_max_errors','point_mass_limits','uncertainty_reconstruction','cumulative_read_hash_decode_charge_bytes','audit_peak_rss_bytes','elapsed_seconds')},indent=2),flush=True)


if __name__=='__main__':main()
