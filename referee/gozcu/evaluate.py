"""``gozcu.evaluate``: the watcher's rules of tohum/28 as one deterministic function (P1 MF7, test 41 of
asama-0/09: "every trigger of tohum/28 gives the right freeze or hard stop on a synthetic input").

``evaluate(views, policy, now)`` reads three arguments and nothing else: no file, no network, no clock (``now``
is the caller's ``YYYY-MM-DDTHH:MM:SSZ``). It answers one new object::

    {"hard_stop": [{trigger, evidence[]}], "freezes": [{trigger, scope[], measurement{}, start}],
     "lifts": [{trigger, scope[], start}], "marks": [{mark, subject[], measurement{}}], "unjudged": [path]}

No value in it is a float (tohum/26: none in a hashed artifact); the four fields of a freeze are tohum/28's
"tetik, kapsam, ölçüm, başlangıç". The same views in another row order give the same answer.

**Not wired, stated** (``status/off_live.json``): no job calls this yet. The cycle-end call in ``yaz`` (tohum/26a),
the builders of the views from ``ledger.jsonl``, the ``freeze`` row's shape in ``ledger.schema`` and the gate's
reading of it (tohum/27a) are not built; the views below are this brain's choice of input, since tohum/26a says
"defter görünümleri" and no page gives them a shape (seed-084). So what is shown is the rules on these views, not
that a cycle freezes.

**Views**: an object of exactly ``VIEWS``; anything else in it, or a value off the shapes below, is ``Unusable``
(nothing is judged on a view that cannot be read):

- ``events``: ``[{ts, kind, class}]``, ``kind`` ``merge`` or ``revert`` (a sentinel red ends at its revert row,
  tohum/26f, so a revert stands for it), ``class`` the class of the merged or reverted work;
- ``containment``: ``[{ts, file, root_cause, class}]``, one row per containment violation (tohum/08 rule 9);
- ``spend``: ``{usd_micros, ci_minutes}``, the calendar month's spend so far, counted by the caller;
- ``freezes``: ``[{trigger, scope[], start, lifted}]``, the soft freezes already written; ``trigger`` one of
  ``SOFT``, ``scope`` a non-empty sorted list of distinct names, ``lifted`` ``null`` (in force) or a time not
  before ``start``;
- ``stops``: ``{fact: [evidence]}``, ``fact`` in ``HARD_FACTS``, each evidence a non-empty string; a fact that is
  absent or has no evidence did not happen;
- ``thresholds``: ``[{name, initial, current}]``, numbers, ``initial`` not 0;
- ``similarities``: ``[{seats: [a, b], similarity}]``, two distinct seats and a number;
- ``genesis``: ``{drafts, queue}``, the drafts made in the window and the queue's depth.

A time is ``ledger.schema``'s ``ts`` and a real date; a count is an integer of 0 or more; a number is an integer
or a finite float, no boolean, compared exactly (a float read as the decimal Python writes for it).

**Thresholds** (``thresholds(policy)``): the thirteen paths of ``policy.reads.GOZCU_PATHS``, each judged by
``harness.params.count`` (an integer of 1 or more) or ``fraction`` (a JSON fraction strictly between 0 and 1);
a value off that is ``harness.params.Invalid`` naming every such path, and nothing is judged. An absent path is
``None``: the rules that need it are not judged and ``unjudged`` names the path, sorted (what a cycle does when a
rule cannot be judged is the wiring's choice, not made here). The leaf names under ``regression_freeze`` and
``genesis_drafts`` are those of ``/vec/policy/policy.json``; tohum/18a and 18b name only the two objects.

**Window**: a time ``t`` is in the last ``d`` days when ``now - d * 86400 < t <= now``; a row after ``now`` is in
no window.

**Soft freezes** (``SOFT``; tohum/28 "Yumuşak dondurma"). A rule that fires asks for a scope; the names of it not
already in the scope of a freeze in force of the same trigger become one new freeze with ``start`` ``now``, and
when none is left no freeze starts (a class a trigger has closed is not closed again by it).

1. ``regression`` (tohum/20, 18a): ``M`` merges and ``R`` reverts in the last ``window_days`` days, over all
   classes. With ``M >= min_merges`` it fires when ``R > revert_rate * M``; with fewer, when ``R >= min_reverts``.
   Scope: the classes of those reverts. Measurement ``{merges, reverts, window_days}``.
2. ``containment`` (tohum/08 rule 10): the violations of the last ``performance.windows.measure`` days, two of
   them one when they name the same ``file`` or the same ``root_cause`` (and so on along such pairs: "bir tetik,
   bir sayım"); fires when the distinct ones are ``containment_freeze`` or more. Scope: the classes of those
   violations. Measurement ``{violations, window_days}``.
3. ``budget_usd``: fires when ``spend.usd_micros >= monthly_cap_usd * 1000000`` ("tavanına ulaşmak");
   ``budget_ci_minutes``: when ``spend.ci_minutes >= monthly_cap_ci_minutes``. Scope ``["loop"]`` (tohum/28: the
   budget freeze cuts the loop). Measurement ``{spent, cap}`` in the view's unit.
4. ``lifts``: each budget freeze in force whose rule is judged and does not fire now (the month turned, so the
   caller's spend is small again, or the operator raised the cap: tohum/28 "kendiliğinden kalkar"), by trigger
   and start.

**Hard stops** (``HARD``; tohum/28 "Sert duruş"), in that order:

5. ``soft_freeze_limit``: the soft freezes whose ``start`` is in the last ``performance.windows.measure`` days,
   lifted or not, with those this call starts, are more than ``gate_rules.soft_freeze_limit``. Evidence: each
   as ``<trigger>@<start>``, sorted.
6. each fact of ``HARD_FACTS`` with evidence: setup drift, chain break, Rekor unwritten, attestation unwritten,
   activation or handover failure, a ``brain/*`` ref changed by an undeclared actor, the kill switch. The
   watcher does not find these: ``drift.check``, ``ledger.chain``, ``loop.sign`` (the three calls of tohum/13)
   and ``activate`` do, and the caller hands their findings over as evidence, which is copied.

**Marks** (``MARKS``; tohum/28 "İşaret, dondurma değil"), by mark and subject; a mark stops nothing:

7. ``threshold_drift``: ``|current - initial| > drift_bound * |initial|`` (tohum/18); subject the threshold's
   name, measurement ``{initial, current}`` as the decimals given.
8. ``seat_similarity``: ``similarity > seat_similarity`` (tohum/09a); subject the two seats sorted.
9. ``genesis_drafts``: ``drafts > genesis_drafts.per_window``; ``genesis_queue``: ``queue >
   genesis_drafts.queue`` (tohum/12, 28); subject ``["genesis"]``, measurement the count and its ``limit``.

Outside, stated: "salınım birikimi" (tohum/28's third soft trigger: no page and no policy key says how many
oscillations accumulate to a freeze, so no rule is written; seed-084); the probe cycle and its lift
(``performance.rules.probe_cycle``); HTTP 429 (an outage, no freeze, tohum/28: nothing here reads it); the
identity freeze of an agent with an unreported violation (tohum/08 rule 9); what a scope closes (the gate's and
genesis's reading); whether a view is true (that the rows are the ledger's, the spend the month's).
"""

