"""D5's criterion 8 (asama-0/08), tohum/07's serial merges: ``ledger.serial.unfinished`` on ``brain/state`` ledgers
written by ``ledger.append`` (the cycle's writer) with rows of ``ledger.schema``.

- no merge (a genesis without a ready candidate): nothing unfinished; a reject is no merge;
- a gate merge (an ``events``/``merge`` row, tohum/26d; its ``decision`` row is no merge) and a planted drill merge
  are unfinished until a later revert or sentinel end row (green or flaky, tohum/26f) names them; order is file
  order;
- a ledger that is not a chain, or holds a row of no known type or of a wrong shape, answers nothing (``Unusable``);
- a revert or end row of no earlier merge (also one written before its merge), a second finisher of one merge (a
  revert after an end, two ends) and the same SHA merged twice answer nothing;
- the reasons are all collected;
- ``lint_before``: the merge's own cycle's last ratchet base before it; a planted merge's likewise (D8 writes
  its cycle's ratchet base before the plant row); none for another cycle's, a later one, a merge without a cycle start
  or a planted merge whose cycle has none; a SHA no merge row names and an unreadable ledger answer nothing;
- ``observed``: none without an observation row, else the last one's base run hash in file order; an unreadable
  ledger (a row of no known type, an observation without its ``fixable``) answers nothing;
- ``integration_tip`` (tohum/13:56-58): the last row in file order that records a write on ``brain/integration``
  and the commit it names: the cut row's base, a gate merge's and a planted merge's merge commit, a revert row's
  reverted merge; none in a ledger without such a row (a decision, a sentinel end, a ratchet base name none); an
  unreadable ledger answers nothing;
- ``used_ids`` (tohum/26p:76-80): the ids with both a ``decision`` merge row and a ``merge`` row since the last
  genesis row; either row alone, a reject and a planted merge name none; a revert or an end frees no id; a genesis
  row frees every id before it (``last_genesis``, the one function the harness's readers of a run's start read
  too); a genesis, decision or merge row with ``proposed_by`` counts for nothing (a proposed genesis row starts no
  run for any of those readers).
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
    """The gate's merge row (tohum/26d ``kind: merge``)."""
    return row(row_id, "events", "merge", {"candidate": row_id, "path": "pkg/a.js", "pull": 1, "head_sha": "f" * 40,
                                           "merge_sha": sha, "hunk_covered": []})


def decided_merge(row_id: str) -> dict:
    """The decision row a merge row follows (``ledger.events.decided``): not itself a merge."""
    return row(row_id, "events", "decision", {"decision": "merge", "candidate": row_id})


def ended(row_id: str, sha: str, verdict: str = "green") -> dict:
    return row(row_id, "events", "sentinel", {"merge_sha": sha, "verdict": verdict, "red": [],
                                              "flaky": ["a"] if verdict == "flaky" else []})


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
        # tohum/26f: a merge is an events/merge or drill/plant row; a merge's decision row alone is none
        self.assertEqual(self.unfinished(START, decided_merge("c1")), [])
        self.assertEqual(self.unfinished(START, decided_merge("c1"), merge("m1", M1)), [M1])

    def test_a_merge_is_unfinished_until_its_revert(self):
        self.assertEqual(self.unfinished(START, merge("c1", M1)), [M1])
        self.assertEqual(self.unfinished(START, merge("c1", M1), reverted("r1", M1, "test_regression")), [])

    def test_a_green_or_flaky_end_row_finishes_a_merge(self):
        for verdict in ("green", "flaky"):
            with self.subTest(verdict=verdict):
                self.assertEqual(self.unfinished(START, merge("c1", M1), ended("e1", M1, verdict)), [])
                self.assertEqual(self.unfinished(START, plant("p1", "i1", M2), ended("e1", M2, verdict)), [])
                self.assertEqual(self.unfinished(START, merge("c1", M1), ended("e1", M1, verdict), merge("c2", M2)),
                                 [M2])

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

    def test_an_end_row_of_no_merge_or_a_second_finisher(self):
        self.assertEqual(self.refused(ledger_with([START, ended("e1", M1)])), ["finish_without_merge:%s" % M1])
        self.assertEqual(self.refused(ledger_with([START, ended("e1", M1), merge("c1", M1)])),
                         ["finish_without_merge:%s" % M1])
        for second in (reverted("r1", M1, "unknown"), ended("e2", M1, "flaky")):
            with self.subTest(second=second["kind"]):
                self.assertEqual(self.refused(ledger_with([START, merge("c1", M1), ended("e1", M1), second])),
                                 ["finished_twice:%s" % M1])
        self.assertEqual(self.refused(ledger_with([START, merge("c1", M1), reverted("r1", M1, "unknown"),
                                                   ended("e1", M1)])), ["finished_twice:%s" % M1])

    def test_merged_twice_and_all_reasons_together(self):
        self.assertEqual(self.refused(ledger_with([merge("c1", M1), plant("p1", "i1", M1)])), ["merged_twice:%s" % M1])
        self.assertEqual(self.refused(ledger_with([reverted("r2", M2, "unknown"), merge("c1", M1), merge("c3", M1)])),
                         ["finish_without_merge:%s" % M2, "merged_twice:%s" % M1])



