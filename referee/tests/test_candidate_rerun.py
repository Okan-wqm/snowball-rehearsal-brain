"""Test 57 (P1 MF11, tohum/26j): ``koş`` reruns a run-time candidate before the gate, as it runs a ready candidate
(three lint runs, a test run, the red control), and a candidate without a rerun does not reach the gate.

What is measured:

- ``Unit`` (``runner.candidate_rerun`` alone): which paths of the kept outputs are packages and what an id held
  twice is, the diff of a package over a table of documents, ``rerun``'s order and its one call per id on a store
  ``organ_output.keep`` wrote, and ``reran``'s every reason (no package, no index, no entry, one byte of the
  package changed, each other verdict, each of the three files missing or a link);
- ``Live`` (the jobs, as test 56 runs them: ``loop.job.run("kos")`` on a ``pulled`` artifact carrying accepted
  organs whose entry points write the packages and the same diffs as ready candidates, then
  ``loop.job.run("yaz")``): the packages at ``candidates/<id>/package.json`` of the results, the rerun's entry and
  files against the ready candidate's of the same diff, the count of contained runs and of red controls, MF8's
  command (``gate.check decide``) on the rerun's files, ``yaz``'s line, and that line again after the rerun or one
  byte of the package was changed in the results.

Not run here: a real docker, the artifact's upload and download, a gate decision of the loop on a run-time
candidate (nothing hands one to ``loop.decide`` yet, MF12), a brain that holds an organ.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loop import job as J  # noqa: E402
from profile import derive as D  # noqa: E402
from runner import candidate_rerun as CR  # noqa: E402
from runner import contained  # noqa: E402
from runner import organ_output as OO  # noqa: E402
from runner import organs  # noqa: E402
from test_kos import BREAKS_TEST, FINDING, GOOD, diff as kos_diff  # noqa: E402
from test_loop_kos import RedAs, candidate  # noqa: E402
from test_organ_output import LiveBase, sha  # noqa: E402


def package(diff: bytes | None, **more) -> bytes:
    """A package (tohum/26a: ``{finding, diff, organ_ids, definition_sha256[]}``) with ``diff`` (none when ``None``)."""
    doc = dict({"finding": FINDING, "organ_ids": ["lint.discover"], "definition_sha256": []}, **more)
    if diff is not None:
        doc["diff"] = diff.decode()
    return json.dumps(doc).encode() + b"\n"


class Unit(unittest.TestCase):
    def setUp(self) -> None:
        self.out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.out)

    def read(self, path: str):
        return D._read_regular(self.out, path)

    def keep(self, files: dict) -> str:
        """``files`` kept as an organ's output by ``organ_output.keep``; its hash."""
        src = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, src)
        for path, data in files.items():
            os.makedirs(os.path.dirname(os.path.join(src, path)), exist_ok=True)
            with open(os.path.join(src, path), "wb") as fh:
                fh.write(data)
        kept = OO.keep(contained.hash_tree(src), lambda path: D._read_regular(src, path), self.out)
        self.assertEqual(kept["reasons"], [], kept)
        return kept["sha256"]

    def test_the_packages_of_an_output_are_the_files_at_the_page_s_path(self):
        output = self.keep({
            "candidates/c1/package.json": b"1", "candidates/c 2\n/package.json": b"2",
            "candidates/package.json": b"no id", "candidates/a/b/package.json": b"two parts",
            "x/candidates/c4/package.json": b"not at the root", "candidates/c5/package.json\n": b"a newline",
            "candidates/c6/package.jsonx": b"longer", "candidates/c1/finding.json": b"another file",
            "candidates/c3/package.json": b"1", "package.json": b"no directory"})
        self.assertEqual(CR.found([output], self.read), {"c1": b"1", "c 2\n": b"2", "c3": b"1"})
        self.assertEqual(CR.found([self.keep({"findings.json": b"[]"})], self.read), {})
        self.assertEqual(CR.found([], self.read), {})
        self.assertEqual(CR.path("c1"), "candidates/c1/package.json")
        self.assertEqual(CR.key(b"1"), "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b")

    def test_an_id_two_outputs_hold_with_different_bytes_is_no_package(self):
        one = self.keep({"candidates/same/package.json": b"1", "candidates/twice/package.json": b"1",
                         "candidates/thrice/package.json": b"1", "candidates/back/package.json": b"1"})
        two = self.keep({"candidates/same/package.json": b"1", "candidates/twice/package.json": b"2",
                         "candidates/thrice/package.json": b"2", "candidates/back/package.json": b"2", "x": b"x"})
        three = self.keep({"candidates/thrice/package.json": b"3", "candidates/back/package.json": b"1",
                           "candidates/own/package.json": b"3"})
        want = {"same": b"1", "twice": None, "thrice": None, "back": None, "own": b"3"}
        for outputs in ([one, two, three], [three, two, one], [two, three, one], [one, three, two]):
            self.assertEqual(CR.found(outputs, self.read), want)
        self.assertEqual(CR.found([one, one], self.read)["twice"], b"1")

    def test_the_diff_of_a_package(self):
        table = [(b'{"diff": "a\\nb\\n"}', b"a\nb\n"), (b'{"diff": ""}', b""), (b'{"diff": "\\u00e9"}', b"\xc3\xa9"),
                 (b' {"x": 1, "diff": "d", "finding": []}\n', b"d"), (package(GOOD), GOOD),
                 (b"", None), (b"{}", None), (b'{"diff": null}', None), (b'{"diff": 1}', None),
                 (b'{"diff": ["a"]}', None), (b'{"diff": {"a": 1}}', None), (b'["diff"]', None), (b'"diff"', None),
                 (b'{"diff": "a"', None), (b'{"diff": "\xff"}', None), (b'{"diff": "\\ud800"}', None),
                 (b'{"Diff": "a"}', None), (b'{"diff": "a"} x', None),
                 (b'{"diff": "a", "x": ' + b"[" * 100000 + b"]" * 100000 + b"}", None)]
        for doc, want in table:
            with self.subTest(doc[:40]):
                self.assertEqual(CR.diff(doc), want)

    def test_rerun_calls_run_once_for_each_id_in_the_order_of_the_ids(self):
        a, b, c = package(GOOD), package(None), package(BREAKS_TEST)
        first = self.keep({"candidates/2/package.json": a, "candidates/1/package.json": b, "findings.json": c,
                           "candidates/twice/package.json": a})
        second = self.keep({"candidates/3/package.json": c, "candidates/other/package.json": a,
                            "candidates/twice/package.json": c})
        third = self.keep({"findings.json": b"[]"})
        calls: list = []

        def run(*args):
            calls.append(args)
            return {"n": len(calls), "package_sha256": "run's own is not the entry's"}

        want = [("1", b, None), ("2", a, GOOD), ("3", c, BREAKS_TEST), ("other", a, GOOD), ("twice", None, None)]
        for outputs in ([first, second, third], [third, second, first]):
            del calls[:]
            got = CR.rerun(outputs, self.read, run)
            self.assertEqual(calls, want)
            self.assertEqual(list(got.items()), [
                (cid, {"n": n + 1, "package_sha256": None if pkg is None else sha(pkg)})
                for n, (cid, pkg, _) in enumerate(want)])
        del calls[:]
        self.assertEqual((CR.rerun([third], self.read, run), CR.rerun([], self.read, run), calls), ({}, {}, []))

    def test_rerun_runs_nothing_when_a_kept_output_is_not_read_back(self):
        first = self.keep({"candidates/1/package.json": package(GOOD)})
        second = self.keep({"candidates/2/package.json": package(BREAKS_TEST)})
        os.remove(os.path.join(self.out, OO.STORE, sha(package(BREAKS_TEST))))
        calls: list = []
        for outputs in ([first, second], [second, first], [first, "0" * 64], [first, None]):
            with self.subTest(outputs):
                with self.assertRaises(OO.Refused):
                    CR.rerun(outputs, self.read, lambda *a: calls.append(a))
        self.assertEqual(calls, [])

    def write(self, cid: str, pkg: bytes | None, files=CR.FILES) -> None:
        """The results with ``pkg`` as ``cid``'s package (none when ``None``) and ``files`` as its rerun's."""
        for part in ("r", "candidates"):
            shutil.rmtree(os.path.join(self.out, part), ignore_errors=True)
        os.makedirs(os.path.join(self.out, "r", cid))
        for f in files:
            with open(os.path.join(self.out, "r", cid, f), "wb") as fh:
                fh.write(f.encode())
        if pkg is not None:
            os.makedirs(os.path.join(self.out, "candidates", cid))
            with open(os.path.join(self.out, "candidates", cid, "package.json"), "wb") as fh:
                fh.write(pkg)

    def refused(self, index, cid="c1") -> list:
        with self.assertRaises(CR.NotRerun) as caught:
            CR.reran(index, cid, self.read)
        return caught.exception.reasons

    def entry(self, pkg: bytes, verdict="verified") -> dict:
        return {"verdict": verdict, "reasons": [], "package_sha256": sha(pkg)}

    def test_reran_hands_out_the_package_and_the_three_files_of_a_verified_rerun(self):
        pkg = package(GOOD)
        self.write("c1", pkg)
        self.assertEqual(CR.FILES, ("cand.jsonl", "checks.json", "hashes.json"))
        self.assertEqual(CR.reran({"reruns": {"c1": self.entry(pkg)}}, "c1", self.read), (
            pkg, {"cand.jsonl": b"cand.jsonl", "checks.json": b"checks.json", "hashes.json": b"hashes.json"}))

    def test_reran_refuses_a_candidate_whose_package_is_not_in_the_results(self):
        pkg = package(GOOD)
        index = {"reruns": {"c1": self.entry(pkg), "..": self.entry(pkg), ".": self.entry(pkg),
                            "a/b": self.entry(pkg), "": self.entry(pkg), "../candidates/c1": self.entry(pkg)}}
        self.write("c1", None)
        self.assertEqual(self.refused(index), ["package_missing"])
        os.makedirs(os.path.join(self.out, "candidates", "c1", "package.json"))        # a directory is no package
        self.assertEqual(self.refused(index), ["package_missing"])
        self.write("c1", pkg)
        with open(os.path.join(self.out, "candidates", "package.json"), "wb") as fh:    # what "candidates/./" names
            fh.write(pkg)
        os.makedirs(os.path.join(self.out, "a"))
        os.symlink(os.path.join(self.out, "candidates", "c1"), os.path.join(self.out, "candidates", "link"))
        index["reruns"]["link"] = self.entry(pkg)
        for cid in ("..", ".", "a/b", "", "../candidates/c1", "c1/../c1", "c1\x00", "link", "c2", None, 1, ["c1"]):
            with self.subTest(cid=cid):
                self.assertEqual(self.refused(index, cid), ["package_missing"])
        self.assertEqual(CR.reran(index, "c1", self.read)[0], pkg)

    def test_reran_refuses_a_package_that_was_not_rerun(self):
        pkg = package(GOOD)
        entry = self.entry(pkg)
        self.write("c1", pkg)
        for index in (None, [], {}, {"reruns": None}, {"reruns": []}, {"reruns": {}}, {"reruns": {"c1": None}},
                      {"reruns": {"c1": "verified"}}, {"reruns": {"c2": entry}}, {"candidates": {"c1": entry}},
                      {"reruns": {"c1": {"verdict": "verified", "reasons": []}}},
                      {"reruns": {"c1": dict(entry, package_sha256=None)}},
                      {"reruns": {"c1": dict(entry, package_sha256=sha(pkg).upper())}}):
            with self.subTest(index=index):
                self.assertEqual(self.refused(index), ["rerun_missing"])
        # the rerun is of the package's bytes: no byte of the package changes and it is still handed out
        index = {"reruns": {"c1": entry}}
        for changed in [pkg[:i] + bytes([pkg[i] ^ 1]) + pkg[i + 1:] for i in range(len(pkg))] + [pkg + b"\n", pkg[:-1], b""]:
            self.write("c1", changed)
            self.assertEqual(self.refused(index), ["rerun_missing"], changed)

    def test_reran_refuses_a_rerun_that_is_not_verified(self):
        pkg = package(GOOD)
        self.write("c1", pkg)
        for verdict in ("refused", "no_verdict", None, True, ["verified"], "Verified", ""):
            with self.subTest(verdict=verdict):
                self.assertEqual(self.refused({"reruns": {"c1": self.entry(pkg, verdict)}}), ["rerun_not_verified"])
        entry = self.entry(pkg)
        del entry["verdict"]
        self.assertEqual(self.refused({"reruns": {"c1": entry}}), ["rerun_not_verified"])

    def test_reran_refuses_a_rerun_whose_files_are_not_all_there(self):
        pkg = package(GOOD)
        index = {"reruns": {"c1": self.entry(pkg), "c2": self.entry(pkg)}}
        for gone in CR.FILES:
            with self.subTest(gone=gone):
                self.write("c1", pkg, [f for f in CR.FILES if f != gone])
                self.assertEqual(self.refused(index), ["rerun_files_missing"])
                os.symlink(os.path.join(self.out, "r", "c1", CR.FILES[0 if gone != CR.FILES[0] else 1]),
                           os.path.join(self.out, "r", "c1", gone))        # a link is not the file
                self.assertEqual(self.refused(index), ["rerun_files_missing"])
                os.remove(os.path.join(self.out, "r", "c1", gone))
                os.mkdir(os.path.join(self.out, "r", "c1", gone))            # nor is a directory
                self.assertEqual(self.refused(index), ["rerun_files_missing"])
        self.write("c1", pkg)
        shutil.move(os.path.join(self.out, "r", "c1"), os.path.join(self.out, "r", "c2"))
        self.assertEqual(self.refused(index), ["rerun_files_missing"])      # another candidate's files are not c1's


