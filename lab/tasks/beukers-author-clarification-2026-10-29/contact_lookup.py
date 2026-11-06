"""Public author-contact metadata only; never log research article contents."""
import hashlib
import html
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
URL = "https://www.nature.com/articles/s44271-024-00079-4#corresponding-author"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    path = HERE / "CONTACT_LOOKUPS.json"
    log = json.loads(path.read_text()) if path.exists() else {"lookups": []}
    assert len(log["lookups"]) < 2
    assert not log["lookups"], "one use, no automatic retry"
    entry = {"number": 1, "url": URL, "utc": datetime.now(timezone.utc).isoformat(), "purpose": "official publisher corresponding-author contact only", "status": "started", "body_bytes": 0}
    log["lookups"].append(entry)
    path.write_text(json.dumps(log, indent=2) + "\n")
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"})
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=20) as response:
            entry["http_status"] = response.status
            raw = response.read(2_000_001)
        entry["body_bytes"] = len(raw)
        assert len(raw) <= 2_000_000, "contact-page cap"
        # Decode only bounded corresponding-author/mailto metadata segments.
        segments = []
        for match in re.finditer(rb"(?i)corresponding author|Correspondence to", raw):
            segment = raw[match.start():match.start() + 3000]
            stop = re.search(rb"(?i)<h[123]", segment[30:])
            if stop:
                segment = segment[:30 + stop.start()]
            text = html.unescape(re.sub(rb"<[^>]*>", b" ", segment).decode("utf-8", errors="replace"))
            text = re.sub(r"\s+", " ", text).strip()
            if text and text not in segments:
                segments.append(text[:1000])
        emails = []
        for match in re.finditer(rb"(?i)mailto:([^\"\s<>?]+)", raw):
            address = html.unescape(match.group(1).decode("ascii", errors="replace"))
            if address not in emails:
                emails.append(address)
        entry["corresponding_author_segments"] = segments
        entry["public_mailto_addresses"] = emails
        entry["research_contents_rendered_or_saved"] = False
        entry["status"] = "contact_metadata_only"
    except Exception as exc:
        entry["status"] = "failed"
        entry["error_type"] = type(exc).__name__
        entry["error"] = str(exc)[:200]
    path.write_text(json.dumps(log, indent=2) + "\n")
    print(json.dumps(entry))


if __name__ == "__main__":
    main()
