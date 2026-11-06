#!/usr/bin/env python3
"""Independent transition/continuation audit; source outcomes already consumed.

Only one original development animal's first1000 rows may be read. Everything
else uses synthetic inputs, frozen models/banks, and generated futures. No Pan
route, later source rows, or historical log writer is permitted.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import sys

C = Path(__file__).resolve().parents[1]
ROOT = C.parents[1]
os.environ.setdefault('NUMBA_CACHE_DIR', str(C / 'artifacts/numba_cache'))
sys.dont_write_bytecode = True
sys.path.insert(0, str(C / 'code'))
import numpy as np
from scipy.special import expit, logit
import common
from session_model import from_frozen
from rnn_learning import load_rnn
from rnn_rollout import calibration_particles
from baselines import load_bank, omission_at
from trainer import VectorTrainer

OUT = C / 'audits/INDEPENDENT_TRANSITION_CHECK.json'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def maximum(a, b):
    return float(np.max(np.abs(np.asarray(a) - np.asarray(b))))


def reference(data, model, initial, continuing=False, double=False,
              transition_after_prediction=False):
    """Scalar NumPy GRU equations, without production sequence/update calls."""
    theta = model.params
    if isinstance(initial, dict):
        w = np.array(initial['w'], float, copy=True)
        h = np.array(initial['h'], float, copy=True)
    else:
        w = np.array(initial, float, copy=True)
        h = np.zeros(model.hidden)
    s = np.nan_to_num(data['contrastRight']) - np.nan_to_num(data['contrastLeft'])
    answer, weights = [], []
    for t, contrast in enumerate(s):
        boundary = bool(data['session_start'][t]) and (t > 0 or continuing)
        if boundary and not transition_after_prediction:
            w *= model.rho
            h *= model.rho
            if double:
                w *= model.rho
                h *= model.rho
        z = np.tanh(5. * contrast) / np.tanh(5.)
        x = np.array([max(z, 0.), min(z, 0.), 1.])
        answer.append(float(expit(w @ x)))
        weights.append(w.copy())
        if boundary and transition_after_prediction:
            w *= model.rho
            h *= model.rho
        choice = data['choice'][t]
        if choice == 0:
            continue
        inp = np.r_[w, z, 1., float(data['session_start'][t]),
                    float(choice < 0), float(data['feedbackType'][t] > 0),
                    float(z > 0)]
        gi = theta['Wih'] @ inp + theta['bih']
        gh = theta['Whh'] @ h + theta['bhh']
        H = model.hidden
        reset = expit(gi[:H] + gh[:H])
        update = expit(gi[H:2*H] + gh[H:2*H])
        new = np.tanh(gi[2*H:] + reset * gh[2*H:])
        h = (1. - update) * new + update * h
        v = np.maximum(theta['A'] @ h + theta['a'], 0.)
        v = np.maximum(theta['B'] @ v + theta['b'], 0.)
        w += theta['scale'] * (theta['C'] @ v + theta['cc'])
    return np.asarray(answer), np.asarray(weights), dict(w=w, h=h)


def sliced(data, lo, hi=None):
    return {k:v[lo:hi] for k,v in data.items()}


def independent_particles(data, model, n, seed):
    """Reconstruct the frozen rank3 prefix uncertainty from scalar reference."""
    initial = model.initial_state(data)
    w0 = initial['w0']
    p, _, endpoint = reference(data, model, w0)
    jac_logits, jac_w, jac_h = [], [], []
    eps = .001
    for j in range(3):
        perturb = np.eye(3)[j] * eps
        a, _, ae = reference(data, model, w0 + perturb)
        b, _, be = reference(data, model, w0 - perturb)
        jac_logits.append((logit(np.clip(a, 1e-7, 1-1e-7)) -
                           logit(np.clip(b, 1e-7, 1-1e-7))) / (2 * eps))
        jac_w.append((ae['w'] - be['w']) / (2 * eps))
        jac_h.append((ae['h'] - be['h']) / (2 * eps))
    J = np.stack(jac_logits, axis=1)
    W = np.stack(jac_w, axis=1)
    H = np.stack(jac_h, axis=1)
    used = data['choice'] != 0
    fisher = .5 * np.eye(3)
    for j, probability in zip(J[used], p[used]):
        fisher += probability * (1 - probability) * np.outer(j, j)
    covariance = np.linalg.inv(fisher)
    ev, U = np.linalg.eigh((covariance + covariance.T) / 2)
    covariance = (U * np.clip(ev, 1e-7, 4.)) @ U.T
    wcov = W @ covariance @ W.T
    maxev = float(np.max(np.linalg.eigvalsh((wcov + wcov.T) / 2)))
    factor = min(1., np.sqrt(4. / maxev)) if maxev > 0 else 1.
    delta = np.random.default_rng(seed).multivariate_normal(
        np.zeros(3), covariance, size=n) * factor
    state = dict(w=endpoint['w'] + delta @ W.T,
                 h=np.clip(endpoint['h'] + delta @ H.T, -1, 1))
    return state, covariance, wcov * factor**2


def independent_autonomous(model,prefix,starts,common_state,initial,policy,seed):
    """New vector recurrence/endpoint reduction; reuse settled frozen trainer.

    This independently checks the new transition's placement and uniqueness in
    an entire autonomous stream. It does not repeat the prior native-trainer
    source reconstruction, which is covered by the historical frozen audit.
    """
    n = len(initial['w'])
    theta = model.params
    w, h = initial['w'].copy(), initial['h'].copy()
    H = model.hidden
    rng = np.random.default_rng(seed+101)
    trainer = VectorTrainer.from_prefix(prefix,n,seed+419,policy)
    all_x, all_c, weight_bins = [], [], []
    for t in range(len(starts)):
        if starts[t]:
            trainer.new_session()
            w *= model.rho
            h *= model.rho
        task = trainer.sample()
        contrast = task['signed_contrast']
        z = np.tanh(5.*contrast)/np.tanh(5.)
        X = np.c_[np.maximum(z,0.),np.minimum(z,0.),np.ones(n)]
        probability = expit(np.sum(w*X,axis=1))
        choice = np.where(rng.random(n)<probability,-1,1).astype(np.int8)
        choice[rng.random(n)<omission_at(common_state,t,'growth')] = 0
        feedback = trainer.observe(choice)['feedbackType']
        inp = np.c_[w,z,np.ones(n),np.full(n,float(starts[t])),
                    (choice<0).astype(float),(feedback>0).astype(float),
                    (z>0).astype(float)]
        gi = np.einsum('pi,ji->pj',inp,theta['Wih'])+theta['bih']
        gh = np.einsum('pi,ji->pj',h,theta['Whh'])+theta['bhh']
        reset = expit(gi[:,:H]+gh[:,:H])
        update = expit(gi[:,H:2*H]+gh[:,H:2*H])
        candidate = np.tanh(gi[:,2*H:]+reset*gh[:,2*H:])
        newh = (1-update)*candidate+update*h
        a = np.maximum(np.einsum('pi,ji->pj',newh,theta['A'])+theta['a'],0.)
        b = np.maximum(np.einsum('pi,ji->pj',a,theta['B'])+theta['b'],0.)
        neww = w+theta['scale']*(np.einsum('pi,ji->pj',b,theta['C'])+theta['cc'])
        responded = (choice!=0)[:,None]
        w = np.where(responded,neww,w)
        h = np.where(responded,newh,h)
        all_x.append(contrast)
        all_c.append(choice)
        if (t+1)%500 == 0:
            weight_bins.append(w.copy())
    xx, cc = np.asarray(all_x).T, np.asarray(all_c).T
    curves = np.empty((n,len(starts)//500,4))
    counts = np.empty(curves.shape,int)
    for b in range(len(starts)//500):
        x = xx[:,b*500:(b+1)*500]
        c = cc[:,b*500:(b+1)*500]
        for j, side in enumerate((-1.,1.)):
            mask = np.isclose(x,side,rtol=0,atol=1e-9)
            counts[:,b,j] = mask.sum(1)
            curves[:,b,j] = (mask&(c==-side)).sum(1)/counts[:,b,j]
        curves[:,b,2] = (c<0).sum(1)/500
        curves[:,b,3] = (c==0).sum(1)/500
        counts[:,b,2:] = 500
    return dict(samples=curves,counts=counts,weights=np.transpose(weight_bins,(1,0,2)),
                hidden_final=h)


def main():
    snapshots = [common.OLD / 'protocols/EXPOSURE.jsonl',
                 common.POP / 'protocols/EXPOSURE.jsonl']
    before = {str(p.relative_to(ROOT)):digest(p) for p in snapshots}
    common.historical_check()

    def forbid(*args, **kwargs):
        raise RuntimeError('A historical exposure logger was called')
    common.oldpop.event = forbid
    common.mixed.log = forbid
    import data_io
    data_io.exposure = forbid

    rng = np.random.default_rng(71929)
    n = 1081
    signed = rng.choice([-1., -.5, -.25, -.125, 0., .125, .25, .5, 1.], n)
    choice = rng.choice([-1, 0, 1], n, p=[.45, .10, .45])
    day = np.zeros(n, bool)
    day[[0, 251, 600, 879, 1000]] = True
    choice[[251, 600]] = 0
    feedback = np.where(choice == -np.sign(signed), 1, -1)
    data = dict(contrastLeft=np.maximum(-signed, 0),
                contrastRight=np.maximum(signed, 0), choice=choice,
                feedbackType=feedback, session_start=day)
    w0 = np.array([1.1, 1.4, .25])
    old = load_rnn(common.MODEL)
    records = []
    for rho in (.5, .7, .9, 1.):
        model = from_frozen(common.MODEL, rho)
        p, w, end = model.sequence(data, w0)
        q, v, ref = reference(data, model, w0)
        errors = dict(probability=maximum(p,q), coefficient=maximum(w,v),
                      coefficient_endpoint=maximum(end['w'],ref['w']),
                      memory_endpoint=maximum(end['h'],ref['h']))
        assert max(errors.values()) < 1e-10, (rho, errors)
        split_errors = []
        for cut in (1, 120, 251, 601, 1000):
            a, aw, ae = model.sequence(sliced(data, 0, cut), w0)
            b, bw, be = model.sequence(sliced(data, cut), ae)
            err = max(maximum(np.r_[a,b], p), maximum(np.r_[aw,bw], w),
                      maximum(be['w'],end['w']), maximum(be['h'],end['h']))
            split_errors.append(err)
            assert err == 0., (rho, cut, err)
        # First omitted boundary must affect its probability before observation.
        _, _, ae = model.sequence(sliced(data, 0, 251), w0)
        state = {k:val.copy() for k,val in ae.items()}
        model.pretrial(state, True)
        assert maximum(state['w'],w[251]) == 0.
        before_update = {k:val.copy() for k,val in state.items()}
        model.update(state, signed[251], 0, -1, True)
        omitted_error = max(maximum(state[k],before_update[k]) for k in ('w','h'))
        assert omitted_error == 0.
        assert maximum(w[0], w0) == 0.
        wrong_double, _, _ = reference(data, model, w0, double=True)
        wrong_post, _, _ = reference(data, model, w0,
                                      transition_after_prediction=True)
        if rho < 1:
            assert maximum(wrong_double,p) > .001
            assert abs(wrong_post[251] - p[251]) > .001
        # Current choice/reward cannot affect current or earlier predictions.
        altered = {k:v.copy() for k,v in data.items()}
        altered['choice'][351] = -choice[351] or 1
        altered['feedbackType'][351] *= -1
        changed, _, _ = model.sequence(altered, w0)
        assert maximum(changed[:352],p[:352]) == 0.
        if rho == 1:
            op, ow, oe = old.sequence(data,w0)
            rho1 = max(maximum(p,op), maximum(w,ow),
                       maximum(end['w'],oe['w']), maximum(end['h'],oe['h']))
            assert rho1 == 0.
        records.append(dict(rho=rho, reference_max_abs=errors,
            split_continuation_max_abs=max(split_errors),
            omitted_boundary_response_update_max_abs=omitted_error,
            wrong_double_transition_probability_gap=maximum(wrong_double,p),
            wrong_post_prediction_boundary_gap=float(abs(wrong_post[251]-p[251])),
            causal_probability_change_through_changed_trial=maximum(changed[:352],p[:352])))

    # Only a consumed original-development prefix; no actual future metadata.
    subject = 'CSHL034'
    prefix = common.load_consumed(subject,cap=1000,
        purpose='independent transition and rho1 prefix/Fisher check; no futures')
    assert len(prefix['choice']) == 1000
    one = from_frozen(common.MODEL,1.)
    seed = 71931
    oldst, oldinfo = calibration_particles(old,prefix,256,seed)
    newst, newinfo = calibration_particles(one,prefix,256,seed)
    calibration_error = max(maximum(oldst[k],newst[k]) for k in ('w','h'))
    assert calibration_error == 0.
    assert oldinfo == newinfo
    prefix_checks = []
    for rho in (.7,1.):
        model = from_frozen(common.MODEL,rho)
        actual, info = calibration_particles(model,prefix,256,seed)
        independent, cov0, wcov = independent_particles(prefix,model,256,seed)
        discrepancies = dict(initial_covariance=maximum(cov0,info['initial_covariance']),
            endpoint_covariance=maximum(wcov,info['endpoint_covariance']),
            coefficient_particles=maximum(actual['w'],independent['w']),
            memory_particles=maximum(actual['h'],independent['h']))
        assert max(discrepancies.values()) < 1e-6, (rho,discrepancies)
        prefix_checks.append(dict(rho=rho,max_abs=discrepancies))

    starts = np.zeros(3000,bool)
    starts[[0,353,1101,1900,2571]] = True
    bank = load_bank(common.BANK)
    forecast_errors = {}
    alternative_forecast_errors = {}
    for policy in ('standard','external'):
        direct_common, direct_initial, direct_persistence, _ = common.oldpop.make_initial(
            prefix,subject,256,seed,old,bank)
        direct = common.oldpop.simulate(old,prefix,starts,direct_common,
            direct_initial,direct_persistence,'rnn',policy,seed)
        revised = common.simulate(one,prefix,starts,'rnn',policy,256,seed,subject)
        compare = {k:maximum(direct[k],revised[k]) for k in direct
                   if isinstance(direct[k],np.ndarray)}
        assert max(compare.values()) == 0., (policy,compare)
        forecast_errors[policy] = compare
        alternative = from_frozen(common.MODEL,.7)
        cstate, istate, persist, _ = common.oldpop.make_initial(
            prefix,subject,256,seed,alternative,bank)
        expected = independent_autonomous(alternative,prefix,starts,cstate,istate,policy,seed)
        actual = common.simulate(alternative,prefix,starts,'rnn',policy,256,seed,subject)
        gaps = {k:maximum(expected[k],actual[k]) for k in expected}
        assert gaps['samples'] == 0. and gaps['counts'] == 0.,(policy,gaps)
        assert max(gaps.values()) < 1e-10,(policy,gaps)
        alternative_forecast_errors[policy] = gaps

    # Refused identities/caps must stop before any event or decoding call.
    event_count = len((C/'protocols/EXPOSURE.jsonl').read_text().splitlines())
    refused = []
    for subject, cap in [('fip_13',1000),('SWC_007',1000),('NYU-21',1000),
                         ('not_a_subject',1000),('CSHL034',4001),('CSHL034',0)]:
        try:
            common.load_consumed(subject,cap=cap,purpose='expected rejection fixture')
        except PermissionError:
            refused.append(dict(subject=subject,cap=cap))
        else:
            raise AssertionError('Whitelist/cap failed for '+subject)
    assert len((C/'protocols/EXPOSURE.jsonl').read_text().splitlines()) == event_count
    after = {str(p.relative_to(ROOT)):digest(p) for p in snapshots}
    assert before == after
    common.historical_check()
    output = dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),passed=True,
        scope='Independent synthetic recurrence plus one consumed original development prefix; no real futures or Pan',
        persistent_question='Can source-inferred dynamics forecast1000+3000 acquisition under a different trainer better than growth?',
        source_status='All source checks are development evidence; historical failures unchanged; Pan20 sealed',
        reviewed_code_sha256={str(p.relative_to(ROOT)):digest(p) for p in
            (C/'code/common.py',C/'code/session_model.py',C/'protocols/DESIGN.md')},
        synthetic_seed=71929,synthetic_trials=n,scalar_reference_checks=records,
        rho1_sequence_max_abs=rho1,rho1_prefix_particles_max_abs=calibration_error,
        rho1_prefix_calibration_metadata_exact=True,independent_prefix_fisher=prefix_checks,
        rho1_autonomous_256particles_3000opportunities_max_abs=forecast_errors,
        rho_0p7_independent_autonomous_256particles_max_abs=alternative_forecast_errors,
        empirical_access=dict(subject='CSHL034',cap=1000,actual_future_rows_read=0),
        denied_access_fixtures=refused,historical_log_sha256_before=before,
        historical_log_sha256_after=after,historical_freeze_intact=True,
        no_historical_log_writers_called=True,all_source_results_are_development=True,
        protected_pan_accesses=0)
    OUT.write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(dict(passed=True,rho1_sequence_max_abs=rho1,
        rho1_prefix_particles_max_abs=calibration_error,
        autonomous_max_abs=max(max(q.values()) for q in forecast_errors.values()),
        independent_prefix_max_abs=max(max(q['max_abs'].values()) for q in prefix_checks),
        output=str(OUT))))


if __name__ == '__main__':
    main()
