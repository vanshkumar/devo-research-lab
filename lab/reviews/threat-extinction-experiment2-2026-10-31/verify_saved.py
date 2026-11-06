"""Final finite reconstruction checks on saved outputs; no source reanalysis."""
import datetime as dt
import hashlib
import json
import pathlib
import resource
import os
for v in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[v]='1'
import numpy as np

HERE=pathlib.Path(__file__).resolve().parent
AUTHOR=HERE.parents[1]/'tasks/threat-extinction-experiment2-2026-10-31'
bytesread=0
def read(p):
    global bytesread
    b=p.read_bytes()
    bytesread+=len(b)
    return b
def load(p):
    return json.loads(read(p))

reconstruction=load(HERE/'RECONSTRUCTION.json')
savedstatic=load(AUTHOR/'CONTRARY.json')['results']
rng=np.random.default_rng(202611010233)
loss_checks=0
maxerr=0.
bootstrap_checks=0
for key,ours in reconstruction['comparisons'].items():
    saved=savedstatic[key]
    rows=ours['per_participant']
    common=np.array([x['common'] for x in rows])
    static=np.array([x['static'] for x in rows])
    for ourrow,theirrow in zip(rows,saved['per_participant']):
        assert ourrow['id']==theirrow['id']
        for a,b in [('common','common_loss'),('static','static_loss')]:
            err=abs(ourrow[a]-theirrow[b])
            maxerr=max(maxerr,err)
            assert err<1e-13
            loss_checks+=1
    delta=common-static
    index=rng.integers(0,len(rows),size=(10000,len(rows)))
    change=delta[index].mean(1)
    ratio=change/common[index].mean(1)
    for a,b in [(np.quantile(change,[.025,.975]),saved['static_gain_mse_bootstrap95']),
                (np.quantile(ratio,[.025,.975]),saved['static_fractional_reduction_bootstrap95'])]:
        err=float(np.max(np.abs(a-b)))
        maxerr=max(maxerr,err)
        assert err<1e-13
        bootstrap_checks+=2
freeze=load(HERE/'CONTRARY_FREEZE.json')
assert all(hashlib.sha256(read(HERE/n)).hexdigest()==h for n,h in freeze['pins'].items())
for filename in ['FREEZE.json','CONTRARY_FREEZE.json']:
    f=load(AUTHOR/filename)
    assert all(hashlib.sha256(read(AUTHOR/n)).hexdigest()==h for n,h in f['pins'].items())
files=load(AUTHOR/'sources/files.json')
node=load(AUTHOR/'sources/node.json')['data']
license=load(AUTHOR/'sources/license.json')['data']
file=next(x for x in files['data'] if x['id']=='5bacda4f71746000164c3e58')
attributes=file['attributes']
cached_archive=read(AUTHOR/'sources/experiment2.zip')
hashes=attributes['extra']['hashes']
assert attributes['size']==len(cached_archive)==106395 and attributes['current_version']==1
assert hashlib.md5(cached_archive).hexdigest()==hashes['md5']
assert hashlib.sha256(cached_archive).hexdigest()==hashes['sha256']
assert node['id']=='dxpb3'
assert node['relationships']['license']['data']['id']==license['id']=='563c1cf88c5e4a3877f9e96a'
assert license['attributes']['url']=='https://creativecommons.org/licenses/by/4.0/legalcode'
manifest={'deposit':'https://osf.io/dxpb3/','paper_doi':'10.1016/j.jbtep.2018.09.007',
          'attribution':'Mertens, Leer, van Dis, Vermeer, Steenhuizen, van der Veen and Engelhard (2019)',
          'title':node['attributes']['title'],'file_id':file['id'],'version':attributes['current_version'],
          'name':attributes['name'],'bytes':len(cached_archive),'source_hashes':hashes,
          'actual_archive_hashes_match_cached_provider_metadata':True,
          'license':{'id':license['id'],'name':license['attributes']['name'],'url':license['attributes']['url']},
          'cached_source':str(AUTHOR/'sources/experiment2.zip'),
          'review_member_hashes':load(HERE/'FIRST_CALCULATION.json')['member_sha256'],
          'new_public_operations':0,'new_ingress_bytes':0,
          'source_limits':'Supplied features, ordinal cues and source-defined schedule only; raw physiology/hardware/elapsed-time/window extraction not independently reconstructed.'}
(HERE/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
out={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'static_individual_loss_checks':loss_checks,
     'static_bootstrap_endpoint_checks':bootstrap_checks,'maximum_difference':maxerr,
     'own_and_author_freeze_pins_pass':True,'source_artifact_hash_bytes_read':bytesread,
     'conservative_stage_charge_bytes':6000000,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     'public_operations':0,'ingress_bytes':0,'jobs_after_command':0}
(HERE/'FINAL_VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
