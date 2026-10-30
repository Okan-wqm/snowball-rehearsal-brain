"""Test 40 (asama-0/09) and group ``root`` (tohum/29j): ``rekor.anchor`` with a fake signer.

- root: interleaved parts give each part's last stored ``row_hash`` (neither the file's last row nor the part's
  first row); the root is checked against a hand-written canonical text; a new row moves only its part's tip;
  a ledger broken in the middle (where no tip sees it), a row without ``part`` and an empty ledger are unusable;
- anchor: the signer signs the root's hex text as its payload, the entry is ``{uuid, hash: root, identity}``;
  an unavailable signer or one that answers no entry is a hard stop; malformed requests and signers are exit 2;
- verify: each reason from its own case and alone, the closed order when several hold, ``entry_missing``
  suppressing the other two, only the last line of the root file read, unusable files exit 2;
- the cycle: one commit with the new ledger and the chained root row, which the next D1 verifies; an
  unsignable root, a rewritten root file and a repeated root row id commit nothing; on the in-process GitHub
  one ``POST git/commits`` sets both files on ``brain/state`` and ``main`` never moves;
- the command lines, outputs and exits.
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

from ledger import anchor as AN  # noqa: E402
from ledger import append as AP  # noqa: E402
from ledger import chain  # noqa: E402
from target import write as W  # noqa: E402
from fake_github import FakeGitHub  # noqa: E402

ZERO = "0" * 64
WORKFLOW = "https://github.com/acme/referee/.github/workflows/loop.yml@refs/heads/main"


def build(rows, prev=ZERO):
    """An independent writer of chained lines (sorted-key json.dumps is the canonical form for these ASCII rows)."""
    out, hashes = [], []
    for row in rows:
        row = dict(row, prev_hash=prev)
        body = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
        prev = row["row_hash"] = hashlib.sha256(body + prev.encode()).hexdigest()
        hashes.append(prev)
        out.append(json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    return b"".join(out), hashes


ROWS = [{"row_id": "e1", "part": "events", "kind": "a"}, {"row_id": "c1", "part": "cost", "kind": "b"},
        {"row_id": "e2", "part": "events", "kind": "c"}, {"row_id": "d1", "part": "drill", "kind": "d"},
        {"row_id": "c2", "part": "cost", "kind": "e"}, {"row_id": "e3", "part": "events", "kind": "f"},
        {"row_id": "c3", "part": "cost", "kind": "g"}]
LEDGER, H = build(ROWS)


def hand_root(tips):
    text = "{" + ",".join('"%s":"%s"' % (k, tips[k]) for k in sorted(tips)) + "}"
    return hashlib.sha256(text.encode()).hexdigest()


class Root(unittest.TestCase):
    def test_part_tips(self):
        tips = AN.tips(LEDGER)
        self.assertEqual(tips, {"events": H[5], "cost": H[6], "drill": H[3]})
        # the events tip is neither the file's last row nor the part's first row
        self.assertNotEqual(tips["events"], H[-1])
        self.assertNotEqual(tips["events"], H[0])
        self.assertEqual(AN.root_of(tips), hand_root({"events": H[5], "cost": H[6], "drill": H[3]}))

    def test_a_new_row_moves_only_its_part(self):
        more, h2 = build(ROWS + [{"row_id": "d2", "part": "drill", "kind": "h"}])
        before, after = AN.tips(LEDGER), AN.tips(more)
        self.assertEqual(after, dict(before, drill=h2[-1]))
        self.assertNotEqual(AN.root_of(after), AN.root_of(before))

    def test_root_depends_on_the_part_name(self):
        renamed, _ = build([dict(r, part="drills" if r["part"] == "drill" else r["part"]) for r in ROWS])
        self.assertIn("drills", AN.tips(renamed))
        self.assertNotEqual(AN.root_of(AN.tips(renamed)), AN.root_of(AN.tips(LEDGER)))

    def test_a_break_no_tip_sees_is_unusable(self):
        # row e2 edited, hashes not recomputed: every tip is unchanged, the chain is not
        broken = LEDGER.replace(b'"kind":"c"', b'"kind":"X"')
        self.assertEqual(broken.count(b'"kind":"X"'), 1)
        with self.assertRaisesRegex(AN.Unusable, "not a valid chain"):
            AN.tips(broken)

    def test_rows_need_a_part_and_a_ledger_needs_a_row(self):
        for bad in ({"row_id": "x", "kind": "a"}, {"row_id": "x", "part": ""}, {"row_id": "x", "part": 7}):
            data, _ = build([ROWS[0], bad])
            with self.assertRaisesRegex(AN.Unusable, "line 2 has no part"):
                AN.tips(data)
        with self.assertRaisesRegex(AN.Unusable, "empty ledger"):
            AN.tips(b"")


class Signer(unittest.TestCase):
    def test_anchor_signs_root(self):
        root = AN.root_of(AN.tips(LEDGER))
        signer = AN.FakeSigner(True, WORKFLOW, "uuid-1")
        self.assertEqual(AN.anchor(root, signer), {"uuid": "uuid-1", "hash": root, "identity": WORKFLOW})
        self.assertEqual(signer.payloads, [root.encode("ascii")])

    def test_unsignable_hard_stop(self):
        signer = AN.FakeSigner(False)
        with self.assertRaises(AN.Unsignable):
            AN.anchor("a" * 64, signer)
        self.assertTrue(issubclass(AN.Unsignable, AP.HardStop))
        self.assertEqual(signer.payloads, [])

    def test_a_signer_that_answers_no_entry_is_a_hard_stop(self):
        class Silent:
            def __init__(self, answer):
                self.answer = answer

            def sign(self, payload):
                return self.answer

        for answer in (None, {}, {"uuid": "u"}, {"uuid": "", "identity": WORKFLOW}, {"uuid": "u", "identity": 3}):
            with self.assertRaises(AN.Unsignable):
                AN.anchor("a" * 64, Silent(answer))

    def test_root_text_is_64_lowercase_hex(self):
        for bad in ("A" * 64, "a" * 63, "a" * 65, 7, None, "g" * 64):
            with self.assertRaises(AN.Unusable):
                AN.anchor(bad, AN.FakeSigner(True, WORKFLOW, "u"))

    def test_signer_file_shape(self):
        for bad in ({"available": "true", "identity": WORKFLOW, "uuid": "u"}, {"available": 1, "identity": WORKFLOW, "uuid": "u"},
                    {"available": True, "identity": WORKFLOW}, {"available": True, "identity": "", "uuid": "u"}, []):
            with self.assertRaises(AN.Unusable):
                AN.FakeSigner.from_json(bad)
        self.assertFalse(AN.FakeSigner.from_json({"available": False}).available)


def roots_file(*pairs):
    data = b""
    for i, (root, uuid) in enumerate(pairs, 1):
        data = AN.root_row(data, "r%d" % i, "2026-10-30T00:00:0%dZ" % i, root, uuid)
    return data


class Verify(unittest.TestCase):
    def setUp(self):
        self.root = AN.root_of(AN.tips(LEDGER))
        self.roots = roots_file(("b" * 64, "old"), (self.root, "uuid-1"))
        self.rekor = {"entries": {"uuid-1": {"hash": self.root, "identity": WORKFLOW}, "old": {"hash": "b" * 64, "identity": WORKFLOW}}}

    def check(self, ledger=None, roots=None, rekor=None, identity=WORKFLOW):
        return AN.verify(LEDGER if ledger is None else ledger, self.roots if roots is None else roots,
                         self.rekor if rekor is None else rekor, identity)

    def test_verify_good(self):
        self.assertEqual(self.check(), {"valid": True, "reasons": []})

    def test_verify_tip_moved(self):
        moved, _ = build(ROWS + [{"row_id": "e4", "part": "events", "kind": "z"}])
        self.assertEqual(self.check(ledger=moved), {"valid": False, "reasons": ["root_mismatch"]})

    def test_verify_identity_pin(self):
        self.rekor["entries"]["uuid-1"]["identity"] = WORKFLOW.replace("loop.yml", "other.yml")
        self.assertEqual(self.check(), {"valid": False, "reasons": ["identity_mismatch"]})
        self.assertEqual(self.check(identity=WORKFLOW + "x"), {"valid": False, "reasons": ["identity_mismatch"]})

    def test_verify_entry_other_root(self):
        self.rekor["entries"]["uuid-1"]["hash"] = "c" * 64
        self.assertEqual(self.check(), {"valid": False, "reasons": ["entry_root_mismatch"]})

    def test_verify_entry_missing(self):
        del self.rekor["entries"]["uuid-1"]
        self.assertEqual(self.check(), {"valid": False, "reasons": ["entry_missing"]})
        # the entry is missing: neither its hash nor its identity is judged, the root still is
        moved, _ = build(ROWS[:-1])
        self.assertEqual(self.check(ledger=moved, identity="other"), {"valid": False, "reasons": ["root_mismatch", "entry_missing"]})

    def test_reasons_in_order(self):
        moved, _ = build(ROWS[:-1])
        self.rekor["entries"]["uuid-1"] = {"hash": "c" * 64, "identity": "someone"}
        self.assertEqual(self.check(ledger=moved)["reasons"], ["root_mismatch", "entry_root_mismatch", "identity_mismatch"])

    def test_entry_hash_is_compared_with_the_recorded_root(self):
        # the ledger moved and the entry signs the ledger's new root: the record still names the old one
        moved, _ = build(ROWS[:-1])
        self.rekor["entries"]["uuid-1"]["hash"] = AN.root_of(AN.tips(moved))
        self.assertEqual(self.check(ledger=moved)["reasons"], ["root_mismatch", "entry_root_mismatch"])

    def test_only_the_last_root_row_is_read(self):
        # an earlier row naming a missing entry does not count; only the last row decides
        roots = roots_file(("d" * 64, "nowhere"), (self.root, "uuid-1"))
        self.assertTrue(self.check(roots=roots)["valid"])
        # the same rows reversed: the last row now names the missing entry
        roots = roots_file((self.root, "uuid-1"), ("d" * 64, "nowhere"))
        self.assertEqual(self.check(roots=roots)["reasons"], ["root_mismatch", "entry_missing"])

    def test_unusable_inputs(self):
        cases = [dict(roots=b""), dict(roots=b"not json\n"), dict(roots=b'{"root": "%s"}\n' % self.root.encode()),
                 dict(roots=b'{"root": "%s", "rekor_uuid": ""}\n' % self.root.encode()),
                 dict(roots=b'{"root": "%s", "rekor_uuid": "u"}\n' % self.root.upper().encode()),
                 dict(rekor={}), dict(rekor={"entries": []}), dict(rekor={"entries": {"uuid-1": {"hash": self.root}}}),
                 dict(identity=""), dict(identity=None), dict(ledger=LEDGER.replace(b'"kind":"c"', b'"kind":"X"'))]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(AN.Unusable):
                self.check(**case)


class Reader:
    def __init__(self, data):
        self.data, self.calls = data, 0

    def __call__(self):
        self.calls += 1
        return self.data


def req(*rows):
    return json.dumps({"rows": list(rows)}).encode()


class Cycle(unittest.TestCase):
    def run_cycle(self, signer, roots=b"", previous_roots=b"", row_id="r1", ledger=LEDGER, reader=None):
        state = AP.CountingState()
        reader = reader or Reader(req({"row_id": "n1", "part": "events"}))
        out = AN.anchor_cycle(ledger, ledger, roots, previous_roots, reader, signer, state, row_id, "2026-10-30T12:00:00Z")
        return out, state, reader

    def test_one_commit_holds_the_rows_and_the_signed_root(self):
        signer = AN.FakeSigner(True, WORKFLOW, "uuid-1")
        out, state, _ = self.run_cycle(signer)
        self.assertEqual(state.commits, 1)
        self.assertEqual(set(state.files), {"ledger.jsonl", "chain/root.jsonl"})
        new_ledger, roots = state.files["ledger.jsonl"], state.files["chain/root.jsonl"]
        self.assertTrue(chain.verify_bytes(new_ledger, LEDGER)["valid"])
        self.assertEqual(AN.tips(new_ledger)["events"], out["row_hashes"][0])
        self.assertEqual(out["root"], AN.root_of(AN.tips(new_ledger)))
        self.assertNotEqual(out["root"], AN.root_of(AN.tips(LEDGER)))
        self.assertEqual(signer.payloads, [out["root"].encode()])
        self.assertTrue(chain.verify_bytes(roots)["valid"])
        row = json.loads(roots)
        self.assertEqual({k: row[k] for k in ("row_id", "ts", "root", "rekor_uuid", "prev_hash")},
                         {"row_id": "r1", "ts": "2026-10-30T12:00:00Z", "root": out["root"], "rekor_uuid": "uuid-1",
                          "prev_hash": ZERO})
        self.assertEqual(set(row), {"row_id", "ts", "root", "rekor_uuid", "prev_hash", "row_hash"})
        rekor = {"entries": {out["entry"]["uuid"]: out["entry"]}}
        self.assertEqual(AN.verify(new_ledger, roots, rekor, WORKFLOW), {"valid": True, "reasons": []})
        # the next cycle chains its root row onto this one
        state2 = AP.CountingState()
        out2 = AN.anchor_cycle(new_ledger, new_ledger, roots, roots, Reader(req({"row_id": "n2", "part": "cost"})),
                               AN.FakeSigner(True, WORKFLOW, "uuid-2"), state2, "r2", "2026-10-30T13:00:00Z")
        roots2 = state2.files["chain/root.jsonl"]
        self.assertTrue(chain.verify_bytes(roots2, roots)["valid"])
        self.assertEqual(json.loads(roots2.splitlines()[1])["prev_hash"], row["row_hash"])
        rekor["entries"]["uuid-2"] = out2["entry"]
        self.assertTrue(AN.verify(state2.files["ledger.jsonl"], roots2, rekor, WORKFLOW)["valid"])
        # the old ledger against the new record: the tip moved
        self.assertEqual(AN.verify(new_ledger, roots2, rekor, WORKFLOW)["reasons"], ["root_mismatch"])

    def test_unsignable_commits_nothing(self):
        state = AP.CountingState()
        with self.assertRaises(AN.Unsignable):
            AN.anchor_cycle(LEDGER, LEDGER, b"", b"", Reader(req({"row_id": "n1", "part": "x"})), AN.FakeSigner(False),
                            state, "r1", "t")
        self.assertEqual((state.commits, state.files), (0, None))

    def test_a_rewritten_root_file_stops_before_the_request(self):
        roots = roots_file(("a" * 64, "u1"), ("b" * 64, "u2"))
        rewritten = roots_file(("c" * 64, "u1"), ("b" * 64, "u2"))  # a valid chain, not an extension
        for current, previous in ((rewritten, roots), (roots[:-10], roots), (roots.replace(b"u2", b"u3"), roots)):
            state, reader, signer = AP.CountingState(), Reader(b"not json"), AN.FakeSigner(True, WORKFLOW, "u")
            with self.assertRaises(AP.HardStop):
                AN.anchor_cycle(LEDGER, LEDGER, current, previous, reader, signer, state, "r9", "t")
            self.assertEqual((reader.calls, state.commits, signer.payloads), (0, 0, []))

    def test_a_repeated_root_row_id_or_no_ts_commits_nothing(self):
        roots = roots_file(("a" * 64, "u1"))
        state = AP.CountingState()
        for row_id in ("r1", "", None):
            with self.assertRaises(AN.Unusable):
                AN.anchor_cycle(LEDGER, LEDGER, roots, roots, Reader(req({"row_id": "n1", "part": "x"})),
                                AN.FakeSigner(True, WORKFLOW, "u"), state, row_id, "t")
        for ts in ("", None, 7):
            with self.assertRaises(AN.Unusable):
                AN.anchor_cycle(LEDGER, LEDGER, roots, roots, Reader(req({"row_id": "n1", "part": "x"})),
                                AN.FakeSigner(True, WORKFLOW, "u"), state, "r2", ts)
        self.assertEqual(state.commits, 0)

    def test_on_the_target(self):
        gh = FakeGitHub("acme/toy")
        main = gh.seed_commit("t0")
        gh.refs["main"] = main
        head = gh.seed_commit("s0", files={"ledger.jsonl": LEDGER, "status.md": b"s\n"})
        gh.refs["brain/state"] = head
        wr = W.Writer("acme/toy", gh)
        with self.assertRaises(AN.Unsignable):
            AN.anchor_cycle(LEDGER, LEDGER, b"", b"", Reader(req({"row_id": "n1", "part": "x"})), AN.FakeSigner(False),
                            AP.TargetState(wr, head), "r1", "t")
        self.assertEqual(gh.requests, [])
        out = AN.anchor_cycle(LEDGER, LEDGER, b"", b"", Reader(req({"row_id": "n1", "part": "x"})),
                              AN.FakeSigner(True, WORKFLOW, "uuid-1"), AP.TargetState(wr, head), "r1", "t")
        self.assertEqual(sum(1 for r in gh.requests if r[0] == "POST" and r[1].endswith("/git/commits")), 1)
        self.assertEqual(gh.commits[gh.refs["brain/state"]]["parents"], [head])
        ledger, roots = gh.read_file("brain/state", "ledger.jsonl"), gh.read_file("brain/state", "chain/root.jsonl")
        self.assertEqual(gh.read_file("brain/state", "status.md"), b"s\n")
        self.assertEqual(gh.refs["main"], main)
        self.assertTrue(AN.verify(ledger, roots, {"entries": {"uuid-1": out["entry"]}}, WORKFLOW)["valid"])


class CommandLine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def file(self, name, data):
        path = os.path.join(self.tmp.name, name)
        with open(path, "wb") as fh:
            fh.write(data if isinstance(data, bytes) else json.dumps(data).encode())
        return path

    def run_cli(self, args, stdin=b""):
        proc = subprocess.run([sys.executable, "-m", "ledger.anchor"] + args, input=stdin, capture_output=True,
                              cwd=REFEREE, timeout=60)
        lines = proc.stdout.decode().splitlines()
        self.assertEqual(len(lines), 1, proc.stdout)
        return proc.returncode, json.loads(lines[0]), proc.stderr.decode()

    def test_root(self):
        code, out, _ = self.run_cli(["root", self.file("l", LEDGER)])
        self.assertEqual((code, out), (0, {"tips": {"events": H[5], "cost": H[6], "drill": H[3]},
                                           "root": hand_root({"events": H[5], "cost": H[6], "drill": H[3]})}))
        code, out, err = self.run_cli(["root", self.file("b", LEDGER.replace(b'"kind":"c"', b'"kind":"X"'))])
        self.assertEqual((code, out), (2, {"tips": None, "root": None}))
        self.assertIn("not a valid chain", err)
        self.assertEqual(self.run_cli(["root", os.path.join(self.tmp.name, "missing")])[:2], (2, {"tips": None, "root": None}))

    def test_anchor(self):
        root = "ab" * 32
        signer = self.file("s", {"available": True, "identity": WORKFLOW, "uuid": "uuid-1", "note": "ignored"})
        code, out, _ = self.run_cli(["anchor", signer], json.dumps({"root": root}).encode())
        self.assertEqual((code, out), (0, {"ok": True, "hard_stop": False, "entry": {"uuid": "uuid-1", "hash": root, "identity": WORKFLOW}}))
        code, out, err = self.run_cli(["anchor", self.file("n", {"available": False, "identity": WORKFLOW, "uuid": "u"})],
                                      json.dumps({"root": root}).encode())
        self.assertEqual((code, out), (1, {"ok": False, "hard_stop": True, "entry": None}))
        self.assertIn("hard stop", err)
        for stdin in (b'{"root": "%s", "x": 1}' % root.encode(), b'{"root": "%s"}' % root.upper().encode(), b"",
                      b'{"root": "%s", "root": "%s"}' % (root.encode(), root.encode())):
            self.assertEqual(self.run_cli(["anchor", signer], stdin)[:2], (2, {"ok": False, "hard_stop": False, "entry": None}))
        self.assertEqual(self.run_cli(["anchor", self.file("x", {"available": "yes"})], json.dumps({"root": root}).encode())[:2],
                         (2, {"ok": False, "hard_stop": False, "entry": None}))

    def test_verify(self):
        root = AN.root_of(AN.tips(LEDGER))
        roots = self.file("r", roots_file((root, "uuid-1")))
        rekor = {"entries": {"uuid-1": {"hash": root, "identity": WORKFLOW, "logIndex": 7}}}
        args = ["verify", self.file("l", LEDGER), roots, self.file("k", rekor)]
        self.assertEqual(self.run_cli(args, json.dumps({"identity": WORKFLOW}).encode())[:2], (0, {"valid": True, "reasons": []}))
        self.assertEqual(self.run_cli(args, json.dumps({"identity": "x"}).encode())[:2],
                         (1, {"valid": False, "reasons": ["identity_mismatch"]}))
        self.assertEqual(self.run_cli(args, json.dumps({"identity": WORKFLOW, "more": 1}).encode())[:2],
                         (2, {"valid": False, "reasons": []}))
        self.assertEqual(self.run_cli(["verify", self.file("l", LEDGER), roots], json.dumps({"identity": WORKFLOW}).encode())[:2],
                         (2, {"error": "usage"}))


if __name__ == "__main__":
    unittest.main()
