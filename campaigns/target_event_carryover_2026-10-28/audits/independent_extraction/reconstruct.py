"""Independent original-byte carryover reconstruction, no imports from lead code.

Uses direct full-design SVD, rather than lead nuisance-QR residualization.
Development outcomes only unless validation release file exists and --part validation.
External files are never opened. Outcome fields are accessed only after ID selection.
"""
from pathlib import Path
import argparse,csv,hashlib,json
import numpy as np
from scipy import linalg,stats
from threadpoolctl import threadpool_limits
threadpool_limits(1)
HERE=Path(__file__).resolve().parent
CAMPAIGN=HERE.parents[1]
REPO=CAMPAIGN.parents[1]
SOURCES=REPO/'sources/learning_intervention_feasibility_2026-10-28'
FILES=('tsay_TE_SPE.csv','tsay_controljump.csv')

def product(a,b):
    if b.ndim==1: return np.einsum('ij,j->i',a,b,optimize=False)
    return np.einsum('ij,jk->ik',a,b,optimize=False)

def number(x):
    try: return float(x)
    except ValueError: return float('nan')

def read_people(filename,ids,endpoint):
    data={int(p):[] for p in ids}
    with (SOURCES/filename).open() as f:
        for row in csv.DictReader(f):
            sn=int(row['SN'])
            if sn not in data: continue
            data[sn].append((int(row['TN']),number(row['clamp_size']),number(row['tgt_jump_size']),-number(row[endpoint])))
    arrays=[]
    for sn in ids:
        rows=sorted(data[int(sn)])
        assert [r[0] for r in rows]==list(range(1,825))
        arrays.append(np.asarray(rows))
    return arrays

def design(arrays,horizon,level,stationary):
    cells=sorted({tuple(x[1:3]) for x in arrays[0][100:280]})
    assert len(cells)==9
    rank_features=[];zs=[];outcomes=[];owners=[];identities=[]
    for person,a in enumerate(arrays):
        label=np.array([cells.index(tuple(x[1:3])) if tuple(x[1:3]) in cells else 0 for x in a])
        for t in range(100,824):
            block,position=divmod(t-100,181)
            if position<20 or position>174 or a[t,1]!=0:continue
            if stationary and a[t+horizon,2]!=0:continue
            past=a[t-5:t,3]
            future=a[t+1:t+6,3]
            if not np.all(np.isfinite(np.r_[past,future])):continue
            if np.max(np.abs(np.r_[past,future]))>90:continue
            event=float(a[t,2]!=0)-2/3
            sign=np.sign(a[t,2])
            row=[]
            for k in range(1,6):
                row.extend([int(label[t-k]==q) for q in range(1,9)])
            for decay in (.8,.95):
                w=decay**np.arange(15);w=w/np.sum(w)
                for q in range(1,9):
                    row.append(float(np.sum(w*np.array([label[t-k]==q for k in range(6,21)]))))
            for k in range(1,horizon+1):
                row.extend([int(label[t+k]==q) for q in range(1,9)])
            row.append(sign)
            row.extend([sign*(label[t-1]==q) for q in range(1,9)])
            row.extend([event*a[t-k,1]/4 for k in range(2,6)])
            # An independent equivalent fixed-effect parameterization:
            # one intercept and time slope per person/block, no shared block columns.
            for pp in range(len(arrays)):
                for bb in range(4):
                    row.append(int(person==pp and block==bb))
                for bb in range(4):
                    row.append(int(person==pp and block==bb)*(position-97)/77)
            z=np.array([event*(label[t-1]==q) for q in range(9)])
            rank_features.append(row);zs.append(z)
            outcomes.append(a[t+horizon,3] if level else a[t+horizon,3]-sum(past)/5)
            owners.append(person);identities.append([person,int(a[t,0])])
    X=np.column_stack((np.asarray(rank_features),np.asarray(zs)))
    contrast=np.zeros(X.shape[1]);contrast[-9+cells.index((4.,0.))]=.5;contrast[-9+cells.index((-4.,0.))]=-.5
    return X,np.asarray(outcomes),np.asarray(owners),contrast,identities,cells

