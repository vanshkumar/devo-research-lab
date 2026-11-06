"""Scientific summary from saved numerical artifacts; no new data access."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

C=Path(__file__).resolve().parents[1]
fit=json.loads((C/'artifacts/transition_fit/RESULT.json').read_text())
comparison=json.loads((C/'artifacts/source_comparison/RESULT.json').read_text())
control=json.loads((C/'artifacts/decision_controls/primary_pooled64_RESULT.json').read_text())
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,3,figsize=(14,4.5),gridspec_kw={'width_ratios':[1,1.3,1]})
grid=fit['grid_results']
axes[0].plot([g['rho'] for g in grid],[100*g['objective_equal_lab_curve_mae'] for g in grid],'-o',color='#355b91')
axes[0].axvline(fit['selected_rho'],color='#bd6240',linestyle='--',alpha=.8)
axes[0].set(xlabel='Shared session coefficient ρ',ylabel='Equal-lab curve MAE (pp)',
            title='Finite fit: 46 consumed animals / 7 labs',xticks=[.5,.6,.7,.8,.9,1.])
names=['existing','session','growth','persistence']
labels=['Existing\nupdater','Fitted\nsession rule','Exposure\ngrowth','Prefix\npersistence']
colors=['#bd6240','#355b91','#4a8263','#8a8e96']
values=[100*comparison['metrics'][k]['equal_lab_curve_mae'] for k in names]
bars=axes[1].bar(labels,values,color=colors,width=.7)
for bar,value in zip(bars,values):
    axes[1].text(bar.get_x()+bar.get_width()/2,value+.16,f'{value:.2f}',ha='center',va='bottom')
axes[1].set(ylabel='Equal-lab curve MAE (pp)',title='Development comparison: 64 animals / 9 labs',ylim=(0,max(values)*1.18))
cases=['signal_baselines_plus10pp','signal_baselines_minus10pp']
rates=[control['cases'][k]['decision_rate'] for k in cases]
points=np.array([r['rate'] for r in rates])*100
low=np.array([r['interval95_ClopperPearson'][0] for r in rates])*100
high=np.array([r['interval95_ClopperPearson'][1] for r in rates])*100
axes[2].bar(['Baseline +10 pp','Baseline −10 pp'],points,color='#355b91',width=.6)
axes[2].errorbar([0,1],points,yerr=[points-low,high-points],fmt='none',ecolor='#202a38',capsize=4)
axes[2].axhline(80,color='#bd6240',linestyle='--',label='Frozen requirement: 80%')
for i,value in enumerate(points):axes[2].text(i,value+3,f'{value:.2f}%',ha='center')
axes[2].set(ylabel='Decision success (%)',title='Known correct forecast / 20 animals',ylim=(0,100))
axes[2].legend(loc='upper left',fontsize=8,frameon=False)
fig.suptitle('The bounded session-rule comparison does not earn a protected transport test',fontsize=14,y=1.01)
fig.text(.5,-.02,'Consumed source evidence throughout. Six 500-opportunity bins after a 1,000-opportunity prefix. Pan20 prefixes/outcomes remain sealed.',ha='center',fontsize=9)
fig.tight_layout()
out=C/'figures';out.mkdir(exist_ok=True)
fig.savefig(out/'BOUNDED_RESULT.png',dpi=180,bbox_inches='tight')
fig.savefig(out/'BOUNDED_RESULT.svg',bbox_inches='tight')
