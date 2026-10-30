"""Test 49 (asama-0/09) and group ``refs`` (tohum/29d): ``target.write``, the one way to write to a target.

- the ref rule: every ref written is a valid branch under ``refs/heads/brain/``; ``main``, ``brain/``'s
  look-alikes and other ref spaces are refused, each git name rule with its own case;
- the route rule: only the listed REST and Git Data routes of the configured repository; the contents API,
  the ``merges`` endpoint, ref deletion, repository settings, GraphQL, another repository, a force update,
  a squash or rebase merge and a merge of a pull request the guard has not seen open on ``brain/`` refuse;
- the writer against an in-process GitHub (``fake_github``) with the target's rulesets: branch, commit,
  pull request, check, merge; every attempt on ``main`` is refused before it is sent and ``main`` never moves;
- revert: the revert commit's tree is the merge's first parent's tree, it goes through a pull request and a
  merge, and after that merge the branch holds that tree; a merge that is not the head, or a commit that is
  not a merge, is refused;
- responses that do not say what was asked are errors; the HTTPS transport sends the token only to the API
  and follows no redirect;
- one way: no other module under ``referee/`` reaches the network or pushes with git;
- the command line: one JSON line, exit 0 / 1 / 2.
"""

from __future__ import annotations

import ast
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.request
import urllib.response
from email.message import Message

REFEREE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REFEREE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from target import write as W  # noqa: E402
from fake_github import FakeGitHub  # noqa: E402

REPO = "acme/toy"
P = "/repos/acme/toy/"
A = "a" * 40
B = "b" * 40
GATE = "snowball/gate"


def check(method, rest, body=None, pulls=None, prefix=P):
    return W.Guard(REPO, pulls).check(method, prefix + rest, body)


OPEN = {"base": "brain/integration", "head": "brain/c/1", "head_sha": A, "state": "open"}


class RefRule(unittest.TestCase):
    def test_brain_branches_are_writable(self):
        for ref in ("refs/heads/brain/integration", "refs/heads/brain/state", "refs/heads/brain/c/k0-17",
                    "refs/heads/brain/c/a.b_c-D9", "refs/heads/brain/c/x/y"):
            self.assertEqual(W.ref_reasons(ref), [], ref)

    def test_outside_brain(self):
        for ref in ("refs/heads/main", "refs/heads/master", "refs/heads/brain", "refs/heads/brainx/a",
                    "refs/heads/Brain/a", "refs/heads/BRAIN/a", "refs/tags/brain/a", "refs/brain/a",
                    "refs/pull/1/head", "brain/c/1", "heads/brain/c/1", " refs/heads/brain/c/1",
                    "refs/heads//brain/c/1", "refs/heads/x/brain/c/1", "", None, 7, ["refs/heads/brain/a"]):
            self.assertEqual(W.ref_reasons(ref), ["ref_outside_brain"], repr(ref))

    def test_git_name_rules(self):
        cases = {
            "empty component": "brain/", "double slash": "brain//a", "trailing slash": "brain/a/",
            "dot dot": "brain/a..b", "dot dot component": "brain/../main", "leading dot": "brain/.a",
            "lock": "brain/a.lock", "lock inner": "brain/a.lock/b", "trailing dot": "brain/a.",
            "colon": "brain/a:b", "tilde": "brain/a~1", "caret": "brain/a^", "space": "brain/a b",
            "backslash": "brain/a\\b", "at brace": "brain/a@{1}", "star": "brain/a*", "question": "brain/a?",
            "bracket": "brain/a[", "control": "brain/a\x01", "newline": "brain/a\n", "del": "brain/a\x7f",
            "non ascii": "brain/ç", "percent": "brain/a%2f",
        }
        for why, name in cases.items():
            self.assertEqual(W.ref_reasons("refs/heads/" + name), ["ref_invalid"], why)

    def test_cross_repository_head_is_refused(self):
        self.assertEqual(W.branch_reasons("evil:brain/c/1"), ["ref_outside_brain"])
        self.assertEqual(W.branch_reasons("brain:brain/c/1"), ["ref_outside_brain"])
        self.assertEqual(W.branch_reasons("brain/c:x"), ["ref_invalid"])


