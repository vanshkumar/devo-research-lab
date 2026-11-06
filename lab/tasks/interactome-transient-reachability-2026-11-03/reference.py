"""Full pinned 2019 release reference; no new perturbation experiment.

Kim, Leahy & Shlizerman (2019), doi:10.3389/fncom.2019.00008.
Source BSD-3-Clause: predecessor sources/interactome-LICENSE.
Extract original mathematical functions without executing server/UI code.
"""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import ast
import base64
import hashlib
import io
import json
import resource
import time
from datetime import datetime, timezone
from pathlib import Path

T0 = time.monotonic()
import numpy as np
import scipy
from scipy import integrate, linalg, sparse, signal

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'sources'
PREVIOUS = ROOT.parent / 'connectome-persistence-contrast-2026-11-03' / 'sources'
N = 279
PINS = {'Gg.npy':'07b8ab0aa4471aa19cfae5e662d291493f09819b',
        'Gs.npy':'0a6e1cc361d9fe377f48cbf48e0557fec65debe8',
        'emask.npy':'ae289f5055e5661739b977cee62935d2f3b0be06'}

def git_blob(data):
    return hashlib.sha1(('blob %d\0' % len(data)).encode() + data).hexdigest()

def decode_assets():
    report = {}
    for name, expected in PINS.items():
        data = base64.b64decode((SOURCES / (name + '.b64')).read_text())
        assert git_blob(data) == expected, name
        array = np.load(io.BytesIO(data), allow_pickle=False)
        assert np.isfinite(array).all()
        target = SOURCES / name
        if target.exists():
            assert target.read_bytes() == data
        else:
            target.write_bytes(data)
        report[name] = dict(bytes=len(data), git_blob_sha1=expected,
            sha256=hashlib.sha256(data).hexdigest(), shape=list(array.shape),
            dtype=str(array.dtype), minimum=float(array.min()),maximum=float(array.max()),
            nonzero=int(np.count_nonzero(array)))
    for name, expected in [('names','19e964a95d45d30f8e0b1ba3ced52a08192da4c7'),
                           ('slider','3f4ecedef8ccfb8794a83121b243333568cd8b57'),
                           ('network','64a0ba0a39d5e7745a842ffd0ca1275a68cc8edc')]:
        response=json.loads((SOURCES/(name+'-response.json')).read_text())
        text=response['result']['structuredContent']['content']
        assert git_blob(text.encode()) == expected, name
        report[name]=dict(bytes=len(text.encode()),git_blob_sha1=expected)
        if name=='names':
            names=ast.literal_eval(text)
    assert len(names)==N and len(set(names))==N
    for name,expected in [('FWD','0840d0d732a38e1b76de384310e113ecda8e1405'),
                          ('PLM','87d8afda2195a3fb5a8dec2bd05a1a14ca5104f2')]:
        data=(SOURCES/(name+'.json')).read_bytes()
        # apply_patch preserves the content's original newline plus one when absent.
        if git_blob(data)!=expected and data.endswith(b'\n') and git_blob(data[:-1])==expected:
            canonical=data[:-1]
        else:
            canonical=data
        assert git_blob(canonical)==expected,name
        report[name]=dict(bytes=len(canonical),git_blob_sha1=expected,
                          local_added_terminal_newline=(data!=canonical))
    return names, report

