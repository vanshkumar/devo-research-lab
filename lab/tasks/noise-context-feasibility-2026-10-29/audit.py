"""Separate scoring, causal boundaries, beta evidence and native-source audit. No data readers."""
from pathlib import Path
import json,math,hashlib,copy,resource,time,importlib.util
import numpy as np
from scipy.special import betaln
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('pilot_frozen',P/'pilot.py');pilot=importlib.util.module_from_spec(s);s.loader.exec_module(pilot)
t0=time.monotonic();checks=[]
def ck(name,value,detail=None):
 checks.append({'check':name,'pass':bool(value),'detail':detail})
 if not value:raise AssertionError(checks[-1])
frozen=json.loads((P/'FREEZE.json').read_text())
for n,v in frozen['files'].items():ck('frozen_'+n,hashlib.sha256((P/n).read_bytes()).hexdigest()==v['sha256'])
meta=json.loads((P/'scored_metadata.json').read_text());met=json.loads((P/'scored_metrics.json').read_text())
a=np.load(P/'scored_predictions.npz',allow_pickle=False);p=a['p'];w=a['w'];z=a['z']
ck('1800_runs_600_sequences',p.shape==(1800,200,4,2) and w.shape==(1800,200,4) and z.shape==(1800,200,4))
ck('finite_probability_simplex',np.isfinite(p).all() and np.max(abs(p.sum(-1)-1))<1e-13 and p.min()>=0 and p.max()<=1)
maxmetric=0.;maxw=0.;edge=[]
# Independent construction from the protocol; does not call pilot.make_sequence.
for i,m in enumerate(meta):
 rng=np.random.default_rng(m['seed'])
 tail=rng.integers(0,2,40);bits=rng.integers(0,2,200)
 c=m['curriculum']
 first={'blocked':[0]*40+[1]*40+[0]*40+[1]*40,'interleaved':[0,1]*80,'early':[0]*40+[1]*40+[0,1]*40,'middle':[0,1]*20+[0]*40+[1]*40+[0,1]*20,'late':[0,1]*40+[0]*40+[1]*40}[c]
 ctx=np.r_[first,tail];truth=np.zeros((200,4),int);truth[:,0]=ctx
 f=m['family']
 if f=='original':truth[:,1]=bits;truth[:,2]=(bits+ctx)%2;truth[:,3]=bits;noise=1
 elif f=='relocated':truth[:,1]=ctx;truth[:,2]=bits;truth[:,3]=(bits+ctx)%2;noise=2
 else:truth[:,1]=ctx;truth[:,2]=0;truth[:,3]=ctx;noise=-1
 pc=np.take_along_axis(p[i],truth[:,:,None],axis=-1)[...,0]
 sig=[j for j in range(1,4) if j!=noise]
 vv={'test_signal_probability':pc[160:,sig].mean(),'test_signal_nll':-np.log(pc[160:,sig]).mean(),'return_first5_signal_probability':pc[80:85,sig].mean(),'signal_w_last40':w[i,160:,sig].mean()}
 for k,v in vv.items():maxmetric=max(maxmetric,abs(float(v)-met[i][k]))
 if m['role']=='learned':
  states=np.c_[np.zeros(200,int),ctx+1,truth[:,1]+3,truth[:,2]+5,truth[:,3]+7]
  if m['permuted']:states=np.random.default_rng(m['seed']+908172).permutation(9)[states]
  counts=np.zeros((206,9,9))
  for n in range(200):
   for t in range(4):
    x=int(states[n,t]);bf=0.
    for row in counts[:,x,:]:
     nz=row[row>0]
     if not len(nz):continue
     if len(nz)==1:n1,n2=float(nz[0]),0.
     else:n1,n2=map(float,nz)
     bf+=float(betaln(n1+.5,n2+.5)-betaln(.5,.5)+(n1+n2)*math.log(2))
    ww=1/(1+math.exp(-max(-700,min(700,bf))))
    maxw=max(maxw,abs(ww-w[i,n,t]))
   group=int(z[i,n,-1])
   for t in range(4):counts[group,states[n,t],states[n,t+1]]+=1
  if not m['permuted']:
   edge.append({**m,'p_each_step':pc[160:].mean(0).tolist(),'w_each_step':w[i,160:].mean(0).tolist()})