class RouteRule(unittest.TestCase):
    def test_allowed_routes(self):
        allowed = [
            ("GET", "git/ref/heads/main", None, []), ("GET", "git/ref/heads/brain/integration", None, []),
            ("GET", "git/commits/" + A, None, []), ("GET", "pulls/12", None, []),
            ("POST", "git/refs", {"ref": "refs/heads/brain/c/1", "sha": A}, ["refs/heads/brain/c/1"]),
            ("PATCH", "git/refs/heads/brain/state", {"sha": A}, ["refs/heads/brain/state"]),
            ("PATCH", "git/refs/heads/brain/state", {"sha": A, "force": False}, ["refs/heads/brain/state"]),
            ("POST", "git/commits", {"message": "m", "tree": A, "parents": [B]}, []),
            ("POST", "git/commits", {"message": "m", "tree": A, "parents": [A, B]}, []),
            ("POST", "pulls", {"title": "t", "head": "brain/c/1", "base": "brain/integration"}, []),
            ("POST", "pulls", {"title": "t", "head": "brain/c/1", "base": "brain/integration", "body": ""}, []),
            ("POST", "check-runs", {"name": GATE, "head_sha": A, "status": "completed", "conclusion": "success"}, []),
            ("POST", "check-runs", {"name": GATE, "head_sha": A, "status": "completed", "conclusion": "failure",
                                    "output": {"title": "t", "summary": ""}}, []),
        ]
        for method, rest, body, refs in allowed:
            self.assertEqual(check(method, rest, body), ([], refs), (method, rest, body))
        self.assertEqual(check("PUT", "pulls/3/merge", {"sha": A, "merge_method": "merge"}, {3: OPEN}),
                         ([], ["refs/heads/brain/integration"]))

    def test_main_and_outside_brain_refused_on_every_writing_route(self):
        for ref in ("refs/heads/main", "refs/heads/release/1", "refs/tags/v1"):
            self.assertEqual(check("POST", "git/refs", {"ref": ref, "sha": A}), (["ref_outside_brain"], []))
        for name in ("main", "dev", "brainx"):
            self.assertEqual(check("PATCH", "git/refs/heads/" + name, {"sha": A}), (["ref_outside_brain"], []))
        for head, base in (("brain/c/1", "main"), ("main", "brain/integration"), ("feature", "dev")):
            reasons, _ = check("POST", "pulls", {"title": "t", "head": head, "base": base})
            self.assertEqual(reasons, ["ref_outside_brain"], (head, base))
        onto_main = dict(OPEN, base="main")
        self.assertEqual(check("PUT", "pulls/3/merge", {"sha": A, "merge_method": "merge"}, {3: onto_main}),
                         (["ref_outside_brain"], []))
        from_main = dict(OPEN, head="main")
        self.assertEqual(check("PUT", "pulls/3/merge", {"sha": A, "merge_method": "merge"}, {3: from_main}),
                         (["ref_outside_brain"], []))

    def test_routes_outside_the_list(self):
        refused = [
            ("PUT", "contents/src/a.js", {"message": "m", "content": "", "branch": "brain/c/1"}),
            ("POST", "merges", {"base": "brain/integration", "head": "brain/c/1"}),
            ("DELETE", "git/refs/heads/brain/c/1", None), ("DELETE", "git/refs/heads/brain/integration", None),
            ("PATCH", "pulls/3", {"base": "main"}), ("POST", "pulls/3/update-branch", {}),
            ("POST", "git/blobs", {"content": "", "encoding": "utf-8"}), ("POST", "git/trees", {"tree": []}),
            ("POST", "git/tags", {}), ("PUT", "branches/main/protection", {}), ("POST", "rulesets", {}),
            ("POST", "forks", {}), ("POST", "dispatches", {}), ("POST", "actions/workflows/x/dispatches", {}),
            ("GET", "contents/a", None), ("GET", "git/refs", None), ("HEAD", "pulls/3", None),
            ("POST", "git/ref/heads/brain/c/1", {"sha": A}), ("PATCH", "git/refs/brain/c/1", {"sha": A}),
            ("PUT", "pulls/0/merge", {"sha": A, "merge_method": "merge"}),
            ("PUT", "pulls/03/merge", {"sha": A, "merge_method": "merge"}),
        ]
        for method, rest, body in refused:
            self.assertEqual(check(method, rest, body, {3: OPEN}), (["route_not_allowed"], []), (method, rest))
        self.assertEqual(W.Guard(REPO).check("PATCH", "/repos/acme/toy", {"default_branch": "brain/x"}),
                         (["route_not_allowed"], []))
        self.assertEqual(W.Guard(REPO).check("POST", "/graphql", {"query": "mutation"}), (["route_not_allowed"], []))
        for other in ("/repos/acme/other/", "/repos/acme/toy2/", "/repos/acmex/toy/", "/repos/ACME/toy/",
                      "https://api.github.com/repos/acme/toy/", "/repos/acme/toy/../other/"):
            reasons, _ = W.Guard(REPO).check("POST", other + "git/refs", {"ref": "refs/heads/brain/c/1", "sha": A})
            self.assertEqual(reasons, ["route_not_allowed"], other)

    def test_path_shapes(self):
        body = {"ref": "refs/heads/brain/c/1", "sha": A}
        for rest in ("git/refs?x=1", "git/refs#x", "git/refs/", "git//refs", "git/%72efs", "git/refs ",
                     "git\\refs", "", "git/refs\n"):
            self.assertEqual(check("POST", rest, body), (["route_not_allowed"], []), repr(rest))
        self.assertEqual(check("PATCH", "git/refs/heads/brain/c/../../main", {"sha": A}), (["route_not_allowed"], []))
        self.assertEqual(check("GET", "git/ref/heads/brain/a..b"), (["route_not_allowed"], []))
        for name in ("brain/c/1?force=true", "brain/c/1#x", "brain/c/1/", "brain//c/1", "brain/c/%31", "brain/c/1 "):
            self.assertEqual(check("PATCH", "git/refs/heads/" + name, {"sha": A}), (["route_not_allowed"], []), name)
        self.assertEqual(check("GET", "git/ref/heads/brain/a~1"), (["ref_invalid"], []))
        self.assertEqual(check("GET", "git/ref/heads/main", {"x": 1}), (["body_invalid"], []))
        self.assertEqual(check("GET", "git/commits/" + A.upper()), (["route_not_allowed"], []))

    def test_bodies(self):
        bad = [
            ("POST", "git/refs", {"ref": "refs/heads/brain/c/1"}), ("POST", "git/refs", {"ref": "refs/heads/brain/c/1",
                                                                                         "sha": A, "force": True}),
            ("POST", "git/refs", {"ref": "refs/heads/brain/c/1", "sha": A[:39]}), ("POST", "git/refs", None),
            ("POST", "git/refs", [["ref", "refs/heads/brain/c/1"]]),
            ("PATCH", "git/refs/heads/brain/state", {"sha": A.upper()}),
            ("PATCH", "git/refs/heads/brain/state", {"sha": A, "ref": "refs/heads/main"}),
            ("POST", "git/commits", {"message": "m", "tree": A, "parents": []}),
            ("POST", "git/commits", {"message": "m", "tree": A, "parents": [A, B, A]}),
            ("POST", "git/commits", {"message": "", "tree": A, "parents": [A]}),
            ("POST", "git/commits", {"message": "m", "tree": A, "parents": [A], "author": {}}),
            ("POST", "git/commits", {"message": "m", "tree": A, "parents": A}),
            ("POST", "pulls", {"title": "", "head": "brain/c/1", "base": "brain/integration"}),
            ("POST", "pulls", {"title": "t", "head": "brain/c/1", "base": "brain/integration", "draft": True}),
            ("POST", "pulls", {"title": "t", "head": "brain/c/1", "base": "brain/integration",
                               "maintainer_can_modify": True}),
            ("POST", "check-runs", {"name": GATE, "head_sha": A, "status": "in_progress", "conclusion": "success"}),
            ("POST", "check-runs", {"name": GATE, "head_sha": A, "status": "completed", "conclusion": "neutral"}),
            ("POST", "check-runs", {"name": GATE, "head_sha": A, "status": "completed", "conclusion": "success",
                                    "actions": []}),
            ("POST", "check-runs", {"name": GATE, "head_sha": A, "status": "completed", "conclusion": "success",
                                    "output": {"title": "t", "summary": "", "annotations": []}}),
            ("PUT", "pulls/3/merge", {"merge_method": "merge"}),
            ("PUT", "pulls/3/merge", {"sha": A, "merge_method": "merge", "commit_message": "x"}),
        ]
        for method, rest, body in bad:
            self.assertEqual(check(method, rest, body, {3: OPEN}), (["body_invalid"], []), (method, rest, body))

    def test_force_update_refused(self):
        for force in (True, 1, "false", None):
            self.assertEqual(check("PATCH", "git/refs/heads/brain/state", {"sha": A, "force": force}),
                             (["force_update"], []), force)

    def test_merge_rules(self):
        body = {"sha": A, "merge_method": "merge"}
        for method in ("squash", "rebase", None):
            self.assertEqual(check("PUT", "pulls/3/merge", dict(body, merge_method=method), {3: OPEN}),
                             (["merge_method"], []))
        self.assertEqual(check("PUT", "pulls/3/merge", body), (["merge_unknown_pull"], []))
        self.assertEqual(check("PUT", "pulls/3/merge", body, {4: OPEN}), (["merge_unknown_pull"], []))
        self.assertEqual(check("PUT", "pulls/3/merge", body, {3: dict(OPEN, state="closed")}),
                         (["merge_not_open"], []))
        self.assertEqual(check("PUT", "pulls/3/merge", dict(body, sha=B), {3: OPEN}), (["merge_head_moved"], []))
        self.assertEqual(check("PUT", "pulls/3/merge", dict(body, commit_title=""), {3: OPEN}), (["body_invalid"], []))

    def test_observe_records_pulls_only_from_pull_responses(self):
        g = W.Guard(REPO)
        resp = {"number": 3, "state": "open", "base": {"ref": "brain/integration"},
                "head": {"ref": "brain/c/1", "sha": A}}
        g.observe("GET", P + "git/commits/" + A, resp)
        g.observe("GET", "/repos/acme/other/pulls/3", resp)
        self.assertEqual(g.pulls, {})
        with self.assertRaises(W.ApiError):
            g.observe("GET", P + "pulls/4", resp)
        for broken in ({}, dict(resp, number="3"), dict(resp, number=True), dict(resp, head={"ref": "brain/c/1"})):
            with self.assertRaises(W.ApiError):
                g.observe("POST", P + "pulls", broken)
        g.observe("GET", P + "pulls/3", resp)
        self.assertEqual(g.pulls[3]["base"], "brain/integration")
        g.observe("GET", P + "pulls/3", dict(resp, base={"ref": "main"}))
        self.assertEqual(g.check("PUT", P + "pulls/3/merge", {"sha": A, "merge_method": "merge"}),
                         (["ref_outside_brain"], []))

    def test_repo_must_be_one_name(self):
        for repo in ("acme", "acme/toy/x", "../toy", "acme/..", "", None, "acme/to y"):
            with self.assertRaises(W.Unusable):
                W.Guard(repo)


