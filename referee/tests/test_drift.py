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
  ``yaz`` it ends the job ``operator_check_stale`` with nothing written (a drift beside it is the job's reason);
  that stop alone is exit 0 with one fixed ``::warning`` line before the job's line (``loop.job.ending``), a line
  with any other reason or none is exit 1, and ``main`` ends as ``ending`` says. Not tested: that GitHub shows
  the warning (no live run was seen).

- ``Compared`` (tohum/01c, the answer to seed-082): the App's permissions other than the recorded object
  (``writer_app_permissions_changed``; JSON equality), a ruleset list whose ids are not the recorded set
  (``rulesets_changed``; every page while one holds 100), a ``visibility`` other than the recorded one for every
  repository the baseline names (``visibility_changed:<repo>``), each of the caller's three hashes against the
  recorded ones; hashes not of the form and an operator check after the clock are unusable with nothing read.
- ``Held``: ``drift.check.held`` on a checkout written here: the folder hash by the page's recipe over literal
  bytes (nested files, an empty folder, a name beyond ASCII), a link, a fifo, a name that is not UTF-8 and a
  folder that is absent, a file or a link refused; the constitutional hash of the object's canonical form, a JSON
  float there ``policy_invalid:<path>``.
- ``YazCheckout``: ``yaz`` with one operator file of its checkout changed ends ``drift`` with that hash's reason
  and nothing written, a pulled policy that differs from the checkout's is not what is hashed, and a checkout
  without ``policy.json``, ``vectors/`` or ``seats/``, with a link among them or a float in the policy, is
  unusable with no request sent.

- ``Activity``: tohum/01c "Etkinlik API'si", ``drift.check``'s rules 1-5: every (actor, type, ref) of the page's
  table allowed or named, logins byte for byte, the refs judged, the window's start and its boundary second, a
  full page that does not reach it, the item's form, the App's slug, the order of the answer, the command;
  ``ledger.serial.last_start``. ``YazActivity``: the same in a ``yaz`` job, the window's start read from the
  pulled ledger, a stop that writes nothing and lasts until ``not_before`` moves.

Not tested, because not built (``drift.check`` "Out of scope"): a second page of the activity, Gözcü's
``hard_stop`` row, other Apps' installations, the referee repository's own
settings, workflow triggers. Not tested either: a real checkout made by git (the folders here are written by
``open``), a real API (the activity items here are written from the documentation's field names; the form of a
real ``timestamp`` was not seen).
"""

from __future__ import annotations

import copy
import datetime
import hashlib
import io
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
from ledger import serial as SE  # noqa: E402
from loop import job as J  # noqa: E402
from policy import reads as R  # noqa: E402
from target import branches as B  # noqa: E402

P = "/repos/%s" % AW.REPO
STATE, INTEGRATION, MAIN = (P + "/rules/branches/" + b for b in (B.STATE, B.INTEGRATION, "main"))
WORKFLOWS, PERMISSIONS, INSTALLED = P + "/actions/workflows", P + "/actions/permissions", "/installation/repositories"
LISTING = P + "/rulesets?per_page=100"
ACTIVITY = P + "/activity?per_page=100"
READS = {"toy": ["/app", INSTALLED, STATE, INTEGRATION, MAIN, P + "/rulesets/1", P + "/rulesets/2", P + "/rulesets/3",
                 WORKFLOWS, LISTING, P, ACTIVITY],
         "copy": ["/app", INSTALLED, STATE, INTEGRATION, MAIN, P + "/rulesets/1", P + "/rulesets/2",
                  P + "/rulesets/3", PERMISSIONS, LISTING, P, ACTIVITY]}
# what genesis reads of them (``activate.genesis`` calls ``rules`` and ``actions``, not the baseline's comparison)
GENESIS_READS = {kind: [path for path in paths if path not in (LISTING, P, ACTIVITY)] for kind, paths in READS.items()}


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


def check(w: AW.World, target="toy", repo=None, now=AW.TS, hashes=None, previous=None) -> dict:
    """The check on the world; ``hashes`` are the checkout's (``activation_world.CHECKOUT``'s when ``None``)."""
    return DC.check(w.gh, w.files["summary.json"], AW.checkout_hashes() if hashes is None else hashes, target, now,
                    previous, repo)


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
            self.assertEqual(check(w), {"ok": True, "hard_stop": False, "reasons": [], "stale": False, "activity": []})
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
                                        "stale": False, "activity": []}, name)
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
        w.gh.overrides[("GET", "/repos/acme/copy")] = (200, {"visibility": "public"})
        self.assertEqual(check(w)["reasons"], ["app_scope"])  # installed on one of the two declared
        change(w.gh, INSTALLED, lambda body: dict(body, repositories=[{"full_name": "acme/copy"},
                                                                      {"full_name": AW.REPO}]))
        self.assertEqual(check(w)["reasons"], [])

    def test_a_caller_writing_to_another_repository_is_refused_before_any_read(self):
        w = world("toy")
        self.assertEqual(check(w, repo="acme/other"),
                         {"ok": False, "hard_stop": True, "reasons": ["target_repo_mismatch"], "stale": False, "activity": []})
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
    **{"without " + key: drop(key) for key in ("writer_app_id", "writer_app_permissions", "targets", "activity",
                                                "hashes", "visibility", "operator_checked_at")},
    "writer_app_permissions a list": put("writer_app_permissions", value=["contents"]),
    "writer_app_permissions null": put("writer_app_permissions", value=None),
    "rulesets not ascending": put("targets", "toy", "rulesets", value=[1, 3, 2]),
    "a ruleset id twice": put("targets", "toy", "rulesets", value=[1, 2, 2, 3]),
    "a ruleset id a boolean": put("targets", "toy", "rulesets", value=[True, 2, 3]),
    "rules naming no branch": put("targets", "toy", "rules", value={}),
    **{"rules without " + b: (lambda b: lambda d: put("targets", "toy", "rules", value={
        k: v for k, v in d["targets"]["toy"]["rules"].items() if k != b})(d))(b) for b in DC.BRANCHES},
    "visibility without the target's repository": put("visibility", value={"acme/other": "public"}),
    "a visibility key that is no repository name": put("visibility", "acme", value="public"),
    "a visibility key with a path": put("visibility", "acme/toy/../other", value="public"),
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
        # the form itself, with no login and no permission, is read
        w = rebased(world("toy"), put("activity", "operator_logins", value=[]))
        self.assertEqual(check(w)["reasons"], [])
        self.assertEqual(check(rebased(w, put("writer_app_permissions", value={})))["reasons"],
                         ["writer_app_permissions_changed"])

    def test_a_baseline_without_the_target_is_unusable(self):
        w = rebased(world("toy"), lambda d: dict(d, targets={"other": d["targets"]["toy"]}))
        with self.assertRaisesRegex(DC.Unusable, r"\Asummary.json: drift.targets has no 'toy'\Z"):
            check(w)
        self.assertEqual(w.gh.requests, [])

    def test_a_writer_app_of_another_id_is_a_hard_stop(self):
        w = rebased(world("copy"), put("writer_app_id", value=AW.APP_ID + 1))
        self.assertEqual(check(w), {"ok": False, "hard_stop": True, "reasons": ["writer_app_changed"],
                                    "stale": False, "activity": []})
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
                                            "stale": False, "activity": []}, name)
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
        self.assertEqual(w.gh.requests, [("GET", path, None) for path in READS["toy"][:-1] + [extra, ACTIVITY]])  # after the others, before the activity
        w.gh.overrides[("GET", extra)] = (200, [])
        self.assertEqual(check(w)["reasons"], ["rules_changed:brain/extra"])
        w.gh.overrides[("GET", extra)] = (200, [{"type": "deletion"}])
        with self.assertRaises(DC.Unusable):
            check(w)
        # another target's entry is not this one's
        w = rebased(world("toy"), lambda d: dict(d, targets=dict(d["targets"], other={
            "rulesets": [], "rules": {b: "0" * 64 for b in DC.BRANCHES}})))
        self.assertEqual(check(w)["reasons"], [])

    def test_an_operator_check_older_than_seven_days_is_stale_and_no_hard_stop(self):
        clean = {"ok": True, "hard_stop": False, "reasons": [], "stale": False, "activity": []}
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
                         {"ok": False, "hard_stop": True, "reasons": ["toy_workflows"], "stale": True, "activity": []})
        self.assertEqual(check(world("toy"), repo="acme/other", now=later(WEEK + 1)),
                         {"ok": False, "hard_stop": True, "reasons": ["target_repo_mismatch"], "stale": True, "activity": []})

    def test_a_clock_that_is_no_time_is_unusable_and_nothing_is_read(self):
        w = world("toy")
        for now in (None, "", "2026-10-30", "2026-10-30T12:00:00", "2026-02-30T12:00:00Z", 1761825600,
                    "2026-10-30T12:00:00Z\n", datetime.datetime(2026, 10, 30)):
            with self.assertRaisesRegex(DC.Unusable, r"\Anow must be ", msg=now):
                check(w, now=now)
        self.assertEqual(w.gh.requests, [])


def hashes(**over) -> dict:
    return dict(AW.checkout_hashes(), **over)


class Compared(unittest.TestCase):
    """tohum/01c (the answer to seed-082): the App's permissions, the ruleset list, the visibility and the three
    hashes against the baseline; an operator check after the clock."""

    def stop(self, w: AW.World, reasons: list, msg=None, **kw) -> None:
        self.assertEqual(check(w, **kw), {"ok": False, "hard_stop": True, "reasons": reasons, "stale": False, "activity": []}, msg)

    def test_permissions_other_than_the_recorded_ones_are_a_hard_stop(self):
        changes = {
            "one widened": lambda app: dict(app, permissions=dict(app["permissions"], metadata="write")),
            "one more": lambda app: dict(app, permissions=dict(app["permissions"], actions="read")),
            "one fewer": lambda app: dict(app, permissions={k: v for k, v in app["permissions"].items()
                                                             if k != "checks"}),
            "none": lambda app: dict(app, permissions={}),
            "the field absent": lambda app: {k: v for k, v in app.items() if k != "permissions"},
            "null": lambda app: dict(app, permissions=None),
        }
        for kind in ("toy", "copy"):
            for name, how in changes.items():
                self.stop(world(kind, ("/app", how)), ["writer_app_permissions_changed"], name)
        # the recorded ones changed instead
        self.stop(rebased(world("toy"), put("writer_app_permissions", "contents", value="read")),
                  ["writer_app_permissions_changed"])
        # the keys' order is no difference; a boolean is not the number it equals
        w = world("toy", ("/app", lambda app: dict(app, permissions=dict(reversed(list(app["permissions"].items()))))))
        self.assertEqual(check(w)["reasons"], [])
        one = lambda value: ("/app", lambda app: dict(app, permissions={"x": value}))  # noqa: E731
        self.assertEqual(check(rebased(world("toy", one(1)), put("writer_app_permissions", value={"x": 1})))["reasons"],
                         [])
        self.stop(rebased(world("toy", one(True)), put("writer_app_permissions", value={"x": 1})),
                  ["writer_app_permissions_changed"])

    def test_a_ruleset_list_other_than_the_recorded_set_is_a_hard_stop(self):
        item = lambda n: {"id": n, "name": "r%d" % n}  # noqa: E731
        for kind in ("toy", "copy"):
            self.stop(world(kind, (LISTING, lambda body: body + [item(4)])), ["rulesets_changed"], "one added")
            self.stop(world(kind, (LISTING, lambda body: body[:2])), ["rulesets_changed"], "one removed")
            self.stop(world(kind, (LISTING, lambda body: body[:2] + [item(9)])), ["rulesets_changed"], "one replaced")
            self.stop(world(kind, (LISTING, lambda body: [])), ["rulesets_changed"], "none")
        self.stop(rebased(world("toy"), put("targets", "toy", "rulesets", value=[1, 2])), ["rulesets_changed"])
        self.stop(rebased(world("toy"), put("targets", "toy", "rulesets", value=[])), ["rulesets_changed"])
        # a set: the list's order and an id listed twice are no difference
        w = world("toy", (LISTING, lambda body: body[::-1] + body[:1]))
        self.assertEqual(check(w)["reasons"], [])
        # another target's recorded list is not this one's
        w = rebased(world("toy"), lambda d: dict(d, targets=dict(d["targets"], other=dict(d["targets"]["toy"],
                                                                                         rulesets=[7]))))
        self.assertEqual(check(w)["reasons"], [])
        for body in ([{"id": "1"}], [{"name": "x"}], [1], [{"id": True}], [item(1), None]):
            w = world("toy", (LISTING, lambda _: body))
            with self.assertRaisesRegex(DC.Unusable, "an item without an integer id", msg=body):
                check(w)

    def test_every_page_of_the_ruleset_list_is_read(self):
        item = lambda n: {"id": n}  # noqa: E731
        full = [item(n) for n in range(1, 101)]
        second, third = LISTING + "&page=2", LISTING + "&page=3"

        def paged(recorded: list, pages: dict) -> AW.World:
            w = rebased(world("toy", (LISTING, lambda _: full)), put("targets", "toy", "rulesets", value=recorded))
            w.gh.overrides.update({("GET", path): (200, body) for path, body in pages.items()})
            return w

        asked = lambda w: [path for _, path, _ in w.gh.requests if path.startswith(LISTING)]  # noqa: E731
        # a full page has a next one: its absence is no end of the list
        w = paged(list(range(1, 101)), {})
        with self.assertRaisesRegex(DC.Unusable, r"rulesets\?per_page=100&page=2 answered 404"):
            check(w)
        w = paged(list(range(1, 101)), {second: []})
        self.assertEqual((check(w)["reasons"], asked(w)), ([], [LISTING, second]))
        # the 101st ruleset is on the second page: one more than recorded there, or one recorded only there
        self.stop(paged(list(range(1, 101)), {second: [item(101)]}), ["rulesets_changed"])
        w = paged(list(range(1, 102)), {second: [item(101)]})
        self.assertEqual((check(w)["reasons"], asked(w)), ([], [LISTING, second]))
        self.stop(paged(list(range(1, 102)), {second: []}), ["rulesets_changed"])
        w = paged(list(range(1, 202)), {second: [item(n) for n in range(101, 201)], third: [item(201)]})
        self.assertEqual((check(w)["reasons"], asked(w)), ([], [LISTING, second, third]))
        # a full page that repeats the pages before it is no progress: refused, not read for ever
        w = paged(list(range(1, 101)), {second: full})
        with self.assertRaisesRegex(DC.Unusable, r"page=2: a full page with no new id"):
            check(w)
        self.assertEqual(asked(w), [LISTING, second])
        # ... while a full page with one new id among known ones is progress
        w = paged(list(range(1, 201)), {second: [item(n) for n in range(100, 200)], third: [item(200)]})
        self.assertEqual((check(w)["reasons"], asked(w)), ([], [LISTING, second, third]))
        # a page of 99 is the last
        w = rebased(world("toy", (LISTING, lambda _: full[:99])), put("targets", "toy", "rulesets",
                                                                      value=list(range(1, 100))))
        self.assertEqual((check(w)["reasons"], asked(w)), ([], [LISTING]))
        with self.assertRaisesRegex(DC.Unusable, "an item without an integer id"):
            check(paged(list(range(1, 102)), {second: [{"id": "101"}]}))

    def test_a_visibility_other_than_the_recorded_one_is_a_hard_stop(self):
        named = "visibility_changed:" + AW.REPO
        seen = lambda value: (P, lambda body: dict(body, visibility=value))  # noqa: E731
        for kind in ("toy", "copy"):
            for value in ("private", "internal", None, "PUBLIC", True):
                self.stop(world(kind, seen(value)), [named], value)
            self.stop(world(kind, (P, lambda body: {"full_name": AW.REPO, "private": False})), [named], "no field")
        private = put("visibility", AW.REPO, value="private")
        self.stop(rebased(world("toy"), private), [named])
        self.assertEqual(check(rebased(world("toy", seen("private")), private))["reasons"], [])
        self.stop(rebased(world("toy", seen("internal")), private), [named])

    def test_every_repository_the_baseline_names_is_read(self):
        other = "/repos/acme/referee"
        w = rebased(world("toy"), put("visibility", "acme/referee", value="private"))
        with self.assertRaisesRegex(DC.Unusable, r"GET /repos/acme/referee answered 404"):
            check(w)
        w.gh.overrides[("GET", other)] = (200, {"visibility": "private"})
        del w.gh.requests[:]
        self.assertEqual(check(w)["reasons"], [])
        self.assertEqual([path for _, path, _ in w.gh.requests], READS["toy"][:-2] + [other, P, ACTIVITY])  # in the names' order
        w.gh.overrides[("GET", other)] = (200, {"visibility": "public"})
        self.stop(w, ["visibility_changed:acme/referee"])
        change(w.gh, P, lambda body: dict(body, visibility="private"))
        self.stop(w, ["visibility_changed:acme/referee", "visibility_changed:" + AW.REPO])
        w.gh.overrides[("GET", other)] = (200, ["public"])
        with self.assertRaises(DC.Unusable):
            check(w)

    def test_a_hash_of_the_checkout_other_than_the_recorded_one_is_a_hard_stop(self):
        reasons = {"constitutional_sha256": "constitutional_hash_mismatch", "vectors_sha256": "vectors_hash_mismatch",
                   "seats_sha256": "seats_hash_mismatch"}
        self.assertEqual(set(reasons), set(AW.checkout_hashes()))
        for key, reason in reasons.items():
            for kind in ("toy", "copy"):
                self.stop(world(kind), [reason], key, hashes=hashes(**{key: "0" * 64}))
            # the recorded one changed instead
            self.stop(rebased(world("toy"), put("hashes", key, value="0" * 64)), [reason], key)
        self.stop(world("toy"), sorted(reasons.values()), hashes=dict.fromkeys(reasons, "0" * 64))
        # one hash in another's place is not that hash
        held = AW.checkout_hashes()
        self.assertEqual(len(set(held.values())), 3)
        self.stop(world("toy"), ["seats_hash_mismatch", "vectors_hash_mismatch"],
                  hashes=hashes(vectors_sha256=held["seats_sha256"], seats_sha256=held["vectors_sha256"]))
        # beside a fact of the target
        self.stop(world("toy", (WORKFLOWS, CASES["a workflow on the toy"][2])),
                  ["toy_workflows", "vectors_hash_mismatch"], hashes=hashes(vectors_sha256="0" * 64))

    def test_hashes_not_of_the_form_are_unusable_and_nothing_is_read(self):
        w = world("toy")
        good = AW.checkout_hashes()
        with self.assertRaisesRegex(DC.Unusable, r"\Ahashes must be "):
            DC.check(w.gh, w.files["summary.json"], None, "toy", AW.TS, None)
        for bad in ({}, [], {k: v for k, v in good.items() if k != "seats_sha256"}, dict(good, more="0" * 64),
                    dict(good, vectors_sha256=good["vectors_sha256"].upper()), dict(good, seats_sha256=None),
                    dict(good, constitutional_sha256="0" * 63)):
            with self.assertRaisesRegex(DC.Unusable, r"\Ahashes must be ", msg=bad):
                check(w, hashes=bad)
        self.assertEqual(w.gh.requests, [])

    def test_an_operator_check_after_the_clock_is_unusable_and_nothing_is_read(self):
        w = world("toy")
        for now in (later(-1), later(-WEEK), "2025-01-01T00:00:00Z"):
            with self.assertRaisesRegex(DC.Unusable, r"\Asummary.json: drift.operator_checked_at is after now\Z"):
                check(w, now=now)
            with self.assertRaises(DC.Unusable):   # not answered as a mismatch before it either
                check(w, now=now, repo="acme/other")
        self.assertEqual(w.gh.requests, [])
        self.assertEqual(check(w, now=later(0))["ok"], True)   # the same second is not after

    def test_every_reason_against_the_baseline_has_a_case_here(self):
        with open(DC.__file__, encoding="utf-8") as fh:
            source = fh.read()
        named = {r for r in ("writer_app_permissions_changed", "rulesets_changed", "visibility_changed:%s",
                             "constitutional_hash_mismatch", "vectors_hash_mismatch", "seats_hash_mismatch")
                 if '"%s"' % r in source}
        self.assertEqual(len(named), 6)
        self.assertEqual(set(DC.HASH_REASONS.values()), {r for r in named if r.endswith("_hash_mismatch")})


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Held(unittest.TestCase):
    """``drift.check.held``: tohum/01c's three hashes of a checkout, each expected value computed here by
    ``hashlib`` over literal bytes."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name

    def tree(self, files: dict) -> str:
        """A new folder under the test's directory holding ``files``."""
        root = tempfile.mkdtemp(dir=self.root)
        AW.write_checkout(root, files)
        return root

    def test_the_three_hashes_of_a_checkout(self):
        AW.write_checkout(self.root)
        self.assertEqual(DC.held(self.root), AW.checkout_hashes())
        # what is beside the three is not read
        AW.write_checkout(self.root, {"setup/summary.json": b"{}", "vectorsx/a": b"1", "README.md": b"x"})
        self.assertEqual(DC.held(self.root), AW.checkout_hashes())
        for path, key in (("vectors/cases.json", "vectors_sha256"), ("seats/rival.json", "seats_sha256")):
            before = DC.held(self.root)
            AW.write_checkout(self.root, {path: AW.CHECKOUT[path] + b" "})
            self.assertEqual({k for k, v in DC.held(self.root).items() if v != before[k]}, {key})
        for gone in ("policy.json", "vectors", "seats"):
            root = self.tree(AW.CHECKOUT)
            (os.remove if gone == "policy.json" else __import__("shutil").rmtree)(os.path.join(root, gone))
            with self.assertRaises(DC.Unusable, msg=gone):
                DC.held(root)

    def test_a_folder_s_hash_is_the_page_s_recipe(self):
        # content sha256, two spaces, the path with "/", LF; the lines sorted (not the names), joined, sha256
        files = {"b.json": b"one\n", "a/z.txt": b"", "a/b/c": b"\x00\xff"}
        lines = sorted(["%s  b.json\n" % sha(b"one\n"), "%s  a/z.txt\n" % sha(b""), "%s  a/b/c\n" % sha(b"\x00\xff")])
        self.assertNotEqual(lines, sorted(lines, key=lambda line: line[66:]))  # the two orders differ here
        want = sha("".join(lines).encode())
        self.assertEqual(DC.folder_hash(self.tree(files)), want)
        # a folder without a file has the hash of no line, and an empty folder inside is no line
        self.assertEqual(DC.folder_hash(self.tree({})), sha(b""))
        root = self.tree(files)
        os.makedirs(os.path.join(root, "a", "empty"))
        self.assertEqual(DC.folder_hash(root), want)
        # a file's bytes, its name and its place are each in the hash; the folder's own name is not
        for other in (dict(files, **{"b.json": b"one"}), {"c.json": b"one\n", "a/z.txt": b"", "a/b/c": b"\x00\xff"},
                      {"a/b.json": b"one\n", "a/z.txt": b"", "a/b/c": b"\x00\xff"}, dict(files, more=b"")):
            self.assertNotEqual(DC.folder_hash(self.tree(other)), want, other)
        self.assertEqual(DC.folder_hash(self.tree(files)), want)
        # a name that is not ASCII is its UTF-8 bytes
        self.assertEqual(DC.folder_hash(self.tree({"\u00e7": b"x"})), sha(("%s  \u00e7\n" % sha(b"x")).encode("utf-8")))

    def test_a_link_or_what_is_no_regular_file_is_refused(self):
        files = {"a.json": b"1", "sub/b.json": b"2"}
        outside = self.tree({"x": b"1"})

        def linked_file(root):
            os.symlink(os.path.join(root, "a.json"), os.path.join(root, "link.json"))

        def linked_file_below(root):
            os.symlink(os.path.join(outside, "x"), os.path.join(root, "sub", "x"))

        def linked_folder(root):
            os.symlink(outside, os.path.join(root, "more"))

        def dangling(root):
            os.symlink(os.path.join(root, "nothing"), os.path.join(root, "gone"))

        def fifo(root):
            os.mkfifo(os.path.join(root, "sub", "pipe"))

        def not_utf8(root):
            with open(os.path.join(os.fsencode(root), b"\xff.json"), "wb") as fh:
                fh.write(b"1")

        for how in (linked_file, linked_file_below, linked_folder, dangling, fifo, not_utf8):
            root = self.tree(files)
            how(root)
            with self.assertRaises(DC.Unusable, msg=how.__name__):
                DC.folder_hash(root)
        # the folder itself: absent, a file, a link to a folder
        root = self.tree(files)
        for name in ("absent", "a.json"):
            with self.assertRaisesRegex(DC.Unusable, "is not a directory of the checkout", msg=name):
                DC.folder_hash(os.path.join(root, name))
        os.symlink(os.path.join(root, "sub"), os.path.join(root, "alias"))
        with self.assertRaisesRegex(DC.Unusable, "is not a directory of the checkout"):
            DC.folder_hash(os.path.join(root, "alias"))
        self.assertEqual(DC.folder_hash(os.path.join(root, "sub")), sha(("%s  b.json\n" % sha(b"2")).encode()))

    def test_the_constitutional_hash_is_of_that_object_s_canonical_form(self):
        policy = b'{"operating": {"ratio": 0.5}, "constitutional": {"b": [1, "0.220000"], "a": {"\\u00e7": null}}}'
        want = sha('{"a":{"\u00e7":null},"b":[1,"0.220000"]}'.encode("utf-8"))
        self.assertEqual(DC.constitutional_hash(policy), want)   # a float beside the object is not in the hash
        self.assertEqual(DC.constitutional_hash(b' {"constitutional":{"a":{"\xc3\xa7":null},"b":[1,"0.220000"]}}\n'), want)
        self.assertNotEqual(DC.constitutional_hash(policy.replace(b"0.220000", b"0.230000")), want)
        self.assertEqual(DC.constitutional_hash(b'{"constitutional": {}}'), sha(b"{}"))

    def test_a_policy_that_has_no_such_hash_is_unusable(self):
        # tohum/01c "Politikanın sayıları": a JSON float there is policy_invalid, the path named
        floats = {b'{"constitutional": {"a": 1, "confidence_level": 0.95}}': "constitutional.confidence_level",
                  b'{"constitutional": {"z": 0.5, "stage_params": {"x": [1, {"y": 1.0}]}}}':
                      "constitutional.stage_params.x.1.y",
                  b'{"constitutional": {"cap": 1e2}}': "constitutional.cap"}
        for policy, path in floats.items():
            with self.assertRaisesRegex(DC.Unusable, r"\Apolicy_invalid:%s " % path.replace(".", r"\."), msg=policy):
                DC.constitutional_hash(policy)
        for policy in (b"", b"[]", b"{}", b'{"constitutional": []}', b'{"constitutional": null}', b"\xff",
                       b'{"constitutional": {"a": 1, "a": 1}}', b'{"constitutional": {"a": NaN}}',
                       b'{"operating": {"constitutional": {}}}'):
            with self.assertRaises(DC.Unusable, msg=policy):
                DC.constitutional_hash(policy)
        AW.write_checkout(self.root, dict(AW.CHECKOUT, **{"policy.json": b'{"constitutional": {"cap": 0.5}}'}))
        with self.assertRaisesRegex(DC.Unusable, r"\Apolicy_invalid:constitutional\.cap "):
            DC.held(self.root)


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
            self.assertEqual(sorted(p for _, p, _ in w.gh.requests), sorted(GENESIS_READS[kind] + more))
        self.assertIs(AC.Unusable, DC.Unusable)


