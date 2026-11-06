"""Offline independent reconstruction; never imports author helpers or scores real data."""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
                  VECLIB_MAXIMUM_THREADS='1', MKL_NUM_THREADS='1',
                  NUMEXPR_NUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
import sys, json, hashlib, zipfile, io, resource, datetime, ast, base64
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parents[1] / 'tasks/dynamic-routing-first-encounter-2026-10-31'
OLD = AUTHOR.parent / 'dynamic-routing-rule-transfer-2026-10-31'
LIMIT = 180_000_000
READS = []

def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def read(p, purpose='input'):
    p = Path(p)
    b = p.read_bytes()
    READS.append(dict(path=str(p), purpose=purpose, bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
    assert sum(x['bytes'] for x in READS) < LIMIT
    return b

def load(p):
    return json.loads(read(p))

def write(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')

def resources(name, extra=None):
    out = dict(created_utc=stamp(), public_operations=0, ingress_bytes=0,
               input_read_and_decoded_bytes=sum(x['bytes'] for x in READS),
               peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               reads=READS, scientific_processes=1, numerical_threads=1)
    if extra: out.update(extra)
    assert out['peak_rss_bytes'] < 500_000_000
    write(name, out)

def setup():
    pin = load(AUTHOR / 'CODEC_PACKAGE_PIN.json')
    wheel = read(AUTHOR / 'numcodecs.whl', 'trusted codec wheel read/hash')
    assert hashlib.sha256(wheel).hexdigest() == pin['digests']['sha256']
    with zipfile.ZipFile(io.BytesIO(wheel)) as z:
        names = z.namelist()
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names)
        if not (HERE / 'deps/numcodecs/__init__.py').exists():
            z.extractall(HERE / 'deps')
            READS.append(dict(path='codec extraction', purpose='inflated wheel members',
                              bytes=sum(v.file_size for v in z.infolist())))
    sys.path.insert(0, str(HERE / 'deps'))
    global np, numcodecs, Blosc, VLenUTF8, VLenBytes
    import numpy as np
    import numcodecs
    from numcodecs import Blosc, VLenUTF8, VLenBytes
    numcodecs.blosc.set_nthreads(1)
    return pin

def decode(spec, p):
    b = read(p, 'cached compressed source read/hash')
    assert spec['compressor']['id'] == 'blosc'
    raw = Blosc().decode(b)
    READS.append(dict(path=str(p), purpose='decoded bytes/hash', bytes=len(raw),
                      sha256=hashlib.sha256(raw).hexdigest()))
    if spec['dtype'] == '|O':
        filters = spec['filters']
        assert len(filters) == 1
        codec = {'vlen-utf8': VLenUTF8, 'vlen-bytes': VLenBytes}[filters[0]['id']]()
        a = np.asarray(codec.decode(raw))
        a = np.asarray([x.decode() if isinstance(x, bytes) else x for x in a], dtype=object)
        READS.append(dict(path=str(p), purpose='expanded variable strings conservative', bytes=a.nbytes+sum(len(str(v).encode()) for v in a)))
    else:
        assert not spec.get('filters')
        a = np.frombuffer(raw, dtype=spec['dtype'])
    expected = spec['shape']
    assert a.size == int(np.prod(expected))
    a = a.reshape(expected)
    assert spec['order'] == 'C'
    assert all(c >= n for c, n in zip(spec['chunks'], expected))
    return a

def sources():
    result, metadata, specs = {}, {}, {}
    for sid in ['742903', '664851', '713655', '759434']:
        m = load((OLD / 'nwb_metadata.json') if sid == '742903' else (AUTHOR / 'metadata' / (sid + '.json')))['metadata']
        metadata[sid] = m
        d, ss = {}, {}
        files = sorted((AUTHOR / 'raw' / sid).glob('*.bin'))
        for p in files:
            name = p.stem.replace('__', '/') if sid == '742903' else 'intervals/trials/' + p.stem
            if not name.startswith('intervals/trials/'): continue
            spec = m[name + '/.zarray']
            d[name.split('/')[-1]] = decode(spec, p)
            ss[name.split('/')[-1]] = spec
        if sid == '742903':
            d['reward_time'] = decode(m['intervals/trials/reward_time/.zarray'], OLD / 'reward_time.blosc')
            ss['reward_time'] = m['intervals/trials/reward_time/.zarray']
        assert len(set(len(a) for a in d.values())) == 1
        result[sid], specs[sid] = d, ss
    return result, metadata, specs

def finite(v):
    if isinstance(v, np.generic): v = v.item()
    return None if isinstance(v, float) and not np.isfinite(v) else v

def channel_summary(d):
    y = d['is_response']; r = d['response_time']; a = d['response_window_start_time']; b = d['response_window_stop_time']; w = d['reward_time']
    bad = np.flatnonzero(y != np.isfinite(r))
    cr = d['is_contingent_reward']
    order = np.flatnonzero(cr & ((~y) | (w < r)))
    rows = sorted(set(bad.tolist() + order.tolist()))
    out = dict(rows=len(y), columns=len(d), flag_finite_mismatch=bad.tolist(),
               contingent_reward_before_physical_rows=order.tolist(),
               finite_physical_licks=int(np.isfinite(r).sum()), responses=int(y.sum()),
               all_finite_physical_times_inside_half_open_window=bool(np.all((r[np.isfinite(r)] >= a[np.isfinite(r)]) & (r[np.isfinite(r)] < b[np.isfinite(r)]))),
               strict_stimulus_order=bool(np.all(np.diff(d['stim_start_time']) > 0)),
               windows_before_next_stimulus=bool(np.all(b[:-1] < d['stim_start_time'][1:])),
               all_reward_flags_match_finite_time=bool(np.array_equal(np.isfinite(w), cr | d['is_noncontingent_reward'])),
               records=[dict(row=i, **{k:finite(v[i]) for k,v in d.items()}) for i in rows])
    if 'task_control_response_time' in d:
        t = d['task_control_response_time']
        out.update(controller_finite=int(np.isfinite(t).sum()),
                   controller_flag_exact_match=bool(np.array_equal(np.isfinite(t), y)),
                   controller_finite_outside_window=np.flatnonzero(np.isfinite(t) & ((t < a)|(t >= b))).tolist(),
                   contingent_reward_after_controller=bool(np.all(w[cr] >= t[cr])))
    return out

def first():
    pin = setup()
    data, metadata, specs = sources()
    # This independent product is only source reconstruction, with no forecast evaluation.
    for sid, d in data.items(): np.savez(HERE / (sid + '_independent_arrays.npz'), **d)
    out = dict(created_utc=stamp(), codec_version=numcodecs.__version__,
               trusted_wheel_sha256=pin['digests']['sha256'],
               subjects={sid:channel_summary(d) for sid,d in data.items()},
               schema_shapes={sid:{k:v['shape'] for k,v in ss.items()} for sid,ss in specs.items()},
               total_joined_rows=sum(len(d['is_response']) for d in data.values()),
               all_real_evaluation_losses='UNCOMPUTED')
    write('FIRST_CALCULATION.json', out)
    resources('FIRST_RESOURCES.json')
    print(json.dumps({k:out[k] for k in ['created_utc','codec_version','total_joined_rows']}))
    print(json.dumps({sid:{k:v for k,v in x.items() if k!='records'} for sid,x in out['subjects'].items()},indent=2))

STIMULI = ['aud+', 'aud-', 'catch', 'vis+', 'vis-']
FAMILIES = ['L', 'G', 'C', 'R']
RATES = [0.1, 0.3]

def target_sign(s):
    return {'vis+':1, 'aud+':-1}.get(s, 0)

def new_history(t0):
    return dict(t0=t0, local_y=np.full((5,2),.5), local_w=np.full((5,2),.5),
                previous_same_y=np.full(5,.5), previous_same_w=np.full(5,.5),
                seen_time=[None]*5, global_y=np.full(2,.5), global_w=np.full(2,.5),
                previous_y=.5, previous_w=.5, last_water_time=None,
                reward_sign_traces=np.zeros(2), last_target=0, first_target=0, context=.5)

def row_before(h,s,t):
    h['context'] = .99*h['context'] + .01*(1-h['context'])
    k = STIMULI.index(s); q = target_sign(s)
    def age_value(age): return min(1.,np.log1p(max(0.,age))/np.log(601))
    age = 600 if h['seen_time'][k] is None else t-h['seen_time'][k]
    f = [('constant',1.)] + [('stim_'+x,float(x==s)) for x in STIMULI]
    for j,a in enumerate(RATES):
        f += [('local_response_'+str(a),h['local_y'][k,j]), ('local_reward_'+str(a),h['local_w'][k,j])]
    f += [('last_same_response',h['previous_same_y'][k]),('last_same_reward',h['previous_same_w'][k]),('same_stimulus_age',age_value(age))]
    cuts={'L':len(f)}
    f += [('previous_response',h['previous_y']),('previous_reward',h['previous_w'])]
    for j,a in enumerate(RATES):
        f += [('global_response_'+str(a),h['global_y'][j]),('global_reward_'+str(a),h['global_w'][j])]
    age = 600 if h['last_water_time'] is None else t-h['last_water_time']
    f += [('reward_recency',age_value(age))]
    cuts['G']=len(f)
    other = STIMULI.index('aud+' if q==1 else 'vis+' if q==-1 else 'catch')
    for j,a in enumerate(RATES):
        f += [('opposite_response_'+str(a),int(q!=0)*h['local_y'][other,j]),('opposite_reward_'+str(a),int(q!=0)*h['local_w'][other,j])]
    for j,a in enumerate(RATES): f += [('signed_reward_trace_'+str(a),q*h['reward_sign_traces'][j])]
    angle = np.pi*(t-h['t0'])/600
    f += [('last_rewarded_target_match',q*h['last_target']),('clock_cos',q*h['first_target']*np.cos(angle)),('clock_sin',q*h['first_target']*np.sin(angle))]
    cuts['C']=len(f)
    f += [('context_match',q*(2*h['context']-1))]
    cuts['R']=len(f)
    return np.asarray([v for n,v in f]),[n for n,v in f],cuts

def row_after(h,s,t,y,w,suppress=False):
    k=STIMULI.index(s); q=target_sign(s); h['seen_time'][k]=t
    if suppress: return
    h['previous_same_y'][k]=y;h['previous_same_w'][k]=w
    for j,a in enumerate(RATES):
        for key,value in [('local_y',y),('local_w',w)]: h[key][k,j]=(1-a)*h[key][k,j]+a*value
        for key,value in [('global_y',y),('global_w',w),('reward_sign_traces',q*w)]:h[key][j]=(1-a)*h[key][j]+a*value
    h['previous_y']=y;h['previous_w']=w
    if w:
        h['last_water_time']=t
        if q:
            h['last_target']=q
            if h['first_target']==0:h['first_target']=q
    if q and (w or y):
        likelihood=.95 if w else .05
        if q==-1:likelihood=1-likelihood
        mass=h['context']*likelihood
        h['context']=np.clip(mass/(mass+(1-h['context'])*(1-likelihood)),1e-12,1-1e-12)

def features(d, ablation=False):
    h=new_history(float(d['stim_start_time'][0]));out=[]
    for i in range(len(d['stim_name'])):
        s=str(d['stim_name'][i]);t=float(d['stim_start_time'][i])
        v,n,c=row_before(h,s,t);out.append(v)
        row_after(h,s,t,float(d['is_response'][i]),float(np.isfinite(d['reward_time'][i])),ablation and bool(d['is_instruction'][i]))
    return np.asarray(out),n,c

def encounters(d):
    out=[];excluded=[]
    for block in np.unique(d['block_index']):
        if block==0:continue
        ix=np.flatnonzero(d['block_index']==block);ins=ix[d['is_instruction'][ix]]
        ok = len(ins)==5 and np.array_equal(ins,ix[:5]) and len(set(d['stim_name'][ins]))==1
        if ok:ok = target_sign(str(d['stim_name'][ins[0]]))!=0
        if not ok or np.any(d['is_opto'][ix] | d['is_repeat'][ix]):
            excluded.append(int(block));continue
        new=str(d['stim_name'][ins[0]]);old='aud+' if new=='vis+' else 'vis+'
        cand=ix[d['stim_name'][ix]==old]
        if len(cand):out.append(dict(trial=int(cand[0]),block=int(block),stimulus=old,new_target=new,strict_immediate=bool(cand[0]==ix[5]),new_block_rows_before=int(cand[0]-ix[0]),instruction_rows_before=5))
        else:excluded.append(int(block))
    return out,excluded

def sigmoid(x):
    # Stable independently implemented logistic transform.
    return np.exp(-np.logaddexp(0.,-x))

def probabilities(X, model):
    beta=np.asarray(model['beta']);z=(X-np.asarray(model['mean']))/np.asarray(model['scale'])
    return np.clip(sigmoid(np.sum(z*beta,axis=1)),.001,.999)

def gate(d):
    t=d['stim_start_time'];a=d['response_window_start_time'];b=d['response_window_stop_time'];r=d['response_time'];w=d['reward_time'];y=d['is_response'];c=d['is_contingent_reward'];n=d['is_noncontingent_reward'];finite_w=np.isfinite(w)
    return dict(equal_shapes=len({len(v) for v in d.values()})==1,
        finite_strict_stimulus_order=bool(np.all(np.isfinite(t)) and np.all(np.diff(t)>0)),
        stim_response_window_order=bool(np.all((t<a)&(a<b))),
        response_window_before_next_stimulus=bool(np.all(b[:-1]<t[1:])),
        response_flag_equals_finite_response=bool(np.array_equal(y,np.isfinite(r))),
        finite_responses_in_window=bool(np.all((r[y]>=a[y])&(r[y]<b[y]))),
        finite_rewards_equal_delivered_flags=bool(np.array_equal(finite_w,c|n)),
        delivered_flags_disjoint=bool(not np.any(c&n)),
        contingent_reward_after_response=bool(np.all(y[c]) and np.all(w[c]>=r[c])),
        rewards_after_stimulus=bool(np.all(w[finite_w]>=t[finite_w])),
        past_rewards_before_next_stimulus=bool(np.all(np.isnan(w[:-1])|(w[:-1]<t[1:]))),
        instruction_equals_scheduled=bool(np.array_equal(d['is_instruction'],d['is_reward_scheduled'])))

def contrary(data, metadata):
    plan=read(HERE/'CONTRARY_PLAN.md','predeclared contrary plan/hash')
    out=dict(created_utc=stamp(),plan_sha256=hashlib.sha256(plan).hexdigest(),subjects={})
    for sid,d in data.items():
        ep,ex=encounters(d);m=metadata[sid]
        defs={k:m['intervals/trials/'+k+'/.zattrs'] for k in ['response_time','is_response','task_control_response_time','response_window_start_time','response_window_stop_time','reward_time']}
        r=d['response_time'];a=d['response_window_start_time'];b=d['response_window_stop_time'];y=d['is_response'];w=d['reward_time'];c=d['is_contingent_reward']
        bad=np.flatnonzero((y!=np.isfinite(r)) | (c & (w<r)))
        rows=[]
        for i in bad:
            actual=float(r[i]);owner=np.flatnonzero((a<=actual)&(actual<b))
            delta=float(b[i]-actual)
            near=[]
            for j in range(max(0,i-1),min(len(y),i+2)):
                near.append(dict(row=j,stimulus=str(d['stim_name'][j]),start=float(a[j]),stop=float(b[j]),physical=finite(r[j]),flag=bool(y[j])))
            before=[e['trial'] for e in ep if i<e['trial']]
            selected=any(e['trial']==i for e in ep)
            rows.append(dict(row=int(i),source_row_field_values={k:finite(v[i]) for k,v in d.items()},
                unique_half_open_window_owners=owner.tolist(),closed_interval_counts_as_response=bool(a[i]<=actual<=b[i]),
                stop_minus_physical_seconds=delta,nominal_60Hz_frames_to_stop=delta*60,
                still_inside_if_stop_one_nominal_frame_earlier=bool(a[i]<=actual<b[i]-1/60),
                neighbors=near,selected_primary_outcome=selected,later_primary_encounters=before,
                reward_minus_physical_seconds=finite(w[i]-r[i]),
                reward_minus_controller_seconds=finite(w[i]-d['task_control_response_time'][i]) if 'task_control_response_time' in d else None))
        # A hypothetical input-channel difference, never a rescored/revised model.
        X,n,cuts=features(d)
        alt={**d,'is_response':np.isfinite(r)}
        XA,_,_=features(alt)
        relevant=[]
        for e in ep:
            diff=XA[e['trial']]-X[e['trial']]
            relevant.append(dict(trial=e['trial'],changed_feature_names=[n[k] for k in np.flatnonzero(diff!=0)],max_absolute_feature_change=float(np.max(np.abs(diff))),context_match_change=float(diff[-1])))
        x=dict(definitions=defs,first_encounters=ep,excluded_blocks=ex,discrepant_rows=rows,
            hypothetical_physical_indicator_history_changes_at_endpoints=relevant,
            response_window_width_seconds_by_stimulus={s:dict(min=float(np.min((b-a)[d['stim_name']==s])),max=float(np.max((b-a)[d['stim_name']==s]))) for s in np.unique(d['stim_name'])},
            guard_checks=gate(d))
        if 'task_control_response_time' in d:
            tcr=d['task_control_response_time'];both=np.isfinite(r)&np.isfinite(tcr)
            dif=r[both]-tcr[both]
            x['physical_minus_controller_seconds_quantiles']={str(q):float(np.quantile(dif,q)) for q in [0,.25,.5,.75,1]}
            x['minimum_window_stop_minus_registered_seconds']=float(np.min(b[np.isfinite(tcr)]-tcr[np.isfinite(tcr)]))
            x['all_contingent_rewards_follow_registered_times']=bool(np.all(w[c]>=tcr[c]))
        out['subjects'][sid]=x
    # Available code is the DEVELOPMENT commit; evaluation commit bodies are not cached.
    source=read(AUTHOR/'deployed_source.py.txt','cached development task source/hash').decode()
    condition='self.trialPreStimFrames[-1] + self.responseWindow[0] <= self._trialFrame < self.trialPreStimFrames[-1] + self.responseWindow[1]'
    assert condition in source
    out['available_task_source_semantics']=dict(path='deployed_source.py.txt',sha256=hashlib.sha256(source.encode()).hexdigest(),
        source_is_development_commit_not_evaluation_commit=True,half_open_frame_admission=condition,
        controller_response_records_session_frame='self.trialResponseFrame.append(self._sessionFrame)' in source,
        same_branch_can_issue_contingent_reward=True,
        TaskControl_input_sampling_and_raw_lick_converter_not_available=True,
        inferred_nominal_frame_length_is_not_measured_or_certified=True)
    write('CONTRARY.json',out)
    return out

def pins_and_freeze():
    f=load(AUTHOR/'SCIENTIFIC_FREEZE.json');paths=[]
    for name,h in f['paths'].items():
        got=hashlib.sha256(read(AUTHOR/name,'12 frozen artifacts read/hash')).hexdigest()
        paths.append(dict(path=name,match=got==h,expected=h,actual=got))
    assert len(paths)==12 and all(x['match'] for x in paths)
    manifest=load(AUTHOR/'SOURCE_MANIFEST.json');source=[]
    for row in manifest['sources']:
        if not row.get('path'):continue
        p=AUTHOR/row['path']
        if not p.is_file():continue
        b=read(p,'cached acquired source read/hash')
        source.append(dict(path=row['path'],bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),match=hashlib.sha256(b).hexdigest()==row['sha256'],url=row['url'],utc_epoch=row['utc_epoch']))
    assert all(v['match'] for v in source)
    pin=load(AUTHOR/'FORECAST_PINS.json');forecasts=[]
    for name,h in pin['paths'].items():
        got=hashlib.sha256(read(AUTHOR/name,'frozen forecast read/hash')).hexdigest()
        forecasts.append(dict(path=name,match=h==got,sha256=got))
    assert all(x['match'] for x in forecasts)
    # Independently check author stable artifact pins without executing author code.
    stable=load(AUTHOR/'ARTIFACT_PINS.json');artifact=[]
    for name,p in stable['paths'].items():
        b=read(AUTHOR/name,'stable author artifact read/hash')
        artifact.append(dict(path=name,match=len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256']))
    assert all(x['match'] for x in artifact)
    freeze_time=datetime.datetime.fromisoformat(f['created_utc'].replace('Z','+00:00')).timestamp()
    eval_times=[x['utc_epoch'] for x in source if any(x['path'].startswith('raw/'+s+'/') and not x['path'].endswith('task_control_response_time.bin') for s in ['664851','713655','759434'])]
    assert eval_times and min(eval_times)>freeze_time
    forecast_time=datetime.datetime.fromisoformat(pin['created_utc'].replace('Z','+00:00')).timestamp()
    assert max(eval_times)<=forecast_time
    tree=ast.parse(read(AUTHOR/'evaluate.py','frozen evaluation guard inspection').decode())
    score=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='score')
    guardline=next(n.lineno for n in ast.walk(score) if isinstance(n,ast.Assert) and 'valid_for_primary' in ast.unparse(n.test))
    calls=[n.lineno for n in ast.walk(score) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='nll']
    assert calls and guardline<min(calls)
    blocked=load(AUTHOR/'EVALUATION_DATA_CHECK.json')
    assert not blocked['valid_for_primary']
    assert not (AUTHOR/'PRIMARY_SCORES.json').exists() and not (AUTHOR/'SCORED_TRIALS.json').exists()
    out=dict(created_utc=stamp(),frozen_paths=paths,source_response_pins=source,forecast_pins=forecasts,stable_artifact_pins=artifact,
        freeze_utc=f['created_utc'],first_eval_trial_acquisition_utc=datetime.datetime.fromtimestamp(min(eval_times),datetime.timezone.utc).isoformat(),
        last_initial_eval_trial_acquisition_utc=datetime.datetime.fromtimestamp(max(eval_times),datetime.timezone.utc).isoformat(),
        saved_forecast_pin_utc=pin['created_utc'],guard_assert_line=guardline,first_loss_call_line=min(calls),
        frozen_guard_precedes_any_evaluation_loss=True,recorded_valid_for_primary=False,
        primary_and_trial_score_files_absent=True,method='independent source/hash/AST inspection; author score command not run')
    write('PINS_AND_FREEZE.json',out)
    return out

def audit_forecasts(data):
    models=load(AUTHOR/'DEVELOPMENT_MODELS.json');check=load(AUTHOR/'EVALUATION_DATA_CHECK.json');out={};maxerr=0;count=0
    for sid,d in data.items():
        X,n,cuts=features(d);ep,ex=encounters(d)
        p=dict(np.load(io.BytesIO(read(AUTHOR/(sid+'_FORECASTS.npz'))),allow_pickle=True)) if sid!='742903' else None
        row=dict(rows=len(X),features=X.shape[1],first_encounters=ep,endpoint_exclusions=ex,probability_checks={})
        if p is not None:
            assert ep==check['subjects'][sid]['first_encounter_rows']
            assert gate(d)==check['subjects'][sid]['checks']
            for ablate in [False,True]:
                XX=X if not ablate else features(d,True)[0]
                for fam in FAMILIES:
                    assert n[:cuts[fam]]==models[fam]['feature_names']
                    v=probabilities(XX[:,:cuts[fam]],models[fam]);key=('ablation_' if ablate else '')+fam
                    err=float(np.max(np.abs(v-p[key])));assert err<2e-14
                    row['probability_checks'][key]=dict(values=len(v),max_abs_error=err)
                    maxerr=max(maxerr,err);count+=len(v)
        # Actual prefix invariance under current/future outcome perturbations, no loss.
        inv=[]
        for j in sorted({0,100,len(X)//2,len(X)-1}):
            changed={**d,'is_response':d['is_response'].copy(),'reward_time':d['reward_time'].copy()}
            changed['is_response'][j:]=~changed['is_response'][j:];changed['reward_time'][j:]=np.nan
            XX,_,_=features(changed);error=float(np.max(np.abs(XX[:j+1]-X[:j+1])));assert error==0
            inv.append(dict(perturbation_start=j,prefix_max_error=error))
        plain={k:d[k] for k in ['stim_name','stim_start_time','is_response','reward_time']}
        XX,_,_=features(plain);assert np.array_equal(X,XX)
        row['future_current_invariance']=inv;row['privileged_columns_removed_features_identical']=True
        out[sid]=row
    result=dict(created_utc=stamp(),subjects=out,total_evaluation_probabilities=count,max_abs_probability_error=maxerr,
                evaluation_losses='UNCOMPUTED; no real outcomes paired with forecasts for scoring',
                independent_refit_of_development_and_control_models='UNRUN; frozen coefficients used')
    write('FORECAST_RECONSTRUCTION.json',result)
    return result

def audit_controls():
    details=load(AUTHOR/'CONTROL_DETAILS.json');records=load(AUTHOR/'CONTROL_FORECASTS.json');summary=load(AUTHOR/'CONTROL_SUMMARY.json')
    groups={};row_count=0
    for r in records:
        groups.setdefault((r['generator'],r['replicate'],r['animal']),[]).append(r);row_count+=1
    rebuilt=[];largest=0
    for detail in details:
        gen=detail['generator'];rep=detail['replicate'];real={f:[] for f in ['L','G','C']};expected={f:[] for f in ['L','G','C']}
        for animal in range(3):
            rr=groups[(gen,rep,animal)];assert len(rr)==5
            truth=np.asarray([r['truth_probability'] for r in rr]);y=np.asarray([r['outcome'] for r in rr]);assert np.all((truth>0)&(truth<1))
            ls={};es={}
            for fam in FAMILIES:
                pp=np.asarray([r[fam] for r in rr]);ls[fam]=float(np.mean(-(y*np.log(pp)+(1-y)*np.log(1-pp))));es[fam]=float(np.mean(-(truth*np.log(pp)+(1-truth)*np.log(1-pp))))
                a=detail['animals'][animal];largest=max(largest,abs(ls[fam]-a['loss'][fam]),abs(es[fam]-a['expected_loss'][fam]))
            for fam in ['L','G','C']:
                real[fam].append(ls[fam]-ls['R']);expected[fam].append(es[fam]-es['R'])
                largest=max(largest,abs(real[fam][-1]-detail['gains']['R_minus_'+fam][animal]),abs(expected[fam][-1]-detail['expected_gains']['R_minus_'+fam][animal]))
        passed=all(np.mean(real[f])>=.05 and min(real[f])>0 for f in ['G','C'])
        assert passed==detail['finite_practical_rule_pass']
        rebuilt.append(dict(generator=gen,replicate=rep,pass_rule=bool(passed),realized_R_over_C=float(np.mean(real['C'])),expected_fitted_R_over_C=float(np.mean(expected['C']))))
    assert largest<2e-14
    totals={}
    for g in ['C','R']:
        rr=[r for r in rebuilt if r['generator']==g]
        totals[g]=dict(replicates=len(rr),practical_passes=sum(r['pass_rule'] for r in rr),
                       mean_realized_R_over_C=float(np.mean([r['realized_R_over_C'] for r in rr])),
                       mean_expected_fitted_R_over_C=float(np.mean([r['expected_fitted_R_over_C'] for r in rr])),
                       min_expected_fitted_R_over_C=min(r['expected_fitted_R_over_C'] for r in rr),
                       max_expected_fitted_R_over_C=max(r['expected_fitted_R_over_C'] for r in rr))
        assert totals[g]['practical_passes']==summary['summary'][g]['practical_rule_passes']
        assert abs(totals[g]['mean_expected_fitted_R_over_C']-summary['summary'][g]['mean_expected_R_minus_C'])<2e-14
    result=dict(created_utc=stamp(),synthetic_saved_rows=row_count,replicates=len(details),max_saved_arithmetic_error=largest,summary=totals,replicate_arithmetic=rebuilt,
        estimand='expected loss of two fitted predictors integrated against saved generator probabilities, conditional on each realized simulated history; NOT optimal-C projection/oracle gap',
        coefficient_four_is_not_a_known_point_zero_five_nat_increment=True,
        full_hyperparameter_selection_and_population_coverage='UNRUN',all_real_evaluation_losses='UNCOMPUTED')
    write('CONTROL_RECONSTRUCTION.json',result)
    return result

def audit():
    setup();data,metadata,specs=sources()
    con=contrary(data,metadata);pins=pins_and_freeze();forecasts=audit_forecasts(data);controls=audit_controls()
    resources('AUDIT_RESOURCES.json')
    print(json.dumps(dict(contrary_rows={s:[r['row'] for r in x['discrepant_rows']] for s,x in con['subjects'].items()},
                         frozen_pins=len(pins['frozen_paths']),source_pins=len(pins['source_response_pins']),stable_artifact_pins=len(pins['stable_artifact_pins']),
                         forecast_values=forecasts['total_evaluation_probabilities'],max_forecast_error=forecasts['max_abs_probability_error'],
                         control_summary=controls['summary'],charged_read_decoded_bytes=sum(x['bytes'] for x in READS)),indent=2))

def metadata_support(metadata,data):
    pin=load(AUTHOR/'CODEC_PACKAGE_PIN.json');pypi=load(AUTHOR/'codec_pypi.json')
    reference=[x for x in pypi['urls'] if x['filename']==pin['filename']]
    assert len(reference)==1 and reference[0]['digests']['sha256']==pin['digests']['sha256']
    codec=load(AUTHOR/'CODEC_CHECK.json');b=read(OLD/'reward_time.blosc','original reward compressed reference/hash');raw=Blosc().decode(b)
    READS.append(dict(path='original reward trusted decoded reference',purpose='decoded/hash',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    assert len(raw)==4304 and hashlib.sha256(raw).hexdigest()==codec['decoded_sha256']
    oldpins=load(OLD/'ARTIFACT_PINS.json')
    # Preserve original source records; check their declared structure explicitly.
    oldresults=[]
    for key in ['reward_time.blosc','nwb_metadata.json','reward_times.csv']:
        wanted=oldpins.get('paths',oldpins).get(key)
        actual=read(OLD/key,'predecessor source artifact read/hash')
        expected=wanted['sha256'] if isinstance(wanted,dict) else wanted
        assert expected is not None and hashlib.sha256(actual).hexdigest()==expected
        oldresults.append(dict(path=key,sha256=expected,match=True))
    units=[]
    fields={'subject':'general/subject/subject_id','session':'general/session_id','source':'general/source_script'}
    for sid,m in metadata.items():
        scalars={}
        for key,field in fields.items():
            path=(AUTHOR/'raw/742903'/(field.replace('/','__')+'.bin')) if sid=='742903' else (AUTHOR/'metadata'/(sid+'_'+key+'.bin'))
            value=decode(m[field+'/.zarray'],path).tolist()
            scalars[key]=value[0] if isinstance(value,list) else value
        desc=load(AUTHOR/'data_description.json' if sid=='742903' else AUTHOR/'metadata'/(sid+'_description.json'))
        assert scalars['subject']==sid==desc['subject_id']
        assert scalars['session'].startswith(sid+'_') and desc['license']=='CC-BY-4.0'
        assert sid not in ['668755']
        record=dict(subject=sid,session=scalars['session'],source_script=scalars['source'],license=desc['license'],asset=desc['name'],
            rows=len(data[sid]['is_response']),table_object_id=m['intervals/trials/.zattrs']['object_id'],
            time_schema_attributes={k:m['intervals/trials/'+k+'/.zattrs'] for k in ['start_time','stim_start_time','response_window_start_time','response_window_stop_time','response_time','reward_time']},
            root_attributes=m['.zattrs'],
            date_after_historical_bug_caveat=scalars['session'].split('_')[1]>'2023-10-20')
        units.append(record)
    assert len({u['subject'] for u in units})==4
    capsule=read(AUTHOR/'capsule_README.md').decode()
    statements=[ln.strip() for ln in capsule.splitlines() if 'different' in ln.lower() and ('mice' in ln.lower() or 'mouse' in ln.lower())]
    assert statements
    blobs=[]
    for record,text in [('task_blob.json','DynamicRouting1.py.txt'),('source_RLmodel_blob.json','source_RLmodel.py.txt')]:
        blob=load(AUTHOR/record);decoded=base64.b64decode(blob['content']);actual=read(AUTHOR/text)
        gitsha=hashlib.sha1(('blob '+str(len(decoded))+'\0').encode()+decoded).hexdigest()
        assert gitsha==blob['sha'] and decoded==actual
        blobs.append(dict(path=text,git_blob_sha1=gitsha,bytes=len(actual),match=True))
    # Source text is inspected, never imported/executed; it does not certify instrument deployment.
    modelsource=read(AUTHOR/'source_RLmodel.py.txt').decode()
    result=dict(created_utc=stamp(),codec_reference=dict(filename=pin['filename'],sha256=pin['digests']['sha256'],cached_PyPI_digest_matches=True,
            reward_decoded_bytes=len(raw),decoded_sha256=hashlib.sha256(raw).hexdigest(),matches_frozen_inherited_decoded_pin=True,
            original_decoder_independent_reexecution='UNRUN; trusted C-Blosc independently decoded original bytes'),
        predecessor_pins=oldresults,units=units,source_independence_statements=statements,git_blobs=blobs,
        closest_cached_model_source_contains_BasicRL='BasicRL' in modelsource,closest_cached_model_source_contains_ContextRL='ContextRL' in modelsource,
        original_sensor_data_hardware_replay_and_evaluation_commit_bodies='UNAVAILABLE/UNRUN',
        time_unit_scope='NWB TimeIntervals source convention: seconds in common session reference. Per-column attrs reproduced; no separately measured sensor-clock calibration.')
    write('SOURCE_SUPPORT.json',result)
    return result

def regenerate_generator(base,rng,positive):
    h=new_history(float(base['stim_start_time'][0]));bias=float(rng.normal(0,.25));truth=[];ys=[];waters=[]
    targets={}
    for block in np.unique(base['block_index']):
        ins=np.flatnonzero((base['block_index']==block)&base['is_instruction'])
        targets[int(block)]=str(base['stim_name'][ins[0]])
    for i in range(len(base['stim_name'])):
        s=str(base['stim_name'][i]);t=float(base['stim_start_time'][i]);v,n,c=row_before(h,s,t);f=dict(zip(n,v))
        linear=-2.2+bias+4*f['local_reward_0.3']+f['local_response_0.3']+1.5*f['clock_cos']
        if positive:linear+=4*f['context_match']
        p=float(np.clip(sigmoid(linear),.001,.999));y=bool(rng.random()<p)
        w=bool(s==targets[int(base['block_index'][i])] and (base['is_instruction'][i] or y))
        row_after(h,s,t,float(y),float(w));truth.append(p);ys.append(y);waters.append(w)
    return np.asarray(truth),np.asarray(ys),bias

def generator_support(base):
    details=load(AUTHOR/'CONTROL_DETAILS.json');records=load(AUTHOR/'CONTROL_FORECASTS.json')
    index={(r['generator'],r['replicate'],r['animal'],r['trial']):r for r in records}
    ep,_=encounters(base);positions=[e['trial'] for e in ep];checks=[];maxerror=0;outcomes=0;biaserror=0
    for detail in details:
        positive=detail['generator']=='R';rng=np.random.default_rng(314159+detail['replicate']+(10000 if positive else 0))
        p,y,bias=regenerate_generator(base,rng,positive)
        biaserror=max(biaserror,abs(bias-detail['development_intercept_shift']))
        for animal in range(3):
            p,y,bias=regenerate_generator(base,rng,positive)
            biaserror=max(biaserror,abs(bias-detail['animals'][animal]['intercept_shift']))
            for trial in positions:
                row=index[(detail['generator'],detail['replicate'],animal,trial)]
                maxerror=max(maxerror,abs(float(p[trial])-row['truth_probability']))
                assert int(y[trial])==row['outcome'];outcomes+=1
        checks.append(dict(generator=detail['generator'],replicate=detail['replicate'],all_saved_outcomes_match=True))
    assert maxerror<2e-14 and biaserror==0
    result=dict(created_utc=stamp(),full_synthetic_sequences_generated=4*len(details),total_synthetic_rows_generated=4*len(details)*len(base['stim_name']),
        saved_endpoint_truths_and_outcomes_verified=outcomes,max_truth_probability_error=maxerror,max_animal_bias_error=biaserror,
        conditional_generator_checks=checks,control_model_refits='UNRUN; this verifies generator truths/outcomes and separate saved-predictor loss arithmetic, not independent refitting',
        evaluation_real_losses='UNCOMPUTED')
    write('GENERATOR_SUPPORT.json',result)
    return result

def support():
    setup();data,metadata,specs=sources();meta=metadata_support(metadata,data);gen=generator_support(data['742903'])
    resources('SUPPORT_RESOURCES.json')
    print(json.dumps(dict(source_units=len(meta['units']),predecessor_pins=len(meta['predecessor_pins']),git_blobs=len(meta['git_blobs']),
        generated_synthetic_rows=gen['total_synthetic_rows_generated'],saved_synthetic_rows_matched=gen['saved_endpoint_truths_and_outcomes_verified'],
        max_truth_probability_error=gen['max_truth_probability_error'],charged_read_decoded_bytes=sum(x['bytes'] for x in READS)),indent=2))

if __name__ == '__main__':
    {'first':first,'audit':audit,'support':support}[sys.argv[1]]()
