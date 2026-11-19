"""``snapshot.make``: a target commit's tree as a snapshot without leaks, with an identity (stage 1, P1 MF2).

Rules: asama-1/13c (the snapshot is made from the commit's file list, ``export-ignore`` has no effect, there is no
``.git``; ``<state_root>/**``, the excluded directories, the excluded paths and the agent configuration are left
out; every identity tied to a planted case is replaced in every file; a planted snapshot holds cases of one
property whose touched paths do not meet; a clean one holds none and nothing tells which one is clean; a snapshot
carries ``snapshot_id``, a content hash, and a manifest, file -> sha256), asama-0/09 test 8, tohum/26a
(``snapshot.make``: ``base_sha``, the case list and the kind in; ``snapshot_id`` and the manifest out; job
``çek``).

**The tree** (``make``): ``loop.gitobj.entries(source, base_sha)``, the commit's tree read object by object from
its file list, so ``.gitattributes`` (``export-ignore``, filters) hides nothing and changes no byte; that reader
refuses a tree holding an entry named ``.git`` in any case, or a gitlink (its ``PulledError`` is raised as it
is). ``build`` is the same over entries already read.

**Left out** (a file or a link; a directory is not an entry of a snapshot, so a directory with nothing kept in it
is not in it):

1. a path that is ``.brain`` or under it at the root of the tree (``target.branches.STATE_ROOT``, in that
   spelling; a ``.brain`` deeper in the tree is kept);
2. a path ``profile.derive.excluded`` excludes: a component that is an agent configuration name or an excluded
   directory name, in any case, or the path matching one of the operator's ``target.excluded_paths`` patterns
   (``target`` is the ``targets[]`` entry; ``None``: no patterns; an invalid one is ``DeriveError``, that
   module's). One rule for the profile and the snapshot.

A link is kept as written unless its own path is left out: what it points at is not judged here.

**The kind and the cases.** ``kind`` is ``clean`` or ``planted`` (else ``kind_unknown``). A case is an object of
exactly ``property`` (a non-empty string), ``paths`` (a non-empty list of distinct paths: the files it
touches), ``identifiers`` (a list of distinct non-empty strings: every identity tied to the case, e.g. its
finding id, its fix commit's SHA, its finding's title) and ``replace`` (``{path: bytes}``, each path one of
``paths``: the file's planted content); another shape is ``case_invalid:<index>``. Every reason that holds is
listed (``SnapshotError``):

- ``clean_has_cases``: a clean snapshot is given a case;
- ``planted_no_cases``: a planted one is given none; ``max_cases_invalid``: ``max_cases`` is not a positive
  integer (the caller reads it from ``stage_params.planted_max_cases``; no number is kept here);
  ``cases_over_max``: more cases than ``max_cases``;
- ``cases_mixed_property``: two cases name different properties;
- ``cases_paths_overlap:<path>``: a path two cases touch;
- ``case_path_missing:<path>``: a touched path that is not a file of the snapshot (absent, a link, or left out).

**Sanitizing** (planted). After the ``replace`` contents are laid, every occurrence of an identifier's UTF-8
bytes in any file's bytes is replaced by ``PLACEHOLDER``, in one pass from the start of the file, the longest
identifier first where two start at the same byte. Then no identifier may be left: ``sanitize_incomplete:<path>``
for a file where the replacement itself made one (``XY`` and ``DQ`` in ``XYQ``), ``identifier_in_path:<path>``
for a file's or link's path, or a link's target, holding one (a path is not rewritten). ``identifier_invalid``:
an identifier that occurs in ``PLACEHOLDER``. Out of scope, stated: an identifier written another way (another
encoding or case, split over lines, inside a compressed file), and the profile's ``finding_id_patterns``
(asama-1/13c: cleaned in comment and document lines only): nothing on the loop's path makes that list yet
and no page says what a comment line is per language (reports/seed-074).

**The document** (``Snapshot.document``; ``Snapshot.files`` holds the bytes, path -> bytes)::

    {schema: "snowball-snapshot/1", snapshot_id, files: {path: sha256}, links: {path: target}, exec: [path]}

``files`` is the manifest; ``exec`` the sorted files whose mode has the owner's execute bit; ``snapshot_id`` the
sha256, lowercase hex, of the UTF-8 bytes of ``{exec, files, links}`` as JSON with sorted keys, separators ``,``
and ``:``, non-ASCII escaped and no newline. So the id changes with any byte or path of a file, a link or its
target, and an execute bit. The document has no key for the kind or the cases: a clean and a planted document
have the same shape. (A planted snapshot's files hold ``PLACEHOLDER`` where an identifier was; that is 13c's
rule and it is seen by whoever reads the files.)

**Writing** (``write(document, dest, content)``; the short-lived directory). ``check`` first: the shape above
with 64 lowercase hex hashes, every path relative with no empty, ``.`` or ``..`` component and no NUL, no path
twice or on the way of another, ``exec`` sorted, distinct and of ``files`` (``document_invalid``); the id
recomputed (``id_mismatch``). ``dest`` must not exist (``dest_exists``). Each file is ``content(path)``, bytes
or ``None`` (``file_missing:<path>``), with the manifest's sha256 (``hash_mismatch:<path>``), written as a new
regular file, mode ``0o755`` when in ``exec`` else ``0o644``; each link is made as written. Every reason found
is listed and ``dest`` is removed when there is one. So a directory ``write`` leaves holds exactly the
document's files and links.

Callers: ``loop.cek.assemble`` (``çek``: the clean snapshot of the commit ``pulled`` carries, its document in
``pulled``'s ``snapshot.json``) and ``loop.job``'s ``kos`` (``koş``: ``write`` from the pulled tree, before
anything runs; ``runner.kos.results`` runs the organs on that directory). A planted snapshot has no caller on the loop's path yet (its first is the
harness, P1's later rows); until then ``kind="planted"`` is reached by the tests and a session only. Not
checked, stated: what a link points at; file modes beyond the execute bit; the size of the tree (held in
memory, as ``loop.gitobj`` holds it).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from typing import Any, Callable, NamedTuple

from loop import gitobj as G
from profile import derive as D
from target import branches as B

SCHEMA = "snowball-snapshot/1"
PLACEHOLDER = b"REDACTED"
KINDS = ("clean", "planted")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
CASE_KEYS = {"property", "paths", "identifiers", "replace"}


class SnapshotError(ValueError):
    """No snapshot; ``reasons`` lists why."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__(", ".join(reasons))
        self.reasons = reasons


