"""``harness.pass_row``: asama-0/10a's conditions that the toy's and the copy's ``brain/state`` record, judged from
those files (stage 0, (B) step 9; the row of tohum/26d; seed-046's draft for the rest).

The states are written by ``ledger.cycle.plan`` (the cycle's one writer: chained rows, the status row and block, one
signed root per cycle) with ``ledger.events``' rows, the ones ``activate`` and D6-D8 write:

- a world in which every judged condition holds is ``PASS``, with the payload (the copy's genesis and merge row
  hashes, the judged and the listed conditions); the command line gives the same line, exit 0;
- each condition's every reason, one change of the world at a time: the genesis row's place, the
  genesis cycle's ratchet base, a candidate undecided, not merged, merged against its reject or rejected for
  another reason (its first decision is its verdict: a later reject of a merged candidate is not), a candidate
  merge unfinished, flaky or reverted, a ledger ``ledger.serial`` refuses, each drill cause unshown, a drill
  judged ``FAIL`` (cause, not reverted), a plant with no commitment before it, no drill inputs, a root missing
  for a cycle and a root that is not the ledger's, a cycle without its status row, no canary, no ``ok`` canary, a
  served model that is not the requested one, a cost over its cap;
- tohum/26d: the payload's ``stage`` (the integer 0), ``verdict``, ``import_line_sha256`` (the counter's last import
  line) and the (A) result's ``owner_exception`` as written, absent when it has none; the last genesis naming
  another import (each of its three keys); a run with no merge row (``merge_missing``); only the run from the last
  genesis counts (its decisions, merges, ratchet base, canary, plants and their commitments; the copy's last genesis
  and its later merge rows in the payload), and an earlier run's PASS does not refuse the next;
- a state that does not conform to ``ledger.schema`` is ``state_invalid`` under every condition and nothing else;
- expectations that are not ``{decision: merge}`` or ``{decision: reject, reason}``, a counter with no import or not
  a chain, a result the import does not name, without an ``exit`` object or with an owner exception not of
  tohum/02's form, and unreadable command-line inputs are unusable (exit 2);
- ``write`` on the in-process GitHub: a ``PASS`` is one ``brain/state`` commit on the head (``cycle_start``, the
  ``pass`` row with the judged payload, the status row; one root), an append-only extension of the ``ledger.schema``
  shape that is judged ``PASS`` again; a second PASS (``already_passed``) and a ``FAIL`` (``not_pass``) write
  nothing; a moved head and a root that cannot be signed are hard stops with nothing written.

The loop's own drill ledger (D8 over four cycles) is judged in test_loop_write.D8.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from harness import pass_row as PR  # noqa: E402
from harness import revert_drill as RD  # noqa: E402
from ledger import anchor as AN  # noqa: E402
from ledger import chain as CH  # noqa: E402
from ledger import cycle as CY  # noqa: E402
from ledger import events as EV  # noqa: E402
from ledger import schema as SC  # noqa: E402
from target import branches as B  # noqa: E402
from target import land as LN  # noqa: E402
from target import write as W  # noqa: E402
from profile_tree import write_tree  # noqa: E402
from test_revert_drill import ledger_with  # noqa: E402
import yaz_world as YW  # noqa: E402

TS = "2026-11-02T10:00:00Z"
COUNTER = YW.transfer()  # the counter's last import and the (A) result it names
IMPORTS, RESULT = COUNTER["imports"], COUNTER["result"]
OWNER_EXCEPTION = {"anchor": "durustluk", "stage": 0, "carry_to": 1, "reason": "no plant before the stage",
                   "carry_commitment": "c" * 64, "measured": False}
CATALOG = {"instances": [{"id": "rd-build", "cause": "build_break"}, {"id": "rd-lint", "cause": "lint_regression"},
                         {"id": "rd-test", "cause": "test_regression"}]}
SEED = {"seed": "pass-row-seed"}
TOY_EXPECT = {"bad-path": {"decision": "reject", "reason": "security_path:src/p.js"},
              "bad-test": {"decision": "reject", "reason": "tests_red"}, "good": {"decision": "merge"}}
COPY_EXPECT = {"bad-unit": {"decision": "reject", "reason": "tests_red"}, "fix": {"decision": "merge"}}


def h(n: int, width: int = 40) -> str:
    return ("%x" % n).rjust(width, "0")


def genesis_payload(target: str, counter: dict = COUNTER) -> dict:
    return {"target": target, "base_sha": h(1), "referee_tree_sha256": "2" * 64,
            "result_sha256": hashlib.sha256(counter["result"]).hexdigest(),
            "import_line_sha256": counter["line_sha256"], "seed_epoch": {"commit": h(5), "spec_tohum_sha256": h(6, 64),
                                                           "seed_sha256": h(7, 64), "bootstrap_sha256": h(8, 64)},
            "policy_sha256": h(9, 64), "summary_sha256": h(10, 64), "seed_security_ledger_sha256": h(11, 64),
            "seed_security_last_row_hash": h(12, 64), "recipe_sha256": h(13, 64), "facts_sha256": h(14, 64)}


def run_for(instance_id: str, after: int) -> str:
    """The first run id above ``after`` whose key under ``SEED`` selects ``instance_id``."""
    for n in range(after + 1, after + 1000):
        if RD.key(SEED, str(n), CATALOG)["instance_id"] == instance_id:
            return str(n)
    raise AssertionError("no run selects %s" % instance_id)


def cost(c: dict, served=None, outcome="ok", usd=1234, cap=1_000_000) -> dict:
    row = YW.cost_row("cagir-" + c["cycle_id"], usd=usd, outcome=outcome, cap_usd_micros=cap,
                      models_served=["m"] if served is None else served)
    return dict(row, ts=TS)


class State:
    """One target's ``brain/state`` written cycle by cycle with ``ledger.cycle.plan``."""

    def __init__(self, target: str):
        self.target, self.ledger, self.roots, self.status, self.run = target, b"", b"", None, 100

    def cycle(self, *makers, genesis: bool | dict = False, run: str | None = None) -> dict:
        """``genesis``: ``True``, or the genesis payload's changed keys (another import)."""
        self.run = int(run) if run else self.run + 1
        c = {"cycle_id": "%d-1" % self.run, "ts": TS, "snapshot_id": h(99)}
        payload = dict(genesis_payload(self.target), **(genesis if isinstance(genesis, dict) else {}))
        rows = [EV.row(c, "genesis", "genesis", payload)] if genesis is not False else []
        rows += [EV.start(c)]
        for m in makers:  # a maker gives a row or a list of rows (ledger.events.decided)
            made = m(c)
            rows += made if isinstance(made, list) else [made]
        facts = {"ts": TS, "snapshot_id": h(99), "row_id": c["cycle_id"] + ":status",
                 "canary_cap_usd_micros": 1_000_000}
        planned = CY.plan(self.ledger, self.ledger, self.roots, self.roots, self.status, rows, IMPORTS, facts,
                          AN.FakeSigner(True, YW.IDENTITY, "rekor-%d" % self.run), c["cycle_id"] + ":root")
        files = planned["files"]
        self.ledger, self.roots, self.status = files[B.STATE_LEDGER], files[B.STATE_ROOTS], files[B.STATE_STATUS]
        return c

    def files(self) -> dict:
        return {"ledger": self.ledger, "roots": self.roots}


