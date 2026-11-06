"""Full original architecture, real MNIST, short SGD execution + unseen test score.

Independent NumPy source-equation implementation, not author Torch replay.
See FEASIBILITY_PLAN.md. No main scientific comparison is performed.
"""
import os
for variable in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS','BLIS_NUM_THREADS'):
    os.environ[variable] = '1'
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import resource
import struct
import time
import warnings
import numpy as np

HERE = Path(__file__).resolve().parent
started = time.perf_counter()
read_bytes = 0
decoded_bytes = 0
checks = {}
trace = []
warning_log = []
pool_info = []
if importlib.util.find_spec('threadpoolctl'):
    import threadpoolctl
    threadpoolctl.threadpool_limits(1)
    pool_info = threadpoolctl.threadpool_info()

def read_idx(name, expected_shape):
    global read_bytes, decoded_bytes
    compressed = (HERE/'data'/name).read_bytes()
    read_bytes += len(compressed)
    raw = gzip.decompress(compressed)
    decoded_bytes += len(raw)
    zero1, zero2, dtype, ndim = struct.unpack('>BBBB', raw[:4])
    shape = struct.unpack('>'+'I'*ndim, raw[4:4+4*ndim])
    assert (zero1,zero2,dtype)==(0,0,8) and shape==expected_shape
    result = np.frombuffer(raw, dtype=np.uint8, offset=4+4*ndim).reshape(shape)
    assert result.size == len(raw)-4-4*ndim
    return result.copy()

def forward(x, weights, biases, reference=False):
    acts = [x]
    for idx, (w,b) in enumerate(zip(weights,biases)):
        z = np.einsum('...i,oi->...o',acts[-1],w,optimize=False)+b if reference else acts[-1]@w.T+b
        acts.append(np.maximum(z,0) if idx<3 else z)
    return acts

def probabilities(logits):
    centered=logits-np.max(logits,axis=-1,keepdims=True)
    exponent=np.exp(centered)
    return exponent/np.sum(exponent,axis=-1,keepdims=True)

def loss(logits,y):
    return float(np.logaddexp.reduce(logits)-logits[y])

def gradients(x,y,weights,biases,reference=False):
    acts=forward(x,weights,biases,reference)
    delta=probabilities(acts[-1])
    delta[y]-=1
    gw=[None]*4
    gb=[None]*4
    for idx in range(3,-1,-1):
        gw[idx]=np.einsum('o,i->oi',delta,acts[idx],optimize=False) if reference else np.outer(delta,acts[idx])
        gb[idx]=delta.copy()
        if idx:
            delta=(np.einsum('o,oi->i',delta,weights[idx],optimize=False) if reference else delta@weights[idx])*(acts[idx]>0)
    return loss(acts[-1],y), gw, gb

