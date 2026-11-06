"""Coverage, remaining performance differences, curves and standalone figures."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/human_learning_matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from analysis import *

def main():
    out=ROOT/'outputs/diagnostics';out.mkdir(exist_ok=True)
    d=pd.read_csv(ROOT/'outputs/primary/trial_predictions.csv',dtype={'subject':str})
    d['correct']=d.feedbackType.eq(1);d['old_choice']=(1+d.choice*d.old_majority)/2
    rows=[]
    for phase,mask in [('calibration',d.trial.lt(200)),('later',d.trial.ge(200)),('primary',d.primary)]:
        s=d.loc[mask]
        p=s.groupby(['subject','instructions','schedule','partition']).agg(n=('trial','size'),n_responded=('responded','sum'),response_rate=('responded','mean'),rt=('response_times_from_stim','median'),movement=('firstMovement_times_from_stim','median')).reset_index()
        acc=s.loc[s.responded].groupby('subject').correct.mean();high=s.loc[s.responded&s.stimContrast.eq(1)].groupby('subject').correct.mean()
        p['accuracy']=p.subject.map(acc);p['high_contrast_accuracy']=p.subject.map(high);p['phase']=phase;rows.append(p)
    p=pd.concat(rows,ignore_index=True);p.to_csv(out/'participant_coverage_performance.csv',index=False)
    p.groupby(['phase','instructions']).agg(n_people=('subject','size'),n_trials=('n','sum'),n_responded=('n_responded','sum'),response_rate=('response_rate','mean'),accuracy=('accuracy','mean'),high_contrast_accuracy=('high_contrast_accuracy','mean'),median_subject_rt=('rt','median')).to_csv(out/'condition_coverage_performance.csv')
    # Response-omission worst-case bounds for the raw old-choice curve.
    bounds=[]
    for lo,hi in [(0,5),(5,10),(10,20),(20,30)]:
        a=d.loc[d.switch_offset.ge(lo)&d.switch_offset.lt(hi)&d.stimContrast.le(.1)].copy()
        a['lower']=np.where(a.responded,a.old_choice,0);a['upper']=np.where(a.responded,a.old_choice,1)
        b=a.groupby(['subject','instructions']).agg(lower=('lower','mean'),upper=('upper','mean'),omissions=('responded',lambda s:int((~s).sum()))).reset_index()
        for g,c in b.groupby('instructions'):bounds.append(dict(start=lo,stop=hi,condition=g,lower=float(c.lower.mean()),upper=float(c.upper.mean()),omissions=int(c.omissions.sum())))
    pd.DataFrame(bounds).to_csv(out/'omission_worst_case_curve.csv',index=False)
    # Preswitch reference, separate event-based extraction to avoid redefining primary windows.
    pre=[]
    for subject,s in d.groupby('subject'):
        prob=s.probabilityLeft.to_numpy();sw=np.where((prob[1:]!=prob[:-1])&(prob[1:]!=.5)&(prob[:-1]!=.5))[0]+1
        for t in sw:
            if t<200:continue
            old=1 if prob[t-1]>.5 else -1
            for _,row in s.iloc[max(0,t-10):t].iterrows():
                if row.responded and row.stimContrast<=.1:pre.append(dict(subject=subject,condition=int(row.instructions),old_choice=(1+old*row.choice)/2,contrast=row.stimContrast))
    pre=pd.DataFrame(pre);pre.to_csv(out/'preswitch_reference_rows.csv',index=False)
    # Compact publication-style figure: heldout score, observed curves, standardization.
    scores=pd.read_csv(ROOT/'outputs/primary/participant_scores.csv',dtype={'subject':str})
    curves=pd.read_csv(ROOT/'outputs/primary/observable_curves.csv')
    old=pd.read_csv(ROOT/'outputs/primary/shared_old_context_component.csv')
    fig,axes=plt.subplots(1,3,figsize=(13,4),constrained_layout=True)
    colors={0:'#be5c35',1:'#286b9b'}
    sch=scores.groupby(['schedule','partition']).delta_log.agg(['mean','count']).reset_index()
    axes[0].axvline(0,color='0.5',lw=1)
    for i,row in sch.iterrows():axes[0].scatter(row['mean'],i,c='#286b9b' if row.partition=='validation_unseen_schedule' else '#999999',s=60)
    axes[0].set_yticks(range(len(sch)),sch.schedule);axes[0].set_xlabel('Condition − shared log score\n(nats per choice; participant means)');axes[0].set_title('Reserved prediction by schedule')
    axes[0].set_xticks([-.01,-.005,0,.005])
    for g in [0,1]:
        c=curves[(curves.condition==g)&(curves.contrast=='zero')];x=(c.start+c.stop-1)/2
        axes[1].errorbar(x,c['mean'],yerr=np.array([c['mean']-c.low,c.high-c['mean']]),marker='o',color=colors[g],label='Taught' if g else 'Discovery',capsize=3)
        v=old[old.condition==g];axes[2].plot((v.start+v.stop-1)/2,100*v.component,marker='o',color=colors[g])
    axes[1].axhline(.5,color='0.6',ls='--');axes[1].set_ylim(0,1);axes[1].set_xlabel('Trials since hidden switch');axes[1].set_ylabel('P(choose previous majority)');axes[1].set_title('Observed zero-contrast choices');axes[1].legend(frameon=False)
    axes[2].axhline(0,color='0.6',ls='--');axes[2].set_xlabel('Trials since hidden switch');axes[2].set_ylabel('Old evidence contribution (pp)');axes[2].set_title('Shared-model feedback component')
    for ax in axes:ax.spines[['top','right']].set_visible(False)
    fig.savefig(out/'primary_results.png',dpi=200);fig.savefig(out/'primary_results.pdf');plt.close(fig)

if __name__=='__main__':main()
