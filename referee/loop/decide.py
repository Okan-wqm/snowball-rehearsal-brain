"""``yaz``'s D5: the gate's decision on every candidate of the cycle, from the artifacts it downloaded, pure (stage 0).

Rules: asama-0/01 D5 (``yaz`` reads D3's artifacts by hash and decides; judges MF2, MF7, MF8), asama-0/08 (the
acceptance rule: criteria 1-8, each a reason), tohum/29g (``gate.diffguard``'s profile ``{security_paths,
excluded_dirs}``, ``excluded_dirs`` carrying the operator's excluded paths), tohum/29h (``gate.check decide``'s inputs),
tohum/07 (merges are serial: no merge while another merge's sentinel is unfinished).

**Inputs** (``decide``): ``art``, the ``pulled`` artifact as ``loop.pulled.read`` gives it; ``recipe``, its one unit;
``tree``, the directory its ``tree.tar`` was extracted to; ``results``, the ``results`` artifact ``runner.kos`` wrote
(``index.json``, ``base.jsonl``, ``c/<cid>/{cand.jsonl, checks.json, hashes.json}``); ``control``, ``control.json`` as
the job's ``control`` step read it; ``unfinished``, the merge SHAs whose sentinel has not finished
(``ledger.serial.unfinished`` of the ``brain/state`` ledger D1 verified, read by the ``yaz`` job); ``frozen``, the
``frozen:<trigger>`` reasons of the soft freezes in force that close this loop's merges (``gozcu.watch.closed`` of
the same ledger; tohum/28, 27a).

**Rules.** Candidates are judged in code-point order of their id. Each one's ``reasons`` are, sorted and unique:

- the path reasons of ``gate.diffguard.check`` (criterion 1, ``<reason>:<path>``) under
  ``profile.unit_verify.guard_profile`` for ``tree`` (derived from the tree ``kos`` staged with; the activation
  judges with the same function). A diff the parser refuses is ``diff_unusable``, and nothing else is judged for it;
- ``kos:<reason>`` for each reason ``index.json`` gives a candidate that ``kos`` did not verify (``kos:<verdict>``
  when it gives none; ``kos:missing`` when the index has no entry for it), so a refusal of D3 (the patch does not
  apply to the tree, a file outside the worktree, a limit) is the candidate's reason, not lost;
- the reasons of ``gate.check.decide`` (criteria 2-8) on the candidate's three files and ``hashes.json``, with
  ``{control, unfinished_sentinels}``. Without ``c/<cid>/hashes.json`` there is nothing whose hash can hold:
  ``artefact_hash_mismatch``. A ``finding.json``, run file or ``hashes.json`` ``gate.check`` cannot use is
  ``candidate_unusable``;
- every reason of ``frozen`` (tohum/28: the merge gate is closed), so under a freeze no candidate merges;
- in every cycle but the genesis cycle (``loop.pulled.genesis``), the reasons of ``gate.allowlist.reasons``
  (P1 MF9, tohum/26j "İzin listesi, MF9") for the candidate's package, against ``art.organs`` (the organ
  definitions of the accepted SHA) and the ``accept`` rows of ``pulled``'s ``brain/state`` ledger (the ledger
  the cycle started from: rows this cycle writes open the gate from the next). The candidates judged here are
  the ready candidates of ``candidates/<target>/``, whose package names no organ (``READY``), so each carries
  ``no_organ`` and no cycle after the genesis cycle merges one (26j: "Aşama 0'ın hazır adayları P1'in
  aktarımıyla biter"); the genesis cycle keeps stage 0's rule. A ledger ``ledger.serial`` or the allowlist
  cannot read is ``Unusable`` for the whole cycle;
- merges are serial: the first candidate with no reason is the cycle's merge; every later one is judged with that
  candidate in ``unfinished_sentinels`` (its merge is written in D6 and its sentinel runs in the next cycle's D7),
  so it carries ``sentinel_pending``.

**A run-time candidate** (P1 MF12, tohum/26j "Aday yolu", test 58; ``loop.candidates``), in every cycle but the
genesis cycle (where none is read): each id of ``loop.candidates.ids`` is judged in the same order, among the
ready ones.

- An id that is also a ready candidate's is one reject for both, ``candidate_id_twice`` (one id is one decision
  row), and neither is judged.
- A candidate ``loop.candidates.read`` refuses carries that one reason (a package not read by its rerun's hash,
  or ``package_invalid``) and nothing else is judged for it: it does not reach the gate.
- Otherwise its reasons are the path reasons of its package's ``diff`` (``diff_unusable`` as above), the reasons
  of ``gate.check.decide`` on the three files of its rerun (``r/<id>/``, handed out by
  ``runner.candidate_rerun.reran``) with the finding ``loop.candidates.found`` derives, ``frozen``, the reasons
  of ``gate.allowlist.reasons`` for the package itself (its ``organ_ids``; never ``READY``; when it names a
  definition of ``pulled`` the allowlist cannot hash, ``organ_unusable`` beside the reasons of the ids it can
  judge: the package chose the definition, so it is that candidate's reject, 26k T2), and its finding's:
  ``no_line`` (the finding has no fingerprint on the cycle's tree), ``registry_unusable`` (``pulled``'s
  ``findings.jsonl`` is no valid chain: D6 stops on the same file), ``findings.write.refusal`` of the finding's
  last row in that file (``finding_unknown``, ``finding_not_open``: tohum/26k T1, given before the merge is
  chosen, so no merge lands for a finding the registry refuses), or ``finding_decided`` when an earlier
  candidate of this cycle took a decision on the same fingerprint that was not a closed gate's
  (``ledger.events.standing``): the later candidate is rejected and the cycle goes on (26k T2).
- Its decision carries ``package_sha256``. A candidate with none of the finding's reasons gives one
  ``{fingerprint, reasons}`` to ``finding_decisions``, in the order judged: what ``findings.write.decide``
  takes, with no fingerprint it refuses and none it would call decided twice.

``decision`` is ``merge`` only with no reason. Output ``{decisions: {cid: {decision, reasons, package_sha256?}},
merge: cid | None, finding_decisions}``.
A recipe whose ``inputs`` is not a list of strings, or a tree ``profile.derive`` refuses, is ``Unusable`` for
the whole cycle (no candidate is judged). Nothing here
writes: the ``events`` rows of the reasons, the merge, the registry's rows and the ledger are D6's
(``loop.write_cycle``).

Out of scope, stated: a finding proposed in the same cycle (no job hands ``yaz`` a proposal: the registry read
here is the one the cycle started from; reports/seed-100), so live every run-time candidate's finding is one the
registry does not hold until a proposal is read; a ``reopened`` row when a run-time merge is reverted
(tohum/26k "Geri alma"; not built, ``loop.candidates``); ``kos:`` reasons for a run-time candidate (one not verified is
not handed out). An operator excluded path written as a glob is judged by ``gate.diffguard`` as written
(29f coverage), not as a pattern; the staging (``derive``'s pattern rule) leaves such files out of the worktree, so
``kos`` refuses a diff that changes one (``kos:base_file_missing``). Criterion 1's "applies to ``brain/integration``'s
head" is D3's application to the pulled tree (``kos:patch_does_not_apply``); which commit was pulled is D1's.
"""

