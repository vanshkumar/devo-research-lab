"""Input-only external schedule recovery; external behavioral fields never accessed.
Uses lead design under review, independently generates complete synthetic trajectories,
and batch-computes participant-cluster uncertainty. No empirical external calibration.
"""
from pathlib import Path
import sys,json,hashlib,argparse
import numpy as np
from scipy import stats
from scipy.linalg.blas import dgemm
HERE=Path(__file__).resolve().parent
CAMPAIGN=HERE.parents[1]
sys.path.insert(0,str(CAMPAIGN/'experiments'))
import transfer as tr


def dot(a,b):return dgemm(alpha=1.,a=np.asfortranarray(a),b=np.asfortranarray(b))


def prepare(people,readout):
    result=[]
    for h in range(1,6):
        d=tr.make_external_design(people,h,readout)
        pp=tr.prep_external(d)
        pp['times']=np.array([m[1]-1 for m in d['meta']])
        pp['Wcontrast']=np.einsum('i,ij->j',d['contrast'],pp['W'])
        pp['correction']=len(people)/(len(people)-1)*(len(d['Y'])-1)/(len(d['Y'])-pp['p'])
        result.append(pp)
        print('prepared',readout,h,len(d['Y']),pp['p'],np.linalg.matrix_rank(pp['RZ']),flush=True)
    return result


def statistics(preps,paths):
    reps=paths.shape[0];ngroups=paths.shape[1]
    curves=[];scores=np.zeros((ngroups,reps))
    for h,p in enumerate(preps,start=1):
        d=p['d'];g=d['groups'];t=p['times']
        yy=paths[:,g,t+h]-sum(paths[:,g,t-k] for k in range(1,6))/5
        Y=yy.T.copy()
        beta=dot(p['W'],Y)
        residual=Y-dot(p['Q'],dot(p['Q'].T,Y))-dot(p['RZ'],beta)
        curves.append(np.einsum('i,ij->j',d['contrast'],beta))
        for owner in range(ngroups):
            keep=(g==owner)
            scores[owner]+=np.einsum('i,ij->j',p['Wcontrast'][keep],residual[keep])/5*np.sqrt(p['correction'])
    curves=np.asarray(curves)
    theta=curves.mean(axis=0);se=np.sqrt(np.sum(scores*scores,axis=0))
    return theta,se,curves


def generate(people,reps,seed):
    rng=np.random.default_rng(seed);n=len(people);length=len(people[0]['c'])
    base=np.zeros((n,length));unit_signal=np.zeros_like(base)
    for i,p in enumerate(people):
        c,j=p['c'],p['j'];state=0.;stimulus=np.zeros(length)
        for t in range(length):
            # State before current exposure plus direct current readout correction.
            kind='none' if j[t]==0 else ('flicker' if j[t]==.01 else ('to' if j[t]==c[t] else 'away'))
            gains={'none':.14,'flicker':.08,'to':.09,'away':.12}
            direct={'none':0.,'flicker':.03,'to':.12,'away':-.07}
            base[i,t]=state+direct[kind]*np.sign(c[t])
            state=.8*state+gains[kind]*c[t]
            if 103<=t<=902 and (j[t]==0 or j[t]==c[t]) and j[t-1]==0:
                stimulus[t]=(float(j[t]!=0)-.5)*c[t-1]/4
        for h in range(1,6):unit_signal[i,h:]+=stimulus[:-h]
    multipliers=rng.lognormal(-.25**2/2,.25,size=(reps,n,1))
    noise_scale=rng.lognormal(-.15**2/2,.15,size=(reps,n,1))
    noise=np.zeros((reps,n,length))
    noise[:,:,0]=rng.normal(0,2.2,size=(reps,n))
    for t in range(1,length):noise[:,:,t]=.55*noise[:,:,t-1]+rng.normal(0,2.2*np.sqrt(1-.55**2),size=(reps,n))
    noise+=rng.normal(0,1.3,size=noise.shape)
    phase=rng.uniform(0,2*np.pi,size=(reps,n,1));amplitude=rng.normal(0,.4,size=(reps,n,1))
    smooth=amplitude*np.sin(2*np.pi*np.arange(length)[None,None,:]/360+phase)
    linear=rng.normal(0,1,size=(reps,n,1))*(np.arange(length)[None,None,:]-450)/450
    trajectories=multipliers*base[None,:,:]+noise_scale*noise+smooth+linear
    return trajectories,base,unit_signal


