"""``ledger.founder``: the Founder's ledger (``founder-ledger.jsonl`` at the brain's root) against the founder row of
tohum/26 and the closing rule of tohum/13 ("Kurucu defterinde kapatma"), and the one command a session appends a
row with. A session tool (``status/off_live.json``): the loop never writes founder rows, a session does; test 14
runs the same ``problems`` on every push (``tests/test_founder_ledger.py``).

Rules checked by ``problems``:
- the file is one chain (``ledger.chain.verify_bytes``, the one verifier); a broken chain is the only problem
  reported, since rows are not read from a file that is not a chain;
- every row has tohum/26's row fields (``ledger.schema.ROW_FIELDS`` and ``ROW_OPTIONAL_FIELDS``, the one source),
  plus the founder row's optional ``supersedes`` (64 lowercase hex) and no other field (a float is refused by the
  chain itself); ``payload`` is exactly ``{summary, refs[]}``, summary a non-empty string and refs a list of
  non-empty strings;
- the meaning rules tohum/13 names (``part``, ``kind``, ``supersedes``): ``part`` is ``founder``; ``kind`` is in the
  set tohum/26 lists after "**`founder` satırı:** `kind` ∈", read from the page (``spec_kinds``), not copied;
  ``supersedes`` names the ``row_hash`` of an earlier row of this file that breaks a meaning rule;
- a row that breaks a meaning rule is a problem unless a later row that breaks none and has the row shape names its
  ``row_hash`` in ``supersedes`` (the row is closed).

Not checked: ``snapshot_id`` being the brain's SHA at that moment (one accepted row, f58, carries a short SHA;
tohum/13 does not count it among the meaning rules a row can be closed for); whether a closed row was accepted
before it was closed (tohum/13: a row a push adds broken is refused even if closed; that needs the last accepted
SHA, which the bootstrap referee holds); append-only against an earlier version (the bootstrap referee checks it
against the last accepted SHA; ``append`` itself only ever adds a line).

**Append** (``append``): builds one row (``row_id`` ``f<n+1>`` after a last row ``f<n>``, ``f1`` on an empty file;
``prev_hash`` the last row's ``row_hash``, or the zero hash; ``row_hash`` by ``ledger.chain.row_hash``), and writes
the file with that line added only if both hold:
- the line is clean under ``gate.secrets.scan(line, "row")``, MF2's row scan (refusal ``row_scan:<rule>`` with its
  sha256, never the value);
- ``problems`` of the new file holds no problem that ``problems`` of the old file did not (refusal
  ``problem:<text>``). So a row that closes an open row is written and the closed row's problem goes; a row that
  breaks a rule is not written, and neither is any row while the file is not a chain (``ledger_unusable``).
The new file is written whole to a temporary file beside it and renamed over it. Not guarded: a second writer
between the read and the rename (a session is one writer).

Command line, run from ``referee/`` (stdout one JSON line; exit 0 ok, 1 problem or refusal, 2 unusable input):

    python -m ledger.founder check [--ledger FILE] [--page FILE]
    python -m ledger.founder append --kind KIND --summary TEXT|- --snapshot SHA [--ref PATH ...]
        [--derivation D] [--trust T] [--supersedes HASH] [--ts TS] [--ledger FILE] [--page FILE]

``--summary -`` reads the summary from stdin (UTF-8, one trailing newline dropped). Defaults: derivation
``llm_inference``, trust ``inferred``, ts the current UTC second, ledger and page the brain's.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import tempfile

from gate import secrets
from ledger import chain, schema

BRAIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LEDGER = os.path.join(BRAIN, "founder-ledger.jsonl")
PAGE = os.path.join(BRAIN, "spec", "tohum", "26-semalar.md")
FOUNDER = "founder"
ROW_ID = re.compile(r"f(\d+)\Z")

PAYLOAD = schema.shape({"summary": schema.text, "refs": schema.list_of(schema.text)})
# part and kind are meaning rules (closable), so the shape takes any non-empty string there
FOUNDER_ROW = schema.shape({**schema.ROW_FIELDS, "part": schema.text, "kind": schema.text, "payload": PAYLOAD},
                           {**schema.ROW_OPTIONAL_FIELDS, "supersedes": schema.hex64})


class Unusable(Exception):
    """The ledger, the page or the arguments cannot be used; nothing is written."""


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


def next_row(data: bytes, kind: str, summary: str, refs: list[str], snapshot: str, ts: str,
             derivation: str = "llm_inference", trust: str = "inferred", supersedes: str | None = None) -> dict:
    """The row that follows the last row of ``data`` (a chain), hashed; its fields are not checked here."""
    lines = chain._lines(data)
    if lines:
        last = chain.parse_row(lines[-1].decode("utf-8"))
        m = ROW_ID.match(str(last.get("row_id")))
        if not m:
            raise Unusable("last row_id %r is not f<n>" % last.get("row_id"))
        row_id, prev = "f%d" % (int(m.group(1)) + 1), last.get("row_hash")
    else:
        row_id, prev = "f1", chain.ZERO_HASH
    row = {"row_id": row_id, "ts": ts, "part": FOUNDER, "kind": kind, "payload": {"summary": summary, "refs": refs},
           "derivation": derivation, "trust": trust, "snapshot_id": snapshot, "evidence_refs": [], "prev_hash": prev}
    if supersedes is not None:
        row["supersedes"] = supersedes
    row["row_hash"] = chain.row_hash(row)
    return row


def line_of(row: dict) -> bytes:
    return (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def refusals(old: bytes, line: bytes, kinds: frozenset) -> list[str]:
    """Why ``line`` may not be added to ``old``: MF2's row scan, then any problem the new file has and ``old`` had
    not. Unusable when ``old`` is not a chain."""
    before = problems(old, kinds)
    if before and before[0].startswith("chain: "):
        raise Unusable("ledger_unusable: %s" % before[0])
    found = ["row_scan:%s:%s" % (m["rule"], m["sha256"]) for m in secrets.scan(line.decode("utf-8"), "row")]
    seen = set(before)
    return found + ["problem:%s" % p for p in problems(old + line, kinds) if p not in seen]


def append(path: str, row: dict, kinds: frozenset) -> list[str]:
    """Add ``row`` to the ledger at ``path`` unless ``refusals`` names a reason; return the reasons."""
    with open(path, "rb") as fh:
        old = fh.read()
    line = line_of(row)
    reasons = refusals(old, line, kinds)
    if reasons:
        return reasons
    fd, tmp = tempfile.mkstemp(prefix=".founder-", dir=os.path.dirname(os.path.abspath(path)))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(old + line)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return []


# ---------------------------------------------------------------- command line

class _Parser(argparse.ArgumentParser):
    def error(self, message: str):
        raise Unusable("usage: %s" % message)


def _parser() -> argparse.ArgumentParser:
    p = _Parser(prog="python -m ledger.founder", add_help=False)
    sub = p.add_subparsers(dest="command", required=True, parser_class=_Parser)
    for name in ("check", "append"):
        s = sub.add_parser(name, add_help=False)
        s.add_argument("--ledger", default=LEDGER)
        s.add_argument("--page", default=PAGE)
    a = sub.choices["append"]
    a.add_argument("--kind", required=True)
    a.add_argument("--summary", required=True)
    a.add_argument("--snapshot", required=True)
    a.add_argument("--ref", action="append", default=[])
    a.add_argument("--derivation", default="llm_inference")
    a.add_argument("--trust", default="inferred")
    a.add_argument("--supersedes")
    a.add_argument("--ts")
    return p


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv: list[str], stdin=None) -> int:
    try:
        args = _parser().parse_args(argv)
        try:
            kinds = spec_kinds(args.page)
            with open(args.ledger, "rb") as fh:
                data = fh.read()
        except (OSError, AssertionError, UnicodeDecodeError) as exc:
            raise Unusable(str(exc)) from None
        if args.command == "check":
            found = problems(data, kinds)
            _emit({"ok": not found, "problems": found})
            return 1 if found else 0
        summary = args.summary
        if summary == "-":
            try:
                summary = (stdin if stdin is not None else sys.stdin.buffer).read().decode("utf-8")
            except UnicodeDecodeError:
                raise Unusable("summary on stdin is not UTF-8") from None
            summary = summary[:-1] if summary.endswith("\n") else summary
        ts = args.ts or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            row = next_row(data, args.kind, summary, args.ref, args.snapshot, ts, args.derivation, args.trust,
                           args.supersedes)
        except (chain.ChainError, UnicodeDecodeError) as exc:
            raise Unusable("ledger_unusable: %s" % exc) from None
        reasons = append(args.ledger, row, kinds)
    except Unusable as exc:
        _emit({"ok": False, "error": str(exc)})
        return 2
    if reasons:
        _emit({"ok": False, "reasons": reasons})
        return 1
    _emit({"ok": True, "row_id": row["row_id"], "row_hash": row["row_hash"]})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
