# Preserved failed commands

Before analysis, ordinary shell composition and commands naming a raw data directory/CSV were blocked; no scientific bytes returned. Details in STATE.

First `analyze.py` execution exited1 while importing SciPy, before reading any scientific input or fitting: our task-local `inspect.py` shadowed Python's standard-library `inspect`, causing `AttributeError: module 'inspect' has no attribute 'cleandoc'`. Renamed that inspection script `schema_check.py`; no environment/dependency or scientific-recipe change. Charge20MBconservative dependency/import/context allowance for this failed pass in addition to successful-pass allowances. Original SCHEMA.json and its successful read/exposure remain. This implementation fix is separate from the one scientific sensitivity step and does not alter PROTOCOL.

First `checks.py` pass read the permitted CSV plus RUN/COMPARISON/protocol/check-plan and computed the finite witness, then exited1 before output write: a NumPy Boolean required explicit `bool()` for standard JSON. Fixed the serialization cast only; no numerical-model change or original-result replacement. Charge another20MBfor imports/failed read-decode/output allowance, including the small actual input pass. No empirical refit had begun on that failed pass.
