"""Static research figure from saved results; no new fitting or selection."""
import json,pathlib,os
H=pathlib.Path(__file__).resolve().parent;C=H.parent
os.environ.setdefault('MPLCONFIGDIR',str(C/'.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
out=C/'figures';out.mkdir(exist_ok=True)
a=json.loads((H/'atlas/followup_summary.json').read_text())['results']
s=json.loads((C/'data/song_learning/fig3_extracted.json').read_text())
def flat(key):return np.array([v for r in s[key] for v in r.values()])
fig,axes=plt.subplots(1,2,figsize=(12.3,4.5),layout='constrained')
ax=axes[0]
for i,r in enumerate(a):
    lo=100*r['joint_min']/r['n'];hi=100*r['joint_max']/r['n']
    ax.plot([lo,hi],[i,i],lw=7,color='#237c87',solid_capstyle='butt')
    ax.scatter([lo,hi],[i,i],s=28,color='#237c87')
    ax.text(hi+1,i,f"{r['joint_min']}–{r['joint_max']} / {r['n']}",va='center',fontsize=9)
ax.set_yticks(range(len(a)),[r['cluster'] for r in a]);ax.invert_yaxis();ax.set_xlim(30,79)
ax.set_xlabel('Feasible OXT + AVP detected overlap (%)')
ax.set_title('A  Bounds from human atlas marginals',loc='left',fontsize=12)
ax.text(.01,-.25,'Intervals are logical bounds, not confidence intervals.\nDetected RNA does not establish functional coexpression.',transform=ax.transAxes,fontsize=9,color='#555555')
ax=axes[1];tr=np.array([list(r.values()) for r in s['e.syllable_traces']]);x=np.arange(1,tr.shape[1]+1)
for row in tr:ax.plot(x,row,color='#8796a1',lw=.6,alpha=.4)
ax.fill_between(x,flat('f.shuffle_pvalue_lower'),flat('f.shuffle_pvalue_upper'),color='#d7b476',alpha=.5,label='Supplied shuffle envelope')
ax.plot(x,flat('f.population_mean'),color='#164b78',lw=2,label='Mean of 25 syllable traces')
ax.set_xlabel('Column of supplied trajectory');ax.set_ylabel('Source future-alignment measure')
ax.set_title('B  Corrected juvenile song source data',loc='left',fontsize=12);ax.legend(fontsize=8,frameon=False,loc='upper left')
ax.text(.01,-.25,'25 syllables are not 25 independent birds.\nAssociation does not identify tutor-target acquisition.',transform=ax.transAxes,fontsize=9,color='#555555')
for ax in axes:
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.15)
fig.savefig(out/'main_results.png',dpi=170,bbox_inches='tight');fig.savefig(out/'main_results.svg',bbox_inches='tight')
print('figures/main_results.png and .svg')
