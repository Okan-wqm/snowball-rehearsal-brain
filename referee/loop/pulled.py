"""The ``pulled`` artifact: what ``çek`` (D1) hands to the jobs after it, one layout written and read here (stage 0).

Rules: asama-0/01 D1 (``çek`` reads, at the SHA the bootstrap referee last accepted, ``candidates/<target>/`` and
``targets/<target>/units.json``, and the target's tree; it writes ``pulled``) and D3 (``koş`` reads ``pulled``),
tohum/26c (a ready candidate is ``candidates/<target>/<cid>/`` holding ``finding.json``, ``diff.patch`` and
``expect.json``; a ``targets[]`` entry of ``setup/summary.json``), tohum/08 item 1 and tohum/01b (a job takes
another job's output only by artifact and hash; the workflow's download checks the artifact's digest,
``digest-mismatch: error``, and this module checks each file against the manifest inside it).

**Layout** (a directory; ``pulled.json`` is written last)::

    pulled.json                 {schema: "snowball-pulled/1", target, files: {path: sha256}}
    tree.tar                    the target's tree as a tar archive (``git archive``'s format)
    units.json                  targets/<target>/units.json as read
    policy.json                 the referee repository's policy.json as read
    candidates/<cid>/finding.json, diff.patch, expect.json

``target`` is the ``targets[]`` entry of ``setup/summary.json`` for this target, as read (an object with a string
``id``; its lists are checked by ``profile.derive`` where they are used). ``<cid>`` is ``runner.kos``'s candidate id.

**Reading** (``read``; every reason that holds is listed, prefixed ``pulled:`` by the job): the manifest is a
regular file holding a JSON object with exactly those three keys (``manifest_unreadable``), the schema
(``schema_unknown``), the target (``target_invalid``); ``files`` maps each path to 64 lowercase hex
(``files_invalid``); every path is one of the layout's (``path_not_in_layout:<path>``); ``tree.tar``,
``units.json`` and ``policy.json`` are listed (``missing:<path>``) and every listed candidate has its three files
(``candidate_incomplete:<cid>``); every listed file is a regular file, no symlink on its way, with the listed
sha256 (``file_missing:<path>``, ``hash_mismatch:<path>``); no other file or directory is in the artifact
(``unlisted:<path>``). ``units.json`` and ``policy.json`` must be JSON (``json_unreadable:<path>``).

**The tree** (``extract_tree``): Python's ``tarfile`` with its ``data`` filter, into a directory that must not
exist: directories, regular files and links that stay inside it; a member whose path leaves the directory
(``..``), a link leaving it (relative or absolute target), a device or FIFO refuses the tree (``tree_unsafe``), as
does an unreadable archive (``tree_unreadable``). A leading ``/`` of a member name is dropped (the filter's rule),
so an absolute name lands inside the directory. Modes are the filter's (no setuid, setgid or sticky bit; the
execute bits kept). A refused tree may be partly written; the caller drops the directory.

Out of scope, stated: who writes ``pulled`` in the workflow (the ``cek`` job is not wired: it still stops with
``cycle_not_wired``; reading the bootstrap result, Sigstore and the target's heads are its D1 work), the target's
``brain/state`` and ``brain/integration`` heads (D1 reads them; nothing here carries them yet), and a size bound on
the archive (the artifact's own size and the job's disk and wall clock bound it).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tarfile
from typing import Any, NamedTuple

from runner import kos as K

SCHEMA = "snowball-pulled/1"
MANIFEST = "pulled.json"
TREE = "tree.tar"
UNITS = "units.json"
POLICY = "policy.json"
TOP = (TREE, UNITS, POLICY)
CANDIDATES = "candidates"
CANDIDATE_FILES = ("diff.patch", "expect.json", "finding.json")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class PulledError(ValueError):
    """The artifact is not a ``pulled`` artifact; ``reasons`` lists why."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__(", ".join(reasons))
        self.reasons = reasons


class Pulled(NamedTuple):
    target: dict
    units: Any
    policy: Any
    tree_tar: str                           # the path of tree.tar inside the artifact
    candidates: dict[str, dict[str, bytes]]  # cid -> {file name: bytes}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dump(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _candidate_of(path: str) -> str | None:
    """The cid of a candidate file's path in the layout, else None."""
    parts = path.split("/")
    if len(parts) == 3 and parts[0] == CANDIDATES and K.CANDIDATE_ID.fullmatch(parts[1]) \
            and parts[2] in CANDIDATE_FILES:
        return parts[1]
    return None


