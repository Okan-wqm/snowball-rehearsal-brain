"""``status.block``, the smallest one: the top block of ``status.md``, produced from the ledger at the end of a
cycle; a hand edit of it is regenerated in the next cycle and written to ``events`` (stage 0, MF16).

Rules: asama-0/14 row 16, asama-0/09 test 42 (cycle, last decision, base age, brake state and the number of
human touches, from the ledger), tohum/26a (``status.block``: reads the ledger, writes the top block of
``status.md`` on ``brain/state``, at the end of the referee's cycle), tohum/15 and tohum/01b (``status.md``'s
block is written only by ``status.block``; a hand edit is not kept), tohum/07 (base age: time and ``main``
commits since ``brain/integration`` was cut), tohum/20 and tohum/27 (human touches; ``setup/imports.jsonl`` is
their counter), tohum/29d (group ``status``). Calls 10 -> 16: the rows and the file go into the cycle's one
``brain/state`` commit through ``ledger.append``.

**What is read.** The ledger only once it is a valid chain extending ``previous`` (``ledger.chain.verify_bytes``
through ``dispatcher.llm_call.CostBook``; ``ledger.append.HardStop`` otherwise, before anything else is read);
the cycle's own rows (``rows``, not yet chained; they count as the ledger's last rows); ``setup/imports.jsonl``,
which must be a valid chain (``Unusable`` otherwise); ``facts`` ``{cycle_id, ts, snapshot_id, row_id, budgets,
main_commits_since_cut}``, exactly these keys: ``cycle_id``, ``snapshot_id`` and ``row_id`` non-empty strings,
``ts`` ``YYYY-MM-DDTHH:MM:SSZ``, ``budgets`` ``{name: micro-USD}`` (integers >= 0), ``main_commits_since_cut``
an integer >= 0 or null (the ``yaz`` job reads it from the target; null is shown as unknown).

**The view** (``view``), each value by one rule over the ledger rows followed by ``rows``:

- ``cycle``: ``{id, ts, number}``; ``number`` is 1 + the count of ``part: events, kind: status`` rows.
- ``last_decision``: the last ``part: events`` row whose ``kind`` is one of ``DECISIONS`` (``merge``, ``reject``,
  ``revert``), as ``{kind, row_id, ts, cause}`` (missing fields null), or null when there is none.
- ``base``: from the last ``part: events, kind: integration_cut`` row (``CUT``), ``{main_sha, cut_ts, age_s,
  main_commits_since_cut}``; ``main_sha`` is the row's ``payload.main_sha``, ``age_s`` the whole seconds from the
  row's ``ts`` to the cycle's ``ts`` (a ``ts`` not in the form above, or later than the cycle's, is ``Unusable``).
  Null when there is no cut row.
- ``brakes``: per budget name, in code point order, ``{budget, budget_usd_micros, spent_usd_micros, state}``;
  spent is ``CostBook.spent`` (the one rule ``llm.call``'s brake uses); ``state`` is ``brake`` when spent >=
  budget, the point from which ``llm.call`` refuses every call whatever its cap, else ``ok`` (a call whose cap is
  above the remainder is still refused by ``llm.call``).
- ``human_touches``: ``{count, last_ts}``, the number of ``setup/imports.jsonl`` rows and the last one's ``ts``.

**The block** (``render``) is fixed English text with one line per view value, from the line ``BEGIN`` to the
line ``END``. Every value from the ledger or the facts is written as JSON with every non-ASCII character and
``<``, ``>``, ``&``, `````, ``|``, ``[``, ``]``, ``@`` written as ``\\uXXXX``: a value cannot add a line (so
not an ``END`` line), HTML, a link, a mention or a code span.

**Edits** (``plan``). The region the block owns is ``status.md`` from its first byte through the last line
that is exactly ``END`` (the last, so an ``END`` line added inside the block cannot leave the old block's tail
behind); with no such line, the whole file. The rest of the file must not hold an ``END`` line. ``expected`` is ``payload.block_sha256`` of the last
``kind: status`` row; ``found`` is the sha256 of the region, null when there is no ``status.md``. The block is
edited when ``expected`` is null and the region is not empty (a ``status.md`` block this module never wrote), or
when ``expected`` is not null and ``found`` differs. Every cycle writes ``status.md`` as the new block followed
by the bytes after the region, and appends, after ``rows``: when edited, a ``part: events, kind: status_edited``
row ``{cycle_id, found_sha256, expected_sha256}`` (row id ``<row_id>:edited``); always a ``part: events,
kind: status`` row ``{cycle_id, number, block_sha256}`` (row id ``row_id``).

**The cycle** (``status_cycle``): ``plan``, then ``ledger.append.plan_cycle`` (chain, secret scan), then one
``state.commit_files`` call with the ledger (at ``state.path``) and ``status.md``. A refusal at any step
commits nothing.

Out of scope here, stated: the other lines of tohum/20's top section (hard stop or freeze reason, organs outside
the seed, regression and impact-miss rates, unseen-file share), human touches not in ``setup/imports.jsonl``
(seed epochs, ``stage-open``, hard-stop lifts), what lies below the block (``docs.render``, stage 1), who writes
the ``integration_cut`` and decision rows (MF18 and the gate; this module only reads them), and composing this
commit with ``ledger.anchor``'s root (MF17 wires the cycle: ``plan`` returns the rows and the file for that).

Command line, run from ``referee/``, one JSON line on stdout, the cause of an error on stderr::

    python -m status.block cycle LEDGER PREVIOUS IMPORTS STATUS   stdin {rows, facts}
        -> {ok, hard_stop, view, block_sha256, status_sha256, edited, found_sha256, expected_sha256, row_hashes,
            commits}
        STATUS may name a missing file (no status.md yet). exit 0 written; 1 refused (hard stop or secret);
        2 unusable input. On 1 and 2 every field but ok and hard_stop is null and commits is 0.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import re
import sys
import time
from typing import Any

from dispatcher import llm_call
from ledger import append, chain

STATUS_PATH = "status.md"
BEGIN = "<!-- status.block:begin -->"
END = "<!-- status.block:end -->"
PART = "events"
KIND = "status"
EDITED = "status_edited"
CUT = "integration_cut"
DECISIONS = ("merge", "reject", "revert")
FACTS = {"cycle_id", "snapshot_id", "row_id", "ts", "budgets", "main_commits_since_cut"}
TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
ESCAPED = {c: "\\u%04x" % ord(c) for c in "<>&`|[]@"}


class Unusable(ValueError):
    pass


# ---------------------------------------------------------------- inputs

def _text(value: Any, what: str) -> str:
    if not isinstance(value, str) or not value:
        raise Unusable("%s must be a non-empty string" % what)
    return value


def _count(value: Any, what: str) -> int:
    if type(value) is not int or not 0 <= value <= chain.MAX_SAFE_INT:
        raise Unusable("%s must be an integer >= 0" % what)
    return value


def seconds(ts: Any, what: str) -> int:
    """``YYYY-MM-DDTHH:MM:SSZ`` as seconds since the epoch; ``Unusable`` for any other form or an invalid date."""
    if not isinstance(ts, str) or not TS.match(ts):
        raise Unusable("%s must be YYYY-MM-DDTHH:MM:SSZ" % what)
    try:
        return calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))
    except ValueError:
        raise Unusable("%s is not a valid time" % what) from None


def _facts(facts: Any) -> dict:
    if not isinstance(facts, dict) or set(facts) != FACTS:
        raise Unusable("facts must be exactly {%s}" % ", ".join(sorted(FACTS)))
    for name in ("cycle_id", "snapshot_id", "row_id"):
        _text(facts[name], name)
    seconds(facts["ts"], "facts.ts")
    budgets = facts["budgets"]
    if not isinstance(budgets, dict):
        raise Unusable("budgets must be an object {name: micro-USD}")
    for name, micros in budgets.items():
        _text(name, "a budget name")
        _count(micros, "budget %r" % name)
    if facts["main_commits_since_cut"] is not None:
        _count(facts["main_commits_since_cut"], "main_commits_since_cut")
    return facts


def _rows(rows: Any) -> list[dict]:
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise Unusable("rows must be a list of JSON objects")
    return rows


def _imports(data: bytes) -> list[dict]:
    verdict = chain.verify_bytes(data)
    if not verdict["valid"]:
        raise Unusable("setup/imports.jsonl: %s (%s)" % (verdict["reason"], verdict["broken_row"]))
    return [chain.parse_row(line.decode("utf-8")) for line in chain._lines(data)]


def _is(row: dict, kinds: tuple) -> bool:
    return row.get("part") == PART and row.get("kind") in kinds


# ---------------------------------------------------------------- the view

def view(book: llm_call.CostBook, rows: list[dict], imports: list[dict], facts: dict) -> dict:
    """The five values of the block (see the module docstring); ``book`` holds the verified ledger and ``rows``."""
    every = book.ledger + rows
    number = 1 + sum(1 for row in every if _is(row, (KIND,)))
    decision = None
    for row in every:
        if _is(row, DECISIONS):
            decision = {"kind": row["kind"], "row_id": row.get("row_id"), "ts": row.get("ts"),
                        "cause": row.get("cause")}
    base = None
    cuts = [row for row in every if _is(row, (CUT,))]
    if cuts:
        cut = cuts[-1]
        payload = cut.get("payload")
        age = seconds(facts["ts"], "facts.ts") - seconds(cut.get("ts"), "the cut row's ts")
        if age < 0:
            raise Unusable("the cut row's ts is later than the cycle's")
        base = {"main_sha": payload.get("main_sha") if isinstance(payload, dict) else None, "cut_ts": cut["ts"],
                "age_s": age, "main_commits_since_cut": facts["main_commits_since_cut"]}
    brakes = []
    for name in sorted(facts["budgets"]):
        budget, spent = facts["budgets"][name], book.spent(name)
        brakes.append({"budget": name, "budget_usd_micros": budget, "spent_usd_micros": spent,
                       "state": "brake" if spent >= budget else "ok"})
    touches = {"count": len(imports), "last_ts": imports[-1].get("ts") if imports else None}
    return {"cycle": {"id": facts["cycle_id"], "ts": facts["ts"], "number": number}, "last_decision": decision,
            "base": base, "brakes": brakes, "human_touches": touches}


# ---------------------------------------------------------------- the block

def show(value: Any) -> str:
    """A value as inert JSON text: no line break, no non-ASCII, none of ``ESCAPED``'s characters."""
    text = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(", ", ": "))
    return "".join(ESCAPED.get(c, c) for c in text)


