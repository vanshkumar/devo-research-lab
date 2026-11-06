"""Rebuild original participant 3 event revisions; other numerical outcomes not converted."""
import pathlib, zipfile, xml.etree.ElementTree as ET, hashlib, json, math, resource, datetime
root=pathlib.Path(__file__).resolve().parent
p=root/'dataset_exp1.xlsx'
pin='cbd91790cb21a6a1c1abda7043dfe96bc9a01d0be2ed51c572a523466d937aa9'
assert hashlib.sha256(p.read_bytes()).hexdigest()==pin
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
wrap=lambda x: (x+180)%360-180
people={}; selected=[]
with zipfile.ZipFile(p) as z:
    ss=ET.fromstring(z.read('xl/sharedStrings.xml'))
    strings=[''.join(t.text or '' for t in x.findall('.//m:t',ns)) for x in ss]
    with z.open('xl/worksheets/sheet1.xml') as f:
        for _,e in ET.iterparse(f,events=('end',)):
            if not e.tag.endswith('}row'): continue
            row={}
            for c in e.findall('m:c',ns):
                v=c.find('m:v',ns)
                value=None if v is None else v.text
                if c.attrib.get('t')=='s' and value is not None:value=strings[int(value)]
                row[''.join(x for x in c.attrib['r'] if x.isalpha())]=value
            if e.attrib['r']=='1':
                header={k:(v or '').strip() for k,v in row.items()}; e.clear();continue
            if row.get('A') in (None,''):e.clear();continue
            pid=int(float(row['A']))
            meta=people.setdefault(pid,{'rows':0,'flags':set(),'sessions':set(),'blocks':set(),'trials':[]})
            meta['rows']+=1
            for field,col in [('flags','B'),('sessions','C'),('blocks','D')]:meta[field].add(int(float(row[col])))
            meta['trials'].append(int(float(row['G'])))
            if pid==3:
                selected.append({header[k]:None if v in ('',None) else v if v.startswith('#') else float(v) for k,v in row.items()})
            e.clear()
for pid,meta in people.items():
    meta['chronology_complete']=meta.pop('trials')==list(range(1,meta['rows']+1))
    for key in ['flags','sessions','blocks']:meta[key]=sorted(meta[key])
assert len(selected)==378
assert all(x['sbj_code']==3 for x in selected)
assert all(abs(x['sbj_angular_error'])<=180 and abs(x['agent_angular_error'])<=180 and abs(x['final_angular_error'])<=180 for x in selected)
assert all(x['sbj_accurate']==(abs(x['sbj_angular_error'])<=10) for x in selected)
assert all(x['agent_accurate']==(abs(x['agent_angular_error'])<=10) for x in selected)
assert all(x['final_accurate']==(abs(x['final_angular_error'])<=10) for x in selected)
examples=[]; mismatches=[]; previous=[]
for x in selected:
    if x['trial_BLOCK']==1:previous=[]
    gap=wrap(x['agent_angular_error']-x['sbj_angular_error'])
    revision=wrap(x['final_angular_error']-x['sbj_angular_error'])
    ratio=revision/gap if abs(gap)>1e-10 else None
    # The supplied influence is an analysis quantity; retain actual unconstrained revision.
    if len(examples)<3:
        examples.append({'trial_all':x['trial_ALL'],'block':x['block'],'adviser_type_for_audit_only':x['agent_type'],
          'initial_error_degrees':x['sbj_angular_error'],'initial_confidence':x['sbj_confidence'],
          'advice_error_degrees':x['agent_angular_error'],'advice_confidence':x['agent_confidence'],
          'final_error_degrees':x['final_angular_error'],'advice_gap_degrees':gap,'revision_degrees':revision,
          'unclipped_revision_over_gap':ratio,'supplied_influence':x.get('influence_sbj'),
          'prior_feedback_count_current_adviser':len(previous),
          'prior_adviser_errors_degrees':list(previous),'prior_adviser_correct_count':sum(abs(v)<=10 for v in previous),
          'current_feedback_after_revision':{'correct_reference_angle':0.0,'adviser_correct':x['agent_accurate'],'feedback_screen_seconds':x['rt_final_screen']}})
    supplied=x.get('influence_sbj')
    if ratio is not None and 0<=ratio<=1 and isinstance(supplied,float) and abs(ratio-supplied)>1e-10:
        mismatches.append({'trial':x['trial_ALL'],'ratio':ratio,'supplied':supplied})
    previous.append(x['agent_angular_error'])
record={'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'required_event_calculation':True,
 'participant':3,'original_rows':len(selected),'source_sha256':pin,'source_url':'https://osf.io/download/jx3fu/',
 'command':'python3 lab/tasks/advice-reliability-forecast-2026-11-01/first_data_check.py',
 'coordinate':'Exported signed errors share the same current correct-direction reference. Subtract and wrap differences; never use current absolute errors as predictive inputs.',
 'feedback_chronology_source':'Zonca et al2026 Methods ADT: correct direction shown after final choice, screen minimum1 maximum5s. Workbook rt_final_screen is 0–5s feedback-to-next latency.',
 'examples':examples,'accuracy_threshold_checks':1134,'interior_supplied_influence_mismatches':mismatches,
 'metadata_people':people,'exposure':'Entire original XLSX acquired/hashed. Shared strings and worksheet XML decoded; all people ID/inclusion/session/block/trial metadata interpreted. Only participant3 numeric response rows converted/interpreted by this program. Other XML response tokens were parsed as strings, not pristine unacquired observations.',
 'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(root/'FIRST_DATA_CHECK.json').write_text(json.dumps(record,indent=2))
(root/'pilot_person3.json').write_text(json.dumps(selected,indent=2))
print(json.dumps({k:v for k,v in record.items() if k!='metadata_people'},indent=2))
print(json.dumps({'people':len(people),'rows':sum(v['rows'] for v in people.values()),'metadata':people},indent=2))