from __future__ import annotations

import calendar
import math
import time
from fractions import Fraction
from typing import Any

from harness import params as HP
from ledger import schema as S
from policy import reads as R

DAY = 86400
SOFT = S.FREEZE_TRIGGERS    # the freeze row's triggers, one list (``ledger.schema``)
BUDGET = (("budget_usd", "usd_micros", "monthly_cap_usd", 1000000),
          ("budget_ci_minutes", "ci_minutes", "monthly_cap_ci_minutes", 1))
HARD_FACTS = ("drift", "chain_break", "rekor", "attestation", "activation", "ref_change", "kill_switch")
HARD = ("soft_freeze_limit",) + HARD_FACTS
MARKS = ("threshold_drift", "seat_similarity", "genesis_drafts", "genesis_queue")
LOOP = "loop"
GENESIS = "genesis"
EVENT_KINDS = ("merge", "revert")
VIEWS = ("events", "containment", "spend", "freezes", "stops", "thresholds", "similarities", "genesis")
THRESHOLDS = {
    "monthly_cap_usd": (HP.count, R.MONTHLY_CAP_USD),
    "monthly_cap_ci_minutes": (HP.count, R.MONTHLY_CAP_CI_MINUTES),
    "min_merges": (HP.count, R.REGRESSION_MIN_MERGES),
    "window_days": (HP.count, R.REGRESSION_WINDOW_DAYS),
    "revert_rate": (HP.fraction, R.REGRESSION_REVERT_RATE),
    "min_reverts": (HP.count, R.REGRESSION_MIN_REVERTS),
    "soft_freeze_limit": (HP.count, R.SOFT_FREEZE_LIMIT),
    "containment_freeze": (HP.count, R.CONTAINMENT_FREEZE),
    "measure_window": (HP.count, R.MEASURE_WINDOW),
    "drift_bound": (HP.fraction, R.DRIFT_BOUND),
    "seat_similarity": (HP.fraction, R.SEAT_SIMILARITY),
    "per_window": (HP.count, R.GENESIS_DRAFTS_PER_WINDOW),
    "queue": (HP.count, R.GENESIS_DRAFTS_QUEUE),
}


