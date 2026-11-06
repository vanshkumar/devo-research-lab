import collections, csv, datetime, hashlib, json, pathlib, re, resource
p=pathlib.Path(__file__).resolve().parent
raw=(p/'source/Final_probes_20200816.csv').read_bytes()
rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
retained=[r for r in rows if not(r['aviary']=='1' and r['cycle']=='1')]
unit=collections.Counter((r['individual'],r['aviary'],r['cycle']) for r in retained)
counts=collections.Counter(r['decision'] for r in retained)
assert len(retained)==25999
assert counts['Left']+counts['Right']==22048
out={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'zandberg':{'all_probe_rows':len(rows),'excluded_aviary1_cycle1':len(rows)-len(retained),
 'retained_probe_rows':len(retained),'retained_recorded_side_choices':counts['Left']+counts['Right'],
 'retained_raw_choice_codes':dict(counts),'subjects':len({r['individual'] for r in retained}),
 'subject_aviary_cycles':len(unit),'probe_identities':len({r['sound_id'] for r in retained}),
 'probe_identities_with_recorded_side':len({r['sound_id'] for r in retained if r['decision'] in ('Left','Right')}),
 'reference':'Published25999probes/22048sidechoices reproduced exactly after stated av1cycle1exclusion; export itself still contains the492 excluded rows.',
 'missing_fields':['produced_song','song_revision','corrective_direction','acceptability','delivered_reward'],
 'note':'Probe export validates source population totals. This is not a reproduction of published model performance or training accuracy.'}}
html=(p/'source/social_page.html').read_text()
start=html.index('window.INITIAL_STATE = ')+len('window.INITIAL_STATE = ')
state,end=json.JSONDecoder().raw_decode(html[start:])
(p/'source/social_embedded_state.json').write_text(json.dumps(state,indent=2)+'\n')
out['social_state']={'top_keys':list(state),'snapshot':state.get('dataset'),'files':state.get('files')}
out['peak_rss_bytes_macos']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
(p/'SOURCE_AUDIT_INTERIM.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'at_utc':out['at_utc'],'zandberg':out['zandberg'],'peak_rss_bytes_macos':out['peak_rss_bytes_macos']},indent=2))
