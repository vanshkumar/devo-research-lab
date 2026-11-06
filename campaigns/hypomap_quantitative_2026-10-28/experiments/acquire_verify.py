"""Verify preserved range bytes, prior metadata, and exported sparse subset integrity."""
from pathlib import Path
import json,hashlib,sys,platform
import numpy as np,pandas as pd,scipy,h5py,requests
from scipy.sparse import load_npz
ROOT=Path(__file__).resolve().parents[1]; INPUT=ROOT/'inputs'; CACHE=INPUT/'range_cache'
records=[]; etags=set(); sizes=set(); versions=set()
for p in sorted(CACHE.glob('*.bin')):
    m=json.loads(p.with_suffix('.json').read_text()); b=p.read_bytes()
    assert len(b)==m['size']==m['end']-m['start']+1
    assert hashlib.sha256(b).hexdigest()==m['sha256']
    assert m['status']==206
    headers={k.lower():v for k,v in m['headers'].items()}
    assert headers['content-range']==f"bytes {m['start']}-{m['end']}/5231283640"
    etags.add(headers.get('etag')); versions.add(headers.get('x-amz-version-id'))
    records.append({'file':str(p.relative_to(ROOT)),'start':m['start'],'end':m['end'],'bytes':m['size'],'sha256':m['sha256']})
assert len(etags)==1 and len(versions)==1
prior=ROOT.parents[1]/'sources'/'research_review_2026-10-28'
old=json.loads((prior/'HYPOMAP_METADATA_MANIFEST.json').read_text()); overlap=[]
for entry in old['subsets']:
    p=prior/entry['file']; oldbytes=p.read_bytes(); start=entry['range_start_inclusive']; end=entry['range_end_inclusive']; rebuilt=[]; cursor=start
    assert hashlib.sha256(oldbytes).hexdigest()==entry['sha256']
    while cursor<=end:
        chunkstart=cursor//1048576*1048576; chunkend=min(5231283640,chunkstart+1048576)-1
        b=(CACHE/f'{chunkstart:012d}-{chunkend:012d}.bin').read_bytes(); take=min(end-cursor+1,len(b)-(cursor-chunkstart)); rebuilt.append(b[cursor-chunkstart:cursor-chunkstart+take]); cursor+=take
    assert b''.join(rebuilt)==oldbytes
    overlap.append({'file':entry['file'],'bytes':len(oldbytes),'match':True})
obs=pd.read_csv(INPUT/'selected_obs.csv'); peptideobs=pd.read_csv(INPUT/'peptide_obs.csv'); a=load_npz(INPUT/'selected_counts.npz'); b=load_npz(INPUT/'peptide_counts.npz')
ix=pd.Index(obs.row_index).get_indexer(peptideobs.row_index); assert np.all(ix>=0)
assert (a[ix]!=b).nnz==0
assert np.array_equal(np.asarray(a.sum(axis=1)).ravel(),obs.raw_total)
assert np.array_equal(np.diff(a.indptr),obs.raw_nfeature)
assert obs.row_index.is_unique and obs['_index'].is_unique
assert a.has_canonical_format and b.has_canonical_format
versions_python={'Python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'h5py':h5py.__version__,'HDF5':h5py.version.hdf5_version,'requests':requests.__version__}
failures=[]
for line in (ROOT/'logs'/'acquire_ranges.jsonl').read_text().splitlines():
    r=json.loads(line)
    if 'error' in r: failures.append(r)
manifest={'asset_url':old['asset_url'],'dataset_id':old['dataset_id'],'dataset_version':old['dataset_version'],'collection_version':old['collection_version'],'whole_file_bytes':5231283640,'whole_file_sha256':None,'range_count':len(records),'downloaded_range_bytes':sum(r['bytes'] for r in records),'ETag':list(etags),'x_amz_version_id':list(versions),'ranges':records,'prior_metadata_byte_comparison':overlap,'prior_metadata_bytes_compared':sum(r['bytes'] for r in overlap),'protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest(),'software':versions_python,'selection':'selection_manifest.json','extractions':['peptide_extraction_manifest.json','selected_extraction_manifest.json'],'byte_read_failures':failures,'subset_consistency':{'all_1476_peptide_rows_identical_in_selected_matrix':True,'actual_row_sums_match_exported_raw_total':True,'row_nonzero_counts_match_raw_nfeature':True,'unique_barcodes':True,'canonical_CSR':True}}
(INPUT/'acquisition_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({k:v for k,v in manifest.items() if k not in ['ranges','byte_read_failures']},indent=2))
