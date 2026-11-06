# Preserved first-pass numerical warning

At 2026-10-31T21:24:02Z, the first source_analysis.py run exited 0 and produced finite results, but NumPy matmul emitted divide/overflow/invalid warnings on small finite matrix-vector contractions at prediction lines109/121. This workspace has previously recorded this behavior. The initial output is preserved as SOURCE_ANALYSIS_INITIAL_WARNINGS.json; it is not the certified final output.

The correction uses explicit einsum contractions, checks every operand/result for finite values, and reruns the affected source calculation. The source CSV rereads are charged again. A separate check compares finite initial/final coefficients, forecasts and model losses. No empirical result is accepted merely because the first process exited0.

An additional reporting correction marks the TsayB success coefficient unidentified: its success design column is identically zero. The minimum-norm zero estimate and tiny bootstrap in the first output were not evidence of absent success effects. Out-of-support TsayB Jump-To/Flicker predictions remain explicitly flagged.

At21:38:21UTC the first artifact-only reproduce.py verification passed, but importing Matplotlib attempted its default cache in the nonwritable home directory and used an allowed temporary cache instead. No raw CSV or scientific result was affected. The verifier now sets MPLCONFIGDIR inside the owned task path, as the figure script already did. The subsequent artifact-only run retained all13pin/scalar checks and emitted no cache warning. These artifact reads remain inside the conservative final accounting reserve.