class Snapshot(NamedTuple):
    document: dict              # see the module docstring, "The document"
    files: dict[str, bytes]     # path -> the file's bytes, the manifest's keys
    left_out: dict[str, int]    # why -> how many files and links were left out (state_root, agent_config, ...)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot_id(files: dict[str, str], links: dict[str, str], execs: list[str]) -> str:
    """The content hash of a snapshot (see the module docstring, "The document")."""
    body = json.dumps({"exec": execs, "files": files, "links": links}, sort_keys=True, separators=(",", ":"))
    return _sha(body.encode("utf-8"))


def left_out(patterns: dict, path: str) -> str | None:
    """Why ``path`` is not in a snapshot (``state_root``, or ``profile.derive.excluded``'s answer), or None."""
    if path == B.STATE_ROOT or path.startswith(B.STATE_ROOT + "/"):
        return "state_root"
    return D.excluded(patterns, path)


def _case_ok(case: Any) -> bool:
    if not (isinstance(case, dict) and set(case) == CASE_KEYS):
        return False
    paths, ids, replace = case["paths"], case["identifiers"], case["replace"]
    return (isinstance(case["property"], str) and bool(case["property"])
            and isinstance(paths, list) and bool(paths) and all(isinstance(p, str) for p in paths)
            and len(set(paths)) == len(paths)
            and isinstance(ids, list) and all(isinstance(i, str) and i for i in ids) and len(set(ids)) == len(ids)
            and isinstance(replace, dict) and all(p in paths and isinstance(d, bytes) for p, d in replace.items()))


def _judge(cases: Any, kind: Any, max_cases: Any, files: dict[str, bytes]) -> list[str]:
    """The reasons ``cases`` cannot be the cases of a ``kind`` snapshot of ``files`` (see "The kind and the cases")."""
    if kind not in KINDS:
        return ["kind_unknown"]
    if not isinstance(cases, list):
        return ["case_invalid:0"]
    reasons = ["case_invalid:%d" % i for i, case in enumerate(cases) if not _case_ok(case)]
    if reasons:
        return reasons
    if kind == "clean":
        return ["clean_has_cases"] if cases else []
    if not cases:
        reasons.append("planted_no_cases")
    if not (isinstance(max_cases, int) and not isinstance(max_cases, bool) and max_cases > 0):
        reasons.append("max_cases_invalid")
    elif len(cases) > max_cases:
        reasons.append("cases_over_max")
    if len({case["property"] for case in cases}) > 1:
        reasons.append("cases_mixed_property")
    touched = [p for case in cases for p in case["paths"]]
    reasons += ["cases_paths_overlap:%s" % p for p in sorted({p for p in touched if touched.count(p) > 1})]
    reasons += ["case_path_missing:%s" % p for p in sorted(set(touched)) if p not in files]
    if any(i.encode("utf-8") in PLACEHOLDER for case in cases for i in case["identifiers"]):
        reasons.append("identifier_invalid")
    return reasons


