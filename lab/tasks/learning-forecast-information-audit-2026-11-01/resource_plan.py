"""Bound cached first4000 assets from existing metadata; read no raw values."""
from pathlib import Path
import datetime as dt
import json

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
C = ROOT/'campaigns/population_learning_transport_2026-10-28'


def main():
    freeze = json.loads((C/'protocols/FREEZE.json').read_text())
    subjects = freeze['source_primary_subjects']
    sessions = json.loads((C/'artifacts/coverage/SESSIONS.json').read_text())
    metadata = json.loads((C/'artifacts/coverage/FILE_METADATA.json').read_text())
    bypath = {x['path']: x for x in metadata}
    rows = []
    for subject in subjects:
        remaining = 4000
        for session in (r for r in sessions if r['subject'] == subject):
            if not remaining:
                break
            take = min(remaining, session['rows'])
            remaining -= take
            for field, path in session['files'].items():
                m = bypath[path]
                # Conservative full-containing-table numeric payload, including unselected fields.
                if field == 'table':
                    uncompressed = int(m['rows']) * len(m['columns']) * 16
                else:
                    uncompressed = int(m['expected_bytes'])
                rows.append(dict(subject=subject, path=path, field=field,
                                 returned_rows=take, containing_rows=session['rows'],
                                 containing_file_bytes=int(m['bytes']),
                                 conservative_decoded_bytes=uncompressed))
        assert remaining == 0
    frozen_bytes = sum(x['bytes'] for x in freeze['files'])
    raw_charge = sum(x['containing_file_bytes']+x['conservative_decoded_bytes'] for x in rows)
    metadata_read = sum((C/p).stat().st_size for p in ('protocols/FREEZE.json',
                          'artifacts/coverage/SESSIONS.json', 'artifacts/coverage/FILE_METADATA.json'))
    # Reader load_scored/_read each reads SESSIONS once; _permit hashes two small manifests.
    repeated_metadata = 2*24*(C/'artifacts/coverage/SESSIONS.json').stat().st_size
    repeated_metadata += 24*((C/'protocols/FREEZE.json').stat().st_size+
                             (C/'protocols/SOURCE_FORECASTS.json').stat().st_size)
    first = json.loads((OUT/'FIRST_CALCULATION.json').read_text())['resources']['conservative_read_charge_bytes']
    charge = first+metadata_read+2*frozen_bytes+raw_charge+repeated_metadata+80_000_000
    assert charge < 400_000_000
    result = dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), files=rows,
                  first_calculation_charge=first, resource_plan_metadata_read=metadata_read,
                  two_strict_freeze_passes_bytes=2*frozen_bytes,
                  selected_containing_raw_charge=raw_charge,
                  repeated_reader_metadata_charge=repeated_metadata,
                  artifacts_code_runtime_decodes_and_margin_allowance=80_000_000,
                  total_conservative_planned_charge_bytes=charge,
                  cap_bytes=400_000_000, anticipated_peak_rss_bytes=500_000_000,
                  physical_io_and_actual_library_decode_unknown=True,
                  note='Full containing rows charged, but only the authorized first4000 may be returned or interpreted.')
    (OUT/'RESOURCE_PLAN.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='files'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
