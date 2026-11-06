"""Bounded, offline original-record adviser revision forecast. No downloaded code."""
import os
for _key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_key]='1'
import pathlib, json, sys, hashlib, datetime, resource, zipfile, math, argparse
import xml.etree.ElementTree as ET
import numpy as np

ROOT=pathlib.Path(__file__).resolve().parent
CFG=json.loads((ROOT/'config.json').read_text())
GATE=json.loads((ROOT/'DESIGN_GATE.json').read_text())
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
NOW=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
wrap=lambda a:(a+1.0)%2.0-1.0
wrap_deg=lambda a:(a+180.0)%360.0-180.0
rho=lambda c:np.exp(-2.0*(c-.5))
BASE_NAMES=['gap','gap_abs_gap','gap_abs_gap2','gap_self_conf','gap_adviser_conf','gap_self_conf2','gap_adviser_conf2','gap_conf_product','gap_logrt','gap_logrt_self_conf','gap_trial_fraction','gap_block_fraction','gap_second_session']
MOMENT_NAMES=['accuracy','confidence','mse','adjusted_mse','conf_accuracy_cov','ew_accuracy','ew_mse','ew_adjusted_mse']
HISTORY_NAMES=['gap_'+who+'_'+name for who in ('adviser','self') for name in MOMENT_NAMES]+['gap_conf_diff_'+name+'_diff' for name in MOMENT_NAMES]+['gap_own_block_slope','gap_own_session_slope','gap_own_ew_slope','gap_adviser_conf_past_mean','gap_self_conf_past_mean']
NAMES=BASE_NAMES+HISTORY_NAMES+['gap_precision_ratio']
DIMS={'B':len(BASE_NAMES),'H':len(NAMES)-1,'P':len(NAMES)}

def savej(path,obj):
    path.write_text(json.dumps(obj,indent=2,allow_nan=False))

