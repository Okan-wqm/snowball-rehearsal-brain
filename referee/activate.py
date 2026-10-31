"""``activate``: the operator's first cycle on a target: the genesis row, the ``brain/integration`` cut, the ratchet
base and the ready candidates, written as one orphan ``brain/state`` commit (stage 0, MF18).

Rules: tohum/29o (``genesis``: the reads, the reasons, the twelve-key payload, the exits), asama-0/14 row 18,
asama-0/09 tests 45 and 14, asama-0/10a #genesis (genesis reads and hashes the facts from the API) and #taban (the
ratchet base is the referee's own tool run at genesis), asama-0/08 (the acceptance rule), tohum/25a rows 3-7 (the
rulesets, the writer App's scope, no workflow on the toy, Actions off on the copy; ``brain/state`` opened with the
genesis row; ``brain/integration`` cut from the toy's ``main`` or at the copy's ``targets[].base_sha``),
tohum/01b:59-60 (``rules/branches`` and ``current_user_can_bypass``), tohum/28:37 (each reason is a hard stop),
tohum/30e (the seed security ledger), tohum/26a (``activate``). Calls: 2, 7 and 8 (the decision), 9 (every write),
10, 11 and 16 (the state commit), through their modules.

**Genesis** (``genesis``), a dry run: it reads through a transport (``target.write``'s; the vector's is
``target.write.Replay`` over a recorded API) and writes nothing. Inputs: ``setup/summary.json``, the
``setup/imports.jsonl`` rows, the referee policy, ``seed/security-ledger.jsonl`` and the verified recipe, as bytes,
and the target id.

The reads, exactly these, each once (``reads``): ``GET /app``, ``GET /installation/repositories``, ``GET
/repos/{repo}/rules/branches/{brain/state, brain/integration, main}``, then ``GET /repos/{repo}/rulesets/{id}`` for
each ``ruleset_id`` of those three answers (in first-seen order); for a ``toy`` ``GET
/repos/{repo}/git/ref/heads/main`` and ``GET /repos/{repo}/actions/workflows``; for a ``copy`` ``GET
/repos/{repo}/actions/permissions``. A read answered other than 200, or a body not of the form read, is unusable:
the list is a ceiling, nothing else is read.

Reasons, sorted; any reason is a hard stop and no payload:

- ``app_scope``: the set of ``repositories[].full_name`` is not the set of ``targets[].repo``;
- ``state_rules_missing``: ``brain/state`` has no ``deletion`` or no ``non_fast_forward`` rule;
- ``integration_rules_missing``: ``brain/integration`` lacks one of ``deletion``, ``non_fast_forward``,
  ``pull_request``, ``required_status_checks``;
- ``integration_check_not_writer``: a ``required_status_checks`` rule of ``brain/integration`` whose
  ``strict_required_status_checks_policy`` is not ``true``, that lists no check, or one of whose checks has an
  ``integration_id`` other than ``/app``'s ``id`` (no such rule: only the reason above);
- ``rules_bypassable``: a ruleset a rule of ``brain/state`` or ``brain/integration`` comes from has
  ``current_user_can_bypass`` other than ``never`` (``exempt`` and ``pull_requests_only`` included);
- ``main_writable``: a ruleset a rule of ``main`` comes from is bypassable so, or ``main`` has neither an
  ``update`` rule nor a ``pull_request`` rule whose ``required_approving_review_count`` is an integer >= 1;
- ``toy_workflows``: the toy's ``workflows`` list is not empty;
- ``copy_actions_enabled``: the copy's ``enabled`` is not ``false``;
- ``security_ledger_broken``: the seed security ledger is empty or not a valid chain (``ledger.chain``).

The payload, twelve keys: ``target`` (the id); ``base_sha`` (``toy``: ``object.sha`` of the API's ``main``, the
summary's not read; ``copy``: ``targets[].base_sha``); of the last ``imports.jsonl`` row carrying
``referee_tree_sha256`` (a counter row that is no transfer is skipped): ``referee_tree_sha256``, ``result_sha256``
and ``import_line_sha256`` (that line's bytes without its LF); ``seed_epoch`` (the last ``seed_epochs[]`` entry as
written); ``policy_sha256``, ``summary_sha256``, ``seed_security_ledger_sha256`` (sha256 of each file's bytes as
given); ``seed_security_last_row_hash``; ``recipe_sha256`` (of the recipe's RFC 8785 form); ``facts_sha256`` (of
the RFC 8785 form of ``{"GET <path>": body}`` over the reads). Unusable (``Unusable``): the target not exactly once
in ``targets[]`` or of another kind, a file that is not the JSON it names (``imports.jsonl`` a valid chain of
objects), no transfer row, a read not answered or malformed (a rule without an integer ``ruleset_id`` included).

**Activation** (``activate``), in this order; nothing is written before step 4:

1. ``genesis`` through the writer's transport; a reason is ``Refused`` (a hard stop: nothing is written); the
   writer's repository must be the target's (``target_repo_mismatch``).
2. The ratchet base (asama-0/10a #taban): ``base.jsonl`` (the referee's lint tool run three times on the base tree
   in ``koş``) must hash to the request's ``base_run_sha256`` (``base_run_hash_mismatch``) and its three records be
   one (``tool_nondeterministic``); ``counts`` is violations per tool in its first record (``gate.check``'s count).
3. Reads: ``brain/state`` must not exist (``already_activated``), ``brain/integration`` must not exist
   (``integration_exists``), the ``base_sha`` commit must read. Any reason: ``Refused``.
4. Cut: ``brain/integration`` created at ``base_sha``. If GitHub refuses the creation, nothing else is written.
5. Each ready candidate, in id order, is decided by the acceptance rule (asama-0/08): ``gate.diffguard.check``
   (criterion 1, with the profile's ``security_paths``/``excluded_dirs`` and the recipe's ``inputs``), then
   ``gate.check.decide`` (criteria 2-8 against ``base.jsonl``, with ``unfinished_sentinels`` the merges this
   activation already made: at most one merge), then the diff applied to the base file (``read_base``; a missing
   file ``base_file_missing``, a diff that does not apply ``patch_does_not_apply``); unusable files
   ``candidate_unusable``; an id that is not a branch name under ``brain/c/`` ``candidate_id_invalid``. A merge:
   branch ``brain/c/<cid>`` at the cut, one commit, a pull request into ``brain/integration``, a ``success`` check
   named ``check_name``, the merge. A reject writes nothing on the target.
6. The state, ``events`` rows in this order: ``genesis`` (the payload), ``cycle_start {cycle_id}``,
   ``integration_cut {branch, base_sha}``, ``ratchet_base {base_run_sha256, counts}``, one ``decision`` per
   candidate (``{decision: merge, candidate, path, pull, head_sha, merge_sha}`` or ``{decision: reject, candidate,
   reasons}`` with ``cause`` the first of ``REJECT_CAUSES`` that matches a reason, else ``unknown``), then
   ``status.block.plan``'s rows (MF16); every row's payload is checked by ``ledger.schema``, the chained ledger
   again; ``ledger.append.plan_cycle`` chains them (secret scan); the root is signed (``ledger.anchor``) and its
   row written; ``ledger.jsonl``, ``chain/root.jsonl`` and ``status.md`` go in one orphan commit that opens
   ``brain/state``.

A failure after step 4 raises ``HardStop`` carrying the refs already written (tohum/25a's failure rule leaves them
to the operator; step 3 refuses a retry).

Out of scope, stated: running the tools and tests (``koş``: their outputs are inputs here); (A)'s Rekor ids, the App
declaration of tohum/25a row 5 and ``bypass_actors`` (genesis does not read them, tohum/29o); writing
``profile.json`` into ``brain/state``; the wiring into ``loop.yml``'s ``yaz`` job (spec-036). Whether GitHub lets
the writer App create ``brain/integration`` under tohum/25a row 3's ``pull_request`` rule is not known here
(seed-037); the fake GitHub is tested both ways.

Command line (group ``genesis``), run from ``referee/``, one JSON line on stdout, the cause on stderr::

    python -m activate genesis API SUMMARY IMPORTS POLICY SECURITY RECIPE   stdin {"target": id}
        -> {ok, hard_stop, reasons, payload}
        exit 0 planned; 1 hard stop; 2 unusable ({"ok": false, "hard_stop": true, "payload": null})
"""