def score(x,y,weights,biases):
    logits=forward(x,weights,biases)[-1]
    ref=forward(x,weights,biases,True)[-1]
    p=probabilities(logits)
    p_ref=probabilities(ref)
    ref_losses=np.logaddexp.reduce(ref,axis=1)-ref[np.arange(len(y)),y]
    losses=np.logaddexp.reduce(logits,axis=1)-logits[np.arange(len(y)),y]
    assert np.isfinite(logits).all() and np.isfinite(losses).all()
    max_gap=float(np.max(np.abs(logits-ref)))
    assert max_gap<1e-10 and np.max(np.abs(p.sum(axis=1)-1))<1e-12
    assert np.max(np.abs(losses-ref_losses))<1e-10
    return {'n':len(y),'accuracy':float(np.mean(np.argmax(logits,axis=1)==y)),
            'mean_cross_entropy':float(np.mean(losses)),
            'reference_max_logit_gap':max_gap,
            'reference_max_probability_gap':float(np.max(np.abs(p-p_ref))),
            'reference_max_loss_gap':float(np.max(np.abs(losses-ref_losses))),
            'logits':logits.tolist(),'probabilities':p.tolist(),'per_example_loss':losses.tolist()}

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter('always')
    train_images=read_idx('train-images-idx3-ubyte.gz',(60000,28,28)).reshape(60000,784)
    train_labels=read_idx('train-labels-idx1-ubyte.gz',(60000,))
    test_images=read_idx('t10k-images-idx3-ubyte.gz',(10000,28,28)).reshape(10000,784)
    test_labels=read_idx('t10k-labels-idx1-ubyte.gz',(10000,))
    assert train_labels.max()<10 and test_labels.max()<10
    rng=np.random.RandomState(63017)
    permutation=rng.permutation(784)
    train_order=rng.permutation(60000)
    test_ids=np.arange(64)
    train_ids=train_order[:256]
    x=train_images[train_ids][:,permutation].astype(np.float64)/255.
    y=train_labels[train_ids].astype(int)
    test_x=test_images[test_ids][:,permutation].astype(np.float64)/255.
    test_y=test_labels[test_ids].astype(int)
    checks['inverse_pixel_permutation_exact']=bool(np.array_equal(test_images[test_ids][:,permutation][:,np.argsort(permutation)],test_images[test_ids]))
    assert checks['inverse_pixel_permutation_exact']
    sizes=[784,2000,2000,2000,10]
    weights=[]
    biases=[]
    for idx in range(4):
        bound=np.sqrt((6. if idx<3 else 3.)/sizes[idx])
        weights.append(rng.uniform(-bound,bound,size=(sizes[idx+1],sizes[idx])))
        biases.append(np.zeros(sizes[idx+1]))
    checks['parameter_count']=sum(w.size+b.size for w,b in zip(weights,biases))
    checks['parameter_bytes']=sum(w.nbytes+b.nbytes for w,b in zip(weights,biases))
    initial=score(test_x,test_y,weights,biases)
    ref_started=time.perf_counter()
    l0,gw,gb=gradients(x[0],y[0],weights,biases)
    lr,rgw,rgb=gradients(x[0],y[0],weights,biases,True)
    checks['first_loss_reference_gap']=abs(l0-lr)
    checks['first_gradient_reference_max_gap']=max(float(np.max(np.abs(a-b))) for a,b in zip(gw+gb,rgw+rgb))
    assert checks['first_gradient_reference_max_gap']<1e-10
    fd=[]
    for layer in range(4):
        for kind,arr,grad in [('weight',weights[layer],gw[layer]),('bias',biases[layer],gb[layer])]:
            index=np.unravel_index(np.argmax(np.abs(grad)),grad.shape)
            analytic=float(grad[index])
            assert abs(analytic)>1e-10
            old=float(arr[index]); eps=1e-5
            arr[index]=old+eps
            plus=loss(forward(x[0],weights,biases,True)[-1],y[0])
            arr[index]=old-eps
            minus=loss(forward(x[0],weights,biases,True)[-1],y[0])
            arr[index]=old
            numerical=(plus-minus)/(2*eps)
            error=abs(numerical-analytic)/max(1.,abs(analytic))
            fd.append({'layer':layer,'kind':kind,'index':[int(k) for k in index],
                       'analytic':analytic,'finite_difference':numerical,'scaled_error':error})
            assert error<1e-6
    checks['finite_difference']=fd
    step=.003
    checks['first_sgd_update_max_gap']=0.
    for p,g,rg in zip(weights+biases,gw+gb,rgw+rgb):
        candidate=p-step*g
        reference=p-step*rg
        checks['first_sgd_update_max_gap']=max(checks['first_sgd_update_max_gap'],float(np.max(np.abs(candidate-reference))))
        p-=step*g
    assert checks['first_sgd_update_max_gap']<1e-12
    del gw,gb,rgw,rgb,candidate,reference,p,g,rg
    reference_seconds=time.perf_counter()-ref_started
    trace.append({'n':1,'online_loss':l0})
    learning_started=time.perf_counter()
    online_losses=[l0]
    for i in range(1,256):
        li,gw,gb=gradients(x[i],y[i],weights,biases)
        online_losses.append(li)
        for p,g in zip(weights+biases,gw+gb): p-=step*g
        if i+1 in (16,64,128,256):
            elapsed=time.perf_counter()-learning_started
            trace.append({'n':i+1,'online_loss':li,'mean_online_loss':float(np.mean(online_losses)),
                          'elapsed_learning_loop_seconds':elapsed})
            print(json.dumps(trace[-1]),flush=True)
        assert time.perf_counter()-started<800
    learning_seconds=time.perf_counter()-learning_started
    del gw,gb,p,g
    final=score(test_x,test_y,weights,biases)
    warning_log=[{'category':w.category.__name__,'message':str(w.message),'line':w.lineno} for w in caught]

