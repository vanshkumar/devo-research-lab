"""Scalar verification of the ONE count-weighting contrary, and fixed code pins."""
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

O=Path(__file__).resolve().parent
R=O.parents[2]
A=R/'lab/tasks/learning-forecast-information-audit-2026-11-01'
C=R/'campaigns/population_learning_transport_2026-10-28'

def main():
    tic=time.monotonic()
    rs=json.loads((O/'RESOURCES.json').read_text())
    p=O/'RECONSTRUCTED_ENDPOINTS.npz'
    # All four particle arrays plus small targets/IDs occupy <5MB decoded.
    limit=rs['conservative_cumulative_read_hash_decode_charge_bytes']+p.stat().st_size+5_000_000+1_500_000
    assert limit<=350_000_000,limit
    b=p.read_bytes()
    with zipfile.ZipFile(io.BytesIO(b)) as z:decoded=sum(v.file_size for v in z.infolist())
    assert decoded<5_000_000
    with np.load(io.BytesIO(b),allow_pickle=False) as z:x={k:z[k] for k in z.files}
    y=x['observed'];s=x['autonomous'];n=x['autonomous_counts']
    pooled=np.empty((24,6,2));plain=np.empty_like(pooled);conditional=np.empty_like(pooled)
    covariance=[]
    for i in range(24):
        for t in range(6):
            for side in range(2):
                den=sum(int(n[i,j,t,side]) for j in range(512))
                num=sum(int(round(float(s[i,j,t,side])*int(n[i,j,t,side]))) for j in range(512))
                pooled[i,t,side]=num/den
                plain[i,t,side]=math.fsum(float(s[i,j,t,side]) for j in range(512))/512
                conditional[i,t,side]=math.fsum(float(x['conditional_sampled'][i,j,t,side]) for j in range(512))/512
                nn=den/512
                covariance.append(math.fsum((float(s[i,j,t,side])-plain[i,t,side])*(int(n[i,j,t,side])-nn) for j in range(512))/512)
    def score(v):
        cohort=[]
        for t in range(6):
            cohort.append(math.fsum(float(y[i,t,k]-v[i,t,k]) for i in range(24) for k in range(2))/48)
        indiv=math.fsum(abs(math.fsum(float(y[i,t,k]-v[i,t,k]) for k in range(2))/2) for i in range(24) for t in range(6))/144
        return dict(population_mae_pp=100*math.fsum(abs(v) for v in cohort)/6,
                    individual_equal_side_mae_pp=100*indiv,
                    individual_side_mae_pp=100*math.fsum(abs(float(v)) for v in (y-v).flat)/288,
                    signed_population_residual_pp=[100*v for v in cohort])
    scalar=dict(original=score(plain),count_pooled=score(pooled),conditional=score(conditional))
    contrary=json.loads((O/'CONTRARY.json').read_text())
    discrepancies=[abs(scalar[k]['population_mae_pp']-contrary[q]['population_mae_pp'])
                   for k,q in [('original','original_autonomous'),('count_pooled','count_pooled_autonomous'),('conditional','unchanged_conditional')]]
    assert max(discrepancies)<1e-10
    checks={};pins={}
    def verify(path,expected,label):
        h=hashlib.sha256(path.read_bytes()).hexdigest();assert h==expected,label
        pins[str(path.relative_to(R))]=h;checks[label]=True
    ownfreeze=json.loads((O/'FROZEN_PLAN.json').read_text())
    verify(O/'review.py',ownfreeze['code_sha256'],'review_executed_source_unchanged')
    verify(O/'DESIGN.md',ownfreeze['design_sha256'],'review_design_unchanged')
    verify(O/'RESOURCE_PLAN.json',ownfreeze['resource_plan_sha256'],'review_amended_resource_plan_unchanged')
    authorfreeze=json.loads((A/'FROZEN_DESIGN.json').read_text())
    verify(A/'run.py',authorfreeze['run_code_sha256'],'author_executed_source_unchanged')
    verify(A/'DESIGN.md',authorfreeze['design_sha256'],'author_frozen_design_unchanged')
    verify(A/'RESOURCE_PLAN.json',authorfreeze['resource_plan_sha256'],'author_resource_plan_unchanged')
    verify(C/'protocols/FREEZE.json',authorfreeze['strict_freeze_sha256'],'strict_freeze_matches_author_precalculation_pin')
    manifest=json.loads((A/'PREDICTION_MANIFEST.json').read_text())
    authorresult=json.loads((A/'RESULT.json').read_text())
    checks['manifest_claims_scores_not_computed_at_prediction_save']=manifest['new_cohort_scores_computed'] is False
    checks['manifest_timestamp_precedes_result']=dt.datetime.fromisoformat(manifest['utc'])<dt.datetime.fromisoformat(authorresult['utc'])
    checks['author_design_precedes_manifest']=dt.datetime.fromisoformat(authorfreeze['utc'])<dt.datetime.fromisoformat(manifest['utc'])
    assert all(checks.values())
    # The 1.5MB allowance includes small scientific JSON/source re-reads above and closeout.
    additional=len(b)+decoded+1_500_000
    total=rs['conservative_cumulative_read_hash_decode_charge_bytes']+additional
    assert total<350_000_000
    out=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),status='scalar_contrary_and_pin_audit_passed',
             reconstructed_endpoint_bundle_sha256=hashlib.sha256(b).hexdigest(),scalar_scores=scalar,
             scalar_vs_vector_max_population_error_pp=max(discrepancies),
             negative_count_accuracy_covariance_cells=sum(v<0 for v in covariance),total_covariance_cells=288,
             covariance_min=min(covariance),covariance_max=max(covariance),
             original_gap_pp=scalar['original']['population_mae_pp']-scalar['conditional']['population_mae_pp'],
             count_pooled_gap_pp=scalar['count_pooled']['population_mae_pp']-scalar['conditional']['population_mae_pp'],
             checks=checks,pins=pins,ordering_consistent_not_independent_proof_of_historical_nonaccess=True,
             additional_read_hash_decode_charge_bytes=additional,final_cumulative_charge_bytes=total,
             peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,elapsed_seconds=time.monotonic()-tic)
    (O/'FINAL_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
    rs['main_and_failed_pass_cumulative_charge_bytes']=rs['conservative_cumulative_read_hash_decode_charge_bytes']
    rs['final_scalar_and_pin_audit_additional_charge_bytes']=additional
    rs['conservative_cumulative_read_hash_decode_charge_bytes']=total
    rs['final_audit_peak_rss_bytes']=out['peak_rss_bytes']
    rs['utc']=out['utc']
    (O/'RESOURCES.json').write_text(json.dumps(rs,indent=2)+'\n')
    print(json.dumps(out,indent=2),flush=True)

if __name__=='__main__':main()
