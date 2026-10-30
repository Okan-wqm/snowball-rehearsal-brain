"""Test 46 (asama-0/09), MF17, D1: ``loop.cek``, ``çek``'s assembly of the ``pulled`` artifact.

- the tree: ``tree_tar`` on a real ``git archive --format=tar.gz --prefix=`` output (``fixtures/git-archive.tgz``,
  git 2.x, one directory, a file, a symlink, an executable) drops the top directory and keeps links and modes;
  every refusal (commit mismatch or absent, not gzip, a member or hard link outside the top, no top directory);
- the brain: the ``targets[]`` entry, ``units.json`` and every candidate directory, each refusal listed together
  and nothing written; an id that is not one path component reads nothing;
- end to end: GitHub-shaped tarball + a brain checkout -> ``assemble`` -> ``loop.job run kos`` -> ``gate.check
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
from profile_tree import writable_base, write_tree  # noqa: E402
from test_kos import BREAKS_TEST, GOOD, operating, recipe  # noqa: E402
import test_loop_kos as LK  # noqa: E402
from test_loop_kos import TREE, candidate  # noqa: E402

FIXTURE = os.path.join(REFEREE, "tests", "fixtures", "git-archive.tgz")
FIXTURE_COMMIT = "120cfdae0984b431fb6d9c693a8821bcef842b95"
COMMIT = "a" * 40
SUMMARY = {"targets": [{"id": "t1", "kind": "toy", "excluded_paths": [], "unit_candidates": []},
                       {"id": "t2", "kind": "copy", "excluded_paths": ["x"], "unit_candidates": []}]}
POLICY = json.dumps({"operating": operating()}).encode()


def info(name: str, kind: bytes = tarfile.REGTYPE, size: int = 0, linkname: str = "", mode: int = 0o644):
    i = tarfile.TarInfo(name)
    i.type, i.size, i.linkname, i.mode = kind, size, linkname, mode
    return i


def tgz(members: list[tuple[tarfile.TarInfo, bytes | None]], comment: str | None = COMMIT) -> bytes:
    """A tar.gz in git archive's shape: a pax global header with the commit, members as given."""
    buf = io.BytesIO()
    headers = {"comment": comment} if comment is not None else {}
    with tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.PAX_FORMAT, pax_headers=headers) as tar:
        for i, data in members:
            tar.addfile(i, io.BytesIO(data) if data is not None else None)
    return buf.getvalue()


def github_tarball(root: str, top: str = "own-t1-aaaaaaa", comment: str = COMMIT) -> bytes:
    members = [(info(top, tarfile.DIRTYPE, mode=0o755), None)]
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        rel = os.path.relpath(dirpath, root)
        if rel != ".":
            members.append((info("%s/%s" % (top, rel.replace(os.sep, "/")), tarfile.DIRTYPE, mode=0o755), None))
        for f in sorted(filenames):
            with open(os.path.join(dirpath, f), "rb") as fh:
                data = fh.read()
            name = "%s/%s" % (top, os.path.relpath(os.path.join(dirpath, f), root).replace(os.sep, "/"))
            members.append((info(name, size=len(data)), data))
    return tgz(members, comment)


def names(tar_bytes: bytes) -> list[tuple[str, bytes, str, int]]:
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tar:
        return [(m.name, m.type, m.linkname, m.mode) for m in tar.getmembers()]


