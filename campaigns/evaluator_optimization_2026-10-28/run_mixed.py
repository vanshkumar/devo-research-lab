"""One prespecified mixed global/local scalar-feedback optimizer revision.

The source plants, training, rewards and six arms are unchanged. Every fourth
round uses a shared target-blind broad proposal batch to escape flat gain-zero
basins. Other rounds use the original coordinate proposals. All proposal slots
count toward the same feedback budget, including cached duplicates.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import pickle
import shutil
import sys
import time

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("evaluator_original_runner", HERE / "run.py")
base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = base
_spec.loader.exec_module(base)
np = base.np

ACTOR_CONFIG = dict(
    name="mixed_global_coordinate_v1",
    global_rounds="4,8,...,128 (one based)", global_batch_count=32,
    global_seed_rule="71000+plant_id", global_batch_shape=[10, 5],
    global_distribution="iid uniform per coordinate over the search bounds",
    global_lower=base.CONFIG["lower"], global_upper=base.CONFIG["upper"],
    fixed_gain_global_value=1., global_failure="retain local step unchanged",
    global_success="accept strict improvement and reset local step to .4",
    local_proposals="+ then - per coordinate0..4; fixed gain slots repeat center",
    local_failure="halve step to floor .00625", initial_step=.4,
    min_step=.00625, accept="strictly smaller scalar cost; first argmin tie",
    queries_per_round=10, initial_queries=1,
    target_information="same scalar feedback, plant, tutor exposure and clock as original",
)


def broad_candidates(plant_id):
    """Draw every permitted broad batch before search; no reward is consumed."""
    rng = np.random.default_rng(71000 + plant_id)
    return rng.uniform(np.asarray(ACTOR_CONFIG["global_lower"]),
                       np.asarray(ACTOR_CONFIG["global_upper"]), size=(32, 10, 5))


def prepare(plant_id, directory):
    """Reuse the exact source preparation; keep mixed actor outputs separate."""
    original = HERE / "results" / f"plant_{plant_id:03d}"
    state = base.prepare(plant_id, original)
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ("inputs.npz", "state.pkl", "preparation.json"):
        src, dst = original / filename, directory / filename
        if dst.exists():
            if base.sha(src) != base.sha(dst):
                raise RuntimeError(f"Source preparation copy differs: {dst}")
        else:
            shutil.copy2(src, dst)
    return state


def save_actor(directory, arm, actor, state):
    base.atomic_pickle(directory / f"{arm}_checkpoint.pkl", actor)
    q_actions = np.asarray(actor["query_actions"])
    t_actions = np.asarray(actor["trajectory_actions"])
    q_losses = base.true_losses(q_actions, state)
    t_losses = base.true_losses(t_actions, state)
    np.savez(directory / f"{arm}_queries.npz", actions=q_actions,
             costs=np.asarray(actor["query_costs"]), true_losses=q_losses)
    np.savez(directory / f"{arm}_trajectory.npz", actions=t_actions,
             costs=np.asarray(actor["trajectory_costs"]),
             steps=np.asarray(actor["trajectory_steps"]),
             queries=np.asarray(actor["trajectory_queries"]), true_losses=t_losses,
             round_types=np.asarray(actor["trajectory_round_types"]))
    initial_loss, end_loss = float(t_losses[0]), float(t_losses[-1])
    summary = dict(arm=arm, rounds=actor["round"], queries=len(q_actions),
        query_budget_expected=1+10*actor["round"],
        initial_action=t_actions[0].tolist(), final_action=t_actions[-1].tolist(),
        initial_cost=float(actor["trajectory_costs"][0]), final_cost=float(actor["cost"]),
        final_step=float(actor["step"]), initial_true_loss=initial_loss,
        final_true_loss=end_loss,
        normalized_final_true_loss=end_loss/initial_loss if initial_loss else None,
        fraction_true_improvement=1-end_loss/initial_loss if initial_loss else None,
        information="search consumes scalar callback; true_loss is offline scorer",
        feedback_execution=actor["feedback_execution"],
        source_hashes=state["source_hashes"], config=base.CONFIG,
        actor_config=ACTOR_CONFIG, actor_script_sha256=actor["actor_script_sha256"],
        broad_candidates_sha256=actor["broad_candidates_sha256"])
    base.atomic_json(directory / f"{arm}.json", summary)


def optimize(directory, arm, rounds, state, memoize=False):
    broad = broad_candidates(state["plant_id"])
    broad_sha = base.hashlib.sha256(broad.tobytes()).hexdigest()
    raw_callback = base.feedback(arm, state)
    checkpoint = directory / f"{arm}_checkpoint.pkl"
    if checkpoint.exists():
        with checkpoint.open("rb") as f:
            actor = pickle.load(f)
        if (actor["config"] != base.CONFIG or actor["actor_config"] != ACTOR_CONFIG
                or actor["broad_candidates_sha256"] != broad_sha):
            raise RuntimeError("Cannot resume mixed actor with changed scientific configuration")
        callback, stats = base.execution_callback(raw_callback, arm, memoize,
            actor["query_actions"], actor["query_costs"], actor["feedback_execution"])
        actor["feedback_execution"] = stats
    else:
        callback, stats = base.execution_callback(raw_callback, arm, memoize)
        x = np.r_[state["initial"], 1.]
        cost = callback(x)
        actor = dict(config=base.CONFIG, actor_config=ACTOR_CONFIG,
            actor_script_sha256=base.sha(__file__), broad_candidates_sha256=broad_sha,
            x=x, cost=cost, step=.4, round=0, query_actions=[x.copy()],
            query_costs=[cost], trajectory_actions=[x.copy()], trajectory_costs=[cost],
            trajectory_steps=[.4], trajectory_queries=[1],
            trajectory_round_types=["initial"], feedback_execution=stats)
    if actor["round"] >= rounds:
        save_actor(directory, arm, actor, state)
        return
    lower, upper = np.asarray(base.CONFIG["lower"]), np.asarray(base.CONFIG["upper"])
    start = time.perf_counter()
    for r in range(actor["round"], rounds):
        is_global = (r+1) % 4 == 0
        if is_global:
            proposals = broad[r//4].copy()
            if arm.endswith("_fixed"):
                proposals[:, base.DIM] = 1.
        else:
            proposals = []
            for d in range(base.DIM+1):
                for sign in (1., -1.):
                    candidate = actor["x"].copy()
                    if not (arm.endswith("_fixed") and d == base.DIM):
                        candidate[d] += sign*actor["step"]
                    proposals.append(np.clip(candidate, lower, upper))
        costs = []
        for candidate in proposals:
            cost = callback(candidate)
            if not np.isfinite(cost):
                raise FloatingPointError(f"Nonfinite mixed feedback: {state['plant_id']} {arm}")
            costs.append(cost)
            actor["query_actions"].append(candidate.copy())
            actor["query_costs"].append(cost)
        best = int(np.argmin(costs))
        if costs[best] < actor["cost"]:
            actor["x"] = proposals[best].copy()
            actor["cost"] = costs[best]
            if is_global:
                actor["step"] = .4
        elif not is_global:
            actor["step"] = max(.00625, actor["step"]/2.)
        actor["round"] = r+1
        actor["trajectory_actions"].append(actor["x"].copy())
        actor["trajectory_costs"].append(actor["cost"])
        actor["trajectory_steps"].append(actor["step"])
        actor["trajectory_queries"].append(len(actor["query_actions"]))
        actor["trajectory_round_types"].append("global" if is_global else "local")
        if (r+1) % 8 == 0 or r+1 == rounds:
            save_actor(directory, arm, actor, state)
            print(json.dumps(dict(plant=state["plant_id"], arm=arm, round=r+1,
                algorithm=ACTOR_CONFIG["name"], cost=float(actor["cost"]),
                step=float(actor["step"]), seconds=time.perf_counter()-start)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plant", type=int, required=True)
    parser.add_argument("--rounds", type=int, choices=[0, 1, 8, 16, 32, 64, 128], default=64)
    parser.add_argument("--arms", nargs="+", choices=base.ARMS, default=list(base.ARMS))
    parser.add_argument("--memoize", action="store_true")
    args = parser.parse_args()
    directory = HERE / "mixed_results" / f"plant_{args.plant:03d}"
    state = prepare(args.plant, directory)
    for arm in args.arms:
        optimize(directory, arm, args.rounds, state, args.memoize)


if __name__ == "__main__":
    main()
