"""Population gate and paired baseline comparisons, fixed before exposure."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.stats import t as student
from campaign import C, ROOT, MODELS, summarize, digest, event, stamp, verify_freeze, marginal_crps

def intervals(residual,labs):
    """Equal-bin mean; influence handles common observed endpoint missingness.

    Animal interval targets this selected fixed-lab mixture. The additional
    small-G cluster interval is a sensitivity, not arbitrary-lab calibration.
    """
    d=np.asarray(residual,float); n=len(d); nb=d.shape[1]
    valid=np.isfinite(d); counts=valid.sum(0)
    if not np.all(counts): raise ValueError('Empty population bin')
    curve=np.nanmean(d,0); mean=float(curve.mean())
    influence=np.nansum((d-curve)*valid*(n/counts)[None,:],axis=1)/nb
    se=float(influence.std(ddof=1)/np.sqrt(n)); ans=dict(mean=mean,se=se)
    for level in (.90,.95):
        hw=float(student.ppf((1+level)/2,n-1)*se)
        ans['animal_'+str(int(level*100))]=[mean-hw,mean+hw]
    labels=sorted(set(labs)); g=len(labels)
    sums=np.array([influence[np.asarray(labs)==lab].sum() for lab in labels])
    cluster_se=float(np.sqrt(g/(g-1)*np.sum(sums**2))/n) if g>1 else None
    ans['cluster_se']=cluster_se
    for level in (.90,.95):
        hw=float(student.ppf((1+level)/2,g-1)*cluster_se) if g>1 else float('inf')
        ans['cluster_'+str(int(level*100))]=[mean-hw,mean+hw]
    return ans

def gate_summary(observed,predicted,labs,config):
    d=np.asarray(observed)-np.asarray(predicted)
    ci=intervals(d,labs); curve=np.nanmean(d,0)
    lb={lab:float(np.nanmean(d[np.asarray(labs)==lab],axis=0).mean()) for lab in sorted(set(labs))}
    loo={lab:float(np.nanmean(d[np.asarray(labs)!=lab],axis=0).mean()) for lab in sorted(set(labs))}
    count=np.isfinite(d).sum(0)
    checks=dict(
        enough_animals=len(d)>=config['minimum_animals'],
        every_bin_coverage=bool(np.all(count>=config['minimum_bin_fraction']*len(d))),
        scalar_animal90=bool(ci['animal_90'][0]>-config['scalar_margin'] and ci['animal_90'][1]<config['scalar_margin']),
        mean_curve_mae=float(np.abs(curve).mean())<=config['curve_mae_max'],
        max_bin_error=float(np.abs(curve).max())<=config['bin_error_max'],
        each_lab_bias=max(abs(v) for v in lb.values())<=config['lab_bias_max'],
        leave_one_lab_out=max(abs(v) for v in loo.values())<=config['leave_one_lab_out_bias_max'])
    if config.get('require_cluster90',False):
        checks['scalar_cluster90']=bool(ci['cluster_90'][0]>-config['scalar_margin'] and ci['cluster_90'][1]<config['scalar_margin'])
    return dict(intervals=ci,bias_curve=curve.tolist(),curve_mae=float(np.abs(curve).mean()),max_bin_error=float(np.abs(curve).max()),
                lab_scalar_bias=lb,leave_one_lab_out_bias=loo,bin_animals=count.tolist(),checks=checks,pass_gate=all(checks.values()))

def paired_baselines(y,means,draws,seed=202610282,replicates=20000):
    n=len(y); rng=np.random.default_rng(seed); ix=rng.integers(0,n,(replicates,n)); result={}
    yy=np.nanmean(y[ix],1)
    rm=np.nanmean(means['rnn'][ix],1)
    for model in ('growth','persistence'):
        bm=np.nanmean(means[model][ix],1)
        gain=np.abs(yy-bm).mean(1)-np.abs(yy-rm).mean(1)
        cr=np.array([np.nanmean(marginal_crps(draws[model][i],y[i]))-np.nanmean(marginal_crps(draws['rnn'][i],y[i])) for i in range(n)])
        bcr=cr[ix].mean(1)
        result[model]=dict(mean_curve_mae_gain=float(np.abs(np.nanmean(y-means[model],0)).mean()-np.abs(np.nanmean(y-means['rnn'],0)).mean()),
                           mean_curve_mae_gain_interval95=np.quantile(gain,[.025,.975]).tolist(),
                           individual_crps_gain=float(cr.mean()),individual_crps_gain_interval95=np.quantile(bcr,[.025,.975]).tolist())
    return result

def analyze(saved,forecast_dir,config,cohort='source'):
    """Analyze already saved observed arrays; never opens raw data here."""
    subjects=sorted(saved); labs=[saved[s]['lab'] for s in subjects]
    y=np.asarray([saved[s]['observed'] for s in subjects])
    mask=np.isfinite(y[:,:,:2]).all(2); target=np.where(mask,y[:,:,:2].mean(2),np.nan)
    all_draws={}; means={}; secondary={}
    for kind in MODELS:
        arr=[]
        for s in subjects:
            with np.load(forecast_dir/(s+'__'+kind+'.npz'),allow_pickle=False) as z: arr.append(z['samples'][:,:6])
        a=np.asarray(arr)
        if not np.isfinite(a).all(): raise FloatingPointError('Nonfinite forecast cannot abstain')
        da=a[:,:,:,:2].mean(3); all_draws[kind]=da
        means[kind]=np.where(mask,da.mean(1),np.nan)
        observed_curve=np.nanmean(target,0); prediction_curve=np.nanmean(means[kind],0)
        population_draws=np.array([np.mean(da[mask[:,b],:,b],0) for b in range(6)]).T
        ind_crps=[float(np.nanmean(marginal_crps(da[i],target[i]))) for i in range(len(y))]
        diag=[]
        for j in range(4):
            diag.append(dict(metric=j,observed_curve=np.nanmean(y[:,:,j],0).tolist(),forecast_curve=np.mean(a[:,:,:,j],(0,1)).tolist(),
                             marginal_individual_crps=float(np.nanmean([np.nanmean(marginal_crps(a[i,:,:,j],y[i,:,j])) for i in range(len(y))]))))
        se=float(np.sqrt(np.var(da.mean(2),axis=1,ddof=1).sum()/da.shape[1])/len(y))
        secondary[kind]=dict(observed_curve=observed_curve.tolist(),forecast_curve=prediction_curve.tolist(),
                              scalar_observed=float(observed_curve.mean()),scalar_forecast=float(prediction_curve.mean()),conditional_MC_SE=se,
                              individual_crps=float(np.mean(ind_crps)),population_marginal_crps=float(np.mean(marginal_crps(population_draws,observed_curve))),
                              marginal_metrics=diag,**gate_summary(target,means[kind],labs,config))
    comparison=paired_baselines(target,means,all_draws)
    best=min(secondary[m]['curve_mae'] for m in ('growth','persistence'))
    baseline_ok=secondary['rnn']['curve_mae']<=best+config['baseline_mae_noninferiority']
    checks=dict(**secondary['rnn']['checks'],baseline_noninferiority=baseline_ok,known_answer_controls=config['known_answer_controls_valid'])
    result=dict(utc=stamp(),cohort=cohort,subjects=subjects,labs=labs,n=len(subjects),endpoint='equal_side_exact100_correct_including_omission_failures',
                bias_sign='observed minus forecast; positive means underprediction',models=secondary,baseline_comparisons=comparison,
                gate_checks=checks,gate_earned=all(checks.values()),config=config,
                inference_scope='selected source animal mixture conditional on fixed represented labs and realized opportunity histories; not arbitrary new laboratories')
    np.savez_compressed(C/'artifacts/results'/('SOURCE_ARRAYS.npz' if cohort=='source' else 'EXTERNAL_ARRAYS.npz'),subjects=np.array(subjects),labs=np.array(labs),observed=y,counts=np.asarray([saved[s]['counts'] for s in subjects]),**{m+'_means':means[m] for m in MODELS})
    return result

def score_source():
    import mixed_reader as reader
    freeze_path=C/'protocols/FREEZE.json'; freeze=verify_freeze(freeze_path)
    manifest_path=C/'protocols/SOURCE_FORECASTS.json'; manifest=json.loads(manifest_path.read_text())
    if manifest['freeze_sha256']!=digest(freeze_path): raise RuntimeError('Wrong forecast freeze')
    for r in manifest['records']:
        if r.get('eligible') and digest(ROOT/r['path'])!=r['sha256']: raise RuntimeError('Forecast changed')
    saved={}; partial={}; coverage=json.loads((C/'artifacts/coverage/RESULT.json').read_text())
    disposition={r['subject']:r for r in coverage['summaries']}
    folder=C/'artifacts/forecasts/source'
    for subject in freeze['source_subjects']:
        if not disposition[subject]['prefix_complete']: continue
        stop=1000+min(3000,disposition[subject]['full_future_bins']*500)
        full=reader.load_scored(subject,stop=stop,freeze_path=freeze_path,forecast_manifest=manifest_path)
        x,c,_,_=__import__('learning_models').subject_arrays(full)
        observed,counts=summarize(x[1000:],c[1000:])
        np.savez_compressed(folder/(subject+'__observed.npz'),observed=observed[0],counts=counts[0])
        row=dict(lab=disposition[subject]['lab'],observed=observed[0],counts=counts[0])
        (saved if disposition[subject]['primary_complete'] else partial)[subject]=row
    config=json.loads((C/'protocols/GATE_CONFIG.json').read_text())
    result=analyze(saved,folder,config)
    result['partial_subjects']=list(partial)
    result['all26_disposition']=[{k:r[k] for k in ('subject','lab','prefix_complete','primary_complete','total_opportunities','full_future_bins')} for r in coverage['summaries']]
    path=C/'artifacts/results/SOURCE_RESULT.json';path.write_text(json.dumps(result,indent=2)+'\n')
    gate=dict(utc=stamp(),new_population_source_gate_earned=result['gate_earned'],original_individual_gate_earned=False,
              result_path=str(path.relative_to(ROOT)),result_sha256=digest(path),freeze_sha256=digest(freeze_path),
              forecast_manifest_sha256=digest(manifest_path),checks=result['gate_checks'],external_release=result['gate_earned'])
    gp=C/'protocols/SOURCE_GATE.json';gp.write_text(json.dumps(gate,indent=2)+'\n')
    event('prospective_source_population_gate_scored',**gate)
    print(json.dumps(dict(n=result['n'],gate=result['gate_checks'],models={m:{k:result['models'][m][k] for k in ('intervals','curve_mae','max_bin_error','lab_scalar_bias')} for m in MODELS}),indent=2),flush=True)
    return result

if __name__=='__main__':score_source()
