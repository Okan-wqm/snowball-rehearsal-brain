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


# An index that answers ``lesson_recheck``'s question with every ``lesson`` row of the ledger it is given (no row
# of these tests closes a lesson); the capsule's own index is not on the machine that runs this file.
INDEX = """import hashlib, json, sys
args = sys.argv[1:]
assert args[:-2] == %r and args[-2] == "--ledger", args
data = open(args[-1], "rb").read()
rows = [{"row_id": json.loads(line)["row_id"], "line": i} for i, line in enumerate(data.split(b"\\n")[:-1], 1)
        if json.loads(line)["kind"] == "lesson"]
print(json.dumps({"complete": True, "sha256": hashlib.sha256(data).hexdigest(), "count": len(rows),
                  "shown": len(rows), "next": None}))
for row in rows:
    print(json.dumps(row))
"""
ZERO = {"runs": 0, "sessions": 0, "findings": 0, "caught": 0, "false_alarm": 0, "unjudged": 0, "carried": 0,
        "repeats": 0, "tokens": 0, "tokens_unknown": 0, "cost_usd_micros": 0, "cost_unknown": 0, "wall_ms": 0,
        "caught_tokens_known": 0}


def old_finding(n: int, verdict: str = A.UNJUDGED, evidence=None) -> dict:
    """A finding in the form of ``agent_run/1``."""
    return {"n": n, "class": "promise", "claim": "a claim", "ref": "a.py:3", "verdict": verdict,
            "evidence": evidence}


