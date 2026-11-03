"""``tests/mutate.py``, the kept-mutant runner (a session tool, run with test 42's session tools): each outcome
on a small brain made here, the brain left unchanged, and every kept mutant still applicable to today's code."""

from __future__ import annotations

import contextlib
import glob
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import git_store  # noqa: E402
import mutate  # noqa: E402
from profile_tree import write_tree  # noqa: E402

MOD = "def add(a, b):\n    return a + b\n\n\ndef twice(a):\n    return a + a\n"
TEST = ("import os, sys, unittest\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
        "import mod\n\n\nclass T(unittest.TestCase):\n    def test_add(self):\n"
        "        self.assertEqual(mod.add(2, 3), 5)\n")
RED = "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_red(self):\n        self.fail()\n"
SLOW = "import time, unittest\n\n\nclass T(unittest.TestCase):\n    def test_slow(self):\n        time.sleep(30)\n"


def mutant(id_: str, old: str, new: str, tests: list[str] | None = None, file: str = "mod.py") -> dict:
    return {"id": id_, "file": file, "old": old, "new": new, "tests": tests or ["test_mod.py"]}


class Runner(unittest.TestCase):
    def setUp(self):
        self.brain = tempfile.mkdtemp(prefix="t-mutate-")
        self.addCleanup(shutil.rmtree, self.brain, ignore_errors=True)
        write_tree(self.brain, {"referee/mod.py": MOD, "referee/tests/test_mod.py": TEST,
                                "referee/tests/test_red.py": RED, "referee/tests/test_slow.py": SLOW})

    def outcomes(self, mutants: list[dict], timeout: float = 120.0) -> dict[str, str]:
        path = os.path.join(self.brain, "m.json")
        with open(path, "w") as fh:
            json.dump({"mutants": mutants}, fh)
        return {r["id"]: r["outcome"] for r in mutate.run(self.brain, [path], 4, timeout)}

    def test_each_outcome(self):
        got = self.outcomes([
            mutant("killed", "return a + b", "return a - b"),
            mutant("survived", "return a + a", "return 2 * a"),  # twice is not tested
            mutant("stale", "return a * b", "return a"),
            mutant("ambiguous", "return a + ", "return 1 + "),
            mutant("missing_file", "x", "y", file="nope.py"),
            mutant("baseline_red", "return a + b", "return a - b", ["test_mod.py", "test_red.py"]),
        ])
        self.assertEqual(got, {"killed": "killed", "survived": "survived", "stale": "stale",
                               "ambiguous": "ambiguous", "missing_file": "stale", "baseline_red": "baseline_red"})

    def test_a_baseline_over_the_limit_is_baseline_red(self):
        got = self.outcomes([mutant("slow", "return a + b", "return a - b", ["test_slow.py"])], timeout=2.0)
        self.assertEqual(got, {"slow": "baseline_red"})

    def test_the_mutant_runs_in_a_copy(self):
        self.outcomes([mutant("killed", "return a + b", "return a - b")])
        with open(os.path.join(self.brain, "referee", "mod.py")) as fh:
            self.assertEqual(fh.read(), MOD)

    def test_exit_is_zero_only_when_every_mutant_is_killed(self):
        path = os.path.join(self.brain, "m.json")
        for mutants, code in (([mutant("k", "return a + b", "return a - b")], 0),
                              ([mutant("k", "return a + b", "return a - b"),
                                mutant("s", "return a + a", "return 2 * a")], 1)):
            with self.subTest(mutants=[m["id"] for m in mutants]):
                with open(path, "w") as fh:
                    json.dump({"mutants": mutants}, fh)
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    self.assertEqual(mutate.main(["--brain", self.brain, "-j", "2", path]), code)
                rows = [json.loads(line) for line in out.getvalue().splitlines()]
                self.assertEqual([(r["file"], r["id"]) for r in rows], [("m.json", m["id"]) for m in mutants])

    def test_a_mutant_over_the_limit_is_a_timeout(self):
        slow = "import mod, time\nif mod.add(2, 3) != 5:\n    time.sleep(30)\n"
        write_tree(self.brain, {"referee/tests/test_hang.py": TEST.replace("import mod\n", "import mod\n" + slow)})
        got = self.outcomes([mutant("hang", "return a + b", "return a - b", ["test_hang.py"])], timeout=5.0)
        self.assertEqual(got, {"hang": "timeout"})

    def test_malformed_files(self):
        good = mutant("k", "return a + b", "return a - b")
        for label, data in (("no list", {}), ("empty", {"mutants": []}), ("extra field", {"mutants": [good | {"x": 1}]}),
                            ("no change", {"mutants": [good | {"new": good["old"]}]}),
                            ("no tests", {"mutants": [good | {"tests": []}]}),
                            ("duplicate id", {"mutants": [good, good]})):
            with self.subTest(label=label):
                path = os.path.join(self.brain, "bad.json")
                with open(path, "w") as fh:
                    json.dump(data, fh)
                with self.assertRaises(ValueError):
                    mutate.load(path)


