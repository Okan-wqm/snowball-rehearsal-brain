"""tohum/13 "Zincir kırığı" (E637): ``loop.integration``, ``brain/integration``'s head against the commit the
ledger names, on ledgers written by ``ledger.append`` and commit objects in git's own format (``git_store``).

- ``named``: ``ledger.serial.integration_tip``'s row; a ledger that names none is ``integration_unnamed``, an
  unreadable one is refused with ``ledger.serial``'s reasons;
- a ``cut`` or ``merge`` row: the head is the named commit or ``head_not_named``; no object is read;
- a ``revert`` row: the head is the merge, on the reverted merge ``M``, of a commit whose one parent is ``M``,
  the revert commit and the head both holding the tree of ``M``'s first parent; each other shape has its one
  reason, the first failing rule's; an object the source lacks or cannot parse is ``integration:<reason>``.
"""

from __future__ import annotations

import os
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import git_store as S  # noqa: E402
from loop import integration as IG  # noqa: E402
from loop.pulled import PulledError  # noqa: E402
from test_revert_drill import ledger_with, reverted, row  # noqa: E402
from test_serial import START, cut, merge  # noqa: E402


class History:
    """A base, a candidate, their merge ``M``, the revert commit ``R`` on ``M`` and the head, ``R``'s merge."""

    def __init__(self):
        self.objects: dict = {}
        self.before = S.store_tree({"a": b"1\n"}, self.objects)
        self.after = S.store_tree({"a": b"2\n"}, self.objects)
        self.base = S.commit(self.objects, self.before, b"base\n")
        self.candidate = S.commit(self.objects, self.after, b"candidate\n", (self.base,))
        self.merge = S.commit(self.objects, self.after, b"merge\n", (self.base, self.candidate))
        self.revert = S.commit(self.objects, self.before, b"revert\n", (self.merge,))
        self.head = S.commit(self.objects, self.before, b"merge of the revert\n", (self.merge, self.revert))
        self.read: list = []

    def commit(self, tree: str, *parents: str) -> str:
        return S.commit(self.objects, tree, b"other\n", parents)

    def source(self, sha: str):
        self.read.append(sha)
        return self.objects[sha]


class Named(unittest.TestCase):
    def test_the_row_of_ledger_serial(self):
        ledger = ledger_with([START, cut("k", "1" * 40), merge("c1", "2" * 40)])
        self.assertEqual(IG.named(ledger), {"row_id": "c1", "kind": "merge", "sha": "2" * 40})

    def test_a_ledger_that_names_none(self):
        with self.assertRaises(PulledError) as ctx:
            IG.named(ledger_with([START]))
        self.assertEqual(ctx.exception.reasons, ["integration_unnamed"])

    def test_an_unreadable_ledger_is_refused_with_its_reasons(self):
        with self.assertRaises(PulledError) as ctx:
            IG.named(ledger_with([cut("k", "1" * 40), row("x", "events", "nope", {})]))
        self.assertTrue(ctx.exception.reasons)
        self.assertNotEqual(ctx.exception.reasons, ["integration_unnamed"])


