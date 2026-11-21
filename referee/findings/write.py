"""``findings.write``: the finding registry's rows, from an adapter's proposal and from the gate's decisions
(P1 MF8, test 12 of asama-0/09; the rules only: nothing in the loop calls this module yet).

Rules: tohum/26h MF8, tohum/26 (the finding's fields and closed sets; both files' rows carry ``prev_hash`` and
``row_hash``; proposed content carries ``proposed_by`` and is stored ``trust: inferred``; no float), tohum/07
"Bulgu kimliği" and asama-1/13d (the fingerprint, the states, three reopenings), asama-1/05 (a failed fix goes
to ``unresolved.jsonl`` with its ``cause``).

**The fingerprint** (``fingerprint``), 64 lowercase hex:

1. A finding with a ``symbol``: sha256 of the RFC 8785 form of ``["symbol", property, file, symbol,
   normalize(claim)]``. Its evidence is not read.
2. A finding without one: sha256 of the RFC 8785 form of ``["line", rule_id, file, normalize(content)]``, where
   ``content`` is the text of the lines of the finding's first evidence ref whose ``path`` is ``file``, read
   through ``read`` (``read(path)`` gives the file's bytes or None). ``no_line`` when the finding has no
   ``rule_id``, no such ref, the file cannot be read, is not UTF-8, or ends before ``line_end``.
3. ``normalize`` is this brain's (no page defines it): every run of Unicode whitespace becomes one space and the
   ends are trimmed; case and punctuation stay.
4. No line number enters either form: the same line found at another place in its file is the same finding.
   So do two equal lines of one file breaking one rule (the page's form holds nothing that tells them apart).
   The "enclosing symbol" of tohum/07 is not derived (no parser here, and no proposal field names it): form 2
   always uses the file.

**A proposal** (``observe``) is a list; each element is judged alone and a refused one writes nothing:

5. ``finding_invalid``: the element is not an object of ``PROPOSED`` (tohum/26's fields without ``finding_id``,
   ``fingerprint``, ``state``, ``trust`` and ``proposed_by``, which are written here; ``symbol``, ``tool`` and
   ``rule_id`` optional), with ``class_level`` K0-K8, ``derivation`` of tohum/26's set, each ``required_change``
   entry ``{file, symbol?, op}`` with ``op`` of tohum/26's list, ``confidence`` a fixed decimal string in [0, 1]
   with one to six decimals, ``file`` a normalised relative path (so no value of it is a float); or it lacks ``tool`` or
   ``rule_id`` in K0-K2; or it names ``doc_fix`` outside K8.
6. A fingerprint the file does not hold is a new finding: one row, ``state: open``, ``finding_id`` ``f-`` and
   the fingerprint (this brain's form), ``proposed_by`` the name ``observe`` was given, ``trust: inferred``.
7. A fingerprint the file holds is a re-observation. When the finding's last row is ``fixed`` or ``verified`` it
   writes a ``reopened`` row carrying the new observation; when that is the finding's third ``reopened`` row, a
   ``blocked`` row follows it (``REOPEN_LIMIT``). In every other state, and for a fingerprint seen earlier in
   the same proposal, it writes nothing and is named in ``reobserved``.

**The gate's decisions** (``decide``) are a list of ``{fingerprint, reasons}``, ``reasons`` a list of non-empty
strings: empty is a merge, anything else a reject (``ledger.events.decided``'s reading).

8. Each names a finding whose last row is ``open`` or ``reopened``, once; otherwise ``Unusable`` and nothing is
   written for any of them.
9. A merge writes the finding's last row again with ``state: fixed``. A reject writes it with ``state:
   unresolved``, and one row in the unresolved file: ``{finding_id, fingerprint, cause, reasons, snapshot_id}``,
   ``cause`` being ``ledger.events.cause(reasons)`` and ``snapshot_id`` the finding's (this brain's shape: no
   page gives the unresolved row's).

**The files.**

10. Every row is added through ``ledger.append.plan_cycle``: the file must be a valid chain extending
    ``previous`` byte for byte (``ledger.append.HardStop`` otherwise, also when nothing would be written), a new
    row holding a secret is ``ledger.append.SecretRow`` (nothing written), rows are chained in order.
11. ``findings_reasons`` and ``unresolved_reasons`` say what in a file does not conform: the chain, then each
    row's shape (``finding_id`` is ``f-`` and its ``fingerprint``; a finding row's ``trust`` in tohum/26's set). A float breaks the chain (``ledger.chain``).

Out of scope, stated (seed-086): writing either file to ``brain/state`` and covering it by the signed root
(tohum/26 says the root covers every chain; ``ledger.anchor`` roots the ledger's parts, and these rows have no
part); who writes ``verified`` and ``withdrawn`` (no page names the trigger; they are read here, never
written); retrying a ``blocked`` or ``unresolved`` finding; whether a ref exists in the snapshot
(``harness.score.sift``); the per-class ``op`` sets of ``policy.json``; that a re-derived fingerprint equals a
stored row's (form 2 needs the tree of that row's snapshot).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Callable

from cases import build as CB
from ledger import append, chain, events
from ledger import schema as S
from profile import derive as D

STATES = ("open", "fixed", "verified", "reopened", "withdrawn", "blocked", "unresolved")
CLASS_LEVELS = tuple("K%d" % n for n in range(9))
OPS = ("lint_fix", "add_guard", "remove", "rename", "change_type", "move", "add_test", "doc_fix", "other")
REOPEN_LIMIT = 3            # tohum/07: a finding reopened three times is an oscillation
REOPENS = ("fixed", "verified")
DECIDABLE = ("open", "reopened")
CONFIDENCE = re.compile(r"(0\.\d{1,6}|1\.0{1,6})\Z")

Read = Callable[[str], "bytes | None"]


class Unusable(ValueError):
    pass


def _confidence(value: Any, where: str) -> list[str]:
    ok = isinstance(value, str) and CONFIDENCE.match(value)
    return [] if ok else ["%s: not a fixed decimal string in [0, 1]" % where]


def _path(value: Any, where: str) -> list[str]:
    return [] if D.norm_path(value) == value else ["%s: not a normalised relative path" % where]


CHANGE = S.shape({"file": S.text, "op": S.one_of(*OPS)}, {"symbol": S.text})
PROPOSED = {"class_level": S.one_of(*CLASS_LEVELS), "property": S.text, "file": _path, "claim": S.text,
            "evidence_refs": S.list_of(S.evidence), "required_change": S.list_of(CHANGE), "severity_hint": S.text,
            "confidence": _confidence, "derivation": S.one_of(*S.DERIVATIONS), "snapshot_id": S.text}
OPTIONAL = {"symbol": S.text, "tool": S.text, "rule_id": S.text}
CHAINED = {"finding_id": S.any_value, "prev_hash": S.any_value, "row_hash": S.any_value}   # judged by rule 11's two checks
WRITTEN = dict(CHAINED, fingerprint=S.hex64, state=S.one_of(*STATES), trust=S.one_of(*S.TRUSTS))
FINDING = S.shape(dict(PROPOSED, **WRITTEN), dict(OPTIONAL, proposed_by=S.text))
UNRESOLVED = S.shape(dict(CHAINED, fingerprint=S.hex64, cause=S.one_of(*S.CAUSES),
                           reasons=S.list_of(S.text, non_empty=True), snapshot_id=S.text))
DECISION = S.shape({"fingerprint": S.text, "reasons": S.list_of(S.text)})


# ---------------------------------------------------------------- the fingerprint

def normalize(text: str) -> str:
    return " ".join(text.split())


def _content(finding: dict, read: Read) -> str | None:
    """The text of the lines of the first evidence ref in the finding's own file, or None (rule 2)."""
    ref = next((r for r in finding["evidence_refs"] if r["path"] == finding["file"]), None)
    data = None if ref is None else read(finding["file"])
    if data is None:
        return None
    try:
        lines = data.decode("utf-8").split("\n")
    except UnicodeDecodeError:
        return None
    if lines[-1] == "":
        lines.pop()
    if ref["line_end"] > len(lines):
        return None
    return "\n".join(lines[ref["line_start"] - 1:ref["line_end"]])


