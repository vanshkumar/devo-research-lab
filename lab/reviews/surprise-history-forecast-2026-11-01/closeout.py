"""Save bounded source/exposure/resource closeout from earned review artifacts."""
import os
for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"
import datetime, hashlib, json, pathlib, platform, resource, zipfile
from xml.etree import ElementTree as ET
import numpy as np
import scipy

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "lab/tasks/surprise-history-forecast-2026-11-01"

def read(name):
    return json.loads((HERE / name).read_text())

def npz_read_bytes(path):
    with zipfile.ZipFile(path) as archive:
        return path.stat().st_size + sum(item.file_size for item in archive.infolist())

def main():
    at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    first, contrary, reconstruction, pins, control = [read(name) for name in (
        "FIRST_CALCULATION.json", "CONTRARY.json", "RECONSTRUCTION.json", "PIN_AUDIT.json", "CONTROL_AUDIT.json")]
    assert hashlib.sha256((HERE / "CONTRARY_PLAN.md").read_bytes()).hexdigest() == contrary["plan_sha256"]
    assert (HERE / "CONTRARY_PLAN.md").stat().st_mtime < datetime.datetime.fromisoformat(contrary["started_at"]).timestamp()
    assert len(reconstruction["audits"]) == 78
    assert all(a["no_short_within_block_event_gaps"] and a["hit_discrepancies"] == 0 and a["prediction_within_trial"] == 240 and a["next_onset_after_offset"] == 239 for a in reconstruction["audits"])
    registry = json.loads((ROOT / "lab/registry.json").read_text())
    pi = registry["pi"]["thread_id"]
    meta = json.loads((SOURCE / "zenodo_meta.source").read_text())
    article = ET.fromstring((SOURCE / "article.source").read_bytes())
    data = (SOURCE / "behavior_zip.source").read_bytes()
    manifest = {"at": at, "primary_work": {"url": "https://elifesciences.org/articles/46975", "doi": "10.7554/eLife.46975",
        "article_cached_license_text": ["".join(x.itertext()) for x in article.iter("license")]},
        "deposit": {"doi": "10.5061/dryad.570pf8n", "mirror_url": "https://zenodo.org/records/5034463",
            "mirror_declared_license": meta["metadata"].get("license"), "archive_bytes": len(data),
            "md5": hashlib.md5(data).hexdigest(), "sha256": hashlib.sha256(data).hexdigest()},
        "analysis_tree": "ed500ff28129c7d9a021fe167782bc07ebf7c23d",
        "task_commit": "a0b782e788f4bbf99d08a31b691556c475f7e041", "source_license": "GPL-3.0 for source approximate recurrence; empirical archive CC0; article CC-BY",
        "exposure": "All 39 full MATs and auxiliary fields already consumed; compressed ZIP/group summaries exposed before author freeze. No new acquisition, family or restored holdout.",
        "provenance_limits": "Cached source/version/blob integrity verified; original hardware execution, recruitment randomization and global novelty not certified."}
    assert manifest["deposit"]["md5"] == "235fad11706c1b93c7a12b55fcde5757"
    (HERE / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    known = {
        "first_calculation_containers_and_decode": (SOURCE / "behavior_zip.source").stat().st_size + first["decoded_MAT_bytes"] + sum(npz_read_bytes(SOURCE / name) for name in ("predictions.npz", "evaluation_truth.npz")),
        "contrary_feature_containers_and_decode": contrary["input_container_bytes"] + contrary["input_decoded_array_bytes"],
        "pin_and_source_audit_recorded_bytes": pins["recorded_bytes_read"],
        "successful_full_reconstruction_containers_and_decode": reconstruction["input_container_bytes"] + reconstruction["decoded_MAT_bytes"] + reconstruction["decoded_array_bytes"],
        "control_audit_containers_decode_and_json": control["input_container_bytes"] + control["decoded_array_bytes"] + control["control_json_bytes"],
        "failed_ID_parse_pass_conservative_charge": 45000000,
        "closeout_archive_metadata_article_and_own_artifacts_allowance": 5000000,
        "ordinary_source_text_and_report_reads_allowance": 10000000,
        "syntax_error_and_denied_or_invalid_search_reads_allowance": 1000000,
    }
    assert sum(known.values()) < 250000000 < 300000000
    peaks = {name: value["peak_rss_bytes"] for name, value in (("FIRST_CALCULATION", first), ("CONTRARY", contrary), ("PIN_AUDIT", pins), ("RECONSTRUCTION", reconstruction), ("CONTROL_AUDIT", control))}
    peaks["CLOSEOUT"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    resources = {"at": at, "review": "surprise-history-forecast-review-2026-11-01", "owner": "01a1960b-982d-7621-876b-8922220fbf29",
        "current_registry_PI": pi, "START": "2026-11-01T07:39:00Z", "first_calculation_at": first["calculated_at"],
        "hard_deadline": "2026-11-01T08:19:00Z", "last_scientific_calculation_at": control["ended_at"],
        "public_operations": 0, "ingress_bytes": 0, "new_empirical_families": 0,
        "separate_additional_read_limit_bytes": 300000000, "conservative_additional_read_charge_bytes": 250000000,
        "read_breakdown_including_failed_passes": known, "breakdown_subtotal_bytes": sum(known.values()),
        "unallocated_read_reserve_inside_charge_bytes": 250000000 - sum(known.values()),
        "read_note": "Conservative task-local file/container/decode/hash accounting, including failed and repeated passes. No RAM arithmetic traffic charge; physical I/O and runtime/import/toolhost processing are not metered.",
        "measured_process_peaks_bytes": peaks, "largest_measured_scientific_RSS_bytes": max(peaks.values()), "peak_limit_bytes": 800000000,
        "simultaneous_scientific_processes": 1, "numerical_threads": 1, "background_jobs_remaining": 0,
        "unknowns": ["Failed raw-ID-parse process peak was not captured", "Ordinary toolhost/wrapper and OS-wide peaks", "Actual physical I/O and import/runtime processing bytes"],
        "failures": ["Initial contrary.py unmatched-parenthesis SyntaxError before imports/data; corrected without a scientific-plan change", "Initial reconstruct.py ID check compared string-coded numeric IDs with integers; failed after loading features/first person. Corrected to explicit int normalization, full failed input pass charged", "Initial compound ordinary shell read blocked before execution; raw .source rg blocked before execution; later rg negative lookahead rejected by rg parser. No public operation or scientific result from these commands"],
        "author_resources_preserved": {"public_operations": 28, "empirical_families": 1, "known_received_body_bytes": 1943144,
            "charged_ingress_bytes": 10000000, "additional_read_charge_bytes": 200000000,
            "largest_measured_RSS_bytes": 272826368, "unknowns": "Failed author run/toolhost/provider wire/fanout/redirect/physical-I/O unknowns retained; no OS-wide certification"},
        "software": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__, "platform": platform.platform()},
        "compliance": "No observed measured process peak or conservative task-local charge exceeds this separate review envelope. Failed-process/OS-wide compliance is not independently certified."}
    (HERE / "RESOURCES.json").write_text(json.dumps(resources, indent=2) + "\n")
    exposure = {"at": at, "raw_people_reread": 39, "raw_rows": 18720, "eligible_updates_reconstructed": 18408,
        "all_raw_auxiliary_fields_consumed": True, "author_development_people": 20, "author_evaluation_people": 19,
        "no_restored_holdout": True, "review_conditional_control_examples_reconstructed": 2,
        "review_source_bootstrap_draws_consumed": 200,
        "author_exposure_preserved": "Compressed archive/hash and all39 published summaries before freeze; evaluation interpreted values reportedly after freeze, not an unacquired holdout. Current hashes/timestamps cannot prove historical non-access.",
        "other_protected_payloads_opened": False, "protected_closed": ["Pan20", "Flesch81/B2/B20 responses", "later HABITS", "memory targets", "four reserved worms", "Figure4_42", "optional210"],
        "source_and_author_files_written": False, "shared_records_written": False,
        "unrun": ["Remaining198 full synthetic target/refit control replays", "5% boundary sensitivity", "interval coverage", "exact continuous filtering accuracy proof", "new cohort/context/noise transfer", "neural or causal mechanism", "global priority/novelty", "historical hardware clock/deployment and unread-value proof"]}
    (HERE / "EXPOSURE.json").write_text(json.dumps(exposure, indent=2) + "\n")
    (HERE / "REPORT_DELIVERY.json").write_text(json.dumps({"at": at, "target_current_registry_PI": pi, "status": "prepared_not_yet_attempted", "allowed_attempts": 1, "model_or_thinking_overrides": False}, indent=2) + "\n")
    print(json.dumps({"recorded_conservative_subtotal_bytes": sum(known.values()), "read_charge_bytes": 250000000,
        "largest_measured_RSS_bytes": max(peaks.values()), "hit_mismatches_all_records": 0,
        "all_78_chronology_and_safe_gap_checks": True, "plan_pin_and_before_start_check": True,
        "current_registry_PI": pi, "mirror_license": manifest["deposit"]["mirror_declared_license"], "at": at}, indent=2))

if __name__ == "__main__":
    main()
