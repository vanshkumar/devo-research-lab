#!/usr/bin/env python3
"""Read-only reference and fixed pilot. No empirical-trial loaders imported."""
from pathlib import Path
from collections import Counter
import datetime as dt
import hashlib
import importlib.util
from io import BytesIO
import json
import resource
import sys
import time

import numpy as np
from scipy.special import expit

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
OLD = ROOT / 'campaigns/learning_rule_transport_2026-10-28'
REV = ROOT / 'campaigns/learning_transport_revised_2026-10-29'
POP = ROOT / 'campaigns/population_learning_transport_2026-10-28'
COMP = REV / 'artifacts/source_comparison'
N = 256
PROBE = np.array([-1., 1., -.25, .25, -.125, .125, -.0625, .0625])
MODELS = ('existing', 'session', 'growth', 'reinforce')
ARMS = ('H_last', 'E_last', 'H_rich', 'E_rich')
STARTS = ('early_1000', 'late_4000')
ENG = ('nominal', 'hard_omit_plus10pp')
D = Counter()
PINS = {}

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def raw(path, pin=None):
    b = path.read_bytes()
    D['file_bytes_returned'] += len(b)
    h = hashlib.sha256(b).hexdigest()
    if pin is not None:
        assert pin == h, (str(path), pin, h)
    PINS[str(path.relative_to(ROOT))] = h
    return b

def js(path, pin=None):
    return json.loads(raw(path, pin))

def arrays(path, keys, pin=None):
    with np.load(BytesIO(raw(path, pin)), allow_pickle=False) as z:
        a = {k:z[k] for k in keys}
    D['decoded_array_bytes'] += sum(x.nbytes for x in a.values())
    return a

def save(name, obj):
    (TASK / name).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')

def model_load():
    code = OLD / 'code'
    sys.path.insert(0, str(code))
    for path, sha in [
        (code/'learning_models.py', '46090bda22320171eaca91b979476b7aefc947d0cff4b3fe3c14ae67fa818017'),
        (code/'rnn_learning.py', '9d08cb223a6e418c7d32575c5927864ccb642f89d4365b510fd9341dbc5d4023'),
        (REV/'code/session_model.py','1eefc9c9f569b20099bb64cf186d64eeeed1b840e411eac6e7dabd9663e62e83'),
    ]:
        raw(path,sha)
    from rnn_learning import load_rnn
    from learning_models import load_model
    sp = importlib.util.spec_from_file_location('pinned_session', REV/'code/session_model.py')
    sm = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(sm)
    existing = OLD/'artifacts/rnn/rnnglm32_nested_best.npz'
    session = REV/'model_session_transition.npz'
    rl = OLD/'artifacts/models/reinforce_nested_stable.npz'
    for path,sha in [
        (existing,'c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940'),
        (session,'c914494c5c8680c1989242d539912f686442dd59c5b64d609efc436834e03f5d'),
        (rl,'c5c8afadcea0b7a6e8ba90c04c0dc8e78f1a9d80442d648b53dd78cb8b3981e2'),
    ]:
        raw(path,sha)
        D['loader_file_bytes_nominal'] += path.stat().st_size
    e,s,r = load_rnn(existing),sm.load_session(session),load_model(rl)
    assert s.rho==.9 and all(np.array_equal(e.params[k],s.params[k]) for k in e.params)
    D['decoded_array_bytes'] += sum(v.nbytes for m in (e,s,r) for v in m.params.values())
    return dict(existing=e,session=s,reinforce=r,growth=None)

