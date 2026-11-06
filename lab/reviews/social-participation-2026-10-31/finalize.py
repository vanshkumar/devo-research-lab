"""Finite record closeout, stdlib only; no author program execution or new sources."""
import csv
import hashlib
import json
import resource
from datetime import datetime, timezone
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
AUTHOR=ROOT/'lab/tasks/social-participation-2026-10-31'
READS=[]
def read(p):
    p=Path(p);assert p.stat().st_size<2_000_000
    b=p.read_bytes();READS.append({'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()});return b
def load(p):return json.loads(read(p))
def save(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def main():
    # Validate cached provider checksum linkage independently of the author's manifest.
    dryad=load(ROOT/'data/social_learning/dryad_files.json')
    figshare_records=[(name,load(ROOT/'data/social_learning'/name)) for name in ('figshare_data_metadata.json','figshare_supp_metadata.json')]
    # Cached labels/descriptions are swapped: select actual file IDs, not labels.
    csv_matches=[(name,article,f) for name,article in figshare_records for f in article['files'] if f['id']==46746183]
    assert len(csv_matches)==1
    metadata_name,figshare,csv_file=csv_matches[0]
    csvbytes=read(ROOT/'data/social_learning/data_primacy.csv')
    sha=hashlib.sha256(csvbytes).hexdigest();md5=hashlib.md5(csvbytes).hexdigest()
    dryad_text=json.dumps(dryad)
    linkage={'csv_bytes':len(csvbytes),'csv_sha256':sha,'csv_md5':md5,'saved_Dryad_metadata_contains_actual_SHA256':sha in dryad_text,'saved_Dryad_metadata_contains_filename':'data_primacy.csv' in dryad_text,'saved_publisher_metadata_contains_actual_MD5':md5==csv_file['computed_md5']==csv_file['supplied_md5'],'saved_publisher_metadata_contains_file_id':csv_file['id']==46746183,'actual_CSV_metadata_cache':metadata_name,'actual_publisher_file_metadata':csv_file,'publisher_article_license_from_cached_metadata':figshare.get('license'),'metadata_file_label_caution':'The cache named figshare_data_metadata.json contains Rmd46746186 despite its CSV description. Resolve actual files by files[].id/name/size/checksum.','inherited_route':'Dryad DOI10.5061/dryad.hx3ffbgnr/version296766 and publisher file46746183; HTTP route and transport provenance inherited from saved source objects, no new network check','data_license':'The saved actual CSV publisher article declares CC-BY4.0; no separate Dryad license or current remote status newly certified.'}
    assert linkage['saved_Dryad_metadata_contains_actual_SHA256'] and linkage['saved_Dryad_metadata_contains_filename']
    assert linkage['saved_publisher_metadata_contains_actual_MD5'] and linkage['saved_publisher_metadata_contains_file_id']
    save('SOURCE_LINKAGE.json',linkage)
    ledgers=[load(OUT/name) for name in ('READS_RECONSTRUCTION.json','READS_WITNESSES.json','READS_AUDIT.json')]
    tracked=sum(l['read_hash_bytes'] for l in ledgers)+sum(r['bytes'] for r in READS)
    now=datetime.now(timezone.utc)
    started=datetime.fromisoformat('2026-10-31T20:56:10.907+00:00')
    registry=load(ROOT/'lab/registry.json')
    pi=registry['pi']['thread_id'];assert pi=='01a193a5-28db-7091-9095-d9e6398ba951'
    tracked+=READS[-1]['bytes']
    # Manual conservative accounting for this completed execution, not a service
    # or authority to rerun. Imported-library physical bytes are not instrumented.
    charge=145_000_000
    components={'tracked_successful_read_hash_bytes':tracked,'two_failed_witness_pass_data_code_output_allowance_bytes':2_000_000,'five_NumPy_process_import_decode_allowance_bytes':100_000_000,'ordinary_context_source_code_tool_output_and_denied_pass_allowance_bytes':20_000_000}
    components['additional_conservative_margin_bytes']=charge-sum(components.values())
    assert components['additional_conservative_margin_bytes']>=0
    resources={'reviewer_thread_id':'01a193bf-8551-79e3-9fb8-7b342ed7784b','scope':'lab/reviews/social-participation-2026-10-31/','START_utc':started.isoformat(),'deadline_utc':'2026-10-31T21:26:10.907+00:00','closeout_utc':now.isoformat(),'elapsed_seconds_from_START':(now-started).total_seconds(),'limit_seconds':1800,'charged_additional_read_decode_hash_bytes':charge,'read_decode_hash_limit_bytes':150_000_000,'charge_components':components,'charge_interpretation':'Additive conservative charge, not exact physical I/O; includes ordinary orientation before START, imports, repeated/failed passes, outputs, code and remaining report bookkeeping. Successful script byte lists are separately inspectable. No new metering service/infrastructure.','successful_numerical_processes':3,'failed_numerical_processes':2,'numerical_processes_total':5,'failed_stdlib_closeout_processes':2,'execution':'Sequential one process / one numerical thread; declared five numerical-thread environment variables=1; no concurrent jobs. Finalize is stdlib only.','largest_recorded_successful_scientific_peak_RSS_bytes':max(l['peak_RSS_bytes'] for l in ledgers),'RSS_limit_bytes':1_000_000_000,'RSS_limitation':'RSS peaks of the two failed witness passes were not instrumented; do not promote successful-process maxima into an exact overall measured peak. Their finite input/array shapes were the same small bounded constructions.','new_network_requests':0,'new_ingress_bytes':0,'jobs':0,'exposure':{'all_original_rows_already_consumed':462,'new_unique_original_rows':0,'original_CSV_decoding_passes':2,'original_rows_decoded_across_those_passes':924,'own_row_table_decoding_passes_including_failures':3,'own_row_table_interpretations':1386,'protected_or_other_branch_payloads_opened':0,'pristine_holdout':False,'old_findings':'All earlier conditional/all-mating/weight-family/ABB summaries remain consumed; no exposure reset.'},'inherited_author_history':{'additional_read_decode_hash_bytes':315_000_000,'charged_ingress_bytes':6_100_505,'logical_source_commands':6},'author_plus_review_read_subtotal_bytes':460_000_000,'other_lineages':'All earlier social bytes outside this author/review subtotal and all memory/molecular/heat/HYPOMAP/protected lineage records remain unchanged and additive.','prohibited_actions_performed':[],'current_registry_PI':pi,'manual_start_usage':'PI supplied2026-10-31T20:56:10.907Z:52%remaining, primary48%used, secondary unavailable, ordinary allowed; no credits/reset.','shared_records_written':False}
    if (OUT/'RESOURCES.json').exists():
        # A later reproduction must not recast its work as this historical run.
        resources=load(OUT/'RESOURCES.json')
        assert resources['reviewer_thread_id']=='01a193bf-8551-79e3-9fb8-7b342ed7784b'
        assert resources['elapsed_seconds_from_START']<1800
    else:
        assert resources['elapsed_seconds_from_START']<1800
        save('RESOURCES.json',resources)
    save('READS_CLOSEOUT.json',{'reads':READS,'read_hash_bytes':sum(r['bytes'] for r in READS),'closeout_utc':now.isoformat()})
    # Pins cover scoped stable evidence; delivery is dynamic bookkeeping.
    files=[]
    excluded={'ARTIFACTS.json','DELIVERY_STATUS.json','READS_CLOSEOUT.json'}
    for p in sorted(OUT.iterdir()):
        if p.is_file() and p.name not in excluded:
            assert p.stat().st_size<2_000_000
            b=p.read_bytes();files.append({'file':p.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    save('ARTIFACTS.json',{'snapshot_utc':now.isoformat(),'files':files,'excluded_dynamic_files':sorted(excluded),'pins_scope':'Reviewer owned artifacts and unchanged PI BRIEF; author/source pins in SOURCE_EVIDENCE. Final manifest hashing is covered by conservative closeout allowance.'})
    print(json.dumps({'source_linkage':linkage,'elapsed_seconds':resources['elapsed_seconds_from_START'],'charged_read_decode_bytes':charge,'charge_components':components,'largest_recorded_successful_RSS_bytes':resources['largest_recorded_successful_scientific_peak_RSS_bytes'],'review_artifact_pins':len(files),'canonical_PI':pi,'jobs':0},indent=2))
if __name__=='__main__':main()
