"""Partial identification from published element means and digitized endpoints.

No bird identities invented, no element-level standard errors or p-values.
"""
from pathlib import Path
import csv,itertools,json
import numpy as np
BASE=Path(__file__).resolve().parents[1]

def partitions(n,k):
    """Canonical restricted-growth strings: each set partition exactly once."""
    a=[0]*n
    def rec(i,m):
        if i==n:
            if m==k-1:yield a.copy()
            return
        for x in range(min(m+1,k-1)+1):
            if max(m,x)+(n-i-1)<k-1:continue
            a[i]=x;yield from rec(i+1,max(m,x))
    yield from rec(1,0)

def bird_bounds(vals,k,max_elements=None):
    all_means=[];witnesses=[]
    for labels in partitions(len(vals),k):
        if max_elements is not None and max(labels.count(i) for i in range(k))>max_elements:continue
        bird_means=[np.mean([v for v,l in zip(vals,labels) if l==i]) for i in range(k)]
        all_means.append(float(np.mean(bird_means)));witnesses.append(labels)
    low=int(np.argmin(all_means));high=int(np.argmax(all_means))
    return {'allocation_count':len(all_means),'equal_bird_mean_bounds_ms':[all_means[low],all_means[high]],
       'attaining_partitions':[witnesses[low],witnesses[high]],
       'max_elements_per_bird':max_elements,
       'meaning':'all source-compatible nonempty anonymous assignments of plotted elements to stated bird count; no family independence assumed'}

def main():
    rows=list(csv.DictReader((BASE/'audits/zhao_source/table_s1_transcription.csv').open()))
    short=np.array([float(r['element_mean_ms']) for r in rows if r['protocol']=='four_50ms'])
    long=np.array([float(r['element_mean_ms']) for r in rows if r['protocol']=='single_300ms_pooled'])
    independent=json.loads((BASE/'audits/prior_work/zhao_table_independent.json').read_text())
    assert np.array_equal(short,independent['short_ms'])
    assert np.array_equal(long,independent['long_ms'])
    med25=[float(np.median(np.delete(short,i))) for i in range(len(short))]
    splits=[]
    for ids in itertools.combinations(range(len(long)),4):
        mask=np.zeros(len(long),bool);mask[list(ids)]=True
        splits.append([float(np.median(long[~mask])),float(np.median(long[mask]))])
    splits=np.array(splits)
    fig=json.loads((BASE/'audits/zhao_source/figure5_duration_digitization_corrected.json').read_text())['summary']
    o=fig['opto_only_300'];c=fig['natural_plus_opto_300']
    # Main P10 states one to three elements/bird in long opto cohorts.
    bo=bird_bounds(o['duration_values_ms'],4,max_elements=3);bc=bird_bounds(c['duration_values_ms'],3,max_elements=3)
    assert bo['allocation_count']==315 and bc['allocation_count']==6
    ob=bo['equal_bird_mean_bounds_ms'];cb=bc['equal_bird_mean_bounds_ms']
    oe=o['conservative_median_extraction_envelope_ms'];ce=c['conservative_median_extraction_envelope_ms']
    # Reconstructed plot medians are a descriptive cross-condition comparison.
    # Complete overwrite predicts the same distribution in every architecture.
    slope=(o['element_duration_median_ms']-62.3)/250
    intercept=62.3-50*slope
    result={
      'status':'source-based descriptive/partial-identification result; no independent-animal inferential test',
      'table_short':{'n':len(short),'median_ms':float(np.median(short)),'mean_ms':float(np.mean(short)),
         'main_caption_n':25,'main_text_median_ms':62.3,'all_single_omission_median_range_ms':[min(med25),max(med25)]},
      'table_long_pooled':{'n':len(long),'median_ms':float(np.median(long)),
         'meaning':'opto-only and natural+opto elements pooled; source table lacks condition and bird IDs'},
      'observed_support_gap_ms':float(long.min()-short.max()),
      'rounding_robust_support_gap_ms':float(long.min()-short.max()-.1),
      'support_gap_assumptions':'all observed long-subset element means drawn from supplied11; short sample drawn from supplied26; aggregate using nonnegative weights summing to1. Bound is on observed summaries, not all renditions or bird population.',
      'unlabeled_table_partitions':{'count':len(splits),'opto_only_median_range_ms':[float(splits[:,0].min()),float(splits[:,0].max())],
           'conflict_median_range_ms':[float(splits[:,1].min()),float(splits[:,1].max())],
           'conflict_minus_opto_median_range_ms':[float((splits[:,1]-splits[:,0]).min()),float((splits[:,1]-splits[:,0]).max())]},
      'plot_opto_only':o,'plot_conflict':c,
      'descriptive_complete_overwrite_comparison':{'calibration':'EXPLORATORY REVISED calibration after source mismatch: main-text short62.3 and fig5 opto-only plotted median; 2 points/2 parameters, no fit degrees of freedom. Not untouched holdout.',
        'slope':slope,'intercept_ms':intercept,
        'predictions_ms':{m:o['element_duration_median_ms'] for m in ['stored_reference','motor_scaffold','shared_representation']},
        'observed_conflict_median_ms':c['element_duration_median_ms'],
        'residual_ms':c['element_duration_median_ms']-o['element_duration_median_ms'],
        'residual_extraction_only_envelope_ms':[ce[0]-oe[1],ce[1]-oe[0]],
        'original_provisional_prediction_ms':323.,
        'original_provisional_residual_ms':c['element_duration_median_ms']-323.,
        'original_prediction_status':'invalid as pure opto-only calibration because323 belongs to pooled long summary; retained to show consequential source-driven revision',
        'interpretation':'All three have identical prediction and identical residual under common overwrite. Extraction precision does not determine sampling error; this is not a statistical rejection of overwrite or a clean withheld-bird validation.'},
      'anonymous_bird_aggregation':{'opto':bo,'conflict':bc,
        'conflict_minus_opto_equal_bird_mean_bounds_ms':[cb[0]-ob[1],cb[1]-ob[0]],
        'with_conservative_4pixel_error_per_group_ms':[cb[0]-ob[1]-2*400/121*4,cb[1]-ob[0]+2*400/121*4],
        'unrestricted_opto_sensitivity':bird_bounds(o['duration_values_ms'],4),
        'maximum_two_elements_opto_sensitivity':bird_bounds(o['duration_values_ms'],4,max_elements=2),
        'interpretation':'Even the sign of a cohort difference in equal-bird means is not identified from plotted elements with missing identities. This does not question short-versus-long support separation.'}
    }
    (BASE/'outputs'/'empirical_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    np.savetxt(BASE/'outputs'/'all_long_condition_partitions.csv',splits,delimiter=',',header='opto7_median_ms,conflict4_median_ms',comments='')
    print(json.dumps({k:v for k,v in result.items() if not k.startswith('plot_')},indent=2))

if __name__=='__main__':main()
