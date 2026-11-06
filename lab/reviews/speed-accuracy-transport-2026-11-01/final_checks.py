"""Complete the required source/denominator/influence/resource audit, no new model."""
from reconstruct import *
import platform, scipy, pandas

def main():
    d=original();source=read('SOURCE_FIT.json');held=read('PREDICTIONS.json')
    rec=json.loads((HERE/'RECONSTRUCTION.json').read_text())
    numerical=json.loads((HERE/'NUMERICAL_AUDIT.json').read_text())
    own_contrary=json.loads((HERE/'CONTRARY.json').read_text())
    author_contrary=read('CONTRARY.json')
    author_paper=read('PAPER_CUTOFF_SENSITIVITY.json')['scores']
    own_paper=json.loads((HERE/'PAPER_CUTOFF_AUDIT.json').read_text())
    condition_order=[];nominal=[]
    for person in range(1,18):
        where=d['id']==person
        blocks=d['block'][where]
        sequence=list(dict.fromkeys(blocks.tolist()))
        condition_order.append({'id':person,'rows':int(where.sum()),'blocks_in_export_order':sequence,
            'nondecreasing_blocks':bool(np.all(np.diff(blocks)>=0)),
            'all_odd_blocks_speed_even_accuracy':bool(np.all(d['condition'][where]==np.where(blocks%2==1,'speed','accuracy')))})
        for block in [1,2]:
            mask=where&(d['block']==block)
            counts=[int(np.sum(mask&(d['stimulus']=='word')&(d['frequency']==f))) for f in ['high','low','very_low']]+[int(np.sum(mask&(d['stimulus']=='nonword')))]
            nominal.append({'id':person,'block':block,'nominal_category_counts':counts})
            assert counts==[16,16,16,48]
    firstpair=d['block']<=2
    raw_cutoff=(d['rt']<.18)|(d['rt']>3.)|~np.isfinite(d['rt'])|~np.isin(d['response'],['word','nonword'])
    assert np.array_equal(raw_cutoff[firstpair],d['censor'][firstpair])
    reasons=[]
    for group,ids in [('source',range(1,10)),('evaluation',range(10,18))]:
        for block in [1,2]:
            mask=np.isin(d['id'],list(ids))&(d['block']==block)
            reasons.append({'group':group,'block':block,'nominal':int(mask.sum()),
                'censored':int(d['censor'][mask].sum()),
                'invalid_response':int(np.sum(mask&~np.isin(d['response'],['word','nonword']))),
                'RT_below_180ms':int(np.sum(mask&(d['rt']<.18))),
                'RT_above_3000ms':int(np.sum(mask&(d['rt']>3.))),
                'nonfinite_RT':int(np.sum(mask&~np.isfinite(d['rt']))),
                'note':'Reasons may overlap; accuracy denominator is usable responses per cell.'})
    bounds=[]
    params=[('pooled',source['center'],[selected(d,p,1) for p in range(1,10)])]+[
       ('source_'+str(i+1),p,[selected(d,i+1,1)]) for i,p in enumerate(source['source_baseline_parameters'])]+[
       ('held_'+str(i+10),p,[selected(d,i+10,1)]) for i,p in enumerate(held['baseline_parameters'])]
    from scipy.special import logit
    for name,p,rows in params:
        p=np.array(p);maximum=min(min(r['rt'].min() for r in rows)-.005,.7)
        lo=np.array([np.log(.25),logit(.15),.03]+[np.log(.05)]*4)
        hi=np.array([np.log(4.),logit(.85),maximum]+[np.log(12.)]*4)
        margin=np.minimum(p-lo,hi-p)
        bounds.append({'fit':name,'minimum_parameter_box_margin':float(margin.min()),
                       'bounds_hit_at_1e_minus5':np.flatnonzero(margin<1e-5)})
    source_ps=np.array(source['source_baseline_parameters'])
    original_additive_upper=min(selected(d,p,2)['rt'].min()-.005-source_ps[p-1,2] for p in range(1,10))
    fit_comparison={'original_additive_shift_upper_s':original_additive_upper,
                    'original_additive_lower_bound_s':-.10,
                    'original_additive_infeasible':bool(original_additive_upper<-.10),
                    'all_saved_optimization_statuses_success':bool(source['pooled_fit']['success'] and all(x['success'] for x in source['source_baseline_fit_status']) and all(x['success'] for x in held['baseline_status']) and source['P_status']['success'] and source['Q_status']['success']),
                    'original_baseline_box_checks':bounds}
    influence_error=max(abs(a[key]-b[key]) for a,b in zip(rec['leave_one_person'],author_contrary['leave_one_person']) for key in ['joint_P_fractional_gain','accuracy_MSE_gain','RT_MSE_gain'])
    paper_error=max(error(model[key],author_paper['models'][name][key]) for name,model in own_paper['models'].items() for key in model)
    assert influence_error<1e-10 and paper_error<1e-10
    assert fit_comparison['original_additive_infeasible']
    assert all(len(x['bounds_hit_at_1e_minus5'])==0 for x in bounds)
    # A compact current return address; no registry modifications.
    registry=json.loads((HERE.parents[1]/'registry.json').read_text())
    largest=max(json.loads((HERE/'FIRST_CALCULATION.json').read_text())['largest_measured_process_rss_bytes_macos'],
                rec['largest_measured_process_rss_bytes_macos'],own_contrary['largest_measured_process_rss_bytes_macos'],
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    out={'at_utc':stamp(),'current_PI':registry['pi']['thread_id'],'reviewer':'01a1963e-8b48-7421-8169-1bf31d358517',
         'firstpair_nominal_counts':nominal,'release_export_order':condition_order,
         'censor_reason_counts':reasons,'source_and_baseline_fit_checks':fit_comparison,
         'influence_max_difference':influence_error,'paper_cutoff_all_score_max_difference':paper_error,
         'paper_cutoff_target_valid':int(sum(len(selected(d,p,2,(.3,2.5))['rt']) for p in range(10,18))),
         'original_baseline_objective_max_difference':max(x['saved_abs_difference'] for x in rec['baseline_objectives']),
         'original_baseline_objective_96_256_max_difference':max(x['refinement_difference'] for x in rec['baseline_objectives']),
         'original_mapping_objective_max_difference':max(x['saved_abs_difference'] for x in rec['mapping_objectives']),
         'original_mapping_objective_96_256_max_difference':max(x['refinement_difference'] for x in rec['mapping_objectives']),
         'numerics_max_probability_error':max(x['probability_error'] for x in numerical['analytic_mass_probability_mean_checks']),
         'numerics_max_mean_error':max(x['mean_error'] for x in numerical['analytic_mass_probability_mean_checks']),
         'original_held_quadrature_256_384_max_difference':max(x['mean_probability_max_difference'] for x in numerical['held_quadrature_256_384']),
         'contrary_source_objective_192_384_difference':abs(own_contrary['source_refined_objective384']-own_contrary['fit']['changed_map_objective192']),
         'contrary_source_objective_256_384_difference':abs(own_contrary['source_refined_objective384']-own_contrary['source_refined_objective256']),
         'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'pandas':pandas.__version__,'rdata':rdata.__version__},
         'largest_measured_process_rss_bytes_macos':largest,
         'new_source_verification':'ZERO network. Prior-paper practice/feedback/order/original15-person mapping/licensing and publication novelty claims inherited from saved source records; not independently re-fetched. Original release bytes and firstpair joins independently reconstructed.',
         'UNRUN':['full original pooled/source/held optimizer refits','source-person resampling/refitting uncertainty','full raw-Wiener/source-pipeline controls','10%boundary power','confidence-interval coverage','independent source acquisition history or hardware timing','biological mechanism/unique process identification']}
    assert largest<800000000
    save('FINAL_CHECKS.json',out)
    print(json.dumps({key:val for key,val in out.items() if key not in ['firstpair_nominal_counts','release_export_order','source_and_baseline_fit_checks']},default=lambda v:np.asarray(v).tolist()),flush=True)

if __name__=='__main__': main()
