#!/usr/bin/env python3
"""Prespecified conditional known-law control; no independent real outcomes."""
from pathlib import Path
import argparse
import hashlib
import json
import time
import numpy as np
from common import C,ROOT,OLD,MODEL,BANK,digest,dump,event,seed_for,load_consumed,simulate
from session_model import from_frozen

OUT=C/'artifacts/known_learner'
FIT=C/'artifacts/transition_fit'
GRID=(.5,.6,.7,.8,.9,1.)
TRUE_RHO=.8


def representatives():
    rows=json.loads((FIT/'FIT_DISPOSITION.json').read_text())['records']
    labs=sorted(set(r['lab'] for r in rows if r['eligible_full_horizon']))
    selected=[]
    for lab in labs:
        group=[r for r in rows if r['lab']==lab and r['eligible_full_horizon']]
        row=min(group,key=lambda r:hashlib.sha256(r['subject'].encode()).hexdigest())
        selected.append(dict(subject=row['subject'],lab=lab))
    assert len(selected)==7
    return selected


def freeze_plan():
    selected=representatives()
    paths=[Path(__file__),OUT/'PLAN.md',C/'code/common.py',C/'code/session_model.py',
        MODEL,BANK,C/'protocols/FIT_FREEZE.json',FIT/'FIT_DISPOSITION.json']
    for row in selected:
        paths.extend(FIT/f'rho_{rho:.1f}'/(row['subject']+'.npz') for rho in GRID)
        paths.append(OLD/'data/processed/dev'/(row['subject']+'.npz'))
    records=[dict(path=str(p.relative_to(ROOT)),sha256=digest(p)) for p in paths]
    obj=dict(date='2026-10-29',scope='synthetic expected conditional law only; Pan data sealed',
        selected_prefixes=selected,true_rho=TRUE_RHO,grid=list(GRID),
        truth_particles=2048,forecast_particles=512,grid_particles=256,
        truth_seed_offset=910000,fit_tie_tolerance=.001,
        predictive_success_max_curve_mae=.01,files=records)
    dump(OUT/'FREEZE.json',obj)
    print(json.dumps(dict(control_freeze_sha256=digest(OUT/'FREEZE.json'),
        selected_prefixes=selected,files=len(records))),flush=True)


def check_freeze():
    obj=json.loads((OUT/'FREEZE.json').read_text())
    for row in obj['files']:
        if digest(ROOT/row['path'])!=row['sha256']:
            raise RuntimeError('Known-control frozen input changed: '+row['path'])
    if obj['selected_prefixes']!=representatives():
        raise RuntimeError('Known-control representative set changed')
    return obj


def accuracy(samples):
    return np.asarray(samples)[...,:2].mean(-1)


def population_mae(a,b):
    """Singleton-per-lab equal-lab objective for six population curves."""
    return float(np.abs(np.asarray(a)-np.asarray(b)).mean())


def record_stream(subject,policy,role,out):
    path=OUT/f'{subject}__{policy}__{role}.npz'
    np.savez_compressed(path,**{k:v for k,v in out.items() if isinstance(v,np.ndarray)})
    return dict(path=str(path.relative_to(ROOT)),sha256=digest(path))


def simulation_se(streams):
    # Independent finite-particle error across the seven fixed prefix contexts.
    values=[accuracy(x['samples']).mean(1) for x in streams]
    return float(np.sqrt(sum(v.var(ddof=1)/len(v) for v in values))/len(values))


