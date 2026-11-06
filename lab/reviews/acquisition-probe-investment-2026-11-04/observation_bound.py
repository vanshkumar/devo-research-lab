"""Read only derived terminal forecasts and calculate a binary-KL test bound."""

import hashlib
import io
import itertools
import json
import math
import resource
import sys
import time
from pathlib import Path

import numpy as np


ALPHA = 0.05
N = 240
POWER = 0.8


def binary_kl(p, q):
    success = p * math.log(p / q) if p else 0.0
    failure = (1 - p) * math.log((1 - p) / (1 - q)) if p < 1 else 0.0
    return success + failure


def ceiling(forward, reverse):
    """Any size-alpha rejection event has to obey both KL constraints."""
    lo, hi = ALPHA, 1.0
    for _ in range(52):
        p = (lo + hi) / 2
        if p == 1 or binary_kl(p, ALPHA) > forward or binary_kl(ALPHA, p) > reverse:
            hi = p
        else:
            lo = p
    return hi


def categorical_kl(p, q):
    assert np.all(p >= 0) and np.all(q >= 0)
    assert np.allclose(p.sum(-1), 1) and np.allclose(q.sum(-1), 1)
    support = p > 0
    assert np.all(q[support] > 0)
    contribution = np.zeros_like(p)
    contribution[support] = p[support] * np.log(p[support] / q[support])
    return np.maximum(0, contribution.sum(-1))


def centered_laws(a, b, o):
    midpoint = (a + b).mean(axis=1, keepdims=True) / 2
    a = midpoint + a - a.mean(axis=1, keepdims=True)
    b = midpoint + b - b.mean(axis=1, keepdims=True)
    omissions = np.broadcast_to(o[:, None, None], a.shape)
    return (
        np.stack((a, 1 - omissions - a, omissions), axis=-1),
        np.stack((b, 1 - omissions - b, omissions), axis=-1),
    )


def compare(a, b, o, w, probes):
    a_prob, b_prob = centered_laws(a, b, o)
    both_directions = (categorical_kl(a_prob, b_prob), categorical_kl(b_prob, a_prob))
    # Balanced arms and equal-lab context proportions. A common stimulus law is
    # shared by the arms. The oracle can choose a different stimulus by context.
    best_common = [float((w[:, None] * d.mean(axis=1)).sum(axis=0).max()) for d in both_directions]
    best_oracle = [float(w @ d.mean(axis=1).max(axis=1)) for d in both_directions]
    # The best sign may differ by KL direction. Giving each direction its own
    # maximizing sign further relaxes the bound.
    def limits(d_ab, d_ba):
        req1, req2 = binary_kl(POWER, ALPHA), binary_kl(ALPHA, POWER)
        return {
            "kl_per_learner_A_B_and_B_A": [d_ab, d_ba],
            "power_ceiling_A_true_B_null": ceiling(N * d_ab, N * d_ba),
            "power_ceiling_B_true_A_null": ceiling(N * d_ba, N * d_ab),
            "necessary_n_A_true_B_null": math.ceil(max(req1 / d_ab, req2 / d_ba)) if d_ab and d_ba else None,
            "necessary_n_B_true_A_null": math.ceil(max(req1 / d_ba, req2 / d_ab)) if d_ab and d_ba else None,
        }

    arm_a = (w[:, None, None] * a).sum(axis=0)
    arm_b = (w[:, None, None] * b).sum(axis=0)
    pooled_laws = centered_laws(arm_a[None], arm_b[None], np.array([w @ o]))
    pooled_signed = [float(categorical_kl(p, q).mean(axis=1).max())
                     for p, q in (pooled_laws, pooled_laws[::-1])]
    gap = (arm_a[0] - arm_a[1]) - (arm_b[0] - arm_b[1])
    paired_sides = gap.reshape(-1, 2)
    exact100 = np.isclose(abs(probes), 1.0)
    strongest = int(np.argmax(abs(gap)))
    return {
        "A_arm_correct_by_probe": arm_a.tolist(),
        "B_arm_correct_by_probe": arm_b.tolist(),
        "signed_contrast_gap": gap.tolist(),
        "equal_side_gap": paired_sides.mean(axis=1).tolist(),
        "half_right_minus_left_gap": ((paired_sides[:, 1] - paired_sides[:, 0]) / 2).tolist(),
        "max_abs_signed_gap": float(abs(gap[strongest])),
        "max_abs_signed_gap_probe": float(probes[strongest]),
        "exact100_power_ceiling": limits(*(float((w[:, None, None] * d[:, :, exact100]).sum() / 4)
                                            for d in both_directions)),
        "iid_unlabeled_mixture_signed_probe": limits(*pooled_signed),
        "common_signed_probe": limits(*best_common),
        "context_oracle_signed_probe": limits(*best_oracle),
    }


