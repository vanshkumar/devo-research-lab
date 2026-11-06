"""Independent INPUT-ONLY reconstruction; never reads choices or feedback."""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
inputs = pd.read_csv(ROOT / 'outputs/input_only/trial_inputs.csv', dtype={'subject': str})
split = pd.read_csv(ROOT / 'protocol/split_manifest.csv', dtype={'subject': str})
rows = []
for subject, s in inputs.groupby('subject'):
    s = s.sort_values('trial')
    p = s.probabilityLeft.to_numpy()
    c = s.stimContrast.to_numpy()
    changes = np.flatnonzero(np.diff(p) != 0) + 1
    switches = [x for x in changes if x >= 200 and p[x] != .5 and p[x - 1] != .5]
    masks = {window: np.zeros(len(s), bool) for window in [20, 30]}
    for start in switches:
        next_switch = next((x for x in changes if x > start), len(s))
        for window, mask in masks.items():
            mask[start:min(start + window, next_switch, len(s))] = True
    rows.append(dict(subject=subject, n_switch=len(switches),
                     n30=int((masks[30] & (c <= .1)).sum()),
                     n20=int((masks[20] & (c <= .1)).sum()),
                     n0=int((masks[30] & (c == 0)).sum())))
coverage = split.merge(pd.DataFrame(rows), on='subject', validate='one_to_one')
coverage.to_csv(Path(__file__).with_name('input_coverage.csv'), index=False)
print(coverage.groupby(['partition', 'condition'])[['n30', 'n20', 'n0']].sum().to_string())
