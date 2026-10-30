"""Test 35 (asama-0/09) and group ``k0map`` (tohum/29d): ``gate.check``, the pure merge decision.

- the mapped line (asama-0/08) on two real git diffs of one change (``-U0`` and ``-U2``), each line checked
  against the post-image file, not only against expected numbers; renames, deletions, untouched paths;
- the parser refuses a hunk whose ``+`` start is not the one git writes (the mapped line reads it);
- criteria 3-8, each rejecting with its own reason and only that reason, from recorded ``koş`` outputs:
  oracle not discriminating, tool not identical in three runs, ``scope_violation``, ratchet increase,
  zero tests, red tests, red control green, ``merge_paused``, a merge whose sentinel has not finished,
  an artifact whose hash does not match; and the good candidate merges;
- the command line: one JSON line, exit 0 / 1 / 2, never a traceback.

Fixture ``koş`` outputs are built here: ESLint ``json`` output (array of ``{filePath, messages,
suppressedMessages, source}``), jest ``--json`` and node ``tap`` summaries, run records as
``run.contained`` writes them.
"""

from __future__ import annotations

import copy
import difflib
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from gate import check as C  # noqa: E402
from gate import diffguard as G  # noqa: E402
from runner import contained  # noqa: E402

# One change made with git 2.x and printed by ``git diff -U0`` and ``git diff -U2``: line 3 modified, two
# lines inserted after line 6, lines 12-13 deleted, the last line modified and left without a newline.
OLD_M = "".join("line %d\n" % i for i in range(1, 26))
NEW_M = ("line 1\nline 2\nline 3 changed\nline 4\nline 5\nline 6\ninserted A\ninserted B\n"
         + "".join("line %d\n" % i for i in range(7, 12)) + "".join("line %d\n" % i for i in range(14, 25))
         + "line 25 last")
DIFF_U0 = """diff --git a/m.js b/m.js
index 086df9f..40db0c4 100644
--- a/m.js
+++ b/m.js
@@ -3 +3 @@ line 2
-line 3
+line 3 changed
@@ -6,0 +7,2 @@ line 6
+inserted A
+inserted B
@@ -12,2 +13,0 @@ line 11
-line 12
-line 13
@@ -25 +25 @@ line 24
-line 25
+line 25 last
\\ No newline at end of file
"""
DIFF_U2 = """diff --git a/m.js b/m.js
index 086df9f..40db0c4 100644
--- a/m.js
+++ b/m.js
@@ -1,8 +1,10 @@
 line 1
 line 2
-line 3
+line 3 changed
 line 4
 line 5
 line 6
+inserted A
+inserted B
 line 7
 line 8
@@ -10,6 +12,4 @@ line 9
 line 10
 line 11
-line 12
-line 13
 line 14
 line 15
@@ -23,3 +23,3 @@ line 22
 line 23
 line 24
-line 25
+line 25 last
\\ No newline at end of file
"""


def run_cli(*args: str) -> tuple[int, dict]:
    proc = subprocess.run([sys.executable, "-m", "gate.check", *args], cwd=REFEREE, capture_output=True,
                          text=True, stdin=subprocess.DEVNULL, timeout=60)
    lines = proc.stdout.strip().split("\n")
    assert "Traceback" not in proc.stderr, proc.stderr
    return proc.returncode, json.loads(lines[-1])


