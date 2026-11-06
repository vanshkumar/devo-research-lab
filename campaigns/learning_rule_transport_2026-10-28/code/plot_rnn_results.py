#!/usr/bin/env python3
"""The stronger architecture challenge, explicitly separated from stage one."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

C=Path(__file__).resolve().parents[1];F=C/'figures';F.mkdir(exist_ok=True,parents=True)


def main():
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'legend.fontsize':9})
    ids=json.loads((C/'artifacts/results/SUBJECT_ORDER.json').read_text());alloc={r['subject']:r for r in json.loads((C/'protocols/SPLIT.json').read_text())['standard']}
    sm=json.loads((C/'artifacts/rnn/results/SUMMARY.json').read_text());s=next(r for r in sm if r['group']=='all'and r['arm']=='autonomous');con=next(r for r in sm if r['group']=='all'and r['arm']=='conditional_diagnostic')
    original=json.loads((C/'artifacts/results/PRIMARY_SUMMARY.json').read_text());g=next(r for r in original if r['group']=='all'and r['model']=='growth'and r['arm']=='autonomous')
    comps=json.loads((C/'artifacts/rnn/results/PAIRED_COMPARISONS.json').read_text());overall=next(r for r in comps if r['group']=='all'and r['baseline']=='growth')
    obs=[];rnn=[];grow=[];rows=[]
    for tag in ['rnn_source_animals','rnn_source_labs']:rows+=json.loads((C/'artifacts/forecasts'/tag/'scores.json').read_text())
    rr={(r['subject'],r['arm'],r['horizon']):r for r in rows}
    for sub in ids:
        held=alloc[sub]['split']=='animal_holdout';base=C/'artifacts/forecasts'/('source_animals'if held else'source_labs');new=C/'artifacts/forecasts'/('rnn_source_animals'if held else'rnn_source_labs')
        obs.append(np.load(base/(sub+'__observed.npz'))['observed'][:6,:2].mean(axis=1))
        grow.append(np.load(base/(sub+'__growth.npz'))['samples_primary'][:,:6,:2].mean(axis=(0,2)))
        rnn.append(np.load(new/(sub+'__rnnglm32.npz'))['samples_primary'][:,:6,:2].mean(axis=(0,2)))
    obs=np.array(obs);rnn=np.array(rnn);grow=np.array(grow)
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    a=axes[0,0]
    values=[con['high_accuracy_mae']*100,s['high_accuracy_mae']*100,g['high_accuracy_mae']*100]
    a.barh([2,1,0],values,color=['#91b4c9','#166c91','#bb7528'],height=.55)
    for y,v in zip([2,1,0],values):a.text(v+.3,y,f'{v:.2f} pp',va='center',fontsize=10)
    a.set(yticks=[2,1,0],yticklabels=['RNN: actual histories\n(conditional diagnostic)','RNN: self-generated\nhistories and trainer','Exposure / growth\nautonomous baseline'],xlabel='High-contrast accuracy error (percentage points)',xlim=(0,22),title='A   Individual forecasts remain much less precise')
    a=axes[0,1];r=overall['crps_gain']
    a.errorbar(r['mean'],0,xerr=[[r['mean']-r['lo']],[r['hi']-r['mean']]],fmt='o',color='#166c91',lw=2,capsize=5)
    a.axvline(0,color='#666',lw=1);a.axvline(.1*g['crps'],color='#a03333',ls=':',lw=1.5)
    a.set(ylim=(-.7,.7),yticks=[0],yticklabels=['RNN32'],xlabel='CRPS gain over growth (positive is better)',title='B   A better point estimate, not an earned source gate')
    a.text(.03,.93,f"Gain {100*overall['crps_relative_gain']:.2f}%\n95% animal interval [{r['lo']:.4f}, {r['hi']:.4f}]",transform=a.transAxes,va='top',fontsize=10)
    a.text(.03,.05,'Dotted line: predeclared 10% score-gain boundary\nThe interval still allows a useful advantage.',transform=a.transAxes,fontsize=9,color='#555')
    a=axes[1,0];xx=np.arange(1250,4000,500);rng=np.random.default_rng(591);boot=obs[rng.integers(len(obs),size=(10000,len(obs)))].mean(axis=1);lo,hi=np.quantile(boot,[.025,.975],axis=0)
    a.fill_between(xx,lo*100,hi*100,color='black',alpha=.12);a.plot(xx,obs.mean(0)*100,'o-',color='black',label='Observed, 40 animals')
    a.plot(xx,rnn.mean(0)*100,color='#166c91',lw=2,label='Frozen RNN32');a.plot(xx,grow.mean(0)*100,color='#bb7528',lw=2,label='Growth')
    a.set(ylim=(45,78),xlabel='Indexed task trial',ylabel='Mean high-contrast correct (%)',title='C   Average acquisition is reproduced');a.legend(frameon=False)
    a=axes[1,1]
    for j,(name,label)in enumerate([('hoferlab','Hofer (9 animals)'),('wittenlab','Witten (10 animals)')]):
        q=next(r for r in comps if r['group']==name and r['baseline']=='growth')['crps_gain']
        a.errorbar(q['mean'],j,xerr=[[q['mean']-q['lo']],[q['hi']-q['mean']]],fmt='o',color='#166c91',capsize=4)
    a.axvline(0,color='#666',lw=1);a.set(yticks=[0,1],yticklabels=['Hofer (9)','Witten (10)'],xlabel='Paired CRPS gain over growth',title='D   Benefit is uneven across the two reserved labs')
    a.set_ylim(-.4,1.7)
    a.text(.02,.96,'Two environments; animal intervals do not\nrepresent arbitrary-new-lab uncertainty.',transform=a.transAxes,va='top',fontsize=9,color='#555')
    fig.suptitle('Stronger published recurrent architecture: promising mean forecast, limited individual utility\nPostvalidation challenge fitted on development animals only; real external cohort remains sealed',fontsize=13)
    for ext in ['png','pdf']:fig.savefig(F/('RNN_CHALLENGE_RESULT.'+ext),dpi=180,bbox_inches='tight')
    plt.close(fig)
    out=dict(observed_mean=obs.mean(0).tolist(),rnn_mean=rnn.mean(0).tolist(),growth_mean=grow.mean(0).tolist(),
             note='Equal-animal mean of two high-contrast side rates per future500-trialbin. Cohortmeancomparison is descriptive, not a new gate.')
    (C/'artifacts/rnn/results/MEAN_CURVES.json').write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__':main()
