"""Independent original-cell decoder and bounded numerical review. No author imports."""
import os
for _k in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_k] = '1'
import io, json, math, hashlib, zipfile, resource, sys
from pathlib import Path
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUTHOR = ROOT / 'lab/tasks/advice-reliability-forecast-2026-11-01'
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

def now(): return datetime.now(timezone.utc).isoformat()
def save(name, obj):
    (HERE/name).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')
def wrap(x): return (np.asarray(x)+180.)%360.-180.
def safe(v): return float(v) if np.isfinite(v) else None
def check_time():
    if now() >= '2026-11-01T12:15:15': raise RuntimeError('Fixed review deadline reached')

def initial():
    check_time()
    path=AUTHOR/'dataset_exp1.xlsx'
    buf=path.read_bytes()
    pin=hashlib.sha256(buf).hexdigest()
    assert pin=='cbd91790cb21a6a1c1abda7043dfe96bc9a01d0be2ed51c572a523466d937aa9'
    z=zipfile.ZipFile(io.BytesIO(buf))
    sb=z.read('xl/sharedStrings.xml')
    strings=[''.join(si.itertext()) for si in ET.fromstring(sb).findall(NS+'si')]
    headers=None; records=[]; exceptional=[]; typed_counts={}
    # iterparse reads cell type before interpreting a cached value. Shared-string
    # indices are never treated as numerical measurements.
    with z.open('xl/worksheets/sheet1.xml') as stream:
        for _, elem in ET.iterparse(stream,events=('end',)):
            if elem.tag!=NS+'row': continue
            rownum=int(elem.attrib['r']); values=[math.nan]*30; head=['']*30
            for cell in elem.findall(NS+'c'):
                coord=cell.attrib['r']; letters=''.join(c for c in coord if c.isalpha())
                col=0
                for c in letters: col=col*26+ord(c)-64
                col-=1
                typ=cell.attrib.get('t','n'); typed_counts[typ]=typed_counts.get(typ,0)+1
                v=cell.find(NS+'v'); token=None if v is None else v.text
                if typ=='s': value=strings[int(token)]
                elif typ=='inlineStr': value=''.join(cell.find(NS+'is').itertext())
                elif typ=='e': value=None
                else: value=token
                if rownum==1: head[col]=str(value).strip(); continue
                try: num=float(value)
                except (TypeError,ValueError): num=math.nan
                values[col]=num
                if not math.isfinite(num): exceptional.append({'coordinate':coord,'row':rownum,'column':col,'type':typ,'raw_token':token,'decoded':value})
            if rownum==1: headers=head
            else: records.append(values)
            elem.clear()
    a=np.asarray(records,dtype=float)
    assert a.shape==(47*378,30)
    p3=a[a[:,0]==3]; p13=a[a[:,0]==13]
    assert len(p3)==len(p13)==378
    missing=[]
    for row in p13:
        if not np.isfinite(row[[10,17]]).all():
            missing.append({'person':13,'block':int(row[3]),'trial':int(row[5]),'trial_all':int(row[6]),'initial':safe(row[10]),'adviser':safe(row[14]),'final':safe(row[17]),'gap':safe(wrap(row[14]-row[10])),'revision':safe(wrap(row[17]-row[10]))})
    first=[]
    for r in p3[:3]:
        g=float(wrap(r[14]-r[10])); y=float(wrap(r[17]-r[10]))
        first.append({'trial':int(r[5]),'gap_degrees':g,'revision_degrees':y,'signed_proportional_revision':y/g,'supplied_influence':safe(r[21]),'prior_adviser_error':None if len(first)==0 else safe(p3[len(first)-1,14])})
    acc={}
    for label,ei,ai in [('initial',10,12),('adviser',14,16),('final',17,18)]:
        ok=np.isfinite(a[:,ei])&np.isfinite(a[:,ai])
        acc[label]={'finite_pairs':int(ok.sum()),'mismatches':int(np.sum((np.abs(a[ok,ei])<=10)!=(a[ok,ai]==1)))}
    counts={'initial':int(np.sum(~np.isfinite(a[:,10]))),'final':int(np.sum(~np.isfinite(a[:,17]))),'unscorable_primary_person13':int(np.sum((p13[:,5]>=19)&(~np.isfinite(p13[:,10])|~np.isfinite(p13[:,17]))))}
    np.savez_compressed(HERE/'raw_reconstructed.npz',rows=a,headers=np.asarray(headers))
    out={'timestamp_utc':now(),'original_sha256':pin,'original_bytes':len(buf),'sheet_decoded_bytes':z.getinfo('xl/worksheets/sheet1.xml').file_size,'shared_strings_bytes':len(sb),'shape':list(a.shape),'headers':headers,'cell_type_counts':typed_counts,'shared_strings_4_12':{str(k):strings[k] for k in (4,12)},'participant3_first_trials':first,'participant13_missing':missing,'missing_counts':counts,'finite_accuracy_checks':acc,'nonfinite_typed_cells':exceptional,'exposure':'All 47x378 rows/all 30 columns decoded by this independent review; already-consumed observations. No new source/holdout.','conservative_first_stage_scientific_read_allowance_bytes':40000000,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'skill_external_path_read':'Blocked by existing lab hook; no bytes read or permission changed.'}
    save('FIRST_CALCULATION.json',out)
    print(json.dumps({k:out[k] for k in ('timestamp_utc','original_sha256','shape','shared_strings_4_12','participant3_first_trials','participant13_missing','missing_counts','finite_accuracy_checks','peak_rss_bytes')},indent=2))

