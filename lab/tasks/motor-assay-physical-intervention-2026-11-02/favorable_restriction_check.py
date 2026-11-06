"""One exact favorable restriction check; standard library; no raw data."""
from fractions import Fraction as F
from pathlib import Path
import datetime
import hashlib
import json
import resource

ROOT = Path(__file__).resolve().parent
raw = (ROOT / "PROTOCOL_INPUTS.json").read_bytes()
p = json.loads(raw)["honda_2012_delay_program"]
delays = [p["reported_system_delay_ms"] + d for d in p["additional_delay_ms"]]
Uminus, Uplus = map(F, p["perturbation_angle_degrees"])
# Two of the source delay levels suffice for this positive control.
supplied_a, supplied_c = F(97, 100), F(1, 2)
supplied_b = [F(1, 5), F(1, 10)]
Xminus, Xplus = F(-3, 2), F(3, 2)
cells = []
recovered = []
for delay, b in zip((delays[0], delays[-1]), supplied_b):
    table = {}
    for x in (Xminus, Xplus):
        for u in (Uminus, Uplus):
            table[(x, u)] = supplied_a*x + b*(u-supplied_c*x)
            cells.append({"delay_ms": delay, "X": str(x), "U": str(u),
                          "Y": str(table[(x, u)])})
    # Estimation consumes observable cell means and known randomization only.
    bhat = (table[(Xplus,Uplus)]-table[(Xplus,Uminus)])/(Uplus-Uminus)
    khat = (table[(Xplus,Uplus)]-table[(Xminus,Uplus)])/(Xplus-Xminus)
    recovered.append((bhat, khat))

(b1,k1),(b2,k2) = recovered
assert b1 != b2
chat = (k1-k2)/(b2-b1)
ahat = k1+b1*chat
assert (ahat,chat) == (supplied_a,supplied_c)

# A distinct unchanged-across-delay intrinsic coefficient with delay-specific
# internal predicted-error loadings reproduces EVERY same observable cell.
alternate_a = F(9, 10)
alternate_c = [supplied_c+(alternate_a-supplied_a)/b for b in supplied_b]
gaps = []
for b,cnew in zip(supplied_b,alternate_c):
    for x in (Xminus,Xplus):
        for u in (Uminus,Uplus):
            original = supplied_a*x+b*(u-supplied_c*x)
            alternate = alternate_a*x+b*(u-cnew*x)
            gaps.append(original-alternate)
assert set(gaps) == {F(0)}
out = {
    "completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "protocol_input_sha256": hashlib.sha256(raw).hexdigest(),
    "status": "PASS: favorable invariant-loading model separates; relaxed loading reproduces it exactly",
    "predeclaration": "CONTRARY_PREDECLARATION.md",
    "supplied_not_empirical": True,
    "observable_cells": cells,
    "recovered_from_observations": {"a":str(ahat),"c":str(chat),
                                    "b":list(map(str,(b1,b2))),
                                    "k":list(map(str,(k1,k2)))},
    "distinct_relaxed_world": {"a":str(alternate_a),"c_by_delay":list(map(str,alternate_c)),
                               "b_unchanged":True,"max_exact_observation_gap":str(max(map(abs,gaps)))},
    "restriction_needed": "Unit physical-input/error transfer, c invariant across delays, and a unaffected by delay",
    "restriction_source_certified": False,
    "empirical_records_accessed": 0,
    "peak_rss_bytes_this_process": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    "platform_peak_units": "macOS bytes",
}
(ROOT/"CONTRARY.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({"status":out["status"],"completed_utc":out["completed_utc"],
                  "recovered_a":str(ahat),"recovered_c":str(chat),
                  "relaxed_gap":str(max(map(abs,gaps))),
                  "peak_rss_bytes":out["peak_rss_bytes_this_process"]}))
