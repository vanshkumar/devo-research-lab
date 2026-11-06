"""Source-support audit. This does not fit or score a behavioral forecast."""
import collections
import csv
import datetime
import hashlib
import json
import pathlib
import resource

ROOT = pathlib.Path(__file__).resolve().parent

def read_rows(name):
    return list(csv.reader((ROOT / ('decoded_' + name)).open(newline='')))

def main():
    # Column positions are pinned in decoded_hc3-tables.sql and the source PDF.
    cell_rows = read_rows('hc3-cell.csv')
    cells = {int(r[0]): {'topdir':r[1], 'animal':r[2], 'region':r[5], 'type':r[14]}
             for r in cell_rows}
    sess_rows = read_rows('hc3-session_a.csv')
    sessions = [dict(zip(sess_rows[0], r)) for r in sess_rows[1:]]
    sessions_by_id = {int(r['id']):r for r in sessions}
    files = {r[1]: {'topdir':r[0], 'compressed_bytes':int(r[2])}
             for r in read_rows('hc3-file.csv')}
    count_rows = read_rows('hc3-spike_count.csv')
    counts = {(int(r[0]),int(r[1])):int(r[2]) for r in count_rows[1:]}
    assert len(sessions_by_id) == len(sessions)
    assert len(cells) == len(cell_rows)
    assert len(counts) == len(count_rows)-1
    assert all(c in cells and s in sessions_by_id for c,s in counts)
    assert all(cells[c]['topdir'] == sessions_by_id[s]['topdir'] for c,s in counts)
    assert all(v >= 0 for v in counts.values())
    by_behavior = collections.defaultdict(lambda: {'all_sessions':0, 'listed_payloads':0})
    for s in sessions:
        by_behavior[s['behavior']]['all_sessions'] += 1
        by_behavior[s['behavior']]['listed_payloads'] += s['session'] in files

    # Fixed source-support example: first metadata-ordered Tmaze / sleep / Tmaze
    # triplet in a single topdir, allowing several consecutive sleep rows.
    # Row order is not certified elapsed acquisition timing.
    candidates = []
    by_topdir = collections.defaultdict(list)
    for s in sessions:
        by_topdir[s['topdir']].append(s)
    for topdir in sorted(by_topdir):
        group = sorted(by_topdir[topdir], key=lambda r:int(r['id']))
        for i,s in enumerate(group):
            if s['behavior'] != 'sleep':
                continue
            before = next((t for t in reversed(group[:i]) if t['behavior'] != 'sleep'), None)
            after = next((t for t in group[i+1:] if t['behavior'] != 'sleep'), None)
            if before and after and before['behavior'] == after['behavior'] == 'Tmaze':
                candidates.append((topdir, int(s['id']), before,s,after))
    # Also quantify the documented wheel-alternation task. These are metadata
    # candidates, not certified trial-level learning records.
    alternation_pairs = {}
    for behavior in ('Tmaze','Mwheel'):
        pairs = {}
        for topdir, group in by_topdir.items():
            group = sorted(group, key=lambda r:int(r['id']))
            for i,s in enumerate(group):
                if s['behavior'] != 'sleep':
                    continue
                before = next((t for t in reversed(group[:i]) if t['behavior'] != 'sleep'), None)
                after = next((t for t in group[i+1:] if t['behavior'] != 'sleep'), None)
                if before and after and before['behavior'] == after['behavior'] == behavior:
                    key = (before['session'],after['session'])
                    pairs[key] = {'topdir':topdir, 'before':key[0], 'after':key[1],
                                  'both_task_payloads_listed':all(k in files for k in key),
                                  'combined_task_archive_bytes':sum(files[k]['compressed_bytes'] for k in key)
                                     if all(k in files for k in key) else None}
        listed = [p for p in pairs.values() if p['both_task_payloads_listed']]
        alternation_pairs[behavior] = {'unique_task_pairs':len(pairs),
                                      'both_task_payloads_listed':len(listed),
                                      'smallest_listed_pair':min(listed,key=lambda p:p['combined_task_archive_bytes'])
                                         if listed else None}
    example = None
    if candidates:
        topdir, sid, before, sleep, after = sorted(candidates, key=lambda x:(x[0], x[1]))[0]
        ids = [int(t['id']) for t in (before,sleep,after)]
        ca1 = [c for c in sorted(cells) if cells[c]['topdir']==topdir
               and cells[c]['region']=='CA1' and cells[c]['type']=='p'
               and all((c,s) in counts for s in ids)]
        outputs = []
        if ca1:
            cid = ca1[0]
            for s in (before,sleep,after):
                n = counts[(cid,int(s['id']))]
                duration = float(s['duration'])
                assert duration > 0
                outputs.append({'session':s['session'],'sessId':int(s['id']),
                                'behavior_label':s['behavior'], 'duration_seconds':duration,
                                'exported_spike_count':n,'rate_spikes_per_second':n/duration,
                                'listed_payload':s['session'] in files,
                                'payload_compressed_bytes':files.get(s['session'],{}).get('compressed_bytes'),
                                'familiarity_code':s['familiarity'], 'problem':s['problem']})
            example = {'animal':cells[cid]['animal'], 'topdir':topdir, 'cellId':cid,
                       'cell_region':'CA1','source_class':'p', 'records':outputs,
                       'interpretation':'exported session-total counts and task labels only',
                       'performance_scores_available_in_these_tables':False,
                       'exact_elapsed_linkage_certified':False,
                       'future_session_spike_sorting_privilege':True}

    inputs = {}
    for name in ('hc3-cell.csv','hc3-session_a.csv','hc3-file.csv','hc3-spike_count.csv'):
        p = ROOT / ('decoded_' + name)
        inputs[p.name] = {'bytes':p.stat().st_size, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    report = {'calculated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status':'PARTIAL_SOURCE_SUPPORT_ONLY; required linked neural-performance milestone NOT earned',
              'families_deliberately_targeted':['hc-3','hc-11/Grosmark'],
              'cells':len(cells),'animals':len({c['animal'] for c in cells.values()}),
              'all_session_rows':len(sessions),'listed_payload_sessions':len(files),
              'spike_count_rows':len(counts),'all_count_identity_joins_pass':True,
              'behavior_support':dict(sorted(by_behavior.items())),
              'Tmaze_sleep_Tmaze_metadata_candidates':len(candidates),
              'alternation_task_archive_support':alternation_pairs,
              'first_source_defined_metadata_order_example':example,
              'behavioral_choices_rewards_or_performance_values_read':0,
              'raw_spike_timestamps_read':0,'raw_or_continuous_LFP_read':0,
              'neural_vs_behavior_forecast_compared':False,
              'inputs':inputs, 'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (ROOT / 'FIRST_DATA_CHECK.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