def merged(sha: str, pull: int = 1) -> dict:
    return {"path": "src/a.js", "pull": pull, "head_sha": h(0xbeef), "merge_sha": sha}


def genesis_cycle(state: State, decisions, genesis: bool | dict = True) -> None:
    state.cycle(lambda c: EV.row(c, "cut", "integration_cut", {"branch": B.INTEGRATION, "base_sha": h(1)}),
                lambda c: EV.ratchet_base(c, h(20, 64), {"no-unused-vars": 0}),
                *[(lambda c, d=d: EV.decided(c, *d)) for d in decisions], genesis=genesis)


def drill(state: State, instance_id: str, cause: str, merge_sha: str, revert_cause: str | None = None,
          reverted: bool = True) -> None:
    """Three cycles: the commitment, the plant (with its ratchet base), the revert with ``revert_cause``."""
    run = run_for(instance_id, state.run)
    key = RD.key(SEED, run, CATALOG)
    assert key["cause"] == cause
    state.cycle(lambda c: EV.drill(c, "commit", RD.commit_payload(key)), cost, run=run)
    state.cycle(lambda c: EV.ratchet_base(c, h(21, 64), {"no-unused-vars": 0}),
                lambda c: EV.drill(c, "plant", RD.plant_payload(instance_id, merge_sha)), cost)
    if reverted:
        state.cycle(lambda c: EV.revert(c, merge_sha, revert_cause or cause), cost)


def runs(state: State) -> int:
    """The genesis rows already on ``state``: a later run's merges are other commits (shas shifted by 0x1000)."""
    return sum(1 for line in state.ledger.splitlines() if json.loads(line)["kind"] == "genesis")


