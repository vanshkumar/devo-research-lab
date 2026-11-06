"""Independent scalar reconstruction from the saved matched endpoint arrays only."""
from pathlib import Path
import datetime as dt
import hashlib
import io
import json
import math
import resource
import zipfile
import numpy as np

OUT = Path(__file__).resolve().parent


def main():
    path = OUT/'MATCHED_PREDICTIONS.npz'
    data = path.read_bytes()
    h = hashlib.sha256(data).hexdigest()
    manifest = json.loads((OUT/'PREDICTION_MANIFEST.json').read_text())
    assert h == manifest['endpoint_file_sha256']
    assert manifest['completed'] == 24 and not manifest['new_cohort_scores_computed']
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        decoded = sum(x.file_size for x in z.infolist())
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        values = {k: z[k] for k in z.files}
    result = json.loads((OUT/'RESULT.json').read_text())
    assert len(values['subjects']) == 24
    assert not {'NYU-21', 'SWC_007'} & set(values['subjects'].tolist())
    target = values['observed_sides']
    prediction_arrays = {
        'saved_central_analytic': values['saved_central_analytic'],
        'saved_autonomous_sampled': values['saved_autonomous_particles'],
        'conditional_mixture_sampled': values['conditional_sampled_particles'],
        'conditional_mixture_analytic': values['conditional_analytic_particles']}
    labs = values['labs'].tolist()
    all_errors, reproduced = [], {}
    comparisons = 0
    for name, array in prediction_arrays.items():
        if array.ndim == 4:
            pred = [[[math.fsum(float(array[i, p, b, s]) for p in range(512))/512
                      for s in range(2)] for b in range(6)] for i in range(24)]
        else:
            pred = array.tolist()
        residual = [[(float(target[i, b, 0])+float(target[i, b, 1])-
                      pred[i][b][0]-pred[i][b][1])/2 for b in range(6)] for i in range(24)]
        cohort_residual = [math.fsum(residual[i][b] for i in range(24))/24 for b in range(6)]
        population = 100*math.fsum(abs(x) for x in cohort_residual)/6
        individual = 100*math.fsum(abs(x) for row in residual for x in row)/(24*6)
        side = 100*math.fsum(abs(float(target[i, b, s])-pred[i][b][s])
                            for i in range(24) for b in range(6) for s in range(2))/(24*6*2)
        scalar_bias = 100*math.fsum(cohort_residual)/6
        cohort_pred = [100*math.fsum((pred[i][b][0]+pred[i][b][1])/2 for i in range(24))/24 for b in range(6)]
        by_animal = [100*math.fsum(abs(x) for x in row)/6 for row in residual]
        by_lab = {}
        for lab in sorted(set(labs)):
            ix = [i for i, lab_i in enumerate(labs) if lab_i == lab]
            by_lab[lab] = 100*math.fsum(abs(math.fsum(residual[i][b] for i in ix)/len(ix))
                                       for b in range(6))/6
        current = dict(population_curve_mae_pp=population, individual_curve_mae_pp=individual,
                       individual_side_curve_mae_pp=side,
                       scalar_bias_observed_minus_prediction_pp=scalar_bias,
                       cohort_curve_percent=cohort_pred,
                       cohort_signed_residual_pp=[100*x for x in cohort_residual],
                       individual_curve_mae_pp_by_animal=by_animal, lab_curve_mae_pp=by_lab)
        expected = result['metrics'][name]
        for k, value in current.items():
            if isinstance(value, list):
                errors = [abs(a-b) for a, b in zip(value, expected[k])]
            elif isinstance(value, dict):
                errors = [abs(a-expected[k][lab]) for lab, a in value.items()]
            else:
                errors = [abs(value-expected[k])]
            all_errors.extend(errors)
            comparisons += len(errors)
        reproduced[name] = current
    assert max(all_errors) < 1e-10
    design = json.loads((OUT/'FROZEN_DESIGN.json').read_text())
    assert hashlib.sha256((OUT/'DESIGN.md').read_bytes()).hexdigest() == design['design_sha256']
    assert hashlib.sha256((OUT/'run.py').read_bytes()).hexdigest() == design['run_code_sha256']
    audit = dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                 status='verified_saved_scores_no_trajectories_or_raw_reads',
                 endpoint_sha256=h, scalar_comparisons=comparisons,
                 max_absolute_discrepancy_pp=max(all_errors), metrics=reproduced,
                 executed_run_and_design_pins_unchanged=True,
                 main_native_exit=120, main_shutdown_failure_retained=True,
                 resources=dict(compressed_input_bytes=len(data), full_zip_decoded_bytes=decoded,
                                other_context_code_allowance_bytes=1_000_000,
                                conservative_added_charge_bytes=len(data)+decoded+1_000_000,
                                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                original_raw_rows_returned=0, generated_trajectories=0,
                                network_operations=0, ingress_bytes=0))
    (OUT/'SAVED_SCORE_AUDIT.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps({k: v for k, v in audit.items() if k != 'metrics'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
