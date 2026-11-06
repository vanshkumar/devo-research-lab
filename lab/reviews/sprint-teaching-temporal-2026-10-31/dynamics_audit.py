"""Independent frozen dynamics/gold/selector reconstruction and contrary test.

Uses only three admitted consumed synthetic snapshots and cached critics.
The exact source sim method is an external reference; the reviewer integrator
uses normal-CDF activation and separately implemented simultaneous Euler steps.
No investigator module or verifier is imported or executed.
"""
import os,sys
sys.dont_write_bytecode=True
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[name]='2'
from pathlib import Path
import ast,copy,datetime as dt,hashlib,io,json,pickle,resource,time,types
import numpy as np
from scipy.special import ndtr,erf
from audit_common import ROOT,HERE,PILOT,SNAP,CACHE,SOURCE,DEADLINE,read,j,npz,save,initialize

class FrozenNetwork:pass
class LocalUnpickler(pickle.Unpickler):
    def find_class(self,module,name):
        if module=='models' and name in ('EINet','WCNet'):return FrozenNetwork
        return super().find_class(module,name)

CHECKS=[];SIMS=0
def check(name,ok,detail=None):
    CHECKS.append({'name':name,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})

def features(shape,basis,bias):
    shape=np.asarray(shape);single=shape.ndim==1
    raw=shape.reshape(-1,4).dot(basis.reshape(-1,4).T).reshape(-1,6,100)+bias
    raw=np.maximum(raw,0);raw-=raw.mean(axis=2,keepdims=True)
    raw=raw*2/np.maximum(np.sqrt(np.mean(raw**2,axis=2,keepdims=True)),1e-12)
    return raw[0] if single else raw

def intervals(on,off,phase=0,stretch=1.,pad=100):
    first=int(on[0]);result=[]
    for lo,hi in zip(on,off):
        start=pad+phase+first+round((int(lo)-first)*stretch)
        result.append((start,start+round((int(hi)-int(lo))*stretch)))
    return result

def stimulus(y,on,off,phase=0,stretch=1.,pad=100,length=1300):
    z=np.zeros((length,600));pattern=np.repeat(y,6,axis=1)
    for k,(lo,hi) in enumerate(intervals(on,off,phase,stretch,pad)):
        assert 0<=lo<hi<=length,'clipped probe'
        z[lo:hi]=pattern[k]
    return z

def waveform_error(y,teacher,on,off,stretch):
    # Independent integration over piecewise-constant100-channel intervals.
    aa=intervals(on,off,0,stretch);bb=intervals(on,off,0,1.)
    cuts=sorted({0,1300,*[v for pair in aa+bb for v in pair]});total=0.
    zero=np.zeros(100)
    for lo,hi in zip(cuts[:-1],cuts[1:]):
        current=next((y[k] for k,(a,b) in enumerate(aa) if a<=lo<b),zero)
        target=next((teacher[k] for k,(a,b) in enumerate(bb) if a<=lo<b),zero)
        total+=(hi-lo)*float(np.mean((current-target)**2))
    return total/1300

def phi(h,par):return par[0]*ndtr((h-par[1])/par[2])

def integrate(net,hE0,hI0,aud,rh):
    global SIMS
    assert dt.datetime.now(dt.timezone.utc)<DEADLINE,'deadline'
    SIMS+=1;hE=np.array(hE0,copy=True);hI=np.array(hI0,copy=True)
    rE=phi(hE,net.phiE);rI=phi(hI,net.phiI);means=np.empty(len(aud));means[0]=rE.mean()
    for t in range(1,len(aud)):
        he_in=net.W@rh[t-1]
        if net.w_inh>0:he_in=he_in-net.w_inh*rh[t-1].sum()
        eflow=(he_in+aud[t-1]+net.JEE@rE-net.JEI@rI-hE)/net.tauE
        iflow=(net.JIE@rE-net.JII@rI-hI)/net.tauI
        hE=hE+eflow;hI=hI+iflow
        rE=phi(hE,net.phiE);rI=phi(hI,net.phiI);means[t]=rE.mean()
    assert np.isfinite(means).all()
    return means,hE,hI

