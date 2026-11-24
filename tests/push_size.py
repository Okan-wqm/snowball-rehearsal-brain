"""Measure the diff a push hands the rival, before the push, and place it against the limit the referee states.

Why: 6820381 (founder ledger f1216) and dd8afd5 (f2136) were rejected ``rival_unresolved`` with ref
``prompt_too_large``: the rival's artefact is the whole diff since the last accepted SHA (tohum/29b "Rakip
çağrısı"), and each time about 800 KB of it were rows of a mutant record that a whole run rewrites. After the
first this tool existed and judged by two sizes kept by hand, and no step ran it; ``tests/prepush.py check`` now
does. Run from anywhere: ``python3 tests/push_size.py [--base REV] [--result PATH] [--head REV] [--top N]``.

What it does, each rule bound by ``tests/test_push_size.py``:

- **The base** is ``--base``, or without it ``state.last_accepted_sha`` of the referee's result at ``--result``
  (default ``/work/referee/result.json``): a result that cannot be read as a JSON object holding that field as a
  40 character lowercase hex string is unreadable. **The head** is ``--head`` (default ``HEAD``): a commit, not
  the work tree, so the measure is taken after the commit and before the push.
- **The measure** is ``git diff --no-renames --no-ext-diff --no-textconv --no-color --binary <base> <head>``
  over the whole tree except the founder records at the root, ``founder-ledger.jsonl`` and ``reports/``
  (``EXCLUDED``; tohum/29e "Kurucu kayıtları": the rival sees neither; a ``reports/`` directory that is not at
  the root is measured). ``bytes`` is its byte count; ``chars`` is its count of Unicode code points read as
  UTF-8, a byte that is not UTF-8 counted as one (tohum/29b counts the prompt in code points).
- **Per path**: a line of the diff is git's, bytes up to and with a line feed (a carriage return or any other
  byte ends none). A line that starts with ``diff --git `` opens a section; one equal, byte for byte, to the line
  that opened the section before it continues that section (git writes a path whose type changed, a file to a
  symlink, as a deletion and a creation under one such line). The sections are named, in order, by ``git diff
  --name-only -z`` with the same arguments; when the two counts differ, or bytes come before the first section,
  the diff is unreadable (``sections_mismatch``) rather than named by guess. ``paths`` holds the ``--top``
  (default 5) largest, ``[path, bytes]``, largest first, equal sizes in path order.
- **The limit** is the referee's own (tohum/29b: every result's ``rival`` record carries ``prompt_max_chars``,
  ``prompt_chars`` and ``prompt_diff_chars``). From the result at ``--result`` (read for the limit also when
  ``--base`` is given): ``max_chars`` is ``rival.prompt_max_chars`` and ``around_chars`` is ``prompt_chars``
  less ``prompt_diff_chars``, the part of that prompt that was not diff; ``limit_from`` is ``result``. The three
  are taken only when each is an integer (no boolean), the limit above 0 and ``0 <= prompt_diff_chars <=
  prompt_chars``; from any other result (not there, not JSON, no ``rival``, a number null) they are ``KEPT``,
  the numbers of the last result this tool's author read that had them, and ``limit_from`` is ``kept``.
- **The band**: ``fits`` when the diff names no file (nothing is handed to the rival), or when ``chars`` plus
  ``RESERVE`` (2) times ``around_chars`` is at most ``max_chars``; ``over`` when ``chars`` plus ``around_chars``
  is above ``max_chars`` (the last prompt's surroundings alone put it past the limit); ``tight`` between the
  two. ``allowed_chars`` is ``max_chars`` less ``RESERVE`` times ``around_chars``.
- One JSON line: ``ok`` (the band is ``fits``), ``base``, ``head``, ``bytes``, ``chars``, ``files``, ``band``,
  ``max_chars``, ``around_chars``, ``allowed_chars``, ``limit_from``, ``paths``. Exit 0 when ok, 1 when not, 2
  when the base, git or the diff cannot be read (``{"ok": false, "reason"}``).

Out of scope, stated: ``fits`` is a prediction, not the referee's answer. The part of the prompt that is not
diff (the seat's text, the protocol, the changed paths, the pages found relevant, the open claims) is the
referee's to build and changes from push to push; it is taken from the last result, and ``RESERVE`` is a margin
chosen from two observations of it (71298 on d01e1e7, f1294; 88651 on dd8afd5, f2136), not a bound: a push whose
surroundings more than double is refused by the referee though ``fits`` here. How the referee counts a byte
that is not UTF-8 is not known here; on dd8afd5 its ``prompt_diff_chars`` and this tool's ``chars`` were both
880904. The work tree's uncommitted changes are not measured. The diff is read as git's patch format with the
caller's git configuration: a setting that changes its bytes changes the measure, and one that writes a path
without a ``diff --git `` line (``diff.submodule=log``) ends in ``sections_mismatch``. ``KEPT`` is changed by
hand, with the ledger row of the result it was read from, when a result shows other numbers.
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
# tohum/29b: the rival is handed a --binary diff; agent_run.packet writes the reviewer's by the same arguments
DIFF = ("diff", "--no-renames", "--no-ext-diff", "--no-textconv", "--no-color", "--binary")
SECTION = b"diff --git "
SHA = re.compile(r"[0-9a-f]{40}")
FITS, TIGHT, OVER = "fits", "tight", "over"
RESERVE = 2  # times the last prompt's part that was not diff (module docstring, "The band" and "Out of scope")
# (prompt_max_chars, prompt_chars - prompt_diff_chars, the head of the result, the ledger row that read it)
KEPT = (600000, 88651, "dd8afd5", "f2136")


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


def _cut(root: str, base: str, head: str, git: str = "git") -> list[tuple[str, int, int]]:
    """``(path, bytes, chars)`` of each path's section of the diff, in the diff's order (module docstring)."""
    diff = _git(root, git, *DIFF, base, head)
    names = [n for n in _git(root, git, *DIFF, "--name-only", "-z", base, head).decode(
        "utf-8", "surrogateescape").split("\0") if n]
    sizes: list[list[int]] = []
    opened = None
    for line in io.BytesIO(diff):  # git's lines: cut after each LF and nowhere else
        if line.startswith(SECTION):
            if line != opened:
                sizes.append([0, 0])
            opened = line
        elif not sizes:
            raise Unreadable("sections_mismatch")
        sizes[-1][0] += len(line)
        # No UTF-8 sequence holds a line feed, so the lines' code points add up to the diff's.
        sizes[-1][1] += len(line.decode("utf-8", "surrogateescape"))
    if len(sizes) != len(names):
        raise Unreadable("sections_mismatch")
    return [(name, size[0], size[1]) for name, size in zip(names, sizes)]


def sections(root: str, base: str, head: str, git: str = "git") -> list[tuple[str, int]]:
    """``(path, bytes)`` of each path's section of the diff, in the diff's order (module docstring)."""
    return [(name, size) for name, size, _ in _cut(root, base, head, git)]


def _count(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def limit_of(result: str) -> tuple[int, int, str]:
    """``(max_chars, around_chars, limit_from)`` (module docstring, "The limit")."""
    try:
        with open(result, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError, RecursionError):
        doc = None
    rival = doc.get("rival") if isinstance(doc, dict) else None
    most, whole, diff = (_count(rival.get(key)) if isinstance(rival, dict) else None
                         for key in ("prompt_max_chars", "prompt_chars", "prompt_diff_chars"))
    if most is None or whole is None or diff is None or most <= 0 or not 0 <= diff <= whole:
        return KEPT[0], KEPT[1], "kept"
    return most, whole - diff, "result"


def band(chars: int, files: int, most: int, around: int) -> str:
    """The band of a diff of ``chars`` code points over ``files`` paths (module docstring, "The band")."""
    if files == 0 or chars + RESERVE * around <= most:
        return FITS
    return OVER if chars + around > most else TIGHT


def measure(root: str, base: str, head: str, top: int = 5, git: str = "git", result: str = RESULT) -> dict:
    parts = _cut(root, base, head, git)
    chars = sum(n for _, _, n in parts)
    most, around, source = limit_of(result)
    name = band(chars, len(parts), most, around)
    return {"ok": name == FITS, "base": base, "head": head, "bytes": sum(n for _, n, _ in parts), "chars": chars,
            "files": len(parts), "band": name, "max_chars": most, "around_chars": around,
            "allowed_chars": most - RESERVE * around, "limit_from": source,
            "paths": [[p, n] for p, n, _ in sorted(parts, key=lambda p: (-p[1], p[0]))[:top]]}


def main(argv: list[str] | None = None, root: str = ROOT, git: str = "git") -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base")
    ap.add_argument("--result", default=RESULT)
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--top", type=int, default=5)
    args = ap.parse_args(argv)
    try:
        base = args.base if args.base is not None else base_of(args.result)
        out = measure(root, base, args.head, args.top, git, args.result)
    except Unreadable as e:
        print(json.dumps({"ok": False, "reason": str(e)}))
        return 2
    print(json.dumps(out, sort_keys=True))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
