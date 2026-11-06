"""Frozen whole-plant analysis of matched evaluator optimization trajectories.

Reads saved trajectory arrays only; never loads circuit/actor pickle state or
queries a plant. The requested round is selected exactly even after extension.
Undefined normalization is reported without dropping or replacing any plant.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ARMS = ("oracle_joint", "learned35_joint", "learned35_fixed",
        "learned140_joint", "untutored_joint", "shuffled35_joint")
BOOTSTRAPS = 20000
SEED = 20261028
COST_TOL = 1e-10
LOSS_TOL = 1e-8
ZERO_GAIN_TOL = 1e-12
FIDELITY_MSE = .4


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite_or_none(value):
    value = float(value)
    return value if np.isfinite(value) else None


def descriptive(values):
    """Summarize all rows, never silently filter undefined ratio endpoints."""
    arr = np.asarray(values, dtype=float)
    defined = bool(np.isfinite(arr).all())
    result = dict(n=int(arr.size), undefined_count=int((~np.isfinite(arr)).sum()),
                  mean=None, sd=None, minimum=None, maximum=None)
    if defined:
        result.update(mean=float(arr.mean()),
                      sd=float(arr.std(ddof=1)) if len(arr) > 1 else None,
                      minimum=float(arr.min()), maximum=float(arr.max()))
    return result


def mean_interval(values, indices):
    arr = np.asarray(values, dtype=float)
    result = descriptive(arr)
    result["paired_plant_percentile_95_interval"] = None
    if np.isfinite(arr).all():
        samples = arr[indices].mean(axis=1)
        result["paired_plant_percentile_95_interval"] = np.quantile(
            samples, [.025, .975]).tolist()
    return result


def read_endpoint(path, plant_id, arm, rounds):
    with np.load(path, allow_pickle=False) as z:
        required = ("actions", "costs", "true_losses", "steps", "queries")
        if any(name not in z for name in required):
            raise ValueError(f"Missing trajectory array in {path}")
        data = {name: np.asarray(z[name]) for name in required}
    lengths = {len(value) for value in data.values()}
    if len(lengths) != 1 or len(data["costs"]) <= rounds:
        raise ValueError(f"Incomplete/unaligned trajectory for round {rounds}: {path}")
    for name, value in data.items():
        if not np.isfinite(value[:rounds+1]).all():
            raise ValueError(f"Nonfinite {name} in {path}")
    actions = np.asarray(data["actions"][:rounds+1], dtype=float)
    costs = np.asarray(data["costs"][:rounds+1], dtype=float)
    losses = np.asarray(data["true_losses"][:rounds+1], dtype=float)
    queries = np.asarray(data["queries"][:rounds+1])
    if not np.array_equal(queries, 1 + 10*np.arange(rounds+1)):
        raise ValueError(f"Unmatched query budget in {path}")
    if actions.ndim != 2 or actions.shape[1] != 5:
        raise ValueError(f"Expected 5 action coordinates in {path}")
    if np.any(losses < 0):
        raise ValueError(f"Negative true MSE in {path}")
    if np.any(np.diff(costs) > COST_TOL):
        raise ValueError(f"Accepted actor trajectory increases its cost in {path}")
    accepted = np.any(np.diff(actions, axis=0) != 0., axis=1)
    reward_improves = (np.diff(costs) < -COST_TOL) & accepted
    true_worsens = np.diff(losses) > LOSS_TOL
    conflicts = reward_improves & true_worsens
    initial, terminal = float(losses[0]), float(losses[-1])
    normalized = terminal/initial if initial > 0 else np.nan
    record = dict(plant_id=int(plant_id), arm=arm, rounds=int(rounds),
                  queries=int(queries[-1]), trajectory_rounds_available=len(data["costs"])-1,
                  trajectory_sha256=digest(path),
                  initial_action=actions[0].tolist(), terminal_action=actions[-1].tolist(),
                  final_gain=float(actions[-1, 4]),
                  zero_gain=bool(abs(actions[-1, 4]) <= ZERO_GAIN_TOL),
                  terminal_true_mse_at_most_0_4=bool(terminal <= FIDELITY_MSE),
                  initial_true_mse=initial, terminal_true_mse=terminal,
                  absolute_true_improvement=initial-terminal,
                  normalized_final_true_loss=finite_or_none(normalized),
                  fraction_true_improvement=finite_or_none(1-normalized),
                  initial_cost=float(costs[0]), terminal_cost=float(costs[-1]),
                  absolute_cost_reduction=float(costs[0]-costs[-1]),
                  fractional_cost_reduction=float((costs[0]-costs[-1])/costs[0])
                  if costs[0] != 0 else None,
                  cost_units="true_feature_MSE" if arm == "oracle_joint" else "circuit_rate_Hz",
                  accepted_steps=int(accepted.sum()),
                  reward_improving_steps=int(reward_improves.sum()),
                  reward_improves_while_true_worsens_steps=int(conflicts.sum()),
                  reward_improves_while_true_worsens_rounds=(np.flatnonzero(conflicts)+1).tolist(),
                  any_reward_improves_while_true_worsens=bool(conflicts.any()),
                  terminal_true_loss_worse_than_initial=bool(terminal > initial+LOSS_TOL),
                  final_step=float(data["steps"][rounds]))
    return record


def numeric_column(rows, name):
    return np.asarray([np.nan if row[name] is None else row[name] for row in rows], dtype=float)


def ratio_of_mean_improvements(numerator, denominator, indices):
    numerator = np.asarray(numerator, dtype=float)
    denominator = np.asarray(denominator, dtype=float)
    result = dict(estimate=None, paired_plant_percentile_95_interval=None,
                  undefined_bootstrap_denominators=None,
                  definition="mean learned35 normalized improvement / mean oracle normalized improvement")
    if not (np.isfinite(numerator).all() and np.isfinite(denominator).all()):
        result["reason_undefined"] = "At least one plant has undefined normalization; no plants dropped."
        return result
    denom_mean = float(denominator.mean())
    denoms = denominator[indices].mean(axis=1)
    numerators = numerator[indices].mean(axis=1)
    invalid = np.abs(denoms) <= 1e-12
    result["undefined_bootstrap_denominators"] = int(invalid.sum())
    if abs(denom_mean) > 1e-12:
        result["estimate"] = float(numerator.mean()/denom_mean)
    if not invalid.any():
        result["paired_plant_percentile_95_interval"] = np.quantile(
            numerators/denoms, [.025, .975]).tolist()
    else:
        result["reason_interval_undefined"] = "A bootstrap oracle mean is zero; no bootstrap samples dropped."
    return result


def analyze(base_dir, plants, rounds, extension128=False):
    if not plants or len(set(plants)) != len(plants):
        raise ValueError("Specify a nonempty list of distinct plants.")
    if rounds < 1:
        raise ValueError("Analysis needs at least one completed round.")
    indices = np.random.default_rng(SEED).integers(0, len(plants),
                                                  size=(BOOTSTRAPS, len(plants)))
    records = {arm: [] for arm in ARMS}
    for plant in plants:
        for arm in ARMS:
            path = base_dir / f"plant_{plant:03d}" / f"{arm}_trajectory.npz"
            records[arm].append(read_endpoint(path, plant, arm, rounds))
        initial_losses = [records[arm][-1]["initial_true_mse"] for arm in ARMS]
        initial_actions = [records[arm][-1]["initial_action"] for arm in ARMS]
        if not np.allclose(initial_losses, initial_losses[0], rtol=0, atol=1e-12):
            raise ValueError(f"Mismatched initial loss across arms for plant {plant}")
        if any(action != initial_actions[0] for action in initial_actions):
            raise ValueError(f"Mismatched initial actions across arms for plant {plant}")
    metrics = ("initial_true_mse", "terminal_true_mse", "absolute_true_improvement",
               "normalized_final_true_loss", "fraction_true_improvement", "initial_cost",
               "terminal_cost", "absolute_cost_reduction", "fractional_cost_reduction", "final_step", "final_gain")
    summaries = {}
    for arm, rows in records.items():
        summary = {name: mean_interval(numeric_column(rows, name), indices) for name in metrics}
        summary.update(plants_with_reward_improves_while_true_worsens=sum(
            row["any_reward_improves_while_true_worsens"] for row in rows),
            plants_with_terminal_true_loss_worse_than_initial=sum(
                row["terminal_true_loss_worse_than_initial"] for row in rows),
            reward_improves_while_true_worsens_steps_total=sum(
                row["reward_improves_while_true_worsens_steps"] for row in rows),
            accepted_steps_total=sum(row["accepted_steps"] for row in rows),
            reward_improving_steps_total=sum(row["reward_improving_steps"] for row in rows),
            plants_with_zero_final_gain=sum(row["zero_gain"] for row in rows),
            plants_with_terminal_true_mse_at_most_0_4=sum(
                row["terminal_true_mse_at_most_0_4"] for row in rows))
        summaries[arm] = summary
    improvement = {arm: numeric_column(rows, "fraction_true_improvement")
                   for arm, rows in records.items()}
    residual = {arm: numeric_column(rows, "normalized_final_true_loss")
                for arm, rows in records.items()}
    learn, oracle = improvement["learned35_joint"], improvement["oracle_joint"]
    contrasts = {
        "learned35_minus_oracle_normalized_residual": mean_interval(
            residual["learned35_joint"]-residual["oracle_joint"], indices),
        "learned35_minus_half_oracle_improvement": mean_interval(learn-.5*oracle, indices),
        "learned35_minus_untutored_improvement": mean_interval(learn-improvement["untutored_joint"], indices),
        "learned35_minus_shuffled35_improvement": mean_interval(learn-improvement["shuffled35_joint"], indices),
        "fixed_gain_minus_joint_learned35_improvement": mean_interval(improvement["learned35_fixed"]-learn, indices),
        "learned140_minus_learned35_improvement": mean_interval(improvement["learned140_joint"]-learn, indices),
    }
    def lower_positive(name):
        ci = contrasts[name]["paired_plant_percentile_95_interval"]
        return bool(ci[0] > 0) if ci is not None else None
    oracle_mean = summaries["oracle_joint"]["fraction_true_improvement"]["mean"]
    half_mean = contrasts["learned35_minus_half_oracle_improvement"]["mean"]
    result = dict(
        analysis=dict(plant_ids=list(plants), rounds=rounds, number_of_plants=len(plants),
                      base_directory=str(base_dir.resolve()),
                      seed=SEED, bootstrap_repetitions=BOOTSTRAPS,
                      resampling_unit="whole plant, paired across all arms",
                      intervals="ordinary percentile95; descriptive fixed generator ensemble; no secondary familywise guarantee",
                      endpoint_selection="exact trajectory index rounds; later entries ignored",
                      normalization="each plant terminal true MSE / same plant initial true MSE",
                      zero_initial_policy="retain plant; normalized endpoint undefined; no filtered ensemble means",
                      reward_improvement_cost_tolerance=COST_TOL,
                      true_worsening_loss_tolerance=LOSS_TOL,
                      secondary_zero_gain_tolerance=ZERO_GAIN_TOL,
                      secondary_target_fidelity_mse_threshold=FIDELITY_MSE,
                      query_budget_per_arm=1+10*rounds,
                      analysis_sha256=digest(__file__)),
        initial_loss=descriptive([row["initial_true_mse"] for row in records["oracle_joint"]]),
        plant_level=records, arm_summaries=summaries, paired_contrasts=contrasts,
        learned35_to_oracle_ratio_of_mean_improvements=ratio_of_mean_improvements(learn, oracle, indices),
        investment_criteria=dict(
            oracle_mean_true_reduction_at_least_75_percent=bool(oracle_mean >= .75) if oracle_mean is not None else None,
            learned35_point_improvement_at_least_half_oracle=bool(half_mean >= 0) if half_mean is not None else None,
            learned35_minus_untutored_lower95_above_zero=lower_positive("learned35_minus_untutored_improvement"),
            learned35_minus_shuffled35_lower95_above_zero=lower_positive("learned35_minus_shuffled35_improvement"),
            interpretation="Half-oracle is the declared point criterion with uncertainty reported separately; all primary target-specific conditions required."))
    if extension128:
        if rounds != 64:
            raise ValueError("--extension128 compares the declared64-to128 extension; set --rounds64")
        extended = {}
        for arm in ("oracle_joint", "learned35_joint"):
            rows = [read_endpoint(base_dir / f"plant_{plant:03d}" / f"{arm}_trajectory.npz",
                                  plant, arm, 128) for plant in plants]
            new_improve = numeric_column(rows, "fraction_true_improvement")
            new_residual = numeric_column(rows, "normalized_final_true_loss")
            extended[arm] = dict(
                plant_level=rows,
                fraction_true_improvement_128=mean_interval(new_improve, indices),
                normalized_final_true_loss_128=mean_interval(new_residual, indices),
                additional_normalized_improvement_64_to128=mean_interval(new_improve-improvement[arm], indices),
                true_loss_change_64_to128=mean_interval(
                    numeric_column(rows, "terminal_true_mse")-numeric_column(records[arm], "terminal_true_mse"), indices),
                additional_cost_reduction_64_to128=mean_interval(
                    numeric_column(records[arm], "terminal_cost")-numeric_column(rows, "terminal_cost"), indices))
        result["extension128"] = extended
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plants", type=int, nargs="+", required=True)
    parser.add_argument("--rounds", type=int, default=64)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-dir", type=Path, default=HERE/"results",
                        help="Directory containing plant_NNN trajectory folders")
    parser.add_argument("--extension128", action="store_true")
    args = parser.parse_args()
    result = analyze(args.base_dir, args.plants, args.rounds, args.extension128)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_name(args.output.name+".tmp")
    tmp.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    tmp.replace(args.output)
    print(json.dumps(dict(output=str(args.output), plants=len(args.plants), rounds=args.rounds,
                          investment_criteria=result["investment_criteria"])))


if __name__ == "__main__":
    main()
