# Reproduce the access checkpoint

The inspection was limited to the saved release index, three pinned source texts, and local filenames. This command reruns the local pin check from the repository root. It does not access the network or any trial file.

```bash
/usr/bin/python3 -B - <<'PY'
import hashlib
import json
from pathlib import Path

source = Path("lab/tasks/human-association-acquisition-qualification-2026-11-05/sources")
tree = json.loads((source / "wmh-tree.json").read_text())
assert tree["sha"] == "f2d4108dea80642e7d5b95d1c108916091a221c8"
entries = {item["path"]: item for item in tree["tree"]}
brown = entries["RLWM/DataSets/Expe3.mat"]
assert brown["type"] == "blob"
assert brown["sha"] == "2ab7b32fd81296453835edb81a7c59d97d9325a2"
assert brown["size"] == 352400
print(brown["path"], brown["size"], brown["sha"], brown["url"])
texts = {
    "RLWM/DataSets/readme.txt": "data-readme.txt",
    "RLWM/general_fitting_script.m": "general_fitting_script.m.txt",
    "RLWM/analyzeBehavior.m": "analyzeBehavior.m.txt",
}
for path, filename in texts.items():
    content = (source / filename).read_bytes()
    git_blob = f"blob {len(content)}\0".encode() + content
    assert entries[path]["sha"] == hashlib.sha1(git_blob).hexdigest()
    assert entries[path]["size"] == len(content)
    print(path, len(content), entries[path]["sha"])
PY
```

At 21:30:45 UTC the check exited 0, printing the matching 352,400-byte Expe3 index entry and verified source text lengths 1,495, 18,002 and 3,626 bytes. The texts name the expected `expe_data` variable, 17-column layout and validity-masked analysis. This verifies the catalogue pin and the saved source text bytes. [Catalogue verification](../human-association-acquisition-qualification-2026-11-05/VERIFICATION.json)

The original command used curl 8.7.1, first-argument `-q`, HTTPS only, no redirects, `--max-filesize 600000`, 7-second connect and 18-second overall limits, and headers `Accept: application/vnd.github.raw+json`, `Accept-Encoding: identity` and `Authorization:`. It targeted only the blob endpoint in [the freeze](ACQUISITION_FREEZE.md). The ordinary attempt exited 6 with HTTP 000, zero bytes and no body file. Review rejections prevented process creation. Do not re-run the network command on the same rejected evidence. [Transfer output](HTTP_TRANSFER.txt) · [Access chronology](ACCESS_HISTORY.md)

## Prepared measurement reader

Run from the repository root using the existing SciPy environment.

```bash
d=lab/tasks/human-association-source-development-2026-11-05
env OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python -B "$d/audit_expe3.py" --self-test
```

The controls make compressed MAT and base64 test fixtures in memory. They verify the predecode guard and recover known response/omission counts, then inject structural and feedback faults. Both actual runs terminated with exit 0. [First run](SYNTHETIC_CONTROLS.json) · [Expanded run](SYNTHETIC_CONTROLS_EXPANDED.json)

The source form is `.venv/bin/python -B "$d/audit_expe3.py" "$d/BROWN_BODY.bin" --report "$d/STAGE_A.json"` once the exact source is acquired under the freeze. It checks size and Git hash, reports SHA-256, inspects MATLAB directory shape and only then decodes the matrix once. The optional `--projection "$d/BROWN_BEHAVIOR.npy"` preserves columns 1–14 from that decode for possible later source work, with the environment-only correct-action column identified in the report. Audit reports contain aggregate scope, omissions, RT, timing, fixed mapping and feedback diagnostics, with the candidate windows counted without selection. Inspect the report and the study protocol for the scientific gate. An exit-0 reader check alone is insufficient.

## Resumed measurement and development

One directly approved supported review returned the frozen 352,400-byte Expe3 file. The file is saved as `BROWN_BODY.bin`. Its Git blob is `2ab7b32fd81296453835edb81a7c59d97d9325a2` and SHA-256 is `5a7426dfaa9167895ae6dde5362feb9070197cedc9ce6ac7fa6b3ceae613751c`. Reproduction uses that local copy. Every future read requires its own scoped scientific allocation and charging. The original reader stops on the opaque companion, as observed. The PI's exact projection amendment applies to the measured run below. [Transfer and amendment](ACCESS_HISTORY.md) · [Original inventory stop](STAGE_A_INVENTORY_STOP.md)

From the repository root, use the current environment and a fresh output directory to preserve saved results.

```bash
d=lab/tasks/human-association-source-development-2026-11-05
brown_rep=$(mktemp -d "$d/reproduction.XXXXXX")
export OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OMP_NUM_THREADS=1

.venv/bin/python -B "$d/audit_expe3_amended.py" control \
  --report "$brown_rep/AMENDED_CONTROLS.json"
.venv/bin/python -B "$d/audit_expe3_amended.py" behavior "$d/BROWN_BODY.bin" \
  --report "$brown_rep/STAGE_A_MEASURED.json" --projection "$brown_rep/BROWN_BEHAVIOR.npy"
.venv/bin/python -B "$d/measure_schedule.py" \
  "$brown_rep/BROWN_BEHAVIOR.npy" "$brown_rep/STAGE_A_SCHEDULE.json"
.venv/bin/python -B "$d/measure_early_support.py" \
  "$brown_rep/BROWN_BEHAVIOR.npy" "$brown_rep/STAGE_A_EARLY_SUPPORT.json"

.venv/bin/python -B "$d/brown_develop.py" control --report "$brown_rep/FORECAST_CONTROLS.json"
.venv/bin/python -B "$d/brown_develop.py" fit --projection "$brown_rep/BROWN_BEHAVIOR.npy" \
  --report "$brown_rep/BROWN_FITS.json"
.venv/bin/python -B "$d/brown_develop.py" forecast --projection "$brown_rep/BROWN_BEHAVIOR.npy" \
  --fit "$brown_rep/BROWN_FITS.json" --archive "$brown_rep/BROWN_FORECAST_COUNTS.npz" \
  --report "$brown_rep/BROWN_FORECAST.json"
.venv/bin/python -B "$d/audit_forecast_scores.py" \
  "$brown_rep/BROWN_FORECAST_COUNTS.npz" "$brown_rep/BROWN_SCORE_AUDIT.json"
```

Inspect the actual measurement and gate before fitting. The complete source numeric matrix decodes only once in these commands. Model stages read the first-14-column projection, and the score audit reads only generated counts and target summaries. The controls run on constructed data. The fit and forecasts use single-thread numerical library settings, one process at a time, fixed five whole-person folds and 512 particles per actor/clock/block. The forecast archive separates metadata, actual target counts, generated counts, person losses and paired gains. Its fit and forecast source projection SHA-256 is `a0d5ebab3b5da429b531d3dcb3916b1d5231d6acaaa9da85e8cd0d87aa48da17`. Reproduce the original paired score and all-distinct-particle audit without changing the fixed models. Source code hashes at freeze, actual timing and resource totals are saved. [Pre-fit implementation freeze](STAGE_B_IMPLEMENTATION_FREEZE.json) · [Actual output](BROWN_FORECAST.json) · [All-pairs check](BROWN_SCORE_AUDIT.json) · [Accounting](RESUMED_ACCOUNTING.json)
