"""Offline pins and finite resource/exposure closeout; no network or science fits."""
import hashlib,json,resource,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
operations=json.loads((ROOT/'OPERATIONS.json').read_text())
acqs=[json.loads(x) for x in (ROOT/'ACQUISITIONS.jsonl').read_text().splitlines()]
source_names=['task_tree.json','REMOTE.md','remote_tutorial.ipynb','zarr.json','nwb_metadata.json','reward_time.blosc']
source_urls={r['path']:r['url'] for r in acqs if r['status']==200}
source_urls['task_tree.json']='https://api.github.com/repos/samgale/DynamicRoutingTask/git/trees/main?recursive=1'
source_urls['REMOTE.md']='https://raw.githubusercontent.com/AllenNeuralDynamics/conect-dev-capsule/main/REMOTE.md'
source_records=[]
pin_read=0
for name in source_names:
    b=(ROOT/name).read_bytes(); pin_read+=2*len(b)
    source_records.append({'path':name,'url':source_urls[name],'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
manifest={'sources':source_records,'source_access':'Public anonymous HTTP/GitHub; no credentials used',
          'data_license':'UNCERTIFIED; no license inferred from public accessibility or repository code license',
          'versioning':'S3 version IDs/ETags/Last-Modified recorded in ACQUISITIONS.jsonl; exact fetched tree SHA in task_tree.json; tutorial pinned by fetched content hash, no commit pin',
          'task_deployment_provenance':'UNRUN; source tree not deployed task certification'}
(ROOT/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
resources={
    'completed_utc':now,'start_utc':'2026-11-01T03:04:30.388Z',
    'source_stop_utc':'2026-11-01T03:24:30.388Z','absolute_deadline_utc':'2026-11-01T04:19:30.388Z',
    'stop_reason':'12/12 public operations reached before full source certification; no automatic continuation',
    'public_operations':len(operations['operations']),'public_operations_limit':12,
    'exact_direct_http_ingress_bytes':sum(r['bytes'] for r in acqs),
    'accounted_ingress_charge_bytes':sum(r['ingress_charge_bytes'] for r in operations['operations']),
    'ingress_limit_bytes':50000000,'provider_ingress_bytes':'UNKNOWN; explicit operation reserves are accounting charges, not provider transfer measurements',
    'additional_scientific_read_decode_hash_charge_bytes':50000000,'additional_read_limit_bytes':500000000,
    'read_accounting':'Conservative task charge includes all owned-source/code/JSON/decoded/hash reads, repeated/failed inspections, and closeout. Not an OS byte meter. Process-local data payloads are only the files in SOURCE_MANIFEST.',
    'closeout_source_read_hash_bytes':pin_read,
    'largest_measured_local_rss_bytes':max([25411584]+[r['rss_bytes'] for r in acqs]+[resource.getrusage(resource.RUSAGE_SELF).ru_maxrss]),
    'rss_limit_bytes':1000000000,'remote_provider_peak_rss':'UNKNOWN','failed_connector_peak_rss':'UNKNOWN',
    'concurrency':'one scientific process at a time; one numerical thread; standard-library code only; no workers/subagents/background jobs',
    'jobs_running':0,'packages_installed':[],
    'failures':'See OPERATIONS.json and ACQUISITIONS.jsonl, including pre-execution guard denials, connector failure and DNS failure. No failure erased.',
    'exposure':{'actual_data':'742903_2024-10-22 complete 538-row reward_time vector consumed; 136finite/402NaN',
                'metadata':'all fetched NWB consolidated metadata including non-trial array schemas; no non-trial array payloads',
                'tutorial':'entire JSON decoded including embedded PNG strings; source/output text/MIME inventory inspected; PNG images not visually inspected',
                'summary':'five Allen session performance/methods summaries from public search; source tree metadata',
                'unacquired':'all stimulus/response/block/instruction/reward-type/opto/repeat arrays; all other animals actual trial arrays; NWB subject/session scalar values',
                'protected_and_old_raw':'NONE; inherited lab protections unchanged'},
    'science_status':'PARTIAL_SOURCE_CHECK_ONLY; split/freeze/models/controls/forecasts/scoring/uncertainty/independent_review UNRUN'
}
(ROOT/'RESOURCES.json').write_text(json.dumps(resources,indent=2)+'\n')
pins={}
for f in sorted(ROOT.iterdir()):
    if f.is_file() and f.name not in ['ARTIFACT_PINS.json','COMMUNICATION_STATUS.json']:
        b=f.read_bytes();pins[f.name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
(ROOT/'ARTIFACT_PINS.json').write_text(json.dumps(pins,indent=2)+'\n')
assert resources['public_operations']==12
assert resources['exact_direct_http_ingress_bytes']==2374916
assert resources['accounted_ingress_charge_bytes']<resources['ingress_limit_bytes']
assert resources['additional_scientific_read_decode_hash_charge_bytes']<resources['additional_read_limit_bytes']
print(json.dumps(resources,indent=2))
