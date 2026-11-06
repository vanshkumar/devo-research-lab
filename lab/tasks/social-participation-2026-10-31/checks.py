"""Execute the bounded first-courter sensitivity and numerical rechecks."""
import analyze as a
import hashlib
import json
import resource
import time
from datetime import datetime, timezone

np = a.np
OUT = a.OUT

def read_json(name):
    return json.loads(a.read(OUT/name))

def relative_main_cells(rows):
    p = np.zeros(15)
    for r in rows:
        q = r['Q'] if r['z']==1 else {0:0,1:2,2:1,3:4,4:3}[r['Q']]
        m = 0 if not r['B'] else 1 if r['copy'] else 2
        p[3*q+m] += 1/len(rows)
    return p

def first_courter_witness(p, theta):
    selected = np.array([q>=3 and m!=0 for q in range(5) for m in range(3)])
    copies = np.array([m==1 for q in range(5) for m in range(3)])
    first = np.array([0 if q==0 else 1 if q in (1,3) else 2
                      for q in range(5) for m in range(3)])
    kernel = np.zeros((2,15)); gate = []; lo, hi = 0., 1.
    for f in range(3):
        mask = first==f; mass = p[mask].sum()
        ar = p[mask & selected & copies].sum()/mass
        bo = p[mask & selected & ~copies].sum()/mass
        lo = max(lo,ar); hi = min(hi,1-bo)
        s = np.array([ar/theta,bo/(1-theta)])
        gate.append({'first_courter':('none','reference','opposite')[f],
                     'marginal_first_courter':float(mass),
                     'eligible_reference_mass_within_first':float(ar),
                     'eligible_opposite_mass_within_first':float(bo),
                     'eligibility_given_W_reference':float(s[0]),
                     'eligibility_given_W_opposite':float(s[1]),
                     'revelation_risk_ratio':float(s[0]/s[1]) if s[1]>0 else None})
        for j in np.where(mask)[0]:
            if selected[j]:
                w = 0 if copies[j] else 1
                kernel[w,j] = p[j]/(theta if w==0 else 1-theta)
            else:
                remaining = p[mask & ~selected].sum()
                kernel[:,j] = mass*(1-s)*p[j]/remaining
    feasible = bool(lo-1e-12 <= theta <= hi+1e-12)
    result = {'theta':theta,'feasible_theta_interval':[float(lo),float(hi)],
              'feasible':feasible,'gate_by_first_courter':gate}
    if feasible:
        rebuilt = theta*kernel[0]+(1-theta)*kernel[1]
        f_marginals = [[float(kernel[w,first==f].sum()) for f in range(3)] for w in range(2)]
        result.update({'original_15cell':p.tolist(),'latent_emission_2x15':kernel.tolist(),
                       'reconstructed_15cell':rebuilt.tolist(),
                       'max_cell_error':float(np.max(np.abs(rebuilt-p))),
                       'W_row_sums':kernel.sum(axis=1).tolist(),
                       'first_courter_given_W':f_marginals,
                       'max_W_first_courter_dependence':float(np.max(np.abs(np.array(f_marginals[0])-f_marginals[1])))})
        assert result['max_cell_error']<1e-12
        assert result['max_W_first_courter_dependence']<1e-12
        assert np.min(kernel)>-1e-12
        assert np.max(np.abs(kernel.sum(axis=1)-1))<1e-12
    else:
        result['failure']='Required gate probability exceeds one; no witness under W independent of first courter.'
    return result

def order_diagnostic(all_rows):
    rows = [r for r in all_rows if r['t']=='T']
    dates = sorted(set(r['date'] for r in all_rows))
    # Four columns: eligible n/k when reference first, then opposite first.
    counts = []
    for d in dates:
        e = [r for r in rows if r['date']==d and r['eligible']]
        counts.append([sum(r['first_match']==1 for r in e),
                       sum(r['first_match']==1 and r['copy']==1 for r in e),
                       sum(r['first_match']==0 for r in e),
                       sum(r['first_match']==0 and r['copy']==1 for r in e)])
    counts = np.array(counts)
    totals = counts.sum(axis=0)
    rng = np.random.default_rng(a.SEED)
    draws = rng.integers(0,len(dates),size=(5000,len(dates)))
    boot = counts[draws].sum(axis=1)
    keep = (boot[:,0]>0)&(boot[:,2]>0)
    vals = boot[keep,1]/boot[keep,0]-boot[keep,3]/boot[keep,2]
    q1,q0 = totals[1]/totals[0],totals[3]/totals[2]
    return {'counts_nk_reference_then_opposite_first':totals.tolist(),
            'copy_reference_first':float(q1),'copy_opposite_first':float(q0),
            'difference':float(q1-q0),'date_bootstrap_95':np.quantile(vals,[.025,.975]).tolist(),
            'bootstrap_resamples':5000,'undefined_resamples':int((~keep).sum()),
            'seed':a.SEED,
            'accept_first_wait_point_inequality_feasible':bool(q1<=q0),
            'restricted_model_required_inequality':'q_reference_first <= theta <= q_opposite_first',
            'interpretation':'A descriptive violation under independent W/first-courter, preferential accept-matched-first, and equal completion after waiting. Not a randomized/causal test or calibrated population interval.'}

