"""Test 12 of asama-0/09 (P1 MF8): ``findings.write``, the registry's rows (beside tests/test_score.py's
``Fingerprint``, which proves the scorer's folding of a fingerprint it is handed; here: where the fingerprint
comes from and what the registry writes).

What is proven, each by the test named for it:

- the fingerprint (``Fingerprint``): the same finding proposed in two runs is one row; the same line found at
  another place of its file (lines added above it, its indentation changed) is the same finding, with a symbol
  and without; a claim reworded only in whitespace is the same, any other word of it is not; each part of either
  form changes it (property, file, symbol, claim; rule, file, line content) and nothing else of the finding
  does; the two forms never meet; the forms are the stated lists; a finding with no symbol has no fingerprint
  without a rule, a ref in its file, a readable UTF-8 file or the ref's lines; two equal lines are one finding;
- a proposal (``Proposal``): the row written (fields, ``open``, ``f-`` id, ``proposed_by``, ``trust:
  inferred``); every field's refusal; K0-K2 without tool or rule; ``doc_fix`` outside K8; a refused element
  writes nothing and the others are written; what is not a list or has no proposer is ``Unusable``;
- re-observation (``Reobserved``): nothing is written in ``open``, ``reopened``, ``blocked``, ``unresolved``,
  ``withdrawn``; ``fixed`` and ``verified`` write ``reopened`` with the new observation; the third ``reopened``
  is followed by ``blocked`` and the second is not; twice in one proposal is once;
- the gate's decisions (``Decisions``): a merge writes ``fixed``; a reject writes ``unresolved`` and the
  unresolved row with ``ledger.events``'s cause; a finding that is not open or reopened, an unknown or repeated
  fingerprint, a decision of another shape refuse all of them;
- the files (``Files``): both are chains ``ledger.chain`` verifies, extended byte for byte; a broken file or one
  that does not extend the previous version is a hard stop, also when nothing would be written; a secret in a
  proposed claim writes nothing; ``findings_reasons`` and ``unresolved_reasons`` on each shape rule;
- with the scorer (``Scored``): the rows written from two runs of a shifted file are what ``harness.score.sift``
  accepts once each, and the two runs' proposals given the writer's fingerprints fold as re-observations.

Not proven here: anything in a cycle (nothing calls the module); the root over these files.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)

from findings import write as W  # noqa: E402
from harness import score as HS  # noqa: E402
from ledger import append as LA  # noqa: E402
from ledger import chain as LC  # noqa: E402
from ledger import schema as SC  # noqa: E402
from profile import derive as D  # noqa: E402

SNAP = "s" * 8
TREE = {"pkg/a.js": b"use strict;\nvar a = 1;\nlet b = 2;\nvar c = 3;\n",
        "pkg/b.js": b"var a = 1;\n"}
SHIFTED = dict(TREE, **{"pkg/a.js": b"// header\n\nuse strict;\n    var  a = 1;\nlet b = 2;\nvar c = 3;\n"})


# What ``profile.derive.file_path`` refuses and takes: absolute, leaving the tree (at once or after a descent),
# not as normpath writes it, the root, a backslash, a NUL, empty; and paths it leaves alone.
NOT_FILE_PATHS = ["/pkg/a.js", "../a.js", "../../outside/x.js", "pkg/../../a.js", "..", "pkg/../a.js", "pkg/./a.js",
                  "./pkg/a.js", "pkg//a.js", "pkg/a.js/", ".", "./", "pkg\\a.js", "pkg/a\x00.js", ""]
FILE_PATHS = ["pkg/a.js", "a", "pkg/..a.js", "pkg/a..js", "...", ".github/x.yml", "pkg/ a.js"]


def reader(tree: dict):
    return lambda path: tree.get(path)


def lint(line: int = 2, path: str = "pkg/a.js", **over) -> dict:
    """A file-level lint finding (no symbol) on ``line``."""
    out = {"class_level": "K0", "property": "lint", "file": path, "tool": "eslint", "rule_id": "no-var",
           "claim": "a var is declared", "evidence_refs": [{"path": path, "line_start": line, "line_end": line}],
           "required_change": [{"file": path, "op": "lint_fix"}], "severity_hint": "low", "confidence": "0.900000",
           "derivation": "tool", "snapshot_id": SNAP}
    out.update(over)
    return {k: v for k, v in out.items() if v is not None}


def named(line: int = 2, **over) -> dict:
    """A finding on a symbol."""
    return lint(line, **dict({"class_level": "K3", "property": "dead_code", "symbol": "helper",
                              "claim": "helper is never called", "tool": None, "rule_id": None,
                              "derivation": "static_analysis",
                              "required_change": [{"file": "pkg/a.js", "symbol": "helper", "op": "remove"}]}, **over))


def observe(data: bytes, proposal: list, tree: dict = TREE, previous: bytes | None = None, by: str = "hunter-1"):
    return W.observe(data, data if previous is None else previous, proposal, by, reader(tree))


def chained(rows: list[dict], onto: bytes = b"") -> bytes:
    """Rows written onto a file by the ledger's own writer."""
    return LA.plan_cycle(onto, onto, lambda: LC.canonical({"rows": rows})).content


