"""``drift.check``: the setup facts of a target, read again from the API before a cycle writes (stage 1, MF6).

Rules: asama-0/09 test 24 (a rule that differs from setup, an undeclared App or a workflow on the target is a hard
stop), tohum/01b:57-65 (every cycle runs this before its first write; any difference is a hard stop), tohum/28,
tohum/25a rows 3-6 (what setup made: the rulesets, the writer App's scope, no workflow on the toy, Actions off on
the copy), tohum/29o (the reads and the reasons, which genesis verified once), tohum/26a (``drift.check``: in
``yaz``, at the start of the cycle). Calls: none.

**One source.** The facts are the ones ``activate.genesis`` verifies before the first cycle; their reads and reasons
are here only, and genesis calls ``rules`` and ``actions`` below. So what a later cycle compares the live target with
is what genesis held it to, and, since tohum/01c, the baseline setup recorded: the top-level ``drift`` object of
``setup/summary.json`` (see "The baseline").

The reads, each once, through a transport (``target.write``'s): ``GET /app``, ``GET /installation/repositories``,
``GET /repos/{repo}/rules/branches/{brain/state, brain/integration, main}``, ``GET /repos/{repo}/rulesets/{id}`` for
each ``ruleset_id`` of those three answers; for a ``toy`` ``GET /repos/{repo}/actions/workflows``; for a ``copy``
``GET /repos/{repo}/actions/permissions``; then, for the baseline, ``GET /repos/{repo}/rulesets?per_page=100`` (and
``&page=2`` and on, while a page holds 100 items), ``GET /repos/{r}`` for each repository ``r`` the baseline's
``visibility`` names, in the names' order, and ``GET /repos/{repo}/rules/branches/{branch}`` for each branch the
baseline names that is not one of those three. A read answered other than 200, or a body not of the form read, is
``Unusable``: no verdict. Genesis sends only the reads of ``rules`` and ``actions``: those before the baseline's.

**The baseline** (tohum/01c). A summary without a top-level ``drift`` object is ``Unusable`` (the reasons below are
never a fallback for it), and so is one whose ``drift`` is not exactly of 01c's form: ``writer_app_id`` an integer;
``writer_app_permissions`` an object; ``targets`` ``{id: {rulesets: [integer], rules: {branch: 64 lowercase hex}}}``
with an entry for the target checked, ``rulesets`` ascending without a repeat, every ``rules`` key a branch name
and ``brain/state``, ``brain/integration`` and ``main`` among them; ``activity`` ``{operator_logins: [string],
not_before}``; ``hashes`` ``{constitutional_sha256, vectors_sha256, seats_sha256}``, each 64 lowercase hex;
``visibility`` ``{repo: "public"|"private"}``, every key a repository name (``loop.accepted.repo_name``) and the
``repo`` of every ``targets[]`` entry of the summary among them; ``operator_checked_at``; no other key at any of
these levels; the two times ``YYYY-MM-DDTHH:MM:SSZ`` of a real date (the one form 01c reads). A ``targets[]`` entry
that carries a ``drift`` key is ``Unusable`` too (01c: never inside ``targets[]``), and so is an
``operator_checked_at`` after ``now``. Compared with it, after the reasons of today:

- ``writer_app_changed``: ``GET /app``'s ``id`` is not the integer ``drift.writer_app_id``;
- ``writer_app_permissions_changed``: ``GET /app``'s ``permissions`` (absent: null) is not equal, as JSON, to
  ``drift.writer_app_permissions`` (the keys' order is no difference; ``true`` is not ``1``);
- ``rulesets_changed``: the set of ``id`` over every page of the target's ruleset list is not the set
  ``drift.targets.<id>.rulesets`` (an item without an integer ``id`` is ``Unusable``; ``includes_parents`` is not
  sent: the API's default, as 01c reads it);
- ``visibility_changed:<repo>``: ``GET /repos/<repo>``'s ``visibility`` is not the recorded string, for each
  repository ``drift.visibility`` names, the targets' and any other (``internal``, or no such field, differs from
  both recorded values);
- ``constitutional_hash_mismatch``, ``vectors_hash_mismatch``, ``seats_hash_mismatch``: the caller's hash of that
  name (``check``'s ``hashes``, see "The hashes") is not ``drift.hashes``' one;
- ``rules_changed:<branch>``: for each key of ``drift.targets.<id>.rules``, the hash of that branch's rules as read
  now is not the recorded one. The hash is 01c's: each item of the answer reduced to ``{type, parameters}``
  (``parameters`` absent: ``{}``), the items ordered by the bytes of their RFC 8785 form (``ledger.chain.canonical``),
  sha256 of the RFC 8785 form of that array, lowercase hex. A rule content the canonical form cannot hold (a float)
  is ``Unusable``.

**The hashes** (tohum/01c "Hash tarifleri", "Okumalar ve nedenler"). ``held(root)`` gives the three of a checkout
of the referee repository, the folder ``root``: ``constitutional_sha256`` is sha256 of the RFC 8785 form of the
``constitutional`` object of ``root/policy.json`` (``Unusable`` when the file is absent, not JSON or holds no such
object, and ``policy_invalid:<dotted path>`` when a value there has no canonical form: a JSON float);
``vectors_sha256`` and ``seats_sha256`` are the tree hash of ``root/vectors`` and ``root/seats``: one line per
regular file at any depth, ``<sha256 of its bytes>  <path relative to the folder, "/" between names>`` and LF
(``loop.treehash.line``, the one place the line is written), the lines sorted by their bytes, joined, sha256
(``loop.treehash.joined``). A link or anything that is neither a regular file nor a folder, at any depth, a name
that is not UTF-8, and a folder that is absent, a link or no folder are ``Unusable``; a folder holding no file has
the hash of no line. ``check`` does not read the checkout: its caller passes the three (``loop.job`` computes
them once per job from ``$GITHUB_WORKSPACE``, the command below from ``ROOT``), and ``hashes`` not of that form
are ``Unusable``.

**The operator's check** (tohum/01c): ``stale`` is true when ``drift.operator_checked_at`` is more than 7 days
(604800 s) before ``now``, the caller's clock (exactly 7 days is not stale). It is no reason and no hard stop: the
caller ends cleanly ("operator check stale"). The reads are made all the same, so a hard stop is not hidden by it.

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

``check`` answers ``{ok, hard_stop, reasons, stale}``: ``reasons`` sorted, ``hard_stop`` true when there is one,
``ok`` true when there is none and the operator's check is not stale. It reads only; the stop itself is the caller's
(``loop.job``'s ``yaz`` runs it for every target it serves before it serves the first, writes nothing on any target
when one has a reason or the check is stale, and ends the job).

Out of scope, stated (none of these is read, so none is promised):

- the baseline's ``activity``, validated in form and compared with nothing: tohum/01c's "Etkinlik API'si" (the
  activity read, its window and actors, Gözcü's ``hard_stop`` row for it) is not built;
- a clean stop that is "not a red job" with a warning the operator sees (01c): ``stale`` is answered here, and
  ``loop.job`` still ends such a job with exit 1;
- the policy a cycle was pulled with (``pulled``'s copy): the hash is of the checkout's ``policy.json`` only, and a
  float elsewhere in that file than under ``constitutional`` is not looked for here (the readers of those paths
  refuse it, ``harness.params``);
- that the checkout is the one setup hashed: file modes, and names git would not check out, are not in the hash;
- a branch the baseline's ``rules`` names beyond the three is compared, one it does not name is not;
- whatever the operator's check covers: other Apps installed on a target, the referee repository's workflow
  permission, ``bypass_actors`` (tohum/01c: the operator's, recorded only as that time);
- a ruleset list of a parent organization's rulesets beyond what the API's default lists, and a repository of
  ``visibility`` the writer's token cannot read (``Unusable``: no verdict);
- a target that is neither ``toy`` nor ``copy`` (``Unusable``, tohum/01c), and so the triggers and secrets of a
  target's workflows: for the two kinds setup knows, no workflow may run at all.

Command line, run from ``referee/``, one JSON line on stdout, the cause on stderr::

    python -m drift.check check API ROOT   stdin {"target": id, "now": "YYYY-MM-DDTHH:MM:SSZ"}
        -> {ok, hard_stop, reasons, stale}
        exit 0 no drift; 1 a hard stop or a stale operator check (the line says which);
        2 unusable ({"ok": false, "hard_stop": true, "reasons": null, "stale": null})

``API`` is a recorded API (``target.write.Replay``: ``{"GET <path>": body}``), ``ROOT`` a checkout of the referee
repository: the folder holding ``setup/summary.json``, ``policy.json``, ``vectors/`` and ``seats/``.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
from typing import Any

from ledger import chain, schema
from loop import accepted, treehash
from policy import reads as paths
from target import branches, write
import cli

STATE = branches.STATE
INTEGRATION = branches.INTEGRATION
MAIN = "main"
KINDS = ("toy", "copy")
BRANCHES = (STATE, INTEGRATION, MAIN)
STATE_RULES = ("deletion", "non_fast_forward")
INTEGRATION_RULES = ("deletion", "non_fast_forward", "pull_request", "required_status_checks")
USAGE = "usage: python -m drift.check check API ROOT"
SUMMARY = "setup/summary.json"
POLICY = "policy.json"
TREES = {"vectors_sha256": "vectors", "seats_sha256": "seats"}  # tohum/01c: operator folders at the checkout's root
HASH_REASONS = {"constitutional_sha256": "constitutional_hash_mismatch", "vectors_sha256": "vectors_hash_mismatch",
                "seats_sha256": "seats_hash_mismatch"}
PAGE = 100  # tohum/01c: the ruleset list is read with per_page=100, every page
FAULT_LINE = {"ok": False, "hard_stop": True, "reasons": None, "stale": None}
STALE_AFTER = datetime.timedelta(days=7)  # tohum/01c: an operator check older than this ends the cycle cleanly


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


def _integer(value: Any, where: str) -> list[str]:
    return [] if type(value) is int else ["%s: not an integer" % where]


def _instant(value: Any, where: str) -> list[str]:
    try:
        return schema.timestamp(value, where) or (moment(value) and [])
    except ValueError:
        return ["%s: not a date" % where]


def _branch_hashes(value: Any, where: str) -> list[str]:
    out = schema.map_of(schema.hex64)(value, where)
    out = out or ["%s: key %r is not a branch name" % (where, b) for b in value if not write.branch_syntax(b)]
    return out or ["%s: %s is not named" % (where, b) for b in BRANCHES if b not in value]


def _repos(value: Any, where: str) -> list[str]:
    out = schema.map_of(schema.one_of("public", "private"))(value, where)
    return out or ["%s: key %r is not a repository name" % (where, r) for r in value if not _repo_name(r)]


def _repo_name(repo: Any) -> bool:
    try:
        return bool(accepted.repo_name(repo))
    except accepted.StateError:
        return False


BASELINE = schema.shape({
    "writer_app_id": _integer,
    "writer_app_permissions": schema.any_object,
    "targets": schema.map_of(schema.shape({"rulesets": schema.list_of(_integer, unique_sorted=True),
                                           "rules": _branch_hashes})),
    "activity": schema.shape({"operator_logins": schema.list_of(schema.text), "not_before": _instant}),
    "hashes": schema.shape({"constitutional_sha256": schema.hex64, "vectors_sha256": schema.hex64,
                            "seats_sha256": schema.hex64}),
    "visibility": _repos,
    "operator_checked_at": _instant})


def moment(ts: str) -> datetime.datetime:
    """The instant of a ``YYYY-MM-DDTHH:MM:SSZ``; ``ValueError`` when it is no date."""
    return datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


def baseline(summary: dict, target_id: str) -> dict:
    """The summary's ``drift`` object (tohum/01c); ``Unusable`` unless it is there, at the top level only, of the
    form, with an entry for ``target_id`` and with the ``repo`` of every ``targets[]`` entry in ``visibility``."""
    if "drift" not in summary:
        raise Unusable("summary.json carries no drift baseline")
    if any(isinstance(t, dict) and "drift" in t for t in summary["targets"]):
        raise Unusable("summary.json: drift inside targets[]")
    faults = BASELINE(summary["drift"], "drift")
    if faults:
        raise Unusable("summary.json: %s" % "; ".join(faults))
    if target_id not in summary["drift"]["targets"]:
        raise Unusable("summary.json: drift.targets has no %r" % target_id)
    for entry in summary["targets"]:
        repo = entry.get("repo") if isinstance(entry, dict) else None
        if not isinstance(repo, str) or repo not in summary["drift"]["visibility"]:
            raise Unusable("summary.json: drift.visibility does not name the repo of every target")
    return summary["drift"]


def _unhashable(value: Any, path: str) -> str | None:
    """The dotted path of the first value under ``value`` that the canonical form refuses, in key order."""
    children = sorted(value.items()) if isinstance(value, dict) else \
        enumerate(value) if isinstance(value, list) else None
    if children is not None:
        for key, child in children:
            found = _unhashable(child, "%s.%s" % (path, key))
            if found:
                return found
        return None
    try:
        chain.canonical(value)
    except chain.ChainError:
        return path
    return None


def constitutional_hash(policy: bytes) -> str:
    """tohum/01c's ``constitutional_sha256`` of a ``policy.json``'s bytes: sha256 of the RFC 8785 form of its
    ``constitutional`` object. ``Unusable`` for bytes that are not JSON or hold no such object, and, naming the
    path as ``policy_invalid:<path>``, for a value there the canonical form refuses (a JSON float, 01c
    "Politikanın sayıları")."""
    doc = read_json(policy, POLICY)
    section = doc.get(paths.CONSTITUTIONAL) if isinstance(doc, dict) else None
    if not isinstance(section, dict):
        raise Unusable("%s carries no %s object" % (POLICY, paths.CONSTITUTIONAL))
    try:
        return hashlib.sha256(chain.canonical(section)).hexdigest()
    except chain.ChainError as exc:
        raise Unusable("policy_invalid:%s (%s)" % (_unhashable(section, paths.CONSTITUTIONAL) or paths.CONSTITUTIONAL,
                                                    cli.cause(exc))) from None


def _lines(root: str) -> list[bytes]:
    """``loop.treehash``'s line of every regular file under the folder ``root`` (no call of itself: a folder's
    depth is the checkout's, not a bound of this code)."""
    out: list[bytes] = []
    folders = [""]
    while folders:
        rel = folders.pop()
        try:
            entries = list(os.scandir(os.path.join(root, *rel.split("/")) if rel else root))
        except OSError as exc:
            raise Unusable("cannot list %s: %s" % (rel or ".", cli.cause(exc))) from None
        for entry in entries:
            path = "%s/%s" % (rel, entry.name) if rel else entry.name
            if entry.is_dir(follow_symlinks=False):
                folders.append(path)
            elif entry.is_file(follow_symlinks=False):
                try:
                    name = path.encode("utf-8")
                except UnicodeEncodeError:
                    raise Unusable("a path that is not UTF-8 under the folder") from None
                out.append(treehash.line(name, _read(entry.path)))
            else:
                raise Unusable("%s is a link or no regular file" % path.encode("utf-8", "backslashreplace").decode())
    return out


