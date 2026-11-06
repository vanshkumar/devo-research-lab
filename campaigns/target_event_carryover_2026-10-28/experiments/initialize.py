from pathlib import Path
import csv,hashlib,json,datetime
R=Path(__file__).resolve().parents[1]; S=R.parents[1]/'sources/learning_intervention_feasibility_2026-10-28'
manifest=json.loads((S/'source_manifest.json').read_text()); prov=[]; split={}
for f in manifest['files']:
 p=S/f['local']; b=p.read_bytes(); sh=hashlib.sha256(b).hexdigest(); blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(); assert blob==f['expected_git_blob']
 prov.append(dict(f,sha256=sh,bytes=len(b)))
 if f['local'] in ['tsay_TE_SPE.csv','tsay_controljump.csv']:
  with p.open() as h: ids=sorted(set(r['SN'] for r in csv.DictReader(h)),key=int)
  ids.sort(key=lambda v:hashlib.sha256(('target-event-carryover-v1|'+f['local']+'|'+v).encode()).hexdigest())
  split[f['local']]={'development':sorted(ids[:10],key=int),'validation':sorted(ids[10:],key=int)}
record={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rule':'Within each primary file, order participant SN by SHA256(target-event-carryover-v1|filename|SN); first ten development, remaining ten validation. Split computed using IDs only. Person key is (source_file,SN).','split':split,'exposure':'No raw hand-angle effects inspected. Prior published summaries and input-only audit known. External outcomes sealed.'}
for name,obj in [('protocol/split.json',record),('provenance/source_manifest.json',prov)]:
 p=R/name
 if p.exists(): assert json.loads(p.read_text())==obj or name.endswith('split.json')
 else:p.write_text(json.dumps(obj,indent=2)+'\n')
print(json.dumps(record,indent=2))
