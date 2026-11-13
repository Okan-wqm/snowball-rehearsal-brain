"""Binds the place of the loop's state files to its source, the "Yer" paragraph of
``spec/tohum/26d-semalar-pass-satiri.md``: the operator's ``stage-open`` reads ``.brain/ledger.jsonl``,
``.brain/chain/root.jsonl`` and the last root's Sigstore bundle ``.brain/chain/<kök>.sigstore.json`` as regular files
of the same ``brain/state`` commit, ``<kök>`` being the ``root`` of the last root row. The paths are read from the
page; a page whose paragraph is missing, written twice, or names no bundle fails here rather than being guessed at.

What is held against the page: the two state commits the loop writes, the activation's orphan commit
(``ledger.cycle.plan``'s files through ``target.write.Writer.open_orphan``) and an ordinary cycle's commit on top of
it (``ledger.cycle.commit`` through ``ledger.append.TargetState``), on the in-process GitHub of ``referee/tests``.
In each: every path of the page is a file of the commit, the bundle found by the root the page's own root file
names; no file of the commit is outside the page's directory; and the data the signer was handed hashes to that
root (the page's "Kök" paragraph: the hash of the record's data is the root itself). The signer is
``ledger.anchor.FakeSigner``: the bundle's bytes are its stand-in's, so nothing here says a real Sigstore bundle
verifies (``referee/tests/test_sign.py`` and ``test_rekor.py`` hold the real signer's and the next D1's rules).
Run from the brain's root (the spec is not in ``referee/``)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))
sys.path.insert(0, os.path.join(ROOT, "referee", "tests"))

from ledger import append as AP  # noqa: E402
from ledger import cycle as CY  # noqa: E402
from target import write as W  # noqa: E402
from fake_github import FakeGitHub  # noqa: E402
from test_cycle import IMPORTS, facts, signer, start  # noqa: E402

PAGE = os.path.join(ROOT, "spec", "tohum", "26d-semalar-pass-satiri.md")
PARAGRAPH = r"\*\*Yer\.\*\* (.*?)(?= \*\*[^*]+\*\*|$)"
ROOT_MARK = "<kök>"
ROOTS_NAME = "/chain/root.jsonl"
STATE = "brain/state"


def page_paths(page: str = PAGE) -> list:
    """The file paths the page's "Yer" paragraph names under a dot directory, in its order, each once."""
    with open(page, encoding="utf-8") as fh:
        text = " ".join(fh.read().split())
    paragraphs = re.findall(PARAGRAPH, text)
    if len(paragraphs) != 1:
        raise AssertionError("26d has %d Yer paragraphs, expected 1" % len(paragraphs))
    paths = list(dict.fromkeys(re.findall(r"`(\.[A-Za-z0-9_-]+/[^`]+)`", paragraphs[0])))
    if sum(ROOT_MARK in p for p in paths) != 1 or sum(p.endswith(ROOTS_NAME) for p in paths) != 1:
        raise AssertionError("26d's Yer paragraph does not name one root file and one bundle of its root: %r" % paths)
    return paths


def state_commits() -> list:
    """``(label, files, payloads)`` of the two commits: ``files`` maps every path of the commit to its bytes,
    ``payloads`` is what the cycle's signer was handed."""
    gh = FakeGitHub("acme/toy")
    gh.refs["main"] = gh.seed_commit("t0")
    writer = W.Writer("acme/toy", gh)

    def files() -> dict:
        return {path: gh.read_file(STATE, path) for path in gh.trees[gh.commits[gh.refs[STATE]]["tree"]]}

    first = signer("uuid-1")
    opened = CY.plan(b"", b"", b"", b"", None, [start("s1", "4100")], IMPORTS, facts(), first, "r1")
    head = writer.open_orphan(STATE, opened["files"], "genesis")
    out = [("activation", files(), first.payloads)]
    second = signer("uuid-2")
    ledger, roots, status = (opened["files"][p] for p in (CY.anchor.LEDGER_PATH, CY.anchor.ROOTS_PATH,
                                                          CY.block.STATUS_PATH))
    CY.commit(AP.TargetState(writer, head), "cycle 4101", ledger, ledger, roots, roots, status, [start("s2", "4101")],
              IMPORTS, facts(row_id="st2"), second, "r2")
    return out + [("cycle", files(), second.payloads)]


def last_root(paths: list, files: dict) -> str:
    """The ``root`` of the last row of the page's root file in ``files``; ``""`` when the file is not there."""
    data = files.get(next(p for p in paths if p.endswith(ROOTS_NAME)))
    return json.loads(data.splitlines()[-1])["root"] if data else ""