def folder_hash(root: str) -> str:
    """tohum/01c's tree hash of a checkout's folder: ``loop.treehash``'s lines (content sha256, two spaces, the
    path relative to ``root`` with ``/``, LF) of every regular file under it, sorted, joined, sha256. ``Unusable``
    when ``root`` is not a directory itself (absent, a link, a file), holds a link or an entry that is neither a
    regular file nor a directory at any depth, a name that is not UTF-8, or cannot be read. A folder without a
    file has the hash of no line."""
    if os.path.islink(root) or not os.path.isdir(root):
        raise Unusable("%s is not a directory of the checkout" % os.path.basename(root))
    return treehash.joined(_lines(root))


def held(root: str) -> dict[str, str]:
    """The three hashes of 01c's ``drift.hashes`` as the checkout ``root`` of the referee repository holds them
    now: ``constitutional_hash`` of ``policy.json`` and ``folder_hash`` of ``vectors/`` and ``seats/``."""
    out = {"constitutional_sha256": constitutional_hash(_read(os.path.join(root, POLICY)))}
    for key, folder in TREES.items():
        out[key] = folder_hash(os.path.join(root, folder))
    return out


def rulesets(reads: Reads, repo: str) -> set[int]:
    """The ids of the repository's ruleset list: ``GET /repos/{repo}/rulesets?per_page=100``, then ``&page=2``
    and on while a page is full; ``Unusable`` for an item without an integer ``id``."""
    ids: set[int] = set()
    page = 1
    while True:
        path = "/repos/%s/rulesets?per_page=%d" % (repo, PAGE) + ("&page=%d" % page if page > 1 else "")
        body = reads.get(path, list)
        if not all(isinstance(item, dict) and type(item.get("id")) is int for item in body):
            raise Unusable("GET %s: an item without an integer id" % path)
        ids.update(item["id"] for item in body)
        if len(body) < PAGE:
            return ids
        page += 1


