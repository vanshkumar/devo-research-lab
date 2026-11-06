"""Challenge the fixed Horizon recipes on the first 160 released source games."""
import hashlib
import json
import resource
import sys
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.special import logsumexp
from scipy.stats import t as student

HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parents[1] / "tasks" / "horizon-feedback-forecast-2026-11-06"
sys.path.insert(0, str(AUTHOR))
from develop import (History, Policy, distance, factual_stats, from_source,
                     precompute_rewards, simulate, target)


SEED = 202611061458
DRAWS = 256
MODELS = ("history", "lookahead", "zero_voi")


def disable_voi(policy):
    common, offsets = policy.common.copy(), policy.offsets.copy()
    # Preserve the logit of the original standardized model at a raw VOI of zero.
    zero_feature = -policy.center[1] / policy.scale[1]
    common[-1] += zero_feature * common[1]
    offsets[:, -1] += zero_feature * offsets[:, 1]
    common[1] = 0
    offsets[:, 1] = 0
    return Policy(policy.center, policy.scale, common, offsets)


def path_logmass(fa, fy, ordinal, a, y, first, policies):
    """Choice factors with a game-level donor mixture and exact log reduction."""
    state = History(len(fa), True)
    for step in range(4):
        state.add(fa[:, step], fy[:, step])
    h = np.full(len(fa), 6)
    n_donors = len(first.offsets)
    accum = {name: np.zeros((len(fa), n_donors)) for name in MODELS}
    for step in range(6):
        if step == 0:
            first_x = state.features(h, step, ordinal, False)
        else:
            history_x = state.features(h, step, ordinal, False)
            look_x = state.features(h, step, ordinal, "lookahead")
        sign = 2 * a[:, step, None] - 1
        for name in MODELS:
            if step == 0:
                x, policy = first_x, first
            else:
                x = history_x if name == "history" else look_x
                policy = policies[name]
            w = (x - policy.center) / policy.scale
            z = np.einsum("ij,j->i", w, policy.common[:-1])[:, None] + policy.common[-1]
            z = z + np.einsum("ij,kj->ik", w[:, :4], policy.offsets[:, :4])
            z = z + policy.offsets[:, -1]
            accum[name] -= np.logaddexp(0., -sign * z)
        state.add(a[:, step], y[:, step])
    return {name: logsumexp(accum[name], axis=1) - np.log(n_donors) for name in MODELS}


def bank(fa, fy, ordinals, first, policies, rng):
    n = len(fa)
    fa, fy, ordinals = (np.repeat(x, DRAWS, axis=0) for x in (fa, fy, ordinals))
    donor = rng.integers(len(first.offsets), size=len(fa))
    uniform = rng.random((len(fa), 6))
    potential = precompute_rewards(fa, fy, uniform, rng.random(len(fa)),
                                   rng.random((len(fa), 6, 2)), False)
    predictions = {}
    log_ratios = {}
    for name in MODELS:
        features = False if name == "history" else "lookahead"
        a, y, seek, surprise, alternate = simulate(
            fa, fy, ordinals, first, (policies[name], features), None, donor, uniform, potential)
        prediction = target(a, y).reshape(n, DRAWS, 6)
        behavior = np.column_stack([
            a[:, -1] != a[:, -2], seek[:, -1], y[:, -1],
            y[:, 1:].mean(axis=1), surprise[:, 1:].mean(axis=1),
        ]).reshape(n, DRAWS, -1)
        if name == "history":
            first_path = a[:, 0].copy(), y[:, 0].copy()
            alt_a, alt_y = a.copy(), y.copy()
            alt_a[:, -1] = alternate
            alt_y[:, -1] = potential[np.arange(len(a)), -1, alternate]
            shift = target(alt_a, alt_y).reshape(n, DRAWS, 6)
            switch_change = (alternate != a[:, -2]).astype(int) - (a[:, -1] != a[:, -2])
            reward_change = alt_y[:, -1] - y[:, -1]
            anchor = np.column_stack([switch_change, reward_change]).reshape(n, DRAWS, 2)
        else:
            assert np.array_equal(a[:, 0], first_path[0])
            assert np.array_equal(y[:, 0], first_path[1])
        logmass = path_logmass(fa, fy, ordinals, a, y, first, policies)
        log_ratios[name] = np.column_stack([
            logmass["lookahead"] - logmass["history"],
            logmass["lookahead"] - logmass["zero_voi"],
        ]).reshape(n, DRAWS, 2)
        predictions[name] = prediction, behavior
    return predictions, shift, anchor, log_ratios


