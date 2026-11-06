"""Tutor-order specificity, mean-drive control and explicit precision assays."""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import argparse,copy,json,pickle,time
from io import BytesIO
import numpy as np
from scipy.special import erf
import teaching_pilot as p
from common import ROOT,HERE,SOURCE,read,load_json,save,now

def train_variant(state,plant,kind):
    path=SOURCE/('%s_%03d.pkl'%(kind,plant))
    if path.exists():return pickle.loads(read(path,'derived_synthetic_state'))
    net=copy.deepcopy(state['nets']['untutored']);order=2 if kind=='reverse' else 0
    aud=p.auditory(state['target_features'][p.PERMS[order]],pad=0,length=1100)
    aud=np.concatenate([np.zeros((p.helper.T_BURN,p.helper.NE)),np.tile(aud,(35,1))])
    tonic=state['rh'].mean(0)
    rh=np.broadcast_to(tonic,(len(aud),p.helper.NH)).copy() if kind=='tonic' else np.zeros((len(aud),p.helper.NH))
    m=p.means();t=time.monotonic()
    result=net.sim(state['initial_hE'],state['initial_hI'],rh,aud,[],len(aud),1,0,
                   plasticity={'JEI':p.helper.bilin_hebb_EI,'JIE':p.helper.bilin_hebb_IE},lr={'JEI':5e-2,'JIE':6e-3},tauW=1e5,
                   JEI0_mean=m[1],JIE0_mean=m[2],asyn_E=10,asyn_I=0,rE_th=1.5,rI_th=5,no_progress_bar=True)
    del result,aud,rh
    out={'net':net,'kind':kind,'teacher_order':order,'seconds':time.monotonic()-t}
    with path.open('wb') as f:pickle.dump(out,f,pickle.HIGHEST_PROTOCOL)
    print(json.dumps({'plant':plant,'variant_trained':kind,'seconds':out['seconds']}),flush=True)
    return out

def build(net,state,drive):
    tonic=state['rh'].mean(0);quiet=np.broadcast_to(tonic,(1000,p.helper.NH)).copy() if drive=='tonic' else np.zeros((1000,p.helper.NH))
    result=net.sim(state['initial_hE'],state['initial_hI'],quiet,np.zeros((1000,p.helper.NE)),[],1000,1,0,no_progress_bar=True)
    hE,hI=result[-2:];del result
    def inputs(y,phase,stretch=1.):
        aud=p.auditory(y,phase=phase,stretch=stretch)
        if drive=='timed':
            active=np.flatnonzero(np.max(np.abs(aud),axis=1)>1e-8)
            align=int(active[0])-(p.PAD+int(p.helper.ON[0])) if len(active) else 0
            rh=p.clock(state['rh'],phase=align)
        elif drive=='tonic':rh=np.broadcast_to(tonic,(p.LENGTH,p.helper.NH)).copy()
        else:rh=np.zeros((p.LENGTH,p.helper.NH))
        return aud,rh
    def score(y,phase,stretch=1.):
        aud,rh=inputs(y,phase,stretch);res=net.sim(hE,hI,rh,aud,[],p.LENGTH,1,0,no_progress_bar=True)
        return float(np.mean(res[0]))
    return score,inputs,hE,hI

def phi(x,params):
    maximum,threshold,slope=params
    return maximum/2*(1+erf((x-threshold)/(np.sqrt(2)*slope)))
