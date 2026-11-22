"""``tests/agent_run.py``'s rules, each bound by a test below (the rules are listed in its docstring, the one
source), and the form of every agent this brain defines. No git is needed: the fake ``git`` is
``test_push_size``'s. Run from the brain's root."""

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

import agent_run as A  # noqa: E402
import test_push_size as TP  # noqa: E402

F = A.F
SNAPSHOT = "a" * 40
TS = "2026-11-22T13:00:00Z"
GOOD = b"---\nname: one\ndescription: Reads a thing.\ntools: Read, Grep\nmodel: opus\n---\nOrigin. A gap.\n"


def finding(n: int, verdict: str = A.UNJUDGED, evidence=None) -> dict:
    return {"n": n, "class": "promise", "claim": "a claim", "ref": "a.py:3", "verdict": verdict,
            "evidence": evidence}


def run_file(*findings: dict, **over) -> dict:
    run = {"invoked_as": "brain:one", "model_served": "claude-opus-5-5", "effort": "medium", "tokens": 1200,
           "cost_usd_micros": 340000, "wall_ms": 90000, "not_measured": None, "findings": list(findings)}
    run.update(over)
    return run


class Base(TP.Base):
    def setUp(self):
        super().setUp()
        self.root = os.path.join(self.tmp, "root")
        os.makedirs(os.path.join(self.root, "agents"))
        self.agent(GOOD)
        self.out = os.path.join(self.tmp, "packet")
        self.ledger = os.path.join(self.tmp, "ledger.jsonl")
        self.data = b""
        self.row("session_start")

    def agent(self, data: bytes, name: str = "one") -> None:
        with open(os.path.join(self.root, "agents", name + ".md"), "wb") as f:
            f.write(data)

    def row(self, kind: str, summary: str = "a row of the test", refs=("tests/agent_run.py",)) -> str:
        row = F.next_row(self.data, kind, summary, list(refs), SNAPSHOT, TS)
        self.data += F.line_of(row)
        with open(self.ledger, "wb") as f:
            f.write(self.data)
        return row["row_id"]

    def packet(self) -> dict:
        return A.packet(self.root, "one", "BASE", "HEAD", self.out, self.git)

    def record(self, run: dict) -> str:
        if not os.path.isdir(self.out):
            self.packet()
        row_id = A.record(A.read_packet(self.out), run, self.ledger, SNAPSHOT, TS, F.spec_kinds())
        with open(self.ledger, "rb") as f:
            self.data = f.read()
        return row_id

    def faults(self, reason: str):
        return self.assertRaisesRegex(A.Fault, "^%s$" % reason)


class FrontMatter(unittest.TestCase):
    def test_the_fields_and_the_text_after_them(self):
        fields, body = A.front_matter(GOOD, A.AGENT_KEYS)
        self.assertEqual(fields, {"name": "one", "description": "Reads a thing.", "tools": "Read, Grep",
                                  "model": "opus"})
        self.assertEqual(body, "Origin. A gap.\n")

    def test_a_blank_line_is_no_field_and_crlf_is_read_as_lf(self):
        fields, _ = A.front_matter(b"---\r\nname: one\r\n\r\ndescription: d: e\r\n---\r\ntext\r\n", A.SKILL_KEYS)
        self.assertEqual(fields, {"name": "one", "description": "d: e"})

    def test_each_break_of_the_form_is_a_fault(self):
        for data, reason in (
                (b"name: one\n---\ntext\n", "no_front_matter"),
                (b"---\nname: one\ntext\n", "no_front_matter"),
                (b"---\nname one\n---\ntext\n", "bad_line"),
                (b"---\nname:   \n---\ntext\n", "bad_line"),
                (b"---\nname: one\nhooks: x\n---\ntext\n", "unknown_key:hooks"),
                (b"---\nname: one\nmodel: opus\n---\ntext\n", "unknown_key:model"),
                (b"---\nname: one\nname: two\n---\ntext\n", "repeated_key:name"),
                (b"---\nname: \"one\"\n---\ntext\n", "quoted_value:name"),
                (b"---\nname: 'one'\n---\ntext\n", "quoted_value:name"),
                (b"---\nname: one\n---\n \n\n", "empty_body"),
                (b"---\nname: \xff\n---\ntext\n", "not_utf8")):
            with self.subTest(data=data), self.assertRaisesRegex(A.Fault, "^%s$" % reason):
                A.front_matter(data, A.SKILL_KEYS)


