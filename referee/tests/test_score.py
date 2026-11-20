"""Tests 1, 6, 7, 12 and 28 (asama-0/09), P1 MF4: ``harness.score`` and ``harness.stats``, and the scorer's line
through the loop (``yaz``).

- test 1 (``Empty``): no finding against cases is recall 0 and a report, no error; no finding and no case too;
- test 6 (``Refs``): a reference outside the manifest, or to a file whose bytes are not the manifest's, is refused
  and reported, and so is each other reason of ``sift``; a refused finding hits nothing and is still counted in
  a clean run;
- test 7 (``Determinism``): the same input twice gives the same bytes (two processes with different hash seeds);
  the number of hits does not depend on the order of the findings or of the cases (``Match``: the largest
  matching, where taking cases greedily would give one hit fewer);
- test 12 (``Fingerprint``): the same finding in two runs is counted once; the same finding on a shifted line is
  the same finding; one fingerprint over two files or rules is refused;
- test 28 (``Statistics``): tohum/29a's tables through the command line, and ``x_eff`` and ``recall_lb`` through
  the report;
- ``Match`` and ``Vectors``: one finding takes one case, one case counts once; the shapes of tohum/29a's
  ``match`` vectors through the command line; the command's refusals;
- ``Report``: the fields, the census, the verdicts, the cases refused;
- ``Live``: from ``çek`` through ``koş`` to ``yaz``'s line (``harness``).
"""

from __future__ import annotations

import copy
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
from fractions import Fraction

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from harness import score as HS  # noqa: E402
from harness import stats as ST  # noqa: E402
from loop import job as J  # noqa: E402
from loop import pulled as P  # noqa: E402
from profile import derive as D  # noqa: E402
from profile_tree import write_tree  # noqa: E402
import test_cases as TCA  # noqa: E402
import test_loop_kos as LK  # noqa: E402
import test_loop_yaz as LY  # noqa: E402

A_JS = "var a = 1;\nvar b = 2;\nvar c = 3;\nvar d = 4;\nvar e = 5;\n"
TREE = {"pkg/a.js": A_JS, "pkg/b.js": "var z = 0;\n", "lib/c.js": "var y = 0;\nvar x = 1;"}
TENTH = Fraction(1, 10)


def case(case_id: str, line: int, path: str = "pkg/a.js", rule: str = "no-var", group: str = "pkg",
         end: int | None = None, **over) -> dict:
    return dict({"case_id": case_id, "class_level": "K0", "property": "lint", "provenance": "mutation",
                 "touched_paths": [{"path": path, "hunks": [{"start": line, "end": end or line}]}],
                 "tool": "eslint", "rule_id": rule, "split": "dev", "group": group}, **over)


def finding(fingerprint: str, *lines: int, path: str = "pkg/a.js", rule: str = "no-var", **over) -> dict:
    return dict({"finding_id": "id-" + fingerprint, "fingerprint": fingerprint, "class_level": "K0",
                 "property": "lint", "file": path, "tool": "eslint", "rule_id": rule, "claim": "a var",
                 "evidence_refs": [{"path": path, "line_start": n, "line_end": n} for n in lines]}, **over)


class Base(unittest.TestCase):
    """A tree, its clean snapshot document, and ``report`` on them (each finding given the document's id)."""

    def setUp(self) -> None:
        self.root = tempfile.mkdtemp(prefix="score-")
        self.addCleanup(shutil.rmtree, self.root)
        self.tree = os.path.join(self.root, "tree")
        write_tree(self.tree, TREE)
        self.snapshot = LK.snapshot_of(self.tree)

    def read(self, path: str) -> bytes | None:
        return D._read_regular(self.tree, path)

    def stamped(self, findings: list) -> list:
        return [dict(f, snapshot_id=self.snapshot["snapshot_id"]) if isinstance(f, dict) and "snapshot_id" not in f
                else f for f in findings]

    def report(self, findings: list, cases: list, **kw) -> dict:
        return HS.report(self.stamped(findings), cases, self.snapshot, self.read, **kw)

    def command(self, *argv: str, seed: str = "0") -> tuple[int, str]:
        done = subprocess.run([sys.executable, "-m", "harness.score", *argv], cwd=REFEREE, capture_output=True,
                              text=True, env=dict(os.environ, PYTHONHASHSEED=seed))
        return done.returncode, done.stdout

    def file(self, name: str, value) -> str:
        path = os.path.join(self.root, name)
        with open(path, "w") as fh:
            json.dump(value, fh)
        return path


class Empty(Base):
    """Test 1."""

    def test_no_finding_is_recall_zero_and_a_report(self):
        out = self.report([], [case("c1", 2), case("c2", 3)], alpha=TENTH, min_groups=1)
        self.assertEqual(out["hits"], 0)
        self.assertEqual(out["refused"], [])
        self.assertEqual(out["counts"], {"given": 0, "distinct": 0, "reobserved": 0, "refused": 0})
        report = out["report"]
        self.assertEqual((report["n"], report["n_groups"], report["recall"], report["x_eff"], report["recall_lb"]),
                         (2, 1, "0.000000", "0.000000", "0.000000"))
        self.assertEqual(report["census"], {"rules_total": 1, "rules_covered": 0, "misses": 2})
        self.assertEqual((report["verdict"], out["verdict_reason"]), ("FAIL", "misses"))

    def test_no_finding_and_no_case(self):
        out = self.report([], [], alpha=TENTH, min_groups=1)
        report = out["report"]
        self.assertEqual((report["n"], report["recall"], report["x_eff"], report["recall_lb"], report["census"]),
                         (0, None, None, None, None))
        self.assertEqual((report["clean_findings"], report["verdict"], out["verdict_reason"]),
                         (0, "UNMEASURABLE", "no_cases"))

    def test_the_command_on_an_empty_list(self):
        empty, cases = self.file("f.json", []), self.file("c.json", [case("c1", 2)])
        self.assertEqual(self.command(empty, cases), (0, '{"hits": 0}\n'))
        code, text = self.command(empty, cases, "--snapshot", self.file("s.json", self.snapshot), "--tree", self.tree)
        self.assertEqual((code, json.loads(text)["report"]["recall"]), (0, "0.000000"))


