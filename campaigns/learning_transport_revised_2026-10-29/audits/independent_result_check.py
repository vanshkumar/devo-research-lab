#!/usr/bin/env python3
"""Independent finite-fit/comparison reductions and two bounded forecast replays.

Read saved consumed-source targets and forecasts only. The optional (default)
two replays read just1000-row consumed prefixes; no protected identity/future
has a route. No production scoring/selection helper is used for reductions.
"""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import sys

C = Path(__file__).resolve().parents[1]
ROOT = C.parents[1]
OLD = ROOT / 'campaigns/learning_rule_transport_2026-10-28'
POP = ROOT / 'campaigns/population_learning_transport_2026-10-28'
FIT = C / 'artifacts/transition_fit'
COMP = C / 'artifacts/source_comparison'
CONTROL = C / 'artifacts/decision_controls'
os.environ.setdefault('NUMBA_CACHE_DIR',str(C/'artifacts/numba_cache'))
sys.dont_write_bytecode = True
sys.path.insert(0,str(C/'code'))
import numpy as np
from scipy.stats import beta

KINDS = ('existing','session','growth','persistence')
GRID = (.5,.6,.7,.8,.9,1.)
SEED = 202610291
REPS = 20000
TOL = 2e-12
CHECKS = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def match(label,actual,expected,tol=TOL):
    a,b = np.asarray(actual),np.asarray(expected)
    assert a.shape == b.shape,(label,a.shape,b.shape)
    error = float(np.max(np.abs(a.astype(float)-b.astype(float)))) if a.size else 0.
    assert error <= tol,(label,error,tol)
    CHECKS.append(dict(check=label,max_abs=error))


def pinned(path):
    obj = read(path)
    for row in obj.get('files',[]):
        p = Path(row['path'])
        if not p.is_absolute():p = ROOT/p
        assert sha(p) == row['sha256'],str(p)
    for path,digest in obj.get('pins',{}).items():
        assert sha(ROOT/path) == digest,path


def canonical_ids():
    first = read(OLD/'artifacts/results/SUBJECT_ORDER.json')
    second = read(POP/'protocols/FREEZE.json')['source_primary_subjects']
    assert len(first) == 40 and len(second) == 24 and len(set(first+second)) == 64
    return first,second


def macro(y,p,labs):
    answer = {}
    for lab in sorted(set(labs)):
        indices = np.flatnonzero(np.asarray(labs)==lab)
        # Independent reduction order: mean curves, then absolute error.
        error = y[indices].mean(0)-p[indices].mean(0)
        answer[str(lab)] = float(np.mean(np.abs(error)))
    return float(np.mean(list(answer.values()))),answer


def crps_pairs(draws,truth):
    # Explicit pair distances, independently of the production sorting identity.
    first = np.abs(draws-truth).mean(0)
    n=len(draws)
    # The frozen score is the unbiased independent-pair MonteCarlo estimate;
    # diagonal distances vanish and the pair denominator is n(n-1), not n².
    second = np.abs(draws[:,None,:]-draws[None,:,:]).sum((0,1))/(2*n*(n-1))
    return float(np.mean(first-second))


