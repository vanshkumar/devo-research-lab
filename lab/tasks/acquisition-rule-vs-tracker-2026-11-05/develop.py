"""Source-fitted generative growth plus adaptive history/psychometric alternatives."""
import time
import resource
import numpy as np
from scipy.special import expit,logit
from pilot import (HERE,PREV,OLD,ROOT,REV,IO,PINS,read,get,save,arrays,seed,utc,cal,track,scan,stats,subject)
from baselines import fit_competence,subset
from numba import njit
from scipy.optimize import minimize

NAMES=('persistence','growth','history_track','growth_track','gru')
FIT_DIAGNOSTICS=[]

def fit_logit(X,y,offset,ridge=12.):
    # Coordinate scaling changes no model or ridge in original coefficients.
    scale=np.maximum(.05,np.sqrt(np.mean(X*X,axis=0)))
    Z=np.ascontiguousarray(X/scale);penalty=ridge/(scale*scale)
    def obj(w):
        v=Z@w+offset
        return float(np.sum(np.logaddexp(0,v)-y*v)+.5*np.sum(penalty*w*w)),Z.T@(expit(v)-y)+penalty*w
    opt=minimize(obj,np.zeros(Z.shape[1]),jac=True,method='L-BFGS-B',
                 options=dict(maxiter=1500,ftol=1e-11,gtol=1e-5))
    value,grad=obj(opt.x)
    FIT_DIAGNOSTICS.append(dict(n=len(y),p=Z.shape[1],success=bool(opt.success),
                         iterations=opt.nit,max_scaled_gradient=float(np.max(np.abs(grad))),objective=value))
    assert opt.success and np.isfinite(opt.x).all(),str(opt.message)
    return opt.x/scale

@njit(cache=True)
def omit_scan(c,day,base,eta):
    out=np.empty(len(c)); state=0.
    for i in range(len(c)):
        if day[i]:state*=.85
        q=1/(1+np.exp(-max(-40.,min(40.,base[i]+state))))
        out[i]=q;state=.996*state+eta*((c[i]==0)-q)
    return out,state

def bank_fit(raw,ids):
    rows=[]; keep=[]
    for s in ids:
        a=raw[s]
        if len(a)<1500:continue
        w,cov,o=fit_competence(subject(a[500:1000])); delta=[];valid=[]
        for t in range(1000,6000,500):
            yes=t+500<=len(a);valid.append(yes)
            v=fit_competence(subject(a[t:t+500]))[0] if yes else w
            delta.append(v-w)
        keep.append(s);rows.append((np.r_[w,logit(o)],delta,valid))
    return dict(ids=keep,prefix=np.array([r[0] for r in rows]),delta=np.array([r[1] for r in rows]),valid=np.array([r[2] for r in rows]))

def donor_growth(a,bank,exclude=None):
    w,cov,o=fit_competence(subject(a[500:1000]));cur=np.r_[w,logit(o)]
    dist=np.sum(((bank['prefix']-cur)/[1.5,1.5,1.5,2.])**2,axis=1)
    if exclude in bank['ids']:dist[bank['ids'].index(exclude)]=np.inf
    order=np.argsort(dist);order=order[np.isfinite(dist[order])]
    delta=[]; pools=[]
    for b in range(10):
        elig=order[bank['valid'][order,b]][:15]
        assert len(elig)
        pools.append(elig);delta.append(bank['delta'][elig,b].mean(0))
    return np.array(delta),pools

