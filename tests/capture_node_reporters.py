"""Capture what ``node --test`` writes to a stdout that is no terminal, per reporter option:
``tests/fixtures/node-test-reporters.json``.

The evidence of rule 4 of ``tests/recipe_contract.py``: the tool says from a command's text whether
``runner.test_results`` reads its output, and ``tests/test_recipe_contract.py`` holds that answer against the
reader's own answer on the bytes captured here. The script writes one test file of its own (one passing test, one
failing) into a fresh directory and runs the local ``node`` on it once per row of ``CASES`` with stdout a pipe;
nothing of a target is read or run. The fixture is ``{node, major, tests, cases: [{options, exit, stdout}]}``;
``stdout`` is the run's bytes as UTF-8 text (durations and the directory's path are in them as node wrote them).

This is how the fixture was made, not what the referee runs. Run from the brain root with the node to measure on
``PATH``: ``python3 tests/capture_node_reporters.py``; a new major is a new fixture row set and a new entry of
``recipe_contract.NODE_TAP_DEFAULT`` only when the default case's bytes are read.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tests", "fixtures", "node-test-reporters.json")
TESTS = ["alpha passes", "beta fails"]
SOURCE = ('const test = require("node:test");\nconst assert = require("node:assert");\n'
          'test("alpha passes", () => {});\ntest("beta fails", () => { assert.equal(1, 2); });\n')
CASES = (
    [],
    ["--test-reporter=tap"],
    ["--test-reporter", "tap"],
    ["--test-reporter=tap", "--test-reporter-destination=stdout"],
    ["--test-reporter=tap", "--test-reporter-destination", "stdout"],
    ["--test-reporter=spec"],
    ["--test-reporter", "dot"],
    ["--test-reporter=junit"],
    ["--test-reporter=tap", "--test-reporter-destination=out.txt"],
    ["--test-reporter", "tap", "--test-reporter-destination", "out.txt"],
)


def main() -> int:
    version = subprocess.run(["node", "--version"], capture_output=True, check=True).stdout.decode().strip()
    work = tempfile.mkdtemp(prefix="node-reporters-")
    try:
        with open(os.path.join(work, "a.test.js"), "w", encoding="utf-8") as fh:
            fh.write(SOURCE)
        cases = []
        for options in CASES:
            run = subprocess.run(["node", "--test", *options, "a.test.js"], cwd=work, capture_output=True)
            cases.append({"options": options, "exit": run.returncode, "stdout": run.stdout.decode("utf-8")})
    finally:
        shutil.rmtree(work, ignore_errors=True)
    doc = {"node": version, "major": int(version.lstrip("v").split(".")[0]), "tests": TESTS, "cases": cases}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps({"node": version, "cases": len(cases), "out": os.path.relpath(OUT, ROOT)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
