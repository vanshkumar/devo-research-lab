"""Saved-artifact/pin/scalar-score audit; no new experimental conditions."""
from reference import *
import ast
import math
import platform
import scipy

start = time.monotonic()
frozen = json.loads((OUT/'FREEZE.json').read_text())
for name,h in frozen['sha256'].items():
    assert sha(OUT/name)==h,(name,'frozen bytes changed')
assert sha(REVIEW/'independent_model.py')==frozen['reused_helper_sha256']
report = json.loads((OUT/'STABILITY_RESULT.json').read_text())
assert report['status']=='FROZEN_STABILITY_EXPERIMENT_COMPLETE'
assert report['all_predeclared_claim_gates_pass'] is True
author = ROOT/'lab/tasks/interactome-transient-reachability-2026-11-03'
names = ast.literal_eval(json.loads((author/'sources/names-response.json').read_text())['result']['structuredContent']['content'])
motor = [i for i,n in enumerate(names) if n.startswith(('DB','VB','DD','VD'))]
assert len(motor)==37
pins = {}
def load(name):
    data = (OUT/name).read_bytes()
    pins[name] = {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    z = np.load(io.BytesIO(data),allow_pickle=False)
    result = {k:z[k] for k in z.files}
    z.close()
    for value in result.values():
        assert np.isfinite(value).all(),name
    return result

initial = load('INPUT_STATES.npz')
scores = {}
plot = {}
for seed in (0,1):
    late = {}; challenge = {}
    for branch in ('finite','sham'):
        key = f'seed{seed}_{branch}'
        z = load(key+'_continuation.npz')
        assert z['y'].shape==(12901,558)
        assert z['t'][0]==42. and z['t'][-1]==300.
        assert np.array_equal(z['y'][0],initial[key])
        assert np.max(abs(np.diff(z['t'])-.02))<1e-12
        late[branch] = z['y'][z['t']>=290.-1e-10][:,motor].copy()
        if seed==0:
            plot['t'] = z['t'][z['t']>=290.-1e-10].copy()
            plot[branch] = late[branch].copy()
        endpoint = z['y'][-1].copy()
        del z
        z = load(key+'_challenge.npz')
        assert z['t'][0]==300. and z['t'][-1]==302.
        assert np.array_equal(z['y'][0],endpoint)
        challenge[branch] = z['y'][z['t']>=300.3-1e-10][:,motor].copy()
        del z
    def scalar_rms(a,b):
        av,bv = a.ravel(),b.ravel()
        return math.sqrt(math.fsum((float(x)-float(y))**2 for x,y in zip(av,bv))/len(av))
    lr = scalar_rms(late['finite'],late['sham'])
    cr = scalar_rms(challenge['finite'],challenge['sham'])
    assert abs(lr-report['contrasts'][str(seed)]['late_290_300_motor_rms'])<1e-12
    assert abs(cr-report['contrasts'][str(seed)]['challenge_300_3_302_motor_rms'])<1e-12
    scores[str(seed)] = {'scalar_late_motor_rms':lr,'scalar_challenge_motor_rms':cr,
                        'late_scalar_count':int(late['finite'].size),
                        'challenge_scalar_count':int(challenge['finite'].size)}

z = load('MONODROMY_2048.npz')
p,values,vectors = z['matrix'],z['eigenvalues'],z['eigenvectors']
phase = int(z['phase_index']); dominant = int(z['dominant_index'])
others = [i for i in range(558) if i!=phase]
assert len(others)==557
largest = float(max(abs(values[others])))
assert abs(largest-report['cycle']['monodromy_refinements'][-1]['dominant_nontrivial_modulus'])<1e-14
vector = vectors[:,dominant]
eigen_residual = float(np.linalg.norm(np.einsum('ij,j->i',p,vector,optimize=False)-values[dominant]*vector)/np.linalg.norm(vector))
assert eigen_residual<1e-10
periodic = load('PERIODIC_ORBIT.npz')
assert periodic['y'].shape==(4097,558)
period = float(periodic['period'])
cycle_closure = closure = periodic['y'][-1]-periodic['y'][0]
assert np.max(abs(cycle_closure[:N]))<1e-6 and np.max(abs(cycle_closure[N:]))<1e-8
for name in ('MONODROMY_512.npz','MONODROMY_1024.npz',
             'seed0_finite_equilibrium.npz','seed1_finite_equilibrium.npz',
             'TANGENT_fixed_sine.npz','TANGENT_dominant_nontrivial_real.npz',
             'NONLINEAR_TANGENT_-1.npz','NONLINEAR_TANGENT_+1.npz',
             'shooting_0.npz','SOURCE_REFERENCE.npz'):
    data = (OUT/name).read_bytes()
    pins[name] = {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

license_path = ROOT/'lab/tasks/connectome-persistence-contrast-2026-11-03/sources/interactome-LICENSE'
license_bytes = license_path.read_bytes()
(OUT/'SOURCE_LICENSE.txt').write_bytes(license_bytes)
assert (OUT/'SOURCE_LICENSE.txt').read_bytes()==license_bytes
license_pin = {'original_path':str(license_path),'copy':'SOURCE_LICENSE.txt',
               'bytes':len(license_bytes),'sha256':hashlib.sha256(license_bytes).hexdigest()}
versions = {'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__}
figure_status = 'not attempted'
try:
    os.environ['MPLCONFIGDIR'] = str(OUT/'.mplconfig')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    versions['matplotlib'] = matplotlib.__version__
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes = plt.subplots(1,2,figsize=(10.2,3.5),layout='constrained')
    delta = np.sqrt(np.mean((plot['sham']-plot['finite'])**2,axis=1))
    axes[0].plot(plot['t'],delta,color='#315d91',lw=1.7)
    axes[0].axhline(report['material_cutoff'],color='#888888',ls='--',lw=1,label='declared material scale')
    axes[0].set(xlabel='Time under common background (s)',ylabel='All 37 motor neurons: RMS difference\n(source-voltage units)',
                title='Pulse and sham remain distinct at 300 s',ylim=(0,4.5))
    axes[0].legend(frameon=False,fontsize=8,loc='lower right')
    circle = np.linspace(0,2*np.pi,361)
    axes[1].plot(np.cos(circle),np.sin(circle),color='#cccccc',lw=1)
    axes[1].scatter(values[others].real,values[others].imag,s=15,color='#315d91',label='557 transverse multipliers')
    axes[1].scatter([values[phase].real],[values[phase].imag],s=35,color='#bc6543',label='neutral phase direction')
    axes[1].set(xlabel='Multiplier: real part',ylabel='Imaginary part',title='Whole-cycle stability, all 558 directions',
                xlim=(-1.1,1.1),ylim=(-1.1,1.1),aspect='equal')
    axes[1].text(-1.02,.8,'Largest transverse modulus: 0.07612\nPhase numerical error: 5.3e−6',fontsize=8)
    axes[1].legend(frameon=False,fontsize=8,loc='lower center')
    fig.savefig(OUT/'STABILITY_FIGURE.png',dpi=180)
    fig.savefig(OUT/'STABILITY_FIGURE.svg')
    plt.close(fig)
    figure_status = 'PNG/SVG rendered from saved outputs only; no new simulation'
except ImportError as exc:
    figure_status = 'optional existing plotting dependency unavailable: '+repr(exc)

write('SOURCE_MANIFEST.json',{
    'model':'Kim-Leahy-Shlizerman2019 Neural Interactome 3.0.0-beta',
    'tree':'bdb94ca174980e46777f7b1936f539903c688719',
    'reference_pins':'REFERENCE.json: exactsource/connectivity/emask/names/presets/cachedinputs/reusedhelper',
    'predecessor_manifest':str(author/'SOURCE_MANIFEST.json'),
    'source_repo_url':'https://github.com/shlizee/C-elegans-Neural-Interactome',
    'code_license':'BSD-3-Clause, exact original notice copied byte for byte',
    'license_pin':license_pin,
    'upstream_fixedasset_license_qualification':'Assets in licensed source repository; separate underlying Varshney/White connectivity terms remain inherited/uncertified',
    'primary_programs':[{'year':2017,'doi':'10.3389/fncom.2017.00053'},
                        {'year':2019,'doi':'10.3389/fncom.2019.00008'}],
    'new_public_ops_ingress_dependencies':[0,0,0],
    'versions':versions,'read_only_inputs':'Exact public source/fixedassets and admitted NEWpredecessor modeltrajectories only',
    'unread_protected_inputs':'All biological/oldfitted/saved_dynamics/reservedworm/Pan20/Flesch/HABITS/memory/Figure4_42/optional210/category targets',
    'prior_priority_and_physical_calibration':'not exhaustively certified; no biological/firstbistability claim',
    'raw_output_pins':pins
})
audit = {'status':'SAVED_FROZEN_INPUTS_RAW_TRAJECTORIES_SCALAR_SCORES_AND_STABILITY_ARTIFACTS_VERIFIED',
         'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'frozen_hashes_unchanged':True,'cached42s_forks_and_300s_challenge_forks_bitwise_match':True,
         'all_full_state_arrays_finite':True,'raw_scalar_scores':scores,
         'monodromy_full_directions':558,'transverse_directions':557,
         'dominant_transverse_saved_eigenpair_residual':eigen_residual,
         'period_s':period,'figure':figure_status,'output_manifest':'SOURCE_MANIFEST.json',
         'process_self_elapsed_s':time.monotonic()-start,
         'rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'new_experimental_conditions_or_simulations':0,
         'independent_scientific_review_of_this_study':False}
write('FINAL_VERIFICATION.json',audit)
print(json.dumps(audit,indent=2))
