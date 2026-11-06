#!/usr/bin/env python3
"""Fit the bounded DNNGLM/REINFORCE set using DEVELOPMENT ANIMALS ONLY."""
from pathlib import Path
import argparse, ast, hashlib, json, time
import numpy as np
from scipy.optimize import minimize
import torch
from torch import nn
from scipy.special import expit
from data_io import subjects, load_subject
from learning_models import LearningModel, load_model, static_fit, subject_arrays, stimulus

CAMPAIGN=Path(__file__).resolve().parents[1]
OUT=CAMPAIGN/'artifacts/models'


class DeltaDNN(nn.Module):
    def __init__(self, hidden=16):
        super().__init__()
        self.dnn=nn.Sequential(nn.Linear(9,hidden),nn.ReLU(),nn.Linear(hidden,hidden),nn.ReLU(),nn.Linear(hidden,3))
        self.scaling_factor=nn.Parameter(torch.full((3,),.001))
    def step(self,w,cov):
        return w+self.scaling_factor*self.dnn(torch.cat((w,cov),dim=-1))
    def export(self,metadata):
        sd=self.state_dict()
        params={k:sd[v].detach().cpu().numpy().astype(float) for k,v in {
            'A':'dnn.0.weight','a':'dnn.0.bias','B':'dnn.2.weight','b':'dnn.2.bias',
            'C':'dnn.4.weight','cc':'dnn.4.bias','scale':'scaling_factor'}.items()}
        return LearningModel('dnnglm',params,metadata)


def slice_data(d, start=0, end=None):
    n=len(d['choice'])
    return {k:v[start:end] for k,v in d.items() if isinstance(v,np.ndarray) and v.ndim>0 and len(v)==n}


def binary_loss(p,c):
    ok=c!=0; y=(c<0).astype(float); p=np.clip(p,1e-8,1-1e-8)
    return float(np.mean((-y*np.log(p)-(1-y)*np.log1p(-p))[ok])) if ok.any() else float('nan')


def dev_split():
    ids=[s for s in subjects('dev') if (CAMPAIGN/'data/processed/dev'/f'{s}.npz').exists()]
    # This is nested DEVELOPMENT tuning only. Source validation remains sealed.
    val=[s for s in ids if int(hashlib.sha256(('model_dev_cv:'+s).encode()).hexdigest(),16)%5==0]
    train=[s for s in ids if s not in val]
    return train,val


def load_dev(ids,end):
    return [(s,slice_data(load_subject(s,split='dev',purpose='published learning-rule development'),0,end)) for s in ids]


def score_model(model,data,prefix=1000):
    records=[]
    for s,d in data:
        if len(d['choice'])<=prefix:continue
        pr=slice_data(d,0,prefix);fu=slice_data(d,prefix)
        state=model.initial_state(pr)
        p,_,_=model.sequence(fu,state['w'])
        static=static_fit(pr)
        sm=LearningModel('reinforce',{'alpha':np.zeros(3),'baseline':np.zeros(3)})
        pp,_,_=sm.sequence(fu,static)
        records.append(dict(subject=s,n=len(fu['choice']),n_response=int(np.sum(fu['choice']!=0)),conditional_nll=binary_loss(p,fu['choice']),static_nll=binary_loss(pp,fu['choice'])))
    return records


