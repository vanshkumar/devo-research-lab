"""Frozen prospective execution: decode, save forecasts, then score separately."""
import sys,json,hashlib,resource,itertools
from pathlib import Path
import analysis as A
import numpy as np
R=A.R;OUT=R
sys.path.insert(0,str(R/'deps'))
from numcodecs import Blosc,VLenUTF8
COLS=['stim_name','is_response','reward_time','block_index','is_instruction','is_opto','is_repeat','stim_start_time','response_window_start_time','response_window_stop_time','response_time','is_noncontingent_reward','is_contingent_reward','is_reward_scheduled']
def save(name,x):(OUT/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def check_freeze():
    f=json.loads((R/'SCIENTIFIC_FREEZE.json').read_bytes())
    assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in f['paths'].items())
    return f
def plan():
    check_freeze();old=R.parent/'dynamic-routing-rule-transfer-2026-10-31';todo=[]
    for x in json.loads((old/'zarr.json').read_bytes()):
        root=x['nwb_path'].replace('s3://aind-open-data/','https://aind-open-data.s3.us-west-2.amazonaws.com/');sid=root.split('/')[-1].split('_')[0]
        if sid in A.EVAL:todo.extend([(root+'/intervals/trials/'+c+'/0','raw/'+sid+'/'+c+'.bin',100000) for c in COLS])
    save('evaluation_requests.json',todo);print('EVALUATION_REQUESTS',len(todo))
def decode(sid):
    m=json.loads((R/'metadata'/f'{sid}.json').read_bytes())['metadata'];d={}
    for c in COLS:
        spec=m['intervals/trials/'+c+'/.zarray'];b=(R/'raw'/sid/(c+'.bin')).read_bytes();raw=Blosc().decode(b)
        x=np.asarray(VLenUTF8().decode(raw),dtype=object) if spec['dtype']=='|O' else np.frombuffer(raw,dtype=spec['dtype'])
        assert list(x.shape)==spec['shape'];d[c]=x
    return d
def checks(d):
    t=d['stim_start_time'];a=d['response_window_start_time'];b=d['response_window_stop_time'];r=d['response_time'];w=d['reward_time'];z=d['is_response'];fr=np.isfinite(w)
    return dict(equal_shapes=len(set(len(x) for x in d.values()))==1,finite_strict_stimulus_order=bool(np.all(np.isfinite(t)) and np.all(np.diff(t)>0)),stim_response_window_order=bool(np.all((t<a)&(a<b))),response_window_before_next_stimulus=bool(np.all(b[:-1]<t[1:])),response_flag_equals_finite_response=bool(np.array_equal(z,np.isfinite(r))),finite_responses_in_window=bool(np.all((r[z]>=a[z])&(r[z]<b[z]))),finite_rewards_equal_delivered_flags=bool(np.array_equal(fr,d['is_contingent_reward']|d['is_noncontingent_reward'])),delivered_flags_disjoint=bool(not np.any(d['is_contingent_reward']&d['is_noncontingent_reward'])),contingent_reward_after_response=bool(np.all(z[d['is_contingent_reward']]) and np.all(w[d['is_contingent_reward']]>=r[d['is_contingent_reward']])),rewards_after_stimulus=bool(np.all(w[fr]>=t[fr])),past_rewards_before_next_stimulus=bool(np.all(np.isnan(w[:-1])|(w[:-1]<t[1:]))),instruction_equals_scheduled=bool(np.array_equal(d['is_instruction'],d['is_reward_scheduled'])))
