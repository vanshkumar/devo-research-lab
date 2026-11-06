import sys
from model import *

def develop():
    df=data();gs=[trials(df,i,1) for i in range(1,10)];ts=[trials(df,i,2) for i in range(1,10)]
    center,cinfo=baseline(combine(gs));print('pooled baseline',cinfo,flush=True)
    fits=[];infos=[]
    for i,g in enumerate(gs,1):
        p,inf=baseline(g,center);fits.append(p);infos.append(inf);print('source baseline',i,inf,flush=True)
    dump('SOURCE_BASELINE_CHECKPOINT.json',{'at':stamp(),'center':center,'pooled_fit':cinfo,'parameters':fits,'status':infos})
    pm,pinf=mapping(fits,ts,False);print('P map',pm,pinf,flush=True)
    qm,qinf=mapping(fits,ts,True);print('Q map',qm,qinf,flush=True)
    B=np.array([summary(g)[0] for g in gs]);F=np.array([summary(g)[1] for g in gs]);Y=np.array([summary(g)[0] for g in ts])
    emp=empirical(B,F,Y)
    out={'at':stamp(),'source_ids':list(range(1,10)),'evaluation_ids':list(range(10,18)),'center':center,'pooled_fit':cinfo,'source_baseline_parameters':fits,'source_baseline_fit_status':infos,'P_mapping':pm,'P_status':pinf,'Q_mapping':qm,'Q_status':qinf,'empirical':emp,'source_baseline_observed':B,'source_target_observed':Y,'source_target_counts':[summary(g)[2] for g in ts]}
    dump('SOURCE_FIT.json',out);run_record('DEVELOP',40000000)
    print('Source reference',emp['reference'],emp['source_CV_joint_loss'],flush=True)

def freeze():
    ss=load('SOURCE_FIT.json')
    assert ss['pooled_fit']['success'] and all(x['success'] for x in ss['source_baseline_fit_status'])
    assert ss['P_status']['success'] and ss['Q_status']['success']
    out={'at':stamp(),'evaluation_outcomes_interpreted':False,'reference':ss['empirical']['reference'],'files':freeze_pins(['PROTOCOL.md','DEVELOPMENT_AMENDMENT.md','model.py','analysis.py','SOURCE_FIT.json','speed_acc.RData','FIRST_DATA_CHECK.json','audit.py','controls.py'])}
    if (ROOT/'FREEZE.json').exists():raise RuntimeError('Refusing overwrite freeze')
    dump('FREEZE.json',out);print(json.dumps(out,indent=2))

def predict():
    f=load('FREEZE.json');assert freeze_pins(list(f['files']))==f['files']
    ss=load('SOURCE_FIT.json');df=data();bs=[trials(df,i,1) for i in range(10,18)]
    fits=[];infos=[]
    for i,g in zip(range(10,18),bs):
        p,inf=baseline(g,ss['center']);fits.append(p);infos.append(inf);print('evaluation baseline only',i,inf,flush=True)
    B=np.array([summary(g)[0] for g in bs]);F=np.array([summary(g)[1] for g in bs]);pred=empirical_predict(B,F,ss['empirical'])
    pred['P']=np.array([integrals(transport(p,ss['P_mapping']),192)[1] for p in fits]);pred['Q']=np.array([integrals(transport(p,ss['Q_mapping'],True),192)[1] for p in fits])
    assert all(np.isfinite(x).all() for x in pred.values())
    out={'at':stamp(),'ids':list(range(10,18)),'baseline_parameters':fits,'baseline_status':infos,'baseline_observed':B,'baseline_features':F,'predictions':pred,'reference':f['reference'],'target_response_values_used':False,'nominal_target_category_counts':[16,16,16,48]}
    if (ROOT/'PREDICTIONS.json').exists():raise RuntimeError('Refusing overwrite predictions')
    dump('PREDICTIONS.json',out);dump('PREDICTION_PIN.json',{'at':stamp(),'sha256':freeze_pins(['PREDICTIONS.json'])});run_record('PREDICT',30000000)
    print('Saved predictions BEFORE scoring',out['at'])

def evaluate(pred,obs,seed=20261101):
    ref=pred['reference'];pp={k:np.array(v) for k,v in pred['predictions'].items()};ls={k:losses(v,obs) for k,v in pp.items()}
    rng=np.random.default_rng(seed);ix=rng.integers(0,len(obs),(10000,len(obs)))
    mean={k:v.mean(axis=0) for k,v in ls.items()};base=ls[ref]
    details={}
    for k,v in ls.items():
        gain=1-v[:,2].mean()/base[:,2].mean();draw=1-v[ix,2].mean(axis=1)/base[ix,2].mean(axis=1)
        abserr=np.sum(np.abs(pp[k]-obs)*W[None,:,None],axis=1).mean(axis=0)
        details[k]={'accuracy_mse':float(mean[k][0]),'rt_mean_mse_s2':float(mean[k][1]),'joint_loss':float(mean[k][2]),'joint_fractional_gain_over_reference':float(gain),'conditional_bootstrap_gain_percentiles':np.percentile(draw,[2.5,97.5]),'accuracy_MAE':float(abserr[0]),'rt_mean_MAE_s':float(abserr[1]),'people_joint_better':int(np.sum(v[:,2]<base[:,2])),'per_person_losses':v}
    p=details['P'];passed=(p['joint_fractional_gain_over_reference']>=.10 and p['conditional_bootstrap_gain_percentiles'][0]>0 and mean['P'][0]<mean[ref][0] and mean['P'][1]<mean[ref][1] and p['accuracy_MAE']<=.05 and p['rt_mean_MAE_s']<=.05)
    return {'reference':ref,'models':details,'primary_P_rule_passes':bool(passed)}

def score():
    f=load('FREEZE.json');assert freeze_pins(list(f['files']))==f['files']
    pin=load('PREDICTION_PIN.json');assert freeze_pins(['PREDICTIONS.json'])==pin['sha256']
    pred=load('PREDICTIONS.json');df=data();tt=[trials(df,i,2) for i in pred['ids']];obs=np.array([summary(g)[0] for g in tt])
    out=evaluate(pred,obs);out.update(at=stamp(),target_values=obs,target_counts=[summary(g)[2] for g in tt],baseline_fit_successes=sum(x['success'] for x in pred['baseline_status']))
    out['primary_P_rule_passes']=bool(out['primary_P_rule_passes'] and out['baseline_fit_successes']==len(pred['ids']))
    dump('SCORES.json',out);run_record('SCORE',30000000)
    print(json.dumps({k:v for k,v in out.items() if k not in ['target_values','target_counts','models']},indent=2))
    for k,v in out['models'].items():print(k,{a:b for a,b in v.items() if a!='per_person_losses'})

if __name__=='__main__':
    {'develop':develop,'freeze':freeze,'predict':predict,'score':score}[sys.argv[1]]()
