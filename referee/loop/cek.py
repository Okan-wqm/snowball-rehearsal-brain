"""``çek``'s assembly (D1): from what the job has read to the ``pulled`` artifact, pure (stage 0).

Rules: asama-0/01 D1 (``çek`` reads, at the SHA the bootstrap referee last accepted, ``candidates/<target>/`` and
``targets/<target>/units.json``, and the target; it writes ``pulled``), tohum/26c (``setup/summary.json``
``targets[]``; a ready candidate is ``candidates/<target>/<cid>/`` with ``finding.json``, ``diff.patch`` and
``expect.json``), ``loop.pulled`` (the layout, the one writer and the one reader).

**Inputs** (``assemble``): ``brain``, a ``loop.gitobj`` object source holding the brain repository's commit
``brain_commit`` (the accepted SHA); ``summary`` and ``policy``, the bytes of the referee repository's
``setup/summary.json`` and ``policy.json``; ``target_id``; ``objects``, a ``loop.gitobj`` object source holding the
target's commit; ``commit``, that commit's 40-hex id. Nothing here reads the network or a clock.

**Rules**, every reason that holds is listed (``PulledError``; ``out`` is not created):

- ``target_id_unsafe``: the id is not one path component of ``[A-Za-z0-9][A-Za-z0-9._-]*`` (at most 128),
  since it names directories of the brain; checked first, nothing is read when it fails.
- ``summary_unreadable``: ``summary`` is not a JSON object whose ``targets`` is a list;
  ``target_unknown`` / ``target_ambiguous``: not exactly one ``targets[]`` object has ``id == target_id``. That
  entry is the artifact's ``target``, as read.
- The brain is read from its git objects with ``loop.gitobj`` like the target (one tree reader for both
  repositories): its files are the blobs as committed, so no checkout's ``.gitattributes`` (end of line,
  filters) can change a ``diff.patch``; a symbolic link is an entry of kind link, never followed.
- ``units_missing``: ``targets/<id>/units.json`` is not a file entry reached through trees only
  (``loop.gitobj.lookup``: absent, a link, a tree, a gitlink, or a link or file on the way).
- ``candidates_not_directory``: ``candidates`` or ``candidates/<id>`` is an entry that is not a tree (a link, a
  file, a gitlink, a malformed mode). When ``candidates`` or, under it, ``candidates/<id>`` is absent, the target
  has no ready candidates. ``candidates/<id>`` is walked whole (``loop.gitobj.walk``). A ``loop.gitobj`` reason
  of a brain read (the commit, the trees on the way, the walk) is listed as ``brain:<reason>``, e.g.
  ``brain:commit_unreadable``, ``brain:tree_submodule:<cid>/x``, so it is not taken for the target's.
  ``candidate_invalid:<name>``: an entry of ``candidates/<id>`` whose name is not a candidate id
  (``runner.kos.CANDIDATE_ID``), that is not a tree, or that does not hold exactly the three entries, each a file.
  Every candidate directory is taken; none is skipped.
- The tree: ``loop.gitobj.tree_tar(objects, commit)``, the commit's tree read object by object with every id
  recomputed, so ``.gitattributes`` (``export-ignore``, ``export-subst``, filters) has no effect; its reasons
  (``object_missing:<sha>``, ``tree_submodule:<path>``, ...) are listed with the others. What the tree may hold
  (links leaving it, devices) is ``loop.pulled.extract_tree``'s rule in ``kos``, not repeated here.

Then ``loop.pulled.write`` writes the artifact and ``loop.pulled.read`` reads it back (its refusals, e.g.
``json_unreadable:units.json``, are this step's too, and the written directory is removed), so an artifact
left in ``out`` is one ``loop.pulled.read`` accepts.

Out of scope, stated: the reads themselves (the bootstrap result and its Sigstore bundle, the target's
``brain/state`` and ``brain/integration`` heads, and which commits are fetched: ``loop.fetch`` fills a git
directory ``loop.gitobj.GitBatch`` reads with one commit, but nothing calls it yet) and D1's checks on them (``verify --previous``,
the root signature, the accepted SHA's ``referee/`` hash against the last ``setup/imports.jsonl`` row: no page
this clone has gives that hash's algorithm), and the ``profile.derive`` judgement of D1 (MF4). Which commit is
read is the caller's choice; ``pulled`` does not record it. The tree is held in memory (on the 15134-file
target: 175 MB of ``tree.tar``, 518 MB peak). The ``cek`` job does not call this yet: it still
stops with ``cycle_not_wired``.
"""

