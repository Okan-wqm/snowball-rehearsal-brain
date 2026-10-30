"""``çek``'s assembly (D1): from what the job has read to the ``pulled`` artifact, pure (stage 0).

Rules: asama-0/01 D1 (``çek`` reads, at the SHA the bootstrap referee last accepted, ``candidates/<target>/`` and
``targets/<target>/units.json``, and the target; it writes ``pulled``), tohum/26c (``setup/summary.json``
``targets[]``; a ready candidate is ``candidates/<target>/<cid>/`` with ``finding.json``, ``diff.patch`` and
``expect.json``), ``loop.pulled`` (the layout, the one writer and the one reader).

**Inputs** (``assemble``): ``brain``, a checkout of the brain repository at the accepted SHA (a directory);
``summary`` and ``policy``, the bytes of the referee repository's ``setup/summary.json`` and ``policy.json``;
``target_id``; ``tarball``, the bytes GitHub's ``GET /repos/{owner}/{repo}/tarball/{ref}`` returns; ``commit``,
the 40-hex commit that tarball was asked for. Nothing here reads the network or a clock.

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
- The tree (``tree_tar``): ``tarball_unreadable`` (not a gzip-compressed tar archive ``tarfile`` reads; it
  also refuses a global header followed by no member);
  ``tarball_commit_mismatch`` (the archive's pax global header ``comment``, where ``git archive`` writes the
  commit it archived, is not ``commit``); ``tarball_layout`` (the members do not all sit under one top
  directory, the first member, as ``git archive --prefix`` writes them, or a hard link points outside it). The
  top directory is dropped from every name and hard-link target; symbolic link targets, modes and contents are
  kept as they are. What the tree may hold (``..``, links leaving it, devices) is ``loop.pulled.extract_tree``'s
  rule in ``kos``, not repeated here.

Then ``loop.pulled.write`` writes the artifact and ``loop.pulled.read`` reads it back (its refusals, e.g.
``json_unreadable:units.json``, are this step's too, and the written directory is removed), so an artifact
left in ``out`` is one ``loop.pulled.read`` accepts.

Out of scope, stated: the reads themselves (the bootstrap result and its Sigstore bundle, the brain checkout at
its ``last_accepted_sha``, the target's ``brain/state`` and ``brain/integration`` heads, the tarball request) and
D1's checks on them (``verify --previous``, the root signature, the accepted SHA's ``referee/`` hash against the
last ``setup/imports.jsonl`` row: no page this clone has gives that hash's algorithm), and the ``profile.derive``
judgement of D1 (MF4). Which ref the tarball is of is the caller's choice; ``pulled`` does not record it. The
tarball is held in memory (its size is bounded by the job's memory). The ``cek`` job does not call this yet: it
still stops with ``cycle_not_wired``. GitHub's tarball is taken to be ``git archive``'s ``tar.gz`` form (a pax
global header with the commit, one prefix directory); this was measured on ``git archive`` output, not on a
response of GitHub's API.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import tarfile
from typing import Any

from loop import pulled as P
from profile import derive as D
from runner import kos as K


def tree_tar(tarball: bytes, commit: str) -> bytes:
    """GitHub's tarball of ``commit`` -> ``pulled``'s ``tree.tar`` (no top directory); ``PulledError``."""
    try:
        with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as src:
            members = src.getmembers()
            comment = src.pax_headers.get("comment")
            if comment != commit:
                raise P.PulledError(["tarball_commit_mismatch"])
            if not members or not members[0].isdir() or "/" in members[0].name.rstrip("/"):
                raise P.PulledError(["tarball_layout"])
            top = members[0].name.rstrip("/") + "/"
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as dst:
                for member in members[1:]:
                    if not member.name.startswith(top):
                        raise P.PulledError(["tarball_layout"])
                    info = member.replace(name=member.name[len(top):], deep=False)
                    if member.islnk():
                        if not member.linkname.startswith(top):
                            raise P.PulledError(["tarball_layout"])
                        info = info.replace(linkname=member.linkname[len(top):], deep=False)
                    dst.addfile(info, src.extractfile(member) if member.isreg() else None)
    except P.PulledError:
        raise
    except (tarfile.TarError, EOFError, OSError, ValueError):
        raise P.PulledError(["tarball_unreadable"]) from None
    return buf.getvalue()


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


def assemble(brain: str, summary: bytes, policy: bytes, target_id: str, tarball: bytes, commit: str,
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
        tree = tree_tar(tarball, commit)
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
