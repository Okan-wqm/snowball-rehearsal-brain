"""Test 46 (asama-0/09), MF17, D1: ``loop.gitobj``, a commit's tree read from its git objects by content id.

- real git: ``fixtures/git-objects.batch`` is ``git cat-file --batch-all-objects --batch`` of a repository made
  with git 2.47.3 (recipe in ``REAL``): a nested file, an empty-free nested directory, a symlink, an executable,
  a CRLF file, ``hidden.txt`` marked ``export-ignore`` and ``subst.txt`` marked ``export-subst``. ``git archive``
  of that commit leaves ``hidden.txt`` out; ``tree_tar`` keeps it and keeps ``subst.txt`` unexpanded, the CRLF
  bytes, the link and the modes (asama-0/06: ``.gitattributes`` has no effect). The same files built by
  ``git_store`` give real git's tree id, so the in-Python objects below are git's format;
- ``GitBatch`` over a fake ``git`` on PATH that answers with real git's records: its argv, its environment
  (no inherited ``GIT_*``), a missing object, an answer that is not the protocol;
- every refusal of the walk, listed together; a lying source (content or type changed) is refused;
- ``tree_tar`` is deterministic and unpacks with ``loop.pulled.extract_tree``, empty directories included.
"""

from __future__ import annotations

import io
import os
import shutil
import sys
import tarfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loop import gitobj as G  # noqa: E402
from loop import pulled as P  # noqa: E402
from profile_tree import writable_base  # noqa: E402
import git_store as S  # noqa: E402

FIXTURE = os.path.join(REFEREE, "tests", "fixtures", "git-objects.batch")
# git init -b main; files as below; chmod +x x.sh; ln -s d/a.txt link; git add -A;
# GIT_AUTHOR_DATE=GIT_COMMITTER_DATE='1700000000 +0000' git -c user.name=A -c user.email=a@example.org commit -m fixture
REAL = {
    ".gitattributes": b"hidden.txt export-ignore\nsubst.txt export-subst\n",
    "d/a.txt": b"hi\n",
    "e/f/win.txt": b"crlf\r\n",
    "hidden.txt": b"hidden\n",
    "link": ("120000", b"d/a.txt"),
    "subst.txt": b"id: $Format:%H$\n",
    "x.sh": ("100755", b"#!/bin/sh\necho x\n"),
}
REAL_COMMIT = "265111f095bfacdaa9ab28c23b217d432eb3d60f"
REAL_TREE = "8eaf6ffd50d03ba51d2b619e8af7f244e86901cd"


def real_objects() -> dict:
    with open(FIXTURE, "rb") as fh:
        return S.parse_batch(fh.read())


def members(tar_bytes: bytes) -> list[tuple]:
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tar:
        return [(m.name, m.type, m.linkname, m.mode, tar.extractfile(m).read() if m.isreg() else None)
                for m in tar.getmembers()]


class RealGit(unittest.TestCase):
    def test_the_tree_of_a_real_commit(self):
        out = G.tree_tar(real_objects().__getitem__, REAL_COMMIT)
        self.assertEqual(members(out), [
            (".gitattributes", tarfile.REGTYPE, "", 0o644, REAL[".gitattributes"]),
            ("d", tarfile.DIRTYPE, "", 0o755, None),
            ("d/a.txt", tarfile.REGTYPE, "", 0o644, b"hi\n"),
            ("e", tarfile.DIRTYPE, "", 0o755, None),
            ("e/f", tarfile.DIRTYPE, "", 0o755, None),
            ("e/f/win.txt", tarfile.REGTYPE, "", 0o644, b"crlf\r\n"),
            ("hidden.txt", tarfile.REGTYPE, "", 0o644, b"hidden\n"),       # export-ignore has no effect
            ("link", tarfile.SYMTYPE, "d/a.txt", 0o777, None),
            ("subst.txt", tarfile.REGTYPE, "", 0o644, b"id: $Format:%H$\n"),  # export-subst has no effect
            ("x.sh", tarfile.REGTYPE, "", 0o755, b"#!/bin/sh\necho x\n"),
        ])

    def test_git_store_writes_gits_format(self):
        objects, commit = S.store(REAL)
        self.assertEqual(G._tree_sha(objects[commit][1]), REAL_TREE)
        self.assertEqual({sha for sha, (kind, _) in objects.items() if kind != "commit"},
                         {sha for sha, (kind, _) in real_objects().items() if kind != "commit"})


