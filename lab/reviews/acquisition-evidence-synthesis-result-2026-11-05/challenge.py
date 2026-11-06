"""Reconstruct the shared-owner working bounds from one pooled score member."""
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from itertools import product
import json
import os
from pathlib import Path
import re
import resource
import struct
import sys
from zipfile import ZipFile, ZIP_DEFLATED
import zlib

import numpy as np
from scipy.stats import t


HERE = Path(__file__).parent
AUTHOR = Path("lab/tasks/acquisition-evidence-synthesis-2026-11-05")
OLD = Path("lab/reviews/calibration-frontier-result-2026-11-05")
NEW = Path("lab/reviews/independent-confirmation-result-2026-11-05")
START = datetime.now(timezone.utc).isoformat()
READS = {}
MEMBERS = []


def read_json(path, pinned=None):
    data = path.read_bytes()
    digest = sha256(data).hexdigest()
    if pinned is not None:
        assert digest == pinned
    READS[str(path)] = {"bytes": len(data), "sha256": digest}
    return json.loads(data)


def members(path, names, pins, receipts):
    archive = pins["archives"][str(path)]
    arrays = {}
    with ZipFile(path) as zf, path.open("rb") as handle:
        assert zf.namelist() == archive["directory_member_names"]
        for name in names:
            pin = archive["authorized"][name]
            entry = zf.getinfo(pin["name"])
            assert entry.compress_type == ZIP_DEFLATED
            assert (entry.compress_size, entry.file_size, entry.CRC) == (
                pin["compressed_bytes"], pin["npy_bytes"], pin["crc32"]
            )
            handle.seek(entry.header_offset)
            header = struct.unpack("<4s5H3I2H", handle.read(30))
            assert header[0] == b"PK\x03\x04"
            handle.seek(header[-2] + header[-1], 1)
            compressed = handle.read(entry.compress_size)
            assert sha256(compressed).hexdigest() == pin["sha256_compressed"]
            body = zlib.decompress(compressed, wbits=-15)
            digest = sha256(body).hexdigest()
            assert len(body) == entry.file_size
            assert digest == receipts[(str(path), entry.filename)]
            arrays[name] = np.load(BytesIO(body), allow_pickle=False)
            MEMBERS.append({
                "path": str(path), "member": entry.filename,
                "compressed_bytes": len(compressed), "inflated_bytes": len(body),
                "sha256_compressed": pin["sha256_compressed"], "sha256_npy": digest,
            })
    READS[str(path)] = {"conservative_bytes": path.stat().st_size}
    return arrays


def bands(points, influence, df):
    se = np.sqrt(np.sum(influence ** 2, axis=0))
    signs = np.array(list(product((-1, 1), repeat=len(influence))))
    signed = np.sum(signs[:, :, None, None] * influence[None, :, :, :], axis=1)
    critical = np.quantile(np.max(np.abs(signed / se), axis=(1, 2)), .95)
    t_critical = t.isf(.05 / (2 * points.size), df)
    return {
        "point": points, "se": se, "wild_critical": critical,
        "bonferroni_t_critical": t_critical,
        "wild_upper": points + critical * se, "t_upper": points + t_critical * se,
        "sign_patterns": len(signs),
    }


def as_json(obj):
    return obj.tolist()


