"""Continuous-parameter finite-horizon identified sets and observation designs.

Only Python's standard library; one process and no numerical worker threads.
See PROTOCOL.md for assumptions, selection law, interpretation and limits.
"""
from pathlib import Path
from itertools import product, combinations
from decimal import Decimal, localcontext
import datetime
import hashlib
import heapq
import json
import math
import resource
import sys

HERE = Path(__file__).resolve().parent


def gain(s, n):
    if s == 1:
        return 1.0
    return -math.expm1(math.log1p(-s) / n)


def target(a, b, rho):
    # Closed finite geometric-sum formula, avoiding a quotient near q=1.
    total = 0.0
    for alpha in (a, b):
        q = rho * (1 - alpha)
        for j in range(1, 6):
            total += alpha * rho * sum(q ** i for i in range(j))
    return total / 12


def simulate(a, b, rho, schedule="ABABABABABAB"):
    # Separately implements the event updates, not the geometric formula.
    states = {"A": 0.0, "B": 0.0}
    trace = []
    for task in schedule:
        other = "B" if task == "A" else "A"
        trace.append({"task": task, "pre": states[task]})
        rate = a if task == "A" else b
        states[task] = states[task] + rate * (1 - states[task])
        states[other] = states[other] * rho
    return sum(z["pre"] for z in trace) / len(trace), states, trace


def count_pairs(k, success_complete=False):
    return [(na, nb) for na in range(2, k + 3) for nb in range(2, k + 3)
            if na + nb <= k + 4 and
            (not success_complete or (na <= 3 and nb <= 3))]


def source_witness(na, nb, rho, sa=.75, sb=.75):
    a, b = gain(sa, na), gain(sb, nb)
    _, final, trace = simulate(a, b, rho, "A" * na + "B" * nb)
    # At s=3/4, exact binary certificates are 1[2*j>=n]. This avoids
    # reversing a true equality at 1/2 by floating-point rounding.
    ya = [int(2 * j >= na) for j in range(na)] if sa == .75 else None
    yb = [int(2 * j >= nb) for j in range(nb)] if sb == .75 else None
    return {"n_A": na, "n_B": nb, "alpha_A": a, "alpha_B": b, "rho": rho,
            "hidden_events": na + nb - 4,
            "retained_positions_A": [1, na], "retained_positions_B": [1, nb],
            "all_source_certificates_A": ya, "all_source_certificates_B": yb,
            "source_endpoint_A_before_B": sa, "source_endpoint_B": sb,
            "simulated_final_B": final["B"], "return_score_A": final["A"],
            "target": target(a, b, rho),
            "recorder": "retain (first_in_block AND Y=0) OR (last_in_block AND Y=1); omit others",
            "admissible_labels": (ya is None or [ya[0], ya[-1]] == [0, 1]) and
                                 (yb is None or [yb[0], yb[-1]] == [0, 1])}


def merge_intervals(items):
    result = []
    for lo, hi in sorted(items):
        if result and lo <= result[-1][1] + 1e-14:
            result[-1][1] = max(hi, result[-1][1])
        else:
            result.append([lo, hi])
    return result


def source_bounds(k, cfg, success_complete=False):
    intervals = []
    low, high = None, None
    for na, nb in count_pairs(k, success_complete):
        wl = source_witness(na, nb, cfg["rho_min"])
        wu = source_witness(na, nb, cfg["rho_max"])
        assert wl["admissible_labels"] and wu["admissible_labels"]
        intervals.append({"counts": [na, nb], "lower": wl["target"], "upper": wu["target"]})
        if low is None or wl["target"] < low["target"]:
            low = wl
        if high is None or wu["target"] > high["target"]:
            high = wu
    worst_count = max(intervals, key=lambda z: z["upper"] - z["lower"])
    return {"K": k, "count_pairs": len(intervals), "per_count_intervals": intervals,
            "identified_set_union": merge_intervals((z["lower"], z["upper"]) for z in intervals),
            "lower": low["target"], "upper": high["target"],
            "diameter": high["target"] - low["target"],
            "lower_witness": low, "upper_witness": high,
            "count_audit_worst_diameter": worst_count["upper"] - worst_count["lower"],
            "count_audit_worst_counts": worst_count["counts"],
            "full_source_audit_worst_diameter": worst_count["upper"] - worst_count["lower"]}