def stored(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.decode("utf-8").splitlines()]


def states(data: bytes) -> list[str]:
    return [row["state"] for row in stored(data)]


def with_state(data: bytes, state: str) -> bytes:
    """The file with its last row written again in ``state`` (what a later writer would add)."""
    row = {k: v for k, v in stored(data)[-1].items() if k not in ("prev_hash", "row_hash")}
    return chained([dict(row, state=state)], data)


class Fingerprint(unittest.TestCase):
    """Test 12: "aynı bulgu iki koşuda tek sayılır; satır kayması kimliği değiştirmez"."""

    def test_the_same_finding_in_two_runs_is_one_row(self):
        first = observe(b"", [lint(2), named(1)])
        self.assertEqual(len(first.rows), 2)
        second = observe(first.content, [lint(2), named(1)])
        self.assertEqual((second.rows, second.content, second.refused), ([], first.content, []))
        self.assertEqual(second.reobserved, [row["fingerprint"] for row in first.rows])
        # the control: another finding in the second run is a row
        third = observe(first.content, [lint(2), lint(4)])
        self.assertEqual([row["evidence_refs"][0]["line_start"] for row in third.rows], [4])

    def test_a_shifted_line_is_the_same_finding(self):
        first = observe(b"", [lint(2), named(1)])
        # the file grew two lines above and the line was re-indented: the tool now reports line 4
        moved = [lint(4), named(3)]
        second = observe(first.content, moved, SHIFTED)
        self.assertEqual((second.rows, len(second.reobserved)), ([], 2))
        self.assertEqual(W.fingerprint(lint(2), reader(TREE)), W.fingerprint(lint(4), reader(SHIFTED)))
        # the control: line 2 of the shifted file is another text, so another finding
        self.assertEqual(len(observe(first.content, [lint(2)], SHIFTED).rows), 1)
        # and a ref of several lines moves the same way
        wide = [dict(lint(), evidence_refs=[{"path": "pkg/a.js", "line_start": 2, "line_end": 3}])]
        there = [dict(lint(), evidence_refs=[{"path": "pkg/a.js", "line_start": 4, "line_end": 5}])]
        self.assertEqual(W.fingerprint(wide[0], reader(TREE)), W.fingerprint(there[0], reader(SHIFTED)))
        self.assertNotEqual(W.fingerprint(wide[0], reader(TREE)), W.fingerprint(lint(2), reader(TREE)))

    def test_normalize_folds_whitespace_and_nothing_else(self):
        self.assertEqual(W.normalize("  a \t b\n\nc d  "), "a b c d")
        self.assertEqual(W.normalize("A b."), "A b.")
        read = reader(TREE)
        base = W.fingerprint(named(), read)
        self.assertEqual(W.fingerprint(named(claim=" helper  is never\ncalled "), read), base)
        for claim in ("Helper is never called", "helper is never called.", "helperis never called"):
            self.assertNotEqual(W.fingerprint(named(claim=claim), read), base, claim)

    def test_each_part_of_the_form_changes_it_and_nothing_else_does(self):
        read = reader(dict(TREE, **{"pkg/c.js": TREE["pkg/a.js"]}))
        base = W.fingerprint(named(), read)
        for over in ({"property": "unused"}, {"file": "pkg/c.js"}, {"symbol": "other"}, {"claim": "helper is dead"}):
            self.assertNotEqual(W.fingerprint(named(**over), read), base, over)
        for over in ({"class_level": "K4"}, {"tool": "knip"}, {"rule_id": "unused"}, {"confidence": "0.1"},
                     {"severity_hint": "high"}, {"snapshot_id": "t"}, {"derivation": "tool"},
                     {"evidence_refs": [{"path": "pkg/b.js", "line_start": 1, "line_end": 1}]},
                     {"evidence_refs": []}, {"required_change": []}):
            self.assertEqual(W.fingerprint(named(**over), read), base, over)
        base = W.fingerprint(lint(), read)
        for changed in (lint(rule_id="no-eval"), lint(path="pkg/c.js"), lint(3)):
            self.assertNotEqual(W.fingerprint(changed, read), base)
        for over in ({"class_level": "K1"}, {"tool": "biome"}, {"property": "style"}, {"claim": "another claim"},
                     {"confidence": "0.1"}, {"snapshot_id": "t"}, {"required_change": []}):
            self.assertEqual(W.fingerprint(lint(**over), read), base, over)

    def test_the_forms_are_the_stated_lists(self):
        def digest(parts):
            return hashlib.sha256(LC.canonical(parts)).hexdigest()
        read = reader(TREE)
        self.assertEqual(W.fingerprint(named(), read),
                         digest(["symbol", "dead_code", "pkg/a.js", "helper", "helper is never called"]))
        self.assertEqual(W.fingerprint(lint(), read), digest(["line", "no-var", "pkg/a.js", "var a = 1;"]))
        # a finding with a symbol does not read its line, even when it has a rule
        self.assertEqual(W.fingerprint(named(rule_id="no-var", tool="eslint"), lambda path: self.fail(path)),
                         W.fingerprint(named(), read))
        # the two forms never meet: a symbol finding whose parts spell a line finding's
        twin = named(property="no-var", symbol="var a = 1;", claim="x")
        self.assertNotEqual(W.fingerprint(twin, read), W.fingerprint(lint(), read))

    def test_no_symbol_and_no_line_is_no_fingerprint(self):
        tree = dict(TREE, **{"pkg/bin.js": b"\xff\xfe\n", "pkg/open.js": b"var a = 1;"})
        read = reader(tree)
        elsewhere = [{"path": "pkg/b.js", "line_start": 1, "line_end": 1}]
        for name, finding in (("no rule", lint(rule_id=None, class_level="K3")),
                              ("no ref in the file", lint(evidence_refs=elsewhere)),
                              ("no file", lint(path="pkg/gone.js")), ("not utf-8", lint(1, path="pkg/bin.js")),
                              ("past the end", lint(5)), ("past the end of one line", lint(2, path="pkg/b.js"))):
            with self.subTest(name=name):
                self.assertIsNone(W.fingerprint(finding, read))
                self.assertEqual(observe(b"", [finding], tree).refused,
                                 [{"index": 0, "reasons": ["no_line"]}])
        # the last line is a line with or without its newline; the ref in the file is used, wherever it stands
        self.assertEqual(W.fingerprint(lint(4), read), W.fingerprint(lint(4), reader({"pkg/a.js": TREE["pkg/a.js"][:-1]})))
        self.assertEqual(W.fingerprint(lint(1, path="pkg/open.js"), read),
                         W.fingerprint(lint(1, path="pkg/open.js"), reader({"pkg/open.js": b"var a = 1;\n"})))
        late = lint(evidence_refs=elsewhere + lint(2)["evidence_refs"] + lint(3)["evidence_refs"])
        self.assertEqual(W.fingerprint(late, read), W.fingerprint(lint(2), read))

    def test_two_equal_lines_of_a_file_are_one_finding(self):
        tree = {"pkg/a.js": b"var a = 1;\nlet b;\nvar a = 1;\n"}
        out = observe(b"", [lint(1), lint(3)], tree)
        self.assertEqual((len(out.rows), len(out.reobserved)), (1, 1))
        # the same line in another file is another finding
        self.assertEqual(len(observe(b"", [lint(2), lint(1, path="pkg/b.js")]).rows), 2)