def challenge(fa, fy, ordinal, a, y, first, policies, rng):
    A, alt_a, anchor_a, truth_a = bank(fa, fy, ordinal, first, policies, rng)
    B, alt_b, anchor_b, truth_b = bank(fa, fy, ordinal, first, policies, rng)
    observed = target(a[:, 4:], y[:, 4:])[:, None, :]
    factual = factual_stats(a, y)
    out = {
        "obs_behavior": np.column_stack([
            factual[:, 22], factual[:, 17], factual[:, 5],
            factual[:, 1:6].mean(axis=1), factual[:, 23:28].mean(axis=1),
        ]),
        "anchor_switch_reward": (anchor_a + anchor_b).mean(axis=1) / 2,
    }
    logmass = path_logmass(fa, fy, ordinal, a[:, 4:], y[:, 4:], first, policies)
    self_dist = {}
    for name in MODELS:
        x, x_beh = A[name]
        z, z_beh = B[name]
        self_dist[name] = distance(x, z).mean(axis=1)
        out[f"{name}_energy"] = (
            (distance(x, observed) + distance(z, observed)).mean(axis=1) - self_dist[name]) / 2
        out[f"{name}_behavior"] = (x_beh + z_beh).mean(axis=1) / 2
        out[f"{name}_choice_path_logmass"] = logmass[name]
        true_ratios = np.concatenate([truth_a[name], truth_b[name]], axis=1)
        out[f"{name}_true_logratios"] = true_ratios.mean(axis=1)
        out[f"{name}_true_logratios_var"] = true_ratios.var(axis=1, ddof=1)
    for left, right in (("history", "lookahead"), ("lookahead", "zero_voi")):
        cross = (distance(A[left][0], B[right][0]) + distance(B[left][0], A[right][0]))
        out[f"energy_separation_{left}_{right}"] = (
            cross.mean(axis=1) - self_dist[left] - self_dist[right]) / 2
    anchor_cross = distance(A["history"][0], alt_b) + distance(B["history"][0], alt_a)
    out["energy_separation_anchor"] = (
        anchor_cross.mean(axis=1) - self_dist["history"] - distance(alt_a, alt_b).mean(axis=1)) / 2
    return out


def measure(people):
    people = np.asarray(people)
    sd = people.std(axis=0, ddof=1)
    return {
        "mean": people.mean(axis=0).tolist(),
        "person_sd": sd.tolist(),
        "halfwidth_25": (student.ppf(.975, 24) * sd / np.sqrt(25)).tolist(),
        "halfwidth_30": (student.ppf(.975, 29) * sd / np.sqrt(30)).tolist(),
        "halfwidth_6": (student.ppf(.975, 5) * sd / np.sqrt(6)).tolist(),
    }


