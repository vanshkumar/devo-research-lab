"""Cached source inspection only; does not import/run the experimental task."""
from pathlib import Path
import hashlib
import io
import json
import resource
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SRC = ROOT / "campaigns/human_learning_routes_2026-10-28/experiments/source_audit/sources"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def workbook(path):
    raw = path.read_bytes()
    rows = []
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members = {x.filename: x.file_size for x in z.infolist()}
        assert sum(members.values()) < 20_000_000
        strings = []
        if "xl/sharedStrings.xml" in members:
            e = ET.fromstring(z.read("xl/sharedStrings.xml"))
            strings = ["".join(c.itertext()) for c in e]
        name = "xl/worksheets/sheet1.xml"
        sheet = ET.fromstring(z.read(name))
        for r in sheet.findall("s:sheetData/s:row", NS):
            row = {}
            for c in r:
                v = c.find("s:v", NS)
                value = None if v is None else v.text
                if c.get("t") == "s" and value is not None:
                    value = strings[int(value)]
                elif c.get("t") == "inlineStr":
                    value = "".join(c.find("s:is", NS).itertext())
                row[c.get("r")] = value
            rows.append(row)
    return raw, members, rows


def main():
    pins = []
    snippets = {}
    patterns = ("pregen", "selection=", "nReps=", "method=", "probabilityLeft",
                "sequence_num", "sequence_file", "stim_pos", "trialList=", "participant")
    paths = [SRC / "WIN_cursor_ibl_lastrun.py", ROOT / "sources/human_learning_feasibility_2026-10-28/WIN_cursor_ibl.psyexp"]
    for path in paths:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        lines = text.splitlines()
        found = []
        for i, line in enumerate(lines):
            if any(p in line for p in patterns):
                if len(line) < 1500:
                    found.append({"line": i + 1, "text": line})
        pins.append({"path": str(path.relative_to(ROOT)), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        snippets[str(path.relative_to(ROOT))] = found
    path = SRC / "pregen_sequence_0.xlsx"
    raw, members, rows = workbook(path)
    pins.append({"path": str(path.relative_to(ROOT)), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "zip_uncompressed_directory_sum": sum(members.values())})
    result = {"utc": datetime.now(timezone.utc).isoformat(), "pins": pins, "snippets": snippets,
              "workbook_header_and_first_two_rows": rows[:3], "workbook_rows": len(rows),
              "rss_bytes_darwin": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "python": sys.version, "scope": "Inspection preceding the source-grounded calculation; not itself the numeric milestone."}
    (OUT / "SOURCE_INSPECTION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
