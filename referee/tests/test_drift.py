"""Test 24 (asama-0/09), stage 1 MF6: ``drift.check`` and its place in ``yaz`` (``loop.job.yaz_drift``, the job's first step).

- ``Check``: on the facts setup leaves (``activation_world.facts``, a toy and a copy) there is no reason and exactly
  the reads the module names are sent, each once, all ``GET``; each change of one fact gives its one reason
  (``CASES``: a rule removed or weakened, a ruleset made bypassable, ``main`` left writable, the writer App on another
  set of repositories, a required check another App may answer, a workflow on the toy, among them one triggered on
  ``brain/**`` with a secret, Actions on for the copy); several changes give their reasons sorted; a caller writing
  to another repository than the summary's is refused before any read; a read that fails or is malformed, and a
  summary without the target, are unusable;
- ``Genesis``: ``activate.genesis`` gives the same reasons for every case (the facts have one reader);
- ``Cli``: the command's three exits and lines;
- ``Yaz``: ``loop.job run yaz`` with one fact of its target changed serves no target, writes nothing and ends
  ``drift`` with the reasons (five cases over test 24's three kinds); on the facts setup left it is written after
  every one of the check's reads. With two targets served: a drift on the second leaves the first unwritten too,
  both targets' reads precede the first write to either, both drifted name each one's reasons with the job's the
  first served's; a target whose ``pulled`` is refused is sent no request. The check is of the repository D6
  writes to; a fact that cannot be read, a checkout without the summary, a summary without the target and a
  missing writer token are unusable with nothing written;
- ``YazGenesis``: a genesis cycle's target with a fact changed stops the job the same way, nothing written.

Not tested, because not built (``drift.check`` "Out of scope"): a diff against values recorded in the summary, other
Apps' installations, the activity API's actors, the referee repository's own settings, workflow triggers.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import activate as AC  # noqa: E402
import activation_world as AW  # noqa: E402
import test_loop_write as TLW  # noqa: E402
import yaz_world as YW  # noqa: E402
from drift import check as DC  # noqa: E402
from loop import job as J  # noqa: E402
from target import branches as B  # noqa: E402

P = "/repos/%s" % AW.REPO
STATE, INTEGRATION, MAIN = (P + "/rules/branches/" + b for b in (B.STATE, B.INTEGRATION, "main"))
WORKFLOWS, PERMISSIONS, INSTALLED = P + "/actions/workflows", P + "/actions/permissions", "/installation/repositories"
READS = {"toy": ["/app", INSTALLED, STATE, INTEGRATION, MAIN, P + "/rulesets/1", P + "/rulesets/2", P + "/rulesets/3",
                 WORKFLOWS],
         "copy": ["/app", INSTALLED, STATE, INTEGRATION, MAIN, P + "/rulesets/1", P + "/rulesets/2",
                  P + "/rulesets/3", PERMISSIONS]}


def without(kind: str):
    return lambda rules: [r for r in rules if r["type"] != kind]


def checks(**params):
    """The ``required_status_checks`` rule's parameters changed."""
    def change(rules):
        return [dict(r, parameters=dict(r["parameters"], **params)) if r["type"] == "required_status_checks" else r
                for r in rules]
    return change


def bypass(value):
    return lambda ruleset: dict(ruleset, current_user_can_bypass=value)


def review(count):
    return lambda rules: [dict(r, parameters={"required_approving_review_count": count})
                          if r["type"] == "pull_request" else r for r in rules]


# A workflow of the target that runs on the brain's branches with a secret (test 24's third item), as the list
# endpoint names one: the list is all ``drift.check`` reads of it.
SECRET_WORKFLOW = {"id": 7, "name": "deploy", "path": ".github/workflows/deploy.yml", "state": "active"}

