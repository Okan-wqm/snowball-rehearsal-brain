"""``tests/lesson_recheck.py``'s rules, each bound by a test below (the rules are listed in its docstring, the one
source). The capsule's ledger index is not in the referee's sandbox: rule 1 is held against the index's own bytes
in ``tests/fixtures/ledger-index-lessons.json`` (``tests/capture_ledger_index.py``), replayed by a program that
answers only the captured questions; the other tests give the tool a scripted answer in the captured shape. No
git is needed: the file list comes from a fake that lists the root. Run from the brain's root."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import lesson_recheck as L  # noqa: E402
import run_like_referee as R  # noqa: E402


def py(code: str) -> str:
    """A shell text that runs ``code`` in this interpreter: the referee's PATH holds python and nothing else (no
    sleep, cat, touch, rm), so the checks of these tests are shell builtins and this."""
    return "%s -c %s" % (shlex.quote(sys.executable), shlex.quote(code))


def sleep(seconds: float) -> str:
    return py("import time; time.sleep(%r)" % seconds)

F = L.F
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "ledger-index-lessons.json")
SNAPSHOT = "a" * 40
TS = "2026-11-21T06:00:00Z"

# Answers a question it was given an answer for ({json [ledger's base name, *more]: [exit, stdout]}) and no other;
# the arguments before the ledger must be the tool's fold.
REPLAY = """import json, os, sys
FOLD, PAGES = %r, %r
args = sys.argv[1:]
assert args[:len(FOLD)] == FOLD and args[len(FOLD)] == "--ledger", args
code, out = PAGES[json.dumps([os.path.basename(args[len(FOLD) + 1])] + args[len(FOLD) + 2:])]
sys.stdout.write(out)
sys.exit(code)
"""
# Every file under the root, as ``git ls-files -z`` prints names (the fake reads ``-C <root>`` only).
FAKE_GIT = """#!%s
import os, sys
root = sys.argv[2]
for d, _, names in os.walk(root):
    for n in names:
        sys.stdout.write(os.path.relpath(os.path.join(d, n), root) + "\\0")
