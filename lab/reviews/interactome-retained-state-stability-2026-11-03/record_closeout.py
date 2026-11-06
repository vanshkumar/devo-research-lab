"""Record-only assembly of native receipts/resources/raw pins, no numerical model execution."""
import datetime, hashlib, json
from pathlib import Path
out = Path(__file__).resolve().parent
read = lambda n: json.loads((out/n).read_text())
record = lambda n, x: (out/n).write_text(json.dumps(x, indent=2)+"\n")
inspection, failed, main, contrary, audit = [read(n) for n in ("INPUT_INSPECTION.json", "FAILED_FIRST_RECONSTRUCTION.json", "RECONSTRUCTION.json", "CONTRARY.json", "FINAL_VERIFICATION.json")]
assert main["native_process_exit"] == contrary["native_process_exit"] == audit["native_process_exit"] == 0
assert main["all_independent_reconstruction_gates_pass"] and contrary["both_evoked_interactions_material"] and audit["all_record_checks_pass"]
measured = sum(x["self_elapsed_s"] for x in (inspection, failed, main, contrary, audit))
resources = dict(task_id="interactome-retained-state-stability-independent-review-2026-11-03", initial_native_utc="2026-11-03T07:45:29Z", hard_utc="2026-11-03T09:00:29Z",
                 process_limit_s=1200, conservative_process_charge_s=1150, summed_reported_process_self_s=measured,
                 max_successful_measured_rss_bytes=max(x["rss_bytes_macos"] for x in (inspection, failed, main, contrary, audit)), rss_limit_bytes=1000000000,
                 new_separate_conservative_read_booking_bytes=1000000000, new_public_operations=0, new_ingress_bytes=0, new_dependencies=0,
                 additional_primary_programs_screened=0, new_complete_state_trajectories=17, new_trajectory_archive_files_including_segments=23,
                 ivp_calls_including_segments_and_failure=30, new_full_monodromy_matrices=2, independent_cached_root_spectra_audits=2, new_Newton_root_solves=0,
                 substantive_amendments_conservatively_charged=1, post_contrary_outcome_revisions=0, native_capacity_failures=1, same_assignment_recoveries=1,
                 clocks_or_reservations_reset=False, simultaneously_running_science_processes_max=1, requested_native_numerical_threads=1, remaining_scientific_jobs=0,
                 inherited=dict(public_operations=145, charged_ingress_bytes=654594722, ingress_compliance="UNCERTIFIED", read_booking_GB=6.801,
                                complete_exposure_failures_and_resource_unknowns_preserved=True), additive_read_booking_GB=7.801,
                 limitations=["Reported process selftimes exclude some interpreter startup/import/context/native-host costs; first comparator-shape failure RSS/selftime unknown; all retained in conservative booking.",
                              "Conservative process/read bookings are manual charges, not exhaustive proof of compliance; complete physical I/O/import/decode/context/provider accounting is UNCERTIFIED.",
                              "Numerical thread environment variables requested1 before imports; complete OS/native library thread enforcement is not certified.",
                              "No new network acquisition occurred. Historical provider/download/license/read-resource uncertainties and any older breaches survive.",
                              "Native model-capacity interruption is preserved; no second worker, reset clock or hidden rerun of successful science."])
record("RESOURCES.json", resources)
native = dict(initial_thread_id="01a1a05e-cbb7-7893-be66-2e3ddc4c3162", capacity_failure=dict(failed_turn_id="01a1a05e-cc3d-7a10-ae4b-49c8d6347a24", failed_at_epoch=1793692771, message="Selected model at capacity", same_assignment_continuation=True),
              successful_inspection=dict(command=".venv/bin/python lab/reviews/interactome-retained-state-stability-2026-11-03/inspect_inputs.py", native_exit=0, finished_utc=inspection["finished_utc"], tool_chunk_id="901884"),
              frozen_first_reference=dict(native_exit=1, tool_session=9638, started_utc=failed["started_utc"], finished_utc=failed["finished_utc"], preserved="FAILED_FIRST_RECONSTRUCTION.json"),
              successful_reconstruction=dict(command=".venv/bin/python lab/reviews/interactome-retained-state-stability-2026-11-03/reconstruct_amended.py", native_exit=0, tool_session=97383, started_utc=main["started_utc"], finished_utc=main["finished_utc"]),
              frozen_contrary=dict(command=".venv/bin/python lab/reviews/interactome-retained-state-stability-2026-11-03/contrary.py", native_exit=0, tool_session=7382, started_utc=contrary["started_utc"], finished_utc=contrary["finished_utc"]),
              saved_output_audit=dict(command=".venv/bin/python lab/reviews/interactome-retained-state-stability-2026-11-03/closeout.py", native_exit=0, tool_chunk_id="4db61a", finished_utc=audit["finished_utc"]), remaining_jobs=0)
record("NATIVE_EXECUTION.json", native)
manifest = {p.name:dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(out.glob("*.npz"))}
record("OUTPUT_MANIFEST.json", dict(generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), raw_npz_outputs=manifest, all_consumed_development=True))
word_count = len((out / "TERMINAL_REPORT.md").read_text().split())
assert word_count <= 400
print(json.dumps(dict(record_closeout="complete", terminal_report_words=word_count, summed_reported_process_self_s=measured,
                      max_rss_bytes=resources["max_successful_measured_rss_bytes"], raw_npz_files=len(manifest), jobs=0), indent=2))
