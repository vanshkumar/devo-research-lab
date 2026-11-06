"""Independent category reconstruction and source perturbation; imports no author code.

The likelihood derivative is computed through normalized exemplar masses. All
estimation/selection consumes source responses only. See CONTRARY_PLAN.md.
"""
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
import time
import zipfile
import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.special import logsumexp
from first_calculation import AUTHOR, HERE, HARD, original_inputs

T0 = time.monotonic()
CONTRARY_STOP = dt.datetime.fromisoformat("2026-11-01T10:18:00+00:00")
AGE = np.linspace(287 / 288, 0, 288)
LIMIT_RSS = 800_000_000


def now():
    return dt.datetime.now(dt.timezone.utc)


def check(deadline=HARD):
    if now() >= deadline:
        raise RuntimeError("Predeclared execution deadline reached")
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > LIMIT_RSS:
        raise RuntimeError("Peak RSS limit exceeded; stop scientific work")


def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2, allow_nan=False))


def resources():
    return dict(utc=now().isoformat(), elapsed_seconds=time.monotonic() - T0,
                peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                numpy=np.__version__, scipy=scipy.__version__, scientific_processes=1,
                numeric_threads_requested=1, public_operations=0)


def read_json(name):
    return json.loads((AUTHOR / name).read_text())


def load_npz(name):
    with np.load(AUTHOR / name) as f:
        return {k: f[k] for k in f.files}


def softmax(a):
    v = np.exp(a - np.max(a, axis=-1, keepdims=True))
    return v / v.sum(axis=-1, keepdims=True)


def selected_nll(prob, answers):
    return -np.log(np.maximum(np.take_along_axis(prob, answers[..., None], axis=-1)[..., 0], 1e-12))


def data_from_raw():
    geom, people, original_reads = original_inputs()
    roles = {k: [] for k in ("source", "evaluation")}
    joins = []
    for person in people:
        if len(person["rows"]) != 672:
            continue
        check()
        tr, te = person["train"], person["novel"]
        labels = np.array([person["mapping"][r[9][0]] for r in tr], dtype=int)
        x = np.array([geom[r[9]] for r in tr], dtype=int)
        q = np.array([geom[r[9]] for r in te], dtype=int)
        mismatches = q[:, None, :] != x[None, :, :]
        relation = np.empty((288, 8), dtype=np.int8)
        relation[0] = 4
        for t in range(1, 288):
            if labels[t] == labels[t-1]:
                relation[t] = (x[t] != x[t-1]).astype(np.int8)
            else:
                relation[t] = 2 + (x[t] != x[t-1]).astype(np.int8)
        counts = np.stack([(mismatches & (relation[None] == k)).sum(axis=-1) for k in range(5)], axis=-1)
        hamming = mismatches.sum(axis=-1) / 8
        last = {}
        gaps = []
        for t, row in enumerate(tr):
            gaps.append(t - last[row[9]] if row[9] in last else 1)
            last[row[9]] = t
        gaplog = np.log(np.array(gaps) + 1.)
        features = np.zeros((24, 3, 9))
        for k in range(3):
            locations = np.where(labels == k)[0]
            distances = hamming[:, locations]
            features[:, k, 0] = np.log(1 + len(locations))
            features[:, k, 1:4] = np.stack([np.mean(np.exp(-c * distances), axis=1) for c in (1., 4., 16.)], axis=-1)
            features[:, k, 4] = -np.min(distances, axis=1)
            features[:, k, 5] = -np.mean(distances, axis=1)
            for d in range(8):
                matches = (q[:, d, None] == x[locations, d][None]).sum(axis=1)
                vocabulary = len(set(x[:, d])) + 1
                features[:, k, 6] += np.log((matches + 1) / (len(locations) + vocabulary)) / 8
            features[:, k, 7] = -AGE[locations[-1]]
            features[:, k, 8] = np.mean(gaplog[locations]) / np.log(289.)
        truth = np.array([person["mapping"][r[9][0]] for r in te], dtype=int)
        answers = np.array([int(r[5]) for r in te], dtype=int)
        assert np.all((0 <= answers) & (answers < 3))
        assert all(r[9] not in {s[9] for s in tr} for r in te)
        role = "source" if "BI" in person["lines"][2] else "evaluation"
        roles[role].append(dict(ids=person["person"], D=counts, labels=labels, loggap=gaplog,
                                E=features, truth=truth, y=answers))
        joins.append(dict(person=person["person"], sha256=person["sha256"], role=role))
    data = {}
    for role, members in roles.items():
        data[role] = {key: np.array([d[key] for d in members]) for key in members[0]}
        data[role]["D"] = data[role]["D"].astype(float)
        data[role]["onehot_labels"] = np.eye(3)[data[role]["labels"]]
    return data, joins, original_reads


