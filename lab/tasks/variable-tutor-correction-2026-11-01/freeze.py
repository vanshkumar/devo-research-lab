"""Freeze this bounded study's artifacts before any evaluation generation."""
import hashlib
import json
from pathlib import Path
import time

root=Path(__file__).resolve().parent
target=root/"FREEZE.json"
if target.exists():
    raise SystemExit("Refusing to replace freeze")
if (root/"main").exists():
    raise SystemExit("Evaluation already exists")
names=["PROTOCOL.md","run.py","audit.py","analyze.py","freeze.py","DEVELOPMENT.md","DEVELOPMENT_REVISION.md","run_initial.py"]
pins={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names}
out=dict(frozen_at=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),sha256=pins,
         evaluation_seeds=list(range(2000,2064)),evaluations_generated=False,
         note="Code/protocol fixed before new whole-case evaluation. No later replacement.")
target.write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
