#!/usr/bin/env python3
"""Predeclared postvalidation source diagnostics and Monte Carlo challenges.

No frozen file is edited. No external animal is accepted. Source outcomes are
already consumed; these checks localize failures and are not new holdouts.
The actual adaptive schedule replay is explicitly conditional diagnostic.
"""
from __future__ import annotations
import argparse, concurrent.futures, datetime as dt, hashlib, json, time
from pathlib import Path
import numpy as np
from data_io import load_prefix_and_opportunities,exposure
from learning_models import load_model
from baselines import load_bank
from rollout import autonomous
from uncertainty import apply_calibration
from evaluation import score,paired_interval
from trainer import VectorTrainer

C=Path(__file__).resolve().parents[1]
OUT=C/'artifacts/challenges'
FREEZE=C/'protocols/FREEZE.json'
FREEZE_SHA='c0141244ac43d240f858956917e3b2b661c72a01a4bddbccdb3974a818b5741f'
CONFIG=C/'artifacts/calibration/CONFIG.json'
MODELS={
 'dnnglm32':C/'artifacts/models/dnnglm32_nested_best.npz',
 'dnnglm':C/'artifacts/models/dnnglm_nested_best.npz',
 'reinforce':C/'artifacts/models/reinforce_nested_stable.npz',
}
VARIANTS={
 'static_current':dict(calibration_method='static'),
 'zero_w0':dict(calibration_method='zero'),
 'retention_0p8':dict(weight_retention=.8),
 'reset_to_prefix_anchor':dict(reset_weights=True),
 'no_correction':dict(trainer_options=dict(correction=False)),
 'fast_promotion':dict(trainer_options=dict(promotion='fast')),
 'slow_promotion':dict(trainer_options=dict(promotion='slow')),
 'fixed_omission':dict(omission_mode='fixed'),
 'actual_contrast_replay':dict(),
}

def write_json(path,x):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,indent=2)+'\n')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def seed_for(subject):return 20261028+int(hashlib.sha256(subject.encode()).hexdigest()[:7],16)

def allocation():
    records=json.loads((C/'protocols/SPLIT.json').read_text())['standard']
    return {r['subject']:r for r in records if r['split']in['animal_holdout','lab_holdout']}

def subject_order():
    ids=json.loads((C/'artifacts/results/SUBJECT_ORDER.json').read_text());amap=allocation()
    if len(ids)!=40 or any(s not in amap for s in ids):raise PermissionError('Expected exactly frozen40full-primarysourceIDs')
    return ids

def verify():
    if sha(FREEZE)!=FREEZE_SHA:raise PermissionError('Scientific freeze changed')
    for r in json.loads(FREEZE.read_text())['files']:
        if sha(C/r['path'])!=r['sha256']:raise RuntimeError('Frozen artifact changed '+r['path'])

def source_folder(subject):
    a=allocation().get(subject)
    if a is None:raise PermissionError('External/dev subject forbidden in source diagnostic')
    return C/'artifacts/forecasts'/('source_animals'if a['split']=='animal_holdout'else'source_labs')

def read_inputs(subject):
    if subject not in subject_order():raise PermissionError('Not a frozen full-source subject')
    a=allocation()[subject]
    prefix,starts,meta=load_prefix_and_opportunities(subject,a['split'],prefix_n=1000,horizon=3000,freeze_path=FREEZE,
              purpose='postvalidation predeclared source-only diagnostic;prefix outcomes only')
    if len(starts)!=3000:raise ValueError('Full primary exposure expected')
    f=source_folder(subject)
    with np.load(f/(subject+'__observed.npz'),allow_pickle=False)as z:y=z['observed'][:6]
    with np.load(C/'artifacts/reconstruction/original_targets'/(subject+'.npz'),allow_pickle=False)as z:replay=z['signed_contrast'][1000:4000]
    return prefix,starts,meta,y,replay

def reference(subject,name):
    p=source_folder(subject)/(subject+'__'+name+'.npz')
    with np.load(p,allow_pickle=False)as z:a=z['samples_primary'][:,:6]
    y=np.load(source_folder(subject)/(subject+'__observed.npz'))['observed'][:6]
    return score(a,y)