def forecast():
    freeze=check_freeze();models=json.loads((R/'DEVELOPMENT_MODELS.json').read_bytes());report={};pin={};all_ok=True
    for sid in A.EVAL:
        d=decode(sid);ch=checks(d);all_ok=all_ok and all(ch.values());np.savez(OUT/(sid+'_evaluation_arrays.npz'),**d)
        X,n,c=A.features(d);Xa,_,_=A.features(d,ablate=True)
        pp={f:A.predict(X[:,:c[f]],models[f]) for f in A.FAMILIES};pa={f:A.predict(Xa[:,:c[f]],models[f]) for f in A.FAMILIES}
        for f in A.FAMILIES:assert n[:c[f]]==models[f]['feature_names']
        # No loss/outcome summary is computed until the score command.
        np.savez(OUT/(sid+'_FORECASTS.npz'),**pp,**{'ablation_'+f:pa[f] for f in A.FAMILIES},trial=np.arange(len(X)),stimulus=d['stim_name'])
        p=OUT/(sid+'_FORECASTS.npz');pin[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
        ep,ex=A.endpoints(d);report[sid]=dict(rows=len(X),checks=ch,first_encounter_rows=ep,endpoint_exclusions=ex,primary_opportunities=len(ep),opto_rows=int(d['is_opto'].sum()),repeat_rows=int(d['is_repeat'].sum()),instruction_rows=int(d['is_instruction'].sum()),all_acquired_columns_consumed=COLS)
    valid=all_ok and all(x['primary_opportunities']>=3 for x in report.values())
    save('FORECAST_PINS.json',dict(created_utc=A.stamp(),forecasts_saved_before_scoring=True,scientific_freeze_utc=freeze['created_utc'],paths=pin))
    save('EVALUATION_DATA_CHECK.json',dict(created_utc=A.stamp(),valid_for_primary=valid,subjects=report,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps(dict(forecasts_saved=True,valid_for_primary=valid,subjects={s:dict(rows=x['rows'],first_encounters=x['primary_opportunities'],checks=x['checks']) for s,x in report.items()}),indent=2))
def contrast(gains):
    a=np.array(gains,dtype=float);N=len(a);mu=float(a.mean());se=float(a.std(ddof=1)/np.sqrt(N));q=float(A.student_t.ppf(.975,N-1));ref=np.array([np.mean(a*np.array(signs)) for signs in itertools.product([-1,1],repeat=N)])
    return dict(equal_animal_mean_gain=mu,animal_gains=a.tolist(),student_t95_interval=[mu-q*se,mu+q*se],one_sided_exact_sign_reference_p=float(np.mean(ref>=mu-1e-14)),positive_animals=int(np.sum(a>0)),animals=N,interpretation='N3 independent selected animals; sign-flip reference assumes exchangeable signs, t interval assumes independent normal animal gains. Neither calibrated coverage nor population significance certified.')
def score():
    check_freeze();check=json.loads((OUT/'EVALUATION_DATA_CHECK.json').read_bytes());pins=json.loads((OUT/'FORECAST_PINS.json').read_bytes())
    assert all(hashlib.sha256((OUT/p).read_bytes()).hexdigest()==h for p,h in pins['paths'].items())
    assert check['valid_for_primary'],'Chronology or first-encounter gate failed; do not substitute cohort.'
    rows=[];animals={};strata={};secondary={};ablation={}
    for sid in A.EVAL:
        d=dict(np.load(OUT/(sid+'_evaluation_arrays.npz'),allow_pickle=True));p=dict(np.load(OUT/(sid+'_FORECASTS.npz'),allow_pickle=True));ep,_=A.endpoints(d);ix=np.array([x['trial'] for x in ep]);y=d['is_response'][ix].astype(float)
        animals[sid]={f:dict(log_loss=float(np.mean(A.nll(y,p[f][ix]))),brier=float(np.mean((y-p[f][ix])**2)),forecast_response_rate=float(p[f][ix].mean())) for f in A.FAMILIES}
        animals[sid]['observed_response_rate']=float(y.mean());animals[sid]['encounters']=len(ix)
        ablation[sid]={f:float(np.mean(A.nll(y,p['ablation_'+f][ix]))) for f in A.FAMILIES}
        for j,e in enumerate(ep):rows.append(dict(subject=sid,**e,outcome=int(y[j]),**{f:float(p[f][e['trial']]) for f in A.FAMILIES},**{'loss_'+f:float(A.nll(y[j],p[f][e['trial']])) for f in A.FAMILIES}))
        strata[sid]={}
        for strict in [False,True]:
            jj=np.array([j for j,e in enumerate(ep) if e['strict_immediate']==strict],dtype=int)
            strata[sid]['immediate' if strict else 'delayed']=dict(encounters=len(jj),losses={f:float(np.mean(A.nll(y[jj],p[f][ix[jj]]))) for f in A.FAMILIES} if len(jj) else None)
        mask=A.eligible(d);first=[]
        for block in sorted(set(d['block_index'])):
            if block==0:continue
            for s in ['aud+','aud-','vis+','vis-']:
                cand=np.flatnonzero((d['block_index']==block)&(d['stim_name']==s)&mask)
                if len(cand):first.append(int(cand[0]))
        secondary[sid]=dict(all_eligible_trials=int(mask.sum()),all_eligible_log_loss={f:float(np.mean(A.nll(d['is_response'][mask],p[f][mask]))) for f in A.FAMILIES},first_noninstruction_per_stimulus_count=len(first),first_noninstruction_per_stimulus_log_loss={f:float(np.mean(A.nll(d['is_response'][first],p[f][first]))) for f in A.FAMILIES})
    contrasts={}
    for model,base in [('R','L'),('R','G'),('R','C'),('C','G'),('G','L')]:contrasts[model+'_over_'+base]=contrast([animals[s][base]['log_loss']-animals[s][model]['log_loss'] for s in A.EVAL])
    passed=all(contrasts['R_over_'+f]['equal_animal_mean_gain']>=.05 and contrasts['R_over_'+f]['positive_animals']==3 for f in ['G','C'])
    out=dict(created_utc=A.stamp(),primary='first formerly rewarded target encounter after a switch',finite_practical_rule_pass=passed,animal_scores=animals,equal_animal_log_loss={f:float(np.mean([animals[s][f]['log_loss'] for s in A.EVAL])) for f in A.FAMILIES},contrasts=contrasts,predeclared_schedule_strata=strata,predeclared_instruction_history_ablation_log_loss=ablation,secondary_descriptive=secondary,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save('PRIMARY_SCORES.json',out);save('SCORED_TRIALS.json',rows)
    print(json.dumps(dict(finite_practical_rule_pass=passed,equal_animal_log_loss=out['equal_animal_log_loss'],contrasts=contrasts,animal_scores=animals),indent=2))
if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='plan':plan()
    elif mode=='forecast':forecast()
    elif mode=='score':score()
    else:raise ValueError(mode)