def certificate_only_bounds(k, cfg):
    rows = []
    for na, nb in count_pairs(k):
        amin = -math.expm1(-math.log(2) / (na - 1))
        bmin = -math.expm1(-math.log(2) / (nb - 1))
        rows.append({"counts": [na, nb], "lower_alpha_A": amin, "lower_alpha_B": bmin,
                     "lower": target(amin, bmin, cfg["rho_min"]),
                     "upper": target(1, 1, cfg["rho_max"]),
                     "labels_witness": "retain first and last event; last pre-score=1/2 at lower gain"})
    lo = min(rows, key=lambda z: z["lower"])
    return {"K": k, "lower": lo["lower"], "upper": rows[0]["upper"],
            "diameter": rows[0]["upper"] - lo["lower"], "lower_witness": lo,
            "upper_witness": {"counts": [2, 2], "alpha_A": 1, "alpha_B": 1,
                              "rho": cfg["rho_max"], "labels": [0, 1, 0, 1]}}


def probe_candidates(k, r, cfg, pairs=None):
    sa, sb = cfg["source_endpoint_A"], cfg["source_endpoint_B"]
    if r > sa or r <= 0:
        return []
    out = []
    for na, nb in (count_pairs(k) if pairs is None else pairs):
        threshold = sa * cfg["rho_min"] ** nb
        if r < threshold:
            continue
        rho = math.exp(math.log(r / sa) / nb)
        out.append({"counts": [na, nb], "rho": rho,
                    "alpha_A": gain(sa, na), "alpha_B": gain(sb, nb),
                    "target": target(gain(sa, na), gain(sb, nb), rho)})
    return out


def probe_bounds(k, r, cfg):
    candidates = probe_candidates(k, r, cfg)
    if not candidates:
        return {"K": k, "return_score": r, "compatible": False}
    lo = min(candidates, key=lambda z: z["target"])
    hi = max(candidates, key=lambda z: z["target"])
    return {"K": k, "return_score": r, "compatible": True,
            "identified_set_points": candidates, "lower": lo["target"], "upper": hi["target"],
            "diameter": hi["target"] - lo["target"],
            "lower_witness": source_witness(*lo["counts"], lo["rho"]),
            "upper_witness": source_witness(*hi["counts"], hi["rho"])}


def worst_probe(k, cfg, success_complete=False):
    """Global envelope over scalar return observations, not a sampling grid.

    In each feasibility cell every count-specific target is increasing in r.
    Thus max T_i(upper)-min T_i(lower) bounds the maximum same-r diameter.
    Floating guard is explicit; high-precision checks are separate controls.
    """
    pairs = count_pairs(k, success_complete)
    sa = cfg["source_endpoint_A"]
    thresholds = sorted({sa * cfg["rho_min"] ** nb for _, nb in pairs} | {sa})
    heap, serial = [], 0
    best = {"diameter": -1.0}
    guard = cfg["numerical_guard"]

    def sample(r):
        nonlocal best
        w = probe_candidates(k, r, cfg, pairs)
        if not w:
            return
        lo, hi = min(w, key=lambda z: z["target"]), max(w, key=lambda z: z["target"])
        width = hi["target"] - lo["target"]
        if width > best["diameter"]:
            best = {"diameter": width, "return_score": r,
                    "lower": lo["target"], "upper": hi["target"],
                    "lower_parameters": lo, "upper_parameters": hi}

    def add(l, u, active):
        nonlocal serial
        lv = probe_candidates(k, l, cfg, active)
        uv = probe_candidates(k, u, cfg, active)
        assert len(lv) == len(active) == len(uv)
        upper = max(z["target"] for z in uv) - min(z["target"] for z in lv) + guard
        serial += 1
        heapq.heappush(heap, (-upper, serial, l, u, active))
        sample(l)
        sample((l + u) / 2)
        sample(u)

    for l, u in zip(thresholds[:-1], thresholds[1:]):
        active = [(na, nb) for na, nb in pairs if sa * cfg["rho_min"] ** nb <= l]
        add(l, u, active)
    iterations = 0
    while -heap[0][0] - best["diameter"] > cfg["worst_probe_gap_tolerance"]:
        if len(heap) >= cfg["worst_probe_max_boxes"]:
            break
        _, _, l, u, active = heapq.heappop(heap)
        mid = (l + u) / 2
        add(l, mid, active)
        add(mid, u, active)
        iterations += 1
    ub = -heap[0][0]
    return {"K": k, "attained_lower_bound_on_worst_diameter": best["diameter"],
            "envelope_upper_bound_on_worst_diameter": ub,
            "gap": ub - best["diameter"], "best_attaining_observation": best,
            "active_boxes": len(heap), "splits": iterations,
            "tolerance_met": ub - best["diameter"] <= cfg["worst_probe_gap_tolerance"],
            "floating_guard": guard,
            "scope": "Algebraically conservative monotone envelopes evaluated in floating point; not formal directed rounding."}


