"""Test 24 (asama-0/09), stage 1 MF6: ``drift.check`` and its place in ``yaz`` (``loop.job.yaz_drift``, the job's step after
stage 1 MF5's offline reading, ``yaz_offline``).

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
  missing writer token are unusable with nothing written. The order with MF5 (``Order``): the offline reading is
  made once per job with no request sent before it; a harness that imports the client stops the job as
  ``harness_online`` with no request sent, no target named and ``pulled`` not opened (the same job without its
  ``pulled`` ends the same way, and ``pulled_invalid`` on the code as it is);
- ``YazGenesis``: a genesis cycle's target with a fact changed stops the job the same way, nothing written.
- ``YazPolicy`` (tohum/29v "Döngüde eksik anahtar", ``loop.job.yaz_policy``): with two targets served, a policy
  of the second without one required path serves no target and writes nothing on either (``policy_unusable``, the
  path named), after drift's reads of both; a drift beside it is the job's reason, and it comes before a stale
  operator check. On one target: each of the twelve required paths absent, and each judged kind off its form (a
  JSON float where a six-decimal string or an integer belongs), stops the job the same way with nothing written
  and no signature; the policy put back is written.

- ``Baseline`` (tohum/01c): a summary without the top-level ``drift`` object, with one inside ``targets[]``, with a
  ``drift`` not of the form or without the target is unusable and nothing is read; a writer App of another id is
  ``writer_app_changed``; a branch whose rule content differs from the recorded hash is ``rules_changed:<branch>``
  (a parameter today's reasons do not read, a rule added), while the order of the rules, their ``ruleset_id`` and
  fields other than ``type`` and ``parameters`` change nothing; the hash is the page's recipe, computed here by
  ``hashlib`` over literal bytes; a branch the baseline names beyond the three is read and compared; an operator check
  more than 7 days old is ``stale`` with no hard stop and every read still made, exactly 7 days is not, and in
  ``yaz`` it ends the job ``operator_check_stale`` with nothing written (a drift beside it is the job's reason).

Not tested, because not built (``drift.check`` "Out of scope"): the baseline's ``rulesets``, ``hashes``,
``visibility`` and ``activity`` beyond their form, other Apps' installations, the referee repository's own settings,
workflow triggers.
"""

from __future__ import annotations

import copy
import datetime
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import activate as AC  # noqa: E402
import activation_world as AW  # noqa: E402
import test_loop_write as TLW  # noqa: E402
import yaz_world as YW  # noqa: E402
from drift import check as DC  # noqa: E402
from loop import job as J  # noqa: E402
from policy import reads as R  # noqa: E402
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


def check(w: AW.World, target="toy", repo=None, now=AW.TS) -> dict:
    return DC.check(w.gh, w.files["summary.json"], target, now, repo)


def recorded(path: str, reason: str) -> list:
    """The reasons of a case of ``CASES``: its own and, when the answer changed is a branch's rules, the baseline's."""
    branch = path.rsplit("/rules/branches/", 1)[1:]
    return sorted([reason] + ["rules_changed:" + b for b in branch])


def rebased(w: AW.World, how) -> AW.World:
    """``w`` with its summary's ``drift`` changed by ``how`` (the object in, the object out)."""
    summary = json.loads(w.files["summary.json"])
    summary["drift"] = how(summary["drift"])
    w.files["summary.json"] = json.dumps(summary).encode()
    return w


