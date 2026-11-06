#!/usr/bin/env python3
"""Single-process retrieval of authorized public documentation and catalogue objects."""

import argparse
import datetime
import hashlib
import http.client
import json
import pathlib
import resource
import time
import urllib.parse


ROOT = pathlib.Path(__file__).resolve().parent
LEDGER = ROOT / "HTTP.jsonl"
BODY_LIMIT = 25_000_000
HEADER_KEYS = {
    "content-length", "content-range", "content-type", "content-encoding",
    "date", "etag", "last-modified", "location", "server", "transfer-encoding",
    "x-amz-request-id", "x-amz-version-id", "x-github-request-id",
}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def append(entry):
    with LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def request(args, method, target, bound, output=None):
    reservation = {"event": "request", "method": method, "url": args.url,
                   "booked_body_bytes": bound, "output": output, "utc": utc()}
    append(reservation)
    start_cpu = time.process_time()
    start = time.monotonic()
    result = {**reservation, "event": "result", "body_bytes_read": 0}
    connection = http.client.HTTPSConnection(target.hostname, timeout=12)
    headers = {"Accept-Encoding": "identity", "Connection": "close",
               "User-Agent": "Allen-public-metadata-qualification/1.0"}
    path = urllib.parse.urlunsplit(("", "", target.path or "/", target.query, ""))
    try:
        connection.request(method, path, headers=headers)
        response = connection.getresponse()
        result["http_status"] = response.status
        result["headers"] = {k.lower(): v for k, v in response.getheaders()
                             if k.lower() in HEADER_KEYS}
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}; error/redirect body left unread")
        length = response.getheader("Content-Length")
        if method == "HEAD":
            return int(length) if length is not None else None
        if response.getheader("Content-Encoding", "identity").lower() != "identity":
            raise ValueError("unexpected content encoding")
        if length is None and not (args.catalogue or args.literature_or_source_index):
            raise ValueError("GET Content-Length missing")
        if length is not None and int(length) > bound:
            raise ValueError(f"GET Content-Length {length} exceeds reserved {bound}")
        body = bytearray()
        while len(body) < bound:
            if time.monotonic() - start > 35:
                raise TimeoutError("35-second body deadline reached")
            part = response.read(min(32_768, bound - len(body)))
            if not part:
                break
            body.extend(part)
            result["body_bytes_read"] += len(part)
        if length is not None and len(body) != int(length):
            raise ValueError("short response")
        if length is None and len(body) == bound:
            raise ValueError("bounded response reached cap")
        result["sha256"] = hashlib.sha256(body).hexdigest()
        with (ROOT / output).open("xb") as handle:
            handle.write(body)
    except Exception as exc:
        result["error"] = str(exc)
        raise
    finally:
        connection.close()
        result["wall_s"] = round(time.monotonic() - start, 6)
        result["process_cpu_s_excludes_imports"] = round(time.process_time() - start_cpu, 6)
        result["peak_rss_native_units"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        append(result)
        print(json.dumps(result, sort_keys=True), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--output")
    parser.add_argument("--cap", type=int, default=0)
    parser.add_argument("--head-only", action="store_true")
    parser.add_argument("--catalogue", action="store_true",
                        help="Only a bounded official S3 key or version list query")
    parser.add_argument("--literature-or-source-index", action="store_true",
                        help="Allow capped chunked text from a public bibliographic or code index")
    args = parser.parse_args()
    target = urllib.parse.urlsplit(args.url)
    if target.scheme != "https" or target.netloc != target.hostname or target.fragment:
        parser.error("plain HTTPS target required; no redirects or credentials")
    if args.catalogue:
        params = urllib.parse.parse_qs(target.query, keep_blank_values=True)
        if (target.hostname != "visual-behavior-ophys-data.s3.amazonaws.com"
                or target.path != "/"
                or not (params.get("list-type") == ["2"] or "versions" in params)
                or not 1 <= int(params.get("max-keys", [0])[0]) <= 1000):
            parser.error("expected the official bucket with a <=1000-key bounded list query")
    if args.literature_or_source_index:
        if not ((target.hostname == "www.ebi.ac.uk"
                 and target.path == "/europepmc/webservices/rest/search")
                or (target.hostname == "api.github.com"
                    and target.path.startswith("/repos/AllenInstitute/AllenSDK/"))):
            parser.error("expected a public Europe PMC query or AllenSDK code index")
    if not args.head_only:
        if (not args.output or pathlib.Path(args.output).name != args.output
                or (ROOT / args.output).exists() or args.cap <= 0):
            parser.error("a fresh task-local basename and positive byte cap are required")
        entries = LEDGER.read_text().splitlines() if LEDGER.exists() else []
        spent = sum(item["booked_body_bytes"] for item in map(json.loads, entries)
                    if item["event"] == "request")
        if spent + args.cap > BODY_LIMIT:
            parser.error("cumulative HTTP body ceiling would be exceeded")
    if not (args.catalogue or args.literature_or_source_index):
        length = request(args, "HEAD", target, 0)
        if args.head_only:
            return
        if length is None or not 0 < length <= args.cap:
            raise SystemExit(f"HEAD length {length} not within reserved cap {args.cap}")
    request(args, "GET", target, args.cap, args.output)


if __name__ == "__main__":
    main()
