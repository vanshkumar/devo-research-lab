"""Independent review. Original frozen modules are objects under test only."""
from pathlib import Path
import datetime as dt
import hashlib
import io
import json
import math
import os
import resource
import socket
import sys
import time
import traceback
import warnings
import zipfile

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
C=ROOT/'campaigns/population_learning_transport_2026-10-28'
OLD=ROOT/'campaigns/learning_rule_transport_2026-10-28'
AUTHOR=ROOT/'lab/tasks/learning-forecast-information-audit-2026-11-01'
HISTORY=ROOT/'experiments/matched_history_diagnostic_2026-10-29'
FREEZE=C/'protocols/FREEZE.json'
STOP=dt.datetime.fromisoformat('2026-11-01T13:29:05+00:00')
sys.dont_write_bytecode=True
os.environ['NUMBA_CACHE_DIR']=str(OUT/'numba_cache')
sys.path[:0]=[str(C/'code'),str(OLD/'code')]

import numpy as np
from numba import njit
from scipy.special import expit,logit
import mixed_reader as reader
import data_io
from rnn_learning import load_rnn
from baselines import load_bank,draw_initial,omission_at
from learning_models import subject_arrays
import campaign

PINS={}
READS=[]

def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()
def dump(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2)+'\n')
def deny(*a,**kw):raise PermissionError('No network, RNN optimizer or uncapped history access')
socket.create_connection=deny
socket.socket.connect=deny
reader.urlopen=deny
reader.acquire=deny
reader.coverage=deny
data_io.load_subject=deny
data_io.prepare_subject=deny

def exposure(event):
    with (OUT/'EXPOSURE.jsonl').open('a') as f:f.write(json.dumps(dict(utc=stamp(),**event))+'\n')
reader.log=exposure
data_io.exposure=exposure

def database():
    import duckdb
    return duckdb.connect(config={'threads':1,'memory_limit':'96MB','temp_directory':str(OUT/'duckdb_tmp')})
reader.db=database

def bounds():
    if dt.datetime.now(dt.timezone.utc)>=STOP:raise RuntimeError('Hard review deadline reached')
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss>800_000_000:raise RuntimeError('RSS cap exceeded')

def read(p,npz=False,expected=None):
    p=Path(p);b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
    if expected is not None:assert h==expected,str(p)
    PINS[str(p.relative_to(ROOT))]=h
    if npz:
        with zipfile.ZipFile(io.BytesIO(b)) as z:decoded=sum(q.file_size for q in z.infolist())
        with np.load(io.BytesIO(b),allow_pickle=False) as z:x={k:z[k] for k in z.files}
    else:decoded=len(b);x=json.loads(b)
    READS.append(dict(path=str(p.relative_to(ROOT)),file_bytes=len(b),decoded_bytes=decoded))
    return x

def complete_freeze():
    f=read(FREEZE)
    for r in f['files']:
        p=ROOT/r['path'];b=p.read_bytes()
        assert hashlib.sha256(b).hexdigest()==r['sha256'],r['path']
        READS.append(dict(path=r['path'],file_bytes=len(b),decoded_bytes=0,strict_freeze=True))
    return f

@njit(cache=True)
def sig(x):
    if x>=0:return 1/(1+math.exp(-x))
    e=math.exp(x);return e/(1+e)

