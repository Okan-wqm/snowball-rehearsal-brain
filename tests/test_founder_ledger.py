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

sys.path.insert(0, os.path.join(ROOT, "referee", "tests"))
from git_store import HistoryGit  # noqa: E402


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


class Cli(unittest.TestCase):
    """The command line's helpers, shared by the test classes below; no test of its own."""

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

    def reports(self, *reports) -> str:
        d = tempfile.mkdtemp()
        self.addCleanup(lambda: [os.unlink(os.path.join(d, n)) for n in os.listdir(d)] and None or os.rmdir(d))
        for name, body in reports:
            with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
                fh.write(body if isinstance(body, str) else json.dumps(body))
        return d


class Append(Cli):
    """``ledger.founder.append`` and its command line: a row is written only when MF2's row scan is clean and the
    new file has no problem the old one had not; a refused row leaves the file's bytes as they were."""

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


class Items(Cli):
    """``closes:`` refs (checked by ``problems``) and ``open``: which reported items are still open."""

    def closer(self, *names: str, **spec) -> dict:
        return {"payload": {"summary": "closes", "refs": ["a.py"] + ["closes:" + n for n in names]}, **spec}

    def listed(self, data: bytes, reports: str | None = None) -> tuple[int, dict]:
        path = self.ledger(data)
        return self.run_cli(path, "open", "--reports", reports or self.reports())

    def ids(self, data: bytes, reports: str | None = None) -> list[str]:
        code, out = self.listed(data, reports)
        self.assertEqual((code, out["problems"]), (0, []), out)
        return [item["id"] for item in out["open"]]

    def test_seed_issue_and_blocked_rows_are_items_until_closed(self):
        rows = [{"kind": k} for k in sorted(KINDS)]  # blocked f0, build f1, cost f2, decision f3, seed_issue f4
        self.assertEqual(self.ids(build(rows)[0]), ["f0", "f4"])
        self.assertEqual(self.ids(build(rows + [self.closer("f4")])[0]), ["f0"])
        self.assertEqual(self.ids(build(rows + [self.closer("f0", "f4")])[0]), [])
        self.assertEqual(self.ids(build(rows + [self.closer("f0"), self.closer("f4", kind="seed_issue")])[0]),
                         ["f8"])
        code, out = self.listed(build([{"kind": "seed_issue", "payload": {"summary": "x" * 300, "refs": []}}])[0])
        self.assertEqual(out["open"], [{"id": "f0", "source": "ledger", "kind": "seed_issue",
                                        "ts": "2026-10-31T00:00:00Z", "head": "x" * 200}])

    def test_bad_closes_refs_are_problems(self):
        item = {"kind": "seed_issue"}
        for rows, what in (([item, self.closer("f9")], "names no earlier seed_issue or blocked row"),
                           ([{}, self.closer("f0")], "names no earlier seed_issue or blocked row"),
                           ([self.closer("f1"), item], "names no earlier seed_issue or blocked row"),
                           ([self.closer("f0", kind="seed_issue")], "names no earlier seed_issue or blocked row"),
                           ([item, self.closer("seed-040")], "names no earlier seed_issue or blocked row"),
                           ([item, self.closer("f0", "f0")], "is named twice"),
                           ([item, self.closer("f0"), self.closer("f0")], "already closed by f1")):
            with self.subTest(what=what, rows=len(rows)):
                found = problems(build(rows)[0], KINDS)
                self.assertEqual(len(found), 1, found)
                self.assertIn(what, found[0])
                code, out = self.listed(build(rows)[0])
                self.assertEqual((code, out["open"]), (1, []))

    def test_a_broken_closer_closes_nothing(self):
        item = {"kind": "seed_issue"}
        for spec in ({"kind": "learning"}, {"derivation": "guess"}):
            with self.subTest(spec=spec):
                data = build([item, self.closer("f0", **spec)])[0]
                self.assertEqual(len(problems(data, KINDS)), 1)
                data = build([item, self.closer("f0", **spec), self.closer("f0")])[0]
                found = problems(data, KINDS)
                self.assertFalse(any("already closed" in p for p in found), found)
        # the broken closer closed by supersedes: the item is closed only by the later valid closer
        data = build([item, self.closer("f0", kind="learning"), {"supersedes": 1}])[0]
        self.assertEqual(self.ids(data), ["f0"])
        data = build([item, self.closer("f0", kind="learning"), {"supersedes": 1}, self.closer("f0")])[0]
        self.assertEqual(self.ids(data), [])

    def test_append_refuses_a_bad_closer_and_writes_a_good_one(self):
        data = build([{"kind": "seed_issue"}, {}])[0]
        for name in ("f1", "f7", "seed-040"):
            with self.subTest(name=name):
                path = self.ledger(data)
                code, out = self.add(path, "--ref", "closes:" + name)
                self.assertEqual(code, 1)
                self.assertTrue(any(r.startswith("problem:") and "closes:" + name in r for r in out["reasons"]))
                self.assertEqual(self.read(path), data)
        path = self.ledger(data)
        self.assertEqual(self.add(path, "--ref", "closes:f0")[0], 0)
        self.assertEqual(self.add(path, "--ref", "closes:f0")[0], 1)
        self.assertEqual(self.run_cli(path, "open", "--reports", self.reports())[1]["open"], [])

    def test_reports_are_open_unless_confirmed(self):
        def report(rid, state):
            return rid + ".json", {"id": rid, "kind": "spec_issue", "ref": "spec/x.md:1", "state": state}
        from unittest import mock
        d = self.reports(report("b-2", "open"), report("a-1", "answered"), report("c-3", "confirmed"),
                         ("notes.txt", "not a report"))
        git = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, git)
        with mock.patch.dict(os.environ, {"PATH": HistoryGit(git).directory}):  # a git is there; d is no work tree
            code, out = self.listed(build([{"kind": "blocked"}])[0], d)
        self.assertEqual(code, 0)
        self.assertEqual(out["open"][0]["id"], "f0")
        self.assertEqual(out["open"][1:], [
            {"id": "a-1", "source": "report", "kind": "spec_issue", "state": "answered", "ref": "spec/x.md:1",
             "ref_check": {"status": "unknown", "why": "not_in_git"}},
            {"id": "b-2", "source": "report", "kind": "spec_issue", "state": "open", "ref": "spec/x.md:1",
             "ref_check": {"status": "unknown", "why": "not_in_git"}}])
        # a ledger row does not close a report: the report's state is its one source
        self.assertEqual(problems(build([{"kind": "seed_issue"}, self.closer("b-2")])[0], KINDS)[0][-30:],
                         "names no earlier seed_issue or blocked row"[-30:])
        missing = os.path.join(d, "no-such-dir")
        self.assertEqual(self.ids(build([{}])[0], missing), [])

    def test_a_bad_report_makes_the_list_unusable(self):
        for name, body in (("x.json", "{"), ("x.json", [1]), ("x.json", {"id": "y", "state": "open"}),
                           ("x.json", {"id": "x"}), ("x.json", {"id": "x", "state": ""}),
                           ("x.json", {"id": "x", "state": 1})):
            with self.subTest(body=body):
                code, out = self.listed(build([{}])[0], self.reports((name, body)))
                self.assertEqual((code, out["ok"]), (2, False), out)
                self.assertIn("x.json", out["error"])

    def test_this_ledger_lists_every_open_item_once(self):
        import subprocess
        proc = subprocess.run([sys.executable, "-m", "ledger.founder", "open"], cwd=os.path.join(ROOT, "referee"),
                              capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        out = json.loads(proc.stdout)
        ids = [item["id"] for item in out["open"]]
        self.assertEqual(len(ids), len(set(ids)))
        with open(LEDGER, "rb") as fh:
            rows = [chain.parse_row(line.decode("utf-8")) for line in chain._lines(fh.read())]
        closed = {r[len("closes:"):] for row in rows for r in row["payload"]["refs"] if r.startswith("closes:")}
        items = [row["row_id"] for row in rows if row["kind"] in ("seed_issue", "blocked")]
        self.assertEqual([i["id"] for i in out["open"] if i["source"] == "ledger"],
                         [i for i in items if i not in closed])
        for item in out["open"]:
            if item["source"] == "report":
                with open(os.path.join(ROOT, "reports", item["id"] + ".json"), encoding="utf-8") as fh:
                    self.assertNotEqual(json.load(fh)["state"], "confirmed")


class Repos(Cli):
    """A repository built here and read by ``ref_checks`` through ``git``: ``repos`` builds it (real git in
    ``tests/capture_ref_since.py``; ``git_store.HistoryGit``, first and alone on ``PATH``, when None). Every
    check's answer is kept in ``answers``, ``filed`` as the index of the commit it names."""

    PAGE = b"one\ntwo\nthree\nfour\n"
    REAL = os.path.join(ROOT, "tests", "fixtures", "ref-since-real-git.json")
    repos = None  # the capture script's real git; HistoryGit when None

    def setUp(self):
        from unittest import mock
        if self.repos is None:
            self.repos = HistoryGit(self.tmp())
            patch = mock.patch.dict(os.environ, {"PATH": self.repos.directory})
            patch.start()
            self.addCleanup(patch.stop)
        self.commits: list[str] = []
        self.answers: list[dict] = []

    def tmp(self) -> str:
        import shutil
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        return d

    def write(self, top: str, path: str, data: bytes) -> None:
        os.makedirs(os.path.dirname(os.path.join(top, path)), exist_ok=True)
        with open(os.path.join(top, path), "wb") as fh:
            fh.write(data)

    def commit(self, top: str) -> str:
        sha = self.repos.commit(top)
        self.commits.append(sha)
        return sha

    def repo(self, ref="spec/p.md:2", page: bytes | None = None, rid: str = "r") -> tuple[str, str]:
        """A repository whose last commit files report ``rid`` (ref ``ref``) beside spec/p.md; (top, that
        commit)."""
        top = self.tmp()
        self.commits = []
        self.repos.init(top)
        self.write(top, "spec/p.md", self.PAGE if page is None else page)
        self.commit(top)
        self.report(top, ref, rid)
        return top, self.commit(top)

    def report(self, top: str, ref, rid: str = "r") -> None:
        self.write(top, "reports/%s.json" % rid,
                   json.dumps({"id": rid, "kind": "seed_issue", "ref": ref, "state": "open"}).encode())

    def check(self, top: str, rid: str = "r") -> dict:
        d = os.path.join(top, "reports")
        got = founder.ref_checks(d, founder.read_reports(d))[rid]
        self.answers.append({k: self.commits.index(v) if k == "filed" and v in self.commits else v
                             for k, v in got.items()})
        return got


class RefSince(Repos):
    """``ref_checks`` (each report item's ``ref_check`` in ``open``): whether the page lines a report's ref names
    changed since the commit that last changed the report, read through ``git`` from a repository built here.

    The referee's sandbox has no git, so ``git`` here is ``git_store.HistoryGit`` (``repos``), first on ``PATH``;
    ``tests/capture_ref_since.py`` runs these same tests on real git (a ``repos`` that runs git) and keeps every
    check's answer, with ``filed`` as the index of the commit it names, in ``tests/fixtures/ref-since-real-git.json``.
    Each test's answers here must be real git's (``tearDown``): a rule of the double that real git does not keep,
    or a test that was never run on real git, is red."""

    def tearDown(self):
        if type(self).repos is None:
            with open(self.REAL, encoding="utf-8") as fh:
                real = json.load(fh)["answers"]
            self.assertIn(self._testMethodName, real, "never run on real git: python3 tests/capture_ref_since.py")
            self.assertEqual(self.answers, real[self._testMethodName], "real git answered otherwise")

    def test_the_page_after_filing(self):
        for name, page, status, extra in (
                ("untouched", PAGE_SAME, "page_unchanged", {}),
                ("another line changed", b"one\ntwo\nthree\nFOUR\n", "line_same", {}),
                ("a line added at the end", b"one\ntwo\nthree\nfour\nfive\n", "line_same", {}),
                ("only the final newline dropped", b"one\ntwo\nthree\nfour", "line_same", {}),
                ("a line inserted above", b"zero\none\ntwo\nthree\nfour\n", "line_moved", {"lines": [3]}),
                ("the line twice elsewhere", b"two\nx\nthree\ntwo\n", "line_moved", {"lines": [1, 4]}),
                ("the line rewritten", b"one\ntwo!\nthree\nfour\n", "line_changed", {}),
                ("the line re-wrapped", b"one\ntwo three\nfour\n", "line_changed", {}),
                ("the line deleted", b"one\nthree\nfour\n", "line_changed", {})):
            with self.subTest(name=name):
                top, filed = self.repo()
                if page is not PAGE_SAME:
                    self.write(top, "spec/p.md", page)
                    if name != "another line changed":  # committed or not, the work tree is what is read
                        self.commit(top)
                self.assertEqual(self.check(top), {"status": status, "filed": filed, "bounded": False, **extra})

    def test_a_range_is_one_block(self):
        top, filed = self.repo("spec/p.md:2-3")
        self.write(top, "spec/p.md", b"two\nx\nthree\none\ntwo\nthree\n")
        self.assertEqual(self.check(top), {"status": "line_moved", "lines": [5], "filed": filed, "bounded": False})
        self.write(top, "spec/p.md", b"one\ntwo\nx\nthree\n")
        self.assertEqual(self.check(top)["status"], "line_changed")
        self.write(top, "spec/p.md", b"one\ntwo\nthree\nFOUR\n")
        self.assertEqual(self.check(top)["status"], "line_same")

    def test_filed_is_the_last_commit_that_changed_the_report(self):
        top, first = self.repo()
        self.write(top, "spec/p.md", b"one\nTWO\nthree\nfour\n")
        self.commit(top)
        self.assertEqual(self.check(top)["status"], "line_changed")
        self.write(top, "other.txt", b"x")
        later = self.commit(top)  # a commit that does not touch the report does not refile it
        self.assertEqual(self.check(top)["filed"], first)
        self.report(top, "spec/p.md:2")
        self.write(top, "reports/r.json", self.read(os.path.join(top, "reports/r.json")) + b"\n")
        refiled = self.commit(top)
        self.assertNotIn(refiled, (first, later))
        self.assertEqual(self.check(top), {"status": "page_unchanged", "filed": refiled, "bounded": False})

    def test_a_report_path_is_literal(self):
        # report r* is filed; a later commit changes only reports/rx.json, which the glob r* would match
        top, filed = self.repo(rid="r*")
        self.report(top, "spec/p.md:1", "rx")
        self.commit(top)
        self.assertEqual(self.check(top, "r*"), {"status": "page_unchanged", "filed": filed, "bounded": False})

    def test_uncommitted_reports(self):
        top, _ = self.repo()
        self.report(top, "spec/p.md:1", "s")  # never committed
        self.assertEqual(self.check(top, "s"), {"status": "uncommitted"})
        self.write(top, "reports/r.json", self.read(os.path.join(top, "reports/r.json")).replace(b"open", b"opened"))
        self.write(top, "spec/p.md", b"x\n")  # the page changed too, but the report is being rewritten
        self.assertEqual(self.check(top), {"status": "uncommitted"})

    def test_unreadable_refs(self):
        for ref in ("spec/p.md", "spec/p.md:0", "spec/p.md:3-2", "spec/p.md:1x", "spec/p.md:-1", "/etc/p.md:1",
                    "../p.md:1", "spec/../p.md:1", "", 5, None, ["spec/p.md:1"], "spec/p.md:1 "):
            with self.subTest(ref=ref):
                top, _ = self.repo(ref)
                self.assertEqual(self.check(top), {"status": "unknown", "why": "ref_unreadable"})

    def test_the_page_at_filing_and_today(self):
        top, filed = self.repo("spec/q.md:1")
        self.assertEqual(self.check(top), {"status": "unknown", "why": "page_absent_at_filing", "filed": filed,
                                           "bounded": False})
        self.write(top, "spec/q.md", b"later\n")  # added after filing: still absent at filing
        self.assertEqual(self.check(top)["why"], "page_absent_at_filing")
        for ref in ("spec/p.md:5", "spec/p.md:4-5", "spec/p.md:99"):
            with self.subTest(ref=ref):
                top, filed = self.repo(ref)
                self.assertEqual(self.check(top), {"status": "unknown", "why": "line_out_of_range", "filed": filed,
                                                   "bounded": False})
        top, filed = self.repo("spec/p.md:4")
        self.assertEqual(self.check(top)["status"], "page_unchanged")
        os.unlink(os.path.join(top, "spec/p.md"))
        self.assertEqual(self.check(top), {"status": "page_gone", "filed": filed, "bounded": False})
        os.makedirs(os.path.join(top, "spec/p.md"))  # a directory where the page was is no page
        self.assertEqual(self.check(top)["status"], "page_gone")

    def test_no_file_at_filing_is_no_page(self):
        # a directory or a symbolic link at the path when the report was filed is no page, whatever is there today
        # (git lists a directory's entries for a path ending in "/": its first entry is no answer either)
        for name, ref, link in (("a directory", "spec:1", True), ("a link to the page", "spec/l.md:1", True),
                                ("a directory named with a slash", "spec/:1", False)):
            with self.subTest(name=name):
                top = self.tmp()
                self.commits = []
                self.repos.init(top)
                self.write(top, "spec/p.md", self.PAGE)
                if link:
                    os.symlink("p.md", os.path.join(top, "spec/l.md"))
                self.report(top, ref)
                filed = self.commit(top)
                self.assertEqual(self.check(top), {"status": "unknown", "why": "page_absent_at_filing",
                                                   "filed": filed, "bounded": False})
        # the report itself: committed as a link, today a file with the bytes it pointed at, is not committed
        top, _ = self.repo()
        os.rename(os.path.join(top, "reports/r.json"), os.path.join(top, "spec/r.json"))
        os.symlink("../spec/r.json", os.path.join(top, "reports/r.json"))
        self.commit(top)
        os.unlink(os.path.join(top, "reports/r.json"))
        os.rename(os.path.join(top, "spec/r.json"), os.path.join(top, "reports/r.json"))
        self.assertEqual(self.check(top), {"status": "uncommitted"})

    def test_a_shallow_boundary_is_bounded(self):
        top, filed = self.repo()
        self.write(top, "other.txt", b"x")
        tip = self.commit(top)
        # depth 1: the report seems filed at the tip, the boundary; depth 2: at its real commit, now the boundary
        # (an earlier filing would not be seen); depth 3: at its real commit, whose parent is there
        for depth, seen, bounded in ((1, tip, True), (2, filed, True), (3, filed, False)):
            with self.subTest(depth=depth):
                clone = os.path.join(self.tmp(), "c")
                self.repos.clone(top, depth, clone)
                got = self.check(clone)
                self.assertEqual(got, {"status": "page_unchanged", "filed": seen, "bounded": bounded})

    def test_no_repository_or_no_git(self):
        from unittest import mock
        d = self.reports(("r.json", {"id": "r", "ref": "spec/p.md:1", "state": "open"}))
        self.assertEqual(founder.ref_checks(d, founder.read_reports(d)),
                         {"r": {"status": "unknown", "why": "not_in_git"}})
        self.assertEqual(founder.ref_checks(os.path.join(d, "absent"), [{"id": "r"}]),
                         {"r": {"status": "unknown", "why": "not_in_git"}})
        top, _ = self.repo()
        with mock.patch.dict(os.environ, {"PATH": self.tmp()}):
            self.assertEqual(self.check(top), {"status": "unknown", "why": "git_unavailable"})

    def test_git_runs_with_the_referee_environment_and_trusts_only_the_ancestors(self):
        from unittest import mock
        top, filed = self.repo()
        d = os.path.join(top, "reports")
        trusted = founder._trust(d)
        real = os.path.realpath(d)
        self.assertEqual(trusted[1::2], ["safe.directory=" + p for p in
                                         [real, os.path.dirname(real)] + self.ancestors(os.path.dirname(real))])
        self.assertEqual(set(trusted[0::2]), {"-c"})
        # a GIT_DIR in the caller's environment does not redirect the reading (loop.gitobj.git_env drops it)
        with mock.patch.dict(os.environ, {"GIT_DIR": os.path.join(tempfile.gettempdir(), "no-such-git")}):
            self.assertEqual(self.check(top)["filed"], filed)

    @staticmethod
    def ancestors(path: str) -> list[str]:
        out = []
        while os.path.dirname(path) != path:
            path = os.path.dirname(path)
            out.append(path)
        return out

    def test_open_lists_the_check_on_report_items_only(self):
        top, filed = self.repo()
        code, out = self.run_cli(self.ledger(build([{"kind": "seed_issue"}])[0]), "open", "--reports",
                                 os.path.join(top, "reports"))
        self.assertEqual(code, 0)
        self.assertNotIn("ref_check", out["open"][0])
        self.assertEqual(out["open"][1]["ref_check"], {"status": "page_unchanged", "filed": filed, "bounded": False})
        self.answers.append(out["open"][1]["ref_check"] | {"filed": self.commits.index(filed)})


class HistoryGitCalls(Repos):
    """What ``ref_checks`` asks git, seen by ``HistoryGit``: every call is ``git <trust> --literal-pathspecs -C
    <top> <command>`` with ``loop.gitobj.git_env``'s environment, and only the five commands it answers."""

    def test_every_call(self):
        from unittest import mock
        from loop.gitobj import git_env
        top, _ = self.repo()
        self.write(top, "spec/p.md", b"one\nTWO\n")
        with mock.patch.dict(os.environ, {"GIT_DIR": "/x", "GIT_WORK_TREE": "/y"}):
            self.check(top)
            want_env = git_env(dict(os.environ))
        calls = self.repos.calls()
        trust = founder._trust(os.path.join(top, "reports"))
        real = os.path.realpath(top)
        self.assertEqual([c["argv"][:len(trust) + 1] for c in calls], [trust + ["--literal-pathspecs"]] * len(calls))
        commands = [c["argv"][len(trust) + 1:] for c in calls]
        self.assertEqual(commands[0], ["-C", os.path.join(top, "reports"), "rev-parse", "--show-toplevel"])
        self.assertTrue(all(c[:2] == ["-C", real] for c in commands[1:]), commands)
        self.assertEqual(sorted({tuple(c[2:4]) for c in commands}),
                         [("cat-file", "blob"), ("log", "-1"), ("ls-tree", "-z"), ("rev-parse", "--git-path"),
                          ("rev-parse", "--show-toplevel")])
        for c in calls:
            env = {k: v for k, v in c["env"].items() if k in want_env or k.startswith("GIT_")}
            self.assertEqual(env, {k: v for k, v in want_env.items() if k in c["env"]})
            self.assertEqual({k for k in c["env"] if k.startswith("GIT_")}, {"GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL"})


PAGE_SAME = object()


if __name__ == "__main__":
    unittest.main()
