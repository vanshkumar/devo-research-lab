"""Bounded, source-specific public metadata/range acquisition; no pickle execution."""
import argparse, datetime, hashlib, io, json, pathlib, resource, struct, time, urllib.request, zipfile, zlib

ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / 'source'
SOURCE.mkdir(exist_ok=True)
LOG = ROOT / 'ACQUISITION.json'

def fetch(url, name, cap, range_header=None):
    prior = json.loads(LOG.read_text()) if LOG.exists() else []
    item = {'url': url, 'name': name, 'cap': cap, 'range': range_header,
            'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    headers = {'User-Agent': 'independent-research-source-audit/1.0', 'Accept-Encoding': 'identity'}
    if range_header:
        headers['Range'] = range_header
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=35) as r:
            item.update(status=r.status, headers=dict(r.headers), final_url=r.url)
            body = r.read(cap + 1)
            item['bytes_read'] = len(body)
            if len(body) > cap:
                raise ValueError('Response exceeded explicit cap')
            if range_header and r.status != 206:
                raise ValueError('Server did not honor byte range; no full download accepted')
        (SOURCE / name).write_bytes(body)
        item['sha256'] = hashlib.sha256(body).hexdigest()
        item['saved'] = True
    except Exception as e:
        item.update(error=repr(e), saved=False)
        raise
    finally:
        item['finished_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        item['process_peak_rss_bytes_macos'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        prior.append(item)
        LOG.write_text(json.dumps(prior, indent=2) + '\n')
    return body

def metadata():
    raw = fetch('https://zenodo.org/api/records/5545872', 'zenodo_metadata.json', 250000)
    j = json.loads(raw)
    print(json.dumps({'id':j['id'], 'files':j['files'], 'license':j['metadata'].get('license')}, indent=2))

def social_metadata():
    raw=fetch('https://data.mendeley.com/public-api/datasets/63db6zc5fm/versions/2', 'social_metadata.json', 500000)
    j=json.loads(raw)
    print(json.dumps(j,indent=2))

def social_page():
    raw=fetch('https://data.mendeley.com/datasets/63db6zc5fm/2', 'social_page.html', 1500000)
    text=raw.decode('utf-8')
    import re
    for needle in ('download_url','downloadUrl','files','__NEXT_DATA__','INITIAL_STATE','public-api'):
        k=text.find(needle)
        print(needle,k,text[max(0,k-150):k+1200] if k>=0 else '')

def social_files():
    raw=fetch('https://data.mendeley.com/public-api/datasets/63db6zc5fm/files?folder_id=root&version=2', 'social_files.json', 500000)
    print(raw.decode('utf-8'))

def social_table():
    info=json.loads((SOURCE/'social_files.json').read_text())[0]
    detail=info['content_details'];assert detail['size']==33918
    body=fetch(detail['download_url'], 'Supplementary Data 1.xlsx', 33918)
    assert hashlib.sha256(body).hexdigest()==detail['sha256_hash']
    print(json.dumps({'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'declared_sha_agrees':True}))

def directory():
    j = json.loads((SOURCE / 'zenodo_metadata.json').read_text())
    f = j['files'][0]
    url = f['links']['self']
    n = f['size']
    tail_start = max(0, n - 262144)
    body = fetch(url, 'zip_tail.bin', 262144, f'bytes={tail_start}-{n-1}')
    end = body.rfind(b'PK\x05\x06')
    assert end >= 0
    e = struct.unpack('<4s4H2LH', body[end:end+22])
    entries, cd_size, cd_offset = e[4], e[5], e[6]
    assert cd_offset >= tail_start, 'Central directory exceeds the acquired tail; stop for explicit planning'
    cd = body[cd_offset-tail_start:cd_offset-tail_start+cd_size]
    items=[]; pos=0
    while pos < len(cd):
        vals=struct.unpack('<4s6H3L5H2L', cd[pos:pos+46])
        assert vals[0] == b'PK\x01\x02'
        name_len, extra_len, comment_len = vals[10:13]
        name=cd[pos+46:pos+46+name_len].decode('utf-8')
        items.append({'path':name,'method':vals[4],'crc32':vals[7], 'compressed_size':vals[8],
                      'uncompressed_size':vals[9], 'local_offset':vals[16]})
        pos += 46+name_len+extra_len+comment_len
    assert len(items)==entries
    out={'url':url,'size':n,'declared_checksum':f.get('checksum'), 'entries':items,
         'tail_start':tail_start,'central_offset':cd_offset,'central_size':cd_size}
    (SOURCE/'zip_directory.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'size':n,'entries':len(items),'selected_candidates':[x for x in items if '/files/' in x['path'] or 'README' in x['path']]},indent=2))

def member(path):
    j=json.loads((SOURCE/'zip_directory.json').read_text())
    m=next(x for x in j['entries'] if x['path']==path)
    assert m['uncompressed_size'] <= 70000000
    assert m['compressed_size'] <= 15000000
    start=m['local_offset']
    # Extra header and filename allowance; last requested bytes may include the following member.
    end=min(j['size']-1,start+30+len(path.encode())+4096+m['compressed_size']-1)
    name=path.rsplit('/',1)[-1]
    raw=fetch(j['url'], name+'.range', end-start+1, f'bytes={start}-{end}')
    v=struct.unpack('<4s5H3L2H',raw[:30]); assert v[0]==b'PK\x03\x04'
    off=30+v[-2]+v[-1]
    assert raw[30:30+v[-2]].decode()==path
    compressed=raw[off:off+m['compressed_size']]
    assert len(compressed)==m['compressed_size']
    decoded=zlib.decompress(compressed,-15) if m['method']==8 else compressed
    assert len(decoded)==m['uncompressed_size']
    assert (zlib.crc32(decoded)&0xffffffff)==m['crc32']
    (SOURCE/name).write_bytes(decoded)
    pin={'path':path,'decoded_bytes':len(decoded),'compressed_sha256':hashlib.sha256(compressed).hexdigest(),
         'sha256':hashlib.sha256(decoded).hexdigest(),'crc32':m['crc32'],
         'note':'Member CRC and range hashes verified; whole archive MD5 not verified.',
         'process_peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (SOURCE/(name+'.pin.json')).write_text(json.dumps(pin,indent=2)+'\n')
    print(json.dumps(pin,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['metadata','directory','member','social_metadata','social_page','social_files','social_table']);p.add_argument('path',nargs='?');a=p.parse_args()
    if a.mode=='member':member(a.path)
    elif a.mode=='social_metadata':social_metadata()
    elif a.mode=='social_page':social_page()
    elif a.mode=='social_files':social_files()
    elif a.mode=='social_table':social_table()
    elif a.mode=='directory':directory()
    else:metadata()
