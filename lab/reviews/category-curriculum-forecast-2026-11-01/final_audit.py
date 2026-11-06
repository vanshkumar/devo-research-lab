"""Bounded verification/closeout of the independent review's saved evidence."""
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"
import datetime as dt
import hashlib
import io
import json
import pathlib
import resource
import sys
import zipfile
import numpy as np
from independent_review import (HERE, AUTHOR, data_from_raw, exemplar, independent_decision,
                                selected_nll, empirical_probability, check, save, resources)
from first_calculation import original_inputs


def archive_initial():
    """Preserve completed results before the disclosed gradient edge correction rerun."""
    archived = {}
    for name in ("ORIGINAL_REFITS.json", "CONTRARY.json"):
        payload = (HERE / name).read_bytes()
        destination = name.replace(".json", "_PRE_CLIP_GRADIENT_CORRECTION.json")
        assert not (HERE / destination).exists()
        (HERE / destination).write_bytes(payload)
        archived[name] = dict(archive=destination, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    save("CORRECTION_RECORD.json", dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), archived=archived,
         reason="Independent audit noticed that the initial analytic gradient omitted the frozen objective's1e-12 clipping derivative. Selected results were complete/converged; final path/edge behavior still required a correction. Preserve them, add zero derivatives below the clip, verify extreme parameters, rerun same seeds/starts/refits and compare. This is an implementation correction, not a scientific/model/cohort/gate revision.",
         affected_recipe="Only independent analytic gradients at chosen probabilities below1e-12. Original author records remain immutable."))
    print(json.dumps(archived, indent=2))


def extreme_gradient():
    data, _, _ = data_from_raw()
    d = {k: v[:2] for k, v in data["source"].items()}
    theta = np.array([2., 2., 2., 4., 2., 0., 0., 0.])
    p = exemplar(theta, "P", d)
    value, gradient = exemplar(theta, "P", d, d["y"])
    assert np.all(np.isfinite(gradient)) and np.isfinite(value)
    numeric = []
    # c/gamma/decay/spacing centered finite differences remain well-defined.
    # Lapse0 uses a sufficiently small right derivative, avoiding negative lapse.
    for j in range(len(theta)):
        step = np.zeros(len(theta)); step[j] = 1e-6
        if j == 7:
            step[j] = 1e-16
            n = (exemplar(theta + step, "P", d, d["y"])[0] - value) / step[j]
        else:
            n = (exemplar(theta + step, "P", d, d["y"])[0] - exemplar(theta - step, "P", d, d["y"])[0]) / 2e-6
        numeric.append(float(n))
    result = dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), theta=theta.tolist(),
                  source_nll=value, minimum_response_probability=float(np.min(np.take_along_axis(p, d["y"][..., None], -1))),
                  clipped_response_count=int(np.sum(np.take_along_axis(p, d["y"][..., None], -1) < 1e-12)),
                  analytic_gradient=gradient.tolist(), numeric_gradient=numeric,
                  warning="Lapse finite differences at0/1e-16 have cancellation error; finite checks and other coordinates are the useful comparison. No alternative model is fitted.", resources=resources())
    assert np.max(np.abs(gradient[:-1] - np.array(numeric[:-1]))) < 2e-5
    save("EXTREME_GRADIENT.json", result)
    print(json.dumps(result, indent=2))


