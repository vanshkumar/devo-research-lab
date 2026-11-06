"""Correct only auxiliary all-success target at zero contrast; preserve originals."""
import time
from pilot import HERE,PREV,IO,get,save,arrays,utc
from generate import crps,HORIZONS

def main():
    begin=time.monotonic();raw=arrays(PREV/'CAPPED_ROWS.npz');target={};zero={}
    for s,a in raw.items():
        target[s]={str(h):int((a[1000:1000+h,3]>0).sum()) for h in HORIZONS}
        zero[s]={str(h):int((((a[1000:1000+h,0]==0)|(a[1000:1000+h,1]==0))&(a[1000:1000+h,3]>0)).sum()) for h in HORIZONS}
    changes={}
    for basename,scorefile in (('GENERATED_COUNTS','GENERATED_SCORES'),('COMMON_GENERATED_COUNTS','COMMON_GENERATED_SCORES'),('RETAINED_GROWTH_COUNTS','RETAINED_GROWTH_SCORES')):
        z=arrays(HERE/(basename+'.npz'));scores=get(HERE/(scorefile+'.json'));ids=list(z['subjects']);names=list(z['names'])
        diff={}
        for i,s in enumerate(ids):
            for j,h in enumerate(HORIZONS):
                difference=target[s][str(h)]-int(z['observed'][i,j,6])
                if difference:diff.setdefault(s,{})[str(h)]=difference
                for k,n in enumerate(names):
                    scores['per_animal'][s][n][str(h)]['all_correct_crps']=crps(z['samples'][i,k,:,j,6]/h,target[s][str(h)]/h)
        scores['observation_target_correction']='All generated correct choices include zero-contrast feedback success; empirical auxiliary all-correct target must use feedbackType>0 as well. Exact100 K/N, omission/right counts and all other primary scores unchanged. Original scores/counts remain preserved.'
        save(scorefile+'_CORRECTED.json',scores);changes[basename]=diff
    save('OBSERVATION_TARGET_CORRECTION.json',dict(utc=utc(),all_feedback_success=target,zero_success=zero,changed_auxiliary_counts=changes,
        reason='Original empirical auxiliary all-correct code excluded zero while generation included it. Corrected auxiliary score only; exact100 primary targets unaffected.',
        seconds=time.monotonic()-begin,io=dict(IO)))
    print('Corrected auxiliary all-success counts; affected animals',sum(bool(x) for x in changes['RETAINED_GROWTH_COUNTS'].values()),flush=True)

if __name__=='__main__':main()
