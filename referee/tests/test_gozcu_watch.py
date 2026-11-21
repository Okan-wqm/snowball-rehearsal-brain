"""Tests for the watcher in ``yaz`` (P1 MF7's wiring; test 41 of asama-0/09 beside tests/test_gozcu.py, which
proves the rules on declared views; here: that a cycle reads them off its ledger, writes the freeze and is stopped
by it).

What is proven, each by the test named for it:

- ``gozcu.watch.views`` (``Views``): merges and reverts become events at their rows' times with the class ``K0``;
  a planted merge and its revert are no events, another merge's revert in the same ledger is; a freeze row is in
  force until a lift row with its trigger, scope and start, whose ``ts`` is ``lifted``, and a later freeze of the
  same trigger is in force again; a lift naming no freeze in force (none, another start, one already lifted) is
  ``Unusable``; the spend is the cost rows of ``now``'s month only; the unmeasured views are the empty ones the
  module names; a ``now`` that is no ``ts`` is ``Unusable``; ``judge`` reads the planned rows after the ledger's
  and names ``unmeasured``;
- the rows (``Rows``): ``gozcu.watch.rows`` gives a ``freeze`` row per new freeze and a ``lift`` row per lift,
  with the ids and payloads stated, each conforming to ``ledger.schema``; the schema refuses a trigger off
  ``FREEZE_TRIGGERS``, an empty, unsorted or repeated scope, a measurement that is no object of counts, a start
  that is no ``ts``, a missing or extra field, and a lift carrying a measurement; ``gozcu.evaluate.SOFT`` is the
  schema's list;
- the gate's reading (``Closed``, ``Decide``): ``closed`` names a freeze in force whose scope has ``K0`` or
  ``loop``, once per trigger, sorted, and not one of another class or a lifted one; a ledger that does not conform
  is ``ledger.serial.Unusable``; ``loop.decide`` adds the frozen reasons to every candidate, so none merges;
- a cycle (``Budget``, ``Regression``, ``HardStop``, ``Refusals``; ``kos`` then ``yaz`` on the fake GitHub):
  a cycle whose own cost row reaches ``monthly_cap_usd`` writes the ``budget_usd`` freeze after its cost rows in
  the same ``brain/state`` commit, one micro-dollar less writes none; the next cycle's candidate is rejected with
  ``frozen:budget_usd`` alone and no second freeze row is written; the first cycle of the next month writes the
  lift and still rejects (the gate reads written rows), and the one after merges; a cycle that reverts a red merge
  writes the ``regression`` freeze with the counts and the next cycle's candidate is rejected with
  ``frozen:regression``, while with ``min_reverts`` 2 the same reverts freeze nothing and the candidate merges;
  the cycle whose freeze passes ``soft_freeze_limit`` is written and its line is ``hard_stop``, the next cycle
  writes nothing and is ``hard_stop``, and at the limit the cycle is not stopped; a policy value the watcher
  cannot use, or without one of the seven required (tohum/28a), refuses the write (``policy_invalid:<path>``,
  nothing written; ``loop.write_cycle.write`` itself, since the job stops before it: ``tests/test_drift.py``'s
  ``YazPolicy``); a ledger whose lift names no freeze is ``state_refused`` (nothing written;
  ``loop.write_cycle.write`` itself: ``Unusable``); without the six thresholds that are not required the cycle
  is written and its line names those six paths unjudged and the unmeasured views.

Not proven here: the rules themselves (tests/test_gozcu.py); anything on a real ledger or GitHub; the views this
loop does not measure (``gozcu.watch.UNMEASURED``); the genesis cycle, which the watcher does not read.
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gozcu import evaluate as GE  # noqa: E402
from gozcu import watch as GW  # noqa: E402
from ledger import events as EV  # noqa: E402
from ledger import schema as SC  # noqa: E402
from ledger import serial as SE  # noqa: E402
from loop import job as J  # noqa: E402
from loop import pulled as P  # noqa: E402
from loop import write_cycle as WC  # noqa: E402
from policy import reads as R  # noqa: E402
from target import branches as B  # noqa: E402
from target import write as W  # noqa: E402
from test_kos import BREAKS_TEST, GOOD  # noqa: E402
from test_loop_cagir import policy as cagir_policy  # noqa: E402
from test_loop_kos import HEADS, candidate  # noqa: E402
from test_loop_write import (GENESIS_TS, RED_AT_HEAD, SENTINEL_UNITS, StateBase, Watching, genesis_state,  # noqa: E402
                             rows_of)
from test_loop_yaz import OPEN, YazBase  # noqa: E402
import yaz_world as YW  # noqa: E402

NOV, NOV2, DEC = "2026-11-01T17:00:00Z", "2026-11-20T09:00:00Z", "2026-12-01T00:00:00Z"
SHA, SHA2 = "1" * 40, "2" * 40
USD = 1_000_000
QUIET = {"hard_stop": [], "freezes": [], "lifts": [], "marks": []}


def cyc(ts: str = NOV, cycle_id: str = "c") -> dict:
    return {"cycle_id": cycle_id, "ts": ts, "snapshot_id": HEADS[B.INTEGRATION]}


def merge(sha: str, ts: str = NOV) -> dict:
    return EV.row(cyc(ts), "m:" + sha, "merge", {"merge_sha": sha})


def plant(sha: str, ts: str = NOV) -> dict:
    return EV.row(cyc(ts), "drill", "plant", {"merge_sha": sha}, part="drill")


def revert(sha: str, ts: str = NOV) -> dict:
    return EV.revert(cyc(ts), sha, "test_regression")


def cost(usd: int, ts: str = NOV, row_id: str = "cost") -> dict:
    return dict(YW.cost_row(row_id, usd=usd), ts=ts)


def frozen(trigger: str = "regression", scope: tuple = ("K0",), start: str = NOV, **measurement) -> dict:
    return {"trigger": trigger, "scope": list(scope), "measurement": measurement, "start": start}


def lifted(trigger: str = "budget_usd", scope: tuple = ("loop",), start: str = NOV) -> dict:
    return {"trigger": trigger, "scope": list(scope), "start": start}


def freeze_rows(ts: str, freezes: tuple = (), lifts: tuple = (), cycle_id: str = "c") -> list[dict]:
    return GW.rows(cyc(ts, cycle_id), {"freezes": list(freezes), "lifts": list(lifts)})


def policy_of(cap: int | None = None, min_reverts: int | None = None, limit: int | None = None) -> dict:
    """test_loop_cagir's policy with the watcher's thresholds named: the cap in USD, the regression rule with
    ``min_reverts`` (the rate rule out of reach: 50 merges), ``soft_freeze_limit`` in a 14 day window."""
    doc = json.loads(cagir_policy())
    if cap is not None:
        doc["constitutional"]["monthly_cap_usd"] = cap
    if min_reverts is not None:
        doc["constitutional"]["regression_freeze"] = {"min_merges": 50, "window_days": 30, "revert_rate": "0.020000",
                                                      "min_reverts": min_reverts}
    if limit is not None:
        doc["constitutional"]["gate_rules"] = {"soft_freeze_limit": limit}
        doc["performance"] = {"windows": {"measure": 14}}
    return doc


class Views(unittest.TestCase):
    def test_merges_and_reverts_are_events_of_class_k0_at_their_rows_times(self):
        got = GW.views([merge(SHA, NOV), revert(SHA, NOV2), EV.start(cyc())], NOV2)
        self.assertEqual(got["events"], [{"ts": NOV, "kind": "merge", "class": "K0"},
                                         {"ts": NOV2, "kind": "revert", "class": "K0"}])

    def test_a_planted_merge_and_its_revert_are_no_events(self):
        got = GW.views([plant(SHA), merge(SHA2), revert(SHA, NOV2), revert(SHA2, DEC)], DEC)
        self.assertEqual(got["events"], [{"ts": NOV, "kind": "merge", "class": "K0"},
                                         {"ts": DEC, "kind": "revert", "class": "K0"}])

    def test_a_freeze_is_in_force_until_its_lift(self):
        budget = frozen("budget_usd", ("loop",), NOV, spent=5, cap=5)
        rows = freeze_rows(NOV, [frozen(merges=1, reverts=1, window_days=30), budget])
        self.assertEqual(GW.views(rows, NOV2)["freezes"],
                         [{"trigger": "regression", "scope": ["K0"], "start": NOV, "lifted": None},
                          {"trigger": "budget_usd", "scope": ["loop"], "start": NOV, "lifted": None}])
        rows += freeze_rows(NOV2, lifts=[lifted()])
        self.assertEqual(GW.views(rows, NOV2)["freezes"],
                         [{"trigger": "regression", "scope": ["K0"], "start": NOV, "lifted": None},
                          {"trigger": "budget_usd", "scope": ["loop"], "start": NOV, "lifted": NOV2}])
        rows += freeze_rows(DEC, [dict(budget, start=DEC)])
        self.assertEqual(GW.views(rows, DEC)["freezes"][1:],
                         [{"trigger": "budget_usd", "scope": ["loop"], "start": NOV, "lifted": NOV2},
                          {"trigger": "budget_usd", "scope": ["loop"], "start": DEC, "lifted": None}])

    def test_a_lift_of_no_freeze_in_force_is_unusable(self):
        budget = freeze_rows(NOV, [frozen("budget_usd", ("loop",), NOV, spent=5, cap=5)])
        for name, rows in (("none", freeze_rows(NOV2, lifts=[lifted()])),
                           ("another start", budget + freeze_rows(NOV2, lifts=[lifted(start=NOV2)])),
                           ("another scope", budget + freeze_rows(NOV2, lifts=[lifted(scope=("K0",))])),
                           ("another trigger", budget + freeze_rows(NOV2, lifts=[lifted("budget_ci_minutes")])),
                           ("lifted already", budget + freeze_rows(NOV2, lifts=[lifted()])
                            + freeze_rows(DEC, lifts=[lifted()]))):
            with self.subTest(name), self.assertRaises(GW.Unusable) as ctx:
                GW.views(rows, DEC)
            self.assertEqual(str(ctx.exception), "row c:lift:%s lifts no freeze in force" %
                             rows[-1]["payload"]["trigger"])

    def test_the_spend_is_the_cost_rows_of_nows_month(self):
        rows = [cost(7, "2026-10-31T23:59:59Z", "a"), cost(30, NOV, "b"), merge(SHA), cost(500, NOV2, "c"),
                cost(1000, DEC, "d"), cost(20000, "2025-11-05T00:00:00Z", "e")]
        self.assertEqual(GW.views(rows, "2026-11-30T23:59:59Z")["spend"], {"usd_micros": 530, "ci_minutes": 0})
        self.assertEqual(GW.views(rows, DEC)["spend"], {"usd_micros": 1000, "ci_minutes": 0})
        self.assertEqual(GW.views(rows, "2027-01-01T00:00:00Z")["spend"], {"usd_micros": 0, "ci_minutes": 0})

    def test_what_is_not_measured_is_empty_and_named(self):
        got = GW.views([merge(SHA), cost(5)], NOV)
        self.assertEqual({k: got[k] for k in ("containment", "stops", "thresholds", "similarities", "genesis")},
                         {"containment": [], "stops": {}, "thresholds": [], "similarities": [],
                          "genesis": {"drafts": 0, "queue": 0}})
        self.assertEqual(sorted(got), sorted(GE.VIEWS))
        self.assertEqual(GW.UNMEASURED, ("containment", "genesis", "similarities", "spend.ci_minutes", "stops",
                                         "thresholds"))

    def test_a_now_that_is_no_ts_is_unusable(self):
        for now in ("2026-11-01", None, 5, "2026-11-01T17:00:00+00:00"):
            with self.subTest(now=now), self.assertRaises(GW.Unusable):
                GW.views([], now)

    def test_judge_reads_the_planned_rows_after_the_ledgers(self):
        policy = policy_of(cap=1)
        quiet = dict(QUIET, unjudged=GW.judge([], [], policy, NOV)["unjudged"], unmeasured=list(GW.UNMEASURED))
        self.assertEqual(quiet["unjudged"], sorted(R.dotted(p) for p in R.GOZCU_PATHS if p not in R.REQUIRED))
        self.assertEqual(len(quiet["unjudged"]), 6)
        self.assertEqual(GW.judge([cost(USD - 1, row_id="a")], [], policy, NOV), quiet)
        fired = dict(quiet, freezes=[frozen("budget_usd", ("loop",), NOV, spent=USD, cap=USD)])
        self.assertEqual(GW.judge([cost(USD - 1, row_id="a")], [cost(1, row_id="b")], policy, NOV), fired)
        self.assertEqual(GW.judge([], [cost(USD)], policy, NOV), fired)
        # the ledger's freeze is read too: in force, so no second one, and lifted by a month with no spend
        written = [cost(USD)] + freeze_rows(NOV, fired["freezes"])
        self.assertEqual(GW.judge(written, [], policy, NOV2), quiet)
        self.assertEqual(GW.judge(written, [], policy, DEC), dict(quiet, lifts=[lifted()]))


class Rows(unittest.TestCase):
    def test_a_freeze_row_and_a_lift_row_per_answer(self):
        one = frozen(merges=1, reverts=1, window_days=30)
        two = frozen("budget_usd", ("loop",), NOV2, spent=5, cap=5)
        got = GW.rows(cyc(NOV2, "77-1"), {"freezes": [one, two], "lifts": [lifted("budget_ci_minutes")]})
        self.assertEqual([(r["row_id"], r["part"], r["kind"], r["payload"]) for r in got],
                         [("77-1:freeze:regression", "freeze", "freeze", one),
                          ("77-1:freeze:budget_usd", "freeze", "freeze", two),
                          ("77-1:lift:budget_ci_minutes", "freeze", "lift", lifted("budget_ci_minutes"))])
        for row in got:
            self.assertEqual((row["ts"], row["snapshot_id"], row["derivation"], row["trust"]),
                             (NOV2, HEADS[B.INTEGRATION], "tool", "verified"))
            self.assertEqual(SC.row_reasons(dict(row, prev_hash="0" * 64, row_hash="0" * 64)), [])
        self.assertEqual(GW.rows(cyc(), dict(QUIET)), [])

    def test_the_schema_refuses_a_freeze_off_its_shape(self):
        good = frozen(merges=1, reverts=1, window_days=30)
        self.assertEqual(SC.payload_reasons("freeze", "freeze", good), [])
        for trigger in SC.FREEZE_TRIGGERS:
            self.assertEqual(SC.payload_reasons("freeze", "freeze", dict(good, trigger=trigger)), [])
        without = {k: v for k, v in good.items() if k != "measurement"}
        for name, bad in (("trigger", dict(good, trigger="oscillation")), ("empty scope", dict(good, scope=[])),
                          ("unsorted scope", dict(good, scope=["K1", "K0"])),
                          ("repeated scope", dict(good, scope=["K0", "K0"])),
                          ("scope of no names", dict(good, scope=[1])), ("scope no list", dict(good, scope="K0")),
                          ("float", dict(good, measurement={"rate": 0.5})),
                          ("negative", dict(good, measurement={"reverts": -1})),
                          ("measurement no object", dict(good, measurement=[1])),
                          ("start", dict(good, start="2026-11-01")), ("extra", dict(good, lifted=None)),
                          ("no measurement", without), ("no trigger", {k: v for k, v in good.items() if k != "trigger"}),
                          ("no scope", {k: v for k, v in good.items() if k != "scope"}),
                          ("no start", {k: v for k, v in good.items() if k != "start"})):
            with self.subTest(name):
                self.assertNotEqual(SC.payload_reasons("freeze", "freeze", bad), [])
        self.assertEqual(SC.payload_reasons("freeze", "lift", without), [])
        for name, bad in (("measurement", good), ("trigger", dict(without, trigger="x")),
                          ("scope", dict(without, scope=[])), ("start", dict(without, start=None)),
                          ("no start", {k: v for k, v in without.items() if k != "start"})):
            with self.subTest("lift " + name):
                self.assertNotEqual(SC.payload_reasons("freeze", "lift", bad), [])
        self.assertNotEqual(SC.payload_reasons("freeze", "hard_stop", good), [])

    def test_the_rules_triggers_are_the_schemas(self):
        self.assertIs(GE.SOFT, SC.FREEZE_TRIGGERS)
        self.assertEqual(SC.FREEZE_TRIGGERS, ("regression", "containment", "budget_usd", "budget_ci_minutes"))


class Closed(unittest.TestCase):
    def closed(self, *rows: dict) -> list[str]:
        return GW.closed(genesis_state(rows)[B.STATE_LEDGER])

    def test_a_freeze_in_force_of_k0_or_the_loop_closes(self):
        k0 = frozen(merges=1, reverts=1, window_days=30)
        budget = frozen("budget_usd", ("loop",), GENESIS_TS, spent=5, cap=5)
        self.assertEqual(self.closed(), [])
        self.assertEqual(self.closed(*freeze_rows(GENESIS_TS, [k0])), ["frozen:regression"])
        self.assertEqual(self.closed(*freeze_rows(GENESIS_TS, [budget])), ["frozen:budget_usd"])
        self.assertEqual(self.closed(*freeze_rows(GENESIS_TS, [k0, budget])), ["frozen:budget_usd", "frozen:regression"])
        both = dict(k0, trigger="containment", scope=["K0", "K3"], measurement={"violations": 2, "window_days": 14})
        self.assertEqual(self.closed(*freeze_rows(GENESIS_TS, [both])), ["frozen:containment"])

    def test_another_class_or_a_lifted_freeze_does_not(self):
        other = frozen(scope=("K1", "K3"), merges=1, reverts=1, window_days=30)
        self.assertEqual(self.closed(*freeze_rows(GENESIS_TS, [other])), [])
        budget = frozen("budget_usd", ("loop",), GENESIS_TS, spent=5, cap=5)
        rows = freeze_rows(GENESIS_TS, [budget]) + freeze_rows(GENESIS_TS, lifts=[lifted(start=GENESIS_TS)], cycle_id="d")
        self.assertEqual(self.closed(*rows), [])
        again = freeze_rows(GENESIS_TS, [budget], cycle_id="e")
        self.assertEqual(self.closed(*(rows + again)), ["frozen:budget_usd"])
        # one trigger in force twice (two classes' freezes) is one reason
        two = freeze_rows(GENESIS_TS, [frozen(merges=1, reverts=1, window_days=30)]) + freeze_rows(
            GENESIS_TS, [frozen(scope=("K0", "K2"), merges=1, reverts=1, window_days=30)], cycle_id="d")
        self.assertEqual(self.closed(*two), ["frozen:regression"])

    def test_a_ledger_that_does_not_conform_is_unusable(self):
        ledger = genesis_state()[B.STATE_LEDGER]
        with self.assertRaises(SE.Unusable):
            GW.closed(ledger + b"{}\n")
        with self.assertRaises(GW.Unusable):
            self.closed(*freeze_rows(GENESIS_TS, lifts=[lifted()]))


class Decide(YazBase):
    def test_a_frozen_gate_merges_nothing(self):
        self.kos({"good": candidate(GOOD), "breaks": candidate(BREAKS_TEST)})
        open_ = self.decide()
        self.assertEqual((open_["merge"], open_["decisions"]["good"]), ("good", {"decision": "merge", "reasons": []}))
        got = self.decide(frozen=["frozen:regression", "frozen:budget_usd"])
        self.assertIsNone(got["merge"])
        self.assertEqual(got["decisions"]["good"],
                         {"decision": "reject", "reasons": ["frozen:budget_usd", "frozen:regression"]})
        own = [r for r in open_["decisions"]["breaks"]["reasons"] if r != "sentinel_pending"]
        self.assertTrue(own)
        self.assertEqual(got["decisions"]["breaks"],
                         {"decision": "reject", "reasons": sorted(own + ["frozen:budget_usd", "frozen:regression"])})


class Watched:
    """A ``StateBase`` whose policy is ``self.policy_doc`` and whose ``yaz`` runs at ``self.now``."""

    policy_doc: dict = {}
    now = YW.NOW

    def write_pulled(self, cands=None, **kw) -> dict:
        kw.setdefault("policy", json.dumps(self.policy_doc).encode())
        return super().write_pulled(cands, **kw)

    def run_yaz(self, **env) -> dict:
        return self.line(J.run("yaz", YW.env(self.temp, self.workspace, **env), transport=self.gh,
                               signer=self.signer, now=lambda: self.now))

    def respond(self, usd: int, run_id: str = "9") -> None:
        """This cycle's response rewritten with one cost row of ``usd`` micro-dollars at ``self.now``."""
        art = P.read(self.pulled)
        shutil.rmtree(os.path.join(self.temp, "in", "response"))
        row = dict(YW.cost_row("cagir-%s-1" % run_id, art.heads[B.INTEGRATION], usd=usd),
                   ts=self.now.strftime("%Y-%m-%dT%H:%M:%SZ"))
        YW.write_response(self.temp, "t1", art.heads, [row])

    def first(self, usd: int, cands: dict | None = None) -> dict:
        """Cycle 9-1 with ``cands``, its call costing ``usd``."""
        self.kos(cands or {})
        self.control(OPEN)
        self.github()
        self.respond(usd)
        return self.run_yaz()

    def then(self, run_id: str, cands: dict | None = None, usd: int = 1234, units=None) -> dict:
        """Cycle ``<run_id>-1`` on what the last one wrote."""
        self.next_cycle(cands or {}, run_id, units=units)
        self.respond(usd, run_id)
        return self.run_yaz(GITHUB_RUN_ID=run_id)

    def added(self) -> list[dict]:
        """The rows the last cycle added to the state it read."""
        return rows_of(self.state_file(B.STATE_LEDGER))[len(rows_of(self.state[B.STATE_LEDGER])):]

    def kinds(self) -> list[tuple]:
        return [(r["row_id"], r["kind"]) for r in self.added()]


