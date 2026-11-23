"""Capture the tool's judgement of every place the mutation library finds in the toy:
``tests/fixtures/toy-mutations.json`` (asama-1/13a, tohum/29za).

The toy is the Founder's own fixture; this script runs the toy's lint on a copy of it, never anything of a real
target. It copies ``tests/fixtures/toy-repo/`` to a fresh directory, links the given ``node_modules`` (installed
from the toy's lock with ``npm ci --ignore-scripts``) into the unit, runs the recipe's ``lint_cmd``
(``targets/toy/units.json``, one source for the command) on the base tree, then for every place of every
operator (``cases.build.propose`` with no limit over the unit's inputs) applies the mutation's diff with the
referee's own ``gate.diffguard.apply``, runs the same command and puts the file back. Each output is read into
the gate's run record by ``runner.lint_record.record``, the reader ``koş`` uses.

The fixture is ``{eslint, node, lint_cmd, base: record, mutations: {mid: {operator, path, line, diff_sha256,
violations}}}``. The tool runs once a tree here (``koş`` runs it three times and compares; whether ESLint is
deterministic on the toy is test 3's fixture, not this one's).

This is how the fixture was made, not what the referee runs: in the loop the lint runs in ``koş``.

Run from the brain root: ``python3 tests/capture_toy_mutations.py NODE_MODULES``.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))

from cases import build as CB  # noqa: E402
from gate import diffguard  # noqa: E402
from runner import lint_record  # noqa: E402

TOY = os.path.join(ROOT, "tests", "fixtures", "toy-repo")
OUT = os.path.join(ROOT, "tests", "fixtures", "toy-mutations.json")


def recipe() -> dict:
    with open(os.path.join(ROOT, "targets", "toy", "units.json"), encoding="utf-8") as fh:
        units = json.load(fh)["units"]
    assert len(units) == 1, "the toy has one unit"
    return units[0]


def toy_files() -> dict[str, bytes]:
    """The toy fixture's files, ``{path: bytes}``; the tests read the same tree by this function."""
    files = {}
    for folder, _, names in os.walk(TOY):
        for name in names:
            path = os.path.join(folder, name)
            with open(path, "rb") as fh:
                files[os.path.relpath(path, TOY).replace(os.sep, "/")] = fh.read()
    return files


def run(cmd: list[str], cwd: str) -> bytes:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, env={"PATH": os.environ["PATH"], "NO_COLOR": "1"}).stdout


def main(argv: list[str]) -> int:
    if len(argv) != 1 or not os.path.isdir(argv[0]):
        sys.stderr.write("usage: python3 tests/capture_toy_mutations.py NODE_MODULES\n")
        return 2
    unit, files = recipe(), toy_files()
    work = tempfile.mkdtemp(prefix="toy-")
    shutil.rmtree(work)
    shutil.copytree(TOY, work)
    os.symlink(os.path.abspath(argv[0]), os.path.join(work, unit["path"], "node_modules"))
    try:
        def lint() -> dict:
            return lint_record.record(run(unit["lint_cmd"], work), work, work)

        base, mutations = lint(), {}
        for mid, mutation in sorted(CB.propose(files, unit["inputs"], "", limit=10 ** 9).items()):
            target = os.path.join(work, mutation["path"])
            with open(target, "wb") as fh:
                fh.write(diffguard.apply(diffguard.parse(mutation["diff"])[0], files[mutation["path"]]))
            mutations[mid] = {"operator": mutation["operator"], "path": mutation["path"], "line": mutation["line"],
                              "diff_sha256": hashlib.sha256(mutation["diff"].encode("utf-8")).hexdigest(),
                              "violations": lint()["violations"]}
            with open(target, "wb") as fh:
                fh.write(files[mutation["path"]])
        assert lint() == base, "the base tree was not put back"
        eslint = run(["node", os.path.join(unit["path"], "node_modules", "eslint", "bin", "eslint.js"), "--version"],
                     work).decode().strip()
        node = run(["node", "--version"], work).decode().strip()
    finally:
        shutil.rmtree(work)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"eslint": eslint, "node": node, "lint_cmd": unit["lint_cmd"], "base": base,
                   "mutations": mutations}, fh, indent=None, sort_keys=True, separators=(",", ":"))
        fh.write("\n")
    print(len(mutations), "mutations captured;", len(base["violations"]), "base violations")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