def final():
    check()
    reconstructed = json.loads((HERE / "RECONSTRUCTION.json").read_text())
    refit = json.loads((HERE / "ORIGINAL_REFITS.json").read_text())
    contrary = json.loads((HERE / "CONTRARY.json").read_text())
    initial_refit = json.loads((HERE / "ORIGINAL_REFITS_PRE_CLIP_GRADIENT_CORRECTION.json").read_text())
    initial_contrary = json.loads((HERE / "CONTRARY_PRE_CLIP_GRADIENT_CORRECTION.json").read_text())
    author_E = json.loads((AUTHOR / "FIT_E.json").read_text())
    data, joins, raw_resources = data_from_raw()
    _, raw_people, chronology_reads = original_inputs()
    expected_blocks = sum(([i] * 72 for i in range(1, 5)), []) + [5] * 48 + sum(([i] * 72 for i in range(6, 10)), []) + [10] * 48
    expected_phases = [1] * 288 + [3] * 48 + [1] * 288 + [3] * 48
    chronology = []
    for person in raw_people:
        rows = person["rows"]
        assert [int(r[3]) for r in rows] == list(range(len(rows)))
        assert [int(r[4]) for r in rows] == expected_blocks[:len(rows)]
        assert [int(r[2]) for r in rows] == expected_phases[:len(rows)]
        chronology.append(dict(person=person["person"], opportunities=len(rows),
                               consecutive_from_zero=True, exact_block_phase_chronology=True,
                               first_test_follows_all_288_training_opportunities=True))
    E_cv_error = max(float(np.max(np.abs(np.array(a["person_losses"]) - b["person_losses"])))
                     for a, b in zip(author_E["CV"], refit["E"]["CV"]))
    source_standardization = {key: float(np.max(np.abs(np.array(author_E[key]) - refit["E"][key]))) for key in ("mean", "sd", "coef")}
    assert author_E["penalty"] == refit["E"]["penalty"]
    assert E_cv_error < 1e-8
    corrections = dict(original_objective_errors={k: abs(refit[k]["selected"]["nll"] - initial_refit[k]["selected"]["nll"]) for k in ("B", "P")},
                       source_bootstrap_max_gain_change=max(abs(a["evaluation"]["comparisons"][k]["relative_gain"] - b["evaluation"]["comparisons"][k]["relative_gain"])
                           for a, b in zip(contrary["records"], initial_contrary["records"]) for k in ("B", "E")),
                       source_bootstrap_changed_decisions=sum(a["evaluation"]["passes"] != b["evaluation"]["passes"] for a, b in zip(contrary["records"], initial_contrary["records"])))
    assert len(contrary["records"]) == len(initial_contrary["records"]) == 48
    # Verify all44originalDAThashes against the separately acquired OSF file list.
    listing = json.loads((AUTHOR / "source/highsim-trial-files.json").read_text())
    originals = {}
    for file in listing["data"]:
        attributes = file["attributes"]
        if attributes["name"].endswith(".dat"):
            originals[attributes["name"]] = attributes["extra"]["hashes"]["sha256"]
    hashes = []
    with zipfile.ZipFile(AUTHOR / "source/highsim-trials.zip") as z:
        for name in z.namelist():
            digest = hashlib.sha256(z.read(name)).hexdigest()
            assert digest == originals[pathlib.PurePosixPath(name).name]
            hashes.append(dict(member=name, sha256=digest, matches_source_listing=True))
    # Check baseline parity and weighted gradients for a nontrivial bootstrap.
    sample = contrary["records"][0]
    multiplicities = np.array(sample["multiplicities"], dtype=float)
    identity_leakage = []
    for record in contrary["records"]:
        weights = np.array(record["multiplicities"])
        assert weights.sum() == 22
        selected = record["E"]["penalty"]
        active = np.flatnonzero(weights)
        for fold in record["E"]["CV"]:
            assert fold["held_identity_indices"] == active.tolist()
            mean = float(np.average(fold["person_losses"], weights=weights[active]))
            assert abs(mean - fold["mean_nll"]) < 1e-14
        assert selected == min(record["E"]["CV"], key=lambda r: r["mean_nll"])["penalty"]
        identity_leakage.append(dict(replicate=record["replicate"], unique_identities=int(len(active)),
                                    grouped_folds_per_penalty=int(len(active)), selected_penalty=selected))
    weights = multiplicities
    theta = np.array([.3, -.4, .7, .4, -.2, .7, .1, .3])
    loss, g = exemplar(theta, "P", data["source"], data["source"]["y"], weights)
    difference = []
    for j in range(len(theta)):
        step = np.zeros(len(theta)); step[j] = 1e-5
        difference.append((exemplar(theta + step, "P", data["source"], data["source"]["y"], weights)[0] - exemplar(theta - step, "P", data["source"], data["source"]["y"], weights)[0]) / 2e-5)
    gradient_error = float(np.max(np.abs(g - difference)))
    assert gradient_error < 2e-7
    original_P = json.loads((AUTHOR / "FIT_P.json").read_text())
    original_B = json.loads((AUTHOR / "FIT_B.json").read_text())
    original_prob = {"B": exemplar(np.array(original_B["selected"]["theta"]), "B", data["evaluation"]), "E": empirical_probability(author_E, data["evaluation"])}
    original_alternatives = []
    for i, run in enumerate(original_P["runs"]):
        prob = {**original_prob, "P": exemplar(np.array(run["theta"]), "P", data["evaluation"])}
        decision = independent_decision(prob, data["evaluation"]["y"], data["evaluation"]["truth"])
        original_alternatives.append(dict(run=i, source_nll=run["nll"], evaluation=decision))
    minimums = {}
    for k in ("B", "E"):
        gains = [r["evaluation"]["comparisons"][k]["relative_gain"] for r in contrary["records"]]
        minimums[k] = dict(min=min(gains), max=max(gains))
    Efits = refit["E"]["optimizer_fits"] + sum(r["E"]["optimizer_fits"] for r in contrary["records"])
    result = dict(completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  source_listing_hash_checks=hashes, original_E_max_fold_loss_error=E_cv_error,
                  original_E_standardization_coefficient_errors=source_standardization,
                  correction_comparison=corrections, weighted_gradient_max_error=gradient_error,
                  grouped_identity_checks=identity_leakage, bootstrap_gain_ranges=minimums,
                  original_saved_P_alternatives=original_alternatives,
                  fit_counts=dict(final_P_B_local_optimizer_fits=5 * 49, final_E_convex_optimizer_fits=Efits,
                                  initial_superseded_P_B_local_optimizer_fits=5 * 49,
                                  initial_superseded_E_convex_optimizer_fits=initial_refit["E"]["optimizer_fits"] + sum(r["E"]["optimizer_fits"] for r in initial_contrary["records"])),
                  original_input_reads=raw_resources, chronology_original_input_reads=chronology_reads,
                  chronology_checks=chronology,
                  review_response_exposure=dict(first_training_choices_checked=43*288,
                      first_test_choices_checked=43*48, selected_intended_new_choices=43*24,
                      nominal_old_probe_choices_checked=43*24,
                      purpose="Code validity/feedback/header/correctness consistency. Only intended-new choices fitted/scored. All first-curriculum training/old-probe choices now numerically consumed; second curricula/partial41remain decoded auxiliary except author's fullID20."),
                  resources=resources())
    save("FINAL_AUDIT.json", result)
    print(json.dumps({k: result[k] for k in ("completed_utc", "original_E_max_fold_loss_error", "original_E_standardization_coefficient_errors", "correction_comparison", "weighted_gradient_max_error", "bootstrap_gain_ranges", "fit_counts", "resources")}, indent=2))


