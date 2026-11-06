"""Read historical JSON metadata/ledgers only; never open trial-data objects."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
OLD = ROOT / "campaigns/learning_rule_transport_2026-10-28"
POP = ROOT / "campaigns/population_learning_transport_2026-10-28"


def read(path):
    return json.loads(path.read_text())


def boundaries(lengths, lo, hi):
    position = 0
    result = []
    for length in lengths:
        if lo <= position < hi:
            result.append(position)
        position += length
    return result


def main():
    inputs = [
        OLD / "protocols/SPLIT.json", OLD / "data/COVERAGE.json",
        OLD / "data/INDEX.json", OLD / "data/EXCLUDED_EXTERNAL_PROTOCOL_RECORDS.json",
        OLD / "protocols/VALIDATION_STATUS.json", OLD / "protocols/EXPOSURE.jsonl",
        POP / "protocols/VALIDATION_STATUS.json", POP / "protocols/EXPOSURE.jsonl",
        POP / "protocols/RELEASE_REQUIREMENTS.json", POP / "protocols/SOURCE_GATE.json",
        POP / "protocols/FREEZE.json", POP / "protocols/PROTOCOL.md",
        OLD / "protocols/TRAINER.md",
        POP / "artifacts/policy_audit/POLICY_AUDIT.md",
        ROOT / "sources/learning_transport_route_2026-10-29/RESULT.json",
    ]
    split = read(inputs[0])
    coverage = read(inputs[1])
    index = read(inputs[2])
    excluded = read(inputs[3])
    strict = split["external_strict_prefix"]
    external = [row for row in coverage if row["split"] == "external"]
    sessions = [row for row in index if row["split"] == "external"]
    assert len(strict) == len(external) == 20
    assert set(strict) == {row["subject"] for row in external}
    assert len({row["eid"] for row in sessions}) == len(sessions) == 453
    assert all(row["kind"] == "table" for row in sessions)
    assert all(row["trials"] >= 4000 for row in external)
    assert all(row["author_day"] > 0 for row in sessions)
    assert all(row["author_day"] == 0 for row in excluded)
    by_subject = []
    for row in external:
        rows = sorted((x for x in sessions if x["subject"] == row["subject"]),
                      key=lambda x: (x["date"], x["number"]))
        days = [x["author_day"] for x in rows]
        assert days[0] == 1
        assert all(a <= b for a, b in zip(days, days[1:]))
        assert len(rows) == row["sessions"] == len(row["session_trials"])
        assert sum(row["session_trials"]) == row["trials"]
        by_subject.append({
            "subject": row["subject"], "indexed_opportunities": row["trials"],
            "ordinary_sessions": row["sessions"], "first_author_day": days[0],
            "future_session_starts_1000_4000": boundaries(row["session_trials"], 1000, 4000),
            "prefix_session_starts_1_1000": boundaries(row["session_trials"], 1, 1000),
        })
    transition_summary = {}
    for group in ("external", "dev", "animal_holdout", "lab_holdout"):
        values = [len(boundaries(x["session_trials"], 1000, 4000)) for x in coverage
                  if x["split"] == group and x["trials"] >= 4000]
        transition_summary[group] = {"n": len(values), "min": min(values),
                                     "median": median(values), "max": max(values)}
    events = []
    for ledger in (OLD / "protocols/EXPOSURE.jsonl", POP / "protocols/EXPOSURE.jsonl"):
        data = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
        positives = [x for x in data if x.get("external_outcomes_read") is True
                     or x.get("external_prefixes_outcomes_read") is True
                     or ((x.get("split") == "external" or x.get("cohort") == "external")
                         and "open" in x.get("event", ""))]
        events.append({"ledger": str(ledger.relative_to(ROOT)), "events": len(data),
                       "positive_external_open_events": positives})
        assert not positives
    result = {
        "date": "2026-10-29", "status": "metadata_audit_only_no_release",
        "new_trial_values_read": False, "trial_objects_opened": 0,
        "strict_animals": len(strict), "ordinary_sessions": len(sessions),
        "excluded_unconditioned_day0_sessions": len(excluded),
        "all_20_have_1000_plus_3000": True,
        "task_protocols": dict(Counter(x["protocol"] for x in sessions)),
        "lab_counts": dict(Counter(x["lab"] for x in external)),
        "prefix_gaps_excluded": split["external_prefix_gap_excluded"],
        "session_transition_metadata": transition_summary,
        "subjects": by_subject, "ledger_checks": events,
        "historical_population_gate_earned": read(POP / "protocols/SOURCE_GATE.json")["new_population_source_gate_earned"],
        "historical_external_release": read(POP / "protocols/SOURCE_GATE.json")["external_release"],
        "pins": {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
                 for path in inputs},
    }
    path = OUT / "METADATA_ACCESS_AUDIT.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"path": str(path.relative_to(ROOT)), "animals": len(strict),
                      "sessions": len(sessions), "new_trial_values_read": False,
                      "all_20_have_4000": True, "historical_external_release": False}))


if __name__ == "__main__":
    main()
