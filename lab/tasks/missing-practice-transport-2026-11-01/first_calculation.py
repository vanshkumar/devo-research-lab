"""Small exact compatibility calculation. Python standard library only."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import datetime
import json
import resource
import sys

HERE = Path(__file__).resolve().parent


def score_sequence(alpha, n):
    x = F(0)
    out = []
    for _ in range(n):
        out.append((x, int(x >= F(1, 2))))
        x = x + alpha * (1 - x)
    return out


def forecast(a, b, rho, schedule="AB" * 6):
    x = {"A": F(0), "B": F(0)}
    scores = []
    for task in schedule:
        other = "B" if task == "A" else "A"
        scores.append(x[task])
        gain = a if task == "A" else b
        x[task] += gain * (1 - x[task])
        x[other] *= rho
    return sum(scores) / len(scores)


def enumerate_worlds(k):
    worlds = []
    for a, b, rho in product((F(1, 4), F(1, 2)), (F(1, 4), F(1, 2)), (F(1, 2), F(1))):
        for na in range(2, k + 3):
            for nb in range(2, k + 3):
                if na + nb - 4 > k:
                    continue
                qa, qb = score_sequence(a, na), score_sequence(b, nb)
                # Last event in each block is retained; the other retained event
                # can be anywhere earlier. Observed binary labels are (0,1).
                if qa[-1][1] != 1 or qb[-1][1] != 1:
                    continue
                for ia, ib in product(range(na - 1), range(nb - 1)):
                    if qa[ia][1] or qb[ib][1]:
                        continue
                    worlds.append({"a": a, "b": b, "rho": rho,
                                   "na": na, "nb": nb, "logged_A": (ia + 1, na),
                                   "logged_B": (ib + 1, nb),
                                   "source_A": tuple(y for _, y in qa),
                                   "source_B": tuple(y for _, y in qb),
                                   "target": forecast(a, b, rho)})
    return worlds


def serial(v):
    if isinstance(v, F):
        return {"rational": str(v), "float": float(v)}
    if isinstance(v, dict):
        return {str(k): serial(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [serial(x) for x in v]
    return v


def main():
    results = []
    for k in range(5):
        w = enumerate_worlds(k)
        lo = min(w, key=lambda z: z["target"])
        hi = max(w, key=lambda z: z["target"])
        targets = sorted({z["target"] for z in w})
        types = {tuple(z[t] for t in ("a", "b", "rho")) for z in w}
        results.append({"max_missing": k, "worlds": len(w), "types": len(types),
                        "target_values": targets, "lower": lo["target"],
                        "upper": hi["target"], "diameter": hi["target"] - lo["target"],
                        "lower_witness": lo, "upper_witness": hi})
    # Independent closed-form check when rho=1: each task's nth score is
    # 1-(1-alpha)^n, regardless of the intervening other-task events.
    checks = []
    for a, b in product((F(1, 4), F(1, 2)), repeat=2):
        reference = sum(1 - (1 - gain) ** j for gain in (a, b) for j in range(6)) / 12
        actual = forecast(a, b, F(1))
        assert actual == reference
        checks.append({"a": a, "b": b, "actual": actual, "closed_form": reference})
    assert results[0]["types"] == 2
    assert results[2]["types"] == 6
    assert results[4]["types"] == 8
    out = {"completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "model": "two deterministic skill traces, pre-update certificate 1[x>=1/2]",
           "source_observation": {"tasks": "AABB", "labels": [0, 1, 0, 1],
                                  "block_ends_retained": True},
           "parameter_grid": {"alpha_A": ["1/4", "1/2"], "alpha_B": ["1/4", "1/2"],
                              "rho": ["1/2", "1"]},
           "target": "mean pre-update calibrated skill on fresh-state AB repeated 6 times",
           "recording": "unknown subsequence selector, may depend on outcomes; realized compatibility only",
           "results": results, "known_rho1_controls": checks,
           "resources": {"peak_rss_native": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                         "platform": sys.platform, "one_process": True, "numerical_threads": 1},
           "scope": "Exact finite class, no empirical or population uncertainty; not a likelihood analysis."}
    (HERE / "FIRST_CALCULATION.json").write_text(json.dumps(serial(out), indent=2) + "\n")
    print(json.dumps({"completed_utc": out["completed_utc"],
                      "bounds": [{"k": z["max_missing"], "types": z["types"],
                                  "lo": float(z["lower"]), "hi": float(z["upper"]),
                                  "width": float(z["diameter"])} for z in results],
                      "peak_rss_native": out["resources"]["peak_rss_native"]}, indent=2))


if __name__ == "__main__":
    main()