def numeric_recheck(rows):
    saved_cv = read_json('CV_FITS.json')
    saved_ecv = read_json('ELIGIBLE_ONLY_FITS.json')
    saved_full = read_json('FULL_FITS.json')
    contexts = [next(r for r in rows if r['t']==t and r['z']==z)
                for t in ('T','C1','C2') for z in (-1,1)]
    original_flags = []
    max_prob_error,max_nll_error = 0.,0.
    rechecks=[]
    for eligible_only,folds in ((False,saved_cv),(True,saved_ecv)):
        source_rows = [r for r in rows if r['eligible']] if eligible_only else rows
        for fold in folds:
            date,model=fold['held_date'],fold['model']
            old_beta={s:np.array(v['coefficients']) for s,v in fold['fits'].items()}
            for s,v in fold['fits'].items():
                if not v['success']:
                    original_flags.append({'held_date':date,'model':model,'eligible_only':eligible_only,**v})
            train=[r for r in source_rows if r['date']!=date]
            test=[r for r in source_rows if r['date']==date]
            new_beta,rec=a.fit_model(train,model,eligible_only,start_shift=-.2,strict=True)
            old_loss=a.evaluate(test,model,old_beta,eligible_only)
            new_loss=a.evaluate(test,model,new_beta,eligible_only)
            err=max(float(np.max(np.abs(old_loss[s]-new_loss[s]))) for s in old_loss)
            if eligible_only:
                pp=a.probabilities(contexts,model,old_beta,True)['Y']
                pn=a.probabilities(contexts,model,new_beta,True)['Y']
            else:
                pp=a.joint_cells(contexts,model,old_beta)
                pn=a.joint_cells(contexts,model,new_beta)
            perr=float(np.max(np.abs(pp-pn)))
            max_prob_error=max(max_prob_error,perr);max_nll_error=max(max_nll_error,err)
            rechecks.append({'held_date':date,'model':model,'eligible_only':eligible_only,
                             'max_probability_difference':perr,'max_held_row_nll_difference':err,
                             'tight_fit_records':rec})
    full_beta={s:np.array(v['coefficients']) for s,v in saved_full['primacy'].items()}
    strict,strict_rec=a.fit_model(rows,'primacy',start_shift=.25,strict=True)
    p=a.joint_cells(contexts,'primacy',full_beta)
    repeat_err=float(np.max(np.abs(p-a.joint_cells(contexts,'primacy',strict))))
    swapped,swap_rec=a.fit_model(a.color_swap(rows),'primacy',strict=True)
    idx=[3*{0:0,1:2,2:1,3:4,4:3}[q]+{0:0,1:2,2:1}[m]
         for q in range(5) for m in range(3)]
    swap_err=float(np.max(np.abs(p-a.joint_cells(a.color_swap(contexts),'primacy',swapped)[:,idx])))
    # Original RUN's one non-success flag could be in the unsaved synthetic folds.
    control_flags=[]; control_replays=[]
    for g,seed in ((1.,20261032),(0.,20261033)):
        start=len(a.FITS)
        sim=a.synthetic(g,seed)
        loss,folds=a.cv(sim,retain_fits=True)
        control_replays.append({'true_g':g,'seed':seed,'cv':a.aggregate(sim,loss),'fold_fits':folds})
        control_flags += [{'true_g':g,**x} for x in a.FITS[start:] if not x['success']]
    summary={'original_empirical_non_success_flags':original_flags,
             'synthetic_non_success_flags_reproduced':control_flags,
             'strict_refit_max_6context_probability_difference':max_prob_error,
             'strict_refit_max_held_row_nll_difference':max_nll_error,
             'full_six_context_repeat_prediction_max_error':repeat_err,
             'full_six_context_color_relabel_max_error':swap_err,
             'rechecked_empirical_fold_models':len(rechecks),
             'strict_empirical_non_success_flags':[x for x in a.FITS[:sum(len(f['tight_fit_records']) for f in rechecks)] if not x['success']],
             'original_scores_preserved':True}
    a.save('NUMERICAL_RECHECK_DETAILS.json',{'summary':summary,'empirical_folds':rechecks,
                                          'full_repeat':strict_rec,'color_relabel':swap_rec,
                                          'synthetic_replay':control_replays})
    assert max_prob_error<1e-5 and max_nll_error<1e-4
    assert repeat_err<1e-5 and swap_err<1e-5
    return summary

def main():
    started=time.time()
    raw=a.read(a.ROOT/'data/social_learning/data_primacy.csv')
    rows=a.reconstruct(raw)
    pins={name:hashlib.sha256(a.read(OUT/name)).hexdigest()
          for name in ('RUN.json','COMPARISON.json','PROTOCOL.md','FIRST_COURTER_CHECK_PLAN.md')}
    main=[r for r in rows if r['t']=='T']
    p=relative_main_cells(main)
    sensitivity={'postvalidation':True,
                 'assumption':'Within T, latent standardized-two-courter W is independent of recorded first-courter category. Noneligible outcomes independent of W conditional on first courter. Eligible Y=W.',
                 'theta_cases':[first_courter_witness(p,theta) for theta in (.5,.45,.375)],
                 'accept_first_wait':order_diagnostic(rows)}
    a.save('FIRST_COURTER_SENSITIVITY.json',sensitivity)
    numerical=numeric_recheck(rows)
    a.save('CHECK_RUN.json',{'completed_utc':datetime.now(timezone.utc).isoformat(),
                            'original_pins':pins,'immutable_input_reads':a.READS,
                            'read_bytes':sum(x['bytes'] for x in a.READS),
                            'elapsed_seconds':time.time()-started,
                            'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                            'numerical_summary':numerical,'new_requests':0,'jobs':0})
    print(json.dumps({'first_courter_sensitivity':[{k:v for k,v in x.items() if k in
                     ('theta','feasible_theta_interval','feasible','gate_by_first_courter','max_cell_error','max_W_first_courter_dependence')}
                      for x in sensitivity['theta_cases']],
                      'accept_first_wait':sensitivity['accept_first_wait'],
                      'numerical':numerical,'elapsed_seconds':time.time()-started},indent=2))

if __name__=='__main__':
    main()
