"""Merges are serial: which merges of a ``brain/state`` ledger have an unfinished sentinel (stage 0, D5's criterion 8).

Rules: tohum/26f (a merge's sentinel ends at the first later ``sentinel`` or ``revert`` row naming its
``merge_sha``; no merge while one is unfinished), tohum/07 (the gate merges one candidate at a time; the next one waits until the previous merge's sentinel
run has finished; on a verified red the referee reverts that merge), asama-0/08 criterion 8 (no other merge whose
sentinel is unfinished), asama-0/01 (D5 reads the cycle's state; D7, the sentinel, runs in the next cycle's ``koş``
and ``yaz``), tohum/26 (the ledger row), ``ledger.schema`` (the row types the loop writes, one table).

**Input**: the bytes of ``brain/state``'s ``ledger.jsonl`` (``pulled``'s ``state/ledger.jsonl``, which D1 verified as
a chain). **Rules** (``unfinished``):

1. The ledger must conform to ``ledger.schema`` (``ledger_reasons``: a chain, every row of a known type with its
   payload's shape); else ``Unusable`` with those reasons, and nothing is answered (fail closed: a row this reader
   cannot read could be a merge).
2. A **merge** is a row of ``MERGES``, tohum/26f's two: ``events``/``merge`` (the gate's merge, tohum/26d's merge
   row, ``activate`` and D6) and ``drill``/``plant`` (the revert drill's planted merge, which the sentinel must see
   red, tohum/22a). Its id is ``payload.merge_sha``. The same SHA merged twice is ``merged_twice:<sha>``.
3. A merge **finishes** at a row of ``FINISHERS``, read in file order, naming its ``merge_sha``: ``events``/``revert``
   (D7's revert of a red) or ``events``/``sentinel`` (D7's end of a green or flaky sentinel; both tohum/26f's). A finisher naming a SHA that no earlier row merged is
   ``finish_without_merge:<sha>`` (the ledger is append-only, so a revert before its merge is a broken state, not
   an unknown one); a second finisher of one merge is ``finished_twice:<sha>`` (a merge's sentinel ends once: a
   revert after a green end, or two ends, is a broken state).
4. ``unfinished`` is every merge without a finisher, in file order.

Reasons 2 and 3 are all collected, sorted, and raised together as ``Unusable``.

**A merge's lint before** (``lint_before``, read by ``loop.watch`` for ``gate.revert``'s ``lint``): the
``counts`` of the last ``events``/``ratchet_base`` row between the merge row's cycle start (the last
``events``/``cycle_start`` before it) and the merge row: the lint totals of the base the merge's cycle judged, which
is the merge's first parent (``activate`` and D6 write that row before their decisions; D8 writes it before its
``drill``/``plant`` row, the planted merge's base being the head the cycle's ``kos`` ran). ``None`` when the merge's
cycle has no ratchet base row (a plant ``harness.revert_drill.run_drill`` wrote outside the loop has none).
The same schema check as ``unfinished`` first; a SHA no merge row names is ``Unusable`` (``not_merged:<sha>``).

**The last published base** (``observed``, read by D6 before it writes an ``events``/``observation`` row): the
``base_run_sha256`` of the ledger's last ``events``/``observation`` row, ``None`` when it has none. The same schema
check as ``unfinished`` first.

**The commit the ledger names for ``brain/integration``** (``integration_tip``, read by D1's ``loop.integration``;
tohum/13 "Zincir kırığı", E637): the last row, in file order, of the three kinds that record a write on
``brain/integration``: ``events``/``integration_cut`` (``activate``'s cut, naming ``base_sha``), a merge of rule 2
(naming ``merge_sha``, the head after it) and ``events``/``revert`` (naming the ``merge_sha`` it reverted: tohum/26f
gives the row no field for the revert's own commit, reports/seed-078). Answer ``{row_id, kind: cut|merge|revert,
sha}``, or ``None`` for a ledger with no such row. The same schema check as ``unfinished`` first. No other rule is
applied here: whether a revert names the merge that was the tip before it is not judged (``loop.integration``
judges the head's own parents instead).

**The candidate ids a merge used** (``used_ids``, read by D5, ``loop.decide``; tohum/26p:76-80: an id is for one
merge of a target between two geneses): the ``candidate`` of every ``events``/``merge`` row after the rows' last
``events``/``genesis`` row whose id an ``events``/``decision`` row of ``decision`` ``merge`` after that genesis
names too (the page's two rows; ``ledger.events.decided`` writes them together). The last genesis is
``last_genesis``'s, the one rule of where a target's run starts (``harness.revert_drill`` and ``harness.pass_row``
read the same function), and with no genesis row the whole of the rows is read. A genesis, decision
or merge row with ``proposed_by`` is a proposal and counts for nothing (tohum/26d:25-26, as ``harness.pass_row``'s
held rows): a proposed genesis row starts no run, for any of the three readers. A reverted merge used its id as any other: the rule reads the two rows, not what followed.
It takes rows ``rows`` gave, so the schema check is its caller's.

Out of scope, stated: whether a finisher's verdict is true (D7 writes it from a sentinel ``loop.watch`` verified;
this reader reads rows); whether a merge row's SHA is on ``brain/integration`` (D1's ``loop.integration`` for the
ledger's last one, D6's for the one it writes).
"""

from __future__ import annotations

from typing import Any

