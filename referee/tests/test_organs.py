"""Test 51 (asama-0/09, P1): the organ runner; an organ that is not accepted has its entry point not called in
``koş`` (asama-1/13 P1 row 1, asama-1/05 step 2).

What is measured: the docker calls a recording stand-in receives (``fake_docker``: it runs the command, so an
entry point that started leaves its file under ``/out``) and the directories under the runs' base. A refusal is
judged by both: no call of any kind, nothing made on disk. The definition's hash is checked against a value
computed by hand in this file (``by_hand``), not by the module's own function alone.

The live path (``Cek``, ``LivePath``): the brain's commit as git objects (``git_store``) through ``loop.cek``'s
assembly into ``pulled``, and the ``kos`` job (``loop.job.run``) on a ``pulled`` artifact, with the same
recording stand-in for docker. ``loop.cek`` carries only what it found at the commit, so an artifact holding an
organ its ``organs.json`` does not accept is written here with ``loop.pulled.write``: that it is refused in
``kos`` is what test 51 asks. Not run here: a real docker, a real brain repository (it holds no organ today),
the workflow file.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loop import cek as C  # noqa: E402
from loop import pulled as P  # noqa: E402
from runner import contained  # noqa: E402
from runner import organs  # noqa: E402
import git_store as S  # noqa: E402
import test_loop_cek as TC  # noqa: E402
import test_loop_kos as LK  # noqa: E402
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


# The organ of the live-path tests, as the brain holds it (``loop.cek``, "Organs"): ``organs/<oid>.json`` names the
# entry and the brain paths of its files.
LIVE_FILES = {"adapters/lint/main.py": MAIN, "adapters/lint/lib/word.txt": b"hello"}


def live_entry(name: str = "said") -> list:
    return ["python3", "/in/adapters/lint/main.py", "/out/%s.txt" % name]


def brain_organ(oid: str = "lint.discover", entry=None, files=None) -> dict:
    """``git_store`` input: one organ's document and its files."""
    files = LIVE_FILES if files is None else files
    doc = {"entry": live_entry() if entry is None else entry, "files": sorted(files)}
    return dict(files, **{"organs/%s.json" % oid: json.dumps(doc).encode()})


