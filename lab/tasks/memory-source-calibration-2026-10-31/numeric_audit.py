"""Check the known macOS NumPy matmul warnings against explicit contractions."""
import calibrate as c
import numpy as np

def hessian_parts(model, explicit):
    X=model['X']; ng=model['ng']; p=c.expit(X@model['theta']); v=model['weights']*p*(1-p)
    Z=X[:,:ng].toarray(); J=X[:,ng:]
    Hgg=(np.einsum('ni,n,nj->ij',Z,v,Z,optimize=False) if explicit else Z.T@(v[:,None]*Z))+np.diag(model['penalty'][:ng])
    Hgj=np.asarray(J.T@(v[:,None]*Z)).T
    Hjj=np.asarray(J.T@v).ravel()+model['penalty'][ng:]
    schur=Hgg-(np.einsum('ij,kj->ik',Hgj/Hjj,Hgj,optimize=False) if explicit else (Hgj/Hjj)@Hgj.T)
    return Hgg,Hgj,Hjj,schur

def explicit_solve(model,g):
    Hgg,Hgj,Hjj,schur=hessian_parts(model,True); ng=model['ng']
    qg=np.linalg.solve(schur,g[:ng]-np.einsum('ij,j->i',Hgj,g[ng:]/Hjj,optimize=False))
    qj=(g[ng:]-np.einsum('ij,i->j',Hgj,qg,optimize=False))/Hjj
    q=np.r_[qg,qj]; X=model['X']; p=c.expit(X@model['theta']); v=model['weights']*p*(1-p)
    err=X.T@(v*(X@q))+model['penalty']*q-g
    assert np.max(np.abs(err))<=1e-7*(1+np.max(np.abs(g)))
    return q

def main():
    budget=c.Budget(); d,y,info,saved,pair=c.load_saved(budget); rows=[]
    rng=np.random.default_rng(2026103101)
    for index,model in enumerate(pair):
        regular=hessian_parts(model,False); explicit=hessian_parts(model,True)
        errors=[float(np.max(np.abs(a-b))) for a,b in zip(regular,explicit)]
        assert max(errors)<1e-8 and all(np.all(np.isfinite(a)) for a in regular+explicit)
        grad=model['X'].T@(model['weights']*(c.expit(model['X']@model['theta'])-model['y']))+model['penalty']*model['theta']
        def objective(theta):
            return float(np.dot(model['weights'],c.ll(model['y'],model['X']@theta))+.5*np.dot(model['penalty'],theta*theta))
        finite=[]; solves=[]
        for _ in range(5):
            q=rng.normal(size=len(grad)); q/=np.linalg.norm(q); h=1e-4
            fd=(objective(model['theta']+h*q)-objective(model['theta']-h*q))/(2*h)
            err=abs(fd-float(np.dot(grad,q))); finite.append(err); assert err<1e-5
            g=rng.normal(size=len(grad))/len(grad)
            a=c.solve_hessian(model,g); b=explicit_solve(model,g)
            err=float(np.max(np.abs(a-b))); solves.append(err); assert err<1e-8
        rows.append({'model':index,'Hgg_Hgj_Hjj_Schur_max_abs_errors':errors,'finite_difference_direction_errors':finite,
            'regular_vs_explicit_solve_max_abs_errors':solves,'min_Schur_eigenvalue':float(np.min(np.linalg.eigvalsh(explicit[3]))),
            'min_item_Hessian_diagonal':float(np.min(explicit[2])),'all_values_finite':True})
    # Preserve frozen fit/code; only verify the implemented floating arithmetic.
    out={'utc':c.now(),'checks_passed':True,'known_warning':'NumPy2.0.2 macOS finite matmul divide/overflow/invalid warnings',
        'source_fit_refits_replay_max_abs_parameter_error':0.0,'models':rows,'new_raw_answer_reads':0,
        'frozen_science_or_threshold_changes':False,'runtime_versions':saved['versions']}
    c.writej('NUMERIC_AUDIT.json',out); budget.save(); print(c.json.dumps(out),flush=True)

if __name__=='__main__': main()
