"""Development-only input diagnostic. This script has no score-reader path."""

from collections import Counter
from decimal import Decimal, InvalidOperation
from io import BytesIO
import json
from math import sqrt
from pathlib import PurePosixPath
import re
from time import perf_counter, process_time
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from audit_layout import PIN, ROOT, verify_blob


NO_REBUTTAL = re.compile(r"\byour essay does not include a rebuttal\.")
NS_WORD = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def normalized(text):
    return " ".join(text.casefold().split())


def tokens(text):
    return re.findall(r"[^\W_]+", text.casefold())


class InputReads:
    def __init__(self):
        self.raw = Counter()
        self.inflated = Counter()

    def load(self, kind, entry):
        body = (ROOT / "source/dev" / entry["path"]).read_bytes()
        self.raw[kind] += len(body)
        verify_blob(body, entry)
        return body

    def xml(self, archive, name):
        if archive.getinfo(name).file_size > 1_000_000:
            raise ValueError(f"Unexpectedly large XML member {name}")
        body = archive.read(name)
        self.inflated[name] += len(body)
        return ET.fromstring(body)


def feedback_proxy(body, reads):
    with ZipFile(BytesIO(body)) as archive:
        document = reads.xml(archive, "word/document.xml")
    paragraphs = [
        "".join(node.text or "" for node in p.iter(NS_WORD + "t"))
        for p in document.iter(NS_WORD + "p")
    ]
    return any(NO_REBUTTAL.search(normalized(p)) for p in paragraphs), len(paragraphs)


def read_annotation(body, reads):
    with ZipFile(BytesIO(body)) as archive:
        workbook = reads.xml(archive, "xl/workbook.xml")
        rels = reads.xml(archive, "xl/_rels/workbook.xml.rels")
        targets = {rel.get("Id"): rel.get("Target") for rel in rels}
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = reads.xml(archive, "xl/sharedStrings.xml")
            strings = [node_text(item) for item in shared.findall("./{*}si")]
        result = {}
        for sheet in workbook.findall(".//{*}sheet"):
            name = normalized(sheet.get("name"))
            if name not in {"old draft", "new draft"}:
                continue
            target = targets[sheet.get(NS_REL + "id")]
            path = target.lstrip("/") if target.startswith("/") else "xl/" + target
            if not path.startswith("xl/worksheets/") or ".." in PurePosixPath(path).parts:
                raise ValueError("Unexpected worksheet path")
            xml = reads.xml(archive, path)
            rows = xml.findall(".//{*}sheetData/{*}row")
            header, *data = (cells(row, strings) for row in rows)
            columns = {normalized(value): column for column, value in header.items()}
            text = columns["sentence content"]
            purpose = columns["revision purpose level 0"]
            operation = columns["revision operation level 0"]
            index = columns["sentence index"]
            data = [row for row in data if row.get(text, "").strip()]
            indices = [Decimal(row[index]) for row in data]
            if any(not number.is_finite() or number != number.to_integral_value() for number in indices):
                raise ValueError("Expected integer-valued sentence indices")
            if indices != sorted(set(indices)):
                raise ValueError("Sentence indices are duplicated or out of order")
            rebuttal_adds = sum(
                normalized(row.get(purpose, "")) == "rebuttal/reservation"
                and normalized(row.get(operation, "")) == "add"
                for row in data
            )
            result[name] = (" ".join(row[text] for row in data), rebuttal_adds)
    if result.keys() != {"old draft", "new draft"}:
        raise ValueError("Expected Old Draft and New Draft sheets")
    return result


def node_text(element):
    return "".join(t.text or "" for t in element.iterfind(".//{*}t"))


def cells(row, strings):
    values = {}
    for cell in row.findall("./{*}c"):
        column = re.match(r"[A-Z]+", cell.get("r")).group()
        cell_type = cell.get("t")
        value = cell.findtext("./{*}v", "")
        if cell_type == "s":
            value = strings[int(value)]
        elif cell_type == "inlineStr":
            value = node_text(cell)
        values[column] = value
    return values


def check(row, reads):
    objects = row["objects"]
    record = {"key": row["key"], "arm": row["arm"], "draft_links": {}}
    annotations = read_annotation(reads.load("rev12", objects["rev12"]), reads)
    for kind, sheet in (("draft1", "old draft"), ("draft2", "new draft")):
        raw = reads.load(kind, objects[kind]).decode("utf-8-sig")
        raw_tokens, annotation_tokens = tokens(raw), tokens(annotations[sheet][0])
        record["draft_links"][kind] = {
            "raw_tokens": len(raw_tokens),
            "annotated_tokens": len(annotation_tokens),
            "exact_token_sequence": raw_tokens == annotation_tokens,
        }
    if all(link["exact_token_sequence"] for link in record["draft_links"].values()):
        demand, paragraphs = feedback_proxy(reads.load("feedback", objects["feedback"]), reads)
        record.update(
            exact_missing_rebuttal_feedback=demand, feedback_paragraphs=paragraphs,
            rebuttal_adds=annotations["new draft"][1],
        )
    return record


def wilson(k, n):
    z = 1.959963984540054
    p = k / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    width = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return center - width, center + width


def summarize(rows):
    verified = [row for row in rows if "rebuttal_adds" in row]
    tab = Counter(
        (row["exact_missing_rebuttal_feedback"], row["rebuttal_adds"] > 0) for row in verified
    )
    yes, no = tab[True, True] + tab[True, False], tab[False, True] + tab[False, False]
    difference, interval = None, None
    if yes and no:
        p, q = tab[True, True] / yes, tab[False, True] / no
        lp, up = wilson(tab[True, True], yes)
        lq, uq = wilson(tab[False, True], no)
        difference = p - q
        interval = [difference - sqrt((p - lp)**2 + (uq - q)**2),
                    difference + sqrt((up - p)**2 + (q - lq)**2)]
    expected_overlap = 0
    for arm in "ABCD":
        group = [row for row in verified if row["arm"] == arm]
        if group:
            expected_overlap += (
                sum(row["exact_missing_rebuttal_feedback"] for row in group)
                * sum(row["rebuttal_adds"] > 0 for row in group) / len(group)
            )
    return {
        "sample": len(rows), "eligible_exact_draft_links": len(verified),
        "feedback_present": {"addition": tab[True, True], "no_addition": tab[True, False]},
        "feedback_absent": {"addition": tab[False, True], "no_addition": tab[False, False]},
        "rate_difference": difference, "newcombe95": interval,
        "expected_overlap_reassign_feedback_within_arm": expected_overlap,
    }


def main():
    started, cpu = perf_counter(), process_time()
    layout = json.loads((ROOT / "LAYOUT.json").read_bytes())
    if layout["pin"] != PIN or len(layout["development"]) != 24:
        raise ValueError("Development manifest does not match the freeze")
    reads = InputReads()
    rows = []
    for row in layout["development"]:
        try:
            rows.append(check(row, reads))
        except (OSError, ValueError, KeyError, InvalidOperation, ET.ParseError) as exc:
            rows.append({"key": row["key"], "arm": row["arm"], "failure": type(exc).__name__})
    print(json.dumps({
        "summary": summarize(rows),
        "development_records": rows,
        "raw_file_bytes_read": dict(reads.raw),
        "xml_bytes_inflated": dict(reads.inflated),
        "analysis_wall_s": perf_counter() - started,
        "analysis_cpu_s": process_time() - cpu,
    }, indent=2))


if __name__ == "__main__":
    main()