def toy_world(toy: State | None = None, **over) -> State:
    """The toy's (B) run; on ``toy`` it is a run after a new genesis (``over["genesis"]``)."""
    toy = toy or State("toy")
    shift = 0x1000 * runs(toy)
    genesis_cycle(toy, over.get("decisions", [("bad-path", ["security_path:src/p.js"]), ("bad-test", ["tests_red"]),
                                              ("good", [], merged(h(0xa1 + shift)))]), over.get("genesis", True))
    toy.cycle(lambda c: EV.sentinel(c, h(0xa1 + shift), over.get("verdict", "green"), []),
              lambda c: cost(c, **over.get("cost", {})))
    for n, (instance_id, cause) in enumerate(over.get("drills", [("rd-test", "test_regression"),
                                                                 ("rd-build", "build_break"),
                                                                 ("rd-lint", "lint_regression")])):
        drill(toy, instance_id, cause, h(0xd0 + n + shift), **over.get("drill_over", {}).get(instance_id, {}))
    return toy


def copy_world(copy: State | None = None, genesis: bool | dict = True) -> State:
    copy = copy or State("copy")
    sha = h(0xc1 + 0x1000 * runs(copy))
    genesis_cycle(copy, [], genesis)
    copy.cycle(lambda c: EV.decided(c, "bad-unit", ["tests_red"]), lambda c: EV.decided(c, "fix", [], merged(sha)),
               cost)
    copy.cycle(lambda c: EV.sentinel(c, sha, "green", []), cost)
    return copy


def judge(toy: State | None = None, copy: State | None = None, drill_inputs=True, toy_expect=None, copy_expect=None,
          counter: dict = COUNTER) -> dict:
    return PR.judge((toy or toy_world()).files(), (copy or copy_world()).files(),
                    TOY_EXPECT if toy_expect is None else toy_expect, COPY_EXPECT if copy_expect is None else copy_expect,
                    {"seed": SEED, "catalog": CATALOG} if drill_inputs else None, counter["imports"], counter["result"])


def raw_cycle(state: State, rows) -> None:
    """Rows chained onto the ledger with no status row and no root: not a cycle ``ledger.cycle`` writes."""
    state.ledger = ledger_with(rows, state.ledger)


class Passes(unittest.TestCase):
    def test_every_judged_condition_holds(self):
        copy = copy_world()
        got = judge(copy=copy)
        self.assertEqual((got["verdict"], got["state"]), ("PASS", {}), got["conditions"])
        self.assertEqual(got["conditions"], {cond: [] for cond in PR.CONDITIONS})
        self.assertEqual(got["not_checked"], PR.NOT_CHECKED)
        rows = [json.loads(line) for line in copy.ledger.splitlines()]
        merge = [r for r in rows if r["kind"] == "merge"]  # tohum/26d's merge rows, not the decision rows
        self.assertEqual([r["payload"]["merge_sha"] for r in merge], [h(0xc1)])
        # tohum/26d's fields: stage the integer 0, the import's line hash, no owner_exception when (A) has none
        self.assertEqual(got["payload"], {"stage": 0, "verdict": "PASS", "import_line_sha256": COUNTER["line_sha256"],
                                          "copy_genesis_row_hash": rows[0]["row_hash"],
                                          "copy_merge_row_hashes": [merge[0]["row_hash"]],
                                          "conditions": sorted(PR.CONDITIONS), "not_checked": sorted(PR.NOT_CHECKED)})
        self.assertIs(type(got["payload"]["stage"]), int)
        self.assertEqual(COUNTER["line_sha256"], hashlib.sha256(IMPORTS.splitlines()[-1]).hexdigest())
        self.assertEqual(SC.payload_reasons("events", "pass", got["payload"]), [])
        self.assertFalse(set(PR.CONDITIONS) & set(PR.NOT_CHECKED))

    def test_the_owner_exception_of_the_a_result_is_carried_as_written(self):
        counter = YW.transfer({"requested": True, "transferable": True, "owner_exception": OWNER_EXCEPTION})
        toy, copy = State("toy"), State("copy")
        toy_world(toy, genesis=genesis_payload("toy", counter))
        copy_world(copy, genesis=genesis_payload("copy", counter))
        got = judge(toy, copy, counter=counter)
        self.assertEqual(got["verdict"], "PASS", got["conditions"])
        self.assertEqual(got["payload"]["owner_exception"], OWNER_EXCEPTION)
        self.assertEqual(got["payload"]["import_line_sha256"], counter["line_sha256"])
        self.assertEqual(SC.payload_reasons("events", "pass", got["payload"]), [])

    def test_a_merged_candidate_offered_again_is_judged_by_its_first_decision(self):
        toy = toy_world()
        toy.cycle(lambda c: EV.decided(c, "good", ["kos:patch_does_not_apply"]), cost)
        self.assertEqual(judge(toy)["verdict"], "PASS")


