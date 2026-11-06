"""Independent synthetic identification audit; no empirical outcome inputs."""
from pathlib import Path
import csv
import hashlib
import json
import platform
import sys
import numpy as np
from scipy.stats import t as student_t, nct

HERE = Path(__file__).resolve().parent
SEED = 21873
rng = np.random.default_rng(SEED)


def enc(x, kind):
    if kind == "linear":
        return np.asarray(x)
    if kind == "log":
        return np.log(x)
    return np.sqrt(x)


def dec(x, kind):
    if kind == "linear":
        return np.asarray(x)
    if kind == "log":
        return np.exp(x)
    return np.asarray(x) ** 2


def equivalence():
    worst = 0.0
    rows = []
    for case in range(1000):
        kind = ("linear", "log", "sqrt")[case % 3]
        # Distinct routines store a sensory code or a motor equilibrium.
        r = float(enc(1.0, kind))
        motor_equilibrium = 1.0
        shared = float(enc(1.0, kind))
        lesion = ("none", "before", "after_first")[(case // 3) % 3]
        count = int(rng.integers(1, 8))
        for j in range(count):
            duration = float(rng.uniform(0.5, 3.0))
            tutor_clock = float(rng.uniform(0.5, 1.2))
            a = float(rng.uniform(0.1, 0.9))
            if lesion == "before" or (lesion == "after_first" and j > 0):
                a = 0.0
            signal = float(enc(tutor_clock * duration, kind))
            r = (1.0 - a) * r + a * signal
            motor_equilibrium = float(dec(
                (1.0 - a) * enc(motor_equilibrium, kind)
                + a * enc(tutor_clock * duration, kind), kind))
            shared += a * (signal - shared)
        production_clock = float(rng.uniform(0.5, 1.2))
        eta = float(rng.uniform(0.02, 0.4))
        w0 = float(enc(rng.uniform(0.5, 3.0), kind))
        innovation = rng.uniform(-0.001, 0.001, 60)
        w_ref = w0
        motor = float(dec(w0, kind))
        max_case = 0.0
        for k, eps in enumerate(innovation, start=1):
            # Reference: error correction in the sensory code.
            w_ref += eta * (r - w_ref) + eps
            y_ref = float(dec(w_ref, kind)) / production_clock
            # Motor: autonomous relaxation toward installed motor equilibrium.
            motor = float(dec((1.0 - eta) * enc(motor, kind)
                              + eta * enc(motor_equilibrium, kind) + eps, kind))
            y_motor = motor / production_clock
            # Shared: closed-form solution, independent of above recurrences.
            residual = sum((1.0 - eta) ** (k - 1 - j) * float(innovation[j])
                           for j in range(k))
            w_shared = shared + (1.0 - eta) ** k * (w0 - shared) + residual
            y_shared = float(dec(w_shared, kind)) / production_clock
            err = max(abs(y_ref - y_motor), abs(y_ref - y_shared))
            max_case = max(max_case, err)
        worst = max(worst, max_case)
        rows.append(dict(case=case, encoding=kind, lesion=lesion,
                         source_events=count, max_path_difference=max_case))
    # Coding at the tutoring clock followed by unaltered production has ratio cT/cP.
    clocks = [(ct, cp, ct / cp) for ct in (.6, .8, 1.0, 1.2)
              for cp in (.6, .8, 1.0, 1.2)]
    with (HERE / "equivalence_cases.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    assert worst < 1e-10
    return {"cases": len(rows), "practice_steps_each": 60,
            "max_absolute_path_difference": worst,
            "clock_ratio_grid": clocks,
            "qualification": "Restricted duration models with common write-gate mapping; not proof of biological equality."}


def vector_field():
    # Stable nonlinear motor drift and an evaluator potential giving that drift.
    errs = []
    for center in (-.5, 0., .5):
        for quartic in (0., .1, 1., 5.):
            for x in np.linspace(-2., 2., 401):
                dx = x - center
                motor_drift = -dx - quartic * dx ** 3
                reward = lambda u: -.5 * (u-center)**2 - .25 * quartic*(u-center)**4
                h = 1e-5
                reward_derivative = (reward(x+h) - reward(x-h))/(2*h)
                errs.append(abs(reward_derivative - motor_drift))
    assert max(errs) < 1e-7
    return {"checked_points": len(errs), "max_finite_difference_error": max(errs),
            "analytic_statement": "For any continuous scalar f(x,z), R(x,z)=integral f(u,z)du has dR/dx=f(x,z)."}


def information():
    w = .65
    end = np.array([w, 1.0-w, 1.0])
    # Exposure, lesion and clock conditions scale a common installed code.
    factors = np.array([0., .1, .4, .8, 1., 1.2, 2.])
    endpoint_design = factors[:, None] * end[None, :]
    probe_design = np.concatenate((endpoint_design, [[1., 0., 1.], [0., 1., 1.]]))
    selective_design = np.concatenate((probe_design, [[0., 0., 1.]]))
    null = np.array([-1., -1., 1.])
    profiles = []
    for shared in np.linspace(0., .6, 61):
        params = np.array([.8 - shared, .6 - shared, shared])
        observed = np.einsum("ij,j->i", probe_design, params)
        profiles.append(observed)
    spread = float(np.max(np.ptp(np.array(profiles), axis=0)))
    assert spread < 1e-14
    return {
        "columns": ["private_reference", "private_motor", "shared_trace"],
        "endpoint_rank": int(np.linalg.matrix_rank(endpoint_design)),
        "endpoint_plus_target_and_motor_probe_rank": int(np.linalg.matrix_rank(probe_design)),
        "with_genuinely_selective_shared_trace_probe_rank": int(np.linalg.matrix_rank(selective_design)),
        "endpoint_singular_values": np.linalg.svd(endpoint_design, compute_uv=False).tolist(),
        "joint_probe_singular_values": np.linalg.svd(probe_design, compute_uv=False).tolist(),
        "gauge_direction": null.tolist(),
        "joint_probe_null_residual": float(np.max(np.abs(np.einsum("ij,j->i", probe_design, null)))),
        "61_equivalent_allocations_max_readout_spread": spread,
        "shared_fraction_feasible_interval_in_example": [0., .6],
        "qualification": "Local additive decomposition; nonlinear copy construction extends same conceptual ambiguity. Selective row is a conditional assumption, not an available validated manipulation."}


def recovery():
    out = []
    kappa = .1
    shift = .2
    simulations = 1000
    for n in (6, 12, 24):
        for repeats in (10, 50):
            for noise in (.03, .1):
                for alpha in (0., .25, .5, .75, 1.):
                    # Means of independent repeated trials have exactly this normal law.
                    # Four cells = active minus/plus, inhibited minus/plus.
                    intercept = rng.normal(0., .08, (simulations, n, 1))
                    inhibitor_effect = rng.normal(0., .05, (simulations, n, 1))
                    errors = rng.normal(0., noise/np.sqrt(repeats), (simulations, n, 4))
                    tutor = np.where(np.arange(n) % 2 == 0, -.5, .5)[None, :, None]
                    active = kappa * tutor
                    inactive = kappa * (1-alpha) * tutor
                    means = np.concatenate((active + kappa*alpha*shift,
                                            active - kappa*alpha*shift,
                                            inactive, inactive), axis=2)
                    nuisance = intercept + np.concatenate((np.zeros_like(inhibitor_effect),
                                                           np.zeros_like(inhibitor_effect),
                                                           inhibitor_effect, inhibitor_effect), axis=2)
                    cell = means + nuisance + errors
                    per_bird = (cell[:, :, 0]-cell[:, :, 1]-cell[:, :, 2]+cell[:, :, 3])/(2*shift*kappa)
                    estimated = per_bird.mean(axis=1)
                    se = per_bird.std(axis=1, ddof=1)/np.sqrt(n)
                    threshold = float(student_t.ppf(.975, n-1))
                    lower, upper = estimated-threshold*se, estimated+threshold*se
                    nearest = np.clip(np.round(estimated/.25)*.25, 0., 1.)
                    exact_se = noise/(np.sqrt(n*repeats)*shift*kappa)
                    exact_detection = 1.0-float(nct.cdf(threshold, n-1, alpha/exact_se))
                    row = dict(n_birds=n, trials_per_cell=repeats, trial_noise_sd=noise,
                               true_evaluator_fraction=alpha,
                               mean_estimate=float(estimated.mean()),
                               bias=float(estimated.mean()-alpha),
                               rmse=float(np.sqrt(np.mean((estimated-alpha)**2))),
                               exact_sampling_rmse=float(exact_se),
                               ci95_coverage=float(np.mean((lower <= alpha) & (upper >= alpha))),
                               ci95_positive_rate=float(np.mean(lower > 0.)),
                               exact_positive_rate=exact_detection,
                               nearest_grid_recovery=float(np.mean(nearest == alpha)))
                    out.append(row)
    with (HERE / "functional_gain_recovery.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    nominal = [r for r in out if r["n_birds"] == 12 and r["trials_per_cell"] == 50
               and r["trial_noise_sd"] == .03]
    # Exact expected sabotage: alpha=0 with an auditory-dependent inhibitory side effect.
    off_target_gain = .05
    false_fraction = off_target_gain/kappa
    # Incomplete inhibition leaves alpha*(1-efficacy) in inhibited trials.
    attenuation = [{"true_fraction": a, "inhibition_efficacy": e,
                    "expected_estimate_if_full_inhibition_assumed": a*e}
                   for a in (0., .25, .5, .75, 1.) for e in (0., .5, 1.)]
    return {"generated_datasets": len(out)*simulations, "nominal_case_rows": nominal,
            "min_coverage": min(r["ci95_coverage"] for r in out),
            "max_coverage": max(r["ci95_coverage"] for r in out),
            "max_simulated_vs_exact_detection_difference": max(abs(r["ci95_positive_rate"]-r["exact_positive_rate"]) for r in out),
            "incomplete_inhibition": attenuation,
            "off_target_control": {"true_evaluator_fraction": 0.,
                                   "inhibitor_auditory_shift_gain": off_target_gain,
                                   "falsely_inferred_fraction": false_fraction},
            "qualification": "Synthetic noise/power calculation conditional on independently calibrated kappa and selective inhibition. Not a biological power calculation."}


def target_tuning():
    n, repeats, score_sd, probe = 12, 50, .3, .4
    simulations = 1000
    estimates = []
    for target in (-.5, .5):
        bird_q = target+rng.normal(0., .1, (simulations, n))
        plus = -(probe-bird_q)**2+rng.normal(0., score_sd/np.sqrt(repeats), (simulations,n))
        minus = -(-probe-bird_q)**2+rng.normal(0., score_sd/np.sqrt(repeats), (simulations,n))
        estimates.append((plus-minus)/(4*probe))
    contrast = estimates[1].mean(axis=1)-estimates[0].mean(axis=1)
    # Motor-stored-readout q=m and reference-stored q=r generate exactly the same scores.
    probe_values = np.linspace(-1., 1., 101)
    reference_q = .6
    motor_m = .6
    sensory_trace_score = -(probe_values-reference_q)**2
    motor_readout_score = -(probe_values-motor_m)**2
    return {"n_birds_per_target": n, "trials_per_probe": repeats,
            "true_target_difference": 1., "mean_estimated_target_difference": float(contrast.mean()),
            "target_difference_rmse": float(np.sqrt(np.mean((contrast-1.)**2))),
            "reference_vs_motor_readout_max_score_difference": float(np.max(np.abs(sensory_trace_score-motor_readout_score))),
            "qualification": "Target tuning plus mediation can establish functional evaluation; its memory source remains ambiguous. Calibrated quadratic curvature and no state-dependent response-gain confound assumed."}


def main():
    result = {"seed": SEED, "python": sys.version, "platform": platform.platform(),
              "numpy_version": np.__version__, "empirical_data_used": False,
              "equivalence": equivalence(), "scalar_vector_field": vector_field(),
              "information_rank": information(), "functional_gain_recovery": recovery(),
              "matched_target_tuning": target_tuning()}
    result["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (HERE / "audit_results.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"max_path_difference": result["equivalence"]["max_absolute_path_difference"],
                      "identification_ranks": [result["information_rank"]["endpoint_rank"],
                                               result["information_rank"]["endpoint_plus_target_and_motor_probe_rank"],
                                               result["information_rank"]["with_genuinely_selective_shared_trace_probe_rank"]],
                      "synthetic_datasets": result["functional_gain_recovery"]["generated_datasets"],
                      "nominal_recovery": result["functional_gain_recovery"]["nominal_case_rows"]}, indent=2))


if __name__ == "__main__":
    main()
