# Reproduction and scope

Run from `/Users/vanshkumar/Documents/repos/devo-research-lab`:

```sh
.venv/bin/python lab/reviews/independent-cohort-investment-2026-11-05/independent_check.py
.venv/bin/python lab/reviews/independent-cohort-investment-2026-11-05/lean_sensitivity.py
python3 lab/reviews/independent-cohort-investment-2026-11-05/identity_check.py
```

These use only saved consumed64derived scores/contributions and allowed public/source metadata/criterion summaries. No author simulator, scorer, inference or planning module is imported. No network request or original/new evaluation trial read is performed. The first script independently derives D from the four-actor1024score tensor, checks exact agreement with saved contributions, samples explicit animal-index arrays for50,000cohorts, checks a separate noncentral-t approximation, counts source first-passage/selection dispositions and sums the whole full-family price. The second applies an independently seeded three-reference calculation, scoped boundary controls and measured-timing lean prices. The third checks stable sessions against the canonical154consumed/protected universe, including later aggregate auxiliary rows.

Expected consequential outputs:
- `INDEPENDENT_CHECK.json`: score reconstruction maximum difference0; expected two-reference relative half-width6.915percentage points; coherent20%/15%positive rates about84%/28%.
- `LEAN_SENSITIVITY.json`: three-reference critical2.41524984;20%/15%positive rates .80718/.23220; zero/5%selected-reference negative rates .81324/.22320; three-band miss rate .02062 in this finite shifted law; two-source whole future CPU range214.8904–344.8466minutes.
- `FULL_IDENTITY_CHECK.json`:192animals,1537horizon sessions,6813full-aggregate sessions,6222excluded old sessions, zero protected/consumed overlaps.135overlaps with the broader6488-session metadata universe are unconsumed metadata-only cases.

The author updated FOCUSED_DESIGN from independently shifted equal-relative reference means to one common neural mean. Both INITIAL and corrected source versions were preserved; this review explicitly checked the corrected final design. Actor truth must be common across its comparator contrasts. Source64residual and source-fit means are not new-cohort power or source-tail guarantees.

To reproduce the supplemental source-draw choice without an author module:

```sh
.venv/bin/python - <<'PY'
from pathlib import Path
import json,numpy as np
p=Path('lab/tasks/calibration-frontier-main-2026-11-05')
f=json.loads((p/'MAIN_FAMILY_REFINED.json').read_text())['columns']
with np.load(p/'REFINED_CONTRASTS.npz',allow_pickle=False) as z:
    x=z['contributions']
rows=[]
for d in range(32):
    i=next(i for i,a in enumerate(f) if
        a['kind']=='source' and a['reference']=='recent_selected'
        and a['cutoff']==200 and a['metric']=='D'
        and a['neural']=='linear256' and a['draw']==d)
    rows.append((float(x[:,i].mean()),d))
print(min(rows),max(rows))
PY
```

Expected: minimum draw0, D−.014559754653872398; maximum draw14, D−.0016234257404730917. SOURCE_CONTRARY preserves all32points, exact input hashes and original execution cost. These are old-output-based contrary choices, not new target selection or source-tail calibration.

`closeout_resources.py` reconstructs the resource receipt from computational receipts and explicit retrospective full-file context bookings. It is closeout accounting, not a live monitor or evidence of physical I/O. Replays change timing/RSS and do not refund prior executions. The first LEAN run (.543526CPU seconds,621512read+399360decoded bytes) predates the added controls and is charged separately. Unknown failure/import/provider costs remain separately booked/unknown.

Preserved failures:
- System Python could not import NumPy before array access; numerical runs use the existing .venv.
- Missing guessed paths and a display helper iterating an integer did not acquire response values.
- FULL_IDENTITY_CHECK_ATTEMPT is a **failed**, nonaccepted attempt despite its preliminary status field. The initial checker included all170metadata names, rather than the154consumed/protected names. Two native assertion failures are preserved. Tracing all135flags to metadata-only subjects resolved the false positive; the final script filters canonical154names before checking all stable UUIDs. Failed work is charged, and no scientist/source acquisition was restarted.
- Broad file listings/JSON presentation were truncated; bounded selected-key reads were used afterwards.

The first horizon-only check against all6488metadata sessions returned zero overlap and remains true, but it was an overbroad comparison and does not replace the corrected full-aggregate check. Original source measurements/old74<=6000, old64<=4000 and all other protected caps remain unchanged. NYU-42raw probe values were not reread here; its declared source summary was inspected.

The source scientist's actual final DESIGN, RESULT, MILESTONE_ASSESSMENT, FINAL_ACCOUNTING and native terminal state were collected. ACCOUNT_CHECKPOINT records the actual native turn completion, usage snapshot and review goal readback. This review does not assert a new main was run or funded; the PI owns that decision. GOAL_FINAL preserves this review's actual native completion response: status complete,189432tokens,1702seconds. The immediately following get_goal returned goal:null, not a second completed-goal object; that exact empty-slot readback is saved without inventing a status or creating a replacement goal. PI goal and heartbeat were not changed.
