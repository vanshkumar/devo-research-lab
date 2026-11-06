#!/usr/bin/env python3
"""Two synthetic developmental-environment pilots. Requires NumPy only.

Run from repository root: .venv/bin/python experiments/development/run.py
Outputs are deterministic for a given NumPy version. No empirical claims.
"""
import argparse
import csv
import json
import math
import platform
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CONFIG = {
    "seeds": list(range(40)), "train_per_environment": 2000,
    "test_per_environment": 10000, "core_noise_sd": 1.0,
    "shortcut_noise_sd": 0.25, "train_shortcut_agreement": [0.95, 0.50],
    "test_shortcut_agreement": [0.95, 0.50, 0.05],
    "learning_rate": 0.03, "l2": 0.01,
    "causal_sample_sizes": [1000, 100000],
    "ability_prevalence": 0.5, "selection_agreement": 0.8,
    "outcome_ability_agreement": 0.9, "pretest_ability_agreement": 0.8,
}


def save_csv(path, rows):
    with path.open("w", newline="") as f:
        out = csv.DictWriter(f, fieldnames=list(rows[0]))
        out.writeheader()
        out.writerows(rows)


def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -40, 40)))


def mv(X, w):
    # einsum avoids spurious Accelerate matmul warnings on this ARM environment.
    return np.einsum("ij,j->i", X, w)


def make_task(rng, n, p_short):
    y = rng.integers(0, 2, n)
    signed_y = 2 * y - 1
    core = signed_y + CONFIG["core_noise_sd"] * rng.normal(size=n)
    agreement = np.where(rng.random(n) < p_short, 1, -1)
    short = signed_y * agreement + CONFIG["shortcut_noise_sd"] * rng.normal(size=n)
    return np.column_stack([np.ones(n), core, short]), y


def objective(X, y, w):
    z = mv(X, w)
    return float(np.mean(np.logaddexp(0, z) - y * z) + 0.5 * CONFIG["l2"] * (w @ w))


def converge(X, y, initial):
    """Damped Newton with directly checked optimality residual."""
    w = initial.copy()
    for step in range(100):
        prob = sigmoid(mv(X, w))
        grad = np.einsum("ij,i->j", X, prob - y) / len(y) + CONFIG["l2"] * w
        if np.linalg.norm(grad) < 1e-11:
            break
        hess = np.einsum("ni,nj,n->ij", X, X, prob * (1 - prob)) / len(y)
        hess += CONFIG["l2"] * np.eye(X.shape[1])
        delta = np.linalg.solve(hess, grad)
        old = objective(X, y, w)
        rate = 1.0
        while objective(X, y, w - rate * delta) > old - 1e-4 * rate * (grad @ delta):
            rate *= 0.5
            if rate < 1e-12:
                break
        w -= rate * delta
    residual = np.linalg.norm(np.einsum("ij,i->j", X, sigmoid(mv(X, w)) - y) / len(y) + CONFIG["l2"] * w)
    assert np.isfinite(w).all() and residual < 1e-8, "failed optimizer control"
    return w, float(residual), step + 1