from __future__ import annotations

import os
from typing import Any

import cli
from findings import write as FW
from gate import check as C
from gate import allowlist as AL
from gate import diffguard as G
from ledger import append, events, serial
from loop import candidates as LC
from loop import pulled as P
from profile import derive as D
from profile import unit_verify as V
from runner import candidate_rerun as CR
from target import branches as B

READY = {"organ_ids": []}   # a ready candidate's package: it is the output of no organ (tohum/26j MF9)
TWICE = "candidate_id_twice"
DECIDED = "finding_decided"
REGISTRY = "registry_unusable"
ORGAN_UNUSABLE = "organ_unusable"


class Unusable(ValueError):
    """The cycle's own inputs (the recipe, the profile) cannot be used: no candidate is judged."""


def _bytes_or_none(path: str) -> bytes | None:
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except (FileNotFoundError, NotADirectoryError, IsADirectoryError):
        return None


def _index(results: str) -> dict:
    raw = _bytes_or_none(os.path.join(results, "index.json"))
    try:
        doc = cli.loads(raw) if raw is not None else {}
    except ValueError:
        doc = {}
    cands = doc.get("candidates") if isinstance(doc, dict) else None
    return cands if isinstance(cands, dict) else {}


def _kos_reasons(entry: Any) -> list[str]:
    if not isinstance(entry, dict):
        return ["kos:missing"]
    if entry.get("verdict") == "verified":
        return []
    reasons = entry.get("reasons")
    if isinstance(reasons, list) and reasons and all(isinstance(r, str) for r in reasons):
        return ["kos:%s" % r for r in reasons]
    return ["kos:%s" % entry.get("verdict")]


def _gate(found: Any, diff_text: str, results: str, run: dict[str, "bytes | None"], control: Any,
          unfinished: list[str]) -> list[str]:
    """``gate.check.decide``'s reasons for one candidate: ``found`` its finding as a document, ``run`` its
    ``cand.jsonl``, ``checks.json`` and ``hashes.json``."""
    if run["hashes.json"] is None:
        return ["artefact_hash_mismatch"]
    try:
        got = C.decide(C.finding(found), diff_text,
                       {"base.jsonl": _bytes_or_none(os.path.join(results, "base.jsonl")),
                        "cand.jsonl": run["cand.jsonl"], "checks.json": run["checks.json"]},
                       C.hashes_file(cli.loads(run["hashes.json"])),
                       C.request({"control": control, "unfinished_sentinels": unfinished}))
    except (C.Unusable, C.DiffError, ValueError):
        return ["candidate_unusable"]
    return got["reasons"]


def _ready(files: dict[str, bytes], results: str, cid: str) -> tuple[Any, dict[str, "bytes | None"]]:
    """A ready candidate's finding and run files: ``finding.json`` of ``pulled`` and ``c/<cid>/`` of the results."""
    run_dir = os.path.join(results, "c", cid)
    run = {name: _bytes_or_none(os.path.join(run_dir, name)) for name in CR.FILES}
    try:
        return cli.loads(files["finding.json"]), run
    except ValueError:
        return None, run        # no object: ``gate.check.finding`` refuses it (``candidate_unusable``)


