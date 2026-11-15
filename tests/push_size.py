"""Measure the diff a push hands the rival, before the push, and place it against the sizes the referee has answered.

Why: 6820381 was rejected ``rival_unresolved`` with ref ``prompt_too_large`` (founder ledger f1216): the rival's
artefact is the whole diff since the last accepted SHA (tohum/29b "Rakip çağrısı"), and that diff was 875761 bytes
by this tool, 820062 of them rows of a mutant record that a whole run rewrites. Nothing here measured a push's
size before it left. Run from anywhere: ``python3 tests/push_size.py [--base REV | --result PATH] [--head REV]
[--top N]``.

What it does, each rule bound by ``tests/test_push_size.py``:

- **The base** is ``--base``, or without it ``state.last_accepted_sha`` of the referee's result at ``--result``
  (default ``/work/referee/result.json``): a result that cannot be read as a JSON object holding that field as a
  40 character lowercase hex string is unreadable. **The head** is ``--head`` (default ``HEAD``): a commit, not
  the work tree, so the measure is taken after the commit and before the push.
- **The measure** is the byte count of ``git diff --no-renames --no-ext-diff --no-textconv --no-color <base>
  <head>`` over the whole tree except the founder records at the root, ``founder-ledger.jsonl`` and ``reports/``
  (``EXCLUDED``; tohum/29e "Kurucu kayıtları": the rival sees neither; a ``reports/`` directory that is not at
  the root is measured).
- **Per path**: a line of the diff is git's, bytes up to and with a line feed (a carriage return or any other
  byte ends none). A line that starts with ``diff --git `` opens a section; one equal, byte for byte, to the line
  that opened the section before it continues that section (git writes a path whose type changed, a file to a
  symlink, as a deletion and a creation under one such line). The sections are named, in order, by ``git diff
  --name-only -z`` with the same arguments; when the two counts differ, or bytes come before the first section,
  the diff is unreadable (``sections_mismatch``) rather than named by guess. ``paths`` holds the ``--top``
  (default 5) largest, ``[path, bytes]``, largest first, equal sizes in path order.
- **The band** places the measure against ``MEASURED``, the one list of sizes this tool measured for diffs the
  referee answered: ``accepted_before`` when it is at most the largest accepted size, ``refused_before`` when it
  is at least the smallest refused size, ``unknown`` between the two.
- One JSON line: ``ok`` (the band is ``accepted_before``), ``base``, ``head``, ``bytes``, ``files``, ``band``,
  ``largest_accepted``, ``smallest_refused``, ``paths``. Exit 0 when ok, 1 when not, 2 when the result, git or
  the diff cannot be read (``{"ok": false, "reason"}``).

Out of scope, stated: the referee's limit is not known here, and its prompt is not this diff alone (it adds the
seed pages it finds relevant and its own framing, and its diff's format is its own); ``accepted_before`` says a
diff at least this large, measured the same way, was once judged, not that this one will be, and ``unknown`` is
unknown. The work tree's uncommitted changes are not measured. The diff is
read as git's patch format with the caller's git configuration: a setting that changes its bytes changes the
measure, and one that writes a path without a ``diff --git `` line (``diff.submodule=log``) ends in
``sections_mismatch``. A new answer from the referee is a new row of
``MEASURED``, added by hand with the ledger row that holds its evidence.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULT = "/work/referee/result.json"
EXCLUDED = ("founder-ledger.jsonl", "reports")
DIFF = ("diff", "--no-renames", "--no-ext-diff", "--no-textconv", "--no-color")
SECTION = b"diff --git "
SHA = re.compile(r"[0-9a-f]{40}")
ACCEPTED, REFUSED, UNKNOWN = "accepted_before", "refused_before", "unknown"
# (base, head, bytes by this tool, the referee's answer, the ledger row of the answer)
MEASURED = (
    ("63811d2", "dab6f8b", 456483, "accepted", "f1107"),
    ("bb80d93", "6820381", 875761, "prompt_too_large", "f1216"),
)


class Unreadable(Exception):
    """The result, git or the diff cannot be read; the message is the reason."""


def base_of(result: str) -> str:
    """``state.last_accepted_sha`` of the referee's result at ``result`` (module docstring)."""
    try:
        with open(result, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError, RecursionError):
        raise Unreadable("result_unreadable") from None
    state = doc.get("state") if isinstance(doc, dict) else None
    sha = state.get("last_accepted_sha") if isinstance(state, dict) else None
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise Unreadable("no_last_accepted_sha")
    return sha


def _git(root: str, git: str, *args: str) -> bytes:
    spec = [".", *(":(top,exclude)" + name for name in EXCLUDED)]
    try:
        proc = subprocess.run([git, "-C", root, *args, "--", *spec], stdin=subprocess.DEVNULL, capture_output=True)
    except OSError:
        raise Unreadable("git_unavailable") from None
    if proc.returncode != 0:
        raise Unreadable("diff_failed:%d" % proc.returncode)
    return proc.stdout


def sections(root: str, base: str, head: str, git: str = "git") -> list[tuple[str, int]]:
    """``(path, bytes)`` of each path's section of the diff, in the diff's order (module docstring)."""
    diff = _git(root, git, *DIFF, base, head)
    names = [n for n in _git(root, git, *DIFF, "--name-only", "-z", base, head).decode(
        "utf-8", "surrogateescape").split("\0") if n]
    sizes: list[int] = []
    opened = None
    for line in io.BytesIO(diff):  # git's lines: cut after each LF and nowhere else
        if line.startswith(SECTION):
            if line != opened:
                sizes.append(0)
            opened = line
        elif not sizes:
            raise Unreadable("sections_mismatch")
        sizes[-1] += len(line)
    if len(sizes) != len(names):
        raise Unreadable("sections_mismatch")
    return list(zip(names, sizes))


def band(size: int, measured: tuple = MEASURED) -> tuple[str, int | None, int | None]:
    """``(band, largest accepted, smallest refused)`` of ``size`` against ``measured`` (module docstring); a
    side with no row is ``None`` and decides nothing."""
    accepted = max((row[2] for row in measured if row[3] == "accepted"), default=None)
    refused = min((row[2] for row in measured if row[3] != "accepted"), default=None)
    if accepted is not None and size <= accepted:
        return ACCEPTED, accepted, refused
    if refused is not None and size >= refused:
        return REFUSED, accepted, refused
    return UNKNOWN, accepted, refused


def measure(root: str, base: str, head: str, top: int = 5, git: str = "git") -> dict:
    parts = sections(root, base, head, git)
    size = sum(n for _, n in parts)
    name, accepted, refused = band(size)
    return {"ok": name == ACCEPTED, "base": base, "head": head, "bytes": size, "files": len(parts), "band": name,
            "largest_accepted": accepted, "smallest_refused": refused,
            "paths": [list(p) for p in sorted(parts, key=lambda p: (-p[1], p[0]))[:top]]}


def main(argv: list[str] | None = None, root: str = ROOT, git: str = "git") -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    where = ap.add_mutually_exclusive_group()
    where.add_argument("--base")
    where.add_argument("--result", default=RESULT)
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args(argv)
    try:
        base = args.base if args.base is not None else base_of(args.result)
        out = measure(root, base, args.head, args.top, git)
    except Unreadable as e:
        print(json.dumps({"ok": False, "reason": str(e)}))
        return 2
    print(json.dumps(out, sort_keys=True))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
