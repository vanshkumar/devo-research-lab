"""Consumed-source masks/medians/detrending controls; Figure4 stays closed."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
import csv,json,resource
from collections import defaultdict
from datetime import datetime,timezone
import numpy as np
from threadpoolctl import threadpool_limits
from source_analysis import HERE,SOURCE,num

def intv(a):return [float(x) for x in np.quantile(a,[.025,.975])]

def summarize(v,rng):
    a=np.asarray(v)
    b=a[rng.integers(len(a),size=(6000,len(a)))].mean(axis=1)
    return dict(n_people=len(a),mean_no_jump=float(a[:,0].mean()),mean_jump_to=float(a[:,1].mean()),
                ratio=float(a[:,1].mean()/a[:,0].mean()),ratio95=intv(b[:,1]/b[:,0]),
                suppression_degrees=float((a[:,0]-a[:,1]).mean()),suppression95=intv(b[:,0]-b[:,1]),
                per_person=a.tolist())

def main():
    rng=np.random.default_rng(2712026);out=dict(created_utc=datetime.now(timezone.utc).isoformat(),sources=[],
             scope='Consumed TsayA20 and Figure3_18 only; measurement sensitivity, not new validation',
             charged_read_decoded_hash_bytes=0)
    for name in ('tsay_TE_SPE.csv','task_success_fig3.csv'):
        p=SOURCE/name;by=defaultdict(list);out['charged_read_decoded_hash_bytes']+=8*p.stat().st_size
        tsay=name.startswith('tsay')
        with p.open(newline='') as f:
            for full in csv.DictReader(f):
                # Only permitted scientific columns; no other files are opened.
                if tsay:
                    person=int(full['SN']);t=int(full['TN'])
                    row=dict(t=t,c=num(full['clamp_size']),j=num(full['tgt_jump_size']),
                             raw=num(full['Hand_raw']),masked=num(full['Hand']),dt=num(full['Hand_dt']),
                             diff=num(full['Hand_Diff']),bad=False)
                else:
                    person=int(full['Subject']);t=int(full['TrialNum'])
                    row=dict(t=t,c=num(full['ClampAngle']),j=num(full['TargetJump']),raw=num(full['HandError']),
                             bad=num(full['FalseStart'])==1)
                if t> (100 if tsay else 103):by[person].append(row)
        methods=(('raw_mean','raw','mean'),('raw_median','raw','median'),('masked_mean','masked','mean'),
                 ('dt_mean','dt','mean'),('dt_median','dt','median'),('supplied_diff_median','diff','median')) if tsay else (
                  ('raw_mean','raw','mean'),('raw_median','raw','median'),
                  ('literal_author_mask_median','literal','median'),('centered_author_mask_median','centered','median'))
        allvals={m:[] for m,_,_ in methods};max_diff_resid=0.
        for person,rr in sorted(by.items()):
            rr.sort(key=lambda r:r['t'])
            if not tsay:
                y=np.asarray([r['raw'] for r in rr]);n=len(y)
                # Literal R `i-2:i+2` is descending i,...,2 in one-based coordinates.
                literal=np.r_[y[0],np.nanmean(y[:3]),[np.nanmean(y[1:i+1]) for i in range(2,n-2)],np.nanmean(y[-3:]),y[-1]]
                centered=np.r_[y[0],np.nanmean(y[:3]),[np.nanmean(y[i-2:i+3]) for i in range(2,n-2)],np.nanmean(y[-3:]),y[-1]]
                assert len(literal)==n and len(centered)==n
                for lab,sm in [('literal',literal),('centered',centered)]:
                    res=y-sm;sd=np.nanstd(res,ddof=1)
                    for i,r in enumerate(rr):r[lab]=float(y[i]) if abs(res[i])<=3*sd and abs(y[i])<=90 and not r['bad'] else float('nan')
            for label,field,aggregator in methods:
                cells=defaultdict(list)
                for a,b in zip(rr,rr[1:]):
                    if b['t']!=a['t']+1:continue
                    if tsay and (a['t']-101)%181>=179:continue
                    if not tsay and a['t']>903:continue
                    if abs(a['c'])!=4 or (a['j']!=0 and a['j']!=a['c']):continue
                    if field=='diff':
                        yy=a['diff']
                        if np.isfinite([a['dt'],b['dt'],yy]).all():max_diff_resid=max(max_diff_resid,abs(yy-(b['dt']-a['dt'])))
                    else:
                        yy=b[field]-a[field]
                        if abs(a[field])>90 or abs(b[field])>90:continue
                        if field=='raw' and (a['bad'] or b['bad']):continue
                    if not np.isfinite(yy):continue
                    cells[(int(np.sign(a['c'])),a['j']!=0)].append(-np.sign(a['c'])*yy)
                vec=[]
                for jump in (False,True):
                    means=[getattr(np,aggregator)(cells[(sgn,jump)]) for sgn in (-1,1)]
                    vec.append(float(np.mean(means)))
                allvals[label].append(vec)
        out['sources'].append(dict(source=name,methods={m:summarize(v,rng) for m,v in allvals.items()},
                                   within_person_supplied_diff_max_residual=max_diff_resid if tsay else None))
    # Matched source ratio shift under transparent and literal-publication controls.
    pairs=[('raw_mean','raw_mean'),('raw_median','raw_median'),('dt_median','literal_author_mask_median'),
           ('supplied_diff_median','literal_author_mask_median'),('masked_mean','centered_author_mask_median')]
    comparisons=[]
    for ma,mf in pairs:
        aa=out['sources'][0]['methods'][ma];ff=out['sources'][1]['methods'][mf]
        a=np.asarray(aa['per_person']);f=np.asarray(ff['per_person'])
        ab=a[rng.integers(len(a),size=(6000,len(a)))].mean(axis=1)
        fb=f[rng.integers(len(f),size=(6000,len(f)))].mean(axis=1)
        shifts=fb[:,1]/fb[:,0]-ab[:,1]/ab[:,0]
        comparisons.append(dict(Tsay_method=ma,Figure3_method=mf,Tsay_ratio=aa['ratio'],Figure3_ratio=ff['ratio'],
                                ratio_shift=ff['ratio']-aa['ratio'],ratio_shift95=intv(shifts)))
    out['comparisons']=comparisons;out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (HERE/'MEASUREMENT_SENSITIVITY.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(created_utc=out['created_utc'],comparisons=comparisons,
       difference_column_residual=out['sources'][0]['within_person_supplied_diff_max_residual'],
       charge=out['charged_read_decoded_hash_bytes'],peak_rss_bytes=out['peak_rss_bytes']),indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=1):main()