from __future__ import annotations

import hashlib
import json
import sys
from typing import Any, Callable

from gate import check, diffguard
from ledger import anchor, append, chain, schema
from status import block
from target import write
import cli

STATE = "brain/state"
INTEGRATION = schema.INTEGRATION
MAIN = "main"
CANDIDATE_PREFIX = "brain/c/"
FILES = ("summary.json", "imports.jsonl", "policy.json", "security-ledger.jsonl", "recipe.json", "profile.json",
         "base.jsonl")
GENESIS_FILES = FILES[:5]
REQUEST = {"target_id", "base_run_sha256", "cycle_id", "ts", "snapshot_id", "candidates"}
KINDS = ("toy", "copy")
BRANCHES = (STATE, INTEGRATION, MAIN)
INTEGRATION_RULES = ("deletion", "non_fast_forward", "pull_request", "required_status_checks")
CANDIDATE_FILES = ("finding.json", "diff.patch", "cand.jsonl", "checks.json", "hashes.json")
# A reject's cause: the first entry whose test holds for some reason (tohum/26 closed set).
REJECT_CAUSES = (
    ("scope_violation", lambda r: r == "scope_violation" or ":" in r),  # criterion 1's path reasons and 4
    ("test_regression", lambda r: r in ("tests_red", "zero_tests")),
    ("lint_regression", lambda r: r == "ratchet_increase"),
)

