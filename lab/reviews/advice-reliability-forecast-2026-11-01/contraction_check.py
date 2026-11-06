"""Reference replay of the SAME analysis with explicit finite contractions.

Imports only our independently authored review, never author scientific code.
Keeps warned outputs untouched. No scientific model or design changes.
"""
import review as r
import warnings
np=r.np
BASE=r.HERE
REF=BASE/'explicit_reference'
REF.mkdir(exist_ok=True)
for name in ('raw_reconstructed.npz','CONTRARY_PLAN.md'):
    (REF/name).write_bytes((BASE/name).read_bytes())
r.HERE=REF

def mm(a,b):
    assert np.isfinite(a).all() and np.isfinite(b).all()
    result=np.einsum('ij,jk->ik',a,b,optimize=False)
    assert np.isfinite(result).all()
    return result

def vm(a,b):
    assert np.isfinite(a).all() and np.isfinite(b).all()
    result=np.einsum('i,ij->j',a,b,optimize=False)
    assert np.isfinite(result).all()
    return result

class ExplicitRidge(r.Ridge):
    def system(self,w,ys,xy):
        n=float(np.einsum('i,i->',w,self.n,optimize=False))
        mx=np.einsum('g,gd->d',w,self.s1,optimize=False)/n
        cov=np.einsum('g,gij->ij',w,self.s2,optimize=False)/n-np.outer(mx,mx)
        var=np.diag(cov); scale=np.where(var<1e-14,1.,np.sqrt(np.maximum(var,1e-14)))
        gram=cov/np.outer(scale,scale); values,vectors=np.linalg.eigh((gram+gram.T)/2.)
        my=np.einsum('g,gk->k',w,ys,optimize=False)/n
        rhs=(np.einsum('g,gdk->dk',w,xy,optimize=False)/n-mx[:,None]*my)/scale[:,None]
        return mx,scale,values,vectors,my,mm(vectors.T,rhs)
    def solve(self,system,penalty):
        mx,scale,values,vectors,my,rhs=system
        b=mm(vectors,rhs/(values[:,None]+penalty))/scale[:,None]
        return b,my-vm(mx,b)
    def fit(self,y,w=None):
        y,ys,xy=self.labels(y); k=y.shape[1]
        if w is None: w=np.ones(len(self.people))
        cv=np.zeros((5,k)); folds=0
        for j,ix in enumerate(self.groups):
            if w[j]==0: continue
            tw=w.copy(); tw[j]=0.
            system=self.system(tw,ys,xy)
            for ll,lam in enumerate(r.PENALTIES):
                b,c=self.solve(system,lam)
                pred=np.clip(mm(self.x[ix],b)+c,-1,1)
                cv[ll]+=w[j]*np.mean(r.cw(y[ix]-pred)**2,axis=0)
                folds+=1
        cv/=w.sum()
        chosen=np.max(np.where(cv<=cv.min(axis=0)+1e-12,np.arange(5)[:,None],-1),axis=0)
        system=self.system(w,ys,xy)
        coef=np.empty((self.dim,k)); intercept=np.empty(k)
        for ll in np.unique(chosen):
            b,c=self.solve(system,r.PENALTIES[ll]); use=chosen==ll
            coef[:,use]=b[:,use]; intercept[use]=c[use]
        return {'coef':coef,'intercept':intercept,'penalty':r.PENALTIES[chosen],'cv':cv*32400.,'fold_penalty_solves':folds}

def explicit_predict(fit,x):
    xx=x[:,:fit['coef'].shape[0]]
    ok=np.isfinite(xx).all(axis=1)
    p=np.full((len(xx),fit['coef'].shape[1]),np.nan)
    p[ok]=np.clip(mm(xx[ok],fit['coef'])+fit['intercept'],-1,1)
    return p