def _sanitize(cases: list[dict], files: dict[str, bytes], links: dict[str, str]) -> list[str]:
    """Lay the cases' contents and replace their identifiers in ``files`` (in place); the reasons an identifier
    is left (see "Sanitizing")."""
    for case in cases:
        files.update(case["replace"])
    ids = sorted({i.encode("utf-8") for case in cases for i in case["identifiers"]}, key=lambda b: (-len(b), b))
    if not ids:
        return []
    found = re.compile(b"|".join(re.escape(i) for i in ids))
    reasons = []
    for path in sorted(files):
        files[path] = found.sub(PLACEHOLDER, files[path])
        if found.search(files[path]):
            reasons.append("sanitize_incomplete:%s" % path)
    named = sorted(p for p in list(files) + list(links)
                   if found.search(p.encode("utf-8")) or found.search(links.get(p, "").encode("utf-8")))
    return reasons + ["identifier_in_path:%s" % p for p in named]


def build(entries: list[G.Entry], cases: Any, kind: Any, target: dict | None = None,
          max_cases: Any = None) -> Snapshot:
    """The snapshot of a tree given as ``loop.gitobj`` entries (see the module docstring); ``SnapshotError``."""
    patterns = {"excluded_paths": D._target(target)[0]}
    files: dict[str, bytes] = {}
    links: dict[str, str] = {}
    execs: list[str] = []
    out: dict[str, int] = {}
    for e in entries:
        if e.kind == "dir":
            continue
        why = left_out(patterns, e.path)
        if why:
            out[why] = out.get(why, 0) + 1
        elif e.kind == "link":
            links[e.path] = e.data.decode("utf-8")
        else:
            files[e.path] = e.data
            if e.mode & 0o100:
                execs.append(e.path)
    reasons = _judge(cases, kind, max_cases, files)
    if not reasons:
        reasons = _sanitize(cases, files, links)
    if reasons:
        raise SnapshotError(reasons)
    manifest = {p: _sha(d) for p, d in sorted(files.items())}
    execs.sort()
    links = dict(sorted(links.items()))
    document = {"schema": SCHEMA, "snapshot_id": snapshot_id(manifest, links, execs), "files": manifest,
                "links": links, "exec": execs}
    return Snapshot(document, files, out)


def make(source: G.Source, base_sha: str, cases: Any, kind: Any, target: dict | None = None,
         max_cases: Any = None) -> Snapshot:
    """The ``kind`` snapshot of commit ``base_sha`` with ``cases`` (see the module docstring); ``SnapshotError``,
    ``loop.gitobj``'s ``PulledError`` for a tree it refuses."""
    return build(G.entries(source, base_sha), cases, kind, target, max_cases)


def _path_ok(path: Any) -> bool:
    return isinstance(path, str) and "\x00" not in path and not path.startswith("/") \
        and all(part not in ("", ".", "..") for part in path.split("/"))


def check(document: Any) -> None:
    """``SnapshotError`` unless ``document`` is a snapshot document with its own id (see "Writing")."""
    if not (isinstance(document, dict) and set(document) == {"schema", "snapshot_id", "files", "links", "exec"}
            and document["schema"] == SCHEMA and isinstance(document["snapshot_id"], str)):
        raise SnapshotError(["document_invalid"])
    files, links, execs = document["files"], document["links"], document["exec"]
    if not (isinstance(files, dict) and isinstance(links, dict) and isinstance(execs, list)
            and all(isinstance(h, str) and HEX64.fullmatch(h) for h in files.values())
            and all(isinstance(t, str) and t and "\x00" not in t for t in links.values())
            and all(_path_ok(p) for p in list(files) + list(links)) and not set(files) & set(links)
            and all(isinstance(p, str) and p in files for p in execs)
            and execs == sorted(set(execs))):
        raise SnapshotError(["document_invalid"])
    paths = sorted(list(files) + list(links))
    held = set(paths)
    if any("/".join(p.split("/")[:n]) in held for p in paths for n in range(1, p.count("/") + 1)):
        raise SnapshotError(["document_invalid"])
    if snapshot_id(files, links, execs) != document["snapshot_id"]:
        raise SnapshotError(["id_mismatch"])


def write(document: Any, dest: str, content: Callable[[str], "bytes | None"]) -> None:
    """Write the snapshot ``document`` names into ``dest`` from ``content`` (see "Writing"); ``SnapshotError``."""
    check(document)
    if os.path.lexists(dest):
        raise SnapshotError(["dest_exists"])
    os.makedirs(dest)
    reasons, execs = [], set(document["exec"])
    for path, want in sorted(document["files"].items()):
        data = content(path)
        if not isinstance(data, bytes):
            reasons.append("file_missing:%s" % path)
            continue
        if _sha(data) != want:
            reasons.append("hash_mismatch:%s" % path)
            continue
        full = os.path.join(dest, *path.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "xb") as fh:
            fh.write(data)
        os.chmod(full, 0o755 if path in execs else 0o644)
    if reasons:
        shutil.rmtree(dest)
        raise SnapshotError(reasons)
    for path, target in sorted(document["links"].items()):
        full = os.path.join(dest, *path.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        os.symlink(target, full)
