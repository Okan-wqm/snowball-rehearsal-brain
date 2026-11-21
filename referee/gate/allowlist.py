"""``gate.allowlist``: the gate's allowlist of organ definitions and the ``accept`` rows it is built from
(P1 MF9, test 55 of tohum/26h, tohum/26j "İzin listesi, MF9"). ``rows`` is called by D6
(``loop.write_cycle``) and ``request`` by ``çek`` (``loop.cek``). ``reasons`` is called by test 55 only: D5
(``loop.decide``) does not ask it yet, so a ready candidate still merges by stage 0's rule in every cycle and
MF9 is not in ``done_mf``.

Rules: tohum/26h MF9 (the gate refuses the candidate of an organ whose definition hash is in no ``accept`` row;
the hash compared is the one the referee computes itself, with its one hash function, from the organ's files at
the accepted SHA, not the package's ``definition_sha256[]`` statement; the ``accept`` row is written from the
bootstrap referee's signed result), tohum/26j MF9 (the gate reads only the package's ``organ_ids``; the list is
keyed by ``(organ_id, definition_sha256)``; ``evidence_run_ids`` is the one bootstrap run of the signed result;
the entry request is ``{organ_ids}``; no row takes an entry off the list), tohum/26b (the ``accept`` row,
``part: accept``: ``{organ_id, definition_sha256, brain_sha, evidence_run_ids[]}``), tohum/26a (the candidate
package ``{finding, diff, organ_ids, definition_sha256[]}``), tohum/26e "Organ tanımının hash'i" (one hash
function in the referee: ``runner.organs.definition_sha256``), tohum/12 "İzin listesi" and tohum/01b.

**The list** (``listed``), over the ledger's rows (parsed objects, in any order):

1. An accept row is a row whose ``part`` is ``accept``. Rows of every other part are not read.
2. The list is the set of the accept rows' ``(payload.organ_id, payload.definition_sha256)`` pairs: a hash
   listed for one organ is not listed for another (26j).
3. An accept row whose ``kind`` is not ``accept`` or whose payload is not ``ledger.schema.ACCEPT`` (26b's four
   keys and no other: ``organ_id`` a non-empty string, ``definition_sha256`` 64 lowercase hex, ``brain_sha`` 40
   lowercase hex, ``evidence_run_ids`` a list of exactly one non-empty string) is ``Unusable``, as are rows
   that are not a list of objects: nothing is listed from such a ledger and no candidate is judged against it,
   one that names no organ included.

**The decision** (``reasons``), over a candidate package, the organ definitions of the accepted SHA
(``{organ_id: runner.organs definition}``, what ``loop.pulled`` carries as ``organs``) and the ledger's rows.
Of the package only ``organ_ids`` is read; it must be a list of distinct non-empty strings (``Unusable``
otherwise). The reasons, in the order the package names its organs, each organ judged:

4. ``no_organ``: the package names no organ (an output of no listed organ, tohum/12).
5. ``organ_unknown:<id>``: the accepted SHA's definitions hold no organ of that id, so there are no files to
   hash.
6. ``organ_not_listed:<id>``: the pair of that id and ``runner.organs.definition_sha256`` of that organ's
   definition is not in the list.
7. The package's ``definition_sha256`` is not read: present or absent, of any value, it changes no answer.
8. A named organ's definition that has no hash (``runner.organs.OrganError``) is ``Unusable``. The definitions
   of organs the package does not name are not hashed.

The candidate is allowed only when there is no reason.

**The entry request** (``request``), over a parsed document:

9. Exactly ``{organ_ids}``, a list of distinct non-empty strings, possibly empty; its ``organ_ids`` is
   returned. Anything else is ``Unusable``.

**The rows** (``rows``), over the cycle (``{cycle_id, ts, snapshot_id}``, ``ledger.events.row``'s), the entry
(``{brain_sha, run_id, organ_ids}``: the SHA the bootstrap referee accepted, the run id of its signed result and
the request's organ ids at that SHA; ``None`` is no entry), the definitions of that SHA and the ledger's rows:

10. One row per named organ, in the order named: ``part`` and ``kind`` ``accept``, ``row_id``
    ``<cycle_id>:accept:<organ_id>``, payload ``{organ_id, definition_sha256, brain_sha, evidence_run_ids}``:
    the hash computed here from the definition (rule 6's function), ``brain_sha`` the entry's,
    ``evidence_run_ids`` the one-element list of the entry's ``run_id``. The other fields are
    ``ledger.events.row``'s (``derivation: tool``, ``trust: verified``).
11. No row for an organ whose ``(organ_id, definition_sha256)`` is already in the list (rule 2): the same entry
    twice writes once.
12. An entry that is not ``None`` nor exactly those three keys, organ ids not a list of distinct non-empty
    strings, an id the definitions do not hold, a definition without a hash, a ledger of rule 3: ``Unusable``,
    and there is no row for any organ. ``brain_sha`` (40 lowercase hex) and ``run_id`` (a non-empty string) are
    judged only when a row would be written: an entry naming no organ, or only listed ones, writes nothing
    whatever they are.

Nothing here writes or chains: the rows enter the ledger in the cycle's one plan (``loop.write_cycle``), and a
candidate is judged against the ledger the cycle started from, so an entry opens the gate from the next cycle.

Out of scope, stated: the run-time package's reading (``candidates/<id>/package.json`` of ``koş``'s output tree,
tohum/26j: P1 MF12, ``loop/candidates.py``). Taking an entry off the list: no row does in stage 1 (26j, L1), so tohum/12's DEGRADED and 12a's planted
organs are not answered here. An organ's ``state`` (tohum/26b). Whether ``brain_sha`` holds that organ and
whether ``run_id`` is that result's run: the caller hands them (``loop.cek`` reads the definitions and the
request at the accepted SHA; ``loop.accepted`` reads the run id from the signed result). The package's other
fields.
"""

