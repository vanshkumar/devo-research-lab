"""Reproduction verification, not another contrary: first task + full cache."""
from collections import OrderedDict
import hashlib
import json
import math
from pathlib import Path
import random
import resource
import time
import traceback

HERE=Path(__file__).resolve().parent
AUTHOR=HERE.parent.parent/'tasks'/'plasticity-renewal-order-consequence-2026-11-02'
NAMES=['cbp_literal','cbp_mean','cbp_literal_replay','cbp_mean_replay',
       'random_literal_replay','random_mean_replay','sgd_replay']
READS=[]; START=time.perf_counter()


def read(path):
    raw=path.read_bytes()
    READS.append(dict(path=str(path),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    return raw


class Model:
    def __init__(self,t,name,seed):
        self.t=t[:]; self.name=name
        self.age=[0]*5;self.mu=[0.]*5;self.u=[0.]*5
        self.r=random.Random(seed+1000);self.e=random.Random(seed+1011)
        self.bins=[];self.loss=0.;self.n=0;self.events=0

    def step(self,key,y,record):
        t=self.t; active=[k for k in range(20) if key&(1<<k)]
        h=[max(0.,t[21*j+20]+sum(t[21*j+k] for k in active)) for j in range(5)]
        err=t[110]+sum(t[105+j]*h[j] for j in range(5))-y
        v=t[105:110]
        for j in range(5):
            if h[j]>0:
                change=.02*err*v[j]
                for k in active:t[21*j+k]-=change
                t[21*j+20]-=change
            t[105+j]-=.02*err*h[j]
        t[110]-=.02*err
        self.n+=1
        if self.name!='sgd_replay':
            score=[]
            for j in range(5):
                self.age[j]+=1
                self.mu[j]=.99*self.mu[j]+.01*h[j]
                corr=1-.99**self.age[j]
                if self.name.startswith('random'):
                    util=0.
                else:
                    util=abs(t[105+j])*abs(h[j]-self.mu[j]/corr)/(sum(abs(t[21*j+k]) for k in range(20))/20)
                self.u[j]=.99*self.u[j]+.01*util
                score.append(self.u[j]/corr)
            if self.name.startswith('random'):score=[self.r.random() for _ in range(5)]
            eligible=[j for j in range(5) if self.age[j]>10]
            if eligible and self.e.random()<=.0001*len(eligible):
                j=min(eligible,key=lambda a:(score[a],a))
                self.u[j]=0.
                if '_mean' in self.name:t[110]+=t[105+j]*self.mu[j]/(1-.99**self.age[j])
                for k in range(20):t[21*j+k]=self.r.uniform(-math.sqrt(.3),math.sqrt(.3))
                t[21*j+20]=0.;t[105+j]=0.;self.mu[j]=0.;self.age[j]=0
                self.events+=1
        return err*err


def main():
    assert not (HERE/'VERIFICATION.json').exists()
    rows=[]
    for seed in range(240001,240009):
        d=json.loads(read(AUTHOR/f'REALIZATION_{seed}.json'))
        o=json.loads(read(AUTHOR/f'OUTPUT_{seed}.json'))
        basekeys=[sum(b<<k for k,b in enumerate(c)) for c in d['contexts'][:100]]
        supports=[[base|(f<<15) for f in range(32)] for base in basekeys]
        labels=d['targets_by_context'][:100] # These labels were independently regenerated in RECONSTRUCTION.
        models={n:Model(d['initial_learner'],n,seed) for n in NAMES}
        sample=random.Random(seed+2000); insert=random.Random(seed+3000); reservoir=[]
        modelbins={n:[] for n in NAMES}; modelbin={n:0. for n in NAMES}
        memo=OrderedDict();total=0;seen=0;hits=0;cachebin=0.;cachebins=[];matrix=[]
        max_cache_gap=0.;max_neural_gap=0.;max_bin_gap=0.
        for i,fast in enumerate(d['fast_indices'][:1_000_000]):
            task=i//10000;key=supports[task][fast];y=labels[task][fast]
            if i<10000:
                old=reservoir[sample.randrange(len(reservoir))] if reservoir else None
                draw=insert.randrange(i+1)
                for n,m in models.items():
                    loss=m.step(key,y,False)
                    if old is not None and n.endswith('_replay'):m.step(*old,False)
                    modelbin[n]+=loss
                if len(reservoir)<506:reservoir.append((key,y))
                elif draw<506:reservoir[draw]=(key,y)
            if key in memo:
                prediction=memo[key];hits+=1
            else:prediction=total/seen if seen else 0.
            cachebin+=(prediction-y)**2
            memo.pop(key,None);memo[key]=y
            if len(memo)>677:memo.popitem(last=False)
            seen+=1;total+=y
            if (i+1)%1000==0:
                cachebins.append(cachebin/1000);cachebin=0.
                if i<10000:
                    for n in NAMES:
                        modelbins[n].append(modelbin[n]/1000);modelbin[n]=0.
            if (i+1)%10000==0:
                fallback=total/seen
                row=[math.fsum((memo.get(k,fallback)-v)**2 for k,v in zip(supports[j],labels[j]))/32 for j in range(task+1)]
                matrix.append(row)
                max_cache_gap=max(max_cache_gap,max(abs(a-b) for a,b in zip(row,o['risk_matrices']['cache'][task])))
                if task==0:
                    for n,m in models.items():
                        max_neural_gap=max(max_neural_gap,max(abs(a-b) for a,b in zip(m.t,o['learner_snapshots'][n][0])))
                        max_bin_gap=max(max_bin_gap,max(abs(a-b) for a,b in zip(modelbins[n],o['online_1000_bins'][n][:10])))
        old=o['cache_final']
        assert list(memo)==old['keys'] and list(memo.values())==old['labels']
        assert (hits,seen,total)==(old['hits'],old['count'],old['total'])
        max_cache_bin=max(abs(a-b) for a,b in zip(cachebins,o['online_1000_bins']['cache']))
        assert max_cache_gap<1e-11 and max_cache_bin<1e-11
        assert max_neural_gap<1e-10 and max_bin_gap<1e-10,(seed,max_neural_gap,max_bin_gap)
        rows.append(dict(seed=seed,cache_examples=seen,cache_hits=hits,cache_misses=seen-hits,
                         cache_all5050_boundary_risks_max_gap=max_cache_gap,cache_all1000_online_bins_max_gap=max_cache_bin,
                         first_task_all7_neural_arms_max_weight_gap=max_neural_gap,first_task_all70_online_bins_max_gap=max_bin_gap,
                         independent_first_task_neural_steps={n:m.n for n,m in models.items()},
                         independent_first_task_replacements={n:m.events for n,m in models.items()},
                         independent_cache_scoring_predictions=161600))
        print(json.dumps(rows[-1]),flush=True)
        assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<1_000_000_000
        assert time.perf_counter()-START<600
    audit=json.loads(read(AUTHOR/'AUDIT.json'))
    manifest=json.loads(read(AUTHOR/'REPRODUCTION_MANIFEST.json'))
    output=dict(status='PASS',utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),per_teacher=rows,
                verification_not_new_contrary=True,new_teacher_or_random_realization=False,
                full_cache_replay=True,full_neural_learning_replay=False,remaining_neural99_tasks_online_errors_inherited=True,
                author_audit_top_level_keys=list(audit),author_manifest=manifest,
                reads=READS,explicit_file_read_bytes=sum(r['bytes'] for r in READS),
                conservative_read_hash_decode_bytes=3*sum(r['bytes'] for r in READS)+1_000_000,
                seconds=time.perf_counter()-START,peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (HERE/'VERIFICATION.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:output[k] for k in ['status','utc','seconds','peak_rss_bytes_macos','explicit_file_read_bytes','author_audit_top_level_keys']}),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException:
        (HERE/'VERIFICATION_FAILURE.txt').write_text(traceback.format_exc())
        (HERE/'VERIFICATION_FAILURE_RESOURCES.json').write_text(json.dumps(dict(seconds=time.perf_counter()-START,
            reads=READS,peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2))
        raise
