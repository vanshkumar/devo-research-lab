"""Independent original-MAT joins and scalar circular scores; author code unused."""
import os
for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"
import datetime, hashlib, io, json, math, pathlib, resource, zipfile
import numpy as np
from scipy.io import loadmat

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "tasks/surprise-history-forecast-2026-11-01"

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def angle(x):
    return math.atan2(math.sin(float(x)), math.cos(float(x)))

def main():
    began = now()
    split = json.loads((SOURCE / "SPLIT.json").read_text())
    forecasts = dict(np.load(SOURCE / "predictions.npz", allow_pickle=False))
    truth = dict(np.load(SOURCE / "evaluation_truth.npz", allow_pickle=False))
    keys = [tuple(map(int, x)) for x in forecasts["keys"]]
    assert len(keys) == len(set(keys)) == 8968
    assert np.array_equal(forecasts["keys"], truth["keys"])
    original = {}
    chronology, decoded, compressed = [], 0, 0
    with zipfile.ZipFile(SOURCE / "behavior_zip.source") as archive:
        for person in split["participants"]:
            if person["split"] != "evaluation":
                continue
            payload = archive.read(person["member"])
            decoded += len(payload)
            compressed += archive.getinfo(person["member"]).compress_size
            mat = loadmat(io.BytesIO(payload), simplify_cells=True)
            for prefix, context in (("DataCP_", 1), ("DataOddball_", 0)):
                raw = mat[next(k for k in mat if k.startswith(prefix))]
                assert len(raw["pred"]) == 240
                valid = 0
                for t in range(239):
                    if raw["block"][t] != raw["block"][t + 1]:
                        continue
                    key = (int(person["id"]), context, int(raw["block"][t]), int(raw["trial"][t]))
                    assert key not in original
                    original[key] = angle(math.radians(float(raw["pred"][t + 1]) - float(raw["pred"][t])))
                    valid += 1
                chronology.append({"id": person["id"], "context": context, "eligible": valid,
                    "prediction_before_offset": int(np.sum(np.asarray(raw["timestampPrediction"]) < raw["timestampOffset"])),
                    "offset_before_next_onset": int(np.sum(np.asarray(raw["timestampOffset"][:-1]) < raw["timestampOnset"][1:]))})
    assert set(keys) == set(original)
    y = np.array([original[key] for key in keys])
    ids = np.array([key[0] for key in keys])
    people = np.unique(ids)
    losses, models = {}, {}
    for name in ("P", "N", "B", "H"):
        errors = np.array([angle(a - b) for a, b in zip(y, forecasts[name])])
        loss = np.array([1.0 - math.cos(e) for e in errors])
        losses[name] = loss
        models[name] = {"mean_person_loss": float(np.mean([loss[ids == p].mean() for p in people])),
            "angular_rmse_degrees": math.degrees(math.sqrt(float(np.mean(errors ** 2)))),
            "angular_mae_degrees": math.degrees(float(np.mean(abs(errors))))}
    pb = np.array([losses["B"][ids == p].mean() for p in people])
    ph = np.array([losses["H"][ids == p].mean() for p in people])
    draws = np.random.default_rng(20261101).integers(0, len(people), (10000, len(people)))
    boot = 1 - ph[draws].mean(axis=1) / pb[draws].mean(axis=1)
    contexts = {}
    for context in (0, 1):
        selected = np.array([key[1] == context for key in keys])
        b = np.mean([losses["B"][selected & (ids == p)].mean() for p in people])
        h = np.mean([losses["H"][selected & (ids == p)].mean() for p in people])
        contexts[str(context)] = {"B": float(b), "H": float(h), "gain": float(1 - h / b)}
    gain = float(1 - ph.mean() / pb.mean())
    interval = np.quantile(boot, [.025, .975]).tolist()
    out = {"started_at": began, "calculated_at": now(), "independent_author_code_imports": False,
        "raw_evaluation_people": len(people), "raw_context_rows_decoded": 19 * 480,
        "eligible_updates": len(y), "unique_keys_and_original_join_exact": True,
        "maximum_target_difference_radians": float(np.max(abs(y - truth["y"]))),
        "models": models, "gain": gain, "paired_person_bootstrap95": interval,
        "contexts": contexts, "people_improved": int(np.sum(ph < pb)),
        "original_joint_rule_passes": bool(gain >= .05 and interval[0] > 0 and all(c["gain"] > 0 for c in contexts.values())),
        "chronology": chronology, "decoded_MAT_bytes": decoded, "compressed_member_bytes": compressed,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "scope": "Independent scalar original-raw target and saved-forecast score reconstruction, conditional on frozen source fits. Full MAT auxiliaries consumed; no independent hardware chronology or source-fit uncertainty certification."}
    (HERE / "FIRST_CALCULATION.json").write_text(json.dumps(out, indent=2) + "\n")
    np.savez(HERE / "reconstructed_scores.npz", keys=forecasts["keys"], y=y, B_loss=losses["B"], H_loss=losses["H"])
    print(json.dumps({k: v for k, v in out.items() if k != "chronology"}, indent=2))

if __name__ == "__main__":
    main()
