"""Generated curriculum histories and exact conditional six-response trees."""
import importlib.util
import resource
import time

import numpy as np
from scipy.special import expit

from calibrate import FAST, SLOW, STAGE, binary_offsets, predictors, signal
from source import BYTES, HERE, blob, check, get, save, utc
from tracker import DECAY, RETENTION, psych

N = 128
ACTORS = ('existing','session','history','track','drift')
STRESSES = ('nominal','engagement_shift')
ASSAYS = np.array([[1,-.5,-1,.5,-1,1],[1,-1,1,-1,1,-1],[1,-1,1,-1,-.5,.5]])
ORDER = ('reactive','ordinary','composition_matched')
OUTCOMES = np.array([1,0,-1])


def random_schedule(rng):
    parts = []
    for span,medium in ((200,(80,110)),(160,(60,90)),(40,(20,20))):
        ranks = np.argsort(rng.random((span,N)),axis=0)
        xs = []
        for n in medium:
            bins = np.repeat([-1,-.5,.5,1],[(span-n)//2,n//2,n//2,(span-n)//2])
            check(len(bins)==span,'Curriculum counts')
            xs.append(bins[ranks])
        parts.append(np.stack(xs,axis=1))
    x = np.concatenate(parts)
    check(np.array_equal(x[-40:,0],x[-40:,1]),'Shared terminal schedule')
    return x.reshape((400,2*N))


def project(x,beta):
    return np.einsum('ij,j->i',x,beta)


class Actor:
    def __init__(self, model, name, base, coeff, track_rate, stress):
        self.model = model
        self.name = name
        self.base = base
        self.coeff = coeff
        self.track_rate = track_rate
        self.stress = stress

    def before(self,state,day):
        if day:
            state['trace'][:,:2] = 0
            if self.model is not None and getattr(self.model,'rho',1.)!=1.:
                self.model.pretrial(state,True)
            if self.name=='track':
                state['w'] *= RETENTION

    def probabilities(self,state,x,t,pos):
        f = psych(x)
        bx,bq = binary_offsets(x,self.base)
        d = predictors(x,t,pos,state['trace'])
        o = expit(bq+project(d[2][1],self.coeff[2][1])+state['omit_shift'])
        if self.stress:
            o = np.minimum(.995,o+.02*(np.abs(x)==.5))
        if self.model is None:
            k = 1 if self.name=='drift' else 2
            p = bx+project(d[k][0],self.coeff[k][0])
            if self.name=='track':
                p += np.einsum('ij,ij->i',f,state['w'])
        else:
            p = np.einsum('ij,ij->i',f,state['w'])
        return expit(p+state['choice_shift']),o

    def update(self,state,x,c,p,day=False):
        r = np.where(c==-np.sign(x),1,-1)
        if self.model is not None:
            self.model.update(state,x,c,r,session_start=day)
        if self.name=='track':
            state['w'] *= DECAY
            state['w'] += self.track_rate*(((c<0)-p)*(c!=0))[:,None]*psych(x)
        ev = signal(x,c,r)
        trace = state['trace']
        trace[:,0] = ev
        trace[:,1] = FAST*trace[:,1]+(1-FAST)*ev
        trace[:,2] = SLOW*trace[:,2]+(1-SLOW)*ev
        return r


def initial(name,start,track,rng,stress):
    state = {'trace':np.tile(np.asarray(start['traces']),(2*N,1,1))}
    draws = rng.standard_normal((N,5))
    state['choice_shift'] = np.tile(draws[:,0]*.35*stress,2)
    state['omit_shift'] = np.tile(draws[:,1]*.50*stress,2)
    if name in ('existing','session'):
        s = start['recurrent'][name]
        c = np.asarray(s['cov'])
        v,u = np.linalg.eigh((c+c.T)/2)
        check(v.min()>-1e-10,'Invalid archived marginal covariance')
        spread = .5*stress*np.einsum('ij,kj->ik',draws[:,2:],u*np.sqrt(np.maximum(v,0)))
        state['w'] = np.tile(np.asarray(s['w'])+spread,(2,1))
        state['h'] = np.tile(np.asarray(s['h']),(2*N,1))
    if name=='track':
        state['w'] = np.tile(np.asarray(track),(2*N,1))
    return state


def train(actor,state,x,u):
    perf = np.zeros((3,2*N))
    for t,contrast in enumerate(x):
        day = t in (0,200)
        actor.before(state,day)
        p,o = actor.probabilities(state,contrast,STAGE+t,t%200)
        c = np.where(np.tile(u[t,0],2)<p,-1,1)
        c[np.tile(u[t,1],2)<o] = 0
        r = actor.update(state,contrast,c,p,day)
        perf[0] += r>0
        perf[1] += c==0
        perf[2] += np.abs(contrast)==.5
    return perf.reshape(3,2,N).mean(-1)


def tree(actor,state,assay):
    prob = np.ones((2*N,1))
    state = {k:v.copy() for k,v in state.items()}
    for depth,contrast in enumerate(assay):
        x = np.full(prob.size,contrast)
        p,o = actor.probabilities(state,x,STAGE+400+depth,200+depth)
        tern = np.column_stack(((1-o)*(1-p),o,(1-o)*p))
        branch_prob = tern.reshape(2*N,-1,3)
        prob = (prob[:,:,None]*branch_prob).reshape(2*N,-1)
        if depth<len(assay)-1:
            state = {k:np.repeat(v,3,axis=0) for k,v in state.items()}
            actor.update(state,np.repeat(x,3),np.tile(OUTCOMES,len(p)),np.repeat(p,3))
    check(np.max(np.abs(prob.sum(1)-1))<3e-14 and np.isfinite(prob).all(), 'Path mass')
    prob = prob.reshape(2,2,N//2,-1)
    return prob.mean(2)


def validate_tree():
    from itertools import product
    c = [[np.zeros(len(x)) for x in ((range(9)),range(6))],
         [np.zeros(14),np.zeros(11)],[np.zeros(34),np.zeros(28)]]
    b = (np.array([.2,1.2,1.2,0,0,0]),np.array([-4.,0,0,0]))
    a = Actor(None,'drift',b,c,0,False)
    state = dict(trace=np.zeros((2*N,3,5)),choice_shift=np.zeros(2*N),omit_shift=np.zeros(2*N))
    p = tree(a,state,ASSAYS[0])[0,0]
    manual = []
    for stim in ASSAYS[0]:
        z = np.tanh(stim*5.)/np.tanh(5.)
        right = expit(.2+1.2*z)
        o = expit(-4.)
        manual.append(((1-o)*(1-right),o,(1-o)*right))
    q = np.array([np.prod([manual[t][k] for t,k in enumerate(ix)]) for ix in product(range(3),repeat=6)])
    error = float(np.max(np.abs(p-q)))
    check(error<1e-14,'Frozen-state product oracle')
    return error


def main():
    started = time.monotonic()
    cal = get(HERE/'CALIBRATION.json')
    tr = get(HERE/'TRACK_CALIBRATION.json')
    src = get(HERE/'SOURCE_MANIFEST.json')
    ids,labs = src['subjects'],src['labs']
    check(cal['selected_medium']==.5,'Frozen sequence support')
    p = HERE.parent/'acquisition-probe-design-2026-11-04/pilot.py'
    blob(p,'febcc48d80ee5163ce58d1735e470a597382f4931e627e4664feb5cb32e94c02')
    spec = importlib.util.spec_from_file_location('archive',p)
    pilot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pilot)
    models = pilot.model_load()
    reference_error = validate_tree()
    joint = np.zeros((len(ids),len(STRESSES),len(ACTORS),len(ASSAYS),2,2,3**6))
    perf = np.zeros((len(ids),len(STRESSES),len(ACTORS),3,2))
    for i,(s,lab) in enumerate(zip(ids,labs)):
        seed = pilot.seed(s)
        rng = np.random.default_rng(seed+3947921)
        x = random_schedule(rng)
        u = rng.random((400,2,N))
        coeff = [[np.asarray(v) for v in z] for z in cal['weights'][lab]]
        for j,_ in enumerate(STRESSES):
            for a,name in enumerate(ACTORS):
                state = initial(name,cal['start'][s],tr['start'][s],np.random.default_rng(seed+33288),j)
                actor = Actor(models.get(name),name,[np.asarray(v) for v in cal['start'][s]['base']],
                              coeff,tr['fit'][lab]['eta'],j)
                perf[i,j,a] = train(actor,state,x,u)
                for k,seq in enumerate(ASSAYS):
                    joint[i,j,a,k] = tree(actor,state,seq)
        if (i+1)%8==0:
            print('Generated curriculum and joint assay',i+1,'/',len(ids),'elapsed',round(time.monotonic()-started,2),flush=True)
    first = joint.reshape(joint.shape[:-1]+(3,-1)).sum(-1)
    first_diff = float(np.max(np.abs(first-first[:,:,:,0:1])))
    check(first_diff<3e-14,'First response changes with later stimuli')
    np.savez_compressed(HERE/'SEQUENCE_MASSES.npz',joint=joint,training=perf,subjects=ids,labs=labs,
                        assays=ASSAYS,assay_names=ORDER,actors=ACTORS,stresses=STRESSES)
    save('SEQUENCE_EXECUTION.json',dict(utc=utc(),seconds=time.monotonic()-started,particle_count=N,
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,io=dict(BYTES),model_io=dict(pilot.D),
            frozen_state_product_max_error=reference_error,first_response_invariance_max_error=first_diff))
    print('Saved',utc(),flush=True)


if __name__=='__main__':
    main()
