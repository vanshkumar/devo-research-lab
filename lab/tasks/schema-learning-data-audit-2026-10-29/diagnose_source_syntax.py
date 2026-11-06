"""Source-only diagnostic; print no source text or literal contents."""
import ast
import hashlib
import json
from pathlib import Path
from notebook_source_reader import Reader, literal_alerts

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NEW = ROOT / "sources/schema_learning_data_audit_2026-10-29"


def main():
    frozen = json.loads((HERE / "NOTEBOOK_READER_FREEZE.json").read_text())
    assert hashlib.sha256((HERE / "notebook_source_reader.py").read_bytes()).hexdigest() == frozen["reader_sha256"]
    opaque = (NEW / (frozen["selected_path"] + ".opaque")).read_bytes()
    assert hashlib.sha1(b"blob " + str(len(opaque)).encode() + b"\0" + opaque).hexdigest() == frozen["selected_git_blob"]
    cells = Reader(opaque).extract()
    diagnostics = []
    for index, text in cells:
        try:
            ast.parse("\n".join("" if line.strip() == "%matplotlib inline" else line for line in text.splitlines()))
        except SyntaxError as error:
            line = text.splitlines()[error.lineno - 1] if error.lineno else ""
            prefix = "bang" if line.lstrip().startswith("!") else "percent" if line.lstrip().startswith("%") else "other"
            diagnostics.append({"cell_index": index, "error_line": error.lineno, "error_column": error.offset,
                                "line_prefix_class": prefix,
                                "bang_line_count": sum(line.lstrip().startswith("!") for line in text.splitlines()),
                                "percent_line_count": sum(line.lstrip().startswith("%") for line in text.splitlines()),
                                "literal_values_rendered": 0})
    (HERE / "SOURCE_SYNTAX_DIAGNOSTIC.json").write_text(json.dumps({"diagnostics": diagnostics, "new_network_requests": 0,
         "source_code_only_redecode_utf8_bytes": sum(len(text.encode()) for index, text in cells),
         "excluded_notebook_values_decoded": 0, "code_executed": False}, indent=2) + "\n")
    print(json.dumps(diagnostics))


if __name__ == "__main__":
    main()
