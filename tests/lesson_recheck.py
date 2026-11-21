"""Run the ``recheck`` of every lesson in force and write what each one gave back into the founder ledger.

Why (tohum/00d E654, tohum/26g): a ``lesson`` row carries ``recheck``, "a command that runs as written from the
brain clone's root, or ``none: <reason>``"; the launcher and the referee do not run it, and until this tool no
one did. A lesson whose check no longer holds, or never ran, stayed in force unseen. A session tool, not a step
of the loop and not in ``referee/``; it runs in a session, where the capsule's ledger index is. From anywhere:

    python3 tests/lesson_recheck.py run [--only ROW_ID ...] [--timeout S] [--index FILE] [--ledger FILE]
    python3 tests/lesson_recheck.py record --snapshot SHA [--timeout S] [--ts TS] [--index FILE] [--ledger FILE]

The rules, each bound by ``tests/test_lesson_recheck.py``:

1. **Which lessons.** The lessons in force are what the capsule's index answers to ``unclosed --kinds lesson
   --tag closes`` (``/opt/founder/ledger_index.py``, the fold tohum/26g names as the reader of the closing rule),
   every page of it (``next``), oldest first. The closing rule is not copied here. An index that cannot be
   started, exits non-zero, prints something other than its JSON lines, says ``complete`` false, or shows a count
   other than the rows it gave is a fault (exit 2), never an empty list.
2. **The check's text** is ``payload.recheck`` of the ledger line the index names (``line``), read from the same
   bytes the index read (the header's ``sha256`` must be the file's; a ledger that moved between the two reads is
   a fault). A line that is not that lesson (other ``row_id``, not JSON) is a fault.
3. **What is run.** A ``recheck`` that is not a string, is empty, or starts with ``none:`` is not run: status
   ``none``. Any other is run as written: ``/bin/sh -c <recheck>``, the brain's root as the working directory,
   no stdin, this process's environment, in its own process group. Exit 0 is ``held``; any other exit is
   ``failed``; no exit within ``--timeout`` seconds (default 900) is ``timeout``, and the whole group is killed.
   One at a time, in ledger order: the checks share one work tree. Each result has ``row_id``, ``line``,
   ``status``, ``exit``, ``ms`` and the sha256 and last 300 characters of stdout and of stderr.
4. **The tree is left as it was.** ``prepush.state`` of every file ``git add -A`` would commit is taken before
   and after; a difference is ``tree_changed`` with the paths, the answer is not ok and nothing is recorded.
5. **The answer.** Each result is printed as one JSON line ``{"result": {...}}`` and flushed when its check
   ends, so a run that is cut keeps the results it printed; then one last line ``{ok, in_force, run, held,
   failed, timeout, none, tree_changed}``, printed only when every lesson has its result: output without it is
   not a whole run. ``ok`` is true only with no ``failed``, no ``timeout`` and no changed path. Exit 0 ok, 1 not
   ok, 2 fault (the last line is ``{ok: false, reason}``). ``--only`` runs the named lessons alone; a name that is not a
   lesson in force is a fault.
6. **record** runs every lesson in force (no ``--only``) and, unless the tree changed, appends one row to the
   ledger through ``ledger.founder`` (``next_row`` and ``append``, the one writer): kind ``build``, derivation
   ``tool``, trust ``observed``, a summary with the counts, and one ref per lesson run:
   ``recheck_held:<row_id>``, ``recheck_failed:<row_id>`` or ``recheck_timeout:<row_id>``; a ``none`` lesson
   gets no ref. The row is written when a check failed too: that is the record of when it did not hold. With no
   lesson run, no row is written. A ledger the writer cannot extend (not a chain) and a row it refuses are
   faults, and the file is left as it was. The answer gains ``recorded`` (the new
   ``row_id`` or null). After it, ``ledger_index.py named <row_id>`` lists a lesson's results, and ``unclosed
   --kinds lesson --tag recheck_held`` lists the lessons in force that no run has seen hold.

What a result does not say, stated: ``held`` is exit 0 of the text as written, on this machine, at this tree;
a command that cannot exit non-zero (one that ends in ``| tail -1``, or only prints) is ``held`` whatever it
shows, and a ``recheck`` written as prose is ``failed`` by the shell, not by the lesson; telling these apart is
the session's reading of the result. ``failed`` does not say which is wrong, the code or the lesson: the session
repairs the code, or closes the lesson with ``closes:<row_id>`` and the reason, or replaces it (tohum/26g). The
checks are this ledger's own text and run with the session's rights; nothing here sandboxes them. Rule 4 sees
only files git would commit: an ignored file or a file outside the brain is not seen. Nothing here stops a push
made without a run (``skills/push/SKILL.md`` names the step).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import shlex
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))

import prepush as P  # noqa: E402
import run_like_referee as R  # noqa: E402
from ledger import founder as F  # noqa: E402

INDEX = "/opt/founder/ledger_index.py"
FOLD = ("unclosed", "--kinds", "lesson", "--tag", "closes", "--order", "oldest")
NONE = "none:"
HELD, FAILED, TIMEOUT, NOT_RUN = "held", "failed", "timeout", "none"
REF = {HELD: "recheck_held:", FAILED: "recheck_failed:", TIMEOUT: "recheck_timeout:"}
TIMEOUT_S = 900.0
TAIL = 300
SHELL = "/bin/sh"


class Fault(Exception):
    """An input this tool cannot read as its rules say; the message is the reason."""


def _page(index: str, ledger: str, more: list[str]) -> tuple[dict, list[dict]]:
    argv = [sys.executable, "-I", index, *FOLD, "--ledger", ledger, *more]
    try:
        proc = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True)
    except OSError as e:
        raise Fault("index_unavailable:%s" % type(e).__name__) from None
    if proc.returncode != 0:
        raise Fault("index_exit:%d" % proc.returncode)
    try:
        lines = [json.loads(line) for line in proc.stdout.decode("utf-8").splitlines()]
    except ValueError:
        raise Fault("index_output_unreadable") from None
    if not lines or not all(isinstance(line, dict) for line in lines):
        raise Fault("index_output_unreadable")
    head, rows = lines[0], lines[1:]
    if head.get("complete") is not True or head.get("shown") != len(rows):
        raise Fault("index_incomplete")
    return head, rows


def in_force(index: str = INDEX, ledger: str = F.LEDGER) -> tuple[str, list[dict]]:
    """Rule 1: the sha256 of the ledger the index read and its lessons in force, ``{row_id, line}``, oldest first."""
    out: list[dict] = []
    more: list[str] = []
    digest = None
    while True:
        head, rows = _page(index, ledger, more)
        if digest not in (None, head.get("sha256")):
            raise Fault("ledger_moved")
        digest = head.get("sha256")
        for row in rows:
            if not isinstance(row.get("row_id"), str) or type(row.get("line")) is not int:
                raise Fault("index_row_unreadable")
            out.append({"row_id": row["row_id"], "line": row["line"]})
        if head.get("next") is None:
            break
        if not isinstance(head["next"], str) or shlex.split(head["next"]) == more:
            raise Fault("index_next_unreadable")
        more = shlex.split(head["next"])
    if not isinstance(digest, str) or head.get("count") != len(out):
        raise Fault("index_incomplete")
    return digest, out


def rechecks(data: bytes, digest: str, lessons: list[dict]) -> list[dict]:
    """Rule 2: each lesson with the ``recheck`` of its ledger line in ``data``, the bytes whose sha256 is ``digest``."""
    if hashlib.sha256(data).hexdigest() != digest:
        raise Fault("ledger_moved")
    lines = data.split(b"\n")
    out = []
    for lesson in lessons:
        try:
            if lesson["line"] < 1:
                raise IndexError
            row = json.loads(lines[lesson["line"] - 1].decode("utf-8"))
            if row["row_id"] != lesson["row_id"] or row["kind"] != F.LESSON:
                raise KeyError
            recheck = row["payload"].get("recheck")
        except (IndexError, ValueError, KeyError, TypeError, AttributeError):
            raise Fault("line_is_not_the_lesson:%s" % lesson["row_id"]) from None
        out.append({**lesson, "recheck": recheck})
    return out


def _tail(data: bytes) -> str:
    return data.decode("utf-8", "replace")[-TAIL:]


def run_one(lesson: dict, root: str, timeout: float = TIMEOUT_S) -> dict:
    """Rule 3: one lesson's result."""
    out = {"row_id": lesson["row_id"], "line": lesson["line"], "status": NOT_RUN, "exit": None, "ms": None}
    text = lesson["recheck"]
    if not isinstance(text, str) or not text or text.startswith(NONE):
        return out
    start = time.monotonic()
    proc = subprocess.Popen([SHELL, "-c", text], cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        out["status"], out["exit"] = (HELD if proc.returncode == 0 else FAILED), proc.returncode
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        stdout, stderr = proc.communicate()
        out["status"] = TIMEOUT
    out["ms"] = int((time.monotonic() - start) * 1000)
    out.update(stdout_sha256=hashlib.sha256(stdout).hexdigest(), stdout_tail=_tail(stdout),
               stderr_sha256=hashlib.sha256(stderr).hexdigest(), stderr_tail=_tail(stderr))
    return out


def _state(root: str, git: str) -> dict[str, str]:
    try:
        return P.state(root, R.files(root, git))
    except R.Unreadable as e:
        raise Fault(str(e)) from None


def run(lessons: list[dict], root: str = ROOT, timeout: float = TIMEOUT_S, git: str = "git",
        emit=lambda result: None) -> tuple[dict, list[dict]]:
    """Rules 3 to 5: every lesson of ``lessons`` (with its ``recheck``) run in order, each result given to
    ``emit`` as it ends; the answer and the results."""
    before = _state(root, git)
    results = []
    for lesson in lessons:
        results.append(run_one(lesson, root, timeout))
        emit(results[-1])
    after = _state(root, git)
    changed = sorted(n for n in set(before) | set(after) if before.get(n) != after.get(n))
    count = {s: sum(1 for r in results if r["status"] == s) for s in (HELD, FAILED, TIMEOUT, NOT_RUN)}
    return {"ok": not (count[FAILED] or count[TIMEOUT] or changed), "in_force": len(results),
            "run": len(results) - count[NOT_RUN], **count, "tree_changed": changed}, results


def refs(results: list[dict]) -> list[str]:
    """Rule 6: one ref per lesson run."""
    return [REF[r["status"]] + r["row_id"] for r in results if r["status"] in REF]


def summary(answer: dict, results: list[dict]) -> str:
    """Rule 6: the recorded row's summary."""
    bad = ["%s (%s)" % (r["row_id"], "timeout" if r["status"] == TIMEOUT else "exit %d" % r["exit"])
           for r in results if r["status"] in (FAILED, TIMEOUT)]
    return ("Lesson recheck (tests/lesson_recheck.py record): %d lessons in force, %d run as written, %d held, "
            "%d failed, %d timeout, %d with no command (none). Not holding: %s. A ref recheck_held:<row_id> is "
            "exit 0 of that lesson's recheck at this row's snapshot; recheck_failed and recheck_timeout are the "
            "other two results." % (answer["in_force"], answer["run"], answer[HELD], answer[FAILED],
                                    answer[TIMEOUT], answer[NOT_RUN], ", ".join(bad) if bad else "none"))


def record(answer: dict, results: list[dict], ledger: str, snapshot: str, ts: str, kinds: frozenset) -> str | None:
    """Rule 6: append the row for ``answer`` and return its ``row_id``; no row when the tree changed or nothing ran."""
    if answer["tree_changed"] or not answer["run"]:
        return None
    with open(ledger, "rb") as f:
        data = f.read()
    try:
        row = F.next_row(data, "build", summary(answer, results), refs(results), snapshot, ts,
                         derivation="tool", trust="observed")
        reasons = F.append(ledger, row, kinds)
    except (F.Unusable, F.chain.ChainError, UnicodeDecodeError) as e:
        raise Fault("ledger_unusable:%s" % type(e).__name__) from None
    if reasons:
        raise Fault("row_refused:%s" % ";".join(reasons))
    return row["row_id"]


def _emit(result: dict) -> None:
    print(json.dumps({"result": result}, sort_keys=True), flush=True)


def main(argv: list[str] | None = None, root: str = ROOT, git: str = "git") -> int:
    parser = argparse.ArgumentParser(description="Run the recheck of every lesson in force (see the docstring).")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "record"):
        p = sub.add_parser(name)
        p.add_argument("--timeout", type=float, default=TIMEOUT_S)
        p.add_argument("--index", default=INDEX)
        p.add_argument("--ledger", default=os.path.join(root, P.LEDGER))
        if name == "run":
            p.add_argument("--only", nargs="+", default=[])
        else:
            p.add_argument("--snapshot", required=True)
            p.add_argument("--ts", default=None)
    args = parser.parse_args(argv)
    try:
        digest, lessons = in_force(args.index, args.ledger)
        try:
            with open(args.ledger, "rb") as f:
                data = f.read()
        except OSError as e:
            raise Fault("ledger_unreadable:%s" % type(e).__name__) from None
        lessons = rechecks(data, digest, lessons)
        only = getattr(args, "only", [])
        missing = sorted(set(only) - {lesson["row_id"] for lesson in lessons})
        if missing:
            raise Fault("not_in_force:%s" % ",".join(missing))
        if only:
            lessons = [lesson for lesson in lessons if lesson["row_id"] in only]
        answer, results = run(lessons, root, args.timeout, git, _emit)
        if args.command == "record":
            ts = args.ts or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            answer["recorded"] = record(answer, results, args.ledger, args.snapshot, ts, F.spec_kinds())
    except Fault as e:
        print(json.dumps({"ok": False, "reason": str(e)}, sort_keys=True))
        return 2
    print(json.dumps(answer, sort_keys=True))
    return 0 if answer["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