HardStopBase = append.HardStop
Refused = write.Refused


class Unusable(ValueError):
    pass


class HardStop(HardStopBase):
    """Activation failed after its first write; ``written`` names the refs already written."""

    def __init__(self, message: str, written: list[str]):
        super().__init__("%s (written: %s)" % (message, ", ".join(written) or "nothing"))
        self.written = written


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(data: bytes, name: str) -> Any:
    """JSON with no duplicate key and no NaN or Infinity (``ledger.chain``'s reading)."""
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=chain._no_duplicates,
                          parse_constant=chain._no_constant)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise Unusable("%s is not JSON: %s" % (name, exc)) from None


def _chain_rows(data: bytes) -> list[dict] | None:
    """The rows of a valid, non-empty chain, else None."""
    if not chain.verify_bytes(data)["valid"]:
        return None
    rows = [chain.parse_row(line.decode("utf-8")) for line in chain._lines(data)]
    return rows or None


def _request(req: Any) -> dict:
    if not isinstance(req, dict) or set(req) != REQUEST:
        raise Unusable("the request must have exactly the keys %s" % ", ".join(sorted(REQUEST)))
    for key in ("target_id", "cycle_id", "snapshot_id"):
        if schema.text(req[key], key):
            raise Unusable("%s must be a non-empty string" % key)
    if schema.timestamp(req["ts"], "ts") or schema.hex64(req["base_run_sha256"], "base_run_sha256"):
        raise Unusable("ts must be YYYY-MM-DDTHH:MM:SSZ and base_run_sha256 64 lowercase hex")
    if schema.list_of(schema.text)(req["candidates"], "candidates"):
        raise Unusable("candidates must be a list of non-empty strings")
    return req


def _canonical_sha(value: Any, name: str) -> str:
    try:
        return _sha(chain.canonical(value))
    except (chain.ChainError, ValueError, TypeError) as exc:
        raise Unusable("%s has no canonical form: %s" % (name, exc)) from None


def _row(cycle: dict, suffix: str, kind: str, payload: dict, cause: str | None = None) -> dict:
    row = {"row_id": "%s:%s" % (cycle["cycle_id"], suffix), "ts": cycle["ts"], "part": "events", "kind": kind,
           "payload": payload, "derivation": "tool", "trust": "verified", "snapshot_id": cycle["snapshot_id"],
           "evidence_refs": []}
    if cause is not None:
        row["cause"] = cause
    reasons = schema.payload_reasons("events", kind, payload)
    if reasons:
        raise Unusable("%s row: %s" % (kind, "; ".join(reasons)))
    return row


