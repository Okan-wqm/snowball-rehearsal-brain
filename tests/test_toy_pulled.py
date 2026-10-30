"""The toy target as ``çek`` would hand it to ``koş``: this brain's own ``targets/toy/units.json`` and
``candidates/toy/`` with the toy's tree (``tests/fixtures/toy-repo``) as git objects (git's format, built by
``referee/tests/git_store.py``), through ``loop.cek.assemble`` (asama-0/01 D1, tohum/26c).

What is proven here: the artifact ``loop.pulled.read`` accepts holds, byte for byte, the brain's ``units.json``
(one unit, the number ``koş`` runs) and all five candidate directories, the ``targets[]`` entry as given, and a
tree that unpacks (``extract_tree``, ``koş``'s rule) to exactly the fixture's files. Not proven here: the
fetch of the real toy repository's objects, and the contained runs over it (asama-0/10a #birim, #merge, #ret).

Run from the brain root: ``python -m unittest discover -s tests -p 'test_toy_pulled.py'``.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))
sys.path.insert(0, os.path.join(ROOT, "referee", "tests"))

from loop import cek as C  # noqa: E402
from loop import pulled as P  # noqa: E402
import git_store as S  # noqa: E402

TOY = os.path.join(ROOT, "tests", "fixtures", "toy-repo")
CANDIDATES = os.path.join(ROOT, "candidates", "toy")
OBJECTS, COMMIT = S.store(S.from_dir(TOY))
ENTRY = {"id": "toy", "repo": "owner/toy", "kind": "toy", "base_sha": COMMIT, "identifiers": [],
         "excluded_paths": [], "unit_candidates": []}


def files(root: str) -> dict[str, bytes]:
    out = {}
    for dirpath, _, names in os.walk(root):
        for n in names:
            with open(os.path.join(dirpath, n), "rb") as fh:
                out[os.path.relpath(os.path.join(dirpath, n), root).replace(os.sep, "/")] = fh.read()
    return out


class ToyPulled(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="t-toy-pulled-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_the_toy_as_pulled(self):
        out = os.path.join(self.tmp, "pulled")
        summary = json.dumps({"targets": [ENTRY, dict(ENTRY, id="copy", kind="copy")]}).encode()
        C.assemble(ROOT, summary, b"{}", "toy", OBJECTS.__getitem__, COMMIT, out)
        got = P.read(out)
        self.assertEqual(got.target, ENTRY)
        with open(os.path.join(ROOT, "targets", "toy", "units.json"), "rb") as fh:
            self.assertEqual(got.units, json.loads(fh.read()))
        self.assertEqual(len(got.units["units"]), 1)
        brain = files(CANDIDATES)
        self.assertEqual(sorted(got.candidates), ["bad-path", "bad-ratchet", "bad-scope", "bad-test", "good"])
        self.assertEqual({"%s/%s" % (cid, f): data for cid, fs in got.candidates.items() for f, data in fs.items()},
                         brain)
        tree = os.path.join(self.tmp, "tree")
        P.extract_tree(got.tree_tar, tree)
        self.assertEqual(files(tree), files(TOY))


if __name__ == "__main__":
    unittest.main()
