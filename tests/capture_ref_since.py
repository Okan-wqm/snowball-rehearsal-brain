"""Capture real git's answers to the ref check's tests: ``tests/fixtures/ref-since-real-git.json``.

``tests/test_founder_ledger.py``'s ``RefSince`` runs on ``git_store.HistoryGit``, a git double, because the
referee's sandbox has no git. This script runs the same tests with ``repos`` building real repositories with real
git (``init``, ``add -A``, ``commit --allow-empty``, ``clone --depth N file://``), and ``ledger.founder`` reading
them with the git first on ``PATH``. Only when every test passes on real git does it write each test's answers (each
check's ``ref_check``, ``filed`` as the index of the commit it names) with git's version; ``RefSince.tearDown`` then
holds the double's answers to them. Run it on a machine with git after changing a ``RefSince`` test or the double.

This is how the fixture was made, not what the referee runs. Run from the brain root:
``python3 tests/capture_ref_since.py``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "referee"))

import test_founder_ledger  # noqa: E402
from loop.gitobj import git_env  # noqa: E402


class RealGit:
    """``Repos.repos`` over real git."""

    @staticmethod
    def git(top: str, *args: str) -> str:
        env = git_env(dict(os.environ))
        env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t.invalid", GIT_COMMITTER_NAME="t",
                   GIT_COMMITTER_EMAIL="t@t.invalid")
        proc = subprocess.run(["git", "-C", top, *args], capture_output=True, env=env, check=True)
        return proc.stdout.decode().strip()

    def init(self, top: str) -> None:
        self.git(top, "init", "-q", "-b", "main")

    def commit(self, top: str) -> str:
        self.git(top, "add", "-A")
        self.git(top, "commit", "-q", "--allow-empty", "-m", "m")
        return self.git(top, "rev-parse", "HEAD")

    def clone(self, top: str, depth: int, dest: str) -> None:
        self.git(os.path.dirname(dest), "clone", "-q", "--depth", str(depth), "file://" + top,
                 os.path.basename(dest))


ANSWERS: dict[str, list] = {}


class OnRealGit(test_founder_ledger.RefSince):
    repos = RealGit()

    def tearDown(self):
        ANSWERS[self._testMethodName] = self.answers


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OnRealGit)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        print("not written: a test failed on real git", file=sys.stderr)
        return 1
    version = subprocess.run(["git", "--version"], capture_output=True, check=True).stdout.decode().strip()
    with open(test_founder_ledger.RefSince.REAL, "w", encoding="utf-8") as fh:
        json.dump({"git": version, "answers": dict(sorted(ANSWERS.items()))}, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
