"""Save compact derived evidence and final manual resource accounting; no new fit."""
from model import *
from importlib import metadata
import sys

f=load('FREEZE.json');assert freeze_pins(list(f['files']))==f['files']
assert freeze_pins(['PREDICTIONS.json'])==load('PREDICTION_PIN.json')['sha256']
s=load('SCORES.json');p=load('PREDICTIONS.json');src=load('SOURCE_FIT.json');c=load('CONTRARY.json');raw=load('RAW_AND_PREDICTION_AUDIT.json')
obs=np.array(s['target_values']);bias={}
for k,v in p['predictions'].items():
    dif=np.sum((np.array(v)-obs)*W[None,:,None],axis=1)
    bias[k]={'weighted_accuracy_mean_bias':float(dif[:,0].mean()),'weighted_RT_mean_bias_s':float(dif[:,1].mean()),'per_person_weighted_bias':dif}
versions={name:metadata.version(name) for name in ['numpy','pandas','scipy','rdata','xarray','typing_extensions']}
(ROOT/'requirements.txt').write_text('\n'.join(k+'=='+v for k,v in versions.items())+'\n')
out={'at':stamp(),'primary_passes':s['primary_P_rule_passes'],'models':{k:{a:b for a,b in v.items() if a!='per_person_losses'} for k,v in s['models'].items()},'biases':bias,
     'source_ids':src['source_ids'],'evaluation_ids':p['ids'],'source_nominal_firstpair_rows':9*192,'evaluation_nominal_baseline_rows':8*96,'evaluation_nominal_target_rows':8*96,'evaluation_target_valid_rows':sum(x['n_target_valid'] for x in raw['rows']),
     'all_release_acquired_decoded_rows':31522,'scientifically_used_firstpair_allpeople_raw_rows':17*192,'person1_later_rows_also_summarized':18*96,'source_mapping_P_factors':np.exp(src['P_mapping']),'source_mapping_Q_factors':np.exp(src['Q_mapping']),
     'original_controls':{'signal_passes':c['original_signal_passes'],'null_passes':c['original_null_passes']},'control_gate_pass_counts':c['signal_gate_pass_counts'],'changed_observation_diagnostics':c['changed_observation_diagnostics'],
     'leave_one_person_joint_gain_range':[min(x['joint_P_fractional_gain'] for x in c['leave_one_person']),max(x['joint_P_fractional_gain'] for x in c['leave_one_person'])],
     'versions':versions,'python':sys.version,'freeze_order':[f['at'],p['at'],s['at']],'historical_nonaccess_proven':False,'author_only':True}
dump('DERIVED_SUMMARY.json',out)
charges=[('orientation_dependencies_first_check_and_failed_imports',50000000),('failed_develop_block_factor',20000000),('failed_develop_additive_map',40000000),('successful_develop',40000000),('source_numerical_audit',15000000),('freeze_hashes',5000000),('predict',30000000),('score',30000000),('held_numerical_audit',15000000),('raw_reconstruction_and_cutoff',35000000),('original_controls',20000000),('contrary_diagnostic',15000000),('final_summary_hash_versions_and_reporting_allowance',15000000)]
resource_files=list(ROOT.glob('*_RESOURCE.json'));peaks=[load(x.name)['peak_rss_bytes_macos'] for x in resource_files]+[94961664,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss]
res=load('RESOURCES.json');res.update(as_of=stamp(),public_operations_final=32,ingress_charge_bytes_final=12000000,read_decode_hash_charge_bytes_final=sum(v for k,v in charges),read_charges=[{'stage':k,'charged_bytes':v} for k,v in charges],largest_measured_local_peak_rss_bytes=max(peaks),jobs_active=0,science_status='author complete; independent review UNRUN',measured_cap_breach=False,OS_wide_cap_compliance_certified=False)
dump('RESOURCES.json',res)
print('versions',versions,'target valid',out['evaluation_target_valid_rows'],'resources',res['read_decode_hash_charge_bytes_final'],max(peaks))
print('biases',{k:{a:b for a,b in v.items() if a!='per_person_weighted_bias'} for k,v in bias.items()})
print('freeze/prediction hashes PASS; no jobs')
