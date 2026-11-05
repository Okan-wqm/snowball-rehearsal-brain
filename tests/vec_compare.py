"""Run the referee's data vectors on two trees of this brain and say which outputs differ: the evidence that a
refactor changes no output a vector reads, or exactly which ones a fix changes.

Why: a push that means to keep behaviour (a refactor, a speed-up such as f873's) is accepted only if every vector
still holds, but the expected values are not here (tohum/29a); what a session can show is that each case's output
is the same before and after the change. f908 did this by hand in ``/tmp``; this is that comparison as a tool,
with its normalisations in one place (``NORMALISE``). Run from anywhere:
``python3 tests/vec_compare.py [--before REV] [--cases PATH] [--only ID ...] [-j N] [--timeout S]``.

What it does, each rule bound by ``tests/test_vec_compare.py``:

- **The two trees.** *before* is the commit ``--before`` names (default ``HEAD``), read with ``git archive``;
  *after* is the work tree as a commit would hold it (``run_like_referee.files``: what ``git add -A`` would
  commit). Both are staged with ``run_like_referee.stage`` (a checkout's modes), one copy per side.
- **Each case is run as the referee runs it** (operator, 2026-10-30): its ``cmd`` under ``/bin/sh -c`` with its
  ``stdin``, from the tree's ``referee/``, and its ``changed`` side the same way; the environment is
  ``run_like_referee.env`` (only python on ``PATH``, no home, a new ``TMPDIR`` per run, ``LANG=C.UTF-8``).
  Every case of ``--cases`` (default ``/vec/cases.json``) is run; ``--only`` keeps the named ids and an unknown
  id is unreadable, not skipped.
- **What is compared**, per case and side: the exit code, stdout and stderr, after ``normalise``; a run killed
  at ``--timeout`` (default 300 s) has exit ``null`` and ``timed_out`` true, which is compared like the others.
- **Normalised** (``NORMALISE``, the one list): only outputs measured to vary between two runs of one tree, each
  replaced by a fixed token. Today one: ``runner.contained``'s container name ``snowball-<32 hex>``
  (``runner/contained.py``: ``"snowball-" + token_hex(16)`` when no name is given). Anything else that varies
  is reported as a difference; ``--before HEAD`` on a clean tree is how a new one is found.
- One JSON line per differing case side (``id``, ``side``, ``fields``: which of exit, stdout, stderr,
  timed_out differ, and each side's values, the streams cut to their last 600 characters), then one summary line
  (``ok``, ``before``, ``cases``, ``runs``, ``differ``: ``id/side`` names). Exit 0 when every run is equal, 1
  when one differs, 2 when the cases, the revision or the file list cannot be read.

Out of scope, stated: equal outputs are not correct outputs (the expected values are the referee's, not here);
a difference is not an error (a fix means one); the referee's image, network isolation and user are not this
machine's (``run_like_referee``'s limits); a file a command writes outside stdout and stderr is not compared.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_like_referee as RLR  # noqa: E402

CASES = "/vec/cases.json"
TIMEOUT = 300.0
TAIL = RLR.TAIL
FIELDS = ("exit", "timed_out", "stdout", "stderr")
NORMALISE = (
    (re.compile(r"\bsnowball-[0-9a-f]{32}\b"), "snowball-<name>"),
)


class Unreadable(Exception):
    """The cases, the revision or the file list cannot be read; the message is the reason."""


def normalise(text: str) -> str:
    """``text`` with every ``NORMALISE`` pattern replaced by its token."""
    for pattern, token in NORMALISE:
        text = pattern.sub(token, text)
    return text


def cases(path: str, only: list[str] | None = None) -> list[dict]:
    """The runs of ``path``'s cases: ``{id, side, cmd, stdin}`` for each case's ``base`` and ``changed`` side."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        runs = []
        for c in data:
            for side, spec in (("base", c), ("changed", c["changed"])):
                if not isinstance(spec["cmd"], str) or not isinstance(spec["stdin"], str):
                    raise TypeError
                runs.append({"id": c["id"], "side": side, "cmd": spec["cmd"], "stdin": spec["stdin"]})
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise Unreadable("cases_unreadable:%s" % type(e).__name__) from None
    if only:
        missing = sorted(set(only) - {r["id"] for r in runs})
        if missing:
            raise Unreadable("case_unknown:%s" % ",".join(missing))
        runs = [r for r in runs if r["id"] in only]
    return runs


