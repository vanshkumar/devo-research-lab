"""Bounded synthetic preflight; no empirical outcomes or target-trained motor basis.

Run with campaigns/learning_rule_transport_2026-10-28/.modelenv/bin/python.
Source EINet.sim and plasticity functions execute unchanged. Only tqdm's display
is replaced by an identity iterator (the environment has no tqdm installed).
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pickle
import sys
import time
import types

import numpy as np
from scipy.sparse import random as sparse_random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'sources/sensory_evaluator_feasibility_2026-10-28/upstream'
shim = types.ModuleType('tqdm')
shim.tqdm = lambda it, *args, **kwargs: it
sys.modules['tqdm'] = shim
sys.path.insert(0, str(SOURCE / 'src'))
from models import EINet, bilin_hebb_EI, bilin_hebb_IE
from train_funcs import generate_HVC

SEED = 20261028
NE, NI, NH, NC, DA = 600, 150, 15, 100, 8
NS = 6
T_BURN, T_SONG, T_POST, N_REND = 500, 900, 200, 35
ON = np.arange(NS) * 150 + 50
OFF = ON + 100


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plant(a, basis, bias):
    """Fixed 8->100 rectified map, then the source RL input normalization.

    This is a controlled sensory-feature plant, not a vocal biomechanics model.
    It is fixed before targets are drawn, and no fit uses a target.
    """
    y = np.maximum(np.einsum('...d,cd->...c', a, basis) + bias, 0)
    y -= y.mean(axis=-1, keepdims=True)
    return 2 * y / np.maximum(y.std(axis=-1, keepdims=True), 1e-12)


def auditory(a, basis, bias):
    y = np.repeat(plant(a, basis, bias), NE // NC, axis=-1)
    out = np.zeros((T_SONG + T_POST, NE))
    for s in range(NS):
        out[ON[s]:OFF[s]] = y[s]
    return out


def hvc(n_rend, burn):
    length = burn + n_rend * (T_SONG + T_POST)
    starts = burn + np.arange(n_rend) * (T_SONG + T_POST)
    bursts = starts[None, :] + np.linspace(0, T_SONG, NH, endpoint=False)[:, None]
    return generate_HVC(length, bursts, np.full(bursts.shape, 150.),
                        np.full(bursts.shape, 20.))


def initialize(rng):
    c = .5
    means = np.array([1 / np.sqrt(NE*c), 1.7 / np.sqrt(NI*c),
                      1 / np.sqrt(NE*c), 1.5 / np.sqrt(NI*c)]) / 10
    def matrix(n, m, mean):
        std = .1 * mean
        mu = np.log(mean**2 / np.sqrt(mean**2 + std**2))
        sd = np.sqrt(np.log(1 + std**2 / mean**2))
        return sparse_random(n, m, c, format='csc', random_state=rng,
                             data_rvs=lambda size: rng.lognormal(mu, sd, size))
    js = [matrix(n, m, x) for n, m, x in zip(
        [NE, NE, NI, NI], [NE, NI, NE, NI], means)]
    net = EINet(NE, NI, NH, 1/NH, (100, 0, 2), (100, 0, 2), 30, 10,
                *js, w0_std=0, cW=.05)
    return net, means


def run_frozen(net, aud, hE, hI, rh):
    t = time.perf_counter()
    res = net.sim(hE, hI, rh, aud, [], len(aud), 1, 0,
                  no_progress_bar=True)
    means = np.array([res[0][a:b+20].mean() for a, b in zip(ON, OFF)])
    return means, time.perf_counter()-t


def prepare():
    t = time.perf_counter()
    np.random.seed(SEED)
    rng = np.random.default_rng(SEED)
    # Draw plant FIRST, targets SECOND. Keep raw independent seeds/bytes.
    basis = rng.normal(size=(NC, DA)) / np.sqrt(DA)
    bias = rng.normal(-.4, .2, NC)
    targets = rng.normal(size=(NS, DA))
    offsets = rng.normal(size=(NS, DA))
    offsets /= np.linalg.norm(offsets, axis=1, keepdims=True)
    np.savez(HERE/'inputs.npz', basis=basis, bias=bias, targets=targets,
             offsets=offsets, on=ON, off=OFF)
    net, means = initialize(rng)
    hE, hI = rng.normal(-10, .5, NE), rng.normal(-1, .5, NI)
    aud_one = auditory(targets, basis, bias)
    rh_probe = hvc(1, T_BURN)
    burn = net.sim(hE, hI, rh_probe[:T_BURN],
                   np.zeros((T_BURN, NE)), [], T_BURN, 1, 0,
                   no_progress_bar=True)
    hE_probe, hI_probe = burn[-2:]
    rh_probe = rh_probe[T_BURN:]
    before, before_secs = run_frozen(net, aud_one, hE_probe, hI_probe, rh_probe)
    untrained = copy.deepcopy(net)
    aud_train = np.concatenate([np.zeros((T_BURN, NE)),
                                np.tile(aud_one, (N_REND, 1))])
    rh_train = hvc(N_REND, T_BURN)
    train_start = time.perf_counter()
    res = net.sim(hE, hI, rh_train, aud_train, [], len(aud_train), 1, 0,
        plasticity={'JEI':bilin_hebb_EI, 'JIE':bilin_hebb_IE},
        lr={'JEI':5e-2, 'JIE':6e-3}, tauW=1e5,
        JEI0_mean=means[1], JIE0_mean=means[2],
        asyn_E=10, asyn_I=0, rE_th=1.5, rI_th=5,
        no_progress_bar=True)
    train_secs = time.perf_counter()-train_start
    del res, aud_train, rh_train
    # Source Environment burn is re-evaluated after loading the trained net.
    rh_burn = hvc(1, T_BURN)[:T_BURN]
    burn = net.sim(hE, hI, rh_burn, np.zeros((T_BURN, NE)), [], T_BURN,
                   1, 0, no_progress_bar=True)
    hE_probe, hI_probe = burn[-2:]
    after, eval_secs = run_frozen(net, aud_one, hE_probe, hI_probe, rh_probe)
    rows = []
    for scale in [0., .25, .5, 1., 2.]:
        a = targets + scale * offsets
        aud = auditory(a, basis, bias)
        score, sec = run_frozen(net, aud, hE_probe, hI_probe, rh_probe)
        y, yt = plant(a, basis, bias), plant(targets, basis, bias)
        rows.append(dict(scale=scale, circuit_cost=float(score.mean()),
            per_syllable_cost=score.tolist(),
            true_loss=float(np.mean((y-yt)**2)), seconds=sec))
    silence, _ = run_frozen(net, np.zeros_like(aud_one), hE_probe, hI_probe, rh_probe)
    with open(HERE/'state.pkl', 'wb') as f:
        pickle.dump(dict(net=net, untrained=untrained, hE=hE_probe, hI=hI_probe,
                         rh=rh_probe, basis=basis, bias=bias, targets=targets,
                         offsets=offsets), f)
    out = dict(seed=SEED, NE=NE, NI=NI, NH=NH, channels=NC, actions_per_syllable=DA,
        syllables=NS, tutor_renditions=N_REND,
        training_seconds=train_secs, probe_seconds=eval_secs,
        total_seconds=time.perf_counter()-t,
        before_cost=float(before.mean()), after_cost=float(after.mean()),
        suppression_fraction=float(1-after.mean()/before.mean()),
        before_per_syllable=before.tolist(), after_per_syllable=after.tolist(),
        silence_cost=float(silence.mean()), perturbation_ordering=rows,
        source_hashes={str(p.relative_to(SOURCE)):sha(p) for p in SOURCE.rglob('*')
                       if p.is_file() and '__pycache__' not in str(p)},
        note='Synthetic feature plant; exact source circuit/plasticity; zero dynamical noise; fixed source clock; no actor yet.')
    (HERE/'suppression_result.json').write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps(out, indent=2), flush=True)


def motor_updates():
    """Matched coordinate perturbations, not a backprop-through-plant actor.

    Each candidate receives the same 96 finite-perturbation observations.
    Circuit actor sees only its scalar rate cost. Oracle alone sees true loss.
    Deterministic finite differences are an intentionally favorable diagnostic;
    this does not establish stochastic RL sample efficiency or neural realism.
    """
    t0 = time.perf_counter()
    with open(HERE/'state.pkl', 'rb') as f:
        d = pickle.load(f)
    net, basis, bias, target = [d[x] for x in ['net', 'basis', 'bias', 'targets']]
    y_target = plant(target, basis, bias)
    eps, step = .05, .1
    def evaluate(a):
        scores, seconds = run_frozen(net, auditory(a, basis, bias),
                                    d['hE'], d['hI'], d['rh'])
        loss = np.mean((plant(a, basis, bias)-y_target)**2)
        return float(scores.mean()), float(loss)
    rows = []
    for scale in [.25, 1., 2.]:
        a = target + scale * d['offsets']
        c0, l0 = evaluate(a)
        gc, gl = np.zeros_like(a), np.zeros_like(a)
        queries = []
        for i in range(a.size):
            delta = np.zeros_like(a)
            delta.flat[i] = eps
            cp, lp = evaluate(a+delta)
            cm, lm = evaluate(a-delta)
            gc.flat[i] = (cp-cm)/(2*eps)
            gl.flat[i] = (lp-lm)/(2*eps)
            queries.append([i, cp, cm, lp, lm])
        c_actor = a - step * gc / np.linalg.norm(gc)
        o_actor = a - step * gl / np.linalg.norm(gl)
        cc, lc = evaluate(c_actor)
        co, lo = evaluate(o_actor)
        row = dict(scale=scale, original_cost=c0, original_loss=l0,
            dot_product=float(np.sum(gc*gl)),
            gradient_cosine=float(np.sum(gc*gl)/np.linalg.norm(gc)/np.linalg.norm(gl)),
            circuit_step_cost=cc, circuit_step_true_loss=lc,
            circuit_true_improvement=l0-lc, oracle_step_cost=co,
            oracle_step_true_loss=lo, oracle_true_improvement=l0-lo,
            fraction_of_oracle_improvement=(l0-lc)/(l0-lo),
            circuit_gradient_norm=float(np.linalg.norm(gc)),
            oracle_gradient_norm=float(np.linalg.norm(gl)),
            queries_per_actor=2*a.size, update_norm=step)
        rows.append(row)
        np.savez(HERE/f'motor_queries_scale_{scale:g}.npz',
                 action=a, queries=np.array(queries), circuit_gradient=gc,
                 oracle_gradient=gl, circuit_next=c_actor, oracle_next=o_actor)
        print(json.dumps(row), flush=True)
    out = dict(seed=SEED, finite_difference=eps, step_norm=step, results=rows,
        total_seconds=time.perf_counter()-t0,
        interpretation='One deterministic finite-perturbation update per start; no full RL, no performance-tuned step, no gradient through plant given to either actor.')
    (HERE/'motor_update_result.json').write_text(json.dumps(out, indent=2)+'\n')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['prepare', 'motor'], default='prepare')
    args = ap.parse_args()
    prepare() if args.stage == 'prepare' else motor_updates()
