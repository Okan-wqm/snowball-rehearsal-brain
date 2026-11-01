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
  read by ``loop.fetch.heads`` (the fake ``git``'s ``ls-remote`` answer), ``brain/state``'s head and its parent
  fetched into their own git directories and verified (``loop.state``'s rules are ``test_loop_state.py``'s; here a
  genesis head without parent, a rewritten ledger, a missing file and a merge head are ``state_refused`` before the
  target is fetched, a state commit the fetch did not bring is unusable), then MF11's verify of the head's root
  with a fake Rekor (``FakeRekor``; ``loop.rekor``'s own rules are ``test_rekor.py``'s) and the same fake verifier:
  the root row anchoring the head's ledger and its entry verified against ``loop.yml``'s identity; a ledger row no
  root anchors, no entry, another root's entry, an entry the verifier refuses and a last root row without a root
  are ``root_refused`` before the target is fetched, Rekor unreadable is unusable; ``brain/integration``'s head
  fetched and ``loop.cek.assemble`` run on both repositories' objects, then MF4's judgement of the read-back
  artifact: agreeing hashes and a recipe the check accepts end ``ok`` with ``done`` ``["D1"]``, ``accepted``,
  ``heads``, ``state``, ``root``, ``assembled`` and ``profile``, the artifact moved from the job's work directory to
  ``out/pulled`` (``loop.pulled.read`` takes it there), and getir, kos and yaz, each on its own copy of it as the
  download hands it over, run their wired steps on it (cagir's canary with the fake ``claude``); any refusal leaves no ``out/pulled``, and an existing
  ``out/pulled`` (an artifact, an empty directory, a file) is unusable and left as it was;
  a different or refused ``referee/``, a broken import, an unknown target or one without a safe ``repo``, a missing
  head, what ``assemble`` refuses, a ``units`` that is not exactly one recipe, a recipe the derivation of the
  assembled tree refuses (no eligible candidate, a path that is none, an input excluded by the agent-configuration
  rule or by the ``targets[]`` entry, an input the tree lacks), a recipe rule ``getir`` refuses and a tree the
  extraction refuses are refusals (exit 1); an unset variable, an unverified state, an unreadable checkout file, a
  failed listing or fetch are unusable (exit 2).
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

import fake_claude  # noqa: E402
import test_loop_cagir
import yaz_world as YW  # noqa: E402
from dispatcher import llm_call as L  # noqa: E402
from loop import cek as C  # noqa: E402
from loop import job as J  # noqa: E402
from loop import pulled as P  # noqa: E402
from loop import treehash as T  # noqa: E402
import git_store as S  # noqa: E402
from ledger import anchor as AN  # noqa: E402
from loop import accepted as A  # noqa: E402
from loop import rekor as RK  # noqa: E402
from test_rekor import entry_for  # noqa: E402
from profile_tree import writable_base, write_tree  # noqa: E402
from test_kos import BREAKS_TEST, GOOD, operating, recipe  # noqa: E402
import test_loop_kos as LK  # noqa: E402
from test_loop_kos import HEADS, TREE, RedAs, candidate, state_files  # noqa: E402
from test_revert_drill import row  # noqa: E402


def state_rows(n: int) -> list[dict]:
    """The first ``n`` rows of the fixture ``brain/state`` ledgers: ``cycle_start`` rows of ``ledger.schema``, no merge."""
    return [row("l%d" % i, "events", "cycle_start", {"cycle_id": str(i)}) for i in range(n)]


SUMMARY = {"targets": [{"id": "t1", "kind": "toy", "excluded_paths": [], "unit_candidates": []},
                       {"id": "t2", "kind": "copy", "excluded_paths": ["x"], "unit_candidates": []}]}
POLICY = json.dumps({"operating": operating(), "stage_budgets": {"asama_0": {"canary_usd": 1}}}).encode()


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

    def assemble(self, target_id="t1", summary=None, commit=None, policy=POLICY, brain_commit=None,
                 state_head=HEADS["brain/state"], state=None, status=None):
        summary = json.dumps(SUMMARY if summary is None else summary).encode() if not isinstance(summary, bytes) \
            else summary
        objects, own = target_objects(self.src)
        brain, brain_own = S.store(self.brain)
        return C.assemble(brain.__getitem__, brain_commit or brain_own, summary, policy, target_id,
                          objects.__getitem__, commit or own, state_head, state_files() if state is None else state,
                          status, self.out)

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
        # the heads: brain/state's as given, brain/integration's the commit the tree was read from
        self.assertEqual((got.heads, got.state),
                         ({"brain/state": HEADS["brain/state"], "brain/integration": target_objects(self.src)[1]},
                          state_files()))

    def test_the_state_it_carries(self):
        for kw, want in (({"state": {"ledger.jsonl": b"x\n"}}, ["state_incomplete"]),
                         ({"state_head": "A" * 40}, ["heads_invalid"])):
            with self.subTest(kw=kw):
                self.assertEqual(self.refused(**kw), want)

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
                   commit, HEADS["brain/state"], state_files(), None, self.pulled)
        out = self.run_kos()
        self.assertEqual((out["reason"], out["done"]), ("cycle_not_wired", ["D3"]))
        self.assertEqual(out["index"]["base"], {"verdict": "verified", "reasons": []})
        self.assertEqual(self.decide("good")["decision"], "merge")
        self.assertEqual((self.decide("breaks")["decision"], self.decide("breaks")["reasons"]),
                         ("reject", ["tests_red"]))


class FakeRekor:
    """``entry(uuid)`` from ``entries``, recording each uuid asked for."""

    def __init__(self) -> None:
        self.entries: dict = {}
        self.calls: list = []
        self.last: dict = {}  # a state commit -> the uuid of its last root row (the tests' bookkeeping)

    def entry(self, uuid):
        self.calls.append(uuid)
        return self.entries.get(uuid)


class CekJob(unittest.TestCase):
    """``loop.job run cek`` up to the assembled ``pulled``: D1's accepted-SHA check, the target's heads, its fetch."""

    BRAIN = dict({"referee/loop/job.py": b"x = 1\n", "referee/a.py": b"a\n",
                  "targets/t1/units.json": json.dumps({"units": [recipe()]}).encode()},
                 **{"candidates/t1/good/%s" % f: d for f, d in candidate(GOOD).items()})
    TARGET = {p: (json.dumps(v) if isinstance(v, dict) else v).encode() for p, v in TREE.items()}
    STATE = {"ledger.jsonl": [2, 5], "chain/root.jsonl": [1, 2]}  # rows at genesis, at the head on top of it
    STATUS_MD = b"# brain/state\n<!-- status.block -->\nx\n<!-- /status.block -->\n"  # carried, not judged by D1
    ANCHORED = (2, 5, 8)  # root row i anchors the first ANCHORED[i] ledger rows (so genesis's and the head's agree)

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
        self.setUp_state()

    def setUp_state(self) -> None:
        self.state_objects: dict = {}
        self.state_content: dict = {}  # commit -> its chained files as written
        self.rekor = FakeRekor()
        self.state_genesis = self.state_commit({p: n[0] for p, n in self.STATE.items()}, ())
        self.state_head = self.state_commit({p: n[1] for p, n in self.STATE.items()}, (self.state_genesis,),
                                            {"status.md": self.STATUS_MD})

    def state_commit(self, counts: dict, parents: tuple, extra: dict | None = None) -> str:
        """A ``brain/state`` commit whose chained files hold ``counts`` rows (``loop.state``'s rules); root row ``i``
        anchors the ledger's first ``ANCHORED[i]`` rows, its entry in the fake Rekor (``ledger.anchor``'s rules)."""
        ledger = state_rows(max(self.ANCHORED))
        content = {}
        if "ledger.jsonl" in counts:
            content["ledger.jsonl"] = self.TA.chained(ledger[:counts["ledger.jsonl"]])
        if "chain/root.jsonl" in counts:
            roots = b""
            for i in range(counts["chain/root.jsonl"]):
                root = AN.root_of(AN.tips(self.TA.chained(ledger[:self.ANCHORED[i]])))
                uuid, entry = entry_for(RK.payload_digest(root))
                self.rekor.entries[uuid] = entry
                roots = AN.root_row(roots, "r%d" % i, "2026-11-01T00:00:00Z", root, uuid)
            content["chain/root.jsonl"] = roots
        commit = S.store(dict(content, **(extra or {})), parents, self.state_objects)[1]
        self.state_content[commit] = content
        if "chain/root.jsonl" in counts:
            self.rekor.last[commit] = uuid
        return commit

    def listing(self, integration: str | None, state: str | None = "head") -> bytes:
        state = self.state_head if state == "head" else state
        rows = [(state, "refs/heads/brain/state"), (integration, "refs/heads/brain/integration")]
        return b"".join(b"%s\t%s\n" % (sha.encode(), ref.encode()) for sha, ref in rows if sha)

    def run_cek(self, brain=None, imported=None, verifier=None, exits=None, env=None, http=None, listing=None,
                target=None, summary=None, rekor=None):
        objects, commit = S.store(self.BRAIN if brain is None else brain)
        tobjects, self.target_commit = S.store(self.TARGET)
        if target is not None:
            tobjects = target
        answers = {sha: S.batch_record(sha, kind, data)
                   for sha, (kind, data) in dict(objects, **tobjects, **self.state_objects).items()}
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
        self.rekor.calls = []
        out = J.run("cek", {k: v for k, v in environ.items() if v is not None}, http=api,
                    verifier=verifier or verify, git=git, rekor=rekor or self.rekor)
        # the upload step's path holds the artifact exactly when D1 held
        self.assertEqual(os.path.lexists(os.path.join(self.temp, "out", "pulled")), out["ok"])
        return out, commit, tree

    def assembled(self) -> list[str]:
        work = os.path.join(self.temp, "work")
        return [os.path.join(work, d, "pulled") for d in sorted(os.listdir(work))
                if os.path.isdir(os.path.join(work, d, "pulled"))] if os.path.isdir(work) else []

    def test_the_job_runs_d1_and_hands_pulled_to_the_upload(self):
        out, commit, tree = self.run_cek()
        self.assertNotIn("reason", out)
        self.assertEqual((out["ok"], out["done"], out["checked"]),
                         (True, ["D1"], ["accepted_sha", "referee_tree", "heads", "state_previous", "root", "assembled",
                                  "profile"]))
        self.assertEqual(out["state"], {"head": self.state_head, "previous": self.state_genesis,
                                        "rows": {"ledger.jsonl": 5, "chain/root.jsonl": 2}})
        self.assertEqual(out["profile"], {"unit_id": "pkg"})
        self.assertEqual(out["accepted"]["brain_sha"], commit)
        self.assertEqual(out["accepted"]["referee_tree_sha256"], tree)
        self.assertEqual(out["accepted"]["artifact_id"], 11)
        self.assertIn("https://github.com/o/referee/.github/workflows/bootstrap.yml@refs/heads/main", self.verified[0])
        # MF11: the head's root (its ledger's, the last root row's) and its Rekor entry, verified against loop.yml
        root = AN.root_of(AN.tips(self.TA.chained(state_rows(5))))
        uuid = entry_for(RK.payload_digest(root))[0]
        self.assertEqual((out["root"], self.rekor.calls), ({"root": root, "rekor_uuid": uuid}, [uuid]))
        self.assertEqual(len(self.verified), 2)
        self.assertEqual(self.verified[1], A.identity_argv(
            "sigstore", self.verified[1][4], "https://github.com/o/referee/.github/workflows/loop.yml@refs/heads/main",
            "sha256:" + RK.payload_digest(root)))
        argvs = [c["argv"] for c in S.calls(self.bin)]
        fetches = [a for a in argvs if "fetch" in a]
        self.assertEqual([(f[-2], f[-1]) for f in fetches],
                         [("https://github.com/o/brain", "%s:refs/pulled" % commit),
                          ("https://github.com/o/target", "%s:refs/pulled" % self.state_head),
                          ("https://github.com/o/target", "%s:refs/pulled" % self.state_genesis),
                          ("https://github.com/o/target", "%s:refs/pulled" % self.target_commit)])
        # each into its own new git directory of the job's work directory, read there
        dirs = [a.split("=", 1)[1] for f in fetches for a in f if a.startswith("--git-dir=")]
        self.assertEqual([os.path.basename(d) for d in dirs],
                         ["brain.git", "state.git", "state-previous.git", "target.git"])
        batches = [a for a in argvs if "cat-file" in a]
        for d in dirs[1:3]:
            self.assertIn(["--git-dir=%s" % d, "cat-file", "--batch"], [b[-3:] for b in batches])
        listings = [a for a in argvs if "ls-remote" in a]
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0][-4:], ["--", "https://github.com/o/target", "refs/heads/brain/state",
                                            "refs/heads/brain/integration"])
        self.assertEqual(out["heads"], {"brain/state": self.state_head, "brain/integration": self.target_commit})
        self.assertEqual(out["assembled"], {"target": "t1", "commit": self.target_commit, "candidates": ["good"]})
        # the artifact assembled in the job's work directory is moved, not copied, to out/pulled, and loop.pulled
        # reads it there: the target's tree at brain/integration's head, the brain's units.json and candidate at
        # the accepted commit
        self.assertEqual(self.assembled(), [])
        [cek] = os.listdir(os.path.join(self.temp, "work"))
        path = os.path.join(self.temp, "out", "pulled")
        art = P.read(path)
        with open(art.tree_tar, "rb") as fh:
            members = names(fh.read())
        self.assertEqual(sorted(n for n, t, _, _ in members if t == tarfile.REGTYPE), sorted(TREE))
        self.assertEqual(art.units, {"units": [recipe()]})
        # MF4 judged the tree extracted next to the artifact, the one the derivation read
        self.assertEqual(sorted(os.listdir(os.path.join(self.temp, "work", cek, "tree", "pkg"))),
                         sorted(p.split("/", 1)[1] for p in TREE if p.startswith("pkg/")))
        self.assertEqual(sorted(art.candidates), ["good"])
        self.assertEqual(art.target["repo"], "o/target")
        # state/: the heads D1 read and brain/state's files at its head, the bytes verify --previous and the root
        # check judged
        self.assertEqual(art.heads, out["heads"])
        self.assertEqual(art.state, self.state_content[self.state_head])
        self.assertEqual(art.status, self.STATUS_MD)  # the head's status.md, for D6

    def test_getir_kos_cagir_and_yaz_run_on_the_pulled_cek_hands_over(self):
        """The workflow's hand-over, each job on its own runner: cek's ``out/pulled`` downloaded whole as each
        consumer's ``in/pulled`` (then getir's ``deps`` to kos and kos's ``results`` to yaz the same way); every
        consumer's wired steps run on those bytes and judge the brain's candidates cek assembled; cagir's canary
        spends against the ledger D1 verified (its cost rows) and records the head cek read."""
        self.BRAIN = dict(self.BRAIN, **{"candidates/t1/breaks/%s" % f: d for f, d in candidate(BREAKS_TEST).items()})
        out, _, _ = self.run_cek()
        self.assertEqual((out["done"], out["assembled"]["candidates"]), (["D1"], ["breaks", "good"]))
        temps = {}
        for job in ("getir", "kos", "cagir", "yaz"):
            temps[job] = os.path.join(self.base, job)
            shutil.copytree(os.path.join(self.temp, "out", "pulled"), os.path.join(temps[job], "in", "pulled"),
                            symlinks=True)
        got = J.run("getir", {"RUNNER_TEMP": temps["getir"]})
        self.assertEqual((got["ok"], got["done"], got["deps"]["packages"]), (True, ["D2"], 0))
        shutil.copytree(os.path.join(temps["getir"], "out", "deps"), os.path.join(temps["kos"], "in", "deps"))
        got = J.run("kos", {"RUNNER_TEMP": temps["kos"]}, runner=RedAs())
        self.assertEqual((got["done"], got["index"]["base"]), (["D3"], {"verdict": "verified", "reasons": []}))
        claude_dir = os.path.join(self.base, "claude-bin")  # not self.bin: the fake git logs its calls there
        os.makedirs(claude_dir)
        claude = fake_claude.install(claude_dir)
        fake_claude.behave(claude_dir, test_loop_cagir.result())
        got = J.run("cagir", {"RUNNER_TEMP": temps["cagir"], "CLAUDE_CODE_OAUTH_TOKEN": "t",
                              "LOOP_CANARY_MODEL": test_loop_cagir.MODEL, "LOOP_CLAUDE_SHA512": L.sha512_file(claude),
                              "GITHUB_RUN_ID": "1", "GITHUB_RUN_ATTEMPT": "1"}, claude=claude)
        self.assertEqual((got["done"], got["call"]["outcome"]), (["D4"], "ok"))
        with open(os.path.join(temps["cagir"], "out", "response", "response.json")) as fh:
            response = json.load(fh)
        self.assertEqual(response["heads"], out["heads"])
        [call] = fake_claude.calls(claude_dir)
        argv = call["argv"]
        self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "1.000000")  # the head's ledger has no cost row
        shutil.copytree(os.path.join(temps["kos"], "out", "results"), os.path.join(temps["yaz"], "in", "results"))
        shutil.copytree(os.path.join(temps["cagir"], "out", "response"), os.path.join(temps["yaz"], "in", "response"))
        write_tree(os.path.join(temps["yaz"], "control"), {"control.json": {"merge_paused": False}})
        # the target at the heads cek read, brain/state holding the files D1 verified
        gh = YW.github_at(out["heads"], self.TARGET, dict(self.state_content[self.state_head],
                                                         **{"status.md": self.STATUS_MD}), repo="o/target")
        got = J.run("yaz", YW.env(temps["yaz"], self.work, GITHUB_RUN_ID="1"), transport=gh, signer=YW.signer(),
                    now=lambda: YW.NOW)
        self.assertEqual(got["done"], ["D5", "D6"])
        # criterion 8 from the ledger cek verified: no merge in it, so good merges
        self.assertEqual((got["merge"], {cid: d["reasons"] for cid, d in got["decisions"].items()}),
                         ("good", {"good": [], "breaks": ["tests_red"]}))
        self.assertEqual((got["written"]["merge"]["candidate"], gh.refs["brain/integration"]),
                         ("good", got["written"]["merge"]["merge_sha"]))
        # D6 appended cagir's cost row, as the response carried it, onto the ledger cek verified
        ledger = gh.read_file("brain/state", "ledger.jsonl")
        self.assertTrue(ledger.startswith(self.state_content[self.state_head]["ledger.jsonl"]))
        [cost] = [json.loads(line) for line in ledger.splitlines() if json.loads(line)["part"] == "cost"]
        self.assertEqual({k: v for k, v in cost.items() if k not in ("prev_hash", "row_hash")}, response["rows"][0])

    def test_an_existing_out_pulled_is_no_verdict_and_left_as_it_was(self):
        # another run's artifact (or anything) at the upload step's path is neither replaced nor mixed with
        self.run_cek()
        out = os.path.join(self.temp, "out", "pulled")
        before = sorted(os.listdir(out))
        for leftover in ("artifact", "empty", "file"):
            with self.subTest(leftover=leftover):
                if leftover == "empty":
                    shutil.rmtree(out)
                    os.makedirs(out)
                    before = []
                elif leftover == "file":
                    os.rmdir(out)
                    write_tree(os.path.join(self.temp, "out"), {"pulled": "x"})
                with self.assertRaisesRegex(J.Unusable, "out/pulled exists"):
                    self.run_cek()
                if leftover == "file":
                    with open(out) as fh:
                        self.assertEqual(fh.read(), "x")
                else:
                    self.assertEqual(sorted(os.listdir(out)), before)

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

    def target_fetched(self) -> bool:
        return any("%s:refs/pulled" % self.target_commit in c["argv"] for c in S.calls(self.bin))

    def test_a_genesis_head_is_verified_as_chains_only(self):
        self.state_head = self.state_genesis
        out, _, _ = self.run_cek()
        self.assertEqual((out["done"], out["state"]), (["D1"], {
            "head": self.state_genesis, "previous": None, "rows": {"ledger.jsonl": 2, "chain/root.jsonl": 1}}))
        self.assertEqual([a[-1] for a in (c["argv"] for c in S.calls(self.bin)) if "fetch" in a][1:2],
                         ["%s:refs/pulled" % self.state_genesis])
        self.assertFalse([d for d in os.listdir(os.path.join(self.temp, "work", os.listdir(
            os.path.join(self.temp, "work"))[0])) if d == "state-previous.git"])

    def test_a_state_that_does_not_verify_is_a_refusal_before_the_target_is_fetched(self):
        for name, head, reasons in (
                # the head rewrote its parent's ledger: fewer rows than the parent had
                ("rewritten", lambda: self.state_commit({"ledger.jsonl": 1, "chain/root.jsonl": 2},
                                                        (self.state_genesis,)),
                 ["not_append_only:ledger.jsonl:2"]),
                ("no roots", lambda: self.state_commit({"ledger.jsonl": 3}, (self.state_genesis,)),
                 ["file_missing:chain/root.jsonl"]),
                ("merge", lambda: self.state_commit({"ledger.jsonl": 3, "chain/root.jsonl": 2},
                                                    (self.state_genesis, self.state_head)),
                 ["state_merge"])):
            with self.subTest(name):
                shutil.rmtree(self.temp)
                os.makedirs(self.temp)
                if os.path.exists(os.path.join(self.bin, "calls.jsonl")):
                    os.remove(os.path.join(self.bin, "calls.jsonl"))
                self.state_head = head()
                out, _, _ = self.run_cek()
                self.assertEqual((out["ok"], out["reason"], out["reasons"]), (False, "state_refused", reasons))
                self.assertEqual(out["heads"]["brain/state"], self.state_head)
                self.assertIn("accepted", out)
                self.assertNotIn("checked", out)
                self.assertFalse(self.target_fetched())
                self.assertEqual(self.assembled(), [])

    def test_a_root_that_does_not_verify_is_a_refusal_before_the_target_is_fetched(self):
        def last_uuid():
            return self.rekor.last[self.state_head]

        def other_entry():
            self.rekor.entries[last_uuid()] = entry_for(RK.payload_digest("2" * 64))[1]

        def refuse_root(argv):
            return 1 if argv[-1].startswith("sha256:") else 0
        for name, head, setup, kw, reasons in (
                # the ledger has a row the last root does not anchor: one more commit than the last cycle wrote
                ("unanchored row", lambda: self.state_commit({"ledger.jsonl": 6, "chain/root.jsonl": 2},
                                                             (self.state_genesis,)), None, {}, ["root_mismatch"]),
                ("no entry", None, lambda: self.rekor.entries.pop(last_uuid()), {}, ["entry_missing"]),
                ("another root's entry", None, other_entry, {}, ["entry_root_mismatch"]),
                ("unverified", None, None, {"verifier": refuse_root}, ["entry_unverified"]),
                ("no root in the last row", lambda: self.state_commit(
                    {"ledger.jsonl": 2}, (), {"chain/root.jsonl": self.TA.chained([{"row_id": "r0", "part": "p"}])}),
                 None, {}, ["root_unreadable"])):
            with self.subTest(name):
                shutil.rmtree(self.temp)
                os.makedirs(self.temp)
                if os.path.exists(os.path.join(self.bin, "calls.jsonl")):
                    os.remove(os.path.join(self.bin, "calls.jsonl"))
                self.setUp_state()
                if head:
                    self.state_head = head()
                if setup:
                    setup()
                out, _, _ = self.run_cek(**kw)
                self.assertEqual((out["ok"], out["reason"], out["reasons"]), (False, "root_refused", reasons))
                self.assertEqual(out["heads"]["brain/state"], self.state_head)
                self.assertEqual(out["state"]["head"], self.state_head)  # the state verified, its root not
                self.assertNotIn("checked", out)
                self.assertFalse(self.target_fetched())
                self.assertEqual(self.assembled(), [])

    def test_rekor_unreadable_is_no_verdict(self):
        class Down:
            def entry(self, uuid):
                raise RK.RekorError("rekor unreadable: URLError")
        with self.assertRaisesRegex(J.Unusable, "rekor unreadable"):
            self.run_cek(rekor=Down())

    def test_a_state_commit_the_fetch_did_not_bring_is_no_verdict(self):
        everything = dict(self.state_objects)
        for missing in (self.state_head, self.state_genesis):  # the head, then its parent
            with self.subTest(missing=missing):
                shutil.rmtree(self.temp)
                os.makedirs(self.temp)
                self.state_objects = {k: v for k, v in everything.items() if k != missing}
                with self.assertRaisesRegex(J.Unusable, "state fetch: object_missing:%s" % missing):
                    self.run_cek()

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

    def refused_after_assembly(self, reason: str, **kw) -> dict:
        out, _, _ = self.run_cek(**kw)
        self.assertEqual((out["ok"], out["reason"]), (False, reason))
        self.assertEqual(out["assembled"]["commit"], self.target_commit)  # the refusal says what was judged
        self.assertNotIn("profile", out)
        self.assertNotIn("checked", out)
        return out

    def with_units(self, units: dict) -> None:
        self.BRAIN = dict(self.BRAIN, **{"targets/t1/units.json": json.dumps(units).encode()})

    def test_the_line_names_the_unit_judged(self):
        self.with_units({"units": [recipe(unit_id="the-unit")]})
        out, _, _ = self.run_cek()
        self.assertEqual((out["done"], out["profile"]), (["D1"], {"unit_id": "the-unit"}))

    def test_stage_0_judges_exactly_one_unit(self):
        for units in ({"units": []}, {"units": [recipe(), recipe(unit_id="b")]}, {"unit": [recipe()]}):
            with self.subTest(units=units):
                self.with_units(units)
                self.refused_after_assembly("units_not_one")

    def test_a_recipe_the_derivation_refuses(self):
        """MF4's part of the check: the recipe against the referee's derivation of the assembled tree."""
        for change, units, reason in (
                # no version file in the tree: pkg is no eligible unit candidate
                ({".nvmrc": None}, None, "profile:units[0]:unit_not_eligible:pkg"),
                # a path the derivation offers no candidate for (no package.json there)
                ({}, {"units": [recipe(path="pkg/sub")]}, "profile:units[0]:unit_not_candidate:pkg/sub"),
                # an input the derivation excludes (agent configuration), and one the tree lacks
                ({".claude/settings.json": b"{}"}, {"units": [recipe(inputs=["pkg", ".claude"])]},
                 "profile:units[0]:input_excluded:.claude"),
                ({}, {"units": [recipe(inputs=["pkg", "shared"])]}, "profile:units[0]:input_missing:shared")):
            with self.subTest(reason=reason):
                self.TARGET = {p: d for p, d in dict(CekJob.TARGET, **change).items() if d is not None}
                self.BRAIN = CekJob.BRAIN
                if units is not None:
                    self.with_units(units)
                out = self.refused_after_assembly("recipe_refused")
                self.assertIn(reason, out["reasons"])

    def test_the_operator_exclusion_is_the_targets_entry(self):
        self.summary["targets"][0]["excluded_paths"] = ["/pkg"]
        out = self.refused_after_assembly("recipe_refused")
        self.assertIn("profile:units[0]:unit_not_candidate:pkg", out["reasons"])  # the walk does not enter it
        self.assertIn("profile:units[0]:input_excluded:pkg", out["reasons"])

    def test_the_recipe_rules_are_getirs(self):
        self.with_units({"units": [recipe(services=["db"])]})
        out = self.refused_after_assembly("recipe_refused")
        self.assertEqual(out["reasons"], ["services_not_empty"])

    def test_a_tree_the_extraction_refuses(self):
        self.TARGET = dict(CekJob.TARGET, **{"pkg/out": ("120000", b"../../../../etc")})
        out = self.refused_after_assembly("pulled_invalid")
        self.assertEqual(out["reasons"], ["tree_unsafe"])

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
                shutil.rmtree(self.temp)
                os.makedirs(self.temp)
                self.run_cek()  # writes the checkout's files
                shutil.rmtree(os.path.join(self.temp, "out"))
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
