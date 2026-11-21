"""``gozcu.watch``: the watcher on one target's ledger, for ``yaz`` (P1 MF7's wiring; tohum/26a ``gozcu.evaluate``:
job ``yaz``, reads "defter görünümleri", writes the ``freeze`` row, "hakem döngü sonu"; tohum/28).

``gozcu.evaluate`` holds the rules; this module gives it its views from the rows of one ``brain/state`` ledger,
turns its answer into rows, and reads the freezes in force for the gate. No file, no network, no clock.

**Rows in**: ledger rows that conform to ``ledger.schema`` (``ledger.serial.rows``'s, or a cycle's rows from
``ledger.events``' builders), in file order. Nothing here checks that again.

**The views** (``views(rows, now)``), each ``gozcu.evaluate``'s shape:

1. ``events``: one ``merge`` per ``events``/``merge`` row and one ``revert`` per ``events``/``revert`` row, at the
   row's ``ts``, in file order. A ``drill``/``plant`` row and the revert of a merge a plant row names are not
   events: the revert drill's red is planted by the referee (tohum/22a), not a regression of the loop. ``class``
   is ``CLASS`` for every row: this loop's candidates are lint fixes, and no row names a class.
2. ``freezes``: one per ``freeze``/``freeze`` row (``trigger``, ``scope``, ``start`` of its payload), ``lifted``
   the ``ts`` of the first later ``freeze``/``lift`` row with the same three, else ``null``. A lift row naming no
   freeze in force before it is ``Unusable`` (a broken state, not an unknown one).
3. ``spend.usd_micros``: ``ledger.cost.spent_micros`` of the rows whose ``ts`` is in ``now``'s calendar month
   (the first seven characters, UTC).
4. Not measured, and said so (``UNMEASURED``, sorted, in every answer): ``spend.ci_minutes`` is 0;
   ``containment``, ``thresholds`` and ``similarities`` are empty; ``genesis`` is ``{drafts: 0, queue: 0}``;
   ``stops`` is ``{}``. No row of this ledger records a containment violation, a CI minute, a threshold's move, a
   seat similarity or a genesis draft, so the rules on them (``gozcu.evaluate``'s 2, 7, 8, 9, and the CI half of 3)
   never fire in a cycle; the facts of rule 6 are found and stopped on by their own finders (``drift.check`` in
   ``yaz``'s drift step, the chain in D1 and D6), which do not pass through here.

**Judging** (``judge(rows, planned, policy, now)``): ``gozcu.evaluate.evaluate`` of the views of ``rows`` followed
by ``planned`` (a cycle's own rows), with ``unmeasured`` added. ``gozcu.evaluate.Unusable`` and
``harness.params.Invalid`` pass through.

**Rows out** (``rows(cycle, judged)``): for each new freeze a ``freeze``/``freeze`` row, id
``<cycle_id>:freeze:<trigger>`` (one new freeze per trigger at most), payload the freeze's four fields; then for
each lift a ``freeze``/``lift`` row, id ``<cycle_id>:lift:<trigger>``, payload the lift's three. Hard stops and
marks are not rows: no page gives them a row, and nothing would read one (they are in the job's line).

**The gate's reading** (``closed(ledger)``, tohum/27a: a ``freeze`` row's reader is the gate; tohum/28: the merge
gate closes for the class, a budget freeze cuts the loop): ``frozen:<trigger>`` for each freeze in force in the
ledger's bytes whose scope has ``CLASS`` or ``gozcu.evaluate.LOOP``, sorted, each once. ``ledger.serial.Unusable``
when the ledger does not conform, ``Unusable`` for rule 2's lift.

Outside, stated: the probe cycle (a ``regression`` or ``containment`` freeze is lifted by nothing here: only a
budget freeze lifts, ``gozcu.evaluate`` rule 4); other targets' ledgers (the month's spend is this target's
alone, while tohum/18's cap is one number); genesis's ACTIVE transitions (no genesis organ runs in this loop);
whether the freeze should close ``kos`` or ``cagir`` (they run before ``yaz`` reads it); the operator's restart
after a hard stop (no row records one).
"""

from __future__ import annotations

from typing import Any

from gozcu import evaluate as GE
from ledger import cost, events, schema, serial

PART = "freeze"
FREEZE, LIFT = (PART, "freeze"), (PART, "lift")
MERGE, PLANT = serial.MERGES
CLASS = "K0"
UNMEASURED = ("containment", "genesis", "similarities", "spend.ci_minutes", "stops", "thresholds")
FROZEN = "frozen:%s"


class Unusable(ValueError):
    pass


def _type(row: dict) -> tuple[Any, Any]:
    return row.get("part"), row.get("kind")


def _key(payload: dict) -> tuple:
    return payload["trigger"], payload["scope"], payload["start"]


def _freezes(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        if _type(row) == FREEZE:
            trigger, scope, start = _key(row["payload"])
            out.append({"trigger": trigger, "scope": list(scope), "start": start, "lifted": None})
        elif _type(row) == LIFT:
            hit = [f for f in out if f["lifted"] is None
                   and (f["trigger"], f["scope"], f["start"]) == _key(row["payload"])]
            if not hit:
                raise Unusable("row %s lifts no freeze in force" % row.get("row_id"))
            hit[0]["lifted"] = row["ts"]
    return out


def views(rows: list[dict], now: str) -> dict[str, Any]:
    """``gozcu.evaluate``'s eight views of ``rows`` at ``now`` (the module's rules 1-4)."""
    if schema.timestamp(now, "now"):
        raise Unusable("now: not YYYY-MM-DDTHH:MM:SSZ")
    planted = {row["payload"]["merge_sha"] for row in rows if _type(row) == PLANT}
    seen = []
    for row in rows:
        if _type(row) == MERGE:
            seen.append({"ts": row["ts"], "kind": "merge", "class": CLASS})
        elif _type(row) == serial.REVERT and row["payload"]["merge_sha"] not in planted:
            seen.append({"ts": row["ts"], "kind": "revert", "class": CLASS})
    month = [row for row in rows if row["ts"][:7] == now[:7]]
    return {"events": seen, "containment": [], "spend": {"usd_micros": cost.spent_micros(month), "ci_minutes": 0},
            "freezes": _freezes(rows), "stops": {}, "thresholds": [], "similarities": [],
            "genesis": {"drafts": 0, "queue": 0}}


def judge(rows: list[dict], planned: list[dict], policy: Any, now: str) -> dict[str, list]:
    """``gozcu.evaluate``'s answer on ``rows`` and then ``planned``, with ``unmeasured``."""
    return dict(GE.evaluate(views(list(rows) + list(planned), now), policy, now), unmeasured=list(UNMEASURED))


def rows(cycle: dict, judged: dict) -> list[dict]:
    """The ``freeze`` and ``lift`` rows of ``judged`` in the cycle ``{cycle_id, ts, snapshot_id}``."""
    out = [events.row(cycle, "freeze:%s" % f["trigger"], FREEZE[1],
                      {k: f[k] for k in ("trigger", "scope", "measurement", "start")}, part=PART)
           for f in judged["freezes"]]
    return out + [events.row(cycle, "lift:%s" % f["trigger"], LIFT[1],
                             {k: f[k] for k in ("trigger", "scope", "start")}, part=PART)
                  for f in judged["lifts"]]


def closed(ledger: bytes) -> list[str]:
    """``frozen:<trigger>`` of every freeze in force that closes this loop's merges (the gate's reading)."""
    return sorted({FROZEN % f["trigger"] for f in _freezes(serial.rows(ledger))
                   if f["lifted"] is None and {CLASS, GE.LOOP} & set(f["scope"])})