def source_method(raw):
    tree=ast.parse(raw.decode());sim=None;activation=None
    for node in tree.body:
        if isinstance(node,ast.ClassDef):
            for method in node.body:
                if isinstance(method,ast.FunctionDef) and node.name=='EINet' and method.name=='sim':sim=copy.deepcopy(method)
                if isinstance(method,ast.FunctionDef) and node.name=='WCNet' and method.name=='phi':activation=copy.deepcopy(method)
    assert sim is not None and activation is not None
    activation.decorator_list=[]
    ns={'np':np,'erf':erf,'tqdm':lambda iterable,**kw:iterable}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[activation],type_ignores=[])),'pinned_source_phi','exec'),ns)
    ns['EINet']=types.SimpleNamespace(phi=ns['phi'])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[sim],type_ignores=[])),'pinned_source_EINet_sim','exec'),ns)
    return ns['sim']

def model_signature(net):
    out=hashlib.sha256()
    for name in ('W','JEE','JEI','JIE','JII'):
        matrix=getattr(net,name)
        if hasattr(matrix,'indptr'):
            for a in (matrix.data,matrix.indices,matrix.indptr):out.update(a.tobytes())
        else:out.update(np.asarray(matrix).tobytes())
    return out.hexdigest()

def reset(net,state,drive):
    rh=np.broadcast_to(state['rh'].mean(0),(1000,15)).copy() if drive=='tonic' else np.zeros((1000,15))
    _,hE,hI=integrate(net,state['initial_hE'],state['initial_hI'],np.zeros((1000,600)),rh)
    return hE,hI

def drive_array(state,drive,phase,length):
    if drive=='zero':return np.zeros((length,15))
    if drive=='tonic':return np.broadcast_to(state['rh'].mean(0),(length,15)).copy()
    out=np.zeros((length,15));start=100+phase
    out[start:start+len(state['rh'])]=state['rh'];return out

def score(net,state,y,on,off,drive,stretch=1.,tail=0,reference=None):
    hE,hI=reset(net,state,drive);scalars=[];traces=[];errors=[]
    for phase in (-60,60):
        aud=stimulus(y,on,off,phase,stretch,length=1300+tail)
        rh=drive_array(state,drive,phase,1300+tail)
        mean,_,_=integrate(net,hE,hI,aud,rh);scalars.append(float(mean.mean()));traces.append(mean)
        if reference is not None:
            result=reference(net,hE,hI,rh,aud,[],len(aud),1,0,no_progress_bar=True)
            err=float(np.max(np.abs(result[0].mean(axis=1)-mean)));errors.append(err)
            del result
    return float(np.mean(scalars)),traces,errors

def replay_scalar_actor(actor,initial,seed):
    costs=actor['query_costs'];stored=actor['query_actions'];rng=np.random.default_rng(seed);states=[];actions=[];positions=0;maxerr=0.
    for order in range(6):
        x=np.r_[initial,float(order)];maxerr=max(maxerr,float(np.max(np.abs(x-stored[positions]))));states.append([x,float(costs[positions]),.4]);positions+=1
    chosen=min(states,key=lambda s:s[1]);trajectory=[np.r_[initial,1.],chosen[0].copy()];values=[float(costs[1]),chosen[1]]
    for iteration in range(20):
        broad=rng.uniform(-2,2,(2,4))
        for order,s in enumerate(states):
            candidates=[]
            for coord in range(4):
                for sign in (1,-1):
                    x=s[0].copy();x[coord]=max(-2.,min(2.,x[coord]+sign*s[2]));candidates.append(x)
            candidates.extend(np.r_[b,float(order)] for b in broad)
            candidate_costs=[]
            for x in candidates:
                maxerr=max(maxerr,float(np.max(np.abs(x-stored[positions]))));candidate_costs.append(float(costs[positions]));positions+=1
            selected=min(range(10),key=candidate_costs.__getitem__)
            if candidate_costs[selected]<s[1]:s[0]=candidates[selected].copy();s[1]=candidate_costs[selected]
            else:s[2]=max(.00625,s[2]/2)
        best=min(states,key=lambda s:s[1]);trajectory.append(best[0].copy());values.append(best[1])
    return positions,maxerr,float(np.max(np.abs(np.asarray(trajectory)-actor['actions']))),float(np.max(np.abs(np.asarray(values)-actor['costs'])))