def run():
    freeze=check_freeze();selected=freeze['selected_prefixes'];started=time.monotonic()
    event('known_learner_control_started',freeze_sha256=digest(OUT/'FREEZE.json'),
        synthetic_truth_rho=TRUE_RHO,protected_pan_prefixes_opened=0,
        protected_pan_outcomes_opened=0)
    context=[];truth_standard=[];grid={rho:[] for rho in GRID};manifest=[]
    true_model=from_frozen(MODEL,TRUE_RHO,{'role':'known synthetic conditional generator'})
    for row in selected:
        subject=row['subject'];prefix=load_consumed(subject,cap=1000,
            purpose='known conditional learner control; first1000consumedprefix only')
        with np.load(FIT/'rho_0.8'/(subject+'.npz'),allow_pickle=False) as z:
            starts=z['session_start'].copy()
        assert len(prefix['choice'])==1000 and len(starts)==3000
        out=simulate(true_model,prefix,starts,kind='rnn',policy='standard',n=2048,
            seed=seed_for(subject)+910000,subject=subject)
        truth_standard.append(out);manifest.append(record_stream(subject,'standard','truth_rho0.8',out))
        for rho in GRID:
            with np.load(FIT/f'rho_{rho:.1f}'/(subject+'.npz'),allow_pickle=False) as z:
                grid[rho].append(accuracy(z['samples']).mean(0))
        context.append((row,prefix,starts))
        print(json.dumps(dict(stage='standard_truth',subject=subject,
            seconds=time.monotonic()-started)),flush=True)
    truth_curves=np.asarray([accuracy(x['samples']).mean(0) for x in truth_standard])
    # The original fitting objective is equal lab MAE, not MAE of the pooled mean.
    losses=[dict(rho=rho,equal_lab_curve_mae=population_mae(grid[rho],truth_curves)) for rho in GRID]
    minimum=min(r['equal_lab_curve_mae'] for r in losses)
    chosen=max(r['rho'] for r in losses if r['equal_lab_curve_mae']<=minimum+.001)
    recovered_model=from_frozen(MODEL,chosen,{'role':'recovered synthetic control prescription'})
    policy_results={};fixed_truth=[];fixed_forecasts=[];growth_forecasts=[]
    for policy in ('standard','external'):
        truths=truth_standard if policy=='standard' else []
        forecasts=[];growth=[];rows=[]
        for i,(row,prefix,starts) in enumerate(context):
            subject=row['subject']
            if policy=='external':
                out=simulate(true_model,prefix,starts,kind='rnn',policy=policy,n=2048,
                    seed=seed_for(subject)+910000,subject=subject)
                truths.append(out);manifest.append(record_stream(subject,policy,'truth_rho0.8',out))
            prediction=simulate(recovered_model,prefix,starts,kind='rnn',policy=policy,n=512,
                seed=seed_for(subject),subject=subject)
            forecasts.append(prediction);manifest.append(record_stream(subject,policy,'selected_forecast',prediction))
            tc=accuracy(truths[i]['samples']).mean(0);pc=accuracy(prediction['samples']).mean(0)
            record=dict(**row,truth_curve=tc.tolist(),forecast_curve=pc.tolist(),
                curve_mae=float(np.abs(tc-pc).mean()),mean_signed_error_observed_minus_forecast=float(np.mean(tc-pc)))
            if policy=='external':
                gp=simulate(recovered_model,prefix,starts,kind='growth',policy=policy,n=512,
                    seed=seed_for(subject),subject=subject)
                growth.append(gp);manifest.append(record_stream(subject,policy,'growth_forecast',gp))
                gc=accuracy(gp['samples']).mean(0)
                record.update(growth_curve=gc.tolist(),growth_curve_mae=float(np.abs(tc-gc).mean()))
            rows.append(record)
            print(json.dumps(dict(stage='control_forecast',policy=policy,subject=subject,
                selected_rho=chosen,seconds=time.monotonic()-started)),flush=True)
        tc=np.asarray([r['truth_curve'] for r in rows]);pc=np.asarray([r['forecast_curve'] for r in rows])
        # Both the declared equal-lab fitting loss and pooled population loss.
        pooled=float(np.abs((tc-pc).mean(0)).mean())
        macro=population_mae(tc,pc)
        result=dict(equal_lab_curve_mae=macro,population_curve_mae=pooled,
            mean_bias_observed_minus_forecast=float(np.mean(tc-pc)),
            truth_population_curve=tc.mean(0).tolist(),forecast_population_curve=pc.mean(0).tolist(),
            truth_scalar_conditional_mc_se=simulation_se(truths),
            forecast_scalar_conditional_mc_se=simulation_se(forecasts),
            predictive_expected_law_success=pooled<=.01,per_prefix=rows)
        if policy=='external':
            gc=np.asarray([r['growth_curve'] for r in rows]);growth_mae=float(np.abs((tc-gc).mean(0)).mean())
            result.update(growth_population_curve=gc.mean(0).tolist(),growth_population_curve_mae=growth_mae,
                population_curve_mae_advantage_over_growth=growth_mae-pooled,
                growth_equal_lab_curve_mae=population_mae(tc,gc),
                growth_scalar_conditional_mc_se=simulation_se(growth))
        policy_results[policy]=result
    result=dict(scope='known conditional synthetic learner; not empirical Pan or whole-animal fit recovery',
        freeze_sha256=digest(OUT/'FREEZE.json'),true_rho=TRUE_RHO,selected_control_rho=chosen,
        exact_parameter_recovery=chosen==TRUE_RHO,grid_results=losses,
        selected_grid_predictive_recovery=next(r['equal_lab_curve_mae'] for r in losses if r['rho']==chosen)<=.01,
        policies=policy_results,truth_particles=2048,forecast_particles=512,
        truth_seed_offset=910000,conditional_on_consumed_prefixes=True,
        truth_mean_fixed_minus_standard=float(np.mean(policy_results['external']['truth_population_curve'])-
            np.mean(policy_results['standard']['truth_population_curve'])),
        expected_law_success_both_policies=all(r['predictive_expected_law_success'] for r in policy_results.values()),
        elapsed_seconds=time.monotonic()-started,manifest=manifest,
        protected_pan_prefixes_opened=0,protected_pan_outcomes_opened=0)
    dump(OUT/'RESULT.json',result)
    event('known_learner_control_complete',result_sha256=digest(OUT/'RESULT.json'),
        selected_control_rho=chosen,expected_law_success_both_policies=result['expected_law_success_both_policies'],
        protected_pan_prefixes_opened=0,protected_pan_outcomes_opened=0)
    print(json.dumps(dict(stage='control_complete',selected_rho=chosen,
        parameter_recovery=chosen==TRUE_RHO,
        standard_curve_mae=policy_results['standard']['population_curve_mae'],
        fixed_curve_mae=policy_results['external']['population_curve_mae'],
        fixed_growth_advantage=policy_results['external']['population_curve_mae_advantage_over_growth'],
        seconds=time.monotonic()-started)),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze-plan',action='store_true')
    parser.add_argument('--run',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.freeze_plan:freeze_plan()
    if args.run:run()


if __name__=='__main__':main()
