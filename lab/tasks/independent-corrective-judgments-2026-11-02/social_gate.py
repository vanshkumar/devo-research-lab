"""Small source-level arithmetic and independent original-cell reference; no group effect test."""
import collections, datetime, decimal, fractions, hashlib, json, pathlib, re, resource, zipfile, xml.etree.ElementTree as E
p=pathlib.Path(__file__).resolve().parent
j=json.loads((p/'SOCIAL_TABLE_TYPED.json').read_text());s=j['sheets'][0]
col=lambda x:re.sub(r'[0-9]','',x)
header={col(k):v['value'] for k,v in s['rows'][0]['cells'].items()}
records=[]
for row in s['rows'][1:]:
    records.append({header[col(k)]:v['value'] for k,v in row['cells'].items()})
units=[{k:r.get(k) for k in ('MaleNum','Condition','ConditionNum','Group')} for r in records]
assert len(records)==18 and len({r['MaleNum'] for r in records})==18
groups=collections.defaultdict(list)
for r in records:groups[r['Group']].append(r['Condition'])
assert len(groups)==9 and all(len(v)==2 for v in groups.values())
first=records[0]
song=decimal.Decimal(first['T5_SongCount']);video=decimal.Decimal(first['T5_ContVidCount']);prop=decimal.Decimal(first['T5_ContProp'])
computed=video/song
diagnostic={'subject':first['MaleNum'],'song_count':str(song),'cont_video_count':str(video),
            'source_prop':str(prop),'computed_ratio':str(computed),'difference':str(abs(computed-prop)),
            'note':'Original1e-6source-proportion equality assertion failed; source value retained without repair.',
            'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(p/'SOCIAL_RATIO_DIAGNOSTIC.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
print(json.dumps(diagnostic,indent=2))

# Original XML replay checks exactly the cells used for first subject and ratio.
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(p/'source/Supplementary Data 1.xlsx') as z:
    string_root=E.fromstring(z.read('xl/sharedStrings.xml'))
    strings=[''.join(e.itertext()) for e in string_root]
    root=E.fromstring(z.read(s['target']))
    row=root.find("m:sheetData/m:row[@r='2']",NS)
    vals={}
    for c in row:
        v=c.find('m:v',NS)
        if v is not None:vals[c.attrib['r']]=strings[int(v.text)] if c.attrib.get('t')=='s' else v.text
    assert vals['A2']==first['MaleNum'] and vals['B2']==first['Condition'] and vals['D2']==first['Group']
    assert vals['F2']==first['T5_SongCount'] and vals['G2']==first['T5_ContVidCount'] and vals['L2']==first['T5_ContProp']
    exact=fractions.Fraction(vals['G2'])/fractions.Fraction(vals['F2'])
    assert abs(float(exact)-float(computed))<1e-15
out={'calculated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_declared_sha256':j['sha256'],'sheet':s['name'],'columns':len(header),'rows':len(records),
 'unit_records':units,'pair_count':len(groups),'conditions':dict(collections.Counter(r['Condition'] for r in records)),
 'session_markers':sorted({re.match(r'T(\d+)_',h).group(1) for h in header.values() if re.match(r'T(\d+)_',h)},key=int),
 'first_original_subject':{k:first[k] for k in ('MaleNum','Condition','Group','T5_SongCount','T5_ContVidCount','T5_RemVidCount','T5_ContProp')},
 'first_ratio':{'formula':'T5_ContVidCount/T5_SongCount','exact_fraction':str(exact),'computed_decimal':str(computed),'provided':str(prop),'absolute_discrepancy':str(abs(computed-prop))},
 'independent_reference':'Original XML cell A2/B2/D2/F2/G2/L2 matches typed output; independent exact rational division matches computed ratio within1e-15. Supplied proportion differs; original equality failure retained, no source repair.',
 'later_and_aggregate_headers':[h for h in header.values() if not re.match(r'T(\d+)_',h)],
 'identification_limit':{'present':'Subject/condition/sibling-pair identifiers, five sampled-session behavior counts/proportions, final song-learning summaries.',
 'absent_in_this_table':'Per-vocalization acoustic identity, exact feedback time, feature-specific improvement/rejection judgment and a next-vocalization correction trace.',
 'not_claimed':'No group effect estimated, causal result reproduced, closed-loop reward learned or biological absence inferred.',
 'split':'Nine paired cohorts/eighteen birds; repeated sessions are not independent birds. All source cells already decoded, no untouched evaluation claimed.'},
 'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(p/'SOCIAL_DATA_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
