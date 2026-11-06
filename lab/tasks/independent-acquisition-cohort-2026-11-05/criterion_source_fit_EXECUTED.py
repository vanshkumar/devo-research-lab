"""Exact official trained1a readout on original74 consumed source<=6000."""
from collections import Counter
from datetime import datetime,timezone
import ast,hashlib,importlib.util,io,json,resource,time
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'acquisition-rule-vs-tracker-2026-11-05'
cpu,wall=time.process_time(),time.monotonic();IO=Counter();PINS={}


def read(p):
    b=p.read_bytes();IO['explicit_reads']+=len(b);PINS[p.name]=hashlib.sha256(b).hexdigest();return b


# Execute only the inspected mathematical dependency and the official criterion.
source=read(HERE/'psychofit_reference.py')
spec=importlib.util.spec_from_file_location('psy_reference',HERE/'psychofit_reference.py')
psy=importlib.util.module_from_spec(spec);spec.loader.exec_module(psy)
tree=ast.parse(read(HERE/'IBL_TRAINING_CRITERIA.py').decode())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='criterion_1a')
ns={'np':np,'Bunch':dict};exec(compile(ast.Module(body=[fn],type_ignores=[]),'official_criterion_1a','exec'),ns)
criterion=ns['criterion_1a']


def classify(blocks,key):
    nums=np.array([len(a) for a in blocks]);easy=[]
    for a in blocks:
        x=100*(np.nan_to_num(a[:,1])-np.nan_to_num(a[:,0]));keep=np.abs(x)>=50
        easy.append(float(np.mean(a[keep,3]==1)) if keep.any() else 0.)
    a=np.concatenate(blocks);x=100*(np.nan_to_num(a[:,1])-np.nan_to_num(a[:,0]))
    if len(blocks)!=3 or not ((nums>200).all() and min(easy)>.8 and (x==0).any()):
        return dict(passed=False,necessary_pass=False,fit_cpu_seconds=0.)
    contrasts,n=np.unique(x,return_counts=True)
    prop=np.array([np.mean(a[x==z,2]==-1) for z in contrasts]) # omissions remain denominator
    seed=int.from_bytes(hashlib.sha256(key.encode()).digest()[:4],'little');np.random.seed(seed)
    start=time.process_time()
    pars,ll=psy.mle_fit_psycho(np.vstack([contrasts,n,prop]),P_model='erf_psycho_2gammas',
        parstart=np.array([np.mean(contrasts),20.,.05,.05]),
        parmin=np.array([min(contrasts),0.,0.,0.]),parmax=np.array([max(contrasts),100.,1.,1.]))
    elapsed=time.process_time()-start
    passed,details=criterion(pars,nums,np.array(easy),contrasts)
    return dict(passed=bool(passed),necessary_pass=True,psychometric=pars.tolist(),log_likelihood=float(ll),
                 n=nums.tolist(),easy=easy,seed=seed,fit_cpu_seconds=elapsed)


manifest=json.loads(read(OLD/'SOURCE_FIT6000_MANIFEST.json'))
with (HERE/'EXPOSURE.jsonl').open('a') as f:
    f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event='original74_source_trained1a_readout',
          subjects=manifest['subjects'],maximum_selected_rows=6000,fields=manifest['fields']+['session_start'],no_evaluation_read=True))+'\n')
with np.load(io.BytesIO(read(OLD/'TRAIN6000_ROWS.npz')),allow_pickle=False) as z:raw={k:z[k] for k in z.files}
IO['decoded_array_bytes']+=sum(a.nbytes for a in raw.values());out=[];fits=[]
for s in manifest['subjects']:
    a=raw[s];assert len(a)<=6000
    rr=sorted([r for r in manifest['sessions'] if r['subject']==s and r['stop']<=len(a)],key=lambda r:(r['date'],r['number']))
    days=[];dates=[];ends=[]
    for r in rr:
        b=a[r['start']:r['stop']]
        if dates and dates[-1]==r['date']:days[-1]=np.concatenate([days[-1],b]);ends[-1]=r['stop']
        else:days.append(b);dates.append(r['date']);ends.append(r['stop'])
    first=None;results=[]
    for j in range(2,len(days)):
        fit=classify(days[j-2:j+1],f'{s}:{dates[j]}:trained1a-v1')
        fit.update(subject=s,date=dates[j],end=ends[j]);results.append(fit)
        if fit['necessary_pass']:fits.append(fit)
        if fit['passed'] and first is None:first=ends[j]
    out.append(dict(subject=s,first_trained1a_end=first,selected_rows=len(a),
                    censor_at_last_complete_training_day=ends[-1] if ends else 0,windows=results))
# Boundary checks invoke the actual official criterion, independently of source values.
base=dict(psych=np.array([0.,10.,.05,.05]),n_trials=np.array([300,300,300]),perf_easy=np.array([.95]*3),signed_contrast=np.array([-100.,0.,100.]))
controls=[]
for label,key,value in [('valid',None,None),('bias_boundary','psych',np.array([16.,10.,.05,.05])),
    ('threshold_boundary','psych',np.array([0.,19.,.05,.05])),('lapse_boundary','psych',np.array([0.,10.,.2,.05])),
    ('trial_boundary','n_trials',np.array([200,300,300])),('easy_boundary','perf_easy',np.array([.8,.95,.95])),
    ('zero_absent','signed_contrast',np.array([-100.,100.]))]:
    args=base.copy()
    if key:args[key]=value
    v=bool(criterion(**args)[0]);assert v==(label=='valid');controls.append(dict(case=label,passed=v))
summary=[]
for h in [3000,4000,6000]:
    events=sum(r['first_trained1a_end'] is not None and r['first_trained1a_end']<=h for r in out)
    censored=sum((r['first_trained1a_end'] is None or r['first_trained1a_end']>h) and r['censor_at_last_complete_training_day']<h for r in out)
    summary.append(dict(horizon=h,observed_first_passages=events,event_free_observation_through_h=74-events-censored,
                        right_censored_before_h_without_observed_event=censored,source_animals=74))
result=dict(utc=datetime.now(timezone.utc).isoformat(),source_only=True,summary=summary,subjects=out,controls=controls,
       exact_official_fit='Official five-fit non-plotting erf_psycho_2gammas prescription; fixed hash seed. Omissions count in denominators. Last3consecutive calendar training days, same-date sessions pooled. This is a defined computational criterion, not recovered historical operator labels.',
       solver='Official source notes the retained starts/constraints can be suboptimal; no plotting parameters or hindsight threshold repair used.',
       fit_windows=len(fits),fit_cpu_seconds=sum(r['fit_cpu_seconds'] for r in fits),
       max_fit_cpu_seconds=max((r['fit_cpu_seconds'] for r in fits),default=0.),
       io=dict(IO),pins=PINS,cpu_seconds=time.process_time()-cpu,process_wall_seconds=time.monotonic()-wall,
       peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(HERE/'CRITERION_SOURCE_FIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['subjects','pins']},indent=2))