class Refs(Base):
    """Test 6."""

    def refused(self, findings: list, cases=None) -> list:
        out = self.report(findings, [case("c1", 2)] if cases is None else cases)
        self.assertEqual(out["hits"], 0)
        return out["refused"]

    def test_the_control_a_reference_of_the_manifest_hits(self):
        out = self.report([finding("x", 2)], [case("c1", 2)])
        self.assertEqual((out["hits"], out["refused"], out["matched"]), (1, [], {"c1": "x"}))

    def test_outside_the_manifest(self):
        # the case is on the very path and line the finding names: only the manifest refuses it
        self.assertNotIn("pkg/gone.js", self.snapshot["files"])
        self.assertEqual(self.refused([finding("x", 2, path="pkg/gone.js")], [case("c1", 2, path="pkg/gone.js")]),
                         [{"index": 0, "reasons": ["ref_outside_manifest"]}])
        # a file that is in the tree but not in the manifest is outside it too
        write_tree(self.tree, {"pkg/new.js": A_JS})
        self.assertEqual(self.refused([finding("x", 2, path="pkg/new.js")], [case("c1", 2, path="pkg/new.js")]),
                         [{"index": 0, "reasons": ["ref_outside_manifest"]}])

    def test_one_reference_outside_refuses_the_finding(self):
        both = finding("x", 2)
        both["evidence_refs"].append({"path": "nowhere.js", "line_start": 1, "line_end": 1})
        self.assertEqual(self.refused([both]), [{"index": 0, "reasons": ["ref_outside_manifest"]}])

    def test_bytes_that_are_not_the_manifests(self):
        before = self.read("pkg/a.js")
        with open(os.path.join(self.tree, "pkg/a.js"), "wb") as fh:
            fh.write(before.replace(b"var e = 5;", b"var e = 6;"))
        self.assertNotEqual(self.read("pkg/a.js"), before)
        self.assertEqual(self.refused([finding("x", 2)]), [{"index": 0, "reasons": ["ref_hash_mismatch"]}])

    def test_a_file_of_the_manifest_that_is_not_there(self):
        os.remove(os.path.join(self.tree, "pkg/a.js"))
        self.assertEqual(self.refused([finding("x", 2)]), [{"index": 0, "reasons": ["ref_hash_mismatch"]}])

    def test_another_snapshot(self):
        other = finding("x", 2, snapshot_id="0" * 64)
        self.assertEqual(self.refused([other]), [{"index": 0, "reasons": ["snapshot_mismatch"]}])
        absent = finding("x", 2, snapshot_id=None)
        self.assertEqual(self.refused([absent]), [{"index": 0, "reasons": ["snapshot_mismatch"]}])

    def test_a_line_the_file_does_not_have(self):
        # pkg/a.js has five lines; lib/c.js two, the last without a newline
        self.assertEqual(self.refused([finding("x", 6)], [case("c1", 6)]),
                         [{"index": 0, "reasons": ["ref_line_missing"]}])
        self.assertEqual(self.report([finding("x", 5)], [case("c1", 5)])["hits"], 1)
        self.assertEqual(self.report([finding("x", 2, path="lib/c.js")], [case("c1", 2, path="lib/c.js")])["hits"], 1)
        self.assertEqual(self.refused([finding("x", 3, path="lib/c.js")], [case("c1", 3, path="lib/c.js")]),
                         [{"index": 0, "reasons": ["ref_line_missing"]}])

    def test_every_reason_in_its_order_each_once(self):
        bad = finding("x", 9, 9, snapshot_id="other")
        bad["evidence_refs"] += [{"path": "nowhere.js", "line_start": 1, "line_end": 1}] * 2
        self.assertEqual(self.refused([bad]),
                         [{"index": 0, "reasons": ["snapshot_mismatch", "ref_outside_manifest", "ref_line_missing"]}])

    def test_what_is_no_finding(self):
        shapes = [None, "x", {}, finding(""), dict(finding("x", 2), fingerprint=7), finding("x"),
                  dict(finding("x", 2), evidence_refs={}), dict(finding("x", 2), evidence_refs=[None]),
                  dict(finding("x", 2), evidence_refs=[{"path": 1, "line_start": 2, "line_end": 2}]),
                  dict(finding("x", 2), evidence_refs=[{"path": "pkg/a.js", "line_start": 0, "line_end": 2}]),
                  dict(finding("x", 2), evidence_refs=[{"path": "pkg/a.js", "line_start": 3, "line_end": 2}]),
                  dict(finding("x", 2), evidence_refs=[{"path": "pkg/a.js", "line_start": True, "line_end": 2}]),
                  dict(finding("x", 2), evidence_refs=[{"path": "pkg/a.js", "line_start": 2, "line_end": 2.0}])]
        self.assertEqual(self.refused(shapes),
                         [{"index": i, "reasons": ["finding_invalid"]} for i in range(len(shapes))])

    def test_the_index_is_the_place_in_the_list_and_the_others_are_scored(self):
        out = self.report([finding("x", 2, path="nowhere.js"), finding("y", 2), None], [case("c1", 2)])
        self.assertEqual((out["hits"], out["matched"]), (1, {"c1": "y"}))
        self.assertEqual(out["refused"], [{"index": 0, "reasons": ["ref_outside_manifest"]},
                                          {"index": 2, "reasons": ["finding_invalid"]}])
        self.assertEqual(out["counts"], {"given": 3, "distinct": 1, "reobserved": 0, "refused": 2})

    def test_a_refused_finding_is_counted_in_a_clean_run(self):
        out = self.report([finding("x", 2, path="nowhere.js"), finding("y", 2), None], [])
        self.assertEqual(out["report"]["clean_findings"], 3)

    def test_the_command_reports_them(self):
        cases = self.file("c.json", [case("c1", 2, path="nowhere.js")])
        findings = self.file("f.json", self.stamped([finding("x", 2, path="nowhere.js")]))
        code, text = self.command(findings, cases, "--snapshot", self.file("s.json", self.snapshot), "--tree", self.tree)
        self.assertEqual((code, json.loads(text)["refused"], json.loads(text)["hits"]),
                         (0, [{"index": 0, "reasons": ["ref_outside_manifest"]}], 0))
        # without a snapshot the references are not judged, the shape is
        self.assertEqual(self.command(findings, cases), (0, '{"hits": 1}\n'))
        self.assertEqual(self.command(self.file("g.json", [None]), cases),
                         (0, '{"hits": 0, "refused": [{"index": 0, "reasons": ["finding_invalid"]}]}\n'))


