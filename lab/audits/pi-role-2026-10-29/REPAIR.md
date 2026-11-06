# PI process repair verification

**Later live activation check:** both project hooks were individually trusted through Codex CLI. Reopening the existing PI made its shell restriction pass. Inline JavaScript still ran, and the live usage-result recorder did not update. The full canary failed, so the user-authorized conditional resume was not performed. The original heartbeat id was absent during verification; the same two-hour PI heartbeat was recreated in **PAUSED** state and its saved configuration was checked. See [activation status](ACTIVATION_STATUS.json) and [live records](LIVE_ACTIVATION.json). The native noise/context work was reconciled as completed, with scientific review still pending.

The PI and its two-hour heartbeat remain paused at the human's request. The repair did not run a scientific analysis, consume protected outcomes, dispatch a new investigator or resume the PI.

The behavior audit identified a real ownership loophole: the PI wrote and ran scientific input diagnostics and numerical calibration planning itself. Its activity increase was separately authorized by the human's October29 usage override; that authority and the eight-start/seven-cycle history were preserved.

## Implemented checks

- Strict PI coordination role: supported arbitrary scripts, scientific shell commands, direct patches, search and native-agent execution are denied. A code-mode wrapper accepts only one literal JSON tool invocation; the nested call is checked separately.
- Paused governance is independent of allowance. Missing/stale task contracts, brief hashes, allowance receipts, ownership or reservation evidence prevent dispatch.
- One-use dispatch permits match exact arguments, contract and current reservation; uncertain/failed dispatch stays pending. Captured app results provide actual identities. Superseded tickets are invalidated.
- Recent captured app status is required for lifecycle reconciliation. Idle alone is insufficient; interrupted or unfinished work retains its slot until reconciled. Completing a task requires the actual completed turn and hashed STATE, RESULT and planned artifacts.
- Validation needs reviewer-originated evidence from a distinct identity and matching hashes for controls, exposure, freeze and decisive scientific artifacts. A changed artifact or failed control blocks promotion. Review/revision cycle caps survive daily budget overrides.

## Verification

`/usr/bin/python3 -m unittest discover -s lab/tests -v` passed **36 tests**. Eight additional simulated hook events verified denials for PI scientific execution, direct JavaScript computation, search, native agents, direct edits and paused dispatch, while allowing controller status and its literal wrapper. [Raw test output](TEST_OUTPUT.txt) and [hashed verification record](VERIFICATION.json) preserve the evidence.

These are offline tests and simulated events. **Live project-hook trust, configuration reload and the actual PI denial canary remain unverified.** Controller flags correctly remain false. Project configuration disables hosted WebSearch and native subagents after reload; investigator search uses the hooked MCP path.

Codex requires review/trust of the new hooks. Follow [the activation instructions](../../HARD_GATES.md) before any human-authorized resume. No trust bypass was used. Investigator shell checks remain cooperative rather than OS isolation, as documented in the workflow.
