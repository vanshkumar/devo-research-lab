import pathlib,json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
H=pathlib.Path(__file__).resolve().parent;s=json.loads((H/'followup_summary.json').read_text());r=list(csv.DictReader((H/'followup_paired_quality.csv').open()));d=np.array([float(x['difference_percentage_points']) for x in r]);q=s['decile_response']['half_open']
fig,ax=plt.subplots(1,2,figsize=(10,4.2),layout='constrained');ax[0].plot(np.arange(1,26),d,'o',ms=4,color='#176789');ax[0].axhline(0,color='.5',ls='--');ax[0].axhline(d.mean(),color='#c8782e',label=f'mean {d.mean():.3f}');ax[0].set(xlabel='Syllable source row (25 from six birds)',ylabel='Closer − farther dopamine (ΔF/F points)',title='A  Published paired response reproduced');ax[0].legend(frameon=False)
ax[1].plot(np.arange(1,11),q,'o-',color='#176789');ax[1].axhline(0,color='.5',ls='--');ax[1].set(xlabel='Source decile column (quality ordering unlabeled)',ylabel='Dopamine, 200–300ms (ΔF/F %)',title='B  Ordered response in unused source panel');fig.suptitle('Song evaluation is constrained; target acquisition remains distinct',fontsize=13);fig.savefig(H/'song_learning.png',dpi=180);fig.savefig(H/'song_learning.svg')