class Cli(unittest.TestCase):
    def run_cli(self, w: AW.World, stdin: str = '{"target": "toy", "now": "%s", "previous": null}' % AW.TS,
                args=None, files=None):
        """The command on a recorded API of ``w``'s answers and a checkout ``ROOT`` holding ``w``'s summary and the
        operator files ``files`` (``activation_world.CHECKOUT`` when ``None``)."""
        with tempfile.TemporaryDirectory() as tmp:
            api, root = os.path.join(tmp, "api.json"), os.path.join(tmp, "checkout")
            with open(api, "w") as fh:
                json.dump({"%s %s" % key: body for key, (_, body) in w.gh.overrides.items()}, fh)
            AW.write_checkout(root, dict(AW.CHECKOUT if files is None else files,
                                         **{DC.SUMMARY: w.files["summary.json"]}))
            proc = subprocess.run([sys.executable, "-m", "drift.check"] + (["check", api, root] if args is None
                                                                           else args),
                                  input=stdin.encode(), capture_output=True, cwd=REFEREE)
        return proc.returncode, json.loads(proc.stdout), proc.stderr.decode()

    def test_the_three_exits(self):
        clean = {"ok": True, "hard_stop": False, "reasons": [], "stale": False, "activity": []}
        self.assertEqual(self.run_cli(world("copy")), (0, clean, ""))
        code, line, err = self.run_cli(world("toy", (WORKFLOWS, CASES["a workflow on the toy"][2])))
        self.assertEqual((code, line, err), (1, dict(clean, ok=False, hard_stop=True, reasons=["toy_workflows"]), ""))
        # a stale operator check is the other exit 1: the line says it is no hard stop
        stale = '{"target": "toy", "now": "%s", "previous": null}' % later(WEEK + 1)
        self.assertEqual(self.run_cli(world("copy"), stdin=stale), (1, dict(clean, ok=False, stale=True), ""))
        w = world("toy")
        del w.gh.overrides[("GET", "/app")]  # not in the record: the replay answers 404
        fault = {"ok": False, "hard_stop": True, "reasons": None, "stale": None, "activity": None}
        now = '"now": "%s"' % AW.TS
        for got in (self.run_cli(w), self.run_cli(world(), stdin='{"target": "toy", "x": 1, %s}' % now),
                    self.run_cli(world(), stdin='{"target": "toy"}'),
                    self.run_cli(world(), stdin='{"target": "toy", "now": "2026-10-30"}'),
                    self.run_cli(rebased(world(), lambda d: None)),
                    self.run_cli(world(), stdin='{"target": "other", %s}' % now), self.run_cli(world(), args=["check"]),
                    self.run_cli(world(), args=["check", "/nonexistent/api", "/nonexistent/root"]),
                    self.run_cli(world(), files={k: v for k, v in AW.CHECKOUT.items() if k != "policy.json"}),
                    self.run_cli(world(), files={k: v for k, v in AW.CHECKOUT.items() if not k.startswith("seats/")})):
            self.assertEqual((got[0], got[1]), (2, fault))
            self.assertTrue(got[2].startswith("unusable input: "), got[2])

