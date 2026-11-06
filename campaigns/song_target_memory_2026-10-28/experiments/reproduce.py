"""Offline reproduction. --full also repeats the40 network runs (~8wall minutes)."""
from pathlib import Path
import argparse,os,json,subprocess,sys,time,hashlib
from provenance import model_fingerprint
BASE=Path(__file__).resolve().parents[1]

def verify_inputs():
    m=json.loads((BASE/'INPUTS.json').read_text())
    for x in m['files']:
        p=BASE/x['path'];assert p.is_file(),str(p)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],'Changed pinned input: '+str(p)
    return len(m['files'])
def verify_models():
    m=json.loads((BASE/'CACHED_MODELS.json').read_text())
    for name,expected in m['models'].items():
        assert model_fingerprint(BASE/name)==expected,'Changed model cache: '+name
    return len(m['models'])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--full',action='store_true');args=ap.parse_args()
    log=BASE/'logs/reproduction';log.mkdir(exist_ok=True)
    result={'mode':'full' if args.full else 'verify_cached_networks_and_rerun_analyses','inputs_verified':verify_inputs(),'cached_models_verified_before':verify_models(),'stages':[]}
    python=sys.executable
    bundled='/Users/vanshkumar/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
    pdf_python=os.environ.get('PDF_PYTHON',bundled if Path(bundled).exists() else python)
    stages=[('extract_tanaka',python,'experiments/extract_tanaka.py',[]),
      ('table',python,'audits/zhao_source/transcribe_table.py',[]),
      ('digitize',python,'audits/zhao_source/digitize.py',[]),
      ('support_audit',python,'audits/zhao_source/audit_support_bound.py',[]),
      ('roberts_vector',pdf_python,'audits/roberts/extract_figure6.py',[]),
      ('stimulus_design',python,'experiments/intervention_design.py',[]),
      ('empirical',python,'experiments/empirical_summary.py',[]),
      ('empirical_independent',python,'audits/model_audit/check_empirical_bounds.py',[]),
      ('mechanisms_and_recovery',python,'audits/model_audit/run_audit.py',[]),
      ('hvc_kernel',python,'experiments/hvc_model.py',['--verify']),
      ('hvc_independent',python,'audits/model_audit/check_hvc_kernel.py',[]),
      ('hvc_second_independent',python,'audits/zhao_source/audit_hvc_kernel.py',[]),
      ('cooling_calibration',python,'audits/prior_work/calibrate_cooling.py',[]),
      ('recovery_summary',python,'experiments/recovery_summary.py',[])]
    if args.full:stages.append(('hvc_full_suite',python,'experiments/run_hvc_suite.py',[]))
    stages += [('hvc_summary',python,'experiments/summarize_hvc.py',[]),('figure',python,'experiments/figure.py',[])]
    for name,exe,path,extra in stages:
        cmd=[exe,str(BASE/path)]+extra;start=time.monotonic()
        with (log/(name+'.stdout')).open('w') as out,(log/(name+'.stderr')).open('w') as err:
            p=subprocess.run(cmd,stdout=out,stderr=err)
        row={'stage':name,'command':cmd,'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-start}
        result['stages'].append(row);print(json.dumps(row),flush=True)
        (BASE/'REPRODUCTION.json').write_text(json.dumps(result,indent=2)+'\n')
        if p.returncode:raise RuntimeError('failed '+name)
    result['cached_models_verified_after']=verify_models()
    # Scientific invariants, independent of formatting and runtime telemetry.
    e=json.loads((BASE/'outputs/empirical_summary.json').read_text());assert abs(e['rounding_robust_support_gap_ms']-24)<1e-9
    assert e['anonymous_bird_aggregation']['opto']['allocation_count']==315
    a=json.loads((BASE/'audits/model_audit/audit_results.json').read_text());assert a['equivalence']['max_absolute_path_difference']<1e-10
    assert a['information_rank']['endpoint_plus_target_and_motor_probe_rank']==2
    h=json.loads((BASE/'outputs/hvc/SUMMARY.json').read_text());assert h['source_rhythmic_exact_100ms_networks']==6 and h['matched_100ms_exact_100ms_networks']==0
    result['scientific_invariants_pass']=True;result['success']=True
    (BASE/'REPRODUCTION.json').write_text(json.dumps(result,indent=2)+'\n')
    print('All offline stages and scientific invariants passed.')
if __name__=='__main__':main()
