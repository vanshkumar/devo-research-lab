"""Read only this task's saved output; write its reproduction/resource audit."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import platform
import resource

ROOT=Path(__file__).resolve().parent
names=['first_calculation.py','FIRST_CALCULATION.json','calibration_frontier.py',
       'CALIBRATION_FRONTIER.json','CALIBRATION_GATE.md','RIVALS_AND_ASSUMPTIONS.md','SOURCES.md']
files={name:(ROOT/name).read_bytes() for name in names}
first=json.loads(files['FIRST_CALCULATION.json'])
front=json.loads(files['CALIBRATION_FRONTIER.json'])
assert first['theta_analytic_and_scalar_deg']==.2
assert all(v==0 for v in first['max_exact_residual_deg'].values())
assert front['exact_max_residual_deg']==0
assert [w['changed_transition_contribution_deg'] for w in front['signed_witnesses']]==[-.2,.2]
assert [w['report_as_true_estimate_deg'] for w in front['signed_witnesses']]==[-.1,.1]
assert hashlib.sha256(files['calibration_frontier.py']).hexdigest()==front['resources']['source_hash_sha256']
assert front['synthetic_reference']['five_probe_average_multiplier']==.941773162
assert front['checks']['full_feasible_recovery_or_coverage'].startswith('UNRUN')
q=front['continuous_2afc_quantized_branch_heterogeneous_noise_check']
assert q['shared_quantizer_mismatches']==q['shared_2afc_response_mismatches']==0
assert q['max_float_discrepancy']<1e-13
cost={'factorial_episode_conditions':2*2*3*2,'post_precursor_reaches_per_episode':1+5,
      'reaches_per_single_person_factorial_repetition_excluding_precursor':2*2*3*2*6,
      'hand_reports_if_one_per_report_branch_episode':2*2*3,
      'conditional_extra_hand_report_seconds':2*2*3*.842,
      'additional_matched_no_report_wait_seconds':2*2*3*.842,
      'people_required_for_mechanistic_separation':'no finite N for exhibited exact pair',
      'other_times_counts':'precursor/reacquisition/washout/calibration/robot replay/goal and 2AFC times unearned'}
audit={'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'saved_output_checks':'PASS; no science rerun',
       'python':platform.python_version(),'platform':platform.platform(),
       'pins':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in files.items()},
       'explicit_bytes_read_by_this_audit':sum(len(data) for data in files.values()),
       'peak_rss_this_audit_native_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'conditional_collection_arithmetic':cost,
       'scope':'Only seven task-owned text/JSON/code files read; no empirical/raw/protected inputs'}
(ROOT/'FINAL_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({k:v for k,v in audit.items() if k!='pins'},indent=2))

if __name__=='__main__':
    pass