def main():
    pins = read_json(AUTHOR / "INPUT_PINS.json")
    resource_receipt = read_json(AUTHOR / "RUN_RESOURCES.json")
    receipts = {(r["archive"], r["member"]): r["sha256_npy"]
                for r in resource_receipt["npz_members_inflated"]}
    old_path = OLD / "REFINED_CHECK.json"
    old = read_json(old_path, pins["dictionaries_and_aggregate_sources_sha256"][str(old_path)])
    reported = read_json(AUTHOR / "SYNTHESIS.json")
    assert old["primary_columns"] == reported["columns"] == ["A200", "D200", "A1000", "D1000"]

    old_ids = members(OLD / "FULL_CONTRASTS.npz", ("subjects",), pins, receipts)["subjects"]
    new = members(NEW / "REVIEW_REDUCTIONS.npz",
                  ("subjects", "actors", "origins", "labs", "pooled"), pins, receipts)
    normalized = [{re.sub(r"[^a-z0-9]", "", str(s).lower()) for s in ids}
                  for ids in (old_ids, new["subjects"])]
    assert tuple(map(len, normalized)) == (64, 192) and normalized[0].isdisjoint(normalized[1])
    assert new["origins"].tolist() == [200, 1000]
    assert new["pooled"].shape == (192, 2, 4, 3)
    recent = new["pooled"][:, :, new["actors"].tolist().index("recent100"), :]
    gru = new["pooled"][:, :, new["actors"].tolist().index("gru"), :]
    accuracy = recent[:, :, 2] - gru[:, :, 2]
    proper = .9 * recent[:, :, 0] - gru[:, :, 0]
    new_scores = np.column_stack((accuracy[:, 0], proper[:, 0], accuracy[:, 1], proper[:, 1]))
    assert np.isfinite(new_scores).all()
    new_labs = np.array(["churchlandlab" if lab == "churchlandlab_ucla" else lab
                         for lab in new["labs"]])
    old_sites = {r["site"]: (r["n"], r["mean"]) for r in old["cohort_site"]["sites"]}
    new_sites = {lab: (np.count_nonzero(new_labs == lab), new_scores[new_labs == lab].mean(axis=0))
                 for lab in np.unique(new_labs)}
    union = sorted(set(old_sites) | set(new_sites))
    counts = np.array([[table.get(lab, (0, None))[0] for table in (old_sites, new_sites)]
                       for lab in union])
    means = np.array([[table.get(lab, (0, [0] * 4))[1] for table in (old_sites, new_sites)]
                      for lab in union])
    assert counts.sum(axis=0).tolist() == [64, 192]
    owner_counts = (counts > 0).sum(axis=0)
    assert owner_counts.tolist() == [9, 10] and len(union) == 11
    df = int(min(owner_counts) - 1)

    def evaluate(weights):
        point = np.sum(weights[:, :, None] * means, axis=0)
        adjustment = np.sqrt(owner_counts / (owner_counts - 1))
        influence = weights[:, :, None] * (means - point) * adjustment[:, None]
        return point, influence

    animal_point, animal_influence = evaluate(counts / counts.sum(axis=0))
    equal_point, equal_influence = evaluate((counts > 0) / owner_counts)
    mix = np.array([[.25, .75], [.5, .5]])
    reconstructed = {
        "roster_shared_owner": bands(animal_point, animal_influence, df),
        "fixed_and_equal_roster_mix": bands(
            mix @ animal_point, np.einsum("mr,orc->omc", mix, animal_influence), df),
        "roster_equal_owner": bands(equal_point, equal_influence, df),
    }
    differences = {}
    for name, result in reconstructed.items():
        differences[name] = max(
            float(np.max(np.abs(result[key] - np.array(reported[name][key]))))
            for key in result
        )
        assert differences[name] < 1e-12
    wild_roster = reconstructed["roster_shared_owner"]["wild_upper"]
    student_roster = reconstructed["roster_shared_owner"]["t_upper"]
    early_root = (.02 - student_roster[0, 0]) / (student_roster[1, 0] - student_roster[0, 0])
    late_root = (.02 - student_roster[0, 2]) / (student_roster[1, 2] - student_roster[0, 2])
    draw = next(r for r in reported["tipping"]["opposing_scenarios"] if r["draw"] == 14)
    old_shift = draw["shifts"][0][0]
    assert old_shift == draw["shifts"][1][0]
    calculation = {
        "columns": reported["columns"], "accuracy_margin": .02, "D_margin": 0,
        "roster_animal_counts": counts.sum(axis=0), "roster_owner_counts": owner_counts,
        "overlap_normalized_deposited_names": len(normalized[0] & normalized[1]),
        "overlap_owners": int(np.all(counts > 0, axis=1).sum()), "owner_count_union": len(union),
        "owner_counts_old_later": dict(zip(union, counts)),
        "reconstructed": reconstructed, "max_abs_difference_from_synthesis": differences,
        "student_corner_interpolation_later_weight_open_interval": [late_root, early_root],
        "shared_owner_covariance": np.sum(animal_influence[:, 0] * animal_influence[:, 1], axis=0),
        "later_early_A_wild_headroom": .02 - wild_roster[1, 0],
        "draw14_old_matched_early_A_shift": old_shift,
        "hypothetical_draw14_later_early_A_point": animal_point[1, 0] + old_shift,
        "hypothetical_draw14_later_early_A_wild_upper": wild_roster[1, 0] + old_shift,
    }
    output = HERE / "CHALLENGE.json"
    output.write_text(json.dumps(calculation, indent=2, default=as_json, allow_nan=False) + "\n")
    r = resource.getrusage(resource.RUSAGE_SELF)
    assert sys.platform == "darwin"
    resources = {
        "pid": os.getpid(), "start_utc_after_imports": START,
        "end_utc": datetime.now(timezone.utc).isoformat(), "job": "complete",
        "cpu_seconds_process": r.ru_utime + r.ru_stime, "peak_rss_bytes": r.ru_maxrss,
        "input_receipts": READS, "opened_members": MEMBERS,
        "inflated_bytes": sum(m["inflated_bytes"] for m in MEMBERS),
        "booked_science_file_bytes_including_full_zip_size": sum(
            v.get("bytes", v.get("conservative_bytes", 0)) for v in READS.values()
        ),
        "ingress_bytes": 0, "output_bytes": output.stat().st_size,
        "physical_io_and_platform_overhead": "unmeasured",
    }
    (HERE / "RUN_RESOURCES.json").write_text(json.dumps(resources, indent=2) + "\n")
    print(json.dumps({"calculation": calculation, "resources": resources},
                     default=as_json, allow_nan=False))


if __name__ == "__main__":
    main()
