#!/usr/bin/env python3
"""Join the pinned outcome-free roster to exact NWB version lengths, offline."""

import csv
import hashlib
import io
import json
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parent
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
PREFIX = "visual-behavior-ophys/behavior_sessions/"
ROSTER_COLUMNS = (
    "behavior_session_id equipment_name full_genotype mouse_id reporter_line "
    "driver_line sex age_in_days cre_line indicator session_number "
    "prior_exposures_to_session_type prior_exposures_to_image_set "
    "prior_exposures_to_omissions ophys_session_id ophys_experiment_id "
    "ophys_container_id project_code date_of_acquisition session_type file_id"
).split()


def version_lengths():
    pages = sorted(ROOT.glob("allen_behavior_versions_[0-9][0-9].xml"))
    index = {}
    deleted = 0
    expected_marker = ("", "")
    for ordinal, page in enumerate(pages, 1):
        assert page.name == f"allen_behavior_versions_{ordinal:02d}.xml"
        root = ElementTree.parse(page).getroot()
        assert root.findtext(NS + "Prefix") == PREFIX
        assert (root.findtext(NS + "KeyMarker"), root.findtext(NS + "VersionIdMarker")) == expected_marker
        assert (root.findtext(NS + "IsTruncated") == "true") == (ordinal < len(pages))
        expected_marker = (root.findtext(NS + "NextKeyMarker"), root.findtext(NS + "NextVersionIdMarker"))
        deleted += len(root.findall(NS + "DeleteMarker"))
        for item in root.findall(NS + "Version"):
            key = item.findtext(NS + "Key")
            version = item.findtext(NS + "VersionId")
            assert key.startswith(PREFIX) and (key, version) not in index
            index[key, version] = (int(item.findtext(NS + "Size")), item.findtext(NS + "ETag"))
    assert pages
    return index, len(pages), deleted


def manifest(version, lengths):
    doc = json.loads((ROOT / f"allen_manifest_v{version}.json").read_bytes())
    assert doc["project_name"] == "visual-behavior-ophys" and doc["manifest_version"] == version
    objects = {}
    for file_id, item in doc["data_files"].items():
        key = urlsplit(item["url"]).path.lstrip("/")
        if not key.startswith(PREFIX):
            continue
        session = re.fullmatch(r"behavior_session_(\d+)\.nwb", key[len(PREFIX):])[1]
        assert session not in objects
        size, etag = lengths[key, item["version_id"]]
        objects[session] = {"file_id": file_id, "bytes": size, "etag": etag, **item}
    return doc["metadata_files"]["behavior_session_table"], objects


def describe_bytes(objects):
    sizes = [obj["bytes"] for obj in objects]
    return {"objects": len(sizes), "total_bytes": sum(sizes), "min_bytes": min(sizes),
            "median_bytes": statistics.median(sizes), "max_bytes": max(sizes)}