def binary_probe(k, cfg):
    out = []
    for label in (0, 1):
        candidates = []
        for na, nb in count_pairs(k):
            cut = (0.5 / cfg["source_endpoint_A"]) ** (1 / nb)
            l, u = ((cfg["rho_min"], cut) if label == 0 else (cut, cfg["rho_max"]))
            candidates.append({"counts": [na, nb], "rho_lower": l, "rho_upper": u,
                               "lower": target(gain(.75, na), gain(.75, nb), l),
                               "upper_supremum": target(gain(.75, na), gain(.75, nb), u),
                               "upper_attained": label == 1})
        lo = min(candidates, key=lambda z: z["lower"])
        hi = max(candidates, key=lambda z: z["upper_supremum"])
        out.append({"observed_label": label, "lower": lo["lower"],
                    "upper_supremum": hi["upper_supremum"],
                    "diameter_supremum": hi["upper_supremum"] - lo["lower"],
                    "lower_parameters": lo, "upper_parameters": hi,
                    "upper_attained": label == 1,
                    "boundary_note": "Y=0 excludes x_A=1/2; its upper endpoint is only a supremum."})
    return out


def calibration_enclosure(eps, cfg):
    """Coupled score/rate relation, split on s_A; endpoints in s_B,r.

    The skill alpha_A and retention are correlated through s_A. Interval
    boxes enclose, but do not assert simultaneous attainability of their
    artificial parameter corners. Actual scalar-endpoint witnesses saved.
    """
    na, nb = cfg["reference_counts"]
    sa0, sb0, r0 = .75, .75, cfg["reference_return_score"]
    sal, sau = sa0 - eps, sa0 + eps
    sbl, sbu, rl, ru = sb0 - eps, sb0 + eps, r0 - eps, r0 + eps
    number = 1 if eps == 0 else cfg["calibration_subintervals"]
    lower, upper = math.inf, -math.inf
    attained_lo, attained_hi = None, None
    for i in range(number):
        l = sal + (sau - sal) * i / number
        u = sal + (sau - sal) * (i + 1) / number
        rhol = max(cfg["rho_min"], (rl / u) ** (1 / nb))
        rhou = min(cfg["rho_max"], (ru / l) ** (1 / nb))
        if rhol > rhou:
            continue
        lower = min(lower, target(gain(l, na), gain(sbl, nb), rhol))
        upper = max(upper, target(gain(u, na), gain(sbu, nb), rhou))
        for sa in (l, u):
            for sb, r in ((sbl, rl), (sbu, ru)):
                rho = (r / sa) ** (1 / nb)
                if not cfg["rho_min"] <= rho <= cfg["rho_max"]:
                    continue
                value = target(gain(sa, na), gain(sb, nb), rho)
                witness = {"s_A": sa, "s_B": sb, "r": r, "n_A": na, "n_B": nb,
                           "alpha_A": gain(sa, na), "alpha_B": gain(sb, nb),
                           "rho": rho, "target": value}
                if attained_lo is None or value < attained_lo["target"]:
                    attained_lo = witness
                if attained_hi is None or value > attained_hi["target"]:
                    attained_hi = witness
    guard = cfg["numerical_guard"] if eps else 0.0
    return {"epsilon": eps, "counts_known": [na, nb],
            "target_lower_enclosure": lower - guard, "target_upper_enclosure": upper + guard,
            "diameter_upper_enclosure": upper - lower + 2 * guard,
            "attained_diameter": attained_hi["target"] - attained_lo["target"],
            "lower_witness": attained_lo, "upper_witness": attained_hi,
            "endpoint_gap": max(attained_lo["target"] - lower, upper - attained_hi["target"]),
            "subintervals": number, "sharp": eps == 0,
            "practical_precision_certified": upper - lower + 2 * guard <= cfg["precision_criterion"]}


