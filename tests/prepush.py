"""Say whether the tree about to be pushed is the tree a whole green run of ``snowball-tests.json`` saw.

Why: 71f64f0 was rejected (test_failed T38) for a line in a report under ``reports/``. That push changed founder
records only, and the session did not run the suite because ``referee/`` was byte-equal to an accepted tree; T38
reads ``reports/``. The rule "which paths can a test read" was a session's judgment. Here it is a comparison of
bytes: a push is checked against a stamp that only a whole green run writes. Two commands, from anywhere:

    python3 tests/prepush.py run [-j N] [--timeout S] [--stamp FILE]
    python3 tests/prepush.py check [-j N] [--timeout S] [--stamp FILE]

Rules, each bound by ``tests/test_prepush.py``:

- **run** runs every command of the manifest with ``run_like_referee`` (its rules and its out-of-scope list are
  that module's; no ``--only`` here) and prints its lines. It writes the stamp only when the summary is ok and
  ``state`` of the tree is the same after the run as before it; otherwise it removes a stamp that is there and
  says why (``tests_red``, ``tree_changed_during_run``). Exit 0 with a stamp written, 1 without.
- **The stamp** holds ``state`` of every file ``git add -A`` would commit except ``founder-ledger.jsonl`` (a
  file's sha256 and execute bit, a link's target), the ledger's length and sha256, and ``readers``: the ids of the
  commands that read the ledger's bytes from their copy during the run (``run_like_referee.run_one``'s ``read``,
  with its stated blind spots). ``readers`` is ``null`` when the run could not know them, which ``check`` reads
  as "every command"; that is so in two cases and no other: the brain had no ledger at the run (no command could
  read a file that was not there, so a ledger made afterwards has no known reader), or access times do not move
  on the temporary directory's file system. A stamp with no ledger and a ``readers`` list is not a stamp.
- **check** is ok only when: a stamp is there and readable (else ``no_green_run``); every file but the ledger is
  as stamped (else ``tree_changed:<path>`` per path added, removed or changed); git reports nothing uncommitted
  (else ``uncommitted``; what is pushed is a commit, and the comparison is of the work tree); and the ledger is
  either as stamped or the stamped bytes followed by more (else ``ledger_rewritten``). When the ledger has grown,
  the stamped ``readers`` are run again on the tree as it is, and each one not ok is ``test_failed:<id>``; they
  are not run when another reason already stands. One JSON line ``{ok, reasons, reran}``; exit 0 ok, 1 not ok.
- Exit 2 with ``{ok: false, reason}`` when the manifest, the file list or git's answers cannot be read.

The ledger is the one exception because its rows are written after the run they describe: a row cannot hold the
result of a run that has already read it.

Out of scope, stated: a green stamp is this machine's run, not the referee's verdict (``run_like_referee``'s
list); the referee's vectors, the map and the generality read are other commands (``skills/push/SKILL.md`` names
them); the stamp lives in the clone's git directory and is trusted as a file this session wrote: it is a guard
against forgetting, not against a session that edits it; nothing here stops a ``git push`` that is typed without
``check``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run_like_referee as R  # noqa: E402

LEDGER = "founder-ledger.jsonl"
STAMP = "snowball-prepush.json"
SCHEMA = "snowball-prepush/1"


def state(root: str, names: list[str]) -> dict[str, str]:
    """``names`` under ``root``, each with what a push would carry of it: ``link:<target>`` for a symbolic link,
    else the sha256 of its bytes, ``:x`` added when it has an execute bit."""
    out = {}
    for name in names:
        path = os.path.join(root, name)
        if os.path.islink(path):
            out[name] = "link:" + os.readlink(path)
        else:
            with open(path, "rb") as f:
                digest = hashlib.sha256(f.read()).hexdigest()
            out[name] = digest + (":x" if os.stat(path).st_mode & 0o111 else "")
    return out


def ledger(root: str) -> bytes | None:
    try:
        with open(os.path.join(root, LEDGER), "rb") as f:
            return f.read()
    except FileNotFoundError:
        return None


def _git(git: str, root: str, *args: str) -> bytes:
    try:
        proc = subprocess.run([git, "-C", root, *args], stdin=subprocess.DEVNULL, capture_output=True)
    except OSError:
        raise R.Unreadable("git_unavailable") from None
    if proc.returncode != 0:
        raise R.Unreadable("git_failed:%s:%d" % (args[0], proc.returncode))
    return proc.stdout


def stamp_path(root: str, git: str) -> str:
    """``snowball-prepush.json`` in the clone's git directory: outside the tree, gone with the clone."""
    return os.path.join(_git(git, root, "rev-parse", "--absolute-git-dir").decode().rstrip("\n"), STAMP)