class Definition(Base):
    def test_the_fields_and_the_sha256_of_the_files_bytes(self):
        self.assertEqual(A.definition(self.root, "one"), {
            "name": "one", "model": "opus", "tools": ["Read", "Grep"], "sha256": hashlib.sha256(GOOD).hexdigest()})

    def test_without_tools_the_tools_are_none(self):
        self.agent(GOOD.replace(b"tools: Read, Grep\n", b""))
        self.assertIsNone(A.definition(self.root, "one")["tools"])

    def test_each_break_is_a_fault(self):
        for old, new, reason in ((b"name: one", b"name: two", "name_is_not_the_files"),
                                 (b"name: one\n", b"", "no_name"),
                                 (b"description: Reads a thing.\n", b"", "no_description"),
                                 (b"model: opus\n", b"", "no_model"),
                                 (b"model: opus", b"model: haiku", "model_not_allowed"),
                                 (b"model: opus", b"model: claude-opus-5-5", "model_not_allowed"),
                                 (b"Read, Grep", b"Read,, Grep", "empty_tool")):
            self.agent(GOOD.replace(old, new))
            with self.subTest(reason=reason), self.faults(reason):
                A.definition(self.root, "one")
        with self.faults("no_definition"):
            A.definition(self.root, "absent")

    def test_sonnet_is_the_other_model(self):
        self.agent(GOOD.replace(b"model: opus", b"model: sonnet"))
        self.assertEqual(A.definition(self.root, "one")["model"], "sonnet")


