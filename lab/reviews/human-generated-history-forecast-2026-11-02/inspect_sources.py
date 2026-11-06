"""Small read-only schema audit of already consumed source objects."""
import io
import json
import zipfile
import openpyxl
from independent import OLD, AUTHOR, OUT, READS, blob, obj, save, utc, usage

path = OLD / 'experiments/source_audit/sources/pregen_sequence_0.xlsx'
b = blob(path)
with zipfile.ZipFile(io.BytesIO(b)) as z:
    expanded = sum(x.file_size for x in z.infolist())
wb = openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
it = wb.active.values
header = next(it)
sample = [dict(zip(header, next(it))) for _ in range(2)]
wb.close()
data = obj(AUTHOR / 'FORECAST_INPUTS.json')
result = dict(utc=utc(), workbook_header=header, first_two_rows=sample,
              expanded_zip_member_allowance=expanded * 2,
              observation_calibration=data['observation_calibration'],
              omission_law=data['omission_law'], teacher_law=data['teacher_law'],
              prefix_convention=data['prefix_convention'], **usage())
save('SOURCE_SCHEMA.json', result)
print(json.dumps(result, indent=2))
