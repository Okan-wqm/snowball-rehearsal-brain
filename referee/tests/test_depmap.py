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
- the target: projects from the root's npm workspaces (globs, ``**``, negation), Nx ``project.json``, every Cargo
  ``[package]`` (an excluded one too; a virtual manifest is none) and ``pyproject.toml``; ``SKIP_DIRS`` and
  symbolic links not entered; arrows ``npm``, ``cargo`` (``path``, ``workspace = true``, ``[patch.crates-io]``,
  each through the workspace root Cargo finds: ``Cargo`` below), ``import`` (relative, bare workspace name and
  subpath, tsconfig alias exact and wildcard with ``baseUrl``, a commented tsconfig) and ``python``; the deepest
  project owns a file; the coverage counts each specifier's outcome and the Python files in no project;
- ``sys.path`` (``SysPath``): a directory a Python file inserts becomes a ``path`` box when no manifest's project
  holds it (nested ones both, a missing one none, one inside a project none), an import through it draws
  ``sys.path`` (a module file or a directory, before a ``pyproject.toml`` package), the coverage's ``sys_path`` and
  the drawing's line; ``RootPackages``: a package or namespace directory an import reaches through the root's
  insertion becomes a ``path`` box (a module file at the root, a directory a project holds: none), Python's finder
  order in ``sys_path_target`` (package, module, then namespace);
- the unread manifests: counted by the first ``MANIFESTS_NOT_READ`` pattern a file's name matches (case-sensitive,
  the name only, a near name not counted), a ``package.json`` outside the npm workspace projects (an Nx project's,
  an unparsed workspace's) counted and the root's not, ``SKIP_DIRS`` not entered; three examples in path order and
  the drawing's line;
- the helpers: segment globs (the tsconfig dialect and the aliases are profile.jsimports's, test_profile_jsimports);
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
                "import { z } from '@t/web-old';",
                "// import { c } from '@t/ui';",
                "const doc = \"import { d } from '@t/ui'\";",
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
            "crates/a/src/lib.rs": "",
            "tools/x.rs": "",
            "infra/main.tf": "module \"m\" { source = \"./m\" }\n",
            "db/001_init.sql": "create table t (id int);\n",
            "api/schema.graphql": "type T { id: ID }\n",
            "infra/README.md": "",
            "web/site.css": "",
            "ci.yaml": "",
            "Dockerfile": "FROM scratch\n",
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
            ("crates/ex", "ex", ["cargo"]),             # excluded from the workspace, still a package
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
            ("crates/ex", "crates/b", ["cargo"]),           # path, from a package that is its own root
            ("libs/ui", "apps/web", ["import"]),            # require of a workspace name
            ("libs/util", "py", ["python"]),                # pyk2 is a package of py (no src/)
        ])

    def test_coverage(self):
        cov = D.target_map(self.checkout())["coverage"]
        self.assertEqual(cov["projects_by_kind"], {"npm": 3, "nx": 4, "cargo": 4, "python": 1, "path": 0})
        self.assertEqual(cov["source_files"], 5)       # main, local, libs/ui, i.js, scripts/s.ts; not dist, node_modules
        self.assertEqual(cov["source_files_outside_projects"], 1)
        self.assertEqual(cov["python_files"], 4)
        self.assertEqual(cov["python_files_outside_projects"], 1)  # scripts/run.py; bad.py is not parsed
        self.assertEqual(cov["python_files_unparsed"], 1)
        self.assertEqual(cov["unread_manifests"], {"package.json": {"count": 1, "examples": ["libs/skip/package.json"]}})
        self.assertEqual(cov["specifiers"], {
            "cross_project": 6,       # util, feat/a, deep/x, ui/button (main.ts); @t/web (ui); pyk2 (tool.py)
            "same_project": 2,        # ./local; pyk2's from pyk import core
            "external_package": 1,    # react
            "outside_projects": 4,    # @t/web-old (an alias to no project; the commented and quoted @t/ui are
                                      # not imports, jsimports.specifiers), main.ts into
                                      # scripts/, scripts/s.ts's import, scripts/run.py's pyk
            "leaves_root": 1,         # ../../../../outside
            "python_external": 1,     # os
            "python_relative": 1,     # from . import rel
        })
        # Terraform, SQL and GraphQL are code; Markdown, CSS, YAML and a file with no extension are not
        self.assertEqual(cov["unread_code_files"], {".graphql": 1, ".rs": 2, ".sh": 1, ".sql": 1, ".tf": 1})
        self.assertEqual(cov["unread_code_files_outside_projects"],  # tools/x.rs, run.sh, infra/, db/, api/
                         {".graphql": 1, ".rs": 1, ".sh": 1, ".sql": 1, ".tf": 1})

    def test_render_lists_every_project_and_arrow(self):
        text = D.render_target(D.target_map(self.checkout()), "a test checkout")
        self.assertIn("a test checkout", text)
        self.assertIn("| @t/web | apps/web | npm nx | x (import npm), feat-a (import), @t/ui (import npm), util (import) |",
                      text)
        self.assertEqual(text.count(" -->|"), 9)
        self.assertIn("SQL, GraphQL, protobuf): .graphql 1 (1 in no project), .rs 2 (1 in no project), "
                      ".sh 1 (1 in no project), .sql 1 (1 in no project), .tf 1 (1 in no project).", text)
        self.assertIn("Python files read 4 (1 outside any project, 1 not parsed).", text)
        self.assertIn("workspaces): package.json 1 (libs/skip/package.json).", text)


