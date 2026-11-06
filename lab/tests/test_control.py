"""Process/lifecycle tests use temporary repositories; never touch lab science."""
import contextlib
import copy
import base64
import datetime as dt
import importlib.util
import io
import json
import multiprocessing
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("lab_control", Path(__file__).resolve().parents[1] / "control.py")
control = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(control)
PI = "01a183c5-84a1-71f1-b38e-323dbbd2e7bd"
OPERATOR = "01a18836-d7ba-7243-a87b-50fdbe613db3"
OWNER = "11111111-1111-4111-8111-111111111111"
REVIEWER = "22222222-2222-4222-8222-222222222222"
UNKNOWN = "33333333-3333-4333-8333-333333333333"
INVESTMENT_CHAT = "01a18a80-83c3-7d41-95e6-1f319d85dccc"
NOW = dt.datetime(2026, 10, 29, 20, 0, tzinfo=dt.timezone.utc)


def reserve_in_process(root, request, queue):
    try:
        control.Gate(root, NOW).reserve("pilot", request, PI)
        queue.put("reserved")
    except control.Denied:
        queue.put("denied")


class ControlFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        (self.root / "lab/contracts").mkdir(parents=True)
        policy = json.loads((Path(__file__).resolve().parents[1] / "policy.json").read_text())
        # Fixture identities stay fixed when the live lab rotates its PI.
        policy["pi_session_id"] = PI
        self.write("lab/policy.json", policy)
        self.registry = {
            "timezone": "America/New_York", "project_id": "local-project", "governance": {"status": "running"},
            "question": {"id": "learning-across-curricula"}, "tasks": [],
            "budget": {"max_autonomous_max_agent_starts_per_day": 2, "max_substantive_pi_cycles_per_day": 2,
                       "minimum_account_remaining_percent_for_new_work": 20,
                       "date_scoped_overrides": {"2026-10-29": {"minimum_account_remaining_percent_for_new_work": 10,
                          "daily_max_agent_start_ceiling": "usage_governed_today", "daily_substantive_pi_cycle_ceiling": "usage_governed_today", "expires_after_local_date": "2026-10-29"}}},
            "daily_usage": {"date": "2026-10-29", "max_agent_starts_reserved": 8, "substantive_pi_cycles_reserved": 7},
            "current_pi_cycle": {"id": "cycle-7"}}
        self.write("lab/registry.json", self.registry)
        self.state = {"schema_version": 1, "governance": {"status": "running", "hook_trust_verified": True, "canary_verified": True},
                      "days": {}, "permits": {}, "assignments": {}, "authorizations": [], "records": [],
                      "allowance": {"source": "get_usage_limits", "observed_at": control.stamp(NOW), "response_sha256": "a" * 64, "remaining_percent": 70}}
        self.save_state()
        self.contract = self.make_contract("pilot")
        self.gate = control.Gate(self.root, NOW)

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, path, value):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(value) if not isinstance(value, str) else value)

    def save_state(self):
        self.write("lab/control-state.json", self.state)

    def load_state(self):
        return json.loads((self.root / "lab/control-state.json").read_text())

    def make_contract(self, task, role="investigator", owner=None):
        prefix = "lab/reviews/" if role == "reviewer" else "lab/tasks/"
        brief = "Bounded source-only scientific feasibility; preserve all protected outcomes.\n"
        path = prefix + task + "/BRIEF.md"
        self.write(path, brief)
        contract = {"schema_version": 1, "task_id": task, "status": "approved", "role": role,
                    "question_id": "learning-across-curricula", "stage": "feasibility", "expires_at": control.stamp(NOW + dt.timedelta(days=2)),
                    "brief": {"path": path, "sha256": control.digest(brief.encode())}, "allowed_paths": [prefix + task],
                    "owner_thread_id": owner, "budget": {"max_starts": 1, "cycle_id": "cycle-7"},
                    "controls": ["known_answer", "null", "sensitivity"], "artifacts": ["RESULT.md", "EXPOSURE.md"],
                    "evidence_scope": "Synthetic and saved public task source only", "data_access": []}
        self.write("lab/contracts/" + task + ".json", contract)
        return contract

    def event(self, name, args=None, session=PI):
        return {"session_id": session, "tool_name": name, "tool_input": {} if args is None else args}

    def cmd(self, *args):
        return shlex.join(["python3", str(self.root / "lab/control.py"), *args])

    def request(self):
        return {"tool": "mcp__codex_app__create_thread", "arguments": {"model": "gpt-6.1-sol", "thinking": "max",
                "prompt": (self.root / self.contract["brief"]["path"]).read_text(),
                "target": {"type": "project", "projectId": "local-project", "environment": {"type": "local"}}}}

    def reserve(self):
        return self.gate.reserve("pilot", self.request(), PI)


