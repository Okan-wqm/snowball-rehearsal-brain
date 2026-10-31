"""Run ``snowball-tests.json``'s commands the way the referee's ``koş`` runs them, as near as a session can.

Why: 057ad34 was rejected (test_failed T14) for a difference of environment only: the tests passed here, where git
is installed, and failed in the referee's sandbox, which has none (founder ledger f396). This runner makes that
class visible before a push. Run from anywhere: ``python3 tests/run_like_referee.py [-j N] [--timeout S]
[--only ID ...]``.

What it does, each rule bound by ``tests/test_run_like_referee.py``:

- **The tree is what a commit would hold.** The files are git's list of what ``git add -A`` would commit
  (``git -C <root> ls-files -z --cached --others --exclude-standard``; a listed file that is gone from the work
  tree is not copied), so an ignored file (``__pycache__``, a local fixture) is not there, as in the referee's
  checkout. A symbolic link is copied as a link. This is the one step that needs git: it reads this clone.
- **Each command gets its own copy, with a checkout's modes** (``0644``, ``0755`` for a file with an execute
  bit, ``0755`` for a directory), like the referee's checkout, so what a test copies out of the tree is writable,
  as there.
- **A write to the tree is a failure, found after the fact** (tohum/29b ``koş``: ``--read-only``, where it fails
  at once). Without root this runner cannot make the tree read-only and keep a checkout's modes (the referee's
  files belong to another user; here they are this user's), so it compares the copy after the command with the
  copy before it: every path added, removed or changed (content, kind, link target, execute bit) is listed in
  ``wrote`` and the command is not ok. One exception, python's own: a path under a directory named
  ``__pycache__`` is not compared, because python writes its bytecode cache there and, on a read-only tree,
  skips that write without an error (any python the command starts, whatever its environment).
- **PATH holds only python**: a directory holding ``python`` and ``python3``, links to this interpreter. The
  command runs under ``/bin/sh -c`` (the shell is found by its path, not by PATH), from the copy's root (tohum/26c:
  ``cmd`` runs from the repository root), stdin ``/dev/null``.
- **The environment is only** ``PATH``, ``HOME=/nonexistent`` (no home to read or write), ``TMPDIR`` (a new
  directory per command) and ``LANG=C.UTF-8``; nothing of this session's environment passes.
- **A time limit per command** (``--timeout``, default 1800 s, the referee's bound for a whole push): a command
  that exceeds it is killed and is ``timed_out``, not ok.
- One JSON line per command (``id``, ``exit``, ``ok``, ``timed_out``, ``wrote``, ``duration_ms``, ``tail``: the
  last 600 characters of stdout and stderr together), then one summary line (``ok``, ``tests``, ``failed``,
  ``network``). Exit 0 when every command exited 0, 1 when one did not, 2 when the manifest or the file list
  cannot be read. The copy and every ``TMPDIR`` are removed after the run.

Out of scope, stated (the referee does these; this runner does not): no network isolation (``--network none``
needs a namespace this session cannot make: ``unshare -rn`` is refused here), so the summary says ``network:
not_isolated`` and a test reaching the network can still pass here; no ``--cap-drop ALL`` and no ``--user 65534``;
a write outside the tree (``/tmp`` aside, the referee's root file system is read-only) is not seen;
the referee's image (its python version, its ``/bin/sh``, its installed programs other than git) is not this
machine's. A green run here is necessary evidence, not the referee's verdict.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = "/nonexistent"
SHELL = "/bin/sh"
TAIL = 600
TIMEOUT = 1800.0
PYCACHE = "__pycache__"
LS_FILES = ("ls-files", "-z", "--cached", "--others", "--exclude-standard")


class Unreadable(Exception):
    """The manifest or the file list cannot be read; the message is the reason."""


def manifest(root: str, only: list[str] | None = None) -> list[dict]:
    """``snowball-tests.json``'s tests (tohum/26c: ``{tests: [{id, cmd, stage}]}``), those named in ``only`` when
    given; an id of ``only`` that is not there is unreadable, not skipped."""
    try:
        with open(os.path.join(root, "snowball-tests.json"), encoding="utf-8") as f:
            tests = json.load(f)["tests"]
        tests = [{"id": t["id"], "cmd": t["cmd"]} for t in tests]
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise Unreadable("manifest_unreadable:%s" % type(e).__name__) from None
    if only:
        missing = sorted(set(only) - {t["id"] for t in tests})
        if missing:
            raise Unreadable("test_unknown:%s" % ",".join(missing))
        tests = [t for t in tests if t["id"] in only]
    return tests


def files(root: str, git: str = "git") -> list[str]:
    """What ``git add -A`` would commit: tracked and untracked files git does not ignore, present in the work tree."""
    try:
        proc = subprocess.run([git, "-C", root, *LS_FILES], stdin=subprocess.DEVNULL, capture_output=True)
    except OSError:
        raise Unreadable("git_unavailable") from None
    if proc.returncode != 0:
        raise Unreadable("ls_files_failed:%d" % proc.returncode)
    names = sorted({n for n in proc.stdout.decode("utf-8", "surrogateescape").split("\0") if n})
    return [n for n in names if os.path.lexists(os.path.join(root, n))]


def stage(root: str, names: list[str], dst: str) -> None:
    """Copy ``names`` from ``root`` into the new directory ``dst``: links as links, files and directories with a
    checkout's modes."""
    os.mkdir(dst, 0o755)
    for name in names:
        src, out = os.path.join(root, name), os.path.join(dst, name)
        os.makedirs(os.path.dirname(out), mode=0o755, exist_ok=True)
        if os.path.islink(src):
            os.symlink(os.readlink(src), out)
        else:
            shutil.copyfile(src, out)
            os.chmod(out, 0o755 if os.stat(src).st_mode & 0o111 else 0o644)
    for top, dirs, _ in os.walk(dst):
        for name in dirs:
            os.chmod(os.path.join(top, name), 0o755)


