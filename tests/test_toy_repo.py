"""The toy target fixture (``tests/fixtures/toy-repo/``) and its unit recipe proposal (``targets/toy/units.json``)
against the referee's own static checks (asama-0/01, asama-0/08 cycle rows 1-2, asama-0/13, tohum/25a rows 2 and 6,
tohum/26c's recipe).

What is proven here, from the committed bytes and without running the fixture's code: MF4 derives one eligible
JavaScript unit, the security paths, no agent configuration and no excluded directory; MF6's static check (which
calls MF4 and MF5's lock check) passes every proposed recipe on this tree, and group ``recipe``'s check passes it;
the recipe's facts agree with the tree (version file, image tag, lock, the lint tool's path under the unit's
``node_modules``, test files matching ``test_cmd``); MF7 lets a one-line change of a plain source file through and
refuses each of the toy's forbidden kinds of path, and ``gate.diffguard.apply`` applies such a change to the base
file. Not proven here (no node in this sandbox): that ESLint finds fixable violations and the tests are green 3/3;
that is asama-0/10a #birim, run by the referee in ``koş``.

Run from the brain root: ``python -m unittest discover -s tests -p 'test_toy_repo.py'``.
"""

from __future__ import annotations

import fnmatch
import json
import os
import posixpath
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))

from gate import diffguard  # noqa: E402
from profile import derive as D  # noqa: E402
from profile import unit_verify as U  # noqa: E402
from runner import deps_npm as N  # noqa: E402

TOY = os.path.join(ROOT, "tests", "fixtures", "toy-repo")
UNITS = os.path.join(ROOT, "targets", "toy", "units.json")
# group recipe's check needs policy.operating; every key with a valid value and band, so that only the recipe is judged
POLICY = {"operating": {k: {"value": 1 << 30, "band": [1, 1 << 40]} for k in U.OPERATING_NAMES}}


def recipes() -> list[dict]:
    with open(UNITS, encoding="utf-8") as fh:
        return json.load(fh)["units"]


def read(rel: str) -> bytes:
    with open(os.path.join(TOY, rel), "rb") as fh:
        return fh.read()


def walk() -> list[str]:
    out = []
    for top, dirs, files in os.walk(TOY):
        dirs.sort()
        out += [os.path.relpath(os.path.join(top, f), TOY).replace(os.sep, "/") for f in files]
    return sorted(out)


def one_line_diff(path: str, line: int, new: str) -> str:
    """The diff git writes with -U0 for replacing line ``line`` of the toy's ``path`` by ``new``."""
    old = read(path).decode("utf-8").split("\n")[line - 1]
    return "diff --git a/{p} b/{p}\n--- a/{p}\n+++ b/{p}\n@@ -{n} +{n} @@\n-{o}\n+{w}\n".format(
        p=path, n=line, o=old, w=new)


class Derivation(unittest.TestCase):
    def setUp(self):
        self.derived = D.derive(TOY, None, None)

    def test_one_eligible_javascript_unit(self):
        self.assertEqual(self.derived["languages"], {"javascript": {"files": 9}})
        self.assertEqual(self.derived["unit_candidates"], [{"path": "textkit", "eligible": True, "reasons": []}])

    def test_security_paths_by_keyword(self):
        self.assertEqual(self.derived["security_paths"],
                         ["textkit/src/permissions.js", "textkit/test/permissions.test.js"])

    def test_no_agent_configuration_no_excluded_directory(self):
        # asama-0/13: the toy carries no agent configuration; dependencies are fetched, never committed
        self.assertEqual(self.derived["excluded_paths"], [])
        self.assertEqual(self.derived["excluded_dirs"], [])

    def test_no_workflow(self):
        # tohum/25a row 6: the toy has no workflow
        self.assertFalse(os.path.lexists(os.path.join(TOY, ".github")))

    def test_tests_are_recognised(self):
        self.assertIn("**/*.test.*", self.derived["test_path_rules"])


