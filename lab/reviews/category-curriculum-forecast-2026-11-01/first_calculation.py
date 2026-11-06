"""Independent original-byte join and observation arithmetic; no author imports."""
import datetime as dt
import hashlib
import io
import json
import pathlib
import re
import resource
import zipfile
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
AUTHOR = HERE.parents[1] / "tasks/category-curriculum-forecast-2026-11-01"
START = dt.datetime.fromisoformat("2026-11-01T09:41:14.530+00:00")
HARD = dt.datetime.fromisoformat("2026-11-01T10:26:14.530+00:00")
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def original_inputs():
    charged = 0
    blob = (AUTHOR / "source/Stim-struct.xlsx").read_bytes()
    charged += len(blob)
    book_sha = hashlib.sha256(blob).hexdigest()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        members = {}
        for name in ("xl/workbook.xml", "xl/_rels/workbook.xml.rels", "xl/sharedStrings.xml"):
            members[name] = z.read(name)
            charged += len(members[name])
        ss = ET.fromstring(members["xl/sharedStrings.xml"])
        strings = ["".join(t.text or "" for t in si.findall(".//s:t", NS)) for si in ss]
        rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(members["xl/_rels/workbook.xml.rels"])}
        sheet = next(s for s in ET.fromstring(members["xl/workbook.xml"]).findall("s:sheets/s:sheet", NS) if s.attrib["name"] == "High Sim")
        rid = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        path = rels[rid].lstrip("/")
        if not path.startswith("xl/"):
            path = "xl/" + path
        xml = z.read(path)
        charged += len(xml)
        geom = {}
        for row in ET.fromstring(xml).findall("s:sheetData/s:row", NS):
            cells = {}
            for c in row:
                v = c.find("s:v", NS)
                if v is None:
                    continue
                value = v.text
                if c.attrib.get("t") == "s":
                    value = strings[int(value)]
                cells[re.sub("[0-9]", "", c.attrib["r"])] = value
            if re.fullmatch("[a-f][0-9]{2}", cells.get("I", "")):
                geom[cells["I"] + ".gif"] = tuple(int(cells[c]) for c in "ABCDEFGH")
    assert len(geom) == 96
    blob = (AUTHOR / "source/highsim-trials.zip").read_bytes()
    charged += len(blob)
    zip_sha = hashlib.sha256(blob).hexdigest()
    people = []
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for name in sorted(z.namelist(), key=lambda x: int(pathlib.PurePosixPath(x).stem)):
            payload = z.read(name)
            charged += len(payload)
            lines = payload.decode("utf-8").splitlines()
            person = int(pathlib.PurePosixPath(name).stem)
            rows = []
            for line in lines:
                fields = line.split()
                if len(fields) == 12 and fields[0] == str(person) and fields[3].isdigit():
                    rows.append(fields)
            first_groups = list(map(int, re.findall("[0-9]+", lines[1].split("Second")[0])))
            assert len(first_groups) == 3
            mapping = {chr(97 + x): i for i, x in enumerate(first_groups)}
            train = [r for r in rows if 1 <= int(r[4]) <= 4]
            test = [r for r in rows if int(r[4]) == 5]
            novel = [r for r in test if 9 <= int(r[9][1:3]) <= 16]
            people.append(dict(person=person, rows=rows, lines=lines[:3], train=train, test=test,
                               novel=novel, mapping=mapping, sha256=hashlib.sha256(payload).hexdigest()))
    return geom, people, dict(logical_original_read_decode_hash_allowance_bytes=charged * 2,
                              workbook_sha256=book_sha, archive_sha256=zip_sha,
                              workbook_member=path, archive_members=len(people))


def main():
    assert dt.datetime.now(dt.timezone.utc) < HARD
    geom, people, reads = original_inputs()
    details, discrepancies = [], []
    for p in people:
        if len(p["rows"]) != 672:
            assert p["person"] == 41 and len(p["rows"]) == 308
            details.append(dict(person=41, rows=308, status="input-incomplete; no response arithmetic"))
            continue
        assert len(p["train"]) == 288 and len(p["test"]) == 48 and len(p["novel"]) == 24
        seq = [int(r[3]) for r in p["rows"]]
        assert all(b - a == 1 for a, b in zip(seq, seq[1:]))
        seen = {r[9] for r in p["train"]}
        assert all(r[9] not in seen for r in p["novel"])
        assert all(r[9] in geom for r in p["train"] + p["test"])
        for r in p["train"] + p["test"]:
            assert p["mapping"][r[9][0]] == int(r[6])
            assert int(r[7]) == int(int(r[5]) == int(r[6]))
            assert 0 <= int(r[5]) <= 2
        labels = [int(r[6]) for r in p["train"]]
        switches = sum(a != b for a, b in zip(labels, labels[1:]))
        role = "source" if "BI" in p["lines"][2] else "evaluation"
        assert (switches < 144) == (role == "source")
        assert (p["person"] % 2 == 0) == (role == "source")
        for r in p["test"]:
            if (r[11] == "0") != (r[9] not in seen):
                discrepancies.append(dict(person=p["person"], item=r[9], nominal_old_flag=r[11], actual_unseen=r[9] not in seen))
        details.append(dict(person=p["person"], role=role, sha256=p["sha256"], rows=len(p["rows"]),
                            category_mapping=p["mapping"], actual_category_counts=[labels.count(k) for k in range(3)],
                            training_items=len(seen), category_switches=switches,
                            intended_new_queries=24,
                            new_correct=sum(int(r[5]) == p["mapping"][r[9][0]] for r in p["novel"])))
    result = dict(completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  command=".venv/bin/python lab/reviews/category-curriculum-forecast-2026-11-01/first_calculation.py",
                  fixed_start=START.isoformat(), status="INDEPENDENT ORIGINAL DAT/WORKBOOK JOIN AND RESPONSE ARITHMETIC EXECUTED",
                  nominal_items=len(geom), nominal_feature_values=[sorted({x[j] for x in geom.values()}) for j in range(8)],
                  details=details, old_flag_nonmembership_discrepancies=discrepancies,
                  totals={role: dict(people=sum(d.get("role") == role for d in details),
                                     queries=sum(d.get("intended_new_queries", 0) for d in details if d.get("role") == role),
                                     correct=sum(d.get("new_correct", 0) for d in details if d.get("role") == role))
                          for role in ("source", "evaluation")},
                  resources={**reads, "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                             "scientific_processes": 1, "numeric_threads": 1, "public_operations": 0})
    (HERE / "FIRST_CALCULATION.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in ("completed_utc", "status", "totals", "old_flag_nonmembership_discrepancies", "resources")}, indent=2))


if __name__ == "__main__":
    main()