def snapshot(tree: str) -> dict[str, tuple]:
    """Every path under ``tree`` with what a write could change: a link's target, a file's content hash and
    execute bit, a directory, anything else's file type. ``__pycache__`` directories are not read (python's cache,
    see the module's rules)."""
    out: dict[str, tuple] = {}
    for top, dirs, names in os.walk(tree):
        dirs[:] = [d for d in dirs if d != PYCACHE]
        for name in dirs + names:
            path = os.path.join(top, name)
            rel = os.path.relpath(path, tree)
            st = os.lstat(path)
            if stat.S_ISLNK(st.st_mode):
                out[rel] = ("link", os.readlink(path))
            elif stat.S_ISREG(st.st_mode):
                with open(path, "rb") as f:
                    out[rel] = ("file", hashlib.sha256(f.read()).hexdigest(), bool(st.st_mode & 0o111))
            elif stat.S_ISDIR(st.st_mode):
                out[rel] = ("dir",)
            else:
                out[rel] = ("other", stat.S_IFMT(st.st_mode))
    return out


def wrote(before: dict[str, tuple], after: dict[str, tuple]) -> list[str]:
    """The paths added, removed or changed between two snapshots, sorted."""
    return sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))


def remove(path: str) -> None:
    """Remove a work directory, whatever modes a command left in it."""
    for top, dirs, _ in os.walk(path):
        os.chmod(top, 0o700)
        for name in dirs:
            if not os.path.islink(os.path.join(top, name)):
                os.chmod(os.path.join(top, name), 0o700)
    shutil.rmtree(path)


def bindir(path: str, python: str = sys.executable) -> str:
    """A directory holding only ``python`` and ``python3``, links to ``python``."""
    os.mkdir(path)
    for name in ("python", "python3"):
        os.symlink(python, os.path.join(path, name))
    return path


def env(path: str, tmp: str) -> dict[str, str]:
    return {"PATH": path, "HOME": HOME, "TMPDIR": tmp, "LANG": "C.UTF-8"}


def run_one(test: dict, root: str, names: list[str], path: str, work: str, timeout: float) -> dict:
    """Run one command on its own copy of ``names``."""
    own = tempfile.mkdtemp(prefix="%s-" % test["id"], dir=work)
    try:
        tree, tmp = os.path.join(own, "brain"), os.path.join(own, "tmp")
        stage(root, names, tree)
        os.mkdir(tmp, 0o700)
        before = snapshot(tree)
        start = time.monotonic()
        try:
            proc = subprocess.run([SHELL, "-c", test["cmd"]], cwd=tree, env=env(path, tmp),
                                  stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  timeout=timeout)
            code, out, timed_out = proc.returncode, proc.stdout, False
        except subprocess.TimeoutExpired as e:
            code, out, timed_out = None, e.output or b"", True
        duration = int((time.monotonic() - start) * 1000)
        changed = wrote(before, snapshot(tree))
    finally:
        remove(own)
    return {"id": test["id"], "exit": code, "ok": code == 0 and not changed, "timed_out": timed_out,
            "wrote": changed, "duration_ms": duration, "tail": out.decode("utf-8", "replace")[-TAIL:]}


def run(root: str, tests: list[dict], names: list[str], jobs: int = 1, timeout: float = TIMEOUT,
        emit=print) -> dict:
    """Run ``tests``, each on its own copy of ``names``; ``emit`` each result line, in the manifest's order;
    return the summary."""
    work = tempfile.mkdtemp(prefix="like-referee-")
    try:
        path = bindir(os.path.join(work, "bin"))
        with concurrent.futures.ThreadPoolExecutor(max(1, jobs)) as pool:
            results = list(pool.map(lambda t: run_one(t, root, names, path, work, timeout), tests))
        for r in results:
            emit(json.dumps(r, sort_keys=True))
        return {"ok": all(r["ok"] for r in results), "tests": len(results),
                "failed": [r["id"] for r in results if not r["ok"]], "network": "not_isolated"}
    finally:
        remove(work)


def main(argv: list[str] | None = None, root: str = ROOT, git: str = "git") -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-j", "--jobs", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=TIMEOUT)
    ap.add_argument("--only", nargs="+")
    args = ap.parse_args(argv)
    try:
        tests = manifest(root, args.only)
        names = files(root, git)
    except Unreadable as e:
        print(json.dumps({"ok": False, "reason": str(e)}))
        return 2
    summary = run(root, tests, names, args.jobs, args.timeout)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