from __future__ import annotations

import json
import shutil
from typing import Any

from loop import gitobj as G
from loop import pulled as P
from runner import kos as K


def _target(summary: bytes, target_id: str) -> tuple[dict | None, list[str]]:
    try:
        doc = json.loads(summary.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        doc = None
    if not (isinstance(doc, dict) and isinstance(doc.get("targets"), list)):
        return None, ["summary_unreadable"]
    found = [t for t in doc["targets"] if isinstance(t, dict) and t.get("id") == target_id]
    if len(found) != 1:
        return None, ["target_unknown" if not found else "target_ambiguous"]
    return found[0], []


def _candidates(brain: G.Source, commit: str, target_id: str) -> tuple[dict[str, dict[str, bytes]], list[str]]:
    for path in ("candidates", "candidates/%s" % target_id):
        found = G.lookup(brain, commit, path)
        if found is None:
            return {}, []
        if found[0] != "dir":
            return {}, ["candidates_not_directory"]
    entries = G.walk(brain, found[1])
    top = sorted({e.path.split("/", 1)[0] for e in entries})
    out: dict[str, dict[str, bytes]] = {}
    reasons = []
    for name in top:
        kinds = {e.path: e.kind for e in entries if e.path == name or e.path.startswith(name + "/")}
        want = {name: "dir", **{"%s/%s" % (name, f): "file" for f in P.CANDIDATE_FILES}}
        if K.CANDIDATE_ID.fullmatch(name) and kinds == want:
            out[name] = {f: e.data for e in entries for f in P.CANDIDATE_FILES if e.path == "%s/%s" % (name, f)}
        else:
            reasons.append("candidate_invalid:%s" % name)
    return out, reasons


def _units(brain: G.Source, commit: str, target_id: str) -> bytes | None:
    found = G.lookup(brain, commit, "targets/%s/units.json" % target_id)
    return G.read(brain, found[1], "blob") if found is not None and found[0] == "file" else None


def assemble(brain: G.Source, brain_commit: str, summary: bytes, policy: bytes, target_id: str,
             objects: G.Source, commit: str, out: str) -> dict[str, Any]:
    """Write ``pulled`` into ``out`` (which must not exist) by the rules above; returns its manifest."""
    if not (isinstance(target_id, str) and K.CANDIDATE_ID.fullmatch(target_id)):
        raise P.PulledError(["target_id_unsafe"])
    target, reasons = _target(summary, target_id)
    units, candidates = None, {}
    try:
        units = _units(brain, brain_commit, target_id)
        if units is None:
            reasons.append("units_missing")
    except P.PulledError as exc:
        reasons += ["brain:%s" % r for r in exc.reasons]
    try:
        candidates, bad = _candidates(brain, brain_commit, target_id)
        reasons += bad
    except P.PulledError as exc:
        reasons += ["brain:%s" % r for r in exc.reasons]
    try:
        tree = G.tree_tar(objects, commit)
    except P.PulledError as exc:
        reasons += exc.reasons
    if reasons:
        raise P.PulledError(list(dict.fromkeys(reasons)))
    manifest = P.write(out, target, tree, units, policy, candidates)
    try:
        P.read(out)
    except P.PulledError:
        shutil.rmtree(out)
        raise
    return manifest
