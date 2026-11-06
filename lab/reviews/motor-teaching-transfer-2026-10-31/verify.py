"""Artifact-only review verifier. Does not open raw CSVs or execute author code."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent

def read(name):
    return json.loads((HERE/name).read_text())

def main():
    manifest=read('MANIFEST.json');pins=[]
    for name,expected in manifest['files'].items():
        body=(HERE/name).read_bytes()
        pins.append(dict(file=name,pass_=len(body)==expected['bytes'] and hashlib.sha256(body).hexdigest()==expected['sha256']))
    recon=read('RECONSTRUCTION.json');contrary=read('CONTRARY.json');later=read('LATER_PROBE.json')
    support=read('SUPPORT.json');audit=read('COORDINATE_MASK_AUDIT.json');pr=read('PRESCRIPTION.json')
    resources=read('RESOURCES.json');definition=read('SOURCE_DEFINITION_PINS.json');oldpins=read('PINS.json')
    primary=recon['matched']['current_plus_next']
    checks=dict(
        immutable_artifact_pins=all(v['pass_'] for v in pins),
        retained_transition_counts=[s['n_transitions'] for s in recon['sources']]==[14318,14320,13204],
        primary_Tsay_ratio=abs(primary['Tsay_ratio']-.890120458269707)<1e-12,
        primary_Figure3_ratio=abs(primary['Figure3_ratio']-.3430823550232561)<1e-12,
        primary_LOO_gain=abs(primary['paired_MSE_gain']-.7254335511176748)<1e-12,
        saturated_contrasts=recon['max_saved_coefficient_contrast_or_scalar_error']<1e-12,
        source_348_coefficients=audit['max_source_coefficient_error']<1e-12,
        source_174_LOO_losses=audit['max_source_LOO_loss_error']<1e-12,
        literal_and_centered_masks=all(s.get('literal_saved_person_error',0)<1e-12 and s.get('centered_saved_person_error',0)<1e-12 for s in audit['source_audits']),
        common_probe_shift=abs(contrary['stationary_next_endpoint_comparison']['ratio_shift']+.37701542530699805)<1e-12,
        common_probe_interval_spans_zero=contrary['stationary_next_endpoint_comparison']['conditional_bootstrap_shift95'][0]<0<contrary['stationary_next_endpoint_comparison']['conditional_bootstrap_shift95'][1],
        retention_all_full_rank=all(p['full_rank'] for row in contrary['retention_sweep'] for g in row['groups'] for p in g['design']),
        later_h1_reconstructs=abs(later['h1_max_previous_error'])<1e-12,
        transient_later_effects_zero=all(abs(v)<1e-12 for q in later['transient_expression_generator']['expression_component_recovery'] if q['horizon']>1 for v in q['effects'].values()),
        source_formula_SSE=abs(pr['source_SSE']-.094647628262872)<1e-12,
        formula_prediction=abs(pr['Figure3']['predicted_ratio']-.8870543144495924)<1e-12,
        support_ranks=support['rank_witness']==dict(source_base=4,source_with_size=4,target_base=2,target_with_size=3,target_Hit_exposures=12096),
        source_shape_agreement=support['max_source_curve_disagreement']<1e-12,
        target_shape_disagreement=abs(support['max_target_curve_disagreement']-1.350568179446706)<1e-12,
        witness_rows=support['witness_rows']==108 and support['max_author_witness_error']<1e-12,
        Figure4_outcomes_closed=support['target_outcome_numeric_values_decoded']==support['target_outcome_statistics']==0,
        optional210_closed=not support['optional210_opened'],
        prior_freeze_pins=len(oldpins['source_only_freeze'])==13 and all(p['pass_'] for p in oldpins['source_only_freeze']),
        prior_artifact_pins=len(oldpins['stable_author_artifacts'])==36 and all(p['pass_'] for p in oldpins['stable_author_artifacts']),
        original_code_pins=len(definition['original_code_pins'])==7 and all(p['pin_pass'] for p in definition['original_code_pins']),
        timing_order_and_frozen_bytes=all(definition['timing_order_checks'].values()),
        reads_under_allowance=resources['charged_additional_read_decode_hash_bytes']<=resources['review_allowance_bytes'],
        peak_under_limit=resources['successful_peak_RSS_bytes']<resources['RSS_limit_bytes'],
        no_numerical_warnings=all(not w['warnings'] for w in resources['numerical_warnings']),
        offline=resources['review_ingress_bytes']==resources['review_public_requests']==0,
        jobs_zero=resources['jobs_running']==0)
    output=dict(created_utc=datetime.now(timezone.utc).isoformat(),all_pass=all(checks.values()),checks=checks,
                own_artifact_pin_count=len(pins),own_pins=pins,raw_CSVs_opened=0,author_code_executed=False)
    (HERE/'VERIFY.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k!='own_pins'},indent=2))
    assert output['all_pass'], [k for k,v in checks.items() if not v]

if __name__=='__main__':main()
