#!/usr/bin/env python3
"""Independent, offline scalar reconstruction; no author estimator import."""
import csv
import datetime as dt
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import re
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AUTHOR = ROOT / "lab/tasks/molecular-correspondence-2026-10-31"
SOURCES = AUTHOR / "sources"
OLD = ROOT / "campaigns/byrnes_todo_2026-10-28"
PERMS = tuple(itertools.permutations(range(3)))
RESERVE = 70_000_000
CAP = 100_000_000
DEADLINE = dt.datetime(2026, 10, 31, 20, 13, 10, 599000, tzinfo=dt.timezone.utc)
START = time.monotonic()
READS = []
REPLAY = "--replay" in sys.argv


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def check_resources():
    # Scientific work cannot continue automatically after this assignment.
    if not REPLAY and dt.datetime.now(dt.timezone.utc) >= DEADLINE:
        raise RuntimeError("Registered deadline reached")
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = peak if sys.platform == "darwin" else peak * 1024
    if peak_bytes > 1_000_000_000:
        raise RuntimeError("Peak RSS cap exceeded")
    return peak_bytes


def read_bytes(path):
    check_resources()
    path = Path(path).resolve()
    allowed = path.is_relative_to(AUTHOR) or path.is_relative_to(HERE)
    allowed = allowed or path in {
        OLD / "data/atlas/matched_clusters_scviCorPruned.tsv",
        OLD / "data/atlas/human_mouse_corresponding_clusters.txt",
        OLD / "data/atlas/cluster_annotations_and_statistics.txt",
        OLD / "sources/atlas/05_match_clusters.R",
        OLD / "sources/atlas/cluster_matching_functions.R",
    }
    if not allowed:
        raise ValueError("Unlisted scientific input: " + str(path))
    size = path.stat().st_size
    if RESERVE + sum(r["read_bytes"] + r["decoded_utf8_bytes"] for r in READS) + 2 * size > CAP:
        raise RuntimeError("Read/decoded cap would be exceeded")
    data = path.read_bytes()
    READS.append({"path": str(path.relative_to(ROOT)), "read_bytes": len(data), "decoded_utf8_bytes": 0})
    return data


def read_text(path):
    data = read_bytes(path)
    text = data.decode("utf-8")
    READS[-1]["decoded_utf8_bytes"] = len(text.encode("utf-8"))
    return text


def read_json(path):
    return json.loads(read_text(path))


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def accounting(stage):
    measured = sum(r["read_bytes"] + r["decoded_utf8_bytes"] for r in READS)
    save("ACCOUNTING_" + stage.upper() + ".json", {
        "stage": stage, "completed_utc": utcnow(), "elapsed_process_seconds": time.monotonic() - START,
        "instrumented_read_and_decoded_bytes": measured, "reads": READS,
        "shared_whole_review_context_runtime_code_output_reserve_bytes": RESERVE,
        "note": "Reserve shared across stages; final accounting adds exact stage reads once. No OS/network meter.",
        "peak_rss_bytes": check_resources(), "python": sys.version,
        "scientific_processes_at_once": 1, "third_party_numerical_imports": [], "new_public_requests": 0,
    })


def load_tables():
    names = ("pomc_lepr_gpcr_table.txt", "pomc_glp1r_gpcr_table.txt", "pomc_glipr1_gpcr_table.txt", "agrp_gpcr_table.txt")
    tables = []
    for name in names:
        reader = csv.DictReader(io.StringIO(read_text(SOURCES / name)))
        fields = reader.fieldnames
        human = [f for f in fields if f.startswith("C4-")]
        mouse = [f for f in fields if f.startswith("C465-")]
        assert len(human) == 1 and len(mouse) >= 1
        rows = list(reader)
        by_pair = {(r["gene"], r["mouse_gene"]): r for r in rows}
        assert len(by_pair) == len(rows), "Duplicated source ortholog pair"
        for r in rows:
            assert all(math.isfinite(float(r[k])) and float(r[k]) >= 0 for k in human + mouse + ["expr_human_all", "expr_mouse_all"])
        tables.append({"file": name, "human": human[0], "mice": mouse, "rows": rows, "by_pair": by_pair})
    return tables


