"""Independent full raw-to-feature/prediction reconstruction, no author imports.

The grid uses explicit state-transition branches and dense drift transitions,
independent of the author's FFT convolution implementation.
"""
import os
for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"
import datetime, hashlib, io, json, math, pathlib, resource, time, zipfile
import numpy as np
from scipy.io import loadmat

HERE = pathlib.Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "tasks/surprise-history-forecast-2026-11-01"

def angle(x):
    return math.atan2(math.sin(float(x)), math.cos(float(x)))

def approximate(errors, blocks, context):
    result = []
    previous_ru, previous_event, previous_error = None, None, None
    for t, error in enumerate(errors):
        if t == 0 or blocks[t] != blocks[t - 1]:
            ru = .99
        else:
            r, p, e = previous_ru, previous_event, previous_error
            if context == 1:
                variance = .1 * (p + (1 - p) * r) + p * (1 - p) * (e * (1 - r)) ** 2
            else:
                run_length = (1 - r) / r
                variance = .1 * (p / run_length + (1 - p) / (run_length + 1)) + p * (1 - p) * (e * r) ** 2 + 1 / 30
            ru = variance / (variance + .1)
        total_variance = .1 / (1 - ru)
        same = (6 / 7) * math.exp(-error ** 2 / (2 * total_variance)) / math.sqrt(2 * math.pi * total_variance)
        new = 1 / (14 * math.pi)
        event = new / (new + same)
        rate = ru + event * (1 - ru) if context else ru * (1 - event)
        result.append((ru, event, rate * error))
        previous_ru, previous_event, previous_error = ru, event, error
    return np.array(result)

def grid(outcomes, blocks, context):
    theta = np.arange(360) * math.pi / 180
    source_uniform = np.full(360, 1 / 359)
    source_uniform[[0, 359]] /= 2
    drift = np.exp(30 * (np.cos(theta[:, None] - theta[None, :]) - 1))
    drift /= drift.sum(axis=0, keepdims=True)
    posterior = np.zeros((4, 360))
    posterior[0] = 1 / 360
    answers = []
    for t, outcome in enumerate(outcomes):
        fresh = t == 0 or blocks[t] != blocks[t - 1]
        regular = np.zeros_like(posterior)
        event = np.zeros_like(posterior)
        if context and fresh:
            event[3] = source_uniform
        else:
            if context:
                prior = posterior
            elif fresh:
                prior = np.repeat((posterior.sum(axis=1) / 360)[:, None], 360, axis=1)
            else:
                prior = np.einsum("ij,sj->si", drift, posterior)
            for remaining in range(4):
                if remaining > 0:
                    regular[remaining - 1] += prior[remaining]
                else:
                    regular[0] += .75 * prior[0]
                    event[3] += .25 * (prior[0].sum() * source_uniform if context else prior[0])
        likelihood = np.zeros(360)
        for offset, weight in ((-.5, 1 / 6), (0., 4 / 6), (.5, 1 / 6)):
            likelihood += weight * np.exp(10 * (np.cos(outcome + offset * math.pi / 180 - theta) - 1))
        likelihood *= (math.pi / 180) / (2 * math.pi * np.i0(10) * math.exp(-10))
        regular *= likelihood
        if context:
            event *= likelihood
        else:
            index = round(math.degrees(outcome)) % 360
            event *= source_uniform[index]
        evidence = regular.sum() + event.sum()
        event_probability = event.sum() / evidence
        posterior = (regular + event) / evidence
        marginal = posterior.sum(axis=0)
        real = float(np.sum(marginal * np.cos(theta)))
        imaginary = float(np.sum(marginal * np.sin(theta)))
        answers.append((math.atan2(imaginary, real), math.hypot(real, imaginary), float(event_probability)))
    return np.array(answers)

