"""Diagnostic count bookkeeping and score-independent distance bounds; no recoding."""
from common import *
d=get(HERE/'DIAGNOSIS_COMPLETE.json');a=[json.loads(l) for l in read(HERE/'DIAGNOSTIC_ANOMALIES.jsonl').splitlines()]
assert len(a)==82 and {r['subject'] for r in a}=={'CSHL_002'}
assert sum('unit_contrast_side_assignment_disagrees' in r['flags'] for r in a)==33
path=HERE/'DIAGNOSTIC_LITERAL_CHRONOLOGY.npz'
with np.load(io.BytesIO(read(path)),allow_pickle=False) as z:
    vals=z['values'];subjects=z['subjects'];IO['decoded_literal_values_bytes']+=vals.nbytes+subjects.nbytes
    x=vals[list(subjects).index('CSHL_002')].copy()
l,r,c=x[:,:3].T;signed=np.nan_to_num(r)-np.nan_to_num(l)
result={}
for tag,lo,hi in [('short1001_1500',1000,1500),('primary1001_3000',1000,3000)]:
    s=signed[lo:hi];ch=c[lo:hi]
    literal=[int(np.sum(s==-1)),int(np.sum((s==-1)&(ch==1))),int(np.sum(s==1)),int(np.sum((s==1)&(ch==-1)))]
    rows=[r for r in a if lo<r['opportunity']<=hi and 'unit_contrast_side_assignment_disagrees' in r['flags']]
    chs=[r['values']['choice'] for r in rows];delta=[-len(rows),-chs.count(1),len(rows),chs.count(-1)]
    candidate=[b+v for b,v in zip(literal,delta)]
    assert min(literal[::2]+candidate[::2])>0
    y=np.array(literal[1::2])/literal[::2];yp=np.array(candidate[1::2])/candidate[::2]
    shift=float(np.abs(y-yp).mean());b=1.9*shift/192
    result[tag]=dict(literal_Nl_Kl_Nr_Kr=literal,column_side_counterfactual_count_delta=delta,
        counterfactual_Nl_Kl_Nr_Kr=candidate,literal_sign_ratios=y,counterfactual_sign_ratios=yp,
        equal_sign_target_distance=shift,maximum_absolute_paired_D_mean_change=b,
        maximum_absolute_primary_Bonferroni_endpoint_change=b*(1+2.4152498375322153),
        maximum_absolute_MAE_contrast_mean_change=2*shift/192)
save('MAPPING_CONSEQUENCE.json',dict(utc=utc(),subject='CSHL_002',all_192_retained=True,no_recoded_arrays=True,
    no_scores_no_forecasts=True,rows_with_negative_contrast=82,affected_prefix_rows_200=0,affected_prefix_rows_1000=0,
    columns=['N_left','K_left','N_right','K_right'],windows=result,
    scope='Counterfactual side bookkeeping only, not a changed target cache or a forecast evaluation. The observed case code keeps original fields unchanged.',
    proof='For both positive counts, distance between mixed states is absolute ratio change; triangle inequality bounds each proper-risk change by its equal-sign target distance. D has multiplier1.9. Only one paired animal changes, so mean and its standard error each change at most abs(delta)/192 (centered Euclidean norm inequality). The frozen critical then bounds the band-endpoint displacement. Applies if a separately released mapping only changes those observed targets and forecasts/weights remain fixed.'))
receipt('MAPPING_CONSEQUENCE');print(json.dumps(result,default=serial),flush=True)
