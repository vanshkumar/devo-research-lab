"""Read the small source workbook's cell values with the standard library."""
import json
import pathlib
import zipfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
with zipfile.ZipFile(ROOT / "source/Stim-struct.xlsx") as z:
    strings = ["".join(x.itertext()) for x in ET.fromstring(z.read("xl/sharedStrings.xml"))] if "xl/sharedStrings.xml" in z.namelist() else []
    print(z.read("xl/workbook.xml").decode())
    out = {}
    for name in z.namelist():
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
            rows = []
            for row in ET.fromstring(z.read(name)).findall("s:sheetData/s:row", ns):
                vals = {}
                for cell in row:
                    v = cell.find("s:v", ns)
                    value = v.text if v is not None else "".join(cell.itertext())
                    if cell.attrib.get("t") == "s":
                        value = strings[int(value)]
                    vals[cell.attrib["r"]] = value
                rows.append(vals)
            out[name] = rows
            print(name, "rows", len(rows), json.dumps(rows[:22]))
    (ROOT / "WORKBOOK_CELLS.json").write_text(json.dumps(out, indent=2))
