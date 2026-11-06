"""Independent arithmetic on the cached original RData; no author-code imports."""
from pathlib import Path
import sys, json, hashlib, datetime, resource

HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parents[1] / 'tasks' / HERE.name
sys.path.insert(0, str(AUTHOR / 'deps'))
import rdata
import numpy as np

raw = (AUTHOR / 'speed_acc.RData').read_bytes()
pin = hashlib.sha256(raw).hexdigest()
blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
assert pin == '991429ecb0a6711dd32422ee4cff9eb7d3010c9de9434387aa36b8788e573f62'
assert blob == '9800773f265db3b30e09ae81b52f612f43527454'
frame = rdata.read_rda(AUTHOR / 'speed_acc.RData')['speed_acc']
pid = frame['id'].astype(str).astype(int).to_numpy()
block = frame['block'].astype(str).astype(int).to_numpy()
rt = frame['rt'].to_numpy(dtype=float)
stimulus = frame['stim_cat'].astype(str).to_numpy()
response = frame['response'].astype(str).to_numpy()
uncensored = ~frame['censor'].to_numpy(dtype=bool)
correct = stimulus == response
mask = (pid == 10) & (block == 2) & uncensored
cells = []
for column in frame.columns:
    if column in ('id', 'block', 'condition', 'stim_cat', 'response', 'frequency'):
        cells.append({'field': column, 'levels': sorted(set(frame[column].astype(str)))})
out = {
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'native_command': 'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python lab/reviews/speed-accuracy-transport-2026-11-01/first_calculation.py',
    'independence': 'Original RData parsed with cached rdata library; independently authored equality/count/sum operations; no author scientific modules imported or executed.',
    'pins': {'bytes':len(raw), 'sha256':pin, 'git_blob':blob},
    'rows':len(frame), 'columns':list(frame.columns), 'levels':cells,
    'person10_block2': {'nominal':int(np.sum((pid==10)&(block==2))),
                         'valid':int(mask.sum()), 'correct':int(correct[mask].sum()),
                         'accuracy':float(correct[mask].mean()),
                         'sum_rt_s':float(rt[mask].sum()), 'mean_rt_s':float(rt[mask].mean())},
    'largest_measured_process_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'additional_scientific_read_decode_hash_charge_bytes':30000000,
    'public_operations':0, 'new_ingress_bytes':0,
    'uncertainties':'Conservative charge includes imports/parser/raw/hash/frame; physical IO and some prior ordinary-read/toolhost peaks unmeasured. Full release again decoded in RAM, preserving original consumed/auxiliary exposure.'
}
assert out['largest_measured_process_rss_bytes_macos'] < 800000000
(HERE/'FIRST_CALCULATION.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