class Cek(unittest.TestCase):
    """``loop.cek.assemble``: the organs of the brain commit, read from git objects, in ``pulled``."""

    setUp, assemble, refused = TC.Brain.setUp, TC.Brain.assemble, TC.Brain.refused

    def test_the_commits_organs_are_carried_with_their_hashes(self):
        other = {"fixers/x/run.py": b"print(2)\n"}
        self.brain.update(brain_organ())
        self.brain.update(brain_organ("second", ["python3", "/in/fixers/x/run.py"], other))
        self.brain["adapters/lint/notes.md"] = b"not named by any organ"
        self.assemble()
        got = P.read(self.out)
        self.assertEqual(got.organs, {"lint.discover": {"entry": live_entry(), "files": LIVE_FILES},
                                      "second": {"entry": ["python3", "/in/fixers/x/run.py"], "files": other}})
        self.assertEqual(got.accepted, {"lint.discover": by_hand(live_entry(), LIVE_FILES),
                                        "second": by_hand(["python3", "/in/fixers/x/run.py"], other)})

    def test_a_commit_without_organs_carries_none(self):
        self.assemble()
        got = P.read(self.out)
        self.assertEqual((got.accepted, got.organs), ({}, {}))

    def test_an_entry_of_organs_that_is_no_organ_refuses_the_assembly(self):
        doc = json.dumps({"entry": live_entry(), "files": sorted(LIVE_FILES)}).encode()
        for name, change, want in (
                ("another suffix", {"organs/x.yaml": doc}, "x.yaml"),
                ("no suffix", {"organs/x": doc}, "x"),
                ("not an organ id", {"organs/.x.json": doc}, ".x.json"),
                ("a directory", {"organs/x.json/doc": doc}, "x.json"),
                ("a link", {"organs/x.json": ("120000", b"lint.discover.json")}, "x.json"),
                ("not JSON", {"organs/x.json": b"{"}, "x.json"),
                ("not UTF-8", {"organs/x.json": b"\xff"}, "x.json"),
                ("a third key", {"organs/x.json": json.dumps({"entry": ["a"], "files": [], "image": "i"}).encode()},
                 "x.json"),
                ("no entry", {"organs/x.json": json.dumps({"files": []}).encode()}, "x.json"),
                ("files an object", {"organs/x.json": json.dumps({"entry": ["a"], "files": {}}).encode()}, "x.json"),
                ("a path twice", {"organs/x.json": json.dumps(
                    {"entry": ["a"], "files": ["adapters/lint/main.py"] * 2}).encode()}, "x.json"),
                ("a path the commit lacks", {"organs/x.json": json.dumps(
                    {"entry": ["a"], "files": ["adapters/lint/absent.py"]}).encode()}, "x.json"),
                ("a path that is a directory", {"organs/x.json": json.dumps(
                    {"entry": ["a"], "files": ["adapters/lint"]}).encode()}, "x.json"),
                ("a path that is a link", {"organs/x.json": json.dumps({"entry": ["a"], "files": ["ln"]}).encode(),
                                           "ln": ("120000", b"adapters/lint/main.py")}, "x.json"),
                ("a path not a string", {"organs/x.json": json.dumps({"entry": ["a"], "files": [1]}).encode()},
                 "x.json"),
                ("an entry that is no entry", {"organs/x.json": json.dumps(
                    {"entry": [], "files": ["adapters/lint/main.py"]}).encode()}, "x.json"),
                ("a path not normal", {"organs/x.json": json.dumps(
                    {"entry": ["a"], "files": ["adapters/lint/../lint/main.py"]}).encode()}, "x.json")):
            with self.subTest(name):
                self.brain = dict(TC.brain_files(), **brain_organ())
                self.brain.update(change)
                # the good organ beside it does not make the artifact: every entry of organs/ is taken
                self.assertEqual(self.refused(), ["organ_invalid:%s" % want])

    def test_organs_must_be_a_tree(self):
        for name, change, want in (("a file", {"organs": b"x"}, ["organs_not_directory"]),
                                   ("a link", {"organs": ("120000", b"adapters")}, ["organs_not_directory"]),
                                   ("a gitlink", {"organs": ("160000", b"x")}, ["organs_not_directory"])):
            with self.subTest(name):
                self.brain = dict(TC.brain_files(), **LIVE_FILES)
                self.brain.update(change)
                self.assertEqual(self.refused(), want)


class Capture(LK.RedAs):
    """``RedAs`` that keeps what each run left under its ``/out`` (``kos`` removes an organ's run when it has its
    hashes): ``outs`` holds ``{name: bytes}`` per call, in the calls' order."""

    def __init__(self, script: str = "pkg/red.py") -> None:
        super().__init__(script)
        self.outs: list[dict] = []

    def __call__(self, argv, env, timeout):
        got = super().__call__(argv, env, timeout)
        if argv[:2] == ["docker", "run"]:
            (out,) = [f.split("src=")[1].split(",")[0] for f in argv if f.startswith("type=bind") and "dst=/out" in f]
            kept = {}
            for name in os.listdir(out):
                if os.path.isfile(os.path.join(out, name)):
                    with open(os.path.join(out, name), "rb") as fh:
                        kept[name] = fh.read()
            self.outs.append(kept)
        return got


