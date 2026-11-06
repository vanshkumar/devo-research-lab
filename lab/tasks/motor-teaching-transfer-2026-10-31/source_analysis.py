"""Consumed source outcomes only; never opens Figure 4."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
import csv, json, hashlib, resource
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT/'sources/learning_intervention_feasibility_2026-10-28'
FILES=('tsay_TE_SPE.csv','tsay_controljump.csv','task_success_fig3.csv')
NAMES=['constant','clamp_over4','clamp_x_any_jump','clamp_x_success',
       'physical_jump_over4','next_minus_current_jump_over4']

def num(v):
    try: return float(v)
    except (ValueError,TypeError): return float('nan')

def load(name):
    p=SOURCE/name
    b=p.read_bytes()
    source_manifest=json.loads((SOURCE/'source_manifest.json').read_text())
    m=next(x for x in source_manifest['files'] if x['local']==name)
    assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==m['expected_git_blob']
    by=defaultdict(list)
    fields={'SN','TN','clamp_size','tgt_jump_size','Hand_raw'} if name.startswith('tsay') else {'Subject','TrialNum','ClampAngle','TargetJump','HandError','FalseStart'}
    with p.open(newline='') as f:
        for full in csv.DictReader(f):
            row={k:v for k,v in full.items() if k in fields}
            if name.startswith('tsay'):
                person=int(row['SN']); t=int(row['TN']); c=num(row['clamp_size']); j=num(row['tgt_jump_size'])
                h=num(row['Hand_raw']); bad=False; flicker=False
            else:
                person=int(row['Subject']); t=int(row['TrialNum']); c=num(row['ClampAngle']); rawj=num(row['TargetJump'])
                flicker=rawj==0.01; j=0. if flicker else rawj
                h=num(row['HandError']); bad=num(row['FalseStart'])==1
            by[person].append(dict(t=t,c=c,j=j,h=h,bad=bad,flicker=flicker,
                                   jump=(j!=0 or flicker),hit=(c!=0 and j==c)))
    return by,dict(file=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),
                   charge=8*len(b),retained_outcome='Hand_raw' if name.startswith('tsay') else 'HandError',
                   decoded_rows=sum(len(v) for v in by.values()),n_people=len(by))

def extract(name,by):
    people=[]; cellrows=[]
    for person,rows in sorted(by.items()):
        rows.sort(key=lambda r:r['t'])
        X=[]; Y=[]; cells=defaultdict(list); rejected=defaultdict(int)
        for a,b in zip(rows,rows[1:]):
            if b['t']!=a['t']+1: rejected['nonadjacent']+=1; continue
            if name.startswith('tsay'):
                if a['t']<=100: continue
                i=a['t']-101
                # Keep both endpoints in one 180-trial randomized portion.
                if i%181>=179: rejected['block_boundary_or_terminal']+=1;continue
            elif not 104<=a['t']<=903: continue
            if a['bad'] or b['bad'] or not np.isfinite([a['h'],b['h']]).all() or abs(a['h'])>90 or abs(b['h'])>90:
                rejected['endpoint_mask']+=1;continue
            c=a['c']/4; j=a['j']/4; dj=(b['j']-a['j'])/4
            X.append([1.,c,c*a['jump'],c*a['hit'],j,dj]);Y.append(b['h']-a['h'])
            cells[(a['c'],a['j'],a['flicker'])].append(b['h']-a['h'])
        X=np.array(X); Y=np.array(Y)
        beta,_,rank,_=np.linalg.lstsq(X,Y,rcond=None)
        naive=np.linalg.lstsq(X[:,:5],Y,rcond=None)[0]
        people.append(dict(person=person,X=X,Y=Y,beta=beta,naive=naive,rank=int(rank),
                           condition_number=float(np.linalg.cond(X)),rejected=dict(rejected)))
        for (c,j,flicker),yy in sorted(cells.items()):
            cellrows.append(dict(source=name,person=person,clamp=c,jump=j,flicker=flicker,n=len(yy),
                                 mean_delta=float(np.mean(yy)),median_delta=float(np.median(yy)),
                                 signed_adaptation_mean=float(-np.sign(c)*np.mean(yy)) if c else None))
    return people,cellrows

def ci(a):
    a=np.asarray(a);return dict(mean=float(np.mean(a)),lo=float(np.quantile(a,.025)),hi=float(np.quantile(a,.975)))

def dot(a,b):
    a=np.asarray(a);b=np.asarray(b)
    assert np.isfinite(a).all() and np.isfinite(b).all()
    z=np.einsum('...i,i->...',a,b)
    assert np.isfinite(z).all()
    return z

def main():
    if (HERE/'SOURCE_ANALYSIS.json').exists() and not (HERE/'SOURCE_ANALYSIS_INITIAL_WARNINGS.json').exists():
        (HERE/'SOURCE_ANALYSIS_INITIAL_WARNINGS.json').write_bytes((HERE/'SOURCE_ANALYSIS.json').read_bytes())
    rng=np.random.default_rng(20261031)
    out=dict(created_utc=datetime.now(timezone.utc).isoformat(),scope='All 58 consumed source people only; Figure4 unopened',
             model='dH=b*c/4+g*c/4*anyjump+s*c/4*success+t*j/4+k*(j_next-j)/4+person_constant',
             interpretation='An algebraic endpoint-expression sensitivity. k is a conditional future-input association; no unique neural storage/online causal mechanism is inferred.',
             coefficient_names=NAMES,sources=[],public_requests=0,new_ingress_bytes=0)
    allcells=[]; coeff=[]; charge=0
    for name in FILES:
        by,meta=load(name); people,cells=extract(name,by)
        charge+=meta['charge'];allcells+=cells
        B=np.array([p['beta'] for p in people]);N=np.array([p['naive'] for p in people]);n=len(B)
        boot=B[rng.integers(n,size=(4000,n))].mean(axis=1)
        bn=N[rng.integers(n,size=(4000,n))].mean(axis=1)
        summary={k:(dict(identified=False,reason='All success regressor values are zero; no success trials in this source.')
                    if i==3 and all(not np.any(p['X'][:,3]) for p in people) else
                    dict(identified=True,estimate=float(B[:,i].mean()),bootstrap=ci(boot[:,i]))) for i,k in enumerate(NAMES)}
        records=[]
        # Prespecified restrictions: success/task-error versus intervention/task-error.
        modelcols={'success_task_error':[0,1,3,4,5],'intervention_task_error':[0,1,2,4,5],
                   'full_source_diagnostic':[0,1,2,3,4,5]}
        for label,cols in modelcols.items():
            losses=[]
            for test in range(n):
                # Equal-person fits, each person centered (the constant is a nuisance only).
                xx=[];yy=[]
                for q,p in enumerate(people):
                    if q==test: continue
                    x=p['X'][:,cols]; y=p['Y']
                    x=x[:,1:]-x[:,1:].mean(axis=0);y=y-y.mean()
                    xx.append(x/np.sqrt(len(y))); yy.append(y/np.sqrt(len(y)))
                fit=np.linalg.lstsq(np.vstack(xx),np.concatenate(yy),rcond=None)[0]
                x=people[test]['X'][:,cols][:,1:]; y=people[test]['Y']
                pred=dot(x-x.mean(axis=0),fit)
                losses.append(float(np.mean((y-y.mean()-pred)**2)))
            records.append(dict(model=label,columns=[NAMES[i] for i in cols],
                                leave_person_out_centered_MSE=float(np.mean(losses)),per_person_MSE=losses))
        src=dict(source=name,metadata=meta,n_transitions=sum(len(p['Y']) for p in people),
                 per_person=[dict(person=p['person'],n=len(p['Y']),rank=p['rank'],condition_number=p['condition_number'],
                     rejected=p['rejected'],coefficient=p['beta'].tolist(),naive_coefficient=p['naive'].tolist()) for p in people],
                 coefficients=summary,naive_task_error=dict(estimate=float(N[:,4].mean()),bootstrap=ci(bn[:,4])),
                 model_comparison=records)
        # Observed endpoint convention (future jump averaged to zero): source c4 predicted condition magnitudes.
        conds={'No Jump':[0,-1,0,0,0,0],'Jump In Place':[0,-1,-1,0,0,0],
               'Jump To':[0,-1,-1,-1,-1,1],'Jump Away':[0,-1,-1,0,1,-1]}
        src['predicted_c4_signed_adaptation']={k:dict(estimate=float(dot(B.mean(axis=0),v)),bootstrap=ci(dot(boot,v)),
            actual_input_support=(k=='No Jump' or (name=='task_success_fig3.csv') or (name=='tsay_TE_SPE.csv' and k=='Jump To'))) for k,v in conds.items()}
        out['sources'].append(src)
        for p in people:
            coeff.append(dict(source=name,person=p['person'],**dict(zip(NAMES,p['beta'].tolist()))))
    with (HERE/'SOURCE_CELLS.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(allcells[0]));w.writeheader();w.writerows(allcells)
    with (HERE/'SOURCE_COEFFICIENTS.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(coeff[0]));w.writeheader();w.writerows(coeff)
    out['charged_additional_read_decoded_hash_bytes']=charge
    out['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    (HERE/'SOURCE_ANALYSIS.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(created_utc=out['created_utc'],charge=charge,peak_rss=out['peak_rss_bytes'],
                         sources=[{k:s[k] for k in ('source','n_transitions','coefficients','naive_task_error','predicted_c4_signed_adaptation')} for s in out['sources']]),indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=1): main()
