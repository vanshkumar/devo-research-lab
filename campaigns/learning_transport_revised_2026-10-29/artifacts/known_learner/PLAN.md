# Conditional known-learner recovery and transport control

Declared 2026-10-29 before this control's simulated scored outcomes. This is a
control conditional on real consumed prefixes, not new whole-animal recovery,
biological retention inference, or any Pan-Vazquez evaluation.

Use one full-horizon original fitting animal from each of the seven fitting
laboratories: choose the eligible subject with the lexicographically smallest
SHA256(subject) digest. Read only each animal's first 1,000 already-consumed
trial rows. Obtain the subsequent 3,000 session-start indicators from saved
finite-fit forecasts; read no actual future responses for this control.

The known process is the same frozen within-session GRU with shared pretrial
session coefficient rho=0.8, applied coherently in prefix MAP/Fisher calibration
and simulation. This is a declared motivating control value, not a selected
biological parameter. Generate standard-policy truth with 2,048 particles and
subject seed +910000. Each simulated learner produces its own choices,
omissions, feedback and trainer responses. Prefix states and omission nuisance
uncertainty retain their existing recipes.

Compare all six saved 256-particle standard-policy rho-grid forecasts at these
seven prefixes with the independent truth's expected exact-100% six-bin
equal-side accuracy curves. Minimize the same equal-lab population-curve MAE
and select the largest rho within0.001 of the minimum. Save the complete loss
profile. Parameter recovery succeeds if rho=0.8 is selected; predictive recovery
is a separate weaker success if the selected prescription has mean-curve MAE
no more than0.01 against the known expected law. Do not refine the grid, change
seeds or repair a failed check.

Then generate 512-particle forecasts from the selected control rho under both
the standard and fixed external trainer using the original subject seed.
Independent fixed-policy truth uses rho=0.8 with2,048particles and subject
seed+910000. Compare fixed-policy growth at512particles with the same truth.
Report expected-law curve error, conditional simulation standard errors,
per-prefix errors, the fixed-policy predictive advantage over growth, and the
population trainer contrast. Expected-law readiness is mean-curve error<=0.01
under both trainers. Failure is retained, not repaired. This checks an expected
conditional law, not noisy-cohort power or biological model correctness.

Freeze this plan, control code, common/session model code, inherited updater and
bank, fit allocation/disposition and all42selected grid files before simulation.
All results and execution logs remain in this control namespace. No protected
prefixes or independent actual outcomes are accessed.
