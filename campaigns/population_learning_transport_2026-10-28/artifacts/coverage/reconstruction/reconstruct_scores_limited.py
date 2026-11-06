#!/usr/bin/env python3
"""Independent original-byte reconstruction, runnable only after source release.

No mixed_reader, campaign, learning_models, or score_campaign imports. Direct
Parquet SQL / NPY prefix slices reconstruct native-choice +/-100% numerators,
denominators and omissions. Distributional scores use explicit pair distances.
The frozen original forecast draws and gate configuration are never altered.
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.stats import t
ROOT=Path(__file__).resolve().parents[5]
C=ROOT/'campaigns/population_learning_transport_2026-10-28'
OUT=C/'artifacts/coverage/reconstruction'
MODELS=('rnn','growth','persistence')
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'sources/longitudinal_learning_feasibility_2026-10-28/tools'))

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def dump(path,obj):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(obj,indent=2,default=str)+'\n')
def event(kind,**kw):
    with (C/'protocols/EXPOSURE.jsonl').open('a') as f:
        f.write(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),event=kind,**kw),sort_keys=True)+'\n')
def rows_from_header(path):
    with Path(path).open('rb') as f:
        version=np.lib.format.read_magic(f)
        if version==(1,0):shape,order,dtype=np.lib.format.read_array_header_1_0(f)
        elif version==(2,0):shape,order,dtype=np.lib.format.read_array_header_2_0(f)
        else:raise ValueError('Unrecognized NPY version')
        assert not dtype.hasobject
        assert f.tell()+int(np.prod(shape))*dtype.itemsize==Path(path).stat().st_size
    return int(shape[0])
def independent_sessions(byte_manifest):
    import duckdb
    con=duckdb.connect();sessions={}
    for record in byte_manifest:
        path=ROOT/record['path']
        if not record['verified'] or path.stat().st_size!=record['bytes'] or sha(path)!=record['sha256']:
            raise ValueError('Pinned original bytes changed '+str(path))
        group=sessions.setdefault(record['eid'],dict(subject=record['subject'],lab=record['lab'],date=record['date'],number=record['number'],eid=record['eid'],fields={}))
        assert group['subject']==record['subject']
        group['fields'][record['field']]=path
    for record in sessions.values():
        if 'table' in record['fields']:
            record['rows']=int(con.execute('SELECT num_rows FROM parquet_file_metadata(?)',[str(record['fields']['table'])]).fetchone()[0])
        else:record['rows']=rows_from_header(record['fields']['choice'])
    return sorted(sessions.values(),key=lambda s:(s['subject'],s['date'],s['number'],s['eid']))
def original_rows(subject,sessions,limit):
    import duckdb
    con=duckdb.connect();pieces=[];remaining=limit
    event('independent_original_byte_reconstruction_access',subject=subject,trial_interval=[0,limit],fields=['contrastLeft','contrastRight','choice'],future_access='after saved forecasts and lead source scoring',full_indexed_history_decoded=False)
    for record in sessions:
        if record['subject']!=subject:continue
        n=min(record['rows'],remaining)
        if n<=0:break
        fields=record['fields']
        if 'table' in fields:
            a=np.asarray(con.execute(f'SELECT contrastLeft,contrastRight,choice FROM read_parquet(?) LIMIT {n}',[str(fields['table'])]).fetchall(),dtype=float)
        else:
            a=np.column_stack([np.array(np.load(fields[k],mmap_mode='r',allow_pickle=False)[:n]).reshape(n) for k in ('contrastLeft','contrastRight','choice')])
        assert a.shape==(n,3)
        pieces.append(a);remaining-=n
    a=np.concatenate(pieces)
    assert len(a)==limit and np.isin(a[:,2],[-1,0,1]).all()
    return a

def exact_observation(a):
    future=a[1000:];nb=len(future)//500
    den=np.empty((nb,4),dtype=np.int64);num=np.empty((nb,4),dtype=np.int64);values=np.full((nb,4),np.nan)
    # Native IBL: +1 left choice and -1 right choice. Contrast sign uses
    # missing-side-as-zero only; there is no psychometric stimulus transform.
    for b in range(nb):
        rows=future[500*b:500*(b+1)]
        signed=np.nan_to_num(rows[:,1])-np.nan_to_num(rows[:,0])
        choice=rows[:,2]
        for j,(stim,correct) in enumerate(((-1.,1),(1.,-1))):
            take=np.abs(signed-stim)<=1e-9
            den[b,j]=int(take.sum());num[b,j]=int((take&(choice==correct)).sum())
            if den[b,j]:values[b,j]=num[b,j]/den[b,j]
        den[b,2:]=500;num[b,2]=int((choice==-1).sum());num[b,3]=int((choice==0).sum())
        values[b,2:]=num[b,2:]/500
    return values,den,num

def crps_pairwise(draws,observed):
    draws=np.asarray(draws,float);m=len(draws)
    first=np.abs(draws-observed).mean(0)
    pair=np.abs(draws[:,None]-draws[None,:]).sum(axis=(0,1))/(2*m*(m-1))
    return first-pair

def infer(error,labs):
    error=np.asarray(error,float);n,b=error.shape
    valid=np.isfinite(error);counts=valid.sum(0);curve=np.nanmean(error,0);mean=float(curve.mean())
    influence=np.zeros(n)
    for j in range(b):
        influence+=np.where(valid[:,j],error[:,j]-curve[j],0)*n/counts[j]/b
    se=float(np.sqrt(np.sum((influence-influence.mean())**2)/(n-1)/n))
    labels=sorted(set(labs));g=len(labels)
    sums=np.asarray([influence[np.asarray(labs)==lab].sum() for lab in labels])
    cse=float(np.sqrt(g/(g-1)*sum(sums*sums))/n)
    result=dict(mean=mean,se=se,cluster_se=cse)
    for level in (.90,.95):
        delta=float(t.ppf((1+level)/2,n-1)*se)
        result['animal_'+str(int(level*100))]=[mean-delta,mean+delta]
        delta=float(t.ppf((1+level)/2,g-1)*cse)
        result['cluster_'+str(int(level*100))]=[mean-delta,mean+delta]
    return result

def gate(target,prediction,labs,config):
    errors=target-prediction;curve=np.nanmean(errors,0);intervals=infer(errors,labs)
    subgroup={lab:float(np.nanmean(errors[np.asarray(labs)==lab],0).mean()) for lab in sorted(set(labs))}
    leaveout={lab:float(np.nanmean(errors[np.asarray(labs)!=lab],0).mean()) for lab in sorted(set(labs))}
    counts=np.isfinite(errors).sum(0)
    checks=dict(enough_animals=len(errors)>=config['minimum_animals'],every_bin_coverage=bool((counts>=config['minimum_bin_fraction']*len(errors)).all()),
       scalar_animal90=bool(min(intervals['animal_90'])>-config['scalar_margin'] and max(intervals['animal_90'])<config['scalar_margin']),
       mean_curve_mae=bool(np.abs(curve).mean()<=config['curve_mae_max']),max_bin_error=bool(np.abs(curve).max()<=config['bin_error_max']),
       each_lab_bias=bool(max(map(abs,subgroup.values()))<=config['lab_bias_max']),leave_one_lab_out=bool(max(map(abs,leaveout.values()))<=config['leave_one_lab_out_bias_max']))
    if config.get('require_cluster90',False):checks['scalar_cluster90']=bool(min(intervals['cluster_90'])>-config['scalar_margin'] and max(intervals['cluster_90'])<config['scalar_margin'])
    checks['subgroup_estimates_finite']=bool(np.isfinite(list(subgroup.values())+list(leaveout.values())).all())
    return dict(intervals=intervals,bias_curve=curve.tolist(),curve_mae=float(np.abs(curve).mean()),max_bin_error=float(np.abs(curve).max()),lab_scalar_bias=subgroup,leave_one_lab_out_bias=leaveout,bin_animals=counts.tolist(),checks=checks,pass_gate=all(checks.values()))

def compare_numbers(found,expected,path=''):
    comparisons=[]
    for key,value in found.items():
        at=path+'/'+key
        if key not in expected:raise KeyError('Expected result missing '+at)
        want=expected[key]
        if isinstance(value,dict):comparisons.extend(compare_numbers(value,want,at))
        elif isinstance(value,bool):
            if value!=want:raise AssertionError('Boolean mismatch '+at)
        elif isinstance(value,(float,int,list,np.ndarray)):
            aa=np.asarray(value,dtype=float);bb=np.asarray(want,dtype=float)
            if aa.shape!=bb.shape:raise AssertionError('Shape mismatch '+at)
            if not np.array_equal(np.isnan(aa),np.isnan(bb)):raise AssertionError('NaN mismatch '+at)
            gap=float(np.nanmax(np.abs(aa-bb))) if np.isfinite(aa).any() else 0.
            comparisons.append(dict(quantity=at,max_abs_error=gap))
            if gap>2e-12:raise AssertionError('Numerical mismatch '+at+' '+str(gap))
    return comparisons

def run():
    result_path=C/'artifacts/results/SOURCE_RESULT.json';gate_path=C/'protocols/SOURCE_GATE.json'
    if not result_path.exists() or not gate_path.exists():raise PermissionError('Lead must finish one frozen source score before independent outcome access')
    result=json.loads(result_path.read_text());released=json.loads(gate_path.read_text())
    if sha(result_path)!=released['result_sha256']:raise PermissionError('Lead scored result not pinned in SOURCE_GATE')
    forecast_path=C/'protocols/SOURCE_FORECASTS.json';forecasts=json.loads(forecast_path.read_text());freeze_path=C/'protocols/FREEZE.json'
    if not forecasts.get('all_forecasts_saved_before_scored_outcomes'):raise PermissionError('Whole-cohort forecasts were not frozen')
    assert sha(forecast_path)==released['forecast_manifest_sha256']
    assert sha(freeze_path)==forecasts['freeze_sha256']==released['freeze_sha256']
    frozen=json.loads(freeze_path.read_text())
    for entry in frozen['files']:
        if sha(ROOT/entry['path'])!=entry['sha256']:raise RuntimeError('Frozen input changed '+entry['path'])
    for entry in forecasts['records']:
        if entry.get('eligible'):
            if sha(ROOT/entry['path'])!=entry['sha256']:raise RuntimeError('Forecast bytes changed')
    config=json.loads((C/'protocols/GATE_CONFIG.json').read_text())
    byte_manifest=json.loads((C/'artifacts/coverage/BYTE_MANIFEST.json').read_text())
    sessions=independent_sessions(byte_manifest)
    disposition={s['subject']:s for s in json.loads((C/'artifacts/coverage/RESULT.json').read_text())['summaries']}
    primary=sorted(s for s in disposition if disposition[s]['primary_complete'])
    partial=sorted(s for s in disposition if disposition[s]['prefix_complete'] and not disposition[s]['primary_complete'])
    assert primary==result['subjects'] and len(primary)==24 and partial==['NYU-21']
    observed=[];denominators=[];numerators=[];comparisons=[];partial_result={}
    folder=C/'artifacts/forecasts/source'
    for subject in primary+partial:
        total=sum(s['rows'] for s in sessions if s['subject']==subject)
        n=min(4000,1000+500*((total-1000)//500))
        y,den,num=exact_observation(original_rows(subject,sessions,n))
        with np.load(folder/(subject+'__observed.npz'),allow_pickle=False) as z:
            comparisons.extend(compare_numbers(dict(observed=y,counts=den),dict(observed=z['observed'],counts=z['counts']),subject))
        if subject in primary:
            observed.append(y);denominators.append(den);numerators.append(num)
        else:partial_result[subject]=dict(observed=y.tolist(),denominators=den.tolist(),numerators=num.tolist(),opportunities_read=n)
    labs=[disposition[s]['lab'] for s in primary]
    observed=np.asarray(observed);denominators=np.asarray(denominators);numerators=np.asarray(numerators)
    mask=np.isfinite(observed[:,:,:2]).all(2)
    target=np.where(mask,observed[:,:,:2].mean(2),np.nan)
    draws={};means={};models={}
    for kind in MODELS:
        raw=[]
        for subject in primary:
            with np.load(folder/(subject+'__'+kind+'.npz'),allow_pickle=False) as z:raw.append(z['samples'][:,:6])
        a=np.asarray(raw);assert np.isfinite(a).all()
        draws[kind]=a[:,:,:,:2].mean(3)
        means[kind]=np.where(mask,draws[kind].mean(1),np.nan)
        pc=np.nanmean(means[kind],0);yc=np.nanmean(target,0)
        population=np.column_stack([draws[kind][mask[:,b],:,b].mean(0) for b in range(6)])
        individual=[float(np.nanmean(crps_pairwise(draws[kind][i],target[i]))) for i in range(24)]
        metrics=[]
        for j in range(4):
            metrics.append(dict(metric=j,observed_curve=np.nanmean(observed[:,:,j],0).tolist(),forecast_curve=a[:,:,:,j].mean((0,1)).tolist(),marginal_individual_crps=float(np.nanmean([np.nanmean(crps_pairwise(a[i,:,:,j],observed[i,:,j])) for i in range(24)]))))
        se=float(np.sqrt(np.var(draws[kind].mean(2),axis=1,ddof=1).sum()/draws[kind].shape[1])/24)
        models[kind]=dict(observed_curve=yc.tolist(),forecast_curve=pc.tolist(),scalar_observed=float(yc.mean()),scalar_forecast=float(pc.mean()),conditional_MC_SE=se,individual_crps=float(np.mean(individual)),population_marginal_crps=float(crps_pairwise(population,yc).mean()),marginal_metrics=metrics,**gate(target,means[kind],labs,config))
        # Metrics list compared separately to retain numeric field names.
        comparable={k:v for k,v in models[kind].items() if k!='marginal_metrics'}
        comparisons.extend(compare_numbers(comparable,result['models'][kind],kind))
        for j in range(4):comparisons.extend(compare_numbers(metrics[j],result['models'][kind]['marginal_metrics'][j],kind+'/metric'+str(j)))
    rng=np.random.default_rng(202610282);ix=rng.integers(0,24,(20000,24));yy=np.nanmean(target[ix],1);rm=np.nanmean(means['rnn'][ix],1)
    baseline_comparison={}
    for kind in ('growth','persistence'):
        bm=np.nanmean(means[kind][ix],1)
        gain=np.abs(yy-bm).mean(1)-np.abs(yy-rm).mean(1)
        cr=np.array([np.nanmean(crps_pairwise(draws[kind][i],target[i]))-np.nanmean(crps_pairwise(draws['rnn'][i],target[i])) for i in range(24)])
        bootstrap=cr[ix].mean(1)
        baseline_comparison[kind]=dict(mean_curve_mae_gain=float(np.abs(np.nanmean(target-means[kind],0)).mean()-np.abs(np.nanmean(target-means['rnn'],0)).mean()),mean_curve_mae_gain_interval95=np.quantile(gain,[.025,.975]).tolist(),individual_crps_gain=float(cr.mean()),individual_crps_gain_interval95=np.quantile(bootstrap,[.025,.975]).tolist())
        comparisons.extend(compare_numbers(baseline_comparison[kind],result['baseline_comparisons'][kind],kind+'/comparison'))
    best=min(models[m]['curve_mae'] for m in ('growth','persistence'))
    checks={**models['rnn']['checks'],'baseline_noninferiority':models['rnn']['curve_mae']<=best+config['baseline_mae_noninferiority'],'known_answer_controls':config['known_answer_controls_valid']}
    assert checks==result['gate_checks'] and all(checks.values())==result['gate_earned']==released['new_population_source_gate_earned']
    with np.load(C/'artifacts/results/SOURCE_ARRAYS.npz',allow_pickle=False) as saved:
        assert np.array_equal(saved['subjects'],primary)
        comparisons.extend(compare_numbers(dict(observed=observed,counts=denominators,**{k+'_means':v for k,v in means.items()}),{k:saved[k] for k in saved.files},'SOURCE_ARRAYS'))
    OUT.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(OUT/'RECONSTRUCTED.npz',subjects=np.asarray(primary),observed=observed,denominators=denominators,numerators=numerators,**{k+'_means':v for k,v in means.items()})
    summary=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),status='passed',scope='independent original-byte reconstruction after one frozen source score',subjects=primary,partial=partial_result,never_decoded=['SWC_007'],original_files_verified=len(byte_manifest),source_result_sha256=sha(result_path),source_forecasts_sha256=sha(forecast_path),freeze_sha256=sha(freeze_path),source_code_sha256=sha(__file__),models=models,baseline_comparisons=baseline_comparison,gate_checks=checks,gate_earned=all(checks.values()),comparisons=comparisons,max_abs_error=max(r['max_abs_error'] for r in comparisons),choice_convention='native +1 left,-1 right,0 omission; correct if opposite sign to signed contrast',endpoint='equal side exact100% accuracy, omission failures',crps_formula='explicit sum over all ordered draw pairs, unbiased U-statistic')
    dump(OUT/'RESULT.json',summary)
    event('independent_source_score_reconstruction_complete',result_sha256=sha(OUT/'RESULT.json'),max_abs_error=summary['max_abs_error'],gate_earned=summary['gate_earned'])
    print(json.dumps({k:v for k,v in summary.items() if k not in ('models','comparisons','partial')},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--released',action='store_true',help='explicit lead release required; source scoring and saved forecast gate files also checked')
    args=parser.parse_args()
    if not args.released:parser.error('No outcome access without explicit --released after lead authorization')
    run()
