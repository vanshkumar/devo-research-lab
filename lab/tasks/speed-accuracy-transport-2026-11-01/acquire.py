"""One-time capped acquisition of two fixed public objects; no retries."""
from pathlib import Path
import urllib.request, hashlib, json, datetime, resource
ROOT=Path(__file__).resolve().parent
objects=[
 ('speed_acc.RData','https://raw.githubusercontent.com/rtdists/rtdists/83a31d43411692f86896c4c1d076ddcfa277cb83/data/speed_acc.RData',200000),
 ('wagenmakers2008.xml','https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2330283/fullTextXML',1500000)]
records=json.loads((ROOT/'ACQUISITION.json').read_text()) if (ROOT/'ACQUISITION.json').exists() else []
for name,url,cap in objects:
    if name=='speed_acc.RData' and (ROOT/'speed_acc.RData.base64').exists():
        print('Binary already acquired with GitHub fetch_file(base64); skipping remote request')
        continue
    p=ROOT/name
    if p.exists():
        raise RuntimeError('Refusing overwrite/reacquisition: '+name)
    r={'name':name,'url':url,'cap':cap,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(url,timeout=25) as f:
            data=f.read(cap+1)
            r.update(status=f.status,headers=dict(f.headers),body_bytes=len(data))
        if len(data)>cap: raise RuntimeError('cap exceeded')
        p.write_bytes(data)
        r.update(sha256=hashlib.sha256(data).hexdigest(),git_blob_sha1=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest())
        if name=='speed_acc.RData': assert r['git_blob_sha1']=='9800773f265db3b30e09ae81b52f612f43527454'
    except Exception as e:
        r['error']=repr(e)
    records.append(r)
    (ROOT/'ACQUISITION.json').write_text(json.dumps(records,indent=2))
    print({k:v for k,v in r.items() if k!='headers'})
print('maxrss_bytes_macos',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
