"""Test 50 (asama-0/09) and group ``revert_drill`` (tohum/29d): the revert drill, ``exit.drill`` revert only.

- the selection: ``HMAC-SHA256(drill_seed, cycle_id)`` checked against RFC 4231 test case 6 and a hand-built HMAC;
  the fixture index over ids sorted by code point, the input order not mattering, every fixture reachable; the
  answer's exact fields; a seed shorter than 32 bytes refused;
- the commitment: ``sha256`` of the RFC 8785 form, independent of key order, different per cycle for the same
  fixture, and holding neither the fixture nor the cause in the commitment row;
- the judge: PASS, and each reason alone (``tampered_key``: an answer changed after the run; an answer not
  from the seed with a matching commitment; not reverted; another cause), every reason at once, every malformed
  input unusable;
- the run on the in-process GitHub with a ledger written by ``ledger.append``: the committed fixture is planted,
  merged and reverted to the first parent's tree, ``cause`` equal to the answer for each of
  ``test_regression``, ``build_break`` and ``lint_regression``; another observed cause, a green watch, a
  commitment that does not match the seed, no commitment, an already revealed one, one from the running cycle,
  and an edited ledger; the reveal row passes ``ledger.append`` and extends the chain;
- the command line's outputs and exits 0/1/2.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from harness import revert_drill as D  # noqa: E402
from ledger import append, chain  # noqa: E402
from target import write as W  # noqa: E402
from test_write import GATE, world  # noqa: E402

SEED = bytes(range(32))
FIXTURES = [
    {"id": "lint-rise", "cause": "lint_regression", "files": {"src/a.js": "var x = 1\n"}},
    {"id": "broken-build", "cause": "build_break", "files": {"src/a.js": "export const = ;\n"}},
    {"id": "failing-test", "cause": "test_regression", "files": {"src/a.js": "export const a = 2;\n"}},
]
IDS = sorted(f["id"] for f in FIXTURES)


def hand_hmac(seed: bytes, message: bytes) -> str:
    """RFC 2104 written out, a second computation beside ``hmac``."""
    block = 64
    k = hashlib.sha256(seed).digest() if len(seed) > block else seed
    k = k.ljust(block, b"\0")
    inner = hashlib.sha256(bytes(b ^ 0x36 for b in k) + message).digest()
    return hashlib.sha256(bytes(b ^ 0x5C for b in k) + inner).hexdigest()


def cycle_choosing(fixture_id: str, fixtures=FIXTURES) -> str:
    ids = sorted(f["id"] for f in fixtures)
    for n in range(1000, 2000):
        if ids[int(hand_hmac(SEED, str(n).encode()), 16) % len(ids)] == fixture_id:
            return str(n)
    raise AssertionError("no cycle chooses " + fixture_id)


def cli(stdin: bytes, *argv: str):
    proc = subprocess.run([sys.executable, "-m", "harness.revert_drill", *argv], cwd=REFEREE, input=stdin,
                          capture_output=True, timeout=60)
    lines = proc.stdout.decode().splitlines()
    return proc.returncode, (json.loads(lines[0]) if len(lines) == 1 else lines), proc.stderr.decode()


class Selection(unittest.TestCase):
    def test_rfc4231_case_6(self):
        seed = b"\xaa" * 131
        message = "Test Using Larger Than Block-Size Key - Hash Key First"
        want = "60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54"
        self.assertEqual(D.selection(seed, message), want)
        self.assertEqual(hand_hmac(seed, message.encode()), want)

    def test_answer(self):
        for n in ("1", "41018820064", "çevrim-7"):
            chosen = hand_hmac(SEED, n.encode("utf-8"))
            fixture = IDS[int(chosen, 16) % 3]
            cause = next(f["cause"] for f in FIXTURES if f["id"] == fixture)
            self.assertEqual(D.answer(SEED, n, FIXTURES), {"drill": "revert", "cycle_id": n, "fixture": fixture,
                                                         "cause": cause, "selection": chosen})

    def test_order_of_fixtures_does_not_matter(self):
        for n in map(str, range(20)):
            self.assertEqual(D.answer(SEED, n, FIXTURES), D.answer(SEED, n, FIXTURES[::-1]))

    def test_sorted_by_code_point(self):
        fixtures = [{"id": "b", "cause": "unknown"}, {"id": "B", "cause": "build_break"},
                    {"id": "a", "cause": "impact_miss"}]
        for n in map(str, range(30)):
            want = ["B", "a", "b"][int(hand_hmac(SEED, n.encode()), 16) % 3]
            self.assertEqual(D.answer(SEED, n, fixtures)["fixture"], want)

    def test_every_fixture_is_reachable_and_the_seed_matters(self):
        seen = {D.answer(SEED, str(n), FIXTURES)["fixture"] for n in range(60)}
        self.assertEqual(seen, set(IDS))
        other = bytes(range(1, 33))
        self.assertNotEqual([D.answer(SEED, str(n), FIXTURES)["fixture"] for n in range(30)],
                            [D.answer(other, str(n), FIXTURES)["fixture"] for n in range(30)])

    def test_seed_length(self):
        D.selection(bytes(32), "1")
        for seed in (bytes(31), b"", "00" * 32, None):
            with self.assertRaises(D.Unusable):
                D.selection(seed, "1")

    def test_fixture_shapes(self):
        good = {"id": "x", "cause": "build_break"}
        bad = [[], None, {"x": good}, [good, dict(good)], [dict(good, id="")], [dict(good, id=1)],
               [dict(good, cause="contract_counterpart")], [dict(good, cause=None)], [{"id": "x"}],
               [dict(good, extra=1)], [dict(good, files=[])], [dict(good, files={"../a": "x"})],
               [dict(good, files={"a": b"x"})], [dict(good, files={".git/config": "x"})], ["x"]]
        for fixtures in bad:
            with self.assertRaises(D.Unusable, msg=fixtures):
                D.answer(SEED, "1", fixtures)
        for cycle in ("", None, 1):
            with self.assertRaises(D.Unusable):
                D.answer(SEED, cycle, [good])


class Commitment(unittest.TestCase):
    def test_sha256_of_the_canonical_form(self):
        ans = D.answer(SEED, "7", FIXTURES)
        text = '{"cause":"%s","cycle_id":"7","drill":"revert","fixture":"%s","selection":"%s"}' % (
            ans["cause"], ans["fixture"], ans["selection"])
        self.assertEqual(D.commitment(ans), hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(D.commitment(dict(reversed(list(ans.items())))), D.commitment(ans))

    def test_differs_per_cycle_for_the_same_fixture(self):
        cycles = [str(n) for n in range(2000, 2100) if D.answer(SEED, str(n), FIXTURES)["fixture"] == "lint-rise"]
        self.assertGreater(len(cycles), 1)
        self.assertEqual(len({D.commitment(D.answer(SEED, n, FIXTURES)) for n in cycles}), len(cycles))

    def test_commit_row_holds_only_the_commitment(self):
        row = D.commit_row(SEED, "7", FIXTURES, "d1", "2026-10-30T00:00:00Z", "a" * 40)
        ans = D.answer(SEED, "7", FIXTURES)
        self.assertEqual(row["part"], "drill")
        self.assertEqual(row["kind"], "commit")
        self.assertEqual(row["payload"], {"drill": "revert", "question": "cause", "family": "revert",
                                          "instance_id": "7", "commitment_sha256": D.commitment(ans),
                                          "outcome": "committed", "verdict": "PENDING"})
        text = json.dumps(row)
        for leaked in (ans["fixture"], ans["selection"], ans["cause"]):
            self.assertNotIn(leaked, text)


def outcome(cause):
    return {"reverted": cause is not None, "cause": cause}


class Judge(unittest.TestCase):
    def setUp(self):
        self.ans = D.answer(SEED, "7", FIXTURES)
        self.committed = D.commitment(self.ans)

    def judge(self, ans=None, out=None, committed=None):
        return D.judge(committed or self.committed, ans or self.ans, out or outcome(self.ans["cause"]), SEED,
                       FIXTURES)

    def test_pass(self):
        self.assertEqual(self.judge(), {"verdict": "PASS", "reasons": []})

    def test_tampered_key(self):
        # the answer edited after the run to match what was observed
        other = next(c for c in ("build_break", "lint_regression") if c != self.ans["cause"])
        tampered = dict(self.ans, cause=other)
        self.assertEqual(self.judge(ans=tampered, out=outcome(other)),
                         {"verdict": "FAIL", "reasons": ["commitment_mismatch", "answer_not_from_seed"]})
        for field in ("fixture", "selection", "cycle_id"):
            got = self.judge(ans=dict(self.ans, **{field: self.ans[field] + "x"}))
            self.assertEqual(got["verdict"], "FAIL")
            self.assertEqual(got["reasons"][0], "commitment_mismatch")

    def test_commitment_without_the_seed(self):
        forged = dict(self.ans, selection="0" * 64)
        self.assertEqual(self.judge(ans=forged, committed=D.commitment(forged)),
                         {"verdict": "FAIL", "reasons": ["answer_not_from_seed"]})

    def test_not_reverted(self):
        self.assertEqual(self.judge(out=outcome(None)), {"verdict": "FAIL", "reasons": ["not_reverted"]})

    def test_cause_mismatch(self):
        for cause in D.revert.CAUSES:
            if cause != self.ans["cause"]:
                self.assertEqual(self.judge(out=outcome(cause)), {"verdict": "FAIL", "reasons": ["cause_mismatch"]})

    def test_every_reason(self):
        forged = dict(self.ans, selection="1" * 64)
        self.assertEqual(self.judge(ans=forged, out=outcome(None)),
                         {"verdict": "FAIL", "reasons": ["commitment_mismatch", "answer_not_from_seed",
                                                         "not_reverted"]})

    def test_unusable(self):
        bad_answers = [None, [], dict(self.ans, drill="lesson"), dict(self.ans, extra=1),
                       {k: v for k, v in self.ans.items() if k != "cause"}, dict(self.ans, fixture=""),
                       dict(self.ans, cycle_id=7), dict(self.ans, cause=""), dict(self.ans, selection=None)]
        for ans in bad_answers:
            with self.assertRaises(D.Unusable, msg=ans):
                D.judge(self.committed, ans, outcome(self.ans["cause"]), SEED, FIXTURES)
        bad_outcomes = [None, {"reverted": True}, {"reverted": 1, "cause": "unknown"},
                        {"reverted": True, "cause": None}, {"reverted": False, "cause": "unknown"},
                        {"reverted": True, "cause": "flaky_dependency"}, dict(outcome("unknown"), extra=1)]
        for out in bad_outcomes:
            with self.assertRaises(D.Unusable, msg=out):
                D.judge(self.committed, self.ans, out, SEED, FIXTURES)
        for committed in (None, "A" * 64, "a" * 63, self.committed + "0"):
            with self.assertRaises(D.Unusable):
                D.judge(committed, self.ans, outcome(self.ans["cause"]), SEED, FIXTURES)
        with self.assertRaises(D.Unusable):
            D.judge(self.committed, self.ans, outcome(self.ans["cause"]), bytes(8), FIXTURES)


# ---------------------------------------------------------------- the run

RED_RUN = {"results": [{"id": "t1", "status": "fail"}, {"id": "t2", "status": "pass"}]}
GREEN_RUN = {"results": [{"id": "t1", "status": "pass"}, {"id": "t2", "status": "pass"}]}
CALM = {"impact": ["t1"], "build_ok": True, "lint": {"eslint": {"before": 3, "after": 3}}}
OBSERVED = {  # what the contained runs at a planted head would report, per planted cause
    "test_regression": ([RED_RUN] * 4, CALM),
    "build_break": ([{"results": []}] * 4, dict(CALM, build_ok=False)),
    "lint_regression": ([RED_RUN] * 4, dict(CALM, lint={"eslint": {"before": 3, "after": 5}})),
}
TS = "2026-10-30T00:00:00Z"


def ledger_with(rows: list[dict], ledger: bytes = b"") -> bytes:
    """Rows chained onto ``ledger`` by ``ledger.append``, the way the cycle writes them."""
    request = json.dumps({"rows": rows}).encode()
    return append.plan_cycle(ledger, ledger, lambda: request).content


class Run(unittest.TestCase):
    def world(self):
        gh, wr, root = world()
        base = gh.seed_commit("t-base", files={"src/a.js": b"export const a = 1;\n", "test/a.test.js": b"ok\n"})
        gh.refs["main"] = gh.refs["brain/integration"] = base
        return gh, wr, base

    def committed(self, fixture_id, extra=()):
        cycle = cycle_choosing(fixture_id)
        start = ledger_with([{"row_id": "g1", "part": "events", "kind": "genesis", "payload": {}}])
        return cycle, ledger_with(list(extra) + [D.commit_row(SEED, cycle, FIXTURES, "d-" + cycle, TS, "a" * 40)],
                                  start)

    def drill(self, wr, ledger, cycle_now="9999", observe=None, fixtures=FIXTURES, previous=None):
        calls = []

        def watch(merge):
            calls.append(merge)
            return observe(merge)

        out = D.run_drill(wr, SEED, fixtures, ledger, ledger if previous is None else previous, cycle_now,
                          watch, "brain/integration", GATE)
        return out, calls

    def test_each_planted_cause_is_reverted_and_matches(self):
        for fixture in FIXTURES:
            with self.subTest(fixture["id"]):
                gh, wr, base = self.world()
                cycle, ledger = self.committed(fixture["id"])
                out, calls = self.drill(wr, ledger, observe=lambda m, c=fixture["cause"]: OBSERVED[c])
                self.assertEqual((out["verdict"], out["reasons"]), ("PASS", []))
                self.assertEqual(out["answer"], D.answer(SEED, cycle, FIXTURES))
                self.assertEqual(out["outcome"], {"reverted": True, "cause": fixture["cause"]})
                merge = out["planted"]["merge"]
                self.assertEqual(calls, [merge])
                first = gh.commits[merge]["parents"][0]
                self.assertEqual(first, base)
                self.assertEqual(gh.read_file("brain/drill/9999", "src/a.js"), fixture["files"]["src/a.js"].encode())
                self.assertEqual(out["revert"]["tree"], gh.commits[base]["tree"])
                self.assertEqual(gh.commits[out["revert"]["commit"]]["tree"], gh.commits[base]["tree"])
                self.assertEqual(gh.refs["brain/drill/9999-revert"], out["revert"]["commit"])
                planted_check = [c for c in gh.checks if c["head_sha"] == gh.commits[merge]["parents"][1]]
                self.assertIn("not a gate decision", json.dumps(planted_check))
                self.assertEqual(gh.refs["main"], base)

    def test_another_cause_fails(self):
        gh, wr, base = self.world()
        cycle, ledger = self.committed("failing-test")
        out, _ = self.drill(wr, ledger, observe=lambda m: OBSERVED["lint_regression"])
        self.assertEqual((out["verdict"], out["reasons"]), ("FAIL", ["cause_mismatch"]))
        self.assertEqual(out["outcome"], {"reverted": True, "cause": "lint_regression"})

    def test_green_watch_is_not_reverted(self):
        gh, wr, base = self.world()
        cycle, ledger = self.committed("failing-test")
        out, _ = self.drill(wr, ledger, observe=lambda m: ([GREEN_RUN], CALM))
        self.assertEqual((out["verdict"], out["reasons"]), ("FAIL", ["not_reverted"]))
        self.assertFalse(out["revert"]["reverted"])
        self.assertNotIn("brain/drill/9999-revert", gh.refs)

    def test_commitment_not_from_the_seed_plants_nothing(self):
        gh, wr, base = self.world()
        forged = D.commit_row(bytes(range(1, 33)), "1234", FIXTURES, "d-1234", TS, "a" * 40)
        ledger = ledger_with([forged])
        before = len(gh.requests)
        out, calls = self.drill(wr, ledger, observe=lambda m: OBSERVED["test_regression"])
        self.assertEqual((out["verdict"], out["reasons"]), ("FAIL", ["commitment_mismatch", "not_reverted"]))
        self.assertEqual((out["planted"], out["revert"], calls), (None, None, []))
        self.assertEqual(len(gh.requests), before)

    def assertNothingWritten(self, gh, error, ledger, cycle_now="9999", previous=None, fixtures=FIXTURES):
        before = len(gh.requests)
        with self.assertRaises(error):
            self.drill(W.Writer("acme/toy", gh), ledger, cycle_now, lambda m: OBSERVED["test_regression"],
                       fixtures, previous)
        self.assertEqual(len(gh.requests), before)

    def test_no_commitment(self):
        gh, wr, base = self.world()
        self.assertNothingWritten(gh, D.NoCommitment, b"")
        self.assertNothingWritten(gh, D.NoCommitment, ledger_with([{"row_id": "x", "part": "events"}]))
        other = dict(D.commit_row(SEED, "5", FIXTURES, "d5", TS, "a" * 40), part="events")
        self.assertNothingWritten(gh, D.NoCommitment, ledger_with([other]))
        lesson = D.commit_row(SEED, "5", FIXTURES, "d5", TS, "a" * 40)
        lesson["payload"] = dict(lesson["payload"], drill="lesson")
        self.assertNothingWritten(gh, D.NoCommitment, ledger_with([lesson]))

    def test_revealed_commitment_is_spent(self):
        gh, wr, base = self.world()
        cycle, ledger = self.committed("failing-test")
        out, _ = self.drill(wr, ledger, observe=lambda m: OBSERVED["test_regression"])
        row = D.reveal_row(out["commitment_sha256"], out["answer"], out["outcome"], out, "r-9999", TS, "b" * 40)
        after = ledger_with([row], ledger)
        self.assertTrue(chain.verify_bytes(after, ledger)["valid"])
        gh2, wr2, _ = self.world()
        self.assertNothingWritten(gh2, D.NoCommitment, after)
        # a newer commitment after the reveal is pending again
        newer = ledger_with([D.commit_row(SEED, "777", FIXTURES, "d-777", TS, "a" * 40)], after)
        self.assertEqual(D.pending_commitment(newer, after)["instance_id"], "777")

    def test_commitment_from_this_cycle_is_refused(self):
        gh, wr, base = self.world()
        cycle, ledger = self.committed("failing-test")
        self.assertNothingWritten(gh, W.Refused, ledger, cycle_now=cycle)

    def test_edited_ledger_stops(self):
        gh, wr, base = self.world()
        cycle, ledger = self.committed("failing-test")
        lines = ledger.splitlines(keepends=True)
        row = json.loads(lines[-1])
        row["payload"]["commitment_sha256"] = D.commitment(D.answer(SEED, "1", FIXTURES))
        edited = b"".join(lines[:-1]) + json.dumps(row).encode() + b"\n"
        self.assertNothingWritten(gh, D.HardStop, edited)
        # a valid chain that is not an append-only extension of the previous version
        self.assertNothingWritten(gh, D.HardStop, ledger, previous=ledger + b'{"row_id": "gone"}\n')

    def test_unusable_inputs_write_nothing(self):
        gh, wr, base = self.world()
        cycle, ledger = self.committed("failing-test")
        self.assertNothingWritten(gh, D.Unusable, ledger, fixtures=[{"id": "x", "cause": "nope"}])
        no_files = [{k: v for k, v in f.items() if k != "files"} for f in FIXTURES]
        self.assertNothingWritten(gh, D.Unusable, ledger, fixtures=no_files)
        empty_files = [dict(f, files={}) for f in FIXTURES]
        self.assertNothingWritten(gh, D.Unusable, ledger, fixtures=empty_files)
        bad = dict(D.commit_row(SEED, "5", FIXTURES, "d5", TS, "a" * 40))
        bad["payload"] = dict(bad["payload"], commitment_sha256="xyz")
        self.assertNothingWritten(gh, D.Unusable, ledger_with([bad]))

    def test_reveal_row(self):
        gh, wr, base = self.world()
        cycle, ledger = self.committed("broken-build")
        out, _ = self.drill(wr, ledger, observe=lambda m: OBSERVED["build_break"])
        row = D.reveal_row(out["commitment_sha256"], out["answer"], out["outcome"], out, "r-9999", TS, "b" * 40)
        self.assertEqual((row["part"], row["kind"], row["cause"]), ("drill", "reveal", "build_break"))
        self.assertEqual(row["payload"], {"drill": "revert", "question": "cause", "family": "revert",
                                          "instance_id": cycle, "commitment_sha256": out["commitment_sha256"],
                                          "revealed_sha256": D.commitment(out["answer"]), "answer": out["answer"],
                                          "outcome": "build_break", "verdict": "PASS", "reasons": []})
        missed = D.reveal_row(out["commitment_sha256"], out["answer"], outcome(None),
                              {"verdict": "FAIL", "reasons": ["not_reverted"]}, "r", TS, "b" * 40)
        self.assertNotIn("cause", missed)
        self.assertEqual(missed["payload"]["outcome"], "not_reverted")


# ---------------------------------------------------------------- command line

def request(**fields):
    base = {"drill_seed": SEED.hex(), "cycle_id": "7", "fixtures": [{"id": f["id"], "cause": f["cause"]}
                                                                   for f in FIXTURES]}
    base.update(fields)
    return json.dumps(base).encode()


class CommandLine(unittest.TestCase):
    def test_commit_and_reveal(self):
        ans = D.answer(SEED, "7", FIXTURES)
        self.assertEqual(cli(request(), "commit"), (0, {"commitment_sha256": D.commitment(ans)}, ""))
        self.assertEqual(cli(request(), "reveal"), (0, {"answer": ans, "commitment_sha256": D.commitment(ans)}, ""))

    def judge_request(self, ans, out):
        fixtures = json.loads(request())["fixtures"]
        return json.dumps({"drill_seed": SEED.hex(), "fixtures": fixtures, "answer": ans, "outcome": out,
                           "commitment_sha256": D.commitment(D.answer(SEED, "7", FIXTURES))}).encode()

    def test_judge(self):
        ans = D.answer(SEED, "7", FIXTURES)
        self.assertEqual(cli(self.judge_request(ans, outcome(ans["cause"])), "judge"),
                         (0, {"verdict": "PASS", "reasons": []}, ""))
        other = next(c for c in ("build_break", "lint_regression") if c != ans["cause"])
        tampered = dict(ans, cause=other)
        self.assertEqual(cli(self.judge_request(tampered, outcome(other)), "judge")[:2],
                         (1, {"verdict": "FAIL", "reasons": ["commitment_mismatch", "answer_not_from_seed"]}))

    def test_unusable(self):
        cases = [(request(), []), (request(), ["drill"]), (request(), ["commit", "x"]), (b"{", ["commit"]),
                 (b"\xff", ["reveal"]), (request(extra=1), ["commit"]), (request(drill_seed="AB" * 32), ["commit"]),
                 (request(drill_seed="0" * 63), ["commit"]), (request(drill_seed="00" * 31), ["reveal"]),
                 (request(drill_seed=7), ["commit"]), (request(fixtures=[]), ["commit"]),
                 (b'{"drill_seed": "", "drill_seed": "", "cycle_id": "1", "fixtures": []}', ["commit"]),
                 (request(), ["judge"])]
        empty = {"commit": {"commitment_sha256": None}, "reveal": {"answer": None, "commitment_sha256": None}}
        for stdin, argv in cases:
            code, out, err = cli(stdin, *argv)
            want = empty.get(argv[0] if len(argv) == 1 else None, {"verdict": None, "reasons": []})
            self.assertEqual((code, out), (2, want), (stdin, argv))
            self.assertTrue(err.startswith("unusable input: "), err)


if __name__ == "__main__":
    unittest.main()
