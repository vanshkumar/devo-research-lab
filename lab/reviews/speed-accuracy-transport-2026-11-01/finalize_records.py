"""Final saved-output summary, manual resource record and hashes; no model run."""
from pathlib import Path
import json, hashlib, datetime, resource

HERE=Path(__file__).resolve().parent
def load(name): return json.loads((HERE/name).read_text())
def dump(name,obj): (HERE/name).write_text(json.dumps(obj,indent=2)+'\n')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
first=load('FIRST_CALCULATION.json');rec=load('RECONSTRUCTION.json')
main=load('RECONSTRUCTED_SCORES.json');contrary=load('CONTRARY.json');checks=load('FINAL_CHECKS.json')
control=load('CONTROL_AUDIT.json')
reference=main['models'][main['reference']]
summary={'at_utc':now,'original_rule_passes':main['primary_P_rule_passes'],
    'original_accuracy_MSE_gain':1-main['models']['P']['accuracy_mse']/reference['accuracy_mse'],
    'original_RT_MSE_gain':1-main['models']['P']['rt_mean_mse_s2']/reference['rt_mean_mse_s2'],
    'source_reference':main['reference'],
    'models':{name:{key:m[key] for key in ['accuracy_mse','rt_mean_mse_s2','joint_loss','accuracy_MAE','rt_mean_MAE_s']} for name,m in main['models'].items()},
    'affine_model':{key:contrary['affine']['models']['P'][key] for key in ['accuracy_mse','rt_mean_mse_s2','joint_loss','accuracy_MAE','rt_mean_MAE_s']},
    'affine_rule_passes':contrary['affine']['primary_P_rule_passes'],
    'affine_source_NLL_improvement':contrary['source_objective_improvement192'],
    'affine_source_gain':contrary['factors']['t0_gain'],
    'affine_common_target_t0_s':.03+contrary['factors']['t0_intercept_above_minimum_source_floor_s'],
    'max_forecast_discrepancy':max(rec['forecast_discrepancies_384_scalars'].values()),
    'original_control_signal_null_passes':[control['original_signal_passes'],control['original_null_passes']],
    'recommendation':'Bank independent reconstruction and finite control limitation; close this consumed-release recipe. One source-only affine map also fails. Full original optimizer/source uncertainty/pipeline power and coverage remain UNRUN.'}
dump('DERIVED_SUMMARY.json',summary)
commands=[
 {'script':'first_calculation.py','exit_code':0,'actual_output_file':'FIRST_CALCULATION.json','completed_at_utc':first['at_utc'],'key_output':'RData31522rows/17people;person10block2valid96/correct95/meanRT.5747604166666667s;actual pins match.'},
 {'script':'reconstruct.py','exit_code':0,'actual_output_files':['RECONSTRUCTION.json','RECONSTRUCTED_FORECASTS.json','RECONSTRUCTED_SCORES.json','NUMERICAL_AUDIT.json','CONTROL_AUDIT.json','PAPER_CUTOFF_AUDIT.json'],'completed_at_utc':control['at_utc'],'key_output':'384forecastmaxdifference5.995204332975845e-15;757validtargets;RIDGEreference;PjointFAIL;signal18/null2;noise-removal100/18/100.'},
 {'script':'contrary.py','exit_code':0,'actual_output_files':['CONTRARY_SOURCE_FIT.json','CONTRARY.json'],'completed_at_utc':contrary['at_utc'],'key_output':'BothSLSQPstartsconvergedfeasible;gain0;t0.1568150466452355;sourceNLLimprovement9.540427162776155;RTMAE.2266356073895331;jointFAIL.'},
 {'script':'final_checks.py','exit_code':0,'actual_output_file':'FINAL_CHECKS.json','completed_at_utc':checks['at_utc'],'key_output':'Allnominalcounts/order/censor/baselineboxes/additiveinfeasibility/influence/cutoffsagree;currentPIverified.'}
]
for entry in commands:
 entry['native_command']='OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /Users/vanshkumar/Documents/repos/devo-research-lab/.venv/bin/python '+str(HERE/entry['script'])
dump('EXECUTION_RECORD.json',{'at_utc':now,'commands':commands,
 'pretool_rejections':[{'action':'Ordinary rootSTATE nonnumeric sed range','effect':'Rejected before execution; used brief/authorSTATE/registry context; no full-history retry.'},
                       {'action':'Inline saved-JSON summary heredoc','effect':'Rejected before execution; summary now uses this owned script. No scientific model/cap change.'}],
 'jobs_active':0,'note':'Native tool results returned exit0 for each listed executed command; saved output is direct evidence. No failed scientific execution passes.'})
