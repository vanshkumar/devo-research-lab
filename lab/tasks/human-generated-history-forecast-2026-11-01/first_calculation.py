"""Frozen-object first check; no fits, raw CSV, scoring, or external access."""
import os
for _k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_k] = '1'
import sys
sys.dont_write_bytecode = True
import csv
import hashlib
import io
import json
import math
import resource
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAMP = ROOT / 'campaigns/human_learning_routes_2026-10-28'
sys.path.insert(0, str(CAMP / 'experiments'))
import numpy as np
import pandas as pd
from scipy.special import expit
from numpy.polynomial.hermite import hermgauss
from model import FitResult, prepare_features, predict_model, CALIBRATION_NAMES


def main():
    started = time.monotonic()
    pins = []
    def read(rel):
        p = CAMP / rel
        b = p.read_bytes()
        pins.append({'path': str(p.relative_to(ROOT)), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(),
                     'conservative_read_hash_decode_charge': 3 * len(b)})
        return b
    fits = {}
    for name in ('shared', 'no_history'):
        obj = json.loads(read('outputs/primary/' + name + '_fit.json'))
        # Load through the inspected frozen class, recording its additional read.
        fits[name] = FitResult.load(CAMP / ('outputs/primary/' + name + '_fit.json'))
        pins[-1]['conservative_read_hash_decode_charge'] += 2 * pins[-1]['bytes']
    val = pd.read_csv(io.BytesIO(read('inputs/validation_numeric.csv')), dtype={'subject': str, 'session': str})
    sid = sorted(val.subject.unique())[0]
    prefix = val.loc[(val.subject == sid) & (val.trial < 200)].copy()
    probe = val.loc[(val.subject == sid) & (val.trial == 200)].copy()
    # Only scheduled input at 200 enters; its actual choice and feedback are masked.
    probe.loc[:, 'choice'] = 0.
    probe.loc[:, 'feedbackType'] = 0.
    supplied = pd.concat([prefix, probe], ignore_index=True)
    fit = fits['shared']
    features = prepare_features(supplied, calibration_transform=fit.calibration_transform, config=fit.config)
    source_prob = float(predict_model(fit, features)[-1])
    # Independently reconstruct all last-row features and marginalize a scalar
    # Gaussian via its original 20-node rule. No frozen design function is used.
    choices = prefix.choice.to_numpy(float)
    feedback = prefix.feedbackType.to_numpy(float)
    contrast = prefix.sideContrast.to_numpy(float)
    raw_cal = []
    for a, b in ((0, 100), (100, 200)):
        good = np.isin(choices[a:b], (-1., 1.)) & (contrast[a:b] != 0)
        raw_cal.append(float(np.mean(choices[a:b][good] * np.sign(contrast[a:b][good]))) if good.any() else 0.)
    good = np.isin(choices, (-1., 1.))
    raw_cal += [float(np.mean(choices[good])) if good.any() else 0., float(1. - good.mean())]
    calibration = dict(zip(CALIBRATION_NAMES,
                           (np.array(raw_cal) - np.array(fit.calibration_transform['center'])) /
                           np.array(fit.calibration_transform['scale'])))
    hist = np.zeros(3)
    decay = np.exp(-1. / np.array([2., 8., 32.]))
    identity_errors = []
    for ch, fb, target in zip(choices, feedback, prefix.stimSide.to_numpy(float)):
        evidence = ch * fb if ch in (-1., 1.) and fb in (-1., 1.) else 0.
        if ch in (-1., 1.) and fb in (-1., 1.):
            identity_errors.append(abs(evidence - target))
        hist = decay * hist + (1. - decay) * evidence
    c = float(probe.sideContrast.iloc[0])
    sign = float(np.sign(c))
    nuisance = {'intercept': 1., 'previous_choice': float(choices[-1]) if good[-1] else 0.,
                'later_time': (200 - 399.5) / 200., 'sensory_time': sign * (200 - 399.5) / 200.}
    for level in (.1, .25, .5, 1.):
        nuisance['contrast_' + str(level).replace('1.0', '1')] = sign * float(np.isclose(abs(c), level, rtol=0., atol=1e-8))
    vals = dict(nuisance)
    vals.update({'condition:' + k: v * (float(probe.instructions.iloc[0]) - .5) for k, v in nuisance.items()})
    for k, v in calibration.items():
        vals.update({k + ':' + n: v * z for n, z in nuisance.items()})
    hnames = ('history_tau2', 'history_tau8', 'history_tau32')
    vals.update(dict(zip(hnames, hist)))
    for k, v in calibration.items():
        vals.update({k + ':' + n: v * z for n, z in zip(hnames, hist)})
    eta = math.fsum(float(b) * vals[n] for n, b in zip(fit.feature_names, fit.beta))
    variance = fit.config.random_sd ** 2 * (1. + sign * sign + float(hist @ hist))
    nodes, weights = hermgauss(20)
    reference = math.fsum(float(w) * float(expit(eta + math.sqrt(2. * variance) * x)) for x, w in zip(nodes, weights)) / math.sqrt(math.pi)
    # A response, whether correct or wrong, reveals the SAME fixed target.
    branch_evidence = {str(target): {str(ch): ch * (1 if ch == target else -1) for ch in (-1, 1)} for target in (-1, 1)}
    assert max(identity_errors, default=0.) == 0.
    assert abs(source_prob - reference) < 1e-13
    assert all(ev == int(target) for target, branches in branch_evidence.items() for ev in branches.values())
    # Zero-history/zero-variance checks are analytical, independent of data fit.
    assert float(expit(0.)) == .5
    zero_variance = float(np.sum(weights * expit(eta)) / math.sqrt(math.pi))
    assert abs(zero_variance - float(expit(eta))) < 1e-15
    result = {'utc': datetime.now(timezone.utc).isoformat(), 'native_goal_created': False,
              'subject_rule': 'lexicographically first original reserved participant', 'subject': sid,
              'source_20_node_probability_trial200': source_prob, 'scalar_reference_probability': reference,
              'absolute_difference': abs(source_prob - reference), 'prefix_trials': len(prefix),
              'prefix_feedback_side_max_identity_error': max(identity_errors, default=0.),
              'target_revealed_for_either_choice': branch_evidence,
              'key_limitation': 'Future feedback-side histories are choice-independent under a known realized target schedule and no omissions. Omission/engagement law is not supplied by this check.',
              'scores_computed': False, 'fits_executed': 0, 'raw134MB_csv_opened': False,
              'pins': pins, 'conservative_explicit_read_hash_decode_bytes': sum(p['conservative_read_hash_decode_charge'] for p in pins),
              'wall_seconds': time.monotonic() - started, 'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'physical_io_bytes': 'unknown; process page-cache behavior is not measured', 'host_or_tool_runtime_peak': 'unknown'}
    (HERE / 'FIRST_CALCULATION.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
