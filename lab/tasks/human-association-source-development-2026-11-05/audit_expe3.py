"""One-pass structural and behavioral audit for the frozen Brown Expe3 blob."""

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import resource
import sys
from time import perf_counter

import numpy as np
from scipy.io import loadmat, savemat, whosmat


BLOB = "2ab7b32fd81296453835edb81a7c59d97d9325a2"
MAT_BYTES = 352400
MAX_BODY = 600000
MAX_ROWS = 43200
COLUMN_NAMES = (
    "person", "block", "load", "time", "cue", "image", "category",
    "cue_iteration", "correct_action", "choice", "physical_key",
    "correct", "reward", "rt",
)
ACTIONS = (1, 2, 3)


class StopAudit(ValueError):
    """An unexpected container, pin, or schema must stop before interpretation."""


def sha1_blob(raw):
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def pinned_mat(body, evidence, expected_bytes=MAT_BYTES, expected_blob=BLOB):
    evidence["body_bytes"] = len(body)
    if len(body) > MAX_BODY:
        raise StopAudit("physical response exceeds frozen cap")
    raw = body
    evidence["representation"] = "raw"
    if body.lstrip().startswith(b"{"):
        evidence["representation"] = "JSON/base64"
        envelope = json.loads(body)
        if (envelope.get("encoding") != "base64"
                or envelope.get("size") != expected_bytes
                or envelope.get("sha") != expected_blob):
            raise StopAudit("unexpected Git blob envelope")
        raw = base64.b64decode("".join(envelope["content"].split()), validate=True)
    evidence["mat_bytes"] = len(raw)
    evidence["actual_git_blob"] = sha1_blob(raw)
    evidence["sha256"] = hashlib.sha256(raw).hexdigest()
    if len(raw) != expected_bytes or evidence["actual_git_blob"] != expected_blob:
        raise StopAudit("byte size or Git blob mismatch")
    return raw


def decode_mat(raw, evidence):
    # The directory read may expand a compressed header buffer. It does not
    # load any trial matrix. Dimensions and class are checked before loadmat.
    if len(raw) < 128 or not raw.startswith(b"MATLAB 5.0 MAT-file"):
        raise StopAudit("expected MATLAB level-5 container")
    endian = {b"IM": "little", b"MI": "big"}.get(raw[126:128])
    if endian is None or int.from_bytes(raw[124:126], endian) != 0x0100:
        raise StopAudit("unexpected endian marker or MAT container version")
    evidence["mat_container"] = {"format": "level-5", "byte_order": endian}
    inventory = whosmat(io.BytesIO(raw))
    evidence["directory"] = inventory
    if len(inventory) != 1:
        raise StopAudit("expected exactly one variable")
    name, shape, mat_class = inventory[0]
    if (name != "expe_data" or mat_class not in ("double", "single")
            or len(shape) != 2 or not 1 <= shape[0] <= MAX_ROWS or shape[1] != 17):
        raise StopAudit("unexpected MAT variable, class or dimensions")
    matrix = loadmat(io.BytesIO(raw), variable_names=["expe_data"],
                     verify_compressed_data_integrity=True)["expe_data"]
    evidence["decoded"] = {"shape": list(matrix.shape), "dtype": str(matrix.dtype),
                           "matrix_bytes": matrix.nbytes, "auxiliary_columns": [15, 16, 17]}
    if matrix.shape != shape or matrix.dtype.kind != "f" or matrix.dtype.itemsize not in (4, 8):
        raise StopAudit("unexpected decoded representation")
    return matrix[:, :14]


def code_hist(values):
    values, counts = np.unique(values, return_counts=True)
    return {str(float(value)): int(n) for value, n in zip(values, counts)}


def quantiles(values):
    finite = values[np.isfinite(values)]
    if not finite.size:
        return {"n": 0}
    q = np.quantile(finite, [0, .05, .25, .5, .75, .95, .99, 1])
    return dict(zip(("n", "min", "q05", "q25", "median", "q75", "q95", "q99", "max"),
                    [int(finite.size)] + q.tolist()))


