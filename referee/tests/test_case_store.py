"""``cases.store``: the dev case set's file (tohum/26m "Dev vaka seti" (1), (4); tohum/01b ``cases/``).

``Rows``: what a line must be (an object the ledger's reader takes, ``case_id``, ``provenance``, ``split``, an id
once, the last newline). ``Prefix``: the append-only rule against the previous file (changed, moved, cut, emptied;
one reason at the first such line; beside ``case_invalid``, by line). ``Add``: added, kept (the same line bytes),
refused (``case_id_taken``, the held row untouched), the list's own twins, what is ``Unusable`` and ``Broken``, the
file's old bytes first. ``Held``: the rows in order or ``Broken``.

Not here: the file on ``brain/state`` (``test_loop_state``, ``test_loop_kos``, ``test_cycle``, ``test_loop_write``),
the proposal that reads the held rows (``test_cases.Proposal``, ``test_loop_cek``).
"""

from __future__ import annotations

import json
import os
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from cases import store as S  # noqa: E402
from ledger import chain  # noqa: E402


def case(cid="c1", **more) -> dict:
    return dict({"case_id": cid, "provenance": "mutation", "split": "dev", "group": "pkg"}, **more)


def line(row) -> bytes:
    return chain.canonical(row) + b"\n"


def file_of(*rows) -> bytes:
    return b"".join(line(r) for r in rows)


A, B_, C = case("a"), case("b"), case("c")


class Rows(unittest.TestCase):
    def test_an_empty_file_and_a_file_of_rows_have_no_reason(self):
        self.assertEqual(S.check(b""), [])
        self.assertEqual(S.check(file_of(A, B_, C)), [])
        for word in S.PROVENANCES:
            self.assertEqual(S.check(file_of(case(provenance=word))), [])
        self.assertEqual(S.PROVENANCES, ("human_fix", "mutation", "system_tp", "system_regression"))

    def test_a_line_that_is_no_row_is_named_by_its_number(self):
        bad = {
            "not json": b"{nope\n",
            "an empty line": b"\n",
            "a list": b"[1]\n",
            "a key twice": b'{"case_id":"x","case_id":"x","provenance":"mutation","split":"dev"}\n',
            "a constant": b'{"case_id":"x","provenance":"mutation","split":"dev","n":NaN}\n',
            "not utf-8": b'{"case_id":"\xff","provenance":"mutation","split":"dev"}\n',
            "no id": line({"provenance": "mutation", "split": "dev"}),
            "an empty id": line(case("")),
            "an id that is no string": line(case(7)),
            "no provenance": line({"case_id": "x", "split": "dev"}),
            "a provenance of no page": line(case("x", provenance="guess")),
            "a provenance that is no string": line(case("x", provenance=["mutation"])),
            "no split": line({"case_id": "x", "provenance": "mutation"}),
            "another split": line(case("x", split="exit")),
            "the heldout split": line(case("x", split="heldout")),
        }
        for name, raw in bad.items():
            with self.subTest(name):
                self.assertEqual(S.check(line(A) + raw + line(B_)), [("case_invalid", 2)])
                with self.assertRaises(S.Broken) as caught:
                    S.held(line(A) + raw + line(B_))
                self.assertEqual(str(caught.exception), "cases: line 2 is no case row")

    def test_an_id_is_held_once(self):
        self.assertEqual(S.check(file_of(A, B_, A)), [("case_invalid", 3)])
        self.assertEqual(S.check(file_of(A, case("a", group="other"), B_, B_)),
                         [("case_invalid", 2), ("case_invalid", 4)])

    def test_the_last_line_ends_in_a_newline(self):
        whole = file_of(A, B_)
        self.assertEqual(S.check(whole[:-1]), [("case_invalid", 2)])
        self.assertEqual(S.check(whole + b"\n"), [("case_invalid", 3)])


