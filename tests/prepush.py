"""Say whether the tree about to be pushed is the tree a whole green run of ``snowball-tests.json`` saw.

Why: 71f64f0 was rejected (test_failed T38) for a line in a report under ``reports/``. That push changed founder
records only, and the session did not run the suite because ``referee/`` was byte-equal to an accepted tree; T38
reads ``reports/``. The rule "which paths can a test read" was a session's judgment. Here it is a comparison of
bytes: a push is checked against a stamp that only a whole green run writes. Two commands, from anywhere:

    python3 tests/prepush.py run [-j N] [--timeout S] [--stamp FILE]
    python3 tests/prepush.py check [-j N] [--timeout S] [--stamp FILE] [--result FILE]

and a third for the work between two whole runs, which stamps nothing and is no part of that comparison:

    python3 tests/prepush.py quick [--since REV] [--plan] [-j N] [--timeout S] [--stamp FILE]

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
  are not run when another reason already stands. **The push's size**: when the referee's result is there
  (``--result``, default ``push_size.RESULT``; a brain no verdict has judged has no base to measure from, and
  ``size`` is ``null``; it is ``null`` too, and nothing is measured, when there is no stamp, and when the base or
  the diff cannot be read), ``push_size.measure`` from the result's last accepted SHA to ``HEAD`` with the result's
  limit is ``size``, and a band that is not ``fits`` is the reason ``push_size:<band>``, a base or a diff that
  cannot be read ``push_size:<its reason>`` (the measure, the bands and what ``fits`` does not promise are that
  module's). One JSON line ``{ok, reasons, reran, size}``; exit 0 ok, 1 not ok.
- **quick** runs the parts of the manifest whose test files reach a changed path, and no other part.
  *Changed paths*: with ``--since REV``, the paths ``mutate.touched`` names (git's diff of REV against the work
  tree and git's untracked files; a REV git cannot read is exit 2, ``rev_unreadable``, and so is any other
  failure of git there; no git to ask is ``git_unavailable``); without it, every path whose ``state`` differs
  from the stamp's (added, removed, changed), and ``no_green_run`` when there is no stamp. The ledger is never a changed path. *Parts*: a command made only of the steps ``cd referee`` (from the
  root), ``cd ..`` (from ``referee``) and ``python -m unittest discover -s tests -p '<pattern>'`` (no quote or
  backslash in the pattern), joined by `` && ``, is one part per discover step, in the directory the steps
  before it reached, with the id ``<test id>:<that directory's tests/><pattern>``; a step named twice in one
  directory is one part. A part is selected when a changed path is in the import closure of the test files its
  pattern names (``mutate.named`` over ``mutate.test_files``, ``mutate.closure_of``: the rules and import spaces
  ``mutate.py --touched`` reads by, one reader), those files included, or when its pattern names no file. A
  command of any other form is run whole every time, under its own id. The selected run as ``run``'s commands do
  (``run_like_referee``), a part by its step alone from its directory; each not ok is ``test_failed:<id>``.
  ``--plan`` selects and runs nothing. One JSON line ``{ok, reasons, changed, parts, selected, unseen, ran}``:
  ``changed`` and ``parts`` are counts, ``unseen`` the changed paths in no part's closure, ``ran`` whether
  anything was run. Exit 0 ok, 1 not ok. It never writes or removes the stamp.
- Exit 2 with ``{ok: false, reason}`` when the manifest, the file list or git's answers cannot be read.

The ledger is the one exception because its rows are written after the run they describe: a row cannot hold the
result of a run that has already read it.

What a green ``quick`` does not say, stated: that a whole run is green. It follows import statements only, so
it does not see what ``mutate.py --touched`` does not see (a changed file that is not Python: a fixture, a JSON,
a page, a report, the manifest; a file a test opens by path, starts as a subprocess or imports by a built name; the
imports of a file that does not parse), nor a test that reads the ledger, nor what a part's earlier steps would
have left for it. ``unseen`` names the changed paths it followed to no part, as a list to read, not as a verdict:
a changed path that one part reaches by import and another only by path is not in it. The whole ``run`` before
the push is the check; ``quick`` only orders the work before it.

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
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import push_size as PS  # noqa: E402  (the size of the diff the rival is handed: one measure)
import run_like_referee as R  # noqa: E402

sys.path.insert(0, os.path.join(R.ROOT, "referee", "tests"))

import mutate as M  # noqa: E402  (what changed since a REV, a test file's import closure: one reader of each)

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


def size(root: str, git: str, result: str | None) -> tuple[dict | None, list[str]]:
    """``(size, reasons)`` of the push from the last accepted SHA of the result at ``result`` to ``HEAD`` (module
    docstring, ``check``); ``(None, [])`` when no result is named or none is there."""
    if result is None or not os.path.lexists(result):
        return None, []
    try:
        measured = PS.measure(root, PS.base_of(result), "HEAD", git=git, result=result)
    except PS.Unreadable as e:
        return None, ["push_size:%s" % e]
    return measured, [] if measured["ok"] else ["push_size:%s" % measured["band"]]


def check(root: str, git: str, path: str, jobs: int, timeout: float, emit=print, result: str | None = None) -> dict:
    """The ``check`` command, as the module says; ``result`` is ``--result`` (``None``: no size is measured)."""
    stamp = read_stamp(path)
    if stamp is None:
        return {"ok": False, "reasons": ["no_green_run"], "reran": [], "size": None}
    now = _others(root, git)
    reasons = ["tree_changed:%s" % n for n in sorted(set(now) | set(stamp["files"]))
               if now.get(n) != stamp["files"].get(n)]
    if _git(git, root, "status", "--porcelain", "-z", "--untracked-files=all"):
        reasons.append("uncommitted")
    change = ledger_change(stamp["ledger"], ledger(root))
    if change == "rewritten":
        reasons.append("ledger_rewritten")
    measured, large = size(root, git, result)
    reasons += large
    reran: list[str] = []
    if change == "grown" and not reasons:
        tests = R.manifest(root)
        if stamp["readers"] is not None:
            tests = [t for t in tests if t["id"] in stamp["readers"]]
        summary = R.run(root, tests, R.files(root, git), jobs, timeout, emit=emit)
        reran = [t["id"] for t in tests]
        reasons += ["test_failed:%s" % i for i in summary["failed"]]
    return {"ok": not reasons, "reasons": reasons, "reran": reran, "size": measured}


DISCOVER = re.compile(r"python -m unittest discover -s tests -p '([^'\\]+)'")
CD = {(".", "cd referee"): "referee", ("referee", "cd .."): "."}  # (directory, step) -> the directory after it


def parts(test: dict) -> list[dict] | None:
    """A manifest command's parts (module docstring, ``quick``): ``{id, cmd, root, pattern}`` per discover step,
    a step named twice in one directory once; ``None`` for a command that is not of the grammar."""
    out, cwd = {}, "."
    for step in test["cmd"].split(" && "):
        found = DISCOVER.fullmatch(step)
        if found:
            name = ("" if cwd == "." else cwd + "/") + "tests/" + found.group(1)
            out.setdefault(name, {"id": "%s:%s" % (test["id"], name), "root": cwd, "pattern": found.group(1),
                                  "cmd": ("" if cwd == "." else "cd %s && " % cwd) + step})
        elif (cwd, step) in CD:
            cwd = CD[(cwd, step)]
        else:
            return None
    return list(out.values()) or None


def changed_since(root: str, git: str, path: str, since: str | None) -> set[str] | None:
    """The paths ``quick`` takes as changed (module docstring), the ledger never among them; ``None`` when there
    is neither a ``since`` nor a stamp."""
    if since is not None:
        try:
            return M.touched(root, since, git) - {LEDGER}
        except ValueError:
            raise R.Unreadable("rev_unreadable") from None
        except OSError:
            raise R.Unreadable("git_unavailable") from None
    stamp = read_stamp(path)
    if stamp is None:
        return None
    now = _others(root, git)
    return {n for n in set(now) | set(stamp["files"]) if now.get(n) != stamp["files"].get(n)}


def quick(root: str, git: str, path: str, jobs: int, timeout: float, emit=print, since: str | None = None,
          plan: bool = False) -> dict:
    """The ``quick`` command, as the module says; it reads the stamp at ``path`` and never writes or removes it."""
    changed = changed_since(root, git, path, since)
    if changed is None:
        return {"ok": False, "reasons": ["no_green_run"], "changed": None, "parts": None, "selected": [],
                "unseen": [], "ran": False}
    spaces: dict[str, tuple] = {}
    selected, seen, total = [], set(), 0
    for test in R.manifest(root):
        found = parts(test)
        if found is None:  # not of the grammar: what it reads is not known, so it runs whole, every time
            total += 1
            selected.append(test)
            continue
        for part in found:
            total += 1
            if part["root"] not in spaces:
                spaces[part["root"]] = (M.closure_of(root, changed, M.ROOTS[part["root"]]),
                                        M.test_files(root, part["root"]))
            closure, files = spaces[part["root"]]
            named = M.named(files, part["pattern"])
            reached = closure(named) & changed
            seen |= reached
            if reached or not named:  # no file of that name: the step is red as written, and is shown so
                selected.append({"id": part["id"], "cmd": part["cmd"]})
    result = {"ok": True, "reasons": [], "changed": len(changed), "parts": total,
              "selected": [t["id"] for t in selected], "unseen": sorted(changed - seen), "ran": False}
    if plan or not selected:
        return result
    summary = R.run(root, selected, R.files(root, git), jobs, timeout, emit=emit)
    reasons = ["test_failed:%s" % i for i in summary["failed"]]
    return result | {"ok": not reasons, "reasons": reasons, "ran": True}


def main(argv: list[str] | None = None, root: str = R.ROOT, git: str = "git") -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=("run", "check", "quick"))
    ap.add_argument("-j", "--jobs", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=R.TIMEOUT)
    ap.add_argument("--stamp")
    ap.add_argument("--since", metavar="REV", help="quick: the paths changed since REV, not since the stamp")
    ap.add_argument("--plan", action="store_true", help="quick: select and run nothing")
    ap.add_argument("--result", default=PS.RESULT, help="check: the referee's result the push's size is read by")
    args = ap.parse_args(argv)
    if args.command != "quick" and (args.since is not None or args.plan):
        ap.error("--since and --plan are quick's")
    try:
        path = args.stamp or stamp_path(root, git)
        if args.command == "quick":
            result = quick(root, git, path, args.jobs, args.timeout, since=args.since, plan=args.plan)
        elif args.command == "run":
            result = green(root, git, path, args.jobs, args.timeout)
        else:
            result = check(root, git, path, args.jobs, args.timeout, result=args.result)
    except R.Unreadable as e:
        print(json.dumps({"ok": False, "reason": str(e)}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
