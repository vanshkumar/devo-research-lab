"""Actual repeated-phrase support: first six chronological recordings only."""
import collections,csv,datetime,io,json,pathlib,resource
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent

def read_rows(p):
    b=p.read_bytes();rows=list(csv.DictReader(io.StringIO(b.decode())))
    r=[(float(x['onset_s']),float(x['offset_s']),x['label']) for x in rows]
    assert all(np.isfinite([a,b]).all() and 0<=a<b and c for a,b,c in r)
    assert all(r[j][1]<=r[j+1][0] for j in range(len(r)-1))
    return r,len(b)

def phrases(r,motif):
    found=[]; j=0
    while j<=len(r)-len(motif):
        seg=r[j:j+len(motif)]
        if tuple(x[2] for x in seg)==tuple(motif):
            d=[]
            for k,x in enumerate(seg):
                d.append(x[1]-x[0])
                if k<len(seg)-1:d.append(seg[k+1][0]-x[1])
            if min(d)>0:found.append({'row_start':j,'start_s':seg[0][0],'seconds':d})
            j+=len(motif)
        else:j+=1
    return found

def main():
    files=sorted((ROOT/'sources/annotations').glob('*.csv'))
    assert len(files)==39
    count=collections.Counter();per={}; charge=0
    for p in files[:6]:
        r,b=read_rows(p);charge+=2*b
        per[p.name]={'rows':len(r),'labels':''.join(x[2] for x in r)}
        for j in range(len(r)-2):
            m=tuple(x[2] for x in r[j:j+3])
            if len(set(m))==3 and 'i' not in m:count[m]+=1
    assert count,'No distinct-label repeated phrase support'
    ranked=sorted(count,key=lambda m:(-count[m],m))
    motif=ranked[0]; samples=[]
    for p in files[:6]:
        r,b=read_rows(p);charge+=2*b
        for s in phrases(r,motif):samples.append(dict(s,file=p.name))
    x=np.array([s['seconds'] for s in samples]);lx=np.log(x)
    cov=np.cov(lx,rowvar=False);e=np.linalg.eigvalsh(cov)
    out={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'bird':'gy6or6','day':'032612','development_files':per,
      'rule':'most frequent consecutive nonintroductory trigram with 3 distinct labels in first6; count ties lexical',
      'top_motifs':[{'labels':m,'count':count[m]} for m in ranked[:8]],
      'chosen_motif':motif,'samples':samples,'n_renditions':len(x),
      'recordings_with_motif':len(set(s['file'] for s in samples)),
      'component_order':['duration1','gap1','duration2','gap2','duration3'],
      'component_mean_ms':(1000*x.mean(axis=0)).tolist(),
      'component_sd_ms':(1000*x.std(axis=0,ddof=1)).tolist(),
      'component_cv':(x.std(axis=0,ddof=1)/x.mean(axis=0)).tolist(),
      'log_covariance':cov.tolist(),'largest_eigenvalue_fraction':float(e[-1]/e.sum()),
      'global_logtempo_sd':float(lx.mean(axis=1).std(ddof=1)),
      'additional_read_decoded_bytes':charge,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (ROOT/'DEVELOPMENT.json').write_text(json.dumps(out,indent=2)+'\n')
    ledger=json.loads((ROOT/'ACQUISITION.json').read_text());ledger['scientific_read_decoded_hash_bytes']+=charge
    ledger['scientific_byte_passes'].append({'operation':'first6 actual variability','bytes':charge,'kind':'annotation read+decode; two passes'})
    ledger['peak_rss_bytes_measured_max']=max(ledger['peak_rss_bytes_measured_max'],out['peak_rss_bytes'])
    (ROOT/'ACQUISITION.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ['samples','log_covariance']},indent=2))
if __name__=='__main__':main()