"""


def fixture() -> dict:
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="test-lesson-recheck-")
        self.addCleanup(R.remove, self.tmp)
        self.root = os.path.join(self.tmp, "root")
        os.mkdir(self.root)
        self.ledger = os.path.join(self.root, "founder-ledger.jsonl")
        self.index = os.path.join(self.tmp, "index.py")
        self.git = os.path.join(self.tmp, "git")
        with open(self.git, "w") as f:
            f.write(FAKE_GIT % sys.executable)
        os.chmod(self.git, 0o755)
        self.data = b""

    def replay(self, pages: dict, fold=None) -> None:
        with open(self.index, "w", encoding="utf-8") as f:
            f.write(REPLAY % (list(L.FOLD) if fold is None else fold, pages))

    def captured(self) -> dict:
        """The captured ledger as the ledger, the captured answers as the index."""
        doc = fixture()
        with open(self.ledger, "wb") as f:
            f.write(doc["ledger"].encode("utf-8"))
        pages = {json.dumps(["founder-ledger.jsonl"] + p["more"]): [p["exit"], p["stdout"]] for p in doc["pages"]}
        pages[json.dumps(["absent.jsonl"])] = [doc["absent"]["exit"], doc["absent"]["stdout"]]
        self.replay(pages, doc["fold"])
        return doc

    def row(self, kind: str, refs=(), recheck=None) -> str:
        """Add a row to the test ledger (a chain) and return its ``row_id``."""
        row = F.next_row(self.data, kind, "a row of the test", list(refs) or ["tests/lesson_recheck.py"], SNAPSHOT,
                         TS, recheck=recheck)
        self.data += F.line_of(row)
        with open(self.ledger, "wb") as f:
            f.write(self.data)
        return row["row_id"]

    def lesson(self, recheck: str) -> dict:
        row_id = self.row("lesson", recheck=recheck)
        return {"row_id": row_id, "line": self.data.count(b"\n")}

    def script(self, lessons: list[dict], pages=None, **head) -> None:
        """The index answers with ``lessons`` in one page shaped like the captured one, or with ``pages``:
        ``[(more, lessons, next)]``."""
        shape = json.loads(fixture()["pages"][0]["stdout"].splitlines()[0])
        out = {}
        total = sum(len(p[1]) for p in pages) if pages else len(lessons)
        for more, rows, nxt in pages or [([], lessons, None)]:
            first = {**shape, "sha256": hashlib.sha256(self.data).hexdigest(), "count": total, "shown": len(rows),
                     "next": nxt, **head}
            lines = [first] + [{"row_id": r["row_id"], "line": r["line"], "kind": "lesson"} for r in rows]
            out[json.dumps(["founder-ledger.jsonl"] + more)] = [0, "".join(json.dumps(x) + "\n" for x in lines)]
        self.replay(out)

    def main(self, *argv: str) -> tuple[int, dict]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = L.main([*argv, "--index", self.index, "--ledger", self.ledger], root=self.root, git=self.git)
        lines = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertTrue(lines and all(list(line) == ["result"] for line in lines[:-1]), lines)
        if code != 2:
            lines[-1]["results"] = [line["result"] for line in lines[:-1]]
        return code, lines[-1]

    def fault(self, reason: str, *argv: str) -> None:
        self.assertEqual(self.main(*(argv or ("run",))), (2, {"ok": False, "reason": reason}))


class InForce(Base):
    """Rule 1."""

    def test_the_lessons_are_the_captured_index_answer_over_every_page(self):
        doc = self.captured()
        self.assertGreater(len(doc["pages"]), 1)
        digest, lessons = L.in_force(self.index, self.ledger)
        self.assertEqual(digest, hashlib.sha256(doc["ledger"].encode("utf-8")).hexdigest())
        self.assertEqual([x["row_id"] for x in lessons], doc["in_force"])
        rows = [json.loads(line) for line in doc["ledger"].splitlines()]
        self.assertEqual([rows[x["line"] - 1]["row_id"] for x in lessons], doc["in_force"])

    def test_the_capture_holds_a_closed_a_twice_closed_and_an_early_named_lesson(self):
        doc = fixture()
        rows = [json.loads(line) for line in doc["ledger"].splitlines()]
        lessons = [r["row_id"] for r in rows if r["kind"] == "lesson"]
        closers = [(i, ref[len("closes:"):]) for i, r in enumerate(rows) for ref in r["payload"]["refs"]
                   if ref.startswith("closes:")]
        place = {r["row_id"]: i for i, r in enumerate(rows)}
        closed = {name for i, name in closers if i > place[name]}
        early = {name for i, name in closers if i < place[name]}
        self.assertEqual(len(closed), 2)
        self.assertTrue(any(sum(1 for _, n in closers if n == name) == 2 for name in closed))
        self.assertTrue(early and early <= set(doc["in_force"]))
        self.assertEqual(doc["in_force"], [x for x in lessons if x not in closed])

    def test_the_fold_asked_is_the_fold_captured(self):
        self.assertEqual(fixture()["fold"], list(L.FOLD))

    def test_an_index_that_exits_non_zero_is_a_fault(self):
        self.captured()
        with self.assertRaises(L.Fault) as e:
            L.in_force(self.index, os.path.join(self.root, "absent.jsonl"))
        self.assertEqual(str(e.exception), "index_exit:2")
        os.unlink(self.index)
        self.fault("index_exit:2")

    def test_an_index_that_cannot_be_started_is_a_fault(self):
        with mock.patch.object(L.subprocess, "run", side_effect=FileNotFoundError):
            self.fault("index_unavailable:FileNotFoundError")

    def test_output_that_is_not_json_lines_of_objects_is_a_fault(self):
        for text in ("", "not json\n", "[1]\n", '{"complete": true, "shown": 1}\n3\n'):
            self.replay({json.dumps(["founder-ledger.jsonl"]): [0, text]})
            self.fault("index_output_unreadable")

    def test_an_incomplete_or_miscounted_answer_is_a_fault(self):
        a = self.lesson("true")
        for head in ({"complete": False}, {"shown": 2}, {"count": 2}, {"sha256": None}):
            self.script([a], **head)
            self.fault("index_incomplete")

    def test_a_row_without_a_text_id_and_a_whole_line_number_is_a_fault(self):
        a = self.lesson("true")
        for bad in ({"row_id": 7, "line": a["line"]}, {"row_id": a["row_id"], "line": "3"},
                    {"row_id": a["row_id"], "line": True}):
            self.script([bad])
            self.fault("index_row_unreadable")

    def test_pages_of_two_ledgers_are_a_fault(self):
        a, b = self.lesson("true"), self.lesson("true")
        self.script([], pages=[([], [a], "--after 1"), (["--after", "1"], [b], None)])
        self.assertEqual(self.main("run")[1]["held"], 2)
        with open(self.index, encoding="utf-8") as f:
            text = f.read()
        digest = hashlib.sha256(self.data).hexdigest()
        self.assertEqual(text.count(digest), 2)
        with open(self.index, "w", encoding="utf-8") as f:
            f.write(text.replace(digest, "0" * 64, 1))
        self.fault("ledger_moved")
        with open(self.index, "w", encoding="utf-8") as f:
            f.write(text[::-1].replace(digest[::-1], "0" * 64, 1)[::-1])
        self.fault("ledger_moved")

    def test_a_next_that_is_no_text_or_does_not_move_is_a_fault(self):
        a = self.lesson("true")
        self.script([], pages=[([], [a], ["--after", "1"])])
        self.fault("index_next_unreadable")
        self.script([], pages=[([], [a], "--after 1"), (["--after", "1"], [a], "--after  1")])
        self.fault("index_next_unreadable")


class Rechecks(Base):
    """Rule 2."""

    def test_the_text_is_the_named_lines_recheck(self):
        a, b = self.lesson("exit 4"), self.lesson("none: a habit")
        digest = hashlib.sha256(self.data).hexdigest()
        self.assertEqual(L.rechecks(self.data, digest, [a, b]),
                         [{**a, "recheck": "exit 4"}, {**b, "recheck": "none: a habit"}])

    def test_other_bytes_than_the_index_read_are_a_fault(self):
        a = self.lesson("true")
        self.script([a])
        self.row("decision")
        self.fault("ledger_moved")

    def test_a_line_that_is_not_that_lesson_is_a_fault(self):
        a, b = self.lesson("true"), self.lesson("true")
        other = self.row("decision")
        digest = hashlib.sha256(self.data).hexdigest()
        for bad in ({"row_id": a["row_id"], "line": b["line"]}, {"row_id": other, "line": b["line"] + 1},
                    {"row_id": a["row_id"], "line": 0}, {"row_id": a["row_id"], "line": 99},
                    {"row_id": a["row_id"], "line": -self.data.count(b"\n")}):
            with self.assertRaises(L.Fault) as e:
                L.rechecks(self.data, digest, [bad])
            self.assertEqual(str(e.exception), "line_is_not_the_lesson:" + bad["row_id"])
        data = self.data + b"not json\n"
        with self.assertRaises(L.Fault):
            L.rechecks(data, hashlib.sha256(data).hexdigest(), [{"row_id": "f9", "line": b["line"] + 2}])

    def test_an_unreadable_ledger_is_a_fault(self):
        a = self.lesson("true")
        self.script([a])
        os.unlink(self.ledger)
        self.fault("ledger_unreadable:FileNotFoundError")


class RunOne(Base):
    """Rule 3."""

    def one(self, recheck, timeout: float = 60.0) -> dict:
        return L.run_one({"row_id": "f1", "line": 1, "recheck": recheck}, self.root, timeout)

    def test_exit_zero_holds_and_any_other_exit_fails(self):
        got = self.one("true")
        self.assertEqual((got["status"], got["exit"], got["row_id"], got["line"]), ("held", 0, "f1", 1))
        self.assertIsInstance(got["ms"], int)
        got = self.one("exit 3")
        self.assertEqual((got["status"], got["exit"]), ("failed", 3))

    def test_no_command_is_not_run(self):
        for text in ("none: a habit; : > ran", "", None, 5):
            self.assertEqual(self.one(text), {"row_id": "f1", "line": 1, "status": "none", "exit": None, "ms": None})
        self.assertEqual(os.listdir(self.root), [])
        self.assertEqual(self.one("true none: && : > ran")["status"], "held")
        self.assertEqual(os.listdir(self.root), ["ran"])

    def test_it_runs_as_written_by_the_shell_from_the_root_without_stdin(self):
        with open(os.path.join(self.root, "here"), "w") as f:
            f.write("a\n")
        self.assertEqual(self.one("cd . && test -f here && read x < here && test \"$x\" = a && ! test \"$x\" = b")["status"], "held")
        reader, writer = os.pipe()
        os.write(writer, b"from the caller's stdin\n")
        os.close(writer)
        saved = os.dup(0)
        os.dup2(reader, 0)
        try:
            self.assertEqual(self.one("! read x")["status"], "held")
        finally:
            os.dup2(saved, 0)
            os.close(saved)
            os.close(reader)
        group = "test \"$('%s' -c 'import os; print(os.getpgrp())')\" = $$" % sys.executable
        self.assertEqual(self.one(group)["status"], "held")

    def test_the_output_is_hashed_and_its_end_kept(self):
        got = self.one("printf '%s' " + "a" * 400 + "b; printf err >&2; exit 1")
        self.assertEqual(got["stdout_sha256"], hashlib.sha256(b"a" * 400 + b"b").hexdigest())
        self.assertEqual(got["stdout_tail"], "a" * 299 + "b")
        self.assertEqual((got["stderr_sha256"], got["stderr_tail"]), (hashlib.sha256(b"err").hexdigest(), "err"))

    def test_no_exit_in_time_is_a_timeout_and_the_group_is_killed(self):
        start = time.monotonic()
        got = self.one(sleep(3) + " & " + sleep(3), timeout=0.3)
        self.assertLess(time.monotonic() - start, 2)
        self.assertEqual((got["status"], got["exit"]), ("timeout", None))
        self.assertGreaterEqual(got["ms"], 300)

    def test_stated_limits_prose_fails_and_a_command_that_cannot_fail_holds(self):
        self.assertEqual(self.one("the tests (all of them) are green")["status"], "failed")
        self.assertEqual(self.one("false | true")["status"], "held")


class Run(Base):
    """Rules 3 to 5, through the command."""

    def test_the_answer_counts_each_status_in_ledger_order(self):
        lessons = [self.lesson(t) for t in ("true", "exit 2", "none: a habit", sleep(4), "true")]
        self.script(lessons)
        code, got = self.main("run", "--timeout", "0.5")
        self.assertEqual(code, 1)
        self.assertEqual([(r["row_id"], r["status"]) for r in got["results"]],
                         list(zip([x["row_id"] for x in lessons], ["held", "failed", "none", "timeout", "held"])))
        del got["results"]
        self.assertEqual(got, {"ok": False, "in_force": 5, "run": 4, "held": 2, "failed": 1, "timeout": 1,
                               "none": 1, "tree_changed": []})

    def test_ok_needs_no_failure_no_timeout_and_an_unchanged_tree(self):
        a = self.lesson("true")
        self.script([a, self.lesson("none: a habit")])
        code, got = self.main("run")
        self.assertEqual((code, got["ok"], got["held"], got["none"]), (0, True, 1, 1))
        for bad, key in (("exit 1", "failed"), (sleep(4), "timeout")):
            self.script([a, self.lesson(bad)])
            code, got = self.main("run", "--timeout", "0.5")
            self.assertEqual((code, got["ok"], got[key]), (1, False, 1))

    def test_each_result_is_printed_when_its_check_ends(self):
        lessons = [self.lesson("true"), self.lesson("exit 1")]
        seen = []
        with mock.patch.object(L, "_emit", side_effect=lambda r: seen.append((r["row_id"], os.path.exists(
                os.path.join(self.root, "second"))))):
            lessons.append(self.lesson(": > second"))
            self.script(lessons)
            self.main("run")
        self.assertEqual(seen, [(lessons[0]["row_id"], False), (lessons[1]["row_id"], False),
                                (lessons[2]["row_id"], True)])
        os.unlink(os.path.join(self.root, "second"))

    def test_a_result_reaches_a_pipe_before_the_next_check_ends(self):
        wait = "i=0; while test ! -e go && test $i -lt 50; do %s; i=$((i+1)); done; test -e go" % sleep(0.1)
        self.script([self.lesson("true"), self.lesson(wait)])
        code = ("import sys; sys.path.insert(0, %r); import lesson_recheck as L; "
                "sys.exit(L.main(['run', '--index', %r, '--ledger', %r], root=%r, git=%r))"
                % (os.path.join(ROOT, "tests"), self.index, self.ledger, self.root, self.git))
        proc = subprocess.Popen([sys.executable, "-c", code], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE)
        try:
            first = json.loads(proc.stdout.readline())
            with open(os.path.join(self.root, "go"), "w"):
                pass
            rest = [json.loads(line) for line in proc.stdout.read().splitlines()]
        finally:
            proc.stdout.close()
            proc.wait()
        self.assertEqual(first["result"]["status"], "held")
        self.assertEqual([rest[0]["result"]["status"], rest[1]["held"], rest[1]["tree_changed"]], ["held", 2, ["go"]])

    def test_one_at_a_time_in_order(self):
        self.script([self.lesson("test ! -e mark && %s && : > mark" % sleep(0.3)),
                     self.lesson("test -e mark && " + py("import os; os.unlink('mark')"))])
        self.assertEqual(self.main("run")[1]["held"], 2)

    def test_a_changed_tree_is_named_and_not_ok(self):
        with open(os.path.join(self.root, "kept"), "w") as f:
            f.write("a\n")
        with open(os.path.join(self.root, "gone"), "w") as f:
            f.write("a\n")
        self.script([self.lesson("echo b > kept; %s; echo c > new" % py("import os; os.unlink('gone')"))])
        code, got = self.main("run")
        self.assertEqual((code, got["ok"], got["held"], got["tree_changed"]), (1, False, 1, ["gone", "kept", "new"]))

    def test_an_unlisted_tree_is_a_fault(self):
        self.script([self.lesson("true")])
        self.git = os.path.join(self.tmp, "no-git")
        self.fault("git_unavailable")

    def test_only_runs_the_named_lessons_and_refuses_other_names(self):
        a, b = self.lesson("exit 1"), self.lesson("true")
        self.script([a, b])
        code, got = self.main("run", "--only", b["row_id"])
        self.assertEqual((code, got["in_force"], [r["row_id"] for r in got["results"]]), (0, 1, [b["row_id"]]))
        self.fault("not_in_force:f0,f9", "run", "--only", "f9", b["row_id"], "f0")


class Record(Base):
    """Rule 6."""

    def rows(self) -> list[dict]:
        with open(self.ledger, "rb") as f:
            return [json.loads(line) for line in f.read().splitlines()]

    def test_one_row_with_a_ref_per_lesson_run(self):
        ids = [self.lesson(t) for t in ("true", "exit 2", "none: a habit", sleep(4))]
        self.script(ids)
        before = self.rows()
        code, got = self.main("record", "--snapshot", SNAPSHOT, "--ts", TS, "--timeout", "0.5")
        rows = self.rows()
        self.assertEqual(rows[:-1], before)
        new = rows[-1]
        self.assertEqual((code, got["recorded"]), (1, new["row_id"]))
        self.assertEqual(new["payload"]["refs"], ["recheck_held:" + ids[0]["row_id"],
                                                  "recheck_failed:" + ids[1]["row_id"],
                                                  "recheck_timeout:" + ids[3]["row_id"]])
        self.assertEqual((new["kind"], new["derivation"], new["trust"], new["snapshot_id"], new["ts"]),
                         ("build", "tool", "observed", SNAPSHOT, TS))
        self.assertEqual(new["payload"]["summary"], L.summary(got, got["results"]))
        self.assertIn("4 lessons in force, 3 run as written, 1 held, 1 failed, 1 timeout, 1 with no command",
                      new["payload"]["summary"])
        self.assertIn("Not holding: %s (exit 2), %s (timeout)." % (ids[1]["row_id"], ids[3]["row_id"]),
                      new["payload"]["summary"])
        with open(self.ledger, "rb") as f:
            self.assertEqual(F.problems(f.read(), F.spec_kinds()), [])

    def test_a_green_run_is_recorded_too_and_says_none(self):
        self.script([self.lesson("true")])
        code, got = self.main("record", "--snapshot", SNAPSHOT)
        new = self.rows()[-1]
        self.assertEqual((code, got["ok"], got["recorded"]), (0, True, new["row_id"]))
        self.assertIn("Not holding: none.", new["payload"]["summary"])
        self.assertRegex(new["ts"], r"\A20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z")

    def test_a_changed_tree_or_no_lesson_run_writes_no_row(self):
        self.script([self.lesson("echo x > new")])
        code, got = self.main("record", "--snapshot", SNAPSHOT)
        self.assertEqual((code, got["recorded"], got["tree_changed"]), (1, None, ["new"]))
        os.unlink(os.path.join(self.root, "new"))
        self.script([self.lesson("none: a habit")])
        code, got = self.main("record", "--snapshot", SNAPSHOT)
        self.assertEqual((code, got["ok"], got["recorded"], got["run"]), (0, True, None, 0))
        with open(self.ledger, "rb") as f:
            self.assertEqual(f.read(), self.data)

    def test_a_ledger_that_is_no_chain_and_a_refused_row_are_faults(self):
        a = self.lesson("true")
        self.script([a])
        with mock.patch.object(F, "append", return_value=["problem:x", "row_scan:y"]):
            self.fault("row_refused:problem:x;row_scan:y", "record", "--snapshot", SNAPSHOT)
        self.data += b'{"row_id": "f2"}\n'
        with open(self.ledger, "wb") as f:
            f.write(self.data)
        self.script([a])
        self.fault("ledger_unusable:ChainError", "record", "--snapshot", SNAPSHOT)
        with open(self.ledger, "rb") as f:
            self.assertEqual(f.read(), self.data)

    def test_record_takes_no_only(self):
        self.script([self.lesson("true")])
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            self.main("record", "--snapshot", SNAPSHOT, "--only", "f1")


class ThisTree(unittest.TestCase):
    def test_the_push_skill_names_the_record_step(self):
        with open(os.path.join(ROOT, "skills", "push", "SKILL.md"), encoding="utf-8") as f:
            self.assertIn("python3 tests/lesson_recheck.py record --snapshot", f.read())


if __name__ == "__main__":
    unittest.main()