def exemplar(theta, model, d, response=None, weights=None):
    """Mass-based independent implementation; return probability or NLL+gradient."""
    if model == "P":
        enc = np.concatenate((np.exp(theta[:3]), [1., 1.]))
        pars = theta[3:]
    else:
        enc = np.ones(5)
        pars = theta
    c, gamma = np.exp(pars[:2])
    decay, spacing, lapse = pars[2:]
    distance = np.sum(d["D"] * enc, axis=-1) / 8
    log_kernel = -c * distance - decay * AGE + spacing * d["loggap"][:, None]
    shift = np.max(log_kernel, axis=-1, keepdims=True)
    kernel = np.exp(log_kernel - shift)
    mass = np.einsum("pqt,ptk->pqk", kernel, d["onehot_labels"], optimize=False)
    log_mass = np.log(mass) + shift
    s = softmax(gamma * log_mass)
    prob = lapse / 3 + (1 - lapse) * s
    if response is None:
        return prob
    if weights is None:
        weights = np.ones(len(response))
    normalizer = weights.sum() * response.shape[1]
    chosen_s = np.take_along_axis(s, response[..., None], axis=-1)[..., 0]
    chosen_p = np.take_along_axis(prob, response[..., None], axis=-1)[..., 0]
    loss = float(np.sum(selected_nll(prob, response) * weights[:, None]) / normalizer)
    # The frozen objective clips probabilities at1e-12. Its derivative is zero
    # below that threshold; keep both likelihood and gradient finite at lapse0.
    chosen_safe = np.maximum(chosen_p, 1e-12)
    differentiable = chosen_p >= 1e-12
    residual = (1 - lapse) * chosen_s[..., None] / chosen_safe[..., None] * (s - np.eye(3)[response])
    residual *= differentiable[..., None]
    residual *= weights[:, None, None] / normalizer
    class_coeff = residual / mass
    item_coeff = np.take_along_axis(class_coeff, np.broadcast_to(d["labels"][:, None], kernel.shape), axis=-1)
    sensitivity = gamma * kernel * item_coeff
    nuisance = np.array([np.sum(sensitivity * (-c * distance)),
                         np.sum(residual * gamma * log_mass),
                         np.sum(sensitivity * (-AGE)),
                         np.sum(sensitivity * d["loggap"][:, None]),
                         np.sum((chosen_s - 1 / 3) / chosen_safe * differentiable * weights[:, None]) / normalizer])
    if model == "P":
        encoding = -c / 8 * np.einsum("pqt,pqte->e", sensitivity, d["D"][..., :3], optimize=False) * enc[:3]
        gradient = np.concatenate((encoding, nuisance))
    else:
        gradient = nuisance
    return loss, gradient


def gradient_check(d):
    records = []
    small = {k: v[:2] for k, v in d.items()}
    points = {"B": np.array([.4, -.2, .7, .1, .3]),
              "P": np.array([.3, -.4, .7, .4, -.2, .7, .1, .3])}
    for model, theta in points.items():
        loss, gradient = exemplar(theta, model, small, small["y"])
        numeric = []
        for j in range(len(theta)):
            step = np.zeros(len(theta)); step[j] = 1e-5
            a = exemplar(theta + step, model, small, small["y"])[0]
            b = exemplar(theta - step, model, small, small["y"])[0]
            numeric.append((a - b) / 2e-5)
        error = float(np.max(np.abs(gradient - numeric)))
        assert error < 2e-7
        records.append(dict(model=model, theta=theta.tolist(), loss=loss, analytic=gradient.tolist(), central_difference=numeric, max_absolute_error=error))
    return records