# name: (kind, the path whose answer changes, the change, the one reason)
CASES = {
    "state deletion rule removed": ("toy", STATE, without("deletion"), "state_rules_missing"),
    "state non_fast_forward rule removed": ("toy", STATE, without("non_fast_forward"), "state_rules_missing"),
    "state rules all removed": ("copy", STATE, lambda rules: [], "state_rules_missing"),
    "integration deletion rule removed": ("toy", INTEGRATION, without("deletion"), "integration_rules_missing"),
    "integration non_fast_forward rule removed": ("toy", INTEGRATION, without("non_fast_forward"),
                                                  "integration_rules_missing"),
    "integration pull_request rule removed": ("toy", INTEGRATION, without("pull_request"),
                                              "integration_rules_missing"),
    "integration required check removed": ("copy", INTEGRATION, without("required_status_checks"),
                                           "integration_rules_missing"),
    "required check answered by another App": (
        "toy", INTEGRATION, checks(required_status_checks=[{"context": AW.GATE, "integration_id": AW.APP_ID + 1}]),
        "integration_check_not_writer"),
    "a second required check of any App": (
        "toy", INTEGRATION, checks(required_status_checks=[{"context": AW.GATE, "integration_id": AW.APP_ID},
                                                           {"context": "other"}]),
        "integration_check_not_writer"),
    "required checks emptied": ("toy", INTEGRATION, checks(required_status_checks=[]),
                                "integration_check_not_writer"),
    "required check not strict": ("copy", INTEGRATION, checks(strict_required_status_checks_policy=False),
                                  "integration_check_not_writer"),
    "state ruleset bypassable": ("toy", P + "/rulesets/1", bypass("always"), "rules_bypassable"),
    "integration ruleset bypassable by pull request": ("toy", P + "/rulesets/2", bypass("pull_requests_only"),
                                                       "rules_bypassable"),
    "integration ruleset exempt": ("copy", P + "/rulesets/2", bypass("exempt"), "rules_bypassable"),
    "main ruleset bypassable": ("toy", P + "/rulesets/3", bypass("always"), "main_writable"),
    "main without a review": ("toy", MAIN, review(0), "main_writable"),
    "main without rules": ("copy", MAIN, lambda rules: [], "main_writable"),
    "the App on a repository setup did not declare": (
        "toy", INSTALLED, lambda body: dict(body, repositories=body["repositories"] + [{"full_name": "acme/other"}]),
        "app_scope"),
    "the App no longer on the target": ("copy", INSTALLED, lambda body: dict(body, repositories=[]), "app_scope"),
    "a workflow on the toy": ("toy", WORKFLOWS, lambda body: dict(body, workflows=[SECRET_WORKFLOW]),
                              "toy_workflows"),
    "Actions on for the copy": ("copy", PERMISSIONS, lambda body: {"enabled": True, "allowed_actions": "all"},
                                "copy_actions_enabled"),
    "the copy's Actions answer without enabled": ("copy", PERMISSIONS, lambda body: {}, "copy_actions_enabled"),
}


def change(gh, path: str, how) -> None:
    status, body = gh.overrides[("GET", path)]
    gh.overrides[("GET", path)] = (status, how(copy.deepcopy(body)))


def world(kind: str = "toy", *changes) -> AW.World:
    w = AW.World(kind)
    for path, how in changes:
        change(w.gh, path, how)
    return w


def check(w: AW.World, target="toy", repo=None) -> dict:
    return DC.check(w.gh, w.files["summary.json"], target, repo)


