"""The founder ledger (``founder-ledger.jsonl``) against the founder row of tohum/26 and the closing rule of tohum/13
("Kurucu defterinde kapatma"), run on every push so a row that breaks them is red in the push that writes it.

Rules checked by ``problems``, each bound by a test below:
- the file is one chain (``ledger.chain.verify_bytes``, the one verifier); a broken chain is the only problem
  reported, since rows are not read from a file that is not a chain;
- every row has tohum/26's row fields (``ledger.schema.ROW_FIELDS`` and ``ROW_OPTIONAL_FIELDS``, the one source),
  plus the founder row's optional ``supersedes`` (64 lowercase hex) and no other field (a float is refused by the
  chain itself); ``payload`` is
  exactly ``{summary, refs[]}``, summary a non-empty string and refs a list of non-empty strings;
- the meaning rules tohum/13 names (``part``, ``kind``, ``supersedes``): ``part`` is ``founder``; ``kind`` is in the
  set tohum/26 lists after "**`founder` satırı:** `kind` ∈", read from the page (``spec_kinds``), not copied;
  ``supersedes`` names the ``row_hash`` of an earlier row of this file that breaks a meaning rule;
- a row that breaks a meaning rule is a problem unless a later row that breaks none and has the row shape names its
  ``row_hash`` in ``supersedes`` (the row is closed).

Not checked here: ``snapshot_id`` being the brain's SHA at that moment (one accepted row, f58, carries a short SHA;
tohum/13 does not count it among the meaning rules a row can be closed for, ledger rows f312 and f316); whether a
closed row was accepted before it was closed (tohum/13: a row a push adds broken is refused even if closed; that
needs the last accepted SHA, which the bootstrap referee holds); append-only against an earlier version (the
bootstrap referee checks it against the last accepted SHA). Run from the brain's root."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))

from ledger import chain, schema  # noqa: E402

LEDGER = os.path.join(ROOT, "founder-ledger.jsonl")
PAGE = os.path.join(ROOT, "spec", "tohum", "26-semalar.md")
FOUNDER = "founder"

PAYLOAD = schema.shape({"summary": schema.text, "refs": schema.list_of(schema.text)})
# part and kind are meaning rules (closable), so the shape takes any non-empty string there
FOUNDER_ROW = schema.shape({**schema.ROW_FIELDS, "part": schema.text, "kind": schema.text, "payload": PAYLOAD},
                           {**schema.ROW_OPTIONAL_FIELDS, "supersedes": schema.hex64})


def spec_kinds(page: str = PAGE) -> frozenset:
    """The founder kinds tohum/26 lists; exactly one such list, or AssertionError rather than a guess."""
    with open(page, encoding="utf-8") as fh:
        found = re.findall(r"\*\*`founder` satırı:\*\*\s+`kind`\s+∈\s+\{([^}]*)\}", fh.read())
    if len(found) != 1:
        raise AssertionError("26 has %d founder kind lists, expected 1" % len(found))
    kinds = re.findall(r"`([^`]+)`", found[0])
    if not kinds or len(set(kinds)) != len(kinds):
        raise AssertionError("26's founder kind list is empty or repeats a kind: %r" % found[0])
    return frozenset(kinds)


def problems(data: bytes, kinds: frozenset) -> list[str]:
    verdict = chain.verify_bytes(data)
    if not verdict["valid"]:
        return ["chain: %s (line %s)" % (verdict["reason"], verdict["line"])]
    rows = [chain.parse_row(line.decode("utf-8")) for line in chain._lines(data)]
    out: list[str] = []
    breaks: list[list[str]] = []
    earlier: dict[str, int] = {}  # row_hash -> index of an earlier row
    for i, row in enumerate(rows):
        where = "line %d (%s)" % (i + 1, row.get("row_id"))
        out += FOUNDER_ROW(row, where)
        broken = []
        if row.get("part") != FOUNDER:
            broken.append("part %r is not founder" % row.get("part"))
        if row.get("kind") not in kinds:
            broken.append("kind %r is not one of 26's founder kinds" % row.get("kind"))
        if "supersedes" in row:
            j = earlier.get(row["supersedes"])
            if j is None:
                broken.append("supersedes names no earlier row")
            elif not breaks[j]:
                broken.append("supersedes names line %d, which breaks no meaning rule" % (j + 1))
        breaks.append(broken)
        earlier[row.get("row_hash")] = i
    closed = {row["supersedes"] for row, broken in zip(rows, breaks)
              if not broken and "supersedes" in row and not FOUNDER_ROW(row, "")}
    for i, (row, broken) in enumerate(zip(rows, breaks)):
        if broken and row.get("row_hash") not in closed:
            out += ["line %d (%s): %s, not closed" % (i + 1, row.get("row_id"), b) for b in broken]
    return out


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


if __name__ == "__main__":
    unittest.main()
