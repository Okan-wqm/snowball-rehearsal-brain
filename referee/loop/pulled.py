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
    state/heads.json            {"brain/state": commit | null, "brain/integration": commit}: the heads D1 read
    state/ledger.jsonl          brain/state's files at that head, the bytes D1 verified (``target.branches``'
    state/chain/root.jsonl        ``STATE_CHAINS``, each by its name under the state directory, ``state_name``:
                                  the commit's ``.brain/`` is not repeated; MF1's verify --previous, MF11's root)
    state/findings.jsonl        brain/state's ``STATE_REGISTERS`` at that head (``findings.write``'s files,
    state/unresolved.jsonl        tohum/26j), each as D1 verified it; absent when the head has none
    state/status.md             brain/state's ``status.md`` at that head, as read; absent when the head has none
    candidates/<cid>/finding.json, diff.patch, expect.json
    organs.json                 {organ_id: definition_sha256}: the accepted organs ("Organs" below)
    organs/<oid>/entry.json     one carried organ's entry point, a JSON document
    organs/<oid>/files/<path>   that organ's files, each under the path its definition names
    snapshot.json               the ``snapshot.make`` document of the tree's clean snapshot ("Snapshot" below)
    mutations.json              {mutation id: mutation}: ``cases.build``'s proposal ("Mutations" below)
    accept.json                 the organ entry of the accepted SHA, or ``null`` ("Entry" below)

**Organs** (asama-1/05 step 2, asama-1/13 P1 row 1: ``koş`` calls only accepted organs, through
``runner.organs``). ``organs.json`` is what ``çek`` found accepted: the ``runner.organs`` hash of each organ
definition of the brain commit it read (``loop.cek``, "Organs"); it is always listed, ``{}`` when that commit has
no organ. ``<oid>`` is one path component, ``runner.kos``'s candidate id pattern; ``<path>`` is relative and
normal (``profile.derive.norm_path`` leaves it as written). A carried organ is read as a ``runner.organs``
definition ``{entry: <entry.json parsed>, files: {path: bytes}}``. This module carries and checks bytes against
the manifest; it does not judge an organ: whether ``organs.json`` has the accepted shape, whether a carried
organ is a key of it, whether its bytes have the accepted hash and whether its entry is an entry are judged at
the call by ``runner.organs`` (``runner.kos``), so an artifact that carries an organ ``organs.json`` does not
name is read here and that organ is refused there.

