# Inspected sources and evidence map — 2026-10-28

This catalog distinguishes public source claims from new calculations. No user writing or motivating essay was used as scientific evidence. The workspace initially held only the charter. The public LOOPER repository was discovered through search, not through unrelated private files. No literature-wide novelty review is claimed.

## Main empirical direction

Full source/provenance table: [social sources](experiments/social_learning/SOURCES.md).

- [Santiago Araújo et al.2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11295924/), DOI10.1098/rsos.240408: inspected §§2.2–2.5, Figure2, §3/Figure3 and discussion. Outcome/inclusion definitions and reported counts checked against actual CSV and Rmd. No mechanistic interpretation accepted by citation alone.
- [Dryad DOI10.5061/dryad.hx3ffbgnr](https://datadryad.org/dataset/doi:10.5061/dryad.hx3ffbgnr): version296766; metadata/codebook inspected. Direct file downloads403/401; metadata saved at data/social_learning/. Public [publisher Figshare collection](https://doi.org/10.6084/m9.figshare.c.7262682), files46746183/46746186, supplied identical CSV and original Rmd. CSV SHA256 matches Dryad; Rmd MD5 matches Figshare/[Zenodo11364554](https://doi.org/10.5281/zenodo.11364554). Raw-source text untouched; precise code locations in independent audit_NOTEBOOK.md. The code-version relationship to the published analysis remains unknown.
- [Nöbel et al.2025](https://www.nature.com/articles/s41598-025-88535-x): inspected introduction final paragraphs and Results/Figure1 on a different long-term-memory paradigm. Provides contrary context to blanket skepticism about all neural social-memory evidence; not an independent replication of conflict order.
- [2021 robustness study](https://www.sciencedirect.com/science/article/pii/S0003347221001068), DOI10.1016/j.anbehav.2021.04.007: publisher search-returned abstract/excerpts inspected; full page403. Contrary outcome with differing line/protocol, not pooled quantitatively here.

## Methodological follow-up

Full precise locations/access limits: [causal sources](experiments/causal_identification/SOURCES.md).

- [Geadah et al., CDC2024 / preprint2025](https://arxiv.org/html/2502.15014v1): §§II-A,II-B Eq10/Figure2,III,V and AppendixA inspected. Established closed-loop parameter ambiguity; their richer inverse-control problem is not reproduced by our example.
- [Ng, Goodwin & Anderson1977](https://doi.org/10.1016/0005-1098(77)90068-1): publisher/institution abstracts only. Positive identifiability results defeat universal impossibility. [NASA TM-107604](https://ntrs.nasa.gov/citations/19920014992) abstract likewise provides known-feedback/excitation context. No unseen theorem invoked.

## Other executed pilots

- Local rules: [source notes](experiments/local_learning/SOURCES.md). Oja1982 publisher abstract; [Chou & Wang1911.02363v2](https://arxiv.org/pdf/1911.02363), §1.1 Definition1.3/Eq1.4, Eq1.5, §3 and AppendixC; [AdaOja1905.12115v2](https://arxiv.org/html/1905.12115v2) §2–2.1.1. Their stationary/unit-sphere theorem assumptions are not imposed on our Gaussian/switching simulations. Full original Oja proof was not accessed. Correlation-based alternatives were read but not implemented.
- Development: [source notes](experiments/development/SOURCES.md). [Bengio et al.2009](https://ronan.collobert.com/pub/matos/2009_curriculum_icml.pdf), pp2–5 §§1,3–5; [Holland1986](https://www.cs.columbia.edu/~blei/fogm/2018F/materials/Holland1986.pdf), printed pp946–949 §§3,4.3. Our synthetic designs do not reproduce their empirical tasks or make child-development claims.
- Worm data: Atanas/Kim2023, DOI10.1016/j.cell.2023.07.035. Open author-deposited paper saved at sources/atanas2023.pdf after PMC browser check/publisher403. [Detailed audit](experiments/development/atanas_source_audit.md): PDF25/e6 preprocessing,28/e9 controls,13–14/4145–46 Figure6 and34/e15 dynamic encoding. Paper inspected/rendered in relevant pages; no raw-image reprocessing performed.
- Data: six baseline JSONs, public [repository commit513782b42ad77e75f35adfbc70064b7418ff674a](https://github.com/vanshkumar/LOOPER-freely-moving-worms/tree/513782b42ad77e75f35adfbc70064b7418ff674a). Selection and per-file Git-blob/SHA256 in experiments/neural_dynamics/selection.json and data/public/manifest.json. These are processed traces, not raw imaging; source-derived encoding annotations not used as truth. Four reserved files were not acquired/opened. Kato .mat absent from this mirror tree; no Kato comparison computed. DANDI000776 metadata inspected(size~1TB) but not downloaded.
- [Brennan et al.2023, PLOS Comput Biol](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1010784): main text on reconstructions, Methods§4 validation inspected. The user's README misidentifies its journal as PNAS; actual publication is PLOS. Public repo documentation/code snapshot in sources/looper_repo/. Our regressions are not a LOOPER replication or refutation.
- [Prichard & Theiler1994](https://arxiv.org/abs/comp-gas/9405002): abstract explicitly distinguishes multivariate cross-correlation preservation. [Theiler et al. long-coherence study](https://arxiv.org/abs/comp-gas/9302003): abstract limitation inspected. [Theiler1992](https://www.sciencedirect.com/science/article/abs/pii/016727899290102S) and surrogate-review abstracts read; full review403. Our independent phases destroy cross-spectra and test a narrower channel-independence null; no nonlinear-dynamics theorem imported.

## Provenance limits

All source summaries identify the material actually inspected, including abstract-only access. Retrieved material was treated as evidence rather than instructions. Source snippets were not ground-truth labels. No comprehensive contrary-literature search, new biological mechanism, or priority claim is made. Exact methods, failed controls and computation logs belong to the investigation notebooks; code/empirical outputs are evidence for campaign findings, not passing software tests alone.
