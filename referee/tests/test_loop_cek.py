"""Test 46 (asama-0/09), MF17, D1: ``loop.cek``, ``çek``'s assembly of the ``pulled`` artifact.

- the tree: the target's git objects (``git_store``) through ``loop.gitobj.tree_tar`` (its own rules are
  ``test_gitobj.py``'s); a commit the source lacks is listed with the brain's reasons;
- the brain, as git objects too (``git_store``): the ``targets[]`` entry, ``units.json`` and every candidate
  directory, read as committed (links, gitlinks, trees where a file belongs, legacy modes), each refusal listed
  together and nothing written, the brain's own object reasons marked ``brain:``; an id that is not one path
  component reads nothing;
- end to end: the target's and the brain's git objects -> ``assemble`` -> ``loop.job run kos`` -> ``gate.check
  decide``: the good candidate merges, the test-breaking one is rejected (``tests_red``);
- the ``cek`` job's D1 accepted-SHA check (``loop.job.cek_d1``): a fake Actions API and verifier, the real
  ``loop.fetch`` and ``loop.gitobj.GitBatch`` with ``git_store``'s test ``git`` holding the brain's commit, the
  checkout's ``setup/imports.jsonl``, ``setup/summary.json`` and ``policy.json``; then the target half: the heads
  read by ``loop.fetch.heads`` (the fake ``git``'s ``ls-remote`` answer), ``brain/integration``'s head fetched and
  ``loop.cek.assemble`` run on both repositories' objects: agreeing hashes end ``cycle_not_wired`` with
  ``accepted``, ``heads`` and ``assembled``, the artifact in the job's work directory (``loop.pulled.read`` takes it)
  and none in ``out/pulled``; a different or refused ``referee/``, a broken import, an unknown target or one
  without a safe ``repo``, a missing head and what ``assemble`` refuses are refusals (exit 1); an unset variable, an
  unverified state, an unreadable checkout file, a failed listing or fetch are unusable (exit 2).
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tarfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loop import cek as C  # noqa: E402
from loop import job as J  # noqa: E402
from loop import pulled as P  # noqa: E402
from loop import treehash as T  # noqa: E402
import git_store as S  # noqa: E402
from profile_tree import writable_base, write_tree  # noqa: E402
from test_kos import BREAKS_TEST, GOOD, operating, recipe  # noqa: E402
import test_loop_kos as LK  # noqa: E402
from test_loop_kos import TREE, candidate  # noqa: E402

SUMMARY = {"targets": [{"id": "t1", "kind": "toy", "excluded_paths": [], "unit_candidates": []},
                       {"id": "t2", "kind": "copy", "excluded_paths": ["x"], "unit_candidates": []}]}
POLICY = json.dumps({"operating": operating()}).encode()


def names(tar_bytes: bytes) -> list[tuple[str, bytes, str, int]]:
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tar:
        return [(m.name, m.type, m.linkname, m.mode) for m in tar.getmembers()]


def target_objects(root: str) -> tuple[dict, str]:
    """The target's tree ``root`` as git objects and its commit (``git_store``, git's own format)."""
    return S.store(S.from_dir(root))


def brain_files() -> dict:
    """The brain at its accepted commit: ``units.json`` and two ready candidates (``git_store`` input)."""
    files: dict = {"targets/t1/units.json": json.dumps({"units": [recipe()]}).encode()}
    for cid, diff in (("good", GOOD), ("breaks", BREAKS_TEST)):
        for f, data in candidate(diff).items():
            files["candidates/t1/%s/%s" % (cid, f)] = data
    return files


class Brain(unittest.TestCase):
    def setUp(self) -> None:
        self.base = writable_base("t-cek-brain-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.src = os.path.join(self.base, "src")
        write_tree(self.src, TREE)
        self.brain = brain_files()
        self.out = os.path.join(self.base, "pulled")

    def assemble(self, target_id="t1", summary=None, commit=None, policy=POLICY, brain_commit=None):
        summary = json.dumps(SUMMARY if summary is None else summary).encode() if not isinstance(summary, bytes) \
            else summary
        objects, own = target_objects(self.src)
        brain, brain_own = S.store(self.brain)
        return C.assemble(brain.__getitem__, brain_commit or brain_own, summary, policy, target_id,
                          objects.__getitem__, commit or own, self.out)

    def refused(self, **kw) -> list[str]:
        with self.assertRaises(P.PulledError) as ctx:
            self.assemble(**kw)
        self.assertFalse(os.path.lexists(self.out))
        return ctx.exception.reasons

    def drop(self, prefix: str) -> None:
        for path in [p for p in self.brain if p == prefix or p.startswith(prefix + "/")]:
            del self.brain[path]

    def test_the_artifact(self):
        self.assemble()
        got = P.read(self.out)
        self.assertEqual(got.target, SUMMARY["targets"][0])
        self.assertEqual(got.units, {"units": [recipe()]})
        self.assertEqual(got.policy, json.loads(POLICY))
        self.assertEqual(got.candidates, {"good": candidate(GOOD), "breaks": candidate(BREAKS_TEST)})
        with open(got.tree_tar, "rb") as fh:
            self.assertEqual(sorted(n[0] for n in names(fh.read()) if n[1] == tarfile.REGTYPE), sorted(TREE))

    def test_the_brain_as_committed(self):
        # blob bytes as they are (no checkout: .gitattributes cannot touch a diff.patch); git's legacy 100664
        # mode is a file; other targets' and other top-level entries are not read
        self.brain[".gitattributes"] = b"* text eol=lf\n*.patch filter=x\n"
        self.brain["candidates/t1/good/diff.patch"] = ("100664", candidate(GOOD)["diff.patch"].replace(b"\n", b"\r\n"))
        self.brain["targets/t1/units.json"] = ("100755", self.brain["targets/t1/units.json"])
        self.brain["targets/t9/units.json"] = ("160000", b"x")
        self.brain["other"] = ("160000", b"x")
        # a candidate id that extends another's is its own directory
        self.brain.update({"candidates/t1/good-2/" + f: data for f, data in candidate(GOOD).items()})
        self.assemble()
        got = P.read(self.out)
        self.assertEqual(sorted(got.candidates), ["breaks", "good", "good-2"])
        self.assertEqual(got.candidates["good"]["diff.patch"], candidate(GOOD)["diff.patch"].replace(b"\n", b"\r\n"))
        self.assertEqual(got.units, {"units": [recipe()]})

    def test_no_candidates(self):
        self.drop("candidates/t1")
        self.brain["candidates/t2/x/diff.patch"] = b"x"  # another target's are not read
        self.assemble()
        self.assertEqual(P.read(self.out).candidates, {})
        shutil.rmtree(self.out)
        self.drop("candidates")
        self.assemble()
        self.assertEqual(P.read(self.out).candidates, {})

    def test_every_reason_together_and_nothing_written(self):
        self.brain["candidates/t1/good/notes.md"] = b"x"
        del self.brain["targets/t1/units.json"]
        self.brain["targets/t1/other.json"] = b"{}"
        self.assertEqual(self.refused(summary={"targets": []}, commit="b" * 40),
                         ["target_unknown", "units_missing", "candidate_invalid:good", "object_missing:%s" % ("b" * 40)])

    def test_the_brains_own_reasons_are_marked(self):
        self.assertEqual(self.refused(brain_commit="a" * 39), ["brain:commit_unreadable"])
        self.assertEqual(self.refused(brain_commit="a" * 40), ["brain:object_missing:%s" % ("a" * 40)])
        self.brain["candidates/t1/good/sub"] = ("160000", b"x")
        self.brain["candidates/t1/breaks/odd"] = ("1x", b"x")
        self.assertEqual(self.refused(), ["brain:tree_mode:breaks/odd:1x", "brain:tree_submodule:good/sub"])

    def test_the_target_id_is_one_path_component(self):
        self.brain["targets/x/units.json"] = b"{}"
        for bad in ("", "../x", "a/b", ".", "..", ".hidden", "t1\n", None, "x" * 129):
            with self.subTest(bad=bad):
                self.assertEqual(self.refused(target_id=bad), ["target_id_unsafe"])

    def test_the_summary(self):
        for summary, reason in ((b"{", "summary_unreadable"), ({"targets": {}}, "summary_unreadable"),
                                ([SUMMARY], "summary_unreadable"), ({"targets": [{"id": "t2"}]}, "target_unknown"),
                                ({"targets": [{"id": "t1"}, {"id": "t1", "kind": "copy"}]}, "target_ambiguous")):
            with self.subTest(reason=reason, summary=str(summary)[:30]):
                self.assertEqual(self.refused(summary=summary), [reason])

    def test_units_must_be_a_file_reached_through_trees(self):
        units = self.brain["targets/t1/units.json"]
        for name, change in (
                ("a link", {"targets/t1/units.json": ("120000", b"../../elsewhere/units.json")}),
                ("a gitlink", {"targets/t1/units.json": ("160000", units)}),
                ("a tree", {"targets/t1/units.json/x": units}),
                ("a link on the way", {"targets/t1": ("120000", b"../elsewhere"), "elsewhere/units.json": units}),
                ("a file on the way", {"targets/t1": units}),
                ("a link for targets", {"targets": ("120000", b"elsewhere"), "elsewhere/t1/units.json": units})):
            with self.subTest(name):
                self.drop("targets")
                self.drop("elsewhere")
                self.brain.update(change)
                self.assertEqual(self.refused(), ["units_missing"])

    def test_candidate_directories(self):
        root = "candidates/t1/"
        breaks = {f: self.brain[root + "breaks/" + f] for f in P.CANDIDATE_FILES}
        cases = []
        del self.brain[root + "good/expect.json"]
        cases.append(("a file missing", "good"))
        self.brain[root + "loose.patch"] = b"x"
        cases.append(("a file in candidates/<id>", "loose.patch"))
        self.brain.update({root + ".hidden/" + f: data for f, data in breaks.items()})
        cases.append(("not a candidate id", ".hidden"))
        self.brain[root + "linked"] = ("120000", b"breaks")
        cases.append(("a linked candidate", "linked"))
        self.brain.update({root + "filelink/" + f: data for f, data in breaks.items()})
        self.brain[root + "filelink/finding.json"] = ("120000", b"../breaks/finding.json")
        cases.append(("a linked file", "filelink"))
        self.brain.update({root + "subdir/" + f: data for f, data in breaks.items() if f != "diff.patch"})
        self.brain[root + "subdir/diff.patch/x"] = b"x"
        cases.append(("a tree for a file", "subdir"))
        self.brain.update({root + "extra/" + f: data for f, data in breaks.items()})
        self.brain[root + "extra/notes.md"] = b"x"
        cases.append(("a fourth file", "extra"))
        self.assertEqual(self.refused(), sorted("candidate_invalid:%s" % name for _, name in cases))

    def test_candidates_must_be_trees(self):
        cands = {p: v for p, v in self.brain.items() if p.startswith("candidates/")}
        for name, change in (("candidates a link", {"candidates": ("120000", b"cands")}),
                             ("candidates/<id> a link", {"candidates/t1": ("120000", b"../cands/t1")}),
                             ("candidates/<id> a file", {"candidates/t1": b"a file"}),
                             ("candidates a gitlink", {"candidates": ("160000", b"x")}),
                             ("candidates/<id> malformed", {"candidates/t1": ("1x", b"x")})):
            with self.subTest(name):
                self.drop("candidates")
                self.drop("cands")
                self.brain.update({"cands/" + p[len("candidates/"):]: v for p, v in cands.items()})
                self.brain.update(change)
                self.assertEqual(self.refused(), ["candidates_not_directory"])

    def test_the_read_back_refuses_and_removes(self):
        self.brain["targets/t1/units.json"] = b"not json"
        self.assertEqual(self.refused(), ["json_unreadable:units.json"])
        self.assertEqual(self.refused(policy=b"\xff"), ["json_unreadable:units.json", "json_unreadable:policy.json"])

    def test_out_must_not_exist(self):
        os.makedirs(self.out)
        with self.assertRaises(FileExistsError):
            self.assemble()


class EndToEnd(LK.Base):
    """The target's and the brain's git objects -> cek's assembly -> the kos job -> MF8's decision."""

    run_kos, results, decide = LK.KosJob.run_kos, LK.KosJob.results, LK.KosJob.decide

    def test_cek_to_kos_to_the_gate(self):
        brain, brain_commit = S.store(brain_files())
        objects, commit = target_objects(self.src)
        C.assemble(brain.__getitem__, brain_commit, json.dumps(SUMMARY).encode(), POLICY, "t1", objects.__getitem__,
                   commit, self.pulled)
        out = self.run_kos()
        self.assertEqual((out["reason"], out["done"]), ("cycle_not_wired", ["D3"]))
        self.assertEqual(out["index"]["base"], {"verdict": "verified", "reasons": []})
        self.assertEqual(self.decide("good")["decision"], "merge")
        self.assertEqual((self.decide("breaks")["decision"], self.decide("breaks")["reasons"]),
                         ("reject", ["tests_red"]))


class CekJob(unittest.TestCase):
    """``loop.job run cek`` up to the assembled ``pulled``: D1's accepted-SHA check, the target's heads, its fetch."""

    BRAIN = dict({"referee/loop/job.py": b"x = 1\n", "referee/a.py": b"a\n",
                  "targets/t1/units.json": b'{"units": []}'},
                 **{"candidates/t1/good/%s" % f: d for f, d in candidate(GOOD).items()})
    TARGET = {"a.js": b"const a = 1;\n", "lib/b.js": b"b\n"}
    STATE_HEAD = "5" * 40

    def setUp(self) -> None:
        import test_accepted as TA
        self.TA = TA
        self.base = writable_base("t-cek-job-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.temp = os.path.join(self.base, "temp")
        self.work = os.path.join(self.base, "checkout")
        self.bin = os.path.join(self.base, "bin")
        for d in (self.temp, os.path.join(self.work, "setup"), self.bin):
            os.makedirs(d)
        self.summary = {"targets": [{"id": "t1", "kind": "toy", "repo": "o/target", "excluded_paths": [],
                                     "unit_candidates": []}]}
        with open(os.path.join(self.work, "policy.json"), "wb") as fh:
            fh.write(POLICY)

    def listing(self, integration: str | None, state: str | None = STATE_HEAD) -> bytes:
        rows = [(state, "refs/heads/brain/state"), (integration, "refs/heads/brain/integration")]
        return b"".join(b"%s\t%s\n" % (sha.encode(), ref.encode()) for sha, ref in rows if sha)

    def run_cek(self, brain=None, imported=None, verifier=None, exits=None, env=None, http=None, listing=None,
                target=None, summary=None):
        objects, commit = S.store(self.BRAIN if brain is None else brain)
        tobjects, self.target_commit = S.store(self.TARGET)
        if target is not None:
            tobjects = target
        answers = {sha: S.batch_record(sha, kind, data) for sha, (kind, data) in dict(objects, **tobjects).items()}
        git = S.install_git(self.bin, answers, exits=exits,
                            listing=self.listing(self.target_commit) if listing is None else listing)
        tree = T.digest([(p, "file", d) for p, d in self.BRAIN.items()])
        with open(os.path.join(self.work, "setup", "imports.jsonl"), "wb") as fh:
            fh.write(self.TA.chained([self.TA.import_row(tree if imported is None else imported, commit)])
                     if imported != "" else b"")
        with open(os.path.join(self.work, "setup", "summary.json"), "wb") as fh:
            fh.write(json.dumps(self.summary if summary is None else summary).encode())
        zip_bytes = self.TA.zip_of({"result.json": self.TA.result(commit), "result.json.sigstore.json": b"{}"})
        api = http or self.TA.FakeApi([self.TA.artifact(11, "2026-11-01T00:00:00Z")], zip_bytes)
        environ = {"RUNNER_TEMP": self.temp, "GITHUB_REPOSITORY": "o/referee", "GITHUB_TOKEN": "t",
                   "GITHUB_WORKSPACE": self.work, "LOOP_BRAIN_REPO": "o/brain", "LOOP_TARGET": "t1",
                   "PATH": os.environ.get("PATH", "")}
        environ.update(env or {})
        self.verified: list = []

        def verify(argv):
            self.verified.append(argv)
            return 0
        out = J.run("cek", {k: v for k, v in environ.items() if v is not None}, http=api,
                    verifier=verifier or verify, git=git)
        self.assertFalse(os.path.lexists(os.path.join(self.temp, "out", "pulled")))  # nothing for the upload step
        return out, commit, tree

    def assembled(self) -> list[str]:
        work = os.path.join(self.temp, "work")
        return [os.path.join(work, d, "pulled") for d in sorted(os.listdir(work))
                if os.path.isdir(os.path.join(work, d, "pulled"))] if os.path.isdir(work) else []

    def test_the_job_checks_the_accepted_sha_and_writes_no_pulled(self):
        out, commit, tree = self.run_cek()
        self.assertEqual(out["reason"], "cycle_not_wired")
        self.assertEqual((out["ok"], out["checked"]), (False, ["accepted_sha", "referee_tree", "heads", "assembled"]))
        self.assertEqual(out["accepted"]["brain_sha"], commit)
        self.assertEqual(out["accepted"]["referee_tree_sha256"], tree)
        self.assertEqual(out["accepted"]["artifact_id"], 11)
        self.assertIn("https://github.com/o/referee/.github/workflows/bootstrap.yml@refs/heads/main", self.verified[0])
        argvs = [c["argv"] for c in S.calls(self.bin)]
        fetches = [a for a in argvs if "fetch" in a]
        self.assertEqual([(f[-2], f[-1]) for f in fetches],
                         [("https://github.com/o/brain", "%s:refs/pulled" % commit),
                          ("https://github.com/o/target", "%s:refs/pulled" % self.target_commit)])
        listings = [a for a in argvs if "ls-remote" in a]
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0][-4:], ["--", "https://github.com/o/target", "refs/heads/brain/state",
                                            "refs/heads/brain/integration"])
        self.assertEqual(out["heads"], {"brain/state": self.STATE_HEAD, "brain/integration": self.target_commit})
        self.assertEqual(out["assembled"], {"target": "t1", "commit": self.target_commit, "candidates": ["good"]})
        # the artifact is assembled in the job's work directory, and loop.pulled reads it: the target's tree at
        # brain/integration's head, the brain's units.json and candidate at the accepted commit
        [path] = self.assembled()
        art = P.read(path)
        with open(art.tree_tar, "rb") as fh:
            members = names(fh.read())
        self.assertEqual(sorted(n for n, t, _, _ in members if t == tarfile.REGTYPE),
                         ["a.js", "lib/b.js"])
        self.assertEqual(art.units, {"units": []})
        self.assertEqual(sorted(art.candidates), ["good"])
        self.assertEqual(art.target["repo"], "o/target")

    def test_a_referee_tree_that_is_not_the_imported_one(self):
        out, _, _ = self.run_cek(imported="0" * 64)
        self.assertEqual((out["ok"], out["reason"]), (False, "referee_tree_mismatch"))
        self.assertNotIn("accepted", out)
        changed = dict(self.BRAIN, **{"referee/a.py": b"b\n"})
        out, _, _ = self.run_cek(brain=changed)
        self.assertEqual(out["reason"], "referee_tree_mismatch")
        self.assertFalse([a for c in S.calls(self.bin) for a in c["argv"] if a == "ls-remote"])  # nothing after it

    def test_a_refused_tree_and_a_broken_import(self):
        out, _, _ = self.run_cek(brain=dict(self.BRAIN, **{"referee/Setup": b""}))
        self.assertEqual((out["reason"], out["reasons"]), ("referee_tree_refused", ["operator_name:Setup"]))
        out, _, _ = self.run_cek(imported="")
        self.assertEqual(out["reason"], "imports_no_transfer")

    def test_a_missing_head_is_a_refusal_and_nothing_is_fetched(self):
        for listing, reasons in ((self.listing(None), ["head_missing:brain/integration"]),
                                 (self.listing("6" * 40, None), ["head_missing:brain/state"]),
                                 (b"", ["head_missing:brain/state", "head_missing:brain/integration"])):
            with self.subTest(reasons=reasons):
                os.remove(os.path.join(self.bin, "calls.jsonl")) if os.path.exists(
                    os.path.join(self.bin, "calls.jsonl")) else None
                out, _, _ = self.run_cek(listing=listing)
                self.assertEqual([out["reason"]] + out.get("reasons", []), reasons)
                self.assertIn("accepted", out)
                self.assertEqual(len([c for c in S.calls(self.bin) if "fetch" in c["argv"]]), 1)  # the brain's only
                self.assertEqual(self.assembled(), [])

    def test_the_target_entry(self):
        for summary, reason in (({"targets": []}, "target_unknown"), ({"x": 1}, "summary_unreadable"),
                                ({"targets": [{"id": "t1", "repo": "o/target"}] * 2}, "target_ambiguous"),
                                ({"targets": [{"id": "t1"}]}, "target_repo_unsafe"),
                                ({"targets": [{"id": "t1", "repo": "o/../x"}]}, "target_repo_unsafe"),
                                ({"targets": [{"id": "t1", "repo": "https://github.com/o/t"}]}, "target_repo_unsafe")):
            with self.subTest(reason=reason, summary=summary):
                out, _, _ = self.run_cek(summary=summary)
                self.assertEqual(out["reason"], reason)
                self.assertNotIn("heads", out)
        out, _, _ = self.run_cek(env={"LOOP_TARGET": "t2"})
        self.assertEqual(out["reason"], "target_unknown")

    def test_what_assemble_refuses_is_a_refusal(self):
        brain = {p: d for p, d in self.BRAIN.items() if p != "targets/t1/units.json"}
        brain["candidates/t1/bad name/x"] = b""
        self.BRAIN = brain
        out, _, _ = self.run_cek()
        self.assertEqual((out["reason"], out["reasons"]), ("pulled_refused", ["units_missing",
                                                                               "candidate_invalid:bad name"]))
        self.assertEqual(out["heads"]["brain/integration"], self.target_commit)
        self.assertEqual(self.assembled(), [])

    def test_no_verdict(self):
        for kw in ({"env": {"GITHUB_TOKEN": None}}, {"env": {"LOOP_BRAIN_REPO": None}},
                   {"env": {"LOOP_TARGET": None}}, {"env": {"LOOP_BRAIN_REPO": "o/brain/x"}},
                   {"verifier": lambda argv: 1}, {"exits": {"fetch": 128}}, {"http": self.TA.FakeApi([], b"")},
                   {"exits": {"ls-remote": 128}}, {"listing": b"garbage\n"},
                   {"target": {}}):  # the target's fetch brings no commit: its read-back fails
            with self.subTest(kw=kw):
                shutil.rmtree(self.temp)
                os.makedirs(self.temp)
                with self.assertRaises(J.Unusable):
                    self.run_cek(**kw)
        for name in ("setup/imports.jsonl", "setup/summary.json", "policy.json"):
            with self.subTest(missing=name):
                self.run_cek()  # writes the checkout's files
                os.remove(os.path.join(self.work, *name.split("/")))
                with self.assertRaisesRegex(J.Unusable, name):
                    J.run("cek", {"RUNNER_TEMP": self.temp, "GITHUB_REPOSITORY": "o/r", "GITHUB_TOKEN": "t",
                                  "GITHUB_WORKSPACE": self.work, "LOOP_BRAIN_REPO": "o/b", "LOOP_TARGET": "t1"},
                          http=self.TA.FakeApi([self.TA.artifact(1, "2026-11-01T00:00:00Z")],
                                               self.TA.zip_of(self.TA.GOOD_ZIP)), verifier=lambda argv: 0)
                if name == "policy.json":
                    with open(os.path.join(self.work, "policy.json"), "wb") as fh:
                        fh.write(POLICY)


if __name__ == "__main__":
    unittest.main()
