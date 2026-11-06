"""Source input support; Figure 4 outcomes never converted/retained."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k] = '1'
import csv, hashlib, json, resource
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT/'sources/learning_intervention_feasibility_2026-10-28'
ALLOW = {'SN','TN','tgt_jump_size','clamp_size','Exp','ti','Subject','TrialNum',
         'ClampAngle','TargetJump','TrialType','TrialLabel','TgtAngle',
         'TargetSize','TgtSize','TargetDiameter','TgtDiameter'}
FILES = ('tsay_TE_SPE.csv','tsay_controljump.csv','task_success_fig3.csv','task_success_fig4.csv')

def main():
    manifest = json.loads((SOURCE/'source_manifest.json').read_text())
    records=[]
    read_charge=0
    for name in FILES:
        item=next(x for x in manifest['files'] if x['local']==name)
        p=SOURCE/name
        payload=p.read_bytes()
        # Eight full-file equivalents cover both physical reads, decode/tokenize,
        # input conversion and two hashes. Authoritative run ledger also charges earlier passes at this rate.
        read_charge += 8*len(payload)
        blob=hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
        assert blob==item['expected_git_blob'],name
        sha=hashlib.sha256(payload).hexdigest()
        del payload
        with p.open(newline='') as f:
            reader=csv.DictReader(f)
            columns=reader.fieldnames
            rows=[{k:v for k,v in row.items() if k in ALLOW} for row in reader]
        if name.startswith('tsay'):
            core=[r for r in rows if int(r['TN'])>100 and (int(r['TN'])-101)%181<180]
            key='SN'; ck='clamp_size'; jk='tgt_jump_size'
        else:
            last=903 if 'fig3' in name else 967
            core=[r for r in rows if 104<=int(r['TrialNum'])<=last]
            key='Subject'; ck='ClampAngle'; jk='TargetJump'
        sizes={k:sorted(set(r[k] for r in core)) for k in ALLOW if k in columns and 'Size' in k or k in columns and 'Diameter' in k}
        counts=Counter((float(r[ck]),float(r[jk]),r.get('TrialLabel','')) for r in core)
        rec=dict(local=name,bytes=p.stat().st_size,sha256=sha,git_blob=blob,pin_matches=True,
                 schema=columns,retained_input_fields=sorted(set(columns)&ALLOW),
                 outcome_numeric_values_decoded=0,n_people=len(set(r[key] for r in core)),n_exposures=len(core),
                 clamps=sorted(set(float(r[ck]) for r in core)),sizes=sizes,
                 input_cells=[dict(clamp=c,jump=j,label=l,n=n) for (c,j,l),n in sorted(counts.items())])
        records.append(rec)
    source_clamps=sorted(set(c for r in records[:3] for c in r['clamps']))
    target_clamps=records[-1]['clamps']
    # Odd monotone saturating laws normalized to agree exactly at +/-4.
    curves=[]
    grid=sorted(set(source_clamps+target_clamps))
    for tau in (1.,4.,16.):
        vals=np.tanh(np.asarray(grid)/tau)/np.tanh(4/tau)
        curves.append(dict(tau=tau,values=vals.tolist()))
    source_idx=[grid.index(c) for c in source_clamps]
    source_difference=max(abs(np.asarray(curves[0]['values'])[source_idx]-np.asarray(curves[-1]['values'])[source_idx]))
    target_idx=[grid.index(c) for c in target_clamps]
    max_target_difference=float(np.max(abs(np.asarray(curves[0]['values'])[target_idx]-np.asarray(curves[-1]['values'])[target_idx])))
    out=dict(created_utc=datetime.now(timezone.utc).isoformat(),scope='inputs only; all outcome strings discarded',
             files=records,source_clamps=source_clamps,target_clamps=target_clamps,
             exact_signed_clamp_overlap=sorted(set(source_clamps)&set(target_clamps)),
             normalized_saturation_counterexample=dict(grid=grid,curves=curves,
                 max_source_difference=float(source_difference),max_target_difference=max_target_difference,
                 interpretation='Distinct odd monotone saturating sensory-response laws agree on every source clamp but differ at target clamps. This forbids unique absolute amplitude transport without an extra shape assumption, not every normalized contrast test.'),
             charged_additional_read_decoded_hash_bytes=read_charge,public_requests=0,new_ingress_bytes=0,
             peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (HERE/'SOURCE_SUPPORT.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('files','normalized_saturation_counterexample')},indent=2))
    print(json.dumps(out['normalized_saturation_counterexample'],indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=1): main()