def ratchet(row_id: str, counts: dict) -> dict:
    return row(row_id, "events", "ratchet_base", {"base_run_sha256": "e" * 64, "counts": counts})


def start(row_id: str) -> dict:
    return row(row_id, "events", "cycle_start", {"cycle_id": row_id})


class LintBefore(unittest.TestCase):
    """``lint_before``: the ratchet base of the merge's own cycle, else ``None``."""

    def before(self, sha: str, *rows: dict):
        return SE.lint_before(ledger_with(list(rows)), sha)

    def test_the_merges_cycle_ratchet_base(self):
        self.assertEqual(self.before(M1, start("s1"), ratchet("b1", {"eslint": 4}), merge("c1", M1)), {"eslint": 4})
        # the last one before the merge in that cycle; a later cycle's does not count
        rows = (start("s1"), ratchet("b1", {"eslint": 4}), ratchet("b2", {"eslint": 2}), merge("c1", M1),
                start("s2"), ratchet("b3", {"eslint": 9}), merge("c2", M2))
        self.assertEqual((self.before(M1, *rows), self.before(M2, *rows)), ({"eslint": 2}, {"eslint": 9}))

    def test_none_without_its_own_cycles_ratchet_base(self):
        # an earlier cycle's ratchet base is another base; a ratchet base after the merge is not its before
        self.assertIsNone(self.before(M1, start("s1"), ratchet("b1", {"eslint": 4}), start("s2"), merge("c1", M1)))
        self.assertIsNone(self.before(M1, start("s1"), merge("c1", M1), ratchet("b1", {"eslint": 4})))
        self.assertIsNone(self.before(M1, merge("c1", M1)))

    def test_a_planted_merge_reads_its_cycles_ratchet_base(self):
        self.assertEqual(self.before(M2, start("s1"), ratchet("b1", {"eslint": 4}), plant("p1", "i1", M2)),
                         {"eslint": 4})
        self.assertIsNone(self.before(M2, start("s1"), plant("p1", "i1", M2)))
        self.assertIsNone(self.before(M2, start("s1"), ratchet("b1", {"eslint": 4}), start("s2"), plant("p1", "i1", M2)))

    def test_refusals(self):
        for ledger, want in ((ledger_with([START, merge("c1", M1)]), ["not_merged:%s" % M2]),
                             (ledger_with([START, reject("c1")]), ["not_merged:%s" % M2])):
            with self.subTest(want=want), self.assertRaises(SE.Unusable) as ctx:
                SE.lint_before(ledger, M2)
            self.assertEqual(ctx.exception.reasons, want)
        with self.assertRaises(SE.Unusable):
            SE.lint_before(ledger_with([row("x", "events", "nope", {})]), M1)

def observation(row_id: str, sha: str) -> dict:
    return row(row_id, "events", "observation", {"base_run_sha256": sha, "fixable": [
        {"rule_id": "import/order", "path": "src/a.ts", "line": 3, "fix_range": [2, 4]}]})


