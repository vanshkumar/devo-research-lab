"""Author numerical/source audit; distinct independent review remains unrun."""
from model import *
from scipy.integrate import quad
import sys

def numerics():
    expanded=[]
    for a in [.7,1.4,2.2]:
        for fraction in [.2,.5,.8]:
            t=a*a*np.array([.05,.1,.2,.25,.4])
            f=fzero(t,a,a*fraction,'image');h=fzero(t,a,a*fraction,'spectral')
            expanded.append(float(np.max(np.abs(f-h))))
    analytic=[]
    for z in [.25,.5,.75]:
        p=np.array([np.log(1.4),logit(z),.2,np.log(3),np.log(2),np.log(.5),np.log(2.5)])
        norm,pred=integrals(p,384,(.2,12))
        a,z,t0,vs=unpack(p)
        upper=-np.expm1(-2*vs*a*z)/(-np.expm1(-2*vs*a))
        pc=np.r_[upper[:3],1-upper[3:]]
        mrt=t0+(a*upper-a*z)/vs
        analytic.append({'z':z,'mass_max_error':float(np.max(abs(norm-1))),'pc_max_error':float(np.max(abs(pred[:,0]-pc))),'mean_rt_max_error_s':float(np.max(abs(pred[:,1]-mrt)))})
    ss=load('SOURCE_FIT.json');pars=[ss['center']]+ss['source_baseline_parameters']
    for key,quality in [('P_mapping',False),('Q_mapping',True)]:pars += [transport(p,ss[key],quality) for p in ss['source_baseline_parameters']]
    if (ROOT/'PREDICTIONS.json').exists():
        pp=load('PREDICTIONS.json')
        pars+=pp['baseline_parameters']
        pars+=[transport(p,ss['P_mapping']) for p in pp['baseline_parameters']]
        pars+=[transport(p,ss['Q_mapping'],True) for p in pp['baseline_parameters']]
    comparisons=[]
    for p in pars:
        n96,y96=integrals(p,96);n192,y192=integrals(p,192);n384,y384=integrals(p,384)
        comparisons.append({'normalizer96_384':float(np.max(abs(n96-n384))),'mean96_384':float(np.max(abs(y96-y384))),'mean192_384':float(np.max(abs(y192-y384)))})
    result={'at':stamp(),'expansion_max_abs_difference':max(expanded),'analytical_checks':analytic,'quadrature':comparisons,'author_only':True}
    dump('NUMERICAL_AUDIT.json',result)
    assert max(expanded)<1e-10
    assert max(max(x[k] for k in ['mass_max_error','pc_max_error','mean_rt_max_error_s']) for x in analytic)<1e-7
    assert max(x['mean192_384'] for x in comparisons)<1e-5
    assert max(x['normalizer96_384'] for x in comparisons)<1e-5
    run_record('NUMERICAL_AUDIT',15000000)
    print('Numerics pass',max(expanded),analytic,'quadrature maxima',{k:max(x[k] for x in comparisons) for k in comparisons[0]})

def reconstruct():
    f=load('FREEZE.json');assert freeze_pins(list(f['files']))==f['files']
    pred=load('PREDICTIONS.json');score=load('SCORES.json');ss=load('SOURCE_FIT.json')
    assert freeze_pins(['PREDICTIONS.json'])==load('PREDICTION_PIN.json')['sha256']
    df=data();target=[];baseline=[];features=[];pin=[]
    for pid in pred['ids']:
        # Direct extraction, separate from trials()/summary() for labels, means and counts.
        g=df[(df.pid==pid)&(df.block==2)]
        g=g[g.response.isin(['word','nonword'])&g.rt.between(.18,3)]
        val=[]
        for c in range(4):
            h=g[g.cat==c];val.append([float((h.response==h.stim_cat).sum()/len(h)),float(h.rt.sum()/len(h))])
        target.append(val)
        b=trials(df,pid,1);yy,ff,nn=summary(b);baseline.append(yy);features.append(ff)
        pin.append({'id':pid,'n_target_valid':len(g),'n_target_censored':96-len(g),'n_target_rulepaper':int(g.rt.between(.3,2.5).sum())})
    target=np.array(target);B=np.array(baseline);F=np.array(features)
    err=float(np.max(abs(target-score['target_values'])));assert err<1e-14
    forecast=empirical_predict(B,F,ss['empirical'])
    forecast['P']=np.array([integrals(transport(p,ss['P_mapping']),192)[1] for p in pred['baseline_parameters']])
    forecast['Q']=np.array([integrals(transport(p,ss['Q_mapping'],True),192)[1] for p in pred['baseline_parameters']])
    ferr={k:float(np.max(abs(v-pred['predictions'][k]))) for k,v in forecast.items()};assert max(ferr.values())<1e-14
    # Outcome-suffix perturbation: replace all held block>=2choice/RT values; baseline inputs must stay exactly identical.
    changed=df.copy();ix=(changed.pid>=10)&(changed.block>=2);changed.loc[ix,'rt']=2.99;changed.loc[ix,'response']='error';changed.loc[ix,'correct']=0
    b2=[summary(trials(changed,pid,1)) for pid in pred['ids']]
    assert np.array_equal(B,np.array([x[0] for x in b2])) and np.array_equal(F,np.array([x[1] for x in b2]))
    # Main maps and feature functions take no target outcome argument; this certifies the implemented input restriction, not historical non-access.
    sensitivity=[]
    for pid in pred['ids']:
        sensitivity.append(summary(trials(df,pid,2,(.3,2.5)))[0])
    from analysis import evaluate
    sensitive=evaluate(pred,np.array(sensitivity));dump('PAPER_CUTOFF_SENSITIVITY.json',{'at':stamp(),'postvalidation':True,'target_cutoff_changed_only':True,'baseline_forecasts_unchanged':True,'scores':sensitive})
    result={'at':stamp(),'all_freeze_pins_match':True,'raw_target_max_difference':err,'forecast_max_differences':ferr,'suffix_input_invariance':True,'rows':pin,'saved_order':[f['at'],pred['at'],score['at']],'ordering_is_independent_historical_proof':False,'author_only':True}
    dump('RAW_AND_PREDICTION_AUDIT.json',result);run_record('RECONSTRUCT',35000000);print(json.dumps(result,indent=2))

if __name__=='__main__':{'numerics':numerics,'reconstruct':reconstruct}[sys.argv[1]]()
