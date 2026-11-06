"""Static scientific figure from saved outputs; no fitting or data selection."""
import pathlib,json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=pathlib.Path(__file__).parent
s=json.loads((H/'summary.json').read_text());r=pd.read_csv(H/'rates.csv');b=s['bootstrap'];p=pd.read_csv(H/'weight_profile.csv')
fig,ax=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
x=np.arange(3)
for j,(incl,label,color) in enumerate([('eligible','Both males courted, then mating','#176789'),('all_matings','All matings (different estimand)','#c8782e')]):
 q=r[(r.inclusion==incl)&(r.score=='copy_first')&(r.stratum=='all')].set_index('treatment').loc[['T','C1','C2']]
 ax[0].plot(x+(j-.5)*.16,q.estimate*100,'o',color=color,label=label,markersize=7)
 for xx,(t,row) in zip(x+(j-.5)*.16,q.iterrows()):ax[0].annotate(f'{int(row.k)}/{int(row.n)}',(xx,row.estimate*100),xytext=(0,8 if j==0 else -16),textcoords='offset points',ha='center',fontsize=9,color=color)
# Only eligible CIs: preserve full date-cluster structure; no frame/row-based interval.
means=[.625,46/74,42/67];cis=np.array([b[k]['ci95'] for k in ['main_first','C1_single','C2_single']])*100
ax[0].errorbar(x-.08,np.array(means)*100,yerr=[np.array(means)*100-cis[:,0],cis[:,1]-np.array(means)*100],fmt='none',color='#176789',capsize=4)
ax[0].axhline(50,color='.5',ls='--',lw=1);ax[0].set_xticks(x,['Conflicting pair','Early only','Late only']);ax[0].set_ylim(35,85);ax[0].set_ylabel('First / unique demonstration copied (%)');ax[0].set_title('A  Observed preference and inclusion rule',loc='left',fontsize=12);ax[0].legend(loc='upper left',fontsize=8,frameon=False)
ax[0].set_xlim(-.35,2.35)
ax[1].plot(p.relative_second_weight,2*(p.log_likelihood.max()-p.log_likelihood),color='#176789',lw=2)
for rr,label in [(0,'First gate'),(1,'Equal evidence'),(2,'Recency')]:
 ax[1].axvline(rr,color='.75',lw=1);ax[1].text(rr,11.6,label,ha='center',fontsize=9)
ax[1].set_ylim(-.2,13);ax[1].set_xlim(-.1,2.1);ax[1].set_xlabel('Relative weight of contradictory second demonstration');ax[1].set_ylabel('2 × log-likelihood loss from best fit');ax[1].set_title('B  Conditional behavioral model comparison',loc='left',fontsize=12)
fig.suptitle('Social information updating: a suggestive behavioral constraint',fontsize=14)
fig.savefig(H/'social_learning.png',dpi=180);fig.savefig(H/'social_learning.svg')
