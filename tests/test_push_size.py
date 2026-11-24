"""``tests/push_size.py``'s rules, each bound by a test below (the rules are listed in its docstring, the one
source). No git is needed (the referee's sandbox has none, f396): a fake ``git`` records its arguments and answers
the diff and the name list from files the test writes. Run from the brain's root."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import push_size as P  # noqa: E402

FAKE_GIT = """#!%s
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "argv.jsonl"), "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\\n")
code = int(open(os.path.join(here, "code")).read())
if code:
    sys.exit(code)
name = "names" if "--name-only" in sys.argv else "diff"
sys.stdout.buffer.write(open(os.path.join(here, name), "rb").read())
"""


def section(path: str, body: bytes) -> bytes:
    return b"diff --git a/%b b/%b\n--- a/%b\n+++ b/%b\n@@ -1 +1 @@\n" % ((path.encode(),) * 4) + body


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="test-push-size-")
        self.addCleanup(shutil.rmtree, self.tmp)
        self.git = os.path.join(self.tmp, "git")
        with open(self.git, "w") as f:
            f.write(FAKE_GIT % sys.executable)
        os.chmod(self.git, 0o755)
        self.answer([("a.py", b"-x\n+y\n"), ("b/c.py", b"+z\n")])
        self.absent = os.path.join(self.tmp, "no-result.json")

    def put(self, name: str, data: bytes) -> str:
        path = os.path.join(self.tmp, name)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def answer(self, parts: list[tuple[str, bytes]], names: list[str] | None = None, code: int = 0,
               before: bytes = b"") -> None:
        self.parts = [(p, section(p, body)) for p, body in parts]
        self.put("diff", before + b"".join(s for _, s in self.parts))
        self.put("names", b"".join(n.encode() + b"\0" for n in (names if names is not None else [p for p, _ in parts])))
        self.put("code", b"%d" % code)

    def argv(self) -> list[list[str]]:
        with open(os.path.join(self.tmp, "argv.jsonl")) as f:
            return [json.loads(line) for line in f]

    def main(self, *argv: str) -> tuple[int, dict]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            if "--result" not in argv:  # no result: the kept limit, whatever this machine holds
                argv += ("--result", os.path.join(self.tmp, "no-result.json"))
            code = P.main(list(argv), root="/the/root", git=self.git)
        lines = buf.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        return code, json.loads(lines[0])


class Measure(Base):
    def test_the_two_git_calls_name_base_head_and_leave_out_the_founder_records_at_the_root(self):
        P.sections("/the/root", "BASE", "HEAD~1", self.git)
        spec = ["--", ".", ":(top,exclude)founder-ledger.jsonl", ":(top,exclude)reports"]
        common = ["-C", "/the/root", "diff", "--no-renames", "--no-ext-diff", "--no-textconv", "--no-color",
                  "--binary"]
        self.assertEqual(self.argv(), [common + ["BASE", "HEAD~1"] + spec,
                                       common + ["--name-only", "-z", "BASE", "HEAD~1"] + spec])

    def test_each_section_is_its_bytes_named_in_the_diff_s_order(self):
        got = P.sections("/the/root", "B", "H", self.git)
        self.assertEqual(got, [(p, len(s)) for p, s in self.parts])
        self.assertEqual([p for p, _ in got], ["a.py", "b/c.py"])

    def test_bytes_is_the_whole_diff(self):
        out = P.measure("/the/root", "B", "H", git=self.git, result=self.absent)
        self.assertEqual(out["bytes"], os.path.getsize(os.path.join(self.tmp, "diff")))
        self.assertEqual((out["files"], out["base"], out["head"]), (2, "B", "H"))

    def test_a_hunk_line_holding_the_marker_after_its_sign_starts_no_section(self):
        self.answer([("a.py", b"+diff --git a/x b/x\n-diff --git a/y b/y\n diff --git a/z b/z\n")])
        self.assertEqual(P.sections("/the/root", "B", "H", self.git), [("a.py", len(self.parts[0][1]))])

    def test_only_a_line_feed_ends_a_line_so_the_marker_after_any_other_break_starts_no_section(self):
        for brk in (b"\r", b"\x0b", b"\x0c", b"\x1c", b"\x1d", b"\x1e", b"\x85", b"\xe2\x80\xa8"):
            self.answer([("a.txt", b"+x" + brk + b"diff --git a/b b/b\n"), ("c.txt", b"+y\r\n")])
            self.assertEqual(P.sections("/the/root", "B", "H", self.git), [(p, len(s)) for p, s in self.parts], brk)

    def test_a_section_opened_by_the_line_that_opened_the_one_before_it_is_the_same_path(self):
        gone = b"diff --git a/f b/f\ndeleted file mode 100644\n--- a/f\n+++ /dev/null\n@@ -1 +0,0 @@\n-a\n"
        came = b"diff --git a/f b/f\nnew file mode 120000\n--- /dev/null\n+++ b/f\n@@ -0,0 +1 @@\n+cr\n"
        self.answer([("a.py", b"+x\n")])
        first = self.parts[0][1]
        self.put("diff", first + gone + came + first)
        self.put("names", b"a.py\0f\0a.py\0")
        self.assertEqual(P.sections("/the/root", "B", "H", self.git),
                         [("a.py", len(first)), ("f", len(gone) + len(came)), ("a.py", len(first))])
        self.put("names", b"a.py\0f\0")
        with self.assertRaisesRegex(P.Unreadable, "^sections_mismatch$"):
            P.sections("/the/root", "B", "H", self.git)

    def test_bytes_that_are_not_utf8_and_a_last_line_without_newline_are_counted(self):
        self.answer([("a.bin", b"+\xff\xfe\n"), ("b.txt", b"+end")])
        self.assertEqual(P.sections("/the/root", "B", "H", self.git), [(p, len(s)) for p, s in self.parts])

    def test_counts_that_differ_are_unreadable_not_named_by_guess(self):
        self.answer([("a.py", b"+x\n"), ("b.py", b"+y\n")], names=["a.py"])
        with self.assertRaisesRegex(P.Unreadable, "^sections_mismatch$"):
            P.sections("/the/root", "B", "H", self.git)
        self.answer([("a.py", b"+x\n")], names=["a.py", "b.py"])
        with self.assertRaisesRegex(P.Unreadable, "^sections_mismatch$"):
            P.sections("/the/root", "B", "H", self.git)

    def test_bytes_before_the_first_section_are_unreadable(self):
        self.answer([("a.py", b"+x\n")], before=b"warning: something\n")
        with self.assertRaisesRegex(P.Unreadable, "^sections_mismatch$"):
            P.sections("/the/root", "B", "H", self.git)

    def test_an_empty_diff_is_zero_bytes_of_no_file(self):
        self.answer([])
        out = P.measure("/the/root", "B", "H", git=self.git, result=self.absent)
        self.assertEqual((out["bytes"], out["chars"], out["files"], out["paths"], out["band"]),
                         (0, 0, 0, [], P.FITS))

    def test_chars_are_code_points_and_a_byte_that_is_not_utf8_is_one(self):
        self.answer([("a.txt", "+\u00e9\u20ac\U0001f600\n".encode()), ("b.bin", b"+\xff\xfe\xe2\x82\n")])
        out = P.measure("/the/root", "B", "H", git=self.git, result=self.absent)
        heads = sum(len(section(p, b"")) for p in ("a.txt", "b.bin"))  # ASCII: a byte each
        self.assertEqual(out["bytes"], heads + 11 + 6)
        self.assertEqual(out["chars"], heads + 5 + 6)
        self.assertEqual(out["paths"], [["a.txt", len(self.parts[0][1])], ["b.bin", len(self.parts[1][1])]])

    def test_no_git_and_a_failing_git_are_unreadable(self):
        with self.assertRaisesRegex(P.Unreadable, "^git_unavailable$"):
            P.sections("/the/root", "B", "H", os.path.join(self.tmp, "absent"))
        self.answer([("a.py", b"+x\n")], code=128)
        with self.assertRaisesRegex(P.Unreadable, "^diff_failed:128$"):
            P.sections("/the/root", "B", "H", self.git)

    def test_paths_are_the_top_largest_first_equal_sizes_in_path_order(self):
        self.answer([("m.py", b"+1\n"), ("z.py", b"+22\n"), ("b.py", b"+22\n"), ("k.py", b"+333\n")])
        size = dict((p, len(s)) for p, s in self.parts)
        out = P.measure("/the/root", "B", "H", top=3, git=self.git, result=self.absent)
        self.assertEqual(out["paths"], [["k.py", size["k.py"]], ["b.py", size["b.py"]], ["z.py", size["z.py"]]])
        self.assertEqual(out["files"], 4)


def result_with(most: object, whole: object, diff: object, **more: object) -> bytes:
    return json.dumps({"rival": {"prompt_max_chars": most, "prompt_chars": whole, "prompt_diff_chars": diff},
                       **more}).encode()


class Limit(Base):
    def test_the_limit_and_the_part_that_was_not_diff_are_the_result_s(self):
        self.assertEqual(P.limit_of(self.put("r.json", result_with(1000, 300, 220))), (1000, 80, "result"))
        self.assertEqual(P.limit_of(self.put("r.json", result_with(1000, 300, 0))), (1000, 300, "result"))
        self.assertEqual(P.limit_of(self.put("r.json", result_with(1, 7, 7))), (1, 0, "result"))

    def test_any_other_result_gives_the_kept_numbers_and_says_so(self):
        kept = (P.KEPT[0], P.KEPT[1], "kept")
        self.assertEqual(P.limit_of(self.absent), kept)
        for data in (b"{", b"[" * 100000, b"[]", b"{}", json.dumps({"rival": None}).encode(),
                     json.dumps({"rival": [1000, 300, 220]}).encode(),
                     json.dumps({"rival": {"prompt_max_chars": 1000, "prompt_chars": 300}}).encode(),
                     result_with(None, 300, 220), result_with(1000, None, 220), result_with(1000, 300, None),
                     result_with("1000", 300, 220), result_with(1000.0, 300, 220), result_with(1000, 300.0, 220),
                     result_with(True, 300, 220), result_with(1000, True, False), result_with(1000, 1, True),
                     result_with(0, 300, 220), result_with(-5, 300, 220), result_with(1000, 300, 301),
                     result_with(1000, 300, -1)):
            self.assertEqual(P.limit_of(self.put("r.json", data)), kept, data[:80])

    def test_the_kept_numbers_name_their_source(self):
        most, around, head, row = P.KEPT
        self.assertGreater(most, P.RESERVE * around)
        self.assertGreater(around, 0)
        self.assertRegex(head, r"^[0-9a-f]{7,40}$")
        self.assertRegex(row, r"^f[0-9]+$")


class Band(unittest.TestCase):
    def test_the_two_edges_and_between(self):
        self.assertEqual(P.RESERVE, 2)
        for chars, want in ((0, P.FITS), (800, P.FITS), (801, P.TIGHT), (900, P.TIGHT), (901, P.OVER),
                            (10 ** 9, P.OVER)):
            self.assertEqual(P.band(chars, 3, 1000, 100), want, chars)

    def test_a_diff_of_no_file_fits_whatever_the_numbers(self):
        self.assertEqual(P.band(0, 0, 1000, 600), P.FITS)
        self.assertEqual(P.band(0, 0, 1000, 5000), P.FITS)
        self.assertEqual(P.band(0, 1, 1000, 600), P.TIGHT)  # a file of an empty section is a file
        self.assertEqual(P.band(0, 1, 1000, 5000), P.OVER)


class BaseOf(Base):
    SHA = "0123456789abcdef0123456789abcdef01234567"

    def test_the_last_accepted_sha_of_the_result(self):
        path = self.put("r.json", json.dumps({"state": {"last_accepted_sha": self.SHA,
                                                        "last_evaluated_sha": "f" * 40}}).encode())
        self.assertEqual(P.base_of(path), self.SHA)

    def test_a_result_that_is_not_there_or_not_json_is_unreadable(self):
        for path in (os.path.join(self.tmp, "absent.json"), self.put("r.json", b"{"),
                     self.put("deep.json", b"[" * 100000)):
            with self.assertRaisesRegex(P.Unreadable, "^result_unreadable$"):
                P.base_of(path)

    def test_a_result_without_the_field_as_a_full_sha_is_unreadable(self):
        for doc in ([], {}, {"state": None}, {"state": []}, {"state": {}}, {"state": {"last_accepted_sha": None}},
                    {"state": {"last_accepted_sha": self.SHA[:39]}}, {"state": {"last_accepted_sha": self.SHA + "0"}},
                    {"state": {"last_accepted_sha": self.SHA.upper()}}, {"last_accepted_sha": self.SHA},
                    {"state": {"last_accepted_sha": self.SHA + "\n"}}):
            with self.assertRaisesRegex(P.Unreadable, "^no_last_accepted_sha$", msg=doc):
                P.base_of(self.put("r.json", json.dumps(doc).encode()))


class Main(Base):
    def one(self, size: int) -> None:
        head = len(section("a.py", b""))
        self.answer([("a.py", b"+" * (size - head))])

    def test_exit_0_when_it_fits_and_1_when_tight_or_over_by_the_result_s_numbers(self):
        path = self.put("r.json", result_with(1000, 300, 200))  # around 100: fits to 800, over above 900
        for size, want, code in ((800, P.FITS, 0), (801, P.TIGHT, 1), (900, P.TIGHT, 1), (901, P.OVER, 1)):
            self.one(size)
            got, out = self.main("--base", "B", "--result", path)
            self.assertEqual((got, out["ok"], out["band"], out["bytes"], out["chars"]),
                             (code, code == 0, want, size, size))
            self.assertEqual((out["max_chars"], out["around_chars"], out["allowed_chars"], out["limit_from"]),
                             (1000, 100, 800, "result"))

    def test_the_band_is_by_chars_not_bytes(self):
        path = self.put("r.json", result_with(1000, 300, 200))
        head = len(section("a.py", b""))
        self.answer([("a.py", "\u20ac".encode() * (800 - head))])  # three bytes a code point
        code, out = self.main("--base", "B", "--result", path)
        self.assertEqual((code, out["band"], out["chars"], out["bytes"]),
                         (0, P.FITS, 800, head + 3 * (800 - head)))

    def test_without_a_result_s_numbers_the_kept_ones_judge(self):
        most, around = P.KEPT[:2]
        allowed = most - P.RESERVE * around
        for size, want, code in ((allowed, P.FITS, 0), (allowed + 1, P.TIGHT, 1), (most - around + 1, P.OVER, 1)):
            self.one(size)
            got, out = self.main("--base", "B")
            self.assertEqual((got, out["band"], out["limit_from"], out["allowed_chars"], out["max_chars"]),
                             (code, want, "kept", allowed, most))

    def test_the_base_is_the_result_s_when_none_is_given_and_the_head_is_head(self):
        path = self.put("r.json", result_with(1000, 300, 200, state={"last_accepted_sha": BaseOf.SHA}))
        code, out = self.main("--result", path)
        self.assertEqual((code, out["base"], out["head"], out["limit_from"]), (0, BaseOf.SHA, "HEAD", "result"))
        self.assertEqual(self.argv()[0][-6:-4], [BaseOf.SHA, "HEAD"])

    def test_base_head_and_top_are_the_arguments(self):
        self.answer([("a.py", b"+1\n"), ("b.py", b"+22\n")])
        code, out = self.main("--base", "B", "--head", "wip/x", "--top", "1")
        self.assertEqual((code, out["base"], out["head"], [p for p, _ in out["paths"]]), (0, "B", "wip/x", ["b.py"]))
        self.assertEqual(self.argv()[0][-6:-4], ["B", "wip/x"])

    def test_five_paths_by_default(self):
        self.answer([("%d.py" % i, b"+x\n") for i in range(7)])
        self.assertEqual(len(self.main("--base", "B")[1]["paths"]), 5)

    def test_unreadable_is_exit_2_with_its_reason(self):
        self.assertEqual(self.main("--result", os.path.join(self.tmp, "absent.json")),
                         (2, {"ok": False, "reason": "result_unreadable"}))
        self.answer([("a.py", b"+x\n")], code=3)
        self.assertEqual(self.main("--base", "B"), (2, {"ok": False, "reason": "diff_failed:3"}))
        self.answer([("a.py", b"+x\n")], names=[])
        self.assertEqual(self.main("--base", "B"), (2, {"ok": False, "reason": "sections_mismatch"}))


if __name__ == "__main__":
    unittest.main()
