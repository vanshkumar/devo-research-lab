"""Verify saved evidence; optionally replay scientific sources into a fresh subdir."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
import hashlib,json,runpy,shutil,sys,resource
from datetime import datetime,timezone
from pathlib import Path
os.environ['MPLCONFIGDIR']=str(Path(__file__).resolve().parent/'mpl_cache')
import numpy as np
import scipy
import matplotlib
import threadpoolctl
from threadpoolctl import threadpool_limits

HERE=Path(__file__).resolve().parent
IGNORED={'created_utc','peak_rss_bytes','charged_additional_read_decoded_hash_bytes','charged_read_decode_hash_bytes',
         'charged_read_decoded_hash_bytes','charge','frozen_at_utc','freeze_sha256'}

def compare(a,b,path=''):
    if isinstance(a,dict):
        assert set(a)==set(b),(path,set(a)^set(b))
        for k in a:
            if k not in IGNORED:compare(a[k],b[k],path+'/'+k)
    elif isinstance(a,list):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+f'/{i}')
    elif isinstance(a,(int,float)) and not isinstance(a,bool):
        assert np.isfinite(a) and np.isfinite(b) and abs(a-b)<=1e-11*(1+abs(a)),(path,a,b)
    else:assert a==b,(path,a,b)

def main():
    frozen=json.loads((HERE/'SOURCE_ONLY_FREEZE.json').read_text())
    for name,h in frozen['files'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h,name
    v=json.loads((HERE/'SUPPORT_WITNESS.json').read_text())
    assert v['target_outcome_numeric_values_decoded']==0 and v['freeze_pins_verified']
    endpoint=json.loads((HERE/'ENDPOINT_CONTROL.json').read_text())
    for channel,out in endpoint['matched_transfer'].items():
        q=[]
        for s in (endpoint['sources'][0],endpoint['sources'][2]):
            q.append(sum(p['effects']['Jump To'][channel] for p in s['people'])/sum(p['effects']['No Jump'][channel] for p in s['people']))
        assert abs(q[1]-q[0]-out['ratio_shift'])<1e-12
    result=dict(created_utc=datetime.now(timezone.utc).isoformat(),freeze_files_verified=len(frozen['files']),
        saved_scalar_reconstructions_pass=True,figure4_outcome_values_decoded_this_verification=0,
        raw_source_files_opened_this_verification=0,
        environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__,threadpoolctl=threadpoolctl.__version__),
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if '--sources' in sys.argv:
        # This mode costs approximately270MB additional scientific-byte allowance.
        # It is supplied for a separately allocated replay, not run in the original tranche.
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        out=HERE/'replay'/stamp;out.mkdir(parents=True,exist_ok=False)
        for name in list(frozen['files'])+['SOURCE_ANALYSIS_INITIAL_WARNINGS.json']:
            if name.endswith(('.py','.md')) or name=='SOURCE_ANALYSIS_INITIAL_WARNINGS.json':shutil.copy2(HERE/name,out/name)
        sys.path.insert(0,str(HERE))
        outputs=[('source_support.py','SOURCE_SUPPORT.json'),('source_analysis.py','SOURCE_ANALYSIS.json'),
                 ('endpoint_control.py','ENDPOINT_CONTROL.json'),('prescription_check.py','PRESCRIPTION_CHECK.json'),
                 ('measurement_sensitivity.py','MEASUREMENT_SENSITIVITY.json')]
        for code,artifact in outputs:
            mod=runpy.run_path(str(HERE/code),run_name='motor_replay')
            mod['main'].__globals__['HERE']=out
            mod['main']()
            compare(json.loads((HERE/artifact).read_text()),json.loads((out/artifact).read_text()),artifact)
        mod=runpy.run_path(str(HERE/'support_witness.py'),run_name='motor_replay')
        mod['main'].__globals__['HERE']=out
        mod['freeze']();mod['main']()
        compare(json.loads((HERE/'SUPPORT_WITNESS.json').read_text()),json.loads((out/'SUPPORT_WITNESS.json').read_text()),'SUPPORT_WITNESS.json')
        result.update(full_source_replay_pass=True,replay_path=str(out),raw_source_files_opened_this_verification=4,
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        (out/'COMPARISON.json').write_text(json.dumps(result,indent=2)+'\n')
    (HERE/'REPRODUCE_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=1):main()
