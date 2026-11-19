"""Test 51 (asama-0/09, P1): the organ runner; an organ that is not accepted has its entry point not called in
``koş`` (asama-1/13 P1 row 1, asama-1/05 step 2).

What is measured: the docker calls a recording stand-in receives (``fake_docker``: it runs the command, so an
entry point that started leaves its file under ``/out``) and the directories under the runs' base. A refusal is
judged by both: no call of any kind, nothing made on disk. The definition's hash is checked against a value
computed by hand in this file (``by_hand``), not by the module's own function alone.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from runner import contained  # noqa: E402
from runner import organs  # noqa: E402
from fake_docker import FakeDocker  # noqa: E402
from test_contained import IMAGE, PROBE, operating, snapshot, writable_base  # noqa: E402

# The organ of these tests: its entry point writes, to the path it is given, the word its other file holds.
MAIN = (b"import os, sys\n"
        b"here = os.path.dirname(os.path.abspath(sys.argv[0]))\n"
        b"with open(os.path.join(here, 'lib', 'word.txt')) as fh:\n"
        b"    word = fh.read()\n"
        b"with open(sys.argv[1], 'w') as fh:\n"
        b"    fh.write('organ said ' + word)\n")
ENTRY = ["python3", "/in/main.py", "/out/said.txt"]
RED = ["python3", "/work/probe.py", "exit", "1"]


def definition(**over) -> dict:
    d = {"entry": list(ENTRY), "files": {"main.py": MAIN, "lib/word.txt": b"hello"}}
    d.update(over)
    return d


def by_hand(entry: list, files: dict) -> str:
    """The module docstring's hash rule, written out with no call of the module."""
    names = sorted(files)
    text = '{"entry":[%s],"files":{%s}}' % (
        ",".join(json.dumps(a) for a in entry),
        ",".join('%s:"%s"' % (json.dumps(n), hashlib.sha256(files[n]).hexdigest()) for n in names))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class HashTest(unittest.TestCase):
    def test_known_answer(self):
        d = definition()
        self.assertEqual(organs.definition_sha256(d), by_hand(ENTRY, d["files"]))
        # the same bytes, fixed: a change of the rule shows here even if by_hand were changed with it
        self.assertEqual(organs.definition_sha256({"entry": ["a"], "files": {"f": b"x"}}),
                         hashlib.sha256(b'{"entry":["a"],"files":{"f":"2d711642b726b04401627ca9fbac32f5c8530fb1903cc4'
                                        b'db02258717921a4881"}}').hexdigest())

    def test_the_order_files_are_given_in_does_not_enter(self):
        d = definition()
        turned = dict(d, files=dict(reversed(list(d["files"].items()))))
        self.assertNotEqual(list(turned["files"]), list(d["files"]))
        self.assertEqual(organs.definition_sha256(turned), organs.definition_sha256(d))

    def test_every_part_enters(self):
        base = organs.definition_sha256(definition())
        seen = {base}
        for name, changed in CHANGES.items():
            with self.subTest(name):
                got = organs.definition_sha256(changed)
                self.assertNotIn(got, seen)
                seen.add(got)

    def test_another_shape_has_no_hash(self):
        for name, bad in INVALID.items():
            with self.subTest(name), self.assertRaises(organs.OrganError):
                organs.definition_sha256(bad)


# Definitions that differ from ``definition()`` in one part each; every one is a definition (it has a hash).
CHANGES = {
    "file byte": definition(files={"main.py": MAIN + b"#", "lib/word.txt": b"hello"}),
    "other file byte": definition(files={"main.py": MAIN, "lib/word.txt": b"hellO"}),
    "file added": definition(files={"main.py": MAIN, "lib/word.txt": b"hello", "extra.py": b""}),
    "file removed": definition(files={"main.py": MAIN}),
    "file renamed": definition(files={"main.py": MAIN, "lib/word2.txt": b"hello"}),
    "contents swapped": definition(files={"main.py": b"hello", "lib/word.txt": MAIN}),
    "entry argument": definition(entry=["python3", "/in/main.py", "/out/other.txt"]),
    "entry order": definition(entry=["python3", "/out/said.txt", "/in/main.py"]),
    "entry longer": definition(entry=ENTRY + ["x"]),
    "entry shorter": definition(entry=ENTRY[:2]),
}

