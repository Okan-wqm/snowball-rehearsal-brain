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
            json.dump({"schema": "agent_rules/2", "designs": [], "rules": rules, **over}, f)

    def outcome(self, run: str, *missed: dict, verdict: str | None = None, **over) -> str:
        """The outcome row of ``run``: rejected with ``missed``, accepted with none, or ``verdict``."""
        row_id = A.outcome("one", TA.answer(run, verdict or (A.REJECTED if missed else A.ACCEPTED), *missed, **over),
                           self.ledger, TA.SNAPSHOT, TA.TS, TA.F.spec_kinds(), self.index)
        self.read()
        return row_id

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
        doc = {"schema": "agent_rules/2", "designs": [], "rules": rules}
        for text in (b"not json", b"[1]", b"{}", json.dumps({**doc, "schema": "agent_rules/1"}).encode(),
                     json.dumps({"schema": "agent_rules/2", "rules": rules}).encode(),
                     json.dumps({**doc, "rules": {}}).encode(), json.dumps({**doc, "more": 1}).encode()):
            with open(path, "wb") as f:
                f.write(text)
            with self.subTest(text=text), self.faults("rules_unreadable"):
                R.load(self.root)
        os.remove(path)
        with self.faults("rules_unreadable"):
            R.load(self.root)
        for designs in ({}, [TA.design(2, "a" * 64)]):
            self.write_rules(rules, designs=designs)
            with self.subTest(designs=designs), self.faults("bad_design"):
                R.load(self.root)
        self.write_rules(rules, designs=[TA.design(1, "a" * 64)])
        self.assertEqual(R.load(self.root), rules)
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

    def test_the_checks_are_these_seven(self):
        self.assertEqual(sorted(R.CHECKS), ["calls_are_rows", "definitions", "earns", "improves", "no_unjudged_left",
                                            "outcomes_known", "repeats_rare"])


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


