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

``decision`` is ``merge`` only with no reason. Output ``{decisions: {cid: {decision, reasons}}, merge: cid | None}``.
A recipe whose ``inputs`` is not a list of strings, or a tree ``profile.derive`` refuses, is ``Unusable`` for the
whole cycle (no candidate is judged). Nothing here writes: the ``events`` rows of the reasons, the merge and the ledger are D6's (``loop.write_cycle``).

Out of scope, stated: a run-time candidate's package (``candidates/<id>/package.json`` of ``koş``'s output,
tohum/26j) is not read: P1 MF12 (``loop/candidates.py``) hands it to this gate. An operator excluded path written as a glob is judged by ``gate.diffguard`` as written
(29f coverage), not as a pattern; the staging (``derive``'s pattern rule) leaves such files out of the worktree, so
``kos`` refuses a diff that changes one (``kos:base_file_missing``). Criterion 1's "applies to ``brain/integration``'s
head" is D3's application to the pulled tree (``kos:patch_does_not_apply``); which commit was pulled is D1's.
"""

from __future__ import annotations

import os
from typing import Any

import cli
from gate import check as C
from gate import allowlist as AL
from gate import diffguard as G
from ledger import serial
from loop import pulled as P
from profile import unit_verify as V
from target import branches as B

READY = {"organ_ids": []}   # a ready candidate's package: it is the output of no organ (tohum/26j MF9)


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


def _gate(files: dict[str, bytes], results: str, cid: str, control: Any, unfinished: list[str]) -> list[str]:
    run_dir = os.path.join(results, "c", cid)
    raw_hashes = _bytes_or_none(os.path.join(run_dir, "hashes.json"))
    if raw_hashes is None:
        return ["artefact_hash_mismatch"]
    try:
        hashes = C.hashes_file(cli.loads(raw_hashes))
        found = C.finding(cli.loads(files["finding.json"]))
        got = C.decide(found, files["diff.patch"].decode("utf-8", "surrogateescape"),
                       {"base.jsonl": _bytes_or_none(os.path.join(results, "base.jsonl")),
                        "cand.jsonl": _bytes_or_none(os.path.join(run_dir, "cand.jsonl")),
                        "checks.json": _bytes_or_none(os.path.join(run_dir, "checks.json"))},
                       hashes, C.request({"control": control, "unfinished_sentinels": unfinished}))
    except (C.Unusable, C.DiffError, ValueError):
        return ["candidate_unusable"]
    return got["reasons"]


def decide(art: P.Pulled, recipe: Any, tree: str, results: str, control: Any,
           unfinished: list[str], frozen: list[str]) -> dict[str, Any]:
    """D5 over every candidate; see the module docstring."""
    profile = V.guard_profile(tree, art.target, art.policy)
    index = _index(results)
    control = control if isinstance(control, dict) else {}
    pending = list(unfinished)
    decisions: dict[str, dict] = {}
    merge = None
    try:
        closed = [] if P.genesis(art) else AL.reasons(READY, art.organs, serial.rows(art.state[B.STATE_LEDGER]))
    except (AL.Unusable, serial.Unusable) as exc:
        raise Unusable("decide: allowlist: %s" % cli.cause(exc)) from None
    for cid in sorted(art.candidates):
        files = art.candidates[cid]
        diff_text = files["diff.patch"].decode("utf-8", "surrogateescape")
        try:
            G.parse(diff_text)
        except G.DiffError:
            decisions[cid] = {"decision": "reject", "reasons": ["diff_unusable"]}
            continue
        try:
            reasons = G.check(diff_text, profile, recipe)
        except G.DiffError as exc:  # the diff parsed: the recipe's inputs or the profile is not usable
            raise Unusable("decide: %s" % cli.cause(exc)) from None
        reasons += _kos_reasons(index.get(cid))
        reasons += _gate(files, results, cid, control, pending + ([merge] if merge else []))
        reasons = sorted(set(reasons + list(frozen) + closed))
        decisions[cid] = {"decision": "reject" if reasons else "merge", "reasons": reasons}
        if not reasons and merge is None:
            merge = cid
    return {"decisions": decisions, "merge": merge}
