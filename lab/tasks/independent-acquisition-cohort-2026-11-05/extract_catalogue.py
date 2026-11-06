"""Extract ONLY sessions/datasets from pinned partial ZIP, never QC.json."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import resource
import struct
import time
import zipfile
import zlib

HERE = Path(__file__).resolve().parent
cpu, wall = time.process_time(), time.monotonic()
tail = (HERE/'GLOBAL_ZIP_TAIL.bin').read_bytes()
prefix = (HERE/'GLOBAL_CATALOGUE_PREFIX.bin').read_bytes()
requests = [json.loads(x) for x in (HERE/'PUBLIC_REQUESTS.jsonl').read_text().splitlines()]
rr = [next(r for r in reversed(requests) if r['local']==s and r.get('status')==206)
      for s in ('GLOBAL_ZIP_TAIL.bin','GLOBAL_CATALOGUE_PREFIX.bin')]
assert rr[0]['response_headers']['ETag'] == rr[1]['response_headers']['ETag']
total = int(rr[0]['response_headers']['Content-Range'].split('/')[-1])
out = []
with zipfile.ZipFile(io.BytesIO(tail)) as z:
    infos = z.infolist()
    for info in infos:
        offset = info.header_offset + total - len(tail)
        out.append(dict(name=info.filename,offset=offset,compressed_bytes=info.compress_size,
                        decoded_bytes=info.file_size,compression=info.compress_type,crc32=info.CRC))
        if info.filename not in ('sessions.pqt','datasets.pqt'):
            continue
        hdr = struct.unpack_from('<4s5H3I2H',prefix,offset)
        assert hdr[0]==b'PK\x03\x04' and hdr[3]==8
        a = offset+30+hdr[-2]+hdr[-1]
        b = a+info.compress_size
        assert b<=len(prefix)
        raw = zlib.decompress(prefix[a:b],-15)
        assert len(raw)==info.file_size and zlib.crc32(raw)==info.CRC
        (HERE/('GLOBAL_'+info.filename)).write_bytes(raw)
        out[-1]['sha256'] = hashlib.sha256(raw).hexdigest()
    qc = next(r for r in out if r['name']=='QC.json')
    assert len(prefix)==qc['offset']
record = dict(utc=datetime.now(timezone.utc).isoformat(),source='https://ibl-brain-wide-map-public.s3.amazonaws.com/caches/openalyx/cache.zip',
              archive_bytes=total,etag=rr[0]['response_headers']['ETag'],entries=out,
              excluded='QC.json is not acquired in full or decoded; tail includes only an opaque end fragment from compressed cache_info.json plus central metadata. No trial data.',
              explicit_read_bytes=len(tail)+len(prefix)+(HERE/'PUBLIC_REQUESTS.jsonl').stat().st_size,
              decoded_metadata_bytes=sum(r['decoded_bytes'] for r in out if 'sha256' in r),
              cpu_seconds=time.process_time()-cpu,process_wall_seconds=time.monotonic()-wall,
              peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(HERE/'CATALOGUE_EXTRACTION.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