def _same(a: Any, b: Any) -> bool:
    """Equal as JSON: a boolean is no number and 1 is not 1.0."""
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def rules_hash(body: list[dict]) -> str:
    """tohum/01c's hash of a branch's effective rules (``_rules`` read them)."""
    try:
        items = [{"type": rule["type"], "parameters": rule.get("parameters", {})} for rule in body]
        return hashlib.sha256(chain.canonical(sorted(items, key=chain.canonical))).hexdigest()
    except chain.ChainError as exc:
        raise Unusable("a rule's content has no canonical form: %s" % cli.cause(exc)) from None


def recorded(reads: Reads, drift: dict, entry: dict, hashes: dict[str, str]) -> set[str]:
    """The reasons against the baseline (``drift`` as ``baseline`` read it; ``hashes`` as ``held`` gives them): the
    writer App's id and permissions, the three hashes, the target's ruleset list and the hash of each branch
    ``drift`` names for it, and the visibility of every repository ``drift`` names."""
    reasons = {reason for key, reason in HASH_REASONS.items() if hashes[key] != drift["hashes"][key]}
    app = reads.get("/app", dict)
    if type(app.get("id")) is not int or app["id"] != drift["writer_app_id"]:
        reasons.add("writer_app_changed")
    if not _same(app.get("permissions"), drift["writer_app_permissions"]):
        reasons.add("writer_app_permissions_changed")
    if rulesets(reads, entry["repo"]) != set(drift["targets"][entry["id"]]["rulesets"]):
        reasons.add("rulesets_changed")
    for repo, visibility in sorted(drift["visibility"].items()):
        if reads.get("/repos/%s" % repo, dict).get("visibility") != visibility:
            reasons.add("visibility_changed:%s" % repo)
    for branch, digest in sorted(drift["targets"][entry["id"]]["rules"].items()):
        found = _rules(reads.get("/repos/%s/rules/branches/%s" % (entry["repo"], branch), list), branch)
        if rules_hash(found) != digest:
            reasons.add("rules_changed:%s" % branch)
    return reasons


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