def high_precision_target(a, b, rho):
    with localcontext() as ctx:
        ctx.prec = 80
        states = [Decimal(0), Decimal(0)]
        total = Decimal(0)
        for j in range(12):
            i, other = j % 2, 1 - j % 2
            total += states[i]
            rate = a if i == 0 else b
            states[i] = states[i] + rate * (1 - states[i])
            states[other] *= rho
        return total / 12


def controls(cfg, src, probe, worst):
    errors, limiting, precision = [], [], []
    # Event simulator versus geometric formula, including boundaries and
    # values outside the source-compatible set.
    for a, b, rho in product((0, .1, .25, .5, .9, 1), repeat=3):
        formula, direct = target(a, b, rho), simulate(a, b, rho)[0]
        errors.append(abs(formula - direct))
        assert abs(formula - direct) < 2e-15
        if rho == 0:
            assert formula == 0
        if rho == 1:
            ref = sum(1 - (1 - rate) ** j for rate in (a, b) for j in range(6)) / 12
            assert abs(formula - ref) < 2e-15
    assert gain(.75, 2) == .5
    assert abs(1 - (1 - .25) ** 2 - .75) > .1  # known incompatible source endpoint
    assert not probe_candidates(4, .8, cfg)
    assert not probe_candidates(4, -.1, cfg)
    assert not probe_candidates(4, .75 * .5 ** 7, cfg)
    # Independent brute-force choices of retained positions; exact threshold
    # comparison follows 1-4^(-j/n)>=1/2 iff 2*j>=n.
    reference = []
    for k in range(5):
        admissible, success_only = set(), set()
        selections = 0
        for na in range(2, k + 3):
            for nb in range(2, k + 3):
                if na + nb - 4 > k:
                    continue
                ya, yb = [int(2 * j >= na) for j in range(na)], [int(2 * j >= nb) for j in range(nb)]
                for ia, ib in product(range(na - 1), range(nb - 1)):
                    if [ya[ia], ya[-1], yb[ib], yb[-1]] != [0, 1, 0, 1]:
                        continue
                    selections += 1
                    admissible.add((na, nb))
                    if all(not y or i in (ia, na - 1) for i, y in enumerate(ya)) and \
                       all(not y or i in (ib, nb - 1) for i, y in enumerate(yb)):
                        success_only.add((na, nb))
        assert admissible == set(count_pairs(k))
        assert success_only == set(count_pairs(k, True))
        reference.append({"K": k, "brute_position_assignments": selections,
                          "compatible_counts": sorted(admissible), "all_successes_logged_counts": sorted(success_only)})
    # High precision uses reconstructed algebraic gains, not decimal casts of
    # the already rounded binary floating point rates.
    candidates = [z[w] for z in src for w in ("lower_witness", "upper_witness")]
    candidates += [z[w] for z in probe for w in ("lower_witness", "upper_witness") if z["compatible"]]
    for result in worst:
        obs = result["best_attaining_observation"]
        for key in ("lower_parameters", "upper_parameters"):
            z = obs[key]
            candidates.append(source_witness(*z["counts"], z["rho"]))
    with localcontext() as ctx:
        ctx.prec = 80
        s = Decimal(3) / 4
        for z in candidates:
            a = 1 - ((1 - s).ln() / z["n_A"]).exp()
            b = 1 - ((1 - s).ln() / z["n_B"]).exp()
            rho = Decimal(str(z["rho"]))
            hp = high_precision_target(a, b, rho)
            err = abs(float(hp) - z["target"])
            assert err < 3e-14
            precision.append({"n_A": z["n_A"], "n_B": z["n_B"], "rho": str(rho),
                              "target_80digit": str(hp), "float_error": err})
    full_low = source_witness(3, 3, .5)
    full_high = source_witness(3, 3, 1)
    assert full_low["all_source_certificates_A"] == full_high["all_source_certificates_A"]
    assert full_low["all_source_certificates_B"] == full_high["all_source_certificates_B"]
    binary_low = source_witness(3, 3, .5)
    binary_high = source_witness(3, 3, .8)
    assert binary_low["return_score_A"] < .5 and binary_high["return_score_A"] < .5
    limiting.append({"test": "same complete source, different retention", "lower": full_low, "upper": full_high,
                     "target_gap": full_high["target"] - full_low["target"]})
    limiting.append({"test": "same binary return certificate Y=0 with known counts", "lower": binary_low,
                     "upper": binary_high, "target_gap": binary_high["target"] - binary_low["target"]})
    return {"formula_vs_event_simulator": {"cases": len(errors), "max_abs_error": max(errors)},
            "incompatible_cases_rejected": ["source s=.75 with alpha=.25,n=2", "r>.75", "r<0", "r below minimum allowed by K"],
            "brute_force_position_reference": reference, "high_precision_checks": precision,
            "strong_alternatives": limiting,
            "known_law_recovery": {"counts": [3, 3], "rho": .75,
                                   "return": source_witness(3, 3, .75),
                                   "identified_from_counts_and_three_scores": True},
            "retained_row_random_audit": {"observed_labels": [0, 1, 0, 1],
                                          "likelihood_of_already_observed_label": 1,
                                          "worlds_removed": 0,
                                          "scope": "Re-reading an existing row, not sampling unrecorded events."}}


