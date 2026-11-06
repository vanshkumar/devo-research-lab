from data import ROOT,load_people,wrap
from model import grid_filter,approximate
import datetime,hashlib,json,resource
import numpy as np

people,audits,b=load_people('development')
results=[]
for x in people:
    flags=x['raw']['cp'] if x['context'] else x['raw']['oddBall']
    gaps=[]
    for bl in range(1,5):
        ix=np.flatnonzero((x['block']==bl)&(flags==1));gaps.extend(np.diff(ix).tolist())
    assert all(v>=4 for v in gaps)
    results.append(dict(id=x['id'],context=x['context'],min_within_block_event_gap=min(gaps),short_gaps=0))

grid=[]
for c in [0,1]:
    f=next(x for x in people if x['id']=='201' and x['context']==c)
    coarse=grid_filter(f['outcome'],c,f['block'],360)
    fine=grid_filter(f['outcome'],c,f['block'],720)
    diff=dict(context=c,max_angle=float(np.max(abs(wrap(coarse[0]-fine[0])))),max_resultant=float(np.max(abs(coarse[1]-fine[1]))),max_event=float(np.max(abs(coarse[2]-fine[2]))))
    assert diff['max_angle']<.005 and diff['max_event']<.005
    grid.append(diff)

# Analytic first-trial checks not using observed behavior.
ys=np.deg2rad(np.full(10,90.));bs=np.ones(10)
cp=grid_filter(ys,1,bs);ob=grid_filter(ys,0,bs)
assert abs(cp[2][0]-1)<1e-14
expected_ob=(.25/359)/(.75/360+.25/359)
assert abs(ob[2][0]-expected_ob)<1e-10
assert cp[2][1]==0 and cp[2][2]==0 and cp[2][3]==0

source_pins=[]
for tree_name,pairs in [('code_tree',[('source_analysis','nassarBrucknerFrank2019_analysis.m'),('source_model','helperFunctions/getTrialVarsFromPEs_cannon.m'),('source_readme','README.md'),('source_license','LICENSE')]),('task_tree',[('task_generate','Task/Functions/GenerateOutcomes.m'),('task_config','Task/AdaptiveLearning.m'),('task_main','Task/Functions/Main.m'),('task_odd','Task/Functions/Oddball.m'),('task_export','DataScripts/ExportData.m')])]:
    tree=json.loads((ROOT/(tree_name+'.source')).read_text());entries={x['path']:x for x in tree['tree']}
    for local,path in pairs:
        data=(ROOT/(local+'.source')).read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert blob==entries[path]['sha']
        source_pins.append(dict(local=local,path=path,bytes=len(data),git_blob=blob,sha256=hashlib.sha256(data).hexdigest(),tree=tree['sha']))

out=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_blob_checks=source_pins,within_block_safe_rule=results,grid_refinement_201_both_contexts=grid,analytic_first_ob_event_probability=expected_ob,computed_first_ob_event_probability=float(ob[2][0]),cp_first_event_probability=float(cp[2][0]),cp_next_three_event_probabilities=cp[2][1:4].tolist(),source_note='Earlier DEVELOPMENT_SOURCE_CHECK event-gap fields included across-block forced resets. Their short gaps were boundary crossings, not violations; all within-block gaps here are >=4. Published constant-hazard approximation is distinct from conditional .25/safe3 law. No deployed hardware timestamp accuracy or original recruitment randomization certified.',peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(ROOT/'SOURCE_VALIDATION.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ['source_blob_checks','within_block_safe_rule']},indent=2))
