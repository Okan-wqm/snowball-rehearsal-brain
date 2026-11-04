"""``profile.nx``: an Nx project's ``lint`` and ``test`` targets as the commands their executors run, and their use
by ``profile.fit`` when the candidate has no npm script.

- Nx's token rules: ``resolveNxTokensInOptions`` and the lint executor's ``interpolate``, case by case as Nx
  22.7.12's code does them;
- the target's refusals, one reason each: no workspace, a lock below the root, no target, a key, an executor, an
  option, a ``targetDefaults`` entry by executor, name or glob;
- lint: default and explicit patterns, the nearest flat config in Nx's name order, no flat config, ESLint's major;
- test: the command, the config as an input, the missing option;
- fit: the npm script wins, an Nx command is judged by ``check_recipe`` like any other (``.bin`` against the lock),
  ``sources`` says which form each command took.
"""

from __future__ import annotations

import os
import shutil
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from profile import fit as F  # noqa: E402
from profile import nx as X  # noqa: E402
from profile import unit_verify as U  # noqa: E402
from profile_tree import writable_base, write_tree  # noqa: E402
from test_deps_npm import sri, url  # noqa: E402
from test_profile_fit import IMAGES, lock, package  # noqa: E402

LINT = {"executor": "@nx/eslint:lint"}
JEST = {"executor": "@nx/jest:jest", "options": {"jestConfig": "libs/a/jest.config.ts"}}
TS = "TS_NODE_COMPILER_OPTIONS=" + '{"moduleResolution":"Node10","module":"commonjs","customConditions":null}'


def entry(name: str, version: str = "1.0.0", **extra) -> dict:
    """A registry entry MF5 takes, its tarball URL naming ``version``."""
    return dict({"version": version, "resolved": url(name, version), "integrity": sri(name.encode())}, **extra)


def eslint_cmd(config: str, *patterns: str) -> list:
    return ["node_modules/.bin/eslint", "--config", config, "--no-error-on-unmatched-pattern", "--format", "json",
            *patterns]


class Tokens(unittest.TestCase):
    def test_interpolate_as_the_lint_executor(self):
        cases = [("{projectRoot}", "libs/a", "libs/a"), ("{projectRoot}", ".", "."),
                 ("libs/a/src/**/*.{ts,tsx}", "libs/a", "libs/a/src/**/*.{ts,tsx}"),  # no token: as written
                 ("{projectRoot}/src/**/*.{ts,tsx}", "libs/a", "libs/a/src/**/*.{ts,tsx}"),
                 ("{workspaceRoot}/libs/a", "libs/a", "libs/a"), ("./{projectRoot}/", "libs/a", "libs/a"),
                 ("{projectRoot}/../b", "libs/a", "libs/b"), ("{projectRoot}/src", ".", "src"),
                 ("/abs/{projectRoot}", "libs/a", "/abs/{projectRoot}"), ("{projectName}/x", "libs/a", "n/x"),
                 ("{ projectRoot }", "libs/a", "libs/a"), ("{nope}/x", "libs/a", "{nope}/x")]
        for template, root, want in cases:
            self.assertEqual(X.nx_interpolate(template, root, "n"), want, (template, root))
        self.assertEqual(X.nx_interpolate("{projectName}/x", "libs/a", None), "{projectName}/x")
        for template, root, reason in [("a/{workspaceRoot}", "libs/a", "token:workspaceRoot"),
                                       ("src/{projectRoot}", ".", "token:projectRoot")]:
            with self.assertRaises(X.NotComposed) as cm:
                X.nx_interpolate(template, root, "n")
            self.assertEqual(str(cm.exception), reason)

    def test_resolve_tokens_as_nx_options(self):
        self.assertEqual(X.resolve_tokens("{workspaceRoot}/a/{projectRoot}/{projectRoot}", "p", None), "a/p/p")
        self.assertEqual(X.resolve_tokens("{workspaceRoot}x", "p", None), "x")
        self.assertEqual(X.resolve_tokens("{projectName}.js", "p", "n"), "n.js")
        for value, name, reason in [("a/{workspaceRoot}", "n", "token:workspaceRoot"),
                                    ("{projectName}", None, "token:projectName"),
                                    ("{projectName}", "", "token:projectName")]:
            with self.assertRaises(X.NotComposed) as cm:
                X.resolve_tokens(value, "p", name)
            self.assertEqual(str(cm.exception), reason)


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.base = writable_base("t-nx-")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.tree = os.path.join(self.base, "tree")
        write_tree(self.tree, {
            ".nvmrc": "v20.11.1\n",
            "nx.json": {"targetDefaults": {"lint": {"inputs": ["default"], "cache": True},
                                           "test": {"outputs": ["{projectRoot}/coverage"]}}},
            "eslint.config.mjs": "export default [];\n",
            "package-lock.json": lock(**{
                "node_modules/eslint": entry("eslint", "9.39.4", bin={"eslint": "bin/eslint.js"}),
                "node_modules/jest": entry("jest", "30.5.2", bin={"jest": "bin/jest.js"})}),
            "package.json": package({}),
            "libs/a/package.json": package({}, name="@w/a"),
            "libs/a/project.json": {"name": "a", "targets": {"lint": LINT, "test": JEST}},
        })

    def project(self, **targets) -> None:
        write_tree(self.tree, {"libs/a/project.json": {"name": "a", "targets": targets}})

    def refused(self, fn, reason: str, path: str = "libs/a") -> None:
        with self.assertRaises(X.NotComposed) as cm:
            fn(self.tree, path)
        self.assertEqual(str(cm.exception), reason)


