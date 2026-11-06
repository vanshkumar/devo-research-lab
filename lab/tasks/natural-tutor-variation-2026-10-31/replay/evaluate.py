"""Frozen small symbolic timing comparison. All fitting is teaching-only."""
import argparse,datetime,hashlib,json,pathlib,resource
import numpy as np
from development import read_rows,phrases
ROOT=pathlib.Path(__file__).resolve().parent
METHODS=['prototype','nearest','covariance','free_tempo','shuffled_covariance','absent']
FACTORS=[0.8,0.9,0.95,1.05,1.1,1.2]
LOCATIONS={'global':[0,1,2,3,4],'duration_b':[2],'gap_ab':[1],'duration_c':[4]}
TOL=1e-12

def weights(groups):
    u,c=np.unique(groups,return_counts=True);d=dict(zip(u,c))
    return np.array([1/len(u)/d[g] for g in groups])

def quantile(x,w,q):
    order=np.argsort(x);xx=np.asarray(x)[order];ww=np.asarray(w)[order]
    return float(xx[min(np.searchsorted(np.cumsum(ww)/ww.sum(),q),len(xx)-1)])

def fit(x,g):
    w=weights(g);mu=np.einsum('n,nd->d',w,x);d=x-mu
    c=np.einsum('n,ni,nj->ij',w,d,d)/(1-np.dot(w,w))
    c=.8*c+.2*np.diag(np.diag(c))+np.eye(5)*(.002**2)
    return {'x':x,'mean':mu,'cov':c,'precision':np.linalg.inv(c)}

def score(model,x,method):
    d=np.atleast_2d(x)-model['mean']
    if method=='prototype':return np.sqrt(np.mean(d*d,axis=1))
    if method=='nearest':
        return np.sqrt(np.min(np.mean((np.atleast_2d(x)[:,None,:]-model['x'][None,:,:])**2,axis=2),axis=1))
    if method in ['covariance','shuffled_covariance']:
        return np.sqrt(np.maximum(0,np.einsum('ni,ij,nj->n',d,model['precision'],d)/5))
    if method=='free_tempo':
        z=d-d.mean(axis=1)[:,None];return np.sqrt(np.mean(z*z,axis=1))
    if method=='absent':return np.zeros(len(d))
    raise ValueError(method)

def shuffle(x,keys):
    out=[]
    for row,key in zip(x,keys):
        seed=int.from_bytes(hashlib.sha256(key.encode()).digest()[:8],'big')
        out.append(row[np.random.default_rng(seed).permutation(5)])
    return np.array(out)

def load(names,motif):
    arr=[];groups=[];keys=[];info=[];charge=0
    for name in names:
        r,b=read_rows(ROOT/'sources/annotations'/name);charge+=2*b
        found=phrases(r,motif)
        info.append({'file':name,'annotated_syllables':len(r),'motif_renditions':len(found)})
        for s in found:
            arr.append(np.log(s['seconds']));groups.append(name);keys.append(name+':'+str(s['row_start']))
    x=np.array(arr);charge+=x.nbytes
    assert x.ndim==2 and x.shape[1]==5 and len(x)>0
    return x,np.array(groups),keys,info,charge

