# Change 6: exact parent integration

Prepared by administrative worker `01a1a2d1-4b8a-71e1-abcb-d5cc116c4c82` on November 3, 2026. Only `lab/PI_WAKEUP.md` and this `stopping/` directory were edited. These proposals do not apply themselves. Current science remains paused for the verified reserve, not newly declared scientifically exhausted. Parent owns shared-record and live-automation integration.

## Existing heartbeat

Use the supported `automation_update` tool to update existing ID `research-pi-progress-loop`, keeping kind `heartbeat`, name `Research PI progress loop`, target operator `01a18836-d7ba-7243-a87b-50fdbe613db3`, status `PAUSED`, its existing 30-minute schedule and current notification setting. Set the prompt to the exact contents of [LIVE_AUTOMATION_PROMPT.txt](LIVE_AUTOMATION_PROMPT.txt). Preserve other fields rather than creating another automation. Read back and verify saved status, target, cadence and prompt. Do not wake the operator or PI to install this text.

`AUTOMATION_BEFORE.toml` is the exact saved automation observed read-only by this worker; source SHA-256 `75a26e3d02a4789d105b08b91efe7badadd8d8cf20b5d5c2efb2354ec7f6211a`. A native `automation_update(mode="view")` also rendered its card, but returned no structured status. The saved TOML supplied the verifiable status/target/schedule. No automation mutation was made.

## Minimal registry and governance wording

Merge these individual field values into `lab/registry.json`; do not replace whole objects. Parent may combine their wording with the other five changes. Existing receipts/history/counters, paused status, `new_scientific_starts_allowed: false`, `scientific_goal_complete: false`, reserve observation and 10% floor stay intact. The pre-reset snapshot preserves superseded current-policy strings; existing historical `human_resume` messages must remain historical, not become fresh resume authority.

```json
{
  "governance.authority": "Human-authorized November 3 administrative reset revises lab workflow and permits reasoned scientific stopping above the 10% reserve. Science, its unfinished native goal and the existing heartbeat remain paused; this reset is not resumption.",
  "governance.resume_condition": "Future science requires human-authorized resumption, verified actual allowance above the 10% reserve, and the applicable scientific evidence/access conditions. A timer tick, reset completion or replenished allowance alone does not resume the run.",
  "governance.scientific_stopping_policy": "lab/PI_WAKEUP.md: close a recipe, continue/revise a program, pivot by comparative payoff, or stop the run when no defensible valuable executable next experiment is justified. Preserve rejected options and reopening conditions; a run stop leaves the scientific goal unachieved.",
  "heartbeat.scope": "Same 30-minute recovery heartbeat on the existing operator for the sole canonical scientific PI. Quiet on unchanged or paused state; bounded recovery during an authorized active run; no duplicate scientists or automatic resumption.",
  "heartbeat.authority": "November 3 administrative reset authorizes this policy revision, with the existing heartbeat remaining PAUSED and future scientific resumption separately requiring human authorization.",
  "heartbeat.retirement_policy": "At a scientific stop for lack of a defensible valuable executable next experiment, a verified 10% reserve stop, or a human stop: checkpoint the unachieved goal and pause/read back this same heartbeat. Never delete it for study completion or schedule an automatic restart. Isolated operational failure calls for bounded recovery, not abandonment."
}
```

For `lab/control-state.json`, retain `governance.status: "paused"`, the actual reserve `pause_reason` and all historical records. Replace only the stale present-tense `governance.reason` with:

> November 3 administrative policy repair only. The scientific run remains paused at the verified 10% reserve, with its goal unachieved. Future science needs human-authorized resumption and actual allowance. Scientific stopping and bounded recovery follow LAB_WORKFLOW.md and lab/PI_WAKEUP.md; the custom gate remains inactive.

No new controller, policy engine, scheduler, automated usage capture or `lab/policy.json` change is needed for this stopping rule. Preserve existing scientific-access boundaries. Parent reconciles obsolete shared prose such as “always choose the next direction above 10%” and “switch direction for a branch blocker” with the decision below.

## Exact shared-workflow stopping block

> At an investment decision, distinguish closing a recipe, continuing or revising the same program, pivoting by explicit comparative scientific payoff, and stopping the whole run. A recipe failure does not by itself close the question. Continue when a feasible, bounded, discriminating test can change a material scientific judgment against the strongest alternatives. Compare any pivot's significance, evidence, feasibility and cost with the strongest useful continuation of the current question. The PI may stop scientifically above the account reserve when no defensible, valuable, executable next experiment is justified from saved evidence and concrete plausible alternatives. Record those alternatives, why they were rejected, and what new evidence or access would reopen the decision. No exhaustive portfolio search is required.
>
> One capacity interruption, failed parse, source-access or messaging/tool failure, expired task deadline, uncertain result or closed recipe is not enough to abandon the run. Reconcile native status and saved outputs; recover the same bounded assignment when useful and permitted, preserving consumed resources and exposure. A hard task limit ends that assignment; any revised allocation requires a justified PI decision within the whole-investigation budget. Missing usage telemetry defers science and retains bounded recovery; it does not establish scientific exhaustion.
>
> The 10% reserve caps scientific spending rather than requiring spending to it. At or below it, stop science regardless of a worthwhile next test. At a scientific, reserve or human stop, checkpoint existing STATE/RESULT/registry, reconcile active work, pause and verify the same operator heartbeat without deletion or automatic restart, and return one concise conclusion to the human. The scientific goal remains unachieved unless its substantive finish line was independently earned. Native goal transitions must use supported controls with explicit human authorization; never invent a receipt, use completion to stop or transfer, or replace an unfinished goal to bypass its lifecycle. Future resumption requires human authorization and actual allowance. The November 3 administrative reset leaves the current reserve pause intact.

## Exact native-objective proposal and lifecycle limits

[NATIVE_OBJECTIVE_PROPOSAL.txt](NATIVE_OBJECTIVE_PROPOSAL.txt) contains the complete proposed scientific objective: the exact existing 2,649-character objective plus an 898-character stopping addendum, totaling 3,547 characters (excluding file's terminal newline). The scientific claim and completion requirements are unchanged. This is proposed wording, **not an applied native goal edit**.

The currently exposed `create_goal` cannot replace an unfinished goal. `update_goal` accepts status only; it cannot edit an objective or resume a goal, and its pause/block/complete conditions remain binding. This worker changes only its own administrative goal. Parent must not mark the scientific goal complete, clear/recreate it, edit private state, or wake/resume science to install this prose. If a supported objective-edit control can preserve paused status, creation/accounting and receipts under the human's authorization, apply and read back there. Otherwise retain this proposal as pending, keep the current native objective and pause, and describe that limitation accurately. Policy integration need not wait for an unsupported text edit.

Official OpenAI documentation describes a user-facing `/goal edit` control, but its presence in documentation does not expose that operation through this worker's tools: [Developer commands](https://learn.chatgpt.com/docs/developer-commands). The [scheduled-automations documentation](https://developers.openai.com/api/docs/guides/agents-api/sessions/automations) distinguishes pausing scheduled delivery from stopping already accepted work; the local tool schema and actual saved/native state govern this Codex heartbeat. These were administrative product-documentation reads, not scientific source investigation.
