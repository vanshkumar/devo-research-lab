# O1 — bulb injections and hypothalamic fluorescence

Decision: **retire these coarse summaries as a decisive pathway test**; retain a calibrated feasibility result. This is not evidence of absence of a sparse direct pathway.

All12 primary MOB injections were selected from2,992 API experiments before target outcomes. None was selected on projection strength. Nine atlas structures and bilateral unionizes were requested;134 returned compartment-specific records cover every analysis target. Eleven injections have≥90% of injection signal in MOB; the≥80% subset is identical. Source cell populations differ by Cre line (preserved in per_experiment.csv); this is not a uniform12-animal mechanistic intervention. Primary densities are outside the injection site. No parent/child density sums or voxel-level statistical tests are used.

Controls: PIR density exceeds cerebellar density in all12 experiments. The density=pixels ratio is recovered to4.72e−16, and each normalized projection volume agrees with projection volume divided by total injection-signal volume. All manifest checksums pass; missing rows would raise rather than become zeros. The initial acquisition display used `id` instead of the API's `data_set_id`; the schema was corrected before target acquisition/analysis. No scientific outcome depended on that failure.

In the11 cleaner injections, HY median density is3.7803e−5, nearly the cerebellar median3.7796e−5; HY exceeds that off-route comparator in4/11. PVH median is0, SO3.3948e−6, ARH1.5303e−5, and PIR5.2826e−4. Specific target densities exceed CB in1/11,1/11 and4/11, respectively. All absolute values and normalized-volume sensitivity are saved; region volumes differ so normalized-volume ranking is not an interchangeable density control. CB is an off-route comparator, not a fitted universal fluorescence-background model.

Strongest objection to a negative inference: these injections neither guarantee coverage of the specialized OR37 projection cells nor distinguish passing fibers, terminal synapses and artifacts. The positive PIR control validates broad assay recovery, not sensitivity for a small hypothalamic pathway. Bader's targeted tracing is more appropriate to the question; the Allen summaries cannot overturn it. Russo's ghrelin claim was inspected only at abstract level. Further image inspection could clarify outliers but would still not identify synaptic or behavioral causality, so this direction did not receive the main follow-up allocation.

Reproduction from root (acquisition requires public network; analysis is offline):
```sh
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/olfaction/acquire.py --stage unionizes
.venv/bin/python campaigns/byrnes_todo_2026-10-28/experiments/olfaction/run.py
```
