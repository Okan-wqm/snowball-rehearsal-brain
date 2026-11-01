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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
