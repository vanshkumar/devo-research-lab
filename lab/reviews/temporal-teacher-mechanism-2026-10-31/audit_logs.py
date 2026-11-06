"""Independent complete scalar-search replay and waveform/gold audit."""
import review_core as r
import numpy as np,json,hashlib,time,resource

def choose(vals):
    vals=np.asarray(vals);return int(np.flatnonzero(vals<=np.min(vals)+1e-14)[0])

def replay(q,initial,seed):
    rng=np.random.default_rng(seed);cursor=0;path=[]
    states=[{'x':np.r_[initial,float(o),d],'cost':np.inf,'step':np.array([.4,.4,.4,.4,.08])} for o in range(6) for d in (.75,1.,1.25)]
    def use(actions):
        nonlocal cursor
        aa=np.asarray(actions);n=len(aa)
        assert np.array_equal(aa,q['query_actions'][cursor:cursor+n]),('proposals',cursor)
        v=q['query_costs'][cursor:cursor+n];cursor+=n;return v
    def best():return states[choose([s['cost'] for s in states])]
    vals=use([s['x'] for s in states])
    for s,v in zip(states,vals):s['cost']=float(v)
    path.append(best()['x'].copy())
    def rounds(n):
        for _ in range(n):
            broad=rng.uniform([-2.,-2.,-2.,-2.,.7],[2.,2.,2.,2.,1.25],size=(2,5))
            pending=[]
            for s in states:
                for axis in range(5):
                    k=axis if axis<4 else 5
                    for sign in (1.,-1.):
                        a=s['x'].copy();a[k]=np.clip(a[k]+sign*s['step'][axis],-2. if axis<4 else .7,2. if axis<4 else 1.25);pending.append(a)
                for b in broad:pending.append(np.r_[b[:4],s['x'][4],b[4]])
            vv=use(pending)
            for i,s in enumerate(states):
                costs=vv[12*i:12*(i+1)];j=choose(costs)
                if costs[j]<s['cost']-1e-14:s['x']=np.array(pending[12*i+j]);s['cost']=float(costs[j])
                else:s['step']=np.maximum([.00625,.00625,.00625,.00625,.00125],s['step']/2)
            path.append(best()['x'].copy())
    rounds(12)
    left=states.copy();ranked=[]
    while left:ranked.append(left.pop(choose([s['cost'] for s in left])))
    states=ranked[:6];rounds(12)
    def expand():
        nonlocal states
        old=best();aa=[np.r_[old['x'][:4],float(o),old['x'][5]] for o in range(64)];vv=use(aa);j=choose(vv)
        if vv[j]<old['cost']-1e-14:old={'x':np.array(aa[j]),'cost':float(vv[j]),'step':np.array([.05,.05,.05,.05,.02])}
        states=[old];path.append(old['x'].copy())
    expand();rounds(10);expand()
    assert cursor==3722 and np.array_equal(np.asarray(path),q['actions'])
    assert best()['cost']<=q['query_costs'].min()+1e-12
    return {'queries':cursor,'decisions':len(path),'final':best()['x'],'feedback':best()['cost']}

def gold_all(actions,env,teacher):
    # Independent prefix-integral reduction of a samplewise square error.
    # No import of segment overlap/loss routines from the implementation.
    u=np.tensordot(actions[:,:4],env['basis'],axes=([1],[2]))+env['bias'][None]
    u=np.maximum(u,0.);u-=u.mean(2,keepdims=True)
    u=2*u/np.maximum(np.sqrt(np.mean(u*u,2,keepdims=True)),1e-12)
    u=np.take_along_axis(u,env['orders'][actions[:,4].astype(int),:,None],axis=1)
    starts=150+np.rint(actions[:,5,None]*(150*np.arange(6))[None]).astype(int)
    ends=starts+np.rint(actions[:,5,None]*100).astype(int)
    active=np.mean(u*u,2)>1e-8
    first=np.where(active,starts,2200).min(1);first=np.where(first==2200,0,first)
    starts=starts-first[:,None];ends=ends-first[:,None]
    ts=int(np.flatnonzero(np.mean(teacher*teacher,1)>1e-8)[0])
    tt=np.zeros_like(teacher);tt[:2200-ts]=teacher[ts:]
    cumulative=np.vstack([np.zeros((1,100)),np.cumsum(tt,axis=0)])
    target_energy=np.sum(tt*tt)
    values=[]
    for i in range(len(actions)):
        energy=0.;cross=0.
        for k in range(6):
            if not active[i,k]:continue
            lo=max(0,int(starts[i,k]));hi=min(2200,int(ends[i,k]))
            energy+=(hi-lo)*float(u[i,k]@u[i,k])
            cross+=float(u[i,k]@(cumulative[hi]-cumulative[lo]))
        values.append(max(0.,(energy+target_energy-2*cross)/220000))
    return np.asarray(values)