INVALID = {
    "not an object": ["python3"],
    "no files": {"entry": ENTRY},
    "no entry": {"files": {}},
    "a third key": dict(definition(), image=IMAGE),
    "entry empty": definition(entry=[]),
    "entry a string": definition(entry="python3 /in/main.py"),
    "entry holds a number": definition(entry=["python3", 1]),
    "entry holds an empty string": definition(entry=["python3", ""]),
    "files a list": definition(files=["main.py"]),
    "file content text": definition(files={"main.py": "text"}),
    "path absolute": definition(files={"/main.py": MAIN}),
    "path leaves": definition(files={"../main.py": MAIN}),
    "path not normal": definition(files={"lib/../main.py": MAIN}),
    "path dot": definition(files={".": MAIN}),
    "path empty": definition(files={"": MAIN}),
    "path not a string": definition(files={1: MAIN}),
    "file on the way of a file": definition(files={"lib": MAIN, "lib/word.txt": b"hello"}),
}


OWN = object()      # "the test's own accepted set" as a default, so that ``None`` can be passed as a bad one


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.base = writable_base()
        self.addCleanup(shutil.rmtree, self.base, True)
        self.tree = os.path.join(self.base, "tree")
        os.mkdir(self.tree)
        shutil.copy(PROBE, os.path.join(self.tree, "probe.py"))
        self.docker = FakeDocker(images=[IMAGE])
        self.accepted = {"lint.discover": organs.definition_sha256(definition())}

    def call(self, organ_id, given, accepted=OWN, red=RED) -> dict:
        return organs.call(self.accepted if accepted is OWN else accepted, organ_id, given,
                           {"image": IMAGE, "tree": self.tree}, red, operating(), runner=self.docker,
                           base=self.base)

    def nothing_started(self) -> None:
        """No docker call of any kind was made, and nothing was made under the runs' base."""
        self.assertEqual((self.docker.calls, self.docker.other), ([], []))
        self.assertEqual(os.listdir(self.base), ["tree"])
        self.assertEqual(os.listdir(self.tree), ["probe.py"])


class RefusedTest(Base):
    def refused(self, reason: str, organ_id, given, accepted=OWN) -> None:
        self.assertEqual(self.call(organ_id, given, accepted),
                         {"organ_id": organ_id, "called": False, "reasons": [reason]})
        self.nothing_started()

    def test_an_organ_that_is_not_accepted_is_not_called(self):
        good = definition()
        self.refused("organ_not_accepted", "fixer.range", good)
        self.refused("organ_not_accepted", "lint.discover", good, accepted={})
        self.refused("organ_not_accepted", "lint.discove", good)      # no prefix, no other spelling
        self.refused("organ_not_accepted", "Lint.Discover", good)
        for other in (None, 0, ["lint.discover"], ("lint.discover",), b"lint.discover"):
            with self.subTest(other):
                self.refused("organ_not_accepted", other, good)

    def test_an_accepted_id_with_other_bytes_is_not_called(self):
        for name, changed in CHANGES.items():
            with self.subTest(name):
                self.refused("definition_mismatch", "lint.discover", changed)

    def test_another_organs_accepted_hash_does_not_accept(self):
        other = CHANGES["file byte"]
        accepted = dict(self.accepted, **{"fixer.range": organs.definition_sha256(other)})
        self.refused("definition_mismatch", "fixer.range", definition(), accepted)
        self.refused("definition_mismatch", "lint.discover", other, accepted)

    def test_a_definition_of_another_shape_is_not_called(self):
        for name, bad in INVALID.items():
            with self.subTest(name):
                self.refused("definition_invalid", "lint.discover", bad)

    def test_an_accepted_set_of_another_shape_starts_nothing(self):
        good = self.accepted["lint.discover"]
        for name, bad in {"a list": ["lint.discover"], "none": None, "hash upper": {"lint.discover": good.upper()},
                          "hash short": {"lint.discover": good[:63]}, "hash long": {"lint.discover": good + "0"},
                          "hash with a newline": {"lint.discover": good + "\n"},
                          "hash a definition": {"lint.discover": definition()},
                          "another entry bad": dict(self.accepted, other="x"),
                          "id empty": dict(self.accepted, **{"": good}),
                          "id not a string": {**self.accepted, 1: good}}.items():
            with self.subTest(name):
                with self.assertRaises(organs.OrganError):
                    self.call("lint.discover", definition(), bad)
                self.nothing_started()


