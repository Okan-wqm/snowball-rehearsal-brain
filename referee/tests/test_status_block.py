"""Test 42 (asama-0/09) and group ``status`` (tohum/29d): ``status.block``, the top block of ``status.md`` from the
ledger; a hand edit is regenerated in the next cycle and written to ``events``.

- the view, one rule each: the cycle number counts ``events/status`` rows (ledger and the cycle's rows); the last
  decision is the last ``events`` row of kind merge, reject or revert, not another kind or part; the base age is
  the seconds from the last cut row to the cycle (hand-computed), unknown commit count shown as unknown, no cut
  row shown as not cut, a cut after the cycle refused; brakes sum cost rows of that budget only (ledger and the
  cycle's rows), ``brake`` from spent == budget, ``ok`` one micro-USD below; human touches are the rows of
  ``setup/imports.jsonl``, a broken imports chain refused;
- the block: a fixture's whole text written by hand; a hostile value (a line break with an END marker, HTML, a
  backtick, a link, a mention, non-ASCII) stays on its line and inert, and the next cycle is not an edit;
- edits: first cycle without a file is not an edit; an untouched block is not an edit; a changed line, a removed
  END line, an END line inserted inside the block, a deleted file, a block this module never wrote are edits:
  one ``status_edited`` row with the found and expected hashes, the regenerated file is the new block followed
  by the bytes after the region, which are kept;
- refusals before any commit: a tampered ledger (hard stop), a secret in a cycle row, bad facts;
- one ``brain/state`` commit through ``target.write`` on the in-process GitHub holding the ledger and
  ``status.md``; a hand edit committed between two cycles is found and recorded in the next one;
- the command line: outputs and exit codes.
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

from ledger import append as AP  # noqa: E402
from ledger import chain  # noqa: E402
from status import block as SB  # noqa: E402
from target import write as W  # noqa: E402
from fake_github import FakeGitHub  # noqa: E402

ZERO = "0" * 64
TOKEN = "ghp_" + "Q7x" * 12  # a GitHub token shape, not a real token
TS = "2026-10-30T12:00:00Z"
END = b"<!-- status.block:end -->"


def build(rows, prev=ZERO):
    """An independent writer of chained lines (sorted keys, no spaces: the canonical form of these ASCII rows)."""
    out = []
    for row in rows:
        row = dict(row, prev_hash=prev)
        body = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
        prev = row["row_hash"] = hashlib.sha256(body + prev.encode()).hexdigest()
        out.append(json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    return b"".join(out)


def cost(row_id, budget, micros):
    return {"row_id": row_id, "part": "cost", "kind": "cost", "payload": {"budget": budget, "cost_usd_micros": micros}}


def ev(row_id, kind, ts="2026-10-30T10:00:00Z", **extra):
    return dict({"row_id": row_id, "part": "events", "kind": kind, "ts": ts}, **extra)


LEDGER = build([
    ev("g1", "integration_cut", "2026-10-30T09:00:00Z", payload={"main_sha": "a" * 40}),
    ev("m1", "merge"),
    cost("c1", "canary", 300000),
    ev("r1", "revert", "2026-10-30T11:00:00Z", cause="test_regression"),
    ev("x1", "status_edited"),   # an events row of another kind is not a decision
    {"row_id": "d1", "part": "drill", "kind": "merge", "ts": TS},   # a merge kind in another part is not either
    cost("c2", "rival", 900000),
])
IMPORTS = build([{"ts": "2026-10-29T08:00:00Z", "stage": 0, "brain_sha": "b" * 40},
                 {"ts": "2026-10-29T09:30:00Z", "stage": 0, "brain_sha": "c" * 40}])


def facts(**over):
    base = {"cycle_id": "4101", "snapshot_id": "e" * 40, "row_id": "s1", "ts": TS,
            "budgets": {"canary": 500000, "zero": 0}, "main_commits_since_cut": 3}
    return dict(base, **over)


def plan(ledger=LEDGER, rows=(), status=None, imports=IMPORTS, **over):
    return SB.plan(ledger, ledger, list(rows), status, imports, facts(**over))


def stored(ledger, rows):
    """The ledger after a cycle with these (already planned) rows, through the real ``ledger.append``."""
    return AP.plan_cycle(ledger, ledger, lambda: json.dumps({"rows": rows}).encode()).content


EXPECTED_BLOCK = b"""<!-- status.block:begin -->
## Status

Written by the referee's status.block from the ledger at the end of every cycle. A hand edit of this
block is replaced in the next cycle and recorded as a status_edited event.

