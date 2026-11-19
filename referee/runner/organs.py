"""The organ runner: in ``koş``, an organ's entry point starts only when the organ is accepted (stage 1, P1 MF1).

Rules: asama-1/13 P1 row 1 and asama-0/09 test 51 (an organ that is not accepted has its entry point not called in
``koş``), asama-1/05 step 2 (``koş`` calls only accepted organs, through this runner), asama-1/06 item 6 and
tohum/26b (an organ is accepted by its ``definition_sha256`` at the brain SHA the bootstrap referee accepted),
tohum/08 items 2-3 (player code runs in a container without network, in a fresh directory, with a red control;
``runner.contained`` does that, this module adds no run of its own).

**A definition** is what the runner is given of one organ: ``{"entry": [str, ...], "files": {path: bytes}}`` and
nothing else. ``entry`` is the entry point, a non-empty list of non-empty strings: the command run in the
container, as written (nothing is appended). ``files`` are the organ's files: each path relative and normal
(``profile.derive.norm_path`` leaves it as written, and it is not ``.``), no path a directory on the way of
another (``a`` and ``a/b``).

**Its hash** (``definition_sha256``): the sha256, lowercase hex, of the UTF-8 bytes of the JSON object
``{"entry": [...], "files": {path: <sha256 of the file's bytes, lowercase hex>}}`` written with sorted keys, the
separators ``,`` and ``:``, non-ASCII characters escaped (``json.dumps``' default) and no newline. So the hash
changes with any byte of a file, any path, a file added or removed, and any string of the entry or their order;
the order ``files`` is given in does not enter. A definition of another shape has no hash (``OrganError``).

**The accepted** (``accepted``): ``{organ_id: definition_sha256}``, each id a non-empty string and each hash 64
lowercase hex (else ``OrganError``: unusable input, and nothing starts). The caller builds it from the organs of
the brain SHA the bootstrap referee accepted; this module compares, it does not decide what that SHA holds.

**A call** (``call``). Refused, and then no docker process starts and no directory is made, when

- ``organ_not_accepted``: ``organ_id`` is not a key of the accepted;
- ``definition_invalid``: the definition given is not of the shape above;
- ``definition_mismatch``: the definition's hash is not the accepted hash of that id (the bytes about to run are
  hashed here, at the call, not taken from a hash the caller states).

The answer is then ``{organ_id, called: false, reasons: [<the one reason>]}``. Otherwise the files are written
into a fresh directory (each a regular file, mode as ``open`` makes it: the executable bit is not part of a
definition) and ``runner.contained.run_with_red_control`` runs ``entry`` with that directory as the run's
artifacts (``/in``, read-only) and ``job``'s ``image``, ``tree`` and ``env``; the red control is ``red_cmd`` in the
same image on the same tree, without the organ's files. The staged directory is removed afterwards (the run keeps
its own copy under its ``run_root``). The answer is ``{organ_id, called: true, definition_sha256, valid, reasons,
result, red_control}``, the last four ``run_with_red_control``'s; a green red control or an invalid run is that
module's verdict, carried as it is.

Caller: none yet (``status/off_live.json``). ``koş`` (``runner.kos``, ``loop.job``'s ``kos``) gets its first organ
call with stage 1's ``lint.discover``, and ``çek`` does not carry the accepted SHA's organs in ``pulled`` yet; no
page fixes where the brain keeps an organ's entry and files (reports/seed-073). Out of scope, stated: what the
entry point does inside the container; an organ's ``state`` (tohum/26b: a ``RETIRED`` organ is not told from an
``ACTIVE`` one here); the gate's allowlist of ``accept`` rows (asama-1/06 item 6, written by ``yaz``: another
reader, of candidates, not of calls); whether the host holds the image (the caller's
``runner.contained.ensure_image``); and code under ``koş`` that would start an organ's files without this module
(nothing does today because nothing carries them; no test here forbids it).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from typing import Any

from profile import derive as D
from runner import contained as C

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
NOT_ACCEPTED = "organ_not_accepted"
INVALID = "definition_invalid"
MISMATCH = "definition_mismatch"


class OrganError(ValueError):
    """Unusable input: a definition that has no hash, or an accepted set of another shape."""


def _shape_ok(definition: Any) -> bool:
    if not (isinstance(definition, dict) and set(definition) == {"entry", "files"}):
        return False
    entry, files = definition["entry"], definition["files"]
    if not (isinstance(entry, list) and entry and all(isinstance(a, str) and a for a in entry)):
        return False
    if not (isinstance(files, dict) and all(isinstance(d, bytes) for d in files.values())):
        return False
    if not all(D.norm_path(p) == p and p != "." for p in files):
        return False
    return not any(q.startswith(p + "/") for p in files for q in files)


def definition_sha256(definition: Any) -> str:
    """The hash of a definition (see the module docstring, "Its hash"); ``OrganError`` for another shape."""
    if not _shape_ok(definition):
        raise OrganError("not an organ definition: {entry: [str, ...], files: {path: bytes}}")
    doc = {"entry": definition["entry"],
           "files": {p: hashlib.sha256(d).hexdigest() for p, d in definition["files"].items()}}
    return hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def refusal(accepted: Any, organ_id: Any, definition: Any) -> str | None:
    """Why ``organ_id``'s entry point may not start with ``definition``, or ``None`` (see "A call")."""
    if not (isinstance(accepted, dict)
            and all(isinstance(k, str) and k and isinstance(v, str) and HEX64.match(v) for k, v in accepted.items())):
        raise OrganError("accepted must map organ ids to definition hashes, 64 lowercase hex")
    if not isinstance(organ_id, str) or organ_id not in accepted:
        return NOT_ACCEPTED
    if not _shape_ok(definition):
        return INVALID
    if definition_sha256(definition) != accepted[organ_id]:
        return MISMATCH
    return None


def call(accepted: Any, organ_id: Any, definition: Any, job: dict, red_cmd: list, operating: dict,
         runner: C.Runner | None = None, base: str | None = None) -> dict:
    """Run ``organ_id``'s entry point, contained, when it is accepted; see the module docstring, "A call".
    ``job``: ``{image, tree?, env?}``."""
    reason = refusal(accepted, organ_id, definition)
    if reason:
        return {"organ_id": organ_id, "called": False, "reasons": [reason]}
    staged = tempfile.mkdtemp(prefix="snowball-organ-", dir=base)
    try:
        for path, data in definition["files"].items():
            full = os.path.join(staged, *path.split("/"))
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "xb") as fh:
                fh.write(data)
        shared = {k: job[k] for k in ("tree", "env") if k in job}
        report = C.run_with_red_control(dict(shared, image=job["image"], cmd=list(definition["entry"]), artifacts=staged),
                                        dict(shared, image=job["image"], cmd=red_cmd), operating, runner, base)
    finally:
        shutil.rmtree(staged, ignore_errors=True)
    return dict(report, organ_id=organ_id, called=True, definition_sha256=accepted[organ_id])
