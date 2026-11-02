"""``harness.pass_row``: asama-0/10a's conditions that the toy's and the copy's ``brain/state`` record, judged from
those files (stage 0, (B) step 9; seed-046's draft).

The states are written by ``ledger.cycle.plan`` (the cycle's one writer: chained rows, the status row and block, one
signed root per cycle) with ``ledger.events``' rows, the ones ``activate`` and D6-D8 write:

- a world in which every judged condition holds is ``PASS``, with the payload (the copy's genesis and merge row
  hashes, the judged and the listed conditions); the command line gives the same line, exit 0;
- each condition's every reason, one change of the world at a time: the genesis row's place and repetition, the
  genesis cycle's ratchet base, a candidate undecided, not merged, merged against its reject or rejected for
  another reason (its first decision is its verdict: a later reject of a merged candidate is not), a candidate
  merge unfinished, flaky or reverted, a ledger ``ledger.serial`` refuses, each drill cause unshown, a drill
  judged ``FAIL`` (cause, not reverted), a plant with no commitment before it, no drill inputs, a root missing
  for a cycle and a root that is not the ledger's, a cycle without its status row, no canary, no ``ok`` canary, a
  served model that is not the requested one, a cost over its cap;
- a state that does not conform to ``ledger.schema`` is ``state_invalid`` under every condition and nothing else;
- expectations that are not ``{decision: merge}`` or ``{decision: reject, reason}`` and unreadable command-line
  inputs are unusable (exit 2);
- ``write`` on the in-process GitHub: a ``PASS`` is one ``brain/state`` commit on the head (``cycle_start``, the
  ``pass`` row with the judged payload, the status row; one root), an append-only extension of the ``ledger.schema``
  shape that is judged ``PASS`` again; a second PASS (``already_passed``) and a ``FAIL`` (``not_pass``) write
  nothing; a moved head and a root that cannot be signed are hard stops with nothing written.

The loop's own drill ledger (D8 over four cycles) is judged in test_loop_write.D8.
"""

from __future__ import annotations

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
IMPORTS = YW.chained(YW.IMPORTS_ROWS)
CATALOG = {"instances": [{"id": "rd-build", "cause": "build_break"}, {"id": "rd-lint", "cause": "lint_regression"},
                         {"id": "rd-test", "cause": "test_regression"}]}
SEED = {"seed": "pass-row-seed"}
TOY_EXPECT = {"bad-path": {"decision": "reject", "reason": "security_path:src/p.js"},
              "bad-test": {"decision": "reject", "reason": "tests_red"}, "good": {"decision": "merge"}}
COPY_EXPECT = {"bad-unit": {"decision": "reject", "reason": "tests_red"}, "fix": {"decision": "merge"}}


def h(n: int, width: int = 40) -> str:
    return ("%x" % n).rjust(width, "0")


