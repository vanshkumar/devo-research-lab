#!/usr/bin/env python3
"""Synthetic controlled recovery for autonomous learning-rule transport.

This module never loads empirical source holdout or external observations.
Known generators use the same causal task trainer as the empirical forecast,
but independent random seeds. Null controls diagnose predictive specificity;
they cannot establish unique mechanism identification.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, time, os
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logit
from trainer import VectorTrainer
from learning_models import LearningModel, features, subject_arrays
from baselines import fit_bank
from baselines import subset, load_bank

CAMPAIGN=Path(__file__).resolve().parents[1]
OUT=CAMPAIGN/'artifacts/recovery'
TRUE_ALPHA=np.array([.006,.006,.003])
TRUE_BASELINE=np.array([-.2,-.2,-.2])

def write_json(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else float(x))+'\n')

def true_model():
    return LearningModel('reinforce',dict(alpha=TRUE_ALPHA.copy(),baseline=TRUE_BASELINE.copy()),
                         dict(name='known_transferable_REINFORCE',generator_only=True))

def invariant_controls():
    """Exact action-marginalized controls for endogenous update semantics."""
    s=np.array([-1.,-.25,-.0625,.0625,.25,1.])
    w=np.broadcast_to([1.1,1.4,.35],(len(s),3)).copy()
    x=features(s);p=expit(np.sum(w*x,axis=1));omit=.13
    # A likelihood/evidence tracker has zero expected parameter update under
    # its own generated actions, despite possible useful teacher-forced fits.
    evidence=(1-omit)*(.02*(p*(1-p)+(1-p)*(-p)))[:,None]*x
    r_right=(s>0).astype(float);r_left=(s<0).astype(float)
    model=true_model();a=model.params['alpha'];base=model.params['baseline']
    reward_update=(1-omit)*a*(p[:,None]*(r_right[:,None]+base)*(1-p[:,None])+
                       (1-p[:,None])*(r_left[:,None]+base)*(-p[:,None]))*x
    state={'w':w.copy()};model.update(state,s,np.zeros(len(s)),np.full(len(s),-1))
    omission_difference=float(np.max(np.abs(state['w']-w)))
    assert np.max(np.abs(evidence))<1e-17 and omission_difference==0.
    # Reward can create a directional expected sensory update. A pure
    # evidence update cannot be rebranded as this generative property.
    assert (reward_update[:3,1]>0).all() and (reward_update[3:,0]>0).all()
    write_json(OUT/'INVARIANT_CONTROLS.json',dict(evidence_filter_expected_update_max_abs=float(np.max(np.abs(evidence))),
                evidence_filter_expected_update=evidence,reward_rule_expected_update=reward_update,
                omission_update_max_abs_difference=omission_difference,
                interpretation='Zero expected coefficient update does not prove constant expected probabilities or identify a biological mechanism. It checks endogenous-action versus teacher-forced update semantics.'))

def initial_weights(n,rng,mode,hidden_sd=.5):
    skill=0.1 if mode in ['learning','learning_reset'] else (1.2 if mode in ['fixed','engagement'] else .1)
    w=np.repeat(np.array([[skill,skill,0.]]),n,axis=0)
    w[:,:2]+=rng.normal(0,.12,(n,2))
    w[:,2]=rng.normal(0,hidden_sd,n)
    return w

def generate(group,n=24,trials=6000,protocol='standard',mode='learning',seed=100,
             hidden_sd=.5,retention=1.,correction=True,censored=False,session_length=500):
    """Generate all columns causally from learner actions and trainer feedback."""
    rng=np.random.default_rng(seed)
    trainer=VectorTrainer(n,seed+19,protocol,correction=correction)
    model=true_model();w0=initial_weights(n,rng,mode,hidden_sd);state={'w':w0.copy()}
    fields={k:np.empty((trials,n),float) for k in ['contrastLeft','contrastRight','choice','feedbackType','rewardVolume',
                                               'probabilityLeft','session','session_start','repNum','true_p_right','true_omit']}
    # Each animal has a persistent engagement trait, independent of feedback.
    omit_base=expit(logit(.07)+rng.normal(0,.35,n))
    for t in range(trials):
        session_start=(t%session_length==0)
        if t and session_start:
            trainer.new_session()
            if retention!=1.:state['w']*=retention
        stimulus=trainer.sample();s=stimulus['signed_contrast']
        if mode=='growth':
            # Ordinary exposure growth deliberately has no reward update.
            state['w']=w0.copy()
            state['w'][:,:2]+=2.4*(1-np.exp(-t/2600.))
        elif mode in ['fixed','engagement']:state['w']=w0.copy()
        p=model.probs(state,s)
        omission=omit_base if mode!='engagement' else expit(logit(omit_base)+2.0-3.5*t/trials)
        choice=np.where(rng.random(n)<p,-1,1).astype(np.int8)
        choice[rng.random(n)<omission]=0
        # Actual future rewards are consequences of this generated choice.
        feedback=trainer.observe(choice)
        if mode in ['learning','learning_reset']:
            model.update(state,s,choice,feedback['feedbackType'],session_start)
        fields['contrastLeft'][t]=stimulus['contrastLeft'];fields['contrastRight'][t]=stimulus['contrastRight']
        fields['choice'][t]=choice;fields['feedbackType'][t]=feedback['feedbackType'];fields['rewardVolume'][t]=feedback['rewardVolume']
        fields['probabilityLeft'][t]=trainer.prob_left
        fields['session'][t]=t//session_length;fields['session_start'][t]=session_start;fields['repNum'][t]=stimulus['rep_num']
        fields['true_p_right'][t]=p;fields['true_omit'][t]=omission
    animals={};meta=[]
    lengths=np.full(n,trials)
    if censored:
        lengths=rng.integers(1600,trials+1,n)
        lengths[:3]=[650,900,1000]
    for i in range(n):
        subject=f'{group}_{i:03d}';T=int(lengths[i])
        d={k:v[:T,i] for k,v in fields.items()}
        for k in ['choice','feedbackType','session','repNum']:d[k]=d[k].astype(np.int32)
        d['session_start']=d['session_start'].astype(bool);d['session_index']=d['session'].copy()
        d['true_initial_w']=w0[i].copy()
        path=OUT/'synthetic'/group/(subject+'.npz');path.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(path,**d);animals[subject]=d
        meta.append(dict(subject=subject,trials=T,initial_w=w0[i].tolist(),npz_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    write_json(OUT/'synthetic'/group/'GENERATOR.json',dict(group=group,protocol=protocol,mode=mode,seed=seed,n=n,trials=trials,
               hidden_sd=hidden_sd,retention=retention,correction=correction,censored=censored,session_length=session_length,
               true_alpha=TRUE_ALPHA.tolist(),true_baseline=TRUE_BASELINE.tolist(),animals=meta,
               omissions='independent persistent beta-logit trait; changing exposure trait only in engagement control',
               independent_of_empirical_outcomes=True))
    return animals

def load_group(group):
    animals={}
    for p in sorted((OUT/'synthetic'/group).glob('*.npz')):
        with np.load(p,allow_pickle=False) as z:animals[p.stem]={k:z[k] for k in z.files}
    return animals

class RetentionAwareModel(LearningModel):
    """Known-answer daybreak model used only to localize a mismatch control."""
    def __init__(self,model,retention=.8):
        super().__init__(model.kind,model.params,dict(model.metadata,known_retention=retention))
        self.retention=retention
    def sequence(self,data,w0=None):
        n=len(data['choice']);_,_,_,starts=subject_arrays(data)
        boundaries=[0]+[int(i) for i in np.flatnonzero(starts) if i>0]+[n]
        w=np.zeros(3) if w0 is None else np.asarray(w0,float).copy();ps=[];ws=[]
        for lo,hi in zip(boundaries[:-1],boundaries[1:]):
            if lo>0:w*=self.retention
            p,ww,w=super().sequence(subset(data,lo,hi),w)
            ps.append(p);ws.append(ww)
        return np.concatenate(ps),np.concatenate(ws),w

def fit_known_init(animals,maxiter=180,name='learning'):
    """Likelihood recovery with generator-known initial conditions.

    This isolates numerical likelihood recovery; the forecast assessment must
    also use prefix-only inferred initial conditions to challenge that help.
    """
    calls=[0];start=time.monotonic()
    def objective(theta):
        # Direct a+b*r parameterization avoids ill-conditioning near zero.
        # b positive; a may be negative; alpha=b, baseline=a/b.
        b=np.exp(theta[:3]);a=theta[3:]
        model=LearningModel('reinforce',dict(alpha=b,baseline=a/b))
        ll=[]
        for subject,d in animals.items():
            p,_,_=model.sequence(d,d['true_initial_w'])
            y=(d['choice']<0).astype(float);ok=d['choice']!=0
            p=np.clip(p,1e-10,1-1e-10)
            ll.append(-np.mean((y*np.log(p)+(1-y)*np.log1p(-p))[ok]))
        calls[0]+=1
        return float(np.mean(ll))
    res=minimize(objective,np.r_[np.log([.004,.004,.002]),[-.001,-.001,-.0005]],method='L-BFGS-B',
                 bounds=[(-10,-2)]*3+[(-.03,.03)]*3,options=dict(maxiter=maxiter,ftol=1e-10,maxls=30))
    alpha=np.exp(res.x[:3]);baseline=res.x[3:]/alpha
    model=LearningModel('reinforce',dict(alpha=alpha,baseline=baseline),dict(name='synthetic_fitted_REINFORCE',
                   recovery_known_train_initialization=True,animal_equal_loss=True,fit_success=bool(res.success),fit_nll=float(res.fun)))
    target=OUT/('fitted_reinforce.npz' if name=='learning' else name+'_fitted_reinforce.npz')
    model.save(target);true_model().save(OUT/'oracle_reinforce.npz')
    target_json=OUT/('PARAMETER_RECOVERY.json' if name=='learning' else name+'_PARAMETER_FIT.json')
    write_json(target_json,dict(generator=name,true_alpha=TRUE_ALPHA if name=='learning' else None,true_baseline=TRUE_BASELINE if name=='learning' else None,
                fitted_alpha=alpha,fitted_baseline=baseline,optimizer_success=bool(res.success),message=str(res.message),
                calls=calls[0],seconds=time.monotonic()-start,fit_nll=float(res.fun),
                interpretation='Forecast recovery, not equality of a weakly identified parameter vector, is the positive-control criterion.'))
    print('synthetic fit',name,alpha,baseline,res.fun,'calls',calls[0],flush=True)
    return model

def fit_empirical_pipeline():
    """Challenge known-init help with the exact empirical fitting initializer."""
    from fit_learning import fit_rl
    animals=load_group('learn_train')
    model=fit_rl(list(sorted(animals.items())),6000,maxiter=180,stable_gain=True)
    model.save(OUT/'pipeline_fitted_reinforce.npz')
    write_json(OUT/'EMPIRICAL_PIPELINE_FIT.json',dict(model=model.metadata,
               alpha=model.params['alpha'],baseline=model.params['baseline'],
               true_alpha=TRUE_ALPHA,true_baseline=TRUE_BASELINE,
               interpretation='Same static first200 initialization and optimizer used for the empirical canonical rule; no generator initial weights supplied.'))

def generate_all(n=24,trials=6000):
    specifications=[
        ('learn_train','standard','learning',8101,dict()),
        ('learn_same','standard','learning',8102,dict()),
        ('learn_external','external','learning',8103,dict()),
        ('learn_hidden','standard','learning',8104,dict(hidden_sd=1.2)),
        ('learn_reset','standard','learning_reset',8105,dict(retention=.8)),
        ('learn_no_correction','standard','learning',8106,dict(correction=False)),
        ('learn_censored','standard','learning',8107,dict(censored=True)),
        ('fixed_train','standard','fixed',8201,dict()),
        ('fixed_test','standard','fixed',8202,dict()),
        ('growth_train','standard','growth',8301,dict()),
        ('growth_test','standard','growth',8302,dict()),
        ('engagement_train','standard','engagement',8401,dict()),
        ('engagement_test','standard','engagement',8402,dict()),
    ]
    for group,protocol,mode,seed,kwargs in specifications:
        print('generate',group,flush=True);generate(group,n,trials,protocol,mode,seed,**kwargs)
    true_model().save(OUT/'oracle_reinforce.npz')
    for kind in ['learn','fixed','growth','engagement']:
        fit_bank(load_group(kind+'_train'),OUT/(kind+'_bank.npz'),prefix=1000,bin_size=500,horizon=5000)
    write_json(OUT/'RECOVERY_DESIGN.json',dict(prefix=1000,horizons=[1000,3000,5000],primary_horizon=3000,
               n_train=n,n_test=n,trials=trials,groups=[x[0] for x in specifications],
               purpose='Known-learning positive control, exposure-only/fixed/engagement negative-generator controls, and localized assumption challenges. All synthetic data independent of real holdout/external outcomes.',
               calibration='Prefix-only inference at forecast; known training initialization separately isolates fit recovery.',
               seed_family='8101-8402; independent forecast seeds recorded in score artifacts'))

def evaluate_groups(groups=None,particles=128,max_animals=None):
    from learning_models import load_model
    from rollout import autonomous,trajectory_summary
    from evaluation import score,paired_interval
    groups=groups or ['learn_same','learn_external','learn_hidden','learn_reset','learn_no_correction','learn_censored',
                      'fixed_test','growth_test','engagement_test']
    all_records=[]
    for gi,group in enumerate(groups):
        path=OUT/('scores_'+group+f'_p{particles}.json')
        existing=json.loads(path.read_text()) if path.exists() else []
        done={(r['subject'],r['model'],r['horizon']) for r in existing}
        records=existing.copy();family=group.split('_')[0]
        bank=load_bank(OUT/(family+'_bank.npz'))
        candidates={'oracle':true_model()} if family=='learn' else {}
        candidates['fitted']=load_model(OUT/('fitted_reinforce.npz' if family=='learn' else family+'_fitted_reinforce.npz'))
        if family=='learn' and (OUT/'pipeline_fitted_reinforce.npz').exists():
            candidates['pipeline_fitted']=load_model(OUT/'pipeline_fitted_reinforce.npz')
        # Persistence/growth share the same actor, omission family, prefix and
        # trainer information. They differ only in source-learned competence.
        candidates['persistence']=candidates['fitted'];candidates['growth']=candidates['fitted']
        animals=load_group(group)
        for ai,(subject,d) in enumerate(sorted(animals.items())):
            if max_animals and ai>=max_animals:break
            P=1000;H=min(5000,((len(d['choice'])-P)//500)*500)
            if H<=0:
                if not any(r['subject']==subject for r in records):
                    records.append(dict(group=group,subject=subject,model='ineligible_short_prefix_or_future',horizon=0,trials=len(d['choice'])))
                continue
            prefix=subset(d,0,P);future=subset(d,P,P+H)
            x=np.nan_to_num(future['contrastRight'])-np.nan_to_num(future['contrastLeft'])
            observed,counts=trajectory_summary(x,future['choice'])
            for mi,(name,model) in enumerate(candidates.items()):
                if (subject,name,H) in done:continue
                seed=13000+gi*1000+ai*17 # Coupled randomness across models.
                forecast=autonomous(model,prefix,future['session_start'],bank,n_particles=particles,seed=seed,
                         protocol='external' if group=='learn_external' else 'standard',subject=subject,
                         competence=name if name in ['persistence','growth'] else None)
                npz=OUT/'forecasts'/group/(subject+'_'+name+f'_p{particles}.npz');npz.parent.mkdir(parents=True,exist_ok=True)
                np.savez_compressed(npz,samples=forecast['samples'],observed=observed[0],counts=counts[0])
                for horizon in [1000,3000,5000]:
                    if H<horizon:continue
                    nb=horizon//500
                    sc=score(forecast['samples'][:,:nb],observed[0,:nb])
                    records.append(dict(group=group,subject=subject,model=name,horizon=horizon,seed=seed,particles=particles,
                                        trials=len(d['choice']),**sc))
                # Censored tails are scored at their available full bins too.
                if H not in [1000,3000,5000]:
                    sc=score(forecast['samples'],observed[0]);records.append(dict(group=group,subject=subject,model=name,
                           horizon=H,seed=seed,particles=particles,trials=len(d['choice']),available_exposure_tail=True,**sc))
                write_json(path,records)
            print('recovery forecast',group,ai+1,len(animals),subject,'H',H,flush=True)
        write_json(path,records);all_records.extend(records)
    summarize(all_records,particles)

def summarize(records,particles):
    from evaluation import paired_interval
    rows=[];comparisons=[]
    groups=sorted(set(r['group'] for r in records))
    for group in groups:
        for horizon in [1000,3000,5000]:
            rr=[r for r in records if r['group']==group and r['horizon']==horizon and 'crps' in r]
            models=sorted(set(r['model'] for r in rr))
            for model in models:
                mm=[r for r in rr if r['model']==model]
                rows.append(dict(group=group,model=model,horizon=horizon,n=len(mm),
                    **{k:float(np.mean([r[k] for r in mm])) for k in ['crps','mae','high_accuracy_mae','energy']},
                    coverage80=float(np.mean([r['coverage']['0.8'] for r in mm])),
                    coverage95=float(np.mean([r['coverage']['0.95'] for r in mm])),
                    width80=float(np.mean([r['width']['0.8'] for r in mm]))))
            by={(r['subject'],r['model']):r for r in rr}
            subjects=sorted(set(r['subject'] for r in rr))
            for model in ['oracle','fitted','pipeline_fitted']:
                for baseline in ['persistence','growth']:
                    diff=[by[(s,baseline)]['crps']-by[(s,model)]['crps'] for s in subjects if (s,model) in by and (s,baseline) in by]
                    if diff:comparisons.append(dict(group=group,horizon=horizon,model=model,baseline=baseline,
                         improvement=paired_interval(diff),relative_improvement=float(np.mean(diff)/np.mean([by[(s,baseline)]['crps'] for s in subjects if (s,model) in by and (s,baseline) in by]))))
    write_json(OUT/f'SCORE_SUMMARY_p{particles}.json',rows);write_json(OUT/f'PAIRED_COMPARISONS_p{particles}.json',comparisons)

def summarize_saved(particles=128):
    records=[]
    for p in sorted(OUT.glob(f'scores_*_p{particles}.json')):records.extend(json.loads(p.read_text()))
    summarize(records,particles)
    return records

def evaluate_rescues(particles=128):
    from learning_models import load_model
    from rollout import autonomous,trajectory_summary
    from evaluation import score,paired_interval
    bank=load_bank(OUT/'learn_bank.npz');rescues=[]
    for group in ['learn_reset','learn_no_correction']:
        path=OUT/('scores_'+group+f'_p{particles}.json');records=json.loads(path.read_text())
        animals=load_group(group)
        for ai,(subject,d) in enumerate(sorted(animals.items())):
            P=1000;H=5000;prefix=subset(d,0,P);future=subset(d,P,P+H)
            x=np.nan_to_num(future['contrastRight'])-np.nan_to_num(future['contrastLeft']);observed,counts=trajectory_summary(x,future['choice'])
            for name,base in [('oracle',true_model()),('fitted',load_model(OUT/'fitted_reinforce.npz'))]:
                rescued_name=name+'_matched_assumption'
                if any(r['subject']==subject and r['model']==rescued_name for r in records):continue
                original=next(r for r in records if r['subject']==subject and r['model']==name and r['horizon']==3000)
                seed=original['seed'];kwargs={}
                if group=='learn_reset':
                    model=RetentionAwareModel(base,.8);kwargs['weight_retention']=.8
                else:model=base;kwargs['trainer_options']={'correction':False}
                forecast=autonomous(model,prefix,future['session_start'],bank,n_particles=particles,seed=seed,subject=subject,**kwargs)
                npz=OUT/'forecasts'/group/(subject+'_'+rescued_name+f'_p{particles}.npz')
                np.savez_compressed(npz,samples=forecast['samples'],observed=observed[0],counts=counts[0])
                for horizon in [1000,3000,5000]:
                    nb=horizon//500;sc=score(forecast['samples'][:,:nb],observed[0,:nb])
                    records.append(dict(group=group,subject=subject,model=rescued_name,horizon=horizon,seed=seed,particles=particles,trials=len(d['choice']),**sc))
                write_json(path,records)
            print('matched rescue',group,ai+1,len(animals),flush=True)
        by={(r['subject'],r['model']):r for r in records if r['horizon']==3000}
        for name in ['oracle','fitted']:
            dif=[by[(s,name)]['crps']-by[(s,name+'_matched_assumption')]['crps'] for s in animals]
            rescues.append(dict(group=group,model=name,correct_assumption='session_retention_.8' if group=='learn_reset' else 'no_correction',improvement=paired_interval(dif)))
    write_json(OUT/'MATCHED_ASSUMPTION_RESCUES.json',rescues);summarize_saved(particles)

def convergence():
    """Matched first-six-animal comparison at 128 versus512 particles."""
    records={p:summarize_saved(p) for p in [128,512]};rows=[]
    small={(r['group'],r['subject'],r['model'],r['horizon']):r for r in records[128] if 'crps' in r}
    for r in records[512]:
        key=(r['group'],r['subject'],r['model'],r['horizon'])
        if key not in small:continue
        rr=small[key]
        rows.append(dict(group=r['group'],subject=r['subject'],model=r['model'],horizon=r['horizon'],
                         delta_crps_512_minus128=r['crps']-rr['crps'],
                         delta_high_accuracy_mae=r['high_accuracy_mae']-rr['high_accuracy_mae']))
    sums=[]
    for group in sorted(set(r['group'] for r in rows)):
        for model in sorted(set(r['model'] for r in rows)):
            rr=[r for r in rows if r['group']==group and r['model']==model and r['horizon']==3000]
            if rr:sums.append(dict(group=group,model=model,n=len(rr),
                         mean_delta_crps=float(np.mean([r['delta_crps_512_minus128'] for r in rr])),
                         max_abs_delta_crps=float(np.max(np.abs([r['delta_crps_512_minus128'] for r in rr]))),
                         mean_delta_high_accuracy_mae=float(np.mean([r['delta_high_accuracy_mae'] for r in rr]))))
    write_json(OUT/'MONTE_CARLO_CONVERGENCE.json',dict(comparison='same first6animals/group,independent samples128vs512 using recorded coupled seeds',summary=sums,animals=rows))

def figures():
    os.environ.setdefault('MPLCONFIGDIR',str(OUT/'matplotlib_cache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    records=summarize_saved(128)
    groups=['learn_same','learn_external'];names=['oracle','pipeline_fitted','growth','persistence']
    colors=['#3366aa','#217a5a','#bb7a24','#777777'];fig,axs=plt.subplots(1,3,figsize=(12,3.7))
    for gi,g in enumerate(groups):
        mm=[];err=[]
        for mi,m in enumerate(names):
            rr=[r['crps'] for r in records if r['group']==g and r['model']==m and r['horizon']==3000]
            rng=np.random.default_rng(9101+mi+gi*10);rr=np.asarray(rr);bs=rr[rng.integers(0,len(rr),(5000,len(rr)))].mean(axis=1)
            mm.append(rr.mean());err.append([rr.mean()-np.quantile(bs,.025),np.quantile(bs,.975)-rr.mean()])
        axs[gi].bar(np.arange(4),mm,color=colors,yerr=np.array(err).T,capsize=3)
        axs[gi].set_xticks(np.arange(4),['Oracle','Fitted','Growth','Persistent'],rotation=25,ha='right')
        axs[gi].set_ylabel('Trajectory CRPS (lower is better)');axs[gi].set_title(['New source learners','Frozen rule, fixed curriculum'][gi]);axs[gi].set_ylim(0,.09)
    for mi,m in enumerate(['pipeline_fitted','growth']):
        for gi,g in enumerate(groups):
            rr=[r for r in records if r['group']==g and r['model']==m and r['horizon']==3000]
            vals=[np.mean([r['coverage'][str(v)] for r in rr]) for v in [.5,.8,.95]]
            label='Fitted' if m=='pipeline_fitted' else 'Growth'
            axs[2].plot([.5,.8,.95],vals,marker='o',color=colors[mi+1],linestyle=['-','--'][gi],label=label+', '+['source','fixed'][gi])
    axs[2].plot([.4,1],[.4,1],':',color='black');axs[2].set_xlim(.45,1);axs[2].set_ylim(.4,1);axs[2].set_xlabel('Nominal interval coverage');axs[2].set_ylabel('Observed cell coverage');axs[2].set_title('Independent animal trajectories');axs[2].legend(fontsize=7)
    fig.suptitle('Known transferable learner: 24 train + 24 new animals per protocol; prefix 1,000, forecast 3,000 trials',fontsize=10)
    fig.tight_layout();fig.savefig(OUT/'KNOWN_TRANSFER_RECOVERY.png',dpi=180);fig.savefig(OUT/'KNOWN_TRANSFER_RECOVERY.pdf');plt.close(fig)

def main():
    p=argparse.ArgumentParser();p.add_argument('--generate',action='store_true');p.add_argument('--fit',action='store_true');p.add_argument('--fit-pipeline',action='store_true');p.add_argument('--fit-nulls',action='store_true');p.add_argument('--evaluate',action='store_true');p.add_argument('--summarize',action='store_true');p.add_argument('--convergence',action='store_true');p.add_argument('--figures',action='store_true');p.add_argument('--rescues',action='store_true');p.add_argument('--groups');p.add_argument('--particles',type=int,default=128);p.add_argument('--max-animals',type=int);p.add_argument('--n',type=int,default=24);p.add_argument('--trials',type=int,default=6000)
    a=p.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    invariant_controls()
    if a.generate:generate_all(a.n,a.trials)
    if a.fit:fit_known_init(load_group('learn_train'))
    if a.fit_pipeline:fit_empirical_pipeline()
    if a.fit_nulls:
        for name in ['fixed','growth','engagement']:fit_known_init(load_group(name+'_train'),name=name)
    if a.evaluate:evaluate_groups(a.groups.split(',') if a.groups else None,a.particles,a.max_animals)
    if a.summarize:summarize_saved(a.particles)
    if a.convergence:convergence()
    if a.figures:figures()
    if a.rescues:evaluate_rescues(a.particles)

if __name__=='__main__':main()
