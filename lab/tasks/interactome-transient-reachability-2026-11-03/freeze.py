"""Write one immutable task-local scientific declaration receipt."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

root=Path(__file__).resolve().parent
target=root/'FREEZE.json'
assert not target.exists(),'Do not overwrite the scientific freeze'
record={'frozen_at_utc':datetime.now(timezone.utc).isoformat(),
        'evaluation_generated_before_freeze':False,
        'substantive_protocol_revisions':0,
        'sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest()
                  for name in ['PROTOCOL.md','CONFIG.json','MODEL_REFERENCE.json']}}
target.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