def rates(est,se,true):
    crit=stats.t.ppf(.975,17);lo=est-crit*se;hi=est+crit*se
    return {'truth':true,'mean_estimate':float(est.mean()),'bias':float(est.mean()-true),'sd_estimate':float(est.std(ddof=1)),'mean_cluster_se':float(se.mean()),'mean_squared_error':float(np.mean((est-true)**2)),'coverage95':float(np.mean((lo<=true)&(hi>=true))),'reject_zero95':float(np.mean((lo>0)|(hi<0))),'wrong_signed_significant':float(np.mean((hi<0) if true>0 else (lo>0))) if true!=0 else None,'interval95_inside_practical_margin':float(np.mean((lo>-.2)&(hi<.2))),'median_interval_width':float(np.median(hi-lo))}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--replicates',type=int,default=300);ap.add_argument('--seed',type=int,default=2026102817);args=ap.parse_args()
    people=tr.load_external(inputs_only=True)
    trajectories,base,signal=generate(people,args.replicates,args.seed)
    report={'exposure':'Input-only external loader; no HandError/HandAngle values accessed. Generated states and noise supply every analyzed outcome.','replicates_per_sign':args.replicates,'seed':args.seed,'generator':{'fixed_retention':.8,'input_gain_by_condition':{'none':.14,'flicker':.08,'to':.09,'away':.12},'direct_endpoint_by_condition':{'none':0,'flicker':.03,'to':.12,'away':-.07},'gain_heterogeneity_log_sd':.25,'noise_heterogeneity_log_sd':.15,'ar_noise_marginal_sd':2.2,'ar_rho':.55,'independent_noise_sd':1.3,'slow_sinusoidal_drift_sd':.4,'linear_drift_sd':1.,'effect':'For every eligible NoJump/JumpTo index, .2*(J-.5)*(prior_clamp/4)*I(previous_target_stationary) enters each of the following five endpoints; signed ±.2 and zero tested.'},'source_sha256':hashlib.sha256((tr.SOURCE/'task_success_fig3.csv').read_bytes()).hexdigest(),'transfer_code_sha256':hashlib.sha256((CAMPAIGN/'experiments/transfer.py').read_bytes()).hexdigest(),'variants':{}}
    for readout in ('all','stationary'):
        ps=prepare(people,readout)
        details={'support':[{'h':h,'n':len(p['d']['Y']),'nuisance_rank':p['rank'],'full_rank':p['p'],'interaction_rank':int(np.linalg.matrix_rank(p['RZ'])),'interaction_condition':float(np.linalg.cond(p['RZ']))} for h,p in enumerate(ps,1)],'results':[]}
        # Independent batch algebra cross-check against the lead single-fit functions.
        synthetic=trajectories[0]+.2*signal
        leadfits=[]
        for h,p in enumerate(ps,1):
            g=p['d']['groups'];t=p['times'];y=synthetic[g,t+h]-sum(synthetic[g,t-k] for k in range(1,6))/5
            leadfits.append(tr.fit(p,y))
        lead=tr.curve_summary(leadfits)
        batch=statistics(ps,synthetic[None,:,:])
        details['batch_vs_lead_max_difference']=float(max(abs(batch[0][0]-lead['estimate']),abs(batch[1][0]-lead['se'])))
        for effect in (-.2,0.,.2):
            known_theta,_,known_curve=statistics(ps,(base+effect*signal)[None,:,:])
            theta,se,curves=statistics(ps,trajectories+effect*signal[None,:,:])
            rec=rates(theta,se,effect)
            rec.update(noiseless_finite_schedule_projection=float(known_theta[0]),noiseless_curve=known_curve[:,0].tolist(),mean_curve=curves.mean(axis=1).tolist(),coverage95_of_noiseless_projection=float(np.mean(np.abs(theta-known_theta[0])<=stats.t.ppf(.975,17)*se)))
            details['results'].append(rec)
            print(readout,effect,json.dumps(rec),flush=True)
        report['variants'][readout]=details
        (CAMPAIGN/'outputs/transfer_recovery/recovery.json').write_text(json.dumps(report,indent=2)+'\n')
    print('wrote',CAMPAIGN/'outputs/transfer_recovery/recovery.json',flush=True)

if __name__=='__main__':main()
