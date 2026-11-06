"""Prespecified exact-target local bias diagnostic, separate from motor actors.

This reads existing locally generated circuit states and never trains a circuit
or changes any primary actor. Target actions initialize only this diagnostic.
Every circuit feedback query executes the unchanged source dynamics, with no
memoization. A diagnostic gradient is not given to a primary learner.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import pickle
import sys

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("evaluator_diagnostic_base", HERE / "run.py")
base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = base
_spec.loader.exec_module(base)
np = base.np

DIAGNOSTIC_CONFIG = dict(
    finite_difference=.025, downhill_step_norm=.05,
    evaluators=["learned35", "learned140"],
    query_order="center, then +/- each coordinate0..4, then normalized downhill step",
    queries_per_evaluator=12, memoization=False,
    initialization="exact target action and gain1, diagnostic only",
    purpose="target-local reward bias and finite-tutoring comparison",
    gain_note="nonnegative gain scales signed post-normalization auditory drive; not sound pressure",
    inference="diagnostic target drift; no predictive correlation or actor repair",
)


def diagnose(plant_id, base_dir, output_dir):
    source_dir = base_dir / f"plant_{plant_id:03d}"
    state_path = source_dir / "state.pkl"
    if not state_path.is_file():
        raise FileNotFoundError(f"Existing generated state is required: {state_path}")
    with state_path.open("rb") as f:
        state = pickle.load(f)
    if state["plant_id"] != plant_id:
        raise RuntimeError("Generated state plant ID mismatch")
    if state["config"] != base.CONFIG or state["source_hashes"] != base.source_hashes():
        raise RuntimeError("Existing generated state config/source mismatch")
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"plant_{plant_id:03d}.json"
    npz_path = output_dir / f"plant_{plant_id:03d}.npz"
    if json_path.exists() or npz_path.exists():
        raise FileExistsError("Preserve existing diagnostics; use a new output directory for replay")
    center = np.r_[state["target"], 1.]
    lower, upper = np.asarray(base.CONFIG["lower"]), np.asarray(base.CONFIG["upper"])
    all_actions, all_costs, all_losses, all_gradients = [], [], [], []
    summaries = {}
    for evaluator in DIAGNOSTIC_CONFIG["evaluators"]:
        callback = base.feedback(f"{evaluator}_joint", state)
        actions = [center.copy()]
        costs = [callback(center)]
        gradient = np.empty(base.DIM+1)
        for d in range(base.DIM+1):
            pair = []
            for sign in (1., -1.):
                proposal = center.copy()
                proposal[d] += sign*DIAGNOSTIC_CONFIG["finite_difference"]
                if np.any(proposal < lower) or np.any(proposal > upper):
                    raise RuntimeError("Diagnostic central difference crosses action bounds")
                cost = callback(proposal)
                actions.append(proposal)
                costs.append(cost)
                pair.append(cost)
            gradient[d] = (pair[0]-pair[1])/(2*DIAGNOSTIC_CONFIG["finite_difference"])
        norm = float(np.linalg.norm(gradient))
        next_program = center.copy()
        if norm > 0.:
            next_program = np.clip(center-DIAGNOSTIC_CONFIG["downhill_step_norm"]*
                                   gradient/norm, lower, upper)
        actions.append(next_program)
        costs.append(callback(next_program))
        actions, costs = np.asarray(actions), np.asarray(costs)
        losses = base.true_losses(actions, state)
        if len(costs) != DIAGNOSTIC_CONFIG["queries_per_evaluator"]:
            raise AssertionError("Unexpected diagnostic feedback count")
        if not np.all(np.isfinite(costs)) or not np.all(np.isfinite(gradient)):
            raise FloatingPointError("Nonfinite circuit diagnostic")
        if losses[0] != 0.:
            raise AssertionError("Generated exact target must have zero feature MSE")
        summaries[evaluator] = dict(
            feedback_queries=len(costs), real_source_calls=len(costs), cache_hits=0,
            gradient=gradient.tolist(), gradient_norm=norm,
            gradient_gain_component=float(gradient[-1]),
            target_program=center.tolist(), target_cost=float(costs[0]), target_true_mse=0.,
            next_program=next_program.tolist(), actual_program_step_norm=float(np.linalg.norm(next_program-center)),
            next_cost=float(costs[-1]), cost_change=float(costs[-1]-costs[0]),
            next_true_mse=float(losses[-1]), true_mse_change=float(losses[-1]))
        all_actions.append(actions)
        all_costs.append(costs)
        all_losses.append(losses)
        all_gradients.append(gradient)
    np.savez(npz_path, evaluators=np.asarray(DIAGNOSTIC_CONFIG["evaluators"]),
        query_actions=np.asarray(all_actions), query_costs=np.asarray(all_costs),
        query_true_losses=np.asarray(all_losses), gradients=np.asarray(all_gradients),
        target_program=center,
        query_types=np.asarray(["center"] + [f"{sign}_{d}" for d in range(base.DIM+1)
                              for sign in ("plus", "minus")] + ["downhill_step"]))
    target_features = state["target_features"]
    out = dict(plant_id=plant_id, diagnostic_config=DIAGNOSTIC_CONFIG,
        source_directory=str(source_dir.resolve()), source_state_sha256=base.sha(state_path),
        script_sha256=base.sha(__file__), source_hashes=state["source_hashes"],
        target_feature_mean_per_context=target_features.mean(axis=-1).tolist(),
        target_feature_sd_per_context=target_features.std(axis=-1).tolist(),
        target_feature_l2_per_context=np.linalg.norm(target_features, axis=-1).tolist(),
        target_feature_mean_square=float(np.mean(target_features**2)),
        target_true_mse=0., evaluators=summaries,
        feedback_queries_total=sum(s["feedback_queries"] for s in summaries.values()),
        source_and_actor_files_modified=False)
    base.atomic_json(json_path, out)
    print(json.dumps(dict(plant=plant_id, diagnostic_queries=out["feedback_queries_total"],
        output=str(json_path), evaluators=summaries)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plants", nargs="+", required=True, type=int)
    parser.add_argument("--base-dir", type=Path, default=HERE/"mixed_results")
    parser.add_argument("--output-dir", type=Path, default=HERE/"diagnostic_results")
    args = parser.parse_args()
    base_dir = args.base_dir
    if not base_dir.is_absolute() and not base_dir.exists():
        base_dir = HERE/base_dir
    output_dir = args.output_dir
    for plant_id in args.plants:
        diagnose(plant_id, base_dir, output_dir)


if __name__ == "__main__":
    main()
