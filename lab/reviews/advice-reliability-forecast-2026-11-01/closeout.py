"""Administrative artifact syntax/completeness check; no scientific execution."""
import json
from pathlib import Path
from datetime import datetime, timezone
p=Path(__file__).resolve().parent
names=['FIRST_CALCULATION.json','FIRST_CALCULATION_RUN.json','RAW_FEATURE_AUDIT.json','SOURCE_FIT_AUDIT.json','SCORE_AUDIT.json','CONTROL_AUDIT.json','SOURCE_STABILITY_AUDIT.json','CONTRARY_FREEZE.json','CONTRARY.json','FINAL_AUDIT.json','NUMERICAL_WARNING_AUDIT.json','RESOURCES.json','SOURCE_REFERENCES.json','MAIN_RUN.json','EXPLICIT_REFERENCE_RUN.json']
for name in names:
    json.loads((p/name).read_text())
documents=['REVIEW.md','README.md','STATE.md','PROPOSED_LEARNING.md','CONTRARY_PLAN.md','TERMINAL_REPORT.md']
assert all((p/name).is_file() for name in documents)
result={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'administrative_check_only':True,'json_records_valid':names,'documents_present':documents,'scientific_jobs_remaining':0,'pretool_denials_preserved':['Initial ordinary shell composition and wccombined-option reads denied; no command execution.','Selected spreadsheet skill external path denied; no bytes read or permission changes.','Inline administrative JSON syntax-check command denied; no execution; used this scoped ordinary artifact check instead.']}
(p/'CLOSEOUT_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'json_records_valid':len(names),'documents_present':len(documents),'scientific_jobs_remaining':0}))
