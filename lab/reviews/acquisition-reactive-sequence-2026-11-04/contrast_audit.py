"""Analyze only saved simulated path laws. Run from the repository root."""

import hashlib
import itertools
import json
import resource
import time
import zipfile
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.special import rel_entr
from scipy.stats import binom


AUTHOR = Path("lab/tasks/acquisition-reactive-sequence-2026-11-04")
SOURCE = AUTHOR / "SEQUENCE_MASSES.npz"
OUT = Path(__file__).resolve().parent
N = 240
ALPHA = 0.05
PATHS = np.array(list(itertools.product(range(3), repeat=6)))
OUTCOMES = np.array([1, 0, -1])


def divergences(a, b, axis):
    return np.stack(
        [rel_entr(a, b).sum(axis=axis), rel_entr(b, a).sum(axis=axis)], axis=-1
    )


def chain(pair):
    """KL of (A,Y), then its exact decomposition into Y and A given Y."""
    a, b = np.moveaxis(pair, 1, 0) / 2
    a_marginal = a.sum(axis=1)
    b_marginal = b.sum(axis=1)
    a_post = a / a_marginal[:, None]
    b_post = b / b_marginal[:, None]
    joint = divergences(a, b, (-2, -1))
    marginal = divergences(a_marginal, b_marginal, -1)
    conditional = np.stack([
        (a_marginal * rel_entr(a_post, b_post).sum(axis=1)).sum(axis=1),
        (b_marginal * rel_entr(b_post, a_post).sum(axis=1)).sum(axis=1),
    ], axis=1)
    np.testing.assert_allclose(joint, marginal + conditional, atol=2e-15, rtol=1e-10)
    return {"joint": joint, "path_only": marginal, "labels_given_path": conditional}


def event_kl(p, q):
    return float(rel_entr(p, q) + rel_entr(1 - p, 1 - q))


def power_cap(forward, reverse):
    """Data processing for a size-.05 rejection event, in both KL directions."""
    def excess(power):
        return max(
            event_kl(power, ALPHA) - max(0, forward),
            event_kl(ALPHA, power) - max(0, reverse),
        )

    return brentq(excess, ALPHA, 1 - 1e-14) if excess(1 - 1e-14) > 0 else 1.0


def caps(total_kl):
    return [power_cap(*total_kl), power_cap(*total_kl[::-1])]


def common_margin(pair, baseline):
    """Calibrate the path marginal while keeping each additive arm contrast."""
    half_contrast = (pair[:, :, 1] - pair[:, :, 0]) / 2
    matched = np.stack(
        [baseline[:, None] - half_contrast, baseline[:, None] + half_contrast], axis=2
    )
    assert matched.min() > 0
    np.testing.assert_allclose(matched.sum(axis=-1), 1, atol=2e-14, rtol=0)
    np.testing.assert_allclose(
        matched[:, :, 1] - matched[:, :, 0], 2 * half_contrast, atol=2e-16, rtol=0
    )
    return matched


def collapse(mass, labels):
    return np.stack([mass[..., labels == k].sum(axis=-1) for k in np.unique(labels)], axis=-1)


def assay_metrics(pair, correct_count=None):
    out = chain(pair)
    midpoint = pair.mean(axis=(1, 2))
    half_contrast = (pair[:, :, 1] - pair[:, :, 0]) / 2
    floor = np.abs(half_contrast).max(axis=1)
    squared_gap = np.square(half_contrast[:, 0] - half_contrast[:, 1])
    floor_mass = floor.sum(axis=-1)
    assert (2 * floor_mass < 1).all()
    assert (floor_mass + .25 < 1).all()

    # Two projected raw anchors. Joint convexity bounds every intermediate
    # baseline, even with different interpolation weights for each stratum.
    anchors = 2 * floor[:, None] + (1 - 2 * floor_mass[:, None, None]) * pair.mean(axis=2)
    endpoint_kl = []
    for anchor in np.moveaxis(anchors, 1, 0):
        endpoint_kl.append(chain(common_margin(pair, anchor))["joint"])
    out["hull"] = np.maximum(*endpoint_kl)
    out["anchor_projection_TV"] = np.abs(anchors - pair.mean(axis=2)).sum(axis=-1) / 2
    out["anchor_kl_recurrent"] = endpoint_kl[0]
    out["anchor_kl_tracker"] = endpoint_kl[1]

    # For ANY shared B >= floor + .25*midpoint, each denominator in
    # chi-squared is >= .25*midpoint. KL <= chi-squared in either direction.
    out["quarter_mid"] = np.repeat(
        (squared_gap / (.25 * midpoint)).sum(axis=-1, keepdims=True), 2, axis=1
    )
    mid_pair = common_margin(pair, anchors.mean(axis=1))
    out["additive_mid"] = chain(mid_pair)["joint"]
    if correct_count is not None:
        out["count_additive_mid"] = chain(collapse(mid_pair, correct_count))["joint"]
        out["first_additive_mid"] = chain(collapse(mid_pair, PATHS[:, 0]))["joint"]
    return out


