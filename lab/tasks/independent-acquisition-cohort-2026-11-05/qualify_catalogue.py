"""Inspect official global metadata after original-subject/session exclusions."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import resource
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'sources/longitudinal_learning_feasibility_2026-10-28/tools'))
import duckdb
cpu,wall=time.process_time(),time.monotonic()
IO=Counter();PINS={}


def read(p):
    b=p.read_bytes();IO['explicit_read_bytes']+=len(b)
    PINS[str(p.relative_to(ROOT))]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    return b


def get(p):return json.loads(read(p))
def norm(s):return re.sub('[^a-z0-9]','',s.lower())
def save(n,x):(HERE/n).write_text(json.dumps(x,indent=2,default=str)+'\n')


def main():
    exclusions=get(HERE/'ORIGINAL_EXCLUSIONS.json')
    keys=set(exclusions['exclusion_keys'])
    original=get(HERE/'ORIGINAL_SESSION_IDS.json')['sessions']
    # Metadata-only catalogue membership is not prior outcome consumption.
    # Propagate aliases only from the actual154 excluded subjects.
    oldeids={r['eid'] for r in original if norm(r['subject']) in keys}
    c=duckdb.connect(':memory:')
    for fname,view in [('GLOBAL_sessions.pqt','s'),('GLOBAL_datasets.pqt','d')]:
        p=HERE/fname;read(p)
        IO['engine_file_full_size_charge']+=p.stat().st_size
        c.execute(f"CREATE VIEW {view} AS SELECT * FROM read_parquet('{p}')")
    rows=c.execute('SELECT id,subject,lab,date,number,task_protocol,projects FROM s ORDER BY subject,date,number,id').fetchall()
    IO['decoded_metadata_representation_bytes']+=len(json.dumps(rows,default=str).encode())
    aliases={r[1] for r in rows if r[0] in oldeids}
    keys|={norm(s) for s in aliases}
    training=[r for r in rows if r[5].startswith('_iblrig_tasks_trainingChoiceWorld')]
    candidates=[r for r in training if norm(r[1]) not in keys]
    assert not any(r[0] in oldeids for r in candidates)
    groups=defaultdict(list)
    for r in candidates:groups[r[1]].append(r)
    # Project only object metadata; qc/performance values are not selected.
    objects=c.execute("SELECT s.id,s.subject,s.lab,s.date,s.number,s.task_protocol,s.projects,d.rel_path,d.id,d.file_size,d.hash,d.default_revision,d.\"exists\" FROM s JOIN d ON s.id=d.eid WHERE s.task_protocol LIKE '_iblrig_tasks_trainingChoiceWorld%' AND (d.rel_path LIKE '%_ibl_trials.table%.pqt' OR d.rel_path LIKE '%_ibl_trials.choice%.npy' OR d.rel_path LIKE '%_ibl_trials.contrastLeft%.npy' OR d.rel_path LIKE '%_ibl_trials.contrastRight%.npy' OR d.rel_path LIKE '%_ibl_trials.feedbackType%.npy' OR d.rel_path LIKE '%_ibl_trials.probabilityLeft%.npy' OR d.rel_path LIKE '%_ibl_trials.rewardVolume%.npy') ORDER BY s.subject,s.date,s.number,d.default_revision DESC,d.id").fetchall()
    objects=[r for r in objects if r[1] in groups]
    IO['decoded_metadata_representation_bytes']+=len(json.dumps(objects,default=str).encode())
    bysession=defaultdict(list)
    for r in objects:
        eid,sub,lab,date,num,protocol,project,rel,did,size,md5,default,exists=r
        relp=Path(rel)
        remote=relp.stem+'.'+did+relp.suffix
        url='https://ibl-brain-wide-map-public.s3.amazonaws.com/data/'+f'{lab}/Subjects/{sub}/{date}/{num:03d}/'+str(relp.parent/remote)
        field='table' if '_ibl_trials.table' in rel else relp.name.split('.')[1]
        bysession[eid].append(dict(field=field,dataset_id=did,rel_path=rel,file_size=size,md5=md5,
                                  default_revision=default,exists=exists,url=url))
    out=[];roster=[]
    for sub,rr in sorted(groups.items()):
        assert len(set((str(r[3]),r[4]) for r in rr))==len(rr)
        allrows=[r for r in rows if r[1]==sub]
        assert len(set(r[2] for r in allrows))==1
        first=min(rr,key=lambda r:(r[3],r[4]));last=max(rr,key=lambda r:(r[3],r[4]))
        earlier=[r for r in allrows if (r[3],r[4])<(first[3],first[4])]
        earliest=min(allrows,key=lambda r:(r[3],r[4]))
        prefixes=[]
        complete=True
        for r in rr:
            assets=bysession.get(r[0],[])
            # Preserve every revision; select only one default or unique object per field.
            selected={}
            for field in sorted(set(a['field'] for a in assets)):
                aa=[a for a in assets if a['field']==field and a['exists']]
                defaults=[a for a in aa if a['default_revision']]
                use=defaults if defaults else aa
                if len(use)==1:selected[field]=use[0]
            core={'choice','contrastLeft','contrastRight','feedbackType','probabilityLeft'}
            usable='table' in selected or core<=set(selected)
            complete&=usable
            out.append(dict(eid=r[0],subject=sub,lab=r[2],date=str(r[3]),number=r[4],protocol=r[5],projects=r[6],
                            object_metadata_complete=usable,selected_objects=selected,all_revisions=assets))
            prefixes.append(dict(eid=r[0],date=str(r[3]),number=r[4],protocol=r[5]))
        projects=sorted(set(r[6] for r in rr))
        cohort=('ASD_project' if any('mouseASD' in p for p in projects) else
                'modern_hofer_special_project' if sub.startswith('SWC_AY_') else 'legacy_standard_other')
        roster.append(dict(subject=sub,lab=first[2],cohort=cohort,training_sessions=len(rr),
               first_date=str(first[3]),first_number=first[4],last_date=str(last[3]),
               first_training_protocol=first[5],projects=projects,all_training_core_object_metadata=complete,
               earliest_public_protocol=earliest[5],earliest_public_date=str(earliest[3]),
               earlier_public_protocols=dict(Counter(r[5] for r in earlier)),
               biological_first_exposure_certified=False,stable_session_ids=[r[0] for r in rr]))
    save('CANDIDATE_OBJECTS.json',dict(source='Official global openalyx catalogue pinned in CATALOGUE_EXTRACTION.json',
          payload_values_opened=False,records=out))
    save('CANDIDATE_ROSTER.json',dict(subjects=roster,scope='Metadata candidates only; footer/schema, initial coverage and animal alias qualification still required. Not a funding release.'))
    summary=dict(utc=datetime.now(timezone.utc).isoformat(),
          total_sessions=len(rows),total_subjects=len({r[1] for r in rows}),
          training_sessions=len(training),training_subjects=len({r[1] for r in training}),
          original_names_recovered_by_shared_stable_eid=len(aliases),
          recovered_additional_name_aliases=sorted(aliases-{r['subject'] for r in original}),
          remaining_candidate_subjects=len(roster),candidate_sessions=len(candidates),
          candidate_counts_by_cohort=dict(Counter(r['cohort'] for r in roster)),
          core_object_metadata_complete_by_cohort=dict(Counter(r['cohort'] for r in roster if r['all_training_core_object_metadata'])),
          candidate_counts_by_lab=dict(Counter(r['lab'] for r in roster)),
          primary_unit='one uniquely registered subject, not sessions/trials/particles',
          identity_limit='Global cache has no animal UUID. Official nickname/lab and all stable session UUID exclusions are verified; undocumented subject renaming cannot be ruled out by this cache alone.',
          no_protected_or_new_evaluation_payload=True,io=dict(IO),pins=PINS,
          cpu_seconds=time.process_time()-cpu,process_wall_seconds=time.monotonic()-wall,
          peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save('CATALOGUE_QUALIFICATION.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='pins'},indent=2))


if __name__=='__main__':main()
