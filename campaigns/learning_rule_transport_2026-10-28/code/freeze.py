#!/usr/bin/env python3
"""Create a one-time, outcome-before-validation scientific freeze."""
import datetime as dt
import hashlib,json
from pathlib import Path

C=Path(__file__).resolve().parents[1]


def main():
    p=C/'protocols/FREEZE.json'
    if p.exists():raise RuntimeError('Freeze already exists; preserve it and record an explicit amendment instead')
    paths=[C/'code'/name for name in ['data_io.py','learning_models.py','trainer.py','baselines.py','rollout.py','evaluation.py','run_forecasts.py','uncertainty.py']]
    paths += [C/'artifacts/models'/name for name in ['dnnglm_nested_best.npz','dnnglm32_nested_best.npz','reinforce_nested_stable.npz','reinforce_pure_nested.npz','DEVELOPMENT_MODEL_SPLIT.json','MODEL_SELECTION.json']]
    paths += [C/'artifacts/baselines/nested_growth_bank.npz',C/'artifacts/calibration/CONFIG.json']
    paths += sorted((C/'artifacts/calibration').glob('*_residuals.npz'))
    paths += [C/'protocols/SPLIT.json',C/'data/INDEX.json',C/'data/ROW_COUNTS.json',C/'data/OBJECT_METADATA_EXCEPTIONS.json']
    files=[dict(path=str(x.relative_to(C)),sha256=hashlib.sha256(x.read_bytes()).hexdigest(),bytes=x.stat().st_size) for x in paths]
    prior=[json.loads(l) for l in (C/'protocols/EXPOSURE.jsonl').read_text().splitlines()]
    bad=[e for e in prior if e.get('split') in ('animal_holdout','lab_holdout','external') and e.get('event') in ('open_outcomes','open_prefix_outcomes','open_prefix_only_outcomes','load_processed_outcomes')]
    if bad:raise RuntimeError('Protected outcomes/prefix already opened before this freeze: '+str(bad[:2]))
    f=dict(campaign='learning_rule_transport_2026-10-28',utc=dt.datetime.now(dt.timezone.utc).isoformat(),
       status='frozen_before_source_validation',files=files,
       outcome_exposure_before_freeze='Development only. Original feasibility examples: schema/hash; subsequent trainer checks: inputs only. No source holdout outcomes or external outcomes read.',
       prefix=dict(task_rows=1000,all_omissions_retained=True,dynamic_calibration='three initial GLM coefficients only, prefix-only MAP; fixed update law',
                   persistence='all1000staticN(0,2I)prior',growth='recent500anchored,15source-neighborcurves',engagement='common recent500beta plus development donor exposure changes'),
       forecast=dict(primary_future_trials=3000,secondary_future_trials=[1000,5000],bin_trials=500,particles=512,
                     source_target='40 full-horizon animals (21 animal+19 lab); all48prefix+bin animals in partial-observation sensitivity; all54allocated disposition',
                     future_conditioning='only observed session opportunity boundaries/counts from pinned footers; not calendar/stopping forecast',
                     metrics=['left_high_correct_including_omission_failures','right_high_correct_including_omission_failures','right_choice_share_all_trials','omission_share'],
                     high_contrast_minimum=.5,score='equal-metric/equal-bin marginalCRPS; equal-animal final mean; unbiased MonteCarloU statistic',
                     empty_cells='common observed-definedmask; nonfiniteforecastfatal; no model-dependentabstention',
                     uncertainty='permodelzero-meanresidualscale0/.5/1chosenbydevelopmentleave-one-animal-outCRPS;CONFIGhashfrozen; raw forecasts also reported'),
       models=['dnnglm32','dnnglm','reinforce','reinforce_pure','growth','persistence'],
       published_primary_model='dnnglm32; source-defaultwidth wins nestedconditionalNLL;16-unitcapacity/optimizationchallenge',
       substantive_rule_candidates=['dnnglm32','dnnglm','reinforce','reinforce_pure'],
       conditional_arm='actual preceding choices/rewards; sequentialbinaryresponseNLL valid; conditionalcurve scores only diagnostic, not autonomousjointforecasts',
       source_gate=dict(primary_horizon=3000,full_horizon=True,baselines=['growth','persistence'],
          overall_crps_relative_improvement_at_least=.10,overall_crps_absolute_improvement_at_least=.002,
          high_accuracy_mae_relative_improvement_at_least=.10,high_accuracy_mae_at_most=.15,
          paired_score_evidence='one-sidedbootstraplowerpercentile.00625>0 for both baselines (4candidates*2baselines;approxBonferroni family screen);10000animalresamplesseed891',
          coverage80_range=[.70,.95],coverage80_scope='allfourmarginals and high-contrastmarginals separately',
          lab_aggregate_crps_relative_improvement_at_least=.05,lab_high_accuracy_mae='mustnotworsen',
          each_reserved_lab_mean_score_gain='positive in both Hofer and Witten',
          interpretation='animal bootstrap does not quantify arbitrarynew-lab uncertainty; any earned candidate triggers frozenexternaltest, chosen by sourceCRPS after passing gates'),
       external=dict(status='sealed until sourcegate',strict_animals=20,protocol='fixedfourcontrasts1,.25,.125,.0625;side.5;reward3uL',
          calibration='same1000prefix and frozen source observation mapping; no externalratepath/update law; source discrepancy distribution frozen',
          interpretation='policy/lab/genotype/year/implant/handling bundled; no causal curriculum inference'),
       challenges=dict(source='bothDNNwidths;pureandbaselineRL;MAP/static/zeroinitialization;.8daybreakretention/anchorreset;no-correction/fast/slowpromotion;actualadaptiveinputreplaydiagnostic;raw/calibrateduncertainty;1k/5k;partialfutures;prefixcompetencestrata;cacheleftedge',
          known_answer='fittedtransferlearnerpasses bothtrainers;fixedcompetence/exposuregrowth/changingengagementnulls;hiddeninit;censoring;daybreakandcorrectionmismatch/rescue',
          monte_carlo='512primary; compare1024 onfirst6fullsubjectsbyhash for DNN32,RL,growth; ifanycandidate within.001ofdecisionthreshold rerun1024allfullprimaryanimals; noretuning'),
       amendments_before_validation=[
          'One public KS016cacheobject changed: originaloldMD5notrecovered;currentobjectsize/ETag/SHAindependentlyverifiedbeforeoutcomes; retained.',
          'Externalday0unconditionedA/Bvariants removed usingmetadataonly.',
          'SourcebaselineRL bound saturation justified stable equivalentgainparameterization; pureRL added as canonical control.',
          'DNN16sourcefits500truncation/1000epochs/twoseeds;source-default32capacitychallenge added and completed before sourcevalidation.',
          'Fixedcompetencecontrol exposed initializationprecision difference; persistence now usesall1000prefix withmatchedprior insteadlast500.',
          'Development-only predictivevariance challenge selects permodel0/.5/1zero-meanresidualscale; no source means/ruleschanged.',
          'Independentdesignreview fixednonfiniteforecastabstention andzero-contrast replayhidden-sidecoding beforevalidation.'
       ])
    p.write_text(json.dumps(f,indent=2)+'\n')
    event=dict(utc=f['utc'],event='method_model_forecast_freeze',path=str(p.relative_to(C)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_outcomes_open=False,external_outcomes_open=False)
    with open(C/'protocols/EXPOSURE.jsonl','a') as out:out.write(json.dumps(event,sort_keys=True)+'\n')
    print(json.dumps(event))

if __name__=='__main__':main()
