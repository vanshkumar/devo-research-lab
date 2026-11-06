"""Frozen exact calibration witness, plus coupled observation-law checks.

No empirical input, external packages, fits to old records, or power/sample-size
calculation. The exact table is fitted before profiling two rival mechanisms.
"""
from fractions import Fraction as F
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import random
import resource

HERE = Path(__file__).resolve().parent
X, b, ar, alpha0, ac = F(3,2), F(1,5), F(97,100), F(7,10), F(17,20)
M = sum(ar**h for h in range(5))/5
margin = F(1,5)
d = margin/(X*M)

def ols2(rows, ys):
    # Exact independently calculated two-column normal equations.
    xx = sum(x*x for x,c in rows)
    cc = sum(c*c for x,c in rows)
    xc = sum(x*c for x,c in rows)
    xy = sum(x*y for (x,c),y in zip(rows,ys))
    cy = sum(c*y for (x,c),y in zip(rows,ys))
    det = xx*cc-xc*xc
    return ((xy*cc-cy*xc)/det, (cy*xx-xy*xc)/det)

def logistic(x):
    return 1/(1+math.exp(-x))

def main():
    signed = []
    exact_error = F(0)
    rng = random.Random(483291)
    coupled_max = 0.0
    coupled_count = 0
    round_mismatches = 0
    choice_mismatches = 0
    for direction in [-1,1]:
        perJ = []
        curve_obs = [direction*X*d*ar**h for h in range(5)]
        for J in [0,1]:
            aN = ac
            aP = ac + direction*(2*J-1)*d/2
            midpoint_a = (aN+aP)/2
            alpha = alpha0 + direction*J*d
            report_k = (alpha-midpoint_a)/b
            rows, ys, rs = [], [], []
            biases = []
            for sign in [-1,1]:
                x = sign*X
                for cursor in [F(-1),F(0),F(1)]:
                    y = alpha*x+b*cursor
                    eN = cursor+(alpha-aN)*x/b
                    eP = cursor+(alpha-aP)*x/b
                    report = cursor+report_k*x
                    qN, qP = report-eN, report-eP
                    # Both fully specified mechanisms generate the same data.
                    residuals = [aN*x+b*eN-y, aP*x+b*eP-y,
                                 eN+qN-report, eP+qP-report]
                    exact_error = max(exact_error, *(abs(v) for v in residuals))
                    biases.extend([abs(qN),abs(qP)])
                    rows.append((x,cursor)); ys.append(y); rs.append(report)
                    # All randomized visual probes, not one chosen threshold.
                    for probe in [F(i,4) for i in range(-16,17)]:
                        logitN = eN+qN-probe
                        logitP = eP+qP-probe
                        assert logitN == logitP
                        pN, pP = logistic(float(logitN)/3), logistic(float(logitP)/3)
                        coupled_max = max(coupled_max,abs(pN-pP))
                    for rep in range(12):
                        # Same innovations prove equality of the entire law;
                        # they do not estimate empirical noise or a rate.
                        report_branch = rep % 2
                        innovation = rng.gauss(0,.4)
                        yN = float(aN*x+b*eN)+innovation+.01*report_branch
                        yP = float(aP*x+b*eP)+innovation+.01*report_branch
                        S = float(alpha0*x+b*cursor)+innovation+.01*report_branch
                        Z = float(direction*J*d*x)
                        for h in range(5):
                            obs_noise = rng.gauss(0,.2)
                            coupled_max = max(coupled_max,abs(yN-yP),abs(yN-(S+Z)))
                            # Heading/endpoints and active/passive physical-hand
                            # measurement kernels depend on behavioral Y here.
                            for loading,offset in [(1,0),(1,.15),(.7,.3),(1,-.2)]:
                                chN=loading*yN+offset+obs_noise
                                chP=loading*yP+offset+obs_noise
                                coupled_max=max(coupled_max,abs(chN-chP))
                            proc_noise=rng.gauss(0,.05)
                            yN=float(ar)*yN+proc_noise
                            yP=float(ar)*yP+proc_noise
                            S=float(ar)*S+proc_noise
                            Z=float(ar)*Z
                        rnoise=rng.gauss(0,2)
                        rN=float(eN+qN)+rnoise
                        rP=float(eP+qP)+rnoise
                        for step in [.1,1,5]:
                            round_mismatches += round(rN/step) != round(rP/step)
                        random_probe=rng.uniform(-4,4)
                        u=rng.random()
                        choice_mismatches += (u<logistic((rN-random_probe)/3)) != (u<logistic((rP-random_probe)/3))
                        coupled_count += 1
            fit_alpha, fit_b = ols2(rows,ys)
            fit_k, fit_scale = ols2(rows,rs)
            assert (fit_alpha,fit_b)==(alpha,b)
            assert (fit_k,fit_scale)==(report_k,F(1))
            report_as_true_a = fit_alpha-fit_b*fit_k
            assert report_as_true_a==midpoint_a
            perJ.append({"J":J,"null_intrinsic_a":float(aN),"changed_intrinsic_a":float(aP),
                         "fitted_observable_alpha":float(fit_alpha),"fitted_cursor_gain":float(fit_b),
                         "fitted_report_cursor_scale":float(fit_scale),"fitted_report_state_loading":float(fit_k),
                         "report_as_true_intrinsic_a":float(report_as_true_a),"max_abs_report_bias_deg":float(max(biases)),
                         "max_abs_report_bias_fraction":str(max(biases))})
        # Scalar check derived WITHOUT recurrence: eN-eP = (aP-aN)x/b.
        # A common report has minimax radius half their separation in each cell.
        lower_bound_cell = X*d/(4*b)
        assert all(F(row['max_abs_report_bias_fraction'])==lower_bound_cell for row in perJ)
        true_theta_N = F(0)
        true_theta_P = X*M*(F(direction)*d)
        fitted_midpoint_theta = X*M*((ac+direction*d/4)-(ac-direction*d/4))
        assert true_theta_P==direction*margin
        assert fitted_midpoint_theta==direction*margin/2
        signed.append({"direction":direction,"observable_five_probe_curve_deg":[float(v) for v in curve_obs],
                       "observable_theta_deg":float(sum(curve_obs)/5),"null_transition_contribution_deg":float(true_theta_N),
                       "changed_transition_contribution_deg":float(true_theta_P),"report_as_true_estimate_deg":float(fitted_midpoint_theta),
                       "minimum_symmetric_cell_bias_for_this_affine_pair_deg":float(lower_bound_cell),"cells":perJ})
    assert exact_error==0
    assert coupled_max<1e-13 and round_mismatches==choice_mismatches==0
    # If |bias at each signed precursor/event cell| <= B, the signed
    # half-contrast event difference is <= 2B. Its theta half-width is 2bMB.
    # Thus 0 and +/-.2 identified sets overlap when 4bMB >= .2.
    bound = margin/(4*b*M)
    frontier=[]
    for B in [F(0),F(1,10),F(1,5),bound,F(1,2),F(1)]:
        half_width=2*b*M*B
        frontier.append({"cell_bias_bound_deg":float(B),"theta_systematic_half_width_deg":float(half_width),
                         "two_target_uncertainty_overlap_at_point2":4*b*M*B>=margin})
    expression=[]
    for kappa in [F(0),F(1,2),F(9,10),F(1)]:
        # Here B_L bounds bias in the secondary channel's ALREADY FORMED
        # signed five-probe scalar, not a per-trial/cell/report error.
        expression.append({"hypothetical_known_expression_loading":float(kappa),
                           "required_scalar_bias_bound_strictly_below_deg":float(margin*abs(1-kappa)/2),
                           "inverse_noise_amplification":None if kappa==1 else float(1/abs(1-kappa)),
                           "identification_at_kappa":kappa!=1})
    result={"created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"kind":"exact closure test, not empirical recovery or calibrated simulation power",
            "synthetic_reference":{"precursor_heading_deg":float(X),"gain":float(b),"probe_retention":float(ar),"five_probe_average_multiplier":float(M)},
            "exact_max_residual_deg":float(exact_error),"signed_witnesses":signed,
            "continuous_2afc_quantized_branch_heterogeneous_noise_check":{"coupled_episodes":coupled_count,"max_float_discrepancy":coupled_max,
               "shared_quantizer_mismatches":round_mismatches,"shared_2afc_response_mismatches":choice_mismatches,"seed":483291,
               "noise_note":"supplied correlated channel/process/report noise and report-branch effect; not empirical variances; equality of laws follows analytically"},
            "systematic_error_frontier":frontier,"critical_cell_bias_deg":float(bound),
            "critical_differential_report_bias_deg":float(2*bound),
            "known_storage_anchor_reference_only":expression,
            "collection_decision":{"new_people":0,"new_episodes":0,"new_reaches":0,"new_reports":0,
                "reason":"do not commission this mechanistic assay without independently justified signal/criterion and expression anchors; no separating N exists for the exhibited pair",
                "conditional_hand_report_extra_seconds_per_report":.842,"goal_report_active_passive_setup_and_reacquisition_times":"not certified; not priced as zero"},
            "checks":{"both_signed_boundaries":True,"gain_and_report_scale_fitted_from_crossed_table":True,
                       "zero_residual_fitted_rivals":True,"independent_scalar_lower_bound":True,"full_feasible_recovery_or_coverage":"UNRUN; separation not earned"},
            "resources":{"ru_maxrss_native_bytes_macos":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                         "public_empirical_raw_bytes":0,"old_empirical_raw_bytes":0,"source_hash_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                         "unmeasured":"physical IO, complete context/import/provider/toolhost/runtime bytes and failed/acquisition peaks"}}
    (HERE/'CALIBRATION_FRONTIER.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({"created_utc":result['created_utc'],"exact_max_residual_deg":float(exact_error),
                      "signed_target_deg":[w['changed_transition_contribution_deg'] for w in signed],
                      "naive_report_as_true_estimate_deg":[w['report_as_true_estimate_deg'] for w in signed],
                      "critical_cell_bias_deg":float(bound),"critical_differential_bias_deg":float(2*bound),
                      "coupled_check":result['continuous_2afc_quantized_branch_heterogeneous_noise_check'],"resources":result['resources']},indent=2))

if __name__=='__main__':
    main()
