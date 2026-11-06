# Information objects and scope

The source is cocosys-lab/human_IBL_cursor at
47ac8356432972c7e6e5a887f15a7dd2d6c686ad; analysis provenance is
cocosys-lab/2026-human-ibl-analyses at
1283c6ddd61fc17d9065a5b017d0e3cfd17535cb. Reuse the original admitted public
assets and inherited license/provenance limitations. This task performed no
new acquisition or license certification. Paths and freshly verified hashes
are in FIRST_CALCULATION.json, SOURCE_LAW.json and SOURCE_PINS.json.

The generated task at lines4556–4559 chooses
`pregen_sequence_<last participant digit>.xlsx`, with `nReps=1`,
`method='sequential'`, `selection='0:600'`. Builder main-loop parameters agree.
The `seed=None` argument does not randomize a sequential list. Random practice
at lines3696–3700 is a separate handler selecting rows36:41. Main-loop source
lines4597–4602 construct grating contrasts from the row's eccentricity and
contrastDelta, and lines4897/4912 use eccentricity for response correctness.
These are cached code facts, not hardware deployment certification.

Visible signed contrast is `-sign(eccentricity)*contrastDelta/.2`, consistent
with original preprocessing and every actual prefix input. Zero contrast
does not reveal the hidden side. The first two contrast pairs, in table0–9
order, are `(1,.25)`, `(-1,.5)`, `(-.5,1)`, `(-1,.25)`, `(.5,.25)`,
`(-1,-1)`, `(-.25,1)`, `(.5,.5)`, `(-1,-.25)`, `(-.25,.25)`. They are ten
distinct pairs. This result does not require treating exported participant-ID
digits as the actual source mapping; actual visible prefixes identify the
table, including exported042's known remapping. It also does not require
actual feedback, engagement or a distribution over participant IDs.

Let U be the finite set of the ten source files, C the permitted observed
contrast prefix, and S the compatible source index. Each observed C has one
compatible S. Given access to U, the future row sequence is a deterministic
function of C. Every distribution supported on U and giving positive mass to
that prefix therefore has zero conditional entropy for that future sequence.
This is a routine finite-support fact, not a new general information theorem.

A source-defined planned input is legitimate prospective information for an
experimenter. The banked benchmark does not need to pretend the targets were
redrawn during the main task. Conversely, uncertainty in the process that
originally generated the ten saved files does not create fresh target draws
after this prefix identifies a saved file. The brief's desired hidden future
realization is absent under this admitted information set. Withholding U or
disallowing the table lookup would be an additional, separately justified
forecaster restriction; the cached experiment does not mandate it.

The `bias`/probabilityLeft labels describe the supplied schedule and original
scoring windows; they do not certify independent Bernoulli target draws,
switch hazards, a recruitment-ID law or a new intervention. Current visible
stimulus, hidden current target at zero contrast, realized past feedback,
planned future rows and an unknown future teacher are distinct objects.
This pass changes no original fit, coefficient, calibration, split, endpoint,
omission assumption or utility criterion, and makes no new forecasts.