# two cases of one rule on lines 2 and 3; f-wide hits both, f-narrow only c1: the largest matching is two
WIDE, NARROW = finding("wide", 2, 3), finding("narrow", 2)
TWO = [case("c1", 2), case("c2", 3)]


def span(fingerprint: str, *spans: tuple, **over) -> dict:
    """``finding`` whose references are the ``(line_start, line_end)`` pairs."""
    made = finding(fingerprint, *[first for first, _ in spans], **over)
    for ref, (_, last) in zip(made["evidence_refs"], spans):
        ref["line_end"] = last
    return made


class RefLength(Base):
    """``ref_over_max_lines``: every reference of the finding spans more lines than ``ref_max_lines``."""

    def test_the_bound_is_the_number_of_lines_spanned(self):
        cases = [case("c1", 1, end=5)]
        at_bound = self.report([span("x", (2, 4))], cases, ref_max_lines=3)
        self.assertEqual((at_bound["hits"], at_bound["refused"]), (1, []))
        over = self.report([span("x", (2, 5))], cases, ref_max_lines=3)
        self.assertEqual((over["hits"], over["refused"]), (0, [{"index": 0, "reasons": ["ref_over_max_lines"]}]))
        self.assertEqual(over["counts"], {"given": 1, "distinct": 0, "reobserved": 0, "refused": 1})
        one_line = self.report([span("x", (2, 2))], cases, ref_max_lines=1)
        self.assertEqual((one_line["hits"], one_line["refused"]), (1, []))

    def test_one_reference_within_the_bound_keeps_the_finding(self):
        cases = [case("c1", 1, end=5)]
        for spans in (((1, 5), (2, 2)), ((2, 2), (1, 5)), ((1, 4), (1, 5), (2, 3))):
            with self.subTest(spans=spans):
                self.assertEqual(self.report([span("x", *spans)], cases, ref_max_lines=2)["refused"], [])
        every = self.report([span("x", (1, 3), (2, 5))], cases, ref_max_lines=2)
        self.assertEqual(every["refused"], [{"index": 0, "reasons": ["ref_over_max_lines"]}])

    def test_without_the_bound_no_length_is_judged(self):
        out = self.report([span("x", (2, 5))], [case("c1", 1, end=5)])
        self.assertEqual((out["hits"], out["refused"]), (1, []))
        self.assertEqual(HS.sift([span("x", (1, 500))])[1], [])

    def test_its_place_among_the_reasons(self):
        long_missing = span("y", (1, 9), path="pkg/none.js")
        twin = dict(span("x", (1, 5)), rule_id="other")
        out = self.report([finding("x", 2), twin, long_missing], [case("c1", 1, end=5)], ref_max_lines=2)
        self.assertEqual(out["refused"], [{"index": 1, "reasons": ["fingerprint_conflict", "ref_over_max_lines"]},
                                          {"index": 2, "reasons": ["ref_over_max_lines", "ref_outside_manifest"]}])

    def test_without_a_snapshot_too(self):
        accepted, refused, _ = HS.sift([span("x", (1, 5)), span("y", (1, 2))], ref_max_lines=2)
        self.assertEqual(([f["fingerprint"] for f in accepted], refused),
                         (["y"], [{"index": 0, "reasons": ["ref_over_max_lines"]}]))

    def test_a_bound_that_is_no_positive_integer_is_unusable(self):
        for bad in (0, -1, True, 2.0, "2"):
            with self.subTest(bad=bad), self.assertRaises(HS.Unusable) as ctx:
                self.report([finding("x", 2)], [case("c1", 1, end=5)], ref_max_lines=bad)
            self.assertEqual(ctx.exception.reasons, ["ref_max_lines_invalid"])

    def test_the_command_s_option_in_both_forms(self):
        found, cases = self.file("f.json", self.stamped([span("x", (2, 4))])), self.file("c.json", [case("c1", 1, end=5)])
        refused = [{"index": 0, "reasons": ["ref_over_max_lines"]}]
        self.assertEqual(self.command(found, cases, "--ref-max-lines", "3"), (0, '{"hits": 1}\n'))
        code, text = self.command(found, cases, "--ref-max-lines", "2")
        self.assertEqual((code, json.loads(text)), (0, {"hits": 0, "refused": refused}))
        snapshot = self.file("s.json", self.snapshot)
        code, text = self.command(found, cases, "--snapshot", snapshot, "--tree", self.tree, "--ref-max-lines", "2")
        self.assertEqual((code, json.loads(text)["refused"]), (0, refused))
        code, text = self.command(found, cases, "--snapshot", snapshot, "--tree", self.tree, "--ref-max-lines", "3")
        self.assertEqual((code, json.loads(text)["hits"]), (0, 1))
        for bad in ("0", "x", "-1", "1.5"):
            code, text = self.command(found, cases, "--ref-max-lines", bad)
            self.assertEqual((code, json.loads(text)["ok"]), (2, False), bad)


