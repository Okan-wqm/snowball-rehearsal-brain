"""``gate.allowlist``: the gate's allowlist of organ definitions and the ``accept`` rows it is built from
(P1 MF9, test 55 of tohum/26h; the rules only: nothing in the loop calls this module yet).

Rules: tohum/26h MF9 (the gate refuses the candidate of an organ whose definition hash is in no ``accept`` row;
the hash compared is the one the referee computes itself, with its one hash function, from the organ's files at
the accepted SHA, not the package's ``definition_sha256[]`` statement; the ``accept`` row is written from the
bootstrap referee's signed result), tohum/26b (the ``accept`` row, ``part: accept``: ``{organ_id,
definition_sha256, brain_sha, evidence_run_ids[]}``; the allowlist is built from these rows), tohum/26a (the
candidate package ``{finding, diff, organ_ids, definition_sha256[]}``), tohum/26e "Organ tanımının hash'i" (one
hash function in the referee: ``runner.organs.definition_sha256``), tohum/12 "İzin listesi" and tohum/01b.

**The list** (``listed``), over the ledger's rows (parsed objects, in any order):

1. An accept row is a row whose ``part`` is ``accept``. Rows of every other part are not read.
2. The list is the set of the accept rows' ``payload.definition_sha256``. The row's ``organ_id`` does not enter:
   a hash is listed whichever organ's row carries it (26h: "in no ``accept`` row").
3. An accept row whose ``kind`` is not ``accept`` or whose payload is not ``PAYLOAD`` (26b's four keys and no
   other: ``organ_id`` a non-empty string, ``definition_sha256`` 64 lowercase hex, ``brain_sha`` 40 lowercase
   hex, ``evidence_run_ids`` a list of distinct non-empty strings, possibly empty) is ``Unusable``, as are rows
   that are not a list of objects: nothing is listed from such a ledger and no candidate is judged against it,
   one that names no organ included.

**The decision** (``reasons``), over a candidate package, the organ definitions of the accepted SHA
(``{organ_id: runner.organs definition}``, what ``loop.pulled`` carries as ``organs``) and the ledger's rows.
Of the package only ``organ_ids`` is read; it must be a list of distinct non-empty strings (``Unusable``
otherwise). The reasons, in the order the package names its organs, each organ judged:

4. ``no_organ``: the package names no organ (an output of no listed organ, tohum/12).
5. ``organ_unknown:<id>``: the accepted SHA's definitions hold no organ of that id, so there are no files to
   hash.
6. ``organ_not_listed:<id>``: ``runner.organs.definition_sha256`` of that organ's definition is not in the list.
7. The package's ``definition_sha256`` is not read: present or absent, of any value, it changes no answer.
8. A named organ's definition that has no hash (``runner.organs.OrganError``) is ``Unusable``. The definitions
   of organs the package does not name are not hashed.

The candidate is allowed only when there is no reason.

**The rows** (``accept``), over the ledger's bytes, its last verified version, the cycle (``{cycle_id, ts,
snapshot_id}``, ``ledger.events.row``'s), the verified signed result (``loop.accepted.open_state``'s answer; only
``last_accepted_sha`` is read, 40 lowercase hex), the definitions of that SHA, the organ ids to enter and the
run ids to record:

9. One row per named organ, in the order named: ``part`` and ``kind`` ``accept``, ``row_id``
   ``<cycle_id>:accept:<organ_id>``, payload ``{organ_id, definition_sha256, brain_sha, evidence_run_ids}``:
   the hash computed here from the definition (rule 6's function), ``brain_sha`` the result's
   ``last_accepted_sha``, ``evidence_run_ids`` the run ids given (a list of distinct non-empty strings, possibly
   empty). The other fields are ``ledger.events.row``'s (``derivation: tool``, ``trust: verified``).
10. No row for an organ whose ``(organ_id, definition_sha256)`` an accept row of the ledger already holds: the
    same entry twice writes once.
11. Organ ids not a list of distinct non-empty strings, an id the definitions do not hold, a definition without
    a hash, a result without such a SHA, run ids of another shape: ``Unusable``, and no row is written for any
    organ.
12. The ledger must be a valid chain extending ``previous`` byte for byte (``ledger.append.HardStop``
    otherwise, also when no row would be written); rows are added through ``ledger.append.plan_cycle`` (its
    secret scan and chaining) onto ``ledger``, whose every row stays. With no row to add the ledger's bytes
    are returned as they are.

Out of scope, stated (reports/seed-087): calling ``reasons`` from the gate and ``accept`` from ``yaz``. The
package's format is asama-1 MF5 (``candidate.publish``), not built: no page gives the file a run-time package's
``organ_ids`` is read from, and the stage-0 ready candidates name no organ (they are not judged here). Which
organs a cycle enters and when is the caller's: asama-1 MF5's red test is the refusal of organs not yet entered
and MF6 their entry, and no page gives what makes ``yaz`` enter an organ at MF6 and not before; nor which run ids
are a row's evidence. Also out: the ``accept`` row type in ``ledger.schema.ROW_TYPES`` (a ledger holding an
accept row is still refused by ``ledger.schema.ledger_reasons`` until the writer is wired); taking a hash off
the list (tohum/12's DEGRADED, 12a's planted organs: no page gives a row that does); an organ's ``state``
(tohum/26b); whether ``brain_sha`` holds that organ (the caller hands the definitions of that SHA, ``loop.cek``
reads them); the package's other fields.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ledger import append, chain, events
from ledger import schema as S
from runner import organs as O

PART = KIND = "accept"
NO_ORGAN = "no_organ"
UNKNOWN = "organ_unknown"
NOT_LISTED = "organ_not_listed"

_IDS = S.list_of(S.text, unique=True)
PAYLOAD = S.shape({"organ_id": S.text, "definition_sha256": S.hex64, "brain_sha": S.hex40, "evidence_run_ids": _IDS})


class Unusable(ValueError):
    """Input the allowlist cannot be read from or written for."""


def _ids(value: Any, where: str) -> list[str]:
    found = _IDS(value, where)
    if found:
        raise Unusable("; ".join(found))
    return value


def _accept_payloads(rows: Any) -> list[dict]:
    """The payloads of the accept rows of ``rows`` (rules 1 and 3)."""
    if not (isinstance(rows, list) and all(isinstance(r, dict) for r in rows)):
        raise Unusable("the rows are not a list of objects")
    out = []
    for row in rows:
        if row.get("part") != PART:
            continue
        found = S.exactly(KIND)(row.get("kind"), "accept row.kind") or PAYLOAD(row.get("payload"), "accept row.payload")
        if found:
            raise Unusable("; ".join(found))
        out.append(row["payload"])
    return out


def listed(rows: Any) -> frozenset[str]:
    """The allowlist: the definition hashes of the ledger's accept rows (rules 1-3)."""
    return frozenset(p["definition_sha256"] for p in _accept_payloads(rows))


