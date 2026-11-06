"""Plot generator-conditional detection rates and simulation uncertainty."""
from pathlib import Path
import os,argparse
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--label',default='sample_size_challenge');a=p.parse_args();OUT=ROOT/a.label
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

d=pd.read_csv(OUT/'replicates.csv')
designs=[(2,'original'),(2,'independent800_wide3'),(4,'original'),(4,'independent800_wide3')]
labels=['160 people\nOriginal','160 people\nExtra800 + wider prior','320 people\nOriginal','320 people\nExtra800 + wider prior']
fig,axes=plt.subplots(1,2,figsize=(12,5),sharey=True)
for ax,metric,title in zip(axes,['score_detect','both_detect'],['Overall score interval favors condition','Overall AND unseen-schedule intervals favor condition']):
    for j,(scenario,label,color) in enumerate([('carryover_null','Shared-law null','#65717d'),('slow_05','Injected +5 points','#2675aa'),('slow_minus05','Injected −5 points','#b85a43')]):
        means=[];low=[];high=[]
        for factor,variant in designs:
            g=d[(d.factor==factor)&(d.variant==variant)&(d.scenario==scenario)];n=len(g);p=float(g[metric].mean());z=1.96
            den=1+z*z/n;center=(p+z*z/(2*n))/den;radius=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
            means.append(p);low.append(p-center+radius);high.append(center+radius-p)
        x=np.arange(4)+(j-1)*.16
        ax.errorbar(x,means,yerr=[low,high],fmt='o',capsize=3,color=color,label=label,markersize=5)
    ax.axhline(.8,color='#808080',linestyle='--',linewidth=1)
    ax.axhline(.05,color='#bcbcbc',linestyle=':',linewidth=1)
    ax.set_xticks(np.arange(4));ax.set_xticklabels(labels,fontsize=9)
    ax.set_ylim(-.02,1.03);ax.set_title(title,fontsize=11);ax.grid(axis='y',alpha=.18)
axes[0].set_ylabel('Fraction of30 simulated cohorts')
handles,legend_labels=axes[1].get_legend_handles_labels()
fig.legend(handles,legend_labels,loc='upper center',bbox_to_anchor=(.5,.90),ncol=3,frameon=False,fontsize=9)
fig.suptitle('Additional observations: detection improves, but the full criterion remains unmet',fontsize=13)
fig.text(.5,.025,'Error bars:95% Wilson intervals for simulation rates. Dashed:80% detection reference; dotted:5% null reference.\nPositive sustained-history generators, fixed ten schedules (three held out); not empirical-task power estimates.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.10,1,.86));fig.savefig(OUT/'sample_size_detection.png',dpi=180);fig.savefig(OUT/'sample_size_detection.pdf')
print(OUT/'sample_size_detection.png')
