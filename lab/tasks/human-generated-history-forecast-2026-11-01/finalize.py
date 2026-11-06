"""Record-only closeout: pins, environment and cumulative accounting; no science rerun."""
import sys
sys.dont_write_bytecode=True
import hashlib, importlib.metadata, json, platform, resource
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
def main():
    reads=[]
    def read(name):
        b=(HERE/name).read_bytes(); reads.append(dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),charge=3*len(b)))
        return json.loads(b)
    old=read('RESOURCES.json'); first=read('FIRST_CALCULATION.json'); feas=read('FEASIBILITY.json')
    audit=read('FINAL_AUDIT.json'); scores=read('SCORES.json'); meta=read('FORECAST_META.json'); freeze=read('FREEZE.json')
    runs={stage:read(f'RUN_{stage}.json') for stage in ('checks','freeze','forecast','score')}
    resumed_explicit=feas['explicit_read_hash_decode_charge']+audit['explicit_read_hash_decode_charge']+sum(x['explicit_read_hash_decode_charge'] for x in runs.values())
    closeout_charge=sum(x['charge'] for x in reads)
    pins=dict(utc=datetime.now(timezone.utc).isoformat(),scope='Inherited primary source provenance plus newly computed hashes; original134MB object never reopened.',
              task_commit='47ac8356432972c7e6e5a887f15a7dd2d6c686ad',task_url='https://github.com/cocosys-lab/human_IBL_cursor/tree/47ac8356432972c7e6e5a887f15a7dd2d6c686ad',
              analysis_commit='1283c6ddd61fc17d9065a5b017d0e3cfd17535cb',analysis_url='https://github.com/cocosys-lab/2026-human-ibl-analyses/tree/1283c6ddd61fc17d9065a5b017d0e3cfd17535cb',
              original_data_url='https://zenodo.org/records/23072548',
              original_raw_pin_inherited=dict(bytes=134562545,md5='5bc8ccf8bdca2e89fc21d20ffb7c1695',sha256='45dcce14e30edba5e38eaeaf8c40edb8cd1a0555928070b44779d0d47458bbe9',opened_by_this_task=False),
              license_scope='Reuse of previously admitted cached public campaign assets; no new license certification or acquisition. Preserve original SOURCES.md/source-audit limitations.',
              inspected_source_and_cached_data_pins=feas['pins'],first_calculation_pins=first['pins'],frozen_main_pins=freeze['sha256'],forecasts_sha256=meta['forecasts_sha256'],closeout_record_reads=reads)
    (HERE/'SOURCE_PINS.json').write_text(json.dumps(pins,indent=2)+'\n')
    environment=dict(utc=datetime.now(timezone.utc).isoformat(),python=sys.version,platform=platform.platform(),
                     packages={x:importlib.metadata.version(x) for x in ('numpy','scipy','pandas','openpyxl')},numerical_thread_environment='All scientific scripts set OPENBLAS/OMP/MKL/VECLIB/NUMEXPR thread limits to1 before numerical imports.',new_dependencies_installed=False)
    (HERE/'ENVIRONMENT.json').write_text(json.dumps(environment,indent=2)+'\n')
    peak=max(old['peak_successful_science_rss_bytes'],feas['peak_rss_bytes'],audit['peak_rss_bytes'],*(x['peak_rss_bytes'] for x in runs.values()))
    old.update(status='completed_bounded_assignment',live_jobs=0,science_finished_utc=audit['utc'],closeout_utc=datetime.now(timezone.utc).isoformat(),
               cumulative_conservative_booking_bytes=450000000,remaining_read_hash_decode_bytes_at_closeout_booking=50000000,
               explicit_resumed_scientific_read_hash_decode_bytes=resumed_explicit,record_only_closeout_explicit_charge=closeout_charge,
               explicit_first_and_resumed_charge_including_closeout=first['conservative_explicit_read_hash_decode_bytes']+resumed_explicit+closeout_charge,
               final_booking_interpretation='150MB prior inclusive booking retained plus300MB inclusive resumed-work/closeout booking. The resumed booking contains explicit operation charges and a containing allowance for all imports/runtime/ordinary context/output/failure/terminal-read overhead. Not measured physical I/O or a proved upper bound; exact cumulative physical/logical I/O and host/tool peaks remain unknown. No certified complete-I/O cap claim.',
               peak_successful_science_rss_bytes=peak,all_completed_native_scientific_exits=0,
               main_forecasts_saved=True,main_forecasts_saved_utc=meta['utc'],new_scores_computed=True,score_saved_utc=scores['utc'],observation_law_calibrations_executed=1,pre_main_revisions_used=1,
               learning_rule_refits=0,original_model_or_fit_assets_modified=False,
               exposure='All80 human sessions already consumed. This task fully decoded cached39-evaluation23400row and41-development24600row numeric records; first200 evaluation behavior only enters forecasts. All ten sourceXLSX objects hashed/first600rows interpreted; full builder parsed. Original134MB CSV unopened. Later evaluation outcomes only used in postvalidation scoring/audit, never forecast input or omission calibration.',
               science_runtime_seconds_by_command={'first_calculation':first['wall_seconds'],'feasibility':feas['wall_seconds'],**{k:v['wall_seconds'] for k,v in runs.items()},'audit':audit['wall_seconds']},
               explicit_read_hash_decode_by_resumed_stage={'feasibility':feas['explicit_read_hash_decode_charge'],**{k:v['explicit_read_hash_decode_charge'] for k,v in runs.items()},'audit':audit['explicit_read_hash_decode_charge']},
               scientific_goal_complete=False,review_status='No distinct independent review yet; PI decides further investment. Author checks are not independent scientific review.')
    old['failed_passes'].append('Feasibility stdout included verbose embedded source condition arrays and was tool-truncated. Full FEASIBILITY.json preserved. No numerical failure or main forecast/scoring rerun.')
    (HERE/'RESOURCES.json').write_text(json.dumps(old,indent=2)+'\n')
    print(json.dumps(dict(status=old['status'],resumed_explicit_bytes=resumed_explicit,record_only_closeout_explicit_charge=closeout_charge,total_explicit_bytes=old['explicit_first_and_resumed_charge_including_closeout'],conservative_booking_bytes=450000000,peak_successful_science_rss_bytes=peak,environment=environment,science_finished_utc=audit['utc'],jobs=0),indent=2))

if __name__=='__main__': main()
