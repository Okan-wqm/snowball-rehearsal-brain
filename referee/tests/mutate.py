"""Run kept mutants: each in its own copy of the brain, each against the tests named for it.

A mutant is data (``tests/mutants/<topic>.json``): ``{"mutants": [{"id", "file", "old", "new", "tests"}]}``,
``file`` relative to ``referee/``, ``tests`` a list whose entries are each either a ``referee/tests`` file pattern
(an entry ending in ``.py``) or a unittest id (``<module>.<Class>`` or ``<module>.<Class>.<method>``, dotted
identifiers, ``<module>`` the file ``referee/tests/<module>.py``); any other entry is malformed. For each mutant:

- ``old`` must occur in ``file`` exactly once in the brain as it is: ``stale`` (zero; a refactor removed the code
  the mutant was written for) or ``ambiguous`` (more), and nothing is run;
- the brain is copied (``.git`` included: some tests read the brain's commits), ``old`` is replaced by ``new`` in
  the copy, and each entry runs in order in the copy's ``referee/``: a pattern as
  ``python -m unittest discover -s tests -p <pattern>``, an id as unittest's ``main`` over that one name with
  ``referee/tests`` first on ``sys.path`` (what discover puts there), so an id runs in the same directory and
  imports the same modules as its file's discover run, only fewer tests. ``killed`` when one exits non-zero (a
  run of no test is non-zero: Python 3.12's exit 5), ``survived`` when all exit 0, ``timeout`` when one runs
  longer than the limit (reported, neither killed nor survived);
- each distinct ``tests`` list is first run once on an unchanged copy: if it is not green there, its mutants are
  ``baseline_red`` and not run (a red test kills every mutant and proves nothing).

Each row ``{file, id, outcome}`` is printed and flushed as its mutant finishes, so the rows come in the order
the mutants finish, and a run that is cut keeps the rows it printed (the baselines run first and print nothing).
Exit 0 only when every mutant is ``killed`` (no mutant run is exit 1: nothing was shown). The brain itself is
only read.

``--touched REV`` runs only the mutants a change since ``REV`` can concern. The changed paths are git's: every path
``git diff --name-only --no-renames REV`` names (``REV`` against the working tree, staged or not, committed or not;
a rename names both its paths) and every untracked path ``git ls-files --others --exclude-standard`` names. A
mutant is selected when a changed path is

- the mutant's own file under ``tests/mutants/`` (a new or edited mutant), or
- a ``.py`` file in the import closure of its ``file`` or of a ``.py`` file under ``referee/tests`` whose name one
  of its ``tests`` entries names (a pattern by ``fnmatch``, discover runs these or fewer; an id by its
  ``<module>``), its ``file`` included. The closure
  is ``status.depmap``'s reading of import statements (one reader of imports) and every package holding a module
  reached (Python runs it first), over the working tree's modules as the test run sees them: ``referee/tests``'s
  files by their names inside ``tests``, then ``referee/``'s outside it; a changed ``.py`` path the working tree no
  longer has (removed, renamed away) is a module still, reached by a file that imports its name.

Not seen by ``--touched``, stated: a change to a file that is not Python (a fixture, a JSON, a workflow) or that
a test reaches without an import statement (opened by path, run as a subprocess, imported by a built name); the
imports of a file that does not parse (it is selected by its own path, it reaches nothing further). Before a push
that changes such a file, run the full set.

Out of scope, stated: tests outside ``referee/tests`` (the brain's root ``tests/``), mutants that are not one
textual replacement, and equivalent mutants (a ``survived`` mutant may be one: the runner says it survived,
a person says why).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from fnmatch import fnmatch
from typing import Any, Callable

BRAIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BRAIN, "referee"))

from status import depmap  # noqa: E402
FIELDS = ("id", "file", "old", "new", "tests")
TEST_ID = re.compile(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*){1,2}", re.ASCII)
# One name run as discover would: referee/tests first on sys.path, the cwd (referee/) after it.
RUN_ID = ("import os, sys, unittest; sys.path.insert(0, os.path.abspath('tests')); "
          "unittest.main(module=None, argv=['unittest', sys.argv[1]])")


def test_file(entry: str) -> str:
    """The ``referee/tests`` file pattern of a ``tests`` entry: a pattern itself, an id its ``<module>.py``."""
    return entry if entry.endswith(".py") else entry.split(".", 1)[0] + ".py"


def _entry(entry: Any) -> bool:
    return isinstance(entry, str) and (entry.endswith(".py") or bool(TEST_ID.fullmatch(entry)))


def load(path: str) -> list[dict[str, Any]]:
    """The mutants of one file; a malformed file or mutant raises ``ValueError``."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    mutants = data.get("mutants") if isinstance(data, dict) else None
    if not isinstance(mutants, list) or not mutants:
        raise ValueError("%s: no mutants list" % path)
    for m in mutants:
        if not (isinstance(m, dict) and sorted(m) == sorted(FIELDS)
                and all(isinstance(m[k], str) and m[k] for k in ("id", "file", "old"))
                and isinstance(m["new"], str) and m["new"] != m["old"]
                and isinstance(m["tests"], list) and m["tests"] and all(_entry(t) for t in m["tests"])):
            raise ValueError("%s: malformed mutant %r" % (path, m.get("id") if isinstance(m, dict) else m))
    ids = [m["id"] for m in mutants]
    if len(set(ids)) != len(ids):
        raise ValueError("%s: duplicate mutant id" % path)
    return mutants