def curriculum(seeds):
    rows, diagnostics = [], []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        n = CONFIG["train_per_environment"]
        Xe, ye = make_task(rng, n, 0.95)
        Xh, yh = make_task(rng, n, 0.50)
        X, y = np.concatenate([Xe, Xh]), np.concatenate([ye, yh])
        easy_idx, hard_idx = rng.permutation(n), n + rng.permutation(n)
        schedules = {
            "easy_then_hard": np.concatenate([easy_idx, hard_idx]),
            "hard_then_easy": np.concatenate([hard_idx, easy_idx]),
            "shuffled": rng.permutation(2 * n),
            "alternating": np.column_stack([easy_idx, hard_idx]).ravel(),
        }
        # Independent test streams are fixed across schedules; no tuning on them.
        tests = {p: make_task(np.random.default_rng(seed + 10000 + j * 1000),
                             CONFIG["test_per_environment"], p)
                 for j, p in enumerate(CONFIG["test_shortcut_agreement"])}
        converged = []
        for schedule, order in schedules.items():
            assert np.array_equal(np.sort(order), np.arange(2 * n)), "unequal exposure"
            w = np.zeros(3)
            for idx in order:
                prob = sigmoid(float(X[idx] @ w))
                w -= CONFIG["learning_rate"] * (X[idx] * (prob - y[idx]) + CONFIG["l2"] * w)
            wc, residual, steps = converge(X, y, w)
            converged.append(wc)
            diagnostics.append({"seed": seed, "schedule": schedule,
                                "gradient_norm": residual, "newton_steps": steps})
            for stage, weights in [("one_pass", w), ("common_convergence", wc)]:
                for p, (Xt, yt) in tests.items():
                    accuracy = float(np.mean((mv(Xt, weights) >= 0) == yt))
                    rows.append({"seed": seed, "schedule": schedule, "stage": stage,
                                 "test_shortcut_agreement": p, "accuracy": accuracy,
                                 "w_intercept": float(weights[0]), "w_core": float(weights[1]),
                                 "w_shortcut": float(weights[2]),
                                 "pooled_train_objective": objective(X, y, weights)})
        diagnostic = max(float(np.linalg.norm(w - converged[0])) for w in converged)
        diagnostics.append({"seed": seed, "schedule": "between_converged_solutions",
                            "gradient_norm": diagnostic, "newton_steps": 0})
        for p, (Xt, yt) in tests.items():
            accuracy = float(np.mean((Xt[:, 1] >= 0) == yt))
            rows.append({"seed": seed, "schedule": "known_core_oracle", "stage": "oracle",
                         "test_shortcut_agreement": p, "accuracy": accuracy,
                         "w_intercept": 0.0, "w_core": 1.0, "w_shortcut": 0.0,
                         "pooled_train_objective": objective(X, y, np.array([0., 1., 0.]))})
    return rows, diagnostics


def exact_selection(include_pretest=False):
    """Enumerate independent latent U and flip noises, rather than sample."""
    joint = np.zeros((2, 2, 2)) if include_pretest else np.zeros((2, 2))
    for u in [0, 1]:
        for t in [0, 1]:
            for y in [0, 1]:
                prob = 0.5 * (0.8 if t == u else 0.2) * (0.9 if y == u else 0.1)
                if include_pretest:
                    for x in [0, 1]:
                        joint[x, t, y] += prob * (0.8 if x == u else 0.2)
                else:
                    joint[t, y] += prob
    return joint


def contrast(t, y):
    return float(y[t == 1].mean() - y[t == 0].mean())


def stratified_contrast(x, t, y):
    return float(sum(np.mean(x == v) * contrast(t[x == v], y[x == v]) for v in [0, 1]))


def causal(seeds):
    selection = exact_selection()
    direct = np.array([[0.5 * 0.74, 0.5 * 0.26], [0.5 * 0.26, 0.5 * 0.74]])
    exact_difference = float(np.max(np.abs(selection - direct)))
    assert exact_difference < 1e-14
    jx = exact_selection(include_pretest=True)
    exact_adjusted = sum(jx[x].sum() * (jx[x, 1, 1] / jx[x, 1].sum() -
                                       jx[x, 0, 1] / jx[x, 0].sum()) for x in [0, 1])
    rows = []
    for seed in seeds:
        for n in CONFIG["causal_sample_sizes"]:
            rng = np.random.default_rng(seed + n * 10)
            u = rng.integers(0, 2, n)
            t_obs = np.bitwise_xor(u, (rng.random(n) > 0.8).astype(int))
            y_selection = np.bitwise_xor(u, (rng.random(n) > 0.9).astype(int))
            x = np.bitwise_xor(u, (rng.random(n) > 0.8).astype(int))
            t_rand = rng.integers(0, 2, n)
            # Same exogenous outcome for selection world under intervention: T never enters Y.
            y_direct_obs = (rng.random(n) < (0.26 + 0.48 * t_rand)).astype(int)
            t_intervene = rng.integers(0, 2, n)
            y_direct_intervene = (rng.random(n) < (0.26 + 0.48 * t_intervene)).astype(int)
            for world, design, estimate, target in [
                ("selection_no_effect", "observational", contrast(t_obs, y_selection), 0.48),
                ("selection_no_effect", "pretest_stratified", stratified_contrast(x, t_obs, y_selection), float(exact_adjusted)),
                ("selection_no_effect", "randomized", contrast(t_rand, y_selection), 0.0),
                ("direct_effect", "observational", contrast(t_rand, y_direct_obs), 0.48),
                ("direct_effect", "randomized", contrast(t_intervene, y_direct_intervene), 0.48),
            ]:
                rows.append({"seed": seed, "n": n, "world": world, "design": design,
                             "estimate": estimate, "population_contrast": target})
    exact = {"selection_joint_T_Y": selection.tolist(), "direct_joint_T_Y": direct.tolist(),
             "max_observational_joint_difference": exact_difference,
             "observational_difference_both_worlds": 0.48,
             "selection_world_true_ATE": 0.0, "direct_world_true_ATE": 0.48,
             "selection_world_pretest_adjusted_association": float(exact_adjusted),
             "note": "pretest X equivalence is not claimed; this is residual-confounding illustration"}
    return rows, exact


