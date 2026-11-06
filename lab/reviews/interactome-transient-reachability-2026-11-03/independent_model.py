"""Reviewer implementation, from pinned initialize.py; no author helpers."""
import os
for _key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS',
             'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'
import ast
import hashlib
import json
from pathlib import Path
import warnings
import numpy as np
from scipy import linalg, sparse
from scipy.special import expit
from scipy.integrate import solve_ivp, ode

ROOT = Path(__file__).resolve().parents[3]
AUTHOR = ROOT/'lab/tasks/interactome-transient-reachability-2026-11-03'
ORIGINAL = ROOT/'lab/tasks/connectome-persistence-contrast-2026-11-03/sources'
OUT = Path(__file__).resolve().parent
N=279
GC=.1
CAP=.015
EC=-35.
RISE=1./1.5
DECAY=5./1.5
BETA=.125
CURRENT=100000.
SEQ=round(RISE/(RISE+2*DECAY),4)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, value):
    (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

class Model:
    def __init__(self):
        self.pins={}
        self.original_source=(ORIGINAL/'interactome-initialize.py').read_text()
        for f, blob in [('Gg.npy','07b8ab0aa4471aa19cfae5e662d291493f09819b'),
                        ('Gs.npy','0a6e1cc361d9fe377f48cbf48e0557fec65debe8'),
                        ('emask.npy','ae289f5055e5661739b977cee62935d2f3b0be06')]:
            p=AUTHOR/'sources'/f
            data=p.read_bytes()
            observed=hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest()
            assert observed==blob,(f,observed)
            self.pins[f]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'git_blob':observed}
        self.gg=np.load(AUTHOR/'sources/Gg.npy',allow_pickle=False)
        self.gs=np.load(AUTHOR/'sources/Gs.npy',allow_pickle=False)
        self.e=-48.*np.load(AUTHOR/'sources/emask.npy',allow_pickle=False).reshape(-1)
        assert self.gg.shape==self.gs.shape==(N,N) and self.e.shape==(N,)
        response=json.loads((AUTHOR/'sources/names-response.json').read_text())
        names_text=response['result']['structuredContent']['content']
        self.names=ast.literal_eval(names_text)
        assert len(set(self.names))==N
        self.motor=np.array([i for i,n in enumerate(self.names) if n.startswith(('DB','VB','DD','VD'))])
        assert len(self.motor)==37
        self.zero=np.zeros(N)
        self.presets={}
        for f,blob in [('FWD','0840d0d732a38e1b76de384310e113ecda8e1405'),
                       ('PLM','87d8afda2195a3fb5a8dec2bd05a1a14ca5104f2')]:
            p=AUTHOR/'sources'/(f+'.json')
            data=p.read_bytes()
            canonical=data[:-1] if data.endswith(b'\n') else data
            observed=hashlib.sha1(('blob '+str(len(canonical))+'\0').encode()+canonical).hexdigest()
            assert observed==blob
            preset=json.loads(data)
            assert all(v['activated'] for v in preset.values())
            self.presets[f]=np.array([preset[n]['inputCurrent'] for n in self.names],float)
            self.pins[f+'.json']={'sha256':hashlib.sha256(data).hexdigest(),'git_blob_canonical':observed,'local_added_newline':data!=canonical}
        source_blob=hashlib.sha1(('blob '+str(len(self.original_source.encode()))+'\0').encode()+self.original_source.encode()).hexdigest()
        assert source_blob=='27bc70d6986e17d00fedf85ffbcaf8cb6b1b7d47'
        self.pins['initialize.py']={'sha256':hashlib.sha256(self.original_source.encode()).hexdigest(),'git_blob':source_blob}
        self.gap=sparse.csr_matrix(self.gg)
        self.syn=sparse.csr_matrix(self.gs)
        self.gsum=self.gg.sum(1)
        offg=self.gg-np.diag(np.diag(self.gg))
        offs=self.gs-np.diag(np.diag(self.gs))
        # Positive steady-balance matrix, separately assembled from physical balance.
        self.a=np.diag(GC+offg.sum(1)+SEQ*offs.sum(1))-offg
        self.base=GC*EC*np.ones(N)+SEQ*np.einsum('ij,j->i',self.gs,self.e,optimize=False)
        self.lu=linalg.lu_factor(self.a)
        self.vzero=linalg.lu_solve(self.lu,self.base)
        self.vstim={k:linalg.lu_solve(self.lu,CURRENT*v) for k,v in self.presets.items()}
        # Exact original functions are ONLY a reference, never our expression.
        allowed={'EffVth','EffVth_rhs','update_Mask','voltage_filter','membrane_voltageRHS','compute_jacobian'}
        tree=ast.parse(self.original_source)
        subset=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in allowed],type_ignores=[])
        self.source={'np':np,'sparse':sparse,'linalg':linalg,'N':N,'Gc':GC,'C':CAP,'Ec':EC,
                     'ggap':1.,'gsyn':1.,'E':self.e.reshape(N,1),'EMat':np.tile(self.e,(N,1)),
                     'ar':RISE,'ad':DECAY,'B':BETA,'Iext':CURRENT,'rate':.025,'offset':.15,
                     'Gg_Dynamic':self.gg,'Gs_Dynamic':self.gs}
        exec(compile(subset,'pinned-original-functions','exec'),self.source)
        self.source['EffVth'](self.gg,self.gs)

    def threshold(self, mask):
        return linalg.lu_solve(self.lu,self.base+CURRENT*mask)

    def input(self,t,old,new,switch=None,side=None):
        if switch is None:
            return new
        if side=='transition' or (switch<=t<=switch+.3):
            w=.5+.5*np.tanh((t-switch-.15)/.025)
            return old*(1-w)+new*w
        return new

    def rhs(self,t,y,mask):
        v,s=y[:N],y[N:]
        # Independent sparse contractions: no tile/pairwise source expression.
        gs=self.syn.dot(s)
        gse=self.syn.dot(s*self.e)
        dv=(-GC*(v-EC)-self.gsum*v+self.gap.dot(v)-gs*v+gse+CURRENT*mask)/CAP
        q=expit(BETA*(v-self.threshold(mask)))
        ds=RISE*(1-s)*q-DECAY*s
        return np.r_[dv,ds]

    def jac(self,t,y,mask):
        v,s=y[:N],y[N:]
        q=expit(BETA*(v-self.threshold(mask)))
        a=(self.gg-np.diag(GC+self.gsum+self.syn.dot(s)))/CAP
        b=self.gs*(self.e[None,:]-v[:,None])/CAP
        c=np.diag(RISE*(1-s)*BETA*q*(1-q))
        d=np.diag(-RISE*q-DECAY)
        return np.block([[a,b],[c,d]])

    def source_setup(self,old,new,switch=0.):
        self.source.update(oldMask=old,newMask=new,t_Switch=switch,transit_End=switch+.3,
                           Vth_Static=self.source['EffVth_rhs'](CURRENT,new))

    def segment(self,y,start,end,old,new,switch=None,rtol=2e-10,atol=2e-11,method='Radau',dt=.01):
        # Each transition is a separate one-sided interval; its clipped endpoint
        # belongs to the adjacent constant interval on the next solver call.
        transition=(switch is not None)
        times=np.linspace(start,end,round((end-start)/dt)+1)
        def mask(t): return self.input(t,old,new,switch,'transition' if transition else None)
        sol=solve_ivp(lambda t,z:self.rhs(t,z,mask(t)),(start,end),y,
                      jac=lambda t,z:self.jac(t,z,mask(t)),method=method,
                      t_eval=times,rtol=rtol,atol=atol,max_step=.01 if transition else .05)
        assert sol.success,sol.message
        assert np.isfinite(sol.y).all()
        return sol.t,sol.y.T

    def schedule(self,y,start,end,initial,switches,rtol=2e-10,atol=2e-11,method='Radau'):
        tt=[np.array([start])]; yy=[np.array([y])]
        old=initial.copy(); now=start
        for when,new in switches:
            if when>now:
                t,z=self.segment(y,now,when,old,old,rtol=rtol,atol=atol,method=method)
                tt.append(t[1:]); yy.append(z[1:]); y=z[-1]
            t,z=self.segment(y,when,when+.3,old,new,when,rtol,atol,method)
            tt.append(t[1:]); yy.append(z[1:]); y=z[-1]; now=when+.3; old=new.copy()
        if end>now:
            t,z=self.segment(y,now,end,old,old,rtol=rtol,atol=atol,method=method)
            tt.append(t[1:]); yy.append(z[1:])
        return np.concatenate(tt),np.concatenate(yy)

    def literal_short(self,y0,new):
        self.source_setup(self.zero,new,0.)
        times=np.arange(55)*.01
        r=ode(self.source['membrane_voltageRHS'],self.source['compute_jacobian'])
        r.set_integrator('vode',method='bdf',rtol=2e-10,atol=2e-11,nsteps=20000,max_step=.01)
        r.set_initial_value(y0,0.)
        ys=[y0.copy()]
        for t in times[1:]:
            r.integrate(t)
            assert r.successful(),r.t
            ys.append(r.y.copy())
        return times,np.array(ys)

def rms(x): return float(np.sqrt(np.mean(np.square(x))))