class FromPolicy(Base):
    """``loop.job.yaz_harness`` gives the scorer ``harness.params.score`` of the artifact's policy."""

    K3 = {"class_level": "K3", "property": "p"}

    def harness(self, policy, findings: list, cases: list) -> dict:
        art = types.SimpleNamespace(snapshot=self.snapshot, policy=policy)
        with mock.patch.object(J, "FINDINGS", self.stamped(findings)):
            return J.yaz_harness(art, self.tree, {"cases": cases})

    def policy(self, level=0.9, **params) -> dict:
        return {"constitutional": {"confidence_level": level, "stage_params": params}}

    def test_each_value_reaches_the_report(self):
        cases, findings = [case("c1", 2), case("c2", 3, group="lib")], [finding("x", 2), finding("y", 3)]
        bare = self.harness({}, findings, cases)
        self.assertEqual(bare, self.report(findings, cases))
        self.assertEqual((bare["report"]["recall_lb"], bare["verdict_reason"]), (None, "min_groups_unknown"))
        got = self.harness(self.policy(census_min_groups=2), findings, cases)
        self.assertEqual(got, self.report(findings, cases, alpha=TENTH, min_groups=2))
        self.assertEqual((got["report"]["recall_lb"], got["report"]["verdict"]),
                         (ST.fixed6(ST.cp_lower(Fraction(2), 2, TENTH)), "PASS"))
        self.assertEqual(self.harness(self.policy(census_min_groups=3), findings, cases)["verdict_reason"],
                         "groups_below_min")
        other = self.harness(self.policy(level=0.5, census_min_groups=2), findings, cases)
        self.assertEqual(other["report"]["recall_lb"], ST.fixed6(ST.cp_lower(Fraction(2), 2, Fraction(1, 2))))
        self.assertNotEqual(other["report"]["recall_lb"], got["report"]["recall_lb"])

    def test_the_window_and_the_reference_bound(self):
        cases = [dict(case("c1", 2), **self.K3)]
        near = dict(finding("x", 4), property="p", required_change=[{"file": "a", "op": "e"}])
        self.assertEqual(self.harness(self.policy(), [near], cases)["hits"], 0)
        self.assertEqual(self.harness(self.policy(match_window_lines=1), [near], cases)["hits"], 0)
        self.assertEqual(self.harness(self.policy(match_window_lines=2), [near], cases)["hits"], 1)
        long = [span("x", (2, 4))]
        self.assertEqual(self.harness(self.policy(evidence_ref_max_lines=3), long, [case("c1", 1, end=5)])["refused"], [])
        self.assertEqual(self.harness(self.policy(evidence_ref_max_lines=2), long, [case("c1", 1, end=5)])["refused"],
                         [{"index": 0, "reasons": ["ref_over_max_lines"]}])

    def test_a_value_elsewhere_in_the_policy_is_not_read(self):
        policy = {"confidence_level": 0.9, "stage_params": {"census_min_groups": 1, "match_window_lines": 9},
                  "performance": self.policy(census_min_groups=1)["constitutional"], "census_min_groups": 1}
        cases, findings = [case("c1", 2)], [finding("x", 2)]
        self.assertEqual(self.harness(policy, findings, cases), self.report(findings, cases))

    def test_an_invalid_value_refuses_the_report(self):
        got = self.harness(self.policy(level=2, match_window_lines=0), [], [case("c1", 2)])
        self.assertEqual(got, {"reason": "harness_refused",
                               "reasons": ["policy_invalid:constitutional.confidence_level",
                                           "policy_invalid:constitutional.stage_params.match_window_lines"]})
        self.assertEqual(self.harness([], [], [])["reason"], "harness_refused")


class Match(Base):
    def test_a_finding_takes_one_case(self):
        self.assertEqual(self.report([WIDE], TWO)["hits"], 1)
        # which of the two it takes is the first by case_id, in either order of the list
        self.assertEqual([self.report([WIDE], cases)["matched"] for cases in (TWO, TWO[::-1])], [{"c1": "wide"}] * 2)
        self.assertEqual(self.report([finding("x", 3)], [case("c1", 3), case("c2", 3, end=4)])["hits"], 1)

    def test_a_case_counts_once(self):
        self.assertEqual(self.report([finding("x", 2), finding("y", 2)], [case("c1", 2)])["hits"], 1)

    def test_the_largest_matching_in_any_order(self):
        for findings in ([WIDE, NARROW], [NARROW, WIDE]):
            for cases in (TWO, TWO[::-1]):
                out = self.report(findings, cases)
                self.assertEqual((out["hits"], out["matched"]), (2, {"c1": "narrow", "c2": "wide"}))

    def test_a_chain_of_three(self):
        # a: c1 c2, b: c2 c3, c: c1 only, given so that a and b sit on c1 and c2 before c comes
        cases = [case("c1", 1), case("c2", 2), case("c3", 3)]
        out = self.report([finding("a", 1, 2), finding("b", 2, 3), finding("c", 1)], cases)
        self.assertEqual(out["matched"], {"c1": "c", "c2": "a", "c3": "b"})

    def test_the_hit_rule_is_cases_builds(self):
        self.assertEqual(self.report([finding("x", 2, rule="no-eval")], [case("c1", 2)])["hits"], 0)
        self.assertEqual(self.report([finding("x", 3)], [case("c1", 2)])["hits"], 0)
        # K3: the window is the caller's
        k3 = dict(case("c1", 2, class_level="K3"), property="p")
        found = dict(finding("x", 4), property="p", required_change=[{"file": "pkg/a.js", "op": "edit"}])
        self.assertEqual(self.report([found], [k3])["hits"], 0)
        self.assertEqual(self.report([found], [k3], window=2)["hits"], 1)
        self.assertEqual(self.report([found], [k3], window=1)["hits"], 0)


class Determinism(Base):
    """Test 7."""

    def test_the_same_input_twice_is_the_same_bytes(self):
        findings = self.file("f.json", self.stamped([WIDE, NARROW, finding("z", 9), None, finding("wide", 4)]))
        cases = self.file("c.json", TWO + [case("c3", 1, path="pkg/b.js", rule="no-eval", group="other")])
        args = (findings, cases, "--snapshot", self.file("s.json", self.snapshot), "--tree", self.tree,
                "--alpha", "0.10", "--min-groups", "2")
        first, second = self.command(*args, seed="1"), self.command(*args, seed="2")
        self.assertEqual(first, second)
        self.assertEqual(first[0], 0)
        out = json.loads(first[1])
        self.assertEqual((out["hits"], out["report"]["recall"], out["missed_rules"]),
                         (2, "0.666667", [["eslint", "no-eval"]]))
        self.assertEqual(self.command(findings, cases, seed="1"), self.command(findings, cases, seed="2"))

    def test_report_twice_and_its_arguments_unchanged(self):
        findings, cases = self.stamped([WIDE, NARROW, None]), list(TWO)
        kept = copy.deepcopy((findings, cases, self.snapshot))
        first = self.report(findings, cases, alpha=TENTH)
        self.assertEqual(first, self.report(findings, cases, alpha=TENTH))
        self.assertEqual((findings, cases, self.snapshot), kept)

    def test_one_byte_of_the_input_changes_the_report(self):
        self.assertNotEqual(self.report([finding("x", 2)], [case("c1", 2)]),
                            self.report([finding("x", 3)], [case("c1", 2)]))


