"""Record versions and final closeout allowance; no scientific calculation."""
from pathlib import Path
import datetime as dt
import json
import platform
import resource
import sys
import numpy
import scipy

O=Path(__file__).resolve().parent
data=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),python=sys.version,
    executable=sys.executable,platform=platform.platform(),numpy=numpy.__version__,
    scipy=scipy.__version__,new_dependencies=0,numerical_threads=1)
(O/'ENVIRONMENT.json').write_text(json.dumps(data,indent=2)+'\n')
rs=json.loads((O/'RESOURCES.json').read_text())
assert 'final_closeout_additional_allowance_bytes' not in rs
rs.update(utc=data['utc'],native_final_audit_exit=0,
    final_closeout_additional_allowance_bytes=5_000_000,
    cumulative_read_hash_decode_charge_bytes=rs['cumulative_read_hash_decode_charge_bytes']+5_000_000,
    environment_record_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    environment_record_inline_attempt='PreToolUse denied inline code before execution; no payload or numeric pass; preserved rather than bypassed',
    jobs=0)
assert rs['cumulative_read_hash_decode_charge_bytes']<200_000_000
(O/'RESOURCES.json').write_text(json.dumps(rs,indent=2)+'\n')
print(json.dumps(data,indent=2),flush=True)
print(json.dumps(dict(cumulative_charge=rs['cumulative_read_hash_decode_charge_bytes'],jobs=0)),flush=True)