class Observed(unittest.TestCase):
    """``observed``: the last observation row's base run hash, the one D6 compares with this cycle's."""

    def test_the_last_observation_row(self):
        b1, b2 = "a" * 64, "b" * 64
        self.assertIsNone(SE.observed(ledger_with([START, merge("c1", M1)])))
        self.assertEqual(SE.observed(ledger_with([START, observation("o1", b1)])), b1)
        # the last one in file order, also when an earlier base comes back after another
        self.assertEqual(SE.observed(ledger_with([START, observation("o1", b1), observation("o2", b2)])), b2)
        self.assertEqual(SE.observed(ledger_with([START, observation("o1", b2), merge("c1", M1),
                                                  observation("o2", b1)])), b1)

    def test_an_unreadable_ledger_answers_nothing(self):
        for rows in ([row("x", "events", "nope", {})],
                     [row("o1", "events", "observation", {"base_run_sha256": "a" * 64})]):
            with self.subTest(rows=rows), self.assertRaises(SE.Unusable):
                SE.observed(ledger_with(rows))


def cut(row_id: str, sha: str) -> dict:
    return row(row_id, "events", "integration_cut", {"branch": "brain/integration", "base_sha": sha})


class IntegrationTip(unittest.TestCase):
    """``integration_tip``: which row names ``brain/integration``'s commit (``loop.integration`` judges the head)."""

    def tip(self, *rows: dict) -> dict | None:
        return SE.integration_tip(ledger_with(list(rows)))

    def test_each_naming_row_and_the_commit_it_names(self):
        self.assertEqual(self.tip(START, cut("k", M1)), {"row_id": "k", "kind": "cut", "sha": M1})
        self.assertEqual(self.tip(START, cut("k", M1), merge("c1", M2)), {"row_id": "c1", "kind": "merge", "sha": M2})
        self.assertEqual(self.tip(START, cut("k", M1), plant("p1", "i1", M3)),
                         {"row_id": "p1", "kind": "merge", "sha": M3})
        # a revert row names the merge it reverted, not its own commit (tohum/26f, reports/seed-078)
        self.assertEqual(self.tip(START, cut("k", M1), merge("c1", M2), reverted("r1", M2, "test_regression")),
                         {"row_id": "r1", "kind": "revert", "sha": M2})

    def test_the_last_one_in_file_order(self):
        rows = [START, cut("k", M1), merge("c1", M2), reverted("r1", M2, "test_regression"), merge("c2", M3)]
        self.assertEqual(self.tip(*rows), {"row_id": "c2", "kind": "merge", "sha": M3})
        self.assertEqual(self.tip(*rows[:4])["row_id"], "r1")
        self.assertEqual(self.tip(*rows[:3])["row_id"], "c1")
        # a later cut (another genesis of the target) names the commit again
        self.assertEqual(self.tip(*rows, ended("e", M3), cut("k2", M1)), {"row_id": "k2", "kind": "cut", "sha": M1})

    def test_rows_that_name_none(self):
        self.assertIsNone(self.tip(START))
        self.assertIsNone(self.tip(START, decided_merge("c1"), reject("c2"), observation("o1", "a" * 64)))
        # a sentinel end after a merge writes nothing on the branch: the merge row stays the one
        self.assertEqual(self.tip(START, cut("k", M1), merge("c1", M2), ended("e1", M2), decided_merge("c3"),
                                  reject("c4"))["row_id"], "c1")

    def test_an_unreadable_ledger_answers_nothing(self):
        for ledger in (ledger_with([cut("k", M1), row("x", "events", "nope", {})]), b"not a chain\n",
                       ledger_with([row("k", "events", "integration_cut", {"branch": "brain/integration"})])):
            with self.subTest(ledger=ledger[:40]), self.assertRaises(SE.Unusable):
                SE.integration_tip(ledger)




def merged_rows(cid: str, sha: str, **extra) -> list[dict]:
    """The two rows of ``cid``'s merge as ``ledger.events.decided`` writes them (``c:<id>``, ``m:<id>``)."""
    return [dict(row("c:" + cid, "events", "decision", {"decision": "merge", "candidate": cid}), **extra),
            dict(row("m:" + cid, "events", "merge", {"candidate": cid, "path": "pkg/a.js", "pull": 1,
                                                     "head_sha": "f" * 40, "merge_sha": sha, "hunk_covered": []}),
                 **extra)]


