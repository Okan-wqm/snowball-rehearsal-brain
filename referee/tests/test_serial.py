"""D5's criterion 8 (asama-0/08), tohum/07's serial merges: ``ledger.serial.unfinished`` on ``brain/state`` ledgers
written by ``ledger.append`` (the cycle's writer) with rows of ``ledger.schema``.

- no merge (a genesis without a ready candidate): nothing unfinished; a reject is no merge;
- a gate merge and a planted drill merge are unfinished until a later revert names them; order is file order;
- a ledger that is not a chain, or holds a row of no known type or of a wrong shape, answers nothing (``Unusable``);
- a revert of no earlier merge (also one written before its merge) and the same SHA merged twice answer nothing;
- the reasons are all collected.
"""

from __future__ import annotations

import os
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ledger import serial as SE  # noqa: E402
from test_revert_drill import ledger_with, plant, reverted, row  # noqa: E402

M1, M2, M3 = "1" * 40, "2" * 40, "3" * 40
START = row("s", "events", "cycle_start", {"cycle_id": "7"})


def merge(row_id: str, sha: str) -> dict:
    return row(row_id, "events", "decision", {"decision": "merge", "candidate": row_id, "path": "pkg/a.js",
                                              "pull": 1, "head_sha": "f" * 40, "merge_sha": sha})


def reject(row_id: str) -> dict:
    return row(row_id, "events", "decision", {"decision": "reject", "candidate": row_id, "reasons": ["tests_red"]},
               "test_regression")


class Unfinished(unittest.TestCase):
    def unfinished(self, *rows: dict) -> list[str]:
        return SE.unfinished(ledger_with(list(rows)))

    def refused(self, ledger: bytes) -> list[str]:
        with self.assertRaises(SE.Unusable) as ctx:
            SE.unfinished(ledger)
        return ctx.exception.reasons

    def test_no_merge_nothing_unfinished(self):
        self.assertEqual(self.unfinished(START), [])
        self.assertEqual(self.unfinished(START, reject("c1")), [])

    def test_a_merge_is_unfinished_until_its_revert(self):
        self.assertEqual(self.unfinished(START, merge("c1", M1)), [M1])
        self.assertEqual(self.unfinished(START, merge("c1", M1), reverted("r1", M1, "test_regression")), [])

    def test_a_planted_merge_counts(self):
        self.assertEqual(self.unfinished(START, plant("p1", "i1", M2)), [M2])
        self.assertEqual(self.unfinished(START, plant("p1", "i1", M2), reverted("r1", M2, "impact_miss")), [])

    def test_only_the_named_merge_finishes_and_order_is_file_order(self):
        rows = (START, merge("c2", M2), plant("p1", "i1", M3), merge("c1", M1), reverted("r1", M3, "unknown"))
        self.assertEqual(self.unfinished(*rows), [M2, M1])

    def test_a_ledger_not_of_the_schema_answers_nothing(self):
        for bad, fragment in ((b"{}\n", "not a valid chain"),
                              (ledger_with([row("x", "events", "merged", {"merge_sha": M1})]), "unknown_row_type"),
                              (ledger_with([row("x", "events", "revert", {"merge_sha": "1"}, "unknown")]),
                               "not 40 lowercase hex"),
                              (ledger_with([row("x", "events", "revert", {"merge_sha": M1})]), "cause: missing")):
            with self.subTest(fragment=fragment):
                reasons = self.refused(bad)
                self.assertTrue(any(fragment in r for r in reasons), reasons)

    def test_a_revert_before_or_without_its_merge(self):
        self.assertEqual(self.refused(ledger_with([START, reverted("r1", M1, "unknown")])),
                         ["finish_without_merge:%s" % M1])
        self.assertEqual(self.refused(ledger_with([START, reverted("r1", M1, "unknown"), merge("c1", M1)])),
                         ["finish_without_merge:%s" % M1])

    def test_merged_twice_and_all_reasons_together(self):
        self.assertEqual(self.refused(ledger_with([merge("c1", M1), plant("p1", "i1", M1)])), ["merged_twice:%s" % M1])
        self.assertEqual(self.refused(ledger_with([reverted("r2", M2, "unknown"), merge("c1", M1), merge("c3", M1)])),
                         ["finish_without_merge:%s" % M2, "merged_twice:%s" % M1])


if __name__ == "__main__":
    unittest.main()
