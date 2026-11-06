"""Exact independent check of a support bound, using Decimal source means."""
import csv,json
from decimal import Decimal
from pathlib import Path
p=Path(__file__).resolve().parent
with (p/'table_s1_transcription.csv').open() as f:rows=list(csv.DictReader(f))
s=[Decimal(r['element_mean_ms']) for r in rows if r['protocol']=='four_50ms']
l=[Decimal(r['element_mean_ms']) for r in rows if r['protocol']=='single_300ms_pooled']
bound=min(l)-max(s)
# Each printed one-decimal mean has rounding interval±.05ms.
rounded_bound=(min(l)-Decimal('.05'))-(max(s)+Decimal('.05'))
assert bound==Decimal('24.1') and rounded_bound==Decimal('24.00')
assert all(min(l)-max(s[:i]+s[i+1:])>=bound for i in range(len(s)))
result={'short_count':len(s),'long_count':len(l),'short_max_printed_ms':str(max(s)),'long_min_printed_ms':str(min(l)),'lower_bound_printed_ms':str(bound),'lower_bound_allowing_rounding_ms':str(rounded_bound),'proof':'Any convex aggregation lies between its minimum and maximum input. Every observed long element mean exceeds every observed short mean. Any nonempty long subset retains minimum≥176.1; arbitrary one-short deletion cannot increase maximum beyond152.0. Thus any assignment of these element means to nonempty bird groups and any nonnegative normalized within-bird weighting preserves the gap.','scope':'Observed element means only; not per-rendition support, population effect, raw individual-bird estimate, p-value, or identification of a tutor-specific comparator.','source_identity':'Table S1 has one blue numeric style for both treatment rows except red median markers; no bird colors or IDs. Main Fig3/5 use treatment colors only.'}
(p/'support_bound_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