class Unusable(ValueError):
    """A view, or ``now``, off its shape; the message is ``<where>: <what>``."""


def thresholds(policy: Any) -> dict[str, Any]:
    """Each name of ``THRESHOLDS`` with its value, ``None`` when absent; ``harness.params.Invalid`` otherwise."""
    out: dict[str, Any] = {}
    reasons: list[str] = []
    for name, (read, path) in THRESHOLDS.items():
        try:
            out[name] = read(policy, path)
        except HP.Invalid as exc:
            reasons += exc.reasons
    if reasons:
        raise HP.Invalid(reasons)
    return out


# ---------------------------------------------------------------- the views' shapes

def _fail(where: str, what: str) -> Any:
    raise Unusable("%s: %s" % (where, what))


def _seconds(value: Any, where: str) -> int:
    if S.timestamp(value, where):
        _fail(where, "not YYYY-MM-DDTHH:MM:SSZ")
    try:
        return calendar.timegm(time.strptime(value, "%Y-%m-%dT%H:%M:%SZ"))
    except ValueError:
        return _fail(where, "not a date")


def _object(value: Any, keys: tuple[str, ...], where: str) -> dict:
    if not isinstance(value, dict) or set(value) != set(keys):
        _fail(where, "not an object of exactly %s" % ", ".join(keys))
    return value


def _rows(value: Any, where: str) -> list:
    return value if isinstance(value, list) else _fail(where, "not a list")


def _text(value: Any, where: str) -> str:
    return value if isinstance(value, str) and value else _fail(where, "not a non-empty string")


def _count(value: Any, where: str) -> int:
    return value if not S.count(value, where) else _fail(where, "not an integer >= 0")


def _number(value: Any, where: str) -> Fraction:
    if type(value) is int:
        return Fraction(value)
    if type(value) is float and math.isfinite(value):
        return Fraction(repr(value))
    return _fail(where, "not a number")


def _said(value: Any) -> str:
    return repr(value)


def _events(value: Any) -> list[dict]:
    out = []
    for i, row in enumerate(_rows(value, "events")):
        where = "events[%d]" % i
        _object(row, ("ts", "kind", "class"), where)
        if row["kind"] not in EVENT_KINDS:
            _fail(where + ".kind", "not one of %s" % "|".join(EVENT_KINDS))
        out.append({"at": _seconds(row["ts"], where + ".ts"), "kind": row["kind"],
                    "class": _text(row["class"], where + ".class")})
    return out


def _containment(value: Any) -> list[dict]:
    out = []
    for i, row in enumerate(_rows(value, "containment")):
        where = "containment[%d]" % i
        _object(row, ("ts", "file", "root_cause", "class"), where)
        out.append({"at": _seconds(row["ts"], where + ".ts"), "file": _text(row["file"], where + ".file"),
                    "root_cause": _text(row["root_cause"], where + ".root_cause"),
                    "class": _text(row["class"], where + ".class")})
    return out


