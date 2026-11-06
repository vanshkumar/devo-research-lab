"""Score the fixed Brown endpoint laws on their finite lattice. No trial decode or fit."""

import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import resource
import sys

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import norm, t


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "tasks" / "human-association-source-development-2026-11-05"
READS = {}


def read(name):
    body = (SOURCE / name).read_bytes()
    READS[name] = {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    return body


def inner(x, y):
    return np.einsum("...i,...i->...", x, y, optimize=False)


def apply(x, matrix):
    return np.einsum("...i,ij->...j", x, matrix, optimize=False)


def mass(index, size):
    rows = [np.bincount(row, minlength=size) / row.size
            for row in index.reshape(-1, index.shape[-1])]
    return np.stack(rows).reshape(*index.shape[:-1], size)


def contrasts(values):
    return values[..., :2] - values[..., 2:3]


def simplex_loss(linear, pair):
    """Empirical energy loss minimized over all weights on three fixed endpoint laws."""
    vertices = np.eye(3)
    weights = list(vertices)
    for i, j in ((0, 1), (0, 2), (1, 2)):
        direction = vertices[j] - vertices[i]
        curvature = -direction @ pair @ direction
        if curvature > 1e-12:
            slope = direction @ (linear - pair[:, i])
            weights.append(vertices[i] + np.clip(-slope / curvature, 0, 1) * direction)
    basis = (vertices[:2] - vertices[2]).T
    hessian = -basis.T @ pair @ basis
    if np.linalg.det(hessian) > 1e-20:
        interior = vertices[2] + basis @ np.linalg.solve(
            hessian, -basis.T @ (linear - pair[:, 2]))
        if np.all(interior >= 0):
            weights.append(interior)
    w = np.stack(weights)
    return float(np.min(w @ linear - .5 * inner(w @ pair, w)))


def assignment_range(gain):
    """Sharp min/max over couplings with the given equally weighted marginals."""
    limits = []
    for sign in (1, -1):
        indices = [linear_sum_assignment(sign * g) for g in np.moveaxis(gain, -1, 0)]
        limits.append([gain[i, j, a].mean() for a, (i, j) in enumerate(indices)])
    return np.array(limits)


def balanced(kernel):
    """Keep all recipient and donor weights uniform while favoring likely endpoints."""
    p = np.exp(kernel - kernel.max())
    for _ in range(1000):
        p /= p.sum(axis=1, keepdims=True)
        p /= p.sum(axis=0, keepdims=True)
        if np.max(np.abs(p.sum(axis=1) - 1)) < 1e-10:
            return p
    raise ValueError("trajectory calibration coupling did not balance")


def central_mass(left, at):
    """Expected randomized central-80% coverage, integrating the within-atom uniform."""
    overlap = np.maximum(0., np.minimum(.9, left + at) - np.maximum(.1, left))
    return np.divide(overlap, at, out=((left >= .1) & (left <= .9)).astype(float), where=at > 0)


def verify_controls(k):
    # Two weighted replacement draws consume two banks of k float64 uniforms.
    seed = 1001
    rng = np.random.default_rng(seed)
    rng.choice(3, k, p=[.3, .4, .3])
    rng.choice(2, k, p=[1., 0.])
    np.testing.assert_array_equal(rng.random(k), np.random.default_rng(seed).random(3 * k)[2 * k:])
    assert abs(simplex_loss(np.array([0., 1., 1.]), np.ones((3, 3)) - np.eye(3))) < 1e-12
    assert abs(simplex_loss(np.full(3, .5), np.ones((3, 3)) - np.eye(3)) - 1 / 6) < 1e-12


def main():
    with np.load(io.BytesIO(read("BROWN_FORECAST_COUNTS.npz")), allow_pickle=False) as z:
        data = {key: z[key] for key in ("counts", "truth", "meta", "paired_gains", "posterior")}
    fits = {f["fold"]: f for f in json.loads(read("BROWN_FITS.json"))["folds"]}
    summary = json.loads(read("BROWN_FORECAST.json"))["forecast"]
    audit = json.loads(read("BROWN_SCORE_AUDIT.json"))
    counts, truth, meta, posterior = (data[k] for k in ("counts", "truth", "meta", "posterior"))
    people, person_index = np.unique(meta[:, 0], return_inverse=True)
    people_fold = np.array([np.unique(meta[person_index == i, 3]).item() for i in range(len(people))])
    assert counts.shape == (280, 3, 3, 512, 2) and len(people) == 40
    assert len(np.unique(meta[:, :2], axis=0)) == 280 and truth.sum(axis=0).tolist() == [4817, 90]
    assert summary["actors"] == ["ordinary", "pooled", "personal"]
    assert summary["scenarios"] == ["brown", "rescue_supported", "rescue_distractor"]
    k = counts.shape[3]
    verify_controls(k)
    for f, fit in fits.items():
        held = set(people[people_fold == f])
        cal = set(fit["calibration_people"])
        train = set(fit["fit_people"])
        assert held == set(fit["test_people"]) and held | cal | train == set(people)
        assert (len(held), len(cal), len(train)) == (8, 8, 24)

    # Recover the assigned types without rebuilding any donors or replaying trial states.
    weights = np.array([fits[f]["component_mixture"] for f in meta[:, 3]])
    u = np.stack([np.random.default_rng(20261105 + 1000 * p + b).random(3 * k)[2 * k:]
                  for p, b in meta[:, :2]])
    types = (u[..., None] >= weights.cumsum(axis=1)[:, None, :-1]).sum(axis=-1)
    personal_types = (u[..., None] >= posterior.cumsum(axis=1)[:, None, :-1]).sum(axis=-1)
    same = types == personal_types
    assert np.all(np.any(same, axis=1))
    assert np.all((counts[:, :, 1] == counts[:, :, 2]).all(axis=-1) | ~same[:, None, :])

    n = len(people)
    person = {}
    by_load = {}
    trajectory_gain = np.zeros((n, n, 2))
    trajectory_log_kernel = np.zeros((2, n, n))
    per_load_assignments = []
    minimum_type_particles = k
    for load, number in ((3, 4), (6, 3)):
        rows = meta[:, 2] == load
        ids = person_index[rows]
        local_blocks = meta[rows, 1]
        order = np.stack([np.flatnonzero(ids == i)[np.argsort(local_blocks[ids == i])]
                          for i in range(n)])
        assert order.shape == (n, number)
        h = 5 * load
        x, y = counts[rows], truth[rows]
        assert np.all(x >= 0) and np.all(x.sum(axis=-1) <= h)
        assert np.all(y >= 0) and np.all(y.sum(axis=-1) <= h) and not x[:, 1:, :, :, 1].any()
        grid = np.argwhere(np.indices((h + 1, h + 1)).sum(axis=0) <= h)
        address = np.full((h + 1, h + 1), -1)
        address[tuple(grid.T)] = np.arange(len(grid))
        delta = grid[:, None] - grid
        distance = np.hypot(delta[..., 0], delta[..., 1]) / h
        xi = address[x[..., 0], x[..., 1]]
        yi = address[y[:, 0], y[:, 1]]
        p = mass(xi, len(grid))
        a = apply(p, distance)
        v = inner(p, a)
        within = k / (k - 1) * v
        surface = a - .5 * within[..., None]
        b = np.arange(len(y))
        observed = surface[b, :, :, yi]
        factual_dist = distance[xi, yi[:, None, None, None]].mean(axis=-1)
        half = factual_dist - .5 * distance[xi[..., :k//2], xi[..., k//2:]].mean(axis=-1)
        chunk = xi.reshape(len(y), 3, 3, 4, k // 4)
        mid = k // 8
        chunk_loss = (distance[chunk, yi[:, None, None, None, None]].mean(axis=-1)
                      - .5 * distance[chunk[..., :mid], chunk[..., mid:]].mean(axis=-1))

        shifted = address[np.minimum(grid[:, 0] + 1, h - grid[:, 1]), grid[:, 1]]
        q = mass(shifted[xi[:, 0, 0]], len(grid))
        shift_delta = q - p[:, 0, 0]
        margin = -.5 * inner(shift_delta, apply(shift_delta, distance))
        room = (x[:, 0, 0].sum(axis=-1) < h).mean(axis=-1)

        # Both axes of the forecast-vs-truth comparison include all three clocks.
        cross = np.einsum("btji,bsai->btsja", p, a, optimize=False)
        r = np.arange(3)
        diagonal = distance[xi[:, :, None, :, None, :], xi[:, None, :, None, :, :]].mean(axis=-1)
        off = (k * cross - diagonal) / (k - 1)
        risk = off - .5 * within[:, None, :, None, :]
        empirical_risk = cross - .5 * v[:, None, :, None, :]
        opposed = contrasts(risk[:, 0, 0, 2])
        opposed_reverse = np.stack([risk[:, 0, 0, j, j] - risk[:, 0, 0, j, 2] for j in (0, 1)], axis=1)
        own_actor = np.diagonal(risk[:, 0], axis1=-2, axis2=-1)
        timing = own_actor[:, 1:] - own_actor[:, :1]

        # Oracle subject to the original component laws. Only pooled particles enter
        # each component estimate, so their empirical blend is exactly the pooled law.
        members = types[rows]
        component = np.array([[mass(row[labels == j], len(grid)) for j in range(3)]
                              for row, labels in zip(xi[:, 0, 1], members)])
        min_count = np.stack([(members == j).sum(axis=-1) for j in range(3)], axis=-1)
        minimum_type_particles = min(minimum_type_particles, int(min_count.min()))
        np.testing.assert_allclose(inner(component.swapaxes(-1, -2), min_count[:, None] / k),
                                   p[:, 0, 1], atol=1e-15)
        potential = apply(component, distance)
        component_pair = np.einsum("bti,bsi->bts", component, potential, optimize=False)
        linear = potential[b, :, yi]
        block_oracle = np.array([simplex_loss(l, m) for l, m in zip(linear, component_pair)])
        pool_cross = inner(component, a[:, 0, 1, None, :])
        comp_within = component_pair[:, r, r]
        pure_type_regret = pool_cross - .5 * (comp_within + v[:, 0, 1, None])
        # Correct plug-in optimism for each fixed type vs the intended pooled mixture.
        u_pair = component_pair.copy()
        u_pair[:, r, r] *= min_count / (min_count - 1)
        w = weights[rows]
        u_type_regret = inner(u_pair, w[:, None]) - .5 * (
            u_pair[:, r, r] + inner(inner(u_pair, w[:, None]), w)[:, None])

        gain_surface = (surface[:, 0, :2] - surface[:, 0, 2:3]).transpose(0, 2, 1)
        gain_matrix = gain_surface[:, yi, :]
        per_load_assignments.append(assignment_range(gain_matrix))
        kernels = np.log(apply(p[:, 0, [0, 2]], np.exp(-h * distance))[:, :, yi])
        for rank in order.T:
            trajectory_gain += gain_matrix[rank][:, rank] * (.5 / number)
            trajectory_log_kernel += kernels[rank][:, :, rank].transpose(1, 0, 2) * (.5 / number)

        pp = x[:, 0].astype(float)
        observed_counts = y[:, None, :]
        mean_error = pp.mean(axis=-2) - observed_counts
        left = (pp < observed_counts[:, :, None]).mean(axis=-2)
        at = (pp == observed_counts[:, :, None]).mean(axis=-2)
        var = pp.var(axis=-2).mean(axis=0)
        by_load[str(load)] = {
            "lattice_size": len(grid), "blocks": len(y), "observed_mean_counts": y.mean(axis=0),
            "mean_count_bias": mean_error.mean(axis=0), "mean_count_absolute_error": abs(mean_error).mean(axis=0),
            "randomized_central_80_coverage_integrating_PIT_jitter": central_mass(left, at).mean(axis=0),
            "residual_SD_over_RMS_conditional_SD": mean_error.std(axis=0) / np.sqrt(var),
            "conditional_count_variance_mean": var,
            "unconstrained_outcome_attainable_gain_min_max": [gain_surface.min(axis=1).mean(axis=0),
                                                               gain_surface.max(axis=1).mean(axis=0)],
            "preserve_empirical_load_marginal_gain_min_max": per_load_assignments[-1],
        }

        empirical_loss = a[b, 0, :, yi] - .5 * v[:, 0]
        values = {
            "loss": observed, "half_loss": half, "chunk_loss": chunk_loss,
            "margin": margin, "room": room, "opposed": opposed, "opposed_reverse": opposed_reverse,
            "timing": timing, "cross_clock_gains": contrasts(risk),
            "nominal_empirical_truth_envelope_min": contrasts(empirical_risk[:, :, 0]).min(axis=(1, 2)),
            "nominal_empirical_truth_envelope_max": contrasts(empirical_risk[:, :, 0]).max(axis=(1, 2)),
            "lattice_min": gain_surface.min(axis=1), "lattice_max": gain_surface.max(axis=1),
            "best_case_outcome": grid[gain_surface.argmax(axis=1)],
            "type_linear": linear, "type_pair": component_pair,
            "type_block_oracle_gains": empirical_loss[:, :2] - block_oracle[:, None],
            "type_pure_vs_pool_capacity": pure_type_regret.max(axis=-1),
            "type_pure_vs_pool_capacity_U_sensitivity": u_type_regret.max(axis=-1),
            "per_type_regret": pure_type_regret,
            "per_type_regret_U_sensitivity": u_type_regret,
            "true_type_oracle_under_fitted_prevalence": inner(u_type_regret, w),
            "true_type_oracle_under_recipient_posterior": inner(u_type_regret, posterior[rows]),
            "empirical_loss": empirical_loss,
        }
        for name, v_ in values.items():
            person[name] = person.get(name, 0) + .5 * v_[order].mean(axis=1)

    gains = contrasts(person["loss"])
    nominal = gains[:, 0]
    sd = nominal.std(axis=0, ddof=1)
    mean = nominal.mean(axis=0)
    width = t.ppf(.9875, n - 1) * sd / np.sqrt(n)
    margin = float(person["margin"].mean())
    separation = person["opposed"].mean(axis=0)
    chunk_gains = contrasts(person["chunk_loss"][:, 0].mean(axis=0).T).T
    np.testing.assert_allclose(contrasts(person["half_loss"]), data["paired_gains"], atol=1e-13)
    np.testing.assert_allclose(gains.mean(axis=0), audit["all_distinct_pair_person_equal_gains"], atol=1e-13)
    np.testing.assert_allclose(separation, audit["opposed_law_expected_gain_after_diagonal_correction"], atol=1e-13)
    np.testing.assert_allclose(person["opposed_reverse"].mean(axis=0), -separation, atol=1e-13)
    np.testing.assert_allclose(person["timing"].mean(axis=0),
                               audit["timing_law_expected_loss_penalty_after_diagonal_correction"], atol=1e-13)
    np.testing.assert_allclose(margin, summary["proper_penalty_of_one_correct_opportunity"], atol=1e-13)
    np.testing.assert_allclose(trajectory_gain[np.arange(n), np.arange(n)], nominal, atol=1e-13)

    capacity = {
        "minimum_paths_per_block_type": minimum_type_particles,
        "same_type_CRN_paths_verified_all_clocks": int(same.sum()) * 3,
        "mean_recipient_type_weight_TV_change": float(abs(posterior - weights).sum(axis=-1).mean() / 2),
        "block_oracle_gains_empirical_energy": person["type_block_oracle_gains"].mean(axis=0),
        "person_shared_type_weights_oracle_gains_empirical_energy": (
            person["empirical_loss"][:, :2] - np.array([simplex_loss(l, m) for l, m in zip(
                person["type_linear"], person["type_pair"])])[:, None]).mean(axis=0),
        "max_proper_regret_vs_pooled_if_truth_in_same_component_hull": person["type_pure_vs_pool_capacity"].mean(),
        "finite_particle_correction_sensitivity_of_same_hull_capacity": person[
            "type_pure_vs_pool_capacity_U_sensitivity"].mean(),
        "same_type_all_blocks_proper_regret_capacity": person["per_type_regret"].max(axis=-1).mean(),
        "same_type_all_blocks_proper_regret_capacity_U_sensitivity": person[
            "per_type_regret_U_sensitivity"].max(axis=-1).mean(),
        "true_type_oracle_expected_gain_under_fitted_prevalence": person[
            "true_type_oracle_under_fitted_prevalence"].mean(),
        "true_type_oracle_expected_gain_under_recipient_posterior": person[
            "true_type_oracle_under_recipient_posterior"].mean(),
    }
    critical = norm.ppf(.975)
    projections = {}
    for cohort in (42, 85, 91):
        se = sd / np.sqrt(cohort)
        projections[str(cohort)] = {
            "SE_given_Brown_paired_SD": se, "simultaneous_one_sided_half_width": critical * se,
            "personal_truth_detect_positive": norm.cdf(separation / se - critical),
            "personal_truth_detect_above_margin": norm.cdf((separation - margin) / se - critical),
            "personal_truth_exclude_margin": norm.cdf((margin - separation) / se - critical),
            "rival_truth_detect_harm": norm.cdf(separation / se - critical),
            "true_gain_for_80pct_power_above_margin_per_contrast": margin + (critical + norm.ppf(.8)) * se,
        }
    common_type_cap = capacity["same_type_all_blocks_proper_regret_capacity_U_sensitivity"]
    capacity["fraction_of_shift_toward_optimal_pure_type_required_for_margin"] = np.sqrt(margin / common_type_cap)
    capacity["fraction_of_shift_toward_optimal_pure_type_required_for_80pct_power_at_n91"] = np.sqrt(
        projections["91"]["true_gain_for_80pct_power_above_margin_per_contrast"][1] / common_type_cap)

    results = {
        "utc": datetime.now(timezone.utc).isoformat(), "numpy": np.__version__,
        "axes": {"clock": summary["scenarios"], "actor": summary["actors"], "contrast": summary["contrasts"]},
        "exact_reads": READS, "npz_member_decoded_bytes": sum(v_.nbytes for v_ in data.values()),
        "roster": [n, len(meta)], "observed_totals_correct_omit": truth.sum(axis=0),
        "mean_all_distinct_losses": person["loss"].mean(axis=0), "mean_all_distinct_gains": gains.mean(axis=0),
        "mean_author_half_pair_gains_reconstructed": contrasts(person["half_loss"]).mean(axis=0),
        "mean_per_particle_chunk_gains": chunk_gains,
        "particle_MC_SE_from_four_chunks": chunk_gains.std(axis=1, ddof=1) / 2,
        "nominal_gain_person_SD": sd, "nominal_gain_person_correlation": np.corrcoef(nominal.T)[0, 1],
        "nominal_simultaneous_t_lo_hi": [mean - width, mean + width],
        "nominal_fold_means": [nominal[people_fold == f].mean(axis=0) for f in fits],
        "drop_one_scoring_fold_no_refit_means": [nominal[people_fold != f].mean(axis=0) for f in fits],
        "load_calibration": by_load, "one_opportunity_margin": margin, "share_paths_shift_feasible": person["room"].mean(),
        "opposed_personal_truth": separation, "opposed_rival_truth": person["opposed_reverse"].mean(axis=0),
        "timing_penalty": person["timing"].mean(axis=0),
        "cross_clock_expected_gains_truth_clock_scorer_clock_truth_actor_contrast": person["cross_clock_gains"].mean(axis=0),
        "nominal_frozen_predictors_any_blockwise_mixture_of_9_empirical_truth_laws_lo_hi": [
            person["nominal_empirical_truth_envelope_min"].mean(axis=0),
            person["nominal_empirical_truth_envelope_max"].mean(axis=0)],
        "nominal_unconstrained_lattice_lo_hi": [person["lattice_min"].mean(axis=0), person["lattice_max"].mean(axis=0)],
        "unconstrained_upper_argmax_mean_counts_by_contrast": person["best_case_outcome"].mean(axis=0),
        "nominal_calibrated_load_marginal_lo_hi": np.mean(per_load_assignments, axis=0),
        "nominal_calibrated_intact_trajectory_lo_hi": assignment_range(trajectory_gain),
        "nominal_calibrated_intact_trajectory_uniform_gains": trajectory_gain.mean(axis=(0, 1)),
        "nominal_calibrated_intact_trajectory_balanced_gains_ordinary_personal": [
            np.einsum("ij,ijc->c", balanced(log_kernel), trajectory_gain, optimize=False) / n
            for log_kernel in trajectory_log_kernel],
        "type_capacity": capacity, "conditional_normal_projections": projections,
    }
    r = resource.getrusage(resource.RUSAGE_SELF)
    results["resource_snapshot_before_output"] = {
        "user_seconds": r.ru_utime, "system_seconds": r.ru_stime,
        "max_rss_bytes_on_darwin": r.ru_maxrss if sys.platform == "darwin" else r.ru_maxrss * 1024,
        "major_faults": r.ru_majflt, "http_ingress_bytes": 0,
    }
    print(json.dumps(results, default=lambda x: x.tolist(), indent=2, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        print(f"user={usage.ru_utime:.6f} sys={usage.ru_stime:.6f} peak_rss={usage.ru_maxrss}",
              file=sys.stderr)
