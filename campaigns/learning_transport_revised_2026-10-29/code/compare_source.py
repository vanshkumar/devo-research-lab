#!/usr/bin/env python3
"""Finite comparison on64 CONSUMED source animals, never confirmation."""
from pathlib import Path
import argparse
import json
import time
import numpy as np
from common import (C, ROOT, OLD, POP, MODEL, BANK, load_rnn, load_consumed,
                    prefix_future, simulate, accuracy, macro_lab_curve_loss,
                    comparison_ids, digest, dump, event, historical_check, seed_for)
from session_model import load_session
from evaluation import marginal_crps

OUT = C / 'artifacts/source_comparison'
KINDS = ('existing', 'session', 'growth', 'persistence')
PARTICLES = 512
BOOTSTRAP = 20000
BOOTSTRAP_SEED = 202610291


def check_freeze():
    path = C / 'protocols/COMPARISON_FREEZE.json'
    obj = json.loads(path.read_text())
    for r in obj['files']:
        if digest(ROOT / r['path']) != r['sha256']:
            raise RuntimeError('Comparison pin changed: ' + r['path'])
    historical_check()
    return path


def run(kinds):
    freeze = check_freeze()
    OUT.mkdir(parents=True, exist_ok=True)
    old = load_rnn(MODEL)
    fitted = load_session(C / 'model_session_transition.npz') if 'session' in kinds else None
    for subject in comparison_ids():
        data = load_consumed(subject, 4000, 'finite64animal comparison; consumed development only')
        prefix, starts, observed, counts = prefix_future(data)
        if not np.isfinite(observed).all():
            raise ValueError('Incomplete exact100 source cell: ' + subject)
        folder = OUT / subject
        folder.mkdir(parents=True, exist_ok=True)
        op = folder / 'observed.npz'
        if op.exists():
            with np.load(op) as z:
                assert np.array_equal(z['observed'], observed)
                assert np.array_equal(z['counts'], counts)
        else:
            np.savez_compressed(op, observed=observed, counts=counts,
                                session_start=starts)
        for kind in kinds:
            path = folder / (kind + '.npz')
            meta_path = path.with_suffix('.json')
            model = fitted if kind == 'session' else old
            model_path = C / 'model_session_transition.npz' if kind == 'session' else MODEL
            if path.exists() and meta_path.exists():
                meta = json.loads(meta_path.read_text())
                assert meta['forecast_sha256'] == digest(path)
                assert meta['model_sha256'] == digest(model_path)
                assert meta['freeze_sha256'] == digest(freeze)
                continue
            started = time.monotonic()
            out = simulate(model, prefix, starts,
                           kind='rnn' if kind in ('existing','session') else kind,
                           policy='standard', n=PARTICLES,
                           seed=seed_for(subject), subject=subject)
            np.savez_compressed(path, **{k:v for k,v in out.items()
                                        if isinstance(v, np.ndarray)})
            target = accuracy(observed)
            draws = accuracy(out['samples'])
            meta = dict(subject=subject, lab=data['metadata']['lab'], kind=kind,
                        source_status='consumed development; not fresh validation',
                        n_particles=PARTICLES, rho=float(getattr(model, 'rho', 1.)),
                        model_sha256=digest(model_path), bank_sha256=digest(BANK),
                        freeze_sha256=digest(freeze), forecast_sha256=digest(path),
                        observed_sha256=digest(op), calibration=out['calibration'],
                        individual_accuracy_crps=float(marginal_crps(draws, target).mean()),
                        seconds=time.monotonic()-started)
            dump(meta_path, meta)
            event('consumed_comparison_forecast_saved', subject=subject,
                  model=kind, sha256=digest(path), independent_outcomes=False)
            print(json.dumps(dict(stage='source_comparison',subject=subject,
                                  model=kind,seconds=meta['seconds'])), flush=True)


def lab_gain_ci(y, model, baseline, labs):
    groups = np.unique(labs)
    differences = []
    for lab in groups:
        ix = labs == lab
        a = np.abs((y[ix]-model[ix]).mean(0)).mean()
        b = np.abs((y[ix]-baseline[ix]).mean(0)).mean()
        differences.append(b-a)
    differences = np.asarray(differences)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    values = differences[rng.integers(len(groups), size=(BOOTSTRAP,len(groups)))].mean(1)
    return dict(gain=float(differences.mean()), lower=float(np.quantile(values,.025)),
                upper=float(np.quantile(values,.975)), labs=len(groups),
                by_lab=dict(zip(groups.tolist(),differences.tolist())),
                scope='paired lab-resampling development robustness only; few labs')