def verify_fit():
    answer = read(FIT/'RESULT.json')
    disposition = read(FIT/'FIT_DISPOSITION.json')
    allocated = read(OLD/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json')['train']
    assert disposition['allocated'] == len(allocated) == 62
    assert [r['subject'] for r in disposition['records']] == allocated
    assert all(0 <= r['rows_returned'] <= 4000 for r in disposition['records'])
    eligible = [r for r in disposition['records'] if r['eligible_full_horizon']]
    assert all(r['rows_returned']==4000 for r in eligible)
    assert len(eligible)==disposition['eligible']==answer['fit_n_animals']
    objectives = []
    records_by_rho = []
    common_targets = {}
    for rho in GRID:
        y,p,labs = [],[],[]
        summary = read(FIT/f'rho_{rho:.1f}'/'SUMMARY.json')
        for row in eligible:
            subject = row['subject']
            path = FIT/f'rho_{rho:.1f}'/(subject+'.npz')
            metadata = read(path.with_suffix('.json'))
            assert metadata['forecast_sha256']==sha(path)
            assert metadata['lab']==row['lab'] and metadata['particles']==256
            assert metadata['rho']==rho
            with np.load(path,allow_pickle=False) as z:
                assert z['samples'].shape==(256,6,4)
                observed = z['observed']
                counts = z['observed_counts']
                assert observed.shape==(6,4) and counts.shape==(6,4)
                assert z['session_start'].shape==(3000,)
                assert np.all(counts[:,:2]>0) and np.all(counts[:,2:]==500)
                target = observed[:,:2].mean(1)
                forecast = z['samples'][:,:,:2].mean(2).mean(0)
            match(f'fit {rho} {subject} target metadata',target,metadata['observed'])
            match(f'fit {rho} {subject} forecast metadata',forecast,metadata['predicted'])
            if subject in common_targets:
                match(f'fit {rho} {subject} shared targets',observed,common_targets[subject][0],0.)
                match(f'fit {rho} {subject} shared counts',counts,common_targets[subject][1],0.)
            else:common_targets[subject]=(observed.copy(),counts.copy())
            y.append(target);p.append(forecast);labs.append(row['lab'])
        objective,bylab = macro(np.asarray(y),np.asarray(p),np.asarray(labs))
        objectives.append(objective)
        match(f'fit {rho} summary objective',objective,summary['objective_equal_lab_curve_mae'])
        frozenrow = next(r for r in answer['grid_results'] if r['rho']==rho)
        match(f'fit {rho} final objective',objective,frozenrow['objective_equal_lab_curve_mae'])
        for lab,value in bylab.items():
            reported = next(r for r in summary['labs'] if r['lab']==lab)
            match(f'fit {rho} lab {lab}',value,reported['curve_mae'])
        records_by_rho.append(dict(rho=rho,objective=objective,by_lab=bylab))
    minimum = min(objectives)
    chosen = max(rho for rho,loss in zip(GRID,objectives) if loss<=minimum+.001)
    assert chosen==answer['selected_rho']
    match('fit minimum',minimum,answer['minimum_objective'])
    match('fit selected objective',objectives[GRID.index(chosen)],answer['selected_objective'])
    model_path=C/'model_session_transition.npz'
    assert sha(model_path)==answer['selected_model_sha256']
    with np.load(model_path,allow_pickle=False) as selected, np.load(OLD/'artifacts/rnn/rnnglm32_nested_best.npz',allow_pickle=False) as original:
        excluded={'kind','metadata','rho'}
        fields=set(selected.files)-excluded
        assert fields==set(original.files)-excluded
        assert float(selected['rho'])==chosen
        for key in fields:match('frozen model parameter '+key,selected[key],original[key],0.)
    return dict(allocated=62,eligible=len(eligible),selected_rho=chosen,
        minimum_objective=minimum,grid=records_by_rho,
        selection='largest rho within .001 of minimum',all_within_session_parameters_exact=True)


def verify_comparison():
    result=read(COMP/'RESULT.json')
    first,second=canonical_ids();ids=first+second
    oldmeta={r['subject']:r for r in read(OLD/'protocols/SPLIT.json')['standard']}
    with np.load(POP/'artifacts/method_audit/CONSUMED_SOURCE_EXACT100.npz',allow_pickle=False) as z:
        oldorder=list(z['subject'].astype(str))
        oldtargets={s:(z['observed'][j],z['counts'][j]) for j,s in enumerate(oldorder)}
    with np.load(POP/'artifacts/results/SOURCE_ARRAYS.npz',allow_pickle=False) as z:
        laterlabs=dict(zip(z['subjects'].astype(str),z['labs'].astype(str)))
    rawy,rawcounts,labs,all_draws=[],[],[],{k:[] for k in KINDS}
    individual_crps={k:[] for k in KINDS}
    for i,subject in enumerate(ids):
        folder=COMP/subject
        op=folder/'observed.npz'
        with np.load(op,allow_pickle=False) as z:
            target=z['observed'];counts=z['counts']
        assert target.shape==(6,4) and counts.shape==(6,4)
        assert np.isfinite(target).all() and np.all(counts[:,:2]>0)
        assert np.all(counts[:,2:]==500)
        if i<40:
            previous,oldcounts=oldtargets[subject]
            match(subject+' historical exact100 equal-side target',target[:,:2].mean(1),previous,0.)
            match(subject+' historical exact100 side counts',counts[:,:2],oldcounts,0.)
            lab=oldmeta[subject]['lab']
        else:
            with np.load(POP/'artifacts/forecasts/source'/(subject+'__observed.npz'),allow_pickle=False) as z:
                match(subject+' later24 full target',target,z['observed'],0.)
                match(subject+' later24 all counts',counts,z['counts'],0.)
            lab=laterlabs[subject]
        rawy.append(target);rawcounts.append(counts);labs.append(lab)
        for kind in KINDS:
            path=folder/(kind+'.npz');metadata=read(path.with_suffix('.json'))
            assert metadata['forecast_sha256']==sha(path)
            assert metadata['observed_sha256']==sha(op)
            assert metadata['lab']==lab and metadata['subject']==subject
            assert metadata['n_particles']==512
            with np.load(path,allow_pickle=False) as z:draws=z['samples']
            assert draws.shape==(512,6,4) and np.isfinite(draws).all()
            all_draws[kind].append(draws)
            score=crps_pairs(draws[:,:,:2].mean(2),target[:,:2].mean(1))
            individual_crps[kind].append(score)
            match(subject+' '+kind+' independent pair CRPS',score,metadata['individual_accuracy_crps'])
    rawy=np.asarray(rawy);rawcounts=np.asarray(rawcounts);labs=np.asarray(labs)
    y=rawy[:,:,:2].mean(2)
    all_draws={k:np.asarray(v) for k,v in all_draws.items()}
    expected={k:np.mean(v[:,:,:,:2],axis=3).mean(1) for k,v in all_draws.items()}
    metrics={};auxiliary={}
    for kind,p in expected.items():
        loss,bylab=macro(y,p,labs)
        scalar_draws=all_draws[kind][:,:,:,:2].mean(3).mean(2)
        scalar_variance=sum(float(np.var(x,ddof=1))/512 for x in scalar_draws)/len(ids)**2
        metrics[kind]=dict(equal_lab_curve_mae=loss,by_lab_curve_mae=bylab,
            pooled_population_curve_mae=float(np.abs(y.mean(0)-p.mean(0)).mean()),
            individual_equal_side_mae=float(np.mean(np.abs(y-p))),
            individual_accuracy_marginal_crps=float(np.mean(individual_crps[kind])),
            mean_curve=p.mean(0),mean_accuracy=float(p.mean()),
            scalar_bias_observed_minus_forecast=float((y-p).mean()),
            conditional_simulation_scalar_se=float(np.sqrt(scalar_variance)))
        for key,value in metrics[kind].items():
            if key=='by_lab_curve_mae':
                for lab,item in value.items():match(kind+' lab '+lab,item,result['metrics'][kind][key][lab])
            else:match(kind+' '+key,value,result['metrics'][kind][key])
        pred4=all_draws[kind].mean(1)
        auxiliary[kind]={}
        for name,mask in [('all64',np.ones(64,bool)),('historical40',np.arange(64)<40),('later24',np.arange(64)>=40)]:
            target=rawy[mask];pred=pred4[mask]
            auxiliary[kind][name]=dict(n=int(mask.sum()),
                observed_mean_curve=target.mean(0).tolist(),predicted_mean_curve=pred.mean(0).tolist(),
                observed_mean=target.mean((0,1)).tolist(),predicted_mean=pred.mean((0,1)).tolist(),
                pooled_population_curve_mae=np.abs(target.mean(0)-pred.mean(0)).mean(0).tolist(),
                individual_curve_mae=np.abs(target-pred).mean((0,1)).tolist(),
                bias_observed_minus_forecast=(target-pred).mean((0,1)).tolist())
    selected='existing' if metrics['existing']['equal_lab_curve_mae']<=metrics['session']['equal_lab_curve_mae']+.001 else 'session'
    assert selected==result['selected_approach']
    match('minimum side denominator',rawcounts[:,:,:2].min(),result['minimum_side_denominator'],0.)
    match('observed population curve',y.mean(0),result['observed_curve'])
    strata={}
    for name,mask in [('historical40',np.arange(64)<40),('later24',np.arange(64)>=40)]:
        losses={k:macro(y[mask],p[mask],labs[mask])[0] for k,p in expected.items()}
        pooled={k:float(np.abs(y[mask].mean(0)-p[mask].mean(0)).mean()) for k,p in expected.items()}
        for kind in KINDS:
            match(name+' macro '+kind,losses[kind],result['strata'][name]['equal_lab_curve_mae'][kind])
            match(name+' pooled '+kind,pooled[kind],result['strata'][name]['pooled_population_curve_mae'][kind])
        advantage=losses['growth']-losses[selected]
        match(name+' selected growth advantage',advantage,result['strata'][name]['selected_growth_advantage'])
        strata[name]=dict(n=int(mask.sum()),loss=losses,selected_growth_advantage=advantage)
    gains={}
    labels=sorted(set(labs))
    # Canonical sorted lab order and independent multinomial-count reduction.
    indices=np.random.default_rng(SEED).integers(0,len(labels),(REPS,len(labels)))
    counts=np.array([np.bincount(row,minlength=len(labels)) for row in indices])
    for kind in ('existing','session'):
        d=np.array([metrics['growth']['by_lab_curve_mae'][lab]-metrics[kind]['by_lab_curve_mae'][lab] for lab in labels])
        boot=counts@d/len(labels)
        lo,hi=np.quantile(boot,[.025,.975])
        gains[kind]=dict(gain=float(d.mean()),lower=float(lo),upper=float(hi),
            by_lab=dict(zip(labels,d.tolist())))
        for key in ('gain','lower','upper'):match(kind+' bootstrap '+key,gains[kind][key],result['growth_comparison'][kind][key])
        for lab,value in gains[kind]['by_lab'].items():match(kind+' lab gain '+lab,value,result['growth_comparison'][kind]['by_lab'][lab])
    advantage=metrics['growth']['equal_lab_curve_mae']-metrics[selected]['equal_lab_curve_mae']
    persistence=metrics['persistence']['equal_lab_curve_mae']-metrics[selected]['equal_lab_curve_mae']
    criteria=dict(macro_growth_gain_at_least2pp=advantage>=.02,
        macro_persistence_gain_positive=persistence>0,
        growth_gain_positive_historical40=strata['historical40']['selected_growth_advantage']>0,
        growth_gain_positive_later24=strata['later24']['selected_growth_advantage']>0,
        paired_lab_bootstrap_lower_positive=gains[selected]['lower']>0)
    assert criteria==result['readiness_criteria']
    assert all(criteria.values())==result['source_readiness_passed']
    match('selected growth advantage',advantage,result['selected_macro_growth_advantage'])
    match('selected persistence advantage',persistence,result['selected_macro_persistence_advantage'])
    for omitted in labels:
        subset=labs!=omitted
        loo=macro(y[subset],expected['growth'][subset],labs[subset])[0]-macro(y[subset],expected[selected][subset],labs[subset])[0]
        match('leave out '+omitted,loo,result['leave_one_lab_out_growth_advantage'][omitted])
    aux=dict(date='2026-10-29',scope='Independent supplemental reductions of saved consumed-source arrays; no new outcomes',
        channel_order=['accuracy_at_minus100','accuracy_at_plus100','right_choice_share','omission_share'],
        bin_opportunities=500,prefix_opportunities=1000,future_opportunities=3000,
        endpoint_means_and_losses=auxiliary,all_source_consumed=True,protected_pan_accesses=0,
        source_result_sha256=sha(COMP/'RESULT.json'))
    (C/'audits/AUXILIARY_ENDPOINTS.json').write_text(json.dumps(aux,indent=2)+'\n')
    clean_metrics={kind:{key:(value.tolist() if isinstance(value,np.ndarray) else value) for key,value in row.items()} for kind,row in metrics.items()}
    return dict(n_animals=64,n_labs=len(labels),particles=512,metrics=clean_metrics,
        selected_approach=selected,selected_macro_growth_advantage=advantage,
        selected_macro_persistence_advantage=persistence,lab_bootstrap=gains,strata=strata,
        readiness_criteria=criteria,source_readiness_passed=all(criteria.values()),
        historical_target_accuracy_and_counts_exact=True,later24_all_targets_and_counts_exact=True,
        auxiliary_artifact='audits/AUXILIARY_ENDPOINTS.json')


def confidence(k,n):
    return [0. if k==0 else float(beta.ppf(.025,k,n-k+1)),
            1. if k==n else float(beta.ppf(.975,k+1,n-k))]


def verify_control_manifest():
    original_path=CONTROL/'MANIFEST.json'
    original=read(original_path)
    mismatches=[]
    for path,expected in original.items():
        actual=sha(C/path)
        if actual!=expected:mismatches.append(dict(path=path,expected=expected,actual=actual))
    # Preserve and explain the known failed original pin rather than omitting it.
    correction_path=CONTROL/'POSTEXECUTION_LOG_MANIFEST.json'
    assert sha(correction_path)=='862863daec6a306ce3edd3e713379db4607076b929052f204b7c2dbf70d55a7b'
    correction=read(correction_path)
    assert correction['original_manifest_sha256']==sha(original_path)
    assert C/correction['original_manifest_path']==original_path
    assert mismatches==correction['mismatches']
    assert len(mismatches)==1
    stdout='artifacts/decision_controls/RUN.stdout'
    assert mismatches[0]['path']==stdout
    assert set(correction['final_files'])==set(original)
    for path,digest in correction['final_files'].items():assert sha(C/path)==digest,path
    raw=(C/stdout).read_bytes()
    lines=raw.splitlines(keepends=True)
    prefix=b''.join(lines[:-1])
    prefix_sha=hashlib.sha256(prefix).hexdigest()
    assert prefix_sha==original[stdout]==correction['stdout_prefix_without_final_line_sha256']
    final=json.loads(lines[-1])
    result=read(CONTROL/'RESULT.json')
    assert final==correction['appended_final_line']==dict(status=result['status'],duration_seconds=result['duration_seconds'])
    assert correction['numerical_or_protocol_files_changed'] is False
    assert correction['access_release'] is False
    return dict(original_manifest_sha256=sha(original_path),
        original_stdout_pin_mismatch_preserved=mismatches,
        postexecution_record_sha256=sha(correction_path),
        stdout_without_appended_final_status_matches_original_pin=True,
        final_status_matches_unchanged_result=True,all_scientific_pins_unchanged=True)


def verify_controls():
    output=read(CONTROL/'RESULT.json');plan=read(CONTROL/'CALIBRATION_FREEZE.json')
    pinned(CONTROL/'CALIBRATION_FREEZE.json')
    manifest_check=verify_control_manifest()
    with np.load(CONTROL/'FROZEN_CONTROL_INPUTS.npz',allow_pickle=False) as z:
        inputs={k:z[k] for k in z.files}
    with np.load(POP/'artifacts/method_audit/CONSUMED_SOURCE_EXACT100.npz',allow_pickle=False) as a,np.load(POP/'artifacts/results/SOURCE_ARRAYS.npz',allow_pickle=False) as b:
        error=np.concatenate((a['observed']-a['rnn'].mean(1),b['observed'][:,:,:2].mean(2)-b['rnn_means']))
    error-=error.mean(0)
    match('control centered residual input',error,inputs['centered_source_residual'])
    # Exact bootstrap-index generation verified without production helper.
    indices=np.random.default_rng(SEED).integers(0,20,(REPS,20))
    counts=np.array([np.bincount(row,minlength=20) for row in indices])
    match('control ordered bootstrap counts',counts,inputs['bootstrap_counts'],0.)
    cases=plan['cases_candidate_growth_persistence_shift_from_template_point5']
    pools={'primary_pooled64':inputs['primary_bounded_residual'][None],
           'double_variability_bounded':inputs['double_bounded_residual'][None],
           'shared_empirical_lab_offset':inputs['shared_lab_offset_bounded_residual']}
    rates={};subset_checks=[]
    for name,pool in pools.items():
        with np.load(CONTROL/(name+'_REPLICATES.npz'),allow_pickle=False) as z:rep={k:z[k] for k in z.files}
        result=output['constructions'][name]
        drawn=pool[rep['environment_index'][:,None],rep['draws']]
        mean=drawn.mean(1);truth=pool.mean(1)[rep['environment_index']]
        match(name+' mean errors',mean,rep['mean_errors'])
        match(name+' finite environment truth',pool.mean(1),rep['finite_environment_truth_residual'])
        rates[name]={}
        for case,shifts in cases.items():
            candidate,growth,persistence=shifts
            point=np.array([(np.abs(mean-baseline).mean(1)-np.abs(mean-candidate).mean(1)) for baseline in (growth,persistence)]).T
            true=np.array([(np.abs(truth-baseline).mean(1)-np.abs(truth-candidate).mean(1)) for baseline in (growth,persistence)]).T
            match(name+' '+case+' point gains',point,rep[case+'__point_gain'])
            match(name+' '+case+' true gains',true,rep[case+'__true_gain'])
            lo,hi=rep[case+'__lower_gain'],rep[case+'__upper_gain']
            success=np.all((point>=.05)&(lo>0),axis=1)
            match(name+' '+case+' decisions',success,rep[case+'__success'],0.)
            count=int(success.sum());n=len(success)
            row=result['cases'][case]
            assert row['decision_rate']['count']==count
            match(name+' '+case+' rate',count/n,row['decision_rate']['rate'])
            match(name+' '+case+' exact binomial bounds',confidence(count,n),row['decision_rate']['interval95_ClopperPearson'])
            material=np.all(true>=.05-1e-13,axis=1)
            false=int(np.sum(success&~material))
            assert false==row['false_material_among_all_cohorts']['count']
            assert int(material.sum())==row['true_material_cohorts']
            coverage=np.all((lo-1e-13<=true)&(true<=hi+1e-13),axis=1)
            assert int(coverage.sum())==row['joint_gain_interval95_coverage']['count']
            rates[name][case]=dict(count=count,n=n,rate=count/n,
                interval95=confidence(count,n),false_material_decisions=false)
        # Three fixed cohorts per construction: regenerate all20k resampled
        # six-bin means directly from ordered animal indices, not count matrix.
        for index in (0,703,1999):
            boot=drawn[index][indices].mean(1)
            for case,(candidate,growth,persistence) in cases.items():
                for j,baseline in enumerate((growth,persistence)):
                    gain=np.abs(boot-baseline).mean(1)-np.abs(boot-candidate).mean(1)
                    interval=np.quantile(gain,[.025,.975])
                    match(f'{name} control cohort{index} {case} interval{j}',interval,
                          [rep[case+'__lower_gain'][index,j],rep[case+'__upper_gain'][index,j]])
            subset_checks.append(dict(construction=name,replicate=index,bootstrap=20000,cases=len(cases)))
    primary=rates['primary_pooled64']
    criteria={case:(r['rate']>=.8 if case.startswith('signal_') else r['rate']<=.05) for case,r in primary.items()}
    assert criteria==output['primary_checks']
    assert all(criteria.values())==output['primary_controls_passed']
    return dict(primary_controls_passed=all(criteria.values()),primary_criteria=criteria,
        decision_rates=rates,all_replicate_point_truth_decision_and_count_reductions_verified=True,
        manifest_finalization=manifest_check,
        independent_full_bootstrap_subset=subset_checks,
        limitation='Full2k x20k bootstrap was not regenerated; every saved replicate reduction plus nine fixed cohort distributions was verified.',
        interpretation='Primary signal sensitivity below80% is decisive. The5.10% equal-error null point miss is imprecise. Shared-lab nominal nulls need conditional-truth interpretation; zero-MAE percentile coverage is nonregular, not equivalence.')


def verify_known_learner():
    folder=C/'artifacts/known_learner'
    pinned(folder/'FREEZE.json')
    result=read(folder/'RESULT.json');plan=read(folder/'FREEZE.json')
    assert result['freeze_sha256']==sha(folder/'FREEZE.json')
    subjects=[r['subject'] for r in plan['selected_prefixes']]
    assert len(subjects)==7
    for row in result['manifest']:assert sha(ROOT/row['path'])==row['sha256']
    curves={};streams={}
    for policy in ('standard','external'):
        curves[policy]={};streams[policy]={}
        for role in ('truth_rho0.8','selected_forecast')+ (('growth_forecast',) if policy=='external' else ()):
            paths=[folder/(s+'__'+policy+'__'+role+'.npz') for s in subjects]
            draws=[]
            for path in paths:
                with np.load(path,allow_pickle=False) as z:
                    draws.append(z['samples'][:,:,:2].mean(2))
            streams[policy][role]=draws
            curves[policy][role]=np.array([d.mean(0) for d in draws])
    grid=[]
    truth=curves['standard']['truth_rho0.8']
    for rho in GRID:
        predicted=[]
        for subject in subjects:
            with np.load(FIT/f'rho_{rho:.1f}'/(subject+'.npz'),allow_pickle=False) as z:
                predicted.append(z['samples'][:,:,:2].mean(2).mean(0))
        loss=float(np.abs(truth-np.array(predicted)).mean())
        reported=next(r for r in result['grid_results'] if r['rho']==rho)
        match('known control fit loss '+str(rho),loss,reported['equal_lab_curve_mae'])
        grid.append((rho,loss))
    minimum=min(loss for rho,loss in grid)
    chosen=max(rho for rho,loss in grid if loss<=minimum+.001)
    assert chosen==result['selected_control_rho']
    policies={}
    for policy in ('standard','external'):
        tc=curves[policy]['truth_rho0.8'];pc=curves[policy]['selected_forecast']
        reported=result['policies'][policy]
        macro=float(np.abs(tc-pc).mean());pooled=float(np.abs(tc.mean(0)-pc.mean(0)).mean())
        match('known '+policy+' macro',macro,reported['equal_lab_curve_mae'])
        match('known '+policy+' pooled',pooled,reported['population_curve_mae'])
        match('known '+policy+' bias',(tc-pc).mean(),reported['mean_bias_observed_minus_forecast'])
        match('known '+policy+' truth curve',tc.mean(0),reported['truth_population_curve'])
        match('known '+policy+' forecast curve',pc.mean(0),reported['forecast_population_curve'])
        assert reported['predictive_expected_law_success']==(pooled<=.01)
        for j,subject in enumerate(subjects):
            record=next(r for r in reported['per_prefix'] if r['subject']==subject)
            match('known '+policy+' '+subject+' truth',tc[j],record['truth_curve'])
            match('known '+policy+' '+subject+' forecast',pc[j],record['forecast_curve'])
            match('known '+policy+' '+subject+' MAE',np.abs(tc[j]-pc[j]).mean(),record['curve_mae'])
        for role,key in [('truth_rho0.8','truth_scalar_conditional_mc_se'),('selected_forecast','forecast_scalar_conditional_mc_se')]+([('growth_forecast','growth_scalar_conditional_mc_se')] if policy=='external' else []):
            draws=streams[policy][role]
            se=float(np.sqrt(sum(np.var(d.mean(1),ddof=1)/len(d) for d in draws))/len(draws))
            match('known '+policy+' '+key,se,reported[key])
        policies[policy]=dict(macro_curve_mae=macro,population_curve_mae=pooled)
        if policy=='external':
            gc=curves[policy]['growth_forecast']
            growth=float(np.abs(tc.mean(0)-gc.mean(0)).mean())
            match('known external growth pooled',growth,reported['growth_population_curve_mae'])
            match('known external growth macro',np.abs(tc-gc).mean(),reported['growth_equal_lab_curve_mae'])
            match('known external gain',growth-pooled,reported['population_curve_mae_advantage_over_growth'])
            policies[policy]['gain_over_growth']=growth-pooled
    contrast=float(curves['external']['truth_rho0.8'].mean()-curves['standard']['truth_rho0.8'].mean())
    match('known fixed-standard contrast',contrast,result['truth_mean_fixed_minus_standard'])
    assert result['exact_parameter_recovery']==(chosen==result['true_rho'])
    assert result['expected_law_success_both_policies']==all(x['population_curve_mae']<=.01 for x in policies.values())
    return dict(reconstructed=True,selected_rho=chosen,true_rho=result['true_rho'],policies=policies,
        expected_law_success_both_policies=result['expected_law_success_both_policies'],
        interpretation='Conditional on supplied consumed prefixes and model-specific initial uncertainty; not whole-animal recovery or empirical transport.')


def replay_two(selected):
    import common
    from session_model import from_frozen,load_session
    from baselines import draw_initial,load_bank
    from rnn_rollout import calibration_particles
    spec=importlib.util.spec_from_file_location('independent_transition_reuse',C/'audits/independent_transition_check.py')
    independent=importlib.util.module_from_spec(spec);spec.loader.exec_module(independent)
    first,second=canonical_ids()
    subjects=[min(group,key=lambda s:hashlib.sha256(s.encode()).hexdigest()) for group in (first,second)]
    model=load_session(C/'model_session_transition.npz') if selected=='session' else from_frozen(common.MODEL,1.)
    bank=load_bank(common.BANK)
    answers=[]
    for subject in subjects:
        prefix=common.load_consumed(subject,cap=1000,purpose='independent selected-rule512particle replay; consumed first1000only')
        with np.load(COMP/subject/'observed.npz',allow_pickle=False) as z:starts=z['session_start']
        seed=common.seed_for(subject)
        engagement=draw_initial(prefix,bank,512,seed+211,exclude=subject,competence='growth')
        initial,metadata=calibration_particles(model,prefix,512,seed+313)
        independent_initial,_,_=independent.independent_particles(prefix,model,512,seed+313)
        fisher=max(float(np.max(np.abs(initial[k]-independent_initial[k]))) for k in ('w','h'))
        assert fisher<1e-6,(subject,fisher)
        expected=independent.independent_autonomous(model,prefix,starts,engagement,initial,'standard',seed)
        errors={}
        with np.load(COMP/subject/(selected+'.npz'),allow_pickle=False) as z:
            for key in expected:
                errors[key]=float(np.max(np.abs(expected[key]-z[key])))
                assert errors[key]==0.,(subject,key,errors[key])
        answers.append(dict(subject=subject,stratum='historical40' if subject in first else 'later24',
            selection='minimum SHA256 subject ID inside each stratum',model=selected,
            particles=512,horizon=3000,prefix_cap=1000,forecast_arrays_max_abs=errors,
            independent_prefix_fisher_particle_max_abs=fisher,real_future_outcomes_read=0))
    return answers


def write_review(out):
    fit=out['fit'];comparison=out['comparison'];control=out['controls']
    lines=['# Independent final result review','','2026-10-29. **PASS for the numerical and access audit.** All source observations remain consumed development evidence. Pan20 prefixes/outcomes remain sealed. This review does not earn an old gate or settle cross-curriculum prediction.','',
        'The executable `independent_result_check.py` independently reduces saved forecast arrays; it imports no production scoring or selection helper. `INDEPENDENT_RESULT_CHECK.json` records checked quantities, input hashes and two forecast replays. `AUXILIARY_ENDPOINTS.json` supplies all four saved channels.','',
        f"The six-value fit selects rho={fit['selected_rho']:.1f} from{fit['eligible']} eligible of62 allocated fit animals under the frozen largest-rho-within.001 rule. Every within-session neural parameter remains byte-exact numerically.",'',
        '| Approach | Equal-lab curve MAE | Pooled curve MAE | Individual accuracy CRPS |','|---|---:|---:|---:|']
    for kind,m in comparison['metrics'].items():lines.append(f"|{kind}|{100*m['equal_lab_curve_mae']:.3f}pp|{100*m['pooled_population_curve_mae']:.3f}pp|{m['individual_accuracy_marginal_crps']:.6f}|")
    lines+=['',f"Selected approach: **{comparison['selected_approach']}**. Source readiness: **{comparison['source_readiness_passed']}**. The independent audit reconstructs all lab/stratum/pooled losses, explicit-pair CRPS, conditional simulation SE, selection, five readiness booleans and20,000 paired lab resamples using sorted lab order/seed202610291.",'',
        'Historical40 exact100 equal-side targets and side counts match their frozen derived source. Later24 all four target channels and all counts match their old saved observed files. No historical>=.5 target is substituted. The old40 derived source stores equal-side accuracy rather than separate side numerators; that audit checks its available exact100 estimand/counts, while side/auxiliary values are reported from the newly saved capped-read targets.','',
        'A first stopped audit attempt used an empirical-distribution n² pair denominator for CRPS and differed by.0001214 on its first score. Inspection confirmed that the frozen metric specifies the unbiased independent-pair n(n−1) denominator. Only the new independent audit formula was corrected; production code, metrics, forecasts and thresholds were unchanged.','',
        'A second stopped audit found the original control-manifest stdout hash mismatch. The owner preserved that manifest and froze `POSTEXECUTION_LOG_MANIFEST.json`, documenting the sole appended final status/duration line. This audit verifies every original pin, retains that stdout failure, verifies the complete final-file mapping, proves that deleting exactly the final line restores the original stdout hash, and checks that the final JSON equals the unchanged result status/duration. No scientific code, protocol or numerical result was changed.','',
        f"Primary comparative-decision controls passed: **{control['primary_controls_passed']}**. Every replicate's point gains, known finite-population gains, decisions and reported rate/false-material/interval-coverage counts are independently checked; all20,000 resamples are additionally regenerated directly for nine fixed simulated cohorts across all cases. This is a bounded independent check, not a complete second2,000-cohort bootstrap run.",'',
        'Both±10pp primary signal success rates fall below the frozen80% requirement. Their MonteCarlo intervals exclude80%, so this is sufficient to stop regardless of the imprecise5.10% equal-error null point miss. Shared-lab nominal labels can change conditional truth, and absolute-MAE percentile intervals are nonregular at zero; neither is evidence of biological absence or equivalence.','',
        'The two selected-rule replays choose the minimum SHA256 ID within each historical stratum. They read only consumed first1000-row prefixes, use already saved source opportunity starts, and generate512-particle futures with an independent vector GRU/transition loop and endpoint reduction. Curves, counts, coefficient bins and final memory agree exactly. Historical loggers are forbidden and historical ledger hashes/freeze remain unchanged.','',
        'Known conditional learner control: saved2048-particle truth/512-particle forecast arrays independently reconstruct the grid choice, both trainers\' curve errors, scalar simulation SE and growth comparison. Recovery in these supplied-prefix contexts is distinct from empirical transport and whole-animal parameter recovery.','',
        'At least one prescribed readiness condition fails; this implementation branch therefore stops before protected prefixes. The central question—whether source-inferred dynamics predict acquisition under a different curriculum better than exposure growth—remains unresolved. A source fit or passing artifact audit does not replace that test.','']
    (C/'audits/RESULT_REVIEW.md').write_text('\n'.join(lines))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--skip-replay',action='store_true')
    args=parser.parse_args()
    required=[FIT/'RESULT.json',COMP/'RESULT.json',CONTROL/'RESULT.json',C/'model_session_transition.npz']
    missing=[str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        print(json.dumps(dict(status='pending',missing=missing,no_outputs_changed=True)));return
    ledgers=[OLD/'protocols/EXPOSURE.jsonl',POP/'protocols/EXPOSURE.jsonl']
    before={str(p.relative_to(ROOT)):sha(p) for p in ledgers}
    pinned(C/'protocols/FIT_FREEZE.json');pinned(C/'protocols/COMPARISON_FREEZE.json');pinned(POP/'protocols/FREEZE.json')
    import common
    def forbid(*a,**k):raise RuntimeError('Historical exposure logger invoked')
    common.oldpop.event=forbid;common.mixed.log=forbid
    import data_io
    data_io.exposure=forbid
    fit=verify_fit();comparison=verify_comparison();controls=verify_controls();known=verify_known_learner()
    replays=[] if args.skip_replay else replay_two(comparison['selected_approach'])
    after={str(p.relative_to(ROOT)):sha(p) for p in ledgers}
    assert before==after
    pinned(POP/'protocols/FREEZE.json')
    inputs=[FIT/'RESULT.json',COMP/'RESULT.json',CONTROL/'RESULT.json',C/'model_session_transition.npz',
            C/'protocols/DESIGN.md',C/'code/compare_source.py',C/'code/fit_transition.py',
            C/'code/calibrate_decision.py',C/'code/comparison_statistics.py',
            CONTROL/'POSTEXECUTION_LOG_MANIFEST.json',C/'artifacts/known_learner/RESULT.json']
    out=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),passed=True,
        scope='Independent saved-array numerical audit; all source development consumed; Pan20sealed',
        persistent_question='Can source-inferred dynamics forecast1000+3000 acquisition across curricula better than growth?',
        fit=fit,comparison=comparison,controls=controls,known_learner_control=known,selected_rule_replays=replays,
        numeric_checks=len(CHECKS),maximum_numeric_discrepancy=max(r['max_abs'] for r in CHECKS),
        checks=CHECKS,inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        historical_ledger_sha256_before=before,historical_ledger_sha256_after=after,
        historical_freeze_intact=True,protected_prefix_accesses=0,protected_future_accesses=0,
        stop_before_protected_prefixes=not(comparison['source_readiness_passed'] and controls['primary_controls_passed']),
        scientific_question_resolved=False)
    (C/'audits/INDEPENDENT_RESULT_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
    write_review(out)
    print(json.dumps(dict(passed=True,checks=len(CHECKS),max_abs=out['maximum_numeric_discrepancy'],
        selected=comparison['selected_approach'],rho=fit['selected_rho'],
        source_ready=comparison['source_readiness_passed'],controls_ready=controls['primary_controls_passed'],
        replays=len(replays),stop_before_pan=out['stop_before_protected_prefixes'])))


if __name__=='__main__':main()
