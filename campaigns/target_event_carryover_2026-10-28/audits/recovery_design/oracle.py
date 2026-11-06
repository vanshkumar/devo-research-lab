"""Known-Gaussian-generator discrimination on reserved INPUT schedules only."""
from pathlib import Path
import sys,json,csv,hashlib
import numpy as np
from scipy import linalg,stats
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'experiments'))
from analysis import load,mm
from generators import generate


def nuisance(p):
    c,j=p['c'],p['j'];n=len(c);cells=sorted(set(zip(c[100:280],j[100:280])))
    # Same fixed time constants; completely free learning gain per input cell
    # and per timescale, free direct endpoint cells, per-block intercept/drift.
    cols=[]
    for a in (.65,.97):
        for cell in cells:
            u=((c==cell[0])&(j==cell[1])).astype(float);x=np.zeros(n)
            for r in range(1,n):x[r]=a*x[r-1]+u[r-1]
            cols.append(x)
    for cc,jj in cells[1:]:cols.append(((c==cc)&(j==jj)).astype(float))
    for b in range(4):
        lo=100+181*b;ix=(np.arange(n)>=lo)&(np.arange(n)<lo+181)
        cols.extend([ix.astype(float),ix*(np.arange(n)-lo-90)/90])
    return np.column_stack(cols)


def run():
    people=load('validation',inputs_only=True)
    kinds=[('two_timescale',0.),('retention',-.2),('retention',.2),
           ('expression_next',-.2),('expression_next',.2),('rebound',.2),('perceived_error',.2)]
    rec=json.loads((R/'outputs/recovery/summary.json').read_text())['scenarios']
    en=rec['actual_margin_negative']['isolated_reference_effect'];ep=rec['actual_margin_positive']['isolated_reference_effect']
    kinds += [('two_timescale',0.),('retention',en),('retention',ep)]
    pairs=[(0,1,'fixed_vs_negative'),(0,2,'fixed_vs_positive'),
           (1,3,'negative_retention_vs_transient'),(2,4,'positive_retention_vs_transient'),
           (2,5,'positive_retention_vs_rebound'),(2,6,'retention_vs_perceived_error'),
           (7,8,'fixed_vs_actual_minus02'),(7,9,'fixed_vs_actual_plus02')]
    rng=np.random.default_rng(194192);rows=[]
    for p in people:
        mask=rng.uniform(size=824)>=.03
        # Use available main-trial endpoints; baseline never contributes means.
        keep=np.flatnonzero(mask&(np.arange(824)>=100))
        lag=np.abs(keep[:,None]-keep[None,:])
        cov=9*(.35*.70**lag+.65*.25**lag)
        L=linalg.cholesky(cov,lower=True,check_finite=False)
        means=[]
        for ik,(kind,effect) in enumerate(kinds):
            g=generate(p['c'],p['j'],kind=kind,effect=effect,gains=(.9,.2) if ik>=7 else (.65,.2),noise_sd=0,
                       drift_scale=0,process_sd=0)
            means.append(g['clean'][keep])
        N=nuisance(p)[keep];WN=linalg.solve_triangular(L,N,lower=True,check_finite=False)
        Q,RR,piv=linalg.qr(WN,mode='economic',pivoting=True,check_finite=False)
        rank=int(np.sum(np.abs(np.diag(RR))>abs(RR[0,0])*1e-10));Q=Q[:,:rank]
        for a,b,name in pairs:
            delta=means[a]-means[b]
            z=linalg.solve_triangular(L,delta,lower=True,check_finite=False)
            zr=z-mm(Q,mm(Q.T,z));d2=float(mm(z,z));d2profile=float(mm(zr,zr))
            rows.append(dict(person=p['key'],pair=name,readouts=len(keep),
                             max_mean_difference=float(np.max(np.abs(delta))),
                             oracle_D2=d2,nuisance_projected_D2=d2profile,nuisance_rank=rank))
    summaries={}
    for _,_,name in pairs:
        ss=[r for r in rows if r['pair']==name]
        d2=sum(r['oracle_D2'] for r in ss);dp=sum(r['nuisance_projected_D2'] for r in ss)
        # LLR under modelA is N(D²/2,D²); equal-prior optimal accuracy Φ(D/2).
        mc_rng=np.random.default_rng(74813)
        mc=float(np.mean(mc_rng.normal(d2/2,np.sqrt(d2),100000)>0)) if d2>1e-20 else .5
        summaries[name]=dict(people=len(ss),oracle_D2=d2,
          oracle_accuracy=float(stats.norm.cdf(np.sqrt(d2)/2)),oracle_monte_carlo_accuracy=mc,
          nuisance_projected_D2=dp,nuisance_projected_accuracy=float(stats.norm.cdf(np.sqrt(dp)/2)),
          note='Projection allows free current-cell learning gains at both fixed timescales, current endpoint cells and participant/block drift; fixed covariance and time constants remain known.')
    out=dict(scope='Reserved input sequences only. Known parameters and Gaussian covariance; no empirical outcome access.',
       noise_sd=3.,motor_phi=.70,observation_phi=.25,process_noise=0.,
       drift='Known absent for oracle; projected block drift nuisance in secondary calculation.',
       meaning='An upper-bound information check for stipulated model pairs, not power of the fitted empirical analysis. High discrimination rejects universal information impossibility; it does not validate a correct mechanistic model.',
       scenarios=summaries,people=rows)
    (R/'outputs/recovery/oracle.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(summaries,indent=2))
    return out
if __name__=='__main__':run()
