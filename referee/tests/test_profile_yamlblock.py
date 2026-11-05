"""``profile.yamlblock`` (run with test 47): each rule of its docstring on a text made for it, and each reason.

- lines: CRLF, comments and blanks, a leading ``---`` after a directive, ``...`` ending the document;
- block mappings (a value below, a sequence at the key's column, nothing below ``None``, quoted keys, a ``:`` not
  followed by a blank, keys kept as strings) and block sequences (``- key:`` opening a mapping at its column,
  ``- -``, ``-`` with the value below);
- scalars: plain typed by the core schema (and the YAML 1.1 words left strings), comments removed, continuations
  folded; single- and double-quoted (escapes, over lines, an escaped line break); literal and folded blocks with
  each chomping and an indentation indicator; flow collections (nested, over lines, quoted, empty values);
- anchors, aliases and merge keys (written keys win, the earlier alias wins);
- every reason of ``REASONS`` raised by a text made for it, with its line; the depth bound for block and flow.
"""

from __future__ import annotations

import os
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from profile import yamlblock as Y  # noqa: E402


class Structure(unittest.TestCase):
    def test_mappings_and_sequences(self):
        text = ("# head\n---\na: 1\nb:\n  c: x\n  d:\n  - p\n  - q: 1\n    r: 2\n  - - n\n    - m\ne:\nf:\n"
                "  -\n    g: h\n  - i\n")
        self.assertEqual(Y.load(text), {"a": 1, "b": {"c": "x", "d": ["p", {"q": 1, "r": 2}, ["n", "m"]]},
                                        "e": None, "f": [{"g": "h"}, "i"]})

    def test_a_key_ends_a_sequence_at_its_column(self):
        self.assertEqual(Y.load("a:\n- x\n- y\nb: 1\n"), {"a": ["x", "y"], "b": 1})

    def test_root_sequence_and_document_end(self):
        self.assertEqual(Y.load("%YAML 1.2\n---\n- a\n- b\n...\nnot: read\n"), ["a", "b"])

    def test_crlf_comments_blanks(self):
        self.assertEqual(Y.load("a: 1\r\n\r\n  # c\r\nb: two # c\r\n"), {"a": 1, "b": "two"})

    def test_keys(self):
        self.assertEqual(Y.load("on: push\ntrue: 1\n'q k': 2\n\"d\\tk\": 3\nurl: http://x:80/y\na:b: c\n"),
                         {"on": "push", "true": 1, "q k": 2, "d\tk": 3, "url": "http://x:80/y", "a:b": "c"})

    def test_value_on_the_next_line(self):
        self.assertEqual(Y.load("a:\n  [x, y]\nb:\n  plain\nc:\n  'q'\n"), {"a": ["x", "y"], "b": "plain", "c": "q"})


class Scalars(unittest.TestCase):
    def test_plain_types(self):
        text = ("a: ~\nb: null\nc:\nd: true\ne: FALSE\nf: 12\ng: -3\nh: 1.5\ni: .5e3\nj: yes\nk: on\nl: 0o7\n"
                "m: 1_000\nn: 'true'\n")
        self.assertEqual(Y.load(text), {"a": None, "b": None, "c": None, "d": True, "e": False, "f": 12, "g": -3,
                                        "h": 1.5, "i": 500.0, "j": "yes", "k": "on", "l": "0o7", "m": "1_000",
                                        "n": "true"})
        self.assertEqual([type(Y.load(text)[k]) for k in "fgh"], [int, int, float])

    def test_plain_comment_and_hash(self):
        self.assertEqual(Y.load("a: x#y # z\nb: '#q' # z\n- \n"[:-4]), {"a": "x#y", "b": "#q"})

    def test_plain_continuation(self):
        self.assertEqual(Y.load("a: one\n  two\n\n  three\nb: x\n- \n"[:-4]), {"a": "one two\nthree", "b": "x"})
        self.assertEqual(Y.load("- a\n  b\n- c\n"), ["a b", "c"])

    def test_quoted(self):
        text = ("a: 'it''s'\nb: \"t\\tq\\\"\\\\\\x41\\u00e9\\U0001F600\\/\"\nc: 'one\n  two\n\n  three'\n"
                "d: \"x\\\n   y\"\ne: \"\"\n")
        self.assertEqual(Y.load(text), {"a": "it's", "b": "t\tq\"\\A\u00e9\U0001F600/", "c": "one two\nthree",
                                        "d": "xy", "e": ""})

    def test_literal_blocks(self):
        text = "a: |\n  x\n   y\n\n  z\n\n\nb: |-\n  x\n\nc: |+\n  x\n\nd: |2\n    x\n  y\ne: |\nf: 1\n"
        self.assertEqual(Y.load(text), {"a": "x\n y\n\nz\n", "b": "x", "c": "x\n\n", "d": "  x\ny\n", "e": "",
                                        "f": 1})

    def test_folded_blocks(self):
        text = "a: >\n  one\n  two\n\n  three\n    more\n  four\nb: >-\n  x\n  y\n- \n"[:-4]
        self.assertEqual(Y.load(text), {"a": "one two\nthree\n  more\nfour\n", "b": "x y"})

    def test_block_in_a_sequence(self):
        self.assertEqual(Y.load("- |\n  a\n  b\n- c\n"), ["a\nb\n", "c"])

    def test_flow(self):
        text = ("a: [x, 'y, z', \"w\", 1, [n, {k: v, e: }], {}, []]\nb: {p: q, r: [1,2], s}\n"
                "c: [\n  one,  # c [\n  two\n  ]\nd: {u: http://x/y}\ne: ['a]',\n  b]\n")
        self.assertEqual(Y.load(text), {"a": ["x", "y, z", "w", 1, ["n", {"k": "v", "e": None}], {}, []],
                                        "b": {"p": "q", "r": [1, 2], "s": None}, "c": ["one", "two"],
                                        "d": {"u": "http://x/y"}, "e": ["a]", "b"]})


