"""Whole-person source fits and forced-origin forecasts for the Horizon Task."""
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
import argparse
import json
import resource

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, ndtr, ndtri
from scipy.stats import t as student

from source import BODY, GAPS, HERE, KEY, load_games


SEED = 20261106
MARGIN = .01
SIGMA = 8.
REWARD_SCALE = SIGMA * np.sqrt(5.)
PAIRS = np.array([(mu, mu + gap)[::side]
                  for mu in [40, 60] for gap in np.r_[-GAPS, GAPS]
                  for side in [1, -1]], dtype=float)
GAP = PAIRS[:, 1] - PAIRS[:, 0]
REWARDS = np.arange(1, 101)


def reward_tables():
    upper = ndtr((REWARDS[:, None, None] + .5 - PAIRS) / SIGMA)
    lower = ndtr((REWARDS[:, None, None] - .5 - PAIRS) / SIGMA)
    clipped = upper - lower
    clipped[0] = upper[0]
    clipped[-1] = 1 - lower[-1]
    truncated = (upper - lower) / (upper[-1] - lower[0])
    assert np.allclose(clipped.sum(axis=0), 1, atol=1e-14)
    assert np.allclose(truncated.sum(axis=0), 1, atol=1e-14)
    assert np.all((clipped >= 0) & (truncated >= 0))
    return np.log(np.maximum(clipped, 1e-300)), np.log(np.maximum(truncated, 1e-300))


LOG_CLIP, LOG_TRUNCATE = reward_tables()
LOOK_KERNEL = np.asarray(np.exp(LOG_CLIP) * GAP[None, :, None], dtype=np.float32)
LOOK_LEFT = LOOK_KERNEL[:, :, 0].T.copy()
LOOK_RIGHT = LOOK_KERNEL[:, :, 1].T.copy()


def row_prob(logw):
    weights = np.exp(logw - logw.max(axis=1, keepdims=True))
    return weights / weights.sum(axis=1, keepdims=True)


def forced_law(a, y, table):
    assert a.shape == y.shape and a.shape[1] == 4
    return row_prob(table[y - 1, :, a].sum(axis=1))


def contrast(x):
    return x[:, 1] - x[:, 0]


def vector_dot(x, w):
    return np.einsum("ij,j->i", x, w, optimize=False)


def information_gain_difference(posterior):
    # The arm-specific posterior predictive denominator cancels in
    # E_reward[max(postmean_H, postmean_I)]. The common expected payoff
    # sum also cancels when comparing which arm to sample.
    weights = posterior.astype(np.float32)
    right = np.einsum("bi,ij->bj", weights, LOOK_RIGHT, optimize=False)
    left = np.einsum("bi,ij->bj", weights, LOOK_LEFT, optimize=False)
    assert np.isfinite(right).all() and np.isfinite(left).all()
    return .5 * (np.abs(right).sum(axis=1) - np.abs(left).sum(axis=1))