charges=[{'stage':'independent_first_raw_calculation_imports_decode_hash','charged_bytes':30000000},
 {'stage':'independent_full_reconstruction_analytical_controls_pins','charged_bytes':100000000},
 {'stage':'one_predeclared_affine_map_fit_forecast','charged_bytes':70000000},
 {'stage':'additional_final_raw_checks_source_code_context_import_uncertainty_summary_hash_reporting_allowance','charged_bytes':80000000}]
largest=max(first['largest_measured_process_rss_bytes_macos'],rec['largest_measured_process_rss_bytes_macos'],
            contrary['largest_measured_process_rss_bytes_macos'],checks['largest_measured_process_rss_bytes_macos'],
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
resources={'at_utc':now,'reviewer_thread_id':'01a1963e-8b48-7421-8169-1bf31d358517',
 'fixed_START_utc':'2026-11-01T08:35:00Z','first_actual_calculation_utc':first['at_utc'],
 'first_calculation_deadline_utc':'2026-11-01T08:47:00Z','hard_STOP_utc':'2026-11-01T09:20:00Z',
 'scientific_execution':'complete; no additional model runs authorized or pending','jobs_active':0,
 'public_operations':0,'public_operations_cap':0,'new_ingress_bytes':0,'new_ingress_cap_bytes':0,
 'scientific_read_decode_hash_charges':charges,'scientific_read_decode_hash_charge_bytes':sum(c['charged_bytes'] for c in charges),
 'scientific_read_decode_hash_cap_bytes':350000000,
 'charge_note':'Separate from author330000000bytes. Manual conservative allowances; expanded final allowance from planned30MBto80MB within unchanged350MBcap covers extra final raw denominator/bounds check and import/read/report uncertainty. No automatic metering/new infrastructure.',
 'largest_measured_process_RSS_bytes_macos':largest,'RSS_cap_bytes':800000000,
 'scientific_processes_max_concurrent':1,'numerical_threads':1,
 'thread_environment':{'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'},
 'measured_cap_breach':False,'physical_IO_or_OS_wide_compliance_certified':False,
 'unknown':['physical IO and file-cache behavior','actual total logical import/decoder reads versus conservative charges','toolhost memory','unmeasured ordinary-read/wrapper peaks'],
 'all_empirical_reads':'Same cached original release only. Full31522rows librarydecoded again; firstpairs selected for response summaries/fitting, metadata allblocks exposed. Original full-RAM prefreeze derived/auxiliary exposure preserved; no pristine new holdout.',
 'protected_payloads_opened':False,'older_scientific_payloads_opened':False,'source_acquisition_refetch':False,
 'usage_for_assignment':'PIprovidedmanualget_usage_limits08:33:39.816Z38%remaining;dailyceilingssuspended/20%reserve. No spending/reset/credits.',
 'heartbeat':'SameACTIVE PI heartbeat unchanged. Assignment completion is not overall lab shutdown.'}
assert resources['scientific_read_decode_hash_charge_bytes']<=350000000 and largest<800000000
dump('RESOURCES.json',resources)
files=['first_calculation.py','reconstruct.py','contrary.py','final_checks.py','finalize_records.py',
 'CONTRARY_PLAN.md','requirements.txt','REVIEW.md','README.md','SOURCE_MANIFEST.md','PROPOSED_LEARNING.md',
 'FIRST_CALCULATION.json','RECONSTRUCTION.json','RECONSTRUCTED_FORECASTS.json','RECONSTRUCTED_SCORES.json',
 'PAPER_CUTOFF_AUDIT.json','NUMERICAL_AUDIT.json','CONTROL_AUDIT.json','CONTRARY_SOURCE_FIT.json',
 'CONTRARY.json','FINAL_CHECKS.json','DERIVED_SUMMARY.json','EXECUTION_RECORD.json','RESOURCES.json']
dump('REVIEW_PINS.json',{'at_utc':now,'sha256':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in files},
 'note':'Pins attest current bytes only; not historical access. STATE/report delivery status remains mutable and excluded.'})
registry=json.loads((HERE.parents[1]/'registry.json').read_text())
print(json.dumps({'saved_at_utc':now,'current_PI':registry['pi']['thread_id'],'resources':{'charged_bytes':resources['scientific_read_decode_hash_charge_bytes'],'largest_measured_RSS':largest,'jobs':0},'summary':summary},indent=2))
