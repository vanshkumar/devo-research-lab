"""Stable physical-session blocks joined to predeclared date/number order."""
import numpy as np
def join_aggregate(values,identities,sessions):
    rows=[]
    for z in sessions:
        lo=z['aggregate_row_start'];hi=z['aggregate_row_stop']
        assert hi-lo==z['rows'] and np.all(identities[lo:hi]==z['eid'])
        v=np.empty((hi-lo,7));v[:,:6]=values[lo:hi,:6];v[:,6]=0;v[0,6]=1;rows.append(v)
    out=np.concatenate(rows)
    assert len(out)==sessions[-1]['stop'] and len(out)>=3000
    return out[:3000].copy()
