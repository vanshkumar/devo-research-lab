#!/usr/bin/env python3
"""Bounded variance calibration from reserved DEVELOPMENT-CV animals only.

Shared candidate amplitudes:0,.5,1. Selection minimizes independent-animal
leave-one-out primary-horizon CRPS. No empirical source holdout or external
outcome may be supplied to this fitting module. The learned update laws and
their unadjusted means remain archived; clipping-induced shifts are measured.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json
from pathlib import Path
import numpy as np
from evaluation import apply_discrepancy,score,paired_interval

CAMPAIGN=Path(__file__).resolve().parents[1]
DEFAULT_FORECASTS=CAMPAIGN/'artifacts/forecasts/dev_pilot'
OUT=CAMPAIGN/'artifacts/calibration'
DEFAULT_CONFIG=OUT/'CONFIG.json'

def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')

def cv_ids():
    split=json.loads((CAMPAIGN/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json').read_text())
    return split.get('validation',split.get('val',split.get('validation_subjects')))

def seed_for(subject,base=20261675):
    return base+int(hashlib.sha256(subject.encode()).hexdigest()[:7],16)

def shift_components(raw,residuals,seed,scale):
    """Separate finite donor sampling and clipping contributions to mean shift."""
    raw=np.asarray(raw,float);r=np.asarray(residuals,float)[:,:raw.shape[1]]
    center=np.nanmean(r,axis=0);rr=np.nan_to_num(r-center)
    rng=np.random.default_rng(seed);delta=rr[rng.integers(len(rr),size=len(raw))]
    unc=raw+scale*delta;cal=np.clip(unc,0,1)
    total=np.mean(cal,axis=0)-np.mean(raw,axis=0)
    clipping=np.mean(cal-unc,axis=0);sampling=np.mean(unc-raw,axis=0)
    return dict(mean_abs_total_shift=float(np.mean(np.abs(total))),
                max_abs_total_cell_shift=float(np.max(np.abs(total))),
                mean_signed_total_shift_by_metric=np.mean(total,axis=0).tolist(),
                mean_abs_clipping_shift=float(np.mean(np.abs(clipping))),
                mean_signed_clipping_shift_by_metric=np.mean(clipping,axis=0).tolist(),
                mean_abs_finite_sampling_shift=float(np.mean(np.abs(sampling))))

def load_development(forecast_dir,models=None):
    forecast_dir=Path(forecast_dir)
    allowed=set(cv_ids());observations={};sources=[]
    for p in sorted(forecast_dir.glob('*__observed.npz')):
        subject=p.stem.split('__')[0]
        if subject not in allowed:raise PermissionError('Not a reserved development-CV animal: '+subject)
        with np.load(p,allow_pickle=False) as z:y=np.asarray(z['observed'],float)
        observations[subject]=y;sources.append(dict(subject=subject,role='development_observed_curve',path=str(p.relative_to(CAMPAIGN)),sha256=sha256(p)))
    if not observations:raise ValueError('No development observations')
    if models is None:
        candidates=set()
        for p in forecast_dir.glob('*__*.npz'):
            pieces=p.stem.split('__')
            if len(pieces)==2 and pieces[1]!='observed':candidates.add(pieces[1])
        # Partial arrival of a new candidate does not silently reduce the
        # common calibration population. Explicitly fit it once complete.
        models=[m for m in sorted(candidates) if all((forecast_dir/(s+'__'+m+'.npz')).exists() for s in observations)]
    forecasts={}
    for model in models:
        forecasts[model]={}
        for subject,y in observations.items():
            p=forecast_dir/(subject+'__'+model+'.npz')
            if not p.exists():raise FileNotFoundError('Wait for every development candidate forecast: '+str(p))
            j=p.with_suffix('.json')
            if j.exists() and json.loads(j.read_text()).get('split') not in [None,'dev']:
                raise PermissionError('Calibration forecast metadata is not development: '+str(j))
            with np.load(p,allow_pickle=False)as z:a=np.asarray(z['samples'],float)
            if a.ndim!=3 or a.shape[1:]!=y.shape:raise ValueError((subject,model,a.shape,y.shape))
            if not np.isfinite(a[:,np.isfinite(y)]).all():raise FloatingPointError('Nonfinite forecast on recorded development target')
            forecasts[model][subject]=a
            sources.append(dict(subject=subject,model=model,role='development_autonomous_samples',path=str(p.relative_to(CAMPAIGN)),sha256=sha256(p)))
    return observations,forecasts,sources

def fit_uncertainty(forecast_dir=None,out_dir=None,models=None,scales=(0.,.5,1.),primary_bins=6,seed_base=20261675):
    forecast_dir=Path(forecast_dir or DEFAULT_FORECASTS);out_dir=Path(out_dir or OUT);out_dir.mkdir(parents=True,exist_ok=True)
    observations,forecasts,sources=load_development(forecast_dir,models)
    subjects=sorted(observations);max_bins=max(len(y) for y in observations.values())
    config_path=out_dir/'CONFIG.json'
    config=json.loads(config_path.read_text()) if config_path.exists() else dict(version=1,models={})
    records=[];summaries=[];comparisons=[]
    for model,aa in forecasts.items():
        residual=np.full((len(subjects),max_bins,4),np.nan)
        for i,s in enumerate(subjects):residual[i,:len(observations[s])]=observations[s]-np.mean(aa[s],axis=0)
        model_records=[]
        for i,s in enumerate(subjects):
            available=len(observations[s]);B=min(primary_bins,available)
            others=np.delete(residual,i,axis=0)
            if len(others)<2:raise ValueError('Too few independent development residual donors')
            raw=aa[s][:,:B];y=observations[s][:B];seed=seed_for(s,seed_base)
            for scale in scales:
                cal=apply_discrepancy(raw,others,seed=seed,scale=scale)
                sc=score(cal,y);shift=shift_components(raw,others,seed,scale)
                model_records.append(dict(subject=s,model=model,scale=scale,seed=seed,
                    primary_horizon=primary_bins*500,available_horizon=B*500,full_primary_horizon=available>=primary_bins,
                    loo_donor_subjects=[x for x in subjects if x!=s],**sc,**shift))
        scores={float(scale):float(np.mean([r['crps']for r in model_records if r['scale']==scale and r['full_primary_horizon']]))for scale in scales}
        # Stable lower-amplitude tie break. Candidate set is fixed in advance.
        chosen=min(scales,key=lambda x:(scores[float(x)],float(x)))
        bank_path=out_dir/(model+'_residuals.npz')
        np.savez_compressed(bank_path,residuals=residual,subjects=np.array(subjects),valid=np.isfinite(residual),
                            primary_bins=np.array(primary_bins),bin_size=np.array(500),selected_scale=np.array(chosen))
        entry=dict(selected_scale=float(chosen),selection='minimum equal-animal LOO CRPS at first3000futuretrials;tiespreferloweramplitude',
                   candidate_scales=[float(x)for x in scales],primary_horizon=primary_bins*500,
                   loo_crps_by_scale={str(k):v for k,v in scores.items()},
                   n_residual_donors=len(subjects),n_primary_scored=sum(len(y)>=primary_bins for y in observations.values()),
                   calibration_seed_base=int(seed_base),calibration_seed_rule='seed_base + integer(first7hexSHA256(subject))',
                   n_cell_donors=np.isfinite(residual).sum(axis=0).tolist(),
                   donor_subjects=subjects,residual_bank_path=str(bank_path.relative_to(CAMPAIGN)),residual_bank_sha256=sha256(bank_path),
                   residual_definition='observedcurve minus raw forecast sample mean;center donors perbin/metric before sampling;missing donor cells map to centered0',
                   update_rule_changed=False,mean_adjustment='none before clipping;all clipping and finite-sampling mean shifts recorded',
                   source_manifest_path=str((out_dir/(model+'_SOURCE_MANIFEST.json')).relative_to(CAMPAIGN)))
        config['models'][model]=entry
        write_json(out_dir/(model+'_SOURCE_MANIFEST.json'),[r for r in sources if r.get('model')in[None,model]])
        write_json(out_dir/(model+'_LOO_RECORDS.json'),model_records)
        for scale in scales:
            rr=[r for r in model_records if r['scale']==scale and r['full_primary_horizon']]
            row=dict(model=model,scale=float(scale),selected=float(scale)==chosen,n=len(rr),
                    **{k:float(np.mean([r[k]for r in rr])) for k in ['crps','mae','high_accuracy_mae','energy','mean_abs_total_shift','mean_abs_clipping_shift','mean_abs_finite_sampling_shift']},
                    coverage80=float(np.mean([r['coverage']['0.8']for r in rr])),
                    coverage95=float(np.mean([r['coverage']['0.95']for r in rr])),
                    width80=float(np.mean([r['width']['0.8']for r in rr])),
                    mean_signed_shift_by_metric=np.mean([r['mean_signed_total_shift_by_metric']for r in rr],axis=0).tolist(),
                    mean_signed_clipping_shift_by_metric=np.mean([r['mean_signed_clipping_shift_by_metric']for r in rr],axis=0).tolist())
            summaries.append(row)
        selected={r['subject']:r for r in model_records if r['scale']==chosen and r['full_primary_horizon']}
        raw={r['subject']:r for r in model_records if r['scale']==0 and r['full_primary_horizon']}
        comparisons.append(dict(model=model,chosen_scale=float(chosen),raw_minus_selected_crps=paired_interval([raw[s]['crps']-selected[s]['crps']for s in selected]),
                                scope='Development calibration selection;not independent validation.'))
        records.extend(model_records)
        print(json.dumps(dict(model=model,selected_scale=float(chosen),loo_crps=scores)),flush=True)
    config.update(dict(frozen_from='reserved development-CV outcomes only',forecast_dir=str(forecast_dir.relative_to(CAMPAIGN)),
                       last_fit_utc=dt.datetime.now(dt.timezone.utc).isoformat(),source_holdout_outcomes_used=False,external_outcomes_used=False,
                       application='apply_calibration(samples,model_name,seed,config_path)'))
    write_json(config_path,config)
    # Per-model files allow candidate arrival without deleting earlier records.
    for model in forecasts:
        write_json(out_dir/(model+'_LOO_SUMMARY.json'),[r for r in summaries if r['model']==model])
        write_json(out_dir/(model+'_LOO_COMPARISON.json'),next(r for r in comparisons if r['model']==model))
    collect(out_dir)
    # Input forecast bytes must not change while residuals are being fitted.
    for r in sources:
        if sha256(CAMPAIGN/r['path'])!=r['sha256']:raise RuntimeError('Development forecast changed during calibration: '+r['path'])
    from data_io import exposure
    exposure(dict(event='development_uncertainty_calibration',subjects=subjects,models=list(forecasts),
                  method='LOO residual widening only;fixed scale candidates0,.5,1',scope='saved devCV observable curves',
                  config_path=str(config_path.relative_to(CAMPAIGN)),source_validation_outcomes_read=False,external_outcomes_read=False))
    return config

def collect(out_dir=None):
    out_dir=Path(out_dir or OUT);summary=[];records=[];comparisons=[]
    for p in sorted(out_dir.glob('*_LOO_SUMMARY.json')):summary.extend(json.loads(p.read_text()))
    for p in sorted(out_dir.glob('*_LOO_RECORDS.json')):records.extend(json.loads(p.read_text()))
    for p in sorted(out_dir.glob('*_LOO_COMPARISON.json')):comparisons.append(json.loads(p.read_text()))
    write_json(out_dir/'LOO_SUMMARY.json',summary);write_json(out_dir/'LOO_RECORDS.json',records);write_json(out_dir/'LOO_COMPARISONS.json',comparisons)
    return summary

def apply_calibration(samples,model_name,seed,config_path=None):
    """Consume a frozen development variance calibration; no outcome argument."""
    config_path=Path(config_path or DEFAULT_CONFIG);config=json.loads(config_path.read_text())
    entry=config['models'][model_name];path=CAMPAIGN/entry['residual_bank_path']
    if sha256(path)!=entry['residual_bank_sha256']:raise ValueError('Frozen residual-bank hash mismatch '+str(path))
    with np.load(path,allow_pickle=False)as z:r=z['residuals']
    if np.asarray(samples).shape[1]>r.shape[1]:raise ValueError('Forecast exceeds frozen residual-bank horizon')
    return apply_discrepancy(samples,r,seed=seed,scale=entry['selected_scale'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--models');p.add_argument('--forecast-dir');p.add_argument('--out-dir');p.add_argument('--collect-only',action='store_true');p.add_argument('--seed-base',type=int,default=20261675)
    a=p.parse_args()
    if a.collect_only:collect(a.out_dir)
    else:fit_uncertainty(a.forecast_dir,a.out_dir,a.models.split(',')if a.models else None,seed_base=a.seed_base)

if __name__=='__main__':main()