def write_csv(name, rows):
    with (ROOT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    lengths, pages, deleted = version_lengths()
    old_roster_pin, old = manifest("1.0.1", lengths)
    _, current = manifest("1.1.0", lengths)

    roster_bytes = (ROOT / "allen_roster_v1.0.1.csv").read_bytes()
    assert hashlib.blake2b(roster_bytes).hexdigest() == old_roster_pin["file_hash"]
    reader = csv.DictReader(io.StringIO(roster_bytes.decode("utf-8")))
    assert reader.fieldnames == ROSTER_COLUMNS
    roster = {}
    by_mouse = defaultdict(list)
    for row in reader:
        session = row["behavior_session_id"]
        assert session not in roster and row["mouse_id"] and None not in row
        row["time"] = datetime.fromisoformat(row["date_of_acquisition"])
        stage = re.fullmatch(r"TRAINING_([0-5])_.+", row["session_type"])
        row["stage"] = int(stage[1]) if stage else None
        roster[session] = row
        by_mouse[row["mouse_id"]].append(row)
    old_csv_file_map = {session: row["file_id"].split(".")[0] for session, row in roster.items() if row["file_id"]}
    assert old_csv_file_map == {session: obj["file_id"] for session, obj in old.items()}

    footprint = []
    for session, obj in sorted(current.items(), key=lambda pair: int(pair[0])):
        row = roster.get(session, {})
        footprint.append({"behavior_session_id": session, "mouse_id": row.get("mouse_id", ""),
                          "historical_date_of_acquisition": row.get("date_of_acquisition", ""),
                          "historical_session_type": row.get("session_type", ""),
                          "historical_equipment_name": row.get("equipment_name", ""),
                          "historical_file_id": row.get("file_id", ""), **obj})

    first0, first1, first1_rows, disposition = [], [], [], []
    stage_decreases = Counter()
    history_issues = Counter()
    room = Counter()
    year = Counter()
    rig = Counter()
    genotype = Counter()
    for mouse, physical_rows in sorted(by_mouse.items()):
        times = [row["time"] for row in physical_rows]
        history_issues["historical_roster_physical_order_not_chronological"] += times != sorted(times)
        history_issues["same_timestamp_learner"] += len(times) != len(set(times))
        rows = sorted(physical_rows, key=lambda row: row["time"])
        latest_training = [row for row in rows if row["behavior_session_id"] in current and row["stage"] is not None]
        stage0 = [row for row in latest_training if row["stage"] == 0]
        stage1 = [row for row in latest_training if row["stage"] == 1]
        assert len(stage0) == 1 and stage1
        zero, one = stage0[0], stage1[0]
        zero_id, one_id = zero["behavior_session_id"], one["behavior_session_id"]
        first0.append(current[zero_id])
        first1.append(current[one_id])
        first1_rows.append(one)
        history_issues["earliest_historical_release_row_not_training_0"] += rows[0] != zero
        history_issues["first_training_1_not_second_latest_training_row"] += latest_training[1] != one
        history_issues["training_1_precedes_training_0"] += one["time"] <= zero["time"]
        history_issues["first_training_1_nonzero_prior_same_type"] += one["prior_exposures_to_session_type"] not in ("0", "0.0")
        history_issues["same_calendar_date_training_rows_learner"] += len({row["time"].date() for row in latest_training}) < len(latest_training)
        history_issues["historical_ophys_linked_learner"] += any(row["ophys_session_id"] for row in rows)
        history_issues["genotype_disagreement_learner"] += len({row["full_genotype"] for row in rows}) != 1
        for earlier, later in zip(latest_training, latest_training[1:]):
            if earlier["stage"] > later["stage"]:
                stage_decreases[f"{earlier['stage']}->{later['stage']}"] += 1
        first_rig = one["equipment_name"]
        rig[first_rig] += 1
        room[first_rig.split("-Box")[0]] += 1
        year[one["time"].year] += 1
        genotype[one["cre_line"]] += 1
        disposition.append({"mouse_id": mouse, "earliest_historical_session_id": rows[0]["behavior_session_id"],
                            "earliest_historical_label": rows[0]["session_type"],
                            "training_0_id": zero_id, "training_0_date": zero["date_of_acquisition"],
                            "training_0_bytes_v1.1.0": current[zero_id]["bytes"],
                            "first_training_1_id": one_id, "first_training_1_date": one["date_of_acquisition"],
                            "first_training_1_bytes_v1.1.0": current[one_id]["bytes"],
                            "first_training_1_rig": first_rig, "first_training_1_cre_line": one["cre_line"],
                            "historical_session_rows": len(rows), "latest_joined_training_rows": len(latest_training),
                            "first_historical_ophys_link": next((row["behavior_session_id"] for row in rows if row["ophys_session_id"]), "")})

    removed = {session: {"mouse_id": roster[session]["mouse_id"], "session_type": roster[session]["session_type"],
                         "historical_date_of_acquisition": roster[session]["date_of_acquisition"]}
               for session in sorted(old.keys() - current.keys())}
    added = {session: {"old_roster_has_session": session in roster,
                       "old_label": roster.get(session, {}).get("session_type"),
                       "old_has_ophys_link": bool(roster.get(session, {}).get("ophys_session_id"))}
             for session in sorted(current.keys() - old.keys())}
    joined_stage = Counter(str(roster[session]["stage"]) for session in current.keys() & roster.keys())
    metrics = {
        "version_catalogue": {"pages": pages, "version_entries": len(lengths), "delete_markers": deleted},
        "historical_roster": {"rows": len(roster), "columns": ROSTER_COLUMNS, "mice": len(by_mouse),
                              "rows_with_naive_datetime": sum(r["time"].tzinfo is None for r in roster.values()),
                              "rows_without_file_id": len(roster) - len(old_csv_file_map),
                              "training_only_bodies": describe_bytes(old.values())},
        "latest_behavior_only_manifest": {"exact_version_sizes": describe_bytes(current.values()),
                                          "old_roster_session_matches": len(current.keys() & roster.keys()),
                                          "old_training_manifest_matches": len(current.keys() & old.keys()),
                                          "stages_from_historical_join": dict(joined_stage),
                                          "removed_from_behavior_only": removed, "added_to_behavior_only": added,
                                          "unknown_historical_labels": sorted(s for s in current.keys() & roster.keys() if not roster[s]["session_type"])},
        "chronology": dict(history_issues), "stage_decreases": dict(stage_decreases),
        "first_0": describe_bytes(first0), "first_1": describe_bytes(first1),
        "paired_0_and_first_1_bytes": sum(obj["bytes"] for obj in first0 + first1),
        "first_1_dates": [min(row["time"] for row in first1_rows).isoformat(), max(row["time"] for row in first1_rows).isoformat()],
        "first_1_by_rig": dict(rig), "first_1_by_rig_prefix": dict(room),
        "first_1_by_year": dict(year), "first_1_by_cre_line": dict(genotype),
        "published_example_328341_in_roster": "328341" in by_mouse,
    }
    write_csv("TRAINING_OBJECTS.csv", footprint)
    write_csv("LEARNER_DISPOSITION.csv", disposition)
    (ROOT / "VERIFICATION.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
