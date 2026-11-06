"""Unscored first-mismatch inspection; preserve frozen gate."""
import analysis as a
for row in a.rows(set(a.GATE['evaluation_people'])):
    bad=[{'error_field':e,'accuracy_field':c,'error':row[e],'reported_accuracy':row[c],'abs_error_minus10':abs(row[e])-10} for e,c in [('K','M'),('O','Q'),('R','S')] if row[c]!=(abs(row[e])<=10)]
    if bad:
        rec={'timestamp_utc':a.NOW(),'person':int(row['A']),'trial':int(row['G']),'block':int(row['D']),'mismatches':bad,'scores':'UNRUN','predictions':'not saved; original prediction invocation stopped at this audit assertion'}
        a.savej(a.ROOT/'THRESHOLD_FIRST_MISMATCH.json',rec);a.resource_record(a.ROOT,'THRESHOLD_FIRST_MISMATCH');print(rec);break
else:raise RuntimeError('No mismatch reproduced')