class History:
    def __init__(self, size, with_posterior):
        self.row = np.arange(size)
        self.n = np.zeros((size, 2), dtype=float)
        self.total = np.zeros_like(self.n)
        self.sq = np.zeros_like(self.n)
        self.last = np.zeros_like(self.n)
        self.ema = np.zeros_like(self.n)
        self.prev = np.zeros(size)
        self.surprise = np.zeros(size)
        self.logw = np.zeros((size, len(PAIRS))) if with_posterior else None

    def add(self, arm, reward):
        at = self.row, arm
        n = self.n[at]
        old = np.divide(self.total[at], np.maximum(n, 1))
        self.surprise = np.where(n > 0, (reward - old) / SIGMA, 0)
        self.prev = arm * 2. - 1.
        self.ema[at] = np.where(n > 0, .6 * self.ema[at] + .4 * reward, reward)
        self.n[at] = n + 1
        self.total[at] += reward
        self.sq[at] += reward ** 2
        self.last[at] = reward
        if self.logw is not None:
            self.logw += LOG_CLIP[reward - 1, :, arm]

    def features(self, horizon, step, ordinal, dynamic):
        n = self.n
        mean = self.total / n
        value = contrast(mean) / SIGMA
        center = (mean.mean(axis=1) - 50) / 20
        counts = -contrast(n) / 3
        info = np.sign(counts)
        uncertainty = n ** -.5
        u_diff = contrast(uncertainty)
        u_total = uncertainty.sum(axis=1) - 1.4
        recent = contrast(self.ema - mean) / SIGMA
        latest = contrast(self.last - mean) / SIGMA
        variability = np.sqrt(np.maximum(0, self.sq / n - mean**2)) / SIGMA
        noise_diff = contrast(variability)
        noise_total = variability.mean(axis=1) - .7
        first_long = (horizon == 6).astype(float)
        progress = np.broadcast_to(np.asarray(step) / 5, len(n))
        phase = np.broadcast_to(np.asarray(step) == 0, len(n))
        stay = self.prev * (1 - .8 * phase)
        surprising = stay * self.surprise
        nonlinear = np.tanh(value)
        columns = [
            value, info, stay, surprising, counts, u_diff, recent, latest,
            noise_diff, noise_total * nonlinear, u_total * value,
            nonlinear, center, center * value, center * counts,
            ordinal, ordinal * value, ordinal * info, ordinal * stay,
            first_long, first_long * value, first_long * info, first_long * stay,
            progress, progress * value, progress * info, progress * stay,
            progress * counts, progress * u_diff, progress * recent,
            progress**2 * value, progress**2 * info, progress**2 * stay,
            (counts == 0) * value, nonlinear * np.abs(counts), nonlinear * u_total,
        ]
        if dynamic:
            posterior = row_prob(self.logw)
            gap_mean = vector_dot(posterior, GAP) / SIGMA
            gap_sd = np.sqrt(np.maximum(
                0, vector_dot(posterior, (GAP / SIGMA)**2) - gap_mean**2))
            p_right = posterior[:, GAP > 0].sum(axis=1)
            sign_odds = ndtri(np.clip(p_right, .001, .999))
            arm_mean = np.einsum("ij,jk->ik", posterior, PAIRS, optimize=False)
            arm_sq = np.einsum("ij,jk->ik", posterior, PAIRS**2, optimize=False)
            arm_sd = np.sqrt(np.maximum(0, arm_sq - arm_mean**2)) / SIGMA
            posterior_bonus = contrast(arm_sd)
            if dynamic == "lookahead":
                remaining = 5 * (1 - progress)
                gain = (information_gain_difference(posterior) / SIGMA
                        if np.any(remaining > 0) else np.zeros(len(n)))
                look = remaining * gain
                return np.column_stack([
                    gap_mean, look, stay, surprising, sign_odds, posterior_bonus,
                    gap_sd * np.tanh(gap_mean), np.tanh(gap_mean), latest, recent,
                    ordinal, ordinal * gap_mean, ordinal * stay,
                    progress, progress * gap_mean, progress * sign_odds, progress * stay,
                    progress**2 * gap_mean, progress**2 * stay,
                ])
            columns.extend([
                gap_mean - value, sign_odds, posterior_bonus, gap_sd * nonlinear,
                posterior_bonus * (1 - progress), sign_odds * progress,
                (gap_mean - value) * progress, gap_mean * gap_sd,
            ])
        return np.column_stack(columns)


def logistic_fit(x, y, l2, offset=0., bounds=None):
    def objective(w):
        z = vector_dot(x, w) + offset
        penalty = .5 * l2 * (w @ w)
        mean_loss = np.mean(np.logaddexp(0., z) - y * z)
        gradient = np.einsum("ij,i->j", x, expit(z) - y, optimize=False) / len(y)
        return mean_loss + penalty, gradient + l2 * w

    fit = minimize(objective, np.zeros(x.shape[1]), jac=True, method="L-BFGS-B", bounds=bounds,
                   options={"gtol": 1e-7, "maxiter": 350, "ftol": 1e-11})
    if not fit.success or not np.isfinite(fit.x).all():
        raise RuntimeError(str(fit.message))
    return fit.x


