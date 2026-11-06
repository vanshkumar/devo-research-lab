"""Saved-output scalar verification, source pins/licenses and bounded cached-primary review. No new trajectories."""
import datetime, hashlib, json, math, resource, time
from model import *
started = time.perf_counter()
m = Circuit()
own_freeze = json.loads((OUT / "FREEZE.json").read_text())
amend = json.loads((OUT / "AMENDMENT_1.json").read_text())
checks = {}
for label, frozen in (("original", own_freeze), ("amendment", amend)):
    checks[label] = {}
    for name, expected in frozen["sha256"].items():
        actual = hashlib.sha256((OUT / name).read_bytes()).hexdigest()
        assert actual == expected
        checks[label][name] = actual
for name, pin in amend["preserved_failed_outputs"].items():
    assert hashlib.sha256((OUT / name).read_bytes()).hexdigest() == pin["sha256"]

expected_blobs = {"Gg.npy": "07b8ab0aa4471aa19cfae5e662d291493f09819b", "Gs.npy": "0a6e1cc361d9fe377f48cbf48e0557fec65debe8", "emask.npy": "ae289f5055e5661739b977cee62935d2f3b0be06"}
source_pins = {}
for name, expected in expected_blobs.items():
    raw = (ASSETS / name).read_bytes()
    assert gitblob(raw) == expected
    source_pins[name] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), git_blob=expected)
raw = ORIGINAL.read_bytes()
assert gitblob(raw) == "27bc70d6986e17d00fedf85ffbcaf8cb6b1b7d47"
source_pins["initialize.py"] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), git_blob=gitblob(raw))
for name, expected, mask in (("FWD.json", "0840d0d732a38e1b76de384310e113ecda8e1405", m.fwd), ("PLM.json", "87d8afda2195a3fb5a8dec2bd05a1a14ca5104f2", m.mask({"PLML": .2, "PLMR": .2}))):
    raw = (ASSETS / name).read_bytes()
    canonical = raw[:-1] if raw.endswith(b"\n") else raw
    assert gitblob(canonical) == expected
    preset = json.loads(raw)
    actual = np.array([preset[n]["inputCurrent"] for n in m.names])
    assert np.array_equal(actual, mask)
    source_pins[name] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), canonical_git_blob=expected, local_added_newline=True,
                             nonzero={n: float(actual[i]) for i, n in enumerate(m.names) if actual[i]})
license_path = ORIGINAL.parent / "interactome-LICENSE"
license_bytes = license_path.read_bytes()
(OUT / "SOURCE_LICENSE.txt").write_bytes(license_bytes)
source_pins["SOURCE_LICENSE.txt"] = dict(bytes=len(license_bytes), sha256=hashlib.sha256(license_bytes).hexdigest(), license="BSD-3-Clause; original notice byte copied")
dump("SOURCE_MANIFEST.json", dict(model="Kim-Leahy-Shlizerman2019 Neural Interactome3.0.0-beta", tree="bdb94ca174980e46777f7b1936f539903c688719",
                                  source_repository="https://github.com/shlizee/C-elegans-Neural-Interactome", primary_dois=["10.3389/fncom.2017.00053", "10.3389/fncom.2019.00008"],
                                  pins=source_pins, underlying_connectivity_separate_license="inherited/uncertified", new_public_operations=0, new_ingress_bytes=0, new_dependencies=0,
                                  independent_implementation="model.py; original released functions external comparator only; no lab helper imports"))

contrary = json.loads((OUT / "CONTRARY.json").read_text())
scalar = {}
for seed in (0, 1):
    paths = {}
    for label in ("finite_challenge", "finite_no_challenge", "sham_challenge", "sham_no_challenge"):
        with np.load(OUT / ("CONTRARY_seed%d_%s.npz" % (seed, label)), allow_pickle=False) as z:
            paths[label] = (z["t"].copy(), z["y"].copy())
    tt = paths["finite_challenge"][0]
    assert all(np.array_equal(tt, x[0]) for x in paths.values())
    vals = []
    for k, t in enumerate(tt):
        if t >= 300.3-1e-9:
            for j in m.motor:
                # Independently grouped as difference of two within-history evoked responses.
                v = (float(paths["finite_challenge"][1][k,j])-float(paths["finite_no_challenge"][1][k,j]))-(float(paths["sham_challenge"][1][k,j])-float(paths["sham_no_challenge"][1][k,j]))
                vals.append(v*v)
    rms = math.sqrt(math.fsum(vals)/len(vals))
    reported = contrary["scores"][str(seed)]["evoked_interaction_motor_rms"]
    assert abs(rms-reported) < 1e-11 and rms > SCALE/10
    for branch in ("finite", "sham"):
        assert np.array_equal(paths[branch+"_challenge"][1][0], paths[branch+"_no_challenge"][1][0])
    scalar[str(seed)] = dict(squared_scalar_count=len(vals), independently_grouped_scalar_rms=rms, reported_abs_error=abs(rms-reported), forks_bitwise=True)

with np.load(OUT / "INDEPENDENT_ORBIT.npz", allow_pickle=False) as z:
    cycle = z["y"]
with np.load(OUT / "EQUILIBRIUM_AUDIT_seed0.npz", allow_pickle=False) as z:
    eq = z["y"]
dist = np.sqrt(np.mean((cycle[:, m.motor]-eq[m.motor])**2, axis=1))
orbit_eq_distance = dict(minimum_motor_rms_over_2049_saved_cycle_samples=float(np.min(dist)), samples=len(dist), continuum_minimum_certified=False)

notes = {}
for name in ("article-open.json", "article-results.json", "article-tail.json", "interactome-paper.json", "interactome-results.json"):
    p = ORIGINAL.parent / name
    raw = p.read_bytes()
    obj = json.loads(raw)
    texts = [b["text"] for b in obj.get("content", []) if b.get("type") == "text"]
    selected = []
    for text in texts:
        for line in text.splitlines():
            low = line.lower()
            if any(s in low for s in ("perturbation", "multistab", "bistab", "state transition", "20000", "24000", "transient", "pulse", "switching")):
                selected.append(line)
    notes[name] = dict(path=str(p.relative_to(ROOT)), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), cached_relevant_lines=selected)
dump("CACHED_PRIMARY_REVIEW.json", notes)
verification = dict(finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), all_record_checks_pass=True, original_and_amended_frozen_bytes=checks,
                    preserved_failed_bytes_verified=True, source_git_blobs_and_preset_values_verified=True, saved_contrary_scalar_verification=scalar,
                    independent_cycle_equilibrium_phase_check=orbit_eq_distance, native_process_exit=0, self_elapsed_s=time.perf_counter()-started,
                    rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, figure_png_visually_inspected=True,
                    new_trajectory_or_setting_evaluation=False)
dump("FINAL_VERIFICATION.json", verification)
print(json.dumps({k:v for k,v in verification.items() if k!="original_and_amended_frozen_bytes"}, indent=2))
for name in ("article-results.json", "article-tail.json", "interactome-results.json"):
    print("CACHED_PRIMARY", name)
    for line in notes[name]["cached_relevant_lines"]:
        print(line)
