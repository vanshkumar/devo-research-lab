"""Independent forward evaluation of a concrete forced-only threshold law."""
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import resource
from time import perf_counter
from typing import Optional

import numpy as np

import validation as v

SEED = 2026110603


@dataclass(frozen=True)
class Threshold:
    payoff_sign: int
    direction: int
    cutoff: Optional[float]
    tie_probability: float

    def p_i(self, opt, pay):
        base, move, ratio = candidates(opt, pay, self.payoff_sign, self.direction)
        if self.cutoff is None:
            return base.astype(float)
        flip = (ratio < self.cutoff) + self.tie_probability * (ratio == self.cutoff)
        return base + (1 - 2 * base) * np.where(move > 0, flip, 0)


def candidates(opt, pay, payoff_sign, direction):
    row = np.arange(len(opt))
    base = (payoff_sign * pay).argmax(axis=1)
    delta_opt = opt[row, 1 - base] - opt[row, base]
    delta_pay = pay[row, 1 - base] - pay[row, base]
    move = direction * delta_opt
    ratio = np.full(len(base), np.inf)
    np.divide(-payoff_sign * delta_pay, move, where=move > 0, out=ratio)
    return base, move, ratio


def fit_threshold(opt, pay, target, payoff_sign):
    base = (payoff_sign * pay).argmax(axis=1)
    base_opt = opt[np.arange(len(opt)), base].mean()
    direction = 1 if target > base_opt else -1
    need = len(opt) * abs(target - base_opt)
    if need <= 1e-12:
        return Threshold(payoff_sign, direction, None, 0.)
    _, move, ratio = candidates(opt, pay, payoff_sign, direction)
    order = np.argsort(ratio[move > 0])
    values, gains = ratio[move > 0][order], move[move > 0][order]
    cumulative = np.cumsum(gains)
    assert len(cumulative) and need <= cumulative[-1] + 1e-9
    cutoff = values[min(np.searchsorted(cumulative, need), len(values) - 1)]
    prior_move = gains[values < cutoff].sum()
    tie_move = gains[values == cutoff].sum()
    tie = np.clip((need - prior_move) / tie_move, 0., 1.)
    return Threshold(payoff_sign, direction, float(cutoff), float(tie))


def marginal(values, p):
    return values[:, :1] + p * (values[:, 1:] - values[:, :1])


def calibrate(opt, pay, observed_opt, observed_pay, per_step):
    target_opt = observed_opt.mean(axis=0)
    target_opt = np.clip(target_opt, opt.min(axis=1).mean(), opt.max(axis=1).mean())
    lo, hi = [[fit_threshold(opt, pay, goal, sign) for goal in target_opt]
              for sign in (-1, 1)]
    p_lo, p_hi = [np.column_stack([rule.p_i(opt, pay) for rule in side]) for side in (lo, hi)]
    assert np.allclose(marginal(opt, p_lo).mean(axis=0), target_opt, atol=2e-11, rtol=0)
    assert np.allclose(marginal(opt, p_hi).mean(axis=0), target_opt, atol=2e-11, rtol=0)
    pay_lo, pay_hi = [marginal(pay, side).mean(axis=0) for side in (p_lo, p_hi)]
    step_interval = np.column_stack([pay_lo, pay_hi])
    assert np.all(pay_hi >= pay_lo - 1e-10)
    if per_step:
        payoff_target = observed_pay.mean(axis=0)
    else:
        pay_lo, pay_hi = pay_lo.mean(), pay_hi.mean()
        payoff_target = observed_pay.mean()
    gap = pay_hi - pay_lo
    weight = np.divide(payoff_target - pay_lo, gap, out=np.zeros_like(gap), where=gap > 1e-12)
    weight = np.clip(weight, 0, 1)
    return (lo, hi, weight), {
        "observed_curve_target": observed_opt.mean(axis=0),
        "attainable_curve_target": target_opt,
        "observed_payoff_target": payoff_target,
        "attainable_payoff_target": pay_lo + weight * gap,
        "payoff_intervals_exact_optimum": step_interval,
        "lower_thresholds": [asdict(x) for x in lo],
        "upper_thresholds": [asdict(x) for x in hi],
        "upper_policy_weight": weight,
    }


