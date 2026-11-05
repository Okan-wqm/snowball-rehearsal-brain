"""``yaz``'s half of D7: the sentinel's verdict read from ``kos``'s results, and the facts ``gate.revert`` needs for a
red (stage 0).

Rules: asama-0/01 D7 (the sentinel runs in the next cycle's ``koş`` and ``yaz``; green, or a revert with its
``cause``), tohum/07 (on red, the 3/3 rule, then ``gate.revert``; a revert is written with a ``cause``), tohum/01b
(the gate reads results by artifact and hash), tohum/29j (``cause``'s request: the verified red tests, the impact
set declared at the merge, "in stage 0 the unit's service-free tests", ``build_ok``, and each tool's lint total at
the merge's first parent and at the head; the seed names no producer of ``build_ok`` and of the lint totals).

**The verdict** (``read(results, watch)``). ``watch`` is the merge whose sentinel ``kos`` ran, chosen from the state
by the rule ``kos`` uses (``loop.job._watched``: the one unfinished merge, at ``brain/integration``'s head), or
``None``. The results' ``index.json`` ``sentinel`` must agree:

- ``watch`` ``None``: the entry must be ``null`` (else ``sentinel_unexpected``); the answer is ``None``;
- else the entry must be an object naming ``watch`` (else ``sentinel_missing``). Its ``verdict`` ``null`` (``kos``
  ran no run that tells something) is ``{merge_sha, verdict: null, reasons}``: nothing to act on this cycle;
- else ``sentinel.json``'s bytes must hash to the entry's ``sha256`` (``sentinel_hash_mismatch``, a missing file
  included), be ``{merge_sha, runs, verdict, red, flaky}`` naming ``watch`` (``sentinel_unreadable``), and MF12's
  own ``gate.sentinel.decide`` on its ``runs`` must give its ``verdict``, ``red`` and ``flaky`` and the index's
  verdict (``sentinel_verdict_mismatch``; runs ``decide`` refuses are ``sentinel_unreadable``). The answer is
  ``{merge_sha, verdict, runs, red, flaky, sha256}`` (``sha256`` the verified ``sentinel.json``'s, which D7's end
  row of a green or flaky verdict carries, ``ledger.events.sentinel``).

Any reason is ``Refused`` with it; nothing is decided from a sentinel this reader did not verify.

**The base's lint** (``base_lint(results)``): ``base.jsonl`` of the results with ``index.json``'s
``base_run_sha256``, read by ``gate.check.base_counts`` (the hash, the three records one): ``{base_run_sha256,
counts}`` or ``None`` when there is no such file, its hash or records do not hold, or ``run_file`` refuses it.
It is the lint at ``brain/integration``'s head: D6 records it as the ``ratchet_base`` of a cycle that merges (the
merge's lint before) and D7 reads it as a red's lint after.

**The facts of a red** (``facts(sentinel, ledger, after)``), each rule exact and stated, since no page names them:

- ``impact``: every test id the sentinel's runs report, sorted. Stage 0's impact set is the unit's whole
  service-free test set (asama-0/08 item 6), which is what ``affected_test_cmd`` runs; so a red test is always in
  it and ``impact_miss`` is not reachable from the live path at stage 0;
- ``build_ok``: ``true``. A stage 0 recipe has no build command: the head's build is ``kos``'s staging (the inputs,
  the dependencies, the install scripts), and ``kos`` gives a sentinel verdict only when the head staged. A module
  that does not load shows as a failing test of the run (its TAP line), so it is judged ``test_regression``, not
  ``build_break``: ``build_break`` is not reachable from the live path at stage 0;
- ``lint``: per tool in either, ``{before, after}`` (a tool absent from one side counts 0, ``gate.check``'s rule):
  ``before`` the ratchet base of the merge's cycle (``ledger.serial.lint_before`` of ``brain/state``'s ledger),
  ``after`` ``base_lint``'s counts; ``None`` when either is missing (``gate.revert.assess``'s rule then).

Caller: ``loop.job``'s ``yaz`` (D7, before D6's writes); the revert itself and its row are ``loop.write_cycle``'s.
Out of scope, stated: the drill's merges (D8).
"""

