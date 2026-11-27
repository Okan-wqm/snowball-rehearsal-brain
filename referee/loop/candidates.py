"""The run-time candidates of a cycle, read by ``yaz`` for the gate and the finding writer (P1 MF12; tohum/26j
"Aday yolu": "``yaz`` ``candidates/<id>/``'yi sonuçlardan hash'iyle okur. ``organ_ids`` kapıya, ``finding`` bulgu
yazıcısına gider; biçimsiz paket yalnız o adayı reddeder", test 58; tohum/26k T1, T2).

**The candidates** (``ids``): the run-time candidate ids (``runner.candidate_rerun.ID``, the rule ``koş``
reruns a package under: tohum/26p's, without a dot) among ``names``: every name under the results' ``candidates/`` and every key
of the index's ``reruns`` (``names`` is the set ``yaz``'s ``reruns`` line shows). Any other name is no candidate
and takes no decision: ``koş`` puts no package under it, and a decision row could not carry every such name (one
that is not UTF-8 has no place in the ledger).

**Read by its hash** (``read``). A candidate's package and the gate's three files are taken from
``runner.candidate_rerun.reran`` and from nowhere else: the package is the bytes whose sha256 the index's rerun
entry carries. A candidate ``reran`` does not hand out is ``runner.candidate_rerun.NotRerun`` with ``reran``'s one
reason (``package_missing``, ``rerun_missing``, ``rerun_files_missing``) and nothing of
it is read: it does not reach the gate, and the reason is no gate reason (tohum/26p (5); ``loop.job``'s line names
it, ``yaz_reruns``). A rerun ``koş`` did not verify is handed out (tohum/26p (5)): ``rerun`` is its entry of the index,
``files`` may lack a file (``None``), and ``loop.decide`` rejects it by the entry's reasons; ``merge_diff`` hands
out no diff of one. One whose package has no form ("The package's form": so every package ``koş`` refused as
``package_unusable``) has no diff and no finding for the gate: it is ``Refused`` with ``package_invalid`` and
the entry's reasons (``runner.candidate_rerun.kos_reasons``), so no reason of the entry is lost.

**The package's form** (``parsed``; tohum/26a: ``{finding, diff, organ_ids, definition_sha256[]}``). The package
is UTF-8 JSON (``cli.loads``) in which no string, key or value at any depth, lacks a UTF-8 encoding (a lone
surrogate written as an escape: no ledger row can hold it and no host can name it as a path), an object of
exactly these four keys: ``diff`` a string, ``organ_ids`` what
``gate.allowlist.request`` reads (a list of distinct non-empty strings), ``definition_sha256`` a list of 64
lowercase hex strings (read by nothing: the gate hashes the definitions itself, tohum/26h), ``finding`` an object
``findings.write.proposal_reasons`` accepts. Anything else is ``Refused`` ``package_invalid``: that candidate's
reject, no other candidate's and not the cycle's.

**The finding.** No page gives the form of a package's ``finding`` (reports/seed-100); this brain's reading: it
is the finding as an adapter proposes it (tohum/26's fields, ``findings.write``'s rule 5), the one the fix is
for. From it, and from nothing the package says about itself:

- ``fingerprint``: ``findings.write.fingerprint`` of the finding on the cycle's tree (``None`` when it has none);
- ``found``: what the gate's criteria read (``gate.check.finding``): ``{rule_id, path, line}``, the finding's
  ``rule_id``, its ``file`` and the ``line_start`` of its primary evidence ref (``cases.build.primary``:
  the first ref, when it is in that file; tohum/26q (3)); absent values stay absent, and the gate refuses them
  (``candidate_unusable``).

Caller: ``loop.decide`` (each cycle but the genesis cycle; its rules for a run-time candidate are stated there).
``merge_diff`` gives D6 the diff of the merge D5 chose, read again under the same package hash.

Out of scope, stated: how a finding comes to be a row of the registry (an organ's output is read as a proposal by
no job: reports/seed-098, reports/seed-100; until it is, a live candidate's finding is one the registry does not
hold); a ``reopened`` row for the finding of a merge that is reverted (tohum/26k "Geri alma": nothing
records which finding a merge fixed, and D6's revert writes no finding row; not built); that the diff fixes the finding it names beyond the gate's criteria; the number of candidates of a cycle
(reports/seed-099); who may write the results between ``koş`` and ``yaz``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable

import cli
from cases import build as CB
from findings import write as FW
from gate import allowlist as AL
from ledger import schema as S
from profile import derive as D
from runner import candidate_rerun as CR
from runner import kos as K

KEYS = ("finding", "diff", "organ_ids", "definition_sha256")
INVALID = "package_invalid"
NO_LINE = "no_line"

Read = Callable[[str], "bytes | None"]


class Refused(Exception):
    """A candidate that is not judged further; ``reasons`` is its reject."""

    def __init__(self, *reasons: str) -> None:
        super().__init__(*reasons)
        self.reasons = list(reasons)


class Unusable(ValueError):
    """The merge D5 chose is not the package D5 read."""


@dataclass
class Candidate:
    package_sha256: str
    package: dict               # the parsed package
    diff: str
    files: dict[str, "bytes | None"]    # ``runner.candidate_rerun.FILES`` of the rerun; None: no such file
    rerun: dict                 # the rerun's entry of the index
    fingerprint: str | None     # the finding's fingerprint on the cycle's tree
    found: dict                 # the finding as ``gate.check.finding`` reads it


def reader(results: str) -> Read:
    """``read(path)`` of the results directory: the bytes of a regular file with no link on its way, else None."""
    return lambda path: D._read_regular(results, path)


def index(read: Read) -> Any:
    """The results' ``index.json`` as JSON, ``None`` when absent or not JSON."""
    raw = read(K.INDEX)
    try:
        return cli.loads(raw.decode("utf-8")) if raw is not None else None
    except (ValueError, RecursionError):
        return None