class Proposal(unittest.TestCase):
    def test_the_row_written(self):
        out = observe(b"", [lint(), named()], by="hunter-7")
        rows = stored(out.content)
        self.assertEqual(len(rows), 2)
        for row, proposed in zip(rows, (lint(), named())):
            print_ = W.fingerprint(proposed, reader(TREE))
            self.assertEqual({k: v for k, v in row.items() if k not in ("prev_hash", "row_hash")},
                             dict(proposed, finding_id="f-" + print_, fingerprint=print_, state="open",
                                  proposed_by="hunter-7", trust="inferred"))
        self.assertEqual(W.findings_reasons(out.content), [])
        self.assertEqual(out.rows, [{k: v for k, v in row.items() if k not in ("prev_hash", "row_hash")}
                                    for row in rows])
        # an observation (no required change) and every class, op and bound of confidence are written
        fine = [lint(3, required_change=[]), named(confidence="1.0"), named(confidence="0.0", symbol="b")]
        fine += [named(class_level=k, symbol=k) for k in W.CLASS_LEVELS[3:]]
        fine += [named(symbol=op, required_change=[{"file": "x", "op": op}]) for op in W.OPS if op != "doc_fix"]
        fine += [named(class_level="K8", symbol="doc", required_change=[{"file": "README.md", "op": "doc_fix"}])]
        out = observe(b"", fine)
        self.assertEqual((out.refused, len(out.rows)), ([], len(fine)))
        self.assertEqual(W.CLASS_LEVELS, ("K0", "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8"))
        self.assertEqual(W.OPS, ("lint_fix", "add_guard", "remove", "rename", "change_type", "move", "add_test",
                                 "doc_fix", "other"))

    def test_each_refusal(self):
        bad = {
            "not an object": ["finding"],
            "a missing field": {k: v for k, v in lint().items() if k != "claim"},
            "a field of no finding": lint(note="x"),
            "its own fingerprint": lint(fingerprint="0" * 64),
            "its own finding_id": lint(finding_id="f-1"),
            "its own state": lint(state="verified"),
            "its own trust": lint(trust="verified"),
            "its own proposed_by": lint(proposed_by="referee"),
            "a class off the ladder": lint(class_level="K9"),
            "an empty property": lint(property=""),
            "an absolute file": lint(path="/pkg/a.js"),
            "a file not normalised": lint(file="pkg/./a.js"),
            "a file leaving the tree": lint(file="../a.js"),
            "an empty claim": lint(claim=""),
            "refs that are no list": lint(evidence_refs={"path": "pkg/a.js", "line_start": 2, "line_end": 2}),
            "a ref ending before it starts": lint(evidence_refs=[{"path": "pkg/a.js", "line_start": 3, "line_end": 2}]),
            "a ref from line 0": lint(evidence_refs=[{"path": "pkg/a.js", "line_start": 0, "line_end": 2}]),
            "a ref with another key": lint(evidence_refs=[{"path": "pkg/a.js", "line_start": 2, "line_end": 2, "x": 1}]),
            "a change with no op": lint(required_change=[{"file": "pkg/a.js"}]),
            "an op off the list": lint(required_change=[{"file": "pkg/a.js", "op": "rewrite"}]),
            "a change with another key": lint(required_change=[{"file": "pkg/a.js", "op": "remove", "line": 2}]),
            "an empty symbol": named(symbol=""),
            "an empty severity hint": lint(severity_hint=""),
            "a float confidence": lint(confidence=0.9),
            "a confidence over one": lint(confidence="1.000001"),
            "a confidence of seven decimals": lint(confidence="0.1234567"),
            "a one of seven decimals": lint(confidence="1.0000000"),
            "a float line": lint(evidence_refs=[{"path": "pkg/a.js", "line_start": 2.0, "line_end": 2.0}]),
            "a change in no file": lint(required_change=[{"file": "", "op": "lint_fix"}]),
            "a change of an empty symbol": lint(required_change=[{"file": "pkg/a.js", "symbol": "", "op": "remove"}]),
            "an empty tool": lint(tool=""),
            "an empty rule": lint(rule_id=""),
            "a confidence with no decimal": lint(confidence="1"),
            "a negative confidence": lint(confidence="-0.5"),
            "a confidence with a tail": lint(confidence="0.5\n"),
            "a derivation off the set": lint(derivation="guess"),
            "an empty snapshot": lint(snapshot_id=""),
            "K0 with no tool": lint(tool=None),
            "K1 with no rule": lint(class_level="K1", rule_id=None, symbol="f"),
            "K2 with no tool": named(class_level="K2", rule_id="r"),
            "doc_fix in K3": named(required_change=[{"file": "README.md", "op": "doc_fix"}]),
            "doc_fix in K0": lint(required_change=[{"file": "pkg/a.js", "op": "lint_fix"}, {"file": "x", "op": "doc_fix"}]),
        }
        for name, finding in bad.items():
            with self.subTest(name=name):
                out = observe(b"", [lint(4), finding, named()])
                self.assertEqual(out.refused, [{"index": 1, "reasons": ["finding_invalid"]}])
                self.assertEqual([row["state"] for row in out.rows], ["open", "open"])
                self.assertEqual(len(stored(out.content)), 2)
                self.assertTrue(W.proposal_reasons(finding))
        self.assertEqual(W.proposal_reasons(lint()), [])
        self.assertEqual(W.proposal_reasons(named(class_level="K3")), [])   # K3 needs neither tool nor rule

    def test_every_path_a_finding_names_is_a_file_of_the_tree(self):
        places = {"file": lambda p: lint(file=p),
                  "evidence_refs[].path": lambda p: lint(evidence_refs=[
                      {"path": "pkg/a.js", "line_start": 2, "line_end": 2}, {"path": p, "line_start": 1, "line_end": 1}]),
                  "required_change[].file": lambda p: lint(required_change=[
                      {"file": "pkg/a.js", "op": "lint_fix"}, {"file": p, "op": "add_test"}])}
        for place, build in places.items():
            for path in NOT_FILE_PATHS:
                with self.subTest(place=place, path=path):
                    out = observe(b"", [lint(4), build(path), named()])
                    self.assertEqual(out.refused, [{"index": 1, "reasons": ["finding_invalid"]}])
                    self.assertEqual(len(stored(out.content)), 2)
                    self.assertTrue(all(place.split("[")[0] in r for r in W.proposal_reasons(build(path))))
            for path in FILE_PATHS:
                with self.subTest(place=place, path=path):
                    if place == "file":         # form 2 reads the finding's own file: give it a line there
                        finding, tree = lint(path=path), dict(TREE, **{path: TREE["pkg/a.js"]})
                    else:
                        finding, tree = build(path), TREE
                    out = observe(b"", [finding], tree)
                    self.assertEqual((out.refused, len(out.rows)), ([], 1))

    def test_the_path_rule_is_one_rule(self):
        self.assertEqual([p for p in NOT_FILE_PATHS + FILE_PATHS if D.file_path(p)], FILE_PATHS)
        self.assertFalse(any(D.file_path(v) for v in (None, 1, b"pkg/a.js", ["pkg/a.js"])))

    def test_what_is_no_proposal_is_unusable(self):
        for proposal, by in (({"findings": [lint()]}, "hunter-1"), (None, "hunter-1"), ([lint()], ""), ([lint()], None)):
            with self.assertRaises(W.Unusable):
                W.observe(b"", b"", proposal, by, reader(TREE))
        self.assertEqual(observe(b"", []).content, b"")


