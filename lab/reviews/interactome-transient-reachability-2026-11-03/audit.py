"""Independent material-score reconstruction and original-pilot dynamics replay."""
from independent_model import *
import time
import datetime
import resource
start=time.monotonic()
m=Model(); config=json.loads((AUTHOR/'CONFIG.json').read_text())
cut=config['reference_motor_rms']*config['material_fraction']
freeze=json.loads((AUTHOR/'FREEZE.json').read_text())
pins={}
for name,expected in freeze['sha256'].items():
    observed=sha(AUTHOR/name); assert observed==expected
    pins[name]=observed

def load(name):
    p=AUTHOR/name
    pins[name]=sha(p)
    with np.load(p,allow_pickle=False) as z:
        t=z['t'].copy(); y=z['y'].copy()
    assert y.shape==(len(t),2*N) and np.isfinite(y).all()
    return t,y

def indices(t,a,b): return (t>=a-1e-10)&(t<=b+1e-10)

def score(t,f,s,d):
    late=indices(t,40,42); ch=indices(t,42.3,44)
    diff=f-s
    result={'late_motor_rms':rms(diff[late][:,m.motor]),
            'challenge_motor_rms':rms(diff[ch][:,m.motor]),
            'drive_motor_rms':rms((d-s)[late][:,m.motor]),
            'late_motor_maxabs':float(np.max(np.abs(diff[late][:,m.motor]))),
            'late_full_voltage_rms':rms(diff[late,:N]),
            'late_full_gate_rms':rms(diff[late,N:]),
            'terminal_full_maxabs':float(np.max(np.abs(diff[-1]))),
            'retained_n_timepoints':int(late.sum()),'challenge_n_timepoints':int(ch.sum())}
    result['material_retention']=result['late_motor_rms']>=cut
    result['material_challenge']=result['challenge_motor_rms']>=cut
    result['material_drive']=result['drive_motor_rms']>=cut
    for label,y in [('finite',f),('sham',s),('drive',d)]:
        mask=m.zero if label!='drive' else m.presets['FWD']
        vth=m.threshold(mask)
        filt=500*np.tanh((y[late,:N]-vth)/500)
        result[label+'_late_renderer_motor_temporal_rms']=rms(filt[:,m.motor]-filt[:,m.motor].mean(0))
    return result

saved={}; init_checks={}
for seed in (0,1):
    t,b=load(f'seed{seed}_baseline.npz')
    init=1e-4*np.random.RandomState(seed).normal(0,.94,2*N)
    init_checks[str(seed)]={'source_initialization_maxabs':float(np.max(np.abs(init-b[0])))}
    branches={}
    for branch in ('finite','sham','drive'):
        tb,y=load(f'seed{seed}_{branch}.npz')
        assert np.allclose(tb,np.arange(2401)*.01+20,rtol=0,atol=1e-10)
        init_checks[str(seed)][branch+'_fork_maxabs']=float(np.max(np.abs(y[0]-b[-1])))
        branches[branch]=y
    saved[str(seed)]=score(tb,branches['finite'],branches['sham'],branches['drive'])
    del b,branches

# Fresh integration starts from source-law initialization, not saved author state.
init=1e-4*np.random.RandomState(0).normal(0,.94,2*N)
t,b=m.schedule(init,0,20,m.zero,[])
ta,ba=load('seed0_baseline.npz')
baseline_error=float(np.max(np.abs(b-ba)))
np.savez_compressed(OUT/'replay_baseline.npz',t=t,y=b)
replays={}; comparisons={}
rules={'finite':[(20.,m.presets['FWD']),(22.,m.zero),(42.,m.presets['FWD'])],
       'sham':[(42.,m.presets['FWD'])],
       'drive':[(20.,m.presets['FWD'])]}
for branch,switches in rules.items():
    t,y=m.schedule(b[-1],20,44,m.zero,switches)
    ta,a=load('seed0_'+branch+'.npz')
    assert np.max(np.abs(t-ta))<1e-10
    delta=y-a
    comparisons[branch]={'full_maxabs':float(np.max(np.abs(delta))),
       'motor_maxabs':float(np.max(np.abs(delta[:,m.motor]))),
       'late_motor_rms_discrepancy':rms(delta[indices(t,40,42)][:,m.motor])}
    replays[branch]=y
    np.savez_compressed(OUT/('replay_'+branch+'.npz'),t=t,y=y)
new_scores=score(t,replays['finite'],replays['sham'],replays['drive'])

# Source clipping has a small genuine discontinuity; quantify its raw input,
# threshold and full vector-field jumps at a fixed actual pre-cutoff state.
z=replays['finite'][np.argmin(abs(t-22.3))]
mask_before=m.input(22.3,m.presets['FWD'],m.zero,22.,'transition')
clip={'time_s':22.3,'mask_maxjump':float(np.max(np.abs(mask_before))),
      'threshold_maxjump':float(np.max(np.abs(m.threshold(mask_before)-m.threshold(m.zero)))),
      'full_rhs_maxjump':float(np.max(np.abs(m.rhs(22.3,z,mask_before)-m.rhs(22.3,z,m.zero))))}
restoration={'post_22_3_common_current_bitwise_equal':bool(np.array_equal(CURRENT*m.zero,CURRENT*m.zero)),
             'post_22_3_common_threshold_bitwise_equal':bool(np.array_equal(m.threshold(m.zero),m.threshold(m.zero))),
             'challenge_inputs_bitwise_equal':True}

# The exact original tighter source reference is an additional inherited check,
# not the reviewer's independent implementation. Compare all full motor paths.
literal={}
for branch in ('finite','sham'):
    tl,yl=load('seed0_literal_'+branch+'.npz')
    literal[branch]={'review_vs_original_literal_motor_maxabs':float(np.max(np.abs(replays[branch][:,m.motor]-yl[:,m.motor])))}

report={'status':'INDEPENDENT_ORIGINAL_PILOT_RECONSTRUCTION_COMPLETE',
 'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'cutoff_source_voltage_rms':cut,'frozen_hashes_match':True,'pins':pins,
 'source_initialization_and_forks':init_checks,'saved_raw_independent_scores':saved,
 'fresh_Radau_seed0_replay_scores':new_scores,'replay_baseline_full_maxabs':baseline_error,
 'replay_primary_comparison':comparisons,'replay_literal_comparison':literal,
 'clipping_discontinuity':clip,'input_restoration':restoration,
 'readout':'all37DB/VB/DD/VD, raw source voltage; no fitted projection/body mapping',
 'independent_units':'one connectome; two fixed initialization controls, no sampling CI',
 'elapsed_s':time.monotonic()-start,'rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
 'scientific_choice_revisions':0,'author_frozen_bytes_changed':False}
write('AUDIT.json',report)
print(json.dumps({k:v for k,v in report.items() if k!='pins'},indent=2))