class Fails(unittest.TestCase):
    def reasons(self, got: dict, cond: str) -> list[str]:
        self.assertEqual(got["verdict"], "FAIL")
        self.assertIsNone(got["payload"])
        return got["conditions"][cond]

    def test_genesis(self):
        toy = State("toy")
        toy.cycle(lambda c: EV.ratchet_base(c, h(20, 64), {}))
        toy.cycle(lambda c: EV.row(c, "genesis", "genesis", genesis_payload("toy")))
        self.assertEqual(self.reasons(judge(toy), "#genesis"), ["toy:genesis_not_first"])
        # the last genesis names another import than the counter's last one: each of the three keys (26d 2, 5)
        other = YW.transfer({"requested": False})
        got = judge(copy=copy_world(State("copy"), genesis_payload("copy", other)))
        self.assertEqual(self.reasons(got, "#genesis"), ["copy:genesis_import:import_line_sha256",
                                                         "copy:genesis_import:result_sha256"])
        got = judge(copy=copy_world(State("copy"), {"referee_tree_sha256": "3" * 64}))
        self.assertEqual(self.reasons(got, "#genesis"), ["copy:genesis_import:referee_tree_sha256"])

    def test_the_genesis_cycles_ratchet_base(self):
        toy = State("toy")
        toy.cycle(genesis=True)
        toy.cycle(lambda c: EV.ratchet_base(c, h(20, 64), {}))
        self.assertEqual(self.reasons(judge(toy), "#taban"), ["toy:base_missing"])

    def test_merge_and_reject_expectations(self):
        toy = toy_world(decisions=[("bad-path", [], merged(h(0xb1))), ("good", ["tests_red"])])
        got = judge(toy, toy_expect=dict(TOY_EXPECT, **{"bad-x": {"decision": "reject", "reason": "tests_red"}}))
        self.assertEqual(got["conditions"]["#merge"], ["toy:not_merged:good"])
        self.assertEqual(got["conditions"]["#ret"], ["toy:merged:bad-path", "toy:undecided:bad-test",
                                                     "toy:undecided:bad-x"])
        toy = toy_world(decisions=[("bad-path", ["security_path:src/p.js", "tests_red"]),
                                   ("bad-test", ["ratchet_increase"])])
        got = judge(toy)
        self.assertEqual(got["conditions"]["#merge"], ["toy:merge_missing", "toy:undecided:good"])
        self.assertEqual(got["conditions"]["#ret"], ["toy:reason_mismatch:bad-path", "toy:reason_mismatch:bad-test"])

    def test_candidate_merges_end_green_and_stay(self):
        self.assertEqual(self.reasons(judge(toy_world(verdict="flaky")), "#nobetci #hayatta"),
                         ["toy:sentinel_flaky:" + h(0xa1)])
        toy = State("toy")
        genesis_cycle(toy, [("good", [], merged(h(0xa1)))])
        self.assertEqual(self.reasons(judge(toy), "#nobetci #hayatta"), ["toy:sentinel_unfinished:" + h(0xa1)])
        toy = State("toy")
        genesis_cycle(toy, [("good", [], merged(h(0xa1)))])
        toy.cycle(lambda c: EV.revert(c, h(0xa1), "test_regression"))
        self.assertEqual(self.reasons(judge(toy), "#nobetci #hayatta"), ["toy:reverted:" + h(0xa1)])
        toy = toy_world()
        toy.cycle(lambda c: EV.revert(c, h(0xa1), "test_regression"), cost)
        self.assertEqual(self.reasons(judge(toy), "#nobetci #hayatta"), ["toy:serial:finished_twice:" + h(0xa1)])

    def test_each_drill_cause_is_shown_by_a_pass(self):
        got = judge(toy_world(drills=[("rd-test", "test_regression")]))
        self.assertEqual(self.reasons(got, "#geri-alma"), ["toy:cause_unshown:build_break",
                                                           "toy:cause_unshown:lint_regression"])
        self.assertEqual(self.reasons(judge(drill_inputs=False), "#geri-alma"), ["toy:drill_inputs_missing"])

    def test_a_drill_judged_fail_is_named(self):
        toy = toy_world(drill_over={"rd-build": {"revert_cause": "test_regression"}})
        self.assertEqual(self.reasons(judge(toy), "#geri-alma"), ["toy:drill_fail:rd-build:cause_mismatch",
                                                                  "toy:cause_unshown:build_break"])
        toy = toy_world(drill_over={"rd-lint": {"reverted": False}})
        self.assertEqual(self.reasons(judge(toy), "#geri-alma"), ["toy:drill_fail:rd-lint:not_reverted",
                                                                  "toy:cause_unshown:lint_regression"])

    def test_a_plant_without_commitment(self):
        toy = toy_world()
        toy.cycle(lambda c: EV.drill(c, "plant", RD.plant_payload("rd-test", h(0xe1))), cost)
        toy.cycle(lambda c: EV.revert(c, h(0xe1), "test_regression"), cost)
        # judged against the last commitment before it, rd-lint's, already used
        self.assertEqual(self.reasons(judge(toy), "#geri-alma"), ["toy:drill_fail:rd-test:cause_mismatch",
                                                                  "toy:drill_fail:rd-test:instance_mismatch"])
        toy = State("toy")
        genesis_cycle(toy, [("bad-path", ["security_path:src/p.js"]), ("bad-test", ["tests_red"]),
                            ("good", [], merged(h(0xa1)))])
        toy.cycle(lambda c: EV.drill(c, "plant", RD.plant_payload("rd-test", h(0xe1))), cost)
        self.assertIn("toy:drill_uncommitted:rd-test", self.reasons(judge(toy), "#geri-alma"))

    def test_roots_and_status(self):
        toy = toy_world()
        raw_cycle(toy, [EV.start({"cycle_id": "900-1", "ts": TS, "snapshot_id": h(99)})])
        got = judge(toy)
        self.assertEqual(got["conditions"]["#kok"], ["toy:roots_per_cycle:11/12", "toy:root_mismatch"])
        self.assertEqual(got["conditions"]["#durum"], ["toy:status_count:900-1:0"])

    def test_the_canary(self):
        toy = State("toy")
        genesis_cycle(toy, [])
        self.assertEqual(self.reasons(judge(toy), "#model #belirtec"), ["toy:canary_missing"])
        toy.cycle(lambda c: cost(c, served=[], outcome="outage"))
        self.assertEqual(self.reasons(judge(toy), "#model #belirtec"), ["toy:canary_not_ok"])
        got = judge(toy_world(cost={"served": ["other"], "usd": 2_000_000}))
        self.assertEqual(got["conditions"]["#model #belirtec"], ["toy:model_mismatch:cagir-102-1",
                                                                 "toy:cap_exceeded:cagir-102-1"])

    def test_a_run_with_no_merge_row(self):
        """26d: the toy's PASS needs a merge row between its last genesis and it; the copy's payload at least one."""
        got = judge(copy_expect={"bad-unit": {"decision": "reject", "reason": "tests_red"}},
                    copy=self.copy_without_merge())
        self.assertEqual(self.reasons(got, "#merge"), ["copy:merge_missing"])
        toy = toy_world(decisions=[("bad-path", ["security_path:src/p.js"]), ("bad-test", ["tests_red"])])
        got = judge(toy, toy_expect={k: v for k, v in TOY_EXPECT.items() if k != "good"})
        self.assertEqual(got["conditions"]["#merge"], ["toy:merge_missing"])

    @staticmethod
    def copy_without_merge() -> State:
        copy = State("copy")
        genesis_cycle(copy, [])
        copy.cycle(lambda c: EV.decided(c, "bad-unit", ["tests_red"]), cost)
        return copy

    def test_the_copy_is_judged_the_same_way_but_for_the_drill(self):
        copy = State("copy")
        genesis_cycle(copy, [("fix", ["tests_red"])])
        got = judge(copy=copy)
        self.assertEqual(got["conditions"]["#merge"], ["copy:merge_missing", "copy:not_merged:fix"])
        self.assertEqual(got["conditions"]["#ret"], ["copy:undecided:bad-unit"])
        self.assertEqual(got["conditions"]["#model #belirtec"], ["copy:canary_missing"])
        self.assertEqual(got["conditions"]["#geri-alma"], [])

    def test_a_state_not_of_the_schema_is_judged_no_further(self):
        toy = toy_world()
        toy.ledger += b'{"not": "a row"}\n'
        got = judge(toy)
        self.assertEqual(got["conditions"], {cond: ["toy:state_invalid"] for cond in PR.CONDITIONS})
        self.assertTrue(got["state"]["toy"])
        self.assertNotIn("copy", got["state"])