def render(v: dict) -> bytes:
    cycle, decision, base = v["cycle"], v["last_decision"], v["base"]
    lines = [BEGIN, "## Status", "",
             "Written by the referee's status.block from the ledger at the end of every cycle. A hand edit of this",
             "block is replaced in the next cycle and recorded as a status_edited event.", "",
             "- Cycle: number %d, id %s, at %s" % (cycle["number"], show(cycle["id"]), show(cycle["ts"]))]
    if decision is None:
        lines.append("- Last decision: none")
    else:
        lines.append("- Last decision: %s, row %s, at %s, cause %s" % (
            show(decision["kind"]), show(decision["row_id"]), show(decision["ts"]), show(decision["cause"])))
    if base is None:
        lines.append("- Base age: brain/integration not cut")
    else:
        behind = base["main_commits_since_cut"]
        lines.append("- Base age: %d s since brain/integration was cut from main %s at %s; main commits since: %s" % (
            base["age_s"], show(base["main_sha"]), show(base["cut_ts"]), "unknown" if behind is None else behind))
    if not v["brakes"]:
        lines.append("- Brakes: no budget")
    for brake in v["brakes"]:
        lines.append("- Brake %s: %s, spent %d of %d micro-USD" % (
            show(brake["budget"]), brake["state"], brake["spent_usd_micros"], brake["budget_usd_micros"]))
    touches = v["human_touches"]
    lines.append("- Human touches: %d, last at %s" % (touches["count"], show(touches["last_ts"])))
    lines.append(END)
    return ("\n".join(lines) + "\n").encode("ascii")


