"""The toy target's ready candidates (``candidates/toy/<cid>/``) against the referee's own gate (asama-0/08 cycle
row 2 and the acceptance rule, asama-0/13, asama-0/10a #merge and #ret, tohum/26c's candidate shape).

What is proven here: the five candidates are one good and asama-0/08's four bad ones (outside the fix range, a
ratchet increase, a broken test, a forbidden path); each ``finding.json`` names a violation of the toy's base
run as the referee's converter (``runner.lint_record``) reads it, with that violation's ``fix`` as ``fix_range``
and ``tool_output_sha256`` the sha256 of the ``base.jsonl`` the converter writes from it (the file whose hash
genesis records as ``ratchet.base_run_sha256``); the captured tool outputs of ``tests/fixtures/toy-candidates/``
belong to the tree each ``diff.patch`` makes; and the referee's acceptance rule (``activate.decide``: MF7 then
MF8) gives each candidate exactly the decision and reason its ``expect.json`` states, alone and inside one
activation on the in-process GitHub holding the toy's tree (MF18), where the good candidate's merged file is the
patched file.

Inputs that are not the referee's, stated: the fixtures were captured by ``tests/capture_toy_candidates.py``
with ESLint 10.13.0 and node 22.23.4 outside a container (the recipe's own commands); ``checks.json`` is built
here from ``node --test``'s TAP lines (one entry per top-level test), because no stage 0 module turns a test
run into ``checks.json`` yet (spec-036); the red control is given as ``fail`` (its result is ``koş``'s, MF3).
Not proven here: that ``koş``'s contained runs give the same outputs (asama-0/10a #birim, #merge, #ret).

Run from the brain root: ``python -m unittest discover -s tests -p 'test_toy_candidates.py'``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "referee"))
sys.path.insert(0, os.path.join(ROOT, "referee", "tests"))

import activate  # noqa: E402
import activation_world as AW  # noqa: E402
from gate import diffguard  # noqa: E402
from profile import derive as D  # noqa: E402
from runner import lint_record as R  # noqa: E402

TOY = os.path.join(ROOT, "tests", "fixtures", "toy-repo")
CANDIDATES = os.path.join(ROOT, "candidates", "toy")
CAPTURED = os.path.join(ROOT, "tests", "fixtures", "toy-candidates")
BASE_OUTPUT = os.path.join(ROOT, "tests", "fixtures", "toy-repo-eslint.json")
FINDING_FIELDS = {"rule_id", "path", "line", "fix_range", "tool_output_sha256"}
CONTROL = {"kill_switch": False, "merge_paused": False}
# asama-0/08 row 2's four bad kinds, each as the gate's reason
BAD_KINDS = {"scope_violation", "ratchet_increase", "tests_red"}
TAP_TOP = re.compile(r"^(ok|not ok) \d+ - (.+)$")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: str):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def raw(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def ids() -> list[str]:
    return sorted(os.listdir(CANDIDATES))


def recipe() -> dict:
    return load(os.path.join(ROOT, "targets", "toy", "units.json"))["units"][0]


def profile() -> dict:
    d = D.derive(TOY, None, None)
    return {"security_paths": d["security_paths"], "excluded_dirs": d["excluded_dirs"]}


def base_record() -> dict:
    return R.record(raw(BASE_OUTPUT), TOY)


def base_run() -> bytes:
    return R.run_file([base_record()] * 3)


def patched(cid: str) -> tuple[str, bytes]:
    """The path and post-image of the candidate's one changed file, applied to the toy's base file."""
    blocks = diffguard.parse(raw(os.path.join(CANDIDATES, cid, "diff.patch")).decode("utf-8"))
    assert len(blocks) == 1, cid
    return blocks[0]["old"], diffguard.apply(blocks[0], raw(os.path.join(TOY, blocks[0]["old"])))


def checks(test_stdout: str) -> bytes:
    tests = [{"id": m.group(2), "status": "pass" if m.group(1) == "ok" else "fail"}
             for m in map(TAP_TOP.match, test_stdout.splitlines()) if m]
    return json.dumps({"tests": tests, "red_control": "fail"}).encode()


def candidate(cid: str) -> dict:
    """The candidate as ``activate`` reads it: its brain files plus the ``koş`` results built from the capture."""
    got = load(os.path.join(CAPTURED, cid + ".json"))
    path, content = patched(cid)
    work = tempfile.mkdtemp()
    try:
        shutil.rmtree(work)
        shutil.copytree(TOY, work)
        with open(os.path.join(work, path), "wb") as fh:
            fh.write(content)
        rec = R.record(got["lint_stdout"].encode("utf-8"), work)
    finally:
        shutil.rmtree(work)
    cand = {"id": cid, "finding.json": raw(os.path.join(CANDIDATES, cid, "finding.json")),
            "diff.patch": raw(os.path.join(CANDIDATES, cid, "diff.patch")),
            "cand.jsonl": R.run_file([rec] * 3), "checks.json": checks(got["test_stdout"])}
    cand["hashes.json"] = json.dumps({"base.jsonl": sha(base_run()), "cand.jsonl": sha(cand["cand.jsonl"]),
                                      "checks.json": sha(cand["checks.json"])}).encode()
    return cand


def expected(cid: str) -> list[str]:
    exp = load(os.path.join(CANDIDATES, cid, "expect.json"))
    return [] if exp["decision"] == "merge" else [exp["reason"]]


class Shape(unittest.TestCase):
    def test_one_good_and_the_four_bad_kinds(self):
        exps = {cid: load(os.path.join(CANDIDATES, cid, "expect.json")) for cid in ids()}
        self.assertEqual(sorted(e["decision"] for e in exps.values()), ["merge"] + ["reject"] * 4)
        for cid, e in exps.items():
            self.assertEqual(set(e), {"decision"} if e["decision"] == "merge" else {"decision", "reason"}, cid)
        reasons = [e["reason"] for e in exps.values() if e["decision"] == "reject"]
        self.assertEqual(len(set(reasons)), 4)
        self.assertEqual(BAD_KINDS, set(reasons) & BAD_KINDS)
        # the fourth: a path criterion 1 forbids (diffguard's <reason>:<path>)
        forbidden = [r for r in reasons if r not in BAD_KINDS]
        self.assertEqual(len(forbidden), 1)
        self.assertEqual(diffguard.path_reasons(forbidden[0].split(":", 1)[1], ["100644"], profile(), recipe()),
                         forbidden)

    def test_each_candidate_is_the_three_files_of_26c(self):
        for cid in ids():
            self.assertEqual(sorted(os.listdir(os.path.join(CANDIDATES, cid))),
                             ["diff.patch", "expect.json", "finding.json"], cid)
            self.assertEqual(set(load(os.path.join(CANDIDATES, cid, "finding.json"))), FINDING_FIELDS, cid)
            self.assertEqual(activate.write.branch_reasons(activate.CANDIDATE_PREFIX + cid), [], cid)

    def test_each_diff_is_one_in_place_change_of_its_finding_path(self):
        for cid in ids():
            path, content = patched(cid)
            self.assertEqual(path, load(os.path.join(CANDIDATES, cid, "finding.json"))["path"], cid)
            self.assertNotEqual(content, raw(os.path.join(TOY, path)), cid)


class Finding(unittest.TestCase):
    def test_finding_is_a_violation_of_the_base_run_with_its_fix(self):
        violations = base_record()["violations"]
        for cid in ids():
            f = load(os.path.join(CANDIDATES, cid, "finding.json"))
            hit = [v for v in violations if (v["rule_id"], v["path"], v["line"]) == (f["rule_id"], f["path"], f["line"])]
            self.assertEqual(len(hit), 1, cid)
            self.assertEqual(f["fix_range"], hit[0]["fix"], cid)
            self.assertIsNotNone(f["fix_range"], cid)

    def test_tool_output_sha256_is_the_base_run_file(self):
        h = sha(base_run())
        for cid in ids():
            self.assertEqual(load(os.path.join(CANDIDATES, cid, "finding.json"))["tool_output_sha256"], h, cid)


class Capture(unittest.TestCase):
    def test_capture_is_of_the_patched_tree_with_the_recipe_commands(self):
        unit = recipe()
        for cid in ids():
            got = load(os.path.join(CAPTURED, cid + ".json"))
            path, content = patched(cid)
            self.assertEqual(got["changed_sha256"], {path: sha(content)}, cid)
            self.assertEqual((got["lint_cmd"], got["test_cmd"]), (unit["lint_cmd"], unit["test_cmd"]), cid)
            self.assertEqual((got["eslint"], got["node"], got["lint_runs_identical"]), ("v10.13.0", "v22.23.4", 3))
            candidate(cid)  # lint_record refuses an output whose sources are not this tree (source_mismatch)

    def test_a_capture_of_another_tree_is_refused(self):
        got = load(os.path.join(CAPTURED, "good.json"))
        with self.assertRaises(R.RecordError) as ctx:
            R.record(got["lint_stdout"].encode("utf-8"), TOY)  # the unpatched tree
        self.assertIn("source_mismatch:textkit/src/stats.js", ctx.exception.reasons)

    def test_checks_count_every_top_level_test(self):
        for cid in ids():
            tests = json.loads(candidate(cid)["checks.json"])["tests"]
            self.assertEqual(len(tests), 8, cid)
            red = [t["id"] for t in tests if t["status"] == "fail"]
            self.assertEqual(red, ["slugify lowers, joins words with dashes and trims dashes"] if cid == "bad-test"
                             else [], cid)


class Decision(unittest.TestCase):
    def test_each_alone_gets_exactly_its_expected_reasons(self):
        for cid in ids():
            got = activate.decide(candidate(cid), base_run(), profile(), recipe(), CONTROL, [], lambda p: raw(
                os.path.join(TOY, p)))
            self.assertEqual(got["reasons"], expected(cid), cid)
            if not got["reasons"]:
                self.assertEqual(got["content"], patched(cid)[1])

    def test_the_bad_ones_are_rejected_for_their_own_fault_only(self):
        """bad-ratchet fixes its target and adds violations; bad-test with green tests and bad-path without the
        security path rule would merge: what rejects each is its fault, not a side effect."""
        rec = json.loads(candidate("bad-ratchet")["cand.jsonl"].splitlines()[0])
        self.assertFalse([v for v in rec["violations"] if (v["rule_id"], v["path"], v["line"])
                          == ("prefer-template", "textkit/src/greet.js", 2)])
        self.assertEqual((len(rec["violations"]), len(base_record()["violations"])), (8, 7))
        cand = candidate("bad-test")
        cand["checks.json"] = candidate("good")["checks.json"]
        cand["hashes.json"] = json.dumps({"base.jsonl": sha(base_run()), "cand.jsonl": sha(cand["cand.jsonl"]),
                                          "checks.json": sha(cand["checks.json"])}).encode()
        read = lambda p: raw(os.path.join(TOY, p))  # noqa: E731
        self.assertEqual(activate.decide(cand, base_run(), profile(), recipe(), CONTROL, [], read)["reasons"], [])
        loose = dict(profile(), security_paths=[])
        self.assertEqual(activate.decide(candidate("bad-path"), base_run(), loose, recipe(), CONTROL, [], read)
                         ["reasons"], [])


class ToyWorld(AW.World):
    """``activation_world``'s in-process GitHub, with the toy fixture's tree on ``main`` and its real inputs."""

    def __init__(self):
        super().__init__()
        files = {}
        for top, dirs, names in os.walk(TOY):
            for n in names:
                p = os.path.join(top, n)
                files[os.path.relpath(p, TOY).replace(os.sep, "/")] = raw(p)
        self.main = self.gh.seed_commit("toy-fixture", files=files)
        self.gh.refs["main"] = self.main
        summary = json.loads(self.summary)
        summary["targets"][0]["base_sha"] = self.main
        self.files.update({"summary.json": json.dumps(summary).encode(), "profile.json": json.dumps(profile()).encode(),
                           "recipe.json": json.dumps(recipe()).encode(), "base.jsonl": base_run()})
        self.candidates = [candidate(cid) for cid in ids()]


class Activation(unittest.TestCase):
    def test_one_activation_merges_the_good_and_rejects_each_bad_with_its_reason(self):
        w = ToyWorld()
        out = w.run()
        decisions = {d["candidate"]: d for d in out["decisions"]}
        self.assertEqual(sorted(decisions), ids())
        for cid in ids():
            self.assertEqual(decisions[cid]["reasons"], expected(cid), cid)
        merged = [cid for cid in ids() if decisions[cid]["decision"] == "merge"]
        self.assertEqual(merged, ["good"])
        path, content = patched("good")
        head = w.gh.refs[activate.INTEGRATION]
        self.assertEqual(w.gh.blobs[w.gh.trees[w.gh.commits[head]["tree"]][path]], content)
        rows = [json.loads(line) for line in out["files"]["ledger.jsonl"].decode().splitlines()]
        genesis = next(r for r in rows if r["kind"] == "genesis")
        self.assertEqual(genesis["payload"]["ratchet"],
                         {"base_run_sha256": load(os.path.join(CANDIDATES, "good", "finding.json"))["tool_output_sha256"],
                          "counts": {"eslint": 7}})
        causes = {r["payload"]["candidate"]: r["cause"] for r in rows if r["kind"] == "reject"}
        self.assertEqual(causes, {"bad-path": "scope_violation", "bad-ratchet": "lint_regression",
                                  "bad-scope": "scope_violation", "bad-test": "test_regression"})


if __name__ == "__main__":
    unittest.main()