@dataclass
class Policy:
    center: np.ndarray
    scale: np.ndarray
    common: np.ndarray
    offsets: np.ndarray

    def p(self, x, donor):
        x = (x - self.center) / self.scale
        heterogeneity = self.offsets[donor]
        z = vector_dot(x, self.common[:-1]) + self.common[-1]
        z += (x[:, :4] * heterogeneity[:, :4]).sum(axis=1) + heterogeneity[:, 4]
        return expit(z)

    def packed(self):
        return {k: v.tolist() for k, v in vars(self).items()}


def fit_policy(x, y, ids, train_ids):
    center = x.mean(axis=0)
    scale = np.maximum(.25, x.std(axis=0))
    x = (x - center) / scale
    ones = np.ones(len(x))
    common = logistic_fit(np.column_stack([x, ones]), y, .001)
    pooled_z = vector_dot(x, common[:-1]) + common[-1]
    donor_x = np.column_stack([x[:, :4], ones])
    offsets = []
    for person in train_ids:
        rows = ids == person
        offsets.append(logistic_fit(donor_x[rows], y[rows], .02, pooled_z[rows]))
    return Policy(center, scale, common, np.array(offsets))


def original_features(state):
    value = contrast(state.total / state.n) / SIGMA
    info = -np.sign(contrast(state.n))
    return np.column_stack([value, info, np.ones(len(value))]), info != 0


def first_reference(x, unequal, h, ids, choice):
    estimates = {}
    # The original positive noise scale requires a positive mean coefficient.
    # Retain boundary fits in predictions, but their bonus/noise ratios are unstable.
    beta_floor = .01
    for person in np.unique(ids):
        coef = np.zeros((2, 2, 3))
        for hi, horizon in enumerate([1, 6]):
            for ui in [0, 1]:
                rows = (ids == person) & (h == horizon) & (unequal == bool(ui))
                coef[hi, ui] = logistic_fit(x[rows], choice[rows], .001,
                                            bounds=[(beta_floor, None), (None, None), (None, None)])
        estimates[int(person)] = coef
    stacked = np.array(list(estimates.values()))
    beta = stacked[:, :, :, 0]
    on_floor = np.isclose(beta, beta_floor)
    bonus = SIGMA * stacked[:, :, 1, 1] / beta[:, :, 1]
    noise = SIGMA / beta
    result = {
        "original_information_bonus_median_H1_H6": np.median(bonus, axis=0).tolist(),
        "original_noise_scale_median_H_by_info": np.median(noise, axis=0).tolist(),
        "original_noise_scale_floor_count_H_by_info": on_floor.sum(axis=0).tolist(),
        "people_positive_change_bonus": int(sum(bonus[:, 1] > bonus[:, 0])),
        "people_positive_change_noise_equal_unequal": (noise[:, 1] > noise[:, 0]).sum(axis=0).tolist(),
    }
    return estimates, result


def from_source():
    table, games = load_games()
    table = table.sort_values(KEY + ["trial"])
    row = table.groupby(KEY).ngroup().to_numpy()
    col = table.trial.to_numpy() - 1
    a = np.full((len(games), 10), -1, dtype=int)
    y = np.full_like(a, -1)
    a[row, col] = (table.choice == "I").to_numpy(dtype=int)
    y[row, col] = table.reward.to_numpy(dtype=int)
    ids = games.index.get_level_values(0).to_numpy()
    ordinal = (games.index.get_level_values(2).to_numpy() - 160.5) / 160
    return ids, games.horizon.to_numpy(), ordinal, a, y


