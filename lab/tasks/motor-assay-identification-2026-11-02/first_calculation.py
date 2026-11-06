"""Exact synthetic rival/observation reference. No empirical inputs; stdlib only."""
from fractions import Fraction as F
import datetime as dt
import json
from pathlib import Path
import resource

OUT = Path(__file__).resolve().parent
X, probe_a, alpha0, b, lam, astar = F(3, 2), F(97, 100), F(7, 10), F(1, 5), F(2, 5), F(97, 100)
M = sum(probe_a ** h for h in range(5)) / 5
delta = F(1, 5) / (X * M)

def maximum(values):
    return float(max(values, default=F(0)))

def main():
    residuals = {k: [] for k in ["endpoint_heading", "perfect_collinear_reports", "random_offsets_biased_reports", "expression_all_channels", "external_report_calibration"]}
    perfect_excited_discrepancies = []
    records = []
    # Precursor sign and randomized event cursor offset are independently crossed.
    for sign in [-1, 1]:
        x = sign * X
        for J in [0, 1]:
            alpha = alpha0 + J * delta
            at = alpha + b * lam
            bgain_rival = (astar - alpha) / lam
            # The no-offset perfect error report is shared by both worlds.
            e0 = -lam * x
            xt = at * x + b * e0
            xe = astar * x + bgain_rival * e0
            residuals["perfect_collinear_reports"].append(abs(xt - xe))
            for c in [F(-1), F(0), F(1)]:
                et = c - lam * x
                xt = at * x + b * et
                # With perfect reports and excitation the same gain rival fails.
                xe_perfect = astar * x + bgain_rival * et
                perfect_excited_discrepancies.append(abs(xt - xe_perfect))
                # Fixed-retention/error rival with event x state report bias.
                lame = (astar - alpha) / b
                ee = c - lame * x
                report_bias = (lame - lam) * x
                xe = astar * x + b * ee
                report_t, report_e = et, ee + report_bias
                residuals["random_offsets_biased_reports"].extend([abs(xt - xe), abs(report_t - report_e)])
                # An external cursor-offset calibration passes with unit slope
                # in BOTH worlds, including at nonzero precursor state.
                residuals["external_report_calibration"].append(abs(((c + 1 - lame*x + report_bias) - report_e) - 1))
                # Independent expression construction: storage has no J effect.
                S, Z = alpha0 * x + b * c, J * delta * x
                for h in range(5):
                    # heading, endpoint, hand-localization, goal-error and
                    # passive matched-hand reports can share observable Y.
                    Y = S + Z
                    channels_t = [xt, xt + F(1, 10), xt + F(1, 4), F(2) - xt, xt]
                    channels_e = [Y, Y + F(1, 10), Y + F(1, 4), F(2) - Y, Y]
                    residuals["expression_all_channels"].extend(abs(u-v) for u,v in zip(channels_t, channels_e))
                    residuals["endpoint_heading"].extend([abs(xt-xe), abs(xt-Y)])
                    xt *= probe_a
                    xe *= probe_a
                    S *= probe_a
                    Z *= probe_a
                records.append({"sign":sign,"event":J,"offset":float(c),"intrinsic_transition_T":float(at),"fixed_transition_E":float(astar),"gain_perfect_collinear_E":float(bgain_rival),"perceived_error_E":float(ee),"report_bias_E":float(report_bias)})
    # Independent scalar analytic calculation; includes the ORIGINAL signed
    # half difference and five-probe averaging, not a latent parameter target.
    effect_by_h = [X * delta * probe_a**h for h in range(5)]
    analytic_theta = sum(effect_by_h)/5
    explicit_cells = {}
    for s in [-1,1]:
        for J in [0,1]:
            explicit_cells[s,J] = [s*X*(alpha0+J*delta)*probe_a**h for h in range(5)]
    scalar_theta = sum(((explicit_cells[1,1][h]-explicit_cells[1,0][h])-(explicit_cells[-1,1][h]-explicit_cells[-1,0][h]))/2 for h in range(5))/5
    assert scalar_theta == analytic_theta == F(1,5)
    assert all(max(v, default=F(0)) == 0 for v in residuals.values())
    # Each J-specific perfect-report design: determinant of population Gram.
    zero_rows = [(s*X,-lam*s*X) for s in [-1,1]]
    excited_rows = [(s*X,c-lam*s*X) for s in [-1,1] for c in [F(-1),F(0),F(1)]]
    def gram_det(rows):
        xx=sum(x*x for x,e in rows); ee=sum(e*e for x,e in rows); xe=sum(x*e for x,e in rows)
        return xx*ee-xe*xe
    data = {
      "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "scope":"synthetic exact reference; no empirical files read; supplied observation alternatives, not certified biological models",
      "parameters":{"X_heading_deg":float(X),"alpha0":float(alpha0),"delta":float(delta),"b":float(b),"lambda_T":float(lam),"astar":float(astar),"probe_retention":float(probe_a)},
      "max_exact_residual_deg":{k:maximum(v) for k,v in residuals.items()},
      "perfect_report_excited_old_rival_max_gap_deg":maximum(perfect_excited_discrepancies),
      "gram_determinant":{"no_offset":float(gram_det(zero_rows)),"crossed_offsets":float(gram_det(excited_rows))},
      "five_probe_effect_curve_deg":[float(v) for v in effect_by_h],
      "theta_analytic_and_scalar_deg":float(analytic_theta),
      "differential_error_report_bias_at_event_deg":float(delta*X/b),
      "rival_records":records,
      "resource":{"ru_maxrss_native":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"platform_note":"macOS ru_maxrss is bytes; host/provider/runtime/physical IO and context/import bytes not fully measured"}
    }
    (OUT/'FIRST_CALCULATION.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:v for k,v in data.items() if k != 'rival_records'},indent=2))

if __name__ == '__main__':
    main()