class SysPath(unittest.TestCase):
    """A directory a Python file puts on ``sys.path`` (``profile.pypath``): a box of kind ``path`` when no manifest's
    project holds it, decided against those projects only; an import of a name an inserted directory of the same
    file holds resolves there (before a ``pyproject.toml`` package of the same name) and draws ``sys.path``."""

    HEAD = "import os\nimport sys\nfrom pathlib import Path\n"

    def checkout(self, extra: dict[str, str] | None = None) -> str:
        root = tempfile.mkdtemp()
        h = self.HEAD
        write(root, {
            "aria/pyproject.toml": "[project]\nname = \"aria\"\n",
            "aria/aria_k/__init__.py": "",
            "aria/tests/test_a.py": h + "_ROOT = Path(__file__).resolve().parents[2]\n"
                                    "sys.path.insert(0, str(_ROOT / 'tools' / 'poc'))\n"
                                    "import poc_mod\nimport aria_k\nimport json\n",
            "aria/tests/conf.py": h + "sys.path.insert(0, str(Path(__file__).parent))\nimport helper\n",
            "aria/tests/helper.py": "",
            "tools/poc/poc_mod.py": h + "sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'aria'))\n"
                                    "import aria_k.core\n",
            "tools/poc/sub/x.py": "import json\n",
            "tools/other/y.py": h + "sys.path.insert(0, str(Path(__file__).parent.parent))\nimport poc\n",
            "scripts/s.py": h + "sys.path.append(os.path.join(os.path.dirname(__file__), 'gone'))\n"
                                "sys.path.insert(0, os.getcwd())\n",
            "scripts/r.py": h + "sys.path.insert(0, str(Path(__file__).parents[1]))\nimport tools\n",
            "scripts/l.py": h + "sys.path.insert(0, str(Path(__file__).parents[5]))\n",
            **(extra or {}),
        })
        return root

    def test_boxes_and_arrows(self):
        m = D.target_map(self.checkout())
        self.assertEqual([(p["dir"], p["name"], p["kinds"]) for p in m["projects"]], [
            ("aria", "aria", ["python"]),
            ("tools", "tools", ["path"]),          # y.py's parent.parent; nested boxes do not hide each other
            ("tools/poc", "tools/poc", ["path"]),  # test_a.py's insertion; aria/tests is inside aria: no box
        ])
        self.assertEqual([(e["from"], e["to"], e["kinds"]) for e in m["edges"]], [
            ("aria", "tools/poc", ["sys.path"]),   # import poc_mod through tools/poc
            ("tools", "tools/poc", ["sys.path"]),  # import poc: a directory in an inserted directory
            ("tools/poc", "aria", ["sys.path"]),   # import aria_k.core through aria
        ])

    def test_coverage(self):
        cov = D.target_map(self.checkout())["coverage"]
        self.assertEqual(cov["sys_path"], {
            "calls": 8, "dirs": 6, "missing": 1, "leaves_root": 1, "unresolved": 1,
            "imports": 5,   # poc_mod, helper, aria_k.core, poc, tools (r.py: into the root's tools box)
            "unresolved_files": {"count": 1, "examples": ["scripts/s.py"]}})
        self.assertEqual(cov["projects_by_kind"]["path"], 2)
        self.assertEqual(cov["python_files_outside_projects"], 3)  # scripts/*.py; tools/** now in boxes
        sp = cov["specifiers"]
        self.assertEqual((sp["cross_project"], sp["same_project"], sp["outside_projects"]), (3, 2, 1))
        self.assertEqual(sp["python_external"], 23)  # os, sys and pathlib in 7 files, json in 2: in no inserted dir

    def test_an_inserted_directory_wins_over_a_package_and_a_missing_name_falls_through(self):
        m = D.target_map(self.checkout({"tools/poc/aria_k.py": ""}))
        edges = [(e["from"], e["to"], e["kinds"]) for e in m["edges"]]
        self.assertIn(("aria", "tools/poc", ["sys.path"]), edges)
        self.assertEqual(m["coverage"]["specifiers"]["same_project"], 1)  # aria_k now resolves in tools/poc

    def test_render(self):
        text = D.render_target(D.target_map(self.checkout()), "x")
        self.assertIn("Projects 3 (npm 0, nx 0, cargo 0, python 1, path 2), arrows 3.", text)
        self.assertIn("`sys.path` insertions in Python files: 8 calls; 6 directories resolved (1 not in the "
                      "checkout), 1 leaving the root, 1 calls or values not resolved (1 files: scripts/s.py); "
                      "5 imports resolved through them.", text)
        self.assertIn("| aria | aria | python | tools/poc (sys.path) |", text)
        self.assertIn("| tools/poc | tools/poc | path | aria (sys.path) |", text)


