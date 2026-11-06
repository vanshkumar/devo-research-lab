"""Record-only final parse/link/freeze verification; no new science."""
import datetime
import hashlib
import json
from pathlib import Path
import re

out = Path(__file__).resolve().parent
frozen = json.loads((out/'FREEZE.json').read_text())
for name,h in frozen['sha256'].items():
    assert hashlib.sha256((out/name).read_bytes()).hexdigest()==h
for p in out.glob('*.json'):
    json.loads(p.read_text())
for name in ('RESULT.md','README.md','STATE.md','EXPOSURE.md','PROTOCOL.md'):
    for target in re.findall(r'\]\(([^)]+)\)',(out/name).read_text()):
        if '://' not in target:
            assert (out/target).exists(),(name,target)
message = (out/'COMMUNICATION_REPORT.md').read_text()
words = len(message.split())
assert words<=400,words
required = ['RESULT.md','STATE.md','README.md','PROTOCOL.md','FREEZE.json',
            'REFERENCE.json','STABILITY_RESULT.json','FINAL_VERIFICATION.json',
            'NATIVE_EXECUTION.json','SOURCE_MANIFEST.json','RESOURCES.json',
            'EXPOSURE.md','FAILURES.md','PROPOSED_LEARNINGS.md','SOURCE_LICENSE.txt',
            'COMMUNICATION_REPORT.md','reference.py','stability.py','freeze.py','verify_saved.py']
record = {'status':'FINAL_RECORDS_PARSED_LINKS_RESOLVED_FROZEN_BYTES_UNCHANGED',
          'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'terminal_report_word_count':words,'all_scientific_sessions_completed':True,
          'new_scientific_calculations':0,
          'sha256':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in required}}
(out/'CLOSEOUT_CHECK.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
