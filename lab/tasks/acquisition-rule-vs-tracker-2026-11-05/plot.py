import time
import resource
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime,timezone
import json
HERE=Path(__file__).resolve().parent
IO={'summary_read_bytes':0}
def get(path):
    b=path.read_bytes();IO['summary_read_bytes']+=len(b);return json.loads(b)
def utc():return datetime.now(timezone.utc).isoformat()
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2)+'\n')

begin=time.monotonic();r=get(HERE/'EARLY_REDUCTION.json')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(11,4.6),gridspec_kw={'width_ratios':[1,1.15]})
colors={'growth':'#487ca5','recent_growth':'#b86628','gru':'#387955'}
labels={'growth':'Retained growth','recent_growth':'Recent-state growth','gru':'Frozen GRU'}
for name in colors:
    y=[];lo=[];hi=[]
    for c in ('200','1000'):
        v=r['risks'][name][c]['2000']['equal_side_mae'];y.append(v['equal_animal']*100)
        lo.append((v['equal_animal']-v['animal_t95'][0])*100);hi.append((v['animal_t95'][1]-v['equal_animal'])*100)
    ax[0].errorbar([200,1000],y,yerr=np.array([lo,hi]),color=colors[name],marker='o',lw=1.8,capsize=3,label=labels[name])
ax[0].set(xticks=[200,1000],xlabel='Observed calibration opportunities',ylabel='Individual side-specific accuracy MAE (%)',
          title='Same future: opportunities 1,001–3,000')
ax[0].legend(frameon=False,loc='upper right',fontsize=8)
for k,name in enumerate(('growth','recent_growth')):
    for hpos,h in enumerate(('500','2000')):
        v=r['paired_information_contrast'][name][h]['equal_side_mae'];pos=hpos+(k-.5)*.22
        mean=v['equal_animal']*100;ci=np.array(v['animal_t95'])*100
        ax[1].errorbar(pos,mean,yerr=[[mean-ci[0]],[ci[1]-mean]],color=colors[name],fmt='o',capsize=3)
        site=v['equal_site']*100;sci=np.array(v['site_t95'])*100
        ax[1].errorbar(pos+.035,site,yerr=[[site-sci[0]],[sci[1]-site]],color=colors[name],fmt='s',mfc='white',alpha=.6,capsize=2)
ax[1].axhline(0,color='#666',lw=.9)
ax[1].set(xticks=[0,1],xticklabels=['1,001–1,500','1,001–3,000'],xlabel='Shared scored opportunities',
          ylabel='Change in ordinary-minus-GRU error (pp)',title='Paired change from early to later calibration')
ax[1].text(.03,.04,'Circles: paired-mouse 95% intervals\nOpen squares: observed-site sensitivity',transform=ax[1].transAxes,fontsize=8,va='bottom')
fig.suptitle('Same future, later forecasts: both improve; neural advantage remains unresolved',fontsize=12,y=.98)
fig.text(.05,.01,'64 consumed mice. Forecasts condition on realized session opportunities; source-fit/teacher uncertainty is not included in these intervals.',fontsize=8,color='#555')
fig.tight_layout(rect=[0,.055,1,.92]);fig.savefig(HERE/'CALIBRATION_FEASIBILITY.png',dpi=170)
save('PLOT_EXECUTION.json',dict(utc=utc(),seconds=time.monotonic()-begin,io=dict(IO),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
print('Saved plot',flush=True)
