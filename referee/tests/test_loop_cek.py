"""Test 46 (asama-0/09), MF17, D1: ``loop.cek``, ``çek``'s assembly of the ``pulled`` artifact.

- the tree: the target's git objects (``git_store``) through ``loop.gitobj.tree_tar`` (its own rules are
  ``test_gitobj.py``'s); a commit the source lacks is listed with the brain's reasons;
- the brain, as git objects too (``git_store``): the ``targets[]`` entry, ``units.json`` and every candidate
  directory, read as committed (links, gitlinks, trees where a file belongs, legacy modes), each refusal listed
  together and nothing written, the brain's own object reasons marked ``brain:``; an id that is not one path
  component reads nothing;
- end to end: the target's and the brain's git objects -> ``assemble`` -> ``loop.job run kos`` -> ``gate.check
  decide``: the good candidate merges, the test-breaking one is rejected (``tests_red``).
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
from loop import pulled as P  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
