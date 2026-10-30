"""``çek``'s assembly (D1): from what the job has read to the ``pulled`` artifact, pure (stage 0).

Rules: asama-0/01 D1 (``çek`` reads, at the SHA the bootstrap referee last accepted, ``candidates/<target>/`` and
``targets/<target>/units.json``, and the target; it writes ``pulled``), tohum/26c (``setup/summary.json``
``targets[]``; a ready candidate is ``candidates/<target>/<cid>/`` with ``finding.json``, ``diff.patch`` and
``expect.json``), ``loop.pulled`` (the layout, the one writer and the one reader).

**Inputs** (``assemble``): ``brain``, a checkout of the brain repository at the accepted SHA (a directory);
``summary`` and ``policy``, the bytes of the referee repository's ``setup/summary.json`` and ``policy.json``;
``target_id``; ``objects``, a ``loop.gitobj`` object source holding the target's commit; ``commit``, that
commit's 40-hex id. Nothing here reads the network or a clock.

**Rules**, every reason that holds is listed (``PulledError``; ``out`` is not created):

- ``target_id_unsafe``: the id is not one path component of ``[A-Za-z0-9][A-Za-z0-9._-]*`` (at most 128),
  since it names directories of the brain; checked first, nothing is read when it fails.
- ``summary_unreadable``: ``summary`` is not a JSON object whose ``targets`` is a list;
  ``target_unknown`` / ``target_ambiguous``: not exactly one ``targets[]`` object has ``id == target_id``. That
  entry is the artifact's ``target``, as read.
- ``units_missing``: ``targets/<id>/units.json`` is not a regular file with no symlink on its way.
- ``candidates_not_directory``: ``candidates/<id>`` exists but is not a real directory, or ``candidates`` is
  not one. When ``candidates`` or (under a real ``candidates``) ``candidates/<id>`` does not exist, the target
  has no ready candidates. ``candidate_invalid:<name>``: an entry of it whose name is not a candidate
  id (``runner.kos.CANDIDATE_ID``), that is not a real directory, or that does not hold exactly the three files,
  each a regular file. Every candidate directory is taken; none is skipped.
- The tree: ``loop.gitobj.tree_tar(objects, commit)``, the commit's tree read object by object with every id
  recomputed, so ``.gitattributes`` (``export-ignore``, ``export-subst``, filters) has no effect; its reasons
  (``object_missing:<sha>``, ``tree_submodule:<path>``, ...) are listed with the others. What the tree may hold
  (links leaving it, devices) is ``loop.pulled.extract_tree``'s rule in ``kos``, not repeated here.

Then ``loop.pulled.write`` writes the artifact and ``loop.pulled.read`` reads it back (its refusals, e.g.
``json_unreadable:units.json``, are this step's too, and the written directory is removed), so an artifact
left in ``out`` is one ``loop.pulled.read`` accepts.

Out of scope, stated: the reads themselves (the bootstrap result and its Sigstore bundle, the brain checkout at
its ``last_accepted_sha``, the target's ``brain/state`` and ``brain/integration`` heads, the fetch of the target's
commit into the git directory ``loop.gitobj.GitBatch`` reads) and D1's checks on them (``verify --previous``,
the root signature, the accepted SHA's ``referee/`` hash against the last ``setup/imports.jsonl`` row: no page
this clone has gives that hash's algorithm), and the ``profile.derive`` judgement of D1 (MF4). Which commit is
read is the caller's choice; ``pulled`` does not record it. The tree is held in memory (on the 15134-file
target: 175 MB of ``tree.tar``, 518 MB peak). The ``cek`` job does not call this yet: it still
stops with ``cycle_not_wired``. The brain is still read from a checkout directory, not from its objects.
"""

from __future__ import annotations

import json
import os
import shutil
from typing import Any

from loop import gitobj as G
from loop import pulled as P
from profile import derive as D
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


def _candidates(brain: str, target_id: str) -> tuple[dict[str, dict[str, bytes]], list[str]]:
    rel = "candidates/%s" % target_id
    root = os.path.join(brain, "candidates", target_id)
    top = os.path.join(brain, "candidates")
    if not os.path.lexists(top) or (D._real_dir(brain, "candidates") == "" and not os.path.lexists(root)):
        return {}, []
    if D._real_dir(brain, rel) != "":
        return {}, ["candidates_not_directory"]
    found: dict[str, dict[str, bytes]] = {}
    reasons = []
    for name in sorted(os.listdir(root)):
        files: dict[str, bytes] = {}
        # a symlink on the way (the candidate directory or a file) is refused by _read_regular
        if K.CANDIDATE_ID.fullmatch(name) and os.path.isdir(os.path.join(root, name)) \
                and sorted(os.listdir(os.path.join(root, name))) == sorted(P.CANDIDATE_FILES):
            for f in P.CANDIDATE_FILES:
                data = D._read_regular(brain, "%s/%s/%s" % (rel, name, f))
                if data is not None:
                    files[f] = data
        if len(files) == len(P.CANDIDATE_FILES):
            found[name] = files
        else:
            reasons.append("candidate_invalid:%s" % name)
    return found, reasons


def assemble(brain: str, summary: bytes, policy: bytes, target_id: str, objects: G.Source, commit: str,
             out: str) -> dict[str, Any]:
    """Write ``pulled`` into ``out`` (which must not exist) by the rules above; returns its manifest."""
    if not (isinstance(target_id, str) and K.CANDIDATE_ID.fullmatch(target_id)):
        raise P.PulledError(["target_id_unsafe"])
    target, reasons = _target(summary, target_id)
    units = D._read_regular(brain, "targets/%s/units.json" % target_id)
    if units is None:
        reasons.append("units_missing")
    candidates, bad = _candidates(brain, target_id)
    reasons += bad
    try:
        tree = G.tree_tar(objects, commit)
    except P.PulledError as exc:
        reasons += exc.reasons
    if reasons:
        raise P.PulledError(reasons)
    manifest = P.write(out, target, tree, units, policy, candidates)
    try:
        P.read(out)
    except P.PulledError:
        shutil.rmtree(out)
        raise
    return manifest
