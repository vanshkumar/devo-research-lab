# Change 6 — scientific stopping and heartbeat recovery

**Scoped implementation complete; parent integration pending. Science remains paused at the verified reserve, and its goal remains unachieved.** Administrative worker `01a1a2d1-4b8a-71e1-abcb-d5cc116c4c82`, November 3, 2026; fresh Astra/xhigh assignment, no delegates.

Rewrote [lab/PI_WAKEUP.md](../../../PI_WAKEUP.md) for the existing 30-minute operator heartbeat. It now separates recipe closure, program continuation/revision, a comparative-payoff pivot, and scientific stopping above reserve. A scientific stop needs concrete rejected options, reasons and reopening evidence; isolated operational failures receive bounded recovery. The 10% reserve still stops spending even if a valuable next test exists. Unchanged paused state exits quietly; no automatic restart, duplicate worker, new scheduler or false scientific-goal completion.

Prepared exact [live prompt](LIVE_AUTOMATION_PROMPT.txt), [shared-record/workflow proposals and integration instructions](INTEGRATION.md), and [native-objective proposal](NATIVE_OBJECTIVE_PROPOSAL.txt). The objective preserves the entire 2,649-character original and adds stopping policy, totaling 3,547 characters. [AUTOMATION_BEFORE.toml](AUTOMATION_BEFORE.toml) preserves the observed live automation byte for byte. Shared records, live automation, scientific/native PI state, histories, counters and scientific artifacts were not mutated by this worker. No scientist/operator was woken and no science/protected data was accessed.

## Checks and limits

- [SCENARIO_CHECKS.md](SCENARIO_CHECKS.md): all six required administrative scenarios and six additional boundary cases pass a policy walkthrough. This is not executed science or runtime enforcement.
- [CHECKS.json](CHECKS.json): 14 structural/status checks passed, including exact automation snapshot identity, unchanged live automation, same paused operator/cadence, recorded unachieved science status, removal of obsolete timing/reserve prose, exact original-objective prefix and artifact links.
- Re-read the compact active LEARNINGS before completion. All write calls used `apply_patch` and only assigned paths. A first patch-format attempt was rejected before mutation; the corrected update succeeded.
- Native automation view returned only a rendered card; saved TOML provided the readback fields. No fresh scientific usage or goal-status query was claimed. The actual existing reserve observation and saved paused-goal receipt remain the authority.
- Official OpenAI documentation was consulted only for administrative lifecycle semantics; sources and local tool limits are in INTEGRATION. No scientific source investigation occurred.

## Remaining parent integration

1. Merge stopping wording into LAB_WORKFLOW and minimal registry/control-state fields alongside the other workers' changes. Preserve current reserve-pause classification, native receipts/history/counters and all protected evidence.
2. Update the same existing automation with LIVE_AUTOMATION_PROMPT, retaining PAUSED status, operator target, 30-minute schedule and notification settings; read back the result. No new permission or resumption is requested by this scoped work.
3. Treat NATIVE_OBJECTIVE_PROPOSAL as unapplied until a supported, authorized objective-edit surface preserves paused status and accounting and returns actual readback. Current tools cannot edit an unfinished goal objective. Do not manufacture completion, clear/recreate the goal or wake science to install text.
4. Integrate the learning below if useful and nonduplicate. Root LEARNINGS belongs to the shared-record maintainer.

## Proposed active learning

**2026-11-03 — Heartbeat instructions drifted from native state**
- Observation: PI_WAKEUP still prescribed two-hour review and an October 29-only reserve override, while the saved native heartbeat was the same 30-minute operator automation, paused at the verified 10% reserve. Its old prompt also made branch closure imply another investment without a scientific-stop option.
- Action: When revising recovery/stopping policy, reconcile PI_WAKEUP, the same native automation prompt and shared workflow together; verify status/target/cadence separately from the prose. Preserve the actual pause and receipts while changing policy.
- Confidence: high

## Native administrative goal receipt

Actual scoped goal creation/readback: `createdAt=1793732998`, no token budget, thread `01a1a2d1-4b8a-71e1-abcb-d5cc116c4c82`. [NATIVE_GOAL_ACTIVE.json](NATIVE_GOAL_ACTIVE.json) records the active readback. After the scoped file changes and checks, `update_goal` returned `status: complete`, `tokensUsed: 73645`, `timeUsedSeconds: 417`; the subsequent `get_goal` returned `goal: null` (no active goal). Both exact responses are saved in [NATIVE_GOAL_COMPLETE.json](NATIVE_GOAL_COMPLETE.json). This administrative completion makes no claim that the scientific mission is achieved.