def explicit_direct_fit(x,y,lam):
    mx=x.mean(axis=0); my=y.mean(); scale=x.std(axis=0); scale=np.where(scale<1e-7,1.,scale)
    z=(x-mx)/scale
    gram=np.einsum('ni,nj->ij',z,z,optimize=False)/len(x)
    rhs=np.einsum('ni,n->i',z,y-my,optimize=False)/len(x)
    values,vectors=np.linalg.eigh((gram+gram.T)/2.)
    transform=np.einsum('ji,j->i',vectors,rhs,optimize=False)
    b=np.einsum('ij,j->i',vectors,transform/(values+lam),optimize=False)/scale
    assert np.isfinite(b).all()
    intercept=my-float(np.einsum('i,i->',mx,b,optimize=False))
    return {'coef':b[:,None],'intercept':np.array([intercept]),'penalty':np.array([lam])}

r.Ridge=ExplicitRidge
r.predict=explicit_predict
r.direct_fit_at_lambda=explicit_direct_fit
with warnings.catch_warnings(record=True) as seen:
    warnings.simplefilter('always')
    r.run_main()

def compare(a,b,path=''):
    result={'max_absolute_numeric_difference':0.,'categorical_mismatches':[],'numeric_comparisons':0}
    def visit(x,y,p):
        if isinstance(x,dict):
            for k in x:
                if k in ('timestamp_utc','peak_rss_bytes','input_ref','input_refs','full_examples','fold_penalty_solves'): continue
                visit(x[k],y[k],p+'/'+k)
        elif isinstance(x,list):
            assert len(x)==len(y),(p,len(x),len(y))
            for j,(xx,yy) in enumerate(zip(x,y)): visit(xx,yy,p+'/'+str(j))
        elif isinstance(x,bool) or isinstance(x,str) or x is None:
            if x!=y: result['categorical_mismatches'].append(p)
        elif isinstance(x,(int,float)):
            delta=abs(float(x)-float(y))
            result['max_absolute_numeric_difference']=max(result['max_absolute_numeric_difference'],delta)
            result['numeric_comparisons']+=1
    visit(a,b,path)
    return result

checks={}
for name in ('SOURCE_FIT_AUDIT.json','SCORE_AUDIT.json','CONTROL_AUDIT.json','SOURCE_STABILITY_AUDIT.json','CONTRARY.json'):
    old=r.json.loads((BASE/name).read_text()); new=r.json.loads((REF/name).read_text())
    checks[name]=compare(old,new)
    assert not checks[name]['categorical_mismatches'],checks[name]
    assert checks[name]['max_absolute_numeric_difference']<1e-8,checks[name]

forecast_checks={}
for name in ('reconstructed_forecasts.npz','contrary_forecasts.npz'):
    with np.load(BASE/name) as old,np.load(REF/name) as new:
        forecast_checks[name]={k:r.array_diff(old[k],new[k]) for k in old.files}
    assert all(v['same_missing'] and v['max_abs_difference']<1e-10 for v in forecast_checks[name].values())

out={'timestamp_utc':r.now(),'reason':'Preserved finite-matrix matmul warnings in original main run required explicit-contraction numerical reference before closing the new contrary. No model, seed, window, criterion or data changes. Original warned artifacts remain untouched.','reference_driver_sha256':r.hashlib.sha256(r.Path(__file__).read_bytes()).hexdigest(),'independent_review_code_sha256':r.hashlib.sha256((BASE/'review.py').read_bytes()).hexdigest(),'warnings_in_explicit_reference':[{'category':w.category.__name__,'message':str(w.message),'filename':w.filename,'lineno':w.lineno} for w in seen],'full_reference_replay_comparisons':checks,'full_forecast_comparisons':forecast_checks,'finite_contraction_assertions':'All explicit source/control/bootstrap/calibrated-fit matrix operands and results checked finite; expected missing current-judgment rows propagated separately.','peak_rss_bytes':r.resource.getrusage(r.resource.RUSAGE_SELF).ru_maxrss,'reference_output_directory':str(REF),'jobs_remaining':0}
(BASE/'NUMERICAL_WARNING_AUDIT.json').write_text(r.json.dumps(out,indent=2,allow_nan=False)+'\n')
print(r.json.dumps({'stage':'explicit finite-contraction reference complete','time':out['timestamp_utc'],'warning_count':len(seen),'comparisons':checks,'peak_rss_bytes':out['peak_rss_bytes']},indent=2))
