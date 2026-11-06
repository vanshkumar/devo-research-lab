"""Frozen auditory-drive amplitude control. Writes only this directory."""
import hashlib
import json
from pathlib import Path
import pickle
import sys
import time
sys.dont_write_bytecode = True
import numpy as np
from scipy.special import erf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT/'experiments/sensory_evaluator_preflight_2026-10-28'
sys.path.insert(0, str(OLD))
import preflight as p


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_features(a, B, b):
    z = np.maximum(a @ B.T + b, 0)
    centered = z - np.sum(z, axis=1, keepdims=True)/z.shape[1]
    sd = np.sqrt(np.sum(centered*centered, axis=1, keepdims=True)/z.shape[1])
    return 2*centered/np.maximum(sd, 1e-12)


def independent_dynamics(net, auditory, hE0, hI0, rh):
    """Explicit frozen source equations, separately implemented; no sim call."""
    def activation(v, params):
        rate, threshold, slope = params
        return .5*rate*(1+erf((v-threshold)/(np.sqrt(2)*slope)))
    hE, hI = hE0.copy(), hI0.copy()
    rE, rI = activation(hE, net.phiE), activation(hI, net.phiI)
    rates = np.empty((len(auditory), net.NE))
    rates[0] = rE
    for t in range(1, len(auditory)):
        e_input = net.W.dot(rh[t-1]) + auditory[t-1] + net.JEE.dot(rE) - net.JEI.dot(rI)
        i_input = net.JIE.dot(rE) - net.JII.dot(rI)
        hE = hE + (-hE + e_input)/net.tauE
        hI = hI + (-hI + i_input)/net.tauI
        rE, rI = activation(hE, net.phiE), activation(hI, net.phiI)
        rates[t] = rE
    return np.array([rates[a:b+20].mean() for a,b in zip(p.ON,p.OFF)])


def main():
    t0 = time.perf_counter()
    plan = json.loads((HERE/'PREDECLARATION.json').read_text())
    paths = [OLD/'state.pkl', OLD/'inputs.npz', OLD/'preflight.py',
        p.SOURCE/'src/models.py', p.SOURCE/'src/train_funcs.py']
    hashes = {str(x.relative_to(ROOT)):sha(x) for x in paths}
    with open(OLD/'state.pkl','rb') as f:
        state = pickle.load(f)
    net = state['net']
    B, b, target = state['basis'], state['bias'], state['targets']
    yt = p.plant(target, B, b)
    yt_check = independent_features(target, B, b)
    features_errors, loss_errors, rows = [], [], []
    score_repeat_max, dynamics_error = 0., 0.
    def score(aud):
        return p.run_frozen(net, aud, state['hE'], state['hI'], state['rh'])[0]
    for offset in plan['motor_offset_scales']:
        a = target + offset*state['offsets']
        y = p.plant(a,B,b)
        y_check = independent_features(a,B,b)
        features_errors.append(float(np.max(np.abs(y-y_check))))
        aud = p.auditory(a,B,b)
        energy = np.mean(y_check*y_check)
        cross = np.mean(y_check*yt_check)
        target_energy = np.mean(yt_check*yt_check)
        continuous_true_optimum = max(0., cross/energy)
        for gain in plan['auditory_drive_gains']:
            gain_aud = gain*aud
            per_context = score(gain_aud)
            again = score(gain_aud)
            score_repeat_max = max(score_repeat_max, float(np.max(np.abs(per_context-again))))
            loss = float(np.mean((gain*y-yt)**2))
            quadratic = float(gain*gain*energy - 2*gain*cross + target_energy)
            loss_errors.append(abs(loss-quadratic))
            per_context_loss = np.mean((gain*y-yt)**2,axis=1)
            if offset == 0 and gain in [.5,1]:
                other = independent_dynamics(net,gain_aud,state['hE'],state['hI'],state['rh'])
                dynamics_error = max(dynamics_error,float(np.max(np.abs(other-per_context))))
            rows.append(dict(offset_scale=offset,gain=gain,circuit_cost=float(per_context.mean()),
                true_loss=loss,quadratic_true_loss=quadratic,
                per_context_cost=per_context.tolist(),per_context_loss=per_context_loss.tolist(),
                continuous_true_optimal_gain=continuous_true_optimum,
                auditory_active_mean=float((gain*y).mean()),
                auditory_active_std=float((gain*y).std()),
                auditory_min=float(gain_aud.min()),auditory_max=float(gain_aud.max())))
    old = json.loads((OLD/'suppression_result.json').read_text())
    exact = next(r for r in rows if r['offset_scale']==0 and r['gain']==1)
    silence = [r for r in rows if r['gain']==0]
    assert exact['circuit_cost'] == old['after_cost']
    assert all(r['circuit_cost']==old['silence_cost'] for r in silence)
    summaries=[]
    for offset in plan['motor_offset_scales']:
        subset=[r for r in rows if r['offset_scale']==offset]
        c=min(subset,key=lambda r:r['circuit_cost'])
        l=min(subset,key=lambda r:r['true_loss'])
        one=next(r for r in subset if r['gain']==1)
        summaries.append(dict(offset_scale=offset,circuit_best_gain=c['gain'],
            true_grid_best_gain=l['gain'],continuous_true_best_gain=c['continuous_true_optimal_gain'],
            circuit_best_cost=c['circuit_cost'],circuit_best_true_loss=c['true_loss'],
            true_grid_best_loss=l['true_loss'],true_loss_excess_over_grid_optimum=c['true_loss']-l['true_loss'],
            cost_at_gain1=one['circuit_cost'],loss_at_gain1=one['true_loss'],
            cost_improvement_from_gain1=one['circuit_cost']-c['circuit_cost'],
            true_loss_change_from_gain1=c['true_loss']-one['true_loss']))
    assert max(loss_errors)<1e-12
    assert max(features_errors)<1e-12
    assert score_repeat_max==0
    assert dynamics_error<1e-12
    assert hashes=={str(x.relative_to(ROOT)):sha(x) for x in paths}
    out=dict(plan=plan,source_commit='8309db5b1e2abb0d937fec7a1f9d434b06a9bd7c',
        predeclaration_sha256=sha(HERE/'PREDECLARATION.json'),source_hashes=hashes,
        result_rows=rows,summaries=summaries,
        verification=dict(exact_repeat_max_error=score_repeat_max,
            independent_feature_max_error=max(features_errors),
            independent_quadratic_loss_max_error=max(loss_errors),
            independent_dynamics_max_error=dynamics_error,
            exact_gain1_original_reproduction=True,exact_silence_original_reproduction=True,
            read_source_files_unchanged=True),
        total_seconds=time.perf_counter()-t0)
    (HERE/'RESULT.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(summaries=summaries,verification=out['verification'],
                         total_seconds=out['total_seconds']),indent=2))


if __name__=='__main__':
    main()
