import datetime as dt
import hashlib
import json
from pathlib import Path
import resource
import time
import numpy as np
from scipy.stats import binom
from screen import midpoint, np_power

def main():
    tick=time.perf_counter()
    d=Path(__file__).resolve().parent
    raw=(d/'SCREEN.json').read_bytes()
    src=json.loads(raw)
    checks={}
    for n in (64,240):
        threshold=int(binom.isf(.05,n,.5))
        frac=(.05-binom.sf(threshold,n,.5))/binom.pmf(threshold,n,.5)
        for effect in (0.,.10,.20):
            p=.5+effect/2
            analytical=float(binom.sf(threshold,n,p)+frac*binom.pmf(threshold,n,p))
            a=src['controls'][f'N{n}_gap{effect}']['no_effect_null']['power']
            assert abs(analytical-a)<1e-12
            checks[f'N{n}_gap{effect}']=dict(analytic_power=analytical,abs_error=abs(analytical-a))
    results={}
    for k,rr in src['results'].items():
        row={}
        for roster,rec in rr.items():
            p={}
            for pair in rec['pairs']:
                a,b=pair.split(':')
                aa,bb=(np.asarray(rec[m]['terminal_accuracy']) for m in (a,b))
                assert rec[a]['terminal_omit']==rec[b]['terminal_omit']
                x,y,_=midpoint(aa,bb,np.array([[rec[a]['terminal_omit']]]))
                tests=[dict(probe=stim,a_null=np_power(x[:,i],y[:,i],240)['power'],
                           b_null=np_power(y[:,i],x[:,i],240)['power']) for i,stim in enumerate(src['probe'])]
                p[pair]=dict(tests=tests,best_two_direction_min=max(min(t['a_null'],t['b_null']) for t in tests),
                           most_favorable_direction=max(max(t['a_null'],t['b_null']) for t in tests))
            row[roster]=p
        results[k]=row
    out=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),input_sha256=hashlib.sha256(raw).hexdigest(),
             results=results,known_effect_crosscheck=checks,bytes_read=len(raw),
             seconds=time.perf_counter()-tick,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (d/'SIGNED_CHECK.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
if __name__=='__main__':main()
