"""Check the saved particle calculation with all distinct particle pairs."""
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import resource
import sys
import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import norm, t

path = Path(sys.argv[1])
payload = path.read_bytes()
with np.load(io.BytesIO(payload), allow_pickle=False) as z:
    keys = ("counts", "truth", "meta", "person_scores", "paired_gains", "law_separation")
    data = {key: z[key] for key in keys}
counts, truth, meta = (data[k] for k in ("counts", "truth", "meta"))
assert counts.shape == (280, 3, 3, 512, 2)
assert truth.sum(axis=0).tolist() == [4817, 90]
people = np.unique(meta[:, 0])
assert len(people) == 40
for subject in people:
    assert np.sum((meta[:, 0] == subject) & (meta[:, 2] == 3)) == 4
    assert np.sum((meta[:, 0] == subject) & (meta[:, 2] == 6)) == 3
    assert len(np.unique(meta[meta[:, 0] == subject, 3])) == 1


def law(samples):
    x, n = np.unique(samples, axis=0, return_counts=True)
    return x, n / n.sum()


def cross(p, q):
    x, wx = p
    y, wy = q
    return np.sum(cdist(x, y) * wx[:, None] * wy[None, :])


def paired_people(values):
    return np.array([
        .5 * (values[(meta[:, 0] == subject) & (meta[:, 2] == 3)].mean(axis=0)
              + values[(meta[:, 0] == subject) & (meta[:, 2] == 6)].mean(axis=0))
        for subject in people
    ])


losses, separations, clock, feasible_shift = [], [], [], []
for values, target, row in zip(counts, truth, meta):
    h = 5 * row[2]
    block_losses = np.empty((3, 3))
    laws = [[law(p) for p in scenario] for scenario in values]
    within = np.empty_like(block_losses)
    k = values.shape[2]
    for s, scenario in enumerate(laws):
        for a, p in enumerate(scenario):
            within[s, a] = cross(p, p)
            target_distance = np.dot(np.linalg.norm(p[0] - target, axis=1), p[1])
            block_losses[s, a] = (target_distance - .5 * k / (k - 1) * within[s, a]) / h

    def unbiased(s, a, r, b):
        empirical = cross(laws[s][a], laws[r][b]) - .5 * (within[s, a] + within[r, b])
        same_pair = np.linalg.norm(values[s, a] - values[r, b], axis=1).mean()
        return (k * empirical - same_pair) / ((k - 1) * h)

    separations.append([unbiased(0, 2, 0, a) for a in (0, 1)])
    clock.append([[unbiased(0, a, s, a) for a in range(3)] for s in (1, 2)])
    feasible_shift.append(np.mean(values[0, 0].sum(axis=1) < h))
    losses.append(block_losses)
losses = paired_people(np.array(losses))
gains = losses[:, :, :2] - losses[:, :, 2:3]
mean = gains.mean(axis=0)
sd = gains.std(axis=0, ddof=1)
width = t.ppf(.9875, len(people) - 1) * sd / np.sqrt(len(people))
law_means = paired_people(np.array(separations)).mean(axis=0)
out = {
    "utc": datetime.now(timezone.utc).isoformat(),
    "actual_archive_read_bytes": len(payload),
    "decoded_member_bytes": sum(v.nbytes for v in data.values()),
    "people": 40, "blocks": 280,
    "observed_target_totals": truth.sum(axis=0).tolist(),
    "all_distinct_pair_person_equal_losses": losses.mean(axis=0).tolist(),
    "all_distinct_pair_person_equal_gains": mean.tolist(),
    "all_distinct_nominal_simultaneous_95": [(mean[0] - width[0]).tolist(),
                                            (mean[0] + width[0]).tolist()],
    "gain_delta_vs_original_half_pair": (mean - data["paired_gains"].mean(axis=0)).tolist(),
    "opposed_law_expected_gain_after_diagonal_correction": law_means.tolist(),
    "timing_law_expected_loss_penalty_after_diagonal_correction":
        paired_people(np.array(clock)).mean(axis=0).tolist(),
    "ordinary_paths_with_room_for_one_correct_at_fixed_omissions":
        float(paired_people(np.array(feasible_shift)).mean()),
    "hypothetical_detect_any_gain_if_own_forecast_is_truth_at_n91":
        norm.cdf(law_means / (sd[0] / np.sqrt(91)) - norm.ppf(.975)).tolist(),
    "scope": "Postfit integration check and paired-law discrimination; no new paths or fitted parameters.",
}
r = resource.getrusage(resource.RUSAGE_SELF)
out["resources"] = {"user_seconds": r.ru_utime, "system_seconds": r.ru_stime, "peak_rss_bytes": r.ru_maxrss}
report = json.dumps(out, indent=2, allow_nan=False) + "\n"
Path(sys.argv[2]).write_text(report)
print(report, end="")
