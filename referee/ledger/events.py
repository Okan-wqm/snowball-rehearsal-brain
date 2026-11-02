"""The loop's ``events`` rows of a cycle, and D8's ``drill`` rows, built in one place (stage 0; written by
``activate`` and D6, D7 and D8 of ``yaz``).

Rules: tohum/26 (the ledger row; ``cause`` from its closed set on a failed or reverted event: a reject, a revert),
tohum/26d (a merge is an ``events`` row of ``kind: merge``, its payload free), tohum/26f (``sentinel`` and ``revert``
payloads), ``ledger.schema`` (``events`` ``cycle_start``, ``ratchet_base``, ``decision``, ``merge``, ``revert`` and
``sentinel``: the shapes these rows must have; ``ledger.cycle`` checks them before anything is signed), asama-0/08 (a
reject's reasons).

``row(cycle, suffix, kind, payload, cause, part)``: ``row_id`` ``<cycle_id>:<suffix>``, ``ts`` and ``snapshot_id``
the cycle's, ``part`` ``events`` unless given, ``derivation`` ``tool``, ``trust`` ``verified``, no evidence refs; ``cause`` only when
given. ``ratchet_base(cycle, base_run_sha256, counts)`` (row suffix ``ratchet``) and ``revert(cycle, merge_sha,
cause)`` (suffix ``revert``, with the cause), ``sentinel(cycle, merge_sha, verdict, flaky)`` (suffix ``sentinel``, no
cause; 26f's ``{merge_sha, verdict, red: [], flaky}``). ``drill(cycle, kind, payload)``: D8's row, part ``drill`` (suffix ``drill``; the payload
``harness.revert_drill``'s). ``decided(cycle, cid, reasons, merged)``, the rows of one candidate's decision: a reject
is one ``decision`` row (``{decision: reject, candidate, reasons}``, suffix ``c:<cid>``) with ``cause(reasons)``; a
merge is two rows, the ``decision`` (``{decision: merge, candidate}``, suffix ``c:<cid>``: 29n's ``last_decision``
reads ``payload.decision``) and then the ``merge`` row (``{candidate, path, pull, head_sha, merge_sha}`` from
``merged``, ``target.land``'s answer and the path; suffix ``m:<cid>``), the row 26d's stage-open and 26f's sentinel
rule count as the merge (``ledger.serial``, ``harness.pass_row``). ``activate`` and D6 both write a decision with it.

**A reject's cause** (``cause``): the first entry of ``REJECT_CAUSES`` one of whose reasons it matches, else
``unknown``. The rules are exact, by name, so a reason of another writer that only looks alike is not taken:

- ``scope_violation``: criterion 4's ``scope_violation`` itself, or a path reason of ``gate.diffguard``
  (criterion 1), ``<r>:<path>`` with ``r`` one of ``gate.diffguard.PATH_REASONS``;
- ``test_regression``: ``tests_red`` or ``zero_tests`` (``gate.check``);
- ``lint_regression``: ``ratchet_increase`` (``gate.check``).

A reason ``kos`` gave (``kos:<reason>``, ``loop.decide``) is none of these: its candidate was not verified by the
contained run (a patch that does not apply, a limit), which no cause of tohum/26 names exactly, so it is
``unknown`` unless another reason of the same candidate matches.
"""

from __future__ import annotations

from typing import Any

from gate import diffguard

PART = "events"
MERGE_FIELDS = ("path", "pull", "head_sha", "merge_sha")  # the merge row's payload besides its candidate
REJECT_CAUSES = (
    ("scope_violation", lambda r: r == "scope_violation" or (":" in r and r.split(":", 1)[0] in diffguard.PATH_REASONS)),
    ("test_regression", lambda r: r in ("tests_red", "zero_tests")),
    ("lint_regression", lambda r: r == "ratchet_increase"),
)


def row(cycle: dict, suffix: str, kind: str, payload: dict, cause: str | None = None, part: str = PART) -> dict:
    """One ``events`` row (or ``part``'s) of the cycle ``{cycle_id, ts, snapshot_id}``; see the module docstring."""
    out = {"row_id": "%s:%s" % (cycle["cycle_id"], suffix), "ts": cycle["ts"], "part": part, "kind": kind,
           "payload": payload, "derivation": "tool", "trust": "verified", "snapshot_id": cycle["snapshot_id"],
           "evidence_refs": []}
    if cause is not None:
        out["cause"] = cause
    return out


def cause(reasons: list[str]) -> str:
    for name, test in REJECT_CAUSES:
        if any(test(r) for r in reasons):
            return name
    return "unknown"


def start(cycle: dict) -> dict:
    return row(cycle, "start", "cycle_start", {"cycle_id": cycle["cycle_id"]})


def ratchet_base(cycle: dict, base_run_sha256: str, counts: dict) -> dict:
    """The lint totals of the base the cycle judged (``activate``'s step 2; D6 in a cycle that merges): a later
    revert's lint before (``ledger.serial.lint_before``)."""
    return row(cycle, "ratchet", "ratchet_base", {"base_run_sha256": base_run_sha256, "counts": counts})


def revert(cycle: dict, merge_sha: str, cause: str) -> dict:
    """D7's revert of ``merge_sha`` with ``gate.revert``'s cause: the row that finishes its sentinel
    (``ledger.serial``)."""
    return row(cycle, "revert", "revert", {"merge_sha": merge_sha}, cause)


def sentinel(cycle: dict, merge_sha: str, verdict: str, flaky: list[str]) -> dict:
    """D7's end of a green or flaky sentinel of ``merge_sha`` (``loop.watch.read``'s verdict): the row that finishes
    its sentinel without a revert (``ledger.serial``). ``red`` is always empty: a red's end is its revert row (26f)."""
    return row(cycle, "sentinel", "sentinel", {"merge_sha": merge_sha, "verdict": verdict, "red": [], "flaky": flaky})


def drill(cycle: dict, kind: str, payload: dict) -> dict:
    """D8's ``drill`` row of the cycle (suffix ``drill``): ``commit`` or ``plant`` with ``harness.revert_drill``'s
    payload (``loop.drill``)."""
    return row(cycle, "drill", kind, payload, part="drill")


def decided(cycle: dict, cid: str, reasons: list[str], merged: Any = None) -> list[dict]:
    """The rows of one candidate's decision: a reject when ``reasons`` is not empty, else the merge ``merged``
    (``{path, pull, head_sha, merge_sha}``) as its ``decision`` and ``merge`` rows."""
    if reasons:
        return [row(cycle, "c:" + cid, "decision", {"decision": "reject", "candidate": cid, "reasons": reasons},
                    cause(reasons))]
    merge = {k: merged[k] for k in MERGE_FIELDS}
    return [row(cycle, "c:" + cid, "decision", {"decision": "merge", "candidate": cid}),
            row(cycle, "m:" + cid, "merge", dict(merge, candidate=cid))]