class Recipe(unittest.TestCase):
    def test_static_check_passes_on_the_tree(self):
        units = recipes()
        self.assertTrue(units)
        for recipe in units:
            self.assertEqual(U.check_recipe(recipe, POLICY, TOY, None), [], recipe["unit_id"])
            self.assertEqual(U.vector_check(recipe, POLICY), [], recipe["unit_id"])

    def test_recipe_agrees_with_the_tree(self):
        for recipe in recipes():
            version = U.TOOLCHAIN.fullmatch(recipe["toolchain"]).group(1)
            _, text = U.nearest_version(TOY, recipe["path"])
            self.assertEqual(text, version)
            self.assertIn(":%s-" % version, recipe["env_image"])
            lock_rel, = recipe["lockfiles"]
            lock = json.loads(read(lock_rel))
            lock_dir = posixpath.dirname(lock_rel)
            # the lint tool is run from where MF6 unpacks the locked packages: <lock dir>/<lock key>/
            tool = recipe["lint_cmd"][1]
            self.assertEqual(recipe["lint_cmd"][0], "node")
            self.assertTrue(tool.startswith(lock_dir + "/node_modules/"), tool)
            key = tool[len(lock_dir) + 1:].split("/bin/")[0]
            self.assertIn(key, lock["packages"])
            self.assertEqual(lock["packages"][""]["devDependencies"][key.split("node_modules/")[-1]],
                             lock["packages"][key]["version"])
            # the lock was written from the committed manifest (npm keeps both lists in the root entry)
            manifest = json.loads(read(posixpath.join(recipe["path"], "package.json")))
            for field in ("dependencies", "devDependencies"):
                self.assertEqual(manifest.get(field), lock["packages"][""].get(field), field)
            # every test command matches at least one committed test file
            for field in ("test_cmd", "affected_test_cmd"):
                pattern = recipe[field][-1]
                self.assertTrue([rel for rel in walk() if fnmatch.fnmatchcase(rel, pattern)], field)

    def test_lock_passes_mf5_without_install_scripts(self):
        for recipe in recipes():
            lock = json.loads(read(recipe["lockfiles"][0]))
            self.assertEqual(lock["lockfileVersion"], 3)
            report = N.check(lock, N.DEFAULT_REGISTRIES, recipe["install_scripts_required"])
            self.assertEqual(report["reasons"], [])
            marked = sorted(k for k, v in lock["packages"].items() if v.get("hasInstallScript"))
            self.assertEqual(marked, sorted(recipe["install_scripts_required"]))


class Diffguard(unittest.TestCase):
    def setUp(self):
        self.profile = D.derive(TOY, None, None)
        self.recipe = recipes()[0]

    def test_plain_source_change_passes_and_applies(self):
        diff = one_line_diff("textkit/src/slug.js", 2, "  const lower = text.toLowerCase();")
        self.assertEqual(diffguard.check(diff, self.profile, self.recipe), [])
        block, = diffguard.parse(diff)
        before = read("textkit/src/slug.js").decode("utf-8").split("\n")
        after = diffguard.apply(block, read("textkit/src/slug.js")).decode("utf-8").split("\n")
        self.assertEqual(len(after), len(before))
        self.assertEqual([i for i, (a, b) in enumerate(zip(before, after)) if a != b], [1])

    def test_each_forbidden_kind_of_path_is_refused(self):
        cases = {
            ("textkit/src/permissions.js", 2): "security_path",
            ("textkit/eslint.config.js", 9): "config",
            ("textkit/.nvmrc", 1): "config",
            ("textkit/package.json", 3): "manifest",
            ("textkit/package-lock.json", 3): "lockfile",
            ("README.md", 1): "outside_inputs",
            (".gitignore", 1): "outside_inputs",
        }
        for (path, line), reason in cases.items():
            reasons = diffguard.check(one_line_diff(path, line, "x"), self.profile, self.recipe)
            self.assertIn("%s:%s" % (reason, path), reasons, path)


if __name__ == "__main__":
    unittest.main()
