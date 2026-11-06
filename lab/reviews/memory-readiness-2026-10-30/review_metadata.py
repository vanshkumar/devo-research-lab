"""Independent frozen metadata audit and ONE focal-item candidate; no answers.

Read one corrected NPY body opaquely, then type-project only permitted byte
columns. Never construct a view of mode/category/sequence or open any archive,
answer shard, response NPZ, network resource, or source-script execution path.
"""
import os
for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "1"
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
from pathlib import Path
import resource
import time
import numpy as np

ROOT = Path('/Users/vanshkumar/Documents/repos/devo-research-lab')
HERE = ROOT / 'lab/reviews/memory-readiness-2026-10-30'
TASK = ROOT / 'lab/tasks/memory-policy-transfer-2026-10-30'
SRC = ROOT / 'sources/memory_policy_transfer_2026-10-30'
DEADLINE = datetime.fromisoformat('2026-10-30T13:38:27+00:00')
ALLOW = ('uid', 'item', 'time', 'install', 'arm', 'count', 'ordinal')
COMPACT = np.dtype([(k, v) for k, v in [('uid','u4'),('item','u4'),('time','i8'),('install','i8'),('arm','u4'),('count','i4'),('ordinal','u8')]])


def epoch(s):
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


class Budget:
    def __init__(self):
        # Covers every earlier normal-context/source/document command, repeated
        # source snippet and NPY-header probe, plus interpreter-independent QA.
        self.total = 20_000_000
        self.entries = [{'path': 'pre-execution ordinary documents/source/LEARNINGS and review QA', 'charge_bytes': 20_000_000, 'basis': 'conservative envelope; actual text bytes far smaller'}]
    def read(self, path):
        allowed = {
            SRC/'metadata_sorted.npy', SRC/'METADATA.json', SRC/'selected_users.json',
            TASK/'COHORT.json', TASK/'COHORT_SUMMARY.json', TASK/'READINESS.json',
            TASK/'SOURCE_FIELD_AUDIT_PEOPLE.json',
        }
        assert path in allowed, 'unlisted data/document access'
        n = path.stat().st_size
        assert self.total + n <= 400_000_000
        self.total += n
        self.entries.append({'path': str(path.relative_to(ROOT)), 'charge_bytes': n, 'basis': 'full application-read file bytes'})
        return path.read_bytes()
    def j(self, path):
        return json.loads(self.read(path))


def projected_top_json(raw, wanted):
    """Only materialize allowlisted top-level values, skipping other byte spans."""
    n = len(raw)
    def ws(i):
        while i < n and raw[i] in b' \n\r\t': i += 1
        return i
    def string_end(i):
        assert raw[i] == 34
        i += 1
        while i < n:
            if raw[i] == 92: i += 2
            elif raw[i] == 34: return i+1
            else: i += 1
        raise ValueError('truncated JSON string')
    def value_end(i):
        if raw[i] == 34: return string_end(i)
        if raw[i] in b'[{':
            stack = [raw[i]]; i += 1
            while i < n and stack:
                if raw[i] == 34: i = string_end(i); continue
                if raw[i] in b'[{': stack.append(raw[i])
                elif raw[i] in b']}':
                    assert (stack.pop(), raw[i]) in ((91,93),(123,125))
                i += 1
            assert not stack
            return i
        while i < n and raw[i] not in b',} \t\r\n': i += 1
        return i
    i = ws(0); assert raw[i] == 123; i += 1
    result = {}; decoded = []
    while True:
        i = ws(i)
        if raw[i] == 125: break
        e = string_end(i); key = json.loads(raw[i:e]); i = ws(e)
        assert raw[i] == 58; i = ws(i+1); e = value_end(i)
        if key in wanted:
            assert key not in result
            result[key] = json.loads(raw[i:e]); decoded.append(key)
        i = ws(e)
        if raw[i] == 125: break
        assert raw[i] == 44; i += 1
    assert set(result) == set(wanted)
    return result, decoded


