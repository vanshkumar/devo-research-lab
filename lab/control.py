#!/usr/bin/env python3
"""Small fail-closed lab process guard. Python stdlib only; see policy limitations.

CLI: status | read PATH | check TASK | reserve TASK --json REQUEST
     record {proposal,decision,review,reconcile} --json RECORD
Hooks: --hook (PreToolUse); --post-hook (capture actual identity/allowance).
All mutating CLI commands require a short-lived authorization written by the
PreToolUse hook for that exact command and actual session. No CLI resume exists.
"""
from __future__ import annotations

import argparse
import codecs
import contextlib
import datetime as dt
import fcntl
import glob
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile
import uuid
from zoneinfo import ZoneInfo


class Denied(ValueError):
    pass


class QuietParser(argparse.ArgumentParser):
    def error(self, message):
        raise Denied("Invalid controller arguments: " + message)


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def stamp(value):
    return value.isoformat().replace("+00:00", "Z")


def parsed_time(value):
    try:
        result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError()
        return result
    except (AttributeError, TypeError, ValueError):
        raise Denied("A timezone-aware timestamp is required") from None


def require(condition, reason):
    if not condition:
        raise Denied(reason)


def uuid_ok(value):
    try:
        return str(uuid.UUID(value)) == value
    except (ValueError, TypeError, AttributeError):
        return False


def leaf(name):
    return str(name).split(".")[-1].split("__")[-1]