def features(raw, context):
    prediction = [math.radians(float(v)) for v in raw["pred"]]
    outcome = [math.radians(float(v)) for v in raw["outcome"]]
    blocks = raw["block"]
    errors = [angle(o - p) for o, p in zip(outcome, prediction)]
    approx = approximate(errors, blocks, context)
    inferred = grid(outcome, blocks, context)
    rows = []
    for t in range(240):
        if t == 0 or blocks[t] != blocks[t - 1]:
            start = t
            absolute_error_states, event_states = [0., 0.], [0., 0.]
            numerator, denominator = [.05] * 3, [.1] * 3
        else:
            old_error = errors[t - 1]
            old_update = angle(prediction[t] - prediction[t - 1])
            numerator[0] += old_error * old_update
            denominator[0] += old_error ** 2
            for j, alpha in enumerate((.25, .0625)):
                numerator[j + 1] = (1 - alpha) * numerator[j + 1] + alpha * old_error * old_update
                denominator[j + 1] = (1 - alpha) * denominator[j + 1] + alpha * old_error ** 2
                absolute_error_states[j] = (1 - alpha) * absolute_error_states[j] + alpha * abs(old_error) / math.pi
                event_states[j] = (1 - alpha) * event_states[j] + alpha * approx[t - 1, 1]
        error = errors[t]
        ru, event, unfit_update = approx[t]
        inferred_aim, resultant, inferred_event = inferred[t]
        base = [1.]
        for order in range(1, 5):
            base += [math.sin(order * error), math.cos(order * error)]
        base += [math.sin(unfit_update), math.cos(unfit_update), ru, event,
                 ru * math.sin(error), event * math.sin(error), ru * event * math.sin(error)]
        delta = angle(inferred_aim - prediction[t])
        base += [math.sin(delta), math.cos(delta), resultant, inferred_event, resultant * math.sin(error)]
        base += [float(raw["hit"][t]), float(raw["actRew"][t]) - 1, math.log1p(float(raw["allASS"][t]))]
        lags = [angle(prediction[t] - prediction[t - 1]) if t > start else 0.,
                angle(prediction[t - 1] - prediction[t - 2]) if t > start + 1 else 0.,
                errors[t - 1] if t > start else 0.]
        for lag in lags:
            base += [math.sin(lag), math.cos(lag)]
        for n, d in zip(numerator, denominator):
            gain = max(-1., min(2., n / d))
            base += [math.sin(gain * error), math.cos(gain * error)]
        first = (int(raw["cBal"][t]) == 2) if context else (int(raw["cBal"][t]) == 1)
        base += [(t - start) / 59, (int(blocks[t]) - 1) / 3, float(first)]
        if t > start:
            circular = []
            for width in (4, 16):
                past = outcome[max(start, t - width):t]
                circular.append(complex(sum(math.cos(o) for o in past), sum(math.sin(o) for o in past)) / len(past))
            z4, z16 = circular
            difference = math.atan2((z4 * z16.conjugate()).imag, (z4 * z16.conjugate()).real)
            states = absolute_error_states + event_states + [abs(z4), abs(z16), math.sin(difference), math.cos(difference)]
        else:
            states = absolute_error_states + event_states + [0., 0., 0., 0.]
        history = []
        for state in states:
            history += [state, state * math.sin(error), state * math.cos(error)]
        if t < 239 and blocks[t] == blocks[t + 1]:
            b = np.array(base)
            h = np.array(history)
            rows.append((int(raw["trial"][t]), np.r_[b * (1 - context), b * context],
                np.r_[h * (1 - context), h * context], angle(prediction[t + 1] - prediction[t]),
                np.array([error, ru, event, unfit_update, prediction[t], outcome[t], float(raw["hit"][t]), inferred_event])))
    return rows