- Cycle: number 1, id "4101", at "2026-10-30T12:00:00Z"
- Last decision: "revert", row "r1", at "2026-10-30T11:00:00Z", cause "test_regression"
- Base age: 10800 s since brain/integration was cut from main "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" at "2026-10-30T09:00:00Z"; main commits since: 3
- Brake "canary": ok, spent 300000 of 500000 micro-USD
- Brake "zero": brake, spent 0 of 0 micro-USD
- Human touches: 2, last at "2026-10-29T09:30:00Z"
<!-- status.block:end -->
"""


class View(unittest.TestCase):
    def test_the_fixture_block_word_for_word(self):
        out = plan()
        self.assertEqual(out["block"], EXPECTED_BLOCK)
        self.assertEqual(out["view"]["base"], {"main_sha": "a" * 40, "cut_ts": "2026-10-30T09:00:00Z", "age_s": 10800,
                                               "main_commits_since_cut": 3})
        self.assertEqual(out["view"]["human_touches"], {"count": 2, "last_ts": "2026-10-29T09:30:00Z"})

    def test_cycle_number_counts_status_rows(self):
        self.assertEqual(plan()["view"]["cycle"]["number"], 1)
        two = build([ev("s0", "status", payload={}), ev("s9", "status", payload={}), ev("o", "other")])
        self.assertEqual(plan(two, imports=b"")["view"]["cycle"]["number"], 3)
        # the cycle's own rows count as the ledger's last rows
        self.assertEqual(plan(two, rows=[ev("s8", "status", payload={})], imports=b"")["view"]["cycle"]["number"], 4)

    def test_last_decision_is_the_last_merge_reject_or_revert(self):
        self.assertEqual(plan()["view"]["last_decision"],
                         {"kind": "revert", "row_id": "r1", "ts": "2026-10-30T11:00:00Z", "cause": "test_regression"})
        later = plan(rows=[ev("j1", "reject", TS), ev("n1", "noted", TS)])
        self.assertEqual(later["view"]["last_decision"], {"kind": "reject", "row_id": "j1", "ts": TS, "cause": None})
        self.assertIsNone(plan(build([ev("z", "status_edited")]), imports=b"")["view"]["last_decision"])
        self.assertIn(b"- Last decision: none\n", plan(build([ev("z", "x")]), imports=b"")["block"])

    def test_base_age(self):
        newer = plan(rows=[ev("g2", "integration_cut", "2026-10-30T11:59:00Z", payload={"main_sha": "f" * 40})])
        self.assertEqual(newer["view"]["base"]["age_s"], 60)
        self.assertEqual(newer["view"]["base"]["main_sha"], "f" * 40)
        unknown = plan(main_commits_since_cut=None)
        self.assertIsNone(unknown["view"]["base"]["main_commits_since_cut"])
        self.assertIn(b"; main commits since: unknown\n", unknown["block"])
        uncut = plan(build([ev("m", "merge")]), imports=b"")
        self.assertIsNone(uncut["view"]["base"])
        self.assertIn(b"- Base age: brain/integration not cut\n", uncut["block"])
        across_a_day = plan(ts="2026-10-31T09:00:01Z")
        self.assertEqual(across_a_day["view"]["base"]["age_s"], 86401)
        for bad in ("2026-10-30T12:00:01Z", "2026-10-30 09:00:00Z", "2026-02-30T09:00:00Z", None):
            with self.subTest(cut_ts=bad), self.assertRaises(SB.Unusable):
                plan(rows=[ev("g2", "integration_cut", bad, payload={"main_sha": "f" * 40})])

    def test_brakes(self):
        brakes = {b["budget"]: b for b in plan()["view"]["brakes"]}
        self.assertEqual(brakes["canary"], {"budget": "canary", "budget_usd_micros": 500000,
                                            "spent_usd_micros": 300000, "state": "ok"})
        self.assertEqual(brakes["zero"]["state"], "brake")
        at = plan(rows=[cost("c3", "canary", 200000)])["view"]["brakes"][0]
        self.assertEqual((at["spent_usd_micros"], at["state"]), (500000, "brake"))
        below = plan(rows=[cost("c3", "canary", 199999)])["view"]["brakes"][0]
        self.assertEqual((below["spent_usd_micros"], below["state"]), (499999, "ok"))
        other = plan(rows=[cost("c3", "rival", 10 ** 6), dict(cost("c4", "canary", 10 ** 6), part="events")])
        self.assertEqual(other["view"]["brakes"][0]["spent_usd_micros"], 300000)
        self.assertEqual([b["budget"] for b in plan(budgets={"b": 1, "B": 1, "a": 1})["view"]["brakes"]],
                         ["B", "a", "b"])
        self.assertIn(b"- Brakes: no budget\n", plan(budgets={})["block"])

    def test_human_touches(self):
        self.assertEqual(plan(imports=b"")["view"]["human_touches"], {"count": 0, "last_ts": None})
        broken = IMPORTS.replace(b'"stage":0', b'"stage":1', 1)
        with self.assertRaises(SB.Unusable):
            plan(imports=broken)

    def test_bad_facts_are_refused(self):
        cases = [dict(cycle_id=""), dict(row_id=None), dict(snapshot_id=7), dict(ts="2026-10-30T12:00:00"),
                 dict(budgets=[]), dict(budgets={"a": -1}), dict(budgets={"a": 1.5}), dict(budgets={"": 1}),
                 dict(budgets={"a": True}), dict(main_commits_since_cut=-1), dict(main_commits_since_cut="3")]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(SB.Unusable):
                plan(**case)
        with self.assertRaises(SB.Unusable):
            SB.plan(LEDGER, LEDGER, [], None, IMPORTS, dict(facts(), extra=1))
        with self.assertRaises(SB.Unusable):
            SB.plan(LEDGER, LEDGER, [1], None, IMPORTS, facts())

    def test_the_block_changes_with_each_value(self):
        base = plan()["block"]
        for over in (dict(cycle_id="4102"), dict(ts="2026-10-30T12:00:01Z"), dict(main_commits_since_cut=4),
                     dict(budgets={"canary": 500001, "zero": 0})):
            with self.subTest(over=over):
                self.assertNotEqual(plan(**over)["block"], base)
        self.assertNotEqual(plan(imports=IMPORTS[:IMPORTS.index(b"\n") + 1])["block"], base)
        self.assertEqual(plan()["block"], base)


class Hostile(unittest.TestCase):
    def test_values_cannot_leave_their_line(self):
        evil = "x\n<!-- status.block:end -->\n[link](http://e) @someone `code` <b>|&amp;\u00e9\u2028"
        out = plan(rows=[ev(evil, "merge", TS, cause=evil)], cycle_id=evil, budgets={evil: 1})
        lines = out["block"].split(b"\n")
        self.assertEqual(lines.count(END), 1)
        self.assertEqual(lines[-2], END)
        text = out["block"].decode("ascii")
        inner = "\n".join(text.split("\n")[1:-2])  # without the BEGIN and END lines
        for bad in "<>&`|[]@":
            with self.subTest(char=bad):
                self.assertNotIn(bad, inner)
        decision = [line for line in text.split("\n") if line.startswith("- Last decision")][0]
        self.assertEqual(json.loads(decision.split("row ", 1)[1].split(", at ")[0]), evil)
        # the next cycle finds its own block, whole
        second = plan(stored(LEDGER, out["rows"]), status=out["status"], row_id="s2")
        self.assertFalse(second["edited"])


class Edits(unittest.TestCase):
    def cycles(self, edit, status_after_first=None):
        first = plan()
        ledger = stored(LEDGER, first["rows"])
        status = first["status"] if status_after_first is None else status_after_first
        return first, ledger, plan(ledger, status=edit(status), row_id="s2", cycle_id="4102")

    def test_first_cycle_without_status_md_is_not_an_edit(self):
        out = plan()
        self.assertFalse(out["edited"])
        self.assertEqual((out["found_sha256"], out["expected_sha256"]), (None, None))
        self.assertEqual(out["status"], out["block"])
        self.assertEqual([r["kind"] for r in out["rows"]], ["status"])
        row = out["rows"][0]
        self.assertEqual((row["row_id"], row["part"], row["ts"], row["snapshot_id"]), ("s1", "events", TS, "e" * 40))
        self.assertEqual(row["payload"], {"cycle_id": "4101", "number": 1,
                                          "block_sha256": hashlib.sha256(out["block"]).hexdigest()})
        self.assertFalse(plan(status=b"")["edited"])

    def test_an_untouched_block_is_not_an_edit(self):
        first, ledger, second = self.cycles(lambda s: s + b"rendered docs below\n")
        self.assertFalse(second["edited"])
        self.assertEqual([r["kind"] for r in second["rows"]], ["status"])
        self.assertEqual(second["expected_sha256"], hashlib.sha256(first["block"]).hexdigest())
        self.assertEqual(second["status"], second["block"] + b"rendered docs below\n")
        self.assertEqual(second["view"]["cycle"]["number"], 2)

    def assertEdit(self, edit, rest=b""):
        first, ledger, second = self.cycles(edit)
        self.assertTrue(second["edited"])
        expected = hashlib.sha256(first["block"]).hexdigest()
        kinds = [(r["row_id"], r["kind"]) for r in second["rows"]]
        self.assertEqual(kinds, [("s2:edited", "status_edited"), ("s2", "status")])
        self.assertEqual(second["rows"][0]["payload"], {"cycle_id": "4102", "found_sha256": second["found_sha256"],
                                                        "expected_sha256": expected})
        self.assertNotEqual(second["found_sha256"], expected)
        self.assertEqual(second["status"], second["block"] + rest)
        # the regenerated block is the same block a cycle without the edit writes
        self.assertEqual(second["block"], plan(ledger, row_id="s2", cycle_id="4102")["block"])
        # and once written, the cycle after is clean again
        third = plan(stored(ledger, second["rows"]), status=second["status"], row_id="s3", cycle_id="4103")
        self.assertFalse(third["edited"])
        return second

    def test_a_changed_line_is_an_edit(self):
        second = self.assertEdit(lambda s: s.replace(b"Human touches: 2", b"Human touches: 0") + b"docs\n", b"docs\n")
        edited = plan().get("status").replace(b"Human touches: 2", b"Human touches: 0")
        self.assertEqual(second["found_sha256"], hashlib.sha256(edited).hexdigest())

    def test_a_removed_end_line_makes_the_whole_file_the_region(self):
        self.assertEdit(lambda s: s.replace(END + b"\n", b"") + b"docs\n")

    def test_an_end_line_inserted_inside_the_block_leaves_no_tail(self):
        self.assertEdit(lambda s: s.replace(b"- Brake \"canary\"", END + b"\n- Brake \"canary\"") + b"docs\n",
                        b"docs\n")

    def test_a_deleted_status_md_is_an_edit(self):
        second = self.assertEdit(lambda s: None)
        self.assertIsNone(second["found_sha256"])

    def test_an_emptied_status_md_is_an_edit(self):
        self.assertEdit(lambda s: b"")

    def test_a_block_never_written_is_an_edit(self):
        forged = plan()["block"].replace(b"spent 300000", b"spent 0")
        out = plan(status=forged + b"docs\n")
        self.assertTrue(out["edited"])
        self.assertEqual(out["rows"][0]["payload"]["expected_sha256"], None)
        self.assertEqual(out["status"], out["block"] + b"docs\n")


class Cycle(unittest.TestCase):
    def test_refusals_commit_nothing(self):
        state = AP.CountingState()
        tampered = LEDGER.replace(b'"kind":"merge"', b'"kind":"reject"', 1)
        with self.assertRaises(AP.HardStop):
            SB.status_cycle(tampered, LEDGER, [], None, IMPORTS, facts(), state)
        with self.assertRaises(AP.HardStop):  # the ledger is checked before the facts are read
            SB.status_cycle(tampered, LEDGER, [], None, IMPORTS, None, state)
        with self.assertRaises(AP.SecretRow):
            SB.status_cycle(LEDGER, LEDGER, [ev("n", "merge", note=TOKEN)], None, IMPORTS, facts(), state)
        with self.assertRaises(AP.Unusable):  # a row id the ledger already has
            SB.status_cycle(LEDGER, LEDGER, [], None, IMPORTS, facts(row_id="m1"), state)
        self.assertEqual(state.commits, 0)

    def test_one_commit_holds_the_ledger_and_status_md(self):
        state = AP.CountingState()
        out = SB.status_cycle(LEDGER, LEDGER, [ev("m2", "merge", TS)], b"old\n" + END + b"\ndocs\n", IMPORTS,
                              facts(), state)
        self.assertEqual(state.commits, 1)
        self.assertEqual(set(state.files), {"ledger.jsonl", "status.md"})
        new = state.files["ledger.jsonl"]
        self.assertTrue(chain.verify_bytes(new, LEDGER)["valid"])
        rows = [json.loads(line) for line in new[len(LEDGER):].splitlines()]
        self.assertEqual([(r["row_id"], r["kind"]) for r in rows],
                         [("m2", "merge"), ("s1:edited", "status_edited"), ("s1", "status")])
        self.assertEqual([r["row_hash"] for r in rows], out["row_hashes"])
        self.assertEqual(state.files["status.md"], out["block"] + b"docs\n")
        self.assertEqual(out["view"]["last_decision"]["row_id"], "m2")


class OnTheTarget(unittest.TestCase):
    def test_two_cycles_and_a_hand_edit_between(self):
        gh = FakeGitHub("acme/toy")
        gh.refs["main"] = main = gh.seed_commit("t0")
        gh.refs["brain/state"] = head = gh.seed_commit("s0", files={"ledger.jsonl": LEDGER})
        wr = W.Writer("acme/toy", gh)
        first = SB.status_cycle(LEDGER, LEDGER, [], gh.read_file("brain/state", "status.md"), IMPORTS, facts(),
                                AP.TargetState(wr, head))
        self.assertFalse(first["edited"])
        self.assertEqual(gh.read_file("brain/state", "status.md"), first["block"])
        self.assertEqual(sum(1 for r in gh.requests if r[0] == "POST" and r[1].endswith("/git/commits")), 1)
        # an operator edits status.md on brain/state by hand
        ledger1 = gh.read_file("brain/state", "ledger.jsonl")
        hand = first["block"].replace(b"ok, spent", b"fine, spent")
        gh.refs["brain/state"] = gh.seed_commit("s-hand", [gh.refs["brain/state"]],
                                                files={"ledger.jsonl": ledger1, "status.md": hand})
        second = SB.status_cycle(ledger1, ledger1, [], gh.read_file("brain/state", "status.md"), IMPORTS,
                                 facts(row_id="s2", cycle_id="4102"), AP.TargetState(wr, gh.refs["brain/state"]))
        self.assertTrue(second["edited"])
        self.assertEqual(gh.read_file("brain/state", "status.md"), second["block"])
        ledger2 = gh.read_file("brain/state", "ledger.jsonl")
        self.assertTrue(chain.verify_bytes(ledger2, ledger1)["valid"])
        edited = [json.loads(line) for line in ledger2.splitlines() if b'"status_edited"' in line]
        self.assertEqual(edited[-1]["payload"]["found_sha256"], hashlib.sha256(hand).hexdigest())
        self.assertEqual(gh.refs["main"], main)


def run(args, stdin=b""):
    proc = subprocess.run([sys.executable, "-m", "status.block"] + args, input=stdin, capture_output=True,
                          cwd=REFEREE, timeout=60)
    return proc.returncode, json.loads(proc.stdout), proc.stderr.decode()


class CommandLine(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name
        for name, data in (("ledger", LEDGER), ("imports", IMPORTS)):
            with open(os.path.join(self.dir, name), "wb") as fh:
                fh.write(data)

    def args(self, ledger="ledger", status="status.md"):
        return ["cycle", *(os.path.join(self.dir, n) for n in (ledger, "ledger", "imports", status))]

    def test_written(self):
        code, out, _ = run(self.args(), json.dumps({"rows": [], "facts": facts()}).encode())
        self.assertEqual(code, 0)
        self.assertEqual((out["ok"], out["hard_stop"], out["commits"], out["edited"]), (True, False, 1, False))
        self.assertEqual(out["block_sha256"], hashlib.sha256(EXPECTED_BLOCK).hexdigest())
        self.assertEqual(out["status_sha256"], out["block_sha256"])
        self.assertEqual(out["view"], json.loads(json.dumps(plan()["view"])))
        self.assertEqual(len(out["row_hashes"]), 1)

    def test_edited_file(self):
        with open(os.path.join(self.dir, "status.md"), "wb") as fh:
            fh.write(b"hand written\n")
        code, out, _ = run(self.args(), json.dumps({"rows": [], "facts": facts()}).encode())
        self.assertEqual((code, out["edited"], out["found_sha256"]),
                         (0, True, hashlib.sha256(b"hand written\n").hexdigest()))
        self.assertEqual(len(out["row_hashes"]), 2)

    def test_refused_and_unusable(self):
        with open(os.path.join(self.dir, "tampered"), "wb") as fh:
            fh.write(LEDGER.replace(b'"kind":"merge"', b'"kind":"reject"', 1))
        code, out, err = run(self.args(ledger="tampered"), json.dumps({"rows": [], "facts": facts()}).encode())
        self.assertEqual((code, out["ok"], out["hard_stop"], out["commits"], out["view"]), (1, False, True, 0, None))
        self.assertIn("hard stop", err)
        code, out, _ = run(self.args(), json.dumps({"rows": [ev("n", "x", note=TOKEN)], "facts": facts()}).encode())
        self.assertEqual((code, out["ok"], out["hard_stop"]), (1, False, False))
        for stdin in (b"{}", b"not json", json.dumps({"rows": [], "facts": facts(ts="now")}).encode(),
                      json.dumps({"rows": [], "facts": facts(), "x": 1}).encode()):
            with self.subTest(stdin=stdin):
                code, out, err = run(self.args(), stdin)
                self.assertEqual((code, out["ok"], out["block_sha256"], out["commits"]), (2, False, None, 0))
                self.assertIn("unusable input", err)
        code, out, _ = run(["cycle"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