BOT = "snowball-writer[bot]"  # ``activation_world.facts``' ``/app`` slug and GitHub's suffix of an App's bot
OPERATOR = "operator"         # ``activation_world.baseline``'s one ``operator_logins``
SINCE = AW.CHECKED_AT         # that baseline's ``not_before``
X, KEPT_STATE, KEPT_INTEGRATION = "refs/heads/brain/x", "refs/heads/brain/state", "refs/heads/brain/integration"
TYPES = ("push", "force_push", "branch_creation", "branch_deletion", "pr_merge", "merge_queue_merge", "some_new_type")
# tohum/01c "İzinli aktörler", written out: (login, type, ref) allowed; every other triple of the table's axes offends
ALLOWED = {(BOT, kind, ref) for kind in ("push", "branch_creation", "pr_merge")
           for ref in (X, KEPT_STATE, KEPT_INTEGRATION)} | {(OPERATOR, "branch_deletion", X)}


def item(n: int, ts: str, ref: str = X, kind: str = "push", login=BOT, **more) -> dict:
    """An activity item as the API's schema names its fields (the ones read, and two that are not)."""
    return dict({"id": n, "node_id": "A_%d" % n, "before": "0" * 40, "after": "a" * 40, "ref": ref, "timestamp": ts,
                 "activity_type": kind, "actor": None if login is None else {"login": login, "id": 7}}, **more)


