"""``çek``'s assembly (D1): from what the job has read to the ``pulled`` artifact, pure (stage 0).

Rules: asama-0/01 D1 (``çek`` reads, at the SHA the bootstrap referee last accepted, ``candidates/<target>/`` and
``targets/<target>/units.json``, and the target; it writes ``pulled``), asama-1/05 step 2 (the accepted organs), tohum/26c (``setup/summary.json``
``targets[]``; a ready candidate is ``candidates/<target>/<cid>/`` with ``finding.json``, ``diff.patch`` and
``expect.json``), ``loop.pulled`` (the layout, the one writer and the one reader).

**Inputs** (``assemble``): ``brain``, a ``loop.gitobj`` object source holding the brain repository's commit
``brain_commit`` (the accepted SHA); ``summary`` and ``policy``, the bytes of the referee repository's
``setup/summary.json`` and ``policy.json``; ``target_id``; ``objects``, a ``loop.gitobj`` object source holding the
target's commit; ``commit``, that commit's 40-hex id (``brain/integration``'s head); ``state_head``, the
``brain/state`` head D1 verified, and ``state``, its files of ``target.branches.STATE_CHAINS`` (path -> bytes) as
verified; ``status``, that head's ``status.md`` (``None`` when it has none), carried as read. ``state/heads.json`` is ``{brain/state: state_head, brain/integration: commit}``, so the head recorded
for the tree is the commit the tree was read from. Nothing here reads the network or a clock.

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
- **Organs** (asama-1/05 step 1 and 2, asama-1/06 item 6: the organs ``koş`` may call are those of the brain SHA
  the bootstrap referee accepted). At ``brain_commit``, an organ is a file ``organs/<oid>.json``, ``<oid>`` a
  candidate id (``runner.kos.CANDIDATE_ID``), holding a JSON object of exactly ``entry`` and ``files``:
  ``files`` a list of distinct paths, each a file entry of that commit reached through trees only
  (``loop.gitobj.lookup``, as ``units.json``); the organ's definition is ``{entry, files: {path: the blob's
  bytes}}`` and must be a ``runner.organs`` definition (its docstring's shape: the entry a non-empty list of
  non-empty strings, every path relative and normal, none on the way of another). Every entry of ``organs/`` is
  taken, none is skipped: one that is not such a file is ``organ_invalid:<name>`` (a directory, a link, another
  name, a document of another shape, a path that is no file); ``organs_not_directory`` when ``organs`` is an
  entry that is not a tree; no ``organs`` entry is no organ. The artifact's ``organs.json`` maps each ``<oid>``
  to ``runner.organs.definition_sha256`` of its definition, and the definitions are carried
  (``loop.pulled``, "Organs"). This layout is this module's choice: no seed page says where the brain keeps an
  organ's entry and files (reports/seed-073); tohum/24a puts player code under ``adapters/``, ``fixers/`` and
  the like, so a definition names its files by their brain paths and they reach the container under those
  paths. Every organ carried from here is a key of ``organs.json`` with its own hash, so ``runner.organs``'
  refusals are reached in ``koş`` only by an artifact not written by this module. Not checked: which directories the paths are in (a file under ``referee/`` can be named), and a
  file's executable bit (not part of a definition).
- The tree: ``loop.gitobj.tree_tar(objects, commit)``, the commit's tree read object by object with every id
  recomputed, so ``.gitattributes`` (``export-ignore``, ``export-subst``, filters) has no effect; its reasons
  (``object_missing:<sha>``, ``tree_submodule:<path>``, ...) are listed with the others. What the tree may hold
  (links leaving it, devices) is ``loop.pulled.extract_tree``'s rule in ``kos``, not repeated here.
- **The snapshot** (asama-1/13c, tohum/26a: ``snapshot.make``, job ``çek``): ``snapshot.make.make(objects,
  commit, [], "clean", target)``, the clean snapshot of the same commit, with the ``targets[]`` entry's
  ``excluded_paths``; its document is the artifact's ``snapshot.json`` (``loop.pulled``, "Snapshot"), which
  ``kos`` writes out from the tree and runs the organs on. ``snapshot:target_invalid``: the entry's lists are
  not ones ``profile.derive`` takes (``DeriveError``: e.g. ``excluded_paths`` that is no list of patterns); the
  tree reader's own reasons are the tree's above and are not listed twice. The commit is walked a second time for
  it (measured on the 15134-file target: 8.0 s for the walk and 0.7 s for the snapshot, whose document
  is 2.0 MB for 14911 files; 223 files are left out).
- ``state_incomplete``: ``state`` does not map exactly the paths of ``STATE_CHAINS`` to bytes;
  ``heads_invalid``: ``state_head`` or ``commit`` is not 40 lowercase hex, ``state_head`` ``None`` (the genesis
  cycle) only with both chains empty and no ``status`` (``loop.pulled.write``'s rules).

Then ``loop.pulled.write`` writes the artifact and ``loop.pulled.read`` reads it back (its refusals, e.g.
``json_unreadable:units.json``, are this step's too, and the written directory is removed), so an artifact
left in ``out`` is one ``loop.pulled.read`` accepts.

Out of scope, stated: the reads themselves (the bootstrap result, the target's heads, the fetches: the ``cek`` job's,
``loop.job.cek_d1``, with ``loop.accepted`` and ``loop.fetch``), D1's other checks (``verify --previous`` of
``brain/state``: ``loop.state``; the root signature: ``ledger.anchor.judge`` with ``loop.rekor``), MF4's judgement
of the assembled artifact (``loop.job``'s, on the artifact read back) and its move to ``out/pulled``
(``loop.job``'s, once every check holds).
Which commit is read is the caller's choice; ``pulled`` does not record it. The tree is held in memory (on the
15134-file target: 175 MB of ``tree.tar``, 518 MB peak).
"""