def _counts(value: Any, keys: tuple[str, ...], where: str) -> dict:
    _object(value, keys, where)
    return {key: _count(value[key], "%s.%s" % (where, key)) for key in keys}


def _freezes(value: Any) -> list[dict]:
    out = []
    for i, row in enumerate(_rows(value, "freezes")):
        where = "freezes[%d]" % i
        _object(row, ("trigger", "scope", "start", "lifted"), where)
        if row["trigger"] not in SOFT:
            _fail(where + ".trigger", "not one of %s" % "|".join(SOFT))
        scope = [_text(name, "%s.scope[%d]" % (where, j))
                 for j, name in enumerate(_rows(row["scope"], where + ".scope"))]
        if not scope or scope != sorted(set(scope)):
            _fail(where + ".scope", "not a non-empty sorted list of distinct names")
        start = _seconds(row["start"], where + ".start")
        if row["lifted"] is not None and _seconds(row["lifted"], where + ".lifted") < start:
            _fail(where + ".lifted", "before start")
        out.append({"trigger": row["trigger"], "scope": scope, "start": row["start"], "at": start,
                    "in_force": row["lifted"] is None})
    return out


def _stops(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict) or not set(value) <= set(HARD_FACTS):
        _fail("stops", "not an object of %s" % ", ".join(HARD_FACTS))
    return {fact: [_text(line, "stops.%s[%d]" % (fact, i))
                   for i, line in enumerate(_rows(value[fact], "stops.%s" % fact))] for fact in value}


def _thresholds(value: Any) -> list[dict]:
    out = []
    for i, row in enumerate(_rows(value, "thresholds")):
        where = "thresholds[%d]" % i
        _object(row, ("name", "initial", "current"), where)
        initial = _number(row["initial"], where + ".initial")
        if not initial:
            _fail(where + ".initial", "0 has no relative movement")
        out.append({"name": _text(row["name"], where + ".name"), "initial": initial,
                    "current": _number(row["current"], where + ".current"),
                    "said": {"initial": _said(row["initial"]), "current": _said(row["current"])}})
    return out


def _similarities(value: Any) -> list[dict]:
    out = []
    for i, row in enumerate(_rows(value, "similarities")):
        where = "similarities[%d]" % i
        _object(row, ("seats", "similarity"), where)
        seats = [_text(seat, "%s.seats[%d]" % (where, j))
                 for j, seat in enumerate(_rows(row["seats"], where + ".seats"))]
        if len(seats) != 2 or seats[0] == seats[1]:
            _fail(where + ".seats", "not two distinct seats")
        out.append({"seats": sorted(seats), "similarity": _number(row["similarity"], where + ".similarity"),
                    "said": _said(row["similarity"])})
    return out


# ---------------------------------------------------------------- the rules

def _within(at: int, clock: int, days: int) -> bool:
    return clock - days * DAY < at <= clock


def _distinct(rows: list[dict]) -> int:
    """The violations counted once per file and per root cause, along chains of either (rule 2)."""
    group: dict[tuple[str, str], tuple[str, str]] = {}

    def top(key: tuple[str, str]) -> tuple[str, str]:
        while group.setdefault(key, key) != key:
            key = group[key]
        return key

    for row in rows:
        group[top(("file", row["file"]))] = top(("root_cause", row["root_cause"]))
    return len({top(("file", row["file"])) for row in rows})


def _regression(events: list[dict], clock: int, need: Any) -> tuple[list[str], dict] | None:
    got = need("min_merges", "window_days", "revert_rate", "min_reverts")
    if got is None:
        return None
    min_merges, days, rate, min_reverts = got
    inside = [row for row in events if _within(row["at"], clock, days)]
    reverts = [row for row in inside if row["kind"] == "revert"]
    merges = len(inside) - len(reverts)
    fires = len(reverts) > rate * merges if merges >= min_merges else len(reverts) >= min_reverts
    if not fires:
        return None
    return (sorted({row["class"] for row in reverts}),
            {"merges": merges, "reverts": len(reverts), "window_days": days})


