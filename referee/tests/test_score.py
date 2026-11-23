"""Tests 1, 6, 7, 12 and 28 (asama-0/09), P1 MF4: ``harness.score`` and ``harness.stats``, and ``harness`` on
``yaz``'s line (no report without a hunter run).

- test 1 (``Empty``): no finding against cases is recall 0 and a report, no error; no finding and no case too;
- test 6 (``Refs``): a reference outside the manifest, or to a file whose bytes are not the manifest's, is refused
  and reported, and so is each other reason of ``sift``; a refused finding hits nothing and is still counted in
  a clean run;
- test 7 (``Determinism``): the same input twice gives the same bytes (two processes with different hash seeds);
  the number of hits does not depend on the order of the findings or of the cases (``Match``: the largest
  matching, where taking cases greedily would give one hit fewer);
- test 12 (``Fingerprint``): the same finding observed twice in a run is counted once; the same finding on a
  shifted line is the same finding; the first row of a fingerprint in the run is the one scored and a later one
  is never read, whatever it says and also after a refused first; ``Runs`` (tohum/26q): the report reads one
  run's observation list: a row of another snapshot, a row of the register (``state``), a decision row, a row
  that is no object and what is no list make it ``Unusable``, no row is skipped; the fingerprint is scored as
  the row holds it;
- test 28 (``Statistics``): tohum/29a's tables through the command line, and ``x_eff`` and ``recall_lb`` through
  the report;
- ``Match`` and ``Vectors``: one finding takes one case, one case counts once; the shapes of tohum/29a's
  ``match`` vectors through the command line; the command's refusals;
- ``Report``: the fields, the census over the rule set the caller gives (none: no count and never ``PASS``),
  the verdicts in their order, the cases refused;
- ``Composed``: ``harness.score.params`` of a policy and ``cases.census.rules`` of a target kind are
  ``report``'s arguments;
- ``Live``: from ``çek`` through ``koş`` to ``yaz``'s line: ``harness`` is ``{reason: "no_hunter_run"}`` with
  a case and without (tohum/26q (6)).
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from fractions import Fraction

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cases import build as CB  # noqa: E402
from cases import census as CC  # noqa: E402
from findings import write as FW  # noqa: E402
from harness import params as HP  # noqa: E402
from harness import score as HS  # noqa: E402
from harness import stats as ST  # noqa: E402
from loop import job as J  # noqa: E402
from loop import pulled as P  # noqa: E402
from profile import derive as D  # noqa: E402
from profile_tree import write_tree  # noqa: E402
import test_cases as TCA  # noqa: E402
import test_findings_write as TFW  # noqa: E402
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


def fp(name: str) -> str:
    """The fingerprint ``observed`` gives the finding a test names ``name``."""
    return hashlib.sha256(name.encode()).hexdigest()


def observed(findings: list) -> list:
    """The findings as the rows of a run's observation list, in their order: each object with ``fp`` of its name
    as fingerprint; what is no object, or has no string under ``fingerprint``, as it is."""
    return [dict(found, fingerprint=fp(found["fingerprint"]))
            if isinstance(found, dict) and isinstance(found.get("fingerprint"), str) else found for found in findings]


# the census rule set of these tests (tohum/26q (10): the caller's; three rules, by hand), then one case of every
# rule of it and the finding that hits it: what a PASS needs
SET = [("eslint", "eqeqeq"), ("eslint", "no-var"), ("eslint", "prefer-const")]
FULL = [{"case_id": "r%d" % n, "class_level": "K0", "property": "lint", "provenance": "mutation",
         "touched_paths": [{"path": "pkg/a.js", "hunks": [{"start": n + 1, "end": n + 1}]}],
         "tool": tool, "rule_id": rule, "split": "dev", "group": "pkg"} for n, (tool, rule) in enumerate(SET)]


# tohum/29za: the toy's census rules as the page lists them, one case of each and the finding that hits it
TOY_RULES = ("dot-notation", "no-var", "object-shorthand", "operator-assignment", "prefer-const", "prefer-template", "yoda")
TOY = [("eslint", rule) for rule in TOY_RULES]
TOY_PLACES = [("pkg/a.js", n) for n in range(1, 6)] + [("pkg/b.js", 1), ("lib/c.js", 1)]      # lines of ``TREE``
TOY_FULL = [dict(FULL[0], case_id="t%d" % n, rule_id=rule,
                 touched_paths=[{"path": TOY_PLACES[n][0], "hunks": [{"start": TOY_PLACES[n][1], "end": TOY_PLACES[n][1]}]}])
            for n, rule in enumerate(TOY_RULES)]


class Base(unittest.TestCase):
    """A tree, its clean snapshot document, and ``report`` on them (the findings as a run's observation list,
    each given the document's id)."""

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
        """``report`` over ``SET`` unless the test gives a census (``None``: a target with no census vector)."""
        return HS.report(observed(self.stamped(findings)), cases, self.snapshot, self.read, **dict({"census": SET}, **kw))

    def full_hit(self) -> list:
        """The findings that hit ``FULL``, one each."""
        return [finding(c["case_id"], c["touched_paths"][0]["hunks"][0]["start"], rule=c["rule_id"], tool=c["tool"])
                for c in FULL]

    def registry(self, name: str, findings: list) -> str:
        """A file holding ``observed`` of the findings as one JSON list."""
        return self.file(name, observed(self.stamped(findings)))

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
        out = self.report([], [case("c1", 2), case("c2", 3)], alpha=TENTH)
        self.assertEqual(out["hits"], 0)
        self.assertEqual(out["refused"], [])
        self.assertEqual(out["counts"], {"given": 0, "distinct": 0, "reobserved": 0, "refused": 0})
        report = out["report"]
        self.assertEqual((report["n"], report["n_groups"], report["recall"], report["x_eff"], report["recall_lb"]),
                         (2, 1, "0.000000", "0.000000", "0.000000"))
        self.assertEqual(report["census"], {"rules_total": 3, "rules_covered": 0, "misses": 2})
        self.assertEqual((report["verdict"], out["verdict_reason"]), ("FAIL", "misses"))

    def test_no_finding_and_no_case(self):
        out = self.report([], [], alpha=TENTH)
        report = out["report"]
        self.assertEqual((report["n"], report["recall"], report["x_eff"], report["recall_lb"], report["census"]),
                         (0, None, None, None, None))
        self.assertEqual((report["clean_findings"], report["verdict"], out["verdict_reason"]),
                         (0, "UNMEASURABLE", "no_cases"))

    def test_the_command_on_an_empty_list(self):
        empty, cases = self.file("f.json", []), self.file("c.json", [case("c1", 2)])
        self.assertEqual(self.command(empty, cases), (0, '{"hits": 0}\n'))
        code, text = self.command(self.registry("f.jsonl", []), cases, "--snapshot", self.file("s.json", self.snapshot), "--tree", self.tree)
        self.assertEqual((code, json.loads(text)["report"]["recall"]), (0, "0.000000"))


class Refs(Base):
    """Test 6."""

    def refused(self, findings: list, cases=None) -> list:
        out = self.report(findings, [case("c1", 2)] if cases is None else cases)
        self.assertEqual(out["hits"], 0)
        return out["refused"]

    def test_the_control_a_reference_of_the_manifest_hits(self):
        out = self.report([finding("x", 2)], [case("c1", 2)])
        self.assertEqual((out["hits"], out["refused"], out["matched"]), (1, [], {"c1": fp("x")}))

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

    def test_a_line_the_file_does_not_have(self):
        # pkg/a.js has five lines; lib/c.js two, the last without a newline
        self.assertEqual(self.refused([finding("x", 6)], [case("c1", 6)]),
                         [{"index": 0, "reasons": ["ref_line_missing"]}])
        self.assertEqual(self.report([finding("x", 5)], [case("c1", 5)])["hits"], 1)
        self.assertEqual(self.report([finding("x", 2, path="lib/c.js")], [case("c1", 2, path="lib/c.js")])["hits"], 1)
        self.assertEqual(self.refused([finding("x", 3, path="lib/c.js")], [case("c1", 3, path="lib/c.js")]),
                         [{"index": 0, "reasons": ["ref_line_missing"]}])

    def test_every_reason_in_its_order_each_once(self):
        bad = finding("x", 9, 9)
        bad["evidence_refs"] += [{"path": "nowhere.js", "line_start": 1, "line_end": 1}] * 2
        self.assertEqual(self.refused([bad]), [{"index": 0, "reasons": ["ref_outside_manifest", "ref_line_missing"]}])
        with open(os.path.join(self.tree, "pkg/b.js"), "ab") as fh:
            fh.write(b"var w = 1;\n")
        bad["evidence_refs"].insert(0, {"path": "pkg/b.js", "line_start": 1, "line_end": 1})
        self.assertEqual(self.refused([bad]), [{"index": 0, "reasons": ["ref_outside_manifest", "ref_hash_mismatch",
                                                                        "ref_line_missing"]}])

    def test_what_is_no_finding(self):
        shapes = [None, "x", {}, finding(""), finding(""), dict(finding("x", 2), fingerprint=7), finding("a"),
                  dict(finding("b", 2), evidence_refs={}), dict(finding("c", 2), evidence_refs=[None]),
                  dict(finding("d", 2), evidence_refs=[{"path": 1, "line_start": 2, "line_end": 2}]),
                  dict(finding("e", 2), evidence_refs=[{"path": "pkg/a.js", "line_start": 0, "line_end": 2}]),
                  dict(finding("f", 2), evidence_refs=[{"path": "pkg/a.js", "line_start": 3, "line_end": 2}]),
                  dict(finding("g", 2), evidence_refs=[{"path": "pkg/a.js", "line_start": True, "line_end": 2}]),
                  dict(finding("h", 2), evidence_refs=[{"path": "pkg/a.js", "line_start": 2, "line_end": 2.0}])]
        for snapshot, given in ((None, shapes), (self.snapshot, self.stamped(shapes))):
            self.assertEqual(HS.sift(given, snapshot, self.read),
                             ([], [{"index": i, "reasons": ["finding_invalid"]} for i in range(len(shapes))], 0))
        # one that carries a fingerprint is its first observation: the shaped finding after it is not read
        accepted, refused, reobserved = HS.sift([dict(finding("x", 2), evidence_refs=[None]), finding("x", 2)])
        self.assertEqual((accepted, [r["index"] for r in refused], reobserved), ([], [0], 1))

    def test_the_index_is_the_place_in_the_list_and_the_others_are_scored(self):
        out = self.report([finding("x", 2, path="nowhere.js"), finding("y", 2), finding("z", 9)], [case("c1", 2)])
        self.assertEqual((out["hits"], out["matched"]), (1, {"c1": fp("y")}))
        self.assertEqual(out["refused"], [{"index": 0, "reasons": ["ref_outside_manifest"]},
                                          {"index": 2, "reasons": ["ref_line_missing"]}])
        self.assertEqual(out["counts"], {"given": 3, "distinct": 1, "reobserved": 0, "refused": 2})
        # the index is the row's place in the list: a re-observation before it counts in
        out = self.report([finding("y", 2), finding("y", 3), finding("x", 2, path="nowhere.js")], [case("c1", 2)])
        self.assertEqual(out["refused"], [{"index": 2, "reasons": ["ref_outside_manifest"]}])

    def test_a_refused_finding_is_counted_in_a_clean_run(self):
        mixed = [finding("x", 2, path="nowhere.js"), finding("y", 2), finding("z", 9)]
        out = self.report(mixed, [])
        self.assertEqual(out["report"]["clean_findings"], 3)
        # each identity once: a later row of a fingerprint is no finding more, the refused one's neither
        again = self.report(mixed + [finding("x", 2), finding("y", 3)], [])
        self.assertEqual((again["report"]["clean_findings"], again["counts"]["reobserved"]), (3, 2))

    def test_the_command_reports_them(self):
        cases = self.file("c.json", [case("c1", 2, path="nowhere.js")])
        findings = self.file("f.json", self.stamped([finding("x", 2, path="nowhere.js")]))
        registry = self.registry("f.jsonl", [finding("x", 2, path="nowhere.js")])
        code, text = self.command(registry, cases, "--snapshot", self.file("s.json", self.snapshot), "--tree", self.tree)
        self.assertEqual((code, json.loads(text)["refused"], json.loads(text)["hits"]),
                         (0, [{"index": 0, "reasons": ["ref_outside_manifest"]}], 0))
        # without a snapshot the references are not judged, the shape is
        self.assertEqual(self.command(findings, cases), (0, '{"hits": 1}\n'))
        self.assertEqual(self.command(self.file("g.json", [None]), cases),
                         (0, '{"hits": 0, "refused": [{"index": 0, "reasons": ["finding_invalid"]}]}\n'))


# two cases of one rule, c1 on lines 2-3 and c2 on line 2; wide (line 2) hits both, narrow (line 3) only c1: the
# largest matching is two (K0 reads the primary reference alone, so a finding hits two cases where hunks overlap)
WIDE, NARROW = finding("wide", 2), finding("narrow", 3)
TWO = [case("c1", 2, end=3), case("c2", 2)]


def span(fingerprint: str, *spans: tuple, **over) -> dict:
    """``finding`` whose references are the ``(line_start, line_end)`` pairs."""
    made = finding(fingerprint, *[first for first, _ in spans], **over)
    for ref, (_, last) in zip(made["evidence_refs"], spans):
        ref["line_end"] = last
    return made


class RefLength(Base):
    """``ref_over_max_lines``: the primary reference, ``evidence_refs[0]``, spans more lines than ``ref_max_lines``."""

    def test_the_bound_is_the_number_of_lines_spanned(self):
        cases = [case("c1", 1, end=5)]
        at_bound = self.report([span("x", (2, 4))], cases, ref_max_lines=3)
        self.assertEqual((at_bound["hits"], at_bound["refused"]), (1, []))
        over = self.report([span("x", (2, 5))], cases, ref_max_lines=3)
        self.assertEqual((over["hits"], over["refused"]), (0, [{"index": 0, "reasons": ["ref_over_max_lines"]}]))
        self.assertEqual(over["counts"], {"given": 1, "distinct": 0, "reobserved": 0, "refused": 1})
        one_line = self.report([span("x", (2, 2))], cases, ref_max_lines=1)
        self.assertEqual((one_line["hits"], one_line["refused"]), (1, []))

    def test_only_the_first_reference_is_bounded(self):
        cases = [case("c1", 1, end=5)]
        refused = [{"index": 0, "reasons": ["ref_over_max_lines"]}]
        for spans, want in ((((2, 2), (1, 5)), []), (((2, 3), (1, 5), (1, 4)), []), (((2, 3),), []),
                            (((1, 5), (2, 2)), refused), (((1, 3), (2, 2), (2, 3)), refused),
                            (((1, 3), (2, 5)), refused), (((2, 4), (2, 3)), refused)):
            with self.subTest(spans=spans):
                self.assertEqual(self.report([span("x", *spans)], cases, ref_max_lines=2)["refused"], want)
                self.assertEqual(HS.sift([span("x", *spans)], ref_max_lines=2)[1], want)

    def test_without_the_bound_no_length_is_judged(self):
        out = self.report([span("x", (2, 5))], [case("c1", 1, end=5)])
        self.assertEqual((out["hits"], out["refused"]), (1, []))
        self.assertEqual(HS.sift([span("x", (1, 500))])[1], [])

    def test_its_place_among_the_reasons(self):
        long_missing = span("y", (1, 9), path="pkg/none.js")
        again = span("x", (1, 5))     # a re-observation is not bounded: nothing of it is read
        out = self.report([finding("x", 2), again, long_missing], [case("c1", 1, end=5)], ref_max_lines=2)
        self.assertEqual(out["refused"], [{"index": 2, "reasons": ["ref_over_max_lines", "ref_outside_manifest"]}])

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
        registry = self.registry("f.jsonl", [span("x", (2, 4))])
        refused = [{"index": 0, "reasons": ["ref_over_max_lines"]}]
        self.assertEqual(self.command(found, cases, "--ref-max-lines", "3"), (0, '{"hits": 1}\n'))
        code, text = self.command(found, cases, "--ref-max-lines", "2")
        self.assertEqual((code, json.loads(text)), (0, {"hits": 0, "refused": refused}))
        snapshot = self.file("s.json", self.snapshot)
        code, text = self.command(registry, cases, "--snapshot", snapshot, "--tree", self.tree, "--ref-max-lines", "2")
        self.assertEqual((code, json.loads(text)["refused"]), (0, refused))
        code, text = self.command(registry, cases, "--snapshot", snapshot, "--tree", self.tree, "--ref-max-lines", "3")
        self.assertEqual((code, json.loads(text)["hits"]), (0, 1))
        for bad in ("0", "x", "-1", "1.5"):
            code, text = self.command(found, cases, "--ref-max-lines", bad)
            self.assertEqual((code, json.loads(text)["ok"]), (2, False), bad)


class Composed(Base):
    """``harness.score.params`` of a policy and ``cases.census.rules`` of a target kind as ``report``'s arguments
    (no job composes them today: ``Live``)."""

    K3 = {"class_level": "K3", "property": "p"}

    def harness(self, policy, findings: list, cases: list, kind: str = "toy") -> dict:
        return HS.report(observed(self.stamped(findings)), cases, self.snapshot, self.read, census=CC.rules(kind),
                         **HS.params(policy))

    def policy(self, level="0.900000", **params) -> dict:
        params = dict({"match_window_lines": 1, "evidence_ref_max_lines": 30}, **params)
        return {"constitutional": {"confidence_level": level, "stage_params": params}}

    def toy_hit(self) -> tuple[list, list]:
        """A case of each rule of the toy's census in two groups, and the findings that hit them."""
        cases = [dict(TOY_FULL[0], group="lib")] + TOY_FULL[1:]
        return cases, [finding(c["case_id"], c["touched_paths"][0]["hunks"][0]["start"], rule=c["rule_id"],
                               path=c["touched_paths"][0]["path"]) for c in cases]

    def test_the_census_is_the_target_kinds(self):
        cases, findings = self.toy_hit()
        toy = self.harness(self.policy(), findings, cases)
        self.assertEqual((toy["report"]["census"], toy["report"]["verdict"], toy["uncased_rules"], toy["outside_rules"]),
                         ({"rules_total": 7, "rules_covered": 7, "misses": 0}, "PASS", [], []))
        # a case of ``eqeqeq``, which the library makes and the toy's set does not hold, is named and not counted
        more = self.harness(self.policy(), findings + self.full_hit()[:1], cases + [FULL[0]])
        self.assertEqual((more["report"]["census"], more["outside_rules"], more["report"]["n"]),
                         ({"rules_total": 7, "rules_covered": 7, "misses": 0}, [["eslint", "eqeqeq"]], 8))
        fewer = self.harness(self.policy(), findings, cases[1:])
        self.assertEqual((fewer["report"]["verdict"], fewer["verdict_reason"], fewer["uncased_rules"]),
                         ("UNMEASURABLE", "rule_without_case", [["eslint", "dot-notation"]]))
        # a copy has no census vector (tohum/26q (10)): the same cases and findings, no count and no PASS
        for kind in ("copy", "other", None):
            copy = self.harness(self.policy(), findings, cases, kind=kind)
            self.assertEqual((copy["hits"], copy["report"]["census"], copy["report"]["verdict"], copy["verdict_reason"]),
                             (7, None, "UNMEASURABLE", "census_vector_absent"), kind)
            self.assertEqual(self.harness(self.policy(), findings[1:], cases, kind=kind)["report"]["verdict"], "FAIL")

    def test_each_value_reaches_the_report(self):
        cases, findings = self.toy_hit()
        got = self.harness(self.policy(), findings, cases)
        self.assertEqual(got, self.report(findings, cases, alpha=TENTH, window=1, ref_max_lines=30, census=TOY))
        self.assertEqual((got["report"]["recall_lb"], got["report"]["verdict"]),
                         (ST.fixed6(ST.cp_lower(Fraction(2), 2, TENTH)), "PASS"))
        other = self.harness(self.policy(level="0.500000"), findings, cases)
        self.assertEqual(other["report"]["recall_lb"], ST.fixed6(ST.cp_lower(Fraction(2), 2, Fraction(1, 2))))
        self.assertNotEqual(other["report"]["recall_lb"], got["report"]["recall_lb"])

    def test_the_group_floor_of_the_policy_changes_nothing_of_the_dev_report(self):
        cases, findings = self.toy_hit()
        plain = self.harness(self.policy(), findings, cases)
        for floor in (1, 2, 3, 40, 10 ** 6):     # tohum/26h: under, at and over G; the exit sample's, not this report's
            with self.subTest(floor=floor):
                self.assertEqual(self.harness(self.policy(census_min_groups=floor), findings, cases), plain)
        self.assertEqual((plain["report"]["n_groups"], plain["report"]["verdict"], plain["verdict_reason"]),
                         (2, "PASS", None))

    def test_the_window_and_the_reference_bound(self):
        cases = [dict(case("c1", 2), **self.K3)]
        near = dict(finding("x", 4), property="p", required_change=[{"file": "a", "op": "other"}])
        self.assertEqual(self.harness(self.policy(match_window_lines=1), [near], cases)["hits"], 0)
        self.assertEqual(self.harness(self.policy(match_window_lines=2), [near], cases)["hits"], 1)
        long = [span("x", (2, 4))]
        self.assertEqual(self.harness(self.policy(evidence_ref_max_lines=3), long, [case("c1", 1, end=5)])["refused"], [])
        self.assertEqual(self.harness(self.policy(evidence_ref_max_lines=2), long, [case("c1", 1, end=5)])["refused"],
                         [{"index": 0, "reasons": ["ref_over_max_lines"]}])
        second = [span("x", (2, 3), (1, 5))]     # the policy's bound is on the first reference alone
        self.assertEqual(self.harness(self.policy(evidence_ref_max_lines=2), second, [case("c1", 1, end=5)])["refused"], [])

    def test_a_value_elsewhere_in_the_policy_is_not_read(self):
        policy = self.policy()
        policy.update({"confidence_level": "0.500000", "stage_params": {"match_window_lines": 9, "evidence_ref_max_lines": 1},
                       "performance": self.policy(level="0.500000", match_window_lines=9)["constitutional"]})
        cases, findings = [case("c1", 2)], [finding("x", 2)]
        self.assertEqual(self.harness(policy, findings, cases),
                         self.report(findings, cases, alpha=TENTH, window=1, ref_max_lines=30, census=TOY))
        del policy["constitutional"]["confidence_level"]     # at the root and in another section only: not that key
        del policy["constitutional"]["stage_params"]["match_window_lines"]
        with self.assertRaises(HP.Invalid) as ctx:
            self.harness(policy, findings, cases)
        self.assertEqual(ctx.exception.reasons, ["policy_invalid:constitutional.confidence_level",
                                                 "policy_invalid:constitutional.stage_params.match_window_lines"])

    def test_a_policy_missing_or_off_a_value_is_no_report(self):
        absent = self.policy()
        del absent["constitutional"]["stage_params"]["evidence_ref_max_lines"]
        for policy, reasons in ((self.policy(level=0.9, match_window_lines=0),
                                 ["policy_invalid:constitutional.confidence_level",
                                  "policy_invalid:constitutional.stage_params.match_window_lines"]),
                                (absent, ["policy_invalid:constitutional.stage_params.evidence_ref_max_lines"]),
                                ({}, ["policy_invalid:constitutional.confidence_level",
                                      "policy_invalid:constitutional.stage_params.match_window_lines",
                                      "policy_invalid:constitutional.stage_params.evidence_ref_max_lines"])):
            with self.subTest(policy=policy), self.assertRaises(HP.Invalid) as ctx:
                self.harness(policy, [], [case("c1", 2)])
            self.assertEqual(ctx.exception.reasons, reasons)


class Match(Base):
    def test_a_finding_takes_one_case(self):
        self.assertEqual(self.report([WIDE], TWO)["hits"], 1)
        # which of the two it takes is the first by case_id, in either order of the list
        self.assertEqual([self.report([WIDE], cases)["matched"] for cases in (TWO, TWO[::-1])], [{"c1": fp("wide")}] * 2)
        self.assertEqual(self.report([finding("x", 3)], [case("c1", 3), case("c2", 3, end=4)])["hits"], 1)

    def test_a_case_counts_once(self):
        self.assertEqual(self.report([finding("x", 2), finding("y", 2)], [case("c1", 2)])["hits"], 1)

    def test_the_largest_matching_in_any_order(self):
        for findings in ([WIDE, NARROW], [NARROW, WIDE]):
            for cases in (TWO, TWO[::-1]):
                out = self.report(findings, cases)
                self.assertEqual((out["hits"], out["matched"]), (2, {"c1": fp("narrow"), "c2": fp("wide")}))

    def test_a_chain_of_three(self):
        # a: c1 c2, b: c2 c3, c: c1 only, given so that a and b sit on c1 and c2 before c comes
        cases = [case("c1", 1, end=2), case("c2", 2, end=3), case("c3", 3)]
        out = self.report([finding("a", 2), finding("b", 3), finding("c", 1)], cases)
        self.assertEqual(out["matched"], {"c1": fp("c"), "c2": fp("a"), "c3": fp("b")})

    def test_the_hit_rule_is_cases_builds(self):
        self.assertEqual(self.report([finding("x", 2, rule="no-eval")], [case("c1", 2)])["hits"], 0)
        self.assertEqual(self.report([finding("x", 3)], [case("c1", 2)])["hits"], 0)
        # K3: the window is the caller's
        k3 = dict(case("c1", 2, class_level="K3"), property="p")
        found = dict(finding("x", 4), property="p", required_change=[{"file": "pkg/a.js", "op": "other"}])
        self.assertEqual(self.report([found], [k3])["hits"], 0)
        self.assertEqual(self.report([found], [k3], window=2)["hits"], 1)
        self.assertEqual(self.report([found], [k3], window=1)["hits"], 0)


class Determinism(Base):
    """Test 7."""

    def test_the_same_input_twice_is_the_same_bytes(self):
        run = [WIDE, NARROW, finding("z", 9), finding("wide", 4)]
        findings, listed = self.registry("f.jsonl", run), self.file("f.json", run + [None])
        cases = self.file("c.json", TWO + [case("c3", 1, path="pkg/b.js", rule="no-eval", group="other")])
        plain = (findings, cases, "--snapshot", self.file("s.json", self.snapshot), "--tree", self.tree,
                 "--alpha", "0.10")
        args = plain + ("--census", self.file("r.json", SET))
        first, second = self.command(*args, seed="1"), self.command(*args, seed="2")
        self.assertEqual(first, second)
        self.assertEqual(first[0], 0)
        out = json.loads(first[1])
        self.assertEqual((out["hits"], out["report"]["recall"], out["missed_rules"]),
                         (2, "0.666667", [["eslint", "no-eval"]]))
        self.assertEqual((out["counts"], out["uncased_rules"], out["outside_rules"], out["report"]["census"]),
                         ({"given": 4, "distinct": 2, "reobserved": 1, "refused": 1},
                          [["eslint", "eqeqeq"], ["eslint", "prefer-const"]], [["eslint", "no-eval"]],
                          {"rules_total": 3, "rules_covered": 1, "misses": 1}))
        # without --census the report has no count; the set is read as the list the file holds
        bare = json.loads(self.command(*plain)[1])
        self.assertEqual((bare["report"]["census"], bare["uncased_rules"], bare["outside_rules"], bare["verdict_reason"],
                          bare["hits"]), (None, None, None, "misses", 2))
        for name, value in (("no.json", {"eslint": "no-var"}), ("pair.json", [["eslint"]]), ("none.json", [])):
            code, text = self.command(*plain, "--census", self.file(name, value))
            self.assertEqual((code, json.loads(text)["ok"]), (2, False), name)
        self.assertEqual(self.command(listed, cases)[0], 0)      # the first form takes no census: it gives no report
        self.assertEqual(self.command(listed, cases, "--census", self.file("r.json", SET))[0], 2)
        self.assertEqual(self.command(listed, cases, seed="1"), self.command(listed, cases, seed="2"))
        self.assertEqual(json.loads(self.command(listed, cases)[1])["hits"], 2)

    def test_report_twice_and_its_arguments_unchanged(self):
        findings, cases = observed(self.stamped([WIDE, NARROW, finding("wide", 4)])), list(TWO)
        kept = copy.deepcopy((findings, cases, self.snapshot))
        first = HS.report(findings, cases, self.snapshot, self.read, alpha=TENTH)
        self.assertEqual(first, HS.report(findings, cases, self.snapshot, self.read, alpha=TENTH))
        self.assertEqual((findings, cases, self.snapshot), kept)

    def test_one_byte_of_the_input_changes_the_report(self):
        self.assertNotEqual(self.report([finding("x", 2)], [case("c1", 2)]),
                            self.report([finding("x", 3)], [case("c1", 2)]))


class Fingerprint(Base):
    """Test 12."""

    def test_the_same_finding_observed_twice_is_one(self):
        run = [finding("x", 2), finding("y", 3)]
        once, twice = self.report(run, []), self.report(run + copy.deepcopy(run), [])
        self.assertEqual(once["report"]["clean_findings"], 2)
        self.assertEqual(twice["report"]["clean_findings"], 2)
        self.assertEqual(twice["counts"], {"given": 4, "distinct": 2, "reobserved": 2, "refused": 0})
        # against cases too: the second observations take no second case
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
        self.assertEqual(self.report(shifted, TWO)["matched"], {"c1": fp("x")})
        # the first row in the file's order is the one scored: turned round, line 4 is, and it hits neither case
        self.assertEqual(self.report(shifted[::-1], TWO)["hits"], 0)

    def test_a_later_row_of_a_fingerprint_is_never_read(self):
        """tohum/26m "Puanlama" 2: neither a hit nor a refusal nor a finding more, whatever the row says."""
        cases = [case("c1", 2), case("c2", 1, path="pkg/b.js"), case("c3", 3, rule="no-eval")]
        for index, other in enumerate([finding("x", 1, path="pkg/b.js"), finding("x", 3, rule="no-eval"),
                                       dict(finding("x", 2), property="other"), dict(finding("x", 2), symbol="f"),
                                       dict(finding("x", 2), tool="ruff"), finding("x", 2, path="nowhere.js"),
                                       finding("x", 99), dict(finding("x", 2), evidence_refs=[]), span("x", (1, 5))]):
            with self.subTest(index=index):
                out = self.report([finding("x", 2), other], cases, ref_max_lines=2)
                self.assertEqual((out["hits"], out["matched"], out["refused"]), (1, {"c1": fp("x")}, []))
                self.assertEqual(out["counts"], {"given": 2, "distinct": 1, "reobserved": 1, "refused": 0})
                self.assertEqual(self.report([finding("x", 2), other], [])["report"]["clean_findings"], 1)
                # the control: under its own fingerprint the same row is read
                apart = self.report([finding("x", 2), dict(other, fingerprint="y")], cases, ref_max_lines=2)
                self.assertEqual((apart["counts"]["reobserved"], apart["counts"]["distinct"] + apart["counts"]["refused"]),
                                 (0, 2))

    def test_the_first_observation_is_the_one_scored_also_when_it_is_refused(self):
        out = self.report([finding("x", 2, path="nowhere.js"), finding("x", 2)], [case("c1", 2)])
        self.assertEqual((out["hits"], out["refused"]), (0, [{"index": 0, "reasons": ["ref_outside_manifest"]}]))
        self.assertEqual(out["counts"], {"given": 2, "distinct": 0, "reobserved": 1, "refused": 1})
        turned = self.report([finding("x", 2), finding("x", 2, path="nowhere.js")], [case("c1", 2)])
        self.assertEqual((turned["hits"], turned["refused"]), (1, []))
        self.assertEqual(turned["counts"], {"given": 2, "distinct": 1, "reobserved": 1, "refused": 0})

    def test_a_fingerprint_whose_first_row_has_no_reference_is_refused_once(self):
        bare = dict(finding("x", 2), evidence_refs=[])
        out = self.report([bare, dict(bare), finding("x", 2), finding("y", 3)], [case("c1", 2)])
        self.assertEqual((out["hits"], out["refused"]), (0, [{"index": 0, "reasons": ["finding_invalid"]}]))
        self.assertEqual(out["counts"], {"given": 4, "distinct": 1, "reobserved": 2, "refused": 1})
        self.assertEqual(HS.sift([finding("x", 2), bare, "x", {"fingerprint": ""}])[1:],
                         ([{"index": 2, "reasons": ["finding_invalid"]}, {"index": 3, "reasons": ["finding_invalid"]}], 1))

    def test_without_a_snapshot_too(self):
        found = HS.sift([finding("x", 2), finding("x", 3), finding("x", 1, path="pkg/b.js")])
        self.assertEqual(found, ([finding("x", 2)], [], 2))
        found = HS.sift([span("x", (1, 5)), finding("x", 3), finding("y", 3)], ref_max_lines=2)
        self.assertEqual(found, ([finding("y", 3)], [{"index": 0, "reasons": ["ref_over_max_lines"]}], 1))


OLD, OLDER = "0" * 64, "1" * 64


class Runs(Base):
    """Test 12 and tohum/26q "Avcı koşusu ve gözlem listesi" (2), (3): the report reads one run's observation
    list; a list holding a row that is not an observation of the document's snapshot is unusable, and no row
    is skipped."""

    def unusable(self, rows, cases=None) -> list:
        with self.assertRaises(HS.Unusable) as caught:
            HS.report(rows, [case("c1", 2)] if cases is None else cases, self.snapshot, self.read)
        return caught.exception.reasons

    def test_a_row_of_another_snapshot_makes_the_list_unusable_wherever_it_stands(self):
        mine, cases = finding("x", 2), [case("c1", 2)]
        self.assertEqual(self.report([mine], cases)["hits"], 1)
        earlier = [finding("x", 2, snapshot_id=OLDER), finding("y", 3, snapshot_id=OLD)]
        for name, rows, reasons in (
                ("before", earlier + [mine], [0, 1]), ("after", [mine] + earlier, [1, 2]),
                ("around", earlier[:1] + [mine] + earlier[1:], [0, 2]), ("alone", earlier[:1], [0]),
                ("a later observation of a fingerprint", [mine, finding("x", 3, snapshot_id=OLD)], [1])):
            with self.subTest(name):
                self.assertEqual(self.unusable(observed(self.stamped(rows)), cases),
                                 ["observation_other_snapshot:%d" % index for index in reasons])
                self.assertEqual(self.unusable(observed(self.stamped(rows)), []),
                                 ["observation_other_snapshot:%d" % index for index in reasons])

    def test_whatever_the_other_snapshot_s_row_says(self):
        for index, other in enumerate([finding("x", 2), finding("y", 3), finding("x", 2, path="nowhere.js"),
                                       finding("x", 99), dict(finding("x", 2), evidence_refs=[]), span("x", (1, 5)), {}]):
            with self.subTest(index=index):
                for other_id in (OLD, None, 7, self.snapshot["snapshot_id"].upper()):
                    rows = observed(self.stamped([finding("x", 2)])) + [dict(other, snapshot_id=other_id)]
                    self.assertEqual(self.unusable(rows), ["observation_other_snapshot:1"])
                absent = {k: v for k, v in other.items() if k != "snapshot_id"}       # a row with no id is of no run
                self.assertEqual(self.unusable([absent]), ["observation_other_snapshot:0"])
        # the control: the same rows on the document's snapshot are read
        self.assertEqual(self.report([finding("y", 3), finding("x", 2)], [case("c1", 2), case("c2", 3)])["hits"], 2)

    def test_the_register_is_no_run(self):
        """26q (3): neither ``findings.jsonl`` nor its rows; (2): the list carries no state and no decision row."""
        made = FW.observe(b"", b"", [TFW.lint(2, snapshot_id=self.snapshot["snapshot_id"])], "hunter-1", self.read)
        rows = TFW.stored(made.content)
        self.assertEqual(([row["state"] for row in rows], rows[0]["snapshot_id"]), (["open"], self.snapshot["snapshot_id"]))
        self.assertEqual(self.unusable(rows), ["observation_state_row:0"])
        for name, data in (("the file's bytes", made.content), ("no row", b""), ("its text", made.content.decode()),
                           ("nothing", None), ("an object", {"rows": []}), ("a tuple", tuple(rows))):
            with self.subTest(name):
                self.assertEqual(self.unusable(data), ["observations_invalid"])
        # the same observation without the register's state is read, under the fingerprint the row holds
        plain = {k: v for k, v in rows[0].items() if k != "state"}
        self.assertEqual(HS.report([plain], [case("c1", 2)], self.snapshot, self.read)["matched"],
                         {"c1": rows[0]["fingerprint"]})
        for state in ("open", "fixed", None, ""):      # the key tells the row, whatever its value
            self.assertEqual(self.unusable([dict(plain, state=state)]), ["observation_state_row:0"])
        for decision in ("merge", "reject", None):
            self.assertEqual(self.unusable([dict(plain, decision=decision)]), ["observation_decision_row:0"])
        self.assertEqual(self.unusable([dict(plain, decision="merge", state="fixed")]), ["observation_state_row:0"])

    def test_every_row_s_reason_in_the_list_s_order(self):
        good = observed(self.stamped([finding("x", 2)]))[0]
        rows = [good, None, dict(good, state="open"), "x", dict(good, snapshot_id=OLD), dict(good, decision="merge"),
                dict(good, state="open", snapshot_id=OLD), dict(good, decision="reject", snapshot_id=OLD), [good], good]
        self.assertEqual(self.unusable(rows), [
            "observation_invalid:1", "observation_state_row:2", "observation_invalid:3", "observation_other_snapshot:4",
            "observation_decision_row:5", "observation_state_row:6", "observation_decision_row:7",
            "observation_invalid:8"])
        self.assertEqual(HS.report([good, good], [case("c1", 2)], self.snapshot, self.read)["counts"],
                         {"given": 2, "distinct": 1, "reobserved": 1, "refused": 0})

    def test_the_counts_add_up(self):
        rows = [finding("x", 2), finding("x", 3), finding("y", 9), finding("z", 3), finding("y", 2)]
        counts = self.report(rows, [case("c1", 2)])["counts"]
        self.assertEqual(counts, {"given": 5, "distinct": 2, "reobserved": 2, "refused": 1})
        self.assertEqual(counts["given"], sum(v for k, v in counts.items() if k != "given"))

    def test_sift_reads_no_snapshot_id(self):
        # the whole list is the run, with a document and without, whatever ids its findings carry
        rows = [finding("x", 2, snapshot_id=OLD), finding("x", 3, snapshot_id=OLDER), finding("y", 3)]
        for found in (HS.sift(rows), HS.sift(rows, self.snapshot, self.read)):
            self.assertEqual(([f["fingerprint"] for f in found[0]], found[1:]), (["x", "y"], ([], 1)))

    def test_the_fingerprint_is_scored_as_the_row_holds_it(self):
        """tohum/26m "Puanlama" 1. The rows here carry what ``findings.write.fingerprint`` gives on the tree; that
        a row's fingerprint is that function's is not checked by the scorer (stated out of scope there)."""
        proposals = [TFW.lint(line, path, snapshot_id=self.snapshot["snapshot_id"])
                     for line, path in ((2, "pkg/a.js"), (3, "pkg/a.js"), (1, "pkg/b.js"))]
        prints = [FW.fingerprint(p, self.read) for p in proposals]
        self.assertEqual(len(set(prints)), 3)
        rows = [dict(p, fingerprint=print_) for p, print_ in zip(proposals, prints)]
        out = HS.report(rows, [case("c1", 2), case("c2", 1, path="pkg/b.js")], self.snapshot, self.read)
        self.assertEqual((out["hits"], out["matched"], out["refused"]), (2, {"c1": prints[0], "c2": prints[2]}, []))
        self.assertEqual(out["counts"], {"given": 3, "distinct": 3, "reobserved": 0, "refused": 0})
        # of the writer's form and not the function's on this tree: scored as held (deriving it again is deferred)
        other = HS.report([dict(rows[0], fingerprint=fp("other"))], [case("c1", 2)], self.snapshot, self.read)
        self.assertEqual(other["matched"], {"c1": fp("other")})

    def test_a_fingerprint_no_writer_makes_is_no_observation(self):
        """tohum/26q (8): only the two-file command takes a fingerprint as given (``fp-f1``, a label)."""
        row = observed(self.stamped([finding("x", 2)]))[0]
        self.assertEqual(row["fingerprint"], fp("x"))
        for label in ("fp-f1", fp("y").upper(), fp("y")[:63], fp("y") + "0", fp("y") + "\n", " " + fp("y"), ""):
            with self.subTest(label=label):
                self.assertEqual(self.unusable([row, dict(row, fingerprint=label)]), ["observation_fingerprint:1"])
                self.assertEqual(self.unusable([row, dict(row, fingerprint=label)], []), ["observation_fingerprint:1"])
        # another snapshot's row is named as that, and a row with no fingerprint string stays sift's to refuse
        self.assertEqual(self.unusable([dict(row, fingerprint="fp-f1", snapshot_id=OLD)]), ["observation_other_snapshot:0"])
        absent = HS.report([row, dict(row, fingerprint=None)], [case("c1", 2)], self.snapshot, self.read)
        self.assertEqual((absent["hits"], absent["refused"]), (1, [{"index": 1, "reasons": ["finding_invalid"]}]))
        # the two-file form still takes the label (the match vectors' findings)
        accepted, refused, _ = HS.sift([dict(row, fingerprint="fp-f1")])
        self.assertEqual(([f["fingerprint"] for f in accepted], refused), (["fp-f1"], []))
        listed, cases = self.file("l.json", [dict(row, fingerprint="fp-f1")]), self.file("c.json", [case("c1", 2)])
        self.assertEqual(self.command(listed, cases), (0, '{"hits": 1}\n'))
        code, text = self.command(listed, cases, "--snapshot", self.file("s.json", self.snapshot), "--tree", self.tree)
        self.assertEqual((code, json.loads(text)["error"]), (2, "unusable input: observation_fingerprint:0"))

    def test_the_command_reads_a_list_in_its_second_form(self):
        cases, snapshot = self.file("c.json", [case("c1", 2)]), self.file("s.json", self.snapshot)
        listed = self.registry("f.json", [finding("x", 2)])
        code, text = self.command(listed, cases, "--snapshot", snapshot, "--tree", self.tree)
        self.assertEqual((code, json.loads(text)["matched"]), (0, {"c1": fp("x")}))
        made = FW.observe(b"", b"", [TFW.lint(2, snapshot_id=self.snapshot["snapshot_id"])], "hunter-1", self.read)
        register = os.path.join(self.root, "findings.jsonl")
        with open(register, "wb") as fh:
            fh.write(made.content + made.content)      # two lines: no JSON value
        for name, path, error in (
                ("the register's file", register, None),
                ("the register's rows as a list", self.file("r.json", TFW.stored(made.content)), "observation_state_row:0"),
                ("a row of another snapshot", self.registry("o.json", [finding("x", 2), finding("y", 3, snapshot_id=OLD)]),
                 "observation_other_snapshot:1"),
                ("an object", self.file("obj.json", {}), "not a JSON list")):
            with self.subTest(name):
                code, text = self.command(path, cases, "--snapshot", snapshot, "--tree", self.tree)
                self.assertEqual((code, json.loads(text)["ok"]), (2, False))
                if error:
                    self.assertEqual(json.loads(text)["error"], "unusable input: %s" % error)


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
        out = self.report(self.full_hit(), FULL, alpha=TENTH, meta=meta)
        self.assertEqual(set(out), {"report", "hits", "matched", "missed_rules", "uncased_rules", "outside_rules",
                                    "refused", "counts", "verdict_reason"})
        self.assertEqual(out["report"], {
            "run_id": "r1", "snapshot_id": self.snapshot["snapshot_id"], "spec_version": "2.2",
            "match_rule_version": "v2", "hunter_id": "h", "prompt_sha256": "p", "rung": 1, "n": 3, "n_groups": 1,
            "x_eff": "1.000000", "recall": "1.000000", "recall_lb": "0.100000", "precision": None,
            "precision_lb": None, "census": {"rules_total": 3, "rules_covered": 3, "misses": 0},
            "clean_findings": None, "unresolved": None, "cost_usd": None, "value_per_usd": None, "verdict": "PASS"})
        bare = self.report([], [])["report"]
        self.assertEqual([bare[k] for k in HS.META], [None] * 5)
        self.assertEqual(set(bare), set(out["report"]))

    def test_no_float_in_the_output(self):
        def walk(value):
            self.assertNotIsInstance(value, float)
            for inner in (value.values() if isinstance(value, dict) else value if isinstance(value, list) else ()):
                walk(inner)
        walk(self.report([finding("x", 2)], TWO + [case("c3", 4, group="g")], alpha=TENTH))

    def test_the_census(self):
        cases = [case("c1", 2), case("c2", 3), case("c3", 4, rule="no-eval"), case("c4", 1, path="pkg/b.js", rule="eqeqeq")]
        out = self.report([finding("x", 2), finding("y", 4, rule="no-eval")], cases)
        # no-var has one case hit and one missed: a rule with a miss is not covered. no-eval is outside the set:
        # its case, hit, is no rule of the total and none covered; prefer-const has no case
        self.assertEqual(out["report"]["census"], {"rules_total": 3, "rules_covered": 0, "misses": 2})
        self.assertEqual(out["missed_rules"], [["eslint", "eqeqeq"], ["eslint", "no-var"]])
        self.assertEqual(out["uncased_rules"], [["eslint", "prefer-const"]])
        self.assertEqual(out["outside_rules"], [["eslint", "no-eval"]])
        self.assertEqual((out["report"]["n"], out["hits"], out["report"]["recall"]), (4, 2, "0.500000"))
        # the same rule id of another tool is another rule: outside this set
        out = self.report([], [case("c1", 2), case("c2", 3, tool="ruff")])
        self.assertEqual(out["report"]["census"], {"rules_total": 3, "rules_covered": 0, "misses": 2})
        self.assertEqual((out["uncased_rules"], out["outside_rules"]),
                         ([["eslint", "eqeqeq"], ["eslint", "prefer-const"]], [["ruff", "no-var"]]))
        # the total is the set's size whatever the cases: one case, or one of each rule
        self.assertEqual(self.report([], FULL[:1])["report"]["census"], {"rules_total": 3, "rules_covered": 0, "misses": 1})
        full = self.report(self.full_hit()[1:], FULL)
        self.assertEqual((full["report"]["census"], full["uncased_rules"], full["outside_rules"]),
                         ({"rules_total": 3, "rules_covered": 2, "misses": 1}, [], []))
        # a rule more in the set is a rule more in the total, as a list of lists (a JSON file's) or a set of pairs
        for more_rules in (SET + [("eslint", "yoda")], [list(rule) for rule in SET] + [["eslint", "yoda"]],
                           frozenset(SET) | {("eslint", "yoda")}):
            more = self.report(self.full_hit(), FULL, census=more_rules)
            self.assertEqual((more["report"]["census"], more["uncased_rules"], more["report"]["verdict"]),
                             ({"rules_total": 4, "rules_covered": 3, "misses": 0}, [["eslint", "yoda"]], "UNMEASURABLE"))
        # the set is the caller's and not the operator library's: another catalog gives the same report
        with mock.patch.object(CB, "CATALOG", CB.CATALOG[:1] + ({"tool": "eslint", "rule_id": "other"},)):
            self.assertEqual(self.report(self.full_hit(), FULL), self.report(self.full_hit(), FULL, census=SET[::-1]))
        self.assertEqual(self.report(self.full_hit(), FULL)["report"]["verdict"], "PASS")

    def test_without_a_census_set_no_count_and_never_pass(self):
        # tohum/26q (10): a target with no census vector has no count and is never PASS
        out = self.report(self.full_hit(), FULL, census=None)
        self.assertEqual((out["hits"], out["report"]["recall"], out["report"]["census"], out["uncased_rules"],
                          out["outside_rules"], out["missed_rules"], out["report"]["verdict"], out["verdict_reason"]),
                         (3, "1.000000", None, None, None, [], "UNMEASURABLE", "census_vector_absent"))
        self.assertEqual(out, HS.report(observed(self.stamped(self.full_hit())), FULL, self.snapshot, self.read))
        # a miss is a FAIL there too (26m "Puanlama" 3: the miss comes before the census)
        missed = self.report(self.full_hit()[1:], FULL, census=None)
        self.assertEqual((missed["report"]["census"], missed["missed_rules"], missed["report"]["verdict"],
                          missed["verdict_reason"]), (None, [list(SET[0])], "FAIL", "misses"))
        # and the earlier verdicts stand: no case, a class outside the census
        self.assertEqual(self.report([], [], census=None)["verdict_reason"], "no_cases")
        self.assertEqual(self.report([], [case("c1", 2, class_level="K3")], census=None)["verdict_reason"],
                         "class_without_census")

    def test_a_census_that_is_no_rule_set_is_refused(self):
        for census in ([], set(), {}, {"eslint": "no-var"}, "eslint", b"eslint", 3, [("eslint",)], [("eslint", "a", "b")],
                       [("eslint", 1)], [["eslint", ["no-var"]]], [[["eslint"], "no-var"]], [["eslint", {}]], ["eslint:no-var"], [None], SET + [SET[0]], SET + [("ruff", "E501")], [["eslint", "no-var"], ("eslint", "no-var")]):
            for cases in (FULL, []):
                with self.subTest(census=census, cases=len(cases)):
                    with self.assertRaises(HS.Unusable) as caught:
                        self.report([], cases, census=census)
                    self.assertEqual(caught.exception.reasons, ["census_invalid"])

    def test_the_verdicts(self):
        hit, cases = self.full_hit(), [FULL[0], dict(FULL[1], group="g2"), FULL[2]]
        # a case of every rule of the set, each hit, is PASS, whatever the number of groups (tohum/26h)
        out = self.report(hit, cases)
        self.assertEqual((out["report"]["n_groups"], out["report"]["verdict"], out["verdict_reason"], out["uncased_rules"]),
                         (2, "PASS", None, []))
        one = self.report(hit, FULL)
        self.assertEqual((one["report"]["n_groups"], one["report"]["verdict"], one["verdict_reason"]), (1, "PASS", None))
        with self.assertRaises(TypeError):     # the report takes no floor of groups
            self.report(hit, cases, min_groups=2)
        # a case more, of a rule outside the set, changes no count and no verdict when it is hit too: it is named
        beside = self.report(hit + [finding("e", 5, rule="no-eval")], FULL + [case("c9", 5, rule="no-eval")])
        self.assertEqual((beside["report"]["census"], beside["report"]["verdict"], beside["outside_rules"], beside["report"]["n"]),
                         ({"rules_total": 3, "rules_covered": 3, "misses": 0}, "PASS", [["eslint", "no-eval"]], 4))
        # ... and missed it is a miss and a FAIL, though every rule of the set is covered
        lost = self.report(hit, FULL + [case("c9", 5, rule="no-eval")])
        self.assertEqual((lost["report"]["census"], lost["report"]["recall"], lost["report"]["verdict"],
                          lost["verdict_reason"], lost["missed_rules"], lost["outside_rules"]),
                         ({"rules_total": 3, "rules_covered": 3, "misses": 1}, "0.750000", "FAIL", "misses",
                          [["eslint", "no-eval"]], [["eslint", "no-eval"]]))
        # only cases of rules outside the set, each hit: every rule of the set is without a case
        apart = self.report([finding("e", 5, rule="no-eval")], [case("c9", 5, rule="no-eval")])
        self.assertEqual((apart["report"]["census"], apart["report"]["verdict"], apart["verdict_reason"]),
                         ({"rules_total": 3, "rules_covered": 0, "misses": 0}, "UNMEASURABLE", "rule_without_case"))
        for gone in range(len(FULL)):
            with self.subTest(gone=gone):
                # a case not hit is FAIL
                out = self.report(hit[:gone] + hit[gone + 1:], FULL)
                self.assertEqual((out["report"]["verdict"], out["verdict_reason"]), ("FAIL", "misses"))
                # every case hit and a rule of the set without a case: UNMEASURABLE, never PASS
                fewer = self.report(hit, FULL[:gone] + FULL[gone + 1:])
                self.assertEqual((fewer["hits"], fewer["report"]["recall"], fewer["report"]["verdict"],
                                  fewer["verdict_reason"], fewer["uncased_rules"]),
                                 (2, "1.000000", "UNMEASURABLE", "rule_without_case",
                                  [[FULL[gone]["tool"], FULL[gone]["rule_id"]]]))
                self.assertEqual(fewer["report"]["census"], {"rules_total": 3, "rules_covered": 2, "misses": 0})
        lone = self.report([finding("x", 2)], [case("c1", 2)])     # a run content with its own one case
        self.assertEqual((lone["report"]["verdict"], lone["verdict_reason"]), ("UNMEASURABLE", "rule_without_case"))
        missed = self.report([], [case("c1", 2)])                  # a miss and two rules without a case
        self.assertEqual((missed["report"]["verdict"], missed["verdict_reason"]), ("FAIL", "misses"))
        # a class outside the census: recall is reported, nothing is gated
        k3 = [case("c1", 2, class_level="K3")]
        found = dict(finding("x", 2), required_change=[{"file": "pkg/a.js", "op": "other"}])
        out = self.report([found], k3, window=0)
        self.assertEqual((out["hits"], out["report"]["recall"], out["report"]["census"], out["missed_rules"],
                          out["uncased_rules"], out["outside_rules"], out["report"]["verdict"], out["verdict_reason"]),
                         (1, "1.000000", None, None, None, None, "UNMEASURABLE", "class_without_census"))
        missed = self.report([], k3, window=0)                     # outside the census a miss is no FAIL
        self.assertEqual((missed["report"]["verdict"], missed["verdict_reason"]), ("UNMEASURABLE", "class_without_census"))

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
        self.assertEqual(caught.exception.reasons, ["observations_invalid"])

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
                     [self.hit, self.one, "--snapshot", snapshot, "--tree", self.tree, "--min-groups", "1"],
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
        # other/ is outside the unit's inputs; with it the tree's commit, the proposal's seed, is one whose two
        # mutations hold a ``no-var`` one, the one rule the lint stand-in knows (``test_the_cycle_s_cases...`` checks)
        write_tree(self.src, {"pkg/a.js": TCA.A_JS, "pkg/b.js": TCA.B_JS, "other/x.js": "const o = 1;\n"})

    cek = TCA.LivePath.cek
    hand_over = TCA.LivePath.hand_over

    def yaz_after_kos(self) -> dict:
        self.hand_over(LK.J.run("kos", {"RUNNER_TEMP": self.temp}, runner=LK.RedAs()))
        self.control(LY.OPEN)
        self.github()
        return self.line(self.run_yaz())

    def test_with_a_case_no_report_is_scored(self):
        """tohum/26q (6): the cycle's case snapshot has no hunter run, so the line names that; there is no
        report and no verdict, neither ``FAIL`` nor ``PASS``."""
        self.cek()
        self.assertEqual(sorted(m["operator"] for m in P.read(self.pulled).mutations.values()), ["eqeqeq", "no-var"])
        yaz = self.yaz_after_kos()
        (built,) = yaz["cases"]["cases"]
        self.assertEqual(built["rule_id"], "no-var")
        self.assertEqual(yaz["harness"], {"reason": "no_hunter_run"})
        self.assertNotIn("FAIL", json.dumps(yaz))
        self.assertTrue(yaz["ok"])

    def test_without_cases_no_report_is_scored(self):
        self.kos({"good": LY.candidate(TCA.TK.GOOD)})
        self.control(LY.OPEN)
        self.github()
        yaz = self.line(self.run_yaz())
        # a ready candidate of a cycle after the genesis merges nowhere (P1 MF9, ``no_organ``)
        self.assertEqual((yaz["merge"], yaz["decisions"]["good"]["reasons"]), (None, ["no_organ"]))
        self.assertEqual((yaz["cases"]["cases"], yaz["harness"]), ([], {"reason": "no_hunter_run"}))

    def test_the_job_does_not_reach_the_scorer(self):
        """Y4: the scorer is off the live path until a hunter run exists; the register of the off-live names it."""
        self.assertFalse(hasattr(J, "HS") or hasattr(J, "yaz_harness") or hasattr(J, "FINDINGS"))
        with open(os.path.join(REFEREE, "status", "off_live.json"), encoding="utf-8") as fh:
            register = json.load(fh)
        self.assertEqual(register["harness.score"]["kind"], "unwired")


if __name__ == "__main__":
    unittest.main()
