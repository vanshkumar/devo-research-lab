"""One-off post-hoc artifact/resource ledger, not a lab control or service."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parent
if (ROOT/"READ_LIMIT_STOP.md").exists():
    raise SystemExit("Retired post-hoc helper: read-limit compliance is uncertified; use saved RESOURCES.json. No further payload reads or full hash pass in this allocation.")
LABELS=["first","development","development_decoupled","development_noiseless",
        "development_decoupled_matched","development_noiseless_matched",
        "main","contrary_decoupled","contrary_noiseless","contrary_resolution"]
AUDITED=["development","development_decoupled_matched","development_noiseless_matched",
         "main","contrary_decoupled","contrary_noiseless","contrary_resolution"]

def write(name,obj):
    (ROOT/name).write_text(json.dumps(obj,indent=2)+"\n")

def stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())

def zmeta(path):
    with zipfile.ZipFile(path) as archive:
        return {info.filename:info for info in archive.infolist()}

scores={label:json.loads((ROOT/label/"SCORES.json").read_text()) for label in LABELS}
obs={label:zmeta(ROOT/label/"observations.npz") for label in LABELS}
pred={label:zmeta(ROOT/label/"predictions.npz") for label in LABELS}

def array_bound(label,key):
    info=obs[label][key+".npy"]
    # NpzFile may open once for magic and again for full decoding. Charge up to
    # two complete compressed-member reads plus one full decoded member and256
    # bytes for magic/header handling. This is an accounting upper allowance,
    # not measured kernel IO or a claim about cache behavior.
    return info.file_size+2*info.compress_size+256

read_components={}
read_components["run_prediction_pin_reads"]=sum((ROOT/label/"predictions.npz").stat().st_size for label in LABELS)
read_components["audit_prediction_decode_load_and_second_pin"]=sum(
    2*(ROOT/label/"predictions.npz").stat().st_size+
    sum(info.file_size+min(8192,info.compress_size)+256 for info in pred[label].values())
    for label in AUDITED)
observation_bound=0
for label in AUDITED:
    for row in scores[label]["records"]:
        seed=row["seed"]
        for key in ("mu","u","plant","offset","goal","zstar","tutors"):
            observation_bound+=array_bound(label,f"s{seed}_{key}")
        wrong=f"s{seed}_shuffled_tutors"
        if row["method"]=="shuffled" and wrong+".npy" in obs[label]:
            observation_bound+=array_bound(label,wrong)
read_components["audit_repeated_observation_read_decode_bound"]=observation_bound
matching_bound=0
for primary,dec,clean,seeds in [
    ("development","development_decoupled_matched","development_noiseless_matched",range(1200,1212)),
    ("main","contrary_decoupled","contrary_noiseless",range(2000,2064))]:
    for seed in seeds:
        for key in ("mu","u","goal","latent","noise","tutors","zstar"):
            for label in (primary,dec):
                matching_bound+=array_bound(label,f"s{seed}_{key}")
        for key in ("mu","u","goal","latent","noise","zstar","plant","offset"):
            for label in (primary,clean):
                matching_bound+=array_bound(label,f"s{seed}_{key}")
        for label,key in ((primary,"tutors"),(clean,"tutors"),(primary,"noise")):
            matching_bound+=array_bound(label,f"s{seed}_{key}")
        for key in ("mu","u","goal","zstar","plant","offset"):
            matching_bound+=array_bound(primary,f"s{seed}_{key}")
read_components["matching_and_analytic_diagnostic_array_bound"]=matching_bound
json_reads=sum(2*(ROOT/label/"SCORES.json").stat().st_size for label in AUDITED)
json_reads+=sum(2*(ROOT/label/"SCORES.json").stat().st_size for label in ("main","contrary_decoupled","contrary_noiseless","contrary_resolution"))
json_reads+=2*(ROOT/"AUDIT.json").stat().st_size
json_reads+=sum(2*(ROOT/label/"SCORES.json").stat().st_size for label in LABELS)
read_components["audit_analysis_closeout_json_read_decode"]=json_reads
read_components["web_text_scientific_read_charge"]=4000000
read_components["ordinary_source_code_zip_directory_and_summary_allowance"]=8000000

mutable={"STATE.md","RESOURCES.json","ARTIFACTS.json","REPORT_STATUS.json"}
paths=sorted(p for p in ROOT.rglob("*") if p.is_file() and "__pycache__" not in p.parts
             and p.name not in mutable and "reproduction" not in p.parts)
planned_hash_bytes=sum(path.stat().st_size for path in paths if path.name!="predictions.npz")
read_components["closeout_new_artifact_hash_pass"]=planned_hash_bytes
posthoc_bound=sum(read_components.values())
parser=argparse.ArgumentParser()
parser.add_argument("--inventory",action="store_true")
args=parser.parse_args()
if args.inventory:
    print(json.dumps(dict(read_components=read_components,posthoc_bound_bytes=posthoc_bound,
        directory_file_bytes=sum(p.stat().st_size for p in paths),trajectories=sum(len(s["records"]) for s in scores.values())),indent=2))
    raise SystemExit(0)

if (ROOT/"ARTIFACTS.json").exists():
    raise SystemExit("Refusing to replace artifact manifest")
artifacts={}
for path in paths:
    relative=path.relative_to(ROOT).as_posix()
    if path.name=="predictions.npz":
        pin=scores[path.parent.name]["prediction_sha256"]
        basis="Saved pre-gold pin; reverified by audit where listed. FIRST/unmatched pins recorded at generation. No redundant third whole-file pass."
    else:
        pin=hashlib.sha256(path.read_bytes()).hexdigest()
        basis="Closeout SHA256 pass"
    artifacts[relative]=dict(sha256=pin,bytes=path.stat().st_size,basis=basis)
freeze=json.loads((ROOT/"FREEZE.json").read_text())
for name,pin in freeze["sha256"].items():
    if artifacts[name]["sha256"]!=pin:
        raise AssertionError("Frozen artifact changed: "+name)
peak=max(s["peak_rss_bytes"] for s in scores.values())
for name in ("DEVELOPMENT_AUDIT.json","AUDIT.json","ANALYSIS.json"):
    peak=max(peak,json.loads((ROOT/name).read_text())["peak_rss_bytes"])
resources=dict(saved_at=stamp(),task_id="variable-tutor-correction-2026-11-01",
    start="2026-11-01T06:00:00Z",first_calculation="2026-11-01T06:04:12Z",
    main_freeze=freeze["frozen_at"],main_finished="2026-11-01T06:12:44Z",
    analysis_finished="2026-11-01T06:12:56Z",hard_deadline="2026-11-01T07:15:00Z",
    public_operations=7,public_operations_cap=20,targeted_primary_families=3,targeted_primary_families_cap=3,
    charged_new_ingress_bytes=4000000,new_ingress_cap=10000000,provider_transfer_bytes=None,provider_peak_rss_bytes=None,
    additional_scientific_read_cap=400000000,posthoc_read_decode_hash_allowance_bytes=posthoc_bound,
    read_components=read_components,
    read_accounting="Post-hoc conservative accounting of application scientific data passes, based on actual archive member sizes and executed code paths. Includes up to two compressed-member reads for NpzFile magic plus full decoding, repeated observation access, pin passes, JSON/source/text allowance and new closeout hashes. Not kernel IO telemetry; runtime library/OS/provider internals are not independently metered. No new automatic metering/control service. Bookkeeping metadata itself is within8MBallowance. No evaluation rerun was executed.",
    largest_measured_scientific_rss_bytes=peak,peak_rss_cap_bytes=800000000,
    process_policy="One foreground scientific process at a time; one numeric thread forced before NumPy import. No child processes, pools, services or background jobs.",
    scientific_jobs_remaining=0,spending=0,downloads=0,new_dependencies=0,
    executed_trajectories=sum(len(s["records"]) for s in scores.values()),
    executed_feedback_slots=sum(len(s["records"])*s["queries"] for s in scores.values()),
    per_experiment={label:{key:scores[label].get(key) for key in ("started_at","finished_at","seeds","budgets","sigma","coupled","resolution","queries","peak_rss_bytes")} for label in LABELS},
    failures=["First contrary-development controls were unmatched because nmax changed sequential RNG draw scheduling; preserved and corrected before freeze.",
              "Primary disk>=10ppinvestment gain failed; no architecture repair.","PMC primary page open returned CAPTCHA; failure counts against operations/ingress.",
              "Ordinary pre-science awk context read blocked by existing shell-composition hook; bounded ordinary reads completed without escalation or control changes."],
    exposure=dict(primary_task_seeds=dict(first=list(range(1100,1103)),development=list(range(1200,1212)),evaluation=list(range(2000,2064))),
        wrong_tutor_seed_rule="primary seed +1000000; synthetic wrong-task controls",
        status="All generated tutor observations, latent/plant arrays, wrong-task controls, scalar feedback, endpoints and summary outcomes in every saved generation are consumed. Conditions/prefixes are paired repeats, not extra independent tasks. Original FIRST/unmatched RNG generation remains distinct from corrected128-prefix generation.",
        evaluation_units=64,all_old_empirical_payloads_opened=0,protected_target_accesses=0,
        old_freezes_failures_resources_and_access_restrictions="Preserved; no shared record edited. Pan20/Flesch81-B2-B20/laterHABITS/memorytargets/fourreservedworms/Figure4_42/optional210 remain closed."),
    unrun=["Fresh independent scientific review", "Second main reproduction", "Unknown-rank/noise calibration", "Nonlinear/acoustic/biological observation and motor models", "Cancellation-circuit reproduction", "Any architecture comparison or novelty certification"],
    heartbeat="Existing single active heartbeat/lab continuation above20%belongs to PI; no scheduler or outer lab state changed.")
write("ARTIFACTS.json",dict(saved_at=stamp(),frozen_pins_pass=True,files=artifacts))
write("RESOURCES.json",resources)
rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps(dict(saved_at=resources["saved_at"],files=len(artifacts),frozen_pins_pass=True,
    posthoc_read_decode_hash_allowance_bytes=posthoc_bound,largest_measured_scientific_rss_bytes=peak,
    trajectories=resources["executed_trajectories"],feedback_slots=resources["executed_feedback_slots"],
    closeout_process_peak_bytes=int(rss if sys.platform=="darwin" else rss*1024)),indent=2))