# ---------------------------------------------------------------- genesis

class Reads:
    """The genesis reads through a transport: each a 200 answer, recorded as ``{"GET <path>": body}``."""

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


def _target(summary: Any, target_id: Any) -> dict:
    if not isinstance(summary, dict) or not isinstance(summary.get("targets"), list) \
            or not isinstance(summary.get("seed_epochs"), list) or not summary["seed_epochs"]:
        raise Unusable("summary.json must carry targets[] and a non-empty seed_epochs[]")
    found = [t for t in summary["targets"] if isinstance(t, dict) and t.get("id") == target_id]
    if not isinstance(target_id, str) or len(found) != 1:
        raise Unusable("target %r is not exactly once in targets[]" % (target_id,))
    target = found[0]
    if target.get("kind") not in KINDS or not isinstance(target.get("repo"), str) or schema.hex40(
            target.get("base_sha"), "base_sha"):
        raise Unusable("target %r: kind toy or copy, a repo and a 40-hex base_sha" % target_id)
    return target


def genesis(transport: Any, files: dict[str, bytes], target_id: Any) -> dict:
    """``{ok, hard_stop, reasons, payload}`` (see the module docstring); reads only, writes nothing."""
    missing = [name for name in GENESIS_FILES if not isinstance(files.get(name), bytes)]
    if missing:
        raise Unusable("missing file(s): %s" % ", ".join(missing))
    summary = _json(files["summary.json"], "summary.json")
    target = _target(summary, target_id)
    _json(files["policy.json"], "policy.json")
    recipe = _json(files["recipe.json"], "recipe.json")
    imports = files["imports.jsonl"]
    if not chain.verify_bytes(imports)["valid"]:
        raise Unusable("imports.jsonl is not a valid chain of JSON objects")
    lines = chain._lines(imports)
    transfers = [i for i, line in enumerate(lines) if "referee_tree_sha256" in chain.parse_row(line.decode())]
    if not transfers:
        raise Unusable("imports.jsonl has no transfer row")
    transfer = chain.parse_row(lines[transfers[-1]].decode())

    repo, reads, reasons = target["repo"], Reads(transport), set()
    app = reads.get("/app", dict)
    installed = reads.get("/installation/repositories", dict).get("repositories")
    if not isinstance(installed, list) or not all(isinstance(r, dict) and isinstance(r.get("full_name"), str)
                                                  for r in installed):
        raise Unusable("GET /installation/repositories: repositories[] of {full_name}")
    rules = {b: _rules(reads.get("/repos/%s/rules/branches/%s" % (repo, b), list), b) for b in BRANCHES}
    if {r["full_name"] for r in installed} != {t.get("repo") for t in summary["targets"] if isinstance(t, dict)}:
        reasons.add("app_scope")
    types = {b: {rule["type"] for rule in rules[b]} for b in BRANCHES}
    if not {"deletion", "non_fast_forward"} <= types[STATE]:
        reasons.add("state_rules_missing")
    if not set(INTEGRATION_RULES) <= types[INTEGRATION]:
        reasons.add("integration_rules_missing")
    for rule in rules[INTEGRATION]:
        if rule["type"] == "required_status_checks":
            params = rule.get("parameters") if isinstance(rule.get("parameters"), dict) else {}
            checks = params.get("required_status_checks")
            if params.get("strict_required_status_checks_policy") is not True or not isinstance(checks, list) \
                    or not checks or any(not isinstance(c, dict) or c.get("integration_id") != app.get("id")
                                         for c in checks):
                reasons.add("integration_check_not_writer")
    if _bypassable(reads, repo, rules[STATE] + rules[INTEGRATION]):
        reasons.add("rules_bypassable")
    reviewed = any(rule["type"] == "pull_request" and isinstance(rule.get("parameters"), dict)
                   and type(rule["parameters"].get("required_approving_review_count")) is int
                   and rule["parameters"]["required_approving_review_count"] >= 1 for rule in rules[MAIN])
    if _bypassable(reads, repo, rules[MAIN]) or not ("update" in types[MAIN] or reviewed):
        reasons.add("main_writable")
    if target["kind"] == "toy":
        ref = reads.get("/repos/%s/git/ref/heads/main" % repo, dict).get("object")
        base_sha = ref.get("sha") if isinstance(ref, dict) else None
        if schema.hex40(base_sha, "main"):
            raise Unusable("GET main: object.sha is not 40 lowercase hex")
        workflows = reads.get("/repos/%s/actions/workflows" % repo, dict).get("workflows")
        if not isinstance(workflows, list):
            raise Unusable("GET actions/workflows: workflows[] missing")
        if workflows:
            reasons.add("toy_workflows")
    else:
        base_sha = target["base_sha"]
        if reads.get("/repos/%s/actions/permissions" % repo, dict).get("enabled") is not False:
            reasons.add("copy_actions_enabled")
    security = _chain_rows(files["security-ledger.jsonl"])
    if security is None:
        reasons.add("security_ledger_broken")
    if reasons:
        return {"ok": False, "hard_stop": True, "reasons": sorted(reasons), "payload": None}
    payload = {
        "target": target_id,
        "base_sha": base_sha,
        "referee_tree_sha256": transfer.get("referee_tree_sha256"),
        "result_sha256": transfer.get("result_sha256"),
        "import_line_sha256": _sha(lines[transfers[-1]]),
        "seed_epoch": summary["seed_epochs"][-1],
        "policy_sha256": _sha(files["policy.json"]),
        "summary_sha256": _sha(files["summary.json"]),
        "seed_security_ledger_sha256": _sha(files["security-ledger.jsonl"]),
        "seed_security_last_row_hash": security[-1]["row_hash"],
        "recipe_sha256": _canonical_sha(recipe, "recipe.json"),
        "facts_sha256": _canonical_sha(reads.facts, "the facts"),
    }
    bad = schema.payload_reasons("events", "genesis", payload)
    if bad:
        raise Unusable("genesis payload: %s" % "; ".join(bad))
    return {"ok": True, "hard_stop": False, "reasons": [], "payload": payload}