def role_name(value):
    return {"investigation_lead": "investigator", "independent_reviewer": "reviewer"}.get(value, value)


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix="." + path.name)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Gate:
    def __init__(self, root=None, now=None, allow_invalid_registry=False):
        self.root = Path(root or Path(__file__).resolve().parent.parent).resolve()
        self.policy = self.load(self.root / "lab/policy.json")
        self.registry_error = None
        try:
            self.registry = self.load(self.root / "lab/registry.json")
        except Denied as error:
            if not allow_invalid_registry:
                raise
            # Hooks must retain policy-defined repair and safe read access.
            # An unavailable registry never grants scientific execution.
            self.registry = {}
            self.registry_error = str(error)
        self.state_path = self.root / "lab/control-state.json"
        self.now = now or dt.datetime.now(dt.timezone.utc)
        self.today = self.now.astimezone(ZoneInfo(self.registry.get("timezone", "America/New_York"))).date().isoformat()

    @staticmethod
    def load(path):
        try:
            with Path(path).open() as stream:
                value = json.load(stream)
            require(isinstance(value, dict), "Expected JSON object: " + str(path))
            return value
        except (OSError, json.JSONDecodeError) as error:
            raise Denied("Missing or invalid record: " + str(path)) from error

    @contextlib.contextmanager
    def locked(self):
        lock_path = self.root / "lab/control-state.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            state = self.load(self.state_path)
            state.setdefault("days", {})
            state.setdefault("permits", {})
            state.setdefault("assignments", {})
            state.setdefault("authorizations", [])
            state.setdefault("records", [])
            yield state
            atomic_json(self.state_path, state)

    def path(self, name):
        require(isinstance(name, str) and name, "A repository path is required")
        result = (self.root / name).resolve()
        require(result.is_relative_to(self.root), "Path escapes repository")
        return result

    def protected(self, name):
        relative = self.path(name).relative_to(self.root).as_posix()
        return any(relative == part or relative.startswith(part + "/") for part in self.policy["protected_paths"])

    def running(self, state):
        require(state.get("governance", {}).get("status") == "running", "Research governance is paused")
        require(self.registry.get("governance", {}).get("status") == "running", "Registry governance is paused or unconfirmed")
        if self.registry.get("governance", {}).get("mode") == "simple_manual":
            return
        require(state["governance"].get("hook_trust_verified") is True, "Project hook trust has not been verified")
        require(state["governance"].get("canary_verified") is True, "Live hook canaries have not been verified")

    def effective_budget(self, state):
        budget = self.registry["budget"]
        override = budget.get("date_scoped_overrides", {}).get(self.today, {})
        if override.get("expires_after_local_date") != self.today:
            override = {}
        floor = override.get("minimum_account_remaining_percent_for_new_work", budget["minimum_account_remaining_percent_for_new_work"])
        starts = budget["max_autonomous_max_agent_starts_per_day"]
        cycles = budget["max_substantive_pi_cycles_per_day"]
        if override.get("daily_max_agent_start_ceiling") == "usage_governed_today":
            starts = None
        if override.get("daily_substantive_pi_cycle_ceiling") == "usage_governed_today":
            cycles = None
        prior = self.registry.get("daily_usage", {})
        day = state.get("days", {}).get(self.today, {})
        return {"date": self.today, "floor": floor, "start_limit": starts, "cycle_limit": cycles,
                "starts": max(day.get("starts", 0), prior.get("max_agent_starts_reserved", 0) if prior.get("date") == self.today else 0),
                "cycles": max(day.get("cycles", 0), prior.get("substantive_pi_cycles_reserved", 0) if prior.get("date") == self.today else 0),
                "cycle_ids": day.get("cycle_ids", [])}

    def allowance(self, state):
        observation = state.get("allowance") or {}
        require(observation.get("source") == "get_usage_limits" and re.fullmatch(r"[a-f0-9]{64}", observation.get("response_sha256", "")), "No captured account allowance telemetry")
        age = (self.now - parsed_time(observation.get("observed_at"))).total_seconds()
        require(0 <= age <= self.policy["allowance_max_age_seconds"], "Account allowance telemetry is stale")
        remaining = observation.get("remaining_percent")
        require(isinstance(remaining, (int, float)) and 0 <= remaining <= 100, "Invalid account allowance")
        require(remaining > self.effective_budget(state)["floor"], "Account allowance is at or below the effective reserve floor")
        return remaining

    def task_path(self, task_id):
        require(isinstance(task_id, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,99}", task_id), "Invalid task ID")
        return self.root / "lab/contracts" / (task_id + ".json")

    def reference(self, reference):
        require(isinstance(reference, dict), "Missing evidence reference")
        path = self.path(reference.get("path"))
        require(path.is_file(), "Missing evidence file: " + str(path))
        require(path.stat().st_size <= 4 * 1024 * 1024, "Evidence reference exceeds 4MB bound")
        require(re.fullmatch(r"[a-f0-9]{64}", reference.get("sha256", "")) is not None, "Evidence SHA256 is required")
        require(digest(path.read_bytes()) == reference["sha256"], "Stale evidence hash: " + str(path))
        return path

    def identity(self, state, session):
        if session in self.policy["operator_session_ids"]:
            return "operator", None
        if session == self.policy["pi_session_id"]:
            return "pi", None
        manual = self.registry.get("governance", {}).get("mode") == "simple_manual"
        matches = []
        if manual:
            # A reused chat can start before the send returns. Its ordinary
            # reservation already supplies the exact owner and scoped paths;
            # waiting for a post-send status creates a startup race.
            matches = [task["id"] for task in self.registry.get("tasks", [])
                       if task.get("thread_id") == session
                       and task.get("status") in ("reserved", "dispatched", "running", "idle")]
        else:
            for task_id, assignment in state.get("assignments", {}).items():
                if assignment.get("thread_id") == session and assignment.get("status") in ("running", "idle"):
                    matches.append(task_id)
            for task in self.registry.get("tasks", []):
                if task.get("thread_id") == session and task.get("status") in ("running", "idle", "dispatched") and task["id"] not in state.get("assignments", {}):
                    matches.append(task["id"])
        require(len(matches) == 1, "Session has no unique active durable task contract")
        if manual:
            task = next(t for t in self.registry["tasks"] if t["id"] == matches[0])
            role = role_name(task.get("role"))
            require(role in ("investigator", "reviewer"), "Unknown registered worker role")
            path = self.path(task.get("path"))
            require(path.is_relative_to(self.root / "lab/tasks") or path.is_relative_to(self.root / "lab/reviews"), "Worker needs an owned task path")
            owned = task.get("owned_paths") or [str(path)]
            require(isinstance(owned, list), "Worker owned paths must be an explicit list")
            allowed = []
            for name in owned:
                candidate = self.path(name)
                parts = candidate.relative_to(self.root).parts
                scoped = len(parts) >= 2 and parts[0] in ("sources", "campaigns", "experiments") or len(parts) >= 3 and parts[:2] in (("lab", "tasks"), ("lab", "reviews"))
                require(scoped and not self.protected(str(candidate)), "Worker ownership must name scoped task/source paths, not root or process controls")
                allowed.append(str(candidate))
            return role, {"role": role, "task_id": task["id"], "allowed_paths": allowed}
        contract = self.contract(matches[0], state)
        return contract["role"], contract

    def known_threads(self, state):
        return {self.policy["pi_session_id"], *self.policy["operator_session_ids"],
                *(task.get("thread_id") for task in self.registry.get("tasks", []) if uuid_ok(task.get("thread_id"))),
                *(item.get("thread_id") for item in state.get("assignments", {}).values() if uuid_ok(item.get("thread_id")))}

    def contract(self, task_id, state):
        contract = self.load(self.task_path(task_id))
        require(contract.get("schema_version") == 1 and contract.get("task_id") == task_id, "Invalid task contract")
        require(contract.get("status") == "approved", "Task contract is not approved")
        require(contract.get("role") in ("investigator", "reviewer"), "Unknown task role")
        require(contract.get("question_id") == self.registry["question"]["id"], "Contract does not address the approved question")
        expiry = parsed_time(contract.get("expires_at"))
        require(self.now < expiry <= self.now + dt.timedelta(days=self.policy["max_contract_age_days"]), "Task contract is stale or unbounded")
        self.reference(contract.get("brief"))
        stage = contract.get("stage")
        require(stage in ("feasibility", "development", "validation"), "Unknown scientific stage")
        require(isinstance(contract.get("controls"), list) and bool(contract["controls"]), "Contract must name scientific controls")
        require(isinstance(contract.get("artifacts"), list) and bool(contract["artifacts"]), "Contract must name expected artifacts")
        require(all(isinstance(name, str) and name and not Path(name).is_absolute() and ".." not in Path(name).parts for name in contract["artifacts"]), "Expected artifacts must have bounded relative names")
        require(isinstance(contract.get("evidence_scope"), str) and bool(contract["evidence_scope"].strip()), "Missing permitted evidence scope")
        require(isinstance(contract.get("data_access"), list), "Missing explicit data access list")
        blocked = set(self.policy["blocked_data_ids"])
        require(not any(str(item).lower() in blocked for item in contract["data_access"]), "User-only protected data are blocked")
        require(contract.get("protected_data_release") is not True, "A contract cannot release protected data")
        owner = state.get("assignments", {}).get(task_id, {}).get("thread_id") or contract.get("owner_thread_id")
        require(owner is None or (uuid_ok(owner) and owner != self.policy["pi_session_id"] and owner not in self.policy["operator_session_ids"]), "Worker must have a distinct actual durable thread identity")
        paths = contract.get("allowed_paths")
        require(isinstance(paths, list) and bool(paths), "Missing owned paths")
        expected_prefix = "lab/reviews/" + task_id if contract["role"] == "reviewer" else "lab/tasks/" + task_id
        require(all(self.path(part).relative_to(self.root).as_posix() == expected_prefix or self.path(part).relative_to(self.root).as_posix().startswith(expected_prefix + "/") for part in paths), "Owned paths must stay in this task directory")
        budget = contract.get("budget", {})
        require(type(budget.get("max_starts")) is int and 1 <= budget["max_starts"] <= 2, "Missing or excessive task start bound")
        require(isinstance(budget.get("cycle_id"), str) and bool(budget["cycle_id"]), "Missing PI decision cycle")
        if stage == "validation":
            self.validation(contract, state, owner)
        return contract

    def validation(self, contract, state, owner):
        gate = contract.get("validation_gate", {})
        require(gate.get("status") == "pass", "Validation gate has not passed")
        review_id = gate.get("review_record_id")
        reviews = [r for r in state.get("records", []) if r.get("id") == review_id and r.get("kind") == "review" and r.get("task_id") == contract["task_id"]]
        require(len(reviews) == 1, "Validation requires an actual reviewer-originated record")
        review = reviews[0]
        reviewer = review.get("actor_session_id")
        implementation_owner = contract.get("implementation_owner_thread_id") or owner
        require(uuid_ok(implementation_owner) and uuid_ok(reviewer) and reviewer != implementation_owner and reviewer != self.policy["pi_session_id"], "Implementation owner cannot self-review")
        require(review.get("verdict") == "pass", "Independent review did not pass")
        for key in ("review", "exposure", "freeze"):
            self.reference(review.get(key))
        controls = review.get("controls", [])
        require(set(self.policy["validation_control_names"]).issubset({r.get("name") for r in controls}), "Missing required scientific controls")
        for control in controls:
            require(control.get("status") == "pass", "A scientific control did not pass")
            self.reference(control)
        artifacts = review.get("artifacts", [])
        require(set(contract["artifacts"]).issubset({item.get("name") for item in artifacts}), "Review must pin all decisive planned scientific artifacts")
        for artifact in artifacts:
            path = self.reference(artifact)
            require(artifact.get("name") in contract["artifacts"] and any(path == self.path(prefix) / artifact["name"] for prefix in contract["allowed_paths"]), "Reviewed scientific artifact does not match its task contract")

    def read(self, name):
        if self.registry.get("governance", {}).get("mode") == "simple_manual":
            return self.context_file(name).read_text()
        path = self.path(name)
        relative = path.relative_to(self.root)
        require(not any(part.lower() in self.policy["read_denied_components"] for part in relative.parts), "Raw data/payload directories are not PI evidence reads")
        require(path.suffix.lower() in self.policy["read_extensions"], "PI may read saved text evidence/source only")
        require(path.is_file() and path.stat().st_size <= self.policy["max_read_bytes"], "Missing file or evidence read exceeds bound")
        raw = path.read_bytes()
        require(b"\0" not in raw, "Binary payload is not saved evidence")
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            raise Denied("PI evidence must be UTF-8 text") from None

    def context_file(self, name, base=None, check_content=True, window=None):
        """Validate ordinary context without consulting assignments or runtime state."""
        path = self.path(str((base or self.root) / name))
        parts = path.relative_to(self.root).parts
        denied = set(self.policy["read_denied_components"]) - {"data"}
        require(not any(part.lower() in denied for part in parts), "Protected/raw payload directories are outside ordinary context reads")
        extension = path.suffix.lower()
        require(extension in self.policy.get("context_read_extensions", self.policy["read_extensions"]), "Ordinary context reads exclude binary and data payload formats")
        if any(part.lower() == "data" for part in parts):
            require(extension in self.policy["source_document_extensions"], "Only source code and documentation may be read under data directories")
        require(path.is_file(), "Missing context file")
        if not check_content:
            return path
        if window is not None:
            self.context_excerpt(path, window)
            return path
        require(path.stat().st_size <= self.policy["max_read_bytes"], "Context read exceeds the existing size bound")
        raw = path.read_bytes()
        require(b"\0" not in raw, "Binary payload is not ordinary context")
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            raise Denied("Ordinary context must be UTF-8 text") from None
        return path

    def context_image(self, name):
        """Recognize saved report figures without allowing raw image payloads."""
        path = self.path(name)
        parts = path.relative_to(self.root).parts
        require(not any(part.lower() in self.policy["read_denied_components"] for part in parts), "Protected/raw directories are not report figures")
        require(len(parts) >= 4 and parts[0] == "lab" and parts[1] in ("tasks", "reviews"), "Image must be a saved study report figure")
        folders = parts[3:-1]
        require(all(part.lower() in ("figures", "plots") for part in folders)
                and (folders or re.search(r"figure|plot|chart|summary", path.stem, re.I)), "Image must be a named summary figure or in a report figures/plots folder")
        require(path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"), "Only raster report figures are ordinary image reads")
        require(path.is_file() and path.stat().st_size <= self.policy["max_read_bytes"], "Missing report figure or image exceeds the existing read bound")
        with path.open("rb") as source:
            header = source.read(12)
        valid = (path.suffix.lower() == ".png" and header.startswith(b"\x89PNG\r\n\x1a\n")
                 or path.suffix.lower() in (".jpg", ".jpeg") and header.startswith(b"\xff\xd8\xff")
                 or path.suffix.lower() == ".webp" and header[:4] == b"RIFF" and header[8:12] == b"WEBP")
        require(valid, "Report figure format does not match its extension")
        return path

    def context_excerpt(self, path, window):
        """Keep the existing content ceiling for a bounded ordinary text read."""
        limit = self.policy["max_read_bytes"]
        decoder = codecs.getincrementaldecoder("utf-8")()
        size, lines, ending = 0, 0, b""
        try:
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(65536), b""):
                    require(b"\0" not in chunk, "Binary payload is not ordinary context")
                    decoder.decode(chunk)
                    size += len(chunk)
                    lines += chunk.count(b"\n")
                    ending = chunk[-1:]
            decoder.decode(b"", final=True)
        except UnicodeDecodeError:
            raise Denied("Ordinary context must be UTF-8 text") from None
        if size <= limit:
            return
        lines += bool(size and ending != b"\n")
        if window[0] == "sed":
            first, last = window[1:]
            # Conservatively cover an unusual backwards sed range through EOF.
            last = lines if last < first else last
        else:
            program, unit, count, from_start = window
            if unit == "bytes":
                length = max(0, size - max(0, count - 1)) if from_start else min(size, count)
                require(length <= limit, "Context excerpt exceeds the existing size bound")
                return
            if program == "head":
                first, last = 1, count
            elif from_start:
                first, last = max(1, count), lines
            else:
                first, last = max(1, lines - count + 1), lines
        first, last = max(1, first), min(lines, last)
        if first > last:
            return
        selected, number = 0, 1
        with path.open("rb") as source:
            while number <= last:
                chunk = source.readline(limit + 1)
                if not chunk:
                    break
                if number >= first:
                    selected += len(chunk)
                    require(selected <= limit, "Context excerpt exceeds the existing size bound")
                number += chunk.endswith(b"\n")

    def context_base(self, name=None):
        base = self.path(name or str(self.root))
        require(base.is_dir(), "Read working directory must exist inside the project")
        denied = set(self.policy["read_denied_components"])
        require(not any(part.lower() in denied for part in base.relative_to(self.root).parts), "Raw/payload directories are not ordinary browsing roots")
        return base

    def context_targets(self, words, base, content=True, inventory=False, window=None):
        for word in words:
            self.path(str(base / word))
            paths = glob.glob(str(base / word), recursive=True) if glob.has_magic(word) else [str(base / word)]
            require(paths, "No context path matches the requested pattern")
            for value in paths:
                path = self.path(value)
                if inventory:
                    require(path.exists(), "Missing inventory path")
                elif content:
                    self.context_file(str(path), window=window)
                elif path.is_dir():
                    self.context_base(str(path))
                else:
                    self.context_file(str(path))

    def context_search(self, paths, base, patterns=(), content=True, hidden=False):
        for value in paths or ["."]:
            path = self.path(str(base / value))
            if path.is_file():
                self.context_file(str(path))
                continue
            self.context_base(str(path))
            if content:
                require(patterns, "For directory content searches, select notes/source with a glob or give explicit context files")
                for pattern in patterns:
                    match = re.fullmatch(r"(?:\*\*/)?\*\.([a-zA-Z0-9]+)", pattern)
                    require(match is not None and "." + match[1].lower() in self.policy["context_read_extensions"], "Directory content searches require a plain context extension glob such as *.md or *.py")
                    for candidate in path.rglob(pattern):
                        relative = candidate.relative_to(path)
                        if candidate.is_file() and (hidden or not any(part.startswith(".") for part in relative.parts)):
                            self.context_file(str(candidate), check_content=False)

    def context_command(self, arguments):
        command = arguments.get("cmd", arguments.get("command"))
        if not isinstance(command, str):
            return False
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        try:
            tokens = list(lexer)
        except ValueError:
            raise Denied("Malformed read command") from None
        if not tokens or tokens[0] not in ("cat", "sed", "head", "tail", "rg", "ls", "pwd", "wc", "python3"):
            return False
        if tokens[0] == "python3":
            if len(tokens) < 3 or tokens[1] != str(self.root / "lab/control.py") or tokens[2] not in ("read", "status"):
                return False
        require(not any(re.fullmatch(r"[;&|<>()]+", token) for token in tokens) and not re.search(r"[\n\r`$]", command), "Ordinary reads do not run shell composition, substitutions or redirects")
        quote, escaped = None, False
        for character in command:
            if escaped:
                escaped = False
            elif character == "\\" and quote != "'":
                escaped = True
            elif quote:
                if character == quote:
                    quote = None
            elif character in ("'", '"'):
                quote = character
            else:
                require(character not in "*?[]{}~", "Quote search patterns; use Glob for filename discovery instead of shell expansion")
        require(not arguments.get("shell") and arguments.get("sandbox_permissions", "use_default") == "use_default", "Ordinary reads cannot change shell or permissions")
        base = self.context_base(arguments.get("workdir", arguments.get("cwd")))
        program, words = tokens[0], tokens[1:]
        if program == "python3":
            parsed = parse_cli(tokens[2:])
            if parsed.operation == "read":
                self.context_file(parsed.path)
            return True
        if program == "pwd":
            require(not words or words in (["-L"], ["-P"]), "Unsupported pwd argument")
            return True
        if program == "sed":
            require(len(words) >= 3 and words[0] == "-n" and re.fullmatch(r"[0-9]+(?:,[0-9]+)?p", words[1]), "Only numeric sed -n read ranges are ordinary reads")
            bounds = [int(value) for value in words[1][:-1].split(",")]
            self.context_targets(words[2:], base, window=("sed", bounds[0], bounds[-1]))
            return True
        if program == "rg":
            paths, patterns, positionals = [], [], []
            files = "--files" in words
            explicit_query = False
            flags = {"--files", "-n", "--line-number", "-i", "--ignore-case", "-l", "--files-with-matches", "-F", "--fixed-strings", "-s", "--case-sensitive", "--hidden", "--no-heading", "--heading", "--count", "-c"}
            index = 0
            while index < len(words):
                word = words[index]
                if word in ("-g", "--glob", "-e", "--regexp", "-m", "--max-count", "-A", "-B", "-C"):
                    require(index + 1 < len(words), "Missing rg option value")
                    index += 1
                    if word in ("-g", "--glob"):
                        patterns.append(words[index])
                    elif word in ("-e", "--regexp"):
                        explicit_query = True
                    else:
                        require(words[index].isdigit(), "rg context/count bounds must be numeric")
                elif word.startswith("--glob="):
                    patterns.append(word.split("=", 1)[1])
                elif word.startswith("-"):
                    require(word in flags, "Unsupported rg option; executable preprocessing is not an ordinary read")
                else:
                    positionals.append(word)
                index += 1
            paths = positionals if files or explicit_query else positionals[1:]
            require(files or explicit_query or bool(positionals), "rg requires a search pattern")
            self.context_search(paths, base, patterns, content=not files, hidden="--hidden" in words)
            return True
        paths = []
        index = 0
        unit, count, from_start = "lines", 10, False
        flags = {"cat": {"-n", "-b", "-s", "-v", "-e", "-t"}, "ls": {"-l", "-a", "-h", "-la", "-lah", "-lh", "-al", "-1"}, "wc": {"-l", "-w", "-c", "-m"}, "head": set(), "tail": set()}
        while index < len(words):
            word = words[index]
            if program in ("head", "tail") and word in ("-n", "-c"):
                index += 1
                require(index < len(words) and re.fullmatch(r"[+]?[0-9]+", words[index]), "Read limit must be numeric")
                unit, count = ("lines" if word == "-n" else "bytes"), int(words[index])
                from_start = program == "tail" and words[index].startswith("+")
            elif word.startswith("-"):
                require(word in flags[program] or program in ("head", "tail") and re.fullmatch(r"-[0-9]+", word), "Unsupported read option")
                if program in ("head", "tail"):
                    unit, count, from_start = "lines", int(word[1:]), False
            else:
                paths.append(word)
            index += 1
        require(paths or program == "ls", "Give explicit context files; stdin is not an ordinary project read")
        window = (program, unit, count, from_start) if program in ("head", "tail") else None
        self.context_targets(paths or ["."], base, content=program != "ls", window=window)
        return True

    def ordinary_read(self, name, arguments):
        if name in self.policy["pi_read_tools"] or name in ("list_archived_threads", "curr_time", "get_goal"):
            return True
        if name == "view_image":
            if not set(arguments).issubset({"path", "detail"}):
                return False
            try:
                self.context_image(arguments.get("path", ""))
            except Denied:
                # Non-report images retain their existing scientific-role rules.
                return False
            return True
        if name in ("Bash", "bash", "exec_command"):
            return self.context_command(arguments)
        if name == "Read":
            self.context_file(arguments.get("file_path", arguments.get("path", "")))
            return True
        if name == "Glob":
            base = self.context_base(arguments.get("path"))
            self.context_targets([arguments.get("pattern", "")], base, content=False, inventory=True)
            return True
        if name == "Grep":
            patterns = [arguments["glob"]] if arguments.get("glob") else []
            if not patterns and arguments.get("type"):
                extension = {"python": "py", "javascript": "js", "typescript": "ts", "markdown": "md"}.get(arguments["type"], arguments["type"])
                require("." + extension in self.policy["context_read_extensions"], "Grep type must select ordinary source or notes")
                patterns = ["*." + extension]
            self.context_search([arguments.get("path", ".")], self.root, patterns)
            return True
        return False

    def active(self, state):
        found = {}
        for task in self.registry.get("tasks", []):
            if task.get("status") in ("running", "reserved", "dispatched", "pending_reconcile", "idle", "held_unfinished"):
                found[task["id"]] = task.get("thread_id") or "unreconciled native assignment"
        for task_id, item in state.get("assignments", {}).items():
            if item.get("status") in ("reserved", "pending_reconcile", "running", "idle", "held_unfinished"):
                found[task_id] = item.get("thread_id") or "pending actual identity"
            elif item.get("status") == "completed":
                found.pop(task_id, None)
        return found

    def reserve(self, task_id, request, actor):
        require(actor == self.policy["pi_session_id"], "Only the canonical PI reserves scientific work")
        with self.locked() as state:
            self.running(state)
            contract = self.contract(task_id, state)
            remaining = self.allowance(state)
            assignment = state["assignments"].get(task_id, {})
            require(assignment.get("status") not in ("reserved", "pending_reconcile", "running", "held_unfinished"), "Task already reserved/active or unfinished outcome needs operator reconciliation")
            active = self.active(state)
            if assignment.get("status") == "idle":
                self.observed_status(state, assignment.get("thread_id"))
                active.pop(task_id, None)
            require(len(active) < self.policy["max_active_workers"], "An active or unreconciled worker already occupies the lab slot")
            starts_used = assignment.get("starts", 0)
            require(starts_used < contract["budget"]["max_starts"], "Task start/continuation bound exhausted")
            require(isinstance(request, dict) and set(request) == {"tool", "arguments"}, "Dispatch request requires exact tool and arguments")
            tool = leaf(request["tool"])
            args = request["arguments"]
            require(tool in ("create_thread", "send_message_to_thread") and isinstance(args, dict), "Only durable worker dispatch is permitted")
            require(args.get("model") == self.policy["worker_model"] and args.get("thinking") == self.policy["worker_reasoning"], "Dispatch must explicitly request Sol/max")
            brief = self.reference(contract["brief"]).read_text()
            require(args.get("prompt") == brief, "Dispatch prompt must match frozen brief bytes exactly")
            owner = assignment.get("thread_id") or contract.get("owner_thread_id")
            if tool == "create_thread":
                require(owner is None, "Use the registered durable worker rather than creating a duplicate")
                require(args.get("target") == {"type": "project", "projectId": self.registry["project_id"], "environment": {"type": "local"}}, "Worker must launch in this local project")
                require(set(args).issubset({"prompt", "model", "thinking", "target", "title"}), "Unclassified dispatch argument")
            else:
                require(uuid_ok(owner) and args.get("threadId") == owner, "Dispatch target does not match actual assigned worker")
                require(set(args).issubset({"prompt", "model", "thinking", "threadId", "hostId"}) and args.get("hostId", "local") == "local", "Unclassified dispatch argument")
            budget = self.effective_budget(state)
            cycle_id = contract["budget"]["cycle_id"]
            cycle_usage = state.setdefault("cycle_usage", {}).setdefault(cycle_id, {})
            recorded_cycle = next((cycle for cycle in [self.registry.get("current_pi_cycle", {}), *self.registry.get("completed_pi_cycles", [])] if cycle.get("id") == cycle_id), {})
            reviews = max(cycle_usage.get("review_starts", 0), recorded_cycle.get("independent_reviews_reserved", 0))
            revisions = max(cycle_usage.get("revision_starts", 0), recorded_cycle.get("revisions_used", 0))
            if contract["role"] == "reviewer":
                require(reviews < self.registry["budget"].get("max_independent_reviews_per_cycle", 1), "Independent-review allocation for this cycle is exhausted")
            is_revision = bool(contract.get("revision_of") or contract.get("previous_task"))
            require(not is_revision or revisions < self.registry["budget"].get("max_revisions_per_cycle", 1), "Revision allocation for this cycle is exhausted")
            known_cycles = set(budget["cycle_ids"])
            current_cycle = self.registry.get("current_pi_cycle", {})
            if current_cycle.get("id") == cycle_id:
                known_cycles.add(cycle_id)
            new_cycle = cycle_id not in known_cycles
            require(budget["start_limit"] is None or budget["starts"] < budget["start_limit"], "Daily worker-start ceiling exhausted")
            require(not new_cycle or budget["cycle_limit"] is None or budget["cycles"] < budget["cycle_limit"], "Daily PI-cycle ceiling exhausted")
            ticket = str(uuid.uuid4())
            state["permits"][ticket] = {"task_id": task_id, "request": request, "contract_sha256": digest(self.task_path(task_id).read_bytes()), "created_at": stamp(self.now), "status": "reserved"}
            state["assignments"][task_id] = {"thread_id": owner, "role": contract["role"], "status": "reserved", "starts": starts_used + 1, "permit_ticket": ticket}
            known_cycles.add(cycle_id)
            state["days"][self.today] = {"starts": budget["starts"] + 1, "cycles": budget["cycles"] + int(new_cycle), "cycle_ids": sorted(known_cycles)}
            cycle_usage["review_starts"] = reviews + int(contract["role"] == "reviewer")
            cycle_usage["revision_starts"] = revisions + int(is_revision)
            return {"ticket": ticket, "task_id": task_id, "dispatch": request, "remaining_percent": remaining, "note": "One use; unknown outcomes require reconciliation, never retry automatically"}

    def consume_permit(self, state, tool, arguments):
        self.running(state)
        self.allowance(state)
        matches = [(ticket, permit) for ticket, permit in state["permits"].items() if permit.get("status") == "reserved" and leaf(permit["request"]["tool"]) == leaf(tool) and permit["request"]["arguments"] == arguments]
        require(len(matches) == 1, "No unique one-use permit matches exact dispatch arguments")
        ticket, permit = matches[0]
        assignment = state["assignments"].get(permit["task_id"], {})
        require(assignment.get("status") == "reserved" and assignment.get("permit_ticket") == ticket, "Dispatch permit has been superseded or assignment changed")
        age = (self.now - parsed_time(permit["created_at"])).total_seconds()
        require(0 <= age <= self.policy["permit_max_age_seconds"], "Dispatch permit expired; reconcile rather than retry")
        self.contract(permit["task_id"], state)
        require(digest(self.task_path(permit["task_id"]).read_bytes()) == permit["contract_sha256"], "Task contract changed after reservation")
        permit.update(status="consumed_pending_reconcile", consumed_at=stamp(self.now))
        state["assignments"][permit["task_id"]]["status"] = "pending_reconcile"
        return ticket

    def command(self, command, arguments):
        require(isinstance(command, str) and "\n" not in command and "\r" not in command, "Controller command must be one simple invocation")
        try:
            tokens = shlex.split(command)
        except ValueError:
            raise Denied("Malformed controller command") from None
        require(command.strip() == shlex.join(tokens), "Use a canonical, safely quoted controller invocation; shell composition is forbidden")
        require(len(tokens) >= 3 and tokens[:2] == ["python3", str(self.root / "lab/control.py")], "PI shell access is restricted to the lab controller")
        require(tokens[2] in ("status", "read", "check", "reserve", "record"), "Unsupported controller operation")
        require(not arguments.get("shell") and arguments.get("sandbox_permissions", "use_default") == "use_default", "Controller cannot change shell or permissions")
        require(arguments.get("workdir", str(self.root)) == str(self.root), "Controller command must run at repository root")
        parse_cli(tokens[2:])
        return tokens

    def literal_wrapper(self, raw):
        if isinstance(raw, dict):
            values = [raw[key] for key in ("code", "input", "source", "command") if key in raw]
            require(len(values) == 1, "Wrapper requires one literal source field")
            raw = values[0]
        require(isinstance(raw, str), "Wrapper source is unavailable")
        match = re.fullmatch(r"text\(await tools\.([A-Za-z_][A-Za-z0-9_]*)\((\{[\s\S]*\})\)\);", raw.strip())
        require(match is not None, "PI wrapper must be exactly text(await tools.NAME(STRICT_JSON_OBJECT));")
        def bad_constant(value):
            raise Denied("Wrapper arguments must be strict JSON")
        def unique_pairs(pairs):
            result = {}
            for key, value in pairs:
                require(key not in result, "Duplicate wrapper JSON key")
                result[key] = value
            return result
        try:
            arguments = json.loads(match[2], parse_constant=bad_constant, object_pairs_hook=unique_pairs)
        except (ValueError, TypeError):
            raise Denied("Wrapper arguments must be strict JSON") from None
        require(isinstance(arguments, dict), "Wrapper tool arguments must be one JSON object")
        return match[1], arguments

    def observed_status(self, state, thread_id):
        require(uuid_ok(thread_id), "Actual assigned thread identity is unavailable")
        observation = state.get("app_status", {}).get(thread_id, {})
        require(observation.get("thread_id") == thread_id and observation.get("source") in ("read_thread", "wait_threads"), "No captured status for this exact assigned chat")
        age = (self.now - parsed_time(observation.get("observed_at"))).total_seconds()
        require(0 <= age <= self.policy["status_max_age_seconds"], "Assigned-chat status is stale")
        require(observation.get("thread_status") == "idle", "Assigned chat is active or status uncertain")
        return observation

    def hook(self, event):
        require(isinstance(event, dict), "Malformed hook event")
        session = event.get("session_id")
        require(uuid_ok(session), "Hook event is missing an actual session identity")
        if session in self.policy["operator_session_ids"]:
            return "Operator repair session; independent of registry and runtime state"
        name = leaf(event.get("tool_name", ""))
        raw_arguments = event.get("tool_input", {})
        is_wrapper = str(event.get("tool_name")) in ("functions.exec", "exec")
        arguments = raw_arguments
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"patch": arguments} if name == "apply_patch" else {}
        require(isinstance(arguments, dict), "Malformed tool input")
        manual = self.registry.get("governance", {}).get("mode") == "simple_manual"
        if manual or self.registry_error:
            report = (name, arguments)
            if is_wrapper:
                try:
                    nested = self.literal_wrapper(raw_arguments)
                except Denied:
                    nested = None
                if nested and self.ordinary_read(leaf(nested[0]), nested[1]):
                    return "Ordinary project context/status read; no task registration required"
                report = nested
            elif self.ordinary_read(name, arguments):
                return "Ordinary project context/status read; no task registration required"
            if report and leaf(report[0]) == "send_message_to_thread" and session == self.policy["pi_session_id"] and report[1].get("threadId") in self.policy["operator_session_ids"]:
                # Handoff/stop reports must still reach the existing operator
                # at the reserve or while execution is paused.
                message = report[1]
                require(set(message).issubset({"threadId", "hostId", "prompt", "model", "thinking"}), "PI operator report has unclassified settings")
                require(message.get("hostId", "local") == "local", "PI operator reports stay local")
                overrides = {"model", "thinking"}.intersection(message)
                require(not overrides or message.get("model") == self.policy["worker_model"] and message.get("thinking") == self.policy["worker_reasoning"], "Operator report must preserve settings or explicitly use Sol/max")
                prompt = message.get("prompt")
                require(isinstance(prompt, str) and 0 < len(prompt.strip()) <= 8000 and len(prompt.split()) <= 400, "PI operator report must be nonempty and at most400words/8000characters")
                return "Canonical PI coordination report to existing operator; no scientific dispatch or work reservation"
            if report and leaf(report[0]) in ("create_goal", "update_goal"):
                require(session == self.policy["pi_session_id"], "Only the canonical PI coordinates the lab's native goal")
                return "Canonical PI native goal coordination; human authorization and existing scientific controls still apply"
            require(not self.registry_error, str(self.registry_error) + "; scientific execution and record changes paused; existing operator can repair")
            if report and leaf(report[0]) == "send_message_to_thread" and session != self.policy["pi_session_id"] and session not in self.policy["operator_session_ids"]:
                # Returning saved evidence is coordination, not dispatching a
                # worker. Keep reporting available after collection or pause.
                require(any(task.get("thread_id") == session and role_name(task.get("role")) in ("investigator", "reviewer")
                            for task in self.registry.get("tasks", [])), "Only registered scientific workers may report to PI")
                message = report[1]
                require(set(message).issubset({"threadId", "hostId", "prompt"}), "Worker reports cannot override PI model or dispatch settings")
                require(message.get("threadId") == self.policy["pi_session_id"] and message.get("hostId", "local") == "local", "Worker reports must target the canonical local PI")
                prompt = message.get("prompt")
                require(isinstance(prompt, str) and 0 < len(prompt.strip()) <= 8000 and len(prompt.split()) <= 400, "Worker report must be nonempty and at most400words/8000characters")
                return "Registered worker report to canonical PI; platform human authorization still applies"
        with self.locked() as state:
            role, contract = self.identity(state, session)
            if is_wrapper:
                self.literal_wrapper(raw_arguments)
                return "One literal tool wrapper; platform must hook its nested tool call"
            if role == "pi":
                if manual and name == "apply_patch":
                    patch = arguments.get("patch", arguments.get("input", arguments.get("command", "")))
                    paths = re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$", patch, flags=re.M)
                    require(paths, "Unrecognized coordination patch")
                    shared = {"STATE.md", "PORTFOLIO.md", "LEARNINGS.md", "RESEARCH_AGENDA_2026-10-29.md", "lab/registry.json"}
                    for pair in paths:
                        path = self.path(next(part for part in pair if part)).relative_to(self.root).as_posix()
                        brief = re.fullmatch(r"lab/(tasks|reviews)/[a-z0-9-]+/BRIEF\.md", path)
                        decision = re.fullmatch(r"lab/PI_DECISION_[A-Za-z0-9_-]+\.md", path)
                        require(path in shared or brief or decision, "PI may edit coordination records and briefs, not scientific code or controls")
                    return "PI coordination records only; scientific work stays delegated"
                if name in self.policy["pi_read_tools"]:
                    known = self.known_threads(state)
                    if name == "read_thread":
                        require(arguments.get("threadId") in known, "PI may inspect only lab and setup chats")
                    if name == "wait_threads":
                        require(isinstance(arguments.get("targets"), list) and 1 <= len(arguments["targets"]) <= 8 and all(target.get("threadId") in known for target in arguments["targets"]), "PI may wait only for registered lab chats")
                    return "Bounded coordination/status read"
                if name in ("Bash", "bash", "exec_command"):
                    tokens = self.command(arguments.get("cmd", arguments.get("command")), arguments)
                    if manual:
                        require(tokens[2] in ("status", "read"), "Use ordinary coordination patches; scientific execution remains delegated")
                        return "Read-only PI controller access"
                    if tokens[2] in ("reserve", "record"):
                        self.authorize(state, session, tokens)
                    return "Validated controller invocation"
                if name in ("create_thread", "send_message_to_thread"):
                    if manual:
                        self.running(state)
                        require(arguments.get("model") == self.policy["worker_model"] and arguments.get("thinking") == self.policy["worker_reasoning"], "Workers must explicitly use Sol/max")
                        observation = self.registry.get("manual_usage_check", {})
                        require(observation.get("source") == "get_usage_limits", "PI must check usage manually before dispatch")
                        age = (self.now - parsed_time(observation.get("observed_at_utc"))).total_seconds()
                        require(0 <= age <= self.policy["allowance_max_age_seconds"], "Manual usage check is stale")
                        require(observation.get("remaining_percent", 0) > self.effective_budget(state)["floor"], "Manual usage check reached the reserve floor")
                        if name == "create_thread":
                            target = arguments.get("target", {})
                            require(isinstance(target, dict) and target.get("type") in ("project", "projectless"), "Use a valid project or projectless worker target")
                            require(target["type"] != "project" or isinstance(target.get("projectId"), str) and bool(target["projectId"]) and target.get("environment", {}).get("type") in ("local", "worktree"), "Invalid project worker target")
                        else:
                            require(uuid_ok(arguments.get("threadId")) and arguments.get("threadId") != self.policy["pi_session_id"], "Worker target must be a distinct actual chat identity")
                        return "Delegated Sol/max work after manual usage check; registry budgets and scientific access rules remain"
                    return "Consumed dispatch permit " + self.consume_permit(state, event["tool_name"], arguments)
                raise Denied("PI performs coordination through the controller; arbitrary scripts, search, edits, native agents and unclassified mutations are blocked")
            self.running(state)
            if name in ("spawn_agent", "followup_task", "Agent", "create_thread", "send_message_to_thread"):
                raise Denied("Workers cannot dispatch other scientific workers")
            if name in ("Bash", "bash", "exec_command"):
                command = arguments.get("cmd", arguments.get("command", ""))
                if "lab/control.py" in command:
                    tokens = self.command(command, arguments)
                    require(tokens[2] in ("status", "read", "check", "record"), "Workers cannot reserve")
                    if tokens[2] == "record":
                        require(len(tokens) > 3 and tokens[3] == "review" and role == "reviewer", "Only reviewers record independent review evidence")
                        self.authorize(state, session, tokens)
                    return "Scoped worker controller invocation"
                require(isinstance(command, str) and not re.search(r"[;|&<>`\n\r]", command) and "$(" not in command, "Worker shell composition and inline code are blocked")
                tokens = shlex.split(command)
                require(not any(token in ("-c", "-e", "--eval", "--command") for token in tokens), "Worker interpreter inline code is blocked")
                require(not any(part in command for part in self.policy["protected_paths"]), "Worker shell cannot target process-control paths")
                return "Scoped worker shell; this hook is not OS isolation"
            if name == "apply_patch":
                patch = arguments.get("patch", arguments.get("input", arguments.get("command", "")))
                paths = re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$", patch, flags=re.M)
                require(paths, "Unrecognized patch shape")
                for pair in paths:
                    path = self.path(next(part for part in pair if part))
                    require(not self.protected(str(path)), "Worker cannot edit process controls")
                    require(any(path.is_relative_to(self.path(prefix)) for prefix in contract["allowed_paths"]), "Worker patch escapes owned task paths")
                return "Patch confined to owned task paths"
            if manual:
                return "Worker tool subject to platform permissions and human authorization"
            require(name in self.policy["pi_read_tools"] or "search" in name.lower() or name in ("open", "find", "click") or event.get("tool_name") == "mcp__codex_apps__search_service_web_run", "Unclassified worker tool is blocked")
            return "Scoped worker evidence tool; separate data restrictions still apply"

    def authorize(self, state, session, tokens):
        state["authorizations"] = [a for a in state["authorizations"] if (self.now - parsed_time(a["created_at"])).total_seconds() <= self.policy["command_max_age_seconds"]]
        state["authorizations"].append({"actor": session, "argv_sha256": digest(tokens[2:]), "created_at": stamp(self.now)})

    def actor_for(self, argv):
        with self.locked() as state:
            matches = [a for a in state["authorizations"] if a["argv_sha256"] == digest(argv) and 0 <= (self.now - parsed_time(a["created_at"])).total_seconds() <= self.policy["command_max_age_seconds"]]
            require(matches, "Mutation requires a fresh exact-command authorization from the hook")
            authorization = matches[0]
            state["authorizations"].remove(authorization)
            return authorization["actor"]

    def record(self, kind, value, actor):
        require(isinstance(value, dict), "Record must be a JSON object")
        with self.locked() as state:
            role, own_contract = self.identity(state, actor)
            if kind == "proposal":
                require(role == "pi", "Only PI records bounded proposals")
                require(value.get("stage") in ("feasibility", "development"), "PI proposals cannot self-certify validation")
                require(not any(key in value for key in ("validation_gate", "review", "verdict", "protected_data_release")), "Proposal cannot self-certify access or independent evidence")
                task_id = value.get("task_id")
                contract_path = self.task_path(task_id)
                require(not contract_path.exists(), "Existing contracts and frozen briefs are immutable through proposals")
                require(value.get("role") in ("investigator", "reviewer"), "Unknown task role")
                prefix = ("lab/reviews/" if value["role"] == "reviewer" else "lab/tasks/") + task_id
                brief = value.get("brief_text")
                require(isinstance(brief, str) and 1 <= len(brief.encode()) <= 30000, "Missing or excessive task brief")
                contract = {key: value[key] for key in ("task_id", "role", "question_id", "stage", "expires_at", "budget", "controls", "artifacts", "evidence_scope", "data_access", "review_of", "revision_of", "previous_task") if key in value}
                contract.update(schema_version=1, status="approved", owner_thread_id=value.get("owner_thread_id"), allowed_paths=[prefix], brief={"path": prefix + "/BRIEF.md", "sha256": digest(brief.encode())})
                require(contract.get("question_id") == self.registry["question"]["id"], "Proposal changes approved question")
                require(all(key in contract for key in ("expires_at", "budget", "controls", "artifacts", "evidence_scope", "data_access")), "Incomplete proposal")
                brief_path = self.path(contract["brief"]["path"])
                require(not brief_path.exists(), "Cannot overwrite an existing task brief")
                brief_path.parent.mkdir(parents=True, exist_ok=True)
                brief_path.write_text(brief)
                atomic_json(contract_path, contract)
                try:
                    self.contract(task_id, state)
                except Exception:
                    contract_path.unlink()
                    brief_path.unlink()
                    raise
                return {"task_id": task_id, "contract": str(contract_path.relative_to(self.root)), "brief_sha256": contract["brief"]["sha256"]}
            if kind == "review":
                require(role == "reviewer", "Independent evidence must originate in an actual reviewer session")
                task_id = value.get("task_id")
                target = self.load(self.task_path(task_id))
                implementation_owner = state["assignments"].get(task_id, {}).get("thread_id") or target.get("owner_thread_id")
                require(actor != implementation_owner and actor != target.get("implementation_owner_thread_id"), "Owner cannot self-review")
                require(own_contract.get("review_of") == task_id, "Review is outside assigned review scope")
                require(value.get("verdict") in ("pass", "fail", "inconclusive"), "Missing independent verdict")
                for key in ("review", "exposure", "freeze"):
                    self.reference(value.get(key))
                require(isinstance(value.get("controls"), list), "Missing reviewed controls")
                for item in value["controls"]:
                    self.reference(item)
                require(isinstance(value.get("artifacts"), list) and bool(value["artifacts"]), "Review must pin decisive scientific artifacts")
                for artifact in value["artifacts"]:
                    self.reference(artifact)
            else:
                require(role == "pi" and kind in ("decision", "reconcile", "promote"), "Unsupported record authority")
                if kind == "promote":
                    self.running(state)
                    task_id = value.get("task_id")
                    contract = self.contract(task_id, state)
                    require(value.get("stage") == "validation", "Promotion only opens the independently checked validation process")
                    candidate = dict(contract, stage="validation", validation_gate={"status": "pass", "review_record_id": value.get("review_record_id")})
                    owner = state["assignments"].get(task_id, {}).get("thread_id") or contract.get("owner_thread_id")
                    self.validation(candidate, state, owner)
                    atomic_json(self.task_path(task_id), candidate)
                if kind == "reconcile":
                    require(value.get("task_id") in state["assignments"], "No known assignment to reconcile")
                    require(value.get("status") in ("idle", "completed", "blocked", "unknown"), "Unrecognized reconciliation status")
                    require(isinstance(value.get("note"), str) and value["note"], "Reconciliation requires a note")
                    assignment = state["assignments"][value["task_id"]]
                    observation = self.observed_status(state, assignment.get("thread_id"))
                    require(observation.get("turn_status") in ("completed", "interrupted", "failed", "needs_attention"), "No captured terminal or attention turn; ownership stays held")
                    if value["status"] == "completed":
                        require(assignment.get("status") == "running", "Only a dispatched running assignment can complete")
                        require(observation["turn_status"] == "completed", "Unfinished or interrupted task cannot be marked complete")
                        contract = self.contract(value["task_id"], state)
                        artifacts = value.get("artifacts", [])
                        names = {item.get("name") for item in artifacts}
                        require(set(contract["artifacts"]).union({"RESULT.md", "STATE.md"}).issubset(names), "Completion requires RESULT, STATE and every decisive contract artifact")
                        for artifact in artifacts:
                            path = self.reference(artifact)
                            require(any(path == self.path(prefix) / artifact.get("name", "") for prefix in contract["allowed_paths"]), "Completion artifact is outside the assigned task")
                        assignment["status"] = "completed"
                    else:
                        assignment["status"] = "held_unfinished"
                    for ticket, permit in state["permits"].items():
                        if permit.get("task_id") == value["task_id"] and permit.get("status") in ("reserved", "consumed_pending_reconcile"):
                            permit["status"] = "invalidated_by_reconciliation"
                    assignment.pop("permit_ticket", None)
            record = dict(value, id=str(uuid.uuid4()), kind=kind, actor_session_id=actor, recorded_at=stamp(self.now))
            state["records"].append(record)
            return record

    def post_hook(self, event):
        if self.registry_error:
            return self.registry_error + "; no receipt recorded; existing operator can repair"
        if self.registry.get("governance", {}).get("mode") == "simple_manual":
            return "Manual usage/process checks selected by the human; no automatic receipt required"
        name = leaf(event.get("tool_name", ""))
        response = event.get("tool_response", event.get("tool_output"))
        def unpack(value):
            yield value
            if isinstance(value, dict):
                for child in value.values():
                    yield from unpack(child)
            elif isinstance(value, list):
                for child in value:
                    yield from unpack(child)
            elif isinstance(value, str):
                try:
                    child = json.loads(value)
                    if isinstance(child, (dict, list)):
                        yield from unpack(child)
                except (ValueError, TypeError):
                    pass
        objects = [obj for obj in unpack(response) if isinstance(obj, dict)]
        with self.locked() as state:
            if name in ("read_thread", "wait_threads") and event.get("session_id") in (self.policy["pi_session_id"], *self.policy["operator_session_ids"]):
                arguments = event.get("tool_input", {})
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                requested = {arguments.get("threadId")} if name == "read_thread" else {target.get("threadId") for target in arguments.get("targets", [])}
                errors = any(obj.get("isError") is True or bool(obj.get("error")) for obj in objects if "thread" not in obj and "id" not in obj)
                if not errors:
                    for obj in objects:
                        thread = obj.get("thread", {})
                        if not isinstance(thread, dict) or thread.get("id") not in requested or not uuid_ok(thread.get("id")):
                            continue
                        thread_status = thread.get("status", {})
                        thread_status = thread_status.get("type") if isinstance(thread_status, dict) else thread_status
                        latest = obj.get("latestTurn")
                        if latest is None and obj.get("page", {}).get("order") == "newest_first" and isinstance(obj.get("turns"), list) and obj["turns"]:
                            latest = obj["turns"][0]
                        if not isinstance(latest, dict) or not isinstance(latest.get("status"), str):
                            continue
                        state.setdefault("app_status", {})[thread["id"]] = {"thread_id": thread["id"], "source": name, "thread_status": thread_status, "turn_status": latest["status"], "turn_id": latest.get("id"), "observed_at": stamp(self.now), "response_sha256": digest(response)}
            if name == "get_usage_limits" and event.get("session_id") in (self.policy["pi_session_id"], *self.policy["operator_session_ids"]):
                values = [max(0, min(100, 100 - obj["usedPercent"])) for obj in objects if isinstance(obj.get("usedPercent"), (int, float))]
                usage_blocked = any(obj.get("ordinaryUsageAllowed") is False or obj.get("rateLimitReached") is True or obj.get("spendControlReached") is True or obj.get("isError") is True or bool(obj.get("error")) for obj in objects)
                if values and not usage_blocked:
                    state["allowance"] = {"source": "get_usage_limits", "response_sha256": digest(response), "observed_at": stamp(self.now), "remaining_percent": min(values)}
                else:
                    state["allowance"] = None
            if name in ("create_thread", "send_message_to_thread") and event.get("session_id") == self.policy["pi_session_id"]:
                arguments = event.get("tool_input", {})
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                permits = [p for p in state["permits"].values() if p.get("status") == "consumed_pending_reconcile" and leaf(p["request"]["tool"]) == name and p["request"]["arguments"] == arguments]
                require(len(permits) == 1, "Tool result has no unique consumed permit")
                permit = permits[0]
                assignment = state["assignments"].get(permit["task_id"], {})
                matching_ticket = next(ticket for ticket, item in state["permits"].items() if item is permit)
                require(assignment.get("status") == "pending_reconcile" and assignment.get("permit_ticket") == matching_ticket, "Dispatch result belongs to a superseded assignment")
                require(not any(obj.get("isError") is True or obj.get("success") is False or obj.get("accepted") is False or obj.get("ok") is False or bool(obj.get("error")) or str(obj.get("status", "")).lower() in ("error", "failed", "rejected", "denied", "cancelled", "queued", "pending") for obj in objects), "Dispatch tool failed or has not completed; preserve consumed permit")
                identities = {obj["threadId"] for obj in objects if uuid_ok(obj.get("threadId"))}
                require(len(identities) == 1 and self.policy["pi_session_id"] not in identities, "Actual durable identity unavailable; consumed permit needs reconciliation")
                owner = identities.pop()
                require(name != "send_message_to_thread" or owner == arguments.get("threadId"), "Returned dispatch identity differs from assigned target")
                require(owner not in self.policy["operator_session_ids"], "Operator cannot become scientific owner")
                assignment.update(thread_id=owner, status="running", identity_response_sha256=digest(response))
                permit["status"] = "dispatched"
                permit["actual_thread_id"] = owner
        return "Captured recognized actual tool evidence"

    def status(self):
        with self.locked() as state:
            return {"governance": state.get("governance"), "registry_governance": self.registry.get("governance"), "budget": self.effective_budget(state), "allowance": state.get("allowance"), "active": self.active(state), "limitations": self.policy["limitations"]}


