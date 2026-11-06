"""Scalar-only, target-blind duration/order multistart motor search."""
import numpy as np
def choose(v):
    v=np.asarray(v);return int(np.flatnonzero(v<=v.min()+1e-14)[0])
def best(states):return states[choose([s['value'] for s in states])]
def rank_states(states):
    left=list(states);out=[]
    while left:out.append(left.pop(choose([s['value'] for s in left])))
    return out
class Actor:
    def __init__(self,initial,seed):
        self.rng=np.random.default_rng(seed);self.states=[];self.queries=[];self.values=[];self.trajectory=[];self.stage='initial';self.round=0
        for order in range(6):
            for stretch in (.75,1.,1.25):self.states.append({'x':np.r_[initial,float(order),stretch],'value':np.inf,'step':np.r_[np.full(4,.4),.08]})
        self.current=None;self.pending=None
    def ask(self):
        if self.stage=='done':return None
        if self.stage=='initial':self.pending=[s['x'].copy() for s in self.states];return np.array(self.pending)
        if self.stage in ('search1','search2','refine'):
            broad=self.rng.uniform(np.r_[np.full(4,-2.),.7],np.r_[np.full(4,2.),1.25],size=(2,5));pp=[]
            for s in self.states:
                for j in range(5):
                    k=j if j<4 else 5
                    for sign in (1.,-1.):
                        a=s['x'].copy();a[k]=np.clip(a[k]+sign*s['step'][j],-2 if j<4 else .7,2 if j<4 else 1.25);pp.append(a)
                pp.extend(np.r_[b[:4],s['x'][4],b[4]] for b in broad)
            self.pending=pp;return np.array(pp)
        if self.stage in ('expand1','expand2'):
            self.pending=[np.r_[self.current['x'][:4],float(order),self.current['x'][5]] for order in range(64)]
            return np.array(self.pending)
        raise RuntimeError(self.stage)
    def tell(self,values):
        vv=np.asarray(values);self.queries.extend(np.array(self.pending));self.values.extend(vv.tolist())
        if self.stage=='initial':
            for s,v in zip(self.states,vv):s['value']=float(v)
            self.stage='search1';self.round=0
        elif self.stage in ('search1','search2','refine'):
            for i,s in enumerate(self.states):
                v=vv[i*12:(i+1)*12];k=choose(v)
                if v[k]<s['value']-1e-14:s['x']=np.array(self.pending[i*12+k]);s['value']=float(v[k])
                else:s['step']=np.maximum(np.r_[np.full(4,.00625),.00125],s['step']/2)
            self.round+=1
            if self.stage=='search1' and self.round==12:self.states=rank_states(self.states)[:6];self.stage='search2';self.round=0
            elif self.stage=='search2' and self.round==12:self.stage='expand1'
            elif self.stage=='refine' and self.round==10:self.stage='expand2'
        elif self.stage in ('expand1','expand2'):
            k=choose(vv);base=self.current
            if vv[k]<base['value']-1e-14:base={'x':np.array(self.pending[k]),'value':float(vv[k]),'step':np.r_[np.full(4,.05),.02]}
            self.states=[base]
            self.stage='refine' if self.stage=='expand1' else 'done';self.round=0
        self.current=best(self.states)
        self.trajectory.append(self.current['x'].copy())
    def arrays(self):return {'query_actions':np.array(self.queries),'query_costs':np.array(self.values),'actions':np.array(self.trajectory)}