def forecast_one(subject,name,variant,particles,prefix,starts,observed,replay,bank,group):
    folder=OUT/group;path=folder/(subject+'__'+name+'__'+variant+'.npz');jp=path.with_suffix('.json')
    if jp.exists()and path.exists():
        saved=json.loads(jp.read_text())
        if sha(path)!=saved['file_sha256']or saved['freeze_sha256']!=FREEZE_SHA or saved['particles']!=particles:
            raise ValueError('Saved source diagnostic integrity/configuration mismatch '+str(path))
        return saved
    options=dict(VARIANTS[variant])if variant in VARIANTS else {}
    conditional=variant in['actual_contrast_replay','balanced_zero_replay']
    if conditional:options['replay_signed_contrast']=replay
    model=None if name=='growth'else load_model(MODELS[name]);competence='growth'if name=='growth'else None
    if variant=='coherent_retention_0p8':
        # This postvalidation review challenge changes the boundary model
        # consistently during prefix inference and every future daybreak.
        from recovery import RetentionAwareModel
        model=RetentionAwareModel(model,.8);options['weight_retention']=.8
    base=seed_for(subject);t0=time.monotonic()
    if variant=='balanced_zero_replay':
        # The frozen replay uses returned task['side'] only when the forced
        # actual contrast is zero. A process-local wrapper makes that side
        # exogenous Bernoulli(.5), independent of pending correction state.
        # Nonzero actual contrasts determine their own side in frozen code.
        original_sample=VectorTrainer.sample
        zero_rng=np.random.default_rng(base+823)
        def balanced_sample(trainer):
            task=original_sample(trainer)
            task['side']=np.where(zero_rng.random(trainer.n)<.5,-1,1).astype(np.int8)
            return task
        VectorTrainer.sample=balanced_sample
        try:result=autonomous(model,prefix,starts,bank,n_particles=particles,seed=base,subject=subject,competence=competence,**options)
        finally:VectorTrainer.sample=original_sample
    else:result=autonomous(model,prefix,starts,bank,n_particles=particles,seed=base,subject=subject,competence=competence,**options)
    primary=apply_calibration(result['samples'],name,base+647,config_path=CONFIG)
    folder.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(path,samples=primary,samples_raw=result['samples'],weights=result['weights'],
                        counts=result['counts'],pool_fraction=result['pool_fraction'])
    sc=score(primary,observed);p=reference(subject,name);g=reference(subject,'growth')
    rec=dict(subject=subject,split=allocation()[subject]['split'],lab=allocation()[subject]['lab'],model=name,
             variant=variant,particles=particles,seed=base,horizon=3000,group=group,
             mode='conditional_actual_contrast_replay'if conditional else'postvalidation_autonomous_sensitivity',
             freeze_sha256=FREEZE_SHA,uncertainty_config_sha256=sha(CONFIG),seconds=time.monotonic()-t0,
             score=sc,primary512_score=p,growth512_score=g,
             score_gain_over_primary512=p['crps']-sc['crps'],score_gain_over_growth512=g['crps']-sc['crps'],
             high_mae_gain_over_primary512=p['high_accuracy_mae']-sc['high_accuracy_mae'],
             high_mae_gain_over_growth512=g['high_accuracy_mae']-sc['high_accuracy_mae'],
             calibration=result['calibration'],simulator_mode=result['mode'],file_sha256=sha(path))
    write_json(jp,rec)
    return rec

def run_subject(task):
    subject,group,particles,names,variants=task
    prefix,starts,meta,y,replay=read_inputs(subject);bank=load_bank(C/'artifacts/baselines/nested_growth_bank.npz')
    rows=[]
    exposure(dict(event='postvalidation_source_diagnostic',subject=subject,split=allocation()[subject]['split'],
              variants=variants,models=names,particles=particles,group=group,external_outcomes_read=False,
              future_outcomes_assimilated=False,future_contrasts_used_only_if_named_replay=True))
    for name in names:
        for variant in variants:rows.append(forecast_one(subject,name,variant,particles,prefix,starts,y,replay,bank,group))
    return dict(subject=subject,group=group,records=len(rows),seconds=sum(r['seconds']for r in rows))

def execute(tasks,workers=3):
    if workers==1:
        for t in tasks:print(json.dumps(run_subject(t)),flush=True)
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers)as pool:
            for result in pool.map(run_subject,tasks):print(json.dumps(result),flush=True)