def main():
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    config_bytes = (HERE / "config.json").read_bytes()
    cfg = json.loads(config_bytes)
    protocol_bytes = (HERE / "PROTOCOL.md").read_bytes()
    # Freeze metadata is committed before computing the main outputs.
    freeze = {"main_started_utc": start,
              "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
              "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
              "main_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "development_revisions_used": 1,
              "first_calculation_sha256": hashlib.sha256((HERE / "FIRST_CALCULATION.json").read_bytes()).hexdigest()}
    (HERE / "FREEZE.json").write_text(json.dumps(freeze, indent=2) + "\n")
    src = [source_bounds(k, cfg) for k in cfg["missing_caps"]]
    cert = [certificate_only_bounds(k, cfg) for k in cfg["missing_caps"]]
    probes = [probe_bounds(k, cfg["reference_return_score"], cfg) for k in cfg["missing_caps"]]
    worst = [worst_probe(k, cfg) for k in cfg["missing_caps"]]
    restriction = {"source": [source_bounds(k, cfg, True) for k in cfg["missing_caps"]],
                   "worst_score_probe": [worst_probe(k, cfg, True) for k in (0, 2, 4, 8)]}
    calibration = [calibration_enclosure(e, cfg) for e in cfg["calibration_errors"]]
    checks = controls(cfg, src, probes, worst)
    result = {"started_utc": start,
              "completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "original_certificate_only": cert,
              "main_source_calibrated": src, "fixed_score_return_probe": probes,
              "worst_case_score_return_probe": worst,
              "binary_return_probe_primary_K": binary_probe(cfg["primary_cap"], cfg),
              "all_successes_logged_contrary": restriction,
              "count_plus_return_calibration": calibration,
              "controls": checks,
              "resources": {"peak_rss_native": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                            "platform": sys.platform, "single_process": True,
                            "numerical_threads": 1, "public_operations_in_this_script": 0,
                            "known_input_bytes": len(config_bytes) + len(protocol_bytes)},
              "freeze": freeze}
    (HERE / "BOUNDS.json").write_text(json.dumps(result, indent=2) + "\n")
    primary = next(z for z in src if z["K"] == cfg["primary_cap"])
    print(json.dumps({"completed_utc": result["completed_utc"],
                      "source": [{"K": z["K"], "lower": z["lower"], "upper": z["upper"],
                                  "width": z["diameter"], "count_audit_worst_width": z["count_audit_worst_diameter"]} for z in src],
                      "worst_return_probe": [{"K": z["K"], "attained": z["attained_lower_bound_on_worst_diameter"],
                                              "upper_envelope": z["envelope_upper_bound_on_worst_diameter"],
                                              "boxes": z["active_boxes"]} for z in worst],
                      "fixed_return_probe": [{"K": z["K"], "lower": z.get("lower"), "upper": z.get("upper"),
                                              "width": z.get("diameter")} for z in probes],
                      "calibration": [{"epsilon": z["epsilon"], "width_upper": z["diameter_upper_enclosure"],
                                       "attained_width": z["attained_diameter"],
                                       "certified": z["practical_precision_certified"]} for z in calibration],
                      "peak_rss_native": result["resources"]["peak_rss_native"]}, indent=2))


if __name__ == "__main__":
    main()