def reduce_metrics(metrics, weights):
    reduced = {key: np.average(value, axis=0, weights=weights) for key, value in metrics.items()}
    for key in ("joint", "path_only", "hull", "quarter_mid", "additive_mid"):
        reduced[key + "_power_cap_at_240"] = caps(N * reduced[key])
    return {key: np.asarray(value).tolist() for key, value in reduced.items()}


def best_panel(metrics):
    """Most favorable 4x60 panel of distinct sites for both decisions."""
    result = {}
    for key in ("hull", "quarter_mid"):
        panels = (
            (min(caps(60 * metrics[key][list(indices)].sum(axis=0))), indices)
            for indices in itertools.combinations(range(len(metrics[key])), 4)
        )
        best, indices = max(panels)
        result[key] = {"min_directional_cap": best, "indices": indices}
    return result


def path_only_test(marginals, seed, reps=24000):
    rng = np.random.default_rng(seed)
    llr = np.log(marginals[0] / marginals[1])

    def totals(mass):
        cdf = mass.cumsum()
        cdf[-1] = 1
        return np.concatenate([
            llr[np.searchsorted(cdf, rng.random((1000, N)))].sum(axis=1)
            for _ in range(reps // 1000)
        ])

    calibrate_a, calibrate_b, test_a, test_b = [totals(marginals[i]) for i in (0, 1, 0, 1)]
    upper = np.quantile(calibrate_b, 1 - ALPHA)
    lower = np.quantile(calibrate_a, ALPHA)
    return {
        "power_recurrent_then_tracker": [np.mean(test_a > upper), np.mean(test_b < lower)],
        "size_same_order": [np.mean(test_b > upper), np.mean(test_a < lower)],
        "replicates_per_draw": reps,
        "seed": seed,
    }


def dependence(pair, correct):
    mean_path = correct.mean(axis=-1)
    correct_marginals = np.stack(
        [pair[..., correct[:, i]].sum(axis=-1) for i in range(6)], axis=-1
    )
    means = (pair * mean_path).sum(axis=-1)
    variances = (pair * (mean_path - means[..., None]) ** 2).sum(axis=-1)
    independent_variances = (correct_marginals * (1 - correct_marginals)).sum(axis=-1) / 36
    first_var = correct_marginals[..., 0] * (1 - correct_marginals[..., 0])
    return {
        "six_slot_arm_gap_pp": 100 * (means[:, :, 1] - means[:, :, 0]).mean(axis=0),
        "first_arm_gap_pp": 100 * (correct_marginals[:, :, 1, 0] - correct_marginals[:, :, 0, 0]).mean(axis=0),
        "variance_ratio_to_independent_slots": variances.mean(axis=(0, 2)) / independent_variances.mean(axis=(0, 2)),
        "six_slot_fixed_site_halfwidth_pp": 196 * np.sqrt(variances.mean(axis=(0, 2)) * 4 / N),
        "first_fixed_site_halfwidth_pp": 196 * np.sqrt(first_var.mean(axis=(0, 2)) * 4 / N),
    }


def half_diagnostic(halves, weights):
    # Relative reproducibility of the signed model-by-arm effect. Each half
    # integrates a different set of 64 paired curriculum innovations.
    half_gap = (halves[:, 0, 1] - halves[:, 0, 0]) - (halves[:, 1, 1] - halves[:, 1, 0])
    midpoint = halves.mean(axis=(1, 2, 3))
    s1, s2 = np.moveaxis(half_gap, 1, 0)
    terms = np.stack([s1**2, s2**2, s1*s2, ((s1+s2)/2)**2], axis=1)
    return np.average((terms / midpoint[:, None]).sum(axis=-1), axis=0, weights=weights).tolist()


def controls():
    # A shared 20-point arm effect and different marginal levels gives
    # conditional label information, but zero additive effect disagreement.
    same_effect = np.array([[[.3, .7], [.5, .5]], [[.5, .5], [.7, .3]]])[None]
    same = assay_metrics(same_effect)
    assert same["labels_given_path"].min() > 0
    assert np.max(np.abs(same["additive_mid"])) < 1e-15
    # A distinct 20-point arm effect with identical levels is detectable.
    plant = np.array([[[.4, .6], [.6, .4]], [[.5, .5], [.5, .5]]])[None]
    planted = assay_metrics(plant)
    np.testing.assert_allclose(planted["path_only"], 0)
    cutoff = int(binom.isf(ALPHA, N, .5))
    tie = (ALPHA - binom.sf(cutoff, N, .5)) / binom.pmf(cutoff, N, .5)
    power = binom.sf(cutoff, N, .6) + tie * binom.pmf(cutoff, N, .6)
    assert power > .80
    return {
        "equal_effect_raw_label_KL": same["labels_given_path"][0].tolist(),
        "equal_effect_additive_KL": same["additive_mid"][0].tolist(),
        "planted_additive_KL": planted["additive_mid"][0].tolist(),
        "planted_exact_power_recurrent": power,
        "required_KL_for_size_05_power_80": [event_kl(.8, .05), event_kl(.05, .8)],
    }


def main():
    started = time.perf_counter()
    cpu_started = time.process_time()
    with SOURCE.open("rb") as handle:
        digest = hashlib.sha256()
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    assert digest.hexdigest() == "a894214bf8267c4a03a06458725c00cb608acb6a036781c2be8dd1bc2dc7a771"
    with zipfile.ZipFile(SOURCE) as archive:
        expanded = sum(entry.file_size for entry in archive.infolist())
    with np.load(SOURCE) as archive:
        masses = archive["joint"]
        actors = list(archive["actors"])
        sites, index, counts = np.unique(archive["labs"], return_inverse=True, return_counts=True)
        assays = list(zip(archive["assay_names"], archive["assays"]))
        stresses = list(archive["stresses"])
    assert masses.shape == (64, 2, 5, 3, 2, 2, 729)
    assert np.isfinite(masses).all() and masses.min() > 0
    np.testing.assert_allclose(masses.sum(axis=-1), 1, atol=2e-14, rtol=0)
    first = masses.reshape(masses.shape[:-1] + (3, 243)).sum(axis=-1)
    first_discrepancy = np.abs(first - first[:, :, :, :1]).max()
    assert first_discrepancy < 2e-14
    weights = 1 / counts[index]
    unseen = np.isin(sites, ["hoferlab", "wittenlab"])
    result = {
        "sha256": digest.hexdigest(),
        "sites": dict(zip(sites, counts.tolist())),
        "first_across_assays_max_error": first_discrepancy,
        "controls": controls(),
        "comparisons": {},
    }

    for stress_index, stress in enumerate(stresses):
        for actor in ("existing", "session"):
            for assay_index, (assay, signed_assay) in enumerate(assays):
                halves = masses[:, stress_index, :, assay_index][:, [actors.index(actor), actors.index("track")]]
                pair = halves.mean(axis=3)
                site_pair = np.stack([pair[index == i].mean(axis=0) for i in range(len(sites))])
                pooled_pair = site_pair.mean(axis=0, keepdims=True)
                correct = OUTCOMES[PATHS] == -np.sign(signed_assay)
                correct_count = correct.sum(axis=1)
                key = f"{stress}:{actor}:{assay}"
                record = {}
                for measurement, labels in (("joint", None), ("first", PATHS[:, 0])):
                    if measurement == "joint":
                        site_metrics = assay_metrics(site_pair, correct_count)
                        prefix_metrics = assay_metrics(pair, correct_count)
                        pooled = assay_metrics(pooled_pair, correct_count)
                    else:
                        site_metrics = assay_metrics(collapse(site_pair, labels))
                        prefix_metrics = assay_metrics(collapse(pair, labels))
                        pooled = assay_metrics(collapse(pooled_pair, labels))
                    prefix_by_site = {
                        name: np.stack([value[index == i].mean(axis=0) for i in range(len(sites))])
                        for name, value in prefix_metrics.items()
                    }
                    record[measurement] = {
                        "pooled": reduce_metrics(pooled, None),
                        "site_observed": reduce_metrics(site_metrics, None),
                        "prefix_oracle": reduce_metrics(prefix_metrics, weights),
                        "sites_absent_from_actor_optimizer": reduce_metrics(
                            {name: value[unseen] for name, value in site_metrics.items()}, None
                        ),
                        "prefixes_at_sites_absent_from_actor_optimizer": reduce_metrics(
                            {name: value[unseen] for name, value in prefix_by_site.items()}, None
                        ),
                        "best_site_panel": best_panel(site_metrics),
                        "best_prefix_panel": best_panel(prefix_by_site),
                        "site_hull": site_metrics["hull"].tolist(),
                        "site_quarter_mid": site_metrics["quarter_mid"].tolist(),
                    }
                record["dependence"] = {k: v.tolist() for k, v in dependence(site_pair, correct).items()}
                record["half_weighted_norm2_first_second_cross_combined"] = half_diagnostic(halves, weights)
                if assay == "reactive":
                    record["path_only_test"] = path_only_test(
                        pooled_pair[0].mean(axis=1), 41077 + 2 * stress_index + (actor == "session")
                    )
                result["comparisons"][key] = record

    result["accounting"] = {
        "wall_seconds": time.perf_counter() - started,
        "process_cpu_seconds": time.process_time() - cpu_started,
        "ru_maxrss_darwin_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "archive_file_bytes_per_pass": SOURCE.stat().st_size,
        "full_file_hash_passes": 1,
        "nominal_full_file_allowance_for_zip_and_numpy": 2,
        "decoded_all_zip_entries_upper_bytes": expanded,
    }
    (OUT / "CONTRAST_AUDIT.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"Verified saved laws and evaluated {len(result['comparisons'])} comparisons.")


if __name__ == "__main__":
    main()