class Select(unittest.TestCase):
    """``--touched``'s rule: which mutants a set of changed paths selects, on a small brain made here."""

    TREE = {
        "referee/pkg/__init__.py": "",
        "referee/pkg/util.py": "def one():\n    return 1\n",
        "referee/mod.py": "from pkg import util\n\n\ndef add(a, b):\n    return a + b + util.one() - 1\n",
        "referee/other.py": "def sub(a, b):\n    return a - b\n",
        "referee/data.json": "{}\n",
        "referee/helper.py": "VALUE = 6\n",
        "referee/tests/helper.py": "VALUE = 5\n",
        "referee/tests/test_mod.py": TEST.replace("import mod\n", "import helper\nimport mod\n"),
        "referee/tests/test_other.py": "import other\n",
        "referee/tests/mutants/a.json": {"mutants": [
            mutant("on_mod", "return a + b", "return a - b"),
            mutant("on_other", "return a - b", "return a + b", ["test_other.py"], "other.py"),
            mutant("on_other_by_glob", "return a - b", "return a * b", ["test_o*.py"], "other.py"),
            mutant("not_imported", "return a - b", "return a", ["test_mod.py"], "other.py")]},  # e.g. a subprocess
        "referee/tests/mutants/b.json": {"mutants": [mutant("b_on_other", "return a - b", "return b",
                                                            ["test_other.py"], "other.py")]},
    }
    BY_TEST = ["on_mod", "not_imported"]
    ON_OTHER = ["on_other", "on_other_by_glob", "not_imported", "b_on_other"]

    def setUp(self):
        self.brain = tempfile.mkdtemp(prefix="t-select-")
        self.addCleanup(shutil.rmtree, self.brain, ignore_errors=True)
        write_tree(self.brain, self.TREE)

    def selected(self, changed: set[str]) -> list[str]:
        files = sorted(glob.glob(os.path.join(self.brain, "referee", "tests", "mutants", "*.json")))
        items = [(path, m) for path in files for m in mutate.load(path)]
        return [m["id"] for _, m in mutate.select(self.brain, items, changed)]

    def test_nothing_changed_selects_nothing(self):
        self.assertEqual(self.selected(set()), [])

    def test_each_path_a_mutant_is_concerned_by(self):
        for rel, ids in (("referee/mod.py", self.BY_TEST),                 # its file, imported by its test
                         ("referee/other.py", self.ON_OTHER),
                         ("referee/tests/test_mod.py", self.BY_TEST),       # its test file
                         ("referee/tests/helper.py", self.BY_TEST),         # imported by its test
                         ("referee/pkg/util.py", self.BY_TEST),             # imported by an imported file
                         ("referee/pkg/__init__.py", self.BY_TEST),         # the package run first
                         ("referee/tests/mutants/b.json", ["b_on_other"]),  # its mutant file
                         ("referee/helper.py", []),                         # shadowed by tests/helper.py
                         ("referee/data.json", []),                         # not Python: stated out of scope
                         ("tests/test_mod.py", [])):                        # the brain's root tests: not referee's
            with self.subTest(rel=rel):
                self.assertEqual(self.selected({rel}), ids)

    def test_a_module_the_tree_no_longer_has_is_reached_by_its_name(self):
        for old, new in (("referee/tests/helper.py", "referee/tests/helper2.py"),  # its shadow is not taken
                         ("referee/pkg/util.py", "referee/pkg/util2.py")):
            with self.subTest(removed=old):
                write_tree(self.brain, self.TREE)
                os.rename(os.path.join(self.brain, old), os.path.join(self.brain, new))
                self.assertEqual(self.selected({old}), self.BY_TEST)
                self.assertEqual(self.selected({new}), [])
                os.remove(os.path.join(self.brain, new))

    def test_a_file_that_does_not_parse_is_selected_by_its_own_path(self):
        write_tree(self.brain, {"referee/other.py": "def (\n", "referee/tests/helper.py": "def (\n"})
        self.assertEqual(self.selected({"referee/other.py"}), self.ON_OTHER)
        self.assertEqual(self.selected({"referee/tests/helper.py"}), self.BY_TEST)


