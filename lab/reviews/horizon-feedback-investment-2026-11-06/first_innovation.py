"""Measure the fixed first-free-reward/next-choice innovation on released Wilson source."""
import json
import resource
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr
from scipy.stats import norm, t

HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parents[1] / "tasks" / "horizon-feedback-forecast-2026-11-06"
sys.path.insert(0, str(AUTHOR))
from source import BODY, KEY, load_games


def moments(mu, clip):
    reward = np.arange(1., 101.)
    hi = ndtr((reward + .5 - mu[:, None]) / 8)
    lo = ndtr((reward - .5 - mu[:, None]) / 8)
    p = hi - lo
    if clip:
        p[:, 0], p[:, -1] = hi[:, 0], 1 - lo[:, -1]
    else:
        p /= p.sum(axis=1, keepdims=True)
    assert np.allclose(p.sum(axis=1), 1.)
    center = (p * reward).sum(axis=1)
    sd = np.sqrt((p * (reward - center[:, None])**2).sum(axis=1))
    return center, sd


def main():
    rows, games = load_games()
    means = pd.read_csv(BODY, usecols=["m1", "m2"])
    assert len(means) == len(rows)
    first = rows.horizon.eq(6) & rows.trial.eq(5)
    second = rows.horizon.eq(6) & rows.trial.eq(6)
    first_rows = rows.loc[first].join(means).set_index(KEY).sort_index()
    next_rows = rows.loc[second].set_index(KEY).sort_index()
    assert first_rows.index.equals(next_rows.index) and first_rows.index.is_unique
    assert first_rows.index.equals(games.index[games.horizon.eq(6)])
    ids = first_rows.index.get_level_values("participant_id")
    assert len(first_rows) == 4000 and (ids.value_counts() == 160).all() and ids.nunique() == 25
    mu = np.where(first_rows.choice.eq("H"), first_rows.m1, first_rows.m2)
    levels, index = np.unique(mu, return_inverse=True)
    repeat = (first_rows.choice == next_rows.choice).to_numpy(dtype=float)
    records = {}
    margin = .04
    n_fixed = 6 * 160
    se = .5 / np.sqrt(n_fixed)
    hw = norm.ppf(.975) * se
    for label, clip in [("rounded_clipped", True), ("rounded_truncated", False)]:
        center, sd = moments(levels, clip)
        innovation = (first_rows.reward.to_numpy() - center[index]) / sd[index]
        person = pd.Series(innovation * (repeat - .5), index=ids).groupby(level=0).mean()
        mean = person.mean()
        sd_people = person.std(ddof=1)
        records[label] = {
            "moment": mean,
            "person_sd": sd_people,
            "descriptive_source_25_95_halfwidth": t.ppf(.975, 24) * sd_people / np.sqrt(25),
            "person_transport_6_95_halfwidth": t.ppf(.975, 5) * sd_people / np.sqrt(6),
            "observed_innovation_mean_sd": [innovation.mean(), innovation.std(ddof=1)],
            "fixed_6_normal_95_interval_if_source_point_transports": [mean - hw, mean + hw],
            "fixed_6_normal_power_two_sided_nonzero_if_source_point_transports": (
                norm.sf(norm.ppf(.975) - mean / se) + norm.cdf(-norm.ppf(.975) - mean / se)
            ),
            "fixed_6_normal_probability_lower95_exceeds_margin_if_source_point_transports":
                norm.sf((margin + hw - mean) / se),
            "per_source_person_moment": {str(i): float(v) for i, v in person.items()},
        }
    usage = resource.getrusage(resource.RUSAGE_SELF)
    result = {
        "source_H6_games": len(first_rows),
        "source_people": len(ids.unique()),
        "source_H6_games_per_person": 160,
        "source_repeat_rate": repeat.mean(),
        "behavior_margin": margin,
        "fixed_six_idealized_conditional_null_se": se,
        "fixed_six_idealized_normal_95_halfwidth": hw,
        "results": records,
        "cost": {"cpu_seconds": usage.ru_utime + usage.ru_stime,
                 "peak_rss_bytes_macos": usage.ru_maxrss,
                 "booked_source_scans_bytes": 4 * BODY.stat().st_size},
    }
    out = json.dumps(result, indent=2, allow_nan=False)
    (HERE / "INNOVATION_RESULT.json").write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main()