def later(seconds: int, since: str = AW.CHECKED_AT) -> str:
    return (DC.moment(since) + datetime.timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


WEEK = 7 * 24 * 3600


class Check(unittest.TestCase):
    def test_setup_s_facts_give_no_reason_and_only_the_named_reads_are_sent(self):
        for kind in ("toy", "copy"):
            w = world(kind)
            self.assertEqual(check(w), {"ok": True, "hard_stop": False, "reasons": [], "stale": False})
            self.assertEqual(w.gh.requests, [("GET", path, None) for path in READS[kind]])
            self.assertEqual(check(w, repo=AW.REPO)["reasons"], [])
        # the summary as ``cek`` reads it (no ``seed_epochs``: genesis' own field) is enough
        w = world("copy")
        whole = json.loads(w.files["summary.json"])
        w.files["summary.json"] = json.dumps({"targets": whole["targets"], "drift": whole["drift"]}).encode()
        self.assertEqual(check(w)["reasons"], [])
        # main closed by an update rule alone (today's reason is none; the recorded content is another)
        w = world("toy", (MAIN, lambda rules: [{"type": "update", "ruleset_id": 3}]))
        self.assertEqual(check(w)["reasons"], ["rules_changed:main"])

    def test_each_changed_fact_is_its_reason(self):
        for name, (kind, path, how, reason) in CASES.items():
            w = world(kind, (path, how))
            self.assertEqual(check(w), {"ok": False, "hard_stop": True, "reasons": recorded(path, reason),
                                        "stale": False}, name)
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
        self.assertEqual(check(w)["reasons"], ["app_scope", "main_writable", "rules_changed:brain/state",
                                               "state_rules_missing", "toy_workflows"])
        # a ruleset shared by brain/state and main that is bypassable opens both
        w = world("copy", (MAIN, lambda rules: [dict(r, ruleset_id=1) for r in rules]),
                  (P + "/rulesets/1", bypass("always")))
        self.assertEqual(check(w)["reasons"], ["main_writable", "rules_bypassable"])  # a ruleset's id is no content

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
                         {"ok": False, "hard_stop": True, "reasons": ["target_repo_mismatch"], "stale": False})
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


def drop(key: str):
    return lambda drift: {k: v for k, v in drift.items() if k != key}


def put(*keys, value):
    """The baseline with ``value`` at the path ``keys``."""
    def how(drift):
        out = copy.deepcopy(drift)
        at = out
        for key in keys[:-1]:
            at = at[key]
        at[keys[-1]] = value
        return out
    return how


# what is not 01c's form, each one change of the baseline setup records
MALFORMED = {
    "not an object": lambda d: [d],
    "null": lambda d: None,
    **{"without " + key: drop(key) for key in ("writer_app_id", "targets", "activity", "hashes", "visibility",
                                                "operator_checked_at")},
    "the draft's apps[]": put("apps", value=[]),
    "the draft's referee_workflow_permission": put("referee_workflow_permission", value="read"),
    "writer_app_id a string": put("writer_app_id", value=str(AW.APP_ID)),
    "writer_app_id a boolean": put("writer_app_id", value=True),
    "targets a list": put("targets", value=[]),
    "a target without rules": put("targets", "toy", value={"rulesets": [1]}),
    "a target without rulesets": put("targets", "toy", value={"rules": {}}),
    "a target with another key": put("targets", "toy", "kind", value="toy"),
    "rulesets not a list": put("targets", "toy", "rulesets", value={"1": 1}),
    "a ruleset id a string": put("targets", "toy", "rulesets", value=["1"]),
    "rules a list": put("targets", "toy", "rules", value=[]),
    "a rules hash in upper case": put("targets", "toy", "rules", "main", value="A" * 64),
    "a rules hash too short": put("targets", "toy", "rules", "main", value="a" * 63),
    "a rules key that is no branch name": put("targets", "toy", "rules", "../../../orgs/acme", value="a" * 64),
    "activity without not_before": put("activity", value={"operator_logins": []}),
    "activity with another key": put("activity", "window", value=1),
    "operator_logins a string": put("activity", "operator_logins", value="operator"),
    "an empty login": put("activity", "operator_logins", value=[""]),
    "not_before without a zone": put("activity", "not_before", value="2026-10-30T00:00:00"),
    "not_before no date": put("activity", "not_before", value="2026-02-30T00:00:00Z"),
    "hashes without seats": put("hashes", value={"constitutional_sha256": "a" * 64, "vectors_sha256": "b" * 64}),
    "genesis' policy_sha256 among the hashes": put("hashes", "policy_sha256", value="a" * 64),
    "a hash not hex": put("hashes", "vectors_sha256", value="g" * 64),
    "visibility internal": put("visibility", AW.REPO, value="internal"),
    "visibility a list": put("visibility", value=["public"]),
    "operator_checked_at with an offset": put("operator_checked_at", value="2026-10-30T00:00:00+00:00"),
    "operator_checked_at no date": put("operator_checked_at", value="2026-13-01T00:00:00Z"),
    "operator_checked_at a number": put("operator_checked_at", value=1761782400),
}


