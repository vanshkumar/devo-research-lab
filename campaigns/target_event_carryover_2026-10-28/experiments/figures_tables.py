"""Scientific figures and plain numeric tables; no raw data access."""
from analysis import ROOT,FILES,stats
import json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=ROOT/'outputs';FIG=OUT/'figures';FIG.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})

def read(name):return json.loads((OUT/name).read_text())
def curve(a):
 ss=[a[f]['summary'] for f in FILES];est=np.mean([s['curve'] for s in ss],axis=0)
 vv=np.array([np.diag(s['cov']) for s in ss]);se=np.sqrt(vv.sum(axis=0))/2
 df=vv.sum(axis=0)**2/(vv**2/9).sum(axis=0);return est,se*stats.t.ppf(.975,df)

def save(fig,name):
 fig.savefig(FIG/(name+'.png'),bbox_inches='tight');fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight');plt.close(fig)

def main():
 scalar=[];lagrows=[]
 for part in ['development','validation']:
  for endpoint,typ,ro in [('Hand_raw','change','all'),('Hand_raw','level','all'),('Hand_raw','change','stationary'),('Hand','change','all'),('Hand_dt','change','all')]:
   name=f'{part}_{endpoint}_{typ}_{ro}.json'
   if not (OUT/name).exists():continue
   a=read(name)
   for label,s in [('pooled',a['pooled'])]+[(f,a[f]['summary']) for f in FILES]:
    scalar.append({'partition':part,'endpoint':endpoint,'outcome':typ,'readout':ro,'set':label,**{k:s[k] for k in ['estimate','se','low','high','people']}})
   if endpoint=='Hand_raw':
    est,ci=curve(a)
    for h in range(5):lagrows.append({'partition':part,'outcome':typ,'readout':ro,'horizon':h+1,'effect_deg':est[h],'low95':est[h]-ci[h],'high95':est[h]+ci[h]})
 for name,rows in [('scalar_estimates.csv',scalar),('lag_curves.csv',lagrows)]:
  with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 if not (OUT/'validation_Hand_raw_change_all.json').exists():return
 colors={'development':'#7a8593','validation':'#126d91'}
 fig,axes=plt.subplots(1,2,figsize=(11.2,4.3),gridspec_kw={'width_ratios':[1.3,1]})
 for part,offset in [('development',-.07),('validation',.07)]:
  a=read(f'{part}_Hand_raw_change_all.json');est,ci=curve(a)
  axes[0].errorbar(np.arange(1,6)+offset,est,yerr=ci,marker='o',capsize=3,color=colors[part],label=part.capitalize())
 axes[0].axhline(0,color='black',lw=.8);axes[0].set(xlabel='Reach after zero-clamp target event',ylabel='Change in earlier-clamp contribution (degrees)',xticks=range(1,6),title='A. Signed response curve (pointwise 95% CI)');axes[0].legend(frameon=False)
 labels=[]
 for i,(part,ro) in enumerate([('development','all'),('validation','all'),('development','stationary'),('validation','stationary')]):
  s=read(f'{part}_Hand_raw_change_{ro}.json')['pooled'];axes[1].errorbar(s['estimate'],i,xerr=[[s['estimate']-s['low']],[s['high']-s['estimate']]],fmt='o',capsize=3,color=colors[part]);labels.append(part.capitalize()+'\n'+('all readouts' if ro=='all' else 'stationary readouts'))
 axes[1].axvspan(-.2,.2,color='#e4edf2',zorder=0,label='Fixed ±0.2° scalar margin');axes[1].axvline(0,color='black',lw=.8);axes[1].set(yticks=range(4),yticklabels=labels,xlabel='Mean effect over reaches 1–5 (degrees)',title='B. Prespecified scalar');axes[1].invert_yaxis();axes[1].legend(frameon=False,loc='lower left',fontsize=8)
 fig.suptitle('Target-event modulation of an earlier cursor-error response',fontsize=13);fig.tight_layout();save(fig,'primary_effect')
 fig,ax=plt.subplots(figsize=(6.7,4))
 for part,off in [('development',-.06),('validation',.06)]:
  a=read(f'{part}_ordinary_response.json');est,ci=curve(a);ax.errorbar(np.arange(1,6)+off,est,yerr=ci,marker='o',capsize=3,label=part.capitalize(),color=colors[part])
 ax.axhline(0,color='black',lw=.8);ax.set(xlabel='Reach after zero-clamp stationary-target index',ylabel='Earlier +4° clamp contribution (degrees)',xticks=range(1,6),title='Ordinary earlier-clamp response');ax.legend(frameon=False);fig.tight_layout();save(fig,'ordinary_response')
 if (OUT/'transfer_fig3.json').exists():
  t=read('transfer_fig3.json');fig,axes=plt.subplots(1,2,figsize=(10.5,4))
  for ax,ro in zip(axes,['all','stationary']):
   for key,col,off,label in [('prediction','#7a8593',-.06,'Frozen primary-A prediction'),('summary','#a54e33',.06,'Independent laboratory')]:
    s=t[ro][key];est=np.array(s['curve']);se=np.sqrt(np.diag(s['cov']));ci=se*stats.t.ppf(.975,s['people']-1)
    ax.errorbar(np.arange(1,6)+off,est,yerr=ci,marker='o',capsize=3,color=col,label=label)
   ax.axhline(0,color='black',lw=.8);ax.set(xticks=range(1,6),xlabel='Reach after index',ylabel='Earlier-clamp modulation (degrees)',title='All readouts' if ro=='all' else 'Stationary-target readouts')
  axes[0].legend(frameon=False,fontsize=8);fig.suptitle('Transfer changes the index to a nonzero ±4° clamp',fontsize=12);fig.tight_layout();save(fig,'external_transfer')
 # Combined estimate is descriptive because development informed method choices.
 sums=[read(f'{p}_Hand_raw_change_all.json')[f]['summary'] for p in ['development','validation'] for f in FILES]
 est=np.mean([s['estimate'] for s in sums]);v=np.array([s['se']**2 for s in sums]);se=np.sqrt(v.sum())/4;df=v.sum()**2/(v*v/9).sum();crit=stats.t.ppf(.975,df)
 combined={'estimate':est,'se':se,'low':est-crit*se,'high':est+crit*se,'df':df,'people':40,'interpretation':'Descriptive equal-stratum aggregate; development informed analysis and is not a second untouched test.'}
 (OUT/'combined_descriptive.json').write_text(json.dumps(combined,indent=2)+'\n')
 print('Figures/tables saved',FIG,combined)
if __name__=='__main__':main()
