from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent;j=json.loads((p/'summary.json').read_text());m=j['summary']
colors={'no_oracle':'#6b7280','oracle':'#c47c22','learned':'#176c9d'}
labels={'no_oracle':'Original (matched parameters)','oracle':'Oracle exclusion','learned':'Learned reliability + story filtering'}
fig,ax=plt.subplots(1,3,figsize=(14,4.2),gridspec_kw={'width_ratios':[1.3,1.1,1]})
currs=['blocked','interleaved','early','middle','late'];x=np.arange(5)
for role in colors:
 rr=[next(r for r in m if r['family']=='original' and r['curriculum']==c)['roles'][role] for c in currs]
 y=np.array([r['test_signal_probability'] for r in rr]);ci=np.array([r['test_signal_probability_ci'] for r in rr])
 ax[0].errorbar(x,y*100,yerr=np.maximum(0,np.stack((y-ci[:,0],ci[:,1]-y)))*100,color=colors[role],marker='o',capsize=3,label=labels[role],lw=1.5,ms=4)
ax[0].set_xticks(x,['Blocked','Interleaved','Early','Middle','Late'],rotation=25,ha='right');ax[0].set_title('Original task: curriculum forecasts');ax[0].set_ylabel('Correct-choice probability, test (%)');ax[0].set_ylim(40,102);ax[0].axhline(50,color='#d1d5db',ls=':',lw=1)
families=['original','relocated','deterministic'];xf=np.arange(3)
for role,offset in zip(colors,[-.19,0,.19]):
 yy=[next(r for r in m if r['family']==f and r['curriculum']=='blocked')['roles'][role]['test_signal_probability'] for f in families]
 ax[1].plot(xf+offset,np.array(yy)*100,'o',color=colors[role],ms=6)
ax[1].set_xticks(xf,['Original','Noise moved','Deterministic'],rotation=25,ha='right');ax[1].set_ylim(40,102);ax[1].axhline(50,color='#d1d5db',ls=':',lw=1);ax[1].set_title('Blocked-task robustness')
for role in ('no_oracle','oracle','learned'):ax[1].plot([],[],color=colors[role],marker='o',ls='',label=labels[role])
a=[next(r for r in m if r['family']=='original' and r['curriculum']==c)['roles']['learned'] for c in ['blocked','interleaved']]
ax[2].bar(np.array([0,1])-.17,[r['signal_w_last40'] for r in a],.34,color='#176c9d',label='Deterministic signal')
ax[2].bar(np.array([0,1])+.17,[r['noise_w_last40'] for r in a],.34,color='#b5525c',label='Irreducible noise')
ax[2].set_xticks([0,1],['Blocked','Interleaved']);ax[2].set_ylim(0,1.06);ax[2].set_title('Learned predictability weights');ax[2].legend(frameon=False,fontsize=8,loc='upper right')
for a0 in ax:
 a0.spines[['top','right']].set_visible(False);a0.grid(axis='y',alpha=.15);a0.set_axisbelow(True)
ax[0].legend(frameon=False,fontsize=7.5,loc='lower left')
fig.suptitle('Synthetic feasibility only: 20 new seeds per condition, 200 stories each',fontsize=12,y=1.01)
fig.text(.01,-.025,'Error bars: paired-seed bootstrap 95% intervals. State permutations give identical predictions. No human responses or fits.',fontsize=9,color='#4b5563')
fig.tight_layout();fig.savefig(p/'result.png',dpi=180,bbox_inches='tight');fig.savefig(p/'result.svg',bbox_inches='tight')
print(json.dumps({'png_bytes':(p/'result.png').stat().st_size,'numpy':np.__version__,'matplotlib':matplotlib.__version__}))
