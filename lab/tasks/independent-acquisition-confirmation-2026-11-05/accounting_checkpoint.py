"""One checkpoint reduction of actual assignment receipts; not a service."""
from common import *
names=['PREFLIGHT_RESOURCES.json','SEAL_RESOURCES.json','ACQUISITION_FAILURE_0_RESOURCES.json',
    'ACQUISITION_FAILURE_1_RESOURCES.json','COMPATIBILITY_CHECKPOINT_RESOURCES.json']
records=[get(HERE/n) for n in names]
requests=[json.loads(line) for line in read(HERE/'PUBLIC_REQUESTS.jsonl').splitlines()]
decoded=[json.loads(line) for line in read(HERE/'EXPOSURE.jsonl').splitlines()]
fp=get(HERE/'ACCESS_FOOTPRINT.json');success=[r for r in requests if r.get('success')]
assert len(success)==802 and len({r['url'] for r in success})==802
assert {r['url'] for r in success}=={r['url'] for r in fp['objects']}
http=sum(r['received_bytes'] for r in requests);assert http==458383178
storage=sum(p.stat().st_size for p in HERE.rglob('*') if p.is_file())
instrument=receipt('CHECKPOINT_REDUCTION')
cpu=sum(r['cpu_seconds'] for r in records)+instrument['cpu_seconds']
readdecode=sum(r['read_decode_bytes'] for r in records)+instrument['read_decode_bytes']
# HTTP acquisition bytes explicitly charged as reads in addition to local decoder/file reads.
booked=readdecode+http+110000000
out=dict(utc=utc(),status='compatibility_reassessment_required',all_jobs_terminal=True,forecast_jobs_started=0,score_jobs_started=0,
    goal_status='active',actual_remaining_account_percent=65,other_windows='unavailable; not zero',
    stage_receipts=names+['CHECKPOINT_REDUCTION_RESOURCES.json'],
    measured_scientific_cpu_seconds=cpu,uninstantiated_failure_probe_cpu_booking_seconds=3,
    conservatively_counted_booked_cpu_seconds=cpu+3,
    explicit_nominal_decoded_read_bytes=readdecode,public_http_body_bytes=http,
    context_and_uninstrumented_read_booking_bytes=110000000,
    conservatively_counted_booked_read_decode_including_http_bytes=booked,
    peak_measured_RSS_bytes=max(r['peak_rss_bytes'] for r in records+[instrument]),storage_bytes_at_checkpoint=storage,
    acquired_objects=802,acquired_whole_object_rows=fp['whole_decoded_rows'],all_whole_object_fields_acquired=True,
    evaluation_objects_numeric_decoded=11,evaluation_rows_numeric_decoded=sum(r['decoded_rows'] for r in decoded),
    evaluation_numeric_fields=['contrastLeft','contrastRight','choice','feedbackType','rewardVolume','probabilityLeft','intervals_0','intervals_1'],
    decoded_subjects=[r['subject'] for r in decoded],
    exact_acquisition_receipts='PUBLIC_REQUESTS.jsonl',exact_decode_receipts='EXPOSURE.jsonl',
    remaining_initial_cpu_seconds=11100-(cpu+3),remaining_initial_read_decode_bytes=3000000000-booked,
    remaining_http_body_bytes=500000000-http,
    hard_original_initial_stage_deadline_UTC='2026-11-06T00:27:47Z',
    reservations_unspent='Fresh distinct result challenge60CPUmin/2.5h/2GB, one explicitly released useful revision90CPUmin/2h/2GB, closeout10CPUmin/1h/1GB; no borrowing.',
    historical_spent='Source153.361bookedCPU seconds/1,862,357,093read-decode/24,593,242HTTPbytes; fundingreview61.197seconds/116,680,756read-decode/0HTTPbytes. Prior fixedauthor4932.694CPU seconds/723.45MB, resultreview29.043seconds/405.59MB and all older lineage/unknowns remain ADDITIONAL.',
    uncertainty='Physical/provider/import I/O and exact uninstrumented discovery costs unknown. Successful outputs do not certify total resource compliance; context charges are bookings.')
save('RESOURCE_CHECKPOINT.json',out);print(json.dumps(out,indent=2,default=serial))