def ratchet_base(base_run: bytes, base_run_sha256: str) -> dict:
    """``{reasons, counts}``: step 2 of the activation."""
    if _sha(base_run) != base_run_sha256:
        return {"reasons": ["base_run_hash_mismatch"], "counts": None}
    try:
        run, same = check.run_file(base_run, "base.jsonl")
    except check.Unusable as exc:
        raise Unusable(str(exc)) from None
    if not same:
        return {"reasons": ["tool_nondeterministic"], "counts": None}
    return {"reasons": [], "counts": {run["tool"]: len(run["violations"])}}


# ---------------------------------------------------------------- the ready candidates

def _cause(reasons: list[str]) -> str:
    for cause, test in REJECT_CAUSES:
        if any(test(r) for r in reasons):
            return cause
    return "unknown"


def decide(cand: dict, base_run: bytes, profile: Any, recipe: Any, control: Any, pending: list[str],
           read_base: Callable[[str], bytes | None]) -> dict:
    """The acceptance rule on one candidate: ``{reasons, path, content}``; ``content`` is the applied file when
    there is no reason. ``cand`` maps ``CANDIDATE_FILES`` to bytes (a missing run file is None)."""
    if write.branch_reasons(CANDIDATE_PREFIX + cand["id"]) or "/" in cand["id"]:
        return {"reasons": ["candidate_id_invalid"], "path": None, "content": None}
    try:
        text = cand["diff.patch"].decode("utf-8", "surrogateescape")
        reasons = diffguard.check(text, profile, recipe)
        found = check.finding(_json(cand["finding.json"], "finding.json"))
        files = {"base.jsonl": base_run, "cand.jsonl": cand.get("cand.jsonl"), "checks.json": cand.get("checks.json")}
        hashes = check.hashes_file(_json(cand["hashes.json"], "hashes.json"))
        decided = check.decide(found, text, files, hashes, check.request(
            {"control": control, "unfinished_sentinels": list(pending)}))
    except (Unusable, check.Unusable, diffguard.DiffError, KeyError, AttributeError):
        return {"reasons": ["candidate_unusable"], "path": None, "content": None}
    reasons = sorted(set(reasons + decided["reasons"]))
    if reasons:
        return {"reasons": reasons, "path": found["path"], "content": None}
    old = read_base(found["path"])
    if old is None:
        return {"reasons": ["base_file_missing"], "path": found["path"], "content": None}
    try:
        content = diffguard.apply(diffguard.parse(text)[0], old)
    except diffguard.DiffError:
        return {"reasons": ["patch_does_not_apply"], "path": found["path"], "content": None}
    return {"reasons": [], "path": found["path"], "content": content}


