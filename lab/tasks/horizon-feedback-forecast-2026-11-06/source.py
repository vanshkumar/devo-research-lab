"""Check and project the pinned 25-person development object."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr


HERE = Path(__file__).resolve().parent
BODY = HERE / "source_train.csv"
SHA256 = "3005b71bab3a91fb6ee74b8895f3508d957fecbd61f9d9d9d17a620a7f82d6a7"
SCHEDULE = ["participant_id", "block", "game", "gameLength", "uc",
            "trial", "horizon", "type"]
KEY = ["participant_id", "block", "game"]
GAPS = np.array([4, 8, 12, 20, 30])


def source_metadata():
    assert BODY.stat().st_size == 2_052_611
    assert hashlib.sha256(BODY.read_bytes()).hexdigest() == SHA256
    schedule = pd.read_csv(BODY, usecols=SCHEDULE)
    assert len(schedule) == 60_000
    assert not schedule.isna().any().any()
    assert not schedule.duplicated(KEY + ["trial"]).any()
    grouped = schedule.groupby(KEY, sort=True)
    games = grouped.agg(rows=("trial", "size"), length=("gameLength", "first"),
                        length_keys=("gameLength", "nunique"),
                        horizon=("horizon", "first"),
                        horizon_keys=("horizon", "nunique"),
                        uc_keys=("uc", "nunique"),
                        first=("trial", "min"), last=("trial", "max"))
    assert len(games) == 8_000 and games.index.get_level_values(0).nunique() == 25
    assert (games[["length_keys", "horizon_keys", "uc_keys"]] == 1).all().all()
    assert set(games.horizon) == {1, 6} and (games.length == games.horizon + 4).all()
    assert (games.rows == games.length).all()
    assert (games["first"] == 1).all() and (games["last"] == games.length).all()
    assert (games.groupby(["participant_id", "horizon"]).size() == 160).all()
    assert (games.groupby(["participant_id", "block"]).size() == 80).all()
    assert set(schedule.type) == {"forced", "free"}
    assert ((schedule.type == "forced") == (schedule.trial <= 4)).all()
    return schedule, games


def load_games():
    schedule, games = source_metadata()
    values = pd.read_csv(BODY, usecols=["choice", "reward"])
    assert len(schedule) == len(values)
    assert not values.isna().any().any() and set(values.choice) == {"H", "I"}
    assert values.reward.between(1, 100).all() and (values.reward % 1 == 0).all()
    observations = pd.concat([schedule, values], axis=1)
    n_forced = observations.query("trial <= 4").groupby(KEY).choice.agg(
        lambda a: int((a == "I").sum()))
    assert set(n_forced) == {1, 2, 3}
    games["n_forced_i"] = n_forced
    games["uc"] = observations.groupby(KEY).uc.first()
    assert games.groupby("uc").n_forced_i.nunique().max() == 1
    return observations, games


def main():
    observations, games = load_games()
    # Generative means are auditor-only. They never enter fit or simulation.
    audit = pd.read_csv(BODY, usecols=["m1", "m2"])
    assert not audit.isna().any().any()
    joined = pd.concat([observations, audit], axis=1)
    assert (joined.groupby(KEY)[["m1", "m2"]].nunique() == 1).all().all()
    means = joined.groupby(KEY)[["m1", "m2"]].first()
    support = ((means.m1.isin([40, 60]) | means.m2.isin([40, 60]))
               & (means.m1 - means.m2).abs().isin(GAPS))
    assert support.all()
    # Test both side mappings with the randomized forced feedback alone.
    f = joined.query("trial <= 4")
    observed = f.reward.to_numpy()
    aligned = np.where(f.choice == "H", f.m1, f.m2)
    inverted = np.where(f.choice == "I", f.m1, f.m2)
    residual = observed - aligned
    wrong = observed - inverted
    assert np.mean(residual**2) < np.mean(wrong**2)
    low = (observed - .5 - aligned) / 8
    high = (observed + .5 - aligned) / 8
    rounded_inside = ndtr((100.5 - aligned) / 8) - ndtr((.5 - aligned) / 8)
    p = ndtr(high) - ndtr(low)
    p_clip = np.where(observed == 1, ndtr(high),
                      np.where(observed == 100, ndtr(-low), p))
    p_truncate = p / rounded_inside
    counts = games.groupby(["horizon", "n_forced_i"]).size()
    uc_map = games.groupby("uc").n_forced_i.first()
    balance = means.assign(horizon=games.horizon).groupby(["horizon", "m1", "m2"]).size()
    free = joined.query("trial > 4").copy()
    free["optimal"] = ((free.choice == "H") == (free.m1 > free.m2)).astype(float)
    accuracy = free.groupby(["horizon", "trial"]).optimal.mean()
    acc_by_person = free.groupby("participant_id").optimal.mean()
    output = {
        "sha256": SHA256, "rows": len(observations), "games": len(games),
        "participant_ids": sorted(int(x) for x in observations.participant_id.unique()),
        "block_labels": sorted(int(x) for x in observations.block.unique()),
        "game_label_range": [int(observations.game.min()), int(observations.game.max())],
        "unique_game_labels_per_participant": sorted(
            int(x) for x in observations.groupby("participant_id").game.nunique().unique()),
        "horizon_and_n_forced_I_counts": {f"{h}:{n}": int(c) for (h, n), c in counts.items()},
        "uncertainty_code_to_n_forced_I": {str(k): int(v) for k, v in uc_map.items()},
        "schedule_mean_pairs_and_frequency_range_per_horizon": {
            str(h): [int(len(v)), int(v.min()), int(v.max())]
            for h, v in balance.groupby(level=0)
        },
        "forced_residual_mean_sd_rmse_inverted": [
            float(residual.mean()), float(residual.std(ddof=1)), float(np.mean(wrong**2)**.5)
        ],
        "forced_rewards_equal_to_1_or_100": [int(sum(observed == y)) for y in [1, 100]],
        "observed_forced_log_likelihood_clipped_minus_truncated": float(
            (np.log(p_clip) - np.log(p_truncate)).sum()),
        "free_optimal_rate": {f"{h}:{t}": float(v) for (h, t), v in accuracy.items()},
        "free_person_optimal_rate_min_median_max": [float(x) for x in
            np.quantile(acc_by_person, [0, .5, 1])],
        "missing_schedule_rows_or_invalid_recorded_choices_or_rewards": 0,
        "booked_input_reads_bytes": 4 * BODY.stat().st_size,
    }
    (HERE / "SOURCE_CHECK.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
