"""The rerun of a run-time candidate, in ``koş``, before the gate (P1 MF11; tohum/26j: "``koş`` bir çalışma-zamanı
adayını kapıdan önce yeniden koşar", tohum/26a: the referee trusts no candidate it did not run again; test 57: the
candidate runs as a ready candidate does, three lint runs, a test run, the red control, and a candidate without a
rerun does not reach the gate).

**A run-time candidate** (this module's reading; tohum/26j puts its package in ``koş``'s output tree at
``candidates/<id>/package.json`` and no page says whose tree, reports/seed-098): a file of an organ's kept output
(``runner.organ_output``) whose path there is ``candidates/<id>/package.json``, ``<id>`` one path part. Its
*package* is that file's bytes; the candidate is named here by their sha256 and by nothing else, so neither
``<id>`` nor the organ's id becomes a path of the results, and the same bytes under two ids or from two organs are
one candidate, rerun once. Every other file of an output is not read here.

**Its diff** (``diff``): the package must be UTF-8 JSON (``cli.loads``, so not nested deeper than its limit), an
object whose ``diff`` is a string that has a UTF-8 encoding; the diff is those bytes. Anything else has no diff
(``None``). The package's other keys (``finding``, ``organ_ids``, ``definition_sha256``, tohum/26a) are not read
here, present or absent: they are the gate's and the finding writer's (MF12, not built).

**The rerun** (``rerun(outputs, read, run)``; ``koş``'s side). ``outputs`` are the hashes of the outputs kept in
this run, ``read(path)`` the bytes of a regular file of the results or ``None``. Each output is read back by its
hash with ``organ_output.read``, so what is rerun is what ``yaz`` can read under the same hash; an output just kept
that is not read back raises ``organ_output.Refused`` (the caller's fault to name: nothing is rerun from bytes
that do not lead to the hash). For every package found, in the order of the package hashes,
``run(<package sha256>, <its diff or None>)`` is called once and what it returns is the candidate's entry; the
answer is ``{<package sha256>: entry}``. ``run`` is ``runner.kos``'s (``results``, "A run-time candidate" there):
a package without a diff is ``refused`` ``package_unusable`` and nothing runs for it; otherwise the diff goes
through the function a ready candidate's ``diff.patch`` goes through (``runner.kos._candidate``: a fresh copy of
the base worktree, the diff applied in place, ``lint_cmd`` three times and ``test_cmd`` once, each its own
contained run with the red control) and its three files stand under ``r/<package sha256>/`` (``RUNS``) as a
ready candidate's stand under ``c/<cid>/``. The index's ``reruns`` holds the entries.

**Before the gate** (``reran(index, package, read)``; ``yaz``'s side). The gate's three files of a candidate
(``FILES``) are handed out by this function and it hands them out only for a rerun: it returns ``{name: bytes}``
when the index's ``reruns`` has an entry under the sha256 of ``package`` whose ``verdict`` is ``verified`` and
the three files are regular files under ``r/<that hash>/``; else it raises ``NotRerun`` with one reason,
``rerun_missing`` (no ``reruns`` object, or no entry that is an object under that hash: so also a package of which
one byte differs from the one rerun), ``rerun_not_verified`` (an entry of another verdict: a diff that did not
apply, a run that told nothing, a package without a diff) or ``rerun_files_missing``, and with the entry
(``entry``, ``None`` when missing). It does not compare the files with ``hashes.json``: that is the gate's own
criterion (``gate.check``, ``artefact_hash_mismatch``), as for a ready candidate.

Caller: ``runner.kos.results`` (``rerun``), and ``loop.job``'s ``yaz`` (``yaz_reruns``, each cycle, over every
package of every organ's output it reads: ``reran``'s answer is on the target's line). Out of scope, stated: no
gate is called with these files yet and nothing decides on them (MF12, ``loop/candidates.py``, hands the candidate
to ``loop.decide``; until then ``reran`` is the only way the code hands the files out, and no test forbids a later
reader of ``r/`` that would go round it); the number of packages of an output and so of reruns of a job, bounded
by nothing here (each contained run has its own limits); who may write the results between ``koş`` and ``yaz``.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Callable

import cli
from runner import organ_output as OO

RUNS = "r"
FILES = ("cand.jsonl", "checks.json", "hashes.json")
PACKAGE = re.compile(r"candidates/[^/]+/package\.json\Z")
UNUSABLE = "package_unusable"

Read = Callable[[str], "bytes | None"]


class NotRerun(Exception):
    """A candidate whose files are not handed out; ``reasons`` says why, ``entry`` is the index's entry or ``None``."""

    def __init__(self, reason: str, entry: Any = None) -> None:
        super().__init__(reason)
        self.reasons = [reason]
        self.entry = entry


def key(package: bytes) -> str:
    """The name of the candidate whose package is ``package``: the sha256 of the bytes."""
    return hashlib.sha256(package).hexdigest()


def packages(files: dict[str, bytes]) -> dict[str, bytes]:
    """``{key: package}`` of the run-time candidates among an output's ``files`` (``organ_output.read``'s)."""
    return {key(data): data for path, data in files.items() if PACKAGE.match(path)}


def diff(package: bytes) -> bytes | None:
    """The diff of a package, or ``None`` (see the module docstring, "Its diff")."""
    try:
        got: Any = cli.loads(package.decode("utf-8"))
        text = got.get("diff") if isinstance(got, dict) else None
        return text.encode("utf-8") if isinstance(text, str) else None
    except ValueError:      # not UTF-8, not JSON, nested too deeply, a string with no UTF-8 encoding
        return None


def rerun(outputs: list[str], read: Read, run: Callable[[str, "bytes | None"], dict]) -> dict[str, dict]:
    """The index's ``reruns`` for the kept outputs ``outputs`` (see the module docstring, "The rerun")."""
    found: dict[str, bytes] = {}
    for sha in outputs:
        found.update(packages(OO.read(sha, read)))
    return {name: run(name, diff(found[name])) for name in sorted(found)}


def reran(index: Any, package: bytes, read: Read) -> dict[str, bytes]:
    """The gate's files of the candidate whose package is ``package``, or ``NotRerun`` (see "Before the gate")."""
    name = key(package)
    reruns = index.get("reruns") if isinstance(index, dict) else None
    entry = reruns.get(name) if isinstance(reruns, dict) else None
    if not isinstance(entry, dict):
        raise NotRerun("rerun_missing")
    if entry.get("verdict") != "verified":
        raise NotRerun("rerun_not_verified", entry)
    files = {f: read("/".join((RUNS, name, f))) for f in FILES}
    if any(data is None for data in files.values()):
        raise NotRerun("rerun_files_missing", entry)
    return files  # type: ignore[return-value]