NO_APPLY = kos_diff("pkg/a.js", ["no such line"], ["x"])
PACKAGES = {"good": package(GOOD), "breaks": package(BREAKS_TEST), "noapply": package(NO_APPLY),
            "nodiff": package(None), "notjson": b"\xff{", "again": package(GOOD), "twice": package(GOOD),
            "bad id": package(GOOD), b"caf\xe9": package(GOOD)}
BAD = {"bad id", "caf\udce9"}      # no candidate ids (the second as the host lists a name that is not UTF-8)


def organ(packages: dict, name: str = "lint") -> dict:
    """An organ whose entry point writes ``packages`` (``{id: bytes}``) at ``candidates/<id>/package.json``."""
    main = ("import os, sys\n"
            "for cid, data in %r.items():\n"
            "    at = os.path.join(os.fsencode(sys.argv[1]), b'candidates', os.fsencode(cid))\n"
            "    os.makedirs(at)\n"
            "    with open(os.path.join(at, b'package.json'), 'wb') as fh:\n"
            "        fh.write(data)\n" % (packages,)).encode()
    path = "adapters/%s/main.py" % name
    return {"entry": ["python3", "/in/" + path, "/out"], "files": {path: main}}


class RedFor(RedAs):
    """``RedAs`` whose red control is red on the calls numbered in ``reds`` (from 1) and green on every other."""

    def __init__(self, reds) -> None:
        super().__init__()
        self.reds = set(reds)

    def __call__(self, argv, env, timeout):
        n = len(J.RED_CONTROL["cmd"])
        if argv[-n:] == J.RED_CONTROL["cmd"]:
            self.script = "pkg/red.py" if self.red_seen + 1 in self.reds else "pkg/green.py"
        return super().__call__(argv, env, timeout)


