"""Test 19 (asama-0/09) and group ``profile`` (tohum/29d): the profile is derived again and a proposal
that differs from it, or narrows it, is refused.

- languages by extension, excluded entries not counted, symlinks not followed;
- security paths by keyword substring (casefolded, any component, topmost path kept) and by an
  ownership-file line whose owner holds a keyword; the policy's keywords replace the default ones;
- excluded directories, the operator's patterns, test path rules and inline Rust tests;
- ``check``: an equal proposal passes; each field narrowed or widened is refused; ``excluded_paths`` may
  only widen; a field the derivation does not produce is refused; the command line.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from unittest import mock

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from profile import derive as D  # noqa: E402
from profile_tree import LOCK_OK, writable_base, write_tree  # noqa: E402

TREE = {
    "package.json": {"name": "toy"},
    "package-lock.json": LOCK_OK,
    ".nvmrc": "20.11.1\n",
    "src/auth/login.js": "x",
    "src/auth/deep/more.js": "x",
    "src/Session.TS": "x",
    "src/util.js": "x",
    "src/util.test.js": "x",
    "lib/helpers.js": "x",
    "lib/plain.py": "x",
    "tests/a.py": "x",
    "go/x_test.go": "x",
    "go/x.go": "x",
    "rs/lib.rs": "fn a() {}\n#[cfg(test)]\nmod t {}\n",
    "rs/other.rs": "fn b() {}\n",
    "rs/spaced.rs": "# [ cfg( all(test, unix) ) ]\nmod t {}\n",
    "rs/attr.rs": "#[test]\nfn t() {}\n",
    "rs/feature.rs": "#[cfg(feature = \"tests\")]\nfn f() {}\n",
    "README": "no extension",
    "notes.txt": "x",
    "node_modules/auth-lib/index.js": "x",
    "pkg/dist/bundle.js": "x",
    "vendor/token.js": "x",
    "a/vendor/b.js": "x",
    "legacy/old.js": "x",
    "legacy/keep.ts": "x",
    ".github/CODEOWNERS": "# owners\n/lib/ @org/Security-Team\n*.md @org/docs\nhelpers.py @org/auth-guild\n"
                          "/go/ @org/web @org/payments-oncall\n",
}


class ProfileTest(unittest.TestCase):
    def setUp(self):
        self.base = writable_base("t-profile-")
        self.addCleanup(shutil.rmtree, self.base, True)
        self.tree = write_tree(os.path.join(self.base, "tree"), TREE)
        self.target = {"excluded_paths": ["vendor", "/legacy/*.js"], "unit_candidates": []}

    def derive(self, **kw):
        return D.derive(self.tree, kw.get("target", self.target), kw.get("policy"))

    def add(self, files):
        write_tree(self.tree, files)

    # ------------------------------------------------------------ languages

    def test_languages_by_extension_excluded_not_counted(self):
        d = self.derive()
        # js: src/auth/login.js, src/auth/deep/more.js, src/util.js, src/util.test.js, lib/helpers.js;
        # not node_modules, pkg/dist, vendor, a/vendor, legacy/old.js (operator), nor README/notes.txt.
        self.assertEqual(d["languages"], {"javascript": {"files": 5}, "typescript": {"files": 2},
                                          "python": {"files": 2}, "go": {"files": 2}, "rust": {"files": 5}})

    def test_symlinks_not_followed_or_counted(self):
        outside = write_tree(os.path.join(self.base, "outside"), {"x1.js": "x", "x2.js": "x", "secret.c": "x"})
        self.add({"link-dir": ("symlink", outside), "link.js": ("symlink", "src/util.js")})
        d = self.derive()
        self.assertEqual(d["languages"]["javascript"], {"files": 5})
        self.assertNotIn("c", d["languages"])
        self.assertFalse(any("link-dir/" in p for p in d["security_paths"]))

    # ------------------------------------------------------------ security paths

    def test_security_paths_keyword_topmost_and_casefold(self):
        d = self.derive()
        self.assertIn("src/auth", d["security_paths"])
        self.assertIn("src/Session.TS", d["security_paths"])
        self.assertNotIn("src/auth/login.js", d["security_paths"])  # covered by src/auth
        self.assertNotIn("src/util.js", d["security_paths"])
        # excluded entries are not security paths: node_modules/auth-lib, vendor/token.js
        self.assertFalse(any(p.startswith(("node_modules", "vendor")) for p in d["security_paths"]))

    def test_every_default_keyword_marks_a_path(self):
        for word in D.SECURITY_KEYWORDS:
            self.add({"kw/x%sy.js" % word.upper(): "x"})
        d = self.derive()
        for word in D.SECURITY_KEYWORDS:
            self.assertIn("kw/x%sy.js" % word.upper(), d["security_paths"], word)

    def test_symlink_named_by_keyword_is_security_path(self):
        self.add({"src/guards": ("symlink", "util.js")})
        self.assertIn("src/guards", self.derive()["security_paths"])

    def test_policy_keywords_replace_default(self):
        d = self.derive(policy={"constitutional": {"security_keywords": ["UTIL"]}})
        self.assertIn("src/util.js", d["security_paths"])
        self.assertNotIn("src/auth", d["security_paths"])
        self.assertEqual(d["security_keywords"], ["util"])
        with self.assertRaises(D.DeriveError):
            self.derive(policy={"constitutional": {"security_keywords": []}})

    def test_ownership_file_owner_with_keyword(self):
        d = self.derive()
        self.assertIn("lib", d["security_paths"])             # /lib/ @org/Security-Team
        self.assertIn("go", d["security_paths"])              # second owner holds "payment"
        self.assertEqual(d["security_owner_patterns"], ["/go/", "/lib/", "helpers.py"])
        self.assertNotIn("README", d["security_paths"])       # *.md @org/docs: no keyword
        self.add({"x/y/helpers.py": "x"})                     # unanchored: any depth
        self.assertIn("x/y/helpers.py", self.derive()["security_paths"])

    def test_ownership_file_symlink_not_read(self):
        os.remove(os.path.join(self.tree, ".github/CODEOWNERS"))
        write_tree(self.base, {"own": "/src/ @org/security\n"})
        self.add({"CODEOWNERS": ("symlink", os.path.join(self.base, "own"))})
        self.assertEqual(self.derive()["security_owner_patterns"], [])

    # ------------------------------------------------------------ excluded, tests

    def test_excluded_dirs_and_operator_patterns(self):
        d = self.derive()
        self.assertEqual(d["excluded_dirs"], ["node_modules", "pkg/dist"])
        self.assertEqual(d["excluded_paths"], ["/legacy/*.js", "vendor"])
        self.assertEqual(D.excluded(d, "a/vendor/b.js"), "excluded_path")
        self.assertEqual(D.excluded(d, "LEGACY/old.js"), "excluded_path")
        self.assertIsNone(D.excluded(d, "legacy/keep.ts"))
        self.assertIsNone(D.excluded(d, "legacy/sub/old.js"))  # * does not cross /
        self.assertEqual(D.excluded(d, "x/Node_Modules/y.js"), "excluded_dir")
        self.assertIsNone(D.excluded(d, "src/util.js"))

    def test_test_path_rules_and_inline_rust(self):
        d = self.derive()
        self.assertEqual(d["test_path_rules"], ["**/*.test.*", "**/*_test.go", "**/tests/**", "rs/attr.rs",
                                                "rs/lib.rs", "rs/spaced.rs"])

    def test_unreadable_directory_stops_derivation(self):
        real = os.listdir

        def listdir(path):
            if path.endswith(os.sep + "src"):
                raise PermissionError(13, "Permission denied")
            return real(path)
        with mock.patch.object(D.os, "listdir", listdir):
            with self.assertRaises(D.DeriveError):
                self.derive()

    def test_pattern_syntax(self):
        cases = [("vendor", "a/vendor/x", True), ("/vendor", "a/vendor", False), ("/vendor", "vendor/x", True),
                 ("a/*.js", "a/b.js", True), ("a/*.js", "a/b/c.js", False), ("a/**/c.js", "a/b/d/c.js", True),
                 ("**/c.js", "c.js", True), ("x?.js", "xy.js", True), ("x[ab].js", "xb.js", True),
                 ("x[!ab].js", "xb.js", False), ("docs/", "docs", True), ("Docs", "dOCS/x", True)]
        for pattern, path, want in cases:
            self.assertEqual(D.pattern_matches(pattern, path), want, (pattern, path))

    # ------------------------------------------------------------ check

    def proposal(self, d):
        return {k: (list(d[k]) if k != "languages" else dict(d[k])) for k in D.PROPOSABLE if k != "units"}

    def test_equal_proposal_passes(self):
        d = self.derive()
        self.assertEqual(D.check(d, self.proposal(d)), {"ok": True, "reasons": []})

    def test_each_field_narrowed_or_widened_is_refused(self):
        d = self.derive()
        for field in D.SET_FIELDS:
            for change in ("narrow", "widen"):
                p = self.proposal(d)
                if change == "narrow":
                    if not p[field]:
                        continue
                    p[field] = p[field][1:]
                else:
                    p[field] = p[field] + ["zz/extra"]
                report = D.check(d, p)
                self.assertFalse(report["ok"], (field, change))
                self.assertEqual(report["reasons"], ["differs:%s" % field], (field, change))
        p = self.proposal(d)
        p["languages"] = {k: v for k, v in p["languages"].items() if k != "rust"}
        self.assertEqual(D.check(d, p)["reasons"], ["differs:languages"])
        p["languages"] = dict(d["languages"], cobol={"files": 1})
        self.assertEqual(D.check(d, p)["reasons"], ["differs:languages"])

    def test_security_path_replaced_by_narrower_child_is_refused(self):
        d = self.derive()
        p = self.proposal(d)
        p["security_paths"] = [x for x in p["security_paths"] if x != "src/auth"] + ["src/auth/login.js"]
        self.assertEqual(D.check(d, p)["reasons"], ["differs:security_paths"])

    def test_excluded_paths_only_widen(self):
        d = self.derive()
        p = {"excluded_paths": d["excluded_paths"] + ["more"]}
        self.assertTrue(D.check(d, p)["ok"])
        p = {"excluded_paths": ["vendor"]}
        self.assertEqual(D.check(d, p)["reasons"], ["narrowed:excluded_paths:/legacy/*.js"])
        # anchoring "vendor" (any depth) to "/vendor" (root only) narrows it
        p = {"excluded_paths": ["/vendor", "/legacy/*.js"]}
        self.assertEqual(D.check(d, p)["reasons"], ["narrowed:excluded_paths:vendor"])
        # a wider directory covers an anchored path below it; a pattern is kept only as written
        self.add({"sub/CLAUDE.md": "x"})
        d = self.derive()
        self.assertTrue(D.check(d, {"excluded_paths": ["vendor", "/legacy/*.js", "sub"]})["ok"])
        self.assertFalse(D.check(d, {"excluded_paths": ["vendor", "/legacy/*", "sub"]})["ok"])

    def test_unknown_and_malformed_fields_are_refused(self):
        d = self.derive()
        self.assertEqual(D.check(d, {"banned_constructs": {}})["reasons"], ["field_not_derived:banned_constructs"])
        self.assertEqual(D.check(d, {"security_paths": "src"})["reasons"], ["malformed:security_paths"])
        self.assertEqual(D.check(d, "x")["reasons"], ["malformed:proposal"])

    # ------------------------------------------------------------ command line

    def run_cli(self, *args):
        proc = subprocess.run([sys.executable, "-m", "profile.derive", *args], cwd=REFEREE,
                              capture_output=True, text=True, timeout=60)
        lines = proc.stdout.splitlines()
        self.assertEqual(len(lines), 1, proc.stdout + proc.stderr)
        return proc.returncode, json.loads(lines[0])

    def test_cli(self):
        target = os.path.join(self.base, "target.json")
        with open(target, "w") as fh:
            json.dump(self.target, fh)
        code, out = self.run_cli("derive", self.tree, "--target", target)
        self.assertEqual(code, 0)
        self.assertEqual(out, json.loads(json.dumps(self.derive())))
        prop = os.path.join(self.base, "p.json")
        for proposal, want in ((self.proposal(out), 0), ({"security_paths": out["security_paths"][1:]}, 1)):
            with open(prop, "w") as fh:
                json.dump(proposal, fh)
            code, report = self.run_cli("check", self.tree, prop, "--target", target)
            self.assertEqual((code, report["ok"]), (want, want == 0))
        code, out = self.run_cli("derive", os.path.join(self.base, "missing"))
        self.assertEqual(code, 2)
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