class Budget(Watched, StateBase):
    policy_doc = policy_of(cap=1)

    def test_the_cycle_that_reaches_the_cap_writes_the_freeze(self):
        out = self.first(USD, {"good": candidate(GOOD)})
        self.assertEqual((out["ok"], out["merge"]), (True, "good"))   # the gate reads written rows: none yet
        freeze = frozen("budget_usd", ("loop",), YW.TS, spent=USD, cap=USD)
        self.assertEqual(self.kinds()[-3:], [("cagir-9-1", "cost"), ("9-1:freeze:budget_usd", "freeze"),
                                             ("9-1:status", "status")])
        row = self.added()[-2]
        self.assertEqual((row["part"], row["payload"], row["ts"]), ("freeze", freeze, YW.TS))
        self.assertEqual(SC.ledger_reasons(self.state_file(B.STATE_LEDGER)), [])
        self.assertEqual({k: out["written"]["gozcu"][k] for k in QUIET}, dict(QUIET, freezes=[freeze]))
        self.assertEqual(len([p for m, p in self.writes() if p.endswith("git/refs/heads/brain/state")]), 1)
        self.assertEqual(GW.closed(self.state_file(B.STATE_LEDGER)), ["frozen:budget_usd"])

    def test_one_micro_dollar_under_the_cap_freezes_nothing(self):
        out = self.first(USD - 1)
        self.assertTrue(out["ok"])
        self.assertEqual(self.kinds()[-2:], [("cagir-9-1", "cost"), ("9-1:status", "status")])
        self.assertEqual(out["written"]["gozcu"]["freezes"], [])

    def test_a_budget_freeze_closes_the_gate_until_the_month_after_its_lift(self):
        self.now = datetime.datetime(2026, 10, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)
        self.assertTrue(self.first(USD)["ok"])
        good = {"good": candidate(GOOD)}
        out = self.then("10", good)
        self.assertEqual((out["ok"], out["merge"], out["decisions"]),
                         (True, None, {"good": {"decision": "reject", "reasons": ["frozen:budget_usd"]}}))
        self.assertEqual(self.kinds(), [("10-1:start", "cycle_start"), ("10-1:c:good", "decision"),
                                        ("cagir-10-1", "cost"), ("10-1:status", "status")])  # no second freeze
        self.assertEqual(self.gh.refs[B.INTEGRATION], HEADS[B.INTEGRATION])
        self.now = datetime.datetime(2026, 11, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)   # the month turns
        out = self.then("11", good)
        self.assertEqual((out["ok"], out["merge"], out["decisions"]["good"]["reasons"]),
                         (True, None, ["frozen:budget_usd"]))
        self.assertEqual(self.kinds()[-2:], [("11-1:lift:budget_usd", "lift"), ("11-1:status", "status")])
        self.assertEqual(self.added()[-2]["payload"], lifted(start="2026-10-31T23:59:59Z"))
        self.assertEqual(out["written"]["gozcu"]["lifts"], [lifted(start="2026-10-31T23:59:59Z")])
        self.assertEqual(SC.ledger_reasons(self.state_file(B.STATE_LEDGER)), [])
        out = self.then("12", good)
        self.assertEqual((out["ok"], out["merge"], out["decisions"]["good"]["reasons"]), (True, "good", []))
        self.assertNotIn("freeze", [r["part"] for r in self.added()])


