"""``profile.jsimports``: the one reader of a JS/TS tree's references (``status.depmap`` and ``profile.fit``).

- ``specifiers``: each import form; an import inside a comment, a string, a template or a regular expression is
  not one; a ``/`` after an operand is division; a ``'`` string ends at the line's end; the specifier is read from
  the text as written;
- ``extends``: a string, a list, comments and trailing commas, nothing when the text does not parse;
- ``jest_preset``: the first ``preset`` key of the code (quoted or not; not in a comment, a string, an assignment
  or a longer name), only a string value, none when the code names ``rootDir``; the config names;
- ``aliases``: exact before ``*``, ``baseUrl`` (one leaving the root is the root), the first target only;
  ``alias_file``'s order; a text that does not parse raises;
- ``package_name`` and ``is_relative``; ``walk``: ``SKIP_DIRS`` and links are not entered;
- ``code_view``, which passes code between two of ``/ ' " ` `` whole: the same view as ``reference_view``, the
  lexer read one character at a time (the rules as first written, kept here as the oracle), on texts drawn from
  the lexer's delimiters, blanks, words and ``REGEX_WORDS`` (a fixed seed).
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

import random  # noqa: E402

from profile import jsimports as J  # noqa: E402


def reference_view(text: str) -> str:
    """``code_view``'s rules read one character at a time."""
    out = list(text)
    i, n = 0, len(text)
    last = ""
    word = ""
    while i < n:
        c = text[i]
        if text.startswith("//", i) or text.startswith("/*", i):
            end = text.find("\n", i) if text[i + 1] == "/" else text.find("*/", i + 2)
            end = n if end < 0 else end if text[i + 1] == "/" else end + 2
            for k in range(i, end):
                out[k] = "\n" if text[k] == "\n" else " "
            i = end
        elif c in "'\"`" or (c == "/" and (last == "" or last in J.REGEX_AFTER or word in J.REGEX_WORDS)):
            j, in_class = i + 1, False
            while j < n:
                d = text[j]
                if d == "\\":
                    j += 2
                    continue
                if d == "\n" and c != "`":
                    break
                if c == "/" and d in "[]":
                    in_class = d == "["
                elif d == c and not in_class:
                    break
                j += 1
            for k in range(i + 1, min(j, n)):
                out[k] = text[k] if text[k] == "\n" else J.FILL
            i, last, word = j + 1, c, ""
        else:
            if not c.isspace():
                word = word + c if (c.isalnum() or c in "_$") and (last.isalnum() or last in "_$") else \
                    (c if c.isalnum() or c in "_$" else "")
                last = c
            i += 1
    return "".join(out)


PIECES = ["/", "//", "/*", "*/", "'", '"', "`", "\\", "\n", "\r\n", " ", "\t", "[", "]", "(", ")", "=", "!",
          "}", "{", "${", ";", "+", "x", "a1", "_", "$", "\u00e9", "\u0661", "ab cd", "import", " from ",
          "'a'", "require('b')"] + sorted(J.REGEX_WORDS)


class Specifiers(unittest.TestCase):
    def test_each_form(self):
        text = "\n".join([
            "import a from 'a';",
            'import { b1, b2 } from "b";',
            "import * as c from 'c'",
            "export * from './d';",
            "export { e } from '@s/e/sub';",
            "import 'f';",
            "const g = require('g');",
            "const h = await import('h');",
            "import type { T } from 'types';",
            "import {\n  m,\n  n,\n} from 'multi';",
        ])
        self.assertEqual(J.specifiers(text), ["a", "b", "c", "./d", "@s/e/sub", "f", "g", "h", "types", "multi"])

    def test_comments_strings_templates_and_regexes_are_not_code(self):
        text = "\n".join([
            "// import a from 'line-comment';",
            "/* import b from 'block'",
            "   require('block2') */ import real1 from 'real1';",
            "const s = 'import c from \"in-single\"';",
            'const d = "require(\'in-double\')";',
            "const t = `import e from 'in-template'\n require('template-line-2')`;",
            "const r = /import f from 'in-regex'/;",
            "if (x) return /require('after-return')/.test(y);",
            "const q = a / b; import real2 from 'real2'; const z = c / d;",
            "import real3 from 'real3'",
        ])
        self.assertEqual(J.specifiers(text), ["real1", "real2", "real3"])

    def test_the_view_keeps_lengths_newlines_and_the_specifier_as_written(self):
        text = "import a from 'x/y'; // c\n'q'\n"
        view = J.code_view(text)
        self.assertEqual((len(view), view.count("\n")), (len(text), text.count("\n")))
        self.assertEqual(view, "import a from '" + J.FILL * 3 + "';     \n'" + J.FILL + "'\n")
        self.assertEqual(J.specifiers(text), ["x/y"])

    def test_an_apostrophe_blanks_the_rest_of_its_line_only(self):
        text = "<p>Don't</p>; import lost from 'lost'\nimport kept from 'kept'\n"
        self.assertEqual(J.specifiers(text), ["kept"])

    def test_escapes_and_regex_classes(self):
        text = "\n".join([
            "const a = 'it\\'s'; import one from 'one';",
            "const re = /[/']/; import two from 'two';",
            "const b = \"\\\\\"; import three from 'three';",
        ])
        self.assertEqual(J.specifiers(text), ["one", "two", "three"])

    def test_the_view_is_the_reference_lexers(self):
        rng = random.Random(20261104)
        for _ in range(30000):
            text = "".join(rng.choice(PIECES) for _ in range(rng.randint(0, 30)))
            self.assertEqual(J.code_view(text), reference_view(text), repr(text))

    def test_a_long_run_of_code_is_read_for_its_last_word(self):
        # blanks between word characters do not end a word (the rule as written); a non-word character does
        for text in ("x = 1 +\n  typeof /a'/", "a.  return /b'/", "await  /c'/", "1 + 2 / 3 / 'd'", "x\nreturn /e'/"):
            self.assertEqual(J.code_view(text), reference_view(text), text)

    def test_a_specifier_that_is_not_a_string_literal_is_not_read(self):
        self.assertEqual(J.specifiers("const m = require(name); import(`x/${y}`);"), [])


