"""Matched scalar-feedback optimization on independently drawn reachable plants.

Source network dynamics and plasticity are imported unchanged. Locally generated
pickles are trusted campaign state; no external pickle is read. Target losses are
computed after actor updates, and never passed to a circuit-reward actor.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pickle
import sys
import time

# Set before numerical libraries are imported. Each plant is a separate process.
for _var in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
             "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_var] = "1"

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HELPER_PATH = ROOT / "experiments/sensory_evaluator_preflight_2026-10-28/preflight.py"
_spec = importlib.util.spec_from_file_location("evaluator_preflight_helper", HELPER_PATH)
helper = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = helper
_spec.loader.exec_module(helper)

DIM = 4
ARMS = ("oracle_joint", "learned35_joint", "learned35_fixed",
        "learned140_joint", "untutored_joint", "shuffled35_joint")
CONFIG = dict(motor_dimension=DIM, contexts=6, sensory_channels=100,
              seed_rule="31000+plant_id", initial_step=.4, min_step=.00625,
              lower=[-2., -2., -2., -2., 0.],
              upper=[2., 2., 2., 2., 2.], queries_per_round=10,
              tutor_renditions=[35, 140], shuffled_context_roll=1,
              training="literal independent35/140/shuffled35 from identical initial state",
              training_clock="one impending rendition included before truncation; exact35/140prefix",
              scoring="mean of six source120ms context windows",
              zero_dynamical_noise=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def atomic_pickle(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as f:
        pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
    tmp.replace(path)


def source_hashes():
    return {str(p.relative_to(ROOT)): sha(p) for p in [HELPER_PATH] + sorted(
        p for p in helper.SOURCE.rglob("*")
        if p.is_file() and "__pycache__" not in str(p))}


def features(action, basis, bias):
    """A fixed independently sampled six-context motor-program map."""
    y = np.maximum(np.einsum("...d,scd->...sc", action, basis) + bias, 0.)
    y -= y.mean(axis=-1, keepdims=True)
    return 2 * y / np.maximum(y.std(axis=-1, keepdims=True), 1e-12)


def auditory_from_features(y):
    aud = np.zeros((helper.T_SONG + helper.T_POST, helper.NE))
    projected = np.repeat(y, helper.NE // helper.NC, axis=-1)
    for s, (on, off) in enumerate(zip(helper.ON, helper.OFF)):
        aud[on:off] = projected[s]
    return aud


def source_training(net, hE0, hI0, target_features, means, renditions):
    aud_one = auditory_from_features(target_features)
    aud_train = np.concatenate([np.zeros((helper.T_BURN, helper.NE)),
                                np.tile(aud_one, (renditions, 1))])
    # Include the impending next rendition before truncation. Without this,
    # Gaussian clock tails near the35-rendition endpoint differ from the
    # corresponding prefix of140-rendition tutoring.
    rh_train = helper.hvc(renditions+1, helper.T_BURN)[:len(aud_train)]
    start = time.perf_counter()
    res = net.sim(hE0, hI0, rh_train, aud_train, [], len(aud_train), 1, 0,
        plasticity={"JEI": helper.bilin_hebb_EI, "JIE": helper.bilin_hebb_IE},
        lr={"JEI": 5e-2, "JIE": 6e-3}, tauW=1e5,
        JEI0_mean=means[1], JIE0_mean=means[2],
        asyn_E=10, asyn_I=0, rE_th=1.5, rI_th=5,
        no_progress_bar=True)
    seconds = time.perf_counter() - start
    del res, aud_train, rh_train
    return seconds


def prepare(plant_id, directory):
    """Fix the plant, draw target and start, then initialize an independent net."""
    state_path = directory / "state.pkl"
    if state_path.exists():
        with state_path.open("rb") as f:
            state = pickle.load(f)
        if state["config"] != CONFIG or state["source_hashes"] != source_hashes():
            raise RuntimeError("Existing generated state has different config/source; preserve it.")
        return state
    if (directory / "inputs.npz").exists():
        # Preparation might have stopped before writing state. Regeneration is
        # deterministic; no outcomes or selected target enter this branch.
        pass
    directory.mkdir(parents=True, exist_ok=True)
    seed = 31000 + plant_id
    np.random.seed(seed)
    rng = np.random.default_rng(seed)
    basis = rng.normal(size=(helper.NS, helper.NC, DIM)) / np.sqrt(DIM)
    bias = rng.normal(-.4, .2, (helper.NS, helper.NC))
    target = rng.uniform(-1., 1., DIM)
    initial = rng.uniform(-1., 1., DIM)
    np.savez(directory / "inputs.npz", basis=basis, bias=bias, target=target,
             initial=initial, on=helper.ON, off=helper.OFF, seed=seed)
    net0, means = helper.initialize(rng)
    hE0 = rng.normal(-10, .5, helper.NE)
    hI0 = rng.normal(-1, .5, helper.NI)
    target_features = features(target, basis, bias)
    nets = {"untutored": net0}
    timing = {}
    for name, renditions, tutor in (
            ("learned35", 35, target_features),
            ("learned140", 140, target_features),
            ("shuffled35", 35, np.roll(target_features, 1, axis=0))):
        net = copy.deepcopy(net0)
        seconds = source_training(net, hE0, hI0, tutor, means, renditions)
        nets[name] = net
        timing[name] = seconds
        print(json.dumps(dict(plant=plant_id, stage="trained", evaluator=name,
                              seconds=seconds)), flush=True)
    rh_full = helper.hvc(1, helper.T_BURN)
    rh = rh_full[helper.T_BURN:]
    probe_states, target_costs = {}, {}
    for name, net in nets.items():
        res = net.sim(hE0, hI0, rh_full[:helper.T_BURN],
                      np.zeros((helper.T_BURN, helper.NE)), [], helper.T_BURN,
                      1, 0, no_progress_bar=True)
        hE, hI = res[-2:]
        probe_states[name] = dict(hE=hE, hI=hI)
        scores, seconds = helper.run_frozen(
            net, auditory_from_features(target_features), hE, hI, rh)
        target_costs[name] = dict(mean=float(scores.mean()),
                                  contexts=scores.tolist(), seconds=seconds)
        del res
    state = dict(config=CONFIG, source_hashes=source_hashes(), plant_id=plant_id,
                 seed=seed, basis=basis, bias=bias, target=target, initial=initial,
                 nets=nets, probe_states=probe_states, rh=rh,
                 initial_hE=hE0, initial_hI=hI0, target_features=target_features)
    atomic_pickle(state_path, state)
    initial_loss = float(np.mean((features(initial, basis, bias)-target_features)**2))
    summary = dict(plant_id=plant_id, seed=seed, config=CONFIG,
                   source_hashes=state["source_hashes"], training_seconds=timing,
                   target_costs=target_costs, initial_true_loss=initial_loss,
                   target_reachable_true_loss=0.,
                   learned35_suppression=1-target_costs["learned35"]["mean"] /
                   target_costs["untutored"]["mean"])
    atomic_json(directory / "preparation.json", summary)
    return state


def true_losses(actions, state):
    y = features(np.asarray(actions)[..., :DIM], state["basis"], state["bias"])
    gain = np.asarray(actions)[..., DIM, None, None]
    return np.mean((gain*y-state["target_features"])**2, axis=(-2, -1))


def feedback(arm, state):
    """Return only the reward callback consumed by the search algorithm."""
    if arm == "oracle_joint":
        # The oracle alone is intentionally given the target objective.
        return lambda x: float(true_losses(x, state))
    evaluator = arm.rsplit("_", 1)[0]
    net = state["nets"][evaluator]
    h = state["probe_states"][evaluator]
    basis, bias, rh = state["basis"], state["bias"], state["rh"]
    def callback(x):
        y = x[DIM] * features(x[:DIM], basis, bias)
        scores, _ = helper.run_frozen(net, auditory_from_features(y),
                                     h["hE"], h["hI"], rh)
        return float(scores.mean())
    return callback


def execution_callback(raw_callback, arm, memoize=False, query_actions=(),
                       query_costs=(), previous_stats=None):
    """Exact deterministic memoization; every feedback slot still counts.

    Seeding uses only previously queried actions/costs, never target loss.
    Execution counters are provenance, outside the scientific CONFIG/search.
    """
    oracle = arm == "oracle_joint"
    if previous_stats is None:
        stats = dict(feedback_calls=len(query_costs),
                     real_source_calls=0 if oracle else len(query_costs),
                     oracle_evaluations=len(query_costs) if oracle else 0,
                     cache_hits=0)
    else:
        stats = dict(previous_stats)
    cache = {}
    if memoize:
        for action, cost in zip(query_actions, query_costs):
            key = np.ascontiguousarray(action).tobytes()
            if key in cache and cache[key] != cost:
                raise RuntimeError("Identical saved query has unequal deterministic costs")
            cache[key] = cost
    def callback(x):
        stats["feedback_calls"] += 1
        key = np.ascontiguousarray(x).tobytes()
        if memoize and key in cache:
            stats["cache_hits"] += 1
            return cache[key]
        cost = raw_callback(x)
        stats["oracle_evaluations" if oracle else "real_source_calls"] += 1
        if memoize:
            cache[key] = cost
        return cost
    return callback, stats


def save_actor(directory, arm, actor, state):
    """Offline scorer; its outputs are never read by a circuit actor."""
    atomic_pickle(directory / f"{arm}_checkpoint.pkl", actor)
    q_actions = np.asarray(actor["query_actions"])
    t_actions = np.asarray(actor["trajectory_actions"])
    q_losses = true_losses(q_actions, state)
    t_losses = true_losses(t_actions, state)
    np.savez(directory / f"{arm}_queries.npz", actions=q_actions,
             costs=np.asarray(actor["query_costs"]), true_losses=q_losses)
    np.savez(directory / f"{arm}_trajectory.npz", actions=t_actions,
             costs=np.asarray(actor["trajectory_costs"]),
             steps=np.asarray(actor["trajectory_steps"]),
             queries=np.asarray(actor["trajectory_queries"]), true_losses=t_losses)
    initial_loss = float(t_losses[0])
    end_loss = float(t_losses[-1])
    summary = dict(arm=arm, rounds=actor["round"], queries=len(q_actions),
                   query_budget_expected=1+10*actor["round"],
                   initial_action=t_actions[0].tolist(),
                   final_action=t_actions[-1].tolist(),
                   initial_cost=float(actor["trajectory_costs"][0]),
                   final_cost=float(actor["cost"]), final_step=float(actor["step"]),
                   initial_true_loss=initial_loss, final_true_loss=end_loss,
                   normalized_final_true_loss=end_loss/initial_loss if initial_loss else None,
                   fraction_true_improvement=1-end_loss/initial_loss if initial_loss else None,
                   information="search consumes only callback scalar; true_loss is offline scorer",
                   feedback_execution=actor.get("feedback_execution"),
                   source_hashes=state["source_hashes"], config=CONFIG)
    atomic_json(directory / f"{arm}.json", summary)


def optimize(directory, arm, rounds, state, memoize=False):
    raw_callback = feedback(arm, state)
    checkpoint = directory / f"{arm}_checkpoint.pkl"
    if checkpoint.exists():
        with checkpoint.open("rb") as f:
            actor = pickle.load(f)
        if actor["config"] != CONFIG:
            raise RuntimeError("Cannot resume actor with changed config")
        callback, execution_stats = execution_callback(
            raw_callback, arm, memoize, actor["query_actions"],
            actor["query_costs"], actor.get("feedback_execution"))
        actor["feedback_execution"] = execution_stats
    else:
        callback, execution_stats = execution_callback(raw_callback, arm, memoize)
        x = np.r_[state["initial"], 1.]
        cost = callback(x)
        actor = dict(config=CONFIG, x=x, cost=cost, step=CONFIG["initial_step"], round=0,
                     query_actions=[x.copy()], query_costs=[cost],
                     trajectory_actions=[x.copy()], trajectory_costs=[cost],
                     trajectory_steps=[CONFIG["initial_step"]], trajectory_queries=[1],
                     feedback_execution=execution_stats)
    if actor["round"] >= rounds:
        save_actor(directory, arm, actor, state)
        return
    lower, upper = np.asarray(CONFIG["lower"]), np.asarray(CONFIG["upper"])
    start = time.perf_counter()
    for r in range(actor["round"], rounds):
        x = actor["x"]
        proposals, costs = [], []
        for d in range(DIM+1):
            for sign in (1., -1.):
                candidate = x.copy()
                if not (arm.endswith("_fixed") and d == DIM):
                    candidate[d] += sign * actor["step"]
                candidate = np.clip(candidate, lower, upper)
                cost = callback(candidate)
                if not np.isfinite(cost):
                    raise FloatingPointError(f"Nonfinite feedback: plant{state['plant_id']} {arm}")
                proposals.append(candidate)
                costs.append(cost)
                actor["query_actions"].append(candidate.copy())
                actor["query_costs"].append(cost)
        best = int(np.argmin(costs))
        if costs[best] < actor["cost"]:
            actor["x"] = proposals[best].copy()
            actor["cost"] = costs[best]
        else:
            actor["step"] = max(CONFIG["min_step"], actor["step"] / 2.)
        actor["round"] = r+1
        actor["trajectory_actions"].append(actor["x"].copy())
        actor["trajectory_costs"].append(actor["cost"])
        actor["trajectory_steps"].append(actor["step"])
        actor["trajectory_queries"].append(len(actor["query_actions"]))
        if (r+1) % 8 == 0 or r+1 == rounds:
            save_actor(directory, arm, actor, state)
            print(json.dumps(dict(plant=state["plant_id"], arm=arm, round=r+1,
                                  cost=float(actor["cost"]), step=float(actor["step"]),
                                  seconds=time.perf_counter()-start)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plant", type=int, required=True)
    parser.add_argument("--rounds", type=int, choices=[0, 1, 8, 16, 32, 64, 128], default=32)
    parser.add_argument("--arms", nargs="+", choices=ARMS, default=list(ARMS))
    parser.add_argument("--memoize", action="store_true",
                        help="reuse exactly identical deterministic feedback, counting every query")
    args = parser.parse_args()
    directory = HERE / "results" / f"plant_{args.plant:03d}"
    state = prepare(args.plant, directory)
    for arm in args.arms:
        optimize(directory, arm, args.rounds, state, memoize=args.memoize)


if __name__ == "__main__":
    main()