class Regenesis(unittest.TestCase):
    """tohum/26d: after a new import each target gets a new genesis and (B) runs again; only its rows count."""

    def test_only_the_run_from_the_last_genesis_counts(self):
        toy, copy = toy_world(), copy_world()
        old_copy_merges = [json.loads(line)["row_hash"] for line in copy.ledger.splitlines()
                           if json.loads(line)["kind"] == "merge"]
        toy.cycle(genesis=True)  # a new genesis, nothing after it yet: the earlier run's rows do not count
        got = judge(toy, copy)
        self.assertEqual(got["conditions"]["#genesis"], [])
        self.assertEqual(got["conditions"]["#merge"], ["toy:merge_missing", "toy:undecided:good"])
        self.assertEqual(got["conditions"]["#ret"], ["toy:undecided:bad-path", "toy:undecided:bad-test"])
        self.assertEqual(got["conditions"]["#geri-alma"], ["toy:cause_unshown:" + c for c in PR.DRILL_CAUSES])
        self.assertEqual(got["conditions"]["#model #belirtec"], ["toy:canary_missing"])
        self.assertEqual(got["conditions"]["#taban"], ["toy:base_missing"])
        # the whole run again on both after a re-import (the first genesis names the earlier import, 26d: it stays):
        # PASS, judged by the last genesis's import; the copy's last genesis and only its later merge rows in the payload
        earlier = {k: v for k, v in genesis_payload("toy", YW.transfer({"requested": False})).items()
                   if k in PR.IMPORT_KEYS}
        toy, copy = toy_world(toy_world(genesis=earlier)), copy_world(copy_world(genesis=earlier))
        got = judge(toy, copy)
        self.assertEqual(got["verdict"], "PASS", got["conditions"])
        rows = [json.loads(line) for line in copy.ledger.splitlines()]
        last = max(i for i, r in enumerate(rows) if r["kind"] == "genesis")
        self.assertGreater(last, 0)
        self.assertEqual(got["payload"]["copy_genesis_row_hash"], rows[last]["row_hash"])
        self.assertEqual(got["payload"]["copy_merge_row_hashes"],
                         [r["row_hash"] for r in rows[last:] if r["kind"] == "merge"])
        self.assertFalse(set(got["payload"]["copy_merge_row_hashes"]) & set(old_copy_merges))

    def test_a_plant_and_its_commitment_count_only_in_the_run(self):
        toy = toy_world(drills=[("rd-test", "test_regression")])
        run = run_for("rd-build", toy.run)
        key = RD.key(SEED, run, CATALOG)
        toy.cycle(lambda c: EV.drill(c, "commit", RD.commit_payload(key)), cost, run=run)  # before the new genesis
        toy_world(toy, drills=[])
        toy.cycle(lambda c: EV.ratchet_base(c, h(21, 64), {"no-unused-vars": 0}),
                  lambda c: EV.drill(c, "plant", RD.plant_payload("rd-build", h(0xe2))), cost)
        toy.cycle(lambda c: EV.revert(c, h(0xe2), "build_break"), cost)
        got = judge(toy)
        self.assertEqual(got["conditions"]["#geri-alma"], ["toy:drill_uncommitted:rd-build",
                                                           "toy:cause_unshown:test_regression",
                                                           "toy:cause_unshown:build_break",
                                                           "toy:cause_unshown:lint_regression"])


