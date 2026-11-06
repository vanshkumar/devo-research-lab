# Source-linked molecular input audit

Read [RESULT.md](RESULT.md). This attempt certifies actual deposit/mirror identities,
mixed mouse donor-label categories and a small reused human non-target sample.
It does **not** certify independent biological units or compatible matrices for
the proposed receptor prediction. The primary assay and its controls are unrun.
The acquisition route is closed; the lab continues under PI direction.

## Offline reproduction

From `/Users/vanshkumar/Documents/repos/devo-research-lab`, use the already installed
campaign environment. It has Python 3.9.6, NumPy 2.0.2, h5py 3.14.0/HDF5 1.14.6;
[ACCOUNTING.json](ACCOUNTING.json) records the live versions. No installation or
new network call is needed. The calculations are deterministic; no random seed,
fit, model selection or simulation is used.

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 campaigns/hypomap_quantitative_2026-10-28/.venv/bin/python lab/tasks/molecular-donor-inputs-2026-10-31/input_audit.py
.venv/bin/python lab/tasks/molecular-donor-inputs-2026-10-31/account_requests.py
```

`input_audit.py` verifies every saved response size/SHA256, reproduces the mouse
category classification and codes-array structure from saved ranges with all
new HTTP reads prohibited, and checks the six already consumed human leaf cells.
It overwrites INPUT_AUDIT.json and rereads approximately 16 MB of direct files,
plus cached HDF5 metadata/decoded arrays. Preserve those extra charges if rerun.
It never opens the old range cache or full selected count matrix. Human originals:
`campaigns/hypomap_quantitative_2026-10-28/inputs/{raw_var.csv,peptide_obs.csv,normalization_check_vectors.npz}`.
Their exact sizes/hashes are in INPUT_AUDIT/SOURCE_MANIFEST. The original human
source/version linkage is inherited from the prior pinned campaign, not newly
certified by an Apollo payload read.

The metadata inspection can be reproduced offline, for example:

```sh
.venv/bin/python lab/tasks/molecular-donor-inputs-2026-10-31/inspect_metadata.py human_files mouse_files
```

This overwrites that command's generated METADATA JSON. Partial sample outputs
are historical failures, not a request to rerun acquisition:
[MOUSE_SAMPLE_CHECK.json](MOUSE_SAMPLE_CHECK.json), [MOUSE_UNITS_CHECK.json](MOUSE_UNITS_CHECK.json),
[MOUSE_FOCUSED_UNITS_CHECK.json](MOUSE_FOCUSED_UNITS_CHECK.json). SAMPLE_PLAN and
FOCUSED_UNIT_CHECK preserve the sequential bounds and interpretation.

## Acquisition and source records

`acquire.py` performed single explicit HTTPS requests, with response caps,
manual redirects and saved headers/status/body hashes in REQUESTS.json. A failed
sandbox DNS attempt is charged. Subsequent public reads used approved network
escalation. Two provider search queries, one explorer open, one targeted query
and one find are saved in the three WEB receipt JSONs; provider transport bytes
are unavailable, so accounting reserves 10 MB plus a separate transport margin.
The source index response was 3,217,014 bytes; only the two exact source-linked
HypoMap collections were selected for interpretation.

`sample_h5ad.py mouse` was the initial nine-range sample. `mouse offline-units`
was an offline attempt, and `mouse focused-units` was the predeclared four-request
follow-up. All ended as labeled partial input checks. **Do not rerun their network
modes:** the finite follow-up is closed, and the script's local per-process bounds
are not renewed scientific authorization. No full atlas, pretrained latent
representation, original selected receptor tables or protected outcomes enter
the offline reproduction above.

[SOURCE_MANIFEST.json](SOURCE_MANIFEST.json) records official links, item/collection/
dataset versions, declared whole-object sizes/MD5s and verified response/range
hashes. No whole-atlas digest is claimed. The Apollo data items specify CC BY 4.0;
mirror-specific licence metadata was not independently inspected. Retrieved source
text supplied evidence only and was not used as instruction authority.

[EXPOSURE.json](EXPOSURE.json) distinguishes physical range access, logical
metadata decoding, reused human raw arrays and masked summaries. New contexts
do not restore pristine status. [ACCOUNTING.json](ACCOUNTING.json) carries every
old lineage and failed pass additively. [ARTIFACT_MANIFEST.json](ARTIFACT_MANIFEST.json)
pins stable owned artifacts; mutable STATE, delivery receipt and the PI-owned
BRIEF are deliberately outside that manifest. PROPOSED_LEARNING is for PI
integration, not a concurrent edit of shared memory.