def factual_features(h, ordinal, a, y, lookahead):
    state = History(len(h), True)
    for k in range(4):
        state.add(a[:, k], y[:, k])
    first = state.features(h, 0, ordinal, False)
    original, unequal = original_features(state)
    long = h == 6
    state = History(sum(long), True)
    a, y, h, ordinal = a[long], y[long], h[long], ordinal[long]
    for k in range(5):
        state.add(a[:, k], y[:, k])
    base_later = []
    dyn_later = []
    look_later = []
    for k in range(5, 10):
        base_later.append(state.features(h, k-4, ordinal, False))
        dyn_later.append(state.features(h, k-4, ordinal, True))
        if lookahead:
            look_later.append(state.features(h, k-4, ordinal, "lookahead"))
        state.add(a[:, k], y[:, k])
    later = [np.concatenate(base_later), np.concatenate(dyn_later)]
    if lookahead:
        later.append(np.concatenate(look_later))
    return first, original, unequal, later


def simulate(fa, fy, ordinal, first, later, original, donor, choice_u, potential,
             freeze_feedback=False):
    size = len(fa)
    state = History(size, later is not None and later[1])
    measurement = History(size, False) if freeze_feedback else state
    for k in range(4):
        state.add(fa[:, k], fy[:, k])
        if freeze_feedback:
            measurement.add(fa[:, k], fy[:, k])
    forced_mean = state.total / state.n if freeze_feedback else None
    h = np.full(size, 6)
    a = np.empty((size, 6), dtype=int)
    y = np.empty_like(a)
    seek = np.empty_like(a)
    surprise_stay = np.empty_like(a, dtype=float)
    low_p = None
    for k in range(6):
        if original is not None:
            x, unequal = original_features(state)
            w = original[donor, 1, unequal.astype(int)] * (1 - k / 5)
            w += original[donor, 0, unequal.astype(int)] * (k / 5)
            p = expit((x * w).sum(axis=1))
        else:
            actor, dynamic = (first, False) if k == 0 else later
            p = actor.p(state.features(h, k, ordinal, dynamic), donor)
        arm = (choice_u[:, k] < p).astype(int)
        reward = potential[state.row, k, arm]
        if k == 5:
            # Shift 5 percentage points toward the less likely final action.
            low_p = (choice_u[:, k] < p + np.where(p >= .5, -.05, .05)).astype(int)
        a[:, k], y[:, k] = arm, reward
        seek[:, k] = (state.n[state.row, arm] < state.n[state.row, 1-arm]).astype(int)
        surprise_stay[:, k] = measurement.surprise * ((arm * 2 - 1 == measurement.prev) - .5)
        update_reward = reward if forced_mean is None else forced_mean[state.row, arm]
        state.add(arm, update_reward)
        if freeze_feedback:
            measurement.add(arm, reward)
    return a, y, seek, surprise_stay, low_p


def target(a, y):
    return np.column_stack([a[:, 1:], (y[:, 1:].sum(axis=1) - 250.) / REWARD_SCALE])


def distance(x, y):
    return np.sqrt(((x - y)**2).sum(axis=-1))


def precompute_rewards(a, y, choice_u, prior_u, reward_u, truncated):
    table = LOG_TRUNCATE if truncated else LOG_CLIP
    cdf = np.cumsum(forced_law(a, y, table), axis=1)
    latent = np.minimum((prior_u[:, None] > cdf).sum(axis=1), len(PAIRS) - 1)
    means = PAIRS[latent, None, :]
    if truncated:
        low = ndtr((.5 - means) / SIGMA)
        high = ndtr((100.5 - means) / SIGMA)
        reward_u = low + (high - low) * reward_u
    rewards = np.clip(np.rint(means + SIGMA * ndtri(reward_u)), 1, 100).astype(int)
    assert rewards.shape == (*choice_u.shape, 2)
    return rewards