class Touched(unittest.TestCase):
    """``touched``, git's half of ``--touched``, against a fake ``git`` (the referee's sandbox has none): what it
    asks git and how it joins the answers. Real git's answers to the same questions are not tested here."""

    def setUp(self):
        self.bin = tempfile.mkdtemp(prefix="t-touched-")
        self.addCleanup(shutil.rmtree, self.bin, ignore_errors=True)
        self.brain = tempfile.mkdtemp(prefix="t-touched-brain-")
        self.addCleanup(shutil.rmtree, self.brain, ignore_errors=True)
        write_tree(self.brain, Select.TREE)
        patcher = mock.patch.dict(os.environ, {"PATH": self.bin + os.pathsep + os.environ.get("PATH", "")})
        patcher.start()
        self.addCleanup(patcher.stop)

    def fake(self, diff: bytes, others: bytes, exits: dict | None = None) -> None:
        git_store.install_git(self.bin, {}, exits=exits,
                              outputs={"rev-parse": b"1" * 40 + b"\n", "diff": diff, "ls-files": others})

    def test_the_questions_and_the_union_of_their_answers(self):
        self.fake(b"referee/mod.py\nreferee/pkg/util.py\n", b"referee/tests/mutants/c.json\n")
        self.assertEqual(mutate.touched(self.brain, "REV"),
                         {"referee/mod.py", "referee/pkg/util.py", "referee/tests/mutants/c.json"})
        self.assertEqual([c["argv"] for c in git_store.calls(self.bin)], [
            ["-C", self.brain, "rev-parse", "--verify", "--quiet", "REV^{commit}"],
            ["-C", self.brain, "diff", "--name-only", "--no-renames", "REV", "--"],
            ["-C", self.brain, "ls-files", "--others", "--exclude-standard"]])

    def test_a_rev_git_cannot_read_raises(self):
        for failing in ("rev-parse", "diff", "ls-files"):
            with self.subTest(failing=failing):
                self.fake(b"", b"", exits={failing: 128})
                with self.assertRaises(ValueError):
                    mutate.touched(self.brain, "REV")

    def test_main_runs_only_the_selected(self):
        self.fake(b"referee/mod.py\n", b"")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = mutate.main(["--brain", self.brain, "-j", "2", "--touched", "REV"])
        rows = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual([(r["id"], r["outcome"]) for r in rows], [("on_mod", "killed"), ("not_imported", "survived")])
        self.assertEqual(code, 1)
        self.assertIn("1 changed paths, 2 mutants selected", err.getvalue())


class Kept(unittest.TestCase):
    def test_every_kept_mutant_is_well_formed_and_applies_to_todays_code(self):
        files = sorted(glob.glob(os.path.join(mutate.BRAIN, "referee", "tests", "mutants", "*.json")))
        self.assertTrue(files)
        for path in files:
            for m in mutate.load(path):
                with self.subTest(file=os.path.basename(path), id=m["id"]):
                    self.assertIsNone(mutate.applicable(mutate.BRAIN, m))
                    for pattern in m["tests"]:
                        self.assertTrue(glob.glob(os.path.join(mutate.BRAIN, "referee", "tests", pattern)), pattern)


if __name__ == "__main__":
    unittest.main()
