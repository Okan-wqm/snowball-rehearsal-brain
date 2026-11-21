"""Test 46 (asama-0/09), MF17, D1: ``loop.cek``, ``çek``'s assembly of the ``pulled`` artifact.

- the tree: the target's git objects (``git_store``) through ``loop.gitobj.tree_tar`` (its own rules are
  ``test_gitobj.py``'s); a commit the source lacks is listed with the brain's reasons;
- the brain, as git objects too (``git_store``): the ``targets[]`` entry, ``units.json`` and every candidate
  directory, read as committed (links, gitlinks, trees where a file belongs, legacy modes), each refusal listed
  together and nothing written, the brain's own object reasons marked ``brain:``; an id that is not one path
  component reads nothing;
- end to end: the target's and the brain's git objects -> ``assemble`` -> ``loop.job run kos`` -> ``gate.check
  decide``: the good candidate merges, the test-breaking one is rejected (``tests_red``);
- ``loop.cek.targets``, the one reader of the served list (tohum/29s "Hedefler"): every ``targets[]`` entry as
  read, in the array's order; ``summary_unreadable``, ``targets_empty``, ``target_id_unsafe`` (an entry that is not
  an object, an id that is not a target id), ``target_ambiguous``, ``target_kind_invalid``, listed together;
- the ``cek`` job's D1 accepted-SHA check (``loop.job.cek_d1``): a fake Actions API and verifier, the real
  ``loop.fetch`` and ``loop.gitobj.GitBatch`` with ``git_store``'s test ``git`` holding the brain's commit, the
  checkout's ``setup/imports.jsonl``, ``setup/summary.json`` and ``policy.json``; the running tree by tohum/29u: a
  transfer row naming the accepted commit (nothing more fetched), naming its parent whose ``referee/`` differs
  (served, on the row's hash, with the accepted commit's candidates), naming an unrelated commit
  (``transfer_not_ancestor``), carrying another hash than the transfer commit's or no commit id, and a history or
  transfer fetch that fails (no verdict); then the targets list
  (``loop.cek.targets``): a refused list is the job's reason, with ``accepted``, before any target is read (no
  listing, no fetch but the brain's, no Rekor read, nothing uploaded); then for each target, in the summary's
  order, in its own directory ``cek-*/<id>/``, the target half: the heads read by ``loop.fetch.heads`` (the fake
  ``git``'s ``ls-remote`` answer, one per repository with ``LISTING_GIT``), ``brain/state``'s head and its parent
  fetched into their own git directories and verified (``loop.state``'s rules are ``test_loop_state.py``'s; here a
  genesis head without parent, a rewritten ledger, a missing file and a merge head are ``state_refused`` before the
  target is fetched, a state commit the fetch did not bring is unusable), then MF11's verify of the head's root
  with a fake Rekor (``FakeRekor``; ``loop.rekor``'s own rules are ``test_rekor.py``'s) and the same fake verifier:
  the root row anchoring the head's ledger and its entry verified against ``loop.yml``'s identity; a ledger row no
  root anchors, no entry, another root's entry, an entry the verifier refuses and a last root row without a root
  are ``root_refused`` before the target is fetched, Rekor unreadable is unusable; a register on the head
  (tohum/26j) is verified, under the root D1 judges and carried in ``pulled``, and a root not over it is refused; then tohum/13:56-58 (E637,
  ``loop.integration``; its own rules are ``test_loop_integration.py``'s): the fixture ledger's cut row names the
  listed ``brain/integration`` head; a head other than the commit the last naming row (cut, merge, plant) names is
  ``integration_refused`` (``head_not_named``) with ``integration`` (the row and its commit) before the target is
  fetched, a ledger naming none is ``integration_unnamed``, a ledger of another shape is refused; after a revert
  row the head's ancestry is fetched without trees into ``integration-history.git`` and the gate's revert of the
  named merge passes, a head still at the merge, a commit after the revert and a head keeping the merge's content
  are refused, a commit the history lacks is a named reason, a failed history fetch is unusable; a genesis cycle
  has ``integration`` ``None``; ``brain/integration``'s head
  fetched and ``loop.cek.assemble`` run on both repositories' objects, then MF4's judgement of the read-back
  artifact: agreeing hashes and a recipe the check accepts end ``ok`` with ``done`` ``["D1"]``, ``accepted`` and
  ``targets``, one line per target with ``heads``, ``state``, ``root``, ``integration``, ``assembled`` and
  ``profile``; each
  artifact moved from the job's work directory to ``out/pulled/<id>`` (``loop.pulled.read`` takes it there, with
  its own ``targets[]`` entry) next to ``served.json`` listing the served ids in the summary's order (reversing
  the summary reverses it; ``loop.pulled.served`` reads it), and getir, kos, cagir and yaz, each on its own copy of
  it as the download hands it over, run their wired steps on it (cagir's canary with the fake ``claude``), and so
  do they on a toy's genesis ``pulled``, yaz's activation opening brain/state at the ``main`` cek read;
- the targets: a copy with neither head waits (``{target, waiting: copy_genesis, heads}``, not red, the job ``ok``;
  not in ``served.json``, no directory, nothing of it fetched; a run whose only target waits serves none) unless
  the toy served before it has the referee's ``copy_gate`` row after its last genesis in its verified ledger: then
  the copy is served as its genesis cycle at ``targets[].base_sha`` (loop.pulled's genesis form, its base fetched,
  no state read), and getir, kos, cagir and yaz run on it, yaz's activation opening the copy's brain/state at that
  base; no row, a proposal of it, a row before a later genesis or a copy before the toy leaves it waiting, and a
  ``base_sha`` that is no commit id is ``base_sha_invalid`` with nothing of the copy fetched; a copy
  with one head is ``head_missing:<branch>``; a toy with neither is its genesis cycle on its ``main`` (``pulled``
  in loop.pulled's genesis form, nothing of a state fetched or anchored), and without a ``main`` too
  ``head_missing:main``; the first refused target stops cek: the job's
  ``reason``/``reasons`` and ``target`` are its, ``targets`` the lines so far, the next target's repository is
  never listed or fetched, and nothing is handed over, also when an earlier target held; ``LOOP_TARGET`` in the
  environment, whatever it names, changes nothing (the same line, the same served list);
- any refusal leaves no ``out/pulled``, and an existing ``out/pulled`` (an artifact, an empty directory, a file) is
  unusable and left as it was; a different or refused ``referee/``, a broken import, a target without a safe
  ``repo``, a missing head, what ``assemble`` refuses, a ``units`` that is not exactly one recipe, a recipe the
  derivation of the assembled tree refuses (no eligible candidate, a path that is none, an input excluded by the
  agent-configuration rule or by the ``targets[]`` entry, an input the tree lacks), a recipe rule ``getir``
  refuses and a tree the extraction refuses are refusals (exit 1), the refused target's fields in its line; an
  unset variable, an unverified state, an unreadable checkout file, a failed listing or fetch are unusable (exit 2).
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tarfile
import unittest
from unittest import mock

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fake_claude  # noqa: E402
import test_loop_cagir
import yaz_world as YW  # noqa: E402
from loop_inputs_world import ABSENT, BOOTSTRAP, install_sigstore, own_path, write_bootstrap  # noqa: E402
from loop import cek as C  # noqa: E402
from harness import pass_row as PR  # noqa: E402
from loop import job as J  # noqa: E402
from loop import pulled as P  # noqa: E402
from loop import treehash as T  # noqa: E402
from snapshot import make as SM  # noqa: E402
import git_store as S  # noqa: E402
from ledger import anchor as AN  # noqa: E402
from loop import accepted as A  # noqa: E402
from loop import rekor as RK  # noqa: E402
from test_rekor import entry_for  # noqa: E402
from profile_tree import writable_base, write_tree  # noqa: E402
from test_kos import BREAKS_TEST, GOOD, operating, recipe  # noqa: E402
import test_loop_kos as LK  # noqa: E402
from test_loop_kos import HEADS, TREE, RedAs, candidate, state_files  # noqa: E402
from test_revert_drill import plant, reverted, row  # noqa: E402

# What ``cases.build.propose`` proposes for this world's target tree (test_kos's ``pkg``: one ``const`` line in
# each of two files), pinned; tests/test_cases.py reads the proposal itself.
MUTATION_IDS = ["no-var-5006bf2ab10fe7b6", "prefer-const-332fb56a7732f46b"]


def cut_row(base: str, row_id: str = "l1") -> dict:
    """``activate``'s ``integration_cut`` row naming ``base``: the row ``loop.integration`` reads the commit from."""
    return row(row_id, "events", "integration_cut", {"branch": "brain/integration", "base_sha": base})


def state_rows(n: int, cut: str | None = None) -> list[dict]:
    """The first ``n`` rows of the fixture ``brain/state`` ledgers: ``cycle_start`` rows of ``ledger.schema``, no
    merge; with ``cut``, row 1 (a row of the genesis commit too) is the ``integration_cut`` row naming it."""
    rows = [row("l%d" % i, "events", "cycle_start", {"cycle_id": str(i)}) for i in range(n)]
    if cut is not None:
        rows[1] = cut_row(cut)
    return rows


SUMMARY = {"targets": [{"id": "t1", "kind": "toy", "excluded_paths": [], "unit_candidates": []},
                       {"id": "t2", "kind": "copy", "excluded_paths": ["x"], "unit_candidates": []}]}
