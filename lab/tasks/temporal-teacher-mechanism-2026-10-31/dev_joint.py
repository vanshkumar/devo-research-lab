import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import argparse,time,json,hashlib
import numpy as np
import core as c
from batched import Circuit,signals,segment_loss,rle_from_waveform,input_moments
from actor import Actor
from common import HERE,save,now,charge,read,check_deadline

def phases(actions,seed):
    return np.array([(-80,0,80)[int.from_bytes(hashlib.blake2b(a.tobytes()+str(seed).encode(),digest_size=2).digest(),'little')%3] for a in actions])

def run_case(plant,d,net,teacher,initial,tag,round_info=True,net0=None):
    started=time.monotonic();h=c.quiet(net);r,_=c.simulate(net,teacher,h);prototype=c.prototype(r);model=Circuit(net,h)
    silence,_=c.simulate(net,np.zeros_like(teacher),h);model.quiet_rate=float(silence.mean());del silence
    memory=c.learn_state(teacher);target=rle_from_waveform(teacher)
    state_target=(memory['emissions'],memory['starts'],memory['starts']+memory['durations'])
    orders=c.policies(98100+plant);input_target=np.r_[(teacher/2).mean(0),(teacher*teacher/4).mean(0)]
    input_scale=np.r_[(teacher/2).var(0),(teacher*teacher/4).var(0)]+1e-6
    np.savez_compressed(c.SOURCE/('%s_%03d_model.npz'%(tag,plant)),JT=model.JT,h=model.h,inv_tau=model.inv_tau,maximum=model.maximum,
                        threshold=model.threshold,width=model.width,prototype_mean=prototype['mean'],prototype_variance=prototype['variance'],
                        teacher=teacher,emissions=memory['emissions'],starts=memory['starts'],durations=memory['durations'],
                        input_mean=input_target,input_scale=input_scale,quiet_rate=model.quiet_rate)
    np.savez(c.SOURCE/('%s_%03d_environment.npz'%(tag,plant)),basis=d['basis'],bias=d['bias'],initial=initial,orders=orders,teacher_observation=teacher)
    cache={};calls=0;timings=[];phase_seed=390000+plant
    def evaluate_many(actions):
        nonlocal calls
        actions=np.asarray(actions);keys=[a.tobytes() for a in actions];missing={k:a for k,a in zip(keys,actions) if k not in cache}
        if missing:
            aa=np.array(list(missing.values()));pp=phases(aa,phase_seed);y,ss,ee,valid=signals(aa,d['basis'],d['bias'],orders,pp)
            t=time.monotonic();mom,_=model.run(y,ss,ee);timings.append({'candidates':len(aa),'seconds':time.monotonic()-t});calls+=len(aa)
            raw=mom[:,:net.NE].mean(1)*100;active=((ee-ss)*valid).sum(1)
            proto=np.mean((mom-prototype['mean'])**2/prototype['variance'],axis=1)
            norm=(raw-model.quiet_rate)*c.T/np.maximum(active,1)
            for i,key in enumerate(missing):cache[key]={'raw':float(raw[i]),'normalized':float(norm[i]),'population':float(proto[i])}
        return {mode:np.array([cache[k][mode] for k in keys]) for mode in ('raw','normalized','population')}
    actors={mode:Actor(initial,180000+plant) for mode in ('raw','normalized','population')}
    iteration=0
    while any(a.stage!='done' for a in actors.values()):
        pending={mode:a.ask() for mode,a in actors.items() if a.stage!='done'}
        joined=np.concatenate(list(pending.values()));v=evaluate_many(joined);start=0
        for mode,aa in pending.items():actors[mode].tell(v[mode][start:start+len(aa)]);start+=len(aa)
        iteration+=1
        if iteration%4==0:print(json.dumps({'case':plant,'stage':tag,'neural_iteration':iteration,'unique_probes':calls,'elapsed':time.monotonic()-started}),flush=True)
        check_deadline()
    # Cheap source-observable teachers and privileged oracle use identical actor.
    for mode in ('state','template','input_moments','oracle'):
        a=Actor(initial,180000+plant)
        while a.stage!='done':
            aa=a.ask();y,ss,ee,valid=signals(aa,d['basis'],d['bias'],orders,phases(aa,phase_seed))
            if mode=='state':v=segment_loss(y,ss,ee,valid,state_target)
            elif mode in ('template','oracle'):v=segment_loss(y,ss,ee,valid,target)
            else:v=np.mean((input_moments(y,ss,ee,valid)-input_target)**2/input_scale,axis=1)
            a.tell(v)
        actors[mode]=a
    if net0 is not None:
        h0=c.quiet(net0);r0,_=c.simulate(net0,teacher,h0);p0=c.prototype(r0);model0=Circuit(net0,h0);cache0={};a=Actor(initial,180000+plant)
        np.savez_compressed(c.SOURCE/('%s_%03d_fixed_model.npz'%(tag,plant)),JT=model0.JT,h=model0.h,inv_tau=model0.inv_tau,maximum=model0.maximum,
                            threshold=model0.threshold,width=model0.width,prototype_mean=p0['mean'],prototype_variance=p0['variance'])
        while a.stage!='done':
            aa=a.ask();keys=[v.tobytes() for v in aa];missing={k:v for k,v in zip(keys,aa) if k not in cache0}
            if missing:
                batch=np.array(list(missing.values()));yy,ss,ee,valid=signals(batch,d['basis'],d['bias'],orders,phases(batch,phase_seed));mm,_=model0.run(yy,ss,ee)
                val=np.mean((mm-p0['mean'])**2/p0['variance'],axis=1)
                for key,v in zip(missing,val):cache0[key]=float(v)
            a.tell([cache0[k] for k in keys]);check_deadline()
        actors['unplasticized_population']=a
    result=[]
    for mode,a in actors.items():
        out=a.arrays();np.savez(HERE/('outputs/%s_%03d_%s_queries.npz'%(tag,plant,mode)),**out)
        # Offline true scoring begins only after this actor's query file exists.
        y,ss,ee,valid=signals(out['actions'],d['basis'],d['bias'],orders,np.zeros(len(out['actions']),dtype=int))
        gold=segment_loss(y,ss,ee,valid,target);a0=np.r_[initial,1.,.8][None,:]
        iy,iss,iee,iv=signals(a0,d['basis'],d['bias'],orders,np.zeros(1,dtype=int));initial_gold=float(segment_loss(iy,iss,iee,iv,target)[0])
        summary={'case':plant,'mode':mode,'queries':len(out['query_actions']),'initial_gold':initial_gold,'final_gold':float(gold[-1]),
                 'improvement':float(1-gold[-1]/initial_gold),'final_action':out['actions'][-1].tolist(),'trajectory_gold':gold.tolist()}
        result.append(summary)
    save('outputs/%s_%03d.json'%(tag,plant),{'time':now(),'results':result,'unique_source_probes':calls,'timings':timings,'seconds':time.monotonic()-started})
    print(json.dumps({'case':plant,'results':[{k:v for k,v in row.items() if k!='trajectory_gold'} for row in result],'seconds':time.monotonic()-started}),flush=True)
    return {'model':model,'prototype':prototype,'memory':memory,'teacher':teacher,'d':d,'orders':orders,'results':result}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--plant',type=int,default=100);args=ap.parse_args()
    d,net=c.load_old(args.plant);y=c.features(d['target'],d['basis'],d['bias']);teacher=c.waveform(y)
    # Check the batched equations against unmodified source before motor search.
    h=c.quiet(net);model=Circuit(net,h);test=np.array([np.r_[d['target'],0.,1.],np.r_[d['target'],2.,.8]])
    orders=c.policies(98100+args.plant);yy,ss,ee,valid=signals(test,d['basis'],d['bias'],orders,np.array([-60,60]));start=time.monotonic()
    stats,tr=model.run(yy,ss,ee,trace=True);bench=time.monotonic()-start;errors=[]
    for i in range(2):
        aud=c.waveform(yy[i],test[i,5],(-60,60)[i]);ref,_=c.simulate(net,aud,h)
        errors.append(float(np.max(np.abs(tr[i]-ref))));assert errors[-1]<1e-10
    save('outputs/BATCH_SOURCE_CHECK_%03d.json'%args.plant,{'max_trace_errors':errors,'two_probe_seconds':bench})
    print(json.dumps({'batch_source_errors':errors,'two_probe_seconds':bench}),flush=True)
    run_case(args.plant,d,net,teacher,d['initial'],'development')
if __name__=='__main__':main()
