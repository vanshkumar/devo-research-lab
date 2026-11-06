"""Finite check of standard sequential importance sampling and KL identities.

This is a constructed reference check, not a biological fit, novelty result,
or experiment on the consumed mouse/crossAct records. Python stdlib only.
"""

from fractions import Fraction as F
from itertools import product
from pathlib import Path
import datetime as dt
import hashlib
import json
import math
import resource
import sys


ROOT = Path(__file__).resolve().parent
HORIZON = 3  # two training responses, then one final (nonlearning) readout


def teacher(h):
    """Probability of action 1; only the observed previous response is used."""
    return F(1, 5) if not h else (F(3, 5) if h[-1][1] else F(1, 10))


def response(h, a, model):
    """The complete observed history determines a constructed skill state."""
    skill = F(1, 4)
    gains = (F(1, 5), F(1, 3)) if model == "P" else (F(1, 6), F(1, 4))
    decay = (F(1, 10), F(1, 8)) if model == "P" else (F(1, 9), F(1, 7))
    for old_a, old_y in h:
        if old_y:
            skill += gains[old_a] * (1 - skill)
        else:
            skill *= 1 - decay[old_a]
    return F(1, 5) + F(3, 5) * skill if a == 0 else skill


def enumerate_law(model, scheduled=False):
    law = {}
    for z in product((0, 1), repeat=2 * HORIZON):
        h = tuple(zip(z[::2], z[1::2]))
        mass = F(1)
        for t, (a, y) in enumerate(h):
            pa = F(1) if scheduled and t == HORIZON - 1 else teacher(h[:t])
            py = response(h[:t], a, model)
            mass *= (pa if a else 1 - pa) * (py if y else 1 - py)
        law[h] = mass
    assert sum(law.values()) == 1
    return law


def kl(p, q):
    return math.fsum(float(v) * math.log(float(v / q[h])) for h, v in p.items() if v)


def conditional_kl(model_p, model_q, h, a):
    p, q = response(h, a, model_p), response(h, a, model_q)
    return float(p) * math.log(float(p / q)) + float(1 - p) * math.log(float((1 - p) / (1 - q)))


def chain_kl(law):
    return math.fsum(float(v) * sum(conditional_kl("P", "Q", h[:t], a)
                                   for t, (a, _) in enumerate(h))
                     for h, v in law.items() if v)


def main():
    pb, qb = enumerate_law("P"), enumerate_law("Q")
    pp, qp = enumerate_law("P", True), enumerate_law("Q", True)
    weights = {h: F(h[-1][0], 1) / teacher(h[:-1]) for h in pb}
    assert all(weights[h] * pb[h] == pp[h] for h in pb)
    assert all(weights[h] * qb[h] == qp[h] for h in qb)
    weight_mean = sum(pb[h] * weights[h] for h in pb)
    assert weight_mean == 1
    true_probe = sum(pp[h] * h[-1][1] for h in pp)
    candidate_probe = sum(qp[h] * h[-1][1] for h in qp)
    is_probe = sum(pb[h] * weights[h] * h[-1][1] for h in pb)
    assert true_probe == is_probe
    db, dpi = kl(pb, qb), kl(pp, qp)
    cb, cpi = chain_kl(pb), chain_kl(pp)
    assert abs(db - cb) < 1e-14 and abs(dpi - cpi) < 1e-14
    c = max(weights.values())
    tv_probe = abs(float(true_probe - candidate_probe))
    tv_path = 0.5 * math.fsum(abs(float(pp[h] - qp[h])) for h in pp)
    assert dpi <= float(c) * db + 1e-14
    assert tv_probe <= tv_path + 1e-14
    assert tv_path <= math.sqrt(dpi / 2) + 1e-14
    assert kl(pb, pb) == 0.0 and kl(pp, pp) == 0.0
    source_bytes = Path(__file__).read_bytes()
    out = {
        "status": "PASS_STANDARD_REFERENCE_CHECK_NOT_NEW_THEOREM",
        "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "python": sys.version,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "assumptions": [
            "complete discrete observed history; same initial law",
            "known positive response-dependent teacher in both candidate worlds",
            "response kernels invariant to replacing terminal teacher action",
            "two ordinary training trials followed by a final probe",
            "no post-probe response is scored; its later learning is outside target",
            "exact rational path enumeration; floating natural logarithms only",
            "population KL is known here by construction, not estimated from data"
        ],
        "paths": len(pb),
        "positive_logging_paths": sum(v > 0 for v in pb.values()),
        "positive_target_paths": sum(v > 0 for v in pp.values()),
        "minimum_logging_probability_of_probe_action": "1/10",
        "max_target_to_logging_trajectory_ratio": str(c),
        "importance_weight_mean_exact": str(weight_mean),
        "true_probe_mean_exact": str(true_probe),
        "candidate_probe_mean_exact": str(candidate_probe),
        "importance_weighted_probe_mean_exact": str(is_probe),
        "true_probe_mean": float(true_probe),
        "candidate_probe_mean": float(candidate_probe),
        "probe_mean_absolute_error": tv_probe,
        "logging_trajectory_KL": db,
        "logging_chain_KL": cb,
        "scheduled_trajectory_KL": dpi,
        "scheduled_chain_KL": cpi,
        "C_times_logging_KL": float(c) * db,
        "scheduled_path_TV": tv_path,
        "pinsker_direct_bound": math.sqrt(dpi / 2),
        "standard_overlap_KL_probe_bound": min(1.0, math.sqrt(float(c) * db / 2)),
        "five_percentage_point_sufficient_logging_KL_for_C10": 2 * 0.05**2 / float(c),
        "zero_model_error_control_KL": 0.0,
        "read_bytes_explicit_source_hash": len(source_bytes),
        "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "physical_IO_runtime_reads": "unknown",
        "scientific_processes": 1,
        "numerical_threads": 1,
        "warnings": [],
        "empirical_records_read": 0,
        "novelty_claim": False,
    }
    target = ROOT / "FIRST_CALCULATION.json"
    target.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
