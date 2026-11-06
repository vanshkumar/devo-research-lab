#!/usr/bin/env python3
"""Independent original-byte reconstruction of frozen source validation.

No lead data reader, trajectory, scoring, or learning-model functions are
imported. External subjects are rejected. Original trial outcomes are read
only after all six frozen forecasts and scoring products exist for a source
subject. This module does not fit or amend any forecast.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, sys, time
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist

C=Path(__file__).resolve().parents[1]
R=Path(__file__).resolve().parents[3]
OUT=C/'artifacts/reconstruction'
FREEZE_SHA='c0141244ac43d240f858956917e3b2b661c72a01a4bddbccdb3974a818b5741f'
MODELS=['dnnglm32','dnnglm','reinforce','reinforce_pure','growth','persistence']
MODEL_PATHS={'dnnglm32':'dnnglm32_nested_best.npz','reinforce':'reinforce_nested_stable.npz'}
FIELDS=['contrastLeft','contrastRight','choice','feedbackType','rewardVolume']

def write_json(path,x):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,indent=2,allow_nan=True)+'\n')

def digest(path,kind='sha256'):
    h=hashlib.new(kind)
    with open(path,'rb')as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def log_exposure(value):
    event=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),**value)
    with open(C/'protocols/EXPOSURE.jsonl','a')as f:f.write(json.dumps(event,sort_keys=True)+'\n')

def verify_freeze():
    p=C/'protocols/FREEZE.json'
    if digest(p)!=FREEZE_SHA:raise PermissionError('Unexpected scientific freeze artifact; stop for lead review')
    fz=json.loads(p.read_text());rows=[]
    for rec in fz['files']:
        actual=digest(C/rec['path']);ok=actual==rec['sha256']
        rows.append(dict(path=rec['path'],expected=rec['sha256'],actual=actual,match=ok))
        if not ok:raise RuntimeError('Frozen scientific artifact changed: '+rec['path'])
    write_json(OUT/'FROZEN_BYTES_VERIFICATION.json',dict(freeze_sha256=FREEZE_SHA,files=rows))
    return fz

def source_allocation():
    split=json.loads((C/'protocols/SPLIT.json').read_text())
    # Explicitly omit every external/dev animal. Source-only task boundary.
    return [r for kind in ['animal_holdout','lab_holdout']for r in split['standard']if r['split']==kind]

def folder_for(split):return C/'artifacts/forecasts'/('source_animals'if split=='animal_holdout'else'source_labs')

def completed(subject,split):
    d=folder_for(split)
    return all((d/(subject+'__'+m+'.npz')).is_file()for m in MODELS)and(d/(subject+'__scores.json')).is_file()and(d/(subject+'__observed.npz')).is_file()

def original_rows(subject,max_rows=6000):
    """Bounded original-byte read; never accepts an external subject."""
    allocation={r['subject']:r for r in source_allocation()}
    if subject not in allocation:raise PermissionError('Independent reader accepts frozen SOURCE holdouts only')
    info=allocation[subject]
    if not completed(subject,info['split']):raise RuntimeError('Wait for all frozen forecasts and scores before reconstructing '+subject)
    index=json.loads((C/'data/INDEX.json').read_text())
    rs=sorted([r for r in index if r['subject']==subject and r['kind']=='table'],key=lambda r:(r['date'],r['number']))
    footer={r['eid']:r['rows']for r in json.loads((C/'data/ROW_COUNTS.json').read_text())}
    downloads={}
    for line in(C/'data/DOWNLOAD_MANIFEST.jsonl').read_text().splitlines():
        r=json.loads(line);downloads[r['dataset_id']]=r
    sys.path.insert(0,str(R/'sources/longitudinal_learning_feasibility_2026-10-28/tools'))
    import duckdb
    con=duckdb.connect();columns={k:[]for k in FIELDS};starts=[];sessions=[];provenance=[];remaining=max_rows
    log_exposure(dict(event='independent_original_byte_source_reconstruction',subject=subject,split=info['split'],
                      freeze_sha256=FREEZE_SHA,scope=f'original indexed task trials[0,{max_rows})oravailable shorter history',
                      fields=FIELDS,all_frozen_forecasts_saved=True,external_outcomes_read=False))
    for i,r in enumerate(rs):
        if remaining<=0:break
        n=min(int(footer[r['eid']]),remaining);remaining-=n
        p=C/r['path'];d=downloads[r['dataset_id']]
        md5=digest(p,'md5');sha=digest(p)
        if not d['verified']or md5!=d['md5']or sha!=d['sha256']or p.stat().st_size!=d['bytes']:
            raise ValueError('Original object hash/byte verification failed '+str(p))
        # Neither data_io nor saved processed NPZs enter this reconstruction.
        query='SELECT '+','.join('"'+f+'"'for f in FIELDS)+f" FROM read_parquet('{p}') LIMIT {n}"
        raw=np.asarray(con.execute(query).fetchall(),float)
        if len(raw)!=n:raise ValueError('Pinned footer/original bytes disagree '+r['eid'])
        for j,k in enumerate(FIELDS):columns[k].append(raw[:,j])
        ss=np.zeros(n,bool)
        if n:ss[0]=True
        starts.append(ss);sessions.append(np.full(n,i,int))
        provenance.append(dict(path=r['path'],dataset_id=r['dataset_id'],session_uuid=r['eid'],date=r['date'],number=r['number'],
                               protocol=r['protocol'],md5=md5,sha256=sha,bytes=p.stat().st_size,
                               cache_md5=r['md5'],bounded_rows=n,footer_rows=footer[r['eid']],query=query))
    data={k:np.concatenate(v)for k,v in columns.items()}
    data['session_start']=np.concatenate(starts);data['session']=np.concatenate(sessions)
    data['choice']=data['choice'].astype(int);data['feedbackType']=data['feedbackType'].astype(int)
    if not np.isin(data['choice'],[-1,0,1]).all():raise ValueError('Unexpected native response code')
    meta=dict(**info,rows_read=len(data['choice']),total_indexed_rows=sum(footer[r['eid']]for r in rs),provenance=provenance)
    return data,meta

def signed(data):
    return np.nan_to_num(data['contrastRight'])-np.nan_to_num(data['contrastLeft'])

def independent_curves(data,prefix=1000,bin_size=500):
    x=signed(data)[prefix:];c=data['choice'][prefix:];B=len(c)//bin_size
    y=np.empty((B,4));counts=np.empty((B,4),int)
    for b in range(B):
        v=x[b*bin_size:(b+1)*bin_size];r=c[b*bin_size:(b+1)*bin_size]
        left=(v<=-.5+1e-9);right=(v>=.5-1e-9)
        nl=int(left.sum());nr=int(right.sum())
        y[b]=[(left&(r==1)).sum()/nl if nl else np.nan,
              (right&(r==-1)).sum()/nr if nr else np.nan,
              np.count_nonzero(r==-1)/bin_size,np.count_nonzero(r==0)/bin_size]
        counts[b]=[nl,nr,bin_size,bin_size]
    return y,counts

def independent_score(samples,observed):
    """Explicit pair-distance CRPS; independently implements all averages."""
    a=np.asarray(samples,float);y=np.asarray(observed,float);n=len(a);valid=np.isfinite(y)
    if a.shape[1:]!=y.shape or not np.isfinite(a[:,valid]).all():raise ValueError('Common observed mask or forecast validity failure')
    cells=np.full(y.shape,np.nan)
    for b,j in zip(*np.where(valid)):
        v=a[:,b,j]
        # pdist enumerates each unordered pair once. No sorted coefficients
        # or lead scoring helper is used; this is the unbiased U statistic.
        cells[b,j]=np.mean(np.abs(v-y[b,j]))-np.sum(pdist(v[:,None],metric='cityblock'))/(n*(n-1))
    bymetric=np.array([np.nanmean(cells[:,j])if valid[:,j].any()else np.nan for j in range(4)])
    mean=np.mean(a,axis=0);error=np.abs(mean-y)
    maes=np.array([np.mean(error[:,j][valid[:,j]])if valid[:,j].any()else np.nan for j in range(4)])
    coverage={};width={};high_coverage={}
    for level in [.5,.8,.95]:
        low=np.quantile(a,(1-level)/2,axis=0);high=np.quantile(a,(1+level)/2,axis=0)
        hit=(y>=low)&(y<=high)
        coverage[str(level)]=float(np.mean(hit[valid]));width[str(level)]=float(np.mean((high-low)[valid]))
        high_coverage[str(level)]=float(np.mean(hit[:,:2][valid[:,:2]]))
    aa=a[:,valid];yy=y[valid]
    energy=float(np.mean(np.sqrt(np.sum((aa-yy)**2,axis=1)))-np.sum(pdist(aa))/(n*(n-1)))
    return dict(crps=float(np.nanmean(bymetric)),crps_by_metric=bymetric.tolist(),mae=float(np.nanmean(maes)),mae_by_metric=maes.tolist(),
                high_accuracy_mae=float(np.nanmean(maes[:2])),coverage=coverage,high_coverage=high_coverage,width=width,energy=energy,n_cells=int(valid.sum()))

def independently_forward(model_path,data,w0):
    """Predict, then update using current choice/reward; source-native coding."""
    with np.load(model_path,allow_pickle=False)as f:params={k:f[k]for k in f.files if k not in ['metadata','kind']};kind=str(f['kind'])
    x=signed(data);c=data['choice'];reward=(data['feedbackType']>0).astype(float);day=data['session_start']
    T=len(c);p=np.empty(T);weights=np.empty((T,3));w=np.asarray(w0,float).copy();den=np.tanh(5.)
    for t in range(T):
        z=np.tanh(5*x[t])/den;phi=np.array([max(z,0.),min(z,0.),1.])
        linear=float(np.dot(w,phi));pt=1./(1.+np.exp(-np.clip(linear,-50,50)))
        p[t]=pt;weights[t]=w
        if c[t]==0:continue
        y=1. if c[t]==-1 else 0.
        if kind=='reinforce':w+=params['alpha']*(reward[t]+params['baseline'])*(y-pt)*phi
        elif kind=='dnnglm':
            cov=np.r_[w,z,1.,float(day[t]),y,reward[t],float(z>0)]
            h1=np.maximum(params['A']@cov+params['a'],0)
            h2=np.maximum(params['B']@h1+params['b'],0)
            w+=params['scale']*(params['C']@h2+params['cc'])
        else:raise ValueError(kind)
    return p,weights,w

def subset(data,start,end=None):return {k:v[start:end]for k,v in data.items()}

def reconstruct_conditionals(subject,folder,data):
    records=[];prefix=subset(data,0,1000);future=subset(data,1000)
    # Existing frozen full-prefix persistence point, evaluated conditionally on
    # the same presented stimuli. This is a diagnostic baseline, never replay
    # of the adaptive schedule inside an autonomous learner.
    static_meta=json.loads((folder/(subject+'__persistence.json')).read_text())
    static_w=np.asarray(static_meta['calibration']['endpoint'],float)
    z=np.tanh(5*signed(future))/np.tanh(5.)
    static_linear=np.column_stack([np.maximum(z,0),np.minimum(z,0),np.ones(len(z))])@static_w
    static_p=1/(1+np.exp(-np.clip(static_linear,-50,50)))
    for name,file in MODEL_PATHS.items():
        meta=json.loads((folder/(subject+'__'+name+'.json')).read_text());cal=meta['calibration']
        model_path=C/'artifacts/models'/file
        pp,pw,endpoint=independently_forward(model_path,prefix,cal['w0'])
        endpoint_error=float(np.max(np.abs(endpoint-np.asarray(cal['endpoint']))))
        p,w,end=independently_forward(model_path,future,endpoint)
        saved_path=folder/(subject+'__'+name+'__conditional.npz')
        with np.load(saved_path,allow_pickle=False)as f:stored_p=f['prob_right'];stored_w=f['weights'];conditional_samples=f['samples']
        if len(p)!=len(stored_p):raise ValueError('Conditional chronology length mismatch')
        prob_error=float(np.max(np.abs(p-stored_p)));weight_error=float(np.max(np.abs(w-stored_w)))
        # Perturb the current response and reward: the same trial's predicted
        # probability is invariant, while later state updates may change.
        altered={k:v.copy()for k,v in future.items()};responded=np.flatnonzero(altered['choice']!=0);t=int(responded[0])if len(responded)else 0
        altered['choice'][t]=-altered['choice'][t]if altered['choice'][t]else 1;altered['feedbackType'][t]*=-1
        ap,aw,_=independently_forward(model_path,subset(altered,0,min(len(p),t+3)),endpoint)
        current_error=float(abs(ap[t]-p[t]));assert current_error==0.
        if endpoint_error>1e-8 or prob_error>1e-8 or weight_error>1e-7:raise ValueError('Independent published recurrence mismatch '+subject+' '+name)
        npz=OUT/'conditional_probabilities'/(subject+'__'+name+'.npz');npz.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(npz,prob_right=p,prefix_prob_right=pp,weights=w)
        for horizon in [1000,3000,5000]:
            h=min(horizon,len(p)//500*500);cc=future['choice'][:h];q=np.clip(p[:h],1e-8,1-1e-8);ok=cc!=0
            ll=-np.mean(np.where(cc[ok]==-1,np.log(q[ok]),np.log1p(-q[ok])))
            sq=np.clip(static_p[:h],1e-8,1-1e-8)
            static_ll=-np.mean(np.where(cc[ok]==-1,np.log(sq[ok]),np.log1p(-sq[ok])))
            observed,_=independent_curves(data)
            curve_diagnostic=independent_score(conditional_samples[:,:h//500],observed[:h//500])
            records.append(dict(subject=subject,model=name,horizon=horizon,actual_horizon=h,full_horizon=len(p)>=horizon,
                     binary_nll=float(ll),static_prefix_binary_nll=float(static_ll),
                     conditional_nll_gain_over_static=float(static_ll-ll),n_responses=int(ok.sum()),prefix_endpoint_max_abs_difference=endpoint_error,
                     future_probability_max_abs_difference=prob_error,future_weight_max_abs_difference=weight_error,
                     current_choice_reward_perturbation_probability_difference=current_error,curve_diagnostic=curve_diagnostic,
                     conditional_artifact_path=str(saved_path.relative_to(C)),conditional_artifact_sha256=digest(saved_path)))
    return records

def reconstruct_subject(subject,info):
    data,meta=original_rows(subject);folder=folder_for(info['split']);observed,counts=independent_curves(data)
    with np.load(folder/(subject+'__observed.npz'),allow_pickle=False)as f:saved_y=f['observed'];saved_counts=f['counts']
    if observed.shape!=saved_y.shape or not np.array_equal(observed,saved_y,equal_nan=True)or not np.array_equal(counts,saved_counts):
        raise ValueError('Independent original targets/counts differ '+subject)
    npz=OUT/'original_targets'/(subject+'.npz');npz.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(npz,observed=observed,counts=counts,choice=data['choice'],signed_contrast=signed(data),feedbackType=data['feedbackType'],session_start=data['session_start'])
    write_json(OUT/'original_provenance'/(subject+'.json'),meta)
    lead=json.loads((folder/(subject+'__scores.json')).read_text());records=[];differences=[];forecast_pins=[]
    H=len(data['choice'])-1000
    for model in MODELS:
        p=folder/(subject+'__'+model+'.npz')
        with np.load(p,allow_pickle=False)as f:primary=f['samples_primary'];raw=f['samples']
        forecast_pins.append(dict(path=str(p.relative_to(C)),sha256=digest(p),particles=len(primary)))
        for horizon in [1000,3000,5000]:
            B=min(horizon//500,len(observed));y=observed[:B]
            for arm,samples in [('autonomous',primary),('raw_autonomous',raw)]:
                sc=independent_score(samples[:,:B],y)
                rec=dict(subject=subject,split=info['split'],lab=info['lab'],model=model,arm=arm,horizon=horizon,
                         actual_horizon=B*500,full_horizon=H>=horizon,**sc);records.append(rec)
                match=[r for r in lead if r['model']==model and r['arm']==arm and r['horizon']==horizon]
                if len(match)!=1:raise ValueError('Missing or duplicate lead score '+subject+' '+model+' '+arm)
                l=match[0]
                delta={k:float(abs(rec[k]-l[k]))for k in ['crps','mae','high_accuracy_mae','energy']}
                delta.update(coverage80=abs(rec['coverage']['0.8']-l['coverage']['0.8']),width80=abs(rec['width']['0.8']-l['width']['0.8']))
                if max(delta.values())>1e-10:raise ValueError('Independent source score mismatch '+repr(delta))
                differences.append(dict(subject=subject,model=model,arm=arm,horizon=horizon,**delta))
    conditional=reconstruct_conditionals(subject,folder,data)
    for r in conditional:
        target=next(x for x in lead if x['model']==r['model']and x['horizon']==r['horizon']and x['arm']=='conditional_diagnostic')
        d=abs(target['binary_nll']-r['binary_nll']);r['lead_binary_nll_abs_difference']=d
        if d>1e-10:raise ValueError('Independent conditional LL mismatch')
        diagnostic=r['curve_diagnostic']
        r['lead_conditional_curve_max_abs_difference']=max(abs(diagnostic[k]-target[k])for k in ['crps','high_accuracy_mae','mae','energy'])
        if r['lead_conditional_curve_max_abs_difference']>1e-10:raise ValueError('Independent conditional diagnostic curve mismatch')
    write_json(OUT/'records'/(subject+'.json'),dict(subject=subject,split=info['split'],lab=info['lab'],
        original_rows_read=len(data['choice']),target_arrays_equal=True,target_counts_equal=True,
        forecast_pins=forecast_pins,scores=records,score_differences=differences,conditionals=conditional))
    return records

def interval(differences,seed=891):
    a=np.asarray(differences,float);rng=np.random.default_rng(seed)
    means=a[rng.integers(0,len(a),(10000,len(a)))].mean(axis=1)
    return dict(n=len(a),mean=float(np.mean(a)),lo95=float(np.quantile(means,.025)),hi95=float(np.quantile(means,.975)),
                gate_lower00625=float(np.quantile(means,.00625)),positive_animals=int(np.sum(a>0)),replicates=10000,seed=seed)

def aggregate():
    allocation=source_allocation();allrows=[];cond=[];diff=[];disposition=[]
    coverage={r['subject']:r for r in json.loads((C/'data/COVERAGE.json').read_text())}
    for a in allocation:
        p=OUT/'records'/(a['subject']+'.json');c=coverage[a['subject']]
        disposition.append(dict(subject=a['subject'],split=a['split'],lab=a['lab'],indexed_trials=c['trials'],
                           prefix1000_complete=c['trials']>=1000,has_future500=c['trials']>=1500,
                           primary3000_complete=c['trials']>=4000,secondary5000_complete=c['trials']>=6000,reconstructed=p.exists()))
        if p.exists():
            r=json.loads(p.read_text());allrows.extend(r['scores']);cond.extend(r['conditionals']);diff.extend(r['score_differences'])
    # Keep split then alphabetical subject order explicit for finite-bootstrap replay.
    order=[a['subject']for split in ['animal_holdout','lab_holdout']for a in sorted(allocation,key=lambda a:a['subject'])if a['split']==split]
    allrows.sort(key=lambda r:(order.index(r['subject']),r['model'],r['arm'],r['horizon']))
    summaries=[];comparisons=[];labs=[]
    for horizon in [1000,3000,5000]:
        for arm in ['autonomous','raw_autonomous']:
            for full in [True,False]:
                rr=[r for r in allrows if r['horizon']==horizon and r['arm']==arm and(r['full_horizon']or not full)]
                for model in MODELS:
                    m=[r for r in rr if r['model']==model]
                    if not m:continue
                    summaries.append(dict(model=model,arm=arm,horizon=horizon,full_only=full,n=len(m),
                         **{k:float(np.mean([r[k]for r in m]))for k in ['crps','high_accuracy_mae','mae','energy']},
                         coverage80=float(np.mean([r['coverage']['0.8']for r in m])),
                         high_coverage80=float(np.mean([r['high_coverage']['0.8']for r in m])),
                         width80=float(np.mean([r['width']['0.8']for r in m]))))
                if horizon!=3000 or arm!='autonomous' or not full:continue
                by={(r['subject'],r['model']):r for r in rr}
                for candidate in MODELS[:4]:
                    for baseline in ['growth','persistence']:
                        ids=[s for s in order if(s,candidate)in by and(s,baseline)in by]
                        delta=[by[(s,baseline)]['crps']-by[(s,candidate)]['crps']for s in ids]
                        if not ids:continue
                        comparisons.append(dict(candidate=candidate,baseline=baseline,animal_order=ids,
                            score_gain=interval(delta),relative_crps_gain=float(np.mean(delta)/np.mean([by[(s,baseline)]['crps']for s in ids])),
                            relative_high_accuracy_mae_gain=float(1-np.mean([by[(s,candidate)]['high_accuracy_mae']for s in ids])/np.mean([by[(s,baseline)]['high_accuracy_mae']for s in ids]))))
                for label in sorted(set(r['lab']for r in rr)) + ['reserved_labs_combined','animal_holdout_combined']:
                    group=[r for r in rr if r['lab']==label or(label=='reserved_labs_combined'and r['split']=='lab_holdout')or(label=='animal_holdout_combined'and r['split']=='animal_holdout')]
                    for model in MODELS:
                        mm=[r for r in group if r['model']==model]
                        if mm:labs.append(dict(group=label,model=model,n=len(mm),crps=float(np.mean([r['crps']for r in mm])),high_accuracy_mae=float(np.mean([r['high_accuracy_mae']for r in mm])),coverage80=float(np.mean([r['coverage']['0.8']for r in mm]))))
    write_json(OUT/'SOURCE_DISPOSITION.json',disposition);write_json(OUT/'INDEPENDENT_SCORES.json',allrows)
    write_json(OUT/'INDEPENDENT_SUMMARY.json',summaries);write_json(OUT/'PAIRED_COMPARISONS.json',comparisons);write_json(OUT/'LAB_STRATA.json',labs)
    write_json(OUT/'CONDITIONAL_RECONSTRUCTION.json',cond);write_json(OUT/'NUMERICAL_DIFFERENCES.json',dict(
        records=len(diff),max_by_stat={k:max([r[k]for r in diff],default=0.)for k in ['crps','mae','high_accuracy_mae','energy','coverage80','width80']},
        reconstructed_animals=sum(r['reconstructed']for r in disposition),allocated_source_animals=len(disposition),external_outcomes_read=False))
    return disposition,summaries

def exposure_order_audit():
    """Audit append-only save/read order without opening any new outcomes."""
    events=[json.loads(l)for l in(C/'protocols/EXPOSURE.jsonl').read_text().splitlines()]
    rows=[]
    for a in source_allocation():
        s=a['subject'];reads=[i for i,e in enumerate(events)if e.get('subject')==s and e.get('split')==a['split']and e.get('event')in['open_outcomes','load_processed_outcomes']]
        if not reads:continue
        first=min(reads)
        saved={e.get('model')for e in events[:first]if e.get('subject')==s and e.get('event')=='autonomous_forecast_saved'}
        missing=set(MODELS)-saved
        if missing:raise AssertionError('Future outcome access before all frozen forecasts: '+s+repr(missing))
        prefix=[i for i,e in enumerate(events[:first])if e.get('subject')==s and e.get('event')=='open_prefix_only_outcomes']
        rows.append(dict(subject=s,split=a['split'],six_models_saved_before_first_full_outcome_read=True,prefix_only_read_before_future=bool(prefix),
                         first_future_read_event_index=first,last_prefix_read_event_index=max(prefix)if prefix else None))
    external=[e for e in events if e.get('split')=='external'and e.get('event')in['open_outcomes','load_processed_outcomes','open_prefix_only_outcomes']]
    if external:raise AssertionError('External outcome access found while source-only reconstruction expected')
    write_json(OUT/'FORECAST_BEFORE_SCORE_AUDIT.json',dict(source_subjects=rows,external_outcome_access_events=0,
                note='Main scoring conversion loads whole source tables after forecast saving, then scores its first5000futuretrials. Independent reconstruction opens only first6000originalrows.'))

def main():
    p=argparse.ArgumentParser();p.add_argument('--subject');p.add_argument('--collect-only',action='store_true');p.add_argument('--overwrite',action='store_true')
    args=p.parse_args();OUT.mkdir(parents=True,exist_ok=True);verify_freeze()
    if not args.collect_only:
        for a in source_allocation():
            s=a['subject']
            if args.subject and s!=args.subject:continue
            path=OUT/'records'/(s+'.json')
            if path.exists()and not args.overwrite:continue
            if not completed(s,a['split']):continue
            start=time.monotonic();reconstruct_subject(s,a);print(json.dumps(dict(subject=s,split=a['split'],seconds=round(time.monotonic()-start,2))),flush=True)
    disposition,summary=aggregate();exposure_order_audit();print(json.dumps(dict(reconstructed=sum(r['reconstructed']for r in disposition),source_allocated=len(disposition),source_prefix_and_future=sum(r['has_future500']for r in disposition),source_full_primary=sum(r['primary3000_complete']for r in disposition))),flush=True)

if __name__=='__main__':main()
