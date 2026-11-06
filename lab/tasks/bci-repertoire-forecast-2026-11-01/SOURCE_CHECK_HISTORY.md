# Source-check changes and failed passes

These are deterministic source-reconstruction checks, not a development model revision or an evaluation gate.

- Initial ordinary-read command used shell composition and was denied before execution. The later `.venv/bin/python` symlink listing was denied as an escaping path; no file was read. Used system Python with the existing repository package directory instead.
- Initial one-file HTTPS attempt failed in the sandbox at DNS resolution. Its JSON is preserved in ACQUIRE_EXAMPLE_FAILED_SANDBOX.json. The same capped, pinned public-file read was approved by platform review and then succeeded. No alternate endpoint or download chain was used.
- 04:42:37 UTC: measured raw-spike and factor decoder reconstruction succeeded, but direct comparison of projected mm/s with stored Progress was wrong by a factor of dt=0.045. FIRST_DATA_CHECK_INITIAL.json and first_data_check_initial.py preserve this failure and the first warnings.
- 04:43:40 UTC: diagnostic values showed the stored Progress equals dt times the raw-spike decoder projection. It is displacement per bin in this export. This is a measured export-unit distinction, not evidence the paper is invalid.
- A subsequent source assertion incorrectly required the factor-derived Progress to agree within 1e-10 mm/bin despite the already measured roughly 3e-8 mm/s raw-spike/factor decoder representation discrepancy. It failed at 1.383542169719476e-9 mm/bin. The raw-spike dt-scaled projection agrees within 8.881784197001252e-15 mm/bin. The final check preserves both residuals and uses the deterministic Cauchy-Schwarz roundtrip bound for the factor route; it changes no hypothesis/model/utility criterion.
- Matrix multiplication emitted the known environment's divide/overflow/invalid warnings on finite inputs. MATRIX_VALIDATION.json records those warnings, confirms finite outputs, and compares the original matrix product with explicit einsum contractions (maximum difference 5.551115123125783e-17). Explicit contractions are used for reconstruction. The warnings are retained rather than interpreted as biological or data failures.

The source gate remains failed for the intended comparison: the only certified perturbed measured example is one selected endpoint session without the initial post-change learning sequence. No main design or evaluation was opened, repaired, or substituted.