def check(transport: Any, summary: bytes, hashes: Any, target_id: Any, now: Any, repo: Any = None) -> dict:
    """``{ok, hard_stop, reasons, stale}`` (see the module docstring); reads only, writes nothing. ``hashes`` are
    the three of the caller's checkout (``held``); ``now`` is the caller's clock, ``YYYY-MM-DDTHH:MM:SSZ``;
    ``repo``, when given, is the repository the caller is about to write to."""
    doc = read_json(summary, "summary.json")
    entry = target(doc, target_id)
    drift = baseline(doc, target_id)
    if schema.shape(dict.fromkeys(HASH_REASONS, schema.hex64))(hashes, "hashes"):
        raise Unusable("hashes must be the three of the checkout, each 64 lowercase hex")
    if _instant(now, "now"):
        raise Unusable("now must be YYYY-MM-DDTHH:MM:SSZ")
    if moment(drift["operator_checked_at"]) > moment(now):
        raise Unusable("summary.json: drift.operator_checked_at is after now")
    stale = moment(now) - moment(drift["operator_checked_at"]) > STALE_AFTER
    if repo is not None and repo != entry["repo"]:
        return {"ok": False, "hard_stop": True, "reasons": ["target_repo_mismatch"], "stale": stale}
    reads = Reads(transport)
    reasons = sorted(rules(reads, doc, entry) | actions(reads, entry) | recorded(reads, drift, entry, hashes))
    return {"ok": not reasons and not stale, "hard_stop": bool(reasons), "reasons": reasons, "stale": stale}


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
        summary = _read(os.path.join(argv[2], *SUMMARY.split("/")))
        hashes = held(argv[2])
        request = read_json(sys.stdin.buffer.read(), "stdin")
        if not isinstance(request, dict) or set(request) != {"target", "now"}:
            raise Unusable('stdin must be {"target", "now"} and nothing else')
        out = check(api, summary, hashes, request["target"], request["now"])
        sys.stdout.write(json.dumps(out, sort_keys=True) + "\n")
        return 0 if out["ok"] else 1
    except (Unusable, write.Unusable) as exc:
        cause = "unusable input: %s" % cli.cause(exc)
    sys.stdout.write(json.dumps(FAULT_LINE, sort_keys=True) + "\n")
    sys.stderr.write(cause + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
