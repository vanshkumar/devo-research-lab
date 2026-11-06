"""Selected-source and cached-input checks; no new stability outcomes.

The implementation imported below is the PREDECESSOR reviewer's independently
expressed model. Reuse is attributed and does not make this study independent
of that helper. Original pinned source functions remain an external comparator.
"""
import os
for _name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
              'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_name] = '1'
import datetime
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import resource
import time
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
REVIEW = ROOT/'lab/reviews/interactome-transient-reachability-2026-11-03'
spec = importlib.util.spec_from_file_location('prior_review_model', REVIEW/'independent_model.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
N = prior.N

def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def background(m):
    b = m.presets['PLM'].copy()
    for name in ('ASKL', 'ASKR'):
        b[m.names.index(name)] = .24
    return b

def scalar_rhs(m, y, mask):
    """Literal scalar accumulation, independent of both vector expressions."""
    v, s = y[:N], y[N:]
    threshold = m.threshold(mask)
    dv = np.empty(N)
    ds = np.empty(N)
    for i in range(N):
        gap = sum(float(m.gg[i,j])*(float(v[i])-float(v[j])) for j in range(N))
        syn = sum(float(m.gs[i,j])*float(s[j])*(float(v[i])-float(m.e[j])) for j in range(N))
        dv[i] = (-prior.GC*(float(v[i])-prior.EC)-gap-syn+prior.CURRENT*float(mask[i]))/prior.CAP
        q = float(prior.expit(prior.BETA*(v[i]-threshold[i])))
        ds[i] = prior.RISE*(1-float(s[i]))*q-prior.DECAY*float(s[i])
    return np.r_[dv, ds]

def main():
    start = time.monotonic()
    m = prior.Model()
    b = background(m)
    states = {}
    pins = {}
    section = None
    cached = {}
    for seed in (0,1):
        for branch in ('finite','sham'):
            name = f'contrary_seed{seed}_{branch}.npz'
            data = (REVIEW/name).read_bytes()
            pins[name] = {'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest()}
            with np.load(io.BytesIO(data), allow_pickle=False) as z:
                t = z['t']; y = z['y']
            ix = int(np.argmin(abs(t-42.)))
            assert abs(t[ix]-42.) < 1e-12 and y.shape[1] == 2*N
            key = f'seed{seed}_{branch}'
            states[key] = y[ix].copy()
            if seed == 0 and branch == 'sham':
                j = m.names.index('VB01')
                selected = (t >= 30-1e-10) & (t <= 42+1e-10)
                section = float(np.mean(y[selected,j]))
                cached['section_neuron'] = 'VB01'
                cached['section_source_window_s'] = [30.,42.]
                cached['section_value_source_voltage'] = section
                cached['section_min_max'] = [float(y[selected,j].min()),float(y[selected,j].max())]
            del y, data
    checks = {}
    for key,y in states.items():
        m.source_setup(b,b,0.)
        rhs = m.rhs(42., y, b)
        scalar = scalar_rhs(m,y,b)
        source = m.source['membrane_voltageRHS'](42., y)
        js = m.source['compute_jacobian'](42., y)
        jac = m.jac(42., y,b)
        direction = np.sin(np.arange(2*N)+.5)
        direction[N:] *= .001
        eps = 1e-4
        fd = (m.rhs(42.,y+eps*direction,b)-m.rhs(42.,y-eps*direction,b))/(2*eps)
        action = np.einsum('ij,j->i',jac,direction,optimize=False)
        checks[key] = {
            'source_sparse_rhs_maxabs':float(np.max(abs(rhs-source))),
            'scalar_sparse_rhs_maxabs':float(np.max(abs(rhs-scalar))),
            'source_sparse_jac_maxabs':float(np.max(abs(jac-js))),
            'central_directional_jac_relative':float(np.linalg.norm(fd-action)/np.linalg.norm(action))
        }
        assert checks[key]['source_sparse_rhs_maxabs'] < 1e-5
        assert checks[key]['scalar_sparse_rhs_maxabs'] < 1e-5
        assert checks[key]['source_sparse_jac_maxabs'] < 1e-8
        assert checks[key]['central_directional_jac_relative'] < 1e-5
    y0 = 1e-4*np.random.RandomState(0).normal(0,.94,2*N)
    t, literal = m.literal_short(y0,m.presets['FWD'])
    ti, independent = m.schedule(y0,0,.54,m.zero,[(0.,m.presets['FWD'])])
    assert np.max(abs(t-ti)) < 1e-12
    error = float(np.max(abs(literal-independent)))
    assert error < .001
    np.savez_compressed(OUT/'SOURCE_REFERENCE.npz',t=t,literal=literal,sparse=independent)
    np.savez_compressed(OUT/'INPUT_STATES.npz',background=b,section=np.array(section),**states)
    record = {
        'status':'SELECTED_ORIGINAL_SOURCE_AND_CACHED_STATES_VERIFIED',
        'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'new_stability_or_continuation_outcomes_generated':False,
        'model_tree':'bdb94ca174980e46777f7b1936f539903c688719',
        'model_source_version':'3.0.0-beta, own 2019 release; not exact 2017',
        'source_fixed_asset_pins':m.pins,
        'reused_model_helper':{'path':str(REVIEW/'independent_model.py'),'sha256':sha(REVIEW/'independent_model.py'),
                             'not_an_independent_review_of_this_helper':True},
        'cached_input_pins':pins,
        'cached_section':cached,
        'background_nonzeros':{n:float(b[i]) for i,n in enumerate(m.names) if b[i]},
        'fwd_nonzeros':{n:float(m.presets['FWD'][i]) for i,n in enumerate(m.names) if m.presets['FWD'][i]},
        'neuron_state_motor_counts':[N,2*N,len(m.motor)],
        'actual_noninitial_source_scalar_jacobian_checks':checks,
        'fresh_original_FWD_54step_source_VODE_sparse_Radau_maxabs':error,
        'common_threshold_source_maxabs':float(np.max(abs(m.threshold(b)-m.source['EffVth_rhs'](prior.CURRENT,b)))),
        'process_self_elapsed_s':time.monotonic()-start,
        'rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'scientific_protocol_revisions':0,
        'new_public_operations':0,
        'new_empirical_or_protected_inputs':0
    }
    write('REFERENCE.json',record)
    print(json.dumps(record,indent=2))

if __name__ == '__main__':
    main()
