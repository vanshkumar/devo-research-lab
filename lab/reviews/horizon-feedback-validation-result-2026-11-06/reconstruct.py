"""Source-only reconstruction. No imports from the author's analysis."""

from collections import Counter, defaultdict
import csv
from dataclasses import asdict, dataclass
from hashlib import sha1, sha256
import io
from itertools import combinations
import json
from pathlib import Path
import resource
from time import perf_counter
from typing import Optional

import numpy as np
from scipy.optimize import linprog
from scipy.special import expit, ndtr, ndtri
from scipy.stats import t


HERE = Path(__file__).resolve().parent
TASKS = HERE.parents[1] / "tasks"
SOURCE = TASKS / "horizon-feedback-forecast-2026-11-06"
AUTHOR = TASKS / "horizon-feedback-validation-2026-11-06"
POINTS = np.arange(1, 101)
SIGMA = 8.0
CURVE_BAND = 0.04
PAYOFF_BAND = 0.65
SEED = 2026110606
DRAWS = 128
BATCH = 40


def pinned_source():
    body = (SOURCE / "source_train.csv").read_bytes()
    assert len(body) == 2_052_611
    digest = sha256(body).hexdigest()
    assert digest == "3005b71bab3a91fb6ee74b8895f3508d957fecbd61f9d9d9d17a620a7f82d6a7"
    git_digest = sha1(f"blob {len(body)}\0".encode() + body).hexdigest()
    assert git_digest == "4914e7cb971cef4fe32aa27096201114239f6d81"
    content = body.decode("ascii")
    schedule = defaultdict(set)
    identity = {}
    rows = csv.DictReader(io.StringIO(content))
    assert rows.fieldnames == [
        "participant_id", "block", "game", "gameLength", "uc", "m1", "m2",
        "trial", "choice", "reward", "horizon", "type",
    ]
    for row in rows:
        key = tuple(int(row[name]) for name in ("participant_id", "block", "game"))
        h, length, trial = [int(row[name]) for name in ("horizon", "gameLength", "trial")]
        assert h in (1, 6) and length == h + 4
        assert identity.setdefault(key, (h, row["uc"])) == (h, row["uc"])
        assert row["type"] == ("forced" if trial <= 4 else "free")
        assert trial not in schedule[key]
        schedule[key].add(trial)
    assert len(schedule) == 8000
    assert all(trials == set(range(1, 5 + identity[k][0])) for k, trials in schedule.items())
    by_person_horizon = Counter((k[0], h) for k, (h, _) in identity.items())
    by_person_block = Counter(k[:2] for k in identity)
    assert len(by_person_horizon) == 50 and set(by_person_horizon.values()) == {160}
    assert len(by_person_block) == 100 and set(by_person_block.values()) == {80}
    assert sum(map(len, schedule.values())) == 60_000
    keys = sorted(k for k, (h, _) in identity.items() if h == 6)
    index = {k: i for i, k in enumerate(keys)}
    arms = np.full((4000, 10), -1, dtype=int)
    reward = np.full_like(arms, -1)
    means = np.full((4000, 2), np.nan)
    for row in csv.DictReader(io.StringIO(content)):
        if int(row["horizon"]) == 1:
            continue
        key = tuple(int(row[name]) for name in ("participant_id", "block", "game"))
        i = index[key]
        j = int(row["trial"]) - 1
        arms[i, j] = {"H": 0, "I": 1}[row["choice"]]
        value = float(row["reward"])
        assert value.is_integer() and 1 <= value <= 100
        reward[i, j] = int(value)
        pair = [float(row["m1"]), float(row["m2"])]
        if np.isnan(means[i]).any():
            means[i] = pair
        assert (means[i] == pair).all()
    assert np.all(arms >= 0) and np.all(reward >= 1)
    assert set(arms[:, :4].sum(axis=1)) == {1, 2, 3}
    return np.array(keys), arms, reward, means, {
        "bytes": len(body), "sha256": digest, "git_blob_sha1": git_digest,
        "roster_people": 25, "schedule_rows": 60_000, "typed_h6_rows": 40_000,
        "factual_label_role": "evaluation and calibration targets from eligible training people",
    }


def design():
    mass = Counter()
    for base in (40, 60):
        for magnitude in (4, 8, 12, 20, 30):
            for other in (base - magnitude, base + magnitude):
                mass[(base, other)] += 1
                mass[(other, base)] += 1
    pair = np.array(list(mass))
    assert pair.shape == (38, 2) and sum(mass.values()) == 40
    return pair, np.array(list(mass.values())) / 40


def reward_law(pair, boundary):
    edge = (np.arange(0.5, 101) - pair[..., None]) / SIGMA
    lower, upper = edge[..., :-1], edge[..., 1:]
    # Use the reflected tail where direct CDF subtraction would lose precision.
    prob = np.where(lower > 0, ndtr(-lower) - ndtr(-upper), ndtr(upper) - ndtr(lower))
    if boundary == "clip":
        prob[..., 0] += ndtr(edge[..., 0])
        prob[..., -1] += ndtr(-edge[..., -1])
    else:
        prob /= prob.sum(axis=-1, keepdims=True)
    mean = np.sum(prob * POINTS, axis=-1)
    variance = np.sum(prob * (POINTS - mean[..., None]) ** 2, axis=-1)
    z = (POINTS - mean[..., None]) / np.sqrt(variance[..., None])
    center_error = np.max(np.abs(np.sum(prob * z, axis=-1)))
    scale_error = np.max(np.abs(np.sum(prob * z**2, axis=-1) - 1))
    assert np.max(np.abs(prob.sum(axis=-1) - 1)) < 2e-14
    assert center_error < 2e-14 and scale_error < 2e-14
    return prob, mean, z, {"max_mean_error": center_error, "max_unit_second_moment_error": scale_error}