def projected_npy(raw):
    f = io.BytesIO(raw)
    version = np.lib.format.read_magic(f)
    if version == (1,0): shape, fortran, dtype = np.lib.format.read_array_header_1_0(f)
    else: shape, fortran, dtype = np.lib.format.read_array_header_2_0(f)
    assert len(shape) == 1 and not fortran and not dtype.hasobject
    offset = f.tell(); n = shape[0]
    assert len(raw) == offset + n*dtype.itemsize
    out = np.empty(n, dtype=COMPACT)
    for field in ALLOW:
        fielddtype, position = dtype.fields[field][:2]
        assert fielddtype == COMPACT.fields[field][0]
        # No typed array/view is ever constructed for excluded fields.
        column = np.ndarray((n,), dtype=fielddtype, buffer=raw, offset=offset+position, strides=(dtype.itemsize,))
        out[field] = column
    return out, {'shape': list(shape), 'record_bytes': dtype.itemsize, 'header_bytes': offset,
                 'interpreted_fields': list(ALLOW), 'excluded_field_names_only': [k for k in dtype.names if k not in ALLOW]}


def cells(delta_days, prior, other):
    # Independent explicit threshold comparisons, matching original left bins.
    return (sum(delta_days > v for v in (1/1440, 1/24, 1, 7)),
            sum(prior > v for v in (1,2,4)), sum(other > v for v in (0,9,99)))


def item_groups(a):
    idx = np.argsort(a['item'], kind='stable')
    if len(idx) == 0: return []
    boundaries = np.r_[0, 1+np.flatnonzero(np.diff(a['item'][idx])), len(idx)]
    return [(int(a['item'][idx[l]]), idx[l:r]) for l,r in zip(boundaries[:-1], boundaries[1:])]


def features(a):
    result = []
    for item, positions in item_groups(a):
        for order, (left, right) in enumerate(zip(positions[:-1], positions[1:]), 1):
            delta = (int(a['time'][right])-int(a['time'][left]))/86400
            other = int(right-left-1)
            result.append((delta, order, other, cells(delta, order, other)))
    return result


def focal_intervals(a, before):
    """Metadata-only frozen complete-focal rule and other-item gap flags."""
    pre = {item: int(before['count'][pos[-1]]) for item,pos in item_groups(before)}
    groups = item_groups(a)
    gaps = []
    stage = Counter()
    eligible = []
    for item, positions in groups:
        counts = a['count'][positions].astype('int64')
        if item in pre:
            inc = int(counts[0])-pre[item]
            if inc != 1: gaps.append((-1, int(positions[0]), 'prefix', max(0,inc-1)))
        elif counts[0] != 1:
            gaps.append((-1, int(positions[0]), 'prefix', max(0,int(counts[0])-1)))
        for left,right,c0,c1 in zip(positions[:-1], positions[1:], counts[:-1], counts[1:]):
            inc = int(c1-c0)
            if inc != 1: gaps.append((int(left),int(right),'jump' if inc>1 else 'reset',max(0,inc-1)))
        stage['all_observed_item_histories'] += 1
        if item in pre: stage['item_known_before_period'] += 1; continue
        if counts[0] != 1: stage['item_first_counter_not_one'] += 1; continue
        if not np.array_equal(counts,np.arange(1,len(counts)+1)): stage['item_later_counter_gap_reset'] += 1; continue
        stage['counter_complete_new_focal_histories'] += 1
        if len(positions) < 2: stage['focal_without_repeat'] += 1; continue
        stage['focal_histories_with_repeat'] += 1
        eligible.append((item,positions))
    # Query gap-overlap sets with sorted endpoints. Gaps belong to ineligible
    # focal items, so they cannot be the same item as an eligible interval.
    sorted_gaps = sorted(gaps)
    starts = np.array([g[0] for g in sorted_gaps],dtype='int64')
    ends = np.array([g[1] for g in sorted_gaps],dtype='int64')
    max_end = np.maximum.accumulate(ends) if len(ends) else ends
    prefix_end = max([g[1] for g in gaps if g[2]=='prefix'] or [-1])
    internal = sorted([g for g in gaps if g[2]!='prefix'])
    istart = np.array([g[0] for g in internal],dtype='int64')
    iend = np.array([g[1] for g in internal],dtype='int64')
    imax = np.maximum.accumulate(iend) if len(iend) else iend
    positive = sorted([g for g in gaps if g[2]=='jump'],key=lambda g:g[1])
    pend = np.array([g[1] for g in positive],dtype='int64')
    pstart = np.array([g[0] for g in positive],dtype='int64')
    pmax = np.maximum.accumulate(pstart) if len(pstart) else pstart
    intervals = []
    for item, positions in eligible:
        for prior, (left,right) in enumerate(zip(positions[:-1],positions[1:]),1):
            left,right = int(left),int(right)
            delta = (int(a['time'][right])-int(a['time'][left]))/86400
            other = right-left-1
            k = int(np.searchsorted(starts,right,side='left'))
            ambiguous = bool(k and max_end[k-1] > left)
            k2 = int(np.searchsorted(istart,right,side='left'))
            internal_ambiguous = bool(k2 and imax[k2-1] > left)
            k3 = int(np.searchsorted(pend,right,side='right'))
            definite = bool(k3 and pmax[k3-1] >= left)
            intervals.append({'item':item,'time':int(a['time'][right]),'left':left,'right':right,
                              'delta_days':delta,'prior':prior,'recorded_other':other,'cell':cells(delta,prior,other),
                              'ambiguous':ambiguous,'prefix_ambiguous':left<prefix_end,
                              'internal_ambiguous':internal_ambiguous,'enclosed_positive_jump':definite})
    stage.update({'other_item_gap_brackets':len(gaps),'prefix_brackets':sum(g[2]=='prefix' for g in gaps),
                  'positive_internal_jump_brackets':sum(g[2]=='jump' for g in gaps),
                  'internal_reset_brackets':sum(g[2]=='reset' for g in gaps),
                  'missing_event_lower_bound_internal_positive_jumps':sum(g[3] for g in gaps if g[2]=='jump')})
    return intervals, stage, gaps