def collect():
    rows=[]
    for folder in OUT.iterdir():
        if folder.is_dir():
            for p in folder.glob('*.json'):
                r=json.loads(p.read_text())
                if 'score'in r:rows.append(r)
    summaries=[]
    for group,name,variant in sorted(set((r['group'],r['model'],r['variant'])for r in rows)):
        rr=[r for r in rows if(r['group'],r['model'],r['variant'])==(group,name,variant)]
        rr.sort(key=lambda r:subject_order().index(r['subject']))
        summaries.append(dict(group=group,model=name,variant=variant,n=len(rr),particles=rr[0]['particles'],mode=rr[0]['mode'],
            crps=float(np.mean([r['score']['crps']for r in rr])),high_accuracy_mae=float(np.mean([r['score']['high_accuracy_mae']for r in rr])),
            coverage80=float(np.mean([r['score']['coverage']['0.8']for r in rr])),width80=float(np.mean([r['score']['width']['0.8']for r in rr])),
            score_gain_over_primary512=paired_interval([r['score_gain_over_primary512']for r in rr]),
            score_gain_over_growth512=paired_interval([r['score_gain_over_growth512']for r in rr]),
            high_mae_gain_over_primary512=float(np.mean([r['high_mae_gain_over_primary512']for r in rr])),
            high_mae_gain_over_growth512=float(np.mean([r['high_mae_gain_over_growth512']for r in rr]))))
    write_json(OUT/'SCORES.json',rows);write_json(OUT/'SUMMARY.json',summaries)
    # Extra precision challenge compares both candidate and baseline at1024.
    mc=[r for r in rows if r['group']=='mc1024_all40'];by={(r['subject'],r['model']):r for r in mc}
    ids=[s for s in subject_order()if(s,'dnnglm')in by and(s,'growth')in by]
    if ids:
        delta=[by[(s,'growth')]['score']['crps']-by[(s,'dnnglm')]['score']['crps']for s in ids]
        baseline=np.mean([by[(s,'growth')]['score']['crps']for s in ids]);mae_g=np.mean([by[(s,'growth')]['score']['high_accuracy_mae']for s in ids]);mae_m=np.mean([by[(s,'dnnglm')]['score']['high_accuracy_mae']for s in ids])
        rng=np.random.default_rng(891);d=np.asarray(delta);bs=d[rng.integers(0,len(d),(10000,len(d)))].mean(axis=1)
        write_json(OUT/'MC1024_DNN16_VS_GROWTH.json',dict(n=len(ids),animal_order=ids,score_gain=paired_interval(delta),gate_lower00625=float(np.quantile(bs,.00625)),
               relative_crps_gain=float(np.mean(delta)/baseline),dnnglm16_crps=float(np.mean([by[(s,'dnnglm')]['score']['crps']for s in ids])),growth_crps=float(baseline),
               dnnglm16_high_mae=float(mae_m),growth_high_mae=float(mae_g),relative_high_mae_gain=float(1-mae_m/mae_g)))
    first6=json.loads((OUT/'CHALLENGE_DESIGN.json').read_text())['mc1024_first6_by_subject_sha256']
    mc6=[]
    for model in ['dnnglm32','reinforce','growth']:
        group='mc1024_all40'if model=='growth'else'mc1024_hash6'
        rr=[r for r in rows if r['group']==group and r['model']==model and r['subject']in first6]
        if rr:mc6.append(dict(model=model,n=len(rr),subjects=[s for s in first6 if any(r['subject']==s for r in rr)],
                         mean_delta_crps_1024_minus512=float(-np.mean([r['score_gain_over_primary512']for r in rr])),
                         max_abs_delta_crps=float(np.max(np.abs([r['score_gain_over_primary512']for r in rr]))),
                         mean_delta_high_mae_1024_minus512=float(-np.mean([r['high_mae_gain_over_primary512']for r in rr])),
                         max_abs_delta_high_mae=float(np.max(np.abs([r['high_mae_gain_over_primary512']for r in rr])))))
    write_json(OUT/'MC1024_HASH6.json',mc6)
    return summaries

def freeze_challenge_design():
    p=OUT/'CHALLENGE_DESIGN.json'
    if p.exists():return
    ids=subject_order();first6=sorted(ids,key=lambda s:hashlib.sha256(s.encode()).hexdigest())[:6]
    write_json(p,dict(status='postvalidation_diagnostic;predeclaredfamiliesfromscientificfreeze',freeze_sha256=FREEZE_SHA,
               full_source_ids=ids,variants=VARIANTS,particles_primary_diagnostics=256,
               confirmation='Any nondiagnostic variant with meanCRPSgain>=.001overgrowth512 receives512particleconfirmation; no new fit/gateclaim.',
               mc1024_first6_by_subject_sha256=first6,mc1024_all40_models=['dnnglm','growth'],
               replay='actual future contrasts only; choices/rewards generated; hidden zero-contrast side drawn by own trainer',
               inert_protocol_parameters='Binary reward actors do not use reward volume or wheel gain; no inert robustness test is claimed.',
               external_status='sealed; no access authorized',utc=dt.datetime.now(dt.timezone.utc).isoformat()))