def posterior_from_forced(arms, reward, prior, pmf):
    weights = np.broadcast_to(prior, (len(arms), len(prior))).copy()
    for j in range(4):
        weights *= pmf[:, arms[:, j], reward[:, j] - 1].T
    assert np.all(weights.sum(axis=1) > 0)
    return weights / weights.sum(axis=1, keepdims=True)


def marginal(values, right_probability):
    return values[:, [0]] + (values[:, [1]] - values[:, [0]]) * right_probability


def weighted(weight, values):
    return np.einsum("g,g...->...", weight, values, optimize=False)


def serialized_cutoff_inputs(arms, rewards, boundary):
    """Recreate the arithmetic that produced the saved binary64 cutoffs."""
    gaps = np.array([4, 8, 12, 20, 30])
    pair = np.array([(mu, mu + gap)[::side]
                     for mu in (40, 60) for gap in np.r_[-gaps, gaps] for side in (1, -1)], dtype=float)
    up = ndtr((POINTS[:, None, None] + .5 - pair) / SIGMA)
    lo = ndtr((POINTS[:, None, None] - .5 - pair) / SIGMA)
    pmf = up - lo
    if boundary == "clip":
        pmf[0] = up[0]
        pmf[-1] = 1 - lo[-1]
    else:
        pmf /= up[-1] - lo[0]
    log_table = np.log(np.maximum(pmf, 1e-300))
    log_prob = log_table[rewards - 1, :, arms].sum(axis=1)
    q = np.exp(log_prob - log_prob.max(axis=1, keepdims=True))
    q /= q.sum(axis=1, keepdims=True)
    p_i = q[:, pair[:, 1] > pair[:, 0]].sum(axis=1)
    mean = (POINTS[:, None, None] * np.exp(log_table)).sum(axis=0)
    return np.column_stack([1 - p_i, p_i]), np.einsum("gi,ij->gj", q, mean, optimize=False)


def finite_lp(opt, pay, optimum_targets, tolerance):
    """LP in action-I probabilities, one bound per origin and curve point."""
    n = len(opt)
    opt0 = opt[:, 0].mean()
    gain = (opt[:, 1] - opt[:, 0]) / n
    pay0 = pay[:, 0].mean()
    benefit = (pay[:, 1] - pay[:, 0]) / n
    answer = []
    for target in optimum_targets:
        row = []
        for sign in (1, -1):
            if tolerance == 0:
                constraints = dict(A_eq=[gain], b_eq=[target - opt0])
            else:
                constraints = dict(A_ub=[gain, -gain],
                                   b_ub=[target + tolerance - opt0, opt0 - target + tolerance])
            result = linprog(sign * benefit, bounds=(0.0, 1.0), method="highs", **constraints,
                             options={"dual_feasibility_tolerance": 1e-9,
                                      "primal_feasibility_tolerance": 1e-9})
            assert result.success, result.message
            row.append(pay0 + sign * result.fun)
        answer.append(row)
    return np.array(answer)


@dataclass(frozen=True)
class Rule:
    """Threshold in the slope measured from the less-optimal arm."""

    payoff_sign: int
    cutoff: Optional[float]
    probability_at_cutoff: float

    def predict(self, opt, pay):
        good = (opt[:, 1] > opt[:, 0]).astype(int)
        j = np.arange(len(opt))
        gain = np.abs(opt[:, 1] - opt[:, 0])
        cost = pay[j, good] - pay[j, 1 - good]
        slope = np.divide(-self.payoff_sign * cost, gain,
                          out=np.zeros(len(opt)), where=gain > 0)
        if self.cutoff is None:
            upgrade = np.zeros(len(opt))
        else:
            tied = np.isclose(slope, self.cutoff, atol=2e-12, rtol=2e-12)
            upgrade = np.where(tied, self.probability_at_cutoff, slope < self.cutoff)
        probability_i = np.where(good == 1, upgrade, 1 - upgrade)
        tie_on_optimum = np.argmax(self.payoff_sign * pay, axis=1)
        return np.where(gain > 0, probability_i, tie_on_optimum)


def fit_rule(opt, pay, weight, target, sign):
    good = (opt[:, 1] > opt[:, 0]).astype(int)
    j = np.arange(len(opt))
    gain = np.abs(opt[:, 1] - opt[:, 0])
    cost = pay[j, good] - pay[j, 1 - good]
    take = gain > 0
    moved = weight[take] * gain[take]
    slope = -sign * cost[take] / gain[take]
    needed = target - weighted(weight, opt.min(axis=1))
    if needed <= 1e-14:
        return Rule(sign, None, 0.0)
    order = np.argsort(slope)
    before = np.cumsum(moved[order])
    assert needed <= before[-1] + 2e-12
    cutoff = slope[order[min(np.searchsorted(before, needed), len(order) - 1)]]
    tied = np.isclose(slope, cutoff, atol=2e-12, rtol=2e-12)
    remaining = needed - moved[(slope < cutoff) & ~tied].sum()
    return Rule(sign, float(cutoff), float(np.clip(remaining / moved[tied].sum(), 0, 1)))