class Regression(Watched, Watching):
    def reverted(self, min_reverts: int) -> dict:
        """Cycle 9-1 merges a candidate the sentinel sees red, cycle 10-1 reverts it; cycle 10-1's line."""
        self.policy_doc = policy_of(min_reverts=min_reverts)
        self.merged_then_watched(RED_AT_HEAD)
        out = self.run_yaz(GITHUB_RUN_ID="10")
        self.assertEqual((out["ok"], out["written"]["revert"]["cause"]), (True, "test_regression"))
        return out

    def test_a_revert_that_reaches_min_reverts_freezes_the_class(self):
        out = self.reverted(1)
        freeze = frozen("regression", ("K0",), YW.TS, merges=1, reverts=1, window_days=30)
        self.assertEqual(self.kinds()[-4:], [("10-1:revert", "revert"), ("cagir-10-1", "cost"),
                                             ("10-1:freeze:regression", "freeze"), ("10-1:status", "status")])
        self.assertEqual(self.added()[-2]["payload"], freeze)
        self.assertEqual(out["written"]["gozcu"]["freezes"], [freeze])
        out = self.then("11", {"good": candidate(GOOD)}, units=SENTINEL_UNITS)
        self.assertEqual((out["ok"], out["merge"], out["decisions"]),
                         (True, None, {"good": {"decision": "reject", "reasons": ["frozen:regression"]}}))
        [decision] = [r for r in self.added() if r["kind"] == "decision"]
        self.assertEqual(decision["cause"], "unknown")   # no cause of tohum/26 names a closed gate
        self.assertNotIn("freeze", [r["part"] for r in self.added()])   # in force: not started again

    def test_under_min_reverts_the_same_revert_freezes_nothing(self):
        out = self.reverted(2)
        self.assertEqual(self.kinds()[-3:], [("10-1:revert", "revert"), ("cagir-10-1", "cost"),
                                             ("10-1:status", "status")])
        self.assertEqual(out["written"]["gozcu"]["freezes"], [])
        out = self.then("11", {"good": candidate(GOOD)}, units=SENTINEL_UNITS)
        self.assertEqual((out["ok"], out["merge"]), (True, "good"))