def archive(root: str, rev: str, dst: str, git: str = "git") -> None:
    """Write the tree of commit ``rev`` of the repository at ``root`` into the new directory ``dst``."""
    try:
        proc = subprocess.run([git, "-C", root, "archive", "--format=tar", rev + "^{commit}"],
                              stdin=subprocess.DEVNULL, capture_output=True)
    except OSError:
        raise Unreadable("git_unavailable") from None
    if proc.returncode != 0:
        raise Unreadable("revision_unreadable:%s" % rev)
    os.mkdir(dst, 0o755)
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as tar:
        tar.extractall(dst, filter="data")


def run_one(run: dict, tree: str, path: str, work: str, timeout: float) -> dict:
    """Run one case side from ``tree``'s ``referee/``; its exit, timeout and normalised streams."""
    tmp = tempfile.mkdtemp(prefix="tmp-", dir=work)
    try:
        try:
            proc = subprocess.run([RLR.SHELL, "-c", run["cmd"]], cwd=os.path.join(tree, "referee"),
                                  env=RLR.env(path, tmp), input=run["stdin"].encode("utf-8"),
                                  capture_output=True, timeout=timeout)
            code, out, err, timed_out = proc.returncode, proc.stdout, proc.stderr, False
        except subprocess.TimeoutExpired as e:
            code, out, err, timed_out = None, e.stdout or b"", e.stderr or b"", True
    finally:
        RLR.remove(tmp)
    return {"exit": code, "timed_out": timed_out, "stdout": normalise(out.decode("utf-8", "replace")),
            "stderr": normalise(err.decode("utf-8", "replace"))}


def differs(before: dict, after: dict) -> list[str]:
    """The ``FIELDS`` whose values differ, in that order."""
    return [k for k in FIELDS if before[k] != after[k]]


def cut(result: dict) -> dict:
    return {k: (v[-TAIL:] if isinstance(v, str) else v) for k, v in result.items()}


def compare(root: str, runs: list[dict], before_rev: str, jobs: int = 1, timeout: float = TIMEOUT,
            git: str = "git", emit=print) -> dict:
    """Run ``runs`` on both trees; ``emit`` a line per differing run, in the cases' order; return the summary."""
    work = tempfile.mkdtemp(prefix="vec-compare-")
    try:
        before, after = os.path.join(work, "before"), os.path.join(work, "after")
        archive(root, before_rev, before, git)
        RLR.stage(root, RLR.files(root, git), after)
        path = RLR.bindir(os.path.join(work, "bin"))
        pairs = [(r, tree) for r in runs for tree in (before, after)]
        with concurrent.futures.ThreadPoolExecutor(max(1, jobs)) as pool:
            got = list(pool.map(lambda p: run_one(p[0], p[1], path, work, timeout), pairs))
        differ = []
        for i, r in enumerate(runs):
            b, a = got[2 * i], got[2 * i + 1]
            fields = differs(b, a)
            if fields:
                name = "%s/%s" % (r["id"], r["side"])
                differ.append(name)
                emit(json.dumps({"id": r["id"], "side": r["side"], "fields": fields,
                                 "before": cut(b), "after": cut(a)}, sort_keys=True))
        return {"ok": not differ, "before": before_rev, "cases": len({r["id"] for r in runs}), "runs": len(runs),
                "differ": differ}
    finally:
        RLR.remove(work)


def main(argv: list[str] | None = None, root: str = RLR.ROOT, git: str = "git") -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--before", default="HEAD")
    ap.add_argument("--cases", default=CASES)
    ap.add_argument("--only", nargs="+")
    ap.add_argument("-j", "--jobs", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=TIMEOUT)
    args = ap.parse_args(argv)
    try:
        runs = cases(args.cases, args.only)
        summary = compare(root, runs, args.before, args.jobs, args.timeout, git)
    except (Unreadable, RLR.Unreadable) as e:
        print(json.dumps({"ok": False, "reason": str(e)}))
        return 2
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