def main():
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    seconds = time.monotonic()
    split = json.loads((SOURCE / "SPLIT.json").read_text())
    participants = split["participants"]
    ranked = sorted([p["id"] for p in participants if p["id"] != "342"],
        key=lambda sid: hashlib.sha256(("surprise-history-20261101:" + sid).encode()).hexdigest())
    expected_dev = {"342", *ranked[:19]}
    assert expected_dev == {p["id"] for p in participants if p["split"] == "development"}
    saved = {name: dict(np.load(SOURCE / (name + "_features.npz"), allow_pickle=False)) for name in ("development", "evaluation")}
    lookups = {name: {tuple(map(int, key)): j for j, key in enumerate(saved[name]["keys"])} for name in saved}
    reconstructed = {name: {key: np.zeros_like(saved[name][key]) for key in ("B", "extra", "y", "diagnostics")} for name in saved}
    seen = {name: set() for name in saved}
    audits = []
    decoded = 0
    with zipfile.ZipFile(SOURCE / "behavior_zip.source") as archive:
        for person in participants:
            payload = archive.read(person["member"])
            decoded += len(payload)
            content = loadmat(io.BytesIO(payload), simplify_cells=True)
            for context, prefix in ((0, "DataOddball_"), (1, "DataCP_")):
                raw = content[next(k for k in content if k.startswith(prefix))]
                assert np.array_equal(raw["trial"], np.arange(1, 241))
                assert np.array_equal(raw["block"], np.repeat(np.arange(1, 5), 60))
                assert {int(value) for value in raw["ID"]} == {int(person["id"])}
                rows = features(raw, context)
                for trial, b, h, y, diagnostics in rows:
                    key = (int(person["id"]), context, int(raw["block"][trial - 1]), trial)
                    assert key not in seen[person["split"]]
                    seen[person["split"]].add(key)
                    row = lookups[person["split"]][key]
                    for name, value in (("B", b), ("extra", h), ("y", y), ("diagnostics", diagnostics)):
                        reconstructed[person["split"]][name][row] = value
                events = np.asarray(raw["cp"] if context else raw["oddBall"]) == 1
                bad_gaps = 0
                for block in range(1, 5):
                    indices = np.flatnonzero(events & (raw["block"] == block))
                    bad_gaps += int(np.sum(np.diff(indices) < 4))
                hit_reconstructed = np.array([abs(angle(math.radians(float(o) - float(p)))) <= math.radians(float(size)) / 2
                    for o, p, size in zip(raw["outcome"], raw["pred"], raw["allASS"])])
                audits.append({"id": person["id"], "context": context, "rows": 240, "eligible": len(rows),
                    "no_short_within_block_event_gaps": bad_gaps == 0,
                    "hit_discrepancies": int(np.sum(hit_reconstructed != raw["hit"])),
                    "prediction_within_trial": int(np.sum((raw["timestampOnset"] <= raw["timestampPrediction"]) & (raw["timestampPrediction"] < raw["timestampOffset"]))),
                    "next_onset_after_offset": int(np.sum(raw["timestampOffset"][:-1] < raw["timestampOnset"][1:]))})
            print("Reconstructed", person["id"], person["split"], "seconds", round(time.monotonic() - seconds, 2), flush=True)
    differences = {}
    for group in saved:
        assert seen[group] == set(lookups[group])
        differences[group] = {key: float(np.max(abs(reconstructed[group][key] - saved[group][key]))) for key in reconstructed[group]}
    forecasts = dict(np.load(SOURCE / "predictions.npz", allow_pickle=False))
    replays = {}
    for name in ("B", "H"):
        fitted = dict(np.load(SOURCE / ("fitted_" + name + ".npz"), allow_pickle=False))
        x = reconstructed["evaluation"]["B"] if name == "B" else np.column_stack((reconstructed["evaluation"]["B"], reconstructed["evaluation"]["extra"]))
        z = np.column_stack((np.ones(len(x)), (x - fitted["mean"]) / fitted["scale"]))
        vector = np.einsum("ni,ij->nj", z, fitted["coef"])
        hat = np.arctan2(vector[:, 1], vector[:, 0])
        hat[np.linalg.norm(vector, axis=1) < 1e-12] = 0
        replays[name] = float(np.max(abs(np.angle(np.exp(1j * (hat - forecasts[name]))))))
    containers = (SOURCE / "behavior_zip.source").stat().st_size
    npz_decoded = 0
    for filename in ("development_features.npz", "evaluation_features.npz", "predictions.npz", "fitted_B.npz", "fitted_H.npz"):
        containers += (SOURCE / filename).stat().st_size
        with zipfile.ZipFile(SOURCE / filename) as archive:
            npz_decoded += sum(item.file_size for item in archive.infolist())
    out = {"started_at": start, "ended_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "author_code_imported": False, "split_identity_hash_exact": True,
        "raw_people": 39, "raw_rows": 18720, "reconstructed_updates": 18408,
        "full_feature_max_differences": differences, "forecast_max_radians_from_independent_raw_features": replays,
        "source_grid_method": "Explicit remaining-safe-count branches and dense circular VM drift matrix; 360 grid/Simpson observation bins match frozen approximation. All 78 original full context records reconstructed, not only examples.",
        "audits": audits, "input_container_bytes": containers, "decoded_MAT_bytes": decoded,
        "decoded_array_bytes": npz_decoded, "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "elapsed_seconds": time.monotonic() - seconds,
        "scope": "Matches frozen numerical approximation to allowed original input fields, with independent raw parsing, scalar histories/reference and non-FFT grid. Does not certify exact continuous Bayesian inference, hardware clocks or unobserved biology."}
    (HERE / "RECONSTRUCTION.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "audits"}, indent=2))
    assert max(v for group in differences.values() for v in group.values()) < 1e-8
    assert max(replays.values()) < 1e-8

if __name__ == "__main__":
    main()
