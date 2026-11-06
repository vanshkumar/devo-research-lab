"""Reproduce the released paired contrasts and challenge their cross-roster scope."""

import json
import re

from read_reductions import (
    AUTH_NEW, AUTH_OLD, FOOTPRINT, HERE, INPUTS, NEW, OLD, ROOT,
    Meter, archive, digest, save,
)


def close(actual, expected):
    np.testing.assert_allclose(actual, expected, rtol=0, atol=3e-13)


def ordinary_neural(scores):
    a = scores[:, :, 0, ..., 2] - scores[:, :, 1, ..., 2]
    d = .9 * scores[:, :, 0, ..., 0] - scores[:, :, 1, ..., 0]
    return np.stack([a, d], axis=2).reshape((len(scores), 4) + a.shape[2:])


def check_equal_band(calculated, saved):
    for key in ("point", "lower", "upper"):
        close(calculated[key], saved[key])


def animal_band(x, k):
    point = x.mean(axis=0)
    se = x.std(axis=0, ddof=1) / np.sqrt(len(x))
    crit = t.ppf(1 - .025 / k, len(x) - 1)
    return dict(point=point, se=se, lower=point-crit*se, upper=point+crit*se,
                marginal_one_sided_upper=point+t.ppf(.95, len(x)-1)*se)


def old_bootstrap(x):
    rng = np.random.default_rng(20261105077)
    first = x[rng.integers(0, 40, size=(20_000, 40))]
    second = x[rng.integers(40, 64, size=(20_000, 24))]
    boot = (first.sum(axis=1) + second.sum(axis=1)) / 64
    point = x.mean(axis=0)
    se = np.sqrt(40 * x[:40].var(axis=0, ddof=1) + 24 * x[40:].var(axis=0, ddof=1)) / 64
    crit = np.quantile(np.max(np.abs((boot - point) / se), axis=1), .95)
    return dict(point=point, se=se, critical=crit, lower=point-crit*se, upper=point+crit*se)


def merge_owner(owner):
    return "churchlandlab" if owner == "churchlandlab_ucla" else owner


def summarize(x, labs, merge=True):
    labels = np.array([merge_owner(s) for s in labs]) if merge else np.array(labs)
    return {s: (int(np.sum(labels == s)), x[labels == s].mean(axis=0))
            for s in sorted(set(labels))}


def owner_scores(table, owners, equal=False, omit=None):
    counts = np.array([table[s][0] if s in table and s != omit else 0 for s in owners])
    means = np.array([table[s][1] if s in table else np.zeros(4) for s in owners])
    g = np.count_nonzero(counts)
    assert g > 1
    weights = (counts > 0) / g if equal else counts / counts.sum()
    point = np.einsum("g,gq->q", weights, means)
    influences = np.sqrt(g / (g-1)) * weights[:, None] * (means - point)
    close(influences.sum(axis=0), 0.)
    return point, influences, int(g)


def blend(left, right, w):
    return ((1-w)*left[0] + w*right[0], (1-w)*left[1] + w*right[1], min(left[2], right[2]))


def owner_family(rows):
    point = np.stack([r[0] for r in rows])
    influences = np.stack([r[1] for r in rows])
    se = np.sqrt(np.sum(influences ** 2, axis=1))
    assert np.all(se > 0)
    g = influences.shape[1]
    signs = 2 * ((np.arange(2**g)[:, None] >> np.arange(g)) & 1) - 1
    contrasts = np.einsum("bg,rgq->brq", signs, influences)
    q = np.quantile(np.max(np.abs(contrasts / se), axis=(1, 2)), .95)
    df = min(row[2] - 1 for row in rows)
    k = t.ppf(1 - .025 / point.size, df)
    marginal = t.ppf(.95, np.array([row[2]-1 for row in rows]))[:, None]
    return dict(point=point, se=se, wild_critical=q, bonferroni_t_critical=k, t_df=df,
                wild_lower=point-q*se, wild_upper=point+q*se,
                t_lower=point-k*se, t_upper=point+k*se,
                marginal_one_sided_t_upper=point+marginal*se, sign_patterns=len(signs))


def admissible_interval(corners, columns):
    """All later-roster weights w for which the named upper limits are strictly below margin."""
    lo, hi = 0., 1.
    for c in columns:
        left, right = corners[:, c]
        if max(left, right) < MARGIN[c]:
            continue
        if min(left, right) >= MARGIN[c]:
            return None
        crossing = (MARGIN[c] - left) / (right - left)
        if right > left:
            hi = min(hi, crossing)
        else:
            lo = max(lo, crossing)
    return [lo, hi] if hi > lo else None