def independent_decision(prob, y, truth, indices=None):
    if indices is None:
        indices = np.random.default_rng(20261101).integers(len(y), size=(2000, len(y)))
    person = {k: np.mean(selected_nll(v, y), axis=1) for k, v in prob.items()}
    comparisons = {}
    for model in ("B", "E"):
        point = 1 - np.mean(person["P"]) / np.mean(person[model])
        draws = 1 - np.mean(person["P"][indices], axis=1) / np.mean(person[model][indices], axis=1)
        interval = np.quantile(draws, [.025, .975])
        comparisons[model] = dict(relative_gain=float(point), gain_interval=interval.tolist(),
                                  passes_relative_interval=bool(point >= .05 and interval[0] > 0))
    predicted = {k: float(np.mean(np.take_along_axis(v, truth[..., None], axis=-1))) for k, v in prob.items()}
    actual = float(np.mean(y == truth))
    bias = predicted["P"] - actual
    deletions = []
    for i in range(len(y)):
        keep = np.arange(len(y)) != i
        deletions.append({k: float(1 - np.mean(person["P"][keep]) / np.mean(person[k][keep])) for k in ("B", "E")})
    return dict(passes=bool(all(x["passes_relative_interval"] for x in comparisons.values()) and abs(bias) <= .10),
                nll={k: float(v.mean()) for k, v in person.items()}, comparisons=comparisons,
                observed_accuracy=actual, predicted_accuracy=predicted, P_accuracy_bias=bias,
                brier={k: float(np.mean(np.sum((v - np.eye(3)[y]) ** 2, axis=-1))) for k, v in prob.items()},
                per_person={k: v.tolist() for k, v in person.items()}, deletions=deletions)


def fit_exemplar(d, weights, model, nested=None, deadline=HARD):
    keep = weights > 0
    subset = {key: value[keep] for key, value in d.items()}
    w = weights[keep]
    starts = [np.array([0., 0., 0., 0., .2]), np.array([np.log(2), 0., 1., .3, .2])]
    bounds = [(-4., 4.), (-2., 2.), (0., 8.), (-2., 2.), (0., .95)]
    if model == "P":
        starts = [np.concatenate(([0., 0., 0.], starts[0])), np.concatenate(([1., -1., -1.], starts[1])), np.concatenate(([0., 0., 0.], nested))]
        bounds = [(-2., 2.)] * 3 + bounds
    runs = []
    def objective(theta):
        check(deadline)
        return exemplar(theta, model, subset, subset["y"], w)
    for start in starts:
        result = minimize(objective, start, jac=True, method="L-BFGS-B", bounds=bounds,
                          options=dict(maxiter=500, ftol=1e-11, gtol=1e-6, maxls=40))
        runs.append(dict(start=start.tolist(), theta=result.x.tolist(), nll=float(result.fun),
                         success=bool(result.success), message=str(result.message), nit=int(result.nit), nfev=int(result.nfev)))
    chosen = min(runs, key=lambda r: r["nll"])
    return dict(model=model, selected=chosen, runs=runs)


def e_standardize(raw, weights):
    normalizer = weights.sum() * raw.shape[1] * raw.shape[2]
    mean = np.sum(raw * weights[:, None, None, None], axis=(0, 1, 2)) / normalizer
    variance = np.sum((raw - mean) ** 2 * weights[:, None, None, None], axis=(0, 1, 2)) / normalizer
    sd = np.maximum(np.sqrt(variance), 1e-8)
    return mean, sd


def e_optimize(raw, y, weights, penalty, mean, sd, deadline):
    keep = weights > 0
    X = (raw[keep] - mean) / sd
    targets = y[keep]
    w = weights[keep]
    norm = w.sum() * y.shape[1]
    target_onehot = np.eye(3)[targets]
    def objective(beta):
        check(deadline)
        logits = np.einsum("pqkf,f->pqk", X, beta, optimize=False)
        p = softmax(logits)
        loss = np.sum((logsumexp(logits, axis=-1) - np.take_along_axis(logits, targets[..., None], axis=-1)[..., 0]) * w[:, None]) / norm
        gradient = np.einsum("pqkf,pqk->f", X, (p - target_onehot) * w[:, None, None], optimize=False) / norm
        return float(loss + penalty * np.dot(beta, beta) / 2), gradient + penalty * beta
    r = minimize(objective, np.zeros(raw.shape[-1]), jac=True, method="L-BFGS-B",
                 options=dict(maxiter=500, ftol=1e-12, gtol=1e-8))
    return r