def synthetic_checks():
    checks = []
    def check(name, ok):
        assert ok, name
        checks.append({'name':name,'passed':True})
    fake = b'{"arms":{"0":"random"},"modes":{"DO_NOT_DECODE":[123,"FORBIDDEN"]},"members":[]}'
    selected, decoded = projected_top_json(fake, {'arms','members'})
    check('JSON_unapproved_values_not_decoded', selected=={'arms':{'0':'random'},'members':[]} and set(decoded)=={'arms','members'})
    orig_dtype = np.dtype([('uid','u4'),('item','u4'),('time','i8'),('install','i8'),('arm','u4'),('count','i4'),('ordinal','u8'),('mode','u4'),('sequence','i4')])
    synthetic = np.zeros(3,dtype=orig_dtype); synthetic['uid']=[1,2,3]; synthetic['mode']=4294967295; synthetic['sequence']=-999999
    f=io.BytesIO(); np.save(f,synthetic,allow_pickle=False)
    safe,info=projected_npy(f.getvalue())
    check('NPY_only_allowed_columns_materialized', safe.dtype.names==ALLOW and safe['uid'].tolist()==[1,2,3])
    check('NPY_excluded_column_names_only', info['excluded_field_names_only']==['mode','sequence'])
    check('cell_exact_edges', cells(1/1440,1,0)==(0,0,0) and cells(7,4,99)==(3,2,2))
    check('cell_just_over_edges', cells(7.001,5,100)==(4,3,3))
    def a(rows):
        out=np.zeros(len(rows),dtype=COMPACT)
        for k,(item,count) in enumerate(rows): out[k]=(1,item,100+10*k,0,0,count,k)
        return out
    empty=a([])
    x=a([(1,1),(2,1),(2,3),(1,2)])
    z,stage,gaps=focal_intervals(x,empty)
    check('focal_survives_other_item_gap',len(z)==1 and z[0]['item']==1)
    check('other_item_gap_detected_inside_interval',z[0]['ambiguous'] and z[0]['enclosed_positive_jump'] and z[0]['recorded_other']==2)
    check('gap_missing_event_lower_bound',stage['missing_event_lower_bound_internal_positive_jumps']==1)
    x=a([(1,1),(1,2),(2,2)])
    z,stage,gaps=focal_intervals(x,empty)
    check('late_first_other_item_ambiguates_earlier_interval',z[0]['prefix_ambiguous'] and z[0]['ambiguous'])
    pre=a([(2,1)])
    z,stage,gaps=focal_intervals(x,pre)
    check('cached_prior_counter_one_step_resolves_prefix',not z[0]['ambiguous'])
    z,stage,gaps=focal_intervals(a([(1,1),(1,3)]),empty)
    check('focal_gap_excludes_item',len(z)==0)
    z,stage,gaps=focal_intervals(a([(1,1),(1,2)]),a([(1,5)]))
    check('known_pregap_item_reset_cannot_be_new_focal',len(z)==0)
    return checks


