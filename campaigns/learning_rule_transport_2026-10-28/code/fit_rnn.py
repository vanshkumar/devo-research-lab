#!/usr/bin/env python3
"""Postvalidation strongest-architecture challenge; DEVELOPMENT DATA ONLY.

No first-stage frozen source file is modified. One source-default RNN seed,
fixed training budget, source optimizer, nested development checkpoint choice.
"""
from pathlib import Path
import argparse,ast,hashlib,json,time
import numpy as np
import torch
from torch import nn
from data_io import load_subject
from fit_learning import prepare_tensors, slice_data, binary_loss
from learning_models import static_fit,stimulus
from rnn_learning import RNNLearningModel,load_rnn

CAMPAIGN=Path(__file__).resolve().parents[1]
OUT=CAMPAIGN/'artifacts/rnn'
SOURCE=CAMPAIGN/'artifacts/models/source/liu_models.py'


def source_class():
    t=ast.parse(SOURCE.read_text());c=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='DeltaRNNGLM')
    ns={'torch':torch,'nn':nn};exec(compile(ast.fix_missing_locations(ast.Module(body=[c],type_ignores=[])),str(SOURCE),'exec'),ns)
    return ns['DeltaRNNGLM']


class SourceRNNCell(nn.Module):
    """Exact one-layer GRU source recurrence; GRUCell avoids sequence wrappers."""
    def __init__(self,hidden=32):
        super().__init__();self.gru=nn.GRUCell(9,hidden)
        self.dnn=nn.Sequential(nn.Linear(hidden,hidden),nn.ReLU(),nn.Linear(hidden,hidden),nn.ReLU(),nn.Linear(hidden,3))
        self.fc=nn.Linear(hidden,3,bias=False) # present but unused in original RNN-first mode
        self.scaling_factor=nn.Parameter(torch.full((3,),.001))
    def forward(self,w,h,cov):
        hn=self.gru(torch.cat((w,cov),dim=-1),h)
        return w+self.scaling_factor*self.dnn(hn),hn
    @torch.jit.export
    def block(self,w,h,cov,X,y,mask):
        loss=w.new_zeros(())
        for t in range(cov.size(1)):
            logits=torch.sum(w*X[:,t],dim=-1)
            ll=nn.functional.binary_cross_entropy_with_logits(logits,y[:,t],reduction='none')
            loss=loss+(ll*mask[:,t]).sum()/mask.size(0)
            nw,nh=self.forward(w,h,cov[:,t]);responded=(mask[:,t]>0).to(w.dtype).unsqueeze(-1)
            w=w+(nw-w)*responded;h=h+(nh-h)*responded
        return loss,w,h
    def from_source(self,source):
        sd=source.state_dict();self.load_state_dict({k.replace('_l0',''):v for k,v in sd.items()})
        return self
    def export(self,metadata):
        sd=self.state_dict();mp={'Wih':'gru.weight_ih','Whh':'gru.weight_hh','bih':'gru.bias_ih','bhh':'gru.bias_hh',
           'A':'dnn.0.weight','a':'dnn.0.bias','B':'dnn.2.weight','b':'dnn.2.bias','C':'dnn.4.weight','cc':'dnn.4.bias','scale':'scaling_factor'}
        return RNNLearningModel({k:sd[v].detach().cpu().numpy().astype(float) for k,v in mp.items()},metadata)


def load_dev(ids,end):
    return [(s,slice_data(load_subject(s,split='dev',purpose='postvalidation RNN challenge development ONLY'),0,end)) for s in ids]


def cv_score(m,data):
    records=[]
    for subject,d in data:
        if len(d['choice'])<=1000:continue
        prefix=slice_data(d,0,1000);future=slice_data(d,1000)
        state=m.initial_state(prefix);p,_,_=m.sequence(future,state)
        records.append(dict(subject=subject,n=len(future['choice']),n_response=int((future['choice']!=0).sum()),conditional_nll=binary_loss(p,future['choice'])))
    return records


