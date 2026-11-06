"""Saved-output and independent signed-contrast audit. No science rerun."""
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import platform
import resource
import sys

HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parents[1] / "tasks" / "motor-assay-identification-2026-11-02"
read_bytes = 0


def read(path):
    global read_bytes
    data = path.read_bytes()
    read_bytes += len(data)
    return data


def main():
    ref = json.loads(read(HERE / "FIRST_CALCULATION.json"))
    contrary = json.loads(read(HERE / "CONTRARY.json"))
    saved_author_manifest = json.loads(read(AUTHOR / "FINAL_AUDIT.json"))
    author_frontier = json.loads(read(AUTHOR / "CALIBRATION_FRONTIER.json"))
    author_pin_results = {}
    for name, pin in saved_author_manifest["pins"].items():
        assert Path(name).name == name
        content = read(AUTHOR / name)
        actual = hashlib.sha256(content).hexdigest()
        assert actual == pin["sha256"] and len(content) == pin["bytes"]
        author_pin_results[name] = {"bytes": len(content), "sha256": actual, "matches": True}
    author_cases = {c["direction"]: c for c in author_frontier["signed_witnesses"]}
    contrast_max_error, author_curve_max_error = 0.0, 0.0
    contrasts = []
    for case in ref["cases"]:
        # Reconstruct the original half-difference directly from the SAVED
        # generated observed cells; do not reuse the coefficient formula.
        cell = {(row["event"], row["precursor"], row["cursor"]): row for row in case["rows"]}
        curve = []
        for h in range(5):
            event_half_differences = []
            for event in (0, 1):
                positive = cell[(event, 1.5, 0.0)]["probe_path"][h]
                negative = cell[(event, -1.5, 0.0)]["probe_path"][h]
                event_half_differences.append((positive - negative) / 2)
            curve.append(event_half_differences[1] - event_half_differences[0])
        contrast_max_error = max(contrast_max_error,
                                 *(abs(x-y) for x, y in zip(curve, case["observable_curve"])))
        published = author_cases[case["direction"]]["observable_five_probe_curve_deg"]
        author_curve_max_error = max(author_curve_max_error,
                                     *(abs(x-y) for x, y in zip(curve, published)))
        assert abs(sum(curve)/5 - case["direction"] * .2) < 2e-15
        contrasts.append({"sign": case["direction"], "direct_observed_half_difference_curve": curve,
                          "mean": sum(curve)/5})
    assert contrast_max_error < 2e-15 and author_curve_max_error < 2e-15
    assert ref["critical_per_cell_bias"]["degrees"] == author_frontier["critical_cell_bias_deg"]
    assert F(ref["single_world_systematic_half_width"]["fraction"]) == F(1,10)
    assert F(ref["two_world_target_diameter"]["fraction"]) == F(1,5)
    assert contrary["shared_criterion_only"]["augmented_world_equality"] is False
    assert contrary["hand_specific_signal_mismatch_allowed"]["augmented_world_equality"] is True
    assert contrary["exact_identity_checks"] == 864
    assert contrary["hand_specific_signal_mismatch_allowed"]["maximum_hand_probability_gap"] == 0
    assert contrary["hand_specific_signal_mismatch_allowed"]["maximum_catch_probability_gap"] == 0
    own_pins = {}
    for name in ("independent_reference.py", "FIRST_CALCULATION.json", "contrary_calibration.py",
                 "CONTRARY_PREDECLARATION.md", "CONTRARY.json", "REVIEW.md", "SOURCES.md",
                 "README.md", "PROPOSED_LEARNING.md", "final_audit.py"):
        data = read(HERE / name)
        own_pins[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    result = {"generated_utc": datetime.now(timezone.utc).isoformat(),
              "all_saved_output_checks": "PASS; no independent-reference/contrary/author-code rerun",
              "direct_normalization_from_saved_cells": contrasts,
              "maximum_direct_contrast_difference": contrast_max_error,
              "maximum_author_curve_difference": author_curve_max_error,
              "critical_radius_matches_author": True,
              "author_seven_frozen_pins": author_pin_results,
              "review_code_and_output_pins": own_pins,
              "conditional_author_collection_arithmetic": {"episode_conditions": 24,
                  "index_and_probe_reaches": 144, "hand_reports": 12,
                  "extra_report_seconds": 12*.842, "matched_wait_seconds": 12*.842,
                  "additional_contrary_catch_costs": "unpriced; not an executable collection recommendation"},
              "explicit_read_bytes_this_audit": read_bytes,
              "python": sys.version.split()[0], "platform": platform.platform(),
              "max_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "empirical_raw_old_array_read_bytes": 0, "author_code_executed": False,
              "provider_runtime_and_physical_io": "UNKNOWN; explicit bytes do not certify total IO",
              "jobs_or_sessions_started": 0}
    (HERE / "FINAL_AUDIT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("generated_utc", "all_saved_output_checks",
                     "maximum_direct_contrast_difference", "maximum_author_curve_difference",
                     "explicit_read_bytes_this_audit", "max_rss_bytes_macos")}))


if __name__ == "__main__":
    main()
