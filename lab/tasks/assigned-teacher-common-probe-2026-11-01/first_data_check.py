"""Original, first-identifier-only development record audit; no forecast fitting.

The first contiguous participant in the published CSV is development by the
predeclared file-order rule. Stop before interpreting any other participant.
"""
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import resource
import sys

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'Crossact_data.csv'
EXPECTED_SIZE = 4015641
EXPECTED_GIT_BLOB = '622d0e34305f7208ef0ec77a0dc6951add1a161c'

b = DATA.read_bytes()
actual_blob = hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
assert len(b) == EXPECTED_SIZE
assert actual_blob == EXPECTED_GIT_BLOB, (actual_blob, EXPECTED_GIT_BLOB)
pin = {'name': DATA.name, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(),
       'git_blob_sha1': actual_blob, 'expected_git_blob_match': True}
del b

rows = []
next_subject_metadata = None
with DATA.open(newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    header = reader.fieldnames
    first_subject = None
    for row in reader:
        if first_subject is None:
            first_subject = row['subject']
        if row['subject'] != first_subject:
            next_subject_metadata = row['subject']
            break
        rows.append(row)
    byte_position_upper = f.buffer.tell()

assert rows
metadata = {k: rows[0][k] for k in ('subject','experiment_name','version','age_group','ambiguity_condition')}
phase_counts = Counter(r['trialType'] for r in rows)
learning = [r for r in rows if r['trialType'] == 'learning']
selection = [r for r in rows if r['trialType'] == 'selection']
tests = [r for r in rows if r['trialType'] == 'test']
indices = [int(float(r['trialIndex'])) for r in rows]
assert indices == list(range(indices[0],indices[0]+len(rows))), indices
print('DEVELOPMENT_METADATA_AND_COUNTS', metadata, dict(phase_counts))
assert metadata['version'] == 'kids2B', metadata
assert len(learning) == 9, len(learning)
assert len(selection) == 2, len(selection)
assert len(tests) == 6, len(tests)
assert max(int(float(r['trialIndex'])) for r in learning) < min(int(float(r['trialIndex'])) for r in selection)
assert max(int(float(r['trialIndex'])) for r in selection) < min(int(float(r['trialIndex'])) for r in tests)

by_image = Counter()
coitems = defaultdict(set)
pair_counts = Counter()
for row in learning:
    a, c = row['image1'], row['image2']
    assert a != c
    by_image.update([a,c])
    coitems[a].add(c)
    coitems[c].add(a)
    pair_counts[tuple(sorted([a,c]))] += 1
assert len(by_image) == 6 and set(by_image.values()) == {3}, by_image

chosen = Counter(r['choiceImage'] for r in selection)
random_paired = Counter(r['randomImage'] for r in selection if r['randomImage'] not in ('','NA'))
assert all(r['choiceImage'] in by_image for r in selection)
targets = [r['targetImage'] for r in tests]
assert Counter(targets) == Counter({k:1 for k in by_image}), targets

essential_fields = ['trialIndex','trialNum','trialType','image1','image2','label1','label2',
                    'choiceImage','randomImage','choiceLabel','randomLabel','label',
                    'targetImage','targetType','choiceLocation','choice_count','chosen',
                    'isRight','rt','High1','High2','High3','High4','Low1','Low2','Low3','Low4']
development_rows = [{k:r.get(k) for k in essential_fields} for r in rows]
checks = []
for r in tests:
    target = r['targetImage']
    available = [r.get('image'+str(i),'') for i in range(1,7)]
    assert set(available) == set(by_image), available
    loc = r['choiceLocation']
    if loc.startswith('pos'):
        selected_image = available[int(loc[3:])-1]
    elif r.get('choiceImage') not in ('','NA'):
        selected_image = r['choiceImage']
    else:
        raise ValueError('No original selected image/location for development test')
    derived = int(selected_image == target)
    supplied = int(float(r['isRight']))
    assert derived == supplied
    if r['choice_count'] not in ('','NA'):
        assert int(float(r['choice_count'])) == chosen[target]
    if r['chosen'] not in ('','NA'):
        assert int(float(r['chosen'])) == int(chosen[target]>0)
    checks.append({'trialIndex':int(float(r['trialIndex'])), 'targetImage':target,
                   'targetType':r['targetType'], 'prior_fixed_exposures':by_image[target],
                   'distinct_prior_partners':len(coitems[target]),
                   'self_chosen_additional_exposures':chosen[target],
                   'random_paired_additional_exposures':random_paired[target],
                   'original_selected_image':selected_image,
                   'derived_correct':derived,'supplied_correct':supplied,
                   'rt_ms':float(r['rt'])})

v1 = (ROOT/'crossact_v1.html').read_text()
v4 = (ROOT/'crossact_v4.html').read_text()
source_checks = {
    'v4_novel_word_and_object_identity_shuffles_present': all(s in v4 for s in ('shuffle(allNovelItems)','shuffle(allNovelWords)')),
    'v1_participant_condition_loaded_from_external_URL': "getParamFromURL( 'cond' )" in v1,
    'v1_default_high_condition_present': 'var condition="high"' in v1,
    'v4_fixed_nine_initial_exposures': 'var numTB = 3' in v4 and 'var numTrialsCTB = 3' in v4,
    'v4_fixed_two_sampling_trials': 'var numLabelSelectTrialsPerBlock = 2' in v4,
    'v4_all_six_test_targets_scheduled_before_execution': 'var testTrialsIndex=[0,1,2,3,4,5]' in v4,
    'v4_all_training_sampling_test_timeline_built_before_start': 'timeline = timeline.concat(trainingList);' in v4 and 'timeline = timeline.concat(testList);' in v4,
    'item_level_ambiguity_manipulation_with_random_novel_identities': True,
    'v4_between_person_independent_teacher_regime_variation': False,
    'independent_between_learner_teacher_assignment_certified': False,
    'reason': 'V4 gives all learners the same within-person teaching structure with random novel identities; extra sampling is learner-selected. V1 URL parameter branches do not certify allocation independence; upstream allocation is not certified.',
    'deployed_version_link_certified': False,
    'test_feedback_plugin_certified': 'V4 finalize_test computes correctness and ends; no correct-item display or replay call occurs in that function. Uncalled playLearningTrial helper is separate; no runtime deployment certification.',
}
out = {'created_at_utc':datetime.now(timezone.utc).isoformat(), 'command':'.venv/bin/python lab/tasks/assigned-teacher-common-probe-2026-11-01/first_data_check.py',
       'status':'PARTIAL_ORIGINAL_RECORD_CHECK_NOT_QUALIFYING_ASSIGNED_TEACHER_GATE',
       'qualifying_first_measurement_milestone':False,
       'source_pin':pin,'development_selection':'first contiguous subject in original CSV file order, fixed before response parsing',
       'development_metadata':metadata,'development_rows':len(rows),'phase_counts':dict(phase_counts),
       'trial_index_sequence':indices,'training_pair_counts':[{ 'images':list(k),'count':v} for k,v in sorted(pair_counts.items())],
       'common_probe_checks':checks,'probe_total_correct':sum(x['derived_correct'] for x in checks),
       'probe_opportunities':len(checks),'source_code_checks':source_checks,
       'exposure': {'original_csv_all_bytes_acquired_hashed':True,'original_csv_all_rows_decoded':False,
                    'development_subject_fully_interpreted':first_subject,
                    'next_subject_first_row_csv_tokenized_but_values_not_interpreted_or_rendered':next_subject_metadata,
                    'decoder_file_position_upper_bytes':byte_position_upper,
                    'other_subject_response_scores_or_aggregates': 'UNRUN',
                    'demographics_and_free_text': 'not used or rendered; contained in acquired/hash bytes and development-row CSV parsing'},
       'resources': {'data_hash_read_bytes':EXPECTED_SIZE,'csv_prefix_read_upper_bytes':byte_position_upper,
                     'peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                     'physical_io':'unknown','python':sys.version,'scientific_processes':1,'numerical_threads':1},
       'unrun':['main fitting','forecast scoring','new evaluation response interpretation','between-teacher comparison','sensitivity or coverage controls','independent review']}
(ROOT/'DEVELOPMENT_ROWS.json').write_text(json.dumps(development_rows,indent=2)+'\n')
(ROOT/'FIRST_DATA_CHECK.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
