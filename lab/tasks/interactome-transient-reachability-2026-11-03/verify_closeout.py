"""Verify saved records/frozen bytes without running a new trajectory."""
import ast
import hashlib
import json
import resource
import time
from datetime import datetime,timezone
from pathlib import Path

START=time.monotonic()
root=Path(__file__).resolve().parent
freeze=json.loads((root/'FREEZE.json').read_text())
for name,sha in freeze['sha256'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha
reference=json.loads((root/'MODEL_REFERENCE.json').read_text())
pilot=json.loads((root/'PILOT_RESULT.json').read_text())
audit=json.loads((root/'OUTPUT_AUDIT.json').read_text())
resources=json.loads((root/'RESOURCES.json').read_text())
for row in pilot['results']:
    assert not row['conditions']['material_retained']
    assert not row['conditions']['material_future_response']
    assert row['conditions']['continuing_drive_positive']
    assert not row['root_check']['attempted']
assert pilot['numerical_control_passed'] and audit['frozen_bytes_unchanged']
assert reference['constants']['N']==279
assert resources['additive_totals']['public_operations']==136+9
assert resources['additive_totals']['charged_ingress_bytes']==634594722+20000000
assert resources['science_exposure']['connectome_units']==1
syntax=[]
for path in sorted(root.glob('*.py')):
    ast.parse(path.read_text());syntax.append(path.name)
required=['RESULT.md','README.md','STATE.md','PROPOSED_LEARNINGS.md','TERMINAL_REPORT.md',
          'SOURCE_MANIFEST.json','NATIVE_EXECUTION.json','PILOT_SUMMARY.csv','OUTPUT_INVENTORY.json']
required += [f'seed{seed}_{kind}.npz' for seed in [0,1] for kind in ['baseline','finite','sham','drive']]
required += ['seed0_literal_baseline.npz','seed0_literal_finite.npz','seed0_literal_sham.npz',
             'DEFAULT_ZERO_reference.npz','PUBLISHED_FWD_PRESET_reference.npz','FWD_20s_reference.npz']
for name in required:assert (root/name).is_file(),name
terminal_words=len((root/'TERMINAL_REPORT.md').read_text().split())
assert terminal_words<=400
json_files=[]
for path in sorted(root.glob('*.json')):
    json.loads(path.read_text());json_files.append(path.name)
result=dict(utc=datetime.now(timezone.utc).isoformat(),status='SAVED_ARTIFACT_CHECKS_PASS_NO_NEW_SCIENCE',
    frozen_files_unchanged=True,required_files=len(required),parsed_json=json_files,parsed_python=syntax,
    terminal_report_words=terminal_words,jobs_remaining=0,
    no_new_trajectory_or_source_request=True,reproduction_entrypoint='statically checked, not executed',
    elapsed_s=time.monotonic()-START,max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(root/'CLOSEOUT_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