def simulate_bank(fa, fy, ordinal, draws, rng, fits, original, truncated, feedback_control):
    n = len(fa)
    fa, fy, ordinal = [np.repeat(x, draws, axis=0) for x in (fa, fy, ordinal)]
    first, history, posterior = fits[:3]
    donor = rng.integers(len(original), size=n * draws)
    choice_u = rng.random((n * draws, 6))
    potential = precompute_rewards(fa, fy, choice_u, rng.random(n * draws),
                                   rng.random((n * draws, 6, 2)), truncated)
    results = {
        "history": simulate(fa, fy, ordinal, first, (history, False), None,
                            donor, choice_u, potential),
        "posterior": simulate(fa, fy, ordinal, first, (posterior, True), None,
                              donor, choice_u, potential),
        "original_extension": simulate(fa, fy, ordinal, None, None, original,
                                       donor, choice_u, potential),
    }
    assert np.array_equal(results["history"][0][:, 0], results["posterior"][0][:, 0])
    assert np.array_equal(results["history"][1][:, 0], results["posterior"][1][:, 0])
    if feedback_control:
        results["no_feedback"] = simulate(fa, fy, ordinal, first, (history, False), None,
                                          donor, choice_u, potential, freeze_feedback=True)
        for i in [0, 1]:
            assert np.array_equal(results["history"][i][:, 0], results["no_feedback"][i][:, 0])
    if len(fits) == 4:
        results["lookahead"] = simulate(fa, fy, ordinal, first, (fits[3], "lookahead"), None,
                                        donor, choice_u, potential)
        for i in [0, 1]:
            assert np.array_equal(results["history"][i][:, 0], results["lookahead"][i][:, 0])
    transformed = {}
    for model, (action, reward, seek, moment, alternate) in results.items():
        stats = np.column_stack([reward, action, seek, action[:, 1:] != action[:, :-1],
                                 moment[:, 1:], np.all(action == action[:, :1], axis=1)])
        transformed[model] = target(action, reward).reshape(n, draws, 6), stats.reshape(n, draws, -1)
        if model == "history":
            alt_a, alt_y = action.copy(), reward.copy()
            alt_a[:, -1] = alternate
            alt_y[:, -1] = potential[np.arange(len(action)), -1, alternate]
            changed_switch = ((alt_a[:, -1] != alt_a[:, -2]).astype(int) -
                              (action[:, -1] != action[:, -2]))
            change = np.column_stack([changed_switch, alt_y[:, -1] - reward[:, -1],
                                      alt_a[:, -1] - action[:, -1]])
            transformed["last_noise_shift"] = (target(alt_a, alt_y).reshape(n, draws, 6),
                                                change.reshape(n, draws, 3))
    return transformed


def factual_stats(a, y):
    state = History(len(a), False)
    for k in range(4):
        state.add(a[:, k], y[:, k])
    a, y = a[:, 4:], y[:, 4:]
    seek = []
    moment = []
    for k in range(6):
        arm = a[:, k]
        seek.append(state.n[state.row, arm] < state.n[state.row, 1-arm])
        moment.append(state.surprise * ((arm * 2 - 1 == state.prev) - .5))
        state.add(arm, y[:, k])
    return np.column_stack([y, a, np.column_stack(seek), a[:, 1:] != a[:, :-1],
                            np.column_stack(moment[1:]), np.all(a == a[:, :1], axis=1)])