class Fingerprint(Base):
    """Test 12."""

    def test_the_same_finding_in_two_runs_is_one(self):
        run = [finding("x", 2), finding("y", 3)]
        once, twice = self.report(run, []), self.report(run + copy.deepcopy(run), [])
        self.assertEqual(once["report"]["clean_findings"], 2)
        self.assertEqual(twice["report"]["clean_findings"], 2)
        self.assertEqual(twice["counts"], {"given": 4, "distinct": 2, "reobserved": 2, "refused": 0})
        # against cases too: the second run's copies take no second case
        cases = [case("c1", 2), case("c2", 2, end=3)]
        self.assertEqual(self.report([finding("x", 2)] * 2, cases)["hits"], 1)
        self.assertEqual(self.report([finding("x", 2), finding("other", 2)], cases)["hits"], 2)

    def test_a_shifted_line_is_the_same_finding(self):
        shifted = [finding("x", 2), finding("x", 3), dict(finding("x", 4), finding_id="another-id", claim="moved")]
        out = self.report(shifted, [])
        self.assertEqual((out["report"]["clean_findings"], out["counts"]["distinct"], out["counts"]["reobserved"]),
                         (1, 1, 2))
        # the control: three fingerprints are three findings
        self.assertEqual(self.report([finding("x", 2), finding("y", 3), finding("z", 4)], [])["report"]["clean_findings"], 3)
        # and a re-observation is not read to match: lines 2 and 3 under one fingerprint take one case of TWO
        self.assertEqual(self.report(shifted, TWO)["hits"], 1)
        self.assertEqual(self.report(shifted, TWO)["matched"], {"c1": "x"})

    def test_one_fingerprint_over_two_files_or_rules_is_refused(self):
        for index, other in enumerate([finding("x", 1, path="pkg/b.js"), finding("x", 2, rule="no-eval"),
                                       dict(finding("x", 2), property="other"), dict(finding("x", 2), symbol="f"),
                                       dict(finding("x", 2), tool="ruff")]):
            with self.subTest(index=index):
                out = self.report([finding("x", 2), other], [])
                self.assertEqual(out["refused"], [{"index": 1, "reasons": ["fingerprint_conflict"]}])
                self.assertEqual(out["report"]["clean_findings"], 2)   # folded it would be 1

    def test_a_refused_finding_gives_its_fingerprint_to_no_one(self):
        out = self.report([finding("x", 2, path="nowhere.js"), finding("x", 2)], [case("c1", 2)])
        self.assertEqual((out["hits"], out["counts"]["distinct"], out["counts"]["reobserved"]), (1, 1, 0))

    def test_without_a_snapshot_too(self):
        accepted, refused, reobserved = HS.sift([finding("x", 2), finding("x", 3), finding("x", 1, path="pkg/b.js")])
        self.assertEqual((accepted, refused, reobserved),
                         ([finding("x", 2)], [{"index": 2, "reasons": ["fingerprint_conflict"]}], 1))


CP_TABLE = (("60", 60, "0.9624"), ("45", 45, "0.9501"), ("44", 44, "0.9490"), ("25", 25, "0.9120"),
            ("10", 10, "0.7943"), ("8", 10, "0.5504"), ("7.5", 10, "0.4982"), ("8.0", 10, "0.5504"))
ANSWER_S = 20   # a harness.stats command of these tests answers inside this many seconds or its test is red
MCNEMAR_TABLE = ((0, 3, "0.1250"), (0, 4, "0.0625"), (1, 7, "0.0352"), (0, 8, "0.0039"), (2, 8, "0.0547"))


def four(text: str) -> str:
    """A six-decimal string rounded to tohum/29a's four decimals."""
    return "%.4f" % (round(Fraction(text) * 10 ** 4) / 10 ** 4)


