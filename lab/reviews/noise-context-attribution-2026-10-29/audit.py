"""Independent chronology/scoring/evidence audit; never reads human payloads."""
from pathlib import Path
import json,math,time,resource,copy,hashlib,importlib.util
import numpy as np
from scipy.special import betaln

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
TASK=ROOT/'lab/tasks/noise-context-feasibility-2026-10-29'
SRC=ROOT/'sources/noise_context_feasibility_2026-10-29'
sp=importlib.util.spec_from_file_location('ablation_frozen',HERE/'ablation.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
pilot=a.pilot
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    start=time.monotonic();checks=[]
    def ck(name,yes,detail=None):
        checks.append({'check':name,'pass':bool(yes),'detail':detail})
        if not yes:raise AssertionError(checks[-1])
    oldfreeze=json.loads((TASK/'FREEZE.json').read_text())
    for n,h in oldfreeze['files'].items():ck('original_freeze_'+n,sha(TASK/n)==h['sha256'])
    fr=json.loads((HERE/'FREEZE.json').read_text())
    for n,h in fr['comparison_files'].items():ck('comparison_freeze_'+n,sha(HERE/n)==h)
    for n,h in fr['source_task_files'].items():ck('unchanged_task_'+n,sha(TASK/n)==h)
    pins=json.loads((SRC/'SOURCE_PINS.json').read_text())
    for n,p in pins['files'].items():
        raw=(SRC/n).read_bytes()
        ck('source_sha256_'+n,hashlib.sha256(raw).hexdigest()==p['sha256'])
        ck('source_git_blob_'+n,hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==p['git_blob'])
    for n in ('__init__','begin_story','end_story','likes','predict','observe'):
        ck('ablation_inherits_'+n,getattr(a.ReliabilityOne,n) is getattr(pilot.Learner,n))
    m=json.loads((HERE/'ablation_metadata.json').read_text());met=json.loads((HERE/'ablation_metrics.json').read_text())
    with np.load(HERE/'ablation_predictions.npz',allow_pickle=False) as z:
        p=z['p'];w=z['w'];e=z['estimated_w'];assignment=z['z']
    ck('960_runs_shape',p.shape==(960,200,4,2) and w.shape==(960,200,4) and assignment.shape==(960,200,4))
    ck('probability_simplex',np.isfinite(p).all() and p.min()>=0 and p.max()<=1 and np.max(abs(p.sum(-1)-1))<1e-13)
    mxscore=0.;mxe=0.;edge=[]
    for idx,meta in enumerate(m):
        exp,ctx,pairs,noise=a.independent_inputs(meta['seed'],meta['curriculum'],meta['family'],meta['permuted'])
        truth=(exp[:,1:,None]==pairs[None,:,:]).argmax(-1)
        pc=p[idx,np.arange(200)[:,None],np.arange(4)[None,:],truth]
        sig=[j for j in range(1,4) if j!=noise]
        vals={'test_signal_probability':pc[160:,sig].mean(),
              'test_signal_nll':-np.log(pc[160:,sig]).mean(),
              'stories81to85_probability':pc[80:85,sig].mean(),
              'stories81to120_probability':pc[80:120,sig].mean()}
        for k,v in vals.items():mxscore=max(mxscore,abs(float(v)-met[idx][k]))
        counts=np.zeros((206,9,9))
        for story in range(200):
            for step in range(4):
                x=int(exp[story,step]);logbf=0.
                for c in counts[:,x,:]:
                    nz=c[c>0]
                    if not len(nz):continue
                    ck_n=bool(len(nz)<=2)
                    if not ck_n:raise AssertionError('not a two-outcome input family')
                    n1=float(nz[0]);n2=float(nz[1]) if len(nz)>1 else 0.
                    logbf+=float(betaln(n1+.5,n2+.5)-betaln(.5,.5)+(n1+n2)*math.log(2))
                vv=1/(1+math.exp(-max(-700,min(700,logbf))))
                mxe=max(mxe,abs(vv-e[idx,story,step]))
            # End-of-story assignment, not a transition's provisional MAP.
            group=int(assignment[idx,story,-1])
            for step in range(4):counts[group,exp[story,step],exp[story,step+1]]+=1
        if not meta['permuted']:
            edge.append({**meta,'test_p_steps':pc[160:].mean(0).tolist(),'test_estimated_w_steps':e[idx,160:].mean(0).tolist()})
    ck('all_960_independent_scores',mxscore<1e-13,{'max_error':mxscore})
    ck('all_960_completed_story_beta_evidence',mxe<1e-11,{'max_error':mxe})
    ck('all_ablation_applied_weights_one',np.all(w[[i for i,x in enumerate(m) if x['role']=='reliability_one']]==1))
    ck('all_full_applied_weights_equal_estimated',np.array_equal(w[[i for i,x in enumerate(m) if x['role']=='full']],e[[i for i,x in enumerate(m) if x['role']=='full']]))
    lookup={(x['family'],x['curriculum'],x['seed'],x['permuted'],x['role']):i for i,x in enumerate(m)}
    for key,i in lookup.items():
        if key[3]:continue
        j=lookup[(key[0],key[1],key[2],True,key[4])]
        assert all(np.array_equal(q[i],q[j]) for q in (p,w,e,assignment))
    ck('all_480_state_permutation_pairs_exact',True)
    # Check source chronology and oracle semantics on one consumed original input.
    seq=pilot.make_sequence(27001,'blocked','original')
    src=pilot.source_module();native=[]
    for skip in (False,True):
        engine=src.SEM(schargs=pilot.S2,skipt1=skip,ppd_allsch=0)
        data=engine.run_exp(seq['exp'])
        rr=pilot.run(seq,'oracle' if skip else 'no_oracle')
        errs=[]
        for s in range(200):
            for t in range(4):
                if skip and t==1:continue
                vv=data['xth'][s,t,list(seq['pairs'][t])];vv=np.exp(4*(vv-vv.max()));vv/=vv.sum()
                errs.append(float(np.max(abs(vv-rr[1][s,t]))))
        mask=data['zt'][:,:4]!=-1
        native.append({'oracle_skip':skip,'max_prediction_error':max(errs),'assignments_exact':bool(np.array_equal(data['zt'][:,:4][mask],rr[3][mask]))})
    ck('native_source_MatchedS2_and_oracle_chronology',all(v['max_prediction_error']<1e-13 and v['assignments_exact'] for v in native),native)
    for ablated in (False,True):
        rr=a.online(seq,ablated)
        alt=copy.deepcopy(seq);alt['ctx']=1-alt['ctx'];alt['noise_t']=3;alt['family']='altered_annotation';alt['curr']='altered_annotation'
        ss=a.online(alt,ablated)
        ck('evaluator_annotations_do_not_affect_'+str(ablated),all(np.array_equal(x,y) for x,y in zip(rr[:4],ss[:4])))
        alt=copy.deepcopy(seq);alt['exp'][91:]=alt['exp'][91:][::-1]
        ss=a.online(alt,ablated)
        ck('future_suffix_does_not_affect_'+str(ablated),all(np.array_equal(x[:91],y[:91]) for x,y in zip(rr[:4],ss[:4])))
        cls=a.ReliabilityOne if ablated else pilot.Learner
        q=cls('learned');q.begin_story();before=copy.deepcopy(q)
        pred=q.predict(0,[1,2]);q.predict(0,[1,2])
        ck('prediction_does_not_update_'+str(ablated),np.array_equal(q.posterior,before.posterior) and np.array_equal(q.T,before.T) and np.array_equal(q.raw,before.raw) and q.n_updates==0 and np.array_equal(pred,[.5,.5]))
    # Use frozen source-role metrics only to quantify the residual inference-package gain.
    oldmet=json.loads((TASK/'scored_metrics.json').read_text())
    residual=[]
    for f in a.FAMILIES:
        for c in ('blocked','interleaved'):
            full=np.array([x['test_signal_probability'] for x in met if x['family']==f and x['curriculum']==c and x['role']=='full' and not x['permuted']])
            one=np.array([x['test_signal_probability'] for x in met if x['family']==f and x['curriculum']==c and x['role']=='reliability_one' and not x['permuted']])
            base=np.array([x['test_signal_probability'] for x in oldmet if x['family']==f and x['curriculum']==c and x['role']=='no_oracle' and not x['permuted']])
            residual.append({'family':f,'curriculum':c,'original_mean':float(base.mean()),'full_minus_original':float((full-base).mean()),'reliability_one_minus_original':float((one-base).mean())})
    before=fr['source_task_files'];ck('all_frozen_task_bytes_still_unchanged',all(sha(TASK/n)==h for n,h in before.items()))
    duration=time.monotonic()-start
    run=json.loads((HERE/'ABLATION.json').read_text())
    ck('combined_substantive_runtime_under_300s',duration+run['runtime_seconds']<300,{'combined_seconds':duration+run['runtime_seconds']})
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    ck('RSS_under_2GB',max(peak,run['peak_rss_bytes_macos'])<=2_000_000_000,{'audit_peak_bytes':peak,'ablation_peak_bytes':run['peak_rss_bytes_macos']})
    result={'all_pass':all(x['pass'] for x in checks),'checks':checks,'n_checks':len(checks),
            'residual_inference_package_gain':residual,'edgewise':edge,
            'runtime_seconds':duration,'combined_runtime_seconds':duration+run['runtime_seconds'],'peak_rss_bytes_macos':peak,
            'scope':'Independent reviewer, consumed synthetic inputs only; not human validation or a new holdout.'}
    (HERE/'AUDIT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','edgewise')},indent=2))

if __name__=='__main__':main()
