"""``findings.write``: the finding registry's rows, from an adapter's proposal and from the gate's decisions
(P1 MF8, test 12 of asama-0/09; called by ``yaz``'s D6, ``loop.write_cycle``, through ``cycle``).

Rules: tohum/26h MF8, tohum/26j "Bulgu yazıcısı" and "Kapalı kapının reddi", tohum/26 (the finding's fields and closed sets; both files' rows carry ``prev_hash`` and
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
   ``rule_id`` optional), with ``class_level`` K0-K8, ``derivation`` of tohum/26's set, each ``evidence_refs``
   entry ``{path, line_start, line_end}`` (``ledger.schema.evidence``), each ``required_change`` entry ``{file,
   symbol?, op}`` with ``op`` of tohum/26's list, ``confidence`` a fixed decimal string in [0, 1] with one to
   six decimals (so no value of it is a float); or one of the three places a finding names a path (its ``file``,
   an ``evidence_refs[].path``, a ``required_change[].file``) is not ``profile.derive.file_path``: relative,
   ``/``-separated, as ``posixpath.normpath`` writes it, not leaving the tree and not its root ``.`` (the rule
   reads the string alone: whether the path exists, is a regular file or a link is not looked at here); or it
   lacks ``tool`` or ``rule_id`` in K0-K2; or it names ``doc_fix`` outside K8.
6. A fingerprint the file does not hold is a new finding: one row, ``state: open``, ``finding_id`` ``f-`` and
   the fingerprint (this brain's form), ``proposed_by`` the name ``observe`` was given, ``trust: inferred``.
7. A fingerprint the file holds is a re-observation. When the finding's last row is ``fixed`` or ``verified`` it
   writes a ``reopened`` row carrying the new observation; when that is the finding's third ``reopened`` row, a
   ``blocked`` row follows it (``REOPEN_LIMIT``; the three are counted over the finding's whole life). When the
   last row is ``unresolved`` and the observation's ``snapshot_id`` is not the base its reject was decided on
   (the ``snapshot_id`` of the finding's last row in the unresolved file, given as ``unresolved``), it writes an
   ``open`` row, which is no reopening and is not counted; a finding whose last row is ``unresolved`` with no
   row in that file is ``Unusable``. In every other state (``unresolved`` on the same base, ``open``,
   ``reopened``, ``withdrawn``, ``blocked``: final in stage 1), and for a fingerprint seen earlier in the same
   proposal, it writes nothing and is named in ``reobserved``.

**The gate's decisions** (``decide``) are a list of ``{fingerprint, reasons}``, ``reasons`` a list of non-empty
strings: empty is a merge, anything else a reject (``ledger.events.decided``'s reading), decided on ``base``
(the snapshot the cycle judged).

8. A reject whose reasons are all standing ones (``ledger.events.standing``: the gate was closed, tohum/26j)
   writes nothing and leaves its finding as it is, whatever finding it names. Every other decision names a
   finding whose last row is ``open`` or ``reopened``; one that names no finding of the file
   (``finding_unknown``) or one in another state (``finding_not_open``: this brain's reading of the same rule)
   writes nothing and is named in ``refused`` (``{index, reasons}``): it is that candidate's, not the cycle's,
   and the other decisions are written. A list that is no list of ``{fingerprint, reasons}``, or that decides
   one fingerprint twice outside rule 8's rejects, is ``Unusable`` and nothing is written for any of them.
9. A merge writes the finding's last row again with ``state: fixed``. A reject writes it with ``state:
   unresolved``, and one row in the unresolved file: ``{finding_id, fingerprint, cause, reasons, snapshot_id}``,
   ``cause`` being ``ledger.events.cause(reasons)`` and ``snapshot_id`` ``base`` (tohum/26j).

**A cycle** (``cycle``), what ``yaz`` calls once per cycle: each ``(proposed_by, proposal)`` of ``proposals`` in
order through ``observe``, then ``decisions`` through ``decide`` on the cycle's base; both files are verified
against themselves as read (rule 10) also when both lists are empty. No proposal reaches ``yaz`` yet (no job
reads an organ's output as one); the decisions are ``loop.decide``'s on the cycle's run-time candidates (P1 MF12).

**The files.**

10. Every row is added through ``ledger.append.plan_cycle``: the file must be a valid chain extending
    ``previous`` byte for byte (``ledger.append.HardStop`` otherwise, also when nothing would be written), a new
    row holding a secret is ``ledger.append.SecretRow`` (nothing written), rows are chained in order.
11. ``findings_reasons`` and ``unresolved_reasons`` say what in a file does not conform: the chain, then each
    row's shape (``finding_id`` is ``f-`` and its ``fingerprint``; a finding row's ``trust`` in tohum/26's set). A float breaks the chain (``ledger.chain``).

Out of scope, stated: writing the files to ``brain/state`` and their keys in the signed root
(``loop.write_cycle``, ``ledger.cycle``, ``ledger.anchor.tips``); where a proposal and a decision's fingerprint
come from (``loop.candidates``, ``loop.decide``: the gate asks ``refusal`` of ``last`` before it chooses a
merge, tohum/26k T1, and sends one decision per finding, T2); who writes ``verified`` and ``withdrawn`` (no page names the
trigger; they are read here, never written); retrying a ``blocked`` finding; whether a ref exists in the snapshot
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
    return [] if D.file_path(value) else ["%s: not a normalised relative path of a file" % where]


def _ref(value: Any, where: str) -> list[str]:
    return S.evidence(value, where) or _path(value["path"], where + ".path")


CHANGE = S.shape({"file": _path, "op": S.one_of(*OPS)}, {"symbol": S.text})
PROPOSED = {"class_level": S.one_of(*CLASS_LEVELS), "property": S.text, "file": _path, "claim": S.text,
            "evidence_refs": S.list_of(_ref), "required_change": S.list_of(CHANGE), "severity_hint": S.text,
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


def _observed_state(earlier: dict | None, finding: dict, decided_at: dict[str, str]) -> str | None:
    """The state an observation of ``finding`` writes after its last row ``earlier``, or None (rules 6 and 7)."""
    if earlier is None:
        return "open"
    if earlier["state"] in REOPENS:
        return "reopened"
    if earlier["state"] != "unresolved":
        return None
    if earlier["fingerprint"] not in decided_at:
        raise Unusable("finding %s is unresolved with no row in the unresolved file" % earlier["finding_id"])
    return None if decided_at[earlier["fingerprint"]] == finding["snapshot_id"] else "open"


def observe(findings: bytes, previous: bytes, proposal: Any, proposed_by: str, read: Read,
            unresolved: bytes = b"") -> Observed:
    """The findings file after an adapter's proposal (rules 5-7, 10)."""
    held = _verified(findings, previous, "findings")
    decided_at = {row["fingerprint"]: row["snapshot_id"] for row in _verified(unresolved, unresolved, "unresolved")}
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
        state = None if print_ in seen else _observed_state(last.get(print_), finding, decided_at)
        if state is None:
            reobserved.append(print_)
            continue
        seen.add(print_)
        row = dict(finding, finding_id=finding_id(print_), fingerprint=print_, proposed_by=proposed_by,
                   state=state, trust="inferred")
        rows.append(row)
        if state == "reopened":
            reopened[print_] = reopened.get(print_, 0) + 1
            if reopened[print_] >= REOPEN_LIMIT:
                rows.append(dict(row, state="blocked"))
    return Observed(_appended(findings, previous, rows), rows, reobserved, refused)


