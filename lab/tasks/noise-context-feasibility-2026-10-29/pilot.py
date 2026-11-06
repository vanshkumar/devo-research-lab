"""Pinned SEM reconstruction and one learned reliability mechanism. No data readers."""
from pathlib import Path
import sys, json, math, time, hashlib, importlib.util
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
SRC=ROOT/'sources/noise_context_feasibility_2026-10-29'
S2=json.loads((SRC/'sim_to_args.json').read_text())['sim2']['sch']
S1=json.loads((SRC/'sim_to_args.json').read_text())['sim1']['sch']
ROLES=('no_oracle','oracle','learned')

def source_module():
    s=importlib.util.spec_from_file_location('published_sem',SRC/'model.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class Learner:
    def __init__(self,role,params=None):
        assert role in ROLES
        self.role=role;self.params=dict(S2 if params is None else params)
        self.alpha=self.params['concentration'];self.beta=self.params['stickiness'];self.lam=self.params['sparsity']
        self.T=np.zeros((206,9,9));self.raw=np.zeros_like(self.T);self.n=np.zeros(206)
        self.k=2;self.active=0;self.visited=set();self.n_updates=0
        self.posterior=None;self.story_buffer=[]
    def begin_story(self):
        if self.role!='learned':return
        prior=np.where(self.n[:self.k]>0,self.n[:self.k],self.alpha)
        prior[self.active]+=self.beta*(self.n[self.active]>0)
        self.posterior=prior/prior.sum();self.story_buffer=[]
    def end_story(self):
        if self.role!='learned':return
        z=int(np.argmax(self.posterior))
        if z==self.k-1:self.k+=1
        self.active=z;self.visited.add(z)
        # Completed past stories alone train the next story. No stored prediction is revised.
        for x,y in self.story_buffer:
            self.T[z,x,y]+=1;self.raw[z,x,y]+=1;self.n[z]+=1
        self.n_updates+=len(self.story_buffer)
    def weight(self,x):
        if self.role!='learned': return 1.
        # exact per-context Dirichlet-multinomial *ordered-sequence* evidence
        # versus independent fair draws. Zero cells contribute logGamma(a)-logGamma(a)=0.
        a=.5;logbf=0.
        for counts in self.raw[:self.k,x,:]:
            n=float(counts.sum())
            if n==0: continue
            nz=counts[counts>0]
            assert len(nz)<=2, 'source two-outcome family exceeded'
            logbf += math.lgamma(2*a)-math.lgamma(2*a+n)
            logbf += sum(math.lgamma(a+float(v))-math.lgamma(a) for v in nz)
            logbf += n*math.log(2.)
        if logbf>=0: return 1/(1+math.exp(-min(logbf,700)))
        e=math.exp(max(logbf,-700));return e/(1+e)
    def likes(self,x):
        return (self.lam+self.T[:self.k,x,:])/(2*self.lam+self.T[:self.k,x,:].sum(1,keepdims=True))
    def predict(self,x,candidates):
        if self.role=='learned':
            v=self.posterior@self.likes(x)[:,np.asarray(candidates)]
        else:v=self.likes(x)[self.active,np.asarray(candidates)]
        z=np.exp(4*(v-v.max()));return z/z.sum()
    def observe(self,x,y,w,skip=False):
        if skip: return self.active
        like=self.likes(x)[:,y]
        if self.role=='learned':
            # A shared fair-noise component contributes no evidence for a context.
            # Reliability and parameters were learned only from completed past stories.
            self.posterior*=w*like+(1-w)*.5
            self.posterior/=self.posterior.sum()
            self.story_buffer.append((x,y))
            return int(np.argmax(self.posterior))
        prior=np.where(self.n[:self.k]>0,self.n[:self.k],self.alpha)
        prior[self.active]+=self.beta*(self.n[self.active]>0)
        post=like*prior
        if self.role=='learned':
            post=post/post.sum()*w
            post[self.active]+=1-w
        z=int(np.argmax(post))
        if z==self.k-1:
            assert self.k<206
            self.k+=1
        self.active=z;self.visited.add(z)
        wt=w if self.role=='learned' else 1.
        self.T[z,x,y]+=wt;self.n[z]+=wt;self.raw[z,x,y]+=1
        self.n_updates+=1
        return z

def curriculum(name,rng):
    if name=='blocked': c=[0]*40+[1]*40+[0]*40+[1]*40
    elif name=='interleaved': c=[0,1]*80
    elif name=='early': c=[0]*40+[1]*40+[0,1]*40
    elif name=='middle': c=[0,1]*20+[0]*40+[1]*40+[0,1]*20
    elif name=='late': c=[0,1]*40+[0]*40+[1]*40
    else: raise ValueError(name)
    return np.array(c+rng.integers(0,2,40).tolist())

def make_sequence(seed,curr='blocked',family='original',permute=False):
    rng=np.random.default_rng(seed);ctx=curriculum(curr,rng);branch=rng.integers(0,2,200)
    # Time/sensory candidate structure is the same in all roles. No role receives ctx/noise.
    exp=np.zeros((200,5),int);exp[:,1]=ctx+1
    if family=='original':
        exp[:,2]=3+branch;exp[:,3]=5+(branch^ctx);exp[:,4]=7+branch;noise_t=1
    elif family=='relocated':
        # Move irreducible randomness to the next transition. Earlier edge is now learnable.
        exp[:,2]=3+ctx;exp[:,3]=5+branch;exp[:,4]=7+(branch^ctx);noise_t=2
    elif family=='deterministic':
        # All post-cue edges deterministic; current pooled row can still be 50/50.
        exp[:,2]=3+ctx;exp[:,3]=5+np.zeros(200,int);exp[:,4]=7+ctx;noise_t=-1
    else: raise ValueError(family)
    pairs=[(1,2),(3,4),(5,6),(7,8)]
    perm=np.arange(9)
    if permute:
        # Separate RNG makes permuted runs exact relabelings of the same sequence.
        perm=np.random.default_rng(seed+908172).permutation(9)
        exp=perm[exp];pairs=[tuple(perm[list(p)]) for p in pairs]
    return {'exp':exp,'ctx':ctx,'pairs':pairs,'noise_t':noise_t,'perm':perm,'family':family,'curr':curr,'seed':seed}

def run(seq,role,params=None,save_trace=False):
    l=Learner(role,params);tr=[];correct=[];nll=[];predictions=[];weights=[];assign=[]
    for s,story in enumerate(seq['exp']):
        l.begin_story()
        for t,(x,y) in enumerate(zip(story[:-1],story[1:])):
            # The oracle's only privileged information is that actual family noise location.
            skip=role=='oracle' and t==seq['noise_t']
            p=l.predict(int(x),seq['pairs'][t]);w=l.weight(int(x))
            target=int(np.flatnonzero(np.asarray(seq['pairs'][t])==y)[0])
            predictions.append(p);weights.append(w);correct.append(p[target]);nll.append(-np.log(max(p[target],1e-15)))
            before=l.active;z=l.observe(int(x),int(y),w,skip)
            assign.append(z)
            if save_trace:tr.append({'story':s,'step':t,'x':int(x),'y':int(y),'p_before':p.tolist(),'w_before':w,'z_before':before,'z_after':z,'skip':skip})
        l.end_story()
    P=np.asarray(correct).reshape(200,4);LL=np.asarray(nll).reshape(200,4);W=np.asarray(weights).reshape(200,4);Z=np.asarray(assign).reshape(200,4)
    # Main outcome concerns deterministic non-cue edges only; full and noise metrics separate.
    signal=[t for t in (1,2,3) if t!=seq['noise_t']]
    metrics={'role':role,'seed':seq['seed'],'family':seq['family'],'curriculum':seq['curr'],
        'all_probability':float(P.mean()),'signal_probability':float(P[:,signal].mean()),
        'test_signal_probability':float(P[160:,signal].mean()),'test_signal_nll':float(LL[160:,signal].mean()),
        'first_block_signal_probability':float(P[:40,signal].mean()),
        'second_block_signal_probability':float(P[40:80,signal].mean()),
        'return_block_signal_probability':float(P[80:120,signal].mean()),
        'return_first5_signal_probability':float(P[80:85,signal].mean()),
        'first_block_last5_signal_probability':float(P[35:40,signal].mean()),
        'test_signal_modal_accuracy':float(np.where(abs(P[160:,signal]-.5)<1e-12,.5,P[160:,signal]>.5).mean()),
        'n_schemas':int((l.n>0).sum()),'signal_w_last40':float(W[160:,signal].mean()),
        'noise_w_last40':float(W[160:,seq['noise_t']].mean()) if seq['noise_t']>=0 else None,
        'signal_w_40to80':float(W[40:80,signal].mean()),
        'max_probability':float(P.max()),'min_probability':float(P.min())}
    # Context decoding by best majority mapping is diagnostic only, never fed to learner.
    zlast=Z[:,-1];ctx=seq['ctx'];right=0
    for k in np.unique(zlast[160:]):
        a=ctx[160:][zlast[160:]==k];right+=max(np.sum(a==0),np.sum(a==1))
    metrics['test_context_purity']=float(right/40)
    metrics['test_noise_error_from_chance']=float(abs(P[160:,seq['noise_t']].mean()-.5)) if seq['noise_t']>=0 else None
    return metrics, np.asarray(predictions).reshape(200,4,2),W,Z,tr,l

def source_checks():
    m=source_module();res=[]
    seq=make_sequence(11)
    for label,pa,skip in [('native_sim1',S1,False),('matched_no_oracle',S2,False),('native_sim2',S2,True)]:
        sm=m.SEM(schargs=pa,skipt1=skip,ppd_allsch=0)
        d=sm.run_exp(seq['exp'])
        role='oracle' if skip else 'no_oracle'
        rr=run(seq,role,pa)
        errs=[]
        for s in range(200):
            for t in range(4):
                if skip and t==1:continue
                p=d['xth'][s,t,list(seq['pairs'][t])];p=np.exp(4*(p-p.max()));p=p/p.sum()
                errs.append(np.max(abs(p-rr[1][s,t])))
        used=d['zt'][:,:4];zs=rr[3]
        mask=used!=-1
        res.append({'name':label,'max_probability_error':float(max(errs)),'assignments_exact':bool(np.array_equal(used[mask],zs[mask])),'source_schema_count':len([k for k in sm.schlib if k.ntimes_sampled>0]),'replica_schema_count':rr[0]['n_schemas']})
    assert all(x['max_probability_error']<1e-13 and x['assignments_exact'] for x in res),res
    # Hand-derived prior-predictive and first-count checks, independent of source runner.
    q=Learner('no_oracle');assert np.all(q.predict(0,[1,2])==.5)
    q.observe(0,1,1);expected=(q.lam+1)/(2*q.lam+1)
    assert abs(q.likes(0)[0,1]-expected)<1e-15
    q=Learner('learned');
    for i in range(30):q.raw[0,3,5]+=1;q.raw[1,3,6]+=1
    conditional=q.weight(3)
    q.raw[:]=0
    for i in range(30):q.raw[0,3,5]+=1;q.raw[0,3,6]+=1
    noise=q.weight(3)
    assert conditional>.99 and noise<.15,(conditional,noise)
    res.append({'name':'known_conditional_vs_pooled_entropy','conditional_deterministic_weight':conditional,'within_context_fair_weight':noise})
    return res

def dump(path,obj):path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')

def develop():
    t=time.monotonic();checks=source_checks();metrics=[]
    for curr in ('blocked','interleaved'):
        for seed in (11,12):
            seq=make_sequence(seed,curr)
            for role in ROLES:
                rr=run(seq,role,save_trace=seed==11 and curr=='blocked');metrics.append(rr[0])
                if rr[4]:dump(OUT/f'development_trace_{role}.json',rr[4])
    dump(OUT/'development.json',{'settings_tested':1,'sequences_used':4,'checks':checks,'metrics':metrics,'runtime_seconds':time.monotonic()-t})
    print(json.dumps({'checks':checks,'metrics':metrics,'runtime_seconds':time.monotonic()-t},indent=2))

def score():
    t=time.monotonic();metrics=[];prob=[];weight=[];assignment=[];meta=[];checks=[]
    for family in ('original','relocated','deterministic'):
        for curr in ('blocked','interleaved','early','middle','late'):
            for seed in range(27001,27021):
                original_outputs={}
                for permuted in (False,True):
                    seq=make_sequence(seed,curr,family,permuted)
                    for role in ROLES:
                        rr=run(seq,role)
                        rr[0]['permuted']=permuted
                        metrics.append(rr[0]);prob.append(rr[1]);weight.append(rr[2]);assignment.append(rr[3])
                        meta.append({'family':family,'curriculum':curr,'seed':seed,'permuted':permuted,'role':role})
                        if not permuted:original_outputs[role]=rr
                        else:
                            a=original_outputs[role]
                            pe=float(np.max(abs(a[1]-rr[1])));we=float(np.max(abs(a[2]-rr[2])))
                            checks.append({'family':family,'curriculum':curr,'seed':seed,'role':role,'permutation_probability_max_error':pe,'permutation_weight_max_error':we,'assignments_equal':bool(np.array_equal(a[3],rr[3]))})
                if family=='deterministic':
                    assert np.array_equal(original_outputs['no_oracle'][1],original_outputs['oracle'][1])
    np.savez_compressed(OUT/'scored_predictions.npz',p=np.stack(prob),w=np.stack(weight),z=np.stack(assignment))
    dump(OUT/'scored_metadata.json',meta);dump(OUT/'scored_metrics.json',metrics)
    dump(OUT/'scored_permutation_checks.json',checks)
    dump(OUT/'score_runtime.json',{'runtime_seconds':time.monotonic()-t,'sequences':600,'unique_unpermuted_sequences':300,'stories_per_sequence':200,'model_runs':len(metrics),'max_concurrent_processes':1})
    print(json.dumps({'runtime_seconds':time.monotonic()-t,'model_runs':len(metrics),'permutation_max_error':max(x['permutation_probability_max_error'] for x in checks),'weight_permutation_max_error':max(x['permutation_weight_max_error'] for x in checks),'assignments_equal':all(x['assignments_equal'] for x in checks)}))

if __name__=='__main__':
    if sys.argv[1:] == ['develop']: develop()
    elif sys.argv[1:] == ['score']:score()