def reference():
    ref = js(COMP/'RESULT.json','cc8b1aedffb9c495d20b059f9c779a8f8762e7abc7500adb40838fb9bb7dab91')
    cohort = js(POP/'protocols/FREEZE.json')['source_primary_subjects']
    historical = js(OLD/'artifacts/results/SUBJECT_ORDER.json')
    ids = historical + cohort
    assert len(historical)==40 and len(cohort)==24 and len(set(ids))==64
    summary = arrays(COMP/'COMPARISON_ARRAYS.npz',
                     ['subjects','labs','observed','counts','existing','session','growth','persistence'],
                     '8263da4c9f615d1040cd7b39d3bb327200bb727d2612c318564f5b5d393d0661')
    assert list(summary['subjects'])==ids
    labs = summary['labs']
    target = summary['observed'][...,:2].mean(-1)
    assert (summary['counts'][...,:2]>0).all() and np.isfinite(target).all()
    metrics = {}
    for k in ('existing','session','growth','persistence'):
        pred = summary[k][...,:2].mean(-1).mean(1)
        resid = pred-target
        by_lab = {str(l):float(np.abs(resid[labs==l].mean(0)).mean()) for l in np.unique(labs)}
        m = dict(equal_lab_curve_mae=np.mean(list(by_lab.values())),
                 pooled_population_curve_mae=np.abs(resid.mean(0)).mean(),
                 individual_equal_side_mae=np.abs(resid).mean(),
                 mean_accuracy=pred.mean())
        for key,v in m.items():
            assert abs(v-ref['metrics'][k][key])<2e-15, (key,v,ref['metrics'][k][key])
        m['by_lab'] = by_lab
        m['last_bin_bias_by_source_stratum'] = [float(resid[sl,-1].mean()) for sl in (slice(0,40),slice(40,64))]
        metrics[k] = m
    bank = arrays(OLD/'artifacts/baselines/nested_growth_bank.npz',
                  ['subjects','prefix','delta_w','delta_omit','valid','bin_size'],
                  '036f3cfedd56e915b051fb29a80a2622cf5a747366ea31aa46b9249a922eea01')
    return ref, summary, dict(verified_metrics=metrics, roster=ids, labs=labs.tolist(),
                 observed_curve=target.mean(0).tolist(),
                 donor_n=len(bank['subjects']), donor_bins=bank['valid'].sum(0).tolist(),
                 donor_bin_size=int(bank['bin_size']))

def build_contexts(ref, summary):
    mfiles = {r['path']:r['sha256'] for r in ref['forecast_records']}
    m_old = {r['path']:r['sha256'] for r in js(OLD/'MANIFEST.json')['artifacts']}
    out = []
    for i, subject in enumerate(summary['subjects']):
        states = {key:{} for key in STARTS}
        baseline = {}
        rng = np.random.default_rng(seed(subject)+33271)
        z = rng.normal(size=(N,3))
        for k in ('existing','session','growth'):
            path = COMP/subject/(k+'.npz')
            keys = ['weights','samples'] + ([] if k=='growth' else ['hidden_final'])
            a = arrays(path, keys, mfiles[str(path.relative_to(ROOT))])
            # Cross check that state archive belongs to the same rows used in the reference.
            assert np.array_equal(a['samples'],summary[k][i])
            assert a['weights'].shape==(512,6,3)
            states['late_4000'][k] = {'w':a['weights'][:N,5].copy()}
            if k=='growth':
                states['early_1000'][k] = {'w':a['weights'][:N,0].copy()}
                for label,b in zip(STARTS,(0,5)):
                    baseline[label] = (500*a['samples'][:N,b,3] + .5)/501.
            else:
                states['late_4000'][k]['h'] = a['hidden_final'][:N].copy()
                rec = js(path.with_suffix('.json'))
                assert rec['forecast_sha256']==mfiles[str(path.relative_to(ROOT))]
                assert rec['freeze_sha256']==ref['comparison_freeze_sha256']
                c = rec['calibration']
                states['early_1000'][k] = dict(w=draw_marginal(z,c),
                    h=np.broadcast_to(c['hidden_endpoint'],(N,32)).copy())
        if i<40:
            candidates = [OLD/'artifacts/forecasts'/f/(subject+'__reinforce.npz') for f in ('source_animals','source_labs')]
            path, = [f for f in candidates if f.is_file()]
            a = arrays(path,['weights'],m_old[str(path.relative_to(OLD))])['weights']
            assert a.shape[0]>=N and a.shape[1]>=6
            states['late_4000']['reinforce']={'w':a[:N,5].copy()}
            rec = js(path.with_suffix('.json'),m_old[str(path.with_suffix('.json').relative_to(OLD))])
            assert rec['model_sha256']=='c5c8afadcea0b7a6e8ba90c04c0dc8e78f1a9d80442d648b53dd78cb8b3981e2'
            states['early_1000']['reinforce']={'w':draw_marginal(z,rec['calibration'])}
        out.append((states,baseline))
    return out

def draw_marginal(z, cal):
    c = np.asarray(cal['endpoint_covariance'])
    v,u = np.linalg.eigh((c+c.T)/2)
    assert v.min()>-1e-10
    return np.asarray(cal['endpoint']) + np.einsum('ij,kj->ik',z,u*np.sqrt(np.maximum(v,0)))

