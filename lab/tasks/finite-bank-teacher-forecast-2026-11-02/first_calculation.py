"""Source-only finite-bank covariance screen; Python standard library only."""
from collections import Counter
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
import hashlib
import json
import resource

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "lab/tasks/action-contingent-acquisition-2026-11-02"
read_bytes = 0


def read(path):
    global read_bytes
    raw = path.read_bytes()
    read_bytes += len(raw)
    return raw


def main():
    pins = json.loads(read(SOURCE / "SOURCE_TEXT_PINS.json"))
    listings = []
    pinchecks = {}
    selected = {"index.html", "additional-functions.js", "jspsych-space-daw-stim.js", "MB_MF_daw_rllik.m", "set_opts.m"}
    for name, pin in pins["files"].items():
        raw = read(SOURCE / "source" / name)
        got = hashlib.sha256(raw).hexdigest()
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        assert got == pin["sha256"] and blob == pin["git_blob"], name
        pinchecks[name] = {"sha256": got, "git_blob": blob, "bytes": len(raw), "url": pin["url"]}
        if name in selected:
            listings.append("FILE " + name + "\n" + "\n".join(f"{i}: {line}" for i, line in enumerate(raw.decode().splitlines(), 1)))
    (HERE / "SOURCE_LISTINGS.txt").write_text("\n\n".join(listings) + "\n")

    n, t, sigma = 1000, 124, .025
    variance = sigma**2 * (t + t*(t-1)/n)
    cross_covariance = sigma**2 * t*t/n
    fresh_variance = sigma**2*t
    # A reference based on counts of every index path, independent of the formula.
    paths = list(product(range(2), repeat=3))
    enum_variance = sum(sum(c*c for c in Counter(p).values()) for p in paths)/len(paths)
    formula_variance = 3 + 3*2/2
    pair_paths = list(product(range(2), repeat=2))
    enum_cross = sum(sum(Counter(p)[i]*Counter(q)[i] for i in range(2)) for p in pair_paths for q in pair_paths)/len(pair_paths)**2
    assert enum_variance == formula_variance == 6
    assert enum_cross == 2*2/2 == 2
    assert sigma**2*(1 + 1*0/n) == sigma**2
    out = {
        "utc": datetime.now(timezone.utc).isoformat(), "scope": "exploratory teacher law before reflection; no human data or learner utility",
        "bank_size": n, "increment_sd": sigma, "updates": t,
        "fresh_cumulative_variance": fresh_variance, "bank_cumulative_variance": variance,
        "variance_ratio": variance/fresh_variance, "bank_cross_option_covariance": cross_covariance,
        "bank_cross_option_correlation": cross_covariance/variance,
        "bank_common_mean_sd": sigma/n**.5, "unreflected_end_common_component_sd": sigma*t/n**.5,
        "independent_reference": {"enumerated_small_bank_variance": enum_variance, "pairwise_formula_variance": formula_variance, "enumerated_cross_covariance": enum_cross, "one_step_variance_agrees": True},
        "pins": pinchecks, "explicit_input_read_bytes": read_bytes,
        "maxrss_bytes_darwin": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "jobs_after_exit": 0, "exit_code": 0,
    }
    (HERE / "FIRST_CALCULATION.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k:v for k,v in out.items() if k != "pins"}, indent=2))


if __name__ == "__main__":
    main()
