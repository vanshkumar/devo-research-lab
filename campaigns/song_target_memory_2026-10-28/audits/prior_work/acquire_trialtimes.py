import urllib.request,pathlib,json,struct,hashlib,zlib
root=pathlib.Path(__file__).resolve().parents[2]/'inputs'/'prior_work'
url=json.loads((root/'mackevicius_range_manifest.json').read_text())['url']
item=next(i for i in json.loads((root/'mackevicius_zip_directory.json').read_text()) if i['name'].endswith('/trialTimes.mat') and '__MACOSX' not in i['name'])
ranges=[]
def get(a,b):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'Range':f'bytes={a}-{b}'}),timeout=30) as r:
  data=r.read(b-a+2);assert r.status==206;assert len(data)==b-a+1
  ranges.append({'start':a,'end':b,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'headers':dict(r.headers)});return data
h=struct.unpack('<4s5H3L2H',get(item['offset'],item['offset']+29));s=item['offset']+30+h[-2]+h[-1]
data=zlib.decompress(get(s,s+item['compressed']-1),-15);assert len(data)==item['size'];assert zlib.crc32(data)&0xffffffff==item['crc']
out=root/'mackevicius_code'/item['name'];out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
(root/'trialtimes_manifest.json').write_text(json.dumps({'url':url,'date':'2026-10-28','member':dict(item,sha256=hashlib.sha256(data).hexdigest()),'ranges':ranges},indent=2))
print(out,len(data))
