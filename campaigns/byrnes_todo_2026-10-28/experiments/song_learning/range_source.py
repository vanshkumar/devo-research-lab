"""Bounded public ZIP member streaming via HTTP206; no workbook edits."""
import pathlib,urllib.request,struct,json,zlib,hashlib,xml.etree.ElementTree as E,posixpath
H=pathlib.Path(__file__).resolve().parent;C=H.parents[1];D=C/'data/song_learning/fig2_members';D.mkdir(parents=True,exist_ok=True)
URL='https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-025-08729-1/MediaObjects/41586_2025_8729_MOESM4_ESM.xlsx';SIZE=72690975;requests=[]
def get(a,b):
 req=urllib.request.Request(URL,headers={'Range':f'bytes={a}-{b}'})
 with urllib.request.urlopen(req,timeout=30) as r:
  assert r.status==206,('Range ignored',r.status)
  data=r.read(b-a+2);assert len(data)==b-a+1
  requests.append(dict(start=a,end=b,bytes=len(data),etag=r.headers.get('ETag'),last_modified=r.headers.get('Last-Modified'),sha256=hashlib.sha256(data).hexdigest()))
  assert sum(x['bytes'] for x in requests)<4_000_000
 return data
tail_start=SIZE-131072;tail=get(tail_start,SIZE-1);eocd=tail.rfind(b'PK\x05\x06');eo=struct.unpack_from('<4s4H2IH',tail,eocd);cd_size,cd_off=eo[5:7]
cd=tail[cd_off-tail_start:cd_off-tail_start+cd_size];entries={};pos=0
while pos<len(cd):
 q=struct.unpack_from('<4s6H3I5H2I',cd,pos);assert q[0]==b'PK\x01\x02';fnlen,extra,comment=q[10:13];name=cd[pos+46:pos+46+fnlen].decode();entries[name]=dict(method=q[4],crc=q[7],compressed=q[8],uncompressed=q[9],offset=q[-1]);pos+=46+fnlen+extra+comment
(D/'zip_directory.json').write_text(json.dumps(entries,indent=2)+'\n')
def member(name):
 out=D/name.replace('/','__')
 if out.exists():
  data=out.read_bytes();e=entries[name];assert len(data)==e['uncompressed'] and zlib.crc32(data)&0xffffffff==e['crc'];return data
 e=entries[name];assert e['compressed']<3_500_000,('Member too large',name,e)
 hdr=get(e['offset'],e['offset']+29);local=struct.unpack('<4s5H3I2H',hdr);start=e['offset']+30+local[-2]+local[-1];raw=get(start,start+e['compressed']-1);data=zlib.decompress(raw,-15) if e['method']==8 else raw;assert len(data)==e['uncompressed'] and zlib.crc32(data)&0xffffffff==e['crc'];out.write_bytes(data);return data
book=E.fromstring(member('xl/workbook.xml'));ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'};rels=E.fromstring(member('xl/_rels/workbook.xml.rels'));rd={q.attrib['Id']:q.attrib['Target'] for q in rels};sheets={}
for sh in book.findall('s:sheets/s:sheet',ns):
 target=rd[sh.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']];target=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target);sheets[sh.attrib['name']]=target
print('SHEETS',json.dumps({n:dict(path=p,**entries[p]) for n,p in sheets.items()},indent=2))
# Fetch only the preselected source scalar panel plus decile traces if small enough.
selected={n:p for n,p in sheets.items() if n.startswith('g.') or n.startswith('f.')}
for n,p in selected.items():
 if entries[p]['compressed']<3_500_000:member(p)
 else:print('SKIP_LARGE',n,entries[p]['compressed'])
(D/'sheet_map.json').write_text(json.dumps(sheets,indent=2)+'\n');(D/'range_manifest.json').write_text(json.dumps(dict(url=URL,total_source_bytes=SIZE,requests=requests,bytes_downloaded=sum(x['bytes'] for x in requests)),indent=2)+'\n');print('downloaded',sum(x['bytes'] for x in requests))