def main():
    p=argparse.ArgumentParser();p.add_argument('--sensitivities',action='store_true');p.add_argument('--mc',action='store_true');p.add_argument('--confirm',action='store_true');p.add_argument('--coherent-retention',action='store_true');p.add_argument('--balanced-replay',action='store_true');p.add_argument('--collect-only',action='store_true');p.add_argument('--workers',type=int,default=3);p.add_argument('--subject')
    a=p.parse_args();OUT.mkdir(parents=True,exist_ok=True);verify();freeze_challenge_design();ids=subject_order()
    if a.subject:ids=[s for s in ids if s==a.subject]
    if a.sensitivities:execute([(s,'source_sens256',256,['dnnglm32','reinforce'],list(VARIANTS))for s in ids],a.workers)
    if a.coherent_retention:
        amendment=OUT/'COHERENT_RETENTION_AMENDMENT.json'
        if not amendment.exists():write_json(amendment,dict(scope='postvalidation independent-review diagnostic;no new holdout claim',
             reason='Original retention_0p8 diagnostic changed future boundaries only; reviewer requested coherent prefix plusfuture boundary model.',
             prefix_model='recovery.RetentionAwareModel(base_model,.8)',future='autonomous(weight_retention=.8)',
             models=['dnnglm32','reinforce'],subjects=subject_order(),particles=256,no_update_rule_refit=True,
             freeze_sha256=FREEZE_SHA,external_status='sealed',utc=dt.datetime.now(dt.timezone.utc).isoformat()))
        execute([(s,'source_coherent256',256,['dnnglm32','reinforce'],['coherent_retention_0p8'])for s in ids],a.workers)
    if a.balanced_replay:
        amendment=OUT/'BALANCED_REPLAY_AMENDMENT.json'
        if not amendment.exists():write_json(amendment,dict(scope='postvalidation conditional diagnostic coding check;primaryunchanged',
            reason='Original frozen contrast replay inherits own trainer pending-correction side on forcedzero contrasts; exogenous actual-contrast replay requires independent balancedzero assignment.',
            implementation='temporary process-local VectorTrainer.sample returnedside wrapper; original method restored in finally; frozenfilesunchanged',
            zero_side_rng='independent np.default_rng(subject_base+823),Bernoulli(.5),notrealzerochoiceorfeedback',
            models=['dnnglm32','reinforce'],subjects=subject_order(),particles=256,freeze_sha256=FREEZE_SHA,
            original_replay_preserved=True,external_status='sealed',utc=dt.datetime.now(dt.timezone.utc).isoformat()))
        execute([(s,'source_balanced_replay256',256,['dnnglm32','reinforce'],['balanced_zero_replay'])for s in ids],a.workers)
    if a.mc:
        execute([(s,'mc1024_all40',1024,['dnnglm','growth'],['map_reference'])for s in ids],a.workers)
        first6=json.loads((OUT/'CHALLENGE_DESIGN.json').read_text())['mc1024_first6_by_subject_sha256']
        execute([(s,'mc1024_hash6',1024,['dnnglm32','reinforce'],['map_reference'])for s in first6 if s in ids],a.workers)
    summary=collect()
    if a.confirm:
        candidates=[r for r in summary if r['group']in['source_sens256','source_coherent256']and r['n']==40 and r['variant']not in['actual_contrast_replay','balanced_zero_replay']and r['score_gain_over_growth512']['mean']>=.001]
        for r in candidates:execute([(s,'source_confirm512',512,[r['model']],[r['variant']])for s in ids],a.workers)
        write_json(OUT/'CONFIRMATION_STATUS.json',dict(trigger='mean CRPS gain over frozen growth512 >=.001,all40sourceanimals,nondiagnostic variants',
              candidates=[dict(model=r['model'],variant=r['variant'],mean_gain=r['score_gain_over_growth512']['mean'])for r in candidates],
              n_confirmed_families=len(candidates),note='No source-holdout novelty or transfer gate is earned by selecting a postvalidation diagnostic.'))
        collect()

if __name__=='__main__':main()