def _runtime(art: P.Pulled, tree: str, results: str) -> tuple[dict[str, Any], "dict[str, dict] | None"]:
    """``({id: loop.candidates.Candidate | its Refused}, the registry's last rows)`` of the cycle's run-time
    candidates: none in the genesis cycle; the rows are ``None`` when the findings file is no valid chain."""
    if P.genesis(art):
        return {}, None
    read = LC.reader(results)
    index = LC.index(read)
    got: dict[str, Any] = {}
    for cid in LC.ids(results, index):
        try:
            got[cid] = LC.read(index, cid, read, lambda path: D._read_regular(tree, path))
        except LC.Refused as exc:
            got[cid] = exc
    try:
        return got, FW.last(art.state.get(B.STATE_FINDINGS, b""))
    except append.HardStop:
        return got, None


def _named(package: dict, definitions: Any, rows: list[dict]) -> list[str]:
    """The allowlist's reasons for each organ id of ``package`` alone, those it can judge."""
    out: list[str] = []
    for organ_id in package["organ_ids"]:
        try:
            out += AL.reasons({"organ_ids": [organ_id]}, definitions, rows)
        except AL.Unusable:
            pass
    return out


def _finding_reasons(cand: LC.Candidate, registry: "dict[str, dict] | None", named: set[str]) -> list[str]:
    """Why the candidate's finding takes no decision of this cycle (tohum/26k T1, T2), or ``[]``."""
    if cand.fingerprint is None:
        return [LC.NO_LINE]
    if registry is None:
        return [REGISTRY]
    refusal = FW.refusal(registry.get(cand.fingerprint))
    if refusal:
        return [refusal]
    return [DECIDED] if cand.fingerprint in named else []


def decide(art: P.Pulled, recipe: Any, tree: str, results: str, control: Any,
           unfinished: list[str], frozen: list[str]) -> dict[str, Any]:
    """D5 over every candidate; see the module docstring."""
    profile = V.guard_profile(tree, art.target, art.policy)
    index = _index(results)
    control = control if isinstance(control, dict) else {}
    pending = list(unfinished)
    decisions: dict[str, dict] = {}
    finding_decisions: list[dict] = []
    named: set[str] = set()
    merge = None
    try:
        rows = None if P.genesis(art) else serial.rows(art.state[B.STATE_LEDGER])
        closed = [] if rows is None else AL.reasons(READY, art.organs, rows)
    except (AL.Unusable, serial.Unusable) as exc:
        raise Unusable("decide: allowlist: %s" % cli.cause(exc)) from None
    runtime, registry = _runtime(art, tree, results)
    for cid in sorted(set(art.candidates) | set(runtime)):
        cand = runtime.get(cid)
        if cand is not None and cid in art.candidates:
            decisions[cid] = {"decision": "reject", "reasons": [TWICE]}
            continue
        if isinstance(cand, LC.Refused):
            decisions[cid] = {"decision": "reject", "reasons": cand.reasons}
            continue
        if cand is None:
            diff_text = art.candidates[cid]["diff.patch"].decode("utf-8", "surrogateescape")
        else:
            diff_text = cand.diff
        try:
            G.parse(diff_text)
        except G.DiffError:
            decisions[cid] = {"decision": "reject", "reasons": ["diff_unusable"]}
            continue
        try:
            reasons = G.check(diff_text, profile, recipe)
        except G.DiffError as exc:  # the diff parsed: the recipe's inputs or the profile is not usable
            raise Unusable("decide: %s" % cli.cause(exc)) from None
        serial_ = pending + ([merge] if merge else [])
        if cand is None:
            reasons += _kos_reasons(index.get(cid))
            found, run = _ready(art.candidates[cid], results, cid)
            reasons += _gate(found, diff_text, results, run, control, serial_)
            reasons += closed
        else:
            reasons += _gate(cand.found, diff_text, results, dict(cand.files), control, serial_)
            try:
                reasons += AL.reasons(cand.package, art.organs, rows)
            except AL.Unusable:     # the rows were read above: a definition the package names cannot be hashed
                reasons += _named(cand.package, art.organs, rows) + [ORGAN_UNUSABLE]
            reasons += _finding_reasons(cand, registry, named)
        reasons = sorted(set(reasons + list(frozen)))
        decisions[cid] = {"decision": "reject" if reasons else "merge", "reasons": reasons}
        if cand is not None:
            decisions[cid]["package_sha256"] = cand.package_sha256
            if not _finding_reasons(cand, registry, named):
                finding_decisions.append({"fingerprint": cand.fingerprint, "reasons": reasons})
                if not events.standing(reasons):
                    named.add(cand.fingerprint)     # type: ignore[arg-type]
        if not reasons and merge is None:
            merge = cid
    return {"decisions": decisions, "merge": merge, "finding_decisions": finding_decisions}
