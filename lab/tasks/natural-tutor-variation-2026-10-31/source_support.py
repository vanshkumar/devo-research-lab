"""One-pass finite archive inventory and development-only support calculation."""
import collections, csv, datetime, gzip, hashlib, io, json, pathlib, resource, tarfile, wave
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parent
class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,d):
        if d.strip(): self.parts.append(d.strip())
class Count:
    def __init__(self,f,cap,digest=False): self.f=f; self.cap=cap;self.n=0;self.md5=hashlib.md5() if digest else None
    def read(self,n=-1):
        if self.n>=self.cap: raise RuntimeError('read cap reached')
        b=self.f.read(min(n if n>=0 else self.cap-self.n,self.cap-self.n));self.n+=len(b)
        if self.md5 is not None:self.md5.update(b)
        return b
def main():
    ledger=json.loads((ROOT/'ACQUISITION.json').read_text())
    # Second public search: prior work. Conservative charge covers returned result text;
    # transport telemetry remains unavailable and is never reported as measured bytes.
    if ledger['web_operations']==1:
        ledger['web_operations']=2;ledger['web_charged_bytes']=1000000
    html=(ROOT/'sources/bfsongrepo.html').read_bytes();p=Text();p.feed(html.decode())
    (ROOT/'METHODOLOGY.txt').write_text('\n'.join(p.parts)+'\n')
    annotation_dir=ROOT/'sources/annotations';annotation_dir.mkdir(exist_ok=True)
    src=ROOT/'sources/gy6or6_032612_complete.tar.gz'
    compressed=Count(src.open('rb'),src.stat().st_size+1,True)
    decoded=Count(gzip.GzipFile(fileobj=compressed),50000000)
    report={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'bird':'gy6or6','day':'032612','members':[],'wav':[],'csv':[], 'development_preview':[]}
    charge=0; samplebytes=0; csvbytes=0
    try:
        with tarfile.open(fileobj=decoded,mode='r|') as t:
            for m in t:
                if not m.isfile():continue
                report['members'].append({'name':m.name,'size':m.size})
                if m.name.endswith('.csv'):
                    if m.size>1000000:raise RuntimeError('oversized annotation')
                    b=t.extractfile(m).read();csvbytes+=len(b)
                    name=pathlib.PurePosixPath(m.name).name
                    (annotation_dir/name).write_bytes(b)
                    report['csv'].append({'name':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
                elif m.name.endswith('.wav'):
                    # ExFileObject in streaming tar mode lacks seekable(); a bounded
                    # BytesIO header supports wave's ordinary header parser.
                    b=t.extractfile(m).read(min(4096,m.size));samplebytes+=len(b)
                    with wave.open(io.BytesIO(b),'rb') as w:
                        report['wav'].append({'name':pathlib.PurePosixPath(m.name).name,'bytes':m.size,
                          'rate':w.getframerate(),'frames':w.getnframes(),'channels':w.getnchannels(),
                          'samplewidth':w.getsampwidth(),'seconds':w.getnframes()/w.getframerate()})
        # gzip tail must be consumed to verify trailer/full MD5 without a new read pass.
        while decoded.read(65536):pass
        report['archive_status']='complete; gzip trailer read'
    except Exception as e:
        report['archive_status']='partial';report['error']=repr(e)
    report['archive_md5']=compressed.md5.hexdigest()
    report['compressed_bytes_read']=compressed.n;report['decoded_tape_bytes']=decoded.n
    report['extracted_csv_bytes']=csvbytes
    # Decode only the first two chronological recording annotations at this support stage.
    for x in sorted(report['csv'],key=lambda z:z['name'])[:2]:
        b=(annotation_dir/x['name']).read_bytes();charge+=len(b)
        rows=list(csv.reader(io.StringIO(b.decode())))
        report['development_preview'].append({'name':x['name'],'nrows':len(rows),'first_rows':rows[:8]})
    report['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if (ROOT/'SOURCE_SUPPORT.json').exists():
        (ROOT/'SOURCE_SUPPORT.failed1.json').write_bytes((ROOT/'SOURCE_SUPPORT.json').read_bytes())
    (ROOT/'SOURCE_SUPPORT.json').write_text(json.dumps(report,indent=2)+'\n')
    charge+=compressed.n+decoded.n+2*csvbytes+samplebytes+2*len(html)+19425
    ledger['scientific_read_decoded_hash_bytes']+=charge
    ledger['scientific_byte_passes'].append({'operation':'source_support','kind':'compressed+decoded+csv extraction/hash+development preview+docs and prior metadata read','bytes':charge})
    ledger['peak_rss_bytes_measured_max']=max(report['peak_rss_bytes'],42745856)
    (ROOT/'ACQUISITION.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print(json.dumps({'archive_status':report['archive_status'],'md5':report['archive_md5'],
        'wav_files':len(report['wav']),'csv_files':len(report['csv']),
        'wav_duration_s':sum(x['seconds'] for x in report['wav']),
        'development_preview':report['development_preview'],
        'compressed_bytes':compressed.n,'decoded_bytes':decoded.n,'cumulative_scientific_bytes':ledger['scientific_read_decoded_hash_bytes'],
        'peak_rss_bytes':report['peak_rss_bytes']},indent=2))
    print('\nMETHODOLOGY PASSAGES\n'+'\n'.join(x for x in p.parts if any(s in x.lower() for s in ['record','label','csv','onset','offset','directed','32','bird','noise'])))
if __name__=='__main__':main()
