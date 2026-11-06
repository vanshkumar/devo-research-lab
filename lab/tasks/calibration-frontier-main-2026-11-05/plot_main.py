"""Scientific summary figure from saved authorized aggregate analyses only."""
import time,resource
BEGIN=time.monotonic();CPU=time.process_time()
import json
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
a=(HERE/'MAIN_ANALYSIS.json').read_bytes();d=json.loads(a)
fb=(HERE/'MAIN_FAMILY_REFINED.json').read_bytes();family=json.loads(fb)['columns']
source_upper={c:max(d['bands']['joint']['upper'][i] for i,col in enumerate(family)
                   if col['kind']=='source' and col['reference']=='recent_selected' and col['metric']=='A' and col['cutoff']==c)
              for c in (200,1000)}
p=d['primary_rows'];sites=d['site_sensitivity'];source=d['source_points']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,2,figsize=(12,9),constrained_layout=False)
blue='#205b92';orange='#b85b26';gray='#aab4be';red='#9c3131';offset=np.array([-.12,.12])
for ax,metric,scale,title,ylabel,margin in [
    (axes[0,0],'A',100,'Primary accuracy benefit','Ordinary MAE − GRU MAE (pp)',2),
    (axes[0,1],'D',1,'Primary proper-score margin','0.9 × ordinary score − GRU score',0)]:
    rows=[r for r in p if r['metric']==metric]
    for i,r in enumerate(rows):
        x=i
        ax.plot([x,x],[scale*r['joint_lower'],scale*r['joint_upper']],color=gray,lw=8,alpha=.5,
                solid_capstyle='butt',label='Primary rows: '+str(d.get('joint_column_count',632))+'-family band' if i==0 else None)
        ax.errorbar(x,scale*r['point'],yerr=np.array([[scale*(r['point']-r['primary_lower'])],
            [scale*(r['primary_upper']-r['point'])]]),fmt='o',color=blue,capsize=5,lw=2,
            label='Primary 4: nominal 95% band' if i==0 else None)
        pts=[s[metric]*scale for s in source if s['reference']=='recent_selected' and s['cutoff']==r['cutoff']]
        jitter=np.linspace(-.13,.13,len(pts))
        ax.scatter(x+.25+jitter*.3,pts,s=13,color=orange,alpha=.55,
                   label='Source points (no uncertainty band)' if i==0 else None)
    ax.axhline(margin,color=red,ls='--',lw=1.4,label='Material benefit boundary')
    if margin!=0:ax.axhline(0,color='black',lw=.7,alpha=.5)
    ax.set_xticks([0,1],['Observe 200','Observe 1,000']);ax.set_xlim(-.5,1.55)
    ax.set_ylabel(ylabel);ax.set_title(title,loc='left',fontweight='bold');ax.grid(axis='y',alpha=.15)
axes[0,0].text(.98,.96,'Source envelope unresolved\nupper bounds '+f'{100*source_upper[200]:.2f} / {100*source_upper[1000]:.2f} pp',
               transform=axes[0,0].transAxes,ha='right',va='top',fontsize=8,color=orange,
               bbox=dict(facecolor='white',alpha=.9,edgecolor='none',pad=3))
axes[0,1].text(.98,.96,'Source envelope unresolved:\nmaterial score gains remain allowed',
               transform=axes[0,1].transAxes,ha='right',va='top',fontsize=8,color=orange,
               bbox=dict(facecolor='white',alpha=.9,edgecolor='none',pad=3))
axes[0,0].legend(fontsize=8,loc='best',frameon=False)
ax=axes[1,0];Aidx=[j for j,r in enumerate(p) if r['metric']=='A']
for label,key,color,marker in [('All64','animal_weighted_cluster_point',blue,'o'),
                             ('Old40','old40_point','#6e438a','s'),('Later24','later24_point',orange,'D')]:
    y=np.array(sites[key])[Aidx]*100
    ax.plot([0,1],y,marker=marker,color=color,label=label,lw=1.4)
ax.axhline(2,color=red,ls='--',lw=1.2);ax.axhline(0,color='black',lw=.7)
ax.set_xticks([0,1],['Observe 200','Observe 1,000']);ax.set_ylabel('Ordinary MAE − GRU MAE (pp)')
ax.set_title('Original cohort composition',loc='left',fontweight='bold');ax.legend(frameon=False,fontsize=9)
ax.grid(axis='y',alpha=.15)
ax=axes[1,1];models=[('growth','Original growth',gray),('recent100','Recent-state growth',orange),('gru','Frozen GRU',blue)]
for j,(model,label,color) in enumerate(models):
    rows=[next(r for r in d['absolute_risks'] if r['condition']=='primary' and r['cutoff']==c and r['model']==model) for c in (200,1000)]
    values=[r['equal_animal']['mae']*100 for r in rows]
    lower=[v-r['equal_animal_pointwise95']['mae'][0]*100 for v,r in zip(values,rows)]
    upper=[r['equal_animal_pointwise95']['mae'][1]*100-v for v,r in zip(values,rows)]
    ax.bar(np.arange(2)+(j-1)*.23,values,width=.22,color=color,label=label,
           yerr=np.array([lower,upper]),capsize=3,error_kw=dict(lw=.8))
ax.set_xticks([0,1],['Observe 200','Observe 1,000']);ax.set_ylabel('Side-specific individual MAE (%)')
ax.set_title('Absolute forecast error',loc='left',fontweight='bold');ax.legend(frameon=False,fontsize=8)
ax.grid(axis='y',alpha=.15)
fig.suptitle('Fixed acquisition forecasts: same opportunities 1,001–3,000',x=.07,y=.98,ha='left',fontsize=16,fontweight='bold')
fig.text(.07,.925,'Unchanged GRU versus source-selected recent-state growth; supplied future opportunity/session boundaries',fontsize=10,color='#444444')
fig.text(.07,.045,'Gray bands cover the PRIMARY ROWS within the652-column family. Orange source points omit their animal-uncertainty bands.\n'
         f'The source envelope does NOT exclude material gains (accuracy upper bounds {100*source_upper[200]:.2f} / {100*source_upper[1000]:.2f} pp). Primary1,024; sourceGRU256 particles.\n'
         'Consumed postvalidation. Bottom-right: pointwise t23 intervals. Failed input/engagement stresses certify neither true-environment robustness nor mechanism.',
         fontsize=8,color='#444444',va='bottom')
fig.subplots_adjust(left=.08,right=.98,top=.87,bottom=.15,hspace=.38,wspace=.30)
fig.savefig(HERE/'MAIN_RESULT.png',dpi=180)
plt.close(fig)
out=dict(utc=datetime.now(timezone.utc).isoformat(),scientific_cpu_seconds=time.process_time()-CPU,
         process_wall_seconds=time.monotonic()-BEGIN,summary_read_bytes=len(a)+len(fb),
         peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         input='MAIN_ANALYSIS and MAIN_FAMILY_REFINED JSON summaries only; no trial/particle reads',output='MAIN_RESULT.png')
(HERE/'PLOT_RESOURCES.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