def build_source():
    names, manifest=decode_assets()
    gg=np.load(SOURCES/'Gg.npy',allow_pickle=False)
    gs=np.load(SOURCES/'Gs.npy',allow_pickle=False)
    mask=np.load(SOURCES/'emask.npy',allow_pickle=False)
    print('ASSET_SHAPES',json.dumps(manifest),flush=True)
    assert gg.shape==gs.shape==(N,N) and mask.shape==(N,1)
    assert (gg>=0).all() and (gs>=0).all() and set(np.unique(mask))<={False,True}
    original=(PREVIOUS/'interactome-initialize.py').read_bytes()
    assert git_blob(original)=='27bc70d6986e17d00fedf85ffbcaf8cb6b1b7d47'
    tree=ast.parse(original.decode())
    constants={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            key=node.targets[0].id
            if key in ['N','Gc','C','ggap','gsyn','Ec','ar','ad','B','Iext','rate','offset']:
                constants[key]=eval(compile(ast.Expression(node.value),'source-constant','eval'),{'__builtins__':{}},{})
    env=dict(constants,np=np,sparse=sparse,linalg=linalg,
             Gg_Static=gg,Gs_Static=gs,Gg_Dynamic=gg,Gs_Dynamic=gs,
             E=-48.0*mask,EMat=np.tile((-48.0*mask).reshape(N),(N,1)))
    wanted=['EffVth','EffVth_rhs','update_Mask','membrane_voltageRHS','compute_jacobian','voltage_filter']
    nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in wanted]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'EXACT_PINNED_SOURCE_FUNCTIONS','exec'),env)
    env['EffVth'](gg,gs)
    constants['inhibitory_reversal']=-48.0
    constants['threshold_gate_rounded']=round(constants['ar']/(constants['ar']+2*constants['ad']),4)
    return names,manifest,env,constants

def set_source_mask(env,mask,old=None,switch=0.0):
    env.update(oldMask=mask.copy() if old is None else old.copy(),newMask=mask.copy(),
        t_Switch=switch,transit_End=switch+.3,
        Vth_Static=env['EffVth_rhs'](env['Iext'],mask))

def efficient_system(env):
    gg,gs=env['Gg_Dynamic'],env['Gs_Dynamic']
    gap=sparse.csr_matrix(gg)-sparse.diags(gg.sum(axis=1))
    syn=sparse.csr_matrix(gs)
    rev=env['E'].reshape(N)
    def rhs(t,y):
        v,s=y[:N],y[N:]
        if env['t_Switch']<=t<=env['transit_End']:
            mask=env['update_Mask'](env['oldMask'],env['newMask'],t,env['t_Switch']+env['offset'])
            threshold=env['EffVth_rhs'](env['Iext'],mask)
        else:
            mask,threshold=env['newMask'],env['Vth_Static']
        activation=1/(1+np.exp(-env['B']*(v-threshold)))
        dv=(-env['Gc']*(v-env['Ec'])+gap.dot(v)-syn.dot(s)*v+syn.dot(s*rev)+env['Iext']*mask)/env['C']
        ds=env['ar']*(1-s)*activation-env['ad']*s
        return np.r_[dv,ds]
    def jac(t,y):
        return env['compute_jacobian'](t,y)
    return rhs,jac

def scalar_rhs(env,t,y):
    # Independent explicit sums, not the source's tiled broadcasting.
    v,s=y[:N],y[N:]
    mask=env['newMask']
    threshold=env['EffVth_rhs'](env['Iext'],mask)
    out=np.zeros(2*N)
    for i in range(N):
        gap=sum(float(env['Gg_Dynamic'][i,j])*(v[i]-v[j]) for j in range(N))
        syn=sum(float(env['Gs_Dynamic'][i,j])*s[j]*(v[i]-env['E'][j,0]) for j in range(N))
        out[i]=(-env['Gc']*(v[i]-env['Ec'])-gap-syn+env['Iext']*mask[i])/env['C']
        activation=1/(1+np.exp(-env['B']*(v[i]-threshold[i])))
        out[N+i]=env['ar']*(1-s[i])*activation-env['ad']*s[i]
    return out

def original_integrate(env,y0,times,atol=1e-9,rtol=1e-8):
    solver=integrate.ode(env['membrane_voltageRHS'],env['compute_jacobian']).set_integrator(
        'vode',atol=atol,rtol=rtol,min_step=1e-8,method='bdf',nsteps=10000)
    solver.set_initial_value(y0,0)
    output=[y0.copy()]
    for t in times[1:]:
        output.append(solver.integrate(float(t)).copy())
        assert solver.successful(), 'original VODE unsuccessful'
    return np.asarray(output)