class HardStop(Watched, StateBase):
    def setUp(self) -> None:
        super().setUp()
        self.old = frozen("regression", ("K3",), GENESIS_TS, merges=0, reverts=2, window_days=30)
        self.state = genesis_state(freeze_rows(GENESIS_TS, [self.old], cycle_id="g"))

    def test_the_cycle_that_passes_the_limit_is_written_and_the_next_writes_nothing(self):
        self.policy_doc = policy_of(cap=1, limit=1)
        out = self.first(USD)
        stop = [{"trigger": "soft_freeze_limit",
                 "evidence": ["budget_usd@%s" % YW.TS, "regression@%s" % GENESIS_TS]}]
        self.assertEqual((out["ok"], out["reason"], out["done"]), (False, "hard_stop", ["D5", "D6"]))
        self.assertEqual(out["written"]["gozcu"]["hard_stop"], stop)
        self.assertEqual(self.kinds()[-2:], [("9-1:freeze:budget_usd", "freeze"), ("9-1:status", "status")])
        head, requests = self.gh.refs[B.STATE], len(self.writes())
        self.next_cycle({"good": candidate(GOOD)}, "10")
        requests = len(self.writes())
        out = self.run_yaz(GITHUB_RUN_ID="10")
        self.assertEqual((out["ok"], out["reason"], out["reasons"], out["written"]),
                         (False, "hard_stop", ["gozcu: soft_freeze_limit (written: nothing)"], []))
        self.assertEqual((self.gh.refs[B.STATE], len(self.writes())), (head, requests))

    def test_at_the_limit_the_cycle_is_not_stopped(self):
        self.policy_doc = policy_of(cap=1, limit=2)
        out = self.first(USD)
        self.assertEqual((out["ok"], out["written"]["gozcu"]["hard_stop"]), (True, []))
        self.assertEqual(self.kinds()[-2:], [("9-1:freeze:budget_usd", "freeze"), ("9-1:status", "status")])
        self.assertTrue(self.then("10")["ok"])