class Check(unittest.TestCase):
    def test_setup_s_facts_give_no_reason_and_only_the_named_reads_are_sent(self):
        for kind in ("toy", "copy"):
            w = world(kind)
            self.assertEqual(check(w), {"ok": True, "hard_stop": False, "reasons": []})
            self.assertEqual(w.gh.requests, [("GET", path, None) for path in READS[kind]])
            self.assertEqual(check(w, repo=AW.REPO)["reasons"], [])
        # the summary as ``cek`` reads it (no ``seed_epochs``: genesis' own field) is enough
        w = world("copy")
        w.files["summary.json"] = json.dumps({"targets": json.loads(w.files["summary.json"])["targets"]}).encode()
        self.assertEqual(check(w)["reasons"], [])
        # main closed by an update rule alone
        w = world("toy", (MAIN, lambda rules: [{"type": "update", "ruleset_id": 3}]))
        self.assertEqual(check(w)["reasons"], [])

    def test_each_changed_fact_is_its_reason(self):
        for name, (kind, path, how, reason) in CASES.items():
            w = world(kind, (path, how))
            self.assertEqual(check(w), {"ok": False, "hard_stop": True, "reasons": [reason]}, name)
            self.assertEqual({m for m, _, _ in w.gh.requests}, {"GET"}, name)

    def test_every_reason_of_the_module_has_a_case(self):
        with open(DC.__file__, encoding="utf-8") as fh:
            source = fh.read()
        named = {r for r in ("app_scope", "state_rules_missing", "integration_rules_missing",
                             "integration_check_not_writer", "rules_bypassable", "main_writable", "toy_workflows",
                             "copy_actions_enabled") if '"%s"' % r in source}
        self.assertEqual(named, {reason for _, _, _, reason in CASES.values()})
        self.assertEqual(len(named), 8)

    def test_several_changes_give_their_reasons_sorted(self):
        w = world("toy", (WORKFLOWS, CASES["a workflow on the toy"][2]), (STATE, without("deletion")),
                  (P + "/rulesets/3", bypass("always")), (INSTALLED, CASES["the App no longer on the target"][2]))
        self.assertEqual(check(w)["reasons"], ["app_scope", "main_writable", "state_rules_missing", "toy_workflows"])
        # a ruleset shared by brain/state and main that is bypassable opens both
        w = world("copy", (MAIN, lambda rules: [dict(r, ruleset_id=1) for r in rules]),
                  (P + "/rulesets/1", bypass("always")))
        self.assertEqual(check(w)["reasons"], ["main_writable", "rules_bypassable"])

    def test_the_scope_is_compared_with_every_target_of_the_summary(self):
        both = [{"id": "toy", "repo": AW.REPO, "kind": "toy", "base_sha": None},
                {"id": "copy", "repo": "acme/copy", "kind": "copy", "base_sha": "c" * 40}]
        w = world("toy")
        w.files["summary.json"] = YW.summary(both)
        self.assertEqual(check(w)["reasons"], ["app_scope"])  # installed on one of the two declared
        change(w.gh, INSTALLED, lambda body: dict(body, repositories=[{"full_name": "acme/copy"},
                                                                      {"full_name": AW.REPO}]))
        self.assertEqual(check(w)["reasons"], [])

    def test_a_caller_writing_to_another_repository_is_refused_before_any_read(self):
        w = world("toy")
        self.assertEqual(check(w, repo="acme/other"),
                         {"ok": False, "hard_stop": True, "reasons": ["target_repo_mismatch"]})
        self.assertEqual(check(w, repo=AW.REPO.upper())["reasons"], ["target_repo_mismatch"])
        self.assertEqual(w.gh.requests, [])

    def test_a_read_that_fails_or_is_malformed_is_unusable(self):
        for kind in ("toy", "copy"):
            for path in READS[kind]:
                for answer in ((404, {"message": "Not Found"}), (500, {}), (200, "text"), (200, None)):
                    w = world(kind)
                    w.gh.overrides[("GET", path)] = answer
                    with self.assertRaises(DC.Unusable, msg=(kind, path, answer)):
                        check(w)
        for path, body in ((STATE, [{"type": "deletion"}]), (STATE, [{"type": "deletion", "ruleset_id": "1"}]),
                           (MAIN, [{"ruleset_id": 3}]), (INTEGRATION, ["deletion"]),
                           (INSTALLED, {"repositories": [{"name": "t"}]}), (INSTALLED, {}),
                           (WORKFLOWS, {"total_count": 0})):
            w = world("toy")
            w.gh.overrides[("GET", path)] = (200, body)
            with self.assertRaises(DC.Unusable, msg=(path, body)):
                check(w)

    def test_a_summary_without_the_target_is_unusable_and_nothing_is_read(self):
        w = world("toy")
        entry = json.loads(w.files["summary.json"])["targets"][0]
        for target in ("other", None, 1):
            with self.assertRaises(DC.Unusable):
                check(w, target)
        for summary in (b"", b"[]", b'{"targets": []}', YW.summary([]), YW.summary([entry, entry]),
                        YW.summary([dict(entry, kind="general")]), YW.summary([dict(entry, repo=None)]),
                        YW.summary([dict(entry, kind="copy", base_sha="abc")]),
                        b'{"seed_epochs": [1], "targets": [], "targets": []}'):
            w.files["summary.json"] = summary
            with self.assertRaises(DC.Unusable, msg=summary):
                check(w)
        self.assertEqual(w.gh.requests, [])