@njit(cache=True)
def explicit_reference(s,c,r,day,w0,h0,Wih,Whh,bih,bhh,A,a,B,b,Cc,cc,scale):
    """Scalar nested sums, independent of original dot/einsum recurrence."""
    w=w0.copy();h=h0.copy();H=len(h);q=np.empty(len(s))
    for t in range(len(s)):
        z=math.tanh(5*s[t])/math.tanh(5.)
        lg=w[0]*max(z,0.)+w[1]*min(z,0.)+w[2]
        q[t]=sig(max(-50.,min(50.,lg)))
        if c[t]==0:continue
        inp=np.empty(9);inp[0:3]=w
        inp[3]=z;inp[4]=1.;inp[5]=day[t];inp[6]=float(c[t]<0)
        inp[7]=float(r[t]>0);inp[8]=float(z>0)
        gi=np.empty(3*H);gh=np.empty(3*H)
        for u in range(3*H):
            gi[u]=bih[u];gh[u]=bhh[u]
            for v in range(9):gi[u]+=Wih[u,v]*inp[v]
            for v in range(H):gh[u]+=Whh[u,v]*h[v]
        hn=np.empty(H)
        for u in range(H):
            reset=sig(gi[u]+gh[u]);keep=sig(gi[H+u]+gh[H+u])
            hn[u]=keep*h[u]+(1-keep)*math.tanh(gi[2*H+u]+reset*gh[2*H+u])
        hidden1=np.empty(A.shape[0])
        for u in range(len(hidden1)):
            v0=a[u]
            for v in range(H):v0+=A[u,v]*hn[v]
            hidden1[u]=max(0.,v0)
        hidden2=np.empty(B.shape[0])
        for u in range(len(hidden2)):
            v0=b[u]
            for v in range(len(hidden1)):v0+=B[u,v]*hidden1[v]
            hidden2[u]=max(0.,v0)
        for u in range(3):
            d=cc[u]
            for v in range(len(hidden2)):d+=Cc[u,v]*hidden2[v]
            w[u]+=scale*d
        h=hn
    return q,w,h

def reference(model,s,c,r,d,w,h):
    p=model.params
    return explicit_reference(s,c,r,d,w,h,*[p[k] for k in ('Wih','Whh','bih','bhh','A','a','B','b','C','cc','scale')])

def reconstruct(model,prefix,cal,seed):
    w0=np.asarray(cal['w0']);p,_,end=model.sequence(prefix,w0)
    s,c,r,d=subject_arrays(prefix)
    rp,rw,rh=reference(model,s,c,r,d,w0,np.zeros(model.hidden))
    referr=max(np.max(np.abs(rp-p)),np.max(np.abs(rw-end['w'])),np.max(np.abs(rh-end['h'])))
    assert referr<1e-10
    centralerr=max(np.max(np.abs(end['w']-cal['endpoint'])),np.max(np.abs(end['h']-cal['hidden_endpoint'])))
    assert centralerr<1e-10
    ds=[];jws=[];jhs=[]
    for j in range(3):
        d0=np.zeros(3);d0[j]=.001
        plus,_,pe=model.sequence(prefix,w0+d0)
        minus,_,me=model.sequence(prefix,w0-d0)
        ds.append((logit(np.clip(plus,1e-7,1-1e-7))-logit(np.clip(minus,1e-7,1-1e-7)))/.002)
        jws.append((pe['w']-me['w'])/.002);jhs.append((pe['h']-me['h'])/.002)
    D=np.array(ds).T;Jw=np.array(jws).T;Jh=np.array(jhs).T
    ok=np.flatnonzero(c!=0)
    fisher=np.array([[math.fsum(float(D[t,j]*D[t,k]*p[t]*(1-p[t])) for t in ok)
                      for k in range(3)] for j in range(3)])+.5*np.eye(3)
    cv=np.linalg.inv(fisher);ev,U=np.linalg.eigh((cv+cv.T)/2)
    cv=np.einsum('ik,k,jk->ij',U,np.clip(ev,1e-7,4),U)
    saved=np.asarray(cal['initial_covariance'])
    cerr=float(np.max(np.abs(cv-saved)));assert cerr<1e-8
    wcov=np.einsum('ik,kl,jl->ij',Jw,saved,Jw)
    maxev=float(np.linalg.eigvalsh((wcov+wcov.T)/2).max())
    factor=min(1.,math.sqrt(4/maxev)) if maxev>0 else 1.
    assert abs(factor-cal['endpoint_sd_cap_factor'])<1e-8
    ecerr=float(np.max(np.abs(wcov*factor**2-cal['endpoint_covariance'])));assert ecerr<1e-8
    delta=np.random.default_rng(seed+313).multivariate_normal(np.zeros(3),saved,512)
    delta*=cal['endpoint_sd_cap_factor']
    initial=dict(w=np.asarray(cal['endpoint'])+delta@Jw.T,
                 h=np.asarray(cal['hidden_endpoint'])+delta@Jh.T)
    clipped=float(np.mean((initial['h']<-1)|(initial['h']>1)))
    assert clipped==cal['hidden_clipped_fraction']
    initial['h']=np.clip(initial['h'],-1,1)
    return initial,dict(independent_prefix_reference_max_error=float(referr),central_error=float(centralerr),
                        fisher_covariance_max_error=cerr,endpoint_covariance_max_error=ecerr,
                        cap_factor=factor,hidden_clipped_fraction=clipped,
                        no_rnn_optimizer=True)