class OutcomesKnown(Base):
    def test_a_run_of_an_earlier_session_without_its_outcome_refutes(self):
        self.assertEqual(self.state("outcomes_known"), ("not_due", {"runs": 0, "unanswered": [], "unlearned": []}))
        old = self.old_run(run_file(old_finding(1, A.CAUGHT, "t")))
        run = self.run_under()
        self.assertEqual(self.state("outcomes_known"), ("not_due", {"runs": 0, "unanswered": [], "unlearned": []}))
        self.row("session_start")
        self.assertEqual(self.state("outcomes_known"),
                         ("refuted", {"runs": 2, "unanswered": [old, run], "unlearned": []}))
        self.outcome(old, verdict=A.UNKNOWN, head=None)
        self.assertEqual(self.state("outcomes_known"), ("refuted", {"runs": 2, "unanswered": [run], "unlearned": []}))
        self.outcome(run)
        self.assertEqual(self.state("outcomes_known"), ("held", {"runs": 2, "unanswered": [], "unlearned": []}))
        self.run_under()
        self.assertEqual(self.state("outcomes_known"), ("held", {"runs": 2, "unanswered": [], "unlearned": []}))

    def test_a_miss_that_was_in_the_runs_diff_names_its_lesson(self):
        run = self.run_under()
        self.row("session_start")
        self.outcome(run, TA.miss(False))
        self.assertEqual(self.state("outcomes_known"), ("held", {"runs": 1, "unanswered": [], "unlearned": []}))
        self.outcome(run, TA.miss(False), TA.miss(True))
        self.assertEqual(self.state("outcomes_known"), ("refuted", {"runs": 1, "unanswered": [], "unlearned": [run]}))
        lesson = self.row("lesson", "what was missed", recheck="true")
        self.outcome(run, TA.miss(False), TA.miss(True, lesson))
        self.assertEqual(self.state("outcomes_known"), ("held", {"runs": 1, "unanswered": [], "unlearned": []}))

    def test_a_run_of_no_session_and_a_run_of_a_removed_agent_are_listed(self):
        self.data = b""
        self.row("decision")
        run = self.run_under()
        self.assertEqual(self.state("outcomes_known"), ("refuted", {"runs": 1, "unanswered": [run], "unlearned": []}))
        self.row("session_start")
        os.remove(os.path.join(self.root, "agents", "one.md"))
        self.assertEqual(self.state("outcomes_known"), ("refuted", {"runs": 1, "unanswered": [run], "unlearned": []}))


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
    """The design in force is the runs under the rules, the one before it the runs before them, unless the rules
    file closes a design."""

    def before(self, *missed: dict, caught: int = 2, refused: int = 2) -> str:
        """Before the rules: one run of 1200 tokens with its outcome."""
        run = self.old_run(run_file(*(old_finding(n, A.CAUGHT if n <= caught else A.FALSE_ALARM, "t")
                                      for n in range(1, caught + refused + 1))))
        self.row("session_start")
        self.outcome(run, *missed)
        return run

    def under(self, sessions: int, caught: int = 1, refused: int = 1, missed=(), tokens: int = 1200) -> None:
        """``sessions`` sessions, each with one run, each run answered in the session after its own; the first
        carries ``missed``. The ledger ends in a session with no run."""
        self.row("session_start")
        for i in range(sessions):
            run = self.run_under(*(finding(n, A.CAUGHT if n <= caught else A.FALSE_ALARM, "t")
                                   for n in range(1, caught + refused + 1)), tokens=tokens)
            self.row("session_start")
            self.outcome(run, *(missed if i == 0 else ()))

    def seen(self, sessions: int = 5, **true) -> dict:
        return {"one": {"state": self.state("improves")[0], "design": 1, "against": 0, "sessions": sessions,
                        "missed_share_higher": False, "missed_share_lower": False, "useful_share_higher": False,
                        "tokens_per_caught_lower": False, **true}}

    def test_before_five_sessions_with_an_answered_run_it_is_not_due(self):
        self.assertEqual(R.AFTER_SESSIONS, 5)
        self.before(TA.miss())
        self.under(4)
        self.assertEqual(self.state("improves"), ("not_due", self.seen(4, missed_share_lower=True)))
        run = self.run_under()
        self.assertEqual(self.state("improves")[0], "not_due")
        self.row("session_start")
        self.outcome(run, verdict=A.UNKNOWN)
        self.assertEqual(self.state("improves"), ("not_due", self.seen(4, missed_share_lower=True)))
        self.outcome(run)
        self.assertEqual(self.state("improves"), ("held", self.seen(5, missed_share_lower=True)))

    def test_at_five_sessions_nothing_better_refutes(self):
        self.before()
        self.under(5)
        self.assertEqual(self.state("improves"), ("refuted", self.seen()))

    def test_more_caught_a_run_and_fewer_tokens_per_caught_are_observed_and_do_not_hold(self):
        self.before()
        self.under(5, caught=3, refused=3, tokens=100)
        self.assertEqual(self.state("improves"), ("refuted", self.seen(tokens_per_caught_lower=True)))

    def test_a_higher_share_of_caught_among_the_findings_holds(self):
        self.before()
        self.under(5, caught=2, refused=1)
        self.assertEqual(self.state("improves"), ("held", self.seen(useful_share_higher=True)))

    def test_a_lower_share_of_missed_holds(self):
        self.before(TA.miss())
        self.under(5, missed=[TA.miss()])
        self.assertEqual(self.state("improves"), ("held", self.seen(missed_share_lower=True)))

    def test_a_higher_share_of_missed_refutes_whatever_else_is_better(self):
        self.before(TA.miss())
        self.under(5, caught=1, refused=0, missed=[TA.miss()] * 3, tokens=100)
        self.assertEqual(self.state("improves"), ("refuted", self.seen(
            missed_share_higher=True, useful_share_higher=True, tokens_per_caught_lower=True)))

    def test_the_missed_share_is_among_the_caught_of_the_judged_runs_alone(self):
        self.before(TA.miss())
        self.under(5, missed=[TA.miss()] * 3)
        seen = self.seen(missed_share_higher=True)
        self.assertEqual(self.state("improves"), ("refuted", seen))
        self.run_under(*(finding(n, A.CAUGHT, "t") for n in range(1, 6)))
        self.assertEqual(self.state("improves"), ("refuted", {"one": {**seen["one"], "useful_share_higher": True}}))

    def test_tokens_per_caught_are_of_the_runs_whose_tokens_are_known(self):
        self.old_run(run_file(*(old_finding(n, A.CAUGHT, "t") for n in range(1, 6)), tokens=None))
        self.before(caught=1, refused=1)
        self.under(5, tokens=600)
        self.assertEqual(self.state("improves"), ("refuted", self.seen(tokens_per_caught_lower=True)))

    def test_a_miss_that_was_not_in_the_runs_diff_is_no_miss_of_the_run(self):
        self.before()
        self.under(5, caught=2, refused=1, missed=[TA.miss(False)])
        self.assertEqual(self.state("improves"), ("held", self.seen(useful_share_higher=True)))
        self.data = b""
        self.row("session_start")
        self.before()
        self.under(5, caught=2, refused=1, missed=[TA.miss(True)])
        self.assertEqual(self.state("improves")[0], "refuted")

    def test_the_missed_share_is_of_the_runs_a_judge_answered(self):
        old = self.before(TA.miss())
        self.under(5)
        self.outcome(old, verdict=A.UNKNOWN)
        self.assertEqual(self.state("improves"), ("refuted", self.seen()))

    def test_a_side_with_nothing_to_divide_by_shows_no_improvement(self):
        self.under(5, caught=1, refused=0)
        self.assertEqual(self.state("improves"), ("refuted", self.seen()))
        self.data = b""
        self.row("session_start")
        self.before(TA.miss())
        self.under(5, caught=0, refused=0)
        self.assertEqual(self.state("improves"), ("refuted", self.seen()))
        self.assertFalse(R._lower(0, 0, 1, 2) or R._lower(0, 2, 1, 0))
        self.assertTrue(R._lower(1, 3, 1, 2) and not R._lower(1, 2, 2, 4))

    def test_a_closed_design_is_what_the_design_in_force_is_judged_against(self):
        self.before(caught=1, refused=9)
        rules = [rule(check) for check in R.CHECKS]
        self.under(1)
        with open(os.path.join(self.root, A.RULES), "rb") as f:
            first = hashlib.sha256(f.read()).hexdigest()
        self.write_rules(rules, designs=[TA.design(1, first)])
        self.assertEqual(self.state("improves"), ("not_due", {"one": {
            "state": "not_due", "design": 2, "against": 1, "sessions": 0, "missed_share_higher": False,
            "missed_share_lower": False, "useful_share_higher": False, "tokens_per_caught_lower": False}}))
        self.under(5)
        self.assertEqual(self.state("improves"), ("refuted", {"one": {
            "state": "refuted", "design": 2, "against": 1, "sessions": 5, "missed_share_higher": False,
            "missed_share_lower": False, "useful_share_higher": False, "tokens_per_caught_lower": False}}))
        self.write_rules(rules)
        self.assertEqual(self.state("improves"), ("held", self.seen(6, useful_share_higher=True)))

    def test_a_closed_design_names_rows_the_ledger_holds(self):
        rules = [rule(check) for check in R.CHECKS]
        self.write_rules(rules, designs=[TA.design(1, "a" * 64, recorded_in=["f1", "f2"])])
        with self.faults("design_not_recorded:1"):
            R.judge(self.root, self.data, None)
        self.row("decision")
        self.assertEqual(self.state("improves")[0], "not_due")


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
            "outcomes_known": "not_due",
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

    def test_the_first_design_is_closed_with_the_rules_files_of_its_runs_and_the_rows_that_refuted_it(self):
        (first,) = A.designs(ROOT)
        self.assertEqual(first["recorded_in"], ["f2081", "f2083", "f2094", "f2108"])
        with open(os.path.join(ROOT, A.LEDGER), "rb") as f:
            data = f.read()
        (name,) = R.tagged(data)[1]
        found = [r for r in A.runs(data, name).values() if r["ts"] < "2026-11-24T02:32:34Z"]
        self.assertEqual(sorted({r["rules_sha256"] for r in found if r["form"] == 2}), sorted(first["rules_sha256"]))
        self.assertEqual([d["runs"] for d in A.measure(data, name, [first])["designs"]][:2],
                         [sum(r["form"] == 1 for r in found), sum(r["form"] == 2 for r in found)])

    def test_the_rules_are_judged_on_the_brains_own_ledger_without_a_fault(self):
        with open(os.path.join(ROOT, A.LEDGER), "rb") as f:
            got = R.judge(ROOT, f.read(), None)
        self.assertEqual([r["id"] for r in got], [r["id"] for r in R.load(ROOT)])
        for r in got:
            self.assertIn(r["state"], (R.HELD, R.REFUTED, R.NOT_DUE), r)
        self.assertEqual({r["check"]: r["state"] for r in got}["definitions"], R.HELD)

    def test_the_rule_earns_and_the_skill_name_each_way_its_check_refutes(self):
        rule = {r["check"]: r for r in R.load(ROOT)}["earns"]
        with open(os.path.join(ROOT, "skills", "agents", "SKILL.md"), encoding="utf-8") as f:
            refuted = " ".join(f.read().split()).partition("When a rule is refuted: `earns` (")[2].partition(")")[0]
        for text in (rule["says"], rule["expects"], refuted):
            with self.subTest(text=text):
                self.assertIn("cost_over_gain", text)
        for said in ("five sessions of its runs caught nothing", "more false alarms than it catches"):
            self.assertIn(said, rule["says"])
        for said in ("five sessions with nothing caught", "more false alarms than catches"):
            self.assertIn(said, refuted)

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
                      "--run <a file with outcome_of> --snapshot", "`designs`", "`rules_sha256`",
                      *("`%s`" % k for k in A.OUTCOME_KEYS[1:]), *("`%s`" % k for k in A.MISS_KEYS),
                      *("`%s`" % v for v in A.OUTCOMES),
                      *("`%s`" % v for v in A.VERDICTS2), "`carried_in`", "`repeat_of`", "`session_start`"):
            self.assertIn(named, text)


if __name__ == "__main__":
    unittest.main()
