"""Conditional score-rule controls, not refitted source-estimation/power controls."""
from model import *
from analysis import evaluate

people=np.arange(8)[:,None]
truep=np.tile(np.array([.90,.82,.70,.86]),(8,1))+(people-3.5)*.005
truert=np.tile(np.array([.60,.66,.72,.68]),(8,1))+(people-3.5)*.015
truth=np.stack([truep,truert],axis=2)
counts=np.array([16,16,16,48])
records=[]
for kind in ['substantial_signal','equal_expected_loss_null']:
    for rep in range(100):
        seed=2026110200+rep+(1000 if kind.endswith('null') else 0)
        rng=np.random.default_rng(seed)
        pc=np.clip(truep+rng.normal(0,.01,(8,1)),.01,.99)
        obs=np.stack([rng.binomial(counts,pc)/counts,truert+rng.normal(0,.015,(8,1))+rng.normal(0,.20/np.sqrt(counts),(8,4))],axis=2)
        if kind=='substantial_signal':candidate=truth.copy();reference=truth-.10
        else:candidate=truth+.015;reference=truth-.015
        pred={'reference':'REFERENCE','predictions':{'P':candidate.tolist(),'REFERENCE':reference.tolist()}}
        result=evaluate(pred,obs,seed)
        records.append({'kind':kind,'rep':rep,'seed':seed,'passes':result['primary_P_rule_passes'],'P':result['models']['P'],'REFERENCE':result['models']['REFERENCE']})
out={'at':stamp(),'scope':'Conditional decision-rule discrimination with binomial accuracy summaries/normal sample-mean RT errors, substantial .10accuracy/.10s wrong forecast; not Wiener raw trials, refitted-source controls,10%boundary power or interval coverage.',
     'truth':truth,'nominal_counts':counts,'repetitions_per_kind':100,'signal_passes':sum(r['passes'] for r in records if r['kind']=='substantial_signal'),'null_passes':sum(r['passes'] for r in records if r['kind']=='equal_expected_loss_null'),'records':records}
dump('CONTROLS.json',out);run_record('CONTROLS',20000000)
print({k:v for k,v in out.items() if k not in ['truth','records']})
