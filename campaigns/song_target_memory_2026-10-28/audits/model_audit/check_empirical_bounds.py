"""Independent exhaustive labelled-assignment audit of empirical summary bounds."""
from pathlib import Path
import csv
import hashlib
import itertools
import json
import math
import statistics

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]


def labelled_assignment_bounds(values, birds, cap):
    best_low = (float("inf"), None)
    best_high = (-float("inf"), None)
    count = 0
    for labels in itertools.product(range(birds), repeat=len(values)):
        groups = [[values[i] for i, label in enumerate(labels) if label == b] for b in range(birds)]
        if any(len(g) == 0 or len(g) > cap for g in groups):
            continue
        count += 1
        score = statistics.fmean(statistics.fmean(g) for g in groups)
        if score < best_low[0]:
            best_low = (score, labels)
        if score > best_high[0]:
            best_high = (score, labels)
    assert count % math.factorial(birds) == 0
    return {"maximum_elements_per_bird": cap, "labelled_assignments": count,
            "unlabelled_partitions": count//math.factorial(birds),
            "lower_ms": best_low[0], "upper_ms": best_high[0],
            "lower_attaining_labels": best_low[1], "upper_attaining_labels": best_high[1]}


def analytic_unrestricted(values, birds):
    v = sorted(values)
    large_group = len(v)-birds+1
    lower = (sum(v[:birds-1])+statistics.fmean(v[birds-1:]))/birds
    upper = (statistics.fmean(v[:large_group])+sum(v[large_group:]))/birds
    return [lower, upper]


def main():
    digitization = BASE / "audits/zhao_source/figure5_duration_digitization_corrected.json"
    figure = json.loads(digitization.read_text())["summary"]
    o = figure["opto_only_300"]["duration_values_ms"]
    c = figure["natural_plus_opto_300"]["duration_values_ms"]
    opto = {str(cap): labelled_assignment_bounds(o, 4, cap) for cap in (2, 3, 4)}
    conflict = labelled_assignment_bounds(c, 3, 2)
    analytic = analytic_unrestricted(o, 4)
    assert abs(analytic[0]-opto["4"]["lower_ms"]) < 1e-10
    assert abs(analytic[1]-opto["4"]["upper_ms"]) < 1e-10
    differences = {}
    for cap, ob in opto.items():
        differences[cap] = [conflict["lower_ms"]-ob["upper_ms"], conflict["upper_ms"]-ob["lower_ms"]]
    # Independent bit-mask partition of the 11 pooled long table entries into4+7.
    table_path = BASE / "audits/zhao_source/table_s1_transcription.csv"
    rows = list(csv.DictReader(table_path.open()))
    short = [float(r["element_mean_ms"]) for r in rows if r["protocol"] == "four_50ms"]
    long = [float(r["element_mean_ms"]) for r in rows if r["protocol"] == "single_300ms_pooled"]
    subset_results = []
    for mask in range(1 << len(long)):
        if bin(mask).count("1") != 4:
            continue
        conflict_values = [v for i, v in enumerate(long) if (mask >> i) & 1]
        only_values = [v for i, v in enumerate(long) if not ((mask >> i) & 1)]
        mc, mo = statistics.median(conflict_values), statistics.median(only_values)
        subset_results.append([mo, mc, mc-mo])
    assert len(subset_results) == math.comb(11, 4) == 330
    extraction_bound = 2 * 400 / 121 * 4
    result = {"method": "Exhaust all labelled assignments with Python product; use standard-library means; divide count by k!; no root analysis imported",
              "figure_sha256": hashlib.sha256(digitization.read_bytes()).hexdigest(),
              "opto_bounds_by_capacity": opto,
              "conflict_bounds": conflict,
              "unrestricted_opto_analytic_bounds": analytic,
              "conflict_minus_opto_bounds_by_capacity": differences,
              "source_consistent_opto_maximum_elements": 3,
              "source_constraint": "Zhao main P10:300ms opto-tutored birds produced1–3song elements; confirmed by source agent and original cached text",
              "source_consistent_bounds_plus_extraction_error_ms": [differences["3"][0]-extraction_bound,
                                                                      differences["3"][1]+extraction_bound],
              "table_partition_count": len(subset_results),
              "table_partition_median_ranges_ms": [[min(r[j] for r in subset_results), max(r[j] for r in subset_results)] for j in range(3)],
              "support_separation_ms": min(long)-max(short),
              "main_text_calibration_prediction_ms": 323.,
              "main_text_calibration_conflict_median_residual_ms": statistics.median(c)-323.,
              "limits": "Finite observed summaries only. Unknown memberships are bounded; no population CI, family independence, or raw-rendition inference."}
    (HERE / "empirical_independent_check.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("opto_bounds_by_capacity", "conflict_bounds")}, indent=2))


if __name__ == "__main__":
    main()
