"""``tests/agent_rules.py``'s rules, each bound by a test below (the rules are listed in its docstring, the one
source), and the rules file and the skill this brain keeps. The ledgers, packets and definitions are
``test_agent_run``'s. Run from the brain's root."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import agent_rules as R  # noqa: E402
import test_agent_run as TA  # noqa: E402

A = R.A
finding, old_finding, run_file = TA.finding, TA.old_finding, TA.run_file
GOOD = TA.GOOD.replace(b"Origin. A gap.\n", b"Origin. Gap: a gap.\nMeasure: its rows.\n")


def rule(check: str, **over) -> dict:
    return {"id": "rule-" + check, "says": "what it says", "expects": "what it expects", "check": check, **over}


def call(kind="brain:one", prompt="a prompt", name: str = "Agent", **more) -> dict:
    given = {k: v for k, v in (("subagent_type", kind), ("prompt", prompt)) if v is not None}
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": "x"},
                                                         {"type": "tool_use", "id": "t", "name": name,
                                                          "input": given}]}, **more}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class Base(TA.Base):
    def setUp(self):
        super().setUp()
        self.agent(GOOD)
        self.write_rules([rule(check) for check in R.CHECKS])
        self.log = None

    def write_rules(self, rules, **over) -> None:
        with open(os.path.join(self.root, A.RULES), "w", encoding="utf-8") as f:
            json.dump({"schema": "agent_rules/1", "rules": rules, **over}, f)

    def write_log(self, *rows, tail: bytes = b"") -> str:
        self.log = self.put("session.jsonl", b"".join(
            (row if isinstance(row, bytes) else json.dumps(row).encode()) + b"\n" for row in rows) + tail)
        return self.log

    def state(self, check: str) -> tuple[str, dict]:
        """The state and what was observed of the one rule of ``check``."""
        (got,) = [r for r in R.judge(self.root, self.data, self.log) if r["check"] == check]
        self.assertEqual((got["id"], sorted(got)), ("rule-" + check, ["check", "id", "observed", "state"]))
        return got["state"], got["observed"]

    def run_under(self, *findings: dict, **over) -> str:
        """A run under the rules, each from its own packet; the message of the last is ``self.message``."""
        self.out = os.path.join(self.tmp, "packet-%d" % len(self.data))
        row_id = self.record(run_file(*findings, **over))
        self.message = self.given("message.txt").decode()
        return row_id

    def faults(self, reason: str):
        return self.assertRaisesRegex(R.Fault, "^%s$" % reason)


class Load(Base):
    def test_the_rules_are_the_files(self):
        rules = [rule(check) for check in R.CHECKS]
        self.assertEqual(R.load(self.root), rules)
        self.write_rules(rules + [rule("earns", id="another")])
        self.assertEqual(len(R.load(self.root)), len(R.CHECKS) + 1)

    def test_each_break_of_the_file_is_a_fault(self):
        rules = [rule(check) for check in R.CHECKS]
        path = os.path.join(self.root, A.RULES)
        for text in (b"not json", b"[1]", b"{}", json.dumps({"schema": "agent_rules/2", "rules": rules}).encode(),
                     json.dumps({"schema": "agent_rules/1", "rules": {}}).encode(),
                     json.dumps({"schema": "agent_rules/1", "rules": rules, "more": 1}).encode()):
            with open(path, "wb") as f:
                f.write(text)
            with self.subTest(text=text), self.faults("rules_unreadable"):
                R.load(self.root)
        os.remove(path)
        with self.faults("rules_unreadable"):
            R.load(self.root)
        first = rules[0]
        for broken in ("a rule", {**first, "more": "x"}, {k: v for k, v in first.items() if k != "expects"},
                       {**first, "says": " "}, {**first, "expects": None}, {**first, "id": 7},
                       {**first, "check": "no_such_check"}, {**first, "check": ["earns"]}):
            self.write_rules([broken] + rules[1:])
            with self.subTest(broken=broken), self.faults("bad_rule"):
                R.load(self.root)
        self.write_rules(rules + [rules[0]])
        with self.faults("rule_id_twice"):
            R.load(self.root)
        self.write_rules(rules[1:])
        with self.faults("check_without_rule"):
            R.load(self.root)

    def test_the_checks_are_these_six(self):
        self.assertEqual(sorted(R.CHECKS), ["calls_are_rows", "definitions", "earns", "improves", "no_unjudged_left",
                                            "repeats_rare"])


class Definitions(Base):
    def test_a_definition_with_its_origin_its_measure_and_tools_that_only_read_holds(self):
        self.agent(GOOD.replace(b"name: one", b"name: two").replace(b"Read, Grep", b"Read, Grep, Glob"), "two")
        self.assertEqual(self.state("definitions"), ("held", {"files": 2, "broken": []}))

    def test_each_break_refutes_and_is_named(self):
        for old, new, reason in ((b"Origin. Gap: ", b"Gap: ", "no_origin"),
                                 (b"Origin. Gap: ", b"\nOrigin. Gap: ", "no_origin"),
                                 (b"Measure: ", b"Measured ", "no_origin"),
                                 (b"tools: Read, Grep\n", b"", "tools_not_read_only"),
                                 (b"Read, Grep", b"Read, Bash", "tools_not_read_only"),
                                 (b"Read, Grep", b"Read, Write", "tools_not_read_only"),
                                 (b"model: opus", b"model: haiku", "model_not_allowed")):
            self.agent(GOOD.replace(old, new))
            with self.subTest(old=old, new=new):
                self.assertEqual(self.state("definitions"), ("refuted", {"files": 1, "broken": ["one:" + reason]}))

    def test_a_file_of_agents_that_is_no_definition_refutes(self):
        self.agent(b"notes", "notes.txt")
        os.rename(os.path.join(self.root, "agents", "notes.txt.md"), os.path.join(self.root, "agents", "notes.txt"))
        self.assertEqual(R.files(self.root), ["notes.txt", "one.md"])
        self.assertEqual(self.state("definitions"),
                         ("refuted", {"files": 2, "broken": ["notes.txt:not_a_definition_file"]}))

    def test_a_file_named_as_an_agent_without_md_is_not_that_agents_definition(self):
        with open(os.path.join(self.root, "agents", "one"), "wb") as f:
            f.write(b"notes")
        self.assertEqual(self.state("definitions"),
                         ("refuted", {"files": 2, "broken": ["one:not_a_definition_file"]}))
        self.assertEqual(list(self.state("earns")[1]), ["one"])

    def test_no_agent_is_no_broken_one_and_a_directory_that_cannot_be_listed_is_a_fault(self):
        os.remove(os.path.join(self.root, "agents", "one.md"))
        self.assertEqual(self.state("definitions"), ("held", {"files": 0, "broken": []}))
        self.assertEqual(self.state("earns"), ("not_due", {}))
        os.rmdir(os.path.join(self.root, "agents"))
        with self.faults("agents_unreadable"):
            self.state("definitions")


class Calls(Base):
    def test_each_agent_or_task_call_of_an_assistant_line_is_a_call(self):
        both = call()
        both["message"]["content"].append({"type": "tool_use", "name": "Task",
                                           "input": {"subagent_type": "Explore", "prompt": "look"}})
        log = self.write_log(
            {"type": "system", "subtype": "init"}, both, call("brain:two", "pç", parent_tool_use_id="t"),
            call(None, None), call(7, ["p"]), call(name="Bash"), {**call(), "type": "user"},
            {"type": "assistant", "message": {"content": "Agent"}}, {"type": "assistant", "message": None},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Agent", "input": "x"},
                                                          {"type": "text", "name": "Agent"}, "Agent"]}},
            {"type": "assistant"}, call("brain:one", "said beside the packet", name="SendMessage"),
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "SendMessage",
                                                          "input": {"to": "one", "message": "more"}}]}})
        self.assertEqual(R.TOOLS, ("Agent", "Task", "SendMessage"))
        self.assertEqual(R.calls(log), [
            {"type": "brain:one", "sha256": sha("a prompt")}, {"type": "Explore", "sha256": sha("look")},
            {"type": "brain:two", "sha256": sha("pç")}, {"type": None, "sha256": None},
            {"type": None, "sha256": None}, {"type": None, "sha256": None},
            {"type": None, "sha256": None}, {"type": None, "sha256": None}])

    def test_a_line_that_is_no_object_is_a_fault_but_a_last_line_still_being_written(self):
        self.assertEqual(len(R.calls(self.write_log(call(), b"", b"  ", call()))), 2)
        self.assertEqual(len(R.calls(self.write_log(call(), tail=b'{"type": "assist'))), 1)
        self.assertEqual(len(R.calls(self.write_log(call(), tail=json.dumps(call()).encode()))), 2)
        for rows in ((b"not json", call()), (b"[1]", call()), (call(), b'{"type": "assist')):
            with self.subTest(rows=rows), self.faults("log_unreadable"):
                R.calls(self.write_log(*rows))
        with self.faults("log_unreadable"):
            R.calls(os.path.join(self.tmp, "absent"))


class CallsAreRows(Base):
    def test_without_a_log_the_rule_is_not_due(self):
        self.assertEqual(self.state("calls_are_rows"), ("not_due", {"log": None}))

    def test_a_log_with_no_call_holds(self):
        self.write_log({"type": "system"}, call(name="Bash"))
        self.assertEqual(self.state("calls_are_rows"), ("held", {"calls": 0, "unrecorded": []}))

    def test_each_call_is_the_message_of_one_run_row_of_that_agent(self):
        self.run_under()
        first = self.message
        self.run_under()
        self.assertNotEqual(first, self.message)
        self.write_log(call(prompt=first), call(prompt=self.message))
        self.assertEqual(self.state("calls_are_rows"), ("held", {"calls": 2, "unrecorded": []}))
        self.write_log(call(prompt=first), call(prompt=first))
        self.assertEqual(self.state("calls_are_rows"),
                         ("refuted", {"calls": 2, "unrecorded": [{"type": "brain:one", "sha256": sha(first)}]}))

    def test_a_call_of_another_type_or_with_another_prompt_or_with_no_row_refutes(self):
        self.agent(GOOD.replace(b"name: one", b"name: two"), "two")
        self.run_under()
        for made in (call("general-purpose", self.message), call("one", self.message), call(None, self.message),
                     call("brain:two", self.message), call("brain:absent", self.message),
                     call(prompt=self.message + "\nAlso look at x."), call(prompt=None),
                     call(prompt=self.message, name="Task", parent_tool_use_id="t")):
            self.write_log(call(prompt=self.message), made)
            with self.subTest(made=made):
                state, seen = self.state("calls_are_rows")
                self.assertEqual((state, seen["calls"], len(seen["unrecorded"])), ("refuted", 2, 1))
                self.assertEqual(seen["unrecorded"], R.calls(self.log)[1:])
        self.write_log(call("brain:two", self.message))
        self.assertEqual(self.state("calls_are_rows")[0], "refuted")

    def test_a_text_sent_to_an_agent_beside_its_message_has_no_row(self):
        self.run_under()
        self.write_log(call(prompt=self.message, name="SendMessage"))
        self.assertEqual(self.state("calls_are_rows"),
                         ("refuted", {"calls": 1, "unrecorded": [{"type": None, "sha256": None}]}))
        self.write_log(call(prompt=self.message), {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "SendMessage", "input": {"to": "one", "message": "also x"}}]}})
        self.assertEqual(self.state("calls_are_rows"),
                         ("refuted", {"calls": 2, "unrecorded": [{"type": None, "sha256": None}]}))

    def test_a_run_row_of_an_earlier_session_is_no_row_for_a_call_of_this_one(self):
        self.run_under()
        self.write_log(call(prompt=self.message))
        self.assertEqual(self.state("calls_are_rows")[0], "held")
        self.row("session_start")
        self.assertEqual(self.state("calls_are_rows"),
                         ("refuted", {"calls": 1, "unrecorded": [{"type": "brain:one", "sha256": sha(self.message)}]}))
        self.data = b""
        self.row("decision")
        self.run_under()
        self.write_log(call(prompt=self.message))
        self.assertEqual(self.state("calls_are_rows")[0], "refuted")

    def test_a_run_before_the_rules_is_no_row_for_a_call(self):
        self.old_run(run_file(old_finding(1, A.CAUGHT, "t")))
        for made in (call(), call(prompt=None)):
            self.write_log(made)
            with self.subTest(made=made):
                self.assertEqual(self.state("calls_are_rows")[0], "refuted")


class NoUnjudgedLeft(Base):
    def test_unjudged_is_a_state_of_the_session_that_ran_the_agent_only(self):
        old = self.old_run(run_file(old_finding(1, A.CAUGHT, "t"), old_finding(2)))
        run = self.run_under(finding(1), finding(2, A.FALSE_ALARM, "why"))
        self.assertEqual(self.state("no_unjudged_left"), ("held", {"left": []}))
        self.row("session_end")
        self.assertEqual(self.state("no_unjudged_left"), ("held", {"left": []}))
        self.row("session_start")
        self.assertEqual(self.state("no_unjudged_left"), ("refuted", {"left": [old + "#2", run + "#1"]}))
        self.amend(old, finding(1, A.CAUGHT, "t"), finding(2, A.CARRIED, "true", old))
        self.assertEqual(self.state("no_unjudged_left"), ("refuted", {"left": [run + "#1"]}))
        self.amend(run, finding(1, A.CAUGHT, "t"), finding(2, A.FALSE_ALARM, "why"))
        self.assertEqual(self.state("no_unjudged_left"), ("held", {"left": []}))

    def test_a_run_before_any_session_start_is_of_no_session(self):
        self.data = b""
        self.row("decision")
        run = self.run_under(finding(1))
        self.assertEqual(self.state("no_unjudged_left"), ("refuted", {"left": [run + "#1"]}))


    def test_a_finding_of_an_agent_whose_definition_was_removed_is_still_listed(self):
        run = self.run_under(finding(1), finding(2, A.FALSE_ALARM, "why"))
        self.row("session_start")
        os.remove(os.path.join(self.root, "agents", "one.md"))
        self.assertEqual(self.state("no_unjudged_left"), ("refuted", {"left": [run + "#1"]}))
        self.assertEqual(self.state("earns"), ("not_due", {}))
        self.assertEqual(R.tagged(self.data)[1], ["one"])
        self.assertEqual(R.tagged(b""), (None, []))


class RepeatsRare(Base):
    def test_one_finding_in_ten_refutes_and_fewer_holds(self):
        self.assertEqual(self.state("repeats_rare"),
                         ("not_due", {"one": {"state": "not_due", "findings": 0, "repeats": 0}}))
        old = self.old_run(run_file(old_finding(1)))
        self.run_under()
        self.assertEqual(self.state("repeats_rare")[0], "not_due")
        self.run_under(*(finding(n, A.CAUGHT, "t") for n in range(1, 11)), finding(11, repeat_of=old + "#1"))
        self.assertEqual(self.state("repeats_rare"),
                         ("held", {"one": {"state": "held", "findings": 11, "repeats": 1}}))
        self.run_under(*(finding(n, A.CAUGHT, "t") for n in range(1, 9)), finding(9, repeat_of=old + "#1"))
        self.assertEqual(self.state("repeats_rare"),
                         ("refuted", {"one": {"state": "refuted", "findings": 20, "repeats": 2}}))


class Earns(Base):
    def test_an_agent_with_no_run_is_not_due_and_one_that_catches_holds(self):
        self.assertEqual(self.state("earns"), ("not_due", {"one": {
            "state": "not_due", "retire_due": False, "cost_over_gain": False, "caught": 0, "false_alarm": 0}}))
        self.run_under(finding(1, A.CAUGHT, "t"), finding(2, A.FALSE_ALARM, "why"))
        self.assertEqual(self.state("earns"), ("held", {"one": {
            "state": "held", "retire_due": False, "cost_over_gain": False, "caught": 1, "false_alarm": 1}}))

    def test_more_false_alarms_than_catches_under_the_rules_refutes(self):
        self.old_run(run_file(old_finding(1, A.FALSE_ALARM, "why"), old_finding(2, A.FALSE_ALARM, "why")))
        self.assertEqual(self.state("earns")[0], "held")
        self.run_under(finding(1, A.CAUGHT, "t"), finding(2, A.FALSE_ALARM, "why"), finding(3, A.FALSE_ALARM, "why"))
        self.assertEqual(self.state("earns"), ("refuted", {"one": {
            "state": "refuted", "retire_due": False, "cost_over_gain": False, "caught": 1, "false_alarm": 2}}))

    def test_an_agent_due_to_retire_refutes(self):
        for _ in range(4):
            self.old_run(run_file(old_finding(1)))
            self.row("session_start")
        self.assertEqual(self.state("earns")[0], "held")
        self.old_run(run_file(old_finding(1)))
        self.assertEqual(self.state("earns"), ("refuted", {"one": {
            "state": "refuted", "retire_due": True, "cost_over_gain": False, "caught": 0, "false_alarm": 0}}))

    def test_an_agent_whose_cost_is_over_what_it_can_have_saved_refutes_at_five_sessions(self):
        self.row("cost", TA.SESSION % 1000)
        for n in range(5):
            run = self.run_under(finding(1, A.CAUGHT, "t"))
            self.row("build", A.FORM2 + json.dumps(TA.cost_fields(run, TA.S1, TA.call(cost_usd_micros=1001))),
                     ["agents/one.md", A.TAG + "one"])
            self.assertEqual(self.state("earns"), ("refuted" if n == 4 else "held", {"one": {
                "state": "refuted" if n == 4 else "held", "retire_due": n == 4, "cost_over_gain": True,
                "caught": n + 1, "false_alarm": 0}}))
            self.row("session_start")

    def test_one_agent_refuting_refutes_the_rule_and_one_not_due_does_not_hide_one_that_holds(self):
        self.agent(GOOD.replace(b"name: one", b"name: two"), "two")
        self.run_under(finding(1, A.CAUGHT, "t"))
        state, seen = self.state("earns")
        self.assertEqual((state, seen["one"]["state"], seen["two"]["state"]), ("held", "held", "not_due"))
        self.old_run(run_file(old_finding(1, A.FALSE_ALARM, "why")), "two")
        self.assertEqual(self.state("earns")[0], "held")
        for _ in range(5):
            self.row("session_start")
            self.old_run(run_file(old_finding(1)), "two")
        state, seen = self.state("earns")
        self.assertEqual((state, seen["one"]["state"], seen["two"]["state"]), ("refuted", "held", "refuted"))


class Improves(Base):
    def before(self) -> str:
        """Before the rules: two runs, three findings, one of them a repeat, two caught, 2400 tokens."""
        first = self.old_run(run_file(old_finding(1, A.CAUGHT, "t"), old_finding(2, A.CAUGHT, "t")))
        second = self.old_run(run_file(old_finding(1)))
        self.amend(second, finding(1, A.FALSE_ALARM, "said before", repeat_of=first + "#1"))
        return first

    def under(self, sessions: int, run) -> None:
        for _ in range(sessions):
            self.row("session_start")
            self.run_under(**run) if isinstance(run, dict) else self.run_under(*run)

    def test_before_five_sessions_under_the_rules_it_is_not_due(self):
        self.assertEqual(R.AFTER_SESSIONS, 5)
        first = self.before()
        self.under(4, {"findings": [finding(1, A.CAUGHT, "t", repeat_of=first + "#1")], "tokens": 5000})
        self.assertEqual(self.state("improves"), ("not_due", {"one": {
            "state": "not_due", "sessions": 4, "caught_per_run_higher": False, "repeats_lower": False,
            "tokens_per_caught_lower": False}}))
        self.run_under()
        self.assertEqual(self.state("improves")[0], "not_due")

    def test_at_five_sessions_neither_fewer_repeats_nor_fewer_tokens_per_catch_refutes(self):
        first = self.before()
        self.under(5, {"findings": [finding(1, A.CAUGHT, "t", repeat_of=first + "#1")], "tokens": 1200})
        self.assertEqual(self.state("improves"), ("refuted", {"one": {
            "state": "refuted", "sessions": 5, "caught_per_run_higher": False, "repeats_lower": False,
            "tokens_per_caught_lower": False}}))

    def test_fewer_repeats_among_findings_alone_is_observed_and_does_not_hold(self):
        first = self.before()
        self.under(5, {"findings": [finding(1, A.CAUGHT, "t", repeat_of=first + "#1"),
                                    *(finding(n, A.FALSE_ALARM, "why") for n in (2, 3, 4))], "tokens": 9000})
        self.assertEqual(self.state("improves"), ("refuted", {"one": {
            "state": "refuted", "sessions": 5, "caught_per_run_higher": False, "repeats_lower": True,
            "tokens_per_caught_lower": False}}))

    def test_tokens_per_caught_are_of_the_runs_whose_tokens_are_known(self):
        first = self.before()
        self.old_run(run_file(old_finding(1, A.CAUGHT, "t"), tokens=None, not_measured="none shown"))
        self.under(5, {"findings": [finding(1, A.CAUGHT, "t", repeat_of=first + "#1")], "tokens": 1000})
        self.assertEqual(self.state("improves"), ("held", {"one": {
            "state": "held", "sessions": 5, "caught_per_run_higher": False, "repeats_lower": False,
            "tokens_per_caught_lower": True}}))

    def test_more_caught_findings_a_run_holds(self):
        first = self.before()
        self.under(5, {"findings": [finding(n, A.CAUGHT, "t", repeat_of=first + "#1") for n in (1, 2)],
                       "tokens": 2400})
        self.assertEqual(self.state("improves"), ("held", {"one": {
            "state": "held", "sessions": 5, "caught_per_run_higher": True, "repeats_lower": False,
            "tokens_per_caught_lower": False}}))

    def test_fewer_tokens_per_caught_finding_holds(self):
        first = self.before()
        self.under(5, {"findings": [finding(1, A.CAUGHT, "t", repeat_of=first + "#1")], "tokens": 1199})
        self.assertEqual(self.state("improves"), ("held", {"one": {
            "state": "held", "sessions": 5, "caught_per_run_higher": False, "repeats_lower": False,
            "tokens_per_caught_lower": True}}))

    def test_a_side_with_no_finding_or_nothing_caught_shows_no_improvement(self):
        self.under(5, {"findings": [finding(1, A.CAUGHT, "t")], "tokens": 1})
        self.assertEqual(self.state("improves"), ("refuted", {"one": {
            "state": "refuted", "sessions": 5, "caught_per_run_higher": False, "repeats_lower": False,
            "tokens_per_caught_lower": False}}))
        self.data = b""
        self.row("session_start")
        self.before()
        self.under(5, {"findings": [], "tokens": 1})
        self.assertEqual(self.state("improves")[0], "refuted")
        self.assertFalse(R._lower(0, 0, 1, 2) or R._lower(0, 2, 1, 0))
        self.assertTrue(R._lower(1, 3, 1, 2) and not R._lower(1, 2, 2, 4))


class Main(Base):
    def main(self, *argv: str, logs: str | None = None) -> tuple[int, dict]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = R.main(["--ledger", self.ledger, *argv], root=self.root, logs=logs or os.path.join(self.tmp, "no"))
        lines = buf.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        return code, json.loads(lines[0])

    def test_each_rule_with_its_state_and_exit_0_when_none_is_refuted(self):
        code, out = self.main()
        self.assertEqual((code, out["ok"]), (0, True))
        self.assertEqual([(r["id"], r["check"]) for r in out["rules"]], [("rule-" + c, c) for c in R.CHECKS])
        self.assertEqual({r["check"]: r["state"] for r in out["rules"]}, {
            "definitions": "held", "calls_are_rows": "not_due", "no_unjudged_left": "held",
            "repeats_rare": "not_due", "earns": "not_due", "improves": "not_due"})
        self.assertEqual(out["rules"], R.judge(self.root, self.data, None))

    def test_a_refuted_rule_is_exit_1(self):
        self.agent(GOOD.replace(b"Read, Grep", b"Read, Bash"))
        code, out = self.main()
        self.assertEqual((code, out["ok"], [r["state"] for r in out["rules"] if r["state"] == "refuted"]),
                         (1, False, ["refuted"]))

    def test_the_log_is_the_one_named_or_the_newest_of_the_logs_or_none(self):
        logs = os.path.join(self.tmp, "logs")
        os.mkdir(logs)
        state = lambda *argv: {r["check"]: r["state"] for r in self.main(*argv, logs=logs)[1]["rules"]}[  # noqa: E731
            "calls_are_rows"]
        self.assertEqual(state(), "not_due")
        self.put(os.path.join("logs", "session-20261122T010000Z.jsonl"), json.dumps(call()).encode() + b"\n")
        self.put(os.path.join("logs", "session-20261122T020000Z.err"), b"x")
        self.put(os.path.join("logs", "loop-runs.jsonl"), b"x")
        self.put(os.path.join("logs", "terminal.jsonl"), b"x")
        self.assertEqual(state(), "refuted")
        self.put(os.path.join("logs", "session-20261122T020000Z.jsonl"), b"")
        self.assertEqual(state(), "held")
        self.assertEqual(state("--log", os.path.join(logs, "session-20261122T010000Z.jsonl")), "refuted")
        self.assertEqual(state("--log", os.path.join(logs, "session-20261122T010000Z.jsonl"), "--no-log"), "not_due")
        self.assertEqual(R.LOGS, "/work/logs")

    def test_a_fault_is_exit_2_with_its_reason(self):
        self.assertEqual(self.main("--log", os.path.join(self.tmp, "absent")),
                         (2, {"ok": False, "reason": "log_unreadable"}))
        with open(self.ledger, "ab") as f:
            f.write(b"not a row\n")
        self.assertEqual(self.main(), (2, {"ok": False, "reason": "ledger_unreadable"}))
        self.assertEqual(self.main("--ledger", os.path.join(self.tmp, "absent")),
                         (2, {"ok": False, "reason": "ledger_unreadable"}))
        os.remove(os.path.join(self.root, A.RULES))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = R.main(["--ledger", os.devnull], root=self.root, logs=self.tmp)
        self.assertEqual((code, json.loads(buf.getvalue())), (2, {"ok": False, "reason": "rules_unreadable"}))


class Brain(unittest.TestCase):
    """The rules this brain keeps, and the skill that is their order of work."""

    def test_the_rules_file_is_read_and_every_check_has_its_rule(self):
        rules = R.load(ROOT)
        self.assertEqual(sorted(r["check"] for r in rules), sorted(R.CHECKS))

    def test_the_rules_are_judged_on_the_brains_own_ledger_without_a_fault(self):
        with open(os.path.join(ROOT, A.LEDGER), "rb") as f:
            got = R.judge(ROOT, f.read(), None)
        self.assertEqual([r["id"] for r in got], [r["id"] for r in R.load(ROOT)])
        for r in got:
            self.assertIn(r["state"], (R.HELD, R.REFUTED, R.NOT_DUE), r)
        self.assertEqual({r["check"]: r["state"] for r in got}["definitions"], R.HELD)

    def test_the_skill_names_every_rule_and_the_commands_of_a_run(self):
        with open(os.path.join(ROOT, "skills", "agents", "SKILL.md"), "rb") as f:
            fields, body = A.front_matter(f.read(), A.SKILL_KEYS)
        self.assertEqual(fields["name"], "agents")
        text = " ".join(body.split())
        for r in R.load(ROOT):
            self.assertIn("`%s`" % r["id"], text)
        for named in ("skills/agents/rules.json", "python3 tests/agent_rules.py",
                      "python3 tests/agent_run.py packet --agent <name> --base <last accepted SHA> --head",
                      "the type `brain:<name>`, a stated effort, and the bytes of the packet's `message.txt` as the "
                      "whole prompt, nothing added",
                      "python3 tests/agent_run.py record --packet", "python3 tests/agent_run.py record --agent <name>",
                      "python3 tests/agent_run.py measure --agent <name>", "stands in for none",
                      *("`%s`" % v for v in A.VERDICTS2), "`carried_in`", "`repeat_of`", "`session_start`"):
            self.assertIn(named, text)


if __name__ == "__main__":
    unittest.main()