def audit(fitted_path=None):
    torch.manual_seed(557);torch.set_num_threads(1)
    original=source_class()(9,32,num_layers=2,truncation_len=500,num_weights_mode=1,DNNfirst=False)
    if fitted_path:
        fitted=load_rnn(fitted_path);sd=original.state_dict()
        mp={'Wih':'gru.weight_ih_l0','Whh':'gru.weight_hh_l0','bih':'gru.bias_ih_l0','bhh':'gru.bias_hh_l0','A':'dnn.0.weight','a':'dnn.0.bias','B':'dnn.2.weight','b':'dnn.2.bias','C':'dnn.4.weight','cc':'dnn.4.bias','scale':'scaling_factor'}
        for k,v in mp.items():sd[v]=torch.tensor(fitted.params[k],dtype=torch.float32)
        original.load_state_dict(sd)
    ours=SourceRNNCell().from_source(original);numpy_model=ours.export(dict(role='source audit'))
    rng=np.random.default_rng(701);N=511
    s=rng.choice([-1,-.25,-.125,0,.125,.25,1],N);c=rng.choice([-1,1],N);r=rng.choice([-1,1],N);day=np.zeros(N);day[[0,73,210]]=1
    data=dict(contrastLeft=np.maximum(-s,0),contrastRight=np.maximum(s,0),choice=c,feedbackType=r,session_start=day)
    w0=np.array([.7,.3,-.5]);z=stimulus(s)
    probs,ws,end=numpy_model.sequence(data,w0)
    cov=np.stack((z,np.ones(N),day,(c<0).astype(float),(r>0).astype(float),(z>0).astype(float)),axis=-1)
    xx=torch.tensor(np.concatenate((z[1:,None],cov[:-1]),axis=1)[None],dtype=torch.float32)
    op,_,ow=original(xx,original.init_hidden(xx,torch.tensor(w0[None],dtype=torch.float32)))
    pd=float(np.max(np.abs(op.detach().numpy()[0,:,0]-probs[1:])))
    wd=float(np.max(np.abs(ow.detach().numpy()[0]-ws[1:])))
    tw=torch.tensor(w0[None],dtype=torch.float32);th=torch.zeros((1,32));ts=[]
    for t in range(N):
        ts.append(tw.detach().numpy()[0]);tw,th=ours(tw,th,torch.tensor(cov[t:t+1],dtype=torch.float32))
    cellwd=float(np.max(np.abs(np.asarray(ts)-ws)))
    hd=float(np.max(np.abs(th.detach().numpy()[0]-end['h'])))
    st={'w':np.broadcast_to(w0,(9,3)).copy(),'h':np.zeros((9,32))};vp=[]
    for t in range(N):
        vp.append(numpy_model.probs(st,np.full(9,s[t])))
        numpy_model.update(st,np.full(9,s[t]),np.full(9,c[t]),np.full(9,r[t]),np.full(9,day[t]))
    vd=float(np.max(np.abs(np.asarray(vp)[:,0]-probs)))
    hbatch=float(np.max(np.abs(st['h'][0]-end['h'])))
    omitted=dict(data);omitted['choice']=np.zeros(N,dtype=int);_,_,ost=numpy_model.sequence(omitted,w0)
    assert pd<2e-6 and wd<2e-5 and cellwd<2e-5 and hd<2e-6 and vd<1e-10 and hbatch<1e-10,(pd,wd,cellwd,hd,vd,hbatch)
    assert np.array_equal(ost['w'],w0) and not ost['h'].any()
    # The scripted block removes Python iteration but keeps the same loss,
    # recurrence and full within-block gradient as eager per-trial training.
    scripted=torch.jit.script(ours);n=31;bs=4
    tc=torch.tensor(np.broadcast_to(cov[:n],(bs,n,6)).copy(),dtype=torch.float32)
    tf=torch.tensor(np.broadcast_to(np.stack((np.maximum(z[:n],0),np.minimum(z[:n],0),np.ones(n)),axis=-1),(bs,n,3)).copy(),dtype=torch.float32)
    ty=torch.tensor(np.broadcast_to((c[:n]<0).astype(float),(bs,n)).copy(),dtype=torch.float32)
    tm=torch.ones((bs,n))/n;mw=torch.tensor(np.broadcast_to(w0,(bs,3)).copy(),dtype=torch.float32);mh=torch.zeros((bs,32))
    sl,sw,sh=scripted.block(mw,mh,tc,tf,ty,tm);sl.backward();sg={k:p.grad.detach().clone() for k,p in ours.named_parameters() if p.grad is not None};ours.zero_grad()
    ew=mw.clone();eh=mh.clone();el=ew.new_zeros(())
    for t in range(n):
        logits=(ew*tf[:,t]).sum(-1);el=el+(nn.functional.binary_cross_entropy_with_logits(logits,ty[:,t],reduction='none')*tm[:,t]).sum()/bs
        ew,eh=ours(ew,eh,tc[:,t])
    el.backward();gd=max(float(torch.max(torch.abs(p.grad-sg[k]))) for k,p in ours.named_parameters() if p.grad is not None)
    ld=float(torch.abs(el-sl));assert gd<1e-7 and ld<1e-7,(gd,ld)
    out=dict(architecture='exact source DeltaRNNGLM RNNfirst, GRU32,2ReLU32,num_weights_mode1',source_pin='0ae19f7eec2836ab05487cc0342c7d1ac51a2727',source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),trials=N,seed=701,
      original_vs_numpy_probability_max_abs=pd,original_vs_numpy_weight_max_abs=wd,GRUCell_vs_numpy_weight_max_abs=cellwd,GRUCell_vs_numpy_hidden_max_abs=hd,
      vectorized_vs_scalar_probability_max_abs=vd,vectorized_vs_scalar_hidden_max_abs=hbatch,scripted_vs_eager_block_loss_difference=ld,scripted_vs_eager_gradient_max_abs=gd,omission_extension='skip both hidden and weight update; observations retained',parameters=sum(p.numel() for p in ours.parameters()),post_source_validation_challenge=True)
    if fitted_path:out.update(fitted_model=str(Path(fitted_path).resolve().relative_to(CAMPAIGN)),fitted_model_sha256=hashlib.sha256(Path(fitted_path).read_bytes()).hexdigest())
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'SOURCE_RECURRENCE_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)