def seeded_frozen_cost(net,hE0,hI0,rh,aud,noise,seed):
    """Separately written frozen Euler updates; no plasticity or source mutation."""
    rng=np.random.default_rng(seed);hE=hE0.copy();hI=hI0.copy();rE=phi(hE,net.phiE);rI=phi(hI,net.phiI);total=float(rE.sum())
    for t in range(1,len(aud)):
        hvc=net.W@rh[t-1]
        if net.w_inh>0:hvc-=net.w_inh*rh[t-1].sum()
        dE=-hE+hvc+aud[t-1]+net.JEE@rE-net.JEI@rI
        dI=-hI+net.JIE@rE-net.JII@rI
        if noise:
            dE+=rng.normal(0,noise,net.NE);dI+=rng.normal(0,noise,net.NI)
        hE+=dE/net.tauE;hI+=dI/net.tauI;rE=phi(hE,net.phiE);rI=phi(hI,net.phiI);total+=float(rE.sum())
    return total/(len(aud)*net.NE)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--plant',type=int,choices=[100,101,102],required=True);ap.add_argument('--noise-repeats',type=int,default=20);args=ap.parse_args();t0=time.monotonic();state=p.load(args.plant);forward=p.train_no_clock(state,args.plant)
    reverse=train_variant(state,args.plant,'reverse');tonic=train_variant(state,args.plant,'tonic')
    learned=np.load(BytesIO(read(HERE/('outputs/teaching_%03d_no_clock_per_order_20.npz'%args.plant),'derived_actor')),allow_pickle=False)['actions'][-1,:4]
    content={'exact_tutor':state['target_features'],'learned_content':p.features(learned,state['basis'],state['bias'])}
    variants={'no_clock_forward':(forward['net'],'zero',0),'no_clock_reverse':(reverse['net'],'zero',2),
              'tonic_forward':(tonic['net'],'tonic',0),'untutored_no_clock':(state['nets']['untutored'],'zero',0),
              'onset_reset':(state['nets']['learned35'],'timed',0)}
    preference=[];mc=[];noise_data={};checks=[];duration=[];broad_order=[]
    for name,(net,drive,desired) in variants.items():
        score,inputs,hE,hI=build(net,state,drive)
        for cname,y in content.items():
            values=np.array([np.mean([score(y[perm],phase) for phase in (-60,60)]) for perm in p.PERMS])
            rank=int(np.flatnonzero(np.argsort(values)==desired)[0])+1
            preference.append({'variant':name,'content':cname,'desired_order':desired,'preferred_order':int(values.argmin()),
                               'desired_rank':rank,'costs':values.tolist(),'nearest_wrong_minus_desired':float(np.min(np.delete(values,desired))-values[desired])})
            if cname=='learned_content':
                rng=np.random.default_rng(93000+args.plant);z=rng.normal(size=(20000,6))
                for sigma in (0,.001,.01):
                    for repeats in (1,4,16,64,256):
                        choices=np.argmin(values[None,:]+z*sigma/np.sqrt(repeats),axis=1)
                        success=float(np.mean(choices==desired))
                        mc.append({'variant':name,'sigma_Hz':sigma,'evaluations_per_order':repeats,'correct_fraction':success,'monte_carlo_n':20000})
        if name in ('no_clock_forward','onset_reset'):
            y=content['learned_content'];aud,rh=inputs(y,-60)
            direct=seeded_frozen_cost(net,hE,hI,rh,aud,0,123);reference=score(y,-60);err=abs(direct-reference);assert err<1e-10
            checks.append({'variant':name,'seeded_port_zero_noise_max_error':err})
            for strength in (.1,.5):
                costs=np.zeros((args.noise_repeats,6))
                for rep in range(args.noise_repeats):
                    phase=-60 if rep%2==0 else 60
                    for order,perm in enumerate(p.PERMS):
                        aud,rh=inputs(y[perm],phase);seed=950000+args.plant*10000+int(strength*10)*1000+rep*6+order
                        costs[rep,order]=seeded_frozen_cost(net,hE,hI,rh,aud,strength,seed)
                noise_data[name+'_'+str(strength)]=costs
                print(json.dumps({'plant':args.plant,'variant':name,'current_noise':strength,'correct_fraction':float(np.mean(costs.argmin(1)==0))}),flush=True)
        if name in ('no_clock_forward','no_clock_reverse','onset_reset'):
            # Expand the finite policy space beyond the six original order actions.
            # Proposals are fixed without evaluating rewards; true errors are offline.
            orders=[tuple(v) for v in p.PERMS];rng=np.random.default_rng(98000+args.plant)
            while len(orders)<64:
                candidate=tuple(rng.permutation(6))
                if candidate not in orders:orders.append(candidate)
            y=content['exact_tutor'];values=np.array([np.mean([score(y[np.array(order)],phase) for phase in (-60,60)]) for order in orders])
            best=int(values.argmin());teacher_order=p.PERMS[desired];gold=np.array([np.mean((y[np.array(order)]-y[teacher_order])**2) for order in orders])
            index=orders.index(tuple(teacher_order));rank=int(np.flatnonzero(np.argsort(values)==index)[0])+1
            broad_order.append({'variant':name,'orders':[list(v) for v in orders],'costs':values.tolist(),'offline_true_feature_errors':gold.tolist(),
                                'target_order_index':index,'target_rank':rank,'chosen_order_index':best,'chosen_order':list(orders[best]),
                                'chosen_error':float(gold[best]),'chosen_cost_minus_target':float(values[best]-values[index]),
                                'logical_feedback_queries':64,'source_samples_per_query':2})
        if name in ('no_clock_forward','onset_reset','tonic_forward'):
            # A complete one-axis policy-learning task after shape acquisition.
            # Actor uses circuit feedback only; waveform error is evaluated offline.
            y=content['learned_content'];cache={};logical=0
            def feedback(stretch):
                nonlocal logical
                logical+=1;key=float(stretch)
                if key not in cache:cache[key]=float(np.mean([score(y,phase,key) for phase in (-60,60)]))
                return cache[key]
            x=.8;value=feedback(x);trajectory=[x];cost_trace=[value];step=.05
            for iteration in range(12):
                proposals=[float(np.clip(x+sgn*step,.7,1.2)) for sgn in (-1,1)];values=[feedback(z) for z in proposals];i=int(np.argmin(values))
                if values[i]<value:x=proposals[i];value=values[i]
                else:step=max(.00625,step/2)
                trajectory.append(x);cost_trace.append(value)
            gold_target=p.auditory(state['target_features'],phase=0)
            errors=[float(np.mean((p.auditory(y,phase=0,stretch=z)-gold_target)**2)) for z in trajectory]
            duration.append({'variant':name,'kind':'circuit','durations':trajectory,'costs':cost_trace,'offline_waveform_errors':errors,'queries':logical,'unique_source_costs':len(cache)})
            if name=='no_clock_forward':
                def gold(z):return float(np.mean((p.auditory(y,phase=0,stretch=z)-gold_target)**2))
                x=.8;value=gold(x);tr=[x];vs=[value];step=.05
                for iteration in range(12):
                    proposals=[float(np.clip(x+sgn*step,.7,1.2)) for sgn in (-1,1)];values=[gold(z) for z in proposals];i=int(np.argmin(values))
                    if values[i]<value:x=proposals[i];value=values[i]
                    else:step=max(.00625,step/2)
                    tr.append(x);vs.append(value)
                duration.append({'variant':'true_waveform_error','kind':'oracle','durations':tr,'offline_waveform_errors':vs,'queries':25})
        print(json.dumps({'plant':args.plant,'preference_variant':name,'elapsed':time.monotonic()-t0}),flush=True)
    np.savez(HERE/('outputs/teaching_source_noise_%03d.npz'%args.plant),**noise_data)
    noise_summary=[]
    for key,costs in noise_data.items():noise_summary.append({'variant':key,'mean_costs':costs.mean(0).tolist(),'std_costs':costs.std(0,ddof=1).tolist(),'one_evaluation_correct_fraction':float(np.mean(costs.argmin(1)==0)),'sets':len(costs)})
    out={'plant':args.plant,'preferences':preference,'readout_noise_choice_assay':mc,'source_current_noise_assay':noise_summary,'duration_learning':duration,'expanded_order_policy':broad_order,'checks':checks,
         'seconds':time.monotonic()-t0,'scope':'exploratory tutor-order/drive/precision diagnostic on three consumed synthetic tuples; no complete noisy motor-learning or biological-noise claim'}
    save('outputs/teaching_followup_%03d.json'%args.plant,out);print(json.dumps({'plant':args.plant,'preferences':preference,'source_current_noise_assay':noise_summary,'checks':checks},indent=2))
if __name__=='__main__':main()
