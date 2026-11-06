#!/usr/bin/env python3
"""Restartable forecasts with outcomes separated from prefix/opportunity access.

For protected cohorts, forecast files are written before the scoring loader is
called. A validation freeze is compulsory; the external gate is separate.
"""
import argparse, hashlib, json, time
from pathlib import Path
import numpy as np
from data_io import load_subject, subjects, exposure
from learning_models import load_model, subject_arrays
from baselines import load_bank, fit_bank, subset
from rollout import autonomous, conditional, trajectory_summary, METRICS
from evaluation import score, paired_interval, apply_discrepancy

CAMP=Path(__file__).resolve().parents[1]
MODEL_FILES={
 'dnnglm':CAMP/'artifacts/models/dnnglm_nested_best.npz',
 'dnnglm32':CAMP/'artifacts/models/dnnglm32_nested_best.npz',
 'reinforce':CAMP/'artifacts/models/reinforce_nested_stable.npz',
 'reinforce_pure':CAMP/'artifacts/models/reinforce_pure_nested.npz',
}
BANK=CAMP/'artifacts/baselines/nested_growth_bank.npz'


def save_json(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,allow_nan=True)+'\n')


def model_split():return json.loads((CAMP/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json').read_text())


def development_bank():
    ms=model_split()
    train=ms.get('train',ms.get('train_subjects',ms.get('training')))
    if train is None:raise KeyError(ms.keys())
    animals={s:load_subject(s,purpose='matched baseline bank; nested training animals only') for s in train}
    return fit_bank(animals,BANK)


def seed_for(subject,base=20261028):
    return base+int(hashlib.sha256(subject.encode()).hexdigest()[:7],16)


def get_prefix(subject,split,horizon,freeze=None,gate=None):
    if split=='dev':
        data=load_subject(subject,purpose='development forecast calibration/scoring')
        if len(data['choice'])<1000:return None,None,dict(n_trials=len(data['choice']))
        H=min(horizon,(len(data['choice'])-1000)//500*500)
        return subset(data,0,1000),data['session_start'][1000:1000+H],dict(n_trials=len(data['choice']))
    from data_io import load_prefix_and_opportunities
    return load_prefix_and_opportunities(subject,split,prefix_n=1000,horizon=horizon,freeze_path=freeze,external_gate_path=gate)


def forecast_subject(subject,split,tag,names,n_particles=256,horizon=5000,freeze=None,gate=None,
                     protocol='standard',neighbors=15,overwrite=False,model_files=None,
                     trainer_options=None,calibration_method='map',omission_mode='growth',
                     calibration_path=None):
    bank=load_bank(BANK);folder=CAMP/'artifacts/forecasts'/tag;folder.mkdir(parents=True,exist_ok=True)
    prefix,starts,meta=get_prefix(subject,split,horizon,freeze,gate)
    if prefix is None or starts is None or len(starts)<500:
        save_json(folder/(subject+'_ineligible.json'),dict(**{**meta,'subject':subject,'split':split,'reason':'fewer than1000prefix+500futureopportunities'}))
        return []
    H=len(starts);records=[];base=seed_for(subject)
    # Save every autonomous forecast before opening actual future outcomes.
    for name in names:
        path=folder/(subject+'__'+name+'.npz')
        if path.exists() and not overwrite:continue
        competence=name if name in ('persistence','growth') else None
        model=None if competence else load_model((model_files or MODEL_FILES)[name])
        t0=time.monotonic()
        result=autonomous(model,prefix,starts,bank,n_particles=n_particles,seed=base,
                          protocol=protocol,subject=subject,competence=competence,neighbors=neighbors,
                          calibration_method=calibration_method,omission_mode=omission_mode,
                          trainer_options=trainer_options)
        primary=result['samples']
        if calibration_path:
            from uncertainty import apply_calibration
            primary=apply_calibration(primary,name,base+647,config_path=calibration_path)
        np.savez_compressed(path,samples=result['samples'],weights=result['weights'],counts=result['counts'],
                            samples_primary=primary,pool_fraction=result['pool_fraction'],seed=np.array(base),session_start=starts)
        save_json(path.with_suffix('.json'),dict(subject=subject,split=split,model=name,mode=result['mode'],
                 n_particles=n_particles,prefix_n=1000,horizon=H,neighbors=neighbors,
                 conditional_on='realized session opportunities only',calibration=result['calibration'],
                 uncertainty_config_sha256=hashlib.sha256(Path(calibration_path).read_bytes()).hexdigest() if calibration_path else None,
                 model_sha256=hashlib.sha256(Path((model_files or MODEL_FILES)[name]).read_bytes()).hexdigest() if not competence else None,
                 trainer=result['initial_trainer'],seconds=time.monotonic()-t0,metadata=meta))
        exposure(dict(event='autonomous_forecast_saved',subject=subject,split=split,model=name,
                      path=str(path.relative_to(CAMP)),future_outcomes_assimilated=False))
    future=load_subject(subject,split,purpose='score forecasts already saved; conditional diagnostic',
                        freeze_path=freeze,external_gate_path=gate)
    future=subset(future,1000,1000+H)
    s,c,_,_=subject_arrays(future);observed,counts=trajectory_summary(s,c)
    np.savez_compressed(folder/(subject+'__observed.npz'),observed=observed[0],counts=counts[0])
    for name in names:
        path=folder/(subject+'__'+name+'.npz');z=np.load(path)
        for hh in [1000,3000,5000]:
            B=min(hh//500,H//500);a=z['samples_primary'][:,:B] if 'samples_primary' in z else z['samples'][:,:B];y=observed[0,:B]
            if B==0:continue
            full=H>=hh
            rec=dict(subject=subject,split=split,model=name,arm='autonomous',horizon=hh,
                     actual_horizon=B*500,full_horizon=full,**score(a,y))
            records.append(rec)
            if calibration_path:
                records.append(dict(subject=subject,split=split,model=name,arm='raw_autonomous',horizon=hh,
                     actual_horizon=B*500,full_horizon=full,**score(z['samples'][:,:B],y)))
        if name not in ('persistence','growth'):
            model=load_model((model_files or MODEL_FILES)[name])
            con=conditional(model,prefix,future,bank,n_particles=n_particles,seed=base,subject=subject,
                            calibration_method=calibration_method,omission_mode=omission_mode)
            np.savez_compressed(folder/(subject+'__'+name+'__conditional.npz'),samples=con['samples'],
                                prob_right=con['prob_right'],weights=con['weights'])
            for hh in [1000,3000,5000]:
                B=min(hh//500,H//500)
                cr=score(con['samples'][:,:B],observed[0,:B])
                # Sequential LL recomputed for each horizon, actual preceding
                # choices/rewards supplied. Curve score remains diagnostic.
                cc=future['choice'][:B*500];q=np.clip(con['prob_right'][:B*500],1e-8,1-1e-8);ok=cc!=0
                nll=float(-np.mean(np.where(cc[ok]<0,np.log(q[ok]),np.log1p(-q[ok]))))
                records.append(dict(subject=subject,split=split,model=name,arm='conditional_diagnostic',horizon=hh,
                    actual_horizon=B*500,full_horizon=H>=hh,binary_nll=nll,**cr))
    score_path=folder/(subject+'__scores.json')
    previous=json.loads(score_path.read_text()) if score_path.exists() else []
    previous=[r for r in previous if r['model'] not in names]
    save_json(score_path,previous+records)
    return records


def collect(tag):
    folder=CAMP/'artifacts/forecasts'/tag
    rows=[]
    for p in sorted(folder.glob('*__scores.json')):rows.extend(json.loads(p.read_text()))
    save_json(folder/'scores.json',rows)
    summary=[]
    for arm in sorted(set(r['arm'] for r in rows)):
      for hh in [1000,3000,5000]:
       for full_only in [True,False]:
        for name in sorted(set(r['model'] for r in rows)):
         rr=[r for r in rows if r['arm']==arm and r['horizon']==hh and r['model']==name and (r['full_horizon'] or not full_only)]
         if not rr:continue
         entry=dict(arm=arm,horizon=hh,full_only=full_only,model=name,n=len(rr))
         for key in ['crps','mae','high_accuracy_mae','energy','binary_nll']:
          if key in rr[0]:entry[key]=float(np.mean([r[key] for r in rr]))
         entry['crps_by_metric']=np.mean([r['crps_by_metric'] for r in rr],axis=0).tolist()
         entry['mae_by_metric']=np.mean([r['mae_by_metric'] for r in rr],axis=0).tolist()
         entry['coverage80']=float(np.mean([r['coverage']['0.8'] for r in rr]))
         entry['width80']=float(np.mean([r['width']['0.8'] for r in rr]))
         summary.append(entry)
    save_json(folder/'summary.json',summary)
    return rows,summary


def main():
    p=argparse.ArgumentParser();p.add_argument('--split',default='devcv',choices=['devcv','animal_holdout','lab_holdout','external'])
    p.add_argument('--tag');p.add_argument('--models',default='persistence,growth,reinforce,reinforce_pure,dnnglm')
    p.add_argument('--particles',type=int,default=256);p.add_argument('--horizon',type=int,default=5000)
    p.add_argument('--freeze');p.add_argument('--gate');p.add_argument('--bank',action='store_true')
    p.add_argument('--calibration')
    p.add_argument('--subject');p.add_argument('--collect-only',action='store_true');p.add_argument('--overwrite',action='store_true')
    args=p.parse_args();tag=args.tag or args.split
    if args.split!='devcv':
        if not args.freeze:raise PermissionError('Protected source/external forecasts require the frozen method artifact')
        fz=json.loads(Path(args.freeze).read_text())
        for entry in fz['files']:
            path=CAMP/entry['path']
            if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
                raise RuntimeError('Frozen scientific artifact changed: '+entry['path'])
    if args.bank:development_bank()
    if args.collect_only:
        _,s=collect(tag);print(json.dumps(s,indent=2));return
    if not BANK.exists():development_bank()
    ms=model_split();ids=(ms.get('validation',ms.get('val',ms.get('validation_subjects')))) if args.split=='devcv' else subjects(args.split)
    if args.subject:ids=[args.subject]
    for s in ids:
        start=time.monotonic()
        rr=forecast_subject(s,'dev' if args.split=='devcv' else args.split,tag,args.models.split(','),
            n_particles=args.particles,horizon=args.horizon,freeze=args.freeze,gate=args.gate,
            protocol='external' if args.split=='external' else 'standard',overwrite=args.overwrite,
            calibration_path=args.calibration)
        print(json.dumps(dict(subject=s,records=len(rr),seconds=round(time.monotonic()-start,2))),flush=True)
    _,summary=collect(tag)
    print(json.dumps([r for r in summary if r['horizon']==3000 and r['full_only']],indent=2))

if __name__=='__main__':main()
