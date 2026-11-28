"""Run ``snowball-tests.json``'s commands the way the referee's ``koş`` runs them, as near as a session can.

Why: 057ad34 was rejected (test_failed T14) for a difference of environment only: the tests passed here, where git
is installed, and failed in the referee's sandbox, which has none (founder ledger f396). This runner makes that
class visible before a push. Run from anywhere: ``python3 tests/run_like_referee.py [-j N] [--timeout S]
[--only ID ...] [--warm]``.

What it does, each rule bound by ``tests/test_run_like_referee.py``:

- **The tree is what a commit would hold.** The files are git's list of what ``git add -A`` would commit
  (``git -C <root> ls-files -z --cached --others --exclude-standard``; a listed file that is gone from the work
  tree is not copied), so an ignored file (``__pycache__``, a local fixture) is not there, as in the referee's
  checkout. A symbolic link is copied as a link. This is the one step that needs git: it reads this clone.
- **Each command gets its own copy, with a checkout's modes** (``0644``, ``0755`` for a file with an execute
  bit, ``0755`` for a directory, the copy's root included, whatever the umask), like the referee's checkout, so
  what a test copies out of the tree is writable, as there. A command's copy is removed when the command ends, so a
  run holds at most ``-j`` copies.
- **A write to the tree is a failure, found after the fact** (tohum/29b ``koş``: ``--read-only``, where it fails
  at once). Without root this runner cannot make the tree read-only and keep a checkout's modes (the referee's
  files belong to another user; here they are this user's), so it compares the copy after the command with the
  copy before it: every path added, removed or changed (content, kind, link target, execute bit) is listed in
  ``wrote`` and the command is not ok. One exception, python's own: a path under a directory named
  ``__pycache__`` is not compared, because python writes its bytecode cache there and, on a read-only tree,
  skips that write without an error (any python the command starts, whatever its environment).
- **PATH holds only python**: a directory holding ``python`` and ``python3``, links to one interpreter. The
  command runs under ``/bin/sh -c`` (the shell is found by its path, not by PATH), from the copy's root (tohum/26c:
  ``cmd`` runs from the repository root), stdin ``/dev/null`` (not the runner's own stdin).
- **Which interpreter.** A run's python keeps no bytecode of the standard library (``cold_home``), unless the
  caller asks for a warm one (``--warm``; ``run``'s ``cold=False``) or the cold home cannot be built. *Cold*: a
  moved home (``move_home``, below) whose every directory is closed to writes (mode ``0555``), so that every
  python process a command starts compiles every standard module it imports, which is what the referee's
  durations say of its own (the time limit, below). It is used only when, started with an empty environment, it
  reports itself as its prefix and the same module search path as this interpreter's with the prefix replaced,
  and that start, which imports ``json``, has left no ``__pycache__`` directory under the home (as root, who
  writes whatever the mode, it is not used). *Warm* (``interpreter``): this one (``sys.executable``), except
  where its standard library is
  cold (``stdlib_cold``: no bytecode file for ``json`` and no way for this user to write one), so that every python
  process a command starts compiles every standard module it imports. There the links go to a moved home
  (``move_home``): a copy of this interpreter's binary beside a mirror of its standard library (directories made,
  files linked, no ``__pycache__`` taken over), where python writes the bytecode on first import and later
  processes of the run load it with no variable handed to them (a test's child with an empty environment
  included; a child told not to write bytecode writes none and loads what is there). It is used only when,
  started with an empty environment, it reports itself as its prefix, the same module search path as this
  interpreter's with the prefix replaced, and has written ``json``'s bytecode; otherwise the links go to this
  interpreter as before. The summary's ``python`` says which: ``cold_home``, ``own`` or ``moved_home``; a run
  asked cold that says another kind timed its commands warm. Measured where this was
  written (founder ledger, 2026-11-17): the capsule's ``/usr/local/lib/python3.12`` holds no bytecode and is
  read-only; one ``python -m loop.job`` start took 1.14 s cold and 0.56 s from a moved home.
- **The environment is only** ``PATH``, ``HOME=/nonexistent`` (no home to read or write), ``TMPDIR`` (a new
  directory per command) and ``LANG=C.UTF-8``; nothing of this session's environment passes.
- **A time limit per command** (``--timeout``, default ``TIMEOUT``, 600 s): a command that exceeds it is killed
  and is ``timed_out``, not ok. The number is tohum/29b:24's (each command alone, ``limits.test_timeout_s`` of
  the operator's ``bootstrap.json``, 600 today); that file is in the referee's repository, which a session does
  not read, so the constant here is the page's and the referee's results' (c467639 and 4292f47: T46 with
  ``exit`` 124, ``timed_out`` true, ``duration_ms`` 600162 and 600160), not read from the file. **A duration
  here is not the referee's**: both of those trees were green here. Measured 2026-11-28 on 4292f47's test
  files: where a file's tests start many python processes the referee took 2.5 to 2.7 times this host's warm
  time (``test_loop_kos`` 21.1 s against 7.9, ``test_loop_yaz`` 73.8 against 29.6, ``test_loop_handover`` 45.3
  against 18.4) and 0.74 to 0.77 of this host's time on a home that keeps no bytecode (28.7, 95.8, 60.6), while
  files that start none took about this host's warm time (``test_serial`` 0.46 against 0.42, ``test_treehash``
  1.9 against 2.2). Read as: the referee's standard library is cold; not seen directly. So a warm run's durations bound no
  command's time there (both rejected trees were green warm), and a cold run's are this host's, not the
  referee's: by the three files above the referee took about three quarters of them, a ratio of one day and one
  host that no test holds. What a cold run does hold: a command that exceeds the limit here on a cold library is
  red here before it is pushed.
- One JSON line per command (``id``, ``exit``, ``ok``, ``timed_out``, ``wrote``, ``duration_ms``, ``tail``: the
  last 600 characters of stdout and stderr together; ``read`` only when the caller watches paths, see ``run_one``),
  then one summary line (``ok``, ``tests``, ``failed``,
  ``network``, ``python``). Exit 0 when every command exited 0, 1 when one did not, 2 when the manifest or the file list
  cannot be read. The copy and every ``TMPDIR`` are removed after the run.

Out of scope, stated (the referee does these; this runner does not): no network isolation (``--network none``
needs a namespace this session cannot make: ``unshare -rn`` is refused here), so the summary says ``network:
not_isolated`` and a test reaching the network can still pass here; no ``--cap-drop ALL`` and no ``--user 65534``;
a write outside the tree (``/tmp`` aside, the referee's root file system is read-only) is not seen;
the referee's image (its python version, its ``/bin/sh``, its installed programs other than git) is not this
machine's; under a moved home ``sys.prefix`` and the standard library's paths are the run's directory, not the
installed ones (a test that reads them sees the difference), the same under a cold home; the referee's own standard library is taken
to be cold from the durations above, not from a look at it, and its machine's speed is not this one's. A green run here is necessary
evidence, not the referee's verdict.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import sysconfig
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = "/nonexistent"
SHELL = "/bin/sh"
TAIL = 600
TIMEOUT = 600.0
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
    # mkdir's mode is masked by the umask; every directory, ``dst`` included, is set after the fact.
    for top, _, _ in os.walk(dst):
        os.chmod(top, 0o755)


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


def stdlib_cold(stdlib: str) -> bool:
    """Whether a python process pays for compiling ``stdlib`` at every start: ``PROBE`` there (the ``json``
    package: a module python does not carry frozen in its binary, and the one ``SELF`` imports) has no bytecode
    file where this process would look for one, and this user cannot write to the directory that would hold it."""
    cache = importlib.util.cache_from_source(os.path.join(stdlib, PROBE))
    if os.path.exists(cache):
        return False
    holder = os.path.dirname(cache)
    while not os.path.isdir(holder):
        holder = os.path.dirname(holder)
    return not os.access(holder, os.W_OK)


def mirror(src: str, dst: str) -> None:
    """Make ``dst`` a tree of ``src``'s directories with a link to each of its other entries; a directory named
    ``__pycache__`` is not taken over, and a link to a directory stays one link."""
    os.makedirs(dst)
    for name in sorted(os.listdir(src)):
        if name == PYCACHE:
            continue
        path = os.path.join(src, name)
        if os.path.isdir(path) and not os.path.islink(path):
            mirror(path, os.path.join(dst, name))
        else:
            os.symlink(path, os.path.join(dst, name))


def move_home(dst: str, binary: str, prefix: str, stdlib: str, libdir: str | None) -> str:
    """Build under the new directory ``dst`` what python needs to take ``dst`` as its prefix: a copy of
    ``binary`` at its place relative to ``prefix``, ``mirror`` of ``stdlib`` at its place, and a link to every
    ``libpython*`` file of ``libdir`` at its place (where the binary finds its shared library relative to itself).
    Returns the copied binary. ``binary``, ``stdlib`` and ``libdir`` must lie under ``prefix``: ValueError if not."""
    def moved(path: str) -> str:
        rel = os.path.relpath(path, prefix)
        if rel == os.curdir or rel.split(os.sep)[0] == os.pardir:
            raise ValueError("outside_prefix:%s" % path)
        return os.path.join(dst, rel)

    out, lib = moved(binary), moved(stdlib)
    libs = moved(libdir) if libdir else None
    os.makedirs(os.path.dirname(out))
    shutil.copyfile(binary, out)
    os.chmod(out, 0o755)
    os.makedirs(os.path.dirname(lib), exist_ok=True)
    mirror(stdlib, lib)
    if libs:
        os.makedirs(libs, exist_ok=True)
        for name in sorted(os.listdir(libdir)):
            if name.startswith("libpython") and not os.path.lexists(os.path.join(libs, name)):
                os.symlink(os.path.join(libdir, name), os.path.join(libs, name))
    return out


PROBE = os.path.join("json", "__init__.py")
SELF = "import json,sys; print(json.dumps([sys.prefix, sys.base_prefix, sys.exec_prefix, json.__file__, sys.path]))"


def describe(python: str) -> list | None:
    """What ``python`` says of itself (``SELF``) started isolated (``-I``) with an empty environment; None when it
    does not start, fails or prints something else."""
    try:
        proc = subprocess.run([python, "-I", "-c", SELF], env={}, stdin=subprocess.DEVNULL, capture_output=True,
                              timeout=60)
        return json.loads(proc.stdout) if proc.returncode == 0 else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def this() -> dict[str, str | None]:
    """This interpreter as ``interpreter`` reads it: the path it was started by, its prefix, its standard library
    and the directory of its shared library (None when the build names none)."""
    return {"executable": sys.executable, "prefix": sys.base_prefix, "stdlib": sysconfig.get_path("stdlib"),
            "libdir": sysconfig.get_config_var("LIBDIR")}


def interpreter(home: str, cold=stdlib_cold, python: dict | None = None) -> tuple[str, str]:
    """The interpreter a run's ``python`` links to and its kind: ``(<executable>, "own")``, or, where the
    standard library of ``python`` (``this()`` when None) is ``cold``, ``(<binary under home>, "moved_home")``
    when the moved home built at the new directory ``home`` passes the module's three checks (prefix, search
    path, bytecode written). A home that cannot be built or fails a check is removed and the answer is ``own``."""
    py = python or this()
    if not cold(py["stdlib"]):
        return py["executable"], "own"
    try:
        binary = move_home(home, os.path.realpath(py["executable"]), py["prefix"], py["stdlib"], py["libdir"])
        cache = says_home(py, home, binary)
        if cache and os.path.isfile(cache):
            return binary, "moved_home"
    except (OSError, ValueError, TypeError, IndexError):
        pass
    if os.path.lexists(home):
        remove(home)
    return py["executable"], "own"


def says_home(py: dict, home: str, binary: str) -> str | None:
    """The first two checks of a moved home: ``binary`` under ``home``, asked by ``describe``, reports ``home`` as
    its prefix and the search path of ``py`` (``this()``'s shape) with the prefix replaced, ``py`` itself
    reporting its own prefix. Then: where ``PROBE``'s bytecode file lies under ``home``, written or not (the
    caller's third check); None when a check fails."""
    prefix = py["prefix"]
    mine, moved = describe(py["executable"]), describe(binary)
    if mine and mine[:3] == [prefix] * 3:
        swap = lambda p: home + p[len(prefix):] if p.startswith(prefix + os.sep) else p  # noqa: E731
        if moved == [home, home, home, swap(mine[3]), [swap(p) for p in mine[4]]]:
            return os.path.join(os.path.dirname(swap(mine[3])), PYCACHE,
                                "__init__.%s.pyc" % sys.implementation.cache_tag)
    return None


def cold_home(home: str, python: dict | None = None) -> str | None:
    """A python whose every start compiles what it imports: the binary of a moved home built at the new directory
    ``home`` from ``python`` (``this()`` when None), every directory under it closed to writes (mode ``0555``), so
    that python can keep no bytecode there. It is answered only when ``says_home`` holds and, after that start
    (which imports ``json``), no directory named ``__pycache__`` lies under ``home``; a home that cannot be built
    or fails a check is removed and the answer is None (as root, who writes whatever the mode, it fails)."""
    py = python or this()
    try:
        binary = move_home(home, os.path.realpath(py["executable"]), py["prefix"], py["stdlib"], py["libdir"])
        for top, _, _ in os.walk(home):
            os.chmod(top, 0o555)
        if says_home(py, home, binary) and not any(PYCACHE in dirs for _, dirs, _ in os.walk(home)):
            return binary
    except (OSError, ValueError, TypeError, IndexError):
        pass
    if os.path.lexists(home):
        remove(home)
    return None


def bindir(path: str, python: str = sys.executable) -> str:
    """A directory holding only ``python`` and ``python3``, links to ``python``."""
    os.mkdir(path)
    for name in ("python", "python3"):
        os.symlink(python, os.path.join(path, name))
    return path


def pythons(work: str, cold: bool = False) -> tuple[str, str]:
    """The ``PATH`` directory of a run under ``work`` and the kind of the interpreter its links go to:
    ``cold_home`` when ``cold`` is asked and ``cold_home`` builds one, else ``interpreter``'s answer."""
    python = cold_home(os.path.join(work, "python-cold")) if cold else None
    if python:
        return bindir(os.path.join(work, "bin"), python), "cold_home"
    python, kind = interpreter(os.path.join(work, "python-home"))
    return bindir(os.path.join(work, "bin"), python), kind


def env(path: str, tmp: str) -> dict[str, str]:
    return {"PATH": path, "HOME": HOME, "TMPDIR": tmp, "LANG": "C.UTF-8"}


def unread(path: str) -> None:
    """Set a file's access time to 0 and keep its modification time, so that the next read of its bytes moves the
    access time (on a file system mounted ``relatime`` or ``strictatime``; ``atime_moves`` asks which)."""
    os.utime(path, ns=(0, os.stat(path).st_mtime_ns))


def was_read(path: str) -> bool:
    return os.stat(path).st_atime_ns != 0


def atime_moves(directory: str) -> bool:
    """Whether reading a file under ``directory`` moves an access time ``unread`` set: False on a ``noatime``
    mount, where ``run_one``'s ``read`` would be empty whatever a command read."""
    fd, probe = tempfile.mkstemp(dir=directory)
    try:
        os.write(fd, b"x")
        os.close(fd)
        unread(probe)
        with open(probe, "rb") as f:
            f.read()
        return was_read(probe)
    finally:
        os.remove(probe)


def run_one(test: dict, root: str, names: list[str], path: str, work: str, timeout: float,
            watch: tuple[str, ...] = ()) -> dict:
    """Run one command on its own copy of ``names``; the copy and its ``TMPDIR`` are removed when it ends. With
    ``watch`` (names of regular files in ``names``), the result carries ``read``: the watched files whose bytes the
    command read from its copy, by access time (``unread`` before the command, ``was_read`` after it; meaningful
    only where ``atime_moves``). Not seen: a read with ``O_NOATIME``, a command that sets the times itself, and the
    same bytes read from anywhere but the copy. The id is data: it names the result and is no part of any path."""
    own = tempfile.mkdtemp(prefix="cmd-", dir=work)
    try:
        tree, tmp = os.path.join(own, "brain"), os.path.join(own, "tmp")
        stage(root, names, tree)
        os.mkdir(tmp, 0o700)
        before = snapshot(tree)
        for name in watch:
            unread(os.path.join(tree, name))
        start = time.monotonic()
        try:
            proc = subprocess.run([SHELL, "-c", test["cmd"]], cwd=tree, env=env(path, tmp),
                                  stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  timeout=timeout)
            code, out, timed_out = proc.returncode, proc.stdout, False
        except subprocess.TimeoutExpired as e:
            code, out, timed_out = None, e.output or b"", True
        duration = int((time.monotonic() - start) * 1000)
        read = sorted(n for n in watch if os.path.isfile(os.path.join(tree, n)) and was_read(os.path.join(tree, n)))
        changed = wrote(before, snapshot(tree))
    finally:
        remove(own)
    result = {"id": test["id"], "exit": code, "ok": code == 0 and not changed, "timed_out": timed_out,
              "wrote": changed, "duration_ms": duration, "tail": out.decode("utf-8", "replace")[-TAIL:]}
    if watch:
        result["read"] = read
    return result


def run(root: str, tests: list[dict], names: list[str], jobs: int = 1, timeout: float = TIMEOUT,
        emit=print, watch: tuple[str, ...] = (), cold: bool = True) -> dict:
    """Run ``tests``, each on its own copy of ``names``; ``emit`` each result line, in the manifest's order;
    return the summary. ``watch``: see ``run_one``. ``cold``: see ``pythons``."""
    work = tempfile.mkdtemp(prefix="like-referee-")
    try:
        path, kind = pythons(work, cold)
        with concurrent.futures.ThreadPoolExecutor(max(1, jobs)) as pool:
            results = list(pool.map(lambda t: run_one(t, root, names, path, work, timeout, watch), tests))
        for r in results:
            emit(json.dumps(r, sort_keys=True))
        return {"ok": all(r["ok"] for r in results), "tests": len(results),
                "failed": [r["id"] for r in results if not r["ok"]], "network": "not_isolated", "python": kind}
    finally:
        remove(work)


def main(argv: list[str] | None = None, root: str = ROOT, git: str = "git") -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-j", "--jobs", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=TIMEOUT)
    ap.add_argument("--only", nargs="+")
    ap.add_argument("--warm", action="store_true")
    args = ap.parse_args(argv)
    try:
        tests = manifest(root, args.only)
        names = files(root, git)
    except Unreadable as e:
        print(json.dumps({"ok": False, "reason": str(e)}))
        return 2
    summary = run(root, tests, names, args.jobs, args.timeout, cold=not args.warm)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
