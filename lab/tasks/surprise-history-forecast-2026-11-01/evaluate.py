from data import ROOT,load_people,wrap
from model import assemble,design,predict,circular_loss,person_means
import datetime,hashlib,json,resource,sys
import numpy as np

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def gains(keys,y,b,h,seed=20261101,reps=10000):
    ids=keys[:,0];lb=circular_loss(y,b);lh=circular_loss(y,h)
    pb=person_means(lb,ids);ph=person_means(lh,ids)
    gain=float((pb.mean()-ph.mean())/pb.mean())
    rng=np.random.default_rng(seed);ix=rng.integers(0,len(pb),(reps,len(pb)))
    boot=(pb[ix].mean(axis=1)-ph[ix].mean(axis=1))/pb[ix].mean(axis=1)
    ci=np.quantile(boot,[.025,.975]).tolist()
    contexts={}
    for c in [0,1]:
        sel=keys[:,1]==c
        bb=person_means(lb[sel],ids[sel]).mean();hh=person_means(lh[sel],ids[sel]).mean()
        contexts[str(c)]=dict(loss_B=float(bb),loss_H=float(hh),gain=float((bb-hh)/bb))
    return dict(gain=gain,bootstrap95=ci,contexts=contexts,people_improved=int(np.sum(ph<pb)),person_loss_B=pb.tolist(),person_loss_H=ph.tolist(),passes=bool(gain>=.05 and ci[0]>0 and all(v['gain']>0 for v in contexts.values())))

if __name__=='__main__':
    if sys.argv[1]=='predict':
        assert not (ROOT/'predictions.npz').exists()
        freeze=json.loads((ROOT/'FREEZE.json').read_text())
        for name,digest in freeze['pins'].items():assert sha(ROOT/name)==digest,name
        people,audits,read=load_people('evaluation')
        (ROOT/'EVALUATION_SOURCE_CHECK.json').write_text(json.dumps(dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),audits=audits,compressed_plus_decoded_bytes=read),indent=2))
        assert all(v['chronology_pred_inside']==240 and v['chronology_next_after']==239 for v in audits)
        d=assemble(people)
        np.savez(ROOT/'evaluation_features.npz',**{k:v for k,v in d.items() if k!='filterchecks'})
        hats={'P':np.zeros(len(d['y'])),'N':d['diagnostics'][:,3]}
        for which in ['B','H']:
            m=dict(np.load(ROOT/('fitted_'+which+'.npz')))
            hats[which]=predict(m,design(d,which))
        np.savez(ROOT/'predictions.npz',keys=d['keys'],**hats)
        np.savez(ROOT/'evaluation_truth.npz',keys=d['keys'],y=d['y'])
        out=dict(saved_before_scoring_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),people=len(np.unique(d['keys'][:,0])),rows=len(d['y']),prediction_sha256=sha(ROOT/'predictions.npz'),truth_sha256=sha(ROOT/'evaluation_truth.npz'),feature_sha256=sha(ROOT/'evaluation_features.npz'),filterchecks=d['filterchecks'],peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,score_UNRUN=True)
        (ROOT/'PREDICTION_MANIFEST.json').write_text(json.dumps(out,indent=2))
        print(json.dumps({k:v for k,v in out.items() if k!='filterchecks'},indent=2))
    elif sys.argv[1]=='score':
        assert not (ROOT/'SCORES.json').exists()
        pins=json.loads((ROOT/'PREDICTION_MANIFEST.json').read_text())
        assert sha(ROOT/'predictions.npz')==pins['prediction_sha256']
        assert sha(ROOT/'evaluation_truth.npz')==pins['truth_sha256']
        f=dict(np.load(ROOT/'predictions.npz'));t=dict(np.load(ROOT/'evaluation_truth.npz'))
        assert np.array_equal(f['keys'],t['keys'])
        keys=t['keys'];y=t['y'];ids=keys[:,0]
        out=dict(scored_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),prediction_manifest_sha256=sha(ROOT/'PREDICTION_MANIFEST.json'),criterion='H over B gain>=.05 AND bootstrap lower>0 AND positive point gain both contexts',primary=gains(keys,y,f['B'],f['H']),models={})
        for name in ['P','N','B','H']:
            e=wrap(y-f[name]);loss=person_means(circular_loss(y,f[name]),ids)
            out['models'][name]=dict(mean_person_circular_loss=float(loss.mean()),angular_rmse_degrees=float(np.rad2deg(np.sqrt(np.mean(e*e)))),angular_mae_degrees=float(np.rad2deg(np.mean(abs(e)))),person_losses=loss.tolist())
        out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (ROOT/'SCORES.json').write_text(json.dumps(out,indent=2))
        print(json.dumps(out,indent=2))
