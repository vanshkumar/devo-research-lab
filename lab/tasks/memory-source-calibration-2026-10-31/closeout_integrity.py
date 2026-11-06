"""Record-only integrity, exposure and conservative ingress-accounting closeout.

Does not open a raw shard/archive, interpret a response NPZ, fit, or score.
"""
import calibrate as c
import hashlib
import io
import zipfile

def main():
    budget=c.Budget()
    fit=budget.j(c.HERE/'SOURCE_FIT.json'); val=budget.j(c.HERE/'SOURCE_VALIDATION.json')
    meta=budget.j(c.HERE/'METADATA_CHECK.json'); initial=budget.j(c.HERE/'INITIAL_FREEZE.json')
    fixed=budget.j(c.HERE/'FIT_FREEZE.json'); audit=budget.j(c.HERE/'NUMERIC_AUDIT.json')
    checks=budget.j(c.HERE/'SYNTHETIC_CHECKS.json'); cache={}; pins=[]
    def read(path):
        if path not in cache: cache[path]=budget.read(path)
        return cache[path]
    for path,record in initial['files'].items():
        actual=hashlib.sha256(read(c.ROOT/path)).hexdigest()
        assert actual==record['sha256']; pins.append({'path':path,'sha256':actual,'unchanged':True})
    for name,sha in fixed['files'].items():
        actual=hashlib.sha256(read(c.HERE/name)).hexdigest()
        assert actual==sha; pins.append({'path':str((c.HERE/name).relative_to(c.ROOT)),'sha256':actual,'unchanged':True})
    # Earlier Budget.read charged compressed NPZ ingress. Correct its missing
    # inflation charge for the two actual load_saved calls (numeric audit and
    # validation). Headers and all decoded arrays are included, without typing
    # those values again here. This correction is conservative and below caps.
    inflation=[]
    for name in ('safe_schedules.npz','fit_answers.npz'):
        raw=read(c.HERE/name)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            n=sum(i.file_size for i in z.infolist())
        for stage in ('numeric_audit.load_saved','validation.load_saved'):
            budget.charge(str((c.HERE/name).relative_to(c.ROOT)),n,'retroactive exact NPZ inflated/header bytes for '+stage)
        inflation.append({'path':name,'decoded_bytes_per_load':n,'loads':2})
    # Opaque output pin; no numerical response array is constructed.
    answer_pin=hashlib.sha256(read(c.HERE/'source_answers_consumed.npz')).hexdigest()
    reads_fit=fit['new_correct_exposure']; reads_val=val['new_correct_exposure']
    assert reads_fit['correct_values_interpreted']==29144 and reads_val['correct_values_interpreted']==6229
    assert val['source_validation_people_consumed']==15 and not val['passed_source_calibration']
    assert meta['candidate_ids']['source_fit'] and checks['all_passed'] and audit['checks_passed']
    assert set(meta['candidate_ids']['source_fit']).isdisjoint(meta['candidate_ids']['source_validation'])
    assert fit['source_validation_answers_interpreted']==0 and val['target_answers_interpreted']==0
    exposure={'utc':c.now(),'source_fit_ids_consumed':75,'source_fit_correct_values_interpreted_this_block':29144,
        'source_validation_ids_consumed':15,'source_validation_correct_values_interpreted_this_block':6229,
        'total_correct_values_interpreted_this_block_including_previously_exposed_values':35373,
        'old_audited_ids_retained_development_exposed':18,'old_audited_ids_in_fit':17,
        'newly_answer_exposed_fit_ids':58,'newly_answer_exposed_validation_ids':15,
        'total_answer_exposed_source_ids_in_lineage':91,
        'primary_validation_rows':485,'primary_validation_ids':10,
        'single_validation_assessment':True,'source_validation_retuned':False,
        'random_arm_code':meta['random_arm_code'],'random_shard_scans':2,
        'compressed_random_shard_ingress_bytes':reads_fit['compressed_bytes']+reads_val['compressed_bytes'],
        'inflated_random_shard_ingress_bytes':reads_fit['inflated_bytes']+reads_val['inflated_bytes'],
        'target_correct_reply_interpreted':0,'real_target_predictions_or_scores':0,
        'target_synthetic_recovery_predictions':0,'nonrandom_shards_opened':0,
        'new_auxiliary_field_values_interpreted':0,'raw_archive_passes':0,'network_or_downloads':0,
        'all_prior_auxiliary_and_summary_exposure_preserved':True,
        'source_answer_output_sha256':answer_pin,'accounting_npz_inflation_correction':inflation,
        'jobs_remaining':0,'shared_or_old_source_files_modified':False,
        'scientific_stop':'failed/imprecise frozen absolute-calibration certification before recovery',
        'unrun':['actual-schedule known-answer recovery','null/boundary false-positive calibration',
            '0.02nat decision sensitivity','1.0logit initialization generator sensitivity','all target-answer/prediction/scoring work'],
        'permissions_note':'Two ordinary missing-name reads and one shell-redirection composition were denied before execution; no guard/configuration changes. Simple permitted validation command succeeded once.'}
    c.writej('EXPOSURE.json',exposure)
    result={'utc':c.now(),'all_frozen_pins_match':True,'pin_checks':pins,'synthetic_checks_passed':checks['check_count'],
        'numerical_audit_passed':audit['checks_passed'],'source_gate_failed_without_retuning':True,
        'primary_gain':val['primary']['gain'],
        'primary_calibration_summary':[{'bias':x['bias']['mean'],'absolute_bias_upper95':x['absolute_bias_upper95'],
            'ece':x['fixed_bin_ece'],'logloss':x['equal_id_logloss'],'brier':x['equal_id_brier']} for x in val['primary']['calibration']],
        'source_repeat_wide_gain':val['all_focal_repeats_diagnostic']['gain'],
        'initialization_primary_gain':{k:v['gain']['mean'] for k,v in val['initialization_sensitivities'].items()},
        'gap_diagnostics':val['gap_category_diagnostics'],
        'counter_lower_bound_perturbed_repeat_gain':val['counter_lower_bound_perturbed_repeat_diagnostic']['gain']['mean'],
        'peak_RSS_limit_check':'All scientific guard checks passed under2GB; exact first-fit peak was overwritten by later per-process accounting. Final validation process recorded112246784bytes; do not call this the lineage peak.',
        'resource_recording_correction':'Added exact decoded NPZ charges omitted by initial compressed-ingress accounting; no cap crossed.'}
    c.writej('FINAL_CHECKS.json',result); budget.save()
    print(c.json.dumps({'all_frozen_pins_match':True,'primary_calibration':result['primary_calibration_summary'],
        'wide_gain':result['source_repeat_wide_gain']['mean'],'initialization_gain':result['initialization_primary_gain'],
        'gap_diagnostics':result['gap_diagnostics'],'missing_lower_perturbed_gain':result['counter_lower_bound_perturbed_repeat_gain'],
        'npz_charge_correction':inflation,'additional_bytes':budget.total,'cumulative_bytes':c.PRIOR+budget.total,
        'science_jobs':0}),flush=True)

if __name__=='__main__': main()