class RootPackages(unittest.TestCase):
    """A directory an import reaches through an inserted directory (``sys_path_target``, Python's finder order:
    package, then module, in the first directory holding one; else the first namespace directory) is a ``path``
    box when no project holds it, which only the root's insertion can give: the top-level packages."""

    HEAD = "import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"

    def checkout(self) -> str:
        root = tempfile.mkdtemp()
        write(root, {
            "app/pyproject.toml": "[project]\nname = \"app\"\n",
            "app/main.py": self.HEAD + "import tools.shared.x\nimport ns.a\nimport mod\nimport pkg\nimport both\n"
                                       "import lib\nimport app_k\nimport json\n",
            "app/app_k/__init__.py": "",
            "lib/pyproject.toml": "[project]\nname = \"lib\"\n",
            "lib/lib/__init__.py": "",
            "tools/__init__.py": "",
            "tools/shared/x.py": "import tools.shared\n",
            "tools/run.sh": "echo\n",
            "tools/poc/p.py": "",
            "ns/a.py": "",                  # a namespace package: a directory without __init__.py
            "mod.py": "",                   # a module file at the root: no box
            "pkg.py": "", "pkg/b.py": "",   # a module beats a namespace directory of the same name
            "both.py": "", "both/__init__.py": "",  # a package beats a module of the same name
            "other/o.py": "import sys\nsys.path.insert(0, '/abs')\nimport other\n",
            "scripts/s.py": "import sys\nfrom pathlib import Path\n"
                            "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'poc'))\n",
        })
        return root

    def test_boxes_and_arrows(self):
        m = D.target_map(self.checkout())
        self.assertEqual([(p["dir"], p["kinds"]) for p in m["projects"]], [
            ("app", ["python"]), ("both", ["path"]), ("lib", ["python"]), ("ns", ["path"]), ("tools", ["path"]),
            ("tools/poc", ["path"]),  # s.py's insertion; the nested box stays its own
        ])
        self.assertEqual([(e["from"], e["to"], e["kinds"]) for e in m["edges"]], [
            ("app", "both", ["sys.path"]), ("app", "lib", ["sys.path"]), ("app", "ns", ["sys.path"]),
            ("app", "tools", ["sys.path"]),
        ])

    def test_files_join_the_box_and_the_rest_is_counted(self):
        cov = D.target_map(self.checkout())["coverage"]
        # tools/shared/x.py and tools/poc/p.py are in boxes; mod.py, pkg.py, pkg/b.py, both.py (both/ is the box,
        # not the module beside it), other/o.py and scripts/s.py are not
        self.assertEqual(cov["python_files_outside_projects"], 6)
        self.assertEqual(cov["sys_path"]["imports"], 6)  # tools, ns, mod, pkg, both, lib; not app_k, json, sys, pathlib
        sp = cov["specifiers"]
        # across: tools, ns, both, lib; outside: mod and pkg (module files at the root); inside: app_k, app's own
        # pyproject package (tools/shared/x.py's tools.shared, with no insertion, is no project's package)
        self.assertEqual((sp["cross_project"], sp["outside_projects"], sp["same_project"]), (4, 2, 1))

    def test_render(self):
        text = D.render_target(D.target_map(self.checkout()), "x")
        self.assertIn("Projects 6 (npm 0, nx 0, cargo 0, python 2, path 4), arrows 4.", text)
        self.assertIn("| app | app | python | both (sys.path), lib (sys.path), ns (sys.path), tools (sys.path) |", text)

    def test_finder_order(self):
        files = {"a/t/__init__.py", "a/t.py", "b/t.py", "c/t/x.py", "d/u.py"}
        dirs = {"a", "a/t", "b", "c", "c/t", "d"}
        self.assertEqual(D.sys_path_target("t", ["a", "b"], files, dirs), "a/t")      # package before module
        self.assertEqual(D.sys_path_target("t", ["b", "a"], files, dirs), "b/t.py")   # the first directory
        self.assertEqual(D.sys_path_target("t", ["c", "b"], files, dirs), "b/t.py")   # namespace last
        self.assertEqual(D.sys_path_target("t", ["d", "c"], files, dirs), "c/t")
        self.assertIsNone(D.sys_path_target("t", ["d"], files, dirs))
        self.assertEqual(D.sys_path_target("u", ["", "d"], {"u/__init__.py", "d/u.py"}, {"", "u", "d"}), "u")


