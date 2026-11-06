"""Artifact-only numerical verification, source manifest, accounting and figure."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[k]='1'
os.environ['MPLCONFIGDIR']=str(__import__('pathlib').Path(__file__).resolve().parent/'mpl_cache')
import csv,hashlib,json,resource
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from threadpoolctl import threadpool_limits

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]

def read(name):return json.loads((HERE/name).read_text())

def main():
    frozen=read('SOURCE_ONLY_FREEZE.json')
    assert all(hashlib.sha256((HERE/k).read_bytes()).hexdigest()==v for k,v in frozen['files'].items())
    support=read('SOURCE_SUPPORT.json');epi=read('ENDPOINT_CONTROL.json');witness=read('SUPPORT_WITNESS.json');p=read('PRESCRIPTION_CHECK.json');src=read('SOURCE_ANALYSIS.json')
    checks=[]
    for channel,vals in epi['matched_transfer'].items():
        ratios=[]
        for source in (epi['sources'][0],epi['sources'][2]):
            no=[r['effects']['No Jump'][channel] for r in source['people']]
            to=[r['effects']['Jump To'][channel] for r in source['people']]
            ratios.append(sum(to)/sum(no))
        assert abs(ratios[1]-ratios[0]-vals['ratio_shift'])<1e-12
        pred=vals['leave_person_out_predictions']
        mse1=sum((r['observed_jump_to']-r['Tsay_ratio_forecast'])**2 for r in pred)/len(pred)
        mse2=sum((r['observed_jump_to']-r['lab_specific_intervention_forecast'])**2 for r in pred)/len(pred)
        assert abs(mse1-vals['Tsay_transfer_MSE'])<1e-12 and abs(mse2-vals['lab_intervention_MSE'])<1e-12
        checks.append(dict(channel=channel,ratios=ratios,mean_square_errors=[mse1,mse2],passed=True))
    manifests=[]
    for item in support['files']:
        manifests.append({k:item[k] for k in ('local','bytes','sha256','git_blob','n_people','n_exposures')})
    people={s['source']:[r['person'] for r in s['per_person']] for s in src['sources']}
    exposure=dict(created_utc=datetime.now(timezone.utc).isoformat(),
       source_outcomes='Already consumed development before this study. New rereads do not restore validation status.',
       decoded_source_people=people,source_people_count=58,matched_TsayA_Figure3_people_count=38,
       figure4=dict(input_only_people=witness['target_input_only_people'],input_rows_per_person=968,
            randomized_exposures=36288,individual_outcome_numeric_values_decoded=0,outcome_statistics=0,
            physical_csv_reads='Input-only scans/hash passes occurred; full-row outcome strings were discarded before conversion/retention.',
            public_paper_summaries='Exposed before this study; retained as background.'),
       optional210=dict(status='CLOSED; no payload read/hash in this tranche'),
       inherited_motor=dict(ordinary_records=['campaigns/target_event_carryover_2026-10-28/STATE.md',
                'campaigns/target_event_carryover_2026-10-28/provenance/source_manifest.json'],
                consumed_primary=40,consumed_Figure3=18,Figure4_individual_outcomes_unexamined=42,optional_geometry_unexamined=210,
                historical_total_read_bytes='Not certified in the inherited compact records; do not replace with zero or reset. This tranche is additive.'),
       other_protected='Pan20, Flesch81/B2/B20, later HABITS/memory targets and four baseline worms unchanged; closed branches not accessed.',
       source_files=manifests)
    (HERE/'EXPOSURE.json').write_text(json.dumps(exposure,indent=2)+'\n')
    S=sum(x['bytes'] for x in support['files'][:3]);A=support['files'][0]['bytes'];F=support['files'][2]['bytes']
    ledger=[dict(operation='source_support.py initial input/pin pass',passes=1,charge=8*sum(x['bytes'] for x in support['files'])),
            dict(operation='source_analysis.py initial warning pass + explicit contraction correction + final supported-cell metadata pass',passes=3,charge=3*8*S),
            dict(operation='endpoint_control.py',passes=1,charge=8*S),
            dict(operation='measurement_sensitivity.py TsayA+Figure3',passes=1,charge=8*(A+F)),
            dict(operation='support_witness.py Figure4 inputs + pinned artifacts',passes=1,charge=witness['charged_additional_read_decoded_hash_bytes']),
            dict(operation='prescription_check.py artifacts/code',passes=1,charge=2*p['charged_read_decode_hash_bytes'])]
    subtotal=sum(r['charge'] for r in ledger);charged=400000000
    assert subtotal<charged<600000000
    sources=dict(created_utc=datetime.now(timezone.utc).isoformat(),
       reused_pinned_csvs=manifests,
       source_repository_pins=dict(Tsay='xiaotsay2015/target_jump@049a846a4207a8a047a3f336bcf63ce16e550ddf',
                Al_Fawakhiri='kimoli/TaskSuccessImplicitAdapt@40ae8aa7c9302ae12c7973fab4748d003e8fc9db'),
       primary_literature=[dict(url='https://elifesciences.org/articles/39882',title='The influence of task outcome on implicit motor learning',
                inspected='Equation3 and modeling discussion: separate outcome gains on retention/update, freely estimated correction U(e) at fixed clamp.'),
               dict(url='https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1010005',title='Interactions between sensory prediction error and task error during implicit motor learning',
                inspected='Distracted SPE plus linear TE; per-clamp sensory calibration and target-motion gain.'),
               dict(url='https://doi.org/10.1152/jn.00061.2023',title='Exploring the role of task success in implicit motor adaptation',
                inspected='Cached text/source code; target size/jump discrepancy already published, endpoint timing for experiments3/4.')],
       requests=dict(new_open_operations=2,find_operations=4,logical_public_operations=6,
                returned_tool_json_utf8_bytes=69669,charged_new_ingress_bytes=2000000,
                note='Two primary article pages; four bounded find responses on those same pages. Tool backend transfer/requests are unobservable. 2MB conservatively charged; no new raw data acquired.'),
       code_prescription=p['code'],licenses='Tsay article is CC-BY; author CSVs remain under their repository terms. No new redistribution or publication occurred.')
    (HERE/'SOURCE_MANIFEST.json').write_text(json.dumps(sources,indent=2)+'\n')
    # Scientific figure: no Figure4 outcome or summary point is plotted.
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
    fig,ax=plt.subplots(1,2,figsize=(10,3.7),layout='constrained')
    v=epi['matched_transfer']['current_plus_next']
    vals=[v['Tsay_ratio'],v['Figure3_ratio']];cis=[v['Tsay_ratio95'],v['Figure3_ratio95']]
    ax[0].errorbar([0,1],vals,yerr=np.array([[m-ci[0],ci[1]-m] for m,ci in zip(vals,cis)]).T,
                  fmt='o',markersize=7,capsize=4,color='#1f536f')
    ax[0].axhline(1,color='0.75',ls=':');ax[0].set_xticks([0,1],['Tsay A\n20 consumed people','Al-Fawakhiri Fig. 3\n18 consumed people'])
    ax[0].set_ylim(0,1.15);ax[0].set_ylabel('Jump-to / stationary response at 4°')
    ax[0].set_title('A  Matched geometry does not fix the ratio',loc='left',fontsize=11)
    ax[0].text(.04,.05,'Additive endpoint-expression control\nParticipant bootstrap; conditional on archives',transform=ax[0].transAxes,fontsize=8)
    c=np.linspace(0,10.5,250)
    for tau,color in zip((1.,4.,16.),('#b05c26','#246a73','#7d518a')):
        ax[1].plot(c,np.tanh(c/tau)/np.tanh(4/tau),label=f'τ = {tau:g}°',color=color,lw=2)
    ax[1].plot([4],[1],'o',color='black',label='Only source magnitude')
    ax[1].set_xlabel('Clamp magnitude (degrees)');ax[1].set_ylabel('Response / source response at 4°')
    ax[1].set_title('B  Source-equivalent shape alternatives',loc='left',fontsize=11)
    ax[1].legend(frameon=False,fontsize=8)
    for m in (1.75,3.5,5.25,7,8.75,10.5):ax[1].plot([m],[0],marker='|',color='0.5',ms=7)
    fig.savefig(HERE/'source_transfer.png');fig.savefig(HERE/'source_transfer.pdf');plt.close(fig)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    resources=dict(created_utc=datetime.now(timezone.utc).isoformat(),start_utc='2026-10-31T21:20:37.770Z',
       deadline_utc='2026-10-31T22:35:37.770Z',charged_additional_scientific_read_decoded_hash_bytes=charged,
       itemized_scientific_pass_subtotal_bytes=subtotal,
       remaining_conservative_reserve_within_charge_bytes=charged-subtotal,
       charge_policy='Eight full-file equivalents per raw CSV pass cover physical reads, decoding/tokenization/conversion and hashing. Early per-pass artifacts used four; this authoritative additive ledger corrects all such passes upward without editing frozen history. Remaining reserve covers literature response processing, generated artifact reads/hashes, code/doc reads, plot/final checks.',
       itemized=ledger,public_operations=6,charged_new_ingress_bytes=2000000,
       scientific_processes_peak=1,numerical_threads=1,jobs_running=0,
       largest_recorded_successful_process_rss_bytes=max(87834624,peak),
       failures=[dict(kind='pre-tool ordinary-read composition denial',scientific_bytes=0),
                 dict(kind='pre-tool wc on data-format denial',scientific_bytes=0),
                 dict(kind='first source-analysis matmul warnings',retained='SOURCE_ANALYSIS_INITIAL_WARNINGS.json; NUMERICAL_WARNING.md',charged=True)],
       full_raw_source_replay_in_this_tranche=False,
       note='Multiple sequential finite processes, never simultaneous scientific jobs. No automatic continuation; task accounting is not a reset of inherited motor lineage.')
    (HERE/'RESOURCES.json').write_text(json.dumps(resources,indent=2)+'\n')
    verified=dict(created_utc=datetime.now(timezone.utc).isoformat(),freeze_pins_pass=True,
       matched_ratio_and_LOO_loss_checks=checks,warning_correction=witness['numerical_warning_check'],
       additive_generator_controls=witness['additive_endpoint_generator_control'],
       source_support_witness=witness['identification'],figure4_outcome_numeric_values_decoded=0,
       resources_charged_bytes=charged,peak_rss_bytes=peak)
    (HERE/'VERIFICATION.json').write_text(json.dumps(verified,indent=2)+'\n')
    print(json.dumps(dict(verified=True,resources=resources,decoded_source_people=people,figure='source_transfer.png'),indent=2))

if __name__=='__main__':
    with threadpool_limits(limits=1):main()
