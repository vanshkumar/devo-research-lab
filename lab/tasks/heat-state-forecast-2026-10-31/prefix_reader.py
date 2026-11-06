"""Lexical projection: interpret only allowed metadata and pre-heat numeric values.

Acquired raw UTF-8 bytes include future outcomes and are charged/hash-checked.
The lexer traverses syntax but never converts non-whitelisted/future scalar values.
Full numerical outcome decoding is a separate command after forecasts are saved.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import argparse,copy,hashlib,json,pathlib,urllib.request
import numpy as np
import forecast as f
from prepare import extract
def ws(s,p):
    while p<len(s) and s[p].isspace():p+=1
    return p
def skip(s,p):
    p=ws(s,p)
    if s[p]=='"':
        p+=1
        while True:
            if s[p]=='\\':p+=2
            elif s[p]=='"':return p+1
            else:p+=1
    if s[p] in '[{':
        stack=[s[p]];p+=1
        while stack:
            if s[p]=='"':p=skip(s,p)
            elif s[p] in '[{':stack.append(s[p]);p+=1
            elif s[p] in ']}':
                assert (stack.pop(),s[p]) in [('[',']'),('{','}')]
                p+=1
            else:p+=1
        return p
    while p<len(s) and s[p] not in ',]} \t\r\n':p+=1
    return p
def spans(s):
    p=ws(s,0);assert s[p]=='{';p+=1;out={}
    while True:
        p=ws(s,p)
        if s[p]=='}':break
        q=skip(s,p);key=json.loads(s[p:q]);p=ws(s,q);assert s[p]==':'
        p=ws(s,p+1);q=skip(s,p);out[key]=(p,q);p=ws(s,q)
        if s[p]==',':p+=1
        else:assert s[p]=='}'
    return out
def prefix_array(s,start,end,n):
    assert s[start]=='[';p=start+1
    for _ in range(n):
        q=s.find(',',p,end)
        assert q>=0, 'Prefix unexpectedly reaches full array end'
        p=q+1
    # q is the comma following exactly n prefix scalar entries.
    return json.loads(s[start:q]+']')
def project(s):
    sp=spans(s);j={}
    for k in ['uid','dataset_type','events','timestamp_confocal','labeled','num_neurons']:
        a,b=sp[k];j[k]=json.loads(s[a:b])
    t=np.asarray(j['timestamp_confocal'],float);h=int(j['events']['heat'][0])-1;heat=float(t[h])
    n=int(np.searchsorted(t-heat,-5.,side='left'));assert n<h
    j['timestamp_confocal']=t[:n].tolist()
    for k in ['velocity','pumping','head_curvature']:
        a,b=sp[k];j[k]=prefix_array(s,a,b,n)
    a,b=sp['trace_original'];p=ws(s,a+1);rows=[]
    while s[p]!=']':
        q=skip(s,p);rows.append(prefix_array(s,p,q,n));p=ws(s,q)
        if s[p]==',':p=ws(s,p+1)
    assert len(rows)==j['num_neurons'];j['trace_original']=rows
    return extract(j,prefix_only=True,heat_time=heat),dict(uid=j['uid'],prefix_frames=n,total_timestamp_frames=len(t),heat_frame_0based=h,last_allowed_relative_time=float(t[n-1]-heat),numerical_response_values_decoded=n*(len(rows)+3),future_response_values_decoded=0)
def selftest():
    rng=np.random.default_rng(11031);n,T=3,1000;t=np.arange(T,dtype=float)
    j=dict(uid='synthetic',dataset_type=['heat','neuropal'],events={'heat':[501]},timestamp_confocal=t.tolist(),num_neurons=n,labeled={str(i+1):dict(label='A'+str(i),neuron_class='A'+str(i),confidence=5) for i in range(n)},trace_original=(2+rng.random((n,T))).tolist(),velocity=rng.normal(size=T).tolist(),pumping=rng.random(T).tolist(),head_curvature=rng.normal(size=T).tolist(),trace_array=[[999]*T]*n,encoding_changing_neurons=[1,2,3])
    p,meta=project(json.dumps(j))
    poison=copy.deepcopy(j)
    cut=meta['prefix_frames']
    for k in ['trace_original','trace_array']:
        for row in poison[k]:row[cut:]=[1e100]*(T-cut)
    for k in ['velocity','pumping','head_curvature']:poison[k][cut:]=[-1e100]*(T-cut)
    poison['encoding_changing_neurons']=['deliberate forbidden annotation change']
    q,_=project(json.dumps(poison))
    full=extract(j)
    checks={k:bool(np.array_equal(p[k],q[k],equal_nan=True)) if p[k].dtype.kind in 'fc' else bool(np.array_equal(p[k],q[k])) for k in p}
    direct={k:bool(np.array_equal(p[k],full[k][...,:cut],equal_nan=True)) for k in ['t','neural','ratio','behavior']}
    assert all(checks.values()) and all(direct.values())
    f.save('PREFIX_READER_CONTROL.json',dict(at_utc=f.now(),synthetic_only=True,source_metadata=meta,poisoned_future_and_annotation_invariance=checks,equality_with_direct_allowed_prefix=direct,future_scalar_values_interpreted=0))
    print('prefix reader control passed',json.dumps(meta))
def acquire():
    freeze=json.loads((f.TASK/'EVALUATION_FREEZE.json').read_text())
    for name,digest in freeze['code_and_config_sha256'].items():
        assert hashlib.sha256((f.TASK/name).read_bytes()).hexdigest()==digest,(name,'freeze mismatch')
    sp=json.loads((f.TASK/'SPLIT.json').read_text());manifest=[]
    for x in sp['items']:
        if x['part']!='evaluation':continue
        dest=f.SRC/pathlib.Path(x['path']).name
        assert not dest.exists(),'No uncharged repeat evaluation acquisition'
        url=f"https://raw.githubusercontent.com/{sp['repo']}/{sp['commit']}/{x['path']}"
        with urllib.request.urlopen(url,timeout=45) as r:b=r.read(x['size']+1)
        assert len(b)==x['size']
        assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['sha']
        dest.write_bytes(b)
        d,meta=project(b.decode('utf-8'))
        assert meta['uid']==x['uid']
        out=f.SRC/('prefix_'+x['uid']+'.npz');np.savez_compressed(out,**d)
        manifest.append(dict(meta,at_utc=f.now(),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),git_blob=x['sha'],prefix_path=str(out.relative_to(f.ROOT)),raw_status='raw acquired/hash-checked; future numeric outcomes uninterpreted'))
        f.save('EVALUATION_PREFIX_ACCESS.json',manifest)
        print(json.dumps(manifest[-1]),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true');ap.add_argument('--acquire',action='store_true');a=ap.parse_args()
    if a.control:selftest()
    if a.acquire:acquire()
