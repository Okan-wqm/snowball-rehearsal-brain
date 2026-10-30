"""Test 14 (asama-0/09): every artifact the stage 0 loop writes (the genesis, ``events``, ``cost`` and ``drill``
rows, the root, the ``status.md`` block) conforms to tohum/26, 26b and 26c and the seed's vector pages' row words
(29m, 29n, 29o), as ``ledger.schema`` writes them.

- the artifacts of a real activation on the in-process GitHub (genesis, cycle start, cut, ratchet base, decision
  and status rows, the root, the block), a cost row from ``llm.call``'s own constructor, the drill commit, plant and
  revert rows from ``harness.revert_drill``'s payloads, a status-edited row from ``status.block``: no reason;
- each rule, broken on one of those artifacts at a time, gives its reason: a missing and an extra key, a float, a
  timestamp, a part, an unknown kind, each closed set, a reject without a cause, a revert without a cause, a merge
  decision with a reject's field, a genesis payload field missing, extra, or of the wrong form, a bad hash,
  evidence lines out of order, a root row with an extra key, a hand-edited block, a file without a block, a broken
  chain;
- a writer that hands ``activate`` a row of the wrong shape writes nothing.
"""

from __future__ import annotations

import copy
import json
import os
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import activate  # noqa: E402
import activation_world as AW  # noqa: E402
from dispatcher import llm_call  # noqa: E402
from harness import revert_drill  # noqa: E402
from ledger import chain, schema  # noqa: E402
from status import block  # noqa: E402


def lines(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.decode().splitlines()]


def rechain(rows: list[dict]) -> bytes:
    return AW.chained([{k: v for k, v in r.items() if k not in ("prev_hash", "row_hash")} for r in rows])


def stored(row: dict) -> dict:
    """A row with the chain's two hash fields (their values are the chain's check, not the schema's; a float
    cannot be chained at all, so the hash fields are set by hand)."""
    return dict(row, prev_hash=chain.ZERO_HASH, row_hash="0" * 64)


class Artifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        w = AW.World()
        cls.out = w.run()
        cls.ledger = w.gh.read_file("brain/state", "ledger.jsonl")
        cls.roots = w.gh.read_file("brain/state", "chain/root.jsonl")
        cls.status = w.gh.read_file("brain/state", "status.md")
        cls.rows = lines(cls.ledger)

    def test_activation_artifacts_conform(self):
        self.assertEqual({r["kind"] for r in self.rows},
                         {"genesis", "cycle_start", "integration_cut", "ratchet_base", "decision", "status"})
        self.assertEqual(schema.ledger_reasons(self.ledger), [])
        self.assertEqual(schema.roots_reasons(self.roots), [])
        self.assertEqual(schema.status_reasons(self.status, self.ledger), [])

    def other_writers_rows(self) -> list[dict]:
        verdict = llm_call.classify(None, "claude-sonnet-5-5", 1000, None)
        planned = {"prompt_sha256": "1" * 64, "cap_micros": 1000}
        cost = llm_call.cost_row({"fields": {}, "text": "canary"}, planned, "claude-sonnet-5-5", verdict, 12, "c1",
                                 AW.TS, AW.SNAP)
        key = revert_drill.key({"seed": "s"}, "41", {"instances": [{"id": "i1", "cause": "test_regression"}]})
        common = {"ts": AW.TS, "derivation": "tool", "trust": "verified", "snapshot_id": AW.SNAP, "evidence_refs": []}
        drill = [dict(common, row_id="d1", part="drill", kind="commit", payload=revert_drill.commit_payload(key)),
                 dict(common, row_id="d2", part="drill", kind="plant", payload=revert_drill.plant_payload("i1", "a" * 40)),
                 dict(common, row_id="d3", part="events", kind="revert", payload=revert_drill.revert_payload("a" * 40),
                      cause=key["cause"])]
        facts = {"ts": AW.TS, "snapshot_id": AW.SNAP, "row_id": "42:status", "canary_cap_usd_micros": 1000}
        planned = block.plan(self.ledger, self.ledger, [cost] + drill, b"hand edit\n", AW.World().imports, facts)
        return planned["rows"]

    def test_other_writers_rows_conform(self):
        rows = self.other_writers_rows()
        self.assertEqual([(r["part"], r["kind"]) for r in rows], [
            ("cost", "cost"), ("drill", "commit"), ("drill", "plant"), ("events", "revert"),
            ("events", "status_edited"), ("events", "status")])
        self.assertEqual(schema.ledger_reasons(rechain(self.rows + rows)), [])

    # ---- each rule caught

    def assert_reason(self, row: dict, fragment: str):
        reasons = schema.row_reasons(stored(row))
        self.assertTrue(any(fragment in r for r in reasons), (fragment, reasons))

    def row(self, kind: str, decision: str | None = None) -> dict:
        r = copy.deepcopy(next(r for r in self.rows if r["kind"] == kind and (
            decision is None or r["payload"].get("decision") == decision)))
        return {k: v for k, v in r.items() if k not in ("prev_hash", "row_hash")}

    def test_row_rules(self):
        merge = self.row("decision", "merge")
        self.assertEqual(schema.row_reasons(stored(merge)), [])
        reject = self.row("decision", "reject")
        cases = [
            ({k: v for k, v in merge.items() if k != "trust"}, "row.trust: missing"),
            (dict(merge, extra=1), "row.extra: not a field"),
            (dict(merge, ts="2026-10-30T12:00:00.5Z"), "row.ts"),
            (dict(merge, part="ledger"), "row.part"),
            (dict(merge, kind="merged"), "unknown_row_type events/merged"),
            (dict(merge, kind="merge"), "unknown_row_type events/merge"),
            (dict(merge, derivation="guess"), "row.derivation"),
            (dict(merge, trust="sure"), "row.trust"),
            (dict(merge, cause="bad_luck"), "row.cause"),
            (dict(merge, miss_reason="other"), "row.miss_reason"),
            (dict(merge, snapshot_id=""), "row.snapshot_id"),
            (dict(merge, evidence_refs=[{"path": "a", "line_start": 3, "line_end": 2}]), "line_start after line_end"),
            (dict(merge, evidence_refs=[{"path": "a", "line_start": 0, "line_end": 2}]), "line_start"),
            (dict(merge, payload=dict(merge["payload"], pull=1.0)), "a float"),
            (dict(merge, payload=dict(merge["payload"], merge_sha="A" * 40)), "payload.merge_sha"),
            (dict(merge, payload=dict(merge["payload"], note="x")), "payload.note"),
            (dict(merge, payload=dict(merge["payload"], reasons=["x"])), "payload.reasons"),
            (dict(merge, payload=dict(merge["payload"], decision="revert")), "payload.decision: not one of"),
            ({k: v for k, v in reject.items() if k != "cause"}, "row.cause: missing"),
            (dict(reject, payload=dict(reject["payload"], reasons=[])), "payload.reasons"),
            (dict(reject, payload=dict(reject["payload"], pull=3)), "payload.pull"),
            (dict(self.row("status"), payload={"block_sha256": "0" * 64, "cycle_id": "1"}), "payload.cycle_id"),
            (dict(self.row("cycle_start"), payload={}), "payload.cycle_id: missing"),
            (dict(self.row("ratchet_base"), payload={"base_run_sha256": "0" * 64, "counts": {"eslint": -1}}),
             "payload.counts.eslint"),
            (dict(self.row("integration_cut"), payload={"branch": "main", "base_sha": "0" * 40}), "payload.branch"),
        ]
        for row, fragment in cases:
            self.assert_reason(row, fragment)
        others = {(r["part"], r["kind"]): r for r in self.other_writers_rows()}
        revert = others[("events", "revert")]
        self.assert_reason({k: v for k, v in revert.items() if k != "cause"}, "row.cause: missing")
        plant = others[("drill", "plant")]
        self.assert_reason(dict(plant, payload=dict(plant["payload"], drill="lesson")), "payload.drill")
        commit = others[("drill", "commit")]
        self.assert_reason(dict(commit, payload=dict(commit["payload"], instance_id="i1")), "payload.instance_id")
        cost = others[("cost", "cost")]
        self.assert_reason(dict(cost, payload=dict(cost["payload"], usd_micros=0.5)), "a float")
        self.assert_reason(dict(cost, payload={k: v for k, v in cost["payload"].items() if k != "usd_micros"}),
                           "payload.usd_micros: missing")

    def test_genesis_payload_rules(self):
        gen = self.row("genesis")
        p = gen["payload"]
        cases = [
            ({k: v for k, v in p.items() if k != "recipe_sha256"}, "payload.recipe_sha256: missing"),
            (dict(p, extra="x"), "payload.extra"),
            (dict(p, target=""), "payload.target"),
            (dict(p, base_sha="A" * 40), "payload.base_sha"),
            (dict(p, facts_sha256="0" * 63), "payload.facts_sha256"),
            (dict(p, seed_epoch=dict(p["seed_epoch"], commit="x")), "payload.seed_epoch.commit"),
            (dict(p, seed_security_last_row_hash=None), "payload.seed_security_last_row_hash"),
        ]
        for payload, fragment in cases:
            self.assert_reason(dict(gen, payload=payload), fragment)

    def test_root_status_and_chain_rules(self):
        root = lines(self.roots)[0]
        bad_root = rechain([dict(root, signer="x")])
        self.assertTrue(any("roots line 1.signer" in r for r in schema.roots_reasons(bad_root)))
        self.assertTrue(any("roots line 1.root" in r for r in schema.roots_reasons(rechain([dict(root, root="0" * 63)]))))
        edited = self.status.replace(b"Human touches: 2", b"Human touches: 9")
        self.assertNotEqual(edited, self.status)
        self.assertIn("status.md: block sha256 is not the last status row's block_sha256",
                      schema.status_reasons(edited, self.ledger))
        self.assertEqual(schema.status_reasons(b"docs above\n" + self.status + b"docs below\n", self.ledger), [])
        no_close = b"\n".join(l for l in self.status.split(b"\n") if l != block.CLOSE)
        self.assertTrue(any("CLOSE" in r for r in schema.status_reasons(no_close, self.ledger)))
        self.assertIn("status.md: has no block", schema.status_reasons(b"x\n", self.ledger))
        no_status = rechain([r for r in self.rows if r["kind"] != "status"])
        self.assertIn("status.md: the ledger has no status row", schema.status_reasons(self.status, no_status))
        broken = self.ledger.replace(b'"decision":"merge"', b'"decision":"reject"')
        self.assertTrue(schema.ledger_reasons(broken)[0].startswith("ledger: not a valid chain"))

    def test_activate_refuses_a_row_of_the_wrong_shape_before_writing(self):
        w = AW.World()
        w.canary_cap = 1.5  # status.block refuses a float cap: a hard stop, brain/state not written
        with self.assertRaises(activate.HardStop):
            w.run()
        self.assertNotIn("brain/state", w.gh.refs)
        with self.assertRaises(activate.Unusable):
            activate.state_files([dict(self.row("decision", "merge"), payload={"decision": "merge", "candidate": "x"})],
                                 AW.World().imports, {"ts": AW.TS, "snapshot_id": "s", "row_id": "1:status",
                                                      "canary_cap_usd_micros": 0}, AW.World().signer, "1:root")


if __name__ == "__main__":
    unittest.main()