class Prefix(unittest.TestCase):
    def test_the_same_file_and_a_longer_one_are_append_only(self):
        old = file_of(A, B_)
        for new in (old, old + line(C)):
            self.assertEqual(S.check(new, old), [])
        for none in (None, b""):
            self.assertEqual(S.check(old, none), [])

    def test_the_first_old_line_that_is_not_the_same_line_is_named_once(self):
        old = file_of(A, B_, C)
        changed = file_of(A, case("b", group="other"), case("c", group="other"))
        self.assertEqual(S.check(changed, old), [("not_append_only", 2)])
        self.assertEqual(S.check(file_of(B_, A, C), old), [("not_append_only", 1)])       # moved
        self.assertEqual(S.check(file_of(A, B_), old), [("not_append_only", 3)])          # cut
        self.assertEqual(S.check(file_of(B_, C), old), [("not_append_only", 1)])          # the first gone
        self.assertEqual(S.check(b"", old), [("not_append_only", 1)])                     # emptied
        self.assertEqual(S.check(file_of(case("z"), A, B_, C), old), [("not_append_only", 1)])  # one put before

    def test_an_old_line_is_the_same_only_with_its_newline(self):
        old = file_of(A)
        self.assertEqual(S.check(old[:-1], old), [("case_invalid", 1), ("not_append_only", 1)])

    def test_both_reasons_are_listed_by_line(self):
        old = file_of(A, B_)
        new = file_of(A, case("b", group="other")) + b"junk\n"
        self.assertEqual(S.check(new, old), [("not_append_only", 2), ("case_invalid", 3)])
        new = b"junk\n" + file_of(B_)
        self.assertEqual(S.check(new, old), [("case_invalid", 1), ("not_append_only", 1)])


class Add(unittest.TestCase):
    def test_a_new_case_is_its_canonical_line_after_the_last(self):
        row = {"split": "dev", "provenance": "mutation", "case_id": "k", "touched_paths": [{"path": "é", "n": 1}]}
        got = S.add(b"", [row])
        self.assertEqual(got, {"content": chain.canonical(row) + b"\n", "added": ["k"], "kept": [], "refused": {}})
        self.assertEqual(got["content"], '{"case_id":"k","provenance":"mutation","split":"dev",'
                                         '"touched_paths":[{"n":1,"path":"é"}]}\n'.encode("utf-8"))
        old = file_of(A, B_)
        got = S.add(old, [C, case("d")])
        self.assertEqual(got, {"content": old + line(C) + line(case("d")), "added": ["c", "d"], "kept": [],
                               "refused": {}})
        self.assertEqual(S.check(got["content"], old), [])
        self.assertEqual(S.held(got["content"]), [A, B_, C, case("d")])

    def test_no_case_leaves_the_file_as_it_is(self):
        for data in (b"", file_of(A)):
            self.assertEqual(S.add(data, []), {"content": data, "added": [], "kept": [], "refused": {}})

    def test_a_held_id_is_kept_on_the_same_line_and_refused_on_another(self):
        old = file_of(A, B_)
        got = S.add(old, [dict(reversed(list(B_.items()))), case("a", group="other"), C])
        self.assertEqual(got, {"content": old + line(C), "added": ["c"], "kept": ["b"],
                               "refused": {"a": S.TAKEN}})
        self.assertEqual(S.TAKEN, "case_id_taken")
        # the same values written otherwise are another line: only this function writes the file
        spaced = json.dumps(A).encode() + b"\n"
        self.assertEqual(S.check(spaced), [])
        self.assertEqual(S.add(spaced, [A]), {"content": spaced, "added": [], "kept": [], "refused": {"a": S.TAKEN}})
        # 1 is not true
        one = file_of(case("n", flag=1))
        self.assertEqual(S.add(one, [case("n", flag=True)])["refused"], {"n": S.TAKEN})

    def test_the_list_s_own_twins(self):
        got = S.add(b"", [A, dict(A), case("a", group="other"), B_])
        self.assertEqual(got, {"content": file_of(A, B_), "added": ["a", "b"], "kept": ["a"],
                               "refused": {"a": S.TAKEN}})

    def test_what_is_no_case_adds_nothing(self):
        for bad in (None, {}, (A,), "a", [None], [A, "x"], [case("")], [case("x", provenance="guess")],
                    [case("x", split="exit")], [{"case_id": "x", "split": "dev"}], [case("x", score=0.5)]):
            with self.subTest(bad=bad):
                with self.assertRaises(S.Unusable):
                    S.add(file_of(A), bad)

    def test_a_file_that_is_no_case_set_is_broken(self):
        for data in (b"junk\n", file_of(A, A), file_of(A)[:-1], file_of(case("x", split="exit"))):
            with self.subTest(data=data):
                with self.assertRaises(S.Broken):
                    S.add(data, [C])
                with self.assertRaises(S.Broken):
                    S.add(data, [])


class Held(unittest.TestCase):
    def test_the_rows_in_the_file_s_order(self):
        self.assertEqual(S.held(b""), [])
        self.assertEqual(S.held(file_of(C, A, B_)), [C, A, B_])


if __name__ == "__main__":
    unittest.main()