def named(n: int, ts: str, ref: str = X, kind: str = "push", login=BOT) -> dict:
    """What ``check``'s ``activity`` says of ``item`` with the same arguments."""
    return {"id": n, "timestamp": ts, "ref": ref, "activity_type": kind, "actor": login}


def acted(*items, kind: str = "toy") -> AW.World:
    """A world whose activity page is ``items``."""
    return world(kind, (ACTIVITY, lambda body: list(items)))


class Activity(unittest.TestCase):
    """tohum/01c "Etkinlik API'si": ``drift.check``'s rules 1-5 of the activity."""

    def test_each_actor_type_and_ref_is_allowed_or_offends_as_the_page_says(self):
        seen = 0
        for login in (BOT, OPERATOR, "someone", None):
            for kind in TYPES:
                for ref in (X, KEPT_STATE, KEPT_INTEGRATION):
                    got = check(acted(item(5, later(60), ref, kind, login)))
                    if (login, kind, ref) in ALLOWED:
                        want = {"ok": True, "hard_stop": False, "reasons": [], "stale": False, "activity": []}
                    else:
                        want = {"ok": False, "hard_stop": True, "reasons": ["ref_change"], "stale": False,
                                "activity": [named(5, later(60), ref, kind, login)]}
                    self.assertEqual(got, want, (login, kind, ref))
                    seen += 1
        self.assertEqual((seen, len(ALLOWED)), (84, 10))

    def test_a_login_is_compared_byte_for_byte_and_the_bot_is_never_an_operator(self):
        for login in ("Operator", "operator ", "snowball-writer", "Snowball-writer[bot]", ""):
            self.assertEqual(check(acted(item(1, later(1), kind="branch_deletion", login=login)))["reasons"],
                             ["ref_change"], login)
            self.assertEqual(check(acted(item(1, later(1), kind="push", login=login)))["reasons"], ["ref_change"], login)
        # a baseline that lists the bot among the operators gives it no deletion
        w = rebased(acted(item(1, later(1), kind="branch_deletion", login=BOT), item(2, later(1), kind="push")),
                    put("activity", "operator_logins", value=[OPERATOR, BOT]))
        self.assertEqual(check(w)["activity"], [named(1, later(1), kind="branch_deletion")])
        # no operator named: nobody deletes
        w = rebased(acted(item(1, later(1), kind="branch_deletion", login=OPERATOR)),
                    put("activity", "operator_logins", value=[]))
        self.assertEqual(check(w)["reasons"], ["ref_change"])
        # the bot is the slug GET /app answers now, not a name of this code
        w = world("toy", ("/app", lambda app: dict(app, slug="another")), (ACTIVITY, lambda body: [
            item(1, later(1)), item(2, later(2), login="another[bot]")]))
        self.assertEqual(check(w)["activity"], [named(1, later(1))])

    def test_only_refs_under_the_brain_s_prefix_are_judged(self):
        for ref in ("refs/heads/main", "refs/heads/brain", "refs/heads/Brain/x", "refs/heads/brainy/x",
                    "refs/tags/brain/x", "brain/x", "refs/heads/x/refs/heads/brain/x", ""):
            self.assertEqual(check(acted(item(1, later(1), ref, "force_push", "someone")))["reasons"], [], ref)
        for ref in ("refs/heads/brain/", "refs/heads/brain/a/b", "refs/heads/brain/state"):
            self.assertEqual(check(acted(item(1, later(1), ref, "force_push", "someone")))["reasons"], ["ref_change"],
                             ref)

    def test_the_window_starts_at_the_later_of_not_before_and_ten_minutes_before_the_previous_start(self):
        bad = lambda ts: item(1, ts, kind="force_push")  # noqa: E731
        judged = lambda ts, previous: check(acted(bad(ts)), previous=previous)["reasons"] == ["ref_change"]  # noqa: E731
        # no cycle before: from not_before, itself inside
        self.assertEqual([judged(later(-1), None), judged(SINCE, None), judged(later(1), None)], [False, True, True])
        # a previous start more than ten minutes after not_before: from 600 s before it
        previous = later(3600)
        self.assertEqual([judged(later(2999), previous), judged(later(3000), previous), judged(later(3001), previous)],
                         [False, True, True])
        self.assertEqual(judged(later(-1), previous), False)
        # a previous start within ten minutes of not_before, at it, or before it: from not_before
        for previous in (later(600), later(599), later(1), SINCE, later(-5000), "0001-01-01T00:00:00Z"):
            self.assertEqual([judged(later(-1), previous), judged(SINCE, previous)], [False, True], previous)
        self.assertEqual([judged(later(0), later(601)), judged(later(1), later(601))], [False, True])
        # the window has no end: an item after the clock is judged
        self.assertEqual(check(acted(bad(later(10 ** 6, AW.TS))))["reasons"], ["ref_change"])
        # the operator lifts the stop by moving not_before past the item
        w = acted(bad(later(50)))
        self.assertEqual(check(w)["reasons"], ["ref_change"])
        self.assertEqual(check(rebased(w, put("activity", "not_before", value=later(50))))["reasons"], ["ref_change"])
        self.assertEqual(check(rebased(w, put("activity", "not_before", value=later(51))))["reasons"], [])

    def test_a_previous_start_that_is_no_time_is_unusable_and_nothing_is_read(self):
        for previous in ("2026-10-30", "2026-10-30T00:00:00+00:00", "2026-02-30T00:00:00Z", 0, True, ["x"], ""):
            w = world()
            with self.assertRaises(DC.Unusable, msg=repr(previous)):
                check(w, previous=previous)
            with self.assertRaises(DC.Unusable, msg=repr(previous)):  # before the caller's repository is compared
                check(w, previous=previous, repo="acme/other")
            self.assertEqual(w.gh.requests, [])

    def test_a_full_page_that_does_not_reach_the_window_s_start_is_unusable(self):
        fill = lambda count, start=1: [item(n, later(n)) for n in range(start, start + count)]  # noqa: E731
        for name, items in (("100 inside", fill(100)), ("101 inside", fill(101)),
                            ("the oldest at the start itself", fill(99) + [item(200, SINCE)]),
                            ("an offender among them", fill(99) + [item(200, later(5), kind="force_push")])):
            with self.assertRaises(DC.Unusable, msg=name):
                check(acted(*items))
        # one item before the start shows the window whole, wherever it stands in the page
        for older in (fill(99) + [item(200, later(-1))], [item(200, later(-1))] + fill(99)):
            self.assertEqual(check(acted(*older))["reasons"], [])
        offender = item(300, later(7), kind="force_push")
        self.assertEqual(check(acted(*([item(200, later(-1)), offender] + fill(98))))["activity"],
                         [named(300, later(7), kind="force_push")])
        # a page under 100 is the whole list
        self.assertEqual(check(acted(*fill(99)))["reasons"], [])
        # the start is the window's: with a previous cycle the same page reaches back before it
        self.assertEqual(check(acted(*fill(100)), previous=later(700))["reasons"], [])
        with self.assertRaises(DC.Unusable):
            check(acted(*fill(100, start=100)), previous=later(700))
        # no second page is asked for
        w = acted(*fill(99))
        check(w)
        self.assertEqual([path for _, path, _ in w.gh.requests if "activity" in path], [ACTIVITY])

    def test_an_item_not_of_the_form_is_unusable_whatever_its_ref(self):
        good = item(1, later(1), "refs/heads/main")
        self.assertEqual(check(acted(good))["reasons"], [])
        cut = lambda key: {k: v for k, v in good.items() if k != key}  # noqa: E731
        bad = [cut("id"), cut("ref"), cut("activity_type"), cut("timestamp"), cut("actor"), dict(good, id="1"),
               dict(good, id=True), dict(good, id=1.0), dict(good, ref=None), dict(good, activity_type=7),
               dict(good, timestamp="2026-10-30T00:00:01+00:00"), dict(good, timestamp="2026-10-30T00:00:01.000Z"),
               dict(good, timestamp="2026-10-32T00:00:01Z"), dict(good, timestamp=1), dict(good, actor="operator"),
               dict(good, actor={}), dict(good, actor={"login": None}), dict(good, actor=[]), "x", None, [good]]
        for n, entry in enumerate(bad):
            with self.assertRaises(DC.Unusable, msg=n):
                check(acted(good, entry))
        for body in ({"items": []}, "x", None):
            with self.assertRaises(DC.Unusable, msg=repr(body)):
                check(world("toy", (ACTIVITY, lambda _: body)))
        w = world()
        w.gh.overrides[("GET", ACTIVITY)] = (404, {"message": "Not Found"})
        with self.assertRaises(DC.Unusable):
            check(w)

    def test_an_app_without_a_slug_is_unusable(self):
        for how in (lambda app: {k: v for k, v in app.items() if k != "slug"}, lambda app: dict(app, slug=""),
                    lambda app: dict(app, slug=None), lambda app: dict(app, slug=7)):
            w = world("copy", ("/app", how))
            with self.assertRaises(DC.Unusable):
                check(w)
            self.assertNotIn(("GET", ACTIVITY, None), w.gh.requests)

    def test_the_offending_items_are_named_in_time_order_beside_the_other_reasons(self):
        items = [item(9, later(30), kind="force_push"), item(3, later(30), login="someone"),
                 item(4, later(10), KEPT_STATE, "branch_deletion", OPERATOR), item(5, later(20)),
                 item(6, later(40), "refs/heads/main", "force_push", "someone"), item(7, later(25), login=None)]
        w = world("toy", (ACTIVITY, lambda body: items), (WORKFLOWS, CASES["a workflow on the toy"][2]))
        self.assertEqual(check(w, now=later(WEEK + 1)), {
            "ok": False, "hard_stop": True, "reasons": ["ref_change", "toy_workflows"], "stale": True,
            "activity": [named(4, later(10), KEPT_STATE, "branch_deletion", OPERATOR), named(7, later(25), login=None),
                         named(3, later(30), login="someone"), named(9, later(30), kind="force_push")]})
        self.assertEqual(w.gh.requests[-1], ("GET", ACTIVITY, None))  # the last read, once
        self.assertEqual(sum(path == ACTIVITY for _, path, _ in w.gh.requests), 1)
        # a caller writing to another repository is told no activity: none was read
        self.assertEqual(check(acted(items[0]), repo="acme/other")["activity"], [])

    def test_the_command_takes_the_previous_start_and_prints_the_items(self):
        w = acted(item(1, later(3000), kind="force_push"))
        stdin = '{"target": "toy", "now": "%s", "previous": %s}'
        code, line, err = Cli.run_cli(self, w, stdin=stdin % (AW.TS, "null"))
        self.assertEqual((code, line, err), (1, {"ok": False, "hard_stop": True, "reasons": ["ref_change"],
                                                 "stale": False,
                                                 "activity": [named(1, later(3000), kind="force_push")]}, ""))
        code, line, err = Cli.run_cli(self, w, stdin=stdin % (AW.TS, '"%s"' % later(3601)))
        self.assertEqual((code, line["ok"], line["activity"], err), (0, True, [], ""))
        for bad in (stdin % (AW.TS, '"yesterday"'), '{"target": "toy", "now": "%s"}' % AW.TS):
            code, line, err = Cli.run_cli(self, w, stdin=bad)
            self.assertEqual((code, line, err.startswith("unusable input: ")), (2, DC.FAULT_LINE, True), err)

    def test_the_last_start_of_a_ledger(self):
        row = lambda n, kind, ts: json.dumps({"part": "events", "kind": kind, "ts": ts, "row_id": str(n)})  # noqa: E731
        with unittest.mock.patch.object(SE.schema, "ledger_reasons", return_value=[]), \
                unittest.mock.patch.object(SE.chain, "parse_row", side_effect=json.loads):
            ledger = "\n".join([row(1, "cycle_start", "2026-10-30T01:00:00Z"), row(2, "merge", "2026-10-30T05:00:00Z"),
                                row(3, "cycle_start", "2026-10-30T00:30:00Z"),
                                json.dumps({"part": "drill", "kind": "cycle_start", "ts": "2026-10-30T09:00:00Z"}),
                                row(4, "status", "2026-10-30T03:00:00Z")]) + "\n"
            self.assertEqual(SE.last_start(ledger.encode()), "2026-10-30T00:30:00Z")  # the last in the file's order
            self.assertEqual(SE.last_start((row(2, "merge", "2026-10-30T05:00:00Z") + "\n").encode()), None)
        self.assertEqual(SE.last_start(b""), None)
        with self.assertRaises(SE.Unusable):
            SE.last_start(b"not a ledger\n")


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


