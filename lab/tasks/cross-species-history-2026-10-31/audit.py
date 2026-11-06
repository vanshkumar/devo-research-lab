"""Independent reconstruction; imports no feature/fitting code from main analysis."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import csv,json,hashlib,zipfile,io,datetime,resource,time
import numpy as np
import pandas as pd
from scipy.special import expit

ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent;RES=OUT/'corrected'
READ=0;DECODED=0

def read(p):
    global READ
    b=Path(p).read_bytes();READ+=len(b);return b

def jread(p):return json.loads(read(p))

def human_primary():
    base=ROOT/'campaigns/human_learning_routes_2026-10-28';lookup={};pins=[]
    fields=['probabilityLeft','contrastLeft','contrastRight','choice','feedbackType']
    for name,record in [('development_numeric.csv','DEVELOPMENT_RELEASE.json'),('validation_numeric.csv','VALIDATION_OPENED.json')]:
        b=read(base/'inputs'/name);pin=hashlib.sha256(b).hexdigest();expected=jread(base/'protocol'/record)['sha256'];assert pin==expected
        pins.append(dict(path=name,sha256=pin,old_pin_matches=True))
        for r in csv.DictReader(io.StringIO(b.decode())):
            key=(r['subject'],int(r['trial']));assert key not in lookup
            lookup[key]=(r['session'],[float(r[k]) if r[k] else float('nan') for k in fields])
    hasher=hashlib.sha256();seen=set();mismatches=[];total=0
    global READ
    raw=base/'inputs/processed_data_2026.csv'
    def lines(f):
        global READ
        for b in f:
            READ+=len(b);hasher.update(b);yield b.decode()
    with raw.open('rb') as f:
        for r in csv.DictReader(lines(f)):
            key=(r['subject'],int(r['trial']));assert key in lookup and key not in seen
            seen.add(key);session,expected=lookup[key]
            assert session==r['session']
            for k,e in zip(fields,expected):
                v=float(r[k]) if r[k] else float('nan')
                if not ((np.isnan(v) and np.isnan(e)) or v==e):mismatches.append([key,k,v,e])
                total+=1
    assert hasher.hexdigest()=='45dcce14e30edba5e38eaeaf8c40edb8cd1a0555928070b44779d0d47458bbe9'
    assert len(seen)==48000 and not mismatches
    return dict(rows=len(seen),scalar_comparisons=total,mismatches=0,raw_sha256=hasher.hexdigest(),derivative_pins=pins,
                scope='Only subject/session/trial and five numeric columns interpreted; cursor trajectory strings never decoded as arrays')

def cached_prefixes():
    global DECODED
    b=read(OUT/'consumed_inputs.npz');result=[]
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        units=sorted({int(x.filename.split('__')[0]) for x in z.infolist()})
        for i in units:
            d={}
            for info in z.infolist():
                if not info.filename.startswith(str(i)+'__'):continue
                k=info.filename.split('__',1)[1][:-4]
                with z.open(info) as f:
                    version=np.lib.format.read_magic(f)
                    shape,fort,dtype=(np.lib.format.read_array_header_1_0(f) if version==(1,0) else np.lib.format.read_array_header_2_0(f))
                    assert not fort and not dtype.hasobject
                    take=min(600,shape[0]) if shape else 1
                    bb=f.read(take*dtype.itemsize);DECODED+=len(bb)
                    a=np.frombuffer(bb,dtype=dtype).copy()
                    d[k]=a if shape else a.reshape(())
            result.append(d)
    return result

def reconstruct(data):
    N=[];H=[];S=[];records=[];errors=[];alpha=np.exp(-1/np.array([2.,8.,32.]))
    for u,d in enumerate(data):
        c=d['choice'].astype(float);f=d['feedback'];x=d['contrast'];sg=np.sign(x);n=len(c);starts=d['session_start'].astype(bool)
        h=np.zeros(3);q=np.zeros(3);s=np.zeros(3);history=[];response=[];stim=[];prev=[];last=0.
        for t in range(n):
            if starts[t]:h[:]=0;q[:]=0;s[:]=0;last=0.
            history.append(h.copy());response.append(q.copy());stim.append(s.copy());prev.append(last)
            h=alpha*h+(1-alpha)*(c[t]*f[t] if c[t]!=0 else 0.)
            q=alpha*q+(1-alpha)*c[t];s=alpha*s+(1-alpha)*sg[t];last=c[t]
        history=np.asarray(history);response=np.asarray(response);stim=np.asarray(stim)
        errors.append(float(np.max(np.abs(history-np.column_stack([d['h2'],d['h8'],d['h32']])))))
        early=(np.arange(n)<200);rr=early&(c!=0);ss=rr&(x!=0)
        a=float(np.mean(c[ss]*sg[ss])) if ss.any() else 0.;bias=float(np.mean(c[rr])) if rr.any() else 0.;omit=float(np.mean(c[early]==0))
        g=int(d['condition']) if str(d['species'])=='human' else 2
        for t in range(200,n):
            if d['session_trial'][t]<32 or abs(x[t]) not in [0,.25,.5,1.]:continue
            tt=(t-399.5)/200.
            v=[1.]+[float(sg[t]*np.isclose(abs(x[t]),cc,rtol=0,atol=1e-10)) for cc in [.0625,.1,.125,.25,.5,1.]]+[prev[t]]+response[t].tolist()+[tt,sg[t]*tt,a,bias,omit,sg[t]*a,sg[t]*bias,d['session'][t]/5.,min(d['session_trial'][t],600)/600.]
            nn=np.zeros(60);nn[g*20:(g+1)*20]=v;st=np.zeros(9);st[g*3:(g+1)*3]=stim[t]
            N.append(nn);S.append(st);H.append(history[t]);records.append((u,str(d['subject']),str(d['species']),t,float(x[t]),float(c[t])))
    assert max(errors)<1e-15
    return np.asarray(N),np.asarray(H),np.asarray(S),records,max(errors)

def weight(frame,train):
    ids=np.where(train)[0];f=frame.iloc[ids];w=np.zeros(len(ids))
    for species in ['human','mouse']:
        j=np.where(f.species.to_numpy()==species)[0];a=f.iloc[j];counts=a.unit.value_counts()
        w[j]=[1/(2*len(counts)*counts[u]) for u in a.unit]
    return w/w.sum()

def main():
    begun=time.time();raw=human_primary();data=cached_prefixes();N,H,S,records,herror=reconstruct(data)
    frame=pd.read_csv(io.BytesIO(read(RES/'scoring_rows.csv')),dtype={'subject':str})
    assert len(frame)==len(records)
    for a,b in zip(records,frame.itertuples(index=False)):
        assert a==(b.unit,b.subject,b.species,b.trial,b.contrast,b.choice)
    fits=jread(RES/'FITS.json');summary=jread(RES/'SUMMARY.json');pins=jread(OUT/'FREEZE.json')
    for p,h in pins['sha256'].items():assert hashlib.sha256(read(OUT/p)).hexdigest()==h,p
    with np.load(io.BytesIO(read(RES/'predictions.npz')),allow_pickle=False) as z:pp={k:z[k] for k in z.files}
    global DECODED
    DECODED+=sum(v.nbytes for v in pp.values())
    y=(frame.choice.to_numpy()==1).astype(float);valid=frame.responded.to_numpy();is_mouse=(frame.species.to_numpy()=='mouse')
    assert np.array_equal(y,pp['y'])
    maxerr=0.;maxgrad=0.;maxobj=0.;pred={};scopes={};point_errors=[]
    for log in fits:
        aug=log['augmented'];base=np.column_stack([N,S]) if aug else N;name=log['model'];fold=log['fold']
        test=valid&(frame.fold.to_numpy()==fold);train=valid&(frame.fold.to_numpy()!=fold)
        if name=='H':X=np.column_stack([base,H])
        elif name=='T':X=np.column_stack([base,H*(~is_mouse[:,None]),H*is_mouse[:,None]])
        else:X=base
        if name.endswith('_fixed'):
            beta=np.array(log['nuisance_coefficients']);offset=np.einsum('ij,j->i',H,log['source_history'],optimize=False)
        else:beta=np.array(log['coefficients']);offset=np.zeros(len(frame))
        eta=np.einsum('ij,j->i',X,beta,optimize=False)+offset;p=expit(eta)
        key=('S_' if aug else 'B_')+name
        if key not in pred:pred[key]=np.full(len(y),np.nan)
        pred[key][test]=p[test]
        err=float(np.max(np.abs(p[test]-pp[key][test])));maxerr=max(maxerr,err)
        w=weight(frame,train);r=expit(eta[train])-y[train]
        grad=np.einsum('ij,i->j',X[train],w*r,optimize=False)+1e-4*beta
        maxgrad=max(maxgrad,float(np.max(np.abs(grad))))
        obj=float(np.sum(w*(np.logaddexp(0,eta[train])-y[train]*eta[train]))+.5e-4*np.sum(beta*beta))
        maxobj=max(maxobj,abs(obj-log['objective']))
    assert maxerr<1e-14 and maxgrad<=1e-6 and maxobj<1e-12
    score_cache={};strata=[]
    for baseline in ['B','S']:
        saved=pd.read_csv(io.BytesIO(read(RES/('unit_scores_'+baseline+'.csv'))),dtype={'subject':str})
        for scope in ['support','all_common_contrast','zero','high']:
            mask=valid.copy()
            if scope=='support':mask &= frame.common_support.to_numpy()
            if scope=='zero':mask &= frame.contrast.to_numpy()==0
            if scope=='high':mask &= abs(frame.contrast.to_numpy())>=.5
            loss={}
            for name in ['B','H','T','human_fixed','mouse_fixed']:
                p=np.clip(pred[baseline+'_'+name],1e-9,1-1e-9)
                loss[name]=-(y*np.log(p)+(1-y)*np.log1p(-p))
            for species in ['human','mouse']:
                groups=frame.loc[mask&(frame.species.to_numpy()==species)].groupby('unit')
                unitloss={name:[] for name in loss}
                for u,a0 in groups:
                    ii=a0.index.to_numpy();savedrow=saved[(saved.unit==u)&(saved.scope==scope)].iloc[0]
                    for name,v in loss.items():
                        actual=float(np.mean(v[ii]));point_errors.append(abs(actual-savedrow[name+'_loss']));unitloss[name].append(actual)
                for row in summary:
                    if row['baseline']!=baseline or row['scope']!=scope or row['species']!=species:continue
                    a0,b0=row['comparison'].split('-minus-');gain=float(np.mean(np.array(unitloss[b0])-np.array(unitloss[a0])));point_errors.append(abs(gain-row['gain_nat']))
        # Declared current-contrast strata, using empirical common-support rows.
        for species in ['human','mouse']:
            for contrast in [0.,.25,.5,1.]:
                mask=valid&frame.common_support.to_numpy()&(frame.species.to_numpy()==species)&np.isclose(abs(frame.contrast.to_numpy()),contrast)
                r=dict(baseline=baseline,species=species,absolute_contrast=contrast,rows=int(mask.sum()),units=int(frame.loc[mask,'unit'].nunique()))
                for a,b in [('H','B'),('T','H'),('human_fixed','B'),('mouse_fixed','B')]:
                    ds=[]
                    for u,g in frame.loc[mask].groupby('unit'):
                        ii=g.index.to_numpy();pa=np.clip(pred[baseline+'_'+a][ii],1e-9,1-1e-9);pb=np.clip(pred[baseline+'_'+b][ii],1e-9,1-1e-9)
                        ds.append(float(np.mean(y[ii]*np.log(pa/pb)+(1-y[ii])*np.log((1-pa)/(1-pb)))))
                    r[a+'-minus-'+b]=float(np.mean(ds)) if ds else None
                strata.append(r)
    assert max(point_errors)<1e-13
    # Prepare a bounded original-Parquet check for 6 input-blind identities (3 old allocations).
    allowed=jread(OUT/'ALLOWED_MANIFEST.json')['subjects'];selected=[]
    for split in ['dev','animal_holdout','lab_holdout']:
        rs=sorted([r for r in allowed if r['species']=='mouse' and r['old_split']==split],key=lambda r:r['subject'])[:2]
        for r in rs:
            d=next(d for d in data if str(d['subject'])==r['subject']);n=len(d['choice'])
            selected.append(dict(subject=r['subject'],old_split=split,links=r['source_rows'],n=n,
                                 values=np.column_stack([d[k] for k in ['contrast','choice','feedback','probabilityLeft']]).tolist()))
    (OUT/'ORIGINAL_MOUSE_REQUEST.json').write_text(json.dumps(selected,indent=2)+'\n')
    result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),human_primary=raw,history_reconstruction_max_error=herror,
                fitted_records=len(fits),prediction_max_error=maxerr,fit_gradient_max=maxgrad,objective_max_error=maxobj,
                all_unit_and_summary_point_score_max_error=max(point_errors),freeze_pins_pass=True,
                read_bytes=READ,decoded_bytes=DECODED,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,elapsed_seconds=time.time()-begun,
                limitations='Author-side independent implementation; no independent scientist signoff; no optimizer refit or biological uncertainty coverage certification')
    (OUT/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'CONTRAST_STRATA.json').write_text(json.dumps(strata,indent=2)+'\n')
    print(json.dumps(result,indent=2));print(json.dumps([r for r in summary if r['scope']=='support' and r['comparison'] in ['H-minus-B','T-minus-H','human_fixed-minus-B','mouse_fixed-minus-B']],indent=2))

if __name__=='__main__':main()
