"""Test 14's check of the founder ledger (``founder-ledger.jsonl``): the rules are ``ledger.founder``'s (tohum/26's
founder row, tohum/13's closing rule; listed in its docstring, the one source), each bound by a test below, and this
ledger is held to them on every push. Run from the brain's root."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))

from ledger import chain, founder  # noqa: E402
from ledger.founder import FOUNDER, LEDGER, PAGE, problems, spec_kinds  # noqa: E402


# ---------------------------------------------------------------- a synthetic ledger

def _payload(n: int) -> dict:
    return {"summary": "row %d" % n, "refs": []}


def build(specs: list[dict]) -> tuple[bytes, list[str]]:
    """A chained file of founder rows, each spec's keys over a valid row; ``supersedes`` may be an int, the index
    of an earlier row whose hash it names. Returns the bytes and every row's hash."""
    prev, lines, hashes = chain.ZERO_HASH, [], []
    for n, spec in enumerate(specs):
        row = {"row_id": "f%d" % n, "ts": "2026-10-31T00:00:%02dZ" % n, "part": FOUNDER, "kind": "decision",
               "payload": _payload(n), "derivation": "llm_inference", "trust": "inferred",
               "snapshot_id": "a" * 40, "evidence_refs": [], "prev_hash": prev}
        row.update(spec)
        if isinstance(row.get("supersedes"), int):
            row["supersedes"] = hashes[row["supersedes"]]
        for key in [k for k, v in row.items() if v is None]:
            del row[key]
        row["row_hash"] = chain.row_hash(row)
        prev = row["row_hash"]
        hashes.append(prev)
        lines.append(json.dumps(row, ensure_ascii=False))
    return ("\n".join(lines) + "\n").encode("utf-8"), hashes


KINDS = frozenset({"session_start", "decision", "build", "blocked", "seed_issue", "cost", "session_end"})


class Rules(unittest.TestCase):
    def check(self, specs: list[dict]) -> list[str]:
        return problems(build(specs)[0], KINDS)

    def test_valid_rows_are_clean(self):
        self.assertEqual(self.check([{"kind": k} for k in sorted(KINDS)]), [])

    def test_unknown_kind_open_then_closed(self):
        self.assertEqual(len(self.check([{}, {"kind": "learning"}])), 1)
        self.assertEqual(self.check([{}, {"kind": "learning"}, {"supersedes": 1}]), [])

    def test_wrong_part_open_then_closed(self):
        self.assertEqual(len(self.check([{"part": "events"}])), 1)
        self.assertEqual(self.check([{"part": "events"}, {"supersedes": 0}]), [])

    def test_supersedes_naming_a_valid_row(self):
        found = self.check([{}, {"supersedes": 0}])
        self.assertEqual(len(found), 1)
        self.assertIn("breaks no meaning rule", found[0])

    def test_supersedes_naming_no_row_of_this_file(self):
        # a later row of the same file cannot be named: its hash depends on this row through prev_hash
        other = build([{"kind": "learning"}])[1][0]
        for target in ("b" * 64, other):
            with self.subTest(target=target):
                found = self.check([{}, {"supersedes": target}])
                self.assertEqual(len(found), 1)
                self.assertIn("names no earlier row", found[0])

    def test_a_broken_closer_closes_nothing(self):
        # the closer's own kind is unknown: both rows stay open; a third valid row may close the closer only
        found = self.check([{"kind": "learning"}, {"kind": "note", "supersedes": 0}])
        self.assertEqual(len(found), 2)
        found = self.check([{"kind": "learning"}, {"kind": "note", "supersedes": 0}, {"supersedes": 1}])
        self.assertEqual(len(found), 1)
        self.assertIn("line 1", found[0])

    def test_a_closer_with_a_bad_shape_closes_nothing(self):
        found = self.check([{"kind": "learning"}, {"supersedes": 0, "payload": {"summary": "x"}}])
        self.assertTrue(any("line 1" in p and "not closed" in p for p in found))

    def test_closing_a_closed_row_again_is_allowed(self):
        self.assertEqual(self.check([{"kind": "learning"}, {"supersedes": 0}, {"supersedes": 0}]), [])

    def test_payload_shape(self):
        for payload in ({"summary": "x"}, {"summary": "", "refs": []}, {"summary": "x", "refs": [1]},
                        {"summary": "x", "refs": [], "extra": 1}, {"summary": "x", "refs": "a"}, "x"):
            with self.subTest(payload=payload):
                self.assertNotEqual(self.check([{"payload": payload}]), [])

    def test_row_fields(self):
        for spec in ({"cause2": "x"}, {"ts": "2026-10-31"}, {"trust": "sure"}, {"derivation": "guess"},
                     {"evidence_refs": [{"path": "a", "line_start": 2, "line_end": 1}]}, {"snapshot_id": ""},
                     {"snapshot_id": None}, {"supersedes": "B" * 64}):
            with self.subTest(spec=spec):
                self.assertNotEqual(self.check([spec]), [])

    def test_a_broken_chain_is_reported_alone(self):
        data = build([{}, {"kind": "learning"}])[0].replace(b"row 0", b"row X")
        found = problems(data, KINDS)
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0].startswith("chain: row_hash does not match"))
        data = build([{}])[0].replace(b'"refs": []', b'"refs": [1.5]')
        self.assertEqual(problems(data, KINDS), ["chain: floating point number in a hashed row (tohum/26) (line 1)"])


