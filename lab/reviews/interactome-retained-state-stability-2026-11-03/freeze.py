import datetime, hashlib, json
from pathlib import Path
out = Path(__file__).resolve().parent
files = ("PROTOCOL.md", "model.py", "reconstruct.py", "contrary.py", "INPUT_INSPECTION.json", "inspect_inputs.py")
record = dict(frozen_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), initial_native_utc="2026-11-03T07:45:29Z",
              contrary_outcomes_generated=False, scientific_revisions=0,
              sha256={name: hashlib.sha256((out/name).read_bytes()).hexdigest() for name in files})
assert not (out / "FREEZE.json").exists()
(out / "FREEZE.json").write_text(json.dumps(record, indent=2)+"\n")
print(record)
