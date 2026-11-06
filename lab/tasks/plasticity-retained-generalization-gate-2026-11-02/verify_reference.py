"""Independent explicit-contraction replay of saved short feasibility, no matmul.

Uses same disclosed source/RNG/data realization, independently expressed SGD.
Does not modify saved calculation/checkpoint or score new observations.
"""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS','BLIS_NUM_THREADS'):
    os.environ[key]='1'
import collections
import gzip
import hashlib
import json
from pathlib import Path
import resource
import time
import warnings
import numpy as np

started=time.perf_counter()
here=Path(__file__).resolve().parent
root=here.parents[2]
read_bytes=0
decoded_bytes=0
def read(path):
    global read_bytes
    value=path.read_bytes()
    read_bytes+=len(value)
    return value

saved=json.loads(read(here/'FEASIBILITY.json'))
tree=json.loads(read(root/'lab/tasks/plasticity-retention-source-benchmark-2026-11-02/SOURCE_TREE.json'))
expected={x['path']:x for x in tree['tree'] if x['type']=='blob'}
sources=[]
for path in sorted((here/'vendor').rglob('*')):
    if not path.is_file(): continue
    rel=path.relative_to(here/'vendor').as_posix()
    data=read(path)
    git_hash=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    sources.append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
                    'expected_git_blob':expected[rel]['sha'],'git_blob':git_hash,
                    'byte_certified':git_hash==expected[rel]['sha']})
train_bytes=gzip.decompress(read(here/'data/train-images-idx3-ubyte.gz'))
label_bytes=gzip.decompress(read(here/'data/train-labels-idx1-ubyte.gz'))
test_bytes=gzip.decompress(read(here/'data/t10k-images-idx3-ubyte.gz'))
test_label_bytes=gzip.decompress(read(here/'data/t10k-labels-idx1-ubyte.gz'))
decoded_bytes+=sum(map(len,(train_bytes,label_bytes,test_bytes,test_label_bytes)))
train=np.frombuffer(train_bytes,dtype=np.uint8,offset=16).reshape(60000,784)
labels=np.frombuffer(label_bytes,dtype=np.uint8,offset=8)
test=np.frombuffer(test_bytes,dtype=np.uint8,offset=16).reshape(10000,784)
test_labels=np.frombuffer(test_label_bytes,dtype=np.uint8,offset=8)
train_hashes={hashlib.sha256(row.tobytes()).digest() for row in train}
test_hashes=[hashlib.sha256(row.tobytes()).digest() for row in test[:64]]
overlap=[i for i,h in enumerate(test_hashes) if h in train_hashes]
assert not overlap
all_fingerprint_bytes=60064*784
rng=np.random.RandomState(saved['seed'])
permutation=rng.permutation(784)
order=rng.permutation(60000)
assert permutation.tolist()==saved['pixel_permutation'] and order[:256].tolist()==saved['train_ids']
x=train[order[:256]][:,permutation].astype(np.float64)/255
ys=labels[order[:256]]
tx=test[:64][:,permutation].astype(np.float64)/255
ty=test_labels[:64]
sizes=[784,2000,2000,2000,10]
w=[rng.uniform(-np.sqrt((6 if i<3 else 3)/sizes[i]),np.sqrt((6 if i<3 else 3)/sizes[i]),(sizes[i+1],sizes[i])) for i in range(4)]
b=[np.zeros(sizes[i+1]) for i in range(4)]
def predict(arr):
    layer=[arr]
    for i in range(4):
        z=np.einsum('...i,oi->...o',layer[-1],w[i],optimize=False)+b[i]
        layer.append(np.maximum(0,z) if i<3 else z)
    return layer

def test_reference(pin):
    z=predict(tx)[-1]
    gap=float(np.max(np.abs(z-np.array(pin['logits']))))
    assert gap<1e-10
    losses=np.logaddexp.reduce(z,axis=1)-z[np.arange(64),ty]
    assert np.max(np.abs(losses-np.array(pin['per_example_loss'])))<1e-10
    return gap

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    initial_logit_gap=test_reference(saved['initial_test'])
    losses=[]
    learning_start=time.perf_counter()
    for xx,yy in zip(x,ys):
        a=predict(xx)
        logits=a[-1]
        losses.append(float(np.logaddexp.reduce(logits)-logits[yy]))
        exponent=np.exp(logits-max(logits))
        delta=exponent/sum(exponent)
        delta[yy]-=1
        deltas=[None]*4
        deltas[3]=delta
        for j in (2,1,0):
            deltas[j]=np.einsum('o,oi->i',deltas[j+1],w[j+1],optimize=False)*(a[j+1]>0)
        for j in range(4):
            w[j]-=saved['step_size']*np.einsum('o,i->oi',deltas[j],a[j],optimize=False)
            b[j]-=saved['step_size']*deltas[j]
    reference_learning_seconds=time.perf_counter()-learning_start
    final_logit_gap=test_reference(saved['final_test'])
max_loss_gap=float(np.max(np.abs(np.array(losses)-np.array(saved['online_losses']))))
assert max_loss_gap<1e-10
checkpoint_size=(here/'FEASIBILITY_CHECKPOINT.npz').stat().st_size
read_bytes+=checkpoint_size
with np.load(here/'FEASIBILITY_CHECKPOINT.npz') as checkpoint:
    parameter_gaps=[]
    for j in range(4):
        parameter_gaps.extend((float(np.max(np.abs(w[j]-checkpoint[f'w{j}']))),float(np.max(np.abs(b[j]-checkpoint[f'b{j}'])))))
    max_parameter_gap=max(parameter_gaps)
assert max_parameter_gap<1e-10
assert not caught
report={'status':'PASS_FULL_256_UPDATE_EXPLICIT_REPLAY','utc_finished':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'initial_64x10_logit_max_gap':initial_logit_gap,'final_64x10_logit_max_gap':final_logit_gap,
        'all_256_online_loss_max_gap':max_loss_gap,'all_9594010_parameters_max_gap':max_parameter_gap,
        'full_reference_learning_seconds':reference_learning_seconds,'total_seconds_after_imports':time.perf_counter()-started,
        'max_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'new_warnings':len(caught),'original_warning_count':len(saved['warnings']),
        'original_warnings_by_type':dict(collections.Counter(x['message'] for x in saved['warnings'])),
        'source_manifest':sources,'all_60000_train_vs_64_test_exact_image_hash_overlap':overlap,
        'explicit_file_read_bytes':read_bytes,'gzip_inflated_decode_bytes':decoded_bytes,
        'additional_decoded_image_fingerprint_bytes':all_fingerprint_bytes,
        'threadpools_reported_original':saved['threadpools'],
        'scope':'within-investigator independent numerical implementation; no independent scientific review or new test observations',
        'warning_backend_cause':'UNIDENTIFIED; whole explicit replay supports numerical outputs, not a universal BLAS diagnosis'}
(here/'REFERENCE.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
