"""Record-only manifest/resource closeout; no simulation or outcome calculation."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import resource

HERE = Path(__file__).resolve().parent


def read_json(name):
    return json.loads((HERE/name).read_text())


def save(name, obj):
    (HERE/name).write_text(json.dumps(obj, indent=2)+"\n")


def main():
    utc = datetime.now(timezone.utc).isoformat()
    first = read_json("FIRST_CALCULATION.json")
    mainrun = read_json("MAIN_RUN.json")
    summary = read_json("SUMMARY.json")
    audit = read_json("POSTVALIDATION_AUDIT.json")
    ref = read_json("REFERENCE_CHECKS.json")
    frozen = read_json("FREEZE.json")
    manifest = {}
    for path in sorted(HERE.iterdir()):
        if not path.is_file() or path.name in {"MANIFEST.json", "FINAL_AUDIT.json", "COMMUNICATION_STATUS.json", "RESOURCES.json", "EXPOSURE.json"}:
            continue
        raw = path.read_bytes()
        manifest[path.name] = {"bytes":len(raw), "sha256":hashlib.sha256(raw).hexdigest()}
    assert all(manifest[name]["sha256"] == value for name, value in frozen["files"].items())
    assert manifest["EXPERIMENTS.npz"]["sha256"] == mainrun["output_sha256"]
    save("MANIFEST.json", {"utc":utc, "files":manifest})
    known = {
        "first_source_pin_reads":first["explicit_input_read_bytes"],
        "reference_public_receipt_read":ref["sources"]["receipts_bytes"],
        "main_frozen_input_reads":mainrun["input_file_bytes"],
        "main_output_hash_read":mainrun["bytes"],
        "summary_compressed_input_booking":summary["explicit_npz_read_bytes"],
        "summary_decoded_arrays_including_float_copy":summary["npz_uncompressed_array_bytes_used"],
        "saved_audit_compressed_input_booking":audit["compressed_input_bytes"],
        "saved_audit_decoded_arrays_including_float_copy":audit["decoded_array_bytes_including_float_conversion"],
        "final_manifest_reads":sum(item["bytes"] for item in manifest.values()),
    }
    known_sum = sum(known.values())
    assert known_sum < 200_000_000
    resources = {"utc":utc, "separate_task_read_hash_decode_cap_bytes":250_000_000,
        "conservative_additional_read_hash_decode_booking_bytes":200_000_000,
        "known_application_read_and_decode_components":known, "known_component_sum":known_sum,
        "remaining_booking_for_context_imports_extra_freeze_record_reads_float_originals_and_unknown_failed_path_reads":200_000_000-known_sum,
        "requested_public_operations":8, "public_operation_cap":8,
        "method_families":["original_Kool2016_task_model_empirical_priors_reused", "Gijsen2022_actual_AI2step_method_implementation"],
        "new_ingress_cap_bytes":5_000_000, "conservative_new_ingress_allowance_bytes":5_000_000,
        "exact_saved_connector_receipt_file_bytes":(HERE/"PUBLIC_RECEIPTS.json").stat().st_size,
        "ingress_note":"All eight requests charged. Saved text size is not physical provider traffic. Full5MBbooking includes unknown provider/redirect/transfer allowance; complete traffic remains uncertified.",
        "peak_scientific_RSS_bytes":max(first["maxrss_bytes_darwin"], ref["maxrss_bytes_darwin"], mainrun["maxrss_bytes_darwin"], summary["maxrss_bytes_darwin"], audit["maxrss_bytes_darwin"]),
        "scientific_RSS_cap_bytes":800_000_000, "record_closeout_RSS_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "scientific_processes_at_once":1, "numerical_threads":1, "scientific_jobs_after_exit":0,
        "premain_scientific_revisions":0, "parameter_policy_seed_horizon_tournaments":0,
        "new_fits":0, "new_human_payload_acquisitions_or_decodes":0,
        "scientific_nonzero_exits":[], "denied_attempts":"FAILURES.md",
        "unknowns":["complete physical I/O", "provider traffic and peaks", "runtime and host aggregate peaks", "exact context/import I/O", "exact denied-path guard reads"],
        "physical_IO_or_complete_provider_compliance_certified":False}
    assert resources["peak_scientific_RSS_bytes"] < resources["scientific_RSS_cap_bytes"]
    save("RESOURCES.json", resources)
    save("EXPOSURE.json", {"utc":utc, "new_human_numeric_outcomes_interpreted":0, "human_MAT_or_cache_decodes":0,
        "saved_fitted_results_objects_opened":0, "new_empirical_acquisition":0, "logged_future_human_paths_used_as_features":0,
        "permitted_numeric_observations":"constructed virtual experiments only; all131072 are consumed for this frozen computational recipe",
        "ordinary_read_only_context":"AGENTS, fullLEARNINGS, LAB_WORKFLOW, currentSTATE, independent-sprint methods, ownBRIEF, predecessor completed reports/source pins; bounded registryPI excerpt",
        "source_text_reads":"seven pinned predecessor source files, complete11blob Gijsen tree metadata, five actual implementation source files, one paper open and one paper find",
        "public_source_metadata":"reanalysis code's fixed participant/trial counts and column indices, not actual person measurements",
        "inherited_exposure_retained":"predecessor whole30900x20cell typed decode/auxiliary raw exposure; first150rows/18numeric fields already consumed; other people's numeric cells not newly interpreted",
        "protected_and_closed_sources":"Pan20/Flesch/HABITS/memory targets/reserved worms/Figure4/optional210/category/consumed mouse fitting and other closed empirical routes untouched",
        "source_code_deployed_version_and_external_license":"uncertified; no new licensing/deployment assertion"})
    links = []
    for name in ["RESULT.md", "README.md", "STATE.md"]:
        for target in re.findall(r"\]\(([^)]+)\)", (HERE/name).read_text()):
            if "://" in target or target.startswith("#"):
                continue
            exists = (HERE/target.split("#")[0]).exists()
            links.append({"from":name, "target":target, "exists":exists})
            assert exists, (name, target)
    save("FINAL_AUDIT.json", {"utc":utc, "frozen_pins_unchanged":True,
        "experiment_sha_matches_actual_main":True, "links":links,
        "materiality_gates":summary["practical_gate"],
        "conservative_uniform_CDF_bound_below_original_boundary":audit["conservative_uniform_CDF_MC_bound"]["under_original_five_pp_boundary"],
        "decision":"CLOSE this source-prior approximation allocation; no consequential or human/published error claim",
        "independent_scientific_review":"UNRUN; within-author checks are not independent review",
        "scientific_goal_completion":False, "science_jobs":0, "native_record_exit_code":0})
    print(json.dumps({"utc":utc, "known_read_decode_component_sum":known_sum,
        "conservative_separate_booking":200_000_000, "peak_scientific_RSS_bytes":resources["peak_scientific_RSS_bytes"],
        "manifest_files":len(manifest), "local_links":len(links), "frozen_pins_unchanged":True,
        "decision":"CLOSE", "science_jobs":0, "exit_code":0}, indent=2))


if __name__ == "__main__":
    main()
