"""Reconstruct published figure endpoint marks; not raw data or bird assignment."""
from pathlib import Path
import json,csv
import numpy as np
from PIL import Image
from scipy.ndimage import label,find_objects
p=Path(__file__).resolve().parent
raw=p.parent.parent/'inputs/zhao'
im=np.asarray(Image.open(raw/'figure5.jpg')).astype(int)
# Axes manually inspected: 0,400,800,1200ms tick centers at y430,309,188,67.
axis={'source':'figure5.jpg panel C','tick_y_px':[430,309,188,67],'tick_value_ms':[0,400,800,1200],'pixel_error':2}
ys=np.array(axis['tick_y_px']); vals=np.array(axis['tick_value_ms'])
slope,intercept=np.polyfit(ys,vals,1)
records=[]
# ROIs contain only each cohort's blue diamond marks, not boxplots.
for group,rect in [('opto_only_300',(1678,52,1731,405)),('natural_plus_opto_300',(1804,190,1858,401))]:
 x0,y0,x1,y1=rect;a=im[y0:y1,x0:x1,:3]
 mask=(a[:,:,2]>a[:,:,0]+30)&(a[:,:,2]>a[:,:,1]+20)&(a[:,:,2]<210)
 lab,n=label(mask)
 for i,sl in enumerate(find_objects(lab),1):
  if sl is None:continue
  yy,xx=sl;area=int((lab[sl]==i).sum());w=xx.stop-xx.start;h=yy.stop-yy.start
  if area<25 or w<7 or h<7:continue
  cx=x0+(xx.start+xx.stop-1)/2;cy=y0+(yy.start+yy.stop-1)/2
  records.append({'group':group,'x_px':cx,'y_px':cy,'duration_ms':slope*cy+intercept,'extraction_error_ms':abs(slope)*2,'component_area':area,'bbox_width':w,'bbox_height':h})
records.sort(key=lambda r:(r['group'],r['duration_ms']))
print(records)
(p/'figure5_duration_digitization.json').write_text(json.dumps({'axis':axis,'slope':slope,'intercept':intercept,'records':records,'warning':'Published element-summary marks; no bird IDs. Do not identify table rows by matching magnitudes.'},indent=2)+'\n')
# Component merging affected the four lowest opto-only marks. Visual inspection of
# the preserved crop shows four separate diamond centers. These manual centers
# replace the two merged components and receive a wider ±3-pixel uncertainty.
clean=[r for r in records if not (r['group']=='opto_only_300' and r['y_px']>340)]
for cx,cy in [(1692.5,377.5),(1717.5,372.0),(1717.5,366.0),(1692.5,354.5)]:
 clean.append({'group':'opto_only_300','x_px':cx,'y_px':cy,'duration_ms':float(slope*cy+intercept),'extraction_error_ms':float(abs(slope)*3),'method':'manual diamond centers after connected-component overlap; see fig5_lowpoints_reading.png'})
import statistics
summary={}
for group in ['opto_only_300','natural_plus_opto_300']:
 rr=[r for r in clean if r['group']==group]
 values=sorted(r['duration_ms'] for r in rr)
 summary[group]={'plotted_element_count':len(values),'source_bird_count':4 if group=='opto_only_300' else 3,'element_duration_median_ms':statistics.median(values),'element_duration_mean_ms':statistics.mean(values),'duration_values_ms':values,'conservative_median_extraction_envelope_ms':[statistics.median(values)-abs(slope)*4,statistics.median(values)+abs(slope)*4],'envelope_definition':'4 pixels covers 3-pixel symbol centers plus1-pixel axis calibration; not biological CI','bird_ids_available':False}
(p/'figure5_duration_digitization_corrected.json').write_text(json.dumps({'axis':axis,'records':clean,'summary':summary,'warning':'Figure-derived element summaries, not raw measurements. No table row membership or individual-bird values inferred. Source captions give7 elements/4 birds and4 elements/3 birds.'},indent=2)+'\n')
print(json.dumps(summary,indent=2))