class Statistics(Base):
    """Test 28."""

    def stats(self, *argv: str) -> tuple[int, str]:
        # an answer later than ANSWER_S is this test's red (subprocess.TimeoutExpired), not a wait
        done = subprocess.run([sys.executable, "-m", "harness.stats", *argv], cwd=REFEREE, capture_output=True, text=True,
                              timeout=ANSWER_S)
        return done.returncode, done.stdout

    def test_the_clopper_pearson_table(self):
        for x, n, want in CP_TABLE:
            with self.subTest(x=x, n=n):
                code, text = self.stats("cp_lower", x, str(n), "0.10")
                self.assertEqual(code, 0)
                self.assertRegex(text, r'\A\{"lb": "[01]\.[0-9]{6}"\}\n\Z')
                self.assertEqual(four(json.loads(text)["lb"]), want)

    def test_the_bound_at_all_successes_is_the_closed_form(self):
        for n in (1, 10, 60, 300):
            for alpha in (Fraction(1, 10), Fraction(1, 20), Fraction(1, 2)):
                self.assertAlmostEqual(ST.cp_lower(Fraction(n), n, alpha), float(alpha) ** (1 / n), places=9)

    def test_the_bound_rises_with_the_successes_and_is_zero_at_none(self):
        self.assertEqual(ST.cp_lower(Fraction(0), 10, TENTH), 0.0)
        bounds = [ST.cp_lower(Fraction(x, 2), 10, TENTH) for x in range(0, 21)]
        self.assertEqual(bounds, sorted(set(bounds)))
        # one success of one at alpha: the bound is alpha itself
        self.assertAlmostEqual(ST.cp_lower(Fraction(1), 1, TENTH), 0.1, places=9)
        # and it falls as alpha does
        self.assertLess(ST.cp_lower(Fraction(8), 10, Fraction(1, 20)), ST.cp_lower(Fraction(8), 10, TENTH))

    def test_the_mcnemar_table(self):
        for b, c, want in MCNEMAR_TABLE:
            with self.subTest(b=b, c=c):
                code, text = self.stats("mcnemar", str(b), str(c))
                self.assertEqual(code, 0)
                self.assertRegex(text, r'\A\{"p": "[01]\.[0-9]{6}"\}\n\Z')
                self.assertEqual(four(json.loads(text)["p"]), want)
        self.assertEqual(self.stats("mcnemar", "0", "4"), (0, '{"p": "0.062500"}\n'))

    def test_mcnemar_is_the_exact_tail(self):
        self.assertEqual(ST.mcnemar(0, 0), 1)
        self.assertEqual(ST.mcnemar(3, 0), 1)
        self.assertEqual(ST.mcnemar(1, 1), Fraction(3, 4))
        self.assertEqual(ST.mcnemar(7, 1), Fraction(255, 256))   # not symmetric: b favours the old
        self.assertEqual(ST.mcnemar(1, 7), Fraction(9, 256))

    def test_mcnemar_is_the_summed_row_for_every_small_pair(self):
        # the definition, term by term, beside the function's shorter-side sum: both sides of b + 1 <= c
        for b in range(0, 34):
            for c in range(0, 34):
                n = b + c
                self.assertEqual(ST.mcnemar(b, c), Fraction(sum(math.comb(n, k) for k in range(c, n + 1)), 2 ** n), (b, c))

    def test_mcnemar_sums_the_shorter_side_of_the_row(self):
        # the work the bound is measured for: min(b + 1, c) terms, never the longer side
        asked = []
        whole = ST._row_head
        with mock.patch.object(ST, "_row_head", lambda n, terms: asked.append((n, terms)) or whole(n, terms)):
            for b, c in ((5, 100), (100, 5), (7, 8), (8, 8), (0, 0), (0, 9), (9, 0)):
                ST.mcnemar(b, c)
        self.assertEqual(asked, [(105, 6), (105, 5), (15, 8), (16, 8), (0, 0), (9, 1), (9, 0)])
        self.assertEqual([whole(6, terms) for terms in range(8)], [0, 1, 7, 22, 42, 57, 63, 64])

    def test_mcnemar_at_larger_counts_by_two_identities(self):
        # an even split: half of what the middle term leaves, plus the middle term
        for half in (1, 100, 1000):
            self.assertEqual(ST.mcnemar(half, half), Fraction(1, 2) + Fraction(math.comb(2 * half, half), 2 ** (2 * half + 1)))
        # the two tails cover the row and share the term at c
        for b, c in ((700, 900), (900, 700), (1, 1500), (1500, 1)):
            self.assertEqual(ST.mcnemar(b, c) + ST.mcnemar(c - 1, b + 1), 1, (b, c))
            # and one step of c is one term of the row
            self.assertEqual(ST.mcnemar(b, c) - ST.mcnemar(b - 1, c + 1), Fraction(math.comb(b + c, c), 2 ** (b + c)), (b, c))

    def test_mcnemar_refuses_more_pairs_than_its_bound_and_answers_at_it(self):
        top = ST.MAX_PAIRS
        self.assertEqual(top, 20000)
        self.assertEqual(ST.mcnemar(top, 0), 1)
        self.assertEqual(ST.mcnemar(0, top), Fraction(1, 2 ** top))
        # no subTest: the first count that is not refused ends the test, before the counts no machine can sum
        for b, c in ((top + 1, 0), (0, top + 1), (top // 2 + 1, top // 2), (1, top), (10 ** 30, 10 ** 30)):
            with self.assertRaises(ValueError, msg=(b, c)):
                ST.mcnemar(b, c)
        # the command: the costliest counts inside the bound answer (inside ANSWER_S), with the even split's value;
        half = top // 2
        want = ST.fixed6(Fraction(1, 2) + Fraction(math.comb(top, half), 2 ** (top + 1)))
        self.assertEqual(self.stats("mcnemar", str(half), str(half)), (0, '{"p": "%s"}\n' % want))
        # one pair more, and the counts of founder ledger f1639 (no answer in 20 s before the bound), are refused
        for argv in (["mcnemar", str(half + 1), str(half)], ["mcnemar", "200000", "200000"],
                     ["mcnemar", "9" * 12, "9" * 12]):
            with self.subTest(argv=argv):
                code, text = self.stats(*argv)
                self.assertEqual((code, json.loads(text)["ok"]), (2, False))

    def test_fixed6(self):
        self.assertEqual([ST.fixed6(Fraction(*q)) for q in ((0, 1), (1, 1), (2, 3), (1, 2000000), (3, 2000000), (15, 2))],
                         ["0.000000", "1.000000", "0.666667", "0.000000", "0.000002", "7.500000"])
        self.assertEqual(ST.fixed6(0.5), "0.500000")
        for bad in (Fraction(-1, 2), 1, "1"):
            with self.assertRaises(ValueError):
                ST.fixed6(bad)

    def test_arguments_refused(self):
        for argv in ([], ["cp_lower"], ["cp_lower", "11", "10", "0.10"], ["cp_lower", "5", "0", "0.10"],
                     ["cp_lower", "5", "10", "0"], ["cp_lower", "5", "10", "1"], ["cp_lower", "-1", "10", "0.1"],
                     ["cp_lower", "5", "10.0", "0.1"], ["cp_lower", "5", "10", "1e-1"], ["cp_lower", "٥", "10", "0.1"],
                     ["cp_lower", "5", "10", "0.1", "x"], ["mcnemar", "1"], ["mcnemar", "1", "2.0"],
                     ["mcnemar", "-1", "2"], ["mcnemar", "1", "9" * 13], ["other", "1", "2"]):
            with self.subTest(argv=argv):
                code, text = self.stats(*argv)
                self.assertEqual((code, json.loads(text)["ok"]), (2, False))
        for bad in ((Fraction(1), 0, TENTH), (Fraction(2), 1, TENTH), (1, 1, TENTH), (Fraction(1), 1, 0.1),
                    (Fraction(1), 1, Fraction(1)), (Fraction(1), True, TENTH)):
            with self.assertRaises(ValueError):
                ST.cp_lower(*bad)
        for bad in ((-1, 1), (1, -1), (1.0, 1), (True, 1)):
            with self.assertRaises(ValueError):
                ST.mcnemar(*bad)

    def scored(self, hits: int, per_group: int) -> dict:
        """Ten groups of ``per_group`` cases each, the first ``hits`` cases hit."""
        tree = {"g%d/f.js" % g: "var a = 1;\n" * per_group for g in range(10)}
        write_tree(self.tree, tree)
        self.snapshot = LK.snapshot_of(self.tree)
        cases = [case("c-%d-%d" % (g, k), k + 1, path="g%d/f.js" % g, group="g%d" % g)
                 for g in range(10) for k in range(per_group)]
        findings = [finding("fp-" + c["case_id"], c["touched_paths"][0]["hunks"][0]["start"],
                            path=c["touched_paths"][0]["path"]) for c in cases[:hits]]
        return self.report(findings, cases, alpha=TENTH)["report"]

    def test_x_eff_and_the_bound_in_the_report(self):
        # eight of ten in ten groups: x_eff 8,0, the integer row of the table
        report = self.scored(8, 1)
        self.assertEqual((report["n"], report["n_groups"], report["recall"], report["x_eff"]),
                         (10, 10, "0.800000", "8.000000"))
        self.assertEqual(four(report["recall_lb"]), "0.5504")
        # fifteen of twenty in ten groups: the real x_eff 7,5 of the table, with n the groups and not the cases
        report = self.scored(15, 2)
        self.assertEqual((report["n"], report["n_groups"], report["recall"], report["x_eff"]),
                         (20, 10, "0.750000", "7.500000"))
        self.assertEqual(four(report["recall_lb"]), "0.4982")
        # all of ten: the table's (10, 10)
        self.assertEqual(four(self.scored(10, 1)["recall_lb"]), "0.7943")

    def test_the_bound_is_of_the_exact_x_eff(self):
        # five of seven cases in two groups: x_eff is 10/7, and its six decimals give another bound
        cases = [case("a%d" % n, n) for n in range(1, 6)] + [case("b%d" % n, n, path="lib/c.js", group="lib") for n in (1, 2)]
        report = self.report([finding("x%d" % n, n) for n in range(1, 6)], cases, alpha=TENTH)["report"]
        self.assertEqual((report["recall"], report["x_eff"]), ("0.714286", "1.428571"))
        self.assertEqual(report["recall_lb"], ST.fixed6(ST.cp_lower(Fraction(10, 7), 2, TENTH)))
        self.assertNotEqual(report["recall_lb"], ST.fixed6(ST.cp_lower(Fraction("1.428571"), 2, TENTH)))

    def test_without_alpha_no_bound(self):
        report = self.report([finding("x", 2)], [case("c1", 2)])["report"]
        self.assertEqual((report["recall"], report["recall_lb"]), ("1.000000", None))


class Report(Base):
    def test_the_fields_are_26b_s(self):
        meta = {"run_id": "r1", "spec_version": "2.2", "hunter_id": "h", "prompt_sha256": "p", "rung": 1, "n": 99}
        out = self.report([finding("x", 2)], [case("c1", 2)], alpha=TENTH, min_groups=1, meta=meta)
        self.assertEqual(set(out), {"report", "hits", "matched", "missed_rules", "refused", "counts", "verdict_reason"})
        self.assertEqual(out["report"], {
            "run_id": "r1", "snapshot_id": self.snapshot["snapshot_id"], "spec_version": "2.2",
            "match_rule_version": "v2", "hunter_id": "h", "prompt_sha256": "p", "rung": 1, "n": 1, "n_groups": 1,
            "x_eff": "1.000000", "recall": "1.000000", "recall_lb": "0.100000", "precision": None,
            "precision_lb": None, "census": {"rules_total": 1, "rules_covered": 1, "misses": 0},
            "clean_findings": None, "unresolved": None, "cost_usd": None, "value_per_usd": None, "verdict": "PASS"})
        bare = self.report([], [])["report"]
        self.assertEqual([bare[k] for k in HS.META], [None] * 5)
        self.assertEqual(set(bare), set(out["report"]))

    def test_no_float_in_the_output(self):
        def walk(value):
            self.assertNotIsInstance(value, float)
            for inner in (value.values() if isinstance(value, dict) else value if isinstance(value, list) else ()):
                walk(inner)
        walk(self.report([finding("x", 2)], TWO + [case("c3", 4, group="g")], alpha=TENTH, min_groups=1))

    def test_the_census(self):
        cases = [case("c1", 2), case("c2", 3), case("c3", 4, rule="no-eval"), case("c4", 1, path="pkg/b.js", rule="eqeqeq")]
        out = self.report([finding("x", 2), finding("y", 4, rule="no-eval")], cases)
        # no-var has one case hit and one missed: a rule with a miss is not covered
        self.assertEqual(out["report"]["census"], {"rules_total": 3, "rules_covered": 1, "misses": 2})
        self.assertEqual(out["missed_rules"], [["eslint", "eqeqeq"], ["eslint", "no-var"]])
        # the same rule id of another tool is another rule
        out = self.report([], [case("c1", 2), case("c2", 3, tool="ruff")])
        self.assertEqual(out["report"]["census"]["rules_total"], 2)

    def test_the_verdicts(self):
        hit, cases = [finding("x", 2), finding("y", 1, path="pkg/b.js")], [case("c1", 2), case("c2", 1, path="pkg/b.js", group="g2")]
        for kw, want in (({"min_groups": 2}, ("PASS", None)), ({"min_groups": 3}, ("UNMEASURABLE", "groups_below_min")),
                         ({}, ("UNMEASURABLE", "min_groups_unknown"))):
            out = self.report(hit, cases, **kw)
            self.assertEqual((out["report"]["verdict"], out["verdict_reason"]), want)
        out = self.report(hit[:1], cases, min_groups=1)
        self.assertEqual((out["report"]["verdict"], out["verdict_reason"]), ("FAIL", "misses"))
        # a class outside the census: recall is reported, nothing is gated
        k3 = [case("c1", 2, class_level="K3")]
        found = dict(finding("x", 2), required_change=[{"file": "pkg/a.js", "op": "edit"}])
        out = self.report([found], k3, min_groups=1, window=0)
        self.assertEqual((out["hits"], out["report"]["recall"], out["report"]["census"], out["missed_rules"],
                          out["report"]["verdict"], out["verdict_reason"]),
                         (1, "1.000000", None, None, "UNMEASURABLE", "class_without_census"))

    def test_cases_refused(self):
        good = case("c1", 2)
        for cases, reasons in (({}, ["cases_invalid"]), ([good, None], ["case_invalid:1"]),
                               ([dict(good, case_id=1)], ["case_invalid:0"]),
                               ([{k: v for k, v in good.items() if k != "group"}], ["case_invalid:0"]),
                               ([{k: v for k, v in good.items() if k != "rule_id"}], ["case_invalid:0"]),
                               ([good, case("c2", 3), dict(good)], ["case_id_twice:2"]),
                               ([good, case("c2", 3, class_level="K1")], ["cases_mixed_class"])):
            with self.subTest(reasons=reasons):
                with self.assertRaises(HS.Unusable) as caught:
                    self.report([], cases)
                self.assertEqual(caught.exception.reasons, reasons)
        with self.assertRaises(HS.Unusable) as caught:
            HS.report({}, [good], self.snapshot, self.read)
        self.assertEqual(caught.exception.reasons, ["findings_invalid"])

    def test_a_document_that_is_no_snapshot(self):
        for document, reasons in ((None, ["snapshot:document_invalid"]),
                                  (dict(self.snapshot, snapshot_id="0" * 64), ["snapshot:id_mismatch"])):
            with self.assertRaises(HS.Unusable) as caught:
                HS.report([], [], document, self.read)
            self.assertEqual(caught.exception.reasons, reasons)


class Vectors(Base):
    """The shapes of tohum/29a's ``match`` vectors, through the command line."""

    def setUp(self) -> None:
        super().setUp()
        vec_case = dict(case("c1", 3, path="pkg/a.py", rule="F401"), tool="ruff", split="exit")
        self.one = self.file("one.json", [vec_case])
        self.two = self.file("two.json", [vec_case, dict(vec_case, case_id="c2", touched_paths=[
            {"path": "pkg/a.py", "hunks": [{"start": 3, "end": 4}]}])])
        hit = dict(finding("fp-f1", 3, path="pkg/a.py", rule="F401"), tool="ruff", snapshot_id="snap-1")
        self.hit = self.file("hit.json", [hit])
        self.other_line = self.file("other.json", [dict(finding("fp-f2", 7, path="pkg/a.py", rule="F401"), tool="ruff")])

    def test_the_three(self):
        self.assertEqual(self.command(self.hit, self.one), (0, '{"hits": 1}\n'))
        self.assertEqual(self.command(self.other_line, self.one), (0, '{"hits": 0}\n'))
        self.assertEqual(self.command(self.hit, self.two), (0, '{"hits": 1}\n'))

    def test_the_window_option(self):
        k3 = self.file("k3.json", [dict(case("c1", 2, class_level="K3"), property="p")])
        found = self.file("k3f.json", [dict(finding("x", 4), property="p", required_change=[{"file": "a", "op": "e"}])])
        self.assertEqual(self.command(found, k3), (0, '{"hits": 0}\n'))
        self.assertEqual(self.command(found, k3, "--window", "2"), (0, '{"hits": 1}\n'))

    def test_unusable(self):
        not_json = os.path.join(self.root, "bad.json")
        with open(not_json, "w") as fh:
            fh.write("[")
        snapshot = self.file("s.json", self.snapshot)
        for argv in ([], [self.hit], [self.hit, os.path.join(self.root, "absent.json")], [self.hit, not_json],
                     [self.hit, self.file("obj.json", {})], [self.file("obj2.json", {}), self.one],
                     [self.hit, self.file("mixed.json", [case("c1", 1), case("c2", 2, class_level="K1")])],
                     [self.hit, self.one, "--snapshot", snapshot], [self.hit, self.one, "--tree", self.tree],
                     [self.hit, self.one, "--alpha", "0.1"], [self.hit, self.one, "--min-groups", "1"],
                     [self.hit, self.one, "--window"], [self.hit, self.one, "--window", "x"],
                     [self.hit, self.one, "--window", "1", "--window", "2"], [self.hit, self.one, "--other", "1"],
                     [self.hit, self.one, "--snapshot", snapshot, "--tree", self.tree, "--alpha", "1"],
                     [self.hit, self.one, "--snapshot", snapshot, "--tree", self.tree, "--alpha", "0"],
                     [self.hit, self.one, "--snapshot", self.one, "--tree", self.tree],
                     [self.hit, self.one, "--snapshot", not_json, "--tree", self.tree]):
            with self.subTest(argv=argv[2:] or argv):
                code, text = self.command(*argv)
                self.assertEqual((code, json.loads(text)["ok"]), (2, False))


class Live(LY.YazBase):
    """``çek``'s assembly -> the ``kos`` job -> the ``yaz`` job: the scorer's output is on ``yaz``'s line."""

    def setUp(self) -> None:
        super().setUp()
        write_tree(self.src, {"pkg/a.js": TCA.A_JS, "pkg/b.js": TCA.B_JS})

    cek = TCA.LivePath.cek
    hand_over = TCA.LivePath.hand_over

    def yaz_after_kos(self) -> dict:
        self.hand_over(LK.J.run("kos", {"RUNNER_TEMP": self.temp}, runner=LK.RedAs()))
        self.control(LY.OPEN)
        self.github()
        return self.line(self.run_yaz())

    def test_the_cycle_s_cases_are_scored_on_yaz_s_line(self):
        self.cek()
        snapshot = P.read(self.pulled).snapshot
        yaz = self.yaz_after_kos()
        (built,) = yaz["cases"]["cases"]
        harness = yaz["harness"]
        # no organ's output is kept yet: the cycle has no finding, its one case is a miss
        self.assertEqual((harness["hits"], harness["counts"]["given"], harness["verdict_reason"]), (0, 0, "misses"))
        report = harness["report"]
        self.assertEqual((report["snapshot_id"], report["n"], report["n_groups"], report["recall"], report["recall_lb"],
                          report["census"], report["verdict"]),
                         (snapshot["snapshot_id"], 1, 1, "0.000000", None,
                          {"rules_total": 1, "rules_covered": 0, "misses": 1}, "FAIL"))
        self.assertEqual(harness["missed_rules"], [["eslint", "no-var"]])

        def read(path):
            return D._read_regular(self.src, path)

        self.assertEqual(harness, HS.report([], yaz["cases"]["cases"], snapshot, read))
        # the case's oracle finding, given an identity and the snapshot, is a hit on the same cases and document
        oracle = dict(yaz["cases"]["oracle"][built["case_id"]], fingerprint="fp", snapshot_id=snapshot["snapshot_id"])
        scored = HS.report([oracle], yaz["cases"]["cases"], snapshot, read)
        self.assertEqual((scored["hits"], scored["report"]["recall"], scored["refused"]), (1, "1.000000", []))

    def test_without_cases_the_report_is_unmeasurable(self):
        self.kos({"good": LY.candidate(TCA.TK.GOOD)})
        self.control(LY.OPEN)
        self.github()
        yaz = self.line(self.run_yaz())
        self.assertEqual(yaz["merge"], "good")
        self.assertEqual((yaz["harness"]["report"]["verdict"], yaz["harness"]["verdict_reason"],
                          yaz["harness"]["report"]["clean_findings"]), ("UNMEASURABLE", "no_cases", 0))

    def test_what_the_scorer_refuses_is_on_the_line(self):
        art = types.SimpleNamespace(snapshot={"schema": "other"}, policy={})
        self.assertEqual(J.yaz_harness(art, self.src, {"cases": []}),
                         {"reason": "harness_refused", "reasons": ["snapshot:document_invalid"]})

    def test_the_cycle_s_findings_are_none(self):
        self.assertEqual(J.FINDINGS, [])


if __name__ == "__main__":
    unittest.main()
