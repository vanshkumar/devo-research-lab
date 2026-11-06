import sys,os
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import core as c
from dev_joint import run_case
from common import charge
for i in range(4):charge('primary_request_%d'%(i+1),1000000,'reserved_public_primary_text')
for plant in (101,102):
    d,net=c.load_old(plant);teacher=c.waveform(c.features(d['target'],d['basis'],d['bias']))
    run_case(plant,d,net,teacher,d['initial'],'development')
