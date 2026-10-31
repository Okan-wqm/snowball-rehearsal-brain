"""``status.depmap`` (run with test 42, the generated views): the dependency drawings are generated from code, and
the brain's committed drawing is the one its code gives today.

- the brain: the committed ``docs/map/brain.md`` equals what ``referee/`` gives now (a stale drawing is red); every
  import form names the module the rules say (``import a.b``, ``from a import b`` as a submodule or as a name,
  relative levels, a function-local import, an import of no module under the root, a relative import above the
  top); ``tests/``, hidden directories and ``__pycache__`` are not read; a file that does not parse is listed;
- live: the roots are the modules a workflow starts with ``python -m``/``python3 -m``, a started module that is
  not under the root is external, live is reachability by imports plus the packages holding a live module;
- the register of the off-live: the brain's ``status/off_live.json`` has no problem; each problem
  (``off_live_unnamed``, ``named_but_live``, ``named_unknown``, ``entry_invalid``, ``register_unreadable``) on a
  tree made for it, an empty package (docstring only) not named and one with code named; the drawing's last column;
- the target: projects from the root's npm workspaces (globs, ``**``, negation), Nx ``project.json``, the root
  Cargo workspace (members minus exclude) and ``pyproject.toml``; ``SKIP_DIRS`` and symbolic links not entered;
  arrows ``npm``, ``cargo`` (``path`` and ``workspace = true``), ``import`` (relative, bare workspace name and
  subpath, tsconfig alias exact and wildcard with ``baseUrl``, a commented tsconfig) and ``python``; the deepest
  project owns a file; the coverage counts each specifier's outcome;
- the helpers: segment globs, the tsconfig dialect keeps ``//`` inside strings;
- the command line: exits 0, 1 (``check`` with a problem) and 2.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from typing import Any

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAIN = os.path.dirname(REFEREE)
sys.path.insert(0, REFEREE)

from status import depmap as D  # noqa: E402


def write(root: str, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)


class Brain(unittest.TestCase):
    def test_committed_brain_drawing_is_current(self):
        with open(os.path.join(BRAIN, "docs", "map", "brain.md"), encoding="utf-8") as f:
            committed = f.read()
        self.assertEqual(D.render_brain(D.brain_map(REFEREE)), committed,
                         "docs/map/brain.md is stale: regenerate it with "
                         "'python -m status.depmap brain . > ../docs/map/brain.md' from referee/")

    def tree(self) -> str:
        root = tempfile.mkdtemp()
        write(root, {
            "pkg/__init__.py": "",
            "pkg/a.py": "import pkg.b\nimport os.path\n",
            "pkg/b.py": "from . import c\n",
            "pkg/c.py": "from .d import helper\nimport pkg.c\n",
            "pkg/d.py": "def f():\n    import top\n",
            "pkg/sub/__init__.py": "from .. import a\n",
            "pkg/sub/e.py": "from ..sub import f\nfrom pkg.sub.f import g\n",
            "pkg/sub/f.py": "from pkg import missing_name\n",
            "top.py": "from pkg import a, nothere\nfrom ... import x\n",
            "lone.py": "import json\nif __name__ == '__main__':\n    pass\n",
            "broken.py": "def (:\n",
            "tests/test_x.py": "import pkg.a\n",
            ".hidden/h.py": "import pkg.a\n",
            ".github/workflows/w.yml": "jobs:\n  a:\n    run: |\n      python3 -m pkg.a run\n"
                                       "      python -m outside.mod\n",
        })
        return root

    def test_import_forms(self):
        m = D.brain_map(self.tree())
        self.assertEqual(sorted(m["modules"]), ["broken", "lone", "pkg", "pkg.a", "pkg.b", "pkg.c", "pkg.d",
                                                 "pkg.sub", "pkg.sub.e", "pkg.sub.f", "top"])
        self.assertEqual(m["edges"], {
            "broken": [], "lone": [], "pkg": [],
            "pkg.a": ["pkg.b"],                    # import pkg.b; os.path is not under the root
            "pkg.b": ["pkg.c"],                    # from . import c: a submodule
            "pkg.c": ["pkg.d"],                    # from .d import helper: the module, not the name; itself: none
            "pkg.d": ["top"],                      # inside a function
            "pkg.sub": ["pkg.a"],                  # from .. in a package's __init__
            "pkg.sub.e": ["pkg.sub.f"],            # from ..sub import f; from pkg.sub.f import g
            "pkg.sub.f": ["pkg"],                  # a name of the package
            "top": ["pkg", "pkg.a"],               # a submodule and a name; from ... above the top is nothing
        })
        self.assertEqual(m["unparsed"], ["broken.py"])
        self.assertEqual(m["entry_points"], ["lone"])

    def test_live_roots_and_reachability(self):
        m = D.brain_map(self.tree())
        self.assertEqual(m["roots"], ["pkg.a"])
        self.assertEqual(m["external_roots"], ["outside.mod"])
        # pkg.a -> b -> c -> d -> top -> pkg; pkg is also live as the package holding pkg.a
        self.assertEqual(m["live"], ["pkg", "pkg.a", "pkg.b", "pkg.c", "pkg.d", "top"])
        self.assertEqual(m["off_live"], ["broken", "lone", "pkg.sub", "pkg.sub.e", "pkg.sub.f"])

    def test_package_of_a_live_module_is_live_without_an_arrow(self):
        root = tempfile.mkdtemp()
        write(root, {"p/__init__.py": "", "p/q/__init__.py": "", "p/q/r.py": "",
                     ".github/workflows/w.yaml": "run: python -m p.q.r\n"})
        m = D.brain_map(root)
        self.assertEqual(m["live"], ["p", "p.q", "p.q.r"])
        self.assertEqual(m["edges"], {"p": [], "p.q": [], "p.q.r": []})

    def test_drawing_marks_roots_and_lists_every_module(self):
        text = D.render_brain(D.brain_map(self.tree()), "a tree")
        self.assertIn("```mermaid", text)
        self.assertIn('[["pkg.a"]]', text)          # the root's double border
        self.assertIn("outside.mod", text)
        self.assertIn("broken.py", text)
        for line in ("| pkg.a | pkg/a.py | root |  | pkg.b | pkg.sub, top |  |",
                     "| lone | lone.py | no | yes |  |  |  |",
                     "| top | top.py | yes |  | pkg, pkg.a | pkg.d |  |"):
            self.assertIn(line, text)


class Register(unittest.TestCase):
    """The register of the off-live (``status/off_live.json``): every module off the live path is named with its
    reason, a named module is not live, and an empty package is not named."""

    def test_the_brains_register_has_no_problem(self):
        m = D.brain_map(REFEREE)
        self.assertEqual(D.register_problems(m), [])
        self.assertTrue(m["off_live"])      # the check is not vacuous today

    def tree(self, register: Any = None, raw: bytes | None = None) -> dict:
        root = tempfile.mkdtemp()
        write(root, {
            "pkg/__init__.py": "",
            "pkg/a.py": "import pkg.b\n",
            "pkg/b.py": "",
            "tool.py": "",
            "doc/__init__.py": '"""Only a docstring."""\n',
            "doc/m.py": "",
            "code/__init__.py": "X = 1\n",
            "code2/__init__.py": '"""A docstring, then code."""\nX = 1\n',
            "num/__init__.py": "1\n",
            "status/__init__.py": "",
            ".github/workflows/w.yml": "run: python -m pkg.a\n",
        })
        if raw is not None or register is not None:
            with open(os.path.join(root, "status", "off_live.json"), "wb") as f:
                f.write(raw if raw is not None else json.dumps(register).encode())
        return D.brain_map(root)

    OK = {"kind": "unwired", "why": "waits for its caller"}

    def test_off_live_modules_must_be_named_and_empty_packages_need_not(self):
        m = self.tree()
        self.assertEqual(m["empty_packages"], ["doc", "pkg", "status"])
        self.assertEqual(m["off_live"], ["code", "code2", "doc", "doc.m", "num", "status", "tool"])
        # absent file: an empty register; doc and status are empty packages; code, code2 (a docstring and code)
        # and num (a constant that is not a string) hold code
        self.assertEqual(D.register_problems(m), ["off_live_unnamed:code", "off_live_unnamed:code2",
                                                  "off_live_unnamed:doc.m", "off_live_unnamed:num",
                                                  "off_live_unnamed:tool"])
        named = {"code": self.OK, "code2": self.OK, "doc.m": self.OK, "num": self.OK,
                 "tool": {"kind": "session_tool", "why": "run by hand"}}
        self.assertEqual(D.register_problems(self.tree(named)), [])
        for missing in named:
            self.assertEqual(D.register_problems(self.tree({k: v for k, v in named.items() if k != missing})),
                             ["off_live_unnamed:%s" % missing])

    def test_named_but_live_unknown_and_empty_package(self):
        base = {"code": self.OK, "code2": self.OK, "doc.m": self.OK, "num": self.OK, "tool": self.OK}
        for name, problem in (("pkg.a", "named_but_live:pkg.a"), ("pkg.b", "named_but_live:pkg.b"),
                              ("pkg", "named_unknown:pkg"), ("gone", "named_unknown:gone"),
                              ("doc", "named_unknown:doc"), ("status", "named_unknown:status")):
            self.assertEqual(D.register_problems(self.tree(dict(base, **{name: self.OK}))), [problem], name)

    def test_entry_shape(self):
        base = {"code": self.OK, "code2": self.OK, "doc.m": self.OK, "num": self.OK}
        for entry in ("unwired", None, {"kind": "unwired"}, {"why": "x"}, dict(self.OK, extra=1),
                      {"kind": "package", "why": "x"}, {"kind": "Unwired", "why": "x"}, {"kind": "unwired", "why": ""},
                      {"kind": "unwired", "why": " \n\t"}, {"kind": "unwired", "why": 3}, {"kind": 1, "why": "x"}):
            self.assertEqual(D.register_problems(self.tree(dict(base, tool=entry))), ["entry_invalid:tool"], entry)
        # an invalid entry for a live or unknown name is reported twice, sorted
        self.assertEqual(D.register_problems(self.tree(dict(base, tool=self.OK, **{"pkg.a": None}))),
                         ["entry_invalid:pkg.a", "named_but_live:pkg.a"])

    def test_unreadable_register_stops_the_check(self):
        for raw in (b"[]", b"{", b"\xff\xfe", b"null", b'"x"', b"[" * 100000):
            self.assertEqual(D.register_problems(self.tree(raw=raw)), ["register_unreadable"], raw[:8])

    def test_drawing_shows_each_reason(self):
        m = self.tree({"code": self.OK, "code2": self.OK, "num": self.OK,
                       "doc.m": {"kind": "unwired", "why": "a | b\nc"},
                       "tool": {"kind": "session_tool", "why": "by hand"}})
        text = D.render_brain(m, "a tree")
        self.assertIn("Register problems: none.", text)
        for line in ("| tool | tool.py | no |  |  |  | session_tool: by hand |",
                     "| doc.m | doc/m.py | no |  |  |  | unwired: a \\| b c |",
                     "| doc | doc/__init__.py | no |  |  |  | empty package |",
                     "| pkg | pkg/__init__.py | yes |  |  |  |  |"):
            self.assertIn(line, text)
        self.assertIn("Register problems: off_live_unnamed:code, off_live_unnamed:code2, off_live_unnamed:doc.m, "
                      "off_live_unnamed:num, off_live_unnamed:tool.",
                      D.render_brain(self.tree(), "a tree"))


class Target(unittest.TestCase):
    def checkout(self) -> str:
        root = tempfile.mkdtemp()
        write(root, {
            "package.json": json.dumps({"workspaces": ["apps/*", "libs/**", "!libs/skip"]}),
            "apps/web/package.json": json.dumps({"name": "@t/web", "dependencies": {"@t/ui": "*", "react": "1"},
                                                 "devDependencies": {"x": "*"}}),
            "apps/web/src/main.ts": "\n".join([
                "import { u } from '@t/util';",
                'export * from "@t/feat/a";',
                "const y = require('../../../libs/deep/x/i');",
                "const r = import('react');",
                "import './local';",
                "import { b } from '@t/ui/button';",
                "// import { z } from '@t/web-old';",
                "import { gone } from '../../../../outside';",
                "import { s } from '../../../scripts/s';",
                ""]),
            "apps/web/src/local.ts": "export const l = 1;\n",
            "apps/web/project.json": json.dumps({"name": "web-nx"}),
            "apps/web/node_modules/q/index.js": "require('@t/ui')\n",
            "apps/web/dist/out.js": "require('@t/ui')\n",
            "libs/ui/package.json": json.dumps({"name": "@t/ui"}),
            "libs/ui/index.js": "module.exports = require('@t/web');\n",
            "libs/skip/package.json": json.dumps({"name": "skip"}),
            "libs/deep/x/package.json": json.dumps({"name": "x"}),
            "libs/deep/x/i.js": "",
            "libs/util/project.json": json.dumps({}),
            "libs/feat/a/project.json": json.dumps({"name": "feat-a"}),
            "libs/feat/a/src/inner/project.json": json.dumps({"name": "feat-a-inner"}),
            "tsconfig.base.json": "{\n  // aliases\n  \"compilerOptions\": {\n    \"baseUrl\": \".\",\n"
                                  "    /* the paths */\n    \"paths\": {\n"
                                  "      \"@t/util\": [\"libs/util/src/index.ts\"],\n"
                                  "      \"@t/feat/*\": [\"libs/feat/*/src\"],\n"
                                  "      \"@t/web-old\": [\"https://example.invalid/x\"],\n"
                                  "    },\n  },\n}\n",
            "scripts/s.ts": "import { u } from '@t/util';\n",
            "Cargo.toml": "[workspace]\nmembers = [\"crates/*\"]\nexclude = [\"crates/ex\"]\n"
                          "[workspace.dependencies]\nb = { path = \"crates/b\" }\nserde = \"1\"\n",
            "crates/a/Cargo.toml": "[package]\nname = \"a\"\n[dependencies]\nb = { path = \"../b\" }\nserde = \"1\"\n",
            "crates/b/Cargo.toml": "[package]\nname = \"b\"\n",
            "crates/c/Cargo.toml": "[package]\nname = \"c\"\n[target.'cfg(unix)'.dev-dependencies]\n"
                                   "b = { workspace = true }\n",
            "crates/ex/Cargo.toml": "[package]\nname = \"ex\"\n[dependencies]\nb = { path = \"../b\" }\n",
            "py/pyproject.toml": "[project]\nname = \"pyk\"\n",
            "py/src/pyk/__init__.py": "",
            "py/pyk2/__init__.py": "from pyk import core\nfrom . import rel\n",
            "libs/util/tool.py": "import pyk2.mod\nimport os\n",
            "scripts/run.py": "from pyk import z\n",
            "scripts/bad.py": "def (:\n",
            "scripts/run.sh": "echo\n",
        })
        os.symlink(os.path.join(root, "libs", "ui"), os.path.join(root, "libs", "link"))
        return root

    def test_projects(self):
        m = D.target_map(self.checkout())
        self.assertEqual([(p["dir"], p["name"], p["kinds"]) for p in m["projects"]], [
            ("apps/web", "@t/web", ["npm", "nx"]),
            ("crates/a", "a", ["cargo"]),
            ("crates/b", "b", ["cargo"]),
            ("crates/c", "c", ["cargo"]),
            ("libs/deep/x", "x", ["npm"]),              # ** reaches it
            ("libs/feat/a", "feat-a", ["nx"]),
            ("libs/feat/a/src/inner", "feat-a-inner", ["nx"]),
            ("libs/ui", "@t/ui", ["npm"]),              # libs/skip negated, libs/link a symbolic link
            ("libs/util", "util", ["nx"]),              # no name: the directory's last segment
            ("py", "pyk", ["python"]),
        ])

    def test_edges(self):
        m = D.target_map(self.checkout())
        self.assertEqual([(e["from"], e["to"], e["kinds"]) for e in m["edges"]], [
            ("apps/web", "libs/deep/x", ["import", "npm"]),  # a relative path; and devDependencies names x
            ("apps/web", "libs/feat/a", ["import"]),        # wildcard alias; the deepest project is feat/a
            ("apps/web", "libs/ui", ["import", "npm"]),     # manifest and a bare subpath import
            ("apps/web", "libs/util", ["import"]),          # exact alias, baseUrl
            ("crates/a", "crates/b", ["cargo"]),            # path
            ("crates/c", "crates/b", ["cargo"]),            # workspace = true, in a [target.*] table
            ("libs/ui", "apps/web", ["import"]),            # require of a workspace name
            ("libs/util", "py", ["python"]),                # pyk2 is a package of py (no src/)
        ])

    def test_coverage(self):
        cov = D.target_map(self.checkout())["coverage"]
        self.assertEqual(cov["projects_by_kind"], {"npm": 3, "nx": 4, "cargo": 3, "python": 1})
        self.assertEqual(cov["source_files"], 5)       # main, local, libs/ui, i.js, scripts/s.ts; not dist, node_modules
        self.assertEqual(cov["source_files_outside_projects"], 1)
        self.assertEqual(cov["python_files"], 4)
        self.assertEqual(cov["python_files_unparsed"], 1)
        self.assertEqual(cov["specifiers"], {
            "cross_project": 6,       # util, feat/a, deep/x, ui/button (main.ts); @t/web (ui); pyk2 (tool.py)
            "same_project": 2,        # ./local; pyk2's from pyk import core
            "external_package": 1,    # react
            "outside_projects": 4,    # the commented-out @t/web-old (an alias to no project), main.ts into
                                      # scripts/, scripts/s.ts's import, scripts/run.py's pyk
            "leaves_root": 1,         # ../../../../outside
            "python_external": 1,     # os
            "python_relative": 1,     # from . import rel
        })
        self.assertEqual(cov["unread_code_files"], {".sh": 1})

    def test_render_lists_every_project_and_arrow(self):
        text = D.render_target(D.target_map(self.checkout()), "a test checkout")
        self.assertIn("a test checkout", text)
        self.assertIn("| @t/web | apps/web | npm nx | x (import npm), feat-a (import), @t/ui (import npm), util (import) |",
                      text)
        self.assertEqual(text.count(" -->|"), 8)


class Helpers(unittest.TestCase):
    def test_globs(self):
        dirs = ["apps", "apps/a", "apps/a/b", "libs/x", "abc/d", "axc/d", "a.b/c"]
        self.assertEqual(D.glob_dirs(["apps/*"], dirs), ["apps/a"])
        self.assertEqual(D.glob_dirs(["apps/**"], dirs), ["apps", "apps/a", "apps/a/b"])
        self.assertEqual(D.glob_dirs(["**/d"], dirs), ["abc/d", "axc/d"])
        self.assertEqual(D.glob_dirs(["a?c/*", "!axc/*"], dirs), ["abc/d"])
        self.assertEqual(D.glob_dirs(["a.b/*"], dirs + ["axb/c"]), ["a.b/c"])
        self.assertEqual(D.glob_dirs(["./libs/*/"], dirs), ["libs/x"])

    def test_exact_alias_before_wildcard(self):
        root = tempfile.mkdtemp()
        write(root, {"tsconfig.json": json.dumps({"compilerOptions": {"baseUrl": "src",
                                                                      "paths": {"@a/*": ["w/*"], "@a/b": ["e"]}}})})
        cov = {"unparsed_manifests": []}
        aliases = D._tsconfig_aliases(root, {"tsconfig.json"}, cov)
        self.assertEqual(D._alias_path("@a/b", aliases), "src/e")
        self.assertEqual(D._alias_path("@a/c/d", aliases), "src/w/c/d")
        self.assertIsNone(D._alias_path("@ab", aliases))

    def test_jsonc_keeps_strings(self):
        self.assertEqual(D.jsonc_loads('{"u": "http://x/*y*/", // c\n "v": [1,],}'), {"u": "http://x/*y*/", "v": [1]})
        self.assertEqual(D.jsonc_loads('{"q": "a\\"//b"}'), {"q": 'a"//b'})


class CommandLine(unittest.TestCase):
    def run_cli(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-m", "status.depmap", *argv], cwd=REFEREE, capture_output=True,
                              text=True)

    def test_exits(self):
        root = tempfile.mkdtemp()
        write(root, {"a.py": "import b\n", "b.py": ""})
        ok = self.run_cli("brain", root)
        self.assertEqual(ok.returncode, 0)
        self.assertIn("| a | a.py | no |  | b |  |", ok.stdout)
        cov = self.run_cli("coverage", root)
        self.assertEqual(cov.returncode, 0)
        self.assertEqual(json.loads(cov.stdout)["files"], 2)
        self.assertEqual(self.run_cli("target", root, "--source", "x").returncode, 0)
        bad = self.run_cli("check", root)
        self.assertEqual((bad.returncode, json.loads(bad.stdout)),
                         (1, {"ok": False, "problems": ["off_live_unnamed:a", "off_live_unnamed:b"]}))
        write(root, {"status/off_live.json": json.dumps({n: {"kind": "unwired", "why": "w"} for n in "ab"})})
        good = self.run_cli("check", root)
        self.assertEqual((good.returncode, json.loads(good.stdout)), (0, {"ok": True, "problems": []}))
        for argv in ([], ["brain"], ["check"], ["check", root, "extra"], ["brain", os.path.join(root, "nope")], ["target", root], ["other", root],
                     ["brain", root, "extra"]):
            self.assertEqual(self.run_cli(*argv).returncode, 2, argv)


if __name__ == "__main__":
    unittest.main()
