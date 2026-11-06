"""Read only cached, allowed source objects; verify pins and save inspectable text."""
import datetime, hashlib, json, pathlib, re, resource
from xml.etree import ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "tasks/surprise-history-forecast-2026-11-01"

def main():
    freeze = json.loads((SOURCE / "FREEZE.json").read_text())
    pins = []
    read_bytes = 0
    for name, expected in freeze["pins"].items():
        payload = (SOURCE / name).read_bytes()
        read_bytes += len(payload)
        digest = hashlib.sha256(payload).hexdigest()
        pins.append({"file": name, "bytes": len(payload), "sha256": digest, "matches": digest == expected})
    assert all(p["matches"] for p in pins)
    manifest = json.loads((SOURCE / "PREDICTION_MANIFEST.json").read_text())
    prediction_pins = []
    for name, field in (("predictions.npz", "prediction_sha256"), ("evaluation_truth.npz", "truth_sha256"), ("evaluation_features.npz", "feature_sha256")):
        payload = (SOURCE / name).read_bytes()
        read_bytes += len(payload)
        digest = hashlib.sha256(payload).hexdigest()
        prediction_pins.append({"file": name, "bytes": len(payload), "sha256": digest, "matches": digest == manifest[field]})
    assert all(p["matches"] for p in prediction_pins)
    validation = json.loads((SOURCE / "SOURCE_VALIDATION.json").read_text())
    trees = {}
    for filename in ("code_tree.source", "task_tree.source"):
        payload = (SOURCE / filename).read_bytes()
        read_bytes += len(payload)
        tree = json.loads(payload)
        trees[tree["sha"]] = {item["path"]: item["sha"] for item in tree["tree"]}
    blobs = []
    for record in validation["source_blob_checks"]:
        payload = (SOURCE / (record["local"] + ".source")).read_bytes()
        read_bytes += len(payload)
        actual = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\x00" + payload).hexdigest()
        expected = trees[record["tree"]][record["path"]]
        assert actual == expected == record["git_blob"]
        blobs.append({"file": record["local"] + ".source", "path": record["path"], "git_blob": actual, "tree": record["tree"], "matches_saved_tree": True})
    score = json.loads((SOURCE / "SCORES.json").read_text())
    order = [freeze["frozen_at"], manifest["saved_before_scoring_at"], score["scored_at"]]
    assert order == sorted(order)
    excerpts = []
    for filename in ("task_generate.source", "source_model.source"):
        payload = (SOURCE / filename).read_bytes()
        read_bytes += len(payload)
        excerpts.append("## " + filename + "\n" + payload.decode("utf-8", errors="replace"))
    for filename, pattern in (("task_main.source", r"timestamp|feedback|Feedback|allASS|actRew|hit|outcome|offset|shield|Shield"),
                              ("task_config.source", r"safe|hazard|Safe|\.25|driftConc|sigma|TAC|Main\("),
                              ("source_analysis.source", r"hazard|Haz|post.?[Oo]dd|oddBall.*==|oddBall.*~=|getTrialVarsFromPEs|empirical")):
        payload = (SOURCE / filename).read_bytes()
        read_bytes += len(payload)
        lines = payload.decode("utf-8", errors="replace").splitlines()
        selected = set()
        for i, line in enumerate(lines):
            if re.search(pattern, line):
                selected.update(range(max(0, i - 2), min(len(lines), i + 3)))
        excerpts.append("## " + filename + "\n" + "\n".join(f"{i+1}: {lines[i]}" for i in sorted(selected)))
    article = (SOURCE / "article.source").read_bytes()
    read_bytes += len(article)
    xml = ET.fromstring(article)
    paragraphs = []
    for p in xml.iter("p"):
        content = "".join(p.itertext())
        if re.search(r"hazard|three trials|shield|post-oddball|following oddball|likelihood", content, re.I):
            paragraphs.append(content)
    excerpts.append("## Pinned article selected paragraphs\n" + "\n\n".join(paragraphs))
    (HERE / "SOURCE_EXCERPTS.md").write_text("\n\n".join(excerpts) + "\n")
    out = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "freeze_pins": pins,
        "prediction_pins": prediction_pins, "source_git_blobs": blobs, "saved_chronology": order,
        "recorded_bytes_read": read_bytes, "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "scope": "Matches current cached bytes to saved pins/tree entries. Saved timestamps and source text support chronology; hashes alone do not prove historical execution or that individual evaluation values were unread. No network or original MATLAB execution."}
    (HERE / "PIN_AUDIT.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"freeze_pins": len(pins), "prediction_pins": len(prediction_pins), "source_blobs": len(blobs), "saved_chronology": order, "recorded_bytes_read": read_bytes, "peak_rss_bytes": out["peak_rss_bytes"]}, indent=2))

if __name__ == "__main__":
    main()