def fingerprint(finding: dict, read: Read) -> str | None:
    """The finding's fingerprint (rules 1-4), or None when it has none (``no_line``)."""
    if "symbol" in finding:
        parts = ["symbol", finding["property"], finding["file"], finding["symbol"], normalize(finding["claim"])]
    else:
        content = _content(finding, read) if "rule_id" in finding else None
        if content is None:
            return None
        parts = ["line", finding["rule_id"], finding["file"], normalize(content)]
    return hashlib.sha256(chain.canonical(parts)).hexdigest()


def finding_id(print_: str) -> str:
    return "f-" + print_


# ---------------------------------------------------------------- the files

def _verified(data: bytes, previous: bytes, name: str) -> list[dict]:
    verdict = chain.verify_bytes(data, previous)
    if not verdict["valid"]:
        raise append.HardStop("%s: %s (%s)" % (name, verdict["reason"], verdict["broken_row"]))
    return append._ledger_rows(data)


def _appended(data: bytes, previous: bytes, rows: list[dict]) -> bytes:
    if not rows:
        return data
    return append.plan_cycle(data, previous, lambda: chain.canonical({"rows": rows})).content


def _file_reasons(data: bytes, row_shape: S.Check) -> list[str]:
    verdict = chain.verify_bytes(data)
    if not verdict["valid"]:
        return ["chain: %s (%s)" % (verdict["reason"], verdict["broken_row"])]
    out = []
    for n, row in enumerate(append._ledger_rows(data), 1):
        where = "row %d" % n
        found = row_shape(row, where)
        if not found and row["finding_id"] != finding_id(row["fingerprint"]):
            found = ["%s.finding_id: not f- and the fingerprint" % where]
        out += found
    return out


def findings_reasons(data: bytes) -> list[str]:
    """What in a findings file does not conform (rule 11); empty when it does."""
    return _file_reasons(data, lambda row, where: FINDING(row, where) or _class_reasons(row, where))


