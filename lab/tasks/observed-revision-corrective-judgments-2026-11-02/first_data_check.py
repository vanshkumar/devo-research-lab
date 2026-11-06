"""Reconstruct the first observed sentence edit and all seven supplied votes."""
import csv
import datetime as dt
import difflib
import hashlib
import io
import json
import pathlib
import resource
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent

def main():
    payload = (ROOT / 'revision_improvements.csv.zip').read_bytes()
    assert hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest() == '00581db66ef19161a18a5eaf1fb92495a11bc527'
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        raw = archive.read('annotated_revision_improvements.csv')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    row = next(reader)
    before, after = row['S1'], row['S2']
    labels = [row['Label' + str(i)] for i in range(1, 8)]
    assert set(labels) <= {'Better', 'NotBetter'}
    words1, words2 = before.split(), after.split()
    changes = [{'operation': op, 'before_positions_zero_based': [a, b], 'after_positions_zero_based': [c, d], 'before_tokens': words1[a:b], 'after_tokens': words2[c:d]} for op, a, b, c, d in difflib.SequenceMatcher(None, words1, words2, autojunk=False).get_opcodes() if op != 'equal']
    # A separate literal word-order audit for this actual first row.
    assert 'maintain important and make connections' in before
    assert 'maintain and make important connections' in after
    assert len(words1) == len(words2) == 19
    assert sorted(words1) == sorted(words2)
    better_votes = sum(x == 'Better' for x in labels)
    assert better_votes == 7
    result = {
        'calculated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'archive_sha256': hashlib.sha256(payload).hexdigest(), 'csv_sha256': hashlib.sha256(raw).hexdigest(),
        'csv_record_one_based': 1, 'before': before, 'after': after,
        'word_counts': [len(words1), len(words2)], 'bag_of_words_unchanged': sorted(words1) == sorted(words2),
        'sequence_matcher_changes': changes, 'seven_labels': labels, 'better_votes': better_votes,
        'majority': 'Better' if better_votes >= 4 else 'NotBetter',
        'fields': reader.fieldnames,
        'identifiers': {'learner': None, 'draft_pair': None, 'assignment': None, 'rater_identity': None, 'only_location': 'CSV data record 1'},
        'meaning': 'Observed original/revised sentence pair and seven posthoc evaluation slots; this record is NOT proof of distinct rater identities, original learner/draft join, feedback received, or causal learning.',
        'required_milestone': 'PARTIAL: actual edit/quality votes reconstructed, but original learner/draft/assignment linkage absent from this CSV and remains uncertified.',
        'exposure': 'Whole CSV inflated and UTF8 decoded; only header/first CSV record tokenized, labels/comments interpreted. Buffering may touch additional characters; all decoded bytes remain exposed.',
        'rss_bytes_macos': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    }
    (ROOT / 'FIRST_DATA_CHECK.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
