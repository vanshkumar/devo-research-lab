"""Inspect only the already acquired ZIP prefix; never fetch or repair it."""
import binascii
import csv
import hashlib
import io
import json
import pathlib
import resource
import struct
import zlib

ROOT = pathlib.Path(__file__).resolve().parent

def main():
    data = (ROOT / 'hc3_metadata.zip').read_bytes()
    position = 0
    members = []
    decoded = 0
    while data[position:position + 4] == b'PK\x03\x04':
        header = struct.unpack_from('<IHHHHHIIIHH', data, position)
        _, version, flags, method, mt, md, crc, compressed, uncompressed, nl, xl = header
        start = position + 30
        name = data[start:start + nl].decode('utf-8')
        payload = start + nl + xl
        row = {'name': name, 'compressed': compressed, 'uncompressed': uncompressed,
               'flags': flags, 'method': method, 'offset': position}
        members.append(row)
        descriptor_size = 0
        if flags & 8:
            assert method == 8
            decoder = zlib.decompressobj(-15)
            value = decoder.decompress(data[payload:], 50_000_001)
            if not decoder.eof:
                row['stop'] = 'partial deflate member or local decode cap'
                break
            compressed = len(data[payload:]) - len(decoder.unused_data)
            end = payload + compressed
            signature_size = 4 if data[end:end+4] == b'PK\x07\x08' else 0
            if end + signature_size + 12 > len(data):
                row['stop'] = 'partial data descriptor'
                break
            crc, declared_compressed, uncompressed = struct.unpack_from('<III', data, end + signature_size)
            assert compressed == declared_compressed
            descriptor_size = signature_size + 12
            row.update(compressed=compressed, uncompressed=uncompressed)
        if payload + compressed > len(data):
            row['stop'] = 'partial member; no further acquisition authorized by this script'
            break
        if uncompressed > 50_000_000 or decoded + uncompressed > 100_000_000:
            row['stop'] = 'local decode cap'
            break
        block = data[payload:payload + compressed]
        if not flags & 8:
            value = zlib.decompress(block, -15) if method == 8 else block
        assert method in (0, 8)
        assert len(value) == uncompressed
        assert binascii.crc32(value) & 0xffffffff == crc
        decoded += len(value)
        row['sha256'] = hashlib.sha256(value).hexdigest()
        leaf = pathlib.PurePosixPath(name).name
        if leaf.endswith(('.csv', '.sql', '.txt')):
            (ROOT / ('decoded_' + leaf)).write_bytes(value)
            if leaf.endswith('.csv'):
                rows = list(csv.reader(io.StringIO(value.decode('utf-8-sig'))))
                row.update(row_count=len(rows), first_three_rows=rows[:3])
            elif len(value) < 10_000:
                row['text'] = value.decode('utf-8', errors='replace')
        position = payload + compressed + descriptor_size
    report = {'acquired_prefix_bytes': len(data), 'decoded_complete_member_bytes': decoded,
              'central_directory_present': b'PK\x05\x06' in data,
              'complete_archive_hash_certified': False, 'members': members,
              'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (ROOT / 'PREFIX_INSPECTION.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
