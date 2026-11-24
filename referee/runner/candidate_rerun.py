"""The rerun of a run-time candidate, in ``koş``, before the gate (P1 MF11; tohum/26j: "``koş`` bir çalışma-zamanı
adayını kapıdan önce yeniden koşar", tohum/26a: the referee trusts no candidate it did not run again; test 57: the
candidate runs as a ready candidate does, three lint runs, a test run, the red control, and a candidate without a
rerun does not reach the gate).

**A run-time candidate** ``<id>`` is the file ``candidates/<id>/package.json`` of ``koş``'s results (tohum/26a:
"``koş`` işinin çıktı ağacındaki ``candidates/<id>/package.json``'a yazılır"; tohum/26j "Paket"); its *package* is
that file's bytes. The pages do not say how a package an organ made comes to stand there (reports/seed-098,
reports/seed-099); here ``koş`` writes it: a file of an organ's kept output (``runner.organ_output``) whose path
in that output is ``candidates/<id>/package.json``, ``<id>`` one path part, is the package of candidate ``<id>``.
Every other file of an output is not read here.

**Its diff** (``diff``): the package must be UTF-8 JSON (``cli.loads``, so not nested deeper than its limit), an
object whose ``diff`` is a string that has a UTF-8 encoding; the diff is those bytes. Anything else has no diff
(``None``). The package's other keys (``finding``, ``organ_ids``, ``definition_sha256``, tohum/26a) are not read
here, present or absent: they are the gate's and the finding writer's (``loop.candidates``, P1 MF12).

**The rerun** (``rerun(outputs, read, run)``; ``koş``'s side). ``outputs`` are the hashes of the outputs kept in
this run, ``read(path)`` the bytes of a regular file of the results or ``None``. Each output is read back by its
hash with ``organ_output.read``, so a package is bytes that lead to the hash in the organ's entry; an output just
kept that is not read back raises ``organ_output.Refused`` before anything is run (the caller's fault to name).
For every ``<id>`` found (``found``), in the order of the ids, ``run(<id>, <package>, <its diff or None>)`` is
called once and what it returns, with ``package_sha256`` (the sha256 of the package), is the candidate's entry;
an ``<id>`` that two of the outputs hold with different bytes is no candidate: ``run(<id>, None, None)`` and
``package_sha256`` ``None`` (the same bytes twice are one package). The answer is ``{<id>: entry}``. ``run`` is
``runner.kos``'s (``results``, "A run-time candidate" there): it refuses an ``<id>`` held twice
(``package_id_twice``) and one that is no run-time candidate id (``ID``, below: ``candidate_id_invalid``; nothing
is written under such a name); it writes the package at ``candidates/<id>/package.json`` of the results; a package without a diff is
``refused`` ``package_unusable`` and nothing runs for it; otherwise the diff goes through the function a ready
candidate's ``diff.patch`` goes through (``runner.kos._candidate``: a fresh copy of the base worktree, the diff
applied in place, ``lint_cmd`` three times and ``test_cmd`` once, each its own contained run with the red control)
and its three files stand under ``r/<id>/`` (``RUNS``) as a ready candidate's stand under ``c/<cid>/``. The
index's ``reruns`` holds the entries.

**The id** (``ID``; tohum/26p "Çalışma-zamanı adayının yeniden koşusu" (1)): a run-time candidate's id is
``[A-Za-z0-9][A-Za-z0-9_-]{0,127}``, without a dot (the id is the name of the branch ``brain/c/<id>`` too). This
is the run-time candidate's rule alone: a ready candidate's id, a target's, an organ's and a mutation's are read
by ``runner.kos.CANDIDATE_ID``, where a dot may stand (tohum/26r:15-17 says so of the organ id).

**Before the gate** (``reran(index, cid, read)``; ``yaz``'s side; tohum/26p (5)). The package and the gate's three
files of a run-time candidate (``FILES``) are handed out by this function and it hands them out only for a rerun:
it returns ``Reran(package, files, entry)`` when ``candidates/<cid>/package.json`` is a regular file of the
results and the index's ``reruns`` has an entry (an object) under ``cid`` whose ``package_sha256`` is the sha256
of that file's bytes; ``entry`` is that entry and ``files`` is ``{name: bytes or None}`` of the three names under
``r/<cid>/`` (``None``: no regular file there). Else it raises ``NotRerun`` with one reason: ``package_missing``
(no such file, or a ``cid`` that is not one path part the host can name), ``rerun_missing`` (no ``reruns``
object, no entry that is an object under ``cid``, or an entry of other bytes: so also a package of which one byte
differs from the one rerun), or ``rerun_files_missing`` (the entry's ``verdict`` is ``verified`` and one of the
three files is absent). An entry of another verdict (a diff that did not apply, a run that told nothing, a
package without a diff) is a rerun, not a missing one: it is handed out with whatever files stand there, and the
gate's reader (``loop.decide``) rejects the candidate with the entry's reasons, as it does a ready candidate
``koş`` refused (``verified`` tells the two apart). It does not compare the files with ``hashes.json``: that is
the gate's own criterion (``gate.check``, ``artefact_hash_mismatch``), as for a ready candidate.

**The reasons of an entry** (``kos_reasons``): the one reading of an index entry ``koş`` did not verify, for a
ready candidate's entry and a rerun's alike (``loop.decide``, ``cases.build``); stated at the function.

Caller: ``runner.kos.results`` (``rerun``), and ``loop.job``'s ``yaz`` (``yaz_reruns``, each cycle, for every
name under the results' ``candidates/`` and every key of the index's ``reruns``: ``reran``'s answer is on the
target's line). ``loop.candidates.read`` (P1 MF12) takes the package and the files from ``reran`` for ``loop.decide``.
Out of scope, stated: no test forbids a later reader of ``r/`` that would go round ``reran``; the number of packages
of an output and so of reruns of a job, bounded by nothing here (each contained run has its own limits;
reports/seed-099); who may write the results between ``koş`` and ``yaz``.
"""

