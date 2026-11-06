"""Read-only reuse of consumed source evidence and frozen generative code.

This module has NO external-cohort reader. All new records go to this campaign.
"""
from pathlib import Path
import datetime as dt
import hashlib
import importlib.util
import json
import os
import sys

C = Path(__file__).resolve().parents[1]
ROOT = C.parents[1]
OLD = ROOT / 'campaigns/learning_rule_transport_2026-10-28'
POP = ROOT / 'campaigns/population_learning_transport_2026-10-28'
sys.dont_write_bytecode = True
os.environ.setdefault('NUMBA_CACHE_DIR', str(C / 'artifacts/numba_cache'))
sys.path.insert(0, str(OLD / 'code'))
import numpy as np
from rnn_learning import load_rnn
from baselines import load_bank


def import_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oldpop = import_path('frozen_population_reuse', POP / 'code/campaign.py')
mixed = import_path('frozen_mixed_decode_reuse', POP / 'code/mixed_reader.py')
MODEL = OLD / 'artifacts/rnn/rnnglm32_nested_best.npz'
BANK = OLD / 'artifacts/baselines/nested_growth_bank.npz'
_bank = None


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str) + '\n')


def event(kind, **kw):
    path = C / 'protocols/EXPOSURE.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as f:
        f.write(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                                event=kind, **kw), sort_keys=True) + '\n')


def seed_for(subject):
    return int(hashlib.sha256(subject.encode()).hexdigest()[:8], 16) % (2**31 - 1)


def allocation():
    return json.loads((OLD / 'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json').read_text())


def comparison_ids():
    first = json.loads((OLD / 'artifacts/results/SUBJECT_ORDER.json').read_text())
    second = json.loads((POP / 'protocols/FREEZE.json').read_text())['source_primary_subjects']
    assert len(first) == 40 and len(second) == 24 and not set(first) & set(second)
    return first + second


def historical_check():
    """Every pin in the historical population freeze, with no exclusions."""
    return oldpop.verify_freeze(POP / 'protocols/FREEZE.json')


def load_consumed(subject, cap=4000, purpose='bounded source development reuse'):
    """Only original dev, original40, and the population24; never Pan/short cases.

    Original prepared archives are already fully consumed; returned arrays are
    capped. Mixed files are decoded with first-n SQL/mmap, never beyond4000.
    """
    if not 0 < int(cap) <= 4000:
        raise PermissionError('This campaign source reader is capped at4000')
    alloc = allocation()
    info = {r['subject']:r for r in json.loads((OLD / 'protocols/SPLIT.json').read_text())['standard']}
    first = set(json.loads((OLD / 'artifacts/results/SUBJECT_ORDER.json').read_text()))
    second = set(json.loads((POP / 'protocols/FREEZE.json').read_text())['source_primary_subjects'])
    if subject in alloc['train'] + alloc['validation'] or subject in first:
        row = info[subject]
        path = OLD / 'data/processed' / row['split'] / (subject + '.npz')
        event('reuse_consumed_source', subject=subject, purpose=purpose,
              cap=int(cap), source=str(path.relative_to(ROOT)),
              source_sha256=digest(path), fresh_confirmation=False)
        with np.load(path, allow_pickle=False) as z:
            total = len(z['choice'])
            data = {k:z[k][:cap].copy() for k in z.files
                    if k != 'metadata_json' and z[k].ndim and len(z[k]) == total}
        data['metadata'] = dict(subject=subject, lab=row['lab'],
                                rows_returned=len(data['choice']), cap=int(cap),
                                exposure='previously consumed full indexed history')
        return data
    if subject in second:
        sessions = mixed._sessions(subject)
        event('reuse_consumed_source', subject=subject, purpose=purpose,
              cap=int(cap), source='historical capped mixed original-byte reader',
              fresh_confirmation=False, future_beyond4000_allowed=False)
        data = mixed._read(subject, cap)
        data['metadata'] = dict(subject=subject, lab=sessions[0]['lab'],
                                rows_returned=len(data['choice']), cap=int(cap),
                                exposure='previously consumed first4000 only')
        return data
    raise PermissionError('Not in this campaign consumed-source whitelist: ' + subject)


def prefix_future(data):
    total = len(data['choice'])
    if total < 4000:
        raise ValueError('No full1000+3000 horizon: ' + str(data.get('metadata')))
    prefix = {k:v[:1000].copy() for k,v in data.items()
              if isinstance(v, np.ndarray) and v.ndim and len(v) == total}
    starts = data['session_start'][1000:4000].copy()
    signed = np.nan_to_num(data['contrastRight'][1000:4000]) - np.nan_to_num(data['contrastLeft'][1000:4000])
    observed, counts = oldpop.summarize(signed, data['choice'][1000:4000])
    return prefix, starts, observed[0], counts[0]


def simulate(model, prefix, starts, kind='rnn', policy='standard', n=256,
             seed=0, subject=None):
    global _bank
    if _bank is None:
        _bank = load_bank(BANK)
    common, initial, persistence, calibration = oldpop.make_initial(
        prefix, subject, n, seed, model, _bank)
    rho = float(getattr(model, 'rho', 1.0)) if kind == 'rnn' else 1.0
    out = oldpop.simulate(model, prefix, starts, common, initial, persistence,
                          kind, policy, seed, retention=rho, hidden_retention=rho)
    out['calibration'] = calibration
    return out


def accuracy(samples):
    return np.mean(np.asarray(samples)[..., :2], axis=-1)


def macro_lab_curve_loss(observed, predicted, labs):
    observed, predicted, labs = np.asarray(observed), np.asarray(predicted), np.asarray(labs)
    by_lab = {str(l):float(np.abs((observed[labs == l] - predicted[labs == l]).mean(0)).mean())
              for l in np.unique(labs)}
    return float(np.mean(list(by_lab.values()))), by_lab
