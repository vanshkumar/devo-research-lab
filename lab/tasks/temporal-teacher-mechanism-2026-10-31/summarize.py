"""Aggregate whole-case effects; make the standalone scientific figure."""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
from common import ROOT,HERE,read,save,now
os.environ['MPLCONFIGDIR']=str(HERE/'mpl_cache')
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    cfg=json.loads((HERE/'CONFIG.json').read_text());d=json.loads(read(HERE/'outputs/DIAGNOSTICS.json','saved_diagnostic_summary'));assert d['complete']
    rng=np.random.default_rng(cfg['bootstrap_seed']);resamples=rng.integers(0,8,(cfg['bootstrap_replicates'],8));cases=d['cases'];modes=cfg['modes']
    def interval(values):
        a=np.asarray(values);return [float(x) for x in np.quantile(a[resamples].mean(1),[.025,.975])]
    bymode={}
    for mode in modes:
        rows=[next(r for r in case['results'] if r['mode']==mode) for case in cases]
        gain=np.array([r['improvement'] for r in rows]);loss=np.array([r['final_gold'] for r in rows])
        bymode[mode]={'mean_error_removal':float(gain.mean()),'error_removal_ci95':interval(gain),'mean_mse':float(loss.mean()),'mse_ci95':interval(loss),
                      'successes':sum(r['success'] for r in rows),'semantic_order_correct':sum(r['correct_semantic_order'] for r in rows),
                      'mean_abs_stretch_error':float(np.mean([r['abs_stretch_error'] for r in rows])),
                      'per_case_error_removal':gain,'per_case_mse':loss,
                      'best_queried_mse':[r['best_queried_gold'] for r in rows],
                      'best_gold_query_cost_minus_final_cost':[r['best_gold_query_cost_minus_final_cost'] for r in rows],
                      'regressed_beyond_best_queried_by_0_01':sum(r['regression_from_best_queried_gold']>.01 for r in rows),
                      'distinct_successes':sum(r['success'] for r,c in zip(rows,cases) if not c['repeated']),
                      'repeated_successes':sum(r['success'] for r,c in zip(rows,cases) if c['repeated'])}
    pairs={}
    for left,right in (('population','raw'),('population','normalized'),('unplasticized_population','population'),('state','population')):
        delta=np.array(bymode[left]['per_case_error_removal'])-np.array(bymode[right]['per_case_error_removal'])
        pairs[left+'_minus_'+right]={'mean_error_removal_gain':float(delta.mean()),'ci95':interval(delta),'whole_cases':8}
    noise={};fidelity={};temporal={}
    for mode in modes:
        if mode=='oracle':continue
        fidelity[mode]={}
        for content in ('exact_content','acquired_content'):
            rows=[case['fidelity'][mode][content] for case in cases]
            fidelity[mode][content]={'strict_correct_cases':sum(x['strict_correct'] for x in rows),'ties':sum(x['tie'] for x in rows),
                                     'best_wrong_minus_correct_margins':[x['best_wrong_minus_best_correct'] for x in rows]}
        noise[mode]={}
        onset_costs=[[case['temporal_probes']['onset_%d'%phase]['costs'][mode] for phase in cfg['diagnostic_onsets_ms']] for case in cases]
        temporal[mode]={'max_abs_onset_cost_change':float(np.max(np.ptp(np.array(onset_costs),axis=1)))}
        for label in ('duration_0.9','duration_1.1','gap_edit','content_edit'):
            margins=[case['temporal_probes'][label]['costs'][mode]-case['temporal_probes']['onset_0']['costs'][mode] for case in cases]
            temporal[mode][label]={'strict_rejection_cases':sum(x>1e-12 for x in margins),'margins':margins}
        for sigma in cfg['noise_sigma']:
            vals=[np.mean([r['scores'][mode]['strict_correct'] for r in case['noise'] if r['sigma']==sigma]) for case in cases]
            chosen=[np.mean([r['scores'][mode]['chosen_correct'] for r in case['noise'] if r['sigma']==sigma]) for case in cases]
            noise[mode][str(sigma)]={'mean_strict_correct_rate':float(np.mean(vals)),'ci95_over_whole_cases':interval(vals),
                                    'per_case_strict_correct_rate':vals,'mean_first_tie_chosen_correct_rate':float(np.mean(chosen))}
    result={'utc':now(),'whole_cases':8,'independent_biological_samples':0,'actor_queries_per_mode_per_case':3722,
            'summary_runtime':{'python':sys.version,'executable':sys.executable,'numpy':np.__version__,'matplotlib':matplotlib.__version__},
            'modes':bymode,'paired_effects':pairs,'fidelity':fidelity,'temporal_probes':temporal,'noise':noise,'verification':{'scalar_log_replays':len(d['checks']),
            'replayed_queries':sum(x['replayed_queries'] for x in d['checks']),'samplewise_waveform_checks':sum(x['direct_waveform_checks'] for x in d['checks'])}}
    save('outputs/SUMMARY.json',result)
    labels={'raw':'Raw rate','normalized':'Normalized rate','population':'Population, tutored','unplasticized_population':'Population, fixed circuit',
            'state':'Sequence memory / template','input_moments':'Static input moments'}
    colors={'raw':'#a8a9ad','normalized':'#777b82','population':'#1f77b4','unplasticized_population':'#e1862b','state':'#31906a','input_moments':'#a55e9b'}
    fig,axes=plt.subplots(1,3,figsize=(15,4.7),gridspec_kw={'width_ratios':[1.25,1.1,1]})
    selected=list(labels);xx=np.arange(8)
    for i,mode in enumerate(selected):
        vals=np.array(bymode[mode]['per_case_error_removal'])*100
        axes[0].plot(xx+(i-2.5)*.07,vals,'o',ms=4,color=colors[mode],label=labels[mode],alpha=.8)
    axes[0].axhline(95,color='#555555',lw=.8,ls='--');axes[0].set_xticks(xx,[str(c['case']) for c in cases],rotation=45)
    axes[0].set(ylabel='Waveform error removed (%)',xlabel='Whole synthetic case',title='A  Complete scalar-feedback learning')
    axes[0].axvspan(3.5,7.5,color='#f0f0f0',zorder=-5);axes[0].text(.73,.03,'Repeated elements',transform=axes[0].transAxes,ha='center',fontsize=8)
    target=np.array(cfg['target_stretches'])
    for mode,marker in (('population','o'),('unplasticized_population','s'),('state','^')):
        duration=[next(r for r in case['results'] if r['mode']==mode)['final_action'][5] for case in cases]
        axes[1].scatter(target,duration,s=35,marker=marker,color=colors[mode],label=labels[mode],alpha=.8)
    axes[1].plot([.8,1.2],[.8,1.2],color='#444444',lw=1,ls='--');axes[1].set(xlabel='Observed tutor stretch',ylabel='Learned motor stretch',title='B  Duration follows the tutor')
    for mode in selected:
        vals=[noise[mode][str(s)]['mean_strict_correct_rate']*100 for s in cfg['noise_sigma']]
        marker={'unplasticized_population':'s','state':'^'}.get(mode,'o');style={'unplasticized_population':'--','state':':'}.get(mode,'-')
        axes[2].plot(cfg['noise_sigma'],vals,marker=marker,ls=style,color=colors[mode],lw=1.4,ms=6 if mode in ('unplasticized_population','state') else 4)
    axes[2].set(xlabel='Active-sample sensory noise (σ)',ylabel='Strict correct choice (%)',title='C  Six-way temporal challenge',ylim=(-3,103),xticks=cfg['noise_sigma'])
    for ax in axes:ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15)
    axes[0].legend(loc='upper center',bbox_to_anchor=(1.45,-.26),ncol=3,frameon=False,fontsize=9)
    fig.suptitle('Tutor-learned evaluation without supplied premotor phase',fontsize=14,y=1.01)
    fig.tight_layout();fig.subplots_adjust(bottom=.3,wspace=.32);fig.savefig(HERE/'outputs/FIGURE.png',dpi=180,bbox_inches='tight');plt.close(fig)
    small={'modes':{mode:{k:v for k,v in row.items() if k in ('mean_error_removal','error_removal_ci95','mean_mse','successes','semantic_order_correct','regressed_beyond_best_queried_by_0_01')} for mode,row in bymode.items()},
           'paired_effects':pairs,'noise':{mode:{s:row['mean_strict_correct_rate'] for s,row in levels.items()} for mode,levels in noise.items()},'verification':result['verification'],
           'population_best_seen_mse':bymode['population']['best_queried_mse'],'population_best_gold_query_cost_minus_final_cost':bymode['population']['best_gold_query_cost_minus_final_cost']}
    print(json.dumps(small,indent=2),flush=True)
if __name__=='__main__':main()
