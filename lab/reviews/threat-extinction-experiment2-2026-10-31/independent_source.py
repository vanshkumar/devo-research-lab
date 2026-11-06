"""Independent, offline SPSS/log reader for the consumed dxpb3 v1 archive.

No author helper is imported. Only SPSS $FL2 dictionary/byte-code formats used
in these two cached files are supported. Downloaded material is data only.
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

HERE = pathlib.Path(__file__).resolve().parent
AUTHOR = HERE.parents[1] / 'tasks/threat-extinction-experiment2-2026-10-31'
READ_BYTES = 0

def read(path):
    global READ_BYTES
    b = pathlib.Path(path).read_bytes()
    READ_BYTES += len(b)
    return b

def sav_decode(data):
    def i(pos):
        return struct.unpack_from('<i', data, pos)[0]
    def d(pos):
        return struct.unpack_from('<d', data, pos)[0]
    assert data[:4] == b'$FL2'
    slots, compression, cases, bias = i(68), i(72), i(80), d(84)
    cursor, dictionary, ext = 176, [], {}
    while True:
        record = i(cursor)
        cursor += 4
        if record == 999:
            cursor += 4
            break
        if record == 2:
            typ, labeled, nmiss = i(cursor), i(cursor+4), i(cursor+8)
            short = data[cursor+20:cursor+28].decode('ascii').strip()
            cursor += 28
            label = ''
            if labeled:
                length = i(cursor)
                cursor += 4
                label = data[cursor:cursor+length].decode('utf8', 'replace')
                cursor += 4*((length+3)//4)
            missing = [d(cursor+8*j) for j in range(abs(nmiss))]
            cursor += 8*abs(nmiss)
            dictionary.append({'short':short, 'type':typ, 'label':label, 'missing':missing})
        elif record == 3:
            length = i(cursor)
            cursor += 4
            for _ in range(length):
                cursor += 8
                n = data[cursor]
                cursor += 8*((n+1+7)//8)
        elif record == 4:
            cursor += 4+4*i(cursor)
        elif record == 6:
            cursor += 4+80*i(cursor)
        elif record == 7:
            subtype, size, count = struct.unpack_from('<iii', data, cursor)
            cursor += 12
            ext[subtype] = data[cursor:cursor+size*count]
            cursor += size*count
        else:
            raise ValueError(('unsupported dictionary record', record, cursor))
    assert len(dictionary) == slots
    mapping = dict(x.split('=',1) for x in ext.get(13,b'').decode('utf8').split('\t') if '=' in x)
    for v in dictionary:
        v['name'] = mapping.get(v['short'], v['short'])
    blocks = []
    if compression == 0:
        blocks = [data[cursor+8*j:cursor+8*j+8] for j in range(slots*cases)]
    else:
        assert compression == 1
        while len(blocks) < slots*cases:
            codes = data[cursor:cursor+8]
            assert len(codes) == 8
            cursor += 8
            for code in codes:
                if code == 0:
                    continue
                if code == 252:
                    assert len(blocks) >= slots*cases
                    break
                if code == 253:
                    value = data[cursor:cursor+8]
                    cursor += 8
                elif code == 254:
                    value = b' '*8
                elif code == 255:
                    value = None
                else:
                    value = struct.pack('<d', code-bias)
                blocks.append(value)
                if len(blocks) == slots*cases:
                    break
    out = []
    for n in range(cases):
        row = {}
        for j,v in enumerate(dictionary):
            if v['type'] < 0:
                continue
            value = blocks[n*slots+j]
            if v['type'] > 0:
                parts = blocks[n*slots+j:n*slots+j+(v['type']+7)//8]
                value = b''.join(x if x is not None else b' '*8 for x in parts)[:v['type']].decode('utf8').rstrip()
            elif value is not None:
                value = struct.unpack('<d', value)[0]
                if value < -1e300:
                    value = None
            row[v['name']] = value
        out.append(row)
    return dictionary, out

def source():
    global READ_BYTES
    archive = read(AUTHOR/'sources/experiment2.zip')
    assert len(archive) == 106395
    assert hashlib.md5(archive).hexdigest() == 'a8a3e15455a7342cd6d9e94872db4859'
    assert hashlib.sha256(archive).hexdigest() == '6d38c558f4ef6e8991b1f59de7a5c2bb50fcee8b55285f5db9c2fa532141298f'
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        listing = [{'name':x.filename,'bytes':x.file_size,'compressed':x.compress_size,'crc32':x.CRC} for x in z.infolist()]
        assert sum(x['bytes'] for x in listing) == 335411
        # Use explicit updates: no closure mutation or cached author parse.
        selected = {}
        for suffix in ['SCR data_SE_exp2.sav','US expectancy_SE_exp2.sav','Secondary extinction exp2.dat']:
            name = next(n for n in z.namelist() if n.endswith('/'+suffix))
            b = z.read(name)
            READ_BYTES += len(b)
            selected[suffix] = b
        sd,sr = sav_decode(selected['SCR data_SE_exp2.sav'])
        ed,er = sav_decode(selected['US expectancy_SE_exp2.sav'])
        logs = list(csv.DictReader(io.StringIO(selected['Secondary extinction exp2.dat'].decode('utf-8-sig')),delimiter='\t'))
    return {'archive': listing, 'scr_dictionary':sd,'expectancy_dictionary':ed,
            'scr':{int(x['PP_number']):x for x in sr},'expectancy':{int(x['PP_number']):x for x in er},
            'log':logs,'members':{n:hashlib.sha256(b).hexdigest() for n,b in selected.items()}}

def write(name, obj):
    (HERE/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')

def main():
    s = source()
    ids = sorted(s['scr'])
    assert ids == sorted(s['expectancy']) and len(ids)==60
    transformed = [0. if (v or 0)/1000 <= .02 else (v/1000)**.5 for p in ids for c in ['CSplus1','CSplus2','CSmin'] for n in range(6,12) for v in [s['scr'][p]['GSR1'+c+'_'+str(n)]] if v is not None]
    out = {'utc':dt.datetime.now(dt.timezone.utc).isoformat(),
           'command':'python3 lab/reviews/threat-extinction-experiment2-2026-10-31/independent_source.py',
           'independent_reader':True,'imports_author_helpers':False,'archive_pins_pass':True,
           'ids':ids,'paired_sav_ids':len(ids),'log_rows':len(s['log']),
           'log_fields':list(s['log'][0]),'first_log_row':s['log'][0],
           'physiology_extinction_finite':len(transformed),'physiology_extinction_zero_count':sum(x==0 for x in transformed),
           'physiology_extinction_sum_sqrt_microS':sum(transformed),
           'PP120_condition':s['scr'][120]['Conditie'],
           'PP120_extinction_missing':sum(s['scr'][120]['GSR1'+c+'_'+str(n)] is None for c in ['CSplus1','CSplus2','CSmin'] for n in range(6,12)),
           'member_sha256':s['members'],'scientific_bytes_read':READ_BYTES,
           'conservative_stage_charge_bytes':2000000,
           'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           'public_operations':0,'ingress_bytes':0,'jobs_after_command':0}
    write('FIRST_CALCULATION.json',out)
    print(json.dumps(out,indent=2))

if __name__=='__main__':
    main()
