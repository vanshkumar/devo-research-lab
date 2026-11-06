"""Parse JSON structure without decoding excluded values; decode code.source only.

The full input is opaque bytes. Structural keys and code-cell type are matched
incrementally against fixed ASCII labels, never materialized as JSON values.
Unknown values are grammar-checked and skipped without creating str/int/float/
list/dict representations. Code source is decoded only after the entire JSON
object validates and its cell type is established, regardless of key order.
"""
import ast
import json
import re


class Reject(ValueError):
    pass


class Reader:
    def __init__(self, data, body_cap=14953, source_cap=65536, cell_cap=512, depth_cap=64, decode=None):
        if not isinstance(data, bytes) or len(data) > body_cap:
            raise Reject("opaque body type/cap")
        self.b, self.n, self.i = data, len(data), 0
        self.source_cap, self.cell_cap, self.depth_cap = source_cap, cell_cap, depth_cap
        self.code_ranges, self.decoded_spans = [], []
        self.cell_count = 0
        self.decoder = decode or json.loads

    def ws(self):
        while self.i < self.n and self.b[self.i] in b" \t\r\n":
            self.i += 1

    def take(self, c):
        self.ws()
        if self.i >= self.n or self.b[self.i] != c:
            raise Reject("JSON structure/truncation")
        self.i += 1

    def peek(self):
        self.ws()
        if self.i >= self.n:
            raise Reject("JSON truncation")
        return self.b[self.i]

    def string(self, labels=()):
        self.take(34)
        start, k = self.i - 1, 0
        candidates = list(labels)  # only fixed caller-supplied labels
        while self.i < self.n:
            c = self.b[self.i]
            self.i += 1
            if c == 34:
                hit = next((s for s in candidates if len(s) == k), None)
                return start, self.i, hit
            if c < 32:
                raise Reject("JSON string control byte")
            if c == 92:
                if self.i >= self.n:
                    raise Reject("JSON escape truncation")
                esc = self.b[self.i]
                self.i += 1
                if esc == 117:
                    c = 0
                    for _ in range(4):
                        if self.i >= self.n:
                            raise Reject("JSON unicode truncation")
                        h = self.b[self.i]
                        self.i += 1
                        if 48 <= h <= 57:
                            v = h - 48
                        elif 65 <= h <= 70:
                            v = h - 55
                        elif 97 <= h <= 102:
                            v = h - 87
                        else:
                            raise Reject("JSON unicode escape")
                        c = 16 * c + v
                else:
                    escapes = {34: 34, 92: 92, 47: 47, 98: 8, 102: 12, 110: 10, 114: 13, 116: 9}
                    if esc not in escapes:
                        raise Reject("JSON escape")
                    c = escapes[esc]
            candidates = [s for s in candidates if k < len(s) and ord(s[k]) == c]
            k += 1
        raise Reject("JSON string truncation")

    def number(self):
        # Validate byte grammar only; never convert or retain its numeric value.
        if self.b[self.i] == 45:
            self.i += 1
        if self.i >= self.n:
            raise Reject("JSON number truncation")
        if self.b[self.i] == 48:
            self.i += 1
        elif 49 <= self.b[self.i] <= 57:
            while self.i < self.n and 48 <= self.b[self.i] <= 57:
                self.i += 1
        else:
            raise Reject("JSON number")
        if self.i < self.n and self.b[self.i] == 46:
            self.i += 1
            start = self.i
            while self.i < self.n and 48 <= self.b[self.i] <= 57:
                self.i += 1
            if self.i == start:
                raise Reject("JSON fraction")
        if self.i < self.n and self.b[self.i] in b"eE":
            self.i += 1
            if self.i < self.n and self.b[self.i] in b"+-":
                self.i += 1
            start = self.i
            while self.i < self.n and 48 <= self.b[self.i] <= 57:
                self.i += 1
            if self.i == start:
                raise Reject("JSON exponent")

    def skip(self, depth=0):
        if depth > self.depth_cap:
            raise Reject("JSON depth cap")
        c = self.peek()
        if c == 34:
            self.string()
        elif c == 123:
            self.take(123)
            if self.peek() == 125:
                self.take(125)
                return
            while True:
                self.string()
                self.take(58)
                self.skip(depth + 1)
                c = self.peek()
                self.take(c)
                if c == 125:
                    return
                if c != 44:
                    raise Reject("JSON object separator")
        elif c == 91:
            self.take(91)
            if self.peek() == 93:
                self.take(93)
                return
            while True:
                self.skip(depth + 1)
                c = self.peek()
                self.take(c)
                if c == 93:
                    return
                if c != 44:
                    raise Reject("JSON array separator")
        elif c == 45 or 48 <= c <= 57:
            self.number()
        else:
            for literal in [b"true", b"false", b"null"]:
                if self.b.startswith(literal, self.i):
                    self.i += len(literal)
                    return
            raise Reject("JSON token")

    def cell(self):
        self.cell_count += 1
        if self.cell_count > self.cell_cap:
            raise Reject("cell cap")
        self.take(123)
        seen, code, source = set(), False, None
        if self.peek() == 125:
            raise Reject("cell without type")
        while True:
            _, _, key = self.string(("cell_type", "source"))
            if key is not None:
                if key in seen:
                    raise Reject("duplicate critical cell key")
                seen.add(key)
            self.take(58)
            if key == "cell_type":
                _, _, matched = self.string(("code",))
                code = matched == "code"
            else:
                self.ws()
                start = self.i
                self.skip()
                if key == "source":
                    source = (start, self.i)
            c = self.peek()
            self.take(c)
            if c == 125:
                break
            if c != 44:
                raise Reject("cell separator")
        if "cell_type" not in seen:
            raise Reject("cell without type")
        if code:
            if source is None:
                raise Reject("code cell without source")
            self.code_ranges.append((self.cell_count - 1, source))

    def cells(self):
        self.take(91)
        if self.peek() == 93:
            self.take(93)
            return
        while True:
            self.cell()
            c = self.peek()
            self.take(c)
            if c == 93:
                return
            if c != 44:
                raise Reject("cells separator")

    def source(self, bounds):
        self.i = bounds[0]
        parts = []

        def leaf():
            start, end, _ = self.string()
            self.decoded_spans.append((start, end))
            value = self.decoder(self.b[start:end])
            if not isinstance(value, str):
                raise Reject("source string decoding")
            parts.append(value)

        if self.peek() == 34:
            leaf()
        elif self.peek() == 91:
            self.take(91)
            if self.peek() == 93:
                self.take(93)
            else:
                while True:
                    if self.peek() != 34:
                        raise Reject("nonstring source item")
                    leaf()
                    c = self.peek()
                    self.take(c)
                    if c == 93:
                        break
                    if c != 44:
                        raise Reject("source separator")
        else:
            raise Reject("unsupported code source profile")
        if self.i != bounds[1]:
            raise Reject("source range mismatch")
        result = "".join(parts)
        if len(result.encode("utf-8")) > self.source_cap:
            raise Reject("decoded source cap")
        return result

    def extract(self):
        self.take(123)
        seen_cells = False
        if self.peek() == 125:
            raise Reject("notebook without cells")
        while True:
            _, _, key = self.string(("cells",))
            self.take(58)
            if key == "cells":
                if seen_cells:
                    raise Reject("duplicate cells")
                seen_cells = True
                self.cells()
            else:
                self.skip()
            c = self.peek()
            self.take(c)
            if c == 125:
                break
            if c != 44:
                raise Reject("root separator")
        self.ws()
        if self.i != self.n or not seen_cells:
            raise Reject("trailing bytes or missing cells")
        # Nothing was decoded before the full opaque structure validated.
        result = []
        total = 0
        for index, bounds in self.code_ranges:
            text = self.source(bounds)
            total += len(text.encode("utf-8"))
            if total > self.source_cap:
                raise Reject("total decoded source cap")
            result.append((index, text))
        return result