class Target(Base):
    def test_no_workspace_or_a_lock_below_the_root(self):
        os.remove(os.path.join(self.tree, "nx.json"))
        self.refused(X.lint, "no_workspace")
        write_tree(self.tree, {"nx.json": "[]"})
        self.refused(X.lint, "no_workspace")
        write_tree(self.tree, {"nx.json": {}, "libs/a/package-lock.json": lock()})
        self.refused(X.lint, "lock_not_at_workspace_root")

    def test_no_target(self):
        self.project(build=LINT)
        self.refused(X.lint, "no_target")
        os.remove(os.path.join(self.tree, "libs/a/project.json"))
        self.refused(X.test, "no_target")
        write_tree(self.tree, {"libs/a/project.json": {"targets": {"lint": "x"}}})
        self.refused(X.lint, "no_target")

    def test_keys_executors_and_options_outside_the_rules(self):
        for spec, reason in [(dict(LINT, dependsOn=["^build"]), "target_key:dependsOn"),
                             (dict(LINT, defaultConfiguration="ci"), "target_key:defaultConfiguration"),
                             (dict(LINT, command="eslint ."), "target_key:command"),
                             ({"executor": "nx:run-commands"}, "executor:nx:run-commands"),
                             ({}, "executor:None"),
                             (dict(LINT, options={"format": "json"}), "option:format"),
                             (dict(LINT, options={"eslintConfig": "x.mjs"}), "option:eslintConfig"),
                             (dict(LINT, options=[]), "option:options")]:
            self.project(lint=spec)
            self.refused(X.lint, reason)
        self.project(lint=dict(LINT, inputs=["default"], outputs=[], cache=True, configurations={"ci": {}}))
        self.assertEqual(X.lint(self.tree, "libs/a")[0], eslint_cmd("eslint.config.mjs", "libs/a"))
        self.project(test=dict(JEST, options={"jestConfig": "j.ts", "ci": True}))
        self.refused(X.test, "option:ci")

    def test_target_defaults_by_executor_then_name_then_longest_glob(self):
        for defaults, reason in [
                ({"@nx/eslint:lint": {"dependsOn": ["^build"]}, "lint": {"cache": True}}, "target_defaults_key:dependsOn"),
                ({"lint": {"options": {"quiet": True}}}, "target_defaults_key:options"),
                ({"l*": {"cache": True}, "li*": {"executor": "x"}}, "target_defaults_key:executor"),
                ({"lint": True}, "target_defaults_key:lint")]:
            write_tree(self.tree, {"nx.json": {"targetDefaults": defaults}})
            self.refused(X.lint, reason)
        # The executor's key wins over the name's, as readTargetDefaultsForTarget reads them.
        write_tree(self.tree, {"nx.json": {"targetDefaults": {"@nx/eslint:lint": {"cache": True},
                                                              "lint": {"dependsOn": ["^build"]}}}})
        self.assertEqual(X.lint(self.tree, "libs/a")[0], eslint_cmd("eslint.config.mjs", "libs/a"))


class Lint(Base):
    def test_default_and_explicit_patterns(self):
        self.assertEqual(X.lint(self.tree, "libs/a"), (eslint_cmd("eslint.config.mjs", "libs/a"),
                                                       ["eslint.config.mjs"]))
        self.project(lint=dict(LINT, options={"lintFilePatterns": ["{projectRoot}/src/**/*.{ts,tsx}",
                                                                    "{workspaceRoot}/libs/a/x.ts", "{projectName}.ts"]}))
        self.assertEqual(X.lint(self.tree, "libs/a")[0],
                         eslint_cmd("eslint.config.mjs", "libs/a/src/**/*.{ts,tsx}", "libs/a/x.ts", "a.ts"))
        for patterns, reason in [([], "option:lintFilePatterns"), ("libs/a", "option:lintFilePatterns"),
                                 ([""], "option:lintFilePatterns"), (["--fix"], "pattern_option"),
                                 (["a/{workspaceRoot}"], "token:workspaceRoot")]:
            self.project(lint=dict(LINT, options={"lintFilePatterns": patterns}))
            self.refused(X.lint, reason)

    def test_the_nearest_flat_config_in_nxs_name_order(self):
        write_tree(self.tree, {"libs/eslint.config.js": "", "libs/eslint.config.cjs": ""})
        self.assertEqual(X.lint(self.tree, "libs/a")[1], ["libs/eslint.config.cjs"])
        write_tree(self.tree, {"libs/a/eslint.config.mts": ""})
        self.assertEqual(X.lint(self.tree, "libs/a")[0][2], "libs/a/eslint.config.mts")
        self.assertEqual(X.flat_config(self.tree, "."), "eslint.config.mjs")

    def test_no_flat_config_or_eslint_before_9(self):
        os.remove(os.path.join(self.tree, "eslint.config.mjs"))
        write_tree(self.tree, {".eslintrc.json": {}})
        self.refused(X.lint, "no_flat_config")
        write_tree(self.tree, {"eslint.config.mjs": ""})
        for version in ("8.57.0", "x", None):
            eslint = entry("eslint", "1.0.0", bin={"eslint": "bin/eslint.js"})
            eslint["version"] = version
            write_tree(self.tree, {"package-lock.json": lock(**{"node_modules/eslint": eslint})})
            self.refused(X.lint, "eslint_version")
        write_tree(self.tree, {"package-lock.json": lock()})
        self.refused(X.lint, "eslint_version")
        write_tree(self.tree, {"package-lock.json": lock(**{"node_modules/eslint": entry("eslint", "10.0.0")})})
        self.assertEqual(X.lint(self.tree, "libs/a")[0][0], "node_modules/.bin/eslint")


