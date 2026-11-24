"""``cases.store``: the dev case set's file, ``<state_root>/cases/dev.jsonl``: its rows, the prefix rule and the
one way a case is added (stage 1, P1 MF3).

Rules: tohum/26m "Dev vaka seti" (1) (one JSON-lines file, a tohum/26 ``case`` a line; ``case_id`` is the
identity: an id in the file is not written again, the same id with other content is refused and is no edit; append
only is judged by the ledger's prefix rule, the earlier lines byte for byte the same) and (4) (a case row is
written only by ``yaz``, only from ``cases.build``'s judgement), tohum/01b ("``cases/``: yalnız ekleme;
``provenance`` zorunlu"), tohum/26 (``provenance`` is one of four words; ``split``), tohum/26n (the set's hash
chain is deferred: the file is no chain, and the cycle's root does not cover it).

**A row** (``PROVENANCES``, ``SPLIT``): a line is a JSON object with no key twice and no constant
(``ledger.chain.parse_row``, the ledger's reader) whose ``case_id`` is a non-empty string no earlier line has,
whose ``provenance`` is one of tohum/26's four and whose ``split`` is ``dev`` (26m (1): another split takes its own
file). The file is empty or ends in a newline.

**The check** (``check(data, previous)``): every ``(reason, line)`` that holds, by line: ``case_invalid`` for a
line that is no row (a last line without its newline included); with ``previous``, ``not_append_only`` once, at
the first line of ``previous`` that is not, byte for byte, the same line of ``data`` (changed, moved or gone).
D1 judges ``brain/state``'s head against its parent with it (``loop.state``).

**Adding** (``add(data, cases)``): ``data`` is the file as D1 carried it (``b""`` when the head has none; a file
with any ``check`` reason is ``Broken``), ``cases`` a list of cases, each one a row but for the file's ids, else
``Unusable`` (``cases.build`` builds them; a value RFC 8785 cannot write is ``Unusable`` too). In the list's
order, each as its line, the case's RFC 8785 bytes (``ledger.chain.canonical``): a case whose id the file (or an
earlier case of the list) has on that same line is ``kept`` and not written again; one whose id is there on a line
of other bytes is ``refused`` as ``case_id_taken``, the held row staying as it is (so a row another writer
serialized otherwise is taken, not kept: only this function writes the file, 26m (4)); any other is ``added``,
its line after the last. Returns ``{content, added, kept, refused}``: the new file, which starts with ``data``'s bytes (with no
case added it is ``data``), the ids added and kept in order and ``{case_id: reason}``.

**The held** (``held(data)``): the rows of a file with no ``check`` reason, in order, else ``Broken``; read by
``loop.cek`` for the proposal (``cases.build.propose``).

Out of scope, stated: the other fields of a row (tohum/26's ``case`` shape is ``cases.build``'s to build and the
scorer's to check, ``harness.score``); a ``withdrawn`` row (tohum/01b: no page gives its form, so no row closes a
case here and a second row of an id is ``case_invalid``); a case whose base commit cannot be read (26m (3): the
scorer's, and no cycle scores the set yet); the set's hash chain (tohum/26n); who may write the file on the target
(the ruleset, tohum/01b). Nothing here reads a file, a clock or the network.
"""

from __future__ import annotations

from typing import Any

from ledger import chain

PROVENANCES = ("human_fix", "mutation", "system_tp", "system_regression")
SPLIT = "dev"
TAKEN = "case_id_taken"


class Broken(ValueError):
    """The file is not a dev case set."""


class Unusable(ValueError):
    """A value given to ``add`` is no case row."""


def _row(case: Any) -> bool:
    return isinstance(case, dict) and isinstance(case.get("case_id"), str) and case["case_id"] != "" \
        and isinstance(case.get("provenance"), str) and case["provenance"] in PROVENANCES \
        and isinstance(case.get("split"), str) and case["split"] == SPLIT


def _read(data: bytes) -> tuple[list[dict], list[int]]:
    """``(the rows, the numbers of the lines that are none)`` of a file."""
    rows: list[dict] = []
    bad: list[int] = []
    seen: set[str] = set()
    lines = data.split(b"\n")
    last = lines.pop()
    for number, line in enumerate(lines + ([last] if last else []), 1):
        try:
            row = chain.parse_row(line.decode("utf-8"))
        except (UnicodeDecodeError, chain.ChainError):
            row = None
        if number > len(lines) or not _row(row) or row["case_id"] in seen:
            bad.append(number)
        else:
            seen.add(row["case_id"])
            rows.append(row)
    return rows, bad


def check(data: bytes, previous: bytes | None = None) -> list[tuple[str, int]]:
    """Every ``(reason, line)`` of the file ``data``, against ``previous`` when given; see the module docstring."""
    found = [("case_invalid", number) for number in _read(data)[1]]
    if previous:
        old, new = previous.split(b"\n"), data.split(b"\n")
        if old[-1] == b"":
            old.pop()
            new.pop()       # an old line is the same line only with its newline
        moved = [n for n, line in enumerate(old, 1) if n > len(new) or new[n - 1] != line]
        found += [("not_append_only", moved[0])] if moved else []
    return sorted(found, key=lambda pair: pair[1])


def held(data: bytes) -> list[dict]:
    """The rows of the file ``data`` in order; ``Broken`` for a file with a ``check`` reason."""
    rows, bad = _read(data)
    if bad:
        raise Broken("cases: line %d is no case row" % bad[0])
    return rows


def add(data: bytes, cases: Any) -> dict[str, Any]:
    """``{content, added, kept, refused}`` of ``cases`` added to the file ``data``; see the module docstring."""
    have = dict(zip((row["case_id"] for row in held(data)), data.split(b"\n")))
    out: dict[str, Any] = {"content": data, "added": [], "kept": [], "refused": {}}
    for case in cases if isinstance(cases, list) else [None]:
        if not _row(case):
            raise Unusable("cases: %r is no case row" % (case,))
        cid = case["case_id"]
        try:
            line = chain.canonical(case)
        except chain.ChainError as exc:
            raise Unusable("cases: %s: %s" % (cid, exc)) from None
        if cid not in have:
            out["content"] += line + b"\n"
            have[cid] = line
            out["added"].append(cid)
        elif have[cid] == line:
            out["kept"].append(cid)
        else:
            out["refused"][cid] = TAKEN
    return out