class Tree(unittest.TestCase):
    def setUp(self) -> None:
        self.base = writable_base("t-cek-tree-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        with open(FIXTURE, "rb") as fh:
            self.real = fh.read()

    def refused(self, tarball: bytes, commit: str = COMMIT) -> list[str]:
        with self.assertRaises(P.PulledError) as ctx:
            C.tree_tar(tarball, commit)
        return ctx.exception.reasons

    def test_real_git_archive(self):
        out = C.tree_tar(self.real, FIXTURE_COMMIT)
        self.assertEqual(names(out), [("d", tarfile.DIRTYPE, "", 0o775), ("d/a.txt", tarfile.REGTYPE, "", 0o664),
                                      ("link", tarfile.SYMTYPE, "d/a.txt", 0o777),
                                      ("x.sh", tarfile.REGTYPE, "", 0o775)])
        path = os.path.join(self.base, "tree.tar")
        with open(path, "wb") as fh:
            fh.write(out)
        dest = os.path.join(self.base, "tree")
        P.extract_tree(path, dest)
        with open(os.path.join(dest, "link"), "rb") as fh:
            self.assertEqual(fh.read(), b"hi\n")
        self.assertTrue(os.access(os.path.join(dest, "x.sh"), os.X_OK))
        self.assertEqual(sorted(os.listdir(dest)), ["d", "link", "x.sh"])

    def test_the_commit_must_be_the_archived_one(self):
        self.assertEqual(self.refused(self.real, "b" * 40), ["tarball_commit_mismatch"])
        top = (info("top", tarfile.DIRTYPE), None)
        self.assertEqual(self.refused(tgz([top], comment=None)), ["tarball_commit_mismatch"])

    def test_not_a_gzip_tar(self):
        self.assertEqual(self.refused(b"not a tarball" * 50), ["tarball_unreadable"])
        self.assertEqual(self.refused(self.real[:100], FIXTURE_COMMIT), ["tarball_unreadable"])
        plain = io.BytesIO()
        with tarfile.open(fileobj=plain, mode="w", pax_headers={"comment": COMMIT}) as tar:
            tar.addfile(info("top", tarfile.DIRTYPE))
        self.assertEqual(self.refused(plain.getvalue()), ["tarball_unreadable"])

    def test_one_top_directory(self):
        top = (info("top", tarfile.DIRTYPE), None)
        cases = {
            "first is a file": [(info("top", size=1), b"x")],
            "first is nested": [(info("top/sub", tarfile.DIRTYPE), None)],
            "a member outside": [top, (info("top/a", size=1), b"x"), (info("other/b", size=1), b"x")],
            "a sibling prefix": [top, (info("topx/a", size=1), b"x")],
            "the top again": [top, (info("top/", tarfile.DIRTYPE), None)],
            "a hard link outside": [top, (info("top/a", tarfile.LNKTYPE, linkname="other/b"), None)],
        }
        for name, members in cases.items():
            with self.subTest(name):
                self.assertEqual(self.refused(tgz(members)), ["tarball_layout"])
        # no member after the global header: tarfile itself refuses to read it ("end of file header")
        self.assertEqual(self.refused(tgz([])), ["tarball_unreadable"])

    def test_a_hard_link_inside_is_renamed(self):
        out = C.tree_tar(tgz([(info("top", tarfile.DIRTYPE), None), (info("top/a", size=2), b"hi"),
                              (info("top/b", tarfile.LNKTYPE, linkname="top/a"), None)]), COMMIT)
        self.assertEqual([n[:3] for n in names(out)], [("a", tarfile.REGTYPE, ""), ("b", tarfile.LNKTYPE, "a")])
        path = os.path.join(self.base, "tree.tar")
        with open(path, "wb") as fh:
            fh.write(out)
        P.extract_tree(path, os.path.join(self.base, "tree"))
        with open(os.path.join(self.base, "tree", "b"), "rb") as fh:
            self.assertEqual(fh.read(), b"hi")

    def test_what_the_tree_holds_is_left_to_extract_tree(self):
        # cek reshapes; an escaping symlink passes here and kos's extract_tree refuses it (one rule, one place)
        out = C.tree_tar(tgz([(info("top", tarfile.DIRTYPE), None),
                              (info("top/l", tarfile.SYMTYPE, linkname="../../etc"), None)]), COMMIT)
        path = os.path.join(self.base, "tree.tar")
        with open(path, "wb") as fh:
            fh.write(out)
        with self.assertRaises(P.PulledError) as ctx:
            P.extract_tree(path, os.path.join(self.base, "tree"))
        self.assertEqual(ctx.exception.reasons, ["tree_unsafe"])


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

    def assemble(self, target_id="t1", summary=None, tarball=None, commit=COMMIT, policy=POLICY):
        summary = json.dumps(SUMMARY if summary is None else summary).encode() if not isinstance(summary, bytes) \
            else summary
        return C.assemble(self.brain, summary, policy, target_id,
                          github_tarball(self.src) if tarball is None else tarball, commit, self.out)

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
                         ["target_unknown", "units_missing", "candidate_invalid:good", "tarball_commit_mismatch"])

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
    """GitHub's tarball and a brain checkout -> cek's assembly -> the kos job -> MF8's decision."""

    run_kos, results, decide = LK.KosJob.run_kos, LK.KosJob.results, LK.KosJob.decide

    def test_cek_to_kos_to_the_gate(self):
        brain = os.path.join(self.base, "brain")
        write_tree(brain, {"targets/t1/units.json": {"units": [recipe()]}})
        for cid, diff in (("good", GOOD), ("breaks", BREAKS_TEST)):
            for f, data in candidate(diff).items():
                write_tree(brain, {"candidates/t1/%s/%s" % (cid, f): data.decode()})
        C.assemble(brain, json.dumps(SUMMARY).encode(), POLICY, "t1", github_tarball(self.src), COMMIT, self.pulled)
        out = self.run_kos()
        self.assertEqual((out["reason"], out["done"]), ("cycle_not_wired", ["D3"]))
        self.assertEqual(out["index"]["base"], {"verdict": "verified", "reasons": []})
        self.assertEqual(self.decide("good")["decision"], "merge")
        self.assertEqual((self.decide("breaks")["decision"], self.decide("breaks")["reasons"]),
                         ("reject", ["tests_red"]))


if __name__ == "__main__":
    unittest.main()