def closeout():
    check()
    required = ["BRIEF.md", "CONTRARY_PLAN.md", "first_calculation.py", "independent_review.py", "final_audit.py",
                "FIRST_CALCULATION.json", "RECONSTRUCTION.json", "reconstructed_forecasts.npz", "ORIGINAL_REFITS.json",
                "CONTRARY.json", "CORRECTION_RECORD.json", "EXTREME_GRADIENT.json", "FINAL_AUDIT.json",
                "ORIGINAL_REFITS_PRE_CLIP_GRADIENT_CORRECTION.json", "CONTRARY_PRE_CLIP_GRADIENT_CORRECTION.json",
                "REVIEW.md", "README.md", "PROPOSED_LEARNING.md", "FAILURES.md", "RESOURCES.json", "COMMUNICATION_MESSAGE.md"]
    pins = {}
    for name in required:
        payload = (HERE / name).read_bytes()
        assert payload
        pins[name] = dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
        if name.endswith(".json"):
            json.loads(payload)
    reconstruction = json.loads((HERE / "RECONSTRUCTION.json").read_text())
    contrary = json.loads((HERE / "CONTRARY.json").read_text())
    resource_record = json.loads((HERE / "RESOURCES.json").read_text())
    assert sum(resource_record["additional_scientific_read_decode_hash"]["phase_allowances_bytes"].values()) == 150000000
    assert len(reconstruction["pins"]["FREEZE.json"]) == 8
    assert len(reconstruction["pins"]["MANIFEST.json"]) == 27
    assert contrary["summary"]["completed"] == 48 and contrary["summary"]["full_passes"] == 0
    assert resource_record["processes"]["active_jobs_at_close"] == 0
    words = len((HERE / "COMMUNICATION_MESSAGE.md").read_text().split())
    assert words <= 400
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    save("MANIFEST.json", dict(created_utc=stamp, owned_artifact_pins=pins,
         mutable_terminal_records_excluded=["STATE.md", "COMMUNICATION_STATUS.json"],
         inputs="Author immutable source and frozen artifacts are independently pinned in FIRST_CALCULATION, RECONSTRUCTION and FINAL_AUDIT. No author executable imported/run."))
    save("CLOSEOUT_CHECK.json", dict(completed_utc=stamp, required_artifacts_present=len(required),
         all_required_JSON_parse=True, author_freeze_pins_verified=8, author_manifest_pins_verified=27,
         source_member_pins_verified=44, source_bootstrap_samples=48, full_passes=0,
         conservative_review_read_bytes=150000000, jobs=0, communication_words=words,
         resources=resources(), terminal_delivery="Pending once-only send after this save"))
    print(json.dumps(dict(completed_utc=stamp, required_artifacts=len(required), communication_words=words,
                         review_read_charge=150000000, jobs=0, resources=resources()), indent=2))


if __name__ == "__main__":
    {"archive_initial": archive_initial, "extreme_gradient": extreme_gradient, "final": final, "closeout": closeout}[sys.argv[1]]()