def calibrate(opt, pay, weight, opt_target, reward_target, per_step):
    reachable = np.clip(opt_target, weighted(weight, opt.min(axis=1)), weighted(weight, opt.max(axis=1)))
    lo = [fit_rule(opt, pay, weight, x, -1) for x in reachable]
    hi = [fit_rule(opt, pay, weight, x, 1) for x in reachable]
    low, high = [np.column_stack([rule.predict(opt, pay) for rule in branch])
                 for branch in (lo, hi)]
    for branch in (low, high):
        assert np.max(np.abs(weighted(weight, marginal(opt, branch)) - reachable)) < 2e-11
    lower = weighted(weight, marginal(pay, low))
    upper = weighted(weight, marginal(pay, high))
    assert np.all(upper >= lower - 2e-11)
    a, b = (lower, upper) if per_step else (lower.mean(), upper.mean())
    fraction = np.divide(reward_target - a, b - a, out=np.zeros_like(b - a), where=b > a)
    fraction = np.clip(fraction, 0, 1)
    recipe = (lo, hi, fraction)
    details = {
        "lower": [asdict(r) for r in lo], "upper": [asdict(r) for r in hi],
        "high_branch_probability": fraction, "per_step_payoff_interval": np.column_stack([lower, upper]),
        "calibration_optimum_target": opt_target, "attained_training_optimum": reachable,
        "calibration_payoff_target": reward_target, "attained_training_payoff": a + fraction * (b - a),
    }
    return recipe, details


def project(recipe, opt, pay):
    lo, hi, fraction = recipe
    return [np.column_stack([rule.predict(opt, pay) for rule in branch]) for branch in (lo, hi)] + [
        np.broadcast_to(fraction, (len(opt), 5)).copy(),
    ]


def saved_threshold(spec, opt, pay, nearby_ties):
    """Evaluate the published form, independently of our fit and score orientation."""
    sign = spec["payoff_sign"]
    base = np.argmax(sign * pay, axis=1)
    if spec["cutoff"] is None:
        return base.astype(float)
    row = np.arange(len(opt))
    gain = spec["direction"] * (opt[row, 1 - base] - opt[row, base])
    loss = sign * (pay[row, base] - pay[row, 1 - base])
    ratio = np.divide(loss, gain, out=np.full(len(base), np.inf), where=gain > 0)
    tied = (np.isclose(ratio, spec["cutoff"], atol=2e-12, rtol=2e-12)
            if nearby_ties else ratio == spec["cutoff"])
    flip = np.where(tied, spec["tie_probability"], ratio < spec["cutoff"])
    return np.where(base == 1, 1 - flip, flip)


def project_saved(spec, opt, pay, nearby_ties=False):
    keys = ("lower_thresholds", "upper_thresholds")
    lo, hi = [np.column_stack([saved_threshold(rule, opt, pay, nearby_ties) for rule in spec[k]]) for k in keys]
    return lo + np.asarray(spec["upper_policy_weight"]) * (hi - lo)


def person_means(values, people):
    return np.array([values[people == i].mean(axis=0) for i in np.unique(people)])


def paired(values, people):
    x = person_means(values, people)
    n = len(x)
    avg = x.mean(axis=0)
    sd = x.std(axis=0, ddof=1)
    return {"mean": avg, "sd": sd, "half90": t.ppf(.95, n - 1) * sd / np.sqrt(n),
            "half95": t.ppf(.975, n - 1) * sd / np.sqrt(n)}


def screen(opt_diff, payoff_diff, people):
    reductions = {
        "later_five_curve": (opt_diff[:, 1:], CURVE_BAND),
        "full_six_curve": (opt_diff, CURVE_BAND),
        "pooled_later_optimum": (opt_diff[:, 1:].mean(axis=1), CURVE_BAND),
        "pooled_later_payoff": (payoff_diff[:, 1:].mean(axis=1), PAYOFF_BAND),
        "each_later_payoff": (payoff_diff[:, 1:], PAYOFF_BAND),
    }
    result = {}
    for label, (x, margin) in reductions.items():
        interval = paired(x, people)
        bound = np.abs(interval["mean"]) + interval["half90"]
        result[label] = dict(interval, margin=margin, max_abs_mean=np.max(np.abs(interval["mean"])),
                             max_tost_extent=np.max(bound), point_pass=bool(np.all(np.abs(interval["mean"]) <= margin)),
                             working_tost=bool(np.all(bound <= margin)))
    for label in ("later_five_curve", "full_six_curve", "pooled_later_optimum"):
        result[label]["joint_point_pass"] = result[label]["point_pass"] and result["pooled_later_payoff"]["point_pass"]
        result[label]["joint_working_tost"] = result[label]["working_tost"] and result["pooled_later_payoff"]["working_tost"]
    return result


def forced_signatures(arms, rewards):
    ordered = [tuple(zip(a.tolist(), y.tolist())) for a, y in zip(arms, rewards)]
    multiset = [tuple(sorted(pairs)) for pairs in ordered]
    return ordered, multiset