def write(out: str, target: dict, tree_tar: bytes, units: bytes, policy: bytes,
          candidates: dict[str, dict[str, bytes]]) -> dict:
    """Write the layout into ``out`` (which must not exist); returns the manifest."""
    files = {TREE: tree_tar, UNITS: units, POLICY: policy}
    for cid, content in candidates.items():
        if sorted(content) != sorted(CANDIDATE_FILES):
            raise PulledError(["candidate_incomplete:%s" % cid])
        for name, data in content.items():
            files["%s/%s/%s" % (CANDIDATES, cid, name)] = data
    bad = [p for p in files if p not in TOP and _candidate_of(p) is None]
    if bad:
        raise PulledError(["path_not_in_layout:%s" % p for p in sorted(bad)])
    os.makedirs(out)
    for path, data in sorted(files.items()):
        full = os.path.join(out, *path.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "xb") as fh:
            fh.write(data)
    manifest = {"schema": SCHEMA, "target": target, "files": {p: _sha(d) for p, d in sorted(files.items())}}
    with open(os.path.join(out, MANIFEST), "xb") as fh:
        fh.write(_dump(manifest))
    return manifest


def _regular(root: str, path: str) -> bytes | None:
    """The bytes of ``path`` under ``root`` when every component is a real directory and it is a regular file."""
    full = root
    for part in path.split("/"):
        full = os.path.join(full, part)
        try:
            st = os.lstat(full)
        except OSError:
            return None
        if stat.S_ISLNK(st.st_mode):
            return None
    if not stat.S_ISREG(st.st_mode):
        return None
    with open(full, "rb") as fh:
        return fh.read()


def _present(root: str) -> list[str]:
    """Every non-directory entry under ``root`` (relative, ``/``-separated), and every empty directory."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        prefix = "" if rel == "." else rel.replace(os.sep, "/") + "/"
        for name in list(dirnames):
            if os.path.islink(os.path.join(dirpath, name)):
                dirnames.remove(name)
                filenames.append(name)
        found += [prefix + n for n in filenames]
        if not dirnames and not filenames and prefix:
            found.append(prefix.rstrip("/") + "/")
    return found


def read(root: str) -> Pulled:
    """Check the artifact in ``root`` against its manifest; ``PulledError`` with every reason, else the content."""
    raw = _regular(root, MANIFEST) if os.path.isdir(root) else None
    try:
        manifest = json.loads(raw.decode("utf-8")) if raw is not None else None
    except (UnicodeDecodeError, ValueError, RecursionError):
        manifest = None
    if not (isinstance(manifest, dict) and set(manifest) == {"schema", "target", "files"}):
        raise PulledError(["manifest_unreadable"])
    reasons = []
    if manifest["schema"] != SCHEMA:
        reasons.append("schema_unknown")
    target = manifest["target"]
    if not (isinstance(target, dict) and isinstance(target.get("id"), str) and target["id"]):
        reasons.append("target_invalid")
    files = manifest["files"]
    if not (isinstance(files, dict) and all(isinstance(v, str) and HEX64.fullmatch(v) for v in files.values())):
        raise PulledError(reasons + ["files_invalid"])
    candidates: dict[str, dict[str, bytes]] = {}
    contents: dict[str, bytes] = {}
    for path in sorted(files):
        cid = _candidate_of(path)
        if path not in TOP and cid is None:
            reasons.append("path_not_in_layout:%s" % path)
            continue
        data = _regular(root, path)
        if data is None:
            reasons.append("file_missing:%s" % path)
        elif _sha(data) != files[path]:
            reasons.append("hash_mismatch:%s" % path)
        elif cid is None:
            contents[path] = data
        else:
            candidates.setdefault(cid, {})[path.rsplit("/", 1)[1]] = data
    reasons += ["missing:%s" % p for p in TOP if p not in files]
    listed_cids = sorted({c for c in map(_candidate_of, files) if c is not None})
    reasons += ["candidate_incomplete:%s" % c for c in listed_cids
                if sorted(p.rsplit("/", 1)[1] for p in files if _candidate_of(p) == c) != sorted(CANDIDATE_FILES)]
    reasons += ["unlisted:%s" % p for p in sorted(_present(root)) if p != MANIFEST and p not in files]
    parsed = {}
    for path in (UNITS, POLICY):
        if path in contents:
            try:
                parsed[path] = json.loads(contents[path].decode("utf-8"))
            except (UnicodeDecodeError, ValueError, RecursionError):
                reasons.append("json_unreadable:%s" % path)
    if reasons:
        raise PulledError(reasons)
    return Pulled(target, parsed[UNITS], parsed[POLICY], os.path.join(root, TREE), candidates)


def extract_tree(tar_path: str, dest: str) -> None:
    """Unpack ``tree.tar`` into ``dest`` (must not exist) with ``tarfile``'s ``data`` filter; ``PulledError``."""
    if os.path.lexists(dest):
        raise PulledError(["tree_dest_exists"])
    os.makedirs(dest)
    try:
        with tarfile.open(tar_path, "r:") as tar:
            tar.extractall(dest, filter="data")
    except tarfile.FilterError:
        raise PulledError(["tree_unsafe"]) from None
    except (tarfile.TarError, EOFError, OSError):
        raise PulledError(["tree_unreadable"]) from None