def cw(x): return (np.asarray(x)+1.)%2.-1.

def exclusive(values):
    v=np.asarray(values)
    return np.concatenate((np.zeros_like(v[:1]),np.cumsum(v,axis=0)[:-1]),axis=0)

def moments(error,confidence,accuracy,beta=-2.):
    """Vectorized exclusive cumulative sums; recency updated component by component."""
    n=len(error); count=np.arange(n)+4.
    valid=np.isfinite(error)
    squares=np.where(valid,error*error,0.)
    adjusted=squares*np.exp(-beta*(confidence-.5))
    na=4.+exclusive(valid.astype(float))
    a=(2.+exclusive(accuracy))/count
    c=(2.+exclusive(confidence))/count
    mse=(3600.+exclusive(squares))/na/32400.
    adj=(3600.+exclusive(adjusted))/na/32400.
    cov=(1.+exclusive(accuracy*confidence))/count-a*c
    ew=np.empty((n,3)); state=np.array([.5,900.,900.])
    for t in range(n):
        ew[t]=state
        state[0]=.8*state[0]+.2*accuracy[t]
        if valid[t]: state[1:]=.8*state[1:]+.2*np.array([squares[t],adjusted[t]])
    ew[:,1:]/=32400.
    return np.column_stack((a,c,mse,adj,cov,ew))

def build_features(a,beta=(-2.,-2.)):
    n=len(a); pid=a[:,0].astype(int); session=a[:,2].astype(int)
    block=a[:,3].astype(int); trial=a[:,5].astype(int)
    cs=a[:,11]/100.; ca=a[:,15]/100.
    g=wrap(a[:,14]-a[:,10])/180.; y=wrap(a[:,17]-a[:,10])/180.
    av=np.empty((n,8)); sv=np.empty((n,8)); slopes=np.empty((n,3))
    for person in np.unique(pid):
        pp=np.flatnonzero(pid==person)
        assert len(pp)==378
        assert np.array_equal(a[pp,6],np.arange(1,379))
        assert np.array_equal(a[pp,5],np.tile(np.arange(1,55),7))
        for ss in np.unique(session[pp]):
            ix=pp[session[pp]==ss]
            sv[ix]=moments(a[ix,10],cs[ix],a[ix,12],beta[0])
            ok=np.isfinite(g[ix])&np.isfinite(y[ix]); gg=np.where(ok,g[ix]**2,0.); gy=np.where(ok,g[ix]*y[ix],0.)
            slopes[ix,1]=(.25/3+exclusive(gy))/(.25+exclusive(gg))
            ey=.25/3; ex=.25
            for t,ii in enumerate(ix):
                slopes[ii,2]=ey/ex
                if ok[t]: ey=.8*ey+.2*gy[t]; ex=.8*ex+.2*gg[t]
        for bb in np.unique(block[pp]):
            ix=pp[block[pp]==bb]
            av[ix]=moments(a[ix,14],ca[ix],a[ix,16],beta[1])
            ok=np.isfinite(g[ix])&np.isfinite(y[ix]); gg=np.where(ok,g[ix]**2,0.); gy=np.where(ok,g[ix]*y[ix],0.)
            slopes[ix,0]=(.25/3+exclusive(gy))/(.25+exclusive(gg))
    slopes=np.clip(slopes,-2,2)
    rt=np.log1p(a[:,13]); ag=np.abs(g)
    cur=np.column_stack((np.ones(n),ag,ag*ag,cs,ca,cs*cs,ca*ca,cs*ca,rt,rt*cs,trial/54.,block/7.,session-1))
    history=np.column_stack((av,sv,(av-sv)*(ca-cs)[:,None],slopes,ca*av[:,1],cs*sv[:,1]))
    vs=sv[:,3]*np.exp(beta[0]*(cs-.5)); va=av[:,3]*np.exp(beta[1]*(ca-.5))
    X=g[:,None]*np.column_stack((cur,history,vs/(vs+va)))
    return {'X':X,'y':y,'id':pid,'trial':trial,'block':block,'gap':g}

def subset(d,mask): return {k:v[mask] for k,v in d.items()}
def primary(d):
    return subset(d,(d['trial']>=19)&np.isfinite(d['y'])&np.isfinite(d['X']).all(axis=1))

PENALTIES=np.array([.0001,.001,.01,.1,1.])
DIMS={'B':13,'H':42,'P':43}