def summarize_responses(x):
    if not len(x):
        return {"rows": 0}
    correct_action, choice, key, correct, reward, rt = x[:, 8:14].T
    responded = np.isin(choice, ACTIONS)
    absent = (np.isfinite(choice) & (choice <= 0)) | np.isnan(choice)
    valid_correct = (choice == correct_action)
    mismatch = responded & (correct != valid_correct)
    positive_rt = responded & np.isfinite(rt) & (rt > 0)
    seconds = rt[positive_rt]
    # The pinned author analysis compares RT directly with 0.15. Diagnose
    # compatibility under seconds without converting unusual values.
    time_bands = np.histogram(
        seconds, [-np.inf, .15, 1.3, 1.35, 1.375, 1.4, 1.5, np.inf]
    )[0].tolist()
    near_deadline = positive_rt & (rt >= 1.3) & (rt <= 1.400001)
    return {
        "rows": len(x), "responded": int(responded.sum()),
        "candidate_omissions": int(absent.sum()),
        "candidate_omission_rate": float(absent.mean()),
        "unknown_choice_rows": int((~(responded | absent)).sum()),
        "responded_correct": int((responded & valid_correct).sum()),
        "responded_wrong": int((responded & ~valid_correct).sum()),
        "correctness_flag_mismatches": int(mismatch.sum()),
        "choice_codes": code_hist(choice),
        "physical_keys_by_action": {str(a): code_hist(key[choice == a]) for a in ACTIONS},
        "correct_codes_on_candidate_omissions": code_hist(correct[absent]),
        "reward_by_actual_response": {
            "correct_action": code_hist(reward[responded & valid_correct]),
            "wrong_action": code_hist(reward[responded & ~valid_correct]),
            "candidate_omission": code_hist(reward[absent]),
        },
        "positive_responded_rt_raw_quantiles": quantiles(seconds),
        "responded_nonpositive_or_nonfinite_rt": int((responded & ~positive_rt).sum()),
        "responded_rt_at_or_below_0p15": int((positive_rt & (rt <= .15)).sum()),
        "responded_rt_above_1p4_plus_1us": int((positive_rt & (rt > 1.400001)).sum()),
        "responded_rt_bands_raw_seconds_edges": ["-inf", .15, 1.3, 1.35, 1.375, 1.4, 1.5, "inf"],
        "responded_rt_band_counts": time_bands,
        "near_deadline_1p3_to_1p4": {
            "responses": int(near_deadline.sum()),
            "correct": int((near_deadline & valid_correct).sum()),
            "choice_codes": code_hist(choice[near_deadline]),
        },
        "candidate_omission_rt_quantiles": quantiles(rt[absent]),
        "candidate_omission_nonpositive_rt_codes": code_hist(rt[absent & ~(rt > 0)]),
        "candidate_omission_key_codes": code_hist(key[absent]),
    }


