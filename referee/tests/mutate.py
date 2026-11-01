"""Run kept mutants: each in its own copy of the brain, each against the tests named for it.

A mutant is data (``tests/mutants/<topic>.json``): ``{"mutants": [{"id", "file", "old", "new", "tests"}]}``,
``file`` relative to ``referee/``, ``tests`` a list of ``referee/tests`` file patterns. For each mutant:

- ``old`` must occur in ``file`` exactly once in the brain as it is: ``stale`` (zero; a refactor removed the code
  the mutant was written for) or ``ambiguous`` (more), and nothing is run;
- the brain is copied (``.git`` included: some tests read the brain's commits), ``old`` is replaced by ``new`` in
  the copy, and ``python -m unittest discover -s tests -p <pattern>`` runs in the copy's ``referee/`` for each
  pattern in order: ``killed`` when one exits non-zero, ``survived`` when all exit 0, ``timeout`` when one runs
  longer than the limit (reported, neither killed nor survived);
- each distinct ``tests`` list is first run once on an unchanged copy: if it is not green there, its mutants are
  ``baseline_red`` and not run (a red test kills every mutant and proves nothing).

Exit 0 only when every mutant is ``killed``. The brain itself is only read.

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
import shutil
import subprocess
import sys
import tempfile
from typing import Any

BRAIN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIELDS = ("id", "file", "old", "new", "tests")


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
                and isinstance(m["tests"], list) and m["tests"] and all(isinstance(t, str) and t for t in m["tests"])):
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
    """``green``, ``red`` or ``timeout`` for the patterns run in order in the copy's ``referee/``."""
    for pattern in tests:
        try:
            done = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern],
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


def run(brain: str, files: list[str], jobs: int, timeout: float) -> list[dict[str, str]]:
    """One row per mutant, in file and mutant order: ``{file, id, outcome}``."""
    mutants = [(path, m) for path in files for m in load(path)]
    suites = sorted({tuple(m["tests"]) for _, m in mutants if not applicable(brain, m)})
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        base = dict(zip(suites, pool.map(lambda t: baseline(brain, list(t), timeout), suites)))

        def one(item: tuple[str, dict[str, Any]]) -> str:
            _, m = item
            reason = applicable(brain, m)
            if reason:
                return reason
            if base[tuple(m["tests"])] != "green":
                return "baseline_red"
            return run_one(brain, m, timeout)

        outcomes = list(pool.map(one, mutants))
    return [{"file": os.path.relpath(path, brain), "id": m["id"], "outcome": outcome}
            for (path, m), outcome in zip(mutants, outcomes)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", help="mutant files (default: every referee/tests/mutants/*.json)")
    parser.add_argument("--brain", default=BRAIN)
    parser.add_argument("-j", "--jobs", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--timeout", type=float, default=900.0, help="seconds per test pattern")
    args = parser.parse_args(argv)
    files = args.files or sorted(glob.glob(os.path.join(args.brain, "referee", "tests", "mutants", "*.json")))
    rows = run(os.path.abspath(args.brain), [os.path.abspath(f) for f in files], args.jobs, args.timeout)
    for row in rows:
        print(json.dumps(row, sort_keys=True))
    return 0 if rows and all(r["outcome"] == "killed" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