class Refusals(Watched, StateBase):
    def test_a_threshold_the_watcher_cannot_use_refuses_the_write(self):
        """``write_cycle.write`` itself, called on a ``pulled`` whose policy the job's own stop (``yaz_policy``,
        shown in ``test_loop_yaz``) would not have let through: refused before any write, absent or off its form."""
        zero = policy_of(cap=1)
        zero["constitutional"]["monthly_cap_usd"] = 0
        self.assertEqual(self.refused_write(zero), ["policy_invalid:constitutional.monthly_cap_usd"])

    def test_a_required_threshold_absent_refuses_the_write(self):
        absent = policy_of()
        del absent["constitutional"]["regression_freeze"]["min_reverts"]
        self.assertEqual(self.refused_write(absent), ["policy_invalid:constitutional.regression_freeze.min_reverts"])

    def refused_write(self, doc: dict) -> list[str]:
        self.policy_doc = doc
        self.kos({})
        self.github()
        with self.assertRaises(WC.Refused) as ctx:
            WC.write(P.read(self.pulled), self.src, {"decisions": {}, "merge": None}, [],
                     W.Writer(YW.REPO, self.gh), self.signer, b"", "9-1", YW.TS)
        self.assertEqual(self.writes(), [])
        return ctx.exception.reasons

    def test_a_lift_of_no_freeze_refuses_the_state(self):
        self.state = genesis_state(freeze_rows(GENESIS_TS, lifts=[lifted(start=GENESIS_TS)], cycle_id="g"))
        self.policy_doc = policy_of(cap=1)
        out = self.first(5, {"good": candidate(GOOD)})
        self.assertEqual((out["ok"], out["reason"], out["reasons"]),
                         (False, "state_refused", ["row g:lift:budget_usd lifts no freeze in force"]))
        self.assertEqual(self.writes(), [])
        with self.assertRaises(WC.Unusable) as ctx:
            WC.write(P.read(self.pulled), self.src, {"decisions": {}, "merge": None}, [], W.Writer(YW.REPO, self.gh),
                     self.signer, b"", "9-1", YW.TS)
        self.assertEqual(str(ctx.exception), "gozcu: row g:lift:budget_usd lifts no freeze in force")
        self.assertEqual(self.writes(), [])

    def test_without_the_six_thresholds_not_required_the_cycle_is_written_and_says_what_was_not_judged(self):
        self.policy_doc = policy_of()
        out = self.first(USD, {"good": candidate(GOOD)})
        self.assertEqual((out["ok"], out["merge"]), (True, "good"))
        unjudged = sorted(R.dotted(p) for p in R.GOZCU_PATHS if p not in R.REQUIRED)
        self.assertEqual(out["written"]["gozcu"], dict(QUIET, unjudged=unjudged, unmeasured=list(GW.UNMEASURED)))
        self.assertEqual(len(unjudged), 6)
        self.assertNotIn("freeze", [r["part"] for r in self.added()])


if __name__ == "__main__":
    unittest.main()