class ControlTests(ControlFixture):
    def test_pi_arbitrary_code_search_patch_and_native_agents_denied(self):
        events = [self.event("Bash", {"command": "python3 -c 'print(1)'"}), self.event("exec_command", {"cmd": "cat STATE.md"}),
                  self.event("apply_patch", {"patch": "*** Begin Patch\n*** Add File: x\n+x\n*** End Patch"}),
                  self.event("mcp__search_service__search", {"q": "learning"}), self.event("web.run", {"search_query": []}),
                  self.event("collaboration.spawn_agent", {"task_name": "science"}), self.event("collaboration.followup_task", {"target": "science"}),
                  self.event("mcp__node_repl__js", {"code": "console.log(1)"}), self.event("mcp__codex_app__automation_update", {"status": "ACTIVE"})]
        for event in events:
            with self.subTest(tool=event["tool_name"]), self.assertRaises(control.Denied):
                self.gate.hook(event)

    def test_code_wrapper_does_not_bypass_nested_check(self):
        self.assertIn("wrapper", self.gate.hook(self.event("functions.exec", {"code": "text(await tools.mcp__codex_app__get_usage_limits({}));"})))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("functions.exec_command", {"cmd": "python3 arbitrary.py"}))

    def test_pi_wrapper_allows_only_literal_single_tool_calls(self):
        for code in ("text(1 + 2);", "const x=await tools.exec_command({});text(x);", "for(;;){}", "text(await tools.exec_command({cmd:'x'}));", "text(await tools.exec_command({}));text(1);", "// comment\ntext(await tools.exec_command({}));", "text(await tools.exec_command({\"x\":NaN}));"):
            with self.subTest(code=code), self.assertRaises(control.Denied):
                self.gate.hook(self.event("functions.exec", {"code": code}))
        for field in ("code", "input", "source", "command"):
            self.gate.hook(self.event("functions.exec", {field: "text(await tools.mcp__codex_app__get_usage_limits({}));"}))
        self.gate.hook(self.event("functions.exec", "text(await tools.mcp__codex_app__get_usage_limits({}));"))

    def test_paused_status_and_saved_evidence_reads_allowed(self):
        self.state["governance"]["status"] = "paused"
        self.save_state()
        self.write("STATE.md", "saved decision\n")
        self.assertIn("controller", self.gate.hook(self.event("Bash", {"command": self.cmd("status")})))
        self.assertEqual(self.gate.read("STATE.md"), "saved decision\n")
        self.assertIn("read", self.gate.hook(self.event("mcp__codex_app__get_usage_limits")))

    def test_chat_reads_are_limited_to_lab_and_setup(self):
        self.gate.hook(self.event("mcp__codex_app__read_thread", {"threadId": OPERATOR}))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("mcp__codex_app__read_thread", {"threadId": UNKNOWN}))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("mcp__codex_app__wait_threads", {"targets": [{"threadId": UNKNOWN}]}))

    def test_shell_composition_and_quoted_code_injection_denied(self):
        for command in [self.cmd("status") + "; echo bypass", self.cmd("status") + " > /tmp/x", self.cmd("status") + " && true",
                        "python3 " + str(self.root / "lab/control.py") + ' record decision --json "$(touch /tmp/x)"',
                        self.cmd("status") + "\ntrue", self.cmd("status", "-c", "print(1)")]:
            with self.subTest(command=command), self.assertRaises(control.Denied):
                self.gate.hook(self.event("Bash", {"command": command}))
        note = json.dumps({"note": "literal $(not a shell) and ; characters"})
        self.gate.hook(self.event("Bash", {"command": self.cmd("record", "decision", "--json", note)}))

    def test_pi_cannot_override_shell_permissions_or_root(self):
        for extra in ({"shell": "/tmp/evil"}, {"sandbox_permissions": "require_escalated"}, {"workdir": "/tmp"}):
            with self.subTest(extra=extra), self.assertRaises(control.Denied):
                self.gate.hook(self.event("Bash", dict(command=self.cmd("status"), **extra)))

    def test_missing_identity_and_unknown_roles_fail_closed(self):
        with self.assertRaises(control.Denied):
            self.gate.hook({"tool_name": "Bash", "tool_input": {"command": "true"}})
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("mcp__codex_app__get_usage_limits", session=UNKNOWN))
        self.contract["role"] = "super_pi"
        self.write("lab/contracts/pilot.json", self.contract)
        with self.assertRaises(control.Denied):
            self.reserve()

    def test_pi_evidence_read_rejects_payloads_and_traversal(self):
        self.write("lab/tasks/pilot/data/raw.json", "[1,2,3]")
        self.write("lab/tasks/pilot/results.npz", "payload")
        for path in ("lab/tasks/pilot/data/raw.json", "lab/tasks/pilot/results.npz", "../outside.md"):
            with self.subTest(path=path), self.assertRaises(control.Denied):
                self.gate.read(path)

    def test_governance_pause_independent_registry_check_and_trust(self):
        for target, key in (("state", "status"), ("registry", "status"), ("state", "hook_trust_verified"), ("state", "canary_verified")):
            with self.subTest(target=target, key=key):
                state = copy.deepcopy(self.state)
                registry = copy.deepcopy(self.registry)
                obj = state if target == "state" else registry
                obj["governance"][key] = "paused" if key == "status" else False
                self.write("lab/control-state.json", state)
                self.write("lab/registry.json", registry)
                with self.assertRaises(control.Denied):
                    control.Gate(self.root, NOW).reserve("pilot", self.request(), PI)

    def test_missing_stale_incomplete_or_changed_brief_contract_denies(self):
        with self.assertRaises(control.Denied):
            self.gate.reserve("missing", self.request(), PI)
        for change in ({"expires_at": control.stamp(NOW - dt.timedelta(seconds=1))}, {"controls": []}, {"artifacts": []},
                       {"evidence_scope": ""}, {"owner_thread_id": PI}, {"data_access": ["pan20"]}):
            self.write("lab/contracts/pilot.json", dict(self.contract, **change))
            with self.subTest(change=change), self.assertRaises(control.Denied):
                self.reserve()
        self.write("lab/contracts/pilot.json", self.contract)
        self.write(self.contract["brief"]["path"], "changed frozen brief")
        with self.assertRaises(control.Denied):
            self.reserve()

    def test_override_migration_preserves_eight_starts_seven_cycles(self):
        self.reserve()
        day = self.load_state()["days"]["2026-10-29"]
        self.assertEqual((day["starts"], day["cycles"]), (9, 7))
        self.assertIsNone(self.gate.effective_budget(self.load_state())["start_limit"])
        self.assertEqual(self.gate.effective_budget(self.load_state())["floor"], 10)

    def test_override_expires_next_local_day_and_caps_do_not_reset(self):
        tomorrow = NOW + dt.timedelta(days=1)
        gate = control.Gate(self.root, tomorrow)
        self.assertEqual(gate.effective_budget(self.state)["floor"], 20)
        self.state["days"]["2026-10-30"] = {"starts": 2, "cycles": 1}
        self.state["allowance"]["observed_at"] = control.stamp(tomorrow)
        self.save_state()
        with self.assertRaisesRegex(control.Denied, "ceiling"):
            gate.reserve("pilot", self.request(), PI)
        self.assertEqual(self.load_state()["days"]["2026-10-30"]["starts"], 2)

    def test_floor_and_stale_or_unproven_allowance_denied(self):
        for change in ({"remaining_percent": 10}, {"observed_at": control.stamp(NOW - dt.timedelta(seconds=301))},
                       {"source": "pi_self_report"}, {"response_sha256": ""}):
            self.state["allowance"].update(change)
            self.save_state()
            with self.subTest(change=change), self.assertRaises(control.Denied):
                self.reserve()
            self.state["allowance"] = {"source": "get_usage_limits", "observed_at": control.stamp(NOW), "response_sha256": "a" * 64, "remaining_percent": 70}

    def test_exact_dispatch_permit_is_one_use_and_unknown_never_retries(self):
        result = self.reserve()
        wrong = copy.deepcopy(result["dispatch"]["arguments"])
        wrong["thinking"] = "ultra"
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event(result["dispatch"]["tool"], wrong))
        self.gate.hook(self.event(result["dispatch"]["tool"], result["dispatch"]["arguments"]))
        state = self.load_state()
        self.assertEqual(state["permits"][result["ticket"]]["status"], "consumed_pending_reconcile")
        self.assertEqual(state["assignments"]["pilot"]["status"], "pending_reconcile")
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event(result["dispatch"]["tool"], result["dispatch"]["arguments"]))
        with self.assertRaises(control.Denied):
            self.reserve()
        self.assertEqual(self.load_state()["days"]["2026-10-29"]["starts"], 9)

    def test_dispatch_requires_explicit_runtime_and_exact_brief(self):
        for key, value in (("thinking", "ultra"), ("model", "other"), ("prompt", "summary of brief")):
            request = self.request()
            request["arguments"][key] = value
            with self.subTest(key=key), self.assertRaises(control.Denied):
                self.gate.reserve("pilot", request, PI)
        self.assertEqual(self.load_state()["days"], {})

    def test_stale_permit_or_changed_contract_denies_without_refunding(self):
        result = self.reserve()
        self.state = self.load_state()
        self.state["allowance"]["observed_at"] = control.stamp(NOW + dt.timedelta(seconds=301))
        self.save_state()
        with self.assertRaisesRegex(control.Denied, "permit expired"):
            control.Gate(self.root, NOW + dt.timedelta(seconds=301)).hook(self.event(result["dispatch"]["tool"], result["dispatch"]["arguments"]))
        self.contract["evidence_scope"] += "; changed after reservation"
        self.write("lab/contracts/pilot.json", self.contract)
        self.state["allowance"]["observed_at"] = control.stamp(NOW)
        self.save_state()
        with self.assertRaisesRegex(control.Denied, "changed after reservation"):
            self.gate.hook(self.event(result["dispatch"]["tool"], result["dispatch"]["arguments"]))
        self.assertEqual(self.load_state()["days"]["2026-10-29"]["starts"], 9)

    def test_cycle_review_allocation_survives_completed_review(self):
        self.contract = self.make_contract("pilot", "reviewer")
        self.registry["current_pi_cycle"]["independent_reviews_reserved"] = 1
        self.write("lab/registry.json", self.registry)
        with self.assertRaisesRegex(control.Denied, "review allocation"):
            control.Gate(self.root, NOW).reserve("pilot", self.request(), PI)

    def test_cycle_revision_allocation_is_not_lifted_by_daily_override(self):
        self.contract["revision_of"] = "previous-scientific-task"
        self.write("lab/contracts/pilot.json", self.contract)
        self.registry["current_pi_cycle"]["revisions_used"] = 1
        self.write("lab/registry.json", self.registry)
        with self.assertRaisesRegex(control.Denied, "Revision allocation"):
            control.Gate(self.root, NOW).reserve("pilot", self.request(), PI)

    def test_double_or_parallel_reservation_rejects_atomically(self):
        context = multiprocessing.get_context("fork")
        queue = context.Queue()
        processes = [context.Process(target=reserve_in_process, args=(str(self.root), self.request(), queue)) for _ in range(2)]
        for process in processes:
            process.start()
        for process in processes:
            process.join(5)
            self.assertEqual(process.exitcode, 0)
        self.assertEqual(sorted(queue.get(timeout=1) for _ in processes), ["denied", "reserved"])
        self.assertEqual(self.load_state()["days"]["2026-10-29"]["starts"], 9)

    def test_active_native_assignment_blocks_new_work(self):
        self.registry["tasks"].append({"id": "old-native", "status": "running", "thread_id": None})
        self.write("lab/registry.json", self.registry)
        with self.assertRaisesRegex(control.Denied, "unreconciled"):
            control.Gate(self.root, NOW).reserve("pilot", self.request(), PI)

    def test_dispatched_native_assignment_is_active_and_blocks_new_work(self):
        self.registry["tasks"].append({"id": "old-native", "status": "dispatched", "thread_id": OWNER})
        self.write("lab/registry.json", self.registry)
        gate = control.Gate(self.root, NOW)
        self.assertEqual(gate.status()["active"], {"old-native": OWNER})
        with self.assertRaisesRegex(control.Denied, "already occupies the lab slot"):
            gate.reserve("pilot", self.request(), PI)
        self.assertNotIn("pilot", self.load_state()["assignments"])

    def test_actual_post_result_binds_identity_not_client_identity(self):
        result = self.reserve()
        event = self.event(result["dispatch"]["tool"], result["dispatch"]["arguments"])
        self.gate.hook(event)
        with self.assertRaises(control.Denied):
            self.gate.post_hook(dict(event, tool_response={"clientThreadId": UNKNOWN}))
        self.assertEqual(self.load_state()["assignments"]["pilot"]["status"], "pending_reconcile")
        self.gate.post_hook(dict(event, tool_response={"content": [{"type": "text", "text": json.dumps({"threadId": OWNER})}]}))
        self.assertEqual(self.load_state()["assignments"]["pilot"]["thread_id"], OWNER)
        self.assertEqual(self.load_state()["assignments"]["pilot"]["status"], "running")

    def capture_status(self, turn="completed", thread="idle", owner=OWNER, source="read_thread"):
        if source == "read_thread":
            response = {"thread": {"id": owner, "status": {"type": thread}}, "turns": [{"id": "actual-turn", "status": turn}], "page": {"order": "newest_first"}}
            args = {"threadId": owner}
        else:
            response = {"polls": [{"thread": {"id": owner, "status": {"type": thread}}, "latestTurn": {"id": "actual-turn", "status": turn}}]}
            args = {"targets": [{"threadId": owner}]}
        self.gate.post_hook(dict(self.event("mcp__codex_app__" + source, args), tool_response=response))

    def test_reconcile_requires_actual_recent_exact_identity_status(self):
        self.state["assignments"]["pilot"] = {"thread_id": OWNER, "status": "running", "starts": 1}
        self.save_state()
        value = {"task_id": "pilot", "status": "blocked", "note": "Actual process needs attention", "evidence": {"path": self.contract["brief"]["path"], "sha256": self.contract["brief"]["sha256"]}}
        with self.assertRaises(control.Denied):
            self.gate.record("reconcile", value, PI)
        self.capture_status(owner=REVIEWER)
        with self.assertRaises(control.Denied):
            self.gate.record("reconcile", value, PI)
        self.capture_status(turn="inProgress")
        with self.assertRaises(control.Denied):
            self.gate.record("reconcile", value, PI)
        self.capture_status(turn="completed")
        with self.assertRaisesRegex(control.Denied, "stale"):
            control.Gate(self.root, NOW + dt.timedelta(seconds=301)).record("reconcile", value, PI)

    def test_interrupted_held_assignment_cannot_be_replaced_or_relaunched(self):
        self.state["assignments"]["pilot"] = {"thread_id": OWNER, "status": "running", "starts": 1}
        self.save_state()
        self.capture_status(turn="interrupted", source="wait_threads")
        self.gate.record("reconcile", {"task_id": "pilot", "status": "blocked", "note": "Interrupted unfinished work stays held"}, PI)
        self.assertIn("pilot", self.gate.active(self.load_state()))
        with self.assertRaises(control.Denied):
            self.reserve()
        self.make_contract("replacement")
        with self.assertRaises(control.Denied):
            self.gate.reserve("replacement", self.request(), PI)

    def test_reconciliation_invalidates_outstanding_bound_ticket(self):
        self.contract["owner_thread_id"] = OWNER
        self.write("lab/contracts/pilot.json", self.contract)
        request = {"tool": "mcp__codex_app__send_message_to_thread", "arguments": {"threadId": OWNER, "model": "gpt-6.1-sol", "thinking": "max", "prompt": (self.root / self.contract["brief"]["path"]).read_text()}}
        result = self.gate.reserve("pilot", request, PI)
        self.capture_status()
        self.gate.record("reconcile", {"task_id": "pilot", "status": "blocked", "note": "Cancel reserved dispatch and preserve unfinished owner"}, PI)
        self.assertEqual(self.load_state()["permits"][result["ticket"]]["status"], "invalidated_by_reconciliation")
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event(request["tool"], request["arguments"]))

    def test_superseded_assignment_ticket_cannot_dispatch(self):
        result = self.reserve()
        self.state = self.load_state()
        self.state["assignments"]["pilot"]["permit_ticket"] = "a different ticket"
        self.save_state()
        with self.assertRaisesRegex(control.Denied, "superseded"):
            self.gate.hook(self.event(result["dispatch"]["tool"], result["dispatch"]["arguments"]))

    def test_actual_completed_turn_plus_saved_artifacts_releases_slot(self):
        self.state["assignments"]["pilot"] = {"thread_id": OWNER, "status": "running", "starts": 1}
        self.save_state()
        self.capture_status(source="wait_threads")
        artifacts = []
        for name in set(self.contract["artifacts"]).union({"STATE.md"}):
            path = "lab/tasks/pilot/" + name
            self.write(path, "Completed saved scientific artifact " + name)
            artifacts.append({"name": name, "path": path, "sha256": control.digest((self.root / path).read_bytes())})
        self.gate.record("reconcile", {"task_id": "pilot", "status": "completed", "note": "Actual completed return reviewed against artifacts", "artifacts": artifacts}, PI)
        self.assertNotIn("pilot", self.gate.active(self.load_state()))

    def test_actual_allowance_capture_uses_most_depleted_window(self):
        self.gate.post_hook(dict(self.event("mcp__codex_app__get_usage_limits"), tool_response={"rateLimitsByLimitId": {"one": {"primary": {"usedPercent": 30}, "secondary": {"usedPercent": 87}}}}))
        self.assertEqual(self.load_state()["allowance"]["remaining_percent"], 13)
        self.gate.post_hook(dict(self.event("mcp__codex_app__get_usage_limits"), tool_response={"rateLimits": None}))
        self.assertIsNone(self.load_state()["allowance"])

    def test_usage_denials_override_apparently_available_percent(self):
        for blocked in ({"ordinaryUsageAllowed": False}, {"rateLimitReached": True}, {"spendControlReached": True}, {"isError": True}):
            self.gate.post_hook(dict(self.event("mcp__codex_app__get_usage_limits"), tool_response=dict(blocked, rateLimits={"primary": {"usedPercent": 2}})))
            self.assertIsNone(self.load_state()["allowance"])
            with self.assertRaises(control.Denied):
                self.reserve()

    def test_failed_or_missing_send_result_never_synthesizes_identity(self):
        self.contract["owner_thread_id"] = OWNER
        self.write("lab/contracts/pilot.json", self.contract)
        request = {"tool": "mcp__codex_app__send_message_to_thread", "arguments": {"threadId": OWNER, "model": "gpt-6.1-sol", "thinking": "max", "prompt": (self.root / self.contract["brief"]["path"]).read_text()}}
        self.gate.reserve("pilot", request, PI)
        event = self.event(request["tool"], request["arguments"])
        self.gate.hook(event)
        for response in ({"isError": True, "threadId": OWNER}, {"success": False, "threadId": OWNER}, {"error": "approval rejected", "threadId": OWNER}, {"status": "failed", "threadId": OWNER}, {"success": True}):
            with self.subTest(response=response), self.assertRaises(control.Denied):
                self.gate.post_hook(dict(event, tool_response=response))
            self.assertEqual(self.load_state()["assignments"]["pilot"]["status"], "pending_reconcile")
        self.gate.post_hook(dict(event, tool_response={"threadId": OWNER, "status": "accepted"}))
        self.assertEqual(self.load_state()["assignments"]["pilot"]["status"], "running")

    def test_guarded_proposal_and_command_authorization(self):
        value = {key: self.contract[key] for key in ("role", "question_id", "stage", "expires_at", "budget", "controls", "artifacts", "evidence_scope", "data_access")}
        value.update(task_id="next-pilot", brief_text="One bounded task; no protected data.\n")
        argv = ["record", "proposal", "--json", json.dumps(value)]
        with self.assertRaises(control.Denied):
            self.gate.actor_for(argv)
        self.gate.hook(self.event("Bash", {"command": self.cmd(*argv)}))
        actor = self.gate.actor_for(argv)
        result = self.gate.record("proposal", value, actor)
        self.assertTrue((self.root / result["contract"]).exists())
        with self.assertRaises(control.Denied):
            self.gate.actor_for(argv)
        value.update(task_id="cannot-validate", stage="validation")
        with self.assertRaises(control.Denied):
            self.gate.record("proposal", value, PI)

    def validation_evidence(self):
        owner_contract = dict(self.contract, owner_thread_id=OWNER, stage="development")
        self.write("lab/contracts/pilot.json", owner_contract)
        reviewer = self.make_contract("pilot-review", "reviewer", REVIEWER)
        reviewer["review_of"] = "pilot"
        self.write("lab/contracts/pilot-review.json", reviewer)
        self.state["assignments"]["pilot-review"] = {"thread_id": REVIEWER, "role": "reviewer", "status": "running", "starts": 1}
        self.save_state()
        def ref(name):
            path = "lab/reviews/pilot-review/" + name + ".md"
            self.write(path, "Actual saved " + name + " evidence\n")
            return {"path": path, "sha256": control.digest((self.root / path).read_bytes())}
        value = {"task_id": "pilot", "verdict": "pass", "review": ref("review"), "exposure": ref("exposure"), "freeze": ref("freeze"),
                 "controls": [dict(ref(name), name=name, status="pass") for name in ("known_answer", "null", "sensitivity")], "artifacts": []}
        for name in owner_contract["artifacts"]:
            path = "lab/tasks/pilot/" + name
            self.write(path, "Decisive saved " + name + "\n")
            value["artifacts"].append({"name": name, "path": path, "sha256": control.digest((self.root / path).read_bytes())})
        return value

    def test_validation_requires_reviewer_origin_and_actual_hashed_evidence(self):
        value = self.validation_evidence()
        with self.assertRaises(control.Denied):
            self.gate.record("review", value, PI)
        with self.assertRaises(control.Denied):
            self.gate.record("promote", {"task_id": "pilot", "stage": "validation", "review_record_id": "fabricated"}, PI)
        record = self.gate.record("review", value, REVIEWER)
        self.gate.record("promote", {"task_id": "pilot", "stage": "validation", "review_record_id": record["id"]}, PI)
        with self.gate.locked() as state:
            self.assertEqual(self.gate.contract("pilot", state)["stage"], "validation")
        self.write(value["controls"][0]["path"], "modified after independent review")
        with self.gate.locked() as state, self.assertRaisesRegex(control.Denied, "Stale evidence"):
            self.gate.contract("pilot", state)

    def test_changed_scientific_artifact_after_review_blocks_promotion(self):
        value = self.validation_evidence()
        record = self.gate.record("review", value, REVIEWER)
        self.write(value["artifacts"][0]["path"], "Changed decisive scientific result after review")
        with self.assertRaisesRegex(control.Denied, "Stale evidence"):
            self.gate.record("promote", {"task_id": "pilot", "stage": "validation", "review_record_id": record["id"]}, PI)

    def test_validation_missing_controls_failures_and_self_review_denied(self):
        value = self.validation_evidence()
        for change in ({"controls": value["controls"][:1]}, {"verdict": "fail"}, {"review": {"path": "missing.md", "sha256": "a" * 64}}):
            altered = dict(value, **change)
            try:
                record = self.gate.record("review", altered, REVIEWER)
            except control.Denied:
                continue
            with self.subTest(change=change), self.assertRaises(control.Denied):
                self.gate.record("promote", {"task_id": "pilot", "stage": "validation", "review_record_id": record["id"]}, PI)
        target = json.loads((self.root / "lab/contracts/pilot.json").read_text())
        target["owner_thread_id"] = REVIEWER
        self.write("lab/contracts/pilot.json", target)
        with self.assertRaisesRegex(control.Denied, "self-review"):
            self.gate.record("review", value, REVIEWER)

    def test_workers_patch_only_own_paths_and_cannot_change_controls(self):
        contract = dict(self.contract, owner_thread_id=OWNER)
        self.write("lab/contracts/pilot.json", contract)
        self.state["assignments"]["pilot"] = {"thread_id": OWNER, "status": "running", "role": "investigator", "starts": 1}
        self.save_state()
        for path in ("lab/policy.json", ".codex/hooks.json", "lab/tasks/other/RESULT.md"):
            with self.subTest(path=path), self.assertRaises(control.Denied):
                self.gate.hook(self.event("apply_patch", {"patch": "*** Begin Patch\n*** Add File: " + path + "\n+x\n*** End Patch"}, OWNER))
        self.gate.hook(self.event("apply_patch", {"command": "*** Begin Patch\n*** Add File: lab/tasks/pilot/RESULT.md\n+x\n*** End Patch"}, OWNER))
        self.gate.hook(self.event("mcp__codex_apps__search_service_web_run", {"search_query": [{"q": "primary source"}]}, OWNER))
        for command in ("python3 -c 'print(1)'", "cat x; echo y", "python3 <<EOF", "touch lab/policy.json"):
            with self.subTest(command=command), self.assertRaises(control.Denied):
                self.gate.hook(self.event("Bash", {"command": command}, OWNER))
        self.state["governance"]["status"] = "paused"
        self.save_state()
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("Bash", {"command": "python3 run.py"}, OWNER))

    def test_hook_malformed_input_and_internal_errors_emit_explicit_deny(self):
        for source, constructor in (("not json", mock.Mock(return_value=self.gate)), (json.dumps(self.event("Bash", {"command": "true"})), mock.Mock(side_effect=RuntimeError("unavailable")))):
            stdout = io.StringIO()
            with mock.patch.object(control, "Gate", constructor), mock.patch("sys.stdin", io.StringIO(source)), contextlib.redirect_stdout(stdout):
                self.assertEqual(control.main(["--hook"]), 0)
            result = json.loads(stdout.getvalue())
            self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertEqual(result["hookSpecificOutput"]["hookEventName"], "PreToolUse")


