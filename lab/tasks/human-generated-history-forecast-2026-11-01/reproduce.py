"""Replay this bounded test into a NEW scoped folder, preserving earned outputs."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
import sys
sys.dont_write_bytecode=True
import argparse, json, shutil
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',default='reproduction/verified_offline',help='New folder beneath this task directory')
    args=parser.parse_args()
    original=Path(__file__).resolve().parent
    out=(original/args.out).resolve()
    out.relative_to(original)
    assert out!=original and not out.exists(),'Choose a new, nonexistent folder within this task'
    out.mkdir(parents=True)
    for name in ('PROTOCOL.md','forward.py','FORECAST_INPUTS.json','FEASIBILITY.json'):
        shutil.copyfile(original/name,out/name)
    sys.path.insert(0,str(original))
    import forward
    forward.HERE=out
    for stage in ('checks','freeze','forecast','score'):
        forward.PINS=[]
        sys.argv=['forward.py',stage]
        forward.main()
    import numpy as np
    with np.load(original/'FORECASTS.npz') as expected,np.load(out/'FORECASTS.npz') as actual:
        differences={key:float(np.max(abs(expected[key]-actual[key]))) for key in expected.files}
    assert all(x==0. for x in differences.values()),differences
    before=json.loads((original/'SCORES.json').read_text()); after=json.loads((out/'SCORES.json').read_text())
    assert before['settings']==after['settings']
    result=dict(forecast_maximum_absolute_differences=differences,all_saved_score_settings_exactly_equal=True,
                original_outputs_modified=False,reused_source_only_observation_calibration=True,
                note='Replays fixed forecasts/scores and reference checks; no original study refits or new source acquisition.')
    (out/'REPRODUCTION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
