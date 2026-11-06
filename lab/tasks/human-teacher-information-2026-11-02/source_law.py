"""Inspect admitted cached source, without importing or executing its task."""
from datetime import datetime, timezone
import ast
import hashlib
import json
import resource
import xml.etree.ElementTree as ET

from inspect_source import ROOT, OUT, SRC, workbook


def main():
    pins = []
    generated = SRC / "WIN_cursor_ibl_lastrun.py"
    raw = generated.read_bytes()
    code = raw.decode("utf-8-sig")
    lines = code.splitlines()
    tree = ast.parse(code)
    handlers = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ("trials", "practice") for t in node.targets):
            if isinstance(node.value, ast.Call) and ast.unparse(node.value.func) == "data.TrialHandler":
                handlers.append({"line": node.lineno, "handler": ast.unparse(node.targets[0]),
                                 "parameters": {k.arg: ast.unparse(k.value) for k in node.value.keywords}})
    target_lines = []
    for i, line in enumerate(lines):
        if i + 1 >= 4556 and any(s in line for s in ("eccentricity", "contrastDelta", "contrastLeft", "contrastRight", "probabilityLeft", "bias")):
            if len(line) < 1000:
                target_lines.append({"line": i + 1, "text": line.strip()})
    pins.append({"path": str(generated.relative_to(ROOT)), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})

    source = ROOT / "sources/human_learning_feasibility_2026-10-28/WIN_cursor_ibl.psyexp"
    raw = source.read_bytes()
    xml = ET.fromstring(raw)
    loops = []
    for node in xml.iter():
        if node.tag == "LoopInitiator":
            params = {p.get("name"): p.get("val") for p in node}
            inline = params.pop("conditions", "")
            loops.append({"loopType": node.get("loopType"), "name": node.get("name"),
                          "params": params,
                          "inline_conditions_characters": len(inline),
                          "inline_conditions_sha256": hashlib.sha256(inline.encode()).hexdigest()})
    pins.append({"path": str(source.relative_to(ROOT)), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})

    # Inspectable finite-source keys, independent of cached human responses.
    keys = []
    for i in range(10):
        path = SRC / ("pregen_sequence_%d.xlsx" % i)
        wbraw, members, cells = workbook(path)
        header = {"".join(x for x in c if x.isalpha()): v for c, v in cells[0].items()}
        pair = []
        for row in cells[1:3]:
            d = {header["".join(x for x in c if x.isalpha())]: v for c, v in row.items()}
            side = 1 if float(d["eccentricity"]) < 0 else -1
            pair.append(side * float(d["contrastDelta"]) / .2)
        keys.append({"source": i, "first_two_visible_signed_contrasts": pair})
    assert len({tuple(k["first_two_visible_signed_contrasts"]) for k in keys}) == 10
    result = {"utc": datetime.now(timezone.utc).isoformat(), "generated_task_handlers": handlers,
              "builder_loops": loops, "generated_main_target_and_contrast_statements": target_lines,
              "first_two_visible_source_keys": keys, "unique_keys": 10,
              "pins": pins, "rss_bytes_darwin": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "scope": "Static source plus finite planned-input audit; not a reconstructed stochastic teacher or hardware deployment certificate."}
    (OUT / "SOURCE_LAW.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
