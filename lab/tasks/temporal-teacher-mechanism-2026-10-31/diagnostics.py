"""Predeclared fidelity/noise challenges, direct scoring and scalar-log replay."""
import os,sys
sys.dont_write_bytecode=True
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='2'
import io,json,hashlib,time
import numpy as np
from scipy.sparse import csc_matrix
import core as c
from common import ROOT,HERE,SOURCE,read,save,now,check_deadline
from actor import Actor
from batched import Circuit,signals,segment_loss,rle_from_waveform,input_moments
from dev_joint import phases
INPUTS={}

def loadz(p):
    blob=read(p,'generated_output_reuse');INPUTS[str(p.relative_to(ROOT))]={'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}
    with np.load(io.BytesIO(blob),allow_pickle=False) as z:out={k:z[k].copy() for k in z.files}
    INPUTS[str(p.relative_to(ROOT))]['decoded_memory_bytes']=sum(v.nbytes for v in out.values())
    return out

def packed(d):
    m=Circuit.__new__(Circuit)
    for k in ('JT','h','inv_tau','maximum','threshold','width'):setattr(m,k,d[k])
    m.NE=600;m.NI=150;m.quiet_rate=float(d.get('quiet_rate',0.))
    return m,{'mean':d['prototype_mean'],'variance':d['prototype_variance']}

def render(y,starts,ends):
    out=np.zeros((c.T,len(y),c.N))
    for b in range(len(y)):
        for j in range(6):out[starts[b,j]:ends[b,j],b]=y[b,j]
    return out

def independent_waveform(action,d,orders,phase=0):
    # Separate samplewise reconstruction, not the segment-overlap loss.
    u=np.tensordot(d['basis'],action[:4],axes=([2],[0]))+d['bias'];u=np.maximum(u,0)
    u=u-u.mean(1,keepdims=True);u=2*u/np.maximum(np.sqrt(np.mean(u*u,axis=1,keepdims=True)),1e-12)
    u=u[orders[int(action[4])]];a=np.zeros((2200,100))
    for j in range(6):
        lo=150+int(phase)+int(np.rint(j*150*action[5]));hi=lo+int(np.rint(100*action[5]));a[lo:hi]=u[j]
    return a

def predict(aa,d,orders,m,p,m0,p0,pack,ss=None,ee=None,noise=None,emissions=None):
    y,starts,ends,valid=signals(aa,d['basis'],d['bias'],orders,np.zeros(len(aa),int))
    if emissions is not None:y=emissions;valid=np.mean(y*y,axis=2)>1e-8
    if ss is not None:starts,ends=ss,ee
    mom,_=m.run(y,starts,ends,noise=noise);mom0,_=m0.run(y,starts,ends,noise=noise)
    raw=mom[:,:600].mean(1)*100;active=((ends-starts)*valid).sum(1)
    clean=render(y,starts,ends);aud=clean if noise is None else clean+noise
    memory={k:pack[k] for k in ('emissions','starts','durations')};teacher=pack['teacher']
    inp=np.stack([np.r_[(aud[:,j]/2).mean(0),(aud[:,j]**2/4).mean(0)] for j in range(len(aa))])
    costs={'raw':raw,'normalized':(raw-m.quiet_rate)*c.T/np.maximum(active,1),
           'population':np.mean((mom-p['mean'])**2/p['variance'],axis=1),
           'unplasticized_population':np.mean((mom0-p0['mean'])**2/p0['variance'],axis=1),
           'state':np.array([c.state_cost(aud[:,j],memory) for j in range(len(aa))]),
           'template':np.array([c.template_cost(aud[:,j],teacher) for j in range(len(aa))]),
           'input_moments':np.mean((inp-pack['input_mean'])**2/pack['input_scale'],axis=1)}
    return costs,clean

def reference_net(m):
    j=m.JT.T
    return c.models.EINet(600,150,15,1/15,(100,0,2),(100,0,2),30,10,
                         csc_matrix(j[:600,:600]),csc_matrix(-j[:600,600:]),
                         csc_matrix(j[600:,:600]),csc_matrix(-j[600:,600:]),w0_std=0,cW=.05)

def main():
    frozen=json.loads(read(HERE/'FREEZE.json','freeze_record'))
    for name,digest in frozen['hashes'].items():assert hashlib.sha256(read(ROOT/name,'frozen_code_verification')).hexdigest()==digest,name
    save('DIAGNOSTICS_FREEZE.json',{'utc':now(),'diagnostics_sha256':hashlib.sha256(read(HERE/'diagnostics.py','diagnostics_pre_run_pin')).hexdigest(),
                                   'protocol':'FROZEN_PROTOCOL.md','config':'CONFIG.json','scientific_choices_changed':False})
    cfg=json.loads((HERE/'CONFIG.json').read_text());held=json.loads(read(HERE/'outputs/HELD.json','saved_result_summary'))
    assert held['complete'];checks=[];case_results=[];started=time.monotonic()
    for case in cfg['case_ids']:
        check_deadline();pack=loadz(SOURCE/('held_%03d_model.npz'%case));fixed=loadz(SOURCE/('held_%03d_fixed_model.npz'%case))
        env=loadz(SOURCE/('held_%03d_environment.npz'%case));truth=loadz(SOURCE/('held_%03d_truth.npz'%case));m,p=packed(pack);m0,p0=packed(fixed)
        d={k:env[k] for k in ('basis','bias')};orders=env['orders'];target=np.r_[truth['target'],float(truth['target_order']),float(truth['target_stretch'])]
        teacher=pack['teacher'];target_rle=rle_from_waveform(teacher);memory={k:pack[k] for k in ('emissions','starts','durations')}
        query_logs={};enriched=[]
        source_rows=next(x for x in held['results'] if x['case']==case)['results']
        for row in source_rows:
            mode=row['mode'];q=loadz(HERE/('outputs/held_%03d_%s_queries.npz'%(case,mode)));query_logs[mode]=q
            a=Actor(env['initial'],180000+case);cursor=0;traj=[]
            while a.stage!='done':
                aa=a.ask();n=len(aa);assert np.array_equal(aa,q['query_actions'][cursor:cursor+n]);a.tell(q['query_costs'][cursor:cursor+n]);cursor+=n
            assert cursor==cfg['logical_queries_per_actor'];assert np.array_equal(a.arrays()['actions'],q['actions'])
            assert a.current['value']<=q['query_costs'].min()+1e-12
            # Independently reconstruct final/reference/sample-query waveform errors.
            final=q['actions'][-1];aud=independent_waveform(final,d,orders);gold=c.template_cost(aud,teacher)
            assert abs(gold-row['final_gold'])<1e-10
            reference=independent_waveform(np.r_[env['initial'],1.,.8],d,orders);g0=c.template_cost(reference,teacher)
            assert abs(g0-row['initial_gold'])<1e-10
            inds=np.linspace(0,len(q['query_actions'])-1,8,dtype=int)
            for index in inds:
                action=q['query_actions'][index];aud=independent_waveform(action,d,orders,37)
                yy,ss,ee,v=signals(action[None],d['basis'],d['bias'],orders,np.array([37]))
                analytic=float(segment_loss(yy,ss,ee,v,target_rle)[0]);direct=c.template_cost(aud,teacher)
                assert abs(analytic-direct)<1e-10;assert abs(c.state_cost(aud,memory)-direct)<1e-10
                if mode in ('state','template','oracle'):assert abs(direct-q['query_costs'][index])<1e-10
            semantic=target.copy();semantic[4]=final[4];order_error=c.template_cost(independent_waveform(semantic,d,orders),teacher)
            stretch_error=abs(final[5]-target[5]);success=(row['improvement']>=.95 and gold<=.1 and stretch_error<=.02)
            # Consumed-log diagnostic only: never feed this gold hindsight to the actor.
            qy,qs,qe,qv=signals(q['query_actions'],d['basis'],d['bias'],orders,np.zeros(cursor,int))
            query_gold=segment_loss(qy,qs,qe,qv,target_rle);best_index=int(np.argmin(query_gold));best_gold=float(query_gold[best_index])
            direct_best=c.template_cost(independent_waveform(q['query_actions'][best_index],d,orders),teacher)
            assert abs(best_gold-direct_best)<1e-10
            np.savez_compressed(HERE/('outputs/held_%03d_%s_gold_queries.npz'%(case,mode)),gold=query_gold)
            enriched.append({**{k:v for k,v in row.items() if k!='trajectory_gold'},'semantic_order_mse':order_error,
                             'correct_semantic_order':order_error<=1e-12,'abs_stretch_error':stretch_error,'success':bool(success),
                             'best_queried_gold':best_gold,'best_gold_query_index':best_index,'regression_from_best_queried_gold':gold-best_gold,
                             'best_gold_query_cost_minus_final_cost':float(q['query_costs'][best_index]-a.current['value'])})
            checks.append({'case':case,'mode':mode,'replayed_queries':cursor,'direct_waveform_checks':11,'passed':True})
        # Validate source-valued query costs, independently of saved gold scores.
        for mode in ('raw','normalized','population','unplasticized_population'):
            q=query_logs[mode];ii=[0,len(q['query_actions'])-1];aa=q['query_actions'][ii]
            yy,ss,ee,v=signals(aa,d['basis'],d['bias'],orders,phases(aa,390000+case));mm,_=(m0 if mode=='unplasticized_population' else m).run(yy,ss,ee)
            if mode=='raw':values=mm[:,:600].mean(1)*100
            elif mode=='normalized':values=(mm[:,:600].mean(1)*100-m.quiet_rate)*2200/np.maximum(((ee-ss)*v).sum(1),1)
            else:
                proto=p0 if mode=='unplasticized_population' else p;values=np.mean((mm-proto['mean'])**2/proto['variance'],axis=1)
            assert np.max(np.abs(values-q['query_costs'][ii]))<1e-10
        # Fixed policy probes: exact tutor content, plus acquired content/duration.
        pop_final=query_logs['population']['actions'][-1]
        exact=np.tile(target,(64,1));exact[:,4]=np.arange(64)
        acquired=np.tile(pop_final,(64,1));acquired[:,4]=np.arange(64)
        extras=[];labels=[]
        for phase in cfg['diagnostic_onsets_ms']:extras.append(target.copy());labels.append('onset_%d'%phase)
        for factor in cfg['diagnostic_duration_multipliers']:
            a=target.copy();a[5]=np.clip(a[5]*factor,.7,1.25);extras.append(a);labels.append('duration_%g'%factor)
        a=target.copy();a[:4]=np.clip(a[:4]+cfg['diagnostic_content_delta'],-2,2);extras.append(a);labels.append('content_edit')
        extras.append(target.copy());labels.append('gap_edit')
        aa=np.concatenate([exact,acquired,np.array(extras)]);yy,ss,ee,v=signals(aa,d['basis'],d['bias'],orders,np.zeros(len(aa),int))
        for j,phase in enumerate(cfg['diagnostic_onsets_ms']):ss[128+j]+=phase;ee[128+j]+=phase
        ss[-1,1]+=20;ee[-1,1]+=20
        costs,clean=predict(aa,d,orders,m,p,m0,p0,pack,ss,ee)
        save('outputs/fidelity_%03d_predictions.json'%case,{'case':case,'actions':aa,'starts':ss,'ends':ee,'extra_labels':labels,'costs':costs})
        gold=np.array([c.template_cost(clean[:,j],teacher) for j in range(len(aa))]);order_equiv=gold[:64]<=1e-12
        fidelity={}
        for mode,values in costs.items():
            fidelity[mode]={}
            for label,lo in (('exact_content',0),('acquired_content',64)):
                vv=values[lo:lo+64];correct=vv[order_equiv].min();wrong=vv[~order_equiv].min();gap=float(wrong-correct)
                fidelity[mode][label]={'best_wrong_minus_best_correct':gap,'strict_correct':gap>1e-12,'tie':abs(gap)<=1e-12,
                                      'target_best_rank':int(1+np.sum(vv<correct-1e-12)),'best_policy':int(np.argmin(vv))}
        save('outputs/fidelity_%03d_scored.json'%case,{'case':case,'gold':gold,'equivalent_orders':np.flatnonzero(order_equiv),'fidelity':fidelity})
        temporal={label:{'gold':float(gold[128+j]),'costs':{mode:float(values[128+j]) for mode,values in costs.items()}} for j,label in enumerate(labels)}
        # The adversarial choice is now made from saved predictions, excluding observable equivalences.
        bad=np.flatnonzero(~order_equiv);adversary=int(bad[np.argmin(costs['population'][bad])])
        noise_actions=np.tile(target,(6,1));noise_actions[1,4]=adversary;noise_actions[2,4]=2
        noise_actions[3,5]=np.clip(target[5]*.9,.7,1.25);noise_actions[4,5]=np.clip(target[5]*1.1,.7,1.25)
        ny,ns,ne,nv=signals(noise_actions,d['basis'],d['bias'],orders,np.zeros(6,int));ns[-1,1]+=20;ne[-1,1]+=20
        # Reverse the observed target sequence itself, even outside the64policy menu.
        ny[2]=ny[0,::-1]
        clean_noise=render(ny,ns,ne);active=np.mean(clean_noise*clean_noise,axis=2)>1e-8
        noise_predictions=[];noise_source_check=None
        for level,sigma in enumerate(cfg['noise_sigma']):
            for rep in range(cfg['noise_replicates']):
                seed=cfg['noise_seed_offset']+100*case+10*level+rep;rng=np.random.default_rng(seed)
                extra=rng.normal(0,sigma,clean_noise.shape)*active[:,:,None]
                cc,_=predict(noise_actions,d,orders,m,p,m0,p0,pack,ns,ne,extra,ny)
                noise_predictions.append({'level':level,'sigma':sigma,'replicate':rep,'seed':seed,'costs':cc})
                if case==400 and level==0 and rep==0:
                    _,tr=m.run(ny[:1],ns[:1],ne[:1],trace=True,noise=extra[:,:1]);net=reference_net(m)
                    ref,_=c.simulate(net,clean_noise[:,0]+extra[:,0],(m.h[:600],m.h[600:]));error=float(np.max(np.abs(ref-tr[0])))
                    assert error<1e-10;noise_source_check={'max_trace_error':error,'sigma':sigma,'seed':seed}
                check_deadline()
        save('outputs/noise_%03d_predictions.json'%case,{'case':case,'actions':noise_actions,'starts':ns,'ends':ne,'emissions':ny,
             'reverse_target_emission_override_index':2,'adversarial_order':adversary,'rows':noise_predictions})
        ngold=np.array([c.template_cost(clean_noise[:,j],teacher) for j in range(6)]);right=ngold<=1e-12;noise_scores=[]
        for pred in noise_predictions:
            scores={}
            for mode,values in pred['costs'].items():
                values=np.asarray(values);ties=np.flatnonzero(values<=values.min()+1e-12);chosen=int(ties[0])
                scores[mode]={'chosen':chosen,'chosen_correct':bool(right[chosen]),'correct_in_tie':bool(np.any(right[ties])),
                              'strict_correct':bool(np.all(right[ties])),'wrong_minus_correct_margin':float(values[~right].min()-values[right].min())}
            noise_scores.append({'sigma':pred['sigma'],'replicate':pred['replicate'],'scores':scores})
        save('outputs/noise_%03d_scored.json'%case,{'case':case,'clean_gold':ngold,'correct_indices':np.flatnonzero(right),'rows':noise_scores,'source_check':noise_source_check})
        case_results.append({'case':case,'repeated':bool(truth['repeated']),'results':enriched,'fidelity':fidelity,'temporal_probes':temporal,'noise':noise_scores})
        save('outputs/DIAGNOSTICS.json',{'updated_utc':now(),'complete':len(case_results)==8,'cases':case_results,'checks':checks})
        save('INPUT_MANIFEST.json',INPUTS)
        print(json.dumps({'case':case,'diagnostics_complete':True,'elapsed':time.monotonic()-started,'source_noise_check':noise_source_check,
                          'results':[{k:v for k,v in row.items() if k in ('mode','final_gold','success','correct_semantic_order','abs_stretch_error')} for row in enriched]}),flush=True)
    assert len(checks)==64
if __name__=='__main__':main()