class Anchors(unittest.TestCase):
    def test_anchor_alias_merge(self):
        text = ("base: &b\n  x: 1\n  y: 2\nmore: &m {y: 3, z: 4}\nv: &s val\nuse:\n  <<: [*b, *m]\n  x: 9\n"
                "copy: *s\nlist:\n  - &item\n    k: v\n  - *item\nwritten_first:\n  y: 7\n  <<: *b\n")
        got = Y.load(text)
        self.assertEqual(got["use"], {"x": 9, "y": 2, "z": 4})        # written key wins, then the earlier alias
        self.assertEqual(got["copy"], "val")
        self.assertEqual(got["list"], [{"k": "v"}, {"k": "v"}])
        self.assertEqual(got["written_first"], {"y": 7, "x": 1})
        self.assertNotIn("<<", got["use"])

    def test_anchor_on_a_key_is_not_read(self):
        for text in ("- &a k: v\n", "&a k: v\n", "a: 1\n*a : 2\n"):
            with self.subTest(text=text), self.assertRaises(Y.Unreadable) as cm:
                Y.load(text)
            self.assertEqual(cm.exception.reason, "complex_key")


class Reasons(unittest.TestCase):
    CASES = {
        "a:\n\tb: 1\n": (2, "tab"),
        "a:\n    b: 1\n  c: 2\n": (3, "indentation"),
        "a: 1\njust text\n": (2, "not_a_key"),
        "- a\nb: 1\n": (2, "not_an_entry"),
        "a: 1\na: 2\n": (2, "duplicate_key"),
        "? a\n: b\n": (1, "complex_key"),
        "a: !!str x\n": (1, "tag"),
        "a: *nope\n": (1, "alias"),
        "a: 'open\nb: 1\n": (1, "unterminated_quote"),
        "a: 'x' y\n": (1, "text_after_quote"),
        "a: \"\\q\"\n": (1, "escape"),
        "a: [x: y]\n": (1, "flow"),
        "a: [x\n": (1, "flow"),
        "a: @x\n": (1, "indicator"),
        "a: x\n  b: y\n": (2, "mapping_in_scalar"),
        "a: 1\n---\nb: 2\n": (2, "documents"),
        "just text\n": (1, "scalar_document"),
        "a: |x\n  y\n": (1, "block_header"),
    }

    def test_each_reason(self):
        self.assertEqual(sorted({r for _l, r in self.CASES.values()}), sorted(set(Y.REASONS) - {"too_deep"}))
        for text, (line, reason) in self.CASES.items():
            with self.subTest(text=text):
                with self.assertRaises(Y.Unreadable) as cm:
                    Y.load(text)
                self.assertEqual((cm.exception.line, cm.exception.reason), (line, reason))
                self.assertIsInstance(cm.exception, ValueError)

    def test_depth_bound(self):
        def nested(n):      # n block mappings open at the last line
            return "".join("  " * k + "k%d:\n" % k for k in range(n - 1)) + "  " * (n - 1) + "v: 1\n"
        ok, deep = nested(Y.MAX_DEPTH), nested(Y.MAX_DEPTH + 1)
        self.assertIsInstance(Y.load(ok), dict)
        with self.assertRaises(Y.Unreadable) as cm:
            Y.load(deep)
        self.assertEqual(cm.exception.reason, "too_deep")
        self.assertEqual(Y.load("a: " + "[" * Y.MAX_DEPTH + "]" * Y.MAX_DEPTH + "\n")["a"] is not None, True)
        with self.assertRaises(Y.Unreadable) as cm:
            Y.load("a: " + "[" * (Y.MAX_DEPTH + 1) + "]" * (Y.MAX_DEPTH + 1) + "\n")
        self.assertEqual(cm.exception.reason, "too_deep")


if __name__ == "__main__":
    unittest.main()
