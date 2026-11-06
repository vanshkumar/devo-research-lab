from data import ROOT, load_people, wrap
from model import assemble, block_features, grid_filter, approximate, choose_fit, circular_loss, person_means, predict, design
import datetime, hashlib, json, resource
import numpy as np

people,audits,charged=load_people('development')
d=assemble(people)
out=dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),split='development',people=len(np.unique(d['keys'][:,0])),rows=len(d['y']),features_B=d['B'].shape[1],extra_H=d['extra'].shape[1],models={})
np.savez(ROOT/'development_features.npz',**{k:v for k,v in d.items() if k!='filterchecks'})
for which in ['B','H']:
    m,cv,cvhat=choose_fit(d,which)
    np.savez(ROOT/('fitted_'+which+'.npz'),**m)
    out['models'][which]=dict(ridge=m['lam'],cv=cv,chosen_oof_loss=float(person_means(circular_loss(d['y'],cvhat),d['keys'][:,0]).mean()))
out['reference']={name:float(person_means(circular_loss(d['y'],hat),d['keys'][:,0]).mean()) for name,hat in [('persistence',np.zeros(len(d['y']))),('source_approximate',d['diagnostics'][:,3])]}

# Known qualitative context effect, development only. No error-normalized LRs.
out['descriptive_context_effect']=[]
for sid in np.unique(d['keys'][:,0]):
    for c in [0,1]:
        sel=(d['keys'][:,0]==sid)&(d['keys'][:,1]==c)
        e=d['diagnostics'][:,0]
        for name,mask in [('small',abs(e)<np.pi/6),('large',abs(e)>np.pi/3)]:
            g=sel&mask
            out['descriptive_context_effect'].append(dict(id=int(sid),context=c,error_bin=name,n=int(g.sum()),pe_update_slope=float(np.sum(e[g]*d['y'][g])/np.sum(e[g]**2))))

# Future suffix changes cannot alter features at or before the cutoff.
focal=people[0]; original=block_features(focal);cut=30
changed={**focal,'pred':focal['pred'].copy(),'outcome':focal['outcome'].copy()}
changed['pred'][cut+1:]=wrap(changed['pred'][cut+1:]+1.234)
changed['outcome'][cut+1:]=wrap(changed['outcome'][cut+1:]-2.345)
other=block_features(changed)
past=original[3][:,3]<=cut+1
future_error=max(float(np.max(abs(original[k][past]-other[k][past]))) for k in [0,1])
assert future_error<1e-12

# Latent variables cannot affect the feature maps.
latent={**focal,'raw':{k:v.copy() for k,v in focal['raw'].items()}}
for key in ['cp','oddBall','TAC','distMean','age']:
    latent['raw'][key]=np.full_like(latent['raw'][key],123)
alter=block_features(latent)
latent_error=max(float(np.max(abs(original[k]-alter[k]))) for k in [0,1])
assert latent_error==0

# Numerical grid refinement, source settings fixed, same development person.
coarse=grid_filter(focal['outcome'],focal['context'],focal['block'],360)
fine=grid_filter(focal['outcome'],focal['context'],focal['block'],720)
gridcheck=dict(max_mean_angle_diff_rad=float(np.max(abs(wrap(coarse[0]-fine[0])))),max_resultant_diff=float(np.max(abs(coarse[1]-fine[1]))),max_event_prob_diff=float(np.max(abs(coarse[2]-fine[2]))))
assert gridcheck['max_mean_angle_diff_rad']<.005

# Rotation check of source-independent descriptive history states and reference.
rot={**focal,'pred':wrap(focal['pred']+.7),'outcome':wrap(focal['outcome']+.7)}
rotated=block_features(rot)
history_rotation=float(np.max(abs(original[1]-rotated[1])))
assert history_rotation<1e-11
a=approximate(wrap(focal['outcome']-focal['pred']),focal['context'],focal['block'])
b=approximate(wrap(rot['outcome']-rot['pred']),focal['context'],focal['block'])
approx_rotation=max(float(np.max(abs(x-y))) for x,y in zip(a,b))
assert approx_rotation<1e-11

# Direct scalar initial cases from the source formula, independent arithmetic.
pe=np.array([0.,0.,1.]);block=np.ones(3)
for c in [0,1]:
    rr,qq,uu=approximate(pe,c,block)
    h=1/7;nv=.1;expectedq=(h/(2*np.pi))/((1-h)/np.sqrt(2*np.pi*10)+h/(2*np.pi))
    assert abs(qq[0]-expectedq)<1e-14
    expectedup=(.99+expectedq-.99*expectedq) if c else .99*(1-expectedq)
    assert abs(uu[0])<1e-14 and 0<expectedup<1
    assert np.all((rr>0)&(rr<1)) and np.all((qq>0)&(qq<1))

out['checks']=dict(future_suffix_max_feature_change=future_error,latent_mutation_max_feature_change=latent_error,grid_refinement=gridcheck,history_rotation_error=history_rotation,approximate_rotation_error=approx_rotation,filterchecks=d['filterchecks'])
out['source_audits']=audits
out['resources']=dict(source_compressed_plus_decode_bytes=charged,feature_array_bytes=sum(v.nbytes for k,v in d.items() if isinstance(v,np.ndarray)),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(ROOT/'DEVELOPMENT.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k not in ['source_audits','descriptive_context_effect','checks']},indent=2))
print('CHECKS',json.dumps({k:v for k,v in out['checks'].items() if k!='filterchecks'}))