def _contained(rows: list[dict], clock: int, need: Any) -> tuple[list[str], dict] | None:
    got = need("containment_freeze", "measure_window")
    if got is None:
        return None
    limit, days = got
    inside = [row for row in rows if _within(row["at"], clock, days)]
    distinct = _distinct(inside)
    if distinct < limit:
        return None
    return sorted({row["class"] for row in inside}), {"violations": distinct, "window_days": days}


def evaluate(views: Any, policy: Any, now: Any) -> dict[str, list]:
    """The hard stops, new soft freezes, lifts and marks of ``views`` at ``now`` (the module's rules 1-9)."""
    limits = thresholds(policy)
    clock = _seconds(now, "now")
    _object(views, VIEWS, "views")
    events, violations = _events(views["events"]), _containment(views["containment"])
    spend = _counts(views["spend"], ("usd_micros", "ci_minutes"), "spend")
    freezes, stops = _freezes(views["freezes"]), _stops(views["stops"])
    moved, similar = _thresholds(views["thresholds"]), _similarities(views["similarities"])
    genesis = _counts(views["genesis"], ("drafts", "queue"), "genesis")
    unjudged: set[str] = set()

    def need(*names: str) -> tuple | None:
        absent = [R.dotted(THRESHOLDS[name][1]) for name in names if limits[name] is None]
        unjudged.update(absent)
        return None if absent else tuple(limits[name] for name in names)

    fired: dict[str, tuple[list[str], dict]] = {}
    lifts = []
    for trigger, rule, rows in (("regression", _regression, events), ("containment", _contained, violations)):
        asked = rule(rows, clock, need)
        if asked is not None:
            fired[trigger] = asked
    for trigger, spent, cap, scale in BUDGET:
        got = need(cap)
        if got is None:
            continue
        if spend[spent] >= got[0] * scale:
            fired[trigger] = ([LOOP], {"spent": spend[spent], "cap": got[0] * scale})
        else:
            lifts += [{"trigger": trigger, "scope": row["scope"], "start": row["start"]}
                      for row in freezes if row["trigger"] == trigger and row["in_force"]]
    started = []
    for trigger in SOFT:
        if trigger not in fired:
            continue
        scope, measurement = fired[trigger]
        closed = {name for row in freezes if row["trigger"] == trigger and row["in_force"] for name in row["scope"]}
        scope = [name for name in scope if name not in closed]
        if scope:
            started.append({"trigger": trigger, "scope": scope, "measurement": measurement, "start": now})

    hard = []
    got = need("soft_freeze_limit", "measure_window")
    if got is not None:
        counted = ["%s@%s" % (row["trigger"], row["start"]) for row in freezes if _within(row["at"], clock, got[1])]
        counted += ["%s@%s" % (row["trigger"], row["start"]) for row in started]
        if len(counted) > got[0]:
            hard.append({"trigger": "soft_freeze_limit", "evidence": sorted(counted)})
    hard += [{"trigger": fact, "evidence": stops[fact]} for fact in HARD_FACTS if stops.get(fact)]

    marks = []
    got = need("drift_bound")
    if got is not None:
        marks += [{"mark": "threshold_drift", "subject": [row["name"]], "measurement": row["said"]}
                  for row in moved if abs(row["current"] - row["initial"]) > got[0] * abs(row["initial"])]
    got = need("seat_similarity")
    if got is not None:
        marks += [{"mark": "seat_similarity", "subject": row["seats"],
                   "measurement": {"similarity": row["said"]}} for row in similar if row["similarity"] > got[0]]
    for mark, key, name in (("genesis_drafts", "drafts", "per_window"), ("genesis_queue", "queue", "queue")):
        got = need(name)
        if got is not None and genesis[key] > got[0]:
            marks.append({"mark": mark, "subject": [GENESIS], "measurement": {key: genesis[key], "limit": got[0]}})
    return {
        "hard_stop": hard,
        "freezes": started,
        "lifts": sorted(lifts, key=lambda row: (SOFT.index(row["trigger"]), row["start"], row["scope"])),
        "marks": sorted(marks, key=lambda row: (MARKS.index(row["mark"]), row["subject"],
                                                sorted(row["measurement"].items()))),
        "unjudged": sorted(unjudged),
    }