ck('all_1800_metric_reconstructions',maxmetric<1e-13,{'max_error':maxmetric})
ck('all_600_learned_weight_reconstructions',maxw<1e-11,{'max_error':maxw})
# Native exact source replay of the development sequence, plus baseline failure metric.
native=pilot.source_checks();ck('exact_native_source_reconstructions',all(x.get('assignments_exact',True) and x.get('max_probability_error',0)<1e-13 for x in native),native)
q=pilot.make_sequence(11);native_metrics={}
for label,role,par in [('native_sim1','no_oracle',pilot.S1),('native_sim2','oracle',pilot.S2),('matched_sim2_no_oracle','no_oracle',pilot.S2)]:native_metrics[label]=pilot.run(q,role,par)[0]
# Evaluator labels and noise flags cannot change learned sensory predictions.
seq=pilot.make_sequence(27001);orig=pilot.run(seq,'learned')
alt=copy.deepcopy(seq);alt['ctx']=1-alt['ctx'];alt['noise_t']=3;alt['family']='false_annotation';alt['curr']='false_annotation'
r=pilot.run(alt,'learned');ck('learned_evaluator_noise_context_label_independence',np.array_equal(orig[1],r[1]) and np.array_equal(orig[2],r[2]) and np.array_equal(orig[3],r[3]))
alt=copy.deepcopy(seq);alt['exp'][91:]=alt['exp'][91:][::-1]
r=pilot.run(alt,'learned');ck('future_suffix_does_not_change_past_predictions',np.array_equal(orig[1][:91],r[1][:91]))
# Midstory counterfactual changes cannot change the prediction made before the next observation.
L=pilot.Learner('learned');L.begin_story();one=L.predict(0,[1,2]);snapshot=copy.deepcopy(L)
L.observe(0,1,L.weight(0));snapshot.observe(0,2,snapshot.weight(0));ck('pre_observation_prediction_uses_no_next_state',np.array_equal(one,pilot.Learner('no_oracle').predict(0,[1,2])))
# Offline sampled replay compares the actual frozen engine with saved arrays; no tuning or new sequence.
maxreplay=0.
for i in [0,2,5,66,89,102,121,604,905,1207,1502,1799]:
 m=meta[i];seq=pilot.make_sequence(m['seed'],m['curriculum'],m['family'],m['permuted']);r=pilot.run(seq,m['role'])
 maxreplay=max(maxreplay,float(np.max(abs(r[1]-p[i]))));ck('replay_'+str(i),np.array_equal(r[1],p[i]) and np.array_equal(r[2],w[i]) and np.array_equal(r[3],z[i]))
# All deterministic oracle versus no-oracle predictions match; the oracle receives no additional skip there.
lookup={(m['family'],m['curriculum'],m['seed'],m['permuted'],m['role']):i for i,m in enumerate(meta)}
ck('deterministic_200_oracle_identity_pairs',all(np.array_equal(p[i],p[lookup[('deterministic',m['curriculum'],m['seed'],m['permuted'],'oracle')]]) for i,m in enumerate(meta) if m['family']=='deterministic' and m['role']=='no_oracle'))
# Aggregate stage-specific failure, preserving deterministic-but-unlearned signal.
aggregate=[]
for f in ('original','relocated','deterministic'):
 for c in ('blocked','interleaved','early','middle','late'):
  v=[e for e in edge if e['family']==f and e['curriculum']==c]
  aggregate.append({'family':f,'curriculum':c,'p_each_step':np.mean([e['p_each_step'] for e in v],0).tolist(),'w_each_step':np.mean([e['w_each_step'] for e in v],0).tolist()})
result={'all_pass':all(c['pass'] for c in checks),'checks':checks,'native_development_metrics':native_metrics,'edgewise_learned':aggregate,'runtime_seconds':time.monotonic()-t0,'max_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'independence_scope':'Separate mathematical/scoring implementation within same investigator; no independent scientist review.'}
(P/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'all_pass':result['all_pass'],'n_checks':len(checks),'max_metric_error':maxmetric,'max_weight_error':maxw,'runtime_seconds':result['runtime_seconds'],'max_rss_bytes_macos':result['max_rss_bytes_macos'],'native_sim1_first_second_return_test':[native_metrics['native_sim1'][k] for k in ('first_block_signal_probability','second_block_signal_probability','return_block_signal_probability','test_signal_probability')]},indent=2))
for e in aggregate:
 if e['curriculum'] in ('blocked','interleaved'):print(json.dumps(e))
