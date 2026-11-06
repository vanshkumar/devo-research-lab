from pathlib import Path
import json,csv,numpy as np
BASE=Path(__file__).resolve().parents[1];P=BASE/'outputs'/'hvc'

def select(mode,period,eta=1,tau=1):
    return [json.loads(f.read_text()) for f in sorted(P.glob(f'{mode}_seed*_period{period}_eta{eta:g}_tau{tau:g}_steps*.json'))
            if json.loads(f.read_text())['trains']==7200]

def summary(rows):
    probes=[v for r in rows for v in r['frozen_probe_ms']]
    clean=[r['clean_probe_ms'] for r in rows]
    finite=[x for x in probes if x is not None]
    return {'networks':len(rows),'clean_probe_ms':clean,
            'clean_right_censored_count':sum(x is None for x in clean),
            'right_censor_threshold_ms':1990,
            'probe_count':len(probes),'probe_right_censored_count':sum(x is None for x in probes),
            'finite_probe_range_ms':[min(finite),max(finite)] if finite else None,
            'network_finite_probe_medians_ms':[float(np.median([x for x in r['frozen_probe_ms'] if x is not None]))
                if any(x is not None for x in r['frozen_probe_ms']) else None for r in rows],
            'warning':'finite-only summaries are conditional, not unbiased duration estimates; ten probes nested within network'}

def main():
    exe=json.loads((P/'suite_execution.json').read_text());assert len(exe)==40 and all(x['returncode']==0 for x in exe)
    source={str(p):summary(select('source',p)) for p in [0,10]}
    matched={str(p):summary(select('matched',p)) for p in [10,20,40]}
    assert all(v['networks']==6 for v in list(source.values())+list(matched.values()))
    sensitivity=[]
    for eta,tau in [(0,1),(.5,1),(2,1),(1,.75),(1,1.25)]:
      sensitivity.append({'eta_scale':eta,'tau_scale':tau,
          'single':summary(select('source',0,eta,tau)),'rhythmic':summary(select('source',10,eta,tau))})
    src=select('source',10);single=select('source',0)
    result={'source_protocol':source,'matched_train_schedule':matched,'sensitivity':sensitivity,
       'source_single_longer_than_rhythmic_clean_networks':sum(a['clean_probe_ms']>b['clean_probe_ms'] for a,b in zip(single,src)),
       'source_rhythmic_exact_100ms_networks':sum(x['clean_probe_ms']==100 for x in src),
       'matched_100ms_exact_100ms_networks':sum(x['clean_probe_ms']==100 for x in select('matched',10)),
       'source_trial_count':7200,'source_training_steps':360000,'matched_training_steps':1224220,
       'source_mean_time_between_trials_ms':float(np.mean(np.diff(__import__('hvc_model').source_times()))*10),
       'matched_mean_time_between_trials_ms':(1224220-210)/(7200-1)*10,
       'exposure_time_warning':'Matched schedule fixes all comparison groups but increases total simulated time and opportunities for spontaneous plasticity. Failure cannot be attributed only to onset period. Source schedule itself is compressed relative to90min/300-370event biological sessions.',
       'elapsed_sum_child_process_seconds':sum(x['elapsed_seconds'] for x in exe),
       'main_constraint':'A fixed published model can generate protocol-sensitive timing, but an onset-only mapping ignores pulse width and fixed-parameter timing transfer is not robust to changed between-train spacing. This does not refute motor-scaffold architectures or establish a biological target comparator.'}
    (P/'SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
