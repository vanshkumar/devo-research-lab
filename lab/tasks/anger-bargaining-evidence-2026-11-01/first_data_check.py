"""Descriptive first outcome calculation; not the main test or an untouched split."""
import csv,json,math,statistics,hashlib,datetime,resource,collections
from pathlib import Path
P=Path(__file__).resolve().parent
p=P/'sources/Study1_rawdata.csv'
b=p.read_bytes()
reader=csv.DictReader(b.decode('utf-8-sig').splitlines())
rows=list(reader)[2:]  # Qualtrics question text + ImportId rows, not people.
conditions=['H/H','H/A','A/H','A/A']
cells={c:[] for c in conditions}; checks={c:collections.Counter() for c in conditions}
ambiguous=[]; ids=[]
for i,r in enumerate(rows):
    ids.append(r['ResponseId'])
    active=[c for c in conditions if r['demand_'+c].strip()]
    if len(active)!=1:
        ambiguous.append(i);continue
    c=active[0];v=float(r['demand_'+c])
    if not math.isfinite(v):raise ValueError('nonfinite')
    cells[c].append(v)
    checks[c].update([(r['check_'+c+'_feel'],r['check_'+c+'_communi'])])
out={'calculated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'EXECUTED_DESCRIPTIVE_ORIGINAL_RESPONSE_CALCULATION; main scientific/source gate PENDING',
 'source':{'paper_doi':'10.1007/s10726-023-09850-0','node':'https://osf.io/upbcf/',
   'download':'https://osf.io/download/hpc8f/','sha256':hashlib.sha256(b).hexdigest(),
   'bytes':len(b),'listing_sha256_matches':hashlib.sha256(b).hexdigest()=='7c886c21731f72d0faf72cd082f8fb9ced05492888d334757d161f72fb5a14ee'},
 'independent_unit':'one recorded participant response, identified by original ResponseId; no repeated-round independence assumed',
 'record_count':len(rows),'unique_nonempty_response_ids':len(set(ids)) if all(ids) else None,
 'ambiguous_branch_rows':ambiguous,
 'condition_meaning':'First letter disclosed supervisor experienced emotion; second communicated emotion. H happy, A angry. Between people, one nonempty branch per response.',
 'outcome':'participant final hypothetical salary-raise demand, percentage points of salary; initial 5.5 supplied by scenario. Lower demand means more concession.',
 'payoff_and_chronology':'Fixed participation payment, hypothetical supervisor; not realized salary or an interactive opponent. Demand follows manipulation checks and precedes perceived-limit reports per primary methods. Source randomization asserted, deployment code not certified.',
 'inclusion':'All 170 source responses before manipulation-check/outlier exclusion; descriptive only. Published analysis uses 144. No clean cohort or check encoding presumed here.',
 'cells':{c:{'n':len(v),'mean_demand':statistics.mean(v),'median_demand':statistics.median(v),
  'sd_demand':statistics.stdev(v),'min':min(v),'max':max(v),
  'check_response_pairs':[{ 'feel':a,'communicated':b,'n':n} for (a,b),n in checks[c].items()]} for c,v in cells.items()},
 'licensing':'OSF project public/read permitted, node_license null; external data reuse license not certified by article CC-BY4.',
 'exposure':'Complete raw Study1 CSV bytes acquired and decoded including auxiliary columns. Study1 all development/exposed. Study2/3 paper summaries exposed; payloads not acquired at this calculation.',
 'resources':{'input_payload_read_decode_hash_allowance_bytes':4*len(b),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
   'provider_transfer_and_wrapper_peaks':'unknown; see FETCH_LEDGER and final RESOURCES; six provider ops plus six fetch attempts as of this calculation'},
 'not_earned':['unique information-vs-affect mechanism','source-design certification','main freeze','predictions','evaluation','independent review']}
(P/'FIRST_DATA_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
