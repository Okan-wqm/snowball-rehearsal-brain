"""Test 8 (asama-0/09, P1 MF2): ``snapshot.make``; no leak (no ``.git``, no ``<state_root>``, no excluded
directory) and the planted identities replaced (asama-1/13c, tohum/26a).

What is measured: the snapshot of a commit built as git objects in git's own format (``git_store``), its
manifest compared with a set written here, its id with a hash computed by hand in this file (``id_by_hand``),
and the bytes of every file searched for every identifier. A written snapshot is read back from the disk.

The live path (``Cek``, ``LivePath``): ``loop.cek.assemble`` puts the commit's clean snapshot document in
``pulled``; the ``kos`` job (``loop.job.run``) writes it out from the pulled tree and the organ it calls sees, as
its tree, the snapshot's files and nothing else (the organ lists ``/work`` under the recording stand-in for
docker, ``fake_docker``); a document that is not the tree's is refused before any run. Not run here: a real
docker, a real target (measured in a session, the ledger has the numbers), a planted snapshot on the loop's path
(it has no caller there yet).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loop import cek as C  # noqa: E402
from loop import pulled as P  # noqa: E402
from profile import derive as D  # noqa: E402
from runner import kos as K  # noqa: E402
from runner import organs  # noqa: E402
from snapshot import make as SM  # noqa: E402
import git_store as S  # noqa: E402
import test_loop_cek as TC  # noqa: E402
import test_loop_kos as LK  # noqa: E402
from profile_tree import writable_base  # noqa: E402
from test_organs import Capture  # noqa: E402

KEPT = {
    "src/a.js": b"const a = 1;\n",
    "src/run.sh": ("100755", b"#!/bin/sh\n"),
    "docs/readme.md": b"read me\n",
    "hidden.txt": b"export-ignore does not hide me\n",
    ".gitattributes": b"hidden.txt export-ignore\n",
    "lib/.brain/kept.txt": b"a .brain deeper in the tree is not the state root\n",
    "brainy/.brain": b"nor is a file of that name there\n",
    ".brainstorm.md": b"nor a name that only starts like it\n",
    "latest": ("120000", b"src/a.js"),
}
LEAKS = {
    ".brain/ledger.jsonl": b"{}\n",                       # state_root
    ".brain/chain/root.jsonl": b"{}\n",
    "node_modules/dep/index.js": b"module.exports = 1\n",  # excluded_dir
    "src/Node_Modules/x.js": b"1\n",
    "web/dist/bundle.js": b"1\n",
    "tools/__pycache__/m.pyc": b"\x00",
    ".cursor/rules": b"1\n",
    "CLAUDE.md": b"instructions\n",                        # agent_config
    "docs/agents.md": b"instructions\n",
    ".claude/settings.json": b"{}\n",
    "pkg/.mcp.json": b"{}\n",
    "vendor/big/blob.bin": b"\x01\x02",                    # excluded_path (the operator's)
    "private": ("120000", b"src/a.js"),
}
TARGET = {"id": "t1", "kind": "toy", "excluded_paths": ["vendor/**", "/private"], "unit_candidates": []}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content(value) -> bytes:
    return value[1] if isinstance(value, tuple) else value


def id_by_hand(files: dict, links: dict, execs: list) -> str:
    """13c's content hash as the module's docstring states it, written out here."""
    body = '{"exec":[%s],"files":{%s},"links":{%s}}' % (
        ",".join(json.dumps(p) for p in sorted(execs)),
        ",".join("%s:%s" % (json.dumps(p), json.dumps(sha(d))) for p, d in sorted(files.items())),
        ",".join("%s:%s" % (json.dumps(p), json.dumps(t)) for p, t in sorted(links.items())))
    return sha(body.encode("utf-8"))


def make(files: dict, cases=None, kind="clean", target=None, max_cases=None) -> SM.Snapshot:
    objects, commit = S.store(files)
    return SM.make(objects.__getitem__, commit, [] if cases is None else cases, kind, target, max_cases)


def case(paths, identifiers=(), replace=None, prop="P-auth") -> dict:
    return {"property": prop, "paths": list(paths), "identifiers": list(identifiers), "replace": dict(replace or {})}


def reasons(files: dict, cases, kind="planted", max_cases=5, target=None) -> list:
    try:
        make(files, cases, kind, target, max_cases)
    except SM.SnapshotError as exc:
        return exc.reasons
    return []


def on_disk(root: str) -> dict:
    """What a directory holds: path -> bytes of a file, ``("link", target)`` of a link; no directory entry."""
    out: dict = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            full = os.path.join(dirpath, name)
            path = os.path.relpath(full, root).replace(os.sep, "/")
            if os.path.islink(full):
                out[path] = ("link", os.readlink(full))
            elif os.path.isfile(full):
                with open(full, "rb") as fh:
                    out[path] = fh.read()
    return out


class NoLeak(unittest.TestCase):
    """Test 8, first half: what a snapshot holds and what it leaves out."""

    def test_state_root_excluded_dirs_agent_config_and_operator_paths_are_left_out(self):
        got = make(dict(KEPT, **LEAKS), target=TARGET)
        files = {p: content(v) for p, v in KEPT.items() if p != "latest"}
        self.assertEqual(got.document["files"], {p: sha(d) for p, d in sorted(files.items())})
        self.assertEqual(got.document["links"], {"latest": "src/a.js"})
        self.assertEqual(got.files, files)
        self.assertEqual(got.left_out, {"state_root": 2, "excluded_dir": 5, "agent_config": 4, "excluded_path": 2})
        # by name, over everything the document names: no component of a kept path is a leak's
        named = list(got.document["files"]) + list(got.document["links"])
        self.assertFalse([p for p in named if p == ".brain" or p.startswith(".brain/")])
        banned = {n.casefold() for n in D.AGENT_CONFIG + D.EXCLUDED_DIR_NAMES} | {".git"}
        self.assertFalse([p for p in named if banned & {part.casefold() for part in p.split("/")}])

    def test_without_the_operators_patterns_only_their_paths_come_back(self):
        got = make(dict(KEPT, **LEAKS))
        self.assertEqual(sorted(set(got.document["files"]) - set(KEPT)), ["vendor/big/blob.bin"])
        self.assertEqual(got.document["links"], {"latest": "src/a.js", "private": "src/a.js"})

    def test_export_ignore_hides_nothing(self):
        got = make(KEPT)
        self.assertEqual(got.files["hidden.txt"], KEPT["hidden.txt"])
        self.assertIn(".gitattributes", got.document["files"])

    def test_a_tree_with_a_git_entry_or_a_gitlink_gives_no_snapshot(self):
        for name, files, reason in (
                ("a .git directory", dict(KEPT, **{".git/config": b"[core]\n"}), "tree_name:.git"),
                ("in another case, deeper", dict(KEPT, **{"sub/.GIT/HEAD": b"ref\n"}), "tree_name:sub/.GIT"),
                ("a .git file", dict(KEPT, **{"mod/.git": b"gitdir: ../x\n"}), "tree_name:mod/.git"),
                ("a gitlink", dict(KEPT, **{"mod": ("160000", b"")}), "tree_submodule:mod")):
            with self.subTest(name):
                with self.assertRaises(P.PulledError) as ctx:
                    make(files)
                self.assertEqual(ctx.exception.reasons, [reason])

    def test_an_invalid_target_entry_is_refused_by_the_profiles_rule(self):
        with self.assertRaises(D.DeriveError):
            make(KEPT, target={"id": "t1", "excluded_paths": "vendor"})


class Identity(unittest.TestCase):
    """13c "Kimlik": ``snapshot_id`` and the manifest."""

    def test_the_id_is_the_stated_hash_and_the_manifest_each_files_sha256(self):
        got = make(dict(KEPT, **LEAKS), target=TARGET).document
        files = {p: content(v) for p, v in KEPT.items() if p != "latest"}
        self.assertEqual(sorted(got), ["exec", "files", "links", "schema", "snapshot_id"])
        self.assertEqual(got["schema"], "snowball-snapshot/1")
        self.assertEqual(got["exec"], ["src/run.sh"])
        self.assertEqual(got["snapshot_id"], id_by_hand(files, {"latest": "src/a.js"}, ["src/run.sh"]))
        # one manifest value as sha256sum printed it for the file's bytes
        self.assertEqual(got["files"]["src/a.js"], "b79b14bd2584dd52b0f0ef042a2a4f104cda48330500e12237737cc51fbda43d")

    def test_the_id_changes_with_a_byte_a_path_a_link_and_an_execute_bit(self):
        base = make(KEPT).document["snapshot_id"]
        changed = {
            "a byte": dict(KEPT, **{"src/a.js": b"const a = 2;\n"}),
            "a path": {("src/b.js" if p == "src/a.js" else p): v for p, v in KEPT.items()},
            "a file more": dict(KEPT, extra=b""),
            "a link's target": dict(KEPT, latest=("120000", b"src/run.sh")),
            "a link's path": {("newest" if p == "latest" else p): v for p, v in KEPT.items()},
            "an execute bit": dict(KEPT, **{"src/run.sh": b"#!/bin/sh\n"}),
        }
        ids = {name: make(files).document["snapshot_id"] for name, files in changed.items()}
        self.assertEqual(len(set(ids.values()) | {base}), len(changed) + 1, ids)

    def test_the_same_commit_gives_the_same_id_and_a_left_out_file_does_not_enter(self):
        self.assertEqual(make(KEPT).document, make(dict(reversed(list(KEPT.items())))).document)
        self.assertEqual(make(dict(KEPT, **LEAKS), target=TARGET).document, make(KEPT, target=TARGET).document)


ID, SHA_, TITLE = "FND-0042", "9f2c1e7a5b3d4c6e8f0a1b2c3d4e5f6a7b8c9d0e", "Tenant check missing in export"
PLANT = {
    "src/a.js": b"const a = 1;\n",
    "src/export.js": b"// fixed by 9f2c1e7a5b3d4c6e8f0a1b2c3d4e5f6a7b8c9d0e (FND-0042)\nexport const ok = check();\n",
    "CHANGELOG.md": b"- FND-0042: Tenant check missing in export\n- FND-0042 again, and FND-00420\n",
    "docs/notes.bin": b"\x00\xffFND-0042\xfe\x00",
    "src/string.js": b'const s = "FND-0042";\n',
    "other/b.js": b"const b = 2;\n",
    "link": ("120000", b"src/a.js"),
}
PLANTED = b"// reverts 9f2c1e7a5b3d4c6e8f0a1b2c3d4e5f6a7b8c9d0e\nexport const ok = true; // FND-0042\n"


class Planted(unittest.TestCase):
    """Test 8, second half: the planted identities are replaced; 13c's rules of a planted snapshot."""

    def one(self) -> dict:
        return case(["src/export.js"], [ID, SHA_, TITLE], {"src/export.js": PLANTED})

    def test_every_identifier_is_replaced_in_every_file(self):
        got = make(PLANT, [self.one()], "planted", max_cases=5)
        for needle in (ID, SHA_, TITLE):
            self.assertEqual([p for p, d in got.files.items() if needle.encode() in d], [], needle)
        self.assertEqual(got.files, {
            "src/a.js": b"const a = 1;\n",
            "src/export.js": b"// reverts REDACTED\nexport const ok = true; // REDACTED\n",   # the planted content
            "CHANGELOG.md": b"- REDACTED: REDACTED\n- REDACTED again, and REDACTED0\n",
            "docs/notes.bin": b"\x00\xffREDACTED\xfe\x00",          # any file, text or not
            "src/string.js": b'const s = "REDACTED";\n',           # a string literal too: every identity, every file
            "other/b.js": b"const b = 2;\n"})
        # the manifest and the id are of the bytes after the replacement
        self.assertEqual(got.document["files"], {p: sha(d) for p, d in sorted(got.files.items())})
        self.assertEqual(got.document["snapshot_id"], id_by_hand(got.files, {"link": "src/a.js"}, []))

    def test_the_written_directory_holds_no_identifier(self):
        base = writable_base("t-snap-")
        self.addCleanup(shutil.rmtree, base, ignore_errors=True)
        got = make(PLANT, [self.one()], "planted", max_cases=5)
        SM.write(got.document, os.path.join(base, "s"), got.files.get)
        held = on_disk(os.path.join(base, "s"))
        self.assertEqual(sorted(held), sorted(list(got.files) + ["link"]))
        for needle in (ID, SHA_, TITLE):
            self.assertEqual([p for p, d in held.items() if isinstance(d, bytes) and needle.encode() in d], [])

    def test_the_longest_identifier_is_taken_where_two_start_together(self):
        files = {"a.txt": b"FND-1 FND-12 FND-123\n", "b.txt": b"x\n"}
        got = make(files, [case(["b.txt"], ["FND-1", "FND-12"])], "planted", max_cases=1)
        self.assertEqual(got.files["a.txt"], b"REDACTED REDACTED REDACTED3\n")

    def test_a_planted_and_a_clean_document_have_the_same_shape(self):
        clean = make(PLANT).document
        planted = make(PLANT, [self.one()], "planted", max_cases=5).document
        self.assertEqual(sorted(clean), sorted(planted))
        self.assertEqual((sorted(clean["files"]), clean["links"], clean["exec"]),
                         (sorted(planted["files"]), planted["links"], planted["exec"]))
        self.assertNotIn("planted", json.dumps(planted))
        self.assertNotIn("clean", json.dumps(clean))
        self.assertNotIn("P-auth", json.dumps(planted))
        self.assertNotEqual(clean["snapshot_id"], planted["snapshot_id"])

    def test_a_clean_snapshot_takes_no_case_and_changes_no_byte(self):
        self.assertEqual(reasons(PLANT, [self.one()], "clean"), ["clean_has_cases"])
        self.assertEqual(make(PLANT).files, {p: d for p, d in PLANT.items() if p != "link"})

    def test_the_rules_of_a_planted_snapshot(self):
        a, b = case(["src/a.js"]), case(["other/b.js"])
        for name, cases, limit, want in (
                ("no case", [], 5, ["planted_no_cases"]),
                ("more than the limit", [a, b], 1, ["cases_over_max"]),
                ("no limit given", [a], None, ["max_cases_invalid"]),
                ("a limit of zero", [a], 0, ["max_cases_invalid"]),
                ("a limit that is true", [a], True, ["max_cases_invalid"]),
                ("two properties", [a, case(["other/b.js"], prop="P-tenant")], 5, ["cases_mixed_property"]),
                ("a path touched twice", [a, case(["other/b.js", "src/a.js"])], 5, ["cases_paths_overlap:src/a.js"]),
                ("a path that is absent", [case(["src/none.js"])], 5, ["case_path_missing:src/none.js"]),
                ("a path that is a link", [case(["link"])], 5, ["case_path_missing:link"]),
                ("several at once", [a, case(["src/a.js", "x"], prop="Q"), b], 2,
                 ["cases_over_max", "cases_mixed_property", "cases_paths_overlap:src/a.js", "case_path_missing:x"])):
            with self.subTest(name):
                self.assertEqual(reasons(PLANT, cases, max_cases=limit), want)
        self.assertEqual(reasons(PLANT, [a, b], max_cases=2), [])
        self.assertEqual(reasons(dict(PLANT, **{"node_modules/x.js": b"1\n"}), [case(["node_modules/x.js"])]),
                         ["case_path_missing:node_modules/x.js"])
        self.assertEqual(reasons(PLANT, [a], kind="canary"), ["kind_unknown"])

    def test_a_case_of_another_shape(self):
        good = case(["src/a.js"])
        bad = [
            dict(good, extra=1), {k: v for k, v in good.items() if k != "replace"}, "src/a.js",
            dict(good, property=""), dict(good, paths=[]), dict(good, paths="src/a.js"),
            dict(good, paths=["src/a.js", "src/a.js"]), dict(good, identifiers=[""]), dict(good, identifiers=["x", "x"]),
            dict(good, identifiers=[7]), dict(good, replace={"other/b.js": b""}), dict(good, replace={"src/a.js": "text"}),
        ]
        for i, one in enumerate(bad):
            with self.subTest(i):
                self.assertEqual(reasons(PLANT, [good, one]), ["case_invalid:1"])
        self.assertEqual(reasons(PLANT, [bad[0], good, bad[3]]), ["case_invalid:0", "case_invalid:2"])
        self.assertEqual(reasons(PLANT, {"0": good}), ["case_invalid:0"])
        self.assertEqual(reasons(PLANT, [bad[0]], kind="clean"), ["case_invalid:0"])

    def test_an_identifier_that_cannot_be_removed_gives_no_snapshot(self):
        files = {"a.txt": b"XYQ\n", "b.txt": b"x\n", "to": ("120000", b"docs/FND-7.md"), "docs/FND-9.md": b"n\n"}
        for name, ids, want in (
                ("the replacement makes one", ["XY", "DQ"], ["sanitize_incomplete:a.txt"]),
                ("in a file's path", ["FND-9"], ["identifier_in_path:docs/FND-9.md"]),
                ("in a link's target", ["FND-7"], ["identifier_in_path:to"]),
                ("part of the placeholder", ["DACT"], ["identifier_invalid"]),
                ("the placeholder", ["REDACTED"], ["identifier_invalid"])):
            with self.subTest(name):
                self.assertEqual(reasons(files, [case(["b.txt"], ids)]), want)


