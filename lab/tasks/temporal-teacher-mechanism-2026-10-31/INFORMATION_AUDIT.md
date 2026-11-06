# What each condition knows

All proposed conditions have the same35sensory tutor renditions and one final sensory observation available. The source synaptic learner uses the35continuous renditions. The readout/template prescriptions use the final clean observation. This is not a claim that each condition makes equal use of every observation, equal parameter counts or equal compute. Every actor has the same3722scalar-feedback query slots, proposal rule, starts and random seed.

| Condition | Target-specific learning | Candidate information | Timing assumption |
|---|---|---|---|
| Raw rate | Source E/I plasticity during35sensory renditions | Full600Eresponse, globally averaged | Fixed2200msepisode and quiet reset; no HVC |
| Normalized rate | Same source plasticity plus a quiet reference | Same response; detected active exposure | Same episode/reset; active auditory boundaries observable |
| Population prototype | Same source plasticity; tutor response means/variances for1200features | Time-pooled first/second coordinate moments of existing recurrent response | Same episode/reset; no externally supplied alignment or new sequence state |
| Unplasticized population | Tutor response prototype on the original circuit; no E/I synaptic tutoring | Corresponding fixed-circuit moments | Same episode/reset; readout still has tutor memory |
| Ordered sensory memory | Means, ordered occurrences, starts and dwell lengths from observable tutor runs | Raw sensory stream | First detectable candidate onset starts the stored relative schedule; no local warp |
| Full sensory template | Stores the observed sensory exemplar | Raw sensory stream | Registers the first sensory onset, with no local warp |
| Static sensory moments | Tutor first/second sensory moments | Time-pooled sensory moments | Order-invariant by construction |
| True-error oracle | Privileged environment truth | True onset-registered waveform error | Diagnostic only; same actor/search budget |

No proposed teacher sees desired motor coordinates, desired permutation, target stretch, the generator's onset variable, or gold error. The environment uses these to produce stimuli and offline tests. The callable critic receives the resulting waveform or its neural response. Code selecting actions constructs the waveform using a fixed plant, but passes only scalar cost back to Actor.tell. The complete query logs are replayed from scalar feedback to verify this separation. Calibration on the tutor waveform is authorized target-specific learning, not outcome-blind source fitting in a biological-data sense.

The ordered memory's occurrence identities are indices of observed runs. It can store two identical emissions at different relative times. That is an explicit sequencing prior, not inference of hidden biological syllable identity. First-onset registration is also a prior about a harmless transformation. One tutor example cannot identify all desired invariances, so the method cannot claim to learn an unrestricted correspondence relation from that example alone.

The population readout minimizes

\[
L(a)=\frac1{1200}\sum_j\frac{(m_j(a)-m_j^{\rm tutor})^2}{v_j^{\rm tutor}+10^{-6}},\qquad
\phi(r)=[r/100,(r/100)^2],\quad m=\langle\phi(r)\rangle_t.
\]

It is nonnegative and the exact clean tutor response has zero cost by construction. Ranking that exact tutor first is therefore a weak result unless wrong candidates remain distinct. Complete acquisition from a different initial motor plan, acquired-content policy tests and noise challenges supply the more informative checks. The finite feature map has no injectivity guarantee. No failure of this readout demonstrates that timing information is absent from the full response.

Static sensory moments commute with a permutation of event order. Recurrent population responses can depend on previous events even when their final readout is pooled in time. Contrasting the two tests whether useful temporal dependence survives in this particular feature code. Contrasting35-rendition versus fixed circuits tests the role of synaptic tutoring conditional on the same prototype readout. Neither comparison identifies a biological neural implementation, and a better fixed-circuit result does not prove that circuit plasticity can never help.

The full template, compressed state and oracle have identical clean objectives on these noise-free, piecewise-constant tutors. The template's equality with the oracle follows because the sensory exemplar supplies the exact reachable target. A claim of added accuracy beyond template matching would be false in this setup. Memory compression is ordinary run-length representation, not a novelty claim.

The assay remains favourable: low-dimensional shared motor coordinates, normalized sensory gain, six fixed production events, target order in a known six-policy subset, finite64policy expansion, long quiet tails, clean tutor, known episode duration and easily detectable silent gaps. The noise challenge perturbs active sensory samples only and tests six-way choices, not full motor acquisition under neural noise or continuous natural song. All whole-case uncertainty refers to synthetic tuples under these restrictions; no new biological experiment or observation supports implementation claims.
