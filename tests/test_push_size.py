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
            code = P.main(list(argv), root="/the/root", git=self.git)
        lines = buf.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        return code, json.loads(lines[0])


class Measure(Base):
    def test_the_two_git_calls_name_base_head_and_leave_out_the_founder_records_at_the_root(self):
        P.sections("/the/root", "BASE", "HEAD~1", self.git)
        spec = ["--", ".", ":(top,exclude)founder-ledger.jsonl", ":(top,exclude)reports"]
        common = ["-C", "/the/root", "diff", "--no-renames", "--no-ext-diff", "--no-textconv", "--no-color"]
        self.assertEqual(self.argv(), [common + ["BASE", "HEAD~1"] + spec,
                                       common + ["--name-only", "-z", "BASE", "HEAD~1"] + spec])

    def test_each_section_is_its_bytes_named_in_the_diff_s_order(self):
        got = P.sections("/the/root", "B", "H", self.git)
        self.assertEqual(got, [(p, len(s)) for p, s in self.parts])
        self.assertEqual([p for p, _ in got], ["a.py", "b/c.py"])

    def test_bytes_is_the_whole_diff(self):
        out = P.measure("/the/root", "B", "H", git=self.git)
        self.assertEqual(out["bytes"], os.path.getsize(os.path.join(self.tmp, "diff")))
        self.assertEqual((out["files"], out["base"], out["head"]), (2, "B", "H"))

    def test_a_hunk_line_holding_the_marker_after_its_sign_starts_no_section(self):
        self.answer([("a.py", b"+diff --git a/x b/x\n-diff --git a/y b/y\n diff --git a/z b/z\n")])
        self.assertEqual(P.sections("/the/root", "B", "H", self.git), [("a.py", len(self.parts[0][1]))])

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
        out = P.measure("/the/root", "B", "H", git=self.git)
        self.assertEqual((out["bytes"], out["files"], out["paths"], out["band"]), (0, 0, [], P.ACCEPTED))

    def test_no_git_and_a_failing_git_are_unreadable(self):
        with self.assertRaisesRegex(P.Unreadable, "^git_unavailable$"):
            P.sections("/the/root", "B", "H", os.path.join(self.tmp, "absent"))
        self.answer([("a.py", b"+x\n")], code=128)
        with self.assertRaisesRegex(P.Unreadable, "^diff_failed:128$"):
            P.sections("/the/root", "B", "H", self.git)

    def test_paths_are_the_top_largest_first_equal_sizes_in_path_order(self):
        self.answer([("m.py", b"+1\n"), ("z.py", b"+22\n"), ("b.py", b"+22\n"), ("k.py", b"+333\n")])
        size = dict((p, len(s)) for p, s in self.parts)
        out = P.measure("/the/root", "B", "H", top=3, git=self.git)
        self.assertEqual(out["paths"], [["k.py", size["k.py"]], ["b.py", size["b.py"]], ["z.py", size["z.py"]]])
        self.assertEqual(out["files"], 4)


class Band(unittest.TestCase):
    ROWS = (("a", "b", 100, "accepted", "f1"), ("c", "d", 70, "accepted", "f2"),
            ("e", "f", 300, "prompt_too_large", "f3"), ("g", "h", 200, "prompt_too_large", "f4"))

    def test_the_two_edges_and_between(self):
        for size, want in ((0, P.ACCEPTED), (100, P.ACCEPTED), (101, P.UNKNOWN), (199, P.UNKNOWN),
                           (200, P.REFUSED), (301, P.REFUSED)):
            self.assertEqual(P.band(size, self.ROWS), (want, 100, 200), size)

    def test_a_side_with_no_row_decides_nothing(self):
        self.assertEqual(P.band(5, ()), (P.UNKNOWN, None, None))
        self.assertEqual(P.band(101, self.ROWS[:2]), (P.UNKNOWN, 100, None))
        self.assertEqual(P.band(10 ** 9, self.ROWS[:2]), (P.UNKNOWN, 100, None))
        self.assertEqual(P.band(199, self.ROWS[2:]), (P.UNKNOWN, None, 200))
        self.assertEqual(P.band(200, self.ROWS[2:]), (P.REFUSED, None, 200))

    def test_the_measured_list_does_not_contradict_itself(self):
        _, accepted, refused = P.band(0)
        self.assertIsNotNone(accepted)
        self.assertIsNotNone(refused)
        self.assertLess(accepted, refused)
        for row in P.MEASURED:
            self.assertEqual(len(row), 5)
            self.assertRegex(row[4], r"^f[0-9]+$")


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

    def test_exit_0_inside_what_was_accepted_and_1_beyond_it(self):
        _, accepted, refused = P.band(0)
        for size, want, code in ((accepted, P.ACCEPTED, 0), (accepted + 1, P.UNKNOWN, 1), (refused, P.REFUSED, 1)):
            self.one(size)
            got, out = self.main("--base", "B")
            self.assertEqual((got, out["ok"], out["band"], out["bytes"]), (code, code == 0, want, size))
            self.assertEqual((out["largest_accepted"], out["smallest_refused"]), (accepted, refused))

    def test_the_base_is_the_result_s_when_none_is_given_and_the_head_is_head(self):
        path = self.put("r.json", json.dumps({"state": {"last_accepted_sha": BaseOf.SHA}}).encode())
        code, out = self.main("--result", path)
        self.assertEqual((code, out["base"], out["head"]), (0, BaseOf.SHA, "HEAD"))
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
