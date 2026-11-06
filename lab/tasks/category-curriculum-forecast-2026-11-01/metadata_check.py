"""Input-only census of newly acquired high-similarity records."""
import collections
import hashlib
import json
import pathlib
import resource
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
out = {"geometry_csv_text": (ROOT / "source/exemplars_highsim.csv").read_text(),
       "people": []}
listing = json.loads((ROOT / "source/highsim-trial-files.json").read_text())
pins = {x["attributes"]["name"]: x["attributes"]["extra"]["hashes"]["sha256"]
        for x in listing["data"]}
with zipfile.ZipFile(ROOT / "source/highsim-trials.zip") as z:
    for name in sorted(z.namelist(), key=lambda s: int(s[:-4])):
        b = z.read(name)
        lines = b.decode().splitlines()
        rows = [s.split() for s in lines if len(s.split()) == 12 and
                s.split()[0] == name[:-4] and s.split()[3].isdigit()]
        groups = collections.defaultdict(list)
        for r in rows:
            groups[int(r[4])].append(r)
        blocks = []
        for bs, tb in [([1,2,3,4],5),([6,7,8,9],10)]:
            tr = [r for bb in bs for r in groups[bb]]
            te = groups[tb]
            blocks.append({"train_rows": len(tr), "test_rows": len(te),
                "categories": sorted(set(r[9][0] for r in tr)),
                "category_switches": sum(a[9][0] != b[9][0] for a,b in zip(tr,tr[1:])),
                "training_items": sorted(set(r[9] for r in tr)),
                "test_items": sorted(set(r[9] for r in te))})
        out["people"].append({"id": int(name[:-4]), "header": lines[:3],
            "sha256": hashlib.sha256(b).hexdigest(),
            "pin_matches": hashlib.sha256(b).hexdigest() == pins[name],
            "row_count": len(rows), "trial_indices_contiguous":
                [int(r[3]) for r in rows] == list(range(len(rows))), "halves": blocks})
out["exposure"] = "All 44 newly acquired high-similarity DAT files decoded and hashed. Census reads only IDs/order/condition/trial/block/stimulus fields; response/truth/accuracy/RT/test-old fields remain uninterpreted except participant20 previously consumed. Decoding is not pristine nonacquisition."
out["peak_rss_native"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
(ROOT / "METADATA_CHECK.json").write_text(json.dumps(out, indent=2))
print(out["geometry_csv_text"])
for p in out["people"]:
    print(p["id"], p["header"][2], p["row_count"], p["pin_matches"],
          [(x["train_rows"],x["test_rows"],x["category_switches"]) for x in p["halves"]])
print("peakRSS",out["peak_rss_native"])
