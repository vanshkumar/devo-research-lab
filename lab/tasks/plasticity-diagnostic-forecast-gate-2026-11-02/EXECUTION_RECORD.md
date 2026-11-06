# Native execution record

Initial task native start 2026-11-03T04:19:10Z. Fixed prior 04:39:10 / original forecast reference 04:54:10 / protocol-or-CLOSE 05:04:10 / hard 05:29:10 UTC, including orientation. START followed actual task-only registration and controller PASS according to canonical PI's delivered message. No deadline reset or native goal was used by this worker.

Executed sequentially:

1. `pilot.py prepare`: launched 04:25:48Z, exec chunk90dae5/session96371; final native chunkedb1bb, exit0. Actual PREPARE_OUTPUT utc04:25:58Z. Full100task1Mupdates,212kcopy-probeupdates,BLIND forecast saved.
2. `pilot.py direct`: native chunk039529 exit0; output04:26:17Z. 12k true-label copy updates, zero continuing future updates; DIRECT forecast saved.
3. `pilot.py acquire`: native chunkcc6883 exit0; acquisition start/output04:26:21Z. 60k continuing future updates; both forecast hash links verified.
4. `audit.py`: native chunk936789 exit0; output04:27:24Z. 12k copied random-target replays on the already consumed six contexts; zero new evaluation, no predictor refit. All six feature/forecast and score replays exact. No branch qualifies for the conditional all-dead scalar trajectory reference; it is empty, not a verified60000reference.

Scientific process timers total11.28172275s before the bounded final packaging audit; startup/tool-host/native-runtime overhead remains unknown. Conservative process booking60seconds against900secondcap; measured RSS35,373,056bytes. All native jobs finished, no session/PID active. No science is scheduled after CLOSE.

A preliminary unsupported `wc -lc` orientation read was denied by the existing hook before execution; `wc -l` and numeric sed then worked. This read-option failure did not cause scientific execution, a new public operation, source access or a change in permissions. Public source failures are separately preserved in PUBLIC_OPERATIONS.json.
