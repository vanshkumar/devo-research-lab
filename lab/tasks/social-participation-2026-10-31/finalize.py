"""Closeout pins, resource allowances and compact decision; no scientific fitting."""
import hashlib
import json
import resource
from datetime import datetime, timezone
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
READS=[]

def read(path):
    path=Path(path)
    assert path.stat().st_size<2_000_000
    b=path.read_bytes()
    READS.append({'path':str(path.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    return b

def load(name):
    return json.loads(read(OUT/name))

def save(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def license_urls(value):
    if isinstance(value,str):
        return [value] if 'creativecommons.org' in value else []
    if isinstance(value,dict):
        return sum((license_urls(v) for v in value.values()),[])
    if isinstance(value,list):
        return sum((license_urls(v) for v in value),[])
    return []

def main():
    schema=load('SCHEMA.json');run=load('RUN.json');check=load('CHECK_RUN.json')
    comparison=load('COMPARISON.json');sensitivity=load('SENSITIVITY.json')
    first=load('FIRST_COURTER_SENSITIVITY.json');controls=load('CONTROLS.json')
    metadata=json.loads(read(ROOT/'data/social_learning/dryad_metadata.json'))
    original_manifest=json.loads(read(ROOT/'data/social_learning/manifest.json'))
    verified=[]
    for item in original_manifest:
        name=item['file']; assert name in ('data_primacy.csv','primacy_bias_script.Rmd')
        b=read(ROOT/'data/social_learning'/name)
        assert hashlib.sha256(b).hexdigest()==item['sha256']
        assert hashlib.md5(b).hexdigest()==item['md5']
        verified.append({'file':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),
                         'md5':hashlib.md5(b).hexdigest()})
    for name,want in check['original_pins'].items():
        assert hashlib.sha256(read(OUT/name)).hexdigest()==want
    artifacts=[]
    ignored={'ARTIFACTS.json','RESOURCES.json','CLOSEOUT.json','DELIVERY_STATUS.json'}
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.suffix in ('.json','.csv','.py','.md') and path.name not in ignored:
            b=read(path)
            artifacts.append({'file':path.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
    source_bytes=next(x['bytes'] for x in artifacts if x['file']=='SOURCE_RESPONSES.json')
    save('ARTIFACTS.json',{'snapshot_utc':datetime.now(timezone.utc).isoformat(),
                           'files':artifacts,'originals_verified_against_saved_manifest':verified,
                           'excluded_dynamic_closeout_files':sorted(ignored)})
    selected=[x for x in comparison['contrasts'] if x['model']=='primacy' and x['baseline'] in ('expression','cancellation')
              and x['metric'] in ('joint','eligible_choice','T_eligible_choice')]
    decisions=[]
    for baseline in ('expression','cancellation'):
        tests=[x for x in selected if x['baseline']==baseline and x['metric'] in ('joint','eligible_choice')]
        decisions.append({'baseline':baseline,'meaningful_joint_and_choice_lead':all(x['gain_nat']>=.01 and x['date_bootstrap_95'][0]>0 for x in tests)})
    now=datetime.now(timezone.utc)
    start=datetime.fromisoformat('2026-10-31T20:35:53.213+00:00')
    deadline=datetime.fromisoformat('2026-10-31T21:50:53.213+00:00')
    assert now<deadline
    failed_check_names=('data/social_learning/data_primacy.csv',
                        'lab/tasks/social-participation-2026-10-31/RUN.json',
                        'lab/tasks/social-participation-2026-10-31/COMPARISON.json',
                        'lab/tasks/social-participation-2026-10-31/PROTOCOL.md',
                        'lab/tasks/social-participation-2026-10-31/FIRST_COURTER_CHECK_PLAN.md')
    failed_check_read=sum(x['bytes'] for x in check['immutable_input_reads'] if x['path'] in failed_check_names)
    charges=[{'category':'Scientific dependency/import reads: failed analyze, successful analyze, failed checks, successful checks',
              'bytes':240_000_000,'basis':'60MB allowance per scientific import pass; exact filesystem/library traffic unavailable'},
             {'category':'Ordinary context, source-code, schema/stdlib and shell-output reads','bytes':20_000_000,
              'basis':'Includes initial truncated whole-record outputs and one necessary LEARNINGS recovery; blocked commands included'},
             {'category':'Generated scientific outputs, hashes and decoded JSON/CSV/rechecks','bytes':30_000_000,
              'basis':'Includes repeated tool reads, numerical-result rechecks and closeout artifact hashing/decoding'},
             {'category':'Closeout standard-library processes/dependencies','bytes':12_000_000,
              'basis':'Two small standard-library passes; no NumPy/SciPy in finalize; remaining administrative reads also covered by context/output categories'},
             {'category':'Public source acquisition/response decoding','bytes':6_000_000,
              'basis':'1MB per logical command; actual saved responses also covered by small-input/output allowances'},
             {'category':'Repeated small immutable-input and failed-pass buffers/rounding','bytes':7_000_000,
              'basis':'Includes all separately recorded application reads below; not added twice'}]
    charged=sum(x['bytes'] for x in charges)
    resources={'task':'social-participation-2026-10-31','owner':'01a193ac-f21a-7b43-8db8-11ecc050d688',
               'START_utc':start.isoformat(),'closeout_utc':now.isoformat(),'deadline_utc':deadline.isoformat(),
               'elapsed_wall_seconds_from_START':(now-start).total_seconds(),
               'public_source_toolcalls':3,'public_source_logical_commands':6,
               'source_commands':'Open PMC11295924, open Dryad, search primacy/courtship; reopen relevant PMC lines, search Monier; open PMC5905535',
               'provider_transport_requests_or_ingress':'not exposed; logical commands counted and conservative allowances used',
               'actual_saved_source_response_bytes':source_bytes,
               'charged_new_ingress_bytes':6_000_000+source_bytes,'new_ingress_ceiling_bytes':30_000_000,
               'read_decode_charge_bytes':charged,'read_decode_ceiling_bytes':350_000_000,
               'read_decode_charges':charges,
               'known_application_read_passes':{'schema_raw_input_bytes':schema['scientific_input_bytes'],
                                               'successful_main_input_bytes':run['scientific_input_read_bytes'],
                                               'failed_checks_input_bytes':failed_check_read,
                                               'successful_checks_input_bytes':check['read_bytes'],
                                               'closeout_input_and_artifact_hash_bytes':sum(x['bytes'] for x in READS)},
               'exact_total_OS_filesystem_or_decoded_memory_bytes':'not measured; conservative charges include known reads and uninstrumented dependency/context/output allowances',
               'recorded_peak_successful_scientific_RSS_bytes':max(schema['peak_rss_bytes'],run['peak_rss_bytes'],check['peak_rss_bytes']),
               'closeout_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'failed_pass_RSS':'not separately sampled; failures were import/serialization stages, successful full-process peaks recorded',
               'max_concurrent_scientific_processes':1,'numerical_threads':1,
               'python_invocations_including_failures_and_closeout':7,
               'failed_passes':['initial analyze import: task inspect.py shadowed stdlib; renamed schema_check.py',
                                'initial checks serialization: NumPy bool; explicit bool cast'],
               'blocked_ordinary_commands':3,
               'dataset_license_urls_from_saved_Dryad_metadata':sorted(set(license_urls(metadata))),
               'historical_exposure':'All462social rows, old conditional/all-mating/weight-family/ABB results remain consumed. No other lineages reset or accessed.',
               'protected_payloads_or_unrelated_raw_inputs_read':0,'originals_changed':False,
               'outside_contact_publication_credits_or_resets':0,'jobs':0}
    assert charged<=350_000_000 and resources['charged_new_ingress_bytes']<=30_000_000
    save('RESOURCES.json',resources)
    common=[{'R':x['R'],'all_six_feasible':x['all_six_feasible'],
             'mean_T_latent_reference_preference':x['mean_T_latent_reference_preference'],
             'max_cell_error':max(y.get('max_cell_error',0) for y in x['contexts'])}
            for x in sensitivity['fitted_P_common_R']]
    closeout={'completed_utc':now.isoformat(),'decisions':decisions,'selected_comparisons':selected,
              'common_R_witness_summary':common,
              'first_courter_independent_compatibility_interval':first['theta_cases'][0]['feasible_theta_interval'],
              'theta_cases':[{'theta':x['theta'],'feasible':x['feasible'],'max_cell_error':x.get('max_cell_error')}
                             for x in first['theta_cases']],
              'first_courter_diagnostic':first['accept_first_wait'],
              'positive_null_controls':[{'true_g':x['true_g'],'fitted_g':x['fitted_g'],
                                         'joint_gain':x['primacy_gain_vs_expression_joint'],
                                         'eligible_gain':x['primacy_gain_vs_expression_eligible']}
                                        for x in controls['synthetic']],
              'original_pins_intact':True,'independent_review_status':'not yet performed',
              'recommendation':'Bank bounded result; fresh independent audit. No archive model repair or new acquisition by this worker.',
              'resources':{k:resources[k] for k in ('elapsed_wall_seconds_from_START','charged_new_ingress_bytes','read_decode_charge_bytes','recorded_peak_successful_scientific_RSS_bytes','jobs')}}
    save('CLOSEOUT.json',closeout)
    print(json.dumps(closeout,indent=2))

if __name__=='__main__':
    main()