def estimate(X,y,g,contrast,ngroups):
    u,s,vt=linalg.svd(X,full_matrices=False,check_finite=True)
    rank=int(np.sum(s>s[0]*1e-10))
    inverse=product((vt[:rank].T/s[:rank]),u[:,:rank].T)
    beta=product(inverse,y)
    residual=y-product(X,beta)
    influence=product(contrast[None,:],inverse)[0]
    scores=np.array([sum(influence[g==i]*residual[g==i]) for i in range(ngroups)])
    correction=ngroups/(ngroups-1)*(len(y)-1)/(len(y)-rank)
    scores*=np.sqrt(correction)
    e=float(sum(contrast*beta));se=float(np.sqrt(sum(scores**2)))
    return {'n':len(y),'rank':rank,'columns':X.shape[1],'condition_number':float(s[0]/s[rank-1]),'estimate':e,'se':se,'scores':scores.tolist(),'cell_event_coefficients':beta[-9:].tolist()}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--part',choices=['development','validation'],default='development')
    parser.add_argument('--endpoint',default='Hand_raw')
    parser.add_argument('--level',action='store_true')
    parser.add_argument('--stationary',action='store_true')
    args=parser.parse_args()
    if args.part=='validation':
        release_path=CAMPAIGN/'protocol/VALIDATION_RELEASE.json'
        assert release_path.exists(),'Validation release required'
        release=json.loads(release_path.read_text())
        freeze_path=CAMPAIGN/'protocol/FINAL_FREEZE.json'
        assert hashlib.sha256(freeze_path.read_bytes()).hexdigest()==release['freeze_sha256'],'Freeze record changed'
        for path,digest in json.loads(freeze_path.read_text())['files_sha256'].items():
            assert hashlib.sha256((CAMPAIGN/path).read_bytes()).hexdigest()==digest,'Frozen file changed: '+path
    split=json.loads((CAMPAIGN/'protocol/split.json').read_text())['split']
    result={'method':'Independent CSV original-byte read; explicit full-design SVD; per-person/block fixed effects; direct sandwich score; no lead code imported','part':args.part,'endpoint':args.endpoint,'level':args.level,'stationary':args.stationary,'files':{}}
    for name in FILES:
        ids=split[name][args.part]
        data=read_people(name,ids,args.endpoint)
        fits=[]
        for h in range(1,6):
            X,y,g,c,events,cells=design(data,h,args.level,args.stationary)
            fit=estimate(X,y,g,c,len(ids));fits.append(fit)
            print(name,h,fit['n'],fit['rank'],fit['estimate'],fit['se'],flush=True)
        curve=np.array([f['estimate'] for f in fits]);scores=np.array([f['scores'] for f in fits]).T
        covariance=product(scores.T,scores)
        theta=float(curve.mean());se=float(np.sqrt(covariance.mean()));crit=stats.t.ppf(.975,len(ids)-1)
        result['files'][name]={'sha256':hashlib.sha256((SOURCES/name).read_bytes()).hexdigest(),'ids':ids,'cells':cells,'lags':fits,'curve_covariance':covariance.tolist(),'theta':theta,'se':se,'low':theta-crit*se,'high':theta+crit*se}
    summaries=list(result['files'].values())
    theta=float(np.mean([s['theta'] for s in summaries]));se=float(np.sqrt(sum(s['se']**2 for s in summaries))/2)
    df=sum(len(s['ids']) for s in summaries)-2
    v=np.array([s['se']**2/4 for s in summaries]);welch_df=float(sum(v)**2/sum(v*v/np.array([len(s['ids'])-1 for s in summaries])))
    result['pooled']={'theta':theta,'se':se,'df_groups_minus_two':df,'df_welch':welch_df,'low_groups_minus_two':theta-stats.t.ppf(.975,df)*se,'high_groups_minus_two':theta+stats.t.ppf(.975,df)*se,'low_welch':theta-stats.t.ppf(.975,welch_df)*se,'high_welch':theta+stats.t.ppf(.975,welch_df)*se}
    stem=f'{args.part}_{args.endpoint}_{"level" if args.level else "change"}_{"stationary" if args.stationary else "all"}'
    lead_path=CAMPAIGN/'outputs'/f'{stem}.json'
    if lead_path.exists():
        lead=json.loads(lead_path.read_text())
        result['comparison']={'lead_result_sha256':hashlib.sha256(lead_path.read_bytes()).hexdigest(),'lead_code_sha256':hashlib.sha256((CAMPAIGN/'experiments/analysis.py').read_bytes()).hexdigest(),'pooled_estimate_absolute_difference':abs(theta-lead['pooled']['estimate']),'pooled_se_absolute_difference':abs(se-lead['pooled']['se'])}
        result['comparison']['maximum_lag_estimate_absolute_difference']=max(abs(f['estimate']-g['contrast']['estimate']) for name in FILES for f,g in zip(result['files'][name]['lags'],lead[name]['lags']))
        result['comparison']['maximum_cell_event_coefficient_absolute_difference']=max(abs(a-b) for name in FILES for f,g in zip(result['files'][name]['lags'],lead[name]['lags']) for a,b in zip(f['cell_event_coefficients'],g['beta']))
    (HERE/f'{stem}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'pooled':result['pooled'],'comparison':result.get('comparison')}),flush=True)

if __name__=='__main__':main()
