"""Synthetic-only checks; run before acquisition, save a source hash freeze."""
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from bounded_reader import CAP, Reject, header_only

HERE = Path(__file__).resolve().parent


def main():
    checks = []

    def check(name, value):
        if not value:
            raise AssertionError(name)
        checks.append({"name": name, "passed": True})

    sentinel = b"FORBIDDEN_RESPONSE_ANSWER_CORRECTNESS_FREE_TEXT"
    header = b",participant,story,state,option0,option1,probe,response,correct\n"
    body = header + sentinel * 200
    result, retained = header_only(io.BytesIO(body))
    check("one_block_cap", result["acquired_body_bytes"] == CAP)
    check("only_header_retained", retained == header)
    check("blind_overread_exact", result["blind_discard_bytes"] == CAP - len(header))
    check("blind_overread_under_4KiB", result["blind_discard_bytes"] < 4096)
    check("no_rows_parsed", result["rows_parsed"] == 0)
    check("no_excluded_value_materialized", result["excluded_values_materialized"] == 0)
    check("no_sentinel_in_results", sentinel.decode() not in json.dumps(result))
    check("no_sentinel_in_retained", sentinel not in retained)
    check("pandas_index_explicit", result["fields"][0] == "__pandas_index__")
    expected = result["fields"]
    identical, _ = header_only(io.BytesIO(body), expected)
    check("exact_expected_schema_passes", identical == result)
    bad = [
        ("headerless_numeric", b"0,123,1,5,6,1,0\n"),
        ("headerless_mixed", b"0,anon,1,5,6,response\n"),
        ("duplicate", b"participant,participant\n"),
        ("quoted_header", b'participant,"story"\n'),
        ("quoted_newline", b'participant,"sto\nry"\n'),
        ("empty_nonindex", b"participant,,state\n"),
        ("all_empty", b",,\n"),
        ("no_newline", b"participant,story"),
        ("oversized_header", b"p" * CAP + b",story\n"),
        ("nonascii", b"participant,st\xffory\n"),
        ("single_field", b"participant\n"),
        ("wrong_expected_schema", b"participant,story\n"),
    ]
    for name, payload in bad:
        try:
            header_only(io.BytesIO(payload), expected)
        except Reject as e:
            check(name + "_rejected_without_payload", not any(chr(c) in str(e) for c in [0xff]))
        else:
            raise AssertionError("accepted " + name)
    for ending, prefix in [(b"\n", b""), (b"\r\n", b""), (b"\n", b"\xef\xbb\xbf")]:
        h = prefix + b"participant,story" + ending
        r, keep = header_only(io.BytesIO(h + sentinel))
        check("line_ending_bom_" + ending.hex() + "_" + prefix.hex(),
              r["fields"] == ("participant", "story") and keep == h)
    short, keep = header_only(io.BytesIO(b"participant,story\n"))
    check("header_only_eof", short["blind_discard_bytes"] == 0)
    frozen = {
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "synthetic header safety before any remote body acquisition",
        "schema_policy": "single-line ASCII identifiers; no numeric/headerless/quoted/ambiguous headers; exact source-derived expected schema must be frozen separately before real header request",
        "data_row_projection": "NONE authorized by this freeze; source certification and a separate tested freeze required before any row decoding",
        "reader_sha256": hashlib.sha256((HERE / "bounded_reader.py").read_bytes()).hexdigest(),
        "test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "checks": checks,
        "all_passed": True,
    }
    (HERE / "HEADER_READER_FREEZE.json").write_text(json.dumps(frozen, indent=2) + "\n")
    print(json.dumps({"passed": len(checks), "reader_sha256": frozen["reader_sha256"], "frozen_utc": frozen["frozen_utc"]}))


if __name__ == "__main__":
    main()

