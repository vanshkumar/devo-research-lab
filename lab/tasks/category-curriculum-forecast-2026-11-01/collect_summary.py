"""Collect final scoped artifact/resource records; does not execute model fits."""
import datetime
import hashlib
import json
import pathlib
import resource

ROOT=pathlib.Path(__file__).resolve().parent
acq=[json.loads(s) for s in (ROOT/"ACQUISITION.jsonl").read_text().splitlines()]
observed_ingress=sum(x.get("bytes_received",0) for x in acq)
native_rss=max(x.get("peak_rss_native",0) for x in acq)
resources={"completed_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "fixed_start_utc":"2026-11-01T09:07:04.423Z","hard_deadline_utc":"2026-11-01T10:37:04.423Z",
    "limits":{"public_operations":32,"empirical_families":2,"primary_families":3,
              "ingress_bytes":25000000,"read_decode_hash_bytes":300000000,
              "process_RSS_bytes":800000000,"scientific_processes":1,"numeric_threads":1,"development_revision":1},
    "public_operations":{"conservatively_charged":24,"delivered_or_native_attempted":23,
        "native_acquire_invocations":len(acq),"native_successes":sum("sha256" in x for x in acq),
        "browser_suboperations":10,"blocked_before_delivery_inline_attempts_charged":1,
        "browser_count_detail":"search1/PMCopen1/Wileyopen1/Wileyfind3/publisherpreview1/authorpage1/authorPDFclick1/authorPDFopen1",
        "provider_redirect_subrequests_fanout":"UNKNOWN; top-level counts are not physical HTTP counts"},
    "families":{"empirical": ["Carvalho-Goldstone2014/OSFs87tf-Experiment1"],
        "primary":["Carvalho-Goldstone2014","Carvalho-Goldstone2022SAT-M"],
        "incidental":"Other search/reference hits not deliberately screened; no third empirical payload"},
    "ingress":{"native_successful_observed_bytes":observed_ingress,"conservative_charged_bytes":20000000,
        "charge_basis":"Native389684known bytes plus failed DNS allocation1MB and conservative allowances for10browser suboperations, including two15-pagePDFfetches, uncertain redirects/cache/toolprovider overhead; rounded20MB.",
        "browser_provider_wire_bytes":"UNKNOWN; charge is an allowance, not measured physical traffic or an OS-wide compliance certificate"},
    "additional_scientific_read_decode_hash":{"conservative_charged_bytes":200000000,
        "charge_basis_bytes":{"source_acquisition_hash_and_failed_pass_allowance":20000000,
            "metadata_workbook_initial_calculations":30000000,"preparation_including_failed_pass":35000000,
            "source_fit_loading_and_saved_outputs":30000000,"forecast_loading_and_pins":25000000,
            "controls_loading_and_outputs":25000000,"scoring_loading_and_raw_reconstruction":15000000,
            "verification_contrary_and_final_pins":20000000},
        "scope":"Conservative scoped serialized input/output reads, decompression/decoding and hashing; ordinary instruction/context reads excluded. Repeated in-memory optimizer arithmetic is computation, not another file acquisition.",
        "physical_IO":"UNKNOWN; failed-pass/toolhost overhead not individually measured"},
    "peak_RSS":{"largest_successfully_measured_native_process_bytes":84885504,
        "largest_acquisition_process_bytes":native_rss,
        "source":"PREPARE.json maximum84,885,504; fit78,249,984; score72,122,368; verification35,504,128; contrary77,299,712. Earlier failed preparation/first-check peaks unmeasured.",
        "toolhost_and_failed_peak":"UNKNOWN; no OS-wide memory-compliance claim"},
    "processes":{"maximum_local_scientific_processes":1,"numerical_threads_requested":1,"active_jobs_at_close":0},
    "development_revisions_used":1,"budget_extensions":0,"new_dependencies_installed":0,
    "protected_or_old_empirical_payloads_accessed":False,
    "heartbeat":"Unchanged by worker; same active PI heartbeat continues across study endpoint",
    "collector_peak_RSS_bytes_macos":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(ROOT/"RESOURCES.json").write_text(json.dumps(resources,indent=2))
names=["PROTOCOL.md","AMENDMENT_1.md","FREEZE.json","analysis.py","verify.py","contrary.py","CONTRARY_PLAN.md",
       "FIRST_DATA_CHECK.json","METADATA_CHECK.json","NOVELTY_AUDIT.json","PREPARE.json","GATE.json",
       "FIT_P.json","FIT_B.json","FIT_E.json","FIT_RESOURCES.json","predictions.npz","PREDICTION_PINS.json",
       "control_outcomes.npz","CONTROLS.json","evaluation_outcomes.npz","SCORES.json","VERIFICATION.json",
       "CONTRARY.json","RESOURCES.json","SOURCES.md","FAILURES.md"]
manifest={"created_utc":resources["completed_utc"],"artifacts":{n:{"bytes":(ROOT/n).stat().st_size,
    "sha256":hashlib.sha256((ROOT/n).read_bytes()).hexdigest()} for n in names},
    "source_files":{p.name:{"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
                    for p in (ROOT/"source").iterdir() if p.is_file()},
    "meaning":"Pins establish content identity, not independent proof of historical nonaccess or review."}
(ROOT/"MANIFEST.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps({"observed_native_ingress":observed_ingress,"public_charge":24,"ingress_charge":20000000,
    "read_charge":200000000,"max_measured_RSS":84885504,"active_jobs":0,"manifest_artifacts":len(names)},indent=2))