def reads_of_two() -> list[tuple]:
    """The reads of t1's check and then t2's that name either repository, in order: each check reads the visibility
    of both (the baseline names every target's repository), in the names' order, after its own target's facts."""
    both = [("GET", "/repos/acme/t1"), ("GET", "/repos/acme/t2")]
    return [read for tid in ("acme/t1", "acme/t2")
            for read in reads_of(tid)[:-2] + both + reads_of(tid)[-1:]]


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
                          {"checked": ["t1"], "drifted": {"t1": reasons}, "stale": False, "activity": {}}), out)
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
                         (True, ["D5", "D6"], "good", {"checked": ["t1"], "drifted": {}, "stale": False, "activity": {}}), job)
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
                                        "stale": False, "activity": {}})
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
                         (True, {"checked": ["t1", "t2"], "drifted": {}, "stale": False, "activity": {}}), out)
        first_write = next(i for i, (m, _) in enumerate(sent) if m != "GET")
        reads = reads_of_two()
        self.assertEqual([s for s in sent[:first_write] if s in reads], reads)
        self.assertEqual([s for s in sent[first_write:] if s in reads], [])
        self.assertEqual({p.split("/")[3] for m, p in sent[first_write:] if m != "GET"}, {"t1", "t2"})

    def test_a_target_refused_for_its_pulled_is_not_read(self):
        ghs = self.two()
        os.remove(os.path.join(self.temp, "in", "pulled", "t2", "units.json"))
        out, sent = self.run_two(ghs)
        self.assertEqual((out["ok"], out["target"], out["reason"], [t["ok"] for t in out["targets"]]),
                         (False, "t2", "pulled_invalid", [True, False]), out)
        self.assertEqual(out["drift"], {"checked": ["t1"], "drifted": {}, "stale": False, "activity": {}})
        # of the refused target only what t1's baseline names is read: its repository's visibility
        self.assertEqual(ghs["t2"].requests, [("GET", "/repos/acme/t2", None)])

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
                          "drift": {"checked": ["t1"], "drifted": {}, "stale": True, "activity": {}}}, out)
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

    def test_a_stale_stop_is_no_red_job_and_warns_the_operator(self):
        """tohum/01c: "iş kırmızı değildir", "operatör görünür bir uyarı alır"; every other stop stays exit 1."""
        self.ready()
        self.stale_summary(1)
        stale = self.job()
        text, code = J.ending(stale)
        lines = text.split("\n")
        self.assertEqual((code, len(lines), lines[2], json.loads(lines[1])), (0, 3, "", stale), text)
        self.assertEqual(lines[1], json.dumps(stale, sort_keys=True))
        self.assertRegex(lines[0], r"\A::warning title=operator check stale::operator check stale: [ -~]+\Z")
        self.assertEqual(lines[0], J.CLEAN_STOPS["operator_check_stale"])
        self.assertEqual(self.writes(), [])
        # a hard stop beside the stale check is red and carries no warning
        change(self.gh, "/repos/%s/rulesets/1" % YW.REPO, bypass("always"))
        drifted = self.job()
        self.assertEqual((drifted["reason"], drifted["drift"]["stale"]), ("drift", True))
        self.assertEqual(J.ending(drifted), (json.dumps(drifted, sort_keys=True) + "\n", 1))
        change(self.gh, "/repos/%s/rulesets/1" % YW.REPO, bypass("never"))
        # the reason alone does not make a job green, nor does a line without one: only ok does
        self.assertEqual(J.ending(dict(stale, ok=True)), (json.dumps(dict(stale, ok=True), sort_keys=True) + "\n", 0))
        for other in (dict(stale, reason="policy_unusable"), dict(stale, reason="hard_stop"),
                      {k: v for k, v in stale.items() if k != "reason"}):
            self.assertEqual(J.ending(other), (json.dumps(other, sort_keys=True) + "\n", 1), other)
        # a written cycle: one line, exit 0
        self.stale_summary(0)
        job = self.job()
        self.assertEqual((job["ok"], J.ending(job)), (True, (json.dumps(job, sort_keys=True) + "\n", 0)))

    def test_the_command_ends_as_ending_says(self):
        """``main`` writes ``ending``'s text and returns its code (``run`` replaced: the command's own ``run``
        reads the process's environment and sends real requests)."""
        self.assertEqual(list(J.CLEAN_STOPS), ["operator_check_stale"])
        stale = {"job": "yaz", "ok": False, "reason": "operator_check_stale", "targets": []}
        for out in (stale, dict(stale, reason="drift"), dict(stale, ok=True)):
            with unittest.mock.patch.object(J, "run", return_value=out) as run, \
                    unittest.mock.patch.object(sys, "stdout", new_callable=io.StringIO) as stdout:
                code = J.main(["run", "yaz"])
            self.assertEqual((stdout.getvalue(), code), J.ending(out), out)
            self.assertEqual(run.call_args.args[0], "yaz")
        self.assertEqual([J.ending(o)[1] for o in (stale, dict(stale, reason="drift"), dict(stale, ok=True))], [0, 1, 0])

    def test_a_stale_check_stops_every_target_after_all_were_read(self):
        ghs = self.two()
        self.stale_summary(1, [YW.entry("t1"), YW.entry("t2")])
        out, sent = self.run_two(ghs)
        self.assertEqual((out["ok"], out["reason"], out["targets"], out["drift"]),
                         (False, "operator_check_stale", [], {"checked": ["t1", "t2"], "drifted": {}, "stale": True, "activity": {}}),
                         out)
        self.assertNotIn("target", out)
        self.assertEqual(([s for s in sent if s[0] != "GET"], self.signer.payloads), ([], []))
        self.assertEqual([s for s in sent if s in reads_of_two()], reads_of_two())

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


