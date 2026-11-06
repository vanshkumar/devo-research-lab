"""Verified cached HTTP-range HDF5 acquisition. No count outcomes in metadata mode."""
import argparse, io, json, hashlib, os, sys, time
from collections import OrderedDict
from pathlib import Path
import requests, h5py, numpy as np
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'inputs'/'range_cache'; CACHE.mkdir(exist_ok=True)
URL='https://datasets.cellxgene.cziscience.com/af06d70d-a2bc-43c1-8378-bc545bc8ee2c.h5ad'
SIZE=5231283640
CHUNK=2**20
LOG=ROOT/'logs'/'acquire_ranges.jsonl'

def js(v):
    if isinstance(v, bytes): return v.decode()
    if isinstance(v, (np.ndarray, list, tuple)): return [js(x) for x in v]
    if isinstance(v, np.generic): return js(v.item())
    if isinstance(v, dict): return {str(k):js(x) for k,x in v.items()}
    return v

class RangeFile(io.RawIOBase):
    def __init__(self): self.pos=0; self.s=requests.Session(); self.n=0; self.memory=OrderedDict(); self.verified=set()
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, offset, whence=0):
        self.pos=offset if whence==0 else self.pos+offset if whence==1 else SIZE+offset
        return self.pos
    def chunk(self, i):
        start=i*CHUNK; end=min(SIZE,start+CHUNK)-1
        p=CACHE/f'{start:012d}-{end:012d}.bin'; m=p.with_suffix('.json')
        if i in self.memory:
            self.memory.move_to_end(i); return self.memory[i]
        if p.exists() and m.exists():
            b=p.read_bytes()
            if i not in self.verified:
                meta=json.loads(m.read_text())
                assert len(b)==end-start+1 and hashlib.sha256(b).hexdigest()==meta['sha256']
                self.verified.add(i)
            self.memory[i]=b
            if len(self.memory)>8: self.memory.popitem(last=False)
            return b
        for trial in range(4):
            try:
                r=self.s.get(URL,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'},timeout=90)
                assert r.status_code==206, (r.status_code,r.text[:100])
                assert r.headers.get('Content-Range')==f'bytes {start}-{end}/{SIZE}',dict(r.headers)
                b=r.content; assert len(b)==end-start+1
                meta={'url':URL,'start':start,'end':end,'size':len(b),'sha256':hashlib.sha256(b).hexdigest(),'status':r.status_code,'headers':dict(r.headers),'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
                p.write_bytes(b); m.write_text(json.dumps(meta,indent=2)); self.n+=len(b)
                with LOG.open('a') as f: f.write(json.dumps(meta)+'\n')
                print('range',start,end,'downloaded',self.n,flush=True)
                return b
            except Exception as e:
                with LOG.open('a') as f: f.write(json.dumps({'start':start,'end':end,'trial':trial,'error':str(e)})+'\n')
                if trial==3: raise
                time.sleep(2)
    def read(self,n=-1):
        if n<0: n=SIZE-self.pos
        n=min(n,SIZE-self.pos); end=self.pos+n; out=[]
        while self.pos<end:
            i=self.pos//CHUNK; b=self.chunk(i); a=self.pos%CHUNK; take=min(end-self.pos,len(b)-a)
            out.append(b[a:a+take]); self.pos+=take
        return b''.join(out)
    def readinto(self,b):
        out=self.read(len(b)); b[:len(out)]=out; return len(out)

def read_col(g):
    if isinstance(g,h5py.Dataset): return js(g[:])
    cats=js(g['categories'][:]); codes=g['codes'][:]
    return [cats[i] if i>=0 else None for i in codes]

def metadata():
    import csv
    rf=RangeFile()
    with h5py.File(rf,'r') as h:
        layout={}
        for key in ['X','raw/X','var','raw/var','obs']:
            o=h[key]; layout[key]={'attrs':js(dict(o.attrs)),'children':list(o)}
            for k in o:
                d=o[k]
                if isinstance(d,h5py.Dataset): layout[key][k]={'shape':d.shape,'dtype':str(d.dtype),'chunks':d.chunks,'compression':d.compression,'offset':d.id.get_offset()}
        (ROOT/'inputs'/'hdf5_layout.json').write_text(json.dumps(layout,indent=2))
        cols={k:read_col(h['obs'][k]) for k in h['obs']}
        n=len(cols['_index']); assert all(len(x)==n for x in cols.values())
        with (ROOT/'inputs'/'obs.csv').open('w') as f:
            w=csv.writer(f); w.writerow(['row_index']+list(cols)); w.writerows([i]+[x[i] for x in cols.values()] for i in range(n))
        for vname in ['var','raw/var']:
            vg=h[vname]; vs={k:read_col(vg[k]) for k in vg}; nvar=len(next(iter(vs.values())))
            with (ROOT/'inputs'/(vname.replace('/','_')+'.csv')).open('w') as f:
                w=csv.writer(f); w.writerow(['column_index']+list(vs)); w.writerows([i]+[x[i] for x in vs.values()] for i in range(nvar))
        from collections import Counter
        target=[i for i,x in enumerate(cols['C4_named']) if str(x).startswith(('C4-313 ', 'C4-296 ', 'C4-312 ', 'C4-315 '))]
        summary={'n_obs':n,'C4_count':len(set(cols['C4_named'])),'candidate_and_comparison_metadata':dict(Counter((cols['C4_named'][i],cols['Dataset'][i],cols['donor_id'][i],cols['Sample_ID'][i]) for i in target))}
        summary['candidate_and_comparison_metadata']=[{'C4_named':k[0],'Dataset':k[1],'donor_id':k[2],'Sample_ID':k[3],'n':v} for k,v in summary['candidate_and_comparison_metadata'].items()]
        (ROOT/'inputs'/'metadata_summary.json').write_text(json.dumps(summary,indent=2))
        print(json.dumps(summary,indent=2))
    rf.close()


def select():
    import pandas as pd
    obs=pd.read_csv(ROOT/'inputs'/'obs.csv',keep_default_na=False)
    target=obs.C4_named.str.match(r'^C4-(296|312|313|315) ')
    donors=set(obs.loc[obs.C4_named.str.startswith('C4-313 '),'donor_id'])
    mid=obs.C4_named.str.contains('Mid-3',regex=False)
    excluded=target|obs.C4_named.str.contains('OXT|AVP',regex=True)
    rng=np.random.default_rng(28102026)
    obs['depth_decile']=obs.groupby('donor_id')['nCount_RNA'].transform(lambda x: pd.qcut(x.rank(method='first'),10,labels=False)).astype(int)
    # Deciles across each donor's full atlas, fixed before all expression inspection.
    obs['pool']=''
    obs.loc[mid&~excluded,'pool']='near_mid3'
    obs.loc[mid&excluded,'pool']='other_mid3_peptide'
    for c in [296,312,313,315]: obs.loc[obs.C4_named.str.startswith(f'C4-{c} '),'pool']='candidate' if c==313 else 'peptide_comparison'
    for label,mask in [('broad_neuronal',(obs.C0_named=='C0-3 Neuron')&~mid&~excluded),('non_neuronal',(obs.C0_named!='C0-3 Neuron'))]:
        for (_,d),grp in obs[mask&obs.donor_id.isin(donors)].groupby(['donor_id','depth_decile'],sort=True):
            chosen=rng.choice(grp.index.to_numpy(),min(100,len(grp)),replace=False)
            obs.loc[chosen,'pool']=label
            obs.loc[chosen,'pool_sampling_probability']=len(chosen)/len(grp)
    obs.loc[mid,'pool_sampling_probability']=1.
    selected=obs.loc[obs.pool!=''].copy().sort_values('row_index')
    selected.to_csv(ROOT/'inputs'/'selected_obs.csv',index=False)
    selected.loc[target].to_csv(ROOT/'inputs'/'peptide_obs.csv',index=False)
    summary={'seed':28102026,'depth_deciles':'within donor across all atlas cells, rank ties by original row order','candidate_donors':sorted(donors),'pool_counts':selected.groupby('pool').size().to_dict(),'selected_n':len(selected),'peptide_n':int(target.sum()),'selection_time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'selection_before_count_outcomes':True}
    (ROOT/'inputs'/'selection_manifest.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2),flush=True)

def extract(which):
    import pandas as pd
    from scipy.sparse import csr_matrix, save_npz
    obs=pd.read_csv(ROOT/'inputs'/f'{which}_obs.csv',keep_default_na=False)
    rows=obs.row_index.to_numpy(); assert np.all(np.diff(rows)>0)
    rf=RangeFile(); data=[]; indices=[]; ptr=[0]; rowsum=[]; nfeature=[]
    with h5py.File(rf,'r') as h:
        x=h['raw/X']; fullptr=x['indptr'][:]
        # Each read is a CSR row. Count values preserved as float32, no rounding.
        for i,r in enumerate(rows):
            lo,hi=map(int,fullptr[r:r+2]); a=x['data'][lo:hi]; j=x['indices'][lo:hi]
            assert np.all(np.isfinite(a)) and np.all(a>=0)
            data.append(a); indices.append(j.astype(np.int32)); ptr.append(ptr[-1]+len(a))
            rowsum.append(float(a.sum(dtype=np.float64))); nfeature.append(int(np.count_nonzero(a)))
            if i%100==0: print('extract',which,i,len(rows),'rawsum',rowsum[-1],flush=True)
        mat=csr_matrix((np.concatenate(data),np.concatenate(indices),np.array(ptr)),shape=(len(rows),36924))
        save_npz(ROOT/'inputs'/f'{which}_counts.npz',mat,compressed=True)
        obs['raw_total']=rowsum; obs['raw_nfeature']=nfeature; obs.to_csv(ROOT/'inputs'/f'{which}_obs.csv',index=False)
        report={'layer':'raw/X','shape':mat.shape,'nnz':mat.nnz,'dtype':str(mat.data.dtype),'min':float(mat.data.min()),'max':float(mat.data.max()),'noninteger_values':int(np.count_nonzero(mat.data!=np.floor(mat.data))),'max_fractional_distance':float(np.max(np.abs(mat.data-np.rint(mat.data)))),'metadata_nCount_max_absolute_difference':float(np.max(np.abs(obs.nCount_RNA-obs.raw_total))),'metadata_nFeature_max_absolute_difference':int(np.max(np.abs(obs.nFeature_RNA-obs.raw_nfeature))),'raw_X_HDF5_object_address':h5py.h5o.get_info(h['raw/X'].id).addr,'X_HDF5_object_address':h5py.h5o.get_info(h['X'].id).addr}
        for f in [f'{which}_counts.npz',f'{which}_obs.csv','raw_var.csv','selection_manifest.json']:
            p=ROOT/'inputs'/f; report[f]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        (ROOT/'inputs'/f'{which}_extraction_manifest.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2),flush=True)
    rf.close()


def normalization_check():
    import pandas as pd
    from scipy.sparse import load_npz
    obs=pd.read_csv(ROOT/'inputs'/'peptide_obs.csv'); raw=load_npz(ROOT/'inputs'/'peptide_counts.npz')
    selected=obs.groupby('Dataset',sort=True).head(3).index
    rf=RangeFile(); reports=[]; vectors={}
    with h5py.File(rf,'r') as h:
        x=h['X']; ptr=x['indptr'][:]
        for local in selected:
            row=obs.iloc[local]; source=int(row.row_index); lo,hi=map(int,ptr[source:source+2]); a=x['data'][lo:hi]; j=x['indices'][lo:hi]
            rr=raw.getrow(local); assert np.array_equal(j,rr.indices)
            actual=np.log1p(1e4*rr.data.astype(float)/row.raw_total)
            metadata=np.log1p(1e4*rr.data.astype(float)/row.nCount_RNA)
            denom=1e4*rr.data/np.expm1(a)
            reports.append({'row_index':source,'barcode':row['_index'],'Dataset':row.Dataset,'nCount_RNA':row.nCount_RNA,'raw_total':row.raw_total,'raw_nfeature':row.raw_nfeature,'nFeature_RNA':row.nFeature_RNA,'X_min':float(a.min()),'X_max':float(a.max()),'rawdenom_max_error':float(np.max(np.abs(a-actual))),'metadenom_max_error':float(np.max(np.abs(a-metadata))),'implied_denominator_median':float(np.median(denom))})
            vectors[str(source)+'_X']=a; vectors[str(source)+'_raw']=rr.data; vectors[str(source)+'_indices']=j
    pd.DataFrame(reports).to_csv(ROOT/'inputs'/'normalization_check.csv',index=False)
    np.savez_compressed(ROOT/'inputs'/'normalization_check_vectors.npz',**vectors)
    print(json.dumps(js(reports),indent=2)); rf.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('mode',choices=['metadata','select','peptide','selected','normalization_check']); a=p.parse_args()
    if a.mode=='metadata': metadata()
    elif a.mode=='select': select()
    elif a.mode=='normalization_check': normalization_check()
    else: extract(a.mode)
