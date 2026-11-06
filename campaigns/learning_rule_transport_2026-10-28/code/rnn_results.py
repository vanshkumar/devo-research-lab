#!/usr/bin/env python3
"""Frozen postvalidation RNN challenge: no refitting or criterion relaxation."""
import hashlib,json
from pathlib import Path
import numpy as np
from data_io import exposure
from source_results import write_csv

C=Path(__file__).resolve().parents[1];O=C/'artifacts/rnn/results';O.mkdir(exist_ok=True,parents=True)


def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')


def main():
    ids=json.loads((C/'artifacts/results/SUBJECT_ORDER.json').read_text())
    alloc={r['subject']:r for r in json.loads((C/'protocols/SPLIT.json').read_text())['standard']}
    rows=[];original=[]
    for tag in ['rnn_source_animals','rnn_source_labs']:
        rows+=json.loads((C/'artifacts/forecasts'/tag/'scores.json').read_text())
    for tag in ['source_animals','source_labs']:
        original+=json.loads((C/'artifacts/forecasts'/tag/'scores.json').read_text())
    rlook={(r['subject'],r['arm'],r['horizon']):r for r in rows};blook={(r['subject'],r['model'],r['arm'],r['horizon']):r for r in original}
    if any((s,'autonomous',3000)not in rlook for s in ids):raise RuntimeError('Wait for every frozen primary RNN animal')
    groups={'all':ids,'animal_holdout':[s for s in ids if alloc[s]['split']=='animal_holdout'],'lab_holdout':[s for s in ids if alloc[s]['split']=='lab_holdout']}
    for lab in sorted({alloc[s]['lab']for s in ids}):groups[lab]=[s for s in ids if alloc[s]['lab']==lab]
    rng=np.random.default_rng(891);draw=rng.integers(40,size=(10000,40))
    def pair(a):
        a=np.asarray(a,float)
        ii=draw if len(a)==40 else np.random.default_rng(891).integers(len(a),size=(10000,len(a)))
        boot=a[ii].mean(axis=1)
        return dict(n=len(a),mean=float(a.mean()),lo=float(np.quantile(boot,.025)),hi=float(np.quantile(boot,.975)),gate_lower=float(np.quantile(boot,.005)),gate_percentile=.005)
    sums=[];comparisons=[]
    for group,ss in groups.items():
      for arm in ['autonomous','raw_autonomous','conditional_diagnostic']:
        rr=[rlook[(s,arm,3000)]for s in ss if(s,arm,3000)in rlook]
        if not rr:continue
        x=dict(group=group,model='rnnglm32',arm=arm,n=len(rr))
        for key in ['crps','high_accuracy_mae','mae','energy','binary_nll']:
            if key in rr[0]:x[key]=float(np.mean([r[key]for r in rr]))
        x['coverage80']=float(np.mean([r['coverage']['0.8']for r in rr]));x['width80']=float(np.mean([r['width']['0.8']for r in rr]))
        x['mae_by_metric']=np.mean([r['mae_by_metric']for r in rr],axis=0).tolist()
        if arm=='autonomous':
            cov=[];wid=[]
            for s in ss:
                tag='rnn_source_animals'if alloc[s]['split']=='animal_holdout'else'rnn_source_labs'
                f=C/'artifacts/forecasts'/tag
                a=np.load(f/(s+'__rnnglm32.npz'))['samples_primary'][:,:6,:2];y=np.load(f/(s+'__observed.npz'))['observed'][:6,:2]
                lo,hi=np.quantile(a,[.1,.9],axis=0);valid=np.isfinite(y)
                cov.append(np.mean(((y>=lo)&(y<=hi))[valid]));wid.append(np.mean((hi-lo)[valid]))
            x['high_coverage80']=float(np.mean(cov));x['high_width80']=float(np.mean(wid))
        sums.append(x)
      for baseline in ['growth','persistence']:
        gain=[blook[(s,baseline,'autonomous',3000)]['crps']-rlook[(s,'autonomous',3000)]['crps']for s in ss]
        hg=[blook[(s,baseline,'autonomous',3000)]['high_accuracy_mae']-rlook[(s,'autonomous',3000)]['high_accuracy_mae']for s in ss]
        bc=np.mean([blook[(s,baseline,'autonomous',3000)]['crps']for s in ss]);bh=np.mean([blook[(s,baseline,'autonomous',3000)]['high_accuracy_mae']for s in ss])
        comparisons.append(dict(group=group,baseline=baseline,crps_gain=pair(gain),crps_relative_gain=float(np.mean(gain)/bc),high_mae_gain=pair(hg),high_mae_relative_gain=float(np.mean(hg)/bh)))
    sm={(r['group'],r['arm']):r for r in sums};r=sm[('all','autonomous')];reasons=[]
    for b in ['growth','persistence']:
        a=next(x for x in comparisons if x['group']=='all'and x['baseline']==b)
        if a['crps_gain']['mean']<.002:reasons.append('absoluteCRPSgain<.002 vs'+b)
        if a['crps_relative_gain']<.10:reasons.append('relativeCRPSgain<10% vs'+b)
        if a['crps_gain']['gate_lower']<=0:reasons.append('expandedfamily-scorelower<=0 vs'+b)
        if a['high_mae_relative_gain']<.10:reasons.append('highMAEimprovement<10% vs'+b)
        lab=next(x for x in comparisons if x['group']=='lab_holdout'and x['baseline']==b)
        if lab['crps_relative_gain']<.05:reasons.append('heldlabCRPSgain<5% vs'+b)
        if lab['high_mae_gain']['mean']<0:reasons.append('heldlabhighMAEworsens vs'+b)
        for lname in ['hoferlab','wittenlab']:
            ll=next(x for x in comparisons if x['group']==lname and x['baseline']==b)
            if ll['crps_gain']['mean']<=0:reasons.append(lname+'scoregain<=0 vs'+b)
    if r['high_accuracy_mae']>.15:reasons.append('highMAE>15pp')
    if not .70<=r['coverage80']<=.95:reasons.append('overallcoverage80outside70–95%')
    if not .70<=r['high_coverage80']<=.95:reasons.append('highcoverage80outside70–95%')
    decision=dict(challenge='post-original-source-validation RNN expansion',untouched_source_confirmation=False,
                  rnn_freeze_sha256=hashlib.sha256((C/'protocols/RNN_FREEZE.json').read_bytes()).hexdigest(),
                  source_gate_earned=not reasons,reasons=reasons,multiplicity='fivecandidates*two baselines;one-sided.005bootstraplower',
                  external_status='sealed unlessthisearnedgateauthorizesafrozenindependenttest')
    dump(O/'SUMMARY.json',sums);dump(O/'PAIRED_COMPARISONS.json',comparisons);dump(O/'SOURCE_GATE.json',decision)
    write_csv(C/'tables/rnn_challenge_scores.csv',sums);write_csv(C/'tables/rnn_challenge_individual.csv',rows)
    if not reasons:
        dump(C/'protocols/EXTERNAL_ACCESS_EARNED.json',dict(**decision,selected_rule='rnnglm32',calibration='same1000prefix and sourceRNNobservation/uncertainty frozen'))
    exposure(dict(event='postvalidation_RNN_source_gate_scored',source_gate_earned=not reasons,external_outcomes_read=False))
    print(json.dumps(dict(primary=[x for x in sums if x['group']=='all'],comparisons=[x for x in comparisons if x['group']in('all','lab_holdout','hoferlab','wittenlab')],gate=decision),indent=2))

if __name__=='__main__':main()
