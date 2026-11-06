"""Fixed saved-ensemble joint energy score; no model or campaign imports."""
from pathlib import Path
import datetime as dt
import hashlib
import io
import json
import resource
import time
import warnings
import zipfile
import numpy as np
from scipy.stats import t as student

O = Path(__file__).resolve().parent
METHODS = ('rnn','growth')
DEADLINE = dt.datetime(2026,11,1,13,56,15,tzinfo=dt.timezone.utc)


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def score_ensemble(q, y, counts, observed_counts):
    """Return equal-bin/side energy, exact U jackknife and count reference."""
    m = len(q)
    cell_v = np.empty((6,2)); cell_u = np.empty((6,2))
    count_v = np.empty((6,2)); count_u = np.empty((6,2))
    av = np.zeros(m); bv = np.zeros((m,m))
    ac = np.zeros(m); bc = np.zeros((m,m))
    for b in range(6):
        for s in range(2):
            assert dt.datetime.now(dt.timezone.utc) < DEADLINE
            z = q[:,b,s]
            a = np.sqrt(np.sum((z-y[b,s])**2,axis=1)/2)
            differences = z[:,None,:]-z[None,:,:]
            d = np.sqrt(np.sum(differences*differences,axis=2)/2)
            cn = counts[:,b,s]/500.
            ca = np.abs(cn-observed_counts[b,s]/500.)
            cd = np.abs(cn[:,None]-cn[None,:])
            cell_v[b,s] = a.mean()-d.sum()/(2*m*m)
            cell_u[b,s] = a.mean()-d.sum()/(2*m*(m-1))
            count_v[b,s] = ca.mean()-cd.sum()/(2*m*m)
            count_u[b,s] = ca.mean()-cd.sum()/(2*m*(m-1))
            av += a/12.; bv += d/12.
            ac += ca/12.; bc += cd/12.
    def numerical(a,d):
        pair = d.sum()
        u = a.mean()-pair/(2*m*(m-1))
        pseudo = a-d.sum(1)/(m-2)+pair/(2*(m-1)*(m-2))
        assert abs(pseudo.mean()-u)<1e-12
        blocks = []
        for j in range(8):
            sl = slice(j*64,(j+1)*64)
            blocks.append(float(a[sl].mean()-d[sl,sl].sum()/(2*64*63)))
        return dict(first_term=float(a.mean()),
                    diversity_term_v=float(pair/(2*m*m)),
                    diversity_term_u=float(pair/(2*m*(m-1))),
                    pseudo=pseudo,block_u=np.array(blocks))
    return cell_v,cell_u,count_v,count_u,numerical(av,bv),numerical(ac,bc)


def interval_summary(loss, labs, ix):
    delta = loss[1]-loss[0]
    n = len(delta); mu = float(delta.mean())
    se = float(delta.std(ddof=1)/np.sqrt(n))
    gnames = sorted(set(labs.tolist())); g = len(gnames)
    cluster_sums = np.array([(delta[labs==label]-mu).sum() for label in gnames])
    cse = float(np.sqrt(g/(g-1)*np.sum(cluster_sums**2))/n)
    pct = np.quantile(delta[ix].mean(1),[.025,.975]).tolist()
    return dict(rnn=float(loss[0].mean()),growth=float(loss[1].mean()),
        growth_minus_rnn=mu,relative_gain_percent=100*mu/float(loss[1].mean()),
        animals_improved=int((delta>0).sum()),animal_count=n,animal_se=se,
        animal_student95=[mu-float(student.ppf(.975,n-1))*se,mu+float(student.ppf(.975,n-1))*se],
        paired_animal_bootstrap95=pct,bootstrap_replicates=len(ix),bootstrap_seed=2026110101,
        cluster_count=g,cluster_se=cse,
        cluster_cr1_t95=[mu-float(student.ppf(.975,g-1))*cse,mu+float(student.ppf(.975,g-1))*cse],
        lab_counts={label:int((labs==label).sum()) for label in gnames},
        lab_growth_minus_rnn={label:float(delta[labs==label].mean()) for label in gnames},
        leave_one_lab_out={label:float(delta[labs!=label].mean()) for label in gnames},
        per_animal_growth_minus_rnn=delta.tolist())


