"""First predetermined source/waveform pair, before the wider diagnostic."""
import review_core as r
import numpy as np,time,resource

def main():
    start=time.monotonic()
    pack=r.loadz(r.SRC/'held_400_model.npz')
    env=r.loadz(r.SRC/'held_400_environment.npz',('basis','bias','orders','initial'))
    q=r.loadz(r.TASK/'outputs/held_400_population_queries.npz')
    rows=[]
    for ix in (3642,3630):
        a=q['query_actions'][ix]
        # Independent rendering at COMMON zero nuisance onset.
        aud=r.render(a[:4],int(a[4]),a[5],env,phase=0)
        cost,features,tr=r.integrate(aud,pack,trace=True)
        ref=r.source_trace(aud,pack)
        z=ref/100.;mom=np.r_[z.mean(0),(z*z).mean(0)]
        source_cost=float(np.mean((mom-pack['prototype_mean'])**2/pack['prototype_variance']))
        error=float(np.max(abs(ref-tr)))
        assert error<1e-10 and abs(source_cost-cost)<1e-12
        rows.append({'query_index':ix,'action':a,'common_phase_ms':0,'independent_cost':cost,'source_cost':source_cost,
                     'saved_actor_cost_original_nuisance':q['query_costs'][ix],
                     'source_trace_max_error':error,'waveform_mse':r.registered(aud,pack['teacher'])})
    out={'utc':r.now(),'case':400,'rows':rows,'source_prefers_worse_at_common_onset':rows[1]['source_cost']<rows[0]['source_cost'] and rows[1]['waveform_mse']>rows[0]['waveform_mse'],
         'feedback_gap':rows[0]['source_cost']-rows[1]['source_cost'],
         'runtime_seconds':time.monotonic()-start,'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    r.dump('PAIR_CHECK.json',out);print(__import__('json').dumps(out,default=lambda x:x.tolist(),indent=2),flush=True)

if __name__=='__main__':main()
