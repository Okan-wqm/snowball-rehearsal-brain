"""``tests/prepush.py``'s rules, each bound by a test below (the rules are listed in its docstring, the one
source), ``run_like_referee``'s ``watch`` and ``skills/push/SKILL.md``'s form and the commands it names. No git is
needed: git's answers come from a fake that answers by its subcommand. Run from the brain's root.

What these tests need of the machine, stated: the tests that expect a list of readers (``Watch``, ``Check`` and
``Run``'s first) need a temporary directory whose file system moves access times on a read. Where it does not
(``noatime``), each of them fails at ``moving_access_times`` with that message and is not skipped: the rules
they bind are not shown on such a machine. The rule for such a machine itself (``readers`` null) is bound with
``atime_moves`` replaced, so it runs on either kind."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import prepush as P  # noqa: E402
import agent_run as A  # noqa: E402
import run_like_referee as R  # noqa: E402

# Answers by subcommand (the first argument after ``-C <root>``) from a JSON file: {subcommand: [stdout, exit]};
# a key of the subcommand and the argument after it ("ls-files --others") answers before the subcommand's own.
FAKE_GIT = """#!%s
import json, sys
with open(%r) as f:
    answers = json.load(f)
out, code = answers.get(" ".join(sys.argv[3:5])) or answers[sys.argv[3]]
sys.stdout.write(out)
sys.exit(code)
"""
READS_LEDGER = "python -c \"open('founder-ledger.jsonl').read()\""
LISTS_ONLY = "python -c \"import os; os.stat('founder-ledger.jsonl'); os.listdir('.')\""
LEDGER_HAS_NO_BAD = "python -c \"import sys; sys.exit('bad' in open('founder-ledger.jsonl').read())\""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="test-prepush-")
        self.addCleanup(R.remove, self.tmp)
        self.root = os.path.join(self.tmp, "root")
        os.mkdir(self.root)
        self.work = os.path.join(self.tmp, "work")
        os.mkdir(self.work)
        saved = tempfile.tempdir
        tempfile.tempdir = self.work
        self.addCleanup(setattr, tempfile, "tempdir", saved)
        self.stamp = os.path.join(self.tmp, "gitdir", P.STAMP)
        os.mkdir(os.path.dirname(self.stamp))
        self.answers = os.path.join(self.tmp, "answers.json")
        self.git = os.path.join(self.tmp, "git")
        with open(self.git, "w") as f:
            f.write(FAKE_GIT % (sys.executable, self.answers))
        os.chmod(self.git, 0o755)
        self.dirty = ""
        self.git_says: dict = {}  # more answers of the fake git, over ``call``'s own
        # ``run`` stamps only what ran on ``run_like_referee``'s cold home; whether this machine builds one is
        # that module's test, so here it is answered: this interpreter stands for it.
        self.addCleanup(setattr, R, "cold_home", R.cold_home)
        R.cold_home = lambda home: os.path.realpath(sys.executable)

    def moving_access_times(self) -> None:
        self.assertTrue(R.atime_moves(self.work), "this test needs a file system where access times move")

    def put(self, name: str, text: str = "x\n", mode: int = 0o644) -> str:
        path = os.path.join(self.root, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        os.chmod(path, mode)
        return name

    def world(self, *cmds: str, ledger: str | None = "row1\n") -> None:
        """A brain: a manifest of ``cmds`` (ids T0, T1, ...), one other file and, unless None, a ledger."""
        self.put("snowball-tests.json", json.dumps(
            {"tests": [{"id": "T%d" % n, "cmd": c, "stage": 0} for n, c in enumerate(cmds)]}))
        self.put("a.txt")
        if ledger is not None:
            self.put(P.LEDGER, ledger)

    def call(self, fn, **kw) -> dict:
        names = [os.path.relpath(os.path.join(top, n), self.root)
                 for top, _, ns in os.walk(self.root) for n in ns]
        with open(self.answers, "w") as f:
            json.dump({"ls-files": ["\0".join(names), 0], "status": [self.dirty, 0],
                       "rev-parse": [os.path.dirname(self.stamp) + "\n", 0]} | self.git_says, f)
        self.lines: list[str] = []
        return fn(self.root, self.git, self.stamp, 2, 60.0, emit=self.lines.append, **kw)

    def green(self) -> dict:
        return self.call(P.green)

    def check(self) -> dict:
        return self.call(P.check)

    def read_stamp(self) -> dict:
        with open(self.stamp) as f:
            return json.load(f)


class Watch(Base):
    def test_read_names_the_watched_files_whose_bytes_a_command_read(self):
        self.moving_access_times()
        names = [self.put("a.txt"), self.put("b.txt"), self.put("c.txt")]
        path = R.bindir(os.path.join(self.tmp, "bin"))
        r = R.run_one({"id": "T0", "cmd": "python -c \"open('b.txt').read(); open('c.txt').read(); "
                                          "import os; os.stat('a.txt')\""},
                      self.root, names, path, self.work, 60.0, watch=("a.txt", "b.txt"))
        self.assertEqual((r["ok"], r["read"]), (True, ["b.txt"]))

    def test_without_watch_a_result_has_no_read_field_and_a_watched_read_is_no_write(self):
        self.moving_access_times()
        names = [self.put("a.txt")]
        path = R.bindir(os.path.join(self.tmp, "bin"))
        cmd = {"id": "T0", "cmd": "python -c \"open('a.txt').read()\""}
        self.assertNotIn("read", R.run_one(cmd, self.root, names, path, self.work, 60.0))
        r = R.run_one(cmd, self.root, names, path, self.work, 60.0, watch=("a.txt",))
        self.assertEqual((r["ok"], r["wrote"], r["read"]), (True, [], ["a.txt"]))

    def test_run_passes_watch_to_every_command(self):
        self.moving_access_times()
        names = [self.put("a.txt")]
        lines: list[str] = []
        R.run(self.root, [{"id": "T0", "cmd": "python -c \"open('a.txt').read()\""},
                          {"id": "T1", "cmd": "python -c pass"}], names, 2, 60.0, emit=lines.append,
              watch=("a.txt",))
        self.assertEqual([json.loads(l)["read"] for l in lines], [["a.txt"], []])


class State(Base):
    def test_bytes_execute_bit_and_link_target(self):
        self.put("a.txt", "one\n")
        os.symlink("a.txt", os.path.join(self.root, "ln"))
        first = P.state(self.root, ["a.txt", "ln"])
        self.assertEqual(first["ln"], "link:a.txt")
        self.put("a.txt", "two\n")
        second = P.state(self.root, ["a.txt", "ln"])
        self.put("a.txt", "two\n", mode=0o755)
        third = P.state(self.root, ["a.txt", "ln"])
        self.assertEqual(len({first["a.txt"], second["a.txt"], third["a.txt"]}), 3)
        self.assertEqual(third["a.txt"], second["a.txt"] + ":x")
        os.remove(os.path.join(self.root, "ln"))
        os.symlink("b.txt", os.path.join(self.root, "ln"))
        self.assertEqual(P.state(self.root, ["ln"]), {"ln": "link:b.txt"})


class Run(Base):
    def test_a_green_run_writes_the_stamp_with_the_ledgers_readers(self):
        self.moving_access_times()
        self.world(READS_LEDGER, LISTS_ONLY, "python -c pass")
        got = self.green()
        self.assertEqual((got["ok"], got["reasons"], got["readers"]), (True, [], ["T0"]))
        stamp = self.read_stamp()
        self.assertEqual(sorted(stamp["files"]), ["a.txt", "snowball-tests.json"])
        self.assertEqual((stamp["ledger"]["bytes"], stamp["readers"], stamp["tests"]), (5, ["T0"], 3))
        self.assertEqual(len(self.lines), 3)
        self.assertEqual(P.read_stamp(self.stamp), stamp)

    def test_a_red_run_writes_no_stamp_and_removes_an_older_one(self):
        self.world("python -c pass")
        self.assertTrue(self.green()["ok"])
        self.world("python -c pass", "python -c \"raise SystemExit(1)\"")
        got = self.green()
        self.assertEqual((got["ok"], got["reasons"], got["failed"]), (False, ["tests_red"], ["T1"]))
        self.assertFalse(os.path.exists(self.stamp))

    def test_a_tree_that_changes_during_the_run_gets_no_stamp(self):
        target = os.path.join(self.root, "a.txt")
        self.world("python -c \"open(%r,'a').write('more')\"" % target)
        got = self.green()
        self.assertEqual((got["ok"], got["reasons"]), (False, ["tree_changed_during_run"]))
        self.assertFalse(os.path.exists(self.stamp))

    def test_a_ledger_row_added_during_the_run_gets_no_stamp(self):
        self.world("python -c \"open(%r,'a').write('row2')\"" % os.path.join(self.root, P.LEDGER))
        self.assertEqual(self.green()["reasons"], ["tree_changed_during_run"])

    def test_where_access_times_do_not_move_readers_is_null_and_check_runs_every_command(self):
        self.world("python -c pass", LEDGER_HAS_NO_BAD)
        saved = R.atime_moves
        R.atime_moves = lambda directory: False
        self.addCleanup(setattr, R, "atime_moves", saved)
        self.assertIsNone(self.green()["readers"])
        self.assertIsNone(self.read_stamp()["readers"])
        self.put(P.LEDGER, "row1\nrow2\n")
        self.assertEqual(self.check(), {"ok": True, "reasons": [], "reran": ["T0", "T1"], "size": None})

    def test_a_brain_without_a_ledger_has_null_readers_and_a_ledger_made_later_runs_every_command(self):
        # No command of the run could read a ledger that was not there, so the run knows no reader of it.
        self.world("python -c pass", "python -c \"import os, sys; sys.exit(os.path.exists('founder-ledger.jsonl') "
                                     "and 'bad' in open('founder-ledger.jsonl').read())\"", ledger=None)
        got = self.green()
        self.assertEqual((got["ok"], got["readers"]), (True, None))
        stamp = self.read_stamp()
        self.assertEqual((stamp["ledger"], stamp["readers"]), (None, None))
        self.assertEqual(self.check(), {"ok": True, "reasons": [], "reran": [], "size": None})
        self.put(P.LEDGER, "row1\n")
        self.assertEqual(self.check(), {"ok": True, "reasons": [], "reran": ["T0", "T1"], "size": None})
        self.put(P.LEDGER, "bad row\n")
        self.assertEqual(self.check(), {"ok": False, "reasons": ["test_failed:T1"], "reran": ["T0", "T1"], "size": None})


class Check(Base):
    def setUp(self):
        super().setUp()
        self.moving_access_times()
        self.world(LEDGER_HAS_NO_BAD, "python -c pass")
        self.assertEqual(self.green()["readers"], ["T0"])

    def test_the_stamped_tree_is_ok_and_nothing_is_run(self):
        self.assertEqual(self.check(), {"ok": True, "reasons": [], "reran": [], "size": None})
        self.assertEqual(self.lines, [])

    def test_no_stamp_and_a_stamp_of_another_form_are_no_green_run(self):
        stamp = self.read_stamp()
        for doc in (None, "{", [], dict(stamp, schema="other/1"), dict(stamp, files=[]),
                    dict(stamp, files={"a.txt": 1}), dict(stamp, ledger={"bytes": "5", "sha256": "x"}),
                    dict(stamp, ledger={"bytes": 5}), dict(stamp, readers="T0"), dict(stamp, readers=[1]),
                    dict(stamp, ledger=None), dict(stamp, ledger=None, readers=[])):
            with self.subTest(doc=doc):
                if doc is None:
                    os.remove(self.stamp)
                else:
                    with open(self.stamp, "w") as f:
                        f.write(doc if isinstance(doc, str) else json.dumps(doc))
                self.assertEqual(self.check(), {"ok": False, "reasons": ["no_green_run"], "reran": [], "size": None})

    def test_a_file_changed_added_removed_or_made_executable_is_named(self):
        self.put("reports/r.json", "{}\n")
        self.assertEqual(self.check()["reasons"], ["tree_changed:reports/r.json"])
        os.remove(os.path.join(self.root, "reports/r.json"))
        self.put("a.txt", "y\n")
        self.assertEqual(self.check()["reasons"], ["tree_changed:a.txt"])
        self.put("a.txt", "x\n", mode=0o755)
        self.assertEqual(self.check()["reasons"], ["tree_changed:a.txt"])
        os.remove(os.path.join(self.root, "a.txt"))
        self.assertEqual(self.check()["reasons"], ["tree_changed:a.txt"])
        self.put("a.txt")
        self.assertTrue(self.check()["ok"])

    def test_uncommitted_work_is_not_ok(self):
        self.dirty = " M a.txt\0"
        self.assertEqual(self.check(), {"ok": False, "reasons": ["uncommitted"], "reran": [], "size": None})

    def test_a_grown_ledger_runs_its_readers_again_and_only_them(self):
        self.put(P.LEDGER, "row1\nrow2\n")
        self.assertEqual(self.check(), {"ok": True, "reasons": [], "reran": ["T0"], "size": None})
        self.assertEqual([json.loads(l)["id"] for l in self.lines], ["T0"])

    def test_a_grown_ledger_no_command_read_runs_nothing(self):
        self.world(LISTS_ONLY, "python -c pass")
        self.assertEqual(self.green()["readers"], [])
        self.put(P.LEDGER, "row1\nrow2\n")
        self.assertEqual(self.check(), {"ok": True, "reasons": [], "reran": [], "size": None})
        self.assertEqual(self.lines, [])

    def test_a_grown_ledger_a_reader_refuses_is_that_readers_failure(self):
        self.put(P.LEDGER, "row1\nbad row\n")
        self.assertEqual(self.check(), {"ok": False, "reasons": ["test_failed:T0"], "reran": ["T0"], "size": None})

    def test_a_ledger_cut_changed_or_removed_is_rewritten(self):
        for text in ("row", "rowX\n", "rowX\nrow2\n", None):
            with self.subTest(text=text):
                if text is None:
                    os.remove(os.path.join(self.root, P.LEDGER))
                else:
                    self.put(P.LEDGER, text)
                self.assertEqual(self.check(), {"ok": False, "reasons": ["ledger_rewritten"], "reran": [], "size": None})

    def test_readers_are_not_run_while_another_reason_stands(self):
        self.put(P.LEDGER, "row1\nbad row\n")
        self.put("a.txt", "y\n")
        self.assertEqual(self.check(), {"ok": False, "reasons": ["tree_changed:a.txt"], "reran": [], "size": None})


class Size(Base):
    """``check``'s reading of the push's size: which result, which two revisions, and what each answer becomes.
    ``push_size.measure`` is replaced (its rules are ``tests/test_push_size.py``'s); ``base_of`` is the real one."""
    SHA = "0123456789abcdef0123456789abcdef01234567"

    def setUp(self):
        super().setUp()
        self.moving_access_times()
        self.world(LEDGER_HAS_NO_BAD, "python -c pass")
        self.green()
        self.result = os.path.join(self.tmp, "result.json")
        with open(self.result, "w") as f:
            json.dump({"state": {"last_accepted_sha": self.SHA}}, f)
        self.calls: list[tuple] = []
        self.answer: object = {"ok": True, "band": "fits", "chars": 5}

    def measure(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer

    def sized(self, result: str | None) -> dict:
        with mock.patch.object(P.PS, "measure", self.measure):
            return self.call(P.check, result=result)

    def test_no_result_named_or_none_there_measures_nothing(self):
        for result in (None, os.path.join(self.tmp, "absent.json")):
            self.assertEqual(self.sized(result), {"ok": True, "reasons": [], "reran": [], "size": None})
        self.assertEqual(self.calls, [])

    def test_without_a_stamp_nothing_is_measured_and_the_usage_names_the_result(self):
        os.remove(self.stamp)
        self.assertEqual(self.sized(self.result), {"ok": False, "reasons": ["no_green_run"], "reran": [], "size": None})
        self.assertEqual(self.calls, [])
        usage = [line for line in P.__doc__.split("\n") if "prepush.py check" in line]
        self.assertEqual([("--result FILE" in line) for line in usage], [True])
        self.assertIn("nothing is measured, when there is no stamp", " ".join(P.__doc__.split()))

    def test_the_measure_is_from_the_result_s_last_accepted_sha_to_head_with_the_result_s_limit(self):
        self.assertEqual(self.sized(self.result), {"ok": True, "reasons": [], "reran": [], "size": self.answer})
        self.assertEqual(self.calls, [((self.root, self.SHA, "HEAD"), {"git": self.git, "result": self.result})])

    def test_a_band_that_does_not_fit_is_the_reason_and_the_readers_are_not_run(self):
        self.put(P.LEDGER, "row1\nrow2\n")
        for name in ("tight", "over"):
            self.answer = {"ok": False, "band": name, "chars": 5}
            self.assertEqual(self.sized(self.result), {"ok": False, "reasons": ["push_size:%s" % name],
                                                       "reran": [], "size": self.answer})
        self.assertEqual(self.lines, [])
        self.answer = {"ok": True, "band": "fits", "chars": 5}
        self.assertEqual(self.sized(self.result)["reran"], ["T0"])

    def test_a_result_or_a_diff_that_cannot_be_read_is_a_reason_not_a_pass(self):
        self.answer = P.PS.Unreadable("diff_failed:128")
        self.assertEqual(self.sized(self.result), {"ok": False, "reasons": ["push_size:diff_failed:128"],
                                                   "reran": [], "size": None})
        with open(self.result, "w") as f:
            f.write("{}")
        self.assertEqual(self.sized(self.result)["reasons"], ["push_size:no_last_accepted_sha"])
        with open(self.result, "w") as f:
            f.write("{")
        self.assertEqual(self.sized(self.result)["reasons"], ["push_size:result_unreadable"])
        self.assertEqual(len(self.calls), 1)

    def test_it_stands_beside_the_other_reasons(self):
        self.answer = {"ok": False, "band": "over", "chars": 5}
        self.put("a.txt", "y\n")
        self.assertEqual(self.sized(self.result)["reasons"], ["tree_changed:a.txt", "push_size:over"])

    def test_the_command_reads_result_and_by_default_push_size_s(self):
        self.answer = {"ok": False, "band": "tight", "chars": 5}
        self.call(lambda *a, **kw: None)
        for argv, saved in ((["check", "--result", self.result], P.PS.RESULT), (["check"], self.result)):
            buf = io.StringIO()
            with mock.patch.object(P.PS, "measure", self.measure), mock.patch.object(P.PS, "RESULT", saved), \
                    contextlib.redirect_stdout(buf):
                code = P.main(argv, root=self.root, git=self.git)
            self.assertEqual((code, json.loads(buf.getvalue().splitlines()[-1])["reasons"]),
                             (1, ["push_size:tight"]), argv)
        self.assertEqual([c[1]["result"] for c in self.calls], [self.result, self.result])


class Main(Base):
    def main(self, *argv: str) -> tuple[int, dict]:
        self.call(lambda *a, **kw: None)  # writes git's answers for the tree as it is
        if argv[0] == "check" and "--result" not in argv:  # no verdict here, whatever this machine holds
            argv += ("--result", os.path.join(self.tmp, "no-result.json"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = P.main(list(argv), root=self.root, git=self.git)
        return code, json.loads(buf.getvalue().splitlines()[-1])

    def test_exit_codes_and_the_stamp_in_the_git_directory(self):
        self.world("python -c pass")
        self.assertEqual(self.main("check"), (1, {"ok": False, "reasons": ["no_green_run"], "reran": [], "size": None}))
        code, got = self.main("run", "-j", "2")
        self.assertEqual((code, got["stamp"]), (0, self.stamp))
        self.assertEqual(self.main("check")[0], 0)
        other = os.path.join(self.tmp, "other.json")
        self.assertEqual(self.main("check", "--stamp", other)[0], 1)
        self.world("python -c \"raise SystemExit(1)\"")
        self.assertEqual(self.main("run")[0], 1)
        os.remove(self.git)
        self.assertEqual(self.main("check"), (2, {"ok": False, "reason": "git_unavailable"}))

    def test_a_git_that_fails_is_unreadable(self):
        self.world("python -c pass")
        self.call(lambda *a, **kw: None)
        with open(self.answers) as f:
            answers = json.load(f)
        answers["rev-parse"] = ["", 128]
        with open(self.answers, "w") as f:
            json.dump(answers, f)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = P.main(["check", "--result", os.path.join(self.tmp, "no-result.json")], root=self.root,
                          git=self.git)
        self.assertEqual((code, json.loads(buf.getvalue())), (2, {"ok": False, "reason": "git_failed:rev-parse:128"}))


def discover(pattern: str) -> str:
    return "python -m unittest discover -s tests -p '%s'" % pattern


def value_test(module: str, value: int, path: str = "") -> str:
    """A test file's text: ``<module>.VALUE`` is ``value``; ``path`` a line that puts ``referee/`` on the path."""
    return ("import unittest\n%simport %s\n\n\nclass T(unittest.TestCase):\n    def test_value(self):\n"
            "        self.assertEqual(%s.VALUE, %d)\n" % (path, module, module, value))


REFEREE_ON_PATH = ("import os, sys\nsys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname("
                   "os.path.abspath(__file__))), 'referee'))\n")
MOD, OTHER, ROOT_TEST = "T0:referee/tests/test_mod.py", "T0:referee/tests/test_other.py", "T0:tests/test_root.py"


class Parts(unittest.TestCase):
    def test_a_command_of_the_grammar_is_one_part_per_discover_step_in_its_directory(self):
        cmd = " && ".join(["cd referee", discover("test_a.py"), discover("test_b*.py"), discover("test_a.py"),
                           "cd ..", discover("test_a.py"), "cd referee", discover("test_c.py")])
        self.assertEqual(P.parts({"id": "T7", "cmd": cmd}), [
            {"id": "T7:referee/tests/test_a.py", "root": "referee", "pattern": "test_a.py",
             "cmd": "cd referee && " + discover("test_a.py")},
            {"id": "T7:referee/tests/test_b*.py", "root": "referee", "pattern": "test_b*.py",
             "cmd": "cd referee && " + discover("test_b*.py")},
            {"id": "T7:tests/test_a.py", "root": ".", "pattern": "test_a.py", "cmd": discover("test_a.py")},
            {"id": "T7:referee/tests/test_c.py", "root": "referee", "pattern": "test_c.py",
             "cmd": "cd referee && " + discover("test_c.py")}])

    def test_any_other_command_is_not_of_the_grammar(self):
        ok = discover("test_a.py")
        for cmd in ("python -c pass", "cd referee", "cd .. && " + ok, "cd referee && cd referee && " + ok,
                    "cd tests && " + ok, ok + " --failfast", ok + "; true", ok + " && true", ok + " || true",
                    " " + ok, ok + " ", discover("a'b"), discover("a\\b"), discover(""),
                    "python -m unittest discover -s tests", "python3 -m unittest discover -s tests -p 'test_a.py'",
                    "python -m unittest discover -s other -p 'test_a.py'", ""):
            with self.subTest(cmd=cmd):
                self.assertIsNone(P.parts({"id": "T7", "cmd": cmd}))


class Quick(Base):
    """``quick``'s rules on a small brain: two modules and a module under them in ``referee/``, a test file of
    each under ``referee/tests`` and one root test that reaches ``referee/mod.py``."""

    def tree(self, *more: str) -> None:
        self.world(" && ".join(["cd referee", discover("test_mod.py"), discover("test_other.py"), "cd ..",
                                discover("test_root.py")]), *more)
        self.put("referee/deep.py", "VALUE = 1\n")
        self.put("referee/mod.py", "from deep import VALUE\n")
        self.put("referee/other.py", "VALUE = 2\n")
        self.put("referee/tests/test_mod.py", value_test("mod", 1))
        self.put("referee/tests/test_other.py", value_test("other", 2))
        self.put("tests/test_root.py", value_test("mod", 1, REFEREE_ON_PATH))

    def quick(self, **kw) -> dict:
        return self.call(P.quick, **kw)

    def since(self, diff: str, others: str = "", **kw) -> dict:
        """``quick --since REV`` where git names ``diff`` as changed since REV and ``others`` as untracked."""
        self.git_says = {"diff": [diff, 0], "ls-files --others": [others, 0]}
        return self.quick(since="REV", **kw)

    def ran(self) -> list[str]:
        return [json.loads(line)["id"] for line in self.lines]

    def test_a_changed_module_runs_the_parts_that_reach_it_and_only_them(self):
        self.tree()
        self.assertTrue(self.green()["ok"])
        with open(self.stamp, "rb") as f:
            stamped = f.read()
        self.put("referee/deep.py", "VALUE = 3\n")  # reached through mod's import, from both test directories
        got = self.quick()
        self.assertEqual(got, {"ok": False, "reasons": ["test_failed:" + MOD, "test_failed:" + ROOT_TEST],
                               "changed": 1, "parts": 3, "selected": [MOD, ROOT_TEST], "unseen": [], "ran": True})
        self.assertEqual(self.ran(), [MOD, ROOT_TEST])
        with open(self.stamp, "rb") as f:
            self.assertEqual(f.read(), stamped)
        self.put("referee/tests/test_mod.py", value_test("mod", 3))
        self.put("tests/test_root.py", value_test("mod", 3, REFEREE_ON_PATH))
        got = self.quick()
        self.assertEqual((got["ok"], got["reasons"], got["changed"], got["selected"]), (True, [], 3, [MOD, ROOT_TEST]))
        with open(self.stamp, "rb") as f:
            self.assertEqual(f.read(), stamped)  # a green quick pass stamps nothing

    def test_run_stamps_only_a_cold_run_and_quick_runs_warm(self):
        # ``run_like_referee``'s cold home is asked for by ``run`` (a command's time is what it bounds) and not by
        # ``quick``. A run that did not get one says which python it had and writes no stamp.
        asked: list = []
        self.tree()
        got = self.green()
        self.assertEqual((got["ok"], got["python"], os.path.exists(self.stamp)), (True, "cold_home", True))
        R.cold_home = lambda home: asked.append(os.path.basename(home))
        got = self.green()
        self.assertEqual((got["ok"], got["reasons"], got["failed"], asked), (False, ["timed_warm"], [], ["python-cold"]))
        self.assertIn(got["python"], ("own", "moved_home"))
        self.assertFalse(os.path.exists(self.stamp))                     # the earlier stamp is gone with it
        self.put("referee/tests/test_other.py", value_test("other", 3))
        self.assertEqual(self.green()["reasons"], ["tests_red", "timed_warm"])
        self.put("referee/tests/test_other.py", value_test("other", 2))
        R.cold_home = lambda home: os.path.realpath(sys.executable)
        self.put("referee/tests/test_other.py", value_test("other", 3))
        got = self.green()
        self.assertEqual((got["reasons"], got["python"]), (["tests_red"], "cold_home"))  # a red run says its python too
        self.put("referee/tests/test_other.py", value_test("other", 2))
        self.assertTrue(self.green()["ok"])
        R.cold_home = lambda home: asked.append(os.path.basename(home))
        self.put("referee/deep.py", "VALUE = 1  # the same\n")
        got = self.quick()
        self.assertEqual((got["ok"], got["ran"], asked), (True, True, ["python-cold"] * 2))  # the two runs' own

    def test_the_stamped_tree_selects_and_runs_nothing(self):
        self.tree()
        self.assertTrue(self.green()["ok"])
        self.assertEqual(self.quick(), {"ok": True, "reasons": [], "changed": 0, "parts": 3, "selected": [],
                                        "unseen": [], "ran": False})
        self.assertEqual(self.lines, [])

    def test_without_a_stamp_and_without_since_nothing_is_known_or_run(self):
        self.tree()
        self.assertEqual(self.quick(), {"ok": False, "reasons": ["no_green_run"], "changed": None, "parts": None,
                                        "selected": [], "unseen": [], "ran": False})
        self.assertEqual(self.lines, [])
        self.assertFalse(os.path.exists(self.stamp))

    def test_a_removed_and_an_added_file_are_changed_paths_of_the_stamp(self):
        self.tree()
        self.assertTrue(self.green()["ok"])
        os.remove(os.path.join(self.root, "referee/other.py"))
        self.put("referee/new.py", "VALUE = 9\n")
        got = self.quick()
        self.assertEqual((got["reasons"], got["changed"], got["selected"], got["unseen"]),
                         (["test_failed:" + OTHER], 2, [OTHER], ["referee/new.py"]))

    def test_since_takes_gits_changed_paths_and_not_the_stamps(self):
        self.tree()
        self.assertTrue(self.green()["ok"])
        self.put("referee/mod.py", "VALUE = 1\n")  # changed against the stamp; git does not name it
        got = self.since("referee/other.py\n")
        self.assertEqual((got["ok"], got["changed"], got["selected"], got["unseen"]), (True, 1, [OTHER], []))
        self.assertEqual(self.ran(), [OTHER])
        os.remove(self.stamp)
        self.assertEqual(self.since("", "referee/tests/test_mod.py\n", plan=True)["selected"], [MOD])

    def test_the_ledger_is_never_a_changed_path(self):
        self.tree()
        got = self.since("%s\nreferee/other.py\n" % P.LEDGER, plan=True)
        self.assertEqual((got["changed"], got["selected"], got["unseen"]), (1, [OTHER], []))
        self.assertTrue(self.green()["ok"])
        self.put(P.LEDGER, "row1\nrow2\n")
        self.assertEqual((self.quick()["changed"], self.lines), (0, []))

    def test_a_changed_path_no_part_reaches_is_unseen(self):
        self.tree()
        self.put("referee/tests/test_unlisted.py", value_test("other", 2))
        got = self.since("a.txt\nreferee/other.py\nsnowball-tests.json\n",
                         "referee/lonely.py\nreferee/tests/test_unlisted.py\n", plan=True)
        self.assertEqual((got["changed"], got["selected"]), (5, [OTHER]))
        self.assertEqual(got["unseen"], ["a.txt", "referee/lonely.py", "referee/tests/test_unlisted.py",
                                         "snowball-tests.json"])

    def test_plan_selects_and_runs_nothing(self):
        self.tree()
        got = self.since("referee/deep.py\n", plan=True)
        self.assertEqual(got, {"ok": True, "reasons": [], "changed": 1, "parts": 3, "selected": [MOD, ROOT_TEST],
                               "unseen": [], "ran": False})
        self.assertEqual(self.lines, [])

    def test_a_command_not_of_the_grammar_runs_whole_every_time(self):
        self.tree("python -c pass", "python -c \"raise SystemExit(1)\"")
        got = self.since("")
        self.assertEqual((got["ok"], got["reasons"], got["parts"], got["selected"], got["ran"]),
                         (False, ["test_failed:T2"], 5, ["T1", "T2"], True))
        self.assertEqual(self.ran(), ["T1", "T2"])

    def test_a_part_that_names_no_test_file_is_selected(self):
        self.tree(discover("test_gone.py"), "cd referee && " + discover("test_root.py"))
        got = self.since("", plan=True)
        self.assertEqual((got["parts"], got["selected"]),
                         (5, ["T1:tests/test_gone.py", "T2:referee/tests/test_root.py"]))

    def test_a_part_runs_in_its_directory_as_its_command_does(self):
        # The root test passes only from the brain's root's tests/, the referee tests only from referee/.
        self.tree()
        got = self.since("referee/deep.py\nreferee/other.py\n")
        self.assertEqual((got["ok"], self.ran()), (True, [MOD, OTHER, ROOT_TEST]))
        self.assertEqual([json.loads(line)["ok"] for line in self.lines], [True, True, True])

    def test_main_takes_since_and_plan_for_quick_only(self):
        self.tree()
        self.git_says = {"diff": ["referee/other.py\n", 0], "ls-files --others": ["", 0]}
        self.call(lambda *a, **kw: {})  # writes git's answers
        for argv, code, selected in ((["quick", "--since", "REV", "--plan"], 0, [OTHER]),
                                     (["quick", "--since", "REV"], 0, [OTHER]),
                                     (["quick"], 1, [])):
            with self.subTest(argv=argv):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    self.assertEqual(P.main(argv + ["--stamp", self.stamp], root=self.root, git=self.git), code)
                self.assertEqual(json.loads(buf.getvalue().splitlines()[-1])["selected"], selected)
        for argv in (["run", "--since", "REV"], ["check", "--plan"]):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    P.main(argv + ["--stamp", self.stamp], root=self.root, git=self.git)
                self.assertEqual(raised.exception.code, 2)
        self.assertFalse(os.path.exists(self.stamp))

    def test_a_rev_git_cannot_read_is_unreadable(self):
        self.tree()
        self.git_says = {"rev-parse": ["", 128], "diff": ["", 0], "ls-files --others": ["", 0]}
        with self.assertRaises(R.Unreadable) as raised:
            self.quick(since="REV")
        self.assertEqual(str(raised.exception), "rev_unreadable")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = P.main(["quick", "--since", "REV", "--stamp", self.stamp], root=self.root, git=self.git)
        self.assertEqual((code, json.loads(buf.getvalue())), (2, {"ok": False, "reason": "rev_unreadable"}))

    def test_since_without_a_git_to_ask_is_unreadable(self):
        self.tree()
        os.remove(self.git)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = P.main(["quick", "--since", "REV", "--stamp", self.stamp], root=self.root, git=self.git)
        self.assertEqual((code, json.loads(buf.getvalue())), (2, {"ok": False, "reason": "git_unavailable"}))


class Skill(unittest.TestCase):
    """tohum/24a "Ajan ve skill tanımları": between ``---`` lines one ``<key>: <value>`` per line, the keys
    ``name`` and ``description`` and no other, then text that is not empty (``agent_run.front_matter``, the one
    reader of the form here). Bound here for every skill of the brain, with one more rule of this brain: ``name``
    is the directory's name."""

    def skills(self) -> list[str]:
        top = os.path.join(ROOT, "skills")
        return sorted(os.listdir(top))

    def parse(self, name: str) -> tuple[dict, str]:
        with open(os.path.join(ROOT, "skills", name, "SKILL.md"), "rb") as f:
            return A.front_matter(f.read(), A.SKILL_KEYS)

    def test_every_skill_has_the_seeds_form(self):
        self.assertIn("push", self.skills())
        for name in self.skills():
            with self.subTest(skill=name):
                head, body = self.parse(name)
                self.assertEqual(sorted(head), ["description", "name"])
                self.assertEqual(head["name"], name)
                self.assertTrue(body.strip())

    def test_the_push_skill_names_commands_that_exist(self):
        _, body = self.parse("push")
        for command in ("run -j 3", "check -j 3", "quick --since <last accepted SHA> -j 3"):
            self.assertIn("python3 tests/prepush.py %s" % command, body)
        for path in ("tests/prepush.py", "tests/run_like_referee.py", "tests/vec_compare.py", "docs/map/brain.md",
                     "referee/ledger/founder.py", "referee/status/depmap.py", "tests/push_size.py",
                     "referee/tests/mutate.py"):
            self.assertTrue(os.path.isfile(os.path.join(ROOT, path)), path)
        for named in ("tests/run_like_referee.py", "tests/vec_compare.py", "docs/map/brain.md",
                      "python -m ledger.founder append", "python -m ledger.founder check",
                      "python -m status.depmap brain", "python3 tests/push_size.py --head",
                      "referee/tests/mutate.py --record", "kayit/mutant-rows"):
            self.assertIn(named, body)
        # the old record copy inside the tree and the sentence that says why it is still there leave together
        self.assertEqual(os.path.lexists(os.path.join(ROOT, "tests/mutant-rows.jsonl")),
                         "`tests/mutant-rows.jsonl` is what is left of the old copy" in " ".join(body.split()))


if __name__ == "__main__":
    unittest.main()
