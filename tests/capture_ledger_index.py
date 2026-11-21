"""Capture what the capsule's ledger index answers about the lessons in force of a small ledger made here:
``tests/fixtures/ledger-index-lessons.json``.

The evidence of rule 1 of ``tests/lesson_recheck.py``: the tool takes the lessons in force from the index
(``/opt/founder/ledger_index.py``, which is in a session's capsule and not in the referee's sandbox), and
``tests/test_lesson_recheck.py`` replays the bytes captured here as that program. The ledger is a chain built
with ``ledger.founder.next_row``: ``LESSONS`` lessons, of which the second is closed by a later row, the third
is named by ``closes:`` in an earlier row only (which does not close it, tohum/26g) and the fourth is closed
twice; so more lessons stay in force than one page of the index holds, and the capture follows ``next``. The
fixture is ``{index_sha256, fold, ledger, in_force, pages: [{more, exit, stdout}], absent: {exit, stdout}}``;
``in_force`` is the row ids this script expects by tohum/26g's rule, written before the index is asked, and the
script fails if the index disagrees.

This is how the fixture was made, not what the referee runs. Run from the brain root, in a session:
``python3 tests/capture_ledger_index.py``; ``| cmp - tests/fixtures/ledger-index-lessons.json`` with ``--stdout``
says whether the index still answers as captured.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import lesson_recheck as L  # noqa: E402

F = L.F
OUT = os.path.join(ROOT, "tests", "fixtures", "ledger-index-lessons.json")
LESSONS = 46
SNAPSHOT = "0" * 40
NAME = "ledger.jsonl"


def ledger() -> tuple[bytes, list[str]]:
    """The ledger's bytes and the row ids of its lessons in force, oldest first."""
    data = b""
    n = 0

    def add(kind: str, refs: list[str], recheck: str | None = None) -> str:
        nonlocal data, n
        n += 1
        row = F.next_row(data, kind, "row %d of the capture" % n, refs, SNAPSHOT,
                         "2026-01-01T00:00:%02dZ" % (n % 60), recheck=recheck)
        data += F.line_of(row)
        return row["row_id"]

    add("session_start", ["tests/lesson_recheck.py"])
    add("decision", ["closes:f5"])  # names the third lesson before it is written: does not close it
    lessons = [add("lesson", ["tests/lesson_recheck.py"], "true" if i % 2 else "none: a habit")
               for i in range(LESSONS)]
    add("decision", ["closes:" + lessons[1]])
    add("build", ["closes:" + lessons[3], "tests/lesson_recheck.py"])
    add("decision", ["closes:" + lessons[3]])
    add("seed_issue", ["spec/tohum/26g-semalar-kurucu-dersi.md:21"])
    return data, [x for i, x in enumerate(lessons) if i not in (1, 3)]


def ask(work: str, more: list[str], name: str = NAME) -> dict:
    run = subprocess.run([sys.executable, "-I", L.INDEX, *L.FOLD, "--ledger", name, *more], cwd=work,
                         stdin=subprocess.DEVNULL, capture_output=True)
    return {"more": more, "exit": run.returncode, "stdout": run.stdout.decode("utf-8")}


def main(argv: list[str]) -> int:
    data, expected = ledger()
    work = tempfile.mkdtemp(prefix="ledger-index-")
    try:
        with open(os.path.join(work, NAME), "wb") as fh:
            fh.write(data)
        pages, more, got = [], [], []
        while True:
            page = ask(work, more)
            pages.append(page)
            lines = [json.loads(line) for line in page["stdout"].splitlines()]
            got += [row["row_id"] for row in lines[1:]]
            if lines[0]["next"] is None:
                break
            more = shlex.split(lines[0]["next"])
        absent = ask(work, [], "absent.jsonl")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if got != expected:
        print("the index's lessons in force are not tohum/26g's: %r != %r" % (got, expected), file=sys.stderr)
        return 1
    with open(L.INDEX, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    doc = {"index_sha256": digest, "fold": list(L.FOLD), "ledger": data.decode("utf-8"), "in_force": expected,
           "pages": pages, "absent": {"exit": absent["exit"], "stdout": absent["stdout"]}}
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if argv == ["--stdout"]:
        sys.stdout.write(text)
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(json.dumps({"pages": len(pages), "in_force": len(expected), "out": os.path.relpath(OUT, ROOT)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