class Reobserved(unittest.TestCase):
    def setUp(self) -> None:
        self.open = observe(b"", [lint()]).content
        self.print = stored(self.open)[0]["fingerprint"]

    def test_nothing_is_written_while_the_finding_is_not_fixed(self):
        for state in ("open", "reopened", "blocked", "unresolved", "withdrawn"):
            with self.subTest(state=state):
                data = self.open if state == "open" else with_state(self.open, state)
                out = observe(data, [lint()])
                self.assertEqual((out.content, out.rows, out.reobserved), (data, [], [self.print]))

    def test_a_fixed_or_verified_finding_seen_again_is_reopened(self):
        for state in ("fixed", "verified"):
            with self.subTest(state=state):
                data = with_state(self.open, state)
                again = lint(4, claim="seen again", snapshot_id="later")
                out = observe(data, [again], SHIFTED, by="hunter-2")
                self.assertEqual(states(out.content), ["open", state, "reopened"])
                self.assertEqual(out.rows, [dict(again, finding_id="f-" + self.print, fingerprint=self.print,
                                                 state="reopened", proposed_by="hunter-2", trust="inferred")])
                self.assertEqual(out.reobserved, [])
                self.assertTrue(out.content.startswith(data))
                self.assertEqual(W.findings_reasons(out.content), [])
        self.assertEqual(W.REOPENS, ("fixed", "verified"))

    def test_the_third_reopening_blocks(self):
        data = self.open
        for turn in (1, 2):
            data = observe(with_state(data, "fixed"), [lint()]).content
            self.assertEqual(states(data)[-1], "reopened", turn)
        self.assertEqual(states(data).count("blocked"), 0)
        out = observe(with_state(data, "verified"), [lint()])
        self.assertEqual(states(out.content)[-3:], ["verified", "reopened", "blocked"])
        self.assertEqual(states(out.content).count("reopened"), 3)
        self.assertEqual([row["state"] for row in out.rows], ["reopened", "blocked"])
        self.assertEqual(dict(out.rows[0], state="blocked"), out.rows[1])
        # blocked, it is not opened again
        self.assertEqual(observe(out.content, [lint()]).rows, [])
        # another finding's reopenings are not counted with it
        other = observe(out.content, [lint(4)]).content
        other = observe(with_state(other, "fixed"), [lint(4)])
        self.assertEqual([row["state"] for row in other.rows], ["reopened"])
        self.assertEqual(W.REOPEN_LIMIT, 3)

    def test_twice_in_one_proposal_is_once(self):
        out = observe(b"", [lint(), lint(claim="again")])
        self.assertEqual((len(out.rows), out.reobserved), (1, [self.print]))
        out = observe(with_state(self.open, "fixed"), [lint(), lint()])
        self.assertEqual(([row["state"] for row in out.rows], out.reobserved), (["reopened"], [self.print]))


