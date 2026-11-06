"""Independent audit of generated optimization evidence.

The feature map, loss, optimizer replay, and frozen dynamics below do not
import run.py or the old preflight's numerical functions. Only the published
models module is loaded to unpickle our own generated circuit objects and to
obtain the separate source-simulation reference when requested.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import pickle
import sys
import types

sys.dont_write_bytecode = True

import numpy as np
from scipy.special import erf
from scipy.sparse import issparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / 'sources/sensory_evaluator_feasibility_2026-10-28/upstream/src'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def features(action, basis, bias):
    """Separate scalar-channel construction for shared-program plants."""
    action = np.asarray(action, dtype=float)
    # Sum in an explicit sequence, independent of the production einsum.
    raw = np.array(bias, dtype=float, copy=True)
    for coordinate in range(action.size):
        raw += basis[:, :, coordinate] * action[coordinate]
    raw = np.maximum(raw, 0.)
    centered = raw - np.sum(raw, axis=1, keepdims=True) / raw.shape[1]
    variance = np.sum(centered ** 2, axis=1, keepdims=True) / raw.shape[1]
    return 2. * centered / np.maximum(np.sqrt(variance), 1e-12)


def target_loss(program, basis, bias, target):
    program = np.asarray(program, dtype=float)
    generated = program[-1] * features(program[:-1], basis, bias)
    target_features = features(target, basis, bias)
    difference = generated - target_features
    return float(np.sum(difference * difference) / difference.size)


def auditory(program, basis, bias, length=1100):
    result = np.zeros((length, 600), dtype=float)
    encoded = float(program[-1]) * features(program[:-1], basis, bias)
    for context in range(6):
        result[50 + 150 * context:150 + 150 * context] = np.repeat(encoded[context], 6)
    return result


def independent_dynamics(net, drive, h_e, h_i, clock, return_state=False):
    """Euler integration with dense explicit contractions, no source sim.

    The source uses sparse dot products and stores every inhibitory state.
    Here sparse matrices are materialized and contractions use einsum with
    optimization disabled. The states used for both derivatives are old states.
    """
    matrices = {}
    dimensions = {'W': (600, 15), 'JEE': (600, 600),
                  'JEI': (600, 150), 'JIE': (150, 600), 'JII': (150, 150)}
    matrix_audit = {}
    for key, shape in dimensions.items():
        value = getattr(net, key)
        assert value.shape == shape, (key, value.shape)
        dense = value.toarray() if issparse(value) else np.array(value)
        assert np.isfinite(dense).all() and (dense >= 0.).all(), key
        if issparse(value):
            assert value.has_canonical_format, key
            assert value.indptr[0] == 0 and value.indptr[-1] == len(value.data)
            assert np.all(np.diff(value.indptr) >= 0)
            assert np.array_equal(dense != 0., value.astype(bool).toarray())
        matrices[key] = dense
        matrix_audit[key] = {'shape': list(shape), 'sparse': bool(issparse(value)),
                             'nonzero': int(np.count_nonzero(dense)),
                             'minimum': float(np.min(dense)),
                             'maximum': float(np.max(dense))}

    def phi(voltage, params):
        maximum, threshold, width = params
        return maximum * (1. + erf((voltage - threshold) / (2. ** .5 * width))) / 2.

    def multiply(name, vector):
        return np.einsum('ij,j->i', matrices[name], vector, optimize=False)

    assert net.NE == 600 and net.NI == 150 and net.NH == 15
    e = np.array(h_e, dtype=float, copy=True)
    i = np.array(h_i, dtype=float, copy=True)
    re, ri = phi(e, net.phiE), phi(i, net.phiI)
    trace = np.empty((len(drive), 600), dtype=float)
    trace[0] = re
    for t in range(1, len(drive)):
        hvc = multiply('W', clock[t - 1])
        if net.w_inh > 0:
            hvc -= net.w_inh * np.sum(clock[t - 1])
        e_derivative = (-e + hvc + drive[t - 1]
                        + multiply('JEE', re) - multiply('JEI', ri))
        i_derivative = -i + multiply('JIE', re) - multiply('JII', ri)
        e += e_derivative / net.tauE
        i += i_derivative / net.tauI
        re, ri = phi(e, net.phiE), phi(i, net.phiI)
        trace[t] = re
    if return_state:
        return (e, i, trace), matrix_audit
    per_context = [float(np.mean(trace[50 + 150 * k:170 + 150 * k])) for k in range(6)]
    return np.array(per_context), matrix_audit


def load_state(path):
    # Display shim only; does not alter numerical source methods.
    shim = types.ModuleType('tqdm')
    shim.tqdm = lambda iterator, *args, **kwargs: iterator
    sys.modules['tqdm'] = shim
    sys.path.insert(0, str(SOURCE))
    with open(path, 'rb') as handle:
        return pickle.load(handle)


def _max_error(left, right):
    left, right = np.asarray(left), np.asarray(right)
    assert left.shape == right.shape, (left.shape, right.shape)
    return float(np.max(np.abs(left - right))) if left.size else 0.


def replay_actor(directory, arm, inputs, search=None):
    """Reconstruct every coordinate proposal and reward-selected transition."""
    with np.load(directory / f'{arm}_queries.npz') as data:
        query = {key: data[key].copy() for key in data.files}
    with np.load(directory / f'{arm}_trajectory.npz') as data:
        trajectory = {key: data[key].copy() for key in data.files}
    summary = json.loads((directory / f'{arm}.json').read_text())
    inferred = 'mixed' if 'actor_config' in summary else 'coordinate'
    if search is None:
        search = inferred
    assert search == inferred, (directory.name, arm, search, inferred)
    n_rounds = len(trajectory['actions']) - 1
    assert len(query['actions']) == 1 + 10 * n_rounds
    assert query['actions'].shape == (1 + 10 * n_rounds, 5)
    assert np.isfinite(query['costs']).all()
    seen = {}
    for action, cost in zip(query['actions'], query['costs']):
        key = np.ascontiguousarray(action).tobytes()
        if key in seen:
            assert cost == seen[key], (directory.name, arm, 'duplicate feedback differs')
        else:
            seen[key] = cost
    execution = summary.get('feedback_execution')
    if execution is not None:
        assert execution['feedback_calls'] == len(query['actions'])
        assert (execution['real_source_calls'] + execution['oracle_evaluations']
                + execution['cache_hits']) == len(query['actions'])
        assert execution['cache_hits'] <= len(query['actions']) - len(seen)
        if arm == 'oracle_joint':
            assert execution['real_source_calls'] == 0
            assert execution['oracle_evaluations'] >= len(seen)
        else:
            assert execution['oracle_evaluations'] == 0
            assert execution['real_source_calls'] >= len(seen)
    initial = np.r_[inputs['initial'], 1.]
    assert np.array_equal(query['actions'][0], initial)
    assert np.array_equal(trajectory['actions'][0], initial)
    assert trajectory['costs'][0] == query['costs'][0]
    assert trajectory['steps'][0] == .4
    assert np.array_equal(trajectory['queries'], 1 + 10 * np.arange(n_rounds + 1))
    lower, upper = np.array([-2., -2., -2., -2., 0.]), np.array([2.] * 5)
    broad = None
    if search == 'mixed':
        plant_id = int(directory.name.split('_')[-1])
        # Independent whole schedule, drawn before reading any reward history.
        broad = np.random.default_rng(71000 + plant_id).uniform(
            lower, upper, size=(32, 10, 5))
        expected_digest = hashlib.sha256(broad.tobytes()).hexdigest()
        assert summary['broad_candidates_sha256'] == expected_digest
        assert summary['actor_script_sha256'] == digest(HERE / 'run_mixed.py')
        assert summary['actor_config']['name'] == 'mixed_global_coordinate_v1'
        expected_types = ['initial'] + [
            'global' if (r + 1) % 4 == 0 else 'local' for r in range(n_rounds)]
        assert np.array_equal(trajectory['round_types'], expected_types)
    assert (query['actions'] >= lower).all() and (query['actions'] <= upper).all()
    if arm.endswith('_fixed'):
        assert np.all(query['actions'][:, -1] == 1.)
    current = initial.copy()
    current_cost = query['costs'][0]
    step = .4
    accepted = 0
    reward_improvements_with_worse_target = 0
    accepted_target_losses = []
    for round_index in range(n_rounds):
        offset = 1 + 10 * round_index
        global_round = search == 'mixed' and (round_index + 1) % 4 == 0
        if global_round:
            proposals = broad[round_index // 4].copy()
            if arm.endswith('_fixed'):
                proposals[:, 4] = 1.
        else:
            proposals = []
            for coordinate in range(5):
                for direction in (1., -1.):
                    candidate = current.copy()
                    if not (arm.endswith('_fixed') and coordinate == 4):
                        candidate[coordinate] += direction * step
                    proposals.append(np.minimum(np.maximum(candidate, lower), upper))
        assert np.array_equal(query['actions'][offset:offset + 10], proposals), (
            directory.name, arm, round_index, 'global' if global_round else 'local')
        proposed_costs = query['costs'][offset:offset + 10]
        best = int(np.argmin(proposed_costs))
        if proposed_costs[best] < current_cost:
            old_loss = target_loss(current, inputs['basis'], inputs['bias'], inputs['target'])
            current = query['actions'][offset + best].copy()
            current_cost = proposed_costs[best]
            new_loss = target_loss(current, inputs['basis'], inputs['bias'], inputs['target'])
            reward_improvements_with_worse_target += int(new_loss > old_loss + 1e-12)
            accepted_target_losses.append([float(old_loss), float(new_loss)])
            accepted += 1
            if global_round:
                step = .4
        elif not global_round:
            step = max(.00625, step / 2.)
        assert np.array_equal(trajectory['actions'][round_index + 1], current)
        assert trajectory['costs'][round_index + 1] == current_cost
        assert trajectory['steps'][round_index + 1] == step
    expected_query_losses = np.array([
        target_loss(action, inputs['basis'], inputs['bias'], inputs['target'])
        for action in query['actions']])
    expected_trajectory_losses = np.array([
        target_loss(action, inputs['basis'], inputs['bias'], inputs['target'])
        for action in trajectory['actions']])
    loss_error = max(_max_error(expected_query_losses, query['true_losses']),
                     _max_error(expected_trajectory_losses, trajectory['true_losses']))
    assert loss_error < 1e-10, (directory.name, arm, loss_error)
    if arm == 'oracle_joint':
        assert _max_error(expected_query_losses, query['costs']) < 1e-10
    assert summary['rounds'] == n_rounds
    assert summary['queries'] == len(query['actions'])
    assert summary['query_budget_expected'] == 1 + 10 * n_rounds
    assert summary['final_cost'] == current_cost
    assert summary['final_step'] == step
    assert np.array_equal(summary['final_action'], current)
    assert abs(summary['initial_true_loss'] - expected_trajectory_losses[0]) < 1e-10
    assert abs(summary['final_true_loss'] - expected_trajectory_losses[-1]) < 1e-10
    if expected_trajectory_losses[0]:
        expected_ratio = expected_trajectory_losses[-1] / expected_trajectory_losses[0]
        assert abs(summary['normalized_final_true_loss'] - expected_ratio) < 1e-10
    with open(directory / f'{arm}_checkpoint.pkl', 'rb') as handle:
        actor = pickle.load(handle)
    allowed_keys = {'config', 'x', 'cost', 'step', 'round', 'query_actions',
                    'query_costs', 'trajectory_actions', 'trajectory_costs',
                    'trajectory_steps', 'trajectory_queries', 'feedback_execution',
                    'actor_config', 'broad_candidates_sha256', 'actor_script_sha256',
                    'trajectory_round_types'}
    assert set(actor).issubset(allowed_keys), (directory.name, arm, set(actor) - allowed_keys)
    assert np.array_equal(actor['query_actions'], query['actions'])
    assert np.array_equal(actor['query_costs'], query['costs'])
    assert np.array_equal(actor['trajectory_actions'], trajectory['actions'])
    assert np.array_equal(actor['x'], current)
    assert actor['cost'] == current_cost and actor['step'] == step
    assert actor['round'] == n_rounds
    if search == 'mixed':
        assert actor['actor_config'] == summary['actor_config']
        assert actor['broad_candidates_sha256'] == expected_digest
        assert actor['actor_script_sha256'] == summary['actor_script_sha256']
        assert np.array_equal(actor['trajectory_round_types'], trajectory['round_types'])
    return {'search': search, 'rounds': n_rounds, 'queries': len(query['actions']),
            'unique_action_queries': len(seen), 'feedback_execution': execution,
            'accepted_updates': accepted,
            'reward_improvements_with_target_deterioration': reward_improvements_with_worse_target,
            'loss_max_error': loss_error,
            'initial_true_loss': float(expected_trajectory_losses[0]),
            'final_true_loss': float(expected_trajectory_losses[-1]),
            'terminal_gain': float(current[-1]),
            'final_action': current.tolist()}, query, trajectory


def verify_plant(directory, dynamics=False, search=None):
    plant_id = int(directory.name.split('_')[-1])
    preparation = json.loads((directory / 'preparation.json').read_text())
    with np.load(directory / 'inputs.npz') as data:
        inputs = {key: data[key].copy() for key in data.files}
    if directory.parent.name == 'mixed_results':
        original = HERE / 'results' / directory.name
        for filename in ('inputs.npz', 'state.pkl', 'preparation.json'):
            assert digest(directory / filename) == digest(original / filename)
    # Independent reconstruction fixes every draw in its declared order. There
    # is no redraw, target-conditioned basis or target-relative initialization.
    rng = np.random.default_rng(31000 + plant_id)
    expected = dict(basis=rng.normal(size=(6, 100, 4)) / 2.,
                    bias=rng.normal(-.4, .2, (6, 100)),
                    target=rng.uniform(-1., 1., 4),
                    initial=rng.uniform(-1., 1., 4))
    for key, value in expected.items():
        assert np.array_equal(inputs[key], value), (directory.name, key)
    assert inputs['seed'].item() == 31000 + plant_id
    assert np.array_equal(inputs['on'], 50 + 150 * np.arange(6))
    assert np.array_equal(inputs['off'], 150 + 150 * np.arange(6))
    assert np.max(np.abs(inputs['target'])) <= 1.
    exact_target = np.r_[inputs['target'], 1.]
    target_l = target_loss(exact_target, inputs['basis'], inputs['bias'], inputs['target'])
    assert target_l == 0.
    zero_program = exact_target.copy()
    zero_program[-1] = 0.
    target_energy = np.mean(features(inputs['target'], inputs['basis'], inputs['bias']) ** 2)
    assert abs(target_loss(zero_program, inputs['basis'], inputs['bias'], inputs['target']) - target_energy) < 1e-12
    assert preparation['target_reachable_true_loss'] == 0.
    for path, expected_hash in preparation['source_hashes'].items():
        assert digest(ROOT / path) == expected_hash, path
    result = dict(plant_id=plant_id, seed=31000 + plant_id,
                  target_reachability_loss=target_l,
                  target_feature_energy=float(target_energy),
                  arms={}, dynamics=[])
    loaded = {}
    for path in sorted(directory.glob('*_trajectory.npz')):
        arm = path.name.removesuffix('_trajectory.npz')
        audit, query, trajectory = replay_actor(directory, arm, inputs, search)
        result['arms'][arm] = audit
        loaded[arm] = (query, trajectory)
    assert result['arms'], directory
    if dynamics:
        state = load_state(directory / 'state.pkl')
        for key in ('basis', 'bias', 'target', 'initial'):
            assert np.array_equal(state[key], inputs[key])
        independent_target = features(inputs['target'], inputs['basis'], inputs['bias'])
        assert _max_error(independent_target, state['target_features']) < 1e-12
        assert state['rh'].shape == (1100, 15)
        # Reconstruct the supplied one-rendition clock without helper imports.
        time_grid = np.arange(1600, dtype=float)[:, None]
        burst_centers = 500. + 60. * np.arange(15, dtype=float)[None, :]
        clock_full = 150. * np.exp(-(time_grid - burst_centers) ** 2 / 800.)
        assert _max_error(clock_full[500:], state['rh']) < 1e-12
        # Tutoring changes only the two plastic recurrent matrices. The other
        # matrices share exact original bytes across exposure/control arms.
        untrained = state['nets']['untutored']
        for evaluator, net in state['nets'].items():
            for matrix in ('W', 'JEE', 'JII'):
                assert (getattr(net, matrix) != getattr(untrained, matrix)).nnz == 0
            (burn_e, burn_i, _), _ = independent_dynamics(net,
                np.zeros((500, 600)), state['initial_hE'], state['initial_hI'],
                clock_full[:500], return_state=True)
            h = state['probe_states'][evaluator]
            burn_error = max(_max_error(burn_e, h['hE']), _max_error(burn_i, h['hI']))
            assert burn_error < 1e-9, (directory.name, evaluator, burn_error)
            result.setdefault('burn_state_errors', {})[evaluator] = burn_error
        selected = [('learned35_joint', 'initial'), ('learned35_joint', 'final'),
                    ('learned140_joint', 'final'), ('shuffled35_joint', 'final'),
                    ('untutored_joint', 'final')]
        for arm, location in selected:
            if arm not in loaded:
                continue
            evaluator = arm.rsplit('_', 1)[0]
            net = state['nets'][evaluator]
            h = state['probe_states'][evaluator]
            query, trajectory = loaded[arm]
            index = 0 if location == 'initial' else -1
            program = trajectory['actions'][index]
            drive = auditory(program, inputs['basis'], inputs['bias'])
            reconstructed, matrices = independent_dynamics(net, drive, h['hE'], h['hI'], state['rh'])
            # Source comparison is separate from the independently generated
            # scalar and additionally checks complete per-context integration.
            source = net.sim(h['hE'], h['hI'], state['rh'], drive, [], 1100, 1, 0,
                             no_progress_bar=True)[0]
            source_contexts = np.array([source[50 + 150*k:170 + 150*k].mean() for k in range(6)])
            source_error = _max_error(reconstructed, source_contexts)
            saved_error = abs(float(reconstructed.mean()) - trajectory['costs'][index])
            assert source_error < 1e-9, (directory.name, arm, source_error)
            assert saved_error < 1e-9, (directory.name, arm, saved_error)
            result['dynamics'].append(dict(arm=arm, location=location,
                independent_cost=float(reconstructed.mean()),
                saved_cost=float(trajectory['costs'][index]),
                independent_source_context_max_error=source_error,
                independent_saved_cost_error=float(saved_error), matrices=matrices))
        # Exact target has no special treatment in the circuit verifier.
        for evaluator in ('learned35', 'learned140'):
            net = state['nets'][evaluator]
            h = state['probe_states'][evaluator]
            target_scores, matrices = independent_dynamics(net,
                auditory(exact_target, inputs['basis'], inputs['bias']), h['hE'], h['hI'], state['rh'])
            saved = preparation['target_costs'][evaluator]
            target_error = _max_error(target_scores, saved['contexts'])
            assert target_error < 1e-9
            result['dynamics'].append(dict(arm=evaluator+'_exact_target', location='target',
                independent_cost=float(target_scores.mean()),
                independent_saved_context_max_error=target_error, matrices=matrices))
    return result


def verify_diagnostics(plant_id, diagnostic_directory, dynamics=False):
    """Independent reconstruction of the separate exact-target probe series."""
    path = diagnostic_directory / f'plant_{plant_id:03d}.npz'
    meta = json.loads(path.with_suffix('.json').read_text())
    with np.load(path) as data:
        queries = {key: data[key].copy() for key in data.files}
    source_directory = Path(meta['source_directory'])
    assert source_directory.name == f'plant_{plant_id:03d}'
    assert digest(source_directory / 'state.pkl') == meta['source_state_sha256']
    assert meta['script_sha256'] == digest(HERE / 'diagnose.py')
    assert meta['plant_id'] == plant_id
    for source, expected_hash in meta['source_hashes'].items():
        assert digest(ROOT / source) == expected_hash
    with np.load(source_directory / 'inputs.npz') as data:
        inputs = {key: data[key].copy() for key in data.files}
    rng = np.random.default_rng(31000 + plant_id)
    for key, expected in (
            ('basis', rng.normal(size=(6, 100, 4)) / 2.),
            ('bias', rng.normal(-.4, .2, (6, 100))),
            ('target', rng.uniform(-1., 1., 4)),
            ('initial', rng.uniform(-1., 1., 4))):
        assert np.array_equal(inputs[key], expected), (plant_id, key)
    center = np.r_[inputs['target'], 1.]
    assert np.array_equal(queries['target_program'], center)
    assert np.array_equal(queries['evaluators'], ['learned35', 'learned140'])
    expected_types = ['center'] + [f'{sign}_{d}' for d in range(5)
                                  for sign in ('plus', 'minus')] + ['downhill_step']
    assert np.array_equal(queries['query_types'], expected_types)
    assert queries['query_actions'].shape == (2, 12, 5)
    assert queries['query_costs'].shape == (2, 12)
    assert queries['query_true_losses'].shape == (2, 12)
    assert queries['gradients'].shape == (2, 5)
    assert np.isfinite(queries['query_costs']).all()
    assert meta['diagnostic_config']['finite_difference'] == .025
    assert meta['diagnostic_config']['downhill_step_norm'] == .05
    assert meta['diagnostic_config']['memoization'] is False
    state = load_state(source_directory / 'state.pkl') if dynamics else None
    result = {'plant_id': plant_id, 'evaluators': {},
              'diagnostic_source_state_sha256': meta['source_state_sha256']}
    lower, upper = np.array([-2., -2., -2., -2., 0.]), np.array([2.] * 5)
    for index, evaluator in enumerate(queries['evaluators']):
        actions = queries['query_actions'][index]
        costs = queries['query_costs'][index]
        assert np.array_equal(actions[0], center)
        for dimension in range(5):
            plus, minus = center.copy(), center.copy()
            plus[dimension] += .025
            minus[dimension] -= .025
            assert np.array_equal(actions[1 + 2*dimension], plus)
            assert np.array_equal(actions[2 + 2*dimension], minus)
        gradient = (costs[1:11:2] - costs[2:12:2]) / .05
        assert _max_error(gradient, queries['gradients'][index]) < 1e-12
        norm = float(np.sqrt(np.sum(gradient * gradient)))
        stepped = center.copy()
        if norm > 0.:
            stepped = np.minimum(np.maximum(center - .05*gradient/norm, lower), upper)
        assert _max_error(stepped, actions[-1]) < 1e-14
        losses = np.array([target_loss(action, inputs['basis'], inputs['bias'], inputs['target'])
                           for action in actions])
        loss_error = _max_error(losses, queries['query_true_losses'][index])
        assert loss_error < 1e-10
        assert losses[0] == 0.
        row = meta['evaluators'][str(evaluator)]
        assert row['target_true_mse'] == 0.
        assert row['feedback_queries'] == 12 and row['real_source_calls'] == 12
        assert row['cache_hits'] == 0
        assert row['target_cost'] == costs[0] and row['next_cost'] == costs[-1]
        assert abs(row['gradient_norm'] - norm) < 1e-10
        assert _max_error(row['gradient'], gradient) < 1e-12
        assert abs(row['next_true_mse'] - losses[-1]) < 1e-10
        dynamics_error = None
        independent_costs = []
        if dynamics:
            net = state['nets'][str(evaluator)]
            h = state['probe_states'][str(evaluator)]
            for action in actions:
                contexts, _ = independent_dynamics(net,
                    auditory(action, inputs['basis'], inputs['bias']), h['hE'], h['hI'], state['rh'])
                independent_costs.append(float(contexts.mean()))
            dynamics_error = _max_error(independent_costs, costs)
            assert dynamics_error < 1e-9, (plant_id, evaluator, dynamics_error)
            own_gradient = (np.array(independent_costs)[1:11:2]
                            - np.array(independent_costs)[2:12:2]) / .05
            assert _max_error(own_gradient, gradient) < 1e-7
        result['evaluators'][str(evaluator)] = dict(
            feedback_queries=12, independent_true_loss_max_error=loss_error,
            independent_dynamics_max_error=dynamics_error,
            independent_dynamics_probes=len(independent_costs),
            target_cost=float(costs[0]), next_cost=float(costs[-1]),
            next_true_mse=float(losses[-1]), gradient_norm=norm,
            gradient_gain_component=float(gradient[-1]))
    assert meta['feedback_queries_total'] == 24
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plants', type=int, nargs='*',
                        help='Default: every complete plant with at least one arm.')
    parser.add_argument('--base-dir', type=Path, default=HERE / 'results',
                        help='Use mixed_results for the revised actor.')
    parser.add_argument('--search', choices=['coordinate', 'mixed'],
                        help='Optional assertion; default infers stored actor metadata.')
    parser.add_argument('--required-rounds', type=int,
                        help='Fail if any audited arm has fewer rounds.')
    parser.add_argument('--require-all-arms', action='store_true',
                        help='Require all six declared arms on every selected plant.')
    parser.add_argument('--diagnostics', type=Path, nargs='?',
                        const=HERE / 'diagnostic_results',
                        help='Also audit matching exact-target diagnostic outputs.')
    parser.add_argument('--dynamics-plants', type=int, nargs='*', default=[0, 100],
                        help='Plant IDs for independent dense dynamics checks.')
    parser.add_argument('--output', type=Path, default=HERE / 'VERIFICATION.json')
    args = parser.parse_args()
    args.base_dir = args.base_dir.resolve()
    args.output = args.output.resolve()
    if args.diagnostics is not None:
        args.diagnostics = args.diagnostics.resolve()
    directories = ([args.base_dir / f'plant_{plant:03d}' for plant in args.plants]
                   if args.plants else sorted(args.base_dir.glob('plant_*')))
    if args.plants:
        for directory in directories:
            assert (directory / 'preparation.json').exists(), directory
            assert list(directory.glob('*_trajectory.npz')), directory
    directories = [d for d in directories if (d / 'preparation.json').exists()
                   and list(d.glob('*_trajectory.npz'))]
    if not directories:
        raise SystemExit('No completed plant outputs available.')
    tracked = sorted(p for d in directories for p in d.iterdir()
                     if p.is_file() and not p.name.endswith('.tmp'))
    if args.diagnostics:
        for directory in directories:
            for suffix in ('.npz', '.json'):
                path = args.diagnostics / (directory.name + suffix)
                assert path.exists(), path
                tracked.append(path)
    before = {str(p.relative_to(HERE)): digest(p) for p in tracked}
    code_before = {path.name: digest(path) for path in [HERE / 'run.py', HERE / 'run_mixed.py']
                   if path.exists()}
    rows = [verify_plant(directory,
                         int(directory.name.split('_')[-1]) in args.dynamics_plants,
                         args.search)
            for directory in directories]
    declared_arms = {'oracle_joint', 'learned35_joint', 'learned35_fixed',
                     'learned140_joint', 'untutored_joint', 'shuffled35_joint'}
    for row in rows:
        if args.require_all_arms:
            assert set(row['arms']) == declared_arms, (row['plant_id'], set(row['arms']))
        if args.required_rounds is not None:
            assert all(arm['rounds'] >= args.required_rounds for arm in row['arms'].values())
    diagnostic_rows = [verify_diagnostics(row['plant_id'], args.diagnostics,
                                          row['plant_id'] in args.dynamics_plants)
                       for row in rows] if args.diagnostics else []
    after = {str(p.relative_to(HERE)): digest(p) for p in tracked}
    assert before == after, 'Read generated evidence changed during verification.'
    assert code_before == {name: digest(HERE / name) for name in code_before}
    output = dict(status='pass', plants=rows, plants_checked=len(rows),
                  arms_checked=sum(len(r['arms']) for r in rows),
                  full_query_losses_and_optimizer_replay=True,
                  seeded_plant_target_and_blind_initialization_reconstruction=True,
                  source_files_unchanged=True, evidence_unchanged=True,
                  independent_dynamics_probes=sum(len(r['dynamics']) for r in rows),
                  diagnostics=diagnostic_rows,
                  diagnostic_independent_dynamics_probes=sum(
                      evaluator['independent_dynamics_probes']
                      for row in diagnostic_rows for evaluator in row['evaluators'].values()),
                  verification_code_sha256=digest(__file__),
                  production_code_sha256=digest(HERE / 'run.py'),
                  all_production_code_sha256=code_before,
                  base_directory=str(args.base_dir.resolve()),
                  evidence_sha256=before,
                  limitations=[
                      'Same simulated plants, not an independent empirical replication.',
                      'Training plasticity is source code; it is not independently reimplemented.',
                      'Frozen dynamics is independently checked only for declared selected plants/probes.',
                      'Target-blindness combines seeded input reconstruction, optimizer replay and code inspection; no sandbox separation is claimed.'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({key: value for key, value in output.items()
                      if key not in ('plants', 'diagnostics', 'evidence_sha256')}, indent=2))


if __name__ == '__main__':
    main()
