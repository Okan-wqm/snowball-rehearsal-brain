"""``koş``'s results: the files the gate reads, made from contained runs of the base tree and of each candidate's
tree (stage 0; the D3 part of the ``kos`` job that ``gate.check`` and ``activate`` read).

Rules: asama-0/01 D3 (``koş`` reads the pulled tree, the ``deps`` artifact, the recipe and the candidates and
writes result files whose hashes are taken outside the containers), asama-0/08 criteria 3, 5, 6 and 7 (the tool
three times, byte for byte; the ratchet; the affected tests, in stage 0 the unit's whole service-free test set;
the red control), tohum/08 items 2-3, tohum/01b (the gate reads results by artifact and hash), tohum/04 (zero
tests is red). It calls MF6's staging (``profile.unit_verify.stage``: the static check, the inputs' closure, the
dependencies, the install scripts; so the worktree is the one ``unit.verify`` proves), MF3 through
``unit_verify``'s contained runs (fresh directory per run, no network, red control in every run),
``runner.lint_record`` (the run record) and MF7's diff parser and ``apply``. It writes what ``gate.check
decide`` (MF8) and ``activate`` (MF18) read; it decides nothing.

**OUT** (a directory that must not exist; ``index.json`` is written last)::

    base.jsonl                          three lint runs of the base worktree, one run record per line
    c/<cid>/cand.jsonl                  three lint runs of the candidate's worktree
    c/<cid>/checks.json                 {red_control: pass|fail, tests: [{id, status: pass|fail}]}
    c/<cid>/hashes.json                 {"base.jsonl", "cand.jsonl", "checks.json"}: sha256 of the bytes written
    m/<mid>/mut.jsonl                   three lint runs of the base worktree with mutation <mid> applied
    o/<sha256>                          an organ's kept output: bytes named by their sha256 (runner.organ_output)
    candidates/<id>/package.json        a run-time candidate's package, as an organ's kept output holds it
    r/<id>/                             its rerun: the three files of c/<cid>/ (runner.candidate_rerun)
    sentinel.json                       {merge_sha, runs, verdict, red, flaky}: only when a merge is watched
    index.json                          {base: {verdict, reasons, lint_stdout_extra?, lint_failed?}, base_run_sha256,
                                         candidates: {cid: {verdict, reasons, lint_stdout_extra?, lint_failed?}},
                                         sentinel: null | {merge_sha, verdict, reasons, sha256},
                                         organs: {oid: {called, reasons, ...}},
                                         reruns: {<id>: {verdict, reasons, package_sha256, lint_stdout_extra?,
                                                         lint_failed?}},
                                         mutations: {mid: {verdict, reasons, run_sha256, lint_stdout_extra?,
                                                           lint_failed?}}}

Verdicts are ``unit_verify``'s classes: ``verified`` (the files are written and no reason holds), ``refused`` (a
reason about the tree: the candidate's or the base's), ``no_verdict`` (a run that tells nothing: a limit, an
invalid contained run, a green red control, a base that gave no run file).

**The base.** ``stage`` on the pulled tree (its last step makes the host hold the recipe's image,
``runner.contained.ensure_image``: an image the host cannot get is ``image_unavailable``, no verdict, and no
contained run starts), then ``lint_cmd`` three times, each in its own contained run. Each run
must end ``ok`` with exit 0 or 1 (``lint_failed:<n>``) and convert (``lint_output:<reason>``); any reason of a
contained run, ``red_control_green`` included, stops the base: no ratchet base comes from a sandbox that a known
bad command passed. ``base.jsonl`` holds the three records in run order even when they differ: the gate and
genesis judge that (``tool_nondeterministic``), this module records it. Bytes before the document on a lint
run's stdout (``lint_record``'s stdout rules) are read past: the base's records, its run file and its verdict
are the same as without them. They are not dropped silently: when the three runs converted and one of them had
such bytes, the base's index entry carries ``lint_stdout_extra``, each run's ``{bytes, sha256}`` in run order
(``lint_record.carried``, the rule ``unit_verify``'s report uses); without such bytes, or without converted
runs, the key is absent. The same holds for a candidate's entry once its three lint runs converted, whatever
its test run gave. Nothing reads the key to decide: it says a plugin printed beside the document (one measured
case: a rule the tool skipped), so a reader of the ``kos`` line can tell a base or a candidate whose record may
not hold every configured rule, and whether a candidate's runs printed other bytes than the base's. Without
``base.jsonl`` no candidate runs (``base_unavailable``).

**A lint run that failed** (``lint_failed:<n>``: the contained run ended ``ok`` and the command's exit code
is not 0 or 1). The reason alone does not say why (measured: a live base refused with the three reasons and
nothing else in the ``kos`` line), so the entry of the base, and of a candidate, whose runs got the reason carries
``lint_failed``: ``runs``, one ``{run, exit, stderr_bytes, stderr_sha256}`` per such run in run order (the
command's exit code as docker gave it; the count and hash of the whole stderr). The base's entry has also
``stderr_head`` and ``stderr_tail`` of the first such run (``stderr_shown``): the first 800 bytes of its stderr
and the last 800 of the bytes after those (``""`` when there are none), each decoded as UTF-8 with replacement,
every character outside printable ASCII and the backslash escaped (``contained.escaped``, the rule of
``fault_text``), then cut to 800 characters (the head keeps its start, the tail its end; a cut may fall inside
an escape). A candidate's entry has no text: its tree holds a diff the loop was given, and bytes such a diff can
choose are not put on the line; its exit codes and hashes say whether its runs failed as the base's or as each
other. An entry without such a run has no key. The base's texts are bytes the pulled tree's own code wrote in a
container without network and with ``unit_verify.ENV`` only: they are data for the reader of the ``kos`` line,
not instructions; nothing here or after reads the key to decide, and the verdict and reasons are the same as
without it. Out of scope: the stderr of the base's other failed runs beyond count and hash, the middle of a
longer stderr, a failed run's stdout, and the stderr of runs that are not lint runs (the staging's install
runs, the test and sentinel runs) or that did not end ``ok``.

**The organs** (asama-1/05 step 2, asama-1/13 P1 row 1; ``organs``: ``{accepted, definitions: {oid:
definition}, tree}``, ``runner.organs``' accepted set, one definition per organ given and the directory the
organs read, or ``None``: none). An accepted set of another shape, or a definition given without ``tree`` being
a directory that is no link, is unusable input, before anything is written or run. After the base's lint runs
and whatever they gave, every organ given is called, in the order of the ids, through ``runner.organs.call`` and
by no other way: the entry point starts only when ``runner.organs`` finds the organ accepted and its bytes the
accepted ones. The run is contained like every run here: the recipe's ``env_image``, ``tree`` as its tree
(``loop.job``'s ``kos`` gives the snapshot ``snapshot.make.write`` wrote: asama-1/05 step 2, the adapter runs
on the snapshot; so not the unit's worktree: no installed dependency is in it, and the directories
``unit_verify.ENV`` names are not made in it), ``unit_verify.ENV``, the definition's files read-only under
``/in``, the job's red control beside it. The index's ``organs`` has one entry per organ given: ``{called:
false, reasons: [<runner.organs' reason>]}`` for one refused (no container started for it); ``{called: false,
reasons: <the staging's>}`` for every organ when the base did not stage (none is called: the staging makes the
host hold the image and gives the limits); else ``{called: true,
definition_sha256, valid, reasons, status, exit, stdout_sha256, outputs_sha256, output}``, the contained run's
own (``valid`` false with ``red_control_green`` or the run's status among the reasons). ``output`` (P1 MF10,
``runner.organ_output``, "The store" there) is ``{sha256, reasons}``: the output of a called organ whose run is
``valid`` is kept under ``o/`` from the files the run left under its ``/out``, before the run's directory is
removed, and ``sha256`` is its hash, whatever the entry point's exit code; a run that is not ``valid`` keeps
nothing (``sha256`` null, ``run_invalid``), nor does an output ``organ_output.keep`` refuses (its reasons: an
entry under ``/out`` that is no regular file or directory, a file whose bytes are not the ones hashed). An organ
that was not called has no ``output`` key. ``loop.job``'s ``yaz`` reads each kept output by that hash
(``yaz_organs``); the one reader of a kept output here is the rerun of its packages ("A run-time candidate"
below, MF11), whose candidates ``loop.decide`` judges (P1 MF12); until the brain holds an organ, ``organs`` is ``{}``. The
image is a choice made here (the organ runs in the unit's toolchain image); no seed page fixes it
(reports/seed-073), nor how an adapter gets its tool when the snapshot has no installed directory
(reports/seed-074).

**A candidate** ``cid`` (a directory holding ``diff.patch``; only that file is read). ``cid`` is
``[A-Za-z0-9][A-Za-z0-9._-]{0,127}`` (else ``candidate_id_invalid``, nothing written for it). Its worktree is a
fresh copy of the base worktree (symlinks copied as symlinks), so no candidate sees another's change. The diff is
parsed by ``gate.diffguard.parse`` (``patch_unusable``); every block must change one file in place
(``patch_not_in_place``), whose path is relative and normal (``patch_path_invalid``), not under ``.snowball``, the
runs' own directory (``reserved_path``), and a regular file of the worktree with no symlink on its way
(``base_file_missing``: a file outside the recipe's ``inputs`` is not in the worktree); ``gate.diffguard.apply``
must apply it there (``patch_does_not_apply``). Then ``lint_cmd`` three times and ``test_cmd`` once (its wall
clock capped by ``test_total_s``), each in its own contained run. When every run ended ``ok``, every lint run
exited 0 or 1 and converts, the three files are written; ``red_control`` is ``pass`` when a run's red control
passed (the gate's criterion 7 rejects it; the index says ``red_control_green``). Any other reason of a contained
run (a limit, ``red_control_fault``, ``runner_fault``, ``breach:``, ``unreadable_output``) writes no file.

**A run-time candidate** (P1 MF11, tohum/26j; ``runner.candidate_rerun``, which says what one is: the package
an organ's kept output holds at ``candidates/<id>/package.json``). Every package of every output kept in this run
is rerun, in the order of the ids, through ``candidate_rerun.rerun``: the outputs are read back from ``o/`` by the
hashes the organs' entries name (one not read back is unusable input: the store this process wrote does not hold
what it hashed). An ``<id>`` two outputs hold with different bytes is ``refused`` ``package_id_twice`` and one that
is no run-time candidate id (``candidate_rerun.ID``: no dot, tohum/26p) ``candidate_id_invalid``, and nothing is written for either. Else the package is written
at ``candidates/<id>/package.json`` of ``OUT`` (tohum/26a: the package stands there in ``koş``'s output tree). A
package without a diff is ``refused`` ``package_unusable``; without ``base.jsonl`` nothing runs
(``base_unavailable``); otherwise the diff is given to the code of "A candidate" above, the same function with
``r/<id>/`` as the directory of its three files: the same refusals of a diff, the same three lint runs and one
test run, each with the red control, the same entry. The index's ``reruns`` has one entry per ``<id>``, the
function's with ``package_sha256`` (the sha256 of the package; ``null`` for an id held twice), ``{}`` when no kept
output holds a package. ``loop.job``'s ``yaz`` asks ``candidate_rerun.reran`` for each (``yaz_reruns``), and D5 reads
them through ``loop.candidates`` (P1 MF12).

**A mutation** ``mid`` (asama-1/13a: the tool runs on the tree with the mutation, in ``koş``; ``mutations``:
``{mid: diff bytes}``, ``cases.build``'s proposal as ``loop.job``'s ``kos`` reads it from ``pulled``). After the
candidates, in the order of the ids, each is treated as a candidate's diff up to its lint runs, by the same
code: ``mid`` is a candidate id (``candidate_id_invalid``), without ``base.jsonl`` nothing runs
(``base_unavailable``), the worktree is a fresh copy of the base worktree, the diff must apply in place (the
candidate's reasons above), then ``lint_cmd`` three times, each in its own contained run. No test runs: a
mutation is judged by the tool's output alone (13a). When every run ended ``ok``, exited 0 or 1 and converted and
no red control passed, ``m/<mid>/mut.jsonl`` holds the three records and the index entry its sha256
(``run_sha256``); with any reason (``red_control_green`` included: a sandbox a known bad command passed gives no
case) no file is written and ``run_sha256`` is ``null``. The entry carries ``lint_stdout_extra`` and
``lint_failed`` as a candidate's does. This module records; whether the mutation is a case is
``cases.build``'s judgement in ``yaz``.

**The tests**: ``runner.test_results.read`` of the test run's stdout and exit code: jest's ``--json`` document
when stdout ends with one, else the top-level TAP lines; a non-zero exit with no failed test listed adds
``{id: "test_cmd exit <code>", status: fail}``. The formats, their rules and what is out of scope are stated
there; a runner that prints neither gives an empty ``tests`` (the gate's ``zero_tests``: closed, not open).

**The sentinel** (D7, MF12; ``watch``, a merge SHA, given by the caller: the merge whose sentinel has not finished,
which must be the tree's own commit). With no ``watch`` the index's ``sentinel`` is ``null`` and nothing more runs.
With one, after the base's lint runs and whatever they gave, the recipe's ``affected_test_cmd`` (stage 0's affected
set is the unit's whole service-free test set, asama-0/08 item 6) runs at the staged base worktree, each run its
own contained run with the red control, its wall clock capped by ``test_total_s``; each run's ``results`` is
``test_results.read`` of its stdout and exit (the rules above). ``gate.sentinel.watch`` asks for the runs: one when the
first is green, four (run 1 and three reruns) otherwise. ``sentinel.json`` holds the merge SHA, every run used and
``gate.sentinel``'s verdict (``green``, ``flaky`` or ``red``) with its ``red`` and ``flaky`` ids; the index carries
the verdict, ``reasons`` ``[]`` and the file's sha256. No verdict (``verdict`` and ``sha256`` null, no file) when the
base did not stage (the staging's reasons), when a run tells nothing (any reason of the contained run,
``red_control_green`` included: a sandbox a known bad command passed judges no test), or when the runs are not
``gate.sentinel``'s shape (``sentinel_unusable``: one test id twice in a run); the runs stop at
the first run that tells nothing. Who reads the verdict is ``yaz``'s half of D7 (``loop.watch``: the revert on red,
the ``events``/``sentinel`` end row on green or flaky, ``loop.write_cycle``), not this module.

Caller: ``loop.job``'s ``kos`` (D3, D7), which reads the ``pulled`` artifact (``loop.pulled``) and passes the one
``deps`` artifact directory under the download (``runner.deps_npm.artifact_in``), and ``watch`` from
``brain/state``'s ledger, and ``organs`` from ``pulled``'s accepted set and carried organs with the snapshot
directory it wrote, and ``mutations`` from ``pulled``'s proposal (the command line below passes neither). Not done here, stated: the drill of the ``kos`` job (D8), and how ``yaz`` treats a
candidate without files (the gate reads a missing file as ``artefact_hash_mismatch``). The hashes are taken by this
process after every container ended, from the bytes it wrote, not from anything a container wrote.

Command line, from ``referee/``; it runs docker::

    python -m runner.kos run FILE    FILE {recipe, tree, policy, red_control: {cmd}, candidates: {cid: dir},
                                     out, deps?, target?, base?, watch?}; stdout the index, one JSON line; exit 0 base
                                     verified, 1 base refused, 2 no verdict or unusable input
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from typing import Any

from gate import diffguard
from gate import sentinel as S
from profile import derive as D
from profile import unit_verify as U
from runner import candidate_rerun as CR
from runner import contained as C
from runner import lint_record as R
from runner import organ_output as OO
from runner import organs as O
from runner import test_results as T
import cli

LINT_RUNS = 3
FAILED_KEY = "lint_failed"
STDERR_SIDE = 800       # bytes read from each end of a failed lint run's stderr, and characters shown of each
CANDIDATE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
INDEX = "index.json"
SENTINEL = "sentinel.json"
BASE = "base.jsonl"
MUTATION_RUN = "mut.jsonl"
MERGE_SHA = re.compile(r"[0-9a-f]{40}\Z")


class KosError(ValueError):
    """Unusable input (exit 2)."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _verdict(reasons: list[str]) -> dict:
    """``unit_verify``'s classes; ``base_unavailable`` tells nothing about the candidate, so it is no verdict."""
    if not reasons:
        return {"verdict": "verified", "reasons": []}
    if any(not r.startswith(U.NO_VERDICT_PREFIXES + ("base_unavailable",)) for r in reasons):
        return {"verdict": "refused", "reasons": reasons}
    return {"verdict": "no_verdict", "reasons": reasons}


