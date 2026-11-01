"""Test 46 (asama-0/09), MF17, D1 -> D3: the ``pulled`` artifact (``loop.pulled``) and the ``kos`` job over it
(``loop.job run kos``), with the fake runner (``fake_docker.py``, Python commands only).

- the layout: what ``write`` writes, ``read`` gives back (``state/``: the heads and ``brain/state``'s chained files,
  byte for byte); every refusal of ``read`` on a tampered artifact (a changed byte, a missing, extra, symlinked or
  unlisted file, a path outside the layout, an incomplete candidate, a bad manifest, a file that is not JSON, heads
  that are not the two branches' commits, a missing state file), and ``write`` refuses what ``read`` would;
- the tree: ``extract_tree`` keeps modes and inside links and refuses absolute, ``..`` and outside-link members;
- the job: from ``$RUNNER_TEMP/in/pulled`` (and ``in/deps``) to ``$RUNNER_TEMP/out/results``, which ``gate.check
  decide`` (MF8's own command) reads: the good candidate merges, a test-breaking and a ratchet-raising one are
  rejected for their own reasons; the red control is the job's own ``RED_CONTROL`` (a green one blocks the base),
  not something the artifact holds; a refused artifact, two units or an unsafe tree run nothing; ``in/deps`` is
  taken as one ``<address>/`` directory, which reaches ``unit.verify``; the job ends ``ok``, exit 0, after D3
  (``done`` ``["D3"]``) or after D3 and D7's sentinel (``["D3", "D7"]``), so the upload runs; the job's steps are
  D3 and D7 only (D8's planted merge is watched by D7's run);
- D7's half in ``kos``: which merge the sentinel watches is read from ``state/ledger.jsonl`` (``ledger.serial``):
  none without an unfinished merge or after its revert; the one unfinished merge at ``brain/integration``'s head
  runs the sentinel there (``sentinel.json`` in the results); an unfinished merge elsewhere, or a ledger that cannot
  be read, runs nothing.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ledger import chain as CH  # noqa: E402
from loop import job as J  # noqa: E402
from loop import pulled as P  # noqa: E402
from fake_docker import FakeDocker  # noqa: E402
from profile_tree import writable_base, write_tree  # noqa: E402
from test_revert_drill import ledger_with, reverted, row  # noqa: E402
from test_serial import START, merge  # noqa: E402
from test_kos import A_JS, BREAKS_TEST, FINDING, GOOD, LINT, RAISES, TESTS, operating, recipe  # noqa: E402

TREE = {
    ".nvmrc": "v20.11.1\n",
    "pkg/package.json": {"name": "pkg", "version": "1.0.0"},
    "pkg/package-lock.json": {"lockfileVersion": 3, "packages": {"": {"name": "pkg", "version": "1.0.0"}}},
    "pkg/lint.py": LINT, "pkg/run_tests.py": TESTS, "pkg/a.js": A_JS, "pkg/b.js": "const c = 3;\n",
    "pkg/red.py": "raise SystemExit(1)\n", "pkg/green.py": "raise SystemExit(0)\n",
}
TARGET = {"id": "t1", "kind": "toy", "excluded_paths": [], "unit_candidates": []}
HEADS = {"brain/state": "a" * 40, "brain/integration": "b" * 40}


def chained(rows: list[dict]) -> bytes:
    """``rows`` as a chained JSONL file (``ledger.chain``'s rules)."""
    prev, out = CH.ZERO_HASH, []
    for row in rows:
        row = dict(row, prev_hash=prev)
        row["row_hash"] = prev = CH.row_hash(row)
        out.append(json.dumps(row))
    return "".join(line + "\n" for line in out).encode()


def state_files(ledger: list[dict] | None = None) -> dict[str, bytes]:
    """``brain/state``'s chained files as ``pulled`` carries them: a ``cycle_start`` row in the ledger (a row of
    ``ledger.schema``, no merge) and a root row, or ``ledger``'s rows."""
    return {"ledger.jsonl": chained(ledger if ledger is not None else [row("g1", "events", "cycle_start", {"cycle_id": "1"})]),
            "chain/root.jsonl": chained([{"row_id": "r0", "part": "root"}])}


def tar_of(root: str) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name in sorted(os.listdir(root)):
            tar.add(os.path.join(root, name), arcname=name)
    return buf.getvalue()


def candidate(diff: bytes) -> dict:
    return {"diff.patch": diff, "finding.json": json.dumps(FINDING).encode(),
            "expect.json": b'{"decision": "merge"}\n'}


class RedAs:
    """The fake runner with the job's ``RED_CONTROL`` argv replaced by a Python script of the tree (the fake runs
    Python only): ``pkg/red.py`` (exit 1) or ``pkg/green.py`` (exit 0). Records whether the constant was seen."""

    def __init__(self, script: str = "pkg/red.py") -> None:
        self.docker, self.script, self.red_seen = FakeDocker(), script, 0

    def __call__(self, argv, env, timeout):
        n = len(J.RED_CONTROL["cmd"])
        if argv[-n:] == J.RED_CONTROL["cmd"]:
            self.red_seen += 1
            argv = argv[:-n] + ["python", self.script]
        return self.docker(argv, env, timeout)

    @property
    def calls(self):
        return self.docker.calls


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.base = writable_base("t-loopkos-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.src = os.path.join(self.base, "src")
        write_tree(self.src, TREE)
        self.temp = os.path.join(self.base, "runner-temp")
        self.pulled = os.path.join(self.temp, "in", "pulled")

    def write_pulled(self, cands=None, units=None, tree_tar=None, policy=None, target=None, heads=None,
                     state=None, status=None) -> dict:
        return P.write(self.pulled, target or TARGET, tree_tar if tree_tar is not None else tar_of(self.src),
                       json.dumps(units if units is not None else {"units": [recipe()]}).encode(),
                       policy if isinstance(policy, bytes) else json.dumps(policy or {"operating": operating()}).encode(),
                       cands if cands is not None else {}, HEADS if heads is None else heads,
                       state_files() if state is None else state, status)

    def manifest(self) -> dict:
        with open(os.path.join(self.pulled, P.MANIFEST)) as fh:
            return json.load(fh)

    def set_manifest(self, manifest: dict) -> None:
        with open(os.path.join(self.pulled, P.MANIFEST), "w") as fh:
            json.dump(manifest, fh)

    def reasons(self) -> list[str]:
        with self.assertRaises(P.PulledError) as ctx:
            P.read(self.pulled)
        return ctx.exception.reasons


class Layout(Base):
    def test_write_then_read(self):
        manifest = self.write_pulled({"good": candidate(GOOD)})
        got = P.read(self.pulled)
        self.assertEqual(got.target, TARGET)
        self.assertEqual(got.units, {"units": [recipe()]})
        self.assertEqual(got.candidates, {"good": candidate(GOOD)})
        self.assertEqual(sorted(manifest["files"]), ["candidates/good/diff.patch", "candidates/good/expect.json",
                                                     "candidates/good/finding.json", "policy.json",
                                                     "state/chain/root.jsonl", "state/heads.json",
                                                     "state/ledger.jsonl", "tree.tar", "units.json"])
        with open(got.tree_tar, "rb") as fh:
            self.assertEqual(fh.read(), tar_of(self.src))
        self.assertEqual((got.heads, got.state), (HEADS, state_files()))

    def test_the_state_files_are_required_and_the_heads_are_two_commits(self):
        self.write_pulled()
        os.remove(os.path.join(self.pulled, "state", "ledger.jsonl"))
        m = self.manifest()
        del m["files"]["state/ledger.jsonl"]
        self.set_manifest(m)
        self.assertEqual(self.reasons(), ["missing:state/ledger.jsonl"])
        for heads, want in (
                ({"brain/state": "a" * 40}, ["heads_invalid"]),
                (dict(HEADS, extra="c" * 40), ["heads_invalid"]),
                (dict(HEADS, **{"brain/state": "A" * 40}), ["heads_invalid"]),
                (dict(HEADS, **{"brain/integration": "b" * 39}), ["heads_invalid"]),
                ([HEADS], ["heads_invalid"]),
                (None, ["json_unreadable:state/heads.json"])):
            with self.subTest(heads=heads):
                shutil.rmtree(self.pulled)
                self.write_pulled()
                data = json.dumps(heads).encode() if heads is not None else b"{"
                with open(os.path.join(self.pulled, "state", "heads.json"), "wb") as fh:
                    fh.write(data)
                m = self.manifest()
                m["files"]["state/heads.json"] = P._sha(data)
                self.set_manifest(m)
                self.assertEqual(self.reasons(), want)

    def test_a_changed_byte(self):
        self.write_pulled({"good": candidate(GOOD)})
        with open(os.path.join(self.pulled, "candidates/good/diff.patch"), "ab") as fh:
            fh.write(b" ")
        self.assertEqual(self.reasons(), ["hash_mismatch:candidates/good/diff.patch"])

    def test_missing_extra_and_symlinked_files(self):
        self.write_pulled({"good": candidate(GOOD)})
        os.remove(os.path.join(self.pulled, "units.json"))
        write_tree(self.pulled, {"extra.txt": "x", "candidates/other/diff.patch": "y"})
        os.makedirs(os.path.join(self.pulled, "empty"))
        self.assertEqual(self.reasons(), ["file_missing:units.json", "unlisted:candidates/other/diff.patch",
                                          "unlisted:empty/", "unlisted:extra.txt"])

    def test_a_symlink_is_not_a_file(self):
        self.write_pulled()
        outside = os.path.join(self.base, "policy.json")
        shutil.move(os.path.join(self.pulled, "policy.json"), outside)
        os.symlink(outside, os.path.join(self.pulled, "policy.json"))
        self.assertEqual(self.reasons(), ["file_missing:policy.json"])

    def test_a_directory_symlink_on_the_way(self):
        self.write_pulled({"good": candidate(GOOD)})
        real = os.path.join(self.base, "real-good")
        shutil.move(os.path.join(self.pulled, "candidates", "good"), real)
        os.symlink(real, os.path.join(self.pulled, "candidates", "good"))
        self.assertEqual(self.reasons(), ["file_missing:candidates/good/diff.patch",
                                          "file_missing:candidates/good/expect.json",
                                          "file_missing:candidates/good/finding.json", "unlisted:candidates/good"])

    def test_paths_outside_the_layout_and_incomplete_candidates(self):
        self.write_pulled({"good": candidate(GOOD)})
        m = self.manifest()
        del m["files"]["candidates/good/expect.json"]
        del m["files"]["tree.tar"]
        write_tree(self.pulled, {"notes.md": "n", "candidates/bad id/diff.patch": "d"})
        m["files"]["notes.md"] = P._sha(b"n")
        m["files"]["candidates/bad id/diff.patch"] = P._sha(b"d")
        self.set_manifest(m)
        self.assertEqual(self.reasons(), ["path_not_in_layout:candidates/bad id/diff.patch",
                                          "path_not_in_layout:notes.md", "missing:tree.tar",
                                          "candidate_incomplete:good", "unlisted:candidates/good/expect.json",
                                          "unlisted:tree.tar"])

    def test_manifest(self):
        self.write_pulled()
        good = self.manifest()
        for broken, want in (
                (dict(good, schema="snowball-pulled/2"), ["schema_unknown"]),
                (dict(good, target={"kind": "toy"}), ["target_invalid"]),
                (dict(good, target={"id": ""}), ["target_invalid"]),
                (dict(good, files=dict(good["files"], **{"units.json": "AB" * 32})), ["files_invalid"]),
                (dict(good, extra=1), ["manifest_unreadable"]),
                ([good], ["manifest_unreadable"])):
            with self.subTest(want=want, broken=str(broken)[:60]):
                self.set_manifest(broken)
                self.assertEqual(self.reasons(), want)
        with open(os.path.join(self.pulled, P.MANIFEST), "wb") as fh:
            fh.write(b"\xff{")
        self.assertEqual(self.reasons(), ["manifest_unreadable"])
        os.remove(os.path.join(self.pulled, P.MANIFEST))
        self.assertEqual(self.reasons(), ["manifest_unreadable"])

    def test_json_files_must_be_json(self):
        self.write_pulled()
        for name in ("units.json", "policy.json"):
            with open(os.path.join(self.pulled, name), "wb") as fh:
                fh.write(b"{not json")
        m = self.manifest()
        m["files"]["units.json"] = m["files"]["policy.json"] = P._sha(b"{not json")
        self.set_manifest(m)
        self.assertEqual(self.reasons(), ["json_unreadable:units.json", "json_unreadable:policy.json"])

    def test_status_md_is_carried_when_the_head_has_one(self):
        # brain/state's status.md (D6 regenerates its block): optional in the layout, read back as it was written
        self.write_pulled(status=b"# notes\n")
        self.assertEqual(P.read(self.pulled).status, b"# notes\n")
        self.assertEqual(self.manifest()["files"]["state/status.md"], P._sha(b"# notes\n"))
        shutil.rmtree(self.pulled)
        self.write_pulled()
        self.assertIsNone(P.read(self.pulled).status)
        self.assertNotIn("state/status.md", self.manifest()["files"])
        shutil.rmtree(self.pulled)
        self.write_pulled(status=b"x")
        os.remove(os.path.join(self.pulled, "state", "status.md"))  # listed, not there
        self.assertEqual(self.reasons(), ["file_missing:state/status.md"])
        write_tree(self.pulled, {"state/status.md": "y"})  # there, other bytes
        self.assertEqual(self.reasons(), ["hash_mismatch:state/status.md"])
        shutil.rmtree(self.pulled)
        self.write_pulled()
        write_tree(self.pulled, {"state/status.md": "z"})  # there, not listed
        self.assertEqual(self.reasons(), ["unlisted:state/status.md"])
        shutil.rmtree(self.pulled)
        with self.assertRaises(P.PulledError) as ctx:
            self.write_pulled(status="text")
        self.assertEqual(ctx.exception.reasons, ["state_incomplete"])

    def test_write_refuses_what_read_would(self):
        with self.assertRaises(P.PulledError) as ctx:
            self.write_pulled({"good": {"diff.patch": GOOD}})
        self.assertEqual(ctx.exception.reasons, ["candidate_incomplete:good"])
        with self.assertRaises(P.PulledError) as ctx:
            self.write_pulled({"../x": candidate(GOOD)})
        self.assertEqual(ctx.exception.reasons[0].split(":")[0], "path_not_in_layout")
        for heads, state, want in ((None, {"ledger.jsonl": b""}, "state_incomplete"),
                                   (None, dict(state_files(), extra=b""), "state_incomplete"),
                                   (None, dict(state_files(), **{"ledger.jsonl": "text"}), "state_incomplete"),
                                   ({"brain/state": "a" * 40}, None, "heads_invalid")):
            with self.subTest(want=want, state=state):
                with self.assertRaises(P.PulledError) as ctx:
                    self.write_pulled(heads=heads, state=state)
                self.assertEqual(ctx.exception.reasons, [want])
        self.assertFalse(os.path.exists(self.pulled))


class Tree(Base):
    def tar(self, members) -> str:
        path = os.path.join(self.base, "t.tar")
        with tarfile.open(path, "w") as tar:
            for info, data in members:
                tar.addfile(info, io.BytesIO(data) if data is not None else None)
        return path

    @staticmethod
    def info(name, kind=tarfile.REGTYPE, size=0, link="", mode=0o644):
        ti = tarfile.TarInfo(name)
        ti.type, ti.size, ti.linkname, ti.mode = kind, size, link, mode
        return ti

    def test_modes_and_inside_links_are_kept(self):
        path = self.tar([(self.info("d", tarfile.DIRTYPE, mode=0o755), None),
                         (self.info("d/run.sh", size=2, mode=0o4755), b"x\n"),
                         (self.info("d/link", tarfile.SYMTYPE, link="run.sh"), None)])
        dest = os.path.join(self.base, "x")
        P.extract_tree(path, dest)
        self.assertEqual(os.stat(os.path.join(dest, "d/run.sh")).st_mode & 0o7777, 0o755)
        self.assertEqual(os.readlink(os.path.join(dest, "d/link")), "run.sh")

    def test_unsafe_members_refuse_the_tree(self):
        for name, info in (("dotdot", self.info("../up", size=1)),
                           ("link_out", self.info("l", tarfile.SYMTYPE, link="../../outside")),
                           ("link_abs", self.info("l", tarfile.SYMTYPE, link="/etc/passwd")),
                           ("fifo", self.info("f", tarfile.FIFOTYPE)),
                           ("device", self.info("c", tarfile.CHRTYPE))):
            with self.subTest(name):
                path = self.tar([(info, b"x" if info.size else None)])
                dest = os.path.join(self.base, "x-" + name)
                with self.assertRaises(P.PulledError) as ctx:
                    P.extract_tree(path, dest)
                self.assertEqual(ctx.exception.reasons, ["tree_unsafe"])
                self.assertFalse(os.path.lexists(os.path.join(self.base, "up")))

    def test_an_absolute_name_is_made_relative(self):
        dest = os.path.join(self.base, "x")
        P.extract_tree(self.tar([(self.info("/abs", size=1), b"x")]), dest)
        self.assertEqual(os.listdir(dest), ["abs"])

    def test_unreadable_and_existing_destination(self):
        path = os.path.join(self.base, "t.tar")
        with open(path, "wb") as fh:
            fh.write(b"not a tar" * 100)
        with self.assertRaises(P.PulledError) as ctx:
            P.extract_tree(path, os.path.join(self.base, "x"))
        self.assertEqual(ctx.exception.reasons, ["tree_unreadable"])
        with self.assertRaises(P.PulledError) as ctx:
            P.extract_tree(path, self.base)
        self.assertEqual(ctx.exception.reasons, ["tree_dest_exists"])


class KosJob(Base):
    def run_kos(self, runner=None, env=None) -> dict:
        return J.run("kos", dict({"RUNNER_TEMP": self.temp}, **(env or {})), runner=runner or RedAs())

    def results(self, *parts) -> str:
        return os.path.join(self.temp, "out", "results", *parts)

    def decide(self, cid: str) -> dict:
        """MF8's own command on the pulled candidate and the files the job wrote."""
        proc = subprocess.run(
            [sys.executable, "-m", "gate.check", "decide", os.path.join(self.pulled, "candidates", cid),
             self.results("base.jsonl"), self.results("c", cid), self.results("c", cid, "hashes.json")],
            input=json.dumps({"control": {"merge_paused": False}, "unfinished_sentinels": []}).encode(),
            cwd=REFEREE, capture_output=True)
        return json.loads(proc.stdout)

    def test_pulled_to_results_to_the_gate(self):
        self.write_pulled({"good": candidate(GOOD), "breaks": candidate(BREAKS_TEST), "raises": candidate(RAISES)})
        runner = RedAs()
        out = self.run_kos(runner)
        self.assertEqual((out["ok"], out.get("reason"), out["done"], out["job"]), (True, None, ["D3"], "kos"))
        self.assertEqual(out["index"]["base"], {"verdict": "verified", "reasons": []})
        self.assertEqual({c: v["verdict"] for c, v in out["index"]["candidates"].items()},
                         {"good": "verified", "breaks": "verified", "raises": "verified"})
        with open(self.results("index.json")) as fh:
            self.assertEqual(json.load(fh), out["index"])
        self.assertEqual(self.decide("good")["decision"], "merge")
        self.assertEqual((self.decide("breaks")["decision"], self.decide("breaks")["reasons"]), ("reject", ["tests_red"]))
        self.assertIn("ratchet_increase", self.decide("raises")["reasons"])
        # every contained run had the job's red control: 3 base lint, 3 x (3 lint + 1 test)
        self.assertEqual(runner.red_seen, 15)
        self.assertEqual(len(runner.calls), 30)

    def test_no_unfinished_merge_watches_nothing(self):
        head = HEADS["brain/integration"]
        for rows in ([START], [START, merge("c1", head), reverted("r1", head, "test_regression")]):
            with self.subTest(rows=len(rows)):
                shutil.rmtree(self.temp, ignore_errors=True)
                self.write_pulled(state=dict(state_files(), **{"ledger.jsonl": ledger_with(rows)}))
                out = self.run_kos()
                self.assertEqual((out["ok"], out["done"], out["index"]["sentinel"]), (True, ["D3"], None))
                self.assertFalse(os.path.exists(self.results("sentinel.json")))

    def test_the_unfinished_merge_at_the_head_is_watched(self):
        head = HEADS["brain/integration"]
        self.write_pulled(state=dict(state_files(), **{"ledger.jsonl": ledger_with([START, merge("c1", head)])}))
        out = self.run_kos()
        self.assertEqual((out["ok"], out["done"]), (True, ["D3", "D7"]))
        self.assertEqual((out["index"]["sentinel"]["merge_sha"], out["index"]["sentinel"]["verdict"]), (head, "green"))
        with open(self.results("sentinel.json")) as fh:
            self.assertEqual(json.load(fh)["merge_sha"], head)

    def test_an_unfinished_merge_elsewhere_runs_nothing(self):
        head, other = HEADS["brain/integration"], "d" * 40
        for rows, want in (([START, merge("c1", other)], ["unfinished:" + other]),
                           ([START, merge("c1", other), merge("c2", head)], ["unfinished:" + other,
                                                                             "unfinished:" + head])):
            with self.subTest(rows=len(rows)):
                shutil.rmtree(self.temp, ignore_errors=True)
                self.write_pulled(state=dict(state_files(), **{"ledger.jsonl": ledger_with(rows)}))
                runner = RedAs()
                out = self.run_kos(runner)
                self.assertEqual((out["reason"], out["reasons"]), ("sentinel_unplaced", want))
                self.assertEqual(runner.calls, [])
                self.assertFalse(os.path.exists(self.results()))

    def test_a_state_it_cannot_read_runs_nothing(self):
        self.write_pulled(state=dict(state_files(), **{"ledger.jsonl": state_files([row("x", "events", "nope", {})])[
            "ledger.jsonl"]}))
        runner = RedAs()
        out = self.run_kos(runner)
        self.assertEqual(out["reason"], "state_refused")
        self.assertTrue(out["reasons"])
        self.assertEqual(runner.calls, [])

    def test_the_red_control_is_the_jobs_own(self):
        self.write_pulled({"good": candidate(GOOD)})
        out = self.run_kos(RedAs("pkg/green.py"))
        self.assertEqual(out["index"]["base"]["verdict"], "no_verdict")
        self.assertIn("red_control_green", out["index"]["base"]["reasons"])
        self.assertEqual(out["index"]["candidates"]["good"]["reasons"], ["base_unavailable"])
        self.assertFalse(os.path.exists(self.results("base.jsonl")))
        self.assertEqual(J.RED_CONTROL, {"cmd": ["node", "-e", "process.exit(1)"]})

    def test_a_tampered_artifact_runs_nothing(self):
        self.write_pulled({"good": candidate(GOOD)})
        with open(os.path.join(self.pulled, "candidates/good/diff.patch"), "ab") as fh:
            fh.write(b"+eval(1);\n")
        runner = RedAs()
        out = self.run_kos(runner)
        self.assertEqual((out["reason"], out["reasons"]), ("pulled_invalid", ["hash_mismatch:candidates/good/diff.patch"]))
        self.assertEqual(runner.calls, [])
        self.assertFalse(os.path.exists(self.results()))

    def test_one_unit_only(self):
        for units in ({"units": [recipe(), recipe(unit_id="b")]}, {"units": []}, {"unit": recipe()}, [recipe()]):
            with self.subTest(units=str(units)[:40]):
                shutil.rmtree(self.temp, ignore_errors=True)
                self.write_pulled(units=units)
                runner = RedAs()
                self.assertEqual(self.run_kos(runner)["reason"], "units_not_one")
                self.assertEqual(runner.calls, [])

    def test_an_unsafe_tree_runs_nothing(self):
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            info = tarfile.TarInfo("pkg/link")
            info.type, info.linkname = tarfile.SYMTYPE, "../../../etc"
            tar.addfile(info)
        self.write_pulled(tree_tar=buf.getvalue())
        runner = RedAs()
        out = self.run_kos(runner)
        self.assertEqual((out["reason"], out["reasons"]), ("pulled_invalid", ["tree_unsafe"]))
        self.assertEqual(runner.calls, [])

    def test_the_deps_artifact_is_taken_by_its_address(self):
        # in/deps is the download of getir's out/deps: one <address>/ directory, which unit.verify takes by its
        # hash (the whole hand-over is test_loop_getir.py); an artifact laid out flat runs nothing
        self.write_pulled()
        write_tree(os.path.join(self.temp, "in", "deps"), {"manifest.json": "{}"})
        runner = RedAs()
        self.assertEqual(self.run_kos(runner)["reason"], "deps_invalid")
        self.assertEqual(runner.calls, [])
        shutil.rmtree(os.path.join(self.temp, "in", "deps"))
        write_tree(os.path.join(self.temp, "in", "deps"), {"ab" * 32 + "/manifest.json": "{}"})
        out = self.run_kos()
        self.assertEqual((out["index"]["base"]["verdict"], out["index"]["base"]["reasons"]),
                         ("no_verdict", ["deps:address_mismatch"]))
        shutil.rmtree(self.results())
        shutil.rmtree(os.path.join(self.temp, "in", "deps"))
        os.makedirs(os.path.join(self.temp, "in", "deps"))
        self.assertEqual(self.run_kos()["index"]["base"]["verdict"], "verified")

    def test_the_inputs_only(self):
        self.write_pulled()
        write_tree(self.src, {"other/outside.js": "var o = 1;\n"})
        shutil.rmtree(self.pulled)
        self.write_pulled()
        self.run_kos()
        with open(self.results("base.jsonl"), "rb") as fh:
            self.assertNotIn(b"other/outside.js", fh.read())

    def test_the_targets_entry_reaches_the_staging(self):
        # the operator's excluded_paths keep a file out of the worktree: here the unit's own lint script
        self.write_pulled(target=dict(TARGET, excluded_paths=["pkg/lint.py"]))
        out = self.run_kos()
        self.assertEqual(out["index"]["base"]["verdict"], "refused")
        self.assertIsNone(out["index"]["base_run_sha256"])

    def test_secret_is_refused_before_anything_is_read(self):
        self.write_pulled()
        runner = RedAs()
        var = "WRITER_TOKEN"
        out = self.run_kos(runner, {var: "x"})
        self.assertEqual(out["reason"], "secret_in_code_job:" + var)
        self.assertEqual(runner.calls, [])

    def test_unusable(self):
        with self.assertRaises(J.Unusable):
            J.run("kos", {})
        with self.assertRaises(J.Unusable):
            J.run("kos", {"RUNNER_TEMP": "relative"})
        self.write_pulled(units={"units": [recipe(lint_cmd="not a list")]})
        out = self.run_kos()
        self.assertEqual(out["index"]["base"]["verdict"], "refused")
        with self.assertRaises(J.Unusable):
            self.run_kos()

    def test_command_line(self):
        env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "SYSTEMROOT")}
        proc = subprocess.run([sys.executable, "-m", "loop.job", "run", "kos"], cwd=REFEREE, env=env,
                              capture_output=True)
        self.assertEqual((proc.returncode, json.loads(proc.stdout)), (2, {"ok": False, "reason": None}))
        proc = subprocess.run([sys.executable, "-m", "loop.job", "run", "kos"], cwd=REFEREE,
                              env=dict(env, RUNNER_TEMP=self.temp), capture_output=True)
        out = json.loads(proc.stdout)
        self.assertEqual((proc.returncode, out["reason"], out["reasons"]), (1, "pulled_invalid", ["manifest_unreadable"]))


if __name__ == "__main__":
    unittest.main()
