"""Independent fixed-prediction scoring; no author functions or optimization."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
from pathlib import Path
import csv, json, resource, datetime
import numpy as np

HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parents[1] / 'tasks' / HERE.name

def main():
    paths = [AUTHOR/'ALLOWED_MANIFEST.json', AUTHOR/'corrected/scoring_rows.csv',
             AUTHOR/'corrected/predictions.npz', AUTHOR/'corrected/unit_scores_B.csv',
             AUTHOR/'corrected/unit_scores_S.csv', AUTHOR/'corrected/SUMMARY.json']
    manifest = json.loads(paths[0].read_text())
    with paths[1].open() as f:
        rows = list(csv.DictReader(f))
    unit = np.array([int(r['unit']) for r in rows])
    choice = np.array([float(r['choice']) for r in rows])
    responded = choice != 0
    contrast = np.array([float(r['contrast']) for r in rows])
    support = np.array([r['common_support'] == 'True' for r in rows])
    species = np.array([r['species'] for r in rows])
    y = (choice == 1).astype(float)
    masks = dict(support=responded & support, all_common_contrast=responded,
                 zero=responded & (contrast==0), high=responded & (abs(contrast)>=.5))
    unit_meta = {int(r['unit']): {k:r[k] for k in ('subject','species','lab','schedule','condition','fold')} for r in rows}
    del rows
    with np.load(paths[2], allow_pickle=False) as z:
        assert np.array_equal(y, z['y'])
        pred = {k:z[k] for k in z.files if k!='y'}
    decoded_bytes = sum(v.nbytes for v in pred.values()) + y.nbytes
    recomputed=[]; maxerr=0.; summary=[]
    for baseline, saved_path in zip(('B','S'), paths[3:5]):
        with saved_path.open() as f:
            saved = {(r['scope'],int(r['unit'])):r for r in csv.DictReader(f)}
        pp={k[len(baseline)+1:]:np.clip(v,1e-9,1-1e-9) for k,v in pred.items() if k.startswith(baseline+'_')}
        losses={}
        for k,v in pp.items():
            loss=np.full(len(y),np.nan)
            logits=np.log(v[responded])-np.log1p(-v[responded])
            loss[responded]=np.logaddexp(0,logits)-y[responded]*logits
            losses[k]=loss
        for scope,m in masks.items():
            byunit={}
            for u in np.unique(unit[m]):
                ids=np.flatnonzero(m & (unit==u)); ref=saved[(scope,int(u))]
                assert int(ref['n'])==len(ids)
                r=dict(unit=int(u),scope=scope,n=len(ids),baseline=baseline,**unit_meta[int(u)])
                for model in pp:
                    loss=float(losses[model][ids].mean()); brier=float(((pp[model][ids]-y[ids])**2).mean())
                    maxerr=max(maxerr,abs(loss-float(ref[model+'_loss'])),abs(brier-float(ref[model+'_brier'])))
                    r[model+'_loss']=loss; r[model+'_brier']=brier
                recomputed.append(r); byunit[int(u)]=r
            for sp in ('human','mouse'):
                rr=[r for r in byunit.values() if r['species']==sp]
                for a,b in [('H','B'),('T','H'),('T','B'),('human_fixed','B'),('mouse_fixed','B'),('T','human_fixed'),('T','mouse_fixed')]:
                    summary.append(dict(baseline=baseline,scope=scope,species=sp,comparison=a+'-minus-'+b,
                        units=len(rr),rows=sum(r['n'] for r in rr),gain_nat=float(np.mean([r[b+'_loss']-r[a+'_loss'] for r in rr]))))
    author_summary=json.loads(paths[5].read_text())
    summary_err=max(abs(a['gain_nat']-next(r['gain_nat'] for r in summary if all(r[k]==a[k] for k in ('baseline','scope','species','comparison')))) for a in author_summary)
    out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='independent score calculation completed',
        scoring_rows=len(unit),responding_rows=int(responded.sum()),primary={s:dict(rows=int(np.sum(masks['support'] & (species==s))),units=int(len(np.unique(unit[masks['support'] & (species==s)])))) for s in ('human','mouse')},
        per_unit_loss_brier_max_abs_error=maxerr,all_summary_gain_max_abs_error=summary_err,
        primary_scores=[r for r in summary if r['scope']=='support'],
        manifest_top_keys=list(manifest),manifest_first_entries={k:(v[:1] if isinstance(v,list) else list(v)[:8] if isinstance(v,dict) else v) for k,v in manifest.items()},
        resource=dict(read_file_bytes=sum(p.stat().st_size for p in paths),decoded_prediction_bytes=decoded_bytes,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        limitations='Saved probabilities independently scored; coefficient/features/source/optimizer/intervals not yet reconstructed. All data consumed development.')
    (HERE/'FIRST_CALCULATION.json').write_text(json.dumps(out,indent=2)+'\n')
    (HERE/'independent_unit_scores.json').write_text(json.dumps(recomputed)+'\n')
    print(json.dumps({k:out[k] for k in ('status','scoring_rows','responding_rows','primary','per_unit_loss_brier_max_abs_error','all_summary_gain_max_abs_error','resource','manifest_top_keys','manifest_first_entries')},indent=2))
    print(json.dumps([r for r in summary if r['scope']=='support' and r['comparison'] in ('human_fixed-minus-B','H-minus-B')],indent=2))

if __name__=='__main__': main()
