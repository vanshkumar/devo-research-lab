"""Replay unchanged frozen analyses under a separate output root, offline."""
import argparse,json,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);args=ap.parse_args()
    out=ROOT/'outputs/reproduction'/args.label;assert (out/'primary/summary.json').exists()
    work=out/'sensitivity_workspace';work.mkdir(exist_ok=False)
    for name in ['inputs','protocol']:(work/name).symlink_to(ROOT/name,target_is_directory=True)
    (work/'outputs').mkdir();(work/'outputs/primary').symlink_to(out/'primary',target_is_directory=True)
    (work/'outputs/recovery').mkdir();(work/'outputs/recovery/final').symlink_to(ROOT/'outputs/recovery/final',target_is_directory=True)
    for name in ['sensitivities','lapse_challenge','time_history','diagnostics','simulation_compatibility']:
        code='import sys,runpy;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import analysis;analysis.ROOT=Path(sys.argv[2]);runpy.run_path(sys.argv[3],run_name="__main__")'
        with (out/(name+'_reproduction.log')).open('w') as log:
            subprocess.run([sys.executable,'-c',code,str(ROOT/'experiments'),str(work),str(ROOT/f'experiments/{name}.py')],stdout=log,stderr=subprocess.STDOUT,check=True)
    checked={}
    for name in ['sensitivities/summary.csv','lapse_challenge/summary.csv','time_history/participant_scores.csv','diagnostics/condition_coverage_performance.csv','simulation_compatibility/discrete_accounts.csv']:
        a=pd.read_csv(ROOT/'outputs'/name);b=pd.read_csv(work/'outputs'/name);assert a.shape==b.shape
        errors=[]
        for c in a.select_dtypes(include='number'):
            av=a[c].to_numpy();bv=b[c].to_numpy();assert np.array_equal(np.isnan(av),np.isnan(bv))
            mask=np.isfinite(av);err=float(np.max(np.abs(av[mask]-bv[mask]))) if mask.any() else 0.;assert err<1e-9,(name,c,err);errors.append(err)
        checked[name]=max(errors) if errors else 0.
    result=dict(passed=True,offline=True,unchanged_frozen_code=True,output_root_redirect='Only analysis.ROOT redirected in child processes; input/protocol and already-verified primary outputs linked. No original result overwritten.',numeric_max_errors=checked)
    (out/'sensitivity_reproduction_result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