from __future__ import annotations

import hashlib
import os
from typing import Any

import cli
from gate import check
from gate import sentinel as S
from ledger import serial
from runner import kos

DOC_KEYS = {"merge_sha", "runs", "verdict", "red", "flaky"}


class Refused(Exception):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__(", ".join(reasons))
        self.reasons = reasons


def _bytes(path: str) -> bytes | None:
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except (FileNotFoundError, NotADirectoryError, IsADirectoryError):
        return None


def _index(results: str) -> dict:
    raw = _bytes(os.path.join(results, kos.INDEX))
    try:
        doc = cli.loads(raw) if raw is not None else None
    except ValueError:
        doc = None
    return doc if isinstance(doc, dict) else {}


def read(results: str, watch: str | None) -> dict | None:
    """The sentinel's verdict for ``watch``; see the module docstring."""
    entry = _index(results).get("sentinel")
    if watch is None:
        if entry is not None:
            raise Refused(["sentinel_unexpected"])
        return None
    if not isinstance(entry, dict) or entry.get("merge_sha") != watch:
        raise Refused(["sentinel_missing"])
    if entry.get("verdict") is None:
        return {"merge_sha": watch, "verdict": None, "reasons": entry.get("reasons")}
    raw = _bytes(os.path.join(results, kos.SENTINEL))
    if raw is None or hashlib.sha256(raw).hexdigest() != entry.get("sha256"):
        raise Refused(["sentinel_hash_mismatch"])
    try:
        doc = cli.loads(raw)
        if not (isinstance(doc, dict) and set(doc) == DOC_KEYS and doc["merge_sha"] == watch):
            raise Refused(["sentinel_unreadable"])
        judged = S.decide(doc["runs"])
    except (ValueError, S.Unusable):
        raise Refused(["sentinel_unreadable"]) from None
    if (judged["verdict"], judged["red"], judged["flaky"]) != (doc["verdict"], doc["red"], doc["flaky"]) \
            or doc["verdict"] != entry["verdict"]:
        raise Refused(["sentinel_verdict_mismatch"])
    return {"merge_sha": watch, "verdict": doc["verdict"], "runs": doc["runs"], "red": doc["red"],
            "flaky": doc["flaky"], "sha256": entry["sha256"]}


def base_run(results: str) -> tuple[bytes, str] | None:
    """The results' base run as given: ``(base.jsonl's bytes, index.json's base_run_sha256)``, or ``None`` when
    either is missing; nothing judged (``base_lint`` and ``activate``'s ratchet base judge it)."""
    sha = _index(results).get("base_run_sha256")
    raw = _bytes(os.path.join(results, kos.BASE))
    return None if raw is None or not isinstance(sha, str) else (raw, sha)


def base_lint(results: str) -> dict | None:
    """``{base_run_sha256, counts}`` of the results' base run, or ``None``; see the module docstring."""
    given = base_run(results)
    if given is None:
        return None
    raw, sha = given
    try:
        got = check.base_counts(raw, sha)
    except check.Unusable:
        return None
    return None if got["reasons"] else {"base_run_sha256": sha, "counts": got["counts"]}


def facts(sentinel: dict, ledger: bytes, after: dict | None) -> dict[str, Any]:
    """``{impact, build_ok, lint}`` of a red ``sentinel`` (``read``'s answer); see the module docstring.
    ``ledger.serial.Unusable`` for a ledger it cannot read."""
    impact = sorted({r["id"] for run in sentinel["runs"] for r in run["results"]})
    before = serial.lint_before(ledger, sentinel["merge_sha"])
    lint = None
    if before is not None and after is not None:
        lint = {tool: {"before": before.get(tool, 0), "after": after["counts"].get(tool, 0)}
                for tool in sorted(set(before) | set(after["counts"]))}
    return {"impact": impact, "build_ok": True, "lint": lint}