def fit_rl(train,end,maxiter=180,adder_bound=1.5,stable_gain=False,w0_override=None,pure_reward=False):
    # All initial coefficients are estimates from only first200 inputs/outputs;
    # no per-animal future-fitted initialization or learning-rate trajectory.
    dat=[(s,d,(w0_override[s] if w0_override is not None else static_fit(d,n=200))) for s,d in train]
    calls=[0];t0=time.monotonic()
    def objective(theta):
        alpha=theta[:3] if stable_gain or pure_reward else np.exp(theta[:3])
        baseline=np.zeros(3) if pure_reward else (theta[3:]/alpha if stable_gain else theta[3:])
        model=LearningModel('reinforce',{'alpha':alpha,'baseline':baseline})
        loss=[]
        for _,d,w0 in dat:
            p,_,_=model.sequence(d,w0)
            loss.append(binary_loss(p,d['choice']))
        ans=float(np.mean(loss))
        calls[0]+=1
        if calls[0]%50==0: print(json.dumps(dict(fit='reinforce',call=calls[0],nll=ans,seconds=time.monotonic()-t0)),flush=True)
        return ans
    candidates=[]
    if pure_reward:
        starts=[np.array([.01,.01,.005]),np.array([.002,.002,.05])]
        bounds=[(1e-6,.5)]*3
    elif stable_gain:
        starts=[np.array([.01,.01,.005,-.002,-.002,-.001]),np.array([.002,.002,.1,.02,.02,.15])]
        bounds=[(1e-6,.5)]*3+[(-.5,.5)]*3
    else:
        starts=[np.array([*np.log([.004,.004,.004]),-.2,-.2,-.2]),np.array([*np.log([.02,.02,.01]),0.,0.,0.])]
        bounds=[(-12,0)]*3+[(-adder_bound,adder_bound)]*3
    for initial in starts:
        res=minimize(objective,initial,method='L-BFGS-B',bounds=bounds,options={'maxiter':maxiter,'ftol':1e-9})
        candidates.append(res)
    res=min(candidates,key=lambda x:x.fun)
    alpha=res.x[:3] if stable_gain or pure_reward else np.exp(res.x[:3]);baseline=np.zeros(3) if pure_reward else (res.x[3:]/alpha if stable_gain else res.x[3:])
    model=LearningModel('reinforce',{'alpha':alpha,'baseline':baseline},dict(name='REINFORCE_pure' if pure_reward else 'REINFORCE',source='Liu et al.2026 reward-baseline policy gradient;3coefficient mode',end=end,initialization='knowncontrolw0' if w0_override is not None else 'static first200development trials',training_equal_animals=True,fit_nll=float(res.fun),fit_calls=calls[0],adder_bound=adder_bound,stable_gain_parameterization=stable_gain,pure_reward=pure_reward,unrewarded_gain=(alpha*baseline).tolist(),reward_gain=alpha.tolist()))
    return model


def prepare_tensors(data,end):
    n=len(data);T=max(len(d['choice']) for _,d in data)
    s=np.zeros((n,T));c=np.zeros((n,T));r=np.zeros((n,T));day=np.zeros((n,T));mask=np.zeros((n,T));w0=[]
    for i,(_,d) in enumerate(data):
        ss,cc,rr,dd=subject_arrays(d);l=len(cc)
        s[i,:l]=stimulus(ss);c[i,:l]=cc;r[i,:l]=rr;day[i,:l]=dd;mask[i,:l]=(cc!=0)
        w0.append(static_fit(d,n=200))
    y=(c<0).astype(float)
    cov=np.stack((s,np.ones_like(s),day,y,r,(s>0).astype(float)),axis=-1)
    X=np.stack((np.maximum(s,0),np.minimum(s,0),np.ones_like(s)),axis=-1)
    # Equal animal weight: each real response contributes1/n_responses.
    mask=mask/np.maximum(mask.sum(1,keepdims=True),1)
    return [torch.tensor(x,dtype=torch.float32) for x in (cov,X,y,mask,np.asarray(w0))]


def fit_dnn(train,val,end,epochs=120,seed=117,truncation=100,check_every=10,hidden=16):
    torch.manual_seed(seed);np.random.seed(seed);torch.set_num_threads(1)
    model=DeltaDNN(hidden)
    optim=torch.optim.Adam(model.parameters(),lr=.001,weight_decay=1e-5)
    cov,X,y,mask,w0=prepare_tensors(train,end)
    history=[];best=(float('inf'),None,0);t0=time.monotonic()
    for epoch in range(epochs+1):
        if epoch>0:
            w=w0.clone();loss_epoch=0.
            # Source-style truncated backpropagation: accumulate gradients
            # over chunks, detach recurrent coefficients after each chunk,
            # then take ONE Adam step for the full animal batch/epoch.
            # Parameters remain shared over animals/trials; no date-rate path.
            optim.zero_grad()
            for t0chunk in range(0,cov.shape[1],truncation):
                loss=torch.tensor(0.)
                for t in range(t0chunk,min(t0chunk+truncation,cov.shape[1])):
                    logits=torch.sum(w*X[:,t],dim=-1)
                    ll=nn.functional.binary_cross_entropy_with_logits(logits,y[:,t],reduction='none')
                    loss=loss+(ll*mask[:,t]).sum()/len(train)
                    neww=model.step(w,cov[:,t])
                    response=(mask[:,t]>0).float().unsqueeze(-1)
                    w=w+(neww-w)*response
                loss.backward()
                loss_epoch+=float(loss.detach())
                w=w.detach()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            optim.step()
        if epoch%check_every==0 or epoch==epochs:
            numpy_model=model.export(dict(name=f'DNNGLM{hidden}',epoch=epoch,seed=seed,end=end,source_pin='0ae19f7eec2836ab05487cc0342c7d1ac51a2727',source_mode=1,hidden=hidden,truncation=truncation,initialization='static first200development trials',training_equal_animals=True,omissions='masked and skipbinaryupdate'))
            records=score_model(numpy_model,val)
            score=float(np.mean([r['conditional_nll'] for r in records]))
            history.append(dict(epoch=epoch,validation_conditional_nll=score,seconds=time.monotonic()-t0))
            print(json.dumps(dict(fit='dnnglm',seed=seed,**history[-1])),flush=True)
            numpy_model.save(OUT/f'dnn_seed{seed}_epoch{epoch}.npz')
            if score<best[0]:
                best=(score,numpy_model,epoch)
                best[1].save(OUT/f'dnn_seed{seed}_best.npz')
                (OUT/f'dnn_seed{seed}_dev_cv_records.json').write_text(json.dumps(records,indent=2)+'\n')
            (OUT/f'dnn_seed{seed}_fit_history.json').write_text(json.dumps(history,indent=2)+'\n')
    return best[1],history