class MappedLine(unittest.TestCase):

    def test_real_diffs_expected_numbers(self):
        u0 = {1: (1, 1), 2: (2, 2), 3: (3, 3), 6: (6, 6), 7: (9, 9), 11: (13, 13), 12: (None, None),
              13: (None, None), 14: (14, 14), 24: (24, 24), 25: (25, 25)}
        u2 = {1: (1, 10), 8: (1, 10), 9: (11, 11), 10: (12, 15), 15: (12, 15), 16: (16, 16), 22: (22, 22),
              23: (23, 25), 25: (23, 25)}
        for diff, table in ((DIFF_U0, u0), (DIFF_U2, u2)):
            blocks = G.parse(diff)
            for line, (start, end) in table.items():
                m = C.map_line(blocks, "m.js", line)
                self.assertEqual((m["start"], m["end"]), (start, end), (diff[:60], line))
                self.assertEqual(m["path"], "m.js")

    def test_real_diffs_against_the_files(self):
        old, new = OLD_M.split("\n"), NEW_M.split("\n")
        for diff in (DIFF_U0, DIFF_U2):
            blocks = G.parse(diff)
            self.assertEqual(C.apply_block(blocks[0], OLD_M), NEW_M)
            hunks = blocks[0]["hunks"]
            for line in range(1, 26):
                m = C.map_line(blocks, "m.js", line)
                inside = [h for h in hunks if h["old_count"] and h["old_start"] <= line < h["old_start"] + h["old_count"]]
                if inside:
                    want = [t for tag, t, _ in inside[0]["lines"] if tag != "-"]
                    got = new[m["start"] - 1:m["end"]] if m["start"] else []
                    self.assertEqual(got, want, line)
                else:
                    self.assertEqual(m["start"], m["end"])
                    self.assertEqual(new[m["start"] - 1], old[line - 1], line)

    def test_insertion_boundary(self):
        # a pure insertion after line 6 moves line 7 on, never line 6 (git writes '-6,0')
        blocks = G.parse(DIFF_U0)
        self.assertEqual(C.map_line(blocks, "m.js", 6)["start"], 6)
        self.assertEqual(C.map_line(blocks, "m.js", 7)["start"], 9)
        top = ("diff --git a/t.js b/t.js\nindex 1..2 100644\n--- a/t.js\n+++ b/t.js\n"
               "@@ -0,0 +1,3 @@\n+a\n+b\n+c\n")
        self.assertEqual(C.map_line(G.parse(top), "t.js", 1)["start"], 4)

    def test_paths(self):
        diff = ("diff --git a/x.js b/y.js\nsimilarity index 90%\nrename from x.js\nrename to y.js\n"
                "index 1..2 100644\n--- a/x.js\n+++ b/y.js\n@@ -2 +2 @@\n-b\n+B\n"
                "diff --git a/gone.js b/gone.js\ndeleted file mode 100644\nindex 1..0\n--- a/gone.js\n"
                "+++ /dev/null\n@@ -1 +0,0 @@\n-x\n"
                "diff --git a/new.js b/new.js\nnew file mode 100644\nindex 0..1\n--- /dev/null\n"
                "+++ b/new.js\n@@ -0,0 +1 @@\n+x\n")
        blocks = G.parse(diff)
        self.assertEqual(C.map_line(blocks, "x.js", 1), {"path": "y.js", "start": 1, "end": 1})
        self.assertEqual(C.map_line(blocks, "x.js", 2), {"path": "y.js", "start": 2, "end": 2})
        self.assertEqual(C.map_line(blocks, "gone.js", 1), {"path": None, "start": None, "end": None})
        self.assertEqual(C.map_line(blocks, "other.js", 7), {"path": "other.js", "start": 7, "end": 7})
        with self.assertRaises(G.DiffError):
            C.map_line(blocks, "new.js", 1)
        with self.assertRaises(G.DiffError):
            C.map_line(blocks, "x.js", 0)

    def test_hunk_starts_are_checked(self):
        lie = DIFF_U0.replace("@@ -6,0 +7,2 @@", "@@ -6,0 +500,2 @@")
        with self.assertRaises(G.DiffError):
            G.parse(lie)
        for bad in (DIFF_U0.replace("@@ -12,2 +13,0 @@", "@@ -12,2 +14,0 @@"),
                    DIFF_U0.replace("@@ -3 +3 @@", "@@ -7 +7 @@"),  # out of order with '-6,0'
                    DIFF_U0.replace("@@ -3 +3 @@ line 2\n-line 3\n+line 3 changed\n",
                                    "@@ -3 +3 @@ line 2\n-line 3\n\\ No newline at end of file\n-line 4\n"
                                    "+line 3 changed\n")):
            with self.assertRaises(G.DiffError):
                G.parse(bad)

    def test_cli_map(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.patch")
            with open(p, "w") as fh:
                fh.write(DIFF_U2)
            self.assertEqual(run_cli("map", p, "m.js", "10"), (0, {"path": "m.js", "start": 12, "end": 15}))
            self.assertEqual(run_cli("map", p, "m.js", "16"), (0, {"path": "m.js", "start": 16, "end": 16}))
            code, out = run_cli("map", p, "m.js", "0")
            self.assertEqual((code, out["ok"]), (2, False))
            with open(p, "w") as fh:
                fh.write(DIFF_U2.replace("+12,4", "+13,4"))
            code, out = run_cli("map", p, "m.js", "16")
            self.assertEqual((code, out["ok"]), (2, False))


# ---------------------------------------------------------------- the decision

SRC = "const x = 1;\nvar y = 2;\nlet z = 3;\nvar w = 4;\n"
VAR_Y = SRC.index("var y")
FIX = {"range": [VAR_Y, VAR_Y + 3], "text": "let"}


def msg(rule, line, fix=None, **kw):
    m = {"ruleId": rule, "severity": 2, "message": "m", "line": line, "column": 1}
    if fix:
        m["fix"] = fix
    m.update(kw)
    return m


def eslint(files):
    return json.dumps([{"filePath": "/work/" + p, "messages": f.get("messages", []),
                        "suppressedMessages": f.get("suppressed", []), "errorCount": 0,
                        **({"source": f["source"]} if "source" in f else {})} for p, f in files]).encode()


def file_diff(path, old, new, a=None, b=None, n=0):
    body = list(difflib.unified_diff(old.splitlines(True), new.splitlines(True), "a/" + (a or path),
                                     "b/" + (b or path), n=n))
    return "diff --git a/%s b/%s\nindex 1111111..2222222 100644\n" % (a or path, b or path) + "".join(body)


BASE_LINT = [("src/a.js", {"messages": [msg("no-var", 2, FIX), msg("no-var", 4, {"range": [36, 39], "text": "let"})],
                           "source": SRC}),
             ("src/b.js", {"messages": []})]
GOOD_NEW = SRC.replace("var y", "let y")
CAND_LINT = [("src/a.js", {"messages": [msg("no-var", 4, {"range": [36, 39], "text": "let"})], "source": GOOD_NEW}),
             ("src/b.js", {"messages": []})]
JEST_GREEN = {"success": True, "numTotalTests": 3, "numPassedTests": 3, "numFailedTests": 0,
              "numPendingTests": 0, "numFailedTestSuites": 0, "numRuntimeErrorTestSuites": 0}


def tap(passed, failed=0, skipped=0, cancelled=0, before=""):
    return (before + "TAP version 13\n1..%d\n# tests %d\n# suites 0\n# pass %d\n# fail %d\n# cancelled %d\n"
            "# skipped %d\n# todo 0\n# duration_ms 12.5\n") % (
        passed + failed + skipped, passed + failed + skipped, passed, failed, cancelled, skipped)


class Case:
    """One decision input: the parts a test changes, written to a temporary directory on ``write``."""

    def __init__(self):
        self.finding = {"tool": "eslint", "rule_id": "no-var", "path": "src/a.js", "line": 2}
        self.base = [eslint(BASE_LINT)] * 3
        self.cand = [eslint(CAND_LINT)] * 3
        self.base_exit = [1, 1, 1]
        self.cand_exit = [1, 1, 1]
        self.status = {}
        self.tests_format, self.tests_out, self.tests_exit = "jest-json", json.dumps(JEST_GREEN).encode(), 0
        self.red = {"status": "ok", "exit": 1}
        self.sentinels = [{"merge": "m1", "state": "green"}]
        self.control = {"kill_switch": False, "merge_paused": False}
        self.diff = file_diff("src/a.js", SRC, GOOD_NEW)
        self.tamper = None

    def write(self, d):
        def rec(role, raw, code):
            name = role.replace("[", "_").replace("]", "") + ".out"
            with open(os.path.join(d, name), "wb") as fh:
                fh.write(raw)
            return {"status": self.status.get(role, "ok"), "exit": code, "stdout": name,
                    "stdout_sha256": hashlib.sha256(raw).hexdigest()}
        bundle = {"finding": self.finding,
                  "lint_base": [rec("lint_base[%d]" % i, r, c) for i, (r, c) in enumerate(zip(self.base, self.base_exit))],
                  "lint_candidate": [rec("lint_candidate[%d]" % i, r, c)
                                     for i, (r, c) in enumerate(zip(self.cand, self.cand_exit))],
                  "tests": {"format": self.tests_format, "run": rec("tests", self.tests_out, self.tests_exit)},
                  "red_control": self.red, "sentinels": self.sentinels}
        if self.tamper:
            with open(os.path.join(d, self.tamper), "ab") as fh:
                fh.write(b" ")
        paths = {}
        for name, obj in (("runs.json", bundle), ("control.json", self.control)):
            paths[name] = os.path.join(d, name)
            with open(paths[name], "w") as fh:
                json.dump(obj, fh)
        paths["diff"] = os.path.join(d, "c.patch")
        with open(paths["diff"], "w") as fh:
            fh.write(self.diff)
        return paths

    def decide(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.write(d)
            with open(p["runs.json"]) as fh:
                bundle = json.load(fh)
            return C.decide(bundle, self.diff, self.control, d)


def with_source(lint, path, new_source, messages=None):
    out = []
    for p, f in lint:
        f = dict(f)
        if p == path:
            f["source"] = new_source
            if messages is not None:
                f["messages"] = messages
        out.append((p, f))
    return out


class Decision(unittest.TestCase):

    def assertReasons(self, case, reasons):
        result = case.decide()
        self.assertEqual(result["reasons"], reasons)
        self.assertEqual(result["decision"], "merge" if not reasons else "reject")
        return result

    def test_good_candidate_merges(self):
        result = self.assertReasons(Case(), [])
        self.assertEqual(result["mapped"], {"path": "src/a.js", "start": 2, "end": 2})
        self.assertEqual([h["covered"] for h in result["hunk_covered"]], ["unmeasured"])
        self.assertTrue(result["hunk_covered"][0]["reason"])

    def test_good_candidate_with_node_tap(self):
        c = Case()
        c.tests_format, c.tests_out = "node-tap", tap(2, skipped=1).encode()
        self.assertReasons(c, [])

    # criterion 3: the oracle discriminates
    def test_base_without_the_finding(self):
        c = Case()
        c.finding = dict(c.finding, line=3)
        self.assertIn("oracle_not_discriminating", c.decide()["reasons"])
        c = Case()
        c.finding = dict(c.finding, rule_id="semi")
        self.assertIn("oracle_not_discriminating", c.decide()["reasons"])

    def test_finding_suppressed_in_base_is_not_a_target(self):
        c = Case()
        base = [("src/a.js", {"messages": [msg("no-var", 4)], "suppressed": [msg("no-var", 2, FIX)], "source": SRC}),
                ("src/b.js", {})]
        c.base = [eslint(base)] * 3
        self.assertIn("oracle_not_discriminating", c.decide()["reasons"])

    def test_candidate_still_violates_at_mapped_line(self):
        c = Case()
        c.cand = [eslint(with_source(CAND_LINT, "src/a.js", GOOD_NEW,
                                     [msg("no-var", 2), msg("no-var", 4)]))] * 3
        c.base = [eslint(with_source(BASE_LINT, "src/a.js", SRC, [msg("no-var", 2, FIX), msg("no-var", 4),
                                                                  msg("semi", 1)]))] * 3
        self.assertReasons(c, ["oracle_not_discriminating"])

    def test_candidate_suppresses_instead_of_fixing(self):
        c = Case()
        c.cand = [eslint([("src/a.js", {"messages": [msg("no-var", 4)], "suppressed": [msg("no-var", 2)],
                                        "source": GOOD_NEW}), ("src/b.js", {})])] * 3
        self.assertReasons(c, ["oracle_not_discriminating"])

    def test_candidate_report_without_the_file(self):
        c = Case()
        c.cand = [eslint([("src/b.js", {})])] * 3
        self.assertReasons(c, ["oracle_not_discriminating"])

    def test_line_shift_is_not_a_new_violation(self):
        # the replacement inserts a line inside the fix range: line 4's violation is now on line 5
        new = SRC.replace("var", "let\n", 1)
        c = Case()
        c.diff = file_diff("src/a.js", SRC, new)
        c.cand = [eslint([("src/a.js", {"messages": [msg("no-var", 5)], "source": new}), ("src/b.js", {})])] * 3
        result = self.assertReasons(c, [])
        self.assertEqual(result["mapped"], {"path": "src/a.js", "start": 2, "end": 3})
        # the same violation inside the mapped range is not a shift
        c.cand = [eslint([("src/a.js", {"messages": [msg("no-var", 3)], "source": new}), ("src/b.js", {})])] * 3
        self.assertReasons(c, ["oracle_not_discriminating"])

    def test_mapped_range_follows_the_diff_context(self):
        # with one context line the hunk's base range is lines 1-3, so the whole candidate range 1-3 is
        # the mapped line: a violation of the rule on line 3 (base line 3 unchanged) refuses the oracle
        c = Case()
        c.diff = file_diff("src/a.js", SRC, GOOD_NEW, n=1)
        self.assertReasons(c, [])
        self.assertEqual(c.decide()["mapped"], {"path": "src/a.js", "start": 1, "end": 3})
        c.cand = [eslint([("src/a.js", {"messages": [msg("no-var", 3)], "source": GOOD_NEW}), ("src/b.js", {})])] * 3
        self.assertReasons(c, ["oracle_not_discriminating"])
        c.diff = file_diff("src/a.js", SRC, GOOD_NEW, n=0)
        self.assertReasons(c, [])

    def test_tool_not_identical_in_three_runs(self):
        for tree in ("base", "cand"):
            c = Case()
            runs = getattr(c, tree)
            setattr(c, tree, [runs[0], runs[1], runs[2] + b" "])
            self.assertReasons(c, ["tool_nondeterministic:" + ("base" if tree == "base" else "candidate")])

    def test_tool_fatal_and_failed(self):
        c = Case()
        c.cand = [eslint([("src/a.js", {"messages": [{"ruleId": None, "fatal": True, "severity": 2,
                                                      "message": "Parsing error"}]}), ("src/b.js", {})])] * 3
        self.assertIn("tool_fatal", c.decide()["reasons"])
        c = Case()
        c.cand_exit = [2, 2, 2]
        c.cand = [b"Oops! Something went wrong!"] * 3
        self.assertReasons(c, ["tool_failed"])

    # criterion 4: inside the tool's fix range
    def test_scope_same_line_outside_the_range(self):
        new = SRC.replace("var y = 2", "let y = 3")
        c = Case()
        c.diff = file_diff("src/a.js", SRC, new)
        c.cand = [eslint(with_source(CAND_LINT, "src/a.js", new))] * 3
        self.assertReasons(c, ["scope_violation"])

    def test_scope_other_line_or_file(self):
        new = GOOD_NEW.replace("const x = 1", "const x = 5")
        c = Case()
        c.diff = file_diff("src/a.js", SRC, new)
        self.assertReasons(c, ["scope_violation"])
        c = Case()
        c.diff = file_diff("src/a.js", SRC, GOOD_NEW) + file_diff("src/b.js", "a\n", "b\n")
        self.assertReasons(c, ["scope_violation"])

    def test_scope_rename_mode_and_no_fix(self):
        c = Case()
        c.diff = c.diff.replace("index 1111111..2222222 100644\n",
                                "old mode 100644\nnew mode 100755\nindex 1111111..2222222\n")
        self.assertReasons(c, ["scope_violation"])
        c = Case()  # a symlink's target text is not a source file, whatever its name
        c.diff = c.diff.replace("index 1111111..2222222 100644", "index 1111111..2222222 120000")
        self.assertReasons(c, ["scope_violation"])
        c = Case()  # the fix applied under a new name
        c.diff = ("diff --git a/src/a.js b/src/c.js\nsimilarity index 90%\nrename from src/a.js\n"
                  "rename to src/c.js\n" + file_diff("src/a.js", SRC, GOOD_NEW, b="src/c.js").split("\n", 2)[2])
        c.cand = [eslint([("src/c.js", {"messages": [msg("no-var", 4)], "source": GOOD_NEW}), ("src/b.js", {})])] * 3
        self.assertReasons(c, ["scope_violation"])
        c = Case()
        c.base = [eslint(with_source(BASE_LINT, "src/a.js", SRC, [msg("no-var", 2), msg("no-var", 4)]))] * 3
        self.assertReasons(c, ["scope_violation"])
        c = Case()
        c.base = [eslint([("src/a.js", {"messages": [msg("no-var", 2, FIX), msg("no-var", 4)]}), ("src/b.js", {})])] * 3
        self.assertReasons(c, ["scope_violation"])  # no source: containment cannot be shown
        c = Case()
        c.diff = c.diff.replace("-var y = 2;", "-var y = 9;")  # does not apply to the base source
        self.assertReasons(c, ["scope_violation"])

    def test_fix_offsets_are_utf16(self):
        src = "const s = '\U0001F600';\nvar y = 2;\nvar w = 4;\n"
        at = len(src[:src.index("var y")].encode("utf-16-le")) // 2
        self.assertEqual(at, src.index("var y") + 1)  # the astral character is two UTF-16 units
        new = src.replace("var y", "let y")
        c = Case()
        c.base = [eslint([("src/a.js", {"messages": [msg("no-var", 2, {"range": [at, at + 3], "text": "let"}),
                                                     msg("no-var", 3)], "source": src}), ("src/b.js", {})])] * 3
        c.cand = [eslint([("src/a.js", {"messages": [msg("no-var", 3)], "source": new}), ("src/b.js", {})])] * 3
        c.diff = file_diff("src/a.js", src, new)
        self.assertReasons(c, [])
        c.base = [eslint([("src/a.js", {"messages": [msg("no-var", 2, {"range": [at - 1, at + 2], "text": "let"}),
                                                     msg("no-var", 3)], "source": src}), ("src/b.js", {})])] * 3
        self.assertReasons(c, ["scope_violation"])

    def test_inline_directive(self):
        for text in ("/* eslint no-var: off */ var", "var /*eslint-disable-line*/", "//  ESLINT-disable-next-line\nvar",
                     "/* global y */ var"):
            new = SRC.replace("var y", text + " y", 1)
            c = Case()
            c.diff = file_diff("src/a.js", SRC, new)
            c.cand = [eslint([("src/a.js", {"messages": [msg("no-var", 4 + text.count("\n"))], "source": new}),
                              ("src/b.js", {})])] * 3
            c.base = [eslint(with_source(BASE_LINT, "src/a.js", SRC, [
                msg("no-var", 2, {"range": [VAR_Y, VAR_Y + 3], "text": "let"}), msg("no-var", 4)]))] * 3
            self.assertReasons(c, ["inline_directive"])
        # a comment that is not a directive passes
        new = SRC.replace("var y", "let /* y is mutable */ y", 1)
        c = Case()
        c.diff = file_diff("src/a.js", SRC, new)
        self.assertReasons(c, [])

    def test_line_basis(self):
        for odd in ("\r", "\u2028", "\u2029"):
            src = SRC.replace("let z", "let" + odd + "z")
            c = Case()
            c.base = [eslint(with_source(BASE_LINT, "src/a.js", src))] * 3
            c.diff = file_diff("src/a.js", src, src.replace("var y", "let y"))
            self.assertIn("line_basis", c.decide()["reasons"], repr(odd))
        c = Case()
        c.base = [eslint(with_source(BASE_LINT, "src/a.js", "\ufeff" + SRC))] * 3
        self.assertIn("line_basis", c.decide()["reasons"])
        c = Case()  # CRLF counts lines as git does
        crlf = SRC.replace("\n", "\r\n")
        at = crlf.index("var y")
        c.base = [eslint([("src/a.js", {"messages": [msg("no-var", 2, {"range": [at, at + 3], "text": "let"}),
                                                     msg("no-var", 4)], "source": crlf}), ("src/b.js", {})])] * 3
        c.diff = file_diff("src/a.js", crlf, crlf.replace("var y", "let y"))
        self.assertReasons(c, [])

    # criterion 5: the ratchet
    def test_ratchet(self):
        c = Case()
        c.cand = [eslint([("src/a.js", {"messages": [msg("no-var", 4)], "source": GOOD_NEW}),
                          ("src/b.js", {"messages": [msg("eqeqeq", 1), msg("eqeqeq", 2)]})])] * 3
        self.assertReasons(c, ["ratchet_increase"])
        c.cand = [eslint([("src/a.js", {"messages": [msg("no-var", 4)], "source": GOOD_NEW}),
                          ("src/b.js", {"suppressed": [msg("eqeqeq", 1), msg("eqeqeq", 2)]})])] * 3
        self.assertReasons(c, ["ratchet_increase"])  # suppressed messages count
        c.cand = [eslint([("src/a.js", {"messages": [msg("no-var", 4)], "source": GOOD_NEW}),
                          ("src/b.js", {"messages": [msg("eqeqeq", 1)]})])] * 3
        self.assertReasons(c, [])  # equal totals hold

    # criterion 6: tests
    def test_zero_tests(self):
        c = Case()
        c.tests_out = json.dumps(dict(JEST_GREEN, numPassedTests=0, numPendingTests=3)).encode()
        self.assertReasons(c, ["zero_tests"])
        c = Case()
        c.tests_format, c.tests_out = "node-tap", tap(0, skipped=4).encode()
        self.assertReasons(c, ["zero_tests"])

    def test_forged_tap_summary(self):
        c = Case()
        c.tests_format = "node-tap"
        c.tests_out = tap(0, skipped=1, before="# pass 9\n# fail 0\n").encode()
        self.assertReasons(c, ["zero_tests"])
        c.tests_out = tap(0, skipped=1) .encode() + b"# pass 9\n"
        with self.assertRaises(C.Unusable):
            c.decide()

    def test_tests_red(self):
        c = Case()
        c.tests_out = json.dumps(dict(JEST_GREEN, numFailedTests=1, numPassedTests=2, success=False)).encode()
        self.assertReasons(c, ["tests_red"])
        c = Case()
        c.tests_out = json.dumps(dict(JEST_GREEN, numRuntimeErrorTestSuites=1)).encode()
        self.assertReasons(c, ["tests_red"])
        c = Case()
        c.tests_exit = 1
        self.assertReasons(c, ["tests_red"])
        c = Case()
        c.tests_format, c.tests_out = "node-tap", tap(3, cancelled=1).encode()
        self.assertReasons(c, ["tests_red"])
        c = Case()
        c.tests_exit, c.tests_out = 1, b"not a report"
        self.assertReasons(c, ["tests_red"])

    # criterion 7: red control and merge_paused
    def test_red_control(self):
        for red, reason in (({"status": "ok", "exit": 0}, "red_control_green"),
                            ({"status": "ok", "exit": 127}, "red_control_fault"),
                            ({"status": "limit_hit:kos_wall_s", "exit": None}, "red_control_fault"),
                            ({"status": "ok", "exit": True}, "red_control_fault")):
            c = Case()
            c.red = red
            self.assertReasons(c, [reason])
            self.assertEqual(contained.red_control_reasons(red), [reason])  # one rule, MF3 and MF8

    def test_merge_paused(self):
        for control in ({"merge_paused": True}, {}, {"merge_paused": "false"}, {"merge_paused": 0}, []):
            c = Case()
            c.control = control
            self.assertReasons(c, ["merge_paused"])

    # criterion 8: serial merges
    def test_sentinel_pending(self):
        for state in ("pending", "red", "running"):
            c = Case()
            c.sentinels = [{"merge": "m1", "state": "green"}, {"merge": "m2", "state": state}]
            self.assertReasons(c, ["sentinel_pending"])
        c = Case()
        c.sentinels = []
        self.assertReasons(c, [])

    # artifacts are read by hash
    def test_artifact_hash_mismatch(self):
        c = Case()
        c.tamper = "lint_base_1.out"
        self.assertReasons(c, ["artifact_hash_mismatch:lint_base[1]"])
        c = Case()
        c.tamper = "tests.out"
        c.red = {"status": "ok", "exit": 0}
        self.assertReasons(c, ["artifact_hash_mismatch:tests"])

    def test_run_invalid(self):
        c = Case()
        c.status = {"tests": "limit_hit:kos_wall_s"}
        self.assertReasons(c, ["run_invalid:tests"])
        c = Case()
        c.status = {"lint_candidate[0]": "breach:in_changed"}
        self.assertReasons(c, ["run_invalid:lint_candidate[0]"])

    def test_secret_in_diff(self):
        token = "".join(["gh", "p_"]) + "".join(chr(65 + (i * 7) % 26) for i in range(36))
        new = SRC.replace("var y = 2;", "let y = '%s';" % token)
        c = Case()
        c.diff = file_diff("src/a.js", SRC, new)
        self.assertIn("secret_in_diff", c.decide()["reasons"])

    def test_every_reason_is_written(self):
        c = Case()
        c.control, c.sentinels = {"merge_paused": True}, [{"merge": "m", "state": "pending"}]
        c.tests_out = json.dumps(dict(JEST_GREEN, numPassedTests=0)).encode()
        self.assertReasons(c, ["merge_paused", "sentinel_pending", "zero_tests"])

    def test_unusable_inputs(self):
        breaks = [
            lambda c: setattr(c, "finding", dict(c.finding, tool="tslint")),
            lambda c: setattr(c, "finding", dict(c.finding, path="../a.js")),
            lambda c: setattr(c, "finding", dict(c.finding, line=True)),
            lambda c: setattr(c, "base", c.base[:2]),
            lambda c: setattr(c, "base", [b"[{]"] * 3),
            lambda c: setattr(c, "base", [json.dumps([{"filePath": "/tmp/a.js", "messages": [],
                                                       "suppressedMessages": []}]).encode()] * 3),
            lambda c: setattr(c, "base", [json.dumps([{"filePath": "/work/a.js", "messages": []}]).encode()] * 3),
            lambda c: setattr(c, "tests_format", "mocha"),
            lambda c: setattr(c, "tests_out", b"{}"),
            lambda c: setattr(c, "diff", "not a diff\n"),
        ]
        for i, brk in enumerate(breaks):
            c = Case()
            brk(c)
            with self.assertRaises((C.Unusable, G.DiffError), msg=str(i)):
                c.decide()

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            c = Case()
            p = c.write(d)
            code, out = run_cli("decide", p["runs.json"], p["diff"], p["control.json"])
            self.assertEqual((code, out["decision"], out["ok"]), (0, "merge", True))
            c.control = {"merge_paused": True}
            p = c.write(d)
            code, out = run_cli("decide", p["runs.json"], p["diff"], p["control.json"])
            self.assertEqual((code, out["reasons"]), (1, ["merge_paused"]))
            with open(p["runs.json"], "w") as fh:
                fh.write("[")
            code, out = run_cli("decide", p["runs.json"], p["diff"], p["control.json"])
            self.assertEqual((code, out["ok"]), (2, False))
            with open(p["runs.json"], "w") as fh:
                json.dump({"finding": {"tool": "eslint", "rule_id": "r", "path": "a", "line": 1},
                           "lint_base": [{"status": "ok", "exit": 1, "stdout": "../../etc/passwd",
                                          "stdout_sha256": "0" * 64}] * 3}, fh)
            code, out = run_cli("decide", p["runs.json"], p["diff"], p["control.json"])
            self.assertEqual((code, out["ok"]), (2, False))
            code, out = run_cli("decide", p["runs.json"])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