class SimpleManualReadTests(ControlFixture):
    """Run the targeted manual regressions without repeating legacy-mode tests."""
    def setUp(self):
        super().setUp()
        self.registry["governance"]["mode"] = "simple_manual"
        self.registry["manual_usage_check"] = {"source": "get_usage_limits", "observed_at_utc": control.stamp(NOW), "remaining_percent": 70}
        self.write("lab/registry.json", self.registry)
        self.write("LEARNINGS.md", "Saved project observations.\n")
        self.write("STATE.md", "Current completed decision.\n")
        self.write("notes/quoted file.txt", "An ordinary note.\n")
        self.write("data/README.md", "Source data documentation.\n")
        self.write("data/schema.py", "# source code, not a data payload\n")
        self.write("data/responses.json", "[1, 2, 3]")
        self.gate = control.Gate(self.root, NOW)

    def test_manual_unregistered_and_completed_chat_reads_before_state_lookup(self):
        self.registry["tasks"].append({"id": "completed", "thread_id": OWNER, "status": "completed", "role": "investigation_lead"})
        self.registry["governance"]["status"] = "paused"
        self.write("lab/registry.json", self.registry)
        self.gate = control.Gate(self.root, NOW)
        with mock.patch.object(self.gate, "locked", side_effect=AssertionError("ordinary reads must not lock runtime state")), mock.patch.object(self.gate, "identity", side_effect=AssertionError("ordinary reads must not need identity registration")):
            for session in (INVESTMENT_CHAT, OWNER, PI):
                for name, args in (("Read", {"file_path": "LEARNINGS.md"}), ("Bash", {"command": "cat LEARNINGS.md STATE.md"}), ("mcp__codex_app__get_usage_limits", {}), ("mcp__codex_app__read_thread", {"threadId": UNKNOWN}), ("mcp__codex_app__wait_threads", {"targets": [{"threadId": UNKNOWN}]})):
                    with self.subTest(session=session, name=name):
                        self.assertIn("no task registration", self.gate.hook(self.event(name, args, session)))

    def test_manual_native_goal_reads_do_not_need_registration_or_runtime(self):
        self.registry["governance"]["status"] = "paused"
        self.write("lab/registry.json", self.registry)
        self.gate = control.Gate(self.root, NOW)
        before = (self.root / "lab/control-state.json").read_bytes()
        with mock.patch.object(self.gate, "locked", side_effect=AssertionError("goal reads must not lock runtime")), mock.patch.object(self.gate, "identity", side_effect=AssertionError("goal reads must not need registration")):
            for session in (PI, OWNER, UNKNOWN):
                for name, arguments in (("get_goal", {}), ("functions.get_goal", {}), ("functions.exec", {"code": "text(await tools.get_goal({}));"})):
                    with self.subTest(session=session, tool=name):
                        self.assertIn("no task registration", self.gate.hook(self.event(name, arguments, session)))
        self.assertEqual(before, (self.root / "lab/control-state.json").read_bytes())

    def test_manual_report_figures_need_no_registration_or_running_state(self):
        png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a3ioAAAAASUVORK5CYII=")
        paths = ("lab/tasks/unregistered/STABILITY_FIGURE.png", "lab/reviews/old-study/figures/trajectory.png", "lab/tasks/unregistered/plots/modes.png")
        for name in paths:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(png)
        self.registry["governance"]["status"] = "paused"
        self.write("lab/registry.json", self.registry)
        self.gate = control.Gate(self.root, NOW)
        before = (self.root / "lab/control-state.json").read_bytes()
        with mock.patch.object(self.gate, "locked", side_effect=AssertionError("report viewing must not lock runtime")), mock.patch.object(self.gate, "identity", side_effect=AssertionError("report viewing must not need registration")):
            for session in (PI, INVESTMENT_CHAT, UNKNOWN):
                for name in paths:
                    with self.subTest(session=session, path=name):
                        result = self.gate.hook(self.event("functions.view_image", {"path": str(self.root / name), "detail": "original"}, session))
                        self.assertIn("no task registration", result)
        self.assertEqual(before, (self.root / "lab/control-state.json").read_bytes())

    def test_manual_report_image_exception_keeps_payload_and_path_guards(self):
        png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a3ioAAAAASUVORK5CYII=")
        cases = {
            "lab/tasks/x/raw/Figure.png": png,
            "lab/tasks/x/data/Figure.png": png,
            "lab/reviews/x/responses/Figure.png": png,
            "notes/Figure.png": png,
            "lab/tasks/x/frame.png": png,
            "lab/tasks/x/Figure.npz": png,
            "lab/tasks/x/FAKE_FIGURE.png": b"PK\x03\x04binary payload",
            "lab/tasks/x/LARGE_FIGURE.png": png + b"x" * self.gate.policy["max_read_bytes"],
        }
        for name, data in cases.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (self.root / "lab/tasks/x/OUTSIDE_FIGURE.png").symlink_to("/etc/hosts")
        (self.root / "lab/tasks/x/ALIAS_FIGURE.png").symlink_to(self.root / "lab/tasks/x/raw/Figure.png")
        for name in (*cases, "lab/tasks/x/OUTSIDE_FIGURE.png", "lab/tasks/x/ALIAS_FIGURE.png", "../outside.png"):
            with self.subTest(path=name), self.assertRaises(control.Denied):
                self.gate.hook(self.event("view_image", {"path": name}, PI))
        safe = self.root / "lab/tasks/x/SAFE_FIGURE.png"
        safe.write_bytes(png)
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("Read", {"file_path": str(safe)}, PI))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("view_image", {"path": str(safe), "remote_url": "https://example.com"}, PI))

    def test_manual_native_goal_coordination_keeps_single_pi_and_science_separate(self):
        self.manual_worker()
        self.registry["governance"]["status"] = "paused"
        self.registry["manual_usage_check"]["remaining_percent"] = 20
        self.write("lab/registry.json", self.registry)
        self.state["governance"]["status"] = "paused"
        self.save_state()
        self.gate = control.Gate(self.root, NOW)
        state_before = (self.root / "lab/control-state.json").read_bytes()
        registry_before = (self.root / "lab/registry.json").read_bytes()
        calls = [("create_goal", {"objective": "Earn an independently tested scientific result."}),
                 ("update_goal", {"status": "paused"})]
        for name, arguments in calls:
            with self.subTest(tool=name):
                self.assertIn("native goal coordination", self.gate.hook(self.event(name, arguments)))
                code = "text(await tools." + name + "(" + json.dumps(arguments) + "));"
                self.assertIn("native goal coordination", self.gate.hook(self.event("functions.exec", {"code": code})))
                for session in (OWNER, UNKNOWN):
                    with self.subTest(session=session), self.assertRaises(control.Denied):
                        self.gate.hook(self.event(name, arguments, session))
        self.assertEqual(state_before, (self.root / "lab/control-state.json").read_bytes())
        self.assertEqual(registry_before, (self.root / "lab/registry.json").read_bytes())
        for name, arguments in (("exec_command", {"cmd": "python3 lab/tasks/pilot/check.py"}),
                                ("Read", {"file_path": "data/responses.json"}),
                                ("mcp__codex_app__create_thread", self.request()["arguments"])):
            with self.subTest(tool=name), self.assertRaises(control.Denied):
                self.gate.hook(self.event(name, arguments))
        self.rotate_fixture_pi()
        self.assertIn("native goal coordination", self.gate.hook(self.event("create_goal", calls[0][1], UNKNOWN)))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("create_goal", calls[0][1], PI))

    def test_manual_common_read_commands_quoted_files_subdirectories_and_controller(self):
        commands = ["cat 'notes/quoted file.txt'", "sed -n '1,20p' LEARNINGS.md", "head -n 5 STATE.md", "tail -10 STATE.md", "rg -n 'project' LEARNINGS.md", "rg -n -g '*.md' 'project' .", "rg --files", "ls -la", "pwd", "wc -l STATE.md", self.cmd("read", "notes/quoted file.txt"), self.cmd("status")]
        for command in commands:
            with self.subTest(command=command):
                self.gate.hook(self.event("Bash", {"command": command}, INVESTMENT_CHAT))
        self.gate.hook(self.event("exec_command", {"cmd": "cat 'quoted file.txt'", "workdir": str(self.root / "notes")}, INVESTMENT_CHAT))
        self.assertEqual(self.gate.read("notes/quoted file.txt"), "An ordinary note.\n")

    def test_manual_native_read_glob_grep_and_source_under_data(self):
        for name, args in (("Read", {"file_path": "data/schema.py"}), ("Read", {"file_path": "data/README.md"}), ("Glob", {"pattern": "notes/*.txt"}), ("Grep", {"path": "LEARNINGS.md", "pattern": "project"}), ("Grep", {"path": ".", "glob": "*.md", "pattern": "project"}), ("Grep", {"path": ".", "type": "python", "pattern": "source"})):
            with self.subTest(name=name, args=args):
                self.gate.hook(self.event(name, args, INVESTMENT_CHAT))

    def test_manual_large_registry_excerpts_do_not_need_registration(self):
        cap = self.gate.policy["max_read_bytes"]
        self.registry["archived_notes"] = ["ordinary history π"] * (cap // 10)
        source = json.dumps(self.registry, indent=2, ensure_ascii=False)
        self.write("lab/registry.json", source)
        self.gate = control.Gate(self.root, NOW)
        lines, size = len(source.splitlines()), len(source.encode())
        self.assertGreater(size, cap)
        commands = ["head -n 3 lab/registry.json", "head -3 lab/registry.json",
                    "sed -n '8,14p' lab/registry.json", "tail -n 3 lab/registry.json",
                    "head -c 64 lab/registry.json", "tail -c 64 lab/registry.json",
                    "tail -n +%s lab/registry.json" % (lines - 2),
                    "tail -c +%s lab/registry.json" % (size - 63)]
        with mock.patch.object(self.gate, "locked", side_effect=AssertionError("context must not lock state")), mock.patch.object(self.gate, "identity", side_effect=AssertionError("context must not need registration")):
            for command in commands:
                with self.subTest(command=command):
                    self.gate.hook(self.event("Bash", {"command": command}, INVESTMENT_CHAT))

    def test_manual_large_context_full_or_excessive_output_stays_blocked(self):
        cap = self.gate.policy["max_read_bytes"]
        lines = cap // 4 + 2
        self.write("notes/large.md", "row\n" * lines)
        commands = ["cat notes/large.md", "head -c %s notes/large.md" % (cap + 1),
                    "tail -c %s notes/large.md" % (cap + 1),
                    "head -n %s notes/large.md" % lines, "tail -n %s notes/large.md" % lines,
                    "sed -n '1,%sp' notes/large.md" % lines,
                    "tail -n +1 notes/large.md", "tail -c +1 notes/large.md"]
        for command in commands:
            with self.subTest(command=command), self.assertRaises(control.Denied):
                self.gate.hook(self.event("Bash", {"command": command}, INVESTMENT_CHAT))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("Read", {"file_path": "notes/large.md"}, INVESTMENT_CHAT))

    def test_manual_large_context_can_skip_a_long_unselected_line(self):
        cap = self.gate.policy["max_read_bytes"]
        self.write("notes/large.md", "prefix π\n" + "z" * (cap + 10) + "\ntail é\n")
        for command in ("head -n 1 notes/large.md", "sed -n '3p' notes/large.md", "tail -n 1 notes/large.md"):
            with self.subTest(command=command):
                self.gate.hook(self.event("Bash", {"command": command}, INVESTMENT_CHAT))
        for command in ("head -n 2 notes/large.md", "sed -n '2p' notes/large.md"):
            with self.subTest(command=command), self.assertRaises(control.Denied):
                self.gate.hook(self.event("Bash", {"command": command}, INVESTMENT_CHAT))

    def test_manual_context_excerpts_keep_whole_file_type_and_path_checks(self):
        cap = self.gate.policy["max_read_bytes"]
        self.write("notes/binary.md", "safe prefix\n" + "x" * cap + "\x00")
        (self.root / "notes/invalid.md").write_bytes(b"safe prefix\n" + b"x" * cap + b"\xff")
        self.write("raw/hidden.md", "A protected raw payload\n")
        (self.root / "notes/outside.md").symlink_to("/etc/hosts")
        (self.root / "notes/alias.json").symlink_to(self.root / "data/responses.json")
        for path in ("notes/binary.md", "notes/invalid.md", "raw/hidden.md", "data/responses.json", "notes/outside.md", "notes/alias.json"):
            for template in ("head -n 1 %s", "sed -n '1p' %s", "tail -c 1 %s"):
                command = template % path
                with self.subTest(command=command), self.assertRaises(control.Denied):
                    self.gate.hook(self.event("Bash", {"command": command}, INVESTMENT_CHAT))

    def test_manual_metadata_and_additional_source_documents_are_readable(self):
        for name in ("mcp__codex_app__list_archived_threads", "clock__curr_time"):
            self.gate.hook(self.event(name, {}, INVESTMENT_CHAT))
        for extension in ("rmd", "qmd", "sh", "bash", "zsh"):
            path = "notes/source." + extension
            self.write(path, "# Ordinary UTF-8 source/documentation\n")
            self.gate.hook(self.event("Read", {"file_path": path}, INVESTMENT_CHAT))
        self.write("notes/outcomes.ipynb", "{}")
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("Read", {"file_path": "notes/outcomes.ipynb"}, INVESTMENT_CHAT))

    def test_manual_directory_search_does_not_decode_or_size_gate_unrelated_notes(self):
        self.write("notes/binary.md", "unrelated\x00binary")
        self.write("notes/large.md", "x" * (self.gate.policy["max_read_bytes"] + 1))
        with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("Directory search authorization must not read candidate bytes")):
            self.gate.hook(self.event("Bash", {"command": "rg -n -g '*.md' learning ."}, INVESTMENT_CHAT))
            self.gate.hook(self.event("Grep", {"path": ".", "glob": "*.md", "pattern": "learning"}, INVESTMENT_CHAT))
        for path in ("notes/binary.md", "notes/large.md"):
            with self.subTest(path=path), self.assertRaises(control.Denied):
                self.gate.hook(self.event("Read", {"file_path": path}, INVESTMENT_CHAT))

    def test_manual_glob_lists_filenames_without_reading_payload_bytes(self):
        self.write("notes/payload.npz", "binary\x00payload")
        with mock.patch.object(self.gate, "context_file", side_effect=AssertionError("Glob inventory must not read file bytes")):
            self.gate.hook(self.event("Glob", {"path": "notes", "pattern": "*"}, INVESTMENT_CHAT))
        (self.root / "notes/outside.md").symlink_to("/etc/hosts")
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("Glob", {"path": "notes", "pattern": "*"}, INVESTMENT_CHAT))

    def test_manual_directory_search_rejects_backend_specific_globs(self):
        for pattern in ("{*.md,*.csv}", "**/*", "!*.npz", "notes/*", "*.csv"):
            with self.subTest(pattern=pattern):
                with self.assertRaises(control.Denied):
                    self.gate.hook(self.event("Grep", {"path": ".", "glob": pattern, "pattern": "x"}, INVESTMENT_CHAT))
                with self.assertRaises(control.Denied):
                    self.gate.hook(self.event("Bash", {"command": shlex.join(["rg", "-g", pattern, "x", "."])}, INVESTMENT_CHAT))
        for command in ("rg {x,data/responses.json} LEARNINGS.md", "rg * LEARNINGS.md", "cat ~+/STATE.md"):
            with self.assertRaises(control.Denied):
                self.gate.hook(self.event("Bash", {"command": command}, INVESTMENT_CHAT))

    def test_manual_literal_read_wrapper_does_not_require_registration(self):
        code = "text(await tools.exec_command(" + json.dumps({"cmd": "cat LEARNINGS.md"}) + "));"
        self.gate.hook(self.event("functions.exec", {"code": code}, INVESTMENT_CHAT))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("functions.exec", {"code": "text(2 + 2);"}, PI))
        batch = "const r = await tools.exec_command({cmd: 'pwd'}); text(r.output);"
        self.gate.hook(self.event("functions.exec", {"code": batch}, OPERATOR))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("functions.exec", {"code": batch}, PI))

    def test_manual_raw_binary_traversal_and_symlink_reads_stay_blocked(self):
        self.write("notes/binary.txt", "binary\x00payload")
        self.write("notes/record.npz", "binary payload format")
        self.write("raw/hidden.md", "A protected raw payload with a note extension")
        (self.root / "notes/outside.md").symlink_to("/etc/hosts")
        (self.root / "notes/alias.json").symlink_to(self.root / "data/responses.json")
        for path in ("data/responses.json", "notes/binary.txt", "notes/record.npz", "raw/hidden.md", "../outside.md", "notes/outside.md", "notes/alias.json"):
            for name, args in (("Read", {"file_path": path}), ("Bash", {"command": shlex.join(["cat", path])})):
                with self.subTest(path=path, name=name), self.assertRaises(control.Denied):
                    self.gate.hook(self.event(name, args, INVESTMENT_CHAT))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("Grep", {"path": "data", "glob": "*.json", "pattern": "."}, INVESTMENT_CHAT))

    def test_manual_read_exception_rejects_shell_execution_and_unsafe_search(self):
        for command in ("cat STATE.md; python3 science.py", "cat STATE.md > /tmp/write", "cat $(pwd)/STATE.md", "cat STATE.md | python3 -c 'print(1)'", "sed -n '1e touch /tmp/x' STATE.md", "sed -i '' STATE.md", "rg --pre python3 'x' LEARNINGS.md", "rg --pre=python3 'x' LEARNINGS.md", "python3 -c 'print(1)'", "python3 science.py"):
            with self.subTest(command=command), self.assertRaises(control.Denied):
                self.gate.hook(self.event("Bash", {"command": command}, PI))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("apply_patch", {"patch": "*** Begin Patch\n*** Add File: notes/new.md\n+x\n*** End Patch"}, INVESTMENT_CHAT))

    def manual_worker(self):
        self.registry["tasks"].append({"id": "pilot", "thread_id": OWNER, "status": "running", "role": "investigation_lead", "path": "lab/tasks/pilot"})
        self.write("lab/registry.json", self.registry)
        self.gate = control.Gate(self.root, NOW)

    def rotate_fixture_pi(self):
        policy = json.loads((self.root / "lab/policy.json").read_text())
        policy["pi_session_id"] = UNKNOWN
        self.write("lab/policy.json", policy)
        self.registry["pi"] = {"thread_id": UNKNOWN, "previous_thread_ids": [PI]}
        self.write("lab/registry.json", self.registry)
        self.gate = control.Gate(self.root, NOW)

    def test_manual_pi_rotation_preserves_role_separation_and_history_reads(self):
        self.rotate_fixture_pi()
        patch = {"patch": "*** Begin Patch\n*** Update File: STATE.md\n@@\n-old\n+new\n*** End Patch"}
        self.assertIn("coordination records", self.gate.hook(self.event("apply_patch", patch, UNKNOWN)))
        self.gate.hook(self.event("Bash", {"command": "cat STATE.md"}, PI))
        self.gate.hook(self.event("mcp__codex_app__read_thread", {"threadId": PI}, UNKNOWN))
        for session in (PI, UNKNOWN):
            with self.subTest(session=session), self.assertRaises(control.Denied):
                self.gate.hook(self.event("Bash", {"command": "python3 lab/tasks/pilot/check.py"}, session))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("apply_patch", patch, PI))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("mcp__codex_app__create_thread", {"model": "gpt-6.1-sol", "thinking": "max"}, PI))

    def test_manual_worker_report_follows_rotated_pi(self):
        self.manual_worker()
        self.rotate_fixture_pi()
        args = {"threadId": UNKNOWN, "prompt": "pilot complete; saved result; jobs0."}
        self.assertIn("report to canonical PI", self.gate.hook(self.event("mcp__codex_app__send_message_to_thread", args, OWNER)))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("mcp__codex_app__send_message_to_thread", dict(args, threadId=PI), OWNER))

    def test_manual_pi_can_report_reserve_or_handoff_to_operator_while_paused(self):
        self.registry["governance"]["status"] = "paused"
        self.registry["manual_usage_check"]["remaining_percent"] = 20
        self.write("lab/registry.json", self.registry)
        self.state["governance"]["status"] = "paused"
        self.save_state()
        self.gate = control.Gate(self.root, NOW)
        args = {"threadId": OPERATOR, "prompt": "Reserve reached; saved checkpoint. Pause existing heartbeat."}
        self.assertIn("coordination report", self.gate.hook(self.event("mcp__codex_app__send_message_to_thread", args)))
        wrapper = "text(await tools.mcp__codex_app__send_message_to_thread(" + json.dumps(args) + "));"
        self.assertIn("coordination report", self.gate.hook(self.event("functions.exec", wrapper)))
        rejected = [dict(args, threadId=OWNER), dict(args, hostId="remote"), dict(args, model="gpt-6.1-sol", thinking="ultra"), dict(args, prompt="x " * 401)]
        for item in rejected:
            with self.subTest(item=item), self.assertRaises(control.Denied):
                self.gate.hook(self.event("mcp__codex_app__send_message_to_thread", item))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("mcp__codex_app__create_thread", {"model": "gpt-6.1-sol", "thinking": "max"}))

    def test_manual_worker_report_returns_to_pi_after_collection_or_pause(self):
        self.manual_worker()
        self.registry["tasks"][0]["status"] = "completed"
        self.registry["governance"]["status"] = "paused"
        self.registry.pop("manual_usage_check", None)
        self.write("lab/registry.json", self.registry)
        self.state["governance"]["status"] = "paused"
        self.save_state()
        self.gate = control.Gate(self.root, NOW)
        args = {"threadId": PI, "hostId": "local", "prompt": "pilot complete; saved lab/tasks/pilot/RESULT.md; jobs0; no new work."}
        self.assertIn("report to canonical PI", self.gate.hook(self.event("mcp__codex_app__send_message_to_thread", args, OWNER)))
        wrapper = "text(await tools.mcp__codex_app__send_message_to_thread(" + json.dumps(args) + "));"
        self.assertIn("report to canonical PI", self.gate.hook(self.event("functions.exec", wrapper, OWNER)))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("Bash", {"command": "python3 lab/tasks/pilot/check.py"}, OWNER))

    def test_manual_worker_report_does_not_enable_dispatch_or_model_changes(self):
        self.manual_worker()
        args = {"threadId": PI, "prompt": "pilot complete; saved result."}
        rejected = [dict(args, threadId=REVIEWER), dict(args, hostId="remote"), dict(args, model="gpt-6.1-sol"),
                    dict(args, thinking="max"), dict(args, prompt=" "), dict(args, prompt="x " * 401), dict(args, prompt="x" * 8001)]
        for item in rejected:
            with self.subTest(args=item), self.assertRaises(control.Denied):
                self.gate.hook(self.event("mcp__codex_app__send_message_to_thread", item, OWNER))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("mcp__codex_app__send_message_to_thread", args, UNKNOWN))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("mcp__codex_app__create_thread", {}, OWNER))
        self.registry["tasks"][0]["role"] = "unknown"
        self.write("lab/registry.json", self.registry)
        with self.assertRaises(control.Denied):
            control.Gate(self.root, NOW).hook(self.event("mcp__codex_app__send_message_to_thread", args, OWNER))

    def test_manual_worker_available_tools_defer_to_platform_authorization(self):
        self.manual_worker()
        self.gate.hook(self.event("mcp__cua_repl__js", {"code": "await cua.getState();"}, OWNER))
        self.gate.hook(self.event("mcp__gmail__create_draft", {"subject": "Human-authorized draft"}, OWNER))
        for name, args in (("spawn_agent", {}), ("Bash", {"command": "touch lab/policy.json"}), ("apply_patch", {"patch": "*** Begin Patch\n*** Add File: lab/tasks/other/RESULT.md\n+x\n*** End Patch"})):
            with self.subTest(name=name), self.assertRaises(control.Denied):
                self.gate.hook(self.event(name, args, OWNER))

    def test_manual_reserved_owner_can_start_execution_before_send_returns(self):
        self.manual_worker()
        self.registry["tasks"][0]["status"] = "reserved"
        self.write("lab/registry.json", self.registry)
        self.gate = control.Gate(self.root, NOW)
        self.gate.hook(self.event("Bash", {"command": "date -u '+%Y-%m-%dT%H:%M:%SZ'"}, OWNER))
        self.gate.hook(self.event("Bash", {"command": "python3 lab/tasks/pilot/check.py"}, OWNER))
        self.gate.hook(self.event("apply_patch", {"patch": "*** Begin Patch\n*** Add File: lab/tasks/pilot/check.py\n+x\n*** End Patch"}, OWNER))
        for session in (UNKNOWN, PI):
            with self.subTest(session=session), self.assertRaises(control.Denied):
                self.gate.hook(self.event("Bash", {"command": "python3 lab/tasks/pilot/check.py"}, session))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("apply_patch", {"patch": "*** Begin Patch\n*** Add File: lab/tasks/other/check.py\n+x\n*** End Patch"}, OWNER))

    def test_manual_registry_reservation_is_not_shadowed_by_legacy_state(self):
        self.manual_worker()
        self.registry["tasks"][0]["status"] = "reserved"
        self.write("lab/registry.json", self.registry)
        self.state["assignments"]["pilot"] = {"thread_id": OWNER, "status": "completed"}
        self.save_state()
        self.gate = control.Gate(self.root, NOW)
        self.gate.hook(self.event("Bash", {"command": "python3 lab/tasks/pilot/check.py"}, OWNER))

    def test_manual_duplicate_reservations_still_deny_execution(self):
        self.manual_worker()
        self.registry["tasks"][0]["status"] = "reserved"
        self.registry["tasks"].append({"id": "other", "thread_id": OWNER, "status": "reserved", "role": "investigation_lead", "path": "lab/tasks/other"})
        self.write("lab/registry.json", self.registry)
        self.gate = control.Gate(self.root, NOW)
        with self.assertRaisesRegex(control.Denied, "no unique active"):
            self.gate.hook(self.event("Bash", {"command": "python3 lab/tasks/pilot/check.py"}, OWNER))

    def test_manual_worker_honors_explicit_scoped_source_ownership(self):
        self.manual_worker()
        self.registry["tasks"][0]["owned_paths"] = ["lab/tasks/pilot", "sources/pilot-audit"]
        self.write("lab/registry.json", self.registry)
        self.gate = control.Gate(self.root, NOW)
        self.gate.hook(self.event("apply_patch", {"patch": "*** Begin Patch\n*** Add File: sources/pilot-audit/check.py\n+x\n*** End Patch"}, OWNER))
        for path in ("sources/other-audit/check.py", "lab/policy.json", "STATE.md"):
            with self.subTest(path=path), self.assertRaises(control.Denied):
                self.gate.hook(self.event("apply_patch", {"patch": "*** Begin Patch\n*** Add File: " + path + "\n+x\n*** End Patch"}, OWNER))
        for broad in (".", "sources", "lab/tasks", "lab/policy.json"):
            self.registry["tasks"][0]["owned_paths"] = [broad]
            self.write("lab/registry.json", self.registry)
            with self.subTest(broad=broad), self.assertRaises(control.Denied):
                control.Gate(self.root, NOW).hook(self.event("apply_patch", {"patch": "*** Begin Patch\n*** Add File: sources/pilot-audit/x.py\n+x\n*** End Patch"}, OWNER))

    def test_manual_dispatch_accepts_projectless_other_project_and_distinct_explicit_chat(self):
        for target in ({"type": "projectless"}, {"type": "project", "projectId": "other-explicit-project", "environment": {"type": "local"}}):
            self.gate.hook(self.event("mcp__codex_app__create_thread", {"model": "gpt-6.1-sol", "thinking": "max", "target": target}))
        for target in (OPERATOR, UNKNOWN):
            self.gate.hook(self.event("mcp__codex_app__send_message_to_thread", {"model": "gpt-6.1-sol", "thinking": "max", "threadId": target, "prompt": "Bounded human-authorized assignment or workflow coordination."}))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("mcp__codex_app__send_message_to_thread", {"model": "gpt-6.1-sol", "thinking": "max", "threadId": PI}))
        with self.assertRaises(control.Denied):
            self.gate.hook(self.event("mcp__codex_app__create_thread", {"model": "gpt-6.1-sol", "thinking": "ultra", "target": {"type": "projectless"}}))


