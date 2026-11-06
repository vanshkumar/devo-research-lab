"""Assemble exact eligible units and longer-horizon metadata; no trial values."""
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,resource,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'sources/longitudinal_learning_feasibility_2026-10-28/tools'))
import duckdb
cpu,wall=time.process_time(),time.monotonic();IO=Counter();PINS={}


def get(name):
    b=(HERE/name).read_bytes();IO['explicit_reads']+=len(b);PINS[name]=hashlib.sha256(b).hexdigest();return json.loads(b)


agg=get('AGGREGATE_CHRONOLOGY.json');per=get('FOOTER_QUALIFICATION.json');old=get('ORIGINAL_EXCLUSIONS.json')
assert agg['status']==per['status']=='complete'
rows=[];horizons=[];c=duckdb.connect(':memory:')
for r in agg['subjects']:
    if r['status']!='identity_qualified_3000':continue
    a=r['session_metadata_source'];p=HERE/(Path(a['key']).stem+'_metadata.pqt')
    IO['engine_metadata_file_charge']+=p.stat().st_size
    sessions=c.execute(f"SELECT id,date,number,task_protocol FROM read_parquet('{p}') ORDER BY date,number,id").fetchall()
    IO['decoded_chronology_utf8_bytes']+=len(json.dumps(sessions,default=str).encode())
    counts={z['eid']:z['rows'] for z in r['all_trial_identity_counts']}
    training=[z for z in sessions if z[3].startswith('_iblrig_tasks_trainingChoiceWorld')]
    first=training[0][0];active=False;complete=0;seq=[];stop='end_of_registered_training'
    for eid,date,num,protocol in sessions:
        if eid==first:active=True
        if not active:continue
        if not protocol.startswith('_iblrig_tasks_trainingChoiceWorld'):
            if eid in counts:stop='other_observed_task';break
            continue
        if eid not in counts:stop='missing_training_rows';break
        seq.append(dict(eid=eid,date=str(date),number=num,protocol=protocol,rows=counts[eid],start=complete,stop=complete+counts[eid]))
        complete+=counts[eid]
    assert complete>=3000
    rows.append(dict(subject=r['subject'],lab=r['lab'],cohort='public_subject_aggregate',
         eligibility='complete indexed standard training from earliest public training through3000',
         training_sessions=r['used_sessions'],all_continuous_training_sessions=seq,
         continuous_training_opportunities=complete,continuous_stop_reason=stop,
         metadata_url=a['url'],trial_url=r['trial_metadata_source']['url'],
         full_trial_object_bytes=r['trial_metadata_source']['size'],full_trial_object_rows=r['total_aggregate_rows'],
         future_decode_warning='Single-row-group aggregate: a selected response-column decode can expose its WHOLE subject history, including later training/biased/ephys phases. A LIMIT3000 is not a decode boundary. Main authorization must name exact whole-column scope and auxiliary later exposure, or obtain separately certified original session objects.',
         biological_first_exposure_certified=False,prior_public_protocols=r['prior_public_protocols']))
for r in per['subjects']:
    if r['status']!='footer_qualified_3000':continue
    s=r['subject']
    role=('source_only_new273rows' if s=='NYU-42' else 'prior_opaque_schema_sample' if s=='NYU-28' else
          'modern_protocol_robustness_only' if r['cohort']=='modern_hofer_special_project' else 'candidate_primary_evaluation')
    rows.append(dict(subject=s,lab=r['lab'],cohort=r['cohort'],role=role,
          eligibility='footer-complete first3000 standard-training opportunities',
          training_sessions=[{k:z[k] for k in ['eid','date','number','protocol','rows','start','stop','dataset_id','source_url','file_size']} for z in r['probes']],
          complete_session_decode_stop=r['verified_opportunities'],
          biological_first_exposure_certified=False,prior_public_protocols=r['chronology']['earlier_public_protocols']))
assert len(rows)==205 and len({r['subject'] for r in rows})==205
for r in rows:
    if 'role' not in r:r['role']='candidate_primary_evaluation'
    assert ''.join(x for x in r['subject'].lower() if x.isalnum()) not in old['exclusion_keys']
primary=[r for r in rows if r['role']=='candidate_primary_evaluation'];assert len(primary)==192
for h in [3000,4000,6000,10000,20000]:
    rr=[r for r in rows if r['cohort']=='public_subject_aggregate']
    horizons.append(dict(horizon=h,aggregate_subjects_with_continuous_training_through_h=sum(r['continuous_training_opportunities']>=h for r in rr),
        metadata_stop_reasons_below_h=dict(Counter(r['continuous_stop_reason'] for r in rr if r['continuous_training_opportunities']<h)),
        censoring='Task switch/end/missingness may depend on learning; metadata-only eligibility does not make it noninformative censoring.'))
body_upper=sum(r['full_trial_object_bytes'] if 'full_trial_object_bytes' in r else
               sum(z['file_size'] for z in r['training_sessions']) for r in primary)
decoded_upper=sum(r.get('full_trial_object_rows',r.get('complete_session_decode_stop',0))*6*8 for r in primary)
result=dict(utc=datetime.now(timezone.utc).isoformat(),source_format_qualified_animals=205,
      candidate_primary_evaluation=192,primary_counts_by_cohort=dict(Counter(r['cohort'] for r in primary)),
      primary_counts_by_lab=dict(Counter(r['lab'] for r in primary)),
      source_only_exclusions=['NYU-42:273rows/eightfields newly consumed; whole animal excluded',
        'NYU-28:prior2026-10-28 opaque28119byte first-session/schema sample; retain as format-source, exclude from fresh primary'],
      robustness_only='11 SWC_AY modern8.x special-project animals: source-format qualified, separate protocol mixture; no outcomes opened and no universal exact-deployed-code requirement inferred.',
      identity='Conservative nickname normalization plus original154 stable-session exclusions, aggregate registered subject/lab consistency and all aggregate session-ID mapping. No known old/protected aliases. Cache lacks animal UUID; unlogged biological aliases cannot be universally excluded.',
      prior_summary_exposure='Noel publication group learning summaries were exposed in the October28 feasibility review; individual evaluation trial values remain unopened. Published-summary knowledge is retained, not reset.',
      hypothetical_main_source_ingress_upper_bytes=body_upper,
      hypothetical_main_six_field_float64_decode_upper_bytes=decoded_upper,
      main_access='NOT released. New pre-outcome freeze must explicitly own whole aggregate column decode and all auxiliary later exposure; exact saved source URLs/IDs/session chronology are listed below.',
      longer_horizon_availability=horizons,subjects=rows,io=dict(IO),pins=PINS,
      cpu_seconds=time.process_time()-cpu,process_wall_seconds=time.monotonic()-wall,
      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
(HERE/'QUALIFIED_COHORT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['subjects','pins']},indent=2))
