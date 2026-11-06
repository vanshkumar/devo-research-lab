# Independent reproduction artifacts

Disposition: [BANK scoped negative/CLOSE repair](REVIEW.md). [RESULT](RESULT.md) and [STATE](STATE.md) state exact scope, inherited claims and terminal delivery status. Reviewer is distinct from the author; no original code/data/report was modified.

The actual executions, in order, used only system Python/standard library, one process/thread at a time:

```sh
python3 -B lab/reviews/plasticity-renewal-order-2026-11-02/reconstruct.py
python3 -B lab/reviews/plasticity-renewal-order-2026-11-02/contrary.py
python3 -B lab/reviews/plasticity-renewal-order-2026-11-02/verify.py
python3 -B lab/reviews/plasticity-renewal-order-2026-11-02/closeout.py
```

These commands document the saved execution, not permission to overwrite it. For a separately authorized reproduction use a FRESH sibling review directory, copy the four scripts, CONTRARY_FREEZE.md and historical RECONSTRUCTION_FAILURE_RESOURCES.json into it, and run the scripts there in this order. Relative source paths still point to the immutable original tasks. Contrary/verification refuse existing output files. The historical failed-pass receipt is copied only so closeout preserves the additive failure charge; reproducing the deliberately wrong initial reference is unnecessary. No broad training rerun/dependency download is needed.

- [reconstruct.py](reconstruct.py) → [RECONSTRUCTION.json](RECONSTRUCTION.json): independent dense LTU/ReLU/scoring/RNG equations; every original teacher/boundary/arm/age/competence summary; all56pairwise gates; Git/code/freeze pins. Its initial cache/online-history inheritance is qualified and later cache inheritance superseded by verification.
- [CONTRARY_FREEZE.md](CONTRARY_FREEZE.md), [receipt](CONTRARY_EXECUTION_RECEIPT.json), [contrary.py](contrary.py) → [CONTRARY.json](CONTRARY.json): ONE fixed-state exact-old-input-mean challenge, all334sampled events including48explicit exclusions. No optimizer, new teacher or long-term learning replay. Oracle uses privileged old inputs, with target labels scoring only.
- [verify.py](verify.py) → [VERIFICATION.json](VERIFICATION.json): independently trains first10,000examples for all seven neural arms and all8teachers; separately replays every full cache stream/boundary/bin/hit/final state. Later99neural learning histories remain inherited.
- [closeout.py](closeout.py) → [FINAL_AUDIT.json](FINAL_AUDIT.json)/[RESOURCES.json](RESOURCES.json): output/summary/code/freeze pins, all seven frozen gate agreements, accepted scope and additive resources. [USAGE_CHECKPOINT.json](USAGE_CHECKPOINT.json) is normalized manual telemetry.
- [reconstruct_beta075_failed.py](reconstruct_beta075_failed.py), [failure](RECONSTRUCTION_FAILURE.txt), [failure resources](RECONSTRUCTION_FAILURE_RESOURCES.json) and [correction](RECONSTRUCTION_CORRECTION.md): preserved reviewer mistake, not an author revision or the ONE contrary.
- [NATIVE_PROCESS_RECEIPTS.md](NATIVE_PROCESS_RECEIPTS.md) records actual process exits and the capacity interruption. [PROPOSED_LEARNING.md](PROPOSED_LEARNING.md) is for PI integration; shared LEARNINGS was untouched.
- [MANIFEST.json](MANIFEST.json) pins the saved scientific artifacts and verifies local Markdown links. Mutable BRIEF/STATE and the manifest's own receipts are excluded from its recursive hashes.

Scientific scalars should agree within the explicitly recorded floating tolerances; runtimes/RSS/timestamps/paths/hashes of newly encoded receipts need not be byte-identical. Original source paths/pins are in RECONSTRUCTION/FINAL_AUDIT. OriginalTorch/float32/RNG/historical deployment/intent, t7coverage and equal total storage are not certified. Cached CVPR primary excerpts were inspected; Nature article Algorithm1 inspection remains inherited rather than directly re-fetched in this zero-public-operation review.

All8original teachers101contexts/1.01Mfast draws each, scorer supports, states and new diagnostic outcomes are consumed. No old protected empirical records or fits were used. Preserve original46publicops/168MBUNCERTIFIEDingress/700MBread/9.13Mgenerated examples and resource/source failures, plus this review's separate600MBcharge and unknown wrapper/physicalIO peaks. Task completion changes no lab-goal/heartbeat state.
