"""One-time timestamp/pins, does not generate new circuit outcomes."""
from pathlib import Path
import datetime
import hashlib
import json
p=Path(__file__).resolve().parent
target=p/'CONTRARY_FREEZE.json'
assert not target.exists(),'Refuse overwrite of prior freeze'
names=['CONTRARY_PLAN.md','contrary.py','independent_model.py','REFERENCE.json']
receipt={'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'contrary_outcomes_generated_before_freeze':False,
         'sha256':{n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names}}
target.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