class Batch(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = writable_base("t-gitobj-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.answers = {sha: S.batch_record(sha, kind, data) for sha, (kind, data) in real_objects().items()}

    def source(self, answers=None, environ=None, exit_after=()) -> G.GitBatch:
        git = S.install_git(self.dir, self.answers if answers is None else answers, exit_after)
        return G.GitBatch("/repo.git", git=git, environ=environ)

    def test_reads_through_cat_file_batch(self):
        env = {"PATH": "/usr/bin", "GIT_DIR": "/elsewhere", "GIT_CONFIG_PARAMETERS": "'core.x=1'", "HOME": "/h"}
        with self.source(environ=env) as src:
            out = G.tree_tar(src, REAL_COMMIT)
        self.assertEqual(out, G.tree_tar(real_objects().__getitem__, REAL_COMMIT))
        (call,) = S.calls(self.dir)
        self.assertEqual(call["argv"], ["--git-dir=/repo.git", "cat-file", "--batch"])
        self.assertEqual(sorted(k for k in call["env"] if k.startswith("GIT_")),
                         ["GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM"])
        self.assertEqual((call["env"]["GIT_CONFIG_GLOBAL"], call["env"]["GIT_CONFIG_NOSYSTEM"], call["env"]["HOME"]),
                         ("/dev/null", "1", "/h"))

    def test_a_missing_object(self):
        blob = G.object_id("blob", b"hi\n")
        del self.answers[blob]
        with self.source() as src:
            with self.assertRaises(KeyError):
                src(blob)
            with self.assertRaises(P.PulledError) as ctx:
                G.tree_tar(src, REAL_COMMIT)
        self.assertEqual(ctx.exception.reasons, ["object_missing:%s" % blob])

    def test_an_answer_outside_the_protocol(self):
        blob = G.object_id("blob", b"hi\n")
        record = self.answers[blob]
        # each answer is followed by git ending: a git that stalls with its pipe open is the job's timeout's
        for name, answer in (("short", record[:-3]), ("no newline", record[:-1] + b"X"), ("nothing", b""),
                             ("other sha", record.replace(blob.encode(), b"0" * 40, 1)),
                             ("other sha missing", b"%s missing\n" % (b"0" * 40)),
                             ("no size", b"%s blob\n" % blob.encode()),
                             ("size not a number", b"%s blob x\n" % blob.encode())):
            with self.subTest(name):
                with self.source(dict(self.answers, **{blob: answer}), exit_after=(blob,)) as src:
                    with self.assertRaises(P.PulledError) as ctx:
                        src(blob)
                self.assertEqual(ctx.exception.reasons, ["git_batch_unreadable"])
        with self.source() as src:
            with self.assertRaises(KeyError):
                src("not-a-sha")


class Walk(unittest.TestCase):
    def refused(self, objects: dict, commit: str) -> list[str]:
        with self.assertRaises(P.PulledError) as ctx:
            G.entries(objects.__getitem__, commit)
        return ctx.exception.reasons

    def test_a_lying_source_is_refused(self):
        objects, commit = S.store({"a": b"x"})
        blob = G.object_id("blob", b"x")
        self.assertEqual(self.refused(dict(objects, **{blob: ("blob", b"y")}), commit), ["object_mismatch:%s" % blob])
        self.assertEqual(self.refused(dict(objects, **{blob: ("tree", b"x")}), commit), ["object_mismatch:%s" % blob])
        self.assertEqual(self.refused(dict(objects, **{commit: ("blob", objects[commit][1])}), commit),
                         ["object_mismatch:%s" % commit])
        tree_sha = G._tree_sha(objects[commit][1])
        self.assertEqual(self.refused({commit: objects[commit]}, commit), ["object_missing:%s" % tree_sha])

    def test_the_commit(self):
        objects: dict = {}
        bad = S.put(objects, "commit", b"author x\n")
        self.assertEqual(self.refused(objects, bad), ["commit_unreadable"])
        for commit in ("A" * 40, "a" * 39, None):
            self.assertEqual(self.refused(objects, commit), ["commit_unreadable"])
        self.assertEqual(self.refused(objects, "a" * 40), ["object_missing:%s" % ("a" * 40)])

    def test_every_bad_entry_listed_together(self):
        objects: dict = {}
        blob = S.put(objects, "blob", b"x")
        odd_link = S.put(objects, "blob", b"\xff")
        sub = S.tree(objects, [(b"100644", b"..", blob), (b"100644", b"ok", blob)])
        broken = S.put(objects, "tree", b"100644 cut\0" + bytes(5))
        root = S.tree(objects, [
            (b"100644", b"", blob), (b"100644", b".", blob), (b"100644", b".GIT", blob), (b"100644", b"a/b", blob),
            (b"100644", b"\xfe", blob), (b"100644", b"dup", blob), (b"100755", b"dup", blob),
            (b"100664", b"legacy", blob), (b"160000", b"mod", blob), (b"120000", b"odd", odd_link),
            (b"40000", b"sub", sub), (b"40000", b"broken", broken), (b"100644", b"gone", "c" * 40),
        ])
        commit = S.commit(objects, root)
        self.assertEqual(self.refused(objects, commit), sorted([
            "tree_name:", "tree_name:.", "tree_name:.GIT", "tree_name:a/b", "tree_name:�",
            "tree_duplicate:dup", "tree_mode:legacy:100664", "tree_submodule:mod", "tree_link:odd",
            "tree_name:sub/..", "tree_unreadable:%s" % broken, "object_missing:%s" % ("c" * 40)]))

    def test_entries_need_their_own_type(self):
        objects: dict = {}
        blob = S.put(objects, "blob", b"x")
        tree_sha = S.tree(objects, [(b"100644", b"a", blob)])
        root = S.tree(objects, [(b"40000", b"d", blob), (b"100644", b"f", tree_sha)])
        self.assertEqual(self.refused(objects, S.commit(objects, root)),
                         sorted(["object_mismatch:%s" % blob, "object_mismatch:%s" % tree_sha]))


class TreeTar(unittest.TestCase):
    def setUp(self) -> None:
        self.base = writable_base("t-gitobj-tar-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)

    def test_deterministic_and_unpacked_by_extract_tree(self):
        objects, commit = S.store(REAL)
        empty = S.tree(objects, [])
        root = G.parse_tree(objects[G._tree_sha(objects[commit][1])][1], "")
        commit = S.commit(objects, S.tree(objects, root + [(b"40000", b"z-empty", empty)]))
        out = G.tree_tar(objects.__getitem__, commit)
        self.assertEqual(out, G.tree_tar(dict(reversed(list(objects.items()))).__getitem__, commit))
        with tarfile.open(fileobj=io.BytesIO(out), mode="r:") as tar:
            self.assertEqual({(m.mtime, m.uid, m.gid, m.uname, m.gname) for m in tar.getmembers()},
                             {(0, 0, 0, "", "")})
        path = os.path.join(self.base, "tree.tar")
        with open(path, "wb") as fh:
            fh.write(out)
        dest = os.path.join(self.base, "tree")
        P.extract_tree(path, dest)
        self.assertEqual(os.listdir(os.path.join(dest, "z-empty")), [])
        self.assertEqual(os.readlink(os.path.join(dest, "link")), "d/a.txt")
        self.assertTrue(os.access(os.path.join(dest, "x.sh"), os.X_OK))
        with open(os.path.join(dest, "hidden.txt"), "rb") as fh:
            self.assertEqual(fh.read(), b"hidden\n")

    def test_what_the_tree_holds_is_left_to_extract_tree(self):
        # gitobj reads; an escaping symlink passes here and kos's extract_tree refuses it (one rule, one place)
        objects, commit = S.store({"l": ("120000", b"../../etc")})
        path = os.path.join(self.base, "tree.tar")
        with open(path, "wb") as fh:
            fh.write(G.tree_tar(objects.__getitem__, commit))
        with self.assertRaises(P.PulledError) as ctx:
            P.extract_tree(path, os.path.join(self.base, "tree"))
        self.assertEqual(ctx.exception.reasons, ["tree_unsafe"])


if __name__ == "__main__":
    unittest.main()