def fit_empirical(d, weights, deadline=HARD):
    raw, y = d["E"], d["y"]
    active = np.flatnonzero(weights)
    assert len(active) > 1
    folds = []
    failures = []
    fits = 0
    for penalty in (.001, .01, .1, 1.):
        losses = []
        for person in active:
            fold_weights = weights.copy(); fold_weights[person] = 0
            mean, sd = e_standardize(raw, fold_weights)
            r = e_optimize(raw, y, fold_weights, penalty, mean, sd, deadline)
            fits += 1
            if not r.success:
                failures.append(dict(penalty=penalty, person=int(person), message=str(r.message)))
            p = softmax(np.einsum("qkf,f->qk", (raw[person] - mean) / sd, r.x, optimize=False))
            losses.append(float(selected_nll(p, y[person]).mean()))
        folds.append(dict(penalty=penalty, mean_nll=float(np.average(losses, weights=weights[active])),
                          held_identity_indices=active.tolist(), person_losses=losses))
    penalty = min(folds, key=lambda r: r["mean_nll"])["penalty"]
    mean, sd = e_standardize(raw, weights)
    r = e_optimize(raw, y, weights, penalty, mean, sd, deadline)
    fits += 1
    if not r.success:
        failures.append(dict(penalty=penalty, person="full", message=str(r.message)))
    return dict(penalty=penalty, coef=r.x.tolist(), mean=mean.tolist(), sd=sd.tolist(), CV=folds,
                optimizer_fits=fits, failures=failures, final_objective=float(r.fun))


def empirical_probability(fit, d):
    x = (d["E"] - np.array(fit["mean"])) / np.array(fit["sd"])
    return softmax(np.einsum("pqkf,f->pqk", x, np.array(fit["coef"]), optimize=False))


def pin_audit():
    results = {}
    for record, field in (("FREEZE.json", "pins"), ("MANIFEST.json", "artifacts")):
        expected = read_json(record)[field]
        checks = []
        for name, spec in expected.items():
            blob = (AUTHOR / name).read_bytes()
            matches = len(blob) == spec["bytes"] and hashlib.sha256(blob).hexdigest() == spec["sha256"]
            checks.append(dict(file=name, matches=matches, bytes=len(blob)))
            assert matches, name
        results[record] = checks
    pred = read_json("PREDICTION_PINS.json")
    assert hashlib.sha256((AUTHOR / "predictions.npz").read_bytes()).hexdigest() == pred["predictions_sha256"]
    return results


