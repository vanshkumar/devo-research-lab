"""Independent generator/refit checks for two controls and 200-row score audit."""
import os
for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"
import datetime, json, math, pathlib, resource, zipfile
import numpy as np
from contrary import SourceFit

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "tasks/surprise-history-forecast-2026-11-01"

def wrapped(x):
    return np.arctan2(np.sin(x), np.cos(x))

def independent_noise(keys, generator):
    offsets = {person: generator.normal(0, .1) for person in np.unique(keys[:, 0])}
    noise = np.zeros(len(keys))
    last = None
    for j, key in enumerate(keys):
        block = tuple(key[:3])
        if block != last:
            value = generator.normal(0, .5)
        else:
            value = .35 * value + generator.normal(0, .5 * math.sqrt(1 - .35 ** 2))
        noise[j] = offsets[key[0]] + value
        last = block
    return noise

def score(keys, y, b, h, seed):
    people = np.unique(keys[:, 0])
    lb, lh = 1 - np.cos(y - b), 1 - np.cos(y - h)
    pb = np.array([lb[keys[:, 0] == person].mean() for person in people])
    ph = np.array([lh[keys[:, 0] == person].mean() for person in people])
    draws = np.random.default_rng(seed).integers(0, len(people), (10000, len(people)))
    interval = np.quantile(1 - ph[draws].mean(axis=1) / pb[draws].mean(axis=1), [.025, .975])
    gain = float(1 - ph.mean() / pb.mean())
    contexts = []
    for context in (0, 1):
        selected = keys[:, 1] == context
        contexts.append(float(1 - lh[selected].mean() / lb[selected].mean()))
    return {"gain": gain, "bootstrap95": interval.tolist(), "context_gains": contexts,
        "passes": bool(gain >= .05 and interval[0] > 0 and min(contexts) > 0)}