def world():
    """A target: ``main`` and ``brain/integration`` at the same commit, as activation cuts it."""
    gh = FakeGitHub(REPO)
    root = gh.seed_commit("t0")
    gh.refs["main"] = root
    gh.refs["brain/integration"] = root
    return gh, W.Writer(REPO, gh), root


def writes(gh):
    return [r for r in gh.requests if r[0] != "GET"]


def written_refs(gh):
    refs = []
    for method, path, body in writes(gh):
        if method == "POST" and path.endswith("/git/refs"):
            refs.append(body["ref"])
        elif method == "PATCH":
            refs.append("refs/heads/" + path.split("/git/refs/heads/", 1)[1])
        elif method == "PUT" and path.endswith("/merge"):
            refs.append("refs/heads/" + gh.pulls[int(path.split("/")[-2])]["base"])
    return refs


def candidate(gh, wr, cid="brain/c/1", tree="t1"):
    """A candidate commit on its own branch, the way the gate publishes one; returns (pull, head sha)."""
    base = wr.head("brain/integration")
    tree_sha = gh.commits[gh.seed_commit(tree)]["tree"]
    sha = wr.commit("candidate " + cid, tree_sha, [base])
    wr.create_branch(cid, sha)
    return wr.open_pull(cid, "brain/integration", "candidate " + cid), sha