class RegistryRecoveryTests(ControlFixture):
    """Exercise the real hook entrypoint with corrupt coordination records."""
    def setUp(self):
        super().setUp()
        self.registry["governance"]["mode"] = "simple_manual"
        self.registry["tasks"].append({"id": "pilot", "thread_id": OWNER, "status": "running", "role": "investigation_lead", "path": "lab/tasks/pilot"})
        self.write("lab/registry.json", self.registry)
        self.write("STATE.md", "Saved current state.\n")
        self.write("data/responses.json", "[1,2,3]")

    def run_hook(self, event, post=False):
        original = control.Gate
        stdout = io.StringIO()
        def constructor(**kwargs):
            return original(self.root, NOW, **kwargs)
        with mock.patch.object(control, "Gate", side_effect=constructor), mock.patch("sys.stdin", io.StringIO(json.dumps(event))), contextlib.redirect_stdout(stdout):
            self.assertEqual(control.main(["--post-hook"] if post else ["--hook"]), 0)
        return json.loads(stdout.getvalue())

    def test_invalid_or_missing_registry_retains_repair_and_safe_reads_only(self):
        registry_path = self.root / "lab/registry.json"
        events = [self.event("Bash", {"command": "python3 science.py"}, OWNER),
                  self.event("mcp__codex_app__create_thread", self.request()["arguments"], PI),
                  self.event("apply_patch", {"patch": "*** Begin Patch\n*** Update File: lab/registry.json\n@@\n-x\n+y\n*** End Patch"}, PI),
                  self.event("Read", {"file_path": "data/responses.json"}, UNKNOWN),
                  self.event("Bash", {"command": "cat STATE.md; python3 science.py"}, PI)]
        for broken in ('{"governance": {"mode": "simple_manual"},}', '[]', None):
            if broken is None:
                registry_path.unlink()
            else:
                registry_path.write_text(broken)
            before = (self.root / "lab/control-state.json").read_bytes()
            with self.subTest(broken=broken):
                with self.assertRaises(control.Denied):
                    control.Gate(self.root, NOW)
                for event in (self.event("apply_patch", {"patch": "repair metadata"}, OPERATOR),
                              self.event("Read", {"file_path": "STATE.md"}, UNKNOWN),
                              self.event("Bash", {"command": self.cmd("status")}, PI),
                              self.event("mcp__codex_app__get_usage_limits", {}, PI),
                              self.event("get_goal", {}, UNKNOWN),
                              self.event("update_goal", {"status": "paused"}, PI),
                              self.event("mcp__codex_app__send_message_to_thread", {"threadId": OPERATOR, "prompt": "Registry is invalid; please repair while science stays stopped."}, PI),
                              self.event("functions.exec", {"code": 'text(await tools.exec_command({"cmd":"cat STATE.md"}));'}, UNKNOWN)):
                    self.assertEqual(self.run_hook(event)["hookSpecificOutput"]["permissionDecision"], "allow")
                for event in events:
                    self.assertEqual(self.run_hook(event)["hookSpecificOutput"]["permissionDecision"], "deny")
                self.assertIn("no receipt recorded", self.run_hook(self.event("mcp__codex_app__get_usage_limits"), post=True)["systemMessage"])
                self.assertEqual(before, (self.root / "lab/control-state.json").read_bytes())

    def test_operator_repair_does_not_depend_on_runtime_state(self):
        (self.root / "lab/control-state.json").write_text('{"broken":}')
        self.assertEqual(self.run_hook(self.event("Bash", {"command": "repair state"}, OPERATOR))["hookSpecificOutput"]["permissionDecision"], "allow")
        for session in (PI, UNKNOWN):
            with self.subTest(session=session):
                self.assertEqual(self.run_hook(self.event("Bash", {"command": "repair state"}, session))["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_invalid_policy_cannot_grant_operator_repair(self):
        (self.root / "lab/policy.json").write_text('{"broken":}')
        self.assertEqual(self.run_hook(self.event("Bash", {"command": "repair state"}, OPERATOR))["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
