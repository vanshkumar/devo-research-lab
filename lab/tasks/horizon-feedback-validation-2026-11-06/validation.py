"""Frozen H6 shadow rollout on the original released train split."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
from time import perf_counter

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import expit, logsumexp, ndtr, ndtri
from scipy.stats import norm, t

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "horizon-feedback-forecast-2026-11-06"
sys.path.insert(0, str(SOURCE))
import develop as original
from source import BODY, KEY, load_games

SEEDS = (2026110601, 2026110602)
DRAWS = 256
BATCH = 24
CURVE_MARGIN = .04
PAYOFF_MARGIN = .65
RESPONSE_MARGIN = .04
BIAS_MARGIN = .02
ROWS = 4000
FIT = SOURCE / "DEVELOPMENT_CLIP.json"
PAIR = original.PAIRS
BETTER_I = PAIR[:, 1] > PAIR[:, 0]
LABELS, INVERSE = np.unique(PAIR, axis=0, return_inverse=True)
MULTIPLICITY = np.bincount(INVERSE)
REWARD = original.REWARDS[:, None, None]


def source():
    observations, games = load_games()
    means = pd.read_csv(BODY, usecols=["m1", "m2"])
    assert len(means) == len(observations)
    observations = pd.concat([observations, means], axis=1)
    assert (observations.groupby(KEY)[["m1", "m2"]].nunique() == 1).all().all()
    h6 = games.loc[games.horizon.eq(6)]
    assert len(h6) == ROWS and (h6.groupby(level=0).size() == 160).all()
    rows = observations.loc[observations.horizon.eq(6)].sort_values(KEY + ["trial"])
    assert rows.set_index(KEY).index[::10].equals(h6.index)
    assert np.array_equal(rows.trial.to_numpy().reshape(ROWS, 10),
                          np.broadcast_to(np.arange(1, 11), (ROWS, 10)))
    arms = (rows.choice.to_numpy() == "I").reshape(ROWS, 10).astype(int)
    rewards = rows.reward.to_numpy().reshape(ROWS, 10).astype(int)
    actual_pairs = rows[["m1", "m2"]].to_numpy()[::10]
    matches = (actual_pairs[:, None] == LABELS).all(axis=2)
    assert (matches.sum(axis=1) == 1).all()
    labels = matches.argmax(axis=1)
    ids, blocks, game = (h6.index.get_level_values(k).to_numpy() for k in range(3))
    return ids, blocks, game, arms, rewards, actual_pairs, labels


def moments(log_table):
    pmf = np.exp(log_table)
    mean = (REWARD * pmf).sum(axis=0)
    sd = np.sqrt(((REWARD - mean) ** 2 * pmf).sum(axis=0))
    z = (REWARD - mean) / sd
    assert np.max(np.abs((z * pmf).sum(axis=0))) < 1e-13
    assert np.allclose((z ** 2 * pmf).sum(axis=0), 1)
    return pmf, mean, z


def expectation(posterior, kernel):
    return np.einsum("gi,ij->gj", posterior, kernel, optimize=False)


def history(arms, rewards):
    state = original.History(len(arms), False)
    for k in range(arms.shape[1]):
        state.add(arms[:, k], rewards[:, k])
    return state


def donor_probabilities(policy, features):
    features = (features - policy.center) / policy.scale
    common = original.vector_dot(features, policy.common[:-1]) + policy.common[-1]
    donors = expectation(features[:, :4], policy.offsets[:, :4].T)
    return expit(common[:, None] + donors + policy.offsets[:, 4])


def exact_handoff(fa, fy, ordinal, first, later, q, pmf, mean, z):
    """Integrate the first and second action and the standardized reward score."""
    n = len(fa)
    p0 = donor_probabilities(first, history(fa, fy).features(np.full(n, 6), 0,
                                                           ordinal, False))
    i0 = p0.mean(axis=1)
    p1, repeat, innovation, opt_delta, reward_delta = np.zeros((5, n))
    for arm, first_weight in enumerate((1 - p0, p0)):
        state = history(np.repeat(fa, 100, axis=0), np.repeat(fy, 100, axis=0))
        state.add(np.full(n * 100, arm), np.tile(original.REWARDS, n))
        x = state.features(np.full(n * 100, 6), 1, np.repeat(ordinal, 100), False)
        p_i = donor_probabilities(later, x).reshape(n, 100, -1)
        joint_i = np.einsum("gd,grd->gr", first_weight, p_i, optimize=False) / p_i.shape[-1]
        p_first = first_weight.mean(axis=1)[:, None]
        joint_repeat = joint_i if arm == 1 else p_first - joint_i
        reward_likelihood = pmf[:, :, arm].T
        p1 += (expectation(q, reward_likelihood) * joint_i).sum(axis=1)
        repeat += (expectation(q, reward_likelihood) * joint_repeat).sum(axis=1)
        innovation += (expectation(q, (pmf * z)[:, :, arm].T)
                       * (joint_repeat - .5 * p_first)).sum(axis=1)
        opt_delta += (expectation(q, reward_likelihood * (2 * BETTER_I[:, None] - 1))
                      * joint_i).sum(axis=1)
        reward_delta += (expectation(q, reward_likelihood * (mean[:, 1:] - mean[:, :1]))
                         * joint_i).sum(axis=1)
    posterior_i = q[:, BETTER_I].sum(axis=1)
    posterior_mean = expectation(q, mean)
    opt_first = 1 - posterior_i + i0 * (2 * posterior_i - 1)
    pay_first = posterior_mean[:, 0] + i0 * original.contrast(posterior_mean)
    return {
        "first_probability_i": i0, "second_probability_i": p1,
        "repeat": repeat, "innovation": innovation,
        "optimum": np.column_stack([opt_first, 1 - posterior_i + opt_delta]),
        "payoff": np.column_stack([pay_first, posterior_mean[:, 0] + reward_delta]),
    }


def environment(q, uniforms, shocks, truncated):
    latent = np.minimum((uniforms[:, None] > np.cumsum(q, axis=1)).sum(axis=1),
                        len(PAIR) - 1)
    mu = PAIR[latent, None, :]
    if truncated:
        low = ndtr((.5 - mu) / original.SIGMA)
        high = ndtr((100.5 - mu) / original.SIGMA)
        shocks = low + (high - low) * shocks
    rewards = np.clip(np.rint(mu + original.SIGMA * ndtri(shocks)), 1, 100).astype(int)
    return latent, rewards


def bank(fa, fy, ordinal, q, posterior_i, posterior_mean, first, later, pmf_mean, z,
         rng, truncated):
    n = len(fa)
    fa, fy, ordinal, q = (np.repeat(x, DRAWS, axis=0) for x in (fa, fy, ordinal, q))
    size = len(fa)
    row = np.arange(size)
    choice = rng.random((size, 6))
    donors = rng.integers(len(first.offsets), size=size)
    simulated_latent, virtual_tape = environment(q, rng.random(size),
                                                rng.random((size, 6, 2)), truncated)
    actual_latent, actual_tape = environment(q, rng.random(size),
                                           rng.random((size, 6, 2)), truncated)
    a, y, seek, _, _ = original.simulate(fa, fy, ordinal, first, (later, False), None,
                                         donors, choice, virtual_tape)
    # Same entire path in each role. Actual shadow tape cannot affect any action.
    y_shadow = np.take_along_axis(actual_tape, a[:, :, None], axis=2)[:, :, 0]
    switch = (a[:, 1:] != a[:, :-1]).astype(float)
    posterior_i = np.repeat(posterior_i, DRAWS)[:, None]
    posterior_mean = np.repeat(posterior_mean, DRAWS, axis=0)
    shadow_opt = 1 - posterior_i + a * (2 * posterior_i - 1)
    shadow_pay = posterior_mean[row[:, None], a]
    relative_to_first = a - a[:, :1]
    latent_gap = original.contrast(pmf_mean[simulated_latent])[:, None]
    opt_gain = 2 * relative_to_first * (BETTER_I[simulated_latent, None] - posterior_i)
    pay_gain = relative_to_first * (latent_gap - original.contrast(posterior_mean)[:, None])
    repeat_sign = .5 - switch[:, 0]
    stats = {
        "adaptive_optimum": shadow_opt + opt_gain,
        "shadow_optimum": shadow_opt,
        "adaptive_payoff": shadow_pay + pay_gain,
        "shadow_payoff": shadow_pay,
        "adaptive_minus_shadow_optimum": opt_gain,
        "adaptive_minus_shadow_payoff": pay_gain,
        "literal_adaptive_optimum": (a == BETTER_I[simulated_latent, None]).astype(float),
        "literal_shadow_optimum": (a == BETTER_I[actual_latent, None]).astype(float),
        "literal_adaptive_payoff": y.astype(float),
        "literal_shadow_payoff": y_shadow.astype(float),
        "adaptive_innovation_mc": z[y[:, 0] - 1, simulated_latent, a[:, 0]] * repeat_sign,
        "shadow_innovation_mc": z[y_shadow[:, 0] - 1, actual_latent, a[:, 0]] * repeat_sign,
        "switch": switch,
        "side_i": a.astype(float),
        "less_sampled": seek.astype(float),
        "all_one_arm": np.all(a == a[:, :1], axis=1).astype(float),
        "adaptive_target": original.target(a, y),
        "shadow_target": original.target(a, y_shadow),
    }
    return {k: x.reshape(n, DRAWS, *x.shape[1:]) for k, x in stats.items()}


def scores(b1, b2, observed, observed_switch):
    x, z = b1.pop("adaptive_target"), b2.pop("adaptive_target")
    u, v = b1.pop("shadow_target"), b2.pop("shadow_target")
    fact = observed[:, None, :]
    d = original.distance

    def energy(a, b, y):
        return .5 * (d(a, y) + d(b, y) - d(a, b))

    stats = {k: .5 * (b1[k] + b2[k]) for k in b1}
    stats["adaptive_energy"] = energy(x, z, fact)
    stats["shadow_energy"] = energy(u, v, fact)
    stats["shadow_minus_adaptive_energy"] = stats["shadow_energy"] - stats["adaptive_energy"]
    stats["choice_energy_common"] = energy(x[..., :-1], z[..., :-1], fact[..., :-1])
    stats["adaptive_reward_crps"] = energy(x[..., -1:], z[..., -1:], fact[..., -1:])
    stats["shadow_reward_crps"] = energy(u[..., -1:], v[..., -1:], fact[..., -1:])
    stats["pair_expected_energy_separation"] = .5 * (d(x, v) + d(z, u) - d(x, z) - d(u, v))
    stats["switch_brier_common"] = ((b1["switch"] - observed_switch[:, None, :])
                                    * (b2["switch"] - observed_switch[:, None, :]))
    assert np.array_equal(x[..., :-1], u[..., :-1])
    assert np.array_equal(z[..., :-1], v[..., :-1])
    return stats


def ceiling(q, means):
    pi = q[:, BETTER_I].sum(axis=1)
    return np.column_stack([1 - pi, pi]), expectation(q, means)


def extremes_with_optimum_band(opt, pay, low, high):
    # For either payoff extremum start with its unconstrained optimal action.
    # Flip the least expensive choices per probability point until the band.
    n = len(opt)
    low = max(low, opt.min(axis=1).mean())
    high = min(high, opt.max(axis=1).mean())
    if high < low - 1e-12:
        return None
    row = np.arange(n)
    extremes = []
    for sign in (-1, 1):
        action = np.argmax(sign * pay, axis=1)
        base_opt = opt[row, action].mean()
        base_pay = pay[row, action].mean()
        target = np.clip(base_opt, low, high)
        if abs(target - base_opt) <= 1e-12:
            extremes.append(float(base_pay))
            continue
        flip_opt = np.sign(target - base_opt) * (opt[row, 1-action] - opt[row, action]) / n
        flip_pay = (pay[row, 1-action] - pay[row, action]) / n
        valid = flip_opt > 0
        move, value = flip_opt[valid], flip_pay[valid]
        order = np.argsort(-sign * value / move)
        move, value = move[order], value[order]
        left = np.abs(target - base_opt) - np.r_[0, np.cumsum(move[:-1])]
        fraction = np.clip(left / move, 0, 1)
        assert abs(np.sum(fraction * move) - np.abs(target - base_opt)) < 1e-10
        extremes.append(float(base_pay + np.sum(fraction * value)))
    assert extremes[1] >= extremes[0] - 1e-12
    return extremes


def feasibility(opt, pay, observed_opt, observed_pay, opt_band, pay_band):
    intervals = [extremes_with_optimum_band(opt, pay, target - opt_band, target + opt_band)
                 for target in observed_opt]
    if None in intervals:
        return {"reward_intervals": intervals, "jointly_feasible": False}
    lo, hi = np.mean(intervals, axis=0)
    return {"reward_intervals": intervals, "pooled_reward_interval": [lo, hi],
            "jointly_feasible": bool(hi >= observed_pay - pay_band - 1e-12
                                     and lo <= observed_pay + pay_band + 1e-12)}


def remaining_inventory(ids, block, game, counts, labels):
    person = np.unique(ids, return_inverse=True)[1]
    assert all(np.all(np.diff(game[ids == i]) > 0) for i in np.unique(ids))
    groups = {
        "person_block_forced_count": person * 100 + block * 10 + counts,
        "person_forced_count": person * 10 + counts,
        "person_block": person * 10 + block,
        "person": person,
    }
    verified = {}
    for label, key in groups.items():
        prior = np.zeros((len(ids), len(LABELS)))
        mismatches = 0
        for code in np.unique(key):
            ix = np.flatnonzero(key == code)
            planned = MULTIPLICITY * len(ix) / len(PAIR)
            seen = np.bincount(labels[ix], minlength=len(LABELS))
            if not np.array_equal(planned, seen):
                mismatches += 1
                continue
            # Use only the frozen factorial quota and earlier true labels.
            for k in ix:
                prior[k] = planned / planned.sum()
                planned[labels[k]] -= 1
        verified[label] = {"groups": len(np.unique(key)), "nonfactorial_groups": mismatches}
        if mismatches == 0 and "chosen_prior" not in verified:
            chosen = prior
            verified["chosen_prior"] = label
    if "chosen_prior" not in verified:
        return verified, None
    return verified, chosen[:, INVERSE] / MULTIPLICITY[INVERSE]


def assignment_audit(game, counts, arms, rewards, pairs, labels, z_actual, pmf):
    def equal_pairs(keys, values):
        _, n = np.unique(keys, axis=0, return_counts=True)
        _, m = np.unique(np.column_stack([keys, values]), axis=0, return_counts=True)
        return int(np.sum(n * (n - 1) // 2)), int(np.sum(m * (m - 1) // 2))

    ordinal_pairs, equal_labels = equal_pairs(np.column_stack([game, counts]), labels)
    keys = np.column_stack([np.repeat(game, 4), np.tile(np.arange(4), ROWS),
                            arms[:, :4].ravel(),
                            pairs[np.arange(ROWS)[:, None], arms[:, :4]].ravel()])
    count, same_reward = equal_pairs(keys, rewards[:, :4].ravel())
    unique_key, occurrences = np.unique(keys, axis=0, return_counts=True)
    arm_means, arm_index = np.unique(PAIR.ravel(), return_index=True)
    agree_p = np.sum(pmf.reshape(100, -1)[:, arm_index] ** 2, axis=0)
    conditional_equal = agree_p[np.searchsorted(arm_means, unique_key[:, -1])]
    lag1 = z_actual.reshape(25, 160)
    lag1 = np.array([np.corrcoef(row[1:], row[:-1])[0, 1] for row in lag1])
    return {
        "same_ordinal_and_forced_count_pairs": ordinal_pairs,
        "same_latent_labels_within_those_pairs": equal_labels,
        "independent_factorial_expected_label_agreement":
            float(np.sum((MULTIPLICITY / len(PAIR)) ** 2)),
        "same_ordinal_trial_arm_mu_forced_pairs": count,
        "exact_reward_agreements": same_reward,
        "independent_conditional_expected_reward_agreements": float(
            np.sum(conditional_equal * occurrences * (occurrences - 1) / 2)),
        "mean_within_person_adjacent_H6_innovation_correlation": float(lag1.mean()),
        "per_person_adjacent_H6_innovation_correlation": lag1,
    }


def null_precision(pmf, z, slope, people):
    log_pmf = np.log(pmf)
    rows = []
    for n in (960, 480):
        # Uniform over the allowed chosen-arm laws and either null repeat sign.
        def bound(lam):
            log_mgf = max(np.max(logsumexp(log_pmf + sign * .5 * lam * z, axis=0))
                          for sign in (-1, 1))
            return (np.log(40) / n + log_mgf) / lam

        cert = minimize_scalar(bound, bounds=(.001, 2), method="bounded").fun
        se = .5 / np.sqrt(n)
        hw = norm.ppf(.975) * se
        rows.append({
            "N": n, "null_SE": se, "normal95_halfwidth": hw,
            "martingale_Chernoff95_halfwidth": cert,
            "normal_power_two_sided_nonzero_at_source": norm.sf((hw - slope) / se)
            + norm.cdf((-hw - slope) / se),
            "normal_probability_exceed_Chernoff_cutoff_at_source": norm.sf((cert - slope) / se),
            "normal_probability_lower95_above_04_at_source":
                norm.sf((RESPONSE_MARGIN + hw - slope) / se),
        })
    return {"fixed_roster": rows,
            "transported_six_person_halfwidth": t.ppf(.975, 5) * np.std(people, ddof=1) / np.sqrt(6)}


def interval(x):
    avg = x.mean(axis=0)
    sd = x.std(axis=0, ddof=1)
    return {"mean": avg, "person_sd": sd,
            "half95": t.ppf(.975, 24) * sd / 5,
            "half90": t.ppf(.95, 24) * sd / 5,
            "projected_six_half95": t.ppf(.975, 5) * sd / np.sqrt(6)}


def screens(opt_diff, payoff_diff):
    def equivalent(error, margin):
        band = interval(error)
        abs_mean = np.abs(band["mean"])
        return {"point": bool(np.all(abs_mean <= margin)),
                "working_TOST": bool(np.all(abs_mean + band["half90"] <= margin))}

    later_pay = equivalent(payoff_diff[:, 1:].mean(axis=1), PAYOFF_MARGIN)
    later_opt = equivalent(opt_diff[:, 1:], CURVE_MARGIN)
    full_opt = equivalent(opt_diff, CURVE_MARGIN)
    pooled_opt = equivalent(opt_diff[:, 1:].mean(axis=1), CURVE_MARGIN)
    each_pay = equivalent(payoff_diff[:, 1:], PAYOFF_MARGIN)
    return {"later_optimum_curve": later_opt, "full_optimum_curve": full_opt,
            "pooled_optimum": pooled_opt, "pooled_payoff": later_pay,
            "all_later_payoff_points": each_pay,
            "primary": {k: later_opt[k] and later_pay[k] for k in later_pay},
            "full_curve_and_payoff": {k: full_opt[k] and later_pay[k] for k in later_pay},
            "pooled": {k: pooled_opt[k] and later_pay[k] for k in later_pay}}


def json_numeric(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("boundary", choices=["clip", "truncate"])
    args = parser.parse_args()
    # This job and the other boundary run serially within the 480 s assignment.
    resource.setrlimit(resource.RLIMIT_CPU, (190, 200))
    start = perf_counter()
    truncated = args.boundary == "truncate"
    log_table = original.LOG_TRUNCATE if truncated else original.LOG_CLIP
    pmf, mean, z = moments(log_table)
    ids, block, game, arms, rewards, pairs, labels = source()
    print("Pinned source and exact H6 support verified.", flush=True)
    fit_raw = FIT.read_bytes()
    fit_record = json.loads(fit_raw)
    fits = fit_record["fitted"]
    people = np.unique(ids)
    assert len(fits) == 5
    for record in fits:
        assert np.array_equal(record["train_ids"], np.setdiff1d(people, record["held_source_ids"]))
    assert np.array_equal(np.sort(np.concatenate([r["held_source_ids"] for r in fits])), people)
    fa, a = arms[:, :4], arms[:, 4:]
    fy, y = rewards[:, :4], rewards[:, 4:]
    ordinal = (game - 160.5) / 160
    q = original.forced_law(fa, fy, log_table)
    opt, pay = ceiling(q, mean)
    latent = np.argmax((pairs[:, None] == PAIR).all(axis=2), axis=1)
    actual_opt = (a == BETTER_I[latent, None]).astype(float)
    actual_z = z[y[:, 0] - 1, latent, a[:, 0]]
    actual_switch = (a[:, 1:] != a[:, :-1]).astype(float)
    actual_moment = actual_z * (.5 - actual_switch[:, 0])
    actual_target = original.target(a, y)

    # Check both potential reward engines on exactly the same test uniforms.
    check_rng = np.random.default_rng(9917)
    latent_u = check_rng.random(24)
    shock_u = check_rng.random((24, 6, 2))
    _, actual_check = environment(q[:24], latent_u, shock_u, truncated)
    reference = original.precompute_rewards(fa[:24], fy[:24], np.zeros((24, 6)),
                                            latent_u, shock_u, truncated)
    assert np.array_equal(actual_check, reference)

    exact = {}
    seed_means = [{} for _ in SEEDS]
    seed_mcvars = [{} for _ in SEEDS]
    rngs = [np.random.default_rng(seed) for seed in SEEDS]
    for record in fits:
        indices = np.flatnonzero(np.isin(ids, record["held_source_ids"]))
        first, later = (original.Policy(**{k: np.array(v) for k, v in record[name].items()})
                        for name in ("first", "history"))
        tick = perf_counter()
        for begin in range(0, len(indices), BATCH):
            ix = indices[begin:begin+BATCH]
            handoff = exact_handoff(fa[ix], fy[ix], ordinal[ix], first, later, q[ix], pmf, mean, z)
            for name, values in handoff.items():
                exact.setdefault(name, np.zeros((ROWS, *values.shape[1:])))[ix] = values
            for seed_idx, rng in enumerate(rngs):
                banks = [bank(fa[ix], fy[ix], ordinal[ix], q[ix], opt[ix, 1], pay[ix],
                              first, later, mean, z, rng, truncated) for _ in range(2)]
                stats = scores(*banks, actual_target[ix], actual_switch[ix])
                for name, values in stats.items():
                    shape = (ROWS, *values.shape[2:])
                    if name not in seed_means[seed_idx]:
                        seed_means[seed_idx][name] = np.zeros(shape)
                        seed_mcvars[seed_idx][name] = np.zeros(shape[1:])
                    seed_means[seed_idx][name][ix] = values.mean(axis=1)
                    seed_mcvars[seed_idx][name] += (values.var(axis=1, ddof=1).sum(axis=0)
                                                    / (DRAWS * ROWS**2))
        print(f"Fold {record['held_source_ids']} completed in {perf_counter() - tick:.2f} s",
              flush=True)

    raw = {k: np.mean([s[k] for s in seed_means], axis=0) for k in seed_means[0]}
    averaged = {k: v.copy() for k, v in raw.items()}
    i_probs = np.column_stack([exact["first_probability_i"], exact["second_probability_i"]])
    averaged["adaptive_optimum"][:, :2] = exact["optimum"]
    averaged["adaptive_payoff"][:, :2] = exact["payoff"]
    averaged["shadow_optimum"][:, :2] = opt[:, :1] + i_probs * original.contrast(opt)[:, None]
    averaged["shadow_payoff"][:, :2] = pay[:, :1] + i_probs * original.contrast(pay)[:, None]
    averaged["adaptive_minus_shadow_optimum"][:, :2] = (
        averaged["adaptive_optimum"][:, :2] - averaged["shadow_optimum"][:, :2])
    averaged["adaptive_minus_shadow_payoff"][:, :2] = (
        averaged["adaptive_payoff"][:, :2] - averaged["shadow_payoff"][:, :2])
    averaged["side_i"][:, :2] = i_probs
    averaged["switch"][:, 0] = 1 - exact["repeat"]
    averaged["observed_optimum"] = actual_opt
    averaged["observed_payoff"] = y
    averaged["observed_switch"] = actual_switch
    averaged["observed_innovation"] = actual_moment
    averaged["adaptive_innovation"] = exact["innovation"]
    averaged["shadow_innovation"] = np.zeros(ROWS)

    row = np.arange(ROWS)
    action_pay = pay.argmax(axis=1)
    action_opt = opt.argmax(axis=1)
    averaged["pay_oracle_optimum"] = opt[row, action_pay]
    averaged["pay_oracle_payoff"] = pay[row, action_pay]
    averaged["opt_oracle_optimum"] = opt[row, action_opt]
    averaged["opt_oracle_payoff"] = pay[row, action_opt]
    averaged["human_minus_opt_ceiling"] = actual_opt - opt.max(axis=1)[:, None]
    averaged["human_minus_pay_ceiling"] = y - pay.max(axis=1)[:, None]
    inventory, prior = remaining_inventory(ids, block, game, fa.sum(axis=1), labels)
    if prior is not None:
        assert np.allclose(prior.sum(axis=1), 1)
        # Evaluate this privileged ceiling only. The primary actors never get this prior.
        likelihood = log_table[fy - 1, :, fa].sum(axis=1)
        with np.errstate(divide="ignore"):
            deplete_q = original.row_prob(likelihood + np.log(prior))
        rich_opt, rich_pay = ceiling(deplete_q, mean)
        averaged["past_reveal_opt_ceiling"] = rich_opt.max(axis=1)
        averaged["past_reveal_pay_ceiling"] = rich_pay.max(axis=1)
        averaged["human_minus_past_reveal_opt_ceiling"] = actual_opt - rich_opt.max(axis=1)[:, None]
        averaged["human_minus_past_reveal_pay_ceiling"] = y - rich_pay.max(axis=1)[:, None]

    by_person = {k: np.stack([v[ids == i].mean(axis=0) for i in people]) for k, v in averaged.items()}
    obs_opt_curve, obs_pay = actual_opt[:, 1:].mean(axis=0), y[:, 1:].mean()
    aggregate = {}
    for model in ("adaptive", "shadow"):
        do = by_person[f"{model}_optimum"] - by_person["observed_optimum"]
        dp = by_person[f"{model}_payoff"] - by_person["observed_payoff"]
        aggregate[model] = {"screens": screens(do, dp), "optimum_bias": interval(do),
                            "payoff_bias": interval(dp),
                            "later_pooled_optimum_bias": interval(do[:, 1:].mean(axis=1)),
                            "later_pooled_payoff_bias": interval(dp[:, 1:].mean(axis=1))}
    source_innovation = by_person["observed_innovation"]
    forecast_innovation = by_person["adaptive_innovation"]
    scope = {
        "conditional_joint_feasibility": feasibility(opt, pay, obs_opt_curve, obs_pay,
                                                     CURVE_MARGIN, PAYOFF_MARGIN),
        "conditional_exact_target_feasibility": feasibility(opt, pay, obs_opt_curve, obs_pay, 0, 0),
        "conditional_pooled_only_feasibility": feasibility(opt, pay, [obs_opt_curve.mean()],
                                                           obs_pay, CURVE_MARGIN, PAYOFF_MARGIN),
        "human_minus_pay_ceiling_later_average": interval(
            by_person["human_minus_pay_ceiling"][:, 1:].mean(axis=1)),
        "privileged_inventory": inventory,
    }
    if prior is not None:
        scope["privileged_joint_feasibility"] = feasibility(rich_opt, rich_pay, obs_opt_curve, obs_pay,
                                                           CURVE_MARGIN, PAYOFF_MARGIN)
        scope["human_minus_past_reveal_pay_ceiling_later_average"] = interval(
            by_person["human_minus_past_reveal_pay_ceiling"][:, 1:].mean(axis=1))

    result = {
        "boundary": args.boundary, "source_fit_sha256": hashlib.sha256(fit_raw).hexdigest(),
        "source_people": people, "source_h6_games": ROWS, "seeds": SEEDS,
        "draws_per_bank": DRAWS, "banks_per_seed": 2,
        "per_person": by_person,
        "summary": {k: interval(v) for k, v in by_person.items()},
        "aggregate_validation": aggregate,
        "adaptive_innovation_bias": interval(forecast_innovation - source_innovation),
        "adaptive_innovation_practically_calibrated_point": bool(
            forecast_innovation.mean() >= RESPONSE_MARGIN
            and np.abs((forecast_innovation - source_innovation).mean()) <= BIAS_MARGIN),
        "actual_innovation_sd_and_mean": [actual_z.std(ddof=1), actual_z.mean()],
        "oracle_scope": scope,
        "assignment_audit": assignment_audit(game, fa.sum(axis=1), arms, rewards, pairs, labels,
                                            actual_z, pmf),
        "forecast_integration": {
            "seed_means": [{k: v.mean(axis=0) for k, v in s.items()} for s in seed_means],
            "combined_conditional_mc_se": {k: np.sqrt(
                np.sum([s[k] for s in seed_mcvars], axis=0)) / len(SEEDS) for k in raw},
            "exact_minus_mc_first_two_optimum": (exact["optimum"]
                                                - raw["adaptive_optimum"][:, :2]).mean(axis=0),
            "exact_minus_mc_first_two_payoff": (exact["payoff"]
                                               - raw["adaptive_payoff"][:, :2]).mean(axis=0),
            "exact_minus_mc_innovation": (exact["innovation"] - raw["adaptive_innovation_mc"]).mean(),
        },
        "six_precision": null_precision(pmf, z, source_innovation.mean(), source_innovation),
    }
    usage = resource.getrusage(resource.RUSAGE_SELF)
    result["cost"] = {"cpu_seconds": usage.ru_utime + usage.ru_stime,
                      "elapsed_seconds": perf_counter() - start,
                      "max_rss_bytes_macos": usage.ru_maxrss,
                      "full_source_scans_booked_bytes": 4 * BODY.stat().st_size,
                      "fit_file_read_bytes": len(fit_raw)}
    output = HERE / f"{args.boundary.upper()}_RESULT.json"
    output.write_text(json.dumps(result, indent=2, allow_nan=False, default=json_numeric) + "\n")
    print(f"Wrote {output.name} | {result['cost']}", flush=True)


if __name__ == "__main__":
    main()
