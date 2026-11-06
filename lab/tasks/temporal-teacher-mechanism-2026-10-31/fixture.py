import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import time,json
import numpy as np
from common import HERE,save,now
import core as c

def main():
    started=time.monotonic();d,net=c.load_old(100);y=c.features(d['target'],d['basis'],d['bias']);teacher=c.waveform(y)
    h=c.quiet(net);r,_=c.simulate(net,teacher,h);p=c.prototype(r);memory=c.learn_state(teacher)
    z,_=c.simulate(net,np.zeros_like(teacher),h);quiet=float(z.mean());cache={}
    def values(y,stretch=1.,phase=0):
        a=c.waveform(y,stretch,phase);key=a.tobytes()
        if key not in cache:
            r,_=c.simulate(net,a,h);active=int(np.sum(np.mean(a*a,axis=1)>1e-8))
            cache[key]={'raw':float(r.mean()),'normalized':float((r.sum()-quiet*r.size)/(max(active,1)*net.NE)),
                        'population':c.population_cost(r,p),'state':c.state_cost(a,memory),'template':c.template_cost(a,teacher)}
        return cache[key]
    orders=c.policies(98100);rank=[]
    for order in orders:rank.append(values(y[order]))
    onset_checks=[{'phase':phase,**values(y,1.,phase)} for phase in (-60,0,60)]
    actors=[]
    for mode in ('raw','normalized','population','state','template','oracle'):
        queries=[];costs=[]
        def reward(s):
            value=float(np.mean((c.waveform(y,s)-teacher)**2)) if mode=='oracle' else values(y,s)[mode]
            queries.append(float(s));costs.append(value);return value
        x=.8;v=reward(x);step=.05;trajectory=[x]
        for iteration in range(12):
            pp=[float(np.clip(x+sign*step,.7,1.2)) for sign in (-1,1)];vv=[reward(s) for s in pp];best=int(np.argmin(vv))
            if vv[best]<v:x=pp[best];v=vv[best]
            else:step=max(.00625,step/2)
            trajectory.append(x)
        save('outputs/fixture_%s_queries.json'%mode,{'durations':queries,'scalar_costs':costs,'accepted_durations':trajectory})
        gold=[float(np.mean((c.waveform(y,s)-teacher)**2)) for s in trajectory]
        actors.append({'mode':mode,'end':x,'end_gold':gold[-1],'initial_gold':gold[0],'queries':len(queries)})
        print(json.dumps(actors[-1]),flush=True)
    ranks={mode:int(np.flatnonzero(np.argsort([v[mode] for v in rank])==0)[0])+1 for mode in rank[0]}
    out={'time':now(),'plant':100,'orders':orders,'scores':rank,'target_ranks':ranks,'onset_checks':onset_checks,'duration_actors':actors,
         'population_target_score':values(y)['population'],'source_simulations':len(cache)+2,'seconds':time.monotonic()-started}
    save('outputs/FIXTURE.json',out);print(json.dumps({'ranks':ranks,'onsets':onset_checks,'seconds':out['seconds']}),flush=True)
if __name__=='__main__':main()
