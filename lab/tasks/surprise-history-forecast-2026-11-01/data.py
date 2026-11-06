"""Decode selected original participant files; never decode the opposite split."""
import os
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[name]='1'
import datetime, hashlib, io, json, pathlib, resource, zipfile
import numpy as np
from scipy.io import loadmat

ROOT=pathlib.Path(__file__).resolve().parent
def wrap(x):return np.angle(np.exp(1j*np.asarray(x,dtype=float)))
def load_people(split):
    manifest=json.loads((ROOT/'SPLIT.json').read_text())
    people=[]; audits=[]; bytes_read=0
    with zipfile.ZipFile(ROOT/'behavior_zip.source') as z:
        for x in manifest['participants']:
            if x['split']!=split:continue
            raw=z.read(x['member']);bytes_read+=len(raw)+x['compressed']
            d=loadmat(io.BytesIO(raw),simplify_cells=True)
            rr=[]
            for prefix,context in [('DataCP_',1),('DataOddball_',0)]:
                key=next(k for k in d if k.startswith(prefix));r=d[key]
                # Complete original file is consumed, including auxiliary fields.
                r={k:np.asarray(v) for k,v in r.items()}
                n=len(r['pred'])
                assert n==240 and np.array_equal(r['trial'],np.arange(1,n+1))
                assert np.array_equal(r['block'],np.repeat(np.arange(1,5),60))
                assert set(str(int(v)) for v in r['ID'])=={x['id']}
                assert set(r['cond'])==({'main'} if context else {'oddball'})
                for k in ['pred','outcome','hit','timestampOnset','timestampPrediction','timestampOffset']:
                    assert np.all(np.isfinite(r[k]))
                assert np.all((r['outcome']>=0)&(r['outcome']<=360))
                before=(r['timestampOnset']<=r['timestampPrediction'])&(r['timestampPrediction']<r['timestampOffset'])
                after=r['timestampOffset'][:-1]<r['timestampOnset'][1:]
                sigma=np.unique(r['sigma']);drift=np.unique(r['driftConc'])
                assert np.array_equal(sigma,[10]) and np.array_equal(drift,[30])
                rr.append(dict(id=x['id'],context=context,raw=r,pred=np.deg2rad(np.asarray(r['pred'],dtype=np.float64)),outcome=np.deg2rad(np.asarray(r['outcome'],dtype=np.float64)),block=r['block']))
                flags=r['cp'] if context else r['oddBall']
                events=np.flatnonzero(flags==1)
                gaps=np.diff(events)
                audits.append(dict(id=x['id'],context=context,rows=n,prediction_range_degrees=[float(r['pred'].min()),float(r['pred'].max())],finite_prediction_outcome=n,chronology_pred_inside=int(before.sum()),chronology_next_after=int(after.sum()),cBal=np.unique(r['cBal']).tolist(),events=int(len(events)),minimum_event_gap=int(gaps.min()) if len(gaps) else None,post_event_within3=int(np.sum(gaps<4)),zip_member_sha256=hashlib.sha256(raw).hexdigest(),all_auxiliary_consumed=True))
            people.extend(rr)
    return people,audits,bytes_read

if __name__=='__main__':
    people,audits,b=load_people('development')
    out=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),people=20,rows=sum(len(x['pred']) for x in people),audits=audits,decoded_plus_compressed_bytes=b,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (ROOT/'DEVELOPMENT_SOURCE_CHECK.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
