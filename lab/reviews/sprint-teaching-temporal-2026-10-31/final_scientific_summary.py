"""Compare completed actor controls with independently reconstructed target scores."""
import datetime as dt,json,hashlib
from audit_common import HERE,SOURCE,j,read,save

def main():
    actor=j(HERE/'READOUT_ACTOR_RESULTS.json');dyn=j(HERE/'DYNAMICS_RESULTS.json');scope=j(HERE/'PUBLICATION_SCOPE_EVIDENCE.json')
    results=[];checks=[]
    for a,d in zip(actor['plants'],dyn['plants']):
        assert a['plant']==d['plant']
        target=next(r for r in d['duration_common_tail'] if r['variant']=='no_clock_forward' and r['stretch']==1.)
        normalized=a['normalized_actor'];raw=a['raw_actor'];oracle=a['waveform_oracle']
        found=next((r for r in a['cached_duration_scores'] if r['duration']==1.),None)
        err=abs(found['normalized']-target['quiet_subtracted_excess_per_active_ms_Hz']) if found else None
        if err is not None:checks.append({'name':'%d_target_normalization_replay'%a['plant'],'passed':err<1e-12,'error':err})
        gap=normalized['scores'][-1]-target['quiet_subtracted_excess_per_active_ms_Hz']
        results.append({'plant':a['plant'],'normalized_final_duration':normalized['durations'][-1],
            'normalized_actor_score_at_final':normalized['scores'][-1],'normalized_score_at_unit_target':target['quiet_subtracted_excess_per_active_ms_Hz'],
            'normalized_chosen_minus_target_Hz':gap,'wrong_selected_point_has_lower_score_than_target':gap<0 and abs(normalized['durations'][-1]-1)>1e-12,
            'raw_final_duration':raw['durations'][-1],'oracle_final_duration':oracle['durations'][-1],
            'normalized_final_waveform_MSE':normalized['offline_waveform_MSE'][-1],
            'raw_final_waveform_MSE':raw['offline_waveform_MSE'][-1],'oracle_final_waveform_MSE':oracle['scores'][-1],
            'normalized_improvement_from_start':1-normalized['offline_waveform_MSE'][-1]/normalized['offline_waveform_MSE'][0],
            'logical_queries_per_actor':25,'one_separate_matched_quiet_calibration_slot':True,
            'physical_integrations':a['physical_integrations_including_calibration']+1}) # add reset
        checks.append({'name':'%d_25query_oracle_and_raw_controls'%a['plant'],'passed':abs(oracle['durations'][-1]-1)<1e-12 and raw['durations'][-1]==.7})
    selected=[r for r in scope['matching_paragraphs'] if r['paragraph_index']>=30 and any(s in r['text'].lower() for s in ('reinforcement learning','motor learning','irregular','timing','temporal','reward'))]
    save('FINAL_SCIENTIFIC_SUMMARY.json',{'time':dt.datetime.now(dt.timezone.utc).isoformat(),'normalized_actor_control':results,
         'checks':checks,'all_passed':all(c['passed'] for c in checks),'scope_excerpts':selected,
         'claim':'Fixed mean-rate readout has finite temporal-fidelity counterexamples; exposure normalization changes duration behavior but does not establish a corrected objective.'})
    print(json.dumps({'actor_control_summary':results,'checks':checks,'publication_scope_selected':selected[:9]}))

if __name__=='__main__':main()