class LivePath(LK.Base):
    """The ``kos`` job (``loop.job.run("kos", ...)``) on a ``pulled`` artifact with organs."""

    run_kos, results, one = LK.KosJob.run_kos, LK.KosJob.results, LK.KosJob.one

    def organ_calls(self, runner, entry: list) -> list:
        return [c for c in runner.calls if c["argv"][-len(entry):] == entry]

    def plain_calls(self) -> int:
        """The docker runs of this job on the same artifact without organs."""
        self.write_pulled()
        runner = Capture()
        self.assertEqual(self.one(self.run_kos(runner))["index"]["organs"], {})
        shutil.rmtree(self.temp)
        return len(runner.calls)

    def from_cek(self, brain_files: dict) -> tuple:
        """``(the kos job's output, its runner)`` on what ``loop.cek`` assembles from a brain commit holding
        ``brain_files``."""
        shutil.rmtree(self.temp, ignore_errors=True)
        brain, brain_commit = S.store(brain_files)
        objects, commit = TC.target_objects(self.src)
        os.makedirs(os.path.dirname(self.pulled))
        P.write_served(os.path.dirname(self.pulled), ["t1"])
        C.assemble(brain.__getitem__, brain_commit, json.dumps(TC.SUMMARY).encode(), TC.POLICY, "t1",
                   objects.__getitem__, commit, LK.HEADS["brain/state"], LK.state_files(), None, self.pulled)
        runner = Capture()
        return self.run_kos(runner), runner

    def test_the_brains_organ_goes_from_cek_to_its_call_in_kos(self):
        out, runner = self.from_cek(TC.brain_files())
        self.assertEqual(self.one(out)["index"]["organs"], {})
        plain = len(runner.calls)
        out, runner = self.from_cek(dict(TC.brain_files(), **brain_organ()))
        line = self.one(out)
        self.assertEqual((out["ok"], line["done"]), (True, ["D3"]))
        entry = line["index"]["organs"]["lint.discover"]
        self.assertEqual(sorted(line["index"]["organs"]), ["lint.discover"])
        self.assertEqual({k: v for k, v in entry.items() if k != "outputs_sha256"},
                         {"called": True, "definition_sha256": by_hand(live_entry(), LIVE_FILES), "valid": True,
                          "reasons": [], "status": "ok", "exit": 0, "stdout_sha256": hashlib.sha256(b"").hexdigest()})
        self.assertNotEqual(entry["outputs_sha256"], contained.tree_sha256({}))     # it wrote a file
        with open(self.results("index.json")) as fh:
            self.assertEqual(json.load(fh)["organs"], line["index"]["organs"])
        # it ran once, contained, in the unit's image, its files read-only under /in at their brain paths
        (call,) = self.organ_calls(runner, live_entry())
        self.assertTrue(contained.check_argv(call["argv"])["ok"])
        self.assertEqual(call["argv"][-len(live_entry()) - 1], LK.recipe()["env_image"])
        (mount,) = [m for m in call["mounts"] if m["dst"] == "/in"]
        self.assertTrue(mount["ro"])
        self.assertEqual(runner.outs[runner.calls.index(call)], {"said.txt": b"organ said hello"})
        # beside the runs of the same commit without the organ: its red control and its entry point
        self.assertEqual(len(runner.calls) - plain, 2)
        (work,) = [m for m in call["mounts"] if m["dst"] == "/work"]
        self.assertFalse(os.path.exists(work["src"]))            # the run's copy is removed with the run

    def test_only_the_accepted_organ_is_called(self):
        """Test 51 on the live path: carried organs that are not accepted have their entry points not called."""
        plain = self.plain_calls()
        good = {"entry": live_entry("good"), "files": dict(LIVE_FILES)}
        carried = {
            "good": good,
            # not a key of organs.json; its bytes are those of an accepted hash (the good organ's entry differs
            # only in the name of its output)
            "unlisted": {"entry": live_entry("unlisted"), "files": dict(LIVE_FILES)},
            # a key of organs.json, with one byte other than the accepted definition's
            "changed": {"entry": live_entry("changed"), "files": dict(LIVE_FILES, **{"adapters/lint/main.py": MAIN + b"#"})},
            # a key of organs.json whose carried entry is no entry
            "shapeless": {"entry": "python3 /in/adapters/lint/main.py /out/shapeless.txt", "files": dict(LIVE_FILES)},
        }
        accepted = {"good": organs.definition_sha256(good),
                    "changed": organs.definition_sha256({"entry": live_entry("changed"), "files": LIVE_FILES}),
                    "shapeless": organs.definition_sha256({"entry": live_entry("shapeless"), "files": LIVE_FILES}),
                    "absent": "c" * 64}
        self.write_pulled(accepted=accepted, organs=carried)
        runner = Capture()
        index = self.one(self.run_kos(runner))["index"]
        self.assertEqual(index["base"], {"verdict": "verified", "reasons": []})
        self.assertEqual({o: e for o, e in index["organs"].items() if o != "good"},
                         {"unlisted": {"called": False, "reasons": ["organ_not_accepted"]},
                          "changed": {"called": False, "reasons": ["definition_mismatch"]},
                          "shapeless": {"called": False, "reasons": ["definition_invalid"]}})
        self.assertEqual((index["organs"]["good"]["called"], index["organs"]["good"]["valid"]), (True, True))
        # by the docker calls: the good organ's entry ran once; no run carries an /in mount but that one, no
        # run's command is a refused organ's, and nothing wrote a refused organ's output
        (call,) = self.organ_calls(runner, live_entry("good"))
        self.assertEqual([c for c in runner.calls if any(m["dst"] == "/in" for m in c["mounts"])], [call])
        for oid in ("unlisted", "changed", "shapeless"):
            self.assertEqual([c for c in runner.calls if any(oid in a for a in c["argv"][-4:])], [])
        self.assertEqual(sorted(n for kept in runner.outs for n in kept if n.endswith(".txt")), ["good.txt"])
        self.assertEqual(len(runner.calls) - plain, 2)

    def test_an_accepted_set_of_another_shape_runs_nothing(self):
        good = {"entry": live_entry(), "files": dict(LIVE_FILES)}
        for name, accepted in (("a hash that is none", {"lint.discover": "zz"}), ("a list", ["lint.discover"]),
                               ("upper case", {"lint.discover": organs.definition_sha256(good).upper()})):
            with self.subTest(name):
                shutil.rmtree(self.temp, ignore_errors=True)
                self.write_pulled(accepted=accepted, organs={"lint.discover": good})
                runner = Capture()
                with self.assertRaises(LK.J.Unusable) as ctx:
                    self.run_kos(runner)
                self.assertIn("accepted must map organ ids to definition hashes", str(ctx.exception))
                self.assertEqual((runner.calls, runner.docker.other), ([], []))
                self.assertFalse(os.path.lexists(self.results()))

    def test_no_organ_is_called_when_the_base_does_not_stage(self):
        good = {"entry": live_entry(), "files": dict(LIVE_FILES)}
        self.write_pulled(accepted={"lint.discover": organs.definition_sha256(good)}, organs={"lint.discover": good})
        runner = Capture()
        runner.docker.registry = set()
        with contextlib.redirect_stderr(io.StringIO()):
            index = self.one(self.run_kos(runner))["index"]
        self.assertEqual(index["base"]["reasons"], ["image_unavailable"])
        self.assertEqual(index["organs"], {"lint.discover": {"called": False, "reasons": ["image_unavailable"]}})
        self.assertEqual(runner.calls, [])

    def test_a_green_red_control_and_a_failing_entry_are_on_the_line(self):
        fails = {"entry": live_entry(), "files": dict(LIVE_FILES, **{"adapters/lint/main.py": b"import sys\nsys.exit(3)\n"})}
        self.write_pulled(accepted={"lint.discover": organs.definition_sha256(fails)}, organs={"lint.discover": fails})
        entry = self.one(self.run_kos(Capture()))["index"]["organs"]["lint.discover"]
        self.assertEqual((entry["called"], entry["valid"], entry["reasons"], entry["exit"]), (True, True, [], 3))
        self.assertEqual(entry["outputs_sha256"], contained.tree_sha256({}))        # it wrote nothing
        shutil.rmtree(self.temp)
        self.write_pulled(accepted={"lint.discover": organs.definition_sha256(fails)}, organs={"lint.discover": fails})
        entry = self.one(self.run_kos(Capture("pkg/green.py")))["index"]["organs"]["lint.discover"]
        self.assertEqual((entry["called"], entry["valid"], entry["reasons"]), (True, False, ["red_control_green"]))


if __name__ == "__main__":
    unittest.main()
