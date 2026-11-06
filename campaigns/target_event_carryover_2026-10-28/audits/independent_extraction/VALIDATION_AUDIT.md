# Independent original-byte validation reconstruction

2026-10-28. **PASS: no numerical disagreement with the lead primary validation statistic.**

Validation was authorized by `protocol/VALIDATION_RELEASE.json`, released at `2026-10-28T22:37:38.820478+00:00`, for the 20 reserved primary people. Before accessing their outcome fields, the independent script verified the release's freeze-record SHA256 and every one of the 46 frozen artifact hashes. No independent-laboratory empirical outcome was accessed by this audit.

## Independent implementation

The reconstruction reads the original CSV files, filters by the fixed reserved IDs before accessing `Hand_raw`, preserves `TN=1...824`, and independently builds all chronological input and outcome features. It imports no lead analysis module. It directly solves the full design by SVD with one intercept and slope per person/block, whereas the lead uses a nuisance-QR residualization and a different fixed-effect coding. Cluster covariance is reconstructed from the direct full-design influence weights; horizon covariance is retained when averaging the five lag effects.

The endpoint is `−Hand_raw`. The outcome is the future endpoint minus the fixed mean of five pre-index endpoints. The primary contrast is half the difference between preceding +4 and −4 clamp conditions when the preceding target was stationary, comparing zero-clamp index jumps with stationary indices. Both source sets and all five future horizons receive equal weights.

## Reserved result

| Population | People | Eligible events per horizon | Five-reach mean | SE | 95% interval |
|---|---:|---:|---:|---:|---:|
| Set A | 10 | 2,073 | +0.3182893145° | 0.2275059305° | [−0.1963648558°, +0.8329434847°] |
| Set B | 10 | 2,041 | −0.1529490003° | 0.2929706802° | [−0.8156947230°, +0.5097967224°] |
| Equal-set primary | 20 | — | **+0.0826701571°** | **0.1854661478°** | **[−0.3086996484°, +0.4740399626°]** |

The primary combined interval uses Welch df 16.9599291961. Each set's full-design rank is 166, 174, 182, 190 and 198 at horizons 1–5. Complete lag coefficients, their uncertainty, cell-event coefficients and curve covariance are in the numerical JSON.

This reserved primary estimate does not establish a nonzero population effect, nor does its interval establish equivalence within the frozen ±0.2° margin. This is a statement about the prespecified observable statistic; interpretation of secondary dynamical models and the full recovery campaign belongs to the lead scientific report.

## Agreement with lead implementation

| Compared quantity | Maximum absolute disagreement |
|---|---:|
| Equal-set scalar | 6.80e−16° |
| Equal-set scalar SE | 2.78e−17° |
| Ten set/horizon primary contrasts | 3.39e−15° |
| Ninety cell-event coefficients | 9.10e−15° |
| Combined interval endpoints | 7.22e−16° |
| Welch df | 3.55e−15 |

The differences are ordinary floating-point numerical error. No extraction, sign, contrast, coding, covariance or pooling discrepancy was found.

## Provenance

- Freeze record SHA256: `ef84ae6624cd37f7ea40ab7b0eac7abe1025de6561d456b4c84acb7d22458246`.
- Primary A source SHA256: `d366820b97af2ce22ed8491b49b086b32c972d44bf2103e4a7b29b87b3b56a98`.
- Primary B source SHA256: `21e551a2cc2b2faecffeee3c63d7054e4d4fa50a089c8b82ac888af0d7dd3947`.
- Reserved A IDs: 1, 2, 5, 7, 10, 12, 15, 17, 18, 19.
- Reserved B IDs: 2, 3, 4, 7, 8, 10, 14, 17, 18, 19.
- Additional script, release, output and compared-result digests: `validation_integrity.json` and `validation_Hand_raw_change_all.json`.

## Reproduction

```sh
.venv/bin/python campaigns/target_event_carryover_2026-10-28/audits/independent_extraction/reconstruct.py --part validation
```

Artifacts: `validation.log`, `validation_Hand_raw_change_all.json`, `validation_integrity.json`. The script requires the existing validation release and unchanged freeze hashes. It writes only its own independent audit outputs and never modifies frozen analysis files or source bytes. No method was selected or changed using the reserved result.