def seed(s):
    return int(hashlib.sha256(s.encode()).hexdigest()[:8],16)

def design(subject):
    rng = np.random.default_rng(seed(subject)+874320)
    e,h = PROBE[:4], PROBE[4:]
    def perm(x,y,ne,nh):
        assert ne%4==0 and nh%4==0
        items = np.r_[np.tile(x,ne//4),np.tile(y,nh//4)]
        u = rng.random((len(items),N))
        return items[np.argsort(u,axis=0)]
    # Reverse the assignment using matched ordinal shuffles.
    first,second = perm(e,h,180,0),perm(e,h,0,180)
    tail = perm(e,h,20,20)
    comp1,comp2 = perm(h,e,152,48),perm(h,e,120,40)
    lookup = dict(zip(PROBE,np.r_[PROBE[4:],PROBE[:4]]))
    reverse = np.vectorize(lookup.__getitem__,otypes=[float])
    xs = np.stack([np.vstack([first,second,tail]), np.vstack([second,first,tail]),
                   np.vstack([comp1,comp2,tail]), np.vstack([reverse(comp1),reverse(comp2),tail])],axis=1)
    assert xs.shape==(400,4,N)
    hist = np.stack([(xs==s).sum(0) for s in PROBE])
    assert (hist[:,0]==50).all() and np.array_equal(hist[:,0],hist[:,1])
    assert np.array_equal(hist[:,2],np.concatenate((hist[4:,3],hist[:4,3])))
    assert (xs[360:]==xs[360:,0:1]).all()
    u = rng.random((400,2,N))
    return xs, u

def coeff(x):
    z = np.tanh(5*x)/np.tanh(5.)
    return np.stack([np.maximum(z,0),np.minimum(z,0),np.ones_like(z)],axis=-1)

def reference_step(models, initial):
    # Explicit scalar update with independent formulas on saved late states.
    from math import exp, tanh
    def sigmoid(a): return 1/(1+exp(-a))
    def affine(M,v,b): return [sum(float(a)*float(x) for a,x in zip(row,v))+float(c) for row,c in zip(M,b)]
    errors={}
    data=[(-.125,1,True), (1.,0,False), (.0625,0,True),(-.25,-1,False),(.25,-1,False)]
    for k in ('existing','session','reinforce'):
        m=models[k]; p=m.params
        state={n:v[0].copy() for n,v in initial[k].items()}
        w=state['w'].tolist(); h=state['h'].tolist() if 'h' in state else []
        errs=[]
        for s,c,day in data:
            if day and k=='session':
                state['w']*=m.rho; state['h']*=m.rho
                w=[x*m.rho for x in w]; h=[x*m.rho for x in h]
            z=tanh(5*s)/tanh(5);x=[max(z,0),min(z,0),1.]
            pr=sigmoid(sum(a*b for a,b in zip(w,x)))
            errs.append(float(abs(m.probs(state,s)-pr)))
            r=int(c==-np.sign(s)); y=int(c<0)
            m.update(state,s,c,1 if r else -1,session_start=day)
            if c!=0 and k=='reinforce':
                w=[wj+float(a)*(r+float(b))*(y-pr)*xj for wj,a,b,xj in zip(w,p['alpha'],p['baseline'],x)]
            if c!=0 and k!='reinforce':
                v=w+[z,1.,float(day),y,r,int(z>0)]
                i=affine(p['Wih'],v,p['bih']);j=affine(p['Whh'],h,p['bhh'])
                R=[sigmoid(i[l]+j[l]) for l in range(32)]
                U=[sigmoid(i[l+32]+j[l+32]) for l in range(32)]
                H=[tanh(i[l+64]+R[l]*j[l+64]) for l in range(32)]
                h=[(1-U[l])*H[l]+U[l]*h[l] for l in range(32)]
                a1=[max(0,a) for a in affine(p['A'],h,p['a'])]
                a2=[max(0,a) for a in affine(p['B'],a1,p['b'])]
                w=[wi+float(q)*v for wi,q,v in zip(w,p['scale'],affine(p['C'],a2,p['cc']))]
            errs.append(float(np.max(np.abs(state['w']-w))))
            if h:
                errs.append(float(np.max(np.abs(state['h']-h))))
        errors[k]=max(errs)
        assert errors[k]<1e-12,(k,errors)
    return errors

def simulate(model, model_name, initial, omit, xs, u, stress):
    # Frozen update/probability functions, same learner state and random
    # numbers for paired counterfactual arms; each arm generates its own path.
    s={k:np.tile(v,(4,1)) for k,v in initial.items()}
    xs=xs.reshape((400,4*N))
    omit=np.tile(omit,4)
    step_coeff=coeff(xs)
    training=np.zeros((3,4*N))
    rho=float(getattr(model,'rho',1.))
    for t in range(400):
        day=t in (0,200)
        if day and rho!=1.:
            s['w']*=rho
            s['h']*=rho
        x=xs[t]
        p=expit(np.einsum('ij,ij->i',s['w'],step_coeff[t]))
        o=np.minimum(.995,omit+stress*.10*(np.abs(x)<=.125))
        c=np.where(np.tile(u[t,0],4)<p,-1,1)
        c[np.tile(u[t,1],4)<o]=0
        correct=c==-np.sign(x)
        training[0]+=correct
        training[1]+=c==0
        training[2]+=np.abs(x)<=.125
        if model is not None:
            model.update(s,x,c,np.where(correct,1,-1),session_start=day)
    # Compute the distribution of one terminal first response. No update.
    assert all(np.isfinite(v).all() for v in s.values())
    right=expit(np.einsum('ij,kj->ik',s['w'],coeff(PROBE)))
    correct=np.where(PROBE>0,right,1-right)
    return (correct.reshape(4,N,8), (correct*(1-omit[:,None])).reshape(4,N,8),
            (training/400).reshape(3,4,N), omit.reshape(4,N))

def main():
    began=utc(); t=time.perf_counter()
    with np.errstate(over='raise',invalid='raise',divide='raise'):
        ref,summary,record=reference()
        models=model_load()
        contexts=build_contexts(ref,summary)
        record['independent_scalar_update_max_abs']=reference_step(models,contexts[0][0]['late_4000'])
        record.update(stage_finished=utc(), seconds=time.perf_counter()-t, input_pins=PINS.copy(),
                      counted_io=dict(D), runtime_usage=dict(peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        save('REFERENCE.json',record)
        print('Verified reference, recovered 64 state contexts, validated update at',utc(),flush=True)
        valid=np.zeros((len(contexts),len(MODELS)),dtype=bool)
        cond=np.zeros((len(contexts),2,2,4,4,N,8),dtype=np.float32)
        obs=np.zeros_like(cond)
        tr=np.zeros((len(contexts),2,2,4,3,4,N),dtype=np.float32)
        om=np.zeros((len(contexts),2,4,N),dtype=np.float32)
        for i, (subject,(states,omits)) in enumerate(zip(summary['subjects'],contexts)):
            xs,u=design(subject)
            for j,when in enumerate(STARTS):
                for l,k in enumerate(MODELS):
                    if k not in states[when]:
                        continue
                    valid[i,l]=True
                    for g in range(2):
                        a,b,c,d=simulate(models[k],k,states[when][k],omits[when],xs,u,g)
                        cond[i,j,g,l]=a
                        obs[i,j,g,l]=b
                        tr[i,j,g,l]=c
                        om[i,j]=d
            if (i+1)%8==0:
                print('Subjects',i+1,'/',len(contexts),'seconds',round(time.perf_counter()-t,1),flush=True)
    np.savez_compressed(TASK/'PILOT_ARRAYS.npz', subjects=summary['subjects'],labs=summary['labs'],
          starts=STARTS,engagement=ENG,models=MODELS,arms=ARMS,probe=PROBE,valid=valid,
          conditional_correct=cond,correct=obs,training=tr,terminal_omit=om)
    ru=resource.getrusage(resource.RUSAGE_SELF)
    save('PILOT_EXECUTION.json',dict(utc_start=began,utc_end=utc(),wall_seconds=time.perf_counter()-t,
                  user_seconds=ru.ru_utime,system_seconds=ru.ru_stime,peak_rss_bytes=ru.ru_maxrss,
                  counted_io=dict(D), input_pins=PINS.copy(), empirical_raw_opened=0,
                  protected_read=0, external_ingress=0, model_fits=0, particles=N))
    print('Saved',utc(),flush=True)
if __name__=='__main__':
    main()