def accuracy_summary(p, observed):
    d = observed-p
    return dict(population_curve_mae_pp=float(100*np.abs(d.mean((0,2))).mean()),
        individual_equal_side_mae_pp=float(100*np.abs(d.mean(2)).mean()),
        individual_side_mae_pp=float(100*np.abs(d).mean()),
        forecast_population_curve_pp=(100*p.mean((0,2))).tolist(),
        observed_population_curve_pp=(100*observed.mean((0,2))).tolist(),
        signed_observed_minus_forecast_curve_pp=(100*d.mean((0,2))).tolist())


def main():
    tic = time.monotonic()
    frozen = json.loads((O/'FROZEN_PLAN.json').read_text())
    base = frozen['resources']['cumulative_read_hash_decode_charge_bytes']
    b = (O/'COMPARISON_OBJECTS.npz').read_bytes()
    pin = hashlib.sha256(b).hexdigest()
    assert pin == frozen['comparison_objects_sha256']
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        decoded = sum(v.file_size for v in z.infolist())
    charge = base+len(b)+decoded+5_000_000
    assert charge < 200_000_000
    for name,expected in frozen['frozen_sources'].items():
        assert hashlib.sha256((O/name).read_bytes()).hexdigest() == expected,name
    with np.load(io.BytesIO(b),allow_pickle=False) as z:
        x = {k:z[k] for k in z.files}
    q,y,n,k = x['generated_categories'],x['observed_categories'],x['opportunities'],x['successes']
    on,ok,labs = x['observed_opportunities'],x['observed_successes'],x['labs']
    assert q.shape == (2,24,512,6,2,3) and y.shape == (24,6,2,3)
    assert np.isfinite(q).all() and np.max(np.abs(q.sum(-1)-1))<1e-14
    assert np.max(np.abs(q[:,:,:,:,:,0]*500-k))<1e-10
    assert np.max(np.abs(q[:,:,:,:,:,1]*500-(n-k)))<1e-10
    shape = (2,24,6,2)
    v=np.empty(shape);u=np.empty(shape);cv=np.empty(shape);cu=np.empty(shape)
    pseudo=np.empty((2,24,512)); cpseudo=np.empty_like(pseudo)
    blocks=np.empty((2,24,8)); cblocks=np.empty_like(blocks)
    terms={}; count_terms={}; caught=[]
    with warnings.catch_warnings(record=True) as warn:
        warnings.simplefilter('always')
        for m,method in enumerate(METHODS):
            terms[method]=[];count_terms[method]=[]
            for i in range(24):
                a,bv,c,d,detail,cdetail = score_ensemble(q[m,i],y[i],n[m,i],on[i])
                v[m,i]=a;u[m,i]=bv;cv[m,i]=c;cu[m,i]=d
                pseudo[m,i]=detail.pop('pseudo');blocks[m,i]=detail.pop('block_u')
                cpseudo[m,i]=cdetail.pop('pseudo');cblocks[m,i]=cdetail.pop('block_u')
                terms[method].append(detail);count_terms[method].append(cdetail)
            print(json.dumps(dict(utc=stamp(),method=method,completed_animals=24)),flush=True)
        caught=[dict(category=w.category.__name__,message=str(w.message),filename=w.filename,lineno=w.lineno) for w in warn]
    ix = np.random.default_rng(2026110101).integers(0,24,(20000,24))
    loss = v.mean((2,3)); uloss = u.mean((2,3))
    closs = cv.mean((2,3)); culoss = cu.mean((2,3))
    joint = interval_summary(loss,labs,ix)
    count = interval_summary(closs,labs,ix)
    def mc_summary(p,b,primary,unbiased):
        delta_pseudo=p[1]-p[0]
        se=float(np.sqrt(np.var(delta_pseudo,axis=1,ddof=1).sum()/512)/24)
        bdelta=(b[1]-b[0]).mean(0)
        return dict(paired_delete_one_u_score_mc_se=se,
            approximate_mc95_around_u_gain=[float((unbiased[1]-unbiased[0]).mean()-1.96*se),float((unbiased[1]-unbiased[0]).mean()+1.96*se)],
            u_score_rnn=float(unbiased[0].mean()),u_score_growth=float(unbiased[1].mean()),
            u_growth_minus_rnn=float((unbiased[1]-unbiased[0]).mean()),
            v_minus_u_growth_minus_rnn=float(((primary[1]-primary[0])-(unbiased[1]-unbiased[0])).mean()),
            eight_disjoint64_u_gains=bdelta.tolist(),
            disjoint64_gain_mean=float(bdelta.mean()),disjoint64_gain_se=float(bdelta.std(ddof=1)/np.sqrt(8)),
            scope='Approximate numerical integration variation conditional on fixed prefix/recipe, not biological uncertainty or calibrated coverage')
    original={};pooled={};counts={};covariances={}
    for m,method in enumerate(METHODS):
        accuracy=k[m]/n[m]
        original[method]=accuracy_summary(accuracy.mean(1),ok/on)
        pooled[method]=accuracy_summary(k[m].sum(1)/n[m].sum(1),ok/on)
        cov=np.mean((n[m]-n[m].mean(1)[:,None])*(accuracy-accuracy.mean(1)[:,None]),axis=1)
        identity=k[m].sum(1)/n[m].sum(1)-accuracy.mean(1)-cov/n[m].mean(1)
        covariances[method]=dict(negative_cells=int((cov<0).sum()),total_cells=int(cov.size),
            covariance_min=float(cov.min()),covariance_max=float(cov.max()),
            ratio_pooling_identity_max_error=float(np.abs(identity).max()))
        counts[method]=dict(mean_forecast_opportunities=float(n[m].mean()),mean_observed_opportunities=float(on.mean()),
            opportunity_mean_absolute_error_counts=float(np.abs(n[m].mean(1)-on).mean()),
            success_mean_absolute_error_counts=float(np.abs(k[m].mean(1)-ok).mean()),
            observed_min=int(on.min()),observed_max=int(on.max()),generated_min=int(n[m].min()),generated_max=int(n[m].max()),
            observed_cohort_side_counts_by_bin=on.mean(0).tolist(),forecast_cohort_side_counts_by_bin=n[m].mean((0,1)).tolist())
    np.savez_compressed(O/'SCORES.npz',subjects=x['subjects'],labs=labs,
        joint_v=v,joint_u=u,count_v=cv,count_u=cu,joint_u_pseudovalues=pseudo,
        count_u_pseudovalues=cpseudo,joint_block_u=blocks,count_block_u=cblocks)
    result=dict(utc=stamp(),status='completed_frozen_saved_forecast_comparison',
        comparison_objects_sha256=pin,units='Normalized opportunity-proportion energy/CRPS; accuracy MAE separately in percentage points',
        main_joint_energy=joint,one_accuracy_blind_count_reference=count,
        main_numerical_variation=mc_summary(pseudo,blocks,loss,uloss),
        reference_numerical_variation=mc_summary(cpseudo,cblocks,closs,culoss),
        original_expected_ratio_accuracy=original,changed_count_pooled_accuracy=pooled,
        count_descriptives=counts,covariance_audits=covariances,
        joint_score_terms_by_animal=terms,count_score_terms_by_animal=count_terms,
        warnings=caught,source_parameter_uncertainty='UNRUN',coverage='UNRUN',
        full_cross_bin_side_joint_trajectory_scoring='UNRUN; main score evaluates cell joint laws',
        original_gate_changed=False,postvalidation_consumed_observations=True)
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert rss<800_000_000
    resources=dict(utc=stamp(),cumulative_read_hash_decode_charge_bytes=charge,
        previous_freeze_charge_bytes=base,comparison_containing_file_bytes=len(b),comparison_decoded_bytes=decoded,
        main_context_code_runtime_margin_bytes=5_000_000,peak_process_rss_bytes=rss,
        peak_rss_bytes=max(rss,frozen['resources']['peak_process_rss_bytes']),
        scientific_processes=1,numerical_threads=1,public_operations=0,downloads=0,ingress_bytes=0,
        new_raw_rows=0,physical_io_unknown=True,failed_start_allowance_preserved_bytes=5_000_000,
        elapsed_seconds=time.monotonic()-tic)
    (O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    (O/'WARNINGS.json').write_text(json.dumps(caught,indent=2)+'\n')
    (O/'RESOURCES.json').write_text(json.dumps(resources,indent=2)+'\n')
    stdout=json.dumps({key:result[key] for key in ('utc','status','main_joint_energy','one_accuracy_blind_count_reference','main_numerical_variation','changed_count_pooled_accuracy','warnings')},indent=2)
    (O/'MAIN.stdout').write_text(stdout+'\n')
    print(stdout,flush=True)
    print(json.dumps(resources),flush=True)


if __name__=='__main__':
    main()
