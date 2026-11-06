# Natural timing variation: inspection and reproduction

Read [RESULT.md](RESULT.md); [RESULT.png](RESULT.png) shows the principal comparisons. All methods fail the frozen full criterion; ordinary exemplar/covariance methods retain useful selective correction, and bounded global alignment repairs only its specific tempo blindness. One adult Bengalese finch/day; supplied human labels; designed interval edits, not biological mistakes.

Required installed environment: project `.venv`, Python3.9.6, NumPy2.0.2; Matplotlib is used only for the optional figure. No install, model download or network is needed to reproduce the numerical result. Seeds are deterministic per-example SHA256 values; all methods/edits/thresholds are fixed in [PROTOCOL.md](PROTOCOL.md) and [REVISION.md](REVISION.md).

From `/Users/vanshkumar/Documents/repos/devo-research-lab`, the tested offline reproduction command was:

```sh
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python lab/tasks/natural-tutor-variation-2026-10-31/replay.py --output replay
```

`replay/` now contains that completed reproduction. **Choose a new unused child name**, e.g. `--output replay-review`, for another run. The wrapper refuses existing/out-of-scope destinations, uses one process, makes zero network calls, and leaves original protocol/scores intact. It copies only the small annotated inputs and frozen code, reruns development/freeze/main/revision/self-audit, and compares every saved array. [REPLAY_CHECK.json](REPLAY_CHECK.json) reports bit-exact reproduction. Further reviews have their own PI allocation; reproduction does not reset exposure or remaining resources.

Historical original commands, in order (existing-output guards intentionally prevent overwriting the earned main test):

```sh
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python lab/tasks/natural-tutor-variation-2026-10-31/development.py
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python lab/tasks/natural-tutor-variation-2026-10-31/freeze.py
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python lab/tasks/natural-tutor-variation-2026-10-31/evaluate.py main
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python lab/tasks/natural-tutor-variation-2026-10-31/revise.py freeze
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python lab/tasks/natural-tutor-variation-2026-10-31/revise.py evaluate
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python lab/tasks/natural-tutor-variation-2026-10-31/audit.py
```

The optional saved-summary plot was rendered and visually checked:

```sh
env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python lab/tasks/natural-tutor-variation-2026-10-31/plot_result.py
```

Use source archives already retained; **do not rerun acquisition**. Full archive file41668992 is19,214,942 bytes, primary MD5 `4441c716563965db4c1522346f99a064`, retained SHA256 `28e8d2787d1faaa177d67f786cf77a03706189ca09933e5f6784547e9023e628`. It is licensed CC BY4.0; credit Nicholson, Queen and Sober, *Bengalese Finch song repository*, DOI10.6084/m9.figshare.4805749.v9. [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json) retains URLs/headers/hashes; [SOURCE_SUPPORT.json](SOURCE_SUPPORT.json) retains the39 WAV/CSV inventory. CSV members are immutable in `sources/annotations/`; per-file hashes and split lists are in [FREEZE.json](FREEZE.json). The full archive is not needed for offline scoring, but supports source reconstruction by a separately bounded reviewer.

Artifact map:

- `DEVELOPMENT.json`: actual first6 support/variation calculation and input-only motif choice.
- `MAIN_SUMMARY.json`, `MAIN_SCORES.npz`: all51 main phrases,6 methods,24 edits/method, natural acceptance, per-recording rates and strict/tied/decreased ranks.
- `REVISION_FREEZE.json`, `REVISION_SUMMARY.json`, `REVISION_SCORES.npz`: untouched-final10 revision and unchanged controls;52 phrases,7 methods.
- `AUDIT.json`: original-CSV feature/cost reconstruction, source joins, timing support, exact symbolic sequence controls and explicitly postvalidation score-separation/decrease diagnostics.
- `RESOURCES.json`, `EXPOSURE.json`, `ACQUISITION.json`: cumulative current-block accounting, known failures/unknowns and protected-data preservation.
- `SOURCE_SUPPORT.failed1.json`: failed streaming header parser; size-guard failure/charge are also preserved in PLAN/ledger. Prefix hashes do not certify complete original archives.
- `ARTIFACT_MANIFEST.json`: stable code/protocol/output hashes, excluding bulky source objects whose acquisition hashes are inherited separately.
- `STATE.md`, `LEARNING_PROPOSAL.md`, `TERMINAL_REPORT.md`: bounded owner closeout and return to PI. No successor is launched by this worker.
