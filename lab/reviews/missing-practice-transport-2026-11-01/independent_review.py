"""Independent protocol-derived calculations; standard library only, one process/thread.

No imports or execution of the author's code. Binary source certificates are read
before each teaching update. Two independent endpoint probes are additional data.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import math
import resource
import sys
import hashlib
from itertools import combinations
from decimal import Decimal, localcontext

SOURCE_DIR = Path(__file__).resolve().parent
AUTHOR = SOURCE_DIR.parent.parent / "tasks" / "missing-practice-transport-2026-11-01"
# Optional third argument sends generated outputs to an existing fresh owned
# directory, while all original evidence remains read-only.
ROOT = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else SOURCE_DIR


def peak_rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value*1024


def event_step(state, action, gain_a, gain_b, retention):
    own = 0 if action == "A" else 1
    other = 1 - own
    pre = state[own]
    new = list(state)
    new[own] = pre + (gain_a if own == 0 else gain_b) * (1 - pre)
    new[other] *= retention
    return tuple(new), pre


def target_events(gain_a, gain_b, retention):
    state = (0.0, 0.0)
    scores = []
    for action in "AB" * 6:
        state, pre = event_step(state, action, gain_a, gain_b, retention)
        scores.append(pre)
    return math.fsum(scores) / 12, scores


def endpoint_gain(count, score=0.75):
    return -math.expm1(math.log1p(-score) / count)


def source_events(count_a, count_b, retention, score_a=0.75, score_b=0.75):
    aa, ab = endpoint_gain(count_a, score_a), endpoint_gain(count_b, score_b)
    state = (0.0, 0.0)
    certs = {"A": [], "B": []}
    endpoints = {}
    for action, count in (("A", count_a), ("B", count_b)):
        for _ in range(count):
            state, pre = event_step(state, action, aa, ab, retention)
            # Preserve scores and explicit inclusion at the 1/2 boundary.
            certs[action].append({"pre": pre, "Y": int(pre >= 0.5 - 1e-15)})
        endpoints[action] = state[0 if action == "A" else 1]
    return {"gains": [aa, ab], "certificates": certs, "block_endpoints": endpoints,
            "return_A": state[0], "retained_positions": {"A": [1, count_a], "B": [1, count_b]},
            "retained_certificates": {k: [v[0]["Y"], v[-1]["Y"]] for k, v in certs.items()},
            "omitted_total": count_a + count_b - 4}


def first_calculation():
    rstar = 81 / 256
    worlds = []
    for na, nb in ((2, 2), (3, 3)):
        rho = (rstar / 0.75) ** (1 / nb)
        src = source_events(na, nb, rho)
        target, trace = target_events(*src["gains"], rho)
        worlds.append({"counts": [na, nb], "rho": rho, "source": src,
                       "target_mean_preupdate": target, "target_trace": trace})
    result = {"generated_utc": datetime.now(timezone.utc).isoformat(),
              "basis": "Independent event recurrence constructed from PROTOCOL, before author numerical code/proofs/results.",
              "rstar": rstar, "K": 2, "worlds": worlds,
              "same_observation": all(w["source"]["retained_certificates"] == {"A": [0, 1], "B": [0, 1]}
                                      and abs(w["source"]["return_A"] - rstar) < 1e-14
                                      and max(abs(v - .75) for v in w["source"]["block_endpoints"].values()) < 1e-14
                                      for w in worlds),
              "target_gap": abs(worlds[0]["target_mean_preupdate"] - worlds[1]["target_mean_preupdate"]),
              "limitations": "Finite attained witness, not a sharp or worst-outcome bound. 1e-15 certificate guard solely handles representation of exact n=2 equality; not directed interval certification.",
              "process_maxrss_bytes": peak_rss_bytes()}
    assert result["same_observation"]
    (ROOT / "FIRST_CALCULATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("generated_utc", "same_observation", "target_gap", "process_maxrss_bytes")}))


def count_pairs(k, success_complete=False):
    return [(a, b) for a in range(2, k + 3) for b in range(2, k + 5 - a)
            if not success_complete or (a <= 3 and b <= 3)]


def coefficients(counts):
    gains = [endpoint_gain(n) for n in counts]
    # Summing pre-update task appearances j=0,...,5 first, each rho^k
    # occurs 6-k times. This is independently derived from the event loop.
    return [(6-k) * math.fsum(a * (1-a)**(k-1) for a in gains) / 12 for k in range(1, 6)]


def polynomial_target(counts, rho):
    return math.fsum(c * rho**k for k, c in enumerate(coefficients(counts), 1))


def at_return(counts, r):
    rho = (r / .75) ** (1 / counts[1])
    return polynomial_target(counts, rho)


def sparse_value(terms, x):
    return math.fsum(c*x**e for e, c in terms)


def sparse_roots(terms, lower, upper):
    """All candidate positive roots via Rolle/monotone intervals in exact arithmetic.

    Strip the least positive power (it has no zeros here); the derivative then
    has one fewer nonzero term. Recurse, then bisect sign changes between all
    derivative roots. Floating evaluations get checked separately; this is not
    directed rounding or a formally certified polynomial root isolator.
    """
    terms = sorted((e, c) for e, c in terms if c != 0)
    if len(terms) <= 1 or all(c > 0 for e, c in terms) or all(c < 0 for e, c in terms):
        return []
    shift = terms[0][0]
    terms = [(e-shift, c) for e, c in terms]
    derivative = [(e-1, e*c) for e, c in terms if e]
    critical = sparse_roots(derivative, lower, upper)
    boundaries = [lower] + critical + [upper]
    roots = []
    for x in boundaries:
        fx = sparse_value(terms, x)
        scale = math.fsum(abs(c*x**e) for e, c in terms)
        if abs(fx) <= 2e-14 * max(scale, 1e-8):
            roots.append(x)
    for left, right in zip(boundaries, boundaries[1:]):
        fl, fr = sparse_value(terms, left), sparse_value(terms, right)
        if fl*fr < 0:
            for _ in range(70):
                mid = (left+right)/2
                fm = sparse_value(terms, mid)
                if fl*fm <= 0:
                    right = mid
                else:
                    left, fl = mid, fm
            roots.append((left+right)/2)
    return sorted(set(round(x, 15) for x in roots if lower <= x <= upper))


def worst_exact_return(k, success_complete=False):
    counts = count_pairs(k, success_complete)
    best = {"diameter": 0.0}
    pair_records = []
    for a, b in combinations(counts, 2):
        common = math.lcm(a[1], b[1])
        coeff = {}
        for sign, pair in ((1, a), (-1, b)):
            power = common // pair[1]
            for j, c in enumerate(coefficients(pair), 1):
                coeff[power*j] = coeff.get(power*j, 0) + sign*c
        deriv = [(e-1, e*c) for e, c in coeff.items() if c]
        rlo = max(.75*.5**a[1], .75*.5**b[1])
        qlo = (rlo/.75)**(1/common)
        critical = sparse_roots(deriv, qlo, 1.0)
        candidates = [rlo, .75] + [.75*q**common for q in critical]
        chosen = max(candidates, key=lambda r: abs(at_return(a, r)-at_return(b, r)))
        ta, tb = at_return(a, chosen), at_return(b, chosen)
        record = {"counts_a": a, "counts_b": b, "return": chosen,
                  "targets": [ta, tb], "gap": abs(ta-tb), "stationary_candidates": len(critical)}
        pair_records.append(record)
        if record["gap"] > best["diameter"]:
            best = {"diameter": record["gap"], **record}
    if len(counts) == 1:
        best = {"diameter": 0, "algebraic": "Only counts (2,2); return determines rho uniquely."}
    # Separate observation grid, with all exact feasibility thresholds included.
    rmin = min(.75*.5**p[1] for p in counts)
    observations = sorted(set([rmin+(.75-rmin)*j/2000 for j in range(2001)]
                              + [.75*.5**p[1] for p in counts]))
    grid_max = 0
    for r in observations:
        vals = [at_return(p, r) for p in counts if r >= .75*.5**p[1]]
        grid_max = max(grid_max, max(vals)-min(vals))
    return {"K": k, "success_complete": success_complete, "count_pairs": counts,
            "worst_candidate": best, "all_pair_extrema": pair_records,
            "observation_grid_max": grid_max, "grid_size": len(observations),
            "global_method": "Each pair difference is a sparse polynomial in (r/.75)^(1/lcm(nB1,nB2)); endpoint + derivative-root recursion. Numerical, not formal directed rounding."}


def decimal_target(counts, r=None, rho=None):
    with localcontext() as ctx:
        ctx.prec = 80
        gains = [Decimal(1) - (Decimal('.25').ln()/Decimal(n)).exp() for n in counts]
        rr = Decimal(str(rho)) if rho is not None else (Decimal(str(r)) / Decimal('.75')).ln()
        if rho is None:
            rr = (rr / Decimal(counts[1])).exp()
        out = Decimal(0)
        for aa in gains:
            state = Decimal(0)
            for _ in range(6):
                out += state
                state = rr*(aa+(1-aa)*state)
        return str(out/Decimal(12))


def binary_probe_bounds(k):
    out = []
    for label in (0, 1):
        vals = []
        for pair in count_pairs(k):
            boundary = (2/3)**(1/pair[1])
            low, high = ((.5, boundary) if label == 0 else (boundary, 1))
            vals.append({"counts": pair, "lower": polynomial_target(pair, low),
                         "upper": polynomial_target(pair, high), "upper_attained": label == 1})
        out.append({"label": label, "lower": min(v["lower"] for v in vals),
                    "upper": max(v["upper"] for v in vals),
                    "diameter": max(v["upper"] for v in vals)-min(v["lower"] for v in vals),
                    "upper_is_supremum": label == 0, "partitions": vals})
    return out


def independent_main():
    result = {"generated_utc": datetime.now(timezone.utc).isoformat(), "class": "Protocol shared-retention model",
              "source_bounds": [], "exact_return": []}
    max_sim_error = 0
    cert_cases = 0
    for k in (0, 1, 2, 3, 4, 8):
        pairs = count_pairs(k)
        source_low, source_high = 1, 0
        certificate_low, certificate_high = 1, 0
        audit_max = 0
        for pair in pairs:
            gains = [endpoint_gain(n) for n in pair]
            tlo = polynomial_target(pair, .5)
            thi = polynomial_target(pair, 1)
            source_low, source_high = min(source_low, tlo), max(source_high, thi)
            certificate_gains = [1 - .5**(1/(n-1)) for n in pair]
            certificate_low = min(certificate_low, target_events(*certificate_gains, .5)[0])
            certificate_high = max(certificate_high, target_events(1, 1, 1)[0])
            audit_max = max(audit_max, thi-tlo)
            for rho in (.5, .63, .75, 1):
                simulated = target_events(*gains, rho)[0]
                max_sim_error = max(max_sim_error, abs(simulated - polynomial_target(pair, rho)))
            # Integer certificate formula avoids incorrectly resolving equality numerically.
            for n in pair:
                labels = [int(2*j >= n) for j in range(n)]
                assert labels[0] == 0 and labels[-1] == 1
                valid_positions = [(i+1, n) for i in range(n-1) if labels[i] == 0]
                assert valid_positions
                if sum(labels) == 1:
                    assert n in (2, 3)
                else:
                    assert n >= 4
                cert_cases += 1
        result["source_bounds"].append({"K": k, "calibrated": [source_low, source_high],
                     "certificate_only": [certificate_low, certificate_high], "worst_after_count_audit": audit_max})
        result["exact_return"].append(worst_exact_return(k))
    result["success_complete_K4"] = worst_exact_return(4, True)
    rstar = 81/256
    fixed = [{"counts": p, "rho": (rstar/.75)**(1/p[1]), "target": at_return(p, rstar)}
             for p in count_pairs(4) if rstar >= .75*.5**p[1]]
    result["fixed_return_K4"] = {"return": rstar, "points": fixed,
                                 "diameter": max(v["target"] for v in fixed)-min(v["target"] for v in fixed)}
    result["binary_return_K4"] = binary_probe_bounds(4)
    result["formula_event_max_abs_error"] = max_sim_error
    result["certificate_count_cases"] = cert_cases
    # Reconstruct maximizing witnesses by the independent event simulator, then compare high precision.
    extrema_checks = []
    for case in result["exact_return"][1:] + [result["success_complete_K4"]]:
        best = case["worst_candidate"]
        witnesses = []
        for pair in (best["counts_a"], best["counts_b"]):
            rho = (best["return"]/.75)**(1/pair[1])
            src = source_events(*pair, rho)
            event_t = target_events(*src["gains"], rho)[0]
            d_t = decimal_target(pair, r=best["return"])
            assert .5 - 1e-12 <= rho <= 1 + 1e-12
            assert src["omitted_total"] <= case["K"]
            assert abs(event_t-float(d_t)) < 2e-14
            witnesses.append({"counts": pair, "rho": rho, "source": src,
                              "target_event": event_t, "target_decimal80": d_t})
        extrema_checks.append({"K": case["K"], "success_complete": case["success_complete"],
                                "return": best["return"], "witnesses": witnesses})
    result["extremum_witness_checks"] = extrema_checks
    result["process_maxrss_bytes"] = peak_rss_bytes()
    (ROOT / "INDEPENDENT_BOUNDS.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"worst": [{"K": c["K"], "diameter": c["worst_candidate"]["diameter"],
                 "return": c["worst_candidate"].get("return")} for c in result["exact_return"]],
                 "success_complete_K4": result["success_complete_K4"]["worst_candidate"],
                 "formula_event_error": max_sim_error, "maxrss": result["process_maxrss_bytes"]}))


def contrary():
    step = .05
    counts = count_pairs(1)
    bins = []
    for integer in range(16):
        center = integer * step
        lo, hi = center - step/2, center + step/2
        pieces = []
        for pair in counts:
            low = max(lo, .75*.5**pair[1])
            high = min(hi, .75)
            high_attained = high == .75 and .75 < hi
            if low < high or (low == high and high_attained):
                pieces.append({"counts": pair, "r_lower": low, "r_upper": high,
                               "lower_target": at_return(pair, low), "upper_target": at_return(pair, high),
                               "upper_attained": high_attained})
        if pieces:
            lower = min(pieces, key=lambda p: p["lower_target"])
            upper = max(pieces, key=lambda p: p["upper_target"])
            bins.append({"displayed_score": center, "pieces": pieces, "lower": lower, "upper": upper,
                         "diameter_supremum": upper["upper_target"]-lower["lower_target"]})
    worst = max(bins, key=lambda b: b["diameter_supremum"])
    witnesses = []
    for label, piece in (("low", worst["lower"]), ("high", worst["upper"])):
        r = piece["r_lower"] + 1e-6 if label == "low" else piece["r_upper"] - 1e-6
        pair = piece["counts"]
        rho = (r/.75)**(1/pair[1])
        src = source_events(*pair, rho)
        target, trace = target_events(*src["gains"], rho)
        display = step * math.floor(src["return_A"] / step + .5)
        witnesses.append({"counts": pair, "rho": rho, "source": src, "true_return": r,
                          "displayed_return": display, "target": target, "target_trace": trace})
    gap = abs(witnesses[1]["target"]-witnesses[0]["target"])
    assert abs(witnesses[0]["displayed_return"]-witnesses[1]["displayed_return"]) < 1e-12
    assert all(w["source"]["retained_certificates"] == {"A": [0, 1], "B": [0, 1]} for w in witnesses)
    out = {"generated_utc": datetime.now(timezone.utc).isoformat(),
           "plan_sha256": hashlib.sha256((SOURCE_DIR/"CONTRARY_PLAN.md").read_bytes()).hexdigest(),
           "change": "Return score rounded to nearest .05; endpoints still exact .75; K1 and all dynamics unchanged.",
           "bins": bins, "worst_bin": worst, "attained_witnesses": witnesses, "attained_gap": gap,
           "passes_point10": worst["diameter_supremum"] <= .1,
           "classification": "Prespecified coarser observation boundary, not a contradiction in the frozen exact-score class.",
           "process_maxrss_bytes": peak_rss_bytes()}
    output_path = ROOT/"CONTRARY.json"
    initial_path = ROOT/"CONTRARY_INITIAL.json"
    if output_path.exists() and not initial_path.exists():
        initial_path.write_bytes(output_path.read_bytes())
    output_path.write_text(json.dumps(out, indent=2)+"\n")
    print(json.dumps({"worst_display": worst["displayed_score"], "diameter_supremum": worst["diameter_supremum"],
                      "attained_gap": gap, "passes_point10": out["passes_point10"], "maxrss": out["process_maxrss_bytes"]}))


def directional_step(state, action, aa, ab, rho_a, rho_b):
    own = int(action == "B")
    other = 1-own
    before = state[own]
    new = list(state)
    new[own] += (ab if own else aa)*(1-before)
    new[other] *= (rho_b if other else rho_a)
    return tuple(new), before


def directional_audit():
    gain_a = gain_b = endpoint_gain(3)
    worlds = []
    for rho_b in (.5, 1):
        state = (0.0, 0.0)
        source_trace = []
        for j, action in enumerate("AAABBB"):
            state, pre = directional_step(state, action, gain_a, gain_b, .75, rho_b)
            source_trace.append(pre)
            if j == 2:
                endpoint_a = state[0]
        source_final = state
        after_extra_a, _ = directional_step(state, "A", gain_a, gain_b, .75, rho_b)
        q_b = after_extra_a[1]  # Read it without another teaching update.
        recovered_b = q_b/source_final[1]
        recovered_a = (source_final[0]/endpoint_a)**(1/3)
        target_state = (0., 0.)
        trace = []
        for action in "AB"*6:
            target_state, pre = directional_step(target_state, action, gain_a, gain_b, recovered_a, recovered_b)
            trace.append(pre)
        worlds.append({"rho_A": .75, "rho_B": rho_b, "complete_source_own_scores": source_trace,
                       "A_endpoint": endpoint_a, "source_final": source_final,
                       "extra_A_poststate": after_extra_a, "nonlearning_B_score": q_b,
                       "recovered_directions": [recovered_a, recovered_b],
                       "target_trace": trace, "target": math.fsum(trace)/12})
    assert worlds[0]["complete_source_own_scores"] == worlds[1]["complete_source_own_scores"]
    assert worlds[0]["source_final"] == worlds[1]["source_final"]
    return {"worlds": worlds, "same_complete_source_and_A_return": True,
            "target_gap": worlds[1]["target"] - worlds[0]["target"],
            "additional_probe_identifies_rho_B": True,
            "scope": "Only fixed, directional retentions and calibrated nonlearning scores. Not state-dependent retention or biological observation validation."}


def score_derivative(sa, sb, r):
    aa, ab = endpoint_gain(3, sa), endpoint_gain(3, sb)
    rho = (r/sa)**(1/3)
    partial_a = partial_rho = total = 0
    for i, a in enumerate((aa, ab)):
        z = da = dr = 0.
        for _ in range(6):
            total += z
            partial_rho += dr
            if i == 0:
                partial_a += da
            base = a+(1-a)*z
            da = rho*((1-z)+(1-a)*da)
            dr = base+rho*(1-a)*dr
            z = rho*base
    gradient = (partial_a/(3*(1-sa)**(2/3)) - partial_rho*rho/(3*sa))/12
    return total/12, gradient


def calibration_audit(epsilon):
    sa_lo, sa_hi = .75-epsilon, .75+epsilon
    r0 = 81/256
    results = []
    for sign in (-1, 1):
        sb, r = .75+sign*epsilon, r0+sign*epsilon
        candidates = [sa_lo, sa_hi]
        # Independently locate derivative sign changes, rather than assuming
        # source-gain and retention marginal corners are jointly feasible.
        for j in range(256):
            left = sa_lo+(sa_hi-sa_lo)*j/256
            right = sa_lo+(sa_hi-sa_lo)*(j+1)/256
            fl, fr = score_derivative(left, sb, r)[1], score_derivative(right, sb, r)[1]
            if fl*fr < 0:
                for _ in range(60):
                    mid = (left+right)/2
                    fm = score_derivative(mid, sb, r)[1]
                    if fl*fm <= 0:
                        right = mid
                    else:
                        left, fl = mid, fm
                candidates.append((left+right)/2)
        vals = [{"s_A": sa, "s_B": sb, "r": r, "rho": (r/sa)**(1/3),
                 "target": score_derivative(sa, sb, r)[0]} for sa in candidates]
        results.append(min(vals, key=lambda v: v["target"]) if sign < 0 else max(vals, key=lambda v: v["target"]))
    lower, upper = 1., 0.
    # Independent real-arithmetic monotone enclosure, with fewer/different
    # subdivisions than the author; not a simultaneous-parameter-corner claim.
    for j in range(2048):
        left = sa_lo+(sa_hi-sa_lo)*j/2048
        right = sa_lo+(sa_hi-sa_lo)*(j+1)/2048
        rho_lo = ((r0-epsilon)/right)**(1/3)
        rho_hi = ((r0+epsilon)/left)**(1/3)
        assert .5 <= rho_lo <= rho_hi <= 1
        lower = min(lower, target_events(endpoint_gain(3, left), endpoint_gain(3, .75-epsilon), rho_lo)[0])
        upper = max(upper, target_events(endpoint_gain(3, right), endpoint_gain(3, .75+epsilon), rho_hi)[0])
    # Certificate constraints continue to hold on these endpoint ranges.
    assert 1-(1-(.75-epsilon))**(2/3) > .5
    return {"epsilon": epsilon, "attained_lower": results[0], "attained_upper": results[1],
            "attained_diameter": results[1]["target"]-results[0]["target"],
            "independent_lower_enclosure": lower-1e-11, "independent_upper_enclosure": upper+1e-11,
            "independent_diameter_upper": upper-lower+2e-11,
            "subintervals": 2048, "sharp_claim": False}


def audit():
    read_bytes = 0

    def read(path):
        nonlocal read_bytes
        data = path.read_bytes()
        read_bytes += len(data)
        return data

    freeze = json.loads(read(AUTHOR/"FREEZE.json"))
    frozen_names = {"protocol_sha256": "PROTOCOL.md", "config_sha256": "config.json",
                    "main_code_sha256": "main.py", "first_calculation_sha256": "FIRST_CALCULATION.json"}
    pin_checks = []
    for key, name in frozen_names.items():
        digest = hashlib.sha256(read(AUTHOR/name)).hexdigest()
        pin_checks.append({"file": name, "matches_freeze": digest == freeze[key]})
    pins = json.loads(read(AUTHOR/"ARTIFACT_PINS.json"))
    for entry in pins["files"]:
        data = read(AUTHOR/entry["name"])
        pin_checks.append({"file": entry["name"], "matches_artifact_pin": hashlib.sha256(data).hexdigest() == entry["sha256"],
                           "matches_size": len(data) == entry["bytes"]})
    assert all(all(v for k, v in row.items() if k != "file") for row in pin_checks)
    author = json.loads(read(AUTHOR/"BOUNDS.json"))
    own = json.loads(read(ROOT/"INDEPENDENT_BOUNDS.json"))
    out = {"generated_utc": datetime.now(timezone.utc).isoformat(), "pin_checks": pin_checks}
    differences = []
    for own_row, src, cert, worst in zip(own["source_bounds"], author["main_source_calibrated"],
                                       author["original_certificate_only"], author["worst_case_score_return_probe"]):
        k = own_row["K"]
        numerical = next(c for c in own["exact_return"] if c["K"] == k)["worst_candidate"]["diameter"]
        diff = max(abs(own_row["calibrated"][0]-src["lower"]), abs(own_row["calibrated"][1]-src["upper"]),
                   abs(own_row["certificate_only"][0]-cert["lower"]), abs(own_row["certificate_only"][1]-cert["upper"]),
                   abs(own_row["worst_after_count_audit"]-src["count_audit_worst_diameter"]))
        assert diff < 1e-14
        assert worst["attained_lower_bound_on_worst_diameter"] - 2e-14 <= numerical <= worst["envelope_upper_bound_on_worst_diameter"] + 2e-14
        differences.append({"K": k, "source_max_difference": diff, "independent_worst": numerical,
                            "author_envelope": [worst["attained_lower_bound_on_worst_diameter"], worst["envelope_upper_bound_on_worst_diameter"]],
                            "author_tolerance_met": worst["tolerance_met"], "author_active_boxes": worst["active_boxes"]})
    out["bound_comparisons"] = differences
    out["calibration"] = [calibration_audit(e) for e in (.001, .002, .005, .01, .02, .04)]
    for row in out["calibration"]:
        other = next(z for z in author["count_plus_return_calibration"] if z["epsilon"] == row["epsilon"])
        assert other["target_lower_enclosure"] <= row["attained_lower"]["target"] <= row["attained_upper"]["target"] <= other["target_upper_enclosure"]
        assert row["independent_diameter_upper"] < .1
        row["author_diameter_upper"] = other["diameter_upper_enclosure"]
        row["author_attained_diameter"] = other["attained_diameter"]
    out["directional"] = directional_audit()
    # Limiting and incompatible cases independent of inherited author checks.
    out["limiting_controls"] = {"zero_retention_target": target_events(.4, .6, 0)[0],
                                "no_interference_error": max(abs(target_events(a, b, 1)[0] - math.fsum(1-(1-rate)**j for rate in (a,b) for j in range(6))/12)
                                    for a, b in ((.1, .9), (.5, .5), (1, 1)))}
    assert out["limiting_controls"]["zero_retention_target"] == 0
    out["feasibility_thresholds_K4"] = []
    for nb in range(2, 7):
        threshold = .75*.5**nb
        below = math.nextafter(threshold, 0)
        above = math.nextafter(threshold, 1)
        members = lambda r: [p for p in count_pairs(4) if r >= .75*.5**p[1]]
        out["feasibility_thresholds_K4"].append({"nB_entering": nb, "return": threshold,
                 "just_below": members(below), "at": members(threshold), "just_above": members(above)})
        assert any(p[1] == nb for p in members(threshold))
        assert not any(p[1] == nb for p in members(below))
    out["incompatible_returns_K4"] = [{"return": r, "feasible_counts": [p for p in count_pairs(4) if .75*.5**p[1] <= r <= .75]}
                                      for r in (-.1, 0, .75*.5**7, .8)]
    assert all(not row["feasible_counts"] for row in out["incompatible_returns_K4"])
    contrary_result = json.loads(read(ROOT/"CONTRARY.json"))
    out["contrary_check"] = {"gap": contrary_result["attained_gap"], "display": contrary_result["worst_bin"]["displayed_score"],
                             "counts": [w["counts"] for w in contrary_result["attained_witnesses"]],
                             "returns": [w["true_return"] for w in contrary_result["attained_witnesses"]],
                             "targets": [w["target"] for w in contrary_result["attained_witnesses"]]}
    out["exact_input_bytes_this_process"] = read_bytes
    out["process_maxrss_bytes"] = peak_rss_bytes()
    out["python_version"] = sys.version
    out["platform"] = sys.platform
    (ROOT/"AUDIT.json").write_text(json.dumps(out, indent=2)+"\n")
    print(json.dumps({"pin_checks": len(pin_checks), "max_source_difference": max(v["source_max_difference"] for v in differences),
                      "calibration_eps04": out["calibration"][-1], "directional_gap": out["directional"]["target_gap"],
                      "contrary": out["contrary_check"], "input_bytes": read_bytes, "maxrss": out["process_maxrss_bytes"]}))


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "first":
        first_calculation()
    elif sys.argv[1] == "main":
        independent_main()
    elif sys.argv[1] == "contrary":
        contrary()
    elif sys.argv[1] == "audit":
        audit()
