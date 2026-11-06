"""Compact derived diagnostics from review JSON; no observation/prediction reread."""
import json
import math
from pathlib import Path

root=Path(__file__).resolve().parent
recon=json.loads((root/"RECONSTRUCTION.json").read_text())
contrary=json.loads((root/"CONTRARY.json").read_text())
first=json.loads((root/"FIRST_CALCULATION.json").read_text())
rows=contrary["records"]
initial={r["seed"]:r["initial"] for r in rows}
by_method={m:[r for r in rows if r["method"]==m] for m in ("mean","gaussian","ball","truth")}
boundary=recon["ball_boundary_checks"]
primary=recon["primary_n32_quadratic_optima"]
asym=recon["asymptotic_mean"]

def median(values):
    values=sorted(values);n=len(values)
    return (values[n//2-1]+values[n//2])/2 if n%2==0 else values[n//2]

summary=dict(
    main_gold_max_discrepancy=recon["main_gold_max_abs_discrepancy"],
    main_initial_max_discrepancy=recon["main_initial_max_abs_discrepancy"],
    main_binary_disagreements=recon["main_binary_disagreements"],
    max_action_difference=recon["max_action_difference"],max_path_difference=recon["max_path_difference"],
    main_box_max_objective_gap=max(r["objective_gap"] for r in primary),
    main_box_max_endpoint_difference=max(r["max_endpoint_difference"] for r in primary),
    main_ball_tangent_identical_paths=sum(r["tangent_ball_path_identical"] for r in boundary),
    main_ball_endpoints_outside_estimated_support=sum(r["endpoint_outside"] for r in boundary),
    main_ball_queried_outside_count=sum(r["queried_outside"] for r in boundary),
    main_ball_cases_any_query_outside=sum(r["queried_outside"]>0 for r in boundary),
    main_ball_min_query_margin=min(r["estimated_radius"]-r["maximum_queried_radius"] for r in boundary),
    mean_infinite_tutor_median_error=recon["asymptotic_mean_median_error"],
    asymptotic_interior_cases=recon["asymptotic_mean_interior_cases"],
    interior_formula_max_action_difference=max(r["interior_formula_action_discrepancy"] for r in asym if r["interior"]),
    contrary_initial_median=median(list(initial.values())),
    contrary_initial_mean=sum(initial.values())/64,
    original_initial_mean=first["summary"]["32"]["absent"]["mean_final"],
    contrary_initial_outside_disk_cases=sum(r["initial"]>.01*r["initial_original"]+1e-12 for r in by_method["gaussian"]),
    contrary_metrics={},
    contrary_quadratic_optima={})
for method,selected in by_method.items():
    old=first["summary"]["32"][method]
    summary["contrary_metrics"][method]=dict(
        acquired=sum(r["acquired"] for r in selected),mean_final=sum(r["final"] for r in selected)/64,
        original_mean_final=old["mean_final"],
        mean_final_ratio=(sum(r["final"] for r in selected)/64)/old["mean_final"],
        median_removal=median([r["removal"] for r in selected]),
        final_error_max=max(r["final"] for r in selected))
for method in ("mean","gaussian"):
    selected=[r for r in contrary["gaussian_mean_box_checks"] if r["method"]==method]
    summary["contrary_quadratic_optima"][method]=dict(
        max_actor_objective_gap=max(r["actor_objective_gap"] for r in selected),
        mean_optimum_true_error=sum(r["optimal_true_error"] for r in selected)/64,
        optimal_acquisitions=sum(r["optimal_true_error"]<=.05*initial[r["seed"]] for r in selected),
        actor_acquisitions=sum(r["acquired"] for r in by_method[method]))
(root/"DERIVED_SUMMARY.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n")
print(json.dumps(summary,indent=2))