def extract(tables, genes):
    h = [[float(t["by_pair"][g][t["human"]]) for g in genes] for t in tables[:3]]
    m = [[float(t["by_pair"][g][t["mice"][0]]) for g in genes] for t in tables[:3]]
    hg = [float(tables[0]["by_pair"][g]["expr_human_all"]) for g in genes]
    mg = [float(tables[0]["by_pair"][g]["expr_mouse_all"]) for g in genes]
    return h, m, hg, mg


def average(values):
    values = list(values)
    return math.fsum(values) / len(values)


def centered(matrix):
    means = [average(row[j] for row in matrix) for j in range(len(matrix[0]))]
    return [[x - means[j] for j, x in enumerate(row)] for row in matrix], means


def loss(h, m, perm):
    return average((h[i][j] - m[perm[i]][j]) ** 2 for i in range(3) for j in range(len(h[0])))


def evaluate(h, m, hg, mg):
    hc, hm = centered(h)
    mc, mm = centered(m)
    class_baseline = average(x * x for row in hc for x in row)
    mouse_variance = average(x * x for row in mc for x in row)
    global_baseline = average((h[i][j] - hg[j]) ** 2 for i in range(3) for j in range(len(hg)))
    corrected = [[hg[j] + row[j] - mg[j] for j in range(len(hg))] for row in m]
    all_losses = [{"permutation": list(p), "raw_mse": loss(h, m, p),
                   "centered_mse": loss(hc, mc, p), "global_corrected_mse": loss(h, corrected, p)} for p in PERMS]
    observed = all_losses[0]
    rank = 1 + sum(x["centered_mse"] < observed["centered_mse"] - 1e-14 for x in all_losses)
    species_offset = average((hm[j] - mm[j]) ** 2 for j in range(len(hg)))
    global_offset = average((hm[j] - mm[j] - hg[j] + mg[j]) ** 2 for j in range(len(hg)))
    per_gene = []
    for j in range(len(hg)):
        hv = average(hc[i][j] ** 2 for i in range(3))
        mv = average(mc[i][j] ** 2 for i in range(3))
        cov = average(hc[i][j] * mc[i][j] for i in range(3))
        err = average((hc[i][j] - mc[i][j]) ** 2 for i in range(3))
        per_gene.append({"human_centered_variance": hv, "mouse_centered_variance": mv,
                         "cross_species_covariance": cov, "published_centered_mse": err,
                         "class_baseline_minus_published_mse": hv - err,
                         "gain_from_covariance_variance": 2 * cov - mv})
    residuals = {
        "raw_centered_offset_max_abs": max(abs(x["raw_mse"] - x["centered_mse"] - species_offset) for x in all_losses),
        "global_centered_offset_max_abs": max(abs(x["global_corrected_mse"] - x["centered_mse"] - global_offset) for x in all_losses),
        "permutation_mean_variance_sum_abs": abs(average(x["centered_mse"] for x in all_losses) - class_baseline - mouse_variance),
        "gene_gain_decomposition_max_abs": max(abs(x["class_baseline_minus_published_mse"] - x["gain_from_covariance_variance"]) for x in per_gene),
    }
    assert max(residuals.values()) < 1e-12
    return {"published": observed, "class_baseline_mse": class_baseline,
            "class_absolute_gain": class_baseline - observed["centered_mse"],
            "class_fractional_gain": 1 - observed["centered_mse"] / class_baseline,
            "global_baseline_mse": global_baseline,
            "global_absolute_gain": global_baseline - observed["global_corrected_mse"],
            "global_fractional_gain": 1 - observed["global_corrected_mse"] / global_baseline,
            "published_rank_out_of_six": rank, "all_permutations": all_losses,
            "mouse_centered_variance": mouse_variance, "per_gene": per_gene,
            "mean_permutation_centered_mse": average(x["centered_mse"] for x in all_losses),
            "published_reduction_from_mean_permutation": 1 - observed["centered_mse"] / average(x["centered_mse"] for x in all_losses),
            "species_mean_offset": species_offset, "global_species_mean_offset": global_offset,
            "numerical_invariants_abs_residual": residuals}