class Baseline(unittest.TestCase):
    """tohum/01c: the summary's ``drift`` object, what is compared with it and the operator's check."""

    def test_a_summary_without_the_baseline_is_unusable_and_nothing_is_read(self):
        w = world("toy")
        summary = json.loads(w.files["summary.json"])
        w.files["summary.json"] = json.dumps({k: v for k, v in summary.items() if k != "drift"}).encode()
        with self.assertRaisesRegex(DC.Unusable, r"\Asummary.json carries no drift baseline\Z"):
            check(w)
        # never inside targets[]: neither instead of the top level's nor beside it
        inside = [dict(summary["targets"][0], drift=summary["drift"])]
        for doc in ({"targets": inside}, dict(summary, targets=inside)):
            w.files["summary.json"] = json.dumps(doc).encode()
            with self.assertRaises(DC.Unusable, msg=doc):
                check(w)
        self.assertEqual(w.gh.requests, [])

    def test_a_baseline_not_of_the_form_is_unusable_and_nothing_is_read(self):
        for name, how in MALFORMED.items():
            w = rebased(world("toy"), how)
            with self.assertRaisesRegex(DC.Unusable, r"\Asummary.json: drift", msg=name):
                check(w)
            self.assertEqual(w.gh.requests, [], name)
        # the form itself, with no login, no ruleset and an empty rules map, is read
        w = rebased(world("toy"), put("activity", "operator_logins", value=[]))
        self.assertEqual(check(rebased(w, put("targets", "toy", value={"rulesets": [], "rules": {}})))["reasons"], [])

    def test_a_baseline_without_the_target_is_unusable(self):
        w = rebased(world("toy"), lambda d: dict(d, targets={"other": d["targets"]["toy"]}))
        with self.assertRaisesRegex(DC.Unusable, r"\Asummary.json: drift.targets has no 'toy'\Z"):
            check(w)
        self.assertEqual(w.gh.requests, [])

    def test_a_writer_app_of_another_id_is_a_hard_stop(self):
        w = rebased(world("copy"), put("writer_app_id", value=AW.APP_ID + 1))
        self.assertEqual(check(w), {"ok": False, "hard_stop": True, "reasons": ["writer_app_changed"],
                                    "stale": False})
        # the App that answers is another: its required check is not the writer's either
        w = world("toy", ("/app", lambda app: dict(app, id=AW.APP_ID + 1)))
        self.assertEqual(check(w)["reasons"], ["integration_check_not_writer", "writer_app_changed"])
        # an id that is no integer is not the recorded integer, whatever it equals
        for app_id, recorded_id in ((True, 1), (str(AW.APP_ID), AW.APP_ID), (None, AW.APP_ID)):
            w = rebased(world("toy", ("/app", lambda app: dict(app, id=app_id))), put("writer_app_id", value=recorded_id))
            self.assertIn("writer_app_changed", check(w)["reasons"], app_id)
        w = world("toy", ("/app", lambda app: {"slug": app["slug"]}))
        self.assertIn("writer_app_changed", check(w)["reasons"])

    def test_a_rule_whose_content_differs_from_the_recorded_hash_is_a_hard_stop(self):
        # each a change none of today's reasons reads
        changes = {
            "main asks for more reviews": (MAIN, review(2), "main"),
            "integration asks for a review": (INTEGRATION, review(1), B.INTEGRATION),
            "a rule added to brain/state": (STATE, lambda rules: rules + [{"type": "creation", "ruleset_id": 1}],
                                            B.STATE),
            "a parameter added to a rule of brain/state": (
                STATE, lambda rules: [dict(r, parameters={"x": 1}) if r["type"] == "deletion" else r for r in rules],
                B.STATE),
            "a rule of main twice": (MAIN, lambda rules: rules + rules[:1], "main"),
            "a second required check context renamed": (
                INTEGRATION, checks(required_status_checks=[{"context": "other", "integration_id": AW.APP_ID}]),
                B.INTEGRATION),
        }
        for name, (path, how, branch) in changes.items():
            for kind in ("toy", "copy"):
                w = world(kind, (path, how))
                self.assertEqual(check(w), {"ok": False, "hard_stop": True, "reasons": ["rules_changed:" + branch],
                                            "stale": False}, name)
        # the recorded hash changed instead: the same stop, of that branch only
        w = rebased(world("toy"), put("targets", "toy", "rules", B.STATE, value="0" * 64))
        self.assertEqual(check(w)["reasons"], ["rules_changed:brain/state"])
        w = rebased(world("toy"), lambda d: put("targets", "toy", "rules", value={
            b: "0" * 64 for b in d["targets"]["toy"]["rules"]})(d))
        self.assertEqual(check(w)["reasons"], ["rules_changed:brain/integration", "rules_changed:brain/state",
                                               "rules_changed:main"])

    def test_what_is_not_rule_content_changes_nothing(self):
        same = {
            "the rules in another order": lambda rules: rules[::-1],
            "another ruleset id": lambda rules: [dict(r, ruleset_id=3) for r in rules],
            "fields beside type and parameters": lambda rules: [
                dict(r, updated_at="2026-11-19T00:00:00Z", _links={"self": {"href": "x"}}, ruleset_source="acme/x",
                     ruleset_source_type="Repository") for r in rules],
            "empty parameters written out": lambda rules: [dict({"parameters": {}}, **r) for r in rules],
        }
        for name, how in same.items():
            w = world("toy", (STATE, how), (INTEGRATION, how), (MAIN, how))
            self.assertEqual(check(w)["reasons"], [], name)
        # parameters that are null are not absent parameters
        w = world("toy", (STATE, lambda rules: [dict(r, parameters=None) for r in rules]))
        self.assertEqual(check(w)["reasons"], ["rules_changed:brain/state"])

    def test_the_hash_is_the_page_s_recipe(self):
        # brain/state as setup leaves it: two rules without parameters, reduced, ordered and written as RFC 8785
        state = hashlib.sha256(b'[{"parameters":{},"type":"deletion"},{"parameters":{},"type":"non_fast_forward"}]')
        rules = [{"type": "non_fast_forward", "ruleset_id": 9, "updated_at": "x"}, {"type": "deletion", "ruleset_id": 1}]
        self.assertEqual(DC.rules_hash(rules), state.hexdigest())
        self.assertEqual(AW.baseline({"toy": ("toy", AW.REPO)})["targets"]["toy"]["rules"][B.STATE], state.hexdigest())
        # the order is of the items' canonical forms (parameters before type), not of their types
        mixed = [{"type": "a", "parameters": {"n": 2}}, {"type": "b", "parameters": {"n": 1}}]
        want = hashlib.sha256(b'[{"parameters":{"n":1},"type":"b"},{"parameters":{"n":2},"type":"a"}]').hexdigest()
        self.assertEqual((DC.rules_hash(mixed), DC.rules_hash(mixed[::-1])), (want, want))
        # every branch of the test worlds' baseline, by this file's own arithmetic
        for kind in ("toy", "copy"):
            for (_, path), (_, body) in AW.facts(kind).items():
                if "/rules/branches/" in path:
                    self.assertEqual(DC.rules_hash(body), AW.rules_sha256(body), path)
        # a content the canonical form cannot hold has no hash
        w = world("toy", (MAIN, lambda rules: rules + [{"type": "x", "ruleset_id": 3, "parameters": {"ratio": 0.5}}]))
        with self.assertRaisesRegex(DC.Unusable, "no canonical form"):
            check(w)

    def test_every_branch_the_baseline_names_is_read_and_compared(self):
        extra = P + "/rules/branches/brain/extra"
        body = [{"type": "deletion", "ruleset_id": 1}]
        w = rebased(world("toy"), put("targets", "toy", "rules", "brain/extra", value=AW.rules_sha256(body)))
        with self.assertRaisesRegex(DC.Unusable, "brain/extra answered 404"):
            check(w)
        w.gh.overrides[("GET", extra)] = (200, body)
        del w.gh.requests[:]
        self.assertEqual(check(w)["reasons"], [])
        self.assertEqual(w.gh.requests, [("GET", path, None) for path in READS["toy"] + [extra]])
        w.gh.overrides[("GET", extra)] = (200, [])
        self.assertEqual(check(w)["reasons"], ["rules_changed:brain/extra"])
        w.gh.overrides[("GET", extra)] = (200, [{"type": "deletion"}])
        with self.assertRaises(DC.Unusable):
            check(w)
        # a branch it does not name is compared with nothing (stated out of scope): today's reasons only
        w = rebased(world("toy", (MAIN, review(2))), put("targets", "toy", "rules", value={}))
        self.assertEqual(check(w)["reasons"], [])
        # another target's entry is not this one's
        w = rebased(world("toy"), lambda d: dict(d, targets=dict(d["targets"], other={
            "rulesets": [], "rules": {"main": "0" * 64}})))
        self.assertEqual(check(w)["reasons"], [])

    def test_an_operator_check_older_than_seven_days_is_stale_and_no_hard_stop(self):
        clean = {"ok": True, "hard_stop": False, "reasons": [], "stale": False}
        for kind in ("toy", "copy"):
            self.assertEqual(check(world(kind), now=later(WEEK)), clean)  # exactly 7 days: not older
            self.assertEqual(check(world(kind), now=AW.CHECKED_AT), clean)
            w = world(kind)
            self.assertEqual(check(w, now=later(WEEK + 1)), dict(clean, ok=False, stale=True))
            self.assertEqual(w.gh.requests, [("GET", path, None) for path in READS[kind]])  # read all the same
        self.assertEqual(check(world("toy"), now="2027-10-30T00:00:00Z"), dict(clean, ok=False, stale=True))
        # the time compared is the baseline's
        w = rebased(world("toy"), put("operator_checked_at", value=later(-1)))
        self.assertEqual(check(w, now=later(WEEK))["stale"], True)
        self.assertEqual(check(rebased(w, put("operator_checked_at", value=later(60))), now=later(WEEK + 60))["stale"],
                         False)
        # a hard stop beside it stays one
        w = world("toy", (WORKFLOWS, CASES["a workflow on the toy"][2]))
        self.assertEqual(check(w, now=later(WEEK + 1)),
                         {"ok": False, "hard_stop": True, "reasons": ["toy_workflows"], "stale": True})
        self.assertEqual(check(world("toy"), repo="acme/other", now=later(WEEK + 1)),
                         {"ok": False, "hard_stop": True, "reasons": ["target_repo_mismatch"], "stale": True})

    def test_a_clock_that_is_no_time_is_unusable_and_nothing_is_read(self):
        w = world("toy")
        for now in (None, "", "2026-10-30", "2026-10-30T12:00:00", "2026-02-30T12:00:00Z", 1761825600,
                    "2026-10-30T12:00:00Z\n", datetime.datetime(2026, 10, 30)):
            with self.assertRaisesRegex(DC.Unusable, r"\Anow must be ", msg=now):
                check(w, now=now)
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
    def run_cli(self, w: AW.World, stdin: str = '{"target": "toy", "now": "%s"}' % AW.TS, args=None):
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
        clean = {"ok": True, "hard_stop": False, "reasons": [], "stale": False}
        self.assertEqual(self.run_cli(world("copy")), (0, clean, ""))
        code, line, err = self.run_cli(world("toy", (WORKFLOWS, CASES["a workflow on the toy"][2])))
        self.assertEqual((code, line, err), (1, dict(clean, ok=False, hard_stop=True, reasons=["toy_workflows"]), ""))
        # a stale operator check is the other exit 1: the line says it is no hard stop
        stale = '{"target": "toy", "now": "%s"}' % later(WEEK + 1)
        self.assertEqual(self.run_cli(world("copy"), stdin=stale), (1, dict(clean, ok=False, stale=True), ""))
        w = world("toy")
        del w.gh.overrides[("GET", "/app")]  # not in the record: the replay answers 404
        fault = {"ok": False, "hard_stop": True, "reasons": None, "stale": None}
        now = '"now": "%s"' % AW.TS
        for got in (self.run_cli(w), self.run_cli(world(), stdin='{"target": "toy", "x": 1, %s}' % now),
                    self.run_cli(world(), stdin='{"target": "toy"}'),
                    self.run_cli(world(), stdin='{"target": "toy", "now": "2026-10-30"}'),
                    self.run_cli(rebased(world(), lambda d: None)),
                    self.run_cli(world(), stdin='{"target": "other", %s}' % now), self.run_cli(world(), args=["check"]),
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


class Yaz(TLW.StateBase):
    """``yaz``'s step before any target is served (``test_loop_write.StateBase``'s worlds: t1, a toy at ``yaz_world.REPO``, or t1 and t2)."""

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
                         (False, "drift", reasons, "t1", [],
                          {"checked": ["t1"], "drifted": {"t1": reasons}, "stale": False}), out)
        self.assertEqual((self.writes(), self.gh.refs, self.signer.payloads), ([], refs, []))
        self.gh.overrides[("GET", path)] = kept

    def test_a_drifted_target_is_not_written_and_a_clean_one_is(self):
        self.ready()
        p = "/repos/%s" % YW.REPO
        # test 24's three: a rule that differs from setup, an undeclared App, a workflow on the brain's branches
        self.drifted(p + "/rules/branches/" + B.INTEGRATION, without("required_status_checks"),
                     ["integration_rules_missing", "rules_changed:brain/integration"])
        self.drifted(p + "/rulesets/1", bypass("always"), ["rules_bypassable"])
        self.drifted(INSTALLED, lambda body: dict(body, repositories=body["repositories"] + [{"full_name": "a/b"}]),
                     ["app_scope"])
        self.drifted(p + "/rules/branches/" + B.INTEGRATION,
                     checks(required_status_checks=[{"context": B.CHECK, "integration_id": 1}]),
                     ["integration_check_not_writer", "rules_changed:brain/integration"])
        # tohum/01c: a rule content other than the recorded one, where none of the reasons above reads
        self.drifted(p + "/rules/branches/main", review(2), ["rules_changed:main"])
        self.drifted(p + "/actions/workflows", lambda body: dict(body, workflows=[SECRET_WORKFLOW]),
                     ["toy_workflows"])
        # the same cycle on the facts setup left: written, after every one of the check's reads
        del self.gh.requests[:]
        job = self.job()
        out = self.line(job)
        self.assertEqual((out["ok"], out["done"], out["merge"], job["drift"]),
                         (True, ["D5", "D6"], "good", {"checked": ["t1"], "drifted": {}, "stale": False}), job)
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
        self.assertEqual(out["drift"], {"checked": ["t1", "t2"], "drifted": {"t2": ["toy_workflows"]},
                                        "stale": False})
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
        self.assertEqual((out["ok"], out["drift"]),
                         (True, {"checked": ["t1", "t2"], "drifted": {}, "stale": False}), out)
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
        self.assertEqual(out["drift"], {"checked": ["t1"], "drifted": {}, "stale": False})
        self.assertEqual(ghs["t2"].requests, [])

    # tohum/01c
    def test_a_summary_without_the_baseline_is_unusable_and_nothing_is_written(self):
        self.ready()
        summary = json.loads(YW.summary())
        TLW.write_tree(self.workspace, {J.SUMMARY: json.dumps({k: v for k, v in summary.items() if k != "drift"})})
        with self.assertRaisesRegex(J.Unusable, r"\Ayaz: drift: summary.json carries no drift baseline\Z"):
            self.job()
        self.assertEqual(self.gh.requests, [])
        TLW.write_tree(self.workspace, {J.SUMMARY: YW.summary(hashes={}).decode()})
        with self.assertRaisesRegex(J.Unusable, r"\Ayaz: drift: summary.json: drift.hashes"):
            self.job()
        self.assertEqual(self.gh.requests, [])

    def test_a_writer_app_other_than_the_recorded_one_stops_the_job(self):
        self.ready()
        TLW.write_tree(self.workspace, {J.SUMMARY: YW.summary(writer_app_id=AW.APP_ID + 1).decode()})
        refs = dict(self.gh.refs)
        out = self.job()
        self.assertEqual((out["ok"], out["reason"], out["reasons"], out["target"], out["targets"]),
                         (False, "drift", ["writer_app_changed"], "t1", []), out)
        self.assertEqual((self.writes(), self.gh.refs, self.signer.payloads), ([], refs, []))

    def stale_summary(self, seconds: int, targets=None) -> None:
        """The checkout's summary with an operator check ``seconds`` older than 7 days at the job's clock."""
        at = later(-WEEK - seconds, YW.TS)
        TLW.write_tree(self.workspace, {J.SUMMARY: YW.summary(targets, operator_checked_at=at).decode()})

    def test_a_stale_operator_check_ends_the_job_cleanly_with_nothing_written(self):
        self.ready()
        self.stale_summary(1)
        refs = dict(self.gh.refs)
        out = self.job()
        self.assertEqual({k: out[k] for k in out if k not in ("job", "steps", "mfs", "offline")},
                         {"ok": False, "reason": "operator_check_stale", "targets": [], "policy": {},
                          "drift": {"checked": ["t1"], "drifted": {}, "stale": True}}, out)
        self.assertEqual((self.writes(), self.gh.refs, self.signer.payloads), ([], refs, []))
        sent = [(m, path) for m, path, _ in self.gh.requests]
        self.assertEqual(sent, [("GET", path.replace(AW.REPO, YW.REPO)) for path in READS["toy"]])
        # a hard stop beside it is the job's reason
        change(self.gh, "/repos/%s/rulesets/1" % YW.REPO, bypass("always"))
        out = self.job()
        self.assertEqual((out["reason"], out["reasons"], out["target"], out["drift"]["stale"], out["targets"]),
                         ("drift", ["rules_bypassable"], "t1", True, []), out)
        self.assertEqual(self.writes(), [])
        change(self.gh, "/repos/%s/rulesets/1" % YW.REPO, bypass("never"))
        # exactly 7 days at the job's clock: the cycle is written
        self.stale_summary(0)
        job = self.job()
        self.assertEqual((self.line(job)["ok"], job["drift"]["stale"], bool(self.writes())), (True, False, True), job)

    def test_a_stale_check_stops_every_target_after_all_were_read(self):
        ghs = self.two()
        self.stale_summary(1, [YW.entry("t1"), YW.entry("t2")])
        out, sent = self.run_two(ghs)
        self.assertEqual((out["ok"], out["reason"], out["targets"], out["drift"]),
                         (False, "operator_check_stale", [], {"checked": ["t1", "t2"], "drifted": {}, "stale": True}),
                         out)
        self.assertNotIn("target", out)
        self.assertEqual(([s for s in sent if s[0] != "GET"], self.signer.payloads), ([], []))
        self.assertEqual([s for s in sent if s in reads_of("acme/t2")], reads_of("acme/t2"))

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