def describe(values):
    v = np.asarray(values)
    return {"mean": float(v.mean()), "sd_across_seeds": float(v.std(ddof=1)) if len(v)>1 else None,
            "min": float(v.min()), "max": float(v.max()), "n_seeds": len(v)}


def summarize(curr, diagnostics, cause, exact):
    curriculum_summary = []
    keys = sorted(set((r["schedule"], r["stage"], r["test_shortcut_agreement"]) for r in curr))
    for schedule, stage, p in keys:
        values = [r["accuracy"] for r in curr if (r["schedule"], r["stage"], r["test_shortcut_agreement"]) == (schedule, stage, p)]
        curriculum_summary.append({"schedule": schedule, "stage": stage, "test_shortcut_agreement": p, **describe(values)})
    cause_summary = []
    for world, design, n in sorted(set((r["world"], r["design"], r["n"]) for r in cause)):
        selected = [r for r in cause if (r["world"], r["design"], r["n"]) == (world, design, n)]
        cause_summary.append({"world": world, "design": design, "n": n,
                              "population_contrast": selected[0]["population_contrast"],
                              **describe([r["estimate"] for r in selected])})
    return {"curriculum_accuracy": curriculum_summary, "causal_contrasts": cause_summary,
            "exact_causal_check": exact,
            "max_converged_gradient_norm": max(r["gradient_norm"] for r in diagnostics if r["schedule"] != "between_converged_solutions"),
            "max_distance_between_converged_solutions": max(r["gradient_norm"] for r in diagnostics if r["schedule"] == "between_converged_solutions"),
            "analytic_core_oracle_accuracy": 0.5 * (1 + math.erf(1 / math.sqrt(2)))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minimal", action="store_true")
    args = ap.parse_args()
    seeds = [0] if args.minimal else CONFIG["seeds"]
    start = time.perf_counter()
    out = HERE / ("minimal" if args.minimal else "results")
    out.mkdir(exist_ok=True)
    curr, diagnostics = curriculum(seeds)
    cause, exact = causal(seeds)
    save_csv(out / "curriculum.csv", curr)
    save_csv(out / "optimizer_checks.csv", diagnostics)
    save_csv(out / "causal.csv", cause)
    summary = summarize(curr, diagnostics, cause, exact)
    summary["runtime_seconds"] = time.perf_counter() - start
    summary["python"] = platform.python_version()
    summary["numpy"] = np.__version__
    (out / "config.json").write_text(json.dumps({**CONFIG, "executed_seeds": seeds}, indent=2) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"output": str(out), "runtime_seconds": summary["runtime_seconds"],
                      "max_gradient_norm": summary["max_converged_gradient_norm"],
                      "max_converged_parameter_distance": summary["max_distance_between_converged_solutions"],
                      "exact_joint_error": exact["max_observational_joint_difference"]}, indent=2))


if __name__ == "__main__":
    main()
