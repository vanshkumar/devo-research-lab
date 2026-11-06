"""Independent saved-table/gold arithmetic; no circuit dynamics or actor fits."""
import os,sys
sys.dont_write_bytecode=True
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[name]='2'
import hashlib,json
import numpy as np
from audit_common import HERE,PILOT,SNAP,CACHE,SOURCE,initialize,j,npz,save

def main():
    initialize();checks=[];result=[]
    def check(name,ok,detail=None):
        checks.append({'name':name,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})
    for plant in (100,101,102):
        inputs=npz(SNAP/('plant_%03d/inputs.npz'%plant))
        # Report keys/shapes only first; all are admitted old synthetic arrays.
        follow=j(PILOT/('outputs/teaching_followup_%03d.json'%plant))
        rows=[]
        for table in follow['expanded_order_policy']:
            costs=np.asarray(table['costs']);orders=np.asarray(table['orders']);target=int(table['target_order_index'])
            best=int(np.argmin(costs));rank=1+int(np.sum(costs<costs[target]))
            check('%d_%s_saved_min_rank'%(plant,table['variant']),best==table['chosen_order_index'] and rank==table['target_rank'])
            check('%d_%s_64_unique_permutations'%(plant,table['variant']),orders.shape==(64,6) and len({tuple(o) for o in orders})==64 and np.all(np.sort(orders,axis=1)==np.arange(6)))
            wrong=[i for i in range(64) if i!=target];bestwrong=min(wrong,key=lambda i:costs[i])
            rows.append({'variant':table['variant'],'target_index':target,'target_rank':rank,'chosen_index':best,'bestwrong_index':int(bestwrong),
                         'bestwrong_order':orders[bestwrong].tolist(),'target_order':orders[target].tolist(),
                         'bestwrong_minus_target_Hz':float(costs[bestwrong]-costs[target]),'saved_gold_at_chosen':float(table['offline_true_feature_errors'][best])})
        duration=[]
        for d in follow['duration_learning']:
            duration.append({'variant':d['variant'],'initial_duration':d['durations'][0],'final_duration':d['durations'][-1],
                             'initial_gold':d['offline_waveform_errors'][0],'final_gold':d['offline_waveform_errors'][-1]})
        result.append({'plant':plant,'input_keys_shapes':{k:list(v.shape) for k,v in inputs.items()},'orders':rows,'duration':duration})
    tail=j(PILOT/'outputs/duration_tail_check.json')
    save('TABLE_AUDIT.json',{'rows':result,'saved_tail_checks':tail['checks'],'checks':checks,'all_passed':all(c['passed'] for c in checks),
         'scope':'Saved arithmetic only; no newly reconstructed dynamics or independent ground-truth calculation yet.'})
    print(json.dumps({'table_checks_passed':sum(c['passed'] for c in checks),'all_passed':all(c['passed'] for c in checks),'plants':result}))

if __name__=='__main__':main()
