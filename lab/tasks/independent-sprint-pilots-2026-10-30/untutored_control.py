"""Matched zero-HVC control on explicitly selected successful pilot cases."""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import argparse,json,time,resource
import numpy as np
import teaching_pilot as p
from common import HERE,save,now

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--plant',type=int,choices=[100,102],required=True);args=ap.parse_args()
    start=time.monotonic();state=p.load(args.plant)
    callback,_,calls=p.evaluator(state,{'net':state['nets']['untutored']},'no_clock')
    initial=np.r_[state['initial'],1.]
    actor=p.search_per_order(callback,initial,80000+args.plant,20)
    actual=np.array([p.true_loss(a,state) for a in actor['actions']])
    queried=np.array([p.true_loss(a,state) for a in actor['query_actions']])
    assert len(queried)==1206
    corrected=actor['actions'][-1].copy();corrected[4]=0
    result={'plant':args.plant,'mode':'untutored_no_clock','queries':len(queried),
            'initial_loss':float(actual[0]),'final_loss':float(actual[-1]),
            'improvement':float(1-actual[-1]/actual[0]),'final_order':int(actor['actions'][-1,4]),
            'offline_canonical_order_content_mse':p.true_loss(corrected,state),
            'feedback':calls,'seconds':time.monotonic()-start,
            'peak_rss_bytes_macOS':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'scope':'post-main falsification on the two successful zero-HVC cases, not independent validation or an unbiased across-case tutoring-effect estimate'}
    np.savez(HERE/('outputs/teaching_%03d_untutored_no_clock_per_order_20.npz'%args.plant),
             **actor,true_losses=actual,query_true_losses=queried)
    save('outputs/untutored_control_%03d.json'%args.plant,result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
