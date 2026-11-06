"""Adversarial probe-window extension, after saved duration learning."""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import json,pickle,time,resource
import numpy as np
import teaching_pilot as p
from teaching_followup import build
from common import ROOT,HERE,SOURCE,read,load_json,save,now

def main():
    started=time.monotonic();rows=[];checks=[]
    for plant in (100,101,102):
        path=HERE/('outputs/teaching_followup_%03d.json'%plant)
        if not path.exists():continue
        f=load_json(path,'derived_result');state=p.load(plant)
        forward=p.train_no_clock(state,plant)
        tonic=pickle.loads(read(SOURCE/('tonic_%03d.pkl'%plant),'derived_synthetic_state'))
        from io import BytesIO
        with np.load(BytesIO(read(HERE/('outputs/teaching_%03d_no_clock_per_order_20.npz'%plant),'derived_actor')),allow_pickle=False) as d:
            shape=d['actions'][-1,:4].copy()
        y=p.features(shape,state['basis'],state['bias'])
        for name,net,drive in (('no_clock_forward',forward['net'],'zero'),('onset_reset',state['nets']['learned35'],'timed'),('tonic_forward',tonic['net'],'tonic')):
            _,inputs,hE,hI=build(net,state,drive)
            learned=next(r for r in f['duration_learning'] if r['variant']==name)
            durations=sorted(set([float(learned['durations'][0]),float(learned['durations'][-1]),1.]))
            group=[]
            for duration in durations:
                prefix_cost=[];extended_cost=[]
                for phase in (-60,60):
                    aud,rh=inputs(y,phase,duration)
                    aud=np.concatenate([aud,np.zeros((700,p.helper.NE))])
                    extra=np.broadcast_to(state['rh'].mean(0),(700,p.helper.NH)).copy() if drive=='tonic' else np.zeros((700,p.helper.NH))
                    rh=np.concatenate([rh,extra]);result=net.sim(hE,hI,rh,aud,[],len(aud),1,0,no_progress_bar=True)
                    prefix_cost.append(float(result[0][:p.LENGTH].mean()));extended_cost.append(float(result[0].mean()))
                row={'plant':plant,'variant':name,'duration':duration,'prefix_mean_1300ms':float(np.mean(prefix_cost)),
                     'extended_mean_2000ms':float(np.mean(extended_cost)),
                     'phase_difference_1300ms':float(abs(prefix_cost[0]-prefix_cost[1])),
                     'phase_difference_2000ms':float(abs(extended_cost[0]-extended_cost[1]))}
                group.append(row);rows.append(row)
            at=lambda d:next(r for r in group if r['duration']==float(d))
            for key,cost in ((learned['durations'][0],learned['costs'][0]),(learned['durations'][-1],learned['costs'][-1])):
                err=abs(at(key)['prefix_mean_1300ms']-cost);assert err<1e-10
                checks.append({'plant':plant,'variant':name,'saved_prefix_score_max_error':err})
            target=at(1.);end=at(learned['durations'][-1])
            checks.append({'plant':plant,'variant':name,'final_duration':float(learned['durations'][-1]),
                           'final_minus_target_1300ms':end['prefix_mean_1300ms']-target['prefix_mean_1300ms'],
                           'final_minus_target_2000ms':end['extended_mean_2000ms']-target['extended_mean_2000ms']})
        print(json.dumps({'plant':plant,'tail_check_elapsed':time.monotonic()-started}),flush=True)
    out={'time':now(),'rows':rows,'checks':checks,'seconds':time.monotonic()-started,
         'peak_rss_bytes_macOS':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'scope':'same frozen circuits/reset;700ms appended quiet; original scores retained; finite window sensitivity only'}
    save('outputs/duration_tail_check.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':main()