def main():
    names,manifest,env,constants=build_source()
    print('ASSETS_AND_ORIGINAL_SOURCE_VERIFIED',flush=True)
    masks={}
    for title in ['FWD','PLM']:
        data=json.loads((SOURCES/(title+'.json')).read_text())
        assert set(data)==set(names) and all(row['activated'] for row in data.values())
        masks[title]=np.array([data[name]['inputCurrent'] for name in names])
    # Fixed initial seed once; source normal law, no state/seed search.
    y0=1e-4*np.random.RandomState(0).normal(0,.94,2*N)
    comparisons={}
    for title,mask in [('DEFAULT_ZERO',np.zeros(N)),('PUBLISHED_FWD_PRESET',masks['FWD'])]:
        set_source_mask(env,mask)
        rhs,jac=efficient_system(env)
        direct=scalar_rhs(env,1.,y0)
        source=env['membrane_voltageRHS'](1.,y0)
        independent=rhs(1.,y0)
        relative=float(np.max(np.abs(source-direct))/max(1,float(np.max(np.abs(source)))))
        assert relative<1e-12
        assert np.allclose(independent,source,atol=1e-8,rtol=1e-12)
        # Same full558state trajectory through two differently expressed RHS/solvers.
        times=np.arange(55)*.01
        original=original_integrate(env,y0,times)
        check=integrate.solve_ivp(rhs,[0,float(times[-1])],y0,method='Radau',
            jac=jac,t_eval=times,atol=1e-10,rtol=1e-9)
        assert check.success
        discrepancy=float(np.max(np.abs(original-check.y.T)))
        assert discrepancy<1e-3,(title,discrepancy)
        np.savez_compressed(ROOT/(title+'_reference.npz'),t=times,source=original,independent=check.y.T,y0=y0,mask=mask)
        comparisons[title]=dict(scalar_rhs_max_relative_error=relative,
            scalar_rhs_max_absolute_error=float(np.max(np.abs(source-direct))),
            integrated_max_absolute_error=discrepancy,original_vode_success=True,
            independent_radau_success=check.success,states=2*N,seconds=float(times[-1]))
        print('FULL_ORIGINAL_REFERENCE',title,comparisons[title],flush=True)
    # Relevant published sustained-input condition: ten reported ~2s cycles.
    set_source_mask(env,masks['FWD'])
    rhs,jac=efficient_system(env)
    t=np.arange(2001)*.01
    full=integrate.solve_ivp(rhs,[0,20.],y0,method='BDF',jac=jac,t_eval=t,atol=1e-9,rtol=1e-8)
    assert full.success
    np.savez_compressed(ROOT/'FWD_20s_reference.npz',t=t,y=full.y.T,y0=y0,mask=masks['FWD'])
    motor=[i for i,n in enumerate(names) if n.startswith(('DB','VB','DD','VD'))]
    raw=full.y[:N].T
    peaks,_=signal.find_peaks(raw[t>=10,names.index('VB01')],prominence=.1)
    sustained=dict(seconds=20.,success=full.success,nfev=full.nfev,
        voltage_min=float(raw.min()),voltage_max=float(raw.max()),
        motor_last10s_rms_temporal_sd=float(np.sqrt(np.mean(np.var(raw[t>=10][:,motor],axis=0)))),
        VB01_last10s_peaks=int(len(peaks)),VB01_median_peak_interval=(float(np.median(np.diff(t[t>=10][peaks]))) if len(peaks)>1 else None))
    result=dict(status='FULL_ORIGINAL_2019_RELEASE_REFERENCE_EXECUTED',
        utc=datetime.now(timezone.utc).isoformat(),constants=constants,assets=manifest,
        comparisons=comparisons,sustained_fwd_reference=sustained,
        python=os.sys.version,numpy=np.__version__,scipy=scipy.__version__,
        elapsed_s=time.monotonic()-T0,max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        independent_units='one deterministic published connectome, one preselected source-law seed; no animals',
        scope='Source-equation extraction of own pinned2019beta version; not exact2017, not full published numerical reproduction. No NEWpilot evaluation.',
        native_threads='environment variables set1 before NumPy/Scipy import; OS enforcement not independently measured')
    (ROOT/'MODEL_REFERENCE.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':
    main()