def region(status: bytes) -> tuple[bytes, bytes]:
    """``status.md`` split into the region the block owns and the rest (see the module docstring)."""
    at, owned = 0, len(status)
    for line in status.split(b"\n"):
        at += len(line) + 1
        if line == END.encode("ascii"):
            owned = min(at, len(status))
    return status[:owned], status[owned:]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def plan(ledger: bytes, previous: bytes, rows: Any, status: bytes | None, imports: bytes, facts: Any) -> dict:
    """The cycle's status: ``{view, block, status, edited, found_sha256, expected_sha256, rows}``, where ``rows``
    are the given rows followed by this module's rows, and ``status`` the new ``status.md``. Writes nothing."""
    book = llm_call.CostBook(ledger, previous)
    rows = _rows(rows)
    facts = _facts(facts)
    for row in rows:
        book.record(row)
    v = view(book, rows, _imports(imports), facts)
    block = render(v)
    owned, rest = region(status) if status is not None else (b"", b"")
    found = None if status is None else _sha(owned)
    expected = None
    for row in book.ledger + rows:
        if _is(row, (KIND,)):
            payload = row.get("payload")
            expected = payload.get("block_sha256") if isinstance(payload, dict) else None
    edited = bool(owned) if expected is None else found != expected
    common = {"part": PART, "ts": facts["ts"], "derivation": "tool", "trust": "verified",
              "snapshot_id": facts["snapshot_id"], "evidence_refs": []}
    new = []
    if edited:
        new.append(dict(common, row_id=facts["row_id"] + ":edited", kind=EDITED,
                        payload={"cycle_id": facts["cycle_id"], "found_sha256": found, "expected_sha256": expected}))
    new.append(dict(common, row_id=facts["row_id"], kind=KIND,
                    payload={"cycle_id": facts["cycle_id"], "number": v["cycle"]["number"],
                             "block_sha256": _sha(block)}))
    return {"view": v, "block": block, "status": block + rest, "edited": edited, "found_sha256": found,
            "expected_sha256": expected, "rows": rows + new}


