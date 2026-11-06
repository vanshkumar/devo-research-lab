"""Independent feature, support, probability and fixed-optimum reconstruction.

No imports of author analysis/audit. Uses signal filtering for prior histories,
and explicit contractions for numerical reliability in the existing workspace.
"""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
from pathlib import Path
import csv, json, hashlib, resource, datetime, collections
import numpy as np
from scipy.signal import lfilter
from scipy.special import expit

HERE=Path(__file__).resolve().parent
AUTHOR=HERE.parents[1]/'tasks'/HERE.name
ROOT=HERE.parents[2]

def prior_filter(events, starts):
    out=np.empty((len(events),3))
    cuts=np.r_[np.flatnonzero(starts),len(events)]
    assert cuts[0]==0
    for j,tau in enumerate((2,8,32)):
        decay=np.exp(-1/tau)
        for lo,hi in zip(cuts[:-1],cuts[1:]):
            running=lfilter([1-decay],[1,-decay],events[lo:hi])
            out[lo:hi,j]=np.r_[0.,running[:-1]]
    return out

def weighted_check(X,beta,y,w,offset=None):
    eta=np.einsum('ij,j->i',X,beta,optimize=False)
    if offset is not None: eta+=offset
    obj=float(np.sum(w*(np.logaddexp(0,eta)-y*eta))+.00005*np.sum(beta**2))
    grad=np.einsum('ij,i->j',X,w*(expit(eta)-y),optimize=False)+.0001*beta
    return obj,grad