def pins():
    manifest = read_json(AUTHOR / "SOURCE_MANIFEST.json")
    tree = read_json(SOURCES / "hypomap_tree.json")
    blob_by_path = {x["path"]: x for x in tree["tree"] if x.get("type") == "blob"}
    source_results = []
    for row in manifest:
        data = read_bytes(SOURCES / row["file"])
        sha = hashlib.sha256(data).hexdigest()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        tree_path = row["url"].split("29599fcb13a74a908c986ad69d68fc3e4a3cf6d0/")[-1]
        entry = blob_by_path.get(tree_path)
        result = {"file": row["file"], "bytes": len(data), "sha256": sha,
                  "manifest_size_match": len(data) == row["application_bytes"], "manifest_sha256_match": sha == row["sha256"],
                  "computed_git_blob_sha1": blob, "tree_path": tree_path if entry else None,
                  "tree_blob_match": blob == entry["sha"] if entry else None,
                  "tree_size_match": len(data) == entry["size"] if entry else None}
        assert result["manifest_size_match"] and result["manifest_sha256_match"]
        if row["tree_verified"]:
            assert result["tree_blob_match"] and result["tree_size_match"]
        source_results.append(result)
    artifacts = []
    for row in read_json(AUTHOR / "ARTIFACT_MANIFEST.json")["files"]:
        data = read_bytes(AUTHOR / row["path"])
        result = {"path": row["path"], "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        result["size_match"] = len(data) == row["bytes"]
        result["sha256_match"] = result["sha256"] == row["sha256"]
        assert result["size_match"] and result["sha256_match"]
        artifacts.append(result)
    old = []
    for name in ("05_match_clusters.R", "cluster_matching_functions.R"):
        data = read_bytes(OLD / "sources/atlas" / name)
        path = "merge_human_mouse_neurons/" + name
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        entry = blob_by_path[path]
        old.append({"path": str((OLD / "sources/atlas" / name).relative_to(ROOT)), "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(), "tree_blob_match": blob == entry["sha"]})
    save("PINS.json", {"completed_utc": utcnow(), "source_pins": source_results,
                       "frozen_artifacts": artifacts, "old_source_helpers": old,
                       "no_original_files_written": True})


def base():
    protocol = read_text(AUTHOR / "PROTOCOL.md")
    panel_text = re.search(r"Fixed target set .*?: (.*?)\. This includes", protocol).group(1)
    panel = set(panel_text.split(", "))
    assert len(panel) == 54
    xf = read_json(SOURCES / "feature_set_cross_species.json")
    hf = read_json(SOURCES / "feature_set.json")
    assert len(xf) == len(set(xf)) and len(hf) == len(set(hf))
    tables = load_tables()
    common = sorted(set.intersection(*(set(t["by_pair"]) for t in tables[:3])))
    assert len(common) == 5
    h, m, hg, mg = extract(tables, common)
    all_score = evaluate(h, m, hg, mg)
    target_indices = [j for j, pair in enumerate(common) if pair[0] in panel]
    target_genes = [common[j] for j in target_indices]
    assert len(target_genes) == 4
    target_score = evaluate(*extract(tables, target_genes))
    edges_data = read_text(OLD / "data/atlas/matched_clusters_scviCorPruned.tsv")
    edge_rows = list(csv.DictReader(io.StringIO(edges_data), delimiter="\t"))
    inv = read_json(AUTHOR / "SOURCE_INVENTORY.json")["matched_clusters_scviCorPruned.tsv"]
    assert hashlib.sha256(edges_data.encode()).hexdigest() == inv["sha256"]
    matches = []
    for t in tables[:3]:
        edges = sorted([r for r in edge_rows if r["from"] == t["human"]], key=lambda x: -float(x["similarity"]))
        ordered = [r["to"] for r in edges]
        assert ordered == t["mice"], (ordered, t["mice"])
        matches.append({"human": t["human"], "source_mouse_columns": t["mice"],
                        "edges_descending_similarity": [{"mouse": r["to"], "similarity": float(r["similarity"])} for r in edges]})
    ratio_checks, global_values = [], {}
    cluster_values, ratios_finite, ratios_infinite = 0, 0, 0
    for t in tables:
        for pair, row in t["by_pair"].items():
            x, y = float(row[t["human"]]), float(row[t["mice"][0]])
            expected = math.log2(x / y) if x > 0 and y > 0 else (-math.inf if x == 0 and y > 0 else math.inf)
            actual = float(row["pct_ratio_adj"])
            diff = abs(actual - expected) if math.isfinite(expected) else None
            assert (diff is not None and diff < 1e-12) or actual == expected
            ratios_finite += math.isfinite(expected)
            ratios_infinite += not math.isfinite(expected)
            ratio_checks.append({"table": t["file"], "pair": pair, "source_ratio_string": row["pct_ratio_adj"], "absolute_error_if_finite": diff})
            gv = (float(row["expr_human_all"]), float(row["expr_mouse_all"]))
            if pair in global_values:
                assert global_values[pair] == gv
            global_values[pair] = gv
            cluster_values += 1 + len(t["mice"])
    hc, _ = centered(h)
    control_positive = [loss(hc, hc, p) for p in PERMS]
    mouse_mean = [average(row[j] for row in m) for j in range(len(common))]
    flat, _ = centered([mouse_mean[:] for _ in range(3)])
    control_negative = [loss(hc, flat, p) for p in PERMS]
    assert control_positive[0] == 0 and all(x > 0 for x in control_positive[1:])
    assert max(control_negative) == min(control_negative)
    assert abs(control_negative[0] - all_score["class_baseline_mse"]) < 1e-14
    pins()
    result = {
        "completed_utc": utcnow(), "implementation": "independent Python standard-library scalar loops and math.fsum; no author estimator import",
        "target_panel": sorted(panel), "cross_species_feature_count": len(xf), "human_feature_count": len(hf),
        "cross_species_target_members": sorted(panel & set(xf)), "human_target_members": sorted(panel & set(hf)),
        "target_members_either": sorted(panel & (set(xf) | set(hf))),
        "common_source_pairs": common, "common_pairs_in_cross_species_features": [g for g in common if g[0] in xf],
        "common_pairs_in_human_features": [g for g in common if g[0] in hf],
        "human_rows": [t["human"] for t in tables[:3]], "mouse_rows": [t["mice"][0] for t in tables[:3]],
        "H": h, "M_leading_source": m, "H_global": hg, "M_global": mg,
        "five_common_receptors": all_score, "four_fixed_target_pairs": target_genes, "four_fixed_targets": target_score,
        "mapping_source_order": matches, "mapping_inventory": {"edges": len(edge_rows), "human_clusters": len(set(r["from"] for r in edge_rows)), "mouse_clusters": len(set(r["to"] for r in edge_rows))},
        "source_table_exposure": {"rows": sum(len(t["rows"]) for t in tables), "distinct_gene_pairs": len(global_values),
                                  "cluster_expression_values": cluster_values, "global_values_including_repeats": 2 * sum(len(t["rows"]) for t in tables), "source_ratios": len(ratio_checks)},
        "source_tables_all_columns_and_rows": [{k: v for k, v in t.items() if k != "by_pair"} for t in tables],
        "source_ratio_checks": {"formula": "log2(H_cluster / leading_M_cluster), not global-adjusted and not percent detection", "finite": ratios_finite, "infinite": ratios_infinite,
                                "max_finite_absolute_error": max(r["absolute_error_if_finite"] for r in ratio_checks if r["absolute_error_if_finite"] is not None), "every_row": ratio_checks},
        "controls": {"human_self_centered_losses": control_positive, "flat_mouse_centered_losses": control_negative, "passed": True},
        "biological_intervals_or_pvalues": "none; subtypes/selected receptors are not donor replicates",
    }
    save("RECONSTRUCTION.json", result)
    accounting("base")
    print(json.dumps({"saved": "RECONSTRUCTION.json", "feature_overlap": [len(result["cross_species_target_members"]), len(result["human_target_members"]), len(result["target_members_either"])],
                      "five_gene_centered_mse": all_score["published"]["centered_mse"], "class_gain": all_score["class_fractional_gain"], "rank": all_score["published_rank_out_of_six"],
                      "global_gain": all_score["global_fractional_gain"], "pins_and_controls": "pass"}))


def influence():
    plan = read_text(HERE / "PLAN.md")
    assert "One contrary diagnostic: receptor influence" in plan
    tables = load_tables()
    common = sorted(set.intersection(*(set(t["by_pair"]) for t in tables[:3])))
    original = evaluate(*extract(tables, common))
    cases = []
    for omitted in common:
        kept = [g for g in common if g != omitted]
        cases.append({"omitted_source_pair": omitted, "retained_pairs": kept, "score": evaluate(*extract(tables, kept))})
    save("RECEPTOR_INFLUENCE.json", {"completed_utc": utcnow(), "plan_sha256": hashlib.sha256(plan.encode()).hexdigest(),
                                    "status": "predeclared postvalidation sensitivity on already consumed selected tables",
                                    "original_all_five": original, "all_five_single_receptor_deletions": cases,
                                    "selection": "all deletions retained; none adopted; leading mouse convention unchanged"})
    accounting("influence")
    print(json.dumps({"saved": "RECEPTOR_INFLUENCE.json", "all_deletions": [{"omitted": c["omitted_source_pair"][0], "class_gain": c["score"]["class_fractional_gain"],
                                                                                      "global_gain": c["score"]["global_fractional_gain"], "rank": c["score"]["published_rank_out_of_six"]} for c in cases]}))


def summarize():
    result = read_json(HERE / "RECONSTRUCTION.json")
    influence_result = read_json(HERE / "RECEPTOR_INFLUENCE.json")
    pin_result = read_json(HERE / "PINS.json")
    base_account = read_json(HERE / "ACCOUNTING_BASE.json")
    influence_account = read_json(HERE / "ACCOUNTING_INFLUENCE.json")
    score = result["five_common_receptors"]
    gene_rows = [{"gene": pair[0], **row} for pair, row in zip(result["common_source_pairs"], score["per_gene"])]
    summary = {
        "completed_utc": utcnow(),
        "feature_memberships": [len(result[k]) for k in ("cross_species_target_members", "human_target_members", "target_members_either")],
        "five_common_receptors": {k: v for k, v in score.items() if k not in ("per_gene", "all_permutations")},
        "four_fixed_targets": {k: v for k, v in result["four_fixed_targets"].items() if k not in ("per_gene", "all_permutations")},
        "per_gene": gene_rows,
        "all_five_deletions": [{"omitted": c["omitted_source_pair"][0],
                                **{k: v for k, v in c["score"].items() if k not in ("per_gene", "all_permutations")}}
                               for c in influence_result["all_five_single_receptor_deletions"]],
        "source_ratio_checks": {k: v for k, v in result["source_ratio_checks"].items() if k != "every_row"},
        "source_pin_count": len(pin_result["source_pins"]),
        "source_git_blob_checks": sum(p["tree_blob_match"] is True for p in pin_result["source_pins"]),
        "frozen_artifact_count": len(pin_result["frozen_artifacts"]),
        "old_helper_git_blob_checks": sum(p["tree_blob_match"] for p in pin_result["old_source_helpers"]),
        "mapping_source_order": result["mapping_source_order"],
        "controls": result["controls"],
        "earlier_instrumented_read_decoded_bytes": base_account["instrumented_read_and_decoded_bytes"] + influence_account["instrumented_read_and_decoded_bytes"],
        "earlier_peak_rss_bytes": max(base_account["peak_rss_bytes"], influence_account["peak_rss_bytes"]),
    }
    # Save every permutation for each fixed panel and all predeclared deletions.
    with (HERE / "PERMUTATIONS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["case", "mouse_source_rows_for_human_373_374_375", "raw_mse", "centered_mse", "global_corrected_mse"])
        cases = [("all_five", score), ("four_fixed_targets", result["four_fixed_targets"])]
        cases.extend(("omit_" + c["omitted_source_pair"][0], c["score"]) for c in influence_result["all_five_single_receptor_deletions"])
        for name, case in cases:
            for row in case["all_permutations"]:
                writer.writerow([name, "/".join(str((122, 125, 124)[i]) for i in row["permutation"]), row["raw_mse"], row["centered_mse"], row["global_corrected_mse"]])
    save("SUMMARY.json", summary)
    accounting("summary")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    args = [arg for arg in sys.argv[1:] if arg != "--replay"]
    if args == ["base"]:
        base()
    elif args == ["influence"]:
        influence()
    elif args == ["summary"]:
        summarize()
    else:
        raise SystemExit("usage: reconstruct.py {base|influence|summary} [--replay]")
