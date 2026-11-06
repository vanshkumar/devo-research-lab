"""Independent core numerical audit of author linear-tail/warning claim."""
from independent_model import *
import resource
import time
import datetime
start=time.monotonic()
m=Model()
with np.load(AUTHOR/'seed0_sham.npz',allow_pickle=False) as z:t=z['t'].copy();s=z['y'].copy()
with np.load(AUTHOR/'seed0_finite.npz',allow_pickle=False) as z:f=z['y'].copy()
ix=int(np.argmin(abs(t-23.)))
j=m.jac(23.,s[ix],m.zero);delta=f[ix]-s[ix]
eigenvalues=linalg.eigvals(j)
a=19.*j
with warnings.catch_warnings(record=True) as observed:
    warnings.simplefilter('always')
    scipy_result=linalg.expm(a)
notices=[{'category':w.category.__name__,'message':str(w.message)} for w in observed]
# Entirely explicit contractions; no author audit or matrix helpers.
scaling=max(0,int(np.ceil(np.log2(max(1.,np.linalg.norm(a,1))/.25))))
small=a/(2.**scaling)
identity=np.eye(2*N);term=identity.copy();explicit=identity.copy()
for k in range(1,25):
    term=np.einsum('ik,kj->ij',term,small,optimize=False)/k
    explicit+=term
for _ in range(scaling):explicit=np.einsum('ik,kj->ij',explicit,explicit,optimize=False)
scipy_action=np.einsum('ij,j->i',scipy_result,delta,optimize=False)
explicit_action=np.einsum('ij,j->i',explicit,delta,optimize=False)
assert np.isfinite(explicit).all() and np.isfinite(scipy_result).all()
sourcep=m.source
m.source_setup(m.zero,m.zero,0.)
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'independent_full558_jacobian':True,
 'source_jacobian_maxabs':float(np.max(abs(j-sourcep['compute_jacobian'](23.,s[ix])))),
 'zero_input_largest_eigenvalue_real':float(np.max(eigenvalues.real)),
 'scipy_warnings':notices,'warnings_count':len(notices),
 'explicit_taylor_terms':24,'scaling_squarings':scaling,
 'finite_all':True,
 'matrix_relative_maxabs':float(np.max(abs(scipy_result-explicit))/max(np.max(abs(explicit)),1e-300)),
 'action_maxabs_difference':float(np.max(abs(scipy_action-explicit_action))),
 'explicit_motor_action_rms':rms(explicit_action[m.motor]),
 'observed_motor_difference_rms_at42':rms((f-s)[np.argmin(abs(t-42.)),m.motor]),
 'interpretation':'Local relaxation corroborated below numerical resolution, not global stability/unique attractor proof; warning cause unknown.',
 'source_names_blob':None,'source_ui_blobs':{},
 'elapsed_s':time.monotonic()-start,'rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
for fname,expected in [('names-response.json','19e964a95d45d30f8e0b1ba3ced52a08192da4c7'),
                       ('slider-response.json','3f4ecedef8ccfb8794a83121b243333568cd8b57'),
                       ('network-response.json','64a0ba0a39d5e7745a842ffd0ca1275a68cc8edc')]:
    obj=json.loads((AUTHOR/'sources'/fname).read_text())
    payload=obj['result']['structuredContent']['content'].encode()
    observed=hashlib.sha1(('blob '+str(len(payload))+'\0').encode()+payload).hexdigest()
    assert observed==expected,(fname,observed)
    entry={'canonical_bytes':len(payload),'git_blob':observed,'sha256':hashlib.sha256(payload).hexdigest()}
    if fname.startswith('names'):report['source_names_blob']=entry
    else:report['source_ui_blobs'][fname]=entry
write('NUMERICAL_AUDIT.json',report)
print(json.dumps(report,indent=2))
