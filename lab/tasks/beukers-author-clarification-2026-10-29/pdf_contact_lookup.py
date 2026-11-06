"""Second/final official contact lookup; keep author/contact metadata only."""
import hashlib
import importlib.util
import io
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
URL = "https://gershmanlab.com/pubs/Beukers24.pdf"


def main():
    available = [name for name in ["pypdf", "PyPDF2", "fitz", "pdfplumber"] if importlib.util.find_spec(name)]
    if sys.argv[1] == "inspect":
        print(json.dumps({"existing_PDF_text_libraries": available, "network_requests": 0}))
        return
    path = HERE / "CONTACT_LOOKUPS.json"
    log = json.loads(path.read_text())
    assert len(log["lookups"]) == 1
    entry = {"number": 2, "url": URL, "utc": datetime.now(timezone.utc).isoformat(),
             "purpose": "already-cited official lab paper: corresponding-author contact metadata only", "status": "started", "body_bytes": 0}
    log["lookups"].append(entry)
    path.write_text(json.dumps(log, indent=2) + "\n")
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"})
        with urllib.request.urlopen(req, timeout=20) as response:
            entry["http_status"] = response.status
            raw = response.read(3_000_001)
        entry["body_bytes"] = len(raw)
        assert len(raw) <= 3_000_000, "official-contact PDF cap"
        entry["sha256"] = hashlib.sha256(raw).hexdigest()
        entry["annotation_mailto_addresses"] = sorted(set(m.decode("ascii", "replace") for m in re.findall(rb"mailto:([^\s()<>?\\]+)", raw)))
        text = ""
        if "pypdf" in available:
            from pypdf import PdfReader
            text = PdfReader(io.BytesIO(raw)).pages[0].extract_text()
        elif "PyPDF2" in available:
            from PyPDF2 import PdfReader
            text = PdfReader(io.BytesIO(raw)).pages[0].extract_text()
        elif "fitz" in available:
            import fitz
            with fitz.open(stream=raw, filetype="pdf") as document:
                text = document[0].get_text()
        elif "pdfplumber" in available:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(raw)) as document:
                text = document.pages[0].extract_text()
        if text:
            lines = [line.strip() for line in text.splitlines()]
            entry["first_page_author_contact_lines"] = [line for line in lines if re.search(r"Beukers|Gershman|correspond|e-mail|email|@", line, re.I)]
            entry["first_page_email_addresses"] = sorted(set(re.findall(r"[A-Za-z0-9_.+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)))
            entry["first_page_text_processing"] = "Only author/contact lines retained; paper scientific content not rendered or saved. No later page text inspected."
        entry["existing_PDF_text_libraries"] = available
        entry["status"] = "official_contact_metadata_only"
        entry["research_data_or_results_saved"] = False
    except Exception as exc:
        entry["status"] = "failed"
        entry["error_type"] = type(exc).__name__
        entry["error"] = str(exc)[:200]
    path.write_text(json.dumps(log, indent=2) + "\n")
    print(json.dumps(entry))


if __name__ == "__main__":
    main()
