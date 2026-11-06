# Sources and provenance

## Primary data
- Hoxha, Johnson, Zang, Enwereuzor & Urai, *Perceptual decision-making: extending a standardized rodent task to humans*, posted8October2026, [DOI](https://doi.org/10.64898/2026.10.01.755923). Primary API abstract/metadata and author code inspected. Full HTML/JATS returnedHTTP429; full-manuscript inspection and exhaustive novelty verification remain incomplete.
- [Zenodo release23072548](https://zenodo.org/records/23072548), [API record](https://zenodo.org/api/records/23072548). Published trial CSV is134,562,545bytes; acquired MD5`5bc8ccf8bdca2e89fc21d20ffb7c1695` matches declaration; SHA256`45dcce14e30edba5e38eaeaf8c40edb8cd1a0555928070b44779d0d47458bbe9`. See `acquisition/MANIFEST.json` and HTTP headers. The original full file is retained. Metadata44599bytes matches MD5`a1727d5e679bddee93db8d7a6423edfa`, preserved under the original feasibility-source directory.
- Previous discovery exposure is explicitly recorded: bytes0–8191 and first record of subject006, plus participant metadata. This campaign forced006 into development. Input-only schedule extraction preceded the saved split; reserved behavioral values were not analyzed during splitting.

## Task and author processing
- [Task repository pinned47ac8356](https://github.com/cocosys-lab/human_IBL_cursor/tree/47ac8356432972c7e6e5a887f15a7dd2d6c686ad). The authoritative builder is preserved under `sources/human_learning_feasibility_2026-10-28/WIN_cursor_ibl.psyexp`. The generated Python contains stale condition assignment and does not override it.
- [Analysis repository pinned1283c6dd](https://github.com/cocosys-lab/2026-human-ibl-analyses/tree/1283c6ddd61fc17d9065a5b017d0e3cfd17535cb). Seventeen downloaded source files match upstream Gitblob hashes. Preprocessing relabels041B→042, removes incomplete/pilot/repeated sessions and handles cursor samples beyond timeout. No additional performance exclusion is introduced here.
- Independent [source audit](experiments/source_audit/AUDIT.md) reconstructs the teaching package, feedback, timeout, contrast pedestal, sparse protocol history, author exclusions and exact schedule mapping. All80participants match one of ten pinned XLSX arrays;042 uses original sequence1. Exact paths, hashes and URLs are recorded in `experiments/source_audit/sources/manifest.json`.

## Close prior work actually inspected
- Bruijns et al., *Infinite hidden Markov models can dissect the complexities of learning*, Nature Neuroscience29:186–194(2026), [publisher](https://www.nature.com/articles/s41593-025-02130-x). Full primary text inspected. Acquisition/path dependence across134mice and>3200sessions; not these80humans.
- Urai et al., *Choice history biases subsequent evidence accumulation*, eLife8:e46331(2019), [publisher](https://elifesciences.org/articles/46331). Full primary text inspected. Human choice-history effects and individual heterogeneity are established; this campaign does not identify drift-versus-starting-point mechanisms from choices alone.
- Fernandez, Fengler & Urai2025, [DOI](https://doi.org/10.1101/2025.08.22.671879). Abstract and university-mirror search text inspected;62mice with comparison to previous human work. No overlap with this human release identified in that bounded inspection. Complete mirror PDF retrieval timed out.

The inspected author figures already analyze psychometrics, pooled block bias, response/cursor measures and200-trial windows. No exact protected participant/schedule predictive comparison was found in inspected code. We claim a new analysis in this investigation, not established priority or discovery of generic history dependence.

## Reproduction and access limits
Acquisition uses public URLs with preserved checksums; no controlled data, private uploads or external contact. The source audit records a failed sandboxed subprocess-wrapper download and its repair using the existing approved direct curl capability. Access failures were retained, not bypassed. Offline source reconstruction: `.venv/bin/python campaigns/human_learning_routes_2026-10-28/experiments/source_audit/check_inputs.py` from repository root.
