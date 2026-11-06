import datetime, hashlib, io, json, pathlib, resource, zipfile
import numpy as np
from scipy.io import loadmat

p=pathlib.Path(__file__).resolve().parent
b=(p/'behavior_zip.source').read_bytes()
assert hashlib.md5(b).hexdigest()=='235fad11706c1b93c7a12b55fcde5757'
member='cannonBehavData_forDryad/ADL_B_000342.mat'
with zipfile.ZipFile(io.BytesIO(b)) as z:
    raw=z.read(member)
    d=loadmat(io.BytesIO(raw),simplify_cells=True)
def wrap(x): return (np.asarray(x,dtype=float)+180)%360-180
out=dict(calculated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
         source='Dryad 10.5061/dryad.570pf8n; identical CC0 Zenodo 5034463 mirror',
         zip_bytes=len(b),zip_sha256=hashlib.sha256(b).hexdigest(),zip_md5=hashlib.md5(b).hexdigest(),
         member=member,member_sha256=hashlib.sha256(raw).hexdigest(),participant='342',independent_units=1,
         timing='Per source article and pinned analysis: pred[t] before outcome[t], next prediction[t+1] after outcome and shield feedback. Circular angles in degrees. No across-block update.',
         groups={})
for prefix,context in [('DataCP_','changepoint'),('DataOddball_','oddball')]:
    key=next(k for k in d if k.startswith(prefix)); r=d[key]
    pred=np.asarray(r['pred'],float); outcome=np.asarray(r['outcome'],float); block=np.asarray(r['block'])
    pe=wrap(outcome[:-1]-pred[:-1]); up=wrap(pred[1:]-pred[:-1])
    valid=(block[1:]==block[:-1])&np.isfinite(pe)&np.isfinite(up)
    ix=np.flatnonzero(valid)
    out['groups'][context]=dict(rows=len(pred),valid_within_block_updates=int(valid.sum()),
        blocks=np.unique(block).tolist(),sigma_concentration=np.unique(r['sigma']).tolist(),
        drift_concentration=np.unique(r['driftConc']).tolist(),exported_hazard_fields={'vola':np.unique(r['vola']).tolist(),'oddballProb':np.unique(r['oddballProb']).tolist()},
        rms_update_degrees=float(np.sqrt(np.mean(up[valid]**2))),
        current_error_slope=float(np.sum(pe[valid]*up[valid])/np.sum(pe[valid]**2)),
        signed_error_update_crossproduct=float(np.sum(pe[valid]*up[valid])),
        example_rows=[dict(trial=int(r['trial'][i]),block=int(block[i]),prediction=float(pred[i]),outcome=float(outcome[i]),next_prediction=float(pred[i+1]),error=float(pe[i]),update=float(up[i])) for i in ix[:5]],
        finite_predictions=int(np.isfinite(pred).sum()),finite_outcomes=int(np.isfinite(outcome).sum()))
out['exposure']='Both complete 240-row contexts and all auxiliary fields of participant342 decoded/consumed. Other participant MAT members acquired as ZIP bytes but not decompressed or numerically interpreted. Published all39 summaries exposed.'
out['resources']=dict(public_operations_so_far=21,known_ingress_body_bytes=sum(x.get('bytes',x.get('bytes_received',0)) for x in json.loads((p/'ACQUISITIONS.json').read_text())),conservative_ingress_charge=8_000_000,additional_scientific_read_charge=25_000_000,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,unknown='Provider HTTP fanout/wirebytes/toolhost RSS and actual physical I/O unknown; charges are allowances, not measurements.')
(p/'FIRST_DATA_CHECK.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
