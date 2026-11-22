"""An organ's output, kept in ``koş``'s results and read from them by its hash (P1 MF10; tohum/26j: "``koş`` bir
organın çıktısını koşu sonuçlarında tutar", test 56: the output stands in the results with its hash, ``yaz`` reads
it by that hash, an output with one byte changed is not read).

**What the output is** (this module's reading, reports/seed-098: tohum/26a's table names an organ's output, a
findings file for ``lint.discover``, a candidate package under ``candidates/<id>/`` for ``candidate.publish``, and
no page says how an entry point hands it over): the regular files the organ's contained run left under its
``/out``, each by its path there. Its stdout is not part of it (the index entry of ``runner.kos`` has its hash, the
bytes are not kept), nor an empty directory, nor a file's mode or times. A package an organ wrote at
``candidates/<id>/package.json`` is therefore one file of its output, under that key of the manifest; reading it
from there (26j MF12, ``loop/candidates.py``) is not built, and nothing here puts a ``candidates/`` directory in
the results.

**The store.** Under the results directory, ``o/<sha256>`` holds bytes whose sha256 is the file's name, and
nothing else is under ``o/``: one file per distinct content, whatever organ wrote it and under whatever name. An
output is one such file, its *manifest*: ``{"files": {<path under /out>: <sha256 of the file's bytes>}}`` as JSON
with sorted keys, no spaces and a final newline; the output's hash is the manifest's. So a name a container chose
is a key inside a JSON document and never a path of the results. A key is a path as a directory listing gives
it: not empty, its parts between ``/`` none of them empty, ``.`` or ``..``.

``keep(entries, read, out)`` (``koş``'s side; ``entries`` is ``runner.contained.hash_tree`` of the run's ``/out``
as the contained run took it after the container ended, ``read(path)`` the bytes of a regular file under it or
``None``, ``out`` the results directory) returns ``{sha256, reasons}``:

- an entry that is no regular file and no directory (a symlink, a fifo, a device) or that the host could not read
  gives ``output_entry:<type>`` or ``output_entry:unreadable``, sorted, once each; nothing is written;
- every file is read again and must hash to the entry's ``sha256`` (the hash the contained run reported), else
  ``output_changed``; nothing is written;
- else every file's bytes and the manifest are written and ``sha256`` is the manifest's, ``reasons`` ``[]``. An
  output without files is kept (the manifest of no files).

``sha256`` is ``None`` with any reason. Whether the run was one to keep is the caller's rule (``runner.kos``,
"The organs").

``read(sha, read)`` (``yaz``'s side; ``read(path)`` the bytes of a regular file of the results or ``None``)
returns ``{path: bytes}`` or raises ``Refused`` with its ``reasons``: ``output_hash_invalid`` (``sha`` is not 64
lowercase hex), ``output_missing:manifest``, ``output_changed:manifest`` (the bytes at ``o/<sha>`` do not hash to
``sha``), ``output_unusable`` (bytes of that hash that are no manifest: not UTF-8 JSON read with ``cli.loads``, so nested
deeper than its limit too; not the object above; a key that is no such path; or bytes other than the ones
``keep`` writes for those files, so other spacing, key order, escapes, a key twice or no final newline),
``output_missing:file`` and ``output_changed:file`` (the same two for a file the manifest names; sorted, once
each). Every byte returned is under a hash that leads back to ``sha``: one changed byte of the manifest or of any
file refuses the whole output, and nothing of it is returned.

Out of scope, stated: who may write the results between ``koş`` and ``yaz`` (the artifact's transport); any bound
on size, in ``keep`` and in ``read`` (the contained run's ``output_bytes`` bounds the sum of the files' bytes of a
valid run; the number of entries and the length of their names are bounded by nothing here, so neither is the
manifest, and ``read`` loads whatever the hashes lead to); files under ``o/`` that no manifest names (they are not
read); and what is done with an output (nothing decides on it yet: MF11 and MF12 read it).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Callable

import cli

STORE = "o"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")

Read = Callable[[str], "bytes | None"]


class Refused(Exception):
    """An output that is not read; ``reasons`` says why."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__(", ".join(reasons))
        self.reasons = reasons


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def path(sha: str) -> str:
    """Where the bytes of hash ``sha`` are, relative to the results directory."""
    return STORE + "/" + sha


def manifest(files: dict[str, str]) -> bytes:
    return (json.dumps({"files": files}, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def keep(entries: dict[str, dict], read: Read, out: str) -> dict:
    """Keep the output whose ``/out`` tree is ``entries`` under ``out`` (see the module docstring)."""
    reasons = sorted({"output_entry:" + ("unreadable" if e.get("unreadable") else e["type"])
                      for e in entries.values() if e.get("unreadable") or e["type"] not in ("file", "dir")})
    if reasons:
        return {"sha256": None, "reasons": reasons}
    blobs: dict[str, bytes] = {}
    files: dict[str, str] = {}
    for rel, entry in entries.items():
        if entry["type"] != "file":
            continue
        try:
            data = read(rel)
        except OSError:
            data = None
        if data is None or sha256(data) != entry["sha256"]:
            return {"sha256": None, "reasons": ["output_changed"]}
        blobs[entry["sha256"]] = data
        files[rel] = entry["sha256"]
    doc = manifest(files)
    blobs[sha256(doc)] = doc
    os.makedirs(os.path.join(out, STORE), exist_ok=True)
    for sha, data in blobs.items():
        try:
            with open(os.path.join(out, STORE, sha), "xb") as fh:
                fh.write(data)
        except FileExistsError:     # the same bytes, kept for another file or another organ of this run
            pass
    return {"sha256": sha256(doc), "reasons": []}


def _files(doc: bytes) -> dict[str, str]:
    """The ``files`` of manifest bytes; ``Refused`` when they are no manifest."""
    try:
        got: Any = cli.loads(doc.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise Refused(["output_unusable"]) from None
    if not (isinstance(got, dict) and isinstance(got.get("files"), dict)     # no other key: the bytes below
            and all(isinstance(v, str) and SHA256.match(v) for v in got["files"].values())
            and all(k and not {"", ".", ".."} & set(k.split("/")) for k in got["files"])
            and manifest(got["files"]) == doc):
        raise Refused(["output_unusable"])
    return got["files"]


def _stored(sha: str, read: Read, what: str) -> bytes:
    data = read(path(sha))
    if data is None:
        raise Refused(["output_missing:" + what])
    if sha256(data) != sha:
        raise Refused(["output_changed:" + what])
    return data


def read(sha: Any, read: Read) -> dict[str, bytes]:
    """The files of the output whose hash is ``sha``, each verified (see the module docstring)."""
    if not (isinstance(sha, str) and SHA256.match(sha)):
        raise Refused(["output_hash_invalid"])
    files = _files(_stored(sha, read, "manifest"))
    got: dict[str, bytes] = {}
    reasons: set[str] = set()
    for rel, file_sha in files.items():
        try:
            got[rel] = _stored(file_sha, read, "file")
        except Refused as exc:
            reasons.update(exc.reasons)
    if reasons:
        raise Refused(sorted(reasons))
    return got
