"""Test 46 (asama-0/09), MF17, D3 -> D5: ``yaz``'s decision (``loop.decide``, ``loop.job run yaz``) on what the
``kos`` job wrote with the fake runner, and on the pulled candidates (asama-0/08 criteria 1-8).

- one cycle: a good candidate merges; a test-breaking and a ratchet-raising one are rejected for their own reasons;
  merges are serial (a second good candidate carries ``sentinel_pending``); the order is the ids' code-point order;
- criterion 1 through ``gate.diffguard`` with the profile ``kos`` staged with: a manifest change, and an operator
  excluded path, which 29g says ``excluded_dirs`` carries (and ``kos`` refused too: ``kos:base_file_missing``);
- criterion 2: a diff that adds a key id is ``secret_in_diff`` (MF2 reached through MF8);
- criteria 7 and 8 from the inputs: ``merge_paused`` missing or true, an unfinished sentinel, and an unread state
  (``None``: ``sentinel_state_unread``, no merge);
- the artifacts by hash: a changed byte of a run file, a missing ``hashes.json``, an unusable diff or finding;
- the job: ``loop.job run yaz`` reads ``control.json`` and the two artifacts, gives every candidate
  ``sentinel_state_unread`` (D1's state read is not wired) and ends ``cycle_not_wired`` after D5; a refused
  artifact, a missing ``control.json`` and an unusable recipe.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loop import decide as E  # noqa: E402
from loop import job as J  # noqa: E402
from loop import pulled as P  # noqa: E402
from profile_tree import write_tree  # noqa: E402
from test_kos import BREAKS_TEST, GOOD, RAISES, diff, recipe  # noqa: E402
from test_loop_kos import TARGET, Base, RedAs, candidate  # noqa: E402

KEY_ID = "AK" + "IA" + "Q7" * 8  # a key id shape (MF2's floor), spelled so this file holds none
LEAK = diff("pkg/a.js", ["var a = 1;"], ["let a = 1; // " + KEY_ID])
MANIFEST = diff("pkg/package.json", ['{"name": "pkg", "version": "1.0.0"}'], ['{"name": "pkg", "version": "1.0.1"}'])
C_JS = diff("pkg/c.js", ["const d = 5;"], ["const d = 6;"])
OPEN = {"merge_paused": False}


class Cycle(Base):
    """``kos`` then ``yaz`` in one ``$RUNNER_TEMP``, as the workflow hands the artifacts over."""

    def kos(self, cands: dict, target: dict | None = None, units=None) -> None:
        self.write_pulled(cands, target=target, units=units)
        out = J.run("kos", {"RUNNER_TEMP": self.temp}, runner=RedAs())
        self.assertEqual(out["reason"], "cycle_not_wired", out)
        shutil.move(os.path.join(self.temp, "out", "results"), self.results())

    def results(self, *parts) -> str:
        return os.path.join(self.temp, "in", "results", *parts)

    def tree(self) -> str:
        tree = os.path.join(self.base, "tree-%d" % len(os.listdir(self.base)))
        P.extract_tree(os.path.join(self.pulled, P.TREE), tree)
        return tree

    def decide(self, control=None, unfinished=(), unit=None) -> dict:
        art = P.read(self.pulled)
        return E.decide(art, unit or recipe(), self.tree(), self.results(), OPEN if control is None else control,
                        None if unfinished is None else list(unfinished))

    def reasons(self, got: dict) -> dict:
        return {cid: d["reasons"] for cid, d in got["decisions"].items()}


class OneCycle(Cycle):
    def test_good_merges_bad_rejected_for_their_reasons(self):
        self.kos({"good": candidate(GOOD), "breaks": candidate(BREAKS_TEST), "raises": candidate(RAISES)})
        got = self.decide()
        self.assertEqual(got["merge"], "good")
        self.assertEqual(got["decisions"]["good"], {"decision": "merge", "reasons": []})
        self.assertEqual(got["decisions"]["breaks"], {"decision": "reject", "reasons": ["tests_red"]})
        # judged after good, which is this cycle's merge: its sentinel is unfinished (tohum/07)
        self.assertEqual(got["decisions"]["raises"]["decision"], "reject")
        self.assertIn("ratchet_increase", got["decisions"]["raises"]["reasons"])
        self.assertIn("sentinel_pending", got["decisions"]["raises"]["reasons"])

    def test_merges_are_serial_in_code_point_order(self):
        self.kos({"b2": candidate(GOOD), "B1": candidate(GOOD), "a3": candidate(GOOD)})
        got = self.decide()
        self.assertEqual(got["merge"], "B1")  # "B" < "a" < "b" by code point
        self.assertEqual(self.reasons(got), {"B1": [], "a3": ["sentinel_pending"], "b2": ["sentinel_pending"]})

    def test_a_rejected_candidate_does_not_take_the_merge(self):
        self.kos({"a": candidate(BREAKS_TEST), "b": candidate(GOOD)})
        got = self.decide()
        self.assertEqual((got["merge"], self.reasons(got)), ("b", {"a": ["tests_red"], "b": []}))

    def test_no_candidates(self):
        self.kos({})
        self.assertEqual(self.decide(), {"decisions": {}, "merge": None})


class Criteria(Cycle):
    def test_criterion_1_a_manifest(self):
        self.kos({"good": candidate(MANIFEST)})
        reasons = self.reasons(self.decide())["good"]
        self.assertIn("manifest:pkg/package.json", reasons)

    def test_criterion_1_the_operators_excluded_path_reaches_diffguard(self):
        # pkg/c.js: a file the fixture's lint does not read, so the base still runs without it
        write_tree(self.src, {"pkg/c.js": "const d = 5;\n"})
        self.kos({"edit": candidate(C_JS)}, target=dict(TARGET, excluded_paths=["pkg/c.js"]))
        art = P.read(self.pulled)
        self.assertIn("pkg/c.js", E.guard_profile(self.tree(), art)["excluded_dirs"])
        reasons = self.reasons(self.decide())["edit"]
        self.assertIn("excluded_path:pkg/c.js", reasons)
        self.assertIn("kos:base_file_missing", reasons)  # the staging left it out of the worktree too

    def test_criterion_1_without_operator_exclusion_the_path_is_not_excluded(self):
        write_tree(self.src, {"pkg/c.js": "const d = 5;\n"})
        self.kos({"edit": candidate(C_JS)})
        reasons = self.reasons(self.decide())["edit"]
        self.assertFalse([r for r in reasons if r.startswith(("excluded_path", "kos:"))], reasons)

    def test_criterion_1_a_security_path(self):
        write_tree(self.src, {"pkg/auth.js": "var s = 1;\n"})
        self.kos({"sec": candidate(diff("pkg/auth.js", ["var s = 1;"], ["let s = 1;"]))})
        art = P.read(self.pulled)
        self.assertIn("pkg/auth.js", E.guard_profile(self.tree(), art)["security_paths"])
        self.assertIn("security_path:pkg/auth.js", self.reasons(self.decide())["sec"])

    def test_criterion_2_a_secret_in_the_diff(self):
        self.kos({"leak": candidate(LEAK)})
        self.assertIn("secret_in_diff", self.reasons(self.decide())["leak"])

    def test_criterion_7_merge_paused(self):
        self.kos({"good": candidate(GOOD)})
        for control in ({}, {"merge_paused": True}, {"merge_paused": "false"}, None, []):
            with self.subTest(control=control):
                got = self.decide(control={} if control is None else control)
                self.assertEqual((got["merge"], self.reasons(got)), (None, {"good": ["merge_paused"]}))

    def test_criterion_8_an_unfinished_sentinel(self):
        self.kos({"good": candidate(GOOD)})
        got = self.decide(unfinished=["a" * 40])
        self.assertEqual((got["merge"], self.reasons(got)), (None, {"good": ["sentinel_pending"]}))

    def test_an_unread_state_merges_nothing(self):
        self.kos({"good": candidate(GOOD), "breaks": candidate(BREAKS_TEST)})
        got = self.decide(unfinished=None)
        self.assertEqual((got["merge"], self.reasons(got)),
                         (None, {"good": ["sentinel_state_unread"], "breaks": ["sentinel_state_unread", "tests_red"]}))


class Artifacts(Cycle):
    def test_a_changed_byte_of_a_run_file(self):
        self.kos({"good": candidate(GOOD)})
        with open(self.results("c", "good", "cand.jsonl"), "ab") as fh:
            fh.write(b"\n")
        self.assertIn("artefact_hash_mismatch", self.reasons(self.decide())["good"])

    def test_no_hashes_file(self):
        self.kos({"good": candidate(GOOD)})
        os.remove(self.results("c", "good", "hashes.json"))
        self.assertEqual(self.reasons(self.decide())["good"], ["artefact_hash_mismatch"])

    def test_kos_refusal_is_the_candidates_reason(self):
        stale = diff("pkg/a.js", ["var zzz = 9;"], ["let zzz = 9;"])
        self.kos({"stale": candidate(stale)})
        reasons = self.reasons(self.decide())["stale"]
        self.assertIn("kos:patch_does_not_apply", reasons)
        self.assertIn("artefact_hash_mismatch", reasons)

    def test_missing_index_entry(self):
        self.kos({"good": candidate(GOOD)})
        with open(self.results("index.json"), "w") as fh:
            json.dump({"candidates": {}}, fh)
        self.assertIn("kos:missing", self.reasons(self.decide())["good"])

    def test_unusable_diff_and_finding(self):
        bad_finding = dict(candidate(GOOD), **{"finding.json": b'{"rule_id": 1}'})
        self.kos({"nodiff": candidate(b"not a diff\n"), "nofinding": bad_finding})
        reasons = self.reasons(self.decide())
        self.assertEqual(reasons["nodiff"], ["diff_unusable"])
        self.assertIn("candidate_unusable", reasons["nofinding"])

    def test_an_unusable_recipe_judges_nothing(self):
        self.kos({"good": candidate(GOOD)})
        with self.assertRaises(E.Unusable):
            self.decide(unit=recipe(inputs="pkg"))


class YazJob(Cycle):
    def control(self, doc) -> None:
        write_tree(os.path.join(self.temp, "control"), {"control.json": doc})

    def test_the_job_runs_d5_and_merges_nothing_without_the_state(self):
        self.kos({"good": candidate(GOOD), "breaks": candidate(BREAKS_TEST)})
        self.control(OPEN)
        out = J.run("yaz", {"RUNNER_TEMP": self.temp, "WRITER_TOKEN": "x"})
        self.assertEqual((out["ok"], out["reason"], out["done"], out["merge"]), (False, "cycle_not_wired", ["D5"], None))
        self.assertEqual(self.reasons(out), {"good": ["sentinel_state_unread"],
                                             "breaks": ["sentinel_state_unread", "tests_red"]})

    def test_the_control_file_is_read(self):
        self.kos({"good": candidate(GOOD)})
        self.control({"merge_paused": True})
        out = J.run("yaz", {"RUNNER_TEMP": self.temp})
        self.assertIn("merge_paused", out["decisions"]["good"]["reasons"])
        os.remove(os.path.join(self.temp, "control", "control.json"))
        with self.assertRaises(J.Unusable):
            J.run("yaz", {"RUNNER_TEMP": self.temp})

    def test_a_refused_artifact(self):
        self.kos({"good": candidate(GOOD)})
        self.control(OPEN)
        with open(os.path.join(self.pulled, "candidates/good/diff.patch"), "ab") as fh:
            fh.write(b" ")
        out = J.run("yaz", {"RUNNER_TEMP": self.temp})
        self.assertEqual((out["reason"], out["reasons"]), ("pulled_invalid", ["hash_mismatch:candidates/good/diff.patch"]))

    def test_two_units(self):
        self.kos({})
        self.control(OPEN)
        shutil.rmtree(self.pulled)
        self.write_pulled(units={"units": [recipe(), recipe(unit_id="b")]})
        self.assertEqual(J.run("yaz", {"RUNNER_TEMP": self.temp})["reason"], "units_not_one")

    def test_an_unusable_recipe(self):
        self.kos({"good": candidate(GOOD)})
        self.control(OPEN)
        shutil.rmtree(self.pulled)
        self.write_pulled({"good": candidate(GOOD)}, units={"units": [recipe(inputs="pkg")]})
        with self.assertRaises(J.Unusable):
            J.run("yaz", {"RUNNER_TEMP": self.temp})

    def test_command_line(self):
        env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "SYSTEMROOT")}
        proc = subprocess.run([sys.executable, "-m", "loop.job", "run", "yaz"], cwd=REFEREE,
                              env=dict(env, RUNNER_TEMP=self.temp), capture_output=True)
        self.assertEqual((proc.returncode, json.loads(proc.stdout)), (2, {"ok": False, "reason": None}))


if __name__ == "__main__":
    unittest.main()
