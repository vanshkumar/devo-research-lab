# Independent extinction review

Accept the fixed numerical benchmark and close further archive fitting. Cue-specific updating worsens primary physiology forecasts3.56%; scaling narrows the penalty to.31%, and expectancy selects identical forecasts. The frozen matched-decay diagnostic shows masking by common decay, but physiology detection remains5/100versus9/100without it. Read [REVIEW.md](REVIEW.md) for scope and interpretation.

The existing repository .venv supplies Python3.9.6/NumPy2.0.2; other dependencies are standard library. All numerical scripts fix thread counts to1before importing NumPy. No author helper imports, network or new package installation are used.

From repository root, the following commands were executed successfully:

```sh
python3 lab/reviews/threat-extinction-experiment2-2026-10-31/independent_source.py
.venv/bin/python lab/reviews/threat-extinction-experiment2-2026-10-31/review.py audit
.venv/bin/python lab/reviews/threat-extinction-experiment2-2026-10-31/review.py controls
.venv/bin/python lab/reviews/threat-extinction-experiment2-2026-10-31/review.py freeze
.venv/bin/python lab/reviews/threat-extinction-experiment2-2026-10-31/review.py diagnostic
python3 lab/reviews/threat-extinction-experiment2-2026-10-31/summarize.py
.venv/bin/python lab/reviews/threat-extinction-experiment2-2026-10-31/verify_saved.py
```

`verify_saved.py` is the small read-only scientific verification; it checks120static participant losses/12bootstrap endpoints, provider metadata/source hashes/license and all freezes. It writes verification/manifest outputs in this directory. `summarize.py` emits a compactable saved-record summary and source README copy. The first controls invocation failed only at a CLI name mismatch before source loading; FAILED_PASSES.md preserves it. All400original controls subsequently reconstruct exactly.

Preserve canonical artifacts: freeze/diagnostic commands refuse overwrites. A fresh isolated replay is available:

```sh
.venv/bin/python lab/reviews/threat-extinction-experiment2-2026-10-31/reproduce.py --name another_audit --stage audit
```

Its audit mode was executed as `--name reproduction_audit --stage audit`; the saved independent reconstruction is exact. The wrapper imports this review's frozen code, keeps its fixed source location and sends all writes to the new child directory. It refuses an existing name. `--stage all` additionally runs the first calculation,400original controls and800new matched records after a fresh copied freeze; this combined mode was not run. Any rerun needs its own read/compute allocation and cannot restore validation status.

Main artifacts: FIRST_CALCULATION.json; SOURCE_MANIFEST.json/SOURCE_SYNTAX.json/SOURCE_README.txt; RECONSTRUCTION.json; CONTROL_RECONSTRUCTION.json; CONTRARY_PLAN.md/CONTRARY_FREEZE.json/CONTRARY.json/CONTRARY_SUMMARY.json; FINAL_VERIFICATION.json; RESOURCES.json; STATE.md; OUTPUT_PINS.json. PROPOSED_LEARNING.md is for PI integration; workers do not edit shared memory.

Source attribution: Mertens, Leer, van Dis, Vermeer, Steenhuizen, van der Veen and Engelhard(2019), DOI10.1016/j.jbtep.2018.09.007, [OSFdxpb3](https://osf.io/dxpb3/), CC-BY4.0. Cache remains under the author task's sources/experiment2.zip; no source data or frozen author file was edited. Review consumes the complete raw log/allcolumns in addition to already consumed complete SAV cases; no untouched cohort, questionnaire/workbook decode, old protected data, contact or publication.
