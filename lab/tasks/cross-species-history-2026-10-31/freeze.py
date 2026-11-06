"""Timestamp and pin the task's finite protocol and code before main scoring."""
from pathlib import Path
import json,hashlib,datetime
OUT=Path(__file__).resolve().parent
files=['PLAN.md','analysis.py','input_support.py','build_inputs.py','certify.py','ALLOWED_MANIFEST.json','SUPPORT.json','FIRST_SUPPORT.json']
pins={x:hashlib.sha256((OUT/x).read_bytes()).hexdigest() for x in files}
p=OUT/'FREEZE.json'
assert not p.exists(),'Preserve original freeze'
p.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='pre-new-prediction-score; consumed development',sha256=pins,
                            amendment='Initial input diagnostic repNum_equals_1 was mislabeled no_repeat; renamed in code before freeze. It is not a nonrepeat claim. Unfrozen INPUT_SUPPORT.json contains that earlier label; no selection/score uses it.'),indent=2)+'\n')
print(p.read_text())