class Decisions(unittest.TestCase):
    def setUp(self) -> None:
        self.data = observe(b"", [lint(), named(), lint(4)]).content
        self.prints = [row["fingerprint"] for row in stored(self.data)]

    def decide(self, decisions, data=None, unresolved=b""):
        data = self.data if data is None else data
        return W.decide(data, data, unresolved, unresolved, decisions)

    def test_a_merge_fixes_and_a_reject_is_unresolved(self):
        a, b, c = self.prints
        out = self.decide([{"fingerprint": a, "reasons": []}, {"fingerprint": b, "reasons": ["tests_red", "kos:limit"]}])
        rows = stored(out.findings)
        self.assertTrue(out.findings.startswith(self.data))
        self.assertEqual([(row["fingerprint"], row["state"]) for row in rows[3:]], [(a, "fixed"), (b, "unresolved")])
        for new, old in zip(rows[3:], rows[:2]):
            self.assertEqual({k: v for k, v in new.items() if k not in ("state", "prev_hash", "row_hash")},
                             {k: v for k, v in old.items() if k not in ("state", "prev_hash", "row_hash")})
        lost = stored(out.unresolved)
        self.assertEqual([{k: v for k, v in row.items() if k not in ("prev_hash", "row_hash")} for row in lost],
                         [{"finding_id": "f-" + b, "fingerprint": b, "cause": "test_regression",
                           "reasons": ["tests_red", "kos:limit"], "snapshot_id": SNAP}])
        self.assertEqual(out.unresolved_rows, [{k: v for k, v in lost[0].items() if k not in ("prev_hash", "row_hash")}])
        self.assertEqual((W.findings_reasons(out.findings), W.unresolved_reasons(out.unresolved)), ([], []))
        # the cause is the ledger's reading of the reasons, and the unresolved file grows
        more = W.decide(out.findings, out.findings, out.unresolved, out.unresolved,
                        [{"fingerprint": c, "reasons": ["ratchet_increase"]}])
        self.assertEqual([row["cause"] for row in stored(more.unresolved)], ["test_regression", "lint_regression"])
        self.assertTrue(more.unresolved.startswith(out.unresolved))
        for reasons, cause in ((["scope_violation"], "scope_violation"), (["kos:patch"], "unknown")):
            one = self.decide([{"fingerprint": c, "reasons": reasons}])
            self.assertEqual(stored(one.unresolved)[0]["cause"], cause)
        # only merges: the unresolved file is as it was
        only = self.decide([{"fingerprint": a, "reasons": []}], unresolved=out.unresolved)
        self.assertEqual((only.unresolved, only.unresolved_rows), (out.unresolved, []))
        # a reopened finding is decided too, and a fixed one seen again reopens (the whole life)
        again = observe(out.findings, [lint()])
        self.assertEqual([row["state"] for row in again.rows], ["reopened"])
        self.assertEqual(self.decide([{"fingerprint": a, "reasons": []}], again.content).rows[0]["state"], "fixed")

    def test_refused_decisions_write_nothing(self):
        a, b, _ = self.prints
        good = {"fingerprint": a, "reasons": []}
        for state in ("fixed", "verified", "withdrawn", "blocked", "unresolved"):
            with self.subTest(state=state):
                data = with_state(observe(b"", [lint()]).content, state)
                with self.assertRaises(W.Unusable):
                    self.decide([good], data)
        bad = {"an unknown fingerprint": {"fingerprint": "0" * 64, "reasons": []},
               "the same fingerprint again": good,
               "no reasons": {"fingerprint": b},
               "reasons that are no list": {"fingerprint": b, "reasons": "tests_red"},
               "an empty reason": {"fingerprint": b, "reasons": [""]},
               "another key": {"fingerprint": b, "reasons": [], "decision": "merge"},
               "a fingerprint that is none": {"fingerprint": "f-" + b, "reasons": []},
               "not an object": [b]}
        for name, decision in bad.items():
            with self.subTest(name=name):
                with self.assertRaises(W.Unusable):
                    self.decide([good, decision])
        with self.assertRaises(W.Unusable):
            self.decide({"decisions": [good]})
        self.assertEqual(len(self.decide([good]).rows), 1)
        self.assertEqual(W.DECIDABLE, ("open", "reopened"))


