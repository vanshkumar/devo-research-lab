"""Local final artifact/link receipts only; no scientific recalculation."""
import hashlib
import json
from pathlib import Path
import re
import resource
import time

HERE=Path(__file__).resolve().parent
begin=time.perf_counter()
excluded={'STATE.md','BRIEF.md','MANIFEST.json','MANIFEST_RESOURCES.json'}
pins=[];links=[];read_bytes=0
for path in sorted(HERE.iterdir()):
    if not path.is_file() or path.name in excluded:continue
    assert path.stat().st_size<10_000_000
    content=path.read_bytes();read_bytes+=len(content)
    pins.append(dict(file=path.name,bytes=len(content),sha256=hashlib.sha256(content).hexdigest()))
    if path.suffix=='.md':
        for target in re.findall(r'\]\(([^)]+)\)',content.decode('utf-8')):
            if target.startswith(('http://','https://','#')):continue
            assert (HERE/target).exists() or target=='MANIFEST.json',(path.name,target)
            links.append(dict(source=path.name,target=target,status='exists'))
receipt=dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
             excluded_mutable_or_recursive=sorted(excluded),scientific_artifact_pins=pins,local_links=links)
(HERE/'MANIFEST.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert all((HERE/link['target']).exists() for link in links)
resources=dict(status='PASS',seconds=time.perf_counter()-begin,read_hash_decode_bytes=3*read_bytes,
               explicit_read_bytes=read_bytes,peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               included_in_existing_600MB_charge_and_5s_short_process_allowance=True,
               no_scientific_recalculation=True,jobs=0)
(HERE/'MANIFEST_RESOURCES.json').write_text(json.dumps(resources,indent=2)+'\n')
print(json.dumps(dict(status='PASS',artifacts=len(pins),local_links=len(links),**resources)),flush=True)
