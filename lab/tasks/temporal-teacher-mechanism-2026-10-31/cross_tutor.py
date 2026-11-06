import sys,os
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import pickle,json
import core as c
from dev_joint import run_case
from common import ROOT,read,save
all_results=[]
for plant,stretch in ((100,.84),(101,.92),(102,1.16)):
    d,net=c.load_old(plant);teacher=c.waveform(c.features(d['target'],d['basis'],d['bias']),stretch,phase=37)
    net0=None
    if plant==100:
        state=pickle.loads(read(ROOT/'campaigns/evaluator_optimization_2026-10-28/primary_snapshots/plant_100/state.pkl','consumed_unplasticized_control'))
        net0=state['nets']['untutored']
    result=run_case(plant,d,net,teacher,d['initial'],'cross_tutor',net0=net0)
    all_results.append({'plant':plant,'tutor_stretch_environment_only':stretch,'results':result['results']})
save('outputs/CROSS_TUTOR.json',{'results':all_results,'scope':'fixed previously trained feature circuits, new sensory goal memories; raw/normalized weights remain stale, not a fair original-circuit-retutoring claim'})
