# Original connectome persistence contrast — CLOSE at source gate

This allocation closes before the 2026-11-03T06:13:24Z source deadline. The initial native turn began 05:53:24Z; orientation counts. This is a source/prior/protocol decision, not a numerical finding of absent circuit memory. No main protocol is earned.

## What the named source establishes

Kunert-Graf, Shlizerman, Walker and Kutz, **2017**, “Multistability and Long-Timescale Transients Encoded by Network Structure in a Model of C. elegans Connectome Dynamics,” Frontiers in Computational Neuroscience 11:53, DOI [10.3389/fncom.2017.00053](https://doi.org/10.3389/fncom.2017.00053), is a real primary paper. See saved [methods](sources/article-open.json) and [results/discussion](sources/article-results.json). The article is CC BY.

Its model contains 279 somatic neurons with voltage and synaptic gate variables. Equations 1–4 specify leakage, electrical coupling, chemical synapses and sigmoid gate dynamics:

`C*dV_i/dt = -Gc*(V_i-Ecell) - sum_j Gg_ij*(V_i-V_j) - sum_j Gs_ij*s_j*(V_i-E_j) + Iext_i`;

`ds_i/dt = ar*sigmoid(beta*(V_i-Vth_i))*(1-s_i) - ad*s_i`.

Connectivity is attributed to Varshney2011; neurons otherwise share electrophysiological constants except excitatory/inhibitory assignment. Table1 gives C=1pF, Gc=10pS, individual connection conductance100pS, Ecell=-35mV, inhibitory reversal=-45mV, ar=1/s and ad=5/s. The text says beta=.25/mV while Table1 says .125/mV. This discrepancy is preserved, not resolved by choosing a convenient value. No numerical effect of it was tested.

The central demonstration uses **constant** PLM-pair input2e4 arbitrary units and **constant** ASK-pair input2.4e4. The fixed-point and limit-cycle outcomes share those inputs and differ in initial conditions. The Figure5 ensemble has200 initial conditions near the standard equilibrium per ASK amplitude; the displayed basin grid displaces states only along a small2D motor plane. These are initial-state ensembles and source-supplied basins, not200 independent animals or a transient pulse comparison. The paper already reports convergence on ~10s scales compared with intrinsic ~100–200ms scales. Section2.3 explicitly states that its oscillation does not persist without external input and discusses omitted proprioception.

Its readout is a projection of DB/DD/VB/VD motor voltages onto two modes defined from constant PLM stimulation. The authors explicitly leave the mapping from these neural modes to actual body movement undefined. A projected fixed point is not certified immobility or a behavioral memory state. The study's search does not guarantee it finds every attractor. Do not infer a unique zero-input attractor or impossibility of persistent fixed states from its statement about oscillations.

The main article's discussion identifies perturbations driving state transitions as future work. That makes a carefully defined intervention a possible research question; it supplies neither its finite pulse specification nor a demonstrated material consequence. Within the inspected material there is no earned source-defined post-pulse behavioral protocol, calibrated horizon/readout, or novel distinction beyond known driven multistability/long transients. The supplementary algorithm/figures were not acquired or certified; this is a bounded source assessment, not a claim that no original code or relevant protocol exists anywhere.

## Closest later implementation and why it is not an exact original replay

The second and final deliberately screened primary program was Kim, Leahy and Shlizerman, **2019**, [“Neural Interactome: Interactive Simulation of a Neuronal System”](https://doi.org/10.3389/fncom.2019.00008). Saved [primary methods](sources/interactome-paper.json) and [results](sources/interactome-results.json) verify its public code link,558-variable full-network formulation and interactive constant-current stimulation. Its posterior-touch example uses continuous PLM1.4nA plus AVB2.3nA. It supports user changes and smooth input transitions, but the inspected examples do not give this allocation a defined finite pulse/offset memory assay. Its discussion also leaves musculature/body coupling for later development. No exhaustive later-prior claim is made.

The public repository tree is pinned to `bdb94ca174980e46777f7b1936f539903c688719`. Exact Git-blob matches are independently checked for [README](sources/interactome-README.md), [initialize.py](sources/interactome-initialize.py), and [BSD3 license](sources/interactome-LICENSE). See [SOURCE_AUDIT.json](SOURCE_AUDIT.json). This is release/source evidence, not circuit execution.

The inspected beta release is not silently interchangeable with the2017 prescription. Its code sets inhibitory reversal to-48 rather than-45, ar=1/1.5 and ad=5/1.5 rather than1 and5, and includes other numeric constants whose unit conventions need reconciliation. `transit_Mask` and the RHS recompute input-dependent `Vth`; the renderer uses `500*tanh((V-Vth)/500)`. After the.3s transition window the mask is the new maintained input. This readout is an instantaneous transform of a voltage-minus-threshold quantity, not a validated fluorescence observation filter or a behavior measurement. Threshold recomputation is documented source behavior; this audit does not call it an author error or hidden parameter-learning mechanism.

The tree lists fixed connectivity assets Gg.npy/Gs.npy and emask.npy. None was acquired or decoded. Original2017 connectivity identity, source-defined full initialization/stimulation schedule, exact executable release and independent numerical reference remain uncertified. The repository's saved_dynamics array was also not acquired. We did not install dependencies, launch its web application, port a reduced model, choose random seeds to seek a favorable basin, repair a source chain or run a parameter/time-horizon hunt.

## Decision and what it does not establish

**CLOSE this gate with zero original-full-model runs, zero numerical references and zero persistence contrasts.** Reproducing the already established driven attractors would not supply the material claim requested by the brief. Running a later changed release under an invented pulse/initial state/readout would not fill that gap either. Exact source certification, an independently justified intervention and a meaningful measurable prediction are still missing.

This is not a new failure of either paper, a demonstrated inability of the circuit to store state, a biological absence claim, a novel generic theorem, proof that the release cannot run, or an affordability measurement. Main simulation, accuracy/stability study, freeze/evaluation, consequential result and independent adversarial review are all UNRUN. No review of this source closure is commissioned. No automatic continuation, further release/dependency repair, empirical recording access or protected-target release is requested. Any new allocation belongs to the PI after a separately justified investment and actual usage check. The broader native scientific goal remains unfinished; the same operator goal/heartbeat are unaffected.

Initial failed source pins came from our saved-file newline, not the repository. The exact decoded connector bytes now match all three authoritative Git blobs. The initial check, decoding correction, final check and all access failures survive in [FAILURES.md](FAILURES.md), [SOURCE_AUDIT_INITIAL.json](SOURCE_AUDIT_INITIAL.json), [SOURCE_DECODING.json](SOURCE_DECODING.json) and [NATIVE_EXECUTION.json](NATIVE_EXECUTION.json). Source-audit success is not a substitute for model/reference execution.