class WriterLoop(unittest.TestCase):
    def test_branch_pull_check_merge(self):
        gh, wr, root = world()
        n, sha = candidate(gh, wr)
        wr.check(sha, GATE, "success", "criteria 1-8 hold")
        merged = wr.merge(n, sha)
        self.assertEqual(gh.refs["brain/integration"], merged)
        self.assertEqual(gh.commits[merged]["parents"], [root, sha])
        self.assertEqual(gh.commits[merged]["tree"], gh.commits[sha]["tree"])
        self.assertEqual(gh.refs["main"], root)
        self.assertEqual(written_refs(gh), ["refs/heads/brain/c/1", "refs/heads/brain/integration"])
        self.assertTrue(all(r.startswith("refs/heads/brain/") for r in written_refs(gh)))
        self.assertTrue(all(path.startswith(P) for _, path, _ in gh.requests))

    def test_the_ruleset_still_holds_without_the_check(self):
        gh, wr, _ = world()
        n, sha = candidate(gh, wr)
        with self.assertRaises(W.ApiError) as ctx:
            wr.merge(n, sha)
        self.assertEqual(ctx.exception.status, 405)

    def test_brain_state_update_is_a_fast_forward(self):
        gh, wr, root = world()
        state = gh.seed_commit("s0")
        wr.create_branch("brain/state", state)
        nxt = wr.commit("cycle 1", gh.commits[state]["tree"], [state])
        wr.update_branch("brain/state", nxt)
        self.assertEqual(gh.refs["brain/state"], nxt)
        self.assertEqual(writes(gh)[-1], ("PATCH", P + "git/refs/heads/brain/state", {"sha": nxt, "force": False}))
        with self.assertRaises(W.ApiError):  # a rewind is not a fast-forward and force is never sent
            wr.update_branch("brain/state", state)
        self.assertEqual(gh.refs["brain/state"], nxt)
        with self.assertRaises(W.ApiError):  # the integration branch takes no direct push
            wr.update_branch("brain/integration", nxt)

    def test_every_attempt_on_main_is_refused_before_it_is_sent(self):
        gh, wr, root = world()
        n, sha = candidate(gh, wr)
        gh.pulls[9] = {"base": "main", "head": "brain/c/1", "state": "open", "merged": False, "sha": sha}
        sent = len(gh.requests)
        attempts = [
            lambda: wr.create_branch("main", sha), lambda: wr.update_branch("main", sha),
            lambda: wr.create_branch("feature/x", sha), lambda: wr.open_pull("brain/c/1", "main", "t"),
            lambda: wr.open_pull("main", "brain/integration", "t"), lambda: wr.create_branch("brain/../main", sha),
        ]
        for attempt in attempts:
            with self.assertRaises(W.Refused):
                attempt()
        self.assertEqual(len(gh.requests), sent)
        wr.check(sha, GATE, "success")
        with self.assertRaises(W.Refused) as ctx:  # a pull onto main made by someone else: read, then refused
            wr.merge(9, sha)
        self.assertEqual(ctx.exception.reasons, ["ref_outside_brain"])
        self.assertEqual(gh.requests[-1][0], "GET")
        self.assertEqual(gh.refs["main"], root)
        self.assertNotIn(("PUT", P + "pulls/9/merge"), [(m, p) for m, p, _ in gh.requests])

    def test_a_pull_whose_base_changed_to_main_is_refused(self):
        gh, wr, root = world()
        n, sha = candidate(gh, wr)
        wr.check(sha, GATE, "success")
        gh.pulls[n]["base"] = "main"  # retargeted after it was opened
        with self.assertRaises(W.Refused):
            wr.merge(n, sha)
        self.assertEqual(gh.refs["main"], root)

    def test_a_head_that_moved_is_refused(self):
        gh, wr, _ = world()
        n, sha = candidate(gh, wr)
        wr.check(sha, GATE, "success")
        newer = gh.seed_commit("t9", [sha])
        gh.refs["brain/c/1"] = newer
        with self.assertRaises(W.Refused) as ctx:
            wr.merge(n, sha)
        self.assertEqual(ctx.exception.reasons, ["merge_head_moved"])

    def test_responses_that_do_not_answer_the_question(self):
        gh, wr, root = world()
        gh.overrides[("GET", P + "git/ref/heads/brain/integration")] = (
            200, {"ref": "refs/heads/brain/integration-old", "object": {"sha": root}})
        with self.assertRaises(W.ApiError):
            wr.head("brain/integration")
        gh.overrides[("GET", P + "git/commits/" + root)] = (200, {"sha": A, "tree": {"sha": B}, "parents": []})
        with self.assertRaises(W.ApiError):
            wr.read_commit(root)
        gh.overrides[("GET", P + "git/ref/heads/main")] = (404, {"message": "Not Found"})
        with self.assertRaises(W.ApiError):
            wr.head("main")
        gh.overrides[("POST", P + "git/commits")] = (201, {"sha": "x"})
        with self.assertRaises(W.ApiError):
            wr.commit("m", gh.commits[root]["tree"], [root])

    def test_a_merge_response_that_did_not_land(self):
        gh, wr, root = world()
        n, sha = candidate(gh, wr)
        wr.check(sha, GATE, "success")
        gh.overrides[("PUT", P + "pulls/%d/merge" % n)] = (200, {"sha": B, "merged": True})
        with self.assertRaises(W.ApiError):
            wr.merge(n, sha)
        del gh.overrides[("PUT", P + "pulls/%d/merge" % n)]

        def unmerged(method, path, body):  # the merge lands but the response says it did not
            status, data = gh(method, path, body)
            return (status, dict(data, merged=False)) if method == "PUT" else (status, data)
        with self.assertRaises(W.ApiError):
            W.Writer(REPO, unmerged).merge(n, sha)

    def test_a_pull_created_elsewhere(self):
        gh, wr, root = world()
        gh.refs["brain/c/1"] = root
        gh.overrides[("POST", P + "pulls")] = (201, {"number": 5, "state": "open", "base": {"ref": "brain/other"},
                                                     "head": {"ref": "brain/c/1", "sha": root}})
        with self.assertRaises(W.ApiError):
            wr.open_pull("brain/c/1", "brain/integration", "t")


