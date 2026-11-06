"""PI-directed composite-null challenge: only one endpoint on its material boundary."""
import time
import numpy as np
from independent import Accounting, save, bootstrap_weights
from controls import point_risk_contrasts, summary


def main():
    meter=Accounting('early PI-directed one-active-boundary composite-null controls')
    weights=bootstrap_weights()
    cases=[];R=2000
    # A single common animal-level innovation makes all four standardized
    # deviations perfectly dependent. This avoids manufacturing protection
    # through independent boundary cutoffs or irrelevant nuisance columns.
    for target in ['A200','D200','A1000','D1000']:
        rng=np.random.default_rng(20261105121+['A200','D200','A1000','D1000'].index(target))
        sign=rng.choice([-1,1],size=(R,64))
        ordinary=np.empty((R,64,2));neural=np.empty_like(ordinary)
        active_cutoff=0 if target.endswith('200') and target!='A1000' and target!='D1000' else 1
        other=1-active_cutoff
        if target.startswith('A'):
            eps=.008*sign
            ordinary[...,active_cutoff]=.300+eps
            neural[...,active_cutoff]=.280+eps/2
            # Active A has true .02; its score D=-.01 remains clearly immaterial.
            ordinary[...,other]=.100+eps/4
            neural[...,other]=.100+eps/8
            truth=np.array([0,-.01,0,-.01]);truth[2*active_cutoff]=.02
        else:
            eps=.004*sign
            ordinary[...,active_cutoff]=.060+eps
            neural[...,active_cutoff]=.054+eps/2
            # Active D has true0 (10% benefit); its A=.006 is clearly below2pp.
            ordinary[...,other]=.100+eps/2
            neural[...,other]=.100+eps/4
            truth=np.array([0,-.01,0,-.01]);truth[2*active_cutoff]=.006;truth[2*active_cutoff+1]=0
        x=point_risk_contrasts(ordinary,neural)
        assert np.all(np.var(x,axis=1)>1e-16)
        c=summary('one_active_'+target,x,truth,weights)
        c['active_boundary']=target
        c['exact_truth']=truth
        c['other_endpoint_true_absence_headroom']=np.array([.02,0,.02,0])-truth
        c['within_animal_correlation']=np.corrcoef(x[0],rowvar=False)
        cases.append(c)
    save('ONE_ACTIVE_BOUNDARY.json',dict(
        purpose='Composite full-absence null: exactly one quantity at its material boundary and the other three permissive for absence',
        cases=cases,cohorts_per_case=R,bootstrap_replicates=20000,
        law='Observed K600/N1000 at both origins; finite integer point forecasts; a shared Rademacher animal innovation correlates all four contrasts. No biological learning or empirical outcome data.',
        interpretation='Conditional known-law decision check. Zero/all-four-at-boundary error in other controls does not calibrate this composite null. Rates are not empirical-study failure probabilities.'))
    save('ONE_ACTIVE_BOUNDARY_RESOURCES.json',meter.receipt())
    print([(c['active_boundary'],c['false_all_four_absence'],c['any_false_endpoint_positive'],c['nominal_any_band_noncoverage']) for c in cases])
    print(meter.receipt())


if __name__=='__main__':
    start=time.process_time()
    try: main()
    except BaseException as exc:
        save('ONE_ACTIVE_BOUNDARY_FAILURE_'+str(time.time_ns())+'.json',dict(error=repr(exc),process_cpu_seconds=time.process_time()-start))
        raise
