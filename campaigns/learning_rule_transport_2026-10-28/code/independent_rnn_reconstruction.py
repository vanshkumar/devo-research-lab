#!/usr/bin/env python3
"""Independent math/original-byte reconstruction of the postvalidation GRU.

The earlier independent Parquet reader, target builder and explicit-pair
scorer are reused unchanged. No lead RNN model or recurrence is imported.
Source outcomes were already consumed in the original study. External data
remain prohibited. This is not an untouched confirmatory source comparison.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, time
from pathlib import Path
import numpy as np
from independent_reconstruction import original_rows,independent_curves,independent_score,signed,source_allocation,write_json,digest,subset

C=Path(__file__).resolve().parents[1]
OUT=C/'artifacts/rnn/reconstruction'
RNN_FREEZE=C/'protocols/RNN_FREEZE.json'
RNN_FREEZE_SHA='a4bcaac21b1302d0527daa31df119bd64b38c7389fcdd8d9323f7eecad5cd652'
MODEL=C/'artifacts/rnn/rnnglm32_nested_best.npz'

def rnn_folder(split):return C/'artifacts/forecasts'/('rnn_source_animals'if split=='animal_holdout'else'rnn_source_labs')

def verify():
    if digest(RNN_FREEZE)!=RNN_FREEZE_SHA:raise PermissionError('Unexpected RNN scientific freeze')
    fz=json.loads(RNN_FREEZE.read_text());rows=[]
    for r in fz['files']:
        actual=digest(C/r['path']);ok=actual==r['sha256'];rows.append(dict(path=r['path'],actual=actual,expected=r['sha256'],match=ok))
        if not ok:raise ValueError('RNN frozen file changed '+r['path'])
        if r['path']=='protocols/FREEZE.json':
            for original in json.loads((C/r['path']).read_text())['files']:
                oldactual=digest(C/original['path'])
                if oldactual!=original['sha256']:raise ValueError('Original scientific freeze changed '+original['path'])
    # The reused helpers are the original independent implementation, not
    # replacements with lead data or score functions.
    helper=C/'code/independent_reconstruction.py';snapshot=C/'artifacts/reconstruction/independent_reconstruction.snapshot.py'
    if digest(helper)!=digest(snapshot):raise ValueError('Original independent helper changed after its pinned reconstruction')
    write_json(OUT/'FROZEN_BYTES_VERIFICATION.json',dict(rnn_freeze_sha256=RNN_FREEZE_SHA,files=rows,
                independent_helper_sha256=digest(helper),scope='postvalidation source-only recurrent architecture challenge',external_outcomes_read=False))

def completed(subject,split):
    f=rnn_folder(split)
    return all((f/(subject+s)).is_file()for s in['__rnnglm32.npz','__rnnglm32.json','__rnnglm32__conditional.npz','__observed.npz','__scores.json'])

def load_export():
    with np.load(MODEL,allow_pickle=False)as z:
        if str(z['kind'])!='rnnglm':raise ValueError('Wrong frozen recurrent architecture')
        return {k:np.asarray(z[k],float)for k in z.files if k not in['kind','metadata']}

def logistic(a):return 1/(1+np.exp(-a))

def manual_recurrence(params,data,w0,h0=None):
    """PyTorch GRU gate order r,z,n, followed by two rectified layers.

    Probability precedes current response/reward. Native omission0 holds
    both latent states. The reset gate multiplies the hidden contribution to
    the candidate, including its hidden bias, as in the pinned GRU source.
    """
    x=signed(data);choice=data['choice'];reward=data['feedbackType']>0
    H=len(params['bhh'])//3;hidden=np.zeros(H)if h0 is None else np.asarray(h0,float).copy()
    w=np.asarray(w0,float).copy();p=np.empty(len(x));weights=np.empty((len(x),3));hidden_checkpoints=[]
    for t in range(len(x)):
        z=np.tanh(5*x[t])/np.tanh(5.)
        phi=np.array([max(z,0.),min(z,0.),1.])
        p[t]=float(logistic(np.clip(np.dot(w,phi),-50,50)));weights[t]=w
        if choice[t]!=0:
            v=np.concatenate([w,np.array([z,1.,float(data['session_start'][t]),float(choice[t]==-1),float(reward[t]),float(z>0)])])
            input_affine=params['Wih']@v+params['bih']
            hidden_affine=params['Whh']@hidden+params['bhh']
            reset=logistic(input_affine[:H]+hidden_affine[:H])
            update=logistic(input_affine[H:2*H]+hidden_affine[H:2*H])
            candidate=np.tanh(input_affine[2*H:]+reset*hidden_affine[2*H:])
            hidden=(1-update)*candidate+update*hidden
            first=np.maximum(params['A']@hidden+params['a'],0)
            second=np.maximum(params['B']@first+params['b'],0)
            w=w+params['scale']*(params['C']@second+params['cc'])
        if(t+1)%500==0:hidden_checkpoints.append(hidden.copy())
    return p,weights,w,hidden,np.asarray(hidden_checkpoints)

def reconstruct(subject,info):
    if subject not in {x['subject']for x in source_allocation()}:raise PermissionError('External/dev subject rejected')
    if not completed(subject,info['split']):raise RuntimeError('Wait for completed frozen RNN forecast and scores')
    data,original_meta=original_rows(subject,max_rows=6000);folder=rnn_folder(info['split']);target,counts=independent_curves(data)
    with np.load(folder/(subject+'__observed.npz'),allow_pickle=False)as z:
        if not np.array_equal(target,z['observed'],equal_nan=True)or not np.array_equal(counts,z['counts']):raise ValueError('RNN original target/count mismatch')
    meta=json.loads((folder/(subject+'__rnnglm32.json')).read_text());cal=meta['calibration'];params=load_export()
    if meta['model_sha256']!=digest(MODEL):raise ValueError('RNN forecast uses another frozen export')
    prefix=subset(data,0,1000);future=subset(data,1000)
    pp,pw,wend,hend,ph=manual_recurrence(params,prefix,cal['w0'])
    delta_w=float(np.max(np.abs(wend-np.asarray(cal['endpoint']))));delta_h=float(np.max(np.abs(hend-np.asarray(cal['hidden_endpoint']))))
    p,w,last_w,last_h,fh=manual_recurrence(params,future,wend,hend)
    with np.load(folder/(subject+'__rnnglm32__conditional.npz'),allow_pickle=False)as z:
        stored_p=z['prob_right'];stored_w=z['weights'];stored_h=z['hidden_final'];conditional_samples=z['samples']
    dp=float(np.max(np.abs(p-stored_p)));dw=float(np.max(np.abs(w-stored_w)));dh=float(np.max(np.abs(last_h-stored_h)))
    if max(delta_w,delta_h,dp,dw,dh)>1e-8:raise ValueError('Manual recurrent source reconstruction mismatch '+subject+repr([delta_w,delta_h,dp,dw,dh]))
    # Causality/omission witness on the actual original future sequence.
    t=0;altered={k:v.copy()for k,v in future.items()};altered['choice'][t]=1 if altered['choice'][t]!=1 else -1;altered['feedbackType'][t]*=-1
    ap,_,_,_,_=manual_recurrence(params,subset(altered,0,min(3,len(p))),wend,hend)
    same_trial_difference=float(abs(ap[0]-p[0]));assert same_trial_difference==0.
    om={k:v[:1].copy()for k,v in future.items()};om['choice'][0]=0
    _,_,ow,oh,_=manual_recurrence(params,om,wend,hend)
    omission_hold=float(max(np.max(np.abs(ow-wend)),np.max(np.abs(oh-hend))));assert omission_hold==0.
    path=OUT/'independent_probabilities'/(subject+'.npz');path.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(path,prob_right=p,prefix_prob_right=pp,weights=w,prefix_hidden_endpoint=hend,
                        hidden_final=last_h,prefix_hidden_checkpoints=ph,future_hidden_checkpoints=fh)
    lead=json.loads((folder/(subject+'__scores.json')).read_text())
    forecast_path=folder/(subject+'__rnnglm32.npz')
    with np.load(forecast_path,allow_pickle=False)as z:primary=z['samples_primary'];raw=z['samples']
    H=len(data['choice'])-1000;rows=[];numerical=[];conditional=[]
    original_folder=C/'artifacts/forecasts'/('source_animals'if info['split']=='animal_holdout'else'source_labs')
    static=np.asarray(json.loads((original_folder/(subject+'__persistence.json')).read_text())['calibration']['endpoint'])
    sx=signed(future);zz=np.tanh(5*sx)/np.tanh(5.);static_p=logistic(np.column_stack([np.maximum(zz,0),np.minimum(zz,0),np.ones(len(zz))])@static)
    for horizon in[1000,3000,5000]:
        B=min(horizon//500,len(target));observed=target[:B]
        for arm,a in[('autonomous',primary),('raw_autonomous',raw),('conditional_diagnostic',conditional_samples)]:
            sc=independent_score(a[:,:B],observed);rec=dict(subject=subject,split=info['split'],lab=info['lab'],model='rnnglm32',arm=arm,
                horizon=horizon,actual_horizon=B*500,full_horizon=H>=horizon,scope='post_source_validation_architecture_challenge',**sc)
            lo,hi=np.quantile(a[:,:B], [.1,.9],axis=0)
            high_valid=np.isfinite(observed[:,:2])
            rec['high_width80']=float(np.mean((hi-lo)[:,:2][high_valid]))
            found=next(r for r in lead if r['horizon']==horizon and r['arm']==arm)
            dif={k:float(abs(sc[k]-found[k]))for k in['crps','mae','high_accuracy_mae','energy']}
            if arm=='conditional_diagnostic':
                n=B*500;c=future['choice'][:n];q=np.clip(p[:n],1e-8,1-1e-8);ok=c!=0
                nll=-np.mean(np.where(c[ok]==-1,np.log(q[ok]),np.log1p(-q[ok])))
                sq=np.clip(static_p[:n],1e-8,1-1e-8);static_nll=-np.mean(np.where(c[ok]==-1,np.log(sq[ok]),np.log1p(-sq[ok])))
                rec.update(binary_nll=float(nll),static_prefix_binary_nll=float(static_nll),conditional_nll_gain_over_static=float(static_nll-nll))
                dif['binary_nll']=float(abs(nll-found['binary_nll']))
                conditional.append(rec)
            if max(dif.values())>1e-10:raise ValueError('Independent RNN score mismatch '+repr(dif))
            rows.append(rec);numerical.append(dict(arm=arm,horizon=horizon,**dif))
    record=dict(subject=subject,split=info['split'],lab=info['lab'],rows_read=len(data['choice']),original_provenance=original_meta['provenance'],
         targets_and_counts_equal=True,prefix_weight_endpoint_max_abs_difference=delta_w,prefix_hidden_endpoint_max_abs_difference=delta_h,
         conditional_probability_max_abs_difference=dp,conditional_weights_max_abs_difference=dw,conditional_hidden_final_max_abs_difference=dh,
         same_trial_perturbation_probability_difference=same_trial_difference,omission_weight_hidden_hold_difference=omission_hold,
         forecast_path=str(forecast_path.relative_to(C)),forecast_sha256=digest(forecast_path),
         conditional_path=str((folder/(subject+'__rnnglm32__conditional.npz')).relative_to(C)),
         conditional_sha256=digest(folder/(subject+'__rnnglm32__conditional.npz')),scores=rows,numerical_differences=numerical)
    write_json(OUT/'records'/(subject+'.json'),record)

def aggregate():
    order=json.loads((C/'artifacts/results/SUBJECT_ORDER.json').read_text());rows=[];checks=[]
    for p in sorted((OUT/'records').glob('*.json')):
        r=json.loads(p.read_text());rows.extend(r['scores']);checks.append(r)
    summaries=[]
    for horizon in[1000,3000,5000]:
        for full in[True,False]:
            for arm in['autonomous','raw_autonomous','conditional_diagnostic']:
                rr=[r for r in rows if r['horizon']==horizon and r['arm']==arm and(r['full_horizon']or not full)]
                if not rr:continue
                entry=dict(arm=arm,horizon=horizon,full_only=full,n=len(rr),crps=float(np.mean([r['crps']for r in rr])),
                    high_accuracy_mae=float(np.mean([r['high_accuracy_mae']for r in rr])),coverage80=float(np.mean([r['coverage']['0.8']for r in rr])),
                    high_coverage80=float(np.mean([r['high_coverage']['0.8']for r in rr])),width80=float(np.mean([r['width']['0.8']for r in rr])),
                    high_width80=float(np.mean([r['high_width80']for r in rr])))
                if arm=='conditional_diagnostic':entry.update(binary_nll=float(np.mean([r['binary_nll']for r in rr])),static_nll=float(np.mean([r['static_prefix_binary_nll']for r in rr])))
                summaries.append(entry)
    primary={r['subject']:r for r in rows if r['arm']=='autonomous'and r['horizon']==3000 and r['full_horizon']}
    baselines=json.loads((C/'artifacts/reconstruction/INDEPENDENT_SCORES.json').read_text());comparisons=[];labs=[]
    for model in['growth','persistence']:
        base={r['subject']:r for r in baselines if r['model']==model and r['arm']=='autonomous'and r['horizon']==3000 and r['full_horizon']}
        ids=[s for s in order if s in primary and s in base]
        if not ids:continue
        delta=np.array([base[s]['crps']-primary[s]['crps']for s in ids]);rng=np.random.default_rng(891)
        bs=delta[rng.integers(0,len(delta),(10000,len(delta)))].mean(axis=1)
        comparisons.append(dict(baseline=model,n=len(ids),animal_order=ids,mean_crps_gain=float(np.mean(delta)),
            lo95=float(np.quantile(bs,.025)),hi95=float(np.quantile(bs,.975)),family5x2_lower005=float(np.quantile(bs,.005)),
            relative_crps_gain=float(np.mean(delta)/np.mean([base[s]['crps']for s in ids])),
            relative_high_accuracy_mae_gain=float(1-np.mean([primary[s]['high_accuracy_mae']for s in ids])/np.mean([base[s]['high_accuracy_mae']for s in ids]))))
    for label in sorted(set(r['lab']for r in primary.values()))+['reserved_labs_combined','animal_holdout_combined']:
        rr=[r for r in primary.values()if r['lab']==label or(label=='reserved_labs_combined'and r['split']=='lab_holdout')or(label=='animal_holdout_combined'and r['split']=='animal_holdout')]
        if rr:labs.append(dict(group=label,n=len(rr),crps=float(np.mean([r['crps']for r in rr])),high_accuracy_mae=float(np.mean([r['high_accuracy_mae']for r in rr])),coverage80=float(np.mean([r['coverage']['0.8']for r in rr]))))
    write_json(OUT/'INDEPENDENT_SCORES.json',rows);write_json(OUT/'INDEPENDENT_SUMMARY.json',summaries);write_json(OUT/'PAIRED_COMPARISONS.json',comparisons);write_json(OUT/'LAB_STRATA.json',labs)
    # Preserve the finite-Monte-Carlo ordering witness and verify the root's
    # canonical result without importing its bootstrap implementation.
    rootpath=C/'artifacts/rnn/results/PAIRED_COMPARISONS.json'
    roots=json.loads(rootpath.read_text())if rootpath.exists()else[]
    ordering=[];root_differences=[]
    for comp in comparisons:
        baseline=comp['baseline'];base={r['subject']:r for r in baselines if r['model']==baseline and r['arm']=='autonomous'and r['horizon']==3000 and r['full_horizon']}
        for label,ids in[('canonical_source_then_lab',comp['animal_order']),('global_alphabetical',sorted(comp['animal_order']))]:
            delta=np.array([base[s]['crps']-primary[s]['crps']for s in ids]);rng=np.random.default_rng(891)
            bs=delta[rng.integers(0,len(delta),(10000,len(delta)))].mean(axis=1)
            ordering.append(dict(baseline=baseline,order_label=label,animal_order=ids,mean=float(np.mean(delta)),
                  lo95=float(np.quantile(bs,.025)),hi95=float(np.quantile(bs,.975)),gate_lower005=float(np.quantile(bs,.005))))
        root=next((x for x in roots if x['group']=='all'and x['baseline']==baseline),None)
        if root:
            q=root['crps_gain'];root_differences.append(dict(baseline=baseline,
                 max_abs_difference=max(abs(comp['mean_crps_gain']-q['mean']),abs(comp['lo95']-q['lo']),abs(comp['hi95']-q['hi']),abs(comp['family5x2_lower005']-q['gate_lower']))))
    write_json(OUT/'BOOTSTRAP_ORDER_AUDIT.json',dict(canonical_order_source='artifacts/results/SUBJECT_ORDER.json',seed=891,resamples=10000,
         ordering_witness=ordering,root_canonical_comparison=root_differences,
         explanation='Finite bootstrap quantiles depend on ID order with a fixed RNG sequence; point estimates and target distribution do not. Canonical root and independent order now match.'))
    baseline_width=[]
    for s in order:
        if s not in primary:continue
        folder=C/'artifacts/forecasts'/('source_animals'if primary[s]['split']=='animal_holdout'else'source_labs')
        path=folder/(s+'__growth.npz')
        with np.load(path,allow_pickle=False)as z:a=z['samples_primary'][:,:6,:2]
        with np.load(folder/(s+'__observed.npz'),allow_pickle=False)as z:y=z['observed'][:6,:2]
        low,high=np.quantile(a,[.1,.9],axis=0)
        baseline_width.append(dict(subject=s,high_width80=float(np.mean((high-low)[np.isfinite(y)])),forecast_sha256=digest(path)))
    write_json(OUT/'GROWTH_WIDTH_AUDIT.json',dict(n=len(baseline_width),metric='mean80%intervalwidth for twohigh-contrastaccuracymarginals;equalanimalweight',
         high_width80=float(np.mean([r['high_width80']for r in baseline_width]))if baseline_width else None,animals=baseline_width))
    stats=['prefix_weight_endpoint_max_abs_difference','prefix_hidden_endpoint_max_abs_difference','conditional_probability_max_abs_difference','conditional_weights_max_abs_difference','conditional_hidden_final_max_abs_difference','same_trial_perturbation_probability_difference','omission_weight_hidden_hold_difference']
    diffs=[d for r in checks for d in r['numerical_differences']]
    write_json(OUT/'NUMERICAL_DIFFERENCES.json',dict(reconstructed_animals=len(checks),score_rows=len(rows),max_recurrence_differences={k:max([r[k]for r in checks],default=0.)for k in stats},
        max_score_difference=max([max(d[k]for k in['crps','mae','high_accuracy_mae','energy'])for d in diffs],default=0.),
        max_conditional_nll_difference=max([d.get('binary_nll',0.)for d in diffs],default=0.),external_outcomes_read=False,
        scope='Post-source-validation architecture challenge;notuntouchedconfirmatorysourcecomparison'))
    return checks,summaries

def main():
    p=argparse.ArgumentParser();p.add_argument('--collect-only',action='store_true');p.add_argument('--overwrite',action='store_true');a=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'records').mkdir(exist_ok=True);verify()
    if not a.collect_only:
        for info in source_allocation():
            subject=info['subject'];saved=OUT/'records'/(subject+'.json')
            if saved.exists()and not a.overwrite:continue
            if not completed(subject,info['split']):continue
            t0=time.monotonic();reconstruct(subject,info);print(json.dumps(dict(subject=subject,seconds=time.monotonic()-t0)),flush=True)
    checks,summary=aggregate();print(json.dumps(dict(reconstructed=len(checks),full_primary=next((r['n']for r in summary if r['arm']=='autonomous'and r['horizon']==3000 and r['full_only']),0))),flush=True)

if __name__=='__main__':main()