class Genesis(unittest.TestCase):
    """``activate.genesis`` reads the same facts through ``drift.check``'s rules."""

    def test_genesis_gives_the_same_reason_for_every_case(self):
        for name, (kind, path, how, reason) in CASES.items():
            w = world(kind, (path, how))
            out = AC.genesis(w.gh, w.files, "toy")
            self.assertEqual((out["hard_stop"], out["reasons"], out["payload"]), (True, [reason], None), name)

    def test_genesis_sends_the_check_s_reads_and_the_toy_s_main(self):
        for kind, more in (("toy", [P + "/git/ref/heads/main"]), ("copy", [])):
            w = world(kind)
            self.assertTrue(AC.genesis(w.gh, w.files, "toy")["ok"])
            self.assertEqual(sorted(p for _, p, _ in w.gh.requests), sorted(READS[kind] + more))
        self.assertIs(AC.Unusable, DC.Unusable)


class Cli(unittest.TestCase):
    def run_cli(self, w: AW.World, stdin: str = '{"target": "toy"}', args=None):
        with tempfile.TemporaryDirectory() as tmp:
            api, summary = os.path.join(tmp, "api.json"), os.path.join(tmp, "summary.json")
            with open(api, "w") as fh:
                json.dump({"%s %s" % key: body for key, (_, body) in w.gh.overrides.items()}, fh)
            with open(summary, "wb") as fh:
                fh.write(w.files["summary.json"])
            proc = subprocess.run([sys.executable, "-m", "drift.check"] + (["check", api, summary] if args is None
                                                                           else args),
                                  input=stdin.encode(), capture_output=True, cwd=REFEREE)
        return proc.returncode, json.loads(proc.stdout), proc.stderr.decode()

    def test_the_three_exits(self):
        self.assertEqual(self.run_cli(world("copy")), (0, {"ok": True, "hard_stop": False, "reasons": []}, ""))
        code, line, err = self.run_cli(world("toy", (WORKFLOWS, CASES["a workflow on the toy"][2])))
        self.assertEqual((code, line, err), (1, {"ok": False, "hard_stop": True, "reasons": ["toy_workflows"]}, ""))
        w = world("toy")
        del w.gh.overrides[("GET", "/app")]  # not in the record: the replay answers 404
        fault = {"ok": False, "hard_stop": True, "reasons": None}
        for got in (self.run_cli(w), self.run_cli(world(), stdin='{"target": "toy", "x": 1}'),
                    self.run_cli(world(), stdin='{"target": "other"}'), self.run_cli(world(), args=["check"]),
                    self.run_cli(world(), args=["check", "/nonexistent/api", "/nonexistent/summary"])):
            self.assertEqual((got[0], got[1]), (2, fault))
            self.assertTrue(got[2].startswith("unusable input: "), got[2])


class Recorded:
    """A transport that names every request it passes on, in order: ``sent`` is ``(method, path)``."""

    def __init__(self, transport) -> None:
        self.transport, self.sent = transport, []

    def __call__(self, method: str, path: str, body):
        self.sent.append((method, path))
        return self.transport(method, path, body)


def reads_of(repo: str, kind: str = "toy") -> list[tuple]:
    """The check's reads that name ``repo`` (all but ``/app`` and the installation's list)."""
    return [("GET", path.replace(AW.REPO, repo)) for path in READS[kind] if AW.REPO in path]