def summarize():
    freeze = check_freeze()
    ids = comparison_ids()
    labs, observed, counts, draws = [], [], [], {k:[] for k in KINDS}
    records = []
    for subject in ids:
        folder = OUT / subject
        with np.load(folder / 'observed.npz') as z:
            observed.append(z['observed']); counts.append(z['counts'])
        for kind in KINDS:
            path = folder / (kind+'.npz')
            meta = json.loads(path.with_suffix('.json').read_text())
            assert meta['forecast_sha256'] == digest(path)
            if kind == 'existing':
                labs.append(meta['lab'])
            with np.load(path) as z:
                draws[kind].append(z['samples'])
            records.append(dict(subject=subject,model=kind,
                                path=str(path.relative_to(ROOT)),sha256=digest(path)))
    observed=np.asarray(observed); labs=np.asarray(labs); counts=np.asarray(counts)
    draws={k:np.asarray(v) for k,v in draws.items()}
    y=accuracy(observed)
    expected={k:accuracy(v).mean(1) for k,v in draws.items()}
    metrics={}
    for kind,pred in expected.items():
        macro,bylab=macro_lab_curve_loss(y,pred,labs)
        samples=accuracy(draws[kind])
        crps=[float(marginal_crps(samples[i],y[i]).mean()) for i in range(len(ids))]
        se=np.std(samples.mean((0,2)),ddof=1)/np.sqrt(PARTICLES)
        # One independent particle stream per animal; variance of cohort means
        # sums per-animal particle variances, with the six-bin mean retained.
        cohort_se=np.sqrt(np.sum(np.var(samples.mean(2),axis=1,ddof=1)/PARTICLES))/len(ids)
        metrics[kind]=dict(equal_lab_curve_mae=macro,by_lab_curve_mae=bylab,
            pooled_population_curve_mae=float(np.abs((y-pred).mean(0)).mean()),
            individual_equal_side_mae=float(np.abs(y-pred).mean()),
            individual_accuracy_marginal_crps=float(np.mean(crps)),
            mean_curve=pred.mean(0).tolist(),mean_accuracy=float(pred.mean()),
            scalar_bias_observed_minus_forecast=float((y-pred).mean()),
            conditional_simulation_scalar_se=float(cohort_se))
    selected='existing' if metrics['existing']['equal_lab_curve_mae'] <= metrics['session']['equal_lab_curve_mae']+.001 else 'session'
    gains={k:lab_gain_ci(y,expected[k],expected['growth'],labs) for k in ('existing','session')}
    strata={}
    for name,ix in [('historical40',np.arange(len(ids))<40),('later24',np.arange(len(ids))>=40)]:
        loss={k:macro_lab_curve_loss(y[ix],p[ix],labs[ix])[0] for k,p in expected.items()}
        pooled={k:float(np.abs((y[ix]-p[ix]).mean(0)).mean()) for k,p in expected.items()}
        strata[name]=dict(n=int(ix.sum()),equal_lab_curve_mae=loss,
            pooled_population_curve_mae=pooled,
            selected_growth_advantage=float(loss['growth']-loss[selected]))
    macro_advantage=metrics['growth']['equal_lab_curve_mae']-metrics[selected]['equal_lab_curve_mae']
    persistence_advantage=metrics['persistence']['equal_lab_curve_mae']-metrics[selected]['equal_lab_curve_mae']
    criteria=dict(macro_growth_gain_at_least2pp=bool(macro_advantage>=.02),
                  macro_persistence_gain_positive=bool(persistence_advantage>0),
                  growth_gain_positive_historical40=bool(strata['historical40']['selected_growth_advantage']>0),
                  growth_gain_positive_later24=bool(strata['later24']['selected_growth_advantage']>0),
                  paired_lab_bootstrap_lower_positive=bool(gains[selected]['lower']>0))
    loo={}
    for lab in np.unique(labs):
        ix=labs!=lab
        loo[str(lab)]=macro_lab_curve_loss(y[ix],expected['growth'][ix],labs[ix])[0]-macro_lab_curve_loss(y[ix],expected[selected][ix],labs[ix])[0]
    result=dict(date='2026-10-29',scope='finite consumed-source development comparison; no new confirmation',
        n_animals=len(ids),n_labs=len(np.unique(labs)),n_particles=PARTICLES,
        target='equal-side exact100 correct share, omissions failures,1000prefix+3000future,6x500bins',
        observed_curve=y.mean(0).tolist(),minimum_side_denominator=int(counts[...,:2].min()),
        metrics=metrics,selected_approach=selected,
        selection_rule='equal-lab curve MAE; existing wins within.001',
        selected_session_rho=float(json.loads((C/'artifacts/transition_fit/RESULT.json').read_text())['selected_rho']),
        growth_comparison=gains,strata=strata,readiness_criteria=criteria,
        source_readiness_passed=all(criteria.values()),
        selected_macro_growth_advantage=float(macro_advantage),
        selected_macro_persistence_advantage=float(persistence_advantage),
        leave_one_lab_out_growth_advantage=loo,bootstrap_repetitions=BOOTSTRAP,
        bootstrap_seed=BOOTSTRAP_SEED,forecast_records=records,
        comparison_freeze_sha256=digest(freeze),
        protected_prefixes_opened=0,protected_futures_opened=0)
    dump(OUT/'RESULT.json',result)
    np.savez_compressed(OUT/'COMPARISON_ARRAYS.npz',subjects=np.asarray(ids),labs=labs,
                        observed=observed,counts=counts,**draws)
    event('finite_source_comparison_complete',selected=selected,
          source_readiness_passed=result['source_readiness_passed'],
          result_sha256=digest(OUT/'RESULT.json'),protected_access=False)
    print(json.dumps({k:v for k,v in result.items() if k!='forecast_records'},indent=2),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',choices=['baselines','alternative','summarize'],required=True)
    args=parser.parse_args()
    if args.phase=='baselines':run(['existing','growth','persistence'])
    elif args.phase=='alternative':run(['session'])
    else:summarize()