def applicable(brain: str, mutant: dict[str, Any]) -> str | None:
    """``None`` when ``old`` occurs once in the brain's ``file``, else ``stale`` or ``ambiguous``."""
    path = os.path.join(brain, "referee", mutant["file"])
    try:
        with open(path, encoding="utf-8") as fh:
            count = fh.read().count(mutant["old"])
    except FileNotFoundError:
        count = 0
    return None if count == 1 else ("stale" if count == 0 else "ambiguous")


def _copy(brain: str) -> str:
    work = tempfile.mkdtemp(prefix="mutate-")
    copy = os.path.join(work, "brain")
    shutil.copytree(brain, copy, symlinks=True, ignore=shutil.ignore_patterns("__pycache__"))
    return copy


def _run_tests(copy: str, tests: list[str], timeout: float) -> str:
    """``green``, ``red`` or ``timeout`` for the entries run in order in the copy's ``referee/``."""
    for entry in tests:
        argv = ([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", entry] if entry.endswith(".py")
                else [sys.executable, "-c", RUN_ID, entry])
        try:
            done = subprocess.run(argv,
                                  cwd=os.path.join(copy, "referee"), stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL, timeout=timeout)
        except subprocess.TimeoutExpired:
            return "timeout"
        if done.returncode != 0:
            return "red"
    return "green"


def baseline(brain: str, tests: list[str], timeout: float) -> str:
    copy = _copy(brain)
    try:
        return _run_tests(copy, tests, timeout)
    finally:
        shutil.rmtree(os.path.dirname(copy), ignore_errors=True)


def run_one(brain: str, mutant: dict[str, Any], timeout: float) -> str:
    """``killed``, ``survived``, ``timeout``, ``stale`` or ``ambiguous``."""
    reason = applicable(brain, mutant)
    if reason:
        return reason
    copy = _copy(brain)
    try:
        path = os.path.join(copy, "referee", mutant["file"])
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text.replace(mutant["old"], mutant["new"]))
        verdict = _run_tests(copy, mutant["tests"], timeout)
    finally:
        shutil.rmtree(os.path.dirname(copy), ignore_errors=True)
    return {"red": "killed", "green": "survived"}.get(verdict, verdict)


def touched(brain: str, rev: str) -> set[str]:
    """The paths changed since ``rev``, relative to the brain (rules in the module docstring); a ``rev`` git
    cannot read raises ``ValueError``."""
    def git(*args: str) -> list[str]:
        done = subprocess.run(["git", "-C", brain, *args], capture_output=True, text=True)
        if done.returncode != 0:
            raise ValueError("git %s: %s" % (" ".join(args), done.stderr.strip()))
        return [line for line in done.stdout.splitlines() if line]
    git("rev-parse", "--verify", "--quiet", rev + "^{commit}")
    return set(git("diff", "--name-only", "--no-renames", rev, "--")) | set(git("ls-files", "--others",
                                                                                 "--exclude-standard"))