POLICY = test_loop_cagir.policy()  # tohum/26b's shape, the canary's cap 1 USD


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
        for kw, want in (({"state": {".brain/ledger.jsonl": b"x\n"}}, ["state_incomplete"]),
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

    def test_the_snapshot_is_made_with_the_policy_s_planted_max_cases(self):
        def with_params(**params) -> bytes:
            policy = json.loads(POLICY)
            policy["constitutional"]["stage_params"].update(params)
            return json.dumps(policy).encode()

        seen = []
        real = C.SM.make

        def spy(*args):
            seen.append(args[5])
            return real(*args)

        with mock.patch.object(C.SM, "make", spy):
            self.assemble(policy=with_params(planted_max_cases=4))
            shutil.rmtree(self.out)
            self.assemble()
            shutil.rmtree(self.out)
        self.assertEqual(seen, [4, json.loads(POLICY)["constitutional"]["stage_params"]["planted_max_cases"]])
        self.assertNotEqual(seen[0], seen[1])
        for bad in (0, "5", True, 2.5, None):
            with self.subTest(bad=bad):
                self.assertEqual(self.refused(policy=with_params(planted_max_cases=bad)),
                                 ["policy_invalid:constitutional.stage_params.planted_max_cases"])

    def test_a_policy_the_loop_cannot_use_is_no_pull(self):
        """tohum/29v: a required path absent, or a judged value off its form, refuses the pull with the path named
        (``harness.params.check``, whose own cross of paths and values is ``tests/test_policy_reads.py``'s)."""
        def changed(change) -> bytes:
            policy = json.loads(POLICY)
            change(policy)
            return json.dumps(policy).encode()

        def hoist(policy):
            policy["planted_max_cases"] = policy["constitutional"]["stage_params"].pop("planted_max_cases")

        made = []
        with mock.patch.object(C.SM, "make", lambda *args: made.append(args)):
            for name, change, reasons in (
                    ("absent", lambda p: p["constitutional"].pop("monthly_cap_usd"),
                     ["policy_invalid:constitutional.monthly_cap_usd"]),
                    ("hoisted", hoist, ["policy_invalid:constitutional.stage_params.planted_max_cases"]),
                    ("float", lambda p: p["constitutional"].update(confidence_level=0.9),
                     ["policy_invalid:constitutional.confidence_level"]),
                    ("optional off form", lambda p: p["performance"].setdefault("rules", {}).update(drift_bound=0.5),
                     ["policy_invalid:performance.rules.drift_bound"]),
                    ("two", lambda p: (p["constitutional"]["regression_freeze"].update(revert_rate=0.02),
                                       p["constitutional"]["stage_params"].pop("match_window_lines")),
                     ["policy_invalid:constitutional.stage_params.match_window_lines",
                      "policy_invalid:constitutional.regression_freeze.revert_rate"])):
                with self.subTest(name=name):
                    self.assertEqual(self.refused(policy=changed(change)), reasons)
        self.assertEqual(made, [])

    def test_out_must_not_exist(self):
        os.makedirs(self.out)
        with self.assertRaises(FileExistsError):
            self.assemble()


class Targets(unittest.TestCase):
    """``loop.cek.targets``: the served list, every entry as read in the array's order, or every reason."""

    def targets(self, doc) -> tuple[list, list]:
        return C.targets(doc if isinstance(doc, bytes) else json.dumps(doc).encode())

    def test_every_entry_in_order_as_read(self):
        entries = [{"id": "b", "kind": "copy", "repo": "o/b", "x": [1]}, {"id": "a", "kind": "toy"},
                   {"id": "t1-2.x_y", "kind": "toy"}]
        self.assertEqual(self.targets({"targets": entries, "other": 1}), (entries, []))
        self.assertEqual(self.targets({"targets": entries[::-1]}), (entries[::-1], []))

    def test_each_refusal(self):
        toy = {"id": "t1", "kind": "toy"}
        for doc, reasons in (
                (b"{", ["summary_unreadable"]), (b"\xff", ["summary_unreadable"]),
                ({"targets": {}}, ["summary_unreadable"]), ([{"targets": [toy]}], ["summary_unreadable"]),
                ({"x": [toy]}, ["summary_unreadable"]),
                ({"targets": []}, ["targets_empty"]),
                ({"targets": [toy, dict(toy, id="../x")]}, ["target_id_unsafe"]),
                ({"targets": [{"kind": "toy"}]}, ["target_id_unsafe"]),
                ({"targets": [dict(toy, id=7)]}, ["target_id_unsafe"]),
                ({"targets": [dict(toy, id="t1\n")]}, ["target_id_unsafe"]),
                ({"targets": [dict(toy, id="x" * 129)]}, ["target_id_unsafe"]),
                ({"targets": [dict(toy, id=".hidden")]}, ["target_id_unsafe"]),
                ({"targets": [toy, dict(toy, kind="copy")]}, ["target_ambiguous"]),
                ({"targets": [toy, {"id": "t2"}]}, ["target_kind_invalid"]),
                ({"targets": [dict(toy, kind="fork")]}, ["target_kind_invalid"]),
                ({"targets": [dict(toy, kind=None)]}, ["target_kind_invalid"]),
                # an entry that is not an object has no id and no kind; reasons are listed together
                ({"targets": [toy, "t2"]}, ["target_id_unsafe", "target_kind_invalid"]),
                ({"targets": [toy, dict(toy, kind="x"), dict(toy, id="a/b")]},
                 ["target_id_unsafe", "target_ambiguous", "target_kind_invalid"])):
            with self.subTest(reasons=reasons, doc=doc):
                self.assertEqual(self.targets(doc), ([], reasons))


class EndToEnd(LK.Base):
    """The target's and the brain's git objects -> cek's assembly -> the kos job -> MF8's decision."""

    run_kos, results, decide, one = LK.KosJob.run_kos, LK.KosJob.results, LK.KosJob.decide, LK.KosJob.one

    def test_cek_to_kos_to_the_gate(self):
        brain, brain_commit = S.store(brain_files())
        objects, commit = target_objects(self.src)
        # the download as cek hands it over: served.json naming t1, and t1's directory (loop.pulled "Served")
        os.makedirs(os.path.dirname(self.pulled))
        P.write_served(os.path.dirname(self.pulled), ["t1"])
        C.assemble(brain.__getitem__, brain_commit, json.dumps(SUMMARY).encode(), POLICY, "t1", objects.__getitem__,
                   commit, HEADS["brain/state"], state_files(), None, self.pulled)
        out = self.run_kos()
        line = self.one(out)
        self.assertEqual((out["ok"], line["done"]), (True, ["D3"]))
        self.assertEqual(line["index"]["base"], {"verdict": "verified", "reasons": []})
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


# ``git_store``'s test ``git`` answers every ``ls-remote`` with one listing; with more than one target each
# repository has its own. This front answers ``ls-remote`` by the URL asked for (recorded in the same
# ``calls.jsonl``) and hands every other command to ``git_store``'s ``git`` beside it.
LISTING_GIT = '''#!%s
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
if "ls-remote" in args:
    with open(os.path.join(here, "calls.jsonl"), "a") as fh:
        fh.write(json.dumps({"argv": args}) + "\\n")
    with open(os.path.join(here, "listings.json")) as fh:
        listings = json.load(fh)
    sys.stdout.buffer.write(bytes.fromhex(listings[args[args.index("--") + 1]]))
    sys.exit(0)
os.execv(os.path.join(here, "git"), [os.path.join(here, "git")] + args)
'''


def install_listing_git(directory: str, listings: dict[str, bytes]) -> str:
    """``LISTING_GIT`` in ``directory`` (which holds ``git_store``'s ``git``), ``listings`` URL -> answer."""
    with open(os.path.join(directory, "listings.json"), "w") as fh:
        json.dump({url: answer.hex() for url, answer in listings.items()}, fh)
    path = os.path.join(directory, "git-listing")
    with open(path, "w") as fh:
        fh.write(LISTING_GIT % sys.executable)
    os.chmod(path, 0o755)
    return path


class CekJob(unittest.TestCase):
    """``loop.job run cek`` up to the assembled ``pulled``: D1's accepted-SHA check, the target's heads, its fetch."""

    BRAIN = dict({"referee/loop/job.py": b"x = 1\n", "referee/a.py": b"a\n",
                  "targets/t1/units.json": json.dumps({"units": [recipe()]}).encode()},
                 **{"candidates/t1/good/%s" % f: d for f, d in candidate(GOOD).items()})
    TARGET = {p: (json.dumps(v) if isinstance(v, dict) else v).encode() for p, v in TREE.items()}
    STATE = {".brain/ledger.jsonl": [2, 5], ".brain/chain/root.jsonl": [1, 2]}  # rows at genesis, at the head on top of it
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
        YW.AW.write_checkout(self.work)  # the operator files yaz hashes (tohum/01c); the policy among them is POLICY
        self.setUp_state()

    def setUp_state(self) -> None:
        self.state_objects: dict = {}
        self.state_content: dict = {}  # commit -> its chained files as written
        self.rekor = FakeRekor()
        self.state_genesis = self.state_commit({p: n[0] for p, n in self.STATE.items()}, ())
        self.state_head = self.state_commit({p: n[1] for p, n in self.STATE.items()}, (self.state_genesis,),
                                            {".brain/status.md": self.STATUS_MD})

    ledger_rows: list | None = None  # the fixture ledger's rows, ``rows()`` unless a test gives its own

    def rows(self) -> list[dict]:
        """The fixture ledger: its cut row names the commit ``run_cek`` lists as ``brain/integration``'s head."""
        return state_rows(max(self.ANCHORED), S.store(self.TARGET)[1])

    def retarget(self, files: dict) -> None:
        """Another target tree, and the ``brain/state`` whose ledger names its commit."""
        self.TARGET = files
        self.setUp_state()

    def state_commit(self, counts: dict, parents: tuple, extra: dict | None = None,
                     registers: dict | None = None) -> str:
        """A ``brain/state`` commit whose chained files hold ``counts`` rows (``loop.state``'s rules); root row ``i``
        anchors the ledger's first ``ANCHORED[i]`` rows, its entry in the fake Rekor (``ledger.anchor``'s rules)."""
        ledger = self.ledger_rows or self.rows()
        content = {}
        if ".brain/ledger.jsonl" in counts:
            content[".brain/ledger.jsonl"] = self.TA.chained(ledger[:counts[".brain/ledger.jsonl"]])
        if ".brain/chain/root.jsonl" in counts:
            roots = b""
            for i in range(counts[".brain/chain/root.jsonl"]):
                last = i == counts[".brain/chain/root.jsonl"] - 1  # ``registers``: files the last root is over
                root = AN.root_of(AN.tips(self.TA.chained(ledger[:self.ANCHORED[i]]),
                                          AN.named(registers) if last else None))
                uuid, entry = entry_for(root)
                self.rekor.entries[uuid] = entry
                roots = AN.root_row(roots, "r%d" % i, "2026-11-01T00:00:00Z", root, uuid)
            content[".brain/chain/root.jsonl"] = roots
        commit = S.store(dict(content, **(extra or {}), **(registers or {})), parents, self.state_objects)[1]
        self.state_content[commit] = content
        if ".brain/chain/root.jsonl" in counts:
            self.rekor.last[commit] = uuid
        return commit

    def listing(self, integration: str | None, state: str | None = "head") -> bytes:
        state = self.state_head if state == "head" else state
        rows = [(state, "refs/heads/brain/state"), (integration, "refs/heads/brain/integration")]
        return b"".join(b"%s\t%s\n" % (sha.encode(), ref.encode()) for sha, ref in rows if sha)

    def run_cek(self, brain=None, imported=None, verifier=None, exits=None, env=None, http=None, listing=None,
                target=None, summary=None, rekor=None, bootstrap=None, sigstore=True, listings=None,
                transfer=None, related=True, row_sha=None, wrap=None):
        """``transfer``: the files of an earlier transfer commit (the row names it and, unless ``imported``, its
        ``referee/`` hash; the accepted commit is its child, or with ``related`` false a commit without parent);
        ``row_sha``: the row's ``brain_sha`` as given; ``wrap``: makes the ``git`` the job runs from the fake's path;
        ``bootstrap``: the checkout's ``bootstrap.json`` (a dict, raw bytes, or ``ABSENT``); ``sigstore``: whether
        the sigstore step's program is in place (``loop.inputs.sigstore``); ``listings``: each repository's own
        ``ls-remote`` answer (URL -> bytes, ``install_listing_git``), else ``listing`` for every repository."""
        objects, self.transfer_commit = ({}, None) if transfer is None else S.store(transfer)
        objects, commit = S.store(self.BRAIN if brain is None else brain, objects=objects,
                                  parents=(self.transfer_commit,) if transfer is not None and related else ())
        tobjects, self.target_commit = S.store(self.TARGET)
        self.snapshot_id = SM.make(tobjects.__getitem__, self.target_commit, [], "clean").document["snapshot_id"]
        if target is not None:
            tobjects = target
        answers = {sha: S.batch_record(sha, kind, data)
                   for sha, (kind, data) in dict(objects, **tobjects, **self.state_objects).items()}
        git = S.install_git(self.bin, answers, exits=exits,
                            listing=self.listing(self.target_commit) if listing is None else listing)
        if listings is not None:
            git = install_listing_git(self.bin, listings)
        tree = imported if imported is not None else T.digest(
            [(p, "file", d) for p, d in (self.BRAIN if transfer is None else transfer).items()])
        named = row_sha if row_sha is not None else self.transfer_commit or commit
        with open(os.path.join(self.work, "setup", "imports.jsonl"), "wb") as fh:
            fh.write(self.TA.chained([self.TA.import_row(tree, named)])
                     if imported != "" else b"")
        if wrap is not None:
            git = wrap(git)
        with open(os.path.join(self.work, "setup", "summary.json"), "wb") as fh:
            doc = self.summary if summary is None else summary
            if isinstance(doc, dict) and isinstance(doc.get("targets"), list) and \
                    all(isinstance(t, dict) for t in doc["targets"]):  # a summary of the form: setup's baseline with it
                doc = YW.with_baseline(doc)
            fh.write(json.dumps(doc).encode())
        write_bootstrap(self.work, bootstrap)
        if sigstore:
            install_sigstore(self.temp)
        zip_bytes = self.TA.zip_of({"result.json": self.TA.result(commit), "result.json.sigstore.json": b"{}"})
        api = http or self.TA.FakeApi([self.TA.artifact(11, "2026-11-01T00:00:00Z")], zip_bytes)
        environ = {"RUNNER_TEMP": self.temp, "GITHUB_REPOSITORY": "o/referee", "GITHUB_TOKEN": "t",
                   "GITHUB_WORKSPACE": self.work, "PATH": own_path(self.base)}
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

    def test_the_entry_request_reaches_pulled_with_the_signed_results_run_id(self):
        """tohum/26j MF9: the accepted commit's ``accept.json`` is carried with that commit and the id of the
        bootstrap run that signed the result D1 verified (``loop.accepted.open_state``'s ``run_id``); a commit
        without a request carries an entry of no organ."""
        organ = {"organs/lint.discover.json": json.dumps({"entry": ["python", "/in/adapter.py"],
                                                           "files": ["adapter.py"]}).encode(),
                 "adapter.py": b"print('lint')\n"}
        for request, ids in ((None, []), (b'{"organ_ids": ["lint.discover"]}', ["lint.discover"])):
            with self.subTest(request=request):
                brain = dict(self.BRAIN, **organ, **({} if request is None else {C.ENTRY_REQUEST: request}))
                out, commit, _ = self.run_cek(brain=brain)
                self.assertEqual(out["ok"], True, out)
                got = P.read(os.path.join(self.temp, "out", "pulled", "t1"))
                self.assertEqual(got.accept, {"brain_sha": commit, "run_id": self.TA.RUN_ID, "organ_ids": ids})
                shutil.rmtree(os.path.join(self.temp, "out"))
                shutil.rmtree(os.path.join(self.temp, "work"))
        out, _, _ = self.run_cek(brain=dict(self.BRAIN, **{C.ENTRY_REQUEST: b'{"organ_ids": ["lint.discover"]}'}))
        self.assertEqual(self.stopped(out)["reasons"], ["accept_unknown:lint.discover"])

    def assembled(self) -> list[str]:
        """Each ``pulled`` left in the job's work directory (``cek-*/<id>/pulled``): one not handed over."""
        work = os.path.join(self.temp, "work")
        return [os.path.join(work, d, t, "pulled") for d in sorted(os.listdir(work))
                for t in sorted(os.listdir(os.path.join(work, d))) if os.path.isdir(os.path.join(work, d, t, "pulled"))
                ] if os.path.isdir(work) else []

    def one(self, out: dict) -> dict:
        """The line's one target, ``t1``: its entry of ``targets`` (where the per-target fields are)."""
        self.assertEqual([t["target"] for t in out["targets"]], ["t1"])
        return out["targets"][0]

    def stopped(self, out: dict, tid: str = "t1") -> dict:
        """A refusal of target ``tid``, the last one cek read: the job's reason is its, with its id; its line."""
        self.assertEqual((out["ok"], out["target"], out["targets"][-1]["target"]), (False, tid, tid))
        line = out["targets"][-1]
        self.assertEqual((out["reason"], out.get("reasons")), (line["reason"], line.get("reasons")))
        self.assertIn("accepted", out)
        return line

    def served(self) -> list[str]:
        """``served.json`` of ``out/pulled``, after ``loop.pulled.served`` checked the root holds exactly those."""
        root = os.path.join(self.temp, "out", "pulled")
        with open(os.path.join(root, P.SERVED)) as fh:
            self.assertEqual(json.load(fh)["targets"], P.served(root))
        return P.served(root)

    def target_dir(self, tid: str = "t1") -> str:
        """``cek-*/<tid>``, the target's own directory in the job's work directory."""
        [cek] = os.listdir(os.path.join(self.temp, "work"))
        return os.path.join(self.temp, "work", cek, tid)

    def ls_remotes(self) -> list[str]:
        """The repositories whose heads were listed, in order."""
        return [a[a.index("--") + 1] for a in (c["argv"] for c in S.calls(self.bin)) if "ls-remote" in a]

    def fetched(self) -> list[tuple[str, str]]:
        """``(url, refspec)`` of every fetch, in order."""
        return [(a[-2], a[-1]) for a in (c["argv"] for c in S.calls(self.bin)) if "fetch" in a]

    def clean(self) -> None:
        """A new runner: no ``$RUNNER_TEMP`` content, no record of the fake ``git``'s calls."""
        shutil.rmtree(self.temp)
        os.makedirs(self.temp)
        if os.path.exists(os.path.join(self.bin, "calls.jsonl")):
            os.remove(os.path.join(self.bin, "calls.jsonl"))

    def test_the_job_runs_d1_and_hands_pulled_to_the_upload(self):
        out, commit, tree = self.run_cek()
        self.assertNotIn("reason", out)
        self.assertEqual((out["ok"], out["done"], out["checked"]),
                         (True, ["D1"], ["accepted_sha", "referee_tree", "heads", "state_previous", "root", "integration",
                                  "assembled", "profile"]))
        line = self.one(out)
        self.assertEqual(sorted(line), ["assembled", "heads", "integration", "profile", "root", "state", "target"])
        # tohum/13:56-58: the commit the ledger's last naming row names, the listed brain/integration head
        self.assertEqual(line["integration"], {"row_id": "l1", "kind": "cut", "sha": self.target_commit})
        self.assertEqual(line["heads"]["brain/integration"], self.target_commit)
        self.assertEqual(line["state"], {"head": self.state_head, "previous": self.state_genesis,
                                         "rows": {".brain/ledger.jsonl": 5, ".brain/chain/root.jsonl": 2}})
        self.assertEqual(line["profile"], {"unit_id": "pkg"})
        self.assertEqual(out["accepted"]["brain_sha"], commit)
        self.assertEqual(out["accepted"]["referee_tree_sha256"], tree)
        self.assertEqual(out["accepted"]["artifact_id"], 11)
        self.assertIn("https://github.com/o/referee/.github/workflows/bootstrap.yml@refs/heads/main", self.verified[0])
        # MF11: the head's root (its ledger's, the last root row's) and its Rekor entry, verified against loop.yml
        root = AN.root_of(AN.tips(self.TA.chained(self.rows()[:5])))
        uuid = entry_for(root)[0]
        self.assertEqual((line["root"], self.rekor.calls), ({"root": root, "rekor_uuid": uuid}, [uuid]))
        self.assertEqual(len(self.verified), 2)
        # both checks run the sigstore step's program (tohum/29s), an argv prefix
        program = (os.path.join(self.temp, "sig", "bin", "python"), "-m", "sigstore")
        self.assertEqual(self.verified[0][:3], list(program))
        self.assertEqual(self.verified[1], A.identity_argv(
            program, self.verified[1][6], "https://github.com/o/referee/.github/workflows/loop.yml@refs/heads/main",
            "sha256:" + root))
        argvs = [c["argv"] for c in S.calls(self.bin)]
        fetches = [a for a in argvs if "fetch" in a]
        self.assertEqual([(f[-2], f[-1]) for f in fetches],
                         [("https://github.com/o/brain", "%s:refs/pulled" % commit),
                          ("https://github.com/o/target", "%s:refs/pulled" % self.state_head),
                          ("https://github.com/o/target", "%s:refs/pulled" % self.state_genesis),
                          ("https://github.com/o/target", "%s:refs/pulled" % self.target_commit)])
        # each into its own new git directory of the job's work directory, read there
        dirs = [a.split("=", 1)[1] for f in fetches for a in f if a.startswith("--git-dir=")]
        self.assertEqual([os.path.relpath(d, os.path.dirname(self.target_dir())) for d in dirs],
                         ["brain.git", "t1/state.git", "t1/state-previous.git", "t1/target.git"])
        batches = [a for a in argvs if "cat-file" in a]
        for d in dirs[1:3]:
            self.assertIn(["--git-dir=%s" % d, "cat-file", "--batch"], [b[-3:] for b in batches])
        listings = [a for a in argvs if "ls-remote" in a]
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0][-4:], ["--", "https://github.com/o/target", "refs/heads/brain/state",
                                            "refs/heads/brain/integration"])
        self.assertEqual(line["heads"], {"brain/state": self.state_head, "brain/integration": self.target_commit})
        self.assertEqual(line["assembled"], {"target": "t1", "commit": self.target_commit, "candidates": ["good"],
                                             "organs": [], "snapshot_id": self.snapshot_id,
                                             "mutations": MUTATION_IDS})
        # the artifact assembled in the job's work directory is moved, not copied, to out/pulled/t1, next to
        # served.json naming it, and loop.pulled reads it there: the target's tree at brain/integration's head, the
        # brain's units.json and candidate at the accepted commit
        self.assertEqual(self.assembled(), [])
        self.assertEqual(sorted(os.listdir(os.path.join(self.temp, "out", "pulled"))), ["served.json", "t1"])
        self.assertEqual(self.served(), ["t1"])
        path = os.path.join(self.temp, "out", "pulled", "t1")
        art = P.read(path)
        with open(art.tree_tar, "rb") as fh:
            members = names(fh.read())
        self.assertEqual(sorted(n for n, t, _, _ in members if t == tarfile.REGTYPE), sorted(TREE))
        self.assertEqual(art.units, {"units": [recipe()]})
        # MF4 judged the tree extracted next to the artifact, the one the derivation read
        self.assertEqual(sorted(os.listdir(os.path.join(self.target_dir(), "tree", "pkg"))),
                         sorted(p.split("/", 1)[1] for p in TREE if p.startswith("pkg/")))
        self.assertEqual(sorted(art.candidates), ["good"])
        self.assertEqual(art.target["repo"], "o/target")
        # state/: the heads D1 read and brain/state's files at its head, the bytes verify --previous and the root
        # check judged
        self.assertEqual(art.target["id"], "t1")
        self.assertEqual(art.heads, line["heads"])
        self.assertEqual(art.state, self.state_content[self.state_head])
        self.assertEqual(art.status, self.STATUS_MD)  # the head's status.md, for D6

    def test_getir_kos_cagir_and_yaz_run_on_the_pulled_cek_hands_over(self):
        """The workflow's hand-over, each job on its own runner: cek's ``out/pulled`` downloaded whole as each
        consumer's ``in/pulled`` (then getir's ``deps`` to kos and kos's ``results`` to yaz the same way); every
        consumer's wired steps run on those bytes and judge the brain's candidates cek assembled; cagir's canary
        spends against the ledger D1 verified (its cost rows) and records the head cek read."""
        self.BRAIN = dict(self.BRAIN, **{"candidates/t1/breaks/%s" % f: d for f, d in candidate(BREAKS_TEST).items()})
        out, _, _ = self.run_cek()
        self.assertEqual((out["done"], self.one(out)["assembled"]["candidates"]), (["D1"], ["breaks", "good"]))
        heads = self.one(out)["heads"]
        temps = {}
        for job in ("getir", "kos", "cagir", "yaz"):
            temps[job] = os.path.join(self.base, job)
            shutil.copytree(os.path.join(self.temp, "out", "pulled"), os.path.join(temps[job], "in", "pulled"),
                            symlinks=True)
        got = J.run("getir", {"RUNNER_TEMP": temps["getir"]})
        self.assertEqual((got["ok"], self.one(got)["done"], self.one(got)["deps"]["packages"]), (True, ["D2"], 0))
        shutil.copytree(os.path.join(temps["getir"], "out", "deps"), os.path.join(temps["kos"], "in", "deps"))
        got = J.run("kos", {"RUNNER_TEMP": temps["kos"]}, runner=RedAs())
        self.assertEqual((got["ok"], self.one(got)["done"], self.one(got)["index"]["base"]),
                         (True, ["D3"], {"verdict": "verified", "reasons": []}))
        claude_dir = os.path.dirname(fake_claude.install_for_loop(temps["cagir"]))
        fake_claude.behave(claude_dir, test_loop_cagir.result(modelUsage={BOOTSTRAP["rival"]["model"]: {"costUSD": 0.01}}))
        got = J.run("cagir", {"RUNNER_TEMP": temps["cagir"], "CLAUDE_CODE_OAUTH_TOKEN": "t",
                              "GITHUB_WORKSPACE": self.work, "GITHUB_RUN_ID": "1", "GITHUB_RUN_ATTEMPT": "1"})
        self.assertEqual((got["ok"], self.one(got)["done"], self.one(got)["call"]["outcome"]), (True, ["D4"], "ok"))
        with open(os.path.join(temps["cagir"], "out", "response", "t1", "response.json")) as fh:
            response = json.load(fh)
        self.assertEqual(response["heads"], heads)
        [call] = fake_claude.calls(claude_dir)
        argv = call["argv"]
        self.assertEqual(argv[argv.index("--max-budget-usd") + 1], "1.000000")  # the head's ledger has no cost row
        shutil.copytree(os.path.join(temps["kos"], "out", "results"), os.path.join(temps["yaz"], "in", "results"))
        shutil.copytree(os.path.join(temps["cagir"], "out", "response"), os.path.join(temps["yaz"], "in", "response"))
        write_tree(os.path.join(temps["yaz"], "control"), {"control.json": {"merge_paused": False}})
        # the target at the heads cek read, brain/state holding the files D1 verified
        gh = YW.github_at(heads, self.TARGET, dict(self.state_content[self.state_head],
                                                         **{".brain/status.md": self.STATUS_MD}), repo="o/target")
        got = J.run("yaz", YW.env(temps["yaz"], self.work, GITHUB_RUN_ID="1"), transport=gh, signer=YW.signer(),
                    now=lambda: YW.NOW)
        self.assertEqual((got["ok"], self.one(got)["done"]), (True, ["D5", "D6"]))
        got = self.one(got)
        # the brain's candidates are ready candidates and this is no genesis cycle: each names no organ and none
        # merges (P1 MF9, tohum/26j); the genesis cycle's merge through every job is the next test's
        self.assertEqual((got["merge"], {cid: d["reasons"] for cid, d in got["decisions"].items()}),
                         (None, {"good": ["no_organ"], "breaks": ["no_organ", "tests_red"]}))
        self.assertEqual((got["written"]["merge"], gh.refs["brain/integration"]), (None, heads["brain/integration"]))
        # D6 appended cagir's cost row, as the response carried it, onto the ledger cek verified
        ledger = gh.read_file("brain/state", ".brain/ledger.jsonl")
        self.assertTrue(ledger.startswith(self.state_content[self.state_head][".brain/ledger.jsonl"]))
        [cost] = [json.loads(line) for line in ledger.splitlines() if json.loads(line)["part"] == "cost"]
        self.assertEqual({k: v for k, v in cost.items() if k not in ("prev_hash", "row_hash")}, response["rows"][0])

    def test_the_genesis_cycle_through_every_job(self):
        """A toy with neither head: cek's genesis ``pulled`` handed over as above; getir, kos and cagir run on it as
        on any cycle (the canary spends against an empty ledger), and yaz's activation opens brain/state with the
        genesis row, the cut at the ``main`` cek read and D5's merge, the canary's cost row among its rows."""
        import activation_world as AW
        self.BRAIN = dict(self.BRAIN, **{"candidates/t1/breaks/%s" % f: d for f, d in candidate(BREAKS_TEST).items()})
        _, main = S.store(self.TARGET)
        summary = {"seed_epochs": [AW.seed_epoch()],
                   "targets": [dict(self.summary["targets"][0], base_sha=AW.summary_base("toy", main),
                                    identifiers=[])]}
        out, _, _ = self.run_cek(summary=summary, listing=b"%s\trefs/heads/main\n" % main.encode())
        self.assertEqual((out["ok"], self.one(out)["genesis"]), (True, True))
        temps = {}
        for job in ("getir", "kos", "cagir", "yaz"):
            temps[job] = os.path.join(self.base, job)
            shutil.copytree(os.path.join(self.temp, "out", "pulled"), os.path.join(temps[job], "in", "pulled"),
                            symlinks=True)
        self.assertTrue(J.run("getir", {"RUNNER_TEMP": temps["getir"]})["ok"])
        shutil.copytree(os.path.join(temps["getir"], "out", "deps"), os.path.join(temps["kos"], "in", "deps"))
        got = J.run("kos", {"RUNNER_TEMP": temps["kos"]}, runner=RedAs())
        self.assertEqual((got["ok"], self.one(got)["done"]), (True, ["D3"]))
        claude_dir = os.path.dirname(fake_claude.install_for_loop(temps["cagir"]))
        fake_claude.behave(claude_dir, test_loop_cagir.result(modelUsage={BOOTSTRAP["rival"]["model"]: {"costUSD": 0.01}}))
        got = J.run("cagir", {"RUNNER_TEMP": temps["cagir"], "CLAUDE_CODE_OAUTH_TOKEN": "t",
                              "GITHUB_WORKSPACE": self.work, "GITHUB_RUN_ID": "1", "GITHUB_RUN_ATTEMPT": "1"})
        self.assertEqual((got["ok"], self.one(got)["call"]["outcome"]), (True, "ok"))
        with open(os.path.join(temps["cagir"], "out", "response", "t1", "response.json")) as fh:
            response = json.load(fh)
        self.assertEqual(response["heads"], {"brain/state": None, "brain/integration": main})
        shutil.copytree(os.path.join(temps["kos"], "out", "results"), os.path.join(temps["yaz"], "in", "results"))
        shutil.copytree(os.path.join(temps["cagir"], "out", "response"), os.path.join(temps["yaz"], "in", "response"))
        write_tree(os.path.join(temps["yaz"], "control"), {"control.json": {"merge_paused": False}})
        write_tree(self.work, {J.SECURITY_LEDGER: YW.chained([{"row_id": "s1", "part": "security", "kind": "note",
                                                               "payload": {}}]).decode()})
        # the toy: main at the commit cek read (no brain/ branch), the facts genesis reads
        gh = YW.FakeGitHub("o/target", required_check=YW.B.CHECK)
        tree = YW.sha_of(["tree", "main"])
        gh.trees[tree] = {path: gh._blob(data) for path, data in self.TARGET.items()}
        gh.commits[main] = {"tree": tree, "parents": [], "message": "main"}
        gh.refs["main"] = main
        gh.overrides.update(AW.facts("toy", "o/target"))
        got = J.run("yaz", YW.env(temps["yaz"], self.work, GITHUB_RUN_ID="1"), transport=gh, signer=YW.signer(),
                    now=lambda: YW.NOW)
        self.assertEqual((got["ok"], self.one(got)["done"]), (True, ["D5", "D6"]), got)
        got = self.one(got)
        self.assertEqual((got["merge"], got["written"]["genesis"], got["written"]["integration_sha"]),
                         ("good", True, main))
        ledger = gh.read_file("brain/state", ".brain/ledger.jsonl")
        rows = [json.loads(line) for line in ledger.splitlines()]
        self.assertEqual((rows[0]["kind"], rows[0]["payload"]["base_sha"]), ("genesis", main))
        [cost] = [r for r in rows if r["part"] == "cost"]
        self.assertEqual({k: v for k, v in cost.items() if k not in ("prev_hash", "row_hash")}, response["rows"][0])
        self.assertEqual(gh.commits[gh.refs["brain/integration"]]["parents"][0], main)

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

    # ---- tohum/29u "Döngü ne okur": main ahead of the transfer. The input that showed the old rule wrong is
    # loop run 44094922317 (2026-11-17): the bootstrap referee accepted a push that changed referee/ after the
    # transfer, and cek stopped with referee_tree_mismatch.

    OLD = {"referee/loop/job.py": b"x = 0\n", "referee/a.py": b"before\n", "candidates/t1/gone/x": b"x"}

    def brain_fetches(self) -> list[tuple[str, str]]:
        """``(how, refspec)`` of each fetch from the brain's repository, in order."""
        return [("history" if "--filter=tree:0" in a else "commit" if "--depth=1" in a else "?", a[-1])
                for a in (c["argv"] for c in S.calls(self.bin)) if "fetch" in a and a[-2] == "https://github.com/o/brain"]

    def test_a_main_ahead_of_the_transfer_runs_on_the_transferred_tree(self):
        out, commit, old_tree = self.run_cek(transfer=self.OLD)
        self.assertEqual((out["ok"], out["done"]), (True, ["D1"]), out)
        new_tree = T.digest([(p, "file", d) for p, d in self.BRAIN.items()])
        self.assertNotEqual(old_tree, new_tree)  # the accepted commit's referee/ is another tree
        self.assertEqual(out["accepted"], {"brain_sha": commit, "transfer_sha": self.transfer_commit,
                                           "referee_tree_sha256": old_tree, "artifact_id": 11,
                                           "result_sha256": out["accepted"]["result_sha256"]})
        # candidates/ and targets/ are the accepted commit's, not the transfer's
        self.assertEqual(self.one(out)["assembled"]["candidates"], ["good"])
        self.assertEqual(self.brain_fetches(), [("commit", "%s:refs/pulled" % commit),
                                                ("history", "%s:refs/pulled" % commit),
                                                ("commit", "%s:refs/pulled" % self.transfer_commit)])
        dirs = [a.split("=", 1)[1] for c in S.calls(self.bin) if "fetch" in c["argv"] for a in c["argv"]
                if a.startswith("--git-dir=")][:3]
        self.assertEqual([os.path.basename(d) for d in dirs], ["brain.git", "history.git", "transfer.git"])
        self.assertEqual(len({os.path.dirname(d) for d in dirs}), 1)

    def test_a_transfer_that_is_the_accepted_commit_fetches_nothing_more(self):
        out, commit, tree = self.run_cek()
        self.assertEqual((out["accepted"]["transfer_sha"], out["accepted"]["referee_tree_sha256"]), (commit, tree))
        self.assertEqual(self.brain_fetches(), [("commit", "%s:refs/pulled" % commit)])

    def test_a_transfer_that_is_no_ancestor_of_the_accepted_commit(self):
        out, commit, _ = self.run_cek(transfer=self.OLD, related=False)
        self.assertEqual((out["ok"], out["reason"]), (False, "transfer_not_ancestor"))
        self.assertNotIn("accepted", out)
        # the transfer commit is not fetched, no target is listed
        self.assertEqual(self.brain_fetches(), [("commit", "%s:refs/pulled" % commit),
                                                ("history", "%s:refs/pulled" % commit)])
        self.assertFalse([a for c in S.calls(self.bin) for a in c["argv"] if a == "ls-remote"])

    def test_the_rows_hash_must_be_the_transfer_commits(self):
        # the accepted commit's own referee/ hash in the row is not the transferred tree's
        new_tree = T.digest([(p, "file", d) for p, d in self.BRAIN.items()])
        out, _, _ = self.run_cek(transfer=self.OLD, imported=new_tree)
        self.assertEqual((out["ok"], out["reason"]), (False, "referee_tree_mismatch"))
        self.clean()
        out, _, _ = self.run_cek(transfer=dict(self.OLD, **{"referee/Setup": b""}), imported=new_tree)
        self.assertEqual((out["reason"], out["reasons"]), ("referee_tree_refused", ["operator_name:Setup"]))

    def test_a_row_without_a_commit_id(self):
        for bad in ("", "x" * 40, "A" * 40, "a" * 39):
            with self.subTest(bad=bad):
                out, commit, _ = self.run_cek(row_sha=bad)
                self.assertEqual((out["ok"], out["reason"]), (False, "imports_invalid"))
                self.assertEqual(self.brain_fetches(), [("commit", "%s:refs/pulled" % commit)])
                self.clean()

    def test_a_history_or_transfer_fetch_that_fails_is_no_verdict(self):
        def failing(marker):
            def wrap(git):
                path = os.path.join(self.bin, "git-failing")
                with open(path, "w") as fh:
                    fh.write('#!/bin/sh\ncase " $* " in *" fetch "*%s*) exit 128;; esac\nexec "%s" "$@"\n'
                             % (marker, git))
                os.chmod(path, 0o755)
                return path
            return wrap
        with self.assertRaisesRegex(J.Unusable, "cek: brain history fetch: fetch_failed:fetch:128"):
            self.run_cek(transfer=self.OLD, wrap=failing("--filter=tree:0"))
        self.assertFalse(os.path.lexists(os.path.join(self.temp, "out", "pulled")))
        self.clean()
        _, transfer = S.store(self.OLD)
        with self.assertRaisesRegex(J.Unusable, "cek: transfer fetch: fetch_failed:fetch:128"):
            self.run_cek(transfer=self.OLD, wrap=failing(transfer + ":"))
        self.assertFalse(os.path.lexists(os.path.join(self.temp, "out", "pulled")))

    def test_a_refused_tree_and_a_broken_import(self):
        out, _, _ = self.run_cek(brain=dict(self.BRAIN, **{"referee/Setup": b""}))
        self.assertEqual((out["reason"], out["reasons"]), ("referee_tree_refused", ["operator_name:Setup"]))
        out, _, _ = self.run_cek(imported="")
        self.assertEqual(out["reason"], "imports_no_transfer")

    def test_a_missing_head_is_a_refusal_and_nothing_is_fetched(self):
        for listing, reasons in ((self.listing(None), ["head_missing:brain/integration"]),
                                 (self.listing("6" * 40, None), ["head_missing:brain/state"]),
                                 (b"", ["head_missing:brain/state", "head_missing:brain/integration",
                                        "head_missing:main"])):
            with self.subTest(reasons=reasons):
                os.remove(os.path.join(self.bin, "calls.jsonl")) if os.path.exists(
                    os.path.join(self.bin, "calls.jsonl")) else None
                out, _, _ = self.run_cek(listing=listing)
                self.stopped(out)
                self.assertEqual([out["reason"]] + out.get("reasons", []), reasons)
                self.assertEqual(len([c for c in S.calls(self.bin) if "fetch" in c["argv"]]), 1)  # the brain's only
                self.assertEqual(self.assembled(), [])

    def target_fetched(self) -> bool:
        return any("%s:refs/pulled" % self.target_commit in c["argv"] for c in S.calls(self.bin))

    def test_a_genesis_head_is_verified_as_chains_only(self):
        self.state_head = self.state_genesis
        out, _, _ = self.run_cek()
        self.assertEqual((out["done"], self.one(out)["state"]), (["D1"], {
            "head": self.state_genesis, "previous": None, "rows": {".brain/ledger.jsonl": 2, ".brain/chain/root.jsonl": 1}}))
        self.assertEqual([a[-1] for a in (c["argv"] for c in S.calls(self.bin)) if "fetch" in a][1:2],
                         ["%s:refs/pulled" % self.state_genesis])
        self.assertIn("state.git", os.listdir(self.target_dir()))
        self.assertNotIn("state-previous.git", os.listdir(self.target_dir()))

    def test_a_toy_with_neither_head_is_its_genesis_cycle_on_main(self):
        """loop.pulled's genesis form: the tree of the toy's ``main``, no ``brain/state`` to verify or anchor."""
        _, main = S.store(self.TARGET)
        out, _, _ = self.run_cek(listing=b"%s\trefs/heads/main\n" % main.encode())
        self.assertEqual((out["ok"], out["done"]), (True, ["D1"]), out)
        line = self.one(out)
        self.assertEqual((line["genesis"], line["state"], line["root"], line["integration"], line["heads"]),
                         (True, None, None, None, {"brain/state": None, "brain/integration": None}))
        self.assertEqual(line["assembled"]["commit"], main)
        art = P.read(os.path.join(self.temp, "out", "pulled", "t1"))
        self.assertTrue(P.genesis(art))
        self.assertEqual((art.heads, art.state, art.status),
                         ({"brain/state": None, "brain/integration": main},
                          {".brain/ledger.jsonl": b"", ".brain/chain/root.jsonl": b""}, None))
        self.assertEqual(self.ls_remotes(), [self.URL["t1"]] * 2)  # the two heads, then main
        self.assertEqual(self.fetched()[1:], [(self.URL["t1"], "%s:refs/pulled" % main)])  # no brain/state fetch
        self.assertEqual(self.rekor.calls, [])
        # a toy with one head is no genesis cycle
        self.clean()
        out, _, _ = self.run_cek(listing=self.listing(None) + b"%s\trefs/heads/main\n" % main.encode())
        self.assertEqual(self.stopped(out)["reason"], "head_missing:brain/integration")

    def test_a_state_that_does_not_verify_is_a_refusal_before_the_target_is_fetched(self):
        for name, head, reasons in (
                # the head rewrote its parent's ledger: fewer rows than the parent had
                ("rewritten", lambda: self.state_commit({".brain/ledger.jsonl": 1, ".brain/chain/root.jsonl": 2},
                                                        (self.state_genesis,)),
                 ["not_append_only:.brain/ledger.jsonl:2"]),
                ("no roots", lambda: self.state_commit({".brain/ledger.jsonl": 3}, (self.state_genesis,)),
                 ["file_missing:.brain/chain/root.jsonl"]),
                ("merge", lambda: self.state_commit({".brain/ledger.jsonl": 3, ".brain/chain/root.jsonl": 2},
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
                line = self.stopped(out)
                self.assertEqual(line["heads"]["brain/state"], self.state_head)
                self.assertNotIn("checked", out)
                self.assertFalse(self.target_fetched())
                self.assertEqual(self.assembled(), [])

    def test_a_root_that_does_not_verify_is_a_refusal_before_the_target_is_fetched(self):
        def last_uuid():
            return self.rekor.last[self.state_head]

        def other_entry():
            self.rekor.entries[last_uuid()] = entry_for("2" * 64)[1]

        def refuse_root(argv):
            return 1 if argv[-1].startswith("sha256:") else 0
        for name, head, setup, kw, reasons in (
                # the ledger has a row the last root does not anchor: one more commit than the last cycle wrote
                ("unanchored row", lambda: self.state_commit({".brain/ledger.jsonl": 6, ".brain/chain/root.jsonl": 2},
                                                             (self.state_genesis,)), None, {}, ["root_mismatch"]),
                ("no entry", None, lambda: self.rekor.entries.pop(last_uuid()), {}, ["entry_missing"]),
                ("another root's entry", None, other_entry, {}, ["entry_root_mismatch"]),
                ("unverified", None, None, {"verifier": refuse_root}, ["entry_unverified"]),
                ("no root in the last row", lambda: self.state_commit(
                    {".brain/ledger.jsonl": 2}, (), {".brain/chain/root.jsonl": self.TA.chained([{"row_id": "r0", "part": "p"}])}),
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
                line = self.stopped(out)
                self.assertEqual(line["heads"]["brain/state"], self.state_head)
                self.assertEqual(line["state"]["head"], self.state_head)  # the state verified, its root not
                self.assertNotIn("checked", out)
                self.assertFalse(self.target_fetched())
                self.assertEqual(self.assembled(), [])

    def test_the_heads_registers_are_under_its_root_and_carried(self):
        """tohum/26j: a register on ``brain/state``'s head is verified with it, its tip is in the root D1 judges,
        and ``pulled`` carries the file to D6."""
        counts = {p: n[1] for p, n in self.STATE.items()}
        findings = self.TA.chained([{"row_id": "f1", "part": "findings"}, {"row_id": "f2", "part": "findings"}])
        files = {".brain/findings.jsonl": findings}
        self.state_head = self.state_commit(counts, (self.state_genesis,), {".brain/status.md": self.STATUS_MD}, files)
        out, _, _ = self.run_cek()
        self.assertEqual((out["ok"], self.one(out)["state"]["rows"]), (True, dict(counts, **{".brain/findings.jsonl": 2})), out)
        art = P.read(os.path.join(self.temp, "out", "pulled", "t1"))
        self.assertEqual(art.state[".brain/findings.jsonl"], findings)
        self.assertNotIn(".brain/unresolved.jsonl", art.state)
        # the file on the head and a root that is not over it (the ledger's alone)
        self.clean()
        self.setUp_state()
        self.state_head = self.state_commit(counts, (self.state_genesis,), dict(files, **{".brain/status.md": self.STATUS_MD}))
        out, _, _ = self.run_cek()
        self.assertEqual((out["ok"], out["reason"], out["reasons"]), (False, "root_refused", ["root_mismatch"]))
        self.assertFalse(self.target_fetched())

    def test_rekor_unreadable_is_no_verdict(self):
        class Down:
            def entry(self, uuid):
                raise RK.RekorError("rekor unreadable: URLError")
        with self.assertRaisesRegex(J.Unusable, "rekor unreadable"):
            self.run_cek(rekor=Down())

    # ---- tohum/13:56-58 (E637): brain/integration's head against the commit the anchored ledger names

    def renamed(self, *rows: dict) -> None:
        """The fixture ``brain/state`` with ``rows`` as the head's rows 2.. (the genesis commit holds rows 0-1)."""
        ledger = self.rows()
        ledger[2:2 + len(rows)] = rows
        self.ledger_rows = ledger
        self.setUp_state()

    def integration_refused(self, reasons: list[str], named: dict | None, **kw) -> dict:
        self.clean()
        out, _, _ = self.run_cek(**kw)
        self.assertEqual((out["ok"], out["reason"], out["reasons"]), (False, "integration_refused", reasons))
        line = self.stopped(out)
        # the break's row and commit (the row and the commit it names) and the head found, with what was verified
        self.assertEqual(line.get("integration"), named)
        self.assertEqual((line["state"]["head"], sorted(line["root"])), (self.state_head, ["rekor_uuid", "root"]))
        self.assertNotIn("checked", out)
        self.assertNotIn("assembled", line)
        self.assertEqual(self.assembled(), [])
        return line

    def test_a_head_the_ledger_does_not_name_is_a_chain_break(self):
        import test_serial as TS
        _, listed = S.store(self.TARGET)
        other = "6" * 40
        for name, rows, named in (
                ("the cut names another commit", [cut_row(other, "l2")], {"row_id": "l2", "kind": "cut", "sha": other}),
                # a merge the state branch did not record: the head is ahead of the last signed row
                ("a later merge names another", [TS.merge("l2", other)], {"row_id": "l2", "kind": "merge", "sha": other}),
                ("a later plant does", [plant("l2", "i1", other)], {"row_id": "l2", "kind": "merge", "sha": other}),
                # the head went back to the commit an earlier row named
                ("an earlier row named the head", [cut_row(listed, "l2"), TS.merge("l3", other)],
                 {"row_id": "l3", "kind": "merge", "sha": other})):
            with self.subTest(name):
                self.renamed(*rows)
                line = self.integration_refused(["head_not_named"], named)
                self.assertEqual(line["heads"]["brain/integration"], listed)
                # refused before anything of the target's tree is fetched: the brain, the state head and its parent
                self.assertEqual(len(self.fetched()), 3)
                self.assertFalse(self.target_fetched())

    def test_the_last_naming_row_names_the_head(self):
        import test_serial as TS
        _, listed = S.store(self.TARGET)
        for name, rows, named in (
                ("a merge after the cut", [TS.merge("l2", listed)], {"row_id": "l2", "kind": "merge", "sha": listed}),
                ("a plant after a merge", [TS.merge("l2", "6" * 40), plant("l3", "i1", listed)],
                 {"row_id": "l3", "kind": "merge", "sha": listed})):
            with self.subTest(name):
                self.ledger_rows = state_rows(max(self.ANCHORED), "7" * 40)
                rows = list(rows)
                self.ledger_rows[2:2 + len(rows)] = rows
                self.setUp_state()
                self.clean()
                out, _, _ = self.run_cek()
                self.assertEqual((out["ok"], self.one(out)["integration"]), (True, named))
                self.assertEqual(len(self.fetched()), 4)  # no fetch for the comparison

    def test_a_ledger_that_names_no_integration_commit(self):
        self.ledger_rows = state_rows(max(self.ANCHORED))
        self.setUp_state()
        self.integration_refused(["integration_unnamed"], None)
        self.assertFalse(self.target_fetched())

    def test_a_ledger_of_another_shape_is_refused_with_ledger_serials_reasons(self):
        self.renamed(row("l2", "events", "nope", {}))
        self.clean()
        out, _, _ = self.run_cek()
        self.assertEqual((out["ok"], out["reason"]), (False, "integration_refused"))
        self.assertTrue(out["reasons"])
        self.assertNotIn("integration", self.stopped(out))
        self.assertFalse(self.target_fetched())

    def reverted_target(self, head_tree: dict | None = None) -> tuple[dict, str, str]:
        """The target's objects after the gate's revert: a base holding ``TARGET``, a candidate, their merge ``M``,
        the revert commit on ``M`` and its merge, the head (holding ``head_tree``, by default ``TARGET`` again);
        ``(objects, M, head)``."""
        objects: dict = {}
        before = S.store_tree(self.TARGET, objects)
        after = S.store_tree(dict(self.TARGET, **{"pkg/new.js": b"1\n"}), objects)
        base = S.commit(objects, before, b"base\n")
        merged = S.commit(objects, after, b"merge\n", (base, S.commit(objects, after, b"candidate\n", (base,))))
        revert = S.commit(objects, before, b"revert\n", (merged,))
        tree = before if head_tree is None else S.store_tree(head_tree, objects)
        return objects, merged, S.commit(objects, tree, b"merge of the revert\n", (merged, revert))

    def test_a_revert_row_names_the_head_by_the_reverts_shape(self):
        import test_serial as TS
        objects, merged, head = self.reverted_target()
        self.renamed(TS.merge("l2", merged), reverted("l3", merged, "test_regression"))
        self.clean()
        out, _, _ = self.run_cek(target=objects, listing=self.listing(head))
        self.assertTrue(out["ok"], out)
        line = self.one(out)
        self.assertEqual(line["integration"], {"row_id": "l3", "kind": "revert", "sha": merged})
        self.assertEqual((line["heads"]["brain/integration"], line["assembled"]["commit"]), (head, head))
        # the head's ancestry without trees, into its own directory, before the head's tree
        argvs = [c["argv"] for c in S.calls(self.bin) if "fetch" in c["argv"]]
        self.assertEqual([("--filter=tree:0" in a, a[-1]) for a in argvs[3:]],
                         [(True, "%s:refs/pulled" % head), (False, "%s:refs/pulled" % head)])
        self.assertEqual(argvs[3][-2], argvs[4][-2])  # the target's repository
        dirs = [next(x.split("=", 1)[1] for x in a if x.startswith("--git-dir=")) for a in argvs[3:]]
        self.assertEqual(dirs[0], os.path.join(self.target_dir(), "integration-history.git"))
        self.assertNotEqual(dirs[0], dirs[1])

    def test_a_head_that_is_not_the_revert_of_the_named_merge(self):
        import test_serial as TS
        objects, merged, head = self.reverted_target()
        named = {"row_id": "l3", "kind": "revert", "sha": merged}
        self.renamed(TS.merge("l2", merged), reverted("l3", merged, "test_regression"))
        kept, _, with_content = self.reverted_target(dict(self.TARGET, **{"pkg/new.js": b"1\n"}))
        objects.update(kept)
        later = S.commit(objects, S.store_tree(self.TARGET, objects), b"later\n", (head,))
        for name, listed, reasons in (("still the merge", merged, ["revert_head_parents"]),
                                      ("a commit after the revert", later, ["revert_head_parents"]),
                                      ("the merge's content kept", with_content, ["revert_head_tree"])):
            with self.subTest(name):
                line = self.integration_refused(reasons, named, target=objects, listing=self.listing(listed))
                self.assertEqual(line["heads"]["brain/integration"], listed)
                self.assertEqual([a[-1] for a in (c["argv"] for c in S.calls(self.bin))
                                  if "fetch" in a and "--depth=1" in a and a[-1] == "%s:refs/pulled" % listed], [])
        # a commit the history fetch did not bring is a reason of the same refusal, named
        lacking = {k: v for k, v in objects.items() if k != merged}
        self.integration_refused(["integration:object_missing:%s" % merged], named, target=lacking,
                                 listing=self.listing(head))

    def test_an_integration_history_fetch_that_fails_is_no_verdict(self):
        import test_serial as TS
        objects, merged, head = self.reverted_target()
        self.renamed(TS.merge("l2", merged), reverted("l3", merged, "test_regression"))

        def wrap(git):
            path = os.path.join(self.bin, "git-failing")
            with open(path, "w") as fh:
                fh.write('#!/bin/sh\ncase " $* " in *" fetch "*--filter=tree:0*) exit 128;; esac\nexec "%s" "$@"\n' % git)
            os.chmod(path, 0o755)
            return path
        with self.assertRaisesRegex(J.Unusable, "cek: integration history fetch: fetch_failed:fetch:128"):
            self.run_cek(target=objects, listing=self.listing(head), wrap=wrap)
        self.assertFalse(os.path.lexists(os.path.join(self.temp, "out", "pulled")))

    def test_a_state_commit_the_fetch_did_not_bring_is_no_verdict(self):
        everything = dict(self.state_objects)
        for missing in (self.state_head, self.state_genesis):  # the head, then its parent
            with self.subTest(missing=missing):
                shutil.rmtree(self.temp)
                os.makedirs(self.temp)
                self.state_objects = {k: v for k, v in everything.items() if k != missing}
                with self.assertRaisesRegex(J.Unusable, "state fetch: object_missing:%s" % missing):
                    self.run_cek()

    def test_a_target_without_a_safe_repo(self):
        # the list holds (ids, kinds); the one target's repo is no repository: refused, its heads never listed
        for repo in (None, "o/../x", "https://github.com/o/t", 7):
            with self.subTest(repo=repo):
                self.clean()
                entry = dict({"id": "t1", "kind": "toy"}, **({} if repo is None else {"repo": repo}))
                out, _, _ = self.run_cek(summary={"targets": [entry]})
                self.assertEqual((out["reason"], out["targets"]), ("target_repo_unsafe", [
                    {"target": "t1", "reason": "target_repo_unsafe"}]))
                self.stopped(out)
                self.assertEqual(self.ls_remotes(), [])

    def test_a_refused_targets_list_stops_cek_before_any_target_is_read(self):
        entry = self.summary["targets"][0]
        for summary, reasons in (
                ({"targets": []}, ["targets_empty"]), ({"x": 1}, ["summary_unreadable"]),
                ({"targets": [entry, dict(entry, kind="copy")]}, ["target_ambiguous"]),
                ({"targets": [entry, dict(entry, id="../t2")]}, ["target_id_unsafe"]),
                ({"targets": [entry, dict(entry, id="t2", kind="fork")]}, ["target_kind_invalid"]),
                ({"targets": [entry, "t2"]}, ["target_id_unsafe", "target_kind_invalid"])):
            with self.subTest(reasons=reasons, summary=summary):
                self.clean()
                out, commit, _ = self.run_cek(summary=summary)
                self.assertEqual((out["ok"], [out["reason"]] + out.get("reasons", [])), (False, reasons))
                self.assertEqual(out["accepted"]["brain_sha"], commit)
                self.assertNotIn("targets", out)
                self.assertNotIn("target", out)
                # not even the valid first entry is read: no listing, no fetch but the brain's, no Rekor read, no
                # target directory; nothing uploaded (run_cek: no out/pulled)
                self.assertEqual(self.ls_remotes(), [])
                self.assertEqual(self.fetched(), [("https://github.com/o/brain", "%s:refs/pulled" % commit)])
                self.assertEqual(self.rekor.calls, [])
                self.assertNotIn("t1", os.listdir(os.path.dirname(self.target_dir())))

    # -------------------------------------------------------------------------------- tohum/29s: every target

    COPY = {"id": "t2", "kind": "copy", "repo": "o/copy", "excluded_paths": [], "unit_candidates": []}
    URL = {"t1": "https://github.com/o/target", "t2": "https://github.com/o/copy"}

    def two(self, order=("t1", "t2")) -> dict:
        """The summary with the toy ``t1`` and the copy ``t2`` in ``order``; the brain gets ``t2``'s unit and its
        own candidate (``breaks``; ``t1``'s is ``good``)."""
        self.BRAIN = dict(self.BRAIN, **{"targets/t2/units.json": self.BRAIN["targets/t1/units.json"]},
                          **{"candidates/t2/breaks/%s" % f: d for f, d in candidate(BREAKS_TEST).items()})
        entries = {"t1": self.summary["targets"][0], "t2": self.COPY}
        return {"targets": [entries[t] for t in order]}

    def listings(self, **over) -> dict:
        """Each target's repository listing both heads (the same objects), unless ``over`` gives its answer."""
        both = self.listing(S.store(self.TARGET)[1])
        return {self.URL[t]: over.get(t, both) for t in ("t1", "t2")}

    def test_every_target_is_served_in_the_summarys_order(self):
        cands = {"t1": ["good"], "t2": ["breaks"]}
        for order in (("t1", "t2"), ("t2", "t1")):
            with self.subTest(order=order):
                self.clean()
                summary = self.two(order)
                out, _, _ = self.run_cek(summary=summary, listings=self.listings())
                self.assertEqual((out["ok"], out["done"]), (True, ["D1"]))
                self.assertEqual([t["target"] for t in out["targets"]], list(order))
                for line in out["targets"]:
                    self.assertEqual(sorted(line), ["assembled", "heads", "integration", "profile", "root", "state",
                                                    "target"])
                    self.assertEqual(line["assembled"], {"target": line["target"], "commit": self.target_commit,
                                                         "candidates": cands[line["target"]], "organs": [],
                                                         "snapshot_id": self.snapshot_id,
                                                         "mutations": MUTATION_IDS})
                # served.json lists them in that order, each in its own directory, read by loop.pulled as its own
                self.assertEqual(self.served(), list(order))
                self.assertEqual(sorted(os.listdir(os.path.join(self.temp, "out", "pulled"))),
                                 ["served.json", "t1", "t2"])
                for entry in summary["targets"]:
                    art = P.read(os.path.join(self.temp, "out", "pulled", entry["id"]))
                    self.assertEqual((art.target, sorted(art.candidates)), (entry, cands[entry["id"]]))
                self.assertEqual(self.assembled(), [])
                # each target's repository read in that order: its heads, its state head and parent, its tree
                self.assertEqual(self.ls_remotes(), [self.URL[t] for t in order])
                self.assertEqual(self.fetched()[1:], [
                    (self.URL[t], "%s:refs/pulled" % c) for t in order
                    for c in (self.state_head, self.state_genesis, self.target_commit)])

    def test_a_copy_without_heads_waits(self):
        heads = {"brain/state": None, "brain/integration": None}
        for order in (("t1", "t2"), ("t2", "t1")):
            with self.subTest(order=order):
                self.clean()
                out, _, _ = self.run_cek(summary=self.two(order), listings=self.listings(t2=b""))
                # not red: the job holds (exit 0), the copy's line says it waits for its genesis
                self.assertEqual((out["ok"], out["done"]), (True, ["D1"]))
                self.assertNotIn("reason", out)
                lines = {t["target"]: t for t in out["targets"]}
                self.assertEqual([t["target"] for t in out["targets"]], list(order))
                self.assertEqual(lines["t2"], {"target": "t2", "waiting": "copy_genesis", "heads": heads})
                self.assertEqual(lines["t1"]["assembled"]["target"], "t1")
                # not served: not in served.json, no directory; nothing of it fetched, its heads listed once
                self.assertEqual(self.served(), ["t1"])
                self.assertEqual(sorted(os.listdir(os.path.join(self.temp, "out", "pulled"))), ["served.json", "t1"])
                self.assertEqual(sorted(self.ls_remotes()), sorted(self.URL.values()))
                self.assertEqual([u for u, _ in self.fetched() if u == self.URL["t2"]], [])
                self.assertEqual(os.listdir(self.target_dir("t2")), [])
        with self.subTest("the copy alone"):
            self.clean()
            out, _, _ = self.run_cek(summary={"targets": [self.COPY]}, listing=b"")
            self.assertEqual((out["ok"], out["targets"]),
                             (True, [{"target": "t2", "waiting": "copy_genesis", "heads": heads}]))
            self.assertEqual(self.served(), [])
            self.assertEqual(os.listdir(os.path.join(self.temp, "out", "pulled")), ["served.json"])
            self.assertEqual(len(self.fetched()), 1)  # the brain's only

    def gated(self, gate: dict | None = None) -> None:
        """The toy's ``brain/state`` (genesis and head) with a genesis first and, in the head, ``gate`` as row 3."""
        import test_pass_row as TP
        rows = self.rows()
        rows[0] = row("l0", "events", "genesis", TP.genesis_payload("t1"))
        if gate is not None:
            rows[3] = gate
        self.ledger_rows = rows
        self.setUp_state()

    def copy_at(self, base: str, order=("t1", "t2")) -> dict:
        summary = self.two(order)
        return {"targets": [dict(t, base_sha=base) if t["id"] == "t2" else t for t in summary["targets"]]}

    def test_an_open_gate_serves_the_copys_genesis_at_its_base(self):
        """tohum/25a row 7: the toy's verified ledger holds the referee's ``copy_gate`` row after its genesis, so the
        copy with neither head is served as its genesis cycle, its tree read at ``targets[].base_sha``."""
        self.gated(row("l3", "events", "copy_gate", PR.gate_payload()))
        _, base = S.store(self.TARGET)
        out, _, _ = self.run_cek(summary=self.copy_at(base), listings=self.listings(t2=b""))
        self.assertEqual((out["ok"], out["done"]), (True, ["D1"]), out)
        lines = {t["target"]: t for t in out["targets"]}
        self.assertNotIn("genesis", lines["t1"])
        line = lines["t2"]
        self.assertEqual((line["genesis"], line["state"], line["root"], line["heads"], line["assembled"]["commit"]),
                         (True, None, None, {"brain/state": None, "brain/integration": None}, base))
        self.assertEqual(self.served(), ["t1", "t2"])
        art = P.read(os.path.join(self.temp, "out", "pulled", "t2"))
        self.assertTrue(P.genesis(art))
        self.assertEqual((art.target["kind"], art.heads, art.state, art.status),
                         ("copy", {"brain/state": None, "brain/integration": base},
                          {".brain/ledger.jsonl": b"", ".brain/chain/root.jsonl": b""}, None))
        # the copy: its heads listed once, its base fetched, nothing of a state fetched; no main read
        self.assertEqual(self.ls_remotes(), [self.URL["t1"], self.URL["t2"]])
        self.assertEqual([f for f in self.fetched() if f[0] == self.URL["t2"]],
                         [(self.URL["t2"], "%s:refs/pulled" % base)])

    def test_the_copys_genesis_cycle_through_every_job(self):
        """The copy's genesis ``pulled`` cek handed over (served alone here: the toy's ordinary cycle is the other
        tests'): getir, kos and cagir run on it, and yaz's activation opens the copy's brain/state with the genesis
        row at ``targets[].base_sha`` and cuts brain/integration there."""
        import activation_world as AW
        self.gated(row("l3", "events", "copy_gate", PR.gate_payload()))
        _, base = S.store(self.TARGET)
        summary = dict(self.copy_at(base), seed_epochs=[AW.seed_epoch()])
        summary["targets"] = [dict(t, identifiers=[]) for t in summary["targets"]]
        out, _, _ = self.run_cek(summary=summary, listings=self.listings(t2=b""))
        self.assertEqual(out["ok"], True, out)
        pulled = os.path.join(self.temp, "out", "pulled")
        shutil.rmtree(os.path.join(pulled, "t1"))
        os.unlink(os.path.join(pulled, P.SERVED))
        P.write_served(pulled, ["t2"])
        temps = {}
        for job in ("getir", "kos", "cagir", "yaz"):
            temps[job] = os.path.join(self.base, job)
            shutil.copytree(pulled, os.path.join(temps[job], "in", "pulled"), symlinks=True)
        self.assertTrue(J.run("getir", {"RUNNER_TEMP": temps["getir"]})["ok"])
        shutil.copytree(os.path.join(temps["getir"], "out", "deps"), os.path.join(temps["kos"], "in", "deps"))
        got = J.run("kos", {"RUNNER_TEMP": temps["kos"]}, runner=RedAs())
        self.assertEqual((got["ok"], got["targets"][0]["done"]), (True, ["D3"]), got)
        claude_dir = os.path.dirname(fake_claude.install_for_loop(temps["cagir"]))
        fake_claude.behave(claude_dir, test_loop_cagir.result(modelUsage={BOOTSTRAP["rival"]["model"]: {"costUSD": 0.01}}))
        got = J.run("cagir", {"RUNNER_TEMP": temps["cagir"], "CLAUDE_CODE_OAUTH_TOKEN": "t",
                              "GITHUB_WORKSPACE": self.work, "GITHUB_RUN_ID": "1", "GITHUB_RUN_ATTEMPT": "1"})
        self.assertEqual(got["ok"], True, got)
        shutil.copytree(os.path.join(temps["kos"], "out", "results"), os.path.join(temps["yaz"], "in", "results"))
        shutil.copytree(os.path.join(temps["cagir"], "out", "response"), os.path.join(temps["yaz"], "in", "response"))
        write_tree(os.path.join(temps["yaz"], "control"), {"control.json": {"merge_paused": False}})
        write_tree(self.work, {J.SECURITY_LEDGER: YW.chained([{"row_id": "s1", "part": "security", "kind": "note",
                                                               "payload": {}}]).decode()})
        # the copy: its base commit on GitHub, no brain/ branch, Actions off (the facts genesis reads)
        gh = YW.FakeGitHub("o/copy", required_check=YW.B.CHECK)
        tree = YW.sha_of(["tree", "base"])
        gh.trees[tree] = {path: gh._blob(data) for path, data in self.TARGET.items()}
        gh.commits[base] = {"tree": tree, "parents": [], "message": "base"}
        gh.refs["main"] = base
        gh.overrides.update(AW.facts("copy", "o/copy"))
        gh.overrides[("GET", "/installation/repositories")] = (200, {  # the App on both targets of the summary
            "total_count": 2, "repositories": [{"full_name": "o/target"}, {"full_name": "o/copy"}]})
        gh.overrides[("GET", "/repos/o/target")] = (200, {  # drift reads every named repository's visibility (01c)
            "full_name": "o/target", "visibility": "public", "private": False})
        got = J.run("yaz", YW.env(temps["yaz"], self.work, GITHUB_RUN_ID="1"), transport=gh, signer=YW.signer(),
                    now=lambda: YW.NOW)
        line = got["targets"][0]
        self.assertEqual((got["ok"], line["target"], line["done"]), (True, "t2", ["D5", "D6"]), got)
        self.assertNotIn("gate", line)  # judged on the toy only
        self.assertEqual((line["written"]["genesis"], line["written"]["integration_sha"]), (True, base))
        rows = [json.loads(x) for x in gh.read_file("brain/state", ".brain/ledger.jsonl").splitlines()]
        self.assertEqual((rows[0]["kind"], rows[0]["payload"]["target"], rows[0]["payload"]["base_sha"]),
                         ("genesis", "t2", base))

    def test_the_copy_waits_unless_the_gate_is_the_referees_own_after_the_toys_genesis_and_before_it(self):
        heads = {"brain/state": None, "brain/integration": None}
        _, base = S.store(self.TARGET)
        gate = row("l3", "events", "copy_gate", PR.gate_payload())
        import test_pass_row as TP
        for name, ledger_gate, order in (
                ("no gate row", None, ("t1", "t2")),
                ("a proposal of it", dict(gate, proposed_by="founder"), ("t1", "t2")),
                ("before a later genesis", "regenesis", ("t1", "t2")),
                ("the copy before the toy", gate, ("t2", "t1"))):
            with self.subTest(name):
                self.clean()
                if ledger_gate == "regenesis":
                    self.gated(gate)
                    self.ledger_rows[4] = row("l4", "events", "genesis", TP.genesis_payload("t1"))
                    self.setUp_state()
                else:
                    self.gated(ledger_gate)
                out, _, _ = self.run_cek(summary=self.copy_at(base, order), listings=self.listings(t2=b""))
                self.assertEqual(out["ok"], True, out)
                lines = {t["target"]: t for t in out["targets"]}
                self.assertEqual(lines["t2"], {"target": "t2", "waiting": "copy_genesis", "heads": heads})
                self.assertEqual(self.served(), ["t1"])
                self.assertEqual([f for f in self.fetched() if f[0] == self.URL["t2"]], [])

    def test_an_open_gate_and_a_copy_base_that_is_no_commit_id(self):
        self.gated(row("l3", "events", "copy_gate", PR.gate_payload()))
        for base in (None, "B" * 40, "b" * 39):
            with self.subTest(base=base):
                self.clean()
                summary = self.copy_at("0" * 40)
                summary["targets"][1] = {k: v for k, v in summary["targets"][1].items() if k != "base_sha"}
                if base is not None:
                    summary["targets"][1]["base_sha"] = base
                out, _, _ = self.run_cek(summary=summary, listings=self.listings(t2=b""))
                line = self.stopped(out, "t2")
                self.assertEqual((out["reason"], line["heads"]),
                                 ("base_sha_invalid", {"brain/state": None, "brain/integration": None}))
                self.assertEqual([f for f in self.fetched() if f[0] == self.URL["t2"]], [])

    def test_a_copy_with_one_head_and_a_toy_with_none_are_red(self):
        for name, entry, listing, missing in (
                ("copy, no integration", self.COPY, self.listing(None), ["head_missing:brain/integration"]),
                ("copy, no state", self.COPY, self.listing("6" * 40, None), ["head_missing:brain/state"]),
                ("toy, neither, no main", self.summary["targets"][0], b"",
                 ["head_missing:brain/state", "head_missing:brain/integration", "head_missing:main"])):
            with self.subTest(name):
                self.clean()
                self.two()
                out, _, _ = self.run_cek(summary={"targets": [entry]}, listing=listing)
                line = self.stopped(out, entry["id"])
                self.assertEqual([out["reason"]] + out.get("reasons", []), missing)
                self.assertNotIn("waiting", line)
                self.assertEqual(len(self.fetched()), 1)  # the brain's only
                self.assertEqual(self.assembled(), [])

    def test_the_first_refused_target_stops_cek(self):
        for name, setup, over, first in (
                ("no head", lambda: None, {"t1": self.listing(None)}, "head_missing:brain/integration"),
                ("after the assembly", lambda: self.with_units({"units": []}), {}, "units_not_one")):
            with self.subTest(name):
                self.clean()
                self.BRAIN = CekJob.BRAIN
                summary = self.two()
                setup()
                out, _, _ = self.run_cek(summary=summary, listings=self.listings(**over))
                line = self.stopped(out, "t1")
                self.assertEqual((out["reason"], len(out["targets"])), (first, 1))
                # t2's repository is never asked: no listing, no fetch, no directory; nothing handed over
                self.assertEqual(self.ls_remotes(), [self.URL["t1"]])
                self.assertEqual([u for u, _ in self.fetched() if u == self.URL["t2"]], [])
                self.assertNotIn("t2", os.listdir(os.path.dirname(self.target_dir())))
                self.assertEqual(line["target"], "t1")
        with self.subTest("the second refused after the first held"):
            self.clean()
            self.BRAIN = CekJob.BRAIN
            summary = self.two()
            self.BRAIN = dict(self.BRAIN, **{"targets/t2/units.json": json.dumps({"units": []}).encode()})
            out, _, _ = self.run_cek(summary=summary, listings=self.listings())
            line = self.stopped(out, "t2")
            self.assertEqual((out["reason"], [t["target"] for t in out["targets"]]), ("units_not_one", ["t1", "t2"]))
            self.assertEqual(out["targets"][0]["profile"], {"unit_id": "pkg"})  # t1 held, and is not handed over
            self.assertEqual(self.assembled(), [os.path.join(self.target_dir(t), "pulled") for t in ("t1", "t2")])
            self.assertEqual(line["assembled"]["target"], "t2")

    def test_loop_target_changes_nothing(self):
        # tohum/29s: no variable chooses a target; LOOP_TARGET, set or naming one target, is not read
        self.clean()
        want, _, _ = self.run_cek(summary=self.two(), listings=self.listings())
        self.assertEqual(self.served(), ["t1", "t2"])
        for value in ("t1", "t2", "t9", ""):
            with self.subTest(LOOP_TARGET=value):
                self.clean()
                out, _, _ = self.run_cek(summary=self.two(), listings=self.listings(), env={"LOOP_TARGET": value})
                self.assertEqual(out, want)
                self.assertEqual(self.served(), ["t1", "t2"])

    def test_what_assemble_refuses_is_a_refusal(self):
        brain = {p: d for p, d in self.BRAIN.items() if p != "targets/t1/units.json"}
        brain["candidates/t1/bad name/x"] = b""
        self.BRAIN = brain
        out, _, _ = self.run_cek()
        self.assertEqual((out["reason"], out["reasons"]), ("pulled_refused", ["units_missing",
                                                                               "candidate_invalid:bad name"]))
        self.assertEqual(self.stopped(out)["heads"]["brain/integration"], self.target_commit)
        self.assertEqual(self.assembled(), [])

    def refused_after_assembly(self, reason: str, **kw) -> dict:
        self.clean()  # one run's work directory
        out, _, _ = self.run_cek(**kw)
        self.assertEqual((out["ok"], out["reason"]), (False, reason))
        line = self.stopped(out)
        self.assertEqual(line["assembled"]["commit"], self.target_commit)  # the refusal says what was judged
        self.assertNotIn("profile", line)
        self.assertNotIn("checked", out)
        self.assertEqual(self.assembled(), [os.path.join(self.target_dir(), "pulled")])  # judged, not handed over
        return out

    def with_units(self, units: dict) -> None:
        self.BRAIN = dict(self.BRAIN, **{"targets/t1/units.json": json.dumps(units).encode()})

    def test_the_line_names_the_unit_judged(self):
        self.with_units({"units": [recipe(unit_id="the-unit")]})
        out, _, _ = self.run_cek()
        self.assertEqual((out["done"], self.one(out)["profile"]), (["D1"], {"unit_id": "the-unit"}))

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
                self.retarget({p: d for p, d in dict(CekJob.TARGET, **change).items() if d is not None})
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
        self.retarget(dict(CekJob.TARGET, **{"pkg/out": ("120000", b"../../../../etc")}))
        out = self.refused_after_assembly("pulled_invalid")
        self.assertEqual(out["reasons"], ["tree_unsafe"])

    def test_the_brain_repository_is_bootstrap_json_s(self):
        # tohum/29s: bootstrap.json's brain_repo in the checkout; no variable names it (one in env is not read)
        boot = dict(BOOTSTRAP, brain_repo="o2/brain-2")
        out, commit, _ = self.run_cek(bootstrap=boot, env={"LOOP_BRAIN_REPO": "o/elsewhere", "BRAIN_REPO": "o/x"})
        self.assertTrue(out["ok"], out)
        fetches = [a for a in (c["argv"] for c in S.calls(self.bin)) if "fetch" in a]
        self.assertEqual(fetches[0][-2:], ["https://github.com/o2/brain-2", "%s:refs/pulled" % commit])
        # a file without the model cek does not read is no reason to stop cek
        out, _, _ = self.reset_and_run(bootstrap={"brain_repo": "o/brain"})
        self.assertTrue(out["ok"], out)

    def reset_and_run(self, **kw):
        shutil.rmtree(self.temp)
        os.makedirs(self.temp)
        for name in os.listdir(self.bin):  # the fake git's record of the previous run
            os.remove(os.path.join(self.bin, name))
        return self.run_cek(**kw)

    def test_an_unusable_bootstrap_or_no_sigstore_is_no_verdict_before_anything_is_read(self):
        bad = {"absent": (ABSENT, "bootstrap_unreadable"), "not json": (b"{", "bootstrap_unreadable"),
               "not utf-8": (b'{"brain_repo": "o/\xff"}', "bootstrap_unreadable"),
               "duplicate key": (b'{"brain_repo": "o/brain", "brain_repo": "o/brain"}', "bootstrap_unreadable"),
               "NaN": (b'{"brain_repo": "o/brain", "x": NaN}', "bootstrap_unreadable"),
               "an array": (b'[{"brain_repo": "o/brain"}]', "bootstrap_unreadable"),
               "no brain_repo": ({"rival": {"model": "m"}}, "brain_repo_invalid"),
               "a URL": ({"brain_repo": "https://github.com/o/brain"}, "brain_repo_invalid"),
               "three parts": ({"brain_repo": "o/brain/x"}, "brain_repo_invalid"),
               "a number": ({"brain_repo": 7}, "brain_repo_invalid")}
        for label, (boot, reason) in bad.items():
            with self.subTest(bootstrap=label):
                api = self.TA.FakeApi([self.TA.artifact(11, "2026-11-01T00:00:00Z")], b"")
                with self.assertRaisesRegex(J.Unusable, reason):
                    self.reset_and_run(bootstrap=boot, http=api)
                self.assertFalse(os.path.exists(os.path.join(self.bin, "calls.jsonl")))  # no git ran
                self.assertEqual(api.calls, [])
        with self.subTest(file="a link to a valid file"):
            target = os.path.join(self.base, "elsewhere.json")
            with open(target, "w") as fh:
                json.dump(BOOTSTRAP, fh)
            write_bootstrap(self.work, ABSENT)
            os.symlink(target, os.path.join(self.work, "bootstrap.json"))
            shutil.rmtree(self.temp)
            os.makedirs(self.temp)
            install_sigstore(self.temp)
            with self.assertRaisesRegex(J.Unusable, "bootstrap_unreadable"):
                J.run("cek", {"RUNNER_TEMP": self.temp, "GITHUB_REPOSITORY": "o/r", "GITHUB_TOKEN": "t",
                              "GITHUB_WORKSPACE": self.work},
                      http=self.TA.FakeApi([], b""), verifier=lambda argv: 0)
        with self.subTest(sigstore="not installed"):
            with self.assertRaisesRegex(J.Unusable, "sigstore_missing"):
                self.reset_and_run(sigstore=False)
            self.assertFalse(os.path.exists(os.path.join(self.bin, "calls.jsonl")))

    def test_no_verdict(self):
        for kw in ({"env": {"GITHUB_TOKEN": None}}, {"env": {"GITHUB_WORKSPACE": None}},
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
                                  "GITHUB_WORKSPACE": self.work},
                          http=self.TA.FakeApi([self.TA.artifact(1, "2026-11-01T00:00:00Z")],
                                               self.TA.zip_of(self.TA.GOOD_ZIP)), verifier=lambda argv: 0)
                if name == "policy.json":
                    with open(os.path.join(self.work, "policy.json"), "wb") as fh:
                        fh.write(POLICY)


if __name__ == "__main__":
    unittest.main()
