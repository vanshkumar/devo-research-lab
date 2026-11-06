"""Independent finite reconstruction. No author program is imported or executed."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import csv
import hashlib
import io
import json
import math
import resource
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
AUTHOR = ROOT / 'lab/tasks/social-participation-2026-10-31'
READS = []
Q_NAMES = ['none_recorded','one_green','one_pink','both_green_first','both_pink_first']
MODELS = ['marginal','expression','primacy','cancellation']

def read(path):
    p = Path(path)
    assert p.stat().st_size < 2_000_000, str(p)
    b = p.read_bytes()
    READS.append({'path':str(p.relative_to(ROOT)), 'bytes':len(b), 'sha256':hashlib.sha256(b).hexdigest()})
    return b

def jread(path):
    return json.loads(read(path))

def save(name, value):
    (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def csvread(path):
    return list(csv.DictReader(io.StringIO(read(path).decode())))

def average(xs):
    return math.fsum(xs)/len(xs)

def reconstruct():
    raw = csvread(ROOT/'data/social_learning/data_primacy.csv')
    result = []
    for ix,r in enumerate(raw,2):
        t = r['treatment']
        ref = r['demo_color_2' if t=='C2' else 'demo_color_1']
        assert ref in ('g','p')
        if t=='T': assert set((r['demo_color_1'],r['demo_color_2']))=={'g','p'}
        else: assert r['demo_color_1' if t=='C2' else 'demo_color_2']=='NA'
        first, second, mate = (r[k] for k in ('color_court_1','color_court_2','test_color'))
        assert first in ('g','p','NA') and second in ('g','p','NA') and mate in ('g','p','NA')
        assert second=='NA' or (first!='NA' and first!=second)
        q = 0 if first=='NA' else (1 if first=='g' else 2)+(2 if second!='NA' else 0)
        m = {'NA':0,'g':1,'p':2}[mate]
        result.append({'row':ix,'date':r['date'],'device':r['device'],'t':t,
            'z':1 if ref=='g' else -1,'A':int(first!='NA'),'F':int(first=='g'),
            'f':{'g':1,'p':-1,'NA':0}[first], 'D':int(second!='NA'),'Q':q,
            'B':int(m>0),'Y':int(m==1),'M':m,'eligible':int(second!='NA' and m>0),
            'copy':None if not m else int(mate==ref),
            'first_match':None if first=='NA' else int(first==ref)})
    return result

def terms(t,z,q,model,stage,eligible_only=False):
    # Features are built by their scientific definitions, then matched to saved names.
    f = 1 if q in (1,3) else -1 if q in (2,4) else 0
    v = {'intercept':1.0,'T':float(t=='T'),'C2':float(t=='C2')}
    if model!='marginal' and not eligible_only:
        if stage=='F': v['reference_green_sign']=z
        if stage=='D': v.update(first_green_sign=f,first_matches_reference_sign=z*f)
        if stage in ('B','Y'):
            v.update({Q_NAMES[k]:float(q==k) for k in range(1,5)})
        if stage=='B': v['first_matches_reference_sign']=z*f
    if stage=='Y' and model in ('primacy','cancellation'):
        v['shared_nonnegative_copy_gain']=z*int(model=='primacy' or t!='T')
    return v

def probability(t,z,q,model,stage,fit,eligible_only=False):
    v=terms(t,z,q,model,stage,eligible_only)
    assert set(v)==set(fit['coefficient_names'])
    eta=math.fsum(v[k]*c for k,c in zip(fit['coefficient_names'],fit['coefficients']))
    return 1/(1+math.exp(-eta))

def table(t,z,model,fits):
    cells=[]
    for q in range(5):
        ps={s:probability(t,z,q,model,s,fits[s]) for s in ('A','F','D','B','Y')}
        court=(1-ps['A']) if q==0 else ps['A']*(ps['F'] if q in (1,3) else 1-ps['F'])*(ps['D'] if q>=3 else 1-ps['D'])
        cells.extend([court*(1-ps['B']),court*ps['B']*ps['Y'],court*ps['B']*(1-ps['Y'])])
    return cells

def bern_loss(p,y):
    return -math.log(p if y else 1-p)

def score(r,model,fits):
    t,z,q=r['t'],r['z'],r['Q']
    ps={s:probability(t,z,q,model,s,fits[s]) for s in fits}
    parts={s:bern_loss(ps[s],r[s]) if (s not in ('F','D') or r['A']) and (s!='Y' or r['B']) else 0.0 for s in fits}
    cells=table(t,z,model,fits)
    ll=-math.log(cells[3*q+r['M']])
    assert abs(sum(cells)-1)<1e-12
    assert abs(ll-math.fsum(parts.values()))<1e-11
    pg=(cells[10]+cells[13])/math.fsum(cells[k] for k in (10,11,13,14))
    return dict(joint=ll,Y=parts['Y'],courtship=parts['A']+parts['F']+parts['D'],mating=parts['B'],participation=math.fsum(parts[s] for s in ('A','F','D','B')),Y_integrated=bern_loss(pg,r['Y']))

def summarize(rows,losses,eligible_only=False):
    masks={'eligible_choice':('Y',lambda r:True),'T_eligible_choice':('Y',lambda r:r['t']=='T')} if eligible_only else {
        'joint':('joint',lambda r:True),'courtship':('courtship',lambda r:True),
        'mating':('mating',lambda r:True),'participation':('participation',lambda r:True),
        'mating_choice':('Y',lambda r:r['B']), 'eligible_choice':('Y',lambda r:r['eligible']),
        'T_eligible_choice':('Y',lambda r:r['eligible'] and r['t']=='T'),
        'eligible_integrated_choice':('Y_integrated',lambda r:r['eligible']),
        'T_eligible_integrated_choice':('Y_integrated',lambda r:r['eligible'] and r['t']=='T')}
    dates=sorted({r['date'] for r in rows})
    draws=np.random.default_rng(20261031).integers(len(dates),size=(5000,len(dates)))
    metrics={}
    for m in losses:
        metrics[m]={}
        for name,(key,fn) in masks.items():
            take=[i for i,r in enumerate(rows) if fn(r)]
            bydate=[[i for i in take if rows[i]['date']==d] for d in dates]
            metrics[m][name]={'n':len(take),'dates':sum(bool(b) for b in bydate),'nll':average([losses[m][i][key] for i in take]),'equal_date_nll':average([average([losses[m][i][key] for i in b]) for b in bydate if b])}
    pairs=[('marginal','primacy'),('cancellation','primacy')] if eligible_only else [('marginal','expression'),('expression','primacy'),('cancellation','primacy'),('expression','cancellation')]
    contrasts=[]
    for base,m in pairs:
        for name,(key,fn) in masks.items():
            bydate=[[i for i,r in enumerate(rows) if fn(r) and r['date']==d] for d in dates]
            sums=np.array([math.fsum(losses[base][i][key]-losses[m][i][key] for i in b) for b in bydate])
            ns=np.array([len(b) for b in bydate])
            den=ns[draws].sum(axis=1)
            vals=sums[draws].sum(axis=1)[den>0]/den[den>0]
            contrasts.append(dict(baseline=base,model=m,metric=name,gain_nat=float(sums.sum()/ns.sum()),date_bootstrap_95=np.quantile(vals,[.025,.975]).tolist(),equal_date_gain=float((sums[ns>0]/ns[ns>0]).mean()),n=int(ns.sum()),dates_with_observations=int(sum(ns>0))))
    return {'aggregate':metrics,'contrasts':contrasts}

def max_compare(a,b):
    if isinstance(a,dict): return max([max_compare(v,b[k]) for k,v in a.items()]+[0])
    if isinstance(a,list):
        assert len(a)==len(b)
        return max([max_compare(x,y) for x,y in zip(a,b)]+[0])
    if isinstance(a,(int,float)) and not isinstance(a,bool): return abs(a-b)
    assert a==b,(a,b)
    return 0

def main():
    rows=reconstruct()
    dates=sorted({r['date'] for r in rows})
    by_t={t:{'n':sum(r['t']==t for r in rows),'eligible':sum(r['t']==t and r['eligible'] for r in rows),'copy':sum(r['t']==t and r['eligible'] and r['copy'] for r in rows),'joint_counts':[sum(r['t']==t and 3*r['Q']+r['M']==j for r in rows) for j in range(15)]} for t in ('T','C1','C2')}
    counts={'n':len(rows),'dates':len(dates),'any_courtship':sum(r['A'] for r in rows),'two_courters':sum(r['D'] for r in rows),'matings':sum(r['B'] for r in rows),'eligible':sum(r['eligible'] for r in rows),'mating_without_courtship_rows':[r['row'] for r in rows if r['B'] and not r['A']],'single_courter_opposite_mating_rows':[r['row'] for r in rows if r['A'] and not r['D'] and r['B'] and r['F']!=r['Y']],'treatments':by_t}
    assert [(by_t[t]['eligible'],by_t[t]['copy']) for t in ('T','C1','C2')]==[(64,40),(74,46),(67,42)]
    with (OUT/'ROWS.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    save('COUNTS.json',counts)
    # Only now read the author row table and fold coefficients for comparison/scoring.
    old=csvread(AUTHOR/'reconstructed.csv')
    row_errors=[]
    for a,b in zip(rows,old):
        for k,v in a.items():
            if ('' if v is None else str(v))!=b[k]: row_errors.append([a['row'],k,v,b[k]])
    assert len(old)==len(rows) and not row_errors,row_errors[:3]
    split=jread(AUTHOR/'SPLIT.json')
    for fold in split['folds']:
        n=sum(r['date']==fold['held_date'] for r in rows)
        assert fold['test_n']==n and fold['train_n']==len(rows)-n
    cv=jread(AUTHOR/'CV_FITS.json')
    losses={m:[None]*len(rows) for m in MODELS}
    train_count_errors=[]
    opt=[]
    for fold in cv:
        m,d,fits=fold['model'],fold['held_date'],fold['fits']
        train=[r for r in rows if r['date']!=d]
        for s,fit in fits.items():
            n=sum((r['A'] if s in ('F','D') else r['B'] if s=='Y' else True) for r in train)
            if n!=fit['n']: train_count_errors.append([m,d,s,n,fit['n']])
            opt.append({'model':m,'date':d,'stage':s,'success':fit['success'],'gradient':fit['projected_gradient_max']})
        for i,r in enumerate(rows):
            if r['date']==d: losses[m][i]=score(r,m,fits)
    assert not train_count_errors
    computed=summarize(rows,losses)
    save('FIXED_COEFFICIENT_RECONSTRUCTION.json',computed)
    saved_losses=csvread(AUTHOR/'CV_LOSSES.csv')
    print('SAVED_LOSS_SCHEMA',list(saved_losses[0]))
    # Save our individual losses independent of the author's CSV conventions.
    lrows=[]
    for m in MODELS:
        for r,ls in zip(rows,losses[m]): lrows.append(dict(row=r['row'],date=r['date'],model=m,**ls))
    with (OUT/'LOSSES.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(lrows[0]));w.writeheader();w.writerows(lrows)
    full=jread(AUTHOR/'FULL_FITS.json')
    compact=[]
    for t in ('T','C1','C2'):
        for z in (-1,1): compact.append({'t':t,'z':z,'models':{m:table(t,z,m,full[m]) for m in MODELS}})
    save('COMPACT_LAWS.json',compact)
    saved=jread(AUTHOR/'FULL_JOINT_PREDICTIONS.json')
    fullerr=max(abs(a-b) for context in saved['contexts'] for m in MODELS for a,b in zip(table(context['t'],1 if context['reference_color']=='green' else -1,m,full[m]),context['models'][m]))
    onlyrows=[r for r in rows if r['eligible']]
    onlyloss={m:[None]*len(onlyrows) for m in ('marginal','primacy','cancellation')}
    for fold in jread(AUTHOR/'ELIGIBLE_ONLY_FITS.json'):
        m,d=fold['model'],fold['held_date'];fit=fold['fits']['Y']
        for i,r in enumerate(onlyrows):
            if r['date']==d: onlyloss[m][i]={'Y':bern_loss(probability(r['t'],r['z'],r['Q'],m,'Y',fit,True),r['Y'])}
    eligible=summarize(onlyrows,onlyloss,True)
    save('ELIGIBLE_ONLY_RECONSTRUCTION.json',eligible)
    comp=jread(AUTHOR/'COMPARISON.json')
    print('COMPARISON_SCHEMA',list(comp))
    save('PROVENANCE_AND_NUMERICS.json',{'fixed_coefficient_not_refitting':True,'row_join_mismatches':row_errors,'fold_train_count_errors':train_count_errors,'full_law_max_error':fullerr,'original_empirical_cv_fit_count':len(opt),'original_empirical_cv_non_success':[o for o in opt if not o['success']],'max_projected_gradient':max(o['gradient'] for o in opt),'author_comparison_keys':list(comp)})
    save('READS_RECONSTRUCTION.json',{'reads':READS,'read_hash_bytes':sum(x['bytes'] for x in READS),'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'completed_utc':datetime.now(timezone.utc).isoformat()})
    print(json.dumps({'counts':counts,'full_law_error':fullerr,'main_contrasts':[c for c in computed['contrasts'] if c['model']=='primacy' and c['metric'] in ('joint','eligible_choice','T_eligible_choice')],'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},indent=2))

if __name__=='__main__': main()