def closure_of(brain: str, changed: set[str]) -> Callable[[list[str]], set[str]]:
    """``paths -> closure``: brain-relative ``.py`` paths to the brain-relative paths of every module their import
    statements reach and every package holding one (Python runs it first), themselves included. A changed
    ``.py`` path the working tree no longer has is a module with no imports, so a file still importing it reaches
    it."""
    removed = sorted(p for p in changed if p.endswith(".py") and not os.path.exists(os.path.join(brain, p)))
    modules: dict[str, str] = {}
    spaces = ("referee/tests/", "referee/")  # the test run's order: tests' own names first
    for prefix in spaces:
        found = {n: prefix + rel for n, rel in depmap.python_modules(os.path.join(brain, prefix)).items()}
        found.update({depmap.module_name(p[len(prefix):]): p for p in removed
                      if next((s for s in spaces if p.startswith(s)), None) == prefix})
        for name, path in sorted(found.items()):
            if name:
                modules.setdefault(name, path)
    names = {rel: n for n, rel in modules.items()}
    edges: dict[str, set[str]] = {}
    for name, rel in modules.items():
        try:
            with open(os.path.join(brain, rel), encoding="utf-8") as fh:
                edges[name] = depmap.module_imports(fh.read(), name, rel.endswith("__init__.py"), modules)
        except (FileNotFoundError, SyntaxError):  # removed, or its imports cannot be read: it reaches nothing
            edges[name] = set()

    def closure(paths: list[str]) -> set[str]:
        reached = depmap.with_packages(depmap.reachable(edges, [names[p] for p in paths if p in names]), modules)
        return set(paths) | {modules[n] for n in reached}
    return closure


def select(brain: str, items: list[tuple[str, dict[str, Any]]], changed: set[str]) -> list[tuple[str, dict]]:
    """The ``(mutant file, mutant)`` items a change to ``changed`` (brain-relative paths) can concern."""
    closure = closure_of(brain, changed)
    root = os.path.join(brain, "referee", "tests")
    tests = sorted("referee/tests/" + rel for rel in depmap.python_modules(root).values())

    def concerned(path: str, m: dict[str, Any]) -> bool:
        if os.path.relpath(path, brain) in changed:
            return True
        roots = ["referee/" + m["file"]] + [t for t in tests if any(fnmatch(os.path.basename(t), test_file(e))
                                                                    for e in m["tests"])]
        return bool(closure(roots) & changed)
    return [(path, m) for path, m in items if concerned(path, m)]


def run(brain: str, files: list[str], jobs: int, timeout: float, changed: set[str] | None = None,
        emit: Callable[[dict[str, str]], None] | None = None) -> list[dict[str, str]]:
    """One row per mutant, in file and mutant order: ``{file, id, outcome}``; with ``changed``, only the mutants
    ``select`` keeps; ``emit`` is called with each row as its mutant finishes (one thread at a time)."""
    mutants = [(path, m) for path in files for m in load(path)]
    if changed is not None:
        mutants = select(brain, mutants, changed)
    suites = sorted({tuple(m["tests"]) for _, m in mutants if not applicable(brain, m)})
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        base = dict(zip(suites, pool.map(lambda t: baseline(brain, list(t), timeout), suites)))

        lock = threading.Lock()

        def one(item: tuple[str, dict[str, Any]]) -> dict[str, str]:
            path, m = item
            outcome = applicable(brain, m) or ("baseline_red" if base[tuple(m["tests"])] != "green"
                                               else run_one(brain, m, timeout))
            row = {"file": os.path.relpath(path, brain), "id": m["id"], "outcome": outcome}
            if emit:
                with lock:
                    emit(row)
            return row

        return list(pool.map(one, mutants))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", help="mutant files (default: every referee/tests/mutants/*.json)")
    parser.add_argument("--brain", default=BRAIN)
    parser.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--timeout", type=float, default=900.0, help="seconds per tests entry")
    parser.add_argument("--touched", metavar="REV", help="only the mutants a change since REV can concern")
    args = parser.parse_args(argv)
    brain = os.path.abspath(args.brain)
    files = args.files or sorted(glob.glob(os.path.join(brain, "referee", "tests", "mutants", "*.json")))
    changed = touched(brain, args.touched) if args.touched else None
    rows = run(brain, [os.path.abspath(f) for f in files], args.jobs, args.timeout, changed,
               lambda row: print(json.dumps(row, sort_keys=True), flush=True))
    if changed is not None:
        print("--touched %s: %d changed paths, %d mutants selected" % (args.touched, len(changed), len(rows)),
              file=sys.stderr)
    return 0 if rows and all(r["outcome"] == "killed" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