checkpoint=HERE/'FEASIBILITY_CHECKPOINT.npz'
np.savez(checkpoint,**{f'w{i}':w for i,w in enumerate(weights)},**{f'b{i}':b for i,b in enumerate(biases)},
         effective_pixel_permutation=permutation,train_ids=train_ids,test_ids=test_ids)
checkpoint_bytes=checkpoint.read_bytes()
read_bytes+=len(checkpoint_bytes)
out={'status':'PASS_EXECUTABLE_FEASIBILITY_ONLY','utc_finished':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
     'implementation':'Independent full-architecture NumPy float64 source equations; not author Torch execution',
     'seed':63017,'step_size':step,'architecture':sizes,'learning_updates':256,'tasks_started':1,'tasks_completed':0,
     'published_updates_per_arm':800*60000,'original_train_observations':len(y),'heldout_official_test_observations':len(test_y),
     'pixel_permutation':permutation.tolist(),'train_ids':train_ids.tolist(),'test_ids':test_ids.tolist(),
     'checks':checks,'initial_test':initial,'final_test':final,'trace':trace,
     'online_loss_mean':float(np.mean(online_losses)),'online_losses':online_losses,
     'learning_loop_seconds_for_255_updates':learning_seconds,'first_update_reference_seconds':reference_seconds,
     'total_seconds_after_imports':time.perf_counter()-started,
     'checkpoint':{'bytes':len(checkpoint_bytes),'sha256':hashlib.sha256(checkpoint_bytes).hexdigest(),'scope':'256-update feasibility only; no published long-history continuation'},
     'explicit_input_read_bytes':read_bytes,'gzip_inflated_decode_bytes':decoded_bytes,
     'max_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     'numpy_version':np.__version__,'numpy_path':np.__file__,'threadpools':pool_info,
     'requested_threads':{v:os.environ[v] for v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS','BLIS_NUM_THREADS')},
     'warnings':warning_log,
     'exposure':{'all_four_gzip_objects':'acquired, MD5/SHA256 hashed and fully IDX-decoded',
                 'train_60000_labels':'range checked; only selected 256 interpreted/learned',
                 'test_10000_labels':'range checked; only first 64 interpreted/scored',
                 'auxiliary':'all image bytes decoded; no claim other acquired images/labels are pristine unacquired',
                 'protected_old_payloads':0},
     'main_campaign':'UNRUN','long_history_cost':'UNCERTIFIED; prefix not full-history pricing'}
(HERE/'FEASIBILITY.json').write_text(json.dumps(out,indent=2)+'\n')
assert out['max_rss_bytes_macos']<1_000_000_000
print(json.dumps({k:out[k] for k in ('status','utc_finished','architecture','learning_updates','learning_loop_seconds_for_255_updates','total_seconds_after_imports','max_rss_bytes_macos','explicit_input_read_bytes','gzip_inflated_decode_bytes','warnings')}))
print(json.dumps({'initial_test_accuracy':initial['accuracy'],'initial_test_cross_entropy':initial['mean_cross_entropy'],
                  'final_test_accuracy':final['accuracy'],'final_test_cross_entropy':final['mean_cross_entropy'],
                  'max_finite_difference_scaled_error':max(f['scaled_error'] for f in fd)}))