class Revert(unittest.TestCase):
    def merged(self):
        gh, wr, root = world()
        n, sha = candidate(gh, wr)
        wr.check(sha, GATE, "success")
        return gh, wr, root, wr.merge(n, sha)

    def test_revert_tree_is_the_first_parents_tree(self):
        gh, wr, root, merge = self.merged()
        out = wr.revert("brain/integration", merge, "brain/c/revert-1", "revert: test_regression")
        first = gh.commits[merge]["parents"][0]
        self.assertEqual(out["tree"], gh.commits[first]["tree"])
        self.assertEqual(gh.commits[out["commit"]], {"tree": gh.commits[first]["tree"], "parents": [merge],
                                                     "message": "revert: test_regression"})
        self.assertEqual(gh.refs["brain/c/revert-1"], out["commit"])
        self.assertEqual(gh.pulls[out["pull"]]["base"], "brain/integration")
        self.assertEqual(gh.refs["brain/integration"], merge)  # the revert is a pull request, not a push
        wr.check(out["commit"], GATE, "success")
        reverted = wr.merge(out["pull"], out["commit"])
        self.assertEqual(gh.commits[reverted]["tree"], gh.commits[root]["tree"])
        self.assertEqual(gh.commits[reverted]["parents"], [merge, out["commit"]])
        self.assertEqual(gh.refs["main"], root)
        self.assertTrue(all(r.startswith("refs/heads/brain/") for r in written_refs(gh)))

    def test_only_the_head_is_reverted(self):
        gh, wr, root, merge = self.merged()
        n, sha = candidate(gh, wr, "brain/c/2", "t2")
        wr.check(sha, GATE, "success")
        wr.merge(n, sha)
        sent = len(writes(gh))
        with self.assertRaises(W.Refused) as ctx:
            wr.revert("brain/integration", merge, "brain/c/revert-1", "revert")
        self.assertEqual(ctx.exception.reasons, ["revert_not_head"])
        self.assertEqual(len(writes(gh)), sent)

    def test_only_a_merge_is_reverted(self):
        gh, wr, root = world()
        gh.direct_push_denied = set()
        child = wr.commit("plain", gh.commits[root]["tree"], [root])
        wr.update_branch("brain/integration", child)
        sent = len(writes(gh))
        with self.assertRaises(W.Refused) as ctx:
            wr.revert("brain/integration", child, "brain/c/revert-1", "revert")
        self.assertEqual(ctx.exception.reasons, ["revert_not_merge"])
        self.assertEqual(len(writes(gh)), sent)

    def test_pure_rule(self):
        commits = {A: {"tree": "1" * 40, "parents": []}, B: {"tree": "2" * 40, "parents": [A, "c" * 40]},
                   "c" * 40: {"tree": "3" * 40, "parents": [A]}, "d" * 40: {"tree": "4" * 40, "parents": [A]}}
        self.assertEqual(W.revert_commit(commits, B, B), ([], {"tree": "1" * 40, "parents": [B]}))
        self.assertEqual(W.revert_commit(commits, "d" * 40, B), (["revert_not_head"], None))
        self.assertEqual(W.revert_commit(commits, "d" * 40, "d" * 40), (["revert_not_merge"], None))
        self.assertEqual(W.revert_commit(commits, "e" * 40, "e" * 40), (["commit_unknown"], None))
        self.assertEqual(W.revert_commit({B: commits[B]}, B, B), (["commit_unknown"], None))
        three = {B: {"tree": "2" * 40, "parents": [A, A, A]}, A: commits[A]}
        self.assertEqual(W.revert_commit(three, B, B), (["revert_not_merge"], None))


