# Source/protocol/prior manifest

Exactly TWO deliberately targeted empirical primary families were used; no separate methods family. Unrelated results surfaced incidentally in the two source-specific searches; none was deliberately opened or pursued as another empirical lead. Historical natural/variable-tutor ordinary reports were context only; no historical raw data were read.

## Family1 — Zandberg et al.2024 / ML4BL

- Article DOI10.1371/journal.pcbi.1012329, published2024-08-07. Public primary article opened twice through the search connector; no local full-article copy/hash is claimed. Article is CC BY. Protocol distinctions, prior comparison and qualification are in RESULT.md.
- Original dataset DOI10.5281/zenodo.5545872, version1.0/2021-10-02. `source/zenodo_metadata.json` declares CC BY4.0 and49,917,019-byteML4BL_ZF.zip/MD5`87437ef9de328d7981abbf37c0becb50`.
- `source/zip_directory.json` records the1800-entry complete central directory and ZIP offsets/sizes/CRCs. `zip_tail.bin` is the bounded262,144-byte tail. Local metadata and headers were inspected before selecting members.
- `source/README.txt` and `source/Final_probes_20200816.csv` are the only decoded dataset members; each has a `.pin.json` with decoded SHA256, compressed SHA256 and source CRC. Original range responses are retained in `.range`. The README's experiment-exclusion statement requires an explicit filter even though excluded rows remain in the CSV.
- Source units:23retained birds/99bird-aviary-cycles. Stimulus rows are relative AXB categorical choices, all intended probe rewards equal. No delivered reward/acquisition clock/produced-song-quality field is certified. Full eight-item category membership, hardware deployment and supplied training-accuracy computation were not reconstructed.
- GitHub public commit`95293610f8c7052fabe376cda3ce091ea6795cf2`, tree`fc9374057f4059f07a020d4de292fb7638d1f4ff`,2024-06-17. Saved metadata, README and reproduce_embedding_decisions.py are context, not executed source modules. API commit diffs also exposed method/old-notebook code; no author model trained or executed. Git source license contents were not separately retrieved, so no code-license certification beyond the dataset license.
- Closest comparison is in this same primary paper: learned embedding versus calibrated Luscinia and established acoustic tools. Reported results, hyperparameter/consistency filtering and optimistic agreement bound are literature evidence, not this run's model replication.

## Family2 — Carouso-Peck/Goldstein2019

- Article DOI10.1016/j.cub.2018.12.026, Current Biology29:631–636.e3. PubMed primary abstract opened; ScienceDirect full text returned403. The Cornell author-thesis stable bitstream was located by source-specific search, but direct web open failed after an inaccessible signed redirect; only the indexed chapter3protocol excerpt was available. Do not call the full published/deployed protocol independently certified.
- Dataset DOI10.17632/63db6zc5fm.2, Mendeley version2, published2018-12-05, CC BY4.0. Public page/embedded metadata retained in `source/social_page.html` and `social_embedded_state.json`; public file list in `social_files.json`.
- Original`Supplementary Data 1.xlsx`:33,918bytes, SHA256`2f8142a717bb1199e3a43563d57ef0c016c7a72084b2e2b91ed7be66194ef557`matches source-declared hash. Exact download URL and final redirect are in ACQUISITION/RESOURCES.
- One source sheet,18birds,9brother pairs,206columns. Session markers5/10/15/20/25 and final outcome/aggregate columns do not constitute per-vocalization feedback/correction chronology. First-subject count/proportion mismatch remains unresolved, with exact cells preserved. No group-effect fit or paper-statistic replication.
- Typed OOXML parsing preserves string/error/blank/numeric/formula-cache types and executes no workbook code; no pickle or macro loads, no spreadsheet rewrite/recalculation. The optional Spreadsheets skill file read was denied by the project path guard; this direct source audit does not claim use of its runtime or visual QA.

All source URLs, range headers, actual response bytes, local SHA256 and access failures are recorded by acquire.py in ACQUISITION.json. Web/GitHub provider traffic and complete redirect internals are unknown. Whole-ZIP integrity, whole-protocol deployment, target acceptability, source-to-production transport and scientific novelty remain unearned.