class Ridge:
    """Independent eigensystem ridge solves, supporting multiple label vectors.

    Raw per-person sums are computed once. Weighted source draws drop every copy
    of the same identity in its validation fold. All standardization is local
    to that training fold; validation labels never enter its fitted intercept.
    """
    def __init__(self,d,dim):
        self.x=d['X'][:,:dim]; self.people=np.unique(d['id']); self.dim=dim
        self.groups=[np.flatnonzero(d['id']==p) for p in self.people]
        self.n=np.array([len(ix) for ix in self.groups],float)
        self.s1=np.stack([self.x[ix].sum(axis=0) for ix in self.groups])
        self.s2=np.stack([np.einsum('ni,nj->ij',self.x[ix],self.x[ix],optimize=False) for ix in self.groups])

    def labels(self,y):
        y=np.asarray(y)
        if y.ndim==1: y=y[:,None]
        return y,np.stack([y[ix].sum(axis=0) for ix in self.groups]),np.stack([np.einsum('ni,nk->ik',self.x[ix],y[ix],optimize=False) for ix in self.groups])

    def system(self,w,ys,xy):
        n=float(w@self.n)
        mx=np.einsum('g,gd->d',w,self.s1)/n
        cov=np.einsum('g,gij->ij',w,self.s2)/n-np.outer(mx,mx)
        var=np.diag(cov); scale=np.where(var<1e-14,1.,np.sqrt(np.maximum(var,1e-14)))
        gram=cov/np.outer(scale,scale); gram=(gram+gram.T)*.5
        values,vectors=np.linalg.eigh(gram)
        my=np.einsum('g,gk->k',w,ys)/n
        rhs=(np.einsum('g,gdk->dk',w,xy)/n-mx[:,None]*my)/scale[:,None]
        return mx,scale,values,vectors,my,vectors.T@rhs

    def solve(self,system,penalty):
        mx,scale,values,vectors,my,rhs=system
        b=(vectors@(rhs/(values[:,None]+penalty)))/scale[:,None]
        return b,my-mx@b

    def fit(self,y,w=None):
        y,ys,xy=self.labels(y); k=y.shape[1]
        if w is None: w=np.ones(len(self.people))
        cv=np.zeros((5,k)); folds=0
        for j,ix in enumerate(self.groups):
            if w[j]==0: continue
            tw=w.copy(); tw[j]=0.
            system=self.system(tw,ys,xy)
            for ll,lam in enumerate(PENALTIES):
                b,c=self.solve(system,lam)
                prediction=np.clip(self.x[ix]@b+c,-1,1)
                cv[ll]+=w[j]*np.mean(cw(y[ix]-prediction)**2,axis=0)
                folds+=1
        cv/=w.sum()
        chosen=np.max(np.where(cv<=cv.min(axis=0)+1e-12,np.arange(5)[:,None],-1),axis=0)
        system=self.system(w,ys,xy)
        coef=np.empty((self.dim,k)); intercept=np.empty(k)
        for ll in np.unique(chosen):
            b,c=self.solve(system,PENALTIES[ll]); use=chosen==ll
            coef[:,use]=b[:,use]; intercept[use]=c[use]
        return {'coef':coef,'intercept':intercept,'penalty':PENALTIES[chosen],'cv':cv*32400.,'fold_penalty_solves':folds}

    def fixed(self,y,penalty):
        _,ys,xy=self.labels(y)
        b,c=self.solve(self.system(np.ones(len(self.people)),ys,xy),penalty)
        return {'coef':b,'intercept':c,'penalty':np.array([penalty])}

def predict(fit,x): return np.clip(x[:,:fit['coef'].shape[0]]@fit['coef']+fit['intercept'],-1,1)
def fit_json(f):
    return {k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in f.items()}

def metrics(d,pred,y=None):
    if y is None: y=d['y']
    if np.asarray(y).ndim==1: y=y[:,None]
    out={}
    for name,p in pred.items():
        if p.ndim==1: p=p[:,None]
        error=cw(y-p)*180.
        out[name]={key:np.stack([value[d['id']==i].mean(axis=0) for i in np.unique(d['id'])]) for key,value in [('mse',error**2),('mae',np.abs(error)),('directed_bias',error*np.sign(d['gap'])[:,None])]}
    return out

def decision(met,draws,coef,col=0):
    ans={}; ok=True
    for name in ('B','H'):
        p=met['P']['mse'][:,col]; b=met[name]['mse'][:,col]
        point=1.-p.mean()/b.mean(); gains=1.-p[draws].mean(axis=1)/b[draws].mean(axis=1)
        lo,hi=np.percentile(gains,[2.5,97.5]); passed=point>=.05 and lo>0
        ans[name]={'gain':float(point),'interval95':[float(lo),float(hi)],'pass':bool(passed)}; ok=ok and passed
    bias=met['P']['directed_bias'][:,col]; lo,hi=np.percentile(bias[draws].mean(axis=1),[2.5,97.5])
    ans['P_calibration']={'directed_bias_degrees':float(bias.mean()),'interval95':[float(lo),float(hi)],'pass':bool(lo>=-3 and hi<=3)}
    ans['positive_precision_coefficient']=bool(coef>0)
    ans['joint_pass']=bool(ok and ans['P_calibration']['pass'] and coef>0)
    return ans