class CalledTest(Base):
    def test_an_accepted_organ_s_entry_point_runs_contained(self):
        got = self.call("lint.discover", definition())
        self.assertEqual((got["organ_id"], got["called"], got["valid"], got["reasons"]),
                         ("lint.discover", True, True, []))
        self.assertEqual(got["definition_sha256"], by_hand(ENTRY, definition()["files"]))
        self.assertEqual(sorted(got), ["called", "definition_sha256", "organ_id", "reasons", "red_control", "result",
                                       "valid"])
        self.assertEqual(self.docker.other, [])
        control, entry = self.docker.calls                       # two runs: the red control, then the entry point
        for run in (control, entry):
            self.assertTrue(contained.check_argv(run["argv"])["ok"])
        # the command is the accepted entry, as written, in the job's image; the control's is the red command
        self.assertEqual(entry["argv"][-len(ENTRY) - 1:], [IMAGE] + ENTRY)
        self.assertEqual(control["argv"][-len(RED) - 1:], [IMAGE] + RED)
        # the entry point's /in is read-only and holds the definition's files, those bytes and nothing else
        (mount,) = [m for m in entry["mounts"] if m["dst"] == "/in"]
        self.assertTrue(mount["ro"])
        self.assertEqual(mount["src"], os.path.join(got["result"]["run_root"], "in"))
        self.assertEqual(snapshot(mount["src"]), {"main.py": hashlib.sha256(MAIN).hexdigest(), "lib": "dir",
                                                  os.path.join("lib", "word.txt"): hashlib.sha256(b"hello").hexdigest()})
        self.assertEqual([m["dst"] for m in control["mounts"]], ["/work", "/out"])   # the control has no organ files
        # it ran: its output is in the run's /out, hashed outside
        with open(os.path.join(got["result"]["run_root"], "out", "said.txt"), "rb") as fh:
            said = fh.read()
        self.assertEqual(said, b"organ said hello")
        self.assertEqual(got["result"]["outputs"]["said.txt"]["sha256"], hashlib.sha256(said).hexdigest())
        self.assertEqual((got["result"]["exit"], got["red_control"]["exit"]), (0, 1))
        # the staged copy is gone: the base holds the tree and the two runs' directories
        roots = sorted(os.path.basename(r[k]["run_root"]) for r, k in ((got, "red_control"), (got, "result")))
        self.assertEqual(sorted(os.listdir(self.base)), sorted(["tree"] + roots))

    def test_the_tree_and_env_of_the_job_reach_both_runs(self):
        with open(os.path.join(self.tree, "seen.txt"), "wb") as fh:
            fh.write(b"tree file")
        got = organs.call(self.accepted, "lint.discover", definition(),
                          {"image": IMAGE, "tree": self.tree, "env": {"LANG": "C.UTF-8"}}, RED, operating(),
                          runner=self.docker, base=self.base)
        self.assertTrue(got["valid"])
        for run, report in zip(self.docker.calls, (got["red_control"], got["result"])):
            self.assertEqual(run["container_env"], {"LANG": "C.UTF-8"})
            with open(os.path.join(report["run_root"], "work", "seen.txt"), "rb") as fh:
                self.assertEqual(fh.read(), b"tree file")

    def test_a_green_red_control_is_carried_as_the_run_s_verdict(self):
        got = self.call("lint.discover", definition(), red=["python3", "/work/probe.py", "exit", "0"])
        self.assertEqual((got["called"], got["valid"], got["reasons"]), (True, False, ["red_control_green"]))
        self.assertEqual(len(self.docker.calls), 2)

    def test_a_failing_entry_point_is_a_result_not_a_refusal(self):
        d = definition(files={"main.py": b"import sys\nsys.exit(3)\n", "lib/word.txt": b"hello"})
        got = self.call("lint.discover", d, accepted={"lint.discover": organs.definition_sha256(d)})
        self.assertEqual((got["called"], got["valid"], got["result"]["exit"]), (True, True, 3))

    def test_the_staged_copy_is_removed_when_the_run_refuses(self):
        with self.assertRaises(contained.ContainmentError):
            organs.call(self.accepted, "lint.discover", definition(), {"image": "python:3.12", "tree": self.tree},
                        RED, operating(), runner=self.docker, base=self.base)
        self.assertEqual(self.docker.calls, [])
        self.assertEqual([n for n in os.listdir(self.base) if n.startswith("snowball-organ-")], [])


if __name__ == "__main__":
    unittest.main()