def main():
    began = datetime.datetime.now(datetime.timezone.utc).isoformat()
    d = dict(np.load(SOURCE / "development_features.npz", allow_pickle=False))
    e = dict(np.load(SOURCE / "evaluation_features.npz", allow_pickle=False))
    controls = json.loads((SOURCE / "CONTROLS.json").read_text())
    state_d = d["extra"][:, 0] + d["extra"][:, 24]
    state_e = e["extra"][:, 0] + e["extra"][:, 24]
    mean, sd = d["B"].mean(axis=0), d["B"].std(axis=0)
    sd[sd < 1e-10] = 1
    z = np.column_stack((np.ones(len(state_d)), (d["B"] - mean) / sd))
    ze = np.column_stack((np.ones(len(state_e)), (e["B"] - mean) / sd))
    penalty_rows = np.diag(np.r_[0., np.repeat(math.sqrt(.001), d["B"].shape[1])])
    augmented = np.vstack((z, penalty_rows))
    targets = np.r_[state_d, np.zeros(z.shape[1])]
    coefficient = np.linalg.lstsq(augmented, targets, rcond=None)[0]
    residual_d = state_d - np.einsum("ni,i->n", z, coefficient)
    residual_e = state_e - np.einsum("ni,i->n", ze, coefficient)
    scale = residual_d.std()
    hd, he = np.clip(residual_d / scale, -3, 3), np.clip(residual_e / scale, -3, 3)
    examples = {}
    for label, beta, offset in (("null", 0., 0), ("positive", .35, 10000)):
        generator = np.random.default_rng(20261101 + offset)
        mu_d = wrapped(d["diagnostics"][:, 0] + beta * hd)
        mu_e = wrapped(e["diagnostics"][:, 0] + beta * he)
        yd = wrapped(mu_d + independent_noise(d["keys"], generator))
        ye = wrapped(mu_e + independent_noise(e["keys"], generator))
        saved = dict(np.load(SOURCE / ("control_" + label + "_example.npz"), allow_pickle=False))
        assert np.array_equal(saved["keys"], e["keys"])
        differences = {"mean": float(np.max(abs(wrapped(mu_e - saved["mean"])))),
            "y": float(np.max(abs(wrapped(ye - saved["y"]))))}
        predictions, penalties = {}, {}
        for name in ("B", "H"):
            x = d["B"] if name == "B" else np.column_stack((d["B"], d["extra"]))
            xe = e["B"] if name == "B" else np.column_stack((e["B"], e["extra"]))
            fitter = SourceFit(x, yd, d["keys"][:, 0])
            model, penalties[name], _ = fitter.choose(np.ones(20, dtype=int))
            predictions[name] = fitter.predict(model, xe)
            differences[name] = float(np.max(abs(wrapped(predictions[name] - saved[name]))))
        record = next(r for r in controls["rows"] if r["label"] == label and r["rep"] == 0)
        scoring = score(e["keys"], ye, predictions["B"], predictions["H"], 20261101 + offset + 30000)
        examples[label] = {"max_differences_radians": differences, "selected_penalties": penalties,
            "score": scoring, "gain_difference": scoring["gain"] - record["gain"],
            "bootstrap_max_difference": float(np.max(abs(np.array(scoring["bootstrap95"]) - record["bootstrap95"]))) }
        assert max(differences.values()) < 1e-8
        assert penalties == record["lambdas"]
        assert abs(scoring["gain"] - record["gain"]) < 1e-8
    reconstructed_rows, max_gain_difference, max_interval_difference = [], 0., 0.
    for record in controls["rows"]:
        pb, ph = np.array(record["person_loss_B"]), np.array(record["person_loss_H"])
        draw = np.random.default_rng(record["seed"] + 30000).integers(0, 19, (10000, 19))
        interval = np.quantile(1 - ph[draw].mean(axis=1) / pb[draw].mean(axis=1), [.025, .975])
        gain = float(1 - ph.mean() / pb.mean())
        passes = bool(gain >= .05 and interval[0] > 0 and all(v["gain"] > 0 for v in record["contexts"].values()))
        assert passes == record["passes"]
        max_gain_difference = max(max_gain_difference, abs(gain - record["gain"]))
        max_interval_difference = max(max_interval_difference, float(np.max(abs(interval - record["bootstrap95"]))))
        reconstructed_rows.append({"label": record["label"], "passes": passes, "gain": gain})
    summary = {label: {"n": sum(r["label"] == label for r in reconstructed_rows),
        "passes": sum(r["label"] == label and r["passes"] for r in reconstructed_rows),
        "mean_gain": float(np.mean([r["gain"] for r in reconstructed_rows if r["label"] == label]))} for label in ("null", "positive")}
    attenuation = math.exp(-.5 * (.1 ** 2 + .5 ** 2))
    expected_oracle = 1 - attenuation
    expected_pe = float(np.mean(1 - attenuation * np.cos(.35 * he)))
    containers, decoded = 0, 0
    for filename in ("development_features.npz", "evaluation_features.npz", "control_null_example.npz", "control_positive_example.npz"):
        containers += (SOURCE / filename).stat().st_size
        with zipfile.ZipFile(SOURCE / filename) as archive:
            decoded += sum(item.file_size for item in archive.infolist())
    out = {"started_at": began, "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "author_code_imported": False, "source_signal_sd_independent": float(scale),
        "signal_sd_difference": float(scale - controls["signal_training_sd"]), "examples": examples,
        "all_200_scores_from_saved_person_losses": {"summary": summary, "max_gain_difference": max_gain_difference,
            "max_bootstrap_interval_difference": max_interval_difference},
        "analytic_marginal_oracle_expected_loss": expected_oracle,
        "analytic_positive_current_PE_expected_loss": expected_pe,
        "analytic_positive_oracle_fraction_vs_current_PE": float(1 - expected_oracle / expected_pe),
        "input_container_bytes": containers, "decoded_array_bytes": decoded,
        "control_json_bytes": (SOURCE / "CONTROLS.json").stat().st_size,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "scope": "Both rep0 synthetic target generators, source-only residual construction, all-penalty refits and forecasts independently reconstructed; other 198 target/refit runs NOT rerun, only saved person-loss score/interval summaries audited. Fixed real response histories do not regenerate with synthetic updates; large .35rad signal, not a 5% boundary-power, human trajectory or interval-coverage test."}
    (HERE / "CONTROL_AUDIT.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