def read_npz(name):
    b=(AUTHOR/name).read_bytes()
    with zipfile.ZipFile(io.BytesIO(b)) as z: decoded=sum(v.file_size for v in z.infolist())
    with np.load(io.BytesIO(b),allow_pickle=False) as z: arrays={k:z[k] for k in z.files}
    return arrays,{'path':str(AUTHOR/name),'bytes':len(b),'decoded_bytes':decoded,'sha256':hashlib.sha256(b).hexdigest()}

def array_diff(a,b):
    assert a.shape==b.shape
    same_missing=np.array_equal(np.isnan(a),np.isnan(b))
    finite=np.isfinite(a)&np.isfinite(b)
    return {'shape':list(a.shape),'same_missing':same_missing,'max_abs_difference':float(np.max(np.abs(a[finite]-b[finite]))) if finite.any() else 0.}

def run_main():
    check_time()
    with np.load(HERE/'raw_reconstructed.npz') as z: a=z['rows']
    gate=json.loads((AUTHOR/'DESIGN_GATE.json').read_text())
    d=build_features(a); sfull=subset(d,np.isin(d['id'],gate['source_people'])); efull=subset(d,np.isin(d['id'],gate['evaluation_people']))
    s=primary(sfull); e=primary(efull)
    assert len(s['y'])==6048 and len(e['y'])==5794
    comparisons={}; input_refs={}; caches={}
    for file,derived in [('source.npz',sfull),('evaluation_features.npz',efull),('evaluation_scored.npz',efull)]:
        cache,ref=read_npz(file); caches[file]=cache; input_refs[file]=ref
        comparisons[file]={k:array_diff(derived[k],v) for k,v in cache.items() if k in derived}
        assert all(q['same_missing'] and q['max_abs_difference']<2e-12 for q in comparisons[file].values())
    chronology=[]
    for person in np.unique(d['id']):
        pp=a[a[:,0]==person]
        chronology.append({'person':int(person),'rows':len(pp),'sessions':[{'session':int(ss),'rows':int(np.sum(pp[:,2]==ss)),'blocks':np.unique(pp[pp[:,2]==ss,3]).astype(int).tolist()} for ss in np.unique(pp[:,2])]})
    # Common correct-direction rotation preserves current gap and revision. Feedback
    # errors themselves stay relative to truth and therefore remain unchanged.
    reference_errors=[]
    for angle in (17.,179.,-113.):
        gg=wrap(wrap(a[:,14]+angle)-wrap(a[:,10]+angle))/180.
        yy=wrap(wrap(a[:,17]+angle)-wrap(a[:,10]+angle))/180.
        reference_errors.extend([array_diff(gg,d['gap'])['max_abs_difference'],array_diff(yy,d['y'])['max_abs_difference']])
    # Current final/correctness/feedback perturbation cannot change its own X.
    # Future perturbations must not alter any prefix. Compare complete features.
    probes=[]
    for person,alltrial in [(3,42),(13,359),(13,362),(50,190)]:
        raw=a[a[:,0]==person].copy(); ii=alltrial-1
        base=build_features(raw)
        changed=raw.copy(); changed[ii,17]=77.; changed[ii,18]=0
        xx=build_features(changed)
        final_diff=array_diff(base['X'][ii:ii+1],xx['X'][ii:ii+1])
        changed=raw.copy(); changed[ii,12]=1-changed[ii,12]; changed[ii,16]=1-changed[ii,16]
        xx=build_features(changed); current_feedback=array_diff(base['X'][ii:ii+1],xx['X'][ii:ii+1])
        changed=raw.copy(); changed[ii+1:,10]=42.; changed[ii+1:,14]=-65.; changed[ii+1:,17]=112.; changed[ii+1:,11]=33.; changed[ii+1:,15]=75.
        xx=build_features(changed); suffix=array_diff(base['X'][:ii+1],xx['X'][:ii+1])
        probes.append({'person':person,'trial_all':alltrial,'current_final_invariance':final_diff,'current_feedback_invariance':current_feedback,'future_suffix_invariance':suffix})
    save('RAW_FEATURE_AUDIT.json',{'timestamp_utc':now(),'comparisons':comparisons,'chronology':chronology,'reference_rotation_max_error':max(reference_errors),'information_timing_probes':probes,'primary_source_rows':len(s['y']),'primary_evaluation_rows':len(e['y']),'input_refs':input_refs,'construction':'Original typed rows decoded independently; exclusive prefix sums by person/session or person/block; recency/behavior histories independent implementation. No author imports.'})
    print('Original complete history/feature reconstruction passed',flush=True)
    engines={name:Ridge(s,dim) for name,dim in DIMS.items()}
    fits={name:engine.fit(s['y']) for name,engine in engines.items()}
    fweight=float(np.sum(s['gap']*s['y'])/np.sum(s['gap']**2))
    predictions={name:predict(f,e['X']) for name,f in fits.items()}
    predictions.update(N=np.zeros((len(e['y']),1)),F=np.clip(fweight*e['gap'][:,None],-1,1))
    savedfits=json.loads((AUTHOR/'SOURCE_FITS.json').read_text())
    savedpred,ref=read_npz('evaluation_predictions.npz'); input_refs['evaluation_predictions.npz']=ref
    source_compare={}; direct=[]
    emask=(efull['trial']>=19)&np.isfinite(efull['y'])&np.isfinite(efull['X']).all(axis=1)
    for name,f in fits.items():
        old=savedfits['models'][name]
        source_compare[name]={'selected_penalty':float(f['penalty'][0]),'original_selected_penalty':old['penalty'],'coefficient_max_difference':float(np.max(np.abs(f['coef'][:,0]-old['coef']))),'intercept_difference':float(abs(f['intercept'][0]-old['intercept'])),'cv_loss_max_difference_degrees2':float(np.max(np.abs(f['cv'][:,0]-old['cv_mse_degrees2']))),'frozen_forecast_max_difference_normalized':array_diff(predictions[name][:,0],savedpred[name][emask])['max_abs_difference']}
        assert f['penalty'][0]==old['penalty']
        assert source_compare[name]['frozen_forecast_max_difference_normalized']<1e-10
        # Independent augmented least squares reference for each final source fit.
        x=s['X'][:,:DIMS[name]]; mx=x.mean(axis=0); scale=x.std(axis=0); scale=np.where(scale<1e-7,1.,scale)
        zz=(x-mx)/scale; yy=s['y']; my=yy.mean(); lam=f['penalty'][0]
        aug=np.vstack((zz,np.sqrt(len(x)*lam)*np.eye(DIMS[name])))
        target=np.concatenate((yy-my,np.zeros(DIMS[name])))
        beta=np.linalg.lstsq(aug,target,rcond=None)[0]/scale
        direct.append({'name':name,'coefficient_difference_vs_augmented_lstsq':float(np.max(np.abs(beta-f['coef'][:,0]))),'intercept_difference':float(abs(my-mx@beta-f['intercept'][0]))})
    fitrecord={'timestamp_utc':now(),'source_people':gate['source_people'],'source_rows':len(s['y']),'fixed_weight':fweight,'models':{k:fit_json(v) for k,v in fits.items()},'comparison_to_original':source_compare,'augmented_lstsq_final_fit_checks':direct,'selection_scope':'All 360 leave-one-source-person/penalty fits and 3 final source fits independently solved. Eigensystem solver, no author imports.'}
    save('SOURCE_FIT_AUDIT.json',fitrecord)
    rng=np.random.default_rng(611013); draws=rng.integers(0,23,(5000,23))
    met=metrics(e,predictions); dec=decision(met,draws,fits['P']['coef'][-1,0])
    loo=[]
    for j,person in enumerate(np.unique(e['id'])):
        mm={name:{key:np.delete(value,j,axis=0) for key,value in info.items()} for name,info in met.items()}
        dd=rng.integers(0,22,(5000,22)); loo.append({'deleted':int(person),'decision':decision(mm,dd,fits['P']['coef'][-1,0])})
    original_scores=json.loads((AUTHOR/'SCORES.json').read_text())
    metricdiff=max(float(np.max(np.abs(value[:,0]-original_scores['person_metrics'][name][key]))) for name,info in met.items() for key,value in info.items())
    fullpred={k:predict(v,efull['X']) for k,v in fits.items()}; fullpred.update(N=np.zeros((len(efull['y']),1)),F=np.clip(fweight*efull['gap'][:,None],-1,1))
    observed=np.isfinite(efull['y'])&np.isfinite(efull['X']).all(axis=1)
    allmet=metrics(subset(efull,observed),{k:v[observed] for k,v in fullpred.items()})
    score_record={'timestamp_utc':now(),'people':np.unique(e['id']).tolist(),'rows':len(e['y']),'summary':{name:{key:float(value.mean()) for key,value in info.items()} for name,info in met.items()},'primary':dec,'leave_one_person_out':loo,'person_metric_max_difference_vs_original':metricdiff,'all54_summary':{name:{key:float(value.mean()) for key,value in info.items()} for name,info in allmet.items()},'person_metrics':{name:{key:value[:,0].tolist() for key,value in info.items()} for name,info in met.items()}}
    save('SCORE_AUDIT.json',score_record)
    np.savez_compressed(HERE/'reconstructed_forecasts.npz',id=e['id'],trial=e['trial'],block=e['block'],y=e['y'],**{k:v[:,0] for k,v in predictions.items()})
    print(json.dumps({'stage':'source fit and primary scores','time':now(),'comparison':source_compare,'decision':dec,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}),flush=True)
    controls_audit(s,e,engines,fits)
    stability_audit(s,e,engines)
    contrary(a,gate,s,e,fits,draws)
    # Read each freeze input once. Already admitted NPZ hashes are reused.
    pin_checks={}; rawpins={}
    for freeze in ('FREEZE.json','FREEZE_v2.json','PREDICTIONS_PIN.json'):
        buf=(AUTHOR/freeze).read_bytes(); rawpins[freeze]=hashlib.sha256(buf).hexdigest()
        obj=json.loads(buf)
        if 'files' not in obj: continue
        for name,h in obj['files'].items():
            if name in pin_checks: assert pin_checks[name]['expected']==h; continue
            if name in input_refs: actual=input_refs[name]['sha256']; size=input_refs[name]['bytes']
            else:
                data=(AUTHOR/name).read_bytes(); actual=hashlib.sha256(data).hexdigest(); size=len(data)
            pin_checks[name]={'expected':h,'actual':actual,'match':actual==h,'bytes':size}
    ppin=json.loads((AUTHOR/'PREDICTIONS_PIN.json').read_text())
    assert input_refs['evaluation_predictions.npz']['sha256']==ppin['prediction_sha256']
    assert input_refs['evaluation_features.npz']['sha256']==ppin['feature_sha256']
    assert all(v['match'] for v in pin_checks.values())
    save('FINAL_AUDIT.json',{'timestamp_utc':now(),'freeze_inputs':pin_checks,'freeze_file_sha256':rawpins,'prediction_and_feature_pins_match':True,'input_refs':input_refs,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'jobs_remaining':0,'original_resource_limitation_preserved':'Author conservative330MB versus300MB cap/compliance UNCERTIFIED; exactfailedprefix/logical/physicalIO unknown. Separate review does not repair it.'})
    print(json.dumps({'stage':'finished','time':now(),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}),flush=True)

