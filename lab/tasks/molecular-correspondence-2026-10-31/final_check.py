"""Artifact/link/JSON checks, charged inside the150MB documentation/output reserve."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import time

P=Path(__file__).resolve().parent
PROTOCOL_SHA="70b50038972587e60173c4ac7d0ede63e51d079be7e6c9a0998dd9b1e68c86b4"
assert hashlib.sha256((P/"PROTOCOL.md").read_bytes()).hexdigest()==PROTOCOL_SHA
checks=[]
for p in sorted(P.glob("*.md")):
    for target in re.findall(r"\]\(([^)]+)\)",p.read_text()):
        if "://" not in target and not target.startswith("#"):
            assert (p.parent/target.split("#")[0]).exists(),(p.name,target)
            checks.append([p.name,target])
json_files=list(P.glob("*.json"))+list((P/"sources").glob("*.json"))
for p in json_files:
    json.loads(p.read_text())
for p in P.glob("*.py"):
    ast.parse(p.read_text())
account=json.loads((P/"ACCOUNTING.json").read_text())
assert account["public_requests"]==20
assert account["charged_read_bytes"]==191451239
assert account["new_ingress_bytes"]==20165421
stable=[]
for p in sorted(list(P.glob("*"))+list((P/"sources").glob("*"))):
    if p.is_file() and p.name not in ["STATE.md","ACCOUNTING.json","ARTIFACT_MANIFEST.json","FINAL_CHECK.json"]:
        b=p.read_bytes()
        stable.append({"path":str(p.relative_to(P)),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
(P/"ARTIFACT_MANIFEST.json").write_text(json.dumps({"note":"Stable artifact snapshot; mutable STATE/ACCOUNTING/delivery records are excluded. Hashing/output checks are within the existing150MB reserve.","files":stable},indent=2)+"\n")
out={"completed_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"protocol_unchanged":True,"local_links_checked":len(checks),"json_files_parsed":len(json_files),"python_syntax_checked":len(list(P.glob("*.py"))),"stable_artifact_pins":len(stable),"scientific_jobs":0,"resources":{k:account[k] for k in ["public_requests","new_ingress_bytes","charged_read_bytes"]},"python_version":sys.version}
(P/"FINAL_CHECK.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
