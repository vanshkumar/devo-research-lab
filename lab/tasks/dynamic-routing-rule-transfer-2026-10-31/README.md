# Dynamic-routing partial source verification

The cross-stimulus first-encounter forecast comparison is **unrun**. Public-access operations reached12/12 before the full trial chronology, license and deployment source could be certified. [RESULT.md](RESULT.md) distinguishes the acquired schema and actual reward vector from the untested hypothesis.

Offline reproduction from repository root, using Python3.9+ standard library only:

```sh
python3 lab/tasks/dynamic-routing-rule-transfer-2026-10-31/first_data_check.py
```

This verifies the stored 3,304-byte Blosc/LZ4 frame and reconstructs FIRST_DATA_CHECK.json and reward_times.csv. The small decoder intentionally supports only the checked stored frame, uses eight byte-shuffled LZ4 splits and validates full consumption/shape. No external decoder cross-check was performed.

Source inspection can be replayed offline:

```sh
python3 lab/tasks/dynamic-routing-rule-transfer-2026-10-31/inspect_tutorial.py
python3 lab/tasks/dynamic-routing-rule-transfer-2026-10-31/inspect_outputs.py
python3 lab/tasks/dynamic-routing-rule-transfer-2026-10-31/inspect_metadata.py
```

These scripts read the complete saved notebook/schema; they do not fetch new data. Resource/output accounting is regenerated offline by `closeout.py`. No model, seeds, fitted parameters or forecasts exist because source certification did not pass. No additional dependencies were installed. SHA256 pins/URLs are in SOURCE_MANIFEST.json; HTTP headers/versions are in ACQUISITIONS.jsonl; all12publicoperations/failures/reserves are in OPERATIONS.json.

`acquire.py` and the four request JSON files preserve the exact bounded acquisition method. **Do not rerun network acquisition under this completed allocation**; the request cap is consumed. The linked S3 objects are anonymous public data, but a data license was not certified, and object-path identities were not checked against scalar NWB subject/session values.

This is a source-check artifact with no scientific signoff. No transfer absence, equality, mechanism identification or novelty claim follows from it.