class UnreadManifests(unittest.TestCase):
    """Manifests of ecosystems the map does not read are counted by MANIFESTS_NOT_READ's patterns; a package.json
    is counted when it is not an npm workspace project's (the root's is read for its workspaces)."""

    def tree(self, files: dict[str, str]) -> dict:
        root = tempfile.mkdtemp()
        write(root, files)
        return D.target_map(root)

    def test_patterns_count_by_file_name(self):
        cov = self.tree({
            "package.json": json.dumps({"workspaces": ["apps/*"]}),
            "apps/a/package.json": json.dumps({"name": "a"}),          # a workspace: read
            "e2e/package.json": json.dumps({"name": "e"}),             # an Nx project's own: not read
            "e2e/project.json": json.dumps({"name": "e2e"}),
            "tools/sup/package.json": "{}",                            # in no workspace
            "svc/one/go.mod": "", "svc/two/go.mod": "", "svc/three/go.mod": "", "svc/four/go.mod": "",
            "requirements-dev.txt": "", "py/requirements.txt": "", "py/setup.py": "",
            "net/App.csproj": "", "jvm/build.gradle.kts": "", "rb/Gemfile": "",
            "svc/go.mod.bak": "", "Requirements.txt": "", "py/notrequirements.txt": "",  # no pattern matches
            "py/pyproject.toml": "[project]\nname = \"p\"\n", "Cargo.toml": "[workspace]\n",  # read manifests
        })["coverage"]
        self.assertEqual(cov["unread_manifests"], {
            "*.csproj": {"count": 1, "examples": ["net/App.csproj"]},
            "Gemfile": {"count": 1, "examples": ["rb/Gemfile"]},
            "build.gradle.kts": {"count": 1, "examples": ["jvm/build.gradle.kts"]},
            "go.mod": {"count": 4, "examples": ["svc/four/go.mod", "svc/one/go.mod", "svc/three/go.mod"]},
            "package.json": {"count": 2, "examples": ["e2e/package.json", "tools/sup/package.json"]},
            "requirements*.txt": {"count": 2, "examples": ["py/requirements.txt", "requirements-dev.txt"]},
            "setup.py": {"count": 1, "examples": ["py/setup.py"]},
        })
        self.assertEqual(cov["python_files"], 1)
        self.assertEqual(cov["python_files_outside_projects"], 0)  # py/setup.py lies in the py project

    def test_an_unparsed_workspace_manifest_is_unread_and_a_skipped_directory_is_not_entered(self):
        cov = self.tree({
            "package.json": json.dumps({"workspaces": ["apps/*"]}),
            "apps/a/package.json": "{",
            "apps/a/node_modules/dep/package.json": "{}",
            "apps/a/node_modules/dep/go.mod": "",
        })["coverage"]
        self.assertEqual(cov["unparsed_manifests"], ["apps/a/package.json"])
        self.assertEqual(cov["unread_manifests"], {"package.json": {"count": 1, "examples": ["apps/a/package.json"]}})

    def test_render_names_each_with_its_examples_and_none(self):
        m = self.tree({"a/go.mod": "", "b/go.mod": "", "c/go.mod": "", "d/go.mod": "", "e/pom.xml": ""})
        text = D.render_target(m, "x")
        self.assertIn("workspaces): go.mod 4 (a/go.mod, b/go.mod, c/go.mod, ...); pom.xml 1 (e/pom.xml).", text)
        self.assertIn("workspaces): none.", D.render_target(self.tree({"a.py": ""}), "x"))
        self.assertIn("Python files read 1 (1 outside any project, 0 not parsed).",
                      D.render_target(self.tree({"a.py": ""}), "x"))

    def test_the_list_is_names_only_and_distinct(self):
        self.assertEqual(len(D.MANIFESTS_NOT_READ), len(set(D.MANIFESTS_NOT_READ)))
        for p in D.MANIFESTS_NOT_READ:
            self.assertNotIn("/", p)
            self.assertNotIn(p, ("package.json", "project.json", "Cargo.toml", "pyproject.toml"))