def parse_cli(argv):
    parser = QuietParser(description=__doc__, add_help=False)
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("status", add_help=False)
    read = sub.add_parser("read", add_help=False)
    read.add_argument("path")
    check = sub.add_parser("check", add_help=False)
    check.add_argument("task_id")
    reserve = sub.add_parser("reserve", add_help=False)
    reserve.add_argument("task_id")
    reserve.add_argument("--json", required=True)
    record = sub.add_parser("record", add_help=False)
    record.add_argument("kind", choices=("proposal", "decision", "review", "reconcile", "promote"))
    record.add_argument("--json", required=True)
    try:
        return parser.parse_args(argv)
    except SystemExit:
        raise Denied("Invalid controller arguments") from None


def hook_result(decision, reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision, "permissionDecisionReason": reason}}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    hook = argv == ["--hook"]
    post = argv == ["--post-hook"]
    try:
        gate = Gate(allow_invalid_registry=hook or post)
        if hook or post:
            event = json.load(sys.stdin)
            if post:
                reason = gate.post_hook(event)
                print(json.dumps({"systemMessage": reason}))
            else:
                print(json.dumps(hook_result("allow", gate.hook(event))))
            return 0
        arguments = parse_cli(argv)
        if arguments.operation == "status":
            result = gate.status()
        elif arguments.operation == "read":
            print(gate.read(arguments.path), end="")
            return 0
        elif arguments.operation == "check":
            with gate.locked() as state:
                contract = gate.contract(arguments.task_id, state)
                result = {"task_id": contract["task_id"], "stage": contract["stage"], "process_check": "pass", "scientific_truth_verified": False}
        else:
            actor = gate.actor_for(argv)
            value = json.loads(arguments.json)
            result = gate.reserve(arguments.task_id, value, actor) if arguments.operation == "reserve" else gate.record(arguments.kind, value, actor)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as error:
        reason = "Lab gate denied: " + str(error)
        if hook:
            print(json.dumps(hook_result("deny", reason)))
            return 0
        if post:
            print(json.dumps({"systemMessage": reason + "; keep consumed work pending reconciliation"}))
            return 0
        print(json.dumps({"denied": reason}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