def finding(n: int, verdict: str = A.UNJUDGED, evidence=None, carried_in=None, repeat_of=None) -> dict:
    return {**old_finding(n, verdict, evidence), "carried_in": carried_in, "repeat_of": repeat_of}


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
        os.makedirs(os.path.join(self.root, "skills", "agents"))
        self.rules = b'{"rules": "of the test"}\n'
        with open(os.path.join(self.root, A.RULES), "wb") as f:
            f.write(self.rules)
        self.agent(GOOD)
        self.loaded = self.load([{"name": "one", "model": "opus", "tools": ["Read", "Grep"], "sha256": "c" * 64},
                                 {"name": "two", "model": "opus", "tools": ["Read"], "sha256": "c" * 64}])
        self.index = self.put("index.py", (INDEX % (list(A.LR.FOLD),)).encode())
        self.out = os.path.join(self.tmp, "packet")
        self.ledger = os.path.join(self.tmp, "ledger.jsonl")
        self.data = b""
        self.row("session_start")

    def agent(self, data: bytes, name: str = "one") -> None:
        with open(os.path.join(self.root, "agents", name + ".md"), "wb") as f:
            f.write(data)

    def load(self, agents) -> str:
        return self.put("loaded.json", json.dumps({"agents": agents}).encode())

    def row(self, kind: str, summary: str = "a row of the test", refs=("tests/agent_run.py",), **more) -> str:
        row = F.next_row(self.data, kind, summary, list(refs), SNAPSHOT, TS, **more)
        self.data += F.line_of(row)
        with open(self.ledger, "wb") as f:
            f.write(self.data)
        return row["row_id"]

    def old_run(self, run: dict, name: str = "one") -> str:
        """A row of the form ``agent_run/1``, which ``record`` no longer writes."""
        return self.row("build", A.FORM + json.dumps({**PACK, "agent": name, **run}),
                        ["agents/%s.md" % name, A.TAG + name])

    def packet(self, name: str = "one", out: str | None = None) -> dict:
        return A.packet(self.root, name, "BASE", "HEAD", out or self.out, self.git, self.loaded, self.index,
                        self.ledger)

    def read(self) -> None:
        with open(self.ledger, "rb") as f:
            self.data = f.read()

    def record(self, run: dict) -> str:
        if not os.path.isdir(self.out):
            self.packet()
        row_id = A.record(A.read_packet(self.out), run, self.ledger, SNAPSHOT, TS, F.spec_kinds(), self.root)
        self.read()
        return row_id

    def amend(self, amends, *findings: dict, name: str = "one") -> str:
        row_id = A.amend(name, {"amends": amends, "findings": list(findings)}, self.ledger, SNAPSHOT, TS,
                         F.spec_kinds(), self.root)
        self.read()
        return row_id

    def given(self, file: str):
        with open(os.path.join(self.out, file), "rb") as f:
            data = f.read()
        return json.loads(data) if file.endswith(".json") else data

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
    def test_the_files_hold_the_diff_the_paths_the_lessons_the_memory_the_message_and_the_record(self):
        doc = self.packet()
        with open(os.path.join(self.tmp, "diff"), "rb") as f:
            diff = f.read()
        message = (A.MESSAGE % self.out).encode()
        self.assertEqual(doc, {
            "agent": "one", "model": "opus", "tools": ["Read", "Grep"], "definition_sha256": "c" * 64,
            "base": "BASE", "head": "HEAD", "diff_sha256": hashlib.sha256(diff).hexdigest(), "bytes": len(diff),
            "files": 2, "rules_sha256": hashlib.sha256(self.rules).hexdigest(), "lessons": 0, "memory": 0,
            "lessons_sha256": hashlib.sha256(b"[]\n").hexdigest(),
            "memory_sha256": hashlib.sha256(b"[]\n").hexdigest(),
            "message_sha256": hashlib.sha256(message).hexdigest()})
        self.assertEqual(sorted(os.listdir(self.out)), sorted([*A.GIVEN, "message.txt"]))
        self.assertEqual(self.given("diff.patch"), diff)
        self.assertEqual(self.given("paths.txt"), b"a.py\nb/c.py\n")
        self.assertEqual(self.given("message.txt"), message)
        self.assertEqual((self.given("packet.json"), self.given("lessons.json"), self.given("memory.json")),
                         (doc, [], []))

    def test_the_message_starts_with_the_directory_and_names_each_file_the_agent_is_given(self):
        os.chdir(self.tmp)
        self.addCleanup(os.chdir, ROOT)
        A.packet(self.root, "one", "BASE", "HEAD", "packet", self.git, self.loaded, self.index, self.ledger)
        lines = self.given("message.txt").decode().split("\n")
        self.assertEqual(lines[0], self.out)
        for file in A.GIVEN:
            self.assertEqual(sum(line.startswith("- %s: " % file) for line in lines), 1, file)
        self.assertIn('"repeat_of"', A.MESSAGE)

    def test_the_diff_is_push_sizes_with_its_exclusion(self):
        self.packet()
        spec = ["--", "."] + [":(top,exclude)" + name for name in A.PS.EXCLUDED]
        common = ["-C", self.root, *A.PS.DIFF]
        self.assertEqual(self.argv(), [common + ["BASE", "HEAD"] + spec,
                                       common + ["--name-only", "-z", "BASE", "HEAD"] + spec])
        self.assertIn("founder-ledger.jsonl", A.PS.EXCLUDED)

    def test_the_model_the_tools_and_the_sha256_are_the_load_records_not_the_files(self):
        self.load([{"name": "one", "model": "sonnet", "tools": ["Glob"], "sha256": "9" * 64, "path": "p"}])
        doc = self.packet()
        self.assertEqual((doc["model"], doc["tools"], doc["definition_sha256"]), ("sonnet", ["Glob"], "9" * 64))
        self.assertEqual(A.definition(self.root, "one")["model"], "opus")

    def test_an_agent_the_session_did_not_load_has_no_packet(self):
        for agents, reason in (([], "definition_not_loaded"),
                               ([{"name": "two", "model": "opus", "tools": [], "sha256": "c" * 64}],
                                "definition_not_loaded"),
                               ([{"name": "one", "model": "haiku", "tools": [], "sha256": "c" * 64}],
                                "load_record_unreadable"),
                               ([{"name": "one", "model": "opus", "tools": "Read", "sha256": "c" * 64}],
                                "load_record_unreadable"),
                               ([{"name": "one", "model": "opus", "tools": [""], "sha256": "c" * 64}],
                                "load_record_unreadable"),
                               ([{"name": "one", "model": "opus", "tools": []}], "load_record_unreadable")):
            self.load(agents)
            with self.subTest(agents=agents), self.faults(reason):
                self.packet()
        for text in (b"not json", b"[1]", b"{}", b'{"agents": 5}', b'{"agents": {"name": "one"}}'):
            self.put("loaded.json", text)
            with self.subTest(text=text), self.faults("load_record_unreadable"):
                self.packet()
        os.remove(self.loaded)
        with self.faults("load_record_unreadable"):
            self.packet()
        self.assertFalse(os.path.exists(self.out))

    def test_the_lessons_are_every_lesson_in_force_whole_and_oldest_first(self):
        long = "a lesson " + "x" * 2000
        first = self.row("lesson", long, recheck="none: a test")
        self.row("decision")
        second = self.row("lesson", "another", recheck="true")
        self.assertEqual(self.packet()["lessons"], 2)
        self.assertEqual(self.given("lessons.json"), [{"row_id": first, "summary": long},
                                                      {"row_id": second, "summary": "another"}])

    def test_without_the_index_the_rules_or_the_ledger_nothing_is_written(self):
        os.remove(self.index)
        with self.assertRaisesRegex(A.Fault, "^lessons:index_exit:[0-9]+$"):
            self.packet()
        self.index = self.put("index.py", (INDEX % (list(A.LR.FOLD),)).encode())
        os.remove(os.path.join(self.root, A.RULES))
        with self.faults("no_rules_or_ledger"):
            self.packet()
        with open(os.path.join(self.root, A.RULES), "wb") as f:
            f.write(self.rules)
        os.remove(self.ledger)
        with self.faults("no_rules_or_ledger"):
            self.packet()
        self.assertFalse(os.path.exists(self.out))

    def test_the_memory_is_each_earlier_finding_not_caught_and_no_repeat_as_last_read(self):
        self.put(os.path.join("root", "report.json"), b"{}")
        os.makedirs(os.path.join(self.root, "reports"))
        os.replace(os.path.join(self.root, "report.json"), os.path.join(self.root, "reports", "r.json"))
        old = self.old_run(run_file(old_finding(1, A.CAUGHT, "t"), old_finding(2)))
        self.old_run(run_file(old_finding(1, A.FALSE_ALARM, "of two")), "two")
        run = self.record(run_file(finding(1, A.FALSE_ALARM, "why"), finding(2, A.CAUGHT, "t"),
                                   finding(3, A.CARRIED, "true", "reports/r.json"),
                                   finding(4, repeat_of=old + "#2"), finding(5)))
        want = [{"id": old + "#2", **{k: v for k, v in old_finding(2).items() if k != "n"}},
                {"id": run + "#1", **{k: v for k, v in finding(1, A.FALSE_ALARM, "why").items() if k != "n"}},
                {"id": run + "#3",
                 **{k: v for k, v in finding(3, A.CARRIED, "true", "reports/r.json").items() if k != "n"}},
                {"id": run + "#5", **{k: v for k, v in finding(5).items() if k != "n"}}]
        self.assertEqual(A.memory(self.data, "one"), want)
        self.amend(old, finding(1, A.CAUGHT, "t"), finding(2, A.FALSE_ALARM, "read later"))
        want[0] = {"id": old + "#2", **{k: v for k, v in finding(2, A.FALSE_ALARM, "read later").items() if k != "n"}}
        self.assertEqual(A.memory(self.data, "one"), want)
        os.rename(self.out, self.out + "-first")
        self.assertEqual(self.packet()["memory"], 4)
        self.assertEqual(self.given("memory.json"), want)

    def test_out_inside_the_brain_or_holding_something_is_refused_and_nothing_is_written(self):
        link = os.path.join(self.tmp, "link")
        os.symlink(self.root, link)
        for out in (self.root, os.path.join(self.root, "x", "y"), os.path.join(link, "p")):
            with self.subTest(out=out), self.faults("out_inside_brain"):
                self.packet(out=out)
        self.assertEqual(sorted(os.listdir(self.root)), ["agents", "skills"])
        os.mkdir(self.out)
        self.put(os.path.join("packet", "kept"), b"x")
        with self.faults("out_not_empty"):
            self.packet()
        self.assertEqual(os.listdir(self.out), ["kept"])
        file = self.put("a-file", b"")
        with self.faults("out_not_empty"):
            self.packet(out=file)

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
        self.assertTrue(text.startswith("agent_run/2 {"))
        pack = A.read_packet(self.out)
        self.assertEqual(sorted(pack), sorted(A.PACKET_KEYS2))
        del pack["tools"]
        self.assertEqual(json.loads(text[len("agent_run/2 "):]), {**pack, **run})
        self.assertEqual(F.problems(self.data, F.spec_kinds()), [])

    def test_the_row_names_the_definitions_model_and_the_one_served_and_no_field_hides_another(self):
        self.record(run_file())
        fields = json.loads(json.loads(self.data.splitlines()[-1])["payload"]["summary"][len(A.FORM2):])
        self.assertEqual((fields["model"], fields["model_served"]), ("opus", "claude-opus-5-5"))
        self.assertEqual(set(A.PACKET_KEYS2) & (set(A.RUN_KEYS) | set(A.AMEND_KEYS[1:])), set())

    def test_an_amending_row_carries_the_agent_the_run_it_names_and_the_findings(self):
        first = self.record(run_file(finding(1)))
        again = finding(1, A.FALSE_ALARM, "read in a later session")
        row_id = self.amend(first, again)
        row = json.loads(self.data.splitlines()[-1])
        self.assertEqual((row["row_id"], row["kind"], row["payload"]["refs"]),
                         (row_id, "build", ["agents/one.md", "agent_run:one"]))
        self.assertEqual(json.loads(row["payload"]["summary"][len("agent_run/2 "):]),
                         {"agent": "one", "amends": first, "findings": [again]})
        self.assertTrue(row["payload"]["summary"].startswith("agent_run/2 {"))

    def test_an_amending_row_that_names_no_run_of_the_agent_or_other_findings_is_refused_and_the_ledger_is_left(self):
        start = json.loads(self.data.splitlines()[0])["row_id"]
        other = self.old_run(run_file(old_finding(1)), "two")
        first = self.record(run_file(finding(1)))
        before = self.data
        for name in (start, other, "f999"):
            with self.subTest(name=name), self.faults("amends_no_run"):
                self.amend(name, finding(1))
        for findings in ((), (finding(1), finding(2))):
            with self.subTest(findings=findings), self.faults("amends_other_findings"):
                self.amend(first, *findings)
        for run in ({"amends": first}, {"findings": []}, {"amends": first, "findings": [finding(1)], "tokens": 1},
                    {"amends": "1", "findings": [finding(1)]}, {"amends": None, "findings": [finding(1)]}):
            with self.subTest(run=run), self.faults("bad_amends"):
                A.amend("one", run, self.ledger, SNAPSHOT, TS, F.spec_kinds(), self.root)
        with self.faults("bad_finding:1"):
            self.amend(first, old_finding(1))
        with open(self.ledger, "rb") as f:
            self.assertEqual(f.read(), before)

    def test_a_carried_finding_names_a_report_that_is_a_file_or_a_row_the_ledger_holds(self):
        os.makedirs(os.path.join(self.root, "reports", "dir.json"))
        with open(os.path.join(self.root, "reports", "kept.json"), "wb") as f:
            f.write(b"{}")
        start = json.loads(self.data.splitlines()[0])["row_id"]
        before = self.data
        for place in ("reports/absent.json", "reports/dir.json", "f999"):
            with self.subTest(place=place), self.faults("carried_in_absent:2"):
                self.record(run_file(finding(1), finding(2, A.CARRIED, "true", place)))
        with open(self.ledger, "rb") as f:
            self.assertEqual(f.read(), before)
        first = self.record(run_file(finding(1, A.CARRIED, "true", "reports/kept.json"),
                                     finding(2, A.CARRIED, "true", start)))
        with self.faults("carried_in_absent:1"):
            self.amend(first, finding(1, A.CARRIED, "true", "f999"), finding(2))
        self.assertEqual(A.measure(self.data, "one")["carried"], 2)

    def test_a_repeat_names_a_finding_of_a_run_of_the_agent_before_the_findings_own_run(self):
        other = self.old_run(run_file(old_finding(1)), "two")
        start = json.loads(self.data.splitlines()[0])["row_id"]
        first = self.record(run_file(finding(1)))
        before = self.data
        for again in (first + "#2", other + "#1", start + "#1", "f999#1"):
            with self.subTest(again=again), self.faults("repeat_of_no_finding:2"):
                self.record(run_file(finding(1), finding(2, repeat_of=again)))
        with self.faults("repeat_of_no_finding:1"):
            self.amend(first, finding(1, repeat_of=first + "#1"))
        with open(self.ledger, "rb") as f:
            self.assertEqual(f.read(), before)
        second = self.record(run_file(finding(1, repeat_of=first + "#1")))
        with self.faults("repeat_of_no_finding:1"):
            self.amend(first, finding(1, repeat_of=second + "#1"))
        self.amend(second, finding(1, A.FALSE_ALARM, "why", repeat_of=first + "#1"))
        self.assertEqual(A.measure(self.data, "one")["repeats"], 1)

    def test_a_ledger_whose_run_rows_cannot_be_read_takes_no_further_run(self):
        row = F.next_row(self.data, "build", "a note", ["agent_run:one"], SNAPSHOT, TS)
        self.data += F.line_of(row)
        with open(self.ledger, "wb") as f:
            f.write(self.data)
        with self.faults("run_row_unreadable:%s" % row["row_id"]):
            self.record(run_file())

    def test_a_file_the_agent_was_given_that_is_no_longer_the_packets_is_refused(self):
        self.packet()
        self.assertEqual([file for file, _ in A.PINNED], ["diff.patch", "lessons.json", "memory.json", "message.txt"])
        for file, key in A.PINNED:
            path = os.path.join(self.out, file)
            with open(path, "rb") as f:
                was = f.read()
            self.assertEqual(A.read_packet(self.out)[key], hashlib.sha256(was).hexdigest())
            with open(path, "ab") as f:
                f.write(b" \n")
            with self.subTest(file=file), self.faults("%s_changed" % file.split(".")[0]):
                A.read_packet(self.out)
            os.remove(path)
            with self.subTest(file=file), self.faults("packet_unreadable"):
                A.read_packet(self.out)
            with open(path, "wb") as f:
                f.write(was)
        self.assertEqual(self.record(run_file())[0], "f")

    def test_a_packet_that_cannot_be_read_is_refused(self):
        with self.faults("packet_unreadable"):
            A.read_packet(self.out)
        self.packet()
        path = os.path.join(self.out, "packet.json")
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        for broken in ([doc], {**doc, "more": 1}, {k: v for k, v in doc.items() if k != "head"},
                       {k: v for k, v in doc.items() if k != "message_sha256"}):
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
                (run_file(effort=None, not_measured="none stated"), "bad_run_field"),
                (run_file(tokens="12"), "bad_run_field"),
                (run_file(tokens=None, not_measured="none shown"), "bad_run_field"),
                (run_file(cost_usd_micros=1.5), "bad_run_field"),
                (run_file(not_measured=" "), "bad_run_field"),
                (run_file(cost_usd_micros=None), "unknown_without_reason"),
                (run_file(amends="1912"), "bad_amends"),
                (run_file(amends="f1"), "bad_run_field"),
                (run_file(findings={}), "findings_not_a_list"),
                (run_file(finding(2)), "bad_finding:1"),
                (run_file(good, finding(3)), "bad_finding:2"),
                (run_file({**good, "n": True}), "bad_finding:1"),
                (run_file({**good, "n": 1.0}), "bad_finding:1"),
                (run_file({**good, "more": 1}), "bad_finding:1"),
                (run_file({k: v for k, v in good.items() if k != "ref"}), "bad_finding:1"),
                (run_file(old_finding(1)), "bad_finding:1"),
                (run_file({k: v for k, v in good.items() if k != "repeat_of"}), "bad_finding:1"),
                (run_file({**good, "class": ""}), "bad_finding:1"),
                (run_file({**good, "claim": None}), "bad_finding:1"),
                (run_file({**good, "ref": ""}), "bad_finding:1"),
                (run_file({**good, "verdict": "real"}), "bad_finding:1"),
                (run_file({**good, "verdict": "real", "evidence": "a test"}), "bad_finding:1"),
                (run_file({**good, "verdict": ["caught"], "evidence": "a test"}), "bad_finding:1"),
                (run_file(finding(1, A.CAUGHT)), "bad_finding:1"),
                (run_file(finding(1, A.FALSE_ALARM)), "bad_finding:1"),
                (run_file(finding(1, A.FALSE_ALARM, " ")), "bad_finding:1"),
                (run_file(finding(1, A.CARRIED, None, "f1")), "bad_finding:1"),
                (run_file(finding(1, A.CARRIED, "true")), "bad_finding:1"),
                (run_file(finding(1, A.CARRIED, "true", "reports/a/b.json")), "bad_finding:1"),
                (run_file(finding(1, A.CARRIED, "true", "docs/a.json")), "bad_finding:1"),
                (run_file(finding(1, A.CARRIED, "true", "f1#1")), "bad_finding:1"),
                (run_file(finding(1, A.CARRIED, "true", ["f1"])), "bad_finding:1"),
                (run_file(finding(1, A.CAUGHT, "t", "f1")), "bad_finding:1"),
                (run_file(finding(1, carried_in="f1")), "bad_finding:1"),
                (run_file(finding(1, repeat_of="f1")), "bad_finding:1"),
                (run_file(finding(1, repeat_of="f1#0")), "bad_finding:1"),
                (run_file(finding(1, repeat_of=["f1#1"])), "bad_finding:1"),
                (run_file("a finding"), "bad_finding:1")):
            with self.subTest(reason=reason, run=run), self.faults(reason):
                self.record(run)
        with open(self.ledger, "rb") as f:
            self.assertEqual(f.read(), before)

    def test_the_cost_may_be_null_with_its_reason_and_a_ref_may_be_null(self):
        self.record(run_file({**finding(1), "ref": None}, cost_usd_micros=None,
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
                     F.spec_kinds(), self.root)


# A packet's fields as a row of the form ``agent_run/1`` carries them, and as ``record`` carries them now, for
# rows written here without a packet directory.
PACK = {"agent": "one", "model": "opus", "definition_sha256": "d" * 64, "base": "B", "head": "H",
        "diff_sha256": "e" * 64, "bytes": 1, "files": 1}
PACK2 = {**PACK, "rules_sha256": "a" * 64, "lessons": 0, "memory": 0, "message_sha256": "b" * 64,
         "lessons_sha256": "e" * 64, "memory_sha256": "f" * 64}


def old_text(pack: dict, run: dict) -> str:
    return A.FORM + json.dumps({**pack, **run})


class Measure(Base):
    def test_no_run_is_all_zero_and_not_due(self):
        self.assertEqual(A.measure(self.data, "one"), {"ok": True, "agent": "one", **ZERO, "before_rules": ZERO,
                                                       "under_rules": ZERO, "retire_due": False})

    def test_runs_sessions_verdicts_and_sums(self):
        self.record(run_file(finding(1, A.CAUGHT, "t"), finding(2)))
        self.record(run_file(finding(1, A.FALSE_ALARM, "why"), wall_ms=5))
        self.row("session_end")
        start = self.row("session_start")
        self.record(run_file(finding(1, A.CARRIED, "true", start), finding(2, A.CAUGHT, "t", repeat_of="f2#2"),
                             cost_usd_micros=None, not_measured="none shown", wall_ms=1))
        got = A.measure(self.data, "one")
        fold = {"runs": 3, "sessions": 2, "findings": 5, "caught": 2, "false_alarm": 1, "unjudged": 1, "carried": 1,
                "repeats": 1, "tokens": 3600, "tokens_unknown": 0, "cost_usd_micros": 680000, "cost_unknown": 1,
                "wall_ms": 90006, "caught_tokens_known": 2}
        self.assertEqual(got, {"ok": True, "agent": "one", **fold, "before_rules": ZERO, "under_rules": fold,
                               "retire_due": False})

    def test_the_runs_before_the_rules_are_still_read_and_folded_apart_from_the_runs_under_them(self):
        old = self.old_run(run_file(old_finding(1, A.CAUGHT, "t"), old_finding(2), effort=None, tokens=None,
                                    cost_usd_micros=None, not_measured="none shown"))
        self.old_run(run_file(old_finding(1)))
        self.row("session_start")
        self.record(run_file(finding(1, A.FALSE_ALARM, "why", repeat_of=old + "#2"), wall_ms=7))
        got = A.measure(self.data, "one")
        before = {**ZERO, "runs": 2, "sessions": 1, "findings": 3, "caught": 1, "unjudged": 2, "tokens": 1200,
                  "tokens_unknown": 1, "cost_usd_micros": 340000, "cost_unknown": 1, "wall_ms": 180000}
        under = {**ZERO, "runs": 1, "sessions": 1, "findings": 1, "false_alarm": 1, "repeats": 1, "tokens": 1200,
                 "cost_usd_micros": 340000, "wall_ms": 7}
        self.assertEqual((got["before_rules"], got["under_rules"]), (before, under))
        self.assertEqual({k: got[k] for k in ZERO}, {
            **ZERO, "runs": 3, "sessions": 2, "findings": 4, "caught": 1, "false_alarm": 1, "unjudged": 2,
            "repeats": 1, "tokens": 2400, "tokens_unknown": 1, "cost_usd_micros": 680000, "cost_unknown": 1,
            "wall_ms": 180007})
        self.assertEqual([r["message_sha256"] for r in A.runs(self.data, "one").values()],
                         [None, None, A.read_packet(self.out)["message_sha256"]])

    def test_another_agents_rows_are_not_counted(self):
        self.agent(GOOD.replace(b"name: one", b"name: two"), "two")
        self.record(run_file(finding(1)))
        row_id = A.record(self.packet("two", self.out + "-two"), run_file(finding(1)),
                          self.ledger, SNAPSHOT, TS, F.spec_kinds(), self.root)
        self.read()
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
        self.amend(first, finding(1, A.CAUGHT, "the rival's reproducer of the same line"),
                   finding(2, A.FALSE_ALARM, "why"))
        got = A.measure(self.data, "one")
        self.assertEqual((got["runs"], got["findings"], got["caught"], got["false_alarm"], got["unjudged"]),
                         (2, 3, 1, 1, 1))
        self.assertEqual((got["tokens"], got["wall_ms"]), (2400, 180000))

    def test_an_amending_row_of_either_form_amends_a_run_before_the_rules(self):
        first = self.old_run(run_file(old_finding(1), old_finding(2)))
        self.old_run(run_file(old_finding(1, A.CAUGHT, "t"), old_finding(2), amends=first, tokens=7, wall_ms=7))
        got = A.measure(self.data, "one")["before_rules"]
        self.assertEqual((got["runs"], got["caught"], got["unjudged"], got["tokens"], got["wall_ms"]),
                         (1, 1, 1, 1200, 90000))
        self.amend(first, finding(1, A.CAUGHT, "t"), finding(2, A.CARRIED, "true", first))
        got = A.measure(self.data, "one")
        self.assertEqual((got["before_rules"]["carried"], got["before_rules"]["unjudged"], got["under_rules"]),
                         (1, 0, ZERO))

    def test_an_amending_row_that_names_no_earlier_run_is_a_fault(self):
        start = json.loads(self.data.splitlines()[0])["row_id"]
        for name in (start, "f999"):
            for text in (old_text(PACK, run_file(amends=name)),
                         A.FORM2 + json.dumps({"agent": "one", "amends": name, "findings": []})):
                row = F.next_row(self.data, "build", text, ["agent_run:one"], SNAPSHOT, TS)
                with self.subTest(text=text), self.faults("amends_no_run:%s" % row["row_id"]):
                    A.measure(self.data + F.line_of(row), "one")

    def unreadable(self, texts) -> None:
        for text in texts:
            row = F.next_row(self.data, "build", text, ["agent_run:one"], SNAPSHOT, TS)
            with self.subTest(text=text), self.faults("run_row_unreadable:%s" % row["row_id"]):
                A.measure(self.data + F.line_of(row), "one")

    def readable(self, text: str) -> dict:
        row = F.next_row(self.data, "build", text, ["agent_run:one"], SNAPSHOT, TS)
        return A.measure(self.data + F.line_of(row), "one")

    def test_a_tagged_row_of_another_form_is_a_fault_never_skipped(self):
        self.assertEqual(self.readable(old_text(PACK, run_file(old_finding(1))))["before_rules"]["runs"], 1)
        self.unreadable((
            "a note about the agent", "agent_run/1 not json", "agent_run/1 [1]", "agent_run/1 {}",
            "agent_run/3 " + json.dumps({**PACK2, **run_file()}), 7,
            A.FORM + json.dumps({"findings": [{"n": 1}], "tokens": 1, "cost_usd_micros": 1, "wall_ms": 1}),
            A.FORM + json.dumps({"findings": [], "tokens": 1, "cost_usd_micros": 1}),
            A.FORM + json.dumps({"findings": [], "tokens": "1", "cost_usd_micros": 1, "wall_ms": 1}),
            A.FORM + json.dumps({"findings": [], "tokens": 1, "cost_usd_micros": 1.5, "wall_ms": 1}),
            A.FORM + json.dumps({"findings": [], "tokens": 1, "cost_usd_micros": 1, "wall_ms": None}),
            A.FORM + json.dumps({"findings": [], "tokens": 1, "cost_usd_micros": 1, "wall_ms": True}),
            # the sums and findings alone are not the form: the packet's and the run file's fields are
            A.FORM + json.dumps({"findings": [], "tokens": 1, "cost_usd_micros": 1, "wall_ms": 1}),
            old_text(dict(PACK, agent="two"), run_file()),
            old_text({k: v for k, v in PACK.items() if k != "diff_sha256"}, run_file()),
            old_text(PACK, {k: v for k, v in run_file().items() if k != "invoked_as"}),
            old_text(PACK, dict(run_file(), more=1)),
            old_text(PACK, dict(run_file(), effort=7)),
            old_text(PACK, dict(run_file(), amends=[])),
            old_text(PACK, dict(run_file(), amends={"f1": 1})),
            old_text(PACK, dict(run_file(), amends="the first")),
            # the forms do not mix: a row before the rules carries none of the rules' fields
            old_text(PACK2, run_file()),
            old_text(PACK, run_file(finding(1))),
            old_text(PACK, run_file({**old_finding(1, A.CARRIED, "true")})),
            A.FORM + json.dumps({"agent": "one", "amends": "f1", "findings": []})))

    def test_a_tagged_row_under_the_rules_that_is_not_their_form_is_a_fault_never_skipped(self):
        self.assertEqual(self.readable(A.summary(PACK2, run_file(finding(1))))["under_rules"]["runs"], 1)
        self.unreadable((
            "agent_run/2 not json", "agent_run/2 [1]", "agent_run/2 {}",
            A.summary(dict(PACK2, agent="two"), run_file()),
            A.summary({k: v for k, v in PACK2.items() if k != "diff_sha256"}, run_file()),
            A.summary({k: v for k, v in PACK2.items() if k != "message_sha256"}, run_file()),
            A.summary({k: v for k, v in PACK2.items() if k != "lessons_sha256"}, run_file()),
            A.summary({k: v for k, v in PACK2.items() if k != "memory_sha256"}, run_file()),
            A.summary(PACK, run_file()),
            A.summary(PACK2, {k: v for k, v in run_file().items() if k != "invoked_as"}),
            A.summary(PACK2, dict(run_file(), more=1)),
            A.summary(PACK2, dict(run_file(), effort=7)),
            A.summary(PACK2, run_file(effort=None, not_measured="none stated")),
            A.summary(PACK2, run_file(tokens=None, not_measured="none shown")),
            A.summary(PACK2, run_file(wall_ms=None)),
            A.summary(PACK2, run_file(amends="f1")),
            A.summary(PACK2, run_file(old_finding(1))),
            A.summary(PACK2, run_file(finding(1, A.CARRIED, "true"))),
            A.summary(PACK2, run_file(finding(1, repeat_of="the first"))),
            A.FORM2 + json.dumps({"agent": "one", "amends": "the first", "findings": []}),
            A.FORM2 + json.dumps({"agent": "one", "amends": ["f1"], "findings": []}),
            A.FORM2 + json.dumps({"agent": "two", "amends": "f1", "findings": []}),
            A.FORM2 + json.dumps({"agent": "one", "amends": "f1", "findings": [old_finding(1)]}),
            A.FORM2 + json.dumps({"agent": "one", "amends": "f1", "findings": [], "tokens": 1}),
            A.FORM2 + json.dumps({"agent": "one", "amends": "f1"})))

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

    def test_retirement_counts_the_sessions_and_the_catches_of_both_forms(self):
        self.data = b""
        for _ in range(4):
            self.row("session_start")
            self.old_run(run_file(old_finding(1)))
        self.row("session_start")
        self.record(run_file(finding(1)))
        self.assertTrue(A.measure(self.data, "one")["retire_due"])
        self.old_run(run_file(old_finding(1, A.CAUGHT, "t")))
        self.assertFalse(A.measure(self.data, "one")["retire_due"])


class Main(Base):
    def main(self, *argv: str) -> tuple[int, dict]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = A.main(list(argv), root=self.root, git=self.git)
        lines = buf.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        return code, json.loads(lines[0])

    def pack(self, *more: str) -> tuple[int, dict]:
        return self.main("packet", "--agent", "one", "--base", "B", "--out", self.out, "--loaded", self.loaded,
                         "--index", self.index, "--ledger", self.ledger, *more)

    def test_packet_record_amend_measure(self):
        code, out = self.pack()
        self.assertEqual((code, out["ok"], out["head"], out["out"], out["lessons"]), (0, True, "HEAD", self.out, 0))
        run = self.put("run.json", json.dumps(run_file(finding(1))).encode())
        code, out = self.main("record", "--packet", self.out, "--run", run, "--snapshot", SNAPSHOT, "--ts", TS,
                              "--ledger", self.ledger)
        self.assertEqual((code, out), (0, {"ok": True, "recorded": "f2"}))
        code, out = self.main("measure", "--agent", "one", "--ledger", self.ledger)
        self.assertEqual((code, out["runs"], out["unjudged"]), (0, 1, 1))
        run = self.put("amend.json", json.dumps({"amends": "f2", "findings": [finding(1, A.CAUGHT, "t")]}).encode())
        code, out = self.main("record", "--agent", "one", "--run", run, "--snapshot", SNAPSHOT, "--ts", TS,
                              "--ledger", self.ledger)
        self.assertEqual((code, out), (0, {"ok": True, "recorded": "f3"}))
        code, out = self.main("measure", "--agent", "one", "--ledger", self.ledger)
        self.assertEqual((code, out["runs"], out["unjudged"], out["caught"]), (0, 1, 0, 1))

    def test_the_default_ledger_is_the_roots(self):
        os.replace(self.ledger, os.path.join(self.root, "founder-ledger.jsonl"))
        self.assertEqual(self.main("measure", "--agent", "one"), (0, A.measure(self.data, "one")))

    def test_the_default_load_record_and_index_are_the_capsules(self):
        self.assertEqual((A.LOADED, A.LR.INDEX), ("/work/logs/brain-definitions.json", "/opt/founder/ledger_index.py"))
        seen = []
        real = A.packet
        A.packet = lambda *args: seen.append(args) or {}
        self.addCleanup(setattr, A, "packet", real)
        self.assertEqual(self.main("packet", "--agent", "one", "--base", "B", "--out", self.out),
                         (0, {"ok": True, "out": self.out}))
        self.assertEqual(seen, [(self.root, "one", "B", "HEAD", self.out, self.git, A.LOADED, A.LR.INDEX,
                                 os.path.join(self.root, "founder-ledger.jsonl"))])

    def test_a_fault_is_exit_2_with_its_reason(self):
        self.load([])
        self.assertEqual(self.pack(), (2, {"ok": False, "reason": "definition_not_loaded"}))
        self.assertEqual(self.main("packet", "--agent", "absent", "--base", "B", "--out", self.out),
                         (2, {"ok": False, "reason": "no_definition"}))
        self.load([{"name": "one", "model": "opus", "tools": [], "sha256": "c" * 64}])
        self.packet()
        for text in (b"not json", b"[1]"):
            run = self.put("run.json", text)
            self.assertEqual(self.main("record", "--packet", self.out, "--run", run, "--snapshot", SNAPSHOT,
                                       "--ledger", self.ledger), (2, {"ok": False, "reason": "run_unreadable"}))
        run = self.put("run.json", json.dumps(run_file()).encode())
        for more in ((), ("--packet", self.out, "--agent", "one")):
            self.assertEqual(self.main("record", "--run", run, "--snapshot", SNAPSHOT, "--ledger", self.ledger,
                                       *more), (2, {"ok": False, "reason": "packet_or_agent"}))
        self.assertEqual(self.main("measure", "--agent", "one", "--ledger", os.path.join(self.tmp, "absent")),
                         (2, {"ok": False, "reason": "ledger_unreadable"}))


class Brain(unittest.TestCase):
    """What this brain promises of its first agent (that every file of ``agents/`` is a definition with its
    origin is the rule ``defined``, bound in ``tests/test_agent_rules.py``)."""

    def test_the_push_reviewer_reads_and_cannot_write_and_is_not_the_model_that_writes_referee_code(self):
        agent = A.definition(ROOT, "push-reviewer")
        self.assertEqual(agent["tools"], ["Read", "Grep", "Glob"])
        self.assertEqual(agent["model"], "opus")

    def test_the_push_reviewers_text_names_what_the_packet_holds_and_the_fold_that_measures_it(self):
        with open(os.path.join(ROOT, "agents", "push-reviewer.md"), "rb") as f:
            _, body = A.front_matter(f.read(), A.AGENT_KEYS)
        for named in (*("`%s`" % file for file in A.GIVEN), "tests/agent_run.py record", "tests/agent_run.py measure",
                      "docs/map/brain.md", *A.VERDICTS2, A.RULES, "tests/agent_rules.py", '"repeat_of"',
                      "do not report one of them again"):
            self.assertIn(named, body)
        self.assertNotIn("/work/logs", body)
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "docs", "map", "brain.md")))

    def test_the_push_skill_names_the_agent_and_the_two_commands_of_its_step(self):
        with open(os.path.join(ROOT, "skills", "push", "SKILL.md"), encoding="utf-8") as f:
            text = f.read()
        for named in ("python3 tests/agent_run.py packet --agent push-reviewer --base <last accepted SHA> --head "
                      "<that commit's SHA> --out",
                      "start the agent `brain:push-reviewer` with effort `high` and the bytes of that directory's "
                      "`message.txt` as its whole message", "python3 tests/agent_run.py record --packet",
                      "stands in for none", *("`%s`" % v for v in A.VERDICTS2), "no finding leaves the session so",
                      "The skill `brain:agents`"):
            self.assertIn(named, " ".join(text.split()))


if __name__ == "__main__":
    unittest.main()
