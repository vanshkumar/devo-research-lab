"""Capped official-contact pages only; no paper/dataset routes or messaging."""
import hashlib
import html
from html.parser import HTMLParser
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

HERE = Path(__file__).resolve().parent
DEADLINE = datetime.fromisoformat("2026-10-29T22:42:26+00:00")


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.active = [], None
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.active = {"href": dict(attrs).get("href", ""), "text": ""}
    def handle_data(self, data):
        if self.active is not None:
            self.active["text"] += data
    def handle_endtag(self, tag):
        if tag == "a" and self.active is not None:
            self.links.append(self.active)
            self.active = None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    assert datetime.now(timezone.utc) < DEADLINE
    url = sys.argv[1]
    assert "nature.com/articles/" not in url and not url.lower().endswith(".pdf")
    lp = HERE / "CONTACT_PAGES.json"
    log = json.loads(lp.read_text()) if lp.exists() else {"pages": []}
    assert len(log["pages"]) < 3 and url not in [p["url"] for p in log["pages"]]
    entry = {"number": len(log["pages"]) + 1, "utc": datetime.now(timezone.utc).isoformat(), "url": url, "status": "started", "body_bytes": 0}
    log["pages"].append(entry)
    lp.write_text(json.dumps(log, indent=2) + "\n")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"})
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=20) as response:
            entry["http_status"] = response.status
            entry["content_type"] = response.headers.get("Content-Type")
            raw = response.read(1_000_001)
        entry["body_bytes"] = len(raw)
        assert len(raw) <= 1_000_000, "official contact page body cap"
        entry["sha256"] = hashlib.sha256(raw).hexdigest()
        text = raw.decode("utf-8", "replace")
        parser = Parser()
        parser.feed(text)
        entry["beukers_links"] = [{"text": re.sub(r"\s+", " ", a["text"]).strip(), "url": urljoin(url, html.unescape(a["href"]))} for a in parser.links if "beukers" in (a["text"] + a["href"]).lower()]
        excerpts = []
        for match in re.finditer(r"Beukers", text, re.I):
            snippet = text[max(0, match.start()-150):match.end()+650]
            snippet = re.sub(r"<[^>]*>", " ", snippet)
            snippet = re.sub(r"\s+", " ", html.unescape(snippet)).strip()
            if snippet not in excerpts:
                excerpts.append(snippet)
        entry["author_contact_excerpts"] = excerpts[:12]
        entry["contact_mailto_links"] = [{"text": re.sub(r"\s+", " ", a["text"]).strip(), "url": html.unescape(a["href"])} for a in parser.links if a["href"].lower().startswith("mailto:") and (len(log["pages"]) > 1 or "beukers" in a["href"].lower())]
        entry["status"] = "official_contact_metadata_read"
        entry["no_research_data_or_results_acquired"] = True
    except Exception as exc:
        entry["status"] = "failed"
        entry["error_type"] = type(exc).__name__
        entry["error"] = str(exc)[:200]
        if hasattr(exc, "headers"):
            entry["redirect_location"] = exc.headers.get("Location")
    lp.write_text(json.dumps(log, indent=2) + "\n")
    print(json.dumps(entry))


if __name__ == "__main__":
    main()
