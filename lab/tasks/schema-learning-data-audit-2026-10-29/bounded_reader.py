"""Value-blind CSV header reader. Never decode a payload row or import source code."""
import hashlib
import re

CAP = 4096
FIELD = re.compile(rb"[A-Za-z_][A-Za-z0-9_. /()-]{0,95}\Z")


class Reject(ValueError):
    pass


def header_only(stream, expected=None):
    """Read one capped block, retain header only, blindly discard any overread.

    No CSV data row is decoded, tokenized, hashed, rendered, or saved. A quote
    or nonidentifier in the header fails closed. This deliberately supports
    only unquoted, single-line ASCII identifier headers, including one empty
    pandas index label. Numeric/headerless input is rejected without rendering.
    """
    block = stream.read(CAP)
    if not isinstance(block, bytes) or len(block) > CAP:
        raise Reject("nonconforming bounded byte stream")
    end = block.find(b"\n")
    if end < 0:
        raise Reject("no complete header within cap")
    raw = block[:end + 1]
    discarded = len(block) - len(raw)
    del block
    line = raw.rstrip(b"\r\n")
    if line.startswith(b"\xef\xbb\xbf"):
        line = line[3:]
    tokens = line.split(b",")
    if len(tokens) < 2 or len(tokens) > 128:
        raise Reject("unsupported field count")
    if tokens[0] == b"":
        tokens[0] = b"__pandas_index__"
    if not all(FIELD.fullmatch(token) for token in tokens):
        raise Reject("not an unambiguous identifier header")
    if len(set(tokens)) != len(tokens):
        raise Reject("duplicate field names")
    names = tuple(token.decode("ascii") for token in tokens)
    if expected is not None and names != tuple(expected):
        raise Reject("header differs from frozen expected schema")
    return {
        "fields": names,
        "acquired_body_bytes": len(raw) + discarded,
        "header_bytes": len(raw),
        "blind_discard_bytes": discarded,
        "header_sha256": hashlib.sha256(raw).hexdigest(),
        "rows_parsed": 0,
        "excluded_values_materialized": 0,
    }, raw