# ---------------------------------------------------------------- the gate's decisions

def last(findings: bytes) -> dict[str, dict]:
    """``{fingerprint: its last row}`` of the findings file ``findings``, a valid chain
    (``ledger.append.HardStop`` otherwise)."""
    return _last(_verified(findings, findings, "findings"))


def refusal(row: dict | None) -> str | None:
    """Why the finding whose last row is ``row`` (``None``: the file holds none) takes no decision (rule 8):
    ``finding_unknown``, ``finding_not_open``, or ``None`` when it takes one."""
    if row is None:
        return "finding_unknown"
    return None if row["state"] in DECIDABLE else "finding_not_open"


@dataclass
class Decided:
    findings: bytes             # the findings file after the decisions
    unresolved: bytes           # the unresolved file after them
    rows: list[dict]            # the finding rows added
    unresolved_rows: list[dict]
    refused: list[dict]         # {index, reasons} of each decision that names no open finding


def decide(findings: bytes, previous: bytes, unresolved: bytes, unresolved_previous: bytes,
           decisions: Any, base: str) -> Decided:
    """Both files after the gate's decisions on ``base`` (rules 8-10)."""
    last = _last(_verified(findings, previous, "findings"))
    _verified(unresolved, unresolved_previous, "unresolved")
    if not isinstance(decisions, list):
        raise Unusable("the decisions are not a list")
    if not (isinstance(base, str) and base):
        raise Unusable("base is not a non-empty string")
    rows: list[dict] = []
    lost: list[dict] = []
    refused: list[dict] = []
    named: set[str] = set()
    for index, decision in enumerate(decisions):
        found = DECISION(decision, "decision %d" % index)
        if found:
            raise Unusable("; ".join(found))
        print_ = decision["fingerprint"]
        if events.standing(decision["reasons"]):
            continue
        if print_ in named:
            raise Unusable("decision %d: a fingerprint decided twice" % index)
        named.add(print_)
        row = last.get(print_)
        if refusal(row):
            refused.append({"index": index, "reasons": [refusal(row)]})
            continue
        if not decision["reasons"]:
            rows.append(_restated(row, "fixed"))
            continue
        rows.append(_restated(row, "unresolved"))
        lost.append({"finding_id": row["finding_id"], "fingerprint": print_, "cause": events.cause(decision["reasons"]),
                     "reasons": decision["reasons"], "snapshot_id": base})
    return Decided(_appended(findings, previous, rows), _appended(unresolved, unresolved_previous, lost), rows, lost,
                   refused)


# ---------------------------------------------------------------- a cycle

@dataclass
class Cycle:
    findings: bytes             # the findings file after the cycle
    unresolved: bytes           # the unresolved file after it
    observed: list[Observed]    # ``observe``'s answer per proposal, in order
    decided: Decided


def cycle(findings: bytes, unresolved: bytes, proposals: Any, decisions: Any, base: str, read: Read) -> Cycle:
    """Both files after one cycle's proposals and decisions; ``findings`` and ``unresolved`` are the files as
    ``brain/state``'s head holds them (``b""`` for an absent one), the previous versions of every step."""
    if not (isinstance(proposals, list) and all(isinstance(p, tuple) and len(p) == 2 for p in proposals)):
        raise Unusable("the proposals are not a list of (proposed_by, proposal)")
    now, observed = findings, []
    for proposed_by, proposal in proposals:
        observed.append(observe(now, findings, proposal, proposed_by, read, unresolved))
        now = observed[-1].content
    decided = decide(now, findings, unresolved, unresolved, decisions, base)
    return Cycle(decided.findings, decided.unresolved, observed, decided)
