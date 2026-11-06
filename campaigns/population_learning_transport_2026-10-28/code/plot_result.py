"""Standalone scientific source-result figure, no raw outcomes accessed."""
import json
import numpy as np
from campaign import C
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    r=json.loads((C/'artifacts/results/SOURCE_RESULT.json').read_text())
    fig,ax=plt.subplots(1,2,figsize=(11,4.4),gridspec_kw={'width_ratios':[1.3,1]})
    x=np.arange(6)*500+250
    colors=dict(rnn='#b33c4b',growth='#257d98',persistence='#8b8794')
    ax[0].plot(x,np.asarray(r['models']['rnn']['observed_curve'])*100,'o-',color='#222222',lw=2.2,label='Observed: 24 new source animals')
    for k,label in [('rnn','Frozen RNN'),('growth','Frozen growth'),('persistence','Prefix persistence')]:
        ax[0].plot(x,np.asarray(r['models'][k]['forecast_curve'])*100,'s--',color=colors[k],lw=1.8,ms=4,label=label)
    ax[0].set(xlabel='Opportunities after 1,000-trial prefix (bin centers)',ylabel='Equal-side ±100% correct, omissions as failures (%)',ylim=(42,73),title='Prospective mean acquisition')
    ax[0].legend(frameon=False,fontsize=8.5,loc='upper left');ax[0].grid(alpha=.15)
    ax[1].axvspan(-5,5,color='#dbe8d6',alpha=.65,label='Frozen ±5 pp tolerance')
    ax[1].axvline(0,color='#888',lw=.8)
    for j,k in enumerate(('rnn','growth','persistence')):
        ci=r['models'][k]['intervals'];mean=ci['mean']*100
        outer=np.asarray(ci['cluster_90'])*100;inner=np.asarray(ci['animal_90'])*100
        ax[1].plot(outer,[j,j],color=colors[k],lw=1.7,alpha=.55)
        ax[1].plot(inner,[j,j],color=colors[k],lw=5,solid_capstyle='butt')
        ax[1].plot(mean,j,'o',color=colors[k],mec='white',ms=6)
    ax[1].set(yticks=[0,1,2],yticklabels=['RNN','Growth','Persistence'],xlabel='Observed minus forecast (percentage points)',xlim=(-13.5,13.5),title='Mean bias: two 90% intervals')
    ax[1].invert_yaxis();ax[1].grid(axis='x',alpha=.15)
    ax[1].text(.02,-.25,'Thick: animal t interval. Thin: lab-cluster t interval.\nFive represented labs; no arbitrary-new-lab guarantee.',transform=ax[1].transAxes,fontsize=8,color='#444')
    for a in ax:
        a.spines[['top','right']].set_visible(False)
    fig.suptitle('Frozen RNN misses the new-source population gate',fontsize=14,y=1.01)
    fig.tight_layout();dest=C/'figures';dest.mkdir(exist_ok=True)
    fig.savefig(dest/'SOURCE_POPULATION_RESULT.png',dpi=190,bbox_inches='tight');plt.close(fig)

if __name__=='__main__':main()
