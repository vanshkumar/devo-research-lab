"""Frozen independent whole-case generation and complete scalar learning."""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import copy,hashlib,importlib.util,json,pickle,time
import numpy as np
import core as c
from common import ROOT,HERE,SOURCE,read,save,now,check_deadline,charge
from dev_joint import run_case
from batched import Circuit,signals

def helper_load():
    p=ROOT/'experiments/sensory_evaluator_preflight_2026-10-28/preflight.py'
    spec=importlib.util.spec_from_file_location('temporal_preflight',p)
    helper=importlib.util.module_from_spec(spec);sys.modules[spec.name]=helper;spec.loader.exec_module(helper)
    return helper

def freeze():
    files=[HERE/x for x in ('CONFIG.json','FROZEN_PROTOCOL.md','held_study.py','actor.py','core.py','batched.py','dev_joint.py','common.py')]
    files += [ROOT/'experiments/sensory_evaluator_preflight_2026-10-28/preflight.py']
    files += sorted((ROOT/'sources/sensory_evaluator_feasibility_2026-10-28/upstream/src').glob('*.py'))
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(read(p,'pre_generation_code_pin')).hexdigest() for p in files}
    assert not (HERE/'FREEZE.json').exists(),'preserve existing freeze; do not regenerate'
    save('FREEZE.json',{'frozen_utc':now(),'hashes':hashes,'new_cases_generated':False})

def main():
    freeze();cfg=json.loads((HERE/'CONFIG.json').read_text());helper=helper_load();all_results=[]
    for case,stretch in zip(cfg['case_ids'],cfg['target_stretches']):
        check_deadline();start=time.monotonic();seed=cfg['case_seed_offset']+case;np.random.seed(seed);rng=np.random.default_rng(seed)
        basis=rng.normal(size=(6,100,4))/2;bias=rng.normal(-.4,.2,(6,100))
        if case in cfg['repeated_cases']:
            basis[2]=basis[0];bias[2]=bias[0];basis[4]=basis[1];bias[4]=bias[1]
        net0,means=helper.initialize(rng);net=copy.deepcopy(net0)
        target=rng.uniform(-1,1,4);initial=rng.uniform(-1,1,4);order=int(rng.integers(0,6));observation_phase=int(rng.integers(-60,61))
        phases=rng.choice(cfg['training_phase_choices_ms'],35);goal=c.features(target,basis,bias)[c.PERMS[order]]
        teacher=c.waveform(goal,stretch,observation_phase)
        np.savez(SOURCE/('held_%03d_truth.npz'%case),target=target,target_order=order,target_stretch=stretch,seed=seed,
                 observation_phase=observation_phase,training_phases=phases,repeated=case in cfg['repeated_cases'])
        # Remove the100msprobe padding while preserving the full1100mstraining rendition.
        aud=np.concatenate([np.zeros((500,600))]+[np.repeat(c.waveform(goal,stretch,int(p))[100:1200],6,axis=1) for p in phases])
        rh=np.zeros((len(aud),15));t=time.monotonic()
        trained=net.sim(np.full(600,-10.),np.full(150,-1.),rh,aud,[],len(aud),1,0,
                        plasticity={'JEI':helper.bilin_hebb_EI,'JIE':helper.bilin_hebb_IE},lr={'JEI':.05,'JIE':.006},tauW=1e5,
                        JEI0_mean=means[1],JIE0_mean=means[2],asyn_E=10,asyn_I=0,rE_th=1.5,rI_th=5,no_progress_bar=True)
        training_seconds=time.monotonic()-t;del trained,aud,rh
        with (SOURCE/('held_%03d_circuits.pkl'%case)).open('wb') as f:pickle.dump({'net35':net,'net0':net0},f,pickle.HIGHEST_PROTOCOL)
        d={'basis':basis,'bias':bias}
        if case==400:
            h=c.quiet(net);model=Circuit(net,h);actions=np.array([np.r_[initial,2.,.83],np.r_[target,float(order),stretch]])
            menus=c.policies(98100+case);yy,ss,ee,_=signals(actions,basis,bias,menus,np.array([-80,80]));mom,tr=model.run(yy,ss,ee,trace=True);errors=[]
            for j in range(2):
                ref,_=c.simulate(net,c.waveform(yy[j],actions[j,5],(-80,80)[j]),h)
                errors.append(float(np.max(np.abs(tr[j]-ref))));assert errors[-1]<1e-10
            save('outputs/HELD_SOURCE_CHECK.json',{'case':case,'trace_errors':errors})
            del tr,ref
        result=run_case(case,d,net,teacher,initial,'held',net0=net0)
        all_results.append({'case':case,'seed':seed,'target_stretch_environment_only':stretch,'target_order_environment_only':order,
                            'repeated':case in cfg['repeated_cases'],'training_seconds':training_seconds,'results':result['results']})
        save('outputs/HELD.json',{'updated_utc':now(),'complete':len(all_results)==8,'results':all_results})
        print(json.dumps({'case':case,'case_complete':True,'seconds':time.monotonic()-start}),flush=True)
        del net,net0,result
if __name__=='__main__':main()
