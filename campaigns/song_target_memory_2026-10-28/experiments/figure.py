from pathlib import Path
import os,json,csv
BASE=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(BASE/'outputs'/'mpl-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold'})
    fig,axes=plt.subplots(2,2,figsize=(12.8,9),layout='constrained')
    e=json.loads((BASE/'outputs/empirical_summary.json').read_text())
    h=json.loads((BASE/'outputs/hvc/SUMMARY.json').read_text())
    r=json.loads((BASE/'outputs/recovery_summary.json').read_text())
    a=json.loads((BASE/'audits/model_audit/audit_results.json').read_text())
    table=list(csv.DictReader((BASE/'audits/zhao_source/table_s1_transcription.csv').open()))
    ax=axes[0,0]
    for j,group in enumerate(['four_50ms','single_300ms_pooled']):
        vals=[float(x['element_mean_ms']) for x in table if x['protocol']==group]
        ax.scatter(j+np.linspace(-.10,.10,len(vals)),vals,s=30,alpha=.85,color=['#d7791d','#236b8e'][j])
    ax.plot([-.18,1.18],[152,152],ls=':',color='#666666',lw=1)
    ax.plot([-.18,1.18],[176.1,176.1],ls=':',color='#666666',lw=1)
    ax.set(yscale='log',ylim=(15,1600),xticks=[0,1],xticklabels=['4 x 50 ms\n26 table elements','1 x 300 ms\n11 pooled elements'],ylabel='Observed element mean duration (ms)',title='A  Duration effect survives missing bird grouping')
    ax.set_yticks([20,50,100,200,500,1000]);ax.set_yticklabels([20,50,100,200,500,1000])
    ax.text(.03,.96,'24.0 ms minimum separation, allowing rounding\nFinite observed summaries; no population CI',transform=ax.transAxes,va='top',fontsize=9)
    ax=axes[0,1]
    groups=[h['source_protocol']['10'],h['source_protocol']['0']]+[h['matched_train_schedule'][str(p)] for p in [10,20,40]]
    for j,d in enumerate(groups):
        for i,v in enumerate(d['clean_probe_ms']):
            ax.scatter(j+(i-2.5)*.037,1990 if v is None else v,marker='^' if v is None else 'o',s=40,color='#236b8e' if j<2 else '#aa523d')
    ax.axhline(100,color='#777777',ls=':',lw=1)
    ax.set(yscale='log',ylim=(20,4500),xticks=range(5),xticklabels=['Source\n100 ms','Source\nsingle','Spaced\n100 ms','Spaced\n200 ms','Spaced\n400 ms'],ylabel='Frozen neural sequence duration (ms)',title='B  Fixed network parameters fail spacing transfer')
    ax.set_yticks([30,100,300,1000,1990]);ax.set_yticklabels(['30','100','300','1000','>1990'])
    ax.text(.03,.96,'Six networks per condition; triangles are censored\nSource ~0.50 s vs spaced ~1.70 s between trains',transform=ax.transAxes,va='top',fontsize=9)
    ax=axes[1,0]
    vals=[];lo=[];hi=[]
    for task,phase in [('timing','WN'),('timing','return'),('pitch','WN'),('pitch','return')]:
        d=r['post_pre_rate_ratios'][task][phase];v=d['ratio_of_group_means'];vals.append(v);lo.append(v-d['extraction_only_interval'][0]);hi.append(d['extraction_only_interval'][1]-v)
    ax.bar(range(4),vals,color=['#236b8e','#236b8e','#a9b5be','#a9b5be'],width=.6)
    ax.errorbar(range(4),vals,yerr=[lo,hi],fmt='none',color='#222222',capsize=4)
    ax.axhline(1,color='#777777',ls=':',lw=1)
    ax.set(ylim=(0,1.48),xticks=range(4),xticklabels=['Timing\nlearning','Timing\nrecovery','Pitch\nlearning','Pitch\nrecovery'],ylabel='Post/pre ratio of displayed group mean rates',title='C  The recovery lesion also slows timing learning')
    ax.text(.03,.96,'Roberts2017: five birds/task, three shared\nError bars show extraction uncertainty only',transform=ax.transAxes,va='top',fontsize=9)
    ax=axes[1,1]
    d=a['functional_gain_recovery']['nominal_case_rows']
    x=[z['true_evaluator_fraction'] for z in d];y=[z['mean_estimate'] for z in d];er=[z['rmse'] for z in d]
    ax.plot([0,1],[0,1],ls=':',color='#777777')
    ax.errorbar(x,y,yerr=er,fmt='o-',color='#236b8e',capsize=4,label='Mean estimate +/- RMSE')
    ax.scatter([0],[.5],marker='x',s=90,color='#b24535',label='Off-target effect: false estimate')
    ax.set(xlim=(-.08,1.08),ylim=(-.15,1.2),xlabel='True functional evaluator contribution',ylabel='Estimated contribution',title='D  Functional testing needs a selective intervention')
    ax.text(.03,.96,'Synthetic illustration: 12 birds, 50 repeats/cell\nInvented noise regime; not biological power',transform=ax.transAxes,va='top',fontsize=9)
    ax.legend(loc='lower right',fontsize=8,frameon=False)
    fig.suptitle('Song target memory: strong intervention effects, limited architectural identification',fontsize=15,fontweight='bold')
    fig.savefig(BASE/'outputs/main_results.png',dpi=180)
    fig.savefig(BASE/'outputs/main_results.svg')
    print('Saved outputs/main_results.png and .svg')
if __name__=='__main__':main()
