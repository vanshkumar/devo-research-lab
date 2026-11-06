"""Acquire only the predeclared development inputs from the pinned public release."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import PurePosixPath
from time import perf_counter
from urllib.parse import quote
from urllib.request import Request, urlopen

from audit_layout import PIN, ROOT, verify_blob


PREFIXES = {
    "draft1": "dataset/essays/Draft1/",
    "draft2": "dataset/essays/Draft2/",
    "feedback": "dataset/meta-data/ExpertFeedback/",
    "rev12": tuple(f"dataset/annotations/{arm}/12/" for arm in "ABCD"),
}


def acquire(entry):
    started = perf_counter()
    path = entry["path"]
    destination = ROOT / "source/dev" / path
    url = "https://raw.githubusercontent.com/omidkashefi/ArgRewrite/" + PIN + "/" + quote(path)
    read = 0
    try:
        request = Request(url, headers={"User-Agent": "ArgRewrite research provenance audit"})
        with urlopen(request, timeout=12) as response:
            if response.geturl() != url:
                raise ValueError("Unexpected redirect")
            body = response.read(entry["size"] + 1)
        read = len(body)
        verify_blob(body, entry)
        destination.parent.mkdir(exist_ok=True, parents=True)
        destination.write_bytes(body)
        return {"path": path, "read_bytes": read, "elapsed_s": perf_counter() - started, "verified": True}
    except (OSError, ValueError) as exc:
        return {
            "path": path, "read_bytes": read, "elapsed_s": perf_counter() - started,
            "verified": False, "failure": repr(exc),
        }


def main():
    started = perf_counter()
    layout = json.loads((ROOT / "LAYOUT.json").read_bytes())
    rows = layout["development"]
    if layout["pin"] != PIN or len(rows) != 24:
        raise ValueError("Development manifest does not match the freeze")
    entries = []
    for row in rows:
        if row["objects"].keys() != PREFIXES.keys():
            raise ValueError("Unexpected development object types")
        for kind, entry in row["objects"].items():
            path = entry["path"]
            if not path.startswith(PREFIXES[kind]) or ".." in PurePosixPath(path).parts:
                raise ValueError(f"Refusing out-of-scope path {path}")
            entries.append(entry)
    if len({entry["path"] for entry in entries}) != 96 or sum(e["size"] for e in entries) > 2_000_000:
        raise ValueError("Development request cap exceeded")
    with ThreadPoolExecutor(max_workers=6) as pool:
        receipt = list(pool.map(acquire, entries))
    print(json.dumps({"elapsed_s": perf_counter() - started, "objects": receipt}, indent=2))


if __name__ == "__main__":
    main()
