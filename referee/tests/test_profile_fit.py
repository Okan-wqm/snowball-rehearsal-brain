"""``profile.fit``: each unit candidate's recipe composed from its own npm scripts, judged by ``check_recipe``.

- the composition: unit id, nearest lock and version file, minimal inputs, install-script marks from the lock,
  the image map, the three ``npm --prefix <path> run --silent`` commands;
- the result: one row per candidate in the derivation's order, its reasons exactly ``check_recipe``'s (the one
  judge), the passing paths;
- the command line: ``--units`` writes the first passing recipe and nothing when none passes; exit 0 / 1 / 2;
- the toy target: the composed recipe passes and agrees with ``targets/toy/units.json`` on every field but the
  commands.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import unittest
from contextlib import redirect_stdout

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAIN = os.path.dirname(REFEREE)
sys.path.insert(0, REFEREE)

from profile import fit as F  # noqa: E402
from profile import unit_verify as U  # noqa: E402
from profile_tree import writable_base, write_tree  # noqa: E402
from test_deps_npm import sri, url  # noqa: E402

IMAGE = "node:20.11.1-bookworm-slim@sha256:" + "ab" * 32
IMAGES = {"20.11.1": IMAGE}


def entry(name: str, **extra) -> dict:
    return dict({"version": "1.0.0", "resolved": url(name, "1.0.0"), "integrity": sri(name.encode())}, **extra)


def lock(**packages) -> dict:
    return {"lockfileVersion": 3, "packages": dict({"": {"name": "root"}}, **packages)}


GOOD_SCRIPTS = {"lint": "eslint .", "test": "node --test"}


def package(scripts=None, **fields) -> dict:
    return dict({"name": "p", "version": "1.0.0", "scripts": GOOD_SCRIPTS if scripts is None else scripts}, **fields)


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.base = writable_base("t-fit-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.tree = os.path.join(self.base, "tree")
        write_tree(self.tree, {
            ".nvmrc": "v20.11.1\n",
            "package-lock.json": lock(**{"node_modules/eslint": entry("eslint", bin={"eslint": "bin/eslint.js"}),
                                         "node_modules/esbuild": entry("esbuild", hasInstallScript=True),
                                         "node_modules/a/node_modules/b": entry("b", hasInstallScript=True),
                                         "node_modules/c": entry("c", hasInstallScript=False)}),
            "package.json": package({}, devDependencies={"eslint": "9"}),
            "pkgs/good/package.json": package(),
            "pkgs/nolint/package.json": package({"test": "node --test"}),
            "pkgs/vitest/package.json": package({"lint": "eslint .", "test": "vitest run"},
                                                devDependencies={"vitest": "1"}),
        })


class Compose(Base):
    def test_unit_id(self):
        cases = {".": "root", "pkgs/good": "pkgs-good", "@s/x y": "s-x-y", ".hidden/a": "hidden-a",
                 "a" * 200: "a" * 128, "___": "root"}
        for path, uid in cases.items():
            self.assertEqual(F.unit_id(path), uid, path)
            self.assertTrue(U.UNIT_ID.fullmatch(F.unit_id(path)), path)

    def test_the_recipe_of_a_member_below_the_root_lock(self):
        npm = ["npm", "--prefix", "pkgs/good", "run", "--silent"]
        self.assertEqual(F.compose(self.tree, "pkgs/good", IMAGES), {
            "unit_id": "pkgs-good", "path": "pkgs/good", "inputs": [".nvmrc", "package-lock.json", "pkgs/good"],
            "toolchain": "node@20.11.1", "env_image": IMAGE, "lockfiles": ["package-lock.json"],
            "install_scripts_required": ["node_modules/a/node_modules/b", "node_modules/esbuild"],
            "lint_cmd": npm + ["lint", "--", "--format", "json"], "test_cmd": npm + ["test"],
            "affected_test_cmd": npm + ["test"], "services": [], "limits": {}})

    def test_nearest_files_and_minimal_inputs(self):
        write_tree(self.tree, {"pkgs/good/.node-version": "20.11.2", "pkgs/good/package-lock.json": lock()})
        r = F.compose(self.tree, "pkgs/good", {"20.11.2": "x"})
        self.assertEqual((r["inputs"], r["lockfiles"], r["toolchain"], r["env_image"], r["install_scripts_required"]),
                         (["pkgs/good"], ["pkgs/good/package-lock.json"], "node@20.11.2", "x", []))
        write_tree(self.tree, {"pkgs/good/npm-shrinkwrap.json": lock()})
        self.assertEqual(F.compose(self.tree, "pkgs/good")["lockfiles"], ["pkgs/good/npm-shrinkwrap.json"])
        self.assertEqual(F.compose(self.tree, ".")["inputs"], ["."])

    def test_no_lock_no_version_no_image(self):
        bare = os.path.join(self.base, "bare")
        write_tree(bare, {"x/package.json": package()})
        r = F.compose(bare, "x", IMAGES)
        self.assertEqual((r["lockfiles"], r["toolchain"], r["env_image"], r["inputs"], r["install_scripts_required"]),
                         ([], "node@", "", ["x"], []))
        self.assertEqual(F.compose(self.tree, "pkgs/good", {"20.11.1": 3})["env_image"], "")


class Fit(Base):
    def test_rows_are_check_recipes_reasons_in_the_derivations_order(self):
        report = F.fit(self.tree, None, None, IMAGES)
        paths = [r["path"] for r in report["rows"]]
        self.assertEqual(paths, [".", "pkgs/good", "pkgs/nolint", "pkgs/vitest"])
        for row in report["rows"]:
            recipe = F.compose(self.tree, row["path"], IMAGES)
            self.assertEqual(row["recipe"], recipe)
            self.assertEqual(row["reasons"], U.check_recipe(recipe, None, self.tree), row["path"])
            # Group recipe's plainness (29g) on the composed inputs: every input is plain except the root unit's
            # ".", which 29g refuses and check_recipe accepts (an open divergence, founder-ledger; stated here).
            plain = [r for r in U.vector_check(recipe, {"operating": {}}) if r.startswith("input")]
            self.assertEqual(plain, ["input_not_plain:."] if row["path"] == "." else [], row["path"])
        by = {r["path"]: r["reasons"] for r in report["rows"]}
        self.assertEqual(by["pkgs/good"], [])
        self.assertEqual(by["pkgs/nolint"], ["script_missing:lint_cmd:lint"])
        self.assertEqual(by["pkgs/vitest"], ["script_not_installed:test_cmd:vitest",
                                             "script_not_installed:affected_test_cmd:vitest"])
        self.assertEqual(by["."], ["script_missing:lint_cmd:lint", "script_missing:test_cmd:test",
                                   "script_missing:affected_test_cmd:test"])
        self.assertEqual((report["candidates"], report["fit"]), (4, ["pkgs/good"]))

    def test_the_operators_order_and_an_ineligible_candidate(self):
        target = {"id": "t", "unit_candidates": ["pkgs/vitest", "pkgs/none", "pkgs/good"]}
        report = F.fit(self.tree, target, None, IMAGES)
        self.assertEqual([r["path"] for r in report["rows"]], ["pkgs/vitest", "pkgs/none", "pkgs/good"])
        self.assertIn("profile:units[0]:unit_not_eligible:pkgs/none", report["rows"][1]["reasons"])

    def test_without_an_image_the_tree_reasons_still_show(self):
        by = {r["path"]: r["reasons"] for r in F.fit(self.tree)["rows"]}
        self.assertEqual(by["pkgs/good"], ["image_not_pinned"])
        self.assertEqual(by["pkgs/nolint"], ["image_not_pinned", "script_missing:lint_cmd:lint"])


class Cli(Base):
    def run_main(self, *argv) -> tuple[int, dict]:
        out = io.StringIO()
        with redirect_stdout(out):
            code = F.main(list(argv))
        return code, json.loads(out.getvalue().splitlines()[-1])

    def json_file(self, name: str, value) -> str:
        path = os.path.join(self.base, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(value, fh)
        return path

    def test_units_written_with_the_first_passing_recipe(self):
        out = os.path.join(self.base, "units.json")
        write_tree(self.tree, {"pkgs/good2/package.json": package()})
        target = self.json_file("target.json", {"id": "t", "unit_candidates": ["pkgs/nolint", "pkgs/good", ".",
                                                                               "pkgs/good2"]})
        code, report = self.run_main(self.tree, "--images", self.json_file("i.json", IMAGES), "--target", target,
                                     "--units", out)
        self.assertEqual((code, report["ok"], report["fit"]), (0, True, ["pkgs/good", "pkgs/good2"]))
        with open(out, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), {"units": [F.compose(self.tree, "pkgs/good", IMAGES)]})

    def test_nothing_written_when_none_passes(self):
        out = os.path.join(self.base, "units.json")
        target = self.json_file("target.json", {"id": "t", "unit_candidates": ["pkgs/nolint", "pkgs/vitest"]})
        code, report = self.run_main(self.tree, "--images", self.json_file("i.json", IMAGES), "--target", target,
                                     "--units", out)
        self.assertEqual((code, report["ok"], report["fit"], report["candidates"]), (1, False, [], 2))
        self.assertFalse(os.path.lexists(out))

    def test_unusable_input(self):
        bad = [(), ("--images",), (self.tree, "--images"), (self.tree, "--other", "x"),
               (self.tree, "--images", "x", "--images", "y"), ("--units", "x", self.tree),
               (self.tree, "--images", self.json_file("l.json", [1])),
               (self.tree, "--target", self.json_file("t.json", "t")),
               (self.tree, "--policy", os.path.join(self.base, "missing.json")),
               (self.tree, "--images", self.json_file("n.json", "{")),
               (os.path.join(self.base, "no-tree"),)]
        for argv in bad:
            code, report = self.run_main(*argv)
            self.assertEqual((code, report["ok"]), (2, False), argv)
            self.assertIn("error", report)


class ToyTarget(unittest.TestCase):
    def test_the_toy_unit_fits_and_agrees_with_its_units_json(self):
        with open(os.path.join(BRAIN, "targets", "toy", "units.json"), encoding="utf-8") as fh:
            toy = json.load(fh)["units"][0]
        version = toy["toolchain"].split("@", 1)[1]
        report = F.fit(os.path.join(BRAIN, "tests", "fixtures", "toy-repo"), None, None,
                       {version: toy["env_image"]})
        self.assertEqual(report["fit"], ["textkit"])
        recipe = report["rows"][0]["recipe"]
        for field in U.RECIPE_FIELDS:
            if field not in U.CMD_FIELDS:
                self.assertEqual(recipe[field], toy[field], field)


if __name__ == "__main__":
    unittest.main()
