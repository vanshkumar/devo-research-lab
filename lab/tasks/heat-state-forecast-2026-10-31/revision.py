"""The one development revision: strengthen the simple behavior alternative."""
import json,numpy as np
import forecast as f
def main():
    res=json.loads((f.TASK/'DEVELOPMENT_RESULT.json').read_text())
    with np.load(f.TASK/'DEVELOPMENT_CV.npz') as z:
        y=z['behavior_truth'];chosen=[]
        for k,name in enumerate(['reverse_fraction','pumping']):
            cand=[]
            for key in ['persistence','recent','shared','relative','shared_constant','relax5','relax30','relax120']+['local_'+str(a) for a in f.ALPHAS]:
                p=z['behavior__'+key]
                ls=np.mean((p[:,k]-y[:,k])**2,axis=1)
                cand.append(dict(model=key.split('_')[0] if key.startswith('local_') else key,alpha=float(key[6:]) if key.startswith('local_') else None,key=key,mse=float(ls.mean()),per_worm=ls.tolist()))
            if name=='pumping':
                ls=np.mean(y[:,k]**2,axis=1)
                cand.append(dict(model='zero',alpha=None,key='zero',mse=float(ls.mean()),per_worm=ls.tolist()))
            best=min(cand,key=lambda x:x['mse']);chosen.append(dict(channel=name,best=best,choices=cand))
    out=dict(at_utc=f.now(),revision_used=1,reason='Shared pumping suppression and individualized reversal are different predictions; one aggregate penalty/family need not be the strongest simple baseline. Preserve original results; select a simple baseline per behavioral channel and include literal zero-pumping after heat. State family/alpha and neural comparison unchanged.',components=chosen)
    f.save('DEVELOPMENT_REVISION.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='components'}))
    for x in chosen:print(x['channel'],json.dumps(x['best']))
if __name__=='__main__':main()