def not_held(paths: list, files: dict) -> list:
    """The page's paths that are no file of the commit, and the commit's files outside the directory the page's
    paths are in."""
    root = last_root(paths, files)
    missing = [p for p in paths if p.replace(ROOT_MARK, root) not in files]
    directory = {p.split("/", 1)[0] + "/" for p in paths}
    return missing + sorted(f for f in files if not any(f.startswith(d) for d in directory))


class StateFilesAreWhereThePageReadsThem(unittest.TestCase):
    def test_the_page_names_the_three_files(self):
        self.assertEqual(len(page_paths()), 3)

    def test_both_state_commits_hold_every_path_of_the_page(self):
        paths = page_paths()
        commits = state_commits()
        self.assertEqual([label for label, _, _ in commits], ["activation", "cycle"])
        for label, files, _ in commits:
            with self.subTest(label):
                self.assertEqual(not_held(paths, files), [])
                self.assertRegex(last_root(paths, files), r"\A[0-9a-f]{64}\Z")
        # the cycle's root is a new one, and the activation's bundle stays in the commit beside it
        (_, opened, _), (_, cycle, _) = commits
        self.assertNotEqual(last_root(paths, opened), last_root(paths, cycle))
        bundle = next(p for p in paths if ROOT_MARK in p)
        self.assertIn(bundle.replace(ROOT_MARK, last_root(paths, opened)), cycle)

    def test_the_signed_data_hashes_to_the_root_the_root_file_names(self):
        paths = page_paths()
        for label, files, payloads in state_commits():
            with self.subTest(label):
                self.assertEqual([hashlib.sha256(p).hexdigest() for p in payloads], [last_root(paths, files)])

    def _page(self, text: str) -> str:
        fh = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        self.addCleanup(os.unlink, fh.name)
        with fh:
            fh.write(text)
        return fh.name

    def test_a_page_that_reads_elsewhere_is_seen(self):
        with open(PAGE, encoding="utf-8") as fh:
            text = fh.read()
        _, files, _ = state_commits()[1]
        for old, new, want in (
                ("`.brain/ledger.jsonl`", "`.brain/book.jsonl`", [".brain/book.jsonl"]),
                ("`.brain/chain/<kök>.sigstore.json`", "`.brain/chain/<kök>.bundle`", [".brain/chain/<kök>.bundle"]),
                ("`.brain/chain/<kök>.sigstore.json`", "`.brain/<kök>.sigstore.json`", [".brain/<kök>.sigstore.json"])):
            with self.subTest(new=new):
                self.assertEqual(text.count(old), 1)
                self.assertEqual(not_held(page_paths(self._page(text.replace(old, new))), files), want)
        # another directory: none of its three paths is held, and every file of the commit is outside it
        moved = page_paths(self._page(text.replace("`.brain/", "`.state/")))
        self.assertEqual(moved, [p.replace(".brain/", ".state/") for p in page_paths()])
        self.assertEqual(not_held(moved, files), moved + sorted(files))

    def test_a_commit_that_lacks_a_file_or_holds_one_outside_is_seen(self):
        paths = page_paths()
        _, files, _ = state_commits()[1]
        root = last_root(paths, files)
        for path in paths:
            with self.subTest(path=path):
                held = path.replace(ROOT_MARK, root)
                lacking = {p: d for p, d in files.items() if p != held}
                if path.endswith(ROOTS_NAME):  # without the root file no root is known: its bundle is not found either
                    self.assertEqual(not_held(paths, lacking),
                                     [p for p in paths if p.endswith(ROOTS_NAME) or ROOT_MARK in p])
                else:
                    self.assertEqual(not_held(paths, lacking), [path])
        self.assertEqual(not_held(paths, dict(files, **{"ledger.jsonl": b""})), ["ledger.jsonl"])
        # the bundle of another root is not the last root's
        bundle = next(p for p in paths if ROOT_MARK in p)
        other = {p: d for p, d in files.items() if p != bundle.replace(ROOT_MARK, root)}
        other[bundle.replace(ROOT_MARK, "0" * 64)] = b"{}"
        self.assertEqual(not_held(paths, other), [bundle])

    def test_the_paragraph_is_not_guessed(self):
        with open(PAGE, encoding="utf-8") as fh:
            text = fh.read()
        start_, end = text.index("**Yer.**"), text.index("**Zincirli dosya**")
        for page in (text[:start_] + text[end:], text[:end] + text[start_:end] + text[end:],
                     text.replace("`.brain/chain/<kök>.sigstore.json`", "paketi"),
                     text.replace("`.brain/chain/root.jsonl`", "kök dosyası")):
            with self.assertRaises(AssertionError):
                page_paths(self._page(page))


if __name__ == "__main__":
    unittest.main()
