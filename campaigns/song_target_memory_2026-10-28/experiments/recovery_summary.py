"""Roberts2017 group-summary contrasts; no reconstructed paired bird observations."""
from pathlib import Path
import json,itertools
BASE=Path(__file__).resolve().parents[1]
def main():
 d=json.loads((BASE/'audits/roberts/figure6_summaries.json').read_text())
 r={(x['task'],x['phase'],x['condition']):x['mean'] for x in d['records']}
 def value(task,phase,cond):return r[task,phase,cond]['value']
 def ratio(task,phase):
    po=r[task,phase,'post'];pr=r[task,phase,'pre']
    return {'ratio_of_group_means':po['value']/pr['value'],
      'extraction_only_interval':[po['extraction_interval'][0]/pr['extraction_interval'][1],po['extraction_interval'][1]/pr['extraction_interval'][0]]}
 ratios={task:{phase:ratio(task,phase) for phase in ['WN','return']} for task in ['timing','pitch']}
 gain=ratios['timing']['WN']['ratio_of_group_means']
 prediction=gain*value('timing','return','pre')
 predicted=[]
 for a,b,c in itertools.product(*[r['timing',phase,cond]['extraction_interval']
      for phase,cond in [('WN','post'),('WN','pre'),('return','pre')]]):predicted.append(a/b*c)
 result={
  'source':'Roberts2017 Fig6c/f, caption-defined mean markers,5birds per task;3birds shared across tasks',
  'status':'exploratory published-summary reconstruction, not independent biological replication, paired reanalysis, or untouched validation',
  'timing_mean_rates_ms_per_day':{phase:{co:value('timing',phase,co) for co in ['pre','post']} for phase in ['baseline','WN','return']},
  'pitch_mean_rates_Hz_per_day':{phase:{co:value('pitch',phase,co) for co in ['pre','post']} for phase in ['baseline','WN','return']},
  'post_pre_rate_ratios':ratios,
  'timing_recovery_attenuation_relative_to_learning':ratios['timing']['return']['ratio_of_group_means']/gain,
  'common_timing_gain_diagnostic':{'calibration':'ratio of post/pre WN group mean rates ONLY; source values already exposed, hence exploratory',
     'gain':gain,'predicted_post_return_rate_ms_per_day':prediction,
     'observed_post_return_rate_ms_per_day':value('timing','return','post'),
     'prediction_extraction_envelope':[min(predicted),max(predicted)],
     'observed_extraction_envelope':r['timing','return','post']['extraction_interval'],
     'residual_ms_per_day':value('timing','return','post')-prediction,
     'interpretation':'A uniform timing-gain reduction captures part, not all, of displayed recovery-rate reduction. No paired values/variance or fully specified slope estimator are available; cannot likelihood-rank mechanisms or statistically reject gain.'},
  'frozen_rate_model_not_fitted':'The planned exponential recovery fraction model requires per-bird displacement-normalized fractions and actual windows. Figure gives group mean slopes with incompletely specified slope/sign estimator. These rates cannot be substituted for recovery fractions.',
  'restrictions':[
    'A pure HVC-local restoring attractor whose timing plasticity is independent of the ablated projection predicts preserved recovery, contrary to the reported within-bird effect under lesion-specific causation and unchanged local state. Fixed intact-first order, no sham/retest cohort and baseline changes qualify that exclusion.',
    'A selective target-retrieval-only intervention is not established: temporal reinforcement learning also slowed in4/5birds; displayed baseline rate magnitude increased and timing changes slightly after lesion. Signed baseline drift is not established.',
    'Pitch preservation argues against a general inability to modify any song feature, but a timing-specific feedback/state-estimation/plasticity deficit remains.',
    'A motor-stored timing target read through the same feedback route remains compatible with an evaluative-reference account.',
    'Rate ratios are ratios of group means, not means of paired ratios; extraction intervals are not confidence intervals.']}
 (BASE/'outputs/recovery_summary.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