class YazActivity(TLW.StateBase):
    """The activity in ``yaz``: the window's start is the pulled ledger's, a stop writes nothing and lasts."""

    ready, job = Yaz.ready, Yaz.job

    def act(self, *items) -> None:
        self.gh.overrides[("GET", "/repos/%s/activity?per_page=100" % YW.REPO)] = (200, list(items))

    def started(self) -> str:
        """The ``ts`` of the last ``cycle_start`` row of the state ``pulled`` carries, read here by ``json``."""
        rows = [json.loads(line) for line in self.state[B.STATE_LEDGER].decode().splitlines()]
        return [r["ts"] for r in rows if (r["part"], r["kind"]) == ("events", "cycle_start")][-1]

    def test_an_item_that_is_not_allowed_stops_the_job_until_the_operator_moves_not_before(self):
        self.ready()
        at = later(-300, self.started())
        self.act(item(8, at, KEPT_STATE, "force_push", "someone"), item(9, at))
        refs = dict(self.gh.refs)
        for _ in range(2):  # the stop wrote nothing, so the next job judges the same window
            out = self.job()
            self.assertEqual((out["ok"], out["reason"], out["reasons"], out["target"], out["targets"], out["drift"]),
                             (False, "drift", ["ref_change"], "t1", [],
                              {"checked": ["t1"], "drifted": {"t1": ["ref_change"]}, "stale": False,
                               "activity": {"t1": [named(8, at, KEPT_STATE, "force_push", "someone")]}}), out)
            self.assertEqual((self.writes(), self.gh.refs, self.signer.payloads), ([], refs, []))
        TLW.write_tree(self.workspace, {J.SUMMARY: YW.summary(
            None, activity={"operator_logins": [OPERATOR], "not_before": later(1, at)}).decode()})
        job = self.job()
        self.assertEqual((self.line(job)["ok"], job["drift"]["activity"], bool(self.writes())), (True, {}, True), job)

    def test_the_window_starts_ten_minutes_before_the_pulled_ledger_s_last_cycle_start(self):
        self.ready()
        self.assertGreater(DC.moment(self.started()) - DC.moment(SINCE), datetime.timedelta(minutes=10))
        self.act(item(8, later(-600, self.started()), kind="force_push"))
        out = self.job()
        self.assertEqual((out["reason"], out["reasons"], self.writes()), ("drift", ["ref_change"], []), out)
        self.act(item(8, later(-601, self.started()), kind="force_push"), item(9, later(-600, self.started())))
        job = self.job()
        self.assertEqual((self.line(job)["ok"], job["drift"]["activity"], bool(self.writes())), (True, {}, True), job)

    def test_a_ledger_that_does_not_conform_gives_the_widest_window(self):
        art = unittest.mock.Mock(state={B.STATE_LEDGER: b"not a ledger\n"})
        self.assertIsNone(J._previous_start(art))
        self.assertIsNone(J._previous_start(unittest.mock.Mock(state={B.STATE_LEDGER: b""})))
        self.assertEqual(J._previous_start(unittest.mock.Mock(state={B.STATE_LEDGER: self.state[B.STATE_LEDGER]})),
                         self.started())


