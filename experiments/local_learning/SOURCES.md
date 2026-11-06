# Inspected primary sources — local-learning pilots

Access date: 2026-10-28. Public web retrieval only. No full copyrighted text copied into artifacts.

1. **Oja (1982), Simplified neuron model as a principal component analyzer**, Journal of Mathematical Biology 15, 267–273, DOI [10.1007/BF00275687](https://link.springer.com/article/10.1007/BF00275687). Inspected publisher abstract and metadata: supports the stationary principal-component objective. Full text is subscription-limited there. Public PDF mirrors at math.bu.edu and hasler.ece.gatech.edu were indexed in search but timed out on attempted full retrieval; do not claim to have read the complete original proof.

2. **Chou & Wang (2020), ODE-Inspired Analysis for the Biological Version of Oja’s Rule in Solving Streaming PCA**, [arXiv:1911.02363v2](https://arxiv.org/pdf/1911.02363). Inspected introduction §1.1, printed pp.4–6 (PDF indices 3–5): Definition 1.3, equation (1.4) gives the local update implemented here; equation (1.5) explains the normalized Hebbian comparator. Problem 1.2 assumes stationary independent input on the unit sphere and a positive eigengap. Our Gaussian and switched simulations do not satisfy all theorem assumptions, so their convergence guarantees are not invoked. Also inspected §3 opening and Appendix C discussion of continuous dynamics. Mean-flow calculations in analytical_check.py are derived directly for our covariance, not quoted as an exact stochastic theorem.

3. **Henriksen & Ward (2019), AdaOja: Adaptive Learning Rates for Streaming PCA**, [arXiv:1905.12115v2 HTML](https://arxiv.org/html/1905.12115v2). Inspected §2 objective, §2.1 projected update and §2.1.1 rate-choice discussion. Relevant prior work for the fact that step-size choice is consequential; our pilots neither implement nor evaluate AdaOja, and do not reproduce its empirical comparisons.

4. **Pehlevan, Zhao & Sengupta (2020), Neurons as Canonical Correlation Analyzers**, [Frontiers/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7338892/). Inspected abstract, introduction and §2 equations (1)–(5): prior work offers a compartmental correlation-based alternative to a variance objective. No CCA experiment was run; this is a possible future modeling direction, not evidence that any observed drive uses CCA.

The actual evidence for our numerical claims is the generated CSVs, independent population calculation, stationary controls and held-out seed sensitivity. Source agreement does not substitute for those checks.
