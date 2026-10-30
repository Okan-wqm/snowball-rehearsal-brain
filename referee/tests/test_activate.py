"""Test 45 (asama-0/09): activation on the in-process GitHub, no git: the genesis row, the ``brain/integration``
cut, the ratchet base, the ready candidates (the good one merges, each bad one is rejected with its own reason),
one orphan ``brain/state`` commit; and group ``genesis`` (tohum/29d): the genesis row's fields and hashes.

- genesis: every payload hash recomputed here from the input bytes; the ratchet counts are the base run's
  violations; a changed input changes its hash and the row hash; refusals each on its own input;
- activation: the cut is ``main``'s head (toy) or ``base_sha`` (copy); the good candidate's file is applied and
  merged through a pull request with the gate's check; four bad candidates rejected with asama-0/08's reasons and
  a cause, nothing written for them; at most one merge (criterion 8); ``merge_paused``; a diff that does not apply
  to the base file; ``brain/state`` is an orphan holding the ledger, the signed root and ``status.md``, which the
  chain, the anchor and the status block read back;
- refusals before any write; an integration branch GitHub refuses to create; a hard stop after the cut names the
  refs written;
- ``gate.diffguard.apply``: context and removed lines must match, end of file, no fuzz;
- the command line.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import activate  # noqa: E402
import activation_world as AW  # noqa: E402
from gate import diffguard  # noqa: E402
from ledger import anchor, chain  # noqa: E402
from target import write as W  # noqa: E402

sha = AW.sha


def canon_sha(value) -> str:
    return hashlib.sha256(chain.canonical(value)).hexdigest()


def rows_of(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.decode().splitlines()]


class Genesis(unittest.TestCase):
    def gen(self, w: AW.World, req=None, main=None):
        return activate.genesis(w.files, w.request() if req is None else req, w.main if main is None else main)

    def test_every_field_and_hash(self):
        w = AW.World()
        got = self.gen(w)
        self.assertEqual(got["reasons"], [])
        row = got["row"]
        self.assertEqual((row["part"], row["kind"], row["row_id"], row["derivation"], row["trust"]),
                         ("events", "genesis", AW.CYCLE + ":genesis", "tool", "verified"))
        imports_last = w.imports.rstrip(b"\n").split(b"\n")[-1]
        imp = json.loads(imports_last)
        sec = json.loads(w.security.rstrip(b"\n").split(b"\n")[-1])
        self.assertEqual(row["payload"], {
            "target": {"id": "toy", "repo": AW.REPO, "kind": "toy", "base_sha": w.main},
            "main_sha": w.main,
            "integration": {"branch": "brain/integration", "sha": w.main},
            "seed_epoch": json.loads(w.summary)["seed_epochs"][-1],
            "import": {"line_sha256": sha(imports_last), "row_hash": imp["row_hash"], "brain_sha": "b" * 40,
                       "referee_tree_sha256": "e" * 64, "result_sha256": sha(w.result), "toy_tree_sha256": "f" * 64},
            "result": {"sha256": sha(w.result), "rekor_uuids": ["rekor-a"]},
            "policy_sha256": sha(b'{"p": 1}\n'),
            "summary_sha256": sha(w.summary),
            "profile_sha256": sha(w.profile),
            "recipe_sha256": sha(w.recipe),
            "seed_security": {"ledger_sha256": sha(w.security), "last_row_hash": sec["row_hash"]},
            "settings_sha256": {k: canon_sha(w.settings[k]) for k in ("rulesets", "apps", "actions")},
            "ratchet": {"base_run_sha256": sha(AW.BASE_RUN), "counts": {"eslint": 2}},
            "candidates": ["bad-path", "bad-ratchet", "bad-scope", "bad-test", "good"],
        })

    def test_same_input_same_row_and_each_change_shows(self):
        w = AW.World()
        first = self.gen(w)["row"]
        self.assertEqual(self.gen(AW.World())["row"], first)
        changes = {
            "policy_sha256": lambda w: w.files.update({"policy.json": b'{"p": 2}\n'}),
            "profile_sha256": lambda w: w.files.update({"profile.json": w.profile + b" "}),
            "recipe_sha256": lambda w: w.files.update({"recipe.json": w.recipe + b" "}),
            "settings_sha256": lambda w: w.settings["actions"].update(enabled=True),
            "result": lambda w: None,  # changed through the request below
        }
        for field, change in changes.items():
            w = AW.World()
            change(w)
            req = w.request()
            if field == "result":
                req["rekor_uuids"] = ["rekor-b"]
            row = self.gen(w, req)["row"]
            self.assertNotEqual(row["payload"][field], first["payload"][field], field)
            for other in set(first["payload"]) - {field}:
                self.assertEqual(row["payload"][other], first["payload"][other], (field, other))

    def test_the_last_seed_epoch(self):
        w = AW.World()
        summary = json.loads(w.files["summary.json"])
        later = {"commit": "5" * 40, "spec_tohum_sha256": "6" * 64, "seed_sha256": "7" * 64,
                 "bootstrap_sha256": "8" * 64}
        summary["seed_epochs"].append(later)
        w.files["summary.json"] = json.dumps(summary).encode()
        self.assertEqual(self.gen(w)["row"]["payload"]["seed_epoch"], later)

    def test_ratchet_counts_per_tool_from_the_first_run(self):
        w = AW.World()
        w.files["base.jsonl"] = AW.run_file({"tool": "biome", "violations": [AW.violation(n) for n in (1, 2, 3, 4)]})
        self.assertEqual(self.gen(w)["row"]["payload"]["ratchet"]["counts"], {"biome": 4})

    def test_copy_is_cut_at_base_sha_whatever_main_is(self):
        w = AW.World(kind="copy")
        got = self.gen(w, main="9" * 40)
        self.assertEqual(got["reasons"], [])
        self.assertEqual(got["row"]["payload"]["integration"]["sha"], w.main)
        self.assertEqual(got["row"]["payload"]["main_sha"], "9" * 40)

    def test_refusals_each_on_its_own_input(self):
        def nondeterministic(w):
            lines = AW.BASE_RUN.split(b"\n")
            w.files["base.jsonl"] = b"\n".join(lines[:2] + [lines[2].replace(b"\"line\": 3", b"\"line\": 4")]) + b"\n"

        cases = {
            "target_unknown": (lambda w: None, {"target_id": "other"}, None),
            "toy_base_not_main": (lambda w: None, {}, "9" * 40),
            "imports_invalid": (lambda w: w.files.update({"imports.jsonl": w.imports.replace(b"\"stage\":0",
                                                                                             b"\"stage\":1")}), {}, None),
            "result_not_imported": (lambda w: w.files.update({"result.json": w.result + b" "}), {}, None),
            "security_ledger_invalid": (lambda w: w.files.update({"security-ledger.jsonl": b""}), {}, None),
            "base_run_hash_mismatch": (lambda w: None, {"base_run_sha256": "0" * 64}, None),
            "tool_nondeterministic": (nondeterministic, {}, None),
        }
        for reason, (change, override, main) in cases.items():
            w = AW.World()
            change(w)
            req = dict(w.request(), **override)
            got = self.gen(w, req, main)
            self.assertEqual(got["reasons"], [reason], reason)
            self.assertIsNone(got["row"])
        w = AW.World()
        w.files["imports.jsonl"] = b""
        self.assertEqual(self.gen(w)["reasons"], ["imports_invalid"])  # an empty chain is no import

    def test_unusable(self):
        w = AW.World()
        bad_requests = [dict(w.request(), extra=1), {k: v for k, v in w.request().items() if k != "ts"},
                        dict(w.request(), ts="2026-10-30 12:00:00"), dict(w.request(), settings={"rulesets": []}),
                        dict(w.request(), rekor_uuids=[""]), dict(w.request(), cycle_id=""), [],
                        dict(w.request(), settings=dict(w.settings, apps=[0.5]))]
        for req in bad_requests:
            with self.assertRaises(activate.Unusable, msg=req):
                self.gen(w, req)
        for name, data in (("summary.json", b"{"), ("policy.json", b"nope"), ("summary.json", b'{"targets": []}')):
            w = AW.World()
            w.files[name] = data
            with self.assertRaises(activate.Unusable, msg=name):
                self.gen(w)
        w = AW.World()
        del w.files["recipe.json"]
        with self.assertRaises(activate.Unusable):
            self.gen(w)
        w = AW.World()  # a fact of the wrong form is refused by the schema, not written
        w.files["imports.jsonl"] = AW.chained([{"ts": "t", "brain_sha": "short", "referee_tree_sha256": "e" * 64,
                                                 "result_sha256": sha(w.result)}])
        with self.assertRaises(activate.Unusable) as ctx:
            self.gen(w)
        self.assertIn("payload.import.brain_sha", str(ctx.exception))


class Activation(unittest.TestCase):
    def test_good_merges_bad_rejected_one_orphan_state(self):
        w = AW.World()
        out = w.run()
        gh = w.gh
        # the cut, then the good candidate's merge on top of it
        merge = gh.refs["brain/integration"]
        self.assertEqual(gh.commits[merge]["parents"][0], w.main)
        self.assertEqual(gh.read_file("brain/integration", "src/a.js"), AW.SOURCE.replace(b"var x", b"let x"))
        self.assertEqual(gh.refs["main"], w.main)
        good = [d for d in out["decisions"] if d["decision"] == "merge"]
        self.assertEqual([d["candidate"] for d in good], ["good"])
        self.assertEqual(good[0]["merge_sha"], merge)
        self.assertEqual(gh.pulls[good[0]["pull"]]["base"], "brain/integration")
        self.assertTrue(any(c["head_sha"] == good[0]["head_sha"] and c["conclusion"] == "success" and c["name"] == AW.GATE
                            for c in gh.checks))
        # each bad candidate: its own reason, a cause, nothing on the target
        rejects = {d["candidate"]: d["reasons"] for d in out["decisions"] if d["decision"] == "reject"}
        self.assertEqual(set(rejects), set(AW.EXPECTED_REJECTS))
        for cid, (reason, _) in AW.EXPECTED_REJECTS.items():
            self.assertIn(reason, rejects[cid], cid)
            self.assertNotIn("brain/c/" + cid, gh.refs)
        self.assertEqual(rejects["bad-test"], ["tests_red"])
        self.assertEqual(rejects["bad-ratchet"], ["ratchet_increase"])
        self.assertEqual(rejects["bad-scope"], ["scope_violation"])
        # brain/state: an orphan holding exactly the three state files
        state = gh.refs["brain/state"]
        self.assertEqual(state, out["state_sha"])
        self.assertEqual(gh.commits[state]["parents"], [])
        self.assertEqual(set(gh.trees[gh.commits[state]["tree"]]),
                         {"ledger.jsonl", "chain/root.jsonl", "status.md"})
        ledger = gh.read_file("brain/state", "ledger.jsonl")
        roots = gh.read_file("brain/state", "chain/root.jsonl")
        self.assertTrue(chain.verify_bytes(ledger)["valid"])
        rows = rows_of(ledger)
        self.assertEqual([(r["kind"], r["row_id"]) for r in rows], [
            ("genesis", AW.CYCLE + ":genesis"), ("integration_cut", AW.CYCLE + ":cut"),
            ("reject", AW.CYCLE + ":c:bad-path"), ("reject", AW.CYCLE + ":c:bad-ratchet"),
            ("reject", AW.CYCLE + ":c:bad-scope"), ("reject", AW.CYCLE + ":c:bad-test"),
            ("merge", AW.CYCLE + ":c:good"), ("status", AW.CYCLE + ":status")])
        self.assertEqual(rows[1]["payload"], {"branch": "brain/integration", "main_sha": w.main, "base_sha": w.main})
        for r in rows[2:6]:
            self.assertEqual(r["cause"], AW.EXPECTED_REJECTS[r["payload"]["candidate"]][1], r["row_id"])
        self.assertEqual(rows[6]["payload"], {"candidate": "good", "path": "src/a.js", "pull": good[0]["pull"],
                                              "head_sha": good[0]["head_sha"], "merge_sha": merge})
        self.assertNotIn("cause", rows[6])
        self.assertEqual([r["row_hash"] for r in rows], out["row_hashes"])
        # the signed root verifies as the next D1 reads it
        rekor = {"entries": {out["entry"]["uuid"]: {"hash": out["entry"]["hash"], "identity": "referee@example"}}}
        self.assertEqual(anchor.verify(ledger, roots, rekor, "referee@example"), {"valid": True, "reasons": []})
        self.assertEqual(w.signer.payloads, [out["root"].encode()])
        status = gh.read_file("brain/state", "status.md").decode()
        self.assertIn('Last decision: "merge", row "%s:c:good"' % AW.CYCLE, status)
        # refs written: the cut, the candidate branch, the merge into the cut, the state; never main
        self.assertEqual(sorted(set(w.wr.written)), ["refs/heads/brain/c/good", "refs/heads/brain/integration",
                                                     "refs/heads/brain/state"])

    def test_the_ratchet_base_is_the_referees_run(self):
        w = AW.World()
        w.run()
        genesis = rows_of(w.gh.read_file("brain/state", "ledger.jsonl"))[0]
        self.assertEqual(genesis["payload"]["ratchet"], {"base_run_sha256": sha(AW.BASE_RUN), "counts": {"eslint": 2}})
        # a candidate whose koş took another base run is not judged against it
        w = AW.World()
        good = w.cand("good")
        hashes = json.loads(good["hashes.json"])
        hashes["base.jsonl"] = sha(b"another base run")
        good["hashes.json"] = json.dumps(hashes).encode()
        out = w.run()
        self.assertEqual([d["reasons"] for d in out["decisions"] if d["candidate"] == "good"],
                         [["artefact_hash_mismatch"]])

    def test_at_most_one_merge(self):
        w = AW.World()
        twin = dict(w.cand("good"), id="good2")
        w.candidates.append(twin)
        out = w.run()
        by = {d["candidate"]: d for d in out["decisions"]}
        self.assertEqual(by["good"]["decision"], "merge")
        self.assertEqual(by["good2"]["reasons"], ["sentinel_pending"])
        self.assertNotIn("brain/c/good2", w.gh.refs)

    def test_merge_paused_rejects_everything(self):
        for control in ({"merge_paused": True}, {}):
            w = AW.World()
            w.control = control
            out = w.run()
            self.assertEqual({d["decision"] for d in out["decisions"]}, {"reject"})
            self.assertIn("merge_paused", [d for d in out["decisions"] if d["candidate"] == "good"][0]["reasons"])
            self.assertEqual(w.gh.refs["brain/integration"], w.main)

    def test_a_diff_that_does_not_apply_to_the_base_file(self):
        w = AW.World()
        w.gh.refs["main"] = w.main = w.gh.seed_commit("toy-main-2", files={
            "src/a.js": b"// toy\nvar x = 1;\nvar y = 2;\nmodule.exports = { x };\n", "eslint.config.js": b"x\n"})
        summary = json.loads(w.files["summary.json"])
        summary["targets"][0]["base_sha"] = w.main
        w.files["summary.json"] = json.dumps(summary).encode()
        good = w.cand("good")
        good["diff.patch"] = AW.diff("src/a.js", 2, ["var x = 1;", "var y = 2;", "module.exports = { x, y };"],
                                     ["let x = 1;", "var y = 2;", "module.exports = { x, y };"])
        empty = AW.run_file({"tool": "eslint", "violations": []})
        good["cand.jsonl"] = empty
        # fix range covers the whole hunk so only the base content can refuse it
        base = AW.run_file({"tool": "eslint", "violations": [AW.violation(2, fix=[2, 4]), AW.violation(3)]})
        w.files["base.jsonl"] = base
        hashes = json.loads(good["hashes.json"])
        hashes["base.jsonl"], hashes["cand.jsonl"] = sha(base), sha(empty)
        good["hashes.json"] = json.dumps(hashes).encode()
        w.candidates = [good]
        out = w.run()
        self.assertEqual(out["decisions"][0]["reasons"], ["patch_does_not_apply"])
        self.assertEqual(w.gh.refs["brain/integration"], w.main)
        w2 = AW.World()
        w2.candidates = [w2.cand("good")]
        w2.read_base = lambda path: None
        self.assertEqual(w2.run()["decisions"][0]["reasons"], ["base_file_missing"])

    def test_unusable_candidate_and_bad_id_are_rejected(self):
        w = AW.World()
        w.cand("good")["finding.json"] = b"{"
        i = w.candidates.index(w.cand("bad-scope"))
        w.candidates[i] = dict(w.candidates[i], id="../main")
        req = w.request()
        out = w.run(req)
        by = {d["candidate"]: d["reasons"] for d in out["decisions"]}
        self.assertEqual(by["good"], ["candidate_unusable"])
        self.assertEqual(by["../main"], ["candidate_id_invalid"])
        rows = rows_of(w.gh.read_file("brain/state", "ledger.jsonl"))
        self.assertEqual({r["cause"] for r in rows if r["kind"] == "reject" and
                          r["payload"]["candidate"] in ("good", "../main")}, {"unknown"})

    def test_copy_target_cut_at_base_sha(self):
        w = AW.World(kind="copy")
        later = w.gh.seed_commit("mirror", [w.main], files={"src/a.js": b"changed\n"})
        w.gh.refs["main"] = later
        out = w.run()
        self.assertEqual(out["main_sha"], later)
        self.assertEqual(w.gh.commits[w.gh.refs["brain/integration"]]["parents"][0], w.main)


class Refusals(unittest.TestCase):
    def assert_nothing_written(self, w: AW.World):
        self.assertEqual(w.writes(), [])

    def test_genesis_refusal_writes_nothing(self):
        w = AW.World()
        w.files["result.json"] = b"{}"
        with self.assertRaises(W.Refused) as ctx:
            w.run()
        self.assertEqual(ctx.exception.reasons, ["result_not_imported"])
        self.assert_nothing_written(w)

    def test_already_activated_and_integration_exists(self):
        w = AW.World()
        w.gh.refs["brain/state"] = w.main
        w.gh.refs["brain/integration"] = w.main
        with self.assertRaises(W.Refused) as ctx:
            w.run()
        self.assertEqual(ctx.exception.reasons, ["already_activated", "integration_exists"])
        self.assert_nothing_written(w)
        w = AW.World()
        w.run()
        before = len(w.writes())
        with self.assertRaises(W.Refused) as ctx:
            w.run()  # a second activation over the first
        self.assertEqual(ctx.exception.reasons, ["already_activated", "integration_exists"])
        self.assertEqual(len(w.writes()), before)

    def test_wrong_repo_and_missing_base_commit(self):
        w = AW.World()
        summary = json.loads(w.files["summary.json"])
        summary["targets"][0]["repo"] = "acme/other"
        w.files["summary.json"] = json.dumps(summary).encode()
        with self.assertRaises(W.Refused) as ctx:
            w.run()
        self.assertEqual(ctx.exception.reasons, ["target_repo_mismatch"])
        self.assert_nothing_written(w)
        w = AW.World(kind="copy")
        summary = json.loads(w.files["summary.json"])
        summary["targets"][0]["base_sha"] = "7" * 40
        w.files["summary.json"] = json.dumps(summary).encode()
        with self.assertRaises(W.ApiError):
            w.run()
        self.assert_nothing_written(w)

    def test_candidates_must_be_the_requests(self):
        w = AW.World()
        req = w.request()
        w.candidates.pop()
        with self.assertRaises(activate.Unusable):
            w.run(req)
        for name, data in (("profile.json", b'{"security_paths": []}'), ("recipe.json", b'{"inputs": "src/"}')):
            w = AW.World()
            w.files[name] = data
            with self.assertRaises(activate.Unusable, msg=name):
                w.run()
            self.assert_nothing_written(w)
        w = AW.World()
        req = w.request()
        w.candidates[0] = dict(w.candidates[0], id=None)
        with self.assertRaises(activate.Unusable):
            w.run(req)
        w = AW.World()
        w.candidates.append(dict(w.cand("good")))  # the same id twice
        with self.assertRaises(activate.Unusable):
            w.run()
        self.assert_nothing_written(w)

    def test_github_refuses_to_create_the_integration_branch(self):
        w = AW.World(create_denied=("brain/integration",))
        with self.assertRaises(W.ApiError):
            w.run()
        self.assertEqual(w.writes(), [("POST", "/repos/%s/git/refs" % AW.REPO)])
        self.assertEqual(sorted(w.gh.refs), ["main"])

    def test_hard_stop_after_the_cut_names_what_was_written(self):
        w = AW.World()
        w.signer = anchor.FakeSigner(False)
        with self.assertRaises(activate.HardStop) as ctx:
            w.run()
        self.assertIsInstance(ctx.exception, activate.append.HardStop)
        self.assertEqual(ctx.exception.written, ["refs/heads/brain/c/good", "refs/heads/brain/integration"])
        self.assertNotIn("brain/state", w.gh.refs)
        w = AW.World()
        w.cand("good")["diff.patch"] = AW.diff("src/a.js", 2, ["var x = 1;"], ["let x = 1; // ghp_" + "a" * 36])
        out = w.run()  # a secret in a diff is the gate's reject, not a stop
        self.assertIn("secret_in_diff", [d for d in out["decisions"] if d["candidate"] == "good"][0]["reasons"])


class Apply(unittest.TestCase):
    def block(self, text: str) -> dict:
        return diffguard.parse(text)[0]

    def test_applies_at_its_own_line_only(self):
        old = b"a\nb\nc\nb\n"
        d = "diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -4 +4 @@\n-b\n+B\n"
        self.assertEqual(diffguard.apply(self.block(d), old), b"a\nb\nc\nB\n")
        with self.assertRaises(diffguard.DiffError):  # the same line elsewhere is not searched for
            diffguard.apply(self.block(d), b"a\nb\nc\nx\n")
        ctx = "diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -1,3 +1,3 @@\n a\n-b\n+B\n c\n"
        self.assertEqual(diffguard.apply(self.block(ctx), old), b"a\nB\nc\nb\n")
        with self.assertRaises(diffguard.DiffError):  # a context line that differs
            diffguard.apply(self.block(ctx), b"z\nb\nc\nb\n")

    def test_insertion_deletion_and_end_of_file(self):
        old = b"a\nb\n"
        ins = "diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -1,0 +2 @@\n+x\n"
        self.assertEqual(diffguard.apply(self.block(ins), old), b"a\nx\nb\n")
        dele = "diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -2 +1,0 @@\n-b\n"
        self.assertEqual(diffguard.apply(self.block(dele), old), b"a\n")
        no_eol = "diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -2 +2 @@\n-b\n+b\n\\ No newline at end of file\n"
        self.assertEqual(diffguard.apply(self.block(no_eol), old), b"a\nb")
        with self.assertRaises(diffguard.DiffError):  # the base has no newline, the diff says it has
            diffguard.apply(self.block("diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -2 +2 @@\n-b\n+c\n"), b"a\nb")
        with self.assertRaises(diffguard.DiffError):  # beyond the end of the file
            diffguard.apply(self.block("diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -5 +5 @@\n-b\n+c\n"), old)

    def test_only_an_in_place_text_change(self):
        for d in ("diff --git a/f b/g\nsimilarity index 90%\nrename from f\nrename to g\n",
                  "diff --git a/f b/f\nnew file mode 100644\n--- /dev/null\n+++ b/f\n@@ -0,0 +1 @@\n+x\n",
                  "diff --git a/f b/f\nold mode 100644\nnew mode 100755\n"):
            with self.assertRaises(diffguard.DiffError, msg=d):
                diffguard.apply(self.block(d), b"x\n")

    def test_bytes_that_are_not_utf8_are_kept(self):
        old = b"\xff\nb\n"
        d = "diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -2 +2 @@\n-b\n+c\n"
        self.assertEqual(diffguard.apply(self.block(d), old), b"\xff\nc\n")


class CommandLine(unittest.TestCase):
    def run_cli(self, w: AW.World, req: dict, args=None):
        with tempfile.TemporaryDirectory() as tmp:
            for name, data in w.files.items():
                with open(os.path.join(tmp, name), "wb") as fh:
                    fh.write(data)
            proc = subprocess.run([sys.executable, "-m", "activate"] + (args or ["genesis", tmp]),
                                  input=json.dumps(req).encode(), cwd=REFEREE, capture_output=True, timeout=60)
        return proc.returncode, json.loads(proc.stdout.decode().splitlines()[-1]), proc.stderr.decode()

    def test_genesis_row_and_its_hash(self):
        w = AW.World()
        code, out, _ = self.run_cli(w, dict(w.request(), main_sha=w.main))
        self.assertEqual(code, 0)
        self.assertEqual(out["row"], activate.genesis(w.files, w.request(), w.main)["row"])
        self.assertEqual(out["row_hash"], chain.row_hash(dict(out["row"], prev_hash=chain.ZERO_HASH)))
        w.settings["apps"].append({"slug": "undeclared"})
        code2, out2, _ = self.run_cli(w, dict(w.request(), main_sha=w.main))
        self.assertEqual(code2, 0)
        self.assertNotEqual(out2["row_hash"], out["row_hash"])
        self.assertNotEqual(out2["row"]["payload"]["settings_sha256"]["apps"],
                            out["row"]["payload"]["settings_sha256"]["apps"])

    def test_refused_and_unusable(self):
        w = AW.World()
        code, out, _ = self.run_cli(w, dict(w.request(), main_sha="9" * 40))
        self.assertEqual((code, out), (1, {"ok": False, "reasons": ["toy_base_not_main"], "row": None,
                                           "row_hash": None}))
        for req, args in ((w.request(), None), (dict(w.request(), main_sha="short"), None),
                          (dict(w.request(), main_sha=w.main), ["genesis"]),
                          (dict(w.request(), main_sha=w.main), ["genesis", "/nonexistent"])):
            code, out, err = self.run_cli(w, req, args)
            self.assertEqual((code, out), (2, {"ok": False, "reasons": [], "row": None, "row_hash": None}), args)
            self.assertTrue(err.startswith("unusable input"), err)


if __name__ == "__main__":
    unittest.main()