def witness_audit(opt, pay, observed_opt, observed_pay, people, arms, rewards, fits, saved, oracle, boundary):
    target_opt = observed_opt[:, 1:].mean(axis=0)
    target_pay = observed_pay[:, 1:].mean(axis=0)
    lp = finite_lp(opt, pay, target_opt, 0)
    band_lp = finite_lp(opt, pay, target_opt, CURVE_BAND)
    error = np.max(np.abs(lp - oracle["conditional_exact_target_feasibility"]["reward_intervals"]))
    band_error = np.max(np.abs(band_lp - oracle["conditional_joint_feasibility"]["reward_intervals"]))
    assert max(error, band_error) < 2e-6
    assert np.all((lp[:, 0] <= target_pay) & (target_pay <= lp[:, 1]))
    weights = np.full(len(opt), 1 / len(opt))
    arm_min = opt.min(axis=1)
    assert np.isfinite(arm_min).all() and np.isfinite(weights).all()
    finite_contraction_error = abs((weights @ arm_min) - weighted(weights, arm_min))
    assert finite_contraction_error < 2e-12
    recipe, info = calibrate(opt, pay, weights, target_opt, target_pay, True)
    assert np.max(np.abs(info["per_step_payoff_interval"] - lp)) < 2e-6
    lo, hi, w = project(recipe, opt, pay)
    full_p = lo + w * (hi - lo)
    cutoff_opt, cutoff_pay = serialized_cutoff_inputs(arms, rewards, boundary)
    assert np.max(np.abs(opt - cutoff_opt)) < 2e-12
    assert np.max(np.abs(pay - cutoff_pay)) < 2e-11
    saved_p = project_saved(saved["full_source_analytic_recipe"], cutoff_opt, cutoff_pay)
    for p in (full_p, saved_p):
        assert np.max(np.abs(marginal(opt, p).mean(axis=0) - target_opt)) < 2e-10
        assert np.max(np.abs(marginal(pay, p).mean(axis=0) - target_pay)) < 2e-10
    result = {
        "ceiling_optimum": opt.max(axis=1).mean(), "ceiling_payoff": pay.max(axis=1).mean(),
        "observed_optimum": target_opt, "observed_payoff": target_pay,
        "lp_exact_intervals": lp, "lp_band_intervals": band_lp,
        "lp_exact_pooled_interval": lp.mean(axis=0), "lp_band_pooled_interval": band_lp.mean(axis=0),
        "author_lp_max_error": error, "author_band_lp_max_error": band_error,
        "full_source_calibration": info,
        "full_source_saved_vs_independent_max_probability_difference": np.max(np.abs(saved_p - full_p)),
        "full_source_achieved_optimum": marginal(opt, full_p).mean(axis=0),
        "full_source_achieved_payoff": marginal(pay, full_p).mean(axis=0),
        "finite_contraction_error": finite_contraction_error,
        "cutoff_replay_optimum_input_error": np.max(np.abs(opt - cutoff_opt)),
        "cutoff_replay_payoff_input_error": np.max(np.abs(pay - cutoff_pay)),
    }
    ordered, multiset = forced_signatures(arms, rewards)
    plans = {key: [np.full((len(opt), 5), np.nan) for _ in range(3)]
             for key in ("original", "forced_multiset_disjoint")}
    saved_held_p = np.full_like(lo, np.nan)
    fold_details = []
    for fit, saved_fold in zip(fits, saved["fold_reports"]):
        assert fit["train_ids"] == saved_fold["training_ids"]
        assert fit["held_source_ids"] == saved_fold["recipient_ids"]
        held = np.isin(people, fit["held_source_ids"])
        train = ~held
        held_order = {x for x, use in zip(ordered, held) if use}
        held_multiset = {x for x, use in zip(multiset, held) if use}
        train_multiset = {x for x, use in zip(multiset, train) if use}
        exact_overlap = np.array([x in held_order for x in ordered])
        multiset_overlap = np.array([x in held_multiset for x in multiset])
        assert np.all(~exact_overlap | multiset_overlap)
        assert np.array_equal(np.unique(people[train]), fit["train_ids"])
        saved_spec = saved_fold["training_calibration"]
        from_saved = project_saved(saved_spec, cutoff_opt[train], cutoff_pay[train])
        assert np.max(np.abs(marginal(opt[train], from_saved).mean(axis=0)
                             - observed_opt[train, 1:].mean(axis=0))) < 2e-10
        assert abs(marginal(pay[train], from_saved).mean() - observed_pay[train, 1:].mean()) < 2e-10
        saved_held_p[held] = project_saved(saved_spec, cutoff_opt[held], cutoff_pay[held])
        near_ties = project_saved(saved_spec, opt[train], pay[train], nearby_ties=True)
        tie_replay_error = np.max(np.abs(marginal(opt[train], near_ties).mean(axis=0)
                                         - observed_opt[train, 1:].mean(axis=0)))
        detail = {"training_people": fit["train_ids"], "recipient_people": fit["held_source_ids"],
                  "ordered_overlap_rows_removed": int(np.sum(train & exact_overlap)),
                  "multiset_overlap_rows_removed": int(np.sum(train & multiset_overlap)),
                  "training_curve_error_when_reusing_cutoffs_with_near_ties": tie_replay_error,
                  "recipient_rows_with_any_training_multiset_match": sum(
                      x in train_multiset for x, use in zip(multiset, held) if use),
                  }
        # Rows with that same sufficient history anywhere in the recipient fold are excluded.
        for name, eligible in (("original", train), ("forced_multiset_disjoint", train & ~multiset_overlap)):
            roster = people[eligible]
            counts = Counter(roster)
            assert counts, "No training person with any eligible forced history"
            weights = np.array([1.0 / (len(counts) * counts[i]) for i in roster])
            assert np.isclose(weights.sum(), 1)
            if name.endswith("disjoint"):
                assert held_multiset.isdisjoint(x for x, use in zip(multiset, eligible) if use)
                print(f"Disjoint fold {fit['held_source_ids']}: {len(counts)}/20 calibration people, "
                      f"{len(roster)}/3200 calibration games", flush=True)
            calibrated, calibration = calibrate(
                opt[eligible], pay[eligible], weights, weighted(weights, observed_opt[eligible, 1:]),
                weighted(weights, observed_pay[eligible, 1:]).mean(), False,
            )
            for out, v in zip(plans[name], project(calibrated, opt[held], pay[held])):
                out[held] = v
            detail[name] = dict(calibration, retained_rows_by_person={str(k): v for k, v in counts.items()},
                                retained_rows=int(np.sum(eligible)),
                                empty_training_people=sorted(set(fit["train_ids"]) - set(counts)))
        fold_details.append(detail)
    assert np.isfinite(saved_held_p).all()
    exact_saved_opt = person_means(marginal(opt, saved_held_p), people)
    exact_saved_pay = person_means(marginal(pay, saved_held_p), people)
    reference = saved["crossfit"]["per_person"]
    opt_error = np.max(np.abs(exact_saved_opt - np.asarray(reference["exact_optimum"])[:, 1:]))
    pay_error = np.max(np.abs(exact_saved_pay - np.asarray(reference["exact_payoff"])[:, 1:]))
    assert max(opt_error, pay_error) < 2e-9
    result.update(folds=fold_details, saved_held_optimum_max_error=opt_error,
                  saved_held_payoff_max_error=pay_error)
    return plans, result