def genesis_payload(target: str) -> dict:
    return {"target": target, "base_sha": h(1), "referee_tree_sha256": h(2, 64), "result_sha256": h(3, 64),
            "import_line_sha256": h(4, 64), "seed_epoch": {"commit": h(5), "spec_tohum_sha256": h(6, 64),
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

    def cycle(self, *makers, genesis: bool = False, run: str | None = None) -> dict:
        self.run = int(run) if run else self.run + 1
        c = {"cycle_id": "%d-1" % self.run, "ts": TS, "snapshot_id": h(99)}
        rows = [EV.row(c, "genesis", "genesis", genesis_payload(self.target))] if genesis else []
        rows += [EV.start(c)] + [m(c) for m in makers]
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


def genesis_cycle(state: State, decisions) -> None:
    state.cycle(lambda c: EV.row(c, "cut", "integration_cut", {"branch": B.INTEGRATION, "base_sha": h(1)}),
                lambda c: EV.ratchet_base(c, h(20, 64), {"no-unused-vars": 0}),
                *[(lambda c, d=d: EV.decision(c, *d)) for d in decisions], genesis=True)


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


def toy_world(**over) -> State:
    toy = State("toy")
    genesis_cycle(toy, over.get("decisions", [("bad-path", ["security_path:src/p.js"]), ("bad-test", ["tests_red"]),
                                              ("good", [], merged(h(0xa1)))]))
    toy.cycle(lambda c: EV.sentinel(c, h(0xa1), over.get("verdict", "green"), [], h(30, 64)),
              lambda c: cost(c, **over.get("cost", {})))
    for n, (instance_id, cause) in enumerate(over.get("drills", [("rd-test", "test_regression"),
                                                                 ("rd-build", "build_break"),
                                                                 ("rd-lint", "lint_regression")])):
        drill(toy, instance_id, cause, h(0xd0 + n), **over.get("drill_over", {}).get(instance_id, {}))
    return toy


def copy_world() -> State:
    copy = State("copy")
    genesis_cycle(copy, [])
    copy.cycle(lambda c: EV.decision(c, "bad-unit", ["tests_red"]), lambda c: EV.decision(c, "fix", [], merged(h(0xc1))),
               cost)
    copy.cycle(lambda c: EV.sentinel(c, h(0xc1), "green", [], h(31, 64)), cost)
    return copy


def judge(toy: State | None = None, copy: State | None = None, drill_inputs=True, toy_expect=None) -> dict:
    return PR.judge((toy or toy_world()).files(), (copy or copy_world()).files(),
                    TOY_EXPECT if toy_expect is None else toy_expect, COPY_EXPECT,
                    {"seed": SEED, "catalog": CATALOG} if drill_inputs else None)


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
        merge = [r for r in rows if r["kind"] == "decision" and r["payload"]["decision"] == "merge"]
        self.assertEqual(got["payload"], {"stage": 0, "copy_genesis_row_hash": rows[0]["row_hash"],
                                          "copy_merge_row_hashes": [merge[0]["row_hash"]],
                                          "conditions": sorted(PR.CONDITIONS), "not_checked": sorted(PR.NOT_CHECKED)})
        self.assertFalse(set(PR.CONDITIONS) & set(PR.NOT_CHECKED))

    def test_a_merged_candidate_offered_again_is_judged_by_its_first_decision(self):
        toy = toy_world()
        toy.cycle(lambda c: EV.decision(c, "good", ["kos:patch_does_not_apply"]), cost)
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
        toy = toy_world()
        toy.cycle(lambda c: EV.row(c, "genesis2", "genesis", genesis_payload("toy")), cost)
        self.assertEqual(self.reasons(judge(toy), "#genesis"), ["toy:genesis_repeated"])

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
        self.assertEqual(got["conditions"]["#merge"], ["toy:undecided:good"])
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

    def test_the_copy_is_judged_the_same_way_but_for_the_drill(self):
        copy = State("copy")
        genesis_cycle(copy, [("fix", ["tests_red"])])
        got = judge(copy=copy)
        self.assertEqual(got["conditions"]["#merge"], ["copy:not_merged:fix"])
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


class Write(unittest.TestCase):
    """``write`` on the in-process GitHub whose ``brain/state`` holds the toy world's files."""

    HEADS = {B.STATE: h(0x5a), B.INTEGRATION: h(0x1a)}
    REQ = {"cycle_id": "900-1", "ts": TS, "snapshot_id": h(0x1a)}

    def setUp(self) -> None:
        self.toy = toy_world()
        self.gh = YW.github_at(self.HEADS, {"src/a.js": b"var a = 1;\n"},
                               {B.STATE_LEDGER: self.toy.ledger, B.STATE_ROOTS: self.toy.roots,
                                B.STATE_STATUS: self.toy.status})

    def write(self, toy: dict | None = None, head: str | None = None, signer=None, drill_inputs=True) -> dict:
        toy = dict(self.toy.files(), status=self.toy.status) if toy is None else toy
        return PR.write(W.Writer(YW.REPO, self.gh), head or self.gh.refs[B.STATE], toy, copy_world().files(),
                        TOY_EXPECT, COPY_EXPECT, {"seed": SEED, "catalog": CATALOG} if drill_inputs else None,
                        self.REQ, IMPORTS, signer or AN.FakeSigner(True, YW.IDENTITY, "rekor-pass"), 1_000_000)

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
        self.assertEqual([r["row_hash"] for r in added], got["written"]["row_hashes"])
        # the state written is still judged PASS: its cycle has its root and its status row
        self.assertEqual(PR.judge({"ledger": new["ledger"], "roots": new["roots"]}, copy_world().files(), TOY_EXPECT,
                                  COPY_EXPECT, {"seed": SEED, "catalog": CATALOG})["verdict"], "PASS")
        # a second PASS on it is refused, nothing written
        before = len(self.writes())
        again = self.write(toy=new, head=got["written"]["state_sha"])
        self.assertEqual((again["refused"], again["written"], len(self.writes())), (["already_passed"], None, before))

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
                PR.judge(toy_world().files(), copy_world().files(), bad, COPY_EXPECT, None)


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
            write_tree(base, {"catalog.json": CATALOG, "seed.json": SEED})
            catalog, seed = os.path.join(base, "catalog.json"), os.path.join(base, "seed.json")
            code, line = self.run_cli("judge", toy, copy, te, ce, catalog, seed)
            self.assertEqual((code, line), (0, json.loads(json.dumps(judge()))))
            code, line = self.run_cli("judge", toy, copy, te, ce)
            self.assertEqual((code, line["verdict"], line["conditions"]["#geri-alma"]),
                             (1, "FAIL", ["toy:drill_inputs_missing"]))
            for argv in (("judge", toy, copy, te), ("judge", toy, copy, te, os.path.join(base, "none")),
                         ("judge", os.path.join(base, "none"), copy, te, ce), ("other", toy, copy, te, ce)):
                with self.subTest(argv=argv):
                    self.assertEqual(self.run_cli(*argv), (2, {"verdict": "FAIL"}))


if __name__ == "__main__":
    unittest.main()
