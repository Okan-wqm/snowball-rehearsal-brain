"""``drift.check``: the setup facts of a target, read again from the API before a cycle writes (stage 1, MF6).

Rules: asama-0/09 test 24 (a rule that differs from setup, an undeclared App or a workflow on the target is a hard
stop), tohum/01b:57-65 (every cycle runs this before its first write; any difference is a hard stop), tohum/28,
tohum/25a rows 3-6 (what setup made: the rulesets, the writer App's scope, no workflow on the toy, Actions off on
the copy), tohum/29o (the reads and the reasons, which genesis verified once), tohum/26a (``drift.check``: in
``yaz``, at the start of the cycle). Calls: none.

**One source.** The facts are the ones ``activate.genesis`` verifies before the first cycle; their reads and reasons
are here only, and genesis calls ``rules`` and ``actions`` below. So what a later cycle compares the live target with
is what genesis held it to: the baseline is the rule set of tohum/25a as tohum/29o reads it, with the targets of
``setup/summary.json`` (tohum/26c gives the summary no field for a ruleset, an App or a hash; see "Out of scope").

The reads, each once, through a transport (``target.write``'s): ``GET /app``, ``GET /installation/repositories``,
``GET /repos/{repo}/rules/branches/{brain/state, brain/integration, main}``, ``GET /repos/{repo}/rulesets/{id}`` for
each ``ruleset_id`` of those three answers; for a ``toy`` ``GET /repos/{repo}/actions/workflows``; for a ``copy``
``GET /repos/{repo}/actions/permissions``. A read answered other than 200, or a body not of the form read, is
``Unusable``: no verdict.

Reasons (``rules``, then ``actions``):

- ``app_scope``: the set of ``repositories[].full_name`` the writer App is installed on is not the set of
  ``targets[].repo`` (the App on a repository setup did not declare, or missing from a declared one);
- ``state_rules_missing``: ``brain/state`` has no ``deletion`` or no ``non_fast_forward`` rule;
- ``integration_rules_missing``: ``brain/integration`` lacks one of ``deletion``, ``non_fast_forward``,
  ``pull_request``, ``required_status_checks``;
- ``integration_check_not_writer``: a ``required_status_checks`` rule of ``brain/integration`` whose
  ``strict_required_status_checks_policy`` is not ``true``, that lists no check, or one of whose checks has an
  ``integration_id`` other than ``/app``'s ``id`` (a check another App may answer; no such rule: only the reason
  above);
- ``rules_bypassable``: a ruleset a rule of ``brain/state`` or ``brain/integration`` comes from has
  ``current_user_can_bypass`` other than ``never``;
- ``main_writable``: a ruleset a rule of ``main`` comes from is bypassable so, or ``main`` has neither an ``update``
  rule nor a ``pull_request`` rule whose ``required_approving_review_count`` is an integer >= 1;
- ``toy_workflows``: the toy's ``workflows`` list is not empty (any workflow: one triggered on ``brain/**`` with a
  secret is one of them; the triggers are not read);
- ``copy_actions_enabled``: the copy's ``enabled`` is not ``false`` (with Actions off no workflow of the copy runs,
  whatever triggers it).

One more, of the caller, before any read: ``target_repo_mismatch``: the repository the caller writes to (``check``'s
``repo``, when given) is not the summary entry's ``repo``; the facts read would be another repository's.

``check`` answers ``{ok, hard_stop, reasons}``: ``reasons`` sorted, ``hard_stop`` true when there is one. It reads
only; the stop itself is the caller's (``loop.job``'s ``yaz`` runs it for every target it serves before it
serves the first, writes nothing on any target when one has a reason, and ends the job).

Out of scope, stated (reported as seed-080; none of these is read, so none is promised):

- a diff against values recorded at setup: tohum/26c's ``setup/summary.json`` carries no ruleset, no declared App
  or actor list (tohum/25a row 5), no workflow permission and no hash of the seed tree, the constitutional policy or
  the vector file (tohum/01b:59-65, 25:59-64 name them in prose only);
- Apps other than the writer App installed on a target, and the actors of ``brain/*`` ref changes in the activity
  API (tohum/01b:61): no declared list to compare with;
- the referee repository's workflow permission and its Apps (tohum/01b:62): ``yaz`` holds no credential that reads
  them;
- a target that is neither ``toy`` nor ``copy`` (``Unusable``), and so the triggers and secrets of a target's
  workflows (tohum/01b:63): for the two kinds setup knows, no workflow may run at all;
- ``bypass_actors`` and the writer App's own permissions (``GET /app``'s ``permissions`` is not compared).

Command line, run from ``referee/``, one JSON line on stdout, the cause on stderr::

    python -m drift.check check API SUMMARY   stdin {"target": id}
        -> {ok, hard_stop, reasons}
        exit 0 no drift; 1 hard stop; 2 unusable ({"ok": false, "hard_stop": true, "reasons": null})

``API`` is a recorded API (``target.write.Replay``: ``{"GET <path>": body}``), ``SUMMARY`` the summary file.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from ledger import chain, schema
from target import branches, write
import cli

STATE = branches.STATE
INTEGRATION = branches.INTEGRATION
MAIN = "main"
KINDS = ("toy", "copy")
BRANCHES = (STATE, INTEGRATION, MAIN)
STATE_RULES = ("deletion", "non_fast_forward")
INTEGRATION_RULES = ("deletion", "non_fast_forward", "pull_request", "required_status_checks")
USAGE = "usage: python -m drift.check check API SUMMARY"
FAULT_LINE = {"ok": False, "hard_stop": True, "reasons": None}


class Unusable(ValueError):
    pass


def read_json(data: bytes, name: str) -> Any:
    """JSON with no duplicate key and no NaN or Infinity (``ledger.chain``'s reading)."""
    try:
        return cli.loads(data.decode("utf-8"), object_pairs_hook=chain._no_duplicates,
                         parse_constant=chain._no_constant)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise Unusable("%s is not JSON: %s" % (name, cli.cause(exc))) from None


class Reads:
    """The reads through a transport: each a 200 answer, sent once, recorded as ``{"GET <path>": body}``."""

    def __init__(self, transport: Any):
        self.transport = transport
        self.facts: dict[str, Any] = {}

    def get(self, path: str, kind: type) -> Any:
        key = "GET " + path
        if key not in self.facts:
            status, body = self.transport("GET", path, None)
            if status != 200:
                raise Unusable("%s answered %s" % (key, status))
            self.facts[key] = body
        body = self.facts[key]
        if not isinstance(body, kind):
            raise Unusable("%s: the body is not a JSON %s" % (key, "object" if kind is dict else "array"))
        return body


def _rules(body: list, where: str) -> list[dict]:
    for rule in body:
        if not isinstance(rule, dict) or not isinstance(rule.get("type"), str) or \
                type(rule.get("ruleset_id")) is not int:
            raise Unusable("%s: a rule without a type and an integer ruleset_id" % where)
    return body


def _bypassable(reads: Reads, repo: str, rules: list[dict]) -> bool:
    out = False
    for ruleset_id in dict.fromkeys(rule["ruleset_id"] for rule in rules):
        ruleset = reads.get("/repos/%s/rulesets/%d" % (repo, ruleset_id), dict)
        out = out or ruleset.get("current_user_can_bypass") != "never"
    return out


def target(summary: Any, target_id: Any) -> dict:
    """The ``targets[]`` entry of ``target_id`` in a parsed summary; ``Unusable`` unless it is there exactly once,
    a ``toy`` or a ``copy`` with a ``repo`` string (a copy's ``base_sha`` 40 lowercase hex)."""
    if not isinstance(summary, dict) or not isinstance(summary.get("targets"), list):
        raise Unusable("summary.json must carry targets[]")
    found = [t for t in summary["targets"] if isinstance(t, dict) and t.get("id") == target_id]
    if not isinstance(target_id, str) or len(found) != 1:
        raise Unusable("target %r is not exactly once in targets[]" % (target_id,))
    entry = found[0]
    if entry.get("kind") not in KINDS or not isinstance(entry.get("repo"), str):
        raise Unusable("target %r: kind toy or copy and a repo" % target_id)
    # The toy's ``base_sha`` is not read: setup leaves it empty and the base is the API's ``main`` (tohum/29o:45-46).
    if entry["kind"] == "copy" and schema.hex40(entry.get("base_sha"), "base_sha"):
        raise Unusable("target %r: a copy's base_sha must be 40 lowercase hex" % target_id)
    return entry


def rules(reads: Reads, summary: dict, entry: dict) -> set[str]:
    """The reasons of the App's scope and of the three branches' rules (``summary`` and ``entry`` as ``target``
    read them)."""
    repo, reasons = entry["repo"], set()
    app = reads.get("/app", dict)
    installed = reads.get("/installation/repositories", dict).get("repositories")
    if not isinstance(installed, list) or not all(isinstance(r, dict) and isinstance(r.get("full_name"), str)
                                                  for r in installed):
        raise Unusable("GET /installation/repositories: repositories[] of {full_name}")
    found = {b: _rules(reads.get("/repos/%s/rules/branches/%s" % (repo, b), list), b) for b in BRANCHES}
    if {r["full_name"] for r in installed} != {t.get("repo") for t in summary["targets"] if isinstance(t, dict)}:
        reasons.add("app_scope")
    types = {b: {rule["type"] for rule in found[b]} for b in BRANCHES}
    if not set(STATE_RULES) <= types[STATE]:
        reasons.add("state_rules_missing")
    if not set(INTEGRATION_RULES) <= types[INTEGRATION]:
        reasons.add("integration_rules_missing")
    for rule in found[INTEGRATION]:
        if rule["type"] == "required_status_checks":
            params = rule.get("parameters") if isinstance(rule.get("parameters"), dict) else {}
            checks = params.get("required_status_checks")
            if params.get("strict_required_status_checks_policy") is not True or not isinstance(checks, list) \
                    or not checks or any(not isinstance(c, dict) or c.get("integration_id") != app.get("id")
                                         for c in checks):
                reasons.add("integration_check_not_writer")
    if _bypassable(reads, repo, found[STATE] + found[INTEGRATION]):
        reasons.add("rules_bypassable")
    reviewed = any(rule["type"] == "pull_request" and isinstance(rule.get("parameters"), dict)
                   and type(rule["parameters"].get("required_approving_review_count")) is int
                   and rule["parameters"]["required_approving_review_count"] >= 1 for rule in found[MAIN])
    if _bypassable(reads, repo, found[MAIN]) or not ("update" in types[MAIN] or reviewed):
        reasons.add("main_writable")
    return reasons


def actions(reads: Reads, entry: dict) -> set[str]:
    """The reasons of the target's Actions: a toy with a workflow, a copy whose Actions are not off."""
    repo = entry["repo"]
    if entry["kind"] == "toy":
        workflows = reads.get("/repos/%s/actions/workflows" % repo, dict).get("workflows")
        if not isinstance(workflows, list):
            raise Unusable("GET actions/workflows: workflows[] missing")
        return {"toy_workflows"} if workflows else set()
    if reads.get("/repos/%s/actions/permissions" % repo, dict).get("enabled") is not False:
        return {"copy_actions_enabled"}
    return set()


def check(transport: Any, summary: bytes, target_id: Any, repo: Any = None) -> dict:
    """``{ok, hard_stop, reasons}`` (see the module docstring); reads only, writes nothing. ``repo``, when given,
    is the repository the caller is about to write to."""
    doc = read_json(summary, "summary.json")
    entry = target(doc, target_id)
    if repo is not None and repo != entry["repo"]:
        return {"ok": False, "hard_stop": True, "reasons": ["target_repo_mismatch"]}
    reads = Reads(transport)
    reasons = sorted(rules(reads, doc, entry) | actions(reads, entry))
    return {"ok": not reasons, "hard_stop": bool(reasons), "reasons": reasons}


def _read(path: str) -> bytes:
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError as exc:
        raise Unusable("cannot read %s: %s" % (path, cli.cause(exc))) from None


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 3 or argv[0] != "check":
            raise Unusable(USAGE)
        api = write.Replay(read_json(_read(argv[1]), "the recorded API"))
        summary = _read(argv[2])
        request = read_json(sys.stdin.buffer.read(), "stdin")
        if not isinstance(request, dict) or set(request) != {"target"}:
            raise Unusable('stdin must be {"target"} and nothing else')
        out = check(api, summary, request["target"])
        sys.stdout.write(json.dumps(out, sort_keys=True) + "\n")
        return 1 if out["hard_stop"] else 0
    except (Unusable, write.Unusable) as exc:
        cause = "unusable input: %s" % cli.cause(exc)
    sys.stdout.write(json.dumps(FAULT_LINE, sort_keys=True) + "\n")
    sys.stderr.write(cause + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