def literal_alerts(text):
    """Conservative pre-render stop for possible embedded participant literals.

    Flags contain locations/categories only, never literal contents. This is
    triage, not semantic proof that a literal is participant data.
    """
    cleaned = "\n".join("" if line.strip() == "%matplotlib inline" else line for line in text.splitlines())
    try:
        tree = ast.parse(cleaned)
    except SyntaxError:
        return [{"line": 0, "category": "source_not_plain_Python_requires_stop"}]
    alerts = []
    sensitive = re.compile(r"participant|subject|worker|prolific|response|correct|attention|accuracy|performance|gender|age", re.I)

    def literal(node):
        if isinstance(node, ast.Constant):
            return True
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return all(literal(v) for v in node.elts)
        if isinstance(node, ast.Dict):
            return all(k is not None and literal(k) and literal(v) for k, v in zip(node.keys, node.values))
        if isinstance(node, ast.UnaryOp):
            return literal(node.operand)
        return False

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [n.id for target in targets for n in ast.walk(target) if isinstance(n, ast.Name)]
            value = node.value
            nonempty = isinstance(value, (ast.List, ast.Tuple, ast.Set, ast.Dict)) and bool(getattr(value, "elts", getattr(value, "keys", [])))
            if nonempty and literal(value) and any(sensitive.search(name) for name in names):
                alerts.append({"line": node.lineno, "category": "sensitive_name_with_embedded_literal"})
        if isinstance(node, (ast.List, ast.Tuple)) and len(node.elts) >= 4:
            if all(isinstance(v, ast.Constant) and isinstance(v.value, (int, float)) for v in node.elts):
                alerts.append({"line": node.lineno, "category": "numeric_data_literal_requires_stop"})
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if len(node.value) > 160 and ("\n" in node.value or sensitive.search(node.value)):
                alerts.append({"line": node.lineno, "category": "large_embedded_string_requires_stop"})
    for line_number, line in enumerate(text.splitlines(), 1):
        if re.search(r"^\s*#.*(?:participant|subject|worker|response|accuracy)\s*[:=]", line, re.I):
            alerts.append({"line": line_number, "category": "possible_data_comment_requires_stop"})
    return alerts
