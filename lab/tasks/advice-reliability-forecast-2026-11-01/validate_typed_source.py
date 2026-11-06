import analysis_v2 as a
import numpy as np,json
d=a.assemble(a.GATE['source_people'])
with np.load(a.ROOT/'source.npz') as z:
 errors={k:float(np.max(abs(d[k]-z[k]))) for k in z.files}
assert all(v==0 for v in errors.values())
r={'timestamp_utc':a.NOW(),'source_people':a.GATE['source_people'],'max_differences':errors,'all_source_features_and_targets_identical':True,'saved_source_fits_reused_without_refit':True}
a.savej(a.ROOT/'SOURCE_FEATURE_EQUIVALENCE.json',r);a.resource_record(a.ROOT,'TYPED_SOURCE_EQUIVALENCE');print(json.dumps(r,indent=2))
