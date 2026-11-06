"""Original-subject probe arithmetic, independently implemented twice; stdlib only."""
import collections, csv, datetime, hashlib, io, json, pathlib, resource

ROOT=pathlib.Path(__file__).resolve().parent
raw=(ROOT/'source/Final_probes_20200816.csv').read_bytes()
sha=hashlib.sha256(raw).hexdigest()
assert sha=='fc953e012778aea5bba206ae5875fa0531b9ee0e21545c5f6da6c5db483761de'
rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'),newline='')))
required={'aviary','cycle','time','individual','left','right','sound_id','ground_truth','decision'}
assert required.issubset(rows[0])
excluded=lambda r:r['aviary']=='1' and r['cycle']=='1'
def parse_time(s):
    for fmt in ('%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M','%d/%m/%Y %H:%M','%d/%m/%Y %H:%M:%S'):
        try:return datetime.datetime.strptime(s,fmt)
        except ValueError:pass
    raise ValueError('Unrecognized deposited timestamp: '+s)
# Fixed source-defined exclusion, then earliest timestamp/row index; no choice-based selection.
index,first=min(((i,r) for i,r in enumerate(rows) if not excluded(r)),key=lambda z:(parse_time(z[1]['time']),z[0]))
subject=first['individual'];context=(first['aviary'],first['cycle'])
selected=[(i,r) for i,r in enumerate(rows) if r['individual']==subject and (r['aviary'],r['cycle'])==context]
ordered=sorted(selected,key=lambda z:(parse_time(z[1]['time']),z[0]))
assert all(r['ground_truth']=='probe' for _,r in selected)
diagnostic={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'subject':subject,'context':context,
            'counts':dict(collections.Counter(r['decision'] for _,r in selected)),
            'other_rows':[r for _,r in selected if r['decision'] not in ('Left','Right')][:5],
            'process_peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'note':'Diagnostic after initial exact-two-code assertion failed; retain all raw codes.'}
(ROOT/'RESPONSE_CODE_CHECK_CURRENT.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
assert all(r['decision'] in ('Left','Right','NA') for _,r in selected)
counts=collections.Counter(r['decision'] for _,r in selected)
responding=counts['Left']+counts['Right']
by_stim=collections.defaultdict(list)
for i,r in ordered:by_stim[(r['left'],r['right'],r['sound_id'])].append((i,r))
repeat_key=next(k for k,v in by_stim.items() if len(v)>=2)
repeated=by_stim[repeat_key]
rc=collections.Counter(r['decision'] for _,r in repeated)

# Reference uses positional csv.reader, index arithmetic and sums instead of DictReader/groups.
reader=csv.reader(io.StringIO(raw.decode('utf-8-sig'),newline=''));head=next(reader); values=list(reader)
ix={n:head.index(n) for n in required}
ref_indices=[i for i,v in enumerate(values) if v[ix['individual']]==subject and
             (v[ix['aviary']],v[ix['cycle']])==context]
assert ref_indices==[i for i,_ in selected]
ref_left=sum(values[i][ix['decision']]=='Left' for i in ref_indices)
ref_right=sum(values[i][ix['decision']]=='Right' for i in ref_indices)
assert ref_left==counts['Left'] and ref_right==counts['Right']
repeat_indices=[i for i in ref_indices if tuple(values[i][ix[k]] for k in ('left','right','sound_id'))==repeat_key]
assert set(repeat_indices)=={i for i,_ in repeated}
ref_rl=sum(values[i][ix['decision']]=='Left' for i in repeat_indices)
assert ref_rl==rc['Left']
def ref_time(s):
    date,clock=s.split(); hms=[int(x) for x in clock.split(':')]
    if '-' in date:y,m,d=map(int,date.split('-'))
    else:d,m,y=map(int,date.split('/'))
    return (y,m,d,*hms,*([] if len(hms)==3 else [0]))
ref_first=min((i for i,v in enumerate(values) if not(v[ix['aviary']]=='1' and v[ix['cycle']]=='1')),
              key=lambda i:(ref_time(values[i][ix['time']]),i))
assert ref_first==index

out={'calculated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
     'input_sha256':sha,'input_bytes':len(raw),'columns':head,'all_table_rows_tokenized':len(rows),
     'ground_truth_values':dict(collections.Counter(r['ground_truth'] for r in rows)),
     'selection':'Earliest timestamp, row-index tie-break, after source-defined aviary1/cycle1 exclusion; subject and first context fixed without response selection.',
     'original_subject':subject,'aviary_cycle':context,'first_data_row_1based':index+2,
     'context_responses':len(selected),'left':counts['Left'],'right':counts['Right'],
     'uninterpreted_NA':counts['NA'],'responding':responding,
     'right_fraction_of_recorded_sides':counts['Right']/responding,
     'chronology_first':ordered[0][1]['time'],'chronology_last':ordered[-1][1]['time'],
     'source_time_zone':'not specified in deposited table; native values retained',
     'first_record':first,'first_repeat_stimulus':dict(zip(('left','right','probe'),repeat_key)),
     'repeat_responses':len(repeated),'repeat_left':rc['Left'],'repeat_right':rc['Right'],
     'repeat_uninterpreted_NA':rc['NA'],
     'repeat_right_fraction_of_recorded_sides':rc['Right']/(rc['Left']+rc['Right']) if rc['Left']+rc['Right'] else None,
     'repeat_chronological_records':[{'data_row_1based':i+2,'time':r['time'],'decision':r['decision']} for i,r in repeated],
     'reference':'Independent positional-reader sums and exact source-row identity checks passed.',
     'semantics':{'observation':'Probe playback followed by left/right perch choice in trained categorical-similarity task.',
                  'stimuli':'Deposited representative left/right training identities and actual probe sound_id, not a controlled scalar edit.',
                  'feedback':'Paper states either probe side rewarded. No delivered reward field in this table; intended protocol is not hardware verification.',
                  'NA':'Literal NA retained separately; no claim that it is a biological omission rather than unrecorded response.',
                  'correction':'No subject-produced song, revision direction, target acceptability or song-learning endpoint in these rows.',
                  'training_accuracy':'acc_cycle is supplied all-cycle summary, not reconstructed from this probe-only export.'},
     'exposure':{'all_rows':'Full CSV bytes acquired/hashed/decoded; all17 fields tokenized in both readers, all subject/context/time/probe status metadata scanned.',
                 'numeric_interpretation':'Only selected subject/context binary choice counts and repeated-probe choices; first five excluded-cycle rows already inspected during schema check.',
                 'not_holdout':'No acquired or tokenized row is pristine unacquired evaluation; no new scientific comparison yet.'},
     'parser_correction':'Initial strict Left/Right assertion failed on literal NA. Follow-up also exposed mixed ISO and day/month timestamps; lexicographic earliest was wrong. Both failed passes preserved in failure record and diagnostic. No endpoint/model selection change.',
     'process_peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(ROOT/'FIRST_DATA_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
