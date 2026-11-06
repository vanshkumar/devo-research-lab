"""Local exact drift/diffusion diagnostics for frozen learning-rule artifacts.

This is not a forecast evaluation or a proof of DNN failure. It enumerates
possible self-generated actions/rewards at a fixed current state. Optional
empirical access is DEVELOPMENT PREFIX ONLY, directly limited in original
Parquet queries to the first1000 task trials. No source validation or external
outcome loader is imported or called.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path
import numpy as np
from scipy.special import expit, logit
from learning_models import LearningModel, features, subject_arrays

CAMPAIGN=Path(__file__).resolve().parents[1]
ROOT=CAMPAIGN.parents[1]
OUT=CAMPAIGN/'artifacts/drift'
STIMULI=[-1.,-.5,-.25,-.125,-.0625,0.,.0625,.125,.25,.5,1.]


def json_write(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else float(x))+'\n')


def csv_write(path,records):
    keys=list(records[0]) if records else []
    with open(path,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(records)


def snapshot_model(path):
    """Read artifact once so provenance and loaded parameters use exact bytes."""
    path=Path(path);raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    with np.load(io.BytesIO(raw),allow_pickle=False) as z:
        model=LearningModel(str(z['kind']),{k:np.asarray(z[k],float) for k in z.files if k not in ('kind','metadata')},json.loads(str(z['metadata'])))
    p=OUT/'model_snapshots'/path.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    return model,dict(original_path=str(path),snapshot_path=str(p),sha256=sha,kind=model.kind,metadata=model.metadata)


def outcome_deltas(model,w,s,omission=.05,day=False,teacher_p_right=None):
    """Exact outcomes. At zero, hidden rewarded side is independent50:50."""
    w=np.asarray(w,float)
    p=float(model.probs({'w':w},float(s)))
    q=p if teacher_p_right is None else float(teacher_p_right)
    probs=[];deltas=[];choices=[];rewards=[]
    sides=[(-1,.5),(1,.5)] if s==0 else [(int(np.sign(s)),1.)]
    for side,sideprob in sides:
        for raw,actionprob in [(-1,q),(1,1-q)]:
            feedback=1 if raw==-side else -1
            st={'w':w.copy()};model.update(st,float(s),raw,feedback,day)
            probs.append((1-omission)*sideprob*actionprob)
            deltas.append(st['w']-w);choices.append(raw);rewards.append(int(feedback>0))
    probs.append(omission);deltas.append(np.zeros(3));choices.append(0);rewards.append(0)
    return p,np.asarray(probs),np.asarray(deltas),choices,rewards


def exact_moments(model,w,s,omission=.05,day=False,teacher_p_right=None):
    p,prob,dw,choices,rewards=outcome_deltas(model,w,s,omission,day,teacher_p_right)
    mu=np.sum(prob[:,None]*dw,axis=0)
    second=np.einsum('n,ni,nj->ij',prob,dw,dw)
    cov=second-np.outer(mu,mu)
    # Compare observable current proficiency before/after one random update.
    # This includes nonlinear effects of action diffusion, not just mean drift.
    before=[];after=[]
    for probe in [-1.,1.]:
        pr=float(model.probs({'w':np.asarray(w)},probe))
        pn=model.probs({'w':np.asarray(w)[None,:]+dw},np.full(len(dw),probe))
        before.append(1-pr if probe<0 else pr)
        after.append(float(np.sum(prob*(1-pn if probe<0 else pn))))
    return dict(p_right=p,mean_dw=mu,cov_dw=cov,second_dw=second,
                probe_correct_before=np.asarray(before),
                probe_correct_change=np.asarray(after)-before,
                outcome_prob=prob,outcome_dw=dw)


def analytic_rl(model,w,s,omission=.05,teacher_p_right=None):
    p=float(model.probs({'w':np.asarray(w,float)},float(s)))
    q=p if teacher_p_right is None else float(teacher_p_right)
    a=model.params['alpha']*model.params['baseline'];b=model.params['alpha']
    if s==0:
        reward_innovation=.5*(q-p)
    elif s>0:
        reward_innovation=q*(1-p)
    else:
        reward_innovation=-(1-q)*p
    history=(1-omission)*a*(q-p)*features(float(s))
    reward=(1-omission)*b*reward_innovation*features(float(s))
    return history,reward


def row_for(modelname,statetype,label,w,s,omission,day,m):
    sd=np.sqrt(np.maximum(np.diag(m['cov_dw']),0))
    r=dict(model=modelname,state_type=statetype,state_label=label,stimulus=s,omission=omission,
           session_start=int(day),w_right=w[0],w_left=w[1],w_bias=w[2],p_right=m['p_right'])
    for j,n in enumerate(['right','left','bias']):
        r['mean_dw_'+n]=m['mean_dw'][j];r['sd_dw_'+n]=sd[j]
        r['frozen_state_1000_step_snr_'+n]=(np.sqrt(1000)*m['mean_dw'][j]/sd[j]) if sd[j]>0 else 0.
    r.update(mean_probe_correct_before=float(np.mean(m['probe_correct_before'])),
             one_update_left_correct_change_pp=100*m['probe_correct_change'][0],
             one_update_right_correct_change_pp=100*m['probe_correct_change'][1],
             one_update_mean_correct_change_pp=100*float(np.mean(m['probe_correct_change'])),
             diffusion_trace=float(np.trace(m['cov_dw'])))
    return r


def read_dev_prefixes(n=8,prefix_n=1000):
    """Input-selected development animals; SQL never returns future outcomes."""
    sys.path.insert(0,str(ROOT/'sources/longitudinal_learning_feasibility_2026-10-28/tools'))
    import duckdb
    split=json.loads((CAMPAIGN/'protocols/SPLIT.json').read_text())
    allowed={r['subject'] for r in split['standard'] if r['split']=='dev'}
    coverage=json.loads((CAMPAIGN/'data/COVERAGE.json').read_text())
    candidates=[r['subject'] for r in coverage if r['subject'] in allowed and r['trials']>=prefix_n]
    selected=sorted(candidates,key=lambda s:hashlib.sha256(('drift_prefix:'+s).encode()).hexdigest())[:n]
    index=json.loads((CAMPAIGN/'data/INDEX.json').read_text());con=duckdb.connect()
    animals={};records=[]
    for subject in selected:
        rs=sorted([r for r in index if r['subject']==subject and r['kind']=='table'],key=lambda r:(r['date'],r['number']))
        fields=['contrastLeft','contrastRight','choice','feedbackType','rewardVolume']
        accum=[];session=[];left=prefix_n;session_start=[]
        for j,r in enumerate(rs):
            if left<=0:break
            path=CAMPAIGN/r['path'];raw=path.read_bytes()
            vals=con.execute('SELECT '+','.join(fields)+f" FROM read_parquet('{path}') LIMIT {left}").fetchall()
            a=np.asarray(vals,float);t=len(a)
            if not t:continue
            accum.append(a);session.extend([j]*t);session_start.extend([True]+[False]*(t-1));left-=t
            records.append(dict(subject=subject,split='dev',path=str(path),sha256=hashlib.sha256(raw).hexdigest(),
                                fields=fields,rows_returned=t,sql_limit=left+t,purpose='drift prefix-only localization'))
        a=np.concatenate(accum);assert len(a)==prefix_n
        d={k:a[:,j] for j,k in enumerate(fields)}
        d['session']=np.asarray(session);d['session_start']=np.asarray(session_start)
        animals[subject]=d
    json_write(OUT/'PREFIX_EXPOSURE.json',dict(scope='development first1000trials only; no validation/external outcomes',selected=selected,records=records))
    return animals


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--models',nargs='+',default=['dnnglm_nested_best.npz','reinforce_nested_stable.npz','reinforce_pure_nested.npz'])
    parser.add_argument('--dev-prefixes',type=int,default=8)
    parser.add_argument('--mc-actions',type=int,default=50000)
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    models={};provenance=[]
    for name in args.models:
        path=Path(name)
        if not path.is_file():path=CAMPAIGN/'artifacts/models'/name
        model,prov=snapshot_model(path);models[path.stem]=model;provenance.append(prov)
    json_write(OUT/'MODEL_MANIFEST.json',provenance)
    prefixes=read_dev_prefixes(args.dev_prefixes) if args.dev_prefixes else {}
    states={};coefrows=[];prefixrows=[]
    grid=[(np.array([skill,skill,bias]),f'symmetric_skill{skill}_bias{bias}') for skill in [0.,.5,1.,2.,4.] for bias in [-2.,-1.,0.,1.,2.]]
    grid += [(np.array([wr,wl,bias]),f'asymmetric_{wr}_{wl}_bias{bias}') for wr,wl in [(0.,2.),(2.,0.),(1.,3.),(3.,1.)] for bias in [-1.,0.,1.]]
    grid += [(np.array([logit(.99),logit(.99),0.]),'symmetric_99percent_correct')]
    for name,model in models.items():
        states[name]=[('grid',label,w) for w,label in grid]
        if model.kind=='reinforce':
            for j,co in enumerate(['right','left','bias']):
                alpha=float(model.params['alpha'][j]);a=alpha*float(model.params['baseline'][j])
                coefrows.append(dict(model=name,coefficient=co,reward_independent_gain_a=a,reward_gain_b=alpha,
                                     ratio_a_over_b=a/alpha,own_mean_drift_depends_on='b only; a contributes diffusion'))
        for subject,d in prefixes.items():
            st=model.initial_state(d);w=st['w'];states[name].append(('development_prefix',subject,w))
            s,c,r,day=subject_arrays(d);p,ws,end=model.sequence(d,st['w0'])
            before=ws.copy();act={'w':ws.copy()};model.update(act,s,c,np.asarray(d['feedbackType']),day)
            actual=act['w']-before
            # Conditional on the actual PREFIX input sides only. Zero has
            # assigned side from its input column, never future feedback.
            sides=np.where(np.isfinite(d['contrastLeft']),-1,1)
            expected=np.zeros_like(ws);second=np.zeros((len(c),3,3))
            omit=float(np.mean(c==0))
            for raw,pr in [(-1,p),(1,1-p)]:
                uu={'w':ws.copy()};fb=np.where(raw==-sides,1,-1)
                model.update(uu,s,np.full(len(s),raw),fb,day)
                dd=uu['w']-ws;prob=(1-omit)*pr
                expected+=prob[:,None]*dd
                second+=np.einsum('n,ni,nj->nij',prob,dd,dd)
            cov=second-np.einsum('ni,nj->nij',expected,expected)
            row=dict(model=name,subject=subject,observed_prefix_trials=len(c),observed_prefix_omission=omit,
                     scope='in-sample permitted prefix; not a future forecast')
            for j,co in enumerate(['right','left','bias']):
                row['actual_conditional_mean_dw_'+co]=float(actual[:,j].mean())
                row['own_action_expected_mean_dw_'+co]=float(expected[:,j].mean())
                row['own_action_rms_sd_dw_'+co]=float(np.sqrt(np.maximum(cov[:,j,j],0).mean()))
                row['prefix_endpoint_'+co]=float(w[j])
            prefixrows.append(row)
    rows=[];teacherrows=[];formula_error=0.
    for name,model in models.items():
        for statetype,label,w in states[name]:
            for day in [False,True]:
                for s in STIMULI:
                    m=exact_moments(model,w,s,.05,day)
                    rows.append(row_for(name,statetype,label,w,s,.05,day,m))
                    if model.kind=='reinforce':
                        a,b=analytic_rl(model,w,s,.05)
                        formula_error=max(formula_error,float(np.max(np.abs(m['mean_dw']-(a+b)))))
                    # A teacher can have different competence from this model.
                    # This is a hypothetical conditional observer diagnostic,
                    # not a fit to any future animal choices.
                    if statetype=='grid' and not day and abs(s)==1:
                        for correct_rate in [.5,.7,.9,.99]:
                            q=correct_rate if s>0 else 1-correct_rate
                            mm=exact_moments(model,w,s,.05,day,q)
                            rr=row_for(name,'hypothetical_teacher',label,w,s,.05,day,mm)
                            rr['teacher_correct_probability']=correct_rate
                            rr['teacher_p_right']=q
                            if model.kind=='reinforce':
                                hist,rew=analytic_rl(model,w,s,.05,q)
                                formula_error=max(formula_error,float(np.max(np.abs(mm['mean_dw']-(hist+rew)))))
                                for j,co in enumerate(['right','left','bias']):
                                    rr['history_component_'+co]=hist[j];rr['reward_component_'+co]=rew[j]
                            else:
                                for co in ['right','left','bias']:
                                    rr['history_component_'+co]='';rr['reward_component_'+co]=''
                            teacherrows.append(rr)
    assert formula_error<1e-12
    csv_write(OUT/'EXACT_LOCAL_DRIFT.csv',rows)
    csv_write(OUT/'HYPOTHETICAL_TEACHER_DRIFT.csv',teacherrows)
    csv_write(OUT/'RL_GAIN_DECOMPOSITION.csv',coefrows)
    csv_write(OUT/'PREFIX_CONDITIONAL_VS_OWN_DRIFT.csv',prefixrows)
    # Seeded Monte Carlo samples exercise actual action/reward/update code.
    rng=np.random.default_rng(51691);mc=[]
    cases=[(np.array([.5,.5,0.]),s,False) for s in [-1.,0.,1.]]
    cases += [(np.array([logit(.99),logit(.99),0.]),s,False) for s in [-1.,1.]]
    cases += [(np.array([1.,3.,1.]),s,True) for s in [-.125,.125]]
    for name,model in models.items():
        for case,(w,s,day) in enumerate(cases):
            n=args.mc_actions;exact=exact_moments(model,w,s,.05,day)
            p=exact['p_right'];raw=np.where(rng.random(n)<p,-1,1)
            raw[rng.random(n)<.05]=0
            side=np.where(rng.random(n)<.5,-1,1) if s==0 else np.full(n,int(np.sign(s)))
            feedback=np.where(raw==-side,1,-1)
            state={'w':np.broadcast_to(w,(n,3)).copy()}
            model.update(state,np.full(n,s),raw,feedback,np.full(n,day))
            delta=state['w']-w;mean=delta.mean(0)
            se=np.sqrt(np.maximum(np.diag(exact['cov_dw']),0)/n)
            z=np.divide(mean-exact['mean_dw'],se,out=np.zeros(3),where=se>1e-15)
            assert np.max(np.abs(z))<6, (name,case,z)
            products=np.einsum('ni,nj->nij',exact['outcome_dw'],exact['outcome_dw'])
            second4=np.einsum('n,nij->ij',exact['outcome_prob'],products**2)
            second_se=np.sqrt(np.maximum(second4-exact['second_dw']**2,0)/n)
            mc_second=np.einsum('ni,nj->ij',delta,delta)/n
            second_z=np.divide(mc_second-exact['second_dw'],second_se,out=np.zeros((3,3)),where=second_se>1e-15)
            assert np.max(np.abs(second_z))<6, (name,case,second_z)
            mc.append(dict(model=name,case=case,stimulus=s,state=w.tolist(),session_start=day,
                           own_p_right=p,omission=.05,actions=n,exact_mean_dw=exact['mean_dw'].tolist(),
                           mc_mean_dw=mean.tolist(),standard_error=se.tolist(),standardized_error=z.tolist(),
                           max_abs_z=float(np.max(np.abs(z))),exact_covariance=exact['cov_dw'].tolist(),
                           mc_covariance=np.cov(delta,rowvar=False,ddof=1).tolist(),
                           max_abs_second_moment_z=float(np.max(np.abs(second_z)))))
    summary=dict(seed=51691,mc_actions_per_case=args.mc_actions,mc_cases=len(mc),max_abs_mc_z=max(v['max_abs_z'] for v in mc),
                 max_abs_mc_second_moment_z=max(v['max_abs_second_moment_z'] for v in mc),
                 max_rl_formula_error=formula_error,models=list(models),grid_rows=len(rows),
                 teacher_rows=len(teacherrows),prefix_rows=len(prefixrows),
                 validation_outcomes_opened=False,external_outcomes_opened=False,
                 interpretation='Exact local conditional expectation/diffusion at fixed state; not an integrated acquisition forecast, causal mechanism, or proof of autonomous failure.')
    json_write(OUT/'MONTE_CARLO_CHECKS.json',mc);json_write(OUT/'SUMMARY.json',summary)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
