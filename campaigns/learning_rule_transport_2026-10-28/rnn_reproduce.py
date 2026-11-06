#!/usr/bin/env python3
"""Offline replay of ALL48 frozen RNN source forecasts from original prefixes.

Actual source outcomes are selected only for the first1000task rows. Realized
future opportunities come only from pinned Parquet footer counts. Saved files
opened for comparison contain model-generated forecasts, not observed future
choices/rewards. The external cohort is never opened or decoded.
"""
import argparse,csv,datetime as dt,hashlib,http.client,importlib.metadata,json,socket,sys,time,urllib.request
from pathlib import Path

C=Path(__file__).resolve().parent
sys.path.insert(0,str(C/'code'))
OUT=C/'artifacts/rnn/offline_reproduction'
RNN_FREEZE=C/'protocols/RNN_FREEZE.json'
MODEL=C/'artifacts/rnn/rnnglm32_nested_best.npz'
CONFIG=C/'artifacts/rnn/calibration/CONFIG.json'
MODEL_NAME='rnnglm32'


def forbidden(*args,**kwargs):
    raise RuntimeError('Offline RNN reproduction forbids Python network connections')


def block_network():
    socket.create_connection=forbidden
    socket.socket.connect=forbidden
    socket.socket.connect_ex=forbidden
    urllib.request.urlopen=forbidden
    urllib.request.OpenerDirector.open=forbidden
    http.client.HTTPConnection.connect=forbidden
    http.client.HTTPSConnection.connect=forbidden


def digest(path,algorithm='sha256'):
    h=hashlib.new(algorithm)
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')


def verify_freezes(path=RNN_FREEZE,seen=None):
    seen=set() if seen is None else seen
    path=Path(path).resolve()
    if path in seen:return []
    seen.add(path);f=json.loads(path.read_text());records=[]
    for r in f['files']:
        p=C/r['path'];actual=digest(p)
        if actual!=r['sha256']:raise RuntimeError('Frozen artifact mismatch: '+r['path'])
        records.append(dict(path=r['path'],bytes=p.stat().st_size,sha256=actual))
        if r['path']=='protocols/FREEZE.json':records.extend(verify_freezes(p,seen))
    return records


def eligible_sources():
    allocation=json.loads((C/'protocols/SPLIT.json').read_text())['standard']
    counts={}
    for r in json.loads((C/'data/ROW_COUNTS.json').read_text()):
        counts[r['subject']]=counts.get(r['subject'],0)+int(r['rows'])
    result=[]
    for r in allocation:
        split=r['split']
        if split not in ('animal_holdout','lab_holdout'):continue
        total=counts.get(r['subject'],0)
        if total<1500:continue
        tag='rnn_source_animals' if split=='animal_holdout' else 'rnn_source_labs'
        folder=C/'artifacts/forecasts'/tag
        p=folder/(r['subject']+'__'+MODEL_NAME+'.npz')
        result.append(dict(subject=r['subject'],split=split,total_trials_from_footer=total,expected_horizon=min(5000,total-1000),forecast=p,metadata=p.with_suffix('.json')))
    return sorted(result,key=lambda r:(r['split'],r['subject']))


def verified_prefix_inputs(prefix_metadata,subject,index,downloads,verified):
    """Pin whole source objects as bytes; decode only allowed prefix rows."""
    paths=[];rp={r['eid']:r for r in index if r['kind']=='repNum'}
    for r in prefix_metadata['prefix_outcome_source_records']:
        paths.append(r['path'])
        if r['eid'] in rp and (C/rp[r['eid']]['path']).exists():paths.append(rp[r['eid']]['path'])
    details=[]
    bypath={r['path']:r for r in index}
    for rel in paths:
        r=bypath[rel]
        if r['cohort']!='standard' or r['subject']!=subject:raise PermissionError('Unexpected prefix source object '+rel)
        if rel not in verified:
            m=downloads[rel];p=C/rel
            sh=digest(p);md=digest(p,'md5')
            if p.stat().st_size!=m['bytes'] or sh!=m['sha256']:raise RuntimeError('Original prefix-byte pin mismatch '+rel)
            if r.get('md5') and md!=r['md5']:raise RuntimeError('Published prefix MD5 mismatch '+rel)
            verified[rel]=dict(path=rel,bytes=p.stat().st_size,sha256=sh,md5=md,published_md5=r.get('md5'))
        details.append(verified[rel])
    return details