def roll_score(fa, fy, ordinal, obs, draws, rng, fits, original, truncated, feedback_control):
    names = ["history", "posterior", "original_extension"]
    if feedback_control:
        names.append("no_feedback")
    if len(fits) == 4:
        names.append("lookahead")
    keys = ["es", "self", "stat", "reward_covered", "choice_es", "reward_crps"]
    output = {name: {key: [] for key in keys} for name in names}
    dynamic_names = [name for name in names if name in {"posterior", "lookahead"}]
    separation = {name: [] for name in dynamic_names}
    last_shift = []
    for begin in range(0, len(fa), 32):
        take = slice(begin, begin + 32)
        a = simulate_bank(fa[take], fy[take], ordinal[take], draws, rng, fits, original, truncated,
                          feedback_control)
        b = simulate_bank(fa[take], fy[take], ordinal[take], draws, rng, fits, original, truncated,
                          feedback_control)
        y = obs[take, None, :]
        self_risk = {}
        for name in names:
            x, stats_x = a[name]
            z, stats_z = b[name]
            risk = .5 * distance(x, z).mean(axis=1)
            self_risk[name] = risk
            score = .5 * (distance(x, y) + distance(z, y)).mean(axis=1) - risk
            output[name]["es"].append(score)
            output[name]["self"].append(risk)
            for key, portion in [("choice_es", slice(None, -1)), ("reward_crps", slice(-1, None))]:
                v, w, fact = x[..., portion], z[..., portion], y[..., portion]
                score = .5 * (distance(v, fact) + distance(w, fact) - distance(v, w)).mean(axis=1)
                output[name][key].append(score)
            output[name]["stat"].append(.5 * (stats_x + stats_z).mean(axis=1))
            lo, hi = np.quantile(np.concatenate([x[..., -1], z[..., -1]], axis=1),
                                 [.05, .95], axis=1)
            output[name]["reward_covered"].append((lo <= y[:, 0, -1]) & (y[:, 0, -1] <= hi))
        x, z = a["history"][0], b["history"][0]
        for name in dynamic_names:
            xd, zd = a[name][0], b[name][0]
            between = .5 * (distance(x, zd) + distance(z, xd)).mean(axis=1)
            separation[name].append(between - self_risk["history"] - self_risk[name])
        delta_a, delta_stats_a = a["last_noise_shift"]
        delta_b, delta_stats_b = b["last_noise_shift"]
        shift_cross = .5 * (distance(x, delta_b) + distance(z, delta_a)).mean(axis=1)
        alt_self = .5 * distance(delta_a, delta_b).mean(axis=1)
        alt_score = .5 * (distance(delta_a, y) + distance(delta_b, y)).mean(axis=1) - alt_self
        last_shift.append(np.column_stack([
            shift_cross - self_risk["history"] - alt_self,
            alt_score - output["history"]["es"][-1],
            .5 * (delta_stats_a + delta_stats_b).mean(axis=1),
        ]))
    output = {name: {k: np.concatenate(v) for k, v in stats.items()}
              for name, stats in output.items()}
    return output, {name: np.concatenate(a) for name, a in separation.items()}, np.concatenate(last_shift)


def mixture_p(policy, x):
    return np.mean([policy.p(x, np.full(len(x), i)) for i in range(len(policy.offsets))], axis=0)


def logloss(p, y):
    return -np.log(np.clip(np.where(y == 1, p, 1-p), 1e-10, 1.))


def stat_summary(stats):
    return {
        "mean_free_rewards_by_step": stats[:6].tolist(),
        "mean_later_cumulative_reward": float(stats[1:6].sum()),
        "fraction_I_by_step": stats[6:12].tolist(),
        "fraction_less_sampled_by_step": stats[12:18].tolist(),
        "switch_frequency_by_transition": stats[18:23].tolist(),
        "reward_surprise_stay_covariation_by_transition": stats[23:28].tolist(),
        "fraction_all_same_arm": float(stats[-1]),
    }