class _FakeHttps(urllib.request.BaseHandler):
    handler_order = 100

    def __init__(self, answers):
        self.answers = list(answers)
        self.seen = []

    def https_open(self, req):
        self.seen.append(req)
        status, body, extra = self.answers.pop(0)
        headers = Message()
        for k, v in extra.items():
            headers[k] = v
        resp = urllib.response.addinfourl(io.BytesIO(body), headers, req.full_url, status)
        resp.msg = "x"
        return resp


class Transport(unittest.TestCase):
    def test_request_shape(self):
        fake = _FakeHttps([(201, b'{"sha": "%s"}' % A.encode(), {})])
        t = W.HttpTransport("tok", handlers=(fake,))
        status, data = t("POST", P + "git/commits", {"message": "m", "tree": A, "parents": [B]})
        self.assertEqual((status, data), (201, {"sha": A}))
        req = fake.seen[0]
        self.assertEqual(req.full_url, "https://api.github.com" + P + "git/commits")
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.get_header("Authorization"), "Bearer tok")
        self.assertEqual(json.loads(req.data), {"message": "m", "tree": A, "parents": [B]})

    def test_no_redirect_is_followed(self):
        for code in (301, 302, 303, 307, 308):
            fake = _FakeHttps([(code, b"", {"Location": "https://evil.example/x"}), (200, b"{}", {})])
            t = W.HttpTransport("tok", handlers=(fake,))
            with self.assertRaises(W.ApiError) as ctx:
                t("POST", P + "git/refs", {"ref": "refs/heads/brain/c/1", "sha": A})
            self.assertEqual(ctx.exception.status, code)
            self.assertEqual([r.full_url for r in fake.seen], ["https://api.github.com" + P + "git/refs"])

    def test_errors(self):
        fake = _FakeHttps([(422, b'{"message": "no"}', {}), (200, b"<html>", {})])
        t = W.HttpTransport("tok", handlers=(fake,))
        with self.assertRaises(W.ApiError) as ctx:
            t("GET", P + "pulls/1", None)
        self.assertEqual(ctx.exception.status, 422)
        with self.assertRaises(W.ApiError):
            t("GET", P + "pulls/1", None)
        for token in ("", "a\nb", None):
            with self.assertRaises(W.Unusable):
                W.HttpTransport(token)

    def test_writer_over_http_refuses_before_the_socket(self):
        fake = _FakeHttps([])
        wr = W.Writer(REPO, W.HttpTransport("tok", handlers=(fake,)))
        with self.assertRaises(W.Refused):
            wr.create_branch("main", A)
        self.assertEqual(fake.seen, [])


