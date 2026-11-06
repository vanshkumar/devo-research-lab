import review_core as r
import numpy as np,json,time

def main():
    started=time.monotonic()
    old=json.loads((r.HERE/'PAIR_CHECK.json').read_text())
    action=np.asarray(old['rows'][1]['action']);correct=np.asarray(old['rows'][0]['action'])
    pack=r.loadz(r.SRC/'held_400_model.npz')
    env=r.loadz(r.SRC/'held_400_environment.npz',('basis','bias','orders','initial'))
    stretches=[float(correct[5]),.835,float(action[5])]
    waves=np.asarray([r.render(action[:4],int(action[4]),d,env) for d in stretches])
    costs,mom=r.integrate_batch(waves,pack)
    residual=(mom[0]-pack['prototype_mean'])/np.sqrt(pack['prototype_variance'])
    rows=[]
    for i,d in enumerate(stretches):
        change=(mom[i]-mom[0])/np.sqrt(pack['prototype_variance'])
        cross=float(2*np.mean(residual*change));positive=float(np.mean(change*change));delta=float(costs[i]-costs[0])
        assert abs(cross+positive-delta)<1e-12
        starts,ends=r.schedule(d)
        rows.append({'stretch_repr':repr(d),'stretch_hex':d.hex(),'starts':starts,'ends':ends,'cost':costs[i],
                     'gold':r.registered(waves[i],pack['teacher']),'cost_delta':delta,'cross_term':cross,'positive_temporal_term':positive,
                     'positive_feature_change':positive>0})
    difference=np.flatnonzero(np.any(waves[1]!=waves[2],axis=1))
    assert abs(costs[0]-old['rows'][0]['source_cost'])<1e-12
    assert abs(costs[2]-old['rows'][1]['source_cost'])<1e-12
    r.dump('PRECISION_CHECK.json',{'utc':r.now(),'rows':rows,'differing_time_samples':difference,
           'binary_stretch_ulp_difference':int(np.asarray(stretches[2]).view(np.uint64)-np.asarray(stretches[1]).view(np.uint64)),
           'runtime_seconds':time.monotonic()-started,'scope':'Postvalidation two-encoding audit; original actor and grid unchanged'})
    print((r.HERE/'PRECISION_CHECK.json').read_text(),flush=True)

if __name__=='__main__':main()
