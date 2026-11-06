# Preserved first numerical startup failure

2026-10-31, observed before06:07:54Z. The first dynamics_audit.py process loaded the pinned plant100snapshot and small input arrays, then stopped at the reviewer's own `permitted(path)` assertion while checking the snapshot's source hashes. No independent circuit dynamics or contrary test ran in that process.

The original snapshot constructor's source_hashes includes its pinned preflight helper and every cached upstream source file, including the source notebook. The review reader's initial allowlist omitted that helper and the notebook extension. Its failed script and pre-execution freeze are preserved byte-exact as dynamics_audit_failed_input_scope.py and NUMERICAL_FREEZE_FAILED_INPUT_SCOPE.json. The cumulative read ledger is not reset; the13,742,317-byte snapshot read remains charged.

Correction: admit the exact pinned preflight.py source and cached upstream notebook bytes for opaque source-checksum verification. No notebook JSON/output is decoded, no source/circuit/metric/action/window changes, and no project hook/controller/permission is altered. The numerical plan remains RECONSTRUCTION_PLAN.md. Re-execution is within the same bounded authorized block, not another continuation or repaired scientific control.