def ids(results: str, index_: Any) -> list[str]:
    """The ids of the results' run-time candidates, in code-point order ("The candidates")."""
    return [name for name in names(results, index_) if CR.ID.fullmatch(name)]


def names(results: str, index_: Any) -> list[str]:
    """Every name under the results' ``candidates/`` and every key of the index's ``reruns``, in code-point
    order."""
    reruns = index_.get("reruns") if isinstance(index_, dict) else None
    try:
        held = set(os.listdir(os.path.join(results, "candidates")))
    except OSError:     # no such directory: no package stands in the results
        held = set()
    return sorted(held | set(reruns if isinstance(reruns, dict) else ()))


def parsed(package: bytes) -> dict:
    """The package as an object of 26a's form, or ``Refused`` ``package_invalid`` ("The package's form")."""
    try:
        doc: Any = cli.loads(package.decode("utf-8"))
        json.dumps(doc, ensure_ascii=False).encode("utf-8")     # UnicodeEncodeError: a string with no encoding
        if not (isinstance(doc, dict) and set(doc) == set(KEYS) and isinstance(doc["diff"], str)):
            raise ValueError
        AL.request({"organ_ids": doc["organ_ids"]})
        if S.list_of(S.hex64)(doc["definition_sha256"], "definition_sha256") or FW.proposal_reasons(doc["finding"]):
            raise ValueError
    except (ValueError, RecursionError):   # AL.Unusable and UnicodeEncodeError are ValueErrors
        raise Refused(INVALID) from None
    return doc


def found(finding: dict) -> dict:
    """The finding as the gate's criteria read it (``gate.check.finding``'s keys; see "The finding")."""
    ref = CB.primary(finding)
    return {"rule_id": finding.get("rule_id"), "path": finding["file"], "line": ref and ref["line_start"]}


def read(index_: Any, cid: str, read_: Read, tree_read: Read) -> Candidate:
    """Candidate ``cid`` of the results; ``Refused``, or ``runner.candidate_rerun.NotRerun`` for one not rerun
    (see the module docstring)."""
    package, files, entry = CR.reran(index_, cid, read_)
    try:
        doc = parsed(package)
    except Refused as exc:      # no diff and no finding to judge: its reject, with what koş said of its rerun
        raise Refused(*exc.reasons, *CR.kos_reasons(entry)) from None
    return Candidate(CR.key(package), doc, doc["diff"], files, entry, FW.fingerprint(doc["finding"], tree_read),
                     found(doc["finding"]))


def merge_diff(results: str, cid: str, package_sha256: str) -> str:
    """The diff of candidate ``cid``'s package, when the package ``reran`` hands out is still the one of
    ``package_sha256`` and its rerun is ``verified``; else ``Unusable``."""
    read_ = reader(results)
    try:
        package, _, entry = CR.reran(index(read_), cid, read_)
    except CR.NotRerun as exc:
        raise Unusable("candidate %s: %s" % (cid, exc.reasons[0])) from None
    if not CR.verified(entry):
        raise Unusable("candidate %s: the rerun is not verified" % cid)
    if CR.key(package) != package_sha256:
        raise Unusable("candidate %s: the package is not the one decided on" % cid)
    return parsed(package)["diff"]