class Write(unittest.TestCase):
    """``write`` on the in-process GitHub whose ``brain/state`` holds the toy world's files."""

    HEADS = {B.STATE: h(0x5a), B.INTEGRATION: h(0x1a)}
    REQ = {"cycle_id": "900-1", "ts": TS, "snapshot_id": h(0x1a)}

    def setUp(self) -> None:
        self.toy = toy_world()
        self.gh = YW.github_at(self.HEADS, {"src/a.js": b"var a = 1;\n"},
                               {B.STATE_LEDGER: self.toy.ledger, B.STATE_ROOTS: self.toy.roots,
                                B.STATE_STATUS: self.toy.status})

    def write(self, toy: dict | None = None, head: str | None = None, signer=None, drill_inputs=True,
              req: dict | None = None) -> dict:
        toy = dict(self.toy.files(), status=self.toy.status) if toy is None else toy
        return PR.write(W.Writer(YW.REPO, self.gh), head or self.gh.refs[B.STATE], toy, copy_world().files(),
                        TOY_EXPECT, COPY_EXPECT, {"seed": SEED, "catalog": CATALOG} if drill_inputs else None,
                        req or self.REQ, IMPORTS, RESULT, signer or AN.FakeSigner(True, YW.IDENTITY, "rekor-pass"), 1_000_000)

    def writes(self) -> list:
        return [(m, p) for m, p, _ in self.gh.requests if m != "GET"]

    def state(self) -> dict:
        return {name: self.gh.read_file(B.STATE, path) for name, path in
                (("ledger", B.STATE_LEDGER), ("roots", B.STATE_ROOTS), ("status", B.STATE_STATUS))}

    def test_a_pass_is_one_cycle_on_the_toys_state(self):
        got = self.write()
        self.assertEqual((got["verdict"], got["refused"]), ("PASS", []))
        self.assertEqual(self.gh.refs[B.STATE], got["written"]["state_sha"])
        self.assertEqual(self.gh.commits[got["written"]["state_sha"]]["parents"], [self.HEADS[B.STATE]])
        self.assertEqual(self.gh.refs[B.INTEGRATION], self.HEADS[B.INTEGRATION])
        new = self.state()
        self.assertTrue(CH.verify_bytes(new["ledger"], self.toy.ledger)["valid"])
        self.assertTrue(CH.verify_bytes(new["roots"], self.toy.roots)["valid"])
        self.assertEqual(SC.ledger_reasons(new["ledger"]), [])
        added = [json.loads(line) for line in new["ledger"].splitlines()][len(self.toy.ledger.splitlines()):]
        self.assertEqual([(r["row_id"], r["kind"]) for r in added],
                         [("900-1:start", "cycle_start"), ("900-1:pass", "pass"), ("900-1:status", "status")])
        self.assertEqual(added[1]["payload"], got["payload"])
        # tohum/26d: the referee's own row (no proposed_by, trust verified, derivation tool), part events
        self.assertEqual((added[1]["part"], added[1]["trust"], added[1]["derivation"], "proposed_by" in added[1]),
                         ("events", "verified", "tool", False))
        self.assertEqual([r["row_hash"] for r in added], got["written"]["row_hashes"])
        # the state written is still judged PASS: its cycle has its root and its status row
        self.assertEqual(PR.judge({"ledger": new["ledger"], "roots": new["roots"]}, copy_world().files(), TOY_EXPECT,
                                  COPY_EXPECT, {"seed": SEED, "catalog": CATALOG}, IMPORTS, RESULT)["verdict"], "PASS")
        # a second PASS on it is refused, nothing written
        before = len(self.writes())
        again = self.write(toy=new, head=got["written"]["state_sha"])
        self.assertEqual((again["refused"], again["written"], len(self.writes())), (["already_passed"], None, before))

    def test_a_pass_of_an_earlier_run_does_not_refuse_the_next(self):
        first = self.write()
        toy = State("toy")
        toy.ledger, toy.roots, toy.status, toy.run = (self.state()["ledger"], self.state()["roots"],
                                                       self.state()["status"], 900)
        toy_world(toy)  # a new genesis and the whole (B) run after it
        self.gh = YW.github_at({B.STATE: h(0x5c), B.INTEGRATION: h(0x1a)}, {"src/a.js": b"var a = 1;\n"},
                               {B.STATE_LEDGER: toy.ledger, B.STATE_ROOTS: toy.roots, B.STATE_STATUS: toy.status})
        got = self.write(toy=dict(toy.files(), status=toy.status), req=dict(self.REQ, cycle_id="990-1"))
        self.assertEqual((first["refused"], got["refused"]), ([], []))
        self.assertIsNotNone(got["written"])

    def test_a_fail_writes_nothing(self):
        got = self.write(drill_inputs=False)
        self.assertEqual((got["verdict"], got["refused"], got["written"], self.writes()),
                         ("FAIL", ["not_pass"], None, []))

    def test_a_moved_head_or_an_unsignable_root_is_a_hard_stop_before_any_write(self):
        for kw, cause in (({"head": h(0x5b)}, "state_head_moved"), ({"signer": AN.FakeSigner(False)}, "Unsignable")):
            with self.subTest(cause=cause):
                self.setUp()
                with self.assertRaises(LN.HardStop) as caught:
                    self.write(**kw)
                self.assertIn(cause, str(caught.exception))
                self.assertEqual((caught.exception.written, self.writes()), ([], []))
                self.assertEqual(self.gh.refs[B.STATE], self.HEADS[B.STATE])