def growth_times(delta,t):
    ix=np.clip((np.asarray(t)-1000)//500,0,len(delta)-1).astype(int)
    return delta[ix]

def augmented(s,a,d,ds,bank):
    delta,pools=donor_growth(a,bank,s)
    growth=track.psych(d['x'])*growth_times(delta,np.arange(len(a)))
    growth=growth.sum(1);growth[:1000]=0
    return dict(delta=delta,pools=pools,growth=growth,
                bx=ds['offsets'][0],bq=ds['offsets'][1],
                X=ds['matrices'][2][0],Z=ds['matrices'][2][1])

def fit_pair(ids,d,features,growth):
    out=[]
    for j in (0,1):
        xx=[];yy=[];oo=[]
        for s in ids:
            c=d[s]['c'][1000:]; m=c!=0 if j==0 else np.ones(len(c),bool)
            f=features[s]
            xx.append(f['X' if j==0 else 'Z'][1000:][m]); yy.append((c[m]<0 if j==0 else c[m]==0).astype(float))
            offset=f['bx' if j==0 else 'bq'][1000:].copy()
            if j==0 and growth:offset+=f['growth'][1000:]
            oo.append(offset[m])
        out.append(fit_logit(np.concatenate(xx),np.concatenate(yy),np.concatenate(oo)))
    return out

def main():
    begin=time.monotonic();prep=get(HERE/'PREPARATION.json');fitprep=get(HERE/'PREPARATION6000.json')
    raw=arrays(HERE/'TRAIN6000_ROWS.npz'); ev=arrays(PREV/'CAPPED_ROWS.npz')
    split=get(OLD/'artifacts/models/DEVELOPMENT_MODEL_SPLIT.json'); tr=[s for s in split['train'] if len(raw[s])>1000]
    val=[s for s in split['validation'] if len(raw[s])>1000]
    allraw={**raw,**ev};ids=tr+val+list(ev)
    d={s:cal.prepare(allraw[s]) for s in ids};ds={s:cal.design(d[s]) for s in ids}
    bank=bank_fit(raw,split['train']);f={s:augmented(s,allraw[s],d[s],ds[s],bank) for s in ids}
    history=fit_pair(tr,d,f,False);hybrid=fit_pair(tr,d,f,True)
    grid=(0.,.04,.12,.24); omitgrid=(0.,.04,.12,.24,.48)
    select={}; params={}
    for name,beta in (('history_track',history),('growth_track',hybrid)):
        losses=[]; omissions=[]
        for s in val:
            x=track.psych(d[s]['x'][1000:]); c=d[s]['c'][1000:];day=d[s]['day'][1000:]
            z=f[s];base=z['bx'][1000:]+z['X'][1000:]@beta[0]
            if name=='growth_track':base+=z['growth'][1000:]
            p=np.array([scan(x,c,day,base,e)[0] for e in grid]);ok=c!=0
            losses.append(-np.log(np.clip(np.where(c[None,ok]<0,p[:,ok],1-p[:,ok]),1e-12,1)).mean(1))
            baseq=z['bq'][1000:]+z['Z'][1000:]@history[1]
            q=np.array([omit_scan(c,day,baseq,e)[0] for e in omitgrid])
            omissions.append(-np.log(np.clip(np.where(c[None,:]==0,q,1-q),1e-12,1)).mean(1))
        means=np.mean(losses,axis=0);om=np.mean(omissions,axis=0)
        select[name]=dict(eta=grid[int(np.argmin(means))],grid_loss=means.tolist())
        params[name]=beta
    etaomit=omitgrid[int(np.argmin(om))]
    np.savez_compressed(HERE/'GROWTH_BANK.npz',ids=bank['ids'],prefix=bank['prefix'],delta=bank['delta'],valid=bank['valid'])
    # Whole-animal source bootstrap is a sensitivity of simple shared parameters.
    # It is not a posterior over frozen neural fits.
    boots=[];rng=np.random.default_rng(202611051)
    for b in range(12):
        draws=list(rng.choice(tr,len(tr),replace=True))
        boots.append([fit_pair(draws,d,f,False),fit_pair(draws,d,f,True)])
    boot={key:np.array([[z[k][j] for z in boots] for j in (0,1)],dtype=object) for k,key in enumerate(('history_track','growth_track'))}
    np.savez_compressed(HERE/'SOURCE_BOOTSTRAP.npz',
        history_choice=np.array([b[0][0] for b in boots]),history_omit=np.array([b[0][1] for b in boots]),
        hybrid_choice=np.array([b[1][0] for b in boots]),hybrid_omit=np.array([b[1][1] for b in boots]))
    from rnn_learning import load_rnn
    read(OLD/'artifacts/rnn/rnnglm32_nested_best.npz','c7f675d18f4143891ed7d2c76d91f74be74da9565fbae5407952768e2c146940')
    model=load_rnn(OLD/'artifacts/rnn/rnnglm32_nested_best.npz')
    scores={};probs={};prefix={}
    for i,s in enumerate(ev):
        z=f[s]; row=d[s];a=ev[s];cr=get(REV/'artifacts/source_comparison'/s/'existing.json')['calibration']
        initial=dict(w=np.array(cr['endpoint']),h=np.array(cr['hidden_endpoint']))
        pgru=model.sequence(subject(a[1000:3000]),initial)[0]
        c=row['c'][1000:3000];day=row['day'][1000:3000];x=track.psych(row['x'][1000:3000])
        baseq=z['bq'][1000:3000]+z['Z'][1000:3000]@history[1]
        q,_=omit_scan(c,day,baseq,etaomit)
        p={'gru':pgru,'persistence':expit(z['bx'][1000:3000]),
           'growth':expit(z['bx'][1000:3000]+z['growth'][1000:3000])}
        for name,beta in params.items():
            base=z['bx'][1000:3000]+z['X'][1000:3000]@beta[0]
            if name=='growth_track':base+=z['growth'][1000:3000]
            p[name]=scan(x,c,day,base,select[name]['eta'])[0]
        truncated={k:v[:3000] for k,v in row.items()}
        scores[s]={name:stats(truncated,v,q) for name,v in p.items()}
        probs[s]=np.column_stack([q]+[p[n] for n in NAMES])
        # Prefix-only information used to initialize every autonomous actor.
        trc,pos,trace=cal.summarize_history(*(row[k][:1000] for k in ('x','c','r','day')))
        base=ds[s]['base'];cov=[]
        for j in (0,1):
            X=cal.signed_basis(row['x'][:1000]) if j==0 else cal.omission_basis(row['x'][:1000])
            mask=row['c'][:1000]!=0 if j==0 else np.ones(1000,bool)
            pr=expit(X@base[j]);precision=np.einsum('ni,n,nj->ij',X[mask],pr[mask]*(1-pr[mask]),X[mask])
            precision+=np.diag([.5,1,1,2,2,4] if j==0 else [2,4,4,4])
            cov.append(np.linalg.inv(precision).tolist())
        prefix[s]=dict(base=[v.tolist() for v in base],cov=cov,trace=trace.tolist(),
                       pos=int(pos[-1]+1),growth_delta=z['delta'].tolist(),
                       donor_pools=[v.tolist() for v in z['pools']],gru=cr)
    labs=dict(zip(prep['eval_source_manifest']['subjects'],prep['eval_source_manifest']['labs']))
    summary={}
    for name in NAMES:
        sites={l:float(np.mean([scores[s][name]['ternary_loss'] for s in ev if labs[s]==l])) for l in sorted(set(labs.values()))}
        blocks={}
        for size in ('6','50','200'):
            z=np.sum([scores[s][name]['blocks'][size] for s in ev],axis=0);blocks[size]=(z[:,0]/z[:,1]).tolist()
        summary[name]=dict(equal_site_ternary=float(np.mean(list(sites.values()))),site=sites,blocks=blocks)
    save('DEVELOPED_FIT.json',dict(utc=utc(),fitids=tr,selectionids=val,fit_window=[1000,6000],
          row_count=sum(max(0,len(raw[s])-1000) for s in tr),select=select,omission_eta=etaomit,
          omission_grid=omitgrid,omission_selection_loss=om.tolist(),prefix=prefix,
          history_coeff=[x.tolist() for x in history],hybrid_coeff=[x.tolist() for x in hybrid],
          donor_count=len(bank['ids']),bootstrap_replicates=12,pins=PINS,
          fit_diagnostics=FIT_DIAGNOSTICS,
          asymmetry='Same original optimizer/selection roster; short histories unavailable after 1000 exclude four optimizer and one selection animal. Frozen GRU used all first <=6000, while simple shared regression uses only post-prefix rows. No neural refit.'))
    save('DEVELOPED_CONDITIONAL.json',dict(utc=utc(),summary=summary,per_animal=scores,labs=labs,
          evaluation_interval=[1000,3000],seconds=time.monotonic()-begin,io=dict(IO),
          peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    np.savez_compressed(HERE/'DEVELOPED_PROBS.npz',**probs)
    print(dict(select=select,omission_eta=etaomit,summary=summary,seconds=time.monotonic()-begin),flush=True)

if __name__=='__main__': main()