def status_cycle(ledger: bytes, previous: bytes, rows: Any, status: bytes | None, imports: bytes, facts: Any,
                 state: Any, message: str = "ledger: one cycle, status block") -> dict:
    """``plan`` and the cycle's one ``brain/state`` commit (ledger and ``status.md``); returns ``plan``'s result
    without ``rows``, with ``row_hashes`` of the stored rows."""
    planned = plan(ledger, previous, rows, status, imports, facts)
    request = json.dumps({"rows": planned["rows"]}, sort_keys=True).encode("utf-8")
    cycle = append.plan_cycle(ledger, previous, lambda: request)
    state.commit_files({state.path: cycle.content, STATUS_PATH: planned["status"]}, message)
    out = {k: v for k, v in planned.items() if k != "rows"}
    out["row_hashes"] = cycle.row_hashes
    return out


# ---------------------------------------------------------------- command line

USAGE = "usage: python -m status.block cycle LEDGER PREVIOUS IMPORTS STATUS < {rows, facts}"
FIELDS = ("view", "block_sha256", "status_sha256", "edited", "found_sha256", "expected_sha256", "row_hashes")


def _emit(ok: bool, hard_stop: bool, out: dict | None, commits: int) -> None:
    line = {name: None for name in FIELDS}
    if out is not None:
        line.update({name: out[name] for name in FIELDS if name in out})
        line["block_sha256"], line["status_sha256"] = _sha(out["block"]), _sha(out["status"])
    line.update(ok=ok, hard_stop=hard_stop, commits=commits)
    sys.stdout.write(json.dumps(line, sort_keys=True) + "\n")


def _read(path: str, missing_ok: bool = False) -> bytes | None:
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except FileNotFoundError:
        if missing_ok:
            return None
        raise


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 5 or argv[0] != "cycle":
            raise Unusable(USAGE)
        ledger, previous, imports = (_read(path) for path in argv[1:4])
        status = _read(argv[4], missing_ok=True)
        request = chain.parse_row(sys.stdin.buffer.read().decode("utf-8"))
        if set(request) != {"rows", "facts"}:
            raise Unusable("stdin must be {rows, facts} and nothing else")
        state = append.CountingState()
        out = status_cycle(ledger, previous, request["rows"], status, imports, request["facts"], state)
        _emit(True, False, out, state.commits)
        return 0
    except append.HardStop as exc:
        sys.stderr.write("hard stop: %s\n" % exc)
        _emit(False, True, None, 0)
        return 1
    except append.SecretRow as exc:
        sys.stderr.write("run invalid: %s\n" % exc)
        _emit(False, False, None, 0)
        return 1
    except (Unusable, append.Unusable, llm_call.Unusable, chain.ChainError, UnicodeDecodeError, OSError) as exc:
        sys.stderr.write("unusable input: %s\n" % exc)
    except Exception as exc:  # noqa: BLE001 - never a traceback, never an exit without a reason
        sys.stderr.write("internal error: %s: %s\n" % (type(exc).__name__, exc))
    _emit(False, False, None, 0)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
