"""Static scientific summary from saved results; no new scoring or fitting."""
import datetime,json,pathlib,resource,os
os.environ.setdefault('MPLCONFIGDIR',str(pathlib.Path(__file__).resolve().parent/'.mplcache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent
def main():
    mainp=ROOT/'MAIN_SUMMARY.json';revp=ROOT/'REVISION_SUMMARY.json'
    a=json.loads(mainp.read_text());b=json.loads(revp.read_text())
    fig,axes=plt.subplots(1,2,figsize=(11.2,4.5),gridspec_kw={'width_ratios':[1.6,1]})
    names=['prototype','nearest','covariance','free_tempo']
    values=[]
    for m in names:
        v=a['methods'][m];row=[v['natural_acceptance']]
        for loc in ['global','duration_b','gap_ab','duration_c']:
            row.append(min(x['rejection'] for x in v['challenges'] if x['location']==loc and x['factor'] in [.8,1.2]))
        values.append(row)
    z=100*np.array(values);axes[0].imshow(z,vmin=0,vmax=100,cmap='Blues',aspect='auto')
    axes[0].set_xticks(range(5),['Natural\naccepted','Global','Duration b','Gap a–b','Duration c'],fontsize=9)
    axes[0].set_yticks(range(4),['Mean template','Nearest example','Covariance','Free tempo'])
    axes[0].set_title('Main: 51 phrases / 10 later recordings',loc='left',fontsize=11,pad=15)
    for i in range(4):
        for j in range(5):
            axes[0].text(j,i,f'{z[i,j]:.0f}%',ha='center',va='center',color='white' if z[i,j]>60 else '#152235',fontsize=10)
    axes[0].tick_params(length=0)
    x=np.arange(3);width=.34
    for shift,m,color,label in [(-width/2,'free_tempo','#9aa9b8','Free tempo'),(width/2,'bounded_tempo','#246d97','Bounded tempo')]:
        v=b['methods'][m]
        vs=[v['natural_acceptance']]+[min(q['rejection'] for q in v['challenges'] if q['location']==loc and q['factor'] in [.8,1.2]) for loc in ['global','duration_b']]
        bars=axes[1].bar(x+shift,100*np.array(vs),width,label=label,color=color)
        axes[1].bar_label(bars,fmt='%.0f%%',padding=3,fontsize=9)
    axes[1].set_ylim(0,112);axes[1].set_xticks(x,['Natural\naccepted','Global\nrejected','Duration b\nrejected'],fontsize=9)
    axes[1].set_yticks([0,50,100],['0%','50%','100%']);axes[1].legend(frameon=False,fontsize=9,loc='upper center',bbox_to_anchor=(.5,-.19),ncol=2)
    axes[1].set_title('Revision: 52 phrases / final 10 recordings',loc='left',fontsize=11,pad=15)
    axes[1].spines[['top','right']].set_visible(False)
    fig.suptitle('Natural timing tolerance is component-specific',x=.06,ha='left',fontsize=15,y=.99)
    fig.text(.06,.02,'One Bengalese finch/day; human-labelled intervals. Rejection = weaker direction of ±20% designed edits.\nEqual weight per recording. Edited features are assay inputs, not recorded biological mistakes.',fontsize=9,color='#444444')
    fig.subplots_adjust(left=.15,right=.98,top=.82,bottom=.28,wspace=.35)
    fig.savefig(ROOT/'RESULT.png',dpi=170,facecolor='white');plt.close(fig)
    ledger=json.loads((ROOT/'ACQUISITION.json').read_text());charge=mainp.stat().st_size+revp.stat().st_size
    ledger['scientific_read_decoded_hash_bytes']+=charge
    ledger['scientific_byte_passes'].append({'operation':'plot saved results','kind':'summary JSON read','bytes':charge})
    ledger['peak_rss_bytes_measured_max']=max(ledger['peak_rss_bytes_measured_max'],resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (ROOT/'ACQUISITION.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print(json.dumps({'output':'RESULT.png','timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'summary_bytes_read':charge}))
if __name__=='__main__':main()