def audit():
    check()
    data, joins, reads = data_from_raw()
    original = load_npz("prepared.npz")
    array_checks = []
    for role, d in data.items():
        for key in ("D", "labels", "loggap", "E", "truth", "ids"):
            difference = float(np.max(np.abs(original[role + "_" + key] - d[key])))
            assert difference < 1e-13
            array_checks.append(dict(role=role, array=key, elements=int(d[key].size), max_absolute_error=difference))
    assert np.array_equal(data["source"]["y"], original["source_y"])
    del original
    fits = {k: read_json("FIT_" + k + ".json") for k in ("B", "P", "E")}
    probability = {}
    objective_checks = []
    for role, d in data.items():
        for model in ("B", "P"):
            theta = np.array(fits[model]["selected"]["theta"])
            probability[role + "_" + model] = exemplar(theta, model, d)
        probability[role + "_E"] = empirical_probability(fits["E"], d)
    for model in ("B", "P"):
        for run in fits[model]["runs"]:
            loss, grad = exemplar(np.array(run["theta"]), model, data["source"], data["source"]["y"])
            objective_checks.append(dict(model=model, nll=loss, recorded_nll=run["nll"], error=abs(loss - run["nll"]), gradient=grad.tolist()))
            assert abs(loss - run["nll"]) < 1e-12
    saved = load_npz("predictions.npz")
    pred_errors = {k: float(np.max(np.abs(v - saved[k]))) for k, v in probability.items()}
    assert max(pred_errors.values()) < 1e-12
    prob = {k: probability["evaluation_" + k] for k in ("P", "B", "E")}
    d = data["evaluation"]
    score = independent_decision(prob, d["y"], d["truth"])
    recorded_score = read_json("SCORES.json")
    assert score["passes"] == recorded_score["pass"]
    scalar_score_errors = {k: abs(score["nll"][k] - recorded_score["nll"][k]) for k in prob}
    for k in ("B", "E"):
        assert np.max(np.abs(np.array(score["comparisons"][k]["gain_interval"]) - recorded_score["comparisons"][k]["gain_interval"])) < 1e-12
    saved_controls = load_npz("control_outcomes.npz")["y"]
    recorded_controls = read_json("CONTROLS.json")["records"]
    rng = np.random.default_rng(20261102)
    control_checks = []
    for i in range(200):
        check()
        generator = "P" if i < 100 else "E"
        u = rng.random(d["truth"].shape)
        response = np.sum(u[..., None] > np.cumsum(prob[generator], axis=-1), axis=-1)
        assert np.array_equal(response, saved_controls[i])
        decision = independent_decision(prob, response, d["truth"])
        rec = recorded_controls[i]
        interval_error = max(np.max(np.abs(np.array(decision["comparisons"][k]["gain_interval"]) - rec["comparisons"][k]["gain_interval"])) for k in ("B", "E"))
        assert interval_error < 1e-12
        assert decision["passes"] == rec["pass"]
        control_checks.append(dict(generator=generator, replicate=i % 100, passes=decision["passes"], maximum_interval_error=float(interval_error)))
    np.savez_compressed(HERE / "reconstructed_forecasts.npz", **probability)
    result = dict(completed_utc=now().isoformat(), original_input_reads=reads, joins=joins,
                  array_checks=array_checks, probability_scalars=sum(v.size for v in probability.values()),
                  probability_errors=pred_errors, objective_checks=objective_checks,
                  analytic_gradient_checks=gradient_check(data["source"]), real_score=score,
                  real_nll_errors=scalar_score_errors, controls=control_checks,
                  signal_passes=sum(r["passes"] for r in control_checks[:100]),
                  null_passes=sum(r["passes"] for r in control_checks[100:]),
                  pins=pin_audit(), resources=resources(),
                  limitations="Saved original P/B parameters evaluated, not yet optimizer-refitted; original E reselection is a separate next phase. Original controls regenerate 100800 conditional answers/rescore all 200 decisions; no full source-generation/refitting, boundary power or coverage.")
    save("RECONSTRUCTION.json", result)
    print(json.dumps(dict(stage="audit", probability_scalars=result["probability_scalars"], maximum_probability_error=max(pred_errors.values()),
                          real_score={k: score[k] for k in ("passes", "nll", "comparisons", "P_accuracy_bias")},
                          signal_passes=result["signal_passes"], null_passes=result["null_passes"], resources=resources()), indent=2), flush=True)


def full_source_refit():
    data, joins, reads = data_from_raw()
    gradient = gradient_check(data["source"])
    weights = np.ones(len(data["source"]["y"]))
    B = fit_exemplar(data["source"], weights, "B")
    print("original B refit", B["selected"]["nll"], flush=True)
    P = fit_exemplar(data["source"], weights, "P", np.array(B["selected"]["theta"]))
    print("original P refit", P["selected"]["nll"], flush=True)
    E = fit_empirical(data["source"], weights)
    print("original E reselected", E["penalty"], [(r["penalty"], r["mean_nll"]) for r in E["CV"]], flush=True)
    d = data["evaluation"]
    prob = {"P": exemplar(np.array(P["selected"]["theta"]), "P", d),
            "B": exemplar(np.array(B["selected"]["theta"]), "B", d), "E": empirical_probability(E, d)}
    result = dict(completed_utc=now().isoformat(), B=B, P=P, E=E, gradients=gradient,
                  evaluation=independent_decision(prob, d["y"], d["truth"]), resources=resources(),
                  original_input_reads=reads, scope="Independent original full-source local optimizer refits using analytic gradients and empirical grouped-by-identity LOO reselection. No global optimum certification; saved frozen result unchanged.")
    save("ORIGINAL_REFITS.json", result)
    print(json.dumps(dict(stage="original_refits", B_source_nll=B["selected"]["nll"], P_source_nll=P["selected"]["nll"],
                          E_penalty=E["penalty"], evaluation=result["evaluation"]["comparisons"], resources=resources()), indent=2), flush=True)