def _dump(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


# ---------------------------------------------------------------- tests

def checks(stdout: bytes, exit_code: int | None, red_control_green: bool) -> bytes:
    """``checks.json``'s bytes (``gate.check``'s shape)."""
    return _dump({"red_control": "pass" if red_control_green else "fail", "tests": T.read(stdout, exit_code)})


# ---------------------------------------------------------------- runs

def stderr_shown(stderr: bytes) -> dict:
    """``{stderr_head, stderr_tail}`` of a failed run's stderr (see the module docstring, "A lint run that
    failed"): the first ``STDERR_SIDE`` bytes and the last ``STDERR_SIDE`` of the bytes after those, each decoded
    as UTF-8 with replacement, escaped by ``contained.escaped`` and cut to ``STDERR_SIDE`` characters (the head
    from its end, the tail from its start)."""
    def text(part: bytes) -> str:
        return C.escaped(part.decode("utf-8", "replace"))

    return {"stderr_head": text(stderr[:STDERR_SIDE])[:STDERR_SIDE],
            "stderr_tail": text(stderr[STDERR_SIDE:][-STDERR_SIDE:])[-STDERR_SIDE:]}


def failed(rows: list[tuple[int, Any, bytes]], shown: bool) -> dict:
    """What an index entry carries of its lint runs that got ``lint_failed:<n>``, ``rows`` being ``(n, exit,
    stderr)`` in run order: ``{FAILED_KEY: {runs: [{run, exit, stderr_bytes, stderr_sha256}]}}``, with
    ``stderr_head`` and ``stderr_tail`` of the first row's stderr (``stderr_shown``) when ``shown`` (the base);
    ``{}`` without rows."""
    if not rows:
        return {}
    return {FAILED_KEY: dict(stderr_shown(rows[0][2]) if shown else {},
                             runs=[{"run": n, "exit": code, "stderr_bytes": len(err), "stderr_sha256": sha256(err)}
                                   for n, code, err in rows])}


def _lint(recipe: dict, red: list, worktree: str, operating: dict, runner: C.Runner,
          root: str, shown: bool) -> tuple[list, list, dict]:
    """Three lint runs: ``(reasons, records, extra)``; ``records`` only when no reason but ``red_control_green``,
    ``extra`` what the index entry carries: of the runs' stdout extra with records (``lint_record.carried``), of
    the runs that got ``lint_failed:<n>`` without them (``failed``, its texts when ``shown``), else ``{}``."""
    reasons, stdouts, bad = [], [], []
    for n in range(1, LINT_RUNS + 1):
        run = U._one(recipe["lint_cmd"], red, recipe["env_image"], worktree, operating, runner, root)
        reasons += [r for r in run["reasons"] if r not in reasons]
        if run["status"] != "ok":
            continue
        if run["exit"] not in U.LINT_OK_EXITS:
            reasons.append("lint_failed:%d" % n)
            bad.append((n, run["exit"], run["stderr"] if isinstance(run["stderr"], bytes) else b""))
        stdouts.append(run["stdout"] if isinstance(run["stdout"], bytes) else b"")
    if [r for r in reasons if r != "red_control_green"] or len(stdouts) != LINT_RUNS:
        return reasons, [], failed(bad, shown)
    refused, records, extras = R.runs(stdouts, worktree)
    return reasons + refused, records, R.carried(extras)


class _NoRun(Exception):
    """A sentinel run that tells nothing; ``reasons`` are its contained run's."""

    def __init__(self, reasons: list[str]) -> None:
        super().__init__(", ".join(reasons))
        self.reasons = reasons


def _sentinel(watch: str, recipe: dict, red: list, staging: str, ctx: dict, runner: C.Runner, root: str,
              out: str) -> dict:
    """The sentinel's runs of the staged base worktree and ``sentinel.json``; its index entry (see the module
    docstring)."""
    def one() -> dict:
        test = U._one(recipe["affected_test_cmd"], red, recipe["env_image"], staging, ctx["operating"], runner, root,
                      ctx["values"]["test_total_s"])
        if test["reasons"]:  # a run whose status is not ok has its status among them (contained)
            raise _NoRun(test["reasons"])
        stdout = test["stdout"] if isinstance(test["stdout"], bytes) else b""
        return {"results": T.read(stdout, test["exit"])}

    entry = {"merge_sha": watch, "verdict": None, "reasons": [], "sha256": None}
    try:
        got = S.watch(one(), one)
    except _NoRun as exc:
        return dict(entry, reasons=exc.reasons)
    except S.Unusable:
        return dict(entry, reasons=["sentinel_unusable"])
    data = _dump({"merge_sha": watch, "runs": got["runs"], "verdict": got["verdict"], "red": got["red"],
                  "flaky": got["flaky"]})
    with open(os.path.join(out, SENTINEL), "xb") as fh:
        fh.write(data)
    return dict(entry, verdict=got["verdict"], sha256=sha256(data))


def _organ(oid: Any, organs: dict, recipe: dict, red: list, operating: dict, runner: C.Runner,
           root: str, out: str) -> dict:
    """One organ's call through ``runner.organs``, its output kept under ``out`` and its index entry (see the
    module docstring, "The organs")."""
    got = O.call(organs["accepted"], oid, organs["definitions"][oid],
                 {"image": recipe["env_image"], "tree": organs["tree"], "env": dict(U.ENV)}, red, operating, runner, root)
    if not got["called"]:
        return {"called": False, "reasons": got["reasons"]}
    main = got["result"]
    kept = {"sha256": None, "reasons": ["run_invalid"]}
    if got["valid"]:
        made = os.path.join(main["run_root"], C.MOUNT_SUBDIR["/out"])
        kept = OO.keep(main["outputs"], lambda path: D._read_regular(made, path), out)
    for run in (main, got["red_control"]):      # the output is kept and the entry carries the hashes
        shutil.rmtree(run["run_root"], ignore_errors=True)
    return {"called": True, "definition_sha256": got["definition_sha256"], "valid": got["valid"],
            "reasons": got["reasons"], "status": main["status"], "exit": main["exit"],
            "stdout_sha256": main.get("stdout_sha256"), "outputs_sha256": main["outputs_sha256"], "output": kept}


def _patch(worktree: str, diff: bytes) -> list[str]:
    """Apply every block of ``diff`` in ``worktree``; the reasons it could not (nothing is half applied then:
    the caller drops the worktree)."""
    try:
        blocks = diffguard.parse(diff.decode("utf-8", "surrogateescape"))
    except diffguard.DiffError:
        return ["patch_unusable"]
    reasons, done = [], {}
    for block in blocks:
        if block["kind"] != "modify" or block["old"] != block["new"] or block["binary"]:
            reasons.append("patch_not_in_place")
            continue
        path = block["old"]
        if not D.file_path(path):
            reasons.append("patch_path_invalid")
            continue
        if path.split("/")[0] == U.RESERVED:
            reasons.append("reserved_path")
            continue
        old = D._read_regular(worktree, path)
        if old is None:
            reasons.append("base_file_missing")
            continue
        try:
            done[path] = diffguard.apply(block, old)
        except diffguard.DiffError:
            reasons.append("patch_does_not_apply")
    if reasons:
        return sorted(set(reasons))
    for path, content in done.items():
        full = os.path.join(worktree, path)
        mode = stat.S_IMODE(os.lstat(full).st_mode)
        fd = os.open(full, os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW)
        with os.fdopen(fd, "wb") as fh:
            fh.write(content)
        os.chmod(full, mode)
    return []


def _changed(diff: bytes, recipe: dict, red: list, staging: str, ctx: dict, runner: C.Runner,
             root: str, then: Any) -> dict:
    """The index entry of one diff on the base worktree, a candidate's or a mutation's: a fresh copy of
    ``staging``, the diff applied in place, three lint runs; without records the entry is the reasons' verdict with
    what the runs carry, with them it is ``then(reasons, records, extra, worktree, work_root)``'s. The copy is
    removed at the end."""
    work_root = tempfile.mkdtemp(prefix="cand-", dir=root)
    worktree = os.path.join(work_root, "work")
    shutil.copytree(staging, worktree, symlinks=True)
    try:
        bad = _patch(worktree, diff)
        if bad:
            return _verdict(bad)
        reasons, records, extra = _lint(recipe, red, worktree, ctx["operating"], runner, work_root, False)
        if not records:
            return dict(_verdict(reasons), **extra)
        return then(reasons, records, extra, worktree, work_root)
    finally:
        shutil.rmtree(work_root, ignore_errors=True)


def _mutation(mid: str, diff: bytes, recipe: dict, red: list, staging: str, ctx: dict, runner: C.Runner,
              root: str, out: str) -> dict:
    def then(reasons: list, records: list, extra: dict, worktree: str, work_root: str) -> dict:
        if reasons:     # red_control_green: the runs converted in a sandbox that judges nothing
            return dict(_verdict(reasons), run_sha256=None, **extra)
        data = R.run_file(records)
        os.makedirs(os.path.join(out, "m", mid))
        with open(os.path.join(out, "m", mid, MUTATION_RUN), "xb") as fh:
            fh.write(data)
        return dict(_verdict([]), run_sha256=sha256(data), **extra)

    return dict({"run_sha256": None}, **_changed(diff, recipe, red, staging, ctx, runner, root, then))


def _candidate(cid: str, diff: bytes, recipe: dict, red: list, staging: str, ctx: dict, runner: C.Runner,
               root: str, out: str, base_run: bytes, kind: str = "c") -> dict:
    """The index entry of one candidate's diff and its three files under ``<out>/<kind>/<cid>/`` (see the module
    docstring, "A candidate"; ``kind`` is ``c`` for a ready candidate, ``candidate_rerun.RUNS`` for a run-time
    one)."""
    def then(reasons: list, records: list, extra: dict, worktree: str, work_root: str) -> dict:
        test = U._one(recipe["test_cmd"], red, recipe["env_image"], worktree, ctx["operating"], runner, work_root,
                      ctx["values"]["test_total_s"])
        reasons += [r for r in test["reasons"] if r not in reasons]
        if test["status"] != "ok" or [r for r in reasons if r != "red_control_green"]:
            return dict(_verdict(reasons), **extra)
        stdout = test["stdout"] if isinstance(test["stdout"], bytes) else b""
        files = {"cand.jsonl": R.run_file(records),
                 "checks.json": checks(stdout, test["exit"], "red_control_green" in reasons)}
        files["hashes.json"] = _dump({"base.jsonl": sha256(base_run), "cand.jsonl": sha256(files["cand.jsonl"]),
                                      "checks.json": sha256(files["checks.json"])})
        directory = os.path.join(out, kind, cid)
        os.makedirs(directory)
        for name, data in files.items():
            with open(os.path.join(directory, name), "xb") as fh:
                fh.write(data)
        return dict(_verdict(reasons), **extra)

    return _changed(diff, recipe, red, staging, ctx, runner, root, then)


def results(recipe: Any, tree: str, policy: Any, red_control: Any, candidates: dict[str, bytes], out: str,
            deps: str | None = None, target: Any = None, runner: C.Runner | None = None,
            base: str | None = None, watch: str | None = None, organs: Any = None,
            mutations: dict[str, bytes] | None = None) -> dict:
    """Write OUT (see the module docstring) and return the index. ``candidates``: ``{cid: diff.patch bytes}``;
    ``watch``: the merge SHA whose sentinel runs, or ``None``; ``organs``: ``{accepted, definitions, tree}`` or
    ``None``; ``mutations``: ``{mid: diff bytes}`` or ``None`` (none)."""
    runner = runner or C.docker_runner
    if watch is not None and not (isinstance(watch, str) and MERGE_SHA.match(watch)):
        raise KosError("watch must be a merge SHA, 40 lowercase hex")
    if not isinstance(candidates, dict) or not all(isinstance(k, str) and isinstance(v, bytes)
                                                   for k, v in candidates.items()):
        raise KosError("candidates must map ids to diff bytes")
    mutations = {} if mutations is None else mutations
    if not isinstance(mutations, dict) or not all(isinstance(k, str) and isinstance(v, bytes)
                                                  for k, v in mutations.items()):
        raise KosError("mutations must map ids to diff bytes")
    organs = {"accepted": {}, "definitions": {}, "tree": None} if organs is None else organs
    if not (isinstance(organs, dict) and set(organs) == {"accepted", "definitions", "tree"}
            and isinstance(organs["definitions"], dict)):
        raise KosError("organs must be {accepted, definitions: {oid: definition}, tree}")
    if organs["definitions"] and not (isinstance(organs["tree"], str) and os.path.isdir(organs["tree"])
                                      and not os.path.islink(organs["tree"])):
        raise KosError("organs.tree must be the directory the organs read")
    O.check_accepted(organs["accepted"])
    if os.path.lexists(out):
        raise KosError("OUT exists: the results directory is written fresh")
    os.makedirs(out)
    root = tempfile.mkdtemp(prefix="snowball-kos-", dir=base)
    try:
        bad, _, ctx = U.stage(recipe, tree, policy, red_control, deps, target, runner, root)
        reasons, records, extra = (bad, [], {}) if bad else _lint(recipe, red_control["cmd"], ctx["staging"],
                                                                  ctx["operating"], runner, root, True)
        index: dict[str, Any] = {"base_run_sha256": None, "candidates": {}, "sentinel": None}
        if records and not reasons:
            base_run = R.run_file(records)
            with open(os.path.join(out, BASE), "xb") as fh:
                fh.write(base_run)
            index["base_run_sha256"] = sha256(base_run)
        index["base"] = dict(_verdict(reasons), **extra)
        index["organs"] = {oid: {"called": False, "reasons": bad} if bad else
                           _organ(oid, organs, recipe, red_control["cmd"], ctx["operating"], runner, root, out)
                           for oid in sorted(organs["definitions"])}
        if watch is not None:
            index["sentinel"] = ({"merge_sha": watch, "verdict": None, "reasons": bad, "sha256": None} if bad else
                                 _sentinel(watch, recipe, red_control["cmd"], ctx["staging"], ctx, runner, root, out))
        for cid in sorted(candidates):
            if not CANDIDATE_ID.fullmatch(cid):
                got = _verdict(["candidate_id_invalid"])
            elif index["base_run_sha256"] is None:
                got = _verdict(["base_unavailable"])
            else:
                got = _candidate(cid, candidates[cid], recipe, red_control["cmd"], ctx["staging"], ctx, runner,
                                 root, out, base_run)
            index["candidates"][cid] = got

        def rerun(cid: str, package: bytes | None, diff: bytes | None) -> dict:
            if package is None:
                return _verdict([CR.TWICE])
            if not CR.ID.fullmatch(cid):
                return _verdict(["candidate_id_invalid"])
            os.makedirs(os.path.dirname(os.path.join(out, CR.path(cid))))
            with open(os.path.join(out, CR.path(cid)), "xb") as fh:
                fh.write(package)
            if diff is None:
                return _verdict([CR.UNUSABLE])
            if index["base_run_sha256"] is None:
                return _verdict(["base_unavailable"])
            return _candidate(cid, diff, recipe, red_control["cmd"], ctx["staging"], ctx, runner, root, out,
                              base_run, CR.RUNS)

        try:
            index["reruns"] = CR.rerun(sorted({e["output"]["sha256"] for e in index["organs"].values()
                                               if e.get("output", {}).get("sha256")}),
                                       lambda path: D._read_regular(out, path), rerun)
        except OO.Refused as exc:
            raise KosError("a kept output is not read back: %s" % ", ".join(exc.reasons)) from None
        index["mutations"] = {}
        for mid in sorted(mutations):
            if not CANDIDATE_ID.fullmatch(mid):
                got = dict(_verdict(["candidate_id_invalid"]), run_sha256=None)
            elif index["base_run_sha256"] is None:
                got = dict(_verdict(["base_unavailable"]), run_sha256=None)
            else:
                got = _mutation(mid, mutations[mid], recipe, red_control["cmd"], ctx["staging"], ctx, runner,
                                root, out)
            index["mutations"][mid] = got
        with open(os.path.join(out, INDEX), "xb") as fh:
            fh.write(_dump(index))
        return index
    finally:
        shutil.rmtree(root, ignore_errors=True)


# ---------------------------------------------------------------- command line

USAGE = "usage: python -m runner.kos run FILE"
# What ``results`` raises on unusable input; read by this command line and by ``loop.job``'s ``kos``.
UNUSABLE = (KosError, U.VerifyError, D.DeriveError, C.ContainmentError, ValueError, KeyError, TypeError, OSError,
            RecursionError)
EXIT = {"verified": 0, "refused": 1, "no_verdict": 2}


def _read(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 2 or argv[0] != "run":
            raise KosError(USAGE)
        req = cli.loads(_read(argv[1]).decode("utf-8"))
        if not (isinstance(req, dict) and isinstance(req.get("tree"), str) and isinstance(req.get("out"), str)
                and isinstance(req.get("candidates"), dict)
                and all(isinstance(v, str) for v in req["candidates"].values())):
            raise KosError("FILE must be {recipe, tree, policy, red_control, candidates: {cid: dir}, out, ...}")
        cands = {cid: _read(os.path.join(d, "diff.patch")) for cid, d in req["candidates"].items()}
        index = results(req.get("recipe"), req["tree"], req.get("policy"), req.get("red_control"), cands,
                        req["out"], req.get("deps"), req.get("target"), base=req.get("base"),
                        watch=req.get("watch"))
        sys.stdout.write(json.dumps(index, sort_keys=True) + "\n")
        return EXIT[index["base"]["verdict"]]
    except UNUSABLE as exc:
        cause = "unusable input: %s" % cli.cause(exc)
    sys.stdout.write(json.dumps({"ok": False, "error": cause}) + "\n")
    return 2


FAULT_LINE = {"ok": False, "error": "internal error"}


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
