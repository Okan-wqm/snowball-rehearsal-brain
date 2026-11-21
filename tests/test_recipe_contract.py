"""``tests/recipe_contract.py``'s rules, each bound by a test below (the rules are listed in its docstring, the one
source), and the check itself on this tree: every command of every ``targets/<id>/units.json`` is ``read``.
Rule 4's fact is held against ``runner.test_results`` on the bytes of ``tests/fixtures/node-test-reporters.json``
(real node, ``tests/capture_node_reporters.py``); no node, jest or ESLint is needed here. Run from the brain's
root."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "referee"))

import recipe_contract as R  # noqa: E402
from profile import fit as F  # noqa: E402
from profile import nx as X  # noqa: E402
from runner import test_results as T  # noqa: E402

JEST = ["node_modules/.bin/jest", "--config", "libs/a/jest.config.json"]
ESLINT = ["node_modules/.bin/eslint", "--config", "eslint.config.mjs"]
NODE20 = "node@20.11.0"


def verdict(field, cmd, toolchain=NODE20):
    answer = R.judge(field, cmd, toolchain)
    return answer["verdict"], answer["reader"], answer["why"]


class Program(unittest.TestCase):
    """Rule 1."""

    def test_no_wrapper(self):
        self.assertEqual(R.program(["a/b/jest", "--json"]), (["a/b/jest", "--json"], ""))

    def test_env_and_its_assignments_go(self):
        for env in R.ENV:
            self.assertEqual(R.program([env, "A=1", "_b9=x=y", "jest", "B=2"]), (["jest", "B=2"], ""))
        self.assertEqual(R.program(["env", "jest"]), (["jest"], ""))

    def test_env_option_is_not_read(self):
        self.assertEqual(R.program(["env", "-i", "jest", "--json"]), (None, "wrapper_not_read"))
        self.assertEqual(R.program(["env", "A=1", "-u", "B", "jest"]), (None, "wrapper_not_read"))

    def test_a_word_that_is_no_assignment_ends_env(self):
        self.assertEqual(R.program(["env", "9A=1", "jest"]), (["9A=1", "jest"], ""))

    def test_the_composed_shell_form_goes(self):
        for sh in R.SH:
            self.assertEqual(R.program([sh, "-c", X.CD_EXEC, "libs/a", "eslint", "."]), (["eslint", "."], ""))

    def test_another_shell_form_is_not_read(self):
        self.assertEqual(R.program(["sh", "-c", "cd libs/a && eslint . --format json"]), (None, "wrapper_not_read"))
        self.assertEqual(R.program(["sh", "-c", X.CD_EXEC + " ", "libs/a", "eslint"]), (None, "wrapper_not_read"))
        self.assertEqual(R.program(["sh", "-e", X.CD_EXEC, "libs/a", "eslint"]), (None, "wrapper_not_read"))
        self.assertEqual(R.program(["sh", "-c", X.CD_EXEC]), (None, "wrapper_not_read"))

    def test_node_before_a_script_goes(self):
        self.assertEqual(R.program(["node", "x/eslint.js", "-f", "json"]), (["x/eslint.js", "-f", "json"], ""))
        self.assertEqual(R.program(["/usr/bin/node", "x/jest.js"]), (["x/jest.js"], ""))

    def test_node_before_an_option_stays(self):
        self.assertEqual(R.program(["node", "--test", "t"]), (["node", "--test", "t"], ""))
        self.assertEqual(R.program(["node"]), (["node"], ""))

    def test_wrappers_nest(self):
        cmd = ["env", "A=1", "/bin/sh", "-c", X.CD_EXEC, "d", "env", "B=2", "node", "bin/jest.js", "--json"]
        self.assertEqual(R.program(cmd), (["bin/jest.js", "--json"], ""))

    def test_not_a_command(self):
        for cmd in (None, [], "jest --json", ["jest", 1], ("jest",), ["env", "A=1"], ["sh", "-c", X.CD_EXEC, "d"]):
            self.assertEqual(R.program(cmd), (None, "not_a_command"), cmd)
            self.assertEqual(verdict("test_cmd", cmd), (R.UNKNOWN, None, "not_a_command"), cmd)

    def test_an_unread_wrapper_is_unknown(self):
        self.assertEqual(verdict("test_cmd", ["env", "-i", *JEST, "--json"]), (R.UNKNOWN, None, "wrapper_not_read"))


class Jest(unittest.TestCase):
    """Rules 2 and 3."""

    def test_with_json_is_read(self):
        for word in ("jest", "node_modules/.bin/jest", "node_modules/jest/bin/jest.js"):
            self.assertEqual(verdict("test_cmd", [word, "--json"]), (R.READ, R.JEST, ""), word)
        self.assertEqual(verdict("affected_test_cmd", JEST + ["--json"]), (R.READ, R.JEST, ""))

    def test_without_json_is_unread(self):
        self.assertEqual(verdict("test_cmd", JEST), (R.UNREAD, R.JEST, "jest_without_json"))
        self.assertEqual(verdict("test_cmd", JEST + ["--jsonx", "-json", "json"]), (R.UNREAD, R.JEST, "jest_without_json"))

    def test_the_option_is_the_composers_constant(self):
        self.assertEqual(verdict("test_cmd", JEST + [X.JEST_JSON]), (R.READ, R.JEST, ""))

    def test_output_file_is_unread(self):
        for extra in (["--outputFile", "o.json"], ["--outputFile=o.json"]):
            self.assertEqual(verdict("test_cmd", JEST + ["--json"] + extra), (R.UNREAD, R.JEST, "jest_output_file"))
            self.assertEqual(verdict("test_cmd", JEST + extra + ["--json"]), (R.UNREAD, R.JEST, "jest_output_file"))
        self.assertEqual(verdict("test_cmd", JEST + ["--json", "--outputFilex=o"]), (R.READ, R.JEST, ""))

    def test_elements_after_two_dashes_are_not_options(self):
        self.assertEqual(verdict("test_cmd", JEST + ["--", "--json"]), (R.UNREAD, R.JEST, "jest_without_json"))
        self.assertEqual(verdict("test_cmd", JEST + ["--json", "--", "--outputFile=o"]), (R.READ, R.JEST, ""))

    def test_the_program_word_is_not_an_option(self):
        self.assertEqual(verdict("test_cmd", ["--json"]), (R.UNKNOWN, None, "program_not_known"))

    def test_the_nx_form(self):
        cmd = ["env", "TS_NODE_COMPILER_OPTIONS=" + X.TS_NODE, *JEST, X.JEST_JSON]
        self.assertEqual(verdict("test_cmd", cmd), (R.READ, R.JEST, ""))


class NodeTest(unittest.TestCase):
    """Rule 4."""

    def test_default_reporter_on_a_measured_major(self):
        for major in R.NODE_TAP_DEFAULT:
            self.assertEqual(verdict("test_cmd", ["node", "--test", "t/*.js"], "node@%d.1.0" % major), (R.READ, R.TAP, ""))
            self.assertEqual(verdict("test_cmd", ["node", "--test"], "node@%d" % major), (R.READ, R.TAP, ""))

    def test_another_major_is_unknown(self):
        for toolchain in ("node@18.19.0", "node@24.0.0", "node@2", "node@200.1.0", "deno@20.0.0", "node@", "20.11.0",
                          "node@20x", "node@22-rc.1", None, 20):
            self.assertEqual(verdict("test_cmd", ["node", "--test"], toolchain),
                             (R.UNKNOWN, R.TAP, "node_major_not_measured"), toolchain)

    def test_a_reporter_that_is_not_tap_is_unread_on_any_major(self):
        for options in (["--test-reporter=spec"], ["--test-reporter", "dot"],
                        ["--test-reporter=tap", "--test-reporter=spec"], ["--test-reporter", "tap", "--test-reporter=x"]):
            for toolchain in (NODE20, "node@18.0.0"):
                self.assertEqual(verdict("test_cmd", ["node", "--test", *options], toolchain),
                                 (R.UNREAD, R.TAP, "reporter_not_tap"), options)

    def test_a_destination_that_is_not_stdout_is_unread(self):
        for options in (["--test-reporter=tap", "--test-reporter-destination=out.txt"],
                        ["--test-reporter-destination", "out.txt"],
                        ["--test-reporter-destination=stdout", "--test-reporter-destination=stderr"]):
            self.assertEqual(verdict("test_cmd", ["node", "--test", *options]),
                             (R.UNREAD, R.TAP, "destination_not_stdout"), options)

    def test_tap_to_stdout_is_read(self):
        for options in (["--test-reporter=tap"], ["--test-reporter", "tap"],
                        ["--test-reporter=tap", "--test-reporter-destination=stdout"],
                        ["--test-reporter", "tap", "--test-reporter-destination", "stdout"]):
            self.assertEqual(verdict("test_cmd", ["node", "--test", *options]), (R.READ, R.TAP, ""), options)

    def test_node_without_the_test_option_is_not_known(self):
        self.assertEqual(verdict("test_cmd", ["node", "--experimental-vm-modules", "x.js"]),
                         (R.UNKNOWN, None, "program_not_known"))
        self.assertEqual(verdict("test_cmd", ["node", "--", "--test"]), (R.UNKNOWN, None, "program_not_known"))
        self.assertEqual(verdict("test_cmd", ["node", "run.js", "--test"]), (R.UNKNOWN, None, "program_not_known"))


class NodeCapture(unittest.TestCase):
    """Rule 4 against the reader: on real node's bytes, ``read`` exactly where ``runner.test_results`` reads the
    two tests, ``unread`` exactly where it reads none."""

    def setUp(self):
        with open(os.path.join(ROOT, "tests", "fixtures", "node-test-reporters.json"), encoding="utf-8") as fh:
            self.doc = json.load(fh)

    def test_the_captured_major_is_a_measured_one(self):
        self.assertIn(self.doc["major"], R.NODE_TAP_DEFAULT)
        self.assertEqual(self.doc["cases"][0]["options"], [])

    def test_each_case(self):
        want = [{"id": self.doc["tests"][0], "status": "pass"}, {"id": self.doc["tests"][1], "status": "fail"}]
        seen = set()
        for case in self.doc["cases"]:
            got = R.judge("test_cmd", ["node", "--test", *case["options"], "a.test.js"], "node@%d.0.0" % self.doc["major"])
            tests = T.tap(case["stdout"].encode("utf-8"))
            self.assertIsNone(T.jest(case["stdout"].encode("utf-8")), case["options"])
            self.assertIn(tests, (want, []), case["options"])
            self.assertEqual(got["verdict"], R.READ if tests == want else R.UNREAD, case["options"])
            seen.add(got["verdict"])
        self.assertEqual(seen, {R.READ, R.UNREAD})


class Eslint(unittest.TestCase):
    """Rule 5."""

    def test_format_json_is_read(self):
        for options in (["--format", "json"], ["-f", "json"], ["--format=json"], ["--format", "stylish", "-f", "json"]):
            self.assertEqual(verdict("lint_cmd", ESLINT + options + ["."]), (R.READ, R.ESLINT, ""), options)

    def test_another_format_or_none_is_unread(self):
        for options in ([], ["--format", "stylish"], ["--format=json-with-metadata"], ["-f", "json", "--format=compact"],
                        ["--format"], ["json"], ["--formatx=json"], ["-f=json"]):
            self.assertEqual(verdict("lint_cmd", ESLINT + options), (R.UNREAD, R.ESLINT, "eslint_format_not_json"), options)

    def test_output_file_is_unread(self):
        for options in (["-o", "out.json"], ["--output-file", "out.json"], ["--output-file=out.json"]):
            self.assertEqual(verdict("lint_cmd", ESLINT + ["-f", "json"] + options),
                             (R.UNREAD, R.ESLINT, "eslint_output_file"), options)

    def test_the_composed_forms(self):
        inferred = ["/bin/sh", "-c", X.CD_EXEC, "libs/a", "/work/node_modules/.bin/eslint", ".", "--format", "json"]
        self.assertEqual(verdict("lint_cmd", inferred), (R.READ, R.ESLINT, ""))
        self.assertEqual(verdict("lint_cmd", ["node", "u/node_modules/eslint/bin/eslint.js", "--format", "json", "u"]),
                         (R.READ, R.ESLINT, ""))


class FieldAndOthers(unittest.TestCase):
    """Rules 6 and 7."""

    def test_a_program_in_another_readers_field_is_unread(self):
        self.assertEqual(verdict("lint_cmd", JEST + ["--json"]), (R.UNREAD, R.JEST, "program_not_for_field"))
        self.assertEqual(verdict("lint_cmd", ["node", "--test"]), (R.UNREAD, R.TAP, "program_not_for_field"))
        for field in ("test_cmd", "affected_test_cmd"):
            self.assertEqual(verdict(field, ESLINT + ["-f", "json"]), (R.UNREAD, R.ESLINT, "program_not_for_field"))

    def test_every_field_has_its_readers(self):
        self.assertEqual(set(R.READERS), set(R.FIELDS))
        self.assertEqual(R.READERS["test_cmd"], R.READERS["affected_test_cmd"])

    def test_other_programs_are_unknown(self):
        for cmd in (["npx", "jest", "--json"], ["mocha"], ["vitest", "run"], ["pytest", "-q"], ["jestx", "--json"],
                    ["npm", "test"]):
            self.assertEqual(verdict("test_cmd", cmd), (R.UNKNOWN, None, "program_not_known"), cmd)

    def test_the_npm_form_of_profile_fit_is_unknown(self):
        self.assertEqual(verdict("lint_cmd", ["npm", "--prefix", "a", *F.LINT_CMD]), (R.UNKNOWN, None, "program_not_known"))
        self.assertEqual(verdict("test_cmd", ["npm", "--prefix", "a", *F.TEST_CMD]), (R.UNKNOWN, None, "program_not_known"))


def unit(**changes):
    base = {"unit_id": "u", "toolchain": NODE20, "lint_cmd": ESLINT + ["-f", "json"], "test_cmd": JEST + ["--json"],
            "affected_test_cmd": ["node", "--test"]}
    base.update(changes)
    return {k: v for k, v in base.items() if v is not None}


class Survey(unittest.TestCase):
    """Rule 8."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="test-recipe-contract-")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def put(self, target, doc):
        os.makedirs(os.path.join(self.root, target), exist_ok=True)
        with open(os.path.join(self.root, target, "units.json"), "w", encoding="utf-8") as fh:
            fh.write(doc if isinstance(doc, str) else json.dumps(doc))

    def run_main(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = R.main(["--targets", self.root])
        return code, json.loads(out.getvalue())

    def test_all_read(self):
        self.put("b", {"units": [unit(unit_id="b1"), unit(unit_id="b2")]})
        self.put("a", {"units": [unit(unit_id="a1")]})
        code, answer = self.run_main()
        self.assertEqual(code, 0)
        self.assertEqual({k: v for k, v in answer.items() if k != "rows"},
                         {"ok": True, "units": 3, "commands": 9, "read": 9, "unread": 0, "unknown": 0})
        self.assertEqual([(r["target"], r["unit_id"], r["field"]) for r in answer["rows"]],
                         [(t, u, f) for t, u in (("a", "a1"), ("b", "b1"), ("b", "b2")) for f in R.FIELDS])
        self.assertEqual(answer["rows"][2], {"target": "a", "unit_id": "a1", "field": "affected_test_cmd",
                                             "verdict": "read", "reader": "tap", "why": ""})

    def test_targets_are_in_name_order_whatever_the_listing_order(self):
        for name in ("b", "a", "c"):
            self.put(name, {"units": [unit()]})
        listing = os.listdir(self.root)
        for order in (sorted(listing), sorted(listing, reverse=True)):
            with mock.patch.object(R.os, "listdir", return_value=order):
                rows = R.survey(self.root)["rows"]
            self.assertEqual([r["target"] for r in rows[::len(R.FIELDS)]], ["a", "b", "c"])

    def test_one_unread_is_not_ok(self):
        self.put("a", {"units": [unit(), unit(test_cmd=JEST)]})
        code, answer = self.run_main()
        self.assertEqual((code, answer["ok"], answer["read"], answer["unread"], answer["unknown"]), (1, False, 5, 1, 0))
        self.assertEqual(answer["rows"][4]["why"], "jest_without_json")

    def test_one_unknown_is_not_ok(self):
        self.put("a", {"units": [unit(lint_cmd=["npm", "--prefix", "a", *F.LINT_CMD])]})
        code, answer = self.run_main()
        self.assertEqual((code, answer["ok"], answer["read"], answer["unread"], answer["unknown"]), (1, False, 2, 0, 1))

    def test_a_missing_command_is_unknown(self):
        self.put("a", {"units": [unit(affected_test_cmd=None)]})
        code, answer = self.run_main()
        self.assertEqual((code, answer["rows"][2]["verdict"], answer["rows"][2]["why"]), (1, "unknown", "not_a_command"))

    def test_the_units_toolchain_is_the_one_read(self):
        self.put("a", {"units": [unit(toolchain="node@18.0.0")]})
        code, answer = self.run_main()
        self.assertEqual((code, answer["rows"][2]["why"]), (1, "node_major_not_measured"))

    def test_no_unit_is_not_ok(self):
        self.put("a", {"units": []})
        code, answer = self.run_main()
        self.assertEqual((code, answer["ok"], answer["commands"]), (1, False, 0))

    def test_a_directory_without_units_is_not_a_target(self):
        os.makedirs(os.path.join(self.root, "empty"))
        with open(os.path.join(self.root, "names.json"), "w") as fh:
            fh.write("{}")
        self.put("a", {"units": [unit()]})
        code, answer = self.run_main()
        self.assertEqual((code, {r["target"] for r in answer["rows"]}), (0, {"a"}))

    def test_unreadable(self):
        self.assertEqual(self.run_main(), (2, {"ok": False, "reason": "no_units_file"}))
        self.put("a", "{not json")
        self.assertEqual(self.run_main(), (2, {"ok": False, "reason": "units_unreadable:a"}))
        for doc in ([], {"units": {}}, {"units": [unit(), "x"]}, {}):
            self.put("a", doc)
            self.assertEqual(self.run_main(), (2, {"ok": False, "reason": "units_not_a_list:a"}), doc)
        shutil.rmtree(self.root)
        self.assertEqual(self.run_main(), (2, {"ok": False, "reason": "targets_unreadable"}))


class ThisTree(unittest.TestCase):
    """The check itself: every recipe command of this brain's targets has a reader for what it asks to print."""

    def test_every_command_is_read(self):
        answer = R.survey()
        self.assertTrue(answer["ok"], [r for r in answer["rows"] if r["verdict"] != R.READ])
        self.assertEqual(answer["commands"], len(R.FIELDS) * answer["units"])

    def test_the_targets_are_this_trees(self):
        self.assertEqual(R.TARGETS, os.path.join(ROOT, "targets"))
        self.assertEqual({r["target"] for r in R.survey()["rows"]},
                         {n for n in os.listdir(R.TARGETS) if os.path.isdir(os.path.join(R.TARGETS, n))})


if __name__ == "__main__":
    unittest.main()
