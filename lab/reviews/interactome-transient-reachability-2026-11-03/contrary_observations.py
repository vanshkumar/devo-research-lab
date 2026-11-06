"""Complete predeclared observations on the SAME saved contrary; no new ODE."""
from independent_model import *
from scipy.signal import find_peaks
import resource
import time
import datetime
start=time.monotonic();m=Model()
freeze=json.loads((OUT/'CONTRARY_FREEZE.json').read_text())
assert all(sha(OUT/n)==h for n,h in freeze['sha256'].items())
bg=m.presets['PLM'].copy()
for name in ('ASKL','ASKR'):bg[m.names.index(name)]=.24
paths={}
for label in ('finite','sham'):
    with np.load(OUT/f'contrary_seed0_{label}.npz',allow_pickle=False) as z:
        t=z['t'].copy();paths[label]=z['y'].copy()
f,s=paths['finite'],paths['sham'];late=(t>=40-1e-10)&(t<=42+1e-10);ch=t>=42.3-1e-10
vbg=m.threshold(bg);vfwd=m.threshold(m.presets['FWD'])
fil={}
for label,y in paths.items():
    threshold=np.tile(vbg,(len(t),1));threshold[ch]=vfwd
    fil[label]=500*np.tanh((y[:,:N]-threshold)/500)
renderer={'late_motor_difference_rms':rms((fil['finite']-fil['sham'])[late][:,m.motor]),
          'challenge_motor_difference_rms':rms((fil['finite']-fil['sham'])[ch][:,m.motor]),
          'temporal_filter_state_added':False}
static=[]
for label,y in paths.items():
    errs=[];jacerrs=[]
    for tm in (20.15,22.15,41.,42.15,43.):
        idx=int(np.argmin(abs(t-tm)));z=y[idx]
        if label=='sham' and tm<42:old,new,when=bg,bg,0.
        elif tm<22:old,new,when=bg,m.presets['FWD'],20.
        elif tm<42:old,new,when=m.presets['FWD'],bg,22.
        else:old,new,when=bg,m.presets['FWD'],42.
        m.source_setup(old,new,when);mask=m.input(tm,old,new,when)
        errs.append(float(np.max(abs(m.rhs(tm,z,mask)-m.source['membrane_voltageRHS'](tm,z)))))
        jacerrs.append(float(np.max(abs(m.jac(tm,z,mask)-m.source['compute_jacobian'](tm,z)))))
    static.append({'branch':label,'source_RHS_maxabs':max(errs),'source_Jacobian_maxabs':max(jacerrs)})
late_records={}
for label,y in paths.items():
    q=y[late]
    vb=m.names.index('VB01')
    ids=find_peaks(y[:,vb],prominence=.01*5.638259640019669)[0]
    ids=ids[(t[ids]>=30.)&(t[ids]<=42.)]
    late_records[label]={'full_voltage_temporal_rms':rms(q[:,:N]-q[:,:N].mean(0)),
        'full_gate_temporal_rms':rms(q[:,N:]-q[:,N:].mean(0)),
        'VB01_30_42_peak_times':t[ids].tolist(),
        'VB01_interpeak_intervals_s':np.diff(t[ids]).tolist(),
        'VB01_peak_values':y[ids,vb].tolist()}
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'new_ODE_executions':0,'same_frozen_contrary_only':True,'frozen_bytes_unchanged':True,
 'new_background_threshold_source_maxabs':float(np.max(abs(vbg-m.source['EffVth_rhs'](CURRENT,bg)))),
 'renderer':renderer,'original_source_new_trajectory_checks':static,'late_descriptions':late_records,
 'late_motor_mean_difference_rms':rms(f[late][:,m.motor].mean(0)-s[late][:,m.motor].mean(0)),
 'conditional_Newton_UNRUN':'Both branches nearsteady prerequisite fails: sham is dynamic; no root hunt or extra continuation.',
 'phase_conclusion':'The frozen single-time-shift check fails; no claim that every possible phase/long-transient mechanism is excluded.',
 'strongest_remaining_alternative':'Sham may be a long transient toward the same fixed point; current finite horizon does not certify a separate stable cycle/basin.',
 'elapsed_s':time.monotonic()-start,'rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
write('CONTRARY_OBSERVATIONS.json',report)
print(json.dumps(report,indent=2))
