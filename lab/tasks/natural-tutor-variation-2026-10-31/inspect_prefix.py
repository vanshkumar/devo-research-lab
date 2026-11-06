"""Inspect a finite compressed prefix without extracting paths or opening other data."""
import csv, datetime, gzip, hashlib, io, json, pathlib, resource, sys, tarfile, wave
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parent

class Counter:
    def __init__(self, f, cap): self.f=f; self.n=0; self.cap=cap
    def read(self,n=-1):
        n=min(n if n>=0 else self.cap-self.n,self.cap-self.n)
        if n<=0: raise RuntimeError('decoded cap reached')
        b=self.f.read(n); self.n+=len(b); return b

class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,d):
        if d.strip(): self.parts.append(d.strip())

def main():
    name=sys.argv[1]; out=sys.argv[2]
    p=ROOT/'sources'/name
    report={'source':name,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'members':[], 'csv_samples':[], 'wave_samples':[]}
    compressed=Counter(p.open('rb'),p.stat().st_size+1)
    decoded=Counter(gzip.GzipFile(fileobj=compressed),20000000)
    csv_bytes=0; wave_bytes=0
    try:
        with tarfile.open(fileobj=decoded,mode='r|') as t:
            for m in t:
                report['members'].append({'name':m.name,'size':m.size,'type':str(m.type)})
                if not m.isfile(): continue
                if m.name.endswith('.csv'):
                    if m.size>1000000: raise RuntimeError('CSV member exceeds sample cap')
                    b=t.extractfile(m).read(); csv_bytes+=len(b)
                    rows=list(csv.reader(io.StringIO(b.decode())))
                    report['csv_samples'].append({'name':m.name,'bytes':len(b),
                        'sha256':hashlib.sha256(b).hexdigest(),'rows':rows})
                elif m.name.endswith('.wav') and len(report['wave_samples'])<1 and m.size<=10000000:
                    b=t.extractfile(m).read(); wave_bytes+=len(b)
                    with wave.open(io.BytesIO(b),'rb') as w:
                        report['wave_samples'].append({'name':m.name,'bytes':len(b),
                          'sha256':hashlib.sha256(b).hexdigest(),'nchannels':w.getnchannels(),
                          'sampwidth':w.getsampwidth(),'samplerate':w.getframerate(),
                          'frames':w.getnframes(),'duration_s':w.getnframes()/w.getframerate()})
    except (EOFError,tarfile.ReadError,RuntimeError) as e: report['prefix_end']=repr(e)
    report['compressed_bytes_read']=compressed.n; report['decoded_tape_bytes']=decoded.n
    report['extracted_csv_bytes']=csv_bytes; report['extracted_wave_bytes']=wave_bytes
    report['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (ROOT/out).write_text(json.dumps(report,indent=2)+'\n')
    ledger=json.loads((ROOT/'ACQUISITION.json').read_text())
    if not any(x.get('operation')=='failed BL8MB first inspection' for x in ledger['scientific_byte_passes']):
        ledger['scientific_read_decoded_hash_bytes']+=35000000
        ledger['scientific_byte_passes'].append({'operation':'failed BL8MB first inspection',
            'kind':'conservative upper charge; early size guard, peak unmeasured', 'bytes':35000000})
    charge=compressed.n+decoded.n+2*(csv_bytes+wave_bytes)
    ledger['scientific_read_decoded_hash_bytes']+=charge
    ledger['scientific_byte_passes'].append({'operation':'inspect '+name,'kind':'compressed+decoded+extracted+hash','bytes':charge})
    (ROOT/'ACQUISITION.json').write_text(json.dumps(ledger,indent=2)+'\n')
    small=dict(report);small['csv_samples']=[dict(x,rows=x['rows'][:6]) for x in report['csv_samples']]
    print(json.dumps(small,indent=2))

if __name__=='__main__': main()