from __future__ import annotations

import shutil
from typing import Any

import cli
from loop import gitobj as G
from loop import pulled as P
from runner import kos as K
from profile import derive as D
from runner import organs as O
from snapshot import make as SM
from target import branches as B

KINDS = ("toy", "copy")  # 26c: targets[].kind


def _entries(summary: bytes) -> list | None:
    """``setup/summary.json``'s ``targets`` list, or ``None`` when ``summary`` is not a JSON object holding one."""
    try:
        doc = cli.loads(summary.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        doc = None
    if not (isinstance(doc, dict) and isinstance(doc.get("targets"), list)):
        return None
    return doc["targets"]


def target_entry(summary: bytes, target_id: str) -> tuple[dict | None, list[str]]:
    entries = _entries(summary)
    if entries is None:
        return None, ["summary_unreadable"]
    found = [t for t in entries if isinstance(t, dict) and t.get("id") == target_id]
    if len(found) != 1:
        return None, ["target_unknown" if not found else "target_ambiguous"]
    return found[0], []


def targets(summary: bytes) -> tuple[list[dict], list[str]]:
    """The targets a run serves (tohum/29s "Hedefler"): every ``targets[]`` entry of ``summary``, in the array's
    order, as read; or ``([], reasons)``: ``summary_unreadable`` (``target_entry``'s), ``targets_empty``,
    ``target_id_unsafe`` (an entry that is not an object whose ``id`` is a target id, ``assemble``'s rule),
    ``target_ambiguous`` (an id twice), ``target_kind_invalid`` (``kind`` not ``toy`` or ``copy``, 26c). The one
    reader of the list: ``cek`` serves it, ``loop.job scope`` scopes the writer token to its repositories."""
    entries = _entries(summary)
    if entries is None:
        return [], ["summary_unreadable"]
    reasons = [] if entries else ["targets_empty"]
    ids = [t.get("id") if isinstance(t, dict) else None for t in entries]
    if not all(isinstance(i, str) and K.CANDIDATE_ID.fullmatch(i) for i in ids):
        reasons.append("target_id_unsafe")
    named = [i for i in ids if isinstance(i, str)]
    if len(set(named)) != len(named):
        reasons.append("target_ambiguous")
    if not all(isinstance(t, dict) and t.get("kind") in KINDS for t in entries):
        reasons.append("target_kind_invalid")
    return ([], reasons) if reasons else (entries, [])


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


ORGANS = "organs"
ORGAN_SUFFIX = ".json"


def _definition(brain: G.Source, commit: str, data: bytes) -> dict | None:
    """The ``runner.organs`` definition an ``organs/<oid>.json`` document ``data`` names at ``commit``, or ``None``
    (see the module docstring, "Organs")."""
    try:
        doc = cli.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None
    if not (isinstance(doc, dict) and set(doc) == {"entry", "files"} and isinstance(doc["files"], list)
            and all(isinstance(p, str) and p for p in doc["files"]) and len(set(doc["files"])) == len(doc["files"])):
        return None
    files = {}
    for path in doc["files"]:
        found = G.lookup(brain, commit, path)
        if found is None or found[0] != "file":
            return None
        files[path] = G.read(brain, found[1], "blob")
    definition = {"entry": doc["entry"], "files": files}
    try:
        O.definition_sha256(definition)
    except O.OrganError:
        return None
    return definition


def _organs(brain: G.Source, commit: str) -> tuple[dict[str, dict], list[str]]:
    """``({oid: definition}, reasons)``: the organs of ``commit`` (see the module docstring, "Organs")."""
    found = G.lookup(brain, commit, ORGANS)
    if found is None:
        return {}, []
    if found[0] != "dir":
        return {}, ["organs_not_directory"]
    entries = G.walk(brain, found[1])
    out: dict[str, dict] = {}
    reasons = []
    for name in sorted({e.path.split("/", 1)[0] for e in entries}):
        entry = next(e for e in entries if e.path == name)
        oid = name[:-len(ORGAN_SUFFIX)]
        definition = _definition(brain, commit, entry.data) \
            if entry.kind == "file" and name.endswith(ORGAN_SUFFIX) and K.CANDIDATE_ID.fullmatch(oid) else None
        if definition is None:
            reasons.append("organ_invalid:%s" % name)
        else:
            out[oid] = definition
    return out, reasons


def _units(brain: G.Source, commit: str, target_id: str) -> bytes | None:
    found = G.lookup(brain, commit, "targets/%s/units.json" % target_id)
    return G.read(brain, found[1], "blob") if found is not None and found[0] == "file" else None


def assemble(brain: G.Source, brain_commit: str, summary: bytes, policy: bytes, target_id: str,
             objects: G.Source, commit: str, state_head: str, state: dict[str, bytes], status: bytes | None,
             out: str) -> dict[str, Any]:
    """Write ``pulled`` into ``out`` (which must not exist) by the rules above; returns its manifest."""
    if not (isinstance(target_id, str) and K.CANDIDATE_ID.fullmatch(target_id)):
        raise P.PulledError(["target_id_unsafe"])
    target, reasons = target_entry(summary, target_id)
    units, candidates, organs = None, {}, {}
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
        organs, bad = _organs(brain, brain_commit)
        reasons += bad
    except P.PulledError as exc:
        reasons += ["brain:%s" % r for r in exc.reasons]
    snapshot = None
    try:
        tree = G.tree_tar(objects, commit)
        snapshot = SM.make(objects, commit, [], "clean", target).document
    except P.PulledError as exc:
        reasons += exc.reasons
    except D.DeriveError:
        reasons.append("snapshot:target_invalid")
    if reasons:
        raise P.PulledError(list(dict.fromkeys(reasons)))
    manifest = P.write(out, target, tree, units, policy, candidates, {B.STATE: state_head, B.INTEGRATION: commit},
                       state, status, {oid: O.definition_sha256(d) for oid, d in organs.items()}, organs, snapshot)
    try:
        P.read(out)
    except P.PulledError:
        shutil.rmtree(out)
        raise
    return manifest
