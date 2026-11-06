"""Read only the certified consumed records, reconstruct causal histories/support."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import json, hashlib, zipfile, io, sys, datetime, resource
import numpy as np
import pandas as pd
from collections import Counter

ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent

def prefix(z,k,n=None):
    with z.open(k+'.npy') as f:
        v=np.lib.format.read_magic(f)
        shape,fort,dtype=(np.lib.format.read_array_header_1_0(f) if v==(1,0) else np.lib.format.read_array_header_2_0(f))
        assert not fort and not dtype.hasobject
        size=int(np.prod(shape)) if shape else 1
        take=size if n is None else min(n,size)
        b=f.read(take*dtype.itemsize)
        assert len(b)==take*dtype.itemsize
        a=np.frombuffer(b,dtype=dtype).copy()
        return (a.reshape(shape) if n is None else a),len(b),shape

def history(c,f,start,tau):
    a=np.exp(-1./tau);h=0.;out=np.empty(len(c))
    for t in range(len(c)):
        if start[t]:h=0.
        out[t]=h
        h=a*h+(1-a)*(c[t]*f[t] if c[t]!=0 else 0.)
    return out

def main():
    sample='--sample' in sys.argv
    m=json.loads((OUT/'ALLOWED_MANIFEST.json').read_text());allowed=m['subjects']
    humans=[r for r in allowed if r['species']=='human'];mice=[r for r in allowed if r['species']=='mouse']
    files={r['path'] for r in humans};raw_read=0;decoded=0;rows=[];pins=[];summ=[]
    for file in sorted(files):
        p=ROOT/file;b=p.read_bytes();raw_read+=len(b)
        pins.append(dict(path=file,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
        d=pd.read_csv(io.BytesIO(b),usecols=['subject','session','trial','probabilityLeft','contrastLeft','contrastRight','choice','feedbackType','instructions'],dtype={'subject':str,'session':str})
        decoded+=int(d.memory_usage(deep=True).sum())
        for r in humans:
            if r['path']!=file:continue
            if sample and r['subject']!=humans[0]['subject']:continue
            s=d[d.subject==r['subject']].sort_values('trial')
            assert len(s)==600 and s.session.nunique()==1 and s.session.iloc[0]==r['session']
            assert np.array_equal(s.trial,np.arange(600))
            cl=s.contrastLeft.to_numpy();cr=s.contrastRight.to_numpy()
            c=s.choice.to_numpy();fb=s.feedbackType.to_numpy();p0=s.probabilityLeft.to_numpy()
            rows.append(make(r,cl,cr,c,fb,p0,np.zeros(600,int),np.r_[True,np.zeros(599,bool)],np.full(600,np.nan)))
    for r in (mice[:1] if sample else mice):
        p=ROOT/r['path'];b=p.read_bytes();raw_read+=len(b);sh=hashlib.sha256(b).hexdigest()
        assert sh==r['expected_sha256'],r['subject']
        pins.append(dict(path=r['path'],bytes=len(b),sha256=sh,old_exposure_pin_matches=True))
        n=r['allowed_rows'][1]
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            d={}
            for k in ['contrastLeft','contrastRight','choice','feedbackType','probabilityLeft','session_index','session_start','repNum']:
                a,nb,shape=prefix(z,k,n);decoded+=nb
                assert shape==(r['indexed_total_rows'],),(r['subject'],k,shape)
                d[k]=a
            a,nb,shape=prefix(z,'metadata_json');decoded+=nb;meta=json.loads(str(a))
            for link in r['source_rows']:
                si=int(d['session_index'][link['global_start']]);mr=meta['sessions'][si]
                assert all(mr[k]==link[k] for k in ['date','number','eid','dataset_id'])
        rows.append(make(r,d['contrastLeft'],d['contrastRight'],d['choice'],d['feedbackType'],d['probabilityLeft'],d['session_index'],d['session_start'],d['repNum']))
    for d in rows:
        c=d['choice'];p=d['probabilityLeft'];ses=d['session'];start=d['session_start']
        same=~start[1:]
        switches=int(np.sum((p[1:]!=p[:-1]) & same))
        biased_switches=int(np.sum((p[1:]!=p[:-1]) & same & (p[1:]!=.5) & (p[:-1]!=.5)))
        summ.append(dict(subject=d['subject'],species=d['species'],n=len(c),sessions=len(np.unique(ses)),
                         probabilityLeft_counts={str(k):int(v) for k,v in zip(*np.unique(p,return_counts=True))},
                         within_session_prior_changes=switches,within_session_biased_prior_switches=biased_switches,
                         contrasts={str(k):int(v) for k,v in zip(*np.unique(np.abs(d['contrast']),return_counts=True))},
                         responses=int(np.sum(c!=0)),omissions=int(np.sum(c==0)),
                         revealed_side_sensory_checks=int(np.sum((c!=0)&(d['contrast']!=0))),
                         revealed_side_sensory_mismatches=int(np.sum((c!=0)&(d['contrast']!=0)&(np.sign(d['contrast'])!=c*d['feedback']))),
                         history_ranges={str(t):[float(d['h'+str(t)].min()),float(d['h'+str(t)].max())] for t in [2,8,32]}))
    key='FIRST_SUPPORT' if sample else 'SUPPORT'
    out=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='consumed development, no new holdout',
             subjects=summ,pins=pins,input_file_bytes_read=raw_read,decoded_bytes_charged=decoded,
             rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             timing='prediction uses only prior within-session responses and feedback; omissions decay traces; reset each session')
    for species in ['human','mouse']:
        s=[x for x in summ if x['species']==species]
        out[species]=dict(subjects=len(s),rows=sum(x['n'] for x in s),
                          prior_changes=sum(x['within_session_prior_changes'] for x in s),
                          biased_prior_switches=sum(x['within_session_biased_prior_switches'] for x in s),
                          sensory_mismatches=sum(x['revealed_side_sensory_mismatches'] for x in s))
    (OUT/(key+'.json')).write_text(json.dumps(out,indent=2)+'\n')
    if not sample:
        serial={}
        for i,d in enumerate(rows):
            for k,v in d.items():serial[str(i)+'__'+k]=np.asarray(v)
        np.savez_compressed(OUT/'consumed_inputs.npz',**serial)
    print(json.dumps({k:v for k,v in out.items() if k not in ['subjects','pins']},indent=2))

def make(r,cl,cr,c,fb,p,ses,start,rep):
    assert np.isin(c,[-1,0,1]).all(),(r['subject'],'choice',np.unique(c))
    assert np.isin(fb[c!=0],[-1,1]).all(),(r['subject'],'responding_feedback',np.unique(fb[c!=0]))
    assert np.isin(fb[c==0],[-1,0,1,np.nan]).all() or np.isnan(fb[c==0]).all()
    fb=np.nan_to_num(fb)
    x=np.nan_to_num(cl)-np.nan_to_num(cr)
    assert np.isfinite(x).all() and np.isfinite(p).all()
    d=dict(subject=r['subject'],species=r['species'],schedule=r.get('schedule',''),lab=r.get('lab','human'),condition=int(r.get('condition',-1)),
           contrast=x,choice=c,feedback=fb,probabilityLeft=p,session=ses,session_start=start,repNum=rep,
           trial=np.arange(len(c)),session_trial=np.arange(len(c))-np.maximum.accumulate(np.where(start,np.arange(len(c)),0)))
    for tau in [2,8,32]:d['h'+str(tau)]=history(c,fb,start,tau)
    prev=np.r_[0,c[:-1]];prev[start]=0;d['prev_choice']=prev
    return d

if __name__=='__main__':main()