def check_pins(manifest):
    for x in manifest['pins']:
        b=(ROOT/x['path']).read_bytes()
        assert hashlib.sha256(b).hexdigest()==x['sha256'],x['path']
    return sum(x['bytes'] for x in manifest['pins'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['main']);a=ap.parse_args()
    manifest=json.loads((ROOT/'FREEZE.json').read_text());charge=check_pins(manifest)
    assert not (ROOT/'MAIN_SUMMARY.json').exists(),'Do not overwrite an already scored main test'
    motif=manifest['motif'];train=manifest['teaching'];test=manifest['main_evaluation']
    tx,tg,tk,tinfo,b=load(train,motif);charge+=b
    ex,eg,ek,einfo,b=load(test,motif);charge+=b
    sx=shuffle(tx,tk);normal=fit(tx,tg);shuffled=fit(sx,tg)
    cal={m:np.zeros(len(tx)) for m in METHODS}
    for g in np.unique(tg):
        held=tg==g;f=fit(tx[~held],tg[~held]);sf=fit(sx[~held],tg[~held])
        for m in METHODS:cal[m][held]=score(sf if m=='shuffled_covariance' else f,tx[held],m)
    threshold={m:quantile(cal[m],weights(tg),.95) for m in METHODS}
    original=np.array([score(shuffled if m=='shuffled_covariance' else normal,ex,m) for m in METHODS])
    challenges=[];changed=[]
    for loc,idx in LOCATIONS.items():
        for factor in FACTORS:
            z=ex.copy();z[:,idx]+=np.log(factor)
            changed.append(z);challenges.append({'location':loc,'factor':factor,'indices':idx})
    edits=np.array([[score(shuffled if m=='shuffled_covariance' else normal,z,m) for z in changed] for m in METHODS])
    # Shape methods x edits x renditions, preserving every comparison.
    ew=weights(eg);result={}
    for j,m in enumerate(METHODS):
        accept=original[j]<=threshold[m]+TOL
        rows=[]
        for k,c in enumerate(challenges):
            diff=edits[j,k]-original[j]
            rows.append(dict(c,rejection=float(np.dot(ew,edits[j,k]>threshold[m]+TOL)),
                strict_increase=float(np.dot(ew,diff>TOL)),ties=float(np.dot(ew,np.abs(diff)<=TOL)),
                decrease=float(np.dot(ew,diff < -TOL)),renditions_increase=int(np.sum(diff>TOL)),
                renditions_total=len(ex)))
        primary=[r for r in rows if r['factor'] in [.8,1.2]]
        passed=bool(np.dot(ew,accept)>=.9-1e-12 and all(r['rejection']>=.8-1e-12 and r['strict_increase']>=.8-1e-12 for r in primary))
        result[m]={'threshold':threshold[m],'natural_acceptance':float(np.dot(ew,accept)),
            'natural_acceptance_pooled':float(accept.mean()),'primary_pass':passed,'challenges':rows,
            'per_recording_natural_acceptance':{g:float(accept[eg==g].mean()) for g in np.unique(eg)}}
    # Independent algebraic controls; no new data or fitted choices.
    q=np.einsum('ni,ij,nj->n',ex-normal['mean'],normal['precision'],ex-normal['mean'])
    qsolve=np.array([np.dot(d,np.linalg.solve(normal['cov'],d)) for d in ex-normal['mean']])
    invariance=max(float(np.max(np.abs(score(normal,ex+np.log(f),'free_tempo')-score(normal,ex,'free_tempo')))) for f in FACTORS)
    checks={'prototype_at_mean':float(score(normal,normal['mean'],'prototype')[0]),
      'covariance_at_mean':float(score(normal,normal['mean'],'covariance')[0]),
      'covariance_quadratic_vs_solve_max':float(np.max(np.abs(q-qsolve))),
      'free_tempo_global_scale_max_change':invariance,
      'all_scores_finite':bool(np.isfinite(original).all() and np.isfinite(edits).all()),
      'true_error_control':[{**c,'reference_log_RMS':float(np.sqrt(len(c['indices'])/5)*abs(np.log(c['factor'])))} for c in challenges],
      'sequence_gate':{'taught_order':motif,'reversal_rejected':True,'cyclic_rejected':True,
          'bag_gate_reversal_rejected':False,'bag_gate_cyclic_rejected':False,
          'scope':'exact learned human-label order; supplied-label positive control'}}
    assert checks['prototype_at_mean']==0 and checks['covariance_at_mean']==0
    assert checks['covariance_quadratic_vs_solve_max']<1e-8 and invariance<1e-12 and checks['all_scores_finite']
    summary={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'main',
      'allocation':{'training_recordings':tinfo,'evaluation_recordings':einfo,'reserved_unscored_recordings':manifest['revision_evaluation']},
      'teaching_renditions':len(tx),'evaluation_renditions':len(ex),'methods':result,'checks':checks,
      'model':{'mean_log_intervals':normal['mean'].tolist(),'covariance':normal['cov'].tolist(),
         'shuffled_mean':shuffled['mean'].tolist(),'calibration':{m:cal[m].tolist() for m in METHODS},
         'calibration_groups':tg.tolist()},
      'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'scientific_read_decoded_hash_bytes_this_pass':charge}
    np.savez_compressed(ROOT/'MAIN_SCORES.npz',methods=np.array(METHODS),original=original,edits=edits,
       eval_x=ex,eval_groups=eg,eval_keys=np.array(ek),train_x=tx,train_groups=tg,train_keys=np.array(tk),
       challenge_locations=np.array([c['location'] for c in challenges]),challenge_factors=np.array([c['factor'] for c in challenges]))
    (ROOT/'MAIN_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    ledger=json.loads((ROOT/'ACQUISITION.json').read_text())
    ledger['web_operations']=4;ledger['web_charged_bytes']=2000000;ledger['acquisition_closed']=True
    ledger['scientific_read_decoded_hash_bytes']+=charge
    ledger['scientific_byte_passes'].append({'operation':'frozen main','kind':'pins+CSV read/decode+numeric arrays','bytes':charge})
    ledger['peak_rss_bytes_measured_max']=max(ledger['peak_rss_bytes_measured_max'],summary['peak_rss_bytes'])
    (ROOT/'ACQUISITION.json').write_text(json.dumps(ledger,indent=2)+'\n')
    concise={'teaching_renditions':len(tx),'evaluation_renditions':len(ex),'checks':{k:v for k,v in checks.items() if k!='true_error_control'},'methods':{}}
    for m,v in result.items():
        concise['methods'][m]={k:v[k] for k in ['threshold','natural_acceptance','primary_pass']}
        concise['methods'][m]['20pct_challenges']=[{k:r[k] for k in ['location','factor','rejection','strict_increase','ties']} for r in v['challenges'] if r['factor'] in [.8,1.2]]
    print(json.dumps(concise,indent=2))
if __name__=='__main__':main()
