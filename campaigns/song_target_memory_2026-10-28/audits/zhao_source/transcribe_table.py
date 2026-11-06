"""Manual visual transcription of original raster Table S1; no bird IDs inferred."""
from pathlib import Path
import csv,json,statistics
p=Path(__file__).resolve().parent
short=[20.4,22.2,37.7,40.8,45.0,45.5,47.0,47.2,50.6,51.6,54.5,56.9,59.2,62.3,64.6,69.9,83.0,86.9,90.4,91.9,93.1,96.8,101.4,105.7,145.3,152.0]
short_sd=[2.3,3.1,3.5,9.1,4.3,5.9,5.7,9.3,6.2,5.9,4.1,6.4,3.3,9.8,5.2,8.9,8.6,6.4,5.0,4.7,18.7,7.0,6.9,5.1,8.3,17.4]
long=[176.1,194.2,194.4,213.4,253.0,323.5,342.9,434.3,568.1,674.2,1152.7]
long_sd=[13.0,6.4,11.9,18.6,7.9,9.3,39.7,33.2,6.7,101.3,109.6]
assert len(short)==len(short_sd)==26 and len(long)==len(long_sd)==11
with (p/'table_s1_transcription.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['protocol','table_position','element_mean_ms','within_element_sd_ms','renditions','bird_id','source'])
 for group,means,sds in [('four_50ms',short,short_sd),('single_300ms_pooled',long,long_sd)]:
  for i,(mu,sd) in enumerate(zip(means,sds),1):w.writerow([group,i,mu,sd,40,'unknown','Supplement PDF page15 Table S1'])
res={}
for group,means in [('50ms_table',short),('300ms_pooled_table',long)]:
 res[group]={'n_elements':len(means),'mean':statistics.mean(means),'median':statistics.median(means),'range':[min(means),max(means)],'reported_average':70.1 if group.startswith('50') else 411.5}
res['50ms_one_omitted_range']={'median_ms':[min(statistics.median(short[:i]+short[i+1:]) for i in range(26)),max(statistics.median(short[:i]+short[i+1:]) for i in range(26))]}
(p/'table_s1_summary.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res,indent=2))
