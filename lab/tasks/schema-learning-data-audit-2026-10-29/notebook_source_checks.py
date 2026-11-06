"""Synthetic fixtures only; freeze extraction and first-block original hashes."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from notebook_source_reader import Reader, Reject, literal_alerts

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NEW = ROOT / "sources/schema_learning_data_audit_2026-10-29"


def main():
    checks = []

    def check(name, ok):
        assert ok, name
        checks.append({"name": name, "passed": True})

    # Deliberately fake excluded values; synthetic construction may materialize
    # them, but the reader under test must never pass them to its decoder.
    sentinel = "EXCLUDED_HUMAN_RESPONSE_ATTACHMENT_SENTINEL"
    code = 'import math\nlabel = "λ \\\" quote"\nprint(label)\n'
    expected_tokens = [json.dumps(code[:12]).encode(), json.dumps(code[12:]).encode()]
    fixture = {
        "source": sentinel,
        "metadata": {"cells": [{"cell_type": "code", "source": sentinel}], "source": sentinel,
                     "measurements": [-1.2345e87, 987654321, True, None]},
        "cells": [
            {"source": [code[:12], code[12:]], "outputs": [{"source": sentinel, "cell_type": "code", "data": {"text/plain": [sentinel]}, "values": [123, 4.5]}],
             "attachments": {"a": {"source": sentinel}}, "cell_type": "code", "execution_count": 999},
            {"cell_type": "markdown", "source": [sentinel], "attachments": {"source": sentinel}},
            {"cell_type": "raw", "source": sentinel},
            {"cell_type": "code", "metadata": {"source": sentinel}, "source": "x = 2\n", "outputs": [sentinel]},
        ],
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    payload = json.dumps(fixture).encode()
    decoded = []

    def spy(raw):
        assert sentinel.encode() not in raw, "excluded sentinel reached decoder"
        decoded.append(raw)
        return json.loads(raw)

    reader = Reader(payload, decode=spy)
    cells = reader.extract()
    check("only_direct_code_cell_source", cells == [(0, code), (3, "x = 2\n")])
    check("exact_selected_string_decoder_calls", decoded == expected_tokens + [json.dumps("x = 2\n").encode()])
    check("excluded_sentinels_never_decoded", all(sentinel.encode() not in raw for raw in decoded))
    check("excluded_nested_source_keys_ignored", len(cells) == 2)
    check("source_before_cell_type_supported", cells[0][1] == code)
    check("array_and_scalar_sources_supported", len(reader.decoded_spans) == 3)
    check("unicode_and_quote_escaping_preserved", cells[0][1] == code)
    check("all_notebook_cell_structure_counted", reader.cell_count == 4)
    check("literal_triage_accepts_plain_code", literal_alerts(code) == [])
    escaped = b'{"ce\\u006cls":[{"sour\\u0063e":"x = 2\\n","cell\\u005ftype":"c\\u006fde","outputs":{"source":"' + sentinel.encode() + b'"}}]}'
    check("escaped_structural_keys_and_code_type", Reader(escaped).extract() == [(0, "x = 2\n")])
    check("empty_source_array", Reader(b'{"cells":[{"cell_type":"code","source":[]}]}').extract() == [(0, "")])
    check("whitespace_order_root_metadata", Reader(b' \n{"cells":[],"metadata":{"source":"' + sentinel.encode() + b'"}}\t').extract() == [])
    for end in range(len(payload)):
        calls = []
        try:
            Reader(payload[:end], decode=lambda raw: calls.append(raw)).extract()
        except Reject:
            assert calls == [], "truncated structure decoded source"
        else:
            raise AssertionError("accepted truncated structure")
    check("every_truncated_prefix_rejected_before_decoding", True)
    bad = {
        "root_array": b'[]',
        "missing_cells": b'{"metadata":{}}',
        "duplicate_cells": b'{"cells":[],"cells":[]}',
        "cell_missing_type": b'{"cells":[{"source":"x=1"}]}',
        "cell_missing_source": b'{"cells":[{"cell_type":"code"}]}',
        "duplicate_cell_type": b'{"cells":[{"cell_type":"code","cell_type":"markdown","source":"x=1"}]}',
        "duplicate_source": b'{"cells":[{"cell_type":"code","source":"x=1","source":"y=2"}]}',
        "numeric_code_source": b'{"cells":[{"cell_type":"code","source":123}]}',
        "numeric_source_array_item": b'{"cells":[{"cell_type":"code","source":[123]}]}',
        "source_object": b'{"cells":[{"cell_type":"code","source":{"source":"fake"}}]}',
        "invalid_escape_in_excluded_value": b'{"metadata":"\\q","cells":[]}',
        "invalid_unicode_in_excluded_value": b'{"metadata":"\\u12xx","cells":[]}',
        "invalid_number_in_excluded_value": b'{"metadata":[01],"cells":[]}',
        "trailing_comma": b'{"cells":[],}',
        "nonJSON_NaN": b'{"metadata":NaN,"cells":[]}',
        "trailing_garbage": b'{"cells":[]}false',
    }
    for name, raw in bad.items():
        try:
            Reader(raw).extract()
        except Reject:
            check(name + "_rejects", True)
        else:
            raise AssertionError("accepted " + name)
    for name, raw, limits in [
        ("opaque_body_cap", payload, {"body_cap": len(payload) - 1}),
        ("decoded_source_cap", payload, {"source_cap": 1}),
        ("cell_count_cap", payload, {"cell_cap": 1}),
        ("nested_depth_cap", b'{"cells":[],"metadata":[[[[1]]]]}', {"depth_cap": 1}),
    ]:
        try:
            Reader(raw, **limits).extract()
        except Reject:
            check(name + "_enforced", True)
        else:
            raise AssertionError("failed cap " + name)
    for name, text in [
        ("participant_sequence_literal", "participant_to_exp = {1: [[0, 1, 2, 3]]}\n"),
        ("response_literal", "responses = [1, 0, 1, 1]\n"),
        ("long_numeric_literal", "values = [1, 2, 3, 4]\n"),
        ("embedded_table_string", 's = "' + ("row," * 60) + '"\n'),
        ("personal_literal", "participant_age = [32]\n"),
        ("possible_data_comment", "# subject: private-values\nx=1\n"),
        ("non_Python_source", "%%javascript\nvar x = 1;\n"),
    ]:
        # The table fixture has no newline in value, so give it a sensitive tag.
        if name == "embedded_table_string":
            text = text.replace("row,", "response,", 1)
        alerts = literal_alerts(text)
        check(name + "_stops_before_render", bool(alerts) and all(set(a) == {"line", "category"} for a in alerts))
    check("known_plot_magic_allowed_without_execution", literal_alerts("%matplotlib inline\nx = 1\n") == [])
    preserved = {}
    for name in ["RESULT.md", "CERTIFICATION.md", "HEADER_READER_FREEZE.json", "bounded_reader.py", "reader_checks.py", "SOURCE_CHECKS.json", "EXPOSURE.json", "ACQUISITION.json", "PROPOSED_LEARNING.md"]:
        preserved[name] = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
    preserved["sources/SOURCE_PINS.json"] = hashlib.sha256((NEW / "SOURCE_PINS.json").read_bytes()).hexdigest()
    freeze = {
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "sole revision; before opaque notebook acquisition",
        "selected_path": "humanData_analysis_sandbox.ipynb",
        "selected_git_blob": "647cd439916dafd9d332c55c11f051f8153113ff",
        "expected_bytes": 14953,
        "commit": "eb0edbe51042ffaf065bd90839f4f999de5f3ffb",
        "body_cap": 14953,
        "code_source_total_bytes_cap": 65536,
        "cell_count_cap": 512,
        "depth_cap": 64,
        "projection": "Only direct cells[*].source strings/array-of-strings where direct cell_type matches code; structural labels matched incrementally without materializing arbitrary keys/types; source decode deferred until whole structure and type validate. No excluded JSON scalar/container decoding.",
        "output_and_attachment_policy": "Opaque acquired bytes only; no rendered output, excluded strings/numbers/arrays, notebook JSON decode, imports or execution. Nested source keys ignored. Stop before rendering/using code if literal triage flags possible participant data; report any embedded-data exposure.",
        "real_header_projection": "NONE unless source establishes a separate safe expected profile and freeze within the single remaining request and original conditions",
        "reader_sha256": hashlib.sha256((HERE / "notebook_source_reader.py").read_bytes()).hexdigest(),
        "tests_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "preserved_first_block_sha256": preserved,
        "checks": checks,
        "all_passed": True,
    }
    (HERE / "NOTEBOOK_READER_FREEZE.json").write_text(json.dumps(freeze, indent=2) + "\n")
    print(json.dumps({"checks_passed": len(checks), "frozen_utc": freeze["frozen_utc"], "reader_sha256": freeze["reader_sha256"], "opaque_notebook_requests": 0}))


if __name__ == "__main__":
    main()