**Snapshot** (asama-1/13c, tohum/26a: ``snapshot.make`` is ``çek``'s). ``snapshot.json`` is always listed and
must be JSON; ``çek`` writes there the document of the clean snapshot of the commit ``tree.tar`` was read from
(``loop.cek``). This module carries it: whether it is a snapshot document, and whether its files are the
tree's, is judged where the snapshot is written out (``snapshot.make.write``, in ``kos``), so an artifact with
another document is read here and refused there.

**Mutations** (asama-1/13a, tohum/26a: ``cases.build`` is ``çek``'s). ``mutations.json`` is always listed and
must be a JSON object (``mutations_invalid``); ``çek`` writes there what ``cases.build.propose`` proposed for the
tree (``loop.cek``), ``{}`` when it proposed nothing. This module carries it: whether an entry is a mutation is
judged where it is used (``loop.job``'s ``kos`` runs the entries that carry a diff; ``cases.build.build``, in
``yaz``, refuses one of another shape).

**Entry** (tohum/26j "İzin listesi, MF9": the entry trigger is data committed at the brain SHA the bootstrap
referee accepted). ``accept.json`` is always listed and must be ``null`` (no entry) or an object of exactly
``brain_sha`` (40 lowercase hex), ``run_id`` (a non-empty string or ``null``) and ``organ_ids`` (a list of
distinct non-empty strings), else ``accept_invalid``; ``çek`` writes there the accepted SHA, the run id of the
signed result it verified and the organ ids of that SHA's entry request (``loop.cek``). This module carries it:
the ``accept`` rows are ``gate.allowlist.rows``' (in ``yaz``), which refuses an entry it cannot write.

**Served** (tohum/29s "Hedefler": a run serves every ``targets[]`` entry, in the array's order). The uploaded
artifact is a directory holding ``served.json`` ``{schema: "snowball-served/1", targets: [id, ...]}``, the ids of the
targets ``cek`` serves this run in that order, and for each id a directory ``<id>/`` laid out as above; nothing
else. ``cek`` alone decides which targets are served (``write_served``); every later job serves exactly that list,
in that order (``served``: ``served_unreadable`` unless the file is a regular file holding exactly those two keys,
the schema, and distinct ids each a target id, ``runner.kos.CANDIDATE_ID``; ``served_missing:<id>`` for an id
without its directory, a link included; ``unlisted:<name>`` for any other entry). Each job's own artifact holds
one ``<id>/`` per served target the same way (``out/deps/<id>/``, ``out/results/<id>/``, ``out/response/<id>/``).

``target`` is the ``targets[]`` entry of ``setup/summary.json`` for this target, as read (an object with a string
``id``; its lists are checked by ``profile.derive`` where they are used). ``<cid>`` is ``runner.kos``'s candidate id.
``state/`` is what the jobs after D1 know of the cycle's state: the ledger the stage brake sums (D4) and that D6
extends, the ``status.md`` whose block D6 regenerates, the heads D6 writes on and D7 watches; a job reads it here,
never from the target.

**The genesis cycle** (``genesis``): ``brain/state`` ``null`` in ``state/heads.json`` is a target that has neither
``brain/state`` nor ``brain/integration`` yet, whose cycle is its activation (tohum/26a ``activate``: the operator's
first cycle; ``yaz`` runs ``activate``). Then ``brain/integration`` is the commit the tree was read from, the one the
activation cuts ``brain/integration`` at, both chained files are empty and there is no ``status.md``; any other
combination is ``heads_invalid`` (``write`` refuses it the same way). Every other cycle has both heads.

**Reading** (``read``; every reason that holds is listed, prefixed ``pulled:`` by the job): the manifest is a
regular file holding a JSON object with exactly those three keys (``manifest_unreadable``), the schema
(``schema_unknown``), the target (``target_invalid``); ``files`` maps each path to 64 lowercase hex
(``files_invalid``); every path is one of the layout's (``path_not_in_layout:<path>``); ``tree.tar``,
``units.json``, ``policy.json``, ``organs.json``, ``snapshot.json``, ``mutations.json``, ``accept.json`` and the ``state/`` files but ``state/status.md`` are listed (``missing:<path>``) and every listed candidate has its three files
(``candidate_incomplete:<cid>``) and every listed organ its ``entry.json`` (``organ_incomplete:<oid>``); every listed file is a regular file, no symlink on its way, with the listed
sha256 (``file_missing:<path>``, ``hash_mismatch:<path>``); no other file or directory is in the artifact
(``unlisted:<path>``). ``units.json``, ``policy.json``, ``organs.json``, ``snapshot.json``, ``mutations.json``, ``accept.json``, ``state/heads.json`` and every ``entry.json`` must be JSON
(``json_unreadable:<path>``), ``mutations.json`` an object (``mutations_invalid``), ``accept.json`` an entry or ``null`` (``accept_invalid``), and ``state/heads.json`` an object of exactly ``brain/state`` and ``brain/integration``, each 40 lowercase hex,
``brain/state`` ``null`` only in the genesis cycle's form above (``heads_invalid``). The chained files are not judged here: their reader verifies what it uses (the stage brake's
``llm_call.CostBook`` verifies the ledger as a chain).

**The tree** (``extract_tree``): Python's ``tarfile`` with its ``data`` filter, into a directory that must not
exist: directories, regular files and links that stay inside it; a member whose path leaves the directory
(``..``), a link leaving it (relative or absolute target), a device or FIFO refuses the tree (``tree_unsafe``), as
does an unreadable archive (``tree_unreadable``). A leading ``/`` of a member name is dropped (the filter's rule),
so an absolute name lands inside the directory. Modes are the filter's (no setuid, setgid or sticky bit; the
execute bits kept). A refused tree may be partly written; the caller drops the directory.

Who writes ``pulled``: ``loop.cek.assemble``, called by the ``cek`` job once D1's checks before it hold
(``loop.job``). Out of scope, stated: whether ``state/`` holds what D1 verified (the ``cek`` job's tests: this
module only carries bytes), and a size bound on the archive (the artifact's own size and the job's disk and wall
clock bound it).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tarfile
from typing import Any, NamedTuple

import cli
from profile import derive as D
from runner import kos as K
from target import branches as B

SCHEMA = "snowball-pulled/1"
MANIFEST = "pulled.json"
TREE = "tree.tar"
UNITS = "units.json"
POLICY = "policy.json"
STATE_DIR = "state"
HEADS = STATE_DIR + "/heads.json"
def _carried(path: str) -> str:
    """Where the artifact carries ``brain/state``'s file ``path``: under ``state/``, by its name under the state
    directory (``target.branches.state_name``)."""
    return "%s/%s" % (STATE_DIR, B.state_name(path))


STATE_FILES = (HEADS,) + tuple(_carried(p) for p in B.STATE_CHAINS)
STATUS = _carried(B.STATE_STATUS)
REGISTER_FILES = tuple(_carried(p) for p in B.STATE_REGISTERS)
HEAD_BRANCHES = (B.STATE, B.INTEGRATION)
ACCEPTED = "organs.json"
SNAPSHOT = "snapshot.json"
MUTATIONS = "mutations.json"
ACCEPT = "accept.json"
TOP = (TREE, UNITS, POLICY, ACCEPTED, SNAPSHOT, MUTATIONS, ACCEPT) + STATE_FILES   # always listed
LAYOUT = TOP + (STATUS,) + REGISTER_FILES    # STATUS and a register listed when the head has the file
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
CANDIDATES = "candidates"
CANDIDATE_FILES = ("diff.patch", "expect.json", "finding.json")
ORGANS = "organs"
ORGAN_ENTRY = "entry.json"
ORGAN_FILES = "files"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SERVED = "served.json"
SERVED_SCHEMA = "snowball-served/1"


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
    heads: dict[str, str]                   # brain/state and brain/integration -> commit
    state: dict[str, bytes]                 # target.branches.STATE_CHAINS path -> bytes, and each path of
                                            # STATE_REGISTERS the head has a file for
    policy_bytes: bytes                     # policy.json as carried (``policy`` is it parsed)
    status: bytes | None                    # brain/state's status.md, None when the head has none
    accepted: Any                           # organs.json parsed: {organ_id: definition_sha256}
    organs: dict[str, dict]                 # oid -> {"entry": entry.json parsed, "files": {path: bytes}}
    snapshot: Any                           # snapshot.json parsed: the snapshot.make document
    mutations: dict                         # mutations.json parsed: {mutation id: mutation} (cases.build)
    accept: dict | None = None              # accept.json parsed: {brain_sha, run_id, organ_ids}, None for no entry


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _accept_valid(doc: Any) -> bool:
    """Whether ``doc`` is ``accept.json``'s (see "Entry")."""
    if doc is None:
        return True
    if not (isinstance(doc, dict) and set(doc) == {"brain_sha", "run_id", "organ_ids"}):
        return False
    ids = doc["organ_ids"]
    return isinstance(doc["brain_sha"], str) and SHA40.fullmatch(doc["brain_sha"]) is not None \
        and (doc["run_id"] is None or (isinstance(doc["run_id"], str) and doc["run_id"] != "")) \
        and isinstance(ids, list) and all(isinstance(i, str) and i for i in ids) and len(set(ids)) == len(ids)


def _dump(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _candidate_of(path: str) -> str | None:
    """The cid of a candidate file's path in the layout, else None."""
    parts = path.split("/")
    if len(parts) == 3 and parts[0] == CANDIDATES and K.CANDIDATE_ID.fullmatch(parts[1]) \
            and parts[2] in CANDIDATE_FILES:
        return parts[1]
    return None


def _organ_of(path: str) -> tuple[str, str | None] | None:
    """``(oid, None)`` for an organ's ``entry.json`` in the layout, ``(oid, <path>)`` for one of its files, else
    None."""
    parts = path.split("/")
    if len(parts) < 3 or parts[0] != ORGANS or not K.CANDIDATE_ID.fullmatch(parts[1]):
        return None
    if parts[2:] == [ORGAN_ENTRY]:
        return parts[1], None
    rest = "/".join(parts[3:])
    if parts[2] == ORGAN_FILES and D.file_path(rest):
        return parts[1], rest
    return None


def _in_layout(path: str) -> bool:
    return path in LAYOUT or _candidate_of(path) is not None or _organ_of(path) is not None


def write(out: str, target: dict, tree_tar: bytes, units: bytes, policy: bytes,
          candidates: dict[str, dict[str, bytes]], heads: dict[str, str], state: dict[str, bytes],
          status: bytes | None, accepted: Any = None, organs: dict[str, dict] | None = None,
          snapshot: Any = None, mutations: Any = None, accept: Any = None) -> dict:
    """Write the layout into ``out`` (which must not exist); returns the manifest. ``state`` maps each path of
    ``STATE_CHAINS``, and any of ``STATE_REGISTERS`` (the ones the head has), to its bytes; ``status`` is ``status.md``'s bytes or ``None`` (not written); ``accepted`` is
    ``organs.json``'s document (``None``: ``{}``) and ``organs`` maps each carried organ's id to ``{entry, files:
    {path: bytes}}`` (``None``: none; another form, or a path that is a directory on the way of another, is
    ``organ_invalid:<oid>``, an id or a path outside the layout ``path_not_in_layout:<path>``); ``snapshot`` is
    ``snapshot.json``'s document, written as given (one json cannot write is ``snapshot_invalid``); ``mutations``
    is ``mutations.json``'s object (``None``: ``{}``; anything else that is no object json can write is
    ``mutations_invalid``); ``accept`` is ``accept.json``'s document (``None``: no entry; anything that is not
    an entry is ``accept_invalid``)."""
    if not set(B.STATE_CHAINS) <= set(state) <= set(B.STATE_CHAINS + B.STATE_REGISTERS) \
            or not all(isinstance(d, bytes) for d in state.values()) \
            or not (status is None or isinstance(status, bytes)):
        raise PulledError(["state_incomplete"])
    if not _heads_valid(heads, state, status):
        raise PulledError(["heads_invalid"])
    files = {TREE: tree_tar, UNITS: units, POLICY: policy, HEADS: _dump(heads)}
    files.update({_carried(p): d for p, d in state.items()})
    if status is not None:
        files[STATUS] = status
    for cid, content in candidates.items():
        if sorted(content) != sorted(CANDIDATE_FILES):
            raise PulledError(["candidate_incomplete:%s" % cid])
        for name, data in content.items():
            files["%s/%s/%s" % (CANDIDATES, cid, name)] = data
    try:
        files[SNAPSHOT] = _dump(snapshot)
    except (TypeError, ValueError, RecursionError):
        raise PulledError(["snapshot_invalid"]) from None
    try:
        if not isinstance({} if mutations is None else mutations, dict):
            raise TypeError("mutations")
        files[MUTATIONS] = _dump({} if mutations is None else mutations)
    except (TypeError, ValueError, RecursionError):
        raise PulledError(["mutations_invalid"]) from None
    if not _accept_valid(accept):
        raise PulledError(["accept_invalid"])
    files[ACCEPT] = _dump(accept)
    try:
        files[ACCEPTED] = _dump({} if accepted is None else accepted)
        for oid, organ in (organs or {}).items():
            if not (isinstance(oid, str) and isinstance(organ, dict) and set(organ) == {"entry", "files"}
                    and isinstance(organ["files"], dict)
                    and all(isinstance(p, str) and isinstance(d, bytes) for p, d in organ["files"].items())
                    and not any(q.startswith(p + "/") for p in organ["files"] for q in organ["files"])):
                raise PulledError(["organ_invalid:%s" % (oid,)])
            files["%s/%s/%s" % (ORGANS, oid, ORGAN_ENTRY)] = _dump(organ["entry"])
            for path, data in organ["files"].items():
                files["%s/%s/%s/%s" % (ORGANS, oid, ORGAN_FILES, path)] = data
    except PulledError:
        raise
    except (TypeError, ValueError, RecursionError):   # a document json cannot write
        raise PulledError(["organ_invalid"]) from None
    bad = [p for p in files if not _in_layout(p)]
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


def write_served(root: str, ids: list[str]) -> None:
    """``served.json`` in ``root``, the ``cek`` job's ``out/pulled`` (see "Served" above)."""
    with open(os.path.join(root, SERVED), "xb") as fh:
        fh.write(_dump({"schema": SERVED_SCHEMA, "targets": list(ids)}))


def served(root: str) -> list[str]:
    """The targets ``root`` (a downloaded ``pulled``) serves, in order (see "Served" above); ``PulledError`` with
    every reason."""
    raw = D._read_regular(root, SERVED) if os.path.isdir(root) and not os.path.islink(root) else None
    try:
        doc = cli.loads(raw.decode("utf-8")) if raw is not None else None
    except (UnicodeDecodeError, ValueError, RecursionError):
        doc = None
    if not (isinstance(doc, dict) and set(doc) == {"schema", "targets"} and doc["schema"] == SERVED_SCHEMA
            and isinstance(doc["targets"], list)
            and all(isinstance(t, str) and K.CANDIDATE_ID.fullmatch(t) for t in doc["targets"])
            and len(set(doc["targets"])) == len(doc["targets"])):
        raise PulledError(["served_unreadable"])
    ids = doc["targets"]
    entries = set(os.listdir(root)) - {SERVED}
    reasons = ["served_missing:%s" % t for t in ids
               if t not in entries or os.path.islink(os.path.join(root, t)) or not os.path.isdir(os.path.join(root, t))]
    reasons += ["unlisted:%s" % n for n in sorted(entries - set(ids))]
    if reasons:
        raise PulledError(reasons)
    return ids


def _heads_valid(heads: Any, state: dict[str, bytes], status: bytes | None) -> bool:
    """``heads`` names both heads, each 40 lowercase hex, except the genesis cycle's ``brain/state`` ``null`` with
    empty chains and no ``status.md`` (see "The genesis cycle")."""
    if not (isinstance(heads, dict) and sorted(heads) == sorted(HEAD_BRANCHES)):
        return False
    shas = [heads[B.INTEGRATION]] + ([] if heads[B.STATE] is None else [heads[B.STATE]])
    if not all(isinstance(v, str) and SHA40.fullmatch(v) for v in shas):
        return False
    return heads[B.STATE] is not None or (status is None and not any(state.values()))


def genesis(art: Pulled) -> bool:
    """Whether ``art`` is a genesis cycle's (see "The genesis cycle"): ``read`` checked its form."""
    return art.heads[B.STATE] is None


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
    raw = D._read_regular(root, MANIFEST) if os.path.isdir(root) else None
    try:
        manifest = cli.loads(raw.decode("utf-8")) if raw is not None else None
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
    organ_files: dict[str, dict[str, bytes]] = {}
    entries: dict[str, bytes] = {}
    for path in sorted(files):
        cid = _candidate_of(path)
        if not _in_layout(path):
            reasons.append("path_not_in_layout:%s" % path)
            continue
        data = D._read_regular(root, path)
        if data is None:
            reasons.append("file_missing:%s" % path)
        elif _sha(data) != files[path]:
            reasons.append("hash_mismatch:%s" % path)
        elif cid is not None:
            candidates.setdefault(cid, {})[path.rsplit("/", 1)[1]] = data
        elif _organ_of(path) is None:
            contents[path] = data
        elif _organ_of(path)[1] is None:
            entries[_organ_of(path)[0]] = data
        else:
            organ_files.setdefault(_organ_of(path)[0], {})[_organ_of(path)[1]] = data
    reasons += ["missing:%s" % p for p in TOP if p not in files]
    listed_cids = sorted({c for c in map(_candidate_of, files) if c is not None})
    reasons += ["candidate_incomplete:%s" % c for c in listed_cids
                if sorted(p.rsplit("/", 1)[1] for p in files if _candidate_of(p) == c) != sorted(CANDIDATE_FILES)]
    listed_oids = sorted({o[0] for o in map(_organ_of, files) if o is not None})
    reasons += ["organ_incomplete:%s" % o for o in listed_oids
                if "%s/%s/%s" % (ORGANS, o, ORGAN_ENTRY) not in files]
    reasons += ["unlisted:%s" % p for p in sorted(_present(root)) if p != MANIFEST and p not in files]
    parsed = {}
    contents.update({"%s/%s/%s" % (ORGANS, o, ORGAN_ENTRY): d for o, d in entries.items()})
    for path in (UNITS, POLICY, ACCEPTED, SNAPSHOT, MUTATIONS, ACCEPT, HEADS) + tuple("%s/%s/%s" % (ORGANS, o, ORGAN_ENTRY) for o in sorted(entries)):
        if path in contents:
            try:
                parsed[path] = cli.loads(contents[path].decode("utf-8"))
            except (UnicodeDecodeError, ValueError, RecursionError):
                reasons.append("json_unreadable:%s" % path)
    state = {p: contents.get(_carried(p), b"") for p in B.STATE_CHAINS}
    state.update({p: contents[_carried(p)] for p in B.STATE_REGISTERS if _carried(p) in contents})
    if HEADS in parsed and not _heads_valid(parsed[HEADS], state, contents.get(STATUS)):
        reasons.append("heads_invalid")
    if MUTATIONS in parsed and not isinstance(parsed[MUTATIONS], dict):
        reasons.append("mutations_invalid")
    if ACCEPT in parsed and not _accept_valid(parsed[ACCEPT]):
        reasons.append("accept_invalid")
    if reasons:
        raise PulledError(reasons)
    organs = {o: {"entry": parsed["%s/%s/%s" % (ORGANS, o, ORGAN_ENTRY)], "files": organ_files.get(o, {})}
              for o in listed_oids}
    return Pulled(target, parsed[UNITS], parsed[POLICY], os.path.join(root, TREE), candidates, parsed[HEADS], state,
                  contents[POLICY], contents.get(STATUS), parsed[ACCEPTED], organs, parsed[SNAPSHOT], parsed[MUTATIONS],
                  parsed[ACCEPT])


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
    except (*cli.ARCHIVE_ERRORS, OSError):
        raise PulledError(["tree_unreadable"]) from None
