"""Record-only byte preservation and exact schedule correction before contrary evaluation."""
import datetime, hashlib, json
from pathlib import Path
out = Path(__file__).resolve().parent
assert not (out / "CONTRARY.json").exists()
assert not (out / "AMENDMENT_1.json").exists()
frozen = json.loads((out / "FREEZE.json").read_text())
for name, pin in frozen["sha256"].items():
    assert hashlib.sha256((out/name).read_bytes()).hexdigest() == pin
preserved = {}
for name in ("RECONSTRUCTION.json", "RECONSTRUCTION_FAILURE.txt", "FWD_SOURCE_REFERENCE.npz"):
    raw = (out/name).read_bytes()
    target = out / ("FAILED_FIRST_" + name)
    assert not target.exists()
    target.write_bytes(raw)
    assert target.read_bytes() == raw
    preserved[target.name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
code = (out / "reconstruct.py").read_text()
old = '''    ref = solve(m, z["literal"][0], float(z["t"][0]), float(z["t"][-1]), m.fwd, step=.005, tight=True, dense=True)
    ref_y = ref.sol(z["t"]).T'''
new = '''    initial_ramp = solve(m, z["literal"][0], 0., .3, np.zeros(N), m.fwd, step=.005, tight=True, dense=True)
    ref = solve(m, initial_ramp.y[:, -1], .3, float(z["t"][-1]), m.fwd, step=.005, tight=True, dense=True)
    ref_y = np.array([initial_ramp.sol(float(tt)) if tt <= .3 else ref.sol(float(tt)) for tt in z["t"]])'''
assert code.count(old) == 1
code = code.replace(old, new)
old = '''        base = solve(m, init, 0., 20., m.background, dense=True)
        np.savez_compressed(OUT / ("ACCESS_seed%d_baseline.npz" % seed), t=np.linspace(0, 20, 1001), y=base.sol(np.linspace(0, 20, 1001)).T)'''
new = '''        initial_ramp = solve(m, init, 0., .3, np.zeros(N), m.background, step=.005, dense=True)
        base = solve(m, initial_ramp.y[:, -1], .3, 20., m.background, dense=True)
        baseline_t = np.linspace(0, 20, 1001)
        baseline_y = np.array([initial_ramp.sol(float(tt)) if tt <= .3 else base.sol(float(tt)) for tt in baseline_t])
        np.savez_compressed(OUT / ("ACCESS_seed%d_baseline.npz" % seed), t=baseline_t, y=baseline_y)'''
assert code.count(old) == 1
code = code.replace(old, new)
target = out / "reconstruct_amended.py"
assert not target.exists()
target.write_text(code)
record = dict(amended_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), contrary_outcomes_generated=False,
              scientific_amendments_conservatively_charged=1, original_frozen_bytes_preserved=True, initial_native_utc="2026-11-03T07:45:29Z",
              preserved_failed_outputs=preserved, changes="only missing zero-to-input source clipped ramp at startup; no scientific gate/settings/tolerance/horizon changes",
              sha256={name: hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ("AMENDMENT_1.md", "reconstruct_amended.py", "contrary.py", "model.py")})
(out / "AMENDMENT_1.json").write_text(json.dumps(record, indent=2)+"\n")
print(record)
