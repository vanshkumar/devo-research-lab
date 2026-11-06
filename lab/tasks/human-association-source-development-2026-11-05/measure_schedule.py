"""Additional Stage A counts for criterion, within-block key coding and window support."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import resource
import sys
import numpy as np

projection = Path(sys.argv[1])
x = np.load(projection, allow_pickle=False)
assert x.shape == (30403, 14)
cut = np.flatnonzero(np.any(x[1:, :2] != x[:-1, :2], axis=1)) + 1
blocks = np.split(x, cut)
support = {3: Counter(), 6: Counter()}
local = {3: {}, 6: {}}
maps_by_person = {}
maps = Counter()
for b in blocks:
    p, _, load = b[0, :3].astype(int)
    keys = tuple(tuple(np.unique(b[b[:, 9] == a, 10]).astype(int)) for a in (1, 2, 3))
    maps["blocks_with_all_three_mapped"] += int(all(len(k) == 1 for k in keys))
    maps_by_person.setdefault(p, set()).add(keys)
    if load not in support:
        continue
    counts = support[load]
    seq = b[:, 4]
    cap = 8 * load
    counts["blocks"] += 1
    counts["opportunity_rows_at_9"] += 9
    for cap_h, origin in ((9, load), (cap, 2 * load)):
        w = b[origin:cap_h]
        counts[f"h{cap_h}_suffix_omissions"] += int(np.sum(w[:, 9] == -1))
        counts[f"h{cap_h}_suffix_correct"] += int(np.sum(w[:, 11] == 1))
        counts[f"h{cap_h}_suffix_prior_cue_exposure_rows"] += int(np.sum(w[:, 7] > 1))
        counts[f"h{cap_h}_suffix_after_prefix_known_correct_cue"] += int(np.sum(np.isin(
            w[:, 4], b[:origin][b[:origin, 11] == 1, 4])))
        counts[f"h{cap_h}_suffix_rows"] += len(w)
    first_ninth = int(np.flatnonzero(b[:, 7] == 9)[0]) + 1
    local[load]["first_ninth_min"] = min(first_ninth, local[load].get("first_ninth_min", first_ninth))
    counts["first_ninth_at_or_before_2x_origin"] += int(first_ninth <= 2 * load)
    counts["first_ninth_at_or_before_8x_cap"] += int(first_ninth <= cap)
    all_ninth_times = [int(np.flatnonzero((seq == s) & (b[:, 7] == 9))[0]) + 1 for s in np.unique(seq)]
    global_first = max(all_ninth_times)
    local[load]["first_all_nine_min"] = min(global_first, local[load].get("first_all_nine_min", global_first))
    counts["all_ninths_by_8x"] += int(global_first <= cap)
    for s in np.unique(seq):
        idx = np.flatnonzero(seq == s)
        nth, last = int(idx[8]) + 1, int(idx[-1]) + 1
        last_four_correct = np.count_nonzero(b[idx[5:9], 11] == 1)
        if last < cap:
            counts["cues_whose_last_deposited_opportunity_precedes_cap"] += 1
            counts["such_cues_ending_9_to_14"] += int(9 <= len(idx) < 15)
        if nth < cap:
            state = "passed_local_criterion" if last_four_correct >= 3 else "below_local_criterion"
            counts[f"ninth_before_cap_{state}"] += 1
            counts[f"ninth_before_cap_{state}_later_same_cue_before_cap"] += int(
                len(idx) > 9 and int(idx[9]) + 1 <= cap)
            counts[f"ninth_before_cap_{state}_later_same_cue_anywhere"] += int(len(idx) > 9)
maps["people_with_more_than_one_partial_or_full_block_map"] = sum(len(m) > 1 for m in maps_by_person.values())
maps["people_with_multiple_distinct_complete_block_maps"] = sum(
    sum(all(len(k) == 1 for k in block_map) for block_map in m) > 1
    for m in maps_by_person.values())
out = {
    "utc": datetime.now(timezone.utc).isoformat(),
    "projection_read_bytes": projection.stat().st_size,
    "load_counts": support, "earliest_order": local, "physical_key_mapping": maps,
    "claim_scope": "Retrospective structure and pre-criterion window support only. No held suffix scheduling for an actor and no fitting.",
}
r = resource.getrusage(resource.RUSAGE_SELF)
out["resources"] = {"user_seconds": r.ru_utime, "sys_seconds": r.ru_stime, "peak_rss_bytes": r.ru_maxrss}
text = json.dumps(out, indent=2) + "\n"
Path(sys.argv[2]).write_text(text)
print(text, end="")
