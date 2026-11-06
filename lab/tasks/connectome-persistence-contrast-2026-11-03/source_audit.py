"""Offline source pin and call-site audit; does not simulate any neural model."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import resource
import time

ROOT = Path(__file__).resolve().parent
start = time.monotonic()
pins = []
for expected in json.loads((ROOT / 'sources/expected-blobs.json').read_text()):
    data = (ROOT / 'sources' / expected['path']).read_bytes()
    git_hash = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    pins.append({**expected, 'actual_bytes': len(data), 'actual_git_blob_sha1': git_hash,
                 'sha256': hashlib.sha256(data).hexdigest(), 'matches': git_hash == expected['sha']})

source = (ROOT / 'sources/interactome-initialize.py').read_text()
tree = ast.parse(source)
constants = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id in {'N', 'Gc', 'C', 'Ec', 'ar', 'ad', 'B', 'Iext', 'rate', 'offset'}:
            constants[node.targets[0].id] = ast.unparse(node.value)

functions = {}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in {
        'transit_Mask', 'update_Mask', 'membrane_voltageRHS', 'voltage_filter', 'run_Network', 'EffVth', 'EffVth_rhs'
    }:
        functions[node.name] = {'line': node.lineno, 'end_line': node.end_lineno}

assert constants['N'] == '279'
assert 'Vth_Static = EffVth_rhs(Iext, newMask)' in source
assert 'InMask = newMask' in source
assert 'E = -48.0 * E' in source
assert 'InitCond = 10**(-4)*np.random.normal(0, 0.94, 2*N)' in source
usage = resource.getrusage(resource.RUSAGE_SELF)
out = {
    'status': 'SOURCE_AUDIT_ONLY_NO_MODEL_RUN',
    'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'pins': pins, 'constants_as_source': constants, 'function_lines': functions,
    'release_tree': 'bdb94ca174980e46777f7b1936f539903c688719',
    'facts': {
        'neurons': 279, 'dynamic_variables_claimed_by_primary_paper': 558,
        'synaptic_gate_constants_differ_from_2017_table': True,
        'inhibitory_potential_source_minus48_2017_table_minus45': True,
        'input_update_recomputes_Vth': True,
        'mask_set_to_new_constant_after_transition_window': True,
        'readout_tanh_of_voltage_minus_input_dependent_threshold': True,
        'original_2017_connectivity_equivalence_certified': False,
        'original_full_model_or_independent_numerical_reference_executed': False
    },
    'elapsed_wall_s': time.monotonic() - start,
    'cpu_s': usage.ru_utime + usage.ru_stime,
    'max_rss_bytes_macos': usage.ru_maxrss,
    'read_bytes_explicit_payload': sum(p['actual_bytes'] for p in pins),
    'resource_note': 'Explicit source payload only, excluding repeated reads, expected metadata, interpreter and context. No complete-I/O claim.'
}
(ROOT / 'SOURCE_AUDIT.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({'status': out['status'], 'pin_matches': [p['matches'] for p in pins],
                  'utc': out['utc'], 'rss': out['max_rss_bytes_macos'], 'cpu_s': out['cpu_s']}))