def main():
    start=time.monotonic();checks=[]
    def ck(n,ok,detail=None):
        checks.append({'check':n,'pass':bool(ok),'detail':detail})
        if not ok:raise AssertionError(checks[-1])
    freeze=json.loads(r.read(r.TASK/'FREEZE.json'))
    for path,h in freeze['hashes'].items():ck('frozen_'+path,hashlib.sha256(r.read(r.ROOT/path)).hexdigest()==h)
    held=json.loads(r.read(r.TASK/'outputs/HELD.json'))
    diagnostics=json.loads(r.read(r.TASK/'outputs/DIAGNOSTICS.json'))
    cfg=json.loads(r.read(r.TASK/'CONFIG.json'))
    ck('eight_whole_cases_complete',held['complete'] and diagnostics['complete'] and [v['case'] for v in held['results']]==list(range(400,408)))
    rows=[];maxgold=0.;maxdirect=0.;totalqueries=0;counts={};reference_errors=[]
    for case in range(400,408):
        r.deadline()
        env=r.loadz(r.SRC/f'held_{case}_environment.npz')
        truth=r.loadz(r.SRC/f'held_{case}_truth.npz')
        teacher=env['teacher_observation'];target=np.asarray(truth['target']);order=int(truth['target_order']);duration=float(truth['target_stretch'])
        generated=r.render(target,order,duration,env,int(truth['observation_phase']))
        ck(f'case_{case}_teacher_from_stored_truth',np.max(abs(generated-teacher))<1e-12)
        ck(f'case_{case}_known_six_policy_target',0<=order<6 and len(env['orders'])==64 and len(set(map(tuple,env['orders'])))==64)
        ck(f'case_{case}_stated_duration',duration==cfg['target_stretches'][case-400])
        if case>=404:ck(f'case_{case}_repeated_content',np.array_equal(env['basis'][2],env['basis'][0]) and np.array_equal(env['bias'][2],env['bias'][0]) and np.array_equal(env['basis'][4],env['basis'][1]))
        reference=r.render(env['initial'],1,.8,env)
        initial=r.registered(reference,teacher);case_rows=next(x for x in held['results'] if x['case']==case)['results']
        saved_diag=next(x for x in diagnostics['cases'] if x['case']==case)['results']
        ck(f'case_{case}_all_eight_modes',len(case_rows)==8 and set(x['mode'] for x in case_rows)==set(cfg['modes']))
        logs={}
        for row in case_rows:
            mode=row['mode'];q=r.loadz(r.TASK/f'outputs/held_{case}_{mode}_queries.npz');logs[mode]=q
            rep=replay(q,env['initial'],180000+case);totalqueries+=rep['queries']
            final=q['actions'][-1];direct=r.registered(r.render(final[:4],int(final[4]),final[5],env),teacher)
            gold=gold_all(q['query_actions'],env,teacher)
            saved_gold=r.loadz(r.TASK/f'outputs/held_{case}_{mode}_gold_queries.npz')['gold']
            error=float(np.max(abs(gold-saved_gold)));maxgold=max(maxgold,error)
            ck(f'{case}_{mode}_all_gold',error<1e-10,{'max_error':error})
            best=int(np.argmin(gold));best_action=q['query_actions'][best]
            best_direct=r.registered(r.render(best_action[:4],int(best_action[4]),best_action[5],env),teacher)
            for index in (0,123,999,2500,3721):
                action=q['query_actions'][index]
                direct_sample=r.registered(r.render(action[:4],int(action[4]),action[5],env,phase=37),teacher)
                maxdirect=max(maxdirect,abs(direct_sample-gold[index]))
            maxdirect=max(maxdirect,abs(best_direct-gold[best]))
            ck(f'{case}_{mode}_direct_saved_final',abs(direct-row['final_gold'])<1e-10 and abs(initial-row['initial_gold'])<1e-10)
            improvement=1-direct/initial;stretch_error=abs(final[5]-duration)
            semantic=r.registered(r.render(target,int(final[4]),duration,env),teacher)
            success=improvement>=.95 and direct<=.1 and stretch_error<=.02
            old=next(x for x in saved_diag if x['mode']==mode)
            ck(f'{case}_{mode}_success_and_semantic',bool(success)==old['success'] and bool(semantic<=1e-12)==old['correct_semantic_order'])
            rows.append({'case':case,'mode':mode,'final_gold':direct,'initial_reference_gold':initial,'improvement':improvement,
                         'success':bool(success),'correct_observable_order':bool(semantic<=1e-12),'stretch_error':stretch_error,
                         'best_gold':float(gold[best]),'best_gold_query_index':best,'regret':float(direct-gold[best]),
                         'best_gold_feedback_minus_selected':float(q['query_costs'][best]-rep['feedback']),
                         'scalar_replay':rep,'all_gold_max_error':error})
        for mode in ('state','template'):
            ck(f'{case}_{mode}_matches_oracle',np.array_equal(logs[mode]['query_actions'],logs['oracle']['query_actions']) and np.max(abs(logs[mode]['query_costs']-logs['oracle']['query_costs']))<1e-12)
        print(json.dumps({'case':case,'scalar_queries_replayed':totalqueries,'elapsed':time.monotonic()-start}),flush=True)
    ck('all_238208_queries',totalqueries==238208)
    ck('independent_direct_gold_agreement',maxdirect<1e-10,{'max_error':maxdirect})
    summary={}
    for mode in cfg['modes']:
        rr=[x for x in rows if x['mode']==mode]
        summary[mode]={'n':len(rr),'successes':sum(x['success'] for x in rr),'correct_order':sum(x['correct_observable_order'] for x in rr),
                       'mean_removal':float(np.mean([x['improvement'] for x in rr])),'mean_MSE':float(np.mean([x['final_gold'] for x in rr])),
                       'regret_gt_01':sum(x['regret']>.01 for x in rr)}
    out={'utc':r.now(),'all_pass':all(x['pass'] for x in checks),'checks':checks,'rows':rows,'summary':summary,
         'total_queries':totalqueries,'independent_gold_max_error':maxgold,'samplewise_gold_max_error':maxdirect,
         'runtime_seconds':time.monotonic()-start,'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'scope':'Independent scalar replay and prefix-integral/samplewise gold checks, not rerunning the neural campaign.'}
    r.dump('LOG_AUDIT.json',out);print(json.dumps({'all_pass':out['all_pass'],'checks':len(checks),'summary':summary,'runtime_seconds':out['runtime_seconds']},indent=2),flush=True)

if __name__=='__main__':main()