from __future__ import annotations

from typing import Any

from ledger import events
from ledger import schema as S
from runner import organs as O
import cli

PART = KIND = "accept"
NO_ORGAN = "no_organ"
UNKNOWN = "organ_unknown"
NOT_LISTED = "organ_not_listed"

_IDS = S.list_of(S.text, unique=True)
ENTRY_KEYS = {"brain_sha", "run_id", "organ_ids"}


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
        found = S.exactly(KIND)(row.get("kind"), "accept row.kind") \
            or S.ACCEPT(row.get("payload"), "accept row.payload")
        if found:
            raise Unusable("; ".join(found))
        out.append(row["payload"])
    return out


def listed(rows: Any) -> frozenset[tuple[str, str]]:
    """The allowlist: the ``(organ_id, definition_sha256)`` pairs of the ledger's accept rows (rules 1-3)."""
    return frozenset((p["organ_id"], p["definition_sha256"]) for p in _accept_payloads(rows))


def _hash(definitions: Any, organ_id: str) -> str | None:
    """The referee's own hash of ``organ_id``'s definition, or ``None`` when the definitions hold no such organ."""
    if not isinstance(definitions, dict):
        raise Unusable("the definitions are not an object")
    if organ_id not in definitions:
        return None
    try:
        return O.definition_sha256(definitions[organ_id])
    except O.OrganError as exc:
        raise Unusable("organ %s: %s" % (organ_id, cli.cause(exc))) from None


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
        elif (organ_id, own) not in allowed:
            out.append("%s:%s" % (NOT_LISTED, organ_id))
    return out


def request(doc: Any) -> list[str]:
    """The organ ids of the entry request ``doc`` (rule 9)."""
    if not (isinstance(doc, dict) and set(doc) == {"organ_ids"}):
        raise Unusable("the entry request is not {organ_ids}")
    return list(_ids(doc["organ_ids"], "request.organ_ids"))


def rows(cycle: dict, entry: Any, definitions: Any, ledger_rows: Any) -> list[dict]:
    """The accept rows of ``entry``, as handed to the chain (rules 10-12)."""
    held = listed(ledger_rows)
    if entry is None:
        return []
    if not (isinstance(entry, dict) and set(entry) == ENTRY_KEYS):
        raise Unusable("the entry is not {brain_sha, run_id, organ_ids}")
    payloads = []
    for organ_id in _ids(entry["organ_ids"], "entry.organ_ids"):
        own = _hash(definitions, organ_id)
        if own is None:
            raise Unusable("organ %s: not an organ of the accepted SHA" % organ_id)
        if (organ_id, own) not in held:
            payloads.append({"organ_id": organ_id, "definition_sha256": own, "brain_sha": entry["brain_sha"],
                             "evidence_run_ids": [entry["run_id"]]})
    found = [f for p in payloads for f in S.ACCEPT(p, "accept %s" % p["organ_id"])]
    if found:
        raise Unusable("; ".join(found))
    return [events.row(cycle, "accept:%s" % p["organ_id"], KIND, p, part=PART) for p in payloads]