def fit(train,val,end=6000,epochs=1000,seed=557,check_every=25,tag='main',use_script=True):
    torch.manual_seed(seed);np.random.seed(seed);torch.set_num_threads(1)
    original=source_class()(9,32,num_layers=2,truncation_len=500,num_weights_mode=1,DNNfirst=False)
    model=SourceRNNCell().from_source(original)
    runner=torch.jit.script(model) if use_script else model
    optimizer=torch.optim.Adam(model.parameters(),lr=.001)
    scheduler=torch.optim.lr_scheduler.StepLR(optimizer,step_size=5,gamma=.999)
    cov,X,y,mask,w0=prepare_tensors(train,end);history=[];best=float('inf');start=time.monotonic()
    for epoch in range(epochs+1):
        epoch_start=time.monotonic();loss_epoch=0.
        if epoch:
            w=w0.clone();h=torch.zeros((len(train),32));optimizer.zero_grad()
            for t0 in range(0,cov.shape[1],500):
                t1=min(t0+500,cov.shape[1])
                loss,w,h=runner.block(w,h,cov[:,t0:t1],X[:,t0:t1],y[:,t0:t1],mask[:,t0:t1])
                if not torch.isfinite(loss):raise FloatingPointError('Nonfinite RNN training likelihood')
                loss.backward();loss_epoch+=float(loss.detach());w=w.detach();h=h.detach()
            if not all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters()):raise FloatingPointError('Nonfinite RNN gradient')
            optimizer.step();scheduler.step()
        if epoch%check_every==0 or epoch==epochs:
            m=model.export(dict(name='RNNGLM32',source_pin='0ae19f7eec2836ab05487cc0342c7d1ac51a2727',hidden=32,num_weights_mode=1,DNNfirst=False,num_dnn_layers=2,epoch=epoch,seed=seed,end=end,truncation=500,
                optimizer='Adam lr.001,StepLR5gamma.999,noweightdecay,noclip',initialization='static first200development trials;prefix-onlyW0MAP atprediction',post_source_validation_challenge=True,
                validation_access='development only; source holdouts consumed in prior stage by lead; no external outcomes',omissions='skiphiddenandweightupdates;full observationcategorypreserved'))
            records=cv_score(m,val);score=float(np.mean([r['conditional_nll'] for r in records]))
            record=dict(epoch=epoch,train_nll=loss_epoch if epoch else None,development_conditional_nll=score,seconds=time.monotonic()-start,last_epoch_seconds=time.monotonic()-epoch_start,lr=float(optimizer.param_groups[0]['lr']))
            history.append(record);print(json.dumps(record),flush=True)
            m.save(OUT/f'{tag}_epoch{epoch}.npz')
            if score<best:
                best=score;m.save(OUT/f'{tag}_best.npz');(OUT/f'{tag}_cv_records.json').write_text(json.dumps(records,indent=2)+'\n')
            (OUT/f'{tag}_history.json').write_text(json.dumps(history,indent=2)+'\n')
    return history


