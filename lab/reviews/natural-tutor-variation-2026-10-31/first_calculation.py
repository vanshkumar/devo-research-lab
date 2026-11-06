"""Independent annotation-to-interval calculation; no author imports."""
import argparse
import collections
import csv
import datetime
import hashlib
import io
import json
from pathlib import Path
import resource
import sys
import numpy as np

ROOT = Path(__file__).resolve().parent
HERE = ROOT
AUTHOR = ROOT.parents[1] / 'tasks' / 'natural-tutor-variation-2026-10-31'

def main():
    global HERE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',help='new unused direct child directory for an authorized reproduction')
    args = parser.parse_args()
    if args.output:
        destination = (ROOT/args.output).resolve()
        assert destination.parent==ROOT and not destination.exists(), 'new owned direct child required'
        destination.mkdir()
        HERE = destination
    assert not (HERE/'FIRST_CALCULATION.json').exists(), 'preserve earned outputs; choose --output'
    ledger = []
    def read(path, kind='read'):
        raw = path.read_bytes()
        ledger.append({'path': str(path.relative_to(AUTHOR)), 'kind': kind, 'bytes': len(raw)})
        return raw
    if HERE != ROOT:
        plan = (ROOT/'PLAN.md').read_bytes()
        ledger.append({'path':'PLAN.md','kind':'reproduction copy read','bytes':len(plan)})
        (HERE/'PLAN.md').write_bytes(plan)
    paths = sorted((AUTHOR / 'sources' / 'annotations').glob('*.csv'))
    assert len(paths) == 39
    features, keys, groups, counts, source = [], [], [], [], []
    motif_counts = collections.Counter()
    all_rows = 0
    for file_index, path in enumerate(paths):
        raw = read(path)
        ledger.append({'path': str(path.relative_to(AUTHOR)), 'kind': 'UTF8 decode', 'bytes': len(raw)})
        parsed = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
        labels = [row['label'] for row in parsed]
        onset = np.array([float(row['onset_s']) for row in parsed])
        offset = np.array([float(row['offset_s']) for row in parsed])
        assert np.isfinite(onset).all() and np.isfinite(offset).all()
        assert np.all(onset >= 0) and np.all(offset > onset)
        assert np.all(onset[1:] >= offset[:-1])
        all_rows += len(parsed)
        if file_index < 6:
            for j in range(len(labels)-2):
                candidate = tuple(labels[j:j+3])
                if len(set(candidate)) == 3 and 'i' not in candidate:
                    motif_counts[candidate] += 1
        n = 0
        j = 0
        while j+2 < len(labels):
            if labels[j:j+3] == ['a','b','c']:
                intervals = [offset[j]-onset[j], onset[j+1]-offset[j],
                             offset[j+1]-onset[j+1], onset[j+2]-offset[j+1],
                             offset[j+2]-onset[j+2]]
                assert min(intervals) > 0
                features.append(intervals)
                keys.append(path.name+':'+str(j))
                groups.append(path.name)
                n += 1
                j += 3
            else:
                j += 1
        counts.append(n)
        source.append({'file':path.name,'annotation_rows':len(parsed),'phrases':n,
                       'csv_bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        ledger.append({'path':str(path.relative_to(AUTHOR)), 'kind':'SHA256 hash', 'bytes':len(raw)})
    x = np.log(np.asarray(features))
    g = np.asarray(groups)
    key = np.asarray(keys)
    split = [sum(counts[:19]),sum(counts[19:29]),sum(counts[29:])]
    comparisons = []
    for phase, names in [('MAIN', paths[19:29]),('REVISION',paths[29:])]:
        raw = read(AUTHOR / (phase+'_SCORES.npz'))
        with np.load(io.BytesIO(raw),allow_pickle=False) as z:
            for name in ['train_x','train_groups','train_keys','eval_x','eval_groups','eval_keys']:
                saved = z[name]
                ledger.append({'path':phase+'_SCORES.npz:'+name, 'kind':'NPY decode', 'bytes':saved.nbytes})
                mask = np.isin(g,[p.name for p in (paths[:19] if name.startswith('train') else names)])
                actual = x[mask] if name.endswith('_x') else g[mask] if name.endswith('_groups') else key[mask]
                equal = bool(np.array_equal(actual,saved))
                comparisons.append({'phase':phase,'array':name,'shape':list(saved.shape),'exact_match':equal,
                                    'max_abs_error':float(np.max(np.abs(saved-actual))) if name.endswith('_x') else None})
                assert equal, (phase,name)
    output = {'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'reviewer':'01a194c8-9a34-7ed3-a40b-5561751322a5',
              'recordings':len(paths),'annotation_rows':all_rows,'total_phrases':len(x),
              'teaching_main_revision_phrases':split,'first6_phrases':sum(counts[:6]),
              'input_only_motif_winner':list(sorted(motif_counts,key=lambda k:(-motif_counts[k],k))[0]),
              'motif_counts':[{'motif':list(k),'count':v} for k,v in sorted(motif_counts.items(),key=lambda kv:(-kv[1],kv[0]))],
              'source_csvs':source,'array_comparisons':comparisons,
              'scientific_byte_passes':ledger,'scientific_read_decoded_hash_bytes':sum(v['bytes'] for v in ledger),
              'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'python':sys.version,'numpy':np.__version__,'network_requests':0,'jobs':0}
    assert output['peak_rss_bytes'] < 400000000
    assert output['scientific_read_decoded_hash_bytes'] < 2000000
    (HERE/'FIRST_CALCULATION.json').write_text(json.dumps(output,indent=2)+'\n')
    np.savez_compressed(HERE/'INDEPENDENT_FEATURES.npz',x=x,seconds=np.asarray(features),groups=g,keys=key)
    print(json.dumps({k:output[k] for k in ['timestamp','recordings','annotation_rows','total_phrases',
          'teaching_main_revision_phrases','first6_phrases','input_only_motif_winner',
          'scientific_read_decoded_hash_bytes','peak_rss_bytes','jobs']},indent=2))

if __name__=='__main__':
    main()