def main():
    started = time.perf_counter()
    source = Path(sys.argv[1]).read_bytes()
    with np.load(io.BytesIO(source), allow_pickle=False) as archive:
        names = ("correct", "terminal_omit", "labs", "valid", "probe", "starts", "engagement", "models", "arms")
        summaries = {key: archive[key] for key in names}
    correct = summaries["correct"].mean(axis=-2, dtype=float)
    omit = summaries["terminal_omit"].mean(axis=-1, dtype=float)
    probes = summaries["probe"]
    assert probes.tolist() == [-1.0, 1.0, -.25, .25, -.125, .125, -.0625, .0625]
    assert summaries["arms"].tolist() == ["H_last", "E_last", "H_rich", "E_rich"]
    assert np.allclose(omit, omit[:, :, :1], atol=1e-9, rtol=0)
    labs = summaries["labs"]
    results = {}
    for t, g, protocol in itertools.product(range(2), range(2), range(2)):
        key = f'{summaries["starts"][t]}:{summaries["engagement"][g]}:{("order", "composition")[protocol]}'
        results[key] = {}
        arm = slice(2 * protocol, 2 * protocol + 2)
        for a_name, b_name in itertools.product(("existing", "session"), ("growth", "reinforce")):
            a, b = [summaries["models"].tolist().index(model) for model in (a_name, b_name)]
            matching = summaries["valid"][:, a] & summaries["valid"][:, b]
            a_correct = correct[matching, t, g, a, arm]
            b_correct = correct[matching, t, g, b, arm]
            context_omit = omit[matching, t, 0]
            by_lab, lab_index, lab_count = np.unique(labs[matching], return_inverse=True, return_counts=True)
            weights = 1.0 / (len(by_lab) * lab_count[lab_index])
            assert np.isclose(weights.sum(), 1)
            result = compare(a_correct, b_correct, context_omit, weights, probes)
            results[key][f"{a_name}:{b_name}"] = {"contexts": int(matching.sum()), "labs": len(by_lab), **result}

    assert abs(ceiling(0, 0) - ALPHA) < 1e-12
    assert abs(ceiling(binary_kl(POWER, ALPHA), binary_kl(ALPHA, POWER)) - POWER) < 1e-12
    toy = np.array([[[.3], [.5]]])
    toy_a, toy_b = centered_laws(toy, toy + .12, np.array([.1]))
    assert np.allclose(toy_a, toy_b)
    assert np.allclose(categorical_kl(toy_a, toy_b), 0)
    assert abs(float(categorical_kl(np.array([.6, .4, 0]), np.array([.5, .5, 0])))
               - binary_kl(.6, .5)) < 1e-12
    data = {
        "alpha": ALPHA, "total_animals": N, "power_threshold": POWER,
        "kl_necessary_true_vs_null_and_null_vs_true": [binary_kl(POWER, ALPHA), binary_kl(ALPHA, POWER)],
        "summary_sha256": hashlib.sha256(source).hexdigest(),
        "summary_bytes": len(source),
        "decoded_summary_bytes": sum(array.nbytes for array in summaries.values()),
        "results": results,
        "runtime": {"elapsed_seconds": time.perf_counter() - started, "peak_rss": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
    }
    print(json.dumps(data, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
