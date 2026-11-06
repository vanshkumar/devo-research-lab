"""Read-only numerical-output checks plus scoped packaging/resource accounting."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

ROOT=Path(__file__).resolve().parent
PREVIOUS=ROOT.parent/'plasticity-retention-source-benchmark-2026-11-02'


def main():
    started=time.perf_counter()
    license_bytes=(PREVIOUS/'vendor/LICENSE').read_bytes()
    (ROOT/'vendor/LICENSE').write_bytes(license_bytes)
    original=json.loads((PREVIOUS/'SOURCE_MANIFEST.json').read_text())
    source_pins=[]
    exact_reads=len(license_bytes)
    for record in original['files']:
        payload=(PREVIOUS/'vendor'/record['path']).read_bytes()
        exact_reads+=len(payload)
        blob=hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()
        assert blob==record['blob_sha1'],record['path']
        source_pins.append(dict(path=str(PREVIOUS/'vendor'/record['path']),bytes=len(payload),
                                git_blob_sha1=blob,sha256=hashlib.sha256(payload).hexdigest()))
    references=json.loads((ROOT/'REFERENCES.json').read_text())
    summary=json.loads((ROOT/'FULL_SUMMARY.json').read_text())
    audit=json.loads((ROOT/'AUDIT.json').read_text())
    assert all(x['status']=='PASS' for x in (references,summary,audit))
    assert summary['steps_per_neural_arm']=={'sgd':1999999,'cbp':1999999}
    assert summary['cache_online_hits']==996800
    assert summary['total_seconds']<60
    assert audit['independent_full_neural_predictions']==323200
    assert audit['maximum_full_risk_gap']<1e-11
    assert (ROOT/'CLOSE.md').exists() and (ROOT/'PROPOSED_LEARNING.md').exists()
    pins=[]
    for name in ('engine.py','references.py','full_stream.py','audit.py','finalize.py',
                 'CALIBRATION_PLAN.md','AMENDMENT_1.md','REFERENCES.json','FULL_STREAM.json',
                 'FULL_SUMMARY.json','AUDIT.json','PRIOR_GATE.md','CLOSE.md'):
        payload=(ROOT/name).read_bytes()
        exact_reads+=len(payload)
        pins.append(dict(path=name,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest()))
    manifest=dict(utc=datetime.now(timezone.utc).isoformat(),python=sys.version,
                  original_commit='3138c5556859e0e2918d40f113b40699b6575cfa',
                  original_sources_all_12_git_blobs_verified=source_pins,
                  new_provider_transcriptions='SOURCE_MANIFEST.json:3FAIL/requirementsPASS; not raw identity certified',
                  files=pins,packaging_exact_read_bytes=exact_reads)
    (ROOT/'REPRODUCTION_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    public=[
        (1,'exact CVPR2024 title search','provider summary/primary-index exposure'),
        (2,'exact CVF paper PDF','403'),
        (3,'same paper arXiv HTML','v2 primary text success'),
        (4,'pinned CBP JSON via urllib','DNSfailure; later loop requests NOT attempted'),
        (5,'pinned CBP JSON via provider','success; normalized copy hash uncertified'),
        (6,'pinned AdamGnT via provider','success; normalized copy hash uncertified'),
        (7,'pinned requirements via provider','success; Git blob matches'),
        (8,'pinned experiment-grid driver via provider','success; normalized copy hash uncertified'),
        (9,'same paper primary excerpt127','success'),
        (10,'same paper primary excerpt256','success'),
        (11,'same paper primary excerpt296','success'),
        (12,'same paper primary excerpt594','success')]
    now=datetime.now(timezone.utc)
    t_start=datetime.fromisoformat('2026-11-03T01:51:37+00:00')
    max_rss=max(x['max_rss_bytes_macos'] for x in (references,summary,audit))
    max_rss=max(max_rss,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    accounting=dict(
        utc=now.isoformat(),elapsed_including_orientation_seconds=(now-t_start).total_seconds(),
        native_start='2026-11-03T01:51:37Z',
        prior_deadline='2026-11-03T02:11:37Z',reference_deadline='2026-11-03T02:21:37Z',
        full_stream_deadline='2026-11-03T02:31:37Z',decision_deadline='2026-11-03T02:41:37Z',
        hard_deadline='2026-11-03T03:11:37Z',
        new_public_operations=[dict(number=n,operation=o,disposition=d) for n,o,d in public],
        operation_count=12,operation_cap=12,named_programs=2,
        new_ingress_allowance_charge_bytes=100_000_000,new_ingress_cap_bytes=100_000_000,
        actual_provider_redirect_failed_ingress='UNKNOWN; compliance UNCERTIFIED; allowance charged in full',
        additional_read_hash_decode_conservative_charge_bytes=100_000_000,
        additional_read_hash_decode_cap_bytes=1_000_000_000,
        accounted_science_decode_hash_bytes_lower_bound=(references['separate_decoded_read_bytes']*2
            +summary['input_bytes']*3+audit['explicit_read_hash_decode_allowance_bytes']+exact_reads),
        read_charge_includes='orientation/imports/context/source hashes/failed verification/repeated decode/packaging allowance',
        physical_IO_provider_runtime_toolhost_peaks='UNKNOWN',
        measured_science_max_rss_bytes=max_rss,science_rss_cap_bytes=1_000_000_000,
        scientific_processes_simultaneously_max=1,scientific_threads_per_process=1,
        scientific_thread_qualification='standard-library Python, no BLAS/third-party worker pools; OS/runtime threads not metered',
        pre_main_substantive_revisions=1,previous_assignment_revision=1,
        previous_charges_preserved=dict(public_operations=30,ingress_allowance_bytes=58_000_000,
                                       ingress_compliance='UNCERTIFIED',separate_read_bytes=100_000_000,
                                       generated_examples=1_050_000,teacher='seed1729consumed/shared'),
        additive_public_operations=42,additive_ingress_allowance_bytes=158_000_000,
        additive_conservative_separate_read_charge_bytes=200_000_000,
        exposure=dict(new_teacher_generated=0,new_source_examples_generated=0,
                      consumed_realization_read='whole2,731,916byteFULL_REALIZATION;1.01Mfastindices/101contexts/teacher/labels alreadyconsumed',
                      new_full_source_learning_current_examples_per_neural_arm=1_000_000,
                      replay_examples_per_neural_arm=999_999,
                      new_full_source_learning_gradient_steps_total=3_999_998,
                      exact_cache_stream_observations=1_000_000,
                      reference_source_gradient_steps=804,audit_SNP_timing_gradient_steps=20_000,
                      exact_rational_constructed_renewal_cases=4,
                      new_main_or_independent_teacher_evaluation=0,
                      empirical_protected_oldraw_fits_targets=0,
                      saved_exposure='fullriskmatrices/boundaryweights/onlinebins/cachekeys-labels/reservoir and within-worker reconstruction'),
        failures=[
            'pre-registration composed discovery denied; corrected to separate ordinary reads',
            'pre-registration clock denied; no science or writes ran',
            'CVF PDF403 and urllibDNS failure counted as new operations',
            'inline Python verification denied; corrected to owned script',
            'wc on large realization and rg on large registry denied by context ceiling; no payload shown; bounded registry sed succeeds',
            'source copy verifier exit1 twice; first extraction included later provider blocks; corrected extraction, all failed hashes retained',
            'three normalized config/Adam/grid-driver copies still lack original-byte identity; no new source repair after cap'],
        substantive_numerical_failures=0,
        actual_run_receipts=[
            dict(command='references.py',status='nativeexit0',utc=references['utc']),
            dict(command='full_stream.py',session_id=79611,status='nativeexit0',utc=summary['utc']),
            dict(command='audit.py',session_id=26840,status='nativeexit0',utc=audit['utc'])],
        installed_dependencies=0,paid_compute=0,new_native_goal=0,shared_record_writes=0,
        protected_access=0,new_main_campaign=0,distinct_independent_scientific_review='UNRUN',
        terminal_report='pending single send; final disposition in STATE/TERMINAL_REPORT',jobs=0,
        closure='recommendCLOSEthismaincampaign;scientificgoalunfinished;labheartbeatnotchanged')
    (ROOT/'RESOURCES.json').write_text(json.dumps(accounting,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',original_source_pins=len(source_pins),
                          actual_code_output_pins=len(pins),elapsed_seconds=accounting['elapsed_including_orientation_seconds'],
                          measured_science_max_rss_bytes=max_rss,packaging_seconds=time.perf_counter()-started,
                          recommendation='CLOSE',jobs=0)))


if __name__=='__main__':
    main()
