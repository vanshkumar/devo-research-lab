"""Pinned published trial release. First arithmetic is on source person 1 only."""
from pathlib import Path
import sys, base64, hashlib, json, datetime, resource
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'deps'))
import rdata
import numpy as np
p=ROOT/'speed_acc.RData'
if not p.exists(): p.write_bytes(base64.b64decode((ROOT/'speed_acc.RData.base64').read_bytes()))
raw=p.read_bytes()
sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
assert sha=='9800773f265db3b30e09ae81b52f612f43527454'
obj=rdata.read_rda(p)
df=obj['speed_acc']
print('columns',list(df.columns),'shape',df.shape)
df['pid']=df['id'].astype(str).astype(int)
src=df[df.pid==1].copy()
src['correct']=(src.stim_cat.astype(str)==src.response.astype(str)).astype(int)
rows=[]
for (block,cond),g in src.groupby(['block','condition'],observed=True):
    valid=g[~g.censor]
    rows.append({'block':int(block),'condition':str(cond),'n_all':len(g),'n_uncensored':len(valid),
                 'correct_uncensored':int(valid.correct.sum()),'accuracy_uncensored':float(valid.correct.mean()),
                 'mean_rt_uncensored_s':float(valid.rt.mean()),'sum_rt_uncensored_s':float(valid.rt.sum()),
                 'n_censored':int(g.censor.sum())})
metadata=[]
for pid,g in df.groupby('pid',observed=True):
    # Nonresponse metadata only for other people; no other-person outcome summaries.
    pairs=g[['block','condition']].drop_duplicates().sort_values('block')
    metadata.append({'id':int(pid),'n_rows':len(g),'blocks':[[int(r.block),str(r.condition)] for r in pairs.itertuples()]})
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':'.venv/bin/python lab/tasks/speed-accuracy-transport-2026-11-01/first_data_check.py',
     'release':'rtdists/rtdists 83a31d43411692f86896c4c1d076ddcfa277cb83/data/speed_acc.RData',
     'git_blob_sha1':sha,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
     'participant1_original_trial_arithmetic':rows,'nonresponse_metadata':metadata,
     'interpretation':'Original released trial-choice/RT/instruction joins for person1 only; not forecast utility or original acquisition-raw provenance.',
     'exposure':'Whole release acquired/base64-decoded/hash checked and library-decoded in memory. Only person1 response values summarized/interpreted here. All block/condition metadata exposed. Evaluation raw bytes are not an unacquired holdout.',
     'read_decode_hash_charge_bytes':20000000,'maxrss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(ROOT/'FIRST_DATA_CHECK.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
