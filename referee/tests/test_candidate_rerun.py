"""Test 57 (P1 MF11, tohum/26j): ``koş`` reruns a run-time candidate before the gate, as it runs a ready candidate
(three lint runs, a test run, the red control), and a candidate without a rerun does not reach the gate.

What is measured:

- ``Unit`` (``runner.candidate_rerun`` alone): which paths of an output are packages, the diff of a package over a
  table of documents, ``rerun``'s order and its one call per package on a store ``organ_output.keep`` wrote, and
  ``reran``'s every reason (no index, no entry, one byte of the package changed, each other verdict, each of the
  three files missing or a link);
- ``Live`` (the jobs, as test 56 runs them: ``loop.job.run("kos")`` on a ``pulled`` artifact carrying an accepted
  organ whose entry point writes the packages and the same diffs as ready candidates, then ``loop.job.run("yaz")``):
  the rerun's entry and files against the ready candidate's of the same diff, the count of contained runs and of
  red controls, MF8's command (``gate.check decide``) on the rerun's files, ``yaz``'s line, and that line again
  after the rerun was removed from the results.

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
        files = {"candidates/c1/package.json": b"1", "candidates/c 2\n/package.json": b"2",
                 "candidates/package.json": b"no id", "candidates/a/b/package.json": b"two parts",
                 "x/candidates/c1/package.json": b"not at the root", "candidates/c1/package.json\n": b"a newline",
                 "candidates/c1/package.jsonx": b"longer", "candidates//package.json": b"empty id",
                 "candidates/c1/finding.json": b"another file", "candidates/c3/package.json": b"1"}
        self.assertEqual(CR.packages(files), {sha(b"1"): b"1", sha(b"2"): b"2"})
        self.assertEqual(CR.packages({}), {})
        self.assertEqual(CR.key(b"1"), "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b")

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

    def test_rerun_calls_run_once_for_each_package_in_the_order_of_the_hashes(self):
        a, b, c = package(GOOD), package(None), package(BREAKS_TEST)
        first = self.keep({"candidates/1/package.json": a, "candidates/2/package.json": b, "findings.json": c})
        second = self.keep({"candidates/1/package.json": c, "candidates/other/package.json": a})
        third = self.keep({"findings.json": b"[]"})
        calls: list = []

        def run(name, diff):
            calls.append((name, diff))
            return {"n": len(calls)}

        want = sorted([(sha(a), GOOD), (sha(b), None), (sha(c), BREAKS_TEST)])
        for outputs in ([first, second, third], [third, second, first]):
            del calls[:]
            got = CR.rerun(outputs, self.read, run)
            self.assertEqual(calls, want)
            self.assertEqual(list(got.items()), [(name, {"n": n + 1}) for n, (name, _) in enumerate(want)])
        del calls[:]
        self.assertEqual((CR.rerun([third], self.read, run), CR.rerun([], self.read, run), calls), ({}, {}, []))

    def test_rerun_runs_nothing_when_a_kept_output_is_not_read_back(self):
        first = self.keep({"candidates/1/package.json": package(GOOD)})
        second = self.keep({"candidates/1/package.json": package(BREAKS_TEST)})
        os.remove(os.path.join(self.out, OO.STORE, sha(package(BREAKS_TEST))))
        calls: list = []
        for outputs in ([first, second], [second, first], [first, "0" * 64], [first, None]):
            with self.subTest(outputs):
                with self.assertRaises(OO.Refused):
                    CR.rerun(outputs, self.read, lambda *a: calls.append(a))
        self.assertEqual(calls, [])

    def write(self, name: str, files=CR.FILES) -> None:
        shutil.rmtree(os.path.join(self.out, "r"), ignore_errors=True)
        os.makedirs(os.path.join(self.out, "r", name))
        for f in files:
            with open(os.path.join(self.out, "r", name, f), "wb") as fh:
                fh.write(f.encode())

    def refused(self, index, pkg: bytes) -> tuple:
        with self.assertRaises(CR.NotRerun) as caught:
            CR.reran(index, pkg, self.read)
        return caught.exception.reasons, caught.exception.entry

    def test_reran_hands_out_the_three_files_of_a_verified_rerun(self):
        pkg = package(GOOD)
        entry = {"verdict": "verified", "reasons": []}
        self.write(sha(pkg))
        self.assertEqual(CR.FILES, ("cand.jsonl", "checks.json", "hashes.json"))
        self.assertEqual(CR.reran({"reruns": {sha(pkg): entry}}, pkg, self.read),
                         {"cand.jsonl": b"cand.jsonl", "checks.json": b"checks.json", "hashes.json": b"hashes.json"})

    def test_reran_refuses_a_package_that_was_not_rerun(self):
        pkg = package(GOOD)
        entry = {"verdict": "verified", "reasons": []}
        self.write(sha(pkg))
        for index in (None, [], {}, {"reruns": None}, {"reruns": []}, {"reruns": {}}, {"reruns": {sha(pkg): None}},
                      {"reruns": {sha(pkg): "verified"}}, {"reruns": {sha(b"other"): entry}},
                      {"candidates": {sha(pkg): entry}}):
            with self.subTest(index=index):
                self.assertEqual(self.refused(index, pkg), (["rerun_missing"], None))
        # the rerun is of the package's bytes: no byte of it changes and the files are still handed out
        index = {"reruns": {sha(pkg): entry}}
        for i in range(len(pkg)):
            changed = pkg[:i] + bytes([pkg[i] ^ 1]) + pkg[i + 1:]
            self.assertEqual(self.refused(index, changed), (["rerun_missing"], None), i)
        self.assertEqual(self.refused(index, pkg + b"\n"), (["rerun_missing"], None))
        self.assertEqual(self.refused(index, pkg[:-1]), (["rerun_missing"], None))

    def test_reran_refuses_a_rerun_that_is_not_verified(self):
        pkg = package(GOOD)
        self.write(sha(pkg))
        for entry in ({"verdict": "refused", "reasons": ["patch_does_not_apply"]}, {"verdict": "no_verdict", "reasons": []},
                      {"verdict": "refused", "reasons": [CR.UNUSABLE]}, {}, {"verdict": None}, {"verdict": True},
                      {"verdict": ["verified"]}, {"verdict": "Verified"}, {"reasons": ["verified"]}):
            with self.subTest(entry=entry):
                self.assertEqual(self.refused({"reruns": {sha(pkg): entry}}, pkg), (["rerun_not_verified"], entry))

    def test_reran_refuses_a_rerun_whose_files_are_not_all_there(self):
        pkg = package(GOOD)
        entry = {"verdict": "verified", "reasons": []}
        index = {"reruns": {sha(pkg): entry}}
        for gone in CR.FILES:
            with self.subTest(gone=gone):
                self.write(sha(pkg), [f for f in CR.FILES if f != gone])
                self.assertEqual(self.refused(index, pkg), (["rerun_files_missing"], entry))
                os.symlink(os.path.join(self.out, "r", sha(pkg), CR.FILES[0 if gone != CR.FILES[0] else 1]),
                           os.path.join(self.out, "r", sha(pkg), gone))        # a link is not the file
                self.assertEqual(self.refused(index, pkg), (["rerun_files_missing"], entry))
                os.remove(os.path.join(self.out, "r", sha(pkg), gone))
                os.mkdir(os.path.join(self.out, "r", sha(pkg), gone))            # nor is a directory
                self.assertEqual(self.refused(index, pkg), (["rerun_files_missing"], entry))
        self.write(sha(b"another package"))     # the files of another rerun are not this one's
        self.assertEqual(self.refused(index, pkg), (["rerun_files_missing"], entry))


NO_APPLY = kos_diff("pkg/a.js", ["no such line"], ["x"])
PACKAGES = {"good": package(GOOD), "breaks": package(BREAKS_TEST), "noapply": package(NO_APPLY),
            "nodiff": package(None), "not json": b"\xff{", "again": package(GOOD)}


def organ(packages: dict) -> dict:
    """An organ whose entry point writes ``packages`` (``{id: bytes}``) at ``candidates/<id>/package.json``."""
    main = ("import os, sys\n"
            "for cid, data in %r.items():\n"
            "    os.makedirs(os.path.join(sys.argv[1], 'candidates', cid))\n"
            "    with open(os.path.join(sys.argv[1], 'candidates', cid, 'package.json'), 'wb') as fh:\n"
            "        fh.write(data)\n" % (packages,)).encode()
    return {"entry": ["python3", "/in/adapters/lint/main.py", "/out"], "files": {"adapters/lint/main.py": main}}


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
        self.cycle({"lint.discover": organ(PACKAGES)}, runner=runner,
                   cands={"good": candidate(GOOD), "breaks": candidate(BREAKS_TEST), "noapply": candidate(NO_APPLY)})
        index = self.index()
        name = {cid: sha(pkg) for cid, pkg in PACKAGES.items()}
        self.assertEqual(name["again"], name["good"])       # the same bytes under two ids: one candidate
        self.assertEqual(sorted(index["reruns"]), sorted(set(name.values())))
        self.assertEqual(list(index["reruns"]), sorted(index["reruns"]))
        for cid in ("good", "breaks", "noapply"):
            with self.subTest(cid):
                self.assertEqual(index["reruns"][name[cid]], index["candidates"][cid])
        self.assertEqual(index["reruns"][name["good"]]["verdict"], "verified")
        self.assertEqual(index["reruns"][name["breaks"]]["verdict"], "verified")
        self.assertEqual(index["reruns"][name["noapply"]], {"verdict": "refused", "reasons": ["patch_does_not_apply"]})
        unusable = {"verdict": "refused", "reasons": ["package_unusable"]}
        self.assertEqual((index["reruns"][name["nodiff"]], index["reruns"][name["not json"]]), (unusable, unusable))
        # the files: byte for byte the ready candidate's of the same diff, and no directory for what did not run
        self.assertEqual(sorted(os.listdir(self.results("r"))), sorted([name["good"], name["breaks"]]))
        for cid in ("good", "breaks"):
            with self.subTest(cid):
                self.assertEqual(sorted(os.listdir(self.results("r", name[cid]))), sorted(CR.FILES))
                for f in ("cand.jsonl", "checks.json"):
                    self.assertEqual(self.file("r", name[cid], f), self.file("c", cid, f), f)
                hashes = json.loads(self.file("r", name[cid], "hashes.json"))
                self.assertEqual(hashes, json.loads(self.file("c", cid, "hashes.json")))
                self.assertEqual({f: hashes[f] for f in ("cand.jsonl", "checks.json")},
                                 {f: sha(self.file("r", name[cid], f)) for f in ("cand.jsonl", "checks.json")})
        # the runs: 3 base lint, the organ, 3 lint + 1 test for each of the two ready candidates and the two reruns
        # whose diff applied; every one of them a contained run with the job's red control
        self.assertEqual(runner.red_seen, 3 + 1 + 4 * 2 + 4 * 2)
        self.assertEqual(len(runner.calls), 2 * (3 + 1 + 4 * 2 + 4 * 2))
        # MF8's command takes the rerun's files as it takes a ready candidate's
        self.assertEqual(self.decide(GOOD, "r/" + name["good"]), self.decide(GOOD, "c/good"))
        self.assertEqual(self.decide(GOOD, "r/" + name["good"])["decision"], "merge")
        got = self.decide(BREAKS_TEST, "r/" + name["breaks"])
        self.assertEqual((got["decision"], got["reasons"]), ("reject", ["tests_red"]))
        # yaz: each package of the output it reads, asked of reran
        self.assertEqual(self.yaz("reruns"), dict(sorted({
            name["good"]: {"reran": True}, name["breaks"]: {"reran": True},
            name["noapply"]: {"reran": False, "reasons": ["rerun_not_verified"]},
            name["nodiff"]: {"reran": False, "reasons": ["rerun_not_verified"]},
            name["not json"]: {"reran": False, "reasons": ["rerun_not_verified"]}}.items())))

    def test_a_candidate_whose_rerun_is_not_in_the_results_is_not_handed_out(self):
        self.cycle({"lint.discover": organ({"good": package(GOOD), "breaks": package(BREAKS_TEST)})})
        good, breaks = sha(package(GOOD)), sha(package(BREAKS_TEST))
        self.assertEqual(self.yaz("reruns"), {k: {"reran": True} for k in sorted([good, breaks])})
        os.remove(self.results("r", good, "checks.json"))
        index = self.index()
        del index["reruns"][breaks]
        with open(self.results("index.json"), "w") as fh:
            json.dump(index, fh)
        self.assertEqual(self.yaz("reruns"), dict(sorted({
            good: {"reran": False, "reasons": ["rerun_files_missing"]},
            breaks: {"reran": False, "reasons": ["rerun_missing"]}}.items())))
        # the ready candidate's files of the same diff are not the rerun's
        shutil.rmtree(self.results("r"))
        os.makedirs(self.results("c", good))
        for f in CR.FILES:
            with open(self.results("c", good, f), "wb") as fh:
                fh.write(b"{}")
        self.assertEqual(self.yaz("reruns")[good], {"reran": False, "reasons": ["rerun_files_missing"]})

    def test_a_rerun_whose_red_control_is_green_is_not_verified(self):
        runner = RedFor(range(1, 3 + 1 + 2 + 1))      # red for the base, the organ and the rerun's first two lint runs
        self.cycle({"lint.discover": organ({"good": package(GOOD)})}, runner=runner)
        good = sha(package(GOOD))
        index = self.index()
        self.assertEqual(index["base"]["verdict"], "verified")
        self.assertEqual(index["reruns"][good]["verdict"], "no_verdict")
        self.assertEqual(runner.red_seen, 3 + 1 + 4)
        self.assertEqual(self.yaz("reruns"), {good: {"reran": False, "reasons": ["rerun_not_verified"]}})

    def test_without_a_base_run_nothing_is_rerun(self):
        runner = RedFor([1, 4])     # red for the first base lint and for the organ only
        self.cycle({"lint.discover": organ({"good": package(GOOD), "nodiff": package(None)})}, runner=runner)
        index = self.index()
        self.assertNotEqual(index["base"]["verdict"], "verified")
        self.assertEqual(index["reruns"], dict(sorted({
            sha(package(GOOD)): {"verdict": "no_verdict", "reasons": ["base_unavailable"]},
            sha(package(None)): {"verdict": "refused", "reasons": ["package_unusable"]}}.items())))
        self.assertEqual(runner.red_seen, 3 + 1)
        self.assertFalse(os.path.lexists(self.results("r")))

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

    def test_without_an_organ_nothing_is_rerun(self):
        self.cycle({})
        self.assertEqual((self.index()["reruns"], os.path.lexists(self.results("r"))), ({}, False))
        self.assertEqual(self.yaz("reruns"), {})

    def test_the_packages_of_an_output_yaz_does_not_read_are_not_on_the_line(self):
        self.cycle({"lint.discover": organ({"good": package(GOOD)})})
        os.remove(self.results("o", self.index()["organs"]["lint.discover"]["output"]["sha256"]))
        self.github()
        line = self.line(self.run_yaz())
        self.assertEqual((line["organs"]["lint.discover"]["read"], line["reruns"]), (False, {}))


if __name__ == "__main__":
    unittest.main()
