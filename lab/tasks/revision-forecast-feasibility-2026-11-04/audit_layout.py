"""Audit only Git metadata and three allowlisted OOXML metadata members."""

from collections import Counter, defaultdict
from hashlib import sha1, sha256
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent
PIN = "a433be296c3d3566754106f64d16dbf48182bc00"
SCORE = "dataset/meta-data/Scores/scores.xlsx"
SCORE_METADATA = ("xl/workbook.xml", "xl/_rels/workbook.xml.rels", "docProps/core.xml")
STRATA = "ABCD"
DEV_PER_ARM = 6
SPLIT_SALT = "revision-forecast-feasibility-2026-11-04/Rev12-v1:"


def verify_blob(body, entry):
    digest = sha1(f"blob {len(body)}\0".encode() + body).hexdigest()
    if len(body) != entry["size"] or digest != entry["sha"]:
        raise ValueError(f"Pinned blob mismatch for {entry['path']}")


def score_layout(entry):
    body = (ROOT / "source/scores.xlsx").read_bytes()
    verify_blob(body, entry)
    with ZipFile(ROOT / "source/scores.xlsx") as archive:
        parts = [
            dict(name=part.filename, bytes=part.file_size, compressed_bytes=part.compress_size)
            for part in archive.infolist()
        ]
        metadata = {name: archive.read(name) for name in SCORE_METADATA}
    workbook, relationships, core = map(ET.fromstring, metadata.values())
    targets = {rel.get("Id"): rel.get("Target") for rel in relationships}
    return {
        "blob": entry,
        "sha256": sha256(body).hexdigest(),
        "archive_parts": parts,
        "part_bytes_inflated": {key: len(value) for key, value in metadata.items()},
        "sheets": [
            {
                "name": sheet.get("name"),
                "state": sheet.get("state", "visible"),
                "part": targets[next(value for key, value in sheet.attrib.items() if key.endswith("}id"))],
            }
            for sheet in workbook.findall(".//{*}sheet")
        ],
        "document_dates": {
            prop.tag.split("}")[-1]: prop.text
            for prop in core
            if prop.tag.endswith(("}created", "}modified"))
        },
    }


def main():
    raw_tree = (ROOT / "RELEASE_TREE.json").read_bytes()
    tree = json.loads(raw_tree)
    if tree["sha"] != PIN or tree["truncated"]:
        raise ValueError("Expected the complete pinned tree response")
    blobs = {entry["path"]: entry for entry in tree["tree"] if entry["type"] == "blob"}
    essays = {draft: {} for draft in "123"}
    feedback = {}
    rev = {stage: defaultdict(list) for stage in ("12", "23")}
    unmatched = []
    groups = Counter()
    for path in blobs:
        groups[path.rsplit("/", 1)[0]] += 1
        essay = re.fullmatch(r"dataset/essays/Draft([123])/(?:draft[12]_)?2018argrewrite_(\d+)\.txt", path)
        item = re.fullmatch(r"dataset/meta-data/ExpertFeedback/feedback_(\d+)\.docx", path)
        annotation = re.fullmatch(
            r"dataset/annotations/([A-D])/(12|23)/Annotation_2018argrewrite_(\d+)(?:_NEW)*\.txt\.xlsx",
            path,
        )
        if essay:
            draft, ident = essay.groups()
            if ident in essays[draft]:
                raise ValueError(f"Duplicate draft key {path}")
            essays[draft][ident] = path
        elif item:
            ident = item.group(1)
            if ident in feedback:
                raise ValueError(f"Duplicate feedback key {path}")
            feedback[ident] = path
        elif annotation:
            arm, stage, ident = annotation.groups()
            rev[stage][ident].append((arm, path))
        elif path.startswith(("dataset/essays/", "dataset/meta-data/ExpertFeedback/")) or (
            path.startswith("dataset/annotations/") and path.endswith(".xlsx")
        ):
            unmatched.append(path)

    common = set.intersection(*(set(group) for group in (*essays.values(), feedback)))
    anomalies = {}
    for stage, files in rev.items():
        anomalies[stage] = {
            "excess": sorted(files.keys() - common, key=int),
            "missing": sorted(common - files.keys(), key=int),
            "duplicate_or_ambiguous": {ident: paths for ident, paths in files.items() if len(paths) != 1},
        }
    by_arm = defaultdict(list)
    cross_arm = {}
    for ident in common:
        before, after = rev["12"].get(ident, []), rev["23"].get(ident, [])
        if len(before) != 1 or len(after) != 1:
            continue
        if before[0][0] != after[0][0]:
            cross_arm[ident] = [before[0][0], after[0][0]]
            continue
        by_arm[before[0][0]].append(ident)
    development = []
    for arm in STRATA:
        keys = sorted(by_arm[arm], key=lambda ident: sha256((SPLIT_SALT + ident).encode()).digest())
        if len(keys) < DEV_PER_ARM:
            raise ValueError(f"Insufficient unambiguous keys in {arm}")
        for ident in keys[:DEV_PER_ARM]:
            paths = {
                "draft1": essays["1"][ident], "draft2": essays["2"][ident],
                "feedback": feedback[ident], "rev12": rev["12"][ident][0][1],
            }
            development.append(
                {"key": ident, "arm": arm, "objects": {name: blobs[path] for name, path in paths.items()}}
            )
    return {
        "pin": PIN,
        "tree_bytes": len(raw_tree),
        "tree_sha256": sha256(raw_tree).hexdigest(),
        "entries": len(tree["tree"]),
        "blob_counts": dict(sorted(groups.items())),
        "unmatched_filenames": unmatched,
        "matched_essay_counts": {draft: len(rows) for draft, rows in essays.items()},
        "matched_feedback_count": len(feedback),
        "all_three_drafts_and_feedback_key_intersection": len(common),
        "annotation_key_counts": {stage: len(rows) for stage, rows in rev.items()},
        "annotation_anomalies": anomalies,
        "cross_arm_mismatches": cross_arm,
        "unique_both_annotations_matching_arm": {arm: len(by_arm[arm]) for arm in STRATA},
        "dev_rule": {"per_arm": DEV_PER_ARM, "salt": SPLIT_SALT, "ordering": "sha256 ascending"},
        "development": development,
        "dev_payload_bytes_planned": sum(
            item["size"] for row in development for item in row["objects"].values()
        ),
        "scores_layout": score_layout(blobs[SCORE]),
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
