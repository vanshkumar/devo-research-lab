"""Static scientific diagnostic from the saved synthetic replicates."""
from pathlib import Path
import os, argparse
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--label',default='calibration_challenge');args=parser.parse_args()
OUT=ROOT/args.label
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

d=pd.read_csv(OUT/'replicates.csv')
variants=['association','association_z','psychometric_z','oracle_skill','oracle_skill_wide3',
          'independent_200','independent_800','independent_3200']
labels=['Original association','Association standardized','First200 psychometric slopes',
        'Oracle latent skill','Oracle + wider effect prior','Extra sensory trials:200',
        'Extra sensory trials:800','Extra sensory trials:3200']
fig,axes=plt.subplots(1,3,figsize=(13,5.6),sharey=True)
for ax,scenario,title in zip(axes,['carryover_null','slow_05','slow_minus05'],['Shared common law','Injected +5 percentage points','Injected −5 percentage points']):
    vals=[100*d.loc[(d.scenario==scenario)&(d.variant==v),'effect'].to_numpy() for v in variants]
    means=[np.mean(v) for v in vals]
    ax.boxplot(vals,positions=np.arange(8),vert=False,widths=.55,whis=(5,95),showfliers=False,
               boxprops={'color':'#466c91'},medianprops={'color':'#133b60'},whiskerprops={'color':'#466c91'},capprops={'color':'#466c91'})
    ax.scatter(means,np.arange(8),marker='D',s=15,color='#b74b29',label='Mean')
    truth=100*d.loc[d.scenario==scenario,'truth_effect'].mean()
    ax.axvline(truth,color='#2b784d',linestyle='--',linewidth=1.5,label='Injected truth')
    ax.axvline(0,color='#bbbbbb',linewidth=.6)
    ax.set_title(title,fontsize=11)
    ax.set_xlim(-9,10);ax.grid(axis='x',alpha=.18);ax.set_yticks(np.arange(8));ax.set_yticklabels(labels)
axes[0].invert_yaxis();axes[-1].legend(loc='lower right',fontsize=8)
fig.suptitle('Calibration and regularization diagnosis on the actual schedules',fontsize=14)
fig.supxlabel('Estimated standardized effect (percentage points)',y=.095,fontsize=11)
fig.text(.5,.025,'30 simulated datasets per generator. Boxes:25th–75th percentiles; whiskers:5th–95th. All variants share datasets.\nOracle and extra-sensory variants use information absent from the empirical dataset. These are not validation results.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.09,1,.94))
fig.savefig(OUT/'calibration_recovery.png',dpi=180)
fig.savefig(OUT/'calibration_recovery.pdf')
print(OUT/'calibration_recovery.png')
