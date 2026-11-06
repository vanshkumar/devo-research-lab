"""Independent offline source reconstruction; never imports author analysis code.

Figure4 is input-only: non-allowlisted strings are discarded before conversion.
Run only under a separately authorized raw-read/resource allowance.
"""
import os
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
            'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import csv
import hashlib
import io
import json
import math
import platform
import resource
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits, threadpool_info

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUTHOR = ROOT / 'lab/tasks/motor-teaching-transfer-2026-10-31'
SOURCE = ROOT / 'sources/learning_intervention_feasibility_2026-10-28'
FILES = ('tsay_TE_SPE.csv', 'tsay_controljump.csv', 'task_success_fig3.csv')
READS = []
RNG = np.random.default_rng(202611010017)

def now():
    return datetime.now(timezone.utc).isoformat()

def read(path, factor=4):
    body = path.read_bytes()
    READS.append(dict(path=str(path.relative_to(ROOT)), physical_bytes=len(body),
                      charge_factor=factor, charged_bytes=factor*len(body)))
    return body

def record(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')

def load_json(path):
    return json.loads(read(path))

def number(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return float('nan')

def cell(row):
    return row['c'], row['j'], row['f']

def core(row, tsay):
    t = row['t']
    return t > 100 and (t-101) % 181 < 180 if tsay else 104 <= t <= 903

def portion(row, tsay):
    return (row['t']-101)//181 if tsay else (row['t']-104)//200

def valid(row):
    return not row['bad'] and np.isfinite(row['h']) and abs(row['h']) <= 90

def decode(name, expected):
    body = read(SOURCE/name, 8)
    sha = hashlib.sha256(body).hexdigest()
    git = hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
    assert sha == expected['sha256'] and git == expected['git_blob'], name
    tsay = name.startswith('tsay')
    reader = csv.DictReader(io.StringIO(body.decode()))
    schema = reader.fieldnames
    by = defaultdict(list)
    for full in reader:
        if tsay:
            p, t = int(full['SN']), int(full['TN'])
            c, j = number(full['clamp_size']), number(full['tgt_jump_size'])
            r = dict(p=p, t=t, c=c, j=j, f=0, h=number(full['Hand_raw']), bad=False,
                     masked=number(full['Hand']), dt=number(full['Hand_dt']),
                     diff=number(full['Hand_Diff']))
        else:
            p, t = int(full['Subject']), int(full['TrialNum'])
            jraw = number(full['TargetJump'])
            r = dict(p=p, t=t, c=number(full['ClampAngle']),
                     j=0. if jraw == .01 else jraw, f=int(jraw == .01),
                     h=number(full['HandError']), bad=number(full['FalseStart']) == 1)
        by[p].append(r)
    for p, rr in by.items():
        rr.sort(key=lambda r:r['t'])
        assert len(rr) == len(set(r['t'] for r in rr))
        assert [r['t'] for r in rr] == list(range(1, 825 if tsay else 905))
    support = sorted({cell(r) for rr in by.values() for r in rr if core(r,tsay)})
    exposures = Counter(cell(r) for rr in by.values() for r in rr if core(r,tsay))
    terminals = Counter(cell(r) for rr in by.values() for r in rr
                        if tsay and r['t'] > 100 and (r['t']-101)%181 == 180)
    meta = dict(file=name, bytes=len(body), sha256=sha, git_blob=git, pin_pass=True,
                identities=[name+':'+str(p) for p in sorted(by)], schema=schema,
                n_rows=sum(map(len, by.values())), people=len(by), cells=support,
                randomized_exposures=sum(exposures.values()),
                cells_counts=[dict(cell=k,n=v) for k,v in sorted(exposures.items())],
                terminal_cells=[dict(cell=k,n=v) for k,v in sorted(terminals.items())],
                full_trial_sequences_verified=True)
    return by, support, meta

def transitions(rr, tsay, history=False):
    out = []
    for k in range(len(rr)-1):
        a,b = rr[k:k+2]
        if b['t'] != a['t']+1 or not core(a,tsay):
            continue
        if tsay and (not core(b,tsay) or portion(a,True)!=portion(b,True)):
            continue
        if not valid(a) or not valid(b):
            continue
        if history:
            if k < 2:
                continue
            old = rr[k-2:k]
            if any(not core(r,tsay) or portion(r,tsay)!=portion(a,tsay) for r in old):
                continue
            out.append((a,b,old[1],old[0]))
        else:
            out.append((a,b))
    return out

def indicators(values, levels):
    # Independent reference convention: omit LAST cell, rather than author's first.
    return np.asarray([[float(v == z) for z in levels[:-1]] for v in values])

def cell_model(tr, support, history=False, common=False):
    if common:
        tr = [v for v in tr if v[1]['j']==0 and v[1]['f']==0 and abs(v[1]['c'])==4]
    current = indicators([cell(v[0]) for v in tr],support)
    nxt = (np.asarray([[v[1]['c']/4] for v in tr]) if common else
           indicators([cell(v[1]) for v in tr],support))
    cols = [np.ones((len(tr),1)),current,nxt]
    if history:
        for lag in (2,3):
            cols.append(indicators([cell(v[lag]) for v in tr],support))
        tsay = tr[0][0]['t'] <= 100 or len(support)==9
        block = [portion(v[0],tsay) for v in tr]
        cols.append(indicators(block, list(range(4))))
        # Explicit, fixed within-portion linear time; no outcome-derived smoothing.
        den = 180 if tsay else 200
        first = 101 if tsay else 104
        stride = 181 if tsay else 200
        cols.append(np.array([[(v[0]['t']-first)%stride/den-.5] for v in tr]))
    X = np.concatenate(cols,axis=1)
    levels = np.asarray([[v[1]['h'],v[0]['h']] for v in tr])
    coef,_,rank,singular = np.linalg.lstsq(X,levels,rcond=None)
    residual = levels-np.einsum('ni,ij->nj',X,coef)
    normal = np.einsum('ni,nj->ij',X,residual)
    return tr,X,coef,dict(n=len(tr),rank=int(rank),columns=X.shape[1],
                          full_rank=bool(rank==X.shape[1]),
                          max_normal_residual=float(np.abs(normal).max()),
                          condition_number=float(singular[0]/singular[-1]))

def channels(coef,K,retention=1.):
    # beta describes H_next - a*H_current; transformed U = C+a*N.
    beta = coef[:,0]-retention*coef[:,1]
    C = np.r_[beta[1:K],0.]
    N = np.r_[beta[K:2*K-1],0.]
    return C,N,C+retention*N

def effects(values,support):
    out = {}
    idx = {c:k for k,c in enumerate(support)}
    for label,pos in [('No Jump',(4.,0.,0)),('Jump To',(4.,4.,0)),
                      ('Jump Away',(4.,-4.,0)),('Jump Past',(4.,8.,0)),
                      ('Jump In Place',(4.,0.,1))]:
        neg=(-pos[0],-pos[1],pos[2])
        if pos in idx and neg in idx:
            out[label] = float((values[idx[neg]]-values[idx[pos]])/2)
    return out

def summary(v):
    v=np.asarray(v)
    means=v.mean(axis=0)
    return dict(people=len(v),stationary=float(means[0]),jump_to=float(means[1]),
                ratio=float(means[1]/means[0]),
                suppression=float(means[0]-means[1]),
                median_person_stationary=float(np.median(v[:,0])),
                median_person_jump_to=float(np.median(v[:,1])),
                nonpositive_stationary_people=int(np.sum(v[:,0]<=0)),
                per_person=v.tolist())

def comparison(a,f,boot=True):
    a,f=np.asarray(a),np.asarray(f)
    qa=float(a[:,1].mean()/a[:,0].mean())
    qf=float(f[:,1].mean()/f[:,0].mean())
    predictions=[]
    for k in range(len(f)):
        train=(f.sum(axis=0)-f[k])/(len(f)-1)
        predictions.append([float(f[k,1]),float(train[0]*qa),float(train[1])])
    pred=np.asarray(predictions)
    lt=(pred[:,0]-pred[:,1])**2
    ll=(pred[:,0]-pred[:,2])**2
    out=dict(Tsay_ratio=qa,Figure3_ratio=qf,ratio_shift=qf-qa,
             stationary_calibrated_residual=float(f[:,1].mean()-qa*f[:,0].mean()),
             Tsay_MSE=float(lt.mean()),Figure3_LOO_MSE=float(ll.mean()),
             paired_MSE_gain=float((lt-ll).mean()),
             loo_rows_observed_Tsay_F3=predictions)
    if boot:
        am=a[RNG.integers(len(a),size=(6000,len(a)))].mean(axis=1)
        fm=f[RNG.integers(len(f),size=(6000,len(f)))].mean(axis=1)
        shifts=fm[:,1]/fm[:,0]-am[:,1]/am[:,0]
        out['conditional_bootstrap_shift95']=np.quantile(shifts,[.025,.975]).tolist()
    return out

def reconstruct_sources(data, author):
    results=[]
    errors=[]
    for si,(name,by,support,meta) in enumerate(data):
        tsay=name.startswith('tsay')
        people=[]
        for p,rr in sorted(by.items()):
            tr=transitions(rr,tsay)
            _,X,coef,stats=cell_model(tr,support)
            C,N,U=channels(coef,len(support))
            rec=dict(person=p,**stats,current=C.tolist(),next=N.tolist(),current_plus_next=U.tolist(),
                     effects={c:effects(v,support) for c,v in
                              [('current',C),('next',N),('current_plus_next',U)]})
            saved=next(v for v in author['sources'][si]['people'] if v['person']==p)
            assert saved['n']==len(tr)
            for label,v in [('current',C),('next',N),('current_plus_next',U)]:
                ref=np.asarray(saved[label])
                errors.append(float(np.max(abs((ref-ref[-1])-v))))
            people.append(rec)
        results.append(dict(source=name,meta=meta,people=people,
                            n_transitions=sum(p['n'] for p in people)))
    matched={}
    for channel in ('current','current_plus_next'):
        groups=[]
        for si in (0,2):
            v=[[p['effects'][channel][c] for c in ('No Jump','Jump To')] for p in results[si]['people']]
            groups.append(v)
        matched[channel]=comparison(*groups)
        saved=author['matched_transfer'][channel]
        for k,old in [('Tsay_ratio','Tsay_ratio'),('Figure3_ratio','Figure3_ratio'),
                      ('Tsay_MSE','Tsay_transfer_MSE'),('Figure3_LOO_MSE','lab_intervention_MSE')]:
            errors.append(abs(matched[channel][k]-saved[old]))
    return dict(created_utc=now(),sources=results,matched=matched,
                max_saved_coefficient_contrast_or_scalar_error=max(errors),
                independent_implementation=True,author_helpers_imported_or_executed=False)

def measurement_controls(data, saved):
    out=[]
    error=0.
    for si in (0,2):
        name,by,support,meta=data[si]
        tsay=si==0
        definitions=[('raw_mean','h','mean'),('raw_median','h','median')]
        if tsay:
            definitions += [('masked_mean','masked','mean'),('dt_mean','dt','mean'),
                            ('dt_median','dt','median'),('supplied_diff_median','diff','median')]
        values={label:[] for label,_,_ in definitions}
        diff_error=0.
        for p,rr in sorted(by.items()):
            for label,field,agg in definitions:
                bins=defaultdict(list)
                # Preserve invalid measurements in chronology; never bridge gaps.
                for k in range(len(rr)-1):
                    a,b=rr[k:k+2]
                    if not core(a,tsay) or (tsay and (not core(b,True) or portion(a,True)!=portion(b,True))):
                        continue
                    if abs(a['c'])!=4 or a['f'] or a['j'] not in (0,a['c']):
                        continue
                    if field=='diff':
                        y=a['diff']
                        if np.isfinite([a['dt'],b['dt'],y]).all():
                            diff_error=max(diff_error,abs(y-(b['dt']-a['dt'])))
                    else:
                        if not np.isfinite([a[field],b[field]]).all() or max(abs(a[field]),abs(b[field]))>90:
                            continue
                        if field=='h' and (a['bad'] or b['bad']):
                            continue
                        y=b[field]-a[field]
                    if np.isfinite(y):
                        bins[(int(np.sign(a['c'])),a['j']==a['c'])].append(-np.sign(a['c'])*y)
                v=[]
                for jump in (False,True):
                    v.append(float(np.mean([getattr(np,agg)(bins[(sgn,jump)]) for sgn in (-1,1)])))
                values[label].append(v)
        methods={k:summary(v) for k,v in values.items()}
        old=next(s for s in saved['sources'] if s['source']==name)
        for k,v in values.items():
            error=max(error,float(np.max(abs(np.asarray(v)-np.asarray(old['methods'][k]['per_person'])))))
        out.append(dict(source=name,methods=methods,supplied_difference_max_error=diff_error))
    return dict(created_utc=now(),sources=out,max_reconstructed_saved_person_effect_error=error,
                literal_R_mask_reconstruction='Source definition inspected; author literal/intended mask estimates inherited, raw/median/masked/dt/diff independently rebuilt.')

def contrary(data):
    all_retention=defaultdict(list)
    probe=[]
    for si in (0,2):
        name,by,support,meta=data[si]
        tsay=si==0
        for hist in (False,True):
            estimates={a:[] for a in (0.,.25,.5,.75,.9,.95,1.)}
            stats=[]
            for p,rr in sorted(by.items()):
                tr=transitions(rr,tsay,history=hist)
                _,X,coef,st=cell_model(tr,support,history=hist)
                stats.append(dict(person=p,**st))
                for a in estimates:
                    _,_,U=channels(coef,len(support),a)
                    effect=effects(U,support)
                    estimates[a].append([effect['No Jump'],effect['Jump To']])
            for a,v in estimates.items():
                all_retention[(hist,a)].append(dict(source=name,**summary(v),design=stats))
        people=[]
        for p,rr in sorted(by.items()):
            tr=transitions(rr,tsay,history=True)
            selected,X,coef,st=cell_model(tr,support,history=True,common=True)
            C=np.r_[coef[1:len(support),0],0.]
            effect=effects(C,support)
            counts=Counter(cell(t[0]) for t in selected)
            people.append(dict(person=p,**st,effects=effect,
                               min_current_cell_count=min(counts.get(c,0) for c in support),
                               current_cell_counts=[dict(cell=c,n=counts.get(c,0)) for c in support]))
        probe.append(dict(source=name,people=people,
                          summary=summary([[p['effects'][c] for c in ('No Jump','Jump To')] for p in people])))
    sweep=[]
    for (hist,a),groups in all_retention.items():
        sweep.append(dict(history_adjusted=hist,retention=a,groups=groups,
                          comparison=comparison(groups[0]['per_person'],groups[1]['per_person'],False)))
    common=comparison(probe[0]['summary']['per_person'],probe[1]['summary']['per_person'])
    return dict(created_utc=now(),frozen_plan_sha256=hashlib.sha256(read(HERE/'PLAN.md')).hexdigest(),
                retention_sweep=sweep,stationary_next_endpoint_groups=probe,
                stationary_next_endpoint_comparison=common,
                assumptions='Conditional linear endpoint model; prior two cell and fixed time effects do not certify exchangeability, actual perception or arbitrary state-dependent observation invariance.')

def prescription(reconstruction,saved):
    sigma,g,t=saved['fit']['parameters']
    rows=[]
    for src in reconstruction['sources'][:2]:
        support=[tuple(c) for c in src['meta']['cells']]
        m=np.mean([p['current_plus_next'] for p in src['people']],axis=0)
        idx={c:k for k,c in enumerate(support)}
        A=effects(m,support)['No Jump']
        for c,j,f in support:
            if f or c<0 or (c==0 and j<=0) or j==0:
                continue
            observed=(m[idx[(c,j,f)]]-m[idx[(-c,-j,f)]])/2
            predicted=t*j if c==0 else -(g*A-c*t)*math.exp(-j*j/(2*sigma*sigma))+t*(j-c)
            rows.append(dict(clamp=c,jump=j,A4=A,observed_signed=float(observed),fitted_signed=float(predicted)))
    assert len(rows)==len(saved['source_rows'])
    error=max(abs(r[k]-s[k]) for r,s in zip(rows,saved['source_rows']) for k in r)
    sse=sum((r['observed_signed']-r['fitted_signed'])**2 for r in rows)
    src=reconstruction['sources'][2]
    base=float(np.mean([p['effects']['current_plus_next']['No Jump'] for p in src['people']]))
    observed=float(np.mean([p['effects']['current_plus_next']['Jump To'] for p in src['people']]))
    pred=(g*base-4*t)*math.exp(-16/(2*sigma*sigma))
    # Conditional linear calibration at the saved sigma; no nonlinear refit claim.
    design=[];response=[]
    for r in rows:
        c,j,A=r['clamp'],r['jump'],r['A4']
        e=math.exp(-j*j/(2*sigma*sigma))
        design.append([0. if c==0 else -A*e, j if c==0 else c*e+j-c])
        response.append(r['observed_signed'])
    gt=np.linalg.lstsq(np.asarray(design),np.asarray(response),rcond=None)[0]
    return dict(created_utc=now(),parameters_inherited=[sigma,g,t],independent_nonlinear_refit=False,
                independent_linear_fit_at_saved_sigma=gt.tolist(),source_rows=rows,
                source_SSE=sse,max_saved_source_row_error=error,
                saved_SSE_error=abs(sse-saved['fit']['SSE']),
                Figure3=dict(stationary=base,jump_to_observed=observed,jump_to_predicted=pred,
                             observed_ratio=observed/base,predicted_ratio=pred/base),
                identification='Finite source fits calibrate the specified Gaussian/linear function at source geometry, conditional on stationary amplitudes and endpoint model. They do not identify unseen clamp amplitudes, a target-size gate or a unique mechanism.')

def support_witness(data,expected,pr,reconstruction):
    name='task_success_fig4.csv'
    body=read(SOURCE/name,8)
    assert hashlib.sha256(body).hexdigest()==expected['sha256']
    assert hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==expected['git_blob']
    reader=csv.DictReader(io.StringIO(body.decode()))
    schema=reader.fieldnames
    allowed={'Subject','TrialNum','ClampAngle','TargetJump','TrialLabel','TgtSize','TgtAngle'}
    by=defaultdict(list);counts=Counter()
    for full in reader:
        kept={k:v for k,v in full.items() if k in allowed}
        del full
        # No discarded string is converted or retained in an analysis record.
        p=int(kept['Subject']);tn=int(kept['TrialNum']);by[p].append(tn)
        if not 104<=tn<=967:
            continue
        c=float(kept['ClampAngle']);jr=float(kept['TargetJump']);label=kept['TrialLabel']
        assert label in ('Miss','Hit','Jump To')
        assert jr == (-c if label=='Jump To' else 0)
        counts[(c,c if label=='Jump To' else 0.,label,kept['TgtSize'])]+=1
    assert len(by)==42 and all(v==list(range(1,969)) for v in by.values())
    sx=[]
    for name,rows,cells,meta in data:
        for c,j,f in cells:
            sx.append([c/4,j/4,c/4*bool(j or f),c/4*bool(c and j==c)])
    tx=[]
    for c,j,label,size in counts:
        tx.append([c/4,j/4,c/4*bool(j),c/4*bool(c and j==c),c/4*(label=='Hit')])
    sx=np.asarray(sx);tx=np.asarray(tx)
    ranks=dict(source_base=int(np.linalg.matrix_rank(sx)),
               source_with_size=int(np.linalg.matrix_rank(np.c_[sx,np.zeros(len(sx))])),
               target_base=int(np.linalg.matrix_rank(tx[:,:4])),
               target_with_size=int(np.linalg.matrix_rank(tx)),
               target_Hit_exposures=sum(n for (c,j,label,size),n in counts.items() if label=='Hit'))
    grid=sorted({c for _,_,cells,_ in data for c,_,_ in cells}|{c for c,_,_,_ in counts})
    curves={str(tau):[math.tanh(c/tau)/math.tanh(4/tau) for c in grid] for tau in (1.,4.,16.)}
    source_clamps=sorted({c for _,_,cells,_ in data for c,_,_ in cells})
    target_clamps=sorted({c for c,_,_,_ in counts})
    ds=max(abs(curves['1.0'][grid.index(c)]-curves['16.0'][grid.index(c)]) for c in source_clamps)
    dt=max(abs(curves['1.0'][grid.index(c)]-curves['16.0'][grid.index(c)]) for c in target_clamps)
    sigma,g,t=pr['parameters_inherited'];A=pr['Figure3']['stationary']
    witnesses=[]
    for tau in (1.,4.,16.):
        for c in sorted({abs(c) for c in target_clamps}):
            amplitude=A*math.tanh(c/tau)/math.tanh(4/tau)
            jump=(g*amplitude-c*t)*math.exp(-c*c/(2*sigma*sigma))
            for extension in ('motion_gate','shared_success_gate'):
                for label in ('Miss','Hit','Jump To'):
                    response=amplitude if label=='Miss' or (label=='Hit' and extension=='motion_gate') else jump
                    witnesses.append(dict(tau=tau,clamp_magnitude=c,extension=extension,condition=label,
                                          predicted_adaptation_degrees=response))
    with (HERE/'SOURCE_COMPATIBLE_WITNESSES.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(witnesses[0]));writer.writeheader();writer.writerows(witnesses)
    old=list(csv.DictReader(io.StringIO(read(AUTHOR/'SOURCE_COMPATIBLE_TARGET_WITNESSES.csv').decode())))
    error=max(abs(float(o['predicted_adaptation_degrees'])-r['predicted_adaptation_degrees']) for o,r in zip(old,witnesses))
    return dict(created_utc=now(),Figure4_input_sha256=expected['sha256'],input_only_ids=sorted(by),
                target_exposures=sum(counts.values()),target_cells=[dict(clamp=c,jump=j,label=l,size=s,n=n) for (c,j,l,s),n in sorted(counts.items())],
                retained_fields=sorted(allowed),discarded_before_conversion=sorted(set(schema)-allowed),
                target_outcome_numeric_values_decoded=0,target_outcome_statistics=0,
                optional210_opened=False,source_clamps=source_clamps,target_clamps=target_clamps,
                rank_witness=ranks,curve_grid=grid,curves=curves,
                max_source_curve_disagreement=ds,max_target_curve_disagreement=dt,
                source_target_size_feature_identically_zero=True,
                witness_rows=len(witnesses),max_author_witness_error=error,
                qualification='Nonunique absolute extrapolation without shape/size assumptions; a specified normalized hypothesis can still be tested. A zero unidentified source coefficient is not an estimate of absence.')

def pins_and_warnings():
    freeze=load_json(AUTHOR/'SOURCE_ONLY_FREEZE.json')
    frozen=[]
    for path,sha in freeze['files'].items():
        found=hashlib.sha256(read(AUTHOR/path,2)).hexdigest()
        frozen.append(dict(path=path,pass_=found==sha))
    manifest=load_json(AUTHOR/'ARTIFACT_MANIFEST.json')
    stable=[]
    for path,pin in manifest['files'].items():
        body=read(AUTHOR/path,2)
        stable.append(dict(path=path,pass_=len(body)==pin['bytes'] and hashlib.sha256(body).hexdigest()==pin['sha256']))
    initial=load_json(AUTHOR/'SOURCE_ANALYSIS_INITIAL_WARNINGS.json')
    final=load_json(AUTHOR/'SOURCE_ANALYSIS.json')
    diffs=[]
    for a,b in zip(initial['sources'],final['sources']):
        diffs += [abs(x-y) for p,q in zip(a['per_person'],b['per_person']) for x,y in zip(p['coefficient'],q['coefficient'])]
        diffs += [abs(p['leave_person_out_centered_MSE']-q['leave_person_out_centered_MSE']) for p,q in zip(a['model_comparison'],b['model_comparison'])]
        diffs += [abs(a['predicted_c4_signed_adaptation'][k]['estimate']-b['predicted_c4_signed_adaptation'][k]['estimate']) for k in a['predicted_c4_signed_adaptation']]
    code=ROOT/'campaigns/target_event_carryover_2026-10-28/audits/source_measurement/code/TargetJumpModels.R'
    codebody=read(code,4)
    expected=load_json(AUTHOR/'SOURCE_MANIFEST.json')['code_prescription']
    codepass=hashlib.sha256(codebody).hexdigest()==expected['sha256']
    assert all(p['pass_'] for p in frozen+stable) and codepass
    return dict(created_utc=now(),source_only_freeze=frozen,stable_author_artifacts=stable,
                published_code_pin_pass=codepass,initial_final_max_numeric_error=max(diffs),
                saved_TsayB_success_identified=final['sources'][1]['coefficients']['clamp_x_success']['identified'],
                warning_note='Saved first/final finite outputs agree. This does not independently observe historical stderr; current reviewer warnings captured separately.')

def main():
    started=now()
    manifest=load_json(AUTHOR/'SOURCE_MANIFEST.json')
    expected={v['local']:v for v in manifest['reused_pinned_csvs']}
    data=[]
    for name in FILES:
        by,cells,meta=decode(name,expected[name]);data.append((name,by,cells,meta))
    endpoint=load_json(AUTHOR/'ENDPOINT_CONTROL.json')
    reconstructed=reconstruct_sources(data,endpoint)
    record('RECONSTRUCTION.json',reconstructed)
    print(json.dumps(dict(stage='independent raw reconstruction',transitions=[s['n_transitions'] for s in reconstructed['sources']],
                          matched=reconstructed['matched']['current_plus_next'],
                          max_error=reconstructed['max_saved_coefficient_contrast_or_scalar_error']),allow_nan=False),flush=True)
    controls=measurement_controls(data,load_json(AUTHOR/'MEASUREMENT_SENSITIVITY.json'))
    record('MEASUREMENT.json',controls)
    adversarial=contrary(data);record('CONTRARY.json',adversarial)
    print(json.dumps(dict(stage='frozen contrary tests',stationary_endpoint=adversarial['stationary_next_endpoint_comparison'],
                          retention_shift_range=[min(r['comparison']['ratio_shift'] for r in adversarial['retention_sweep']),
                                                 max(r['comparison']['ratio_shift'] for r in adversarial['retention_sweep'])])),flush=True)
    pr=prescription(reconstructed,load_json(AUTHOR/'PRESCRIPTION_CHECK.json'));record('PRESCRIPTION.json',pr)
    support=support_witness(data,expected['task_success_fig4.csv'],pr,reconstructed);record('SUPPORT.json',support)
    pins=pins_and_warnings();record('PINS.json',pins)
    record('RUN.json',dict(started_utc=started,finished_utc=now(),python=platform.python_version(),numpy=np.__version__,
                          threadpools=threadpool_info(),jobs_running_at_exit=0,read_passes=READS,
                          charged_script_read_decode_hash_bytes=sum(r['charged_bytes'] for r in READS),
                          raw_source_hashes=[d[3] for d in data],peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    print(json.dumps(dict(stage='complete',source_SSE=pr['source_SSE'],formula_comparison=pr['Figure3'],
                          support=support['rank_witness'],max_curve_disagreement=support['max_target_curve_disagreement'],
                          frozen_pins=len(pins['source_only_freeze']),stable_pins=len(pins['stable_author_artifacts']),
                          charged_bytes=sum(r['charged_bytes'] for r in READS),peak_rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)

if __name__=='__main__':
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        with threadpool_limits(limits=1):
            main()
        record('NUMERICAL_WARNINGS.json',dict(warnings=[dict(message=str(w.message),file=w.filename,line=w.lineno) for w in caught]))