class Packet(Base):
    def test_the_three_files_hold_the_diff_the_paths_and_the_record(self):
        doc = self.packet()
        with open(os.path.join(self.tmp, "diff"), "rb") as f:
            diff = f.read()
        self.assertEqual(doc, {
            "agent": "one", "model": "opus", "tools": ["Read", "Grep"],
            "definition_sha256": hashlib.sha256(GOOD).hexdigest(), "base": "BASE", "head": "HEAD",
            "diff_sha256": hashlib.sha256(diff).hexdigest(), "bytes": len(diff), "files": 2})
        self.assertEqual(sorted(os.listdir(self.out)), ["diff.patch", "packet.json", "paths.txt"])
        with open(os.path.join(self.out, "diff.patch"), "rb") as f:
            self.assertEqual(f.read(), diff)
        with open(os.path.join(self.out, "paths.txt"), "rb") as f:
            self.assertEqual(f.read(), b"a.py\nb/c.py\n")
        with open(os.path.join(self.out, "packet.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f), doc)

    def test_the_diff_is_push_sizes_with_its_exclusion(self):
        self.packet()
        spec = ["--", "."] + [":(top,exclude)" + name for name in A.PS.EXCLUDED]
        common = ["-C", self.root, *A.PS.DIFF]
        self.assertEqual(self.argv(), [common + ["BASE", "HEAD"] + spec,
                                       common + ["--name-only", "-z", "BASE", "HEAD"] + spec])
        self.assertIn("founder-ledger.jsonl", A.PS.EXCLUDED)

    def test_out_inside_the_brain_or_holding_something_is_refused_and_nothing_is_written(self):
        link = os.path.join(self.tmp, "link")
        os.symlink(self.root, link)
        for out in (self.root, os.path.join(self.root, "x", "y"), os.path.join(link, "p")):
            with self.subTest(out=out), self.faults("out_inside_brain"):
                A.packet(self.root, "one", "B", "H", out, self.git)
        self.assertEqual(sorted(os.listdir(self.root)), ["agents"])
        os.mkdir(self.out)
        self.put(os.path.join("packet", "kept"), b"x")
        with self.faults("out_not_empty"):
            self.packet()
        self.assertEqual(os.listdir(self.out), ["kept"])
        file = self.put("a-file", b"")
        with self.faults("out_not_empty"):
            A.packet(self.root, "one", "B", "H", file, self.git)

    def test_an_empty_directory_is_taken(self):
        os.mkdir(self.out)
        self.packet()
        self.assertIn("packet.json", os.listdir(self.out))

    def test_a_git_that_fails_and_a_broken_definition_write_nothing(self):
        self.put("code", b"128")
        with self.faults("diff_failed:128"):
            self.packet()
        self.put("code", b"0")
        self.agent(GOOD.replace(b"model: opus", b"model: haiku"))
        with self.faults("model_not_allowed"):
            self.packet()
        self.assertFalse(os.path.exists(self.out))


class Record(Base):
    def test_the_row_carries_the_packet_and_the_run(self):
        run = run_file(finding(1, A.CAUGHT, "test_x was red at 1111111, green at 2222222"),
                       finding(2, A.FALSE_ALARM, "the page says at most, the code keeps it"), finding(3))
        row_id = self.record(run)
        row = json.loads(self.data.splitlines()[-1])
        self.assertEqual((row["row_id"], row["kind"], row["part"], row["derivation"], row["trust"]),
                         (row_id, "build", "founder", "llm_inference", "inferred"))
        self.assertEqual(row["payload"]["refs"], ["agents/one.md", "agent_run:one"])
        text = row["payload"]["summary"]
        self.assertTrue(text.startswith("agent_run/1 {"))
        pack = A.read_packet(self.out)
        del pack["tools"]
        self.assertEqual(json.loads(text[len("agent_run/1 "):]), {**pack, **run})
        self.assertEqual(F.problems(self.data, F.spec_kinds()), [])

    def test_the_row_names_the_definitions_model_and_the_one_served_and_no_field_hides_another(self):
        self.record(run_file())
        fields = json.loads(json.loads(self.data.splitlines()[-1])["payload"]["summary"][len(A.FORM):])
        self.assertEqual((fields["model"], fields["model_served"]), ("opus", "claude-opus-5-5"))
        self.assertEqual(set(A.PACKET_KEYS) & (set(A.RUN_KEYS) | {"amends"}), set())

    def test_an_amending_run_that_names_no_earlier_run_of_the_agent_is_refused_and_the_ledger_is_left(self):
        start = json.loads(self.data.splitlines()[0])["row_id"]
        self.agent(GOOD.replace(b"name: one", b"name: two"), "two")
        A.packet(self.root, "two", "BASE", "HEAD", self.out + "2", self.git)
        other = A.record(A.read_packet(self.out + "2"), run_file(), self.ledger, SNAPSHOT, TS, F.spec_kinds())
        with open(self.ledger, "rb") as f:
            before = self.data = f.read()
        for name in (start, other, "f999"):
            with self.subTest(name=name), self.faults("amends_no_run"):
                self.record(run_file(amends=name))
        with open(self.ledger, "rb") as f:
            self.assertEqual(f.read(), before)

    def test_a_ledger_whose_run_rows_cannot_be_read_takes_no_further_run(self):
        row = F.next_row(self.data, "build", "a note", ["agent_run:one"], SNAPSHOT, TS)
        self.data += F.line_of(row)
        with open(self.ledger, "wb") as f:
            f.write(self.data)
        with self.faults("run_row_unreadable:%s" % row["row_id"]):
            self.record(run_file())

    def test_a_diff_that_is_no_longer_the_packets_is_refused(self):
        self.packet()
        with open(os.path.join(self.out, "diff.patch"), "ab") as f:
            f.write(b"+more\n")
        with self.faults("diff_changed"):
            A.read_packet(self.out)

    def test_a_packet_that_cannot_be_read_is_refused(self):
        with self.faults("packet_unreadable"):
            A.read_packet(self.out)
        self.packet()
        path = os.path.join(self.out, "packet.json")
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        for broken in ([doc], {**doc, "more": 1}, {k: v for k, v in doc.items() if k != "head"}):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(broken, f)
            with self.subTest(broken=broken), self.faults("packet_unreadable"):
                A.read_packet(self.out)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f)
        os.remove(os.path.join(self.out, "diff.patch"))
        with self.faults("packet_unreadable"):
            A.read_packet(self.out)

    def test_each_break_of_the_run_file_is_refused_and_the_ledger_is_left(self):
        good = finding(1)
        before = self.data
        for run, reason in (
                (run_file(more=1), "run_keys:more"),
                ({k: v for k, v in run_file().items() if k != "wall_ms"}, "run_keys:wall_ms"),
                (run_file(invoked_as=""), "bad_run_field"),
                (run_file(model_served=None), "bad_run_field"),
                (run_file(wall_ms=None), "bad_run_field"),
                (run_file(wall_ms=-1), "bad_run_field"),
                (run_file(wall_ms=True), "bad_run_field"),
                (run_file(effort=3, not_measured="x"), "bad_run_field"),
                (run_file(tokens="12"), "bad_run_field"),
                (run_file(cost_usd_micros=1.5), "bad_run_field"),
                (run_file(not_measured=" "), "bad_run_field"),
                (run_file(effort=None), "unknown_without_reason"),
                (run_file(tokens=None), "unknown_without_reason"),
                (run_file(cost_usd_micros=None), "unknown_without_reason"),
                (run_file(amends="1912"), "bad_amends"),
                (run_file(amends=None), "bad_amends"),
                (run_file(findings={}), "findings_not_a_list"),
                (run_file(finding(2)), "bad_finding:1"),
                (run_file(good, finding(3)), "bad_finding:2"),
                (run_file({**good, "n": True}), "bad_finding:1"),
                (run_file({**good, "n": 1.0}), "bad_finding:1"),
                (run_file({**good, "more": 1}), "bad_finding:1"),
                (run_file({k: v for k, v in good.items() if k != "ref"}), "bad_finding:1"),
                (run_file({**good, "class": ""}), "bad_finding:1"),
                (run_file({**good, "claim": None}), "bad_finding:1"),
                (run_file({**good, "ref": ""}), "bad_finding:1"),
                (run_file({**good, "verdict": "real"}), "bad_finding:1"),
                (run_file({**good, "verdict": "real", "evidence": "a test"}), "bad_finding:1"),
                (run_file(finding(1, A.CAUGHT)), "bad_finding:1"),
                (run_file(finding(1, A.FALSE_ALARM)), "bad_finding:1"),
                (run_file(finding(1, A.FALSE_ALARM, " ")), "bad_finding:1"),
                (run_file("a finding"), "bad_finding:1")):
            with self.subTest(reason=reason, run=run), self.faults(reason):
                self.record(run)
        with open(self.ledger, "rb") as f:
            self.assertEqual(f.read(), before)

    def test_what_may_be_unknown_is_null_with_its_reason_and_a_ref_may_be_null(self):
        self.record(run_file({**finding(1), "ref": None}, effort=None, tokens=None, cost_usd_micros=None,
                             not_measured="the tool's answer carries no cost"))
        self.assertEqual(A.measure(self.data, "one")["cost_unknown"], 1)

    def test_a_row_the_writer_refuses_and_a_ledger_it_cannot_extend_are_faults(self):
        before = self.data
        key = "AKIA" + "IOSFODNN7EXAMPLE"
        with self.assertRaisesRegex(A.Fault, "^row_refused:row_scan:"):
            self.record(run_file({**finding(1), "claim": "the key %s is in the file" % key}))
        with open(self.ledger, "rb") as f:
            self.assertEqual(f.read(), before)
        with open(self.ledger, "wb") as f:
            f.write(before + b"not a row\n")
        with self.faults("ledger_unreadable"):
            self.record(run_file())
        with open(self.ledger, "wb") as f:
            f.write(before + before)
        with self.assertRaisesRegex(A.Fault, "^ledger_unusable:"):
            self.record(run_file())
        with self.assertRaisesRegex(A.Fault, "^ledger_unusable:"):
            A.record(A.read_packet(self.out), run_file(), os.path.join(self.tmp, "absent"), SNAPSHOT, TS,
                     F.spec_kinds())


class Measure(Base):
    def test_no_run_is_all_zero_and_not_due(self):
        self.assertEqual(A.measure(self.data, "one"), {
            "ok": True, "agent": "one", "runs": 0, "sessions": 0, "findings": 0, "caught": 0, "false_alarm": 0,
            "unjudged": 0, "tokens": 0, "tokens_unknown": 0, "cost_usd_micros": 0, "cost_unknown": 0, "wall_ms": 0,
            "retire_due": False})

    def test_runs_sessions_verdicts_and_sums(self):
        self.record(run_file(finding(1, A.CAUGHT, "t"), finding(2)))
        self.record(run_file(finding(1, A.FALSE_ALARM, "why"), tokens=None, not_measured="none shown"))
        self.row("session_end")
        self.row("session_start")
        self.record(run_file(cost_usd_micros=None, not_measured="none shown", wall_ms=1))
        got = A.measure(self.data, "one")
        self.assertEqual(got, {
            "ok": True, "agent": "one", "runs": 3, "sessions": 2, "findings": 3, "caught": 1, "false_alarm": 1,
            "unjudged": 1, "tokens": 2400, "tokens_unknown": 1, "cost_usd_micros": 680000, "cost_unknown": 1,
            "wall_ms": 180001, "retire_due": False})

    def test_another_agents_rows_are_not_counted(self):
        self.agent(GOOD.replace(b"name: one", b"name: two"), "two")
        self.record(run_file(finding(1)))
        os.rename(self.out, self.out + "-one")
        row_id = A.record(A.packet(self.root, "two", "B", "H", self.out, self.git), run_file(finding(1)),
                          self.ledger, SNAPSHOT, TS, F.spec_kinds())
        with open(self.ledger, "rb") as f:
            self.data = f.read()
        self.assertEqual(json.loads(self.data.splitlines()[-1])["payload"]["refs"],
                         ["agents/two.md", "agent_run:two"])
        self.assertEqual((A.measure(self.data, "one")["runs"], A.measure(self.data, "two")["runs"]), (1, 1))
        self.assertTrue(row_id)

    def test_a_run_before_any_session_start_is_one_more_session(self):
        self.data = b""
        self.row("decision")
        self.record(run_file())
        self.row("session_start")
        self.record(run_file())
        self.assertEqual(A.measure(self.data, "one")["sessions"], 2)

    def test_an_amending_row_replaces_the_findings_of_the_run_it_names_and_is_no_run(self):
        first = self.record(run_file(finding(1), finding(2)))
        self.record(run_file(finding(1)))
        self.record(run_file(finding(1, A.CAUGHT, "the rival's reproducer of the same line"),
                             finding(2, A.FALSE_ALARM, "why"), amends=first, tokens=7, wall_ms=7))
        got = A.measure(self.data, "one")
        self.assertEqual((got["runs"], got["findings"], got["caught"], got["false_alarm"], got["unjudged"]),
                         (2, 3, 1, 1, 1))
        self.assertEqual((got["tokens"], got["wall_ms"]), (2400, 180000))

    def test_an_amending_row_that_names_no_earlier_run_is_a_fault(self):
        start = json.loads(self.data.splitlines()[0])["row_id"]
        for name in (start, "f999"):
            data = self.data
            row = F.next_row(data, "build", A.summary({"agent": "one"}, run_file(amends=name)),
                             ["agent_run:one"], SNAPSHOT, TS)
            with self.subTest(name=name), self.faults("amends_no_run:%s" % row["row_id"]):
                A.measure(data + F.line_of(row), "one")

    def test_a_tagged_row_of_another_form_is_a_fault_never_skipped(self):
        for text in ("a note about the agent", "agent_run/1 not json", "agent_run/1 [1]", "agent_run/1 {}",
                     A.FORM + json.dumps({"findings": [{"n": 1}], "tokens": 1, "cost_usd_micros": 1, "wall_ms": 1}),
                     A.FORM + json.dumps({"findings": [], "tokens": 1, "cost_usd_micros": 1}),
                     A.FORM + json.dumps({"findings": [], "tokens": "1", "cost_usd_micros": 1, "wall_ms": 1}),
                     A.FORM + json.dumps({"findings": [], "tokens": 1, "cost_usd_micros": 1.5, "wall_ms": 1}),
                     A.FORM + json.dumps({"findings": [], "tokens": 1, "cost_usd_micros": 1, "wall_ms": None}),
                     A.FORM + json.dumps({"findings": [], "tokens": 1, "cost_usd_micros": 1, "wall_ms": True})):
            row = F.next_row(self.data, "build", text, ["agent_run:one"], SNAPSHOT, TS)
            with self.subTest(text=text), self.faults("run_row_unreadable:%s" % row["row_id"]):
                A.measure(self.data + F.line_of(row), "one")

    def test_a_ledger_line_that_is_no_row_is_a_fault(self):
        for line in (b"not json\n", b"[1]\n", b'{"kind": "build"}\n'):
            with self.subTest(line=line), self.faults("ledger_unreadable"):
                A.measure(self.data + line, "one")

    def sessions(self, count: int, last: dict) -> dict:
        self.data = b""
        for i in range(count):
            self.row("session_start")
            self.record(last if i == count - 1 else run_file(finding(1, A.FALSE_ALARM, "why")))
        return A.measure(self.data, "one")

    def test_retirement_is_due_at_five_sessions_with_nothing_caught(self):
        self.assertEqual(A.RETIRE_AFTER, 5)
        four = self.sessions(4, run_file(finding(1)))
        self.assertEqual((four["sessions"], four["caught"], four["retire_due"]), (4, 0, False))
        five = self.sessions(5, run_file(finding(1)))
        self.assertEqual((five["sessions"], five["caught"], five["retire_due"]), (5, 0, True))
        caught = self.sessions(5, run_file(finding(1, A.CAUGHT, "t")))
        self.assertEqual((caught["sessions"], caught["caught"], caught["retire_due"]), (5, 1, False))


class Main(Base):
    def main(self, *argv: str) -> tuple[int, dict]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = A.main(list(argv), root=self.root, git=self.git)
        lines = buf.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        return code, json.loads(lines[0])

    def test_packet_record_measure(self):
        code, out = self.main("packet", "--agent", "one", "--base", "B", "--out", self.out)
        self.assertEqual((code, out["ok"], out["head"], out["out"]), (0, True, "HEAD", self.out))
        run = self.put("run.json", json.dumps(run_file(finding(1))).encode())
        code, out = self.main("record", "--packet", self.out, "--run", run, "--snapshot", SNAPSHOT, "--ts", TS,
                              "--ledger", self.ledger)
        self.assertEqual((code, out), (0, {"ok": True, "recorded": "f2"}))
        code, out = self.main("measure", "--agent", "one", "--ledger", self.ledger)
        self.assertEqual((code, out["runs"], out["unjudged"]), (0, 1, 1))

    def test_the_default_ledger_is_the_roots(self):
        os.replace(self.ledger, os.path.join(self.root, "founder-ledger.jsonl"))
        self.assertEqual(self.main("measure", "--agent", "one"), (0, A.measure(self.data, "one")))

    def test_a_fault_is_exit_2_with_its_reason(self):
        self.assertEqual(self.main("packet", "--agent", "absent", "--base", "B", "--out", self.out),
                         (2, {"ok": False, "reason": "no_definition"}))
        self.packet()
        for text in (b"not json", b"[1]"):
            run = self.put("run.json", text)
            self.assertEqual(self.main("record", "--packet", self.out, "--run", run, "--snapshot", SNAPSHOT,
                                       "--ledger", self.ledger), (2, {"ok": False, "reason": "run_unreadable"}))
        self.assertEqual(self.main("measure", "--agent", "one", "--ledger", os.path.join(self.tmp, "absent")),
                         (2, {"ok": False, "reason": "ledger_unreadable"}))


class Brain(unittest.TestCase):
    """The agents this brain defines, read by rule 2, and what this brain promises of the first one."""

    def names(self) -> list[str]:
        return sorted(n[:-3] for n in os.listdir(os.path.join(ROOT, "agents")))

    def test_every_file_of_agents_is_a_definition_whose_text_starts_with_its_origin(self):
        self.assertIn("push-reviewer", self.names())
        for name in self.names():
            with self.subTest(agent=name):
                A.definition(ROOT, name)
                with open(os.path.join(ROOT, "agents", name + ".md"), "rb") as f:
                    _, body = A.front_matter(f.read(), A.AGENT_KEYS)
                self.assertTrue(body.startswith("Origin. Gap: "), body[:40])
                self.assertIn("Measure: ", body)

    def test_the_push_reviewer_reads_and_cannot_write_and_is_not_the_model_that_writes_referee_code(self):
        agent = A.definition(ROOT, "push-reviewer")
        self.assertEqual(agent["tools"], ["Read", "Grep", "Glob"])
        self.assertEqual(agent["model"], "opus")

    def test_the_push_reviewers_text_names_what_the_packet_holds_and_the_fold_that_measures_it(self):
        with open(os.path.join(ROOT, "agents", "push-reviewer.md"), "rb") as f:
            _, body = A.front_matter(f.read(), A.AGENT_KEYS)
        for named in ("diff.patch", "paths.txt", "packet.json", "tests/agent_run.py record",
                      "tests/agent_run.py measure", "docs/map/brain.md", *A.VERDICTS):
            self.assertIn(named, body)
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "docs", "map", "brain.md")))

    def test_the_push_skill_names_the_agent_and_the_two_commands_of_its_step(self):
        with open(os.path.join(ROOT, "skills", "push", "SKILL.md"), encoding="utf-8") as f:
            text = f.read()
        for named in ("python3 tests/agent_run.py packet --agent push-reviewer --base <last accepted SHA> --head "
                      "<that commit's SHA> --out",
                      "start the agent `brain:push-reviewer` with effort `high`", "python3 tests/agent_run.py record --packet",
                      "stands in for none", *("`%s`" % v for v in A.VERDICTS)):
            self.assertIn(named, " ".join(text.split()))


if __name__ == "__main__":
    unittest.main()
