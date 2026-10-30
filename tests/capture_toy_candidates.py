"""Capture the toy candidates' tool outputs: ``tests/fixtures/toy-candidates/<cid>.json`` for each
``candidates/toy/<cid>/`` (asama-0/08 cycle row 2, asama-0/13).

The toy target is the Founder's own fixture (asama-0/08: its candidates may be prepared before (A)); this script
runs the toy's lint and tests on a copy of it, never anything of a real target. For each candidate it copies
``tests/fixtures/toy-repo/`` to a fresh directory, applies the candidate's ``diff.patch`` with the referee's own
``gate.diffguard.apply``, links the given ``node_modules`` (installed from the toy's lock with ``npm ci
--ignore-scripts``) into the unit, and runs the recipe's ``lint_cmd`` three times and its ``test_cmd`` once, both
read from ``targets/toy/units.json`` (one source for the commands). ESLint's ``filePath`` root is rewritten to
``/work``, the container's worktree (asama-0/01). The base tree's output is ``tests/fixtures/toy-repo-eslint.json``
(captured the same way, session 36); the script checks that it still reproduces.

This is how the fixtures were made, not what the referee runs: in (B) the lint and tests run in ``koş`` (MF3).

Run from the brain root: ``python3 tests/capture_toy_candidates.py NODE_MODULES``.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))

from gate import diffguard  # noqa: E402

TOY = os.path.join(ROOT, "tests", "fixtures", "toy-repo")
CANDIDATES = os.path.join(ROOT, "candidates", "toy")
OUT = os.path.join(ROOT, "tests", "fixtures", "toy-candidates")
BASE_OUTPUT = os.path.join(ROOT, "tests", "fixtures", "toy-repo-eslint.json")
CONTAINER_ROOT = "/work"


def recipe() -> dict:
    with open(os.path.join(ROOT, "targets", "toy", "units.json"), encoding="utf-8") as fh:
        units = json.load(fh)["units"]
    assert len(units) == 1, "the toy has one unit"
    return units[0]


def tree(cid: str | None, node_modules: str, unit: dict) -> tuple[str, dict]:
    """A fresh copy of the toy with the candidate applied; ``{path: sha256}`` of each file the diff changes."""
    work = tempfile.mkdtemp(prefix="toy-")
    shutil.rmtree(work)
    shutil.copytree(TOY, work)
    changed = {}
    if cid is not None:
        with open(os.path.join(CANDIDATES, cid, "diff.patch"), encoding="utf-8") as fh:
            blocks = diffguard.parse(fh.read())
        for block in blocks:
            path = os.path.join(work, block["old"])
            with open(path, "rb") as fh:
                new = diffguard.apply(block, fh.read())
            with open(path, "wb") as fh:
                fh.write(new)
            changed[block["old"]] = hashlib.sha256(new).hexdigest()
    os.symlink(node_modules, os.path.join(work, unit["path"], "node_modules"))
    return work, changed


def run(cmd: list[str], cwd: str, shell_glob: bool = False) -> subprocess.CompletedProcess:
    if shell_glob:  # the recipe's test_cmd carries a shell glob, expanded as a shell would
        out = []
        for part in cmd:
            found = sorted(glob.glob(part, root_dir=cwd)) if "*" in part else []
            out += found or [part]
        cmd = out
    return subprocess.run(cmd, cwd=cwd, capture_output=True, env={"PATH": os.environ["PATH"], "NO_COLOR": "1"})


def capture(cid: str | None, node_modules: str, unit: dict) -> dict:
    work, changed = tree(cid, node_modules, unit)
    try:
        lint = [run(unit["lint_cmd"], work) for _ in range(3)]
        outs = {p.stdout for p in lint}
        assert len(outs) == 1, "%s: the three lint runs differ" % cid
        stdout = lint[0].stdout.decode("utf-8").replace(json.dumps(work)[1:-1], CONTAINER_ROOT)
        test = run(unit["test_cmd"], work, shell_glob=True)
        version = run(["node", os.path.join(unit["path"], "node_modules", "eslint", "bin", "eslint.js"), "--version"],
                      work).stdout.decode().strip()
        node = run(["node", "--version"], work).stdout.decode().strip()
    finally:
        shutil.rmtree(work)
    return {"candidate": cid, "eslint": version, "node": node, "lint_cmd": unit["lint_cmd"],
            "lint_exit": lint[0].returncode, "lint_runs_identical": 3, "lint_stdout": stdout,
            "test_cmd": unit["test_cmd"], "test_exit": test.returncode, "test_stdout": test.stdout.decode("utf-8"),
            "changed_sha256": changed}


def main(argv: list[str]) -> int:
    if len(argv) != 1 or not os.path.isdir(argv[0]):
        sys.stderr.write("usage: python3 tests/capture_toy_candidates.py NODE_MODULES\n")
        return 2
    unit = recipe()
    base = capture(None, os.path.abspath(argv[0]), unit)
    with open(BASE_OUTPUT, encoding="utf-8") as fh:
        assert json.loads(base["lint_stdout"]) == json.load(fh), "the base output no longer reproduces"
    os.makedirs(OUT, exist_ok=True)
    for cid in sorted(os.listdir(CANDIDATES)):
        got = capture(cid, os.path.abspath(argv[0]), unit)
        with open(os.path.join(OUT, cid + ".json"), "w", encoding="utf-8") as fh:
            json.dump(got, fh, indent=1, sort_keys=True)
            fh.write("\n")
        print(cid, "lint exit", got["lint_exit"], "test exit", got["test_exit"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