def forced_features(arms, rewards, ordinal, step):
    """Rebuild the documented ordinary features from a supplied history."""
    n = len(arms)
    rows = np.arange(n)
    count = np.zeros((n, 2))
    total = np.zeros_like(count)
    squares = np.zeros_like(count)
    ema = np.zeros_like(count)
    last = np.zeros_like(count)
    for j in range(arms.shape[1]):
        at = (rows, arms[:, j])
        count_before = count[at]
        y = rewards[:, j]
        if j == arms.shape[1] - 1:
            prior_average = total[at] / np.maximum(count_before, 1)
            surprise = np.where(count_before > 0, (y - prior_average) / SIGMA, 0)
        ema[at] = np.where(count_before > 0, .6 * ema[at] + .4 * y, y)
        last[at] = y
        total[at] += y
        squares[at] += y**2
        count[at] += 1

    def contrast(x):
        return x[:, 1] - x[:, 0]

    average = total / count
    value = contrast(average) / SIGMA
    center = (average.mean(axis=1) - 50) / 20
    count_delta = -contrast(count) / 3
    info = np.sign(count_delta)
    u = count ** -.5
    u_delta, u_total = contrast(u), u.sum(axis=1) - 1.4
    recent = contrast(ema - average) / SIGMA
    latest = contrast(last - average) / SIGMA
    variability = np.sqrt(np.maximum(0, squares / count - average**2)) / SIGMA
    stay = (2. * arms[:, -1] - 1.) * (1. - .8 * (step == 0))
    nonlinear = np.tanh(value)
    progress = step / 5
    return np.column_stack((
        value, info, stay, stay * surprise, count_delta, u_delta, recent, latest,
        contrast(variability), (variability.mean(axis=1) - .7) * nonlinear,
        u_total * value, nonlinear, center, center * value, center * count_delta,
        ordinal, ordinal * value, ordinal * info, ordinal * stay,
        np.ones(n), value, info, stay, np.full(n, progress), progress * value,
        progress * info, progress * stay, progress * count_delta, progress * u_delta,
        progress * recent, progress**2 * value, progress**2 * info, progress**2 * stay,
        (count_delta == 0) * value, nonlinear * np.abs(count_delta), nonlinear * u_total,
    ))


def choice_probability(policy, features, donor=None):
    x = (features - policy["center"]) / policy["scale"]
    intercept = policy["common"][-1]
    logit = np.einsum("ij,j->i", x, policy["common"][:-1]) + intercept
    if donor is None:
        offset = np.einsum("ij,kj->ik", x[:, :4], policy["offsets"][:, :4])
        return expit(logit[:, None] + offset + policy["offsets"][:, 4])
    offset = policy["offsets"][donor]
    return expit(logit + (x[:, :4] * offset[:, :4]).sum(axis=1) + offset[:, 4])


def exact_first_handoff(fa, fy, ordinal, q, later, pmf, z, p0):
    """Average over reward, latent type, arm and one shared donor."""
    n, n_donors = p0.shape
    outcomes = np.tile(POINTS, n)
    past_arms = np.repeat(fa, 100, axis=0)
    past_rewards = np.repeat(fy, 100, axis=0)
    all_rewards = np.column_stack((past_rewards, outcomes))
    prior_ordinal = np.repeat(ordinal, 100)
    result = np.zeros(n)
    repeat = np.zeros(n)
    for arm, weight in enumerate((1 - p0, p0)):
        history = np.column_stack((past_arms, np.full(n * 100, arm)))
        features = forced_features(history, all_rewards, prior_ordinal, 1)
        second = choice_probability(later, features).reshape(n, 100, n_donors)
        repeat_given_reward = second if arm else 1 - second
        mass = np.einsum("gd,grd->gr", weight, repeat_given_reward) / n_donors
        density = np.einsum("gl,lr->gr", q, pmf[:, arm])
        centered_density = np.einsum("gl,lr->gr", q, pmf[:, arm] * z[:, arm])
        result += ((mass - 0.5 * weight.mean(axis=1, keepdims=True)) * centered_density).sum(axis=1)
        repeat += (mass * density).sum(axis=1)
    return result, repeat