def summarize_opportunities(x):
    evidence = {
        "fields_1_to_14": list(COLUMN_NAMES),
        "nan_cells_by_field": dict(zip(COLUMN_NAMES, np.isnan(x).sum(axis=0).tolist())),
        "infinite_cells_by_field": dict(zip(COLUMN_NAMES, np.isinf(x).sum(axis=0).tolist())),
    }
    identity = x[:, [0, 1, 2, 4, 5, 6, 7, 8]]
    if (not np.isfinite(identity).all() or np.any(identity != np.floor(identity))
            or np.any(identity[:, [0, 1, 2, 6, 7]] <= 0)):
        evidence["structural_flags"] = ["nonintegral, nonpositive or nonfinite required identity values"]
        return evidence

    person, block, load, time, cue, _, _, iteration, action, choice = x[:, :10].T
    boundaries = np.flatnonzero((person[1:] != person[:-1]) | (block[1:] != block[:-1])) + 1
    starts = np.r_[0, boundaries]
    ends = np.r_[boundaries, len(x)]
    runs = x[starts, :2]
    people = np.unique(person)
    positions = x[:, [0, 1, 4, 7]]
    evidence["people"] = len(people)
    evidence["trial_rows"] = len(x)
    evidence["contiguous_person_block_runs"] = len(runs)
    evidence["distinct_person_blocks"] = len(np.unique(runs, axis=0))
    evidence["distinct_person_block_cue_iterations"] = len(np.unique(positions, axis=0))
    evidence["person_block_count_histogram"] = dict(Counter(
        int(np.count_nonzero(runs[:, 0] == p)) for p in people))
    evidence["nonconsecutive_person_block_ordinals"] = int(sum(
        not np.array_equal(runs[runs[:, 0] == p, 1], np.arange(1, 1 + np.sum(runs[:, 0] == p)))
        for p in people))
    evidence["person_with_multiple_row_runs"] = int(
        np.count_nonzero(person[1:] != person[:-1]) + 1 - len(people))
    flags = Counter()
    support = {}
    in_cap = np.zeros(len(x), dtype=bool)
    in_target = np.zeros(len(x), dtype=bool)
    pair_present = np.ones(len(x) - 1, dtype=bool)
    pair_present[boundaries - 1] = False
    for start, end in zip(starts, ends):
        ns = int(load[start])
        row = slice(start, end)
        n = int(end - start)
        summary = support.setdefault(ns, Counter())
        summary["blocks"] += 1
        summary["rows"] += n
        if ns not in range(1, 7) or np.any(load[row] != ns):
            flags["invalid_or_inconsistent_load_blocks"] += 1
            continue
        if ns in (3, 6):
            summary["prefix_2x_rows_available"] += int(n >= 2 * ns)
            summary["cap_8x_rows_available"] += int(n >= 8 * ns)
            summary["prefix_present_target_incomplete"] += int(2 * ns <= n < 8 * ns)
            cap = min(end, start + 8 * ns)
            in_cap[start:cap] = True
            in_target[min(end, start + 2 * ns):cap] = True
            summary["blocks_with_a_ninth_cue_occurrence_in_cap"] += int(
                np.any(iteration[start:cap] >= 9))
            if n >= 8 * ns:
                cycles = cue[start:cap].reshape(8, ns)
                summary["complete_caps_with_eight_balanced_cycles"] += int(
                    all(len(np.unique(cycle)) == ns for cycle in cycles))
        seq = cue[row]
        distinct, repeats = np.unique(seq, return_counts=True)
        summary["blocks_below_9_per_cue"] += int(len(distinct) < ns or min(repeats) < 9)
        summary["blocks_above_15_for_a_cue"] += int(max(repeats) > 15)
        summary["blocks_all_cues_15"] += int(len(distinct) == ns and min(repeats) == 15)
        summary["blocks_in_9_to_15_band_below_full_max"] += int(
            len(distinct) == ns and 9 <= min(repeats) < 15 and max(repeats) <= 15)
        if len(distinct) != ns:
            flags["cue_set_incomplete_or_excess_blocks"] += 1
        keys = x[row, 10]
        physical = [set(keys[(choice[row] == a) & np.isfinite(keys)]) for a in ACTIONS]
        if any(len(p) > 1 for p in physical) or sum(map(len, physical)) != len(set().union(*physical)):
            flags["observed_physical_mapping_conflicts_blocks"] += 1
        for stimulus in distinct:
            mask = seq == stimulus
            iterations = iteration[row][mask]
            correct_keys = action[row][mask]
            if 9 <= len(iterations) < 15:
                summary["cues_ending_at_9_to_14"] += 1
                delivered_correct = choice[row][mask] == correct_keys
                summary["cues_ending_at_9_to_14_with_3_of_last_4_correct"] += int(
                    delivered_correct[-4:].sum() >= 3)
            flags["cue_iteration_sequences_with_gaps_or_reordering"] += int(
                not np.array_equal(iterations, np.arange(1, len(iterations) + 1)))
            flags["cue_maps_not_fixed_legal_actions"] += int(
                not np.isin(correct_keys[0], ACTIONS) or np.any(correct_keys != correct_keys[0]))
            flags["cue_image_category_changes"] += int(
                len(np.unique(x[row, 5:7][mask], axis=0)) != 1)
        block_time = time[row]
        if not np.isfinite(block_time).all():
            flags["time_nonfinite_blocks"] += 1
        if np.any(np.diff(block_time) < 0):
            flags["time_reversals_within_blocks"] += 1
        summary["time_equals_one_based_trial_ordinal_blocks"] += int(
            np.array_equal(block_time, np.arange(1, n + 1)))

    evidence["structural_flags"] = dict(flags)
    evidence["block_support_by_load"] = {str(k): dict(v) for k, v in sorted(support.items())}
    evidence["load_3_6_blocks_per_person_histograms"] = {
        str(ns): dict(Counter(
            int(np.sum((person[starts] == p) & (load[starts] == ns))) for p in people))
        for ns in (3, 6)
    }
    absent = (np.isfinite(choice) & (choice <= 0)) | np.isnan(choice)
    responded = np.isin(choice, ACTIONS)
    delta = np.diff(time)
    evidence["time_raw_quantiles"] = quantiles(time)
    evidence["time_raw_within_block_delta_quantiles"] = quantiles(delta[pair_present])
    evidence["time_ties_within_blocks"] = int((pair_present & (delta == 0)).sum())
    for label, pair in {
        "after_candidate_omission": pair_present & absent[:-1],
        "after_response": pair_present & responded[:-1],
    }.items():
        evidence[label] = {
            "next_retained_opportunities": int(pair.sum()),
            "next_same_cue": int((pair & (cue[:-1] == cue[1:])).sum()),
            "next_same_cue_iteration_advances": int(
                (pair & (cue[:-1] == cue[1:]) & (iteration[1:] == iteration[:-1] + 1)).sum()),
            "next_trial_delta_time_raw": quantiles(delta[pair]),
        }
    evidence["response_diagnostics"] = {
        "full_matrix": summarize_responses(x),
        "early_8x_cap_load_3_6": summarize_responses(x[in_cap]),
        "target_2x_to_8x_load_3_6": summarize_responses(x[in_target]),
        "target_by_load": {str(ns): summarize_responses(x[in_target & (load == ns)]) for ns in (3, 6)},
    }
    return evidence