def contrary_summary(records):
    if not records:
        return {}
    gains = {k: np.array([r["evaluation"]["comparisons"][k]["relative_gain"] for r in records]) for k in ("B", "E")}
    bias = np.array([r["evaluation"]["P_accuracy_bias"] for r in records])
    return dict(completed=len(records), B_gain_percentiles=np.quantile(gains["B"], [.025, .5, .975]).tolist(),
                E_gain_percentiles=np.quantile(gains["E"], [.025, .5, .975]).tolist(),
                B_positive=int(np.sum(gains["B"] > 0)), E_positive=int(np.sum(gains["E"] > 0)),
                both_positive=int(np.sum((gains["B"] > 0) & (gains["E"] > 0))),
                B_point_at_least_5percent=int(np.sum(gains["B"] >= .05)), E_point_at_least_5percent=int(np.sum(gains["E"] >= .05)),
                full_passes=sum(r["evaluation"]["passes"] for r in records),
                P_accuracy_bias_percentiles=np.quantile(bias, [.025, .5, .975]).tolist(),
                calibration_within_10pp=int(np.sum(np.abs(bias) <= .1)),
                E_penalties={str(k): sum(r["E"]["penalty"] == k for r in records) for k in (.001, .01, .1, 1.)},
                B_P_optimizer_failures=sum(sum(not run["success"] for run in r[m]["runs"]) for r in records for m in ("B", "P")),
                E_optimizer_failures=sum(len(r["E"]["failures"]) for r in records))


def contrary():
    check(CONTRARY_STOP)
    data, joins, reads = data_from_raw()
    gradients = gradient_check(data["source"])
    rng = np.random.default_rng(20261113)
    samples = rng.integers(len(data["source"]["y"]), size=(48, len(data["source"]["y"])))
    records = []
    plan_sha = hashlib.sha256((HERE / "CONTRARY_PLAN.md").read_bytes()).hexdigest()
    result = dict(plan_sha256=plan_sha, source_identity_samples=data["source"]["ids"][samples].tolist(),
                  started_utc=now().isoformat(), original_input_reads=reads, gradients=gradients,
                  records=records, summary={}, planned_replicates=48,
                  scope="Finite postvalidation paired source-person resampling with grouped duplicate-identity selection; not calibrated confidence, replacement validation or global optimization.")
    save("CONTRARY.json", result)
    for i, sample in enumerate(samples):
        try:
            check(CONTRARY_STOP)
            weights = np.bincount(sample, minlength=len(data["source"]["y"])).astype(float)
            B = fit_exemplar(data["source"], weights, "B", deadline=CONTRARY_STOP)
            P = fit_exemplar(data["source"], weights, "P", np.array(B["selected"]["theta"]), deadline=CONTRARY_STOP)
            assert P["selected"]["nll"] <= B["selected"]["nll"] + 1e-6
            E = fit_empirical(data["source"], weights, deadline=CONTRARY_STOP)
            d = data["evaluation"]
            prob = {"P": exemplar(np.array(P["selected"]["theta"]), "P", d),
                    "B": exemplar(np.array(B["selected"]["theta"]), "B", d), "E": empirical_probability(E, d)}
            score = independent_decision(prob, d["y"], d["truth"])
            records.append(dict(replicate=i, source_identities=data["source"]["ids"][sample].tolist(),
                                multiplicities=weights.astype(int).tolist(), B=B, P=P, E=E, evaluation=score))
            result["summary"] = contrary_summary(records)
            result["resources"] = resources()
            result["last_completed_utc"] = now().isoformat()
            save("CONTRARY.json", result)
            print(json.dumps(dict(stage="contrary", replicate=i, gains={k: score["comparisons"][k]["relative_gain"] for k in ("B", "E")},
                                  passes=score["passes"], elapsed_seconds=resources()["elapsed_seconds"])), flush=True)
        except Exception as error:
            result["stopped_at_replicate"] = i
            result["stop_reason"] = repr(error)
            result["resources"] = resources()
            save("CONTRARY.json", result)
            raise
    result["completed_utc"] = now().isoformat()
    result["resources"] = resources()
    save("CONTRARY.json", result)
    print(json.dumps(dict(stage="contrary_complete", summary=result["summary"], resources=resources()), indent=2), flush=True)


if __name__ == "__main__":
    {"audit": audit, "original_refits": full_source_refit, "contrary": contrary}[sys.argv[1]]()
