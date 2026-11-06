import pathlib,zipfile,xml.etree.ElementTree as E,json,math,hashlib,datetime,resource
r=pathlib.Path(__file__).resolve().parent;n={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
raw=r/'dataset_exp1.xlsx';assert hashlib.sha256(raw.read_bytes()).hexdigest()=='cbd91790cb21a6a1c1abda7043dfe96bc9a01d0be2ed51c572a523466d937aa9'
out=[];missing=[];mismatch=[];typed=[]
cols=('A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S')
with zipfile.ZipFile(raw) as z:
 ss=[''.join(t.text or '' for t in x.findall('.//m:t',n)) for x in E.fromstring(z.read('xl/sharedStrings.xml'))]
 with z.open('xl/worksheets/sheet1.xml') as f:
  for _,e in E.iterparse(f,events=('end',)):
   if not e.tag.endswith('}row'):continue
   if e.attrib.get('r')=='1':e.clear();continue
   d={}
   for c in e.findall('m:c',n):
    col=''.join(x for x in c.attrib['r'] if x.isalpha())
    if col not in cols:continue
    v=c.find('m:v',n);s=None if v is None else v.text
    if c.attrib.get('t')=='s' and s is not None:
     val=ss[int(s)];typed.append({'cell':c.attrib['r'],'raw_index':s,'decoded':val});s=val
    d[col]=None if s in ('NaN','NA','',None) else float(s)
   if 'A' not in d:e.clear();continue
   assert all(d.get(k) is not None for k in ('A','B','C','D','E','F','G','L','M','N','P','Q','S'))
   for k in ('K','O','R'):
    if d.get(k) is None:missing.append({'person':int(d['A']),'trial_all':int(d['G']),'trial_block':int(d['F']),'field':k,'xml_row':int(e.attrib['r'])})
   for k,b in [('K','M'),('O','Q'),('R','S')]:
    if d.get(k) is not None and d[b]!=(abs(d[k])<=10):mismatch.append({'person':d['A'],'trial':d['G'],'field':k,'error':d[k],'accuracy':d[b]})
   out.append(d);e.clear()
assert len(out)==17766 and not mismatch
assert len(missing)==6 and {v['person'] for v in missing}=={13}
assert sum(v['field']=='K' for v in missing)==5 and sum(v['field']=='R' for v in missing)==1
dest=r/'original_typed_rows.json';dest.write_text(json.dumps(out,separators=(',',':'),allow_nan=False))
rec={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':len(out),'people':47,'missing_original_fields':missing,'finite_error_accuracy_mismatches':mismatch,'typed_cache_bytes':dest.stat().st_size,'typed_cache_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'typed_shared_string_original_cells':typed,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'supersedes':'MEASUREMENT_AUDIT.json wrongly interpreted shared string indices as numbers. No source contradiction was established.'}
(r/'TYPED_MEASUREMENT_AUDIT.json').write_text(json.dumps(rec,indent=2));print(json.dumps({k:v for k,v in rec.items() if k!='typed_shared_string_original_cells'},indent=2))
