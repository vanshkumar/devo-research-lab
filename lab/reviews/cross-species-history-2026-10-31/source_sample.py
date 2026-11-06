"""Bounded original-source checks for exact manifest-admitted consumed rows."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
from pathlib import Path
import csv,io,json,hashlib,resource,datetime,importlib.util
import numpy as np
HERE=Path(__file__).resolve().parent;AUTHOR=HERE.parents[1]/'tasks'/HERE.name;ROOT=HERE.parents[2]

def main():
    manifest=json.loads((AUTHOR/'ALLOWED_MANIFEST.json').read_text());selection=json.loads((HERE/'SOURCE_SELECTION.json').read_text())
    human=selection['human_samples'][0];mouse=selection['mouse_sample']
    assert human['species']=='human' and human['allowed_rows']==[0,600]
    assert mouse['species']=='mouse' and mouse['allowed_rows']==[0,402] and mouse['indexed_total_rows']==402
    assert mouse['full_payload_previously_consumed']
    source=ROOT/human['source_path'];assert source.stat().st_size==134562545
    # The prior source audit certifies this exact object as the 80 admitted
    # complete 600-row sessions; full hash is read without interpreting fields.
    hasher=hashlib.sha256();hashed=0
    with source.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):hasher.update(b);hashed+=len(b)
    assert hasher.hexdigest()==human['source_sha256']
    columns=('subject','session','trial','probabilityLeft','contrastLeft','contrastRight','choice','feedbackType','instructions')
    records=[];csv.field_size_limit(10000000)
    with source.open('rb') as raw:
        with io.TextIOWrapper(raw,newline='') as text:
            reader=csv.DictReader(text)
            assert set(columns)<=set(reader.fieldnames)
            for i,r in enumerate(reader):
                assert r['subject'].zfill(3)==human['subject'] and r['session']==human['session']
                assert int(float(r['trial']))==i
                assert i<human['allowed_rows'][1]
                records.append({k:r[k] for k in columns})
                if i==599:break
            sampled_bytes=raw.tell()
    assert len(records)==600
    check=json.loads((HERE/'RECONSTRUCTION.json').read_text())
    indices={r['subject']:r['unit'] for r in check['per_unit_checks']}
    inputpath=AUTHOR/'consumed_inputs.npz';decoded=0
    with np.load(inputpath,allow_pickle=False) as z:
        needed=('contrast','choice','feedback','probabilityLeft','session','session_start','session_trial','trial','prev_choice')
        cache={sid:{k:z[str(indices[sid])+'__'+k] for k in needed} for sid in (human['subject'],mouse['subject'])}
        decoded+=sum(a.nbytes for d in cache.values() for a in d.values())
    def number(s):return float(s) if s!='' else np.nan
    original={k:np.array([number(r[k]) for r in records]) for k in columns if k not in ('subject','session')}
    decoded+=sum(a.nbytes for a in original.values())
    hc=cache[human['subject']]
    hx=np.nan_to_num(original['contrastLeft'])-np.nan_to_num(original['contrastRight'])
    human_errors={k:float(np.max(abs(a-hc[k]))) for k,a in [('contrast',hx),('choice',original['choice']),('feedback',np.nan_to_num(original['feedbackType'])),('probabilityLeft',original['probabilityLeft']),('trial',original['trial'])]}
    assert max(human_errors.values())==0
    assert np.all(original['instructions']==int(human['condition']))
    npzpath=ROOT/mouse['path'];payload=npzpath.read_bytes()
    assert hashlib.sha256(payload).hexdigest()==mouse['expected_sha256']
    with np.load(io.BytesIO(payload),allow_pickle=False) as z:
        md=json.loads(str(z['metadata_json']));marrays={k:z[k] for k in ('contrastLeft','contrastRight','choice','feedbackType','probabilityLeft','session_index','session_start','repNum')}
    decoded+=sum(a.nbytes for a in marrays.values())
    link=mouse['source_rows'][0]
    assert link['rows']==[0,402] and link['global_start']==0 and link['full_rows']==402
    assert all(md['sessions'][0][k]==link[k] for k in ('date','number','eid','dataset_id'))
    pqtpath=ROOT/link['path'];pqtbytes=pqtpath.read_bytes()
    libraries={k:importlib.util.find_spec(k) is not None for k in ('pyarrow','fastparquet','duckdb')}
    raw_to_npz=None
    if libraries['pyarrow']:
        import pyarrow.parquet as pq
        table=pq.read_table(io.BytesIO(pqtbytes),columns=['contrastLeft','contrastRight','choice','feedbackType','probabilityLeft','repNum'])
        assert table.num_rows==402
        rawmouse={k:table[k].to_numpy() for k in table.column_names};decoded+=sum(a.nbytes for a in rawmouse.values())
        raw_to_npz={k:bool(np.all((a==marrays[k]) | (np.isnan(a)&np.isnan(marrays[k])))) for k,a in rawmouse.items()}
        assert all(raw_to_npz.values())
    else:
        rawmouse=marrays
    mc=cache[mouse['subject']]
    mx=np.nan_to_num(rawmouse['contrastLeft'])-np.nan_to_num(rawmouse['contrastRight'])
    mouse_errors={k:float(np.max(abs(a-mc[k]))) for k,a in [('contrast',mx),('choice',rawmouse['choice']),('feedback',np.nan_to_num(rawmouse['feedbackType'])),('probabilityLeft',rawmouse['probabilityLeft']),('trial',np.arange(402))]}
    assert max(mouse_errors.values())==0
    report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),human=dict(subject=human['subject'],session=human['session'],rows=600,source_path=human['source_path'],source_bytes=source.stat().st_size,whole_source_sha256=hasher.hexdigest(),expected_hash_matches=True,full_source_numeric_reconstruction=False,sampled_raw_bytes=sampled_bytes,errors_to_cache=human_errors,scope='Fresh original CSV check of one admitted 600-row session; other 79 human sessions retain inherited original-source extraction.'),mouse=dict(subject=mouse['subject'],rows=402,npz_path=mouse['path'],npz_sha256=hashlib.sha256(payload).hexdigest(),old_exposure_pin_matches=True,raw_parquet_path=link['path'],raw_parquet_sha256=hashlib.sha256(pqtbytes).hexdigest(),parquet_decoder_libraries=libraries,raw_to_npz_equal=raw_to_npz,errors_from_pinned_npz_to_cache=mouse_errors,session_link_matches=True,scope='One full 402-row admitted first session; pinned NPZ decoded and compared. Parquet numeric comparison only if raw_to_npz_equal is non-null. No new/later rows or other mouse originals.'),resource=dict(read_file_bytes=hashed+sampled_bytes+len(payload)+len(pqtbytes)+inputpath.stat().st_size+(AUTHOR/'ALLOWED_MANIFEST.json').stat().st_size+(HERE/'SOURCE_SELECTION.json').stat().st_size+(HERE/'RECONSTRUCTION.json').stat().st_size,decoded_array_bytes=decoded,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),protected_reads=0,new_subjects=0)
    (HERE/'SOURCE_SAMPLE.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
