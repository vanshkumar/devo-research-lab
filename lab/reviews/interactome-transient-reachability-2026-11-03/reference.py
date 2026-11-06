"""Run reviewer original-source/independent full-model reference only."""
from independent_model import *
import datetime
import resource
import time
start=time.monotonic()
warnings.simplefilter('always')
model=Model()
initial=1e-4*np.random.RandomState(0).normal(0,.94,2*N)
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'independent_implementation':'independent_model.py; no author helpers imported',
        'source_reference':'six exact AST-extracted pinned original functions',
        'full_neurons':N,'full_states':2*N,'motor_neurons':len(model.motor),
        'pins':model.pins,'preset_nonzeros':{k:{n:float(v[i]) for i,n in enumerate(model.names) if v[i]} for k,v in model.presets.items()},
        'constants':{'GC':GC,'CAP':CAP,'EC':EC,'RISE':RISE,'DECAY':DECAY,'BETA':BETA,'CURRENT':CURRENT,'SEQ':SEQ}}
report['threshold_source_independent_maxabs']={k:float(np.max(np.abs(model.threshold(v)-model.source['EffVth_rhs'](CURRENT,v)))) for k,v in [('ZERO',model.zero)]+list(model.presets.items())}
report['source_LU_pivot_is_identity']=bool(np.array_equal(linalg.lu(-model.a)[0],np.eye(N)))
checks={}
for k,mask in [('ZERO',model.zero),('FWD',model.presets['FWD'])]:
    t,literal=model.literal_short(initial,mask)
    tr,own=model.schedule(initial,0.,.54,model.zero,[(0.,mask)],method='Radau')
    assert np.max(np.abs(t-tr))<1e-12
    checks[k]={'literal_own_full_maxabs':float(np.max(np.abs(literal-own))),
               'literal_own_motor_maxabs':float(np.max(np.abs(literal[:,model.motor]-own[:,model.motor])))}
    # Check noninitial, nonsteady states at multiple locations, not just inputs.
    rhs_err=[];jac_err=[]
    for ix in (7,19,30,45,54):
        tm=t[ix]; z=literal[ix]
        actual=model.input(tm,model.zero,mask,0.)
        model.source_setup(model.zero,mask,0.)
        rhs_err.append(float(np.max(np.abs(model.rhs(tm,z,actual)-model.source['membrane_voltageRHS'](tm,z)))))
        jac_err.append(float(np.max(np.abs(model.jac(tm,z,actual)-model.source['compute_jacobian'](tm,z)))))
    checks[k]['rhs_noninitial_maxabs']=max(rhs_err)
    checks[k]['jac_noninitial_maxabs']=max(jac_err)
    np.savez_compressed(OUT/('reference_'+k+'.npz'),t=t,literal=literal,independent=own)
report['original_reference_checks']=checks
t,y=model.schedule(initial,0.,20.,model.zero,[(0.,model.presets['FWD'])])
vb=model.names.index('VB01'); from scipy.signal import find_peaks
ids=find_peaks(y[:,vb],prominence=.1)[0]; ids=ids[t[ids]>=10]
report['FWD_20s']={'VB01_late_peak_times':t[ids].tolist(),
    'VB01_median_period_s':float(np.median(np.diff(t[ids]))),
    'motor_temporal_rms_10_20':rms(y[t>=10][:,model.motor]-y[t>=10][:,model.motor].mean(0))}
np.savez_compressed(OUT/'reference_FWD20.npz',t=t,y=y)
report['elapsed_s']=time.monotonic()-start
report['rss_bytes_macos']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
write('REFERENCE.json',report)
print(json.dumps(report,indent=2))