def predict(calibrated, opt, pay):
    lo, hi, weight = calibrated
    p_lo = np.column_stack([rule.p_i(opt, pay) for rule in lo])
    p_hi = np.column_stack([rule.p_i(opt, pay) for rule in hi])
    return p_lo, p_hi, np.broadcast_to(weight, p_lo.shape).copy()


def evaluate_exact(q, pmf, z, p):
    """Recompute attained outcomes directly in the latent/reward space."""
    opt, reward = np.zeros_like(p), np.zeros_like(p)
    innovation = np.zeros(len(p))
    for arm, probability in enumerate((1 - p, p)):
        optimal_indicator = (v.BETTER_I == arm)
        distribution = pmf[:, :, arm]
        opt += np.einsum("gi,gk,ri,i->gk", q, probability, distribution,
                         optimal_indicator, optimize=False)
        reward += np.einsum("gi,gk,ri,r->gk", q, probability, distribution,
                            v.original.REWARDS, optimize=False)
        # First action is independent of the later branch conditional on origin.
        innovation += np.einsum("gi,g,ri,ri->g", q,
                                probability[:, 0] * (probability[:, 1] - .5),
                                distribution, z[:, :, arm], optimize=False)
    assert np.max(np.abs(innovation)) < 1e-13
    return {"optimum": opt, "payoff": reward, "innovation": innovation}