def land(writer: write.Writer, cid: str, path: str, content: bytes, cut: str, check_name: str) -> dict:
    """Branch, commit, pull request, check and merge of one accepted candidate onto ``brain/integration``."""
    branch = CANDIDATE_PREFIX + cid
    title = "candidate %s" % cid
    writer.create_branch(branch, cut)
    head = writer.commit_files(branch, cut, {path: content}, title)
    pull = writer.open_pull(branch, INTEGRATION, title, "accepted by the gate (asama-0/08)")
    if pull is None:
        raise write.ApiError(None, "pull request created without a number")
    writer.check(head, check_name, "success", "gate: merge")
    merge = writer.merge(pull, head)
    return {"pull": pull, "head_sha": head, "merge_sha": merge}


# ---------------------------------------------------------------- the state commit

def state_files(rows: list[dict], imports: bytes, facts: dict, signer: Any, root_row_id: str) -> dict:
    """The files of the orphan ``brain/state``: ``status.block`` rows added, chained, schema-checked, root signed."""
    planned = block.plan(b"", b"", rows, None, imports, facts)
    for row in planned["rows"]:
        reasons = schema.payload_reasons(row.get("part"), row.get("kind"), row.get("payload"))
        if reasons:
            raise Unusable("row %s: %s" % (row.get("row_id"), "; ".join(reasons)))
    request = json.dumps({"rows": planned["rows"]}, sort_keys=True).encode("utf-8")
    cycle = append.plan_cycle(b"", b"", lambda: request)
    reasons = schema.ledger_reasons(cycle.content)
    if reasons:
        raise Unusable("ledger: %s" % "; ".join(reasons))
    root = anchor.root_of(anchor.tips(cycle.content))
    entry = anchor.anchor(root, signer)
    roots = anchor.root_row(b"", root_row_id, facts["ts"], root, entry["uuid"])
    return {"files": {anchor.LEDGER_PATH: cycle.content, anchor.ROOTS_PATH: roots, block.STATUS_PATH: planned["status"]},
            "row_hashes": cycle.row_hashes, "root": root, "entry": entry}


# ---------------------------------------------------------------- activation

