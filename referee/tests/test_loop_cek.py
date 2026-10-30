"""Test 46 (asama-0/09), MF17, D1: ``loop.cek``, ``çek``'s assembly of the ``pulled`` artifact.

- the tree: the target's git objects (``git_store``) through ``loop.gitobj.tree_tar`` (its own rules are
  ``test_gitobj.py``'s); a commit the source lacks is listed with the brain's reasons;
- the brain: the ``targets[]`` entry, ``units.json`` and every candidate directory, each refusal listed together
  and nothing written; an id that is not one path component reads nothing;
- end to end: the target's git objects + a brain checkout -> ``assemble`` -> ``loop.job run kos`` -> ``gate.check
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


class Brain(unittest.TestCase):
    def setUp(self) -> None:
        self.base = writable_base("t-cek-brain-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.brain = os.path.join(self.base, "brain")
        self.src = os.path.join(self.base, "src")
        write_tree(self.src, TREE)
        self.units = {"units": [recipe()]}
        write_tree(self.brain, {"targets/t1/units.json": self.units})
        for cid, diff in (("good", GOOD), ("breaks", BREAKS_TEST)):
            for f, data in candidate(diff).items():
                write_tree(self.brain, {"candidates/t1/%s/%s" % (cid, f): data.decode()})
        self.out = os.path.join(self.base, "pulled")

    def assemble(self, target_id="t1", summary=None, commit=None, policy=POLICY):
        summary = json.dumps(SUMMARY if summary is None else summary).encode() if not isinstance(summary, bytes) \
            else summary
        objects, own = target_objects(self.src)
        return C.assemble(self.brain, summary, policy, target_id, objects.__getitem__, commit or own, self.out)

    def refused(self, **kw) -> list[str]:
        with self.assertRaises(P.PulledError) as ctx:
            self.assemble(**kw)
        self.assertFalse(os.path.lexists(self.out))
        return ctx.exception.reasons

    def test_the_artifact(self):
        self.assemble()
        got = P.read(self.out)
        self.assertEqual(got.target, SUMMARY["targets"][0])
        self.assertEqual(got.units, self.units)
        self.assertEqual(got.policy, json.loads(POLICY))
        self.assertEqual(got.candidates, {"good": candidate(GOOD), "breaks": candidate(BREAKS_TEST)})
        with open(got.tree_tar, "rb") as fh:
            self.assertEqual(sorted(n[0] for n in names(fh.read()) if n[1] == tarfile.REGTYPE), sorted(TREE))

    def test_no_candidates(self):
        shutil.rmtree(os.path.join(self.brain, "candidates", "t1"))
        self.assemble()
        self.assertEqual(P.read(self.out).candidates, {})
        shutil.rmtree(self.out)
        shutil.rmtree(os.path.join(self.brain, "candidates"))
        self.assemble()
        self.assertEqual(P.read(self.out).candidates, {})

    def test_every_reason_together_and_nothing_written(self):
        write_tree(self.brain, {"candidates/t1/good/notes.md": "x"})
        os.remove(os.path.join(self.brain, "targets/t1/units.json"))
        self.assertEqual(self.refused(summary={"targets": []}, commit="b" * 40),
                         ["target_unknown", "units_missing", "candidate_invalid:good", "object_missing:%s" % ("b" * 40)])

    def test_the_target_id_is_one_path_component(self):
        os.makedirs(os.path.join(self.base, "targets", "x"))
        for bad in ("", "../x", "a/b", ".", "..", ".hidden", "t1\n", None, "x" * 129):
            with self.subTest(bad=bad):
                self.assertEqual(self.refused(target_id=bad), ["target_id_unsafe"])

    def test_the_summary(self):
        for summary, reason in ((b"{", "summary_unreadable"), ({"targets": {}}, "summary_unreadable"),
                                ([SUMMARY], "summary_unreadable"), ({"targets": [{"id": "t2"}]}, "target_unknown"),
                                ({"targets": [{"id": "t1"}, {"id": "t1", "kind": "copy"}]}, "target_ambiguous")):
            with self.subTest(reason=reason, summary=str(summary)[:30]):
                self.assertEqual(self.refused(summary=summary), [reason])

    def test_units_must_be_a_regular_file(self):
        units = os.path.join(self.brain, "targets/t1/units.json")
        outside = os.path.join(self.base, "units.json")
        shutil.move(units, outside)
        os.symlink(outside, units)
        self.assertEqual(self.refused(), ["units_missing"])
        os.remove(units)
        shutil.move(os.path.join(self.brain, "targets", "t1"), os.path.join(self.base, "t1"))
        os.symlink(os.path.join(self.base, "t1"), os.path.join(self.brain, "targets", "t1"))
        self.assertEqual(self.refused(), ["units_missing"])

    def test_candidate_directories(self):
        root = os.path.join(self.brain, "candidates", "t1")
        cases = []
        os.remove(os.path.join(root, "good", "expect.json"))
        cases.append(("a file missing", "good"))
        write_tree(root, {"loose.patch": "x"})
        cases.append(("a file in candidates/<id>", "loose.patch"))
        write_tree(root, {".hidden/diff.patch": "x", ".hidden/expect.json": "{}", ".hidden/finding.json": "{}"})
        cases.append(("not a candidate id", ".hidden"))
        shutil.copytree(os.path.join(root, "breaks"), os.path.join(self.base, "linked"))
        os.symlink(os.path.join(self.base, "linked"), os.path.join(root, "linked"))
        cases.append(("a symlinked candidate", "linked"))
        os.makedirs(os.path.join(root, "filelink"))
        for f in ("diff.patch", "expect.json"):
            shutil.copy(os.path.join(root, "breaks", f), os.path.join(root, "filelink", f))
        os.symlink(os.path.join(root, "breaks", "finding.json"), os.path.join(root, "filelink", "finding.json"))
        cases.append(("a symlinked file", "filelink"))
        os.makedirs(os.path.join(root, "subdir", "diff.patch"))
        for f in ("expect.json", "finding.json"):
            shutil.copy(os.path.join(root, "breaks", f), os.path.join(root, "subdir", f))
        cases.append(("a directory for a file", "subdir"))
        self.assertEqual(self.refused(), sorted("candidate_invalid:%s" % name for _, name in cases))

    def test_candidates_must_be_a_real_directory(self):
        root = os.path.join(self.brain, "candidates")
        shutil.move(root, os.path.join(self.base, "cands"))
        os.symlink(os.path.join(self.base, "cands"), root)
        self.assertEqual(self.refused(), ["candidates_not_directory"])
        os.remove(root)
        os.makedirs(root)
        os.symlink(os.path.join(self.base, "cands", "t1"), os.path.join(root, "t1"))
        self.assertEqual(self.refused(), ["candidates_not_directory"])
        os.remove(os.path.join(root, "t1"))
        write_tree(root, {"t1": "a file"})
        self.assertEqual(self.refused(), ["candidates_not_directory"])

    def test_the_read_back_refuses_and_removes(self):
        write_tree(self.brain, {"targets/t1/units.json": "not json"})
        self.assertEqual(self.refused(), ["json_unreadable:units.json"])
        self.assertEqual(self.refused(policy=b"\xff"), ["json_unreadable:units.json", "json_unreadable:policy.json"])

    def test_out_must_not_exist(self):
        os.makedirs(self.out)
        with self.assertRaises(FileExistsError):
            self.assemble()


class EndToEnd(LK.Base):
    """The target's git objects and a brain checkout -> cek's assembly -> the kos job -> MF8's decision."""

    run_kos, results, decide = LK.KosJob.run_kos, LK.KosJob.results, LK.KosJob.decide

    def test_cek_to_kos_to_the_gate(self):
        brain = os.path.join(self.base, "brain")
        write_tree(brain, {"targets/t1/units.json": {"units": [recipe()]}})
        for cid, diff in (("good", GOOD), ("breaks", BREAKS_TEST)):
            for f, data in candidate(diff).items():
                write_tree(brain, {"candidates/t1/%s/%s" % (cid, f): data.decode()})
        objects, commit = target_objects(self.src)
        C.assemble(brain, json.dumps(SUMMARY).encode(), POLICY, "t1", objects.__getitem__, commit, self.pulled)
        out = self.run_kos()
        self.assertEqual((out["reason"], out["done"]), ("cycle_not_wired", ["D3"]))
        self.assertEqual(out["index"]["base"], {"verdict": "verified", "reasons": []})
        self.assertEqual(self.decide("good")["decision"], "merge")
        self.assertEqual((self.decide("breaks")["decision"], self.decide("breaks")["reasons"]),
                         ("reject", ["tests_red"]))


if __name__ == "__main__":
    unittest.main()
