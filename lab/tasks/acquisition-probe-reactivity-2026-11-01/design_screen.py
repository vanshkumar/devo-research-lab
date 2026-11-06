"""Routine design-cost reference and terminal feasibility decision, not a main test."""
from pathlib import Path
import datetime as dt
import json
import math
import resource

OUT = Path(__file__).resolve().parent
raw = (OUT / "FIRST_CALCULATION.json").read_bytes()
first = json.loads(raw)
assert first["max_scalar_reference_error"] < 2e-13
assert all(c["zero_equals_negative_feedback"] and c["omission_is_state_identity"] for c in first["constructed_cases"])

# A transparent scale illustration, not an optimized or frozen study allocation.
# One independent first response per learner targets a population mean. The
# bound also permits nonidentical independent Bernoulli success probabilities.
n = 400
j = 6
teachers = 2
out = dict(
    utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    decision="CLOSE prior/feasibility screen; no consequential main claim or independent review earned",
    reference_type="Elementary sampling variance and cohort cost; not a new theorem or experiment",
    scale_example=dict(independent_learners_per_teacher_endpoint=n,
                       endpoints=j, teachers=teachers,
                       separate_learners=n*j*teachers,
                       first_probe_responses=n*j*teachers,
                       per_endpoint_population_mean_worst_case_se=math.sqrt(.25/n),
                       independent_two_teacher_difference_worst_case_se=math.sqrt(.5/n),
                       normal_1_96_times_difference_se=1.96*math.sqrt(.5/n),
                       training_opportunities_cost="n * sum over endpoints and teachers of T[j,teacher], plus one terminal response per learner",
                       nonreactivity_scope="No earlier probe-induced changes for the fixed target first response; later acquisition is not measured in that same cohort",
                       precision_scope="Sampling SE under independent Bernoulli responses; not power, a guaranteed interval, latent competence precision, or a recommended human/animal sample size"),
    alternatives=dict(
        terminal_only="Already supplies the narrow common first-response population endpoint without requiring nonlearning post-response dynamics",
        matched_terminal_cohorts="Separate cohorts at earlier endpoints estimate a population trajectory, priced in independent learners and repeated acquisition, without recovering individual trajectories",
        repeated_full_feedback="Supported by the pinned update law as a changed training protocol; not an unchanged acquisition measurement",
        repeated_without_feedback="The pinned RNN has no separate feedback-withheld condition; zero aliases negative feedback",
        skip_update_or_zero_choice="Skipping is not earned by the learning hypothesis; zero choice encodes omission, inconsistent with a measured left/right response",
        extra_training_control="Additional versus substituted probe opportunities, feedback, session flags and protocol timing must be separated before attributing a change to measurement"),
    unearned=["No material 1pp/5pp disturbance threshold is certified", "No repeated-probe schedule or novel estimator tested", "No empirical/no-feedback dynamics identified", "No general impossibility or exhaustive novelty conclusion", "No main experiment, claim freeze, or review"],
    explicit_read_bytes=len(raw), peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
)
assert dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat("2026-11-01T15:53:30+00:00")
(OUT / "DESIGN_SCREEN.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out))
