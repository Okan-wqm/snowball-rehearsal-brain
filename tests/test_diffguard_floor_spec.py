"""Binds the diff-guard's floor to its source, the ``diffguard`` paragraph of
``spec/tohum/29k-vektor-arayuzleri-yol-kurallari.md``: the base names the page lists for ``config``, ``manifest``,
``lockfile`` and ``gitattributes`` each get that reason from ``gate.diffguard``, and test 23's copies of the lists
(``referee/tests/test_diffguard.py`` ``SEED_CONFIG``, ``SEED_LOCKS``) hold the page's names. Each list is found as
the one parenthesis after its reason's name; a page where one is missing or written twice fails here rather than
being guessed at. A name with ``*`` is a shape; it is tried with one sample (``*`` read as ``build``) and is not
compared with the copies. Run from the brain's root (the spec is not in ``referee/``)."""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))
sys.path.insert(0, os.path.join(ROOT, "referee", "tests"))

from test_diffguard import SEED_CONFIG, SEED_LOCKS, edit, reasons  # noqa: E402

PAGE = os.path.join(ROOT, "spec", "tohum", "29k-vektor-arayuzleri-yol-kurallari.md")
LISTS = {"config": r"`config` \(temel adı ([^()]*?); ya da kökteki `\.github/` altında\)",
         "manifest": r"`manifest` \(temel adı ([^()]*?)\)",
         "lockfile": r"`lockfile` \(([^()]*?)\)",
         "gitattributes": r"`gitattributes` \(([^()]*?)\)"}


def floor(page: str = PAGE) -> dict:
    """``{reason: [name, ...]}`` as the page writes them, in its order."""
    with open(page, encoding="utf-8") as fh:
        text = " ".join(fh.read().split())
    found = {}
    for reason, shape in LISTS.items():
        lists = re.findall(shape, text)
        if len(lists) != 1:
            raise AssertionError("29k has %d %s lists, expected 1" % (len(lists), reason))
        names = re.findall(r"`([^`]+)`", lists[0])
        if not names:
            raise AssertionError("29k's %s list names nothing" % reason)
        found[reason] = names
    return found


def not_given(lists: dict) -> list:
    """The ``(reason, name)`` pairs for which the diff-guard does not give exactly ``<reason>:<path>``."""
    missing = []
    for reason, names in lists.items():
        for name in names:
            path = "pkg/" + name.replace("*", "build")
            if reasons(edit(path)) != ["%s:%s" % (reason, path)]:
                missing.append((reason, name))
    return missing


class FloorIsThePages(unittest.TestCase):
    def test_every_name_of_the_page_gets_its_reason(self):
        self.assertEqual(not_given(floor()), [])

    def test_the_copies_hold_the_pages_names(self):
        lists = floor()
        self.assertEqual([n for n in lists["config"] if "*" not in n], list(SEED_CONFIG))
        self.assertEqual(lists["lockfile"], list(SEED_LOCKS))

    def _page(self, text: str) -> str:
        fh = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        self.addCleanup(os.unlink, fh.name)
        with fh:
            fh.write(text)
        return fh.name

    def test_a_name_added_to_the_page_is_seen(self):
        with open(PAGE, encoding="utf-8") as fh:
            text = fh.read()
        for reason, old in (("config", "`biome.json`"), ("manifest", "`package.json`"),
                            ("lockfile", "`pnpm-lock.yaml`"), ("gitattributes", "(`.gitattributes`)")):
            with self.subTest(reason=reason):
                self.assertEqual(text.count(old), 1)
                new = old.replace("`", "`not-a-floor-name.zz`, `", 1)
                self.assertEqual(not_given(floor(self._page(text.replace(old, new)))),
                                 [(reason, "not-a-floor-name.zz")])

    def test_a_name_with_another_reason_is_not_given(self):
        self.assertEqual(not_given({"manifest": ["yarn.lock"], "lockfile": ["yarn.lock"]}), [("manifest", "yarn.lock")])

    def test_lists_not_guessed(self):
        with open(PAGE, encoding="utf-8") as fh:
            text = fh.read()
        start, end = text.index("`manifest` (temel adı"), text.index("`lockfile` (")
        for page in (text[:start] + text[end:], text[:end] + text[start:end] + text[end:],
                     text.replace("`manifest` (temel adı `package.json`)", "`manifest` (temel adı yok)")):
            with self.assertRaises(AssertionError):
                floor(self._page(page))


if __name__ == "__main__":
    unittest.main()
