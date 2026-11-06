# Source and protocol audit

2026-10-28. Performed independently of behavioral outcomes. The only campaign trial file read here was `outputs/input_only/trial_inputs.csv`; choice, feedback, movement, response time and cursor outcomes were not opened. Existing feasibility inspection had already seen the first trial prefix.

## What the participant received

The pinned task builder (`47ac8356432972c7e6e5a887f15a7dd2d6c686ad`, preserved under the root feasibility sources) is the authority for intended task flow. `active_builder.txt` extracts active-flow routines and readable code/text. Its inactive legacy routines must not be mistaken for the executed task.

- The instructed condition receives written contrast discrimination rules, two example images, the opposite-direction mouse mapping, feedback tone meanings, and five practice trials. The active practice loop selects source rows36:41 with random order and `nReps=instructions`; the main loop selects rows0:600 sequentially once. The teaching package is broader than verbal instructions alone. It contains no advance information about changing target probabilities.
- Discovery participants are told to figure out the rules, that moving the mouse interacts with the game and clicking does nothing, and to fixate. Both conditions are permitted to ask the experimenter questions; actual assistance is not documented trial by trial.
- Both gratings start at a0.5 pedestal; target contrast increments are0,.02,.05,.1,.2. The public processed contrasts divide these increments by.2, producing0,.1,.25,.5,1. Zero contrast therefore means equal-contrast gratings, not an empty visual display.
- Participants bring the selected grating into the center by moving the mouse in the opposite direction. The code's correctness branches use scheduled `eccentricity`, even when the contrast increment is zero. Correct answers produce a high tone and1s feedback interval; errors produce white noise and2s feedback interval. Timeout produces a different low tone after a10s response window. The timeout does not reveal the scheduled target side.
- On responding trials, a participant who understands the feedback mapping can reconstruct target side from own choice and correctness, including at zero contrast. This is available after response. It is not direct sensory evidence before choice, and discovery participants initially have to learn the mapping. A target-side history assumes use of this available information, not proof that it was understood or used. Correctness and chosen-side times signed correctness are not independently identified reward-learning and stimulus-learning mechanisms.
- Cursor movement determines threshold crossing and the choice. Cursor endpoints therefore cannot supply independent confirmation of an effect computed from the choices.

## Schedule reconstruction

`check_inputs.py` independently converts all ten pinned `pregen_sequence_*.xlsx` files into the public input columns. All80 participants match exactly one complete600-trial source sequence across `probabilityLeft`, left/right processed contrasts and stimulus side. All ten have90 initial unbiased trials. The source XLSX files contain more than600 rows; only the task-selected first600 were compared.

`042` is the sole mismatch between exported ID digit and actual sequence: it matches task sequence1. Author preprocessing renames041B→042, explaining this mismatch. The full mapping and source hashes are in `schedule_mapping.csv`, `schedule_sources.json`, and `sources/manifest.json`. This independent check supports the parent's array-derived schedule assignment without relying on exported digits. It does not inspect behavioral outcomes or imply independent random schedules per participant.

## Assignment, chronology and release selection

The active builder assigns instructions=1 when integer participantID modulo4 is1or2, otherwise0. It does not call a random generator. Exported metadata matches in77/80 cases;006,009,010 are all discovery exceptions. All three precede the first taught session. Metadata dates span2024-10-22–2024-12-13 for discovery and2024-10-30–2024-12-12 for taught participants. Exact date-by-condition counts are saved without demographics/free text in `input_audit_summary.json`.

The public builder file history contains Apr22/23,2024 pilot commits and a Dec5,2024 update (`681e1f39e916b2e3922fdd7779b6936eba0f8101`) whose commit message says it brings the code into line with the J-drive and Nov–Dec experiments. No Oct-session-specific builder snapshots were identified. This sparse history cannot establish the exact assignment implementation for every early session. The generated `WIN_cursor_ibl_lastrun.py` at the pinned commit has the modulo rule commented and `instructions=0` active, contrary to the authoritative builder; it cannot override exported per-session labels or establish that all sessions were discovery.

Author `preprocessing/1_fetch_human_data.py` establishes these public-release decisions:

- IDs041A→041,041B→042,082A→082.
- Incomplete014,082,040,071,083 omitted; pilots001–005 omitted.
-087 is duplicate participation by066, and only066 retained.
-006 had no600-trial limit and was stopped manually; only its first600 trials retained.
- Instruction labels are imported from session metadata, not recomputed from exported ID.