class Test(Base):
    def test_the_command_and_its_config_input(self):
        self.assertEqual(X.test(self.tree, "libs/a"),
                         (["env", TS, "node_modules/.bin/jest", "--config", "libs/a/jest.config.ts"],
                          ["libs/a/jest.config.ts"]))
        self.project(test=dict(JEST, options={"jestConfig": "{projectRoot}/jest.config.cts"}))
        self.assertEqual(X.test(self.tree, "libs/a")[0][-1], "libs/a/jest.config.cts")
        self.project(test=dict(JEST, options={"jestConfig": "/abs/jest.config.js"}))
        self.assertEqual(X.test(self.tree, "libs/a"),
                         (["env", TS, "node_modules/.bin/jest", "--config", "/abs/jest.config.js"], []))

    def test_refused(self):
        for options, reason in [({}, "option_missing:jestConfig"), ({"jestConfig": ""}, "option:jestConfig"),
                                ({"jestConfig": 3}, "option:jestConfig"), ({"jestConfig": "-c"}, "pattern_option")]:
            self.project(test=dict(JEST, options=options))
            self.refused(X.test, reason)


class Fit(Base):
    def test_an_nx_recipe_is_judged_like_any_other(self):
        recipe = F.compose(self.tree, "libs/a", IMAGES)
        self.assertEqual((recipe["lint_cmd"], recipe["test_cmd"], recipe["affected_test_cmd"], recipe["inputs"]),
                         (eslint_cmd("eslint.config.mjs", "libs/a"),
                          ["env", TS, "node_modules/.bin/jest", "--config", "libs/a/jest.config.ts"],
                          ["env", TS, "node_modules/.bin/jest", "--config", "libs/a/jest.config.ts"],
                          [".nvmrc", "eslint.config.mjs", "libs/a", "package-lock.json"]))
        row = {r["path"]: r for r in F.fit(self.tree, None, None, IMAGES)["rows"]}["libs/a"]
        self.assertEqual((row["reasons"], row["sources"]), ([], {"lint": "nx_target", "test": "nx_target"}))
        # The lock without jest's bin: check_recipe, the one judge, refuses the .bin path.
        write_tree(self.tree, {"package-lock.json": lock(**{
            "node_modules/eslint": entry("eslint", "9.39.4", bin={"eslint": "bin/eslint.js"})})})
        row = {r["path"]: r for r in F.fit(self.tree, None, None, IMAGES)["rows"]}["libs/a"]
        self.assertEqual(row["reasons"], ["cmd_not_installed:test_cmd:node_modules/.bin/jest",
                                          "cmd_not_installed:affected_test_cmd:node_modules/.bin/jest"])

    def test_the_npm_script_wins_and_sources_say_why(self):
        write_tree(self.tree, {"libs/a/package.json": package({"lint": "eslint ."}, name="@w/a")})
        sources = F.commands(self.tree, "libs/a")["sources"]
        self.assertEqual(sources, {"lint": "npm_script", "test": "nx_target"})
        recipe = F.compose(self.tree, "libs/a", IMAGES)
        self.assertEqual(recipe["lint_cmd"][:3], ["npm", "--prefix", "libs/a"])
        self.assertNotIn("eslint.config.mjs", recipe["inputs"])
        self.project(lint={"executor": "nx:run-commands"})
        write_tree(self.tree, {"libs/a/package.json": package({}, name="@w/a")})
        row = {r["path"]: r for r in F.fit(self.tree, None, None, IMAGES)["rows"]}["libs/a"]
        self.assertEqual(row["sources"], {"lint": "none:executor:nx:run-commands", "test": "none:no_target"})
        self.assertEqual(row["recipe"]["lint_cmd"], ["npm", "--prefix", "libs/a"] + list(F.LINT_CMD))
        self.assertEqual(row["reasons"], U.check_recipe(row["recipe"], None, self.tree))
        self.assertIn("script_missing:lint_cmd:lint", row["reasons"])


if __name__ == "__main__":
    unittest.main()