ONLINE = {"harness/__init__.py": "", "harness/score.py": "from dispatcher import llm_call\n",
          "dispatcher/__init__.py": "", "dispatcher/llm_call.py": ""}


class Order(TLW.StateBase):
    """Stage 1 MF5 before MF6: the static reading of the running harness is the job's first step."""
    ready, job, two = Yaz.ready, Yaz.job, Yaz.two

    def online(self) -> dict:
        """The job on a code root whose harness imports the client: its line, after nothing was sent or written."""
        root = os.path.join(self.temp, "online-code")
        TLW.write_tree(root, ONLINE)
        refs = dict(self.gh.refs)
        with unittest.mock.patch.object(J, "CODE_ROOT", root):
            out = self.job()
        self.assertEqual((self.gh.requests, self.gh.refs, self.signer.payloads), ([], refs, []))
        return out

    def test_an_online_harness_stops_the_job_before_a_request_to_any_target(self):
        self.ready()
        out = self.online()
        self.assertEqual({k: out[k] for k in out if k not in ("job", "steps", "mfs")},
                         {"ok": False, "reason": "harness_online", "targets": [],
                          "reasons": ["client_import:harness.score:dispatcher.llm_call"]}, out)

    def test_an_online_harness_stops_the_job_before_pulled_is_opened(self):
        self.ready()
        pulled = os.path.join(self.temp, "in", "pulled")
        os.rename(pulled, pulled + "-away")
        self.assertEqual(self.online()["reason"], "harness_online")
        out = self.job()   # the code as it is: the reading passes and the job goes on to open ``pulled``
        self.assertEqual((out["reason"], out["offline"], "drift" in out),
                         ("pulled_invalid", {"modules": J.yaz_offline()["modules"]}, False), out)

    def test_the_reading_is_made_once_per_job_before_the_first_request(self):
        ghs = self.two()
        transport, real, seen = Recorded(TLW.Router(ghs)), J.yaz_offline, []
        with unittest.mock.patch.object(J, "yaz_offline", side_effect=lambda: seen.append(list(transport.sent)) or real()):
            out = J.run("yaz", YW.env(self.temp, self.workspace), transport=transport, signer=self.signer,
                        now=lambda: YW.NOW)
        self.assertEqual((out["ok"], out["drift"]["checked"], seen), (True, ["t1", "t2"], [[]]), out)
        self.assertEqual(out["offline"], {"modules": real()["modules"]})
        self.assertTrue(all("offline" not in line for line in out["targets"]), out["targets"])
        self.assertTrue(transport.sent)


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


