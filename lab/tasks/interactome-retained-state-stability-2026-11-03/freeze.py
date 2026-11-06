"""Timestamp/hash the ONE protocol before its new outcomes."""
from reference import *

now = datetime.datetime.now(datetime.timezone.utc)
assert now < datetime.datetime(2026,11,3,7,35,34,tzinfo=datetime.timezone.utc)
assert not (OUT/'FREEZE.json').exists()
assert not (OUT/'STABILITY_RESULT.json').exists()
assert not list(OUT.glob('*_continuation.npz'))
names = ['PROTOCOL.md','stability.py','reference.py','REFERENCE.json','INPUT_STATES.npz','SOURCE_REFERENCE.npz']
write('FREEZE.json',{
    'frozen_at_utc':now.isoformat(),
    'new_stability_or_continuation_outcomes_generated_before_freeze':False,
    'substantive_protocol_revisions':0,
    'sha256':{name:sha(OUT/name) for name in names},
    'reused_helper_sha256':sha(REVIEW/'independent_model.py'),
    'original_initial_native_utc':'2026-11-03T07:10:34Z',
    'native_capacity_failure_preserved':True,
    'deadline_or_resource_reset':False,
    'horizon_s':300.,'same_background_pulse_seeds_and_full_model':True
})
print((OUT/'FREEZE.json').read_text())