def activate(writer: write.Writer, files: dict[str, bytes], req: Any, candidates: list[dict],
             read_base: Callable[[str], bytes | None], signer: Any, control: Any, check_name: str,
             canary_cap_usd_micros: int) -> dict:
    """The activation; see the module docstring. ``candidates``: ``{id, <CANDIDATE_FILES>: bytes|None}`` each."""
    req = _request(req)
    ids = [c.get("id") if isinstance(c, dict) else None for c in candidates]
    wanted = req["candidates"]
    if not all(isinstance(i, str) for i in ids) or sorted(ids) != sorted(set(wanted)) or len(wanted) != len(ids):
        raise Unusable("the candidates given are not the request's candidates, each once")
    missing = [name for name in FILES if not isinstance(files.get(name), bytes)]
    if missing:
        raise Unusable("missing file(s): %s" % ", ".join(missing))
    gen = genesis(writer.transport, files, req["target_id"])
    if gen["hard_stop"]:
        raise Refused(gen["reasons"])
    target = _target(_json(files["summary.json"], "summary.json"), req["target_id"])
    if writer.repo != target["repo"]:
        raise Refused(["target_repo_mismatch"])
    base = ratchet_base(files["base.jsonl"], req["base_run_sha256"])
    if base["reasons"]:
        raise Refused(base["reasons"])
    reasons = []
    if writer.exists(STATE):
        reasons.append("already_activated")
    if writer.exists(INTEGRATION):
        reasons.append("integration_exists")
    if reasons:
        raise Refused(reasons)
    cut = gen["payload"]["base_sha"]
    writer.read_commit(cut)
    profile, recipe = _json(files["profile.json"], "profile.json"), _json(files["recipe.json"], "recipe.json")
    try:  # the shapes criterion 1 reads, checked before the first write
        diffguard.check("diff --git a/x b/x\n", profile, recipe)
    except diffguard.DiffError as exc:
        raise Unusable(str(exc)) from None
    writer.create_branch(INTEGRATION, cut)
    try:
        rows = [_row(req, "genesis", "genesis", gen["payload"]),
                _row(req, "start", "cycle_start", {"cycle_id": req["cycle_id"]}),
                _row(req, "cut", "integration_cut", {"branch": INTEGRATION, "base_sha": cut}),
                _row(req, "ratchet", "ratchet_base", {"base_run_sha256": req["base_run_sha256"],
                                                      "counts": base["counts"]})]
        merges, decisions = [], []
        for cand in sorted(candidates, key=lambda c: c["id"]):
            got = decide(cand, files["base.jsonl"], profile, recipe, control, merges, read_base)
            if got["reasons"]:
                payload = {"decision": "reject", "candidate": cand["id"], "reasons": got["reasons"]}
                rows.append(_row(req, "c:" + cand["id"], "decision", payload, _cause(got["reasons"])))
                decisions.append(payload)
                continue
            done = land(writer, cand["id"], got["path"], got["content"], cut, check_name)
            merges.append(done["merge_sha"])
            payload = dict(done, decision="merge", candidate=cand["id"], path=got["path"])
            rows.append(_row(req, "c:" + cand["id"], "decision", payload))
            decisions.append(payload)
        facts = {"ts": req["ts"], "snapshot_id": req["snapshot_id"], "row_id": "%s:status" % req["cycle_id"],
                 "canary_cap_usd_micros": canary_cap_usd_micros}
        state = state_files(rows, files["imports.jsonl"], facts, signer, "%s:root" % req["cycle_id"])
        sha = writer.open_orphan(STATE, state["files"], "genesis: cycle %s" % req["cycle_id"])
    except (write.ApiError, write.Refused, Unusable, HardStopBase, block.Unusable, anchor.Unusable) as exc:
        raise HardStop("%s: %s" % (type(exc).__name__, exc), sorted(set(writer.written))) from None
    return {"state_sha": sha, "integration_sha": cut, "row_hashes": state["row_hashes"], "root": state["root"],
            "entry": state["entry"], "decisions": decisions, "files": state["files"]}


# ---------------------------------------------------------------- command line

USAGE = "usage: python -m activate genesis API SUMMARY IMPORTS POLICY SECURITY RECIPE < {\"target\": id}"


def _emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, sort_keys=True) + "\n")


def _read(path: str) -> bytes:
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError as exc:
        raise Unusable("%s: %s" % (path, exc.strerror)) from None


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 7 or argv[0] != "genesis":
            raise Unusable(USAGE)
        api = write.Replay(_json(_read(argv[1]), "the recorded API"))
        files = dict(zip(GENESIS_FILES, (_read(path) for path in argv[2:])))
        request = _json(sys.stdin.buffer.read(), "stdin")
        if not isinstance(request, dict) or set(request) != {"target"}:
            raise Unusable('stdin must be {"target"} and nothing else')
        out = genesis(api, files, request["target"])
        _emit(out)
        return 1 if out["hard_stop"] else 0
    except (Unusable, write.Unusable, chain.ChainError) as exc:
        cause = "unusable input: %s" % exc
    _emit({"ok": False, "hard_stop": True, "payload": None})
    sys.stderr.write(cause + "\n")
    return 2


FAULT_LINE = {"ok": False, "hard_stop": True, "payload": None}


if __name__ == "__main__":
    sys.exit(cli.run(main, sys.argv[1:], FAULT_LINE))
