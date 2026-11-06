"""One frozen content x timing diagnostic on consumed cases."""
import review_core as r
import numpy as np,time,resource,hashlib,json

def main():
    started=time.monotonic()
    freeze=json.loads((r.HERE/'DIAGNOSTIC_FREEZE.json').read_text())
    for name,h in freeze['sha256'].items():assert hashlib.sha256((r.HERE/name).read_bytes()).hexdigest()==h
    rows=[];source_checks=[]
    for case in range(400,408):
        pack=r.loadz(r.SRC/f'held_{case}_model.npz')
        env=r.loadz(r.SRC/f'held_{case}_environment.npz',('basis','bias','orders','initial'))
        truth=r.loadz(r.SRC/f'held_{case}_truth.npz')
        q=r.loadz(r.TASK/f'outputs/held_{case}_population_queries.npz')
        target=np.asarray(truth['target']);stretch=float(truth['target_stretch']);order=int(truth['target_order'])
        final=q['actions'][-1,:4]
        waves=[];metadata=[]
        for alpha in (0.,.5,1.):
            shape=target+alpha*(final-target)
            for delta in (-.02,-.005,0.,.005,.02):
                waves.append(r.render(shape,order,stretch+delta,env))
                metadata.append({'alpha':alpha,'duration_delta':delta,'gap_ms':0,'shape':shape,'stretch':stretch+delta})
            for gap in (-20,20):
                waves.append(r.render(shape,order,stretch,env,gap=gap))
                metadata.append({'alpha':alpha,'duration_delta':0.,'gap_ms':gap,'shape':shape,'stretch':stretch})
        waves=np.asarray(waves);gold=np.array([r.registered(x,pack['teacher']) for x in waves])
        cost,mom=r.integrate_batch(waves,pack)
        conditions=[('population',pack,cost,mom)]
        if case==400:
            fixed=r.loadz(r.SRC/'held_400_fixed_model.npz')
            fixed_cost,fixed_mom=r.integrate_batch(waves,fixed)
            conditions.append(('fixed_population',fixed,fixed_cost,fixed_mom))
        for name,current,cc,mm in conditions:
            for i,meta in enumerate(metadata):
                base=next(j for j,m in enumerate(metadata) if m['alpha']==meta['alpha'] and m['duration_delta']==0 and m['gap_ms']==0)
                residual=(mm[base]-current['prototype_mean'])/np.sqrt(current['prototype_variance'])
                change=(mm[i]-mm[base])/np.sqrt(current['prototype_variance'])
                cross=float(2*np.mean(residual*change));temporal=float(np.mean(change*change));delta=float(cc[i]-cc[base])
                assert abs(delta-cross-temporal)<1e-11
                wrong=delta<0 and gold[i]>gold[base]+1e-12
                rows.append({'case':case,'critic':name,'candidate':i,**meta,'base_candidate':base,'cost':float(cc[i]),'base_cost':float(cc[base]),
                             'gold':float(gold[i]),'base_gold':float(gold[base]),'delta_cost':delta,'delta_gold':float(gold[i]-gold[base]),
                             'cross_term':cross,'positive_temporal_feature_term':temporal,
                             'distinct_temporal_feature':temporal>1e-24,
                             'wrong_corrective_preference':bool(wrong),
                             'wrong_preference_robust_at_eps':{str(eps):bool(wrong and -delta>2*eps) for eps in (0.,1e-8,1e-6)}})
            # Predetermined common target and one acquired-content shortening.
            if case in (400,407):
                for index in (2,15):
                    src=r.source_trace(waves[index],current)
                    z=src/100.;sf=np.r_[z.mean(0),(z*z).mean(0)]
                    ss=float(np.mean((sf-current['prototype_mean'])**2/current['prototype_variance']))
                    err=float(np.max(abs(sf-mm[index])))
                    assert err<1e-10 and abs(ss-cc[index])<1e-10
                    source_checks.append({'case':case,'critic':name,'candidate':index,'source_cost':ss,'independent_cost':float(cc[index]),'feature_max_error':err})
        r.dump('CROSSED_PROGRESS.json',{'utc':r.now(),'last_completed_case':case,'rows':len(rows),'elapsed_seconds':time.monotonic()-started})
        print(json.dumps({'case':case,'elapsed':time.monotonic()-started,'rows':len(rows)}),flush=True)
    A=np.array([[1.,1.],[0.,1.]])
    toy=[]
    for c,t in ((0.,0.),(.1,0.),(.1,-.05)):
        x=np.array([c,t]);toy.append({'content_error':c,'timing_error':t,'feature_cost':float(np.sum((A@x)**2)),'true_error':float(x@x)})
    assert np.linalg.det(A)!=0 and toy[2]['feature_cost']<toy[1]['feature_cost'] and toy[2]['true_error']>toy[1]['true_error']
    summary=[]
    for critic in ('population','fixed_population'):
        for alpha in (0.,.5,1.):
            rr=[x for x in rows if x['critic']==critic and x['alpha']==alpha and (x['duration_delta']!=0 or x['gap_ms']!=0)]
            summary.append({'critic':critic,'alpha':alpha,'candidates':len(rr),'cases':len(set(x['case'] for x in rr)),
                            'wrong_preference_candidates':sum(x['wrong_corrective_preference'] for x in rr),
                            'cases_with_wrong_preference':sorted(set(x['case'] for x in rr if x['wrong_corrective_preference'])),
                            'robust_wrong_candidates_by_eps':{str(e):sum(x['wrong_preference_robust_at_eps'][str(e)] for x in rr) for e in (0.,1e-8,1e-6)}})
    result={'utc':r.now(),'predeclared_protocol':'DIAGNOSTIC_PROTOCOL.md','rows':rows,'summary':summary,'source_checks':source_checks,
            'invertible_metric_toy':{'A':A,'determinant':float(np.linalg.det(A)),'points':toy},
            'runtime_seconds':time.monotonic()-started,'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'scope':'Postvalidation finite diagnostic; no new plant, model fit or temporal architecture; source/formula checks only.'}
    r.dump('CROSSED_DIAGNOSTIC.json',result);np.savez_compressed(r.HERE/'CROSSED_FEATURES_LAST_CASE.npz',features=mom,cost=cost,gold=gold)
    print(json.dumps({'summary':summary,'source_checks':source_checks,'toy':toy,'runtime_seconds':result['runtime_seconds']},indent=2),flush=True)

if __name__=='__main__':main()