class Files(unittest.TestCase):
    def setUp(self) -> None:
        self.one = observe(b"", [lint()]).content
        self.two = observe(self.one, [named()]).content
        self.print = stored(self.one)[0]["fingerprint"]

    def test_both_files_are_chains_extended_byte_for_byte(self):
        self.assertTrue(self.two.startswith(self.one) and len(stored(self.two)) == 2)
        self.assertTrue(LC.verify_bytes(self.two, self.one)["valid"])
        rows = stored(self.two)
        self.assertEqual((rows[0]["prev_hash"], rows[1]["prev_hash"]), (LC.ZERO_HASH, rows[0]["row_hash"]))
        self.assertEqual([LC.row_hash(row) for row in rows], [row["row_hash"] for row in rows])
        self.assertEqual(self.two.splitlines()[1], LC.canonical(rows[1]))
        out = W.decide(self.two, self.two, b"", b"", [{"fingerprint": self.print, "reasons": ["tests_red"]}])
        self.assertTrue(LC.verify_bytes(out.findings, self.two)["valid"])
        self.assertTrue(LC.verify_bytes(out.unresolved, b"")["valid"])
        self.assertEqual(stored(out.unresolved)[0]["prev_hash"], LC.ZERO_HASH)

    def test_a_file_that_is_no_extension_is_a_hard_stop(self):
        edited = self.two.replace(b"a var is declared", b"a var was declared")
        self.assertNotEqual(edited, self.two)
        cut = self.two[:-20]
        decision = [{"fingerprint": self.print, "reasons": ["tests_red"]}]
        for name, data, previous in (("an edited row", edited, edited), ("a cut line", cut, cut),
                                     ("a row gone", self.one, self.two),
                                     ("another history", observe(b"", [named()]).content, self.one)):
            with self.subTest(name=name):
                for proposal in ([lint(4)], [lint()], []):       # a new row, a re-observation, nothing
                    with self.assertRaises(LA.HardStop):
                        W.observe(data, previous, proposal, "hunter-1", reader(TREE))
                with self.assertRaises(LA.HardStop):
                    W.decide(data, previous, b"", b"", decision)
                with self.assertRaises(LA.HardStop):             # the unresolved file is held to the same
                    W.decide(self.two, self.two, data, previous, decision)
                with self.assertRaises(LA.HardStop):             # even when only merges are decided
                    W.decide(self.two, self.two, data, previous, [{"fingerprint": self.print, "reasons": []}])
        # the stop comes before the proposal is judged
        with self.assertRaises(LA.HardStop):
            W.observe(edited, edited, None, "", reader(TREE))

    def test_a_secret_in_a_claim_writes_nothing(self):
        leak = named(claim="the key is AKIA" + "IOSFODNN7EXAMPLE and password = 'correct-horse-battery'")
        with self.assertRaises(LA.SecretRow):
            observe(self.one, [lint(4), leak])
        self.assertEqual(len(observe(self.one, [lint(4), named()]).rows), 2)   # the control: the same without it

    def test_findings_reasons(self):
        self.assertEqual(W.findings_reasons(self.two), [])
        self.assertEqual(W.findings_reasons(b""), [])
        row = {k: v for k, v in stored(self.one)[0].items() if k not in ("prev_hash", "row_hash")}
        self.assertEqual(W.findings_reasons(chained([row])), [])
        self.assertEqual(W.findings_reasons(chained([dict(row, state=s) for s in W.STATES])), [])
        self.assertEqual(W.STATES, ("open", "fixed", "verified", "reopened", "withdrawn", "blocked", "unresolved"))
        bare = {k: v for k, v in row.items() if k != "proposed_by"}       # the referee's own row has no proposer
        self.assertEqual(W.findings_reasons(chained([dict(bare, trust=t) for t in SC.TRUSTS])), [])
        bad = {"a state off the list": dict(row, state="closed"),
               "an id that is not the fingerprint's": dict(row, finding_id="f-" + "0" * 64),
               "a fingerprint that is none": dict(row, fingerprint="x", finding_id="f-x"),
               "a trust off the set": dict(bare, trust="sure"),
               "no state": {k: v for k, v in row.items() if k != "state"},
               "a field of no finding": dict(row, note="x"),
               "an empty proposer": dict(row, proposed_by=""),
               "a float": dict(row, confidence=0.5),
               "K0 with no rule": {k: v for k, v in row.items() if k != "rule_id"},
               "doc_fix in K0": dict(row, required_change=[{"file": "a", "op": "doc_fix"}]),
               "a change leaving the tree": dict(row, required_change=[{"file": "../../outside/x.js", "op": "lint_fix"}]),
               "a ref leaving the tree": dict(row, evidence_refs=[{"path": "../a.js", "line_start": 1, "line_end": 1}]),
               "the root as its file": dict(row, file="."),
               "an unresolved row": {"finding_id": row["finding_id"], "fingerprint": row["fingerprint"],
                                     "cause": "unknown", "reasons": ["x"], "snapshot_id": SNAP}}
        for name, changed in bad.items():
            with self.subTest(name=name):
                try:
                    data = chained([row, changed])
                except LC.ChainError:         # the chain holds no float: written by hand, the chain breaks
                    data = self.one + json.dumps(dict(changed, prev_hash="0" * 64, row_hash="0" * 64)).encode() + b"\n"
                found = W.findings_reasons(data)
                self.assertTrue(found and all(r.startswith(("row 2", "chain")) for r in found), found)
        self.assertTrue(W.findings_reasons(self.two.replace(b"a var is declared", b"a var was declared"))[0]
                        .startswith("chain: "))

    def test_unresolved_reasons(self):
        out = W.decide(self.two, self.two, b"", b"", [{"fingerprint": self.print, "reasons": ["tests_red"]}])
        row = out.unresolved_rows[0]
        self.assertEqual(W.unresolved_reasons(out.unresolved), [])
        self.assertEqual(W.unresolved_reasons(chained([dict(row, cause=c) for c in SC.CAUSES])), [])
        bad = {"a cause off the set": dict(row, cause="bad_luck"), "no reasons": dict(row, reasons=[]),
               "an empty reason": dict(row, reasons=[""]), "no snapshot": {k: v for k, v in row.items() if k != "snapshot_id"},
               "another field": dict(row, state="unresolved"),
               "a fingerprint that is none": dict(row, fingerprint="x", finding_id="f-x"), "an empty snapshot": dict(row, snapshot_id=""), "an id that is not the fingerprint's": dict(row, finding_id="f-1"),
               "a finding row": stored(self.one)[0] and {k: v for k, v in stored(self.one)[0].items()
                                                         if k not in ("prev_hash", "row_hash")}}
        for name, changed in bad.items():
            with self.subTest(name=name):
                found = W.unresolved_reasons(chained([row, changed]))
                self.assertTrue(found and all(r.startswith("row 2") for r in found), found)
        self.assertTrue(W.unresolved_reasons(out.unresolved[:-9])[0].startswith("chain: "))