class Write(unittest.TestCase):
    """``write`` and ``check``: the short-lived directory holds exactly the document's files and links."""

    def setUp(self) -> None:
        self.base = writable_base("t-snapw-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.dest = os.path.join(self.base, "snap")
        self.snap = make(dict(KEPT, **LEAKS), target=TARGET)

    def refused(self, document, content=None) -> list:
        with self.assertRaises(SM.SnapshotError) as ctx:
            SM.write(document, self.dest, content or self.snap.files.get)
        self.assertFalse(os.path.lexists(self.dest))
        return ctx.exception.reasons

    def doc(self, **over) -> dict:
        """The document with ``over`` and the id of that content: only the rule under test is broken."""
        d = dict(json.loads(json.dumps(self.snap.document)), **over)
        try:
            d["snapshot_id"] = SM.snapshot_id(d["files"], d["links"], d["exec"])
        except (TypeError, ValueError):
            pass
        return d

    def test_it_writes_the_files_the_links_and_the_execute_bits(self):
        SM.write(self.snap.document, self.dest, self.snap.files.get)
        want = {p: content(v) for p, v in KEPT.items()}
        want["latest"] = ("link", "src/a.js")
        self.assertEqual(on_disk(self.dest), want)
        modes = {p: stat.S_IMODE(os.lstat(os.path.join(self.dest, p)).st_mode) for p in self.snap.files}
        self.assertEqual({p for p, m in modes.items() if m == 0o755}, {"src/run.sh"})
        self.assertEqual({m for p, m in modes.items() if p != "src/run.sh"}, {0o644})

    def test_a_tree_that_is_not_the_documents_is_refused_and_nothing_is_left(self):
        files = dict(self.snap.files)
        self.assertEqual(self.refused(self.snap.document, dict(files, **{"src/a.js": b"const a = 2;\n"}).get),
                         ["hash_mismatch:src/a.js"])
        del files["docs/readme.md"]
        files["hidden.txt"] += b" "
        self.assertEqual(self.refused(self.snap.document, files.get),
                         ["file_missing:docs/readme.md", "hash_mismatch:hidden.txt"])
        self.assertEqual(self.refused(self.snap.document, lambda path: "text"), sorted(
            "file_missing:%s" % p for p in self.snap.files))

    def test_an_existing_destination_is_refused_and_kept(self):
        os.makedirs(self.dest)
        with self.assertRaises(SM.SnapshotError) as ctx:
            SM.write(self.snap.document, self.dest, self.snap.files.get)
        self.assertEqual((ctx.exception.reasons, os.listdir(self.dest)), (["dest_exists"], []))

    def test_a_document_with_another_id_is_refused(self):
        doc = json.loads(json.dumps(self.snap.document))
        doc["files"]["src/extra.js"] = sha(b"x")
        self.assertEqual(self.refused(doc, dict(self.snap.files, **{"src/extra.js": b"x"}).get), ["id_mismatch"])
        doc = dict(self.snap.document, exec=[])
        self.assertEqual(self.refused(doc), ["id_mismatch"])
        doc = dict(self.snap.document, links={"latest": "src/run.sh"})
        self.assertEqual(self.refused(doc), ["id_mismatch"])

    def test_a_document_of_another_shape_is_refused(self):
        files, h = self.snap.document["files"], sha(b"x")
        bad = {
            "not an object": [self.snap.document],
            "none": None,
            "a key more": dict(self.snap.document, kind="clean"),
            "a key less": {k: v for k, v in self.snap.document.items() if k != "links"},
            "another schema": dict(self.snap.document, schema="snowball-snapshot/2"),
            "a hash that is none": self.doc(files=dict(files, **{"src/a.js": "zz"})),
            "an upper case hash": self.doc(files=dict(files, **{"src/a.js": files["src/a.js"].upper()})),
            "a path leaving the directory": self.doc(files=dict(files, **{"../out.txt": h})),
            "a path leaving it deeper": self.doc(files=dict(files, **{"src/../../out.txt": h})),
            "an absolute path": self.doc(files=dict(files, **{"/tmp/out.txt": h})),
            "an empty component": self.doc(files=dict(files, **{"src//x": h})),
            "a dot component": self.doc(files=dict(files, **{"./x": h})),
            "a link's path leaving": self.doc(links={"../l": "x"}),
            "a link with no target": self.doc(links={"l": ""}),
            "a link that is a file too": self.doc(links={"src/a.js": "x"}),
            "a file under a file": self.doc(files=dict(files, **{"src/a.js/x": h})),
            "a file under a link": self.doc(files=dict(files, **{"latest/x": h})),
            "exec of no file": self.doc(exec=["src/none.sh"]),
            "exec twice": self.doc(exec=["src/run.sh", "src/run.sh"]),
            "exec unsorted": self.doc(exec=["src/run.sh", "src/a.js"]),
            "exec not a list": self.doc(exec={"src/run.sh": True}),
        }
        for name, doc in bad.items():
            with self.subTest(name):
                self.assertEqual(self.refused(doc, lambda path: b"x"), ["document_invalid"])
        self.assertEqual(os.listdir(self.base), [])        # nothing was written beside the destination either


class Cek(unittest.TestCase):
    """``loop.cek.assemble`` (the job ``çek``): the commit's clean snapshot document is in ``pulled``."""

    setUp, assemble, refused = TC.Brain.setUp, TC.Brain.assemble, TC.Brain.refused

    def plant_leaks(self) -> None:
        for path, data in (("pkg/CLAUDE.md", b"instructions\n"), ("pkg/node_modules/dep/index.js", b"1\n"),
                           (".brain/ledger.jsonl", b"{}\n"), ("x/secret.txt", b"s\n")):
            os.makedirs(os.path.dirname(os.path.join(self.src, path)), exist_ok=True)
            with open(os.path.join(self.src, path), "wb") as fh:
                fh.write(data)

    def test_pulled_carries_the_snapshot_of_the_commit_without_the_leaks(self):
        kept = on_disk(self.src)
        self.plant_leaks()
        self.assemble(summary={"targets": [dict(TC.SUMMARY["targets"][0], excluded_paths=["x"])]})
        got = P.read(self.out)
        self.assertEqual(got.snapshot, {"schema": "snowball-snapshot/1", "exec": [], "links": {},
                                        "files": {p: sha(d) for p, d in sorted(kept.items())},
                                        "snapshot_id": id_by_hand(kept, {}, [])})
        # the tree itself is carried whole: the snapshot is made beside it, not from a narrowed tree
        with open(got.tree_tar, "rb") as fh:
            names = {n[0] for n in TC.names(fh.read())}
        self.assertTrue({"pkg/CLAUDE.md", ".brain/ledger.jsonl", "x/secret.txt"} <= names)

    def test_the_operators_paths_are_the_served_entrys(self):
        self.plant_leaks()
        self.assemble()                                      # the entry has no excluded_paths: x/ is kept
        self.assertIn("x/secret.txt", P.read(self.out).snapshot["files"])

    def test_an_entry_the_profile_refuses_gives_no_artifact(self):
        summary = {"targets": [dict(TC.SUMMARY["targets"][0], excluded_paths="x")]}
        self.assertEqual(self.refused(summary=summary), ["snapshot:target_invalid"])


# The organ of these tests: it writes, to the path it is given second, every file under the directory given first.
LISTER = (b"import os, sys\n"
          b"found = []\n"
          b"for d, dirs, names in os.walk(sys.argv[1]):\n"
          b"    found += [os.path.relpath(os.path.join(d, n), sys.argv[1]) for n in dirs + names\n"
          b"              if not os.path.isdir(os.path.join(d, n)) or os.path.islink(os.path.join(d, n))]\n"
          b"with open(sys.argv[2], 'w') as fh:\n"
          b"    fh.write('\\n'.join(sorted(found)))\n")
ORGAN = {"entry": ["python3", "/in/adapters/list/main.py", "/work", "/out/listing.txt"],
         "files": {"adapters/list/main.py": LISTER}}
BRAIN_ORGAN = {"adapters/list/main.py": LISTER,
               "organs/lister.json": json.dumps({"entry": ORGAN["entry"], "files": ["adapters/list/main.py"]}).encode()}


class LivePath(LK.Base):
    """The ``kos`` job (``loop.job.run("kos", ...)``): the snapshot is written out and the organ runs on it."""

    run_kos, results, one = LK.KosJob.run_kos, LK.KosJob.results, LK.KosJob.one
    plant_leaks = Cek.plant_leaks

    def listing(self, runner) -> list:
        (kept,) = [o for o in runner.outs if "listing.txt" in o]
        return kept["listing.txt"].decode().split("\n")

    def test_from_cek_the_organ_in_kos_reads_the_snapshot_and_no_leak(self):
        kept = on_disk(self.src)
        self.plant_leaks()
        brain, brain_commit = S.store(dict(TC.brain_files(), **BRAIN_ORGAN))
        objects, commit = TC.target_objects(self.src)
        os.makedirs(os.path.dirname(self.pulled))
        P.write_served(os.path.dirname(self.pulled), ["t1"])
        summary = {"targets": [dict(TC.SUMMARY["targets"][0], excluded_paths=["x"])]}
        C.assemble(brain.__getitem__, brain_commit, json.dumps(summary).encode(), TC.POLICY, "t1",
                   objects.__getitem__, commit, LK.HEADS["brain/state"], LK.state_files(), None, self.pulled)
        runner = Capture()
        out = self.run_kos(runner)
        line = self.one(out)
        self.assertEqual((out["ok"], line["done"]), (True, ["D3"]))
        self.assertEqual(line["snapshot"], {"snapshot_id": id_by_hand(kept, {}, []), "files": len(kept), "links": 0})
        self.assertEqual((line["index"]["organs"]["lister"]["called"], line["index"]["organs"]["lister"]["exit"]),
                         (True, 0))
        # what the organ found under /work: the snapshot's files, no leak, no installed or staged directory
        self.assertEqual(self.listing(runner), sorted(kept))
        # the base's runs saw the pulled tree's unit as before (its lint ran on the staged worktree)
        self.assertEqual(line["index"]["base"]["verdict"], "verified")

    def refused(self, snapshot) -> tuple:
        shutil.rmtree(self.temp, ignore_errors=True)
        self.write_pulled(accepted={"lister": organs.definition_sha256(ORGAN)}, organs={"lister": ORGAN},
                          snapshot=snapshot)
        runner = Capture()
        out = self.run_kos(runner)
        self.assertEqual((runner.calls, runner.docker.other), ([], []))     # no docker process of any kind
        self.assertFalse(os.path.lexists(self.results()))
        return out["ok"], out["reason"], out["reasons"]

    def test_a_snapshot_that_is_not_the_trees_runs_nothing(self):
        good = LK.snapshot_of(self.src)
        other = dict(good, files=dict(good["files"], **{"pkg/a.js": sha(b"other")}))
        other["snapshot_id"] = SM.snapshot_id(other["files"], other["links"], other["exec"])
        more = dict(good, files=dict(good["files"], **{"pkg/absent.js": sha(b"")}))
        more["snapshot_id"] = SM.snapshot_id(more["files"], more["links"], more["exec"])
        for name, doc, want in (
                ("a file with other bytes", other, ["hash_mismatch:pkg/a.js"]),
                ("a file the tree has not", more, ["file_missing:pkg/absent.js"]),
                ("an id that is not the content's", dict(good, snapshot_id="0" * 64), ["id_mismatch"]),
                ("no document", None, ["document_invalid"]),
                ("another document", {"snapshot_id": good["snapshot_id"]}, ["document_invalid"])):
            with self.subTest(name):
                self.assertEqual(self.refused(doc), (False, "snapshot_refused", want))

    def test_the_trees_own_snapshot_runs(self):
        self.write_pulled(accepted={"lister": organs.definition_sha256(ORGAN)}, organs={"lister": ORGAN})
        runner = Capture()
        line = self.one(self.run_kos(runner))
        self.assertEqual(self.listing(runner), sorted(on_disk(self.src)))
        self.assertEqual(line["snapshot"]["snapshot_id"], LK.snapshot_of(self.src)["snapshot_id"])


class Carried(LK.Base):
    """``loop.pulled``: ``snapshot.json`` is always listed and is JSON; the document is carried, not judged."""

    def test_snapshot_json_is_required_and_read_as_json(self):
        self.write_pulled(snapshot={"any": ["document", 1]})
        self.assertEqual(P.read(self.pulled).snapshot, {"any": ["document", 1]})
        with open(os.path.join(self.pulled, "snapshot.json"), "wb") as fh:
            fh.write(b"{not json")
        manifest = self.manifest()
        manifest["files"]["snapshot.json"] = sha(b"{not json")
        self.set_manifest(manifest)
        self.assertEqual(self.reasons(), ["json_unreadable:snapshot.json"])
        os.remove(os.path.join(self.pulled, "snapshot.json"))
        del manifest["files"]["snapshot.json"]
        self.set_manifest(manifest)
        self.assertEqual(self.reasons(), ["missing:snapshot.json"])

    def test_a_document_json_cannot_write_is_refused_at_the_write(self):
        with self.assertRaises(P.PulledError) as ctx:
            self.write_pulled(snapshot={"files": {b"bytes"}})
        self.assertEqual(ctx.exception.reasons, ["snapshot_invalid"])
        self.assertFalse(os.path.lexists(self.pulled))


class KosOrgans(unittest.TestCase):
    """``runner.kos.results``: organs are given with the directory they read."""

    def test_organs_without_their_tree_are_unusable_input(self):
        base = writable_base("t-snapk-")
        self.addCleanup(shutil.rmtree, base, ignore_errors=True)
        out = os.path.join(base, "out")
        link = os.path.join(base, "link")
        os.symlink(base, link)
        accepted = {"lister": organs.definition_sha256(ORGAN)}
        for name, given in (("no tree", {"accepted": accepted, "definitions": {"lister": ORGAN}, "tree": None}),
                            ("no tree key", {"accepted": accepted, "definitions": {"lister": ORGAN}}),
                            ("a tree that is absent", {"accepted": accepted, "definitions": {"lister": ORGAN},
                                                       "tree": os.path.join(base, "none")}),
                            ("a tree that is a link", {"accepted": accepted, "definitions": {"lister": ORGAN},
                                                       "tree": link})):
            with self.subTest(name):
                runner = Capture()
                with self.assertRaises(K.KosError):
                    K.results(LK.recipe(), base, {"operating": LK.operating()}, {"cmd": ["false"]}, {}, out,
                              runner=runner, organs=given)
                self.assertEqual((runner.calls, runner.docker.other), ([], []))
                self.assertFalse(os.path.lexists(out))


if __name__ == "__main__":
    unittest.main()
