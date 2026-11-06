"""Narrow diagnosis of already decoded CSHL_002 sign-feedback failure."""
from common import *
sys.path.insert(0,str(ROOT/'sources/longitudinal_learning_feasibility_2026-10-28/tools'))
import duckdb
from chronology import join_aggregate
fp=get(HERE/'ACCESS_FOOTPRINT.json');u=next(r for r in fp['primary_units'] if r['subject']=='CSHL_002')
obj=next(r for r in fp['objects'] if r['subject']=='CSHL_002');p=HERE/'bodies'/obj['local']
con=duckdb.connect(':memory:');con.execute('SET threads=1')
IO['logical_decoder_file_bytes']+=p.stat().st_size
q=con.execute(f'''SELECT contrastLeft,contrastRight,choice,feedbackType,rewardVolume,probabilityLeft,intervals_0,intervals_1,session,file_row_number
FROM read_parquet('{p}',file_row_number=true) ORDER BY file_row_number''').fetchnumpy()
fields=['contrastLeft','contrastRight','choice','feedbackType','rewardVolume','probabilityLeft','intervals_0','intervals_1']
v=np.column_stack([np.asarray(q[k].filled(np.nan) if np.ma.isMaskedArray(q[k]) else q[k],float) for k in fields])
ident=np.asarray(q['session'],str);IO['decoded_numeric_bytes']+=v.nbytes;IO['decoded_row_index_bytes']+=q['file_row_number'].nbytes
IO['decoded_session_identity_utf8_bytes']+=sum(len(z.encode()) for z in ident)
a=join_aggregate(v,ident,u['training_sessions']);xx=np.nan_to_num(a[:,1])-np.nan_to_num(a[:,0]);nz=(xx!=0)&(a[:,2]!=0)
bad=nz&((a[:,3]>0)!=(a[:,2]==-np.sign(xx)));rowmap=np.concatenate([np.arange(z['aggregate_row_start'],z['aggregate_row_stop']) for z in u['training_sessions']])[:3000]
errors=[]
for i in np.flatnonzero(bad):
    z=next(s for s in u['training_sessions'] if s['start']<=i<s['stop']);physical=int(rowmap[i])
    assert ident[physical]==z['eid']
    errors.append(dict(opportunity=int(i+1),aggregate_physical_row=physical,session=z['eid'],date=z['date'],protocol=z['protocol'],
        within_session_row=int(i-z['start']),fields={k:float(v[physical,j]) if np.isfinite(v[physical,j]) else None for j,k in enumerate(fields)},
        signed_contrast=float(xx[i]),geometrically_correct=bool(a[i,2]==-np.sign(xx[i])),positive_feedback=bool(a[i,3]>0)))
record=dict(utc=utc(),subject='CSHL_002',first3000_rows=3000,nonzero_responding_rows=int(nz.sum()),mismatch_count=int(bad.sum()),
    mismatch_prefix200=int(bad[:200].sum()),mismatch_prefix1000=int(bad[:1000].sum()),mismatch_scored1001_3000=int(bad[1000:].sum()),
    mismatch_feedback_codes={str(k):int(np.sum(bad&(a[:,3]==k))) for k in [-1,0,1]},
    correct_session_block_joins_verified=True,no_animal_or_row_removed=True,no_semantic_recoding_or_forecast_executed=True,
    exact_conflicting_rows=errors,required_reassessment='Frozen incompatibility stop: decide whether literal supplied feedback and geometrical accuracy preserve funded measurement/model meaning. No silent correction/filter/cohort shrink.',
    resources=receipt('COMPATIBILITY_CHECKPOINT'))
save('COMPATIBILITY_CHECKPOINT.json',record);print(json.dumps(record,default=serial))