def main():
    t0=time.monotonic();initialize();assert not (HERE/'DYNAMICS_RESULTS.json').exists(),'one planned execution'
    pilot_manifest=j(PILOT/'MANIFEST.json');pins={a['path']:a for a in pilot_manifest['artifacts']}
    def pinned(path):
        raw=read(path,'pinned_consumed_synthetic_state' if path.suffix=='.pkl' else 'pinned_source_code')
        expected=pins.get(str(path.relative_to(ROOT)))
        check('pin_'+str(path.relative_to(ROOT)),expected is not None and expected['bytes']==len(raw) and expected['sha256']==hashlib.sha256(raw).hexdigest())
        return raw
    def state_load(path):return LocalUnpickler(io.BytesIO(pinned(path))).load()
    source_raw=read(SOURCE/'upstream/src/models.py','pinned_equation_reference');reference=source_method(source_raw)
    save('NUMERICAL_FREEZE.json',{'time':dt.datetime.now(dt.timezone.utc).isoformat(),'scope':'RECONSTRUCTION_PLAN.md',
        'plan_sha256':hashlib.sha256((HERE/'RECONSTRUCTION_PLAN.md').read_bytes()).hexdigest(),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_models_sha256':hashlib.sha256(source_raw).hexdigest(),
        'new_plants':False,'warm_cycles':5,'quiet_tail_ms':700,'target_errors_not_used_by_scalar_selector':True})
    allresults=[]
    for plant in (100,101,102):
        print(json.dumps({'plant':plant,'stage':'loading_and_gold'}),flush=True)
        state=state_load(SNAP/('plant_%03d/state.pkl'%plant))
        input_arrays=npz(SNAP/('plant_%03d/inputs.npz'%plant));basis=input_arrays['basis'];bias=input_arrays['bias'];on=input_arrays['on'];off=input_arrays['off']
        teacher=features(input_arrays['target'],basis,bias)
        check('%d_groundtruth_target_features'%plant,np.max(np.abs(teacher-state['target_features']))<1e-12)
        for rel,expected in state['source_hashes'].items():
            raw=read(ROOT/rel,'snapshot_source_pin_check');check('%d_source_%s'%(plant,rel),hashlib.sha256(raw).hexdigest()==expected)
        forward=state_load(CACHE/('noclock_%03d.pkl'%plant))['net'];tonic=state_load(CACHE/('tonic_%03d.pkl'%plant))['net']
        clocked=state['nets']['learned35'];follow=j(PILOT/('outputs/teaching_followup_%03d.json'%plant))
        nets={'no_clock_forward':(forward,'zero'),'onset_reset':(clocked,'timed'),'tonic_forward':(tonic,'tonic')}
        signatures={name:model_signature(net) for name,(net,drive) in nets.items()}
        # Saved gold and actor choices reconstructed independently.
        actor_details=[];learned_y=None
        for mode in ('oracle','clocked','unregistered','onset_reset','no_clock')+ (('untutored_no_clock',) if plant in (100,102) else ()):
            actor=npz(PILOT/('outputs/teaching_%03d_%s_per_order_20.npz'%(plant,mode)))
            positions,proposalerr,selectionerr,costerr=replay_scalar_actor(actor,input_arrays['initial'],80000+plant)
            check('%d_%s_scalar_only_actor_replay'%(plant,mode),positions==1206 and proposalerr<1e-12 and selectionerr<1e-12 and costerr<1e-12,
                  {'proposal_error':proposalerr,'selection_error':selectionerr,'cost_error':costerr})
            aa=actor['query_actions'];yy=features(aa[:,:4],basis,bias);perms=np.array([np.arange(6),np.roll(np.arange(6),1),np.arange(6)[::-1],[1,0,3,2,5,4],np.roll(np.arange(6),3),np.roll(np.arange(6),2)])
            yy=np.take_along_axis(yy,perms[aa[:,4].astype(int),:,None],axis=1)
            querygold=np.mean((yy-teacher)**2,axis=(1,2));gold_err=float(np.max(np.abs(querygold-actor['query_true_losses'])))
            check('%d_%s_query_gold_reconstructed'%(plant,mode),gold_err<1e-12,{'max_error':gold_err})
            if mode=='oracle':check('%d_oracle_cost_is_true_loss'%plant,np.max(np.abs(querygold-actor['query_costs']))<1e-12)
            if mode=='no_clock':learned_y=features(actor['actions'][-1,:4],basis,bias)
            actor_details.append({'mode':mode,'queries':positions,'query_gold_max_error':gold_err,'saved_offline_final_gold':float(actor['true_losses'][-1])})
        gold_tables=[];order_pairs=[];warm_pairs=[]
        for table in follow['expanded_order_policy']:
            orders=np.asarray(table['orders']);costs=np.asarray(table['costs']);target=int(table['target_order_index'])
            desired=teacher[orders[target]]
            gold=np.mean((teacher[orders]-desired)**2,axis=(1,2));err=float(np.max(np.abs(gold-table['offline_true_feature_errors'])))
            check('%d_%s_64_gold_errors'%(plant,table['variant']),err<1e-12,{'max_error':err})
            gold_tables.append({'variant':table['variant'],'independent_gold_max_error':err,'reward_only_argmin':int(costs.argmin()),'chosen_gold_error':float(gold[costs.argmin()])})
            if table['variant'] not in ('no_clock_forward','onset_reset'):continue
            name=table['variant'];net,drive=nets[name];wrong=min((i for i in range(64) if i!=target),key=lambda i:costs[i])
            row={'variant':name,'target_index':target,'bestwrong_index':int(wrong),'pair':[]}
            for tag,index in (('target',target),('bestwrong',wrong)):
                y=teacher[orders[index]];value,traces,errors=score(net,state,y,on,off,drive,reference=reference)
                check('%d_%s_%s_source_reconstruction'%(plant,name,tag),abs(value-costs[index])<1e-10 and max(errors)<1e-10,
                      {'saved_score_error':abs(value-costs[index]),'source_trace_error':max(errors)})
                aud=stimulus(y,on,off);energy=float(np.sum(aud**2));active=int(np.sum(np.any(aud!=0,axis=1)))
                row['pair'].append({'kind':tag,'score_Hz':value,'saved_score_Hz':float(costs[index]),'input_energy':energy,'active_ms':active,'source_trace_max_error':max(errors)})
                if name=='no_clock_forward':
                    one=stimulus(y,on,off,pad=0,length=1100);repeated=np.tile(one,(5,1));rh=np.zeros((len(repeated),15))
                    trace,_,_=integrate(net,state['initial_hE'],state['initial_hI'],repeated,rh)
                    warm_pairs.append({'kind':'order','policy':tag,'order_index':int(index),'cycle_means_Hz':trace.reshape(5,1100).mean(1).tolist(),
                                       'input_energy_one_cycle':float(np.sum(one**2))})
            row['bestwrong_minus_target_Hz']=row['pair'][1]['score_Hz']-row['pair'][0]['score_Hz']
            check('%d_%s_order_exposure_matched'%(plant,name),abs(row['pair'][1]['input_energy']-row['pair'][0]['input_energy'])<1e-8 and row['pair'][1]['active_ms']==row['pair'][0]['active_ms'])
            order_pairs.append(row)
            print(json.dumps({'plant':plant,'stage':'fresh_order_pair','variant':name,'gap':row['bestwrong_minus_target_Hz']}),flush=True)
        reverse_result=None
        if plant==102:
            reverse=state_load(CACHE/'reverse_102.pkl')['net'];rr=[]
            for netname,net in (('forward',forward),('reverse_tutored',reverse)):
                for order in (0,2):
                    y=teacher if order==0 else teacher[::-1]
                    value,traces,errors=score(net,state,y,on,off,'zero',reference=reference)
                    saved=next(x for x in follow['preferences'] if x['variant']==('no_clock_forward' if netname=='forward' else 'no_clock_reverse') and x['content']=='exact_tutor')['costs'][order]
                    check('102_%s_order%d_reconstruction'%(netname,order),abs(value-saved)<1e-10 and max(errors)<1e-10)
                    rr.append({'net':netname,'order':order,'score_Hz':value})
            reverse_result=rr
        duration=[];normalized=[]
        for name,(net,drive) in nets.items():
            saved=next(d for d in follow['duration_learning'] if d['variant']==name);final=float(saved['durations'][-1])
            # A matched quiet baseline supports exposure-normalized arithmetic.
            hE,hI=reset(net,state,drive);baseline=[]
            for phase in (-60,60):
                mean,_,_=integrate(net,hE,hI,np.zeros((2000,600)),drive_array(state,drive,phase,2000));baseline.append(mean)
            for stretch in sorted({.8,final,1.}):
                value,traces,_=score(net,state,learned_y,on,off,drive,stretch,700)
                prefix=float(np.mean([t[:1300].mean() for t in traces]));gold=waveform_error(learned_y,teacher,on,off,stretch)
                # Find original duration endpoint, using float-close equality.
                for index in (0,-1):
                    if abs(stretch-saved['durations'][index])<1e-12:
                        check('%d_%s_duration_%s_prefix'%(plant,name,str(stretch)),abs(prefix-saved['costs'][index])<1e-10)
                        check('%d_%s_duration_%s_gold'%(plant,name,str(stretch)),abs(gold-saved['offline_waveform_errors'][index])<1e-12)
                aud=stimulus(learned_y,on,off,stretch=stretch,length=2000);active=int(np.sum(np.any(aud!=0,axis=1)))
                excess=float(np.mean([(t-b).sum()/active for t,b in zip(traces,baseline)]))
                duration.append({'variant':name,'stretch':stretch,'prefix_1300_Hz':prefix,'mean_2000_Hz':value,'independent_waveform_MSE':gold,
                                 'active_ms':active,'input_energy':float(np.sum(aud**2)),'quiet_subtracted_excess_per_active_ms_Hz':excess})
                if name=='no_clock_forward' and (abs(stretch-final)<1e-12 or abs(stretch-1)<1e-12):
                    one=stimulus(learned_y,on,off,stretch=stretch,pad=0,length=1100);repeated=np.tile(one,(5,1))
                    trace,_,_=integrate(net,state['initial_hE'],state['initial_hI'],repeated,np.zeros((len(repeated),15)))
                    warm_pairs.append({'kind':'duration','stretch':stretch,'cycle_means_Hz':trace.reshape(5,1100).mean(1).tolist(),
                                       'input_energy_one_cycle':float(np.sum(one**2))})
            print(json.dumps({'plant':plant,'stage':'duration_complete','variant':name}),flush=True)
        for name,(net,drive) in nets.items():check('%d_%s_weights_unchanged'%(plant,name),model_signature(net)==signatures[name])
        item={'plant':plant,'actor_reconstruction':actor_details,'independent_order_gold':gold_tables,'fresh_order_pairs':order_pairs,
              '102_positive_reverse_preference':reverse_result,'duration_common_tail':duration,'candidate_conditioned_5_cycle_contrary_test':warm_pairs}
        allresults.append(item)
        save('DYNAMICS_PARTIAL.json',{'plants':allresults,'checks':CHECKS,'all_passed':all(c['passed'] for c in CHECKS)})
        print(json.dumps({'plant':plant,'stage':'done','elapsed':time.monotonic()-t0,'independent_integrations':SIMS}),flush=True)
        del state,forward,tonic,clocked
    result={'plants':allresults,'checks':CHECKS,'all_passed':all(c['passed'] for c in CHECKS),'independent_integrations':SIMS,
            'elapsed_seconds':time.monotonic()-t0,'max_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'scope':'Recomputed source-selected pairs and independent continuous-CDF Euler dynamics; saved64scores reranked separately; same3consumed plants only; no retraining/noise/new mechanism.'}
    save('DYNAMICS_RESULTS.json',result)
    print(json.dumps({'all_passed':result['all_passed'],'checks':len(CHECKS),'integrations':SIMS,'elapsed_seconds':result['elapsed_seconds'],'max_rss':result['max_rss_bytes_macos']}),flush=True)

if __name__=='__main__':main()