class Live(LiveBase):
    def index(self) -> dict:
        with open(self.results("index.json")) as fh:
            return json.load(fh)

    def file(self, *parts) -> bytes:
        with open(self.results(*parts), "rb") as fh:
            return fh.read()

    def decide(self, diff: bytes, run: str) -> dict:
        """MF8's own command on a candidate directory holding ``diff`` and the files under the results' ``run``."""
        cand = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, cand)
        for name, data in candidate(diff).items():
            with open(os.path.join(cand, name), "wb") as fh:
                fh.write(data)
        proc = subprocess.run(
            [sys.executable, "-m", "gate.check", "decide", cand, self.results("base.jsonl"), self.results(run),
             self.results(run, "hashes.json")],
            input=json.dumps({"control": {"merge_paused": False}, "unfinished_sentinels": []}).encode(),
            cwd=REFEREE, capture_output=True)
        return json.loads(proc.stdout)

    def test_a_run_time_candidate_runs_as_the_ready_candidate_of_the_same_diff(self):
        runner = RedAs()
        self.cycle({"lint.discover": organ(PACKAGES), "candidate.publish": organ({"twice": package(BREAKS_TEST),
                                                                                  "good": package(GOOD)}, "publish")},
                   runner=runner,
                   cands={"good": candidate(GOOD), "breaks": candidate(BREAKS_TEST), "noapply": candidate(NO_APPLY)})
        index = self.index()
        named = {os.fsdecode(cid): pkg for cid, pkg in PACKAGES.items()}
        self.assertEqual(list(index["reruns"]), sorted(named))
        self.assertEqual({cid: e["package_sha256"] for cid, e in index["reruns"].items()},
                         dict({cid: sha(pkg) for cid, pkg in named.items()}, twice=None))
        entries = {cid: {k: v for k, v in e.items() if k != "package_sha256"} for cid, e in index["reruns"].items()}
        for cid in ("good", "breaks", "noapply"):
            with self.subTest(cid):
                self.assertEqual(entries[cid], index["candidates"][cid])
        self.assertEqual((entries["good"]["verdict"], entries["breaks"]["verdict"], entries["again"]),
                         ("verified", "verified", entries["good"]))
        self.assertEqual(entries["noapply"], {"verdict": "refused", "reasons": ["patch_does_not_apply"]})
        unusable = {"verdict": "refused", "reasons": ["package_unusable"]}
        self.assertEqual((entries["nodiff"], entries["notjson"]), (unusable, unusable))
        self.assertEqual(entries["twice"], {"verdict": "refused", "reasons": ["package_id_twice"]})
        for cid in BAD:
            self.assertEqual(entries[cid], {"verdict": "refused", "reasons": ["candidate_id_invalid"]})
        # the packages: at the page's path of the results, the bytes the organ wrote; none for an id held twice or
        # one that is no candidate id
        self.assertEqual(sorted(os.listdir(self.results("candidates"))), sorted(set(named) - BAD - {"twice"}))
        for cid in os.listdir(self.results("candidates")):
            self.assertEqual(os.listdir(self.results("candidates", cid)), ["package.json"])
            self.assertEqual(self.file("candidates", cid, "package.json"), named[cid])
        # the files: byte for byte the ready candidate's of the same diff, and no directory for what did not run
        self.assertEqual(sorted(os.listdir(self.results("r"))), ["again", "breaks", "good"])
        for cid, ready in (("good", "good"), ("breaks", "breaks"), ("again", "good")):
            with self.subTest(cid):
                self.assertEqual(sorted(os.listdir(self.results("r", cid))), sorted(CR.FILES))
                for f in ("cand.jsonl", "checks.json"):
                    self.assertEqual(self.file("r", cid, f), self.file("c", ready, f), f)
                hashes = json.loads(self.file("r", cid, "hashes.json"))
                self.assertEqual(hashes, json.loads(self.file("c", ready, "hashes.json")))
                self.assertEqual({f: hashes[f] for f in ("cand.jsonl", "checks.json")},
                                 {f: sha(self.file("r", cid, f)) for f in ("cand.jsonl", "checks.json")})
        # the runs: 3 base lint, the two organs, 3 lint + 1 test for each of the two ready candidates and the three
        # reruns whose diff applied; every one of them a contained run with the job's red control
        self.assertEqual(runner.red_seen, 3 + 2 + 4 * 2 + 4 * 3)
        self.assertEqual(len(runner.calls), 2 * (3 + 2 + 4 * 2 + 4 * 3))
        # MF8's command takes the rerun's files as it takes a ready candidate's
        self.assertEqual(self.decide(GOOD, "r/good"), self.decide(GOOD, "c/good"))
        self.assertEqual(self.decide(GOOD, "r/good")["decision"], "merge")
        got = self.decide(BREAKS_TEST, "r/breaks")
        self.assertEqual((got["decision"], got["reasons"]), ("reject", ["tests_red"]))
        # yaz: every candidate of the results, asked of reran
        not_verified = {"reran": False, "reasons": ["rerun_not_verified"]}
        no_package = {"reran": False, "reasons": ["package_missing"]}
        line = self.yaz("reruns")
        self.assertEqual(list(line), sorted(named))
        self.assertEqual(line, dict(
            {cid: {"reran": True, "package_sha256": sha(named[cid])} for cid in ("good", "breaks", "again")},
            noapply=not_verified, nodiff=not_verified, notjson=not_verified, twice=no_package,
            **{cid: no_package for cid in BAD}))

    def test_a_candidate_whose_rerun_is_not_in_the_results_is_not_handed_out(self):
        self.cycle({"lint.discover": organ({"good": package(GOOD), "breaks": package(BREAKS_TEST),
                                            "other": package(GOOD), "kept": package(GOOD)})})
        reran = {"reran": True, "package_sha256": sha(package(GOOD))}
        self.assertEqual(self.yaz("reruns"), {
            "breaks": {"reran": True, "package_sha256": sha(package(BREAKS_TEST))}, "good": reran, "kept": reran,
            "other": reran})
        os.remove(self.results("r", "good", "checks.json"))
        index = self.index()
        del index["reruns"]["breaks"]
        with open(self.results("index.json"), "w") as fh:
            json.dump(index, fh)
        with open(self.results("candidates", "other", "package.json"), "ab") as fh:
            fh.write(b" ")      # one byte more than the package that was rerun
        os.makedirs(self.results("candidates", "new"))
        with open(self.results("candidates", "new", "package.json"), "wb") as fh:
            fh.write(package(GOOD))     # a package no rerun is of
        self.assertEqual(self.yaz("reruns"), {
            "breaks": {"reran": False, "reasons": ["rerun_missing"]},
            "good": {"reran": False, "reasons": ["rerun_files_missing"]}, "kept": reran,
            "new": {"reran": False, "reasons": ["rerun_missing"]},
            "other": {"reran": False, "reasons": ["rerun_missing"]}})
        # the ready candidate's files of the same name are not the rerun's; a package taken away is missing
        shutil.rmtree(self.results("r"))
        shutil.rmtree(self.results("candidates", "kept"))
        os.makedirs(self.results("c", "good"))
        for f in CR.FILES:
            with open(self.results("c", "good", f), "wb") as fh:
                fh.write(b"{}")
        line = self.yaz("reruns")
        self.assertEqual((line["good"], line["kept"]), ({"reran": False, "reasons": ["rerun_files_missing"]},
                                                        {"reran": False, "reasons": ["package_missing"]}))

    def test_a_rerun_whose_red_control_is_green_is_not_verified(self):
        runner = RedFor(range(1, 3 + 1 + 2 + 1))      # red for the base, the organ and the rerun's first two lint runs
        self.cycle({"lint.discover": organ({"good": package(GOOD)})}, runner=runner)
        index = self.index()
        self.assertEqual(index["base"]["verdict"], "verified")
        self.assertEqual((index["reruns"]["good"]["verdict"], index["reruns"]["good"]["package_sha256"]),
                         ("no_verdict", sha(package(GOOD))))
        self.assertEqual(runner.red_seen, 3 + 1 + 4)
        self.assertEqual(self.yaz("reruns"), {"good": {"reran": False, "reasons": ["rerun_not_verified"]}})

    def test_without_a_base_run_nothing_is_rerun(self):
        runner = RedFor([1, 4])     # red for the first base lint and for the organ only
        self.cycle({"lint.discover": organ({"good": package(GOOD), "nodiff": package(None)})}, runner=runner)
        index = self.index()
        self.assertNotEqual(index["base"]["verdict"], "verified")
        self.assertEqual(index["reruns"], {
            "good": {"verdict": "no_verdict", "reasons": ["base_unavailable"], "package_sha256": sha(package(GOOD))},
            "nodiff": {"verdict": "refused", "reasons": ["package_unusable"], "package_sha256": sha(package(None))}})
        self.assertEqual(runner.red_seen, 3 + 1)
        self.assertFalse(os.path.lexists(self.results("r")))
        self.assertEqual(sorted(os.listdir(self.results("candidates"))), ["good", "nodiff"])

    def test_a_kept_output_that_is_not_read_back_stops_the_run(self):
        test = self

        class Loses(RedAs):
            """Removes the kept blobs during the ready candidate's first run: after the keep, before the rerun."""

            def __call__(self, argv, env, timeout):
                if self.red_seen == 3 + 1 and argv[-len(J.RED_CONTROL["cmd"]):] == J.RED_CONTROL["cmd"]:
                    store = os.path.join(test.temp, "out", "results", "t1", "o")
                    for blob in os.listdir(store):
                        os.remove(os.path.join(store, blob))
                return super().__call__(argv, env, timeout)

        runner = Loses()
        carried = {"lint.discover": organ({"good": package(GOOD)})}
        self.write_pulled({"good": candidate(GOOD)}, organs=carried,
                          accepted={o: organs.definition_sha256(d) for o, d in carried.items()})
        with self.assertRaises(J.Unusable) as caught:
            J.run("kos", {"RUNNER_TEMP": self.temp}, runner=runner)
        self.assertEqual(str(caught.exception), "kos: a kept output is not read back: output_missing:manifest")
        self.assertEqual(runner.red_seen, 3 + 1 + 4)        # the ready candidate ran; nothing ran for the package
        self.assertFalse(os.path.lexists(os.path.join(self.temp, "out", "results", "t1", "candidates")))

    def test_without_a_package_nothing_is_rerun(self):
        self.cycle({})
        self.assertEqual((self.index()["reruns"], os.path.lexists(self.results("r")),
                          os.path.lexists(self.results("candidates"))), ({}, False, False))
        self.assertEqual(self.yaz("reruns"), {})


if __name__ == "__main__":
    unittest.main()