def owner_comparison(left, right):
    shared = sorted(set(left) & set(right))
    change = np.array([right[s][1] - left[s][1] for s in shared]).reshape(-1, 4)
    return dict(shared=shared, change_by_shared_owner=change,
                equal_shared_owner_change_band=animal_band(change, 4) if len(shared) >= 2 else None)


def exact_old_source(old):
    highlights = old["highlights"]
    keys = [(origin, metric) for origin in (200, 1000) for metric in ("A", "D")]
    ref = {(r["cutoff"], r["metric"]): r["point"]
           for r in highlights if r["kind"] == "fixed" and r["condition"] == "primary"
           and r["reference"] == "recent_selected" and r["neural"] == "exact256"}
    draws = {}
    for r in highlights:
        if r["kind"] == "source" and r["reference"] == "recent_selected" and r["neural"] == "exact256":
            draws.setdefault(r["draw"], {})[(r["cutoff"], r["metric"])] = r["point"]
    assert sorted(draws) == list(range(32))
    return np.array([[draws[i][key] - ref[key] for key in keys] for i in range(32)])


def run(meter):
    pins = json.loads(meter.read(str((HERE / "INPUT_PINS.json").relative_to(ROOT))))
    assert pins["analysis_plan_sha256"] == digest(meter.read(str((HERE / "PLAN.md").relative_to(ROOT))))

    def summary(path):
        body = meter.read(path)
        assert pins["dictionaries_and_aggregate_sources_sha256"][path] == digest(body)
        return json.loads(body)

    old_frozen = summary(f"{AUTH_OLD}/MAIN_RUN_FREEZE.json")
    new_frozen = summary(FOOTPRINT)["primary_units"]
    old_summary = summary(f"{OLD}/FINAL_CHALLENGE.json")
    refined = summary(f"{OLD}/REFINED_CHECK.json")
    new_summary = summary(f"{NEW}/REVIEW_CALCULATION.json")
    literal = summary(f"{AUTH_NEW}/LITERAL_SENSITIVITY.json")

    old_path, new_path = INPUTS
    old = archive(old_path, meter, pins["archives"][old_path], np)
    old_ids = old["subjects"].tolist()
    assert old_ids == old_frozen["subjects"] and len(set(old_ids)) == 64
    assert old["labs"].tolist() == [old_frozen["labs"][s] for s in old_ids]
    indices = old["primary_indices"].tolist()
    assert indices == old_summary["primary_indices"] == [0, 1, 2, 3]
    assert old["contributions"].shape == (64, 632)
    x_old = old["contributions"][:, indices]
    for i, (origin, metric) in zip(indices, [(200, "A"), (200, "D"), (1000, "A"), (1000, "D")]):
        assert old_summary["labels"][i] == dict(kind="fixed", condition="primary", neural="linear512",
                                               reference="recent_selected", cutoff=origin, horizon=2000, metric=metric)
    old_boot = old_bootstrap(x_old)
    for key in ("lower", "upper"):
        close(old_boot[key], np.array(old_summary["bands"]["primary"][key])[indices])

    new = archive(new_path, meter, pins["archives"][new_path], np)
    new_ids = new["subjects"].tolist()
    assert new_ids == [r["subject"] for r in new_frozen] and len(set(new_ids)) == 192
    assert new["labs"].tolist() == [r["lab"] for r in new_frozen]
    assert new["cohorts"].tolist() == [r["cohort"] for r in new_frozen]
    canonical = lambda s: re.sub("[^a-z0-9]", "", s.lower())
    assert len({canonical(s) for s in old_ids + new_ids}) == 256
    assert new["origins"].tolist() == [200, 1000]
    assert new["actors"].tolist() == ["growth", "recent100", "recent250", "gru"]
    assert new["pooled"].shape == (192, 2, 4, 3) and new["stream_scores"].shape == (192, 2, 4, 2, 3)
    scored = np.take(new["pooled"], [1, 3], axis=2)
    stream = ordinary_neural(np.take(new["stream_scores"], [1, 3], axis=2))
    x_new = ordinary_neural(scored)
    assert new["primary_D"].shape == (192, 3)
    close(x_new[:, 1], new["primary_D"][:, 1])
    newer = animal_band(x_new, 4)
    early_primary = animal_band(x_new[:, 1], 3)
    check_equal_band(early_primary, new_summary["primary"][1]["D"])
    for i, entry in enumerate(new_summary["secondary"]):
        check_equal_band({key: newer[key][i] for key in ("point", "lower", "upper")}, entry["band"])
        if i % 2 == 0:
            for j in range(2):
                check_equal_band(animal_band(stream[:, i, j], 4), entry["stream_bands"][j])

    old512_table = summarize(x_old, old["labs"])
    old_refined = {r["site"]: (r["n"], np.array(r["mean"])) for r in refined["cohort_site"]["sites"]}
    assert {k: v[0] for k, v in old_refined.items()} == {k: v[0] for k, v in old512_table.items()}
    new_table = summarize(x_new, new["labs"])
    owners = sorted(set(old_refined) | set(new_table))
    corner_rows = [owner_scores(table, owners) for table in (old_refined, new_table)]
    roster = owner_family(corner_rows)
    close(roster["point"][0], refined["primary"]["point"])
    close(roster["point"][1], newer["point"])
    separate = owner_family([owner_scores(old512_table, owners), corner_rows[1]])
    no_merge_table = summarize(x_new, new["labs"], merge=False)
    registered = sorted(set(old_refined) | set(no_merge_table))
    unmerged = owner_family([owner_scores(table, registered) for table in (old_refined, no_merge_table)])

    fixed_mix = [blend(*corner_rows, w) for w in (.75, .5)]
    mix = owner_family(fixed_mix)
    equality = owner_family([owner_scores(table, owners, equal=True) for table in (old_refined, new_table)])
    deletes = []
    for owner in owners:
        left, right = [owner_scores(table, owners, omit=owner) for table in (old_refined, new_table)]
        deletes.extend([left, right, blend(left, right, .75)])
    deleted = owner_family(deletes)
    table_delete_point = deleted["point"].reshape(len(owners), 3, 4)

    aggregate = new["cohorts"] == "public_subject_aggregate"
    asd = new["cohorts"] == "ASD_project"
    assert (int(aggregate.sum()), int(asd.sum())) == (116, 76)
    cohort_x = [x_old[:40], x_old[40:], x_new[aggregate], x_new[asd]]
    cohort_labs = [old["labs"][:40], old["labs"][40:], new["labs"][aggregate], new["labs"][asd]]
    cohort_tables = [summarize(x, labs) for x, labs in zip(cohort_x, cohort_labs)]
    multisite = [i for i, table in enumerate(cohort_tables) if len(table) > 1]
    assert multisite == [0, 1, 2] and list(cohort_tables[3]) == ["angelakilab"]
    cohorts = owner_family([owner_scores(cohort_tables[i], owners) for i in multisite])
    refined_cohort_points = np.array([refined["cohort_site"][s] for s in ("old40", "later24")])
    close(np.average(refined_cohort_points, axis=0, weights=[40, 24]), roster["point"][0])
    old_shifts = exact_old_source(old_summary)
    later_draws = {d: np.array([next(s["D"]["point"] for s in new_summary["source"]
                                   if s["draw"] == d and s["origin"] == origin and s["reference"] == "recent100")
                               for origin in (200, 1000)]) for d in (0, 14)}
    shared_shifts = np.broadcast_to(old_shifts[:, None, :], (32, 2, 4)).copy()
    # No later A is observed for these source perturbations. D uses actual later summary
    # shifts only for draws with both roster summaries; otherwise do not posit a later D.
    opposing = []
    for d in (0, 14):
        delta = shared_shifts[d].copy()
        delta[1, 1::2] = later_draws[d] - roster["point"][1, 1::2]
        opposing.append(dict(draw=d, shifts=delta,
                              shifted_points=roster["point"]+delta,
                              shifted_roster_wild_uppers=roster["wild_upper"]+delta,
                              shifted_fixed_mix_wild_upper=mix["wild_upper"][0]+np.array([.25, .75]) @ delta))

    literal_secondary = [{key: row["literal_band"][key] for key in ("point", "lower", "upper")}
                         for row in literal["secondary_selected_four"]]
    stream_bands = [animal_band(stream[:, :, s], 4) for s in range(2)]
    return dict(
        columns=["A200", "D200", "A1000", "D1000"], margins=MARGIN,
        source_counts=dict(roster_animals=[64, 192], disjoint_normalized_deposited_names=256,
                           owner_counts={s: [old_refined.get(s, (0,))[0], new_table.get(s, (0,))[0]] for s in owners},
                           cohort_counts=[40, 24, 116, 76]),
        original=dict(old512_reconstructed=old_boot, old512_original_joint_upper=np.array(old_summary["bands"]["joint"]["upper"])[indices],
                      old1024_primary={k: refined["primary"][k] for k in ("point", "se", "primary", "bonferroni_primary")},
                      old1024_augmented_upper=np.array(refined["augmented"]["joint"]["upper"])[refined["refined_primary_indices"]],
                      later_original_three_reference_gate=new_summary["primary"], later_secondary=newer,
                      later_recent100_primary_reconstructed=early_primary, later_literal_secondary=literal_secondary,
                      later_literal_primary=new_summary["literal"]["primary"]),
        later_risk_by_origin_actor= scored[..., 0].mean(axis=0),
        later_mae_by_origin_actor= scored[..., 2].mean(axis=0),
        roster_shared_owner=roster, roster_using_old512=separate, roster_using_registered_labels=unmerged,
        roster_equal_owner=equality, fixed_and_equal_roster_mix=mix,
        same_owner_working_covariance=(corner_rows[0][1] * corner_rows[1][1]).sum(axis=0),
        leave_owner_out=dict(owners=owners, per_owner_roster_points_and_fixed_mix=table_delete_point,
                             marginal_one_sided_t_upper=deleted["marginal_one_sided_t_upper"].reshape(len(owners), 3, 4),
                             simultaneous_wild_upper=deleted["wild_upper"].reshape(len(owners), 3, 4)),
        recruitment_strata=dict(order=["old40", "later24", "public_subject_aggregate", "ASD_project"],
                                owner_counts_by_stratum=[{s: v[0] for s, v in tab.items()} for tab in cohort_tables],
                                points=[x.mean(axis=0) for x in cohort_x], estimable_shared_owner_indices=multisite,
                                shared_owner_family=cohorts, animal_four_bands=[animal_band(x, 4) for x in cohort_x],
                                old1024_points=refined_cohort_points,
                                within_old_owner_composition=owner_comparison(*cohort_tables[:2]),
                                within_later_owner_composition=owner_comparison(*cohort_tables[2:]),
                                between_rosters_within_shared_owner=owner_comparison(old_refined, new_table)),
        mixture_intervals={
            weighting: {band: {name: admissible_interval(family[band], cols)
                               for name, cols in [("A200", [0]), ("A1000", [2]), ("both_A", [0, 2]),
                                                  ("D200", [1]), ("D1000", [3]), ("both_D", [1, 3])]}
                        for band in ("wild_upper", "t_upper")}
            for weighting, family in [("animal", roster), ("equal_owner_within_roster", equality)]},
        tipping=dict(
            additive_shift_to_point_margin=MARGIN-roster["point"],
            additive_shift_to_roster_wild_upper_margin=MARGIN-roster["wild_upper"],
            additive_shift_to_roster_t_upper_margin=MARGIN-roster["t_upper"],
            additive_shift_to_fixed_mix_point_margin=MARGIN-mix["point"][0],
            additive_shift_to_fixed_mix_wild_upper_margin=MARGIN-mix["wild_upper"][0],
            additive_shift_to_fixed_mix_t_upper_margin=MARGIN-mix["t_upper"][0],
            ordinary_only_risk_shift_to_roster_D_point_margin=-roster["point"][:, 1::2]/.9,
            old_refined_minus_original512=roster["point"][0]-old_boot["point"],
            old_refined_leave_stream_max_abs=refined["numerical"]["leave_one_stream_out_max_abs_shift"],
            old_original_growth_minus_recent100_mae=np.array(refined["absolute_risks"])[:, 0, 0]
            - np.array(refined["absolute_risks"])[:, 1, 0],
            old_original_growth_minus_recent100_mixed_risk=np.array(refined["absolute_risks"])[:, 0, 1]
            - np.array(refined["absolute_risks"])[:, 1, 1],
            later_pooled_stream_points=[s["point"] for s in stream_bands],
            later_pooled_stream_uppers=[s["upper"] for s in stream_bands],
            old_finite_32_matched_exact256_shifts=old_shifts,
            old_source_shift_range=[old_shifts.min(axis=0), old_shifts.max(axis=0)],
            hypothetical_common_A_shifts_break_corner_count=np.sum(
                np.any(roster["wild_upper"][None, :, ::2] + shared_shifts[:, :, ::2] >= .02, axis=(1, 2))),
            hypothetical_common_A_shifts_break_mix_count=np.sum(
                np.any(mix["wild_upper"][None, 0, ::2] + old_shifts[:, ::2] >= .02, axis=1)),
            later_recent100_actual_source=[s for s in new_summary["source"] if s["reference"] == "recent100"],
            opposing_scenarios=opposing),
    )


def jsonify(value):
    if isinstance(value, dict):
        return {k: jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonify(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


if __name__ == "__main__":
    meter = Meter()
    error = None
    try:
        import numpy as np
        from scipy.stats import t

        MARGIN = np.array([.02, 0., .02, 0.])
        result = run(meter)
        save("SYNTHESIS.json", jsonify(result))
        for key in ("roster_shared_owner", "roster_equal_owner", "fixed_and_equal_roster_mix"):
            group = result[key]
            print(key, jsonify({k: group[k] for k in ("point", "wild_upper", "t_upper")}))
        print("recruitment_strata", jsonify(result["recruitment_strata"]["shared_owner_family"]))
        print("mixture_intervals", result["mixture_intervals"])
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        save("RUN_RESOURCES.json", meter.receipt(error))