def _hash(definitions: Any, organ_id: str) -> str | None:
    """The referee's own hash of ``organ_id``'s definition, or ``None`` when the definitions hold no such organ."""
    if not isinstance(definitions, dict):
        raise Unusable("the definitions are not an object")
    if organ_id not in definitions:
        return None
    try:
        return O.definition_sha256(definitions[organ_id])
    except O.OrganError as exc:
        raise Unusable("organ %s: %s" % (organ_id, exc)) from None


def reasons(package: Any, definitions: Any, rows: Any) -> list[str]:
    """Why the candidate ``package`` is not allowed, or ``[]`` (rules 4-8)."""
    if not isinstance(package, dict):
        raise Unusable("the package is not an object")
    organ_ids = _ids(package.get("organ_ids"), "package.organ_ids")
    allowed = listed(rows)
    out = [] if organ_ids else [NO_ORGAN]
    for organ_id in organ_ids:
        own = _hash(definitions, organ_id)
        if own is None:
            out.append("%s:%s" % (UNKNOWN, organ_id))
        elif own not in allowed:
            out.append("%s:%s" % (NOT_LISTED, organ_id))
    return out


@dataclass
class Accepted:
    content: bytes              # the ledger after the rows
    rows: list[dict]            # the rows added, in order, as handed to the chain


def accept(ledger: bytes, previous: bytes, cycle: dict, state: Any, definitions: Any, organ_ids: Any,
           run_ids: Any) -> Accepted:
    """The ledger after the accept rows of ``organ_ids`` (rules 9-12)."""
    verdict = chain.verify_bytes(ledger, previous)
    if not verdict["valid"]:
        raise append.HardStop("ledger: %s (%s)" % (verdict["reason"], verdict["broken_row"]))
    brain_sha = state.get("last_accepted_sha") if isinstance(state, dict) else None
    if S.hex40(brain_sha, "last_accepted_sha"):
        raise Unusable("the signed result names no accepted SHA")
    runs = list(_ids(run_ids, "run_ids"))
    held = {(p["organ_id"], p["definition_sha256"]) for p in _accept_payloads(append._ledger_rows(ledger))}
    rows = []
    for organ_id in _ids(organ_ids, "organ_ids"):
        own = _hash(definitions, organ_id)
        if own is None:
            raise Unusable("organ %s: not an organ of the accepted SHA" % organ_id)
        if (organ_id, own) in held:
            continue
        payload = {"organ_id": organ_id, "definition_sha256": own, "brain_sha": brain_sha,
                   "evidence_run_ids": list(runs)}
        rows.append(events.row(cycle, "accept:%s" % organ_id, KIND, payload, part=PART))
    if not rows:
        return Accepted(ledger, [])
    return Accepted(append.plan_cycle(ledger, previous, lambda: chain.canonical({"rows": rows})).content, rows)
