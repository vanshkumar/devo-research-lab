"""Independent metadata-only horizon/full-aggregate identity challenge."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,time,resource
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
NEW=ROOT/'lab/tasks/independent-acquisition-cohort-2026-11-05'
reads=[]
def load(n):
    b=(NEW/n).read_bytes()
    reads.append(dict(path=str((NEW/n).relative_to(ROOT)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    return json.loads(b)
cpu=time.process_time()
co=load('QUALIFIED_COHORT.json');old=load('ORIGINAL_SESSION_IDS.json')
ex=load('ORIGINAL_EXCLUSIONS.json');chrono=load('AGGREGATE_CHRONOLOGY.json')
oldnames={r['subject'] for r in ex['subjects']}
normalise=lambda s: ''.join(c for c in s.lower() if c.isalnum())
excluded_keys={normalise(s) for s in oldnames}
excluded_sessions=[r for r in old['sessions'] if normalise(r['subject']) in excluded_keys]
oldids={r['eid'] for r in excluded_sessions}
all_metadata_ids={r['eid'] for r in old['sessions']}
primary=[r for r in co['subjects'] if r['role']=='candidate_primary_evaluation']
names={s['subject'] for s in primary}
horizon={};horizon_dups=[];horizon_overlap=[]
for s in primary:
    for r in s['training_sessions']:
        eid=r['eid']
        if eid in oldids:horizon_overlap.append(dict(subject=s['subject'],eid=eid))
        if eid in horizon and horizon[eid]!=s['subject']:horizon_dups.append(dict(subjects=[horizon[eid],s['subject']],eid=eid))
        horizon[eid]=s['subject']
full={};full_dups=[];full_overlap=[]
for s in chrono['subjects']:
    if s['subject'] not in names:continue
    for row in s['all_trial_identity_counts']:
        eid=row['eid']
        if eid in oldids:full_overlap.append(dict(subject=s['subject'],eid=eid))
        if eid in full and full[eid]!=s['subject']:full_dups.append(dict(subjects=[full[eid],s['subject']],eid=eid))
        if eid in horizon and horizon[eid]!=s['subject']:full_dups.append(dict(subjects=[horizon[eid],s['subject']],eid=eid))
        full[eid]=s['subject']
result=dict(utc=datetime.now(timezone.utc).isoformat(),status='complete',
    primary_animals=len(primary),distinct_primary_horizon_sessions=len(horizon),
    whole_aggregate_sessions_for_primary_subjects=len(full),old_excluded_session_UUIDs=len(oldids),
    metadata_universe_session_UUIDs=len(all_metadata_ids),
    metadata_universe_subjects=len({r['subject'] for r in old['sessions']}),
    full_aggregate_overlap_with_metadata_only_sessions=len(set(full)&(all_metadata_ids-oldids)),
    original_exclusion_subjects=len(oldnames),
    horizon_old_session_overlap=horizon_overlap,horizon_cross_animal_shared_sessions=horizon_dups,
    whole_aggregate_old_session_overlap=full_overlap,whole_aggregate_cross_animal_shared_sessions=full_dups,
    known_name_overlap=sorted(names&oldnames),source_only_animals_in_primary=sorted(names&{'NYU-28','NYU-42'}),
    scope='Full-aggregate session UUID challenge covers later auxiliary rows to be acquired by a hypothetical whole-column read; ASD payload access is only listed complete sessions.',
    residual_identity_uncertainty='Animal UUID unavailable; undocumented biological renaming not universally excluded.',
    no_evaluation_response_or_outcome_payload_reads=True,
    resources=dict(cpu_seconds=time.process_time()-cpu,explicit_read_bytes=sum(x['bytes'] for x in reads),
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,read_receipts=reads,public_ingress_bytes=0))
assert len(primary)==192 and len(horizon)==1537
assert not horizon_overlap and not horizon_dups and not full_overlap and not full_dups
assert not result['known_name_overlap'] and not result['source_only_animals_in_primary']
(HERE/'FULL_IDENTITY_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='resources'},indent=2))