class Head(unittest.TestCase):
    def setUp(self):
        self.h = History()

    def tip(self, kind: str, sha: str) -> dict:
        return {"row_id": "r", "kind": kind, "sha": sha}

    def revert_reasons(self, head: str, merged: str | None = None) -> list[str]:
        return IG.reasons(self.tip("reverted", merged or self.h.merge), head, self.h.source)

    def test_a_cut_merge_or_revert_row_names_the_head_itself(self):
        # a revert row's ``sha`` is its ``head_sha`` (26f:78-79): compared as a merge row's is, no shape judged,
        # so a head with the revert's shape that is not the commit named is refused
        for kind in ("cut", "merge", "revert"):
            with self.subTest(kind=kind):
                self.assertEqual(IG.reasons(self.tip(kind, self.h.merge), self.h.merge, self.h.source), [])
                # the commit after it (the gate's own revert too) is not the commit the row names
                self.assertEqual(IG.reasons(self.tip(kind, self.h.merge), self.h.head, self.h.source),
                                 ["head_not_named"])
                self.assertEqual(IG.reasons(self.tip(kind, self.h.merge), self.h.base), ["head_not_named"])
        # another merge of the same revert commit on the same merge: the shape a row without ``head_sha`` is
        # judged by passes it, the row that names the head does not
        h = self.h
        twin = S.commit(h.objects, h.before, b"another merge of the revert\n", (h.merge, h.revert))
        self.assertEqual(IG.reasons(self.tip("revert", h.head), h.head, h.source), [])
        self.assertEqual(IG.reasons(self.tip("revert", h.head), twin, h.source), ["head_not_named"])
        self.assertEqual(self.h.read, [])  # no object read: the comparison is of the two ids
        self.assertEqual(self.revert_reasons(twin), [])

    def test_the_gates_revert_of_the_named_merge(self):
        self.assertEqual(self.revert_reasons(self.h.head), [])

    def test_a_revert_row_does_not_name_the_merge_as_head(self):
        # the row says the merge was reverted: a head still at the merge is not what the ledger records
        self.assertEqual(self.revert_reasons(self.h.merge), ["revert_head_parents"])

    def test_the_heads_parents(self):
        h = self.h
        for name, head in (("the revert commit pushed without its pull request", h.revert),
                           ("the parents the other way round", h.commit(h.before, h.revert, h.merge)),
                           ("a third parent", h.commit(h.before, h.merge, h.revert, h.base)),
                           ("a commit after the revert's merge", h.commit(h.before, h.head)),
                           ("on another merge", h.commit(h.before, h.base, h.revert))):
            with self.subTest(name):
                self.assertEqual(self.revert_reasons(head), ["revert_head_parents"])

    def test_the_reverted_commit_is_a_merge(self):
        h = self.h
        revert = h.commit(h.before, h.candidate)
        head = h.commit(h.before, h.candidate, revert)
        self.assertEqual(self.revert_reasons(head, h.candidate), ["reverted_not_merge"])

    def test_the_second_parent_is_a_commit_on_the_merge(self):
        h = self.h
        for name, second in (("another line's commit", h.candidate), ("the merge's base", h.base),
                             ("two commits on the merge", h.commit(h.before, h.revert)),
                             ("a merge itself", h.commit(h.before, h.merge, h.base))):
            with self.subTest(name):
                self.assertEqual(self.revert_reasons(h.commit(h.before, h.merge, second)), ["revert_commit_parents"])

    def test_the_tree_is_the_one_before_the_merge(self):
        h = self.h
        other = S.store_tree({"a": b"3\n"}, h.objects)
        for name, revert_tree, head_tree in (("the head keeps the merge's content", h.before, h.after),
                                             ("the revert commit does", h.after, h.before),
                                             ("both do", h.after, h.after),
                                             ("a third content", other, other),
                                             ("the head adds to the revert", h.before, other)):
            with self.subTest(name):
                revert = h.commit(revert_tree, h.merge)
                self.assertEqual(self.revert_reasons(h.commit(head_tree, h.merge, revert)), ["revert_head_tree"])

    def test_an_object_the_history_lacks_or_cannot_parse(self):
        h = self.h
        for name, sha in (("the head", h.head), ("the merge", h.merge), ("the revert commit", h.revert),
                          ("the merge's first parent", h.base)):
            with self.subTest(name):
                kept = h.objects.pop(sha)
                self.assertEqual(self.revert_reasons(h.head), ["integration:object_missing:%s" % sha])
                h.objects[sha] = kept
        self.assertEqual(self.revert_reasons(h.before), ["integration:object_mismatch:%s" % h.before])  # a tree
        self.assertEqual(self.revert_reasons(h.head), [])


if __name__ == "__main__":
    unittest.main()