def genesis(row_id: str) -> dict:
    from test_pass_row import genesis_payload  # here: test_pass_row's imports reach this module

    return row(row_id, "events", "genesis", genesis_payload("toy"))


class UsedIds(unittest.TestCase):
    def used(self, *rows: dict) -> set[str]:
        return SE.used_ids(SE.rows(ledger_with(list(rows))))

    def test_an_id_with_both_rows_of_its_merge_is_used(self):
        self.assertEqual(self.used(START), set())
        self.assertEqual(self.used(START, *merged_rows("c1", M1)), {"c1"})
        self.assertEqual(self.used(START, *merged_rows("c1", M1), *merged_rows("c2", M2)), {"c1", "c2"})

    def test_one_row_of_the_two_a_reject_and_a_plant_name_no_id(self):
        decision, merged = merged_rows("c1", M1)
        self.assertEqual(self.used(START, decision), set())
        self.assertEqual(self.used(START, merged), set())
        self.assertEqual(self.used(START, reject("c1"), plant("p1", "i1", M2)), set())
        self.assertEqual(self.used(START, reject("c1"), merged), set())  # a reject decision and a merge row
        # the two rows are one id's: a decision of one id and a merge row of another use neither
        self.assertEqual(self.used(START, decision, merged_rows("c2", M2)[1]), set())

    def test_a_revert_or_an_end_frees_no_id(self):
        self.assertEqual(self.used(START, *merged_rows("c1", M1), reverted("r1", M1, "test_regression")), {"c1"})
        self.assertEqual(self.used(START, *merged_rows("c1", M1), ended("e1", M1)), {"c1"})

    def test_a_genesis_row_frees_the_ids_before_it(self):
        first, again = genesis("g"), genesis("g2")
        self.assertEqual(self.used(first, *merged_rows("c1", M1)), {"c1"})
        self.assertEqual(self.used(first, *merged_rows("c1", M1), ended("e1", M1), again), set())
        second = [dict(r, row_id=r["row_id"] + ":2") for r in merged_rows("c2", M2)]
        self.assertEqual(self.used(first, *merged_rows("c1", M1), ended("e1", M1), again, *second), {"c2"})
        # the two rows on either side of a genesis are not one merge of the run
        decision, merged = merged_rows("c3", M3)
        self.assertEqual(self.used(first, decision, again, merged), set())

    def test_the_run_s_start_is_the_one_rule_of_every_reader(self):
        # ``last_genesis`` is the one function ``harness.revert_drill`` and ``harness.pass_row`` read too, and the
        # used ids are those of the rows from it on; a genesis row with ``proposed_by`` is a proposal (tohum/26d:25-26)
        # and starts no run for any of them
        from harness import pass_row, revert_drill

        self.assertIs(revert_drill.serial.last_genesis, SE.last_genesis)
        self.assertIs(pass_row.serial.last_genesis, SE.last_genesis)
        self.assertFalse(hasattr(revert_drill, "last_genesis"))
        for second, start, used in ((genesis("g2"), 4, {"c2"}),
                                    (dict(genesis("g2"), proposed_by="someone"), 0, {"c1", "c2"})):
            rows = SE.rows(ledger_with([genesis("g"), *merged_rows("c1", M1), ended("e1", M1), second,
                                        *merged_rows("c2", M2)]))
            self.assertEqual((SE.last_genesis(rows), pass_row._last_genesis(rows)), (start, start))
            self.assertEqual(SE.used_ids(rows), used)
        self.assertIsNone(SE.last_genesis([dict(genesis("g"), proposed_by="someone")]))

    def test_a_proposed_row_counts_for_nothing(self):
        self.assertEqual(self.used(START, *merged_rows("c1", M1, proposed_by="someone")), set())
        decision, merged = merged_rows("c1", M1)
        self.assertEqual(self.used(START, dict(decision, proposed_by="someone"), merged), set())
        self.assertEqual(self.used(START, decision, dict(merged, proposed_by="someone")), set())

if __name__ == "__main__":
    unittest.main()