class Unusable(unittest.TestCase):
    def test_expectations(self):
        for bad in ([], {"c": {"decision": "merge", "reason": "x"}}, {"c": {"decision": "reject"}},
                    {"c": {"decision": "reject", "reason": ""}}, {"c": {"decision": "hold"}}, {"": {"decision": "merge"}}):
            with self.subTest(bad=bad), self.assertRaises(PR.Unusable):
                PR.judge(toy_world().files(), copy_world().files(), bad, COPY_EXPECT, None, IMPORTS, RESULT)

    def test_the_import_and_the_a_result(self):
        """``imported``: the counter must hold an import, the result must be the one it names and carry an
        ``exit`` object, and an owner exception must be of tohum/02's form."""
        toy, copy = toy_world().files(), copy_world().files()
        no_transfer = YW.chained(YW.IMPORTS_ROWS)
        cases = [(no_transfer, RESULT, "imports_no_transfer"), (IMPORTS[:-5], RESULT, "imports_broken"),
                 (IMPORTS, RESULT + b" ", "not the (A) result")]
        docs = [({"exit": "closed"}, "no exit object"), ([], "not a JSON object")]
        docs += [({"exit": {"owner_exception": bad}}, "owner_exception")
                 for bad in ("durustluk", dict(OWNER_EXCEPTION, anchor="#durustluk"), dict(OWNER_EXCEPTION, measured=0),
                             {k: v for k, v in OWNER_EXCEPTION.items() if k != "stage"}, dict(OWNER_EXCEPTION, extra=1))]
        for doc, fragment in docs:  # each result named by its own import, so only its form is wrong
            result = json.dumps(doc).encode()
            imports = YW.chained(YW.IMPORTS_ROWS + [{"stage": 0, "referee_tree_sha256": "2" * 64,
                                                     "result_sha256": hashlib.sha256(result).hexdigest()}])
            cases.append((imports, result, fragment))
        for imports, result, fragment in cases:
            with self.subTest(fragment=fragment, result=result[:60]):
                with self.assertRaises(PR.Unusable) as caught:
                    PR.judge(toy, copy, TOY_EXPECT, COPY_EXPECT, None, imports, result)
                self.assertIn(fragment, str(caught.exception))