def tape_audit(keys, arms, rewards, pair, label, pmf, moment, actual_z):
    forced, _ = forced_signatures(arms[:, :4], rewards[:, :4])
    groups = defaultdict(list)
    for i, signature in enumerate(forced):
        groups[(label[i], signature, arms[i, 4])].append(i)
    exact_pairs = equal_pairs = within_person = 0
    expected = 0.
    for (latent, _, arm), members in groups.items():
        coincidence = float(np.sum(pmf[latent, arm]**2))
        for i, j in combinations(members, 2):
            if keys[i, 0] == keys[j, 0]:
                within_person += 1
            else:
                exact_pairs += 1
                equal_pairs += int(rewards[i, 4] == rewards[j, 4])
                expected += coincidence
    singleton = [v[0] for v in groups.values() if len(v) == 1]
    repeated = [i for v in groups.values() if len(v) > 1 for i in v]
    ordinal_groups = defaultdict(list)
    mean_probability = {}
    for i, (_, _, game) in enumerate(keys):
        for j, arm in enumerate(arms[i, :4]):
            mu = pair[label[i], arm]
            ordinal_groups[(game, j, arm, mu)].append(rewards[i, j])
            mean_probability[mu] = float(np.sum(pmf[label[i], arm]**2))
    ordinal_pairs = sum(len(v) * (len(v) - 1) // 2 for v in ordinal_groups.values())
    ordinal_equal = sum(c * (c - 1) // 2 for v in ordinal_groups.values() for c in Counter(v).values())
    ordinal_expected = sum(len(v) * (len(v) - 1) / 2 * mean_probability[k[-1]]
                           for k, v in ordinal_groups.items())
    return {
        "exact_signatures": len(groups), "games_in_repeated_signatures": len(repeated),
        "cross_person_exact_signature_pairs": exact_pairs, "within_person_pairs": within_person,
        "cross_person_equal_first_rewards": equal_pairs, "independent_expected_equal_first_rewards": expected,
        "equal_signature_moment": np.mean([moment[v].mean() for v in groups.values()]),
        "singleton_moment": moment[singleton].mean(), "repeated_moment": moment[repeated].mean(),
        "within_repeated_signature_max_innovation_range": max(np.ptp(actual_z[v]) for v in groups.values() if len(v) > 1),
        "same_ordinal_forced_pairs": ordinal_pairs, "same_ordinal_equal_forced_rewards": ordinal_equal,
        "same_ordinal_independent_expected_equal_forced_rewards": ordinal_expected,
    }


def pick_latent(q, rng):
    return np.minimum((rng.random((len(q), 1)) > np.cumsum(q, axis=1)).sum(axis=1), q.shape[1] - 1)


def earned_reward(mu, u, boundary):
    if boundary == "truncate":
        lower = ndtr((.5 - mu) / SIGMA)
        upper = ndtr((100.5 - mu) / SIGMA)
        u = lower + (upper - lower) * u
    return np.clip(np.rint(mu + SIGMA * ndtri(u)), 1, 100).astype(int)


def rollout_bank(rng, fa, fy, ordinal, q, pair, mean, z, opt, pay, p0, later,
                 threshold_plan, boundary):
    size = len(fa)
    row = np.arange(size)
    donor = rng.integers(p0.shape[1], size=size)
    choice = rng.random((size, 6))
    shock = rng.random((size, 6))
    latent = pick_latent(q, rng)
    mu = pair[latent]
    a, y = np.column_stack([fa, np.zeros((size, 6), dtype=int)]), np.column_stack(
        [fy, np.zeros((size, 6), dtype=int)])
    for step in range(6):
        j = step + 4
        if step == 0:
            p_i = p0[row, donor]
        else:
            x = forced_features(a[:, :j], y[:, :j], ordinal, step)
            p_i = choice_probability(later, x, donor)
        a[:, j] = choice[:, step] < p_i
        y[:, j] = earned_reward(mu[row, a[:, j]], shock[:, step], boundary)
    action, obtained = a[:, 4:], y[:, 4:]
    repeat = action[:, 0] == action[:, 1]
    arm_idx = action[:, 0]
    shadow_latent = pick_latent(q, rng)
    shadow_rewards = earned_reward(pair[shadow_latent[:, None], action],
                                   rng.random(action.shape), boundary)
    # The exact same action array is evaluated in the independent environment.
    opt_adaptive = action == (mu[:, [1]] > mu[:, [0]])
    pay_adaptive = mean[latent[:, None], action]
    opt_shadow = opt[row[:, None], action]
    pay_shadow = pay[row[:, None], action]
    lo, hi, w = threshold_plan
    use_high = rng.random((size, 1)) < w
    prob = np.column_stack([p0.mean(axis=1), np.where(use_high, hi, lo)])
    blind_a = (rng.random(prob.shape) < prob).astype(int)
    # Every choice is committed before sampling the independent earned rewards.
    blind_latent = pick_latent(q, rng)
    blind_y = earned_reward(pair[blind_latent[:, None], blind_a], rng.random(prob.shape), boundary)
    return {
        "adaptive_optimum": opt_adaptive.astype(float), "adaptive_payoff": pay_adaptive,
        "adaptive_literal_payoff": obtained, "shadow_optimum": opt_shadow, "shadow_payoff": pay_shadow,
        "shadow_literal_payoff": shadow_rewards, "optimum_gain": opt_adaptive - opt_shadow,
        "payoff_gain": pay_adaptive - pay_shadow,
        "adaptive_innovation": z[latent, arm_idx, obtained[:, 0] - 1] * (repeat - .5),
        "shadow_innovation": z[shadow_latent, arm_idx, shadow_rewards[:, 0] - 1] * (repeat - .5),
        "blind_optimum": (blind_a == (pair[blind_latent, 1] > pair[blind_latent, 0])[:, None]).astype(float),
        "blind_payoff": blind_y,
        "blind_innovation": z[blind_latent, blind_a[:, 0], blind_y[:, 0] - 1]
                            * ((blind_a[:, 0] == blind_a[:, 1]) - .5),
        "action": action, "reward_adaptive": obtained, "reward_shadow": shadow_rewards,
        "blind_action": blind_a, "reward_blind": blind_y,
    }


def outcome_vector(action, reward):
    return np.concatenate([action[:, 1:], (reward[:, 1:].sum(axis=1, keepdims=True) - 250)
                           / (SIGMA * np.sqrt(5))], axis=1)


def energy(bank1, bank2, outcome):
    return 0.5 * (np.linalg.norm(bank1 - outcome, axis=1) + np.linalg.norm(bank2 - outcome, axis=1)
                  - np.linalg.norm(bank1 - bank2, axis=1))


def score_banks(b1, b2, observed):
    for bank in (b1, b2):
        action, blind_action = bank.pop("action"), bank.pop("blind_action")
        bank["switch_common"] = (action[:, 1:] != action[:, :-1]).astype(float)
        bank["switch_blind"] = (blind_action[:, 1:] != blind_action[:, :-1]).astype(float)
        bank["joint_adaptive"] = outcome_vector(action, bank.pop("reward_adaptive"))
        bank["joint_shadow"] = outcome_vector(action, bank.pop("reward_shadow"))
        bank["joint_blind"] = outcome_vector(blind_action, bank.pop("reward_blind"))
    scores = {}
    for model in ("adaptive", "shadow", "blind"):
        key = f"joint_{model}"
        first, second = b1.pop(key), b2.pop(key)
        scores[f"{model}_energy"] = energy(first, second, observed)
        scores[f"{model}_choice_energy"] = energy(first[:, :-1], second[:, :-1], observed[:, :-1])
    assert np.array_equal(scores["adaptive_choice_energy"], scores["shadow_choice_energy"])
    scores.update({k: (b1[k] + b2[k]) / 2 for k in b1})
    return scores


def evaluate_models(keys, arms, rewards, q, pair, pmf, mean, z, opt, pay, plan, fits, boundary):
    rng = np.random.default_rng(SEED)
    observed = outcome_vector(arms[:, 4:], rewards[:, 4:])
    people = keys[:, 0]
    ordinals = (keys[:, 2] - 160.5) / 160
    fa, fy = arms[:, :4], rewards[:, :4]
    mean_first = np.full(len(q), np.nan)
    exact_innovation, exact_repeat = np.full_like(mean_first, np.nan), np.full_like(mean_first, np.nan)
    forecasts, squared_se = {}, {}
    for fit in fits:
        first, later = [{k: np.asarray(x) for k, x in fit[part].items()} for part in ("first", "history")]
        assert first["offsets"].shape == later["offsets"].shape == (20, 5)
        fold = np.flatnonzero(np.isin(people, fit["held_source_ids"]))
        for start in range(0, len(fold), BATCH):
            ix = fold[start:start + BATCH]
            p0 = choice_probability(first, forced_features(fa[ix], fy[ix], ordinals[ix], 0))
            mean_first[ix] = p0.mean(axis=1)
            exact_innovation[ix], exact_repeat[ix] = exact_first_handoff(
                fa[ix], fy[ix], ordinals[ix], q[ix], later, pmf, z, p0,
            )
            replicate = np.repeat(ix, DRAWS)
            batch = (fa[replicate], fy[replicate], ordinals[replicate], q[replicate], pair, mean, z,
                     opt[replicate], pay[replicate], np.repeat(p0, DRAWS, axis=0), later,
                     [x[replicate] for x in plan], boundary)
            bank1, bank2 = rollout_bank(rng, *batch), rollout_bank(rng, *batch)
            for name, scores in score_banks(bank1, bank2, observed[replicate]).items():
                shaped = scores.reshape(len(ix), DRAWS, *scores.shape[1:])
                forecast = forecasts.setdefault(name, np.full((len(q), *scores.shape[1:]), np.nan))
                forecast[ix] = shaped.mean(axis=1)
                squared_se[name] = squared_se.get(name, 0) + shaped.var(axis=1, ddof=1).sum(axis=0)
    assert all(np.isfinite(x).all() for x in forecasts.values())
    assert np.isfinite(exact_innovation).all()
    mc_se = {k: np.sqrt(v / DRAWS) / len(q) for k, v in squared_se.items()}
    # First choice is exactly the same law in both roles; use its analytic integral.
    for k in ("adaptive", "shadow"):
        forecasts[f"{k}_optimum"][:, 0] = marginal(opt, mean_first[:, None])[:, 0]
        forecasts[f"{k}_payoff"][:, 0] = marginal(pay, mean_first[:, None])[:, 0]
    return mean_first, exact_innovation, exact_repeat, forecasts, mc_se


def witness_report(plan, first, opt, pay, fixed_opt, fixed_pay, truth_opt, truth_pay, people):
    lo, hi, w = plan
    p = np.column_stack([first, lo + w * (hi - lo)])
    generated_opt, generated_pay = marginal(opt, p), marginal(pay, p)
    factual_opt, factual_pay = marginal(fixed_opt, p), marginal(fixed_pay, p)
    return {
        "conditional": screen(generated_opt - truth_opt, generated_pay - truth_pay, people),
        "fixed_label": screen(factual_opt - truth_opt, factual_pay - truth_pay, people),
        "conditional_optimum": generated_opt.mean(axis=0), "conditional_payoff": generated_pay.mean(axis=0),
        "fixed_label_optimum": factual_opt.mean(axis=0), "fixed_label_payoff": factual_pay.mean(axis=0),
        "zero_innovation_given_model": 0.0,
    }


def run(boundary, keys, arms, rewards, actual_pair, fits, saved, primary):
    people = keys[:, 0]
    pair, prior = design()
    pmf, mean, z, centering = reward_law(pair, boundary)
    q = posterior_from_forced(arms[:, :4], rewards[:, :4], prior, pmf)
    is_pair = (actual_pair[:, None] == pair[None, :]).all(axis=-1)
    assert (is_pair.sum(axis=1) == 1).all()
    label = is_pair.argmax(axis=1)
    better = (pair[:, 1] > pair[:, 0]).astype(int)
    p_better_i = q[:, better == 1].sum(axis=1)
    opt = np.column_stack((1 - p_better_i, p_better_i))
    pay = np.einsum("gl,la->ga", q, mean)
    fixed_opt = np.column_stack((1 - better[label], better[label]))
    fixed_pay = mean[label]
    truth_opt, truth_pay = (arms[:, 4:] == better[label, None]).astype(float), rewards[:, 4:]
    plans, witness = witness_audit(opt, pay, truth_opt, truth_pay, people, arms[:, :4], rewards[:, :4],
                                  fits, saved, primary["oracle_scope"], boundary)
    print(f"{boundary}: independent LP and saved/reconstructed witness checks passed", flush=True)
    first, innovation, repeat, forecasts, mc_se = evaluate_models(
        keys, arms, rewards, q, pair, pmf, mean, z, opt, pay, plans["original"], fits, boundary)
    truth_innovation = z[label, arms[:, 4], rewards[:, 4] - 1]
    truth_repeat = arms[:, 4] == arms[:, 5]
    moment = truth_innovation * (truth_repeat - .5)
    innovations = {
        "law_standardization": centering,
        "observed": paired(moment, people), "adaptive_exact": paired(innovation, people),
        "paired_adaptive_minus_human": paired(innovation - moment, people),
        "exact_adaptive_repeat": paired(repeat, people),
        "shadow_exact": 0.0, "witness_exact": 0.0,
        "conditional_null_variance": 0.25, "working_normal_half95_if_960_independent_null": 1.96 * 0.5 / np.sqrt(960),
        "projected_six_empirical_person_half95": t.ppf(.975, 5) * paired(moment, people)["sd"] / np.sqrt(6),
    }
    for ref, value in (("adaptive_innovation", innovation), ("observed_innovation", moment)):
        error = np.max(np.abs(person_means(value, people) - np.asarray(primary["per_person"][ref])))
        assert error < 2e-11
        innovations[f"{ref}_author_max_error"] = error
    tape = tape_audit(keys, arms, rewards, pair, label, pmf, moment, truth_innovation)
    assert tape["cross_person_exact_signature_pairs"] == tape["cross_person_equal_first_rewards"] == 388
    result = {
        "boundary": boundary, "frontier_and_calibration": witness, "innovation": innovations, "tapes": tape,
        "observed_optimum": paired(truth_opt, people), "observed_payoff": paired(truth_pay, people),
        "observed_switch": paired(arms[:, 5:] != arms[:, 4:-1], people),
        "path_match": {"equal_path_in_every_paired_draw": True,
                       "per_person_replay": {k: person_means(v, people) for k, v in forecasts.items()},
                       "replay": {k: paired(v, people) for k, v in forecasts.items()},
                       "conditional_mc_se": mc_se},
    }
    for actor in ("adaptive", "shadow"):
        result["path_match"][actor] = screen(
            forecasts[f"{actor}_optimum"] - truth_opt, forecasts[f"{actor}_payoff"] - truth_pay, people)
    result["witness"] = {}
    for name, plan in plans.items():
        report_args = (first, opt, pay, fixed_opt, fixed_pay, truth_opt, truth_pay, people)
        result["witness"][name] = witness_report(plan, *report_args)
        result["witness"][name]["folds"] = []
        for fit in fits:
            held = np.isin(people, fit["held_source_ids"])
            result["witness"][name]["folds"].append(
                witness_report([p[held] for p in plan], *(v[held] for v in report_args)))
    print(f"{boundary}: generated replay, independent first-innovation and tape checks finished", flush=True)
    return result


def numeric(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value))


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (190, 200))
    started = perf_counter()
    loaded_bytes = {}

    def read_json(path):
        raw = path.read_bytes()
        loaded_bytes[path.name] = len(raw)
        return json.loads(raw), sha256(raw).hexdigest()

    keys, arms, rewards, actual_pair, provenance = pinned_source()
    fit, fit_hash = read_json(SOURCE / "DEVELOPMENT_CLIP.json")
    assert fit_hash == "bca10c6e15d5e861318f509376d8fe70cb078a48c9e62de9ef5efd0ef0094445"
    fit = fit["fitted"]
    people = np.unique(keys[:, 0])
    assert len(fit) == 5
    assert np.array_equal(people, np.sort(np.concatenate([f["held_source_ids"] for f in fit])))
    for fold in fit:
        assert np.array_equal(fold["train_ids"], np.setdiff1d(people, fold["held_source_ids"]))
    print("Pinned 25-person source, schedule and frozen fit partitions verified", flush=True)
    witness, witness_hash = read_json(AUTHOR / "WITNESS_RESULT.json")
    sources = {"ordinary_fit_sha256": fit_hash, "author_witness_sha256": witness_hash}
    results = []
    for saved in witness["results"]:
        boundary = saved["boundary"]
        primary, digest = read_json(AUTHOR / f"{boundary.upper()}_RESULT.json")
        sources[f"author_{boundary}_sha256"] = digest
        assert primary["source_fit_sha256"] == fit_hash and primary["boundary"] == boundary
        results.append(run(boundary, keys, arms, rewards, actual_pair, fit, saved, primary))
    rss = resource.getrusage(resource.RUSAGE_SELF)
    actual = {"cpu_seconds": rss.ru_utime + rss.ru_stime, "wall_seconds": perf_counter() - started,
              "macos_peak_rss_bytes": rss.ru_maxrss, "science_processes": 1, "external_ingress_bytes": 0,
              "explicit_file_read_bytes": provenance["bytes"] + sum(loaded_bytes.values()),
              "explicit_json_read_bytes_by_file": loaded_bytes,
              "nominal_body_read_plus_two_parses_bytes": 3 * provenance["bytes"]}
    output = {"source": provenance, "inputs": sources, "seed": SEED, "draws": DRAWS, "banks": 2,
              "results": results, "resource": actual}
    (HERE / "RECONSTRUCTION.json").write_text(json.dumps(output, default=numeric, allow_nan=False, indent=2) + "\n")
    print(actual, flush=True)


if __name__ == "__main__":
    try:
        main()
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        print(f"terminal CPU {usage.ru_utime + usage.ru_stime:.4f} s, RSS {usage.ru_maxrss} B", flush=True)
