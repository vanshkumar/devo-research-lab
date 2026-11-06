from analysis import *
p=[p for p in load() if p['file']==FILES[0]];d=make_design(p,1);Q,rank=residualizer(d['NF']);Z=d['Z']
a=Q@(Q.T@Z);b=np.einsum('ij,jk->ik',Q,np.einsum('ji,jk->ik',Q,Z,optimize=False),optimize=False)
r={'Q_finite':bool(np.all(np.isfinite(Q))),'Z_finite':bool(np.all(np.isfinite(Z))),'matrix_product_finite':bool(np.all(np.isfinite(a))),'max_einsum_difference':float(np.max(np.abs(a-b))),'Qmax':float(np.max(np.abs(Q))),'Zmax':float(np.max(np.abs(Z)))}
(ROOT/'outputs/numerical_check.json').write_text(json.dumps(r,indent=2));print(r)
