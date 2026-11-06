# Learning-rule transport — campaign state

Started 2026-10-28. Lead: GPT-6.1 Sol, MAX. Persistent goal is active in this chat. This is the focused study selected in `RESEARCH_STRATEGY_RESET_2026-10-28.md`; prior campaigns remain complete.

## Objective

Test whether a learning rule inferred under adaptive IBL mouse training can autonomously forecast acquisition after a fixed early prefix, first in unfamiliar source animals/labs, then (only if the source gate is earned) in the independent fixed-curriculum Pan-Vazquez cohort. Distinguish actual-history conditional prediction from generated-history rollouts.

## Current status

- Read project learnings, charter, strategy reset and feasibility record. Created persistent scientific goal without a token budget.
- Metadata-based allocation frozen by data worker in `protocols/SPLIT.json`: 74 development animals, 27 unfamiliar animals in development labs, 27 animals in wholly reserved Hofer/Witten labs. 26 animals excluded for incomplete indexed trial-table coverage. Strict external cohort: 20 animals; two early-day gaps excluded.
- No new raw behavioral outcomes inspected as of this initial entry. Two previously downloaded feasibility examples were schema/hash checks only (CSHL034 and fip_13).
- Public source acquisition, published model reconstruction and versioned trainer reconstruction are running in parallel. External outcomes stay sealed.

### 2026-10-28 20:25 EDT — empirical source test underway

- Original byte acquisition and all74development conversions complete.128source+20strict external animals pinned; one mutable KS016public object exception resolved from independent metadata before its outcomes;34externalday0unconditioned sessions excluded by metadata.
- Published recurrence audits pass(DNN32probabilityerror<8e−8;RLcoefficienterror~1e−16). Fitted62development animals;12nested development animals used for checkpoint/uncertainty choices. DNN16(two seeds), source-defaultDNN32, source-baselineRL andpureRL are frozen. No external rule was fitted.
- Development conditional forecasts are substantially more accurate than free rollouts; these are development results only. Strong exposure/growth and full-prefix persistence baselines are implemented. Shared engagement/omission handling is explicit.
- Exact empirical fitting recovers a known transferable synthetic learner: sourceCRPS improves22.6% andfixed-protocolCRPS10.3% againstgrowth; fixed-protocol80%coverage83.7%. Fixedcompetence, ordinarygrowth andchangingengagement do not earn material advantage over strongest baselines. A wrong.8daybreak retention assumption causes failure and the known correction rescues it. See `protocols/RECOVERY.md`.
- Independent design/code review fixed nonfinite-score abstention and zero-contrast replay side handling. Exact score/coding/causality controls pass. Local drift analysis explains how reward-independent action tracking can supply conditional accuracy but zero mean autonomous coefficient drift.
- Scientific freeze is `protocols/FREEZE.json`,SHA256`c0141244ac43d240f858956917e3b2b661c72a01a4bddbccdb3974a818b5741f`. Original freeze preserved; a pre-execution metadata serialization repair changed no scientific choice and is recorded in the final freeze/exposure log.
- Source jobs now run512particles/model, all6models, first1000prefix andup-to5000futureopportunities. Prefix-onlyParquet reader supplies nofuturecontrasts/actions/rewards; each animal's forecast files are saved before actualfuture scoring reads. Jobs/logs: `source_animals` and`source_labs`. External outcomes remain sealed.
- Next: finish source scores/gate; challenge strongest result under declared trainer/initialization/daybreak/replay assumptions; obtain independent original-Parquet reconstruction and fresh adversarial scientific review; run offline reproduction; complete REPORT and project learning.

## Ownership and access boundaries

- `data` worker: raw acquisition, manifests, split/exposure records, data loader. May open development outcomes only after split freeze. Validation and external bytes remain sealed.
- `model` worker: published DNNGLM + REINFORCE recurrence, source equivalence and development-only fits. No validation/external outcomes.
- `trainer` worker: source acquisition-code audit and causal curriculum simulator. No raw animal outcomes in any split.
- Lead: baseline forecasts, scoring, controlled recovery, fit/evaluation freeze, source validation, interpretation and report. Validation is opened only after a written method freeze. Independent reconstruction/review follows decisive statistics.

Workers share the workspace and must not revert each other's files. Root launch/handoff files belong initially to the launching chat.

## Decisions already fixed

- Source allocation uses all 128 animals with trial tables for every indexed training session, without selection on learning success. Whole labs Hofer/Witten withheld. Other labs: SHA256(`learning_rule_transport_2026-10-28:` + subject) modulo 5 equals zero → unfamiliar-animal holdout; remainder development.
- The inference target starts at the first indexed training session, not certified first biological exposure.
- Autonomous forecast conditions on available task-trial opportunities and session boundaries. It is not an unconditional calendar-time or training-cessation forecast.
- Simulations receive no actual future choice/reward, smoothed weights, adaptive contrasts/rewards or attainment labels. The trainer responds to simulated performance. Actual future stimuli may be used only in a separately labeled conditional diagnostic.
- Omissions are observations, with explicit response/no-response modeling.
- External outcomes will be evaluated once only after meaningful calibrated autonomous source performance; otherwise remain protected.

## Next executable actions

1. Verify downloaded original bytes/coverage and open development data.
2. Audit published recurrence numerically, run a small source conditional reproduction and construct matched persistence/exposure baselines.
3. Use development data and controlled generators to set the fixed prefix/horizon, proper distributional score, practical improvement gate and uncertainty policy.
4. Freeze code/model hashes and evaluate source holdouts.
5. Challenge/reconstruct the strongest result, complete an offline runner and report.

## Restart notes

Read this file and `protocols/EXPOSURE.jsonl` before any continuation. A new context does not reset validation exposure. Use original pinned source caches under `sources/longitudinal_learning_feasibility_2026-10-28/`. No paid compute, accounts, author contact, publication or private upload is authorized. Additional bounded agents and lead continuation chats are authorized for this objective.
