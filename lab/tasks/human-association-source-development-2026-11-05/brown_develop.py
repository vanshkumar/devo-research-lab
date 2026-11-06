"""Fit the Brown forecast and run held-person generated-response development."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import resource
from time import perf_counter, process_time

import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.spatial.distance import cdist
from scipy.special import expit, logsumexp
from scipy.stats import norm, t as student

from brown_forecast import (
    ACTORS, SCENARIOS, TYPE_COUNT, Environment, History, MapBank, Prefix,
    environment, log_key_prob, make_block, make_prefix, prefix_weights, simulate,
)


PARTICLES = 512
FOLDS = 5
RIDGE = 1.5


def load_blocks(path):
    payload = path.read_bytes()
    x = np.load(io.BytesIO(payload), allow_pickle=False)
    if x.shape != (30403, 14) or not np.isfinite(x).all():
        raise ValueError("projection differs from passed Stage A")
    split = np.flatnonzero(np.any(x[1:, :2] != x[:-1, :2], axis=1)) + 1
    blocks = [b for b in np.split(x, split) if b[0, 2] in (3, 6)]
    people = np.unique(x[:, 0]).astype(int)
    if len(blocks) != 280 or len(people) != 40:
        raise ValueError("source roster or block scope differs from Stage A")
    return blocks, people, hashlib.sha256(payload).hexdigest(), len(payload)


def role_data(blocks):
    features, actions, people = [], [], []
    clock_features, omissions = [], []
    for b in blocks:
        p = b.prefix
        h = History(p, TYPE_COUNT, np.arange(TYPE_COUNT))
        for j, (s, a, y) in enumerate(zip(b.cue, b.action, b.feedback)):
            cue = np.full(TYPE_COUNT, s)
            f, timing, _ = h.features(cue)
            if a >= 0:
                features.append(f)
                actions.append(a)
                people.append(p.person)
            if j >= len(p.cue):
                clock_features.append(timing[0])
                omissions.append(a < 0)
            h.advance(cue, np.full(TYPE_COUNT, a), np.full(TYPE_COUNT, y))
    _, pid = np.unique(people, return_inverse=True)
    return (np.stack(features, axis=1), np.array(actions), pid,
            np.array(clock_features), np.array(omissions, dtype=float))


def subject_loglik(lp, y, pid):
    rows = np.arange(len(y))
    return np.stack([np.bincount(pid, weights=part) for part in lp[:, rows, y]])


def key_fit(x, y, pid, initial):
    m, _, _, d = x.shape
    n_people = int(pid.max()) + 1
    row = np.arange(len(y))

    def objective(v):
        coef = v[:d]
        logits = np.r_[v[d:], 0.]
        log_mix = logits - logsumexp(logits)
        lp = log_key_prob(x, coef)
        joint = subject_loglik(lp, y, pid) + log_mix[:, None]
        ll = logsumexp(joint, axis=0)
        resp = np.exp(joint - ll[None, :])
        err = np.exp(lp)
        err[:, row, y] -= 1
        slope = np.einsum("mna,mnaf->f", err * resp[:, pid, None], x, optimize=False)
        grad_mix = n_people * np.exp(log_mix) - resp.sum(axis=1)
        grad = np.r_[slope, grad_mix[:-1]] + RIDGE * v
        loss = -ll.sum() + .5 * RIDGE * np.dot(v, v)
        return loss, grad

    res = minimize(objective, np.r_[initial, np.zeros(m - 1)], jac=True,
                   method="L-BFGS-B", options={"maxiter": 250, "ftol": 1e-10})
    coef = res.x[:d]
    raw = np.r_[res.x[d:], 0.]
    w = np.exp(raw - logsumexp(raw))
    if not np.isfinite(res.fun) or not np.isfinite(coef).all():
        raise ValueError("nonfinite conditional choice fit")
    return coef, w, optimizer_receipt(res)


def optimizer_receipt(res):
    return {"converged": bool(res.success), "iterations": int(res.nit),
            "objective": float(res.fun), "max_abs_gradient": float(np.max(np.abs(res.jac))),
            "message": str(res.message)}


def key_temperature(x, y, pid, coef, mix):
    def loss(temp):
        q = subject_loglik(log_key_prob(x, coef, temp), y, pid)
        return -logsumexp(q + np.log(mix)[:, None], axis=0).sum()

    res = minimize_scalar(loss, bounds=(.5, 2.), method="bounded")
    return float(res.x), {"nll_before": float(loss(1.)), "nll_after": float(res.fun),
                          "converged": bool(res.success)}


def timeout_fit(x, y):
    penalty = np.r_[.01, np.full(x.shape[1] - 1, RIDGE)]

    def objective(b):
        z = np.einsum("nf,f->n", x, b, optimize=False)
        v = np.logaddexp(0., z).sum() - np.dot(y, z)
        v += .5 * np.dot(penalty, b * b)
        g = np.einsum("n,nf->f", expit(z) - y, x, optimize=False) + penalty * b
        return v, g

    init = np.zeros(x.shape[1])
    init[0] = -4.
    res = minimize(objective, init, jac=True, method="L-BFGS-B",
                   options={"maxiter": 250, "ftol": 1e-11})
    return res.x, optimizer_receipt(res)


def timeout_calibration(x, y, b):
    z = np.einsum("nf,f->n", x, b, optimize=False)

    def loss(delta):
        logits = z + delta
        return np.logaddexp(0., logits).sum() - np.dot(y, logits)

    r = minimize_scalar(loss, bounds=(-1.5, 1.5), method="bounded")
    return float(r.x), {"nll_before": float(loss(0.)), "nll_after": float(r.fun),
                        "converged": bool(r.success)}


def fit_models(raw, people):
    out = []
    label = {int(p): j % FOLDS for j, p in enumerate(people)}
    for f in range(FOLDS):
        mark = process_time()
        cf = (f + 1) % FOLDS
        train = [make_block(b) for b in raw if label[int(b[0, 0])] not in (f, cf)]
        cal = [make_block(b) for b in raw if label[int(b[0, 0])] == cf]
        x, y, pid, clock, omit = role_data(train)
        cx, cy, cpid, cclock, comit = role_data(cal)
        ordinary_x = x[:1, :, :, :-4]
        cordinary_x = cx[:1, :, :, :-4]
        ord_coef, ord_mix, o_fit = key_fit(ordinary_x, y, pid, np.zeros(ordinary_x.shape[-1]))
        dyn_coef, mix, d_fit = key_fit(x, y, pid, np.r_[ord_coef, .2, .2, 0., 0.])
        timeout_coef, tm_fit = timeout_fit(clock, omit)
        fitted = process_time()
        o_temp, o_cal = key_temperature(cordinary_x, cy, cpid, ord_coef, ord_mix)
        d_temp, d_cal = key_temperature(cx, cy, cpid, dyn_coef, mix)
        shift, t_cal = timeout_calibration(cclock, comit, timeout_coef)
        out.append({
            "fold": f, "test_people": [int(p) for p in people if label[p] == f],
            "calibration_people": [int(p) for p in people if label[p] == cf],
            "fit_people": [int(p) for p in people if label[p] not in (f, cf)],
            "fit_blocks": len(train), "calibration_blocks": len(cal),
            "fit_answer_rows": len(y), "fit_timeout_rows": len(omit),
            "fit_omissions": int(omit.sum()), "calibration_answer_rows": len(cy),
            "calibration_timeout_rows": len(comit), "calibration_omissions": int(comit.sum()),
            "ordinary_coef": ord_coef.tolist(), "ordinary_temp": o_temp,
            "dynamic_coef": dyn_coef.tolist(), "dynamic_temp": d_temp,
            "component_mixture": mix.tolist(), "timeout_coef": timeout_coef.tolist(),
            "timeout_shift": shift, "fit": [o_fit, d_fit, tm_fit],
            "calibration": [o_cal, d_cal, t_cal],
            "fit_cpu_seconds": fitted - mark,
            "calibration_cpu_seconds": process_time() - fitted,
        })
        print(f"fold {f} fit and calibration terminal", flush=True)
    return out


def prefix_equal(x, y):
    return ((x.person, x.block, x.load) == (y.person, y.block, y.load)
            and all(np.array_equal(getattr(x, k), getattr(y, k))
                    for k in ("cue", "action", "feedback", "rt")))


def energy(paths, target, h):
    mid = len(paths) // 2
    u = paths.astype(float) / h
    return float(np.linalg.norm(u - target / h, axis=1).mean()
                 - .5 * np.linalg.norm(u[:mid] - u[mid:], axis=1).mean())


def empirical_law(paths):
    unique, frequency = np.unique(paths, axis=0, return_counts=True)
    return unique.astype(float), frequency / frequency.sum()


def law_separation(law, other, h):
    x, wx = law
    y, wy = other
    xy = np.sum(cdist(x, y) * wx[:, None] * wy[None, :])
    xx = np.sum(cdist(x, x) * wx[:, None] * wx[None, :])
    yy = np.sum(cdist(y, y) * wy[:, None] * wy[None, :])
    return float((xy - .5 * xx - .5 * yy) / h)


def one_opportunity(law, h):
    x, w = law
    shifted = x.copy()
    shifted[:, 0] = np.minimum(x[:, 0] + 1, h - x[:, 1])
    return law_separation(law, (shifted, w), h)


def score_paths(values, truth, h):
    loss = np.empty(values.shape[:2])
    mc = np.empty((*values.shape[:2], 4))
    for s in range(values.shape[0]):
        for a in range(values.shape[1]):
            p = values[s, a]
            loss[s, a] = energy(p, truth, h)
            mc[s, a] = [energy(part, truth, h) for part in np.split(p, 4)]
    laws = [empirical_law(p) for p in values[0]]
    discrimination = [law_separation(laws[j], laws[2], h) for j in (0, 1)]
    return loss, mc, discrimination, one_opportunity(laws[0], h)


def person_average(values, info):
    people = np.unique(info[:, 0])
    return np.stack([.5 * sum(
        values[(info[:, 0] == person) & (info[:, 2] == load)].mean(axis=0)
        for load in (3, 6)) for person in people])


def paired_summary(d):
    n = len(d)
    avg = d.mean(axis=0)
    sd = d.std(axis=0, ddof=1)
    half = student.ppf(.9875, n - 1) * sd / np.sqrt(n)
    return {"mean": avg.tolist(), "sd": sd.tolist(),
            "nominal_simultaneous_95_lo": (avg - half).tolist(),
            "nominal_simultaneous_95_hi": (avg + half).tolist()}


def calibration(values, truth, meta):
    result = {}
    for load in (3, 6):
        rows = meta[:, 2] == load
        pp, yy = values[rows, 0].astype(float), truth[rows]
        mean = pp.mean(axis=2)
        bias = (mean - yy[:, None, :]).mean(axis=0)
        mae = np.abs(mean - yy[:, None, :]).mean(axis=0)
        low = np.quantile(pp, .1, axis=2)
        high = np.quantile(pp, .9, axis=2)
        coverage = ((yy[:, None, :] >= low) & (yy[:, None, :] <= high)).mean(axis=0)
        probability = (pp[:, :, :, 1] > 0).mean(axis=2)
        brier = ((probability - (yy[:, 1] > 0)[:, None]) ** 2).mean(axis=0)
        lo = (pp < yy[:, None, None, :]).mean(axis=2)
        hi = (pp <= yy[:, None, None, :]).mean(axis=2)
        rng = np.random.default_rng(30591 + load)
        randomized = lo + (hi - lo) * rng.random((len(yy), 1, 2))
        pit = ((randomized >= .1) & (randomized <= .9)).mean(axis=0)
        result[str(load)] = {"mean_error_counts": bias.tolist(), "mae_counts": mae.tolist(),
                             "central_80_count_interval_coverage": coverage.tolist(),
                             "randomized_central_80_pit": pit.tolist(),
                             "any_omission_brier": brier.tolist(),
                             "observed_any_omission": float((yy[:, 1] > 0).mean())}
    return result


def supported_precision(sd, margin):
    out = {}
    z = norm.ppf(.975)
    for n in (42, 85, 91):
        se = sd / np.sqrt(n)
        if np.any(se == 0):
            raise ValueError("degenerate paired-person scale")
        hit = norm.cdf(margin / se - z)
        out[str(n)] = {"one_sided_marginal_halfwidth": (z * se).tolist(),
                       "at_true_2x_margin_detect_material": hit.tolist(),
                       "at_true_zero_exclude_margin": hit.tolist(),
                       "lower_bound_both_individual_events": float(max(0, hit.sum() - 1))}
    return out


def forecast(raw, fits, archive):
    all_meta, all_truth, all_counts, rescues = [], [], [], []
    all_scores, all_mc, all_separation, all_margin = [], [], [], []
    posterior_deltas, all_posterior, donor_notes = [], [], []
    poison_packets = 0
    poison_forecasts = 0
    schedule_mae, observed_repeats, forecast_repeats = [], [], []
    timings = []
    for f in fits:
        tick = process_time()
        train_ids = set(f["fit_people"])
        cal_ids = set(f["calibration_people"])
        test_ids = set(f["test_people"])
        if train_ids & cal_ids or train_ids & test_ids or cal_ids & test_ids:
            raise ValueError("whole-person leakage between roles")
        donors = [make_block(b) for b in raw if int(b[0, 0]) in train_ids]
        banks = {l: MapBank(donors, l) for l in (3, 6)}
        checked = set()
        ordinary = np.array(f["ordinary_coef"])
        dyn = np.array(f["dynamic_coef"])
        tm = np.array(f["timeout_coef"])
        shift = f["timeout_shift"]
        mix = np.array(f["component_mixture"])
        for b in (v for v in raw if int(v[0, 0]) in test_ids):
            prefix, ids = make_prefix(b)
            origin = len(prefix.cue)
            h = 5 * prefix.load
            seed = 20261105 + 1000 * prefix.person + prefix.block
            world = environment(prefix, donors, banks[prefix.load], seed, PARTICLES)
            post = prefix_weights(prefix, dyn, mix, f["dynamic_temp"])
            configs = [(ordinary, f["ordinary_temp"], None),
                       (dyn, f["dynamic_temp"], mix),
                       (dyn, f["dynamic_temp"], post)]
            counts = np.empty((len(SCENARIOS), len(ACTORS), PARTICLES, 2), dtype=np.int16)
            rescued = np.empty(counts.shape[:2], dtype=int)
            for i, scenario in enumerate(SCENARIOS):
                for j, (coef, temp, weights) in enumerate(configs):
                    counts[i, j], rescued[i, j] = simulate(prefix, world, coef, temp, tm, shift,
                                                           weights, scenario)
            if np.any(counts < 0) or np.any(counts.sum(axis=-1) > h) or np.any(counts[1:, :, :, 1]):
                raise ValueError("invalid generated endpoint counts or timing rescue")
            poisoned = b.copy()
            poisoned[origin:] = poisoned[origin:][::-1]
            poisoned[origin:, 3:] = -999
            p2, _ = make_prefix(poisoned)
            if not prefix_equal(prefix, p2):
                raise ValueError("held suffix altered recipient prefix")
            poison_packets += 1
            if prefix.load not in checked:
                p_world = environment(p2, donors, banks[p2.load], seed, PARTICLES)
                for j, (coef, temp, weights) in enumerate(configs):
                    p_weight = (prefix_weights(p2, dyn, mix, f["dynamic_temp"]) if j == 2 else weights)
                    copy, _ = simulate(p2, p_world, coef, temp, tm, shift, p_weight)
                    if not np.array_equal(copy, counts[0, j]):
                        raise ValueError("held suffix poison altered forecast")
                    poison_forecasts += 1
                checked.add(prefix.load)

            # Access real held suffix only in the score and schedule diagnostics.
            suffix = b[origin:origin + h]
            truth = np.array([np.count_nonzero(suffix[:, 11] == 1),
                              np.count_nonzero(suffix[:, 9] == -1)])
            score, mc, separation, margin = score_paths(counts, truth, h)
            all_meta.append([prefix.person, prefix.block, prefix.load, f["fold"]])
            all_truth.append(truth)
            all_counts.append(counts)
            rescues.append(rescued)
            all_scores.append(score)
            all_mc.append(mc)
            all_separation.append(separation)
            all_margin.append(margin)
            all_posterior.append(post)
            posterior_deltas.append(np.abs(post - mix).sum() / 2)
            donor_notes.append([world.donor_options, world.donor_mismatch, world.map_support])
            s = np.searchsorted(ids, suffix[:, 4])
            real_cues = np.r_[prefix.cue, s]
            gen_cues = np.concatenate((np.broadcast_to(prefix.cue, (PARTICLES, origin)),
                                       world.cues), axis=1)
            observed_repeats.append(np.sum(real_cues[origin:] == real_cues[origin - 1:-1]))
            forecast_repeats.append(np.mean(np.sum(gen_cues[:, origin:] == gen_cues[:, origin - 1:-1], axis=1)))
            actual_freq = np.bincount(s, minlength=prefix.load)
            forecast_freq = (world.cues[:, :, None] == np.arange(prefix.load)).sum(axis=1).mean(axis=0)
            schedule_mae.append(np.abs(actual_freq - forecast_freq).mean())
        timings.append(process_time() - tick)
        print(f"fold {f['fold']} generated and scored", flush=True)
    meta, truth, values = np.array(all_meta), np.array(all_truth), np.array(all_counts)
    scores, mc = np.array(all_scores), np.array(all_mc)
    donor_notes = np.array(donor_notes)
    if len(meta) != 280 or len(np.unique(meta[:, 0])) != 40:
        raise ValueError("missed prescribed source units")
    person_scores = person_average(scores, meta)
    paired = person_scores[:, :, :2] - person_scores[:, :, 2, None]
    margin = float(person_average(np.array(all_margin), meta).mean())
    nominal = paired_summary(paired[:, 0])
    sd = np.asarray(nominal["sd"])
    mc_person = person_average(mc, meta)
    mc_gains = (mc_person[:, 0, :2] - mc_person[:, 0, 2, None]).mean(axis=0)
    avg_count = values.mean(axis=3)
    truth_diff = avg_count - truth[:, None, None, :]
    clock_difference = values[:, 1:].astype(float) - values[:, :1]
    clock_horizon = (5 * meta[:, 2])[:, None, None, None, None]
    shift_cost = np.linalg.norm(clock_difference / clock_horizon, axis=-1).mean(axis=3)
    results = {
        "actors": ACTORS, "scenarios": SCENARIOS, "contrasts": ["ordinary-personal", "pooled-personal"],
        "people": 40, "blocks": 280, "particles_per_block_actor_scenario": PARTICLES,
        "forecasts": int(np.prod(values.shape[:-1])),
        "generated_opportunity_updates": int(sum(5 * meta[:, 2]) * len(ACTORS) * len(SCENARIOS) * PARTICLES),
        "stage_cpu_seconds_by_fold": timings,
        "person_equal_energy": person_scores.mean(axis=0).tolist(),
        "nominal_person_paired": nominal,
        "timing_stress_against_brown_person_paired": [paired_summary(paired[:, i]) for i in (1, 2)],
        "four_independent_particle_chunk_mean_gains": mc_gains.tolist(),
        "particle_mc_se_for_full_size_gains": (mc_gains.std(axis=1, ddof=1) / 2).tolist(),
        "fold_mean_gains_nominal": [
            paired[np.isin(np.unique(meta[:, 0]), meta[meta[:, 3] == f, 0]), 0].mean(axis=0).tolist()
            for f in range(FOLDS)
        ],
        "calibration": calibration(values, truth, meta),
        "proper_penalty_of_one_correct_opportunity": margin,
        "opposed_empirical_predictive_separation": person_average(np.array(all_separation), meta).mean(axis=0).tolist(),
        "conditional_precision_projections": supported_precision(sd, margin),
        "timing_mean_count_changes": person_average(avg_count[:, 1:] - avg_count[:, :1], meta).mean(axis=0).tolist(),
        "timing_mean_coupled_joint_norm_change": person_average(shift_cost, meta).mean(axis=0).tolist(),
        "all_rescues": np.sum(rescues, axis=0).tolist(),
        "person_equal_bias_by_scenario": person_average(truth_diff, meta).mean(axis=0).tolist(),
        "prefix_type_update_total_variation_mean": float(np.mean(posterior_deltas)),
        "prefix_type_update_total_variation_max": float(np.max(posterior_deltas)),
        "poison_prefix_packets": poison_packets, "poison_full_nominal_forecasts": poison_forecasts,
        "donors": {"min": int(donor_notes[:, 0].min()), "max": int(donor_notes[:, 0].max()),
                   "fallback_profile_mismatch_blocks": int(np.sum(donor_notes[:, 1] > 0)),
                   "max_profile_mismatch": int(donor_notes[:, 1].max()),
                   "map_support_min": int(donor_notes[:, 2].min()),
                   "map_support_median": float(np.median(donor_notes[:, 2])),
                   "cue_counts_mae": float(np.mean(schedule_mae)),
                   "real_adjacent_repeats_per_target": float(np.mean(observed_repeats)),
                   "predicted_adjacent_repeats_per_target": float(np.mean(forecast_repeats))},
    }
    np.savez_compressed(archive, meta=meta, truth=truth, counts=values, scores=scores,
                        particle_chunk_scores=mc, person_scores=person_scores, paired_gains=paired,
                        law_separation=np.array(all_separation), one_opportunity=np.array(all_margin),
                        posterior=np.array(all_posterior), donor_notes=donor_notes,
                        rescues=np.array(rescues))
    results["forecast_archive_bytes"] = archive.stat().st_size
    return results


def control():
    p = Prefix(1, 1, 3, np.array([0, 1, 2, 1, 2, 0]), np.array([0, 1, -1, 2, 1, 0]),
               np.array([1, 0, -1, 0, 1, 1]), np.array([.5, .6, -1, .5, .5, .5]))
    w = Environment(np.zeros((4, 2), dtype=int), np.array([[0, 0, 1]] * 4), np.full(4, .5),
                    np.zeros((4, 2)), np.full((4, 2), .5), np.ones((4, 2, 3)), 1, 0, 1)
    h = History(p, 1)
    h.observe_prefix(p)
    assert h.seen[0, 2] == 2
    assert h.wins[0, 2, 1] == 1
    assert h.errors[0, 2].sum() == 0
    _, _, rank = h.features(np.array([1]))
    assert rank[0].argmax() == 0
    expected = ([0, 2], [2, 0], [0, 0])
    for i, scenario in enumerate(SCENARIOS):
        vals, _ = simulate(p, w, np.zeros(14), 1., np.r_[100., np.zeros(9)], 0.,
                           scenario=scenario)
        assert np.all(vals == expected[i])
    identical = empirical_law(np.array([[0, 0], [0, 1]]))
    assert law_separation(identical, identical, 2) == 0
    assert one_opportunity(identical, 2) > 0
    return {"source_rows_read": 0, "known_omission_and_rescue_counts": expected,
            "checked": ["omission advances clock without feedback", "truthful wrong-key elimination",
                        "all-rescue corner updates", "energy-law identity and one-opportunity shift"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=("fit", "forecast", "control"))
    p.add_argument("--projection", type=Path)
    p.add_argument("--fit", type=Path)
    p.add_argument("--archive", type=Path)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args()
    start = perf_counter()
    result = {"stage": args.stage, "started_utc": datetime.now(timezone.utc).isoformat()}
    if args.stage == "control":
        result["control"] = control()
    else:
        raw, people, digest, n_bytes = load_blocks(args.projection)
        result["projection_sha256"] = digest
        result["projection_body_bytes"] = n_bytes
        if args.stage == "fit":
            result["folds"] = fit_models(raw, people)
        else:
            fits = json.loads(args.fit.read_text())
            if fits["projection_sha256"] != digest:
                raise ValueError("fit and forecast use different source projections")
            result["forecast"] = forecast(raw, fits["folds"], args.archive)
    r = resource.getrusage(resource.RUSAGE_SELF)
    result["resources"] = {"user_cpu_seconds": r.ru_utime, "sys_cpu_seconds": r.ru_stime,
                           "wall_seconds": perf_counter() - start, "peak_rss_bytes": r.ru_maxrss}
    args.report.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(result["resources"], flush=True)


if __name__ == "__main__":
    main()
