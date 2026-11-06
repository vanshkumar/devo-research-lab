# Frozen deployment envelope before any biological access

2026-10-29. This executable envelope is a falsification target, not a claim that
the publication pins every deployed mouse's firmware. No parameters are fitted.
The original MT firmware is publication revision8778c33e1e5f1a59fa461fbaa86ed7b8d0e15afb;
its local source SHA256 is8d44a0808ea2405969abbd5845261aeae479cee5fb2f0ca952f64baa3df8c1b4.

## Clock, schema and phase mapping

Each complete newline-terminated row has14fixed integer fields followed by exactly
2*nVisited state/time entries: Unix time, trial number, protocol, rewarded side,
outcome, sample ms, delay ms, early flag, modality, sample index, test index,
psychometric sample/test indices, nVisited. Outcome0is omission,1correct,2error,
3abort. State6/8/9 is correct/omission/error, state11 marks early licking. Checks
must agree with these redundant state fields, preserve every omission and abort,
and require consecutive trial numbers, monotone clock and within-trial times.
The archive must begin at trial1/protocol0. Missing earlier history stops the
route; a filename or a large expanded member is insufficient evidence of origin.

Protocols0and1are both habituation. The first row labeled2is the first complete
post-habituation opportunity. Count all rows labeled>=2, including omissions and
aborts. Stop on the newline of row200, with no request for decoded byte1of201.
History from both habituation phases remains in the prefix and replay.

`UpdateTrialOutcome` increments valid counts for outcomes1/2, logs the current
protocol, then `autoChangeProtocol`, `autoReward`, `trialSelection` run. Phase0
advances after>1000valid responses with<=20early responses in the last100, or
>2000valid. Phase1advances after>2000valid. It resets the phase counter before
selection. Consequently the last phase1response is the teacher's first accepted
update when it advances into2; initialization at the first phase2row would lose
that update. Phase2advances only after>2000valid responses, so this200opportunity
prefix cannot reach phase3 through the published executable chronology.

## Six early deployment alternatives, declared before comparison

Each combines one of two initialization states with one of three restart
prescriptions. All are evaluated and reported, including rejected variants.

1. Published modelparam load: theta/m=0, t=0, alpha=.01, beta=0, L1=0,
   Gamma=.03, Eta=1, S0=[-1,-.5,0,.5,1]. Alternatively, a modelparam read failure
   retains the compiled live S0[1]=+.5. Behavioral paraS otherwise uses the
   published initialization, including its initial100history entries.
2. No reload after initial setup; warm resume at every observed intertrial gap
   >=1800seconds; or reboot/reload at every such gap. No arbitrary per-trial
   intervention or fitted reset time is allowed. This is a finite sensitivity
   envelope for credible pauses, not proof that all actual pauses are observable.
   A short-gap hidden replacement that is necessary for replay retires this route.

The source live model updates on accepted responding, non-probe observations;
the cache copies only on even accepted-update t. Selection computes some terms
from the cache but its probability calls read live theta. Reload parses saved
theta/m to four decimal places; persisted performance EMAs also use four decimals.
Warm resume retains the cache and already selected next pair. Reboot resets the
cache, including its compiled+.5encoding, and starts the first resumed pair at
the compiled(0,0), side1; that single boundary must match this explicit rule.
Only the initial first trial has no preceding pair prediction. There are no
post-hoc boundary exemptions, parameter swaps or per-trial exceptions.

Habituation mode1resamples uniformly among20unequal pairs after a correct outcome,
and otherwise repeats the pair. Stochastic validation checks this support and
rewarded-side consistency, not random-seed equality. In phases2–4, accepted trials
select the strict row-order argmin using the unchanged C++ functions; omitted,
aborted or probe responses skip fitting and repeat. Every deterministic next-pair
and predicted phase is checked. We require at least one *complete* predeclared
variant to pass, with all alternatives' failures retained. No mixture choosing a
different variant per row is allowed. Host float compilation is not hardware
certification, and no tolerance-based best-pair rescue is allowed.

## Two late-phase alternatives carried into any future design

The source-code deployment keeps adaptive direction selection while uniformly
drawing an adjacent magnitude1–4 in phases5/6; delays are discrete500–1999ms.
Phase6also chooses the psychometric modality with probability1/2and uses the
source psychometric index/reward rule. The Methods deployment uses constant500ms
delay and uniform presentation of the eight adjacent hard pairs during testing.
Both retain the explicitly logged protocol clock and the phase2–4 teacher update.
Together with six initialization/restart alternatives this gives at most12
finite deployments. The early prefix cannot distinguish late deployments; both
must survive as forecast uncertainty. No claim that their intermediate hybrids
are observed, or that an early match certifies unseen firmware, is permitted.

Any later necessity for a third unbounded policy, arbitrary manual substitutions
or an unrecorded phase schedule stops before target futures. Scientific conclusions
must be stable across all retained deployments; disagreement in the investment
decision stops this public-data route. This revision does not fit learners or
authorize subsequent development/calibration.
