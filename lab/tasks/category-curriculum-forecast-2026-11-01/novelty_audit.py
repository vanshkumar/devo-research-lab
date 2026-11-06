"""Audit the already saved input census; no response fields are present."""
import datetime
import json
import pathlib

ROOT=pathlib.Path(__file__).resolve().parent
census=json.loads((ROOT/"METADATA_CHECK.json").read_text())
out=[]
for person in census["people"]:
    h=person["halves"][0]
    tr=set(h["training_items"]); te=set(h["test_items"])
    intended_new={s for s in te if int(s[1:3])>=9}
    if person["row_count"] == 672:
        out.append({"id":person["id"],"training_item_count":len(tr),
            "test_item_count":len(te),"intended_new_count":len(intended_new),
            "intended_new_seen_in_training":sorted(intended_new & tr),
            "unseen_intended_old":sorted({s for s in te-tr if int(s[1:3])<9}),
            "exact_new_count":len(te-tr),"categories":h["categories"]})
result={"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"people":out,
    "failure":"First analysis.py prepare assertion len(seen)==24 and len(exact_new)==24 failed before fitting. No evaluation responses interpreted.",
    "response_exposure":"None added: saved census contains stimulus names only."}
(ROOT/"NOVELTY_AUDIT.json").write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