class KindsAreTheSpecs(unittest.TestCase):
    def _page(self, text: str) -> str:
        fh = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        self.addCleanup(os.unlink, fh.name)
        with fh:
            fh.write(text)
        return fh.name

    def test_page_lists_the_kinds(self):
        self.assertEqual(spec_kinds(), KINDS)

    def test_a_changed_page_is_seen(self):
        with open(PAGE, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("`blocked`, ", text)
        self.assertEqual(spec_kinds(self._page(text.replace("`blocked`, ", ""))), KINDS - {"blocked"})
        self.assertEqual(spec_kinds(self._page(text.replace("`blocked`, ", "`blocked`, `learning`, "))),
                         KINDS | {"learning"})

    def test_list_not_guessed(self):
        with open(PAGE, encoding="utf-8") as fh:
            text = fh.read()
        marker = "**`founder` satırı:**"
        self.assertEqual(text.count(marker), 1)
        start = text.index(marker)
        listed = text[start:text.index("}", start) + 1]
        for page in (text.replace(marker, "**founder:**"), text + "\n" + listed + "\n",
                     text.replace(listed, marker + " `kind` ∈ {}")):
            with self.assertRaises(AssertionError):
                spec_kinds(self._page(page))


class ThisLedger(unittest.TestCase):
    def test_founder_ledger_has_no_problem(self):
        with open(LEDGER, "rb") as fh:
            self.assertEqual(problems(fh.read(), spec_kinds()), [])

    def test_without_its_closers_the_closed_rows_are_open(self):
        # the file cut before its first closing row: each row a later row closes is reported, and no other
        with open(LEDGER, "rb") as fh:
            lines = chain._lines(fh.read())
        rows = [chain.parse_row(line.decode("utf-8")) for line in lines]
        first = next(i for i, row in enumerate(rows) if "supersedes" in row)  # f306 closes f185
        named = {row["supersedes"] for row in rows if "supersedes" in row}
        found = problems(b"".join(line + b"\n" for line in lines[:first]), spec_kinds())
        expected = sorted(i + 1 for i, row in enumerate(rows[:first]) if row["row_hash"] in named)
        self.assertEqual(sorted(int(p.split()[1]) for p in found), expected)


class Append(unittest.TestCase):
    """``ledger.founder.append`` and its command line: a row is written only when MF2's row scan is clean and the
    new file has no problem the old one had not; a refused row leaves the file's bytes as they were."""

    SHA = "c" * 40

    def ledger(self, data: bytes) -> str:
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: [os.unlink(os.path.join(d, n)) for n in os.listdir(d)] and None or os.rmdir(d))
        path = os.path.join(d, "founder-ledger.jsonl")
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def run_cli(self, path: str, *argv: str, stdin: bytes = b"") -> tuple[int, dict]:
        import io
        out = io.StringIO()
        old, sys.stdout = sys.stdout, out
        try:
            code = founder.main([argv[0], "--ledger", path, *argv[1:]], stdin=io.BytesIO(stdin))
        finally:
            sys.stdout = old
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        return code, json.loads(lines[0])

    def add(self, path: str, *extra: str, kind: str = "decision", summary: str = "a row") -> tuple[int, dict]:
        return self.run_cli(path, "append", "--kind", kind, "--summary", summary, "--snapshot", self.SHA,
                            "--ts", "2026-10-31T23:00:00Z", *extra)

    def read(self, path: str) -> bytes:
        with open(path, "rb") as fh:
            return fh.read()

    def test_first_row_of_an_empty_file(self):
        path = self.ledger(b"")
        code, out = self.add(path, "--ref", "a.py", "--ref", "b.py")
        self.assertEqual((code, out["ok"], out["row_id"]), (0, True, "f1"))
        row = chain.parse_row(self.read(path).decode("utf-8"))
        self.assertEqual(row["prev_hash"], chain.ZERO_HASH)
        self.assertEqual(row["payload"], {"summary": "a row", "refs": ["a.py", "b.py"]})
        self.assertEqual((row["part"], row["snapshot_id"], row["ts"]), (FOUNDER, self.SHA, "2026-10-31T23:00:00Z"))
        self.assertEqual(problems(self.read(path), KINDS), [])

    def test_a_row_follows_the_last_and_keeps_the_old_bytes(self):
        data, hashes = build([{}, {"kind": "build"}])
        path = self.ledger(data)
        code, out = self.add(path, "--derivation", "test_verified", "--trust", "verified")
        self.assertEqual((code, out["row_id"]), (0, "f2"))
        new = self.read(path)
        self.assertTrue(new.startswith(data))
        row = chain.parse_row(new[len(data):].decode("utf-8"))
        self.assertEqual(row["prev_hash"], hashes[-1])
        self.assertEqual(row["row_hash"], out["row_hash"])
        self.assertEqual((row["derivation"], row["trust"]), ("test_verified", "verified"))
        self.assertTrue(chain.verify_bytes(new, data)["valid"])
        self.assertEqual(problems(new, KINDS), [])

    def test_a_row_that_breaks_a_rule_is_not_written(self):
        data = build([{}])[0]
        for extra, kind, what in ((), "learning", "kind 'learning'"),\
                                 (("--derivation", "guess"), "decision", "derivation"),\
                                 (("--trust", "sure"), "decision", "trust"),\
                                 (("--supersedes", "B" * 64), "decision", "supersedes"),\
                                 (("--supersedes", "b" * 64), "decision", "names no earlier row"),\
                                 (("--ts", "2026-10-31"), "decision", "ts"),\
                                 (("--ref", ""), "decision", "refs"):
            with self.subTest(extra=extra, kind=kind):
                path = self.ledger(data)
                code, out = self.add(path, *extra, kind=kind)
                self.assertEqual((code, out["ok"]), (1, False))
                self.assertTrue(any(r.startswith("problem:") and what in r for r in out["reasons"]), out)
                self.assertEqual(self.read(path), data)
        path = self.ledger(data)
        code, out = self.run_cli(path, "append", "--kind", "decision", "--summary", "", "--snapshot", self.SHA)
        self.assertEqual((code, self.read(path)), (1, data))
        code, out = self.run_cli(path, "append", "--kind", "decision", "--summary", "x", "--snapshot", "")
        self.assertEqual((code, self.read(path)), (1, data))

    def test_closing_an_open_row_is_written_and_naming_a_valid_row_is_not(self):
        data, hashes = build([{}, {"kind": "learning"}])
        path = self.ledger(data)
        self.assertEqual(len(problems(data, KINDS)), 1)
        code, out = self.add(path, "--supersedes", hashes[0])
        self.assertEqual(code, 1)
        self.assertTrue(any("breaks no meaning rule" in r for r in out["reasons"]))
        code, out = self.add(path, "--supersedes", hashes[1])
        self.assertEqual(code, 0, out)
        self.assertEqual(problems(self.read(path), KINDS), [])

    def test_only_new_problems_refuse(self):
        # an open problem already in the file does not block a valid row, and does not excuse a second break
        data = build([{"kind": "learning"}])[0]
        path = self.ledger(data)
        self.assertEqual(self.add(path)[0], 0)
        code, out = self.add(path, kind="learning")
        self.assertEqual(code, 1)
        self.assertEqual([r for r in out["reasons"]],
                         ["problem:line 3 (f2): kind 'learning' is not one of 26's founder kinds, not closed"])

    def test_a_secret_shaped_summary_is_not_written(self):
        data = build([{}])[0]
        token = "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
        for summary in ("the token " + token, "pass" + "word = " + "'" + "hunter2hunter2" + "'"):
            with self.subTest(summary=summary[:8]):
                path = self.ledger(data)
                code, out = self.add(path, summary=summary)
                self.assertEqual(code, 1)
                self.assertTrue(out["reasons"] and all(r.startswith("row_scan:") for r in out["reasons"]), out)
                self.assertNotIn(token, json.dumps(out))
                self.assertNotIn("hunter2", json.dumps(out))
                self.assertEqual(self.read(path), data)

    def test_summary_from_stdin(self):
        path = self.ledger(b"")
        text = "line one, \"quoted\" and ü\nline two"
        code, out = self.run_cli(path, "append", "--kind", "build", "--summary", "-", "--snapshot", self.SHA,
                                 stdin=(text + "\n").encode("utf-8"))
        self.assertEqual(code, 0, out)
        self.assertEqual(chain.parse_row(self.read(path).decode("utf-8"))["payload"]["summary"], text)
        code, out = self.run_cli(path, "append", "--kind", "build", "--summary", "-", "--snapshot", self.SHA,
                                 stdin=b"\xff")
        self.assertEqual(code, 2)

    def test_unusable_inputs_write_nothing(self):
        good = build([{}])[0]
        broken = good.replace(b"row 0", b"row X")
        cases = [(broken, ("append", "--kind", "decision", "--summary", "x", "--snapshot", self.SHA)),
                 (build([{"row_id": "r7"}])[0], ("append", "--kind", "decision", "--summary", "x",
                                                 "--snapshot", self.SHA)),
                 (good + b"{", ("append", "--kind", "decision", "--summary", "x", "--snapshot", self.SHA)),
                 (good, ("append", "--kind", "decision", "--summary", "x")),
                 (good, ("append", "--kind", "decision", "--summary", "x", "--snapshot", self.SHA, "--page",
                         os.path.join(ROOT, "no-such-page.md"))),
                 (good, ("rewrite",))]
        for data, argv in cases:
            with self.subTest(argv=argv):
                path = self.ledger(data)
                code, out = self.run_cli(path, *argv)
                self.assertEqual((code, out["ok"]), (2, False), out)
                self.assertEqual(self.read(path), data)
                self.assertEqual(os.listdir(os.path.dirname(path)), ["founder-ledger.jsonl"])
        code, out = self.run_cli(os.path.join(ROOT, "no-such-ledger.jsonl"), "check")
        self.assertEqual(code, 2)

    def test_check(self):
        self.assertEqual(self.run_cli(self.ledger(build([{}])[0]), "check"), (0, {"ok": True, "problems": []}))
        code, out = self.run_cli(self.ledger(build([{"kind": "learning"}])[0]), "check")
        self.assertEqual((code, len(out["problems"])), (1, 1))
        # a broken chain is the file's one problem, reported, not an unusable input
        code, out = self.run_cli(self.ledger(build([{}])[0].replace(b"row 0", b"row X")), "check")
        self.assertEqual((code, out["problems"]), (1, ["chain: row_hash does not match the row (line 1)"]))

    def test_no_temporary_file_is_left(self):
        path = self.ledger(build([{}])[0])
        self.add(path)
        self.add(path, kind="learning")
        self.assertEqual(os.listdir(os.path.dirname(path)), ["founder-ledger.jsonl"])

    def test_the_command_runs_from_referee(self):
        import subprocess
        path = self.ledger(b"")
        proc = subprocess.run([sys.executable, "-m", "ledger.founder", "append", "--ledger", path, "--kind",
                               "session_start", "--summary", "-", "--snapshot", self.SHA],
                              cwd=os.path.join(ROOT, "referee"), input=b"started", capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["row_id"], "f1")
        proc = subprocess.run([sys.executable, "-m", "ledger.founder", "check"], cwd=os.path.join(ROOT, "referee"),
                              capture_output=True)
        self.assertEqual((proc.returncode, json.loads(proc.stdout)), (0, {"ok": True, "problems": []}))


if __name__ == "__main__":
    unittest.main()
