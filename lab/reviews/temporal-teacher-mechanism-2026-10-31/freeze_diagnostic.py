from pathlib import Path
import json,hashlib,datetime
p=Path(__file__).resolve().parent
assert not (p/'DIAGNOSTIC_FREEZE.json').exists(),'Preserve the original freeze'
names=['DIAGNOSTIC_PROTOCOL.md','review_core.py','crossed_diagnostic.py']
d={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'Before first crossed response execution; initial predetermined source pair already reconstructed',
   'sha256':{n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names}}
(p/'DIAGNOSTIC_FREEZE.json').write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps(d,indent=2))
