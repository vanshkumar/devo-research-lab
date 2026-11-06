#!/usr/bin/env python3
"""Save the public version inventory for behavior-session NWB keys only."""

import json
from types import SimpleNamespace
from urllib.parse import urlencode, urlsplit
from xml.etree import ElementTree

from fetch_public import BODY_LIMIT, LEDGER, ROOT, request


NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"
BASE = "https://visual-behavior-ophys-data.s3.amazonaws.com/?"
PREFIX = "visual-behavior-ophys/behavior_sessions/"
PAGE_CAP = 600_000
MAX_PAGES = 24


def main():
    query = {"versions": "", "prefix": PREFIX, "max-keys": 1000}
    markers = set()
    for page in range(1, MAX_PAGES + 1):
        output = f"allen_behavior_versions_{page:02d}.xml"
        if (ROOT / output).exists():
            raise SystemExit(f"existing page {output}; inspect before any retry")
        ledger = map(json.loads, LEDGER.read_text().splitlines())
        spent = sum(item["booked_body_bytes"] for item in ledger
                    if item["event"] == "request")
        if spent + PAGE_CAP > BODY_LIMIT:
            raise SystemExit("cumulative body ceiling would be exceeded")
        url = BASE + urlencode(query)
        args = SimpleNamespace(url=url, catalogue=True, literature_or_source_index=False)
        request(args, "GET", urlsplit(url), PAGE_CAP, output)
        root = ElementTree.fromstring((ROOT / output).read_bytes())
        if (root.tag != NS + "ListVersionsResult"
                or root.findtext(NS + "Prefix") != PREFIX):
            raise ValueError(f"unexpected listing envelope {output}")
        if root.findtext(NS + "IsTruncated") == "false":
            return
        key = root.findtext(NS + "NextKeyMarker")
        version = root.findtext(NS + "NextVersionIdMarker")
        if not key or not key.startswith(PREFIX) or not version or (key, version) in markers:
            raise ValueError(f"invalid continuation marker in {output}")
        markers.add((key, version))
        query.update({"key-marker": key, "version-id-marker": version})
    raise SystemExit("predeclared page ceiling reached")


if __name__ == "__main__":
    main()