NET_MODULES = {"urllib.request", "http.client", "socket", "ssl", "requests", "httpx", "urllib3", "aiohttp",
               "http"}
# The modules that may open a connection, each for one job (tohum/01a): ``yaz`` writes the target through
# ``target.write``; ``getir`` reads registry tarballs through ``deps.fetch`` and sends nothing (no request body,
# no method, no header: ``ReadOnlyFetch`` below).
NET_ALLOWED = {os.path.join("target", "write.py"), os.path.join("runner", "deps_npm.py")}


def scan(rel, src):
    found = []
    for node in ast.walk(ast.parse(src)):
        mods = []
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods = [node.module] + [node.module + "." + a.name for a in node.names]
        if rel not in NET_ALLOWED:
            found += ["%s: import %s" % (rel, m) for m in mods if m in NET_MODULES]
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and rel != os.path.join("target", "write.py"):
            if "github.com" in node.value.lower() or node.value in ("push", "send-pack", "receive-pack"):
                found.append("%s: %r" % (rel, node.value))
    return found


def referee_modules():
    for top, dirs, files in os.walk(REFEREE):
        dirs[:] = [d for d in dirs if d not in ("tests", "__pycache__")]
        for name in files:
            if name.endswith(".py"):
                path = os.path.join(top, name)
                with open(path, encoding="utf-8") as fh:
                    yield os.path.relpath(path, REFEREE), fh.read()


