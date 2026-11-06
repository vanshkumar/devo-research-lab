#!/usr/bin/env python3
"""Scientific figures from frozen forecasts; no model fitting or external data."""
import hashlib,json,os
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from evaluation import paired_interval

C=Path(__file__).resolve().parents[1];F=C/'figures';F.mkdir(exist_ok=True,parents=True)
COLORS={'dnnglm32':'#3856a6','dnnglm':'#7589bd','reinforce':'#257b62','reinforce_pure':'#88b6a5','growth':'#bd7628','persistence':'#8c8c8c'}
LABELS={'dnnglm32':'DNN32','dnnglm':'DNN16','reinforce':'RL + baseline','reinforce_pure':'Reward-only RL','growth':'Exposure / growth','persistence':'Skill persistence'}


def save(fig,name):
    fig.savefig(F/(name+'.png'),dpi=180,bbox_inches='tight');fig.savefig(F/(name+'.pdf'),bbox_inches='tight');plt.close(fig)


def main():
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titlesize':12,'axes.labelsize':10,'legend.fontsize':9,'savefig.facecolor':'white'})
    alloc={r['subject']:r for r in json.loads((C/'protocols/SPLIT.json').read_text())['standard']}
    ids=json.loads((C/'artifacts/results/SUBJECT_ORDER.json').read_text());rows=[]
    for tag in ['source_animals','source_labs']:rows+=json.loads((C/'artifacts/forecasts'/tag/'scores.json').read_text())
    look={(r['subject'],r['model'],r['arm'],r['horizon']):r for r in rows}
    sums=json.loads((C/'artifacts/results/PRIMARY_SUMMARY.json').read_text());ss={(r['model'],r['arm']):r for r in sums if r['group']=='all'}
    def folder(s):return C/'artifacts/forecasts'/('source_animals'if alloc[s]['split']=='animal_holdout'else'source_labs')
    def data(s,m):return np.load(folder(s)/(s+'__'+m+'.npz'))
    observed=np.array([np.load(folder(s)/(s+'__observed.npz'))['observed'][:6]for s in ids])
    rng=np.random.default_rng(591)
    def ci(v):
        v=np.asarray(v);a=v[rng.integers(len(v),size=(10000,len(v)))].mean(axis=1);return np.quantile(a,[.025,.975])
    fig,ax=plt.subplots(2,2,figsize=(12.5,8.2),layout='constrained')
    rules=['reinforce_pure','reinforce','dnnglm','dnnglm32'];yy=np.arange(len(rules));height=.34
    for offset,arm,label,alpha in [(-height/2,'conditional_diagnostic','Conditional',.48),(height/2,'autonomous','Autonomous',1)]:
        means=[];lower=[];upper=[]
        for m in rules:
            v=np.array([look[(s,m,arm,3000)]['high_accuracy_mae']for s in ids])*100;bounds=ci(v)
            means.append(v.mean());lower.append(v.mean()-bounds[0]);upper.append(bounds[1]-v.mean())
        ax[0,0].barh(yy+offset,means,height=height,color=[COLORS[m]for m in rules],alpha=alpha,label=label)
        ax[0,0].errorbar(means,yy+offset,xerr=[lower,upper],fmt='none',color='#303030',lw=.8,capsize=2)
    ax[0,0].set(yticks=yy,yticklabels=[LABELS[m]for m in rules],xlabel='High-contrast accuracy error (percentage points)',title='A   Accurate tracking does not ensure individual forecasts')
    ax[0,0].legend(loc='upper right',frameon=False,fontsize=8);ax[0,0].set_xlim(0,27)
    ax[0,0].text(.01,-.24,'Conditional curves are diagnostics; their actual input histories differ.',transform=ax[0,0].transAxes,fontsize=8,color='#555')
    comps=json.loads((C/'artifacts/results/PAIRED_COMPARISONS.json').read_text())
    for j,m in enumerate(rules):
        r=next(r for r in comps if r['group']=='all'and r['model']==m and r['baseline']=='growth')['crps_gain']
        ax[0,1].errorbar(r['mean'],j,xerr=[[r['mean']-r['lo']],[r['hi']-r['mean']]],fmt='o',color=COLORS[m],capsize=3)
    base=ss[('growth','autonomous')]['crps'];ax[0,1].axvline(0,color='#666',lw=1);ax[0,1].axvline(.1*base,color='#9b3333',ls=':',lw=1.2)
    ax[0,1].set(yticks=yy,yticklabels=[LABELS[m]for m in rules],xlabel='Paired CRPS gain over growth (positive is better)',title='B   No rule earns the frozen material-improvement gate')
    ax[0,1].text(.99,.04,'Dotted line: 10% growth-score gain\nIntervals: 95% animal bootstrap',transform=ax[0,1].transAxes,ha='right',va='bottom',fontsize=8,color='#555')
    x=np.arange(1250,4000,500)
    v=observed[:,:,:2].mean(axis=2);bs=v[rng.integers(len(v),size=(5000,len(v)))].mean(axis=1)
    lo,hi=np.quantile(bs,[.025,.975],axis=0)
    ax[1,0].fill_between(x,lo*100,hi*100,color='black',alpha=.12);ax[1,0].plot(x,v.mean(axis=0)*100,'o-',color='black',label='Observed, 40 animals',lw=2)
    for m in ['dnnglm32','reinforce','growth']:
        a=np.array([data(s,m)['samples_primary'][:,:6,:2].mean(axis=(0,2))for s in ids])
        ax[1,0].plot(x,a.mean(axis=0)*100,'-',color=COLORS[m],label=LABELS[m],lw=2)
    ax[1,0].set(xlabel='Indexed task trial (after 1,000-trial calibration)',ylabel='Mean high-contrast correct (%)',ylim=(40,83),title='C   The models do generate average acquisition')
    ax[1,0].legend(frameon=False,ncol=2,fontsize=8)
    for m in ['persistence','growth','reinforce_pure','reinforce','dnnglm','dnnglm32']:
        r=ss[(m,'autonomous')];xx=r['high_width80']*100;yy2=r['high_coverage80']*100
        ax[1,1].scatter(xx,yy2,color=COLORS[m],s=45)
        offsets={'dnnglm32':(2,-6),'growth':(1,4),'dnnglm':(2,-4),'reinforce':(-15,4),'reinforce_pure':(1,-4),'persistence':(1,2)}
        dx,dy=offsets[m];ax[1,1].annotate(LABELS[m],(xx,yy2),xytext=(xx+dx,yy2+dy),fontsize=8,color=COLORS[m])
    ax[1,1].axhline(80,color='#555',ls='--',lw=1)
    ax[1,1].set(xlabel='Mean 80% high-contrast interval width (pp)',ylabel='High-contrast coverage (%)',xlim=(38,80),ylim=(52,96),title='D   Marginal coverage is bought with broad intervals')
    fig.suptitle('Frozen IBL source test: population acquisition, limited individual forecast value\n1,000 calibration trials → 3,000 future opportunities; 40 reserved animals, including 19 from two new labs',fontsize=13)
    save(fig,'SOURCE_FORECAST_RESULT')
    # Representative animals selected solely by subject hash, before viewing
    # their forecast errors. Same selection as the declared MC challenge.
    chosen=sorted(ids,key=lambda s:hashlib.sha256(s.encode()).hexdigest())[:6]
    fig,axes=plt.subplots(6,2,figsize=(12,15),layout='constrained',sharex=True,sharey=True)
    for i,s in enumerate(chosen):
        y=np.load(folder(s)/(s+'__observed.npz'))['observed'][:6]
        z=data(s,'dnnglm32')['samples_primary'][:,:6];g=data(s,'growth')['samples_primary'][:,:6]
        con=np.load(folder(s)/(s+'__dnnglm32__conditional.npz'))['samples'][:,:6]
        for side in [0,1]:
            a=axes[i,side];lo,hi=np.quantile(z[:,:,side],[.1,.9],axis=0)
            a.fill_between(x,lo*100,hi*100,color=COLORS['dnnglm32'],alpha=.18)
            a.plot(x,z[:,:,side].mean(axis=0)*100,color=COLORS['dnnglm32'],label='Autonomous DNN32',lw=2)
            a.plot(x,g[:,:,side].mean(axis=0)*100,color=COLORS['growth'],label='Growth',lw=1.5)
            a.plot(x,con[:,:,side].mean(axis=0)*100,color='#367b49',ls='--',label='Conditional diagnostic',lw=1.4)
            a.plot(x,y[:,side]*100,'o-',color='black',label='Observed',ms=3,lw=1)
            a.set_ylim(0,100);a.set_title(s+' · '+alloc[s]['lab']+' · '+('left' if side==0 else 'right'),fontsize=10)
            if side==0:a.set_ylabel('High-contrast correct (%)')
            if i==5:a.set_xlabel('Indexed task trial')
    axes[0,0].legend(frameon=False,fontsize=8,ncol=2)
    fig.suptitle('Individual forecasts: six animals selected by hash\nBlue bands: 80% marginal forecasts; green uses actual intervening histories and stimuli',fontsize=12)
    save(fig,'INDIVIDUAL_SOURCE_TRAJECTORIES')
    # Every full primary animal, without a selected error subset.
    fig,axes=plt.subplots(10,4,figsize=(16,25),layout='constrained',sharex=True,sharey=True)
    for a,s in zip(axes.flat,ids):
        y=np.load(folder(s)/(s+'__observed.npz'))['observed'][:6,:2].mean(axis=1)
        for m in ['dnnglm32','growth']:
            z=data(s,m)['samples_primary'][:,:6,:2].mean(axis=2);lo,hi=np.quantile(z,[.1,.9],axis=0)
            if m=='dnnglm32':a.fill_between(x,lo*100,hi*100,color=COLORS[m],alpha=.15)
            a.plot(x,z.mean(axis=0)*100,color=COLORS[m],lw=1.3)
        a.plot(x,y*100,'o-',color='black',lw=1,ms=2);a.set(title=s,ylim=(0,100))
    fig.suptitle('All 40 full-horizon animals · autonomous DNN32 (blue), growth (orange), observed (black)\nCurves average the two side-specific high-contrast rates; this display is not a separate primary score',fontsize=13)
    save(fig,'ALL_PRIMARY_SOURCE_ANIMALS')
    print('Saved scientific source figures; external outcomes not read.')

if __name__=='__main__':main()
