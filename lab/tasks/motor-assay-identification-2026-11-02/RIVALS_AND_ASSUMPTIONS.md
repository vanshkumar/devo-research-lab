# What the extra channels do and do not identify

These are synthetic mathematical witnesses, not fits, measurements of subjects, or claims about the truth of a psychological model. All angles are degrees. The original behavioral target is retained: a signed precursor half-difference, event minus no event, averaged over five subsequent common probes. The reference precursor state X=1.5 is supplied; it is NOT an estimate from the earlier 4-degree programmed precursor. Producing this state and supporting the assumed probe law would themselves need validation.

## First reference and the optimistic identifying case

Let the observable event update be `y_next = alpha_J*x + b*c`, with event J, independently randomized cursor offset c, and common probe multiplier `r=.97`. The five-probe multiplier is `M=(1+r+r^2+r^3+r^4)/5=.941773162`. With `X=1.5`, `b=.2`, `alpha_0=.7` and `delta=.2/(X*M)=.141576909083...`, set `alpha_1=alpha_0+delta`. The signed five-probe curve is `[.21236536,.20599440,.19981457,.19382013,.18800553]`; its mean is exactly .2 by rational arithmetic. The reverse sign is also tested.

In a restricted state model `y_next=a_J*x+b_J*e`, a PERFECT error report `e=-lambda*x` still gives rank one within J. Fixed retention can trade against an event-dependent error gain. `FIRST_CALCULATION.json` verifies this with zero exact residual. Crossing c with precursor sign gives rank two when `e=c-lambda*x` is a known, invariant measurement and x is observed without error. The Gram determinant changes from 0 to 54 in this reference. This is standard identification under supplied measurement assumptions, not a novel result or an earned human assay.

The stronger rival retains known unit response of perceived error to c, shared b, and unit calibration slope of the report under randomized changes in c. It changes the unobserved state-dependent component of error and compensates that change in the report's state-dependent bias. The first, uncentered construction needs a 1.061826818-degree DIFFERENCE between event-condition report biases at the positive precursor. That is not the smallest symmetric bias bound; the next construction computes that bound explicitly.

## A sharp calibration requirement in this affine reference

Two mechanisms have the same observed `alpha_J`, cursor gain b, precursor and complete subsequent behavior. World N has `a_N,J=a_c=.85`; world P has `a_P,J=a_c+s*(2J-1)*delta/2`, with s=+1 or -1. Thus their intrinsic transition contributions differ by exactly s*.2 on the original five-probe scale. Both are stable one-state transitions. For each world w define

```
e_w = c + (alpha_J-a_w,J)*x/b
m_J = (a_N,J+a_P,J)/2
R   = c + (alpha_J-m_J)*x/b
q_w = R-e_w = (a_w,J-m_J)*x/b
```

Then `a_w,J*x+b*e_w` is exactly the same next behavior in both worlds, and `e_w+q_w=R` is exactly the same report. Both worlds pass every randomized c-increment calibration, including at nonzero x: `dR/dc=de_w/dc=1`. A baseline x=0 absolute calibration also passes. Neither calibration bounds the event-by-precursor component q. Separate goal and hand reports can allocate q to the hand report while leaving the goal report identical; this is an explicit report-to-learning-signal alternative, not an allegation of observed subject bias.

The common probe multiplier r is an EFFECTIVE behavioral update, not a claim that no-feedback probes reveal intrinsic retention or stop learning. For example, a world with intrinsic retention fixed globally at a_c can realize that probe law with unobserved perceived correction `e_probe=(r-a_c)*Y/b`; the changed world's baseline retention can be completed analogously. The sharp B bound concerns the index event-by-precursor error reports. No additional validated restriction on a probe's learning-driving signal is silently granted.

The construction has `|q_w|=.265456704531` in each signed precursor/event cell. This radius is sharp within the stated affine, shared-b reference. For any null/changed pair with transition differences d_J, the event difference requires `|d_1-d_0|=delta`, hence `max|d_J|>=delta/2`. If a common report is within B of both true errors, `|e_P-e_N|<=2B`. Combining gives `B>=delta*X/(4b)=.2/(4bM)`. The centered witness attains equality. This is an elementary partial-identification bound, not a global minimum over all assays.

The full crossed mean table is fitted with independent exact two-column normal equations. It recovers the common cursor gain .2, both observable alpha values, report cursor scale 1 and each report state loading. Both mechanistic profiles have zero residual. Treating reports as the true error instead returns the midpoint transition contribution: -.1 or +.1 where the changed world is at -.2 or +.2. Thus an asymptotically shrinking report-as-oracle interval could falsely certify interior equivalence at either boundary. This is an exact bias counterexample, not an estimated finite-sample error rate.