class YazCheckout(TLW.StateBase):
    """``yaz`` and the operator files of its checkout (tohum/01c's three hashes; ``Yaz``'s world)."""
    ready, job = Yaz.ready, Yaz.job

    def test_an_operator_file_other_than_the_recorded_one_stops_the_job(self):
        self.ready()
        refs = dict(self.gh.refs)
        policy = json.loads(AW.CHECKOUT["policy.json"])
        policy["constitutional"]["monthly_cap_usd"] = "changed"
        cases = {"vectors_hash_mismatch": {"vectors/chain/V1.json": b'{"row": 2}\n'},
                 "seats_hash_mismatch": {"seats/more.json": b"{}"},
                 "constitutional_hash_mismatch": {"policy.json": json.dumps(policy).encode()}}
        for reason, files in cases.items():
            AW.write_checkout(self.workspace, files)
            out = self.job()
            self.assertEqual((out["ok"], out["reason"], out["reasons"], out["target"], out["targets"], out["drift"]),
                             (False, "drift", [reason], "t1", [],
                              {"checked": ["t1"], "drifted": {"t1": [reason]}, "stale": False, "activity": {}}), out)
            self.assertEqual((self.writes(), self.gh.refs, self.signer.payloads), ([], refs, []))
            for path in files:
                os.remove(os.path.join(self.workspace, *path.split("/")))
            AW.write_checkout(self.workspace)
        # the pulled policy is not what is hashed: with another constitutional value than the checkout's, written
        YazPolicy.repolicied(self, "t1", lambda doc: doc["constitutional"].update(monthly_cap_usd=10001))
        job = self.job()
        self.assertEqual((self.line(job)["ok"], job["drift"], bool(self.writes())),
                         (True, {"checked": ["t1"], "drifted": {}, "stale": False, "activity": {}}, True), job)

    def test_a_checkout_without_an_operator_file_is_unusable_and_no_request_is_sent(self):
        self.ready()
        refs = dict(self.gh.refs)
        import shutil

        def no_policy(root):
            os.remove(os.path.join(root, "policy.json"))

        def no_vectors(root):
            shutil.rmtree(os.path.join(root, "vectors"))

        def seats_a_file(root):
            shutil.rmtree(os.path.join(root, "seats"))
            AW.write_checkout(root, {"seats": b""})

        def a_link_among_the_vectors(root):
            os.symlink(os.path.join(root, "policy.json"), os.path.join(root, "vectors", "policy.json"))

        def a_float(root):
            AW.write_checkout(root, {"policy.json": b'{"constitutional": {"monthly_cap_usd": 0.5}}'})

        for how in (no_policy, no_vectors, seats_a_file, a_link_among_the_vectors, a_float):
            how(self.workspace)
            with self.assertRaisesRegex(J.Unusable, r"\Ayaz: drift: ", msg=how.__name__):
                self.job()
            self.assertEqual((self.gh.requests, self.gh.refs, self.signer.payloads), ([], refs, []), how.__name__)
            for name in ("vectors", "seats"):
                path = os.path.join(self.workspace, name)
                shutil.rmtree(path) if os.path.isdir(path) else os.path.exists(path) and os.remove(path)
            AW.write_checkout(self.workspace)
        with self.assertRaisesRegex(J.Unusable, r"\Ayaz: drift: policy_invalid:constitutional\.monthly_cap_usd "):
            a_float(self.workspace)
            self.job()


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
        self.assertEqual(out["drift"], {"checked": ["t1", "t2"], "drifted": {}, "stale": False, "activity": {}})
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
        self.assertEqual(len(LISTED), 14)


LISTED = (Check, Baseline, Compared, Activity, Held, Genesis, Cli, Yaz, YazActivity, YazCheckout, YazPolicy, Order, YazGenesis, Listed)


def load_tests(loader, standard, pattern):
    """This module's own tests: ``Yaz`` and ``Order`` inherit ``test_loop_write.StateBase``'s world, not its bases'
    tests (a class left out of this list is not run by the manifest's command: ``Listed`` reads the list)."""
    suite = unittest.TestSuite()
    for case in LISTED:
        names = [n for n in loader.getTestCaseNames(case) if n in vars(case)]
        suite.addTests(case(n) for n in names)
    return suite
