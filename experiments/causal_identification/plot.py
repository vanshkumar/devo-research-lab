#!/usr/bin/env python3
import os
from pathlib import Path
HERE=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(HERE/'mpl-cache'))
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
s=json.loads((HERE/'summary.json').read_text())
r=[x for x in s if x['phase']=='verification' and x['q']>0]
fig,ax=plt.subplots(figsize=(6.5,4),constrained_layout=True)
for key,label,c in [('B_error','Feedback B error','#aa3d25'),('F_error','Closed-loop F error','#126e82')]:
 x=[v['q'] for v in r]; med=[v[key+'_median'] for v in r]
 lo=[v[key+'_q10'] for v in r]; hi=[v[key+'_q90'] for v in r]
 ax.plot(x,med,'o-',label=label,color=c); ax.fill_between(x,lo,hi,alpha=.18,color=c)
ax.set(xscale='log',yscale='log',xlabel='Independent feedback excitation SD q',ylabel='Frobenius parameter error',title='Knowing closed-loop dynamics does not locate recurrence')
ax.legend(frameon=False); ax.grid(alpha=.2,which='both')
ax.text(.03,.03,'50 reserved seeds; T=2,000; bands = 10th–90th percentile\nSynthetic linear Gaussian model; parameters fixed in advance',transform=ax.transAxes,fontsize=8)
fig.savefig(HERE/'excitation_errors.png',dpi=180)
