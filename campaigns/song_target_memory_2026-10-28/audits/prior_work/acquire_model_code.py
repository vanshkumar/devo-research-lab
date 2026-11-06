"""Acquire selected public ZIP members via HTTP206, not the 52MB whole archive."""
import urllib.request,struct,zipfile,io,json,pathlib,hashlib,zlib
ROOT=pathlib.Path(__file__).resolve().parents[2]/'inputs'/'prior_work'
URL='https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-020-18732-x/MediaObjects/41467_2020_18732_MOESM5_ESM.zip'
TOTAL=52620152
manifest={'url':URL,'size':TOTAL,'date':'2026-10-28','initial_capped_attempt_bytes':12000001,'ranges':[],'members':[]}
def fetch(start,end):
 req=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}'})
 with urllib.request.urlopen(req,timeout=30) as r:
  data=r.read(end-start+2)
  assert r.status==206,(r.status,dict(r.headers))
  assert len(data)==end-start+1,(len(data),end-start+1)
  manifest['ranges'].append({'start':start,'end':end,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'headers':dict(r.headers)})
  return data
start=TOTAL-65557;tail=fetch(start,TOTAL-1);idx=tail.rfind(b'PK\x05\x06');e=struct.unpack('<4s4H2LH',tail[idx:idx+22]);cdsize,cdstart=e[5],e[6]
central=fetch(cdstart,cdstart+cdsize-1);(ROOT/'mackevicius_zip_central.bin').write_bytes(central)
z=zipfile.ZipFile(io.BytesIO(central+tail[idx:])); infos=z.infolist()
info_list=[{'name':i.filename,'size':i.file_size,'compressed':i.compress_size,'offset':i.header_offset+cdstart,'crc':i.CRC,'method':i.compress_type} for i in infos]
(ROOT/'mackevicius_zip_directory.json').write_text(json.dumps(info_list,indent=2))
print(json.dumps(info_list,indent=2),flush=True)
for item in info_list:
 name=item['name']
 if '__MACOSX' in name or not (name.endswith('.m') or name.endswith('.txt') or name.endswith('.md')): continue
 assert item['compressed']<1000000,item
 local=fetch(item['offset'],item['offset']+29);h=struct.unpack('<4s5H3L2H',local);assert h[0]==b'PK\x03\x04'
 payload_start=item['offset']+30+h[-2]+h[-1]
 raw=fetch(payload_start,payload_start+item['compressed']-1)
 if item['method']==8: content=zlib.decompress(raw,-15)
 elif item['method']==0: content=raw
 else: raise ValueError(item['method'])
 assert len(content)==item['size'];assert zlib.crc32(content)&0xffffffff==item['crc']
 target=ROOT/'mackevicius_code'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
 manifest['members'].append(dict(item,sha256=hashlib.sha256(content).hexdigest()))
(ROOT/'mackevicius_range_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Saved',len(manifest['members']),'code/text files; downloaded',sum(i['bytes'] for i in manifest['ranges']),'range bytes')
