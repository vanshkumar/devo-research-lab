# Connectome persistence contrast — source gate CLOSED

Read [RESULT.md](RESULT.md) and [SOURCE_GATE.md](SOURCE_GATE.md). This is an auditable primary-source clarification; there is no numerical persistence result or earned main protocol.

The named2017 paper studies maintained-input attractors/long transients. The later public2019 beta code is not certified as its exact executable model. Original full-network simulation and independent numerical reference are UNRUN.

Offline source audit (standard existing Python; no network, installation, neural arrays or application server):

```sh
cd /Users/vanshkumar/Documents/repos/devo-research-lab
python3 lab/tasks/connectome-persistence-contrast-2026-11-03/source_audit.py
```

It checks the three pinned source Git blobs, parses source constants/call locations and overwrites only SOURCE_AUDIT.json with a fresh resource/time receipt. Expected output has status SOURCE_AUDIT_ONLY_NO_MODEL_RUN and pin_matches [true,true,true]. This command does not simulate the circuit. Historical outputs remain in SOURCE_AUDIT_INITIAL.json, SOURCE_DECODING.json and NATIVE_EXECUTION.json.

decode_sources.py is the historical one-time newline correction, preserved for inspection. It intentionally asserts the original one-extra-newline condition; do not rerun it on the now-correct files. Saved connector response JSON is the exact recovery source. The original code and BSD3 notice are retained in sources; do not execute initialize.py as part of this source audit.

Source URLs/version/tree/blob pins and exposure are in SOURCE_MANIFEST.json. Resource bookings/unknowns and inherited charges are in RESOURCES.json. No full byte-level original article archive, empirical recording, model matrix, data fit or protected target is part of this task.