from ledger import chain
from ledger import schema

MERGES = (("events", "merge"), ("drill", "plant"))
FINISHERS = (("events", "revert"), ("events", "sentinel"))
CYCLE_START = ("events", "cycle_start")
RATCHET_BASE = ("events", "ratchet_base")
OBSERVATION = ("events", "observation")
CUT = ("events", "integration_cut")
REVERT = ("events", "revert")
GENESIS = ("events", "genesis")
DECISION = ("events", "decision")
MERGE = ("events", "merge")


class Unusable(ValueError):
    def __init__(self, reasons: list[str]):
        super().__init__("; ".join(reasons))
        self.reasons = reasons


def _type(row: dict) -> tuple[Any, Any]:
    return row.get("part"), row.get("kind")


def _is_merge(row: dict) -> bool:
    return _type(row) in MERGES


def _rows(ledger: bytes) -> list[dict]:
    """The rows of ``ledger`` once it conforms to ``ledger.schema`` (rule 1), else ``Unusable``: one reading for
    ``unfinished``, ``lint_before`` and ``observed``."""
    reasons = schema.ledger_reasons(ledger)
    if reasons:
        raise Unusable(reasons)
    return [chain.parse_row(line.decode("utf-8")) for line in chain._lines(ledger)]


def rows(ledger: bytes) -> list[dict]:
    """``_rows`` for a reader of other rows of the same ledger (``gozcu.watch``, ``loop.write_cycle``)."""
    return _rows(ledger)


def last_start(ledger: bytes) -> str | None:
    """The ``ts`` of the last ``events``/``cycle_start`` row of ``ledger``, ``None`` when it has none (an empty
    ledger among them); ``Unusable`` when the ledger does not conform."""
    starts = [row["ts"] for row in _rows(ledger) if _type(row) == CYCLE_START]
    return starts[-1] if starts else None


def unfinished(ledger: bytes) -> list[str]:
    """The merge SHAs of ``ledger`` whose sentinel has not finished, in file order; see the module docstring."""
    open_: dict[str, bool] = {}  # merge sha -> still unfinished, in file order
    bad: set[str] = set()
    for row in _rows(ledger):
        sha = row["payload"].get("merge_sha")
        if _is_merge(row):
            if sha in open_:
                bad.add("merged_twice:%s" % sha)
            open_[sha] = True
        elif _type(row) in FINISHERS:
            if sha not in open_:
                bad.add("finish_without_merge:%s" % sha)
            elif not open_[sha]:
                bad.add("finished_twice:%s" % sha)
            else:
                open_[sha] = False
    if bad:
        raise Unusable(sorted(bad))
    return [sha for sha, is_open in open_.items() if is_open]


def lint_before(ledger: bytes, merge_sha: str) -> dict[str, int] | None:
    """The ratchet base counts of the cycle that merged ``merge_sha``, or ``None``; see the module docstring."""
    counts = None
    for row in _rows(ledger):
        if _type(row) == CYCLE_START:
            counts = None
        elif _type(row) == RATCHET_BASE:
            counts = row["payload"]["counts"]
        elif _is_merge(row) and row["payload"].get("merge_sha") == merge_sha:
            return counts
    raise Unusable(["not_merged:%s" % merge_sha])


def observed(ledger: bytes) -> str | None:
    """The base run hash of the last observation row of ``ledger``, or ``None``; see the module docstring."""
    last = None
    for row in _rows(ledger):
        if _type(row) == OBSERVATION:
            last = row["payload"]["base_run_sha256"]
    return last


def integration_tip(ledger: bytes) -> dict[str, str] | None:
    """The last row of ``ledger`` that records a write on ``brain/integration`` and the commit it names, or
    ``None``; see the module docstring."""
    tip = None
    for row in _rows(ledger):
        if _type(row) == CUT:
            tip = {"row_id": row["row_id"], "kind": "cut", "sha": row["payload"]["base_sha"]}
        elif _is_merge(row):
            tip = {"row_id": row["row_id"], "kind": "merge", "sha": row["payload"]["merge_sha"]}
        elif _type(row) == REVERT:
            tip = {"row_id": row["row_id"], "kind": "revert", "sha": row["payload"]["merge_sha"]}
    return tip


def last_genesis(rows: list[dict]) -> int | None:
    """The index of the last ``events``/``genesis`` row of ``rows`` without ``proposed_by`` (tohum/26d:25-26, 29: a
    proposal enters no count and a genesis row is the referee's own), None when there is none: where a target's run
    starts, for every reader of "since the last genesis" (this module's ``used_ids``, ``harness.revert_drill``,
    ``harness.pass_row``)."""
    found = [i for i, row in enumerate(rows)
             if _type(row) == GENESIS and "proposed_by" not in row and isinstance(row.get("payload"), dict)]
    return found[-1] if found else None


def used_ids(rows: list[dict]) -> set[str]:
    """The candidate ids whose merge ``rows`` (``rows``'s answer) hold since their last genesis; see the module
    docstring."""
    decided: set[str] = set()
    merged: set[str] = set()
    for row in rows[last_genesis(rows) or 0:]:
        if "proposed_by" in row:
            continue
        if _type(row) == DECISION and row["payload"]["decision"] == "merge":
            decided.add(row["payload"]["candidate"])
        elif _type(row) == MERGE:
            merged.add(row["payload"]["candidate"])
    return decided & merged
