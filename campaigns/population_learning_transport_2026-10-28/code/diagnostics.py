"""Secondary challenges after the one frozen source score; no gate replacement.

Only saved source prefixes, forecasts and already-scored endpoints are read.
No external loader or external values. The two perturbations were already
examined in the consumed-prefix audit; here they test the new-source miss.
"""
import json,time
import numpy as np
from campaign import C,MODEL,BANK,MODELS,load_rnn,load_bank,draw_initial,calibration_particles,fit_competence,simulate,digest,seed_for

class SavedCalibration:
    def __init__(self,model,cal):self.model=model;self.cal=cal;self.hidden=model.hidden
    def initial_state(self,prefix,method):
        return dict(w=np.asarray(self.cal['endpoint']),h=np.asarray(self.cal['hidden_endpoint']),w0=np.asarray(self.cal['w0']))
    def sequence(self,*a,**kw):return self.model.sequence(*a,**kw)

def main():
    out=C/'artifacts/diagnostics';out.mkdir(parents=True,exist_ok=True)
    f=C/'artifacts/forecasts/source';cf=C/'artifacts/forecasts/source_policy_swap'
    result=json.loads((C/'artifacts/results/SOURCE_RESULT.json').read_text());subjects=result['subjects']
    model=load_rnn(MODEL);bank=load_bank(BANK);policy={};partial={};variants={k:[] for k in ('future_retention_0p8','prefix_static_omission')}
    reference={};model_diagnostics={}
    def stats(a):
        a=np.asarray(a);v=a.mean(2)
        return dict(mean=float(v.mean()),mean_curve=a.mean((0,1)).tolist(),animal_means=v.mean(1).tolist(),
                    conditional_MC_SE=float(np.sqrt(np.var(v,axis=1,ddof=1).sum()/v.shape[1])/v.shape[0]))
    for kind in MODELS:
        a=[];b=[];pa=[];pb=[]
        for s in subjects:
            with np.load(f/(s+'__'+kind+'.npz'),allow_pickle=False) as z:
                a.append(z['samples'][:,:,:2].mean(2));pa.append(z['probe100'])
            with np.load(cf/(s+'__'+kind+'.npz'),allow_pickle=False) as z:
                b.append(z['samples'][:,:,:2].mean(2));pb.append(z['probe100'])
        a,b,pa,pb=map(np.asarray,(a,b,pa,pb))
        policy[kind]=dict(standard=stats(a),fixed=stats(b),fixed_minus_adaptive=stats(b-a),probe_fixed_minus_adaptive=stats(pb-pa))
    observed=np.asarray(result['models']['rnn']['observed_curve'])
    volume_checks=[]
    for i,s in enumerate(subjects):
        t=time.monotonic();seed=seed_for(s);meta=json.loads((f/(s+'__rnn.json')).read_text())
        with np.load(f/(s+'__prefix.npz'),allow_pickle=False) as z:
            prefix={k:z[k] for k in z.files if k!='future_session_start'};starts=z['future_session_start']
        n=128;common=draw_initial(prefix,bank,n,seed+211,exclude=s,competence='growth')
        state,cal=calibration_particles(SavedCalibration(model,meta['calibration']),prefix,n,seed+313)
        w,cov,_=fit_competence(prefix,ridge=.5)
        persistence=np.random.default_rng(seed+313).multivariate_normal(w,cov,size=n)
        for name,kw in [('future_retention_0p8',dict(retention=.8,hidden_retention=.8)),('prefix_static_omission',dict(omission_mode='static'))]:
            ans=simulate(model,prefix,starts,common,state,persistence,'rnn','standard',seed,**kw)
            variants[name].append(ans['samples'][:,:,:2].mean(2))
        if i<2:
            a=simulate(model,prefix,starts,common,state,persistence,'rnn','standard',seed)
            modified={k:v.copy() for k,v in prefix.items()}
            modified['rewardVolume']=np.where(modified['feedbackType']>0,100.,0.)
            b=simulate(model,modified,starts,common,state,persistence,'rnn','standard',seed)
            volume_checks.append(dict(subject=s,prefix_reward_metadata_replaced_with_100uL=True,
                                      generated_samples_exact=bool(np.array_equal(a['samples'],b['samples'])),
                                      generated_weights_exact=bool(np.array_equal(a['weights'],b['weights']))))
        print(json.dumps(dict(subject=s,seconds=time.monotonic()-t)),flush=True)
    sensitivity={}
    for k,arr in variants.items():
        a=np.asarray(arr);mean=a.mean((0,1));err=observed-mean
        sensitivity[k]=dict(particles=128,bias=float(err.mean()),curve_mae=float(np.abs(err).mean()),max_bin_error=float(np.abs(err).max()),forecast_curve=mean.tolist(),
                            note='postvalidation diagnostic only; future-only perturbation with frozen primary prefix calibration, never a replacement gate')
        np.savez_compressed(out/(k+'.npz'),subjects=np.array(subjects),samples=a)
    with np.load(f/'NYU-21__observed.npz',allow_pickle=False) as z:yy=z['observed'];counts=z['counts']
    partial['NYU-21']=dict(observed=yy.tolist(),counts=counts.tolist(),models={})
    for kind in MODELS:
        with np.load(f/('NYU-21__'+kind+'.npz'),allow_pickle=False) as z:pp=z['samples'].mean(0)
        partial['NYU-21']['models'][kind]=dict(predicted=pp.tolist(),equal_side_curve_mae=float(np.abs((yy[:,:2]-pp[:,:2]).mean(1)).mean()))
    final=dict(scope='secondary source-only diagnostics after fixed primary failure; no new learner, primary changes or external reads',
               source_policy_swap=policy,sensitivity=sensitivity,volume_metadata_invariance=volume_checks,partial=partial,
               model_sha256=digest(MODEL),bank_sha256=digest(BANK))
    (out/'RESULT.json').write_text(json.dumps(final,indent=2)+'\n')
    print(json.dumps(dict(policy_gap=policy['rnn']['fixed_minus_adaptive']['mean'],sensitivity=sensitivity,volume_checks=volume_checks),indent=2),flush=True)

if __name__=='__main__':main()