def fixture():
    rows = []
    for block, load in ((1, 3), (2, 6)):
        for i in range(load * 9):
            cue = i % load + 1
            action = (cue - 1) % 3 + 1
            choice = action
            if block == 1 and i == 7:
                choice = 0
            if block == 1 and i == 8:
                choice = action % 3 + 1
            key = 40 + choice if choice else 0
            feedback = int(choice == action)
            rt = .45 if choice else -1
            rows.append([1, block, load, 1 + i * 2.25, cue, cue + 30, 20,
                         i // load + 1, action, choice, key, feedback, feedback, rt, 0, 0, 0])
    return np.asarray(rows, dtype=np.float64)


def packed(matrix, **extra):
    f = io.BytesIO()
    savemat(f, {"expe_data": matrix, **extra}, do_compression=True)
    return f.getvalue()


def expect_stop(call, explanation):
    try:
        call()
    except StopAudit as error:
        assert explanation in str(error)
    else:
        raise AssertionError(f"expected stop: {explanation}")


def self_test():
    matrix = fixture()
    raw = packed(matrix)
    digest = sha1_blob(raw)
    envelope = json.dumps({"encoding": "base64", "content": base64.b64encode(raw).decode(),
                           "sha": digest, "size": len(raw)}).encode()
    for body in (raw, envelope):
        file_evidence = {}
        verified = pinned_mat(body, file_evidence, len(raw), digest)
        parsed = decode_mat(verified, file_evidence)
        assert np.array_equal(parsed, matrix[:, :14])
        assert file_evidence["decoded"]["matrix_bytes"] == matrix.nbytes
    expect_stop(lambda: pinned_mat(raw, {}, len(raw), "0" * 40), "blob mismatch")
    expect_stop(lambda: pinned_mat(b"x" * (MAX_BODY + 1), {}), "exceeds frozen cap")
    expect_stop(lambda: decode_mat(b"not a mat", {}), "MATLAB level-5")
    expect_stop(lambda: decode_mat(packed(matrix, extra=np.array([[1]])), {}), "one variable")
    expect_stop(lambda: decode_mat(packed(matrix[:, :16]), {}), "dimensions")
    diagnostics = summarize_opportunities(parsed)
    json.dumps(diagnostics, allow_nan=False)
    assert diagnostics["trial_rows"] == diagnostics["distinct_person_block_cue_iterations"] == 81
    assert not any(diagnostics["structural_flags"].values())
    for ns in ("3", "6"):
        assert diagnostics["block_support_by_load"][ns]["complete_caps_with_eight_balanced_cycles"] == 1
        assert diagnostics["block_support_by_load"][ns]["blocks_with_a_ninth_cue_occurrence_in_cap"] == 0
    assert diagnostics["after_candidate_omission"]["next_retained_opportunities"] == 1
    assert diagnostics["time_raw_within_block_delta_quantiles"]["median"] == 2.25
    target = diagnostics["response_diagnostics"]["target_2x_to_8x_load_3_6"]
    assert (target["rows"], target["responded_correct"], target["responded_wrong"],
            target["candidate_omissions"], target["correctness_flag_mismatches"]) == (54, 52, 1, 1, 0)
    corrupt = parsed.copy()
    corrupt[7, 7] += 1        # a timeout row still owns its cue iteration
    corrupt[8, 11] = 1       # a known wrong key cannot be recorded as correct
    corrupt[9, 3] = 0        # clock reversal
    corrupt[10, 8] = 3       # change the hidden map for one cue
    bad = summarize_opportunities(corrupt)
    for flag in ("cue_iteration_sequences_with_gaps_or_reordering", "time_reversals_within_blocks",
                 "cue_maps_not_fixed_legal_actions"):
        assert bad["structural_flags"][flag] == 1
    assert bad["response_diagnostics"]["full_matrix"]["correctness_flag_mismatches"] >= 1
    return {"synthetic_only": True, "source_trial_files_read": 0,
            "known_answer_checks": [
                "raw and base64 envelope integrity", "header and size guards",
                "one variable and 17 columns before decode", "ordered opportunity and timeout",
                "target correct/wrong/omission counts", "ordinal, key map, clock and feedback corruption",
            ], "known_target": {key: target[key] for key in
                                ("rows", "responded_correct", "responded_wrong", "candidate_omissions")}}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("body", type=Path, nargs="?")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--projection", type=Path,
                    help="Optional first 14 columns as NPY for a lawful subsequent source fit")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test == (args.body is not None):
        ap.error("provide the exact source body or --self-test")
    if args.self_test and args.projection is not None:
        ap.error("synthetic controls never save trial arrays")
    evidence = {"started_utc": datetime.now(timezone.utc).isoformat()}
    start = perf_counter()
    status = 0
    try:
        if args.self_test:
            evidence["synthetic_controls"] = self_test()
        else:
            with args.body.open("rb") as f:
                body = f.read(MAX_BODY + 1)
            source = evidence.setdefault("source", {})
            raw = pinned_mat(body, source)
            behavior = decode_mat(raw, source)
            evidence["opportunities"] = summarize_opportunities(behavior)
            if args.projection:
                with args.projection.open("xb") as f:
                    np.save(f, behavior, allow_pickle=False)
                evidence["projection_bytes"] = args.projection.stat().st_size
            evidence["stage_a_pass"] = None
            evidence["interpretation_required"] = (
                "Inspect aggregate results and source protocol before deciding compatibility. "
                "This report does not certify deployed assignment or omitted RTs."
            )
    except (ValueError, OSError, TypeError, KeyError, NotImplementedError) as error:
        evidence["stop"] = f"{type(error).__name__}: {error}"
        status = 1
    usage = resource.getrusage(resource.RUSAGE_SELF)
    evidence["resources"] = {"user_seconds": usage.ru_utime, "system_seconds": usage.ru_stime,
                             "audit_wall_seconds": perf_counter() - start,
                             "peak_rss_bytes": usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)}
    report = json.dumps(evidence, indent=2, allow_nan=False)
    if args.report:
        args.report.write_text(report + "\n")
    print(report)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