class Yaz(TLW.D6):
    """``yaz``'s first step (``test_loop_write.D6``'s worlds: t1, a toy at ``yaz_world.REPO``, or t1 and t2)."""

    def ready(self) -> None:
        self.kos({"good": TLW.candidate(TLW.GOOD)})
        self.control(TLW.OPEN)
        self.github()

    def job(self, **env) -> dict:
        """The job's line (``run_yaz`` of the base is its one target line)."""
        return TLW.YazBase.run_yaz(self, **env)

    def drifted(self, path: str, how, reasons: list) -> None:
        """``yaz`` with one fact changed: the job's line, no target served, nothing written; the fact is put back."""
        kept = self.gh.overrides[("GET", path)]
        change(self.gh, path, how)
        refs = dict(self.gh.refs)
        out = self.job()
        self.assertEqual((out["ok"], out["reason"], out["reasons"], out["target"], out["targets"], out["drift"]),
                         (False, "drift", reasons, "t1", [], {"checked": ["t1"], "drifted": {"t1": reasons}}), out)
        self.assertEqual((self.writes(), self.gh.refs, self.signer.payloads), ([], refs, []))
        self.gh.overrides[("GET", path)] = kept

    def test_a_drifted_target_is_not_written_and_a_clean_one_is(self):
        self.ready()
        p = "/repos/%s" % YW.REPO
        # test 24's three: a rule that differs from setup, an undeclared App, a workflow on the brain's branches
        self.drifted(p + "/rules/branches/" + B.INTEGRATION, without("required_status_checks"),
                     ["integration_rules_missing"])
        self.drifted(p + "/rulesets/1", bypass("always"), ["rules_bypassable"])
        self.drifted(INSTALLED, lambda body: dict(body, repositories=body["repositories"] + [{"full_name": "a/b"}]),
                     ["app_scope"])
        self.drifted(p + "/rules/branches/" + B.INTEGRATION,
                     checks(required_status_checks=[{"context": B.CHECK, "integration_id": 1}]),
                     ["integration_check_not_writer"])
        self.drifted(p + "/actions/workflows", lambda body: dict(body, workflows=[SECRET_WORKFLOW]),
                     ["toy_workflows"])
        # the same cycle on the facts setup left: written, after every one of the check's reads
        del self.gh.requests[:]
        job = self.job()
        out = self.line(job)
        self.assertEqual((out["ok"], out["done"], out["merge"], job["drift"]),
                         (True, ["D5", "D6"], "good", {"checked": ["t1"], "drifted": {}}), job)
        sent = [(m, path) for m, path, _ in self.gh.requests]
        first_write = next(i for i, (m, _) in enumerate(sent) if m != "GET")
        reads = [("GET", path.replace(AW.REPO, YW.REPO)) for path in READS["toy"]]
        self.assertEqual([s for s in sent[:first_write] if s in reads], reads)
        self.assertEqual([s for s in sent[first_write:] if s in reads], [])

    def two(self) -> dict:
        """t1 then t2 served (``two_targets``), both responses written: the targets' GitHubs."""
        ghs = self.two_targets({"good": TLW.candidate(TLW.GOOD)})
        for tid in ("t1", "t2"):
            YW.write_response(self.temp, tid, TLW.HEADS, [YW.cost_row(snapshot=TLW.HEADS[B.INTEGRATION])], at=tid)
        return ghs

    def run_two(self, ghs: dict) -> tuple[dict, list]:
        transport = Recorded(TLW.Router(ghs))
        out = J.run("yaz", YW.env(self.temp, self.workspace), transport=transport, signer=self.signer,
                    now=lambda: YW.NOW)
        return out, transport.sent

    # tohum/01b:57-58: before the cycle's first write, whichever target the drift is on
    def test_a_drift_on_a_later_target_leaves_the_earlier_one_unwritten(self):
        ghs = self.two()
        workflows = "/repos/acme/t2/actions/workflows"
        change(ghs["t2"], workflows, lambda body: dict(body, workflows=[SECRET_WORKFLOW]))
        out, sent = self.run_two(ghs)
        self.assertEqual((out["ok"], out["reason"], out["reasons"], out["target"], out["targets"]),
                         (False, "drift", ["toy_workflows"], "t2", []), out)
        self.assertEqual(out["drift"], {"checked": ["t1", "t2"], "drifted": {"t2": ["toy_workflows"]}})
        self.assertEqual(([s for s in sent if s[0] != "GET"], self.signer.payloads), ([], []))
        for gh in ghs.values():
            self.assertEqual((gh.refs[B.STATE], gh.refs[B.INTEGRATION]), (TLW.HEADS[B.STATE], TLW.HEADS[B.INTEGRATION]))
        # both drifted: every target's reasons are named, the job's are the first served's
        change(ghs["t1"], "/repos/acme/t1/rulesets/1", bypass("always"))
        out, sent = self.run_two(ghs)
        self.assertEqual((out["reason"], out["reasons"], out["target"], out["targets"]),
                         ("drift", ["rules_bypassable"], "t1", []), out)
        self.assertEqual(out["drift"]["drifted"], {"t1": ["rules_bypassable"], "t2": ["toy_workflows"]})
        self.assertEqual([s for s in sent if s[0] != "GET"], [])

    def test_every_served_target_is_read_before_the_first_write_to_any(self):
        ghs = self.two()
        out, sent = self.run_two(ghs)
        self.assertEqual((out["ok"], out["drift"]), (True, {"checked": ["t1", "t2"], "drifted": {}}), out)
        first_write = next(i for i, (m, _) in enumerate(sent) if m != "GET")
        reads = reads_of("acme/t1") + reads_of("acme/t2")
        self.assertEqual([s for s in sent[:first_write] if s in reads], reads)
        self.assertEqual([s for s in sent[first_write:] if s in reads], [])
        self.assertEqual({p.split("/")[3] for m, p in sent[first_write:] if m != "GET"}, {"t1", "t2"})

    def test_a_target_refused_for_its_pulled_is_not_read(self):
        ghs = self.two()
        os.remove(os.path.join(self.temp, "in", "pulled", "t2", "units.json"))
        out, sent = self.run_two(ghs)
        self.assertEqual((out["ok"], out["target"], out["reason"], [t["ok"] for t in out["targets"]]),
                         (False, "t2", "pulled_invalid", [True, False]), out)
        self.assertEqual(out["drift"], {"checked": ["t1"], "drifted": {}})
        self.assertEqual(ghs["t2"].requests, [])

    def test_the_check_is_of_the_repository_d6_writes_to(self):
        self.ready()
        entry = json.loads(YW.summary())["targets"][0]
        TLW.write_tree(self.workspace, {J.SUMMARY: YW.summary([dict(entry, repo="acme/elsewhere")]).decode()})
        out = self.job()
        self.assertEqual((out["ok"], out["reason"], out["reasons"], out["targets"]),
                         (False, "drift", ["target_repo_mismatch"], []))
        self.assertEqual(self.gh.requests, [])

    def test_a_fact_that_cannot_be_read_is_unusable_and_nothing_is_written(self):
        self.ready()
        self.gh.overrides[("GET", "/app")] = (401, {"message": "Bad credentials"})
        with self.assertRaisesRegex(J.Unusable, r"\Ayaz: drift: GET /app answered 401\Z"):
            self.job()
        self.gh.overrides.update(AW.facts("toy", YW.REPO))
        os.remove(os.path.join(self.workspace, "setup", "summary.json"))
        with self.assertRaisesRegex(J.Unusable, r"\Ayaz: setup/summary.json: "):
            self.job()
        TLW.write_tree(self.workspace, {J.SUMMARY: YW.summary([]).decode()})
        with self.assertRaisesRegex(J.Unusable, r"\Ayaz: drift: target 't1' is not exactly once in targets\[\]\Z"):
            self.job()
        self.assertEqual(self.writes(), [])
        # without the writer's token the check is not started
        del self.gh.requests[:]
        with self.assertRaisesRegex(J.Unusable, r"\Ayaz: WRITER_TOKEN is not set\Z"):
            self.job(WRITER_TOKEN="")
        self.assertEqual(self.gh.requests, [])


class YazGenesis(TLW.Genesis):
    """A genesis cycle's target is read with the others, before the job serves any."""

    def test_a_genesis_target_s_drift_stops_the_job_before_its_activation(self):
        self.main_at()
        self.kos({"good": TLW.candidate(TLW.GOOD)})
        self.control(TLW.OPEN)
        self.github()
        change(self.gh, "/repos/%s/rulesets/1" % YW.REPO, bypass("always"))
        out = TLW.YazBase.run_yaz(self)
        self.assertEqual((out["ok"], out["reason"], out["reasons"], out["target"], out["targets"]),
                         (False, "drift", ["rules_bypassable"], "t1", []), out)
        self.assertEqual(self.writes(), [])


def load_tests(loader, standard, pattern):
    """This module's own tests: ``Yaz`` inherits ``test_loop_write.StateBase``'s world, not its bases' tests."""
    suite = unittest.TestSuite()
    for case in (Check, Genesis, Cli, Yaz, YazGenesis):
        names = [n for n in loader.getTestCaseNames(case) if n in vars(case)]
        suite.addTests(case(n) for n in names)
    return suite