def controls_audit(s,e,engines,fits):
    check_time()
    sm=predict(fits['H'],s['X'])[:,0]; em=predict(fits['H'],e['X'])[:,0]
    projection=engines['H'].fixed(s['X'][:,-1],.0001)
    zs=s['X'][:,-1]-predict(projection,s['X'])[:,0]
    ze=e['X'][:,-1]-predict(projection,e['X'])[:,0]
    sigma=float(np.sqrt(np.mean(cw(s['y']-sm)**2)))
    gamma=math.sqrt(sigma**2*.75*.2/.8/np.mean(zs**2))
    rng=np.random.default_rng(611015); dd=rng.integers(0,23,(5000,23))
    sy=np.empty((len(sm),200)); ey=np.empty((len(em),200)); oracle=[]
    for k in range(200):
        kind='signal' if k<100 else 'null'
        ms=np.clip(sm+(gamma*zs if kind=='signal' else 0.),-1,1)
        me=np.clip(em+(gamma*ze if kind=='signal' else 0.),-1,1)
        offsets=rng.normal(size=24); ino=np.searchsorted(np.unique(s['id']),s['id'])
        sn=sigma*(.5*offsets[ino]*s['gap']+math.sqrt(.75)*rng.normal(size=len(sm)))
        offsets=rng.normal(size=23); ino=np.searchsorted(np.unique(e['id']),e['id'])
        en=sigma*(.5*offsets[ino]*e['gap']+math.sqrt(.75)*rng.normal(size=len(em)))
        sy[:,k]=np.clip(ms+sn,-1,1); ey[:,k]=np.clip(me+en,-1,1)
        oracle.append(1.-np.mean(cw(ey[:,k]-me)**2)/np.mean(cw(ey[:,k]-em)**2))
    cf={name:eng.fit(sy) for name,eng in engines.items()}
    cp={name:predict(f,e['X']) for name,f in cf.items()}
    mm=metrics(e,cp,y=ey)
    original=json.loads((AUTHOR/'CONTROLS.json').read_text()); rows=[]; differences=[]; decision_mismatch=0; penalty_mismatch=0
    for k in range(200):
        if k%20==0: check_time()
        dec=decision(mm,dd,cf['P']['coef'][-1,k],k)
        old=original['replicates'][k]; penalties={name:float(f['penalty'][k]) for name,f in cf.items()}
        decision_mismatch+=int(dec['joint_pass']!=old['decision']['joint_pass'])
        penalty_mismatch+=int(penalties!=old['penalties'])
        for name in ('B','H'):
            differences.extend([abs(dec[name]['gain']-old['decision'][name]['gain']),*np.abs(np.array(dec[name]['interval95'])-old['decision'][name]['interval95']).tolist()])
        rows.append({'kind':'signal' if k<100 else 'null','rep':k%100,'decision':dec,'oracle_gain_vs_H_mean':float(oracle[k]),'penalties':penalties})
    examples={}
    for kind,k in [('signal',0),('null',100)]:
        saved,ref=read_npz('CONTROL_EXAMPLE_'+kind+'.npz')
        dif={'source_labels':array_diff(sy[:,k],saved['source_y']),'evaluation_labels':array_diff(ey[:,k],saved['evaluation_y'])}
        for name in DIMS: dif[name]=array_diff(cp[name][:,k],saved['prediction_'+name])
        examples[kind]={'comparisons':dif,'input_ref':ref}
    counts={kind:sum(row['decision']['joint_pass'] for row in rows if row['kind']==kind) for kind in ('signal','null')}
    out={'timestamp_utc':now(),'scope':'All200 label/noise generators,600 final models/72000 person-penalty fits and complete decisions independently reconstructed. Histories held fixed: not full generative recovery, boundary5% power or interval coverage. Two original full examples independently compared.','sigma':sigma,'gamma':gamma,'counts':counts,'decision_mismatches':decision_mismatch,'penalty_mismatches':penalty_mismatch,'max_gain_interval_scalar_difference':float(max(differences)),'full_examples':examples,'attained_signal_oracle_gain_percentiles':np.percentile(oracle[:100],[2.5,50,97.5]).tolist(),'replicates':rows,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save('CONTROL_AUDIT.json',out)
    print(json.dumps({'stage':'all200 controls','time':now(),'counts':counts,'decision_mismatches':decision_mismatch,'penalty_mismatches':penalty_mismatch,'max_gain_interval_scalar_difference':float(max(differences)),'peak_rss_bytes':out['peak_rss_bytes']}),flush=True)

def stability_audit(s,e,engines):
    check_time(); original=json.loads((AUTHOR/'SOURCE_UNCERTAINTY.json').read_text())
    rng=np.random.default_rng(611014); rows=[]; differences=[]; mismatches=0
    for k in range(100):
        if k%10==0: check_time()
        weights=np.bincount(rng.integers(0,24,24),minlength=24).astype(float)
        ff={name:eng.fit(s['y'],weights) for name,eng in engines.items()}
        pp={name:predict(f,e['X']) for name,f in ff.items()}
        mm=metrics(e,pp); draw=rng.integers(0,23,23)
        row={'rep':k,'source_multiplicities':weights.astype(int).tolist(),'penalties':{name:float(f['penalty'][0]) for name,f in ff.items()},'precision_coefficient':float(ff['P']['coef'][-1,0])}
        for name in ('B','H'):
            row['gain_'+name]=float(1-mm['P']['mse'].mean()/mm[name]['mse'].mean())
            row['paired_gain_'+name]=float(1-mm['P']['mse'][draw].mean()/mm[name]['mse'][draw].mean())
        old=original['replicates'][k]
        assert row['source_multiplicities']==old['source_multiplicities']
        mismatches+=int(row['penalties']!=old['penalties'])
        differences.extend(abs(row[key]-old[key]) for key in ('gain_B','gain_H','paired_gain_B','paired_gain_H','precision_coefficient'))
        rows.append(row)
    out={'timestamp_utc':now(),'scope':'All100 source-person resamples independently refit with duplicate identity folds excluded together; every draw repeats local standardization and five-penalty selection. Finite perturbations, not coverage or biological equality.','penalty_mismatches':mismatches,'max_gain_coefficient_scalar_difference':float(max(differences)),'summary':{key:np.percentile([r[key] for r in rows],[2.5,50,97.5]).tolist() for key in ('gain_B','gain_H','paired_gain_B','paired_gain_H')},'reach5percent_vs_H':sum(r['gain_H']>=.05 for r in rows),'max_gain_H':max(r['gain_H'] for r in rows),'replicates':rows,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save('SOURCE_STABILITY_AUDIT.json',out)
    print(json.dumps({'stage':'all100 source resamples','time':now(),'summary':out['summary'],'reach5percent_vs_H':out['reach5percent_vs_H'],'penalty_mismatches':mismatches,'max_difference':out['max_gain_coefficient_scalar_difference']}),flush=True)

def calibrated_beta(a,people):
    r=a[np.isin(a[:,0],people)]; results=[]
    for channel,ei,ci,gi in [('self',10,11,2),('adviser',14,15,3)]:
        groups=[]
        for person in np.unique(r[:,0]):
            for group in np.unique(r[r[:,0]==person,gi]):
                rows=r[(r[:,0]==person)&(r[:,gi]==group)]
                ok=np.isfinite(rows[:,ei])&np.isfinite(rows[:,ci])
                c=rows[ok,ci]/100.-.5; e2=rows[ok,ei]**2
                groups.append((c,e2))
        def derivative(b):
            total=0.
            for c,e2 in groups:
                v=e2*np.exp(-b*c); den=max(float(v.sum()),1e-12*len(c))
                total+=c.sum()-len(c)*float(np.sum(c*v))/den
            return total
        lo=-8.; hi=0.; dl=derivative(lo); dh=derivative(hi)
        if dl>=0: b=lo
        elif dh<=0: b=hi
        else:
            for _ in range(64):
                mid=(lo+hi)/2
                if derivative(mid)>0: hi=mid
                else: lo=mid
            b=(lo+hi)/2
        floor=sum(np.mean(e2*np.exp(-b*c))<1e-12 for c,e2 in groups)
        loss=sum(len(c)*math.log(max(float(np.mean(e2*np.exp(-b*c))),1e-12))+b*c.sum() for c,e2 in groups)
        results.append({'channel':channel,'beta':b,'group_count':len(groups),'observations':sum(len(c) for c,e2 in groups),'profile_loss':float(loss),'derivative_at_selected':derivative(b),'floored_groups':int(floor),'boundary':bool(b in (-8.,0.))})
    return tuple(row['beta'] for row in results),results

def direct_fit_at_lambda(x,y,lam):
    mx=x.mean(axis=0); my=y.mean(); scale=x.std(axis=0); scale=np.where(scale<1e-7,1.,scale)
    z=(x-mx)/scale
    gram=np.einsum('ni,nj->ij',z,z,optimize=False)/len(x)
    rhs=np.einsum('ni,n->i',z,y-my,optimize=False)/len(x)
    values,vectors=np.linalg.eigh((gram+gram.T)/2.)
    b=(vectors@((vectors.T@rhs)/(values+lam)))/scale
    return {'coef':b[:,None],'intercept':np.array([my-mx@b]),'penalty':np.array([lam])}

def contrary(a,gate,s,e,original_fits,draws):
    check_time(); people=gate['source_people']; folds=[]; losses={k:np.zeros(5) for k in ('H','P')}
    for person in people:
        check_time(); training=[p for p in people if p!=person]
        beta,cal=calibrated_beta(a,training)
        raw=a[np.isin(a[:,0],people)]
        data=primary(build_features(raw,beta)); train=subset(data,data['id']!=person); val=subset(data,data['id']==person)
        fold={'deleted':person,'calibration':cal,'cv_losses_degrees2':{}}
        for name in ('H','P'):
            errors=[]
            for lam in PENALTIES:
                f=direct_fit_at_lambda(train['X'][:,:DIMS[name]],train['y'],lam)
                pr=predict(f,val['X'])[:,0]
                errors.append(float(np.mean(cw(val['y']-pr)**2))*32400.)
            losses[name]+=np.array(errors)/24.
            fold['cv_losses_degrees2'][name]=errors
        folds.append(fold)
    beta,cal=calibrated_beta(a,people)
    changed=build_features(a,beta); ss=primary(subset(changed,np.isin(changed['id'],people))); ee=primary(subset(changed,np.isin(changed['id'],gate['evaluation_people'])))
    ff={'B':original_fits['B']}; pred={'B':predict(ff['B'],ee['X'])}
    for name in ('H','P'):
        best=losses[name].min(); selected=np.flatnonzero(losses[name]<=best+32400e-12)[-1]
        ff[name]=direct_fit_at_lambda(ss['X'][:,:DIMS[name]],ss['y'],PENALTIES[selected])
        ff[name]['cv_mse_degrees2']=losses[name]
        pred[name]=predict(ff[name],ee['X'])
    # Save changes and forecast bytes BEFORE evaluating their held-person losses.
    np.savez_compressed(HERE/'contrary_forecasts.npz',id=ee['id'],trial=ee['trial'],block=ee['block'],**{k:v[:,0] for k,v in pred.items()})
    pbytes=(HERE/'contrary_forecasts.npz').read_bytes()
    plan=(HERE/'CONTRARY_PLAN.md').read_bytes(); code=Path(__file__).read_bytes()
    frozen={'timestamp_utc':now(),'plan_sha256':hashlib.sha256(plan).hexdigest(),'code_sha256':hashlib.sha256(code).hexdigest(),'predictions_sha256':hashlib.sha256(pbytes).hexdigest(),'prediction_bytes':len(pbytes),'source_people':people,'calibration':cal,'folds':folds,'models':{k:fit_json(v) for k,v in ff.items()},'status':'Predictions and calibration frozen before own changed-model scoring; all people consumed/postvalidation.'}
    save('CONTRARY_FREEZE.json',frozen)
    met=metrics(ee,pred); dec=decision(met,draws,ff['P']['coef'][-1,0])
    out={'timestamp_utc':now(),'scope':'ONE source-only confidence/error-map calibration, applied consistently to both H and P. Nested re-estimation within all24 source folds; no evaluation tuning, changed score/gate/cohort. Postvalidation on consumed people.','calibration':cal,'selected_penalties':{k:float(v['penalty'][0]) for k,v in ff.items()},'summary':{name:{key:float(value.mean()) for key,value in info.items()} for name,info in met.items()},'primary_rule_applied_without_change':dec,'calibration_folds':len(folds),'source_person_penalty_fits':24*5*2,'person_metrics':{name:{key:value[:,0].tolist() for key,value in info.items()} for name,info in met.items()},'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save('CONTRARY.json',out)
    print(json.dumps({'stage':'ONE confidence calibration contrary','time':now(),'calibration':cal,'penalties':out['selected_penalties'],'summary':out['summary'],'decision':dec}),flush=True)

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='main': run_main()
    else: initial()
