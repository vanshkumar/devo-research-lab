"""Record this study's scientific and source pins; no raw observations decoded."""
import datetime
import hashlib
import json
import pathlib

ROOT=pathlib.Path(__file__).resolve().parent
names=["PROTOCOL.md","AMENDMENT_1.md","analysis.py","BRIEF.md",
       "source/highsim-trials.zip","source/Stim-struct.xlsx",
       "source/exemplars_highsim.csv","source/highsim-trial-files.json"]
pins={name:{"sha256":hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),
            "bytes":(ROOT/name).stat().st_size} for name in names}
out={"frozen_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
     "pins":pins,"evaluation_response_interpretation":"NONE",
     "source_development":"ID20pilot/all672rows; sourceIDs2/4/6novelresponses parsed on failed preparation; no source fits yet.",
     "development_revision_used":1,"main_evaluation":"UNRUN"}
(ROOT/"FREEZE.json").write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