def resource_record(out,name,extra=None):
    rec={'timestamp_utc':NOW(),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'python':sys.version,'numpy':np.__version__,'numerical_thread_env':{k:os.environ[k] for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')}}
    if extra:rec.update(extra)
    savej(out/(name+'_RUN.json'),rec)

def rows(selected):
    """Parse all XML; convert only selected people's original fields."""
    with zipfile.ZipFile(ROOT/'dataset_exp1.xlsx') as z:
        assert z.getinfo('xl/worksheets/sheet1.xml').file_size==21241768
        with z.open('xl/worksheets/sheet1.xml') as f:
            for _,e in ET.iterparse(f,events=('end',)):
                if not e.tag.endswith('}row'):continue
                if e.attrib.get('r')=='1':e.clear();continue
                d={}
                for c in e.findall('m:c',NS):
                    v=c.find('m:v',NS)
                    if v is not None:d[''.join(x for x in c.attrib['r'] if x.isalpha())]=v.text
                if 'A' not in d:e.clear();continue
                pid=int(float(d['A']))
                if pid in selected:
                    # Do not convert precomputed influence/optimality/delta fields.
                    v={k:float(d[k]) for k in ('A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S')}
                    assert all(math.isfinite(x) for x in v.values())
                    assert 0<=v['L']<=100 and 0<=v['P']<=100 and v['N']>=0
                    assert max(abs(v[k]) for k in ('K','O','R'))<=180
                    yield v
                e.clear()

class Moments:
    def __init__(self):
        self.n=0;self.acc=0.;self.c=0.;self.e2=0.;self.adj=0.;self.cc=0.
        self.ew=np.array([.5,900.,900.])
    def vector(self):
        n=4+self.n;a=(2+self.acc)/n;c=(2+self.c)/n
        return np.array([a,c,(3600+self.e2)/n/32400,(3600+self.adj)/n/32400,(1+self.cc)/n-c*a,self.ew[0],self.ew[1]/32400,self.ew[2]/32400])
    def update(self,error,c):
        a=float(abs(error)<=10);sq=error*error;adj=sq/float(rho(c))
        self.n+=1;self.acc+=a;self.c+=c;self.e2+=sq;self.adj+=adj;self.cc+=c*a
        self.ew=.8*self.ew+.2*np.array([a,sq,adj])

class History:
    def __init__(self):
        self.session=None;self.block=None
    def begin(self,row):
        if self.session!=row['C']:
            self.self=Moments();self.sy=.25/3;self.sx=.25;self.ey=.25/3;self.ex=.25;self.session=row['C']
        if self.block!=row['D']:
            self.adviser=Moments();self.by=.25/3;self.bx=.25;self.block=row['D']
    def feature(self,row):
        self.begin(row)
        g=wrap_deg(row['O']-row['K'])/180.;a=abs(g);cs=row['L']/100;ca=row['P']/100;rt=math.log1p(row['N'])
        cur=np.array([1,a,a*a,cs,ca,cs*cs,ca*ca,cs*ca,rt,rt*cs,row['F']/54,row['D']/7,row['C']-1])
        av=self.adviser.vector();sv=self.self.vector()
        slopes=np.clip(np.array([self.by/self.bx,self.sy/self.sx,self.ey/self.ex]),-2,2)
        h=np.concatenate((av,sv,(av-sv)*(ca-cs),slopes,[ca*av[1],cs*sv[1]]))
        vs=sv[3]*32400*float(rho(cs));va=av[3]*32400*float(rho(ca))
        q=vs/(vs+va)
        x=g*np.concatenate((cur,h,[q]))
        assert len(x)==len(NAMES) and np.all(np.isfinite(x))
        return x,g
    def update(self,row,g):
        y=wrap_deg(row['R']-row['K'])/180.
        self.self.update(row['K'],row['L']/100);self.adviser.update(row['O'],row['P']/100)
        self.by+=g*y;self.bx+=g*g;self.sy+=g*y;self.sx+=g*g
        self.ey=.8*self.ey+.2*g*y;self.ex=.8*self.ex+.2*g*g
        return y

def assemble(selected):
    xs=[];ys=[];ids=[];trials=[];blocks=[];gs=[];hist=None;prev=None;checks=0
    for row in rows(set(selected)):
        pid=int(row['A'])
        if pid!=prev:hist=History();prev=pid;last=0
        assert int(row['G'])==last+1;last=int(row['G'])
        x,g=hist.feature(row) # Always before current final response/feedback update.
        y=hist.update(row,g)
        assert row['M']==(abs(row['K'])<=10) and row['Q']==(abs(row['O'])<=10) and row['S']==(abs(row['R'])<=10)
        checks+=3;xs.append(x);ys.append(y);ids.append(pid);trials.append(int(row['F']));blocks.append(int(row['D']));gs.append(g)
    assert len(xs)==len(selected)*378
    return {'X':np.array(xs),'y':np.array(ys),'id':np.array(ids),'trial':np.array(trials),'block':np.array(blocks),'gap':np.array(gs),'accuracy_checks':checks}

def load_data(path,primary=True):
    with np.load(path) as z:d={k:z[k] for k in z.files}
    if primary:
        m=d['trial']>=CFG['score_first_trial']
        d={k:v[m] for k,v in d.items() if np.ndim(v)>0}
    return d

def predict(model,X):
    return np.clip(np.einsum('ij,j->i',X[:,:model['dim']],np.array(model['coef']),optimize=False)+model['intercept'],-1,1)

class Engine:
    """Sufficient statistics preserve person folds, including duplicate bootstrap copies."""
    def __init__(self,d,dim):
        self.X=d['X'][:,:dim];self.ids=d['id'];self.people=np.unique(self.ids);self.dim=dim
        self.ix=[np.flatnonzero(self.ids==i) for i in self.people]
        self.n=np.array([len(k) for k in self.ix],dtype=float)
        self.sx=np.array([self.X[k].sum(0) for k in self.ix])
        self.xx=np.array([np.einsum('ij,ik->jk',self.X[k],self.X[k],optimize=False) for k in self.ix])
    def labels(self,y):
        return np.array([y[k].sum() for k in self.ix]),np.array([np.einsum('ij,i->j',self.X[k],y[k],optimize=False) for k in self.ix])
    def fixed(self,w):
        n=float(np.dot(w,self.n));mx=np.einsum('i,ij->j',w,self.sx)/n
        xx=np.einsum('i,ijk->jk',w,self.xx)/n
        var=np.diag(xx)-mx*mx;scale=np.sqrt(np.maximum(var,1e-14));scale[var<1e-14]=1.
        gram=(xx-np.outer(mx,mx))/np.outer(scale,scale)
        return n,mx,scale,gram
    def solve(self,sy,xy,w,lam):
        n,mx,scale,gram=self.fixed(w);my=float(np.dot(w,sy)/n)
        rhs=(np.einsum('i,ij->j',w,xy)/n-mx*my)/scale
        beta=np.linalg.solve(gram+lam*np.eye(self.dim),rhs)/scale
        return {'dim':self.dim,'coef':beta.tolist(),'intercept':float(my-np.dot(mx,beta)),'penalty':float(lam)}
    def fit(self,y,w=None):
        if w is None:w=np.ones(len(self.people))
        sy,xy=self.labels(y);loss=[]
        for lam in CFG['penalties']:
            value=0.
            for j,k in enumerate(self.ix):
                if w[j]==0:continue
                train=w.copy();train[j]=0
                model=self.solve(sy,xy,train,lam)
                err=wrap(y[k]-predict(model,self.X[k]))
                value+=w[j]*float(np.mean(err*err))
            loss.append(value/float(w.sum()))
        best=min(loss);chosen=max(j for j,v in enumerate(loss) if v<=best+1e-12)
        model=self.solve(sy,xy,w,CFG['penalties'][chosen]);model['cv_mse_degrees2']=(np.array(loss)*32400).tolist()
        return model

def all_fits(d,y=None,weights=None):
    if y is None:y=d['y']
    return {name:Engine(d,dim).fit(y,weights) for name,dim in DIMS.items()}

def person_metrics(d,pred):
    ids=np.unique(d['id']);out={}
    for name,p in pred.items():
        e=wrap(d['y']-p)*180
        out[name]={'mse':np.array([np.mean(e[d['id']==i]**2) for i in ids]),
          'mae':np.array([np.mean(abs(e[d['id']==i])) for i in ids]),
          'directed_bias':np.array([np.mean((e*np.sign(d['gap']))[d['id']==i]) for i in ids])}
    return ids,out

def rule(metrics,indices,coef):
    result={};ok=True
    for other in ('B','H'):
        p=metrics['P']['mse'];b=metrics[other]['mse'];point=1-float(p.mean()/b.mean())
        gains=1-p[indices].mean(1)/b[indices].mean(1)
        lo,hi=np.percentile(gains,[2.5,97.5]);passed=point>=CFG['minimum_gain'] and lo>0
        result[other]={'gain':point,'interval95':[float(lo),float(hi)],'pass':bool(passed)};ok&=bool(passed)
    bias=metrics['P']['directed_bias'];bl,bh=np.percentile(bias[indices].mean(1),[2.5,97.5])
    calibration=bl>=-CFG['calibration_bound_degrees'] and bh<=CFG['calibration_bound_degrees']
    result['P_calibration']={'directed_bias_degrees':float(bias.mean()),'interval95':[float(bl),float(bh)],'pass':bool(calibration)}
    result['positive_precision_coefficient']=bool(coef>0);result['joint_pass']=bool(ok and calibration and coef>0)
    return result

def frozen(out):
    pin=json.loads((out/'FREEZE.json').read_text())
    for f,h in pin['files'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h, f

def main(stage,out):
    out.mkdir(exist_ok=True,parents=True)
    assert out==ROOT or ROOT in out.parents
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(CFG['hard_stop_utc'])
    if stage=='freeze':
        assert not(out/'SOURCE_FITS.json').exists()
        files=['analysis.py','config.json','PROTOCOL.md','DESIGN_GATE.json']
        savej(out/'FREEZE.json',{'timestamp_utc':NOW(),'files':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}})
        resource_record(out,'FREEZE');print((out/'FREEZE.json').read_text());return
    frozen(out)
    if stage=='source':
        assert not(out/'SOURCE_FITS.json').exists()
        assert hashlib.sha256((ROOT/'dataset_exp1.xlsx').read_bytes()).hexdigest()==CFG['source_pin']
        d=assemble(GATE['source_people']);checks=d.pop('accuracy_checks');np.savez_compressed(out/'source.npz',**d)
        ds={k:v[d['trial']>=CFG['score_first_trial']] for k,v in d.items()};fits=all_fits(ds)
        w=float(np.dot(ds['gap'],ds['y'])/np.dot(ds['gap'],ds['gap']))
        result={'timestamp_utc':NOW(),'features':NAMES,'dimensions':DIMS,'models':fits,'fixed_weight':w,'source_people':GATE['source_people'],'primary_rows':len(ds['y']),
          'training_mse_degrees2':{k:float(np.mean(wrap(ds['y']-predict(v,ds['X']))**2)*32400) for k,v in fits.items()}}
        savej(out/'SOURCE_FITS.json',result);resource_record(out,'SOURCE',{'original_accuracy_checks':checks});print(json.dumps({k:v for k,v in result.items() if k!='models'},indent=2));return
    fitted=json.loads((out/'SOURCE_FITS.json').read_text());fits=fitted['models']
    if stage=='predict':
        assert not(out/'evaluation_predictions.npz').exists()
        d=assemble(GATE['evaluation_people']);checks=d.pop('accuracy_checks')
        # y was only used as prior history after each trial's feature was made; no scores here.
        predictions={k:predict(v,d['X']) for k,v in fits.items()}
        predictions.update(N=np.zeros(len(d['y'])),F=np.clip(fitted['fixed_weight']*d['gap'],-1,1))
        inputs={k:v for k,v in d.items() if k!='y'}
        np.savez_compressed(out/'evaluation_features.npz',**inputs)
        np.savez_compressed(out/'evaluation_predictions.npz',**predictions)
        pin={'timestamp_utc':NOW(),'prediction_sha256':hashlib.sha256((out/'evaluation_predictions.npz').read_bytes()).hexdigest(),
          'feature_sha256':hashlib.sha256((out/'evaluation_features.npz').read_bytes()).hexdigest(),'rows':len(d['y']),'primary_rows':int(np.sum(d['trial']>=CFG['score_first_trial'])),
          'interpretation':'Every feature computed before its current final response/feedback updated history. Complete arrays saved without calculating losses. Numerical target responses used as preceding behavioral histories, after freeze; acquired XML is not sealed at this point.'}
        savej(out/'PREDICTIONS_PIN.json',pin);resource_record(out,'PREDICT',{'original_accuracy_checks':checks});print(json.dumps(pin,indent=2));return
    if stage=='score':
        assert not(out/'SCORES.json').exists()
        pin=json.loads((out/'PREDICTIONS_PIN.json').read_text())
        assert hashlib.sha256((out/'evaluation_predictions.npz').read_bytes()).hexdigest()==pin['prediction_sha256']
        with np.load(out/'evaluation_features.npz') as z:d={k:z[k] for k in z.files}
        with np.load(out/'evaluation_predictions.npz') as z:p={k:z[k] for k in z.files}
        target=[];ids=[]
        for r in rows(set(GATE['evaluation_people'])):target.append(wrap_deg(r['R']-r['K'])/180);ids.append(int(r['A']))
        assert np.array_equal(ids,d['id']);d['y']=np.array(target)
        np.savez_compressed(out/'evaluation_scored.npz',**d)
        m=d['trial']>=CFG['score_first_trial'];dp={k:v[m] for k,v in d.items()};pp={k:v[m] for k,v in p.items()}
        people,metrics=person_metrics(dp,pp);rng=np.random.default_rng(CFG['seed_evaluation']);indices=rng.integers(0,len(people),(CFG['bootstrap_evaluation'],len(people)))
        decision=rule(metrics,indices,fits['P']['coef'][-1]);summary={k:{t:float(a.mean()) for t,a in v.items()} for k,v in metrics.items()}
        loo=[]
        for j,person in enumerate(people):
            mm={k:{t:np.delete(a,j) for t,a in v.items()} for k,v in metrics.items()};ii=rng.integers(0,len(people)-1,(CFG['bootstrap_evaluation'],len(people)-1))
            loo.append({'deleted':int(person),'decision':rule(mm,ii,fits['P']['coef'][-1])})
        _,allm=person_metrics(d,p)
        linear={k:float(np.mean((dp['y']-v)**2)*32400) for k,v in pp.items()}
        result={'timestamp_utc':NOW(),'people':people.tolist(),'rows':len(dp['y']),'summary':summary,'primary':decision,'leave_one_person_out':loo,
          'contrary_all54_summary':{k:{t:float(a.mean()) for t,a in v.items()} for k,v in allm.items()},'contrary_linear_wrapped_revision_mse':linear,
          'person_metrics':{k:{t:a.tolist() for t,a in v.items()} for k,v in metrics.items()},'precision_coefficient':fits['P']['coef'][-1]}
        savej(out/'SCORES.json',result);resource_record(out,'SCORE');print(json.dumps({k:v for k,v in result.items() if k not in ('person_metrics','leave_one_person_out')},indent=2));return
    if stage=='source_uncertainty':
        assert not(out/'SOURCE_UNCERTAINTY.json').exists()
        s=load_data(out/'source.npz');e=load_data(out/'evaluation_scored.npz');people=np.unique(s['id']);ep=np.unique(e['id']);rng=np.random.default_rng(CFG['seed_source']);results=[]
        for rep in range(CFG['source_resamples']):
            w=np.bincount(rng.integers(0,len(people),len(people)),minlength=len(people)).astype(float)
            new=all_fits(s,weights=w);pred={k:predict(v,e['X']) for k,v in new.items()};_,met=person_metrics(e,pred);draw=rng.integers(0,len(ep),len(ep))
            row={'rep':rep,'source_multiplicities':w.astype(int).tolist(),'penalties':{k:v['penalty'] for k,v in new.items()},'precision_coefficient':new['P']['coef'][-1]}
            for other in ('B','H'):
                row['gain_'+other]=1-float(met['P']['mse'].mean()/met[other]['mse'].mean())
                row['paired_gain_'+other]=1-float(met['P']['mse'][draw].mean()/met[other]['mse'][draw].mean())
            results.append(row)
            if (rep+1)%20==0:print('source bootstrap',rep+1,flush=True)
        summary={k:np.percentile([r[k] for r in results],[2.5,50,97.5]).tolist() for k in ('gain_B','gain_H','paired_gain_B','paired_gain_H')}
        savej(out/'SOURCE_UNCERTAINTY.json',{'timestamp_utc':NOW(),'scope':'Finite resampling diagnostics, not certified coverage. Duplicate identity copies always share/exclude one source fold.','summary':summary,'replicates':results});resource_record(out,'SOURCE_UNCERTAINTY');print(json.dumps(summary,indent=2));return
    if stage=='controls':
        assert not(out/'CONTROLS.json').exists()
        s=load_data(out/'source.npz');e=load_data(out/'evaluation_scored.npz');sp=np.unique(s['id']);ep=np.unique(e['id']);rng=np.random.default_rng(CFG['seed_controls'])
        engines={k:Engine(s,dim) for k,dim in DIMS.items()};sm=predict(fits['H'],s['X']);em=predict(fits['H'],e['X'])
        # Project P's extra feature on H, using fixed positive regularization for stability.
        h=engines['H'];q=s['X'][:,-1];sy,xy=h.labels(q);projection=h.solve(sy,xy,np.ones(len(sp)),.0001)
        zs=q-predict(projection,s['X']);ze=e['X'][:,-1]-predict(projection,e['X'])
        sigma=float(np.sqrt(np.mean(wrap(s['y']-sm)**2)));signal_var=sigma*sigma*.75*CFG['nominal_control_oracle_gain']/(1-CFG['nominal_control_oracle_gain'])
        gamma=math.sqrt(signal_var/float(np.mean(zs*zs)))
        results=[];indices=rng.integers(0,len(ep),(CFG['bootstrap_evaluation'],len(ep)))
        for kind in ('signal','null'):
            for rep in range(CFG['control_replicates_per_class']):
                def noise(d,people):
                    offsets=rng.normal(size=len(people));lookup={int(k):j for j,k in enumerate(people)}
                    off=np.array([offsets[lookup[int(i)]] for i in d['id']]);return sigma*(.5*off*d['gap']+math.sqrt(.75)*rng.normal(size=len(off)))
                ms=np.clip(sm+(gamma*zs if kind=='signal' else 0),-1,1);me=np.clip(em+(gamma*ze if kind=='signal' else 0),-1,1)
                syy=np.clip(ms+noise(s,sp),-1,1);ey=np.clip(me+noise(e,ep),-1,1)
                new={k:engine.fit(syy) for k,engine in engines.items()};pr={k:predict(v,e['X']) for k,v in new.items()};ed=dict(e,y=ey)
                _,met=person_metrics(ed,pr);decision=rule(met,indices,new['P']['coef'][-1])
                oracle_mse=float(np.mean((wrap(ey-me)*180)**2));h_mse=float(np.mean((wrap(ey-em)*180)**2))
                results.append({'kind':kind,'rep':rep,'decision':decision,'oracle_gain_vs_H_mean':1-oracle_mse/h_mse,'penalties':{k:v['penalty'] for k,v in new.items()}})
                if rep==0:np.savez_compressed(out/('CONTROL_EXAMPLE_'+kind+'.npz'),source_y=syy,evaluation_y=ey,**{'prediction_'+k:v for k,v in pr.items()})
                if (rep+1)%20==0:print(kind,'controls',rep+1,flush=True)
        counts={k:sum(r['decision']['joint_pass'] for r in results if r['kind']==k) for k in ('signal','null')}
        rec={'timestamp_utc':NOW(),'scope':'Fixed observed feature histories only. Source labels/penalty selection refit in every replicate. No regenerated outcome-dependent histories, boundary power or coverage claim.',
          'sigma_normalized':sigma,'gamma':gamma,'counts':counts,'conditional_discrimination_pass':counts['signal']>=80 and counts['null']<=5,
          'attained_signal_oracle_gain_percentiles':np.percentile([r['oracle_gain_vs_H_mean'] for r in results if r['kind']=='signal'],[2.5,50,97.5]).tolist(),'replicates':results}
        savej(out/'CONTROLS.json',rec);resource_record(out,'CONTROLS');print(json.dumps({k:v for k,v in rec.items() if k!='replicates'},indent=2));return
    raise ValueError(stage)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['freeze','source','predict','score','source_uncertainty','controls']);parser.add_argument('--outdir',default=str(ROOT));a=parser.parse_args()
    main(a.stage,pathlib.Path(a.outdir).resolve())
