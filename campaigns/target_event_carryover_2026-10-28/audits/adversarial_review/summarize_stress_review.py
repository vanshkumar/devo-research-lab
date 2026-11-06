from pathlib import Path
import json,csv,numpy as np
R=Path(__file__).resolve().parents[2]
r=json.loads((R/'outputs/state_models_stress.json').read_text())['records'];f=json.loads((R/'outputs/state_models_optimizer_fairness.json').read_text())['records'];b=json.loads((R/'outputs/state_models_bootstrap.json').read_text())
summary=[]
for key in sorted(set((x['scenario'],x['target_theta']) for x in r)):
 rows=[x for x in r if (x['scenario'],x['target_theta'])==key];good=[x for x in rows if not x['diagnostic_only']]
 summary.append(dict(scenario=key[0],target=key[1],n=len(rows),mean_theta=float(np.mean([x['fit_theta'] for x in rows])),coverage=sum(x['coverage'] for x in rows),reject_zero=sum(x['detect_zero_exclusion'] for x in rows),false_equivalence=sum(x['false_equivalence_at_or_outside_boundary'] for x in rows),diagnostic=sum(x['diagnostic_only'] for x in rows),unflagged_n=len(good),unflagged_false_equivalence=sum(x['false_equivalence_at_or_outside_boundary'] for x in good)))
mx=max(abs(x['difference']) for x in f)
out=dict(scenarios=summary,multistart=dict(n=len(f),max_absolute_theta_change=mx,any_inference_changed=any((x['coverage']!=(x['old_ci95'][0]<=.2<=x['old_ci95'][1])) for x in f)),bootstrap=dict(n=len(b['records']),ci95=b['percentile_ci95'],slow_upper_bound=b['slow_upper_bound_count']))
(R/'audits/adversarial_review/secondary_stress_review.json').write_text(json.dumps(out,indent=2)+'\n')
lines=['# Secondary state-model stress review','',
'2026-10-28. This reviews the original unweighted two-state efficiency model. Any later covariance-aware repair needs its own calibration and must remain separately labeled. No reserved or external outcomes were accessed.','',
'## Verdict','',
'The original secondary model detects injected signed effects efficiently, but its nominal interval is not calibrated for broad observable equivalence. At a correctly specified fast-state physical effect of+0.2°,14/100 intervals falsely lie wholly inside±0.2°;4 of those occur among35 fits not flagged diagnostic. Negative fast modulation gives6/100 false-equivalence intervals. Slow-state negative modulation gives10/50. Rebound with true five-lag mean zero is incorrectly declared nonzero36/50 times. The narrow development interval and narrow empirical bootstrap interval cannot be used as general evidence of a small physical propagation effect.','',
'## Full stress results','',
'Each row uses all20development input schedules with synthetic outcomes only. The target physical scalar is calibrated over actual future event histories. Raw counts avoid implying more precision than100/50replicates.','',
'| Challenge | True θ | Mean fitted θ | n | CI covers truth | CI excludes zero | False equivalence | Diagnostic flags |','|---|---:|---:|---:|---:|---:|---:|---:|']
for x in summary:lines.append(f"| {x['scenario']} | {x['target']:+.1f} | {x['mean_theta']:+.3f} | {x['n']} | {x['coverage']} | {x['reject_zero']} | {x['false_equivalence']} | {x['diagnostic']} |")
lines+=['',
'“False equivalence” means the entire nominal95%CI is inside±0.2° while the generating physical scalar is at the boundary. It is not the same as a failure to detect zero. Every slow-modulation fit is flagged diagnostic; its failure cannot be hidden by reporting only regular fits, because the model never yields a regular fit in that challenge. Conversely, false equivalence in fast positive modulation remains among unflagged fits.','',
'## Optimizer and bootstrap checks','',
'An exact empirical-rule multistart comparison was performed on30positive fast-effect replicates, including20evenly spaced indices and ten worst-bias examples. Maximum change inθ is '+f'{mx:.3g}'+'°. Therefore the observed recovery failures in this check are not explained by fewer optimizer starts in simulation. Full per-start status and losses are preserved by the model author.','',
'The200stratified empirical participant bootstraps give a narrow percentile interval '+str(b['percentile_ci95'])+'°, while'+str(b['slow_upper_bound_count'])+'/200slow rates hit the upper bound. This demonstrates sampling stability of the fitted criterion in this development sample. It does not repair known-generator bias, misspecification or coverage.','',
'## Confirmed failure mechanism and next requirement','',
'The independent exact expected-loss calculation in `profile_noise_bias.json` shows that colored noise plus person-specific linear profiling can make wrong retention parameters outperform the true parameters in expected unweighted SSE, despite equal model rank and a correctly specified mean family. Cluster-robust uncertainty estimates sampling variation around the fitted criterion; it does not remove this criterion bias.','',
'A bounded covariance-aware or explicitly simulation-calibrated repair is scientifically justified. Any repaired interval must pass independent signed-effect and readout/slow-state challenges before supporting equivalence. A successful repair can supply a conditional bound or frozen prediction; it must not replace the original observable endpoint or silently spend validation on model selection.','',
'Exact source data: `outputs/state_models_stress.json`, `outputs/state_models_optimizer_fairness.json`, `outputs/state_models_bootstrap.json`. Independent physical truth check: `slow_truth_check.json`.']
(R/'audits/adversarial_review/SECONDARY_STRESS_REVIEW.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(out,indent=2))
