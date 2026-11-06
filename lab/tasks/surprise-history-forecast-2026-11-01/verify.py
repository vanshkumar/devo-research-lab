"""Offline author audit. Separate independent scientific review remains unrun."""
from data import ROOT
from model import predict,design,wrap
from controls import cache,refit
import datetime,hashlib,io,json,math,resource,zipfile
import numpy as np
from scipy.io import loadmat

freeze=json.loads((ROOT/'FREEZE.json').read_text())
for name,digest in freeze['pins'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
f=dict(np.load(ROOT/'predictions.npz'));t=dict(np.load(ROOT/'evaluation_truth.npz'))
split=json.loads((ROOT/'SPLIT.json').read_text())
rawkeys=[];rawtargets=[];ref=[]
def angle(x):return math.atan2(math.sin(x),math.cos(x))
with zipfile.ZipFile(ROOT/'behavior_zip.source') as z:
    for person in split['participants']:
        if person['split']!='evaluation':continue
        records=loadmat(io.BytesIO(z.read(person['member'])),simplify_cells=True)
        for prefix,c in [('DataCP_',1),('DataOddball_',0)]:
            row=records[next(k for k in records if k.startswith(prefix))]
            pred=[float(v)*math.pi/180 for v in row['pred']]
            out=[float(v)*math.pi/180 for v in row['outcome']]
            pe=[angle(o-p) for o,p in zip(out,pred)]
            ru=.99;oldq=0;oldpe=0;oldru=.99
            for j in range(240):
                if j%60==0:ru=.99
                else:
                    if c:
                        variance=oldq*.1+(1-oldq)*oldru*.1+oldq*(1-oldq)*(oldpe*(1-oldru))**2
                    else:
                        run=(1-oldru)/oldru
                        variance=oldq*.1/run+(1-oldq)*.1/(run+1)+oldq*(1-oldq)*(oldpe*oldru)**2+1/30
                    ru=variance/(variance+.1)
                total=.1/(1-ru)
                same=(6/7)*math.exp(-pe[j]**2/(2*total))/math.sqrt(2*math.pi*total)
                new=(1/7)/(2*math.pi);q=new/(same+new)
                lr=ru+q-ru*q if c else ru*(1-q)
                if j%60<59:
                    rawkeys.append([int(person['id']),c,j//60+1,j+1])
                    rawtargets.append(angle(pred[j+1]-pred[j]));ref.append(lr*pe[j])
                oldq=q;oldpe=pe[j];oldru=ru
assert np.array_equal(rawkeys,f['keys']) and np.array_equal(rawkeys,t['keys'])
truth_error=float(np.max(abs(wrap(np.array(rawtargets)-t['y']))))
reference_error=float(np.max(abs(wrap(np.array(ref)-f['N']))))
assert truth_error<2e-13 and reference_error<2e-13

d=dict(np.load(ROOT/'development_features.npz'));e=dict(np.load(ROOT/'evaluation_features.npz'))
replay={};cached={}
for which in ['B','H']:
    m=dict(np.load(ROOT/('fitted_'+which+'.npz')))
    hat=predict(m,design(e,which))
    err=float(np.max(abs(wrap(hat-f[which]))));assert err<1e-13
    replay[which]=err
    pre=cache(d,e,which)
    ch,lam=refit(pre,d['y'],d['keys'][:,0])
    cerr=float(np.max(abs(wrap(ch-hat))));assert cerr<1e-9 and lam==float(m['lam'])
    cached[which]=dict(chosen_ridge=lam,max_prediction_angle_error=cerr)
scores=json.loads((ROOT/'SCORES.json').read_text());loss_error={}
for name in ['P','N','B','H']:
    loss=np.mean([1-math.cos(y-h) for y,h in zip(rawtargets,f[name])])
    err=abs(loss-scores['models'][name]['mean_person_circular_loss']);assert err<1e-14
    loss_error[name]=err
out=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),author_self_audit_only=True,freeze_pins_verified=len(freeze['pins']),original_mat_target_rows=len(rawtargets),max_original_target_angle_error=truth_error,max_independent_scalar_approximate_model_error=reference_error,frozen_prediction_replay=replay,cached_vs_direct_ridge=cached,loss_reconstruction_error=loss_error,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(ROOT/'VERIFICATION.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
