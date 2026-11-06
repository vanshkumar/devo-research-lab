"""Source-only saturated current/next-input control, no Figure4 access."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
import json,resource
from datetime import datetime,timezone
import numpy as np
from threadpoolctl import threadpool_limits
from source_analysis import HERE,load,FILES

def interval(a):
    return [float(x) for x in np.quantile(a,[.025,.975])]

def cell(r): return (r['c'],r['j'],int(r['flicker']))

def main():
    rng=np.random.default_rng(10132026)
    result=dict(created_utc=datetime.now(timezone.utc).isoformat(),
       equation='DeltaH = intercept + A(current input cell) + B(next input cell); odd A+B contrasts cancel any additive endpoint term E(cell) if A=U-E and B=E.',
       scope='Source-only; conditional additive diagnostic, not proof of unique updating/storage or randomized causal assignment',
       sources=[],charged_additional_read_decoded_hash_bytes=0)
    for name in FILES:
        by,meta=load(name);result['charged_additional_read_decoded_hash_bytes']+=meta['charge']
        inputs=sorted(set(cell(r) for rr in by.values() for r in rr if r['t']>103))
        if name.startswith('tsay'): inputs=sorted(set(cell(r) for rr in by.values() for r in rr if r['t']>100))
        K=len(inputs);idx={v:i for i,v in enumerate(inputs)};people=[]
        for p,rr in sorted(by.items()):
            rr.sort(key=lambda r:r['t']);X=[];Y=[]
            for a,b in zip(rr,rr[1:]):
                if a['t']+1!=b['t']:continue
                if name.startswith('tsay'):
                    if a['t']<=100 or (a['t']-101)%181>=179:continue
                elif not 104<=a['t']<=903:continue
                if a['bad'] or b['bad'] or not np.isfinite([a['h'],b['h']]).all() or max(abs(a['h']),abs(b['h']))>90:continue
                ca=idx[cell(a)];cb=idx[cell(b)]
                x=np.zeros(2*K-1);x[0]=1
                if ca: x[ca]=1
                if cb: x[K-1+cb]=1
                X.append(x);Y.append(b['h']-a['h'])
            X=np.asarray(X);Y=np.asarray(Y)
            coef,_,rank,_=np.linalg.lstsq(X,Y,rcond=None)
            A=np.r_[0,coef[1:K]];B=np.r_[0,coef[K:]]
            assert len(A)==K and len(B)==K and rank==2*K-1
            rec=dict(person=p,n=len(Y),rank=int(rank),n_columns=2*K-1,
                     current=A.tolist(),next=B.tolist(),current_plus_next=(A+B).tolist(),
                     max_fit_normal_equation_residual=float(np.max(abs(np.einsum('ni,n->i',X,Y-np.einsum('ni,i->n',X,coef))))))
            conditions={'No Jump':(4.,0.,0),'Jump To':(4.,4.,0),'Jump Away':(4.,-4.,0),
                        'Jump Past':(4.,8.,0),'Jump In Place':(4.,0.,1)}
            effects={}
            for lab,pos in conditions.items():
                neg=(-pos[0],-pos[1],pos[2])
                if pos not in idx or neg not in idx:continue
                i,j=idx[pos],idx[neg]
                effects[lab]={key:float(-.5*(v[i]-v[j])) for key,v in
                              [('current',A),('next',B),('current_plus_next',A+B)]}
            rec['effects']=effects;people.append(rec)
        conds=list(people[0]['effects']);summary={}
        for con in conds:
            summary[con]={}
            for channel in ('current','next','current_plus_next'):
                vals=np.array([p['effects'][con][channel] for p in people])
                boot=vals[rng.integers(len(vals),size=(4000,len(vals)))].mean(axis=1)
                summary[con][channel]=dict(estimate=float(vals.mean()),bootstrap95=interval(boot))
        result['sources'].append(dict(source=name,metadata=meta,input_cells=inputs,people=people,summary=summary))
    # Matched clamp/jump response ratios cancel an unknown overall lab amplitude.
    a=result['sources'][0]; f=result['sources'][2]
    transfers={}
    for channel in ('current','current_plus_next'):
        aa=np.array([[p['effects'][c][channel] for c in ('No Jump','Jump To')] for p in a['people']])
        ff=np.array([[p['effects'][c][channel] for c in ('No Jump','Jump To')] for p in f['people']])
        ia=rng.integers(len(aa),size=(6000,len(aa)));iff=rng.integers(len(ff),size=(6000,len(ff)))
        am=aa[ia].mean(axis=1); fm=ff[iff].mean(axis=1)
        aq=am[:,1]/am[:,0];fq=fm[:,1]/fm[:,0]
        qa=float(aa[:,1].mean()/aa[:,0].mean());qf=float(ff[:,1].mean()/ff[:,0].mean())
        residual=fm[:,1]-aq*fm[:,0]
        # Both forecasts receive identical leave-one-person-out stationary amplitude calibration.
        # Only the intervention ratio differs: fixed Tsay versus other Figure3 people.
        predictions=[]
        for i in range(len(ff)):
            train=np.delete(ff,i,axis=0).mean(axis=0);qm=train[1]/train[0]
            predictions.append(dict(person=f['people'][i]['person'],observed_jump_to=float(ff[i,1]),
                 stationary_calibration_other_people=float(train[0]),Tsay_ratio_forecast=float(qa*train[0]),
                 lab_specific_intervention_forecast=float(qm*train[0])))
        lt=np.array([(p['observed_jump_to']-p['Tsay_ratio_forecast'])**2 for p in predictions])
        ll=np.array([(p['observed_jump_to']-p['lab_specific_intervention_forecast'])**2 for p in predictions])
        gain=lt-ll
        gb=gain[rng.integers(len(gain),size=(6000,len(gain)))].mean(axis=1)
        transfers[channel]=dict(Tsay_ratio=qa,Tsay_ratio95=interval(aq),Figure3_ratio=qf,Figure3_ratio95=interval(fq),
             ratio_shift=qf-qa,ratio_shift95=interval(fq-aq),
             stationary_calibrated_transfer_residual_degrees=float(ff[:,1].mean()-qa*ff[:,0].mean()),
             transfer_residual95=interval(residual),leave_person_out_predictions=predictions,
             Tsay_transfer_MSE=float(lt.mean()),lab_intervention_MSE=float(ll.mean()),
             lab_intervention_MSE_gain=float(gain.mean()),fixed_fit_paired_bootstrap_gain95=interval(gb),
             limitations='Consumed-source postvalidation diagnostic. Fixed-fit paired bootstrap is descriptive; overlapping LOO training, source fit uncertainty and laboratory population uncertainty are not all calibrated.')
    result['matched_transfer']=transfers
    result['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (HERE/'ENDPOINT_CONTROL.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(created_utc=result['created_utc'],charge=result['charged_additional_read_decoded_hash_bytes'],
                         source_summary=[dict(source=s['source'],summary=s['summary']) for s in result['sources']],
                         transfer={k:{x:v for x,v in d.items() if x!='leave_person_out_predictions'} for k,d in transfers.items()},
                         peak_rss_bytes=result['peak_rss_bytes']),indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=1):main()
