"""Preserve frozen bytes; make an explicitly audited numerical-only revision."""
from pathlib import Path
import json,hashlib,datetime
OUT=Path(__file__).resolve().parent
src=(OUT/'analysis.py').read_text()
replacements={
    "eta=X@beta":"eta=np.einsum('ij,j->i',X,beta,optimize=False)",
    "grad=X.T@(w*(expit(eta)-y))+RIDGE*beta":"grad=np.einsum('ij,i->j',X,w*(expit(eta)-y),optimize=False)+RIDGE*beta",
    "expit(X[test]@beta)":"expit(np.einsum('ij,j->i',X[test],beta,optimize=False))",
    "offset=H@theta":"offset=np.einsum('ij,j->i',H,theta,optimize=False)",
    "expit(base[test]@nb+offset[test])":"expit(np.einsum('ij,j->i',base[test],nb,optimize=False)+offset[test])",
    "eta=N@base":"eta=np.einsum('ij,j->i',N,base,optimize=False)",
    "fd-grad@v":"fd-np.sum(grad*v)",
    "OUT=Path(__file__).resolve().parent":"OUT=Path(__file__).resolve().parent/'corrected'\nOUT.mkdir(exist_ok=True)",
}
for old,new in replacements.items():
    assert old in src,old
    src=src.replace(old,new)
start=src.index('def bootstrap(');end=src.index('\ndef summarize(',start)
src=src[:start]+'''_BOOT={}
def bootstrap(g,column,reps=2000):
    if len(g)==0:return [None,None]
    key=(tuple(g.subject),str(g.iloc[0].species),reps)
    if key not in _BOOT:
        rng=np.random.default_rng(20261031);a=g.reset_index(drop=True)
        group='schedule' if a.iloc[0].species=='human' else 'lab'
        clusters=[v.index.to_numpy() for _,v in a.groupby(group)]
        W=np.zeros((reps,len(a)))
        for b in range(reps):
            draw=[]
            if group=='schedule':
                for j in rng.integers(len(clusters),size=len(clusters)):
                    ids=clusters[j];draw.extend(ids[rng.integers(len(ids),size=len(ids))])
            else:
                for ids in clusters:draw.extend(ids[rng.integers(len(ids),size=len(ids))])
            W[b]=np.bincount(draw,minlength=len(a))/len(draw)
        _BOOT[key]=W
    values=np.einsum('ij,j->i',_BOOT[key],g[column].to_numpy(),optimize=False)
    return np.quantile(values,[.025,.975]).tolist()
''' + src[end:]
audit='''
def numerical_audit(N,H,frame,y):
    import warnings
    valid=frame.responded.to_numpy();X=N[valid];w=weights(frame,valid);yy=y[valid]
    b=np.linspace(-.03,.03,X.shape[1]);v=np.linspace(-.01,.02,X.shape[0])
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter('always')
        legacy=X@b;legacy_g=X.T@v
    explicit=np.einsum('ij,j->i',X,b,optimize=False);explicit_g=np.einsum('ij,i->j',X,v,optimize=False)
    assert np.isfinite(X).all() and np.isfinite(legacy).all() and np.isfinite(legacy_g).all()
    errors=[float(np.max(np.abs(legacy-explicit))),float(np.max(np.abs(legacy_g-explicit_g)))]
    assert errors[0]<1e-12 and errors[1]<1e-9,errors
    r=dict(finite_inputs=True,finite_outputs=True,matrix_shape=list(X.shape),max_matvec_error=errors[0],max_transpose_matvec_error=errors[1],
           legacy_warning_messages=[str(x.message) for x in ws],
           correction='Explicit contractions throughout optimization and prediction; same objective/features/folds/ridge/support. Cached bootstrap draws preserve original RNG order.')
    (OUT/'NUMERICAL_AUDIT.json').write_text(json.dumps(r,indent=2)+'\\n')
'''
src=src.replace('\ndef main():',audit+'\ndef main():')
src=src.replace("if not controls:\n        diagnostics", "if not controls:\n        numerical_audit(N,H,frame,y)\n        diagnostics")
tail="if __name__=='__main__':main()"
assert tail in src
src=src.replace(tail,"""if __name__=='__main__':
    from contextlib import redirect_stdout,redirect_stderr
    mode='controls' if '--controls' in sys.argv else 'main'
    class Tee:
        def __init__(self,a,b):self.a=a;self.b=b
        def write(self,x):self.a.write(x);self.b.write(x);self.b.flush()
        def flush(self):self.a.flush();self.b.flush()
    with (OUT/(mode+'.stdout')).open('w') as so,(OUT/(mode+'.stderr')).open('w') as se:
        with redirect_stdout(Tee(sys.stdout,so)),redirect_stderr(Tee(sys.stderr,se)):main()
""")
assert '@' not in src.split('def numerical_audit')[0]
path=OUT/'analysis_explicit.py';assert not path.exists();path.write_text(src)
amend=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
          reason='Known workspace NumPy2.0.2 matmul warnings on small finite products. Initial run stopped with KeyboardInterrupt during first B bootstrap; no summary accepted. First partial unit scores/diagnostics retained at task root.',
          original_analysis_sha256=hashlib.sha256((OUT/'analysis.py').read_bytes()).hexdigest(),
          revised_analysis_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
          scientific_changes='NONE. Same objective, regularization, features, cohorts, folds, support, controls, score and bootstrap RNG sequence. Explicit contractions plus cached identical bootstrap draws and logging only.',
          extra_read_charge_bytes=90000000)
(OUT/'NUMERICAL_AMENDMENT.json').write_text(json.dumps(amend,indent=2)+'\n')
print(json.dumps(amend,indent=2))
