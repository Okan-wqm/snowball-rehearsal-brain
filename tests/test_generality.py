"""``tests/generality.py``'s rules, each bound by a test below (the rules are listed in its docstring, the one
source), and the check itself on this tree: ``referee/`` holds no name of ``targets/names.json`` and no file that
is not text. The trees are built in a temporary directory with made-up names. Run from the brain's root."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import generality as G  # noqa: E402

NAMES = {"targets": [
    {"repo": "https://example.org/o/Blue_Heron", "commit": "c1",
     "names": [{"name": "Blue_Heron", "from": "repository"}, {"name": "heron-app", "from": "package.json"}]},
    {"repo": "https://example.org/o/second", "commit": "c2", "names": [{"name": "Ünïted", "from": "repository"}]},
]}


class Base(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="test-generality-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.put("targets/names.json", json.dumps(NAMES))
        self.put("referee/clean.py", "x = 1\n")

    def put(self, rel: str, content: str | bytes = "x\n") -> str:
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(content.encode() if isinstance(content, str) else content)
        return rel

    def main(self, *argv: str) -> tuple[int, dict]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = G.main(list(argv))
        return code, json.loads(out.getvalue())


class ThisTree(unittest.TestCase):
    def test_referee_holds_no_listed_name_and_only_text(self):
        names = G.load_names(os.path.join(ROOT, G.NAMES))
        self.assertTrue(names)  # an empty list would make the next line say nothing
        answer = G.check(ROOT)
        self.assertEqual((answer["reasons"], answer["why"], answer["ok"]), ([], {}, True))
        self.assertGreater(answer["files"], 100)  # the walk found referee/


class Names(Base):
    def test_a_name_in_a_files_text_or_path(self):
        self.put("referee/tests/a.py", 'URL = "https://example.org/o/Blue_Heron"\n')
        self.put("referee/tests/fixtures/b.json", '{"pkg": "@x/HERON-APP", "other": "blue_heron"}\n')  # casefolded
        self.put("referee/gate/heron-app/c.txt", "nothing here\n")  # the path alone
        self.put("referee/d.md", "the ünïted one\n")  # the second target's name
        self.put("referee/e.py", "blue heron, heron_app, Blue-Heron\n")  # no name as written
        self.put("docs/f.md", "Blue_Heron\n")  # outside referee/
        answer = G.check(self.root)
        self.assertEqual(answer, {
            "ok": False, "files": 6,
            "reasons": ["target_name_in_referee:referee/d.md", "target_name_in_referee:referee/gate/heron-app/c.txt",
                        "target_name_in_referee:referee/tests/a.py",
                        "target_name_in_referee:referee/tests/fixtures/b.json"],
            "why": {"referee/d.md": ["targets[1].names[0]"],
                    "referee/gate/heron-app/c.txt": ["targets[0].names[1]"],
                    "referee/tests/a.py": ["targets[0].names[0]"],
                    "referee/tests/fixtures/b.json": ["targets[0].names[0]", "targets[0].names[1]"]},
        })

    def test_a_clean_tree_and_an_empty_list(self):
        self.assertEqual(G.check(self.root), {"ok": True, "files": 1, "reasons": [], "why": {}})
        self.put("referee/a.py", "Blue_Heron\n")
        self.put("targets/names.json", json.dumps({"targets": []}))
        self.assertEqual(G.check(self.root), {"ok": True, "files": 2, "reasons": [], "why": {}})

    def test_files_not_read(self):
        self.put("referee/gate/__pycache__/a.cpython-312.pyc", b"\x00\xffBlue_Heron")
        self.put("outside.txt", "Blue_Heron\n")
        os.symlink(os.path.join(self.root, "outside.txt"), os.path.join(self.root, "referee", "link.txt"))
        os.symlink(os.path.join(self.root, "targets"), os.path.join(self.root, "referee", "linked"))
        self.assertEqual(G.files(self.root), ["referee/clean.py"])
        self.assertEqual(G.check(self.root), {"ok": True, "files": 1, "reasons": [], "why": {}})


class Text(Base):
    def test_what_is_text(self):
        for data in (b"", b"a\tb\r\nc\n", "ğ ü ∑ 𝄞\n".encode(), b"{\"a\": \"\\u0000\"}\n"):
            with self.subTest(data=data):
                self.assertEqual(G.text(data), data.decode())
        for data in (b"\xff", b"caf\xe9\n", b"a\x00b", b"a\x1bb", b"a\x0cb", b"a\x7fb", b"\xc0\x80", b"\xed\xa0\x80",
                     "a".encode("utf-16")):
            with self.subTest(data=data):
                self.assertIsNone(G.text(data))

    def test_a_file_that_is_not_text_is_named_and_only_its_path_is_searched(self):
        self.put("referee/a.py", "heron-app\n")
        self.put("referee/tests/fixtures/objects.batch", b"tree 3\x00\x9f\xa1Blue_Heron\n")
        self.put("referee/tests/nul.txt", b"Blue_Heron\x00\n")
        self.put("referee/tests/fixtures/blue_heron.batch", b"\xff")
        self.assertEqual(G.check(self.root), {
            "ok": False, "files": 5,
            "reasons": ["referee_file_not_text:referee/tests/fixtures/blue_heron.batch",
                        "referee_file_not_text:referee/tests/fixtures/objects.batch",
                        "referee_file_not_text:referee/tests/nul.txt",
                        "target_name_in_referee:referee/a.py",
                        "target_name_in_referee:referee/tests/fixtures/blue_heron.batch"],
            "why": {"referee/a.py": ["targets[0].names[1]"],
                    "referee/tests/fixtures/blue_heron.batch": ["targets[0].names[0]"]},
        })


class NamesFile(Base):
    def test_a_list_that_cannot_be_used(self):
        entry = NAMES["targets"][0]
        for doc, reason in (
                ("{", "names_unreadable: JSONDecodeError"), (b"\xff", "names_unreadable: UnicodeDecodeError"),
                ("[" * 100000, "names_unreadable: RecursionError"),
                ("[]", "names_invalid: top"), ("{}", "names_invalid: top"),
                ({"targets": {}}, "names_invalid: top"), ({"targets": [], "x": 1}, "names_invalid: top"),
                ({"targets": [[]]}, "names_invalid: targets[0]"),
                ({"targets": [entry, dict(entry, extra=1)]}, "names_invalid: targets[1]"),
                ({"targets": [{"repo": "r", "names": []}]}, "names_invalid: targets[0]"),
                ({"targets": [dict(entry, repo="")]}, "names_invalid: targets[0]"),
                ({"targets": [dict(entry, commit=7)]}, "names_invalid: targets[0]"),
                ({"targets": [dict(entry, names={})]}, "names_invalid: targets[0]"),
                ({"targets": [dict(entry, names=["a"])]}, "names_invalid: targets[0].names[0]"),
                ({"targets": [dict(entry, names=[{"name": "a"}])]}, "names_invalid: targets[0].names[0]"),
                ({"targets": [dict(entry, names=[{"name": "a", "from": "b"}, {"name": "", "from": "b"}])]},
                 "names_invalid: targets[0].names[1]"),
                ({"targets": [dict(entry, names=[{"name": "a", "from": None}])]}, "names_invalid: targets[0].names[0]"),
                ({"targets": [dict(entry, names=[{"name": "a", "from": "b", "c": "d"}])]},
                 "names_invalid: targets[0].names[0]")):
            with self.subTest(reason=reason, doc=str(doc)[:40]):
                self.put("targets/names.json", doc if isinstance(doc, (str, bytes)) else json.dumps(doc))
                with self.assertRaises(G.Unreadable) as ctx:
                    G.check(self.root)
                self.assertEqual(str(ctx.exception), reason)
        os.remove(os.path.join(self.root, "targets", "names.json"))
        with self.assertRaises(G.Unreadable) as ctx:
            G.check(self.root)
        self.assertEqual(str(ctx.exception), "names_unreadable: FileNotFoundError")

    def test_labels_count_across_targets(self):
        self.assertEqual(G.load_names(os.path.join(self.root, "targets", "names.json")),
                         [("targets[0].names[0]", "Blue_Heron"), ("targets[0].names[1]", "heron-app"),
                          ("targets[1].names[0]", "Ünïted")])

    def test_no_referee_directory(self):
        shutil.rmtree(os.path.join(self.root, "referee"))
        for make in (lambda: None, lambda: self.put("referee"),
                     lambda: (os.remove(os.path.join(self.root, "referee")),
                              os.symlink(os.path.join(self.root, "targets"), os.path.join(self.root, "referee")))):
            make()
            with self.assertRaises(G.Unreadable) as ctx:
                G.check(self.root)
            self.assertEqual(str(ctx.exception), "referee_unreadable")


class Derive(Base):
    def checkout(self, files: dict) -> str:
        for rel, content in files.items():
            self.put("checkout/" + rel, content)
        os.makedirs(os.path.join(self.root, "checkout"), exist_ok=True)
        return os.path.join(self.root, "checkout")

    def test_the_repository_and_the_root_manifests(self):
        top = self.checkout({
            "package.json": '{"name": "heron-app", "workspaces": ["apps/*"]}',
            "Cargo.toml": '[package]\nname = "heron_core"\nversion = "1.0.0"\n',
            "pyproject.toml": '[project]\nname = "heron-py"\n[tool.x]\nname = "not-this"\n',
            "apps/a/package.json": '{"name": "@heron/a"}',  # not at the root
        })
        self.assertEqual(G.derive(top, "https://example.org/o/Blue_Heron.git", "c1"), {
            "repo": "https://example.org/o/Blue_Heron.git", "commit": "c1",
            "names": [{"name": "Blue_Heron", "from": "repository"}, {"name": "heron-app", "from": "package.json"},
                      {"name": "heron_core", "from": "Cargo.toml"}, {"name": "heron-py", "from": "pyproject.toml"}],
        })

    def test_a_name_twice_is_listed_once_and_a_manifest_without_a_name_gives_none(self):
        top = self.checkout({
            "package.json": '{"name": "heron"}',
            "Cargo.toml": '[workspace]\nmembers = ["crates/*"]\n',  # no [package]
            "pyproject.toml": '[project]\nname = "heron"\n',
        })
        self.assertEqual(G.derive(top, "https://example.org/o/heron/", "c1")["names"],
                         [{"name": "heron", "from": "repository"}])
        for manifest in ('{"name": 7}', '{"name": ""}', '{"private": true}', "[]", '"heron-x"'):
            with self.subTest(manifest=manifest):
                top = self.checkout({"package.json": manifest})
                self.assertEqual(G.derive(top, "https://example.org/o/heron", "c1")["names"],
                                 [{"name": "heron", "from": "repository"}])

    def test_no_manifest(self):
        top = self.checkout({})
        for url in ("https://example.org/o/r", "https://example.org/o/r.git", "https://example.org/o/r/",
                    "https://example.org/o/r.git/", "ssh://git@example.org/o/r.git", "/srv/git/r.git"):
            with self.subTest(url=url):
                self.assertEqual(G.derive(top, url, "c1")["names"], [{"name": "r", "from": "repository"}])

    def test_refused(self):
        top = self.checkout({})
        for url in ("", "https://example.org", "https://example.org/", "https://example.org/.git"):
            with self.subTest(url=url):
                with self.assertRaises(G.Unreadable) as ctx:
                    G.derive(top, url, "c1")
                self.assertEqual(str(ctx.exception), "repo_unreadable")
        with self.assertRaises(G.Unreadable) as ctx:
            G.derive(top, "https://example.org/o/r", "")
        self.assertEqual(str(ctx.exception), "commit_unreadable")
        for manifest, content in (("package.json", "{"), ("package.json", b"\xff"), ("Cargo.toml", "[package\n"),
                                  ("pyproject.toml", "name = \n")):
            with self.subTest(manifest=manifest, content=content):
                top = self.checkout({manifest: content})
                with self.assertRaises(G.Unreadable) as ctx:
                    G.derive(top, "https://example.org/o/r", "c1")
                self.assertEqual(str(ctx.exception), "manifest_unreadable: %s" % manifest)
                os.remove(os.path.join(top, manifest))


class Command(Base):
    def test_check_exits(self):
        self.assertEqual(self.main("check", "--root", self.root),
                         (0, {"ok": True, "files": 1, "reasons": [], "why": {}}))
        self.put("referee/a.py", "# blue_heron\n")
        self.assertEqual(self.main("check", "--root", self.root),
                         (1, {"ok": False, "files": 2, "reasons": ["target_name_in_referee:referee/a.py"],
                              "why": {"referee/a.py": ["targets[0].names[0]"]}}))
        self.put("targets/names.json", "{}")
        self.assertEqual(self.main("check", "--root", self.root), (2, {"ok": False, "reason": "names_invalid: top"}))

    def test_names_prints_a_names_file_the_check_reads(self):
        self.put("checkout/package.json", '{"name": "heron-app"}')
        code, doc = self.main("names", os.path.join(self.root, "checkout"), "--repo",
                              "https://example.org/o/Blue_Heron", "--commit", "c1")
        self.assertEqual((code, doc), (0, {"targets": [NAMES["targets"][0]]}))
        self.put("targets/names.json", json.dumps(doc))
        self.put("referee/a.py", "import heron-app\n")
        self.assertEqual(G.check(self.root)["why"], {"referee/a.py": ["targets[0].names[1]"]})
        self.assertEqual(self.main("names", os.path.join(self.root, "checkout"), "--repo", "x:", "--commit", "c1"),
                         (2, {"ok": False, "reason": "repo_unreadable"}))


if __name__ == "__main__":
    unittest.main()
