"""Correct a Python-only syntax false alarm without changing JSON projection."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from notebook_source_reader import Reader, literal_alerts

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NEW = ROOT / "sources/schema_learning_data_audit_2026-10-29"
KNOWN_DIRECTIVES = frozenset({"%matplotlib inline", "%load_ext autoreload", "%autoreload 2"})


def screen(text):
    lines = text.splitlines()
    other = [i for i, line in enumerate(lines, 1) if line.lstrip().startswith(("%", "!")) and line.strip() not in KNOWN_DIRECTIVES]
    if other:
        return [{"line": line, "category": "unrecognized_nonPython_directive_STOP"} for line in other]
    cleaned = "\n".join("" if line.strip() in KNOWN_DIRECTIVES else line for line in lines)
    return literal_alerts(cleaned)


def freeze():
    tests = []

    def check(name, passed):
        assert passed, name
        tests.append({"name": name, "passed": True})

    directives = "\n".join(sorted(KNOWN_DIRECTIVES)) + "\n"
    check("known_directives_do_not_trigger_Python_syntax_alarm", screen(directives + "x = 1\n") == [])
    for name, text in [
        ("response_literal_retained", "responses = [1, 0, 1, 1]\n"),
        ("participant_literal_retained", "participant_to_exp = {1: [[1,2,3,4]]}\n"),
        ("numeric_data_literal_retained", "values = [1,2,3,4]\n"),
        ("personal_literal_retained", "participant_age = [32]\n"),
        ("comment_stop_retained", "# subject: private-values\nx=1\n"),
        ("unknown_directive_stops", "%unknown private-values\n"),
        ("cell_magic_stops", "%%javascript\nvar x=1;\n"),
        ("bang_stops", "!echo private-values\n"),
        ("changed_directive_arguments_stop", "%load_ext another_extension\n"),
        ("syntax_error_still_stops", "x = (\n"),
    ]:
        check(name, bool(screen(directives + text)))
    original = json.loads((HERE / "NOTEBOOK_READER_FREEZE.json").read_text())
    reader_hash = hashlib.sha256((HERE / "notebook_source_reader.py").read_bytes()).hexdigest()
    check("original_JSON_projection_unchanged", reader_hash == original["reader_sha256"])
    correction = {
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "reason": "Post-acquisition code-only syntax diagnostic located three percent directives in cell0; no participant-data literal was flagged. The original Python-only triage classified a directive as a syntax failure. This is a documented screen correction, not a successful first pass or removal of a participant-literal stop.",
        "original_NOTEBOOK_READER_FREEZE_unchanged": True,
        "original_NOTEBOOK_PROJECTION_STOP_preserved": True,
        "JSON_projection_reader_sha256_unchanged": reader_hash,
        "scope": "Same already-authorized code.source strings only; no new network/object/field/value access; recognize only the three canonical literal directive lines listed here and never execute them. All original participant-literal checks remain active.",
        "known_directives": sorted(KNOWN_DIRECTIVES),
        "correction_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "checks": tests,
        "all_passed": True,
    }
    (HERE / "SOURCE_TRIAGE_CORRECTION_FREEZE.json").write_text(json.dumps(correction, indent=2) + "\n")
    print(json.dumps({"correction_checks_passed": len(tests), "frozen_utc": correction["frozen_utc"]}))


def apply():
    amendment = json.loads((HERE / "SOURCE_TRIAGE_CORRECTION_FREEZE.json").read_text())
    assert amendment["all_passed"]
    assert amendment["correction_source_sha256"] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    original = json.loads((HERE / "NOTEBOOK_READER_FREEZE.json").read_text())
    assert hashlib.sha256((HERE / "notebook_source_reader.py").read_bytes()).hexdigest() == original["reader_sha256"]
    raw = (NEW / (original["selected_path"] + ".opaque")).read_bytes()
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == original["selected_git_blob"]
    reader = Reader(raw)
    selected = reader.extract()
    alerts = [{"cell_index": index, **alert} for index, text in selected for alert in screen(text)]
    result = {"checked_utc": datetime.now(timezone.utc).isoformat(), "code_cell_indices": [i for i,t in selected],
              "decoded_code_source_utf8_bytes_this_pass": sum(len(t.encode()) for i,t in selected),
              "excluded_notebook_values_decoded": 0, "new_network_requests": 0, "code_executed": False,
              "literal_alerts": alerts, "original_STOP_not_relabelled": True,
              "canonical_directive_counts": {str(i): sum(line.strip() in KNOWN_DIRECTIVES for line in text.splitlines()) for i,text in selected}}
    if not alerts:
        code = "\n\n".join("# Notebook code cell %d\n%s" % (index, text) for index,text in selected)
        path = NEW / "notebook_code_only.py"
        path.write_text(code)
        result["source_file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        result["status"] = "code_source_ready_for_static_inspection_no_literal_alerts"
    else:
        result["status"] = "STOP_do_not_render_or_use_possible_data_literals"
    (HERE / "NOTEBOOK_SOURCE_TRIAGE.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    import sys
    if sys.argv[1] == "freeze":
        freeze()
    elif sys.argv[1] == "apply":
        apply()