def source_audit():
    torch.manual_seed(157);torch.set_num_threads(1)
    src=OUT/'source/liu_models.py'
    tree=ast.parse(src.read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='DeltaDNNGLM')
    module=ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[]))
    ns={'torch':torch,'nn':nn};exec(compile(module,str(src),'exec'),ns)
    original=ns['DeltaDNNGLM'](9,16,truncation_len=100,num_layers=2,num_weights_mode=1)
    ours=DeltaDNN(16);ours.load_state_dict(original.state_dict())
    m=ours.export(dict(name='audit'))
    rng=np.random.default_rng(43);N=233
    s=rng.choice([-1,-.25,-.125,0,.125,.25,1],N);choice=rng.choice([-1,1],N);reward=(choice==-np.sign(s)).astype(float);day=np.zeros(N);day[[0,41,117]]=1
    prefix=dict(contrastLeft=np.maximum(-s,0),contrastRight=np.maximum(s,0),choice=choice,feedbackType=reward,session_start=day)
    w0=rng.normal(0,.5,3)
    pr,ws,_=m.sequence(prefix,w0)
    z=stimulus(s);inputs=np.stack((z[1:],z[:-1],np.ones(N-1),day[:-1],(choice[:-1]<0).astype(float),reward[:-1],(z[:-1]>0).astype(float)),axis=-1)[None]
    xx=torch.tensor(inputs,dtype=torch.float32);h=original.init_hidden(xx,torch.tensor(w0,dtype=torch.float32))
    p,dw,w=original(xx,h)
    delta=float(np.max(np.abs(p.detach().numpy()[0,:,0]-pr[1:])))
    wd=float(np.max(np.abs(w.detach().numpy()[0]-ws[1:])))
    if delta>2e-6 or wd>2e-5:raise AssertionError((delta,wd))
    # Vectorized numpy updates must equal scalar recurrence for cloned data.
    st={'w':np.broadcast_to(w0,(7,3)).copy()}
    rec=[]
    for t in range(N):
        rec.append(m.probs(st,np.full(7,s[t])))
        m.update(st,np.full(7,s[t]),np.full(7,choice[t]),np.full(7,reward[t]),np.full(7,day[t]))
    vd=float(np.max(np.abs(np.asarray(rec)[:,0]-pr)))
    if vd>1e-10:raise AssertionError(vd)
    # Original source subtracts baseline; our exported legacy key 'baseline'
    # is an ADDITIVE reward offset, so source_base = -exported_baseline.
    rsrc=OUT/'source/liu_simulate_learning.py'
    rt=ast.parse(rsrc.read_text())
    rf=next(n for n in rt.body if isinstance(n,ast.FunctionDef) and n.name=='reinforce_base')
    rns={'np':np,'expit':expit};exec(compile(ast.fix_missing_locations(ast.Module(body=[rf],type_ignores=[])),str(rsrc),'exec'),rns)
    alpha=np.array([.01,.008,.02]);adder=np.array([-.2,.1,-.4])
    rl=LearningModel('reinforce',{'alpha':alpha,'baseline':adder})
    rp,rw,_=rl.sequence(prefix,w0)
    X=np.stack((np.maximum(z,0),np.minimum(z,0),np.ones(N)),axis=-1)
    originalW=np.zeros((N,3));originalW[0]=w0
    yy=(choice<0).astype(int)
    for i in range(1,N):
        originalW[i]=originalW[i-1]+alpha*rns['reinforce_base'](originalW,X,yy,reward,(z>0).astype(int),i,-adder)
    rd=float(np.max(np.abs(originalW-rw)))
    if rd>1e-10:raise AssertionError(rd)
    omitted=dict(prefix);omitted['choice']=np.zeros(N,dtype=int)
    _,ow,_=m.sequence(omitted,w0)
    od=float(np.max(np.abs(ow-w0)))
    if od!=0:raise AssertionError(od)
    changed=dict(prefix);changed['choice']=choice.copy();changed['feedbackType']=reward.copy()
    changed['choice'][137]*=-1;changed['feedbackType'][137]=1-reward[137]
    cp,_,_=m.sequence(changed,w0)
    causal_before=float(np.max(np.abs(cp[:138]-pr[:138])))
    causal_after=float(np.max(np.abs(cp[138:]-pr[138:])))
    if causal_before!=0 or causal_after==0:raise AssertionError((causal_before,causal_after))
    out=dict(source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),source_pin='0ae19f7eec2836ab05487cc0342c7d1ac51a2727',source_class='DeltaDNNGLM',source_mode=1,hidden=16,synthetic_trials=N,seed=43,prob_max_abs_difference=delta,weight_max_abs_difference=wd,vectorized_vs_scalar_max_abs_difference=vd,reinforce_source_weight_max_abs_difference=rd,reinforce_source_baseline_sign='sourcebase=-exportedbaselineadditiveoffset',omission_extension_skips_update_max_abs_weight_change=od,current_actionreward_perturbation_max_probability_change_at_or_before_trial=causal_before,current_actionreward_perturbation_max_probability_change_after_trial=causal_after,causality='predictionbeforecurrentactionreward;sourceprevtrialcovariateshiftmatched')
    (OUT/'SOURCE_RECURRENCE_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--audit',action='store_true');p.add_argument('--rl',action='store_true');p.add_argument('--dnn',action='store_true');p.add_argument('--end',type=int,default=6000);p.add_argument('--epochs',type=int,default=120);p.add_argument('--seed',type=int,default=117);p.add_argument('--max-animals',type=int);p.add_argument('--check-every',type=int,default=10);p.add_argument('--truncation',type=int,default=100);p.add_argument('--adder-bound',type=float,default=1.5);p.add_argument('--all-dev-refit',action='store_true');p.add_argument('--stable-gain',action='store_true');p.add_argument('--pure-reward',action='store_true');p.add_argument('--hidden',type=int,default=16)
    a=p.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    if a.audit:source_audit()
    if not(a.rl or a.dnn):return
    train_ids,val_ids=dev_split()
    if a.all_dev_refit:
        train_ids=subjects('dev')
    if a.max_animals:train_ids=train_ids[:a.max_animals];val_ids=val_ids[:min(4,len(val_ids))]
    train=load_dev(train_ids,a.end);val=load_dev(val_ids,a.end)
    (OUT/'DEVELOPMENT_MODEL_SPLIT.json').write_text(json.dumps(dict(train=train_ids,validation=val_ids,end=a.end,validation_is_development_only=True),indent=2)+'\n')
    print(json.dumps(dict(train_animals=len(train),validation_animals=len(val),end=a.end,train_trials=sum(len(d['choice']) for _,d in train))),flush=True)
    if a.rl:
        m=fit_rl(train,a.end,adder_bound=a.adder_bound,stable_gain=a.stable_gain,pure_reward=a.pure_reward);suffix='pure_nested' if a.pure_reward else (('all_dev' if a.all_dev_refit else 'nested_stable') if a.stable_gain else ('all_dev' if a.all_dev_refit else ('nested_train' if a.adder_bound==1.5 else 'nested_wide')));m.save(OUT/f'reinforce_{suffix}.npz');records=score_model(m,val)
        (OUT/f'reinforce_{suffix}_dev_cv_records.json').write_text(json.dumps(records,indent=2)+'\n')
        print(json.dumps(dict(model=m.name,params={k:v.tolist() for k,v in m.params.items()},dev_cv_conditional_nll=np.mean([r['conditional_nll'] for r in records]),static_nll=np.mean([r['static_nll'] for r in records]))),flush=True)
    if a.dnn:
        m,h=fit_dnn(train,val,a.end,a.epochs,a.seed,truncation=a.truncation,check_every=a.check_every,hidden=a.hidden)
        print(json.dumps(dict(best_model=m.metadata)),flush=True)

if __name__=='__main__':main()