def target_reference(s,c):
    y=np.empty((6,2));n=np.empty((6,2),int)
    for b in range(6):
        for k,side in enumerate((-1,1)):
            ix=[t for t in range(500*b,500*(b+1)) if abs(s[t]-side)<=1e-9]
            n[b,k]=len(ix);assert len(ix)>0
            y[b,k]=sum(int(c[t]==-side) for t in ix)/len(ix)
    return y,n

def conditional_review(model,initial,omission,future,seed):
    s,c,r,d=subject_arrays(future)
    state={k:v.copy() for k,v in initial.items()}
    rng=np.random.default_rng(seed+101)
    probability=np.empty((512,3000));choices=np.empty((512,3000),np.int8)
    omitchecks=0
    for t in range(3000):
        if t%500==0:bounds()
        probability[:,t]=model.probs(state,np.repeat(s[t],512))
        choices[:,t]=np.where(rng.random(512)<probability[:,t],-1,1)
        choices[rng.random(512)<omission[:,t//500],t]=0
        old={k:v.copy() for k,v in state.items()} if c[t]==0 else None
        model.update(state,s[t],c[t],r[t],session_start=bool(d[t]))
        if c[t]==0:
            assert all(np.array_equal(state[k],old[k]) for k in state);omitchecks+=1
    assert np.isfinite(probability).all() and (probability>=0).all() and (probability<=1).all()
    referr=finalerr=0.
    for j in (0,17,255,511):
        q,w,h=reference(model,s,c,r,d,initial['w'][j],initial['h'][j])
        referr=max(referr,float(np.max(np.abs(q-probability[j]))))
        finalerr=max(finalerr,float(np.max(np.abs(w-state['w'][j]))),float(np.max(np.abs(h-state['h'][j]))))
    assert referr<1e-10 and finalerr<1e-10
    sampled=np.empty((512,6,2));analytic=np.empty_like(sampled)
    for b in range(6):
        for k,side in enumerate((-1,1)):
            ix=np.array([t for t in range(500*b,500*(b+1)) if abs(s[t]-side)<=1e-9])
            for j in range(512):
                sampled[j,b,k]=np.count_nonzero(choices[j,ix]==-side)/len(ix)
                ps=probability[j,ix] if side==1 else 1-probability[j,ix]
                analytic[j,b,k]=(1-omission[j,b])*math.fsum(float(v) for v in ps)/len(ix)
    return dict(sampled=sampled,analytic=analytic,probability=probability,choices=choices,
                final_w=state['w'],final_h=state['h']),dict(full_scalar_particle_paths=4,
                    scalar_future_probability_values=12000,scalar_future_probability_max_error=referr,
                    scalar_final_state_max_error=finalerr,actual_omission_state_skips=omitchecks,
                    update_inputs='actual choice and positive actual feedback; sampled choices used only in scores')

def metrics(target,pred,labs):
    residual=target.mean(2)-pred.mean(2)
    return dict(population_mae_pp=float(100*np.abs(residual.mean(0)).mean()),
                individual_mae_pp=float(100*np.abs(residual).mean()),
                side_mae_pp=float(100*np.abs(target-pred).mean()),
                lab_mae_pp={l:float(100*np.abs(residual[labs==l].mean(0)).mean()) for l in sorted(set(labs))})

def uncertainty(target,auto,sampled,analytic,labs,saved):
    truth=target.mean(2);a=auto.mean((1,3));s=sampled.mean((1,3));q=analytic.mean((1,3))
    ix=np.random.default_rng(20261029).integers(0,24,(20000,24))
    comparisons={}
    for name,p in [('sampled',s),('analytic',q)]:
        ar=truth-a;cr=truth-p
        pop=100*(np.abs(ar[ix].mean(1)).mean(1)-np.abs(cr[ix].mean(1)).mean(1))
        indiv=100*(np.abs(ar).mean(1)-np.abs(cr).mean(1))[ix].mean(1)
        comparisons[name]=dict(population95_pp=np.quantile(pop,[.025,.975]).tolist(),
                                individual95_pp=np.quantile(indiv,[.025,.975]).tolist(),
                                lab_deletion_gain_pp={l:float(100*(np.abs(ar[labs!=l].mean(0)).mean()-np.abs(cr[labs!=l].mean(0)).mean())) for l in sorted(set(labs))})
        if name=='sampled':
            e=float(np.max(np.abs(pop-saved['paired_animal_population_gain_sampled'])))
            assert e<1e-10;comparisons[name]['saved_draw_max_error_pp']=e
    rng=np.random.default_rng(20261101);curves=[np.zeros((2000,6)) for _ in range(3)]
    for i in range(24):
        for start in range(0,2000,100):
            j=rng.integers(0,512,(100,512))
            for data,out in zip((auto,sampled,analytic),curves):
                out[start:start+100]+=data[i].mean(2)[j].mean(1)/24
    means=truth.mean(0);errors=[100*np.abs(v-means).mean(1) for v in curves]
    names=['particle_bootstrap_autonomous_curve','particle_bootstrap_conditional_sampled_curve','particle_bootstrap_conditional_analytic_curve']
    savederror=max(float(np.max(np.abs(v-saved[k]))) for v,k in zip(curves,names));assert savederror<1e-12
    return dict(paired_animal=comparisons,particle_sampled_gap95_pp=np.quantile(errors[0]-errors[1],[.025,.975]).tolist(),
                particle_analytic_gap95_pp=np.quantile(errors[0]-errors[2],[.025,.975]).tolist(),
                particle_saved_curve_max_error=savederror,
                numerical_conditional_curve_se_pp=(100*curves[1].std(0,ddof=1)).tolist(),
                biological_coverage_established=False)

def main():
    tic=time.monotonic();bounds()
    plan=read(OUT/'RESOURCE_PLAN.json');assert plan['conservative_total_charge_bytes']<350_000_000
    dump('FROZEN_PLAN.json',dict(utc=stamp(),design_sha256=hashlib.sha256((OUT/'DESIGN.md').read_bytes()).hexdigest(),
         code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         resource_plan_sha256=PINS[str((OUT/'RESOURCE_PLAN.json').relative_to(ROOT))],
         contrary='fixed predeclared particle count weighting; no contrary values calculated yet'))
    freeze=complete_freeze();subjects=freeze['source_primary_subjects']
    assert subjects==plan['subjects'] and not set(subjects)&{'NYU-21','SWC_007'}
    histpins=read(HISTORY/'SOURCE_PINS.json')['artifacts']
    def pin(p):return histpins[str(p.relative_to(ROOT))]
    x=read(AUTHOR/'MATCHED_PREDICTIONS.npz',True)
    assert subjects==x['subjects'].tolist();labs=x['labs']
    modelpath=OLD/'artifacts/rnn/rnnglm32_nested_best.npz'
    bankpath=OLD/'artifacts/baselines/nested_growth_bank.npz'
    mp=read(modelpath,True);bp=read(bankpath,True)
    assert PINS[str(modelpath.relative_to(ROOT))]=='c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940'
    assert PINS[str(bankpath.relative_to(ROOT))]=='036f3cfedd56e915b051fb29a80a2622cf5a747366ea31aa46b9249a922eea01'
    # Avoid another model/bank read; instantiate the frozen class with pinned arrays.
    from rnn_learning import RNNLearningModel
    model=RNNLearningModel({k:np.asarray(v,float) for k,v in mp.items() if k not in ('kind','metadata')})
    model.initial_state=deny;bank=bp
    oldread=reader._read
    def restricted(subject,stop):
        if subject not in subjects or int(stop)!=4000:raise PermissionError('Only same24first4000')
        return oldread(subject,4000)
    reader._read=restricted
    audits=[];targets=[];observed_counts=[];all_auto=[];all_counts=[];all_sampled=[];all_analytic=[]
    selected_records=[]
    manifest=read(AUTHOR/'PREDICTION_MANIFEST.json')
    pm={v['subject']:v for v in manifest['complete']}
    assert manifest['completed']==24 and manifest['new_cohort_scores_computed'] is False
    assert manifest['endpoint_file_sha256']==PINS[str((AUTHOR/'MATCHED_PREDICTIONS.npz').relative_to(ROOT))]
    for i,subject in enumerate(subjects):
        bounds();t0=time.monotonic();folder=C/'artifacts/forecasts/source'
        pmeta=folder/(subject+'__rnn.json');meta=read(pmeta,expected=pin(pmeta))
        pp=folder/(subject+'__prefix.npz');prefix=read(pp,True,meta['prefix_sha256'])
        starts=prefix.pop('future_session_start')
        ap=folder/(subject+'__rnn.npz');aut=read(ap,True,pin(ap))
        op=folder/(subject+'__observed.npz');observed=read(op,True,pin(op))
        historical=read(HISTORY/(subject+'__conditional.npz'),True)
        assert meta['particles']==512 and meta['horizon']==3000
        raw=reader.load_scored(subject,4000,FREEZE,C/'protocols/SOURCE_FORECASTS.json',purpose='Independent postvalidation review; same consumed first4000 only')
        assert len(raw['choice'])==4000
        fieldchecks=0
        for k,v in prefix.items():
            if isinstance(v,np.ndarray) and v.ndim and len(v)==1000:
                assert np.array_equal(v,raw[k][:1000],equal_nan=True),k;fieldchecks+=1
        future={k:v[1000:4000] for k,v in raw.items() if isinstance(v,np.ndarray) and v.ndim and len(v)==4000}
        s,c,r,d=subject_arrays(future)
        assert np.array_equal(starts,d.astype(bool))
        y,n=target_reference(s,c)
        assert np.array_equal(y,observed['observed'][:,:2]) and np.array_equal(n,observed['counts'][:,:2])
        assert np.array_equal(y,x['observed_sides'][i])
        seed=int(hashlib.sha256(subject.encode()).hexdigest()[:8],16)%(2**31-1)
        initial,initcheck=reconstruct(model,prefix,meta['calibration'],seed)
        common=draw_initial(prefix,bank,512,seed+211,exclude=subject,competence='growth')
        omit=np.column_stack([omission_at(common,500*b) for b in range(6)])
        omiterror=float(np.max(np.abs(omit.mean(0)-historical['p_omit'].reshape(6,500)[:,0])))
        assert omiterror<1e-12
        replay=campaign.simulate(model,prefix,starts,common,initial,None,'rnn','standard',seed)
        assert np.array_equal(replay['samples'],aut['samples'])
        assert np.array_equal(replay['counts'],aut['counts'])
        werr=float(np.max(np.abs(replay['weights']-aut['weights'])))
        herr=float(np.max(np.abs(replay['hidden_final']-aut['hidden_final'])))
        assert werr<1e-8 and herr<1e-8
        assert np.array_equal(aut['samples'][:,:,:2],x['saved_autonomous_particles'][i])
        out,checks=conditional_review(model,initial,omit,future,seed)
        sampleerr=float(np.max(np.abs(out['sampled']-x['conditional_sampled_particles'][i])))
        analyticerr=float(np.max(np.abs(out['analytic']-x['conditional_analytic_particles'][i])))
        assert sampleerr==0 and analyticerr<1e-12
        assert hashlib.sha256(out['sampled'].tobytes()).hexdigest()==pm[subject]['sampled_side_array_sha256']
        if subject in plan['saved_full_trial_file_checks']:
            saved=read(AUTHOR/'predictions'/(subject+'.npz'),True)
            errors={}
            for own,key in [('probability','prob_right'),('choices','scoring_choice'),('final_w','final_w'),('final_h','final_h')]:
                errors[key]=float(np.max(np.abs(out[own]-saved[key])))
                assert errors[key]<1e-12
            for key,own in [('initial_w',initial['w']),('initial_h',initial['h']),('omission_by_particle_bin',omit),
                            ('actual_signed_contrast',s),('actual_choice',c),('actual_feedback_positive',r),('actual_session_start',d)]:
                errors[key]=float(np.max(np.abs(saved[key]-own)));assert errors[key]<1e-12
            selected_records.append(dict(subject=subject,full_file_sha256=PINS[str((AUTHOR/'predictions'/(subject+'.npz')).relative_to(ROOT))],
                                         complete_arrays_max_errors=errors,probability_values=int(out['probability'].size),
                                         scoring_choices=int(out['choices'].size)))
            del saved
        audits.append(dict(subject=subject,lab=str(labs[i]),prefix_field_checks=fieldchecks,
                           raw_rows=4000,exact100_opportunities=int(n.sum()),session_start_checks=int(d.sum()),
                           initial=initcheck,omission_mean_error=omiterror,
                           original_autonomous_samples_and_counts_exact=True,original_autonomous_weight_error=werr,
                           original_autonomous_hidden_error=herr,conditional_sampled_max_error=sampleerr,
                           conditional_analytic_max_error=analyticerr,conditional=checks,seconds=time.monotonic()-t0))
        targets.append(y);observed_counts.append(n);all_auto.append(aut['samples'][:,:,:2]);all_counts.append(aut['counts'][:,:,:2])
        all_sampled.append(out['sampled']);all_analytic.append(out['analytic'])
        dump('AUDIT.json',dict(utc=stamp(),completed=len(audits),records=audits,selected_saved_trial_files=selected_records))
        dump('STATE.json',dict(utc=stamp(),status='running',completed=len(audits),process=os.getpid()))
        print(json.dumps(dict(subject=subject,completed=len(audits),auto_exact=True,conditional_sample_error=sampleerr,
                              scalar_error=checks['scalar_future_probability_max_error'],seconds=audits[-1]['seconds'],rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)
        del raw,future,prefix,aut,replay,historical,out
    target=np.array(targets);auto=np.array(all_auto);counts=np.array(all_counts)
    sampled=np.array(all_sampled);analytic=np.array(all_analytic);nobs=np.array(observed_counts)
    np.savez_compressed(OUT/'RECONSTRUCTED_ENDPOINTS.npz',subjects=np.array(subjects),labs=labs,observed=target,
                         observed_counts=nobs,autonomous=auto,autonomous_counts=counts,conditional_sampled=sampled,conditional_analytic=analytic)
    saved_u=read(AUTHOR/'UNCERTAINTY_DRAWS.npz',True)
    unc=uncertainty(target,auto,sampled,analytic,labs,saved_u)
    dump('UNCERTAINTY_AUDIT.json',dict(utc=stamp(),**unc))
    # ONE predeclared contrary, first numerical evaluation here.
    numer=auto*counts
    integer_error=float(np.max(np.abs(numer-np.rint(numer))));assert integer_error<1e-10
    unweighted=auto.mean(1);pooled=numer.sum(1)/counts.sum(1)
    covariance=((auto-unweighted[:,None])*(counts-counts.mean(1)[:,None])).mean(1)
    identity_error=float(np.max(np.abs((pooled-unweighted)-covariance/counts.mean(1))))
    assert identity_error<1e-12
    condpooled=(sampled*nobs[:,None]).sum(1)/(512*nobs)
    conditional_invariance=float(np.max(np.abs(condpooled-sampled.mean(1))));assert conditional_invariance<1e-12
    metrics0=metrics(target,unweighted,labs);metrics1=metrics(target,pooled,labs);cm=metrics(target,sampled.mean(1),labs)
    contrary=dict(utc=stamp(),test='mean of particle ratios versus ratio of summed correct counts/opportunities',
                 changed_estimand_not_replacement_forecast=True,original_autonomous=metrics0,count_pooled_autonomous=metrics1,
                 unchanged_conditional=cm,original_gap_pp=metrics0['population_mae_pp']-cm['population_mae_pp'],
                 count_pooled_gap_pp=metrics1['population_mae_pp']-cm['population_mae_pp'],
                 max_animal_bin_side_prediction_change_pp=float(100*np.max(np.abs(pooled-unweighted))),
                 cohort_bin_side_prediction_change_pp=(100*(pooled-unweighted).mean(0)).tolist(),
                 count_min=int(counts.min()),count_max=int(counts.max()),integer_numerator_max_error=integer_error,
                 covariance_identity_max_error=identity_error,conditional_invariance_max_error=conditional_invariance)
    dump('CONTRARY.json',contrary)
    result=dict(utc=stamp(),status='completed_independent_review',animals=24,raw_rows=96000,
                scored_exact100_opportunities=int(nobs.sum()),metrics=dict(autonomous=metrics0,conditional_sampled=cm,
                conditional_analytic=metrics(target,analytic.mean(1),labs)),
                primary_gap_pp=contrary['original_gap_pp'],contrary_count_weighted_gap_pp=contrary['count_pooled_gap_pp'],
                all24_autonomous_samples_and_counts_exact=True,all24_conditional_endpoint_samples_exact=True,
                all24_analytic_endpoint_max_error=float(np.max(np.abs(analytic-x['conditional_analytic_particles']))),
                scalar_probability_values=24*4*3000,selected_saved_trial_files=selected_records,
                uncertainty=unc,scope='fixed equal-weight prefix mixture, actual past observations assimilated; not future-likelihood-weighted posterior')
    complete_freeze()
    dump('RESULT.json',result);dump('SOURCE_PINS.json',dict(utc=stamp(),pins=PINS,reads=READS))
    resources=dict(utc=stamp(),status='completed',conservative_cumulative_read_hash_decode_charge_bytes=plan['conservative_total_charge_bytes'],
                   cap_bytes=350_000_000,recorded_explicit_artifact_and_freeze_charge_bytes=sum(r['file_bytes']+r['decoded_bytes'] for r in READS),
                   peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,cap_rss_bytes=800_000_000,
                   elapsed_seconds=time.monotonic()-tic,processes=1,numerical_threads=1,public_operations=0,ingress_bytes=0,
                   physical_io_internal_parquet_decode_unknown=True,author_resources_separate=True,
                   whole_author_trial_file_hashes_checked=plan['saved_full_trial_file_checks'],
                   remaining22_author_whole_trial_file_hashes='UNRUN; all24endpoint bundles independently reconstructed')
    assert resources['peak_rss_bytes']<800_000_000
    dump('RESOURCES.json',resources)
    dump('STATE.json',dict(utc=stamp(),status='completed',jobs=0,scientific_process='ending normally',hardstop=STOP.isoformat()))
    print(json.dumps(dict(result={k:result[k] for k in ('utc','status','primary_gap_pp','contrary_count_weighted_gap_pp','metrics')},resources=resources),indent=2),flush=True)

if __name__=='__main__':
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        try:main()
        except BaseException as e:
            dump('STOP.json',dict(utc=stamp(),exception=repr(e),traceback=traceback.format_exc(),
                                  peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
            raise
        finally:dump('WARNINGS.json',[dict(category=w.category.__name__,message=str(w.message),filename=w.filename,lineno=w.lineno) for w in captured])
