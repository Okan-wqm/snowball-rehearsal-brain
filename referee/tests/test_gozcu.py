"""``gozcu.evaluate`` (P1 MF7; test 41 of asama-0/09): every trigger of tohum/28 on a synthetic input.

What these tests show, on the views and policies they build (no ledger, no job and no file is read here: the
cycle's reading of its ledger is tests/test_gozcu_watch.py's):

- ``Quiet``, ``Pure``: the answer's five lists, empty on empty views; the arguments are not changed, the row
  order does not matter, no value is a float, the clock is not read;
- ``Regression``, ``Containment``, ``Budget``, ``InForce``: rules 1-4, each soft trigger firing and one step
  short of firing, the window's two edges, the scope a freeze in force leaves;
- ``HardStop``: rules 5-6, the soft-freeze limit and each fact of ``HARD_FACTS``;
- ``Marks``: rules 7-9;
- ``Thresholds``: the thirteen paths, an absent one named in ``unjudged`` with its rules unjudged, a value off
  its rule ``Invalid``;
- ``Shapes``: each view off its shape is ``Unusable`` at the place named.

Not shown: "salınım birikimi" (no rule exists, see the module), a cycle that freezes, a gate that closes.
"""

from __future__ import annotations

import calendar
import copy
import os
import sys
import time
import unittest
from fractions import Fraction
from unittest import mock

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from gozcu import evaluate as G  # noqa: E402
from harness import params as HP  # noqa: E402
from policy import reads as P  # noqa: E402

NOW = "2026-11-21T12:00:00Z"
CLOCK = calendar.timegm(time.strptime(NOW, "%Y-%m-%dT%H:%M:%SZ"))
QUIET = {"hard_stop": [], "freezes": [], "lifts": [], "marks": [], "unjudged": []}
CAP_MICROS = 10000 * 1000000


