"""Fixed conditional binary-response forecast benchmark; see PROTOCOL.md."""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
import sys,json,time,hashlib,resource,itertools,csv
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import t as student_t
R=Path(__file__).resolve().parent
STIMS=['aud+','aud-','catch','vis+','vis-']; ALPHAS=[0.1,0.3]; FAMILIES=['L','G','C','R']; EVAL=['664851','713655','759434']
def stamp():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def save(name,x): (R/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def load_dev():return dict(np.load(R/'development_arrays.npz',allow_pickle=True))
def nll(y,p):
    y=np.asarray(y,dtype=float)
    return -y*np.log(np.clip(p,.001,.999))-(1-y)*np.log(np.clip(1-p,.001,.999))
def sign(s):return 1 if s=='vis+' else -1 if s=='aud+' else 0

class State:
    def __init__(self,t0):
        self.t0=t0;self.qr=np.full((5,2),.5);self.qy=np.full((5,2),.5);self.last_r=np.full(5,.5);self.last_y=np.full(5,.5);self.last_t=np.full(5,np.nan)
        self.gy=np.full(2,.5);self.gr=np.full(2,.5);self.prev_y=.5;self.prev_r=.5;self.reward_t=None;self.traces=np.zeros(2);self.last_sign=0;self.first_sign=0;self.pvis=.5
    def before(self,s,t):
        self.pvis=.99*self.pvis+.01*(1-self.pvis)
        k=STIMS.index(s);sg=sign(s);age=600 if np.isnan(self.last_t[k]) else max(0,t-self.last_t[k])
        names=['constant']+['stim_'+x for x in STIMS]
        v=[1.]+[float(s==x) for x in STIMS]
        for j,a in enumerate(ALPHAS):
            names+=['local_response_'+str(a),'local_reward_'+str(a)];v += [self.qy[k,j],self.qr[k,j]]
        names+=['last_same_response','last_same_reward','same_stimulus_age'];v += [self.last_y[k],self.last_r[k],min(1,np.log1p(age)/np.log(601))]
        cuts={'L':len(v)}
        names+=['previous_response','previous_reward'];v += [self.prev_y,self.prev_r]
        for j,a in enumerate(ALPHAS):
            names+=['global_response_'+str(a),'global_reward_'+str(a)];v += [self.gy[j],self.gr[j]]
        names+=['reward_recency'];v += [min(1,np.log1p(600 if self.reward_t is None else max(0,t-self.reward_t))/np.log(601))]
        cuts['G']=len(v)
        opp=STIMS.index('aud+' if s=='vis+' else 'vis+' if s=='aud+' else 'catch')
        for j,a in enumerate(ALPHAS):
            names+=['opposite_response_'+str(a),'opposite_reward_'+str(a)];v += [float(bool(sg))*self.qy[opp,j],float(bool(sg))*self.qr[opp,j]]
        for j,a in enumerate(ALPHAS):names+=['signed_reward_trace_'+str(a)];v += [sg*self.traces[j]]
        angle=np.pi*(t-self.t0)/600
        names+=['last_rewarded_target_match','clock_cos','clock_sin'];v += [sg*self.last_sign,sg*self.first_sign*np.cos(angle),sg*self.first_sign*np.sin(angle)]
        cuts['C']=len(v)
        names+=['context_match'];v += [sg*(2*self.pvis-1)]
        cuts['R']=len(v)
        return np.array(v,dtype=float),names,cuts
    def after(self,s,t,y,water,ignore=False):
        k=STIMS.index(s);sg=sign(s);self.last_t[k]=t
        if ignore:return
        self.last_y[k]=y;self.last_r[k]=water
        for j,a in enumerate(ALPHAS):
            self.qy[k,j]=(1-a)*self.qy[k,j]+a*y;self.qr[k,j]=(1-a)*self.qr[k,j]+a*water
            self.gy[j]=(1-a)*self.gy[j]+a*y;self.gr[j]=(1-a)*self.gr[j]+a*water
            self.traces[j]=(1-a)*self.traces[j]+a*sg*water
        self.prev_y=y;self.prev_r=water
        if water:
            self.reward_t=t
            if sg:
                self.last_sign=sg
                if not self.first_sign:self.first_sign=sg
        if sg and (water or y):
            active_like=.95 if water else .05
            vis_like=active_like if sg==1 else 1-active_like
            z=self.pvis*vis_like+(1-self.pvis)*(1-vis_like)
            self.pvis=np.clip(self.pvis*vis_like/z,1e-12,1-1e-12)

def features(d,ablate=False):
    st=State(float(d['stim_start_time'][0]));rows=[]
    for i,(s,t) in enumerate(zip(d['stim_name'],d['stim_start_time'])):
        v,n,cuts=st.before(str(s),float(t));rows.append(v)
        st.after(str(s),float(t),float(d['is_response'][i]),float(np.isfinite(d['reward_time'][i])),ignore=ablate and bool(d['is_instruction'][i]))
    return np.array(rows),n,cuts
def eligible(d):return ~d['is_instruction']&~d['is_opto']&~d['is_repeat']&(d['stim_name']!='catch')
def endpoints(d):
    rows=[];exclusions=[]
    for block in sorted(set(d['block_index'])):
        if block==0:continue
        ix=np.flatnonzero(d['block_index']==block);ins=ix[d['is_instruction'][ix]]
        ok=(len(ins)==5 and np.array_equal(ins,ix[:5]) and len(set(d['stim_name'][ins]))==1 and sign(d['stim_name'][ins[0]])!=0 and not np.any(d['is_opto'][ix]|d['is_repeat'][ix]))
        if not ok:exclusions.append(dict(block=int(block),reason='instruction/contiguity/opto/repeat gate'));continue
        new=str(d['stim_name'][ins[0]]);old='vis+' if new=='aud+' else 'aud+'
        candidates=ix[d['stim_name'][ix]==old]
        if not len(candidates):exclusions.append(dict(block=int(block),reason='no old target encounter'));continue
        i=int(candidates[0])
        rows.append(dict(trial=i,block=int(block),stimulus=old,new_target=new,strict_immediate=bool(i==ix[5]),new_block_rows_before=int(i-ix[0]),instruction_rows_before=5))
    return rows,exclusions

def fit(X,y,mask,lam):
    xx=X[mask];yy=y[mask].astype(float);mu=xx.mean(0);sd=xx.std(0);sd[sd<1e-6]=1;mu[0]=0;sd[0]=1;Z=(xx-mu)/sd
    penalty=np.ones(Z.shape[1]);penalty[0]=0
    def fg(b):
        eta=np.einsum('ij,j->i',Z,b);p=expit(eta)
        return float(np.sum(np.logaddexp(0,eta)-yy*eta)+lam*.5*np.sum(penalty*b*b)),np.einsum('ij,i->j',Z,p-yy)+lam*penalty*b
    ans=minimize(fg,np.zeros(Z.shape[1]),jac=True,method='L-BFGS-B',options={'maxiter':1000,'ftol':1e-12,'gtol':1e-7,'maxls':40})
    return dict(beta=ans.x.tolist(),mean=mu.tolist(),scale=sd.tolist(),lambda_=float(lam),success=bool(ans.success),message=str(ans.message),objective=float(ans.fun),max_gradient=float(np.max(np.abs(ans.jac))),iterations=int(ans.nit),training_rows=int(mask.sum()))
def predict(X,model):
    Z=(X-np.array(model['mean']))/np.array(model['scale']);return np.clip(expit(np.einsum('ij,j->i',Z,np.array(model['beta']))),.001,.999)
def chosen_models(d):
    X,n,c=features(d);mask=eligible(d);y=d['is_response'];models={};cv={};fitlog=[]
    for fam in FAMILIES:
        xx=X[:,:c[fam]];scores=[]
        for lam in [.1,1,10,100]:
            losses=[]
            for block in sorted(set(d['block_index'])):
                train=mask&(d['block_index']!=block);test=mask&(d['block_index']==block)
                m=fit(xx,y,train,lam);fitlog.append(dict(family=fam,block=int(block),lambda_=lam,**{k:m[k] for k in ['success','message','objective','max_gradient','iterations']}));losses.append(float(np.mean(nll(y[test],predict(xx[test],m)))))
            scores.append(dict(lambda_=lam,equal_block_log_loss=float(np.mean(losses)),block_losses=losses))
        lam=min(scores,key=lambda x:(x['equal_block_log_loss'],-x['lambda_']))['lambda_']
        models[fam]=fit(xx,y,mask,lam);models[fam]['feature_names']=n[:c[fam]];cv[fam]=scores
    return X,n,c,models,cv,fitlog

def invariance(d):
    X,n,c=features(d);j=100;dd={k:np.array(v,copy=True) for k,v in d.items()};dd['is_response'][j:]=~dd['is_response'][j:];dd['reward_time'][j:]=np.nan
    Y,_,_=features(dd)
    plain={k:v for k,v in d.items() if k in ['stim_name','stim_start_time','is_response','reward_time']};Z,_,_=features(plain)
    return dict(current_and_past_invariant_to_current_future_response_reward_change=bool(np.array_equal(X[:j+1],Y[:j+1])),all_features_identical_after_removing_block_instruction_scheduled_flags=bool(np.array_equal(X,Z)),max_future_invariance_error=float(np.max(np.abs(X[:j+1]-Y[:j+1]))))

def development():
    d=load_dev();X,n,c,models,cv,log=chosen_models(d);ep,ex=endpoints(d);ix=np.array([x['trial'] for x in ep]);scores={f:dict(primary_first_encounter_log_loss=float(np.mean(nll(d['is_response'][ix],predict(X[ix,:c[f]],models[f])))),probabilities=predict(X[ix,:c[f]],models[f]).tolist(),selected_ridge=models[f]['lambda_']) for f in FAMILIES}
    # Independent centered finite-difference check of the implemented logistic gradient.
    xx=X[:35,:c['R']];yy=d['is_response'][:35].astype(float);b=np.linspace(-.1,.1,xx.shape[1]);eta=np.einsum('ij,j->i',xx,b);g=np.einsum('ij,i->j',xx,expit(eta)-yy)+b
    def obj(q):
        z=np.einsum('ij,j->i',xx,q);return np.sum(np.logaddexp(0,z)-yy*z)+.5*np.sum(q*q)
    num=[]
    for j in range(len(b)):
        p=b.copy();q=b.copy();p[j]+=1e-5;q[j]-=1e-5;num.append((obj(p)-obj(q))/2e-5)
    grad=float(np.max(np.abs(g-np.array(num))))
    checks=dict(invariance(d),gradient_max_abs_error=grad,gradient_pass=grad<1e-6,all_cv_and_final_fits_converged=all(x['success'] for x in log) and all(x['success'] for x in models.values()),first_encounters=len(ep),first_responses=d['is_response'][ix].astype(int).tolist(),endpoint_exclusions=ex,maximum_recorded_optimizer_gradient=max([x['max_gradient'] for x in log]+[x['max_gradient'] for x in models.values()]))
    save('DEVELOPMENT_MODELS.json',models);save('DEVELOPMENT_CV.json',dict(scores=cv,fit_log=log));save('DEVELOPMENT_CHECKS.json',dict(created_utc=stamp(),checks=checks,primary_development_scores=scores,revision_used=False,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps(dict(checks=checks,scores=scores,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2))

def generator(d,rng,positive):
    out={k:np.array(v,copy=True) for k,v in d.items()};st=State(float(d['stim_start_time'][0]));ys=[];water=[];truth=[]
    animal_bias=float(rng.normal(0,.25))
    for i,(s,t) in enumerate(zip(d['stim_name'],d['stim_start_time'])):
        v,n,c=st.before(str(s),float(t));vals=dict(zip(n,v));eta=-2.2+animal_bias+4*vals['local_reward_0.3']+vals['local_response_0.3']+1.5*vals['clock_cos']+(4*vals['context_match'] if positive else 0)
        p=float(np.clip(expit(eta),.001,.999));y=bool(rng.random()<p)
        block=d['block_index'][i];ins=np.flatnonzero((d['block_index']==block)&d['is_instruction']);new=str(d['stim_name'][ins[0]])
        w=bool(s==new and (d['is_instruction'][i] or y));st.after(str(s),float(t),float(y),float(w));ys.append(y);water.append(w);truth.append(p)
    out['is_response']=np.array(ys);out['is_contingent_reward']=np.array(water)&np.array(ys);out['is_noncontingent_reward']=np.array(water)&~np.array(ys);out['is_rewarded']=np.array(water)
    out['response_time']=np.where(out['is_response'],(out['response_window_start_time']+out['response_window_stop_time'])/2,np.nan)
    out['reward_time']=np.where(np.array(water),np.where(out['is_response'],out['response_time']+.025,out['response_window_stop_time']),np.nan)
    return out,np.array(truth),animal_bias

def controls():
    base=load_dev();real=json.loads((R/'DEVELOPMENT_MODELS.json').read_bytes());rows=[];outputs=[]
    for positive in [False,True]:
        for rep in range(32):
            seed=314159+rep+(10000 if positive else 0);rng=np.random.default_rng(seed)
            dev,_,db=generator(base,rng,positive);X,n,c=features(dev);ms={f:fit(X[:,:c[f]],dev['is_response'],eligible(dev),real[f]['lambda_']) for f in FAMILIES}
            gains={x:[] for x in ['R_minus_L','R_minus_G','R_minus_C']};expected={x:[] for x in gains};animals=[]
            for a in range(3):
                dd,ptrue,ab=generator(base,rng,positive);xx,_,_=features(dd);ep,_=endpoints(dd);ix=np.array([e['trial'] for e in ep]);yy=dd['is_response'][ix].astype(float);pp={f:predict(xx[ix,:c[f]],ms[f]) for f in FAMILIES};loss={f:float(np.mean(nll(yy,pp[f]))) for f in FAMILIES};eloss={f:float(np.mean(nll(ptrue[ix],pp[f]))) for f in FAMILIES}
                for f in ['L','G','C']:gains['R_minus_'+f].append(loss[f]-loss['R']);expected['R_minus_'+f].append(eloss[f]-eloss['R'])
                animals.append(dict(animal=a,intercept_shift=ab,loss=loss,expected_loss=eloss))
                for j,i in enumerate(ix):outputs.append(dict(generator='R' if positive else 'C',replicate=rep,animal=a,trial=int(i),truth_probability=float(ptrue[i]),outcome=int(yy[j]),**{f:float(pp[f][j]) for f in FAMILIES}))
            passed=all(np.mean(gains['R_minus_'+f])>=.05 and min(gains['R_minus_'+f])>0 for f in ['G','C'])
            rows.append(dict(generator='R' if positive else 'C',replicate=rep,seed=seed,development_intercept_shift=db,all_fits_converged=all(m['success'] for m in ms.values()),gains=gains,expected_gains=expected,animals=animals,finite_practical_rule_pass=bool(passed)))
            if rep%8==0:print('CONTROL',rows[-1]['generator'],rep,'pass',passed,flush=True)
    save('CONTROL_DETAILS.json',rows);save('CONTROL_FORECASTS.json',outputs)
    summary={g:dict(replicates=32,practical_rule_passes=sum(x['finite_practical_rule_pass'] for x in rows if x['generator']==g),mean_R_minus_C=float(np.mean([np.mean(x['gains']['R_minus_C']) for x in rows if x['generator']==g])),mean_expected_R_minus_C=float(np.mean([np.mean(x['expected_gains']['R_minus_C']) for x in rows if x['generator']==g]))) for g in ['C','R']}
    save('CONTROL_SUMMARY.json',dict(created_utc=stamp(),summary=summary,all_fits_converged=all(x['all_fits_converged'] for x in rows),limitations='One fixed development schedule, same schedule copied across four synthetic animals, selected real-development ridge held fixed, normal(.0,.25) per-animal logit shifts; generator C local/clock, generator R adds coefficient4context_match. Not full hyperparameter-selection calibration, mechanistic identification, unconditional power or null error certification.',rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps(summary,indent=2))

def freeze():
    chk=json.loads((R/'DEVELOPMENT_CHECKS.json').read_bytes())['checks'];assert chk['gradient_pass'] and chk['all_cv_and_final_fits_converged'] and chk['all_features_identical_after_removing_block_instruction_scheduled_flags'] and chk['current_and_past_invariant_to_current_future_response_reward_change']
    paths=['PROTOCOL.md','analysis.py','evaluate.py','DEVELOPMENT_MODELS.json','DEVELOPMENT_CHECKS.json','DEVELOPMENT_CV.json','FIRST_DATA_CHECK.json','UNIT_CERTIFICATION.json','CODEC_CHECK.json','CONTROL_SUMMARY.json','CONTROL_DETAILS.json','CONTROL_FORECASTS.json']
    assert not (R/'SCIENTIFIC_FREEZE.json').exists()
    save('SCIENTIFIC_FREEZE.json',dict(created_utc=stamp(),evaluation_trial_arrays_acquired=False,development_revision_used=False,paths={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in paths},protocol='PROTOCOL.md',selection='fixed three distinct mice, old-target first encounters',source_gate_earned_utc='2026-11-01T03:24:25Z'))
    print('FROZEN',stamp())

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='development':development()
    elif mode=='controls':controls()
    elif mode=='freeze':freeze()
    else:raise ValueError(mode)
