"""Bounded two-variable measurement of the pinned Brown Expe3 release."""

import argparse
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import resource
import sys
from time import perf_counter

import numpy as np
from scipy.io import loadmat, savemat, whosmat

from audit_expe3 import MAX_BODY, StopAudit, expect_stop, fixture, pinned_mat, summarize_opportunities


EXACT_DIRECTORY = [("columns", (1, 17), "cell"), ("expe_data", (30403, 17), "double")]


def verify_directory(raw, evidence, expected=EXACT_DIRECTORY):
    if (len(raw) < 128 or not raw.startswith(b"MATLAB 5.0 MAT-file")
            or raw[124:128] != b"\x00\x01IM"):
        raise StopAudit("expected pinned little-endian MATLAB level-5 container")
    evidence["directory"] = whosmat(io.BytesIO(raw))
    if evidence["directory"] != expected:
        raise StopAudit("inventory differs from the amended exact directory")


def read_behavior(raw, evidence, shape=EXACT_DIRECTORY[-1][1]):
    parsed = loadmat(io.BytesIO(raw), variable_names=["expe_data"],
                     verify_compressed_data_integrity=True)
    evidence["loaded_user_variables"] = sorted(k for k in parsed if not k.startswith("__"))
    if evidence["loaded_user_variables"] != ["expe_data"]:
        raise StopAudit("numeric projection did not return exactly expe_data")
    evidence["opaque_companion"] = "columns (1x17 cell), directory only; no cell values interpreted"
    matrix = parsed["expe_data"]
    evidence["numeric_decode"] = {
        "shape": list(matrix.shape), "dtype": str(matrix.dtype),
        "nbytes": matrix.nbytes, "uninterpreted_numeric_columns": [15, 16, 17],
    }
    if matrix.shape != shape or matrix.dtype.kind != "f" or matrix.dtype.itemsize != 8:
        raise StopAudit("decoded matrix differs from the allowed numeric representation")
    return matrix[:, :14]


def control():
    matrix = fixture()
    labels = [f"fixture field {i + 1}" for i in range(17)]
    raw = io.BytesIO()
    savemat(raw, {"columns": np.array([labels], dtype=object), "expe_data": matrix},
            do_compression=True)
    expected = [("columns", (1, 17), "cell"), ("expe_data", matrix.shape, "double")]
    body = raw.getvalue()
    evidence = {}
    verify_directory(body, evidence, expected)
    assert np.array_equal(read_behavior(body, evidence, matrix.shape), matrix[:, :14])
    assert evidence["loaded_user_variables"] == ["expe_data"]
    expect_stop(lambda: verify_directory(body, {}, EXACT_DIRECTORY), "exact directory")
    return {"synthetic_only": True, "source_trial_files_read": 0,
            "checks": ["exact two-entry inventory", "only expe_data returned",
                       "reject unexpected inventory"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["behavior", "control"])
    parser.add_argument("body", nargs="?", type=Path)
    parser.add_argument("--projection", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if (args.phase == "control") != (args.body is None):
        parser.error("exact body is required for source phases only")
    if args.projection is not None and args.phase != "behavior":
        parser.error("projection is only valid in the behavior phase")
    evidence = {"phase": args.phase, "started_utc": datetime.now(timezone.utc).isoformat()}
    start = perf_counter()
    rc = 0
    try:
        if args.phase == "control":
            evidence["control"] = control()
        else:
            with args.body.open("rb") as f:
                body = f.read(MAX_BODY + 1)
            source = evidence.setdefault("source", {})
            raw = pinned_mat(body, source)
            verify_directory(raw, source)
            behavior = read_behavior(raw, source)
            evidence["opportunities"] = summarize_opportunities(behavior)
            if args.projection:
                with args.projection.open("xb") as f:
                    np.save(f, behavior, allow_pickle=False)
                evidence["projection_bytes"] = args.projection.stat().st_size
            evidence["stage_a_pass"] = None
    except (ValueError, OSError, TypeError, KeyError) as error:
        evidence["stop"] = f"{type(error).__name__}: {error}"
        rc = 1
    usage = resource.getrusage(resource.RUSAGE_SELF)
    evidence["resources"] = {
        "user_seconds": usage.ru_utime, "system_seconds": usage.ru_stime,
        "audit_wall_seconds": perf_counter() - start,
        "peak_rss_bytes": usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024),
    }
    result = json.dumps(evidence, indent=2, allow_nan=False) + "\n"
    args.report.write_text(result)
    print(result, end="")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