def check_lookahead():
    # Independently sum conditional best-payoff values across outcomes.
    posterior = forced_law(np.array([[0, 1, 1, 1], [0, 0, 1, 1]]),
                           np.array([[40, 53, 52, 51], [18, 9, 39, 40]]), LOG_CLIP)
    pmf = np.exp(LOG_CLIP)
    future_best = np.einsum("bi,ria,ij->braj", posterior, pmf, PAIRS, optimize=False)
    exact_diff = future_best.max(axis=-1).sum(axis=1)
    check = information_gain_difference(posterior)
    assert np.allclose(check, contrast(exact_diff), atol=1e-5)
    return {"fast": check.tolist(), "explicit": contrast(exact_diff).tolist()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=int, default=256)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--truncated", action="store_true")
    parser.add_argument("--feedback-control", action="store_true")
    parser.add_argument("--lookahead", action="store_true")
    parser.add_argument("--output", required=True, type=lambda s: HERE / Path(s).name)
    args = parser.parse_args()
    assert 1 <= args.draws <= 512
    start = perf_counter()
    ids, h, ordinal, a, y = from_source()
    ppl = np.unique(ids)
    partitions = np.random.default_rng(SEED).permutation(ppl).reshape(5, 5)
    first_x, orig_x, unequal, later_features = factual_features(h, ordinal, a, y, args.lookahead)
    look_check = check_lookahead() if args.lookahead else None
    original, first_result = first_reference(orig_x, unequal, h, ids, a[:, 4])
    origin = a[:, :4], y[:, :4]
    p_origin = forced_law(*origin, LOG_CLIP)
    reverse = forced_law(1 - origin[0], origin[1], LOG_CLIP)
    mate = np.arange(len(PAIRS)) ^ 1
    assert np.allclose(p_origin, reverse[:, mate])
    long = h == 6
    later_ids = np.tile(ids[long], 5)
    later_labels = a[long, 5:].T.reshape(-1)
    observed = target(a[long, 4:], y[long, 4:])
    obs_stats = factual_stats(a[long], y[long])
    rng = np.random.default_rng(args.seed)
    per_person = {}
    fitted = []
    timings = []
    for fold in partitions:
        tic = perf_counter()
        train_ids = np.setdiff1d(ppl, fold)
        first_fit = ~np.isin(ids, fold)
        later_fit = ~np.isin(later_ids, fold)
        first_policy = fit_policy(first_x[first_fit], a[first_fit, 4], ids[first_fit], train_ids)
        policies = [fit_policy(x[later_fit], later_labels[later_fit], later_ids[later_fit], train_ids)
                    for x in later_features]
        original_train = np.array([original[i] for i in train_ids])
        fits = (first_policy, *policies)
        fitted.append({
            "held_source_ids": fold.tolist(), "train_ids": train_ids.tolist(),
            "first": first_policy.packed(), "history": policies[0].packed(),
            "posterior": policies[1].packed(), "original": original_train.tolist(),
        })
        if args.lookahead:
            fitted[-1]["lookahead"] = policies[2].packed()
        fit_s = perf_counter() - tic
        first_eval = ~first_fit
        later_eval = ~later_fit
        first_pred = mixture_p(first_policy, first_x[first_eval])
        ref_x = orig_x[first_eval]
        ref_weights = original_train[:, (h[first_eval] == 6).astype(int),
                                     unequal[first_eval].astype(int)]
        first_orig = expit((ref_x * ref_weights).sum(axis=2)).mean(axis=0)
        nll = [logloss(mixture_p(p, x[later_eval]), later_labels[later_eval])
               for p, x in zip(policies, later_features)]
        use_long = np.isin(ids[long], fold)
        scored, expected, shift = roll_score(a[long][use_long, :4], y[long][use_long, :4],
                                             ordinal[long][use_long], observed[use_long],
                                             args.draws, rng, fits, original_train, args.truncated,
                                             args.feedback_control)
        sim_s = perf_counter() - tic - fit_s
        for person in fold:
            u = ids[long][use_long] == person
            first_rows = ids[first_eval] == person
            y_first = a[first_eval, 4][first_rows]
            later_rows = later_ids[later_eval] == person
            row = {
                "observed_stats": stat_summary(obs_stats[use_long][u].mean(axis=0)),
                "joint_expected_score_separation": float(expected["posterior"][u].mean()),
                "joint_expected_last_noise_shift": float(shift[u, 0].mean()),
                "observed_score_cost_of_last_noise_shift": float(shift[u, 1].mean()),
                "last_noise_shift_final_switch_reward_I_change": shift[u, 2:].mean(axis=0).tolist(),
                "first_nll_history": float(logloss(first_pred[first_rows], y_first).mean()),
                "first_nll_original": float(logloss(first_orig[first_rows], y_first).mean()),
                "later_factual_nll_history": float(nll[0][later_rows].mean()),
                "later_factual_nll_posterior": float(nll[1][later_rows].mean()),
            }
            if args.lookahead:
                row["joint_expected_lookahead_separation"] = float(expected["lookahead"][u].mean())
                row["later_factual_nll_lookahead"] = float(nll[2][later_rows].mean())
            for name, metrics in scored.items():
                row[name] = {"score": float(metrics["es"][u].mean()),
                             "self_risk": float(metrics["self"][u].mean()),
                             "choice_es": float(metrics["choice_es"][u].mean()),
                             "reward_crps": float(metrics["reward_crps"][u].mean()),
                             "later_reward_90pct_coverage": float(metrics["reward_covered"][u].mean()),
                             "stats": stat_summary(metrics["stat"][u].mean(axis=0))}
            per_person[int(person)] = row
        timings.append({"fold": fold.tolist(), "fit_seconds": fit_s, "rollout_seconds": sim_s})
        print(f"fold {fold.tolist()} fit {fit_s:.2f}s, rollout and diagnostics {sim_s:.2f}s", flush=True)
    results = [per_person[int(person)] for person in ppl]
    names = ["history", "posterior", "original_extension"]
    if args.feedback_control:
        names.append("no_feedback")
    if args.lookahead:
        names.append("lookahead")
    scores = {name: np.array([r[name]["score"] for r in results]) for name in names}
    gain = scores["history"] - scores["posterior"]
    avg, sd = gain.mean(), gain.std(ddof=1)
    half = {str(n): float(student.ppf(.975, n-1)*sd/np.sqrt(n)) for n in [6, 25, 30]}
    mean_over_people = lambda key: float(np.mean([r[key] for r in results]))
    summary = {
        **first_result,
        "scores": {k: float(v.mean()) for k, v in scores.items()},
        "absolute_posterior_gain": float(avg), "relative_posterior_gain": float(avg/scores["history"].mean()),
        "gain_person_sd": float(sd), "gain_person_min_max": [float(gain.min()), float(gain.max())],
        "material_margin": MARGIN, "planning_95pct_halfwidths": half,
        "expected_pair_separation": mean_over_people("joint_expected_score_separation"),
        "expected_last_noise_shift_separation": mean_over_people("joint_expected_last_noise_shift"),
        "later_cumulative_reward": {name: float(np.mean(
            [r[name]["stats"]["mean_later_cumulative_reward"] for r in results])) for name in scores},
        "observed_later_cumulative_reward": float(np.mean(
            [r["observed_stats"]["mean_later_cumulative_reward"] for r in results])),
        "reward_90pct_coverage": {name: float(np.mean(
            [r[name]["later_reward_90pct_coverage"] for r in results])) for name in scores},
    }
    for key in ("first_nll_history", "first_nll_original",
                "later_factual_nll_history", "later_factual_nll_posterior"):
        summary[key] = mean_over_people(key)
    for key in ("choice_es", "reward_crps"):
        summary[key] = {name: float(np.mean([r[name][key] for r in results])) for name in names}
    if args.lookahead:
        summary["expected_lookahead_separation"] = mean_over_people("joint_expected_lookahead_separation")
        summary["later_factual_nll_lookahead"] = mean_over_people("later_factual_nll_lookahead")
        summary["lookahead_value_check"] = look_check
    usage = resource.getrusage(resource.RUSAGE_SELF)
    output = {
        "seed": args.seed, "independent_draws_per_bank": args.draws, "truncated": args.truncated,
        "feedback_control": args.feedback_control,
        "lookahead": args.lookahead,
        "summary": summary, "per_person": per_person, "timings": timings, "fitted": fitted,
        "usage": {"process_cpu_seconds": usage.ru_utime + usage.ru_stime,
                  "process_peak_rss_bytes_macos": usage.ru_maxrss,
                  "elapsed_work_seconds": perf_counter()-start,
                  "booked_source_read_bytes": 3 * BODY.stat().st_size},
    }
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
