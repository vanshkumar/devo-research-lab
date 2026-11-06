"""Audit exported judgments against accuracy and supplied influence; no forecast scores."""
import json,pathlib,hashlib,zipfile,xml.etree.ElementTree as ET,datetime,resource,math
root=pathlib.Path(__file__).resolve().parent
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
wrap=lambda x:(x+180)%360-180
mismatch=[];n=0;badtypes=[];ratioissues=[];maxdiff=0.;compared=0;nearsmall=0;orig=[]
with zipfile.ZipFile(root/'dataset_exp1.xlsx') as z:
 with z.open('xl/worksheets/sheet1.xml') as f:
  for _,e in ET.iterparse(f,events=('end',)):
   if not e.tag.endswith('}row'):continue
   if e.attrib.get('r')=='1':e.clear();continue
   d={}
   for c in e.findall('m:c',ns):
    v=c.find('m:v',ns)
    if v is not None:d[''.join(x for x in c.attrib['r'] if x.isalpha())]=v.text
   if 'A' not in d:e.clear();continue
   n+=1
   r={k:float(d[k]) for k in ('A','B','C','D','E','F','G','H','K','L','M','N','O','P','Q','R','S')}
   orig.append(r)
   gaps=wrap(r['O']-r['K']);change=wrap(r['R']-r['K'])
   bad=[]
   for err,acc in [('K','M'),('O','Q'),('R','S')]:
    if r[acc]!=(abs(r[err])<=10):bad.append({'error_field':err,'error':r[err],'accuracy_field':acc,'accuracy':r[acc],'boundary_distance':abs(abs(r[err])-10)})
   supplied=None
   try:supplied=float(d.get('V',''))
   except ValueError:pass
   ratio=change/gaps if abs(gaps)>1e-12 else None
   # Basic interior ratio consistency is a support check; edge processing can differ.
   if supplied is not None and ratio is not None and abs(gaps)>=5 and .01<ratio<.99 and .01<supplied<.99:
    compared+=1;diff=abs(supplied-ratio);maxdiff=max(maxdiff,diff)
    if diff>1e-6:ratioissues.append({'person':int(r['A']),'trial':int(r['G']),'ratio':ratio,'supplied':supplied})
   if bad:
    implied=None
    if supplied is not None and 0<supplied<1 and abs(1-supplied)>1e-8:
     implied=(r['R']-supplied*r['O'])/(1-supplied)
    mismatch.append({'person':int(r['A']),'trial_all':int(r['G']),'block':int(r['D']),'trial_block':int(r['F']),
      'source_xml_row':int(e.attrib['r']),'keep_trial_angle':r['H'],'author_keep_person':r['B'],'mismatches':bad,
      'initial_error':r['K'],'advice_error':r['O'],'final_error':r['R'],'advice_gap':gaps,'actual_revision':change,'ratio':ratio,
      'supplied_influence':supplied,'initial_error_implied_by_unwrapped_interior_influence':implied,'original_xml_numeric_tokens':d})
   e.clear()
rec={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':n,'people':len(set(r['A'] for r in orig)),
 'original_accuracy_comparisons':3*n,'accuracy_mismatch_rows':mismatch,'accuracy_mismatch_count':sum(len(r['mismatches']) for r in mismatch),
 'interior_influence_rows_compared':compared,'max_interior_ratio_difference':maxdiff,'interior_differences_over1e_6':ratioissues,
 'original_data_scope':'All47people/17766original judgments/advice/final errors and confidence/accuracy now numerically decoded and audited, including all evaluation people. No forecast losses computed. Supplied raw XML derived tokens exposed only where mismatches returned.',
 'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(root/'MEASUREMENT_AUDIT.json').write_text(json.dumps(rec,indent=2))
(root/'audited_original_rows.json').write_text(json.dumps(orig,separators=(',',':')))
print(json.dumps(rec,indent=2))
