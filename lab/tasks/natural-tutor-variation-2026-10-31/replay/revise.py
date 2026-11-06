"""One predeclared constrained-tempo revision, with separate untouched evaluation."""
import argparse,datetime,hashlib,json,resource
import numpy as np
from evaluate import ROOT,METHODS,FACTORS,LOCATIONS,TOL,weights,quantile,fit,score,shuffle,load,check_pins
ALL=METHODS+['bounded_tempo']

def bounds(model):
    u=(model['x']-model['mean']).mean(axis=1)
    return float(u.min()),float(u.max())

def bounded(model,x):
    d=x-model['mean'];u=d.mean(axis=1);lo,hi=bounds(model)
    r=d-u[:,None];extra=np.maximum(np.maximum(lo-u,u-hi),0)
    return np.sqrt(np.mean(r*r,axis=1)+extra*extra)

def scores(model,shuf,x,m):
    return bounded(model,x) if m=='bounded_tempo' else score(shuf if m=='shuffled_covariance' else model,x,m)

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['freeze','evaluate']);a=p.parse_args()
    if a.mode=='freeze':
        assert not (ROOT/'REVISION_FREEZE.json').exists()
        f=json.loads((ROOT/'FREEZE.json').read_text());charge=check_pins(f)
        pins=[]
        for name in ['REVISION.md','revise.py','FREEZE.json']:
            b=(ROOT/name).read_bytes();charge+=len(b);pins.append({'path':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
        obj={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pins':pins,
             'final10_before_decode':True,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        (ROOT/'REVISION_FREEZE.json').write_text(json.dumps(obj,indent=2)+'\n')
        ledger=json.loads((ROOT/'ACQUISITION.json').read_text());ledger['scientific_read_decoded_hash_bytes']+=charge
        ledger['scientific_byte_passes'].append({'operation':'revision freeze','kind':'hash pins','bytes':charge})
        (ROOT/'ACQUISITION.json').write_text(json.dumps(ledger,indent=2)+'\n')
        print(json.dumps(obj));return
    assert not (ROOT/'REVISION_SUMMARY.json').exists()
    f=json.loads((ROOT/'FREEZE.json').read_text());rf=json.loads((ROOT/'REVISION_FREEZE.json').read_text())
    charge=check_pins(f)+check_pins(rf)
    tx,tg,tk,tinfo,b=load(f['teaching'],f['motif']);charge+=b
    ex,eg,ek,einfo,b=load(f['revision_evaluation'],f['motif']);charge+=b
    sx=shuffle(tx,tk);model=fit(tx,tg);sf=fit(sx,tg)
    cal={m:np.zeros(len(tx)) for m in ALL}
    for g in np.unique(tg):
        h=tg==g;mm=fit(tx[~h],tg[~h]);ss=fit(sx[~h],tg[~h])
        for m in ALL:cal[m][h]=scores(mm,ss,tx[h],m)
    threshold={m:quantile(cal[m],weights(tg),.95) for m in ALL}
    original=np.array([scores(model,sf,ex,m) for m in ALL]);changed=[];challenges=[]
    for loc,idx in LOCATIONS.items():
        for factor in FACTORS:
            z=ex.copy();z[:,idx]+=np.log(factor);changed.append(z)
            challenges.append({'location':loc,'indices':idx,'factor':factor})
    edits=np.array([[scores(model,sf,z,m) for z in changed] for m in ALL]);ew=weights(eg)
    result={}
    for j,m in enumerate(ALL):
        accept=original[j]<=threshold[m]+TOL;rows=[]
        for k,c in enumerate(challenges):
            diff=edits[j,k]-original[j]
            rows.append(dict(c,rejection=float(np.dot(ew,edits[j,k]>threshold[m]+TOL)),
                strict_increase=float(np.dot(ew,diff>TOL)),ties=float(np.dot(ew,np.abs(diff)<=TOL)),
                decrease=float(np.dot(ew,diff < -TOL)),renditions_increase=int(np.sum(diff>TOL)),renditions_total=len(ex)))
        primary=[r for r in rows if r['factor'] in [.8,1.2]]
        result[m]={'threshold':threshold[m],'natural_acceptance':float(np.dot(ew,accept)),
           'natural_acceptance_pooled':float(accept.mean()),
           'primary_pass':bool(np.dot(ew,accept)>=.9-1e-12 and all(r['rejection']>=.8-1e-12 and r['strict_increase']>=.8-1e-12 for r in primary)),
           'challenges':rows,'per_recording_natural_acceptance':{g:float(accept[eg==g].mean()) for g in np.unique(eg)}}
    lo,hi=bounds(model)
    checks={'bounded_equals_free_on_teaching_max':float(np.max(np.abs(bounded(model,tx)-score(model,tx,'free_tempo')))),
      'lo_hi_log_tempo':[lo,hi],'lo_hi_tempo_factors':[float(np.exp(lo)),float(np.exp(hi))],
      'finite':bool(np.isfinite(original).all() and np.isfinite(edits).all())}
    assert checks['bounded_equals_free_on_teaching_max']<1e-12 and checks['finite']
    report={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'phase':'independently reserved final10; same bird/day','teaching_renditions':len(tx),
       'evaluation_renditions':len(ex),'allocation':{'training_recordings':tinfo,'evaluation_recordings':einfo},
       'methods':result,'checks':checks,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'scientific_read_decoded_hash_bytes_this_pass':charge}
    np.savez_compressed(ROOT/'REVISION_SCORES.npz',methods=np.array(ALL),original=original,edits=edits,
       eval_x=ex,eval_groups=eg,eval_keys=np.array(ek),train_x=tx,train_groups=tg,train_keys=np.array(tk),
       challenge_locations=np.array([c['location'] for c in challenges]),challenge_factors=np.array([c['factor'] for c in challenges]))
    (ROOT/'REVISION_SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n')
    ledger=json.loads((ROOT/'ACQUISITION.json').read_text());ledger['scientific_read_decoded_hash_bytes']+=charge
    ledger['scientific_byte_passes'].append({'operation':'revision final10','kind':'pins+CSV read/decode+numeric arrays','bytes':charge})
    ledger['peak_rss_bytes_measured_max']=max(ledger['peak_rss_bytes_measured_max'],report['peak_rss_bytes'])
    (ROOT/'ACQUISITION.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print(json.dumps({'evaluation_renditions':len(ex),'checks':checks,'methods':{m:{
      'natural_acceptance':v['natural_acceptance'],'primary_pass':v['primary_pass'],
      '20pct_challenges':[{k:r[k] for k in ['location','factor','rejection','strict_increase','ties']} for r in v['challenges'] if r['factor'] in [.8,1.2]]} for m,v in result.items()}},indent=2))
if __name__=='__main__':main()
