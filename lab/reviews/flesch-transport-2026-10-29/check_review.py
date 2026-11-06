"""Offline source/hash and selection-likelihood witnesses. No data-array loader."""
import ast
import hashlib
import itertools
import json
import math
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
checks = []
def check(value, label):
    if not value:
        raise AssertionError(label)
    checks.append(label)

tree = json.loads((ROOT / 'model_tree.json').read_text())
manifest = {x['path']: x for x in tree['tree']}
for path in ROOT.glob('model_code__*'):
    original = path.name.removeprefix('model_code__').replace('__', '/')
    body = path.read_bytes()
    gitsha = hashlib.sha1(('blob %d\0' % len(body)).encode() + body).hexdigest()
    check(gitsha == manifest[original]['sha'], '2023 Git blob: ' + original)

oldtree = json.loads((REPO / 'sources/fixed_training_evidence_2026-10-29/flesch_tree.json').read_text())
oldblobs = {x['sha'] for x in oldtree['tree'] if x['type'] == 'blob'}
for name in ['flesch_parameters.js', 'flesch_conditions.js', 'flesch_response.js', 'flesch_show.js', 'flesch_run.js', 'flesch_parser.m', 'flesch_reshape.m', 'flesch_rename.m']:
    body = (REPO / 'sources/fixed_training_evidence_2026-10-29' / name).read_bytes()
    check(hashlib.sha1(('blob %d\0' % len(body)).encode()+body).hexdigest() in oldblobs, '2018 original Git blob: ' + name)

trainer = ast.parse((ROOT / 'model_code__hebbcl__trainer.py').read_text())
optim = next(x for x in trainer.body if isinstance(x, ast.ClassDef) and x.name == 'Optimiser')
step = next(x for x in optim.body if isinstance(x, ast.FunctionDef) and x.name == 'step')
check([x.arg for x in step.args.args] == ['self', 'model', 'x_in', 'r_target'], 'optimizer accepts scheduled target, no sampled choice')
calls = [x.func.attr for x in ast.walk(step) if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)]
check('_sgd_update' in calls and '_oja_update' in calls and '_oja_ctx_update' in calls, 'supervised plus distinct all-input/context-only Oja paths available')
data_src = (ROOT / 'model_code__utils__data.py').read_text()
check(data_src.count('.ewm(alpha=args.ctx_avg_alpha, adjust=False, min_periods=1)') == 4, 'EMA alpha is current observation weight in both generators')
check('data["x_test_a"][:, -2] = (' not in data_src and 'data["x_test_b"][:, -2] = (' not in data_src, 'supplied dataset generators smooth train context, not test context')

# Exact integer form of the strict >55% criterion avoids binary rounding.
threshold = lambda n: (11*n)//20+1
check(threshold(160) == 89 and 20*88 == 11*160, 'strict threshold excludes exactly 88/160')
check(threshold(158) == 87, 'dropping two NaN omissions changes threshold to 87/158')
check(20*88 > 11*158 and not 20*88 > 11*160, '88 correct plus two omitted can change inclusion')

# Four-test-trial history dependence: correctness has 0.9 persistence.
probs = {}
for ys in itertools.product((0, 1), repeat=4):
    prob = F(1,2)
    for prev, y in zip(ys, ys[1:]):
        p = F(9,10) if prev else F(1,10)
        prob *= p if y else (1-p)
    probs[ys] = prob
selected = {ys:p for ys,p in probs.items() if sum(ys) >= threshold(4)}
normalizer = sum(selected.values(), F(0))
independent_normalizer = sum(F(math.comb(4,k),16) for k in range(threshold(4),5))
check(sum(probs.values()) == 1, 'enumerated history law sums to one')
check(normalizer != independent_normalizer, 'independent marginal Bernoullis give wrong selection probability')
check(sum(p/normalizer for p in selected.values()) == 1, 'history-aware selected trajectory law normalizes')

# Independently compute the same selection event by finite-state recursion.
states = {(None,0):F(1)}
for t in range(4):
    new = {}
    for (last,k), mass in states.items():
        p = F(1,2) if last is None else F(9,10) if last else F(1,10)
        for y, py in ((1,p),(0,1-p)):
            key = (y,k+y)
            new[key] = new.get(key,F(0)) + mass*py
    states = new
dp_norm = sum(m for (_,k),m in states.items() if k >= threshold(4))
check(dp_norm == normalizer, 'independent recursion equals exhaustive trajectory sum')

# Heterogeneous population: normalize after integrating the preselection mixture.
weak, strong = F(2,5), F(4,5)
a = lambda p: 3*p*p*(1-p)+p**3
j = lambda p: p*p*(1-p)  # the selected trajectory 110
right = (j(weak)+j(strong))/(a(weak)+a(strong))
wrong = (j(weak)/a(weak)+j(strong)/a(strong))/2
check(right != wrong, 'ratio of integrals differs from averaging individually truncated laws')
selected_strong = a(strong)/(a(weak)+a(strong))
check(selected_strong != F(1,2), 'selection reweights latent types')

result = {
    'passed': True, 'checks': len(checks), 'check_names': checks,
    'history_witness': {'n':4, 'strict_threshold':threshold(4), 'history_selection_probability':float(normalizer), 'independent_marginals_probability':float(independent_normalizer)},
    'mixture_witness': {'correct_selected_probability_110':float(right), 'wrong_mean_of_truncated_probabilities':float(wrong), 'selected_strong_type_probability':float(selected_strong)},
    'scope':'Original code text/hash checks and synthetic exact arithmetic only; no human numeric arrays, fits or forecasts.'
}
(ROOT / 'review_checks.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