def array_comparison(fresh,saved):
    import numpy as np
    a=np.asarray(fresh);b=np.asarray(saved)
    if a.shape!=b.shape:raise AssertionError(('array shape mismatch',a.shape,b.shape))
    same=np.array_equal(a,b,equal_nan=True)
    good=np.isfinite(a)&np.isfinite(b)
    bad_nonfinite=~good&~(np.isnan(a)&np.isnan(b))
    difference=float(np.max(np.abs(a[good].astype(float)-b[good].astype(float)),initial=0))
    if np.any(bad_nonfinite):difference=float('inf')
    return dict(exact=bool(same),shape=list(a.shape),max_abs_difference=difference,
       fresh_array_sha256=hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest(),
       saved_array_sha256=hashlib.sha256(np.ascontiguousarray(b).tobytes()).hexdigest())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default=str(OUT));p.add_argument('--require-count',type=int,default=48);p.add_argument('--no-save-replayed',action='store_true');a=p.parse_args()
    block_network();started=time.monotonic();output=Path(a.output).resolve();output.mkdir(parents=True,exist_ok=True)
    before=verify_freezes();dump(output/'FROZEN_BYTES_VERIFIED.json',before)
    jobs=eligible_sources()
    if len(jobs)!=a.require_count:raise RuntimeError(f'Footer-defined forecastable source count {len(jobs)} != required {a.require_count}')
    missing=[r['subject'] for r in jobs if not r['forecast'].is_file() or not r['metadata'].is_file()]
    if missing:
        dump(output/'RESULT.json',dict(status='not_ready',expected=len(jobs),missing=missing,source_future_outcomes_read=False,external_outcomes_read=False))
        raise SystemExit('Wait for the complete source forecast set: '+','.join(missing))
    # Imports below can make no Python network connection. All source paths
    # are local, and no acquisition/installer/fit routine is called.
    import numpy as np
    from data_io import load_prefix_and_opportunities,exposure
    from rnn_learning import load_rnn
    from rnn_rollout import autonomous
    from baselines import load_bank
    from run_forecasts import seed_for
    from uncertainty import apply_calibration
    # Defense against accidentally expanding this replay into a scoring read.
    import data_io
    def no_future_loader(*args,**kwargs):raise PermissionError('Offline RNN replay forbids full subject outcome loaders')
    data_io.load_subject=no_future_loader;data_io.prepare_subject=no_future_loader
    index=json.loads((C/'data/INDEX.json').read_text());downloads={}
    for line in (C/'data/DOWNLOAD_MANIFEST.jsonl').read_text().splitlines():
        r=json.loads(line)
        if r.get('verified'):downloads[r['path']]=r
    bank=load_bank(C/'artifacts/baselines/nested_growth_bank.npz');model=load_rnn(MODEL);model_hash=digest(MODEL)
    config=json.loads(CONFIG.read_text())
    if config['models'][MODEL_NAME]['selected_scale']!=0.:raise RuntimeError('Unexpected frozen RNN variance scale; expected0')
    rows=[];verified={};max_difference=0.;all_exact=True
    for i,j in enumerate(jobs):
        t0=time.monotonic();subject=j['subject'];meta=json.loads(j['metadata'].read_text())
        if meta['model_sha256']!=model_hash or meta['n_particles']!=512 or meta['prefix_n']!=1000:raise RuntimeError('Forecast identity mismatch '+subject)
        # This reader executes SQL LIMIT on the original first1000rows and
        # uses only pinned footer counts for every future session boundary.
        prefix,starts,pm=load_prefix_and_opportunities(subject,j['split'],prefix_n=1000,horizon=5000,freeze_path=RNN_FREEZE,
             purpose='offline frozen RNN replay: originalfirst1000prefix+footeropportunitiesonly; no future choice/reward read')
        if len(prefix['choice'])!=1000 or len(starts)!=j['expected_horizon']:raise AssertionError('Prefix/opportunity length mismatch '+subject)
        provenance=verified_prefix_inputs(pm,subject,index,downloads,verified)
        seed=seed_for(subject);fresh=autonomous(model,prefix,starts,bank,n_particles=512,seed=seed,protocol='standard',subject=subject)
        primary=apply_calibration(fresh['samples'],MODEL_NAME,seed+647,config_path=CONFIG)
        arrays=dict(samples=fresh['samples'],samples_primary=primary,weights=fresh['weights'],hidden_final=fresh['hidden_final'],counts=fresh['counts'],pool_fraction=fresh['pool_fraction'],session_start=starts,seed=np.array(seed))
        with np.load(j['forecast'],allow_pickle=False) as old:
            comparison={k:array_comparison(v,old[k]) for k,v in arrays.items()}
        exact=all(r['exact'] for r in comparison.values());difference=max(r['max_abs_difference'] for r in comparison.values())
        all_exact &=exact;max_difference=max(max_difference,difference)
        row=dict(subject=subject,split=j['split'],particles=512,prefix_n=1000,horizon=len(starts),model_sha256=model_hash,
          forecast_path=str(j['forecast'].relative_to(C)),forecast_sha256=digest(j['forecast']),metadata_sha256=digest(j['metadata']),
          seed=seed,exact=exact,max_abs_difference=difference,arrays=comparison,original_prefix_objects=provenance,
          prefix_rows_per_session=[r['prefix_rows_read'] for r in pm['prefix_outcome_source_records']],
          opportunity_source='pinned footer counts only',future_outcomes_read=False,external_outcomes_read=False,seconds=time.monotonic()-t0)
        rows.append(row);dump(output/'records'/(subject+'.json'),row);dump(output/'FORECAST_REPLAY.json',rows)
        if not a.no_save_replayed:np.savez_compressed(output/'records'/(subject+'__replayed.npz'),**arrays)
        print(json.dumps(dict(subject=subject,index=i+1,total=len(jobs),exact=exact,max_abs_difference=difference,seconds=round(time.monotonic()-t0,3))),flush=True)
    after=verify_freezes()
    if before!=after:raise RuntimeError('Frozen artifacts changed during offline replay')
    dump(output/'ORIGINAL_PREFIX_BYTES_VERIFIED.json',list(verified.values()))
    with open(output/'FORECAST_REPLAY.csv','w') as f:
        names=['subject','split','particles','prefix_n','horizon','seed','exact','max_abs_difference','forecast_sha256','seconds']
        writer=csv.DictWriter(f,fieldnames=names,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    result=dict(status='passed' if all_exact and max_difference==0 else 'FAILED',utc=dt.datetime.now(dt.timezone.utc).isoformat(),
       scope='ALL frozen RNN source forecasts from original first1000rows + pinnedfooteropportunities; no future outcome scoring',
       source_subjects=len(rows),forecasts_replayed=len(rows),particles=512,max_abs_difference=max_difference,all_arrays_exact=all_exact,
       compared_arrays=list(rows[0]['arrays']),model_sha256=model_hash,original_freeze_sha256=digest(C/'protocols/FREEZE.json'),
       rnn_freeze_sha256=digest(RNN_FREEZE),config_sha256=digest(CONFIG),original_prefix_objects_verified=len(verified),
       original_prefix_bytes_verified=sum(r['bytes'] for r in verified.values()),whole_objects_hashed_as_bytes_only=True,
       source_outcome_rows_selected_per_animal=[0,1000],source_future_outcomes_read=False,external_files_opened=False,external_outcomes_read=False,
       full_subject_loaders_disabled=True,python_network_entrypoints_disabled=True,network_calls_attempted=False,
       python=sys.version,libraries={k:importlib.metadata.version(k) for k in ['numpy','scipy','numba']},seconds=time.monotonic()-started,
       scientific_scope='Deterministic computational replay of frozen simulator; independent empirical statistics are a separate reconstruction.')
    dump(output/'RESULT.json',result)
    exposure(dict(event='offline_RNN_source_forecasts_replayed',source_subjects=[r['subject'] for r in rows],forecasts=len(rows),particles=512,
      max_abs_difference=max_difference,source_outcome_interval=[0,1000],future_outcomes_read=False,external_outcomes_read=False,network_calls=False,
      rnn_freeze_sha256=digest(RNN_FREEZE)))
    print(json.dumps(result,indent=2),flush=True)
    if not all_exact or max_difference!=0:raise SystemExit(1)

if __name__=='__main__':main()
