"""Test 14 (asama-0/09): every artifact the stage 0 loop writes (the genesis, ``events``, ``cost`` and ``drill``
rows, the root, the ``status.md`` block) conforms to tohum/26, 26b and 26c, as ``ledger.schema`` writes them.

- the artifacts of a real activation on the in-process GitHub (genesis, cut, merge, reject and status rows, the
  root, the block), a cost row from ``llm.call``'s own constructor, the drill commit and reveal rows from
  ``exit.drill``'s, a status-edited row from ``status.block``: no reason;
- each rule, broken on one of those artifacts at a time, gives its reason: a missing and an extra key, a float, a
  timestamp, a part, an unknown kind, each closed set, a reject without a cause, a genesis payload field missing,
  extra, or of the wrong form, a bad hash, evidence lines out of order, a root row with an extra key, a hand-edited
  block, a block without its END line, a broken chain;
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
        self.assertEqual({r["kind"] for r in self.rows}, {"genesis", "integration_cut", "merge", "reject", "status"})
        self.assertEqual(schema.ledger_reasons(self.ledger), [])
        self.assertEqual(schema.roots_reasons(self.roots), [])
        self.assertEqual(schema.status_reasons(self.status, self.ledger), [])

    def other_writers_rows(self) -> list[dict]:
        verdict = llm_call.classify(None, "claude-sonnet-5-5", 1000, {})
        cost = llm_call.cost_row({"name": "canary"}, {"prompt_sha256": "1" * 64, "system_sha256": "2" * 64},
                                 "claude-sonnet-5-5", 1000, "canary", verdict, 12, "c1", AW.TS, AW.SNAP)
        seed = b"k" * 32
        fixtures = [{"id": "f1", "cause": "test_regression", "files": {"a": "b"}}]
        commit = revert_drill.commit_row(seed, "41", fixtures, "d1", AW.TS, AW.SNAP)
        ans = revert_drill.answer(seed, "41", fixtures)
        outcome = {"reverted": True, "cause": "test_regression"}
        committed = revert_drill.commitment(ans)
        reveal = revert_drill.reveal_row(committed, ans, outcome,
                                         revert_drill.judge(committed, ans, outcome, seed, fixtures), "d2", AW.TS,
                                         AW.SNAP)
        facts = {"cycle_id": "42", "ts": AW.TS, "snapshot_id": AW.SNAP, "row_id": "42:status", "budgets": {},
                 "main_commits_since_cut": None}
        planned = block.plan(self.ledger, self.ledger, [cost, commit, reveal], b"hand edit\n", AW.World().imports,
                             facts)
        return planned["rows"]

    def test_other_writers_rows_conform(self):
        rows = self.other_writers_rows()
        self.assertEqual([(r["part"], r["kind"]) for r in rows], [
            ("cost", "cost"), ("drill", "commit"), ("drill", "reveal"), ("events", "status_edited"),
            ("events", "status")])
        self.assertEqual(schema.ledger_reasons(rechain(self.rows + rows)), [])

    # ---- each rule caught

    def assert_reason(self, row: dict, fragment: str):
        reasons = schema.row_reasons(stored(row))
        self.assertTrue(any(fragment in r for r in reasons), (fragment, reasons))

    def row(self, kind: str) -> dict:
        r = copy.deepcopy(next(r for r in self.rows if r["kind"] == kind))
        return {k: v for k, v in r.items() if k not in ("prev_hash", "row_hash")}

    def test_row_rules(self):
        merge = self.row("merge")
        self.assertEqual(schema.row_reasons(stored(merge)), [])
        cases = [
            ({k: v for k, v in merge.items() if k != "trust"}, "row.trust: missing"),
            (dict(merge, extra=1), "row.extra: not a field"),
            (dict(merge, ts="2026-10-30T12:00:00.5Z"), "row.ts"),
            (dict(merge, part="ledger"), "row.part"),
            (dict(merge, kind="merged"), "unknown_row_type events/merged"),
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
            ({k: v for k, v in self.row("reject").items() if k != "cause"}, "row.cause: missing"),
            (dict(self.row("reject"), payload=dict(self.row("reject")["payload"], reasons=[])), "payload.reasons"),
        ]
        for row, fragment in cases:
            self.assert_reason(row, fragment)
        # a float is caught wherever it is, even where the shape takes any object
        reveal = [r for r in self.other_writers_rows() if r["kind"] == "reveal"][0]
        reveal["payload"]["answer"]["weight"] = 0.5
        self.assert_reason(reveal, "payload.answer.weight: a float")

    def test_genesis_payload_rules(self):
        gen = self.row("genesis")
        p = gen["payload"]
        cases = [
            ({k: v for k, v in p.items() if k != "recipe_sha256"}, "payload.recipe_sha256: missing"),
            (dict(p, extra="x"), "payload.extra"),
            (dict(p, target=dict(p["target"], kind="fork")), "payload.target.kind"),
            (dict(p, import_=1), "payload.import_"),
            (dict(p, seed_security=dict(p["seed_security"], last_row_hash="x")), "payload.seed_security.last_row_hash"),
            (dict(p, ratchet={"base_run_sha256": p["ratchet"]["base_run_sha256"], "counts": {"eslint": -1}}),
             "payload.ratchet.counts.eslint"),
            (dict(p, candidates=["b", "a"]), "payload.candidates: not sorted"),
            (dict(p, result=dict(p["result"], rekor_uuids=[])), "payload.result.rekor_uuids: empty"),
            (dict(p, integration=dict(p["integration"], branch="main")), "payload.integration.branch"),
        ]
        for payload, fragment in cases:
            self.assert_reason(dict(gen, payload=payload), fragment)

    def test_root_status_and_chain_rules(self):
        root = lines(self.roots)[0]
        bad_root = rechain([dict(root, signer="x")])
        self.assertTrue(any("roots line 1.signer" in r for r in schema.roots_reasons(bad_root)))
        self.assertTrue(any("roots line 1.root" in r for r in schema.roots_reasons(rechain([dict(root, root="0" * 63)]))))
        edited = self.status.replace(b"Cycle: number 1", b"Cycle: number 9")
        self.assertIn("status.md: block sha256 is not the last status row's block_sha256",
                      schema.status_reasons(edited, self.ledger))
        no_end = b"\n".join(l for l in self.status.split(b"\n") if l != block.END.encode())
        self.assertIn("status.md: has no END line", schema.status_reasons(no_end, self.ledger))
        self.assertIn("status.md: does not start with the block's BEGIN line",
                      schema.status_reasons(b"x\n" + self.status, self.ledger))
        no_status = rechain([r for r in self.rows if r["kind"] != "status"])
        self.assertIn("status.md: the ledger has no status row", schema.status_reasons(self.status, no_status))
        broken = self.ledger.replace(b'"kind":"merge"', b'"kind":"reject"')
        self.assertTrue(schema.ledger_reasons(broken)[0].startswith("ledger: not a valid chain"))

    def test_activate_refuses_a_row_of_the_wrong_shape_before_writing(self):
        w = AW.World()
        w.budgets = {"founder": 1.5}  # status.block refuses a float budget: a hard stop, brain/state not written
        with self.assertRaises(activate.HardStop):
            w.run()
        self.assertNotIn("brain/state", w.gh.refs)
        with self.assertRaises(activate.Unusable):
            activate.state_files([dict(self.row("merge"), payload={"candidate": "x"})], AW.World().imports,
                                 {"cycle_id": "1", "ts": AW.TS, "snapshot_id": "s", "row_id": "1:status",
                                  "budgets": {}, "main_commits_since_cut": 0}, AW.World().signer, "1:root")


if __name__ == "__main__":
    unittest.main()