def _others(root: str, git: str) -> dict[str, str]:
    return state(root, [n for n in R.files(root, git) if n != LEDGER])


def green(root: str, git: str, path: str, jobs: int, timeout: float, emit=print) -> dict:
    """The ``run`` command: the whole manifest; the stamp at ``path`` written or removed, as the module says."""
    tests, names = R.manifest(root), R.files(root, git)
    before, book = state(root, names), ledger(root)
    watched = (LEDGER,) if book is not None and R.atime_moves(tempfile.gettempdir()) else ()
    results: list[dict] = []

    def keep(line: str) -> None:
        results.append(json.loads(line))
        emit(line)

    summary = R.run(root, tests, names, jobs, timeout, emit=keep, watch=watched)
    reasons = [] if summary["ok"] else ["tests_red"]
    if state(root, R.files(root, git)) != before:
        reasons.append("tree_changed_during_run")
    if reasons:
        if os.path.lexists(path):
            os.remove(path)
        return {"ok": False, "reasons": reasons, "failed": summary["failed"], "stamp": None}
    # One rule for "who read the ledger is not known": nothing was watched (no ledger at the run, or a still clock).
    readers = [r["id"] for r in results if r["read"]] if watched else None
    stamp = {"schema": SCHEMA, "files": {n: v for n, v in before.items() if n != LEDGER},
             "ledger": None if book is None else {"bytes": len(book), "sha256": hashlib.sha256(book).hexdigest()},
             "readers": readers, "tests": summary["tests"]}
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(stamp, f, sort_keys=True)
    os.replace(path + ".tmp", path)
    return {"ok": True, "reasons": [], "failed": [], "stamp": path, "readers": readers}


def read_stamp(path: str) -> dict | None:
    """The stamp, or None when it is absent or not one this module wrote (each field of the form ``green`` gives it)."""
    try:
        with open(path, encoding="utf-8") as f:
            stamp = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(stamp, dict) or stamp.get("schema") != SCHEMA:
        return None
    files, book, readers = stamp.get("files"), stamp.get("ledger"), stamp.get("readers")
    if not isinstance(files, dict) or not all(isinstance(v, str) for v in files.values()):
        return None
    if book is not None and not (isinstance(book, dict) and type(book.get("bytes")) is int
                                 and isinstance(book.get("sha256"), str)):
        return None
    if readers is not None and not (isinstance(readers, list) and all(isinstance(i, str) for i in readers)):
        return None
    if book is None and readers is not None:
        return None
    return stamp


def ledger_change(stamped: dict | None, now: bytes | None) -> str:
    """``same``, ``grown`` (the stamped bytes, then more; a ledger where the stamp had none) or ``rewritten``."""
    if stamped is None:
        return "same" if now is None else "grown"
    # A shorter ledger's first bytes are the whole of it, which is not the stamped hash's content.
    if now is None or hashlib.sha256(now[:stamped["bytes"]]).hexdigest() != stamped["sha256"]:
        return "rewritten"
    return "same" if len(now) == stamped["bytes"] else "grown"


def check(root: str, git: str, path: str, jobs: int, timeout: float, emit=print) -> dict:
    """The ``check`` command, as the module says."""
    stamp = read_stamp(path)
    if stamp is None:
        return {"ok": False, "reasons": ["no_green_run"], "reran": []}
    now = _others(root, git)
    reasons = ["tree_changed:%s" % n for n in sorted(set(now) | set(stamp["files"]))
               if now.get(n) != stamp["files"].get(n)]
    if _git(git, root, "status", "--porcelain", "-z", "--untracked-files=all"):
        reasons.append("uncommitted")
    change = ledger_change(stamp["ledger"], ledger(root))
    if change == "rewritten":
        reasons.append("ledger_rewritten")
    reran: list[str] = []
    if change == "grown" and not reasons:
        tests = R.manifest(root)
        if stamp["readers"] is not None:
            tests = [t for t in tests if t["id"] in stamp["readers"]]
        summary = R.run(root, tests, R.files(root, git), jobs, timeout, emit=emit)
        reran = [t["id"] for t in tests]
        reasons += ["test_failed:%s" % i for i in summary["failed"]]
    return {"ok": not reasons, "reasons": reasons, "reran": reran}


def main(argv: list[str] | None = None, root: str = R.ROOT, git: str = "git") -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=("run", "check"))
    ap.add_argument("-j", "--jobs", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=R.TIMEOUT)
    ap.add_argument("--stamp")
    args = ap.parse_args(argv)
    try:
        path = args.stamp or stamp_path(root, git)
        result = (green if args.command == "run" else check)(root, git, path, args.jobs, args.timeout)
    except R.Unreadable as e:
        print(json.dumps({"ok": False, "reason": str(e)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
