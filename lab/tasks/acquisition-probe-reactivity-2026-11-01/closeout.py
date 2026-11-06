"""Record-only closeout: owned artifact hashes and preserved accounting."""
from pathlib import Path
import datetime as dt
import hashlib
import importlib.metadata
import json
import platform
import resource
import sys

out = Path(__file__).resolve().parent
names = ["FIRST_CALCULATION.json", "DESIGN_SCREEN.json", "SOURCE_PINS.json", "EXECUTION.json"]
records = {}
record_bytes = 0
for name in names:
    raw = (out / name).read_bytes()
    record_bytes += len(raw)
    records[name] = json.loads(raw)
assert records["EXECUTION.json"]["jobs"] == 0
assert [c["native_exit"] for c in records["EXECUTION.json"]["commands"]] == [1, 0, 0]
assert records["SOURCE_PINS.json"]["public_operation_count"] == 2
assert records["SOURCE_PINS.json"]["deliberately_targeted_families"] == 2
assert records["DESIGN_SCREEN.json"]["decision"].startswith("CLOSE")
manifest = {}
for path in sorted(out.iterdir()):
    if path.is_file() and path.name not in ("RESOURCES.json", "ARTIFACT_MANIFEST.json"):
        raw = path.read_bytes()
        record_bytes += len(raw)
        manifest[path.name] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
now = dt.datetime.now(dt.timezone.utc).isoformat()
versions = {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "numba")}
res = dict(
    task="acquisition-probe-reactivity-2026-11-01", recorded_at_utc=now,
    scientific_status="CLOSED; no science after design_screen close; this command is record-only verification",
    limits=dict(public_operations=8, deliberately_targeted_families=2, new_ingress_bytes=5000000,
                additional_read_hash_decode_bytes=500000000, peak_rss_bytes=800000000,
                scientific_processes=1, numerical_threads=1),
    public_operations=2, deliberately_targeted_families=2,
    charged_new_ingress_allowance_bytes=2000000, returned_provider_tool_json_utf8_bytes=59321,
    actual_provider_ingress_bytes="UNKNOWN: provider acquisition/crawl/redirect traffic not exposed; 2MB is an allowance, not a measured cap certificate",
    explicit_measured_scientific_read_hash_decode_bytes=120306+8808,
    record_only_file_reads_and_hashes_this_pass_bytes=record_bytes,
    cumulative_conservative_read_charge_bytes=200000000,
    charge_scope="Includes explicit parameter/source/hash/decode reads, ordinary context and repeated/truncated selected reads, provider-return interpretation, successful scientific processes, syntax-only failure, rejected inline command, imports/runtime/record work and small closeout edits. 200MB is a containing allowance; actual physical/runtime IO is not certified.",
    max_measured_successful_scientific_process_rss_bytes=116342784,
    measured_design_screen_rss_bytes=18333696,
    failed_syntax_pass_peak_rss="UNKNOWN; parsing failed before imports or scientific payload reads",
    rejected_inline_record_command="PreToolUse rejected before execution; zero file changes or scientific payload reads",
    record_only_closeout_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    whole_task_max_rss="UNKNOWN including failed interpreter/provider/host processes; measured successful science reported separately",
    provider_peak_and_runtime_bytes="UNKNOWN", physical_io="UNKNOWN",
    observed_cap_breach=False,
    exact_all_pass_compliance="UNCERTIFIED for provider ingress, runtime physical reads and unmeasured failed/host peaks; measured science and conservative charges below finite bounds",
    scientific_native_exits=[1, 0, 0], scientific_process_overlap=0, numerical_threads_environment=1,
    jobs=0, empirical_source_acquisition=0, biological_rows_read=0, empirical_target_arrays_read=0,
    saved_empirical_prefix_reads=0, new_fits=0, consumed_scoring=0,
    current_runtime=dict(python=sys.version, platform=platform.platform(), packages=versions),
    source_asset_modifications=0, shared_record_modifications=0, credits_spent_or_reset=False,
    prior_resources="All older studies, failed starts, exposures, resource breaches and unknowns remain separate and unchanged. No budget/data reset.",
    report_delivery="Single terminal report accepted by native send_message_to_thread for current PI; see STATE.md and REPORT_DELIVERY.json. No acknowledgement wait or further science.",
)
(out / "ARTIFACT_MANIFEST.json").write_text(json.dumps(dict(utc=now,
    scope="Current closure artifacts; not a pre-main freeze or historical nonaccess proof", files=manifest), indent=2)+"\n")
(out / "RESOURCES.json").write_text(json.dumps(res, indent=2)+"\n")
print(json.dumps(dict(record_only=True, utc=now, checked_files=len(manifest),
    record_read_hash_bytes=record_bytes, read_charge=200000000, public_ops=2,
    max_measured_science_rss=116342784, unknowns_preserved=True, versions=versions, jobs=0)))
