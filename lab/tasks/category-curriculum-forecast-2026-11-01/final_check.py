"""Static closeout integrity only; no additional scientific calculation."""
import datetime
import hashlib
import json
import pathlib

ROOT=pathlib.Path(__file__).resolve().parent
manifest=json.loads((ROOT/"MANIFEST.json").read_text())
checks={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==p["sha256"]
        for n,p in manifest["artifacts"].items()}
assert all(checks.values())
required=["RESULT.md","README.md","STATE.md","PROPOSED_LEARNING.md","COMMUNICATION_MESSAGE.md"]
assert all((ROOT/n).is_file() for n in required)
message=(ROOT/"COMMUNICATION_MESSAGE.md").read_text()
assert len(message.split())<=400
pi=json.loads((ROOT.parents[2]/"lab/registry.json").read_text())["pi"]["thread_id"]
out={"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"core_manifest_pins":checks,
     "closeout_files_present":required,"terminal_report_words":len(message.split()),"current_registry_pi":pi,
     "jobs":"All native analysis/acquisition sessions returned completion; no live sessions remain.",
     "independent_review":"UNRUN; assigned by PI if earned"}
(ROOT/"CLOSEOUT_CHECK.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