If B bounds absolute error relative to the learning-driving error in EACH signed precursor/event cell, the systematic half-width for the signed five-probe transition scalar is `2bMB`. To make 0 and either signed boundary (±.2) disjoint even at infinite precision requires STRICTLY `B<.265456704531` in this reference. In terms of a bound on the DIFFERENTIAL event report bias, the requirement is `<.530913409061`. The earlier 1.0618 number compares one calibrated world with an uncentered rival; using it as the symmetric tolerance would miss a factor of two. These numerical thresholds depend on supplied b and r. General formulas, not these numbers, transfer to another calibration.

## Forced choice, quantization, noise and report reactivity

A randomized visual probe v with logistic response probability `logistic((e_w+q_w-v)/sigma)` has the same psychometric curve in both worlds, for every v. Randomizing v estimates the report/criterion curve and its slope; it does not by itself show that q is zero or condition invariant. The witness covers the concrete 2AFC alternative as well as numeric reports. It does not say that 2AFC is uninformative for its actual perceptual estimand.

Applying any common quantizer to identical reports preserves equality. The code checks .1-, 1- and 5-degree grids as SUPPLIED sensitivity examples; none is asserted to be a documented resolution of a particular source protocol. Shared conditional observation/process/report noise preserves the full-law equality, including correlated channels. The executed 288 coupled-episode check includes a report-branch behavioral effect and a five-probe trajectory; its maximum numerical discrepancy is 5.56e-16, with zero forced-choice or quantizer mismatches. This is a construction check, not 288 independent experimental units or a power estimate. No heterogeneous-parameter recovery is run: the identity holds conditionally for each admissible parameter value, so integrating the same heterogeneity distribution preserves equality. The fixed homogeneous subcase already defeats a guarantee over a broader class.

Matched report/no-report timing permits a comparison of observable report reactivity. It does not validate the reporting criterion relative to the active learning signal. A common branch-specific update/noise law can be used by both worlds. No claim is made that the methods cause no reactivity or that no-feedback probes cause no learning.

## Biological storage needs a separate anchor

For any behavioral recurrence `Y_next=(a+delta*J)*Y+U`, set `S_next=a*S+U`, `Z_next=(a+delta*J)*Z+delta*J*S`, and `Y=S+Z`. All channels measuring physical behavior, or a context-dependent perception of that behavior, can remain identical while stored S has no J-modulated transition. Heading can eliminate a purely late online endpoint correction, but not this pre-movement expression rival. The code verifies the scalar construction through five common probes.

Robot-matched passive localization supplies a real, different behavioral/perceptual context. Treating it as `L=S+kappa*Z` with KNOWN kappa is an extra measurement restriction. Calibration against actual robot/hand angle does not certify a loading on hypothetical stored S. One admissible unanchored readout has kappa=1; passive context can have a different error/criterion law without affecting active update equivalence. To rule it out requires independently justified cross-context restrictions, not merely another correlated channel.

If an unequal loading WERE known, `S=(L-kappa*Y)/(1-kappa)`. A bias bound B_L on the secondary channel's ALREADY FORMED signed five-probe scalar gives storage-scalar half-width `B_L/|1-kappa|`, even granting perfect Y. Separating 0 and .2 requires `B_L<.1*|1-kappa|`: .1, .05 and .01 degrees for kappa=0, .5 and .9. At kappa=1 no inversion exists. These are hypothetical reference requirements, not source-certified perceptual precision, per-trial bias bounds or sufficient power conditions.

## Statistical and collection implication

For either exact pair, every measurable test has the same rejection probability in both worlds. A size-.05 test therefore cannot have .8 power against its paired rival, at ANY N. A confidence set with 95% coverage in both worlds must contain both target values with probability at least .90 under their common observation law. Bigger N, a stochastic-likelihood estimator, denser probe grids and independent reimplementations cannot replace the missing restriction. No meaningless separating sample size, coverage simulation or oracle recovery is reported.

The two signed precursor states, two events, three offsets and two report branches require 24 episode conditions for ONE within-person factorial repetition. Even before building precursor states, one index reach plus five probes is 144 reaches. A single hand report in each of the 12 report-branch episodes is 12 reports; separate goal reports add 12 reports with unverified timing. Applying the inspected source's hand-report interval increment gives about 10.1 seconds extra, plus about 10.1 seconds of matched waiting in no-report branches. This is a source-specific conditional timing translation, not a session estimate. Precursor acquisition, washout, robot replay, calibration, breaks and goal/2AFC report times are unpriced and not zero. The required number of people and repetitions is NOT identified because the mechanistic pair remains exact. Recommended new people/episodes/reaches/reports under this proposal: zero pending a justified anchor.
