"""Scoped independent reconstruction. Does not import the author's estimator."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
import io, json, hashlib, gzip, zipfile, resource, sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, Counter
import numpy as np
from scipy.special import expit
from scipy.stats import t as student_t
from scipy.linalg import solve

ROOT=Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
HERE=ROOT/'lab/reviews/memory-source-calibration-2026-10-31'
AUTHOR=ROOT/'lab/tasks/memory-source-calibration-2026-10-31'
CAND=ROOT/'lab/reviews/memory-readiness-2026-10-30'
SOURCE=ROOT/'sources/memory_policy_transfer_2026-10-30'
DEADLINE=datetime.fromisoformat('2026-10-31T19:41:42+00:00')
BASELINE=7638337193
GROUPS=['source_fit','source_validation','smart','spaced']

def now(): return datetime.now(timezone.utc).isoformat()
def write(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def guard():
    assert datetime.now(timezone.utc)<DEADLINE, 'review deadline reached'
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<2000000000, 'RSS cap'
def charge(path,size,basis):
    guard()
    ledger=json.loads((HERE/'ACCOUNTING.json').read_text())
    total=ledger['charged']+int(size)
    assert total<=150000000 and BASELINE+total<=8000000000, 'read cap'
    ledger['entries'].append({'path':str(path),'bytes':int(size),'basis':basis})
    ledger.update(charged=total,cumulative=BASELINE+total,utc=now(),maxrss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write('ACCOUNTING.json',ledger)
def read(path):
    charge(path.relative_to(ROOT),path.stat().st_size,'full file ingress, reserved before access')
    raw=path.read_bytes()
    pins=json.loads((HERE/'INPUT_PINS.json').read_text()) if (HERE/'INPUT_PINS.json').exists() else {}
    pins[str(path.relative_to(ROOT))]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    write('INPUT_PINS.json',pins)
    return raw
def readj(path): return json.loads(read(path))
def npz(path):
    raw=read(path)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        size=sum(info.file_size for info in archive.infolist())
    charge(path.relative_to(ROOT),size,'NPZ uncompressed member bytes including NPY headers')
    with np.load(io.BytesIO(raw),allow_pickle=False) as z:
        return {name:z[name] for name in z.files}

def metadata():
    assert not (HERE/'METADATA_RECONSTRUCTION.json').exists(), 'metadata already computed'
    candidate=readj(CAND/'CANDIDATE_READINESS.json')
    raw=read(SOURCE/'metadata_sorted.npy')
    assert hashlib.sha256(raw).hexdigest()=='b6ece5e1c7525e0027679b545ab07167772f559adf9cc74c44f405c8f689d9fe'
    stream=io.BytesIO(raw)
    version=np.lib.format.read_magic(stream)
    header=np.lib.format.read_array_header_1_0 if version==(1,0) else np.lib.format.read_array_header_2_0
    shape,fortran,dtype=header(stream)
    assert not fortran and not dtype.hasobject and len(shape)==1
    offset=stream.tell()
    # Project only the seven authorized fields, never materializing auxiliary values.
    names=('uid','item','time','install','arm','count','ordinal')
    fields={name:np.ndarray(shape,dtype=dtype.fields[name][0],buffer=raw,
        offset=offset+dtype.fields[name][1],strides=(dtype.itemsize,)).copy() for name in names}
    del raw
    start=int(datetime(2020,3,1,tzinfo=timezone.utc).timestamp())
    end=int(datetime(2020,6,1,tzinfo=timezone.utc).timestamp())
    rows=[]; folds={}; source_items=set()
    for person in candidate['people']:
        guard()
        uid=person['uid']; group=GROUPS.index(person['group'])
        lo,hi=np.searchsorted(fields['uid'],[uid,uid+1])
        indices=np.arange(lo,hi)
        before=indices[fields['time'][indices]<start]
        current=indices[(fields['time'][indices]>=start)&(fields['time'][indices]<end)]
        assert np.all(np.diff(fields['time'][current])>0)
        by_item=defaultdict(list); previous={}
        for q in before: previous[int(fields['item'][q])]=int(fields['count'][q])
        for position,q in enumerate(current): by_item[int(fields['item'][q])].append(position)
        gaps=[]; eligible=[]
        for item,positions in by_item.items():
            counts=fields['count'][current[positions]].astype(int)
            initial_increment=int(counts[0])-previous[item] if item in previous else int(counts[0])
            if initial_increment!=1:
                gaps.append((-1,positions[0],'prefix',max(0,initial_increment-1)))
            for j in range(1,len(positions)):
                increment=int(counts[j]-counts[j-1])
                if increment!=1:
                    gaps.append((positions[j-1],positions[j],'jump' if increment>1 else 'reset',max(0,increment-1)))
            if item not in previous and len(positions)>1 and counts.tolist()==list(range(1,len(positions)+1)):
                eligible.append((item,positions))
        count_repeats=0
        for item,positions in eligible:
            for rank,right in enumerate(positions):
                left=positions[rank-1] if rank else right
                q=current[right]
                delay=(int(fields['time'][q])-int(fields['time'][current[left]]))/86400.
                other=right-left-1 if rank else 0
                overlaps=[g for g in gaps if g[0]<right and g[1]>left] if rank else []
                cell=(int(np.searchsorted([1/1440,1/24,1,7],delay,side='left')),
                      int(np.searchsorted([1,2,4],rank,side='left')),
                      int(np.searchsorted([0,9,99],other,side='left')))
                row=dict(uid=uid,group=group,item=item,ordinal=int(fields['ordinal'][q]),time=int(fields['time'][q]),
                    prior=rank,delta=delay,other=other,ambiguous=bool(overlaps),
                    prefix=any(g[2]=='prefix' for g in overlaps),internal=any(g[2]!='prefix' for g in overlaps),
                    missing_lower=sum(g[3] for g in gaps if g[2]=='jump' and g[0]>=left and g[1]<=right) if rank else 0,
                    preperiod=person['installation_pre_period'],cell=cell)
                rows.append(row)
                if rank: count_repeats+=1
                if rank and group==0: source_items.add(item)
        assert count_repeats==person['focal_repeat_rows']
        folds[uid]=int(person['hash'][16:24],16)%3
    clean=[r for r in rows if r['group']==0 and r['prior'] and not r['ambiguous']]
    counts=Counter(r['cell'] for r in clean); supporters=defaultdict(set)
    for row in clean: supporters[row['cell']].add(row['uid'])
    cells={cell for cell,n in counts.items() if n>=10 and len(supporters[cell])>=5}
    for row in rows:
        row['primary']=bool(row['prior'] and not row['ambiguous'] and row['cell'] in cells and row['item'] in source_items)
    rows.sort(key=lambda row:(row['uid'],row['time']))
    keys=('uid','group','item','ordinal','time','prior','delta','other','ambiguous','prefix','internal','missing_lower','primary','preperiod')
    data={key:np.array([r[key] for r in rows]) for key in keys}
    saved=npz(AUTHOR/'safe_schedules.npz')
    comparisons={key:bool(np.array_equal(data[key],saved[key])) for key in keys}
    assert all(comparisons.values()), comparisons
    summary={}
    for group,name in enumerate(GROUPS):
        select=data['group']==group; primary=select&data['primary']
        summary[name]={'ids':int(len(np.unique(data['uid'][select]))),'focal_events':int(select.sum()),
            'repeat_rows':int(np.sum(select&(data['prior']>0))),
            'primary_rows':int(primary.sum()),'primary_ids':int(len(np.unique(data['uid'][primary])))}
    assert [summary[n]['primary_rows'] for n in GROUPS]==[1116,485,1472,1432]
    np.savez_compressed(HERE/'independent_schedules.npz',**data)
    write('METADATA_RECONSTRUCTION.json',{'utc':now(),'groups':summary,'fields_exactly_equal_author':comparisons,
        'source_item_bank':sorted(source_items),'folds':folds,'support_cells':sorted(cells),
        'method':'Independent item-position/gap-bracket reconstruction from pinned seven-field projection; candidate IDs inherited, no auxiliary eligibility recertification',
        'answers_interpreted':0,'target_predictions':0,'maxrss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
    state=(HERE/'STATE.md').read_text()
    (HERE/'STATE.md').write_text('**ACTUAL independent metadata calculation saved '+now()+'.** All four primary row/ID counts and all14schedule arrays reconstructed exactly from pinned metadata. Answers0; target predictions0. Jobs0 at phase completion. Numerical prediction/uncertainty review remains in progress.\n\n'+state)
    print(json.dumps({'stage':'independent_metadata','groups':summary,'all14arrays_match':all(comparisons.values()),'answers':0}),flush=True)

def source_answers(data):
    permitted={int(o) for o in data['ordinal'][data['group']<2]}
    path=SOURCE/'opaque_answers/arm_02.tsv.gz'
    raw=read(path)
    assert hashlib.sha256(raw).hexdigest()=='77aa272fb8eaf6f8f253002aa417025e53603bd86415eb2830e91b0c394c9f13'
    # Frozen exact inflation size reserved/charged before decompressing.
    charge(path.relative_to(ROOT),6255236,'entire inflated stream, including blindly discarded bytes')
    answers={}; size=0; lines=0
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
        for line in stream:
            size+=len(line); lines+=1
            assert size<=6255236
            prefix,separator,rest=line.partition(b'\t')
            assert separator
            ordinal=int(prefix)
            if ordinal not in permitted: continue
            correct,separator,opaque=rest.partition(b'\t')
            assert separator and correct in (b'0',b'1',b'0.0',b'1.0')
            assert ordinal not in answers
            answers[ordinal]=float(correct)
    assert size==6255236 and set(answers)==permitted
    result=np.full(len(data['uid']),np.nan)
    for i in np.flatnonzero(data['group']<2): result[i]=answers[int(data['ordinal'][i])]
    assert np.all(np.isnan(result[data['group']>=2]))
    previous=json.loads((HERE/'EXPOSURE.json').read_text()) if (HERE/'EXPOSURE.json').exists() else {}
    write('EXPOSURE.json',{'utc':now(),'source_focal_correct_values_reinterpreted_per_scan':len(answers),
        'cumulative_correct_value_interpretations':previous.get('cumulative_correct_value_interpretations',previous.get('source_focal_correct_values_reinterpreted',0))+len(answers),
        'fit_values':int(np.sum(data['group']==0)),'validation_values':int(np.sum(data['group']==1)),
        'candidate_source_ids_consumed_preserved':90,'full_source_lineage_ids_preserved':91,
        'new_source_ids_exposed':0,'target_correct_values':0,'target_predictions':0,'target_scores':0,
        'auxiliary_or_reply_values':0,'nonrandom_shards':0,'raw_archive_reads':0,'network':0,
        'random_shard_scans':previous.get('random_shard_scans',0)+1,'blind_discarded_inflated_bytes_included':True,'inflated_bytes_per_scan':size,'lines_per_scan':lines})
    return result

def feature_history(data,answers,k):
    feature=np.zeros((len(answers),6)); feature[:,0]=1
    for uid in np.unique(data['uid'][data['group']<2]):
        successes=failures=0.; items={}
        for i in np.flatnonzero(data['uid']==uid):
            item=int(data['item'][i]); good,bad=items.get(item,(0.,0.))
            feature[i,1]=np.log1p(good); feature[i,2]=np.log1p(bad)
            feature[i,3]=np.log1p(data['delta'][i])
            feature[i,4]=np.log(successes+k/2)-np.log(failures+k/2)
            feature[i,5]=np.log1p(data['other'][i])
            value=answers[i]; assert value in (0,1)
            items[item]=(good+value,bad+1-value)
            successes+=value; failures+=1-value
    return feature

def aggregate(value,uid):
    ids,inverse,counts=np.unique(uid,return_inverse=True,return_counts=True)
    return np.bincount(inverse,weights=value)/counts,ids,inverse,counts

def eta(model,Z,index):
    ng=Z.shape[1]
    effects=np.where(index>=0,model['theta'][ng:][np.maximum(index,0)],0.)
    return np.sum(Z*model['theta'][:ng],axis=1)+effects

def hessian(model):
    Z=model['Z']; index=model['index']; ng=Z.shape[1]; nitems=model['nitems']
    p=expit(eta(model,Z,index)); variance=model['weights']*p*(1-p)
    gg=np.einsum('ni,n,nj->ij',Z,variance,Z,optimize=False)+np.diag(model['penalty'][:ng])
    gi=np.array([np.bincount(index,weights=variance*Z[:,j],minlength=nitems) for j in range(ng)])
    ii=np.bincount(index,weights=variance,minlength=nitems)+model['penalty'][ng:]
    schur=gg-np.einsum('ik,jk,k->ij',gi,gi,1/ii,optimize=False)
    return gg,gi,ii,schur

def solve_curvature(model,gradient):
    ng=model['Z'].shape[1]; gg,gi,ii,schur=model['curvature']
    rhs=gradient[:ng]-np.sum(gi*(gradient[ng:]/ii),axis=1)
    globals_=solve(schur,rhs,assume_a='pos',check_finite=True)
    items_=(gradient[ng:]-np.sum(gi*globals_[:,None],axis=0))/ii
    result=np.r_[globals_,items_]
    residual=np.r_[np.sum(gg*globals_,axis=1)+np.sum(gi*items_,axis=1),
        np.sum(gi*globals_[:,None],axis=0)+ii*items_]-gradient
    assert np.max(np.abs(residual))<1e-7
    return result

def gradient_on(model,Z,index,row_derivative):
    seen=index>=0
    return np.r_[np.sum(Z*row_derivative[:,None],axis=0),
        np.bincount(index[seen],weights=row_derivative[seen],minlength=model['nitems'])]

def fit_newton(Z,index,y,uid,lam,nitems):
    guard(); ng=Z.shape[1]
    _,ids,inverse,counts=aggregate(y,uid)
    weights=len(y)/(len(ids)*counts[inverse])
    penalty=np.r_[.04,np.repeat(1/9,ng-1),np.repeat(lam,nitems)]
    theta=np.zeros(ng+nitems); average=np.sum(weights*y)/weights.sum()
    theta[0]=np.log(average/(1-average))
    model=dict(theta=theta,Z=Z,index=index,y=y,uid=uid,weights=weights,penalty=penalty,nitems=nitems)
    def objective(parameters):
        temp=dict(model,theta=parameters); e=eta(temp,Z,index)
        return float(np.sum(weights*(np.logaddexp(0,e)-y*e))+.5*np.sum(penalty*parameters**2))
    for iteration in range(80):
        guard()
        p=expit(eta(model,Z,index))
        gradient=gradient_on(model,Z,index,weights*(p-y))+penalty*model['theta']
        error=float(np.max(np.abs(gradient)))
        if error<1e-7: break
        model['curvature']=hessian(model)
        step=solve_curvature(model,gradient)
        before=objective(model['theta']); descent=float(np.sum(gradient*step)); scale=1.
        while scale>2**-30:
            proposal=model['theta']-scale*step
            if objective(proposal)<=before-1e-4*scale*descent+1e-10: break
            scale/=2
        assert scale>2**-30,'independent Newton line search stalled'
        model['theta']=proposal
    assert error<1e-5,('independent optimizer convergence',error)
    model.update(curvature=hessian(model),gradient_max=error,iterations=iteration,objective=objective(model['theta']))
    return model

def source_influences(pair,gradients):
    vectors=[]; details=[]
    for model,g in zip(pair,gradients):
        if g is None:
            vectors.append(np.zeros(75)); details.append(None); continue
        q=solve_curvature(model,g); Z=model['Z']; ix=model['index']; ng=Z.shape[1]
        projected=np.sum(Z*q[:ng],axis=1)+q[ng:][ix]
        contribution=projected*model['weights']*(model['y']-expit(eta(model,Z,ix)))
        ids,inverse=np.unique(model['uid'],return_inverse=True)
        values=np.bincount(inverse,weights=contribution,minlength=len(ids))
        values-=values.mean(); vectors.append(values)
        details.append({'ids':ids.tolist(),'values':values.tolist()})
    factor=75/74
    variances=[float(factor*np.sum(v*v)) for v in vectors]
    covariance=float(factor*np.sum(vectors[0]*vectors[1]))
    total=float(factor*np.sum((vectors[0]+vectors[1])**2))
    return total,dict(model_variances=variances,cross_covariance=covariance,
        uncoupled_sum=sum(variances),coupled_sum=total,influences=details)

def interval(pair,value,uid,gradients):
    means,ids,_,_=aggregate(value,uid); n=len(ids)
    evaluation=float(np.sum((means-means.mean())**2)/(n*(n-1)))
    source,detail=source_influences(pair,gradients)
    critical=float(student_t.ppf(.975,min(75,n)-1)); se=float(np.sqrt(evaluation+source))
    mean=float(means.mean())
    return dict(mean=mean,lower=mean-critical*se,upper=mean+critical*se,se=se,df=min(75,n)-1,
        evaluation_cluster_variance=evaluation,source_estimation_variance=source,
        people=n,rows=len(value),per_id=[{'uid':int(u),'mean':float(m)} for u,m in zip(ids,means)],
        covariance_detail=detail)

def evaluation(data,y,pair,features,bank,mask):
    assert np.all(data['group'][mask]<2), 'no target predictions'
    uid=data['uid'][mask]; answer=y[mask]
    _,ids,inverse,counts=aggregate(answer,uid); w=1/(len(ids)*counts[inverse])
    index=np.array([bank.get(int(item),-1) for item in data['item'][mask]])
    matrices=[features[mask,:model['Z'].shape[1]] for model in pair]
    logits=[eta(model,Z,index) for model,Z in zip(pair,matrices)]
    probabilities=[expit(e) for e in logits]
    loss=[np.logaddexp(0,e)-answer*e for e in logits]
    gain_grad=[gradient_on(model,Z,index,sign*w*(p-answer)) for model,Z,p,sign in zip(pair,matrices,probabilities,[1,-1])]
    gain=interval(pair,loss[0]-loss[1],uid,gain_grad)
    brier_grad=[gradient_on(model,Z,index,sign*w*2*(p-answer)*p*(1-p)) for model,Z,p,sign in zip(pair,matrices,probabilities,[-1,1])]
    brier=interval(pair,(probabilities[1]-answer)**2-(probabilities[0]-answer)**2,uid,brier_grad)
    calibration=[]
    for j,(model,Z,p,L) in enumerate(zip(pair,matrices,probabilities,loss)):
        gradients=[None,None]; gradients[j]=gradient_on(model,Z,index,w*p*(1-p))
        bias=interval(pair,p-answer,uid,gradients)
        bins=np.searchsorted([.2,.4,.6,.8],p,side='right')
        signed=np.bincount(bins,weights=w*(p-answer),minlength=5)
        calibration.append(dict(bias=bias,absolute_bias_upper95=max(abs(bias['lower']),abs(bias['upper'])),
            fixed_bin_ece=float(np.abs(signed).sum()),equal_id_logloss=float(np.sum(w*L)),
            equal_id_brier=float(np.sum(w*(p-answer)**2))))
    return dict(gain=gain,brier_augmented_minus_baseline=brier,calibration=calibration,
        calibration_gate=bool(all(c['absolute_bias_upper95']<=.1 and c['fixed_bin_ece']<=.1 for c in calibration) and brier['upper']<=.02),
        meaningful_gain_gate=bool(gain['lower']>.01))

def science():
    assert not (HERE/'PREDICTION_RECONSTRUCTION.json').exists(),'science phase already completed'
    data=npz(HERE/'independent_schedules.npz')
    metadata_info=readj(HERE/'METADATA_RECONSTRUCTION.json')
    y=source_answers(data)
    bank={int(item):j for j,item in enumerate(metadata_info['source_item_bank'])}; nitems=len(bank)
    all_index=np.array([bank.get(int(item),-1) for item in data['item']])
    train=(data['group']==0)&(data['prior']>0)
    selected_features=feature_history(data,y,16)
    pair=[fit_newton(selected_features[train,:ng],all_index[train],y[train],data['uid'][train],64,nitems) for ng in (5,6)]
    mask=(data['group']==1)&data['primary']
    primary=evaluation(data,y,pair,selected_features,bank,mask)
    write('EARLY_NUMERICAL.json',{'utc':now(),'primary':primary,
        'independent_optimizer':'block Newton with explicit contractions and backtracking, no author import',
        'gradient_maxima':[m['gradient_max'] for m in pair],
        'fit_objectives':[m['objective'] for m in pair], 'source_correct_values':int(np.sum(data['group']<2)),
        'target_predictions':0})
    (HERE/'STATE.md').write_text('**ACTUAL independent predictions/gate saved '+now()+'.** See EARLY_NUMERICAL.json. Independent block-Newton fit and coupled source covariance implemented without author import. Primary gate '+str(primary['calibration_gate'])+'; gain '+str(primary['gain']['mean'])+'. Full selection/freeze/influence review continuing; one scientific process active.\n\n'+(HERE/'STATE.md').read_text())
    print(json.dumps({'stage':'independent_prediction','gain':primary['gain']['mean'],
        'gain_interval':[primary['gain']['lower'],primary['gain']['upper']],
        'bias_envelopes':[c['absolute_bias_upper95'] for c in primary['calibration']],
        'gate':primary['calibration_gate']}),flush=True)

    # Reconstruct the entire finite inner-fit selection with the independent optimizer.
    folds={int(u):v for u,v in metadata_info['folds'].items()}
    grid=[]; best=None
    fit_ids=np.unique(data['uid'][data['group']==0])
    for k in (4,16,64):
        F=feature_history(data,y,k)
        for lam in (1,8,64):
            values=[[],[]]
            for fold in range(3):
                held=[u for u in fit_ids if folds[int(u)]==fold]
                training=train&~np.isin(data['uid'],held)
                valid=(data['group']==0)&data['primary']&np.isin(data['uid'],held)
                for j,ng in enumerate((5,6)):
                    model=fit_newton(F[training,:ng],all_index[training],y[training],data['uid'][training],lam,nitems)
                    e=eta(model,F[valid,:ng],all_index[valid])
                    loss=np.logaddexp(0,e)-y[valid]*e
                    values[j].extend(aggregate(loss,data['uid'][valid])[0].tolist())
            score=float(.5*(np.mean(values[0])+np.mean(values[1])))
            grid.append(dict(k=k,lambda_=lam,joint_cv_loss=score,baseline_cv_loss=float(np.mean(values[0])),augmented_cv_loss=float(np.mean(values[1]))))
            if best is None or score<best[0]-1e-10: best=(score,k,lam)
            print(json.dumps({'stage':'independent_grid','k':k,'lambda':lam,'joint_loss':score}),flush=True)
    assert best[1:]==(16,64),best
    saved_fit=readj(AUTHOR/'SOURCE_FIT.json'); saved_val=readj(AUTHOR/'SOURCE_VALIDATION.json')
    old_grid=saved_fit['selection']['grid']
    grid_error=max(abs(a['joint_cv_loss']-b['joint_cv_loss']) for a,b in zip(grid,old_grid))
    parameter_errors=[float(np.max(np.abs(model['theta']-np.array(old['theta'])))) for model,old in zip(pair,saved_fit['models'])]
    source_prediction_errors=[]
    for model,old in zip(pair,saved_fit['models']):
        old_model=dict(model,theta=np.array(old['theta'])); ng=model['Z'].shape[1]
        check=(data['group']<2)&(data['prior']>0)
        source_prediction_errors.append(float(np.max(np.abs(expit(eta(model,selected_features[check,:ng],all_index[check]))-expit(eta(old_model,selected_features[check,:ng],all_index[check]))))))
    contrasts={}
    for name in ('gain','brier_augmented_minus_baseline'):
        contrasts[name]={key:float(primary[name][key]-saved_val['primary'][name][key]) for key in ('mean','lower','upper','se','evaluation_cluster_variance','source_estimation_variance')}
    wide=evaluation(data,y,pair,selected_features,bank,(data['group']==1)&(data['prior']>0))
    write('PREDICTION_RECONSTRUCTION.json',{'utc':now(),'primary':primary,'repeat_wide_diagnostic':wide,
        'selection':{'k':16,'lambda':64,'grid':grid,'max_author_joint_grid_loss_error':grid_error},
        'independent_fit':{'optimizer':'block Newton, explicit Hessian contractions, max80iterations, backtracking',
            'parameter_max_abs_difference_from_author':parameter_errors,'source_repeat_probability_max_difference':source_prediction_errors,
            'objectives':[m['objective'] for m in pair],'gradient_maxima':[m['gradient_max'] for m in pair],
            'min_schur_eigenvalues':[float(np.linalg.eigvalsh(m['curvature'][3]).min()) for m in pair],
            'min_item_curvatures':[float(m['curvature'][2].min()) for m in pair]},
        'author_primary_contrast_differences':contrasts,'target_predictions':0,
        'scope':'Source-only conditional reconstruction; no recovered coverage, target work or gate change'})
    # One predeclared contrary diagnostic: precision and deletion influence.
    decomposition=[]
    for c in primary['calibration']:
        bias=c['bias']; half=(bias['upper']-bias['lower'])/2
        eval_half=float(student_t.ppf(.975,bias['df'])*np.sqrt(bias['evaluation_cluster_variance']))
        means=np.array([v['mean'] for v in bias['per_id']])
        decomposition.append(dict(point_bias=bias['mean'],nominal_half_width=half,zero_centered_envelope=half,
            known_source_parameter_half_width=eval_half,zero_bias_would_pass_at_observed_dispersion=bool(half<=.1),
            negative_id_biases=int(np.sum(means<0)),positive_id_biases=int(np.sum(means>0)),
            id_bias_range=[float(means.min()),float(means.max())]))
    deletions=[]
    for uid in np.unique(data['uid'][mask]):
        reduced=evaluation(data,y,pair,selected_features,bank,mask&(data['uid']!=uid))
        deletions.append(dict(omitted_uid=int(uid),remaining_rows=reduced['gain']['rows'],gain=reduced['gain'],
            calibration=reduced['calibration'],calibration_gate=reduced['calibration_gate']))
    id_rows=[]
    for uid in np.unique(data['uid'][mask]):
        member=mask&(data['uid']==uid)
        id_rows.append(dict(uid=int(uid),rows=int(member.sum()),equal_id_weight=.1,
            bias=[next(v['mean'] for v in c['bias']['per_id'] if v['uid']==uid) for c in primary['calibration']],
            gain=next(v['mean'] for v in primary['gain']['per_id'] if v['uid']==uid)))
    write('PRECISION_INFLUENCE.json',{'utc':now(),'plan':'DIAGNOSTIC_PLAN.md','decomposition':decomposition,
        'ids':id_rows,'all_ten_deletions':deletions,'deletion_pass_count':sum(d['calibration_gate'] for d in deletions),
        'interpretation_limit':'Algebraic precision/influence diagnostic; deletions do not revise the frozen cohort/gate; no exact coverage or true-bias guarantee'})
    print(json.dumps({'stage':'independent_science_complete','best':best,'grid_error':grid_error,
        'parameter_errors':parameter_errors,'source_probability_errors':source_prediction_errors,
        'zero_centered_envelopes':[d['zero_centered_envelope'] for d in decomposition],
        'deletion_gate_passes':sum(d['calibration_gate'] for d in deletions),
        'maxrss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}),flush=True)

def audit():
    """Exact frozen-coefficient replay, chronology and numerical reference checks."""
    from scipy import sparse
    assert not (HERE/'FROZEN_AUDIT.json').exists()
    data=npz(HERE/'independent_schedules.npz')
    y=npz(AUTHOR/'source_answers_consumed.npz')['y']
    # Only inherited90-IDsource values; all other entries must be nonvalues.
    assert np.all(np.isnan(y[data['group']>=2]))
    assert np.all(np.isin(y[data['group']<2],[0,1]))
    metadata_info=readj(HERE/'METADATA_RECONSTRUCTION.json')
    old=readj(AUTHOR/'SOURCE_FIT.json'); val=readj(AUTHOR/'SOURCE_VALIDATION.json')
    bank={int(item):j for j,item in enumerate(metadata_info['source_item_bank'])}
    item_index=np.array([bank.get(int(item),-1) for item in data['item']]); nitems=len(bank)
    F=feature_history(data,y,16); training=(data['group']==0)&(data['prior']>0)
    primary=(data['group']==1)&data['primary']
    pair=[]; references=[]; checks=[]
    for j,ng in enumerate((5,6)):
        model=fit_newton(F[training,:ng],item_index[training],y[training],data['uid'][training],64,nitems)
        # Use the actual frozen approximate L-BFGS coefficients to reconstruct
        # the author's executed calculation; own Newton optima are already saved separately.
        model['theta']=np.array(old['models'][j]['theta']); model['curvature']=hessian(model)
        pair.append(model)
        Z=model['Z']; ix=model['index']; probability=expit(eta(model,Z,ix))
        value=model['weights']*probability*(1-probability)
        one=sparse.csr_matrix((np.ones(len(ix)),(np.arange(len(ix)),ix)),shape=(len(ix),nitems))
        design=sparse.hstack([sparse.csr_matrix(Z),one],format='csr')
        full=(design.T@design.multiply(value[:,None])).toarray()+np.diag(model['penalty'])
        gg,gi,ii,schur=model['curvature']
        block=np.block([[gg,gi],[gi.T,np.diag(ii)]])
        max_matrix=float(np.max(np.abs(full-block)))
        ref_gradient=np.linspace(-.1,.1,len(model['theta']))
        direct=solve(full,ref_gradient,assume_a='pos')
        reduced=solve_curvature(model,ref_gradient)
        solve_error=float(np.max(np.abs(direct-reduced)))
        assert max_matrix<1e-8 and solve_error<1e-10
        # Independent finite difference of the frozen equal-IDvalidation gain.
        selected=F[primary,:ng]; evix=item_index[primary]; yy=y[primary]
        _,ids,inverse,counts=aggregate(yy,data['uid'][primary]); w=1/(len(ids)*counts[inverse])
        pp=expit(eta(model,selected,evix))
        gradient=gradient_on(model,selected,evix,w*(pp-yy))
        direction=np.sin(np.arange(len(model['theta']))+.5); direction/=np.linalg.norm(direction)
        step=1e-4
        def score(theta):
            temp=dict(model,theta=theta); e=eta(temp,selected,evix)
            return float(np.sum(w*(np.logaddexp(0,e)-yy*e)))
        numerical=(score(model['theta']+step*direction)-score(model['theta']-step*direction))/(2*step)
        analytic=float(np.sum(gradient*direction))
        references.append(dict(model=j,full_sparse_vs_explicit_Hessian_max_error=max_matrix,
            full_solve_vs_Schur_max_error=solve_error,score_gradient_direction_error=abs(numerical-analytic),
            min_schur_eigenvalue=float(np.linalg.eigvalsh(schur).min()),all_finite=bool(np.isfinite(full).all())))
    replay=evaluation(data,y,pair,F,bank,primary)
    diffs={}
    for name in ('gain','brier_augmented_minus_baseline'):
        diffs[name]={key:float(replay[name][key]-val['primary'][name][key]) for key in ('mean','lower','upper','se','evaluation_cluster_variance','source_estimation_variance')}
    caldiff=[]
    for new,previous in zip(replay['calibration'],val['primary']['calibration']):
        caldiff.append({key:float(new[key]-previous[key]) for key in ('absolute_bias_upper95','fixed_bin_ece','equal_id_logloss','equal_id_brier')})
    assert max(abs(v) for values in diffs.values() for v in values.values())<1e-12
    assert max(abs(v) for values in caldiff for v in values.values())<1e-12
    # Actual source-history chronology spot checks with current/future answers
    # mutated but candidate metadata held fixed. This is a software property,
    # not an assertion of biological/external calibration.
    fit_u=np.unique(data['uid'][data['group']==0]); val_u=np.unique(data['uid'][data['group']==1])
    for uid in list(fit_u[::15])+list(val_u[::3]):
        ix=np.flatnonzero(data['uid']==uid); cutoff=ix[len(ix)//2]
        changed=y.copy(); changed[ix[ix>=cutoff]]=1-changed[ix[ix>=cutoff]]
        altered=feature_history(data,changed,16)
        preceding=ix[ix<=cutoff]
        assert np.array_equal(F[preceding],altered[preceding])
        i=int(cutoff); previous_rows=ix[ix<i]; same=previous_rows[data['item'][previous_rows]==data['item'][i]]
        expected=[np.log1p(y[same].sum()),np.log1p(len(same)-y[same].sum()),
            np.log1p(data['delta'][i]),np.log((y[previous_rows].sum()+8)/(len(previous_rows)-y[previous_rows].sum()+8)),np.log1p(data['other'][i])]
        assert np.max(np.abs(F[i,1:]-expected))<2e-15
        checks.append(dict(uid=int(uid),cutoff_ordinal=int(data['ordinal'][i]),prefix_invariance=True,
            independently_counted_past_values_match=True))
    initial=readj(AUTHOR/'INITIAL_FREEZE.json'); fitfreeze=readj(AUTHOR/'FIT_FREEZE.json')
    access=readj(AUTHOR/'VALIDATION_ACCESS.json')
    pins=json.loads((HERE/'INPUT_PINS.json').read_text())
    freeze_checks=[]
    for path,pin in initial['files'].items():
        if path not in pins:
            read(ROOT/path)
            pins=json.loads((HERE/'INPUT_PINS.json').read_text())
        match=pins[path]['sha256']==pin['sha256']
        assert match
        freeze_checks.append(dict(path=path,sha256=pin['sha256'],matches=True))
    for name,pin in fitfreeze['files'].items():
        path=str((AUTHOR/name).relative_to(ROOT))
        if path not in pins:
            read(AUTHOR/name)
            pins=json.loads((HERE/'INPUT_PINS.json').read_text())
        assert pins[path]['sha256']==pin
        freeze_checks.append(dict(path=path,sha256=pin,matches=True))
    chronology={key:value for key,value in [('initial_freeze',initial['utc']),('source_fit',old['utc']),
        ('fit_freeze',fitfreeze['utc']),('validation_access',access['utc']),('validation_result',val['utc'])]}
    assert list(chronology.values())==sorted(chronology.values())
    assert access['fit_freeze_sha256']==hashlib.sha256((AUTHOR/'FIT_FREEZE.json').read_bytes()).hexdigest()
    write('FROZEN_AUDIT.json',dict(utc=now(),frozen_coefficient_primary=replay,
        author_scalar_differences=diffs,author_calibration_differences=caldiff,numerical_reference_checks=references,
        actual_history_checks=checks,pin_checks=freeze_checks,chronology=chronology,
        chronology_scope='Saved timestamps and executed code ordering agree; no independent OS-level audit of historical access',
        limitations=['No causal/biological state identification','No coverage/null/boundary/effect recovery','No target work'],
        maxrss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    exposure=json.loads((HERE/'EXPOSURE.json').read_text())
    exposure['source_derived_answer_array_additional_loads']=1
    exposure['cumulative_correct_value_interpretations']+=int(np.sum(data['group']<2))
    exposure['nan_target_mask_verified']=True
    write('EXPOSURE.json',exposure)
    print(json.dumps({'stage':'frozen_exact_audit','contrast_differences':diffs,'calibration_differences':caldiff,
        'reference_numerics':references,'actual_history_checks':len(checks),'pins':len(freeze_checks),
        'chronology':chronology,'maxrss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}),flush=True)

def summary():
    # Own output QA is covered by the20MBdocument/code/output envelope.
    r=json.loads((HERE/'PREDICTION_RECONSTRUCTION.json').read_text())
    d=json.loads((HERE/'PRECISION_INFLUENCE.json').read_text())
    g=r['primary']['gain']
    result={'gain':{k:v for k,v in g.items() if k not in ('per_id','covariance_detail')},
        'source_covariance':{k:v for k,v in g['covariance_detail'].items() if k!='influences'},
        'calibration':[{k:v for k,v in c.items() if k!='bias'} for c in r['primary']['calibration']],
        'decomposition':d['decomposition'],
        'deletions':[{'uid':x['omitted_uid'],'gain':[x['gain'][k] for k in ('mean','lower','upper')],
            'bias_envelopes':[c['absolute_bias_upper95'] for c in x['calibration']]} for x in d['all_ten_deletions']],
        'repeat_wide_gain':{k:v for k,v in r['repeat_wide_diagnostic']['gain'].items() if k not in ('per_id','covariance_detail')}}
    write('COMPACT_RESULTS.json',result)
    print(json.dumps(result,indent=2))

def finalize():
    # Own saved-output QA only; no original scientific files are reopened.
    record=json.loads((HERE/'FROZEN_AUDIT.json').read_text())
    metadata_record=json.loads((HERE/'METADATA_RECONSTRUCTION.json').read_text())
    prediction=json.loads((HERE/'PREDICTION_RECONSTRUCTION.json').read_text())
    diagnostic=json.loads((HERE/'PRECISION_INFLUENCE.json').read_text())
    ledger=json.loads((HERE/'ACCOUNTING.json').read_text())
    exposure=json.loads((HERE/'EXPOSURE.json').read_text())
    assert sum(e['bytes'] for e in ledger['entries'])==ledger['charged']==136488919
    assert BASELINE+ledger['charged']==7774826112<8000000000
    assert all(metadata_record['fields_exactly_equal_author'].values())
    assert len(record['pin_checks'])==10 and all(p['matches'] for p in record['pin_checks'])
    assert len(record['actual_history_checks'])==10
    assert not record['frozen_coefficient_primary']['calibration_gate']
    assert prediction['selection']['k']==16 and prediction['selection']['lambda']==64
    assert diagnostic['deletion_pass_count']==0
    assert exposure['random_shard_scans']==2 and exposure['cumulative_correct_value_interpretations']==106119
    assert all(exposure[key]==0 for key in ('target_correct_values','target_predictions','target_scores','auxiliary_or_reply_values','nonrandom_shards','raw_archive_reads','network'))
    assert len((HERE/'COMPLETION_REPORT.md').read_text().split())<=400
    # The audit's final stdout records a slightly higher RSS after JSON serialization
    # than its saved pre-serialization snapshot; preserve that actual observed peak.
    ledger.update(final=True,finalized_utc=now(),maxrss_bytes_macos=max(ledger['maxrss_bytes_macos'],record['maxrss_bytes_macos'],205668352),
        peak_RSS_basis='Maximum actual audit command stdout, including post-output serialization; saved pre-output snapshot was205438976',
        jobs_remaining=0,additional=ledger['charged'],cumulative=BASELINE+ledger['charged'],
        context_QA_envelope_is_conservative=True,unused_scientific_reservation_released=True)
    write('ACCOUNTING.json',ledger)
    exposure.update(utc=now(),final=True,jobs_remaining=0,shared_or_original_files_modified=False,
        all_old_failures_freezes_exposure_preserved=True,
        source_derived_answer_array_correct_values_reinterpreted=35373)
    write('EXPOSURE.json',exposure)
    frozen_decomposition=[]
    for c in record['frozen_coefficient_primary']['calibration']:
        bias=c['bias']
        frozen_decomposition.append(dict(point_bias=bias['mean'],half_width=(bias['upper']-bias['lower'])/2,
            zero_centered_fails=bool((bias['upper']-bias['lower'])/2>.1)))
    state='''# Independent memory source review — completed

**Accept the independently reproduced source calculation/stop; narrow to failed certification and park this fixed candidate. Jobs0.** No target release or successor. Scientific output completed before19:04UTC on2026-10-31, within START18:56:42/deadline19:41:42UTC. Reviewer `01a19352-1977-7192-9401-a1d6bccd4b99`; current PI at closeout `01a1933c-0d2e-7b32-bc71-e1a7b2923c72`.

REVIEW.md/README.md explain the result and exact reproduction. Independent metadata reconstruction matches all14schedule arrays and all four primary count pairs. Independent block-Newton fitting reconstructs54inner fits and the same k16/lambda64selection. Exact frozen-coefficient replay matches primary loss/bias/Brier/uncertainty within1.11e-16. Ten actual-history checks, ten freeze references/chronology, and independent full Hessian/Schur/finite-difference checks pass. Source covariance is preserved; no author estimator import.

Frozen485-review/10-IDgain.007703nat[−.021151,.036557]; absolute-bias envelopes.145088/.122139exceed.10. Both nominal half-widths alone(.117990464/.105356869)also exceed.10at algebraic zero point bias. All ten single-IDdeletions with fixed independently reconstructed source coefficients retain joint failure; no alternative cohort is adopted. Coverage recovery, null/boundary calibration, meaningful-effect sensitivity and all transport remain unrun. Small point biases do not prove calibration; this failure does not prove gross true bias, absent information or equivalence.

Final charge136,488,919additional bytes; exact lineage7,774,826,112/8GB. Conservative20MBcontext/code/QA envelope and all failed-pass/full compressed/inflated/decoded reads included. Two random-shard scans plus one consumed-source answer-array load reinterpret106,119values from the same35,373source focal corrects. All90candidate source IDs/91lineage source IDs remain consumed; no new source IDs. Target values/predictions/scores, reply/auxiliary interpretation, nonrandom shards/archive/network and other protected datasets0. Peak observed scientific RSS205,668,352bytes; one scientific process/one numerical thread; all processes exited/jobs0. No original/shared/frozen files changed.

REVIEWER_FAILURES.md preserves one reviewer unseen-item scorer correction and a denied inline own-output inspection; existing scoped-script execution completed without guard changes. PROPOSED_LEARNING.md is for PI integration, not a concurrent shared-memory edit. COMPLETION_REPORT.md is<=400words. Communication status is recorded separately; send once to CURRENT registry PI without overrides, then finish. This bounded review does not pause the lab or heartbeat. PI owns collection/next allocation.
'''
    (HERE/'STATE.md').write_text(state)
    write('COMMUNICATION_STATUS.json',dict(status='prepared_not_yet_attempted',attempts=0,
        intended_pi='01a1933c-0d2e-7b32-bc71-e1a7b2923c72',report='COMPLETION_REPORT.md',jobs_remaining=0))
    hashes={}
    for path in sorted(HERE.iterdir()):
        if path.is_file() and path.name not in ('OUTPUT_HASHES.json','STATE.md','COMMUNICATION_STATUS.json'):
            raw=path.read_bytes()
            hashes[path.name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    write('OUTPUT_HASHES.json',dict(utc=now(),files=hashes,
        excluded_mutable_closeout_records=['STATE.md','COMMUNICATION_STATUS.json','OUTPUT_HASHES.json']))
    print(json.dumps(dict(status='complete',jobs=0,additional_bytes=ledger['charged'],cumulative_bytes=ledger['cumulative'],
        maxrss=ledger['maxrss_bytes_macos'],frozen_bias_decomposition=frozen_decomposition,
        report_words=len((HERE/'COMPLETION_REPORT.md').read_text().split()),hashed_outputs=len(hashes))),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='metadata': metadata()
    elif sys.argv[1]=='science': science()
    elif sys.argv[1]=='audit': audit()
    elif sys.argv[1]=='summary': summary()
    elif sys.argv[1]=='finalize': finalize()
    else: raise ValueError('unknown phase')
