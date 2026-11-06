"""One bounded source-only experiment. No target-answer/prediction access path."""
import os
for _k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_k] = '1'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import resource
import time
import numpy as np
import scipy
from scipy import sparse
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import t as student_t

ROOT = Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
HERE = ROOT/'lab/tasks/memory-source-calibration-2026-10-31'
REVIEW = ROOT/'lab/reviews/memory-readiness-2026-10-30'
SRC = ROOT/'sources/memory_policy_transfer_2026-10-30'
PRIOR = 7_515_180_884
LIMIT = 400_000_000
DEADLINE = datetime.fromisoformat('2026-10-31T20:07:47+00:00')
GROUPS = ('source_fit','source_validation','smart','spaced')
ALLOW = ('uid','item','time','install','arm','count','ordinal')
COMPACT = np.dtype([(k,v) for k,v in [('uid','u4'),('item','u4'),('time','i8'),('install','i8'),('arm','u4'),('count','i4'),('ordinal','u8')]])
GRID = [(k,lam) for k in (4,16,64) for lam in (1,8,64)]
NPY_PIN = 'b6ece5e1c7525e0027679b545ab07167772f559adf9cc74c44f405c8f689d9fe'

def now(): return datetime.now(timezone.utc).isoformat()

def guard():
    if datetime.now(timezone.utc) >= DEADLINE: raise RuntimeError('hard deadline reached')
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > 2_000_000_000:
        raise RuntimeError('2GB RSS limit exceeded')

