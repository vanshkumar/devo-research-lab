"""One bounded public retry, honoring the repository's previous Retry-After.

No alternate credentials, accounts, proxy rotation, or access-control bypass.
The last official legacy URL response was HTTP429 at 2026-10-28 17:44:54Z
with Retry-After900; execution before17:59:54Z is refused.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "inputs" / "prior_work"
URL = "https://dspace.mit.edu/bitstreams/5b1871c5-194c-478a-a3a2-0d49173db31b/download"
CAP = 35_000_000
EARLIEST = datetime(2026, 10, 28, 17, 59, 54, tzinfo=timezone.utc)
EXPECTED_MD5 = "d4c68c36635fadb85a8f4a7bd40280bb"


def main():
    now = datetime.now(timezone.utc)
    if now < EARLIEST:
        raise RuntimeError(f"Honor Retry-After: earliest retry is {EARLIEST.isoformat()}")
    metadata = {
        "url": URL,
        "repository_url": "https://hdl.handle.net/1721.1/156934",
        "retrieved_at_utc": now.isoformat(),
        "expected_md5_from_repository": EXPECTED_MD5,
        "max_bytes": CAP,
        "prior_attempts": [
            {"url": URL, "outcome": "sandbox DNS failure", "bytes": 0},
            {"url": URL, "outcome": "HTTP429; no PDF bytes retained"},
            {"url": "https://dspace.mit.edu/bitstream/handle/1721.1/156934/Bahle-abahle-phd-bcs-2024-thesis.pdf?sequence=1&isAllowed=y", "outcome": "HTTP429", "response_time_utc": "2026-10-28T17:44:54+00:00", "retry_after_seconds": 900},
        ],
    }
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (public academic source audit)"})
        with urllib.request.urlopen(req, timeout=60) as response:
            metadata["http_status"] = response.status
            metadata["response_headers"] = dict(response.headers)
            data = response.read(CAP + 1)
        metadata["transferred_bytes"] = len(data)
        if len(data) > CAP:
            raise ValueError("Source exceeds bounded download cap")
        if not data.startswith(b"%PDF"):
            raise ValueError("Response is not a PDF")
        metadata["md5"] = hashlib.md5(data).hexdigest()
        metadata["sha256"] = hashlib.sha256(data).hexdigest()
        if metadata["md5"] != EXPECTED_MD5:
            raise ValueError("Public metadata checksum mismatch; no verified source saved")
        dest = OUT / "bahle_2024_thesis.pdf"
        dest.write_bytes(data)
        metadata["saved_file"] = str(dest.relative_to(ROOT))
        metadata["outcome"] = "complete; repository MD5 verified"
    except urllib.error.HTTPError as err:
        metadata["http_status"] = err.code
        metadata["response_headers"] = dict(err.headers)
        metadata["outcome"] = f"HTTPError {err.code}; no PDF bytes retained"
    except Exception as err:
        metadata["outcome"] = f"{type(err).__name__}: {err}"
    (OUT / "bahle_acquisition_manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({k: metadata[k] for k in ["retrieved_at_utc", "outcome", "http_status", "transferred_bytes", "sha256"] if k in metadata}, indent=2))


if __name__ == "__main__":
    main()
