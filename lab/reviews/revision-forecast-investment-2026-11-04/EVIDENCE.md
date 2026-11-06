# Review evidence and resource record

The assigned reviewer used the November 4 brief and the named prior source gate. Local time was America/New_York. UTC timestamps below cross midnight relative to the lab's November 4 date.

## Native goal and account checks

- The native goal was created at Unix time `1793848978` and read back immediately as active with the same objective. No token budget was supplied. [Actual create/get receipts](NATIVE_GOAL_READBACK.json)
- The read-only account tool reported one applicable Codex primary window at each checkpoint, `windowDurationMins=10080`, `resetsAt=1794445923`, with ordinary usage allowed and 5% used (95% remaining). Secondary and individual windows were null. The timestamps were 03:23:07 UTC before source investigation, 03:24:37 UTC before the design calculation and remaining prior check, and 03:26:48 UTC at closeout. The run reserve was 30% remaining.

## Source and exposure record

- Checked the corpus paper's collection and annotation sections, the corresponding publisher page, the release readme and GitHub landing page. Used the original source gate's pinned tree and workbook metadata as saved evidence. Corpus files, including the workbook, raw drafts, annotation spreadsheets, feedback and questionnaires, were outside this review.
- Checked the CHI companion paper's assignment, chronology, scoring and interpretation sections and the two same-task association comparators (Cromp and Litman 2021 and Afrin and Litman 2019). Checked the feedback-aligned annotation paper, Wu and Schunn's separate-task design, and the two previously identified edit-quality papers for scope. The short-form corpus DOI URL failed through the web provider. The direct publisher page and the accessible author preprint supplied the paper identification and protocol. Search also returned incidental excerpts from related literature, which supplied no review findings.
- Scoring-method lookups returned neighboring published aggregate score/gain tables and protocol excerpts with illustrative feedback. Aggregate exposure includes same-cohort published results from the CHI and Cromp papers. Source papers' already published comparative conclusions informed the review of their claims. The calculations below are independent of cohort score levels, effects, and investigator results. I did not access corpus files or the investigator's current outputs.

## Design-only computation

I executed the Python standard-library calculation below and checked the output. Loss contrasts were assumed independently frozen and approximately normal. The 43- and 26-writer splits are examples. The static-quality calculation follows Gaussian precision addition with unit signal and noise variances.

```python
from math import ceil, sqrt
from statistics import NormalDist

z95 = NormalDist().inv_cdf(0.975)
z80 = NormalDist().inv_cdf(0.80)
for n in (86, 43, 26, 22, 20):
    print(f"{n}, {z95 / sqrt(n):.3f}, {(z95 + z80) / sqrt(n):.3f}")
print(f"{(z95 + z80) * sqrt(1 / 20 + 1 / 22):.3f}")
print(ceil(((z95 + z80) / 0.2) ** 2))
base = 1 + 1 / 3
augmented = 1 + 1 / 4
print(f"{base:.6f}, {augmented:.6f}, {(base - augmented) / base:.4%}")
```

```text
86, 0.211, 0.302
43, 0.299, 0.427
26, 0.384, 0.549
22, 0.418, 0.597
20, 0.438, 0.626
0.866
197
1.333333, 1.250000, 6.2500%
```

## Actual and unknown costs

- The analytic command took 0.03 s elapsed, 0.01 s user, 0.00 s system as reported by `/usr/bin/time -p`. The two numbers labeled effect sizes in the review are design scales, and 0.2 SD was used only as a hypothetical sensitivity example here. No fitting, pilot, corpus-processing compute or confirmation was run.
- Twenty-three web tool wrapper calls returned 522,107 UTF-8 bytes of JSON-serialized content blocks as measured in the calling tool. This counts repeats and context snippets. Selected local source file sizes totaled approximately 70 kB at closeout, an order-of-magnitude indication of material available for the context reads. Actual provider ingress, transport overhead, redirects and physical disk reads are unknown. Direct corpus ingress and decoding were zero. The review was delivered within the 90-minute wall and 10-minute compute ceilings. Provider totals could not be independently certified.