def main():
    start = perf_counter()
    fit_body = (AUTHOR / "DEVELOPMENT_LOOKAHEAD.json").read_bytes()
    fits = json.loads(fit_body)["fitted"]
    ids, h, ordinal, a, y = from_source()
    early = ordinal < 0
    long = early & (h == 6)
    people = np.unique(ids)
    assert len(people) == 25
    early_ordinals = (np.arange(1, 161) - 160.5) / 160
    assert all(np.array_equal(ordinal[early & (ids == i)], early_ordinals) for i in people)
    h6_counts = [int((long & (ids == i)).sum()) for i in people]
    assert all(0 < n < 160 for n in h6_counts)
    forced_i = a[long, :4].sum(axis=1)
    assert set(forced_i) == {1, 2, 3}
    print(f"Early H6 origins {sum(h6_counts)} with per-person range "
          f"{min(h6_counts)}–{max(h6_counts)}", flush=True)
    rng = np.random.default_rng(SEED)
    per_person = []
    for fit in fits:
        held = fit["held_source_ids"]
        assert set(held).isdisjoint(fit["train_ids"])
        first, history, lookahead = (
            Policy(**{k: np.asarray(v) for k, v in fit[name].items()})
            for name in ("first", "history", "lookahead"))
        zero = disable_voi(lookahead)
        probe = np.tile(lookahead.center, (len(first.offsets), 1))
        probe[:, 1] = 0
        donors = np.arange(len(first.offsets))
        assert np.allclose(lookahead.p(probe, donors), zero.p(probe, donors), atol=1e-14)
        policies = dict(zip(MODELS, (history, lookahead, zero)))
        for i in held:
            games = np.flatnonzero(long & (ids == i))
            batches = []
            for start_game in range(0, len(games), 20):
                g = games[start_game:start_game + 20]
                batches.append(challenge(a[g, :4], y[g, :4], ordinal[g], a[g], y[g],
                                         first, policies, rng))
            averages = {}
            for key in batches[0]:
                metric = np.concatenate([batch[key] for batch in batches], axis=0)
                assert np.isfinite(metric).all()
                averages[key] = metric.mean(axis=0).tolist()
            per_person.append({"source_id": int(i), "H6_origins": len(games), **averages})
        print(f"Measured {len(per_person)} source people", flush=True)
    assert sorted(p["source_id"] for p in per_person) == list(people)
    per_person.sort(key=lambda row: row["source_id"])
    by_metric = {k: np.asarray([p[k] for p in per_person])
                 for k in per_person[0] if k not in {"source_id", "H6_origins"}}
    results = {k: measure(v) for k, v in by_metric.items() if not k.endswith("_var")}
    for left, right in (("lookahead", "history"), ("lookahead", "zero_voi")):
        for key in ("energy", "behavior", "choice_path_logmass"):
            results[f"{left}_minus_{right}_{key}"] = measure(
                by_metric[f"{left}_{key}"] - by_metric[f"{right}_{key}"])
    for name in MODELS:
        results[f"{name}_minus_obs_behavior"] = measure(
            by_metric[f"{name}_behavior"] - by_metric["obs_behavior"])
    known_law = {}
    for name in MODELS:
        expectation = by_metric[f"{name}_true_logratios"]
        within_var = by_metric[f"{name}_true_logratios_var"] / np.asarray(h6_counts)[:, None]
        profile_var = expectation.var(axis=0, ddof=1)
        known_law[name] = {
            "average_logratios": expectation.mean(axis=0).tolist(),
            "working_30_same_support_halfwidth": (
                student.ppf(.975, 29) * np.sqrt((profile_var + within_var.mean(axis=0)) / 30)
            ).tolist(),
        }
    usage = resource.getrusage(resource.RUSAGE_SELF)
    out = {
        "seed": SEED,
        "draws_per_independent_bank": DRAWS,
        "people": len(people),
        "games_per_person": 160,
        "H6_origins": sum(h6_counts),
        "H6_origins_per_person_min_max": [min(h6_counts), max(h6_counts)],
        "forced_I_counts_on_H6": np.bincount(forced_i)[1:].tolist(),
        "author_fit_sha256": hashlib.sha256(fit_body).hexdigest(),
        "behavior_order": ["final_switch", "final_less_sampled", "final_reward",
                           "later_reward_per_opportunity", "feedback_stay_moment"],
        "true_logratio_order": ["lookahead_minus_history", "lookahead_minus_zero_voi"],
        "results": results,
        "conditional_law_planning": known_law,
        "per_person": per_person,
        "cost": {"cpu_seconds": usage.ru_utime + usage.ru_stime,
                 "peak_rss_bytes_macos": usage.ru_maxrss, "elapsed_seconds": perf_counter() - start,
                 "source_body_bytes_logical_three_scans": 3 * 2_052_611,
                 "saved_fit_input_bytes": len(fit_body)},
    }
    (HERE / "PROBE_RESULT.json").write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
