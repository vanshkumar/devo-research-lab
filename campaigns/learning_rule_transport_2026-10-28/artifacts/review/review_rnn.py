"""Independent retained-source-sample review of the postvalidation RNN.

Run only after both source folders finish. No external outcomes, raw
unbounded source history, model fitting or calibration tuning is consumed.
"""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from review_scores import independent_score, average, boot, digest

C = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def main():
    original = json.loads((OUT/'SOURCE_REVIEW_SCORES.json').read_text())
    primary_ids = {r['subject'] for r in original if r['horizon']==3000 and r['full_horizon']}
    all_ids = {r['subject'] for r in original}
    canonical_order = json.loads((C/'artifacts/results/SUBJECT_ORDER.json').read_text())
    coverage = {r['subject']:r for r in json.loads((C/'data/COVERAGE.json').read_text())}
    baseline = {(r['subject'],r['model']):r for r in original
                if r['horizon']==3000 and r['full_horizon'] and r['arm']=='autonomous'}
    static = {}
    with (C/'tables/conditional_nll.csv').open() as f:
        for r in csv.DictReader(f):static[r['subject']] = float(r['static_nll'])
    rows = []
    conditional = []
    ycurves = []
    mean_curves = []
    manifests = []
    for tag in ['rnn_source_animals','rnn_source_labs']:
        folder = C/'artifacts/forecasts'/tag
        saved_files = list(folder.glob('*__scores.json'))
        saved = [r for p in saved_files for r in json.loads(p.read_text())]
        for path in sorted(folder.glob('*__observed.npz')):
            subject = path.name.removesuffix('__observed.npz')
            pp = folder/(subject+'__rnnglm32.npz')
            if not pp.exists() or not any(r['subject']==subject for r in saved):continue
            with np.load(path) as z:y_all=z['observed']
            with np.load(pp) as z:a_all=z['samples_primary'];a_raw=z['samples']
            assert a_all.shape[1] <= 10
            for p in [path,pp]:manifests.append(dict(path=str(p.relative_to(C)),sha256=digest(p)))
            for horizon in [1000,3000,5000]:
                b=min(len(y_all),horizon//500)
                r=dict(subject=subject,lab=coverage[subject]['lab'],split=coverage[subject]['split'],
                       model='rnnglm32',horizon=horizon,full_horizon=len(y_all)>=horizon//500,
                       actual_bins=b,**independent_score(a_all[:,:b],y_all[:b]))
                ref=[x for x in saved if x['subject']==subject and x['arm']=='autonomous' and x['horizon']==horizon]
                assert len(ref)==1
                assert abs(r['crps']-ref[0]['crps'])<1e-15
                rows.append(r)
            if subject in primary_ids:
                cr=next(r for r in saved if r['subject']==subject and r['arm']=='conditional_diagnostic' and r['horizon']==3000)
                conditional.append(dict(subject=subject,binary_nll=cr['binary_nll'],static_nll=static[subject],
                                        gain=static[subject]-cr['binary_nll'],curve_crps_diagnostic=cr['crps'],
                                        high_mae_diagnostic=cr['high_accuracy_mae']))
                ycurves.append(y_all[:6]);mean_curves.append(a_all[:,:6].mean(axis=0))
    complete_ids={r['subject'] for r in rows if r['horizon']==3000 and r['full_horizon']}
    available_ids={r['subject'] for r in rows}
    if complete_ids != primary_ids or available_ids != all_ids:
        raise RuntimeError(f'RNN source evaluation incomplete: primary {len(complete_ids)}/{len(primary_ids)}, available {len(available_ids)}/{len(all_ids)}')
    summaries=[];paired=[]
    for horizon in [1000,3000,5000]:
     for full in [True,False]:
      for group in ['all','animal_holdout','lab_holdout','hoferlab','wittenlab']:
        rr=[r for r in rows if r['horizon']==horizon and (not full or r['full_horizon'])
            and(group=='all' or r['split']==group or r['lab']==group)]
        if not rr:continue
        summaries.append(dict(horizon=horizon,full_only=full,group=group,n=len(rr),**average(rr)))
        if horizon != 3000 or not full:continue
        for base in ['growth','persistence']:
            d=[baseline[(r['subject'],base)]['crps']-r['crps'] for r in sorted(rr,key=lambda r:canonical_order.index(r['subject']))]
            h=[baseline[(r['subject'],base)]['high_accuracy_mae']-r['high_accuracy_mae'] for r in sorted(rr,key=lambda r:canonical_order.index(r['subject']))]
            rng=np.random.default_rng(891);v=np.asarray(d);bs=v[rng.integers(0,len(v),(10000,len(v)))].mean(axis=1)
            paired.append(dict(group=group,baseline=base,crps=boot(d),high_mae=boot(h),
                               gate_lower005=float(np.quantile(bs,.005)),
                               relative_crps_gain=float(np.mean(d)/np.mean([baseline[(r['subject'],base)]['crps'] for r in rr])),
                               high_mae_relative_gain=float(np.mean(h)/np.mean([baseline[(r['subject'],base)]['high_accuracy_mae'] for r in rr]))))
    result=dict(stage='post-source-validation diagnostic expansion; original four-candidate source gate unchanged',
                rnn_freeze_sha256=digest(C/'protocols/RNN_FREEZE.json'),
                final_model_sha256=digest(C/'artifacts/rnn/main_best.npz'),
                original_freeze_sha256=digest(C/'protocols/FREEZE.json'),
                raw_equals_calibrated=all(np.array_equal(np.load(C/m['path'])['samples'],np.load(C/m['path'])['samples_primary'])
                                         for m in manifests if m['path'].endswith('__rnnglm32.npz')),
                summary=summaries,paired=paired,
                conditional=dict(n=len(conditional),binary_nll=float(np.mean([r['binary_nll'] for r in conditional])),
                                 static_nll=float(np.mean([r['static_nll'] for r in conditional])),
                                 gain=boot([r['gain'] for r in conditional]),
                                 curve_crps_diagnostic=float(np.mean([r['curve_crps_diagnostic'] for r in conditional])),
                                 high_mae_diagnostic=float(np.mean([r['high_mae_diagnostic'] for r in conditional]))),
                mean_curves=dict(observed=np.mean(ycurves,axis=0).tolist(),rnnglm32=np.mean(mean_curves,axis=0).tolist()),
                source_forecast_manifest=manifests)
    (OUT/'RNN_REVIEW_STATS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (OUT/'RNN_REVIEW_SCORES.json').write_text(json.dumps(rows,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['source_forecast_manifest','mean_curves','summary']},indent=2))
    print(json.dumps([r for r in summaries if r['horizon']==3000 and r['full_only']],indent=2))


if __name__=='__main__':main()