class OneWay(unittest.TestCase):
    def test_no_other_module_reaches_the_network_or_pushes(self):
        offenders = []
        for rel, src in referee_modules():
            offenders += scan(rel, src)
        self.assertEqual(offenders, [])

    def test_the_scan_sees_an_offender(self):
        src = "import urllib.request\nfrom http import client\nimport subprocess\n" \
              "subprocess.run(['git', 'push'])\nURL = 'https://API.GitHub.com/repos'\n"
        self.assertEqual(sorted(scan(os.path.join("gate", "x.py"), src)), [
            "gate/x.py: 'https://API.GitHub.com/repos'", "gate/x.py: 'push'", "gate/x.py: import http",
            "gate/x.py: import http.client", "gate/x.py: import urllib.request"])
        self.assertEqual(scan(os.path.join("runner", "deps_npm.py"), "import urllib.request\n"), [])

    def test_read_only_fetch(self):
        """``deps.fetch`` opens a bare URL: no ``Request``, no ``data``/``method``/``headers`` anywhere."""
        src = dict(referee_modules())[os.path.join("runner", "deps_npm.py")]
        bad = []
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Attribute) and node.attr in ("Request", "urlopen", "add_header"):
                bad.append(node.attr)
            if isinstance(node, ast.Call):
                bad += [k.arg for k in node.keywords if k.arg in ("data", "method", "headers")]
        self.assertEqual(bad, [])


def cli(*args, doc=None):
    with tempfile.TemporaryDirectory() as tmp:
        argv = list(args)
        if doc is not None:
            path = os.path.join(tmp, "in.json")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(doc if isinstance(doc, str) else json.dumps(doc))
            argv.append(path)
        proc = subprocess.run([sys.executable, "-m", "target.write", *argv], cwd=REFEREE, capture_output=True,
                              text=True, timeout=60)
    lines = proc.stdout.splitlines()
    return proc.returncode, (json.loads(lines[-1]) if lines else None), proc.stdout, proc.stderr


class CommandLine(unittest.TestCase):
    def test_guard(self):
        plan = {"repo": REPO, "pulls": {"3": OPEN}, "requests": [
            {"method": "POST", "path": P + "git/refs", "body": {"ref": "refs/heads/brain/c/1", "sha": A}},
            {"method": "PUT", "path": P + "pulls/3/merge", "body": {"sha": A, "merge_method": "merge"}}]}
        code, out, stdout, err = cli("guard", doc=plan)
        self.assertEqual((code, out), (0, {"ok": True, "reasons": [], "refs": ["refs/heads/brain/c/1",
                                                                            "refs/heads/brain/integration"]}))
        self.assertEqual(stdout.count("\n"), 1)
        plan["requests"].append({"method": "PATCH", "path": P + "git/refs/heads/main", "body": {"sha": A}})
        plan["requests"].append({"method": "POST", "path": P + "merges", "body": {}})
        code, out, _, _ = cli("guard", doc=plan)
        self.assertEqual((code, out["ok"], out["reasons"]), (1, False, ["2:ref_outside_brain", "3:route_not_allowed"]))
        self.assertEqual(out["refs"], ["refs/heads/brain/c/1", "refs/heads/brain/integration"])

    def test_revert(self):
        state = {"head": B, "merge": B, "commits": {A: {"tree": "1" * 40, "parents": []},
                                                    B: {"tree": "2" * 40, "parents": [A, "c" * 40]}}}
        code, out, _, _ = cli("revert", doc=state)
        self.assertEqual((code, out), (0, {"ok": True, "reasons": [], "commit": {"tree": "1" * 40, "parents": [B]}}))
        code, out, _, _ = cli("revert", doc=dict(state, head=A))
        self.assertEqual((code, out), (1, {"ok": False, "reasons": ["revert_not_head"], "commit": None}))

    def test_unusable(self):
        for args, doc in ((("guard",), "{"), (("guard",), {"repo": REPO}), (("guard",), {"repo": "x", "requests": []}),
                          (("guard",), {"repo": REPO, "requests": [{"method": "GET", "url": "x"}]}),
                          (("guard",), {"repo": REPO, "pulls": {"x": {}}, "requests": []}),
                          (("revert",), {"head": "x", "merge": B, "commits": {}}), (("push",), {}), ((), None)):
            code, out, stdout, err = cli(*args, doc=doc)
            self.assertEqual(code, 2, (args, doc))
            self.assertFalse(out["ok"])
            self.assertIn("unusable", out["error"])
            self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
