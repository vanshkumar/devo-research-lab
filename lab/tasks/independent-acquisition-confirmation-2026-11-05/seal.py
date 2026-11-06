"""Write-once timestamped source/recipe/access seal, before any evaluation body."""
from common import *
assert not (HERE/'PUBLIC_REQUESTS.jsonl').exists()
assert get(HERE/'PREFLIGHT_CONTROLS.json')['all_passed']
files=[HERE/n for n in ['BRIEF.md','GOAL_START.json','PRE_OUTCOME_FREEZE.md','ACCESS_FOOTPRINT.json',
    'PREFLIGHT_CONTROLS.json','SOURCE_SENSITIVITY_PRESCRIPTIONS.json','common.py','preflight.py','chronology.py','acquire.py','run_confirmation.py','seal.py']]
files+=list((HERE/'banks').glob('*.npz'))
for p in files:read(p)
ms,e,model,canonical,recent=load_prescriptions()
for name,module in list(sys.modules.items()):
    path=getattr(module,'__file__',None)
    if path:
        p=Path(path).resolve()
        if p.is_relative_to(ROOT) and p.suffix=='.py' and 'site-packages' not in str(p):read(p)
fp=get(HERE/'ACCESS_FOOTPRINT.json')
record=dict(utc=utc(),write_once=True,no_evaluation_response_bodies_acquired=True,
    actual_passed_control_sha256=PINS[str((HERE/'PREFLIGHT_CONTROLS.json').relative_to(ROOT))],
    pins=PINS.copy(),animals=192,objects=len(fp['objects']),expected_http_bytes=458383178,
    cumulative_http_ceiling_bytes=500000000,primary_family='three10%proper-score contrasts, origin200, same1001–3000',
    source_draws=[0,14],primary_particles=1024,source_particles=512,streams=[0,10000019],
    initial_stage_cpu_seconds=11100,initial_stage_elapsed_seconds=21600,initial_stage_read_decode_bytes=3000000000)
with (HERE/'PRE_OUTCOME_SEAL.json').open('x') as f:f.write(json.dumps(record,indent=2,default=serial)+'\n')
receipt('SEAL');print(json.dumps({k:v for k,v in record.items() if k!='pins'}))
