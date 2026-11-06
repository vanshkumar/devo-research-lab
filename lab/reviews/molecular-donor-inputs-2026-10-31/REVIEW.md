# Accept the bounded closeout; primary biology remains untested

2026-10-31. Independent reviewer `01a1939b-4d9b-7222-9f01-3ac7b17a1e61`.
Author `01a19384-44c5-7e42-bea7-2022880795eb`; current PI
`01a19361-5b4a-7040-a135-42a2c6f90b29`.

**Decision: accept the numerical/provenance facts and the closed acquisition
attempt. Narrow every unit conclusion to what the saved definitions certify.**
The required cross-species independent-unit/expression/ortholog object was not
certified in this tranche. This does not establish absent datasets, impossible
sample analysis, failed prediction, or absent conserved biology. Do not reopen
acquisition or substitute selected-table scoring.

## Independent reconstruction

I read the author's implementation as documentation, then wrote a separate
offline positional byte provider and scientific checks in [reconstruct.py](reconstruct.py).
No author analysis/helper was imported or executed. Missing cached spans fail;
there is no network fallback. Independent source/HDF5 and human-array outputs
were saved before reading INPUT_AUDIT for comparison. The run completed at
20:19:59 UTC, inside the 20:36:34 UTC deadline.

- All **31 saved response size/SHA256 pairs**, **59 stable author artifact pins**
  and **three human leaf pins** pass. The failed DNS response and unsuccessful
  content attempts remain in the record. Whole-atlas MD5s are publisher
  declarations; this review does not verify whole-file digests.
- Complete ORIGINAL-bundle listings contain five human and two mouse files.
  The human H5AD is **6,639,007,892 bytes**, human snRNA RDS **6,463,103,232**,
  and mouse RDS **4,369,673,011**. The 4,608-byte human README and both requested
  atlas prefixes have recorded HTTP500 responses, corroborated by their saved
  JSON error bodies. Those errors are endpoint observations, not data absence.
- Saved official Cambridge links identify human dataset `a2c833f7-…` and mouse
  `dbb4e1ed-…`. The saved current mouse API identifies collection
  `d86517f0-fa7e-4266-b82e-a521350d6d36`, collection version
  `827c7fc1-0bb1-4988-be1e-7bf93cd5e590`, dataset version
  `2408fb24-d43f-42a2-8962-72ad13b899e8`, and a **3,814,401,380-byte** H5AD.
  The current saved mirror is distinct from the earlier indexed candidate.
- Direct HDF5 decoding, independently of the author's summary, recovers the
  same **18 unique donor category strings: 13 single-run, four composite-run,
  and `pooled`**. The codes dataset schema is **384,925 rows, int8,
  chunks 12,029, gzip**. The reader used 76,996 logical HDF5 bytes from the
  same 13 saved ranges totaling 9,184,724 physical bytes. Codes values,
  category cell counts and mouse expression were not decoded.

Exact identities, checks and values are in [RECONSTRUCTION.json](RECONSTRUCTION.json),
[AUTHOR_COMPARISON.json](AUTHOR_COMPARISON.json), and [INPUT_PINS.json](INPUT_PINS.json).

## Consequential contrary check: does the source define independent animals?

[UNIT_SOURCE_DEFINITIONS.json](UNIT_SOURCE_DEFINITIONS.json) preserves the exact
saved Apollo/DataCite descriptions, CELLxGENE collection description and dataset
metadata. Their description defines an integrated atlas of 384,925 cells and
mentions SmartSeq2/bulk validation; it supplies no run-to-animal map. The API's
`donor_id` enumeration agrees with the 18 directly decoded labels. Its
`batch_condition` explicitly lists **Dataset, Batch_ID and Sample_ID**, which
does not itself define any of them as an independent animal.

Thus the API independently corroborates the label vocabulary, but does not add
the missing biological-unit mapping. A composite run label could represent
multiple runs from one animal, and pooling need not have a one-label-one-animal
interpretation. I do not resolve either possibility from spelling. This defeats
the inference **“18 categories therefore 18 independent mice”** while preserving
the possibility of a valid source-defined design elsewhere. No SRA lookup,
new metadata, category counts or model was used to repair that uncertainty.
There is no finite row/category contradiction here; the conclusion is lack of
certification from these saved definitions, not proof of structural impossibility.

## Human row and gene linkage

The independent join uses only `raw_var.csv`, `peptide_obs.csv` and
`normalization_check_vectors.npz`. All **36,924 feature column_index values equal
their CSV positions**, feature IDs are unique, and all **1,476 metadata row IDs
and barcodes are unique**. Each consumed sparse row has in-bounds, strictly
increasing unique feature indices. The 54-symbol mask is parsed from the
original frozen protocol rather than imported from the author's analysis.

| Source row | Donor | Sample | Non-target stored entries | Non-target count sum |
|---:|---|---|---:|---:|
| 241710 | tzan2 | tzan2_N6.3 | 5,063 | 20,532 |
| 243245 | tzan2 | tzan2_US6.1 | 2,745 | 5,296 |
| 248769 | tzan2 | tzan2_5.1 | 3,998 | 14,808 |
| 317822 | siletti_H18.30.002 | siletti_10X190_5 | 7,543 | 47,196 |
| 334411 | siletti_H19.30.002 | siletti_10X380_5 | 3,920 | 10,414 |
| 335846 | siletti_H19.30.001 | siletti_10X376_6 | 6,693 | 31,064 |

All **29,962 stored non-target entries** are finite positive integers. All six
barcodes/donor/sample/study/cluster joins, entry counts and sums match the
author exactly. Three different samples share tzan2, illustrating why cells,
samples and donors must remain distinct in these actual leaf records.
This is consistency within pinned exports; the old full human source is not
independently re-decoded here. Its source linkage and preprocessing remain
inherited. No one-to-one mouse/human ortholog map is certified by capitalization.

Full raw/index arrays were decoded before masking, including already consumed
receptor values; no pristine status is restored. Only masked values were
summarized. Normalized-X arrays were not read, and no receptor score was computed.

## Limits and disposition

Compatible mouse expression, biological-unit mapping and cross-species
ortholog/processing reconciliation remain uncertified. Target-excluded matching,
training-only normalization, receptor prediction, donor evaluation, known-answer
recovery, shuffled controls and predictive sensitivity are **UNRUN**, not failed
scientific tests. Reused published clusters also retain their conditioning limit.

Charge **89,126,792 additional read/decoded/hash/allowance bytes** against the
100,000,000-byte review cap; additive molecular lineage **603,659,710 bytes**.
The charge includes 39,126,792 instrumented file/hash/text/array/HDF5 bytes plus
50 MB conservative context, decoding, failed-command and closeout allowances;
it is not exact OS metering. Peak scientific-process RSS was **123,551,744 bytes**,
one scientific process/one numerical thread, zero requests and jobs0.
Historical HYPOMAP 3,277,786,552 range bytes and memory 7,774,826,112/8GB lineage
remain separate and unchanged. See [ACCOUNTING.json](ACCOUNTING.json) and
[EXPOSURE.json](EXPOSURE.json).

Bank this independently reconstructed input evidence and preserve the acquisition
stop. Primary molecular prediction remains unresolved. Reallocation and any PI
refresh belong to the current PI; this review commissions no successor and
changes no heartbeat, protected-data restriction, freeze or credit setting.
