# Source-fixed adviser reliability forecast, version 1

Written after the person3 pilot and metadata-only split, before converting any other person's numerical responses or fitting any forecast. The executable feature definitions and configuration will be pinned with this protocol before source fitting. One scientific development revision remains available; parsing corrections are documented separately.

Question: does a compact nonlinear estimate of relative adviser precision improve a new person's expressed revision forecast beyond current gap/confidence and strong simple feedback/behavior history? The consequence is investment in this particular portable prediction recipe. This is neither a test for absence of human reliability learning nor identification of latent trust.

Source: Zonca et al2026, DOI10.1038/s44271-026-00456-1, original published-linked Experiment1 workbook `jx3fu`, SHA256cbd91790cb21a6a1c1abda7043dfe96bc9a01d0be2ed51c572a523466d937aa9. Source pins, guide and known limitations are in DESIGN_GATE.json. The closest work already describes feedback learning and normative trial-level advice integration; Pescetelli/Yeung2021 already compares trial-level confidence forecasts by correlation. No broad novelty claim is made.

## Units, observations and exposure

Use all47exported two-session completers, including author-excluded25. The absent three noncompleters cannot be restored. No exclusion by supplied influence, final accuracy, keep_trial_angle, gap or final choice. Exact24source/23evaluation IDs in DESIGN_GATE.json come from fixed SHA ranking with pilot3 assigned source. These remain unchanged. Metadata and all XML tokens have been parsed before this split; only person3 numeric responses have been converted/interpreted. Entire workbook acquisition/hash is not untouched acquisition.

Each person has7advisers×54ordered trials. All trials update histories; primary scoring uses trials19–54in every block,252per person. The first18 provide feedback for this question and parallel the published learning allowance, while our response remains the actual angular revision. People are the uncertainty units.

Let wrap(x)=(x+180)mod360−180. At each trial, g=wrap(advice_error−initial_error)/180, y=wrap(final_error−initial_error)/180. Numerical predictions refer to y. Score circular forecast errors wrap(180(y−prediction)) in degrees. The raw signed errors share the correct-direction reference; g/y are invariant to that reference. Current absolute errors, correctness and final response cannot enter the current features. The final response and feedback may update history only AFTER that trial's forecast.

Permitted current inputs: g, own/adviser confidence c_s,c_a in[0,1], own initial RT (log1p RT), trial-in-block, block and session. Histories use preceding ADT responses/confidence/correct direction feedback, reset adviser/own-block history each block; own feedback and behavioral history reset at session changes. IDT practice is unavailable and replaced by explicit generic priors. No agent_type, future rows, supplied optimal prediction, full-record deltas/normalized confidence, final RT or keep/discard flags as predictors.

## Prescriptions

N predicts no revision. F fits one source-only common proportional weight, y=w g (no intercept), as a descriptive fixed-weight reference.

B is ridge on current inputs: g times[1,|g|,|g|²,c_s,c_a,c_s²,c_a²,c_sc_a,log1p(RT),log1p(RT)c_s,t/54,block/7,session−1], plus the fitted intercept.

H augments B with g times simple adviser and own-session feedback moments: cumulative accuracy, confidence, squared error, confidence-adjusted squared error, confidence–accuracy covariance; EWMA accuracy/squared error/adjusted squared error (alpha.2). Cumulative estimates use four pseudo-observations (accuracy/confidence.5, covariance0, squared error900degrees²). Adjusted squared error is e²/rho(c), rho(c)=exp[−2(c−.5)]. Include adviser-minus-self differences of all eight moments interacting with current c_a−c_s, g times own prior proportional-response slopes (current block, session, EWMA), and two current-confidence×past-mean-confidence terms. Slopes use prior sum(g²)=.25 and weight1/3; clip slope estimates to[−2,2]. This alternative has the same primitive feedback information as P and already learns simple reliability and past advice use.

P adds ONE feature to H: g q, where V_j=[(4×900+sum prior e_j²/rho(c_j))/(4+n_j)]rho(current c_j), and q=V_self/(V_self+V_adviser). These are shrunken confidence-adjusted variance indices, not certified Bayesian biological posteriors. No current feedback enters V. The coefficient is learned on source people; no target coefficient fitting. This nonlinear ratio is motivated by precision weighting; its failure would concern this prescription/forecast comparison.

For B/H/P use person-grouped leave-one-source-person-out selection from ridge penalties[.0001,.001,.01,.1,1], minimizing equal-person circular MSE; ties choose the larger penalty within1e−12. Standardization/intercept are estimated inside each fit. Fit final coefficients on all source people with the selected penalty. Every model's predictions are clipped to[−1,1]. Save complete evaluation predictions/features before any evaluation scores.

## Decision and uncertainty

Primary success jointly requires P to reduce equal-person mean circular MSE by at least5%against BOTH B and H; both paired-person5000-resample95%percentile gain intervals have lower bound>0; and P's95%person-bootstrap interval for mean adviser-directed residual lies wholly within±3degrees. Positive P precision-feature coefficient is additionally needed to interpret success as the proposed positive precision weighting. The5%/3degree criteria are investment thresholds (3degrees is30%of the task's10degree accuracy half-width), not a biological equivalence claim. Report MAE, individual gains and bias alongside MSE. Do not substitute an endpoint after evaluation.

Quantify source fitting instability through100source-person bootstrap fits, repeating standardization and grouped penalty selection with all duplicate copies of a person assigned to the same fold. Save fixed-evaluation gains and100paired source/evaluation perturbations. These finite perturbations supplement the conditional original interval; their percentile ranges are not certified coverage.

Known-answer controls:100substantial-signal and100null conditional datasets on the fixed observed feature histories, seeds in config. Refit B/H/P on each source-label simulation and apply the complete decision rule. A null uses source H's conditional mean. Signal adds the P-only precision feature residual after source H projection, scaled to nominal20%oracle MSE advantage under declared noise. Noise combines a person-specific random slope(.5sigma×g) and independent trial noise(sqrt(.75)sigma); sigma is source H's residual RMS. Clip simulated outcomes. Require at least80signal passes and at most5null passes to call this substantial-effect conditional assay discriminating. Report attained oracle gains. Controls do not regenerate feedback/behavior histories or certify5%boundary power, biological generative recovery or interval coverage. Preserve any weakness instead of changing this gate.

Highest-value contrary: compare the same source-fixed recipes on all54trials and with raw mean-squared error on the wrapped revision representation; preserve primary circular scoring. Also evaluate all23leave-one-evaluation-person-out decisions and the source-estimation perturbations. Audit current/suffix information invariance and common-reference rotation invariance. This tests endpoint/leverage/source instability; it does not replace the primary comparison. A distinct reviewer remains necessary after substantive outputs.

No further source family/query is planned. Conservative public-operation charge33/36counts all8web calls'17subcommands,15native request attempts and one blocked inline attempt; the ordinary skill/context denials are separate. Known native ingress is about4.96MB; provider traffic/fanout unknown. Keep conservative ingress/read allowances in RESOURCES, single scientific process/thread, peak<800MB and fixed12:13Zhard stop.
