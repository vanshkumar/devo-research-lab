"""Same pooled acquisition counts/psychometric, different official trained1a."""
import ast,json,time,resource
from pathlib import Path
import numpy as np
import psychofit_reference as psy

HERE=Path(__file__).resolve().parent;cpu,wall=time.process_time(),time.monotonic()
tree=ast.parse((HERE/'IBL_TRAINING_CRITERIA.py').read_text())
fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='criterion_1a')
ns={'np':np,'Bunch':dict};exec(compile(ast.Module(body=[fn],type_ignores=[]),'official_criterion','exec'),ns)
contrasts=np.array([-100.,-25.,0.,25.,100.]);per_session_n=np.array([100,33,34,33,100])
profiles=[np.array([95,95,75]),np.array([89,88,88])]
pooled=[];results=[]
for high_correct in profiles:
    right=np.stack([np.array([100-k,4,17,29,k]) for k in high_correct])
    pooled.append(right.sum(0));n=3*per_session_n;prop=right.sum(0)/n
    np.random.seed(20261105161 % (2**32))
    psych,ll=psy.mle_fit_psycho(np.vstack([contrasts,n,prop]),P_model='erf_psycho_2gammas',
        parstart=np.array([np.mean(contrasts),20.,.05,.05]),parmin=np.array([-100.,0.,0.,0.]),parmax=np.array([100.,100.,1.,1.]))
    easy=high_correct/100
    passed,_=ns['criterion_1a'](psych,np.array([300]*3),easy,contrasts)
    results.append(dict(session_easy_correct_share=easy.tolist(),pooled_high_correct=int(2*high_correct.sum()),
          pooled_high_denominator=600,pooled_psychometric=psych.tolist(),criterion_1a=bool(passed)))
assert np.array_equal(pooled[0],pooled[1])
assert results[0]['criterion_1a']==False and results[1]['criterion_1a']==True
result=dict(same_per_contrast_pooled_counts=True,same_primary_side_specific_NK=True,
     same_three_session_pooled_psychometric=True,results=results,
     conclusion='Saved long-window pooled per-sign counts cannot determine trained1a first passage. Full generated joint session/contrast/choice/feedback histories or their sufficient histograms are required.',
     scope='Exact constructive measurement/readout counterexample, not a biological plant, predicted utility or power.',
     cpu_seconds=time.process_time()-cpu,process_wall_seconds=time.monotonic()-wall,
     input_read_charge_bytes=(HERE/'IBL_TRAINING_CRITERIA.py').stat().st_size+(HERE/'psychofit_reference.py').stat().st_size,
     peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(HERE/'CRITERION_COUNT_COUNTEREXAMPLE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