def main():
    t0=time.monotonic(); assert datetime.now(timezone.utc)<DEADLINE
    assert not (HERE/'CANDIDATE_READINESS.json').exists(), 'single candidate execution only'
    checks=synthetic_checks()
    freeze={'utc':datetime.now(timezone.utc).isoformat(),'candidate_definition_sha256':hashlib.sha256((HERE/'CANDIDATE_FREEZE.md').read_bytes()).hexdigest(),
            'execution_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checks':checks,'all_passed':True}
    (HERE/'EXECUTION_FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n')
    budget=Budget()
    mappings,decoded=projected_top_json(budget.read(SRC/'METADATA.json'),{'arms','members','sampled_users','sampled_rows','fixed_end_date','cumulative_archive_decoded_bytes'})
    users=budget.j(SRC/'selected_users.json')
    old=budget.j(TASK/'COHORT.json'); summary=budget.j(TASK/'COHORT_SUMMARY.json'); readiness=budget.j(TASK/'READINESS.json')
    consumed_records=budget.j(TASK/'SOURCE_FIELD_AUDIT_PEOPLE.json'); consumed={x['uid'] for x in consumed_records}
    data,npyinfo=projected_npy(budget.read(SRC/'metadata_sorted.npy'))
    def check(name,ok,detail=None):
        checks.append({'name':name,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})
    check('selected_hash_bucket0_mod8',all(int(u['hash'][:8],16)%8==0 for u in users))
    check('row_user_count_matches_manifest',len(data)==mappings['sampled_rows'] and len(users)==mappings['sampled_users'])
    check('metadata_sorted_uid_time_ordinal',all(np.all(data['uid'][1:]>=data['uid'][:-1]) for _ in [0]))
    starts=np.searchsorted(data['uid'],np.arange(len(users)+1))
    def person(uid): return data[starts[uid]:starts[uid+1]]
    S,E=epoch('2020-03-01'),epoch('2020-06-01')
    days={datetime.strptime(Path(m['name']).stem[-8:],'%Y%m%d').date() for m in mappings['members'] if m['name'].endswith('.csv')}
    expected_days={datetime.fromtimestamp(S+86400*k,timezone.utc).date() for k in range((E-S)//86400)}
    check('complete_postgap_daily_manifest',expected_days.issubset(days))
    calendar_missing=[]; d=min(days)
    while d<=max(days):
        if d not in days: calendar_missing.append(d.isoformat())
        d+=timedelta(days=1)
    armmap={int(k):v for k,v in mappings['arms'].items()}
    excluded=Counter(); old_candidates=[]; old_contexts=Counter()
    for uid,info in enumerate(users):
        a=person(uid)
        if len(info['arms'])!=1: excluded['multiple_arms']+=1; continue
        arm=armmap[info['arms'][0]]
        if arm not in ('random','smart','spaced'): excluded['unrecognised_policy']+=1; continue
        if len(info['installations'])!=1: excluded['multiple_installations']+=1; continue
        install=info['installations'][0]
        if not S<=install<epoch('2020-05-11'): excluded['installation_outside_gap_free_window']+=1; continue
        if len(info['language_set'])!=1: excluded['multiple_language_or_set']+=1; continue
        if int(a['time'][0])<install: excluded['preinstallation_records']+=1; continue
        a=a[(a['time']>=install)&(a['time']<install+21*86400)]
        if not len(a): excluded['no_window_rows']+=1; continue
        if np.any(a['time'][1:]<=a['time'][:-1]): excluded['timestamp_ties']+=1; continue
        groups=item_groups(a)
        bad=sum(np.count_nonzero(a['count'][p]!=np.arange(1,len(p)+1)) for _,p in groups)
        if bad: excluded['item_counter_gap_or_left_truncation']+=1; continue
        repeats=len(a)-len(groups)
        if repeats<20 or len(np.unique(a['time']//86400))<2: excluded['fewer_than_20_repeats_or_two_days']+=1; continue
        ctx=tuple(info['language_set'][0]); old_contexts[(arm,ctx)]+=1
        old_candidates.append({'uid':uid,'hash':info['hash'],'arm':arm,'context':ctx,'repeats':repeats,'rows':len(a)})
    check('original_attrition_exact',dict(excluded)==summary['exclusions'],dict(excluded))
    old_groups={
        'source_fit':[x for x in old_candidates if x['arm']=='random' and x['context']==('de','B') and int(x['hash'][8:16],16)%4!=0],
        'source_validation':[x for x in old_candidates if x['arm']=='random' and x['context']==('de','B') and int(x['hash'][8:16],16)%4==0],
        'smart':[x for x in old_candidates if x['arm']=='smart' and x['context']==('de','B')],
        'spaced':[x for x in old_candidates if x['arm']=='spaced' and x['context']==('de','B')]}
    old_cells={}; old_stats={}
    for g,people in old_groups.items():
        c=Counter(); itemset=set(); rowcount=0
        for p in people:
            info=users[p['uid']]; install=info['installations'][0]; a=person(p['uid'])
            a=a[(a['time']>=install)&(a['time']<install+21*86400)]
            f=features(a); c.update(x[3] for x in f); rowcount+=len(f); itemset.update(int(x) for x in a['item'])
        old_cells[g]=c
        expected_people=old[g] if g.startswith('source') else old['targets'][g]
        check('original_'+g+'_identities',{p['uid'] for p in people}=={p['uid'] for p in expected_people})
        check('original_'+g+'_repeat_counts',rowcount==summary['repeat_events'][g])
        old_stats[g]={'people':len(people),'repeat_rows':rowcount,'unique_observed_items':len(itemset)}
    supported={c for c,n in old_cells['source_fit'].items() if n>=10}
    old_support={}
    for g in ('source_validation','smart','spaced'):
        n=sum(n for c,n in old_cells[g].items() if c in supported)
        old_support[g]={'supported_repeats':n,'fraction':n/old_stats[g]['repeat_rows']}
        check('original_'+g+'_joint_support',n==readiness['joint_support'][g]['supported_repeat_rows'])
    first=Counter(); increments=Counter(); violations_by_person={}; audited_rows=0
    for uid in consumed:
        info=users[uid]; install=info['installations'][0]; a=person(uid)
        a=a[(a['time']>=install)&(a['time']<install+21*86400)]
        audited_rows+=len(a); bad=0
        for item,p in item_groups(a):
            vals=a['count'][p].astype('int64'); first[int(vals[0])]+=1; bad+=int(vals[0]!=1)
            inc=np.diff(vals); increments.update(int(v) for v in inc); bad+=int(np.count_nonzero(inc!=1))
        violations_by_person[str(uid)]=bad
    check('18_consumed_source_people',len(consumed)==18)
    check('9819_audited_source_rows_metadata_only',audited_rows==9819)
    check('229_source_continuity_violations',sum(violations_by_person.values())==229)
    check('source_first_count_histogram',dict(first)=={1:5605,2:116,3:3})
    check('source_increment_counts_metadata_only',dict(increments)=={1:3985,2:105,3:5})
    check('original_validation_is_consumed',all(p['uid'] in consumed for p in old['source_validation']))
    # The single candidate. No changed masks/window/threshold after this count.
    stages=Counter(); candidates=[]; interval_rows=[]; cohort_stage_by_arm=defaultdict(Counter)
    for uid,info in enumerate(users):
        assert datetime.now(timezone.utc)<DEADLINE
        if len(info['arms'])!=1: stages['multiple_arms']+=1; continue
        arm=armmap[info['arms'][0]]
        if arm not in ('random','smart','spaced'): stages['unrecognised_policy']+=1; continue
        if len(info['installations'])!=1: stages['multiple_installations']+=1; continue
        if info['language_set']!=[['de','B']]: stages['not_stable_German_B']+=1; continue
        all_a=person(uid); install=info['installations'][0]
        if int(all_a['time'][0])<install: stages['preinstallation_records']+=1; continue
        before=all_a[all_a['time']<S]; a=all_a[(all_a['time']>=S)&(all_a['time']<E)]
        if not len(a): stages['no_postgap_rows']+=1; continue
        cohort_stage_by_arm[arm]['stable_context_postgap_people']+=1
        if np.any(a['time'][1:]<=a['time'][:-1]): stages['timestamp_ties']+=1; continue
        records,itemstages,gaps=focal_intervals(a,before)
        cohort_stage_by_arm[arm].update(itemstages)
        if records: cohort_stage_by_arm[arm]['people_with_any_focal_repeat']+=1
        days_with_repeats=len({r['time']//86400 for r in records})
        if len(records)<20 or days_with_repeats<2:
            stages['fewer_than20_focal_repeats_or2_dates']+=1; continue
        exposed=uid in consumed
        if arm=='random':
            group='source_fit' if exposed or int(info['hash'][8:16],16)%4!=0 else 'source_validation'
        else: group=arm
        p={'uid':uid,'hash':info['hash'],'group':group,'arm':arm,'rows_postgap':len(a),'focal_repeat_rows':len(records),
           'repeat_dates':days_with_repeats,'focal_item_histories':len({r['item'] for r in records}),
           'development_exposed':exposed,'installation_pre_period':install<S,'item_stages':dict(itemstages)}
        candidates.append(p)
        for r in records: interval_rows.append({'uid':uid,'group':group,**r})
    grouped={g:[r for r in interval_rows if r['group']==g] for g in ('source_fit','source_validation','smart','spaced')}
    fit=grouped['source_fit']; cellrows=Counter(r['cell'] for r in fit)
    cellpeople=defaultdict(set); source_items={r['item'] for r in fit}
    for r in fit: cellpeople[r['cell']].add(r['uid'])
    supported_rows={c for c,n in cellrows.items() if n>=10}
    supported_people={c for c,n in cellrows.items() if n>=10 and len(cellpeople[c])>=5}
    fit_clean=[r for r in fit if not r['ambiguous']]
    clean_cellrows=Counter(r['cell'] for r in fit_clean); clean_people=defaultdict(set)
    for r in fit_clean: clean_people[r['cell']].add(r['uid'])
    clean_support={c for c,n in clean_cellrows.items() if n>=10 and len(clean_people[c])>=5}
    output={}
    def subset_stats(rows):
        return {'repeat_rows':len(rows),'people':len({r['uid'] for r in rows}),'unique_items':len({r['item'] for r in rows}),
                'learner_item_histories':len({(r['uid'],r['item']) for r in rows})}
    for g,rows in grouped.items():
        people=[p for p in candidates if p['group']==g]
        shared=[r for r in rows if r['item'] in source_items]
        clean=[r for r in rows if not r['ambiguous']]
        source_supported=[r for r in rows if r['cell'] in supported_rows]
        stronger=[r for r in rows if r['cell'] in supported_people and r['item'] in source_items]
        clean_supported=[r for r in clean if r['cell'] in clean_support and r['item'] in source_items]
        output[g]={**subset_stats(rows), 'people_total_selected':len(people),
            'development_exposed_people':sum(p['development_exposed'] for p in people),
            'fresh_people':sum(not p['development_exposed'] for p in people),
            'preperiod_installation_people':sum(p['installation_pre_period'] for p in people),
            'joint_cells':len({r['cell'] for r in rows}),
            'row10_supported':subset_stats(source_supported),
            'row10_person5_and_seen_source_item_supported':subset_stats(stronger),
            'shared_source_items':subset_stats(shared),
            'possible_gap_overlap':subset_stats([r for r in rows if r['ambiguous']]),
            'prefix_ambiguity':subset_stats([r for r in rows if r['prefix_ambiguous']]),
            'internal_gap_or_reset_ambiguity':subset_stats([r for r in rows if r['internal_ambiguous']]),
            'enclosed_positive_jump':subset_stats([r for r in rows if r['enclosed_positive_jump']]),
            'no_detected_gap':subset_stats(clean),
            'no_detected_gap_supported_row10_person5_and_seen_item':subset_stats(clean_supported),
            'recorded_other_quantiles':np.quantile([r['recorded_other'] for r in rows],[0,.1,.5,.9,1]).tolist() if rows else [],
            'repeat_count_per_person_quantiles':np.quantile([p['focal_repeat_rows'] for p in people],[0,.1,.5,.9,1]).tolist() if people else []}
    check('candidate_validation_no_consumed_people',all(not p['development_exposed'] for p in candidates if p['group']=='source_validation'))
    check('candidate_target_groups_exclude_audited_source_people',all(not p['development_exposed'] for p in candidates if p['group'] in ('smart','spaced')))
    check('candidate_counts_sum',sum(v['repeat_rows'] for v in output.values())==len(interval_rows))
    check('original8_and_candidate_18_consumed_preserved',len(consumed)==18)
    # Independent simple gap-overlap reconstruction for at most first10
    # candidates, using the same frozen metadata without new file access.
    gap_replay=0
    for p in candidates[:10]:
        all_a=person(p['uid']); a=all_a[(all_a['time']>=S)&(all_a['time']<E)]; before=all_a[all_a['time']<S]
        r,st,gaps=focal_intervals(a,before)
        for row in r:
            brute=any(lo<row['right'] and hi>row['left'] for lo,hi,kind,missing in gaps)
            assert brute==row['ambiguous']; gap_replay+=1
    check('gap_overlap_independent_brute_reconstruction',gap_replay>0,{'intervals_checked':gap_replay})
    original_result={'original_attrition':dict(excluded),'cohort':old_stats,'support':old_support,
         'missing_daily_files':calendar_missing,'source_audit_metadata_check':{'people':len(consumed),'rows':audited_rows,'first_count_histogram':dict(first),
          'increment_histogram':dict(increments),'violations_by_uid':violations_by_person,'total_violations':sum(violations_by_person.values()),
          'raw_answers_opened':False,'correctness_combination_counts_not_independently_redecoded':True}}
    (HERE/'ORIGINAL_AUDIT.json').write_text(json.dumps(original_result,indent=2)+'\n')
    candidate={'one_candidate_definition':'CANDIDATE_FREEZE.md','frozen_before_count':True,'period_UTC':['2020-03-01','2020-06-01'],
         'global_person_attrition':dict(stages),'per_arm_prequalification_stage_counts':{k:dict(v) for k,v in cohort_stage_by_arm.items()},
         'cohort':output,'source_fit_populated_cells_row10':len(supported_rows),'source_fit_populated_cells_row10_person5':len(supported_people),
         'source_fit_no_detected_gap_populated_cells_row10_person5':len(clean_support),
         'people':candidates,'unknowns':'No-detected-gap is not complete true practice; unseen items/tails and unknown preperiod experience remain. Counts do not establish discrimination or equivalence.',
         'current_or_future_response_fields_read':0,'fit_or_score':False}
    (HERE/'CANDIDATE_READINESS.json').write_text(json.dumps(candidate,indent=2)+'\n')
    (HERE/'CHECKS.json').write_text(json.dumps({'checks':checks,'all_passed':all(c['passed'] for c in checks),'check_count':len(checks)},indent=2)+'\n')
    exposure={'checked_utc':datetime.now(timezone.utc).isoformat(),'prior_cumulative_charge':7351194530,
         'review_additional_cached_metadata_document_charge':budget.total,'new_cumulative_charge':7351194530+budget.total,
         'review_limit':400000000,'cumulative_cap':8000000000,'read_entries':budget.entries,'NPY_projection':npyinfo,
         'METADATA_JSON_value_keys_materialized':decoded,'excluded_NPY_values_materialized':0,
         'raw_archive_answer_shard_response_NPZ_reads':0,'new_response_values_interpreted':0,'network':False,'fits_scores':False,
         'repeated_saved_summary_exposure':'A preliminary cat of listed SOURCE_FIELD_AUDIT.json rendered its already-saved source learn/correct cross-table, test-difference quantiles, and difficulty constancy summary. No raw values or target responses opened; no auxiliary fields used in selection/computation. This is a reviewer read mistake and repeated auxiliary summary exposure, not restored blindness.',
         'source_consumed_people_retained':18,'target_correct_reply_interpreted':0,'unknown_auxiliary_predictors_used':0,
         'elapsed_seconds':time.monotonic()-t0,'maxrss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'jobs_remaining':0,'source_artifacts_modified':False,'candidate_count':1}
    assert budget.total<=400000000 and exposure['new_cumulative_charge']<=8000000000
    assert exposure['maxrss_bytes_macos']<=1_000_000_000
    (HERE/'EXPOSURE.json').write_text(json.dumps(exposure,indent=2)+'\n')
    print(json.dumps({'all_checks_passed':all(c['passed'] for c in checks),'checks':len(checks),'original':old_stats,
          'candidate':output,'additional_byte_charge':budget.total,'maxrss_bytes':exposure['maxrss_bytes_macos'],'elapsed_seconds':exposure['elapsed_seconds']}))


if __name__=='__main__': main()
