#!/usr/bin/env python3
"""Reconcile earned outputs and record final resource/exposure accounting."""
import hashlib
import json
from pathlib import Path
import re

import reconstruct as audit


def every_string(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from every_string(child)
    elif isinstance(value, list):
        for child in value:
            yield from every_string(child)
    elif isinstance(value, str):
        # Saved connector blocks sometimes contain a JSON-encoded response.
        if value.lstrip().startswith(("{", "[")):
            try:
                yield from every_string(json.loads(value))
                return
            except (ValueError, TypeError):
                pass
        yield value


def main():
    independently_earned = audit.read_json(audit.HERE / "RECONSTRUCTION.json")
    author = audit.read_json(audit.AUTHOR / "COMPARISON.json")
    influence = audit.read_json(audit.HERE / "RECEPTOR_INFLUENCE.json")
    pins = audit.read_json(audit.HERE / "PINS.json")
    prior_accounts = [audit.read_json(audit.HERE / name) for name in
                      ("ACCOUNTING_BASE.json", "ACCOUNTING_INFLUENCE.json", "ACCOUNTING_SUMMARY.json")]
    # This source-pin extension is a second final verification pass. Preserve the first pass's charge.
    prior_final_path = audit.HERE / "ACCOUNTING_FINAL.json"
    if prior_final_path.exists():
        prior_accounts.append(audit.read_json(prior_final_path))
    old_inventory = audit.read_json(audit.AUTHOR / "SOURCE_INVENTORY.json")
    old_input_pins = []
    for name in ("matched_clusters_scviCorPruned.tsv", "human_mouse_corresponding_clusters.txt", "cluster_annotations_and_statistics.txt"):
        payload = audit.read_bytes(audit.OLD / "data/atlas" / name)
        digest = hashlib.sha256(payload).hexdigest()
        assert len(payload) == old_inventory[name]["bytes"] and digest == old_inventory[name]["sha256"]
        old_input_pins.append({"path": str((audit.OLD / "data/atlas" / name).relative_to(audit.ROOT)),
                               "bytes": len(payload), "sha256": digest, "source_inventory_match": True,
                               "inspection": "hash-only in this final pass; no additional donor values interpreted"})
    loss_errors, baseline_errors = [], []
    for mine_key, author_key in (("five_common_receptors", "all_five_common_receptors"),
                                  ("four_fixed_targets", "four_prespecified_targets")):
        mine, other = independently_earned[mine_key], author[author_key]
        for x, y in zip(mine["all_permutations"], other["permutations"]):
            assert x["permutation"] == y["mouse_group_for_human_row"]
            for mk, ak in (("raw_mse", "raw_mse"), ("centered_mse", "pomc_gene_centered_mse"),
                           ("global_corrected_mse", "global_abundance_adjusted_mse")):
                loss_errors.append(abs(x[mk] - y[ak]))
        baseline_errors.extend((abs(mine["class_baseline_mse"] - other["class_gene_abundance_baseline_mse"]),
                                abs(mine["global_baseline_mse"] - other["global_human_abundance_only_mse"])))
        assert mine["published_rank_out_of_six"] == other["identity_centered_rank_of_6"]
        assert abs(mine["class_fractional_gain"] * 100 - other["identity_centered_reduction_vs_class_mean_percent"]) < 1e-11
        assert abs(mine["global_fractional_gain"] * 100 - other["identity_global_adjusted_reduction_percent"]) < 1e-11
    assert len(loss_errors) == 36 and max(loss_errors + baseline_errors) < 1e-12
    # All original main vectors agree exactly; this comparison occurs after independent calculation.
    source_vectors_checked = 0
    source_by_human = {t["human"]: t for t in independently_earned["source_tables_all_columns_and_rows"][:3]}
    for row in author["source_rows"]:
        table = source_by_human[row["human_cluster"]]
        original = next(r for r in table["rows"] if r["gene"] == row["gene"] and r["mouse_gene"] == row["mouse_gene"])
        assert row["human_expression"] == float(original[table["human"]])
        assert row["mouse_first"] == table["mice"][0]
        assert row["mouse_expression"] == float(original[table["mice"][0]])
        assert row["all_mouse_expressions"] == {k: float(original[k]) for k in table["mice"]}
        source_vectors_checked += 1
    # The predeclared PTGER3 omission must equal the independently reconstructed fixed-target panel.
    ptger3 = next(c["score"] for c in influence["all_five_single_receptor_deletions"] if c["omitted_source_pair"][0] == "PTGER3")
    assert ptger3 == independently_earned["four_fixed_targets"]
    snippets, seen = [], set()
    receipts = audit.read_json(audit.AUTHOR / "WEB_RECEIPTS.json")
    for text in every_string(receipts):
        for line in text.replace("\\n", "\n").splitlines():
            if re.match(r"^L(?:28\d|29\d|30\d|31\d):", line) and line not in seen:
                snippets.append(line)
                seen.add(line)
    (audit.HERE / "SOURCE_EXCERPTS.md").write_text(
        "# Saved primary-article excerpts\n\nFrom the author's pinned WEB_RECEIPTS.json, decoded without new requests. "
        "The saved provider returned a bounded article excerpt, not a new full-text acquisition. "
        "Article: https://pmc.ncbi.nlm.nih.gov/articles/PMC11922758/ . Preserve original provider line labels.\n\n" +
        "\n".join(snippets) + "\n", encoding="utf-8")
    owned_files = ("PLAN.md", "reconstruct.py", "final_check.py", "RECONSTRUCTION.json", "RECEPTOR_INFLUENCE.json",
                   "SUMMARY.json", "PERMUTATIONS.csv", "PINS.json", "SOURCE_EXCERPTS.md")
    own_pins = []
    for name in owned_files:
        payload = audit.read_bytes(audit.HERE / name)
        own_pins.append({"file": name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    audit.save("REVIEW_ARTIFACT_PINS.json", {"files": own_pins})
    audit.accounting("final")
    measured_final = sum(r["read_bytes"] + r["decoded_utf8_bytes"] for r in audit.READS)
    measured_total = measured_final + sum(a["instrumented_read_and_decoded_bytes"] for a in prior_accounts)
    peak = max([audit.check_resources()] + [a["peak_rss_bytes"] for a in prior_accounts])
    accounting = {
        "completed_utc": audit.utcnow(), "registered_start_utc": "2026-10-31T19:38:10.599Z", "deadline_utc": audit.DEADLINE.isoformat(),
        "instrumented_scientific_file_read_and_decoded_bytes_all_four_passes": measured_total,
        "whole_review_conservative_context_source_code_runtime_output_and_failed_call_reserve_bytes": audit.RESERVE,
        "charged_additional_read_decoded_bytes": audit.RESERVE + measured_total,
        "cap_bytes": audit.CAP, "peak_instrumented_rss_bytes": peak, "rss_cap_bytes": 1_000_000_000,
        "scientific_passes": {"base": "success", "influence": "success", "summary": "success", "final": "success; original and old-source-pin extension both charged"},
        "failed_scientific_passes": 0,
        "ordinary_tool_denials": ["shell composition in file listing", "mixed existent/nonexistent STATE path search", "ordinary head of data-format TSV", "unsupported rg -o option", "ordinary cat of own generated CSV"],
        "failed_call_charges": "All included in conservative reserve; denied calls produced no new scientific observations.",
        "new_public_requests": 0, "new_network_ingress_bytes": 0, "scientific_processes_at_once": 1, "numerical_threads": 1,
        "measurement_limit": "Exact instrumented file reads/UTF-8 decoded-byte charges plus conservative reserve; not an OS/network/token meter.",
        "author_read_decoded_bytes_preserved": 191_451_239, "author_ingress_bytes_preserved": 20_165_421, "author_requests_preserved": 20,
        "author_plus_review_current_branch_read_decoded_bytes": 191_451_239 + audit.RESERVE + measured_total,
        "historical_hypomap_range_bytes_unchanged": 3_277_786_552, "memory_lineage_bytes_unchanged": 7_774_826_112,
        "exposure": {"consumed_gene_pair_rows_reread_each_table_pass": 70, "distinct_pairs": 40, "cluster_expression_values": 229,
                     "global_expression_values_with_repeats": 140, "source_ratios": 70,
                     "interpretation": "Existing selected summaries reread; no new independent units, donors, raw atlas cells or holdouts.",
                     "raw_atlas_or_range_cache_payloads": 0, "new_donor_identifiers": 0,
                     "protected": "Pan20/Flesch81/B2/B20/later HABITS/memory targets/four reserved baseline worms unopened;19 heat animals remain consumed."},
        "jobs": 0,
    }
    assert accounting["charged_additional_read_decoded_bytes"] < audit.CAP
    audit.save("ACCOUNTING.json", accounting)
    final = {"completed_utc": audit.utcnow(), "all_checks_pass": True,
             "independently_reconstructed_losses_compared_afterwards": len(loss_errors),
             "max_absolute_loss_difference_from_author": max(loss_errors), "max_absolute_baseline_difference_from_author": max(baseline_errors),
             "complete_source_rows_with_all_mouse_columns_compared": source_vectors_checked,
             "fixed_target_panel_equals_predeclared_PTGER3_omission": True,
             "source_manifest_SHA256_checks": len(pins["source_pins"]), "source_git_blob_checks": sum(x["tree_blob_match"] is True for x in pins["source_pins"]),
             "frozen_artifact_checks": len(pins["frozen_artifacts"]), "old_helper_git_blob_checks": sum(x["tree_blob_match"] for x in pins["old_source_helpers"]),
             "old_small_source_inventory_pins": old_input_pins,
             "source_excerpt_lines": len(snippets), "accounting": accounting}
    audit.save("FINAL_CHECK.json", final)
    print(json.dumps({k: v for k, v in final.items() if k != "accounting"}, indent=2))
    print(json.dumps({"charged_read_decoded_bytes": accounting["charged_additional_read_decoded_bytes"], "peak_rss_bytes": peak}))


if __name__ == "__main__":
    main()
