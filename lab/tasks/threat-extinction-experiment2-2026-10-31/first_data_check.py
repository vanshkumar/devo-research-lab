"""Read the numeric dictionary and first case of the supplied SPSS exports.

main() reads each first case only. The reusable reader accepts explicit case
and variable masks for later authorized development/evaluation stages.
The Inquisit prefix previously exposed IDs109 and110 is retained as development.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import pathlib
import resource
import struct
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent

def first_sav(b, case_limit=1, selected=None, case_indices=None):
    assert b[:4] == b'$FL2', b[:4]
    integer = lambda p: struct.unpack_from('<i', b, p)[0]
    slots, compression, ncases = integer(68), integer(72), integer(80)
    bias = struct.unpack_from('<d', b, 84)[0]
    p, variables, extensions = 176, [], {}
    while True:
        record = integer(p)
        p += 4
        if record == 2:
            typ, has_label, nmiss = integer(p), integer(p+4), integer(p+8)
            name = b[p+20:p+28].decode('ascii').rstrip()
            p += 28
            label = ''
            if has_label:
                n = integer(p)
                p += 4
                label = b[p:p+n].decode('utf8', errors='replace')
                p += ((n+3)//4)*4
            missing = [struct.unpack_from('<d', b, p+8*k)[0] for k in range(abs(nmiss))]
            p += abs(nmiss)*8
            variables.append({'name': name, 'type': typ, 'label': label, 'missing': missing})
        elif record == 3:
            n = integer(p)
            p += 4
            for _ in range(n):
                p += 8
                nlabel = b[p]
                p += ((nlabel + 1 + 7)//8)*8
        elif record == 4:
            n = integer(p)
            p += 4 + n*4
        elif record == 6:
            n = integer(p)
            p += 4 + n*80
        elif record == 7:
            subtype, size, count = integer(p), integer(p+4), integer(p+8)
            p += 12
            if subtype in [13, 14, 20]:
                extensions[str(subtype)] = b[p:p+size*count].decode('utf8', errors='replace')
            p += size*count
        elif record == 999:
            p += 4
            break
        else:
            raise ValueError(('unknown dictionary record', record, p-4))
    names = dict(x.split('=', 1) for x in extensions.get('13', '').split('\t') if '=' in x)
    for v in variables:
        v['long_name'] = names.get(v['name'], v['name'])
    assert len(variables) == slots, (len(variables), slots)
    allowed_slots = set(range(slots)) if selected is None else set()
    if selected is not None:
        for k, v in enumerate(variables):
            if v['long_name'] in selected:
                allowed_slots.update(range(k, k + max(1, (v['type']+7)//8)))
    def keep(index):
        return (index % slots in allowed_slots and
                (case_indices is None or index // slots in case_indices))
    values = []
    target = slots * min(case_limit, ncases)
    if compression == 0:
        values = [struct.unpack_from('<d', b, p+8*k)[0] if keep(k) else None for k in range(target)]
    elif compression == 1:
        while len(values) < target:
            codes = b[p:p+8]
            p += 8
            for c in codes:
                if c == 0:
                    continue
                if c == 252:
                    break
                if c == 253:
                    value = struct.unpack_from('<d', b, p)[0] if keep(len(values)) else None
                    p += 8
                elif c == 254:
                    value = '        '
                elif c == 255:
                    value = None
                else:
                    value = c - bias if keep(len(values)) else None
                values.append(value)
                if len(values) == target:
                    break
    else:
        raise ValueError(('unsupported compression', compression))
    assert len(values) == target
    def chunk(value):
        if value == '        ':
            return b'        '
        return struct.pack('<d', value) if value is not None else b' '*8
    cases = []
    for offset in range(0, target, slots):
        case = {}
        if case_indices is not None and offset // slots not in case_indices:
            cases.append(case)
            continue
        for k, v in enumerate(variables):
            if v['type'] < 0 or (selected is not None and v['long_name'] not in selected):
                continue
            value = values[offset+k]
            if v['type'] > 0:
                count = (v['type'] + 7)//8
                value = b''.join(chunk(x) for x in values[offset+k:offset+k+count])[:v['type']].decode('utf8', errors='replace').rstrip()
            case[v['long_name']] = value
        cases.append(case)
    return {'ncases_header': ncases, 'case_slots': slots, 'compression': compression,
            'dictionary': variables, 'first_case': cases[0], 'cases': cases, 'dictionary_extensions': extensions}

def main():
    z = zipfile.ZipFile(ROOT / 'sources/experiment2.zip')
    result = {'command': 'python3 lab/tasks/threat-extinction-experiment2-2026-10-31/first_data_check.py',
              'utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'sav': {}}
    for suffix in ['SCR data_SE_exp2.sav', 'US expectancy_SE_exp2.sav']:
        name = next(n for n in z.namelist() if n.endswith('/' + suffix))
        b = z.read(name)
        result['sav'][suffix] = first_sav(b)
        result['sav'][suffix]['sha256'] = hashlib.sha256(b).hexdigest()
    n = next(n for n in z.namelist() if n.endswith('/Secondary extinction exp2.dat'))
    rows = []
    with z.open(n) as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'), delimiter='\t')
        header = reader.fieldnames
        for row in reader:
            rows.append(row)
            if len(rows) >= 48:
                break
    result['inquisit_header'] = header
    result['first_48_rows'] = rows
    result['scientific_read_charge_bytes'] = 2000000
    result['peak_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result['participant_pairing_and_chronology_certification'] = 'PENDING_EXAMINATION'
    (ROOT / 'FIRST_DATA_CHECK.json').write_text(json.dumps(result, indent=2) + '\n')
    for file, d in result['sav'].items():
        print(file, 'ncases', d['ncases_header'], 'slots', d['case_slots'], 'compression', d['compression'])
        print('VARIABLES', [(v['long_name'], v['label']) for v in d['dictionary']])
        print('FIRST_CASE', json.dumps(d['first_case']))
    print('INQUISIT_HEADER', header)
    print('FIRST_48_ROWS', json.dumps(rows))
    print('RESOURCES', result['scientific_read_charge_bytes'], result['peak_rss_bytes'])

if __name__ == '__main__':
    main()
