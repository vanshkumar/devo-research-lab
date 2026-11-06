"""Original participant 20: exposure-to-new-item response arithmetic."""
import collections
import datetime
import hashlib
import json
import pathlib
import resource
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
with zipfile.ZipFile(ROOT / "source/highsim-trials.zip") as z:
    payload = z.read("20.dat")
lines = payload.decode().splitlines()
rows = [s.split() for s in lines if len(s.split()) == 12 and
        s.split()[0] == "20" and s.split()[3].isdigit()]
print("record counts", len(rows), dict(collections.Counter(r[2] for r in rows)), flush=True)
assert len(rows) == 672
assert [int(x[3]) for x in rows] == list(range(672))
byblock = collections.defaultdict(list)
for row in rows:
    byblock[int(row[4])].append(row)
checks = []
for blocks, testblock in [([1, 2, 3, 4], 5), ([6, 7, 8, 9], 10)]:
    train = [r for b in blocks for r in byblock[b]]
    test = byblock[testblock]
    exposure_names = {r[9] for r in train}
    novel = [r for r in test if r[9] not in exposure_names]
    old = [r for r in test if r[9] in exposure_names]
    assert all((r[5] == r[6]) == (r[7] == "1") for r in train + test)
    assert all((r[11] == "0") == (r[9] not in exposure_names) for r in test)
    switches = sum(a[9][0] != b[9][0] for a, b in zip(train, train[1:]))
    correct = sum(r[7] == "1" for r in novel)
    checks.append({"train_blocks": blocks, "test_block": testblock,
        "exposures": len(train), "distinct_training_items": len(exposure_names),
        "category_counts": dict(collections.Counter(r[9][0] for r in train)),
        "category_switches": switches, "adjacent_pairs": len(train)-1,
        "switch_fraction": switches/(len(train)-1),
        "test_items": len(test), "novel_items": len(novel), "old_items": len(old),
        "novel_correct": correct, "novel_accuracy": correct/len(novel),
        "old_correct": sum(r[7] == "1" for r in old),
        "first_novel_response": next(r for r in test if r[9] not in exposure_names)})
out = {"completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "command": "python3 lab/tasks/category-curriculum-forecast-2026-11-01/first_data_check.py",
    "status": "ACTUAL_ORIGINAL_OBSERVATION_ARITHMETIC_EXECUTED",
    "participant": "highsim/20.dat", "sha256": hashlib.sha256(payload).hexdigest(),
    "sha256_matches_osf_listing": hashlib.sha256(payload).hexdigest() ==
        "04e708007c6aa6ca37f44a461a8d57ba48c3e39976a6f3406752f8df07c1f514",
    "headers": lines[:3], "rows": len(rows),
    "block_phase_counts": {str(b): dict(collections.Counter(r[2] for r in v))
                           for b, v in byblock.items()},
    "linked_checks": checks,
    "exposure": "All 672 participant-20 rows decoded; 18 start and 10 end lines previously rendered. Other 43 ZIP members acquired/hash-compressed but not decoded by this script. Published group summaries already exposed.",
    "scope": "Response equals supplied answer column agrees with correctness on all rows; novel flag agrees with exact training-item nonmembership. Raw field semantics and chronology still require primary methods certification. This is not a learning-model forecast or unique mechanism test.",
    "peak_rss_native": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(ROOT / "FIRST_DATA_CHECK.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
