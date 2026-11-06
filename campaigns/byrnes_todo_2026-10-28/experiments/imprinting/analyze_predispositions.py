import pathlib,json,math,csv
import pandas as pd,numpy as np
from scipy import stats
R=pathlib.Path(__file__).resolve().parents[2];D=R/'data/imprinting';H=pathlib.Path(__file__).parent
rng=np.random.default_rng(20261028);rows=[];groups={};checks=[]
for i,ext,label in [(1,'xlsx','red_both'),(2,'xlsx','yellow_both'),(3,'csv','red_large_yellow_small'),(4,'csv','yellow_large_red_small')]:
 p=D/f'13420_2024_638_MOESM{i}_ESM.{ext}';d=pd.read_excel(p) if ext=='xlsx' else pd.read_csv(p)
 assert not d.duplicated(['chickID','bins']).any();assert all(d.groupby('chickID').size()==20)
 # Resolve adult side per subject using agreement with supplied ratio, not result direction.
 for sid,a in d.groupby('chickID'):
  den=a.left+a.right;lp=100*a.left/den;rp=100*a.right/den
  el=np.nansum(abs(a.adultPercentage-lp));er=np.nansum(abs(a.adultPercentage-rp));side='left' if el<er else 'right'
  target=a[side].sum();total=den.sum();pct=a.adultPercentage.mean()
  observed=np.where(den>0,100*a[side]/den,50)
  errors=np.abs(observed-a.adultPercentage);checks.append(dict(group=label,chickID=int(sid),target_side=side,max_ratio_discrepancy=float(max(errors))))
  rows.append(dict(group=label,chickID=int(sid),sex=a.sex.iloc[0],mean_minute_preference=float(pct),occupancy_weighted_preference=float(100*target/total),target_fraction_all_frames=float(100*target/a[['left','centre','right']].to_numpy().sum()),choice_frames=int(total),tracked_frames=int(a[['left','centre','right']].to_numpy().sum())))
 s=pd.DataFrame([r for r in rows if r['group']==label]);groups[label]=s
pd.DataFrame(rows).to_csv(H/'predisposition_subjects.csv',index=False);pd.DataFrame(checks).to_csv(H/'ratio_reconstruction.csv',index=False)
summary=[]
for label,s in groups.items():
 v=s.mean_minute_preference.values;boot=np.mean(v[rng.integers(len(v),size=(5000,len(v)))],axis=1)
 summary.append(dict(group=label,n=len(v),mean=float(v.mean()),sem_subject=float(stats.sem(v)),ci95=np.quantile(boot,[.025,.975]).tolist(),wilcoxon_vs50=float(stats.wilcoxon(v-50).pvalue),mean_occupancy_weighted=float(s.occupancy_weighted_preference.mean()),target_fraction_all_frames_mean=float(s.target_fraction_all_frames.mean())))
a=groups['red_both'].mean_minute_preference.values;b=groups['yellow_both'].mean_minute_preference.values
boots=a[rng.integers(len(a),size=(5000,len(a)))].mean(1)-b[rng.integers(len(b),size=(5000,len(b)))].mean(1)
# Positive known effect and null: exact sign symmetry through elementary finite enumeration.
from itertools import product
v=np.array([1.,2.,3.,4.]);exact=np.mean([sum(sign*v)>=v.sum() for sign in product([-1,1],repeat=4)]);assert exact==1/16
assert abs(summary[0]['mean']-66.62135451514818)<1e-10 and abs(summary[1]['mean']-48.07638955680646)<1e-10
physical=dict(large_area_mm2=111.8**2,small_total_area_mm2=5*50**2,large_perimeter_mm=4*111.8,small_total_perimeter_mm=5*4*50,red_srgb_relative_luminance=.2126,yellow_srgb_relative_luminance=.2126+.7152,white_background_michelson_red=(1-.2126)/(1+.2126),white_background_michelson_yellow=(1-.9278)/(1+.9278),caution='Standard sRGB illustration only; actual monitor/chicken photoreceptor brightness not measured. Size differs in numerosity and total contour as well as individual extent.')
result=dict(groups=summary,red_minus_yellow=dict(estimate=float(a.mean()-b.mean()),ci95=np.quantile(boots,[.025,.975]).tolist(),mannwhitney_p=float(stats.mannwhitneyu(a,b).pvalue)),ratio_anomaly_rows=[c for c in checks if c['max_ratio_discrepancy']>1e-5],known_control_exact_p=exact,stimulus_audit=physical,limitations=['Tables already omit nonapproachers, so population attraction denominators cannot be reconstructed from raw tables.','Minute mean scores impute50 when neither side occupied; occupancy-weighted sensitivity is a different summary.','No trained-imprinting manipulation or teaching signal in these naive birds.'])
(H/'predisposition_summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