def main():
    read_paths=[];decoded=0
    def js(p):
        read_paths.append(p); return json.loads(p.read_text())
    manifest=js(AUTHOR/'ALLOWED_MANIFEST.json')
    allowed={(r['species'],r['subject']):r for r in manifest['subjects']}
    fits=js(AUTHOR/'corrected/FITS.json')
    features=js(AUTHOR/'corrected/FEATURES.json')
    source_support=js(AUTHOR/'SUPPORT.json')
    derived=AUTHOR/'consumed_inputs.npz';read_paths.append(derived)
    with np.load(derived,allow_pickle=False) as z:
        number=len([k for k in z.files if k.endswith('__subject')])
        units=[]
        for i in range(number):
            d={k.split('__',1)[1]:z[k] for k in z.files if k.startswith(str(i)+'__')}
            decoded+=sum(a.nbytes for a in d.values());units.append(d)
    assert len(units)==len(allowed)==202
    actual={(str(d['species']),str(d['subject'])) for d in units}
    assert actual==set(allowed)
    for d in units:
        r=allowed[(str(d['species']),str(d['subject']))]
        assert len(d['trial'])==r['allowed_rows'][1]-r['allowed_rows'][0]
        assert r['allowed_rows'][0]==0
        assert np.array_equal(d['trial'],np.arange(len(d['trial'])))
        assert len(d['trial']) <= (6000 if str(d['species'])=='mouse' else 600)
    digest=lambda s:hashlib.sha256(('20261031:'+s).encode()).hexdigest()
    schedules=sorted({str(d['schedule']) for d in units if str(d['species'])=='human'},key=digest)
    fold_h={s:i%5 for i,s in enumerate(schedules)};fold_m={}
    for lab in sorted({str(d['lab']) for d in units if str(d['species'])=='mouse'}):
        ids=sorted([str(d['subject']) for d in units if str(d['species'])=='mouse' and str(d['lab'])==lab],key=digest)
        fold_m.update({s:i%5 for i,s in enumerate(ids)})
    blocks=[];history=[];physical=[];zero=[];omitted=[];meta=[];checks=[]
    for ui,d in enumerate(units):
        sp=str(d['species']);sid=str(d['subject']);c=d['choice'].astype(float);fb=d['feedback'].astype(float);x=d['contrast'].astype(float);starts=d['session_start'].astype(bool)
        n=len(c);t=np.arange(n);sign=np.sign(x)
        event=np.where(c!=0,c*fb,0.)
        E=prior_filter(event,starts);P=prior_filter(sign,starts)
        Z=prior_filter(np.where(x==0,event,0.),starts)
        O=prior_filter(np.where(c==0,sign,0.),starts)
        C=prior_filter(c,starts)
        saved_h=np.stack([d['h2'],d['h8'],d['h32']],axis=1)
        identity=float(np.max(abs(E-P-Z+O)));historyerr=float(np.max(abs(E-saved_h)))
        assert identity<3e-15 and historyerr<3e-15
        mismatch=int(np.sum((c!=0)&(x!=0)&(c*fb!=sign)))
        assert mismatch==0
        expected_prev=np.r_[0,c[:-1]];expected_prev[starts]=0
        assert np.array_equal(d['prev_choice'],expected_prev)
        expected_position=t-np.maximum.accumulate(np.where(starts,t,0))
        assert np.array_equal(expected_position,d['session_trial'])
        assert np.all(starts[1:]==(d['session'][1:]!=d['session'][:-1]))
        cut=min(250,n-1);changed=event.copy();changed[cut:]=.123-changed[cut:]
        futureerr=float(np.max(abs(prior_filter(changed,starts)[:cut+1]-E[:cut+1])))
        assert futureerr==0
        cal=(t<200)&(c!=0);sens=cal&(x!=0)
        early=[float(np.mean(c[sens]*sign[sens])) if sens.any() else 0.,float(np.mean(c[cal])) if cal.any() else 0.,float(np.mean(c[t<200]==0))]
        ii=np.flatnonzero((t>=200)&(t<600)&(d['session_trial']>=32)&np.isin(abs(x),[0,.25,.5,1.]))
        exposure=(ii-399.5)/200.
        b=np.empty((len(ii),20));b[:,0]=1
        for j,value in enumerate((.0625,.1,.125,.25,.5,1.),1):b[:,j]=sign[ii]*np.isclose(abs(x[ii]),value,atol=1e-10,rtol=0)
        b[:,7]=expected_prev[ii];b[:,8:11]=C[ii]
        b[:,11]=exposure;b[:,12]=sign[ii]*exposure
        b[:,13:16]=early;b[:,16]=sign[ii]*early[0];b[:,17]=sign[ii]*early[1]
        b[:,18]=d['session'][ii]/5.;b[:,19]=np.minimum(d['session_trial'][ii],600)/600.
        group=int(d['condition']) if sp=='human' else 2
        nb=np.zeros((len(ii),60));nb[:,group*20:(group+1)*20]=b
        st=np.zeros((len(ii),9));st[:,group*3:(group+1)*3]=P[ii]
        blocks.append(nb);history.append(E[ii]);physical.append(st);zero.append(Z[ii]);omitted.append(O[ii])
        for j in ii:
            cell='|'.join(str(v) for v in (float(x[j]),int(E[j,0]>=0),int(np.searchsorted([-.5,0,.5],E[j,1],side='right')),int(np.searchsorted([-.25,0,.25],E[j,2],side='right'))))
            meta.append(dict(unit=ui,subject=sid,species=sp,schedule=str(d['schedule']),lab=str(d['lab']),condition=int(d['condition']),trial=int(j),session=int(d['session'][j]),session_trial=int(d['session_trial'][j]),contrast=float(x[j]),choice=float(c[j]),feedback=float(fb[j]),responded=bool(c[j]!=0),fold=fold_h[str(d['schedule'])] if sp=='human' else fold_m[sid],cell=cell,repNum=float(d['repNum'][j])))
        checks.append(dict(unit=ui,subject=sid,species=sp,total_rows=n,selected_rows=len(ii),history_error=historyerr,identity_error=identity,current_future_invariance_error=futureerr,sensory_mismatches=mismatch,early_calibration=early,within_session_prior_changes=int(np.sum((d['probabilityLeft'][1:]!=d['probabilityLeft'][:-1])&(~starts[1:])))))
    del units
    N=np.concatenate(blocks);H=np.concatenate(history);S=np.concatenate(physical);Z=np.concatenate(zero);O=np.concatenate(omitted)
    del blocks,history,physical,zero,omitted
    cells=collections.defaultdict(list)
    for i,r in enumerate(meta):cells[r['cell']].append(i)
    support=np.zeros(len(meta),bool);cell_records=[]
    for cell,ii in sorted(cells.items()):
        h=[meta[i] for i in ii if meta[i]['species']=='human'];m=[meta[i] for i in ii if meta[i]['species']=='mouse']
        ok=len(h)>=20 and len(m)>=20 and len({r['unit'] for r in h})>=5 and len({r['unit'] for r in m})>=5 and len({r['schedule'] for r in h})>=2
        if ok:support[ii]=True
        cell_records.append(dict(cell=cell,human_rows=len(h),mouse_rows=len(m),human_units=len({r['unit'] for r in h}),mouse_units=len({r['unit'] for r in m}),human_schedules=len({r['schedule'] for r in h}),admitted=ok))
    rowpath=AUTHOR/'corrected/scoring_rows.csv';read_paths.append(rowpath)
    rowerr=[]
    with rowpath.open() as f:
        for i,stored in enumerate(csv.DictReader(f)):
            r=meta[i]
            for k,v in r.items():
                a=stored[k]
                if isinstance(v,bool):equal=a==str(v)
                elif isinstance(v,int):equal=int(a)==v
                elif isinstance(v,float):
                    parsed=float(a) if a!='' else np.nan
                    equal=(parsed==v) or (np.isnan(parsed) and np.isnan(v))
                else:equal=a==v
                if not equal:rowerr.append((i,k,str(v),a))
            if (stored['common_support']=='True')!=support[i]:rowerr.append((i,'support'))
    assert i+1==len(meta) and not rowerr,rowerr[:3]
    valid=np.array([r['responded'] for r in meta]);mouse=np.array([r['species']=='mouse' for r in meta]);unit=np.array([r['unit'] for r in meta]);folds=np.array([r['fold'] for r in meta]);y=np.array([r['choice']==1 for r in meta],float)
    predpath=AUTHOR/'corrected/predictions.npz';read_paths.append(predpath)
    with np.load(predpath,allow_pickle=False) as z:
        savedp={k:z[k] for k in z.files};decoded+=sum(a.nbytes for a in savedp.values())
    maxprob=0.;objchecks=[];predictions={};splitchecks=[]
    for augmented in (False,True):
        baseline='S' if augmented else 'B';base=np.column_stack((N,S)) if augmented else N
        for model in ('B','H','T','human_fixed','mouse_fixed'):
            predictions[baseline+'_'+model]=np.full(len(meta),np.nan)
        for fold in range(5):
            train=valid&(folds!=fold);test=valid&(folds==fold)
            assert not (set(unit[train]) & set(unit[test]))
            hs_train={meta[i]['schedule'] for i in np.flatnonzero(train&~mouse)};hs_test={meta[i]['schedule'] for i in np.flatnonzero(test&~mouse)}
            assert not hs_train & hs_test
            w=np.zeros(len(meta))
            for mm in (~mouse,mouse):
                ids=np.unique(unit[train&mm])
                for u in ids:w[train&(unit==u)]=1/(2*len(ids)*np.sum(train&(unit==u)))
            assert abs(w.sum()-1)<1e-14
            splitchecks.append(dict(baseline=baseline,fold=fold,train_rows=int(train.sum()),test_rows=int(test.sum()),human_schedules_train=sorted(hs_train),human_schedules_test=sorted(hs_test)))
            for model in ('B','H','T','human_fixed','mouse_fixed'):
                fit=next(r for r in fits if r['augmented']==augmented and r['fold']==fold and r['model']==model)
                if model=='B':X=base;beta=np.array(fit['coefficients']);offset=np.zeros(len(meta))
                elif model=='H':X=np.column_stack((base,H));beta=np.array(fit['coefficients']);offset=np.zeros(len(meta))
                elif model=='T':X=np.column_stack((base,H*(~mouse[:,None]),H*mouse[:,None]));beta=np.array(fit['coefficients']);offset=np.zeros(len(meta))
                else:X=base;beta=np.array(fit['nuisance_coefficients']);offset=np.einsum('ij,j->i',H,np.array(fit['source_history']),optimize=False)
                eta=np.einsum('ij,j->i',X[test],beta,optimize=False)+offset[test]
                p=expit(eta);predictions[baseline+'_'+model][test]=p
                err=float(np.max(abs(p-savedp[baseline+'_'+model][test])));maxprob=max(maxprob,err)
                obj,g=weighted_check(X[train],beta,y[train],w[train],offset[train])
                objchecks.append(dict(baseline=baseline,fold=fold,model=model,objective=obj,objective_error=abs(obj-fit['objective']),gradient_max=float(np.max(abs(g))),gradient_max_error=abs(float(np.max(abs(g)))-fit['gradient_max']),prediction_error=err))
    witness=[]
    for sp,mm in [('human',~mouse),('mouse',mouse)]:
        m=valid&mm;res=Z[m]-O[m];delta=res.sum(axis=1)
        witness.append(dict(species=sp,rows=int(m.sum()),history_rms=np.sqrt(np.mean(H[m]**2,axis=0)).tolist(),residual_rms=np.sqrt(np.mean(res**2,axis=0)).tolist(),identity_max_error=float(np.max(abs(H[m]-S[m].reshape(-1,3,3).sum(axis=1)-res))),logit_shift_rms=float(np.sqrt(np.mean(delta**2))),mean_probability_shift_bound=float(np.mean(np.tanh(abs(delta)/4))),max_probability_shift_bound=float(np.max(np.tanh(abs(delta)/4))),residual_below_1e12_rows=int(np.sum(np.max(abs(res),axis=1)<1e-12))))
    out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),number_of_units=202,total_cache_rows={sp:sum(r['total_rows'] for r in checks if r['species']==sp) for sp in ('human','mouse')},scoring_rows=len(meta),row_map_mismatches=rowerr,admitted_support_cells=sum(r['admitted'] for r in cell_records),candidate_support_cells=len(cell_records),primary={sp:dict(rows=int(np.sum(support&valid&(mouse if sp=='mouse' else ~mouse))),units=int(len(np.unique(unit[support&valid&(mouse if sp=='mouse' else ~mouse)])))) for sp in ('human','mouse')},maximum_probability_error=maxprob,maximum_objective_error=max(r['objective_error'] for r in objchecks),maximum_gradient_error=max(r['gradient_max_error'] for r in objchecks),maximum_reconstructed_gradient=max(r['gradient_max'] for r in objchecks),per_fit=objchecks,split_checks=splitchecks,per_unit_checks=checks,support_cells=cell_records,coefficient_shift_witness=witness,center_and_scale='No empirical feature centering or standardization. Exposure uses fixed (trial-399.5)/200; session /5 and position /600; first-200 unit calibration. No center is estimated using a held fold.',source_fit_limitation='Reconstructs all 50 stored main/nuisance objective values and gradients, not optimizer refits. The 20 source-only fits save theta and diagnostics but omit source nuisance coefficients; their objective cannot be independently reconstructed from those records.',resource=dict(read_file_bytes=sum(p.stat().st_size for p in read_paths),decoded_array_bytes=decoded,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    (HERE/'RECONSTRUCTION.json').write_text(json.dumps(out,indent=2)+'\n')
    np.savez_compressed(HERE/'independent_predictions.npz',**predictions,y=y)
    print(json.dumps({k:out[k] for k in ('number_of_units','total_cache_rows','scoring_rows','admitted_support_cells','candidate_support_cells','primary','maximum_probability_error','maximum_objective_error','maximum_gradient_error','maximum_reconstructed_gradient','coefficient_shift_witness','resource')},indent=2))

if __name__=='__main__':main()
