"""Compare independent1024 calculations with actual author outputs, not author code."""
import numpy as np
from independent import HERE, MAIN, Accounting, save


def main():
    meter=Accounting('final refined-output comparison and diagnostic inspection')
    own=meter.arrays(HERE/'REFINED_SCORE_CACHE.npz',keys=['metrics','new512_metrics','contributions'])
    author=meter.arrays(MAIN/'REFINED_SCORES.npz',keys=['pooled1024','additional512'])
    vectors=meter.arrays(MAIN/'REFINED_CONTRASTS.npz',keys=['contributions'])
    checks={label:float(np.max(np.abs(a-b))) for label,a,b in
            [('pooled1024',own['metrics'],author['pooled1024']),
             ('additional512',own['new512_metrics'],author['additional512']),
             ('augmented652_contributions',own['contributions'],vectors['contributions'])]}
    assert max(checks.values())<1e-12
    reconstructed=meter.json(HERE/'REFINED_CHECK.json')
    reported=meter.json(MAIN/'MAIN_ANALYSIS.json')
    indices=reported['primary_indices']
    checks['refined_primary_point']=float(np.max(np.abs(np.array(reconstructed['primary']['point'])-np.array(reported['bands']['point'])[indices])))
    checks['refined_primary_upper']=float(np.max(np.abs(np.array(reconstructed['primary']['primary']['upper'])-np.array(reported['bands']['primary']['upper'])[indices])))
    checks['augmented652_upper']=float(np.max(np.abs(np.array(reconstructed['augmented']['joint']['upper'])-np.array(reported['bands']['joint']['upper']))))
    assert max(checks.values())<1e-12
    # Metadata aliases only: independent labels 'refined'/'refined_interaction'
    # correspond to author's 'fixed_refined'/'interaction_refined'.
    family=meter.json(MAIN/'MAIN_FAMILY_REFINED.json')
    normalized=[]
    for label in reconstructed['labels']:
        label=dict(label)
        label['kind']={'refined':'fixed_refined','refined_interaction':'interaction_refined'}.get(label['kind'],label['kind'])
        normalized.append(label)
    assert normalized==family['columns'] and indices==reconstructed['refined_primary_indices']
    mc=meter.json(MAIN/'REFINED_MONTE_CARLO.json')
    calibration=meter.json(MAIN/'REFINED_CALIBRATION_SUMMARY.json')
    save('AUTHOR_REFINED_AGREEMENT.json',dict(max_abs_differences=checks,
        identical_scientific_columns_after_documented_metadata_alias=True,
        numerical_summary=mc,absolute_calibration_summary=calibration,
        scope='Independent count-score/vector/band agreement plus inspected saved diagnostics, not biological replication or exact coverage certification'))
    save('AUTHOR_REFINED_AGREEMENT_RESOURCES.json',meter.receipt())
    print(checks)
    print('MC summaries',{k:v for k,v in mc.items() if not isinstance(v,(list,dict))})
    print('Calibration keys',calibration.keys())


if __name__=='__main__': main()