class Scored(unittest.TestCase):
    """The writer's rows under ``harness.score.sift``: one identity, counted once."""

    def test_two_runs_of_a_shifted_file_are_counted_once(self):
        first = observe(b"", [lint(2), lint(4), named(1)])
        second = observe(first.content, [lint(4), lint(6), named(3), lint(1)], SHIFTED)
        self.assertEqual(len(second.rows), 1)                      # only "// header" is new
        rows = stored(second.content)
        accepted, refused, reobserved = HS.sift(rows)
        self.assertEqual((len(accepted), refused, reobserved), (4, [], 0))
        # the two runs' proposals, each given the writer's fingerprint: the scorer folds the second run
        runs = [dict(f, fingerprint=W.fingerprint(f, reader(tree)))
                for tree, run in ((TREE, [lint(2), lint(4), named(1)]), (SHIFTED, [lint(4), lint(6), named(3)]))
                for f in run]
        accepted, refused, reobserved = HS.sift(copy.deepcopy(runs))
        self.assertEqual((len(accepted), refused, reobserved), (3, [], 3))
        self.assertEqual([f["fingerprint"] for f in accepted], [row["fingerprint"] for row in rows[:3]])
        # a state row of the same finding is the same identity to the scorer, never a conflict
        fixed = W.decide(second.content, second.content, b"", b"", [{"fingerprint": rows[0]["fingerprint"], "reasons": []}])
        accepted, refused, reobserved = HS.sift(stored(fixed.findings))
        self.assertEqual((len(accepted), refused, reobserved), (4, [], 1))


if __name__ == "__main__":
    unittest.main()
