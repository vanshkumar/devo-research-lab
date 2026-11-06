"""Postprocessing/numerical audit of the SAME consumed frozen outputs; no new pilot."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import csv
import hashlib
import json
import math
import resource
import time
import warnings
from datetime import datetime,timezone

START=time.monotonic()
from reference import np,linalg,N,ROOT,build_source,set_source_mask

def main():
    freeze=json.loads((ROOT/'FREEZE.json').read_text())
    for name,sha in freeze['sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha
    report=json.loads((ROOT/'PILOT_RESULT.json').read_text())
    names,_,env,_=build_source()
    motors=np.array([i for i,n in enumerate(names) if n.startswith(('DB','VB','DD','VD'))])
    recomputed=[]
    for seed in [0,1]:
        with np.load(ROOT/f'seed{seed}_finite.npz',allow_pickle=False) as a,np.load(ROOT/f'seed{seed}_sham.npz',allow_pickle=False) as b:
            t=a['t'];a=a['y'];b=b['y']
            assert np.isfinite(a).all() and np.isfinite(b).all()
            finite=a;sham=b
            summary={}
            # Direct scalar accumulation, no source scoring helper or matrix product.
            for label,lo,hi in [('late',40.,42.),('challenge',42.3,44.)]:
                indices=np.flatnonzero((t>=lo-1e-9)&(t<=hi+1e-9))
                total=math.fsum((float(a[k,i])-float(b[k,i]))**2 for k in indices for i in motors)
                summary[label]=math.sqrt(total/(len(indices)*len(motors)))
            expected=report['results'][seed]
            assert math.isclose(summary['late'],expected['retained_motor_rms'],rel_tol=1e-12)
            assert math.isclose(summary['challenge'],expected['challenge_motor_rms'],rel_tol=1e-12)
            recomputed.append(dict(seed=seed,**summary))
            if seed==0:
                origin=int(round((23-20)/.01))
                initial_difference=finite[origin]-sham[origin]
                origin_state=sham[origin].copy()
    set_source_mask(env,np.zeros(N),switch=22.)
    jac=env['compute_jacobian'](23.,origin_state)
    assert np.isfinite(jac).all()
    A=19.*jac
    scale_count=max(0,math.ceil(math.log2(float(np.linalg.norm(A,1))/.25)))
    reduced=A/(2**scale_count)
    # Independently expressed Taylor + scaling/squaring. Every matrix product
    # uses the explicit einsum C loop, bypassing this Mac's warning-prone matmul.
    exp_explicit=np.eye(2*N)
    term=np.eye(2*N)
    for k in range(1,25):
        term=np.einsum('ik,kj->ij',term,reduced,optimize=False)/k
        exp_explicit+=term
    for _ in range(scale_count):
        exp_explicit=np.einsum('ik,kj->ij',exp_explicit,exp_explicit,optimize=False)
    with warnings.catch_warnings(record=True) as wr:
        warnings.simplefilter('always')
        exp_scipy=linalg.expm(A)
    assert np.isfinite(exp_explicit).all() and np.isfinite(exp_scipy).all()
    scipy_action=np.einsum('ij,j->i',exp_scipy,initial_difference,optimize=False)
    explicit_action=np.einsum('ij,j->i',exp_explicit,initial_difference,optimize=False)
    exp_relative=float(np.max(np.abs(exp_explicit-exp_scipy))/np.max(np.abs(exp_explicit)))
    action_error=float(np.max(np.abs(explicit_action-scipy_action)))
    assert exp_relative<1e-5
    result=dict(utc=datetime.now(timezone.utc).isoformat(),frozen_bytes_unchanged=True,
        all_six_primary_outputs_and_references_preserved=True,
        independently_recomputed_scores=recomputed,
        matrix_exponential_audit=dict(scaling_steps=scale_count,taylor_terms=24,
            all_matrix_and_action_values_finite=True,max_relative_matrix_discrepancy=exp_relative,
            max_absolute_action_discrepancy=action_error,
            explicit_motor_action_rms=float(np.sqrt(np.mean(explicit_action[:N][motors]**2))),
            scipy_warnings=[str(w.message) for w in wr],
            interpretation='Warning cause unidentified. Explicit contractions corroborate this finite control; no sub-resolution physical tail claim.'),
        elapsed_s=time.monotonic()-START,max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (ROOT/'OUTPUT_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    with (ROOT/'PILOT_SUMMARY.csv').open('w') as stream:
        fields=['seed','retained_motor_rms','retained_fraction','challenge_motor_rms','challenge_fraction','maintained_drive_motor_rms']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in report['results']:writer.writerow({key:row[key] for key in fields})
    # Inspectable inventory: explicit task bytes/hash, not complete physical I/O.
    inventory={}
    for item in sorted(ROOT.rglob('*')):
        if item.is_file() and item.suffix in ['.npz','.npy','.json','.md','.py','.b64','.csv'] and item.name!='OUTPUT_INVENTORY.json':
            data=item.read_bytes()
            inventory[str(item.relative_to(ROOT))]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    (ROOT/'OUTPUT_INVENTORY.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