class Cargo(unittest.TestCase):
    """Cargo packages anywhere, each dependency resolved through the workspace root Cargo finds for its package."""

    def tree(self, files: dict[str, str]) -> dict:
        root = tempfile.mkdtemp()
        write(root, files)
        m = D.target_map(root)
        return {"projects": [(p["dir"], p["name"]) for p in m["projects"]],
                "edges": [(e["from"], e["to"]) for e in m["edges"]], "unparsed": m["coverage"]["unparsed_manifests"]}

    ROOT_WS = ("[workspace]\nmembers = [\"crates/*\"]\nexclude = [\"crates/ex\", \"gw\"]\n"
               "[workspace.dependencies]\nb = { path = \"crates/b\" }\nq = \"1\"\n"
               "r = { version = \"1\", package = \"real-r\" }\ng = { git = \"https://example.invalid/g\" }\n"
               "[patch.crates-io]\nq = { path = \"vendor/q\" }\nreal-r = { path = \"vendor/r\" }\n"
               "s = { path = \"vendor/s\" }\n")

    def test_every_package_is_a_project_and_a_virtual_manifest_is_none(self):
        got = self.tree({"Cargo.toml": self.ROOT_WS,
                         "crates/a/Cargo.toml": "[package]\nname = \"a\"\n",
                         "crates/ex/Cargo.toml": "[package]\nname = \"ex\"\n",
                         "crates/nameless/Cargo.toml": "[package]\nversion = \"1\"\n",
                         "virtual/Cargo.toml": "[workspace]\nmembers = []\n",
                         "broken/Cargo.toml": "[package\n",
                         "fixtures/deep/k/Cargo.toml": "[package]\nname = \"k-fixture\"\n"})
        self.assertEqual(got["projects"], [("crates/a", "a"), ("crates/ex", "ex"), ("crates/nameless", "nameless"),
                                           ("fixtures/deep/k", "k-fixture")])
        self.assertEqual(got["unparsed"], ["broken/Cargo.toml"])

    def test_a_root_package_is_no_project_and_still_the_workspace_root(self):
        got = self.tree({"Cargo.toml": "[package]\nname = \"top\"\n[workspace]\n"
                                       "[patch.crates-io]\nq = { path = \"vendor/q\" }\n",
                         "vendor/q/Cargo.toml": "[package]\nname = \"q\"\n",
                         "a/Cargo.toml": "[package]\nname = \"a\"\n[dependencies]\nq = \"1\"\n"})
        self.assertEqual(got["projects"], [("a", "a"), ("vendor/q", "q")])
        self.assertEqual(got["edges"], [("a", "vendor/q")])

    def test_patch_and_workspace_dependencies_resolve_from_the_root(self):
        got = self.tree({"Cargo.toml": self.ROOT_WS,
                         "vendor/q/Cargo.toml": "[package]\nname = \"q\"\n",
                         "vendor/r/Cargo.toml": "[package]\nname = \"real-r\"\n",
                         "vendor/s/Cargo.toml": "[package]\nname = \"s\"\n",
                         "crates/b/Cargo.toml": "[package]\nname = \"b\"\n",
                         # a plain version, a renamed one and an inherited version string are patched
                         "crates/a/Cargo.toml": "[package]\nname = \"a\"\n[dependencies]\nq = \"1\"\n"
                                                "[dev-dependencies]\nalias = { version = \"1\", package = \"s\" }\n",
                         "crates/c/Cargo.toml": "[package]\nname = \"c\"\n[dependencies]\nq = { workspace = true }\n"
                                                "r = { workspace = true }\nb = { workspace = true }\n",
                         # a git, a registry and a missing workspace entry are not patched
                         "crates/d/Cargo.toml": "[package]\nname = \"d\"\n[dependencies]\n"
                                                "q = { git = \"https://example.invalid/q\" }\n"
                                                "s = { version = \"1\", registry = \"other\" }\n"
                                                "g = { workspace = true }\n",
                         # s is patched but no [workspace.dependencies] entry: Cargo refuses, nothing is drawn
                         "crates/e/Cargo.toml": "[package]\nname = \"e\"\n[dependencies]\ns = { workspace = true }\n"})
        self.assertEqual(got["edges"], [("crates/a", "vendor/q"), ("crates/a", "vendor/s"),
                                        ("crates/c", "crates/b"), ("crates/c", "vendor/q"), ("crates/c", "vendor/r")])

    def test_an_excluded_package_and_a_nested_workspace_are_their_own_roots(self):
        got = self.tree({"Cargo.toml": self.ROOT_WS,
                         "vendor/q/Cargo.toml": "[package]\nname = \"q\"\n",
                         "own/q/Cargo.toml": "[package]\nname = \"q\"\n",
                         # excluded, at and below the excluded path: the root's patch does not reach them
                         "crates/ex/Cargo.toml": "[package]\nname = \"ex\"\n[dependencies]\nq = \"1\"\n",
                         "crates/ex/sub/Cargo.toml": "[package]\nname = \"sub\"\n[dependencies]\nq = \"1\"\n",
                         # a nested workspace's own patch, written from its own directory
                         "gw/Cargo.toml": "[package]\nname = \"gw\"\n[workspace]\n[dependencies]\nq = \"1\"\n"
                                          "[patch.crates-io]\nq = { path = \"../own/q\" }\n",
                         "gw/fuzz/Cargo.toml": "[package]\nname = \"fz\"\n[dependencies]\nq = \"1\"\n"
                                               "gw = { path = \"..\" }\n",
                         # a member's own [patch] is ignored (Cargo reads it from the root only)
                         "crates/m/Cargo.toml": "[package]\nname = \"m\"\n[dependencies]\nq = \"1\"\n"
                                                "[patch.crates-io]\nq = { path = \"../../own/q\" }\n"})
        self.assertEqual(got["edges"], [("crates/m", "vendor/q"), ("gw", "own/q"), ("gw/fuzz", "gw"),
                                        ("gw/fuzz", "own/q")])

    def test_package_workspace_names_the_root(self):
        got = self.tree({"ws/Cargo.toml": "[workspace]\n[patch.crates-io]\nq = { path = \"../vendor/q\" }\n",
                         "vendor/q/Cargo.toml": "[package]\nname = \"q\"\n",
                         "far/p/Cargo.toml": "[package]\nname = \"p\"\nworkspace = \"../../ws\"\n"
                                             "[dependencies]\nq = \"1\"\n",
                         "far/n/Cargo.toml": "[package]\nname = \"n\"\nworkspace = \"../nowhere\"\n"
                                             "[dependencies]\nq = \"1\"\n"})
        self.assertEqual(got["edges"], [("far/p", "vendor/q")])

    def test_cargo_workspace_finds_the_root_as_cargo_does(self):
        roots = {"": {"workspace": {"exclude": ["x", 3]}}, "x/y": {"workspace": {}}}
        self.assertEqual(D.cargo_workspace("a/b", {"package": {}}, roots), "")
        self.assertIsNone(D.cargo_workspace("x", {"package": {}}, roots))
        self.assertIsNone(D.cargo_workspace("x/z", {"package": {}}, roots))
        self.assertEqual(D.cargo_workspace("xz", {"package": {}}, roots), "")   # a prefix by segments, not text
        self.assertEqual(D.cargo_workspace("x/y/z", {"package": {}}, roots), "x/y")
        self.assertEqual(D.cargo_workspace("x/y", {"package": {}}, roots), "x/y")
        self.assertIsNone(D.cargo_workspace("a", {"package": {}}, {}))


class Helpers(unittest.TestCase):
    def test_globs(self):
        dirs = ["apps", "apps/a", "apps/a/b", "libs/x", "abc/d", "axc/d", "a.b/c"]
        self.assertEqual(D.glob_dirs(["apps/*"], dirs), ["apps/a"])
        self.assertEqual(D.glob_dirs(["apps/**"], dirs), ["apps", "apps/a", "apps/a/b"])
        self.assertEqual(D.glob_dirs(["**/d"], dirs), ["abc/d", "axc/d"])
        self.assertEqual(D.glob_dirs(["a?c/*", "!axc/*"], dirs), ["abc/d"])
        self.assertEqual(D.glob_dirs(["a.b/*"], dirs + ["axb/c"]), ["a.b/c"])
        self.assertEqual(D.glob_dirs(["./libs/*/"], dirs), ["libs/x"])


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
