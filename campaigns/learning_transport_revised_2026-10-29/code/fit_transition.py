#!/usr/bin/env python3
"""Finite generative fit of ONE shared session coefficient on consumed source.

No within-session neural parameters are fitted and no independent outcomes are
opened. Every grid cell recomputes prefix MAP/Fisher state under its own rho.
The fitting objective is the equally weighted mean of lab population curve
MAEs at exact +/-100% contrast; animals and six bins are equal within lab.
"""
from pathlib import Path
import argparse
import json
import time
import numpy as np
from session_model import from_frozen, semantic_audit
from common import (C,ROOT,OLD,MODEL,BANK,digest,dump,event,seed_for,allocation,
                    load_consumed,prefix_future,simulate)

OUT=C/'artifacts/transition_fit'
GRID=(.5,.6,.7,.8,.9,1.)
TIE_TOLERANCE=.001
PARTICLES=256


def scalar_curve(samples):
    return np.mean(samples[...,:2],axis=-1)


def fit_objective(records):
    labs=sorted(set(r['lab'] for r in records))
    lab_records=[]
    for lab in labs:
        group=[r for r in records if r['lab']==lab]
        observed=np.asarray([r['observed'] for r in group],float)
        predicted=np.asarray([r['predicted'] for r in group],float)
        if observed.shape[1:]!=(6,) or not np.isfinite(observed).all():
            raise ValueError('Fit endpoint coverage is incomplete: '+lab)
        oc=observed.mean(0);pc=predicted.mean(0)
        lab_records.append(dict(lab=lab,n=len(group),
            observed_curve=oc.tolist(),predicted_curve=pc.tolist(),
            curve_mae=float(np.mean(np.abs(oc-pc))),bias_observed_minus_predicted=float(np.mean(oc-pc))))
    return float(np.mean([r['curve_mae'] for r in lab_records])),lab_records


def load_fit_data():
    ids=allocation()['train']
    data=[];disposition=[]
    for subject in ids:
        d=load_consumed(subject,cap=4000,purpose='finite session-transition fit on original consumed62fit subjects')
        n=len(d['choice']);meta=d.get('metadata',{})
        lab=meta.get('lab')
        if not lab:
            raise ValueError('Missing source lab metadata for '+subject)
        eligible=n>=4000
        disposition.append(dict(subject=subject,lab=lab,rows_returned=n,
            eligible_full_horizon=eligible,reason=None if eligible else 'fewer than1000prefix+3000future indexed opportunities'))
        if eligible:
            prefix,starts,observed,counts=prefix_future(d)
            data.append((subject,lab,prefix,starts,observed,counts))
    dump(OUT/'FIT_DISPOSITION.json',dict(allocated=len(ids),eligible=len(data),
        scope='consumed original fit subjects only, returned rows never exceed4000',records=disposition))
    return data


def benchmark():
    """One consumed fit animal,128particles; no numerical selection from it."""
    OUT.mkdir(parents=True,exist_ok=True)
    coverage={r['subject']:int(r['trials']) for r in json.loads((OLD/'data/COVERAGE.json').read_text())}
    subject=next(s for s in allocation()['train'] if coverage.get(s,0)>=4000)
    data=load_consumed(subject,cap=4000,purpose='bounded128particle runtime benchmark; no model selection')
    prefix,starts,observed,counts=prefix_future(data)
    model=from_frozen(MODEL,.8,{'role':'benchmark only; not fitted model'})
    t=time.monotonic()
    result=simulate(model,prefix,starts,kind='rnn',policy='standard',n=128,
        seed=seed_for(subject),subject=subject)
    elapsed=time.monotonic()-t
    info=dict(subject=subject,selection='first original fit subject with metadata-certified4000opportunities',particles=128,rho=.8,seconds=elapsed,
        actual_horizon=len(starts),grid=GRID,fit_particles=PARTICLES,
        upper_nominal_grid_seconds=elapsed*(PARTICLES/128)*len(GRID)*len(allocation()['train']),
        estimated_peak_memory_note='one256particle3000trial rollout stores~7MB contrasts+choices;GRU arrays<2MB;source batch<=4000rows/animal',
        returned_source_rows=len(data['choice']),independent_outcomes_opened=False,
        model_sha256=digest(MODEL),bank_sha256=digest(BANK))
    dump(OUT/'BENCHMARK.json',info)
    print(json.dumps(info),flush=True)


def check_freeze(path):
    """Support root-relative file manifests without changing historical guards."""
    freeze=json.loads(Path(path).read_text())
    for entry in freeze.get('files',[]):
        p=Path(entry['path'])
        if not p.is_absolute():p=ROOT/p
        if digest(p)!=entry['sha256']:
            raise RuntimeError('Frozen file mismatch: '+str(p))
    if not freeze.get('files'):
        raise ValueError('An explicit nonempty prefit freeze manifest is required')
    return freeze


