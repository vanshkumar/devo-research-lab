"""Measure a conservative fixed precriterion window and cue/key constraints."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import resource
import sys
import numpy as np

p = Path(sys.argv[1])
x = np.load(p, allow_pickle=False)
assert x.shape == (30403, 14)
cuts = np.flatnonzero(np.any(x[1:, :2] != x[:-1, :2], axis=1)) + 1
support = {3: Counter(), 6: Counter()}
actions = {}
maps = {3: Counter(), 6: Counter()}
balances = {3: Counter(), 6: Counter()}
for b in np.split(x, cuts):
    subject, _, load = b[0, :3].astype(int)
    for a, key in zip(b[:, 9].astype(int), b[:, 10].astype(int)):
        if a > 0:
            actions.setdefault((subject, a), set()).add(key)
    if load not in support:
        continue
    h = 7 * load
    d = support[load]
    d["blocks"] += 1
    d["complete_h7L"] += int(len(b) >= h)
    seq = b[:, 4].astype(int)
    cues, inv = np.unique(seq, return_inverse=True)
    cumulative = np.cumsum(inv[:, None] == np.arange(load), axis=0)
    d["cues_not_seen_by_origin"] += int(np.count_nonzero(cumulative[2 * load - 1] == 0))
    d["cues_not_seen_by_horizon"] += int(np.count_nonzero(cumulative[h - 1] == 0))
    spread = np.ptp(cumulative[:h], axis=1)
    balances[load][int(spread.max())] += 1
    d["ninth_at_or_before_horizon"] += int(np.any(cumulative[:h] >= 9))
    d["adjacent_repeated_cues_through_horizon"] += int(np.sum(seq[1:h] == seq[:h - 1]))
    d["maximum_identical_run"] = max(d["maximum_identical_run"], max(
        np.diff(np.r_[0, np.flatnonzero(seq[1:h] != seq[:h - 1]) + 1, h]).tolist()))
    first = [np.flatnonzero(seq == cue)[0] for cue in cues]
    hist = np.bincount(b[first, 8].astype(int), minlength=4)[1:]
    maps[load]["-".join(map(str, sorted(hist)))] += 1
    f = b[2 * load:h]
    d["target_rows"] += len(f)
    d["target_omitted"] += int(np.sum(f[:, 9] == -1))
    d["target_correct"] += int(np.sum(f[:, 11] == 1))
    near = (f[:, 13] >= 1.3) & (f[:, 13] <= 1.4)
    d["target_responded_1p3_to_1p4"] += int(near.sum())
    d["target_correct_1p3_to_1p4"] += int(np.sum(near & (f[:, 11] == 1)))
    d["target_responded_at_or_below_0p15"] += int(np.sum((f[:, 13] > 0) & (f[:, 13] <= .15)))
out = {
    "utc": datetime.now(timezone.utc).isoformat(), "projection_read_bytes": p.stat().st_size,
    "candidate_window": "origin at 2L, horizon 7L; choose before any modeling",
    "load_support": support, "prefix_max_cue_count_spread_hist": balances,
    "correct_key_map_sorted_counts": maps,
    "subject_action_observed_key_pairs": len(actions),
    "pairs_with_multiple_physical_keys": sum(len(v) != 1 for v in actions.values()),
    "scope": "Observed structural support. The actual preplanned tape or controller was not recovered.",
}
r = resource.getrusage(resource.RUSAGE_SELF)
out["resources"] = {"user_seconds": r.ru_utime, "sys_seconds": r.ru_stime, "peak_rss_bytes": r.ru_maxrss}
text = json.dumps(out, indent=2) + "\n"
Path(sys.argv[2]).write_text(text)
print(text, end="")