def rollouts(q, first, plan, factual, factual_switch, truncated):
    rng = np.random.default_rng(SEED)
    n, draws = len(q), v.DRAWS
    out = {}
    var = {}
    for begin in range(0, n, v.BATCH):
        ix = slice(begin, begin + v.BATCH)
        lo, hi, weight = [np.repeat(x[ix], draws, axis=0) for x in plan]
        conditional_latent = np.repeat(q[ix], draws, axis=0)
        p0 = np.repeat(first[ix], draws)
        size = len(p0)
        row = np.arange(size)
        banks = []
        for _ in range(2):
            branch = rng.random((size, 1)) < weight
            prob_i = np.column_stack([p0, np.where(branch, hi, lo)])
            # Commit to all six choices before drawing any actual feedback.
            actions = (rng.random(prob_i.shape) < prob_i).astype(int)
            latent, potential = v.environment(conditional_latent, rng.random(size),
                                              rng.random((size, 6, 2)), truncated)
            reward = potential[row[:, None], np.arange(6)[None, :], actions]
            target = v.original.target(actions, reward)
            switch = (actions[:, 1:] != actions[:, :-1]).astype(float)
            stats = {"optimum": (actions == v.BETTER_I[latent, None]).astype(float),
                     "payoff": reward, "switch": switch, "target": target}
            banks.append({k: a.reshape(size // draws, draws, -1) for k, a in stats.items()})
        b1, b2 = banks
        x, y = b1.pop("target"), b2.pop("target")
        outcomes = factual[ix, None, :]
        dist = v.original.distance
        reductions = {k: .5 * (b1[k] + b2[k]) for k in b1}
        reductions["energy"] = .5 * (dist(x, outcomes) + dist(y, outcomes) - dist(x, y))
        reductions["choice_energy"] = .5 * (
            dist(x[..., :-1], outcomes[..., :-1]) + dist(y[..., :-1], outcomes[..., :-1])
            - dist(x[..., :-1], y[..., :-1]))
        reductions["switch_brier"] = ((b1["switch"] - factual_switch[ix, None, :])
                                      * (b2["switch"] - factual_switch[ix, None, :]))
        for k, values in reductions.items():
            if k not in out:
                out[k] = np.zeros((n, *values.shape[2:]))
                var[k] = np.zeros(values.shape[2:])
            out[k][ix] = values.mean(axis=1)
            var[k] += values.var(axis=1, ddof=1).sum(axis=0) / (draws * n**2)
    return out, {k: np.sqrt(value) for k, value in var.items()}


def tape_audit(ids, pairs, fa, fy, a0, y0, z_observed, pmf, latent, repeat):
    signature = np.column_stack([pairs, fa, fy, a0])
    _, rep, group, counts = np.unique(signature, axis=0, return_index=True,
                                       return_inverse=True, return_counts=True)

    def pairs_in(keys):
        _, n = np.unique(keys, axis=0, return_counts=True)
        return int(np.sum(n * (n - 1) // 2))

    _, person_first, person_counts = np.unique(np.column_stack([group, ids]), axis=0,
                                               return_index=True, return_counts=True)
    within_by_group = np.bincount(group[person_first],
                                  weights=person_counts * (person_counts - 1) / 2,
                                  minlength=len(counts))
    cross = counts * (counts - 1) / 2 - within_by_group
    same_y_cross = (pairs_in(np.column_stack([group, y0]))
                    - pairs_in(np.column_stack([group, ids, y0])))
    probability_equal = (pmf[:, latent[rep], a0[rep]] ** 2).sum(axis=0)
    observed_moment = z_observed * (repeat - .5)
    repeated = counts[group] > 1
    return {
        "distinct_exact_signatures": len(counts), "games_with_repeated_signature": int(repeated.sum()),
        "within_person_exact_signature_pairs": int(within_by_group.sum()),
        "cross_person_exact_signature_pairs": int(cross.sum()),
        "cross_person_equal_first_rewards": same_y_cross,
        "independent_expected_equal_first_rewards": float(np.sum(cross * probability_equal)),
        "moment_repeated": float(observed_moment[repeated].mean()) if repeated.any() else None,
        "moment_singleton": float(observed_moment[~repeated].mean()) if (~repeated).any() else None,
        "moment_equal_signature_weights": float(np.mean(
            np.bincount(group, weights=observed_moment) / counts)),
    }


def run_law(boundary, inputs, fits):
    ids, _, game, all_a, all_y, pairs, _ = inputs
    people = np.unique(ids)
    fa, fy, a, y = all_a[:, :4], all_y[:, :4], all_a[:, 4:], all_y[:, 4:]
    h = np.full(len(ids), 6)
    ordinal = (game - 160.5) / 160
    truncated = boundary == "truncate"
    table = v.original.LOG_TRUNCATE if truncated else v.original.LOG_CLIP
    pmf, mean, z = v.moments(table)
    q = v.original.forced_law(fa, fy, table)
    opt, pay = v.ceiling(q, mean)
    latent = np.argmax((pairs[:, None] == v.PAIR).all(axis=2), axis=1)
    actual_opt = (a == v.BETTER_I[latent, None]).astype(float)
    actual_switch = (a[:, 1:] != a[:, :-1]).astype(float)
    factual = v.original.target(a, y)
    full_fit, full_rec = calibrate(opt, pay, actual_opt[:, 1:], y[:, 1:], True)
    reference_path = Path(__file__).resolve().parent / f"{boundary.upper()}_RESULT.json"
    primary = json.loads(reference_path.read_text())
    ref = primary["oracle_scope"]["conditional_exact_target_feasibility"]["reward_intervals"]
    assert np.allclose(full_rec["payoff_intervals_exact_optimum"], ref, atol=1e-10, rtol=0)

    first = np.zeros(len(ids))
    projected = [np.zeros((len(ids), 5)) for _ in range(3)]
    fold_reports = []
    for saved in fits:
        test = np.isin(ids, saved["held_source_ids"])
        train = ~test
        assert np.array_equal(np.unique(ids[train]), saved["train_ids"])
        fitted, rec = calibrate(opt[train], pay[train], actual_opt[train, 1:], y[train, 1:], False)
        for column, p in zip(projected, predict(fitted, opt[test], pay[test])):
            column[test] = p
        actor = v.original.Policy(**{k: np.array(data) for k, data in saved["first"].items()})
        features = v.history(fa[test], fy[test]).features(h[test], 0, ordinal[test], False)
        first[test] = v.donor_probabilities(actor, features).mean(axis=1)
        fold_reports.append({"training_ids": saved["train_ids"], "recipient_ids": saved["held_source_ids"],
                             "training_calibration": rec})

    def report(plan):
        p_lo, p_hi, weight = plan
        probability = np.column_stack([first, p_lo + weight * (p_hi - p_lo)])
        exact = evaluate_exact(q, pmf, z, probability)
        assert np.allclose(exact["optimum"], marginal(opt, probability), atol=1e-11, rtol=0)
        assert np.allclose(exact["payoff"], marginal(pay, probability), atol=1e-11, rtol=0)
        literal, mcse = rollouts(q, first, plan, factual, actual_switch, truncated)
        fixed_i = v.BETTER_I[latent].astype(float)
        fixed_label_opt = np.column_stack([1 - fixed_i, fixed_i])
        fixed_label_pay = mean[latent]

        def person(x):
            return np.stack([x[ids == i].mean(axis=0) for i in people])

        opt_diff = person(exact["optimum"] - actual_opt)
        pay_diff = person(exact["payoff"] - y)
        fixed_opt_diff = person(marginal(fixed_label_opt, probability) - actual_opt)
        fixed_pay_diff = person(marginal(fixed_label_pay, probability) - y)
        per_person = {
            "exact_optimum": person(exact["optimum"]), "exact_payoff": person(exact["payoff"]),
            "exact_innovation": person(exact["innovation"]),
            "optimal_bias": opt_diff, "payoff_bias": pay_diff,
            "optimal_bias_fixed_evaluator_label": fixed_opt_diff,
            "payoff_bias_fixed_evaluator_label": fixed_pay_diff,
        }
        per_person.update({f"mc_{k}": person(x) for k, x in literal.items()})
        output = {
            "point_and_working_screens": v.screens(opt_diff, pay_diff),
            "pooled_later_payoff_bias": v.interval(pay_diff[:, 1:].mean(axis=1)),
            "pooled_later_optimum_bias": v.interval(opt_diff[:, 1:].mean(axis=1)),
            "fixed_evaluator_label_screens": v.screens(fixed_opt_diff, fixed_pay_diff),
            "source_ids": people, "per_person": per_person,
            "summary": {k: v.interval(x) for k, x in per_person.items()},
            "conditional_mc_se": mcse,
        }
        return output, exact

    full, exact_full = report(predict(full_fit, opt, pay))
    assert np.allclose(exact_full["optimum"][:, 1:].mean(axis=0),
                       full_rec["attainable_curve_target"], atol=1e-11, rtol=0)
    assert np.allclose(exact_full["payoff"][:, 1:].mean(axis=0),
                       full_rec["attainable_payoff_target"], atol=1e-11, rtol=0)
    crossfit, exact_cv = report(projected)
    for fold in fold_reports:
        ix = np.isin(ids, fold["recipient_ids"])
        delta_opt = (exact_cv["optimum"][ix] - actual_opt[ix]).mean(axis=0)
        delta_pay = (exact_cv["payoff"][ix] - y[ix]).mean(axis=0)
        fold["later_max_abs_optimum_bias"] = float(np.max(np.abs(delta_opt[1:])))
        fold["pooled_later_payoff_bias"] = float(delta_pay[1:].mean())
        fold["curve_and_payoff_point_pass"] = bool(
            fold["later_max_abs_optimum_bias"] <= v.CURVE_MARGIN
            and abs(fold["pooled_later_payoff_bias"]) <= v.PAYOFF_MARGIN)
    actual_z = z[y[:, 0] - 1, latent, a[:, 0]]
    return {"boundary": boundary, "full_source_analytic_recipe": full_rec, "finite_witness": full,
            "crossfit": crossfit, "fold_reports": fold_reports,
            "first_reward_tape_audit": tape_audit(ids, pairs, fa, fy, a[:, 0], y[:, 0],
                                                  actual_z, pmf, latent, 1 - actual_switch[:, 0])}


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (100, 110))
    start = perf_counter()
    inputs = v.source()
    fits = json.loads(v.FIT.read_text())["fitted"]
    results = []
    for label in ("clip", "truncate"):
        print(f"Calibrating and evaluating {label} law", flush=True)
        results.append(run_law(label, inputs, fits))
        print(f"Completed {label} witness", flush=True)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    cost = {"cpu_seconds": usage.ru_utime + usage.ru_stime,
            "max_rss_bytes_macos": usage.ru_maxrss,
            "elapsed_seconds": perf_counter() - start,
            "full_source_scans_booked_bytes": 4 * v.BODY.stat().st_size,
            "fit_file_read_bytes": v.FIT.stat().st_size,
            "primary_result_file_bytes": sum((v.HERE / f"{label.upper()}_RESULT.json").stat().st_size
                                             for label in ("clip", "truncate"))}
    out = {"seed": SEED, "banks": 2, "draws_per_bank": v.DRAWS, "results": results, "cost": cost}
    (v.HERE / "WITNESS_RESULT.json").write_text(
        json.dumps(out, indent=2, allow_nan=False, default=v.json_numeric) + "\n")
    print(cost, flush=True)


if __name__ == "__main__":
    main()