from __future__ import annotations

import hashlib
import os
import re
from typing import Any, Callable, NamedTuple

import cli
from runner import organ_output as OO

RUNS = "r"
FILES = ("cand.jsonl", "checks.json", "hashes.json")
PACKAGE = re.compile(r"candidates/([^/]+)/package\.json\Z")
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z")     # a run-time candidate's id ("The id")
UNUSABLE = "package_unusable"
TWICE = "package_id_twice"

Read = Callable[[str], "bytes | None"]


class NotRerun(Exception):
    """A candidate whose package and files are not handed out; ``reasons`` says why."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reasons = [reason]


class Reran(NamedTuple):
    """What ``reran`` hands out: the package, the gate's files as they stand, the index's entry of the rerun."""

    package: bytes
    files: dict[str, "bytes | None"]
    entry: dict


def verified(entry: Any) -> bool:
    """Whether an entry of the index (a rerun's, a ready candidate's) says ``koş`` verified its run."""
    return isinstance(entry, dict) and entry.get("verdict") == "verified"


def kos_reasons(entry: Any) -> list[str]:
    """The reject reasons of an entry of the index ``koş`` did not verify, each as ``kos:<reason>``: its
    ``reasons`` when that is a non-empty list of strings, else its ``verdict``; ``kos:missing`` for no entry
    (anything but an object); ``[]`` for a ``verified`` one."""
    if not isinstance(entry, dict):
        return ["kos:missing"]
    if verified(entry):
        return []
    reasons = entry.get("reasons")
    if isinstance(reasons, list) and reasons and all(isinstance(r, str) for r in reasons):
        return ["kos:%s" % r for r in reasons]
    return ["kos:%s" % entry.get("verdict")]


def key(package: bytes) -> str:
    """The sha256 of a package's bytes: what binds a rerun to the package it is of."""
    return hashlib.sha256(package).hexdigest()


def path(cid: str) -> str:
    """Where candidate ``cid``'s package stands in the results (tohum/26a)."""
    return "candidates/%s/package.json" % cid


def found(outputs: list[str], read: Read) -> dict[str, "bytes | None"]:
    """``{id: package}`` of the run-time candidates in the kept outputs ``outputs``; ``None`` for an id that two
    of them hold with different bytes."""
    got: dict[str, bytes | None] = {}
    for sha in outputs:
        for name, data in OO.read(sha, read).items():
            held = PACKAGE.match(name)
            if held:
                cid = held.group(1)
                got[cid] = data if cid not in got or got[cid] == data else None
    return got


def diff(package: bytes) -> bytes | None:
    """The diff of a package, or ``None`` (see the module docstring, "Its diff")."""
    try:
        got: Any = cli.loads(package.decode("utf-8"))
        text = got.get("diff") if isinstance(got, dict) else None
        return text.encode("utf-8") if isinstance(text, str) else None
    except ValueError:      # not UTF-8, not JSON, nested too deeply, a string with no UTF-8 encoding
        return None


def rerun(outputs: list[str], read: Read,
          run: Callable[[str, "bytes | None", "bytes | None"], dict]) -> dict[str, dict]:
    """The index's ``reruns`` for the kept outputs ``outputs`` (see the module docstring, "The rerun")."""
    packages = found(outputs, read)
    reruns = {}
    for cid in sorted(packages):
        package = packages[cid]
        if package is None:
            reruns[cid] = dict(run(cid, None, None), package_sha256=None)
        else:
            reruns[cid] = dict(run(cid, package, diff(package)), package_sha256=key(package))
    return reruns


def _one_part(cid: Any) -> bool:
    """Whether ``cid`` is one part of a path the host can name: a string, not ``.`` or ``..``, without ``/`` or
    NUL, with an encoding as a file name."""
    if not (isinstance(cid, str) and cid != "." and cid != ".." and PACKAGE.match(path(cid)) and "\x00" not in cid):
        return False
    try:
        os.fsencode(cid)
    except UnicodeError:
        return False
    return True


def reran(index: Any, cid: Any, read: Read) -> Reran:
    """Candidate ``cid``'s package, its gate's files and its rerun's entry, or ``NotRerun`` (see "Before the
    gate")."""
    package = read(path(cid)) if _one_part(cid) else None
    if package is None:
        raise NotRerun("package_missing")
    reruns = index.get("reruns") if isinstance(index, dict) else None
    entry = reruns.get(cid) if isinstance(reruns, dict) else None
    if not isinstance(entry, dict) or entry.get("package_sha256") != key(package):
        raise NotRerun("rerun_missing")
    files = {f: read("/".join((RUNS, cid, f))) for f in FILES}
    if verified(entry) and any(data is None for data in files.values()):
        raise NotRerun("rerun_files_missing")
    return Reran(package, files, entry)