def audit_fitted(path):
    """Compare the selected fitted export with exact original source code."""
    torch.set_num_threads(1);m=load_rnn(path);original=source_class()(9,32,num_layers=2,truncation_len=500,num_weights_mode=1,DNNfirst=False)
    sd=original.state_dict();mp={'Wih':'gru.weight_ih_l0','Whh':'gru.weight_hh_l0','bih':'gru.bias_ih_l0','bhh':'gru.bias_hh_l0','A':'dnn.0.weight','a':'dnn.0.bias','B':'dnn.2.weight','b':'dnn.2.bias','C':'dnn.4.weight','cc':'dnn.4.bias','scale':'scaling_factor'}
    for k,v in mp.items():sd[v]=torch.tensor(m.params[k],dtype=torch.float32)
    original.load_state_dict(sd)
    d=load_dev(['CSHL053'],6000)[0][1];prefix=slice_data(d,0,1000);st=m.initial_state(prefix)
    pr,_,_=m.sequence(d,st['w0'])
    from learning_models import subject_arrays
    s,c,r,day=subject_arrays(d);ok=c!=0;indices=np.flatnonzero(ok);s,c,r,day=s[ok],c[ok],r[ok],day[ok];z=stimulus(s)
    cov=np.stack((z,np.ones(len(z)),day,(c<0).astype(float),r,(z>0).astype(float)),axis=-1)
    xx=torch.tensor(np.concatenate((z[1:,None],cov[:-1]),axis=1)[None],dtype=torch.float32)
    with torch.no_grad():op,_,_=original(xx,original.init_hidden(xx,torch.tensor(st['w0'][None],dtype=torch.float32)))
    pp=op.numpy()[0,:,0];target=pr[ok][1:];future=indices[1:]>=1000
    pd=float(np.max(np.abs(pp-target)));nll_source=binary_loss(pp[future],c[1:][future]);nll_numpy=binary_loss(target[future],c[1:][future])
    assert pd<2e-5 and abs(nll_source-nll_numpy)<2e-6,(pd,nll_source,nll_numpy)
    out=dict(model=str(Path(path).resolve().relative_to(CAMPAIGN)),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),development_subject='CSHL053',trials=len(d['choice']),responding_trials=int(ok.sum()),prefix_n=1000,
        original_source_vs_numpy_probability_max_abs=pd,original_source_future_response_nll=nll_source,numpy_future_response_nll=nll_numpy,absolute_nll_difference=abs(nll_source-nll_numpy),omission_mapping='Original source class applied to responding subsequence; omitted trials leavebothstatesunchanged;fulltrialexposureindexretained',source_or_external_outcomes_accessed=False)
    (OUT/'FITTED_SOURCE_RECURRENCE_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)


def audit_closed_loop(path):
    """Known-answer self-generated choices/feedback against source modules."""
    torch.set_num_threads(1);m=load_rnn(path);original=source_class()(9,32,num_layers=2,truncation_len=500,num_weights_mode=1,DNNfirst=False)
    sd=original.state_dict();mp={'Wih':'gru.weight_ih_l0','Whh':'gru.weight_hh_l0','bih':'gru.bias_ih_l0','bhh':'gru.bias_hh_l0','A':'dnn.0.weight','a':'dnn.0.bias','B':'dnn.2.weight','b':'dnn.2.bias','C':'dnn.4.weight','cc':'dnn.4.bias','scale':'scaling_factor'}
    for k,v in mp.items():sd[v]=torch.tensor(m.params[k],dtype=torch.float32)
    original.load_state_dict(sd)
    rng=np.random.default_rng(7901);n=2000;s=rng.choice([-1,-.25,-.125,-.0625,.0625,.125,.25,1],n);uniform=rng.random(n)
    st={'w':np.array([.7,.3,-.5]),'h':np.zeros(32)};tw=torch.tensor(st['w'][None],dtype=torch.float32);th=torch.zeros((1,1,32));diff=[];mismatches=0;reward_mismatches=0
    with torch.no_grad():
        for t in range(n):
            z=float(stimulus(s[t]));x=torch.tensor([[max(z,0.),min(z,0.),1.]],dtype=torch.float32)
            pt=float(torch.sigmoid(torch.sum(tw*x)));pn=float(m.probs(st,s[t]));diff.append(abs(pt-pn))
            ct=-1 if uniform[t]<pt else 1;cn=-1 if uniform[t]<pn else 1
            if t%113==0:ct=0;cn=0
            rt=1 if ct==-int(np.sign(s[t])) else -1;rn=1 if cn==-int(np.sign(s[t])) else -1
            mismatches+=ct!=cn;reward_mismatches+=rt!=rn
            start=t%500==0
            m.update(st,s[t],cn,rn,start)
            if ct!=0:
                cov=torch.tensor([[z,1.,float(start),float(ct<0),float(rt>0),float(z>0)]],dtype=torch.float32)
                _,th=original.gru(torch.cat((tw,cov),dim=-1).unsqueeze(1),th)
                tw=tw+original.scaling_factor*original.dnn(th[-1])
    pd=max(diff);wd=float(np.max(np.abs(tw.numpy()[0]-st['w'])));hd=float(np.max(np.abs(th.numpy()[0,0]-st['h'])))
    assert not mismatches and not reward_mismatches and pd<5e-5 and wd<1e-4 and hd<1e-4,(mismatches,pd,wd,hd)
    out=dict(model_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),trials=n,seed=7901,policy='fixed independent nonzero contrasts;sharedchoiceuniforms;generatedownfeedback;periodicomissionextension',choice_mismatches=mismatches,reward_mismatches=reward_mismatches,source_vs_numpy_max_probability_difference=pd,final_weight_difference=wd,final_hidden_difference=hd,animal_outcomes_accessed=False)
    (OUT/'CLOSED_LOOP_SOURCE_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--audit',action='store_true');p.add_argument('--audit-source-model');p.add_argument('--audit-fitted');p.add_argument('--audit-closed-loop');p.add_argument('--fit',action='store_true');p.add_argument('--end',type=int,default=6000);p.add_argument('--epochs',type=int,default=1000);p.add_argument('--seed',type=int,default=557);p.add_argument('--check-every',type=int,default=25);p.add_argument('--max-animals',type=int);p.add_argument('--tag',default='main');p.add_argument('--no-script',action='store_true');a=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if a.audit:audit()
    if a.audit_source_model:audit(a.audit_source_model)
    if a.audit_fitted:audit_fitted(a.audit_fitted)
    if a.audit_closed_loop:audit_closed_loop(a.audit_closed_loop)
    if a.fit:
        allocation=json.loads((CAMPAIGN/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json').read_text());train=allocation['train'];val=allocation['validation']
        if a.max_animals:train=train[:a.max_animals];val=val[:4]
        ds=load_dev(train,a.end);dv=load_dev(val,a.end)
        (OUT/f'{a.tag}_ALLOCATION.json').write_text(json.dumps(dict(train=train,validation=val,end=a.end,seed=a.seed,post_source_validation_challenge=True,source_outcomes_accessed=False,external_outcomes_accessed=False),indent=2)+'\n')
        print(json.dumps(dict(train_animals=len(ds),development_validation_animals=len(dv),trials=sum(len(d['choice']) for _,d in ds),end=a.end,epochs=a.epochs)),flush=True)
        fit(ds,dv,a.end,a.epochs,a.seed,a.check_every,a.tag,not a.no_script)

if __name__=='__main__':main()