class YazPolicy(Yaz):
    """``yaz``'s stop on a policy it cannot use, before any target is served (``Yaz``'s worlds)."""

    def repolicied(self, tid: str, change) -> None:
        """Target ``tid``'s ``pulled`` with ``change`` made to its parsed policy, the manifest naming the new bytes
        (what a ``cek`` of other code would have handed over: this code's ``cek`` refuses such a pull)."""
        self.pulled = os.path.join(self.temp, "in", "pulled", tid)
        path = os.path.join(self.pulled, "policy.json")
        with open(path, "rb") as fh:
            doc = json.loads(fh.read())
        change(doc)
        data = json.dumps(doc).encode()
        with open(path, "wb") as fh:
            fh.write(data)
        manifest = self.manifest()
        manifest["files"]["policy.json"] = TLW.P._sha(data)
        self.set_manifest(manifest)

    # "before the loop's first write", whichever target's policy it is
    def test_a_required_path_absent_on_a_later_target_leaves_every_target_unwritten(self):
        ghs = self.two()
        self.repolicied("t2", lambda doc: doc["constitutional"]["stage_params"].pop("evidence_ref_max_lines"))
        named = ["policy_invalid:constitutional.stage_params.evidence_ref_max_lines"]
        out, sent = self.run_two(ghs)
        self.assertEqual((out["ok"], out["reason"], out["reasons"], out["target"], out["targets"], out["policy"]),
                         (False, "policy_unusable", named, "t2", [], {"t2": named}), out)
        self.assertEqual(out["drift"], {"checked": ["t1", "t2"], "drifted": {}, "stale": False})
        self.assertEqual(([s for s in sent if s[0] != "GET"], self.signer.payloads), ([], []))
        for gh in ghs.values():
            self.assertEqual((gh.refs[B.STATE], gh.refs[B.INTEGRATION]), (TLW.HEADS[B.STATE], TLW.HEADS[B.INTEGRATION]))
        # before a stale operator check, which is the other clean stop
        self.stale_summary(1, [YW.entry("t1"), YW.entry("t2")])
        out, sent = self.run_two(ghs)
        self.assertEqual((out["reason"], out["target"], out["drift"]["stale"], out["targets"]),
                         ("policy_unusable", "t2", True, []), out)
        # a hard stop beside it is the job's reason
        change(ghs["t1"], "/repos/acme/t1/rulesets/1", bypass("always"))
        out, sent = self.run_two(ghs)
        self.assertEqual((out["reason"], out["reasons"], out["target"], out["targets"]),
                         ("drift", ["rules_bypassable"], "t1", []), out)
        self.assertNotIn("policy", out)
        self.assertEqual(([s for s in sent if s[0] != "GET"], self.signer.payloads), ([], []))

    def test_each_required_path_absent_or_off_its_form_stops_the_job_and_the_policy_put_back_is_written(self):
        self.ready()
        refs = dict(self.gh.refs)
        with open(os.path.join(self.pulled, "policy.json"), "rb") as fh:
            good = json.loads(fh.read())
        self.assertEqual(len(R.REQUIRED), 12)

        def cut(path):
            def change(doc):
                for key in path[:-1]:
                    doc = doc[key]
                del doc[path[-1]]
            return change

        def put(path, value):
            def change(doc):
                for key in path[:-1]:
                    doc = doc[key]
                doc[path[-1]] = value
            return change

        for path in R.REQUIRED:
            for how in (cut(path), put(path, 0.5), put(path, None)):     # absent; a JSON float; a null
                self.repolicied("t1", lambda doc: (doc.clear(), doc.update(copy.deepcopy(good))))
                self.repolicied("t1", how)
                with self.subTest(path=path):
                    out = self.job()
                    named = ["policy_invalid:" + R.dotted(path)]
                    self.assertEqual((out["ok"], out["reason"], out["reasons"], out["target"], out["targets"],
                                      out["policy"]), (False, "policy_unusable", named, "t1", [], {"t1": named}), out)
                    self.assertEqual((self.writes(), self.gh.refs, self.signer.payloads), ([], refs, []))
        self.repolicied("t1", lambda doc: (doc.clear(), doc.update(copy.deepcopy(good))))
        job = self.job()
        self.assertEqual((self.line(job)["ok"], job["policy"], bool(self.writes())), (True, {}, True), job)


class Listed(unittest.TestCase):
    def test_every_test_class_of_this_module_is_in_the_list_the_command_runs(self):
        own = {c for c in globals().values() if isinstance(c, type) and issubclass(c, unittest.TestCase)
               and c.__module__ == __name__}
        self.assertEqual(own, set(LISTED))
        self.assertEqual(len(LISTED), 9)


LISTED = (Check, Baseline, Genesis, Cli, Yaz, YazPolicy, Order, YazGenesis, Listed)


def load_tests(loader, standard, pattern):
    """This module's own tests: ``Yaz`` and ``Order`` inherit ``test_loop_write.StateBase``'s world, not its bases'
    tests (a class left out of this list is not run by the manifest's command: ``Listed`` reads the list)."""
    suite = unittest.TestSuite()
    for case in LISTED:
        names = [n for n in loader.getTestCaseNames(case) if n in vars(case)]
        suite.addTests(case(n) for n in names)
    return suite
