"""Compare independent reconstruction with saved evidence; verify pins/fit objectives."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import csv
import hashlib
import io
import json
import math
import re
import resource
from datetime import datetime, timezone
from pathlib import Path
import reconstruct as own

ROOT=own.ROOT;OUT=own.OUT;AUTHOR=own.AUTHOR
READS=[]
def read(p):
    p=Path(p);assert p.stat().st_size<2_000_000
    b=p.read_bytes();READS.append({'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()});return b
def load(p):return json.loads(read(p))
def csvload(p):return list(csv.DictReader(io.StringIO(read(p).decode())))
def save(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def leaf_strings(obj,path=''):
    if isinstance(obj,dict):
        for k,v in obj.items():yield from leaf_strings(v,path+'/'+str(k))
    elif isinstance(obj,list):
        for i,v in enumerate(obj):yield from leaf_strings(v,path+'/'+str(i))
    elif isinstance(obj,str):yield path,obj

def objective(fit,rows,t,model,eligible_only=False):
    stage=fit['stage'];b=fit['coefficients'];names=fit['coefficient_names']
    chosen=[r for r in rows if (r['A'] if stage in ('F','D') else r['B'] if stage=='Y' else True)]
    terms=[];grad=[b[i] if i else 0.0 for i in range(len(b))]
    for r in chosen:
        v=own.terms(r['t'],r['z'],r['Q'],model,stage,eligible_only)
        assert set(names)==set(v)
        x=[v[k] for k in names];eta=math.fsum(a*c for a,c in zip(x,b))
        p=1/(1+math.exp(-eta));y=r[stage]
        terms.append(max(eta,0)+math.log1p(math.exp(-abs(eta)))-y*eta)
        for i in range(len(b)):grad[i]+=x[i]*(p-y)
    val=math.fsum(terms)+.5*math.fsum(c*c for c in b[1:])
    if model in ('primacy','cancellation') and stage=='Y' and b[-1]<1e-10:grad[-1]=min(0.,grad[-1])
    return val,max(abs(g) for g in grad),grad

def main():
    manifest=load(AUTHOR/'MANIFEST.json')
    sourcepins=[]
    for m in manifest['immutable_input_reads']:
        b=read(ROOT/m['path']);actual=hashlib.sha256(b).hexdigest()
        sourcepins.append(dict(path=m['path'],bytes=len(b),sha256=actual,matches=actual==m['sha256'] and len(b)==m['bytes']))
    artifacts=load(AUTHOR/'ARTIFACTS.json');apins=[]
    for m in artifacts['files']:
        b=read(AUTHOR/m['file']);actual=hashlib.sha256(b).hexdigest()
        apins.append(dict(file=m['file'],bytes=len(b),sha256=actual,matches=actual==m['sha256'] and len(b)==m['bytes']))
    assert all(p['matches'] for p in sourcepins+apins)
    response=load(AUTHOR/'SOURCE_RESPONSES.json')
    terms=['used once','used only once','court_1','court_2','test_color','block','primacy','first-courting','first courting','choosiness','copiers','early','CC BY','license']
    excerpts=[]
    for path,s in leaf_strings(response):
        for term in terms:
            matches=list(re.finditer(re.escape(term),s,re.I))
            for m in matches[:3]:
                excerpts.append({'saved_response_path':path,'query':term,'snippet':s[max(0,m.start()-180):min(len(s),m.end()+270)]})
    save('SOURCE_EVIDENCE.json',{'source_pins':sourcepins,'artifact_pins':apins,'saved_responses_top_keys':list(response) if isinstance(response,dict) else None,'excerpts':excerpts,'new_network_requests':0,'scope':'Saved bytes/pins and rendered source excerpts only; no new source verification, deployment chronology or archive/final-version certification.'})
    a=load(OUT/'FIXED_COEFFICIENT_RECONSTRUCTION.json');e=load(OUT/'ELIGIBLE_ONLY_RECONSTRUCTION.json');b=load(AUTHOR/'COMPARISON.json')
    aggregate_error=own.max_compare(a['aggregate'],b['joint_models']);contrast_error=own.max_compare(a['contrasts'],b['contrasts'])
    eligible_error=max(own.max_compare(e['aggregate'],b['eligible_only_models']),own.max_compare(e['contrasts'],b['eligible_only_contrasts']))
    ownloss={(int(r['row']),r['model']):r for r in csvload(OUT/'LOSSES.csv')}
    oldloss=csvload(AUTHOR/'CV_LOSSES.csv');loss_error={k:0. for k in ('Y','joint','courtship','mating','participation','Y_integrated')}
    for r in oldloss:
        key=(int(r['row']),r['model']);c=ownloss[key]
        assert c['date']==r['held_date']
        for k in loss_error:loss_error[k]=max(loss_error[k],abs(float(c[k])-float(r[k])))
    assert max(loss_error.values())<1e-12 and max(aggregate_error,contrast_error,eligible_error)<1e-12
    decisions=[]
    for base in ('expression','cancellation'):
        cs={c['metric']:c for c in a['contrasts'] if c['baseline']==base and c['model']=='primacy'}
        rule=all(cs[k]['gain_nat']>=.01 and cs[k]['date_bootstrap_95'][0]>0 for k in ('joint','eligible_choice'))
        decisions.append({'baseline':base,'declared_joint_and_choice_rule_passes':rule})
    save('LOSS_COMPARISON.json',{'source_rows':462,'saved_joint_loss_rows':len(oldloss),'per_row_loss_max_error':loss_error,'aggregate_max_error':aggregate_error,'contrasts_max_error':contrast_error,'eligible_only_aggregate_and_contrast_max_error':eligible_error,'decisions':decisions,'evidence_kind':'Independent row/features/factorization/loss/bootstrap reconstruction using author frozen coefficients; no independent optimizer refit.'})
    rows=own.reconstruct();fit_records=[]
    cv=load(AUTHOR/'CV_FITS.json');ecv=load(AUTHOR/'ELIGIBLE_ONLY_FITS.json');full=load(AUTHOR/'FULL_FITS.json')
    for folds,eligible_only in ((cv,False),(ecv,True)):
        for fold in folds:
            train=[r for r in rows if r['date']!=fold['held_date'] and (r['eligible'] or not eligible_only)]
            for s,fit in fold['fits'].items():
                val,g,grad=objective(fit,train,None,fold['model'],eligible_only)
                fit_records.append({'model':fold['model'],'date':fold['held_date'],'eligible_only':eligible_only,'stage':s,'objective_error':abs(val-fit['objective']),'projected_gradient_error':abs(g-fit['projected_gradient_max']),'projected_gradient':g,'success':fit['success']})
    for m,fits in full.items():
        for s,fit in fits.items():
            val,g,grad=objective(fit,rows,None,m)
            fit_records.append({'model':m,'full':True,'stage':s,'objective_error':abs(val-fit['objective']),'projected_gradient_error':abs(g-fit['projected_gradient_max']),'projected_gradient':g,'success':fit['success']})
    assert max(f['objective_error'] for f in fit_records)<1e-10
    assert max(f['projected_gradient_error'] for f in fit_records)<1e-10
    # Central differences independently validate this review's gradient/objective.
    fit=dict(full['primacy']['Y']);beta=list(fit['coefficients']);analytic=objective(fit,rows,None,'primacy')[2];fd=[]
    for i in range(len(beta)):
        h=1e-5
        plus=dict(fit,coefficients=[v+(h if j==i else 0) for j,v in enumerate(beta)])
        minus=dict(fit,coefficients=[v-(h if j==i else 0) for j,v in enumerate(beta)])
        fd.append((objective(plus,rows,None,'primacy')[0]-objective(minus,rows,None,'primacy')[0])/(2*h))
    gradcheck=max(abs(x-y) for x,y in zip(fd,analytic));assert gradcheck<1e-7
    recheck=load(AUTHOR/'CHECK_RUN.json');details=load(AUTHOR/'NUMERICAL_RECHECK_DETAILS.json');controls=load(AUTHOR/'CONTROLS.json')
    save('OPTIMIZATION_AUDIT.json',{'independent_fitting':False,'fixed_fit_objective_and_gradient_records':fit_records,'max_objective_error':max(f['objective_error'] for f in fit_records),'max_projected_gradient_error':max(f['projected_gradient_error'] for f in fit_records),'independent_central_difference_gradient_max_error':gradcheck,'original_non_success':[f for f in fit_records if not f['success']],'saved_recheck_summary':recheck['numerical_summary'],'saved_detailed_recheck_top_keys':list(details) if isinstance(details,dict) else None,'saved_controls_top_keys':list(controls),'inherited_recheck_scope':'Author tighter fits, label invariance and positive/null generator recovery inspected as saved evidence; not rerun as independent fits.'})
    print('SAVED_DETAIL_STRUCTURE',json.dumps({k:(list(v)[:8] if isinstance(v,dict) else {'length':len(v),'first_keys':list(v[0]) if v and isinstance(v[0],dict) else None} if isinstance(v,list) else v) for k,v in details.items()},indent=2)[:6000])
    print('SAVED_CONTROL_STRUCTURE',json.dumps({k:(list(v)[:8] if isinstance(v,dict) else {'length':len(v),'first_keys':list(v[0]) if v and isinstance(v[0],dict) else None} if isinstance(v,list) else v) for k,v in controls.items()},indent=2)[:3500])
    save('READS_AUDIT.json',{'reads':READS+own.READS,'read_hash_bytes':sum(r['bytes'] for r in READS+own.READS),'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'completed_utc':datetime.now(timezone.utc).isoformat()})
    print(json.dumps({'source_pins':len(sourcepins),'artifact_pins':len(apins),'all_pins_pass':True,'saved_source_excerpts':len(excerpts),'loss_errors':loss_error,'aggregate_error':aggregate_error,'contrast_error':contrast_error,'eligible_error':eligible_error,'fixed_fit_records':len(fit_records),'objective_error':max(f['objective_error'] for f in fit_records),'gradient_error':max(f['projected_gradient_error'] for f in fit_records),'finite_difference_gradient_error':gradcheck,'decisions':decisions,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2))

if __name__=='__main__':main()
