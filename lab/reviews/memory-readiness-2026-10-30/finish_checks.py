"""Report one saved candidate and verify input pins; no candidate rerun/answers."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import resource

ROOT=Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
HERE=ROOT/'lab/reviews/memory-readiness-2026-10-30'
TASK=ROOT/'lab/tasks/memory-policy-transfer-2026-10-30'
SRC=ROOT/'sources/memory_policy_transfer_2026-10-30'


def main():
    assert not (HERE/'FINAL_CHECKS.json').exists(), 'one final hash/report pass'
    candidate=json.loads((HERE/'CANDIDATE_READINESS.json').read_text())
    original=json.loads((HERE/'ORIGINAL_AUDIT.json').read_text())
    exposure=json.loads((HERE/'EXPOSURE.json').read_text())
    manifest=json.loads((TASK/'MANIFEST.json').read_text())
    old=json.loads((TASK/'COHORT.json').read_text())
    checks=[]; pins={}; bytes_read=0
    paths=[TASK/n for n in ('ACCESS_PLAN.md','COHORT.json','PROTOCOL.md','READINESS.json','RESULT.md','SOURCE_ACCESS.md','SOURCE_FIELD_AUDIT.json','SOURCE_FIELD_AUDIT_PEOPLE.json','choose_cohort.py','readiness.py','metadata_scan.py')]
    paths += [SRC/n for n in ('metadata_sorted.npy','METADATA.json','selected_users.json','NOTEBOOK_SOURCE.txt')]
    for path in paths:
        digest=hashlib.sha256(); count=0
        with path.open('rb') as stream:
            for raw in iter(lambda:stream.read(1<<20),b''):
                count+=len(raw); digest.update(raw)
        bytes_read+=count
        rel=str(path.relative_to(ROOT)); expected=manifest.get(rel)
        ok=expected is not None and expected['bytes']==count and expected['sha256']==digest.hexdigest()
        checks.append({'name':'original_manifest_pin_'+rel,'passed':ok})
        pins[rel]={'bytes':count,'sha256':digest.hexdigest(),'matches_saved_manifest':ok}
    summary={}
    for group,stats in candidate['cohort'].items():
        people=[p for p in candidate['people'] if p['group']==group]
        stage=Counter()
        for person in people: stage.update(person['item_stages'])
        summary[group]={
            'people':stats['people'],'repeat_rows':stats['repeat_rows'],'unique_items':stats['unique_items'],
            'learner_item_histories':stats['learner_item_histories'],
            'row10_support_percent':100*stats['row10_supported']['repeat_rows']/stats['repeat_rows'],
            'row10_person5_seen_item_support_percent':100*stats['row10_person5_and_seen_source_item_supported']['repeat_rows']/stats['repeat_rows'],
            'possible_gap_overlap_percent':100*stats['possible_gap_overlap']['repeat_rows']/stats['repeat_rows'],
            'enclosed_positive_jump_percent':100*stats['enclosed_positive_jump']['repeat_rows']/stats['repeat_rows'],
            'candidate_people_gap_totals':dict(stage),
            'no_detected_gap_supported':stats['no_detected_gap_supported_row10_person5_and_seen_item'],
            'no_detected_gap_supported_fraction_of_original_candidate':stats['no_detected_gap_supported_row10_person5_and_seen_item']['repeat_rows']/stats['repeat_rows']}
    oldval={p['uid'] for p in old['source_validation']}
    moved=[p for p in candidate['people'] if p['uid'] in oldval]
    checks.append({'name':'both_original_validation_people_forced_to_development_fit','passed':len(moved)==2 and all(p['group']=='source_fit' and p['development_exposed'] for p in moved)})
    checks.append({'name':'229_violations_occur_in10_source_identifiers_not_all18','passed':sum(v>0 for v in original['source_audit_metadata_check']['violations_by_uid'].values())==10})
    # Checked from stored metadata, not source outcome values.
    checks.append({'name':'no_candidate_untouched_validation_is_original_val','passed':all(p['uid'] not in oldval for p in candidate['people'] if p['group']=='source_validation')})
    allpeople={p['uid'] for p in candidate['people']}; groups=[{p['uid'] for p in candidate['people'] if p['group']==g} for g in summary]
    checks.append({'name':'four_candidate_groups_person_disjoint','passed':sum(map(len,groups))==len(allpeople)})
    prior_additional=exposure['review_additional_cached_metadata_document_charge']
    # A further1MB conservatively covers this code, manifest and own result reads.
    additional=bytes_read+1_000_000
    exposure['final_integrity_hash_read_bytes']=bytes_read
    exposure['final_document_read_envelope_bytes']=1_000_000
    exposure['review_additional_cached_metadata_document_charge']=prior_additional+additional
    exposure['new_cumulative_charge']=7351194530+exposure['review_additional_cached_metadata_document_charge']
    checks.append({'name':'additional400MB_cap','passed':exposure['review_additional_cached_metadata_document_charge']<=400000000})
    checks.append({'name':'cumulative8GB_cap','passed':exposure['new_cumulative_charge']<=8000000000})
    exposure['final_hash_process_maxrss_bytes_macos']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    exposure['final_checked_utc']=datetime.now(timezone.utc).isoformat()
    exposure['final_hash_note']='Opaque hashes of specifically allowed cached metadata/documents only; no numerical reread/candidate rerun and no modes/sequence values decoded.'
    (HERE/'EXPOSURE.json').write_text(json.dumps(exposure,indent=2)+'\n')
    (HERE/'INPUT_PINS.json').write_text(json.dumps(pins,indent=2)+'\n')
    (HERE/'FINAL_CHECKS.json').write_text(json.dumps({'checks':checks,'all_passed':all(c['passed'] for c in checks),'check_count':len(checks),'candidate_runs':1},indent=2)+'\n')
    (HERE/'CANDIDATE_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'all_final_checks_passed':all(c['passed'] for c in checks),'checks':len(checks),'source_val_moved_to_fit':len(moved),
       'additional_byte_charge':exposure['review_additional_cached_metadata_document_charge'],'new_cumulative_charge':exposure['new_cumulative_charge'],
       'summary':summary}))


if __name__=='__main__':main()