def ago(days: int = 0, seconds: int = 0) -> str:
    """The time ``days`` days and ``seconds`` seconds before ``NOW`` (negative: after)."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(CLOCK - days * 86400 - seconds))


def policy() -> dict:
    """tohum/18a's and 18b's starting values on the thirteen paths, and other values beside them."""
    return {
        "constitutional": {
            "monthly_cap_usd": 10000, "monthly_cap_ci_minutes": 1800,
            "regression_freeze": {"min_merges": 50, "window_days": 30, "revert_rate": "0.020000", "min_reverts": 2},
            "gate_rules": {"soft_freeze_limit": 2, "containment_freeze": 2, "gross_delete_cap": 200},
        },
        "performance": {"windows": {"measure": 14, "security_sweep": 7},
                        "rules": {"drift_bound": "0.200000", "seat_similarity": "0.800000",
                                  "genesis_drafts": {"per_window": 3, "queue": 10}}},
    }


def without(path: tuple) -> dict:
    out = policy()
    node = out
    for key in path[:-1]:
        node = node[key]
    del node[path[-1]]
    return out


def having(path: tuple, value) -> dict:
    out = policy()
    node = out
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return out


def views(**given) -> dict:
    out = {"events": [], "containment": [], "spend": {"usd_micros": 0, "ci_minutes": 0}, "freezes": [], "stops": {},
           "thresholds": [], "similarities": [], "genesis": {"drafts": 0, "queue": 0}}
    assert set(given) <= set(out), given
    out.update(given)
    return out


def run(policy_=None, **given) -> dict:
    return G.evaluate(views(**given), policy() if policy_ is None else policy_, NOW)


def event(kind: str, ts: str = NOW, klass: str = "K0") -> dict:
    return {"ts": ts, "kind": kind, "class": klass}


def merges(n: int, ts: str = NOW) -> list:
    return [event("merge", ts) for _ in range(n)]


def reverts(n: int, ts: str = NOW, klass: str = "K0") -> list:
    return [event("revert", ts, klass) for _ in range(n)]


def violation(file: str, cause: str, ts: str = NOW, klass: str = "K0") -> dict:
    return {"ts": ts, "file": file, "root_cause": cause, "class": klass}


def frozen(trigger: str, scope: list, start: str, lifted=None) -> dict:
    return {"trigger": trigger, "scope": scope, "start": start, "lifted": lifted}


def freeze(trigger: str, scope: list, **measurement) -> dict:
    return {"trigger": trigger, "scope": scope, "measurement": measurement, "start": NOW}


class Quiet(unittest.TestCase):
    def test_empty_views_give_five_empty_lists(self):
        self.assertEqual(run(), QUIET)

    def test_work_inside_every_bound_gives_five_empty_lists(self):
        got = run(events=merges(60) + reverts(1), containment=[violation("a", "c1")],
                  spend={"usd_micros": CAP_MICROS - 1, "ci_minutes": 1799},
                  freezes=[frozen("regression", ["K0"], ago(3), ago(2)), frozen("containment", ["K0"], ago(1))],
                  stops={"drift": [], "kill_switch": []},
                  thresholds=[{"name": "recall_gate", "initial": 0.5, "current": 0.6}],
                  similarities=[{"seats": ["rival", "oracle"], "similarity": 0.8}],
                  genesis={"drafts": 3, "queue": 10})
        self.assertEqual(got, QUIET)


class Regression(unittest.TestCase):
    """Rule 1."""

    def test_under_min_merges_the_count_of_reverts_decides(self):
        self.assertEqual(run(events=merges(49) + reverts(1)), QUIET)
        self.assertEqual(run(events=merges(49) + reverts(2))["freezes"],
                         [freeze("regression", ["K0"], merges=49, reverts=2, window_days=30)])
        self.assertEqual(run(events=reverts(2))["freezes"],
                         [freeze("regression", ["K0"], merges=0, reverts=2, window_days=30)])

    def test_from_min_merges_the_rate_decides_and_not_the_count(self):
        self.assertEqual(run(events=merges(50) + reverts(1)), QUIET)
        self.assertEqual(run(events=merges(100) + reverts(2)), QUIET)
        self.assertEqual(run(events=merges(100) + reverts(3))["freezes"],
                         [freeze("regression", ["K0"], merges=100, reverts=3, window_days=30)])
        self.assertEqual(run(events=merges(50) + reverts(2))["freezes"],
                         [freeze("regression", ["K0"], merges=50, reverts=2, window_days=30)])

    def test_the_rate_is_the_decimal_written_and_not_its_binary_float(self):
        self.assertGreater(57, 0.57 * 100)
        rate = having(P.REGRESSION_REVERT_RATE, "0.570000")
        self.assertEqual(run(rate, events=merges(100) + reverts(57)), QUIET)
        self.assertEqual(len(run(rate, events=merges(100) + reverts(58))["freezes"]), 1)

    def test_exactly_min_merges_is_judged_by_the_rate(self):
        rate = having(P.REGRESSION_REVERT_RATE, "0.570000")
        self.assertEqual(run(rate, events=merges(50) + reverts(2)), QUIET)
        self.assertEqual(len(run(rate, events=merges(49) + reverts(2))["freezes"]), 1)

    def test_the_window_is_open_at_its_start_and_closed_at_now(self):
        for ts, inside in ((ago(30), False), (ago(30, -1), True), (NOW, True), (ago(0, -1), False)):
            with self.subTest(ts=ts):
                got = run(events=reverts(1) + reverts(1, ts))
                self.assertEqual(len(got["freezes"]), 1 if inside else 0)

    def test_merges_outside_the_window_are_not_counted(self):
        got = run(events=merges(60, ago(31)) + merges(10) + reverts(2))
        self.assertEqual(got["freezes"], [freeze("regression", ["K0"], merges=10, reverts=2, window_days=30)])
        self.assertEqual(run(events=merges(60, ago(29)) + merges(40) + reverts(2)), QUIET)

    def test_the_window_is_regression_freeze_window_days(self):
        self.assertEqual(run(having(P.REGRESSION_WINDOW_DAYS, 10), events=reverts(1) + reverts(1, ago(11))), QUIET)
        self.assertEqual(len(run(having(P.REGRESSION_WINDOW_DAYS, 12),
                                 events=reverts(1) + reverts(1, ago(11)))["freezes"]), 1)

    def test_all_classes_are_counted_together_and_the_scope_is_the_counted_reverts_classes(self):
        got = run(events=[event("merge", NOW, "K4")] + reverts(1, NOW, "K1") + reverts(1, NOW, "K0")
                  + reverts(1, ago(40), "K2"))
        self.assertEqual(got["freezes"], [freeze("regression", ["K0", "K1"], merges=1, reverts=2, window_days=30)])


class Containment(unittest.TestCase):
    """Rule 2."""

    def frozen(self, rows: list, policy_=None) -> list:
        return run(policy_, containment=rows)["freezes"]

    def test_two_distinct_violations_in_the_window_freeze(self):
        self.assertEqual(self.frozen([violation("a", "c1")]), [])
        self.assertEqual(self.frozen([violation("a", "c1"), violation("b", "c2", NOW, "K1")]),
                         [freeze("containment", ["K0", "K1"], violations=2, window_days=14)])

    def test_the_same_file_or_the_same_root_cause_is_one_violation(self):
        self.assertEqual(self.frozen([violation("a", "c1"), violation("a", "c2")]), [])
        self.assertEqual(self.frozen([violation("a", "c1"), violation("b", "c1")]), [])
        self.assertEqual(self.frozen([violation("a", "c1")] * 5), [])

    def test_one_count_runs_along_a_chain_of_shared_files_and_causes(self):
        chain = [violation("a", "c1"), violation("a", "c2"), violation("b", "c2"), violation("b", "c3")]
        self.assertEqual(self.frozen(chain), [])
        self.assertEqual(self.frozen(list(reversed(chain))), [])
        self.assertEqual(self.frozen([chain[0], chain[3], chain[1], chain[2]]), [])
        self.assertEqual(self.frozen(chain + [violation("z", "c9")]),
                         [freeze("containment", ["K0"], violations=2, window_days=14)])
        self.assertEqual(self.frozen([chain[0], chain[3]]),
                         [freeze("containment", ["K0"], violations=2, window_days=14)])

    def test_a_file_and_a_root_cause_of_one_name_are_two_things(self):
        self.assertEqual(self.frozen([violation("x", "c1"), violation("b", "x")]),
                         [freeze("containment", ["K0"], violations=2, window_days=14)])

    def test_the_window_is_the_measure_window_open_at_its_start(self):
        for ts, inside in ((ago(14), False), (ago(14, -1), True), (ago(0, -1), False)):
            with self.subTest(ts=ts):
                self.assertEqual(len(self.frozen([violation("a", "c1"), violation("b", "c2", ts)])),
                                 1 if inside else 0)
        self.assertEqual(len(self.frozen([violation("a", "c1"), violation("b", "c2", ago(14))],
                                         having(P.MEASURE_WINDOW, 15))), 1)

    def test_the_limit_is_containment_freeze_and_the_scope_is_the_windows_violations(self):
        three = having(P.CONTAINMENT_FREEZE, 3)
        rows = [violation("a", "c1", NOW, "K1"), violation("b", "c2"), violation("o", "c0", ago(20), "K7")]
        self.assertEqual(self.frozen(rows, three), [])
        self.assertEqual(self.frozen(rows + [violation("c", "c3", ago(1), "K5")], three),
                         [freeze("containment", ["K0", "K1", "K5"], violations=3, window_days=14)])


class Budget(unittest.TestCase):
    """Rules 3 and 4."""

    def test_reaching_the_usd_cap_freezes_the_loop(self):
        self.assertEqual(run(spend={"usd_micros": CAP_MICROS - 1, "ci_minutes": 0}), QUIET)
        for spent in (CAP_MICROS, CAP_MICROS + 5):
            self.assertEqual(run(spend={"usd_micros": spent, "ci_minutes": 0})["freezes"],
                             [freeze("budget_usd", ["loop"], spent=spent, cap=CAP_MICROS)])

    def test_reaching_the_minutes_cap_freezes_the_loop(self):
        self.assertEqual(run(spend={"usd_micros": 0, "ci_minutes": 1799}), QUIET)
        self.assertEqual(run(spend={"usd_micros": 0, "ci_minutes": 1800})["freezes"],
                         [freeze("budget_ci_minutes", ["loop"], spent=1800, cap=1800)])

    def test_each_cap_is_read_from_its_own_path(self):
        got = run(having(P.MONTHLY_CAP_USD, 3), spend={"usd_micros": 3000000, "ci_minutes": 4})
        self.assertEqual(got["freezes"], [freeze("budget_usd", ["loop"], spent=3000000, cap=3000000)])
        got = run(having(P.MONTHLY_CAP_CI_MINUTES, 4), spend={"usd_micros": 3000000, "ci_minutes": 4})
        self.assertEqual(got["freezes"], [freeze("budget_ci_minutes", ["loop"], spent=4, cap=4)])

    def test_both_caps_reached_are_two_freezes_in_the_order_of_soft(self):
        got = run(spend={"usd_micros": CAP_MICROS, "ci_minutes": 1800})
        self.assertEqual([f["trigger"] for f in got["freezes"]], ["budget_usd", "budget_ci_minutes"])

    def test_a_budget_freeze_in_force_is_not_started_again_and_a_lifted_one_is(self):
        spend = {"usd_micros": CAP_MICROS, "ci_minutes": 0}
        self.assertEqual(run(spend=spend, freezes=[frozen("budget_usd", ["loop"], ago(1))]), QUIET)
        got = run(spend=spend, freezes=[frozen("budget_usd", ["loop"], ago(2), ago(1))])
        self.assertEqual(got["freezes"], [freeze("budget_usd", ["loop"], spent=CAP_MICROS, cap=CAP_MICROS)])
        self.assertEqual(got["lifts"], [])

    def test_a_budget_freeze_in_force_lifts_when_its_cap_is_no_longer_reached(self):
        rows = [frozen("budget_usd", ["loop"], ago(9)), frozen("budget_ci_minutes", ["loop"], ago(8)),
                frozen("budget_usd", ["loop"], ago(40), ago(30)), frozen("regression", ["K0"], ago(7)),
                frozen("containment", ["K0"], ago(6))]
        roomy = having(P.SOFT_FREEZE_LIMIT, 9)
        got = run(roomy, spend={"usd_micros": CAP_MICROS - 1, "ci_minutes": 1800}, freezes=rows)
        self.assertEqual(got, dict(QUIET, lifts=[{"trigger": "budget_usd", "scope": ["loop"], "start": ago(9)}]))
        got = run(roomy, spend={"usd_micros": CAP_MICROS, "ci_minutes": 0}, freezes=rows)
        self.assertEqual(got, dict(QUIET, lifts=[{"trigger": "budget_ci_minutes", "scope": ["loop"],
                                                  "start": ago(8)}]))

    def test_a_raised_cap_lifts(self):
        rows = [frozen("budget_usd", ["loop"], ago(1))]
        spend = {"usd_micros": CAP_MICROS, "ci_minutes": 0}
        self.assertEqual(run(spend=spend, freezes=rows)["lifts"], [])
        self.assertEqual(run(having(P.MONTHLY_CAP_USD, 10001), spend=spend, freezes=rows)["lifts"],
                         [{"trigger": "budget_usd", "scope": ["loop"], "start": ago(1)}])

    def test_lifts_are_ordered_by_trigger_then_start(self):
        rows = [frozen("budget_ci_minutes", ["loop"], ago(1)), frozen("budget_usd", ["loop"], ago(2)),
                frozen("budget_usd", ["loop"], ago(3))]
        for order in (rows, list(reversed(rows))):
            self.assertEqual([(lift["trigger"], lift["start"]) for lift in run(freezes=order)["lifts"]],
                             [("budget_usd", ago(3)), ("budget_usd", ago(2)), ("budget_ci_minutes", ago(1))])

    def test_an_absent_cap_neither_freezes_nor_lifts(self):
        got = run(without(P.MONTHLY_CAP_CI_MINUTES), spend={"usd_micros": 0, "ci_minutes": 10 ** 9},
                  freezes=[frozen("budget_ci_minutes", ["loop"], ago(1))])
        self.assertEqual(got, dict(QUIET, unjudged=["constitutional.monthly_cap_ci_minutes"]))
        with self.assertRaises(HP.Invalid) as ctx:     # the USD cap is one of tohum/28a's seven: absent is no rule skipped
            run(without(P.MONTHLY_CAP_USD), spend={"usd_micros": CAP_MICROS * 9, "ci_minutes": 0},
                freezes=[frozen("budget_usd", ["loop"], ago(1))])
        self.assertEqual(ctx.exception.reasons, ["policy_invalid:constitutional.monthly_cap_usd"])


class InForce(unittest.TestCase):
    """The scope a freeze in force of the same trigger leaves."""

    def test_a_class_the_trigger_has_closed_is_not_closed_again(self):
        events = reverts(1, NOW, "K0") + reverts(1, NOW, "K1")
        self.assertEqual(run(events=events, freezes=[frozen("regression", ["K0", "K1"], ago(40))]), QUIET)
        self.assertEqual(run(events=events, freezes=[frozen("regression", ["K0"], ago(40)),
                                                     frozen("regression", ["K1"], ago(40))]), QUIET)
        got = run(events=events, freezes=[frozen("regression", ["K0"], ago(40))])
        self.assertEqual(got["freezes"], [freeze("regression", ["K1"], merges=0, reverts=2, window_days=30)])

    def test_a_lifted_freeze_and_another_triggers_freeze_close_nothing(self):
        events = reverts(2)
        for rows in ([frozen("regression", ["K0"], ago(40), ago(39))], [frozen("containment", ["K0"], ago(40))]):
            with self.subTest(rows=rows):
                self.assertEqual(run(events=events, freezes=rows)["freezes"],
                                 [freeze("regression", ["K0"], merges=0, reverts=2, window_days=30)])

    def test_containment_leaves_its_own_closed_classes_too(self):
        rows = [violation("a", "c1", NOW, "K0"), violation("b", "c2", NOW, "K1")]
        got = run(containment=rows, freezes=[frozen("containment", ["K1"], ago(40))])
        self.assertEqual(got["freezes"], [freeze("containment", ["K0"], violations=2, window_days=14)])


class HardStop(unittest.TestCase):
    """Rules 5 and 6."""

    def test_more_soft_freezes_in_the_window_than_the_limit_is_a_hard_stop(self):
        two = [frozen("regression", ["K0"], ago(3), ago(2)), frozen("containment", ["K0"], ago(1))]
        self.assertEqual(run(freezes=two), QUIET)
        third = frozen("budget_ci_minutes", ["loop"], ago(13), ago(12))
        self.assertEqual(run(freezes=two + [third])["hard_stop"],
                         [{"trigger": "soft_freeze_limit", "evidence": sorted([
                             "regression@" + ago(3), "containment@" + ago(1), "budget_ci_minutes@" + ago(13)])}])
        self.assertEqual(run(having(P.SOFT_FREEZE_LIMIT, 3), freezes=two + [third]), QUIET)

    def test_a_freeze_this_call_starts_is_counted(self):
        two = [frozen("regression", ["K1"], ago(3), ago(2)), frozen("containment", ["K0"], ago(1))]
        got = run(freezes=two, events=reverts(2))
        self.assertEqual(len(got["freezes"]), 1)
        self.assertEqual(got["hard_stop"], [{"trigger": "soft_freeze_limit", "evidence": sorted([
            "regression@" + ago(3), "containment@" + ago(1), "regression@" + NOW])}])
        self.assertEqual(run(freezes=two[:1], events=reverts(2))["hard_stop"], [])

    def test_only_the_freezes_started_in_the_measure_window_are_counted(self):
        for ts, inside in ((ago(14), False), (ago(14, -1), True), (ago(0, -1), False)):
            with self.subTest(ts=ts):
                rows = [frozen("regression", ["K0"], ago(3), ago(2)), frozen("containment", ["K0"], ago(1)),
                        frozen("regression", ["K1"], ts, None if inside else ago(0, -2))]
                self.assertEqual(len(run(freezes=rows)["hard_stop"]), 1 if inside else 0)

    def test_each_fact_with_evidence_is_a_hard_stop(self):
        for fact in G.HARD_FACTS:
            with self.subTest(fact=fact):
                got = run(stops={fact: ["line one", "line two"]})
                self.assertEqual(got, dict(QUIET, hard_stop=[{"trigger": fact,
                                                              "evidence": ["line one", "line two"]}]))
                self.assertEqual(run(stops={fact: []}), QUIET)

    def test_the_facts_are_tohum_28s_seven(self):
        self.assertEqual(G.HARD_FACTS, ("drift", "chain_break", "rekor", "attestation", "activation",
                                        "ref_change", "kill_switch"))
        self.assertEqual(G.HARD, ("soft_freeze_limit",) + G.HARD_FACTS)

    def test_every_hard_stop_at_once_in_the_order_of_hard(self):
        rows = [frozen("regression", ["K0"], ago(3), ago(2)), frozen("containment", ["K0"], ago(1)),
                frozen("budget_usd", ["loop"], ago(2), ago(1))]
        stops = {fact: ["e:" + fact] for fact in reversed(G.HARD_FACTS)}
        got = run(freezes=rows, stops=stops)
        self.assertEqual([stop["trigger"] for stop in got["hard_stop"]], list(G.HARD))
        self.assertEqual(got["hard_stop"][3], {"trigger": "rekor", "evidence": ["e:rekor"]})

    def test_the_evidence_is_a_copy(self):
        stops = {"drift": ["rules_bypassable"]}
        got = run(stops=stops)
        got["hard_stop"][0]["evidence"].append("x")
        self.assertEqual(stops, {"drift": ["rules_bypassable"]})


class Marks(unittest.TestCase):
    """Rules 7-9."""

    def marks(self, policy_=None, **given) -> list:
        got = run(policy_, **given)
        self.assertEqual((got["hard_stop"], got["freezes"], got["lifts"]), ([], [], []))
        return got["marks"]

    def moved(self, initial, current, policy_=None) -> list:
        return self.marks(policy_, thresholds=[{"name": "recall_gate", "initial": initial, "current": current}])

    def test_a_threshold_moved_by_more_than_the_bound_is_marked(self):
        for initial, current in ((10, 12), (10, 8), (0.5, 0.6), (0.5, 0.4), (-10, -12), (-10, -8), (10, 10),
                                 (0.1, 0.12), (0.3, 0.36), (0.7, 0.84)):
            with self.subTest(initial=initial, current=current):
                self.assertEqual(self.moved(initial, current), [])
        for initial, current in ((10, 13), (10, 7), (0.5, 0.61), (0.5, 0.39), (-10, -13), (-10, -7), (10, -10),
                                 (1, 1.21), (0.1, 0.1201)):
            with self.subTest(initial=initial, current=current):
                self.assertEqual(self.moved(initial, current),
                                 [{"mark": "threshold_drift", "subject": ["recall_gate"],
                                   "measurement": {"initial": repr(initial), "current": repr(current)}}])

    def test_the_movement_is_compared_as_decimals_and_not_as_binary_floats(self):
        self.assertGreater(abs(0.42 - 0.35), 0.2 * abs(0.35))
        self.assertEqual(self.moved(0.35, 0.42), [])

    def test_the_bound_is_drift_bound(self):
        self.assertEqual(len(self.moved(10, 12, having(P.DRIFT_BOUND, "0.190000"))), 1)
        self.assertEqual(self.moved(10, 13, having(P.DRIFT_BOUND, "0.300000")), [])

    def test_two_seats_more_similar_than_the_bound_are_marked(self):
        rows = [{"seats": ["rival", "oracle"], "similarity": 0.81}, {"seats": ["a", "b"], "similarity": 0.8},
                {"seats": ["c", "b"], "similarity": 1}, {"seats": ["d", "e"], "similarity": 0}]
        self.assertEqual(self.marks(similarities=rows), [
            {"mark": "seat_similarity", "subject": ["b", "c"], "measurement": {"similarity": "1"}},
            {"mark": "seat_similarity", "subject": ["oracle", "rival"], "measurement": {"similarity": "0.81"}}])
        self.assertEqual(len(self.marks(having(P.SEAT_SIMILARITY, "0.790000"), similarities=rows)), 3)

    def test_genesis_drafts_and_queue_over_their_limits_are_marked(self):
        self.assertEqual(self.marks(genesis={"drafts": 3, "queue": 10}), [])
        self.assertEqual(self.marks(genesis={"drafts": 4, "queue": 10}),
                         [{"mark": "genesis_drafts", "subject": ["genesis"], "measurement": {"drafts": 4, "limit": 3}}])
        self.assertEqual(self.marks(genesis={"drafts": 3, "queue": 11}),
                         [{"mark": "genesis_queue", "subject": ["genesis"], "measurement": {"queue": 11, "limit": 10}}])
        self.assertEqual(self.marks(having(P.GENESIS_DRAFTS_PER_WINDOW, 9), genesis={"drafts": 9, "queue": 11}),
                         [{"mark": "genesis_queue", "subject": ["genesis"], "measurement": {"queue": 11, "limit": 10}}])
        self.assertEqual(self.marks(having(P.GENESIS_DRAFTS_QUEUE, 11), genesis={"drafts": 4, "queue": 11}),
                         [{"mark": "genesis_drafts", "subject": ["genesis"], "measurement": {"drafts": 4, "limit": 3}}])

    def test_marks_are_ordered_by_mark_then_subject(self):
        got = self.marks(genesis={"drafts": 4, "queue": 11},
                         similarities=[{"seats": ["y", "x"], "similarity": 0.9}],
                         thresholds=[{"name": "b", "initial": 1, "current": 2},
                                     {"name": "a", "initial": 1, "current": 2}])
        self.assertEqual([(m["mark"], m["subject"]) for m in got],
                         [("threshold_drift", ["a"]), ("threshold_drift", ["b"]), ("seat_similarity", ["x", "y"]),
                          ("genesis_drafts", ["genesis"]), ("genesis_queue", ["genesis"])])
        self.assertEqual(G.MARKS, ("threshold_drift", "seat_similarity", "genesis_drafts", "genesis_queue"))


def loud() -> dict:
    """Views on which every rule that has a threshold fires at ``NOW`` under ``policy()``."""
    return views(
        events=reverts(2), containment=[violation("a", "c1"), violation("b", "c2")],
        spend={"usd_micros": CAP_MICROS, "ci_minutes": 1800},
        freezes=[frozen("regression", ["K9"], ago(2), ago(1))], stops={"drift": ["rules_bypassable"]},
        thresholds=[{"name": "recall_gate", "initial": 0.5, "current": 0.75}],
        similarities=[{"seats": ["rival", "oracle"], "similarity": 0.9}], genesis={"drafts": 4, "queue": 11})


def fired(got: dict) -> list:
    return sorted([row["trigger"] for row in got["freezes"] + got["hard_stop"]] + [row["mark"] for row in got["marks"]])


ALL = sorted(G.SOFT + ("soft_freeze_limit", "drift") + G.MARKS)
SILENCED = {
    P.MONTHLY_CAP_USD: {"budget_usd"},
    P.MONTHLY_CAP_CI_MINUTES: {"budget_ci_minutes"},
    P.REGRESSION_MIN_MERGES: {"regression"},
    P.REGRESSION_WINDOW_DAYS: {"regression"},
    P.REGRESSION_REVERT_RATE: {"regression"},
    P.REGRESSION_MIN_REVERTS: {"regression"},
    P.SOFT_FREEZE_LIMIT: {"soft_freeze_limit"},
    P.CONTAINMENT_FREEZE: {"containment"},
    P.MEASURE_WINDOW: {"containment", "soft_freeze_limit"},
    P.DRIFT_BOUND: {"threshold_drift"},
    P.SEAT_SIMILARITY: {"seat_similarity"},
    P.GENESIS_DRAFTS_PER_WINDOW: {"genesis_drafts"},
    P.GENESIS_DRAFTS_QUEUE: {"genesis_queue"},
}


class Thresholds(unittest.TestCase):
    def test_the_thirteen_paths_are_policy_reads_and_the_command_names_them(self):
        self.assertEqual(tuple(G.THRESHOLDS.values()), P.GOZCU_PATHS)
        self.assertEqual(len(set(P.GOZCU_PATHS)), 13)
        self.assertEqual(set(SILENCED), set(P.GOZCU_PATHS))
        for path in P.GOZCU_PATHS:
            self.assertIn(path, P.PATHS)
        self.assertEqual(sorted(P.dotted(p) for p in P.GOZCU_PATHS), [
            "constitutional.gate_rules.containment_freeze", "constitutional.gate_rules.soft_freeze_limit",
            "constitutional.monthly_cap_ci_minutes", "constitutional.monthly_cap_usd",
            "constitutional.regression_freeze.min_merges", "constitutional.regression_freeze.min_reverts",
            "constitutional.regression_freeze.revert_rate", "constitutional.regression_freeze.window_days",
            "performance.rules.drift_bound", "performance.rules.genesis_drafts.per_window",
            "performance.rules.genesis_drafts.queue", "performance.rules.seat_similarity",
            "performance.windows.measure"])

    def test_the_values_are_read_from_their_paths(self):
        self.assertEqual(G.thresholds(policy()), {
            "monthly_cap_usd": 10000, "monthly_cap_ci_minutes": 1800, "min_merges": 50, "window_days": 30,
            "revert_rate": Fraction(1, 50), "min_reverts": 2, "soft_freeze_limit": 2, "containment_freeze": 2,
            "measure_window": 14, "drift_bound": Fraction(1, 5), "seat_similarity": Fraction(4, 5),
            "per_window": 3, "queue": 10})

    def test_every_rule_fires_on_the_loud_views(self):
        got = G.evaluate(loud(), policy(), NOW)
        self.assertEqual(fired(got), ALL)
        self.assertEqual(got["unjudged"], [])

    def test_an_absent_path_is_named_and_only_its_rules_are_not_judged(self):
        optional = (P.MONTHLY_CAP_CI_MINUTES, P.CONTAINMENT_FREEZE, P.DRIFT_BOUND, P.SEAT_SIMILARITY,
                    P.GENESIS_DRAFTS_PER_WINDOW, P.GENESIS_DRAFTS_QUEUE)
        self.assertEqual(set(optional), set(P.GOZCU_PATHS) - set(P.REQUIRED))
        for path in optional:
            with self.subTest(path=path):
                got = G.evaluate(loud(), without(path), NOW)
                self.assertEqual(got["unjudged"], [P.dotted(path)])
                self.assertEqual(fired(got), sorted(set(ALL) - SILENCED[path]))

    def test_an_absent_required_path_is_invalid_and_nothing_is_judged(self):
        required = (P.MONTHLY_CAP_USD, P.REGRESSION_MIN_MERGES, P.REGRESSION_WINDOW_DAYS, P.REGRESSION_REVERT_RATE,
                    P.REGRESSION_MIN_REVERTS, P.SOFT_FREEZE_LIMIT, P.MEASURE_WINDOW)     # tohum/28a's seven
        self.assertEqual(set(required), set(P.GOZCU_PATHS) & set(P.REQUIRED))
        for path in required:
            for views_ in (loud(), views()):
                with self.subTest(path=path), self.assertRaises(HP.Invalid) as ctx:
                    G.evaluate(views_, without(path), NOW)
                self.assertEqual(ctx.exception.reasons, ["policy_invalid:" + P.dotted(path)])

    def test_values_at_the_root_or_in_another_section_are_not_read(self):
        source = policy()
        hoisted = dict(source["constitutional"], **source["performance"])
        hoisted.update(constitutional={"performance": source["performance"], "rules": source["performance"]["rules"]},
                       performance=source["constitutional"])
        named = ["policy_invalid:" + P.dotted(p) for p in P.GOZCU_PATHS if p in P.REQUIRED]
        for policy_ in (hoisted, {}):
            with self.assertRaises(HP.Invalid) as ctx:
                G.evaluate(loud(), policy_, NOW)
            self.assertEqual(ctx.exception.reasons, named)
        # with the seven required ones in their sections, the other six are still not read from elsewhere
        for path in P.REQUIRED:
            if path in P.GOZCU_PATHS:
                node, at = hoisted, source
                for key in path[:-1]:
                    node, at = node[key] if key in ("constitutional", "performance") else node.setdefault(key, {}), at[key]
                node[path[-1]] = at[path[-1]]
        got = G.evaluate(loud(), hoisted, NOW)
        self.assertEqual(got["unjudged"], sorted(P.dotted(p) for p in P.GOZCU_PATHS if p not in P.REQUIRED))

    def test_a_value_off_its_rule_is_invalid_and_nothing_is_judged(self):
        fractions = (P.REGRESSION_REVERT_RATE, P.DRIFT_BOUND, P.SEAT_SIMILARITY)
        for path in P.GOZCU_PATHS:
            bad = (0, 1, 1.0, 0.0, 0.5, 0.02, 2e-2, 1.5, True, None, "0.5", "0.000000", "1.000000", "0.0200000",
                   ["0.500000"]) if path in fractions else (0, -1, 1.5, 0.5, 2.0, True, None, "2", "0.500000", [2])
            for value in bad:
                with self.subTest(path=path, value=value), self.assertRaises(HP.Invalid) as ctx:
                    G.evaluate(loud(), having(path, value), NOW)
                self.assertEqual(ctx.exception.reasons, ["policy_invalid:" + P.dotted(path)])

    def test_every_invalid_path_is_named_in_the_order_of_the_table(self):
        bad = policy()
        bad["constitutional"]["monthly_cap_usd"] = 0.5
        bad["constitutional"]["gate_rules"] = []
        bad["performance"]["rules"]["genesis_drafts"]["queue"] = 0
        with self.assertRaises(HP.Invalid) as ctx:
            G.thresholds(bad)
        self.assertEqual(ctx.exception.reasons, [
            "policy_invalid:constitutional.monthly_cap_usd",
            "policy_invalid:constitutional.gate_rules.soft_freeze_limit",
            "policy_invalid:constitutional.gate_rules.containment_freeze",
            "policy_invalid:performance.rules.genesis_drafts.queue"])
        with self.assertRaises(HP.Invalid):
            G.evaluate(views(), [], NOW)


def bad_views() -> dict:
    """``{where: views}``: each one value off its shape."""
    ok_event, ok_violation = event("merge"), violation("a", "c1")
    ok_frozen = frozen("regression", ["K0"], ago(2), ago(1))
    ok_moved = {"name": "n", "initial": 1, "current": 1}
    ok_similar = {"seats": ["a", "b"], "similarity": 0.5}
    out = {
        "events": views(events={}),
        "events[1]": views(events=[ok_event, dict(ok_event, extra=1)]),
        "events[0]": views(events=[{"ts": NOW, "kind": "merge"}]),
        "events[0].kind": views(events=[dict(ok_event, kind="sentinel")]),
        "events[0].ts": views(events=[dict(ok_event, ts="2026-11-21 12:00:00")]),
        "events[0].class": views(events=[dict(ok_event, **{"class": ""})]),
        "containment": views(containment=None),
        "containment[0]": views(containment=[dict(ok_violation, extra=1)]),
        "containment[0].ts": views(containment=[dict(ok_violation, ts="2026-02-30T00:00:00Z")]),
        "containment[0].file": views(containment=[dict(ok_violation, file=3)]),
        "containment[0].root_cause": views(containment=[dict(ok_violation, root_cause="")]),
        "containment[0].class": views(containment=[dict(ok_violation, **{"class": None})]),
        "spend": views(spend={"usd_micros": 0}),
        "spend.usd_micros": views(spend={"usd_micros": -1, "ci_minutes": 0}),
        "spend.ci_minutes": views(spend={"usd_micros": 0, "ci_minutes": 1.0}),
        "freezes": views(freezes="x"),
        "freezes[0]": views(freezes=[{"trigger": "regression", "scope": ["K0"], "start": NOW}]),
        "freezes[0].trigger": views(freezes=[dict(ok_frozen, trigger="drift")]),
        "freezes[0].scope": views(freezes=[dict(ok_frozen, scope="K0")]),
        "freezes[0].scope[1]": views(freezes=[dict(ok_frozen, scope=["K0", 1])]),
        "freezes[0].start": views(freezes=[dict(ok_frozen, start=None)]),
        "freezes[0].lifted": views(freezes=[dict(ok_frozen, lifted="soon")]),
        "stops": views(stops=[]),
        "stops.drift": views(stops={"drift": "rules_bypassable"}),
        "stops.drift[1]": views(stops={"drift": ["a", ""]}),
        "thresholds": views(thresholds={}),
        "thresholds[0]": views(thresholds=[{"name": "n", "initial": 1}]),
        "thresholds[0].name": views(thresholds=[dict(ok_moved, name="")]),
        "thresholds[0].initial": views(thresholds=[dict(ok_moved, initial=True)]),
        "thresholds[0].current": views(thresholds=[dict(ok_moved, current="1")]),
        "similarities": views(similarities=()),
        "similarities[0]": views(similarities=[dict(ok_similar, extra=1)]),
        "similarities[0].seats": views(similarities=[dict(ok_similar, seats="ab")]),
        "similarities[0].seats[0]": views(similarities=[dict(ok_similar, seats=["", "b"])]),
        "similarities[0].similarity": views(similarities=[dict(ok_similar, similarity=float("inf"))]),
        "genesis": views(genesis=[]),
        "genesis.drafts": views(genesis={"drafts": True, "queue": 0}),
        "genesis.queue": views(genesis={"drafts": 0, "queue": -1}),
    }
    return out


class Shapes(unittest.TestCase):
    def refused(self, where: str, value: dict, what: str = "") -> None:
        with self.subTest(where=where, what=what), self.assertRaises(G.Unusable) as ctx:
            G.evaluate(value, policy(), NOW)
        self.assertTrue(str(ctx.exception).startswith(where + ": "), ctx.exception)
        if what:
            self.assertEqual(str(ctx.exception), "%s: %s" % (where, what))

    def test_each_value_off_its_shape_is_refused_at_its_place(self):
        for where, value in bad_views().items():
            self.refused(where, value)

    def test_the_views_are_exactly_the_eight(self):
        self.assertEqual(set(views()), set(G.VIEWS))
        missing = views()
        del missing["genesis"]
        for value in (missing, dict(views(), extra=[]), [], None):
            self.refused("views", value)

    def test_an_unknown_stop_fact_is_refused(self):
        self.refused("stops", views(stops={"soft_freeze_limit": ["x"]}))
        self.refused("stops", views(stops={"drift": ["x"], "panic": ["x"]}))

    def test_a_scope_is_a_non_empty_sorted_list_of_distinct_names(self):
        for scope in ([], ["K1", "K0"], ["K0", "K0"]):
            self.refused("freezes[0].scope", views(freezes=[frozen("regression", scope, NOW)]),
                         "not a non-empty sorted list of distinct names")

    def test_a_lift_before_its_start_is_refused_and_one_at_its_start_is_not(self):
        self.refused("freezes[0].lifted", views(freezes=[frozen("regression", ["K0"], ago(1), ago(1, 1))]),
                     "before start")
        self.assertEqual(run(freezes=[frozen("regression", ["K0"], ago(1), ago(1))]), QUIET)

    def test_an_initial_threshold_of_zero_is_refused(self):
        for zero in (0, 0.0):
            self.refused("thresholds[0].initial",
                         views(thresholds=[{"name": "n", "initial": zero, "current": 1}]),
                         "0 has no relative movement")

    def test_two_seats_are_two_and_distinct(self):
        for seats in (["a"], ["a", "b", "c"], ["a", "a"]):
            self.refused("similarities[0].seats", views(similarities=[{"seats": seats, "similarity": 0.5}]),
                         "not two distinct seats")

    def test_a_number_is_an_integer_or_a_finite_float(self):
        for value in (float("nan"), float("-inf"), False, None, "0.5", Fraction(1, 2)):
            self.refused("similarities[0].similarity",
                         views(similarities=[{"seats": ["a", "b"], "similarity": value}]), "not a number")

    def test_now_is_a_timestamp_and_a_real_date(self):
        for now, what in (("2026-11-21 12:00:00", "not YYYY-MM-DDTHH:MM:SSZ"), (None, "not YYYY-MM-DDTHH:MM:SSZ"),
                          (CLOCK, "not YYYY-MM-DDTHH:MM:SSZ"), ("2026-11-21T12:00:00Z\n", "not YYYY-MM-DDTHH:MM:SSZ"),
                          ("2026-02-30T00:00:00Z", "not a date"), ("2026-13-01T00:00:00Z", "not a date"),
                          ("2026-11-21T24:00:00Z", "not a date")):
            with self.subTest(now=now), self.assertRaises(G.Unusable) as ctx:
                G.evaluate(views(), policy(), now)
            self.assertEqual(str(ctx.exception), "now: " + what)

    def test_a_bad_view_is_refused_even_when_a_hard_fact_is_given(self):
        self.refused("events", views(events=None, stops={"kill_switch": ["control.json"]}))


def floats(value, where="out") -> list:
    if isinstance(value, dict):
        return [w for k, v in value.items() for w in floats(v, "%s.%s" % (where, k))]
    if isinstance(value, list):
        return [w for i, v in enumerate(value) for w in floats(v, "%s[%d]" % (where, i))]
    return [where] if isinstance(value, float) else []


class Pure(unittest.TestCase):
    def test_the_arguments_are_not_changed(self):
        given, rules = loud(), policy()
        before = copy.deepcopy((given, rules))
        G.evaluate(given, rules, NOW)
        self.assertEqual((given, rules), before)

    def test_the_answer_shares_nothing_with_the_views(self):
        given = dict(loud(), freezes=[frozen("budget_usd", ["loop"], ago(1))],
                     spend={"usd_micros": 0, "ci_minutes": 0})
        got = G.evaluate(given, policy(), NOW)
        got["lifts"][0]["scope"].append("x")
        got["hard_stop"][0]["evidence"].append("x")
        self.assertEqual(given["freezes"], [frozen("budget_usd", ["loop"], ago(1))])
        self.assertEqual(given["stops"], {"drift": ["rules_bypassable"]})

    def test_the_row_order_does_not_change_the_answer(self):
        given = loud()
        given["events"] += merges(3) + reverts(1, NOW, "K1")
        given["containment"] += [violation("a", "c9", NOW, "K3"), violation("q", "c2")]
        given["freezes"] += [frozen("containment", ["K7"], ago(3)), frozen("budget_usd", ["x"], ago(5), ago(4))]
        given["thresholds"] += [{"name": "a", "initial": 1, "current": 2}]
        given["similarities"] += [{"seats": ["a", "b"], "similarity": 1}]
        turned = {name: list(reversed(value)) if isinstance(value, list) else value for name, value in given.items()}
        turned["similarities"] = [dict(row, seats=list(reversed(row["seats"]))) for row in turned["similarities"]]
        self.assertEqual(G.evaluate(turned, policy(), NOW), G.evaluate(given, policy(), NOW))

    def test_no_value_of_the_answer_is_a_float(self):
        got = G.evaluate(loud(), policy(), NOW)
        self.assertEqual(floats(got), [])
        self.assertEqual(got["marks"][0]["measurement"], {"initial": "0.5", "current": "0.75"})

    def test_the_clock_is_not_read(self):
        def read(*args):
            raise AssertionError("the clock was read")
        with mock.patch.object(time, "time", read), mock.patch.object(time, "time_ns", read), \
                mock.patch.object(time, "monotonic", read):
            got = G.evaluate(loud(), policy(), NOW)
        self.assertEqual(got["freezes"][0]["start"], NOW)
        later = G.evaluate(dict(loud(), freezes=[]), policy(), ago(-40))
        self.assertEqual(fired(later), sorted(("budget_usd", "budget_ci_minutes", "drift") + G.MARKS))
        self.assertEqual({row["start"] for row in later["freezes"]}, {ago(-40)})


if __name__ == "__main__":
    unittest.main()
