"""Replay frozen source circuits and actors into a new isolated directory.

This is exact software reproduction of already consumed synthetic evidence. It
does not create independent scientific data or restore validation status. The
authoritative scripts, source paths and result files are never modified.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import pickle
import sys
import time

CAMPAIGN = Path(__file__).resolve().parent
ARM_NAMES = ("oracle_joint", "learned35_joint", "learned35_fixed",
             "learned140_joint", "untutored_joint", "shuffled35_joint")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_redirected_runner(output_dir):
    """Redirect result roots only; source ROOT and HELPER_PATH remain unchanged."""
    spec = importlib.util.spec_from_file_location(
        "isolated_reproduction_mixed_runner", CAMPAIGN/"run_mixed.py")
    runner = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = runner
    spec.loader.exec_module(runner)
    runner.HERE = Path(output_dir)
    runner.base.HERE = Path(output_dir)
    return runner


def compare_plant(runner, plant_id, rounds, arms, output_dir):
    """Check every frozen numerical object and requested actor prefix exactly."""
    np = runner.np
    from scipy.sparse import issparse
    fresh = output_dir/"mixed_results"/f"plant_{plant_id:03d}"
    authoritative = CAMPAIGN/"mixed_results"/f"plant_{plant_id:03d}"
    checks = []

    def require(name, condition):
        checks.append(dict(check=name, passed=bool(condition)))
        if not condition:
            raise AssertionError(f"Reproduction mismatch, plant{plant_id}: {name}")

    def exact_array(name, actual, expected):
        actual, expected = np.asarray(actual), np.asarray(expected)
        require(name, actual.shape == expected.shape and actual.dtype == expected.dtype
                and actual.tobytes(order="C") == expected.tobytes(order="C"))

    require("authoritative_directory_exists", authoritative.is_dir())
    with np.load(fresh/"inputs.npz") as actual, np.load(authoritative/"inputs.npz") as expected:
        require("input_array_names", set(actual.files) == set(expected.files))
        for key in expected.files:
            exact_array(f"inputs.{key}", actual[key], expected[key])
    with (fresh/"state.pkl").open("rb") as f:
        actual_state = pickle.load(f)
    with (authoritative/"state.pkl").open("rb") as f:
        expected_state = pickle.load(f)
    for key in ("config", "source_hashes", "plant_id", "seed"):
        require(f"state.{key}", actual_state[key] == expected_state[key])
    require("current_source_hashes_match", actual_state["source_hashes"] ==
            runner.base.source_hashes())
    for key in ("basis", "bias", "target", "initial", "rh", "initial_hE", "initial_hI",
                "target_features"):
        exact_array(f"state.{key}", actual_state[key], expected_state[key])
    require("all_four_evaluator_names", set(actual_state["nets"]) ==
            set(expected_state["nets"]) == {"untutored", "learned35", "learned140", "shuffled35"})
    for name in expected_state["nets"]:
        actual_net, expected_net = actual_state["nets"][name], expected_state["nets"][name]
        require(f"net.{name}.attribute_names", set(vars(actual_net)) == set(vars(expected_net)))
        for key, expected_value in vars(expected_net).items():
            actual_value = getattr(actual_net, key)
            if issparse(expected_value):
                require(f"net.{name}.{key}.format_shape", issparse(actual_value)
                        and actual_value.format == expected_value.format
                        and actual_value.shape == expected_value.shape)
                for component in ("data", "indices", "indptr"):
                    exact_array(f"net.{name}.{key}.{component}", getattr(actual_value, component),
                                getattr(expected_value, component))
            elif isinstance(expected_value, np.ndarray):
                exact_array(f"net.{name}.{key}", actual_value, expected_value)
            else:
                require(f"net.{name}.{key}", actual_value == expected_value)
        for component in ("hE", "hI"):
            exact_array(f"probe_states.{name}.{component}",
                        actual_state["probe_states"][name][component],
                        expected_state["probe_states"][name][component])
    query_count, trajectory_count = 1+10*rounds, rounds+1
    for arm in arms:
        summary = json.loads((fresh/f"{arm}.json").read_text())
        original_summary = json.loads((authoritative/f"{arm}.json").read_text())
        require(f"{arm}.exact_requested_rounds", summary["rounds"] == rounds)
        require(f"{arm}.exact_feedback_budget", summary["queries"] == query_count)
        require(f"{arm}.authoritative_has_requested_prefix", original_summary["rounds"] >= rounds)
        require(f"{arm}.actor_config", summary["actor_config"] == original_summary["actor_config"])
        require(f"{arm}.broad_candidates_hash", summary["broad_candidates_sha256"] ==
                original_summary["broad_candidates_sha256"])
        require(f"{arm}.frozen_actor_script_hash", summary["actor_script_sha256"] ==
                original_summary["actor_script_sha256"] == sha(CAMPAIGN/"run_mixed.py"))
        execution = summary["feedback_execution"]
        require(f"{arm}.execution_slot_count", execution["feedback_calls"] == query_count)
        require(f"{arm}.execution_accounting", execution["real_source_calls"] +
                execution["oracle_evaluations"] + execution["cache_hits"] == query_count)
        for suffix, count in (("queries", query_count), ("trajectory", trajectory_count)):
            with np.load(fresh/f"{arm}_{suffix}.npz") as actual, np.load(
                    authoritative/f"{arm}_{suffix}.npz") as expected:
                require(f"{arm}.{suffix}.field_names", set(actual.files) == set(expected.files))
                for key in expected.files:
                    require(f"{arm}.{suffix}.{key}.exact_length", len(actual[key]) == count)
                    exact_array(f"{arm}.{suffix}.{key}.prefix", actual[key], expected[key][:count])
        with (fresh/f"{arm}_checkpoint.pkl").open("rb") as f:
            checkpoint = pickle.load(f)
        require(f"{arm}.checkpoint_rounds", checkpoint["round"] == rounds)
        require(f"{arm}.checkpoint_queries", len(checkpoint["query_costs"]) == query_count)
    return dict(plant_id=plant_id, passed=True, checks=checks,
                comparison="byte-exact numerical objects and requested actor prefixes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="new nonexistent directory; authoritative evidence is never overwritten")
    parser.add_argument("--plants", nargs="+", type=int, required=True)
    parser.add_argument("--rounds", type=int, choices=[64, 128], default=64)
    parser.add_argument("--arms", nargs="+", choices=ARM_NAMES)
    parser.add_argument("--memoize", action="store_true")
    parser.add_argument("--compare-authoritative", action="store_true")
    args = parser.parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    if output_dir.exists():
        parser.error("--output-dir must be new and nonexistent")
    output_dir.mkdir(parents=True)
    frozen_paths = [CAMPAIGN/"run.py", CAMPAIGN/"run_mixed.py"]
    frozen_hashes = {str(p): sha(p) for p in frozen_paths}
    start = time.perf_counter()
    report = dict(status="running", plants=args.plants, rounds=args.rounds,
        arms=args.arms or list(ARM_NAMES), memoize=args.memoize,
        compare_authoritative=args.compare_authoritative, output_directory=str(output_dir),
        frozen_script_hashes=frozen_hashes, reproduction_wrapper_sha256=sha(__file__),
        scientific_status="exact software verification; no independent data or restored validation",
        plants_completed=[], comparisons=[])
    runner = None
    try:
        runner = load_redirected_runner(output_dir)
        for plant_id in args.plants:
            directory = output_dir/"mixed_results"/f"plant_{plant_id:03d}"
            state = runner.prepare(plant_id, directory)
            for arm in report["arms"]:
                runner.optimize(directory, arm, args.rounds, state, args.memoize)
            report["plants_completed"].append(plant_id)
            if args.compare_authoritative:
                report["comparisons"].append(compare_plant(runner, plant_id, args.rounds,
                    report["arms"], output_dir))
        if frozen_hashes != {str(p): sha(p) for p in frozen_paths}:
            raise RuntimeError("Frozen source script changed during reproduction")
        report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["elapsed_seconds"] = time.perf_counter()-start
        (output_dir/"REPRODUCTION.json").write_text(json.dumps(report, indent=2,
                                                             allow_nan=False)+"\n")
        print(json.dumps(dict(status=report["status"], report=str(output_dir/"REPRODUCTION.json"))),
              flush=True)


if __name__ == "__main__":
    main()