def fit(freeze_path):
    OUT.mkdir(parents=True,exist_ok=True)
    check_freeze(freeze_path)
    event('transition_grid_fit_started',protocol_freeze_sha256=digest(freeze_path),
        grid=list(GRID),particles=PARTICLES,source_data_status='consumed development',
        protected_pan_prefixes_opened=0,protected_pan_futures_opened=0)
    data=load_fit_data();all_grid=[];started=time.monotonic()
    for rho in GRID:
        model=from_frozen(MODEL,rho,{'role':'finite generative source fit grid cell'})
        folder=OUT/f'rho_{rho:.1f}';folder.mkdir(parents=True,exist_ok=True)
        records=[]
        for subject,lab,prefix,starts,observed,counts in data:
            t=time.monotonic()
            path=folder/f'{subject}.npz';meta_path=path.with_suffix('.json')
            if path.exists() and meta_path.exists():
                record=json.loads(meta_path.read_text())
                if record['rho']!=rho or record['particles']!=PARTICLES or record['freeze_sha256']!=digest(freeze_path):
                    raise RuntimeError('Incompatible existing grid artifact: '+str(path))
                if record['forecast_sha256']!=digest(path):
                    raise RuntimeError('Grid forecast hash mismatch: '+str(path))
            else:
                result=simulate(model,prefix,starts,kind='rnn',policy='standard',
                    n=PARTICLES,seed=seed_for(subject),subject=subject)
                np.savez_compressed(path,**{k:v for k,v in result.items() if isinstance(v,np.ndarray)},
                    observed=observed,observed_counts=counts,session_start=starts)
                record=dict(subject=subject,lab=lab,rho=rho,particles=PARTICLES,
                    observed=np.mean(observed[:,:2],axis=-1).tolist(),
                    predicted=scalar_curve(result['samples']).mean(0).tolist(),
                    seconds=time.monotonic()-t,forecast_path=str(path.relative_to(ROOT)),
                    forecast_sha256=digest(path),freeze_sha256=digest(freeze_path),
                    own_actions_rewards=True,source_data_status='consumed fit development')
                dump(meta_path,record)
            records.append(record)
            print(json.dumps(dict(stage='fit_grid',rho=rho,subject=subject,
                elapsed_seconds=time.monotonic()-started,subject_seconds=time.monotonic()-t)),flush=True)
        loss,labs=fit_objective(records)
        grid_record=dict(rho=rho,objective_equal_lab_curve_mae=loss,
            labs=labs,n_animals=len(records),records=records)
        all_grid.append(grid_record);dump(folder/'SUMMARY.json',grid_record)
        dump(OUT/'GRID_PROGRESS.json',dict(grid=list(GRID),completed=all_grid,
            full_grid_complete=len(all_grid)==len(GRID)))
        print(json.dumps(dict(stage='grid_objective',rho=rho,
            objective_equal_lab_curve_mae=loss,elapsed_seconds=time.monotonic()-started)),flush=True)
    minimum=min(r['objective_equal_lab_curve_mae'] for r in all_grid)
    selected=max((r for r in all_grid if r['objective_equal_lab_curve_mae']<=minimum+TIE_TOLERANCE),key=lambda r:r['rho'])
    metadata=dict(role='one fitted session-transition extension; consumed source development',
        selected_rho=selected['rho'],fit_grid=list(GRID),fitting_particles=PARTICLES,
        fitting_objective='equal lab mean of six500opportunity population curve MAE at exact100percent, equal animals in lab',
        tiebreak='largest rho within0.001 absolute loss of minimum',
        original_updater_sha256=digest(MODEL),bank_sha256=digest(BANK),
        protocol_freeze_sha256=digest(freeze_path),fit_n_animals=len(data),
        fit_n_allocated=len(allocation()['train']),future_horizon=3000,prefix=1000,
        outcome_scope='first4000alreadyconsumed rows per original fit subject',
        no_independent_target_data=True)
    fitted=from_frozen(MODEL,selected['rho'],metadata)
    fitted_path=C/'model_session_transition.npz';fitted.save(fitted_path)
    result=dict(**metadata,grid_results=all_grid,
        minimum_objective=minimum,selected_objective=selected['objective_equal_lab_curve_mae'],
        selected_model_path=str(fitted_path.relative_to(ROOT)),selected_model_sha256=digest(fitted_path),
        elapsed_seconds=time.monotonic()-started,
        code_sha256={str(Path(__file__).relative_to(ROOT)):digest(__file__),
            str((Path(__file__).parent/'session_model.py').relative_to(ROOT)):digest(Path(__file__).parent/'session_model.py')})
    dump(OUT/'RESULT.json',result)
    event('transition_grid_fit_complete',selected_rho=selected['rho'],
        result_sha256=digest(OUT/'RESULT.json'),model_sha256=digest(fitted_path),
        protected_pan_prefixes_opened=0,protected_pan_futures_opened=0)
    print(json.dumps(dict(stage='fit_complete',rho=selected['rho'],minimum_objective=minimum,
        selected_objective=selected['objective_equal_lab_curve_mae'],seconds=time.monotonic()-started)),flush=True)
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--audit',action='store_true')
    parser.add_argument('--benchmark',action='store_true');parser.add_argument('--fit',action='store_true')
    parser.add_argument('--freeze');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.audit:
        audit=semantic_audit(MODEL);dump(OUT/'SEMANTIC_AUDIT.json',audit);print(json.dumps(audit),flush=True)
    if args.benchmark:benchmark()
    if args.fit:
        if not args.freeze:parser.error('--fit requires --freeze')
        fit(Path(args.freeze))


if __name__=='__main__':main()
