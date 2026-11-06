"""Source-equation confirmation of a post hoc already-visited-plan witness."""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import numpy as np
import core as c
from common import HERE,SOURCE,save,now
from diagnostics import loadz,packed,reference_net,independent_waveform,INPUTS
from dev_joint import phases

def main():
    # Fixed choice: first held tuple,400. No model/actor change or new motor query.
    case=400;pack=loadz(SOURCE/'held_400_model.npz');env=loadz(SOURCE/'held_400_environment.npz')
    q=loadz(HERE/'outputs/held_400_population_queries.npz');g=loadz(HERE/'outputs/held_400_population_gold_queries.npz')['gold']
    best=int(np.argmin(g));final=q['actions'][-1];indices=[best,int(np.flatnonzero(np.all(q['query_actions']==final,axis=1))[0])]
    m,p=packed(pack);net=reference_net(m);rows=[]
    for label,index in zip(('best_visited_gold','selected_final'),indices):
        action=q['query_actions'][index];phase=int(phases(action[None],390000+case)[0]);aud=independent_waveform(action,env,env['orders'],phase)
        trace,_=c.simulate(net,aud,(m.h[:600],m.h[600:]));cost=c.population_cost(trace,p);gold=c.template_cost(aud,pack['teacher'])
        assert abs(cost-q['query_costs'][index])<1e-10;assert abs(gold-g[index])<1e-10
        rows.append({'label':label,'query_index':index,'action':action,'onset_shift_ms':phase,'source_population_cost':cost,
                     'saved_batch_cost':float(q['query_costs'][index]),'waveform_mse':gold,'cost_reconstruction_error':abs(cost-q['query_costs'][index])})
    assert rows[1]['source_population_cost']<rows[0]['source_population_cost'];assert rows[1]['waveform_mse']>rows[0]['waveform_mse']
    result={'utc':now(),'post_hoc_consumed_log_witness':True,'case':case,'rows':rows,'source_prefers_worse_visited_program':True,
            'feedback_gap_best_gold_minus_selected':rows[0]['source_population_cost']-rows[1]['source_population_cost'],
            'meaning':'local ordering counterexample, not a global wrong minimum or full-response information bound','input_hashes':INPUTS}
    save('outputs/MISRANKING_WITNESS.json',result);print(__import__('json').dumps(result,default=lambda x:x.tolist() if hasattr(x,'tolist') else x,indent=2),flush=True)
if __name__=='__main__':main()
