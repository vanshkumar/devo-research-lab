"""Recorded pre-scoring guard for undefined subgroup estimates.

The original frozen scorer remains byte-identical. NaN cannot satisfy a finite
absolute-bias tolerance. This wrapper makes that existing protocol requirement
explicit; every complete-data statistic and scientific threshold is unchanged.
"""
import json
import numpy as np
import score_campaign as frozen
from campaign import C,digest

original=frozen.gate_summary

def guarded(*args,**kwargs):
    r=original(*args,**kwargs)
    finite=all(np.isfinite(v) for name in ('lab_scalar_bias','leave_one_lab_out_bias') for v in r[name].values())
    r['checks']['subgroup_estimates_finite']=bool(finite)
    r['pass_gate']=all(r['checks'].values())
    return r

if __name__=='__main__':
    frozen.gate_summary=guarded
    result=frozen.score_source()