def unresolved_reasons(data: bytes) -> list[str]:
    return _file_reasons(data, UNRESOLVED)


# ---------------------------------------------------------------- a proposal

def _class_reasons(finding: dict, where: str) -> list[str]:
    out = []
    if finding["class_level"] in CB.DETERMINISTIC:
        out += ["%s.%s: missing in %s" % (where, key, finding["class_level"]) for key in ("tool", "rule_id")
                if key not in finding]
    if finding["class_level"] != "K8" and any(c["op"] == "doc_fix" for c in finding["required_change"]):
        out.append("%s.required_change: doc_fix outside K8" % where)
    return out


def proposal_reasons(finding: Any, where: str = "finding") -> list[str]:
    """Why one proposed finding is ``finding_invalid`` (rule 5); empty when it is not."""
    found = S.shape(PROPOSED, OPTIONAL)(finding, where)
    return found or _class_reasons(finding, where)


def _last(rows: list[dict]) -> dict[str, dict]:
    return {row["fingerprint"]: row for row in rows}


def _restated(row: dict, state: str) -> dict:
    out = {k: v for k, v in row.items() if k not in ("prev_hash", "row_hash")}
    out["state"] = state
    return out


@dataclass
class Observed:
    content: bytes              # the findings file after the proposal
    rows: list[dict]            # the rows added, in order, as handed to the chain
    reobserved: list[str]       # the fingerprints that wrote nothing, in proposal order
    refused: list[dict]         # {index, reasons} of each refused element


def observe(findings: bytes, previous: bytes, proposal: Any, proposed_by: str, read: Read) -> Observed:
    """The findings file after an adapter's proposal (rules 5-7, 10)."""
    held = _verified(findings, previous, "findings")
    if not isinstance(proposal, list):
        raise Unusable("the proposal is not a list")
    if not (isinstance(proposed_by, str) and proposed_by):
        raise Unusable("proposed_by is not a non-empty string")
    last = _last(held)
    reopened: dict[str, int] = {}
    for row in held:
        if row["state"] == "reopened":
            reopened[row["fingerprint"]] = reopened.get(row["fingerprint"], 0) + 1
    seen: set[str] = set()
    rows: list[dict] = []
    reobserved: list[str] = []
    refused: list[dict] = []
    for index, finding in enumerate(proposal):
        if proposal_reasons(finding):
            refused.append({"index": index, "reasons": ["finding_invalid"]})
            continue
        print_ = fingerprint(finding, read)
        if print_ is None:
            refused.append({"index": index, "reasons": ["no_line"]})
            continue
        earlier = last.get(print_)
        if print_ in seen or (earlier is not None and earlier["state"] not in REOPENS):
            reobserved.append(print_)
            continue
        seen.add(print_)
        row = dict(finding, finding_id=finding_id(print_), fingerprint=print_, proposed_by=proposed_by,
                   state="open" if earlier is None else "reopened", trust="inferred")
        rows.append(row)
        if earlier is not None:
            reopened[print_] = reopened.get(print_, 0) + 1
            if reopened[print_] >= REOPEN_LIMIT:
                rows.append(dict(row, state="blocked"))
    return Observed(_appended(findings, previous, rows), rows, reobserved, refused)


# ---------------------------------------------------------------- the gate's decisions

@dataclass
class Decided:
    findings: bytes             # the findings file after the decisions
    unresolved: bytes           # the unresolved file after them
    rows: list[dict]            # the finding rows added
    unresolved_rows: list[dict]


def decide(findings: bytes, previous: bytes, unresolved: bytes, unresolved_previous: bytes,
           decisions: Any) -> Decided:
    """Both files after the gate's decisions (rules 8-10)."""
    last = _last(_verified(findings, previous, "findings"))
    _verified(unresolved, unresolved_previous, "unresolved")
    if not isinstance(decisions, list):
        raise Unusable("the decisions are not a list")
    rows: list[dict] = []
    lost: list[dict] = []
    named: set[str] = set()
    for index, decision in enumerate(decisions):
        found = DECISION(decision, "decision %d" % index)
        if found:
            raise Unusable("; ".join(found))
        print_ = decision["fingerprint"]
        if print_ in named:
            raise Unusable("decision %d: a fingerprint decided twice" % index)
        named.add(print_)
        row = last.get(print_)
        if row is None or row["state"] not in DECIDABLE:
            raise Unusable("decision %d: no finding of that fingerprint is %s" % (index, " or ".join(DECIDABLE)))
        if not decision["reasons"]:
            rows.append(_restated(row, "fixed"))
            continue
        rows.append(_restated(row, "unresolved"))
        lost.append({"finding_id": row["finding_id"], "fingerprint": print_, "cause": events.cause(decision["reasons"]),
                     "reasons": decision["reasons"], "snapshot_id": row["snapshot_id"]})
    return Decided(_appended(findings, previous, rows), _appended(unresolved, unresolved_previous, lost), rows, lost)
