import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',MKL_NUM_THREADS='1')
import numpy as np, json, time, resource, hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
d=dict(np.load(R/'development_arrays.npz',allow_pickle=True))
N=len(d['stim_name']);t=d['stim_start_time'];a=d['response_window_start_time'];b=d['response_window_stop_time'];r=d['response_time'];w=d['reward_time'];z=d['is_response'];finite=np.isfinite
checks={
'all_columns_same_rows':all(len(x)==N for x in d.values()),
'trial_index_consecutive':bool(np.array_equal(d['trial_index'],np.arange(N))),
'stimulus_onsets_strictly_increasing':bool(np.all(np.diff(t)>0)),
'start_stim_response_order':bool(np.all((d['start_time']<=t)&(t<a)&(a<b)&(b<=d['stop_time']))),
'noncatch_stimulus_offset_order':bool(np.all(d['stim_stop_time'][d['stim_name']!='catch']>t[d['stim_name']!='catch'])),
'windows_end_before_next_stimulus':bool(np.all(b[:-1]<t[1:])),
'response_flag_equals_finite_response_time':bool(np.array_equal(z,finite(r))),
'actual_responses_inside_window':bool(np.all((r[z]>=a[z])&(r[z]<b[z]))),
'task_registered_responses_inside_window':bool(np.all((d['task_control_response_time'][z]>=a[z])&(d['task_control_response_time'][z]<b[z]))),
'reward_flag_equals_finite_delivery':bool(np.array_equal(d['is_rewarded'],finite(w))),
'reward_flag_equals_contingent_or_noncontingent':bool(np.array_equal(d['is_rewarded'],d['is_contingent_reward']|d['is_noncontingent_reward'])),
'contingent_noncontingent_disjoint':bool(not np.any(d['is_contingent_reward']&d['is_noncontingent_reward'])),
'rewards_after_stimulus_and_before_trial_stop':bool(np.all((w[finite(w)]>=t[finite(w)])&(w[finite(w)]<d['stop_time'][finite(w)]))),
'past_rewards_before_next_trial_onset':bool(np.all(np.isnan(w[:-1])|(w[:-1]<t[1:]))),
'contingent_rewards_after_response':bool(np.all(w[d['is_contingent_reward']]>=r[d['is_contingent_reward']])),
'instruction_equals_scheduled_in_this_session':bool(np.array_equal(d['is_instruction'],d['is_reward_scheduled'])),
'no_opto_or_repeat':bool(not np.any(d['is_opto']|d['is_repeat']))}
encounters=[]
for block in np.unique(d['block_index']):
    ix=np.flatnonzero(d['block_index']==block); instr=ix[d['is_instruction'][ix]]
    if block==0:continue
    new=d['rewarded_modality'][ix[0]];old='vis+' if new=='aud' else 'aud+'
    choices=ix[(d['stim_name'][ix]==old)&~d['is_instruction'][ix]]
    i=int(choices[0])
    before=ix[ix<i]
    encounters.append(dict(block=int(block),trial=i,stimulus=old,response=bool(z[i]),instruction_count_before=int(np.sum(d['is_instruction'][before])),prior_same_stimulus_trial=int(np.flatnonzero(d['stim_name'][:i]==old)[-1]),other_target_delivered_rewards_since_switch=int(np.sum(finite(w[before])&(d['stim_name'][before]!=old))),rewarded_modality_selection_only=str(new)))
summary=dict(created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),kind='Actual complete development trial join and narrow source-defined chronology certification',rows=N,columns=list(d),checks=checks,all_checks_pass=all(checks.values()),source_subject_session=json.loads((R/'DEVELOPMENT_SCALARS.json').read_bytes()),data_description=json.loads((R/'data_description.json').read_bytes()),time_units='NWB seconds relative to session reference; hardware-corrected export, no independent acquisition clock or water-sensor replay',reward_counts={k:int(d[k].sum()) for k in ['is_rewarded','is_contingent_reward','is_noncontingent_reward','is_reward_scheduled','is_instruction']},scheduled_replaced_by_contingent=int(np.sum(d['is_reward_scheduled']&d['is_contingent_reward'])),response_start_minus_stimulus_range_seconds=[float(np.min(a-t)),float(np.max(a-t))],response_window_duration_range_seconds=[float(np.min(b-a)),float(np.max(b-a))],noncontingent_delivery_minus_window_stop_seconds=(w[d['is_noncontingent_reward']]-b[d['is_noncontingent_reward']]).tolist(),contingent_delivery_minus_response_range_seconds=[float(np.min((w-r)[d['is_contingent_reward']])),float(np.max((w-r)[d['is_contingent_reward']]))],first_encounters=encounters,first_encounter_count=len(encounters),codec=json.loads((R/'CODEC_CHECK.json').read_bytes()),historical_bug='Development date 2024-10-22 is after both documented fixes; finite response/registered response windows checked directly. 668755_2023-08-31 predates fixes and is excluded outcome-blind from planned evaluation.',provenance_limit='Source-defined export links exact commit 467df765931d707cb6cfbd5a0b74d381ce288acb. This is an archive assertion, not independent proof of hardware deployment. Sufficient for conditional exported binary-response forecasts, not hardware or causal timing claims.',unrun=['evaluation acquisition','scientific freeze','fitting','controls','forecasts','scores','independent review'],rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(R/'FIRST_DATA_CHECK.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