def writej(name, obj):
    (HERE/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')

class Budget:
    def __init__(self):
        p=HERE/'ACCOUNTING.json'
        self.entries=json.loads(p.read_text())['entries'] if p.exists() else [
            {'path':'ordinary context/source/code/QA envelope','bytes':20_000_000,'basis':'conservative envelope, includes all shell document reads and own code/hash/output QA'}]
    @property
    def total(self): return sum(e['bytes'] for e in self.entries)
    def charge(self, path, n, basis):
        guard()
        if self.total+n > LIMIT or PRIOR+self.total+n > 8_000_000_000:
            raise RuntimeError('read budget would be exceeded')
        self.entries.append({'path':str(path),'bytes':int(n),'basis':basis})
    def read(self,path):
        self.charge(path.relative_to(ROOT),path.stat().st_size,'full cached/derived application-ingress bytes')
        return path.read_bytes()
    def j(self,path): return json.loads(self.read(path))
    def save(self):
        writej('ACCOUNTING.json',{'utc':now(),'prior':PRIOR,'additional':self.total,'cumulative':PRIOR+self.total,
            'additional_cap':LIMIT,'cumulative_cap':8_000_000_000,'entries':self.entries,
            'maxrss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})

def projected_npy(raw):
    f=io.BytesIO(raw); version=np.lib.format.read_magic(f)
    reader=np.lib.format.read_array_header_1_0 if version==(1,0) else np.lib.format.read_array_header_2_0
    shape,fort,dt=reader(f); offset=f.tell()
    assert len(shape)==1 and not fort and not dt.hasobject
    assert len(raw)==offset+shape[0]*dt.itemsize
    out=np.empty(shape[0],dtype=COMPACT)
    for k in ALLOW:
        typ,pos=dt.fields[k][:2]; assert typ==COMPACT.fields[k][0]
        out[k]=np.ndarray(shape,dtype=typ,buffer=raw,offset=offset+pos,strides=(dt.itemsize,))
    return out,{'shape':list(shape),'record_bytes':dt.itemsize,'header_bytes':offset,
                'typed_fields':list(ALLOW),'excluded_field_names_only':[k for k in dt.names if k not in ALLOW]}

def cells(d,prior,other):
    return (sum(d>v for v in (1/1440,1/24,1,7)),sum(prior>v for v in (1,2,4)),sum(other>v for v in (0,9,99)))

def item_groups(a):
    ids=np.argsort(a['item'],kind='stable')
    bounds=np.r_[0,1+np.flatnonzero(np.diff(a['item'][ids])),len(ids)]
    return [(int(a['item'][ids[l]]),ids[l:r]) for l,r in zip(bounds[:-1],bounds[1:]) if r>l]

def focal_events(a,before):
    pre={item:int(before['count'][pos[-1]]) for item,pos in item_groups(before)}
    gaps=[]; eligible=[]
    for item,pos in item_groups(a):
        c=a['count'][pos].astype('int64')
        if item in pre:
            inc=int(c[0])-pre[item]
            if inc!=1: gaps.append((-1,int(pos[0]),'prefix',max(0,inc-1)))
        elif c[0]!=1: gaps.append((-1,int(pos[0]),'prefix',max(0,int(c[0])-1)))
        for l,r,c0,c1 in zip(pos[:-1],pos[1:],c[:-1],c[1:]):
            inc=int(c1-c0)
            if inc!=1: gaps.append((int(l),int(r),'jump' if inc>1 else 'reset',max(0,inc-1)))
        if item not in pre and len(pos)>=2 and np.array_equal(c,np.arange(1,len(c)+1)):
            eligible.append((item,pos))
    gs=sorted(gaps); starts=np.array([g[0] for g in gs]); ends=np.array([g[1] for g in gs])
    maxend=np.maximum.accumulate(ends) if len(ends) else ends
    internal=sorted(g for g in gaps if g[2]!='prefix')
    istart=np.array([g[0] for g in internal]); iend=np.array([g[1] for g in internal])
    imax=np.maximum.accumulate(iend) if len(iend) else iend
    prefix_end=max([g[1] for g in gaps if g[2]=='prefix'] or [-1])
    jumps=[g for g in gaps if g[2]=='jump']
    out=[]
    for item,pos in eligible:
        for rank,r in enumerate(pos):
            r=int(r); l=int(pos[rank-1]) if rank else r
            d=(int(a['time'][r])-int(a['time'][l]))/86400
            other=r-l-1 if rank else 0
            k=int(np.searchsorted(starts,r,side='left')) if rank else 0
            ki=int(np.searchsorted(istart,r,side='left')) if rank else 0
            missing=sum(g[3] for g in jumps if g[0]>=l and g[1]<=r) if rank else 0
            out.append({'item':item,'ordinal':int(a['ordinal'][r]),'time':int(a['time'][r]),
                'prior':rank,'delta':d,'other':other,'cell':cells(d,rank,other),
                'ambiguous':bool(rank and k and maxend[k-1]>l),
                'prefix':bool(rank and l<prefix_end),'internal':bool(rank and ki and imax[ki-1]>l),
                'missing_lower':missing})
    return sorted(out,key=lambda r:r['time'])

def source_shard(budget,arm,allowed):
    """Never convert an unallowlisted correct value or any auxiliary value."""
    path=SRC/('opaque_answers/arm_%02d.tsv.gz'%arm)
    # One compressed ingress, charged before open; streaming inflation charged
    # line-by-line including blind discards. No other shard can be passed in.
    compressed=budget.read(path)
    manifest=budget.j(ROOT/'lab/tasks/memory-policy-transfer-2026-10-30/MANIFEST.json')
    assert hashlib.sha256(compressed).hexdigest()==manifest[str(path.relative_to(ROOT))]['sha256']
    values={}; inflated=0; lines=0
    with gzip.GzipFile(fileobj=io.BytesIO(compressed),mode='rb') as f:
        for line in f:
            inflated+=len(line); lines+=1
            if budget.total+inflated>LIMIT: raise RuntimeError('inflated shard read cap')
            ordinal_bytes,sep,remaining=line.partition(b'\t'); assert sep
            ordinal=int(ordinal_bytes)
            if ordinal not in allowed: continue
            correct_bytes,sep,opaque_aux=remaining.partition(b'\t'); assert sep
            value=float(correct_bytes)
            if value not in (0,1): raise RuntimeError('nonbinary permitted source answer')
            assert ordinal not in values
            values[ordinal]=int(value)
    budget.charge(path.relative_to(ROOT),inflated,'entire inflated stream including blind-discarded nonpermitted rows/fields')
    assert set(values)==set(allowed),'missing permitted source answers'
    return values,{'compressed_sha256':hashlib.sha256(compressed).hexdigest(),'compressed_bytes':len(compressed),
        'inflated_bytes':inflated,'streamed_rows':lines,'correct_values_interpreted':len(values),
        'auxiliary_values_interpreted':0,'nonrandom_shards_opened':0}

def features(d,y,k,groups=(0,),init=.5):
    X=np.zeros((len(y),6)); X[:,0]=1
    for uid in np.unique(d['uid'][np.isin(d['group'],groups)]):
        ix=np.flatnonzero(d['uid']==uid); A=B=0; histories={}
        for i in ix:
            item=int(d['item'][i]); S,F=histories.get(item,(0,0))
            X[i,1:]=[np.log1p(S),np.log1p(F),np.log1p(d['delta'][i]),
                np.log((A+k*init)/(B+k*(1-init)))-np.log(init/(1-init)),np.log1p(d['other'][i])]
            # The current answer is consulted strictly after the feature row.
            value=y[i]; assert value in (0,1)
            histories[item]=(S+value,F+1-value); A+=value; B+=1-value
    return X

def ll(y,eta): return np.logaddexp(0,eta)-y*eta

def per_id(v,uid):
    ids=np.unique(uid)
    return np.array([np.mean(v[uid==u]) for u in ids]),ids

def design(d,F,mask,aug,item_bank):
    ng=6 if aug else 5; idx=np.flatnonzero(mask)
    item_index={v:i for i,v in enumerate(item_bank)}
    columns=np.array([item_index.get(int(v),-1) for v in d['item'][idx]],dtype=int)
    seen=columns>=0
    one=sparse.csr_matrix((np.ones(np.sum(seen)),(np.flatnonzero(seen),columns[seen])),shape=(len(idx),len(item_bank)))
    return sparse.hstack([sparse.csr_matrix(F[idx,:ng]),one],format='csr')

def fit(X,y,uid,lam,ng):
    guard(); n=len(y); ids,inv,count=np.unique(uid,return_inverse=True,return_counts=True)
    weights=n/(len(ids)*count[inv]); penalty=np.r_[.04,np.full(ng-1,1/9),np.full(X.shape[1]-ng,lam)]
    def obj(theta):
        eta=X@theta; p=expit(eta)
        return float(np.dot(weights,ll(y,eta))+.5*np.dot(penalty,theta*theta)),np.asarray(X.T@(weights*(p-y))).ravel()+penalty*theta
    initial=np.zeros(X.shape[1]); mean=np.clip(np.average(y,weights=weights),.01,.99)
    initial[0]=np.log(mean/(1-mean))
    res=minimize(obj,initial,jac=True,method='L-BFGS-B',options={'maxiter':500,'ftol':1e-11,'gtol':1e-6,'maxls':40})
    value,gradient=obj(res.x)
    ok=np.isfinite(value) and np.all(np.isfinite(res.x)) and (res.success or np.max(np.abs(gradient))<=1e-3)
    if not ok: raise RuntimeError('failed frozen fit: '+str(res.message))
    return {'theta':res.x,'X':X,'y':y,'uid':uid,'weights':weights,'penalty':penalty,'ng':ng,
        'objective':value,'max_abs_gradient':float(np.max(np.abs(gradient))),'iterations':int(res.nit),'solver_success':bool(res.success)}

def fit_pair(d,y,k,lam,item_bank,training=None):
    F=features(d,y,k,groups=(0,)); mask=(d['group']==0)&(d['prior']>0)
    if training is not None: mask &= np.isin(d['uid'],training)
    return [fit(design(d,F,mask,aug,item_bank),y[mask],d['uid'][mask],lam,6 if aug else 5) for aug in (False,True)],F

def select(d,y,item_bank,folds):
    records=[]; fitids=np.unique(d['uid'][d['group']==0]); best=None
    for k,lam in GRID:
        guard(); F=features(d,y,k,groups=(0,)); values=[[],[]]
        for fold in range(3):
            train=[u for u in fitids if folds[int(u)]!=fold]; valid=[u for u in fitids if folds[int(u)]==fold]
            tr=(d['group']==0)&(d['prior']>0)&np.isin(d['uid'],train)
            va=(d['group']==0)&d['primary']&np.isin(d['uid'],valid)
            if not np.any(va): raise RuntimeError('empty frozen inner primary fold')
            for j,aug in enumerate((False,True)):
                model=fit(design(d,F,tr,aug,item_bank),y[tr],d['uid'][tr],lam,6 if aug else 5)
                eta=design(d,F,va,aug,item_bank)@model['theta']
                scores,_=per_id(ll(y[va],eta),d['uid'][va]); values[j].extend(scores.tolist())
        score=.5*(np.mean(values[0])+np.mean(values[1])); records.append({'k':k,'lambda':lam,'joint_cv_loss':float(score),
            'baseline_cv_loss':float(np.mean(values[0])),'augmented_cv_loss':float(np.mean(values[1]))})
        if best is None or score<best[0]-1e-10: best=(score,k,lam)
    pair,F=fit_pair(d,y,best[1],best[2],item_bank)
    return pair,{'k':best[1],'lambda':best[2],'grid':records},F

def solve_hessian(model,g):
    X=model['X']; ng=model['ng']; p=expit(X@model['theta']); v=model['weights']*p*(1-p)
    Z=X[:,:ng].toarray(); J=X[:,ng:]
    Hgg=Z.T@(v[:,None]*Z)+np.diag(model['penalty'][:ng])
    Hgj=np.asarray(J.T@(v[:,None]*Z)).T
    Hjj=np.asarray(J.T@v).ravel()+model['penalty'][ng:]
    schur=Hgg-(Hgj/Hjj)@Hgj.T
    qg=np.linalg.solve(schur,g[:ng]-Hgj@(g[ng:]/Hjj))
    qj=(g[ng:]-Hgj.T@qg)/Hjj
    q=np.r_[qg,qj]
    residual=X.T@(v*(X@q))+model['penalty']*q-g
    assert np.max(np.abs(residual))<=1e-7*(1+np.max(np.abs(g)))
    return q

def source_variance(pair,grads):
    influences={}
    for model,g in zip(pair,grads):
        if g is None: continue
        q=solve_hessian(model,g); eta=model['X']@model['theta']
        z=(model['X']@q)*model['weights']*(model['y']-expit(eta))
        for u in np.unique(model['uid']):
            influences[int(u)]=influences.get(int(u),0.)+float(np.sum(z[model['uid']==u]))
    vals=np.array(list(influences.values())); vals-=np.mean(vals)
    return float(len(vals)/(len(vals)-1)*np.sum(vals*vals)) if len(vals)>1 else 0.

def interval(pair,values,uid,grads):
    means,ids=per_id(values,uid); n=len(ids); assert n>=2
    sampling=float(np.var(means,ddof=1)/n); estimation=source_variance(pair,grads)
    se=np.sqrt(sampling+estimation); df=min(75,n)-1; critical=float(student_t.ppf(.975,df))
    mean=float(np.mean(means))
    return {'mean':mean,'lower':float(mean-critical*se),'upper':float(mean+critical*se),
        'se':float(se),'evaluation_cluster_variance':sampling,'source_estimation_variance':estimation,'df':df,
        'people':n,'rows':len(values),'per_id':[{'uid':int(u),'mean':float(v)} for u,v in zip(ids,means)]}

def evaluate(d,y,pair,k,item_bank,group,primary=True,init=.5,missing=False):
    F=features(d,y,k,groups=(group,),init=init)
    if missing: F[:,5]=np.log1p(d['other']+d['missing_lower'])
    mask=(d['group']==group)&(d['primary'] if primary else d['prior']>0)
    uid=d['uid'][mask]; ids,inv,cnt=np.unique(uid,return_inverse=True,return_counts=True)
    w=1/(len(ids)*cnt[inv]); Y=y[mask]
    matrices=[design(d,F,mask,aug,item_bank) for aug in (False,True)]
    etas=[X@m['theta'] for X,m in zip(matrices,pair)]; probs=[expit(e) for e in etas]
    loss=[ll(Y,e) for e in etas]
    grads=[np.asarray(X.T@(w*(p-Y)*sgn)).ravel() for X,p,sgn in zip(matrices,probs,(1,-1))]
    gain=interval(pair,loss[0]-loss[1],uid,grads)
    brier=[(p-Y)**2 for p in probs]
    bg=[np.asarray(X.T@(w*2*(p-Y)*p*(1-p)*sgn)).ravel() for X,p,sgn in zip(matrices,probs,(-1,1))]
    brier_diff=interval(pair,brier[1]-brier[0],uid,bg)
    calibration=[]
    for j,(X,p,L,B) in enumerate(zip(matrices,probs,loss,brier)):
        g=np.asarray(X.T@(w*p*(1-p))).ravel(); gs=[None,None]; gs[j]=g
        bias=interval(pair,p-Y,uid,gs)
        binno=np.minimum((p*5).astype(int),4)
        ece=float(sum(abs(np.dot(w[binno==b],(p-Y)[binno==b])) for b in range(5)))
        cal={'bias':bias,'absolute_bias_upper95':max(abs(bias['lower']),abs(bias['upper'])),
            'fixed_bin_ece':ece,'equal_id_logloss':float(np.dot(w,L)),'equal_id_brier':float(np.dot(w,B))}
        calibration.append(cal)
    return {'gain':gain,'brier_augmented_minus_baseline':brier_diff,'calibration':calibration,
        'calibration_gate':bool(all(c['absolute_bias_upper95']<=.10 and c['fixed_bin_ece']<=.10 for c in calibration)
             and brier_diff['upper']<=.02),'meaningful_gain_gate':bool(gain['lower']>.01)}

def serialize_model(model):
    return {k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in model.items() if k not in ('X','y','uid','weights','penalty')}

def freeze():
    files=[HERE/'PROTOCOL.md',Path(__file__),REVIEW/'CANDIDATE_FREEZE.md',REVIEW/'CANDIDATE_READINESS.json',REVIEW/'FUTURE_COMPARISON.md']
    return {'utc':now(),'before_new_answers':True,'files':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}}

def synthetic():
    checks=[]
    def check(name,condition):
        assert condition,name
        checks.append({'name':name,'passed':True})
    fake=np.zeros(3,dtype=np.dtype(COMPACT.descr+[('mode','u4'),('sequence','i4')]))
    fake['uid']=[1,2,3]; fake['mode']=4294967295; fake['sequence']=-999
    f=io.BytesIO(); np.save(f,fake,allow_pickle=False); a,info=projected_npy(f.getvalue())
    check('typed_metadata_allowlist_only',a.dtype.names==ALLOW and a['uid'].tolist()==[1,2,3])
    check('excluded_metadata_names_not_values',info['excluded_field_names_only']==['mode','sequence'])
    # This sample contains an ineligible other item, whose row still counts.
    raw=np.zeros(5,dtype=COMPACT)
    for i,(item,count) in enumerate([(1,1),(2,4),(1,2),(1,3),(3,1)]): raw[i]=(1,item,100+i*10,0,0,count,i)
    ev=focal_events(raw,np.empty(0,dtype=COMPACT))
    check('other_ineligible_item_counted',ev[1]['other']==1)
    d={k:np.array(v) for k,v in {'uid':[1,1,1,1],'item':[4,5,4,4],'delta':[0,0,1,2],'other':[0,0,1,0]}.items()}
    d['group']=np.zeros(4,dtype=int); y=np.array([1.,0.,0.,1.]); F=features(d,y,4)
    check('preceding_focal_success_failure_only',F[2,1]==np.log(2) and F[2,2]==0 and F[3,1]==np.log(2) and F[3,2]==np.log(2))
    check('person_update_is_pre_response',F[0,4]==0 and F[1,4]==np.log(3/2) and F[2,4]==0)
    theta=np.array([.3,.8,-.6,-.2,.5,.1]); pred=expit(F@theta)
    for i in range(4):
        changed=y.copy(); changed[i]=1-changed[i]
        check('current_answer_invariant_'+str(i),np.array_equal(features(d,changed,4)[:i+1],F[:i+1]))
        changed=y.copy(); changed[i:]=1-changed[i:]
        check('future_answer_suffix_invariant_'+str(i),np.array_equal(features(d,changed,4)[:i+1],F[:i+1]))
    future={k:v.copy() for k,v in d.items()}; future['delta'][3]=1e6; future['other'][3]=999
    check('future_timestamp_count_suffix_invariant',np.array_equal(expit(features(future,y,4)@theta)[:3],pred[:3]))
    check('deliberate_current_inclusive_feature_detected',not np.array_equal(np.cumsum(y),np.cumsum(1-y)))
    # Convert only the allowed ordinal's correct; malformed other rows/aux fields stay opaque.
    lines=[b'10\tFORBIDDEN\tBAD_AUX\n',b'11\t1\tBAD_AUX\n']; vals={}
    for line in lines:
        o,_,rest=line.partition(b'\t')
        if int(o)==11: vals[int(o)]=int(rest.partition(b'\t')[0])
    check('masked_correct_reader_skips_disallowed_malformed_answer',vals=={11:1})
    check('binary_correctness_rejection',not (2. in (0,1)))
    return {'utc':now(),'checks':checks,'all_passed':True,'check_count':len(checks),
        'known_probabilities':pred.tolist(),'source_answer_reads':0,'target_answer_reads':0}

def prepare(budget):
    candidate=budget.j(REVIEW/'CANDIDATE_READINESS.json')
    people=candidate['people']; raw=budget.read(SRC/'metadata_sorted.npy')
    assert hashlib.sha256(raw).hexdigest()==NPY_PIN
    data,npyinfo=projected_npy(raw); del raw
    events=[]; folds={}; random_codes=set(); source_items=set()
    S=int(datetime(2020,3,1,tzinfo=timezone.utc).timestamp()); E=int(datetime(2020,6,1,tzinfo=timezone.utc).timestamp())
    for person in people:
        guard(); uid=person['uid']; group=GROUPS.index(person['group'])
        start,end=np.searchsorted(data['uid'],[uid,uid+1]); all_a=data[start:end]
        before=all_a[all_a['time']<S]; a=all_a[(all_a['time']>=S)&(all_a['time']<E)]
        assert np.all(a['time'][1:]>a['time'][:-1])
        if group in (0,1): random_codes.update(int(v) for v in np.unique(a['arm']))
        rows=focal_events(a,before); assert sum(r['prior']>0 for r in rows)==person['focal_repeat_rows']
        folds[uid]=int(person['hash'][16:24],16)%3
        for r in rows:
            r.update(uid=uid,group=group,preperiod=person['installation_pre_period'])
            events.append(r)
            if group==0 and r['prior']>0: source_items.add(r['item'])
    assert len(random_codes)==1
    clean=[r for r in events if r['group']==0 and r['prior']>0 and not r['ambiguous']]
    counts=Counter(r['cell'] for r in clean); ids=defaultdict(set)
    for r in clean: ids[r['cell']].add(r['uid'])
    support={c for c,n in counts.items() if n>=10 and len(ids[c])>=5}
    for r in events:
        r['primary']=r['prior']>0 and not r['ambiguous'] and r['cell'] in support and r['item'] in source_items
    events.sort(key=lambda r:(r['uid'],r['time']))
    fields=('uid','group','item','ordinal','time','prior','delta','other','ambiguous','prefix','internal','missing_lower','primary','preperiod')
    d={k:np.array([r[k] for r in events]) for k in fields}
    counts_out={}
    for group,name in enumerate(GROUPS):
        m=(d['group']==group)&d['primary']; r=(d['group']==group)&(d['prior']>0)
        counts_out[name]={'primary_rows':int(np.sum(m)),'primary_people':len(np.unique(d['uid'][m])),
            'repeat_rows':int(np.sum(r)),'focal_events_including_first':int(np.sum(d['group']==group))}
        assert counts_out[name]['primary_rows']==(1116,485,1472,1432)[group]
        assert counts_out[name]['primary_people']==(36,10,29,23)[group]
        assert counts_out[name]['repeat_rows']==(18272,4096,16234,16821)[group]
    np.savez_compressed(HERE/'safe_schedules.npz',**d)
    info={'utc':now(),'groups':counts_out,'random_arm_code':next(iter(random_codes)),'item_bank':sorted(source_items),
        'folds':folds,'NPY_projection':npyinfo,'candidate_ids':{g:[p['uid'] for p in people if p['group']==g] for g in GROUPS},
        'candidate_sha256':hashlib.sha256((REVIEW/'CANDIDATE_READINESS.json').read_bytes()).hexdigest(),
        'metadata_sha256':NPY_PIN,'new_answers_read':0}
    writej('METADATA_CHECK.json',info)
    return d,info

def run_checks():
    assert not (HERE/'INITIAL_FREEZE.json').exists(),'checks already frozen'
    checks=synthetic(); writej('SYNTHETIC_CHECKS.json',checks); writej('INITIAL_FREEZE.json',freeze())
    print(json.dumps({'synthetic_checks':checks['check_count'],'all_passed':True,'known_probabilities':checks['known_probabilities'],'source_answers':0,'target_answers':0}),flush=True)

def run_fit(budget):
    assert (HERE/'SYNTHETIC_CHECKS.json').exists() and not (HERE/'SOURCE_FIT.json').exists()
    frozen=json.loads((HERE/'INITIAL_FREEZE.json').read_text())
    assert frozen['files'][str(Path(__file__).relative_to(ROOT))]['sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    d,info=prepare(budget); budget.save()
    allowed=set(int(o) for o in d['ordinal'][d['group']==0])
    values,exposure=source_shard(budget,info['random_arm_code'],allowed)
    y=np.full(len(d['uid']),np.nan)
    for i in np.flatnonzero(d['group']==0): y[i]=values[int(d['ordinal'][i])]
    np.savez_compressed(HERE/'fit_answers.npz',y=y)
    folds={int(k):v for k,v in info['folds'].items()}
    pair,choice,F=select(d,y,info['item_bank'],folds)
    train=evaluate(d,y,pair,choice['k'],info['item_bank'],0)
    out={'utc':now(),'selection':choice,'models':[serialize_model(m) for m in pair],
        'training_primary_diagnostic_only':train,'new_correct_exposure':exposure,
        'source_fit_people':75,'source_validation_answers_interpreted':0,'target_answers_interpreted':0,
        'nuisance_and_gate_freeze_before_source_validation':True,'source_only_success_does_not_release_targets':True,
        'versions':{'python':os.sys.version,'numpy':np.__version__,'scipy':scipy.__version__}}
    writej('SOURCE_FIT.json',out); budget.save()
    writej('FIT_FREEZE.json',{'utc':now(),'before_validation_answers':True,
        'files':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('PROTOCOL.md','calibrate.py','SOURCE_FIT.json','safe_schedules.npz','fit_answers.npz')}})
    print(json.dumps({'stage':'fit_complete','k':choice['k'],'lambda':choice['lambda'],
        'source_exposure':exposure,'training_primary_gain':train['gain']['mean'],'additional_bytes':budget.total}),flush=True)

def load_saved(budget):
    z=np.load(io.BytesIO(budget.read(HERE/'safe_schedules.npz')),allow_pickle=False); d={k:z[k] for k in z.files}
    y=np.load(io.BytesIO(budget.read(HERE/'fit_answers.npz')),allow_pickle=False)['y']
    info=budget.j(HERE/'METADATA_CHECK.json'); saved=budget.j(HERE/'SOURCE_FIT.json')
    pair,F=fit_pair(d,y,saved['selection']['k'],saved['selection']['lambda'],info['item_bank'])
    for model,old in zip(pair,saved['models']): assert np.max(np.abs(model['theta']-old['theta']))<=1e-8
    return d,y,info,saved,pair

def run_validation(budget):
    assert not (HERE/'VALIDATION_ACCESS.json').exists(),'once-only validation access already started'
    d,y,info,saved,pair=load_saved(budget); k=saved['selection']['k']
    writej('VALIDATION_ACCESS.json',{'utc':now(),'once_only':True,'fit_freeze_sha256':hashlib.sha256((HERE/'FIT_FREEZE.json').read_bytes()).hexdigest()})
    allowed=set(int(o) for o in d['ordinal'][d['group']==1])
    values,exposure=source_shard(budget,info['random_arm_code'],allowed)
    for i in np.flatnonzero(d['group']==1): y[i]=values[int(d['ordinal'][i])]
    np.savez_compressed(HERE/'source_answers_consumed.npz',y=y)
    primary=evaluate(d,y,pair,k,info['item_bank'],1)
    wide=evaluate(d,y,pair,k,info['item_bank'],1,primary=False)
    sensitivities={'initial_prior_'+str(p):evaluate(d,y,pair,k,info['item_bank'],1,init=p) for p in (.25,.75)}
    missing=evaluate(d,y,pair,k,info['item_bank'],1,primary=False,missing=True)
    # Explicit source development diagnostics for prefix/internal gaps; not new gates.
    gap_diagnostics={}
    F=features(d,y,k,groups=(1,)); repeat=(d['group']==1)&(d['prior']>0)
    for label,criterion in [('prefix',d['prefix']),('internal',d['internal']),('no_detected_gap',~d['ambiguous']),('preperiod_install',d['preperiod']),('period_install',~d['preperiod'])]:
        mask=repeat&criterion
        if np.any(mask):
            losses=[ll(y[mask],design(d,F,mask,aug,info['item_bank'])@m['theta']) for aug,m in zip((False,True),pair)]
            scores,ids=per_id(losses[0]-losses[1],d['uid'][mask])
            gap_diagnostics[label]={'people':len(ids),'rows':int(np.sum(mask)),'equal_id_gain':float(np.mean(scores)),
                'counter_indicated_missing_lower_total':int(np.sum(d['missing_lower'][mask]))}
    out={'utc':now(),'primary':primary,'all_focal_repeats_diagnostic':wide,'initialization_sensitivities':sensitivities,
        'gap_category_diagnostics':gap_diagnostics,'counter_lower_bound_perturbed_repeat_diagnostic':missing,
        'new_correct_exposure':exposure,'source_validation_people_consumed':15,'target_answers_interpreted':0,
        'passed_source_calibration':primary['calibration_gate'],'no_retuning':True}
    writej('SOURCE_VALIDATION.json',out); budget.save()
    print(json.dumps({'stage':'validation_complete','calibration_gate':primary['calibration_gate'],
        'gain':primary['gain'],'baseline_bias_upper95':primary['calibration'][0]['absolute_bias_upper95'],
        'augmented_bias_upper95':primary['calibration'][1]['absolute_bias_upper95'],
        'brier_increase_upper95':primary['brier_augmented_minus_baseline']['upper'],
        'additional_bytes':budget.total,'target_answers':0}),flush=True)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=('checks','fit','validation'))
    args=parser.parse_args(); budget=Budget(); begin=time.monotonic()
    try:
        guard()
        if args.stage=='checks': run_checks()
        elif args.stage=='fit': run_fit(budget)
        elif args.stage=='validation': run_validation(budget)
    except Exception as exc:
        writej('FAILURE_'+args.stage+'.json',{'utc':now(),'error_type':type(exc).__name__,'error':str(exc),
            'elapsed_seconds':time.monotonic()-begin,'maxrss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        raise
    finally: budget.save()

if __name__=='__main__': main()