class Extends(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(J.extends('{"extends": "../../tsconfig.base.json"}'), ["../../tsconfig.base.json"])
        self.assertEqual(J.extends('{\n // c\n "extends": ["./a", "@w/tsconfig/b.json", 3, ""],\n}'),
                         ["./a", "@w/tsconfig/b.json"])
        self.assertEqual(J.extends('{"compilerOptions": {}}'), [])
        self.assertEqual(J.extends("not json"), [])
        self.assertEqual(J.extends("[1]"), [])


class JestPreset(unittest.TestCase):
    def test_the_first_preset_key_of_the_code(self):
        cases = {
            "export default {\n  displayName: 'x',\n  preset: '../../jest.preset.js',\n};": "../../jest.preset.js",
            'module.exports = {"preset": "ts-jest", preset2: "no"};': "ts-jest",
            "// preset: 'commented'\nmodule.exports = { preset: 'real' };": "real",
            "const doc = \"preset: 'quoted'\"; module.exports = { preset: 'real' };": "real",
            "config.preset = 'assigned'; const o = { mypreset: 'x', a.preset: 'y' };": None,
            "module.exports = { preset: base };": None,
            "module.exports = {};": None,
            "module.exports = { 'my preset': 'spaced', preset: 'real' };": "real",
        }
        for text, preset in cases.items():
            self.assertEqual(J.jest_preset(text), preset, text)

    def test_a_root_dir_in_code_gives_none(self):
        self.assertIsNone(J.jest_preset("export default { rootDir: '..', preset: './p.js' };"))
        self.assertIsNone(J.jest_preset("export default { 'rootDir': '..', preset: './p.js' };"))
        self.assertEqual(J.jest_preset("/* rootDir: '..' */ const s = 'rootDir: 1'; export default { preset: './p' };"),
                         "./p")

    def test_the_config_names(self):
        self.assertEqual([bool(J.JEST_CONFIG.fullmatch(n)) for n in
                          ("jest.config.ts", "jest.config.cts", "jest.config.mjs", "jest.config.json",
                           "jest.preset.js")],
                         [True, True, True, False, False])


class Aliases(unittest.TestCase):
    def test_exact_alias_before_wildcard(self):
        table = J.aliases(json.dumps({"compilerOptions": {"baseUrl": "src",
                                                          "paths": {"@a/*": ["w/*", "z/*"], "@a/b": ["e"]}}}))
        self.assertEqual(J.alias_path("@a/b", table), "src/e")
        self.assertEqual(J.alias_path("@a/c/d", table), "src/w/c/d")
        self.assertIsNone(J.alias_path("@ab", table))

    def test_base_url_leaving_the_root_is_the_root(self):
        for base in ("..", "../x", "/abs", "."):
            table = J.aliases(json.dumps({"compilerOptions": {"baseUrl": base, "paths": {"@a": ["libs/a"]}}}))
            self.assertEqual(J.alias_path("@a", table), "libs/a", base)

    def test_the_alias_file_and_an_unparsable_one(self):
        self.assertEqual(J.alias_file({"tsconfig.json", "tsconfig.base.json"}), "tsconfig.base.json")
        self.assertEqual(J.alias_file({"tsconfig.json"}), "tsconfig.json")
        self.assertIsNone(J.alias_file({"libs/a/tsconfig.base.json"}))
        with self.assertRaises(ValueError):
            J.aliases("{")

    def test_jsonc_keeps_strings(self):
        self.assertEqual(J.jsonc_loads('{"u": "http://x/*y*/", // c\n "v": [1,],}'), {"u": "http://x/*y*/", "v": [1]})
        self.assertEqual(J.jsonc_loads('{"q": "a\\"//b"}'), {"q": 'a"//b'})


class Names(unittest.TestCase):
    def test_package_name(self):
        cases = {"@s/n/x/y": "@s/n", "@s/n": "@s/n", "n/x": "n", "n": "n", "./a": None, "../a": None, ".": None,
                 "..": None, "/abs": None, "node:fs": None, "#internal": None, "https://x/y": None, "@s": None,
                 "@/components/ai": None, "a\\b": None}
        for spec, name in cases.items():
            self.assertEqual(J.package_name(spec), name, spec)

    def test_is_relative(self):
        self.assertEqual([J.is_relative(s) for s in (".", "..", "./a", "../a", ".a", "a/./b")],
                         [True, True, True, True, False, False])


class Walk(unittest.TestCase):
    def test_skip_dirs_and_links_are_not_entered(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        for rel in ("a/x.ts", "a/node_modules/m/i.js", "dist/o.js", "b/c/y.js"):
            os.makedirs(os.path.join(root, os.path.dirname(rel)), exist_ok=True)
            open(os.path.join(root, rel), "w").close()
        os.symlink(os.path.join(root, "a"), os.path.join(root, "link"))
        os.symlink(os.path.join(root, "a", "x.ts"), os.path.join(root, "b", "l.ts"))
        self.assertEqual(J.walk(root), (["a/x.ts", "b/c/y.js"], ["", "a", "b", "b/c"]))


if __name__ == "__main__":
    unittest.main()
