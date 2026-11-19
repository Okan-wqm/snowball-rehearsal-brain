"""Tests 2 and 4 (asama-1/13g), P1 MF3: ``cases.build`` and its line through the loop (``çek`` proposes, ``pulled``
carries, ``koş`` runs the tool on each mutated tree, ``yaz`` judges and reports), with the fake runner
(``fake_docker.py``) and the lint stand-in of ``test_kos.py`` (``no-var`` on a line starting ``var ``, ``no-eval``
on a line holding ``eval(``; it knows no other rule, as an ESLint whose configuration enables no other).

- test 2 (``Oracle``): the cases built from real runs of the mutated trees; each case's oracle finding hits its own
  case and no other, recall 1,0; a finding moved one line, or of another rule, loses its case;
- test 4 (``Hit``): K0: the right file and rule on another line is no hit, nor a reference wider than the hunk, another
  tool, another rule, another file, and the K3+ window does not widen it; K3: a hit inside the symbol or inside the
  window, none outside both, on another file, with another property or without a required change;
- the proposal (``Proposal``): the ids and diffs by hand, the order by the seed, the rounds over the catalog, the
  limit, the inputs, the places left out; each diff applies to its file through ``gate.diffguard``'s own parse;
- the judgement (``Judgement``): each reason; a violation a hunk shifted is not new;
- the case (``Built``): the fields; ``koş``'s refusal, a missing entry, a run file that is not the index's;
- ``runner.kos`` (``KosRuns``): a mutation's three lint runs on its own copy, no test run, the file and the entry;
  the refusals; the base and a candidate beside it are untouched;
- ``loop.pulled`` (``Carried``) and the jobs (``LivePath``): ``mutations.json`` is required and an object; from
  ``çek``'s assembly through the ``kos`` job to the ``yaz`` job's line (``cases``).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cases import build as CB  # noqa: E402
from gate import diffguard  # noqa: E402
from loop import cek as C  # noqa: E402
from loop import pulled as P  # noqa: E402
from runner import kos as K  # noqa: E402
from runner import lint_record as R  # noqa: E402
from fake_docker import FakeDocker  # noqa: E402
from profile_tree import write_tree  # noqa: E402
import git_store as S  # noqa: E402
import test_kos as TK  # noqa: E402
import test_loop_cek as TC  # noqa: E402
import test_loop_kos as LK  # noqa: E402
import test_loop_yaz as LY  # noqa: E402
import yaz_world as YW  # noqa: E402

# pkg/a.js of these tests: a violation of the base (line 1), three declarations and one comparison to mutate.
A_JS = "var a = 1;\nconst b = 2;\nlet d = 4;\nif (a === b) eval(a);\n"
B_JS = "const c = 3;\n"
FILES = {"pkg/a.js": A_JS.encode(), "pkg/b.js": B_JS.encode()}
SEED = "5" * 40


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mid_by_hand(operator: str, path: str, line: int, data: bytes) -> str:
    joined = "\x00".join((operator, path, str(line), sha(data)))
    return "%s-%s" % (operator, sha(joined.encode())[:16])


def one_line(path: str, line: int, old: str, new: str) -> str:
    return "diff --git a/{p} b/{p}\n--- a/{p}\n+++ b/{p}\n@@ -{n} +{n} @@\n-{o}\n+{w}\n".format(p=path, n=line, o=old, w=new)


def mutation(diff: str, rule_id: str = "no-var", path: str = "pkg/a.js", line: int = 1) -> dict:
    return {"operator": "by-hand", "tool": "eslint", "rule_id": rule_id, "path": path, "line": line, "diff": diff}


def v(rule_id: str, line: int, path: str = "pkg/a.js") -> dict:
    return {"rule_id": rule_id, "path": path, "line": line, "fix": None}


def run(*violations: dict, tool: str = "eslint") -> bytes:
    return R.run_file([{"tool": tool, "violations": list(violations)}] * 3)


NO_VAR_2 = mid_by_hand("no-var", "pkg/a.js", 2, FILES["pkg/a.js"])
NO_VAR_3 = mid_by_hand("no-var", "pkg/a.js", 3, FILES["pkg/a.js"])
NO_VAR_B = mid_by_hand("no-var", "pkg/b.js", 1, FILES["pkg/b.js"])
PREFER_2 = mid_by_hand("prefer-const", "pkg/a.js", 2, FILES["pkg/a.js"])
PREFER_B = mid_by_hand("prefer-const", "pkg/b.js", 1, FILES["pkg/b.js"])
EQEQEQ_4 = mid_by_hand("eqeqeq", "pkg/a.js", 4, FILES["pkg/a.js"])
ALL = {
    NO_VAR_2: {"operator": "no-var", "tool": "eslint", "rule_id": "no-var", "path": "pkg/a.js", "line": 2,
               "diff": one_line("pkg/a.js", 2, "const b = 2;", "var b = 2;")},
    NO_VAR_3: {"operator": "no-var", "tool": "eslint", "rule_id": "no-var", "path": "pkg/a.js", "line": 3,
               "diff": one_line("pkg/a.js", 3, "let d = 4;", "var d = 4;")},
    NO_VAR_B: {"operator": "no-var", "tool": "eslint", "rule_id": "no-var", "path": "pkg/b.js", "line": 1,
               "diff": one_line("pkg/b.js", 1, "const c = 3;", "var c = 3;")},
    PREFER_2: {"operator": "prefer-const", "tool": "eslint", "rule_id": "prefer-const", "path": "pkg/a.js", "line": 2,
               "diff": one_line("pkg/a.js", 2, "const b = 2;", "let b = 2;")},
    PREFER_B: {"operator": "prefer-const", "tool": "eslint", "rule_id": "prefer-const", "path": "pkg/b.js", "line": 1,
               "diff": one_line("pkg/b.js", 1, "const c = 3;", "let c = 3;")},
    EQEQEQ_4: {"operator": "eqeqeq", "tool": "eslint", "rule_id": "eqeqeq", "path": "pkg/a.js", "line": 4,
               "diff": one_line("pkg/a.js", 4, "if (a === b) eval(a);", "if (a == b) eval(a);")},
}


class Proposal(unittest.TestCase):
    def test_every_place_by_hand(self):
        self.assertEqual(CB.propose(FILES, ["pkg"], SEED, limit=100), ALL)

    def test_each_diff_is_one_line_of_its_file_replaced(self):
        for mid, m in CB.propose(FILES, ["."], SEED, limit=100).items():
            with self.subTest(mid):
                (block,) = diffguard.parse(m["diff"])
                self.assertEqual((block["kind"], block["old"], block["new"]), ("modify", m["path"], m["path"]))
                (hunk,) = block["hunks"]
                self.assertEqual((hunk["old_start"], hunk["old_count"], hunk["new_start"], hunk["new_count"]),
                                 (m["line"], 1, m["line"], 1))
                old = FILES[m["path"]].decode().split("\n")[m["line"] - 1]
                self.assertIn("\n-%s\n+" % old, m["diff"])

    def order(self, seed: str, operator: str) -> list:
        """The places of ``operator`` in the order ``seed`` gives, by hand."""
        places = [(m["path"], m["line"]) for m in ALL.values() if m["operator"] == operator]
        return sorted(places, key=lambda p: sha("\x00".join((seed, operator, p[0], str(p[1]))).encode()))

    def test_rounds_over_the_catalog_in_the_seeds_order_up_to_the_limit(self):
        orders = set()
        for seed in ("5" * 40, "6" * 40, "7" * 40, "8" * 40):
            first = [mid_by_hand(op, *self.order(seed, op)[0], FILES[self.order(seed, op)[0][0]])
                     for op in ("no-var", "prefer-const", "eqeqeq")]
            second = [mid_by_hand(op, *self.order(seed, op)[1], FILES[self.order(seed, op)[1][0]])
                      for op in ("no-var", "prefer-const")]
            for limit in range(0, 6):
                with self.subTest(seed=seed[0], limit=limit):
                    self.assertEqual(list(CB.propose(FILES, ["pkg"], seed, limit=limit)), (first + second)[:limit])
            self.assertEqual(list(CB.propose(FILES, ["pkg"], seed)), first[:2])     # the default limit
            orders.add(tuple(self.order(seed, "no-var")))
        self.assertGreater(len(orders), 1)      # the seed decides: these four do not all give one order
        self.assertEqual(CB.LIMIT, 2)

    def test_only_the_inputs(self):
        files = dict(FILES, **{"other/x.js": b"const o = 1;\n", "pkgs/y.js": b"const p = 1;\n"})
        self.assertEqual(CB.propose(files, ["pkg"], SEED, limit=100), ALL)
        self.assertEqual(set(CB.propose(files, ["pkg/b.js"], SEED, limit=100)), {NO_VAR_B, PREFER_B})
        self.assertEqual(CB.propose(files, [], SEED, limit=100), {})
        everywhere = CB.propose(files, ["."], SEED, limit=100)
        self.assertEqual({m["path"] for m in everywhere.values()}, set(files))

    def test_places_left_out(self):
        left_out = {
            "pkg/readme.md": b"const a = 1;\n",                 # not a suffix of the tool
            "pkg/a b.js": b"const a = 1;\n",                    # a path a diff header would quote
            "pkg/\u00e7.js": b"const a = 1;\n",
            "pkg/latin.js": b"const a = '\xe7';\n",             # not UTF-8
            "pkg/crlf.js": b"const a = 1;\r\n",                 # a carriage return in the line
            "pkg/open.js": b"const a = 1;",                     # the last line has no newline
            "pkg/none.js": b"// const a = 1;\nconstant = 1;\nlets = 2;\na !== b; a ==== b; a == b;\n",
        }
        self.assertEqual(CB.propose(left_out, ["."], SEED, limit=100), {})
        kept = CB.propose({"pkg/x.ts": b"  let [p, q] = r;\nif (a===b && c === d) {}\n"}, ["."], SEED, limit=100)
        self.assertEqual(sorted(m["diff"].split("\n", 4)[4] for m in kept.values()),
                         ["-  let [p, q] = r;\n+  var [p, q] = r;\n",
                          "-if (a===b && c === d) {}\n+if (a==b && c === d) {}\n"])

    def test_a_line_is_one_place_of_an_operator_and_a_blank_is_not_a_newline(self):
        twice = {"pkg/t.js": b"x===y; p===q;\nz===w;\n"}
        for seed in "01234567":
            with self.subTest(seed=seed):
                got = CB.propose(twice, ["pkg"], seed, limit=2)
                self.assertEqual(sorted(m["line"] for m in got.values()), [1, 2])
        self.assertIn("\n-x===y; p===q;\n+x==y; p===q;\n", "".join(m["diff"] for m in got.values()))
        after_blank_lines = CB.propose({"pkg/n.js": b"\n \nconst a = 1;\n"}, ["pkg"], SEED, limit=100)
        self.assertEqual(sorted((m["operator"], m["line"]) for m in after_blank_lines.values()),
                         [("no-var", 3), ("prefer-const", 3)])
        self.assertEqual({m["diff"].split("\n")[4] for m in after_blank_lines.values()}, {"-const a = 1;"})

    def test_the_id_is_of_the_place_and_the_files_bytes(self):
        moved = dict(FILES, **{"pkg/a.js": b"\n" + FILES["pkg/a.js"]})
        self.assertFalse(set(CB.propose(moved, ["pkg/a.js"], SEED, limit=100)) & set(ALL))
        self.assertEqual(CB.propose(FILES, ["pkg"], "other seed", limit=100), ALL)


class Judgement(unittest.TestCase):
    M = ALL[NO_VAR_2]
    BASE = run(v("no-var", 1), v("no-eval", 4))
    # a hunk that makes two lines of line 2: the base's line 4 is the mutated tree's line 5
    WIDE = mutation("diff --git a/pkg/a.js b/pkg/a.js\n--- a/pkg/a.js\n+++ b/pkg/a.js\n@@ -2 +2,2 @@\n"
                    "-const b = 2;\n+var b = 2;\n+var e = 5;\n", line=2)

    def test_exactly_one_new_violation_in_the_region(self):
        self.assertEqual(CB.judge(self.M, self.BASE, run(v("no-var", 1), v("no-var", 2), v("no-eval", 4))),
                         ([], {"line": 2, "hunk": {"start": 2, "end": 2}}))

    def test_a_violation_the_hunk_shifted_is_not_new(self):
        shifted = run(v("no-var", 1), v("no-var", 3), v("no-eval", 5))
        self.assertEqual(CB.judge(self.WIDE, self.BASE, shifted), ([], {"line": 3, "hunk": {"start": 2, "end": 3}}))
        # the base's line 4 is the mutated tree's line 5 and no other: a no-eval reported at 4 is new, outside the region
        beside = run(v("no-var", 1), v("no-var", 3), v("no-eval", 4), v("no-eval", 5))
        self.assertEqual(CB.judge(self.WIDE, self.BASE, beside), (["violation_outside_region:1"], None))

    def test_no_new_violation(self):
        self.assertEqual(CB.judge(self.M, self.BASE, self.BASE), (["violation_none"], None))
        # the replaced line already violated the rule: the mutation planted nothing
        base = run(v("no-var", 1), v("no-var", 2))
        self.assertEqual(CB.judge(self.M, base, base), (["violation_none"], None))
        # fewer violations than the base is none new either
        self.assertEqual(CB.judge(self.M, self.BASE, run()), (["violation_none"], None))

    def test_a_base_violation_of_another_rule_on_the_line_carries_nothing(self):
        base = run(v("no-var", 1), v("no-eval", 2))
        self.assertEqual(CB.judge(self.M, base, run(v("no-var", 1), v("no-eval", 2), v("no-var", 2))),
                         ([], {"line": 2, "hunk": {"start": 2, "end": 2}}))
        # nor does the same rule's violation of another file on that line
        base = run(v("no-var", 1), v("no-var", 2, "pkg/b.js"))
        self.assertEqual(CB.judge(self.M, base, run(v("no-var", 1), v("no-var", 2), v("no-var", 2, "pkg/b.js")))[0], [])

    def test_more_than_one_in_the_region(self):
        both = run(v("no-var", 1), v("no-var", 2), v("no-var", 3), v("no-eval", 5))
        self.assertEqual(CB.judge(self.WIDE, self.BASE, both), (["violations_many:2"], None))
        two_rules = run(v("no-var", 1), v("no-var", 2), v("no-eval", 2), v("no-eval", 4))
        self.assertEqual(CB.judge(self.M, self.BASE, two_rules), (["violations_many:2"], None))
        # one (rule, line) reported twice is one violation
        twice = run(v("no-var", 1), v("no-var", 2), v("no-var", 2), v("no-eval", 4))
        self.assertEqual(CB.judge(self.M, self.BASE, twice)[0], [])

    def test_a_new_violation_outside_the_region(self):
        for name, extra in (("another line", v("no-var", 3)), ("another file", v("no-var", 2, "pkg/b.js"))):
            with self.subTest(name):
                self.assertEqual(CB.judge(self.M, self.BASE, run(v("no-var", 1), v("no-var", 2), v("no-eval", 4), extra)),
                                 (["violation_outside_region:1"], None))
                self.assertEqual(CB.judge(self.M, self.BASE, run(v("no-var", 1), v("no-eval", 4), extra)),
                                 (["violation_none", "violation_outside_region:1"], None))

    def test_the_one_new_violation_is_of_another_rule(self):
        self.assertEqual(CB.judge(self.M, self.BASE, run(v("no-var", 1), v("no-eval", 2), v("no-eval", 4))),
                         (["rule_unexpected"], None))

    def test_the_runs(self):
        good = run(v("no-var", 1), v("no-var", 2), v("no-eval", 4))
        noisy = R.run_file([{"tool": "eslint", "violations": [v("no-var", 1), v("no-var", n)]} for n in (2, 2, 3)])
        for name, base, mut, want in (
                ("a base that is no run file", b"not json\n", good, "run_unusable"),
                ("a mutated run of two lines", self.BASE, b"\n".join(good.split(b"\n")[:2]) + b"\n", "run_unusable"),
                ("a base that differs between runs", noisy, good, "tool_nondeterministic"),
                ("a mutated run that differs between runs", self.BASE, noisy, "tool_nondeterministic"),
                ("another tool's base", run(v("no-var", 1), tool="tsc"), good, "tool_unexpected"),
                ("another tool's mutated run", self.BASE, run(v("no-var", 1), v("no-var", 2), tool="tsc"),
                 "tool_unexpected")):
            with self.subTest(name):
                self.assertEqual(CB.judge(self.M, base, mut), ([want], None))

    def test_a_mutation_that_is_not_one(self):
        good = run(v("no-var", 1), v("no-var", 2), v("no-eval", 4))
        two = self.M["diff"] + ALL[NO_VAR_B]["diff"]
        deletion = "diff --git a/pkg/a.js b/pkg/a.js\n--- a/pkg/a.js\n+++ b/pkg/a.js\n@@ -2 +1,0 @@\n-const b = 2;\n"
        rename = self.M["diff"].replace("b/pkg/a.js", "b/pkg/z.js")
        for name, m in (("not an object", [self.M]), ("a key short", {k: x for k, x in self.M.items() if k != "tool"}),
                        ("a key more", dict(self.M, note="x")), ("an empty rule", dict(self.M, rule_id="")),
                        ("a line that is a string", dict(self.M, line="2")), ("a line that is true", dict(self.M, line=True)),
                        ("a diff that is none", dict(self.M, diff="no diff")), ("a diff of two files", dict(self.M, diff=two)),
                        ("a diff of another file", dict(self.M, path="pkg/b.js")),
                        ("a hunk with no mutated line", dict(self.M, diff=deletion)),
                        ("a rename", dict(self.M, diff=rename))):
            with self.subTest(name):
                self.assertEqual(CB.judge(m, self.BASE, good), (["mutation_unusable"], None))
        self.assertEqual(CB.judge(self.M, self.BASE, good)[0], [])


class World(TK.Base):
    """``runner.kos.results`` on the tree with ``A_JS``, and ``cases.build.build`` on what it wrote."""

    def setUp(self) -> None:
        super().setUp()
        write_tree(self.tree, {"pkg/a.js": A_JS, "pkg/b.js": B_JS})

    def kos(self, mutations: dict, candidates=None, red=TK.RED, runner=None) -> dict:
        return K.results(TK.recipe(), self.tree, {"operating": TK.operating()}, red, candidates or {}, self.out,
                         runner=runner or FakeDocker(), base=self.runs,
                         mutations={mid: m["diff"].encode() for mid, m in mutations.items()})

    def read(self, path: str) -> bytes | None:
        full = os.path.join(self.out, path)
        return TK.read(full) if os.path.isfile(full) else None

    def build(self, mutations: dict, index=None, read=None) -> dict:
        index = json.loads(self.read("index.json")) if index is None else index
        return CB.build(SEED, mutations, index, read or self.read)


class Oracle(World):
    """Test 2: the oracle findings of the built cases, scored by the hit rule: recall 1,0."""

    def recall(self, built: dict, findings: list) -> float:
        hit = [c for c in built["cases"] if any(CB.hit(f, c) for f in findings)]
        return len(hit) / len(built["cases"])

    def test_oracle_findings_recall_one(self):
        self.kos(ALL)
        built = self.build(ALL)
        # the stand-in knows no-var only: its three mutations are the cases, the others plant nothing it reports
        self.assertEqual([c["mutation_id"] for c in built["cases"]], sorted([NO_VAR_2, NO_VAR_3, NO_VAR_B]))
        self.assertEqual(built["refused"], {m: ["violation_none"] for m in (PREFER_2, PREFER_B, EQEQEQ_4)})
        self.assertEqual(sorted(built["oracle"]), sorted(c["case_id"] for c in built["cases"]))
        self.assertEqual(self.recall(built, list(built["oracle"].values())), 1.0)
        # each oracle finding hits its own case and no other (two of the cases share file and rule)
        for case in built["cases"]:
            for case_id, finding in built["oracle"].items():
                with self.subTest(case=case["case_id"], finding=case_id):
                    self.assertEqual(CB.hit(finding, case), case_id == case["case_id"])

    def test_findings_that_are_not_the_oracles_lose_recall(self):
        self.kos(ALL)
        built = self.build(ALL)
        oracle = list(built["oracle"].values())
        self.assertEqual(self.recall(built, oracle[:2]), 2 / 3)
        self.assertEqual(self.recall(built, []), 0.0)
        down = [dict(f, evidence_refs=[dict(r, line_start=r["line_start"] + 5, line_end=r["line_end"] + 5)
                                       for r in f["evidence_refs"]]) for f in oracle]
        self.assertEqual(self.recall(built, down), 0.0)
        self.assertEqual(self.recall(built, [dict(f, rule_id="no-eval") for f in oracle]), 0.0)

    def test_the_oracle_is_where_the_tool_reported(self):
        self.kos({NO_VAR_3: ALL[NO_VAR_3]})
        built = self.build({NO_VAR_3: ALL[NO_VAR_3]})
        self.assertEqual(built["oracle"], {"k0-" + NO_VAR_3: {
            "class_level": "K0", "property": "lint", "file": "pkg/a.js", "tool": "eslint", "rule_id": "no-var",
            "evidence_refs": [{"path": "pkg/a.js", "line_start": 3, "line_end": 3}]}})
        record = json.loads(self.read(CB.run_path(NO_VAR_3)).split(b"\n")[0])
        self.assertIn({"rule_id": "no-var", "path": "pkg/a.js", "line": 3, "fix": [3, 3]}, record["violations"])


K0 = {"case_id": "k0-x", "class_level": "K0", "property": "lint", "provenance": "mutation", "base_sha": SEED,
      "mutation_id": "x", "touched_paths": [{"path": "src/a.ts", "hunks": [{"start": 10, "end": 12}]}],
      "tool": "eslint", "rule_id": "no-var", "split": "dev", "group": "src",
      "validity_evidence": {"kind": "tool_diff", "ref": "m/x/mut.jsonl", "output_sha256": "0" * 64}}
K3 = {"case_id": "k3-y", "class_level": "K3", "property": "authz", "provenance": "human_fix", "base_sha": SEED,
      "fix_sha": "9" * 40, "touched_paths": [{"path": "src/svc.ts", "hunks": [{"start": 40, "end": 50}],
                                              "symbol": "Svc.find"}],
      "split": "dev", "group": "src",
      "validity_evidence": {"kind": "test_diff", "ref": "x", "output_sha256": "0" * 64}}


def ref(path: str, first: int, last: int | None = None) -> dict:
    return {"path": path, "line_start": first, "line_end": first if last is None else last}


def k0_finding(*refs: dict, **over) -> dict:
    return dict({"class_level": "K0", "property": "lint", "file": "src/a.ts", "tool": "eslint", "rule_id": "no-var",
                 "claim": "x", "evidence_refs": list(refs)}, **over)


def k3_finding(*refs: dict, **over) -> dict:
    return dict({"class_level": "K3", "property": "authz", "file": "src/svc.ts", "symbol": "Svc.other",
                 "claim": "x", "evidence_refs": list(refs),
                 "required_change": [{"file": "src/svc.ts", "op": "add_guard"}]}, **over)


class Hit(unittest.TestCase):
    """Test 4: the right file on another line is no hit (K0); outside the symbol is none (K3)."""

    def test_k0_the_mapped_line(self):
        for line in (10, 11, 12):
            self.assertTrue(CB.hit(k0_finding(ref("src/a.ts", line)), K0))
        self.assertTrue(CB.hit(k0_finding(ref("src/a.ts", 10, 12)), K0))
        self.assertTrue(CB.hit(k0_finding(ref("src/z.ts", 1), ref("src/a.ts", 11)), K0))    # one reference is enough

    def test_k0_the_right_file_and_rule_on_another_line_is_no_hit(self):
        for name, finding in (
                ("the line before the hunk", k0_finding(ref("src/a.ts", 9))),
                ("the line after it", k0_finding(ref("src/a.ts", 13))),
                ("a reference wider than the hunk", k0_finding(ref("src/a.ts", 9, 12))),
                ("a reference running past it", k0_finding(ref("src/a.ts", 12, 13))),
                ("a reference of the whole file", k0_finding(ref("src/a.ts", 1, 500))),
                ("the same line of another file", k0_finding(ref("src/b.ts", 11))),
                ("another rule", k0_finding(ref("src/a.ts", 11), rule_id="prefer-const")),
                ("another tool", k0_finding(ref("src/a.ts", 11), tool="tsc")),
                ("no rule", {k: x for k, x in k0_finding(ref("src/a.ts", 11)).items() if k != "rule_id"}),
                ("no reference", k0_finding()),
                ("a reversed reference", k0_finding(ref("src/a.ts", 12, 10))),
                ("lines that are not numbers", k0_finding({"path": "src/a.ts", "line_start": "11", "line_end": "11"})),
                ("not a finding", [k0_finding(ref("src/a.ts", 11))])):
            with self.subTest(name):
                self.assertFalse(CB.hit(finding, K0))
                self.assertFalse(CB.hit(finding, K0, 15))       # the K3+ window is not K0's

    def test_k0_does_not_hit_by_symbol_and_property(self):
        case = dict(K0, touched_paths=[dict(K0["touched_paths"][0], symbol="f")])
        finding = k0_finding(ref("src/a.ts", 30), symbol="f", required_change=[{"file": "src/a.ts", "op": "x"}])
        self.assertFalse(CB.hit(finding, case, 15))
        for level in ("K1", "K2"):                              # the three deterministic classes read one rule
            self.assertFalse(CB.hit(finding, dict(case, class_level=level), 15))
            self.assertTrue(CB.hit(k0_finding(ref("src/a.ts", 11)), dict(case, class_level=level)))

    def test_k0_a_case_without_its_tool_or_rule_is_hit_by_nothing(self):
        finding = k0_finding(ref("src/a.ts", 11))
        for key in ("tool", "rule_id"):
            case = {k: x for k, x in K0.items() if k != key}
            self.assertFalse(CB.hit({k: x for k, x in finding.items() if k != key}, case))

    def test_k3_inside_the_symbol_or_the_window(self):
        self.assertTrue(CB.hit(k3_finding(ref("src/svc.ts", 400), symbol="Svc.find"), K3))        # the symbol, far away
        self.assertTrue(CB.hit(k3_finding(ref("src/svc.ts", 400), symbol="Svc.find"), K3, 15))
        for first, last in ((25, 25), (65, 65), (25, 65), (45, 45)):                            # 40-15 .. 50+15
            self.assertTrue(CB.hit(k3_finding(ref("src/svc.ts", first, last)), K3, 15), (first, last))

    def test_k3_outside_the_symbol_and_the_window_is_no_hit(self):
        for name, finding, window in (
                ("one line above the window", k3_finding(ref("src/svc.ts", 24)), 15),
                ("one line below it", k3_finding(ref("src/svc.ts", 66)), 15),
                ("a reference wider than the window", k3_finding(ref("src/svc.ts", 24, 45)), 15),
                ("inside a window nobody gave", k3_finding(ref("src/svc.ts", 45)), None),
                ("a narrower window", k3_finding(ref("src/svc.ts", 30)), 5),
                ("a window that is true", k3_finding(ref("src/svc.ts", 41)), True),
                ("a negative window", k3_finding(ref("src/svc.ts", 45)), -1),
                ("the symbol in another file", k3_finding(ref("src/other.ts", 45), symbol="Svc.find"), 15),
                ("the symbol without a reference", k3_finding(symbol="Svc.find"), 15),
                ("no symbol, outside", {k: x for k, x in k3_finding(ref("src/svc.ts", 400)).items() if k != "symbol"}, 15),
                ("another property", k3_finding(ref("src/svc.ts", 45), property="tenancy", symbol="Svc.find"), 15),
                ("an empty required change", k3_finding(ref("src/svc.ts", 45), required_change=[], symbol="Svc.find"), 15),
                ("no required change", {k: x for k, x in k3_finding(ref("src/svc.ts", 45), symbol="Svc.find").items()
                                        if k != "required_change"}, 15)):
            with self.subTest(name):
                self.assertFalse(CB.hit(finding, K3, window))

    def test_k3_a_case_without_a_symbol_is_hit_by_the_window_only(self):
        case = dict(K3, touched_paths=[{"path": "src/svc.ts", "hunks": [{"start": 40, "end": 50}]}])
        no_symbol = {k: x for k, x in k3_finding(ref("src/svc.ts", 400)).items() if k != "symbol"}
        self.assertFalse(CB.hit(no_symbol, case, 15))
        self.assertFalse(CB.hit(dict(no_symbol, symbol=None), case, 15))
        self.assertTrue(CB.hit(k3_finding(ref("src/svc.ts", 60)), case, 15))


class Built(World):
    def test_the_case(self):
        index = self.kos({NO_VAR_2: ALL[NO_VAR_2]})
        built = self.build({NO_VAR_2: ALL[NO_VAR_2]})
        self.assertEqual(built["cases"], [{
            "case_id": "k0-" + NO_VAR_2, "class_level": "K0", "property": "lint", "provenance": "mutation",
            "base_sha": SEED, "mutation_id": NO_VAR_2,
            "touched_paths": [{"path": "pkg/a.js", "hunks": [{"start": 2, "end": 2}]}],
            "tool": "eslint", "rule_id": "no-var",
            "validity_evidence": {"kind": "tool_diff", "ref": "m/%s/mut.jsonl" % NO_VAR_2,
                                  "output_sha256": index["mutations"][NO_VAR_2]["run_sha256"]},
            "split": "dev", "group": "pkg"}])
        self.assertEqual(built["refused"], {})
        self.assertEqual(index["mutations"][NO_VAR_2]["run_sha256"], sha(self.read("m/%s/mut.jsonl" % NO_VAR_2)))

    def test_the_group_of_a_file_at_the_root(self):
        m = mutation(one_line("a.js", 1, "const b = 2;", "var b = 2;"), path="a.js")
        index = {"base_run_sha256": sha(run()), "mutations": {"x": {"verdict": "verified", "reasons": [],
                                                                     "run_sha256": sha(run(v("no-var", 1, "a.js")))}}}
        files = {"base.jsonl": run(), "m/x/mut.jsonl": run(v("no-var", 1, "a.js"))}
        (case,) = CB.build(SEED, {"x": m}, index, files.get)["cases"]
        self.assertEqual((case["group"], case["touched_paths"]), (".", [{"path": "a.js", "hunks": [{"start": 1, "end": 1}]}]))

    def test_what_kos_refused_is_no_case(self):
        absent = mutation(one_line("pkg/a.js", 2, "const z = 9;", "var z = 9;"), line=2)      # does not apply
        index = self.kos({NO_VAR_2: ALL[NO_VAR_2], "absent": absent, "bad id!": ALL[NO_VAR_3]})
        self.assertEqual(index["mutations"]["absent"]["verdict"], "refused")
        built = self.build({NO_VAR_2: ALL[NO_VAR_2], "absent": absent, "bad id!": ALL[NO_VAR_3],
                            "unknown": ALL[NO_VAR_B], "broken": dict(ALL[NO_VAR_B], diff="x")})
        self.assertEqual([c["mutation_id"] for c in built["cases"]], [NO_VAR_2])
        self.assertEqual(built["refused"], {
            "absent": ["kos:%s" % r for r in index["mutations"]["absent"]["reasons"]],
            "bad id!": ["kos:candidate_id_invalid"], "unknown": ["kos:missing"], "broken": ["mutation_unusable"]})
        self.assertTrue(index["mutations"]["absent"]["reasons"])

    def test_an_entry_without_reasons_gives_its_verdict(self):
        self.kos({NO_VAR_2: ALL[NO_VAR_2]})
        index = json.loads(self.read("index.json"))
        index["mutations"][NO_VAR_2] = {"verdict": "no_verdict", "reasons": [], "run_sha256": None}
        self.assertEqual(self.build({NO_VAR_2: ALL[NO_VAR_2]}, index)["refused"], {NO_VAR_2: ["kos:no_verdict"]})
        for index in ({}, {"mutations": []}, [], None):
            self.assertEqual(CB.build(SEED, {NO_VAR_2: ALL[NO_VAR_2]}, index, self.read)["refused"],
                             {NO_VAR_2: ["kos:missing"]})

    def test_a_run_file_is_read_under_its_hash_only(self):
        mutations = {NO_VAR_2: ALL[NO_VAR_2]}
        self.kos(mutations)
        good = json.loads(self.read("index.json"))
        path = CB.run_path(NO_VAR_2)
        # a mutated run that would be a case by itself, were it not for the hash
        other = run(v("no-var", 1), v("no-var", 2), v("no-eval", 4))
        self.assertNotEqual(other, self.read(path))
        for name, index, read in (
                ("the mutated run's bytes changed", good, lambda p: other if p == path else self.read(p)),
                ("the base's bytes changed", good, lambda p: run(v("no-eval", 4)) if p == "base.jsonl" else self.read(p)),
                ("no mutated run", good, lambda p: None if p == path else self.read(p)),
                ("no base", good, lambda p: None if p == "base.jsonl" else self.read(p)),
                ("no hash of the base", {k: x for k, x in good.items() if k != "base_run_sha256"}, self.read),
                ("no hash of the run", dict(good, mutations={NO_VAR_2: dict(good["mutations"][NO_VAR_2], run_sha256=None)}),
                 self.read)):
            with self.subTest(name):
                self.assertEqual(self.build(mutations, index, read),
                                 {"cases": [], "oracle": {}, "refused": {NO_VAR_2: ["artefact_hash_mismatch"]}})
        self.assertEqual(self.build(mutations, good)["refused"], {})

    def test_mutations_that_are_no_object(self):
        for mutations in (None, [], "x"):
            self.assertEqual(CB.build(SEED, mutations, {}, lambda p: None), {"cases": [], "oracle": {}, "refused": {}})


class GreenAfter:
    """The fake runner whose red control is red for its first ``n`` runs and passes after them."""

    def __init__(self, n: int) -> None:
        self.docker, self.n, self.seen = FakeDocker(), n, 0

    def __call__(self, argv, env, timeout):
        k = len(TK.RED["cmd"])
        if argv[-k:] == TK.RED["cmd"]:
            self.seen += 1
            if self.seen > self.n:
                argv = argv[:-k] + TK.GREEN_RED["cmd"]
        return self.docker(argv, env, timeout)


class KosRuns(World):
    def cmds(self, docker) -> list:
        return [c["argv"][c["argv"].index(TK.IMAGE) + 1:] for c in docker.calls]

    def test_three_lint_runs_of_the_mutated_tree_and_no_test_run(self):
        docker = FakeDocker()
        index = self.kos({NO_VAR_2: ALL[NO_VAR_2]}, runner=docker)
        record = {"tool": "eslint", "violations": [
            {"rule_id": "no-var", "path": "pkg/a.js", "line": 1, "fix": [1, 1]},
            {"rule_id": "no-var", "path": "pkg/a.js", "line": 2, "fix": [2, 2]},
            {"rule_id": "no-eval", "path": "pkg/a.js", "line": 4, "fix": None}]}
        data = self.read("m/%s/mut.jsonl" % NO_VAR_2)
        self.assertEqual(data, R.run_file([record] * 3))
        self.assertEqual(index["mutations"], {NO_VAR_2: {"verdict": "verified", "reasons": [], "run_sha256": sha(data)}})
        self.assertEqual(os.listdir(os.path.join(self.out, "m", NO_VAR_2)), ["mut.jsonl"])
        # the base's three lint runs, then the mutation's three; each with the red control; the tests never run
        self.assertEqual(self.cmds(docker), [["python", "pkg/red.py"], ["python", "pkg/lint.py"]] * 6)
        self.assertEqual(json.loads(self.read("index.json")), index)

    def test_the_base_and_a_candidate_beside_it_do_not_see_the_mutation(self):
        alone = self.kos({}, {"good": TK.GOOD})
        base, cand = self.read("base.jsonl"), self.read("c/good/cand.jsonl")
        self.assertEqual(alone["mutations"], {})
        shutil.rmtree(self.out)
        both = self.kos({NO_VAR_2: ALL[NO_VAR_2], NO_VAR_B: ALL[NO_VAR_B]}, {"good": TK.GOOD})
        self.assertEqual((self.read("base.jsonl"), self.read("c/good/cand.jsonl")), (base, cand))
        self.assertEqual(both["candidates"], alone["candidates"])
        # each mutation ran on its own copy: neither run holds the other's violation
        runs = {m: json.loads(self.read(CB.run_path(m)).split(b"\n")[0])["violations"] for m in (NO_VAR_2, NO_VAR_B)}
        self.assertEqual([(x["path"], x["line"]) for x in runs[NO_VAR_2] if x["rule_id"] == "no-var"],
                         [("pkg/a.js", 1), ("pkg/a.js", 2)])
        self.assertEqual([(x["path"], x["line"]) for x in runs[NO_VAR_B] if x["rule_id"] == "no-var"],
                         [("pkg/a.js", 1), ("pkg/b.js", 1)])
        self.assertEqual(TK.read(os.path.join(self.tree, "pkg/a.js")).decode(), A_JS)      # nor did the tree given

    def test_refusals_write_no_run_file(self):
        noisy = mutation(one_line("pkg/a.js", 2, "const b = 2;", "var b = 2; // NOISE"), line=2)
        crash = mutation(one_line("pkg/a.js", 2, "const b = 2;", "var b = 2; // LINTCRASH"), line=2)
        absent = mutation(one_line("pkg/a.js", 2, "const z = 9;", "var z = 9;"), line=2)
        outside = mutation(one_line("other/outside.js", 1, "var o = 1;", "var p = 1;"), path="other/outside.js")
        index = self.kos({"noisy": noisy, "crash": crash, "absent": absent, "outside": outside, "bad id!": noisy})
        got = index["mutations"]
        self.assertEqual(set(got), {"noisy", "crash", "absent", "outside", "bad id!"})
        # a tool that differs between runs still wrote its three records: the judgement reads them (below)
        self.assertEqual(os.listdir(os.path.join(self.out, "m")), ["noisy"])
        self.assertEqual((got["noisy"]["verdict"], got["noisy"]["run_sha256"]),
                         ("verified", sha(self.read("m/noisy/mut.jsonl"))))
        for mid in ("crash", "absent", "outside", "bad id!"):
            with self.subTest(mid):
                self.assertNotEqual(got[mid]["verdict"], "verified")
                self.assertTrue(got[mid]["reasons"])
                self.assertIsNone(got[mid]["run_sha256"])
        self.assertEqual(got["bad id!"]["reasons"], ["candidate_id_invalid"])
        self.assertEqual(self.build({"noisy": noisy})["refused"], {"noisy": ["tool_nondeterministic"]})

    def test_a_red_control_that_passes_judges_nothing(self):
        index = self.kos({NO_VAR_2: ALL[NO_VAR_2]}, red=TK.GREEN_RED)
        entry = index["mutations"][NO_VAR_2]
        self.assertEqual((entry["verdict"] == "verified", entry["run_sha256"]), (False, None))
        self.assertFalse(os.path.lexists(os.path.join(self.out, "m")))
        self.assertEqual(self.build({NO_VAR_2: ALL[NO_VAR_2]})["cases"], [])

    def test_a_red_control_that_passes_in_the_mutations_runs_only(self):
        runner = GreenAfter(3)                              # the base's three runs had a red red control
        index = self.kos({NO_VAR_2: ALL[NO_VAR_2]}, runner=runner)
        self.assertEqual(index["base"]["verdict"], "verified")
        self.assertEqual(index["mutations"], {NO_VAR_2: {"verdict": "no_verdict", "reasons": ["red_control_green"],
                                                         "run_sha256": None}})
        self.assertFalse(os.path.lexists(os.path.join(self.out, "m")))
        self.assertEqual(self.build({NO_VAR_2: ALL[NO_VAR_2]})["refused"], {NO_VAR_2: ["kos:red_control_green"]})

    def test_no_base_no_mutation_run(self):
        write_tree(self.tree, {"pkg/a.js": "LINTCRASH\nconst b = 2;\n"})
        m = mutation(one_line("pkg/a.js", 2, "const b = 2;", "var b = 2;"), line=2)
        docker = FakeDocker()
        index = self.kos({"m1": m}, runner=docker)
        self.assertEqual(index["mutations"], {"m1": {"verdict": "no_verdict", "reasons": ["base_unavailable"],
                                                     "run_sha256": None}})
        self.assertEqual(len(docker.calls), 6)          # the base's own
        self.assertEqual(self.build({"m1": m})["refused"], {"m1": ["kos:base_unavailable"]})

    def test_mutations_are_ids_to_diff_bytes(self):
        for given in ({NO_VAR_2: ALL[NO_VAR_2]["diff"]}, {NO_VAR_2: ALL[NO_VAR_2]}, [ALL[NO_VAR_2]["diff"].encode()],
                      {1: b""}):
            with self.subTest(given=repr(given)[:30]):
                docker = FakeDocker()
                with self.assertRaises(K.KosError):
                    K.results(TK.recipe(), self.tree, {"operating": TK.operating()}, TK.RED, {}, self.out,
                              runner=docker, base=self.runs, mutations=given)
                self.assertEqual(docker.calls, [])
                self.assertFalse(os.path.lexists(self.out))


class Carried(LK.Base):
    """``loop.pulled``: ``mutations.json`` is always listed and holds an object; carried, not judged."""

    def test_mutations_json_is_required_and_an_object(self):
        self.write_pulled(mutations={"m1": {"any": ["value", 1]}})
        self.assertEqual(P.read(self.pulled).mutations, {"m1": {"any": ["value", 1]}})
        manifest = self.manifest()
        for data, want in ((b"{not json", "json_unreadable:mutations.json"), (b"[]", "mutations_invalid"),
                           (b"null", "mutations_invalid")):
            with self.subTest(data=data):
                with open(os.path.join(self.pulled, "mutations.json"), "wb") as fh:
                    fh.write(data)
                manifest["files"]["mutations.json"] = sha(data)
                self.set_manifest(manifest)
                self.assertEqual(self.reasons(), [want])
        os.remove(os.path.join(self.pulled, "mutations.json"))
        del manifest["files"]["mutations.json"]
        self.set_manifest(manifest)
        self.assertEqual(self.reasons(), ["missing:mutations.json"])

    def test_none_is_written_as_no_mutation(self):
        self.write_pulled()
        self.assertEqual(P.read(self.pulled).mutations, {})
        with open(os.path.join(self.pulled, "mutations.json"), "rb") as fh:
            self.assertEqual(json.loads(fh.read()), {})

    def test_what_is_no_object_is_refused_at_the_write(self):
        for given in ([], "x", {"m": {b"bytes"}}):
            with self.subTest(given=repr(given)):
                with self.assertRaises(P.PulledError) as ctx:
                    self.write_pulled(mutations=given)
                self.assertEqual(ctx.exception.reasons, ["mutations_invalid"])
                self.assertFalse(os.path.lexists(self.pulled))


class LivePath(LY.YazBase):
    """``çek``'s assembly -> the ``kos`` job -> the ``yaz`` job: the cases are on ``yaz``'s line."""

    def setUp(self) -> None:
        super().setUp()
        # other/ is outside the unit's inputs: nothing of it is proposed
        write_tree(self.src, {"pkg/a.js": A_JS, "pkg/b.js": B_JS, "other/x.js": "const o = 1;\n"})

    def cek(self) -> str:
        """``loop.cek.assemble`` of the tree and the brain into the download ``kos`` reads; the target's commit."""
        brain, brain_commit = S.store(TC.brain_files())
        objects, commit = TC.target_objects(self.src)
        os.makedirs(os.path.dirname(self.pulled))
        P.write_served(os.path.dirname(self.pulled), ["t1"])
        summary = {"targets": [dict(LK.TARGET, repo=YW.REPO)]}
        C.assemble(brain.__getitem__, brain_commit, json.dumps(summary).encode(), TC.POLICY, "t1",
                   objects.__getitem__, commit, LK.HEADS["brain/state"], LK.state_files(), None, self.pulled)
        return commit

    def hand_over(self, out: dict) -> dict:
        self.assertTrue(out["ok"], out)
        os.makedirs(os.path.dirname(self.results()), exist_ok=True)
        shutil.move(os.path.join(self.temp, "out", "results", "t1"), self.results())
        return self.line(out)

    def test_from_cek_through_kos_the_cases_are_on_yaz_s_line(self):
        commit = self.cek()
        proposed = P.read(self.pulled).mutations
        # cek proposed from the commit's files, the unit's inputs and the commit as the seed: the default limit
        self.assertEqual(proposed, CB.propose(FILES, ["pkg"], commit))
        self.assertEqual(len(proposed), 2)
        runner = LK.RedAs()
        kos = self.hand_over(LK.J.run("kos", {"RUNNER_TEMP": self.temp}, runner=runner))
        self.assertEqual({m: e["verdict"] for m, e in kos["index"]["mutations"].items()},
                         {m: "verified" for m in proposed})
        self.control(LY.OPEN)
        self.github()
        yaz = self.line(self.run_yaz())
        self.assertEqual((yaz["ok"], yaz["done"][:1]), (True, ["D5"]))
        (valid,) = [m for m in proposed if proposed[m]["operator"] == "no-var"]
        (other,) = [m for m in proposed if m != valid]
        self.assertEqual(yaz["cases"]["refused"], {other: ["violation_none"]})
        (case,) = yaz["cases"]["cases"]
        self.assertEqual((case["case_id"], case["base_sha"], case["rule_id"], case["touched_paths"]),
                         ("k0-" + valid, commit, "no-var",
                          [{"path": proposed[valid]["path"],
                            "hunks": [{"start": proposed[valid]["line"], "end": proposed[valid]["line"]}]}]))
        with open(self.results(case["validity_evidence"]["ref"]), "rb") as fh:
            self.assertEqual(case["validity_evidence"]["output_sha256"], sha(fh.read()))
        self.assertTrue(CB.hit(yaz["cases"]["oracle"][case["case_id"]], case))

    def test_yaz_judges_only_what_kos_ran(self):
        self.write_pulled({}, mutations={NO_VAR_2: ALL[NO_VAR_2], NO_VAR_3: ALL[NO_VAR_3]})
        self.hand_over(LK.J.run("kos", {"RUNNER_TEMP": self.temp}, runner=LK.RedAs()))
        self.control(LY.OPEN)
        self.github()
        # after kos: one run file changed, the other's index entry gone
        with open(self.results(CB.run_path(NO_VAR_2)), "ab") as fh:
            fh.write(b"\n")
        with open(self.results("index.json")) as fh:
            index = json.load(fh)
        del index["mutations"][NO_VAR_3]
        with open(self.results("index.json"), "w") as fh:
            json.dump(index, fh)
        yaz = self.line(self.run_yaz())
        self.assertEqual(yaz["cases"], {"cases": [], "oracle": {}, "refused": {
            NO_VAR_2: ["artefact_hash_mismatch"], NO_VAR_3: ["kos:missing"]}})

    def test_without_mutations_the_line_holds_no_case(self):
        self.kos({"good": LY.candidate(TK.GOOD)})
        self.control(LY.OPEN)
        self.github()
        yaz = self.line(self.run_yaz())
        self.assertEqual((yaz["merge"], yaz["cases"]), ("good", {"cases": [], "oracle": {}, "refused": {}}))


if __name__ == "__main__":
    unittest.main()
