"""Verify retained feasibility evidence without opening target answer fields."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): os.environ[key]='2'
import datetime as dt
import hashlib
import json
from pathlib import Path
import resource
import numpy as np
from metadata_scan import fields, EXPECTED

ROOT=Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
TASK=ROOT/'lab/tasks/memory-policy-transfer-2026-10-30'
OUT=ROOT/'sources/memory_policy_transfer_2026-10-30'

def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): digest.update(block)
    return digest.hexdigest()

def main():
    checks=[]
    acq=json.loads((OUT/'ACQUISITION.json').read_text())
    fail=json.loads((OUT/'METADATA_FAILED.json').read_text())
    meta=json.loads((OUT/'METADATA.json').read_text())
    co=json.loads((TASK/'COHORT.json').read_text())
    ready=json.loads((TASK/'READINESS.json').read_text())
    audit=json.loads((TASK/'SOURCE_FIELD_AUDIT.json').read_text())
    docs=json.loads((OUT/'DOCUMENT_REQUESTS.json').read_text())
    assert acq['complete'] and acq['bytes_received']==572563931
    assert sha(OUT/'stats-20191220-20200731.tar.gz')==acq['sha256']=='b582da91b05e16dbda0fb14b52118e41b6f0f566a457c8991a0fa2859179c6af'
    checks.append('complete archive bytes independently reread and SHA256-matched')
    assert fail['error']=='Python integer 65536 out of bounds for uint16'
    assert fail['decoded_bytes']+meta['decoded_bytes']==meta['cumulative_archive_decoded_bytes']==7035801600
    checks.append('failed and corrected archive decoding summed exactly')
    assert len(co['source_fit'])==6 and len(co['source_validation'])==2
    assert len(co['targets']['smart'])==10 and len(co['targets']['spaced'])==4
    allhashes=[p['hash'] for p in co['source_fit']+co['source_validation']+co['targets']['smart']+co['targets']['spaced']]
    assert len(allhashes)==len(set(allhashes))==22
    assert all(int(x[:8],16)%8==0 for x in allhashes)
    assert ready['joint_support']['smart']['supported_repeat_rows']==214
    assert ready['joint_support']['spaced']['supported_repeat_rows']==128
    checks.append('frozen cohort disjointness/hash selection and support summaries agree')
    assert audit['source_correct_values_decoded']==9819 and audit['target_correct_or_reply_values_decoded']==0
    source=np.load(OUT/'source_field_audit_answers.npz',allow_pickle=False)
    assert len(source['ordinal'])==9819 and len(np.unique(source['ordinal']))==9819
    assert set(np.unique(source['correct'])) <= {0,1}
    checks.append('only declared source answer array present and internally consistent')
    # Target-answer bytes need not even be valid UTF-8 for metadata projection.
    original=[b'x']*22
    original[6]=b'pseudonymous-user'; original[7]=b'random'; original[8]=b'de'; original[9]=b'B'
    original[12]=b'1.1'; original[13]=b'question'; original[16]=b'time'; original[17]=b'install'; original[19]=b'1'; original[20]=b'0'
    raw=b','.join(original)+b'\r\n'
    poisoned=list(original); poisoned[18]=b'\xff\xfe'; poisoned[14]=b'\xff'; poisoned[15]=b'"opaque,reply"'
    altered=fields(b','.join(poisoned)+b'\r\n'); clean=fields(raw)
    allowed=(6,7,8,9,12,13,16,17,19,20)
    assert [clean[i] for i in allowed]==[altered[i] for i in allowed]
    assert fields(b','.join(b'"'+x+b'"' for x in EXPECTED)+b'\r\n')==EXPECTED
    checks.append('binary CSV metadata survives poisoned correctness/difficulty and quoted reply commas')
    receipt=acq['bytes_received']+sum(d.get('body_bytes') or d.get('conservative_charge',0) for d in docs)
    # Actual public-array readers: cohort_metadata(parts), choose_cohort(sorted),
    # readiness(sorted), source_field_audit(sorted). Verification does not reopen them.
    derived=sum((OUT/x['path']).stat().st_size for x in meta['parts'])+3*(OUT/'metadata_sorted.npy').stat().st_size
    derived+=4*((OUT/'METADATA.json').stat().st_size+(OUT/'selected_users.json').stat().st_size)
    derived+=(OUT/'METADATA.json').stat().st_size+3*(TASK/'COHORT.json').stat().st_size
    original_decoded=meta['cumulative_archive_decoded_bytes']+audit['source_answer_shard_bytes_streamed']
    total_charge=original_decoded+derived+20_000_000
    assert receipt<650_000_000 and total_charge<8_000_000_000
    assert 2+len(docs)==6
    exposure={'requests_attempted':6,'requests_remaining':2,'new_public_receipt_bytes_or_conservative_charge':receipt,
              'compressed_receipt_cap':650000000,'decoded_archive_bytes':meta['cumulative_archive_decoded_bytes'],
              'source_answer_shard_bytes_streamed':audit['source_answer_shard_bytes_streamed'],
              'derived_metadata_read_charge':derived,'extra_documents_and_context_conservative_charge':20000000,
              'total_streamed_decoded_charge':total_charge,'streamed_decoded_cap':8000000000,
              'blind_whole_archive_receipt_authorized':True,'source_correct_values_interpreted':9819,
              'source_people_consumed_for_field_semantics':18,'initial_source_validation_people_also_consumed':2,
              'target_correct_or_reply_values_numerically_interpreted':0,'target_predictions':0,'target_fits':0,
              'auxiliary_exposure':'metadata modes dictionary accidentally rendered; test timestamp/learn binary semantics uncertified; excluded from predictors; no blanket auxiliary-blindness claim',
              'unrelated_protected_payloads_accessed':0,'max_scan_rss_bytes_macos':meta['max_rss_bytes_macos'],
              'one_metadata_storage_correction':True,'no_scientific_recovery_or_source_adequacy_pass_claimed':True}
    (TASK/'EXPOSURE.json').write_text(json.dumps(exposure,indent=2)+'\n')
    checks.append('six-request, compressed-receipt and conservative decoded-read caps respected')
    manifest={}
    excluded={'MANIFEST.json','VERIFY.json','STATE.md'}
    for base in (TASK,OUT):
        for path in sorted(base.rglob('*')):
            if path.is_file() and path.name not in excluded and '__pycache__' not in path.parts:
                manifest[str(path.relative_to(ROOT))]={'bytes':path.stat().st_size,'sha256':sha(path)}
    (TASK/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    result={'passed':True,'checks':checks,'scientific_controls_passed':False,
            'known_effect_null_recovery':'not run because feasibility stopped before fitting',
            'independent_scientific_signoff':False,'target_answers_opened':False,
            'verified_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'manifest_files':len(manifest),
            'max_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (TASK/'VERIFY.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'verification':result,'exposure':exposure},indent=2))

if __name__=='__main__': main()