def write_state(root: str, state: State) -> str:
    write_tree(root, {B.STATE_LEDGER: state.ledger, B.STATE_ROOTS: state.roots})
    return root


def write_expect(root: str, expect: dict) -> str:
    write_tree(root, {"%s/expect.json" % cid: doc for cid, doc in expect.items()})
    return root


class CommandLine(unittest.TestCase):
    def run_cli(self, *argv: str):
        proc = subprocess.run([sys.executable, "-m", "harness.pass_row", *argv], cwd=REFEREE, capture_output=True,
                              timeout=120)
        lines = proc.stdout.decode().splitlines()
        return proc.returncode, json.loads(lines[0]) if len(lines) == 1 else lines

    def test_judge_from_files(self):
        with tempfile.TemporaryDirectory() as base:
            toy, copy = write_state(os.path.join(base, "toy"), toy_world()), write_state(os.path.join(base, "copy"),
                                                                                          copy_world())
            te, ce = write_expect(os.path.join(base, "te"), TOY_EXPECT), write_expect(os.path.join(base, "ce"),
                                                                                       COPY_EXPECT)
            write_tree(base, {"catalog.json": CATALOG, "seed.json": SEED, "imports.jsonl": IMPORTS,
                              "result.json": RESULT})
            catalog, seed = os.path.join(base, "catalog.json"), os.path.join(base, "seed.json")
            imports, result = os.path.join(base, "imports.jsonl"), os.path.join(base, "result.json")
            code, line = self.run_cli("judge", toy, copy, te, ce, imports, result, catalog, seed)
            self.assertEqual((code, line), (0, json.loads(json.dumps(judge()))))
            code, line = self.run_cli("judge", toy, copy, te, ce, imports, result)
            self.assertEqual((code, line["verdict"], line["conditions"]["#geri-alma"]),
                             (1, "FAIL", ["toy:drill_inputs_missing"]))
            for argv in (("judge", toy, copy, te, ce), ("judge", toy, copy, te, ce, imports, catalog),
                         ("judge", toy, copy, te, ce, imports, os.path.join(base, "none")),
                         ("judge", toy, copy, te, ce, imports, result, catalog),
                         ("judge", os.path.join(base, "none"), copy, te, ce, imports, result),
                         ("other", toy, copy, te, ce, imports, result)):
                with self.subTest(argv=argv):
                    self.assertEqual(self.run_cli(*argv), (2, {"verdict": "FAIL"}))


if __name__ == "__main__":
    unittest.main()