Thus the analysis population is the80 complete, nonpilot, nonrepeat sessions selected by the authors, not every recruited participant. Excluding assignment exceptions and restricting to the common date range are defensible prespecified sensitivities. Neither makes allocation randomized or resolves unrecorded assistance/protocol confounding.

Author `preprocessing/2_process_data.py` recodes choices to+1left,-1right,0omission. It explicitly handles cursor samples recorded up to506ms beyond the10s timeout: trajectories are truncated to the recorded mouse-time length and response times set missing when trajectory lengths exceed time lengths. This prevents late cursor crossings being reinterpreted as valid responses. The exported `feedbackType` arrives through an upstream ALF table; the local builder and trial identity check together should establish its semantics.

## Prior work and the scope of novelty

1. Hoxha et al.2026 primary bioRxiv API metadata was retrieved and saved (`hoxha_api.json`). It identifies v1,2026-10-08, DOI10.64898/2026.10.01.755923 and describes80humans×600trials, instruction comparison, accuracy/lapses and early improvement. The primary full HTML and API-linked JATS XML both returnedHTTP429; responses and headers are preserved. Full manuscript inspection remains incomplete. Do not state that the manuscript definitively lacks the present analysis.
2. Pinned author analysis source contains pooled block-conditioned psychometric functions and raw/fitted zero-contrast block bias (`figure2.py`), RT/cursor plots (`figure3.py`), and three200-trial windows (`figure4.py`). A utility computes `Trials_since_change`, but no use of it for the proposed held-out adaptation comparison was found in these inspected figures. The planned contribution is a quantitative withheld predictive test with matched nuisance structure; generic probability sensitivity, early learning or group block bias are not new here.
3. Bruijns et al., *Infinite hidden Markov models can dissect the complexities of learning*, Nature Neuroscience29:186–194(2026), DOI10.1038/s41593-025-02130-x, full publisher text inspected. It models acquisition across134mice and>3200sessions using dynamic infinite hidden semi-Markov states, allowing abrupt and gradual changes and individual paths. It is mouse acquisition data, not these80humans; its path-dependence motivation does not establish a teaching-condition effect here.
4. Urai et al., *Choice history biases subsequent evidence accumulation*, eLife8:e46331(2019), DOI10.7554/eLife.46331, full publisher text inspected. It compares history-dependent drift versus starting-point bias across human perceptual tasks and documents individual differences. History dependence and heterogeneous strategies are established; this study does not identify those within-trial accumulation mechanisms from choices alone.
5. Fernandez, Fengler & Urai2025, DOI10.1101/2025.08.22.671879, abstract and university-mirror PDF search text inspected. It fits diffusion decision models to62mice and compares strategy to prior human work. No overlap with this human release is identified in that bounded inspection. A direct mirror download timed out; complete PDF verification is not claimed.

Useful source URLs: https://zenodo.org/records/23072548 ; https://github.com/cocosys-lab/human_IBL_cursor/tree/47ac8356432972c7e6e5a887f15a7dd2d6c686ad ; https://github.com/cocosys-lab/2026-human-ibl-analyses/tree/1283c6ddd61fc17d9065a5b017d0e3cfd17535cb ; https://www.nature.com/articles/s41593-025-02130-x ; https://elifesciences.org/articles/46331 ; https://anneurai.net/publications/ .

## Access record and reproduction

Initial GitHub tree API downloads succeeded. A Python wrapper launching curl inside the sandbox then failed DNS for raw.githubusercontent.com. Its escalation request remained pending and was aborted after approximately20minutes; no denial or access-control bypass occurred. Direct `curl -L` commands subsequently used the session's existing approved prefix and acquired the pinned public files immediately. Do not reuse the failed wrapper as the recommended acquisition command. No full trial CSV was downloaded by this audit.

Offline input verification, from repository root:

```
.venv/bin/python campaigns/human_learning_routes_2026-10-28/experiments/source_audit/check_inputs.py
```

The source check needs the parent's input-only extraction plus pandas, NumPy and openpyxl. Saved source manifest records byte counts, hashes, upstream URLs and pinned commits. Sparse public version history, inaccessible full Hoxha manuscript, and unrecorded experimenter assistance remain source limitations; none supplies a reason to change the frozen prediction target after observing outcomes.
