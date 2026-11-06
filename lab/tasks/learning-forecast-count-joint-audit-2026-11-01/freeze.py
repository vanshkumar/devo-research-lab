"""Form comparison vectors and pin the pre-score design; no new scoring."""
from pathlib import Path
import datetime as dt
import hashlib
import io
import json
import resource
import zipfile
import numpy as np

O=Path(__file__).resolve().parent


def main():
    now=dt.datetime.now(dt.timezone.utc)
    assert now<dt.datetime(2026,11,1,13,16,15,tzinfo=dt.timezone.utc)
    first=json.loads((O/'FIRST_CALCULATION.json').read_text())
    b=(O/'ENDPOINTS.npz').read_bytes()
    with zipfile.ZipFile(io.BytesIO(b)) as z:decoded=sum(v.file_size for v in z.infolist())
    with np.load(io.BytesIO(b),allow_pickle=False) as z:x={k:z[k] for k in z.files}
    n=np.array([x[m+'_opportunities'] for m in ('rnn','growth')])
    k=np.array([x[m+'_successes'] for m in ('rnn','growth')])
    on=x['observed_opportunities'];ok=x['observed_successes']
    generated=np.stack([k,n-k,500-n],axis=-1)/500.
    observed=np.stack([ok,on-ok,500-on],axis=-1)/500.
    assert generated.shape==(2,24,512,6,2,3)
    assert (generated>=0).all() and (observed>=0).all()
    np.savez_compressed(O/'COMPARISON_OBJECTS.npz',subjects=x['subjects'],labs=x['labs'],
        generated_categories=generated,observed_categories=observed,
        opportunities=n,successes=k,observed_opportunities=on,observed_successes=ok)
    cb=(O/'COMPARISON_OBJECTS.npz').read_bytes()
    # Reading the freshly written compressed bytes for their pin is charged.
    charge=first['resources']['cumulative_read_hash_decode_charge_bytes']+len(b)+decoded+len(cb)+2_000_000
    assert charge<200_000_000
    paths=('DESIGN.md','RESOURCE_PLAN.json','compare.py','first_calculation.py','freeze.py')
    pins={p:hashlib.sha256((O/p).read_bytes()).hexdigest() for p in paths}
    frozen=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),status='comparison_objects_and_design_frozen_before_new_scores',
        first_calculation_utc=first['utc'],new_joint_and_growth_pooled_scores_computed=False,
        endpoint_input_sha256=hashlib.sha256(b).hexdigest(),comparison_objects_sha256=hashlib.sha256(cb).hexdigest(),
        frozen_sources=pins,input_manifest=first['input_manifest'],
        resources=dict(cumulative_read_hash_decode_charge_bytes=charge,
            freeze_endpoint_containing_bytes=len(b),freeze_endpoint_decoded_bytes=decoded,
            comparison_pin_bytes=len(cb),freeze_code_context_allowance_bytes=2_000_000,
            peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            physical_io_unknown=True,failed_start_allowance_preserved_bytes=5_000_000,
            scientific_processes=1,numerical_threads=1,public_operations=0,downloads=0,ingress_bytes=0))
    (O/'FROZEN_PLAN.json').write_text(json.dumps(frozen,indent=2)+'\n')
    print(json.dumps({k:frozen[k] for k in ('utc','status','comparison_objects_sha256','resources')},indent=2),flush=True)


if __name__=='__main__':main()
