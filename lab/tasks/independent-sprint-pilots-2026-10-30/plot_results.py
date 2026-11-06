"""Plot saved exploratory summaries; no model fitting or source simulation."""
import sys,os
from pathlib import Path
sys.dont_write_bytecode=True
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parent/'matplotlib_cache')
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import HERE, read

def load(name):return json.loads(read(HERE/'outputs'/name,'derived_result'))

def main():
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.titlesize':11,'savefig.facecolor':'white'})
    plants=(100,101,102);colors={'oracle':'#20262e','clocked':'#366b9f','unregistered':'#a06a9f',
                                'onset_reset':'#227b8c','no_clock':'#d97922','tonic_forward':'#57964d'}
    labels={'oracle':'True-error oracle','clocked':'Supplied clock','unregistered':'Shifted onset, fixed clock',
            'onset_reset':'Reset retained clock','no_clock':'Zero HVC','no_clock_forward':'Zero HVC',
            'no_clock_reverse':'Zero HVC, reverse tutor','tonic_forward':'Constant HVC drive'}
    runs=[load('teaching_learning_%03d_per_order_20.json'%plant)['results'] for plant in plants]
    follow=[load('teaching_followup_%03d.json'%plant) for plant in plants]
    fig,axes=plt.subplots(2,2,figsize=(13,8.6),layout='constrained')
    ax=axes[0,0]
    modes=('oracle','clocked','unregistered','onset_reset','no_clock')
    for i,mode in enumerate(modes):
        vals=[100*next(r['improvement'] for r in rows if r['mode']==mode) for rows in runs]
        ax.scatter(np.arange(3)+(i-2)*.13,vals,color=colors[mode],s=45,label=labels[mode])
    ax.set(xticks=np.arange(3),xticklabels=plants,ylabel='Initial feature error removed (%)',
           title='A. Complete shape/order learning; 1,206 scalar queries')
    lo=min(0,min(100*r['improvement'] for rows in runs for r in rows)-2)
    ax.set_ylim(lo,102);ax.legend(fontsize=8,loc='lower left',frameon=False)
    ax=axes[0,1]
    for j,variant in enumerate(('no_clock_forward','no_clock_reverse','onset_reset')):
        vals=[next(r['target_rank'] for r in d['expanded_order_policy'] if r['variant']==variant) for d in follow]
        color=colors['onset_reset'] if variant=='onset_reset' else ('#86519e' if variant.endswith('reverse') else colors['no_clock'])
        ax.plot(plants,vals,marker='o',label=labels[variant],color=color)
    ax.set(xticks=plants,ylabel='Tutor-order rank among 64 (1 is best)',ylim=(.2,65),
           title='B. Broader order choices at exact tutor content')
    ax.set_yticks([1,10,20,30,40,50,60])
    ax.axhline(1,color='#aaaaaa',lw=.8,ls=':');ax.legend(fontsize=8,frameon=False)
    ax=axes[1,0]
    variants=('true_waveform_error','onset_reset','no_clock_forward','tonic_forward')
    for j,variant in enumerate(variants):
        vals=[next(r['durations'][-1] for r in d['duration_learning'] if r['variant']==variant) for d in follow]
        color=colors['oracle'] if variant=='true_waveform_error' else colors['no_clock'] if variant=='no_clock_forward' else colors[variant]
        label='Waveform-error oracle' if variant=='true_waveform_error' else labels[variant]
        ax.scatter(np.arange(3)+(j-1.5)*.13,vals,color=color,s=45,label=label)
    ax.axhline(1,color='#777777',ls=':',lw=1)
    ax.set(xticks=np.arange(3),xticklabels=plants,ylim=(.67,1.23),ylabel='Final duration stretch (target = 1)',
           title='C. Duration-only learning after shape; start 0.8')
    ax.legend(fontsize=8,frameon=False,loc='upper left')
    ax=axes[1,1]
    for j,(variant,strength) in enumerate((('no_clock_forward',.1),('no_clock_forward',.5),('onset_reset',.1),('onset_reset',.5))):
        key=variant+'_'+str(strength)
        vals=[next(r['one_evaluation_correct_fraction'] for r in d['source_current_noise_assay'] if r['variant']==key) for d in follow]
        color=colors['no_clock'] if variant.startswith('no_clock') else colors['onset_reset']
        ax.scatter(np.arange(3)+(j-1.5)*.14,vals,color=color,marker='o' if strength==.1 else 's',
                   s=48,label=labels[variant]+', current noise '+str(strength))
    ax.axhline(1/6,color='#aaaaaa',ls=':',lw=1)
    ax.set(xticks=np.arange(3),xticklabels=plants,ylim=(-.03,1.04),ylabel='Correct order selected (20 trial sets)',
           title='D. Frozen-circuit source-noise assay; six orders')
    ax.legend(fontsize=8,frameon=False,loc='center left',bbox_to_anchor=(0,.75))
    fig.suptitle('Exploratory teaching pilot: three consumed synthetic tuples',fontsize=14)
    fig.supxlabel('Plant ID. B uses a privileged content fixture; C is one-axis learning; D is a fixed-circuit assay, not noisy motor learning.',fontsize=9)
    fig.savefig(HERE/'outputs/TEACHING_RESULT.png',dpi=170)
    plt.close(fig)
    d=load('worm_followup.json');f=d['families'];ctrl=load('worm_controls.json')['rows']
    fig,axes=plt.subplots(1,2,figsize=(12.7,4.4),layout='constrained')
    ax=axes[0];x=np.arange(len(f))
    ax.bar(x-.15,[100*r['population_gain'] for r in f],width=.3,color='#467ca7',label='Population family')
    ax.bar(x+.15,[100*r['with_fallback_gain'] for r in f],width=.3,color='#75a78d',label='Population/local fallback')
    ax.axhline(0,color='#444444',lw=.8)
    ax.set(xticks=x,xticklabels=[r['uid'] for r in f],ylabel='Test MSE gain over selected local family (%)',
           title='A. Six consumed worms; 3-second forecasts')
    ax.tick_params(axis='x',labelrotation=40);ax.legend(fontsize=8,frameon=False)
    ax=axes[1]
    for j,(name,label) in enumerate((('rotation','Shared rotation'),('independent_ar','Independent AR'),('independent_ar2','Independent AR2'))):
        values=[100*r['population_current_gain_vs_local_history'] for r in ctrl if r['uid'].rsplit('_',1)[0]==name]
        assert len(values)==5
        ax.scatter(np.full(5,j)+np.linspace(-.12,.12,5),values,s=36,color=('#467ca7','#b99566','#8f7aa4')[j])
    ax.axhline(0,color='#444444',lw=.8)
    ax.set(xticks=[0,1,2],xticklabels=['Shared rotation','Independent AR','Independent AR2'],
           ylabel='Population-current gain over own 5 lags (%)',title='B. Five seeds per known generated control')
    fig.suptitle('Population forecasting: strong local memory changes the comparison',fontsize=13)
    fig.supxlabel('Forecast recipe is refitted within each animal. No cross-animal weight transfer, untouched validation or causal-circuit claim.',fontsize=9)
    fig.savefig(HERE/'outputs/WORM_RESULT.png',dpi=170)
    plt.close(fig)
    print('Saved outputs/TEACHING_RESULT.png and outputs/WORM_RESULT.png')

if __name__=='__main__':main()
