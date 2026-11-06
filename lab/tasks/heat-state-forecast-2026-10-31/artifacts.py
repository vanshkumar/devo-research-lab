"""Create the standalone scientific figure and compact source/environment manifests."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
os.environ['MPLCONFIGDIR']=str(__import__('pathlib').Path(__file__).resolve().parent/'mpl-cache')
import json,sys,platform,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import forecast as f
def main():
    r=json.loads((f.TASK/'EVALUATION_RESULT.json').read_text())
    fig,axes=plt.subplots(1,3,figsize=(12,3.9),gridspec_kw={'width_ratios':[1,1,1.1]})
    for ax,mode,title in zip(axes[:2],['neural','behavior'],['Identified-neuron response','Behavioral response']):
        m=r['modalities'][mode];a=np.asarray(m['per_worm_losses']['simple']);b=np.asarray(m['per_worm_losses']['state'])
        mx=max(a.max(),b.max())*1.1
        ax.plot([0,mx],[0,mx],color='#c8ced5',lw=1,zorder=0)
        ax.scatter(a,b,s=48,c=np.where(b<a,'#187c88','#b1533e'),edgecolor='white',linewidth=.6)
        ax.set(xlim=(0,mx),ylim=(0,mx),xlabel='Strong simple forecast MSE',ylabel='Compact state forecast MSE',title=title)
        ax.text(.04,.96,f"7 held animals\nState gain: {100*m['state_fraction_gain']:+.1f}%",transform=ax.transAxes,va='top',fontsize=9)
        ax.set_aspect('equal',adjustable='box')
        for i,(x,y) in enumerate(zip(a,b)):ax.annotate(str(i+1),(x,y),xytext=(4,2),textcoords='offset points',fontsize=8,color='#49525c')
    ax=axes[2];labels=['Neural: prefix SD','Behavior: joint','Neural: fractional']
    ms=[r['modalities']['neural'],r['modalities']['behavior'],r['fractional_fluorescence']]
    for i,m in enumerate(ms):
        mu=100*m['state_fraction_gain'];lo,hi=np.array(m['fraction_gain_bootstrap95'])*100
        ax.errorbar(mu,2-i,xerr=[[mu-lo],[hi-mu]],fmt='o',color='#187c88' if mu>0 else '#b1533e',capsize=3,ms=6)
    ax.axvline(0,color='#c8ced5',lw=1);ax.axvline(10,color='#adb7c0',lw=1,ls=':')
    ax.set(yticks=[2,1,0],yticklabels=labels,xlabel='State MSE reduction (%)',title='Animal bootstrap 95% intervals',ylim=(-.6,2.6))
    for a in axes:
        a.spines[['top','right']].set_visible(False);a.tick_params(labelsize=8);a.title.set_fontsize(10)
    fig.suptitle('Pre-heat state does not earn joint neural and behavioral forecast gain',fontsize=13,y=1.02)
    fig.text(.01,-.015,'Frozen 12-development / 7-evaluation comparison; 30–450s after heat. Points below identity favor state.\nFluorescence is processed upstream; small animal count and scaling sensitivity limit interpretation.',fontsize=8,color='#4f5963')
    fig.tight_layout();fig.savefig(f.TASK/'HEAT_FORECAST_RESULT.png',dpi=190,bbox_inches='tight');plt.close(fig)
    split=json.loads((f.TASK/'SPLIT.json').read_text());dev=json.loads((f.TASK/'DEVELOPMENT_DATA.json').read_text());ev=json.loads((f.TASK/'EVALUATION_PREFIX_ACCESS.json').read_text())
    known={x['uid']:x for x in dev+ev};items=[]
    for x in split['items']:
        items.append(dict(uid=x['uid'],part=x['part'],path=x['path'],bytes=x['size'],git_blob=x['sha'],sha256=known[x['uid']]['sha256'],url=f"https://raw.githubusercontent.com/{split['repo']}/{split['commit']}/{x['path']}",final_exposure='consumed development' if x['part']=='development' else 'consumed once-only numeric evaluation after forecast saving'))
    manifest=dict(at_utc=f.now(),repo=split['repo'],commit=split['commit'],all_heat_payloads_bytes=sum(x['bytes'] for x in items),items=items,source_documentation='sources/looper_repo/atanas-data/DATASET.md; blob38353b53afffeac6c41c8fea6a7ec9bd09269b69',primary_data_deposit='https://zenodo.org/records/8150515',data_availability='Atanas primary paper links WormWideWeb/Zenodo/GitHub; mirror files verified to exact git blobs, not separately matched against original deposit',license='Zenodo license not verified: web access returned an error. Pinned mirror has no top-level data license; nested LOOPER code license does not certify these heat payloads. Local research cache only; no publication/redistribution undertaken.',processing='activity/marker ratio, interpolation and whole-record exponential bleach correction upstream; prefix-only normalization here; neuron labels post-hoc',protected='no reserved baseline worms, Pan20, Flesch, HABITS or memory targets acquired/decoded')
    (f.SRC/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    f.save('ENVIRONMENT.json',dict(at_utc=f.now(),python=sys.version,executable=sys.executable,platform=platform.platform(),numpy=np.__version__,matplotlib=matplotlib.__version__,threads=dict(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),packages_required=['numpy','matplotlib'],network='public pinned raw.githubusercontent.com only for numerical data; connector for metadata/articles; platform escalation after sandbox DNS failure'))
    print('created HEAT_FORECAST_RESULT.png, SOURCE_MANIFEST.json, ENVIRONMENT.json')
if __name__=='__main__':main()
