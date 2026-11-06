"""Offline reproduction from preserved inputs; never downloads or overwrites results.

Default: primary500-refit result, independent audits,12 original-control and8
repulsive-control replications, exact numerical comparisons. --full repeats all
1000 recovery datasets/5500bootstrap fits and both calibration/design studies.
"""
import argparse,json,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--full',action='store_true');ap.add_argument('--label',default=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));args=ap.parse_args()
    out=ROOT/'outputs/reproduction'/args.label;out.mkdir(parents=True,exist_ok=False)
    def run(script,*opts):
        cmd=[sys.executable,str(ROOT/script),*map(str,opts)]
        with (out/(Path(script).stem+'.log')).open('w') as log:subprocess.run(cmd,check=True,stdout=log,stderr=subprocess.STDOUT)
    run('experiments/test_model.py')
    run('experiments/source_audit/check_inputs.py')
    target=str((out/'primary').relative_to(ROOT))
    run('experiments/run_study.py','--out',target,'--bootstrap',500)
    orig=pd.read_csv(ROOT/'outputs/primary/trial_predictions.csv');new=pd.read_csv(out/'primary/trial_predictions.csv')
    assert orig.shape==new.shape
    numeric=['p_no_history','p_shared','p_condition','delta_log','delta_brier']
    errors={c:float(np.max(np.abs(orig[c]-new[c]))) for c in numeric}
    assert max(errors.values())<1e-9,errors
    a=pd.read_csv(ROOT/'outputs/primary/development_refit_bootstrap.csv');b=pd.read_csv(out/'primary/development_refit_bootstrap.csv')
    boot_error=float(np.max(np.abs(a.effect-b.effect)));assert boot_error<1e-8,boot_error
    run('experiments/source_audit/independent_score.py')
    run('experiments/design_audit/independent_validation_audit.py')
    label='offline_'+args.label
    run('experiments/recovery.py','--label',label,'--reps',100 if args.full else 2,'--bootstrap-outer',20 if args.full else 0,'--effect-bootstraps',50 if args.full else 0,'--refine-injection','--workers',2)
    actual=pd.read_csv(ROOT/'outputs/recovery/final/replicates.csv');replayed=pd.read_csv(ROOT/'outputs/recovery'/label/'replicates.csv')
    m=actual.merge(replayed,on=['scenario','replicate'],suffixes=('_original','_replayed'),validate='one_to_one')
    control_errors={c:float(np.max(np.abs(m[c+'_original']-m[c+'_replayed']))) for c in ['delta_log','effect','truth_effect']}
    assert max(control_errors.values())<1e-8,control_errors
    repulsive_label='offline_'+args.label
    run('experiments/repulsive_recovery.py','--label',repulsive_label,'--reps',100 if args.full else 2,'--workers',2)
    ra=pd.read_csv(ROOT/'outputs/repulsive_recovery/supplementary/replicates.csv');rb=pd.read_csv(ROOT/'outputs/repulsive_recovery'/repulsive_label/'replicates.csv')
    rm=ra.merge(rb,on=['scenario','replicate'],suffixes=('_original','_replayed'),validate='one_to_one')
    repulsive_errors={c:float(np.max(np.abs(rm[c+'_original']-rm[c+'_replayed']))) for c in ['delta_log','effect','truth_effect']}
    assert max(repulsive_errors.values())<1e-8,repulsive_errors
    if args.full:
        run('experiments/design_audit/calibration_challenge.py','--label','offline_calibration_'+args.label,'--reps',30,'--workers',2)
        run('experiments/design_audit/sample_size_challenge.py','--label','offline_design_'+args.label,'--reps',30,'--workers',2)
    run('experiments/reproduce_sensitivities.py','--label',args.label)
    result=dict(passed=True,offline=True,full=args.full,primary_prediction_max_errors=errors,primary_bootstrap_max_error=boot_error,recovery_replications_compared=len(m),recovery_max_errors=control_errors,repulsive_replications_compared=len(rm),repulsive_max_errors=repulsive_errors,output=str(out),note='Full mode includes complete simulation studies; default includes all empirical primary/bootstrap results, sensitivities and20 repeated control datasets. Original scientific outputs retained.')
    (out/'reproduction_result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
