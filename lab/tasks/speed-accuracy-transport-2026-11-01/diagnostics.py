from model import *
from analysis import evaluate

con=load('CONTROLS.json');main=load('SCORES.json');sens=load('PAPER_CUTOFF_SENSITIVITY.json')
signal=[x for x in con['records'] if x['kind']=='substantial_signal']
def gates(r):
    p=r['P'];b=r['REFERENCE']
    return {'joint_gain_ge10percent':p['joint_fractional_gain_over_reference']>=.10,
            'paired_interval_lower_positive':p['conditional_bootstrap_gain_percentiles'][0]>0,
            'accuracy_mse_better':p['accuracy_mse']<b['accuracy_mse'],
            'rt_mse_better':p['rt_mean_mse_s2']<b['rt_mean_mse_s2'],
            'accuracy_MAE_le5pp':p['accuracy_MAE']<=.05,
            'rt_MAE_le50ms':p['rt_mean_MAE_s']<=.05}
gatecounts={k:sum(gates(r)[k] for r in signal) for k in gates(signal[0])}
truth=np.array(con['truth']);counts=np.array(con['nominal_counts']);changed=[]
for noise in ['remove_accuracy_noise','remove_rt_noise','remove_both']:
    hits=[]
    for r in signal:
        rng=np.random.default_rng(r['seed']);pc=np.clip(truth[:,:,0]+rng.normal(0,.01,(8,1)),.01,.99)
        obs=np.stack([rng.binomial(counts,pc)/counts,truth[:,:,1]+rng.normal(0,.015,(8,1))+rng.normal(0,.20/np.sqrt(counts),(8,4))],axis=2)
        if noise in ['remove_accuracy_noise','remove_both']:obs[:,:,0]=truth[:,:,0]
        if noise in ['remove_rt_noise','remove_both']:obs[:,:,1]=truth[:,:,1]
        p={'reference':'REFERENCE','predictions':{'P':truth.tolist(),'REFERENCE':(truth-.10).tolist()}}
        rr=evaluate(p,obs,r['seed']);hits.append(rr['primary_P_rule_passes'])
    changed.append({'changed_observation':noise,'passes':sum(hits),'n':100})
ref=main['reference'];P=np.array(main['models']['P']['per_person_losses']);E=np.array(main['models'][ref]['per_person_losses'])
influence=[]
for i in range(8):
    ix=np.arange(8)!=i;influence.append({'omitted_id':10+i,'joint_P_fractional_gain':float(1-P[ix,2].mean()/E[ix,2].mean()),'accuracy_MSE_gain':float(1-P[ix,0].mean()/E[ix,0].mean()),'RT_MSE_gain':float(1-P[ix,1].mean()/E[ix,1].mean())})
result={'at':stamp(),'postvalidation':True,'original_signal_passes':con['signal_passes'],'original_null_passes':con['null_passes'],'signal_gate_pass_counts':gatecounts,'changed_observation_diagnostics':changed,'leave_one_person':influence,
        'primary_P_accuracy_MSE_fractional_gain':float(1-P[:,0].mean()/E[:,0].mean()),'primary_P_RT_MSE_fractional_gain':float(1-P[:,1].mean()/E[:,1].mean()),
        'paper_cutoff_primary_passes':sens['scores']['primary_P_rule_passes'],'paper_cutoff_P':sens['scores']['models']['P'],'paper_cutoff_reference':sens['scores']['models'][ref],
        'interpretation':'Finite conditional resolution/influence checks, no source refitting, replacement holdout, repaired criterion, new primary acceptance, coverage or biological inference.'}
dump('CONTRARY.json',result);run_record('CONTRARY',15000000)
print(json.dumps({k:v for k,v in result.items() if k not in ['paper_cutoff_P','paper_cutoff_reference']},indent=2))
for k in ['paper_cutoff_P','paper_cutoff_reference']:print(k,{a:b for a,b in result[k].items() if a!='per_person_losses'})
